"""Leitura de segredos em H:\\HypadoLocal\\segredos\\.

Regra: o valor NUNCA é impresso, logado nem gravado fora dessa pasta.
Formato aceito: arquivo com `CHAVE=valor` por linha (# comenta) ou só o
valor na primeira linha.
"""
from __future__ import annotations

from pathlib import Path

from .caminhos import pasta_segredos


class SegredoAusente(KeyError):
    def __str__(self) -> str:  # a mensagem nunca carrega valor, só o nome
        return f"segredo ausente: {self.args[0]}"


def ler_segredo(arquivo: str, chave: str | None = None,
                pasta: Path | None = None) -> str:
    p = Path(pasta or pasta_segredos()) / arquivo
    if not p.exists():
        raise SegredoAusente(arquivo)
    linhas = [l.strip() for l in p.read_text(encoding="utf-8-sig").splitlines()]
    linhas = [l for l in linhas if l and not l.startswith("#")]
    if chave is None:
        if not linhas:
            raise SegredoAusente(arquivo)
        l = linhas[0]
        return l.split("=", 1)[1].strip() if "=" in l else l
    for l in linhas:
        if "=" in l:
            k, v = l.split("=", 1)
            if k.strip().lower() == chave.lower():
                return v.strip()
    raise SegredoAusente(f"{arquivo}:{chave}")
