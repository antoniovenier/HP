"""A6 (§3.2): pesado.lock nos DOIS formatos (PC: {"quem","desde" ISO} sem pid, 30 min;
rodada 1: {"dono","pid","desde" epoch}, processo morto ou 3 h), trava ilegível pela data do
arquivo, relógio injetável, e as pastas da nuvem (esteira_sombra / paridade_nuvem)."""
import json
import os
from datetime import datetime, timedelta

import pytest

from hpbase import (TravaOcupada, TravaPesada, ler_trava, pasta_app, pasta_esteira,
                    pasta_paridade, raiz_local, trava_abandonada)

AGORA = datetime(2026, 10, 1, 10, 0)


def _lock(tmp_path, dados, mtime=None):
    p = tmp_path / "pesado.lock"
    p.write_text(dados if isinstance(dados, str) else json.dumps(dados), encoding="utf-8")
    if mtime is not None:
        os.utime(p, (mtime, mtime))
    return p


def _ler(p):
    return json.loads(p.read_text(encoding="utf-8"))


# --- formato do PC: {"quem", "desde": "AAAA-MM-DDTHH:MM"} ---------------------------------
def test_formato_do_pc_recente_ocupa_e_nao_quebra(tmp_path):
    p = _lock(tmp_path, {"quem": "cortar.py", "desde": "2026-10-01T09:45"})
    with pytest.raises(TravaOcupada, match="cortar.py"):
        TravaPesada("esteira:editar", caminho=p, agora=AGORA).adquirir()
    assert _ler(p) == {"quem": "cortar.py", "desde": "2026-10-01T09:45"}  # não mexeu


def test_formato_do_pc_sem_pid_vale_30_min(tmp_path):
    p = _lock(tmp_path, {"quem": "cortar.py", "desde": "2026-10-01T09:29"})  # 31 min
    with TravaPesada("eu", caminho=p, agora=AGORA):
        assert _ler(p)["quem"] == "eu"
    assert not p.exists()
    p = _lock(tmp_path, {"quem": "cortar.py", "desde": "2026-10-01T09:31"})  # 29 min
    with pytest.raises(TravaOcupada):
        TravaPesada("eu", caminho=p, agora=AGORA).adquirir()
    assert _ler(p)["quem"] == "cortar.py"


def test_desde_iso_completo_tambem_vale(tmp_path):
    p = _lock(tmp_path, {"quem": "x", "desde": "2026-10-01T09:50:00"})
    info = ler_trava(p)
    assert info["desde"] == datetime(2026, 10, 1, 9, 50) and info["legivel"] is True
    with pytest.raises(TravaOcupada):
        TravaPesada("eu", caminho=p, agora=AGORA).adquirir()


# --- formato da rodada 1: {"dono", "pid", "desde": epoch} ---------------------------------
def test_formato_antigo_com_pid_vivo_vale_3_h(tmp_path):
    quase = (AGORA - timedelta(hours=2, minutes=59)).timestamp()
    p = _lock(tmp_path, {"dono": "esteira:editar", "pid": os.getpid(), "desde": quase})
    with pytest.raises(TravaOcupada, match="esteira:editar"):
        TravaPesada("eu", caminho=p, agora=AGORA).adquirir()
    passou = (AGORA - timedelta(hours=3, minutes=1)).timestamp()
    p = _lock(tmp_path, {"dono": "esteira:editar", "pid": os.getpid(), "desde": passou})
    with TravaPesada("eu", caminho=p, agora=AGORA):
        assert _ler(p)["dono"] == "eu"


def test_formato_antigo_processo_morto_e_assumida(tmp_path):
    recente = (AGORA - timedelta(minutes=1)).timestamp()
    p = _lock(tmp_path, {"dono": "morto", "pid": 999999, "desde": recente})
    with TravaPesada("novo", caminho=p, agora=AGORA):
        assert _ler(p)["quem"] == "novo"
    assert not p.exists()


def test_epoch_absurdo_usa_a_data_do_arquivo_e_nao_quebra(tmp_path):
    p = _lock(tmp_path, {"dono": "outro", "pid": os.getpid(), "desde": 9e18},
              mtime=(AGORA - timedelta(minutes=5)).timestamp())
    info = ler_trava(p)
    assert info["legivel"] is False and info["desde"] == AGORA - timedelta(minutes=5)
    with pytest.raises(TravaOcupada, match="outro"):
        TravaPesada("eu", caminho=p, agora=AGORA).adquirir()


