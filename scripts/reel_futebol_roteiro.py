"""Roteiro (JSON) do reel do Futebol | HP: carregar, validar e aplicar as regras.

Regras que o validador NUNCA deixa passar (vêm do CLAUDE.md da empresa):
- futebol sem imagem de transmissão de TV (fonte_tipo "transmissao_tv" = recusa);
- vídeo só oficial (clube, CBF ou liga), com crédito e com o ÁUDIO ORIGINAL;
- NUNCA narração/voz sintética no futebol (qualquer campo de voz = recusa);
- música só livre de direitos, da pasta musicas_livres, com licença registrada;
- gol nunca é o vídeo puro: cartão + caixa de legenda + crédito, sempre.
"""
from __future__ import annotations

import copy
import json
import os
import sys
import tempfile
from pathlib import Path

from PIL import Image

from reel_futebol_arte import ESTILO_PADRAO
from reel_futebol_base import (AQUI, FONTES_FOTO_OK, FONTES_PROIBIDAS,
                               FONTES_VIDEO_OK, MODOS, ErroReel, garantir,
                               ler_json, raiz_local, rodar)
from reel_futebol_midia import info_midia, medir_volume

CHAVES_VOZ = {"voz", "voz_sintetica", "narracao", "narração", "narrador",
              "tts", "locucao", "locução", "dublagem", "voz_off", "piper",
              "texto_para_fala"}
TIPOS_VOZ = {"voz", "tts", "narracao", "narração", "locucao", "locução",
             "dublagem", "voz_sintetica", "narrador"}
LICENCAS_RUINS = {"", "?", "desconhecida", "nenhuma", "sem licença",
                  "sem licenca", "todos os direitos reservados", "copyright",
                  "all rights reserved"}
EXTS_FOTO = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

PADROES = {
    "gol": {"duracao_cartao": 2.0},
    "noticia": {"duracao_por_foto": 4.0},
    "debate": {"duracao_recorte": 3.0, "duracao_final": 2.5,
               "pergunta_final": "Quem é o melhor? Comenta aí!"},
    "estatistica": {"duracao": 5.0, "duracao_contagem": 2.5, "casas_decimais": 0,
                    "prefixo": "", "sufixo": ""},
    "resultado": {"duracao": 5.0},
    "tabela": {"duracao": 6.0},
}


# ------------------------------------------------------------------ carregar
def carregar_roteiro(fonte, base: Path | None = None) -> tuple[dict, Path, Path | None]:
    """Devolve (roteiro, pasta_base, caminho_do_json). Aceita caminho ou dict."""
    if isinstance(fonte, dict):
        return copy.deepcopy(fonte), Path(base or Path.cwd()).resolve(), None
    p = Path(fonte)
    if not p.exists():
        raise ErroReel(f"roteiro não encontrado: {p}")
    try:
        dados = ler_json(p)
    except json.JSONDecodeError as e:
        raise ErroReel(f"roteiro com JSON quebrado ({p.name}, linha {e.lineno}): {e.msg}") from e
    if not isinstance(dados, dict):
        raise ErroReel(f"roteiro precisa ser um objeto JSON: {p}")
    return dados, p.parent.resolve(), p.resolve()


def resolver(valor, base: Path) -> Path:
    p = Path(str(valor))
    return p if p.is_absolute() else (base / p)


def _txt(v) -> str:
    return "" if v is None else str(v).strip()


def _num(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).replace(".", "").replace(",", ".")) if "," in str(v) else float(str(v))
    except (TypeError, ValueError):
        return None


