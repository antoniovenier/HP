# -*- coding: utf-8 -*-
"""adb_falso.py — o adb de mentira dos testes do story_dispositivo / story_fluxos (sem aparelho).

AdbFalso é um `runner(argv) -> (codigo, saida)` que responde como o adb responderia — `devices`,
`getprop sys.boot_completed`, `wm size`, `dumpsys power|window|activity`, `uiautomator dump`,
`cat /sdcard/ui.xml`, `input tap|swipe|text|keyevent|keycombination`, `push`, `pull`, `am start`,
`am broadcast`, `content call|query`, `monkey`, `screencap`, `ime list`, `settings get` — e anota
TUDO (`comandos`, `toques`, `digitados`, `pushados`, `scans`...).

As telas vêm de arquivos XML de uiautomator em tests/fixtures/android/:
  - ui_story_visualizador_hp_futebol_derivado.xml: DERIVADO do único dump real do PC (§4.7, saída do
    ui.py com o centro de cada elemento); os centros são reais, largura/altura são ESTIMADOS
    (bounds_estimados) — o PC troca pelo ui.xml de verdade quando a coleta (E4) existir;
  - *_sintetico_1080x2400.xml e *_sintetico_1080x2340.xml: telas INVENTADAS (perfil, lista de contas,
    post aberto, folha Send, editor, figurinhas, enquete, link, galeria, destaques, aviso da Meta,
    login), com os ids do story_post_seletores.py; a versão 2340 é proporcional (y × 2340/2400).
    "sintetico" NO NOME para o PC saber que não são dumps reais.
Toque: o AdbFalso acha o menor nó clicável que contém (x, y) na tela atual e segue `transicoes`
{(tela, id ou texto): próxima tela}; assim um fluxo só avança se tocou DENTRO dos bounds certos —
é a prova de que ninguém usa coordenada fixa (o mesmo fluxo em 1080x2400 e 1080x2340 dá toques
diferentes e proporcionais).

Gerar/regenerar as fixtures: python scripts\\testes\\adb_falso.py  (grava em tests/fixtures/android/)
"""
from __future__ import annotations

import re
import shlex
import sys
from pathlib import Path
from xml.sax.saxutils import quoteattr

AQUI = Path(__file__).resolve().parent
SCRIPTS = AQUI.parent
RAIZ = SCRIPTS.parent
FIXTURES = RAIZ / "tests" / "fixtures" / "android"
PC_REAL = RAIZ / "tests" / "fixtures" / "pc_real"
DUMP_REAL = PC_REAL / "ui_story_visualizador_hp_futebol.txt"
for _p in (SCRIPTS, RAIZ / "app" / "hp_studio_nuvem"):
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import ui_dump  # noqa: E402
import story_dispositivo as sd  # noqa: E402

PKG = "com.instagram.android"
TELA_PADRAO = (1080, 2400)
TELA_ALTERNATIVA = (1080, 2340)
TELAS_TESTE = (TELA_PADRAO, TELA_ALTERNATIVA)
CONTAS = ["hpgta6", "hp.futebol", "hp.filmes", "hp.receitas", "hp.carros", "hp.destinos"]
IME_GBOARD = "com.google.android.inputmethod.latin/com.android.inputmethod.latin.LatinIME"
NOME_DERIVADO = "ui_story_visualizador_hp_futebol_derivado.xml"
NOME_DERIVADO_2340 = "ui_story_visualizador_hp_futebol_derivado_sintetico_1080x2340.xml"
COMENTARIO_DERIVADO = (
    "DERIVADO do dump real de 30/09 23:41 (tests/fixtures/pc_real/ui_story_visualizador_hp_futebol.txt, "
    "saida do ui.py): os CENTROS sao reais; largura e altura sao ESTIMADAS a partir do centro "
    "(bounds_estimados em scripts/testes/adb_falso.py). O PC troca este arquivo pelo ui.xml real da coleta (E4).")
COMENTARIO_SINTETICO = (
    "SINTETICO: tela '{nome}' inventada para os testes, {w}x{h} (ids do story_post_seletores.py; os de "
    "A_CONFIRMAR sao palpite). O PC troca este arquivo pelo dump real da coleta (tarefa E4). "
    "Gerado por scripts/testes/adb_falso.py (gerar_fixtures).")


# ===========================================================================
# XML de uiautomator
# ===========================================================================
def el(id="", texto="", desc="", b=(0, 0, 0, 0), clicavel=False, classe="android.widget.TextView",
       senha=False, focado=False, pacote=PKG, marcado=False) -> dict:
    return {"id": id, "texto": texto, "desc": desc, "b": tuple(b), "clicavel": clicavel, "classe": classe,
            "senha": senha, "focado": focado, "pacote": pacote, "marcado": marcado}


