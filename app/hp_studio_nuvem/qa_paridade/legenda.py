"""Legendas: leitura de SRT, VTT e ASS/SSA (ou extraída do vídeo) e comparação.

Texto: similaridade por palavras (difflib) depois de normalizar acento,
caixa e pontuação ("Olá, Mundo!" == "ola mundo").
Tempos: blocos pareados (mesmo texto, ou substituição 1 para 1) e desvio
em ms do início e do fim.
"""
from __future__ import annotations

import difflib
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from .limites import nota_por_pontos
from .midia import EXT_LEGENDA, extrair_legenda_srt
from .util import br, metrica, nao_se_aplica, tempo_txt


@dataclass
class Bloco:
    inicio_ms: int
    fim_ms: int
    texto: str


# ---------------------------------------------------------------- leitura
_RX_SRT = re.compile(
    r"(?:(\d+):)?(\d{1,2}):(\d{2})[,.](\d{1,3})\s*-->\s*"
    r"(?:(\d+):)?(\d{1,2}):(\d{2})[,.](\d{1,3})")
_RX_TAG_HTML = re.compile(r"</?[a-zA-Z][^>]*>")
_RX_TAG_ASS = re.compile(r"\{[^}]*\}")
_RX_TEMPO_ASS = re.compile(r"(\d+):(\d{1,2}):(\d{1,2})(?:[.,](\d{1,3}))?")


def _ms(h, m, s, frac) -> int:
    frac = (frac or "0").ljust(3, "0")[:3]
    return ((int(h or 0) * 60 + int(m)) * 60 + int(s)) * 1000 + int(frac)


def _limpar_texto(t: str) -> str:
    t = _RX_TAG_ASS.sub("", t)
    t = _RX_TAG_HTML.sub("", t)
    t = t.replace("\\N", " ").replace("\\n", " ").replace("\\h", " ")
    return " ".join(t.split())


def ler_srt_texto(texto: str) -> list[Bloco]:
    """SRT e WebVTT: bloco = linha de tempo + linhas de texto até linha vazia."""
    blocos: list[Bloco] = []
    atual: Bloco | None = None
    linhas_txt: list[str] = []

    def fechar():
        nonlocal atual, linhas_txt
        if atual is not None:
            atual.texto = _limpar_texto(" ".join(linhas_txt))
            blocos.append(atual)
        atual, linhas_txt = None, []

    for linha in texto.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        m = _RX_SRT.search(linha)
        if m:
            fechar()
            g = m.groups()
            atual = Bloco(_ms(*g[0:4]), _ms(*g[4:8]), "")
        elif not linha.strip():
            fechar()
        elif atual is not None:
            linhas_txt.append(linha.strip())
    fechar()
    return blocos


def _tempo_ass(txt: str) -> int:
    m = _RX_TEMPO_ASS.search(txt)
    if not m:
        raise ValueError(f"tempo ASS inválido: {txt!r}")
    return _ms(*m.groups())  # "0:00:01.50" = 1,5 s (fração decimal)


def ler_ass_texto(texto: str) -> list[Bloco]:
    """ASS/SSA: linhas Dialogue da seção [Events], na ordem do Format."""
    campos = ["layer", "start", "end", "style", "name", "marginl", "marginr",
              "marginv", "effect", "text"]
    em_eventos = False
    blocos: list[Bloco] = []
    for linha in texto.replace("\r\n", "\n").split("\n"):
        l = linha.strip()
        if l.startswith("[") and l.endswith("]"):
            em_eventos = l.lower() == "[events]"
            continue
        if not em_eventos:
            continue
        if l.lower().startswith("format:"):
            campos = [c.strip().lower() for c in l.split(":", 1)[1].split(",")]
        elif l.lower().startswith("dialogue:"):
            partes = l.split(":", 1)[1].split(",", len(campos) - 1)
            if len(partes) < len(campos):
                continue
            d = dict(zip(campos, partes))
            try:
                blocos.append(Bloco(_tempo_ass(d["start"]), _tempo_ass(d["end"]),
                                    _limpar_texto(d.get("text", ""))))
            except (KeyError, ValueError):
                continue
    blocos.sort(key=lambda b: (b.inicio_ms, b.fim_ms))
    return blocos


