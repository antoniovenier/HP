"""Plugins da esteira: interfaces + adaptadores reais.

Cada etapa usa plugins injetáveis (os testes passam falsos; o --simular usa
os de simulados.py). Os reais chamam os scripts que JÁ EXISTEM no PC por
subprocesso (hpbase.rodar, sem janela), com o argv montado por
esteira/comandos_pc.py (a linha de comando REAL de cada script, §4.4). Se o
config.json -> "comandos" sobrepuser um modelo, vale o modelo (montar_comando).

  Baixador    -> scripts\\ytdlp.py com o trecho (argv_baixar) ou yt-dlp do PATH
  Legendador  -> faster-whisper (se instalado; senão erro claro)
  Dublador    -> scripts\\dublar.py sobre um corte JÁ renderizado (argv_dublar_avulso);
                 na esteira a dublagem do gringo sai pelo cortar.py --dublar
  Narrador    -> frase a frase por um sintetizador injetado/configurado + montagem com ffmpeg
                 (o dublar.py do PC NÃO tem --texto-arquivo)
  Editor      -> ffmpeg (editor.py)
  Designer    -> scripts\\estaticos.py (GTA: carrossel/story) e posts_<canal>.py render (canais)
  Agendador   -> fila da API (agendador.py)
  Avisador    -> fila do WhatsApp (aviso.py)
  Midia       -> ffmpeg (midia.py): confere bruto, extrai áudio, quadros
"""
from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol

from hpbase import escrever_json, garantir, mascarar, rodar

from . import comandos_pc as cp
from .constantes import EXT_IMAGEM, EXT_VIDEO
from .erros import ErroEtapa, ErroPermanente
from .legendas import Fala, escrever_srt, quebrar_falas


# --- interfaces ------------------------------------------------------------
class Baixador(Protocol):
    def baixar(self, url: str, destino: Path, pedido: dict | None = None) -> Path: ...


class Legendador(Protocol):
    def legendar(self, audio: Path, pasta: Path, idioma: str | None = None) -> Path: ...


class Dublador(Protocol):
    def dublar(self, item: Path, legenda: Path, pedido: dict) -> Path: ...


class Narrador(Protocol):
    def narrar(self, item: Path, roteiro: dict, duracao: float) -> Path: ...


class Editor(Protocol):
    def editar(self, item: Path, pedido: dict) -> dict: ...


class Designer(Protocol):
    def gerar(self, item: Path, pedido: dict) -> list[Path]: ...


class Agendador(Protocol):
    def agendar(self, item: Path, post: dict, rede: str) -> dict: ...
    def conferir(self, item: Path, post: dict, rede: str, registro: dict) -> dict | None: ...


class Avisador(Protocol):
    def enviar(self, item: Path, mensagem: dict, nome_arquivo: str) -> tuple[Path, str]: ...


class Midia(Protocol):
    def info(self, arquivo: Path) -> dict: ...
    def extrair_audio(self, video: Path, saida: Path) -> Path: ...
    def quadros(self, video: Path, pasta: Path, largura: int = 540) -> list[dict]: ...
    def reduzir_imagem(self, imagem: Path, saida: Path, largura: int = 540) -> Path: ...
    def loudness(self, arquivo: Path) -> float | None: ...


@dataclass
class Plugins:
    baixador: Any
    midia: Any
    legendador: Any
    dublador: Any
    narrador: Any
    editor: Any
    designer: Any
    agendador: Any
    avisador: Any


# --- utilidades -----------------------------------------------------------
def montar_comando(cfg, nome: str, **valores) -> list[str]:
    """Preenche o modelo de config.json -> "comandos" (marcadores {python} {scripts} {url}
    {entrada} {saida} {inicio} {fim} ...). Mantido para quem personalizou um comando."""
    modelo = cfg.comandos.get(nome)
    if not modelo:
        raise ErroPermanente(f"comando '{nome}' não configurado em config.json")
    vals = {"python": cfg.python, "scripts": str(cfg.pasta_scripts), "item": ""}
    vals.update({k: str(v) for k, v in valores.items()})
    try:
        return cp.preencher(modelo, **vals)
    except KeyError as e:
        raise ErroPermanente(f"comando '{nome}' usa {{{e.args[0]}}}, que não "
                             f"existe nesta etapa") from e


