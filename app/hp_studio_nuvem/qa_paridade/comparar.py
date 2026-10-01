"""As comparações completas: vídeo, imagem, lâminas e legenda.

Cada função devolve o relatório (dict) montado por `relatorio.montar`.
O trabalho de vídeo (decodificar quadros e medir loudness) roda dentro da
`TravaPesada("qa_paridade")`: 1 trabalho pesado por vez e nunca das 18h às
22h30. Nos testes dá para desligar a trava (`usar_trava=False`) ou fixar a
hora (`agora=`).
"""
from __future__ import annotations

import contextlib
from datetime import datetime
from pathlib import Path

import numpy as np

from hpbase import TravaPesada, obter_logger

from . import relatorio
from .legenda import comparar_blocos, ler_legenda, ler_srt_texto
from .limites import carregar_limites, nota_por_pontos
from .loudness import medir_loudness, metrica_loudness
from .midia import (InfoMidia, dimensoes_imagem, extrair_legenda_srt, extrair_quadros,
                    info_midia, ler_imagem_cinza, tamanho_reduzido, tempos_das_amostras)
from .laminas import comparar_pastas
from .ssim import pior_regiao, ssim_mapa
from .util import br, metrica, nao_se_aplica, tempo_txt

DONO_TRAVA = "qa_paridade"


def _log():
    return obter_logger("qa_paridade")


# ---------------------------------------------------------------- métricas
def metrica_duracao(dur_app: float | None, dur_ref: float | None, lim: dict) -> dict:
    if dur_app is None or dur_ref is None:
        return nao_se_aplica("duracao", "duração desconhecida")
    dif = abs(dur_app - dur_ref)
    nota = nota_por_pontos(dif, lim["duracao"]["pontos"])
    sinal = "mais longo" if dur_app > dur_ref else "mais curto"
    resumo = (f"app {br(dur_app, 2)} s x ref {br(dur_ref, 2)} s"
              + (f" (app {br(dif, 2)} s {sinal})" if dif > 0.005 else " (iguais)"))
    return metrica("duracao", {"diferenca": nota},
                   {"app_s": dur_app, "ref_s": dur_ref, "diferenca_s": round(dif, 3)}, resumo)


def metrica_formato(ia: InfoMidia, ir: InfoMidia, lim: dict, video: bool = True) -> dict:
    cfg = lim["formato"]
    sub, avisos = {}, []
    iguais_dim = (ia.largura, ia.altura) == (ir.largura, ir.altura)
    sub["resolucao"] = 10.0 if iguais_dim else float(cfg["nota_resolucao_diferente"])
    if not iguais_dim:
        avisos.append(f"resolução {ia.largura}x{ia.altura} x {ir.largura}x{ir.altura}")
    if video:
        if ia.fps and ir.fps and abs(ia.fps - ir.fps) > float(cfg["tolerancia_fps"]):
            sub["fps"] = float(cfg["nota_fps_diferente"])
            avisos.append(f"fps {br(ia.fps, 2)} x {br(ir.fps, 2)}")
        else:
            sub["fps"] = 10.0
        if ia.tem_audio != ir.tem_audio:
            sub["audio"] = float(cfg["nota_audio_diferente"])
            avisos.append("áudio só no " + ("app" if ia.tem_audio else "referência"))
        else:
            sub["audio"] = 10.0
    detalhes = {"app": f"{ia.largura}x{ia.altura}" + (f" {br(ia.fps, 2)} fps" if video and ia.fps else ""),
                "ref": f"{ir.largura}x{ir.altura}" + (f" {br(ir.fps, 2)} fps" if video and ir.fps else ""),
                "diferencas": avisos}
    return metrica("formato", sub, detalhes, "; ".join(avisos) if avisos else "iguais")


def _nota_ssim(valores: list[float], lim: dict) -> tuple[dict, float, float]:
    cfg = lim["ssim"]
    media = float(np.mean(valores))
    minimo = float(np.min(valores))
    sub = {"media": nota_por_pontos(media, cfg["pontos_media"]),
           "pior_quadro": nota_por_pontos(minimo, cfg["pontos_minimo"])}
    return sub, media, minimo


