# -*- coding: utf-8 -*-
"""Testes do story_post.py: sem emulador, sem adb e sem rede.

O "InstagramFalso" faz o papel do adb + emulador: recebe os mesmos comandos
que o adb receberia (via rodar_fn), devolve XMLs de uiautomator realistas e
muda de tela conforme os toques (pelas coordenadas, como no aparelho).

Rodar:  cd app && python -m pytest -q ../scripts/testes/test_story_post.py
"""
import json
import re
import shlex
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from xml.sax.saxutils import quoteattr

import pytest

AQUI = Path(__file__).resolve().parent
SCRIPTS = AQUI.parent
APP = SCRIPTS.parent / "app"
# o conftest do app/ não é carregado quando o teste está fora de app/:
# este arquivo se vira sozinho (sys.path + pastas temporárias), com ou sem
# um conftest.py em scripts/testes.
for _p in (SCRIPTS, APP / "hp_studio", SCRIPTS.parent / "06 Projeto" / "app" / "hp_studio"):
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import story_post as sp  # noqa: E402
from hpbase import FUSO, escrever_json, ler_json  # noqa: E402

PKG = "com.instagram.android"
W, H = 1080, 2400
LINK = "https://www.instagram.com/p/ABC123xyz/?igsh=aa&x=1"
CONTAS = ["hpgta6", "hp.futebol", "hp.filmes", "hp.receitas", "hp.carros", "hp.destinos"]


@pytest.fixture(autouse=True)
def _raizes(tmp_path, monkeypatch):
    local, drive = tmp_path / "HypadoLocal", tmp_path / "Drive"
    local.mkdir(exist_ok=True)
    drive.mkdir(exist_ok=True)
    monkeypatch.setenv("HP_LOCAL", str(local))
    monkeypatch.setenv("HP_DRIVE", str(drive))
    android = local / "android"
    android.mkdir(exist_ok=True)
    for n in ("ligar_emulador.ps1", "desligar_emulador.ps1", "digitar.py"):
        (android / n).write_text("# falso\n", encoding="utf-8")
    return local, drive


# ===========================================================================
# XML de uiautomator
# ===========================================================================
XML_PERFIL_REAL = (
    "<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>"
    '<hierarchy rotation="0">'
    '<node index="0" text="" resource-id="" class="android.widget.FrameLayout" '
    'package="com.instagram.android" content-desc="" checkable="false" checked="false" '
    'clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" '
    'long-clickable="false" password="false" selected="false" bounds="[0,0][1080,2400]">'
    '<node index="0" text="" resource-id="com.instagram.android:id/action_bar_container" '
    'class="android.widget.FrameLayout" package="com.instagram.android" content-desc="" '
    'checkable="false" checked="false" clickable="false" enabled="true" focusable="false" '
    'focused="false" scrollable="false" long-clickable="false" password="false" '
    'selected="false" bounds="[0,63][1080,210]">'
    '<node index="0" text="" resource-id="com.instagram.android:id/action_bar_username_container" '
    'class="android.widget.LinearLayout" package="com.instagram.android" content-desc="" '
    'checkable="false" checked="false" clickable="true" enabled="true" focusable="true" '
    'focused="false" scrollable="false" long-clickable="false" password="false" '
    'selected="false" bounds="[42,84][505,189]">'
    '<node index="0" text="hp.futebol" '
    'resource-id="com.instagram.android:id/action_bar_large_title_auto_size" '
    'class="android.widget.TextView" package="com.instagram.android" content-desc="" '
    'checkable="false" checked="false" clickable="false" enabled="true" focusable="false" '
    'focused="false" scrollable="false" long-clickable="false" password="false" '
    'selected="false" bounds="[42,105][389,168]" />'
    '<node index="1" text="" resource-id="com.instagram.android:id/action_bar_title_chevron" '
    'class="android.widget.ImageView" package="com.instagram.android" '
    'content-desc="Trocar de conta" checkable="false" checked="false" clickable="false" '
    'enabled="true" focusable="false" focused="false" scrollable="false" '
    'long-clickable="false" password="false" selected="false" bounds="[400,115][442,157]" />'
    "</node></node>"
    '<node index="1" text="" resource-id="com.instagram.android:id/row_profile_header_imageview" '
    'class="android.widget.ImageView" package="com.instagram.android" '
    'content-desc="Foto do perfil de hp.futebol" checkable="false" checked="false" '
    'clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" '
    'long-clickable="true" password="false" selected="false" bounds="[42,252][273,483]" />'
    '<node index="2" text="Publicações &amp; Reels" resource-id="" class="android.widget.TextView" '
    'package="com.instagram.android" content-desc="" checkable="false" checked="false" '
    'clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" '
    'long-clickable="false" password="false" selected="false" bounds="[0,0][0,0]" />'
    '<node index="3" text="" resource-id="com.instagram.android:id/profile_tab" '
    'class="android.widget.FrameLayout" package="com.instagram.android" content-desc="Perfil" '
    'checkable="false" checked="false" clickable="true" enabled="true" focusable="true" '
    'focused="false" scrollable="false" long-clickable="false" password="false" '
    'selected="true" bounds="[864,2253][1080,2400]" />'
    "</node></hierarchy>\nUI hierchary dumped to: /dev/tty"
)


def no_xml(e: dict) -> str:
    rid = e.get("id", "")
    if rid and ":" not in rid:
        rid = f"{PKG}:id/{rid}"
    b = e.get("b", (0, 0, 0, 0))
    clic = e.get("clicavel", False)
    attrs = {
        "index": "0", "text": e.get("texto", ""), "resource-id": rid,
        "class": e.get("classe", "android.widget.TextView"),
        "package": e.get("pacote", PKG), "content-desc": e.get("desc", ""),
        "checkable": str(e.get("checkable", False)).lower(),
        "checked": str(e.get("marcado", False)).lower(), "clickable": str(clic).lower(),
        "enabled": "true", "focusable": str(clic).lower(),
        "focused": str(e.get("focado", False)).lower(), "scrollable": "false",
        "long-clickable": "false", "password": str(e.get("senha", False)).lower(),
        "selected": "false", "bounds": f"[{b[0]},{b[1]}][{b[2]},{b[3]}]",
    }
    return "<node " + " ".join(f"{k}={quoteattr(v)}" for k, v in attrs.items()) + " />"


def tela_xml(els: list) -> str:
    raiz = no_xml({"classe": "android.widget.FrameLayout", "b": (0, 0, W, H)})[:-3] + ">"
    return ("<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>"
            '<hierarchy rotation="0">' + raiz + "".join(no_xml(e) for e in els)
            + "</node></hierarchy>")


def el(id="", texto="", desc="", b=(0, 0, 0, 0), **kw) -> dict:
    return {"id": id, "texto": texto, "desc": desc, "b": b, **kw}


ABAS = [el("feed_tab", desc="Página inicial", b=(0, 2253, 216, 2400), clicavel=True,
           classe="android.widget.FrameLayout"),
        el("profile_tab", desc="Perfil", b=(864, 2253, 1080, 2400), clicavel=True,
           classe="android.widget.FrameLayout")]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
         "setembro", "outubro", "novembro", "dezembro"]


