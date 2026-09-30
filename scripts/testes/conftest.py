"""Configuração comum dos testes dos scripts: nada toca no H: nem no G: de verdade.

No PC os scripts ficam em G:\\Meu Drive\\Hypado\\scripts e o app em
G:\\Meu Drive\\Hypado\\06 Projeto\\app — por isso este conftest procura o
hp_studio nos dois lugares (ou na variável HP_APP).
"""
import os
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent
_cands = [Path(os.environ["HP_APP"])] if os.environ.get("HP_APP") else []
_cands += [SCRIPTS.parent / "06 Projeto" / "app" / "hp_studio", SCRIPTS.parent / "app" / "hp_studio"]
for p in [SCRIPTS] + [c for c in _cands if c.exists()][:1]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


@pytest.fixture(autouse=True)
def raizes_temporarias(tmp_path, monkeypatch):
    local = tmp_path / "HypadoLocal"
    drive = tmp_path / "Drive"
    local.mkdir(exist_ok=True)
    drive.mkdir(exist_ok=True)
    monkeypatch.setenv("HP_LOCAL", str(local))
    monkeypatch.setenv("HP_DRIVE", str(drive))
    return local, drive
