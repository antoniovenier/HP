# -*- coding: utf-8 -*-
"""story_post.py — story clicável pelo emulador Android (app oficial do Instagram).

Comandos (passo a passo leigo em LEIA_story_post.md):
  python scripts\\story_post.py fila [--uma-vez] [--simular]
  python scripts\\story_post.py post <post_id> [--simular]
  python scripts\\story_post.py enquete --dia 2026-09-30 [--cortar] [--simular]
  python scripts\\story_post.py contagem [--dia D] [--arte ARQ] [--titulo T] [--data AAAA-MM-DD]
  python scripts\\story_post.py status
  python scripts\\story_post.py config

Fluxo do story de post (cada passo é uma função; toda espera lê a tela pelo
uiautomator e tem prazo — nada de "dormir e torcer"):
  1 liga o emulador (ligar_emulador.ps1, boot frio) e espera sys.boot_completed=1
  2 abre o Instagram
  3 troca para a conta do canal e CONFERE o @ ativo (não bateu: aborta)
  4 abre o post pelo link (plano B: grade do perfil, conferindo o título)
  5 Enviar -> Adicionar ao story -> Seu story
  6 destaque (se pedido): abre o próprio story, avança até o de agora, Destaque
  7 story_clicavel.py feito <post_id> --link <url> e desliga o emulador
    (desliga SEMPRE, mesmo em erro)

Segurança: para ao primeiro aviso da Meta (grava PARADO_AVISO_META.json; nada
sai enquanto ele existir), nunca digita senha/código, nunca toca em
login/termos/permissões, 1 story por post, intervalo mínimo entre stories,
orçamento de tempo por story (padrão 5 min).
"""
from __future__ import annotations

import argparse
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import unicodedata
import xml.etree.ElementTree as ET
from contextlib import nullcontext
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Callable

AQUI = Path(__file__).resolve().parent


def _achar_hp_studio() -> Path | None:
    """Acha a pasta hp_studio (onde está o pacote hpbase)."""
    cands = []
    env = os.environ.get("HP_APP")
    if env:
        cands += [Path(env), Path(env) / "hp_studio_nuvem", Path(env) / "hp_studio"]
    cands += [AQUI.parent / "app" / "hp_studio_nuvem",           # repositório (rodada 2)
              AQUI.parent / "06 Projeto" / "app" / "hp_studio_nuvem",  # PC (pacote irmão)
              Path(r"G:\Meu Drive\Hypado\06 Projeto\app\hp_studio_nuvem"),
              AQUI.parent / "app" / "hp_studio",                 # repositório (rodada 1)
              AQUI.parent / "06 Projeto" / "app" / "hp_studio",  # Drive
              Path(r"G:\Meu Drive\Hypado\06 Projeto\app\hp_studio")]
    for c in cands:
        if (c / "hpbase" / "__init__.py").exists():
            return c
    return None


_HP = _achar_hp_studio()
if _HP and str(_HP) not in sys.path:
    sys.path.insert(0, str(_HP))
if str(AQUI) not in sys.path:
    sys.path.insert(0, str(AQUI))

from hpbase import (FUSO, TravaOcupada, TravaPesada, agora, anexar_linha,  # noqa: E402
                    escrever_json, garantir, ler_json, mascarar, obter_logger,
                    raiz_drive, raiz_local, rodar)
import story_post_seletores as SEL  # noqa: E402

PACOTE = SEL.PACOTE

# códigos de saída
OK, ERRO, BLOQUEADO, AVISO_META = 0, 1, 2, 3

CONFIG_PADRAO = {
    # canal -> @ da conta no Instagram (os 6 perfis)
    "contas": {
        "gta": "hpgta6", "futebol": "hp.futebol", "filmes": "hp.filmes",
        "receitas": "hp.receitas", "carros": "hp.carros",
        "destinos": "hp.destinos",
    },
    "intervalo_min_seg": 180,          # mínimo entre dois stories (qualquer conta)
    "orcamento_seg": 300,              # tempo máximo de um story (inclui o boot)
    "max_tentativas": 3,               # depois disso o post sai da fila automática
    "timeout_elemento_seg": 20,
    "timeout_abrir_app_seg": 45,
    "timeout_post_seg": 30,
    "timeout_editor_seg": 30,
    "timeout_publicar_seg": 30,
    "timeout_upload_seg": 60,
    "timeout_boot_seg": 180,
    "timeout_script_ligar_seg": 150,
    "intervalo_leitura_seg": 1.0,      # entre duas leituras da tela
    "pausa_toque_seg": 0.6,            # depois de cada toque (e depois espera o elemento)
    "recente_max_min": 2,              # story "de agora" = até 2 min
    "max_stories_avancar": 40,
    "toque_avancar": [0.92, 0.3],      # onde tocar para passar o story (fração da tela)
    "serial": None,                    # ex.: "emulator-5554" (só se houver 2 aparelhos)
    "adb": None,                       # caminho do adb.exe (ou env HP_ADB)
    "android": None,                   # pasta H:\HypadoLocal\android
    "python": None,                    # padrão: o mesmo Python deste script
    "story_clicavel": None,            # padrão: story_clicavel.py ao lado deste script
    "digitar_cmd": ["{python}", "{script}", "{texto}"],
    "pastas_lotes": None,              # padrão: <Drive>\lotes e H:\HypadoLocal\lotes
    "limite_pergunta": 25,
    "limite_opcao": 25,
    "cortar_pergunta": False,
    "enquete_canal": "gta",
    "destaque_enquetes": "Enquetes",
    "caixa_enquete": [540, 1500],      # onde soltar a enquete (px da tela ou fração 0-1)
    "origem_adesivo": [0.5, 0.5],      # onde a figurinha aparece depois do Concluir
    "arrastar_modo": "swipe",          # "swipe" ou "draganddrop"
    "arrastar_ms": 1200,
    "contagem": {
        "canal": "gta", "titulo": "Lançamento do GTA 6", "data": "2026-11-19",
        "arte": None, "destaque": None, "caixa": None, "limite_titulo": 30,
    },
    "seletores": {},                   # {"ids": {...}, "textos": {...}} sobrepõe o padrão
    "avisos_meta_extra": [],
}


# ===========================================================================
# Erros
# ===========================================================================
class StoryErro(Exception):
    """Erro do story_post (a mensagem é em português e vai para o log)."""


class ElementoNaoApareceu(StoryErro):
    pass


class ContaErrada(StoryErro):
    pass


class OrcamentoEstourado(StoryErro):
    pass


class EmuladorNaoLigou(StoryErro):
    pass


class AdbErro(StoryErro):
    pass


class DadosInvalidos(StoryErro):
    pass


class PerguntaLonga(DadosInvalidos):
    pass


class AvisoMeta(StoryErro):
    """Tela com aviso da Meta / login / termos: para TUDO e grava a parada."""

    def __init__(self, frase: str, trecho: str = ""):
        super().__init__(f"aviso na tela: '{frase}'")
        self.frase = frase
        self.trecho = trecho


class TelaProibida(AvisoMeta):
    """Ia tocar/digitar em login, senha, código ou termos."""