def _varrer(obj, caminho: str = ""):
    """Todas as (caminho, chave, valor) de dicionários dentro do roteiro."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            c = f"{caminho}.{k}" if caminho else str(k)
            yield c, str(k), v
            yield from _varrer(v, c)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _varrer(v, f"{caminho}[{i}]")


# ------------------------------------------------------------------- música
def pasta_musicas(estilo: dict | None = None) -> Path:
    env = os.environ.get("HP_MUSICAS_LIVRES")
    if env:
        return Path(env)
    if estilo and estilo.get("pasta_musicas"):
        return Path(estilo["pasta_musicas"])
    return raiz_local() / "musicas_livres"


def resolver_musica(m: dict, base: Path, estilo: dict | None = None) -> Path:
    """Nome solto = pasta padrão musicas_livres; caminho = relativo ao roteiro."""
    p = Path(_txt(m.get("arquivo")))
    if p.is_absolute():
        return p
    if len(p.parts) == 1:
        return pasta_musicas(estilo) / p
    return base / p


def _raiz_musicas_livres(p: Path) -> Path | None:
    for pai in p.resolve().parents:
        if pai.name.lower() == "musicas_livres":
            return pai
    return None


def licenca_da_musica(p: Path) -> dict | None:
    """Procura a licença: <arquivo>.licenca.json ao lado, ou licencas.json na
    pasta da música (ou acima, até a musicas_livres) com a chave = nome."""
    lado = p.with_name(p.name + ".licenca.json")
    if lado.exists():
        return ler_json(lado, {})
    raiz = _raiz_musicas_livres(p)
    pasta = p.resolve().parent
    while True:
        reg = ler_json(pasta / "licencas.json", {})
        if isinstance(reg, dict):
            chave = p.resolve().relative_to(pasta).as_posix()
            for k in (chave, p.name):
                if k in reg:
                    return reg[k]
        if raiz is None or pasta == raiz or pasta.parent == pasta:
            return None
        pasta = pasta.parent


def problema_licenca(lic) -> str | None:
    if not isinstance(lic, dict):
        return "sem licença registrada"
    tipo = _txt(lic.get("licenca")).lower()
    if tipo in LICENCAS_RUINS:
        return f"licença inválida ou desconhecida ('{lic.get('licenca', '')}')"
    if not _txt(lic.get("fonte")):
        return "a licença precisa do campo 'fonte' (de onde a música veio)"
    return None


# ----------------------------------------------------------------- legendas
def normalizar_legendas(valor, duracao: float) -> list[tuple[str, float, float]]:
    """str, lista de str ou lista de {texto, inicio, fim} -> [(texto, ini, fim)]."""
    if valor is None:
        return []
    if isinstance(valor, str):
        return [(valor.strip(), 0.0, duracao)] if valor.strip() else []
    itens = [v for v in valor if (_txt(v.get("texto")) if isinstance(v, dict) else _txt(v))]
    n = len(itens)
    saida = []
    for i, v in enumerate(itens):
        ini_pad, fim_pad = duracao * i / n, duracao * (i + 1) / n
        if isinstance(v, dict):
            ini = float(v.get("inicio", ini_pad) if v.get("inicio") is not None else ini_pad)
            fim = float(v.get("fim", fim_pad) if v.get("fim") is not None else fim_pad)
            texto = _txt(v.get("texto"))
        else:
            ini, fim, texto = ini_pad, fim_pad, _txt(v)
        ini, fim = max(0.0, ini), min(duracao, fim)
        if fim > ini:
            saida.append((texto, ini, fim))
    return saida


def obter_legenda_auto(caminho_roteiro: Path | None, roteiro: dict, estilo: dict,
                       executor=None) -> str:
    """Pede a legenda ao `posts_futebol.py legenda_video` (existe no PC).

    Contrato assumido: recebe o caminho do roteiro JSON e imprime a legenda
    no stdout (texto puro ou JSON com a chave "legenda"). O comando pode ser
    trocado no estilo (campo legenda_auto_cmd) sem mexer no código.
    """
    script = Path(os.environ.get("HP_POSTS_FUTEBOL") or (AQUI / "posts_futebol.py"))
    if not script.exists():
        raise ErroReel(f"--legenda-auto: não achei {script} (defina HP_POSTS_FUTEBOL "
                       "ou preencha o campo 'legenda' no roteiro)")
    tmp = None
    if caminho_roteiro is None:
        pasta = garantir(raiz_local() / "app" / "tmp")
        fd, tmp = tempfile.mkstemp(prefix="roteiro_", suffix=".json", dir=pasta)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(roteiro, f, ensure_ascii=False)
        caminho_roteiro = Path(tmp)
    modelo = estilo.get("legenda_auto_cmd") or ESTILO_PADRAO["legenda_auto_cmd"]
    cmd = [str(p).format(python=sys.executable, script=str(script),
                         roteiro=str(caminho_roteiro)) for p in modelo]
    try:
        r = (executor or rodar)(cmd, timeout=120)
    finally:
        if tmp:
            Path(tmp).unlink(missing_ok=True)
    if r.returncode != 0:
        cauda = (r.stderr or b"").decode("utf-8", "replace").strip().splitlines()[-3:]
        raise ErroReel(f"posts_futebol.py legenda_video falhou (código {r.returncode}): "
                       + " | ".join(cauda))
    bruto = r.stdout or b""
    try:
        txt = bruto.decode("utf-8").strip()
    except UnicodeDecodeError:
        txt = bruto.decode("cp1252", "replace").strip()
    if txt.startswith("{"):
        try:
            d = json.loads(txt)
            txt = _txt(d.get("legenda") or d.get("legenda_video") or d.get("texto"))
        except json.JSONDecodeError:
            pass
    if not txt:
        raise ErroReel("posts_futebol.py legenda_video não devolveu texto")
    return txt


# ---------------------------------------------------------------- validação
class _Coletor:
    def __init__(self):
        self.erros: list[str] = []
        self.avisos: list[str] = []

    def erro(self, m: str) -> None:
        if m not in self.erros:
            self.erros.append(m)

    def aviso(self, m: str) -> None:
        if m not in self.avisos:
            self.avisos.append(m)


def _validar_video(c: _Coletor, v, onde: str, base: Path, conferir: bool) -> dict | None:
    if not isinstance(v, dict):
        c.erro(f"{onde}: falta o vídeo (objeto com arquivo, fonte_tipo e credito)")
        return None
    ft = _txt(v.get("fonte_tipo")).lower()
    if ft in FONTES_PROIBIDAS:
        c.erro(f"{onde}.fonte_tipo = '{ft}': imagem de transmissão de TV é proibida no "
               "futebol (só vídeo oficial publicado pelo clube, CBF ou liga)")
    elif ft not in FONTES_VIDEO_OK:
        c.erro(f"{onde}.fonte_tipo precisa ser um de {', '.join(FONTES_VIDEO_OK)} "
               f"(veio '{ft or 'vazio'}')")
    if not _txt(v.get("credito")):
        c.erro(f"{onde}: falta o crédito do vídeo (campo 'credito', ex.: \"@flamengo\")")
    if not _txt(v.get("arquivo")):
        c.erro(f"{onde}: falta o campo 'arquivo'")
        return None
    p = resolver(v["arquivo"], base)
    if not conferir:
        return None
    if not p.exists():
        c.erro(f"{onde}: arquivo não encontrado: {p}")
        return None
    try:
        info = info_midia(p)
    except ErroReel as e:
        c.erro(f"{onde}: {e}")
        return None
    if not info["tem_video"] or not info["largura"]:
        c.erro(f"{onde}: o arquivo não tem imagem de vídeo: {p.name}")
        return None
    for campo in ("inicio", "fim"):
        if v.get(campo) is not None and _num(v.get(campo)) is None:
            c.erro(f"{onde}.{campo} precisa ser número (segundos)")
            return info
    ini = _num(v.get("inicio")) or 0.0
    fim = _num(v.get("fim")) if v.get("fim") is not None else info["duracao"]
    if info["duracao"] and fim is not None:
        if ini < 0 or fim <= ini or fim > info["duracao"] + 0.05:
            c.erro(f"{onde}: trecho inválido (inicio {ini}, fim {fim}, vídeo tem "
                   f"{info['duracao']:.2f}s)")
            return info
    if not info["tem_audio"]:
        c.erro(f"{onde}: o vídeo não tem áudio — no futebol vai SEMPRE o áudio "
               "original do clube/CBF/liga (nunca mudo)")
    else:
        vol = medir_volume(p, ini, (fim - ini) if fim else None)
        if vol["pico_db"] < -60:
            c.erro(f"{onde}: o áudio original está mudo (pico {vol['pico_db']:.0f} dB)")
    return info


def _validar_foto(c: _Coletor, f, onde: str, base: Path, conferir: bool) -> None:
    if not isinstance(f, dict):
        c.erro(f"{onde}: foto precisa ser objeto com 'arquivo' e 'credito'")
        return
    if not _txt(f.get("credito")):
        c.erro(f"{onde}: falta o crédito da foto (campo 'credito')")
    ft = _txt(f.get("fonte_tipo")).lower()
    if ft and ft not in FONTES_PROIBIDAS and ft not in FONTES_FOTO_OK:
        c.erro(f"{onde}.fonte_tipo precisa ser um de {', '.join(FONTES_FOTO_OK)}")
    if not _txt(f.get("arquivo")):
        c.erro(f"{onde}: falta o campo 'arquivo'")
        return
    p = resolver(f["arquivo"], base)
    if conferir:
        if not p.exists():
            c.erro(f"{onde}: arquivo não encontrado: {p}")
        elif p.suffix.lower() not in EXTS_FOTO:
            c.erro(f"{onde}: foto precisa ser {', '.join(sorted(EXTS_FOTO))}")
        else:
            try:
                with Image.open(p) as im:
                    im.size
            except OSError:
                c.erro(f"{onde}: não consegui abrir a imagem {p.name}")


def _validar_time(c: _Coletor, t, onde: str, base: Path, conferir: bool) -> None:
    if not isinstance(t, dict) or not _txt(t.get("nome")):
        c.erro(f"{onde}: precisa de objeto com 'nome' e 'gols'")
        return
    g = t.get("gols")
    if isinstance(g, bool) or not isinstance(g, int) or g < 0:
        c.erro(f"{onde}.gols precisa ser número inteiro >= 0")
    if t.get("escudo") and conferir and not resolver(t["escudo"], base).exists():
        c.erro(f"{onde}.escudo: arquivo não encontrado")


def _validar_musica(c: _Coletor, r: dict, base: Path, estilo: dict, conferir: bool) -> None:
    m = r.get("musica")
    if not m:
        return
    if r.get("modo") == "gol":
        c.erro("gol: sem música — o gol usa só o áudio original do vídeo oficial "
               "(música por cima abafa o som do estádio)")
        return
    if not isinstance(m, dict) or not _txt(m.get("arquivo")):
        c.erro("musica: precisa ser objeto com 'arquivo'")
        return
    p = resolver_musica(m, base, estilo)
    if _raiz_musicas_livres(p) is None:
        c.erro(f"musica: só vale arquivo da pasta musicas_livres (veio {p})")
        return
    if conferir and not p.exists():
        c.erro(f"musica: arquivo não encontrado: {p}")
        return
    prob = problema_licenca(licenca_da_musica(p))
    if prob:
        c.erro(f"musica '{p.name}': {prob} — registre em musicas_livres/licencas.json "
               "(licenca, fonte, autor) ou não use")
    if conferir and p.exists():
        try:
            if not info_midia(p)["tem_audio"]:
                c.erro(f"musica '{p.name}': o arquivo não tem áudio")
        except ErroReel as e:
            c.erro(f"musica: {e}")


def _exigir_titulo(c: _Coletor, r: dict) -> None:
    if not _txt(r.get("titulo")):
        c.erro(f"{r.get('modo')}: título vazio (campo 'titulo')")


def _faixa(c: _Coletor, r: dict, campo: str, minimo: float, maximo: float) -> None:
    if campo in r:
        v = _num(r[campo])
        if v is None or not (minimo <= v <= maximo):
            c.erro(f"{campo} precisa estar entre {minimo} e {maximo} segundos")


def validar_roteiro(r: dict, base: Path, estilo: dict | None = None,
                    legenda_auto: bool = False, conferir_arquivos: bool = True):
    """Devolve (erros, avisos). Lista de erros vazia = pode montar."""
    c = _Coletor()
    estilo = estilo or ESTILO_PADRAO
    if not isinstance(r, dict):
        return ["roteiro precisa ser um objeto JSON"], []
    modo = _txt(r.get("modo")).lower()
    if modo not in MODOS:
        c.erro(f"modo precisa ser um de {', '.join(MODOS)} (veio '{modo or 'vazio'}')")
        return c.erros, c.avisos
    if _txt(r.get("canal")) and _txt(r.get("canal")).lower() != "futebol":
        c.erro("canal: este montador é só do Futebol | HP (canal 'futebol')")
    # regras que valem para o roteiro inteiro
    for cam, k, v in _varrer(r):
        kl = k.lower()
        if kl in CHAVES_VOZ and v not in (None, False, "", [], {}):
            c.erro(f"{cam}: futebol NUNCA leva narração/voz sintética — tire o campo '{k}'")
        if kl == "tipo" and _txt(v).lower() in TIPOS_VOZ:
            c.erro(f"{cam}: futebol NUNCA leva narração/voz sintética (tipo '{v}')")
        if kl == "fonte_tipo" and _txt(v).lower() in FONTES_PROIBIDAS:
            c.erro(f"{cam}: imagem de transmissão de TV é proibida no futebol "
                   "(só vídeo/foto oficial do clube, CBF ou liga)")
    _validar_musica(c, r, base, estilo, conferir_arquivos)
    if r.get("marca_dagua") is not None and not isinstance(r.get("marca_dagua"), str):
        c.erro("marca_dagua precisa ser texto")

    if modo == "gol":
        _validar_time(c, r.get("mandante"), "mandante", base, conferir_arquivos)
        _validar_time(c, r.get("visitante"), "visitante", base, conferir_arquivos)
        if _txt(r.get("time_do_gol")).lower() not in ("mandante", "visitante"):
            c.erro("time_do_gol precisa ser 'mandante' ou 'visitante'")
        if not _txt(r.get("autor")):
            c.erro("gol: falta o autor do gol (campo 'autor')")
        if not _txt(r.get("minuto")):
            c.erro("gol: falta o minuto (campo 'minuto', ex.: 67 ou \"45+2\")")
        _faixa(c, r, "duracao_cartao", 1.5, 3.0)
        _validar_video(c, r.get("video"), "video", base, conferir_arquivos)
        leg = r.get("legenda")
        if not legenda_auto and not normalizar_legendas(leg, 1.0):
            c.erro("gol: falta a legenda do vídeo (campo 'legenda') — ou use "
                   "--legenda-auto para pedir ao posts_futebol.py")
    elif modo == "noticia":
        _exigir_titulo(c, r)
        fotos = r.get("fotos")
        if not isinstance(fotos, list) or not 2 <= len(fotos) <= 4:
            c.erro("noticia: precisa de 2 a 4 fotos (campo 'fotos')")
        else:
            for i, f in enumerate(fotos):
                _validar_foto(c, f, f"fotos[{i}]", base, conferir_arquivos)
        if not normalizar_legendas(r.get("legendas"), 1.0):
            c.erro("noticia: falta a legenda queimada (campo 'legendas')")
        _faixa(c, r, "duracao_por_foto", 1.0, 10.0)
        if not r.get("musica"):
            c.aviso("noticia sem música: o reel vai sair só com silêncio")
    elif modo == "debate":
        _exigir_titulo(c, r)
        rec = r.get("recortes")
        if not isinstance(rec, list) or len(rec) != 3:
            c.erro("debate: precisa de exatamente 3 recortes (campo 'recortes')")
        else:
            for i, it in enumerate(rec):
                onde = f"recortes[{i}]"
                if not isinstance(it, dict):
                    c.erro(f"{onde}: precisa ser objeto")
                    continue
                if not _txt(it.get("nome")):
                    c.erro(f"{onde}: falta o nome do jogador")
                if not _txt(it.get("numero")):
                    c.erro(f"{onde}: falta o número (estatística) do jogador")
                tem_f, tem_c = bool(it.get("foto")), bool(it.get("clipe"))
                if tem_f == tem_c:
                    c.erro(f"{onde}: use 'foto' OU 'clipe' (um dos dois)")
                elif tem_f:
                    _validar_foto(c, it["foto"], f"{onde}.foto", base, conferir_arquivos)
                else:
                    _validar_video(c, it["clipe"], f"{onde}.clipe", base, conferir_arquivos)
        _faixa(c, r, "duracao_recorte", 1.0, 10.0)
        _faixa(c, r, "duracao_final", 1.0, 6.0)
    elif modo == "estatistica":
        _exigir_titulo(c, r)
        if _num(r.get("valor")) is None:
            c.erro("estatistica: 'valor' precisa ser número")
        if not _txt(r.get("rotulo")):
            c.erro("estatistica: falta o rótulo do número (campo 'rotulo')")
        cd = r.get("casas_decimais", 0)
        if isinstance(cd, bool) or not isinstance(cd, int) or not 0 <= cd <= 3:
            c.erro("casas_decimais precisa ser inteiro de 0 a 3")
        _faixa(c, r, "duracao", 2.0, 30.0)
        _faixa(c, r, "duracao_contagem", 0.5, 10.0)
        d = _num(r.get("duracao", PADROES["estatistica"]["duracao"])) or 0
        dc = _num(r.get("duracao_contagem", PADROES["estatistica"]["duracao_contagem"])) or 0
        if dc > d:
            c.erro("duracao_contagem não pode ser maior que duracao")
        if r.get("foto"):
            _validar_foto(c, r["foto"], "foto", base, conferir_arquivos)
    elif modo == "resultado":
        _validar_time(c, r.get("mandante"), "mandante", base, conferir_arquivos)
        _validar_time(c, r.get("visitante"), "visitante", base, conferir_arquivos)
        gols = r.get("gols", [])
        if not isinstance(gols, list):
            c.erro("gols precisa ser lista")
        else:
            conta = {"mandante": 0, "visitante": 0}
            for i, g in enumerate(gols):
                if not isinstance(g, dict):
                    c.erro(f"gols[{i}]: precisa ser objeto")
                    continue
                lado = _txt(g.get("time")).lower()
                if lado not in conta:
                    c.erro(f"gols[{i}].time precisa ser 'mandante' ou 'visitante'")
                else:
                    conta[lado] += 1
                if not _txt(g.get("autor")):
                    c.erro(f"gols[{i}]: falta o autor")
                if not _txt(g.get("minuto")):
                    c.erro(f"gols[{i}]: falta o minuto")
            for lado in conta:
                t = r.get(lado)
                if isinstance(t, dict) and isinstance(t.get("gols"), int) and gols \
                        and conta[lado] != t["gols"]:
                    c.erro(f"placar não bate: {lado} tem {t['gols']} gol(s) e a lista "
                           f"'gols' tem {conta[lado]}")
        _faixa(c, r, "duracao", 2.0, 30.0)
    elif modo == "tabela":
        _exigir_titulo(c, r)
        linhas = r.get("linhas")
        if not isinstance(linhas, list) or len(linhas) < 2:
            c.erro("tabela: precisa de pelo menos 2 linhas (campo 'linhas')")
        else:
            for i, ln in enumerate(linhas):
                if not isinstance(ln, dict) or not _txt(ln.get("time")) \
                        or _num(ln.get("pos")) is None or _num(ln.get("pts")) is None:
                    c.erro(f"linhas[{i}]: precisa de 'pos', 'time' e 'pts'")
        top = r.get("top")
        if top is not None and (isinstance(top, bool) or not isinstance(top, int)
                                or not 2 <= top <= 20):
            c.erro("top precisa ser inteiro de 2 a 20")
        _faixa(c, r, "duracao", 2.0, 30.0)
    return c.erros, c.avisos


# ---------------------------------------------------------------- normalizar
def normalizar(r: dict, base: Path, estilo: dict) -> dict:
    """Aplica os padrões e troca caminhos relativos por absolutos."""
    modo = _txt(r["modo"]).lower()
    n = copy.deepcopy(PADROES.get(modo, {}))
    n.update(copy.deepcopy(r))
    n["modo"] = modo
    if n.get("musica"):
        n["musica"]["arquivo"] = str(resolver_musica(r["musica"], base, estilo))
    _absolutos(n, base)
    return n


def _absolutos(obj, base: Path) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("arquivo", "escudo") and isinstance(v, str) and v.strip():
                obj[k] = str(resolver(v, base))
            else:
                _absolutos(v, base)
    elif isinstance(obj, list):
        for v in obj:
            _absolutos(v, base)
