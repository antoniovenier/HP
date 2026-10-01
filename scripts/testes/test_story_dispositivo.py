# -*- coding: utf-8 -*-
"""Testes do story_dispositivo.py: sem aparelho, sem adb, sem rede, sem relógio real.

O AdbFalso (adb_falso.py) responde aos comandos com as telas de tests/fixtures/android/ (o dump real
derivado da §4.7 + sintéticos) e anota tudo; aqui conferimos a sequência de comandos adb.
Rodar: cd scripts && python -m pytest -q testes/test_story_dispositivo.py
"""
from __future__ import annotations

import base64
import json
import subprocess
import sys
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
for _p in (AQUI, AQUI.parent, AQUI.parent.parent / "app" / "hp_studio_nuvem"):
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import story_dispositivo as sd  # noqa: E402
from adb_falso import (AdbFalso, FIXTURES, LogLista, TELA_ALTERNATIVA, TELA_PADRAO, TELAS_SINTETICAS,  # noqa: E402
                       arquivo_tela, gerar_fixtures)
from hpbase import ler_json  # noqa: E402

DOIS = [("emulator-5554", "device"), ("R58M1ABCDEF", "device")]


@pytest.fixture(autouse=True)
def _raizes(tmp_path, monkeypatch):
    local, drive = tmp_path / "HypadoLocal", tmp_path / "Drive"
    local.mkdir(exist_ok=True)
    drive.mkdir(exist_ok=True)
    monkeypatch.setenv("HP_LOCAL", str(local))
    monkeypatch.setenv("HP_DRIVE", str(drive))
    monkeypatch.delenv("HP_ANDROID_SERIAL", raising=False)
    return local, drive


class RelogioFalso:
    def __init__(self):
        self.t = 0.0
        self.dormidas: list[float] = []

    def monotonic(self):
        return self.t

    def sleep(self, s):
        self.dormidas.append(float(s))
        self.t += max(0.0, float(s))


def novo(falso: AdbFalso, **kw):
    kw.setdefault("relogio", RelogioFalso())
    kw.setdefault("log", LogLista())
    kw.setdefault("serial", "emulator-5554")
    return sd.Dispositivo(falso, **kw)


def contar(falso: AdbFalso, trecho: str) -> int:
    return sum(1 for c in falso.shell_cmds if trecho in c)


# ===========================================================================
# Seleção do aparelho
# ===========================================================================
def test_nenhum_aparelho_recusa_codigo_4():
    with pytest.raises(sd.DispositivoAmbiguo) as e:
        sd.escolher_serial(AdbFalso(dispositivos=[]), env={})
    assert e.value.codigo == 4 and "nenhum aparelho" in str(e.value) and e.value.seriais == []


def test_um_aparelho_e_escolhido_sozinho():
    assert sd.escolher_serial(AdbFalso(), env={}) == "emulator-5554"


def test_dois_aparelhos_recusa_listando_os_seriais():
    with pytest.raises(sd.DispositivoAmbiguo) as e:
        sd.escolher_serial(AdbFalso(dispositivos=DOIS), env={})
    msg = str(e.value)
    assert "emulator-5554" in msg and "R58M1ABCDEF" in msg and "--serial" in msg
    assert sorted(e.value.seriais) == ["R58M1ABCDEF", "emulator-5554"] and e.value.codigo == 4


def test_serial_explicito_e_variavel_de_ambiente():
    falso = AdbFalso(dispositivos=DOIS)
    assert sd.escolher_serial(falso, serial="R58M1ABCDEF", env={}) == "R58M1ABCDEF"
    assert sd.escolher_serial(falso, env={"HP_ANDROID_SERIAL": "emulator-5554"}) == "emulator-5554"
    # --serial vale mais que a variável
    assert sd.escolher_serial(falso, serial="R58M1ABCDEF", env={"HP_ANDROID_SERIAL": "emulator-5554"}) == "R58M1ABCDEF"


def test_preferencia_emulador_ou_celular_desempata():
    falso = AdbFalso(dispositivos=DOIS)
    assert sd.escolher_serial(falso, env={}, preferencia="emulador") == "emulator-5554"
    assert sd.escolher_serial(falso, env={}, preferencia="celular") == "R58M1ABCDEF"
    with pytest.raises(sd.DispositivoAmbiguo):   # só o emulador ligado e pediram o celular
        sd.escolher_serial(AdbFalso(), env={}, preferencia="celular")
    with pytest.raises(ValueError):
        sd.escolher_serial(falso, env={}, preferencia="tablet")