# ===========================================================================
# Texto
# ===========================================================================
def normalizar(s) -> str:
    """minúsculas, sem acento, espaços simples (para comparar textos da tela)."""
    s = unicodedata.normalize("NFKD", str(s or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("\u2019", "'").replace("\u2018", "'").replace("\xa0", " ")
    return re.sub(r"\s+", " ", s.casefold()).strip()


def limpar_handle(s) -> str:
    """'@HP.Futebol ' -> 'hp.futebol' (só letras, números, ponto e _)."""
    t = normalizar(s).lstrip("@")
    m = re.match(r"[a-z0-9._]+", t)
    return m.group(0).rstrip(".") if m else ""


def _lista(v) -> list | None:
    if v is None:
        return None
    if isinstance(v, (list, tuple, set)):
        return [x for x in v]
    return [v]


def _txt(b) -> str:
    if b is None:
        return ""
    if isinstance(b, bytes):
        return b.decode("utf-8", errors="replace")
    return str(b)


# ===========================================================================
# Nós da tela (dump do uiautomator)
# ===========================================================================
_RX_BOUNDS = re.compile(r"\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]")


def ler_bounds(s: str | None) -> tuple | None:
    """'[0,100][1080,300]' -> (0, 100, 1080, 300)."""
    m = _RX_BOUNDS.search(s or "")
    return tuple(int(g) for g in m.groups()) if m else None


def centro(b: tuple) -> tuple:
    return ((b[0] + b[2]) // 2, (b[1] + b[3]) // 2)


@dataclass(frozen=True)
class No:
    rid: str = ""
    texto: str = ""
    desc: str = ""
    classe: str = ""
    pacote: str = ""
    bounds: tuple = (0, 0, 0, 0)
    clicavel: bool = False
    focado: bool = False
    senha: bool = False
    selecionado: bool = False
    marcado: bool = False
    habilitado: bool = True

    @property
    def id_curto(self) -> str:
        return self.rid.split(":id/", 1)[1] if ":id/" in self.rid else self.rid

    @property
    def centro(self) -> tuple:
        return centro(self.bounds)

    @property
    def area(self) -> int:
        return max(0, self.bounds[2] - self.bounds[0]) * max(0, self.bounds[3] - self.bounds[1])

    @property
    def rotulo(self) -> str:
        return self.texto or self.desc

    def contem(self, x: int, y: int) -> bool:
        b = self.bounds
        return b[0] <= x < b[2] and b[1] <= y < b[3]

    def dentro_de(self, outro: "No") -> bool:
        a, b = self.bounds, outro.bounds
        return a[0] >= b[0] and a[1] >= b[1] and a[2] <= b[2] and a[3] <= b[3]


def parse_xml(xml: str) -> list[No]:
    """Transforma o XML do `uiautomator dump` numa lista de nós (ordem do XML).

    Aceita lixo antes/depois (ex.: "UI hierchary dumped to: /dev/tty").
    XML vazio, cortado ou inválido devolve [] (quem espera tenta de novo).
    """
    if not xml:
        return []
    i = xml.find("<?xml")
    if i < 0:
        i = xml.find("<hierarchy")
    j = xml.rfind("</hierarchy>")
    if i < 0 or j < 0:
        return []
    try:
        raiz = ET.fromstring(xml[i:j + len("</hierarchy>")].encode("utf-8"))
    except ET.ParseError:
        return []
    nos = []
    for el in raiz.iter("node"):
        b = ler_bounds(el.get("bounds"))
        if b is None:
            continue
        a = el.get
        nos.append(No(
            rid=a("resource-id", "") or "", texto=a("text", "") or "",
            desc=a("content-desc", "") or "", classe=a("class", "") or "",
            pacote=a("package", "") or "", bounds=b,
            clicavel=a("clickable") == "true", focado=a("focused") == "true",
            senha=a("password") == "true", selecionado=a("selected") == "true",
            marcado=a("checked") == "true",
            habilitado=(a("enabled", "true") or "true") == "true"))
    return nos


def _casa_id(no: No, ids: list) -> bool:
    for i in ids:
        if not i:
            continue
        if no.rid == i or no.rid.endswith(":id/" + i):
            return True
    return False


def _casa_texto(valor: str, alternativas: list, parcial: bool) -> bool:
    v = normalizar(valor)
    if not v:
        return False
    for a in alternativas:
        a = normalizar(a)
        if a and ((a in v) if parcial else (v == a)):
            return True
    return False


def filtrar(nos: list[No], id=None, texto=None, desc=None, rotulo=None,
            parcial: bool = False, visivel: bool = True) -> list[No]:
    """Nós que batem com TODOS os critérios dados (cada um aceita alternativas).

    id: resource-id (curto ou completo); texto: atributo text; desc:
    content-desc; rotulo: text OU content-desc. parcial=True compara por "contém".
    """
    ids, txs, dss, rts = _lista(id), _lista(texto), _lista(desc), _lista(rotulo)
    saida = []
    for n in nos:
        if visivel and n.area <= 0:
            continue
        if ids is not None and not _casa_id(n, ids):
            continue
        if txs is not None and not _casa_texto(n.texto, txs, parcial):
            continue
        if dss is not None and not _casa_texto(n.desc, dss, parcial):
            continue
        if rts is not None and not (_casa_texto(n.texto, rts, parcial)
                                    or _casa_texto(n.desc, rts, parcial)):
            continue
        saida.append(n)
    return saida


def escolher_no(nos: list[No], modo: str = "primeiro") -> No:
    if modo == "topo":
        return min(nos, key=lambda n: (n.bounds[1], n.bounds[0]))
    if modo == "ultimo":
        return nos[-1]
    return nos[0]


def descrever(crit: dict) -> str:
    partes = []
    for k in ("id", "texto", "desc", "rotulo"):
        v = crit.get(k)
        if v:
            v = _lista(v)
            partes.append(f"{k}=" + "|".join(str(x) for x in v[:3]))
    return " ".join(partes) or "?"


def tamanho_tela(nos: list[No]) -> tuple:
    if not nos:
        return (1080, 1920)
    return (max(n.bounds[2] for n in nos), max(n.bounds[3] for n in nos))


def _coord(v, total: int) -> int:
    """Número <= 1 com ponto (0.5) é fração da tela; senão é pixel."""
    if isinstance(v, float) and 0 <= v <= 1:
        return int(round(v * total))
    return int(v)


# ===========================================================================
# Seletores (padrão do story_post_seletores.py + ajustes do config)
# ===========================================================================
class Seletores:
    def __init__(self, extra: dict | None = None, avisos_extra: list | None = None):
        extra = extra or {}
        self.ids = {k: list(v) for k, v in SEL.IDS.items()}
        self.textos = {k: list(v) for k, v in SEL.TEXTOS.items()}
        for k, v in (extra.get("ids") or {}).items():
            self.ids[k] = _lista(v)
        for k, v in (extra.get("textos") or {}).items():
            self.textos[k] = _lista(v)
        self.avisos = [normalizar(a) for a in list(SEL.AVISOS_META) + list(avisos_extra or [])]
        self.avisos_palavras = [re.compile(r"(?<![a-z0-9])" + re.escape(normalizar(a)))
                                for a in SEL.AVISOS_META_PALAVRAS]
        self.proibido_exato = {normalizar(x) for x in SEL.PROIBIDO_TOCAR_EXATO}
        self.proibido_contem = [normalizar(x) for x in SEL.PROIBIDO_TOCAR_CONTEM]
        self.popups = [normalizar(x) for x in SEL.POPUPS_DISPENSAVEIS]
        self.ignorar_aviso = set(SEL.IDS_CONTEUDO_IGNORAR_AVISO)
        self.agora = {normalizar(x) for x in SEL.TIMESTAMP_AGORA}

    def id(self, chave: str) -> list:
        return self.ids[chave]

    def txt(self, chave: str) -> list:
        return self.textos[chave]


def detectar_aviso(nos: list[No], sel: Seletores) -> tuple | None:
    """(frase, trecho) se a tela tem aviso da Meta, login ou termos; senão None.

    Frases valem no texto e na descrição; palavras soltas ("suspeita"...) só no
    texto visível. Legenda, grade, fotos e campos de digitação não contam.
    """
    for n in nos:
        if n.senha:
            return ("campo de senha (tela de login)", n.rotulo[:300])
        if n.id_curto in sel.ignorar_aviso or n.classe.endswith("EditText"):
            continue
        for campo, e_texto in ((n.texto, True), (n.desc, False)):
            if not campo:
                continue
            t = normalizar(campo)
            for a in sel.avisos:
                if a and a in t:
                    return (a, campo[:300])
            if e_texto:
                for rx in sel.avisos_palavras:
                    m = rx.search(t)
                    if m:
                        return (m.group(0), campo[:300])
    return None


def toque_proibido(no: No, sel: Seletores) -> bool:
    for campo in (no.texto, no.desc):
        t = normalizar(campo)
        if not t:
            continue
        if t in sel.proibido_exato or any(p in t for p in sel.proibido_contem):
            return True
    return False


# ===========================================================================
# Relógio e orçamento de tempo (injetáveis nos testes)
# ===========================================================================
class Relogio:
    def monotonic(self) -> float:
        return time.monotonic()

    def dormir(self, seg: float) -> None:
        if seg > 0:
            time.sleep(seg)

    def agora(self) -> datetime:
        return agora()


class Orcamento:
    """Tempo máximo de um story. Estourou -> OrcamentoEstourado."""

    def __init__(self, limite_seg: float, relogio: Relogio):
        self.limite = float(limite_seg)
        self.relogio = relogio
        self.inicio = relogio.monotonic()

    def gasto(self) -> float:
        return self.relogio.monotonic() - self.inicio

    def restante(self) -> float:
        return self.limite - self.gasto()

    def verificar(self, onde: str = "") -> None:
        if self.gasto() > self.limite:
            raise OrcamentoEstourado(
                f"orçamento de {self.limite:.0f}s estourado ({self.gasto():.0f}s)"
                + (f" em '{onde}'" if onde else ""))


# ===========================================================================
# adb
# ===========================================================================
def achar_adb(cfg: dict | None = None) -> str | None:
    """HP_ADB > config "adb" > H:\\HypadoLocal\\android\\sdk\\platform-tools > PATH."""
    cands = []
    for v in (os.environ.get("HP_ADB"), (cfg or {}).get("adb")):
        if v:
            cands.append(Path(v))
    sdk = raiz_local() / "android" / "sdk"
    cands += [sdk / "platform-tools" / "adb.exe", sdk / "platform-tools" / "adb"]
    for c in cands:
        if c.is_file():
            return str(c)
    if sdk.is_dir():
        for padrao in ("*/platform-tools/adb.exe", "*/*/platform-tools/adb.exe",
                       "*/platform-tools/adb"):
            achados = sorted(sdk.glob(padrao))
            if achados:
                return str(achados[0])
    return shutil.which("adb")


class Adb:
    """Comandos do adb. Tudo passa por `rodar_fn` (hpbase.rodar, sem janela)."""

    def __init__(self, exe: str, serial: str | None = None,
                 rodar_fn: Callable | None = None, log=None,
                 arquivo_dump: str = "/sdcard/hp_ui.xml", timeout: float = 60):
        self.exe = exe
        self.serial = serial
        self.rodar_fn = rodar_fn or rodar
        self.log = log
        self.arquivo_dump = arquivo_dump
        self.timeout = timeout
        self.ultimo_xml = ""

    def _cmd(self, *args) -> list:
        base = [self.exe] + (["-s", self.serial] if self.serial else [])
        return base + [str(a) for a in args]

    def executar(self, *args, timeout: float | None = None) -> subprocess.CompletedProcess:
        try:
            return self.rodar_fn(self._cmd(*args), timeout=timeout or self.timeout)
        except subprocess.TimeoutExpired as e:
            raise AdbErro(f"adb demorou demais: {' '.join(str(a) for a in args)[:80]}") from e

    def shell(self, comando: str, timeout: float | None = None) -> str:
        r = self.executar("shell", comando, timeout=timeout)
        return _txt(r.stdout).strip()

    def boot_completo(self) -> bool:
        try:
            r = self.executar("shell", "getprop sys.boot_completed", timeout=20)
        except AdbErro:
            return False
        return r.returncode == 0 and _txt(r.stdout).strip() == "1"

    def dump_xml(self) -> str:
        """Um comando só: apaga o dump velho, gera outro e mostra (sem tela velha)."""
        f = self.arquivo_dump
        try:
            r = self.executar(
                "shell", f"rm -f {f}; uiautomator dump {f} >/dev/null 2>&1; cat {f}",
                timeout=40)
        except AdbErro:
            return ""
        self.ultimo_xml = _txt(r.stdout)
        return self.ultimo_xml

    def dump_ui(self) -> list[No]:
        return parse_xml(self.dump_xml())

    def tocar(self, x: int, y: int) -> None:
        self.shell(f"input tap {int(x)} {int(y)}")

    def arrastar(self, x1, y1, x2, y2, ms: int = 1200, modo: str = "swipe") -> None:
        verbo = "draganddrop" if modo == "draganddrop" else "swipe"
        self.shell(f"input {verbo} {int(x1)} {int(y1)} {int(x2)} {int(y2)} {int(ms)}")

    def tecla(self, codigo) -> None:
        self.shell(f"input keyevent {codigo}")

    def apagar(self, n: int = 30) -> None:
        self.shell("input keyevent " + " ".join(["67"] * n))

    def texto(self, txt: str) -> None:
        """Só ASCII simples (acentos vão pelo digitar.py)."""
        self.shell("input text " + shlex.quote(txt.replace(" ", "%s")))

    def abrir_app(self, pacote: str = PACOTE) -> None:
        self.shell(f"monkey -p {pacote} -c android.intent.category.LAUNCHER 1")

    def fechar_app(self, pacote: str = PACOTE) -> None:
        self.shell(f"am force-stop {pacote}")

    def abrir_link(self, link: str, pacote: str = PACOTE) -> None:
        self.shell(f"am start -a android.intent.action.VIEW -d {shlex.quote(link)} {pacote}")

    def push(self, local: Path, remoto: str) -> None:
        r = self.executar("push", str(local), remoto, timeout=180)
        if r.returncode != 0:
            raise AdbErro(f"adb push falhou: {mascarar(_txt(r.stderr))[:200]}")

    def escanear_midia(self, remoto: str) -> None:
        self.shell("am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE "
                   f"-d file://{remoto}")

    def midia_indexada(self, nome: str) -> bool:
        out = self.shell("content query --uri content://media/external/images/media "
                         f"--projection _display_name --where \"_display_name='{nome}'\"")
        return nome in out

    def screencap(self) -> bytes:
        r = self.executar("exec-out", "screencap -p", timeout=30)
        return r.stdout if isinstance(r.stdout, bytes) else b""

    def emu_kill(self) -> None:
        self.executar("emu", "kill", timeout=30)


# ===========================================================================
# Digitação (acentos pelo android\digitar.py que já existe)
# ===========================================================================
_ASCII_SEGURO = re.compile(r"[A-Za-z0-9 .,!?:\-]+")


class Digitador:
    def __init__(self, adb: Adb, rodar_fn: Callable, script: Path, python_exe: str,
                 modelo: list | None = None, verificar_arquivo: bool = True):
        self.adb = adb
        self.rodar_fn = rodar_fn
        self.script = Path(script)
        self.python = python_exe
        self.modelo = modelo or ["{python}", "{script}", "{texto}"]
        self.verificar_arquivo = verificar_arquivo

    def digitar(self, texto: str) -> None:
        if not texto:
            return
        if _ASCII_SEGURO.fullmatch(texto):
            self.adb.texto(texto)
            return
        if self.verificar_arquivo and not self.script.exists():
            raise StoryErro(f"não achei {self.script} (precisa dele para acentos)")
        cmd = [p.format(python=self.python, script=str(self.script), texto=texto)
               for p in self.modelo]
        try:
            r = self.rodar_fn(cmd, timeout=90)
        except subprocess.TimeoutExpired as e:
            raise StoryErro("digitar.py demorou demais") from e
        if r.returncode != 0:
            raise StoryErro(f"digitar.py falhou: {mascarar(_txt(r.stderr))[:200]}")


# ===========================================================================
# Tela: achar / esperar / tocar (sempre lendo o dump; com prazo)
# ===========================================================================
class Tela:
    def __init__(self, adb: Adb, relogio: Relogio, sel: Seletores, log,
                 intervalo: float = 1.0, timeout_padrao: float = 20.0,
                 pausa_toque: float = 0.6, digitador: Digitador | None = None,
                 saida: Callable = print):
        self.adb = adb
        self.relogio = relogio
        self.sel = sel
        self.log = log
        self.intervalo = intervalo
        self.timeout_padrao = timeout_padrao
        self.pausa_toque = pausa_toque
        self.digitador = digitador
        self.saida = saida
        self.orcamento: Orcamento | None = None
        self.ultimos_nos: list[No] = []

    # -- leitura ------------------------------------------------------------
    def ler(self) -> list[No]:
        """Lê a tela; para na hora se houver aviso da Meta ou tempo estourado."""
        if self.orcamento:
            self.orcamento.verificar("lendo a tela")
        nos = self.adb.dump_ui()
        self.ultimos_nos = nos
        aviso = detectar_aviso(nos, self.sel)
        if aviso:
            raise AvisoMeta(*aviso)
        return nos

    def achar(self, nos: list[No] | None = None, escolher: str = "primeiro",
              **crit) -> No | None:
        nos = self.ler() if nos is None else nos
        lst = filtrar(nos, **crit)
        return escolher_no(lst, escolher) if lst else None

    def achar_todos(self, nos: list[No] | None = None, **crit) -> list[No]:
        nos = self.ler() if nos is None else nos
        return filtrar(nos, **crit)

    def _popup(self, nos: list[No]) -> No | None:
        for n in nos:
            if n.area > 0 and normalizar(n.rotulo) in self.sel.popups:
                return n
        return None

    def _prazo(self, timeout: float | None) -> float:
        return self.relogio.monotonic() + (self.timeout_padrao if timeout is None else timeout)

    def esperar_qualquer(self, alternativas: list[dict], timeout: float | None = None,
                         escolher: str = "primeiro", fechar_popups: bool = True) -> No:
        """Espera até aparecer um nó que bata com alguma das alternativas."""
        fim = self._prazo(timeout)
        popups = 0
        while True:
            nos = self.ler()
            for crit in alternativas:
                lst = filtrar(nos, **crit)
                if lst:
                    return escolher_no(lst, escolher)
            if fechar_popups and popups < 3:
                p = self._popup(nos)
                if p:
                    popups += 1
                    self.log.info("fechando pop-up '%s'", p.rotulo)
                    self._tap(p)
                    continue
            if self.relogio.monotonic() >= fim:
                raise ElementoNaoApareceu(
                    "não apareceu: " + " ou ".join(descrever(c) for c in alternativas))
            self.relogio.dormir(self.intervalo)

    def esperar(self, timeout: float | None = None, escolher: str = "primeiro",
                fechar_popups: bool = True, **crit) -> No:
        return self.esperar_qualquer([crit], timeout, escolher, fechar_popups)

    def esperar_condicao(self, func: Callable, descricao: str,
                         timeout: float | None = None, simulado=True,
                         levantar: bool = True):
        """Espera func(nós) devolver algo verdadeiro (e devolve esse algo)."""
        fim = self._prazo(timeout)
        while True:
            nos = self.ler()
            r = func(nos)
            if r:
                return r
            if self.relogio.monotonic() >= fim:
                if levantar:
                    raise ElementoNaoApareceu(f"não aconteceu: {descricao}")
                return None
            self.relogio.dormir(self.intervalo)

    def esperar_sumir(self, timeout: float | None = None, levantar: bool = True,
                      **crit) -> bool:
        fim = self._prazo(timeout)
        popups = 0
        while True:
            nos = self.ler()
            if not filtrar(nos, **crit):
                return True
            p = self._popup(nos)
            if p and popups < 3:
                popups += 1
                self.log.info("fechando pop-up '%s'", p.rotulo)
                self._tap(p)
                continue
            if self.relogio.monotonic() >= fim:
                if levantar:
                    raise ElementoNaoApareceu(f"não sumiu: {descrever(crit)}")
                return False
            self.relogio.dormir(self.intervalo)

    # -- ações --------------------------------------------------------------
    def _tap(self, no: No) -> None:
        if toque_proibido(no, self.sel):
            raise TelaProibida(f"botão proibido '{no.rotulo}'", no.rotulo)
        x, y = no.centro
        self.adb.tocar(x, y)
        self.relogio.dormir(self.pausa_toque)

    def tocar(self, no: No | None = None, *, motivo: str = "",
              timeout: float | None = None, escolher: str = "primeiro", **crit) -> No:
        if no is None:
            no = self.esperar(timeout=timeout, escolher=escolher, **crit)
        if no.area <= 0:
            raise ElementoNaoApareceu(f"elemento invisível: {motivo or descrever(crit)}")
        self.log.info("tocar %s em %s", motivo or descrever(crit) or no.rotulo, no.centro)
        self._tap(no)
        return no

    def tocar_qualquer(self, alternativas: list[dict], motivo: str = "",
                       timeout: float | None = None) -> No:
        no = self.esperar_qualquer(alternativas, timeout)
        return self.tocar(no, motivo=motivo)

    def tocar_xy(self, x: int, y: int, motivo: str = "") -> None:
        self.log.info("tocar (%s,%s) %s", x, y, motivo)
        self.adb.tocar(x, y)
        self.relogio.dormir(self.pausa_toque)

    def digitar(self, texto: str) -> None:
        nos = self.ler()
        if any(n.senha for n in nos):
            raise TelaProibida("campo de senha na tela", "")
        if not self.digitador:
            raise StoryErro("sem digitador configurado")
        self.log.info("digitar %d caracteres", len(texto))
        self.digitador.digitar(texto)
        self.relogio.dormir(self.pausa_toque)

    def voltar(self) -> None:
        self.adb.tecla(4)
        self.relogio.dormir(self.pausa_toque)

    def voltar_ate(self, max_voltas: int = 4, **crit) -> No:
        """Aperta VOLTAR até aparecer o elemento (ex.: as abas do app)."""
        for i in range(max_voltas + 1):
            no = self.achar(**crit)
            if no:
                return no
            if i < max_voltas:
                self.voltar()
        raise ElementoNaoApareceu(f"não voltei até {descrever(crit)}")

    def tamanho(self, nos: list[No] | None = None) -> tuple:
        return tamanho_tela(self.ultimos_nos if nos is None else nos)


class TelaRoteiro(Tela):
    """--simular: não lê tela nenhuma; imprime o roteiro do que faria."""

    def __init__(self, *a, respostas: dict | None = None, **kw):
        super().__init__(*a, **kw)
        self.respostas = respostas or {"reel_viewer_timestamp": "Agora"}

    @staticmethod
    def _sintetico(crit: dict | None = None) -> No:
        crit = crit or {}
        rot = (_lista(crit.get("rotulo")) or _lista(crit.get("texto"))
               or _lista(crit.get("desc")) or [""])[0]
        rid = (_lista(crit.get("id")) or [""])[0]
        return No(rid=rid, texto=str(rot), bounds=(0, 0, 1080, 1920))

    def ler(self) -> list[No]:
        if self.orcamento:
            self.orcamento.verificar("roteiro")
        return []

    def achar(self, nos=None, escolher="primeiro", **crit):
        for i in _lista(crit.get("id")) or []:
            if i in self.respostas:
                return No(rid=i, texto=self.respostas[i], bounds=(0, 0, 1080, 100))
        return None

    def achar_todos(self, nos=None, **crit):
        return []

    def esperar_qualquer(self, alternativas, timeout=None, escolher="primeiro",
                         fechar_popups=True):
        self.saida("  esperar " + " ou ".join(descrever(c) for c in alternativas))
        return self._sintetico(alternativas[0])

    def esperar_condicao(self, func, descricao, timeout=None, simulado=True,
                         levantar=True):
        self.saida(f"  esperar {descricao}")
        return simulado

    def esperar_sumir(self, timeout=None, levantar=True, **crit):
        self.saida(f"  esperar sumir {descrever(crit)}")
        return True

    def tocar(self, no=None, *, motivo="", timeout=None, escolher="primeiro", **crit):
        if no is None:
            no = self.esperar(**crit)
        self.saida(f"  tocar {motivo or descrever(crit) or no.rotulo or no.id_curto}")
        return no

    def tocar_xy(self, x, y, motivo=""):
        self.saida(f"  tocar ({x},{y}) {motivo}")

    def digitar(self, texto):
        self.saida(f"  digitar '{texto}'")

    def voltar(self):
        self.saida("  voltar")

    def voltar_ate(self, max_voltas=4, **crit):
        self.saida(f"  voltar até {descrever(crit)}")
        return self._sintetico(crit)


# ===========================================================================
# Emulador (ligar/desligar pelos .ps1 que já existem)
# ===========================================================================
class Emulador:
    def __init__(self, adb: Adb, rodar_fn: Callable, pasta_android: Path,
                 relogio: Relogio, log, cfg: dict, verificar_arquivos: bool = True):
        self.adb = adb
        self.rodar_fn = rodar_fn
        self.pasta = Path(pasta_android)
        self.relogio = relogio
        self.log = log
        self.cfg = cfg
        self.verificar_arquivos = verificar_arquivos

    def _ps(self, script: Path, timeout: float) -> subprocess.CompletedProcess:
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)]
        return self.rodar_fn(cmd, timeout=timeout)

    def ligar(self, orcamento: Orcamento | None = None) -> None:
        if self.adb.boot_completo():
            self.log.info("emulador já estava ligado; sigo com ele")
            return
        ps1 = self.pasta / "ligar_emulador.ps1"
        if self.verificar_arquivos and not ps1.exists():
            raise EmuladorNaoLigou(f"não achei {ps1}")
        lim = float(self.cfg["timeout_script_ligar_seg"])
        if orcamento:
            lim = max(5.0, min(lim, orcamento.restante()))
        try:
            r = self._ps(ps1, timeout=lim)
            if r.returncode != 0:
                self.log.warning("ligar_emulador.ps1 voltou %s: %s", r.returncode,
                                 mascarar(_txt(r.stderr))[:300])
        except subprocess.TimeoutExpired:
            self.log.info("ligar_emulador.ps1 não voltou em %.0fs; sigo esperando o boot", lim)
        self.esperar_boot(orcamento)

    def esperar_boot(self, orcamento: Orcamento | None = None) -> None:
        fim = self.relogio.monotonic() + float(self.cfg["timeout_boot_seg"])
        while True:
            if orcamento:
                orcamento.verificar("esperando o boot")
            if self.adb.boot_completo():
                self.log.info("boot completo")
                return
            if self.relogio.monotonic() >= fim:
                raise EmuladorNaoLigou("o emulador não terminou o boot a tempo")
            self.relogio.dormir(3)

    def preparar(self) -> None:
        """Acorda a tela e desliga as animações de janela (o dump fica estável)."""
        for c in ("input keyevent KEYCODE_WAKEUP", "wm dismiss-keyguard",
                  "settings put global window_animation_scale 0",
                  "settings put global transition_animation_scale 0"):
            try:
                self.adb.shell(c, timeout=20)
            except Exception as e:  # nada disso é essencial
                self.log.info("preparar: '%s' falhou (%s)", c, e)

    def desligar(self) -> None:
        """Nunca levanta erro (roda no finally)."""
        ps1 = self.pasta / "desligar_emulador.ps1"
        ok = False
        if ps1.exists() or not self.verificar_arquivos:
            try:
                ok = self._ps(ps1, timeout=120).returncode == 0
            except Exception as e:
                self.log.warning("desligar_emulador.ps1 falhou: %s", e)
        else:
            self.log.warning("não achei %s; vou pelo adb emu kill", ps1)
        if not ok:
            try:
                self.adb.emu_kill()
            except Exception as e:
                self.log.warning("adb emu kill falhou: %s", e)


# ===========================================================================
# Pastas, config e estado
# ===========================================================================
def pasta_emulador() -> Path:
    return raiz_local() / "emulador"


def pasta_fila() -> Path:
    return pasta_emulador() / "fila_story"


def arquivo_parado() -> Path:
    return pasta_emulador() / "PARADO_AVISO_META.json"


def arquivo_estado() -> Path:
    return pasta_emulador() / "story_post_estado.json"


def arquivo_config() -> Path:
    return pasta_emulador() / "story_post_config.json"


def arquivo_historico() -> Path:
    return pasta_emulador() / "story_post_historico.log"


def pasta_android(cfg: dict) -> Path:
    return Path(cfg.get("android") or (raiz_local() / "android"))


def carregar_config(caminho: Path | None = None) -> dict:
    cfg = {k: (dict(v) if isinstance(v, dict) else v) for k, v in CONFIG_PADRAO.items()}
    p = Path(caminho) if caminho else arquivo_config()
    dados = ler_json(p, {}) or {}
    if not isinstance(dados, dict):
        raise DadosInvalidos(f"{p} não é um objeto JSON")
    for k, v in dados.items():
        if k.startswith("_"):
            continue
        if isinstance(v, dict) and isinstance(cfg.get(k), dict):
            cfg[k].update(v)
        else:
            cfg[k] = v
    return cfg


def _estado_padrao() -> dict:
    return {"ultimo_story_em": None, "postados": {}, "tentativas": {},
            "falhas": []}


def ler_estado() -> dict:
    e = ler_json(arquivo_estado(), {}) or {}
    for k, v in _estado_padrao().items():
        e.setdefault(k, v)
    return e


def _parse_dt(v) -> datetime | None:
    if not v:
        return None
    try:
        d = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=FUSO)


