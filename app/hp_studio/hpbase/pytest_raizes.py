"""Fixture comum dos testes dos módulos novos: nada toca no H: nem no G: de verdade.

Cada pasta testes\\ dos módulos novos tem um conftest.py que põe o hp_studio no
sys.path e importa esta fixture (autouse). Assim não é preciso nenhum conftest.py
em app\\ — que o PC pode já ter, com os 53 testes da etapa 1.
"""
import pytest


@pytest.fixture(autouse=True)
def raizes_temporarias(tmp_path, monkeypatch):
    local = tmp_path / "HypadoLocal"
    drive = tmp_path / "Drive"
    local.mkdir(exist_ok=True)
    drive.mkdir(exist_ok=True)
    monkeypatch.setenv("HP_LOCAL", str(local))
    monkeypatch.setenv("HP_DRIVE", str(drive))
    return local, drive
