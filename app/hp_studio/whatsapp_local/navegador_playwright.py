"""Navegador REAL: a página oficial web.whatsapp.com numa janela própria.

- Playwright `launch_persistent_context` com perfil separado em
  H:\\HypadoLocal\\whatsapp_perfil (o login do QR fica guardado ali);
- janela fora da tela e minimizada, som mudo; o código nunca traz a janela
  para frente (não existe chamada de "trazer para frente" neste arquivo);
- nenhum login é digitado: o QR é escaneado pelo Antônio no comando `login`;
- nenhuma biblioteca que imita protocolo (Baileys, whatsapp-web.js, yowsup...):
  só automação do navegador na página oficial;
- o Playwright é importado SÓ dentro de `abrir()` (import tardio), para os
  testes e o modo sombra rodarem sem ele instalado.

Os seletores ficam em seletores.py (é lá que se conserta quando o WhatsApp muda).
"""
from __future__ import annotations

import re
import time
from pathlib import Path

from hpbase import garantir

from . import seletores as S
from .config import URL_WHATSAPP, nfc, pasta_perfil
from .navegador import (CabecalhoDivergente, ConversaNaoEncontrada, ErroEnvio,
                        MensagemLida, Navegador, NavegadorIndisponivel)

EXT_MIDIA = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4", ".mov", ".m4v", ".3gp"}

# Sempre: sem som, sem pedido de notificação, sem o Chrome "dormir" a
# página por estar fora da tela.
ARGS_BASE = [
    "--mute-audio",
    "--disable-notifications",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding",
]
# Uso normal (nunca em primeiro plano): janela fora da tela e minimizada.
ARGS_FORA_DA_TELA = ["--window-position=-32000,-32000", "--start-minimized"]


def opcoes_lancamento(perfil: Path, visivel: bool = False,
                      canal: str | None = None) -> dict:
    """Parâmetros do launch_persistent_context (função pura, testada).

    visivel=True só no comando `login` (o Antônio precisa ver o QR).
    canal="chrome" usa o Google Chrome instalado em vez do Chromium do Playwright.
    """
    args = list(ARGS_BASE)
    if not visivel:
        args += ARGS_FORA_DA_TELA
    op = {
        "user_data_dir": str(perfil),
        "headless": False,
        "args": args,
        "locale": "pt-BR",
        "timezone_id": "America/Sao_Paulo",
        "viewport": {"width": 1280, "height": 900},
    }
    if canal:
        op["channel"] = canal
    return op


def classificar_subtitulo(texto: str) -> bool | None:
    """Linha de baixo do cabeçalho → True grupo, False contato, None não sei."""
    t = nfc(texto).lower()
    if not t:
        return None
    if ("dados do contato" in t or "contact info" in t or t == "online"
            or t.startswith(("visto por último", "visto hoje", "visto ontem",
                             "last seen"))):
        return False
    if "grupo" in t or "group" in t or "," in t:
        return True
    return None