def parado_existe() -> bool:
    return arquivo_parado().exists()


def resolver_conta(cfg: dict, item: dict, log=None) -> str:
    """Devolve o @ (sem @) da conta do item, pelo canal (config) e/ou 'conta'."""
    contas = {normalizar(k): limpar_handle(v) for k, v in (cfg.get("contas") or {}).items()}
    validas = set(contas.values())
    canal = normalizar(item.get("canal"))
    por_canal = None
    if canal:
        if canal in contas:
            por_canal = contas[canal]
        else:
            for k, v in contas.items():
                if re.search(rf"(^|[^a-z0-9]){re.escape(k)}", canal):
                    por_canal = v
                    break
    conta = limpar_handle(item.get("conta") or "")
    if conta and conta not in validas and normalizar(item.get("conta")) in contas:
        conta = contas[normalizar(item.get("conta"))]
    if conta and conta in validas:
        if por_canal and por_canal != conta:
            raise DadosInvalidos(f"conta @{conta} e canal '{item.get('canal')}' "
                                 f"(@{por_canal}) não batem")
        return conta
    if por_canal:
        if conta and log:
            log.warning("conta '%s' fora do mapa; uso @%s pelo canal", conta, por_canal)
        return por_canal
    raise DadosInvalidos(f"não sei a conta do item (conta='{item.get('conta')}', "
                         f"canal='{item.get('canal')}'); veja 'contas' no config")