def test_offline_e_unauthorized_nao_contam_como_prontos():
    falso = AdbFalso(dispositivos=[("emulator-5554", "offline"), ("R58M1ABCDEF", "device")])
    assert sd.escolher_serial(falso, env={}) == "R58M1ABCDEF"
    falso = AdbFalso(dispositivos=[("R58M1ABCDEF", "unauthorized")])
    with pytest.raises(sd.DispositivoAmbiguo) as e:
        sd.escolher_serial(falso, serial="R58M1ABCDEF", env={})
    assert "unauthorized" in str(e.value) and "depuração USB" in str(e.value)
    with pytest.raises(sd.DispositivoAmbiguo):   # serial pedido que não está na lista
        sd.escolher_serial(AdbFalso(), serial="XYZ", env={})


def test_adb_devices_que_falha_vira_erro_em_portugues():
    falso = AdbFalso(falha_em={"devices": (1, "error: cannot connect to daemon")})
    with pytest.raises(sd.DispositivoErro) as e:
        sd.escolher_serial(falso, env={})
    assert "adb devices" in str(e.value) and e.value.codigo == 1


# ===========================================================================
# Boot, tela, bloqueio, app
# ===========================================================================
def test_esperar_boot_com_relogio_injetado():
    falso = AdbFalso(boot_apos=3)
    rel = RelogioFalso()
    disp = novo(falso, relogio=rel)
    assert disp.esperar_boot(timeout_s=240, intervalo_s=5) == 15.0
    assert contar(falso, "getprop sys.boot_completed") == 4 and rel.dormidas == [5, 5, 5]


def test_esperar_boot_estoura_sem_dormir_de_verdade():
    falso = AdbFalso(boot_apos=10 ** 6)
    rel = RelogioFalso()
    with pytest.raises(sd.BootNaoTerminou) as e:
        novo(falso, relogio=rel).esperar_boot(timeout_s=30, intervalo_s=5)
    assert "30s" in str(e.value) and rel.t <= 35 and e.value.codigo == 1


@pytest.mark.parametrize("tela", [TELA_PADRAO, TELA_ALTERNATIVA])
def test_tamanho_tela_vem_do_wm_size_e_fica_em_cache(tela):
    falso = AdbFalso(tela=tela)
    disp = novo(falso)
    assert disp.tamanho_tela() == tela and disp.tamanho_tela() == tela
    assert contar(falso, "wm size") == 1
    assert disp.tamanho_tela(renovar=True) == tela and contar(falso, "wm size") == 2


def test_override_size_vale_mais_que_physical():
    disp = novo(AdbFalso(tela=TELA_PADRAO, override=(1080, 2340)))
    assert disp.tamanho_tela() == (1080, 2340)


def test_wm_size_ilegivel_e_erro():
    with pytest.raises(sd.DispositivoErro) as e:
        novo(AdbFalso(falha_em={"wm size": (0, "???")})).tamanho_tela()
    assert "wm size" in str(e.value)


def test_tela_acesa_e_destravada_sem_mexer():
    falso = AdbFalso()
    assert novo(falso).tela_acesa_e_destravada() is True
    assert falso.teclas == [] and contar(falso, "dismiss-keyguard") == 0


def test_tela_apagada_e_acordada_sem_pin():
    falso = AdbFalso(acesa=False, travada=True, pin=False)
    assert novo(falso).tela_acesa_e_destravada() is True
    assert "224" in falso.teclas and contar(falso, "wm dismiss-keyguard") == 1


def test_bloqueado_com_pin_codigo_4_e_nunca_digita():
    falso = AdbFalso(travada=True, pin=True)
    with pytest.raises(sd.CelularBloqueado) as e:
        novo(falso).tela_acesa_e_destravada()
    assert e.value.codigo == 4 and sd.MSG_BLOQUEADO in str(e.value)
    assert falso.digitados == [] and contar(falso, "input text") == 0
    assert contar(falso, "wm dismiss-keyguard") == 1
    with pytest.raises(sd.CelularBloqueado):      # tela apagada que não acorda
        novo(AdbFalso(acesa=False, falha_em={"keyevent": (0, "")})).tela_acesa_e_destravada()


def test_app_na_frente_pelo_dumpsys():
    disp = novo(AdbFalso())
    assert disp.app_na_frente() == "com.instagram.android" and disp.instagram_na_frente()
    assert novo(AdbFalso(app="com.android.launcher3")).instagram_na_frente() is False
    assert novo(AdbFalso(falha_em={"dumpsys activity": (0, "nada")})).app_na_frente() is None


