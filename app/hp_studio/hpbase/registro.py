"""Log em arquivo (H:\\HypadoLocal\\app\\logs\\<nome>_AAAA-MM-DD.log).

Todo texto passa por `mascarar` antes de ir para o arquivo: token da Meta,
access_token=..., Bearer ..., chave de API do Google e senha nunca aparecem.
"""
from __future__ import annotations

import logging
import re
from datetime import date

from .caminhos import garantir, pasta_logs

_PADROES = [
    (re.compile(r"(access_token|token|senha|password|key|secret|apikey|api_key)"
                r"(\s*[=:]\s*)([^\s&\"',;]+)", re.I), r"\1\2***"),
    (re.compile(r"Bearer\s+[A-Za-z0-9._\-]+", re.I), "Bearer ***"),
    (re.compile(r"\bEAA[A-Za-z0-9]{20,}"), "EAA***"),        # token da Meta
    (re.compile(r"\bAIza[0-9A-Za-z_\-]{30,}"), "AIza***"),    # chave Google
    (re.compile(r"\bya29\.[0-9A-Za-z_\-]+"), "ya29.***"),     # OAuth Google
]


def mascarar(texto: str) -> str:
    """Troca qualquer coisa com cara de segredo por ***."""
    s = str(texto)
    for rx, troca in _PADROES:
        s = rx.sub(troca, s)
    return s


class _FiltroSegredo(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = mascarar(record.getMessage())
        record.args = ()
        return True


def obter_logger(nome: str) -> logging.Logger:
    """Logger que escreve em logs\\<nome>_<dia>.log (e nunca no console)."""
    lg = logging.getLogger(f"hp.{nome}")
    lg.setLevel(logging.INFO)
    arquivo = garantir(pasta_logs()) / f"{nome}_{date.today():%Y-%m-%d}.log"
    ja_tem = any(isinstance(h, logging.FileHandler)
                 and getattr(h, "baseFilename", "") == str(arquivo.resolve())
                 for h in lg.handlers)
    if not ja_tem:
        for h in list(lg.handlers):  # troca de dia: fecha o arquivo antigo
            lg.removeHandler(h)
            h.close()
        h = logging.FileHandler(arquivo, encoding="utf-8")
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s",
                                         "%Y-%m-%d %H:%M:%S"))
        h.addFilter(_FiltroSegredo())
        lg.addHandler(h)
    lg.propagate = False
    return lg