def validar_link(link) -> str:
    link = str(link or "").strip()
    if not re.match(r"^https://(www\.)?instagram\.com/\S+$", link):
        raise DadosInvalidos(f"link inválido (tem que ser https://www.instagram.com/...): '{link}'")
    if any(c in link for c in "\"'`\\ "):
        raise DadosInvalidos("link com caractere estranho")
    return link


def minutos_do_timestamp(txt) -> float | None:
    """'Agora'->0, '1 min'->1, '1m'->1, '30 s'->0, 'há 2 min'->2, '3 h'->None."""
    t = normalizar(txt)
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"^ha\s+", "", t)
    t = re.sub(r"\s+(atras|ago)$", "", t).strip()
    if t in {normalizar(x) for x in SEL.TIMESTAMP_AGORA}:
        return 0.0
    if re.fullmatch(r"\d+\s*(s|seg|segs|segundo|segundos|sec|secs|second|seconds)", t):
        return 0.0
    m = re.fullmatch(r"(\d+)\s*(m|min|mins|minuto|minutos|minute|minutes)", t)
    if m:
        return float(m.group(1))
    return None


def validar_texto_curto(texto, limite: int, cortar: bool, nome: str) -> str:
    t = re.sub(r"\s+", " ", str(texto or "")).strip()
    if not t:
        raise DadosInvalidos(f"{nome} vazia")
    if len(t) <= limite:
        return t
    if not cortar:
        raise PerguntaLonga(f"{nome} tem {len(t)} caracteres (máximo {limite}): '{t}'. "
                            "Encurte no JSON ou rode com --cortar")
    corte = t[:limite]
    if t[limite] != " " and " " in corte:
        corte = corte.rsplit(" ", 1)[0]
    return corte.rstrip(" ,;:-")


# ===========================================================================
# Contexto de execução (tudo o que os passos usam; os testes trocam as peças)
# ===========================================================================
@dataclass
class Contexto:
    cfg: dict
    sel: Seletores
    adb: Adb
    tela: Tela
    emu: Emulador
    relogio: Relogio
    rodar_fn: Callable
    simular: bool
    log: object
    saida: Callable = print
    passo: str = ""
    orcamento: Orcamento | None = None
    estados_sessao: dict = field(default_factory=dict)

    def marcar(self, passo: str, checar: bool = True) -> None:
        self.passo = passo
        self.log.info("passo: %s", passo)
        if self.simular:
            self.saida(f"-> {passo}")
        if checar and self.orcamento:
            self.orcamento.verificar(passo)

    def novo_orcamento(self) -> Orcamento:
        self.orcamento = Orcamento(self.cfg["orcamento_seg"], self.relogio)
        self.tela.orcamento = self.orcamento
        return self.orcamento


def rodar_roteiro(saida: Callable) -> Callable:
    """rodar() falso do --simular: imprime o comando e não executa nada."""
    estado = {"ligado": False}

    def _citar(c: str) -> str:
        return f'"{c}"' if (" " in c or not c) else c

    def _r(cmd, timeout=None, entrada=None, cwd=None):
        cmd = [str(c) for c in cmd]
        texto = " ".join(_citar(c) for c in cmd)
        if "ligar_emulador.ps1" in texto and "desligar" not in texto:
            estado["ligado"] = True
        saida(f"  [simular] {texto}")
        out = b"1" if ("sys.boot_completed" in texto and estado["ligado"]) else b""
        return subprocess.CompletedProcess(cmd, 0, stdout=out, stderr=b"")
    return _r


def criar_contexto(cfg: dict | None = None, simular: bool = False,
                   rodar_fn: Callable | None = None, relogio: Relogio | None = None,
                   saida: Callable = print, adb_exe: str | None = None) -> Contexto:
    cfg = cfg if cfg is not None else carregar_config()
    relogio = relogio or Relogio()
    log = obter_logger("story_post")
    sel = Seletores(cfg.get("seletores"), cfg.get("avisos_meta_extra"))
    if simular:
        rodar_fn = rodar_roteiro(saida)
        exe = adb_exe or "adb"
    else:
        rodar_fn = rodar_fn or rodar
        exe = adb_exe or achar_adb(cfg)
        if not exe:
            raise StoryErro("não achei o adb.exe (defina HP_ADB ou 'adb' no config)")
    adb = Adb(exe, cfg.get("serial"), rodar_fn, log)
    android = pasta_android(cfg)
    dig = Digitador(adb, rodar_fn, android / "digitar.py",
                    cfg.get("python") or sys.executable, cfg.get("digitar_cmd"),
                    verificar_arquivo=not simular)
    cls = TelaRoteiro if simular else Tela
    tela = cls(adb, relogio, sel, log, intervalo=float(cfg["intervalo_leitura_seg"]),
               timeout_padrao=float(cfg["timeout_elemento_seg"]),
               pausa_toque=float(cfg["pausa_toque_seg"]), digitador=dig, saida=saida)
    emu = Emulador(adb, rodar_fn, android, relogio, log, cfg,
                   verificar_arquivos=not simular)
    return Contexto(cfg=cfg, sel=sel, adb=adb, tela=tela, emu=emu, relogio=relogio,
                    rodar_fn=rodar_fn, simular=simular, log=log, saida=saida)


# ---------------------------------------------------------------------------
# Estado local (intervalo, 1 story por post, falhas)
# ---------------------------------------------------------------------------
def _gravar_estado(ctx: Contexto, e: dict) -> None:
    if ctx.simular:
        return
    e["falhas"] = (e.get("falhas") or [])[-50:]
    escrever_json(arquivo_estado(), e)


def _historico(ctx: Contexto, texto: str) -> None:
    ctx.log.info(texto)
    if not ctx.simular:
        anexar_linha(arquivo_historico(), texto)


def falta_intervalo(ctx: Contexto) -> float:
    """Segundos que ainda faltam para poder soltar outro story (0 = liberado)."""
    ult = _parse_dt(ler_estado().get("ultimo_story_em"))
    if not ult:
        return 0.0
    passou = (ctx.relogio.agora() - ult).total_seconds()
    return max(0.0, float(ctx.cfg["intervalo_min_seg"]) - passou)


def registrar_tocado(ctx: Contexto, chave: str, handle: str, link: str | None) -> None:
    """Grava ANTES de tocar em "Seu story": nunca repetir o mesmo story."""
    ctx.estados_sessao[chave] = "tocado"
    e = ler_estado()
    e["postados"][chave] = {"estado": "tocado", "conta": handle, "link": link,
                            "quando": ctx.relogio.agora().isoformat(timespec="seconds"),
                            "feito": None}
    e["ultimo_story_em"] = ctx.relogio.agora().isoformat(timespec="seconds")
    _gravar_estado(ctx, e)


def registrar_publicado(ctx: Contexto, chave: str) -> None:
    ctx.estados_sessao[chave] = "publicado"
    e = ler_estado()
    if chave in e["postados"]:
        e["postados"][chave]["estado"] = "publicado"
        _gravar_estado(ctx, e)
    _historico(ctx, f"story publicado {chave}")


def registrar_falha(ctx: Contexto, chave: str, erro: Exception) -> None:
    e = ler_estado()
    if chave not in e["postados"]:
        e["tentativas"][chave] = int(e["tentativas"].get(chave, 0)) + 1
    e["falhas"].append({"quando": ctx.relogio.agora().isoformat(timespec="seconds"),
                        "story": chave, "passo": ctx.passo,
                        "erro": f"{type(erro).__name__}: {erro}"})
    _gravar_estado(ctx, e)
    _historico(ctx, f"FALHA {chave} no passo '{ctx.passo}': {type(erro).__name__}: {erro}")


def registrar_parado(ctx: Contexto, erro: AvisoMeta, chave: str, handle: str) -> None:
    dados = {
        "parado_em": ctx.relogio.agora().isoformat(timespec="seconds"),
        "motivo": erro.frase, "trecho_da_tela": (erro.trecho or "")[:300],
        "passo": ctx.passo, "story": chave, "conta": f"@{handle}",
        "o_que_fazer": [
            "Nenhum story sai enquanto este arquivo existir.",
            "Ligue o emulador, abra o Instagram nessa conta e veja o aviso.",
            "Resolva à mão (sem pressa: espere pelo menos 24 h se for bloqueio).",
            "Só então apague este arquivo para o story_post voltar a funcionar.",
        ],
    }
    ctx.saida(f"PARADO: aviso da Meta na tela ('{erro.frase}')")
    if ctx.simular:
        return
    if not arquivo_parado().exists():
        escrever_json(arquivo_parado(), dados)
    base = pasta_emulador() / "avisos"
    marca = ctx.relogio.agora().strftime("%Y%m%d_%H%M%S")
    try:
        garantir(base)
        if ctx.adb.ultimo_xml:
            (base / f"aviso_{marca}.xml").write_text(ctx.adb.ultimo_xml, encoding="utf-8")
        png = ctx.adb.screencap()
        if png:
            (base / f"aviso_{marca}.png").write_bytes(png)
    except Exception as e:  # diagnóstico é extra; nunca atrapalha a parada
        ctx.log.info("não salvei a imagem do aviso: %s", e)
    _historico(ctx, f"PARADO por aviso da Meta em {chave} (@{handle}): {erro.frase}")


