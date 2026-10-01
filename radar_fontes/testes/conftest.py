"""Põe radar_fontes\\ e app\\hp_studio_nuvem\\ no sys.path (sem depender do conftest de tests/).

Nenhum teste desta pasta toca rede: todo acesso passa por um `transporte` falso
(função url -> (status, bytes, cabeçalhos)) e a data de hoje é injetada (`hoje=`).
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
for _p in (RAIZ / "radar_fontes", RAIZ / "app" / "hp_studio_nuvem"):
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