def _ler_texto_arquivo(p: Path) -> str:
    dados = p.read_bytes()
    if dados[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return dados.decode("utf-16")
    try:
        return dados.decode("utf-8-sig")
    except UnicodeDecodeError:
        return dados.decode("cp1252", errors="replace")  # legenda salva no Bloco de Notas antigo


def ler_legenda(caminho) -> list[Bloco]:
    """Lê .srt/.vtt/.ass/.ssa; se for vídeo, extrai a 1ª faixa de legenda."""
    p = Path(caminho)
    if not p.is_file():
        raise FileNotFoundError(f"legenda não encontrada: {p}")
    ext = p.suffix.lower()
    if ext not in EXT_LEGENDA:
        srt = extrair_legenda_srt(p)
        if srt is None:
            raise ValueError(f"{p.name} não tem faixa de legenda")
        return ler_srt_texto(srt)
    texto = _ler_texto_arquivo(p)
    if ext in (".ass", ".ssa") or "[events]" in texto.lower():
        return ler_ass_texto(texto)
    return ler_srt_texto(texto)


# ---------------------------------------------------------------- comparação
def normalizar(texto: str) -> str:
    """Sem acento, minúsculo, sem pontuação, espaços únicos."""
    t = unicodedata.normalize("NFKD", texto)
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    t = re.sub(r"[^\w\s]", " ", t).replace("_", " ")
    return " ".join(t.split())


def parear_blocos(app: list[Bloco], ref: list[Bloco]) -> list[tuple[int, int]]:
    """Pares (i_app, j_ref): blocos de texto igual e substituições 1 para 1."""
    ta = [normalizar(b.texto) for b in app]
    tr = [normalizar(b.texto) for b in ref]
    pares = []
    sm = difflib.SequenceMatcher(None, ta, tr, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op in ("equal", "replace"):
            pares.extend(zip(range(i1, i2), range(j1, j2)))
    return pares


def _diferencas_texto(pa: list[str], pr: list[str], maximo: int = 5) -> list[dict]:
    saida = []
    sm = difflib.SequenceMatcher(None, pa, pr, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            continue
        saida.append({"tipo": {"replace": "trocado", "delete": "sobrando no app",
                               "insert": "faltando no app"}[op],
                      "app": " ".join(pa[i1:i2])[:120], "ref": " ".join(pr[j1:j2])[:120]})
        if len(saida) >= maximo:
            break
    return saida


def comparar_blocos(app: list[Bloco], ref: list[Bloco], lim: dict) -> dict:
    """Métrica 'legenda' a partir de duas listas de blocos."""
    cfg = lim["legenda"]
    if not app and not ref:
        return nao_se_aplica("legenda", "as duas legendas estão vazias")
    if not app or not ref:
        quem = "app" if not app else "referência"
        return metrica("legenda", {"blocos": 0.0},
                       {"blocos_app": len(app), "blocos_ref": len(ref)},
                       f"legenda vazia no {quem}", nota_forcada=0.0)
    pa = normalizar(" ".join(b.texto for b in app)).split()
    pr = normalizar(" ".join(b.texto for b in ref)).split()
    sim = 1.0 if not pa and not pr else difflib.SequenceMatcher(
        None, pa, pr, autojunk=False).ratio()

    pares = parear_blocos(app, ref)
    desvios_ini = [abs(app[i].inicio_ms - ref[j].inicio_ms) for i, j in pares]
    desvios_fim = [abs(app[i].fim_ms - ref[j].fim_ms) for i, j in pares]
    todos = desvios_ini + desvios_fim
    medio = sum(todos) / len(todos) if todos else 0.0
    maximo = max(todos) if todos else 0
    piores = sorted(pares, key=lambda p: -max(abs(app[p[0]].inicio_ms - ref[p[1]].inicio_ms),
                                               abs(app[p[0]].fim_ms - ref[p[1]].fim_ms)))[:3]
    dif_blocos = abs(len(app) - len(ref))

    sub = {"texto": nota_por_pontos(sim, cfg["pontos_texto"]),
           "tempo_medio": nota_por_pontos(medio, cfg["pontos_desvio_medio_ms"]),
           "tempo_maximo": nota_por_pontos(maximo, cfg["pontos_desvio_maximo_ms"]),
           "blocos": nota_por_pontos(dif_blocos, cfg["pontos_blocos"])}
    if not pares:
        sub["tempo_medio"] = sub["tempo_maximo"] = 0.0
    detalhes = {
        "similaridade_texto": round(sim, 4),
        "palavras_app": len(pa), "palavras_ref": len(pr),
        "blocos_app": len(app), "blocos_ref": len(ref),
        "blocos_pareados": len(pares),
        "desvio_medio_ms": round(medio, 1), "desvio_maximo_ms": int(maximo),
        "desvio_inicio_medio_ms": round(sum(desvios_ini) / len(desvios_ini), 1) if desvios_ini else None,
        "desvio_fim_medio_ms": round(sum(desvios_fim) / len(desvios_fim), 1) if desvios_fim else None,
        "piores_blocos": [{"bloco_app": i + 1, "bloco_ref": j + 1,
                           "inicio_app": tempo_txt(app[i].inicio_ms / 1000),
                           "inicio_ref": tempo_txt(ref[j].inicio_ms / 1000),
                           "desvio_inicio_ms": app[i].inicio_ms - ref[j].inicio_ms,
                           "desvio_fim_ms": app[i].fim_ms - ref[j].fim_ms,
                           "texto_ref": ref[j].texto[:80]} for i, j in piores],
        "diferencas_texto": _diferencas_texto(pa, pr),
    }
    resumo = (f"texto {br(sim * 100, 1)}% igual; desvio médio {br(medio, 0)} ms, "
              f"máximo {maximo} ms; blocos {len(app)} x {len(ref)}")
    return metrica("legenda", sub, detalhes, resumo)


def comparar_arquivos_legenda(app, ref, lim: dict) -> dict:
    return comparar_blocos(ler_legenda(app), ler_legenda(ref), lim)