def salvar_diagnostico(ctx: Contexto, chave: str) -> None:
    """Guarda o último dump da tela do erro (para conferir ids com o ui.py)."""
    if ctx.simular or not ctx.adb.ultimo_xml:
        return
    try:
        pasta = garantir(pasta_emulador() / "story_post_erros")
        nome = re.sub(r"[^A-Za-z0-9_.-]", "_", chave)[:60]
        marca = ctx.relogio.agora().strftime("%Y%m%d_%H%M%S")
        (pasta / f"{marca}_{nome}.xml").write_text(ctx.adb.ultimo_xml, encoding="utf-8")
        velhos = sorted(pasta.glob("*.xml"))[:-40]
        for v in velhos:
            v.unlink(missing_ok=True)
    except Exception as e:
        ctx.log.info("não salvei o diagnóstico: %s", e)


# ===========================================================================
# PASSOS DO FLUXO (cada um é uma função)
# ===========================================================================
def ligar_emulador(ctx: Contexto) -> None:
    """Passo 1: liga (boot frio pelo ligar_emulador.ps1) e espera boot_completed=1."""
    ctx.marcar("1 ligar o emulador")
    ctx.emu.ligar(ctx.orcamento)
    ctx.emu.preparar()


def desligar_emulador(ctx: Contexto) -> None:
    """Passo final: desliga SEMPRE (chamado no finally)."""
    ctx.marcar("desligar o emulador", checar=False)
    ctx.emu.desligar()


def abrir_instagram(ctx: Contexto) -> None:
    """Passo 2: fecha e abre o Instagram (começa sempre da mesma tela)."""
    ctx.marcar("2 abrir o Instagram")
    ctx.adb.fechar_app(PACOTE)
    ctx.adb.abrir_app(PACOTE)
    ctx.tela.esperar(id=ctx.sel.id("aba_perfil"),
                     timeout=float(ctx.cfg["timeout_abrir_app_seg"]))


def ir_para_perfil(ctx: Contexto) -> No:
    ctx.tela.tocar(id=ctx.sel.id("aba_perfil"), motivo="aba Perfil")
    return ctx.tela.esperar(id=ctx.sel.id("conta_container"))


def conta_ativa(ctx: Contexto, nos: list[No]) -> str | None:
    """Lê o @ do perfil aberto (texto dentro do action_bar_username_container)."""
    cont = filtrar(nos, id=ctx.sel.id("conta_container"))
    if cont:
        c = cont[0]
        for n in nos:
            if n is not c and n.texto.strip() and n.dentro_de(c):
                h = limpar_handle(n.texto)
                if h:
                    return h
        if c.texto or c.desc:
            h = limpar_handle(c.texto or c.desc)
            if h:
                return h
    tit = filtrar(nos, id=ctx.sel.id("conta_titulo"))
    if tit and tit[0].texto:
        return limpar_handle(tit[0].texto) or None
    return None


def _linha_da_conta(ctx: Contexto, nos: list[No], handle: str) -> No | None:
    cont = filtrar(nos, id=ctx.sel.id("conta_container"))
    for n in nos:
        if n.area <= 0 or (cont and n.dentro_de(cont[0])):
            continue
        if n.texto and normalizar(n.texto).lstrip("@") == handle:
            return n
    for n in nos:
        if n.area > 0 and n.desc and normalizar(n.desc).lstrip("@").startswith(handle + ","):
            return n
    return None


def trocar_conta(ctx: Contexto, handle: str) -> None:
    """Passo 3: perfil -> toca no @ -> toca na conta -> CONFERE (se errado, aborta)."""
    ctx.marcar(f"3 trocar para @{handle}")
    ir_para_perfil(ctx)
    ativa = conta_ativa(ctx, ctx.tela.ler())
    if ativa == handle:
        ctx.log.info("já estava em @%s", handle)
    else:
        ctx.tela.tocar(id=ctx.sel.id("conta_container"), motivo="lista de contas")
        linha = ctx.tela.esperar_condicao(
            lambda nos: _linha_da_conta(ctx, nos, handle),
            f"linha da conta @{handle} na lista",
            simulado=No(texto=handle, bounds=(0, 0, 1080, 100)), levantar=False)
        if not linha:
            raise ContaErrada(f"@{handle} não aparece na lista de contas do emulador "
                              "(faça login nela uma vez, à mão)")
        ctx.tela.tocar(linha, motivo=f"conta @{handle}")
    ok = ctx.tela.esperar_condicao(
        lambda nos: conta_ativa(ctx, nos) == handle, f"perfil ativo = @{handle}",
        timeout=float(ctx.cfg["timeout_elemento_seg"]), simulado=True, levantar=False)
    if not ok:
        atual = conta_ativa(ctx, ctx.tela.ultimos_nos)
        raise ContaErrada(f"conta ativa é @{atual or '?'}, esperado @{handle}: abortei")


def _primeiro_da_grade(ctx: Contexto, nos: list[No]) -> No | None:
    itens = [n for n in filtrar(nos, id=ctx.sel.id("grade_item"))
             if not re.search(r"fixad|pinned", normalizar(n.desc))]
    return min(itens, key=lambda n: (n.bounds[1], n.bounds[0])) if itens else None


def abrir_post_pela_grade(ctx: Contexto, handle: str, titulo: str | None) -> None:
    """Plano B: primeiro post (não fixado) da grade, conferindo o título na tela."""
    if not titulo:
        raise ElementoNaoApareceu("o link não abriu o post e sem título não dá para "
                                  "conferir na grade: abortei")
    ctx.marcar("4b abrir o post pela grade do perfil")
    ctx.tela.voltar_ate(id=ctx.sel.id("aba_perfil"))
    ir_para_perfil(ctx)
    item = ctx.tela.esperar_condicao(lambda nos: _primeiro_da_grade(ctx, nos),
                                     "primeiro post da grade",
                                     simulado=No(texto="post", bounds=(0, 0, 360, 360)))
    ctx.tela.tocar(item, motivo="primeiro post da grade")
    ctx.tela.esperar(id=ctx.sel.id("compartilhar"), timeout=float(ctx.cfg["timeout_post_seg"]))
    alvo = normalizar(titulo)[:30]
    achou = ctx.tela.esperar_condicao(
        lambda nos: any(alvo in normalizar(n.texto) for n in nos),
        "legenda com o título do post", timeout=8, simulado=True, levantar=False)
    if not achou:
        raise ElementoNaoApareceu("plano B: o post aberto não tem o título esperado; "
                                  "não compartilho post errado")


def abrir_post(ctx: Contexto, link: str, handle: str, titulo: str | None = None) -> None:
    """Passo 4: abre o post pelo link (am start VIEW); plano B pela grade."""
    ctx.marcar("4 abrir o post")
    ctx.adb.abrir_link(link, PACOTE)
    try:
        ctx.tela.esperar(id=ctx.sel.id("compartilhar"),
                         timeout=float(ctx.cfg["timeout_post_seg"]))
    except ElementoNaoApareceu:
        ctx.log.warning("o link não abriu o post; tentando a grade do perfil")
        abrir_post_pela_grade(ctx, handle, titulo)
    autor = ctx.tela.achar(nos=ctx.tela.ultimos_nos, escolher="topo",
                           id=ctx.sel.id("autor_post"))
    if autor and autor.texto and limpar_handle(autor.texto) != handle:
        raise ContaErrada(f"o post aberto é de @{limpar_handle(autor.texto)}, "
                          f"não de @{handle}: abortei")


def publicar_seu_story(ctx: Contexto, chave: str, handle: str,
                       link: str | None = None) -> None:
    """Toca em "Seu story" (grava antes: nunca repete) e espera o editor fechar."""
    botao = ctx.tela.esperar(id=ctx.sel.id("publicar_seu_story"),
                             timeout=float(ctx.cfg["timeout_editor_seg"]))
    registrar_tocado(ctx, chave, handle, link)
    ctx.tela.tocar(botao, motivo="Seu story (publicar)")
    ctx.tela.esperar_sumir(id=ctx.sel.id("publicar_seu_story"),
                           timeout=float(ctx.cfg["timeout_publicar_seg"]))
    registrar_publicado(ctx, chave)


def compartilhar_no_story(ctx: Contexto, chave: str, handle: str, link: str) -> None:
    """Passo 5: Enviar -> Adicionar ao story -> Seu story."""
    ctx.marcar("5 Enviar -> Adicionar ao story -> Seu story")
    ctx.tela.tocar(id=ctx.sel.id("compartilhar"), escolher="topo", motivo="Enviar")
    ctx.tela.tocar(rotulo=ctx.sel.txt("add_story"), motivo="Adicionar ao story")
    publicar_seu_story(ctx, chave, handle, link)


def esperar_upload(ctx: Contexto) -> None:
    """Espera o "Publicando..." sumir (não desliga o emulador no meio do envio)."""
    ctx.marcar("5b esperar o envio terminar")
    if not ctx.tela.esperar_sumir(rotulo=ctx.sel.txt("enviando"), parcial=True,
                                  timeout=float(ctx.cfg["timeout_upload_seg"]),
                                  levantar=False):
        ctx.log.warning("o indicador de envio não sumiu no prazo")


def avancar_ate_story_de_agora(ctx: Contexto) -> No:
    """No visualizador do próprio story, passa até o timestamp ser "Agora"/"1 min"."""
    lim = float(ctx.cfg["recente_max_min"])
    sumiu = 0
    for _ in range(int(ctx.cfg["max_stories_avancar"])):
        nos = ctx.tela.ler()
        ts = ctx.tela.achar(nos=nos, id=ctx.sel.id("story_timestamp"))
        if ts is None:
            if filtrar(nos, rotulo=ctx.sel.txt("enviando"), parcial=True):
                ctx.relogio.dormir(ctx.tela.intervalo)
                continue
            sumiu += 1
            if sumiu >= 3:
                raise ElementoNaoApareceu("o story fechou antes de achar o de agora")
            ctx.relogio.dormir(ctx.tela.intervalo)
            continue
        sumiu = 0
        m = minutos_do_timestamp(ts.texto)
        if m is not None and m <= lim:
            return ts
        w, h = ctx.tela.tamanho(nos)
        fx, fy = ctx.cfg["toque_avancar"]
        ctx.tela.tocar_xy(_coord(float(fx), w), _coord(float(fy), h), "próximo story")
    raise ElementoNaoApareceu("não achei o story de agora")


def adicionar_destaque(ctx: Contexto, nome: str) -> None:
    """Passo 6: abre o próprio story, vai até o de agora, Destaque -> nome."""
    ctx.marcar(f"6 destaque '{nome}'")
    ctx.tela.voltar_ate(id=ctx.sel.id("aba_perfil"))
    ir_para_perfil(ctx)
    ctx.tela.tocar(id=ctx.sel.id("avatar_perfil"), motivo="abrir meu story")
    ctx.tela.esperar(id=ctx.sel.id("story_timestamp"))
    avancar_ate_story_de_agora(ctx)
    ctx.tela.tocar(id=ctx.sel.id("story_destaque"), motivo="Destaque")
    alvo = ctx.tela.esperar(texto=[nome])
    ctx.tela.tocar(alvo, motivo=f"destaque '{nome}'")
    confirmou = ctx.tela.esperar_condicao(
        lambda nos: (filtrar(nos, rotulo=ctx.sel.txt("destaque_ok"), parcial=True)
                     or not filtrar(nos, texto=[nome])),
        "confirmação do destaque", timeout=10, simulado=True, levantar=False)
    if not confirmou:
        ctx.log.warning("não vi a confirmação do destaque '%s'", nome)
    ctx.tela.voltar()