class NavegadorPlaywright(Navegador):
    def __init__(self, perfil: Path | None = None, *, visivel: bool = False,
                 canal: str | None = None, timeout_ms: int = 30000):
        self.perfil = Path(perfil) if perfil else pasta_perfil()
        self.visivel = visivel
        self.canal = canal
        self.timeout_ms = timeout_ms
        self._pw = None
        self._ctx = None
        self._page = None
        self._grupo_atual: str | None = None   # só vale depois de conferido

    # ------------------------------------------------------------ ciclo
    def abrir(self) -> None:
        try:
            from playwright.sync_api import sync_playwright  # import tardio
        except ImportError as e:
            raise NavegadorIndisponivel(
                "Playwright não instalado: rode 'pip install playwright' e "
                "'python -m playwright install chromium'") from e
        garantir(self.perfil)
        try:
            self._pw = sync_playwright().start()
            self._ctx = self._pw.chromium.launch_persistent_context(
                **opcoes_lancamento(self.perfil, self.visivel, self.canal))
            self._ctx.set_default_timeout(self.timeout_ms)
            self._page = self._ctx.pages[0] if self._ctx.pages else self._ctx.new_page()
            self._page.goto(URL_WHATSAPP, wait_until="domcontentloaded", timeout=90000)
        except Exception as e:
            self.fechar()
            raise NavegadorIndisponivel(
                f"não consegui abrir o WhatsApp Web: {type(e).__name__}: {e}") from e

    def fechar(self) -> None:
        for obj, metodo in ((self._ctx, "close"), (self._pw, "stop")):
            try:
                if obj is not None:
                    getattr(obj, metodo)()
            except Exception:
                pass
        self._pw = self._ctx = self._page = None
        self._grupo_atual = None

    # --------------------------------------------------------- auxiliares
    def _pagina(self):
        if self._page is None:
            raise ErroEnvio("navegador não está aberto")
        return self._page

    def _algum_visivel(self, lista: list[str]) -> bool:
        for sel in lista:
            try:
                if self._page.locator(sel).first.is_visible():
                    return True
            except Exception:
                continue
        return False

    def _achar(self, lista: list[str], nome: str, timeout_s: float = 15,
               visivel: bool = True):
        """Primeiro seletor da lista que existir (e estiver visível)."""
        p = self._pagina()
        fim = time.monotonic() + timeout_s
        while True:
            for sel in lista:
                try:
                    loc = p.locator(sel)
                    if loc.count() == 0:
                        continue
                    el = loc.first
                    if not visivel or el.is_visible():
                        return el
                except Exception:
                    continue
            if time.monotonic() >= fim:
                raise ErroEnvio(f"elemento não encontrado: {nome} (ver seletores.py)")
            p.wait_for_timeout(300)

    @staticmethod
    def _texto(el) -> str:
        return el.evaluate(S.JS_TEXTO_COM_EMOJI) or ""

    def _digitar(self, texto: str) -> None:
        """Insere o texto; quebra de linha = Shift+Enter (Enter enviaria)."""
        kb = self._pagina().keyboard
        for i, linha in enumerate(texto.split("\n")):
            if i:
                kb.press("Shift+Enter")
            if linha:
                kb.insert_text(linha)

    def _limpar_campo(self) -> None:
        kb = self._pagina().keyboard
        kb.press("Control+A")
        kb.press("Backspace")

    def _ultima_saida(self) -> dict:
        try:
            return self._pagina().evaluate(S.JS_ULTIMA_SAIDA) or {}
        except Exception:
            return {}

    def _esperar_confirmacao(self, antes: dict, timeout_s: float = 60) -> None:
        """Espera surgir uma mensagem NOVA desta conta, já sem o relógio."""
        p = self._pagina()
        fim = time.monotonic() + timeout_s
        while time.monotonic() < fim:
            agora = self._ultima_saida()
            if agora.get("id") and agora.get("id") != antes.get("id") \
                    and not agora.get("pendente"):
                return
            p.wait_for_timeout(500)
        raise ErroEnvio("o envio não confirmou a tempo (relógio não sumiu)")

    def _conferir_de_novo(self) -> None:
        """Última conferência do cabeçalho, logo antes de clicar em Enviar."""
        if not self._grupo_atual or nfc(self.titulo_conversa()) != self._grupo_atual:
            try:
                self._limpar_campo()
            except Exception:
                pass
            raise CabecalhoDivergente("o cabeçalho mudou antes de enviar; nada enviado")

    # ------------------------------------------------------------- login
    def logado(self, timeout_s: float = 90) -> bool:
        p = self._pagina()
        fim = time.monotonic() + timeout_s
        while time.monotonic() < fim:
            if self._algum_visivel(S.LISTA_CONVERSAS):
                return True
            if self._algum_visivel(S.QR_CODE):
                return False
            p.wait_for_timeout(500)
        return False

    def esperar_login(self, timeout_s: float) -> bool:
        """Só OLHA a tela até a lista de conversas aparecer (QR escaneado)."""
        p = self._pagina()
        fim = time.monotonic() + timeout_s
        while time.monotonic() < fim:
            if self._algum_visivel(S.LISTA_CONVERSAS):
                p.wait_for_timeout(10000)   # tempo de o WhatsApp gravar a sessão no perfil
                return True
            p.wait_for_timeout(1000)
        return False

    # ---------------------------------------------------------- conversa
    def abrir_conversa(self, grupo: str) -> None:
        p = self._pagina()
        self._grupo_atual = None
        alvo = nfc(grupo)
        try:
            p.keyboard.press("Escape")      # fecha conversa/busca anterior
        except Exception:
            pass
        caixa = self._achar(S.CAIXA_BUSCA, "CAIXA_BUSCA")
        caixa.click()
        self._limpar_campo()
        p.keyboard.insert_text(alvo)
        fim = time.monotonic() + 15
        while time.monotonic() < fim:
            p.wait_for_timeout(700)
            for sel in S.TITULOS_RESULTADO:
                try:
                    itens = p.locator(sel).all()[:40]
                except Exception:
                    continue
                for el in itens:
                    try:
                        if nfc(self._texto(el)) == alvo and el.is_visible():
                            el.click()
                            self._achar(S.CABECALHO_CONVERSA, "CABECALHO_CONVERSA")
                            p.wait_for_timeout(1500)
                            self._grupo_atual = alvo
                            return
                    except Exception:
                        continue
        raise ConversaNaoEncontrada(f"a busca não achou o grupo com nome exato: {grupo}")

    def _ler_titulo(self) -> str:
        for sel in S.TITULO_CONVERSA:
            try:
                loc = self._page.locator(sel)
                if loc.count() == 0:
                    continue
                t = self._texto(loc.first)
                if t and t.strip():
                    return t
            except Exception:
                continue
        return ""

    def titulo_conversa(self) -> str:
        """Lê o título 2 vezes; se mudou no meio (troca de conversa), devolve
        vazio — e vazio nunca bate com o grupo, então nada é enviado."""
        p = self._pagina()
        a = self._ler_titulo()
        p.wait_for_timeout(800)
        b = self._ler_titulo()
        return b if nfc(a) == nfc(b) else ""

    def conversa_e_grupo(self) -> bool | None:
        p = self._pagina()
        for sel in S.MARCADOR_GRUPO:
            try:
                if p.locator(sel).count():
                    return True
            except Exception:
                continue
        for sel in S.SUBTITULO_CONVERSA:
            try:
                loc = p.locator(sel)
                if loc.count():
                    r = classificar_subtitulo(self._texto(loc.first))
                    if r is not None:
                        return r
            except Exception:
                continue
        return None

    # ------------------------------------------------------------- envio
    def enviar_texto(self, texto: str) -> None:
        p = self._pagina()
        if not self._grupo_atual:
            raise ErroEnvio("nenhuma conversa conferida aberta")
        caixa = self._achar(S.CAIXA_MENSAGEM, "CAIXA_MENSAGEM")
        caixa.click()
        self._limpar_campo()                 # tira rascunho antigo
        self._digitar(texto)
        p.wait_for_timeout(1500)             # prévia de link carregar
        self._conferir_de_novo()
        antes = self._ultima_saida()
        self._achar(S.BOTAO_ENVIAR, "BOTAO_ENVIAR").click()
        self._esperar_confirmacao(antes)

    def enviar_anexos(self, caminhos: list[Path], legenda: str | None) -> None:
        p = self._pagina()
        if not self._grupo_atual:
            raise ErroEnvio("nenhuma conversa conferida aberta")
        midias = [Path(c) for c in caminhos if Path(c).suffix.lower() in EXT_MIDIA]
        docs = [Path(c) for c in caminhos if Path(c).suffix.lower() not in EXT_MIDIA]
        primeira = True
        for lote, campos in ((midias, S.INPUT_ARQUIVO_MIDIA),
                             (docs, S.INPUT_ARQUIVO_DOCUMENTO)):
            if not lote:
                continue
            self._conferir_de_novo()         # confere com a conversa ainda visível
            self._achar(S.BOTAO_ANEXAR, "BOTAO_ANEXAR").click()
            p.wait_for_timeout(800)
            campo = self._achar(campos, "INPUT_ARQUIVO", visivel=False)
            campo.set_input_files([str(c) for c in lote])
            p.wait_for_timeout(2000)
            if primeira and legenda:
                cx = self._achar(S.LEGENDA_ANEXO, "LEGENDA_ANEXO")
                cx.click()
                self._digitar(legenda)
            antes = self._ultima_saida()
            self._achar(S.BOTAO_ENVIAR_ANEXO, "BOTAO_ENVIAR_ANEXO").click()
            self._esperar_confirmacao(antes, timeout_s=180)
            primeira = False

    # ----------------------------------------------------------- leitura
    def ler_mensagens(self, limite: int) -> list[MensagemLida]:
        p = self._pagina()
        try:
            dados = p.evaluate(S.JS_LER_MENSAGENS, int(limite)) or []
        except Exception as e:
            raise ErroEnvio(f"não consegui ler as mensagens: {type(e).__name__}") from e
        rx = re.compile(S.REGEX_PRE_TEXTO)
        saida = []
        for d in dados:
            m = rx.match(d.get("pre") or "")
            saida.append(MensagemLida(
                autor=m.group("autor").strip() if m else "",
                hora=m.group("hora").strip() if m else "",
                texto=(d.get("texto") or "").strip(),
                saida=bool(d.get("saida"))))
        return saida
