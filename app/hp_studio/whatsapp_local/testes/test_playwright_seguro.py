"""O navegador real: import tardio, janela fora da tela, sem som, perfil
separado, sem "trazer para frente" e sem biblioteca proibida."""
import ast
import sys
from pathlib import Path

import pytest

from hpbase import raiz_local
from whatsapp_local import seletores
from whatsapp_local.config import pasta_perfil
from whatsapp_local.enviador import fabrica_padrao
from whatsapp_local.config import Config
from whatsapp_local.navegador import NavegadorIndisponivel
from whatsapp_local.navegador_playwright import (NavegadorPlaywright, classificar_subtitulo,
                                                 opcoes_lancamento)

PACOTE = Path(__file__).resolve().parents[1]


def test_import_tardio_sem_playwright(monkeypatch):
    monkeypatch.setitem(sys.modules, "playwright", None)       # simula "não instalado"
    monkeypatch.setitem(sys.modules, "playwright.sync_api", None)
    nav = fabrica_padrao(Config())                            # criar não importa nada
    assert isinstance(nav, NavegadorPlaywright)
    with pytest.raises(NavegadorIndisponivel) as e:
        nav.abrir()
    assert "pip install playwright" in str(e.value)


def test_perfil_separado_fora_da_tela_e_mudo():
    op = opcoes_lancamento(pasta_perfil())
    assert op["user_data_dir"] == str(raiz_local() / "whatsapp_perfil")
    assert "--window-position=-32000,-32000" in op["args"]
    assert "--start-minimized" in op["args"]
    assert "--mute-audio" in op["args"]
    assert op["headless"] is False and "channel" not in op
    assert opcoes_lancamento(pasta_perfil(), canal="chrome")["channel"] == "chrome"


def test_login_abre_visivel_mas_continua_mudo():
    op = opcoes_lancamento(pasta_perfil(), visivel=True)
    assert "--window-position=-32000,-32000" not in op["args"]
    assert "--mute-audio" in op["args"]


def _arvores():
    for p in PACOTE.rglob("*.py"):
        if "testes" not in p.parts:
            yield p, ast.parse(p.read_text(encoding="utf-8"))


def test_nunca_traz_janela_para_frente_nem_usa_biblioteca_proibida():
    permitidos = set(sys.stdlib_module_names) | {"hpbase", "playwright"}
    for p, arvore in _arvores():
        for no in ast.walk(arvore):
            if isinstance(no, ast.Attribute):
                assert no.attr != "bring_to_front", f"{p.name} traz a janela para frente"
            if isinstance(no, ast.Import):
                for a in no.names:
                    assert a.name.split(".")[0] in permitidos, f"{p.name}: import {a.name}"
            if isinstance(no, ast.ImportFrom) and no.level == 0:
                assert no.module.split(".")[0] in permitidos, f"{p.name}: from {no.module}"


def test_playwright_so_e_importado_dentro_de_abrir():
    arvore = ast.parse((PACOTE / "navegador_playwright.py").read_text(encoding="utf-8"))
    for no in arvore.body:              # nada de playwright no topo do módulo
        if isinstance(no, (ast.Import, ast.ImportFrom)):
            nomes = [a.name for a in no.names] + [getattr(no, "module", "") or ""]
            assert not any(n.startswith("playwright") for n in nomes)


def test_seletores_sao_listas_de_alternativas():
    listas = {k: v for k, v in vars(seletores).items() if k.isupper() and isinstance(v, list)}
    assert {"CAIXA_BUSCA", "TITULO_CONVERSA", "CAIXA_MENSAGEM", "BOTAO_ENVIAR",
            "LISTA_CONVERSAS", "QR_CODE"} <= set(listas)
    for nome, v in listas.items():
        assert len(v) >= 2 and all(isinstance(s, str) and s for s in v), nome


def test_classificar_subtitulo():
    assert classificar_subtitulo("Antônio, Fulano, Você") is True
    assert classificar_subtitulo("clique para mostrar os dados do grupo") is True
    assert classificar_subtitulo("online") is False
    assert classificar_subtitulo("visto por último hoje às 10:00") is False
    assert classificar_subtitulo("") is None
