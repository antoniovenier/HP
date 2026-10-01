# -*- coding: utf-8 -*-
"""story_dispositivo.py — o aparelho Android (emulador ou celular real) que o story_post usa, por ADB.

O que faz: tudo o que encosta no aparelho fica aqui, num lugar só — escolher o aparelho, esperar
o boot, ler o tamanho da tela, conferir se está acesa e destravada, ler a tela (uiautomator
dump), achar e tocar botões pelo CENTRO dos bounds, deslizar, apertar tecla, tirar foto da tela,
digitar (ASCII pelo `input text`; acento vira letra sem acento e fica no log), mandar a arte para a
galeria e PARAR ao ver aviso da Meta, tela de login, código ou termos. Nada roda de verdade sem
um `runner` real: todo comando adb passa por `runner(argv) -> (codigo, saida)` injetado, e fica
gravado em `dispositivo.historico` (lista de argv) para os testes conferirem a sequência.

Uso (de outro script):
    from story_dispositivo import Dispositivo, escolher_serial, runner_real, runner_roteiro
    runner = runner_real(r"H:\\HypadoLocal\\android\\sdk\\platform-tools\\adb.exe", timeout=60)
    serial = escolher_serial(runner, serial=None, preferencia="emulador")   # ou --serial / HP_ANDROID_SERIAL
    disp = Dispositivo(runner, serial, gravar_parada=gravar_parada_padrao())
    disp.esperar_boot(240); disp.tela_acesa_e_destravada(); disp.abrir_app()
    nos = disp.dump(); disp.tocar(achar(nos, id="row_feed_button_share"))
    disp.digitar("O que você faz?")        # vai "O%sque%svoce%sfaz?" e o log diz: acento trocado: 'você' -> 'voce'
  --simular: Dispositivo(runner_roteiro(print), "emulator-5554") imprime o roteiro e não chama adb.

Uso (CLI de diagnóstico; códigos 0 ok · 1 erro · 3 aviso da rede · 4 bloqueado/precisa do Antônio):
    python scripts\\story_dispositivo.py aparelhos [--simular]
    python scripts\\story_dispositivo.py status [--serial S | --emulador | --celular]
    python scripts\\story_dispositivo.py dump [filtro] [--serial S]
    python scripts\\story_dispositivo.py foto <destino.png> [--serial S]

Regras:
- Aparelho: `--serial`, senão HP_ANDROID_SERIAL, senão exatamente UM "device" em `adb devices`; com
  0 ou 2+ recusa listando os seriais (preferência "emulador" = emulator-NNNN, "celular" = o outro).
- Tela diferente = coordenada diferente: NUNCA coordenada fixa. `tocar(no)` toca no centro dos bounds
  do dump; `tocar_fracao` usa o `wm size` do aparelho (nunca 1080x2400 fixo; "Override size" vale).
- Nunca digita senha/PIN/código: tela travada -> CelularBloqueado ("celular bloqueado: o Antônio
  desbloqueia", código 4). Nunca toca em Entrar/Login/Aceitar/Permitir/termos (PROIBIDO_* do
  story_post_seletores): `tocar` recusa com TelaProibida e grava a parada.
- Aviso da Meta / login / código / termos na tela -> `gravar_parada(dados)` injetado grava o arquivo
  de parada e AvisoMetaDetectado sobe (código 3). `dump()` já confere isso a cada leitura.
- Acento/emoji: o `adb shell input text` só digita ASCII. Política padrão "sem_acento" troca por letra
  sem acento (NFKD), tira emoji e REGISTRA no log. "acento_real" fica DESLIGADA: só funciona com o
  ADBKeyBoard instalado e selecionado pelo Antônio (o código não instala nada; sem ele, explica).
- Arte na galeria: `adb push` para /sdcard/Pictures/HP/<nome ASCII> e aviso ao MediaStore —
  principal: `content call --uri content://media/external/file --method scan_file --arg <caminho>`
  (MediaStore.SCAN_FILE_CALL = "scan_file", Android 10+; conferido no AOSP: MediaProvider trata a
  chamada sem checar permissão); plano B: broadcast MEDIA_SCANNER_SCAN_FILE (depreciado desde o
  Android 10, ainda tratado pelo MediaService); plano C: `scan_volume external_primary`. Cada plano é
  conferido com `content query` e só o próximo roda se a foto não apareceu. O que só dá para confirmar
  no aparelho está no docs/rodada2/E1.md.
- Windows: subprocesso só por hpbase.rodar (sem janela preta); caminhos com pathlib; nada de /tmp.
"""
from __future__ import annotations

import argparse
import base64
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

AQUI = Path(__file__).resolve().parent


def caminho_hp_studio() -> Path | None:
    """Acha a pasta que contém o pacote hpbase e põe no sys.path (mesmo truque do story_artes_base)."""
    cands: list[Path] = []
    env = os.environ.get("HP_APP")
    if env:
        cands += [Path(env), Path(env) / "hp_studio_nuvem", Path(env) / "hp_studio"]
    cands += [AQUI.parent / "app" / "hp_studio_nuvem",
              AQUI.parent / "06 Projeto" / "app" / "hp_studio_nuvem",
              AQUI.parent / "app" / "hp_studio",
              AQUI.parent / "06 Projeto" / "app" / "hp_studio"]
    for c in cands:
        if (c / "hpbase" / "__init__.py").exists():
            if str(c) not in sys.path:
                sys.path.insert(0, str(c))
            return c
    return None


caminho_hp_studio()
if str(AQUI) not in sys.path:
    sys.path.insert(0, str(AQUI))

from hpbase import FUSO, escrever_json, mascarar, raiz_local, rodar  # noqa: E402
import story_post_seletores as SEL  # noqa: E402

PACOTE = SEL.PACOTE
OK, ERRO, BLOQUEADO, AVISO_META, PRECISA_ANTONIO = 0, 1, 2, 3, 4
MSG_BLOQUEADO = "celular bloqueado: o Antônio desbloqueia"
ARQUIVO_DUMP = "/sdcard/ui.xml"
ARQUIVO_FOTO = "/sdcard/hp_tela.png"
PASTA_FOTOS = "/sdcard/Pictures/HP"
ADB_PC = r"H:\HypadoLocal\android\sdk\platform-tools\adb.exe"   # só aqui (HP_ADB troca)
ARQUIVO_PARADA_NOME = "PARADO_AVISO_META.json"                    # em H:\HypadoLocal\emulador\
TECLADO_ADB = "com.android.adbkeyboard/.AdbIME"
KEYCODE_BACK, KEYCODE_DEL, KEYCODE_WAKEUP, KEYCODE_CTRL, KEYCODE_A = 4, 67, 224, 113, 29
POLITICAS = ("sem_acento", "acento_real")
_RX_EMULADOR = re.compile(r"^emulator-\d+$")
_RX_TAMANHO = re.compile(r"(Physical|Override) size:\s*(\d+)\s*x\s*(\d+)", re.I)
_RX_BOUNDS = re.compile(r"\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]")
_RX_ATIVIDADE = re.compile(r"(?:topResumedActivity|mResumedActivity|ResumedActivity)\s*[=:]\s*"
                           r"ActivityRecord\{[^}]*?\s(?:u\d+\s)?([A-Za-z][\w.]*)/")
