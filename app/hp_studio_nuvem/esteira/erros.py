"""Erros da esteira.

- ErroEtapa: falha que pode passar tentando de novo (rede caiu, arquivo
  aberto por outro programa...). O item fica na etapa e é tentado de novo no
  próximo ciclo, até `max_tentativas`; depois vai para 99_erros.
- ErroPermanente: não adianta tentar de novo (pedido inválido, programa não
  instalado, regra de conteúdo quebrada). Vai direto para 99_erros.
"""
from __future__ import annotations


class ErroEsteira(Exception):
    """Base de todos os erros da esteira."""


class ErroEtapa(ErroEsteira):
    """Falha transitória: tenta de novo no próximo ciclo."""


class ErroPermanente(ErroEsteira):
    """Falha definitiva: vai direto para 99_erros."""


class PedidoInvalido(ErroPermanente, ValueError):
    """pedido.json fora do esquema ou quebrando regra de conteúdo."""

    def __init__(self, erros):
        if isinstance(erros, str):
            erros = [erros]
        self.erros = list(erros)
        super().__init__("pedido inválido: " + "; ".join(self.erros))


class ItemNaoEncontrado(ErroEsteira, LookupError):
    """Nenhum item com esse nome em nenhuma etapa."""