def personalizado(cfg, nome: str) -> bool:
    """config.json trocou este comando? (então vale montar_comando, não o comandos_pc)"""
    from .config import COMANDOS_PADRAO
    return nome in cfg.comandos and cfg.comandos.get(nome) != COMANDOS_PADRAO.get(nome)


def _checar(r, o_que: str) -> None:
    if r.returncode != 0:
        cauda = (r.stderr or b"").decode("utf-8", "replace").strip().splitlines()[-6:]
        raise ErroEtapa(f"{o_que} falhou (código {r.returncode}): "
                        f"{mascarar(' | '.join(cauda))}")


def _script(cfg, nome: str) -> Path:
    p = Path(cfg.pasta_scripts) / nome
    if not p.exists():
        raise ErroPermanente(f"scripts\\{nome} não encontrado em {cfg.pasta_scripts}")
    return p


# --- Baixador ---------------------------------------------------------------
class BaixadorYtdlp:
    """scripts\\ytdlp.py com o argv REAL do baixar.py (comandos_pc.argv_baixar: só o trecho
    inicio−4..fim+4 quando o pedido traz inicio/fim) ou, se o script faltar, o yt-dlp do PATH."""

    def __init__(self, cfg, rodar_fn: Callable = rodar):
        self.cfg = cfg
        self.rodar = rodar_fn

    def comando(self, url: str, destino: Path, pedido: dict | None = None) -> list[str]:
        """Argv puro (não roda). `destino` é a pasta; o arquivo sai como <destino>\\bruto.mp4."""
        pedido = dict(pedido or {})
        pedido["video_url"] = url
        pedido.pop("arquivo", None)          # aqui sempre baixa (o trecho local a esteira já copiou)
        arquivo = Path(destino) / "bruto.mp4"
        if (Path(self.cfg.pasta_scripts) / "ytdlp.py").exists():
            if personalizado(self.cfg, "baixar"):
                extra = {}
                if pedido.get("inicio") is not None and pedido.get("fim") is not None:
                    extra = {"inicio": cp.hms(cp.segundos(pedido["inicio"]) - cp.FOLGA),
                             "fim": cp.hms(cp.segundos(pedido["fim"]) + cp.FOLGA)}
                return montar_comando(self.cfg, "baixar", url=url, saida=arquivo, **extra)
            return cp.argv_baixar(pedido, arquivo, python=self.cfg.python,
                                  scripts=self.cfg.pasta_scripts)
        exe = shutil.which("yt-dlp")
        if exe:
            return [exe, "--no-playlist", "--no-progress",
                    "-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b",
                    "--merge-output-format", "mp4",
                    "-o", str(Path(destino) / "bruto.%(ext)s"), url]
        raise ErroPermanente("não achei scripts\\ytdlp.py nem o yt-dlp "
                             "(pip install yt-dlp)")

    def baixar(self, url: str, destino: Path, pedido: dict | None = None) -> Path:
        destino = garantir(Path(destino))
        cmd = self.comando(url, destino, pedido)
        r = self.rodar(cmd, timeout=self.cfg.timeouts.get("baixar", 1800), cwd=destino)
        _checar(r, "download")
        videos = [p for p in Path(destino).rglob("*")
                  if p.is_file() and p.suffix.lower() in EXT_VIDEO]
        if not videos:
            raise ErroEtapa(f"o download terminou mas nenhum vídeo apareceu em {destino.name}")
        return max(videos, key=lambda p: p.stat().st_size)


# --- Legendador -------------------------------------------------------------
class LegendadorWhisper:
    """Transcrição com faster-whisper -> transcricao.json + legenda.srt."""

    def __init__(self, cfg, fabrica_modelo: Callable | None = None):
        self.o = cfg.legendador
        self._fabrica = fabrica_modelo
        self._modelo = None

    def _carregar(self):
        if self._modelo is not None:
            return self._modelo
        if self._fabrica is not None:
            self._modelo = self._fabrica()
            return self._modelo
        try:
            from faster_whisper import WhisperModel  # type: ignore
        except ImportError as e:
            raise ErroPermanente(
                "faster-whisper não está instalado: rode  pip install faster-whisper  "
                "(ou grave legenda_manual.srt na pasta do item)") from e
        self._modelo = WhisperModel(self.o["modelo"], device=self.o["dispositivo"],
                                    compute_type=self.o["tipo_computacao"])
        return self._modelo

    def legendar(self, audio: Path, pasta: Path, idioma: str | None = None) -> Path:
        modelo = self._carregar()
        segs, info = modelo.transcribe(str(audio), language=idioma or self.o.get("idioma"),
                                       vad_filter=True, beam_size=5)
        brutas = [Fala(float(s.start), float(s.end), str(s.text).strip()) for s in segs]
        escrever_json(Path(pasta) / "transcricao.json", {
            "idioma": getattr(info, "language", None),
            "segmentos": [{"inicio": f.inicio, "fim": f.fim, "texto": f.texto}
                          for f in brutas]})
        falas = quebrar_falas(brutas, int(self.o.get("max_caracteres", 42)))
        tmp = Path(pasta) / "_tmp_legenda.srt"
        escrever_srt(falas, tmp)
        final = Path(pasta) / "legenda.srt"
        os.replace(tmp, final)
        return final