# --- trava ilegível -------------------------------------------------------------------------
def test_ilegivel_usa_mtime_e_nunca_vira_velha_de_graca(tmp_path):
    p = _lock(tmp_path, "{isso não é json", mtime=(AGORA - timedelta(minutes=5)).timestamp())
    info = ler_trava(p)
    assert info["quem"] == "?" and info["pid"] == 0 and info["legivel"] is False
    with pytest.raises(TravaOcupada):          # 5 min: continua ocupada
        TravaPesada("eu", caminho=p, agora=AGORA).adquirir()
    assert p.read_text(encoding="utf-8") == "{isso não é json"
    os.utime(p, ((AGORA - timedelta(minutes=31)).timestamp(),) * 2)
    with TravaPesada("eu", caminho=p, agora=AGORA):  # 31 min sem pid: abandonada
        assert _ler(p)["quem"] == "eu"


def test_trava_abandonada_regras():
    vivo = {"quem": "a", "pid": os.getpid(), "desde": AGORA - timedelta(hours=1)}
    assert trava_abandonada(vivo, AGORA) is False
    assert trava_abandonada({**vivo, "desde": AGORA - timedelta(hours=3, seconds=1)}, AGORA) is True
    assert trava_abandonada({**vivo, "pid": 999999}, AGORA) is True
    sem_pid = {"quem": "cortar.py", "pid": 0, "desde": AGORA - timedelta(minutes=29)}
    assert trava_abandonada(sem_pid, AGORA) is False
    assert trava_abandonada({**sem_pid, "desde": AGORA - timedelta(minutes=31)}, AGORA) is True
    futuro = {**sem_pid, "desde": AGORA + timedelta(days=3)}   # relógio adiantado: não é velha
    assert trava_abandonada(futuro, AGORA) is False


# --- o que gravamos -------------------------------------------------------------------------
def test_grava_os_dois_formatos(tmp_path):
    p = tmp_path / "pesado.lock"
    with TravaPesada("esteira:editar", caminho=p, agora=AGORA):
        d = _ler(p)
        assert d["quem"] == d["dono"] == "esteira:editar"
        assert d["desde"] == "2026-10-01T10:00" and d["pid"] == os.getpid()
        assert abs(d["desde_epoch"] - AGORA.timestamp()) < 1
        info = ler_trava(p)
        assert info["desde"] == AGORA and info["pid"] == os.getpid() and info["legivel"]
    assert not p.exists()


def test_relogio_injetavel_decide_a_idade(tmp_path):
    p = _lock(tmp_path, {"quem": "cortar.py", "desde": "2026-10-01T09:00"})
    with pytest.raises(TravaOcupada):
        TravaPesada("eu", caminho=p, agora=datetime(2026, 10, 1, 9, 20)).adquirir()
    with TravaPesada("eu", caminho=p, agora=datetime(2026, 10, 1, 9, 31)):
        pass
    assert not p.exists()


def test_soltar_nao_apaga_a_trava_de_outro(tmp_path):
    p = tmp_path / "pesado.lock"
    t = TravaPesada("eu", caminho=p, agora=AGORA)
    t.adquirir()
    p.write_text(json.dumps({"quem": "cortar.py", "desde": "2026-10-01T10:01"}), encoding="utf-8")
    t.soltar()
    assert p.exists() and _ler(p)["quem"] == "cortar.py"
    assert ler_trava(tmp_path / "nao_existe.lock") is None


# --- pastas da nuvem (hpbase.caminhos) -----------------------------------------------------
def test_pasta_esteira_e_paridade_padrao(monkeypatch):
    monkeypatch.delenv("HP_ESTEIRA_NOME", raising=False)
    monkeypatch.delenv("HP_PARIDADE_NOME", raising=False)
    assert pasta_esteira() == raiz_local() / "esteira_sombra"
    assert pasta_paridade() == pasta_app() / "paridade_nuvem"
    assert pasta_esteira().name != "esteira" and pasta_paridade().name != "paridade"  # pastas do PC


def test_pasta_esteira_e_paridade_por_variavel(monkeypatch):
    monkeypatch.setenv("HP_ESTEIRA_NOME", "esteira_teste")
    monkeypatch.setenv("HP_PARIDADE_NOME", "paridade_teste")
    assert pasta_esteira() == raiz_local() / "esteira_teste"
    assert pasta_paridade() == pasta_app() / "paridade_teste"