# ===========================================================================
# Relógio falso e aparelho falso
# ===========================================================================
class RelogioFalso:
    def __init__(self, inicio=datetime(2026, 9, 30, 10, 0, tzinfo=FUSO)):
        self.t = 0.0
        self.inicio = inicio

    def monotonic(self):
        return self.t

    def dormir(self, s):
        self.t += max(0.0, float(s))

    def agora(self):
        return self.inicio + timedelta(seconds=self.t)


class InstagramFalso:
    """Emulador + Instagram de mentira, dirigido pelos comandos do adb."""

    def __init__(self, relogio, ativa="hp.futebol"):
        self.relogio = relogio
        self.comandos, self.eventos = [], []
        self.ligado = False
        self.tela = "desligado"
        self.anterior = "feed"
        self.contas_logadas = list(CONTAS)
        self.ativa = ativa
        self.troca_vai_para = None          # simula troca que cai na conta errada
        self.autor_post = None              # simula link de post de outra conta
        self.legenda = "Trailer 3 do GTA 6: a suspeita virou verdade"
        self.link_abre = True
        self.aviso_ao_entrar = set()        # telas que viram aviso da Meta
        self.popup_ao_abrir = False
        self.falhas_dump = 0
        self.falha_boot = False
        self.falha_em = {}                  # trecho do comando -> exceção
        self.custo = {}                     # "dump"/"ligar" -> segundos no relógio
        self.feito_rc = 0
        self.stories = {"hpgta6": [-3 * 3600, -40 * 60]}
        self.publicados = []
        self.destaques = ["Enquetes", "GTA 6", "Notícias"]
        self.adicionados = []
        self.idx = 0
        self.feitos, self.feitos_cwd = [], []
        self.pushados, self.digitados = [], []
        self.escolhida = None
        self.foco = None
        self.campos = {}
        self.n_opcoes = 2
        self.enquete_pronta = None
        self.bandeja_so_com_busca = False
        self.busca = ""
        self.dia_inteiro = False
        self.mes = (2026, 9)
        self.data_escolhida = None
        self.data_confirmada = None
        self.titulo_contagem = None
        self.toast = ""

    # ------------------------------------------------------------------ telas
    def _ts(self, t):
        d = self.relogio.t - t
        if d < 60:
            return "Agora"
        if d < 3600:
            return f"{int(d // 60)} min"
        return f"{int(d // 3600)} h"

    def els(self):
        t = self.tela
        if t == "launcher":
            return [el(texto="Instagram", desc="Instagram", b=(100, 1000, 300, 1200),
                       pacote="com.android.launcher3", clicavel=True)]
        if t == "popup":
            return [el(texto="Ativar notificações", b=(100, 900, 980, 980)),
                    el(texto="Ativar", b=(100, 1100, 980, 1200), clicavel=True),
                    el(texto="Agora não", b=(100, 1220, 980, 1320), clicavel=True)]
        if t == "feed":
            return [el("title_logo", desc="Instagram", b=(40, 80, 400, 190)),
                    el("row_feed_photo_profile_name", texto="amigo.qualquer",
                       b=(150, 300, 600, 360)), *ABAS]
        if t == "perfil":
            els = [el("action_bar_username_container", b=(42, 84, 505, 189), clicavel=True,
                      classe="android.widget.LinearLayout"),
                   el("action_bar_large_title_auto_size", texto=self.ativa, b=(42, 105, 389, 168)),
                   el("creation_tab", desc="Criar", b=(860, 90, 940, 180), clicavel=True),
                   el("row_profile_header_imageview", desc=f"Foto do perfil de {self.ativa}",
                      b=(42, 252, 273, 483), clicavel=True, classe="android.widget.ImageView"),
                   el(texto="Enquetes", b=(40, 900, 200, 940))]
            for i, (x, pin) in enumerate([(0, True), (360, False), (720, False)]):
                els.append(el("image_button", desc=("Post fixado " if pin else "Foto ") + str(i),
                              b=(x, 1200, x + 358, 1558), clicavel=True))
            return els + ABAS
        if t == "trocar_conta":
            els = [el("bottom_sheet_container", b=(0, 1300, W, H), classe="android.widget.FrameLayout")]
            y = 1350
            for c in self.contas_logadas:
                els.append(el("row_user_container_base", b=(0, y, W, y + 140), clicavel=True,
                              classe="android.widget.LinearLayout"))
                els.append(el("row_user_primary_name", texto=c, b=(180, y + 40, 700, y + 100)))
                y += 140
            els.append(el(texto="Adicionar conta", b=(180, y + 40, 700, y + 100)))
            return els
        if t == "post":
            return [el("row_feed_photo_profile_name", texto=self.autor_post or self.ativa,
                       b=(150, 250, 600, 310)),
                    el("row_feed_photo_imageview", desc="Foto", b=(0, 330, W, 1410),
                       classe="android.widget.ImageView"),
                    el("row_feed_button_like", desc="Curtir", b=(20, 1420, 120, 1520), clicavel=True),
                    el("row_feed_button_comment", desc="Comentar", b=(140, 1420, 240, 1520), clicavel=True),
                    el("row_feed_button_share", desc="Enviar publicação", b=(260, 1420, 360, 1520),
                       clicavel=True),
                    el("row_feed_comment_textview_layout", texto=f"{self.ativa} {self.legenda}",
                       b=(20, 1600, 1060, 1700)), *ABAS]
        if t == "compartilhar":
            return [el("direct_private_share_container", b=(0, 900, W, H),
                       classe="android.widget.FrameLayout"),
                    el("search_row", desc="Pesquisar", classe="android.widget.EditText",
                       b=(40, 950, 1040, 1050)),
                    el(texto="amigo.qualquer", b=(60, 1100, 300, 1150)),
                    el("share_sheet_action", desc="Adicionar ao story", b=(40, 2150, 240, 2350),
                       clicavel=True, classe="android.widget.Button"),
                    el(texto="Adicionar ao story", b=(40, 2355, 240, 2395)),
                    el(texto="Copiar link", b=(260, 2355, 460, 2395))]
        if t == "composer":
            return [el("story_post_sticker", desc="Publicação", b=(200, 700, 880, 1500)),
                    el("your_story_share_shortcut_button", texto="Seu story", b=(40, 2250, 500, 2350),
                       clicavel=True, classe="android.widget.Button"),
                    el("close_friends_share_shortcut_button", texto="Amigos próximos",
                       b=(520, 2250, 900, 2350), clicavel=True)]
        if t == "aviso":
            return [el(texto="Tente novamente mais tarde", b=(100, 900, 980, 980)),
                    el(texto="Restringimos certas atividades para proteger nossa comunidade.",
                       b=(100, 1000, 980, 1150)),
                    el(texto="OK", b=(100, 1200, 980, 1300), clicavel=True,
                       classe="android.widget.Button")]
        if t == "story_viewer":
            lst = self.stories.get(self.ativa, [])
            els = [el("reel_viewer_media_container", b=(0, 0, W, H), classe="android.widget.FrameLayout"),
                   el("reel_viewer_title", texto=self.ativa, b=(150, 120, 500, 170)),
                   el("reel_viewer_timestamp", texto=self._ts(lst[self.idx]), b=(510, 120, 640, 170)),
                   el("toolbar_highlights_button", desc="Destaque", b=(420, 2250, 660, 2380),
                      clicavel=True)]
            if self.toast:
                els.append(el(texto=self.toast, b=(100, 2000, 980, 2080)))
                self.toast = ""
            return els
        if t == "destaques":
            els = [el(texto="Adicionar ao destaque", b=(0, 1500, W, 1580)),
                   el(texto="Novo", b=(40, 1800, 220, 1850))]
            x = 260
            for d in self.destaques:
                els.append(el("highlight_title", texto=d, b=(x, 1800, x + 200, 1850)))
                x += 220
            return els
        if t == "criar_menu":
            return [el(texto=n, b=(40, 1500 + i * 120, 1040, 1600 + i * 120), clicavel=True)
                    for i, n in enumerate(["Reel", "Publicação", "Story", "Destaque dos stories",
                                           "Ao vivo"])]
        if t == "camera":
            return [el("camera_shutter_button", desc="Tirar foto", b=(440, 2000, 640, 2200)),
                    el("gallery_preview_button", desc="Galeria", b=(40, 2100, 160, 2220),
                       clicavel=True)]
        if t == "galeria":
            els = [el(texto="Recentes", b=(40, 150, 400, 220))]
            for i in range(3):
                els.append(el("gallery_grid_item_thumbnail", desc=f"Foto {i}",
                              b=(i * 360, 300, i * 360 + 358, 658), clicavel=True))
            return els
        if t in ("editor", "editor_adesivo"):
            return [el("asset_button", desc="Figurinhas", b=(700, 80, 800, 180), clicavel=True),
                    el("your_story_share_shortcut_button", texto="Seu story",
                       b=(40, 2250, 500, 2350), clicavel=True)]
        if t == "bandeja":
            els = [el("row_search_edit_text", desc="Pesquisar", texto=self.busca,
                      classe="android.widget.EditText", b=(40, 300, 1040, 400), clicavel=True)]
            figs = [("Figurinha de localização", "local"), ("Figurinha de enquete", "enquete"),
                    ("Figurinha de contagem regressiva", "contagem")]
            for i, (d, chave) in enumerate(figs):
                if self.bandeja_so_com_busca and (not self.busca or self.busca not in chave):
                    continue
                els.append(el(f"sticker_{chave}", desc=d, b=(40 + i * 330, 450, 340 + i * 330, 600),
                              clicavel=True))
            return els
        if t == "enquete":
            els = [el("poll_sticker_v2_question", texto=self.campos.get("pergunta", ""),
                      classe="android.widget.EditText", b=(140, 800, 940, 900))]
            for i in range(self.n_opcoes):
                els.append(el(texto=self.campos.get(f"op{i}", ""), classe="android.widget.EditText",
                              b=(140, 950 + i * 120, 940, 1050 + i * 120)))
            if self.n_opcoes < 4:
                els.append(el(texto="Adicionar opção", b=(140, 950 + self.n_opcoes * 120, 940,
                                                           1050 + self.n_opcoes * 120)))
            els.append(el("done_button", texto="Concluir", b=(880, 80, 1040, 180), clicavel=True))
            return els
        if t == "contagem":
            return [el("countdown_sticker_title", texto=self.campos.get("titulo", ""),
                       classe="android.widget.EditText", b=(140, 800, 940, 900)),
                    el("countdown_sticker_all_day_switch", classe="android.widget.Switch",
                       marcado=self.dia_inteiro, b=(800, 950, 940, 1030), clicavel=True),
                    el(texto="Dia inteiro", b=(140, 960, 600, 1020)),
                    el("countdown_sticker_end_date", texto="Definir data e hora de término",
                       b=(140, 1060, 940, 1140), clicavel=True),
                    el("done_button", texto="Concluir", b=(880, 80, 1040, 180), clicavel=True)]
        if t == "calendario":
            a, m = self.mes
            els = [el("android:id/date_picker_header_date", texto=f"{MESES[m - 1]} de {a}",
                      b=(100, 500, 900, 600)),
                   el("android:id/next", desc="Próximo mês", b=(900, 700, 1000, 800), clicavel=True)]
            dias = (date(a + (m == 12), m % 12 + 1, 1) - date(a, m, 1)).days
            for d in range(1, dias + 1):
                c, r = (d - 1) % 7, (d - 1) // 7
                els.append(el(texto=str(d), desc=f"{d} de {MESES[m - 1]} de {a}",
                              b=(40 + c * 140, 900 + r * 100, 170 + c * 140, 990 + r * 100),
                              classe="android.view.View", clicavel=True))
            els += [el("android:id/button2", texto="Cancelar", b=(500, 1700, 740, 1800)),
                    el("android:id/button1", texto="OK", b=(760, 1700, 1000, 1800), clicavel=True)]
            return els
        return []

    # ------------------------------------------------------------------ ações
    def _ir(self, tela):
        self.anterior = self.tela
        self.tela = "aviso" if tela in self.aviso_ao_entrar else tela

    def _ev(self, e):
        self.eventos.append(e)

    def _publicar(self, destino):
        self.stories.setdefault(self.ativa, []).append(self.relogio.t)
        self.publicados.append((self.ativa, self.relogio.t))
        self._ev("publicar")
        self._ir(destino)

    def _acao(self, e) -> bool:
        t, i, tx, d = self.tela, e.get("id", ""), e.get("texto", ""), e.get("desc", "")
        if i == "profile_tab":
            self._ev("tap:profile_tab")
            self._ir("perfil")
        elif t == "popup" and tx == "Agora não":
            self._ev("tap:Agora não")
            self._ir("feed")
        elif t == "perfil" and i == "action_bar_username_container":
            self._ev("tap:action_bar_username_container")
            self._ir("trocar_conta")
        elif t == "perfil" and i == "row_profile_header_imageview":
            self._ev("tap:row_profile_header_imageview")
            self.idx = 0
            self._ir("story_viewer" if self.stories.get(self.ativa) else "perfil")
        elif t == "perfil" and i == "creation_tab":
            self._ev("tap:creation_tab")
            self._ir("criar_menu")
        elif t == "perfil" and i == "image_button":
            self._ev(f"tap:grade:{d}")
            self._ir("post")
        elif t == "trocar_conta" and tx in self.contas_logadas:
            self._ev(f"conta:{tx}")
            self.ativa = self.troca_vai_para or tx
            self._ir("perfil")
        elif t == "post" and i == "row_feed_button_share":
            self._ev("tap:row_feed_button_share")
            self._ir("compartilhar")
        elif t == "compartilhar" and "Adicionar ao story" in (tx, d):
            self._ev("tap:Adicionar ao story")
            self._ir("composer")
        elif t == "composer" and i == "your_story_share_shortcut_button":
            self._publicar("post")
        elif t == "editor_adesivo" and i == "your_story_share_shortcut_button":
            self._publicar("feed")
        elif t == "story_viewer" and i == "toolbar_highlights_button":
            self._ev("tap:toolbar_highlights_button")
            self._ir("destaques")
        elif t == "destaques" and tx in self.destaques:
            self._ev(f"destaque:{tx}")
            self.adicionados.append((self.ativa, tx))
            self.toast = f"Adicionado a {tx}"
            self._ir("story_viewer")
        elif t == "criar_menu" and tx == "Story":
            self._ev("tap:Story")
            self._ir("camera")
        elif t == "camera" and i == "gallery_preview_button":
            self._ev("tap:galeria")
            self._ir("galeria")
        elif t == "galeria" and i == "gallery_grid_item_thumbnail":
            self._ev(f"tap:{d}")
            self.escolhida = self.pushados[-1] if d == "Foto 0" and self.pushados else "antiga"
            self._ir("editor")
        elif t == "editor" and i == "asset_button":
            self._ev("tap:asset_button")
            self._ir("bandeja")
        elif t == "bandeja" and i == "row_search_edit_text":
            self._ev("tap:busca")
            self.foco = "busca"
        elif t == "bandeja" and i.startswith("sticker_"):
            self._ev(f"tap:{i}")
            self.foco = None
            self._ir({"sticker_enquete": "enquete", "sticker_contagem": "contagem"}.get(i, "editor"))
        elif t == "enquete" and i == "poll_sticker_v2_question":
            self.foco = "pergunta"
        elif t == "enquete" and e.get("classe", "").endswith("EditText"):
            self.foco = f"op{(e['b'][1] - 950) // 120}"
        elif t == "enquete" and tx == "Adicionar opção":
            self.n_opcoes += 1
        elif t == "enquete" and i == "done_button":
            self._ev("tap:done_button")
            self.enquete_pronta = dict(self.campos)
            self.campos = {}
            self._ir("editor_adesivo")
        elif t == "contagem" and i == "countdown_sticker_title":
            self.foco = "titulo"
        elif t == "contagem" and i == "countdown_sticker_all_day_switch":
            self.dia_inteiro = not self.dia_inteiro
        elif t == "contagem" and i == "countdown_sticker_end_date":
            self._ir("calendario")
        elif t == "contagem" and i == "done_button":
            self._ev("tap:done_button")
            self.titulo_contagem = self.campos.get("titulo")
            self.campos = {}
            self._ir("editor_adesivo")
        elif t == "calendario" and i == "android:id/next":
            a, m = self.mes
            self.mes = (a + (m == 12), m % 12 + 1)
            self._ev("tap:proximo_mes")
        elif t == "calendario" and i == "android:id/button1":
            self.data_confirmada = self.data_escolhida
            self._ev("tap:ok_data")
            self._ir("contagem")
        elif t == "calendario" and d and re.match(r"\d+ de ", d):
            a, m = self.mes
            self.data_escolhida = date(a, m, int(tx))
        else:
            return False
        return True

    def _tocar(self, x, y):
        cand = sorted((e for e in self.els() if e["b"][0] <= x < e["b"][2] and e["b"][1] <= y < e["b"][3]),
                      key=lambda e: (e["b"][2] - e["b"][0]) * (e["b"][3] - e["b"][1]))
        for e in cand:
            if self._acao(e):
                return
        if self.tela == "story_viewer" and x > 0.6 * W:
            self._ev("avancar")
            self.idx += 1
            if self.idx >= len(self.stories.get(self.ativa, [])):
                self._ir("perfil")
            return
        self._ev(f"tap:?({x},{y})")

    def _digitado(self, txt):
        self.digitados.append(txt)
        if self.foco == "busca":
            self.busca = normalizar_simples(txt)
        elif self.foco:
            self.campos[self.foco] = self.campos.get(self.foco, "") + txt

    def _voltar(self):
        self._ev("voltar")
        volta = {"story_viewer": "perfil", "destaques": "story_viewer", "composer": "post",
                 "compartilhar": "post", "trocar_conta": "perfil"}
        self._ir(volta.get(self.tela, "feed"))

    # ------------------------------------------------------------------ rodar
    def rodar(self, cmd, timeout=None, entrada=None, cwd=None):
        cmd = [str(c) for c in cmd]
        self.comandos.append(cmd)
        junto = " ".join(cmd)
        for trecho, exc in self.falha_em.items():
            if trecho in junto:
                raise exc
        out = self._interpretar(cmd, cwd)
        if out is None:
            return subprocess.CompletedProcess(cmd, 1, stdout=b"", stderr=b"error: no devices/emulators found")
        if isinstance(out, str):
            out = out.encode("utf-8")
        return subprocess.CompletedProcess(cmd, 0, stdout=out, stderr=b"")

    def _interpretar(self, cmd, cwd):
        if cmd[0] == "powershell":
            if "desligar_emulador" in cmd[-1]:
                self._ev("desligar")
                self.ligado = False
                self.tela = "desligado"
            elif "ligar_emulador" in cmd[-1]:
                self._ev("ligar")
                self.relogio.t += self.custo.get("ligar", 0)
                if not self.falha_boot:
                    self.ligado = True
                    self.tela = "launcher"
            return ""
        if any(c.endswith("story_clicavel.py") for c in cmd):
            self._ev("feito")
            self.feitos.append(cmd)
            self.feitos_cwd.append(cwd)
            return "ok" if self.feito_rc == 0 else None
        if any(c.endswith("digitar.py") for c in cmd):
            self._ev(f"digitar.py:{cmd[-1]}")
            self._digitado(cmd[-1])
            return ""
        if cmd[0] != "adb":
            return None
        args = cmd[1:]
        if args[:1] == ["-s"]:
            args = args[2:]
        if not self.ligado:
            return None
        if args[0] == "push":
            nome = args[2].rsplit("/", 1)[-1]
            self.pushados.append(nome)
            self._ev(f"push:{nome}")
            return ""
        if args[0] == "exec-out":
            return b"\x89PNG falso"
        if args[0] == "emu":
            self._ev("emu kill")
            self.ligado = False
            return ""
        s = args[1]
        if "getprop sys.boot_completed" in s:
            return "1"
        if "uiautomator dump" in s:
            self.relogio.t += self.custo.get("dump", 0)
            if self.falhas_dump > 0:
                self.falhas_dump -= 1
                return "ERROR: could not get idle state."
            return tela_xml(self.els())
        if s.startswith("input tap"):
            _, _, x, y = s.split()
            self._tocar(int(x), int(y))
            return ""
        if s.startswith("input keyevent"):
            codigos = s.split()[2:]
            if codigos == ["4"]:
                self._voltar()
            elif codigos and set(codigos) == {"67"} and self.foco:
                if self.foco == "busca":
                    self.busca = ""
                else:
                    self.campos[self.foco] = ""
            return ""
        if s.startswith("input text"):
            txt = shlex.split(s)[2].replace("%s", " ")
            self._ev(f"texto:{txt}")
            self._digitado(txt)
            return ""
        if s.startswith("input swipe") or s.startswith("input draganddrop"):
            p = s.split()
            self._ev(f"arrastar:{p[2]},{p[3]}->{p[4]},{p[5]}")
            return ""
        if s.startswith("monkey -p"):
            self._ev("abrir_ig")
            self.tela = "popup" if self.popup_ao_abrir else "feed"
            return ""
        if s.startswith("am force-stop"):
            self._ev("fechar_ig")
            self.tela = "launcher"
            return ""
        if s.startswith("am start"):
            p = shlex.split(s)
            link = p[p.index("-d") + 1]
            self._ev(f"link:{link}")
            self.links = getattr(self, "links", []) + [link]
            if self.link_abre:
                self._ir("post")
            return "Starting: Intent { act=android.intent.action.VIEW }"
        if s.startswith("am broadcast"):
            self._ev("scan")
            return "Broadcast completed: result=0"
        if s.startswith("content query"):
            m = re.search(r"_display_name='([^']+)'", s)
            if m and m.group(1) in self.pushados:
                return f"Row: 0 _display_name={m.group(1)}"
            return "No result found."
        return ""


