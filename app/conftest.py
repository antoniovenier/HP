"""Configuração comum dos testes: nada toca no H: nem no G: de verdade."""
import sys
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
for p in (AQUI, AQUI / "hp_studio", AQUI.parent / "scripts"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


@pytest.fixture(autouse=True)
def raizes_temporarias(tmp_path, monkeypatch):
    local = tmp_path / "HypadoLocal"
    drive = tmp_path / "Drive"
    local.mkdir()
    drive.mkdir()
    monkeypatch.setenv("HP_LOCAL", str(local))
    monkeypatch.setenv("HP_DRIVE", str(drive))
    return local, drive