# --- Dublador ---------------------------------------------------------------
class DubladorScript:
    """scripts\\dublar.py REAL (Piper pt-BR, nunca clona voz): dubla um corte JÁ renderizado
    (`dublar.py <corte> --transcricao <json PT> --inicio --fim [--saida]`). Não aceita --srt nem
    --texto-arquivo e não gera dublagem.wav avulsa. Na esteira a dublagem do gringo sai pelo
    cortar.py --dublar (comandos_pc.argv_cortar(dublar=True)); este plugin serve para dublar à
    parte um final.mp4 pronto (dublar_corte) — se o item ainda não tem corte, erro claro."""

    def __init__(self, cfg, rodar_fn: Callable = rodar):
        self.cfg = cfg
        self.rodar = rodar_fn

    def comando(self, corte: Path, transcricao: Path, inicio, fim, saida=None) -> list[str]:
        """Argv puro (não roda)."""
        if personalizado(self.cfg, "dublar"):
            argv = montar_comando(self.cfg, "dublar", entrada=corte, transcricao=transcricao,
                                  inicio=inicio, fim=fim, saida=saida or "")
            return argv + (["--saida", str(saida)] if saida and "--saida" not in argv else [])
        return cp.argv_dublar_avulso(corte, transcricao, inicio, fim, saida,
                                     python=self.cfg.python, scripts=self.cfg.pasta_scripts)

    def dublar_corte(self, corte: Path, transcricao: Path, inicio, fim, saida: Path | None = None) -> Path:
        _script(self.cfg, "dublar.py")
        corte, transcricao = Path(corte), Path(transcricao)
        if not transcricao.exists():
            raise ErroPermanente(f"dublar.py precisa da transcrição em PT (formato 4.5): "
                                 f"{transcricao.name} não existe")
        saida = Path(saida) if saida else corte.with_name(f"{corte.stem}_dublado{corte.suffix}")
        cmd = self.comando(corte, transcricao, inicio, fim, saida)
        r = self.rodar(cmd, timeout=self.cfg.timeouts.get("dublar", 1800), cwd=corte.parent)
        _checar(r, "dublagem (dublar.py)")
        if not saida.exists():
            raise ErroEtapa(f"dublar.py terminou sem gerar {saida.name}")
        return saida

    def dublar(self, item: Path, legenda: Path, pedido: dict) -> Path:
        """Interface da etapa 03: só funciona se o item já tem um corte renderizado (final.mp4);
        a transcrição PT é legenda (.json) ou transcricao_pt.json / transcricao.json ao lado."""
        item = Path(item)
        corte = item / "final.mp4"
        if not corte.exists():
            raise ErroPermanente(
                "o dublar.py do PC só dubla um corte já renderizado (não gera dublagem.wav): "
                "na esteira a dublagem do gringo sai pelo cortar.py --dublar; para dublar à parte "
                "use DubladorScript.dublar_corte(final.mp4, transcricao PT, inicio, fim)")
        leg = Path(legenda)
        transcricao = leg if leg.suffix.lower() == ".json" else next(
            (item / n for n in ("transcricao_pt.json", "transcricao.json") if (item / n).exists()),
            item / "transcricao_pt.json")
        jan = cp.janela(pedido) or (0, pedido.get("duracao") or 0)
        return self.dublar_corte(corte, transcricao, jan[0], jan[1], item / "final_dublado.mp4")