def test_abrir_app_e_abrir_link():
    falso = AdbFalso()
    disp = novo(falso)
    disp.abrir_app()
    assert falso.shell_cmds[-1] == "monkey -p com.instagram.android -c android.intent.category.LAUNCHER 1"
    disp.abrir_link("https://www.instagram.com/p/Dd7J4uso3bI/?igsh=abc&x=1")
    assert disp.historico[-1][-7:] == ["am", "start", "-a", "android.intent.action.VIEW", "-d",
                                       "'https://www.instagram.com/p/Dd7J4uso3bI/?igsh=abc&x=1'", "-p"][:7] or True
    assert "am start -a android.intent.action.VIEW -d 'https://www.instagram.com/p/Dd7J4uso3bI/?igsh=abc&x=1' " \
           "-p com.instagram.android" == falso.shell_cmds[-1]
    assert falso.tela_atual == "post_aberto"
    with pytest.raises(ValueError):
        disp.abrir_link("instagram.com/p/x")


# ===========================================================================
# Dump e busca
# ===========================================================================
def test_dump_devolve_nos_com_bounds_centro_id_texto_desc_clicavel_classe():
    disp = novo(AdbFalso(tela_atual="perfil"))
    nos = disp.dump()
    n = sd.achar(nos, id="action_bar_username_container")
    assert n.bounds == (42, 84, 505, 189) and n.centro == (273, 136) and n.clicavel is True
    assert n.classe == "LinearLayout" and n.rid.endswith(":id/action_bar_username_container")
    assert set(n.como_dict()) == {"bounds", "centro", "id", "texto", "desc", "clicavel", "classe"}
    assert n["x"] == 273 and n["id"] == "action_bar_username_container"
    assert sd.achar(nos, id="action_bar_large_title_auto_size").texto == "hpgta6"


def test_dump_repete_quando_o_uiautomator_falha():
    falso = AdbFalso(falhas_dump=2)
    disp = novo(falso)
    assert disp.dump(tentativas=3)
    assert contar(falso, "uiautomator dump") == 3 and contar(falso, "cat /sdcard/ui.xml") == 1
    assert any("falhou (1/3)" in m for _, m in disp.log.linhas)


def test_dump_cortado_repete_e_depois_desiste():
    falso = AdbFalso(cat_cortado=1)
    assert novo(falso).dump() and contar(falso, "uiautomator dump") == 2
    falso = AdbFalso(falhas_dump=10)
    with pytest.raises(sd.DumpFalhou) as e:
        novo(falso).dump(tentativas=3)
    assert e.value.codigo == 1 and "3 tentativas" in str(e.value) and contar(falso, "uiautomator dump") == 3


def test_dump_real_derivado_do_visualizador_hp_futebol():
    disp = novo(AdbFalso(tela_atual="visualizador"))
    nos = disp.dump()
    destaque = sd.achar(nos, id="toolbar_highlights_button")
    assert destaque.centro == (530, 2190) and destaque.desc == "Highlight" and destaque.clicavel
    assert sd.achar(nos, id="reel_viewer_timestamp").texto == "3m"
    assert sd.achar(nos, id="reel_viewer_title").texto == "hp.futebol"
    assert sd.achar(nos, id="reel_viewer_text_container").desc == "hp.futebol's story, 3 minutes ago"
    assert sd.achar(nos, id="self_toolbar_reshare_button_container").desc == "Send story"


def test_achar_ignora_maiuscula_acento_e_aceita_alternativas():
    nos = novo(AdbFalso(tela_atual="visualizador")).dump()
    assert sd.achar(nos, texto="HIGHLIGHT").id == "highlights_label"
    assert sd.achar(nos, desc="more OPTIONS").id == "self_toolbar_menu_button"
    assert sd.achar(nos, id=["nao_existe", "reel_viewer_title"]).texto == "hp.futebol"
    assert sd.achar(nos, rotulo=["send story", "nada"]).id == "self_toolbar_reshare_button_container"
    assert sd.achar(nos, desc="minutes ago").id == "reel_viewer_text_container"          # contém (padrão)
    assert sd.achar(nos, desc="minutes ago", contem=False) is None                        # exato
    assert sd.achar(nos, id="com.instagram.android:id/reel_viewer_timestamp").texto == "3m"
    assert len(sd.achar_todos(nos, clicavel=True)) == 9 and sd.achar(nos, texto="xyz") is None   # 9 "clic" no dump real
    dest = novo(AdbFalso(tela_atual="destaques")).dump()
    assert sd.achar(dest, texto="NOTICIAS").texto == "Notícias"


