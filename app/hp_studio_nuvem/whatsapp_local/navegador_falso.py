"""Navegador de mentira, para testes (nenhuma internet, nenhum WhatsApp).

Simula conversas em memória e registra cada chamada em `chamadas`, para
os testes conferirem o que o enviador fez (e o que ele NÃO fez).
"""
from __future__ import annotations

from pathlib import Path

from .config import nfc
from .navegador import (ConversaNaoEncontrada, ErroEnvio, MensagemLida,
                        Navegador)


class NavegadorFalso(Navegador):
    def __init__(self, conversas: dict | None = None, *, esta_logado: bool = True,
                 login_escaneado: bool = True, titulos: dict | None = None,
                 tipos: dict | None = None, falhas_envio: int = 0,
                 falha_depois_de_enviar: bool = False):
        # conversas: {"nome do grupo": [MensagemLida, ...]}
        self.conversas = {nfc(k): list(v) for k, v in (conversas or {}).items()}
        self.esta_logado = esta_logado
        self.login_escaneado = login_escaneado
        # titulos: força o cabeçalho de um grupo (simula abrir a conversa errada)
        self.titulos = {nfc(k): v for k, v in (titulos or {}).items()}
        # tipos: {"grupo": False} simula contato individual
        self.tipos = {nfc(k): v for k, v in (tipos or {}).items()}
        self.falhas_envio = falhas_envio          # quantos envios vão falhar
        self.falha_depois_de_enviar = falha_depois_de_enviar
        self.aberto = False
        self.atual: str | None = None
        self.chamadas: list[tuple] = []
        self.enviadas: list[dict] = []           # o que "saiu" de verdade

    # --- ciclo de vida
    def abrir(self) -> None:
        self.chamadas.append(("abrir",))
        self.aberto = True

    def fechar(self) -> None:
        self.chamadas.append(("fechar",))
        self.aberto = False

    def logado(self, timeout_s: float = 90) -> bool:
        self.chamadas.append(("logado",))
        return self.esta_logado

    def esperar_login(self, timeout_s: float) -> bool:
        self.chamadas.append(("esperar_login", timeout_s))
        if self.login_escaneado:
            self.esta_logado = True
        return self.esta_logado

    # --- conversa
    def abrir_conversa(self, grupo: str) -> None:
        self.chamadas.append(("abrir_conversa", grupo))
        assert self.aberto, "abrir_conversa com navegador fechado"
        if nfc(grupo) not in self.conversas:
            raise ConversaNaoEncontrada(f"conversa não encontrada: {grupo}")
        self.atual = nfc(grupo)

    def titulo_conversa(self) -> str:
        self.chamadas.append(("titulo_conversa",))
        return self.titulos.get(self.atual, self.atual or "")

    def conversa_e_grupo(self) -> bool | None:
        return self.tipos.get(self.atual, True)

    def _registrar(self, texto: str, anexos: list[Path] | None = None) -> None:
        self.enviadas.append({"grupo": self.atual, "texto": texto,
                              "anexos": [str(a) for a in (anexos or [])]})
        self.conversas[self.atual].append(
            MensagemLida(autor="Antônio", hora=f"10:{len(self.enviadas):02d}, 30/09/2026",
                         texto=texto, saida=True))

    def _talvez_falhar(self, texto: str, anexos=None) -> None:
        if self.falhas_envio > 0:
            self.falhas_envio -= 1
            if self.falha_depois_de_enviar:     # saiu, mas não confirmou
                self._registrar(texto, anexos)
            raise ErroEnvio("envio não confirmou (falso)")

    def enviar_texto(self, texto: str) -> None:
        self.chamadas.append(("enviar_texto", self.atual, len(texto)))
        assert self.aberto and self.atual
        self._talvez_falhar(texto)
        self._registrar(texto)

    def enviar_anexos(self, caminhos: list[Path], legenda: str | None) -> None:
        self.chamadas.append(("enviar_anexos", self.atual, len(caminhos)))
        assert self.aberto and self.atual
        self._talvez_falhar(legenda or "", caminhos)
        self._registrar(legenda or "", caminhos)

    def ler_mensagens(self, limite: int) -> list[MensagemLida]:
        self.chamadas.append(("ler_mensagens", self.atual, limite))
        return list(self.conversas.get(self.atual, []))[-limite:]

    def nomes_chamadas(self) -> list[str]:
        return [c[0] for c in self.chamadas]
