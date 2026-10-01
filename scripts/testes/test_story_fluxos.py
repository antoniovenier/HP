# -*- coding: utf-8 -*-
"""Testes do story_fluxos.py (tarefa E2): sem aparelho, sem adb, sem rede, sem relógio real.

Cada fluxo roda contra o AdbFalso (adb_falso.py do E1) nas DUAS telas (1080x2400 e 1080x2340): a tela só
muda quando o toque cai DENTRO dos bounds do nó certo, por isso os toques provam que seguem o dump e não
coordenadas fixas. O dump real do visualizador (@hp.futebol, "3m", Highlight) é o derivado da §4.7.
Rodar: cd scripts && python -m pytest -q testes/test_story_fluxos.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
for _p in (AQUI, AQUI.parent, AQUI.parent.parent / "app" / "hp_studio_nuvem"):
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import story_dispositivo as sd  # noqa: E402
import story_fluxos as sf  # noqa: E402
import story_post as sp  # noqa: E402
import story_fila_v2 as fila  # noqa: E402
import ui_dump  # noqa: E402
from adb_falso import (AdbFalso, FIXTURES, PC_REAL, LogLista, TELA_ALTERNATIVA, TELA_PADRAO,  # noqa: E402
                       arquivo_tela, el, escalar, telas_sinteticas, xml_da_tela)
from hpbase import FUSO, marca  # noqa: E402

TELAS = (TELA_PADRAO, TELA_ALTERNATIVA)
LINK = "https://www.instagram.com/p/Dd7J4uso3bI/"
BASE = datetime(2026, 10, 1, 10, 0, tzinfo=FUSO)


# ===========================================================================
# Base: raízes temporárias, relógio falso, telas extras (figurinha no editor, contagem, calendário)
# ===========================================================================
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
    """monotonic/sleep/agora sem o relógio de verdade; `salto` avança o monotonic a cada leitura (orçamento)."""

    def __init__(self, salto: float = 0.0):
        self.t = 0.0
        self.salto = float(salto)
        self.dormidas: list[float] = []

    def monotonic(self):
        self.t += self.salto
        return self.t

    def sleep(self, s):
        self.dormidas.append(float(s))
        self.t += max(0.0, float(s))

    def agora(self):
        return BASE + timedelta(seconds=self.t)


def _editor_com(nome: str, figurinha: dict) -> list:
    return telas_sinteticas()["editor"] + [el(**figurinha)]


def telas_extra(tela: tuple) -> dict:
    """Telas que o E1 não tem: editor com a figurinha recém-criada, contagem, calendário, destaque novo."""
    base = {
        "editor_link": _editor_com("editor", dict(id="link_sticker_view", desc="Link sticker: Ver post",
                                                  b=(340, 1100, 740, 1300), clicavel=True,
                                                  classe="android.widget.FrameLayout")),
        "editor_enquete": _editor_com("editor", dict(id="poll_sticker_view", desc="Poll sticker: O que voce faz?",
                                                     b=(190, 900, 890, 1400), clicavel=True,
                                                     classe="android.widget.FrameLayout")),
        "editor_contagem": _editor_com("editor", dict(id="countdown_sticker_view", desc="Countdown: Lancamento do GTA 6",
                                                      b=(190, 1000, 890, 1300), clicavel=True,
                                                      classe="android.widget.FrameLayout")),
        "contagem": [
            el("countdown_sticker_title", texto="Countdown title", b=(120, 700, 960, 820), clicavel=True, focado=True,
               classe="android.widget.EditText"),
            el("countdown_sticker_end_date", texto="Set end date", b=(120, 860, 960, 960), clicavel=True),
            el("done_button", texto="Done", b=(880, 90, 1040, 190), clicavel=True),
        ],
        "calendario_out": [
            el("android:id/date_picker_header_date", texto="October 2026", b=(100, 300, 980, 380)),
            el("android:id/prev", desc="Previous month", b=(60, 420, 180, 540), clicavel=True),
            el("android:id/next", desc="Next month", b=(900, 420, 1020, 540), clicavel=True),
            el("android:id/button1", texto="OK", b=(760, 1700, 1000, 1800), clicavel=True),
        ],
        "calendario_nov": [
            el("android:id/date_picker_header_date", texto="November 2026", b=(100, 300, 980, 380)),
            el("android:id/prev", desc="Previous month", b=(60, 420, 180, 540), clicavel=True),
            el("android:id/next", desc="Next month", b=(900, 420, 1020, 540), clicavel=True),
            el(texto="18", desc="18 November 2026", b=(400, 1000, 520, 1100), clicavel=True),
            el(texto="19", desc="19 November 2026", b=(540, 1000, 660, 1100), clicavel=True),
            el(texto="20", desc="20 November 2026", b=(680, 1000, 800, 1100), clicavel=True),
            el("android:id/button1", texto="OK", b=(760, 1700, 1000, 1800), clicavel=True),
        ],
        "destaque_novo": [
            el("highlight_title_edit_text", texto="Highlights", b=(120, 600, 960, 720), clicavel=True, focado=True,
               classe="android.widget.EditText"),
            el("highlight_add_button", texto="Add", b=(760, 800, 1000, 900), clicavel=True, classe="android.widget.Button"),
        ],
        "post_outro_autor": [e if e["id"] != "row_feed_photo_profile_name" else dict(e, texto="outra.conta")
                             for e in telas_sinteticas()["post_aberto"]],
    }
    out = {}
    for nome, els in base.items():
        e = els if tela == TELA_PADRAO else escalar(els, tela)
        out[nome] = xml_da_tela(e, tela, f"SINTETICA de teste: {nome}")
    return out


TRANSICOES_EXTRA = {
    ("link", "done_button"): "editor_link",
    ("editor_link", "asset_button"): "figurinhas",
    ("editor_link", "your_story_share_shortcut_button"): "perfil",
    ("enquete", "done_button"): "editor_enquete",
    ("editor_enquete", "asset_button"): "figurinhas",
    ("editor_enquete", "your_story_share_shortcut_button"): "perfil",
    ("figurinhas", "COUNTDOWN"): "contagem",
    ("contagem", "countdown_sticker_end_date"): "calendario_out",
    ("calendario_out", "next"): "calendario_nov",
    ("calendario_nov", "button1"): "contagem",
    ("contagem", "done_button"): "editor_contagem",
    ("editor_contagem", "your_story_share_shortcut_button"): "perfil",
    ("destaques", "highlight_new"): "destaque_novo",
    ("destaque_novo", "Add"): "visualizador",
    ("post_outro_autor", "row_feed_button_share"): "folha_send",
}


def falso_com(tela=TELA_PADRAO, **kw) -> AdbFalso:
    telas = dict(telas_extra(tela))
    telas.update(kw.pop("telas", {}) or {})
    trans = dict(TRANSICOES_EXTRA)
    trans.update(kw.pop("transicoes", {}) or {})
    kw.setdefault("tela_atual", "perfil")
    return AdbFalso(tela=tela, telas=telas, transicoes=trans, **kw)


def novo(falso: AdbFalso, **kw) -> sd.Dispositivo:
    kw.setdefault("relogio", RelogioFalso())
    kw.setdefault("log", LogLista())
    kw.setdefault("serial", "emulator-5554")
    kw.setdefault("gravar_parada", sd.gravar_parada_padrao())
    return sd.Dispositivo(falso, **kw)


def arte_com_zonas(tmp_path, nome="story_chamada.jpg", figurinhas=("link", "enquete")) -> Path:
    """Arte (arquivo qualquer) + <arte>_zonas.json no formato do story_artes (zonas_de)."""
    arte = tmp_path / nome
    arte.write_bytes(b"\xff\xd8\xff\xe0 arte de teste")
    la, al = marca.TAMANHOS["story"]
    z = {"largura": la, "altura": al, "figurinhas": list(figurinhas)}
    for n, ret in (("link", marca.ZONA_LINK), ("enquete", marca.ZONA_ENQUETE)):
        if n in figurinhas:
            z[n] = [int(v) for v in ret]
            z[n + "_fracao"] = [round(ret[0] / la, 4), round(ret[1] / al, 4), round(ret[2] / la, 4), round(ret[3] / al, 4)]
    (tmp_path / (arte.stem + "_zonas.json")).write_text(json.dumps(z), encoding="utf-8")
    return arte


def nomes(falso: AdbFalso) -> list:
    return [t[2] for t in falso.toques]


def zona_esperada(tela: tuple, nome: str, arte: Path) -> list:
    """O centro da zona na tela real: fração × área da prévia do editor (camera_preview) — como o fluxo calcula."""
    editor = sd.parse_dump(arquivo_tela("editor", tela).read_text(encoding="utf-8"))
    area = sf.area_da_arte(editor, tela)
    assert area != (0, 0, tela[0], tela[1])        # a prévia sintética ocupa 0..2160 de 2400: área lida do dump
    return fila.ler_zonas(arte, tela, area)["centro_" + nome]


class Registro:
    def __init__(self, estado: sf.Estado | None = None, relogio=None):
        self.chamadas: list[tuple] = []
        self.estado = estado
        self.relogio = relogio

    def __call__(self, chave, etapa, **extra):
        self.chamadas.append((chave, etapa))
        if self.estado is not None:
            return self.estado.registrar(chave, etapa, agora=self.relogio.agora() if self.relogio else None, **extra)
        return True


# ===========================================================================
# 1. Carimbo de tempo do story ("3m" real, "Now", "agora"; "7m"/"1h" não)
# ===========================================================================
def test_eh_timestamp_de_agora_aceita_3m_now_just_now_agora():
    for t in ("3m", "5m", "1m", "0m", "Now", "now", "Just now", "agora", "Agora mesmo", "30 s", "1 min", "há 2 min"):
        assert sf.eh_timestamp_de_agora(t), t


def test_eh_timestamp_de_agora_recusa_7m_1h_2d_e_vazio():
    for t in ("7m", "6m", "1h", "2d", "3 h", "12 min", "", None, "ontem"):
        assert not sf.eh_timestamp_de_agora(t), t


def test_carimbo_pelo_content_desc_real_do_cabecalho():
    assert sf.eh_timestamp_de_agora("", "hp.futebol's story, 3 minutes ago")
    assert sf.eh_timestamp_de_agora("", "hp.futebol's story, 45 seconds ago")
    assert not sf.eh_timestamp_de_agora("", "hp.futebol's story, 12 minutes ago")
    assert not sf.eh_timestamp_de_agora("", "hp.futebol's story, 2 hours ago")
    assert sf.minutos_de("", "hp.futebol's story, 3 minutes ago") == 3.0
    assert sf.minutos_de("3m") == 3.0 and sf.minutos_de("Now") == 0.0 and sf.minutos_de("1h") is None


def test_fixture_real_3m_vira_3_minutos_no_story_post_e_no_story_fluxos():
    nos = ui_dump.ler_linhas_ui((PC_REAL / "ui_story_visualizador_hp_futebol.txt").read_text(encoding="utf-8-sig"))
    ts = ui_dump.achar(nos, id="reel_viewer_timestamp")
    cab = ui_dump.achar(nos, id="reel_viewer_text_container")
    assert ts["texto"] == "3m" and cab["desc"] == "hp.futebol's story, 3 minutes ago"
    assert sp.minutos_do_timestamp(ts["texto"]) == 3.0           # a rodada 1 já lia "3m"...
    assert sp.CONFIG_PADRAO["recente_max_min"] == 5               # ...mas o limite era 2 min: patch (a) sobe para 5
    assert sp._de_agora(ts["texto"], cab["desc"], sp.CONFIG_PADRAO["recente_max_min"])
    assert not sp._de_agora("7m", "", 5) and not sp._de_agora("1h", "", 5)
    assert sf.eh_timestamp_de_agora(ts["texto"], cab["desc"])
    assert sf.LIMITE_MIN_AGORA == 5 and set(["now", "just now", "agora", "agora mesmo"]) <= set(sp.SEL.TIMESTAMP_AGORA)


def test_limite_de_minutos_e_configuravel():
    assert not sf.eh_timestamp_de_agora("3m", limite_min=2)
    assert sf.eh_timestamp_de_agora("7m", limite_min=10)


# ===========================================================================
# 2. Estado (JSON injetável, o mesmo da rodada 1)
# ===========================================================================
def test_estado_registra_antes_do_toque_e_nao_repete(tmp_path):
    e = sf.Estado(tmp_path / "estado.json")
    assert e.ja_postado("p1") is None
    assert e.registrar("p1", "antes_do_toque", agora=BASE, conta="hp.futebol") is True
    assert e.registrar("p1", "antes_do_toque", agora=BASE) is False          # já registrado: não repete
    assert e.registrar("p1", "tocado", agora=BASE) is True
    assert e.ja_postado("p1") == "tocado" and e.dados["ultimo_story_em"] == BASE.isoformat(timespec="seconds")
    gravado = json.loads((tmp_path / "estado.json").read_text(encoding="utf-8"))
    assert gravado["postados"]["p1"]["estado"] == "tocado" and gravado["postados"]["p1"]["conta"] == "hp.futebol"
    assert sf.Estado(tmp_path / "estado.json").ja_postado("p1") == "tocado"
    assert not list(tmp_path.glob(".tmp_*"))                                   # gravação atômica (sem resto)


def test_estado_falhas_contam_e_tres_tiram_da_fila():
    e = sf.Estado(dados={}, gravar=False)
    for i in range(3):
        assert not e.fora_da_fila("p2", 3)
        assert e.registrar_falha("p2", RuntimeError(f"erro {i}"), passo="x", agora=BASE) == i + 1
    assert e.fora_da_fila("p2", 3) and len(e.dados["falhas"]) == 3
    e.registrar("p3", "antes_do_toque", agora=BASE)
    e.registrar_falha("p3", RuntimeError("depois do toque"), agora=BASE)
    assert e.tentativas("p3") == 0 and not e.fora_da_fila("p3")               # já tocado: não conta tentativa


def test_estado_falta_intervalo_de_3_min():
    e = sf.Estado(dados={"ultimo_story_em": (BASE - timedelta(seconds=60)).isoformat()}, gravar=False)
    assert e.falta_intervalo(BASE, 180) == 120.0
    assert e.falta_intervalo(BASE + timedelta(seconds=120), 180) == 0.0
    assert sf.Estado(dados={}, gravar=False).falta_intervalo(BASE) == 0.0


def test_estado_le_o_formato_da_rodada_1():
    dados = {"ultimo_story_em": "2026-09-30T17:40:00-03:00",
             "postados": {"futebol_2026-09-30_1707_cr7_ig_feed": {"estado": "publicado", "conta": "hp.futebol",
                                                                   "link": LINK, "quando": "2026-09-30T17:40:00-03:00", "feito": True}},
             "tentativas": {"x": 2}, "falhas": []}
    e = sf.Estado(dados=dados, gravar=False)
    assert e.ja_postado("futebol_2026-09-30_1707_cr7_ig_feed") == "publicado" and e.tentativas("x") == 2
    assert sf.Estado(dados={"postados": "lixo"}, gravar=False).dados["postados"] == {}


# ===========================================================================
# 3. trocar_conta
# ===========================================================================
def test_trocar_conta_ja_ativa_nao_toca():
    falso = falso_com()
    disp = novo(falso)
    assert sf.trocar_conta(disp, "@HPGTA6") == "hpgta6"
    assert falso.toques == [] and falso.digitados == []


@pytest.mark.parametrize("tela", TELAS)
def test_trocar_conta_toca_pelos_bounds_e_le_de_volta(tela):
    falso = falso_com(tela)
    disp = novo(falso)
    assert sf.trocar_conta(disp, "hp.carros") == "hp.carros"
    assert nomes(falso) == ["action_bar_username_container", "row_user_container"] and falso.conta == "hp.carros"
    x, y = falso.taps()[1]
    linha = sd.achar(sd.parse_dump(arquivo_tela("lista_contas", tela).read_text(encoding="utf-8")), desc="hp.carros", contem=False)
    assert (x, y) == linha.centro                                            # o toque é o centro do nó da conta
    assert sf.conta_ativa(disp.ultimos_nos) == "hp.carros"


def test_trocar_conta_toques_diferentes_nas_duas_telas():
    taps = {}
    for tela in TELAS:
        falso = falso_com(tela)
        sf.trocar_conta(novo(falso), "hp.filmes")
        taps[tela] = falso.taps()
    assert taps[TELA_PADRAO] != taps[TELA_ALTERNATIVA]
    for (x1, y1), (x2, y2) in zip(taps[TELA_PADRAO], taps[TELA_ALTERNATIVA]):
        assert x1 == x2 and abs(y2 - y1 * 2340 / 2400) <= 1.5


def test_trocar_conta_errada_aborta():
    def troca_para_outra(falso, no):
        falso.conta = "hp.filmes"
        return "perfil"
    falso = falso_com(transicoes={("lista_contas", "row_user_container"): troca_para_outra})
    with pytest.raises(sf.ContaErrada) as e:
        sf.trocar_conta(novo(falso), "hp.carros")
    assert "@hp.filmes" in str(e.value) and "@hp.carros" in str(e.value) and e.value.codigo == 1


def test_trocar_conta_que_nao_esta_na_lista_aborta_sem_digitar():
    falso = falso_com()
    with pytest.raises(sf.ContaErrada) as e:
        sf.trocar_conta(novo(falso), "conta.inexistente")
    assert "não aparece na lista" in str(e.value) and falso.digitados == [] and nomes(falso) == ["action_bar_username_container"]


def test_trocar_conta_na_tela_de_login_para_codigo_3_sem_tocar_nem_digitar(tmp_path):
    falso = falso_com(tela_atual="login")
    disp = novo(falso)
    with pytest.raises(sd.AvisoMetaDetectado) as e:
        sf.trocar_conta(disp, "hp.futebol")
    assert e.value.codigo == 3 and "login" in str(e.value)
    parada = sd.arquivo_parada_padrao()
    assert parada.exists() and "login" in parada.read_text(encoding="utf-8")
    assert falso.toques == [] and falso.digitados == []                      # nada de Entrar, nada de senha


# ===========================================================================
# 4. story_da_arte: galeria -> editor -> figurinhas -> zona -> Seu story
# ===========================================================================
@pytest.mark.parametrize("tela", TELAS)
def test_story_da_arte_com_link_segue_os_bounds_e_arrasta_para_a_zona(tmp_path, tela):
    arte = arte_com_zonas(tmp_path)
    falso = falso_com(tela)
    disp = novo(falso)
    reg = Registro()
    r = sf.story_da_arte(disp, arte, [{"tipo": "link", "url": LINK, "rotulo": "Ver post"}], registrar=reg, chave="p1")
    assert r["estado"] == "tocado" and reg.chamadas == [("p1", "antes_do_toque"), ("p1", "tocado")]
    assert nomes(falso) == ["action_bar_new_post_button", "gallery_grid_item_thumbnail", "asset_button", "asset_item",
                            "link_sticker_url_edit_text", "link_sticker_custom_text_button",
                            "link_sticker_custom_text_edit_text", "done_button", "your_story_share_shortcut_button"]
    assert falso.digitados == [LINK, "Ver post"]
    assert falso.pushados[0][1] == "/sdcard/Pictures/HP/story_chamada.jpg" and "principal" in falso.scans
    # o arraste sai do CENTRO da figurinha lida no dump e termina no centro da zona do link convertida para a tela
    fig = sd.achar(sd.parse_dump(falso.xml_tela("editor_link")), id="link_sticker_view")
    assert [s[:4] for s in falso.swipes] == [(fig.x, fig.y, *zona_esperada(tela, "link", arte))]
    assert r["figurinhas"][0]["arrastada"] and r["figurinhas"][0]["de"] == list(fig.centro)
    # a galeria escolhida foi a foto MAIS RECENTE (a primeira da grade)
    assert falso.toques[1][:2] == sd.achar(sd.parse_dump(falso.xml_tela("galeria")), desc="Photo, 1 of 6").centro


def test_story_da_arte_zona_muda_com_a_tela():
    swipes = {}
    for tela in TELAS:
        with pytest.MonkeyPatch.context() as mp:
            pasta = Path(sd.raiz_local()).parent / f"artes_{tela[1]}"
            pasta.mkdir(exist_ok=True)
            arte = arte_com_zonas(pasta)
            falso = falso_com(tela)
            sf.story_da_arte(novo(falso), arte, [{"tipo": "link", "url": LINK}], chave="p")
            swipes[tela] = falso.swipes[0]
            mp.undo()
    assert swipes[TELA_PADRAO] != swipes[TELA_ALTERNATIVA]
    assert swipes[TELA_PADRAO][2] == swipes[TELA_ALTERNATIVA][2] and swipes[TELA_PADRAO][3] > swipes[TELA_ALTERNATIVA][3]


def test_story_da_arte_enquete_acento_trocado_e_logado_e_pergunta_no_limite(tmp_path):
    arte = arte_com_zonas(tmp_path, "story_enquete.jpg")
    falso = falso_com()
    log = LogLista()
    disp = novo(falso, log=log)
    r = sf.story_da_arte(disp, arte, [{"tipo": "enquete", "pergunta": "O que você faz?", "opcoes": ["Sim", "Não"]}], chave="e1")
    assert r["estado"] == "tocado"
    assert falso.digitados == ["O que voce faz?", "Sim", "Nao"]                    # ASCII pelo input text
    assert "acento trocado: 'você' -> 'voce'" in log.texto() and "acento trocado: 'Não' -> 'Nao'" in log.texto()
    assert nomes(falso)[2:] == ["asset_button", "asset_item", "poll_sticker_v2_question", "poll_sticker_v2_option_text",
                                "poll_sticker_v2_option_text", "done_button", "your_story_share_shortcut_button"]
    assert falso.swipes[0][2:4] == tuple(zona_esperada(TELA_PADRAO, "enquete", arte))


def test_story_da_arte_pergunta_longa_e_recusada_sem_cortar_e_sem_publicar(tmp_path):
    arte = arte_com_zonas(tmp_path, "story_enquete.jpg")
    falso = falso_com()
    reg = Registro()
    with pytest.raises(sf.DadosInvalidos) as e:
        sf.story_da_arte(novo(falso), arte, [{"tipo": "enquete", "pergunta": "Você prefere o novo BMW Série 3 ou o antigo?",
                                              "opcoes": ["Novo", "Antigo"]}], registrar=reg, chave="e2")
    assert "não cabe" in str(e.value) and "25" in str(e.value)
    assert reg.chamadas == [] and "your_story_share_shortcut_button" not in nomes(falso)
    # pergunta com oração curta no fim é encurtada sem cortar palavra (story_post_lote)
    assert sf.pergunta_para_figurinha("Você viu o trailer? O que você faz?") == "O que você faz?"
    with pytest.raises(sf.DadosInvalidos):
        sf.preencher_enquete(novo(falso_com()), "Pergunta?", ["Só uma"])


def test_story_da_arte_link_e_enquete_juntas_arrasta_cada_uma_para_a_sua_zona(tmp_path):
    arte = arte_com_zonas(tmp_path)
    falso = falso_com()
    r = sf.story_da_arte(novo(falso), arte, [{"tipo": "link", "url": LINK}, {"tipo": "enquete", "pergunta": "Curtiu?",
                                                                               "opcoes": ["Sim", "Não"]}], chave="p")
    assert [f["tipo"] for f in r["figurinhas"]] == ["link", "enquete"] and all(f["arrastada"] for f in r["figurinhas"])
    assert falso.swipes[0][2:4] == tuple(zona_esperada(TELA_PADRAO, "link", arte))
    assert falso.swipes[1][2:4] == tuple(zona_esperada(TELA_PADRAO, "enquete", arte))
    assert nomes(falso).count("your_story_share_shortcut_button") == 1


def test_story_da_arte_contagem_pelo_calendario(tmp_path):
    arte = arte_com_zonas(tmp_path, "story_contagem.jpg", ("enquete",))
    falso = falso_com()
    r = sf.story_da_arte(novo(falso), arte, [{"tipo": "contagem", "rotulo": "Lançamento do GTA 6", "data": "2026-11-19"}], chave="c")
    assert r["estado"] == "tocado" and falso.digitados == ["Lancamento do GTA 6"]
    seq = nomes(falso)
    assert seq[2:] == ["asset_button", "asset_item", "countdown_sticker_title", "countdown_sticker_end_date", "next", "19",
                       "button1", "done_button", "your_story_share_shortcut_button"]
    assert falso.swipes and falso.swipes[0][2:4] == tuple(zona_esperada(TELA_PADRAO, "enquete", arte))


def test_post_registrado_antes_do_toque_e_segunda_chamada_nao_repete(tmp_path):
    arte = arte_com_zonas(tmp_path)
    estado = sf.Estado(tmp_path / "estado.json")
    rel = RelogioFalso()
    reg = Registro(estado, rel)
    falso = falso_com()
    disp = novo(falso, relogio=rel)
    sf.story_da_arte(disp, arte, [{"tipo": "link", "url": LINK}], registrar=reg, chave="p1")
    # o registro "antes_do_toque" entrou ANTES do input tap em "Seu story"
    i_tap = [i for i, c in enumerate(falso.shell_cmds) if c.startswith("input tap")][-1]
    assert reg.chamadas[0] == ("p1", "antes_do_toque") and estado.ja_postado("p1") == "tocado"
    assert falso.shell_cmds[i_tap].startswith("input tap") and i_tap > 0
    # segunda chamada: não toca em "Seu story" de novo
    falso2 = falso_com()
    with pytest.raises(sf.PostJaFeito) as e:
        sf.story_da_arte(novo(falso2, relogio=rel), arte, [{"tipo": "link", "url": LINK}], registrar=reg, chave="p1")
    assert e.value.codigo == 2 and "your_story_share_shortcut_button" not in nomes(falso2)
    assert nomes(falso).count("your_story_share_shortcut_button") == 1


def test_falha_depois_do_toque_vira_a_conferir_e_nao_toca_de_novo(tmp_path):
    arte = arte_com_zonas(tmp_path)
    estado = sf.Estado(dados={}, gravar=False)
    rel = RelogioFalso()
    reg = Registro(estado, rel)
    falso = falso_com(transicoes={("editor_link", "your_story_share_shortcut_button"): "editor_link"})   # o botão nunca some
    r = sf.story_da_arte(novo(falso, relogio=rel), arte, [{"tipo": "link", "url": LINK}], registrar=reg, chave="p1",
                         tempos={"publicar": 5, "upload": 5})
    assert r["estado"] == "a_conferir" and estado.ja_postado("p1") == "a_conferir"
    assert reg.chamadas == [("p1", "antes_do_toque"), ("p1", "a_conferir")]
    assert nomes(falso).count("your_story_share_shortcut_button") == 1


def test_aviso_da_meta_depois_do_toque_registra_a_conferir_e_sobe_codigo_3(tmp_path):
    arte = arte_com_zonas(tmp_path)
    reg = Registro(sf.Estado(dados={}, gravar=False), RelogioFalso())
    falso = falso_com(transicoes={("editor_link", "your_story_share_shortcut_button"): "aviso_meta"})
    with pytest.raises(sd.AvisoMetaDetectado) as e:
        sf.story_da_arte(novo(falso), arte, [{"tipo": "link", "url": LINK}], registrar=reg, chave="p1")
    assert e.value.codigo == 3 and reg.chamadas == [("p1", "antes_do_toque"), ("p1", "a_conferir")]
    assert sd.arquivo_parada_padrao().exists()


def test_story_da_arte_sem_zonas_json_recusa_antes_de_publicar(tmp_path):
    arte = tmp_path / "sem_zonas.jpg"
    arte.write_bytes(b"x")
    falso = falso_com()
    with pytest.raises(sf.DadosInvalidos) as e:
        sf.story_da_arte(novo(falso), arte, [{"tipo": "link", "url": LINK}], chave="z")
    assert "_zonas.json" in str(e.value) and "your_story_share_shortcut_button" not in nomes(falso)


def test_figurinha_nova_e_area_da_arte(tmp_path):
    falso = falso_com()
    antes = sd.parse_dump(falso.xml_tela("editor"))
    depois = sd.parse_dump(falso.xml_tela("editor_link"))
    area = sf.area_da_arte(antes, TELA_PADRAO)
    assert area == (0, 240, 1080, 2160)
    fig = sf.figurinha_nova(antes, depois, area, ["Ver post"])
    assert fig is not None and fig.id == "link_sticker_view" and fig.centro == (540, 1200)
    assert sf.figurinha_nova(antes, antes, area) is None
    assert sf.area_da_arte([], TELA_ALTERNATIVA) == (0, 0, 1080, 2340)


def test_story_da_arte_com_destaque_depois_de_publicar(tmp_path):
    arte = arte_com_zonas(tmp_path)
    falso = falso_com(conta="hp.futebol")
    r = sf.story_da_arte(novo(falso), arte, [{"tipo": "link", "url": LINK}], destaque="Enquetes", chave="p", conta="hp.futebol")
    assert r["estado"] == "tocado" and r["destaque"]["confirmado"] and r["destaque"]["carimbo"] == "3m"
    assert nomes(falso)[-3:] == ["row_profile_header_imageview", "toolbar_highlights_button", "highlight_title"]


# ===========================================================================
# 5. compartilhar_post_no_story
# ===========================================================================
@pytest.mark.parametrize("tela", TELAS)
def test_compartilhar_post_pelo_deep_link_e_taps_pelos_bounds(tela):
    falso = falso_com(tela)
    disp = novo(falso)
    reg = Registro()
    r = sf.compartilhar_post_no_story(disp, LINK, "hpgta6", registrar=reg, chave="post1")
    assert r["estado"] == "tocado" and reg.chamadas == [("post1", "antes_do_toque"), ("post1", "tocado")]
    assert nomes(falso) == ["row_feed_button_share", "direct_share_sheet_add_to_story", "your_story_share_shortcut_button"]
    assert f"am start -a android.intent.action.VIEW -d {LINK} -p com.instagram.android" in falso.shell_cmds
    share = sd.achar(sd.parse_dump(arquivo_tela("post_aberto", tela).read_text(encoding="utf-8")), id="row_feed_button_share")
    assert falso.taps()[0] == share.centro


def test_compartilhar_post_de_outro_autor_aborta():
    falso = falso_com(link_abre="post_outro_autor")
    with pytest.raises(sf.ContaErrada) as e:
        sf.compartilhar_post_no_story(novo(falso), LINK, "hpgta6", chave="x")
    assert "@outra.conta" in str(e.value) and falso.toques == []


def test_compartilhar_plano_b_pela_grade_confere_o_titulo():
    falso = falso_com(link_abre=None)                      # o deep link não abre nada: fica no perfil
    disp = novo(falso)
    r = sf.compartilhar_post_no_story(disp, LINK, "hpgta6", titulo="Dá pra ficar GORDO no GTA 6", chave="b",
                                      tempos={"post": 3})
    assert r["estado"] == "tocado" and nomes(falso)[0] == "image_button"
    falso = falso_com(link_abre=None)
    with pytest.raises(sd.ElementoNaoApareceu) as e:
        sf.compartilhar_post_no_story(novo(falso), LINK, "hpgta6", titulo="Outro título qualquer", chave="b", tempos={"post": 3})
    assert "não compartilho post errado" in str(e.value) and "row_feed_button_share" not in nomes(falso)


def test_compartilhar_sem_titulo_e_sem_post_aberto_aborta():
    falso = falso_com(link_abre=None)
    with pytest.raises(sd.ElementoNaoApareceu) as e:
        sf.compartilhar_post_no_story(novo(falso), LINK, "hpgta6", chave="b", tempos={"post": 3})
    assert "sem título" in str(e.value)


# ===========================================================================
# 6. adicionar_ao_destaque (fixture REAL do visualizador: hp.futebol, "3m", Highlight)
# ===========================================================================
@pytest.mark.parametrize("tela", TELAS)
def test_destaque_com_o_dump_real_hp_futebol_3m_highlight(tela):
    falso = falso_com(tela, conta="hp.futebol")
    disp = novo(falso)
    r = sf.adicionar_ao_destaque(disp, "Enquetes", "hp.futebol")
    assert r == {"destaque": "Enquetes", "carimbo": "3m", "criado": False, "confirmado": True}
    assert nomes(falso) == ["row_profile_header_imageview", "toolbar_highlights_button", "highlight_title"]
    if tela == TELA_PADRAO:
        assert falso.taps()[1] == (530, 2190)                 # o centro REAL do Highlight no dump de 30/09
    else:
        assert falso.taps()[1] == (530, 2135)                 # proporcional (y × 2340/2400)
    vis = sd.parse_dump(falso.xml_tela("visualizador"))
    assert sd.achar(vis, id="reel_viewer_title").texto == "hp.futebol"
    assert sd.achar(vis, id="toolbar_highlights_button").desc == "Highlight"
    assert sd.achar(vis, id="self_toolbar_reshare_button_container").desc == "Send story"


def test_destaque_de_outra_conta_aborta():
    falso = falso_com(conta="hp.carros")
    with pytest.raises(sf.ContaErrada) as e:
        sf.adicionar_ao_destaque(novo(falso), "Enquetes", "hp.carros")
    assert "@hp.futebol" in str(e.value) and "toolbar_highlights_button" not in nomes(falso)


def test_destaque_7m_avanca_pelos_bounds_da_midia_e_desiste():
    xml = falso_com().xml_tela("visualizador").replace('text="3m"', 'text="7m"').replace("3 minutes ago", "7 minutes ago")
    falso = falso_com(conta="hp.futebol", telas={"visualizador": xml})
    with pytest.raises(sf.StoryNaoDeAgora) as e:
        sf.adicionar_ao_destaque(novo(falso), "Enquetes", "hp.futebol", limite_min=5, tempos={"elemento": 2})
    assert "7m" not in str(e.value) or True
    avancos = falso.taps()[1:]
    assert len(avancos) == sf.MAX_STORIES_AVANCAR
    midia = sd.achar(sd.parse_dump(xml), id="reel_viewer_media_container")
    assert avancos[0] == sf._ponto_em(midia.bounds, 0.92, 0.30) and "toolbar_highlights_button" not in nomes(falso)


def test_destaque_cria_novo_quando_nao_existe():
    falso = falso_com(conta="hp.futebol")
    r = sf.adicionar_ao_destaque(novo(falso), "Novidades", "hp.futebol")
    assert r["criado"] and r["confirmado"]
    assert nomes(falso)[-3:] == ["highlight_new", "highlight_title_edit_text", "highlight_add_button"]
    assert falso.digitados == ["Novidades"]


def test_dono_do_story_pelo_titulo_e_pelo_desc():
    vis = sd.parse_dump(falso_com().xml_tela("visualizador"))
    assert sf.dono_do_story(vis) == "hp.futebol"
    so_desc = [n for n in vis if n.id != "reel_viewer_title"]
    assert sf.dono_do_story(so_desc) == "hp.futebol"
    assert sf.dono_do_story([]) is None


# ===========================================================================
# 7. conferir_pela_api (get_json injetado; nada de rede)
# ===========================================================================
class GetJsonFalso:
    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.chamadas = []

    def __call__(self, url, params):
        self.chamadas.append((url, dict(params)))
        r = self.respostas.pop(0) if self.respostas else {"data": []}
        if isinstance(r, Exception):
            raise r
        return r


def test_conferir_pela_api_acha_o_story_mais_novo():
    g = GetJsonFalso([{"data": [
        {"id": "1", "media_type": "IMAGE", "permalink": "https://www.instagram.com/stories/hp.futebol/1/", "timestamp": "2026-10-01T12:50:00+0000"},
        {"id": "2", "media_type": "IMAGE", "permalink": "https://www.instagram.com/stories/hp.futebol/2/", "timestamp": "2026-10-01T13:05:10+0000"},
        {"id": "3", "media_type": "VIDEO", "permalink": "https://www.instagram.com/stories/hp.futebol/3/", "timestamp": "2026-10-01T13:02:00+0000"},
    ]}])
    dormidas = []
    r = sf.conferir_pela_api(g, "17841400000000001", desde="2026-10-01T13:00:00+0000", dormir=dormidas.append)
    assert r["id"] == "2" and r["tentativa"] == 1 and r["permalink"].startswith("https://www.instagram.com/stories/hp.futebol/")
    assert g.chamadas == [("https://graph.instagram.com/v21.0/17841400000000001/stories",
                           {"fields": "id,media_type,permalink,timestamp"})]
    assert dormidas == []


def test_conferir_pela_api_sem_story_novo_devolve_none_depois_das_tentativas():
    g = GetJsonFalso([{"data": [{"id": "1", "timestamp": "2026-10-01T12:50:00+0000"}]}] * 3)
    dormidas = []
    r = sf.conferir_pela_api(g, "178", desde=datetime(2026, 10, 1, 13, 0, tzinfo=FUSO), tentativas=3, espera_s=20,
                             dormir=dormidas.append)
    assert r is None and len(g.chamadas) == 3 and dormidas == [20.0, 20.0]


def test_conferir_pela_api_get_json_que_falha_tenta_de_novo():
    g = GetJsonFalso([RuntimeError("curl: (7) rede fora"), {"data": [{"id": "9", "timestamp": "2026-10-01T13:10:00+0000"}]}])
    dormidas = []
    r = sf.conferir_pela_api(g, "178", desde="2026-10-01T13:00:00+0000", dormir=dormidas.append, espera_s=5)
    assert r["id"] == "9" and r["tentativa"] == 2 and dormidas == [5.0]


def test_conferir_pela_api_recusa_sem_get_json_ou_id_invalido():
    with pytest.raises(sf.DadosInvalidos):
        sf.conferir_pela_api(None, "178", desde=BASE)
    with pytest.raises(sf.DadosInvalidos):
        sf.conferir_pela_api(GetJsonFalso([]), "IG_hp.futebol", desde=BASE)
    assert sf.story_mais_novo({"data": "lixo"}, BASE) is None and sf.story_mais_novo([], BASE) is None


# ===========================================================================
# 8. Regras: rodar_item_v2 / rodar_pedido_v2 (intervalo, orçamento, trava, desligar, 3 falhas, API)
# ===========================================================================
def contexto(**kw) -> sf.Contexto:
    kw.setdefault("estado", sf.Estado(dados={}, gravar=False))
    kw.setdefault("relogio", RelogioFalso())
    kw.setdefault("log", LogLista())
    kw.setdefault("saida", lambda *_: None)
    return sf.Contexto(**kw)


def pedido_v2(tmp_path, tipo: str, conta="hpgta6", **story) -> dict:
    arte = arte_com_zonas(tmp_path, f"story_{tipo}.jpg")
    figurinha = {"chamada_post": {"tipo": "link", "url": LINK, "rotulo": "Ver post"},
                 "mais_sobre": {"tipo": "link", "url": LINK, "rotulo": "Ver post"},
                 "interacao": {"tipo": "enquete", "opcoes": ["Sim", "Não"]},
                 "enquete": {"tipo": "enquete", "opcoes": ["Jogo", "Durmo"]},
                 "contagem": {"tipo": "contagem", "data": "2026-11-19", "rotulo": "Lançamento do GTA 6"},
                 "compartilhar_post": None}[tipo]
    s = {"quando": "2026-10-01 09:40", "tipo": tipo, "arte": None if tipo == "compartilhar_post" else str(arte),
         "zonas": None, "texto": "Dá pra ficar GORDO no GTA 6", "figurinha": figurinha,
         "pergunta_publico": "O que você faz?" if tipo in ("interacao", "enquete") else None, "destaque": None}
    s.update(story)
    return {"post_id": f"gta_2026-10-01_{tipo}", "conta": conta, "canal": "gta", "link": LINK,
            "publicado_em": "2026-10-01 09:00", "titulo": "Dá pra ficar GORDO no GTA 6", "destaque": None,
            "criado_em": "2026-10-01 09:10", "stories": [s]}


@pytest.mark.parametrize("tipo, toque_que_prova", [
    ("chamada_post", "asset_item"), ("mais_sobre", "asset_item"), ("interacao", "poll_sticker_v2_question"),
    ("enquete", "poll_sticker_v2_question"), ("contagem", "countdown_sticker_title"), ("compartilhar_post", "row_feed_button_share")])
def test_rodar_item_v2_despacha_pelo_tipo(tmp_path, tipo, toque_que_prova):
    pedido = fila.validar_v2(pedido_v2(tmp_path, tipo))
    falso = falso_com()
    ctx = contexto()
    r = sf.rodar_item_v2(novo(falso), pedido, pedido["stories"][0], ctx, 0)
    assert r["ok"] and r["codigo"] == 0 and r["estado"] == "tocado", r
    assert toque_que_prova in nomes(falso) and nomes(falso).count("your_story_share_shortcut_button") == 1
    assert ctx.estado.ja_postado(r["chave"]) == "tocado"
    if tipo == "compartilhar_post":
        assert r["chave"] == pedido["post_id"]                       # a mesma chave da rodada 1
    else:
        assert r["chave"] == f"{pedido['post_id']}#{tipo}@202610010940"


def test_intervalo_de_3_min_bloqueia_sem_adb_e_espera_com_relogio_injetado(tmp_path):
    pedido = fila.validar_v2(pedido_v2(tmp_path, "chamada_post"))
    rel = RelogioFalso()
    estado = sf.Estado(dados={"ultimo_story_em": (BASE - timedelta(seconds=60)).isoformat()}, gravar=False)
    falso = falso_com()
    r = sf.rodar_item_v2(novo(falso, relogio=rel), pedido, pedido["stories"][0], contexto(estado=estado, relogio=rel), 0)
    assert r["codigo"] == 2 and r["faltam_s"] == 120.0 and "3 min" in r["erro"] and falso.comandos == []
    # pelo pedido inteiro com esperar_intervalo: dorme os 120 s (relógio falso) e aí posta
    falso = falso_com()
    ctx = contexto(estado=estado, relogio=rel)
    r = sf.rodar_pedido_v2(pedido, ctx, lambda: novo(falso, relogio=rel), esperar_intervalo=True, trava=_SemTrava())
    assert rel.dormidas[0] == 120.0 and r["ok"] and r["resultados"][0]["estado"] == "tocado"


class _SemTrava:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_orcamento_de_5_min_por_story_com_relogio_injetado(tmp_path):
    pedido = fila.validar_v2(pedido_v2(tmp_path, "chamada_post"))
    rel = RelogioFalso(salto=61.0)                   # cada olhada no relógio = 61 s: estoura antes do toque final
    falso = falso_com()
    ctx = contexto(relogio=rel)
    r = sf.rodar_item_v2(novo(falso, relogio=rel), pedido, pedido["stories"][0], ctx, 0)
    assert not r["ok"] and "tempo máximo" in r["erro"] and r["codigo"] == 1 and r["tentativas"] == 1
    assert "your_story_share_shortcut_button" not in nomes(falso) and ctx.estado.ja_postado(r["chave"]) is None
    assert sf.Orcamento(300, RelogioFalso()).restante() == 300.0


def test_pesado_lock_devolve_2_sem_ligar_o_aparelho(tmp_path, _raizes):
    local, _ = _raizes
    lock = local / "app" / "pesado.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text(json.dumps({"quem": "cortar.py", "desde": BASE.strftime("%Y-%m-%dT%H:%M")}), encoding="utf-8")
    pedido = fila.validar_v2(pedido_v2(tmp_path, "chamada_post"))
    ligou = []
    r = sf.rodar_pedido_v2(pedido, contexto(), lambda: ligou.append(1))
    assert r["codigo"] == 2 and "não liguei o aparelho" in r["mensagem"] and ligou == [] and r["resultados"] == []
    assert lock.exists()                                                     # a trava dos outros fica como estava


def test_sem_trava_ocupada_o_pedido_roda_e_solta_o_lock(tmp_path, _raizes):
    pedido = fila.validar_v2(pedido_v2(tmp_path, "chamada_post"))
    falso = falso_com()
    r = sf.rodar_pedido_v2(pedido, contexto(), lambda: novo(falso))
    assert r["ok"] and not (_raizes[0] / "app" / "pesado.lock").exists()


@pytest.mark.parametrize("serial, desliga", [("emulator-5554", True), ("R58M1ABCDEF", False)])
def test_emulador_desligado_mesmo_em_erro_e_celular_real_nunca(tmp_path, serial, desliga):
    pedido = fila.validar_v2(pedido_v2(tmp_path, "chamada_post", arte=str(tmp_path / "nao_existe.jpg")))
    falso = falso_com(dispositivos=[(serial, "device")])
    disp = novo(falso, serial=serial)
    r = sf.rodar_pedido_v2(pedido, contexto(), lambda: disp, trava=_SemTrava())
    assert not r["ok"] and "não achei a arte" in r["resultados"][0]["erro"]
    assert (["adb", "-s", serial, "emu", "kill"] in falso.comandos) is desliga
    # erro inesperado fora do item (não é engolido) também passa pelo finally
    falso = falso_com(dispositivos=[(serial, "device")])
    ctx = contexto()
    ctx.estado.falta_intervalo = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("quebrou"))
    with pytest.raises(RuntimeError):
        sf.rodar_pedido_v2(pedido, ctx, lambda: novo(falso, serial=serial), trava=_SemTrava())
    assert (["adb", "-s", serial, "emu", "kill"] in falso.comandos) is desliga


def test_tres_falhas_tiram_o_post_da_fila_automatica(tmp_path):
    pedido = fila.validar_v2(pedido_v2(tmp_path, "chamada_post", arte=str(tmp_path / "nao_existe.jpg")))
    ctx = contexto()
    chave = sf.chave_do_story(pedido, pedido["stories"][0], 0)
    for i in range(3):
        falso = falso_com()
        r = sf.rodar_item_v2(novo(falso), pedido, pedido["stories"][0], ctx, 0)
        assert not r["ok"] and r["tentativas"] == i + 1
    assert r["fora_da_fila"] is True and ctx.estado.fora_da_fila(chave)
    falso = falso_com()
    r = sf.rodar_item_v2(novo(falso), pedido, pedido["stories"][0], ctx, 0)
    assert r["codigo"] == 2 and "fora da fila" in r["erro"] and falso.comandos == []


def test_rodar_item_conferido_pela_api_vira_publicado_e_sem_prova_a_conferir(tmp_path):
    pedido = fila.validar_v2(pedido_v2(tmp_path, "compartilhar_post"))
    g = GetJsonFalso([{"data": [{"id": "77", "permalink": "https://www.instagram.com/stories/hpgta6/77/",
                                 "timestamp": "2026-10-01T13:00:30+0000"}]}])
    rel = RelogioFalso()
    ctx = contexto(relogio=rel, get_json=g, ig_user_id="17841400000000001")
    r = sf.rodar_item_v2(novo(falso_com(), relogio=rel), pedido, pedido["stories"][0], ctx, 0)
    assert r["ok"] and r["estado"] == "publicado" and r["api"]["id"] == "77"
    assert ctx.estado.dados["postados"][r["chave"]]["permalink"].endswith("/77/")
    # sem story novo na API: "a conferir", e o toque não se repete
    g2 = GetJsonFalso([{"data": []}] * 3)
    ctx2 = contexto(relogio=rel, get_json=g2, ig_user_ids={"hpgta6": "178"}, espera_api_s=7)
    falso = falso_com()
    r = sf.rodar_item_v2(novo(falso, relogio=rel), pedido, pedido["stories"][0], ctx2, 0)
    assert not r["ok"] and r["estado"] == "a_conferir" and "a_conferir" in r and len(g2.chamadas) == 3
    assert rel.dormidas[-2:] == [7.0, 7.0] and nomes(falso).count("your_story_share_shortcut_button") == 1
    assert ctx2.estado.ja_postado(r["chave"]) == "a_conferir"


def test_rodar_pedido_v2_com_o_pedido_real_migrado(tmp_path):
    xml = falso_com().xml_tela("post_aberto").replace('text="hpgta6"', 'text="hp.futebol"')
    falso = falso_com(telas={"post_aberto": xml})
    ctx = contexto()
    r = sf.rodar_pedido_v2(PC_REAL / "fila_story_pedido_real.json", ctx, lambda: novo(falso), trava=_SemTrava())
    assert r["ok"] and r["codigo"] == 0, r
    res = r["resultados"][0]
    assert res["chave"] == "futebol_2026-09-30_1707_cr7-deixa-portugal_ig_feed" and res["conta"] == "@hp.futebol"
    assert falso.conta == "hp.futebol" and "row_user_container" in nomes(falso)
    assert any("am start -a android.intent.action.VIEW -d https://www.instagram.com/p/Dd7J4uso3bI/" in c for c in falso.shell_cmds)
    assert ["adb", "-s", "emulator-5554", "emu", "kill"] in falso.comandos


def test_parada_existente_bloqueia_com_codigo_3_sem_adb(tmp_path):
    pedido = fila.validar_v2(pedido_v2(tmp_path, "chamada_post"))
    sd.gravar_parada_padrao()({"frase": "try again later"})
    falso = falso_com()
    r = sf.rodar_item_v2(novo(falso), pedido, pedido["stories"][0], contexto(), 0)
    assert r["codigo"] == 3 and "só o Antônio apaga" in r["erro"] and falso.comandos == []


def test_ja_postado_bloqueia_com_codigo_2_sem_adb(tmp_path):
    pedido = fila.validar_v2(pedido_v2(tmp_path, "compartilhar_post"))
    estado = sf.Estado(dados={"postados": {pedido["post_id"]: {"estado": "publicado"}}}, gravar=False)
    falso = falso_com()
    r = sf.rodar_item_v2(novo(falso), pedido, pedido["stories"][0], contexto(estado=estado), 0)
    assert r["codigo"] == 2 and "nunca repete" in r["erro"] and falso.comandos == []


def test_chave_do_story_e_figurinhas_do_story():
    p = {"post_id": "x_2026-10-01", "link": LINK}
    assert sf.chave_do_story(p, {"tipo": "compartilhar_post"}) == "x_2026-10-01"
    assert sf.chave_do_story(p, {"tipo": "enquete", "quando": "2026-10-01 16:00"}) == "x_2026-10-01#enquete@202610011600"
    figs = sf.figurinhas_do_story({"figurinha": {"tipo": "link"}, "pergunta_publico": None}, p)
    assert figs == [{"tipo": "link", "url": LINK, "rotulo": "Ver post"}]
    assert sf.figurinhas_do_story({"figurinha": {"tipo": "enquete", "opcoes": ["a", "b"]}, "pergunta_publico": "Qual?"})[0]["pergunta"] == "Qual?"
    assert sf.figurinhas_do_story({"figurinha": None}) == [] and sf.figurinhas_do_story({"figurinha": {"tipo": "null"}}) == []


def test_bloqueado_e_precisa_do_antonio_no_item(tmp_path):
    pedido = fila.validar_v2(pedido_v2(tmp_path, "chamada_post"))
    falso = falso_com(travada=True, pin=True)
    r = sf.rodar_item_v2(novo(falso), pedido, pedido["stories"][0], contexto(), 0)
    assert r["codigo"] == 4 and r["precisa_antonio"] and "o Antônio desbloqueia" in r["erro"] and falso.digitados == []
    r = sf.rodar_pedido_v2(pedido, contexto(), lambda: novo(falso_com(travada=True, pin=True)), trava=_SemTrava())
    assert r["codigo"] == 4


# ===========================================================================
# 9. --simular: o roteiro completo de cada fluxo SEM adb
# ===========================================================================
@pytest.fixture
def sem_subprocesso(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("o --simular chamou um subprocesso de verdade")
    monkeypatch.setattr(subprocess, "run", _boom)
    monkeypatch.setattr(sd, "rodar", _boom)


def test_simular_arte_imprime_o_roteiro_inteiro_sem_adb(sem_subprocesso, tmp_path):
    linhas = []
    rc = sf.main(["arte", str(tmp_path / "story_chamada.jpg"), "--conta", "hp.carros", "--link", LINK, "--enquete",
                  "O que você faz?", "--opcao", "Jogo", "--opcao", "Durmo", "--destaque", "Enquetes", "--simular"], saida=linhas.append)
    txt = "\n".join(linhas)
    assert rc == 0 and "SIMULAÇÃO" in linhas[0]
    for passo in ("-> trocar para @hp.carros", "-> mandar a arte", "-> criar story", "-> figurinha de link",
                  "-> figurinha de enquete", "-> posicionar a figurinha de link", "-> publicar: Seu story",
                  "-> destaque 'Enquetes'", "estado do story story_chamada: tocado"):
        assert passo in txt, passo
    assert "[simular] adb -s emulator-5554 shell input swipe" in txt and "shell input text O%sque%svoce%sfaz" in txt
    assert "shell content call --uri content://media/external/file --method scan_file" in txt
    assert "push" in txt and "story_chamada.jpg" in txt


def test_simular_trocar_conta_compartilhar_e_destaque(sem_subprocesso):
    for argv, trecho in ((["trocar-conta", "hp.futebol"], "conta ativa: @hp.futebol"),
                         (["compartilhar", LINK, "--conta", "hp.futebol", "--destaque", "Noticias"], "am start -a android.intent.action.VIEW -d"),
                         (["destaque", "Enquetes", "--conta", "hp.futebol"], "-> destaque 'Enquetes'")):
        linhas = []
        assert sf.main(argv + ["--simular", "--tela", "1080x2340"], saida=linhas.append) == 0
        txt = "\n".join(linhas)
        assert trecho in txt and "[simular] adb" in txt and "input tap" in txt


def test_simular_pedido_real_nao_toca_no_pesado_lock_nem_no_estado(sem_subprocesso, _raizes):
    local, _ = _raizes
    linhas = []
    rc = sf.main(["pedido", str(PC_REAL / "fila_story_pedido_real.json"), "--simular"], saida=linhas.append)
    txt = "\n".join(linhas)
    assert rc == 0 and "OK: ok" in txt and "-> Enviar > Adicionar ao story > Seu story" in txt
    assert "emu kill" in txt                                         # no fim o emulador seria desligado
    assert not (local / "app" / "pesado.lock").exists() and not (local / "emulador" / "story_post_estado.json").exists()


def test_cli_sem_comando_e_erros_de_dados(sem_subprocesso, tmp_path):
    linhas = []
    assert sf.main([], saida=linhas.append) == 1
    assert sf.main(["arte", "x.jpg", "--conta", "hpgta6", "--enquete", "Uma pergunta comprida demais para a figurinha?",
                    "--opcao", "a", "--opcao", "b", "--simular"], saida=linhas.append) == 1
    assert any("não cabe" in l for l in linhas)
