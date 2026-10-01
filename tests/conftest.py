"""Testes de contrato com os formatos reais do PC (tests/fixtures/pc_real/).

Põe app\\hp_studio_nuvem, scripts\\ e radar_fontes\\ no sys.path e troca H:/G:
por pastas temporárias (fixture autouse de hpbase.pytest_raizes). Nenhum teste
aqui toca rede, adb, segredos nem relógio real.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
for _p in (RAIZ / "app" / "hp_studio_nuvem", RAIZ / "scripts", RAIZ / "radar_fontes"):
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from hpbase.pytest_raizes import raizes_temporarias  # noqa: E402,F401  (autouse)

PC_REAL = RAIZ / "tests" / "fixtures" / "pc_real"


@pytest.fixture
def pc_real() -> Path:
    """Pasta com as fixtures copiadas do PC (Seção 4 do prompt da rodada 2)."""
    return PC_REAL