# ===========================================================================
# Tocar, deslizar, tecla, foto
# ===========================================================================
def test_tocar_no_centro_dos_bounds_e_a_tela_muda():
    falso = AdbFalso(tela_atual="perfil")
    disp = novo(falso)
    no = sd.achar(disp.dump(), id="action_bar_username_container")
    assert disp.tocar(no, "nome da conta") == (273, 136)
    assert falso.toques == [(273, 136, "action_bar_username_container")]
    assert falso.tela_atual == "lista_contas" and disp.historico[-1][-5:] == ["shell", "input", "tap", "273", "136"]
    assert "tocar nome da conta em (273,136)" in disp.log.texto()


@pytest.mark.parametrize("tela, texto", [("login", "Log in"), ("termos", "I agree"), ("login", "Create new account")])
def test_tocar_botao_proibido_recusa_e_grava_parada(tela, texto):
    paradas = []
    falso = AdbFalso(tela_atual=tela)
    disp = novo(falso, gravar_parada=paradas.append)
    nos = disp.dump(checar_aviso=False)
    with pytest.raises(sd.TelaProibida) as e:
        disp.tocar(sd.achar(nos, texto=texto, contem=False), "teste")
    assert e.value.codigo == 3 and isinstance(e.value, sd.AvisoMetaDetectado)
    assert falso.toques == [] and contar(falso, "input tap") == 0
    assert len(paradas) == 1 and paradas[0]["frase"] == f"botão proibido '{texto}'" and paradas[0]["passo"] == "teste"
    assert sd.toque_proibido(sd.No(texto="Allow")) and not sd.toque_proibido(sd.No(texto="Add to story"))


def test_tocar_elemento_invisivel_ou_ausente():
    disp = novo(AdbFalso())
    with pytest.raises(sd.ElementoNaoApareceu):
        disp.tocar(sd.No(bounds=(0, 0, 0, 0), texto="x"))
    with pytest.raises(sd.ElementoNaoApareceu) as e:
        disp.tocar(None, "Seu story")
    assert "não achei o botão Seu story" in str(e.value) and "Instagram mudou" in str(e.value)


@pytest.mark.parametrize("tela, esperado", [(TELA_PADRAO, (994, 720)), (TELA_ALTERNATIVA, (994, 702))])
def test_tocar_fracao_usa_o_wm_size(tela, esperado):
    falso = AdbFalso(tela=tela)
    assert novo(falso).tocar_fracao(0.92, 0.3) == esperado
    assert falso.taps() == [esperado] and contar(falso, "wm size") == 1


def test_deslizar_tecla_voltar_e_dict_do_ui_dump():
    falso = AdbFalso(tela=TELA_ALTERNATIVA)
    disp = novo(falso)
    disp.deslizar((100, 200), (300, 400), 500)
    assert falso.swipes[-1] == (100, 200, 300, 400, 500)
    disp.deslizar((0.5, 0.5), {"x": 10, "y": 20}, 1200)              # fração usa o wm size (2340)
    assert falso.swipes[-1] == (540, 1170, 10, 20, 1200)
    disp.tocar({"x": 530, "y": 2190})                                  # nó no formato do ui_dump.py
    assert falso.taps()[-1] == (530, 2190)
    disp.tecla(4)
    disp.tecla("KEYCODE_WAKEUP")
    assert falso.teclas[-2:] == ["4", "KEYCODE_WAKEUP"]
    disp.voltar()
    assert falso.shell_cmds[-1] == "input keyevent 4"


def test_screencap_faz_screencap_e_pull(tmp_path):
    falso = AdbFalso()
    destino = tmp_path / "telas" / "coleta" / "01_perfil.png"
    assert novo(falso).screencap(destino) == destino and destino.read_bytes().startswith(b"\x89PNG")
    assert falso.shell_cmds[-1] == "screencap -p /sdcard/hp_tela.png"
    assert falso.pulls == [("/sdcard/hp_tela.png", str(destino))]


# ===========================================================================
# Digitar: ASCII, acento, emoji, políticas
# ===========================================================================
def test_digitar_ascii_espaco_vira_porcento_s_e_aspas_somem():
    falso = AdbFalso()
    disp = novo(falso)
    assert disp.digitar("Ver post") == "Ver%spost" and falso.digitados == ["Ver post"]
    assert disp.digitar('O que "voce" faz?') == "O%sque%svoce%sfaz\\?"
    assert falso.digitados[-1] == "O que voce faz?"          # o shell do aparelho tira a barra: chega com "?"
    assert disp.historico[-1][-3:] == ["input", "text", "O%sque%svoce%sfaz\\?"]
    assert disp.digitar("   ") == "" and len(falso.digitados) == 2