def marcar_feito(ctx: Contexto, post_id: str, link: str) -> bool:
    """Passo 7: python scripts\\story_clicavel.py feito <post_id> --link <url>."""
    ctx.marcar("7 story_clicavel.py feito", checar=False)
    script = Path(ctx.cfg.get("story_clicavel") or (AQUI / "story_clicavel.py"))
    cmd = [ctx.cfg.get("python") or sys.executable, str(script), "feito",
           str(post_id), "--link", link]
    try:
        r = ctx.rodar_fn(cmd, timeout=120, cwd=str(script.parent.parent))
        ok = r.returncode == 0
        if not ok:
            ctx.log.warning("story_clicavel feito voltou %s: %s", r.returncode,
                            mascarar(_txt(r.stderr))[:300])
    except Exception as e:
        ok = False
        ctx.log.warning("story_clicavel feito falhou: %s", e)
    e = ler_estado()
    if str(post_id) in e["postados"]:
        e["postados"][str(post_id)]["feito"] = ok
        _gravar_estado(ctx, e)
    return ok


# ---------------------------------------------------------------------------
# Passos do story com arte (enquete e contagem)
# ---------------------------------------------------------------------------
def enviar_arte(ctx: Contexto, arte: Path, prefixo: str) -> str:
    """adb push para /sdcard/Pictures + MEDIA_SCANNER; espera entrar na galeria."""
    ctx.marcar("enviar a arte para a galeria do emulador")
    marca = ctx.relogio.agora().strftime("%Y%m%d_%H%M%S")
    nome = f"hp_{prefixo}_{marca}{Path(arte).suffix.lower() or '.png'}"
    remoto = f"/sdcard/Pictures/{nome}"
    ctx.adb.push(Path(arte), remoto)
    ctx.adb.shell(f"touch {remoto}")
    ctx.adb.escanear_midia(remoto)
    if ctx.simular:
        return nome
    fim = ctx.relogio.monotonic() + 20
    while not ctx.adb.midia_indexada(nome):
        if ctx.orcamento:
            ctx.orcamento.verificar("esperando a arte na galeria")
        if ctx.relogio.monotonic() >= fim:
            raise ElementoNaoApareceu(f"a arte {nome} não entrou na galeria")
        ctx.relogio.dormir(1.5)
    return nome


def abrir_camera_story(ctx: Contexto) -> None:
    """Perfil -> "+" -> Story (câmera do story)."""
    ctx.marcar("criar story (câmera)")
    ctx.tela.voltar_ate(id=ctx.sel.id("aba_perfil"))
    ir_para_perfil(ctx)
    ctx.tela.tocar_qualquer([{"id": ctx.sel.id("criar")},
                             {"desc": ctx.sel.txt("criar_desc")}], motivo="Criar (+)")
    ctx.tela.tocar(rotulo=ctx.sel.txt("menu_story"), motivo="Story")


def escolher_da_galeria(ctx: Contexto) -> None:
    """Galeria -> a mais recente (a arte que acabou de ser enviada)."""
    ctx.marcar("galeria: escolher a arte mais recente")
    ctx.tela.tocar_qualquer([{"id": ctx.sel.id("galeria")},
                             {"desc": ctx.sel.txt("galeria_desc"), "parcial": True}],
                            motivo="galeria")
    item = ctx.tela.esperar(id=ctx.sel.id("galeria_item"), escolher="topo")
    ctx.tela.tocar(item, motivo="arte mais recente")
    ctx.tela.esperar(id=ctx.sel.id("figurinhas"), timeout=float(ctx.cfg["timeout_editor_seg"]))


def _achar_figurinha(ctx: Contexto, nos: list[No], textos: list) -> No | None:
    for n in filtrar(nos, rotulo=textos, parcial=True):
        if n.classe.endswith("EditText") or _casa_id(n, ctx.sel.id("busca_figurinha")):
            continue
        return n
    return None


def abrir_figurinha(ctx: Contexto, tipo: str) -> None:
    """asset_button -> figurinha (enquete/contagem); busca se não estiver à vista."""
    ctx.marcar(f"figurinha de {tipo}")
    textos = ctx.sel.txt(f"figurinha_{tipo}")
    ctx.tela.tocar(id=ctx.sel.id("figurinhas"), motivo="figurinhas")
    alvo = ctx.tela.esperar_condicao(lambda nos: _achar_figurinha(ctx, nos, textos),
                                     f"figurinha de {tipo} na bandeja", timeout=6,
                                     simulado=No(texto=tipo, bounds=(0, 0, 300, 300)),
                                     levantar=False)
    if not alvo:
        busca = ctx.tela.tocar_qualquer(
            [{"id": ctx.sel.id("busca_figurinha")},
             {"rotulo": ctx.sel.txt("busca_rotulo"), "parcial": True}], motivo="busca")
        for i, termo in enumerate(ctx.sel.txt(f"busca_{tipo}")):
            if i:
                ctx.tela.tocar(busca, motivo="busca")
                ctx.adb.apagar(30)
            ctx.tela.digitar(termo)
            alvo = ctx.tela.esperar_condicao(
                lambda nos: _achar_figurinha(ctx, nos, textos),
                f"resultado '{termo}'", timeout=8,
                simulado=No(texto=tipo, bounds=(0, 0, 300, 300)), levantar=False)
            if alvo:
                break
    if not alvo:
        raise ElementoNaoApareceu(f"não achei a figurinha de {tipo}")
    ctx.tela.tocar(alvo, motivo=f"figurinha de {tipo}")


def _campos_opcoes(ctx: Contexto, nos: list[No]) -> list[No]:
    por_id = filtrar(nos, id=ctx.sel.id("enquete_opcao"))
    if por_id:
        return sorted(por_id, key=lambda n: (n.bounds[1], n.bounds[0]))
    perg = filtrar(nos, id=ctx.sel.id("enquete_pergunta"))
    topo = perg[0].bounds[3] if perg else 0
    campos = [n for n in nos if n.classe.endswith("EditText") and n.area > 0
              and not _casa_id(n, ctx.sel.id("enquete_pergunta")) and n.bounds[1] >= topo]
    return sorted(campos, key=lambda n: (n.bounds[1], n.bounds[0]))


def preencher_enquete(ctx: Contexto, pergunta: str, opcoes: list[str]) -> None:
    """poll_sticker_v2_question + opções (acentos pelo digitar.py) -> Concluir."""
    ctx.marcar("preencher a enquete")
    ctx.tela.tocar(id=ctx.sel.id("enquete_pergunta"), motivo="pergunta")
    ctx.tela.digitar(pergunta)
    sint = [No(texto=f"opção {i + 1}", bounds=(0, 0, 1080, 100)) for i in range(len(opcoes))]
    for i, texto in enumerate(opcoes):
        campos = ctx.tela.esperar_condicao(
            lambda nos: (lambda c: c if len(c) > i else None)(_campos_opcoes(ctx, nos)),
            f"campo da opção {i + 1}", timeout=4, simulado=sint, levantar=False)
        if not campos:
            ctx.tela.tocar(rotulo=ctx.sel.txt("enquete_add_opcao"), parcial=True,
                           motivo="adicionar opção")
            campos = ctx.tela.esperar_condicao(
                lambda nos: (lambda c: c if len(c) > i else None)(_campos_opcoes(ctx, nos)),
                f"campo da opção {i + 1}", simulado=sint)
        ctx.tela.tocar(campos[i], motivo=f"opção {i + 1}")
        ctx.tela.digitar(texto)
    ctx.tela.tocar(id=ctx.sel.id("concluir"), motivo="Concluir")


def arrastar_adesivo(ctx: Contexto, destino) -> None:
    """Arrasta a figurinha do meio da tela para a caixa da arte."""
    ctx.marcar("arrastar a figurinha para a caixa da arte")
    nos = ctx.tela.ler()
    w, h = ctx.tela.tamanho(nos)
    ox, oy = ctx.cfg.get("origem_adesivo") or [0.5, 0.5]
    x1, y1 = _coord(ox, w), _coord(oy, h)
    x2, y2 = _coord(destino[0], w), _coord(destino[1], h)
    ctx.adb.arrastar(x1, y1, x2, y2, ms=int(ctx.cfg["arrastar_ms"]),
                     modo=str(ctx.cfg["arrastar_modo"]))
    ctx.relogio.dormir(ctx.tela.pausa_toque)


_MESES_PT = ["janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho",
             "agosto", "setembro", "outubro", "novembro", "dezembro"]
_MESES_EN = ["january", "february", "march", "april", "may", "june", "july",
             "august", "september", "october", "november", "december"]


def _achar_dia(nos: list[No], d: date) -> No | None:
    pt, en = _MESES_PT[d.month - 1], _MESES_EN[d.month - 1]
    rotulos = [f"{d.day} de {pt} de {d.year}", f"{d.day} {pt} {d.year}",
               f"{d.day} {en} {d.year}", f"{en} {d.day}, {d.year}", f"{en} {d.day} {d.year}"]
    rx = [re.compile(r"(?<!\d)" + re.escape(r)) for r in rotulos]
    for n in nos:
        t = normalizar(n.desc or n.texto)
        if n.area > 0 and t and any(r.search(t) for r in rx):
            return n
    return None


def escolher_data(ctx: Contexto, alvo: date) -> None:
    """Calendário do Android: avança o mês até achar o dia e toca OK."""
    for _ in range(25):
        dia = ctx.tela.esperar_condicao(lambda nos: _achar_dia(nos, alvo),
                                        f"dia {alvo:%d/%m/%Y} no calendário", timeout=3,
                                        simulado=No(texto=str(alvo), bounds=(0, 0, 100, 100)),
                                        levantar=False)
        if dia:
            ctx.tela.tocar(dia, motivo=f"dia {alvo:%d/%m/%Y}")
            break
        ctx.tela.tocar(id=ctx.sel.id("data_proximo_mes"), motivo="próximo mês")
    else:
        raise ElementoNaoApareceu(f"não achei {alvo} no calendário")
    ctx.tela.tocar(id=ctx.sel.id("data_ok"), motivo="OK da data")
    # se abrir o relógio (hora), aceita a hora padrão com OK
    extra = ctx.tela.esperar_condicao(
        lambda nos: (filtrar(nos, id=ctx.sel.id("data_ok")) or [None])[0],
        "relógio da hora (opcional)", timeout=3, simulado=None, levantar=False)
    if extra:
        ctx.tela.tocar(extra, motivo="OK da hora")


def preencher_contagem(ctx: Contexto, titulo: str, data_alvo: date) -> None:
    """Figurinha de contagem: título, dia inteiro, data -> Concluir. (ids a confirmar)"""
    ctx.marcar("preencher a contagem regressiva")
    ctx.tela.tocar(id=ctx.sel.id("contagem_titulo"), motivo="título da contagem")
    ctx.tela.digitar(titulo)
    chave = ctx.tela.achar(id=ctx.sel.id("contagem_dia_inteiro"))
    if chave and not chave.marcado:
        ctx.tela.tocar(chave, motivo="dia inteiro")
    ctx.tela.tocar_qualquer([{"id": ctx.sel.id("contagem_data")},
                             {"rotulo": ctx.sel.txt("definir_data"), "parcial": True}],
                            motivo="data de término")
    escolher_data(ctx, data_alvo)
    ctx.tela.tocar(id=ctx.sel.id("concluir"), motivo="Concluir")


