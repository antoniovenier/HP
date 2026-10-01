# -*- coding: utf-8 -*-
"""Testes do story_coletar_telas.py (tarefa E4): a coleta assistida SÓ lê a tela (dump + screencap).

Sem aparelho: o AdbFalso responde às telas; quem "navega" é a função de entrada injetada, que troca a tela
atual do falso antes de devolver o ENTER. O que se prova: nenhum `input`, `am`, `monkey` ou `push` vai ao
aparelho; os arquivos NN_nome.xml/.png e o coleta.json saem; tela de login/aviso para com código 3 sem toque.
Rodar: cd scripts && python -m pytest -q testes/test_story_coletar_telas.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
for _p in (AQUI, AQUI.parent, AQUI.parent.parent / "app" / "hp_studio_nuvem"):
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import story_coletar_telas as sct  # noqa: E402
import story_dispositivo as sd  # noqa: E402
import story_fluxos as sf  # noqa: E402
import story_post_seletores as SEL  # noqa: E402
from adb_falso import AdbFalso, LogLista, TELA_ALTERNATIVA, TELA_PADRAO  # noqa: E402

# a tela do AdbFalso que faz as vezes de cada uma das 12 telas da coleta (menu "+" e busca não têm fixture própria)
SEQUENCIA = ["perfil", "perfil", "galeria", "editor", "figurinhas", "figurinhas", "link", "enquete", "editor",
             "folha_send", "destaques", "lista_contas"]


@pytest.fixture(autouse=True)
def _raizes(tmp_path, monkeypatch):
    local, drive = tmp_path / "HypadoLocal", tmp_path / "Drive"
    local.mkdir(exist_ok=True)
    drive.mkdir(exist_ok=True)
    monkeypatch.setenv("HP_LOCAL", str(local))
    monkeypatch.setenv("HP_DRIVE", str(drive))
    monkeypatch.delenv("HP_ANDROID_SERIAL", raising=False)
    return local, drive


class Navegador:
    """Faz o papel do Antônio: a cada ENTER, deixa o aparelho na próxima tela e responde o que foi pedido."""

    def __init__(self, falso: AdbFalso, telas=SEQUENCIA, respostas=None):
        self.falso = falso
        self.telas = list(telas)
        self.respostas = list(respostas or [])
        self.enters = 0

    def __call__(self) -> str:
        if self.telas:
            self.falso.tela_atual = self.telas.pop(0)
        self.enters += 1
        return self.respostas.pop(0) if self.respostas else ""


def novo(falso: AdbFalso, **kw) -> sd.Dispositivo:
    kw.setdefault("log", LogLista())
    kw.setdefault("serial", "emulator-5554")
    kw.setdefault("gravar_parada", sd.gravar_parada_padrao())
    return sd.Dispositivo(falso, **kw)


def so_leitura(falso: AdbFalso, disp: sd.Dispositivo) -> None:
    """Prova de que a coleta não toca em nada: nenhum input/am/monkey/push no histórico."""
    assert falso.toques == [] and falso.swipes == [] and falso.digitados == [] and falso.teclas == []
    assert falso.abertos == [] and falso.pushados == [] and falso.broadcasts == []
    assert not any(c.split()[0] in ("input", "am", "monkey") for c in falso.shell_cmds if c.strip())
    assert sct.comandos_fora_da_lista(disp.historico) == []


# ===========================================================================
# A coleta
# ===========================================================================
@pytest.mark.parametrize("tela", [TELA_PADRAO, TELA_ALTERNATIVA])
def test_coleta_grava_xml_png_e_indice_sem_nenhum_toque(tmp_path, tela):
    falso = AdbFalso(tela=tela, tela_atual="perfil")
    disp = novo(falso)
    nav = Navegador(falso)
    linhas = []
    codigo, indice = sct.coletar(disp, tmp_path / "coleta", entrada=nav, saida=linhas.append)
    assert codigo == 0 and nav.enters == 12 and len(indice["telas"]) == 12
    so_leitura(falso, disp)
    pasta = tmp_path / "coleta"
    for n, t in enumerate(sct.TELAS, 1):
        xml, png = pasta / f"{n:02d}_{t['nome']}.xml", pasta / f"{n:02d}_{t['nome']}.png"
        assert xml.exists() and png.exists(), t["nome"]
        assert "<hierarchy" in xml.read_text(encoding="utf-8") and png.read_bytes().startswith(b"\x89PNG")
    gravado = json.loads((pasta / "coleta.json").read_text(encoding="utf-8"))
    assert gravado["tela"] == list(tela) and gravado["serial"] == "emulator-5554" and gravado["codigo"] == 0
    assert gravado["telas"][0]["xml"] == "01_perfil_proprio.xml" and gravado["telas"][-1]["nome"] == "lista_contas"
    assert gravado["sinteticas_que_substitui"][0] == f"perfil_sintetico_{tela[0]}x{tela[1]}.xml"
    assert falso.n_dump == 12 and sum(1 for c in falso.shell_cmds if c.startswith("screencap")) == 12
    assert any("Aperte ENTER" in l or "aperte ENTER" in l for l in linhas)


def test_indice_diz_quais_seletores_cada_tela_confirmou(tmp_path):
    falso = AdbFalso(tela_atual="perfil")
    _, indice = sct.coletar(novo(falso), tmp_path / "c", entrada=Navegador(falso), saida=lambda *_: None)
    perfil = indice["telas"][0]
    assert perfil["vistos"]["aba_perfil"] == ["profile_tab"] and perfil["vistos"]["conta_container"] == ["action_bar_username_container"]
    assert perfil["vistos"]["avatar_perfil"] == ["row_profile_header_imageview"] and "image_button" in perfil["vistos"]["grade_item"]
    assert set(perfil["confirmadas"]) >= {"aba_perfil", "conta_container", "conta_titulo", "avatar_perfil", "grade_item", "criar"}
    enquete = next(t for t in indice["telas"] if t["nome"] == "figurinha_enquete_aberta")
    assert enquete["vistos"]["enquete_pergunta"] == ["poll_sticker_v2_question"] and "concluir" in enquete["confirmadas"]
    assert enquete["vistos"]["enquete_add_opcao"] == ["Add option"]
    destaque = next(t for t in indice["telas"] if t["nome"] == "seletor_destaque")
    assert destaque["vistos"]["destaque_item"] == ["highlight_title"] and destaque["faltam"]       # o que a tela não mostrou fica listado
    assert "action_bar_username_container" in perfil["ids_da_tela"]


def test_coleta_para_na_tela_de_login_sem_tocar_e_codigo_3(tmp_path):
    falso = AdbFalso(tela_atual="perfil")
    disp = novo(falso)
    nav = Navegador(falso, ["perfil", "perfil", "login"])
    linhas = []
    codigo, indice = sct.coletar(disp, tmp_path / "c", entrada=nav, saida=linhas.append)
    assert codigo == 3 and nav.enters == 3 and len(indice["telas"]) == 2
    assert indice["parado"]["tela"] == "03_galeria" and "login" in indice["parado"]["frase"]
    assert (tmp_path / "c" / "03_galeria_AVISO.xml").exists() and not (tmp_path / "c" / "03_galeria.png").exists()
    assert sd.arquivo_parada_padrao().exists()                   # a parada é gravada (função injetada do E1)
    so_leitura(falso, disp)
    assert any("PAREI" in l and "não peço senha" in l for l in linhas)
    assert json.loads((tmp_path / "c" / "coleta.json").read_text(encoding="utf-8"))["codigo"] == 3


@pytest.mark.parametrize("tela_ruim", ["aviso_meta", "termos"])
def test_coleta_para_em_aviso_da_meta_ou_termos(tmp_path, tela_ruim):
    falso = AdbFalso(tela_atual="perfil")
    disp = novo(falso)
    codigo, indice = sct.coletar(disp, tmp_path / "c", entrada=Navegador(falso, [tela_ruim]), saida=lambda *_: None)
    assert codigo == 3 and indice["telas"] == [] and indice["parado"]["tela"] == "01_perfil_proprio"
    so_leitura(falso, disp)


def test_pular_e_sair(tmp_path):
    falso = AdbFalso(tela_atual="perfil")
    disp = novo(falso)
    nav = Navegador(falso, SEQUENCIA, respostas=["", "pular", "", "sair"])
    codigo, indice = sct.coletar(disp, tmp_path / "c", entrada=nav, saida=lambda *_: None)
    assert codigo == 0 and nav.enters == 4
    assert [t.get("pulada", False) for t in indice["telas"]] == [False, True, False]
    assert (tmp_path / "c" / "03_galeria.xml").exists() and not (tmp_path / "c" / "02_menu_mais.xml").exists()
    so_leitura(falso, disp)


def test_so_algumas_telas(tmp_path):
    falso = AdbFalso(tela_atual="perfil")
    nav = Navegador(falso, ["figurinhas", "lista_contas"])
    codigo, indice = sct.coletar(novo(falso), tmp_path / "c", entrada=nav, saida=lambda *_: None, so=["05", "lista_contas"])
    assert codigo == 0 and [t["n"] for t in indice["telas"]] == [5, 12] and nav.enters == 2


def test_nunca_pede_senha_e_nao_ecoa_o_que_foi_digitado(tmp_path):
    falso = AdbFalso(tela_atual="perfil")
    linhas = []
    sct.coletar(novo(falso), tmp_path / "c", entrada=Navegador(falso, ["perfil"], ["FAKE_NAO_E_SENHA_1", "sair"]),
                saida=linhas.append)
    txt = "\n".join(linhas)
    assert "FAKE_NAO_E_SENHA_1" not in txt
    for t in sct.TELAS:
        assert "senha" not in t["instrucao"].lower() and "password" not in t["instrucao"].lower()
    assert "Nunca escreva senha" in txt


def test_tela_que_confirma_cobre_todos_os_palpites():
    palpites = set(SEL.A_CONFIRMAR) | set(sf.IDS_PALPITE)
    sem_tela = sorted(k for k in palpites if not sct.tela_que_confirma(k))
    # os ids da contagem/calendário não têm tela na lista da tarefa E4 (12 telas): ficam anotados no E2.md
    assert set(sem_tela) <= {"contagem_titulo", "contagem_data", "contagem_dia_inteiro", "data_proximo_mes", "data_ok"}
    assert sct.tela_que_confirma("aba_perfil") == ["01_perfil_proprio"]
    assert sct.tela_que_confirma("link_url") == ["07_figurinha_link_aberta"]
    assert sct.tela_que_confirma("conta_container") == ["01_perfil_proprio", "12_lista_contas"]
    assert sct.alternativas_de("link_url") == ("id", sf.IDS_PALPITE["link_url"])
    assert sct.alternativas_de("add_story") == ("texto", SEL.TEXTOS["add_story"])
    assert sct.alternativas_de("inexistente") == ("id", ["inexistente"])
    assert [t["nome"] for t in sct.TELAS] == ["perfil_proprio", "menu_mais", "galeria", "editor_story", "bandeja_figurinhas",
                                             "busca_link", "figurinha_link_aberta", "figurinha_enquete_aberta",
                                             "botao_seu_story", "folha_envio_post", "seletor_destaque", "lista_contas"]


def test_comandos_fora_da_lista_pega_toque_e_push():
    hist = [["adb", "-s", "x", "shell", "uiautomator", "dump", "/sdcard/ui.xml"], ["adb", "-s", "x", "pull", "/a", "/b"],
            ["adb", "-s", "x", "shell", "input", "tap", "1", "2"], ["adb", "-s", "x", "push", "a", "b"],
            ["adb", "-s", "x", "shell", "am", "start", "-d", "x"]]
    assert sct.comandos_fora_da_lista(hist) == ["input tap 1 2", "push a b", "am start -d x"]


# ===========================================================================
# CLI: --simular sem adb, bloqueado -> 4, dois aparelhos -> 4, --pasta
# ===========================================================================
@pytest.fixture
def sem_subprocesso(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("a coleta chamou um subprocesso de verdade")
    monkeypatch.setattr(subprocess, "run", _boom)
    monkeypatch.setattr(sd, "rodar", _boom)


def test_simular_imprime_o_roteiro_sem_adb_e_sem_esperar_enter(sem_subprocesso, tmp_path):
    linhas = []
    pediu = []
    rc = sct.main(["--simular", "--pasta", str(tmp_path / "c")], saida=linhas.append, entrada=lambda: pediu.append(1) or "")
    txt = "\n".join(linhas)
    assert rc == 0 and "SIMULAÇÃO" in linhas[0] and len(pediu) == 12
    for n, t in enumerate(sct.TELAS, 1):
        assert f"[{n}/12] {t['instrucao'][:40]}" in txt
    assert "[simular] adb -s emulator-5554 shell uiautomator dump" in txt and "screencap" in txt
    assert "input" not in txt.replace("input()", "") or "shell input" not in txt
    assert (tmp_path / "c" / "coleta.json").exists() and (tmp_path / "c" / "01_perfil_proprio.xml").exists()


def test_main_com_aparelho_bloqueado_e_codigo_4_sem_acordar(tmp_path):
    falso = AdbFalso(tela_atual="perfil", travada=True, pin=True)
    linhas = []
    rc = sct.main(["--pasta", str(tmp_path / "c")], saida=linhas.append, entrada=lambda: "", runner=falso, env={})
    assert rc == 4 and any("o Antônio desbloqueia" in l for l in linhas)
    assert falso.teclas == [] and falso.toques == [] and not (tmp_path / "c").exists()


def test_main_dois_aparelhos_sem_escolha_e_codigo_4(tmp_path):
    falso = AdbFalso(tela_atual="perfil", dispositivos=[("emulator-5554", "device"), ("R58M1ABCDEF", "device")])
    linhas = []
    assert sct.main(["--pasta", str(tmp_path / "c")], saida=linhas.append, entrada=lambda: "", runner=falso, env={}) == 4
    assert any("--serial" in l for l in linhas)
    # com --celular escolhe o que não é emulador e a coleta roda
    falso = AdbFalso(tela_atual="perfil", dispositivos=[("emulator-5554", "device"), ("R58M1ABCDEF", "device")])
    nav = Navegador(falso)
    assert sct.main(["--pasta", str(tmp_path / "c"), "--celular"], saida=lambda *_: None, entrada=nav, runner=falso, env={}) == 0
    assert all(a[1:3] == ["-s", "R58M1ABCDEF"] for a in falso.comandos if a[1:2] == ["-s"])


def test_main_grava_na_pasta_padrao_do_pc_quando_nao_passa_pasta(tmp_path, _raizes, monkeypatch):
    local, _ = _raizes
    falso = AdbFalso(tela_atual="perfil")
    nav = Navegador(falso, ["perfil"], respostas=["", "sair"])
    assert sct.main([], saida=lambda *_: None, entrada=nav, runner=falso, env={}) == 0
    pasta = local / "android" / "telas" / "coleta"
    assert (pasta / "01_perfil_proprio.xml").exists() and (pasta / "coleta.json").exists()
    assert sct.pasta_coleta_padrao() == pasta


def test_nome_arquivo_e_nenhuma_linha_de_cabecalho_de_arquivo_nas_instrucoes():
    assert sct.nome_arquivo(7, "figurinha_link_aberta", "xml") == "07_figurinha_link_aberta.xml"
    for t in sct.TELAS:
        assert not t["instrucao"].startswith("## ")
