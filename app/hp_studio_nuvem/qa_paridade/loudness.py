"""Loudness integrado (LUFS) e true peak (dBTP) pelo ffmpeg.

Método principal: filtro `loudnorm` com `print_format=json` (só análise,
nada é gravado). Plano B: resumo do filtro `ebur128=peak=true`.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

from hpbase import achar_ffmpeg, rodar

from .limites import nota_por_pontos
from .util import br, metrica, nao_se_aplica

_RX_JSON = re.compile(r"\{[^{}]*\"input_i\"[^{}]*\}", re.S)
_RX_I = re.compile(r"\bI:\s*(-?inf|-?\d+(?:\.\d+)?)\s*LUFS")
_RX_PICO = re.compile(r"\bPeak:\s*(-?inf|-?\d+(?:\.\d+)?)\s*dBFS")
_RX_LRA = re.compile(r"\bLRA:\s*(-?inf|-?\d+(?:\.\d+)?)\s*LU\b")


def _num(txt) -> float | None:
    """Converte '-14.02' em número; '-inf'/'inf'/lixo viram None (silêncio)."""
    try:
        v = float(str(txt).strip())
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def interpretar_loudnorm(texto: str) -> dict | None:
    """Lê o JSON que o loudnorm imprime no stderr (o último, se houver vários)."""
    blocos = _RX_JSON.findall(texto)
    if not blocos:
        return None
    try:
        d = json.loads(blocos[-1])
    except json.JSONDecodeError:
        return None
    return {"integrado_lufs": _num(d.get("input_i")),
            "true_peak_dbtp": _num(d.get("input_tp")),
            "lra_lu": _num(d.get("input_lra")),
            "metodo": "loudnorm"}


def interpretar_ebur128(texto: str) -> dict | None:
    """Lê o resumo (Summary) do ebur128: pega o último I, LRA e Peak."""
    if "Summary" not in texto:
        return None
    resumo = texto[texto.rindex("Summary"):]
    i = _RX_I.findall(resumo)
    if not i:
        return None
    pico = _RX_PICO.findall(resumo)
    lra = _RX_LRA.findall(resumo)
    integrado = _num(i[-1])
    if integrado is not None and integrado <= -70.0:
        integrado = None  # o ebur128 marca silêncio como -70
    return {"integrado_lufs": integrado,
            "true_peak_dbtp": _num(pico[-1]) if pico else None,
            "lra_lu": _num(lra[-1]) if lra else None,
            "metodo": "ebur128"}


def medir_loudness(arquivo, ffmpeg: str | None = None, timeout: float = 900) -> dict | None:
    """LUFS integrado, true peak e LRA da 1ª faixa de áudio (None se não há áudio)."""
    ff = ffmpeg or achar_ffmpeg()
    base = [ff, "-hide_banner", "-nostdin", "-nostats", "-i", str(Path(arquivo)),
            "-map", "0:a:0", "-vn", "-sn", "-dn"]
    r = rodar(base + ["-af", "loudnorm=I=-14:TP=-1:LRA=11:print_format=json",
                      "-f", "null", "-"], timeout=timeout)
    medida = interpretar_loudnorm(r.stderr.decode("utf-8", errors="replace"))
    if medida is None:
        r = rodar(base + ["-af", "ebur128=peak=true", "-f", "null", "-"], timeout=timeout)
        medida = interpretar_ebur128(r.stderr.decode("utf-8", errors="replace"))
    return medida


def metrica_loudness(med_app: dict | None, med_ref: dict | None, lim: dict) -> dict:
    """Nota do áudio: diferença app x referência, distância do alvo e true peak."""
    cfg = lim["loudness"]
    if med_app is None and med_ref is None:
        return nao_se_aplica("loudness", "nenhum dos dois tem áudio")
    detalhes = {"app": med_app, "ref": med_ref, "alvo_lufs": cfg["alvo_lufs"]}
    if med_app is None or med_ref is None:
        quem = "app" if med_app is None else "referência"
        return metrica("loudness", {"audio": 0.0}, detalhes,
                       f"sem áudio no {quem}", nota_forcada=0.0)
    ia, ir = med_app.get("integrado_lufs"), med_ref.get("integrado_lufs")
    if ia is None and ir is None:
        return metrica("loudness", {"silencio": 10.0}, detalhes, "os dois em silêncio")
    if ia is None or ir is None:
        quem = "app" if ia is None else "referência"
        return metrica("loudness", {"audio": 0.0}, detalhes,
                       f"áudio mudo no {quem}", nota_forcada=0.0)
    dif = abs(ia - ir)
    sub = {"diferenca": nota_por_pontos(dif, cfg["pontos_diferenca"])}
    detalhes["diferenca_lu"] = round(dif, 2)
    if cfg.get("usar_alvo", True):
        dist = abs(ia - float(cfg["alvo_lufs"]))
        detalhes["distancia_alvo_app_lu"] = round(dist, 2)
        detalhes["distancia_alvo_ref_lu"] = round(abs(ir - float(cfg["alvo_lufs"])), 2)
        sub["alvo"] = nota_por_pontos(dist, cfg["pontos_alvo"])
    tp = med_app.get("true_peak_dbtp")
    if tp is not None:
        sub["true_peak"] = nota_por_pontos(tp, cfg["pontos_true_peak"])
    resumo = (f"app {br(ia, 1)} LUFS x ref {br(ir, 1)} LUFS "
              f"(diferença {br(dif, 1)} LU; alvo {br(cfg['alvo_lufs'], 0)})")
    if tp is not None:
        resumo += f"; pico app {br(tp, 1)} dBTP"
    return metrica("loudness", sub, detalhes, resumo)