def normalizar_simples(s):
    return sp.normalizar(s)


# ===========================================================================
# Ajudantes
# ===========================================================================
def novo(ativa="hp.futebol", **cfg_extra):
    relogio = RelogioFalso()
    fake = InstagramFalso(relogio, ativa=ativa)
    cfg = sp.carregar_config()
    cfg.update(cfg_extra)
    saidas = []
    ctx = sp.criar_contexto(cfg, rodar_fn=fake.rodar, relogio=relogio,
                            saida=saidas.append, adb_exe="adb")
    ctx._saidas = saidas
    return ctx, fake, relogio


def item_fila(pid="2026-09-30_gta_trailer3", canal="gta", conta="hpgta6", link=LINK,
              destaque="GTA 6", publicado_em="2026-09-30T09:00:00-03:00",
              titulo="Trailer 3", **kw):
    d = {"post_id": pid, "conta": conta, "canal": canal, "link": link,
         "publicado_em": publicado_em, "titulo": titulo, "destaque": destaque, **kw}
    escrever_json(sp.pasta_fila() / f"{pid}.json", d)
    return d


def lote_enquete(drive, pergunta="Vai comprar no 1º dia?", opcoes=("Sim", "Não"), **kw):
    pasta = drive / "lotes"
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "arte_enquete_0930.png").write_bytes(b"\x89PNG arte")
    item = {"tipo": "story_enquete", "canal": "gta", "arquivo": "arte_enquete_0930.png",
            "pergunta": pergunta, "opcoes": list(opcoes), "caixa_enquete": [540, 1650], **kw}
    escrever_json(pasta / "2026-09-30_estaticos.json",
                  {"dia": "2026-09-30", "itens": [{"tipo": "carrossel", "arquivo": "x.png"}, item]})
    return item