_RX_TRAVADA = re.compile(r"(?:\bmShowingLockscreen|\bmDreamingLockscreen|\bisKeyguardShowing|"
                         r"\bmKeyguardShowing|^\s*showing)\s*=\s*true", re.M)
_RX_ACORDADO = re.compile(r"mWakefulness\s*=\s*(\w+)")
_RX_EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\U0001FB00-\U0001FBFF\u2600-\u27BF\u2B00-\u2BFF\u2300-\u23FF\u2190-\u21FF"
    "\u2934\u2935\u3030\u303D\u3297\u3299\u00A9\u00AE\u2122\u2139\u231A\u231B\u24C2\u25AA-\u25FE"
    "\uFE0E\uFE0F\u200D\u20E3\U0001F1E6-\U0001F1FF\U000E0020-\U000E007F]")
_TROCAS_ASCII = {"ß": "ss", "æ": "ae", "Æ": "AE", "ø": "o", "Ø": "O", "ł": "l", "Ł": "L", "œ": "oe",
                 "Œ": "OE", "đ": "d", "Đ": "D", "—": "-", "–": "-", "…": "...", "\xa0": " ",
                 "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "«": '"', "»": '"'}
_PERIGOSOS_SHELL = set("&|;<>()$`\\*?[]{}~#!^")
_ASCII_LIVRE = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,:-_/@+=%")


# ===========================================================================
# Erros (código de saída em .codigo; mensagem em português, para leigo)
# ===========================================================================
class DispositivoErro(Exception):
    """Base: qualquer problema com o aparelho."""
    codigo = ERRO


class DispositivoAmbiguo(DispositivoErro):
    """0 ou 2+ aparelhos: o Antônio escolhe (--serial / HP_ANDROID_SERIAL / --emulador / --celular)."""
    codigo = PRECISA_ANTONIO

    def __init__(self, msg: str, seriais: list | None = None):
        super().__init__(msg)
        self.seriais = list(seriais or [])


class BootNaoTerminou(DispositivoErro):
    pass


class CelularBloqueado(DispositivoErro):
    """Tela apagada ou travada: o script nunca digita PIN."""
    codigo = PRECISA_ANTONIO


class DumpFalhou(DispositivoErro):
    pass


class ElementoNaoApareceu(DispositivoErro):
    pass


class TecladoAcentoIndisponivel(DispositivoErro):
    """Política acento_real pedida sem o ADBKeyBoard instalado/selecionado."""
    codigo = PRECISA_ANTONIO


class ArteNaoIndexada(DispositivoErro):
    pass


class AvisoMetaDetectado(DispositivoErro):
    """Aviso da Meta / login / código / termos na tela: para TUDO (a parada já foi gravada)."""
    codigo = AVISO_META

    def __init__(self, frase: str, trecho: str = ""):
        super().__init__(f"aviso na tela: '{frase}'" + (f" ({trecho[:80]})" if trecho else ""))
        self.frase = frase
        self.trecho = trecho


class TelaProibida(AvisoMetaDetectado):
    """Ia tocar em Entrar/Aceitar/Permitir/termos/senha: recusado."""


# ===========================================================================
# Texto
# ===========================================================================
def normalizar(s) -> str:
    """minúsculas, sem acento, espaços simples (para comparar textos da tela)."""
    t = unicodedata.normalize("NFKD", str(s or ""))
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.replace("\u2019", "'").replace("\u2018", "'").replace("\xa0", " ")
    return re.sub(r"\s+", " ", t.casefold()).strip()


def _lista(v) -> list | None:
    if v is None:
        return None
    if isinstance(v, (list, tuple, set)):
        return list(v)
    return [v]


def _txt(b) -> str:
    if b is None:
        return ""
    if isinstance(b, bytes):
        return b.decode("utf-8", errors="replace")
    return str(b)


def sem_acento(texto: str) -> tuple:
    """Texto só ASCII + lista de trocas [(original, trocado, motivo)] para o log.

    Acento vira letra sem acento (NFKD); emoji some; travessão/aspas curvas viram ASCII;
    o que não tem equivalente é removido. Nunca inventa letra.
    """
    trocas: list[tuple] = []
    original = str(texto or "")
    sem_emoji = _RX_EMOJI.sub("", original)
    sem_emoji = "".join(ch for ch in sem_emoji if unicodedata.category(ch) not in ("So", "Cs", "Co"))
    if sem_emoji != original:
        tirados = "".join(ch for ch in original if ch not in sem_emoji or ord(ch) > 0xFFFF)
        trocas.append((original.strip(), sem_emoji.strip(), "emoji removido: '" + tirados.strip() + "'"))
    saida = []
    for ch in sem_emoji:
        if ord(ch) < 128:
            saida.append(ch)
            continue
        if ch in _TROCAS_ASCII:
            saida.append(_TROCAS_ASCII[ch])
            continue
        base = "".join(c for c in unicodedata.normalize("NFKD", ch) if not unicodedata.combining(c))
        saida.append(base if base and all(ord(c) < 128 for c in base) else "")
    resultado = re.sub(r"[ \t]{2,}", " ", "".join(saida)).strip()
    # uma linha de log por palavra que mudou: "acento trocado: 'Você' -> 'Voce'"
    for antes, depois in zip(sem_emoji.split(), resultado.split()):
        if antes != depois:
            trocas.append((antes, depois, f"acento trocado: '{antes}' -> '{depois}'"))
    return resultado, trocas


def texto_para_input(texto_ascii: str) -> tuple:
    """Como o digitar.py: espaço vira %s e aspas somem. O resto que o shell do aparelho entenderia
    (? ! & $ | ; < > ( ) * etc.) ganha barra invertida, porque o `adb shell` junta os argumentos com
    espaço SEM escapar (como o ssh) e o shell do Android lê de novo: 'faz\\?' chega como 'faz?'.

    Devolve (texto pronto para o `input text`, lista de caracteres removidos).
    """
    removidos = []
    saida = []
    for ch in str(texto_ascii or ""):
        if ch in ("'", '"') or ord(ch) >= 128 or ord(ch) < 32:
            removidos.append(ch)
        elif ch in _PERIGOSOS_SHELL:
            saida.append("\\" + ch)
        else:
            saida.append(ch)
    return "".join(saida).replace(" ", "%s"), removidos


def nome_ascii_de(nome) -> str:
    """'contagem ção 09h.JPG' -> 'contagem_cao_09h.JPG' (só letras, números, ponto, _ e -)."""
    base, _ = sem_acento(Path(str(nome or "")).name)
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("._")
    base = re.sub(r"_{2,}", "_", base)
    return base or "arte.jpg"


def e_nome_ascii(nome: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9._-]+", str(nome or ""))) and ".." not in str(nome)


# ===========================================================================
# Nós da tela
# ===========================================================================
@dataclass(frozen=True)
class No:
    """Um elemento do dump do uiautomator. `bounds` = (x0, y0, x1, y1); `centro` é onde se toca."""
    bounds: tuple = (0, 0, 0, 0)
    id: str = ""            # curto: o que vem depois de ":id/"
    rid: str = ""           # completo: com.instagram.android:id/...
    texto: str = ""
    desc: str = ""
    clicavel: bool = False
    classe: str = ""        # curto: "TextView"
    classe_completa: str = ""
    pacote: str = ""
    senha: bool = False
    focado: bool = False
    habilitado: bool = True
    selecionado: bool = False
    marcado: bool = False

    @property
    def centro(self) -> tuple:
        b = self.bounds
        return ((b[0] + b[2]) // 2, (b[1] + b[3]) // 2)

    @property
    def x(self) -> int:
        return self.centro[0]

    @property
    def y(self) -> int:
        return self.centro[1]

    @property
    def largura(self) -> int:
        return max(0, self.bounds[2] - self.bounds[0])

    @property
    def altura(self) -> int:
        return max(0, self.bounds[3] - self.bounds[1])

    @property
    def area(self) -> int:
        return self.largura * self.altura

    @property
    def rotulo(self) -> str:
        return self.texto or self.desc

    def contem_ponto(self, x: int, y: int) -> bool:
        b = self.bounds
        return b[0] <= x < b[2] and b[1] <= y < b[3]

    def __getitem__(self, chave: str):
        """Compatível com os dicts do ui_dump.py: no["x"], no["id"], no["texto"]..."""
        if chave in ("x", "y", "centro", "largura", "altura", "area", "rotulo"):
            return getattr(self, chave)
        return getattr(self, chave)

    def como_dict(self) -> dict:
        return {"bounds": list(self.bounds), "centro": list(self.centro), "id": self.id, "texto": self.texto,
                "desc": self.desc, "clicavel": self.clicavel, "classe": self.classe}


def ler_bounds(s) -> tuple | None:
    m = _RX_BOUNDS.search(str(s or ""))
    return tuple(int(g) for g in m.groups()) if m else None


def parse_dump(xml: str) -> list[No]:
    """XML do `uiautomator dump` -> lista de nós (ordem do XML). Aceita lixo antes/depois
    ("UI hierchary dumped to: ..."). Vazio, cortado ou inválido -> [] (quem chama tenta de novo)."""
    xml = _txt(xml)
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
    nos: list[No] = []
    for el in raiz.iter("node"):
        b = ler_bounds(el.get("bounds"))
        if b is None:
            continue
        a = el.get
        rid = a("resource-id", "") or ""
        classe = a("class", "") or ""
        nos.append(No(bounds=b, id=rid.split(":id/", 1)[1] if ":id/" in rid else rid, rid=rid,
                      texto=a("text", "") or "", desc=a("content-desc", "") or "",
                      clicavel=a("clickable") == "true", classe=classe.rsplit(".", 1)[-1],
                      classe_completa=classe, pacote=a("package", "") or "",
                      senha=a("password") == "true", focado=a("focused") == "true",
                      habilitado=(a("enabled", "true") or "true") == "true",
                      selecionado=a("selected") == "true", marcado=a("checked") == "true"))
    return nos


def _casa_id(no: No, alternativas: list) -> bool:
    for i in alternativas:
        i = str(i or "")
        if i and (no.id == i or no.rid == i or no.rid.endswith(":id/" + i)):
            return True
    return False


def _casa_texto(valor: str, alternativas: list, contem: bool) -> bool:
    v = normalizar(valor)
    if not v:
        return False
    for a in alternativas:
        a = normalizar(a)
        if a and ((a in v) if contem else (v == a)):
            return True
    return False


def achar_todos(nos: list, id=None, texto=None, desc=None, contem: bool = True, rotulo=None,
                clicavel: bool | None = None, classe=None, visivel: bool = True) -> list[No]:
    """Nós que batem com TODOS os critérios (cada um aceita uma lista de alternativas).

    id: curto ou completo (sempre exato); texto / desc / rotulo (= texto OU desc) ignoram maiúscula
    e acento e, com contem=True (padrão), aceitam trecho; classe compara o nome curto.
    """
    ids, txs, dss, rts, cls = _lista(id), _lista(texto), _lista(desc), _lista(rotulo), _lista(classe)
    saida = []
    for n in nos:
        if visivel and n.area <= 0:
            continue
        if ids is not None and not _casa_id(n, ids):
            continue
        if txs is not None and not _casa_texto(n.texto, txs, contem):
            continue
        if dss is not None and not _casa_texto(n.desc, dss, contem):
            continue
        if rts is not None and not (_casa_texto(n.texto, rts, contem) or _casa_texto(n.desc, rts, contem)):
            continue
        if clicavel is not None and n.clicavel != clicavel:
            continue
        if cls is not None and not any(normalizar(n.classe) == normalizar(c) for c in cls):
            continue
        saida.append(n)
    return saida


def achar(nos: list, id=None, texto=None, desc=None, contem: bool = True, **crit) -> No | None:
    """Primeiro nó que casa (ou None). Mesmos critérios de achar_todos."""
    lst = achar_todos(nos, id=id, texto=texto, desc=desc, contem=contem, **crit)
    return lst[0] if lst else None


def descrever(crit: dict) -> str:
    partes = []
    for k in ("id", "texto", "desc", "rotulo"):
        v = _lista(crit.get(k))
        if v:
            partes.append(f"{k}=" + "|".join(str(x) for x in v[:3]))
    return " ".join(partes) or "?"


# ===========================================================================
# Avisos da Meta, login, termos; botões proibidos (listas do story_post_seletores)
# ===========================================================================
_AVISOS = [normalizar(a) for a in SEL.AVISOS_META]
_AVISOS_PALAVRAS = [re.compile(r"(?<![a-z0-9])" + re.escape(normalizar(a))) for a in SEL.AVISOS_META_PALAVRAS]
_PROIBIDO_EXATO = {normalizar(x) for x in SEL.PROIBIDO_TOCAR_EXATO}
_PROIBIDO_CONTEM = [normalizar(x) for x in SEL.PROIBIDO_TOCAR_CONTEM]
_IGNORAR_AVISO = set(SEL.IDS_CONTEUDO_IGNORAR_AVISO)
IDS_TELA_LOGIN = ("login_username", "login_password", "password", "log_in_button", "login_button",
                  "confirmation_code", "security_code", "verification_code")   # palpites (E4 confirma)


def detectar_aviso(nos: list, avisos_extra: list | None = None) -> tuple | None:
    """(frase, trecho) se a tela tem aviso da Meta, login, código ou termos; senão None.

    Frases valem no texto e na descrição; palavras soltas ("suspeita"...) só no texto visível e fora
    de legenda/grade/foto/campo de digitação (IDS_CONTEUDO_IGNORAR_AVISO). Campo de senha = login.
    """
    avisos = _AVISOS + [normalizar(a) for a in (avisos_extra or []) if a]
    for n in nos:
        if n.senha:
            return ("campo de senha (tela de login)", n.rotulo[:300])
        if n.id in IDS_TELA_LOGIN and n.area > 0:
            return (f"tela de login/código (id {n.id})", n.rotulo[:300])
        if n.id in _IGNORAR_AVISO or n.classe.endswith("EditText"):
            continue
        for campo, e_texto in ((n.texto, True), (n.desc, False)):
            if not campo:
                continue
            t = normalizar(campo)
            for a in avisos:
                if a and a in t:
                    return (a, campo[:300])
            if e_texto:
                for rx in _AVISOS_PALAVRAS:
                    m = rx.search(t)
                    if m:
                        return (m.group(0), campo[:300])
    return None


def toque_proibido(no) -> bool:
    """True se o nó é Entrar/Login/Aceitar/Permitir/Cadastre-se ou fala em senha/termos/código."""
    for campo in (getattr(no, "texto", ""), getattr(no, "desc", "")):
        t = normalizar(campo)
        if not t:
            continue
        if t in _PROIBIDO_EXATO or any(p in t for p in _PROIBIDO_CONTEM):
            return True
    return False


def arquivo_parada_padrao() -> Path:
    return raiz_local() / "emulador" / ARQUIVO_PARADA_NOME


def gravar_parada_padrao(caminho: Path | None = None, agora: Callable | None = None) -> Callable:
    """gravar_parada(dados) que grava o PARADO_AVISO_META.json (atômico). Só o Antônio apaga."""
    def _g(dados: dict) -> Path:
        p = Path(caminho) if caminho else arquivo_parada_padrao()
        d = dict(dados)
        d.setdefault("quando", (agora() if agora else datetime.now(FUSO)).isoformat(timespec="seconds"))
        d.setdefault("quem_apaga", "só o Antônio, depois de olhar o aparelho")
        return escrever_json(p, d)
    return _g


# ===========================================================================
# runners: real (hpbase.rodar), roteiro (--simular)
# ===========================================================================
def achar_adb() -> str | None:
    """HP_ADB > H:\\HypadoLocal\\android\\sdk\\platform-tools\\adb.exe > PATH."""
    env = os.environ.get("HP_ADB")
    if env and Path(env).is_file():
        return env
    for c in (raiz_local() / "android" / "sdk" / "platform-tools" / "adb.exe",
              raiz_local() / "android" / "sdk" / "platform-tools" / "adb", Path(ADB_PC)):
        if c.is_file():
            return str(c)
    return shutil.which("adb")


def runner_real(adb_exe: str | None = None, timeout: float = 60, rodar_fn: Callable | None = None) -> Callable:
    """runner(argv) -> (codigo, saida) de verdade: hpbase.rodar (sem janela no Windows, com timeout)."""
    rodar_fn = rodar_fn or rodar

    def _r(argv) -> tuple:
        cmd = [str(a) for a in argv]
        if adb_exe:
            cmd[0] = str(adb_exe)
        try:
            r = rodar_fn(cmd, timeout=timeout)
        except subprocess.TimeoutExpired:
            return (124, f"adb demorou mais de {timeout:.0f}s: {' '.join(cmd[1:])[:80]}")
        except FileNotFoundError:
            return (127, f"não achei o adb: {cmd[0]} (defina HP_ADB)")
        out = _txt(r.stdout)
        err = _txt(r.stderr)
        if r.returncode != 0 and err.strip():
            out = (out.rstrip("\r\n") + "\n" + err.strip()).strip()
        return (r.returncode, out)
    return _r


def runner_roteiro(saida: Callable = print, tela: tuple = (1080, 2400),
                   serial: str = "emulator-5554") -> Callable:
    """--simular: imprime cada comando e não executa nada (respostas mínimas para o fluxo seguir)."""
    def _citar(c: str) -> str:
        return f'"{c}"' if (" " in c or not c) else c

    def _r(argv) -> tuple:
        cmd = [str(a) for a in argv]
        texto = " ".join(cmd[1:])
        saida("  [simular] " + " ".join(_citar(c) for c in cmd))
        if cmd[1:2] == ["devices"]:
            return (0, f"List of devices attached\n{serial}\tdevice\n")
        if "sys.boot_completed" in texto:
            return (0, "1")
        if "wm size" in texto:
            return (0, f"Physical size: {tela[0]}x{tela[1]}")
        if "dumpsys power" in texto:
            return (0, "mWakefulness=Awake")
        if "dumpsys window" in texto:
            return (0, "mShowingLockscreen=false mDreamingLockscreen=false")
        if "dumpsys activity" in texto:
            return (0, f"topResumedActivity=ActivityRecord{{1 u0 {PACOTE}/.MainTabActivity t1}}")
        if "uiautomator dump" in texto:
            return (0, "UI hierchary dumped to: " + ARQUIVO_DUMP)
        if texto.endswith("cat " + ARQUIVO_DUMP):
            return (0, "<?xml version='1.0' encoding='UTF-8' standalone='yes' ?><hierarchy rotation=\"0\">"
                       f"<node index=\"0\" text=\"\" resource-id=\"\" class=\"android.widget.FrameLayout\" "
                       f"package=\"{PACOTE}\" content-desc=\"\" clickable=\"false\" enabled=\"true\" "
                       f"bounds=\"[0,0][{tela[0]},{tela[1]}]\" /></hierarchy>")
        if "content query" in texto:
            m = re.search(r"_display_name='([^']+)'", texto)
            return (0, f"Row: 0 _display_name={m.group(1)}" if m else "No result found.")
        return (0, "")
    return _r


# ===========================================================================
# Escolha do aparelho
# ===========================================================================
def listar_aparelhos(runner: Callable, adb: str = "adb") -> list[tuple]:
    """[(serial, estado)] do `adb devices` (estado: device, offline, unauthorized...)."""
    rc, out = runner([adb, "devices"])
    if rc != 0:
        raise DispositivoErro(f"não consegui rodar 'adb devices' (código {rc}): {mascarar(_txt(out))[:200]}")
    lista = []
    for linha in _txt(out).splitlines():
        linha = linha.strip()
        if not linha or linha.lower().startswith("list of devices") or linha.startswith("*"):
            continue
        partes = linha.split()
        if len(partes) >= 2:
            lista.append((partes[0], partes[1]))
    return lista


def _descreve(lista: list) -> str:
    return ", ".join(f"{s} ({e}{', emulador' if _RX_EMULADOR.match(s) else ', celular'})" for s, e in lista) or "nenhum"


def escolher_serial(runner: Callable, serial: str | None = None, env=None, preferencia: str | None = None,
                    adb: str = "adb") -> str:
    """--serial > HP_ANDROID_SERIAL > o único "device" do adb devices (filtrado pela preferência)."""
    env = os.environ if env is None else env
    lista = listar_aparelhos(runner, adb)
    pedido = (serial or "").strip() or (env.get("HP_ANDROID_SERIAL") or "").strip()
    if pedido:
        estados = dict(lista)
        if pedido in estados and estados[pedido] != "device":
            raise DispositivoAmbiguo(
                f"o aparelho {pedido} está '{estados[pedido]}': se for 'unauthorized', aceite a depuração USB "
                f"na tela do celular (o Antônio); se 'offline', desligue e ligue o cabo/emulador. Vi: {_descreve(lista)}",
                [s for s, _ in lista])
        if lista and pedido not in estados:
            raise DispositivoAmbiguo(f"o serial pedido ({pedido}) não apareceu em 'adb devices'. Vi: {_descreve(lista)}",
                                     [s for s, _ in lista])
        return pedido
    prontos = [s for s, e in lista if e == "device"]
    if preferencia:
        p = normalizar(preferencia)
        if p not in ("emulador", "celular"):
            raise ValueError(f"preferência '{preferencia}' desconhecida (use 'emulador' ou 'celular')")
        prontos = [s for s in prontos if bool(_RX_EMULADOR.match(s)) == (p == "emulador")]
    if len(prontos) == 1:
        return prontos[0]
    if not prontos:
        raise DispositivoAmbiguo(
            "nenhum aparelho pronto" + (f" com preferência '{preferencia}'" if preferencia else "")
            + f": ligue o emulador ou conecte o celular com a depuração USB aceita. Vi: {_descreve(lista)}",
            [s for s, _ in lista])
    raise DispositivoAmbiguo(
        f"há {len(prontos)} aparelhos ligados e não sei qual usar: {_descreve(lista)}. "
        "Escolha com --serial <serial>, --emulador, --celular ou a variável HP_ANDROID_SERIAL.", prontos)


# ===========================================================================
# O aparelho
# ===========================================================================
class Dispositivo:
    """Emulador ou celular real por ADB. Todo comando passa por `runner` e fica em `historico`."""

    def __init__(self, runner: Callable, serial: str | None = None, relogio=time, log=None,
                 adb: str = "adb", gravar_parada: Callable | None = None, pausa_toque: float = 0.5,
                 arquivo_dump: str = ARQUIVO_DUMP, pasta_fotos: str = PASTA_FOTOS,
                 avisos_extra: list | None = None, pacote: str = PACOTE):
        self.runner = runner
        self.serial = serial
        self.relogio = relogio
        self.log = log or logging.getLogger("hp.story_dispositivo")
        self.adb = adb
        self.gravar_parada = gravar_parada
        self.pausa_toque = float(pausa_toque)
        self.arquivo_dump = arquivo_dump
        self.pasta_fotos = pasta_fotos.rstrip("/")
        self.avisos_extra = list(avisos_extra or [])
        self.pacote = pacote
        self.historico: list[list] = []
        self.ultimo_xml = ""
        self.ultimos_nos: list[No] = []
        self._tela: tuple | None = None
        self.passo = ""

    # -- base ----------------------------------------------------------------
    def argv(self, *args) -> list:
        base = [self.adb] + (["-s", self.serial] if self.serial else [])
        return base + [str(a) for a in args]

    def executar(self, *args) -> tuple:
        """(codigo, saida) de um comando adb (sem 'adb' e sem '-s': só o resto)."""
        argv = self.argv(*args)
        self.historico.append(argv)
        rc, out = self.runner(argv)
        return int(rc), _txt(out)

    def shell(self, *args) -> tuple:
        return self.executar("shell", *args)

    def comandos_shell(self) -> list[str]:
        """Os comandos `adb shell ...` já mandados, como texto (para conferir a sequência)."""
        saida = []
        for argv in self.historico:
            if "shell" in argv:
                i = argv.index("shell")
                saida.append(" ".join(argv[i + 1:]))
        return saida

    def _dormir(self, seg: float) -> None:
        if seg > 0:
            self.relogio.sleep(seg)

    # -- boot, tela, app ------------------------------------------------------
    def boot_completo(self) -> bool:
        rc, out = self.shell("getprop", "sys.boot_completed")
        return rc == 0 and out.strip() == "1"

    def esperar_boot(self, timeout_s: float = 240, intervalo_s: float = 5) -> float:
        """Espera sys.boot_completed = 1 (relógio injetado). Devolve os segundos esperados."""
        inicio = self.relogio.monotonic()
        while True:
            if self.boot_completo():
                gasto = self.relogio.monotonic() - inicio
                self.log.info("boot completo em %.0fs", gasto)
                return gasto
            if self.relogio.monotonic() - inicio >= timeout_s:
                raise BootNaoTerminou(f"o Android não terminou de ligar em {timeout_s:.0f}s "
                                      f"(serial {self.serial or '?'})")
            self._dormir(intervalo_s)

    def tamanho_tela(self, renovar: bool = False) -> tuple:
        """(largura, altura) do `wm size`; "Override size" vale mais que "Physical size". Com cache."""
        if self._tela and not renovar:
            return self._tela
        rc, out = self.shell("wm", "size")
        achados = {m.group(1).lower(): (int(m.group(2)), int(m.group(3))) for m in _RX_TAMANHO.finditer(out)}
        tela = achados.get("override") or achados.get("physical")
        if rc != 0 or not tela:
            raise DispositivoErro(f"não entendi o tamanho da tela ('wm size' respondeu: {out.strip()[:120]!r})")
        self._tela = tela
        self.log.info("tela %dx%d", *tela)
        return tela

    def _acesa(self) -> bool:
        _, out = self.shell("dumpsys", "power")
        m = _RX_ACORDADO.search(out)
        if m:
            return m.group(1).lower() == "awake"
        m = re.search(r"Display Power:\s*state=(\w+)", out)
        return (m.group(1).upper() == "ON") if m else True

    def _travada(self) -> bool:
        _, out = self.shell("dumpsys", "window")
        return bool(_RX_TRAVADA.search(out))

    def tela_acesa_e_destravada(self, tentar: bool = True) -> bool:
        """Acorda a tela (KEYCODE_WAKEUP) e tira a tela de bloqueio SEM PIN (wm dismiss-keyguard).
        Continua travada (PIN/padrão) -> CelularBloqueado, código 4. Nunca digita PIN."""
        if not self._acesa():
            if tentar:
                self.tecla(KEYCODE_WAKEUP)
                self._dormir(1)
            if not self._acesa():
                raise CelularBloqueado(MSG_BLOQUEADO + " (a tela está apagada e não acordou)")
        if self._travada():
            if tentar:
                self.shell("wm", "dismiss-keyguard")
                self._dormir(1)
            if self._travada():
                raise CelularBloqueado(MSG_BLOQUEADO + " (tela de bloqueio com PIN/padrão; o script nunca digita o PIN)")
        return True

    def app_na_frente(self) -> str | None:
        """Pacote do app na frente ('com.instagram.android') pelo dumpsys activity activities."""
        _, out = self.shell("dumpsys", "activity", "activities")
        m = _RX_ATIVIDADE.search(out)
        return m.group(1) if m else None

    def instagram_na_frente(self) -> bool:
        return self.app_na_frente() == self.pacote

    def abrir_app(self, pacote: str | None = None) -> None:
        self.shell("monkey", "-p", pacote or self.pacote, "-c", "android.intent.category.LAUNCHER", "1")

    def fechar_app(self, pacote: str | None = None) -> None:
        self.shell("am", "force-stop", pacote or self.pacote)

    def abrir_link(self, link: str, pacote: str | None = None) -> None:
        """Deep link no Instagram: am start -a VIEW -d <link> -p com.instagram.android."""
        link = str(link or "").strip()
        if not re.match(r"^https?://", link, re.I):
            raise ValueError(f"link inválido: {link!r}")
        self.shell("am", "start", "-a", "android.intent.action.VIEW", "-d", shlex.quote(link),
                   "-p", pacote or self.pacote)

    # -- ler a tela -------------------------------------------------------------
    def dump(self, tentativas: int = 3, checar_aviso: bool = True, intervalo_s: float = 1.0) -> list[No]:
        """Lê a tela (uiautomator dump + cat), repetindo quando o dump falha. Com checar_aviso,
        para na hora se houver aviso da Meta/login/termos (grava a parada, código 3)."""
        erro = ""
        for i in range(1, max(1, int(tentativas)) + 1):
            rc, out = self.shell("uiautomator", "dump", self.arquivo_dump)
            if rc == 0 and "error" not in out.lower():
                rc2, xml = self.shell("cat", self.arquivo_dump)
                nos = parse_dump(xml) if rc2 == 0 else []
                if nos:
                    self.ultimo_xml = xml
                    self.ultimos_nos = nos
                    if checar_aviso:
                        self.parar_por_aviso(nos)
                    return nos
                erro = "dump vazio ou cortado"
            else:
                erro = out.strip()[:120] or f"código {rc}"
            self.log.warning("uiautomator dump falhou (%d/%d): %s", i, tentativas, erro)
            if i < tentativas:
                self._dormir(intervalo_s)
        raise DumpFalhou(f"não consegui ler a tela depois de {tentativas} tentativas ({erro}); "
                         "a tela está mudando sem parar ou o aparelho travou")

    def parar_por_aviso(self, nos: list, passo: str | None = None) -> None:
        """Aviso da Meta / login / código / termos -> grava a parada (função injetada) e levanta
        AvisoMetaDetectado (código 3). Sem aviso: não faz nada."""
        achado = detectar_aviso(nos, self.avisos_extra)
        if not achado:
            return
        frase, trecho = achado
        self._parar(frase, trecho, passo, AvisoMetaDetectado)

    def _parar(self, frase: str, trecho: str, passo: str | None, tipo) -> None:
        dados = {"frase": frase, "trecho": trecho, "passo": passo or self.passo, "serial": self.serial,
                 "motivo": "aviso da Meta / login / código / termos na tela" if tipo is AvisoMetaDetectado
                 else "ia tocar num botão proibido (login/aceitar/permitir/termos)"}
        self.log.error("PARADA: %s (%s) no passo '%s'", frase, trecho[:80], dados["passo"])
        if self.gravar_parada:
            try:
                self.gravar_parada(dados)
            except Exception as e:  # a parada tem de subir mesmo se o arquivo falhar
                self.log.error("não consegui gravar o arquivo de parada: %s", e)
        raise tipo(frase, trecho)

    def esperar(self, timeout_s: float = 20, intervalo_s: float = 1.0, **crit) -> No:
        """Lê a tela até aparecer um nó que case com os critérios (relógio injetado)."""
        return self.esperar_qualquer([crit], timeout_s, intervalo_s)

    def esperar_qualquer(self, alternativas: list, timeout_s: float = 20, intervalo_s: float = 1.0) -> No:
        fim = self.relogio.monotonic() + timeout_s
        while True:
            nos = self.dump()
            for crit in alternativas:
                lst = achar_todos(nos, **crit)
                if lst:
                    return lst[0]
            if self.relogio.monotonic() >= fim:
                raise ElementoNaoApareceu("não achei na tela: " + " ou ".join(descrever(c) for c in alternativas)
                                          + "; o Instagram mudou?")
            self._dormir(intervalo_s)

    def esperar_sumir(self, timeout_s: float = 20, intervalo_s: float = 1.0, **crit) -> bool:
        fim = self.relogio.monotonic() + timeout_s
        while True:
            if not achar_todos(self.dump(), **crit):
                return True
            if self.relogio.monotonic() >= fim:
                raise ElementoNaoApareceu(f"não sumiu da tela: {descrever(crit)}")
            self._dormir(intervalo_s)

    # -- agir -------------------------------------------------------------------
    @staticmethod
    def _ponto(alvo) -> tuple:
        """No, dict do ui_dump ({'x','y'} ou {'bounds'}) ou (x, y) -> (x, y) inteiros."""
        if isinstance(alvo, No):
            return alvo.centro
        if isinstance(alvo, dict):
            if "bounds" in alvo:
                b = alvo["bounds"]
                return ((int(b[0]) + int(b[2])) // 2, (int(b[1]) + int(b[3])) // 2)
            return (int(alvo["x"]), int(alvo["y"]))
        x, y = alvo
        return (int(round(x)), int(round(y)))

    def tocar(self, no, motivo: str = "") -> tuple:
        """Toca no CENTRO dos bounds do nó (input tap). Botão proibido -> TelaProibida (nada é tocado)."""
        if no is None:
            raise ElementoNaoApareceu(f"não achei o botão {motivo or ''} na tela; o Instagram mudou?".replace("  ", " "))
        if toque_proibido(no):
            rot = getattr(no, "rotulo", "") or (no.get("texto") or no.get("desc") if isinstance(no, dict) else "")
            self._parar(f"botão proibido '{rot}'", str(rot), motivo, TelaProibida)
        if isinstance(no, No) and no.area <= 0:
            raise ElementoNaoApareceu(f"elemento invisível (bounds vazios): {motivo or no.rotulo or no.id}")
        x, y = self._ponto(no)
        self.log.info("tocar %s em (%d,%d)", motivo or getattr(no, "rotulo", "") or getattr(no, "id", ""), x, y)
        self.shell("input", "tap", x, y)
        self._dormir(self.pausa_toque)
        return (x, y)

    def tocar_fracao(self, fx: float, fy: float, motivo: str = "") -> tuple:
        """Toca numa fração da tela (0-1), usando SEMPRE o wm size do aparelho."""
        w, h = self.tamanho_tela()
        x, y = int(round(float(fx) * w)), int(round(float(fy) * h))
        self.log.info("tocar fração (%.2f,%.2f) = (%d,%d) %s", fx, fy, x, y, motivo)
        self.shell("input", "tap", x, y)
        self._dormir(self.pausa_toque)
        return (x, y)

    def _ponto_ou_fracao(self, p) -> tuple:
        if isinstance(p, (tuple, list)) and len(p) == 2 and all(isinstance(v, float) and 0 <= v <= 1 for v in p):
            w, h = self.tamanho_tela()
            return (int(round(p[0] * w)), int(round(p[1] * h)))
        return self._ponto(p)

    def deslizar(self, de, para, ms: int = 300) -> None:
        """input swipe x1 y1 x2 y2 ms. `de`/`para`: No, (x, y) em pixels ou (fx, fy) em fração (floats 0-1)."""
        x1, y1 = self._ponto_ou_fracao(de)
        x2, y2 = self._ponto_ou_fracao(para)
        self.log.info("deslizar (%d,%d) -> (%d,%d) em %dms", x1, y1, x2, y2, ms)
        self.shell("input", "swipe", x1, y1, x2, y2, int(ms))
        self._dormir(self.pausa_toque)

    def tecla(self, codigo) -> None:
        """input keyevent <código> (número ou KEYCODE_...)."""
        self.shell("input", "keyevent", codigo)

    def voltar(self) -> None:
        self.tecla(KEYCODE_BACK)
        self._dormir(self.pausa_toque)

    def screencap(self, destino) -> Path:
        """screencap -p no aparelho + pull para `destino` (cria a pasta)."""
        destino = Path(destino)
        destino.parent.mkdir(parents=True, exist_ok=True)
        rc, out = self.shell("screencap", "-p", ARQUIVO_FOTO)
        if rc != 0:
            raise DispositivoErro(f"screencap falhou: {out.strip()[:120]}")
        rc, out = self.executar("pull", ARQUIVO_FOTO, str(destino))
        if rc != 0:
            raise DispositivoErro(f"adb pull da foto falhou: {out.strip()[:120]}")
        return destino

    # -- digitar ------------------------------------------------------------------
    def teclado_acento(self) -> tuple:
        """(instalado_e_ativo, selecionado) do ADBKeyBoard. Só lê; não instala nem ativa nada."""
        _, lista = self.shell("ime", "list", "-s")
        ativo = TECLADO_ADB in lista
        _, atual = self.shell("settings", "get", "secure", "default_input_method")
        return ativo, atual.strip() == TECLADO_ADB

    def digitar(self, texto: str, politica: str = "sem_acento", campo=None, limpar: bool = False) -> str:
        """Digita no campo focado (ou toca `campo` antes). Devolve o texto que foi mandado.

        sem_acento (padrão): acento -> letra sem acento, emoji some; cada troca vai para o log.
        acento_real: só com o ADBKeyBoard instalado E selecionado (o Antônio faz; o código não
        instala). Sem ele, TecladoAcentoIndisponivel explica o passo a passo (código 4).
        """
        if politica not in POLITICAS:
            raise ValueError(f"política '{politica}' desconhecida; use {POLITICAS}")
        texto = str(texto or "")
        if campo is not None:
            self.tocar(campo, "campo de texto")
        if limpar:
            self.shell("input", "keycombination", KEYCODE_CTRL, KEYCODE_A)
            self.shell("input", "keyevent", KEYCODE_DEL)
        if not texto.strip():
            return ""
        if any(n.senha for n in self.ultimos_nos):
            self._parar("campo de senha (tela de login)", "", "digitar", TelaProibida)
        if politica == "acento_real":
            return self._digitar_acento_real(texto)
        ascii_, trocas = sem_acento(texto)
        for _, _, motivo in trocas:
            self.log.warning("%s", motivo)
        pronto, removidos = texto_para_input(ascii_)
        if removidos:
            self.log.warning("caracteres removidos antes do input text: %s", "".join(sorted(set(removidos))))
        if not pronto:
            return ""
        self.log.info("digitar %d caracteres (ASCII, política %s)", len(ascii_), politica)
        self.shell("input", "text", pronto)
        self._dormir(self.pausa_toque)
        return pronto

    def _digitar_acento_real(self, texto: str) -> str:
        ativo, selecionado = self.teclado_acento()
        if not (ativo and selecionado):
            raise TecladoAcentoIndisponivel(
                "a política 'acento_real' precisa do teclado ADBKeyBoard, que o Antônio instala e ativa "
                "(o script não instala nada):\n"
                "  1. Baixar o ADBKeyboard.apk (projeto senzhk/ADBKeyBoard no GitHub) e instalar: "
                "adb install ADBKeyboard.apk\n"
                "  2. No aparelho: Configurações > Sistema > Idiomas e entrada > Teclado virtual > "
                "Gerenciar teclados > ligar 'ADB Keyboard' e ACEITAR o aviso de segurança do Android\n"
                "  3. Selecionar como teclado padrão: adb shell ime set " + TECLADO_ADB + "\n"
                "  4. Depois de postar, voltar ao Gboard: adb shell ime set com.google.android.inputmethod.latin/"
                "com.android.inputmethod.latin.LatinIME\n"
                f"Agora: instalado e ativo = {'sim' if ativo else 'não'}; selecionado = {'sim' if selecionado else 'não'}. "
                "Enquanto isso, use a política padrão 'sem_acento'.")
        b64 = base64.b64encode(texto.encode("utf-8")).decode("ascii")
        self.log.info("digitar %d caracteres pelo ADBKeyBoard (acento real)", len(texto))
        self.shell("am", "broadcast", "-a", "ADB_INPUT_B64", "--es", "msg", b64)
        self._dormir(self.pausa_toque)
        return texto

    # -- arte na galeria ---------------------------------------------------------
    def midia_indexada(self, nome: str) -> bool:
        _, out = self.shell("content", "query", "--uri", "content://media/external/images/media",
                            "--projection", "_display_name", "--where", f"\"_display_name='{nome}'\"")
        return nome in out and "No result" not in out

    def planos_mediastore(self, remoto: str) -> list[tuple]:
        """(nome do plano, argv do shell) na ordem em que são tentados."""
        return [
            ("principal: content call scan_file (MediaStore.scanFile, Android 10+)",
             ["content", "call", "--uri", "content://media/external/file", "--method", "scan_file",
              "--arg", remoto]),
            ("plano B: broadcast MEDIA_SCANNER_SCAN_FILE (depreciado desde o Android 10)",
             ["am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE", "-d", f"file://{remoto}"]),
            ("plano C: content call scan_volume external_primary (varre a memória toda)",
             ["content", "call", "--uri", "content://media/external/file", "--method", "scan_volume",
              "--arg", "external_primary"]),
        ]

    def empurrar_arte(self, arquivo_local, nome_ascii: str | None = None, espera_s: float = 1.0) -> dict:
        """adb push para /sdcard/Pictures/HP/<nome> + aviso ao MediaStore até a foto aparecer na galeria.

        Devolve {"remoto", "nome", "plano"}; nenhum plano funcionou -> ArteNaoIndexada.
        """
        local = Path(arquivo_local)
        if not local.is_file():
            raise DispositivoErro(f"não achei a arte para mandar ao aparelho: {local}")
        nome = nome_ascii or nome_ascii_de(local.name)
        if not e_nome_ascii(nome):
            raise DispositivoErro(f"o nome do arquivo no aparelho precisa ser ASCII (letras, números, ponto, _ e -): "
                                  f"{nome!r}; sugestão: {nome_ascii_de(nome)!r}")
        remoto = f"{self.pasta_fotos}/{nome}"
        self.shell("mkdir", "-p", self.pasta_fotos)
        rc, out = self.executar("push", str(local), remoto)
        if rc != 0:
            raise DispositivoErro(f"adb push falhou: {mascarar(out.strip())[:200]}")
        self.log.info("arte enviada: %s -> %s", local.name, remoto)
        tentados = []
        for plano, argv in self.planos_mediastore(remoto):
            rc, out = self.shell(*argv)
            tentados.append(plano)
            self._dormir(espera_s)
            if self.midia_indexada(nome):
                self.log.info("foto na galeria pelo %s", plano)
                return {"remoto": remoto, "nome": nome, "plano": plano}
            self.log.warning("a foto não apareceu na galeria pelo %s (resposta: %s)", plano, out.strip()[:100])
        raise ArteNaoIndexada(
            f"a arte foi para {remoto}, mas não apareceu na galeria do aparelho depois de: " + "; ".join(tentados)
            + ". Abra a galeria/Instagram à mão e veja se a foto está lá; se não, o Antônio confere o "
              "MediaStore nesse Android (docs/rodada2/E1.md).")


# ===========================================================================
# CLI de diagnóstico
# ===========================================================================
def _argumentos(argv) -> argparse.Namespace:
    ap = argparse.ArgumentParser(prog="python scripts\\story_dispositivo.py",
                                 description="Diagnóstico do aparelho (emulador ou celular) por ADB.")
    sub = ap.add_subparsers(dest="cmd")
    for nome, ajuda in (("aparelhos", "lista o adb devices"), ("status", "boot, tela, bloqueio, app na frente"),
                        ("dump", "lista os elementos da tela (filtro opcional)"), ("foto", "screencap para um PNG")):
        p = sub.add_parser(nome, help=ajuda)
        p.add_argument("--serial")
        p.add_argument("--emulador", action="store_true")
        p.add_argument("--celular", action="store_true")
        p.add_argument("--simular", action="store_true", help="não chama o adb; imprime o roteiro")
        p.add_argument("--adb", help="caminho do adb.exe (padrão: HP_ADB ou o do PC)")
        if nome == "dump":
            p.add_argument("filtro", nargs="?", default="")
        if nome == "foto":
            p.add_argument("destino")
    return ap.parse_args(argv), ap


def main(argv=None, runner: Callable | None = None, saida: Callable = print, env=None) -> int:
    args, ap = _argumentos(argv)
    if not args.cmd:
        ap.print_help()
        return ERRO
    try:
        if runner is None:
            if args.simular:
                runner = runner_roteiro(saida)
            else:
                exe = args.adb or achar_adb()
                if not exe:
                    saida("não achei o adb.exe (defina HP_ADB ou passe --adb)")
                    return ERRO
                runner = runner_real(exe)
        if args.cmd == "aparelhos":
            lista = listar_aparelhos(runner)
            saida("aparelhos: " + _descreve(lista))
            return OK
        pref = "emulador" if args.emulador else ("celular" if args.celular else None)
        serial = escolher_serial(runner, args.serial, env=env, preferencia=pref)
        disp = Dispositivo(runner, serial, gravar_parada=gravar_parada_padrao())
        if args.cmd == "status":
            saida(f"aparelho: {serial} ({'emulador' if _RX_EMULADOR.match(serial) else 'celular'})")
            saida(f"boot completo: {'sim' if disp.boot_completo() else 'não'}")
            w, h = disp.tamanho_tela()
            saida(f"tela: {w}x{h}")
            disp.tela_acesa_e_destravada(tentar=False)
            saida("tela acesa e destravada: sim")
            saida(f"na frente: {disp.app_na_frente() or '?'}")
            return OK
        if args.cmd == "dump":
            nos = disp.dump()
            f = normalizar(args.filtro)
            for n in nos:
                if not (n.texto or n.desc or n.id):
                    continue
                linha = f"{n.x},{n.y} | {n.classe} | {n.texto[:60]} | {n.desc[:60]} | {n.id} | {'clic' if n.clicavel else ''}"
                if not f or f in normalizar(linha):
                    saida(linha)
            return OK
        p = disp.screencap(args.destino)
        saida(f"foto: {p}")
        return OK
    except DispositivoErro as e:
        saida(f"{type(e).__name__}: {e}")
        return int(getattr(e, "codigo", ERRO))


if __name__ == "__main__":
    raise SystemExit(main())