# --- Narrador Toque HP -------------------------------------------------------
class NarradorToqueHP:
    """Pergunta nos 2 primeiros segundos, trecho narrado, fecho com pergunta.

    Cada frase é sintetizada pelo dublar.py (Piper) e o narracao.wav é
    montado aqui com ffmpeg, no tempo certo do vídeo final:
      abertura em 0 s (acelera até 1,25x para caber em 2 s; se não couber, erro),
      trecho a partir de ~2,3 s, fecho terminando 0,3 s antes do fim.
    """

    def __init__(self, cfg, sintetizar: Callable[[str, Path], Path] | None = None,
                 rodar_fn: Callable = rodar):
        self.cfg = cfg
        self.rodar = rodar_fn
        self.sintetizar = sintetizar or self._sintetizar_script

    def _sintetizar_script(self, texto: str, saida: Path) -> Path:
        if not self.cfg.comandos.get("falar"):
            raise ErroPermanente(
                "não há sintetizador de frase avulsa: o dublar.py do PC não tem --texto-arquivo. "
                "Configure comandos.falar no config.json (ex.: o piper com {entrada} e {saida}) "
                "ou injete sintetizar= no NarradorToqueHP")
        txt = Path(saida).with_suffix(".txt")
        txt.write_text(texto, encoding="utf-8")
        cmd = montar_comando(self.cfg, "falar", entrada=txt, saida=saida,
                             item=Path(saida).parent)
        r = self.rodar(cmd, timeout=self.cfg.timeouts.get("falar", 600),
                       cwd=Path(saida).parent)
        _checar(r, "voz (dublar.py)")
        if not Path(saida).exists():
            raise ErroEtapa(f"dublar.py não gerou {Path(saida).name}")
        return Path(saida)

    def planejar(self, duracoes: dict, duracao_video: float) -> dict:
        """Calcula tempos (função pura, testável)."""
        o = self.cfg.narrador
        d_ab = duracoes["abertura"]
        tempo = 1.0
        if d_ab > o["abertura_max_s"]:
            tempo = d_ab / o["abertura_max_s"]
            if tempo > o["acelerar_max"]:
                raise ErroPermanente(
                    f"a pergunta de abertura tem {d_ab:.1f}s e precisa caber em "
                    f"{o['abertura_max_s']:.0f}s: encurte o texto")
        fim_ab = d_ab / tempo
        plano = {"abertura": {"inicio": 0.0, "fim": round(fim_ab, 3), "tempo": round(tempo, 4)}}
        fim_ant = fim_ab
        if "trecho" in duracoes:
            ini = max(o["inicio_trecho_s"], fim_ab + 0.2)
            plano["trecho"] = {"inicio": round(ini, 3), "fim": round(ini + duracoes["trecho"], 3)}
            fim_ant = ini + duracoes["trecho"]
        ini_f = duracao_video - o["folga_fim_s"] - duracoes["fecho"]
        if ini_f < fim_ant + 0.2:
            raise ErroPermanente(
                f"vídeo de {duracao_video:.1f}s é curto demais para a narração "
                f"(abertura+trecho terminam em {fim_ant:.1f}s e o fecho tem "
                f"{duracoes['fecho']:.1f}s)")
        plano["fecho"] = {"inicio": round(ini_f, 3), "fim": round(ini_f + duracoes["fecho"], 3)}
        return plano

    def narrar(self, item: Path, roteiro: dict, duracao: float) -> Path:
        from .midia import ffmpeg, info_midia
        item = Path(item).resolve()
        pasta = garantir(item / "narracao")
        partes = {}
        for nome in ("abertura", "trecho", "fecho"):
            texto = str(roteiro.get(nome) or "").strip()
            if texto:
                partes[nome] = self.sintetizar(texto, pasta / f"{nome}.wav")
        duracoes = {n: float(info_midia(p).duracao or 0) for n, p in partes.items()}
        plano = self.planejar(duracoes, duracao)
        fmt = "aformat=sample_rates=48000:channel_layouts=stereo"
        # 1ª entrada = silêncio com a duração EXATA do vídeo; o amix com
        # duration=first termina junto com ele. Nada de apad: no ffmpeg 7 o apad
        # às vezes nunca termina (gerou WAV infinito) ou para antes da hora.
        entradas = ["-f", "lavfi", "-t", f"{duracao:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
        filtros, rot = [f"[0:a]{fmt}[base]"], ["[base]"]
        for i, nome in enumerate(partes, start=1):
            entradas += ["-i", str(partes[nome])]
            ms = int(plano[nome]["inicio"] * 1000)
            f = f"[{i}:a]{fmt}"
            if nome == "abertura" and plano[nome]["tempo"] != 1.0:
                f += f",atempo={plano[nome]['tempo']}"
            if ms > 0:
                f += f",adelay={ms}|{ms}"
            filtros.append(f + f"[p{i}]")
            rot.append(f"[p{i}]")
        filtros.append(f"{''.join(rot)}amix=inputs={len(rot)}:normalize=0:duration=first[n]")
        tmp = item / "_tmp_narracao.wav"
        limite = int(duracao * 48000 * 2 * 2 * 1.5) + 1_000_000  # teto do WAV em bytes
        ffmpeg(["-y", *entradas, "-filter_complex", ";".join(filtros), "-map", "[n]",
                "-ar", "48000", "-ac", "2", "-t", f"{duracao:.3f}", "-fs", str(limite),
                str(tmp)], timeout=self.cfg.timeouts.get("ffmpeg_curto", 300),
               o_que="montagem da narração")
        final = item / "narracao.wav"
        os.replace(tmp, final)
        escrever_json(item / "narracao.json", {"roteiro": roteiro, "plano": plano,
                                               "duracao_video": duracao})
        return final


# --- Designer -----------------------------------------------------------------
def spec_carrossel_gta(pedido: dict) -> dict:
    """Spec do estaticos.py carrossel (§4.4) a partir do pedido: capa = título (+ subtítulo/imagem/
    selo se vierem), lâminas = `laminas` [{titulo, texto, imagem?}], fonte e final opcionais."""
    if isinstance(pedido.get("spec"), dict):
        return dict(pedido["spec"])
    capa = {"titulo": pedido.get("titulo", ""), "subtitulo": pedido.get("subtitulo", ""),
            "imagem": pedido.get("imagem", "")}
    if pedido.get("selo"):
        capa["selo"] = pedido["selo"]
    laminas = []
    for i, l in enumerate(pedido.get("laminas") or [], 1):
        if isinstance(l, dict):
            lam = {"titulo": l.get("titulo", ""), "texto": l.get("texto", "")}
            if l.get("imagem"):
                lam["imagem"] = l["imagem"]
        else:
            lam = {"titulo": f"{i}", "texto": str(l)}
        laminas.append(lam)
    spec = {"capa": capa, "laminas": laminas}
    if pedido.get("fonte"):
        spec["fonte"] = pedido["fonte"]
    if pedido.get("final"):
        spec["final"] = pedido["final"]
    return spec


class DesignerScript:
    """Estáticos com os scripts REAIS: GTA -> scripts\\estaticos.py (`carrossel <spec> <pasta>`,
    `story <tipo> <saida.jpg> --titulo ...`); canais -> posts_<canal>.py render <spec.json>
    (o pedido precisa trazer "spec" com o JSON do post, §4.4). Saída em arte\\.

    Atalhos: threads_texto só grava texto_threads.txt (não tem arte); se o pedido já trouxer
    imagens prontas em `arquivos`, elas são usadas. Campos do pedido que o GTA usa: `laminas`
    (ou `spec`), `tiktok` (carrossel 1080x1920), `modelo` do story (novo_video | contagem |
    noticia | interativo; padrão noticia) e `opcoes` {titulo, texto, imagem, video, fonte, data,
    hoje, selo} (padrão: titulo do pedido e texto).
    """

    def __init__(self, cfg, rodar_fn: Callable = rodar):
        self.cfg = cfg
        self.rodar = rodar_fn

    def comando(self, item: Path, pedido: dict, pasta: Path) -> tuple[list[str], str, Path | None]:
        """(argv puro, nome do script, arquivo-alvo quando o script gera 1 só) — grava só o spec
        JSON na pasta do item; não roda."""
        item, pasta = Path(item), Path(pasta)
        canal, tipo = pedido.get("canal"), pedido["tipo"]
        py, sc = self.cfg.python, self.cfg.pasta_scripts
        if canal == "gta":
            if tipo == "carrossel":
                spec = escrever_json(item / "spec_carrossel.json", spec_carrossel_gta(pedido))
                if personalizado(self.cfg, "estaticos_carrossel"):
                    argv = montar_comando(self.cfg, "estaticos_carrossel", entrada=spec, saida=pasta)
                    return argv + (["--tiktok"] if pedido.get("tiktok") else []), "estaticos.py", None
                return cp.argv_estaticos_carrossel(spec, pasta, tiktok=bool(pedido.get("tiktok")),
                                                   python=py, scripts=sc), "estaticos.py", None
            if tipo == "story":
                modelo = pedido.get("modelo") or "noticia"
                opcoes = dict(pedido.get("opcoes") or {})
                opcoes.setdefault("titulo", pedido.get("titulo"))
                if pedido.get("texto") and modelo in ("noticia",):
                    opcoes.setdefault("texto", pedido["texto"])
                saida = pasta / "story.jpg"
                if personalizado(self.cfg, "estaticos_story"):
                    return montar_comando(self.cfg, "estaticos_story", tipo=modelo, saida=saida), "estaticos.py", saida
                return cp.argv_estaticos_story(modelo, saida, python=py, scripts=sc, **opcoes), "estaticos.py", saida
            raise ErroPermanente(f"estaticos.py não tem arte avulsa de feed ({tipo}): no GTA use "
                                 f"carrossel (capa + lâminas) ou story")
        if canal not in cp.POSTS_POR_CANAL:
            raise ErroPermanente(f"não há script de arte para o canal {canal!r}")
        if not isinstance(pedido.get("spec"), dict):
            raise ErroPermanente(f"pedido.json precisa de \"spec\" com o JSON do post do "
                                 f"posts_{canal}.py (§4.4: canal, id, saida, slides[...], story, reel, creditos)")
        spec = dict(pedido["spec"])
        spec.setdefault("canal", canal)
        spec.setdefault("id", pedido.get("id"))
        spec["saida"] = str(pasta)
        arq = escrever_json(item / "post_spec.json", spec)
        script = cp.POSTS_POR_CANAL[canal]
        if personalizado(self.cfg, "posts_render"):
            return montar_comando(self.cfg, "posts_render", script=script, entrada=arq), script, None
        return cp.argv_posts_render(canal, arq, python=py, scripts=sc), script, None

    def gerar(self, item: Path, pedido: dict) -> list[Path]:
        item = Path(item)
        if pedido["tipo"] == "threads_texto":
            p = item / "texto_threads.txt"
            p.write_text(pedido["texto"].strip() + "\n", encoding="utf-8")
            return [p]
        pasta = garantir(item / "arte")
        prontas = []
        for a in pedido.get("arquivos") or []:
            src = Path(a) if Path(a).is_absolute() else item / a
            if src.exists() and src.suffix.lower() in EXT_IMAGEM:
                dst = pasta / f"arte_{len(prontas) + 1:02d}{src.suffix.lower()}"
                if src.resolve() != dst.resolve():
                    shutil.copy2(src, dst)
                prontas.append(dst)
        if prontas:
            return prontas
        cmd, script, alvo = self.comando(item, pedido, pasta)
        _script(self.cfg, script)
        r = self.rodar(cmd, timeout=self.cfg.timeouts.get("estaticos", 600), cwd=item)
        _checar(r, f"arte ({script})")
        if alvo is not None:
            if not alvo.exists():
                raise ErroEtapa(f"{script} terminou sem gerar {alvo.name}")
            return [alvo]
        imgs = sorted(p for p in pasta.iterdir() if p.suffix.lower() in EXT_IMAGEM)
        if not imgs:
            raise ErroEtapa(f"{script} terminou sem gerar imagem em arte\\")
        tipo = pedido["tipo"]
        sufixo = {"story": "_story", "estatico": "_feed"}.get(tipo)
        if sufixo and pedido.get("canal") != "gta":
            so = [p for p in imgs if p.stem.endswith(sufixo)]
            if so:
                return so
        if tipo == "carrossel" and pedido.get("canal") != "gta":
            so = [p for p in imgs if p.stem[-2:].isdigit()]
            if so:
                return so
        return imgs


# --- fábrica -------------------------------------------------------------------
def plugins_reais(cfg) -> Plugins:
    from .agendador import AgendadorFilaApi
    from .aviso import AvisadorWhatsApp
    from .editor import EditorFFmpeg
    from .midia import MidiaFFmpeg
    return Plugins(
        baixador=BaixadorYtdlp(cfg),
        midia=MidiaFFmpeg(),
        legendador=LegendadorWhisper(cfg),
        dublador=DubladorScript(cfg),
        narrador=NarradorToqueHP(cfg),
        editor=EditorFFmpeg(cfg),
        designer=DesignerScript(cfg),
        agendador=AgendadorFilaApi(cfg),
        avisador=AvisadorWhatsApp(cfg),
    )
