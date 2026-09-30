"""Contas para o Analista de resultados (manual 11).

- taxa de engajamento = (curtidas + comentários + salvamentos + compartilhamentos) / alcance
- delta de seguidores no dia (vs ontem) e em 7 dias (vs a foto de 7 dias atrás)
- média de views por formato (reels, carrossel, shorts...) e por hora de publicação
  (hora de Brasília), juntando os posts das fotos dos últimos 30 dias.
"""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from hpbase import ler_json

from .modelos import METRICAS_POST, ler_data

INTERACOES = ("curtidas", "comentarios", "salvamentos", "compartilhamentos")
DIAS_HISTORICO = 30


def _n(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def taxa_engajamento(post: dict) -> float | None:
    alcance = _n(post.get("alcance"))
    if not alcance:
        return None
    inter = sum(_n(post.get(k)) or 0 for k in INTERACOES)
    return round(inter / alcance, 4)


def totais(posts: list) -> dict:
    t = {"posts": len(posts)}
    for k in METRICAS_POST:
        vals = [_n(p.get(k)) for p in posts if _n(p.get(k)) is not None]
        t[k] = sum(vals) if vals else None
    com_alcance = [p for p in posts if _n(p.get("alcance"))]
    if com_alcance:
        inter = sum(sum(_n(p.get(k)) or 0 for k in INTERACOES) for p in com_alcance)
        t["taxa_engajamento"] = round(inter / sum(p["alcance"] for p in com_alcance), 4)
    else:
        t["taxa_engajamento"] = None
    return t


def ler_foto(pasta: Path, dia: date) -> dict | None:
    return ler_json(Path(pasta) / f"{dia.isoformat()}.json", None)


def rede_da_foto(foto, conta: str, rede: str) -> dict:
    return (((foto or {}).get("contas") or {}).get(conta) or {}).get(rede) or {}


def seguidores(foto, conta: str, rede: str):
    return _n(rede_da_foto(foto, conta, rede).get("seguidores"))


def delta_seguidores(foto_hoje, foto_antes, conta: str, rede: str):
    a, b = seguidores(foto_hoje, conta, rede), seguidores(foto_antes, conta, rede)
    return None if a is None or b is None else a - b


def media_views_por(posts: list, chave) -> dict:
    grupos: dict = {}
    for p in posts:
        v, k = _n(p.get("views")), chave(p)
        if v is None or k is None:
            continue
        grupos.setdefault(k, []).append(v)
    return {k: {"media": round(sum(vs) / len(vs), 1), "posts": len(vs)}
            for k, vs in sorted(grupos.items())}


def views_por_formato(posts: list) -> dict:
    return media_views_por(posts, lambda p: p.get("tipo") or "outro")


def _hora(p):
    d = ler_data(p.get("publicado_em"))
    return f"{d.hour:02d}h" if d else None


def views_por_hora(posts: list) -> dict:
    return media_views_por(posts, _hora)


def carregar_fotos(pasta: Path, hoje: date, dias: int, foto_hoje=None) -> dict:
    fotos = {}
    for i in range(dias, -1, -1):
        d = hoje - timedelta(days=i)
        f = foto_hoje if (i == 0 and foto_hoje is not None) else ler_foto(pasta, d)
        if f:
            fotos[d] = f
    return fotos


def posts_historicos(fotos: dict, conta: str, rede: str) -> list:
    """Posts de todas as fotos; o mesmo post fica com os números da foto mais nova."""
    vistos = {}
    for d in sorted(fotos):
        for p in rede_da_foto(fotos[d], conta, rede).get("posts") or []:
            if p.get("id") is not None:
                vistos[p["id"]] = p
    return list(vistos.values())


def analise(foto: dict, pasta: Path, dias_hist: int = DIAS_HISTORICO) -> dict:
    hoje = date.fromisoformat(foto["data"])
    fotos = carregar_fotos(pasta, hoje, max(dias_hist, 7), foto)
    ontem, semana = fotos.get(hoje - timedelta(days=1)), fotos.get(hoje - timedelta(days=7))
    fotos_hist = {d: f for d, f in fotos.items() if d >= hoje - timedelta(days=dias_hist)}
    out: dict = {}
    for conta, redes in (foto.get("contas") or {}).items():
        for rede, r in (redes or {}).items():
            if not isinstance(r, dict):
                continue
            hist = posts_historicos(fotos_hist, conta, rede)
            out.setdefault(conta, {})[rede] = {
                "seguidores": seguidores(foto, conta, rede),
                "delta_dia": delta_seguidores(foto, ontem, conta, rede),
                "delta_7d": delta_seguidores(foto, semana, conta, rede),
                "taxa_engajamento": totais(r.get("posts") or [])["taxa_engajamento"],
                "views_por_formato": views_por_formato(hist),
                "views_por_hora": views_por_hora(hist),
                "posts_no_historico": len(hist),
            }
    return out