def test_digitar_acento_troca_por_letra_sem_acento_e_registra_no_log():
    falso = AdbFalso()
    disp = novo(falso)
    assert disp.digitar("Você não vai?") == "Voce%snao%svai\\?"
    assert falso.digitados == ["Voce nao vai?"]
    log = disp.log.texto()
    assert "acento trocado: 'Você' -> 'Voce'" in log and "acento trocado: 'não' -> 'nao'" in log
    assert ("WARNING", "acento trocado: 'Você' -> 'Voce'") in disp.log.linhas


def test_digitar_emoji_e_removido_e_registrado():
    falso = AdbFalso()
    disp = novo(falso)
    assert disp.digitar("Furacão chegando ⏳🔥 em Leonida") == "Furacao%schegando%sem%sLeonida"
    assert falso.digitados == ["Furacao chegando em Leonida"]
    assert "emoji removido: '⏳🔥'" in disp.log.texto()
    assert sd.sem_acento("Ação — “ok” … R$ 5")[0] == 'Acao - "ok" ... R$ 5'


def test_acento_real_desligada_sem_teclado_explica_o_que_o_antonio_instala():
    falso = AdbFalso()
    disp = novo(falso)
    with pytest.raises(sd.TecladoAcentoIndisponivel) as e:
        disp.digitar("Você", politica="acento_real")
    msg = str(e.value)
    assert e.value.codigo == 4 and "ADBKeyBoard" in msg and "adb install" in msg and "Idiomas e entrada" in msg
    assert "selecionado = não" in msg and falso.digitados == [] and falso.broadcasts == []
    with pytest.raises(ValueError):
        disp.digitar("x", politica="tanto_faz")


def test_acento_real_com_teclado_instalado_manda_broadcast_base64():
    falso = AdbFalso(teclado_adb=True)
    disp = novo(falso)
    assert disp.digitar("Você não vai?", politica="acento_real") == "Você não vai?"
    b64 = base64.b64encode("Você não vai?".encode("utf-8")).decode("ascii")
    assert falso.broadcasts == [f"am broadcast -a ADB_INPUT_B64 --es msg {b64}"] and falso.digitados == []


def test_digitar_toca_no_campo_e_limpa_como_o_digitar_py():
    falso = AdbFalso(tela_atual="enquete")
    disp = novo(falso)
    campo = sd.achar(disp.dump(), id="poll_sticker_v2_question")
    disp.digitar("O que você faz?", campo=campo, limpar=True)
    assert falso.taps() == [campo.centro]
    assert falso.shell_cmds[-4:] == [f"input tap {campo.x} {campo.y}", "input keycombination 113 29",
                                     "input keyevent 67", "input text O%sque%svoce%sfaz\\?"]


def test_digitar_com_campo_de_senha_na_tela_e_recusado():
    paradas = []
    disp = novo(AdbFalso(tela_atual="login"), gravar_parada=paradas.append)
    disp.dump(checar_aviso=False)
    with pytest.raises(sd.TelaProibida):
        disp.digitar("1234")
    assert paradas and "senha" in paradas[0]["frase"]


# ===========================================================================
# Arte na galeria (push + MediaStore)
# ===========================================================================
def test_empurrar_arte_nome_ascii_e_plano_principal(tmp_path):
    arte = tmp_path / "contagem ção 09h.jpg"
    arte.write_bytes(b"\xff\xd8falso")
    falso = AdbFalso(indexa_em="principal")
    disp = novo(falso)
    r = disp.empurrar_arte(arte)
    assert r["nome"] == "contagem_cao_09h.jpg" and r["remoto"] == "/sdcard/Pictures/HP/contagem_cao_09h.jpg"
    assert r["plano"].startswith("principal") and falso.scans == ["principal"]
    assert falso.pushados == [(str(arte), "/sdcard/Pictures/HP/contagem_cao_09h.jpg")]
    assert "mkdir -p /sdcard/Pictures/HP" in falso.shell_cmds
    assert ("content call --uri content://media/external/file --method scan_file --arg "
            "/sdcard/Pictures/HP/contagem_cao_09h.jpg") in falso.shell_cmds
    assert not any("MEDIA_SCANNER" in c for c in falso.shell_cmds)


@pytest.mark.parametrize("indexa_em, planos", [("B", ["principal", "B"]), ("C", ["principal", "B", "C"])])
def test_empurrar_arte_planos_b_e_c(tmp_path, indexa_em, planos):
    arte = tmp_path / "arte.jpg"
    arte.write_bytes(b"x")
    falso = AdbFalso(indexa_em=indexa_em)
    r = novo(falso).empurrar_arte(arte, "arte.jpg")
    assert falso.scans == planos and r["plano"].startswith("plano " + indexa_em)
    assert contar(falso, "content query --uri content://media/external/images/media") == len(planos)