def no_xml(e: dict) -> str:
    rid = e.get("id", "")
    if rid and ":" not in rid:
        rid = f"{PKG}:id/{rid}"
    b = e.get("b", (0, 0, 0, 0))
    clic = bool(e.get("clicavel"))
    attrs = {
        "index": "0", "text": e.get("texto", ""), "resource-id": rid,
        "class": e.get("classe", "android.widget.TextView"), "package": e.get("pacote", PKG),
        "content-desc": e.get("desc", ""), "checkable": "false",
        "checked": str(bool(e.get("marcado"))).lower(), "clickable": str(clic).lower(), "enabled": "true",
        "focusable": str(clic).lower(), "focused": str(bool(e.get("focado"))).lower(), "scrollable": "false",
        "long-clickable": "false", "password": str(bool(e.get("senha"))).lower(), "selected": "false",
        "bounds": f"[{b[0]},{b[1]}][{b[2]},{b[3]}]",
    }
    return "<node " + " ".join(f"{k}={quoteattr(str(v))}" for k, v in attrs.items()) + " />"


def xml_da_tela(els: list, tela: tuple = TELA_PADRAO, comentario: str = "") -> str:
    W, H = tela
    raiz = no_xml(el(classe="android.widget.FrameLayout", b=(0, 0, W, H)))[:-3] + ">"
    linhas = ["<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>"]
    if comentario:
        linhas.append("<!-- " + comentario.replace("--", "- -") + " -->")
    linhas.append('<hierarchy rotation="0">')
    linhas.append(raiz)
    linhas += ["  " + no_xml(e) for e in els]
    linhas.append("</node></hierarchy>")
    return "\n".join(linhas) + "\n"


def escalar(els: list, tela: tuple, base: tuple = TELA_PADRAO) -> list:
    """Bounds proporcionais a outra tela (x × W/1080, y × H/2400)."""
    fx, fy = tela[0] / base[0], tela[1] / base[1]
    saida = []
    for e in els:
        x0, y0, x1, y1 = e["b"]
        d = dict(e)
        d["b"] = (int(round(x0 * fx)), int(round(y0 * fy)), int(round(x1 * fx)), int(round(y1 * fy)))
        saida.append(d)
    return saida


# ===========================================================================
# Dump real (centros) -> XML com bounds estimados
# ===========================================================================
def bounds_estimados(no: dict, tela: tuple = TELA_PADRAO) -> tuple:
    """Caixa em volta do centro real: texto -> 24 px por letra × 56; clicável -> 140×140 (ou largo
    quando a descrição é longa); contêiner centrado sem texto -> largura toda, altura até a borda
    mais perto; o resto (ícones) -> 48×48. Tudo recortado na tela."""
    W, H = tela
    cx, cy = int(no["x"]), int(no["y"])
    texto, desc = no.get("texto") or "", no.get("desc") or ""
    if texto:
        w, h = max(48, 24 * len(texto)), 56
    elif no.get("clicavel"):
        w = min(2 * cx, 2 * (W - cx), 24 * len(desc)) if len(desc) > 20 else 140
        w, h = max(w, 140), 140
    elif cx == W // 2 and not desc:
        w, h = W, 2 * min(cy, H - cy)
    else:
        w, h = 48, 48
    # encolhe (em vez de recortar) para o CENTRO continuar exatamente o do dump real
    w = min(w, 2 * cx, 2 * (W - cx))
    h = min(h, 2 * cy, 2 * (H - cy))
    w, h = w - w % 2, h - h % 2
    return (cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2)


def elementos_do_ui_py(texto: str, tela: tuple = TELA_PADRAO) -> list:
    classes = {"TextView": "android.widget.TextView", "Button": "android.widget.Button",
               "ImageView": "android.widget.ImageView", "LinearLayout": "android.widget.LinearLayout",
               "FrameLayout": "android.widget.FrameLayout", "ViewGroup": "android.view.ViewGroup",
               "View": "android.view.View"}
    saida = []
    for n in ui_dump.ler_linhas_ui(texto):
        saida.append(el(id=n["id"], texto=n["texto"], desc=n["desc"], b=bounds_estimados(n, tela),
                        clicavel=n["clicavel"], classe=classes.get(n["classe"], "android.view." + n["classe"])))
    return saida


def xml_derivado_do_ui_py(texto: str, tela: tuple = TELA_PADRAO, comentario: str = COMENTARIO_DERIVADO) -> str:
    els = elementos_do_ui_py(texto, TELA_PADRAO)
    if tuple(tela) != TELA_PADRAO:
        els = escalar(els, tela)
        comentario += f" Versao PROPORCIONAL (sintetica) para {tela[0]}x{tela[1]}."
    return xml_da_tela(els, tela, comentario)