def sem_ruido(eventos):
    return [e for e in eventos if not e.startswith("tap:?")]


# ===========================================================================
# 1. parse do XML e bounds -> centro
# ===========================================================================
def test_bounds_e_centro():
    assert sp.ler_bounds("[42,84][505,189]") == (42, 84, 505, 189)
    assert sp.centro((42, 84, 505, 189)) == (273, 136)
    assert sp.ler_bounds("lixo") is None


def test_parse_xml_real_com_lixo_no_fim():
    nos = sp.parse_xml(XML_PERFIL_REAL)
    assert len(nos) == 8
    cont = [n for n in nos if n.id_curto == "action_bar_username_container"][0]
    assert cont.clicavel and cont.centro == (273, 136)
    titulo = [n for n in nos if n.texto == "hp.futebol"][0]
    assert titulo.dentro_de(cont)
    assert titulo.rid == f"{PKG}:id/action_bar_large_title_auto_size"
    assert [n for n in nos if n.id_curto == "profile_tab"][0].selecionado
    assert any(n.texto == "Publicações & Reels" for n in nos)  # entidade XML decodificada
    ctx, _, _ = novo()
    assert sp.conta_ativa(ctx, nos) == "hp.futebol"
    # nó de área zero não é "visível"
    assert not sp.filtrar(nos, texto="Publicações & Reels")
    assert sp.filtrar(nos, texto="Publicações & Reels", visivel=False)