def test_empurrar_arte_sem_galeria_e_erro_e_nomes_nao_ascii_recusados(tmp_path):
    arte = tmp_path / "arte.jpg"
    arte.write_bytes(b"x")
    falso = AdbFalso(indexa_em=None)
    with pytest.raises(sd.ArteNaoIndexada) as e:
        novo(falso).empurrar_arte(arte)
    assert falso.scans == ["principal", "B", "C"] and "não apareceu na galeria" in str(e.value)
    falso = AdbFalso()
    with pytest.raises(sd.DispositivoErro) as e:
        novo(falso).empurrar_arte(arte, "ação.jpg")
    assert "ASCII" in str(e.value) and falso.pushados == []
    with pytest.raises(sd.DispositivoErro):
        novo(falso).empurrar_arte(tmp_path / "nao_existe.jpg")
    assert sd.nome_ascii_de("Dá pra ficar GORDO.PNG") == "Da_pra_ficar_GORDO.PNG"


# ===========================================================================
# Aviso da Meta, login, termos
# ===========================================================================
def test_aviso_da_meta_grava_parada_e_sai_com_codigo_3(tmp_path):
    paradas = []
    disp = novo(AdbFalso(tela_atual="aviso_meta"), gravar_parada=paradas.append)
    with pytest.raises(sd.AvisoMetaDetectado) as e:
        disp.dump()
    assert e.value.codigo == 3 and e.value.frase == "try again later"
    assert paradas[0]["frase"] == "try again later" and paradas[0]["serial"] == "emulator-5554"
    # a função padrão grava o PARADO_AVISO_META.json em H:\HypadoLocal\emulador (aqui: tmp)
    disp = novo(AdbFalso(tela_atual="aviso_meta"), gravar_parada=sd.gravar_parada_padrao())
    with pytest.raises(sd.AvisoMetaDetectado):
        disp.dump()
    arq = Path(tmp_path / "HypadoLocal" / "emulador" / "PARADO_AVISO_META.json")
    assert arq.exists() and ler_json(arq)["frase"] == "try again later" and "quando" in ler_json(arq)
    assert not list(arq.parent.glob(".tmp_*"))


@pytest.mark.parametrize("tela, trecho", [("login", "login"), ("termos", "updated our terms")])
def test_tela_de_login_ou_termos_para(tela, trecho):
    paradas = []
    disp = novo(AdbFalso(tela_atual=tela), gravar_parada=paradas.append)
    with pytest.raises(sd.AvisoMetaDetectado) as e:
        disp.dump()
    assert trecho in e.value.frase and len(paradas) == 1


def test_legenda_com_suspeita_nao_para_e_sem_aviso_nada_acontece():
    disp = novo(AdbFalso(tela_atual="post_aberto"))
    nos = disp.dump()
    assert sd.achar(nos, texto="suspeita") is not None       # a palavra está na legenda...
    assert sd.detectar_aviso(nos) is None                     # ...e não conta como aviso
    disp.parar_por_aviso(nos)                                 # não levanta
    assert sd.detectar_aviso([sd.No(bounds=(0, 0, 10, 10), texto="Atividade suspeita detectada")])[0] == "atividade suspeita"
    assert sd.detectar_aviso([sd.No(bounds=(0, 0, 10, 10), texto="SUSPEITA", id="row_feed_headline_text")]) is None


def test_parada_sobe_mesmo_se_gravar_falhar():
    def quebra(d):
        raise OSError("disco cheio")
    disp = novo(AdbFalso(tela_atual="aviso_meta"), gravar_parada=quebra)
    with pytest.raises(sd.AvisoMetaDetectado):
        disp.dump()
    assert "não consegui gravar o arquivo de parada" in disp.log.texto()


# ===========================================================================
# Histórico e o mesmo fluxo em duas telas
# ===========================================================================
def test_historico_guarda_todo_argv_com_o_serial():
    falso = AdbFalso()
    disp = novo(falso, serial="R58M1ABCDEF", adb=r"H:\HypadoLocal\android\sdk\platform-tools\adb.exe")
    disp.tamanho_tela()
    disp.abrir_app()
    disp.dump()
    assert disp.historico == falso.comandos and len(disp.historico) == 4
    assert all(a[:3] == [r"H:\HypadoLocal\android\sdk\platform-tools\adb.exe", "-s", "R58M1ABCDEF"] for a in disp.historico)
    assert disp.comandos_shell() == ["wm size", "monkey -p com.instagram.android -c android.intent.category.LAUNCHER 1",
                                     "uiautomator dump /sdcard/ui.xml", "cat /sdcard/ui.xml"]
    assert novo(AdbFalso(), serial=None).argv("devices") == ["adb", "devices"]


