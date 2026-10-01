"""Resultado de um trabalho da esteira (o que o motor faz com o item)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

AVANCAR = "avancar"      # move o item para `destino`
AGUARDAR = "aguardar"    # fica onde está (esperando revisor, TikTok...)
FINAL = "final"          # terminou a esteira (07_postados com aviso feito)
ERRO = "erro"            # vai para 99_erros


@dataclass
class Resultado:
    status: str
    destino: str | None = None
    mensagem: str = ""
    dados: dict = field(default_factory=dict)
    permanente: bool = True
    # chamado pelo motor depois do movimento, com o novo caminho do item
    apos_mover: Callable[[Path], None] | None = None

    @classmethod
    def avancar(cls, destino: str, mensagem: str = "", **dados) -> "Resultado":
        return cls(AVANCAR, destino, mensagem, dados)

    @classmethod
    def aguardar(cls, mensagem: str = "", **dados) -> "Resultado":
        return cls(AGUARDAR, None, mensagem, dados)

    @classmethod
    def final(cls, mensagem: str = "", **dados) -> "Resultado":
        return cls(FINAL, None, mensagem, dados)

    @classmethod
    def erro(cls, mensagem: str, permanente: bool = True, **dados) -> "Resultado":
        return cls(ERRO, None, mensagem, dados, permanente)

    @property
    def ok(self) -> bool:
        return self.status != ERRO