def test_parse_xml_invalido_devolve_vazio():
    assert sp.parse_xml("") == []
    assert sp.parse_xml("ERROR: could not get idle state.") == []
    assert sp.parse_xml(XML_PERFIL_REAL[:300]) == []   # cortado no meio


def test_filtrar_por_texto_desc_rotulo_sem_acento():
    nos = sp.parse_xml(tela_xml([el("a", texto="Adicionar ao story", b=(0, 0, 10, 10)),
                                 el("b", desc="Adicionar publicação ao seu story", b=(0, 0, 10, 10))]))
    assert [n.id_curto for n in sp.filtrar(nos, rotulo=["ADICIONAR AO STORY"])] == ["a"]
    assert [n.id_curto for n in sp.filtrar(nos, desc="adicionar publicacao", parcial=True)] == ["b"]
    assert [n.id_curto for n in sp.filtrar(nos, id=f"{PKG}:id/b")] == ["b"]


def test_timestamp_do_story():
    m = sp.minutos_do_timestamp
    assert m("Agora") == 0 and m("now") == 0 and m("Just now") == 0
    assert m("1 min") == 1 and m("1m") == 1 and m("há 2 min") == 2 and m("30 s") == 0
    assert m("3 h") is None and m("2d") is None and m("") is None


# ===========================================================================
# 2. conta: resolução e troca certa/errada
# ===========================================================================
def test_resolver_conta_pelo_canal_e_conflito():
    cfg = sp.carregar_config()
    assert sp.resolver_conta(cfg, {"canal": "GTA 6 | HP"}) == "hpgta6"
    assert sp.resolver_conta(cfg, {"canal": "Filmes e Séries | HP"}) == "hp.filmes"
    assert sp.resolver_conta(cfg, {"conta": "@HP.Futebol", "canal": "futebol"}) == "hp.futebol"
    assert sp.resolver_conta(cfg, {"conta": "receitas"}) == "hp.receitas"
    with pytest.raises(sp.DadosInvalidos):
        sp.resolver_conta(cfg, {"conta": "hpgta6", "canal": "futebol"})
    with pytest.raises(sp.DadosInvalidos):
        sp.resolver_conta(cfg, {"conta": "outra", "canal": "xadrez"})


def test_link_so_do_instagram():
    assert sp.validar_link(LINK) == LINK
    for ruim in ("https://evil.com/p/x", "http://instagram.com/p/x", "", "https://www.instagram.com/p/x y"):
        with pytest.raises(sp.DadosInvalidos):
            sp.validar_link(ruim)


def test_troca_de_conta_certa():
    ctx, fake, _ = novo(ativa="hp.futebol")
    fake.ligado, fake.tela = True, "feed"
    sp.trocar_conta(ctx, "hpgta6")
    assert fake.ativa == "hpgta6"
    assert sem_ruido(fake.eventos) == ["tap:profile_tab", "tap:action_bar_username_container",
                                       "conta:hpgta6"]


def test_troca_de_conta_ja_ativa_nao_mexe():
    ctx, fake, _ = novo(ativa="hpgta6")
    fake.ligado, fake.tela = True, "feed"
    sp.trocar_conta(ctx, "hpgta6")
    assert "tap:action_bar_username_container" not in fake.eventos


def test_troca_de_conta_errada_aborta():
    ctx, fake, _ = novo(ativa="hp.futebol")
    fake.ligado, fake.tela = True, "feed"
    fake.troca_vai_para = "hp.receitas"
    with pytest.raises(sp.ContaErrada) as e:
        sp.trocar_conta(ctx, "hpgta6")
    assert "hp.receitas" in str(e.value)