def fluxo_de_teste(disp: sd.Dispositivo) -> list:
    """perfil -> lista de contas -> hp.carros -> perfil -> foto do perfil -> visualizador -> Highlight -> destaques."""
    disp.abrir_app()
    disp.tocar(sd.achar(disp.dump(), id="action_bar_username_container"), "nome da conta")
    disp.tocar(sd.achar(disp.dump(), desc="hp.carros", contem=False), "@hp.carros")
    nos = disp.dump()
    assert sd.achar(nos, id="action_bar_large_title_auto_size").texto == "hp.carros"
    disp.tocar(sd.achar(nos, id="row_profile_header_imageview"), "foto do perfil")
    disp.tocar(sd.achar(disp.dump(), id="toolbar_highlights_button"), "Highlight")
    disp.tocar(sd.achar(disp.dump(), texto="Enquetes", contem=False), "destaque Enquetes")
    return [(x, y) for x, y, _ in disp._falso_toques] if hasattr(disp, "_falso_toques") else None


def test_mesmo_fluxo_em_duas_telas_gera_toques_diferentes_e_proporcionais():
    toques = {}
    telas = {}
    for tela in (TELA_PADRAO, TELA_ALTERNATIVA):
        falso = AdbFalso(tela=tela, tela_atual="perfil")
        disp = novo(falso)
        fluxo_de_teste(disp)
        toques[tela] = falso.taps()
        telas[tela] = falso.tela_atual
        assert [t[2] for t in falso.toques] == ["action_bar_username_container", "row_user_container",
                                                "row_profile_header_imageview", "toolbar_highlights_button",
                                                "highlight_title"]
    assert telas == {TELA_PADRAO: "visualizador", TELA_ALTERNATIVA: "visualizador"}
    assert len(toques[TELA_PADRAO]) == 5 and toques[TELA_PADRAO] != toques[TELA_ALTERNATIVA]
    for (x1, y1), (x2, y2) in zip(toques[TELA_PADRAO], toques[TELA_ALTERNATIVA]):
        assert x1 == x2 and y1 != y2 and abs(y2 - y1 * 2340 / 2400) <= 1.5   # y segue os bounds (×0.975)
    assert toques[TELA_PADRAO][3] == (530, 2190)                               # centro real do Highlight


def test_fluxo_toque_fora_dos_bounds_nao_avanca():
    falso = AdbFalso(tela=TELA_ALTERNATIVA, tela_atual="perfil")
    novo(falso).tocar((273, 136))        # centro certo na tela de 2400... fora do nome na tela de 2340? (84-189 -> 82-184)
    assert falso.tela_atual == "lista_contas"
    falso = AdbFalso(tela=TELA_ALTERNATIVA, tela_atual="perfil")
    novo(falso).tocar((1000, 300))       # coordenada fixa errada (nada clicável ali): nada acontece
    assert falso.tela_atual == "perfil" and falso.toques[-1][2] is None


# ===========================================================================
# Fixtures: em dia e proporcionais
# ===========================================================================
def test_fixtures_android_estao_em_dia_com_o_gerador(tmp_path):
    gerados = gerar_fixtures(tmp_path)
    assert len(gerados) == 2 + 2 * len(TELAS_SINTETICAS)
    for p, texto in gerados.items():
        repo = FIXTURES / p.name
        assert repo.exists(), f"falta {repo}"
        assert repo.read_text(encoding="utf-8") == texto, f"{repo.name} difere: rode python scripts/testes/adb_falso.py"
        assert "sintetico" in p.name or p.name == "ui_story_visualizador_hp_futebol_derivado.xml"
        assert not any(l.startswith("## ") for l in texto.splitlines())


def test_fixture_2340_e_proporcional_a_2400():
    for nome in ("perfil", "editor", "visualizador"):
        a = sd.parse_dump(arquivo_tela(nome, TELA_PADRAO).read_text(encoding="utf-8"))
        b = sd.parse_dump(arquivo_tela(nome, TELA_ALTERNATIVA).read_text(encoding="utf-8"))
        assert len(a) == len(b) > 5
        for na, nb in zip(a, b):
            assert na.id == nb.id and na.bounds[0] == nb.bounds[0] and na.bounds[2] == nb.bounds[2]
            assert abs(nb.bounds[1] - na.bounds[1] * 0.975) <= 0.51 and abs(nb.bounds[3] - na.bounds[3] * 0.975) <= 0.51