# ===========================================================================
# Telas sintéticas (1080x2400; as de 2340 são proporcionais)
# ===========================================================================
ABAS = [el("feed_tab", desc="Home", b=(0, 2253, 216, 2400), clicavel=True, classe="android.widget.FrameLayout"),
        el("search_tab", desc="Search and explore", b=(216, 2253, 432, 2400), clicavel=True,
           classe="android.widget.FrameLayout"),
        el("creation_tab", desc="Create", b=(432, 2253, 648, 2400), clicavel=True, classe="android.widget.FrameLayout"),
        el("clips_tab", desc="Reels", b=(648, 2253, 864, 2400), clicavel=True, classe="android.widget.FrameLayout"),
        el("profile_tab", desc="Profile", b=(864, 2253, 1080, 2400), clicavel=True, classe="android.widget.FrameLayout")]


def telas_sinteticas() -> dict:
    t = {}
    t["perfil"] = [
        el("action_bar_container", b=(0, 63, 1080, 210), classe="android.widget.FrameLayout"),
        el("action_bar_username_container", b=(42, 84, 505, 189), clicavel=True, classe="android.widget.LinearLayout"),
        el("action_bar_large_title_auto_size", texto="hpgta6", b=(42, 105, 389, 168)),
        el("action_bar_title_chevron", desc="Switch accounts", b=(400, 115, 442, 157), classe="android.widget.ImageView"),
        el("action_bar_new_post_button", desc="Create", b=(820, 90, 930, 180), clicavel=True, classe="android.widget.ImageView"),
        el("action_bar_overflow_icon", desc="Options", b=(950, 90, 1060, 180), clicavel=True, classe="android.widget.ImageView"),
        el("row_profile_header_imageview", desc="Profile photo of hpgta6", b=(42, 252, 273, 483), clicavel=True,
           classe="android.widget.ImageView"),
        el("profile_header_full_name", texto="GTA 6 | HP", b=(42, 510, 500, 560)),
        el("profile_header_bio_text", texto="Tudo sobre o GTA 6. Valores aproximados.", b=(42, 570, 900, 640)),
        el("profile_header_edit_profile_button", texto="Edit profile", b=(42, 700, 520, 800), clicavel=True,
           classe="android.widget.Button"),
        el("profile_header_share_profile_button", texto="Share profile", b=(540, 700, 1038, 800), clicavel=True,
           classe="android.widget.Button"),
        el("image_button", desc="Photo by hpgta6, 1 of 9", b=(0, 1000, 358, 1358), clicavel=True, classe="android.widget.ImageView"),
        el("image_button", desc="Photo by hpgta6, 2 of 9", b=(361, 1000, 719, 1358), clicavel=True, classe="android.widget.ImageView"),
        el("image_button", desc="Photo by hpgta6, 3 of 9", b=(722, 1000, 1080, 1358), clicavel=True, classe="android.widget.ImageView"),
    ] + ABAS
    linhas = []
    y = 1300
    for h in CONTAS:
        linhas.append(el("row_user_container", desc=f"{h}", b=(0, y, 1080, y + 150), clicavel=True,
                         classe="android.widget.LinearLayout"))
        linhas.append(el("row_user_textview", texto=h, b=(180, y + 45, 700, y + 105)))
        y += 150
    t["lista_contas"] = [
        el("bottom_sheet_container", b=(0, 1180, 1080, 2400), classe="android.widget.FrameLayout"),
        el("bottom_sheet_drag_handle", desc="Drag handle", b=(480, 1190, 600, 1210), classe="android.view.View"),
        el("title", texto="Accounts", b=(42, 1220, 500, 1290)),
    ] + linhas + [
        el("row_add_account", texto="Add account", b=(0, y, 1080, y + 150), clicavel=True, classe="android.widget.LinearLayout"),
    ]
    t["post_aberto"] = [
        el("action_bar_title", texto="Posts", b=(400, 90, 680, 180)),
        el("row_feed_photo_profile_name", texto="hpgta6", b=(140, 240, 420, 300), clicavel=True),
        el("row_feed_photo_imageview", desc="Photo by hpgta6", b=(0, 330, 1080, 1410), clicavel=True,
           classe="android.widget.ImageView"),
        el("row_feed_button_like", desc="Like", b=(20, 1430, 140, 1550), clicavel=True, classe="android.widget.ImageView"),
        el("row_feed_button_comment", desc="Comment", b=(160, 1430, 280, 1550), clicavel=True, classe="android.widget.ImageView"),
        el("row_feed_button_share", desc="Share", b=(300, 1430, 420, 1550), clicavel=True, classe="android.widget.ImageView"),
        el("row_feed_button_save", desc="Save", b=(940, 1430, 1060, 1550), clicavel=True, classe="android.widget.ImageView"),
        el("row_feed_textview_likes", texto="1,234 likes", b=(40, 1570, 400, 1620), clicavel=True),
        el("row_feed_comment_textview_layout",
           texto="hpgta6 Dá pra ficar GORDO no GTA 6: a suspeita virou verdade. Valores aproximados.",
           b=(40, 1640, 1040, 1760), clicavel=True),
    ] + ABAS
    t["folha_send"] = [
        el("bottom_sheet_container", b=(0, 560, 1080, 2400), classe="android.widget.FrameLayout"),
        el("row_search_edit_text", texto="Search", b=(60, 600, 1020, 700), clicavel=True, classe="android.widget.EditText"),
        el("direct_share_sheet_add_to_story", texto="Add to story", b=(60, 740, 540, 900), clicavel=True,
           classe="android.widget.LinearLayout"),
        el("direct_share_sheet_copy_link", texto="Copy link", b=(540, 740, 1020, 900), clicavel=True,
           classe="android.widget.LinearLayout"),
        el("row_inbox_username", texto="amigo.um", b=(180, 960, 700, 1020)),
        el("direct_share_sheet_send_button", texto="Send", b=(820, 950, 1020, 1030), clicavel=True, classe="android.widget.Button"),
        el("row_inbox_username", texto="amiga.dois", b=(180, 1110, 700, 1170)),
        el("direct_share_sheet_send_button", texto="Send", b=(820, 1100, 1020, 1180), clicavel=True, classe="android.widget.Button"),
    ]
    t["editor"] = [
        el("camera_close_button", desc="Close", b=(20, 90, 140, 210), clicavel=True, classe="android.widget.ImageView"),
        el("text_tool_button", desc="Text", b=(560, 90, 680, 210), clicavel=True, classe="android.widget.ImageView"),
        el("asset_button", desc="Stickers", b=(700, 90, 820, 210), clicavel=True, classe="android.widget.ImageView"),
        el("draw_button", desc="Draw", b=(840, 90, 960, 210), clicavel=True, classe="android.widget.ImageView"),
        el("camera_preview", desc="Story preview", b=(0, 240, 1080, 2160), classe="android.widget.FrameLayout"),
        el("your_story_share_shortcut_button", texto="Your story", b=(40, 2200, 480, 2360), clicavel=True,
           classe="android.widget.LinearLayout"),
        el("close_friends_share_shortcut_button", texto="Close friends", b=(500, 2200, 900, 2360), clicavel=True,
           classe="android.widget.LinearLayout"),
        el("share_button", desc="Send to", b=(920, 2200, 1060, 2360), clicavel=True, classe="android.widget.ImageView"),
    ]
    figs = []
    nomes = ["LOCATION", "MENTION", "ADD YOURS", "POLL", "QUESTIONS", "LINK", "COUNTDOWN", "QUIZ", "MUSIC"]
    x, y = 40, 760
    for i, nome in enumerate(nomes):
        figs.append(el("asset_item", texto=nome, b=(x, y, x + 320, y + 160), clicavel=True, classe="android.widget.FrameLayout"))
        x += 340
        if x > 760:
            x, y = 40, y + 200
    t["figurinhas"] = [
        el("bottom_sheet_container", b=(0, 400, 1080, 2400), classe="android.widget.FrameLayout"),
        el("row_search_edit_text", texto="Search", b=(60, 480, 1020, 600), clicavel=True, classe="android.widget.EditText"),
    ] + figs
    t["enquete"] = [
        el("poll_sticker_v2_container", b=(90, 900, 990, 1500), classe="android.widget.LinearLayout"),
        el("poll_sticker_v2_question", texto="Ask a question…", b=(120, 940, 960, 1060), clicavel=True, focado=True,
           classe="android.widget.EditText"),
        el("poll_sticker_v2_option_text", texto="Yes", b=(120, 1100, 960, 1220), clicavel=True, classe="android.widget.EditText"),
        el("poll_sticker_v2_option_text", texto="No", b=(120, 1240, 960, 1360), clicavel=True, classe="android.widget.EditText"),
        el("poll_sticker_v2_add_option", texto="Add option", b=(120, 1380, 960, 1460), clicavel=True),
        el("done_button", texto="Done", b=(880, 90, 1040, 190), clicavel=True, classe="android.widget.TextView"),
    ]
    t["link"] = [
        el("link_sticker_url_edit_text", texto="URL", b=(120, 400, 960, 520), clicavel=True, focado=True, classe="android.widget.EditText"),
        el("link_sticker_custom_text_button", texto="Customize sticker text", b=(120, 560, 960, 640), clicavel=True),
        el("link_sticker_custom_text_edit_text", texto="Sticker text", b=(120, 660, 960, 780), clicavel=True,
           classe="android.widget.EditText"),
        el("done_button", texto="Done", b=(880, 90, 1040, 190), clicavel=True, classe="android.widget.TextView"),
    ]
    itens = []
    for i in range(6):
        x, y = (i % 3) * 360, 400 + (i // 3) * 360
        itens.append(el("gallery_grid_item_thumbnail", desc=f"Photo, {i + 1} of 6", b=(x, y, x + 356, y + 356),
                        clicavel=True, classe="android.widget.ImageView"))
    t["galeria"] = [
        el("gallery_folder_menu", texto="Recents", b=(60, 90, 400, 190), clicavel=True),
        el("gallery_multi_select_button", desc="Select multiple", b=(900, 90, 1040, 190), clicavel=True,
           classe="android.widget.ImageView"),
    ] + itens + ABAS[:0]
    t["destaques"] = [
        el("title", texto="Add to highlights", b=(42, 120, 800, 190)),
        el("highlight_new", texto="New", b=(0, 300, 1080, 450), clicavel=True, classe="android.widget.LinearLayout"),
        el("highlight_title", texto="Enquetes", b=(0, 460, 1080, 610), clicavel=True, classe="android.widget.LinearLayout"),
        el("highlight_title", texto="GTA 6", b=(0, 620, 1080, 770), clicavel=True, classe="android.widget.LinearLayout"),
        el("highlight_title", texto="Notícias", b=(0, 780, 1080, 930), clicavel=True, classe="android.widget.LinearLayout"),
    ]
    t["aviso_meta"] = [
        el("igds_headline_headline", texto="Try Again Later", b=(100, 900, 980, 1000)),
        el("igds_headline_body", texto="We limit how often you can do certain things on Instagram, like following "
           "people, to protect our community. Tell us if you think we made a mistake.", b=(100, 1020, 980, 1300)),
        el("primary_button", texto="Tell us", b=(100, 1360, 980, 1480), clicavel=True, classe="android.widget.Button"),
        el("secondary_button", texto="OK", b=(100, 1500, 980, 1620), clicavel=True, classe="android.widget.Button"),
    ]
    t["login"] = [
        el("login_landing_logo", desc="Instagram", b=(340, 400, 740, 560), classe="android.widget.ImageView"),
        el("login_username", texto="Phone number, username or email", b=(60, 900, 1020, 1030), clicavel=True,
           classe="android.widget.EditText"),
        el("password", texto="Password", b=(60, 1070, 1020, 1200), clicavel=True, senha=True, classe="android.widget.EditText"),
        el("login_button", texto="Log in", b=(60, 1260, 1020, 1390), clicavel=True, classe="android.widget.Button"),
        el("login_forgot_button", texto="Forgot password?", b=(300, 1430, 780, 1500), clicavel=True),
        el("sign_up_button", texto="Create new account", b=(60, 2150, 1020, 2280), clicavel=True, classe="android.widget.Button"),
    ]
    t["termos"] = [
        el("igds_headline_headline", texto="We've updated our Terms", b=(100, 800, 980, 900)),
        el("igds_headline_body", texto="Review and agree to the updated Terms of Use to continue.", b=(100, 940, 980, 1200)),
        el("primary_button", texto="I agree", b=(100, 1300, 980, 1420), clicavel=True, classe="android.widget.Button"),
    ]
    return t


TELAS_SINTETICAS = tuple(telas_sinteticas().keys())


def arquivo_tela(nome: str, tela: tuple = TELA_PADRAO, pasta: Path = FIXTURES) -> Path:
    W, H = tela
    if nome == "visualizador":
        return pasta / (NOME_DERIVADO if (W, H) == TELA_PADRAO else NOME_DERIVADO_2340)
    return pasta / f"{nome}_sintetico_{W}x{H}.xml"


def gerar_fixtures(pasta: Path = FIXTURES, dump_real: Path = DUMP_REAL) -> dict:
    """Grava todos os XML (dict caminho -> texto). Determinístico: rodar de novo dá o mesmo conteúdo."""
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    arquivos = {}
    real = dump_real.read_text(encoding="utf-8-sig")
    arquivos[arquivo_tela("visualizador", TELA_PADRAO, pasta)] = xml_derivado_do_ui_py(real, TELA_PADRAO)
    arquivos[arquivo_tela("visualizador", TELA_ALTERNATIVA, pasta)] = xml_derivado_do_ui_py(real, TELA_ALTERNATIVA)
    for nome, els in telas_sinteticas().items():
        for tela in TELAS_TESTE:
            W, H = tela
            e = els if tela == TELA_PADRAO else escalar(els, tela)
            arquivos[arquivo_tela(nome, tela, pasta)] = xml_da_tela(
                e, tela, COMENTARIO_SINTETICO.format(nome=nome, w=W, h=H))
    for p, texto in arquivos.items():
        p.write_text(texto, encoding="utf-8")
    return arquivos


# ===========================================================================
# Log que guarda as linhas (para conferir "acento trocado: ...")
# ===========================================================================
class LogLista:
    def __init__(self):
        self.linhas: list[tuple] = []

    def _add(self, nivel, msg, *args):
        self.linhas.append((nivel, (msg % args) if args else str(msg)))

    def info(self, msg, *a):
        self._add("INFO", msg, *a)

    def warning(self, msg, *a):
        self._add("WARNING", msg, *a)

    def error(self, msg, *a):
        self._add("ERROR", msg, *a)

    def debug(self, msg, *a):
        self._add("DEBUG", msg, *a)

    def texto(self) -> str:
        return "\n".join(m for _, m in self.linhas)


# ===========================================================================
# O adb falso
# ===========================================================================
def _transicoes_padrao() -> dict:
    def troca_conta(falso, no):
        falso.conta = no.desc or no.texto
        return "perfil"

    return {
        ("perfil", "action_bar_username_container"): "lista_contas",
        ("perfil", "row_profile_header_imageview"): "visualizador",
        ("perfil", "creation_tab"): "galeria",
        ("perfil", "action_bar_new_post_button"): "galeria",
        ("perfil", "image_button"): "post_aberto",
        ("lista_contas", "row_user_container"): troca_conta,
        ("galeria", "gallery_grid_item_thumbnail"): "editor",
        ("editor", "asset_button"): "figurinhas",
        ("figurinhas", "POLL"): "enquete",
        ("figurinhas", "LINK"): "link",
        ("enquete", "done_button"): "editor",
        ("link", "done_button"): "editor",
        ("editor", "your_story_share_shortcut_button"): "perfil",
        ("post_aberto", "row_feed_button_share"): "folha_send",
        ("folha_send", "Add to story"): "editor",
        ("visualizador", "toolbar_highlights_button"): "destaques",
        ("destaques", "Enquetes"): "visualizador",
        ("destaques", "GTA 6"): "visualizador",
    }


class AdbFalso:
    """runner(argv) de mentira. Veja a docstring do módulo."""

    def __init__(self, tela: tuple = TELA_PADRAO, dispositivos=None, tela_atual: str = "perfil",
                 boot_apos: int = 0, acesa: bool = True, travada: bool = False, pin: bool = False,
                 app: str = PKG, falhas_dump: int = 0, cat_cortado: int = 0, transicoes: dict | None = None,
                 conta: str = "hpgta6", teclado_adb: bool = False, indexa_em: str | None = "principal",
                 override: tuple | None = None, link_abre: str | None = "post_aberto",
                 telas: dict | None = None, pasta_fixtures: Path = FIXTURES, falha_em: dict | None = None):
        self.tela = tuple(tela)
        self.dispositivos = list(dispositivos if dispositivos is not None else [("emulator-5554", "device")])
        self.tela_atual = tela_atual
        self.boot_apos = int(boot_apos)
        self.acesa, self.travada, self.pin = acesa, travada, pin
        self.app = app
        self.falhas_dump, self.cat_cortado = int(falhas_dump), int(cat_cortado)
        self.transicoes = dict(_transicoes_padrao())
        if transicoes:
            self.transicoes.update(transicoes)
        self.conta = conta
        self.teclado_adb = teclado_adb
        self.indexa_em = indexa_em
        self.override = override
        self.link_abre = link_abre
        self.telas = dict(telas or {})
        self.pasta_fixtures = Path(pasta_fixtures)
        self.falha_em = dict(falha_em or {})       # trecho do comando -> (codigo, saida)
        self.comandos: list[list] = []
        self.shell_cmds: list[str] = []
        self.toques: list[tuple] = []
        self.swipes: list[tuple] = []
        self.teclas: list[str] = []
        self.digitados: list[str] = []
        self.broadcasts: list[str] = []
        self.pushados: list[tuple] = []
        self.pulls: list[tuple] = []
        self.scans: list[str] = []
        self.indexados: set = set()
        self.ultimo_push_nome = ""
        self.abertos: list[str] = []
        self.pilha: list[str] = []
        self.n_getprop = 0
        self.n_dump = 0
        self.ultimo_xml = ""
        self.dump_gravado = False

    # -- telas --------------------------------------------------------------------
    def xml_tela(self, nome: str | None = None) -> str:
        nome = nome or self.tela_atual
        if nome in self.telas:
            xml = self.telas[nome]
        else:
            p = arquivo_tela(nome, self.tela, self.pasta_fixtures)
            if not p.exists():
                raise FileNotFoundError(f"tela '{nome}' sem fixture: {p}")
            xml = p.read_text(encoding="utf-8")
        if nome == "perfil" and self.conta != "hpgta6":
            xml = xml.replace("hpgta6", self.conta)
        return xml

    def nos_tela(self, nome: str | None = None) -> list:
        return sd.parse_dump(self.xml_tela(nome))

    def no_em(self, x: int, y: int):
        """O menor nó clicável que contém (x, y) na tela atual (ou None)."""
        cands = [n for n in self.nos_tela() if n.clicavel and n.contem_ponto(x, y)]
        return min(cands, key=lambda n: n.area) if cands else None

    def ir_para(self, nome: str) -> None:
        if nome != self.tela_atual:
            self.pilha.append(self.tela_atual)
            self.tela_atual = nome

    def _seguir(self, no) -> None:
        if no is None:
            return
        for chave in (no.id, no.texto, no.desc):
            dest = self.transicoes.get((self.tela_atual, chave)) if chave else None
            if dest is None:
                continue
            if callable(dest):
                dest = dest(self, no)
            if dest:
                self.ir_para(dest)
            return

    # -- o runner --------------------------------------------------------------------
    def __call__(self, argv) -> tuple:
        argv = [str(a) for a in argv]
        self.comandos.append(argv)
        resto = argv[1:]
        if resto[:1] == ["-s"]:
            resto = resto[2:]
        texto = " ".join(resto)
        for trecho, resp in self.falha_em.items():
            if trecho in texto:
                return resp
        if not resto:
            return (1, "adb: sem comando")
        sub = resto[0]
        if sub == "devices":
            return (0, "List of devices attached\n" + "".join(f"{s}\t{e}\n" for s, e in self.dispositivos))
        if sub == "push":
            local, remoto = resto[1], resto[2]
            self.pushados.append((local, remoto))
            self.ultimo_push_nome = remoto.rsplit("/", 1)[-1]
            if not Path(local).is_file():
                return (1, f"adb: error: cannot stat '{local}': No such file or directory")
            return (0, f"{local}: 1 file pushed, 0 skipped.")
        if sub == "pull":
            remoto, local = resto[1], resto[2]
            self.pulls.append((remoto, local))
            Path(local).write_bytes(b"\x89PNG\r\n\x1a\nfalso")
            return (0, f"{remoto}: 1 file pulled, 0 skipped.")
        if sub == "shell":
            return self._shell(" ".join(resto[1:]))
        return (0, "")

    def _shell(self, linha: str) -> tuple:
        self.shell_cmds.append(linha)
        try:
            cmd = shlex.split(linha)
        except ValueError:
            cmd = linha.split()
        if not cmd:
            return (1, "")
        c0 = cmd[0]
        if c0 == "getprop":
            self.n_getprop += 1
            return (0, "1" if self.n_getprop > self.boot_apos else "")
        if c0 == "wm" and cmd[1:2] == ["size"]:
            out = f"Physical size: {self.tela[0]}x{self.tela[1]}\n"
            if self.override:
                out += f"Override size: {self.override[0]}x{self.override[1]}\n"
            return (0, out)
        if c0 == "wm" and cmd[1:2] == ["dismiss-keyguard"]:
            if not self.pin:
                self.travada = False
            return (0, "")
        if c0 == "dumpsys":
            if cmd[1:2] == ["power"]:
                return (0, f"POWER MANAGER (dumpsys power)\n  mWakefulness={'Awake' if self.acesa else 'Asleep'}\n"
                           "  mWakefulnessChanging=false\n")
            if cmd[1:2] == ["window"]:
                t = "true" if self.travada else "false"
                return (0, f"WINDOW MANAGER POLICY STATE (dumpsys window policy)\n  mShowingDream=false\n"
                           f"  mDreamingLockscreen={t}\n  mShowingLockscreen={t}\n  KeyguardServiceDelegate\n"
                           f"    showing={t}\n")
            if cmd[1:2] == ["activity"]:
                return (0, "ACTIVITY MANAGER ACTIVITIES (dumpsys activity activities)\n  Display #0\n"
                           f"    topResumedActivity=ActivityRecord{{1a2b3c u0 {self.app}/.activity.MainTabActivity t42}}\n"
                           f"    mResumedActivity: ActivityRecord{{1a2b3c u0 {self.app}/.activity.MainTabActivity t42}}\n")
            return (0, "")
        if c0 == "uiautomator":
            self.n_dump += 1
            if self.falhas_dump > 0:
                self.falhas_dump -= 1
                return (0, "ERROR: could not get idle state.")
            self.ultimo_xml = self.xml_tela()
            self.dump_gravado = True
            return (0, f"UI hierchary dumped to: {cmd[-1]}")
        if c0 == "cat":
            if not self.dump_gravado:
                return (1, f"cat: {cmd[-1]}: No such file or directory")
            if self.cat_cortado > 0:
                self.cat_cortado -= 1
                return (0, self.ultimo_xml[: len(self.ultimo_xml) // 2])
            return (0, self.ultimo_xml)
        if c0 == "input":
            return self._input(cmd[1:])
        if c0 == "am":
            if cmd[1:2] == ["start"]:
                self.abertos.append(" ".join(cmd))
                if "-d" in cmd and self.link_abre:
                    self.ir_para(self.link_abre)
                return (0, "Starting: Intent { act=android.intent.action.VIEW }")
            if cmd[1:2] == ["broadcast"]:
                self.broadcasts.append(" ".join(cmd))
                if "MEDIA_SCANNER_SCAN_FILE" in linha:
                    self.scans.append("B")
                    self._indexar("B", linha.rsplit("/", 1)[-1])
                return (0, "Broadcast completed: result=0")
            if cmd[1:2] == ["force-stop"]:
                return (0, "")
            return (0, "")
        if c0 == "content":
            if cmd[1:2] == ["call"]:
                metodo = cmd[cmd.index("--method") + 1] if "--method" in cmd else "?"
                arg = cmd[cmd.index("--arg") + 1] if "--arg" in cmd else ""
                plano = "principal" if metodo == "scan_file" else ("C" if metodo == "scan_volume" else metodo)
                self.scans.append(plano)
                # scan_volume varre a memória toda: indexa o último arquivo empurrado
                self._indexar(plano, self.ultimo_push_nome if metodo == "scan_volume" else arg.rsplit("/", 1)[-1])
                return (0, "Result: Bundle[{android.intent.extra.STREAM=content://media/external/images/media/77}]")
            if cmd[1:2] == ["query"]:
                m = re.search(r"_display_name='([^']+)'", linha)
                nome = m.group(1) if m else ""
                if nome in self.indexados:
                    return (0, f"Row: 0 _display_name={nome}\n")
                return (0, "No result found.\n")
            return (0, "")
        if c0 == "monkey":
            self.abertos.append(" ".join(cmd))
            return (0, "Events injected: 1")
        if c0 == "mkdir":
            return (0, "")
        if c0 == "screencap":
            return (0, "")
        if c0 == "ime":
            return (0, (IME_GBOARD + "\n" + (sd.TECLADO_ADB + "\n" if self.teclado_adb else "")))
        if c0 == "settings":
            return (0, (sd.TECLADO_ADB if self.teclado_adb else IME_GBOARD) + "\n")
        return (0, "")

    def _indexar(self, plano: str, nome: str) -> None:
        if self.indexa_em is not None and plano == self.indexa_em:
            self.indexados.add(nome)
        elif self.indexa_em == "qualquer":
            self.indexados.add(nome)

    def _input(self, cmd: list) -> tuple:
        if not cmd:
            return (1, "usage: input ...")
        verbo = cmd[0]
        if verbo == "tap":
            x, y = int(cmd[1]), int(cmd[2])
            no = self.no_em(x, y)
            self.toques.append((x, y, (no.id or no.texto or no.desc) if no else None))
            self._seguir(no)
            return (0, "")
        if verbo == "swipe":
            self.swipes.append(tuple(int(v) for v in cmd[1:6]))
            return (0, "")
        if verbo == "keyevent":
            for k in cmd[1:]:
                self.teclas.append(k)
                if k in ("224", "KEYCODE_WAKEUP"):
                    self.acesa = True
                if k in ("4", "KEYCODE_BACK") and self.pilha:
                    self.tela_atual = self.pilha.pop()
            return (0, "")
        if verbo == "text":
            self.digitados.append(" ".join(cmd[1:]).replace("%s", " "))
            return (0, "")
        if verbo == "keycombination":
            self.teclas.append("+".join(cmd[1:]))
            return (0, "")
        return (0, "")

    # -- atalhos para os testes ---------------------------------------------------------
    def taps(self) -> list:
        return [(x, y) for x, y, _ in self.toques]

    def comandos_shell(self) -> list:
        return list(self.shell_cmds)


if __name__ == "__main__":
    for p in gerar_fixtures():
        print("gravado:", p)