def metrica_ssim_video(app, ref, ia: InfoMidia, ir: InfoMidia, lim: dict) -> dict:
    cfg = lim["ssim"]
    if not (ia.tem_video and ir.tem_video):
        if ia.tem_video == ir.tem_video:
            return nao_se_aplica("ssim", "nenhum dos dois tem imagem")
        return metrica("ssim", {"video": 0.0}, {}, "um dos dois não tem imagem",
                       nota_forcada=0.0)
    duracoes = [d for d in (ia.duracao, ir.duracao) if d]
    comum = min(duracoes) if duracoes else 1.0
    n = int(round(comum * float(cfg["quadros_por_segundo"])))
    n = max(int(cfg["min_quadros"]), min(int(cfg["max_quadros"]), n))
    passo = comum / n
    w, h = tamanho_reduzido(ir.largura, ir.altura, int(cfg["lado_max"]))
    qa = extrair_quadros(app, w, h, passo, n)
    qr = extrair_quadros(ref, w, h, passo, n)
    k = min(len(qa), len(qr))
    if k == 0:
        return metrica("ssim", {"quadros": 0.0}, {"quadros_app": len(qa), "quadros_ref": len(qr)},
                       "não saiu nenhum quadro para comparar", nota_forcada=0.0)
    tempos = tempos_das_amostras(passo, k)
    valores, regioes = [], []
    for a, r in zip(qa[:k], qr[:k]):
        mapa = ssim_mapa(a, r, int(cfg["janela"]), float(cfg["sigma"]))
        valores.append(float(mapa.mean()))
        regioes.append(pior_regiao(mapa))
    sub, media, minimo = _nota_ssim(valores, lim)
    ordem = sorted(range(k), key=lambda i: valores[i])[:int(cfg["piores"])]
    detalhes = {
        "quadros_comparados": k, "passo_s": round(passo, 3),
        "tamanho_comparado": f"{w}x{h}",
        "media": round(media, 4), "minimo": round(minimo, 4),
        "piores_quadros": [{"tempo_s": tempos[i], "tempo": tempo_txt(tempos[i]),
                            "ssim": round(valores[i], 4), "pior_regiao": regioes[i]}
                           for i in ordem],
        "por_quadro": [{"tempo_s": t, "ssim": round(v, 4)} for t, v in zip(tempos, valores)],
    }
    pior = detalhes["piores_quadros"][0]
    if minimo >= 0.9999:
        resumo = f"média {br(media, 4)}; nenhum quadro diferente; {k} quadros"
    else:
        resumo = (f"média {br(media, 3)}, pior {br(minimo, 3)} em {pior['tempo']} "
                  f"({pior['pior_regiao']}); {k} quadros")
    return metrica("ssim", sub, detalhes, resumo)


def metrica_ssim_imagem(app, ref, lim: dict) -> tuple[dict, tuple, tuple]:
    dims_a = dimensoes_imagem(app)
    dims_r = dimensoes_imagem(ref)
    w, h = tamanho_reduzido(*dims_r, lado_max=int(lim["imagem"]["lado_max"]))
    a = ler_imagem_cinza(app, w, h)
    r = ler_imagem_cinza(ref, w, h)
    mapa = ssim_mapa(a, r, int(lim["ssim"]["janela"]), float(lim["ssim"]["sigma"]))
    valor = float(mapa.mean())
    sub, _, _ = _nota_ssim([valor], lim)
    regiao = pior_regiao(mapa)
    m = metrica("ssim", sub, {"ssim": round(valor, 4), "pior_regiao": regiao,
                              "tamanho_comparado": f"{w}x{h}"},
                f"SSIM {br(valor, 4)} (pior região: {regiao})")
    return m, dims_a, dims_r


# ---------------------------------------------------------------- legenda do vídeo
def _legenda_do_video(info: InfoMidia, arquivo) -> list | None:
    if not info.tem_legenda:
        return None
    srt = extrair_legenda_srt(arquivo)
    return ler_srt_texto(srt) if srt else None


def _metrica_legenda_video(app, ref, ia, ir, legenda_app, legenda_ref, lim) -> dict:
    blocos_app = ler_legenda(legenda_app) if legenda_app else _legenda_do_video(ia, app)
    blocos_ref = ler_legenda(legenda_ref) if legenda_ref else _legenda_do_video(ir, ref)
    if blocos_app is None and blocos_ref is None:
        return nao_se_aplica("legenda", "sem legenda em arquivo nem faixa de legenda")
    if blocos_app is None or blocos_ref is None:
        quem = "app" if blocos_app is None else "referência"
        return metrica("legenda", {"blocos": 0.0}, {}, f"sem legenda no {quem}",
                       nota_forcada=0.0)
    return comparar_blocos(blocos_app, blocos_ref, lim)