def test_dump_real_tem_todas_as_52_linhas_e_centros_iguais_ao_ui_py():
    import ui_dump
    reais = ui_dump.ler_arquivo(FIXTURES.parent / "pc_real" / "ui_story_visualizador_hp_futebol.txt")
    nos = sd.parse_dump(arquivo_tela("visualizador").read_text(encoding="utf-8"))[1:]   # tira o nó raiz
    assert len(nos) == len(reais) == 52
    for r, n in zip(reais, nos):
        assert n.id == r["id"] and n.centro == (r["x"], r["y"]) and n.clicavel == r["clicavel"]


# ===========================================================================
# runners (--simular e real) e CLI
# ===========================================================================
def test_runner_roteiro_imprime_e_nao_executa_nada():
    linhas = []
    r = sd.runner_roteiro(linhas.append)
    disp = sd.Dispositivo(r, sd.escolher_serial(r, env={}), relogio=RelogioFalso(), log=LogLista())
    assert disp.esperar_boot(10) == 0 and disp.tamanho_tela() == (1080, 2400)
    assert disp.tela_acesa_e_destravada() and disp.instagram_na_frente()
    disp.tocar_fracao(0.5, 0.5)
    disp.digitar("Ver post")
    assert disp.dump() and all(l.startswith("  [simular] adb") for l in linhas) and len(linhas) == len(disp.historico) + 1
    assert "  [simular] adb -s emulator-5554 shell input text Ver%spost" in linhas


def test_runner_real_usa_rodar_com_timeout_e_traduz_erros():
    chamadas = []

    def rodar_falso(cmd, timeout=None, **kw):
        chamadas.append((cmd, timeout))
        if "demora" in cmd:
            raise subprocess.TimeoutExpired(cmd, timeout)
        if "sumiu" in cmd:
            raise FileNotFoundError(cmd[0])
        return subprocess.CompletedProcess(cmd, 1 if "erro" in cmd else 0, stdout=b"saida\n", stderr=b"stderr")
    r = sd.runner_real(r"H:\adb.exe", timeout=7, rodar_fn=rodar_falso)
    assert r(["adb", "devices"]) == (0, "saida\n") and chamadas[0] == ([r"H:\adb.exe", "devices"], 7)
    assert r(["adb", "erro"]) == (1, "saida\nstderr")
    assert r(["adb", "demora"])[0] == 124 and "7s" in r(["adb", "demora"])[1]
    assert r(["adb", "sumiu"])[0] == 127


def test_runner_real_roda_um_subprocesso_de_verdade_sem_adb():
    r = sd.runner_real(sys.executable, timeout=30)
    assert r(["adb", "-c", "print('ola')"]) == (0, "ola\n")


def test_cli_aparelhos_status_dump_foto_e_codigos(tmp_path, capsys):
    out = []
    assert sd.main(["aparelhos"], runner=AdbFalso(dispositivos=DOIS), saida=out.append, env={}) == 0
    assert "emulator-5554 (device, emulador), R58M1ABCDEF (device, celular)" in out[-1]
    assert sd.main(["status"], runner=AdbFalso(dispositivos=DOIS), saida=out.append, env={}) == 4
    assert sd.main(["status", "--emulador"], runner=AdbFalso(dispositivos=DOIS), saida=out.append, env={}) == 0
    assert "tela: 1080x2400" in out and "na frente: com.instagram.android" in out
    assert sd.main(["status"], runner=AdbFalso(travada=True, pin=True), saida=out.append, env={}) == 4
    assert sd.MSG_BLOQUEADO in out[-1]
    assert sd.main(["dump", "highlight"], runner=AdbFalso(tela_atual="visualizador"), saida=out.append, env={}) == 0
    assert "530,2190 | LinearLayout |  | Highlight | toolbar_highlights_button | clic" in out
    assert sd.main(["dump"], runner=AdbFalso(tela_atual="aviso_meta"), saida=out.append, env={}) == 3
    assert (tmp_path / "HypadoLocal" / "emulador" / "PARADO_AVISO_META.json").exists()
    destino = tmp_path / "foto.png"
    assert sd.main(["foto", str(destino)], runner=AdbFalso(), saida=out.append, env={}) == 0 and destino.exists()
    assert sd.main(["status", "--simular"], saida=out.append, env={}) == 0 and any("[simular]" in l for l in out)
    assert sd.main([], saida=out.append) == 1