# ===========================================================================
# Orquestração: um story (com o emulador) e as rodadas
# ===========================================================================
class SessaoEmulador:
    """Liga na primeira vez que precisa; no fim desliga SEMPRE (mesmo em erro)."""

    def __init__(self, ctx: Contexto):
        self.ctx = ctx
        self.tentou = False
        self.ligado = False

    def garantir_ligado(self) -> None:
        if self.ligado:
            return
        if self.tentou:
            raise EmuladorNaoLigou("o emulador já falhou ao ligar nesta rodada")
        self.tentou = True
        ligar_emulador(self.ctx)
        self.ligado = True

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        if self.tentou:
            desligar_emulador(self.ctx)
        return False


def executar_story(ctx: Contexto, sessao: SessaoEmulador, tarefa: dict) -> dict:
    """Um story: abre o app, troca a conta, monta, publica, destaque, depois."""
    chave, handle = tarefa["chave"], tarefa["handle"]
    res = {"story": chave, "conta": f"@{handle}", "ok": False}
    ctx.saida(f"Story {chave} em @{handle}")
    try:
        sessao.garantir_ligado()
        abrir_instagram(ctx)
        trocar_conta(ctx, handle)
        tarefa["montar"](ctx)
        esperar_upload(ctx)
        if tarefa.get("destaque"):
            try:
                adicionar_destaque(ctx, tarefa["destaque"])
                res["destaque"] = "ok"
            except (ElementoNaoApareceu, OrcamentoEstourado, AdbErro) as e:
                res["destaque"] = f"falhou: {e}"
                _historico(ctx, f"destaque de {chave} falhou: {e}")
                salvar_diagnostico(ctx, chave + "_destaque")
    except AvisoMeta as e:
        res["erro"] = str(e)
        res["aviso_meta"] = True
        registrar_parado(ctx, e, chave, handle)
    except EmuladorNaoLigou as e:
        res["erro"] = str(e)
        res["erro_emulador"] = True
        registrar_falha(ctx, chave, e)
    except StoryErro as e:
        res["erro"] = f"{type(e).__name__}: {e}"
        registrar_falha(ctx, chave, e)
        salvar_diagnostico(ctx, chave)
    except Exception as e:  # erro inesperado: registra e segue para o finally
        res["erro"] = f"inesperado: {e!r}"
        ctx.log.exception("erro inesperado em %s", chave)
        registrar_falha(ctx, chave, e)
        salvar_diagnostico(ctx, chave)
    st = ctx.estados_sessao.get(chave)
    res["ok"] = st == "publicado"
    if st == "tocado":
        res["a_conferir"] = "tocou em 'Seu story' mas não confirmou; confira no Instagram"
    if st == "publicado" and tarefa.get("depois"):
        try:
            res["feito"] = tarefa["depois"](ctx)
        except Exception as e:
            ctx.log.warning("depois de %s falhou: %s", chave, e)
    return res


def _trava(ctx: Contexto):
    if ctx.simular:
        return nullcontext()
    return TravaPesada("story_post", ignorar_horario=True)


def _resultado(ok: bool, codigo: int, mensagem: str, **extra) -> dict:
    return {"ok": ok, "codigo": codigo, "mensagem": mensagem, **extra}


def _bloqueio(ctx: Contexto, chave: str | None = None) -> str | None:
    """Motivo para NÃO soltar story agora (ou None). Simular só avisa."""
    motivos = []
    if parado_existe():
        motivos.append(f"parado por aviso da Meta ({arquivo_parado()}); só o Antônio libera")
    if chave and chave in ler_estado()["postados"]:
        motivos.append(f"story de {chave} já saiu (1 story por post)")
    falta = falta_intervalo(ctx)
    if falta > 0:
        motivos.append(f"intervalo mínimo entre stories: faltam {falta:.0f}s")
    if not motivos:
        return None
    if ctx.simular:
        for m in motivos:
            ctx.saida(f"(no modo real pararia aqui: {m})")
        return None
    return "; ".join(motivos)


def _rodar_tarefas(ctx: Contexto, tarefas: list[dict], esperar_intervalo: bool) -> dict:
    resultados = []
    try:
        with _trava(ctx):
            with SessaoEmulador(ctx) as sessao:
                for t in tarefas:
                    if parado_existe() and not ctx.simular:
                        resultados.append({"story": t["chave"], "ok": False,
                                           "erro": "parado por aviso da Meta"})
                        break
                    falta = falta_intervalo(ctx)
                    if falta > 0:
                        if ctx.simular:
                            ctx.saida(f"(no modo real esperaria {falta:.0f}s de intervalo)")
                        elif esperar_intervalo:
                            ctx.log.info("esperando %.0fs de intervalo entre stories", falta)
                            ctx.relogio.dormir(falta)
                        else:
                            resultados.append({"story": t["chave"], "ok": False,
                                               "erro": f"intervalo: faltam {falta:.0f}s"})
                            break
                    ctx.novo_orcamento()
                    res = executar_story(ctx, sessao, t)
                    resultados.append(res)
                    ctx.saida(("OK " if res["ok"] else "ERRO ") + f"{res['story']} {res['conta']}"
                              + (f" - {res['erro']}" if res.get("erro") else ""))
                    if res.get("aviso_meta") or res.get("erro_emulador"):
                        break
    except TravaOcupada as e:
        return _resultado(False, BLOQUEADO, f"outro trabalho pesado está rodando ({e}); "
                                            "tento na próxima")
    if any(r.get("aviso_meta") for r in resultados):
        return _resultado(False, AVISO_META, "parado por aviso da Meta", resultados=resultados)
    tudo_ok = bool(resultados) and all(r.get("ok") for r in resultados)
    return _resultado(tudo_ok, OK if tudo_ok else ERRO,
                      "ok" if tudo_ok else "houve erro (veja o log)", resultados=resultados)


def tarefa_de_post(ctx: Contexto, item: dict) -> dict:
    pid = str(item.get("post_id"))
    handle = resolver_conta(ctx.cfg, item, ctx.log)
    link = validar_link(item.get("link"))
    titulo = item.get("titulo")

    def montar(c: Contexto) -> None:
        abrir_post(c, link, handle, titulo)
        compartilhar_no_story(c, pid, handle, link)

    return {"chave": pid, "handle": handle, "montar": montar,
            "destaque": (item.get("destaque") or "").strip() or None,
            "depois": lambda c: marcar_feito(c, pid, link)}


def _ja_feito(d: dict) -> bool:
    return d.get("feito") is True or normalizar(d.get("status")) in {
        "feito", "postado", "publicado", "story_ok"}


def listar_pendentes(ctx: Contexto) -> list[dict]:
    """Itens da fila_story prontos: post já publicado, story ainda não feito."""
    e = ler_estado()
    agora_ = ctx.relogio.agora()
    itens = []
    for p in sorted(pasta_fila().glob("*.json")):
        d = ler_json(p, {})
        if not isinstance(d, dict) or not d:
            ctx.log.warning("fila: %s ilegível; pulei", p.name)
            continue
        d.setdefault("post_id", p.stem)
        pid = str(d["post_id"])
        if _ja_feito(d) or pid in e["postados"]:
            continue
        if int(e["tentativas"].get(pid, 0)) >= int(ctx.cfg["max_tentativas"]):
            continue
        pub = _parse_dt(d.get("publicado_em"))
        if pub and pub > agora_:
            continue  # o post ainda não saiu: story só depois do post
        if not d.get("link"):
            continue
        itens.append(d)
    itens.sort(key=lambda d: (str(d.get("publicado_em") or ""), str(d["post_id"])))
    return itens


def reenviar_feitos_pendentes(ctx: Contexto) -> None:
    """Story saiu mas o story_clicavel feito falhou: tenta só o feito de novo."""
    for chave, d in list(ler_estado()["postados"].items()):
        if d.get("estado") == "publicado" and d.get("feito") is False and d.get("link"):
            marcar_feito(ctx, chave, d["link"])


def rodar_fila(ctx: Contexto, uma_vez: bool = False) -> dict:
    if parado_existe() and not ctx.simular:
        return _resultado(False, BLOQUEADO, "parado por aviso da Meta; nada sai")
    if not ctx.simular:
        reenviar_feitos_pendentes(ctx)
    pend = listar_pendentes(ctx)
    if not pend:
        ctx.saida("fila vazia")
        return _resultado(True, OK, "fila vazia", resultados=[])
    if uma_vez:
        pend = pend[:1]
        motivo = _bloqueio(ctx)
        if motivo:
            return _resultado(False, BLOQUEADO, motivo)
    tarefas = []
    for item in pend:
        try:
            tarefas.append(tarefa_de_post(ctx, item))
        except DadosInvalidos as e:
            ctx.log.warning("fila: %s inválido: %s", item.get("post_id"), e)
            registrar_falha(ctx, str(item.get("post_id")), e)
    if not tarefas:
        return _resultado(False, ERRO, "itens da fila inválidos (veja o log)")
    return _rodar_tarefas(ctx, tarefas, esperar_intervalo=True)


def rodar_post(ctx: Contexto, post_id: str) -> dict:
    arq = pasta_fila() / f"{post_id}.json"
    item = ler_json(arq, None)
    if not isinstance(item, dict):
        return _resultado(False, ERRO, f"não achei {arq}")
    item.setdefault("post_id", post_id)
    motivo = _bloqueio(ctx, str(item["post_id"]))
    if motivo:
        return _resultado(False, BLOQUEADO, motivo)
    try:
        tarefa = tarefa_de_post(ctx, item)
    except DadosInvalidos as e:
        return _resultado(False, ERRO, str(e))
    return _rodar_tarefas(ctx, [tarefa], esperar_intervalo=False)


# ---------------------------------------------------------------------------
# Enquete (story interativo das 16h do GTA) e contagem regressiva
# ---------------------------------------------------------------------------
def pastas_lotes(cfg: dict) -> list[Path]:
    if cfg.get("pastas_lotes"):
        return [Path(p) for p in cfg["pastas_lotes"]]
    return [raiz_drive() / "lotes", raiz_local() / "lotes"]


def _itens_do_lote(dados) -> list:
    if isinstance(dados, list):
        return dados
    if isinstance(dados, dict):
        for k in ("itens", "items", "estaticos", "posts"):
            if isinstance(dados.get(k), list):
                return dados[k]
        if "tipo" in dados:
            return [dados]
    return []


def _achar_estaticos(cfg: dict, dia: str) -> Path | None:
    for base in pastas_lotes(cfg):
        p = base / f"{dia}_estaticos.json"
        if p.exists():
            return p
    return None


def _item_do_lote(cfg: dict, dia: str, tipo: str) -> tuple:
    p = _achar_estaticos(cfg, dia)
    if not p:
        return None, None
    for it in _itens_do_lote(ler_json(p, {})):
        if isinstance(it, dict) and normalizar(it.get("tipo")) == tipo:
            return it, p
    return None, p


def _resolver_arte(arquivo, base_json: Path | None) -> Path:
    a = Path(str(arquivo))
    cands = [a] if a.is_absolute() else [
        *([base_json.parent / a] if base_json else []), raiz_drive() / a, raiz_local() / a]
    for c in cands:
        if c.is_file():
            return c
    raise DadosInvalidos(f"arte não encontrada: {arquivo}")


def _validar_caixa(v) -> list:
    if (not isinstance(v, (list, tuple)) or len(v) != 2
            or not all(isinstance(x, (int, float)) for x in v)):
        raise DadosInvalidos(f"caixa_enquete inválida (use [x, y]): {v}")
    return list(v)