def test_conta_nao_logada_aborta_sem_postar():
    ctx, fake, _ = novo()
    fake.contas_logadas.remove("hpgta6")
    item_fila()
    r = sp.rodar_post(ctx, "2026-09-30_gta_trailer3")
    assert r["codigo"] == sp.ERRO and "ContaErrada" in r["resultados"][0]["erro"]
    assert not any(e.startswith("link:") for e in fake.eventos)
    assert fake.eventos[-1] == "desligar"


def test_post_de_outra_conta_aborta():
    ctx, fake, _ = novo()
    fake.autor_post = "outra.conta"
    item_fila()
    r = sp.rodar_post(ctx, "2026-09-30_gta_trailer3")
    assert "outra.conta" in r["resultados"][0]["erro"]
    assert "publicar" not in fake.eventos and "desligar" in fake.eventos


# ===========================================================================
# 3. fluxo completo (sequência de comandos) e 9. story_clicavel feito
# ===========================================================================
def test_fluxo_completo_sequencia_de_comandos():
    ctx, fake, _ = novo(ativa="hp.futebol")
    item_fila()
    r = sp.rodar_post(ctx, "2026-09-30_gta_trailer3")
    assert r["ok"] and r["codigo"] == sp.OK, r
    assert sem_ruido(fake.eventos) == [
        "ligar", "fechar_ig", "abrir_ig",
        "tap:profile_tab", "tap:action_bar_username_container", "conta:hpgta6",
        f"link:{LINK}", "tap:row_feed_button_share", "tap:Adicionar ao story", "publicar",
        "tap:profile_tab", "tap:row_profile_header_imageview", "avancar", "avancar",
        "tap:toolbar_highlights_button", "destaque:GTA 6", "voltar",
        "feito", "desligar"]
    assert fake.adicionados == [("hpgta6", "GTA 6")]
    assert fake.publicados and fake.publicados[0][0] == "hpgta6"
    # comandos exatos do adb / powershell
    assert ["adb", "shell", "am start -a android.intent.action.VIEW -d "
            f"'{LINK}' {PKG}"] in fake.comandos
    assert ["adb", "shell", f"monkey -p {PKG} -c android.intent.category.LAUNCHER 1"] in fake.comandos
    ligar = [c for c in fake.comandos if c[0] == "powershell"][0]
    assert ligar[:5] == ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File"]
    assert ligar[5].endswith("ligar_emulador.ps1")
    assert any(c == ["adb", "shell", "getprop sys.boot_completed"] for c in fake.comandos)
    # estado local
    e = ler_json(sp.arquivo_estado())
    assert e["postados"]["2026-09-30_gta_trailer3"]["estado"] == "publicado"
    assert e["postados"]["2026-09-30_gta_trailer3"]["feito"] is True
    assert e["ultimo_story_em"]


def test_story_clicavel_feito_com_argumentos_certos():
    ctx, fake, _ = novo()
    item_fila(pid="p1")
    sp.rodar_post(ctx, "p1")
    assert len(fake.feitos) == 1
    cmd = fake.feitos[0]
    assert cmd[0] == sys.executable
    assert Path(cmd[1]) == SCRIPTS / "story_clicavel.py"
    assert cmd[2:] == ["feito", "p1", "--link", LINK]
    assert fake.feitos_cwd[0] == str(SCRIPTS.parent)


def test_feito_que_falhou_e_reenviado_sem_ligar_o_emulador():
    ctx, fake, relogio = novo()
    fake.feito_rc = 1
    item_fila(pid="p1")
    sp.rodar_post(ctx, "p1")
    assert ler_json(sp.arquivo_estado())["postados"]["p1"]["feito"] is False
    fake.feito_rc, fake.eventos = 0, []
    relogio.t += 1000
    sp.rodar_fila(ctx)
    assert fake.eventos == ["feito"]     # só o feito; nada de emulador nem story novo
    assert ler_json(sp.arquivo_estado())["postados"]["p1"]["feito"] is True


def test_sem_destaque_nao_abre_o_story():
    ctx, fake, _ = novo()
    item_fila(pid="p2", destaque="")
    assert sp.rodar_post(ctx, "p2")["ok"]
    assert "tap:toolbar_highlights_button" not in fake.eventos
    assert fake.eventos[-2:] == ["feito", "desligar"]


def test_plano_b_pela_grade_quando_o_link_nao_abre():
    ctx, fake, _ = novo(ativa="hpgta6", timeout_post_seg=3)
    fake.link_abre = False
    fake.legenda = "Trailer 3 chegou"
    item_fila(pid="p3", destaque="")
    r = sp.rodar_post(ctx, "p3")
    assert r["ok"], r
    assert "tap:grade:Foto 1" in fake.eventos       # pulou o post fixado
    assert "publicar" in fake.eventos


def test_popup_e_dump_com_erro_nao_atrapalham():
    ctx, fake, _ = novo()
    fake.ligado, fake.tela = True, "launcher"
    fake.popup_ao_abrir = True
    fake.falhas_dump = 2
    sp.abrir_instagram(ctx)
    assert "tap:Agora não" in fake.eventos and fake.tela == "feed"


# ===========================================================================
# 4/5. aviso da Meta e arquivo de parada
# ===========================================================================
def test_aviso_da_meta_interrompe_e_cria_arquivo_de_parada():
    ctx, fake, _ = novo()
    fake.aviso_ao_entrar = {"composer"}
    item_fila()
    r = sp.rodar_post(ctx, "2026-09-30_gta_trailer3")
    assert r["codigo"] == sp.AVISO_META
    p = sp.arquivo_parado()
    assert p.exists()
    dados = json.loads(p.read_text(encoding="utf-8"))
    assert dados["motivo"] == "tente novamente mais tarde" and dados["conta"] == "@hpgta6"
    assert "publicar" not in fake.eventos and "feito" not in fake.eventos
    assert fake.eventos[-1] == "desligar"
    assert list((sp.pasta_emulador() / "avisos").glob("aviso_*.xml"))


def test_legenda_com_palavra_de_aviso_nao_para():
    sel = sp.Seletores()
    nos = sp.parse_xml(tela_xml([el("row_feed_comment_textview_layout",
                                    texto="Polícia suspeita do vilão", b=(0, 0, 10, 10))]))
    assert sp.detectar_aviso(nos, sel) is None
    nos = sp.parse_xml(tela_xml([el(texto="Atividade suspeita na sua conta", b=(0, 0, 10, 10))]))
    assert sp.detectar_aviso(nos, sel)[0] == "atividade suspeita"
    nos = sp.parse_xml(tela_xml([el(texto="Conta suspeita de spam", b=(0, 0, 10, 10))]))
    assert sp.detectar_aviso(nos, sel)[0] == "suspeita"
    # foto de notícia com o texto "SUSPEITA" na descrição automática: não para
    nos = sp.parse_xml(tela_xml([el("row_feed_photo_imageview", classe="android.widget.ImageView",
                                    desc="Pode ser uma imagem com o texto 'SUSPEITA PRESA'",
                                    b=(0, 0, 10, 10)),
                                 el(desc="Foto: polícia suspeita", classe="android.widget.ImageView",
                                    b=(0, 0, 10, 10))]))
    assert sp.detectar_aviso(nos, sel) is None
    # frase completa vale também na descrição
    nos = sp.parse_xml(tela_xml([el(desc="Action Blocked", b=(0, 0, 10, 10))]))
    assert sp.detectar_aviso(nos, sel)[0] == "action blocked"
    nos = sp.parse_xml(tela_xml([el(texto="", classe="android.widget.EditText", senha=True,
                                    b=(0, 0, 10, 10))]))
    assert "senha" in sp.detectar_aviso(nos, sel)[0]


