"""Plugins da esteira: interfaces + adaptadores reais.

Cada etapa usa plugins injetáveis (os testes passam falsos; o --simular usa
os de simulados.py). Os reais chamam os scripts que JÁ EXISTEM no PC por
subprocesso (hpbase.rodar, sem janela), com a linha de comando montada a
partir de config.json -> "comandos" (dá para ajustar sem mexer no código).

  Baixador    -> scripts\\ytdlp.py (ou yt-dlp do PATH)
  Legendador  -> faster-whisper (se instalado; senão erro claro)
  Dublador    -> scripts\\dublar.py (Piper pt-BR)
  Narrador    -> scripts\\dublar.py para cada frase + montagem com ffmpeg
  Editor      -> ffmpeg (editor.py)
  Designer    -> scripts\\estaticos.py
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

from .constantes import EXT_IMAGEM, EXT_VIDEO
from .erros import ErroEtapa, ErroPermanente
from .legendas import Fala, escrever_srt, quebrar_falas


# --- interfaces ------------------------------------------------------------
class Baixador(Protocol):
    def baixar(self, url: str, destino: Path) -> Path: ...


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
    """Troca {python} {scripts} {url} {entrada} {saida} {item} no modelo."""
    modelo = cfg.comandos.get(nome)
    if not modelo:
        raise ErroPermanente(f"comando '{nome}' não configurado em config.json")
    vals = {"python": cfg.python, "scripts": str(cfg.pasta_scripts)}
    vals.update({k: str(v) for k, v in valores.items()})
    saida = []
    for parte in modelo:
        try:
            saida.append(str(parte).format(**vals))
        except KeyError as e:
            raise ErroPermanente(f"comando '{nome}' usa {{{e.args[0]}}}, que não "
                                 f"existe nesta etapa") from e
    return saida


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
    """Usa scripts\\ytdlp.py (o que já existe) ou, se faltar, o yt-dlp do PATH."""

    def __init__(self, cfg, rodar_fn: Callable = rodar):
        self.cfg = cfg
        self.rodar = rodar_fn

    def comando(self, url: str, destino: Path) -> list[str]:
        if (Path(self.cfg.pasta_scripts) / "ytdlp.py").exists():
            return montar_comando(self.cfg, "baixar", url=url, saida=destino)
        exe = shutil.which("yt-dlp")
        if exe:
            return [exe, "--no-playlist", "--no-progress",
                    "-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b",
                    "--merge-output-format", "mp4",
                    "-o", str(Path(destino) / "bruto.%(ext)s"), url]
        raise ErroPermanente("não achei scripts\\ytdlp.py nem o yt-dlp "
                             "(pip install yt-dlp)")

    def baixar(self, url: str, destino: Path) -> Path:
        destino = garantir(Path(destino))
        cmd = self.comando(url, destino)
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
    """scripts\\dublar.py (Piper pt-BR, voz gratuita já instalada; nunca clona voz)."""

    def __init__(self, cfg, rodar_fn: Callable = rodar):
        self.cfg = cfg
        self.rodar = rodar_fn

    def dublar(self, item: Path, legenda: Path, pedido: dict) -> Path:
        _script(self.cfg, "dublar.py")
        saida = Path(item) / "dublagem.wav"
        cmd = montar_comando(self.cfg, "dublar", entrada=legenda, saida=saida, item=item)
        r = self.rodar(cmd, timeout=self.cfg.timeouts.get("dublar", 1800), cwd=item)
        _checar(r, "dublagem (dublar.py)")
        if not saida.exists():
            raise ErroEtapa("dublar.py terminou sem gerar dublagem.wav")
        return saida


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
        _script(self.cfg, "dublar.py")
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
        entradas, filtros, rot = [], [], []
        for i, nome in enumerate(partes):
            entradas += ["-i", str(partes[nome])]
            ms = int(plano[nome]["inicio"] * 1000)
            f = f"[{i}:a]{fmt}"
            if nome == "abertura" and plano[nome]["tempo"] != 1.0:
                f += f",atempo={plano[nome]['tempo']}"
            if ms > 0:
                f += f",adelay={ms}|{ms}"
            filtros.append(f + f"[p{i}]")
            rot.append(f"[p{i}]")
        # apad SEMPRE com whole_dur (fluxo finito) + -t na saída: apad sozinho nunca
        # termina e o ffmpeg 7 não encerra no atrim (gerava WAV infinito)
        filtros.append(f"{''.join(rot)}amix=inputs={len(rot)}:normalize=0:duration=longest,"
                       f"apad=whole_dur={duracao:.3f},atrim=end={duracao:.3f}[n]")
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
class DesignerScript:
    """Estáticos: scripts\\estaticos.py gera as lâminas em arte\\.

    Atalhos: threads_texto só grava texto_threads.txt (não tem arte); se o
    pedido já trouxer imagens prontas em `arquivos`, elas são usadas.
    """

    def __init__(self, cfg, rodar_fn: Callable = rodar):
        self.cfg = cfg
        self.rodar = rodar_fn

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
        _script(self.cfg, "estaticos.py")
        cmd = montar_comando(self.cfg, "estaticos", entrada=item / "pedido.json",
                             saida=pasta, item=item)
        r = self.rodar(cmd, timeout=self.cfg.timeouts.get("estaticos", 600), cwd=item)
        _checar(r, "arte (estaticos.py)")
        imgs = sorted(p for p in pasta.iterdir() if p.suffix.lower() in EXT_IMAGEM)
        if not imgs:
            raise ErroEtapa("estaticos.py terminou sem gerar imagem em arte\\")
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