# ---------------------------------------------------------------- comparações
def _trava(usar_trava: bool, agora: datetime | None):
    if not usar_trava:
        return contextlib.nullcontext()
    return TravaPesada(DONO_TRAVA, agora=agora)


def comparar_video(app, ref, legenda_app=None, legenda_ref=None, limites: dict | None = None,
                   usar_trava: bool = True, agora: datetime | None = None) -> dict:
    """Vídeo do app x vídeo de referência (feito 100% pelo Claude)."""
    lim = limites or carregar_limites()
    for f in (app, ref, legenda_app, legenda_ref):
        if f and not Path(f).is_file():
            raise FileNotFoundError(f"arquivo não encontrado: {f}")
    with _trava(usar_trava, agora):
        ia = info_midia(app)
        ir = info_midia(ref)
        metricas = {
            "duracao": metrica_duracao(ia.duracao, ir.duracao, lim),
            "ssim": metrica_ssim_video(app, ref, ia, ir, lim),
            "loudness": metrica_loudness(medir_loudness(app) if ia.tem_audio else None,
                                         medir_loudness(ref) if ir.tem_audio else None, lim),
            "legenda": _metrica_legenda_video(app, ref, ia, ir, legenda_app, legenda_ref, lim),
            "formato": metrica_formato(ia, ir, lim, video=True),
        }
    entradas = {"app": {"arquivo": _abs(app), **_resumo_info(ia)},
                "ref": {"arquivo": _abs(ref), **_resumo_info(ir)}}
    if legenda_app or legenda_ref:
        entradas["legenda_app"] = _abs(legenda_app) if legenda_app else None
        entradas["legenda_ref"] = _abs(legenda_ref) if legenda_ref else None
    rel = relatorio.montar("video", entradas, metricas, lim)
    _log().info("video %s x %s: %s nota %s", Path(app).name, Path(ref).name,
                rel["veredito"], rel["nota_final"])
    return rel


def _abs(p) -> str:
    return str(Path(p).resolve())


def _resumo_info(i: InfoMidia) -> dict:
    return {"duracao_s": i.duracao, "largura": i.largura, "altura": i.altura,
            "fps": i.fps, "tem_audio": i.tem_audio, "tem_legenda": i.tem_legenda}


def comparar_imagem(app, ref, limites: dict | None = None) -> dict:
    """Arte/lâmina única do app x referência."""
    lim = limites or carregar_limites()
    m_ssim, dims_a, dims_r = metrica_ssim_imagem(app, ref, lim)
    ia = InfoMidia(str(app), largura=dims_a[0], altura=dims_a[1])
    ir = InfoMidia(str(ref), largura=dims_r[0], altura=dims_r[1])
    metricas = {"ssim": m_ssim, "formato": metrica_formato(ia, ir, lim, video=False)}
    entradas = {"app": {"arquivo": _abs(app), "largura": dims_a[0], "altura": dims_a[1]},
                "ref": {"arquivo": _abs(ref), "largura": dims_r[0], "altura": dims_r[1]}}
    rel = relatorio.montar("imagem", entradas, metricas, lim)
    _log().info("imagem %s x %s: %s nota %s", Path(app).name, Path(ref).name,
                rel["veredito"], rel["nota_final"])
    return rel


def comparar_laminas(pasta_app, pasta_ref, limites: dict | None = None) -> dict:
    """Pasta de lâminas do app x pasta da referência."""
    lim = limites or carregar_limites()
    m_laminas, m_formato = comparar_pastas(pasta_app, pasta_ref, lim)
    entradas = {"app": {"pasta": _abs(pasta_app)}, "ref": {"pasta": _abs(pasta_ref)}}
    rel = relatorio.montar("laminas", entradas, {"laminas": m_laminas, "formato": m_formato}, lim)
    _log().info("laminas %s x %s: %s nota %s", Path(pasta_app).name, Path(pasta_ref).name,
                rel["veredito"], rel["nota_final"])
    return rel


def comparar_legenda(app, ref, limites: dict | None = None) -> dict:
    """Legenda do app x referência (.srt/.ass/.vtt ou vídeo com faixa de legenda)."""
    lim = limites or carregar_limites()
    m = comparar_blocos(ler_legenda(app), ler_legenda(ref), lim)
    entradas = {"app": {"arquivo": _abs(app)}, "ref": {"arquivo": _abs(ref)}}
    rel = relatorio.montar("legenda", entradas, {"legenda": m}, lim)
    _log().info("legenda %s x %s: %s nota %s", Path(app).name, Path(ref).name,
                rel["veredito"], rel["nota_final"])
    return rel
