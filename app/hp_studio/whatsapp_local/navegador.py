"""Interface do navegador (o que o enviador precisa da página do WhatsApp).

Toda a lógica (fila, validação, cabeçalho, ritmo, tentativas, recebidas)
fala só com esta interface. Existem duas implementações:
- `NavegadorPlaywright` (navegador_playwright.py): a janela real do
  WhatsApp Web, página oficial, perfil separado;
- `NavegadorFalso` (navegador_falso.py): usado nos testes, sem internet.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


class ErroWhatsApp(Exception):
    """Base dos erros do enviador."""


class NavegadorIndisponivel(ErroWhatsApp):
    """Não deu para abrir o navegador (Playwright ausente, perfil em uso...).
    Erro GERAL: não conta tentativa das mensagens."""


class ConversaNaoEncontrada(ErroWhatsApp):
    """A busca não achou um grupo com esse nome exato."""


class CabecalhoDivergente(ErroWhatsApp):
    """O título da conversa aberta não é o grupo esperado: NÃO envia."""


class NaoEGrupo(ErroWhatsApp):
    """A conversa aberta parece contato individual: NÃO envia."""


class ErroEnvio(ErroWhatsApp):
    """Falha ao digitar/anexar/enviar ou o envio não confirmou."""


@dataclass
class MensagemLida:
    """Uma mensagem lida da conversa aberta."""
    autor: str
    hora: str        # como o WhatsApp mostra: "10:32, 30/09/2026"
    texto: str
    saida: bool      # True = saiu desta conta (celular do Antônio ou o app)


class Navegador(ABC):
    """O que o enviador precisa. Nada aqui digita login: o QR é do Antônio."""

    @abstractmethod
    def abrir(self) -> None:
        """Abre o WhatsApp Web (janela fora da tela, sem som)."""

    @abstractmethod
    def fechar(self) -> None:
        """Fecha a janela (o login fica guardado no perfil)."""

    @abstractmethod
    def logado(self, timeout_s: float = 90) -> bool:
        """True se a lista de conversas apareceu; False se apareceu o QR."""

    @abstractmethod
    def esperar_login(self, timeout_s: float) -> bool:
        """Espera o Antônio escanear o QR (só olha a tela, não digita nada)."""

    @abstractmethod
    def abrir_conversa(self, grupo: str) -> None:
        """Abre a conversa pela busca (clica só no resultado de nome exato)."""

    @abstractmethod
    def titulo_conversa(self) -> str:
        """Título do cabeçalho da conversa aberta (com emoji)."""

    def conversa_e_grupo(self) -> bool | None:
        """True = grupo, False = contato individual, None = não deu para saber."""
        return None

    @abstractmethod
    def enviar_texto(self, texto: str) -> None:
        """Digita e envia o texto na conversa aberta; espera confirmar."""

    @abstractmethod
    def enviar_anexos(self, caminhos: list[Path], legenda: str | None) -> None:
        """Anexa os arquivos (com legenda no primeiro) e envia."""

    @abstractmethod
    def ler_mensagens(self, limite: int) -> list[MensagemLida]:
        """Últimas mensagens de texto da conversa aberta (mais antiga primeiro)."""

    def __enter__(self):
        self.abrir()
        return self

    def __exit__(self, *exc):
        self.fechar()
        return False