def test_arquivo_de_parada_impede_novos_stories(_raizes):
    _, drive = _raizes
    ctx, fake, _ = novo()
    item_fila()
    lote_enquete(drive)
    escrever_json(sp.arquivo_parado(), {"motivo": "teste"})
    assert sp.rodar_post(ctx, "2026-09-30_gta_trailer3")["codigo"] == sp.BLOQUEADO
    assert sp.rodar_fila(ctx)["codigo"] == sp.BLOQUEADO
    assert sp.rodar_fila(ctx, uma_vez=True)["codigo"] == sp.BLOQUEADO
    assert sp.rodar_enquete(ctx, "2026-09-30")["codigo"] == sp.BLOQUEADO
    assert sp.rodar_contagem(ctx, arte=str(drive / "lotes" / "arte_enquete_0930.png"))["codigo"] \
        == sp.BLOQUEADO
    assert fake.comandos == []   # nem o emulador foi ligado


def test_nunca_toca_em_login_ou_termos():
    ctx, fake, _ = novo()
    fake.ligado = True
    fake.els = lambda: [el(texto="Entrar", b=(0, 0, 500, 100), clicavel=True),
                        el(texto="Li e concordo com os Termos de Uso", b=(0, 200, 500, 300))]
    with pytest.raises(sp.TelaProibida):
        ctx.tela.tocar(texto="Entrar")
    with pytest.raises(sp.TelaProibida):
        ctx.tela.tocar(texto="termos", parcial=True)
    assert not any("input tap" in " ".join(c) for c in fake.comandos)


# ===========================================================================
# 6. intervalo mínimo e 1 story por post
# ===========================================================================
def test_intervalo_minimo_bloqueia_post_avulso():
    ctx, fake, relogio = novo()
    item_fila(pid="p1")
    e = sp.ler_estado()
    e["ultimo_story_em"] = (relogio.agora() - timedelta(seconds=60)).isoformat()
    escrever_json(sp.arquivo_estado(), e)
    r = sp.rodar_post(ctx, "p1")
    assert r["codigo"] == sp.BLOQUEADO and "faltam 120s" in r["mensagem"]
    assert fake.comandos == []
    relogio.t += 121
    assert sp.rodar_post(ctx, "p1")["ok"]


def test_fila_espera_o_intervalo_entre_dois_stories():
    ctx, fake, _ = novo(intervalo_min_seg=180)
    item_fila(pid="a_gta", destaque="")
    item_fila(pid="b_fut", canal="futebol", conta="hp.futebol", destaque="",
              publicado_em="2026-09-30T09:30:00-03:00")
    r = sp.rodar_fila(ctx)
    assert r["ok"], r
    (c1, t1), (c2, t2) = fake.publicados
    assert (c1, c2) == ("hpgta6", "hp.futebol")
    assert t2 - t1 >= 180
    assert fake.eventos.count("ligar") == 1 and fake.eventos.count("desligar") == 1


def test_fila_uma_vez_respeita_intervalo_sem_esperar():
    ctx, fake, relogio = novo()
    item_fila(pid="p1")
    e = sp.ler_estado()
    e["ultimo_story_em"] = relogio.agora().isoformat()
    escrever_json(sp.arquivo_estado(), e)
    r = sp.rodar_fila(ctx, uma_vez=True)
    assert r["codigo"] == sp.BLOQUEADO and fake.comandos == [] and relogio.t == 0


def test_um_story_por_post():
    ctx, fake, relogio = novo()
    item_fila(pid="p1")
    assert sp.rodar_post(ctx, "p1")["ok"]
    relogio.t += 3600
    r = sp.rodar_post(ctx, "p1")
    assert r["codigo"] == sp.BLOQUEADO and "já saiu" in r["mensagem"]
    assert fake.eventos.count("publicar") == 1
    assert sp.listar_pendentes(ctx) == []


def test_listar_pendentes_filtra_a_fila():
    ctx, _, _ = novo()
    item_fila(pid="ok1")
    item_fila(pid="futuro", publicado_em="2026-09-30T23:00:00-03:00")
    item_fila(pid="feito1", status="feito")
    item_fila(pid="semlink", link="")
    (sp.pasta_fila() / "quebrado.json").write_text("{nao é json", encoding="utf-8")
    e = sp.ler_estado()
    e["tentativas"]["cansado"] = 3
    escrever_json(sp.arquivo_estado(), e)
    item_fila(pid="cansado")
    assert [d["post_id"] for d in sp.listar_pendentes(ctx)] == ["ok1"]


# ===========================================================================
# 7. emulador sempre desligado em erro / 10. orçamento
# ===========================================================================
@pytest.mark.parametrize("quebra", ["conta_errada", "excecao", "boot"])
def test_emulador_sempre_desligado_em_erro(quebra):
    ctx, fake, _ = novo()
    item_fila()
    if quebra == "conta_errada":
        fake.troca_vai_para = "hp.carros"
    elif quebra == "excecao":
        fake.falha_em = {"am start": RuntimeError("adb travou")}
    else:
        fake.falha_boot = True
    r = sp.rodar_post(ctx, "2026-09-30_gta_trailer3")
    assert not r["ok"]
    assert fake.eventos[-1] == "desligar"
    assert "publicar" not in fake.eventos
    falha = sp.ler_estado()["falhas"][-1]
    assert falha["story"] == "2026-09-30_gta_trailer3"
    assert sp.ler_estado()["tentativas"]["2026-09-30_gta_trailer3"] == 1


def test_orcamento_de_5_min_estourado():
    ctx, fake, relogio = novo(orcamento_seg=300)
    fake.custo = {"dump": 30}        # cada leitura de tela "demora" 30 s
    item_fila()
    r = sp.rodar_post(ctx, "2026-09-30_gta_trailer3")
    res = r["resultados"][0]
    assert not res["ok"] and "OrcamentoEstourado" in res["erro"]
    assert "publicar" not in fake.eventos and fake.eventos[-1] == "desligar"
    falha = sp.ler_estado()["falhas"][-1]
    assert "OrcamentoEstourado" in falha["erro"] and falha["passo"]
    hist = sp.arquivo_historico().read_text(encoding="utf-8")
    assert "FALHA" in hist and "orçamento" in hist


def test_tres_falhas_tiram_o_post_da_fila():
    ctx, fake, relogio = novo()
    fake.contas_logadas.remove("hpgta6")
    item_fila(pid="p1")
    for _ in range(3):
        sp.rodar_fila(ctx, uma_vez=True)
        relogio.t += 400
    assert sp.ler_estado()["tentativas"]["p1"] == 3
    fake.eventos = []
    assert sp.rodar_fila(ctx)["mensagem"] == "fila vazia" and fake.eventos == []


