"""Exportação resumida para o painel: H:\\HypadoLocal\\metricas\\metricas_painel.json.

Estrutura (o painel_local.py lê só isto; ver LEIA.md):
{
  "versao": 1, "gerado_em": "...", "data": "AAAA-MM-DD", "coletado_em": "...",
  "totais": {"seguidores": N, "delta_dia": N},
  "contas": {"gta": {"nome": "GTA 6 | HP", "seguidores_total": N, "delta_dia_total": N,
             "redes": {"instagram": {"status", "fonte", "seguidores", "delta_dia", "delta_7d",
                                     "views_24h", "posts_24h", "taxa_engajamento", "coletado_em"}},
             "top_24h": [...], "top_7d": [...]}},
  "top_posts": {"24h": [5 posts], "7d": [5 posts]}
}
"""
from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from hpbase import agora as agora_brasilia, agora_iso, escrever_json

from .modelos import ler_data

ARQUIVO = "metricas_painel.json"
CAMPOS_TOP = ("id", "legenda_inicio", "tipo", "publicado_em", "link", "views",
              "curtidas", "comentarios")


def _n(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _dentro(p: dict, ref, dias: int) -> bool:
    d = ler_data(p.get("publicado_em"))
    return bool(d and ref - timedelta(days=dias) <= d <= ref + timedelta(hours=1))


def top(posts: list, ref, dias: int, n: int = 5) -> list:
    cand = [p for p in posts if _n(p.get("views")) is not None and _dentro(p, ref, dias)]
    cand.sort(key=lambda p: (p["views"], p.get("publicado_em") or ""), reverse=True)
    return cand[:n]


def _soma(vals):
    vals = [v for v in vals if _n(v) is not None]
    return sum(vals) if vals else None


def montar(foto: dict, cfg: dict | None = None) -> dict:
    ref = ler_data(foto.get("coletado_em")) or agora_brasilia()
    nomes = {c: (v or {}).get("nome", c) for c, v in ((cfg or {}).get("contas") or {}).items()}
    analise = foto.get("analise") or {}
    contas, todos = {}, []
    for conta, redes in (foto.get("contas") or {}).items():
        saida = {"nome": nomes.get(conta, conta), "redes": {}}
        posts_conta = []
        for rede, r in (redes or {}).items():
            if not isinstance(r, dict):
                continue
            a = (analise.get(conta) or {}).get(rede) or {}
            posts = r.get("posts") or []
            p24 = [p for p in posts if _dentro(p, ref, 1)]
            saida["redes"][rede] = {
                "status": r.get("status"), "fonte": r.get("fonte", "api"),
                "seguidores": r.get("seguidores"), "delta_dia": a.get("delta_dia"),
                "delta_7d": a.get("delta_7d"),
                "views_24h": _soma(p.get("views") for p in p24), "posts_24h": len(p24),
                "taxa_engajamento": (r.get("totais") or {}).get("taxa_engajamento"),
                "coletado_em": r.get("coletado_em")}
            for p in posts:
                posts_conta.append({**{k: p.get(k) for k in CAMPOS_TOP},
                                    "conta": conta, "rede": rede})
        saida["seguidores_total"] = _soma(r["seguidores"] for r in saida["redes"].values())
        saida["delta_dia_total"] = _soma(r["delta_dia"] for r in saida["redes"].values())
        saida["top_24h"] = top(posts_conta, ref, 1)
        saida["top_7d"] = top(posts_conta, ref, 7)
        contas[conta] = saida
        todos += posts_conta
    return {
        "versao": 1, "gerado_em": agora_iso(), "data": foto.get("data"),
        "coletado_em": foto.get("coletado_em"),
        "totais": {"seguidores": _soma(c["seguidores_total"] for c in contas.values()),
                   "delta_dia": _soma(c["delta_dia_total"] for c in contas.values())},
        "contas": contas,
        "top_posts": {"24h": top(todos, ref, 1), "7d": top(todos, ref, 7)},
    }


def exportar(foto: dict, pasta: Path, cfg: dict | None = None) -> Path:
    return escrever_json(Path(pasta) / ARQUIVO, montar(foto, cfg))
