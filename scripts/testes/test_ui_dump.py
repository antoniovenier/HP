"""Testes do leitor da saída do ui.py (scripts/ui_dump.py) sobre o dump real do visualizador
de story do @hp.futebol (tests/fixtures/pc_real/ui_story_visualizador_hp_futebol.txt). Sem adb."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import ui_dump  # noqa: E402

DUMP = SCRIPTS.parent / "tests" / "fixtures" / "pc_real" / "ui_story_visualizador_hp_futebol.txt"


@pytest.fixture
def nos():
    return ui_dump.ler_arquivo(DUMP)


def test_le_todas_as_linhas_do_dump_real(nos):
    linhas = [l for l in DUMP.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(nos) == len(linhas) == 52
    assert all(set(n) >= set(ui_dump.COLUNAS) for n in nos)
    assert nos[0] == {"x": 540, "y": 1168, "classe": "LinearLayout", "texto": "", "desc": "",
                      "id": "action_bar_root", "clicavel": False}
    assert not any(n.get("ambiguo") for n in nos)


def test_os_ids_reais_do_visualizador_de_story(nos):
    destaque = ui_dump.achar(nos, id="toolbar_highlights_button")
    assert destaque["desc"] == "Highlight" and destaque["clicavel"] is True
    assert ui_dump.centro(destaque) == (530, 2190)
    assert ui_dump.achar(nos, id="reel_viewer_timestamp")["texto"] == "3m"
    assert ui_dump.achar(nos, id="reel_viewer_title")["texto"] == "hp.futebol"
    assert ui_dump.achar(nos, id="reel_viewer_text_container")["desc"] == "hp.futebol's story, 3 minutes ago"
    assert ui_dump.achar(nos, id="self_toolbar_reshare_button_container")["desc"] == "Send story"
    assert ui_dump.achar(nos, id="add_comment_textview")["texto"] == "Say something…"


def test_busca_por_texto_e_desc_ignora_maiuscula_acento_e_aceita_trecho(nos):
    assert ui_dump.achar(nos, desc="highlight")["id"] == "toolbar_highlights_button"
    assert ui_dump.achar(nos, desc="minutes ago", contem=True)["id"] == "reel_viewer_text_container"
    assert ui_dump.achar(nos, texto="HP.FUTEBOL")["id"] == "reel_viewer_title"
    assert ui_dump.achar(nos, texto="3m", clicavel=True) is None
    assert len(ui_dump.achar_todos(nos, clicavel=True)) == 9
    assert ui_dump.achar(nos, id="nao_existe") is None
    assert ui_dump.achar(nos, desc="Highlight", id="highlights_label") is None   # os dois têm que bater


def test_linha_fora_do_formato_e_texto_com_barra():
    assert ui_dump.ler_linha_ui("") is None
    assert ui_dump.ler_linha_ui("toquei: 530 2190 | Highlight") is None
    assert ui_dump.ler_linha_ui("nao achei: x") is None
    # coluna 'clicavel' vazia com o espaço final tirado pelo editor
    n = ui_dump.ler_linha_ui("540,64 | View |  |  | statusBarBackground |")
    assert n["id"] == "statusBarBackground" and n["clicavel"] is False
    # " | " dentro do texto (nome de grupo "HP | Futebol") é recomposto e marcado
    n = ui_dump.ler_linha_ui("100,200 | TextView | HP | Futebol ⚽ |  | row_title | clic")
    assert n["texto"] == "HP | Futebol ⚽" and n["desc"] == "" and n["id"] == "row_title"
    assert n["clicavel"] is True and n["ambiguo"] is True
    assert ui_dump.ler_linhas_ui("lixo\n540,64 | View |  |  | a | \n") == [
        {"x": 540, "y": 64, "classe": "View", "texto": "", "desc": "", "id": "a", "clicavel": False}]


def test_cli_imprime_json(capsys):
    assert ui_dump.main([str(DUMP), "highlight"]) == 0
    saida = json.loads(capsys.readouterr().out)
    assert [n["id"] for n in saida] == ["toolbar_highlights_button", "highlights_status", "highlights_label"]