# ===========================================================================
# 8. enquete (pergunta <= 25) e contagem
# ===========================================================================
def test_pergunta_da_enquete_maior_que_25_aborta(_raizes):
    _, drive = _raizes
    ctx, fake, _ = novo()
    lote_enquete(drive, pergunta="Qual vai ser o preço do GTA 6 no Brasil?")
    with pytest.raises(sp.PerguntaLonga):
        sp.carregar_enquete(ctx.cfg, "2026-09-30")
    r = sp.rodar_enquete(ctx, "2026-09-30")
    assert r["codigo"] == sp.ERRO and "25" in r["mensagem"]
    assert fake.comandos == []
    cortada = sp.carregar_enquete(ctx.cfg, "2026-09-30", cortar=True)["pergunta"]
    assert len(cortada) <= 25 and cortada == "Qual vai ser o preço do"


def test_enquete_opcoes_invalidas(_raizes):
    _, drive = _raizes
    ctx, _, _ = novo()
    lote_enquete(drive, opcoes=["Só uma"])
    with pytest.raises(sp.DadosInvalidos):
        sp.carregar_enquete(ctx.cfg, "2026-09-30")


def test_enquete_fluxo_completo(_raizes):
    _, drive = _raizes
    ctx, fake, _ = novo(ativa="hpgta6")
    lote_enquete(drive)
    r = sp.rodar_enquete(ctx, "2026-09-30")
    assert r["ok"], r
    nome = fake.pushados[0]
    assert re.fullmatch(r"hp_enquete_\d{8}_\d{6}\.png", nome)
    assert fake.escolhida == nome                      # pegou a arte recém-enviada
    assert fake.enquete_pronta == {"pergunta": "Vai comprar no 1º dia?", "op0": "Sim", "op1": "Não"}
    assert "digitar.py:Vai comprar no 1º dia?" in fake.eventos    # acento pelo digitar.py
    assert "texto:Sim" in fake.eventos                            # ASCII pelo input text
    assert ["adb", "shell", "am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE "
            f"-d file:///sdcard/Pictures/{nome}"] in fake.comandos
    ev = sem_ruido(fake.eventos)
    ordem = [f"push:{nome}", "scan", "tap:creation_tab", "tap:Story", "tap:galeria",
             "tap:Foto 0", "tap:asset_button", "tap:sticker_enquete", "tap:done_button",
             "arrastar:540,1200->540,1650", "publicar", "destaque:Enquetes", "desligar"]
    pos = [ev.index(x) for x in ordem]
    assert pos == sorted(pos), ev
    assert fake.adicionados == [("hpgta6", "Enquetes")]
    assert "feito" not in fake.eventos
    # 1 enquete por dia
    assert sp.rodar_enquete(ctx, "2026-09-30")["codigo"] == sp.BLOQUEADO


def test_contagem_regressiva_fluxo_com_busca(_raizes):
    _, drive = _raizes
    ctx, fake, _ = novo(ativa="hpgta6")
    arte = drive / "fundo_contagem.png"
    arte.write_bytes(b"\x89PNG")
    fake.bandeja_so_com_busca = True
    r = sp.rodar_contagem(ctx, arte=str(arte))
    assert r["ok"], r
    assert "texto:contagem" in fake.eventos                      # buscou a figurinha
    assert fake.titulo_contagem == "Lançamento do GTA 6"
    assert fake.dia_inteiro is True
    assert fake.eventos.count("tap:proximo_mes") == 2            # setembro -> novembro
    assert fake.data_confirmada == date(2026, 11, 19)
    assert fake.publicados[-1][0] == "hpgta6"
    assert fake.eventos[-1] == "desligar"


def test_contagem_sem_arte_ou_data_passada():
    ctx, _, _ = novo()
    r = sp.rodar_contagem(ctx)
    assert r["codigo"] == sp.ERRO and "arte" in r["mensagem"]
    with pytest.raises(sp.DadosInvalidos):
        sp.carregar_contagem(ctx.cfg, "2026-09-30", arte="x.png", data_alvo="2026-09-01",
                             hoje=date(2026, 9, 30))


# ===========================================================================
# --simular, status e CLI
# ===========================================================================
def test_simular_nao_chama_adb_e_imprime_o_roteiro(capsys, monkeypatch):
    def proibido(*a, **k):
        raise AssertionError("o --simular não pode rodar comando nenhum")
    monkeypatch.setattr(sp, "rodar", proibido)
    item_fila(pid="p1")
    assert sp.main(["--simular", "post", "p1"]) == 0
    out = capsys.readouterr().out
    for trecho in ("ligar_emulador.ps1", "am start -a android.intent.action.VIEW",
                   "row_feed_button_share", "your_story_share_shortcut_button",
                   "reel_viewer_timestamp", "story_clicavel.py feito p1 --link",
                   "desligar_emulador.ps1"):
        assert trecho in out, trecho
    assert not sp.arquivo_estado().exists() and not sp.arquivo_parado().exists()
    # --simular também depois do comando
    assert sp.main(["fila", "--simular"]) == 0


def test_simular_enquete_mostra_digitacao_e_arrasto(capsys, _raizes):
    _, drive = _raizes
    lote_enquete(drive)
    assert sp.main(["enquete", "--dia", "2026-09-30", "--simular"]) == 0
    out = capsys.readouterr().out
    assert "digitar 'Vai comprar no 1º dia?'" in out
    assert "poll_sticker_v2_question" in out and "input swipe" in out


def test_status_e_config(capsys):
    assert sp.main(["config"]) == 0
    cfg = ler_json(sp.arquivo_config())
    assert cfg["contas"]["gta"] == "hpgta6" and cfg["intervalo_min_seg"] == 180
    escrever_json(sp.arquivo_parado(), {"motivo": "x"})
    assert sp.main(["status"]) == 0
    assert "PARADO por aviso da Meta: SIM" in capsys.readouterr().out


def test_config_do_usuario_sobrepoe_padrao():
    escrever_json(sp.arquivo_config(), {"intervalo_min_seg": 600,
                                        "contas": {"gta": "@novo.gta"},
                                        "seletores": {"ids": {"compartilhar": ["novo_share"]}}})
    cfg = sp.carregar_config()
    assert cfg["intervalo_min_seg"] == 600
    assert cfg["contas"]["gta"] == "@novo.gta" and cfg["contas"]["futebol"] == "hp.futebol"
    assert sp.Seletores(cfg["seletores"]).id("compartilhar") == ["novo_share"]
    assert sp.resolver_conta(cfg, {"canal": "gta"}) == "novo.gta"


def test_gancho_executar_do_hp_studio(monkeypatch):
    monkeypatch.setattr(sp, "achar_adb", lambda cfg=None: None)
    r = sp.executar({"modo": "fila"})
    assert r["ok"] is False and r["codigo"] == sp.ERRO and "adb" in r["mensagem"]
    r = sp.executar({"modo": "fila", "simular": True})
    assert r["ok"] and r["mensagem"] == "fila vazia"
    assert sp.executar({"modo": "xpto", "simular": True})["codigo"] == sp.ERRO


def test_dia_hoje_e_dia_invalido():
    ctx, fake, _ = novo()
    assert sp._dia(ctx, "hoje") == "2026-09-30" and sp._dia(ctx, None) == "2026-09-30"
    r = sp.rodar_enquete(ctx, "30/09")
    assert r["codigo"] == sp.ERRO and "AAAA-MM-DD" in r["mensagem"] and fake.comandos == []