def carregar_enquete(cfg: dict, dia: str, cortar: bool | None = None) -> dict:
    """Lê lotes\\<dia>_estaticos.json e devolve a enquete validada.

    Formato suposto (item da lista "itens"/"items" ou a própria lista):
      {"tipo": "story_enquete", "arquivo": "arte.png", "pergunta": "...",
       "opcoes": ["Sim", "Não"], "caixa_enquete": [540, 1500],
       "canal": "gta", "destaque": "Enquetes"}
    """
    cortar = cfg.get("cortar_pergunta") if cortar is None else cortar
    it, p = _item_do_lote(cfg, dia, "story_enquete")
    if not p:
        raise DadosInvalidos(f"não achei lotes\\{dia}_estaticos.json em "
                             + ", ".join(str(x) for x in pastas_lotes(cfg)))
    if not it:
        raise DadosInvalidos(f"{p.name} não tem item com tipo 'story_enquete'")
    pergunta = validar_texto_curto(it.get("pergunta"), int(cfg["limite_pergunta"]),
                                   bool(cortar), "pergunta")
    opcoes = [validar_texto_curto(o, int(cfg["limite_opcao"]), False, "opção")
              for o in (it.get("opcoes") or [])]
    if not 2 <= len(opcoes) <= 4:
        raise DadosInvalidos("a enquete precisa de 2 a 4 opções")
    handle = resolver_conta(cfg, {"canal": it.get("canal") or cfg["enquete_canal"],
                                  "conta": it.get("conta")})
    return {"arte": _resolver_arte(it.get("arquivo"), p), "pergunta": pergunta,
            "opcoes": opcoes, "handle": handle,
            "caixa": _validar_caixa(it.get("caixa_enquete") or cfg["caixa_enquete"]),
            "destaque": it.get("destaque", cfg["destaque_enquetes"])}


def _dia(ctx: Contexto, dia: str | None) -> str:
    """None/"hoje" -> data de hoje (AAAA-MM-DD); senão valida o formato."""
    if not dia or normalizar(dia) in ("hoje", "today"):
        return ctx.relogio.agora().date().isoformat()
    try:
        return date.fromisoformat(str(dia)).isoformat()
    except ValueError as e:
        raise DadosInvalidos(f"dia inválido '{dia}' (use AAAA-MM-DD ou hoje)") from e


def rodar_enquete(ctx: Contexto, dia: str | None = None, cortar: bool | None = None) -> dict:
    try:
        dia = _dia(ctx, dia)
        dados = carregar_enquete(ctx.cfg, dia, cortar)
    except DadosInvalidos as e:
        ctx.saida(f"ERRO: {e}")
        return _resultado(False, ERRO, str(e))
    chave = f"enquete_{dia}"
    motivo = _bloqueio(ctx, chave)
    if motivo:
        return _resultado(False, BLOQUEADO, motivo)
    handle = dados["handle"]

    def montar(c: Contexto) -> None:
        enviar_arte(c, dados["arte"], "enquete")
        abrir_camera_story(c)
        escolher_da_galeria(c)
        abrir_figurinha(c, "enquete")
        preencher_enquete(c, dados["pergunta"], dados["opcoes"])
        arrastar_adesivo(c, dados["caixa"])
        c.marcar("publicar em Seu story")
        publicar_seu_story(c, chave, handle)

    return _rodar_tarefas(ctx, [{"chave": chave, "handle": handle, "montar": montar,
                                 "destaque": dados["destaque"]}], esperar_intervalo=False)


def carregar_contagem(cfg: dict, dia: str, arte=None, titulo=None, data_alvo=None,
                      hoje: date | None = None) -> dict:
    cc = cfg["contagem"]
    it, p = _item_do_lote(cfg, dia, "story_contagem")
    it = it or {}
    titulo = validar_texto_curto(titulo or it.get("titulo") or cc["titulo"],
                                 int(cc.get("limite_titulo") or 30), False, "título")
    try:
        d = date.fromisoformat(str(data_alvo or it.get("data") or cc["data"]))
    except ValueError as e:
        raise DadosInvalidos(f"data inválida: {e}") from e
    if d <= (hoje or agora().date()):
        raise DadosInvalidos(f"a data da contagem ({d}) já passou")
    arq = arte or it.get("arquivo") or cc.get("arte")
    if not arq:
        raise DadosInvalidos("sem arte para a contagem (use --arte, item 'story_contagem' "
                             "no lote do dia ou contagem.arte no config)")
    handle = resolver_conta(cfg, {"canal": it.get("canal") or cc["canal"],
                                  "conta": it.get("conta")})
    caixa = it.get("caixa") or cc.get("caixa")
    return {"arte": _resolver_arte(arq, p), "titulo": titulo, "data": d, "handle": handle,
            "caixa": _validar_caixa(caixa) if caixa else None,
            "destaque": it.get("destaque", cc.get("destaque"))}


def rodar_contagem(ctx: Contexto, dia: str | None = None, arte=None, titulo=None,
                   data_alvo=None) -> dict:
    try:
        dia = _dia(ctx, dia)
        dados = carregar_contagem(ctx.cfg, dia, arte, titulo, data_alvo,
                                  hoje=ctx.relogio.agora().date())
    except DadosInvalidos as e:
        ctx.saida(f"ERRO: {e}")
        return _resultado(False, ERRO, str(e))
    chave = f"contagem_{dia}"
    motivo = _bloqueio(ctx, chave)
    if motivo:
        return _resultado(False, BLOQUEADO, motivo)
    handle = dados["handle"]

    def montar(c: Contexto) -> None:
        enviar_arte(c, dados["arte"], "contagem")
        abrir_camera_story(c)
        escolher_da_galeria(c)
        abrir_figurinha(c, "contagem")
        preencher_contagem(c, dados["titulo"], dados["data"])
        if dados["caixa"]:
            arrastar_adesivo(c, dados["caixa"])
        c.marcar("publicar em Seu story")
        publicar_seu_story(c, chave, handle)

    return _rodar_tarefas(ctx, [{"chave": chave, "handle": handle, "montar": montar,
                                 "destaque": dados["destaque"]}], esperar_intervalo=False)


# ---------------------------------------------------------------------------
# status / config
# ---------------------------------------------------------------------------
def mostrar_status(ctx: Contexto) -> dict:
    e = ler_estado()
    parado = parado_existe()
    ctx.saida("PARADO por aviso da Meta: " + (f"SIM ({arquivo_parado()})" if parado else "não"))
    ctx.saida(f"último story: {e.get('ultimo_story_em') or 'nenhum'}")
    falta = falta_intervalo(ctx)
    ctx.saida("próximo story liberado " + (f"em {falta:.0f}s" if falta else "agora"))
    pend = listar_pendentes(ctx)
    ctx.saida(f"na fila prontos para sair: {len(pend)}")
    for d in pend[:10]:
        ctx.saida(f"  - {d['post_id']} ({d.get('canal') or d.get('conta')})")
    conferir = [k for k, v in e["postados"].items() if v.get("estado") == "tocado"]
    if conferir:
        ctx.saida("a conferir no Instagram (tocou em 'Seu story' sem confirmação): "
                  + ", ".join(conferir))
    for f in e["falhas"][-5:]:
        ctx.saida(f"  falha {f['quando']} {f['story']}: {f['erro']}")
    return _resultado(True, OK, "status", parado=parado, pendentes=len(pend))


def criar_config_padrao() -> Path:
    p = arquivo_config()
    if not p.exists():
        dados = {"_leia": "Ajuste e salve. Veja LEIA_story_post.md. Chaves que começam "
                          "com _ são ignoradas."}
        dados.update(CONFIG_PADRAO)
        escrever_json(p, dados)
    return p


# ===========================================================================
# Gancho do HP Studio e linha de comando
# ===========================================================================
def executar(trabalho: dict) -> dict:
    """Gancho do motor do HP Studio: {"modo": "fila"|"post"|"enquete"|"contagem", ...}.

    Devolve {"ok", "codigo", "mensagem", "resultados"?}; nunca levanta StoryErro.
    """
    try:
        ctx = criar_contexto(simular=bool(trabalho.get("simular")), saida=lambda *_: None)
    except StoryErro as e:
        return _resultado(False, ERRO, str(e))
    modo = trabalho.get("modo", "fila")
    if modo == "fila":
        return rodar_fila(ctx, uma_vez=bool(trabalho.get("uma_vez", True)))
    if modo == "post":
        return rodar_post(ctx, str(trabalho["post_id"]))
    if modo == "enquete":
        return rodar_enquete(ctx, trabalho.get("dia"), trabalho.get("cortar"))
    if modo == "contagem":
        return rodar_contagem(ctx, trabalho.get("dia"), trabalho.get("arte"),
                              trabalho.get("titulo"), trabalho.get("data"))
    return _resultado(False, ERRO, f"modo desconhecido: {modo}")


def _parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="story_post.py",
        description="Story clicável pelo emulador Android (app oficial do Instagram).")
    ap.add_argument("--simular", action="store_true",
                    help="não chama o adb: só imprime o roteiro do que faria")
    ap.add_argument("--config", help="outro story_post_config.json")
    comum = argparse.ArgumentParser(add_help=False)
    comum.add_argument("--simular", action="store_true", default=argparse.SUPPRESS,
                       help="não chama o adb: só imprime o roteiro")
    sub = ap.add_subparsers(dest="comando", required=True, metavar="comando")
    f = sub.add_parser("fila", parents=[comum], help="posta os stories pendentes da fila_story")
    f.add_argument("--uma-vez", action="store_true", help="no máximo 1 story e sai")
    p = sub.add_parser("post", parents=[comum], help="story de um post da fila")
    p.add_argument("post_id", help="nome do arquivo da fila_story sem .json")
    e = sub.add_parser("enquete", parents=[comum], help="story com enquete (16h do GTA)")
    e.add_argument("--dia", default="hoje", help="dia do lote, ex.: 2026-09-30 (padrão: hoje)")
    e.add_argument("--cortar", action="store_true",
                   help="corta a pergunta em 25 caracteres em vez de abortar")
    c = sub.add_parser("contagem", parents=[comum], help="story com contagem regressiva do GTA 6")
    c.add_argument("--dia", default="hoje", help="dia do lote (padrão: hoje)")
    c.add_argument("--arte", help="imagem de fundo do story")
    c.add_argument("--titulo", help="título da contagem")
    c.add_argument("--data", help="data final AAAA-MM-DD (padrão 2026-11-19)")
    sub.add_parser("status", parents=[comum], help="mostra parada, intervalo e fila")
    sub.add_parser("config", parents=[comum], help="cria o story_post_config.json padrão")
    return ap


def main(argv: list | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.comando == "config":
        print(f"config em: {criar_config_padrao()}")
        return OK
    try:
        cfg = carregar_config(Path(args.config) if args.config else None)
        simular = bool(getattr(args, "simular", False))
        ctx = criar_contexto(cfg, simular=simular,
                             adb_exe="adb" if args.comando == "status" else None)
    except StoryErro as e:
        print(f"ERRO: {e}")
        return ERRO
    if ctx.simular:
        print("== SIMULAÇÃO: nada é enviado ao emulador ==")
    if args.comando == "fila":
        r = rodar_fila(ctx, uma_vez=args.uma_vez)
    elif args.comando == "post":
        r = rodar_post(ctx, args.post_id)
    elif args.comando == "enquete":
        r = rodar_enquete(ctx, args.dia, True if args.cortar else None)
    elif args.comando == "contagem":
        r = rodar_contagem(ctx, args.dia, args.arte, args.titulo, args.data)
    else:
        r = mostrar_status(ctx)
    if args.comando != "status":
        print(f"{'OK' if r['ok'] else 'NÃO SAIU'}: {r['mensagem']}")
    return int(r["codigo"])


if __name__ == "__main__":
    sys.exit(main())
