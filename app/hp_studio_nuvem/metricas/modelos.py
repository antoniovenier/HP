"""Formato de um post na foto diária, datas e números."""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime

from hpbase import FUSO

CAMPOS_POST = ("id", "legenda_inicio", "tipo", "publicado_em", "link",
               "curtidas", "comentarios", "views", "salvamentos",
               "compartilhamentos", "alcance")
METRICAS_POST = ("curtidas", "comentarios", "views", "salvamentos",
                 "compartilhamentos", "alcance")
TAM_LEGENDA = 80


class SemToken(Exception):
    """Falta token ou id no arquivo de segredos (vira status sem_token)."""


def inicio_legenda(texto, n: int = TAM_LEGENDA) -> str:
    s = " ".join(str(texto or "").split())
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def ler_data(valor) -> datetime | None:
    """Aceita '2026-09-30T12:00:00+0000', '...Z', ISO com fuso ou sem; devolve em Brasília."""
    if not valor:
        return None
    if isinstance(valor, datetime):
        d = valor
    else:
        s = str(valor).strip().replace("Z", "+00:00")
        s = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", s)
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
            s += "T00:00:00"
        s = s.replace(" ", "T", 1) if "T" not in s else s
        try:
            d = datetime.fromisoformat(s)
        except ValueError:
            for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y"):
                try:
                    d = datetime.strptime(str(valor).strip(), fmt)
                    break
                except ValueError:
                    d = None
            if d is None:
                return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=FUSO)
    return d.astimezone(FUSO)


def iso(d: datetime | None) -> str | None:
    return d.isoformat(timespec="seconds") if d else None


def numero(v):
    """Número de planilha/JSON: 1234, '1.234', '1,2 mil', '3,4K', '1M' → int/float; vazio → None."""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return v
    s = str(v).strip().lower().replace(" ", " ")
    if not s or s in {"-", "—", "n/a", "na", "none", "null"}:
        return None
    mult = 1
    for suf, m in (("mil", 1_000), ("k", 1_000), ("mi", 1_000_000),
                   ("m", 1_000_000), ("bi", 1_000_000_000)):
        if s.endswith(suf):
            mult = m
            s = s[: -len(suf)].strip()
            break
    if mult == 1 and re.fullmatch(r"\d{1,3}([.,]\d{3})+", s):
        s = re.sub(r"[.,]", "", s)          # 1.234.567 (milhar)
    elif "." in s and "," in s:
        s = s.replace(".", "").replace(",", ".")  # 1.234,5 (padrão BR)
    else:
        s = s.replace(",", ".")
    try:
        x = float(s) * mult
    except ValueError:
        return None
    return int(round(x)) if abs(x - round(x)) < 1e-9 else x


def novo_post(id, legenda=None, tipo=None, publicado_em=None, link=None, **metricas) -> dict:
    post = {"id": str(id), "legenda_inicio": inicio_legenda(legenda), "tipo": tipo,
            "publicado_em": iso(ler_data(publicado_em)), "link": link}
    for k in METRICAS_POST:
        post[k] = numero(metricas.pop(k, None))
    post.update(metricas)
    return post


def sem_acento(s: str) -> str:
    n = unicodedata.normalize("NFKD", str(s))
    return "".join(c for c in n if not unicodedata.combining(c)).lower().strip()
