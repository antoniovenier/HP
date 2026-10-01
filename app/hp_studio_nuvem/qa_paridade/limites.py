"""Limites configuráveis (limites.json) e a conta de nota por pontos."""
from __future__ import annotations

import copy
from pathlib import Path

from hpbase import ler_json, pasta_paridade

PADRAO = Path(__file__).with_name("limites.json")


def arquivo_local() -> Path:
    """Ajuste local opcional: H:\\HypadoLocal\\app\\paridade_nuvem\\limites.json (hpbase.pasta_paridade)."""
    return pasta_paridade() / "limites.json"


def _limpar(d):
    """Tira as chaves de comentário (começam com _)."""
    if isinstance(d, dict):
        return {k: _limpar(v) for k, v in d.items() if not str(k).startswith("_")}
    return d


def _mesclar(base: dict, extra: dict) -> dict:
    for k, v in (extra or {}).items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _mesclar(base[k], v)
        else:
            base[k] = copy.deepcopy(v)
    return base


def carregar_limites(caminho: str | Path | None = None, extra: dict | None = None) -> dict:
    """Padrão do pacote + ajuste local (se existir) + arquivo/dict pedido."""
    lim = _limpar(ler_json(PADRAO))
    for p in (arquivo_local(), Path(caminho) if caminho else None):
        if p and Path(p).is_file():
            _mesclar(lim, _limpar(ler_json(p, {})))
    if extra:
        _mesclar(lim, _limpar(extra))
    return lim


def nota_por_pontos(valor: float, pontos) -> float:
    """Interpola a nota entre pontos [valor, nota] (ordenados pelo valor).

    Serve para "quanto maior melhor" (SSIM) e "quanto menor melhor"
    (diferença): fora da faixa vale a nota da ponta mais próxima.
    """
    pts = sorted((float(x), float(n)) for x, n in pontos)
    if not pts:
        raise ValueError("lista de pontos vazia")
    v = float(valor)
    if v <= pts[0][0]:
        return round(pts[0][1], 2)
    if v >= pts[-1][0]:
        return round(pts[-1][1], 2)
    for (x0, n0), (x1, n1) in zip(pts, pts[1:]):
        if x0 <= v <= x1:
            if x1 == x0:
                return round(min(n0, n1), 2)
            return round(n0 + (n1 - n0) * (v - x0) / (x1 - x0), 2)
    return round(pts[-1][1], 2)  # não chega aqui
