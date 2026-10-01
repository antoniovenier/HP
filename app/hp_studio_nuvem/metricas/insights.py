"""Insights que toleram métrica não suportada.

A Graph API recusa o pedido inteiro (HTTP 400, código 100) quando UMA métrica
não vale para aquele tipo de mídia (ex.: story x reel x carrossel). Então:
1) pede todas; 2) se recusar, pede uma a uma e fica com as que vieram;
3) lembra, por tipo de mídia, quais foram recusadas, para não errar de novo
nos próximos posts do mesmo tipo.
"""
from __future__ import annotations

from .cliente import ErroAPI, ErroNaoAutorizado, ErroTemporario


def ler_valores(resp: dict) -> dict:
    """{"data":[{"name":..,"values":[{"value":N}]}]} ou total_value → {nome: N}."""
    out = {}
    for m in (resp or {}).get("data") or []:
        nome = m.get("name")
        if not nome:
            continue
        v = None
        if isinstance(m.get("total_value"), dict):
            v = m["total_value"].get("value")
        elif m.get("values"):
            v = (m["values"][-1] or {}).get("value")
        if isinstance(v, dict):  # métrica quebrada por tipo → soma
            v = sum(x for x in v.values() if isinstance(x, (int, float)))
        out[nome] = v
    return out


def _recusa(e: ErroAPI) -> bool:
    """Erro que significa 'essa métrica não serve aqui' (não é token nem rede)."""
    return (not isinstance(e, (ErroNaoAutorizado, ErroTemporario))
            and e.status == 400)


class InsightsTolerante:
    def __init__(self, cliente):
        self.cliente = cliente
        self.recusadas: dict[str, set] = {}

    def buscar(self, url: str, metricas, tipo: str, params: dict | None = None) -> dict:
        recusadas = self.recusadas.setdefault(tipo or "?", set())
        pedir = [m for m in metricas if m not in recusadas]
        if not pedir:
            return {}
        base = dict(params or {})
        try:
            return ler_valores(self.cliente.get(url, {**base, "metric": ",".join(pedir)}))
        except ErroAPI as e:
            if not _recusa(e):
                raise
            if len(pedir) == 1:
                recusadas.add(pedir[0])
                return {}
        valores, falhas = {}, []
        for m in pedir:
            try:
                valores.update(ler_valores(self.cliente.get(url, {**base, "metric": m})))
            except ErroAPI as e:
                if not _recusa(e):
                    raise
                falhas.append(m)
        # se TODAS falharam o problema é a mídia (ex.: antiga), não o tipo
        if valores:
            recusadas.update(falhas)
        return valores
