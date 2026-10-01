"""Mensagens novas do Antônio nos grupos HP → arquivo (nunca responde nada).

Grava em H:\\HypadoLocal\\whatsapp_local\\recebidas\\AAAA-MM-DD.jsonl, uma
linha JSON por mensagem:
    {"hash", "grupo", "autor", "hora", "direcao", "texto", "lido_em"}
- pula as mensagens do próprio app/plantão (começam com "*Claude - *");
- não duplica: hash de grupo + autor + hora + texto (quem já está em
  qualquer arquivo da pasta não entra de novo);
- o LOG só recebe hash e tamanho (nunca o texto) — privacidade.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime
from pathlib import Path

from hpbase import garantir, obter_logger

from .config import PREFIXO, nfc, pasta_recebidas
from .navegador import MensagemLida

_FORMATACAO = re.compile(r"[*_~]")
_RX_DATA = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")


def e_mensagem_claude(texto: str) -> bool:
    """True se é mensagem do app/plantão. Na tela, "*Claude - *" pode vir
    sem os asteriscos (o WhatsApp transforma em negrito)."""
    t = nfc(texto)
    return t.startswith(PREFIXO) or _FORMATACAO.sub("", t).lstrip().startswith("Claude - ")


def hash_mensagem(grupo: str, autor: str, hora: str, texto: str) -> str:
    base = "\x1f".join(nfc(x) for x in (grupo, autor, hora, texto))
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def hash_curto(texto: str) -> str:
    """Para log: identifica sem mostrar o conteúdo."""
    return hashlib.sha256(nfc(texto).encode("utf-8")).hexdigest()[:12]


def data_da_hora(hora: str) -> date | None:
    """ "10:32, 30/09/2026" → date(2026, 9, 30)."""
    m = _RX_DATA.search(hora or "")
    if not m:
        return None
    try:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None


class ArquivoRecebidas:
    def __init__(self, pasta: Path | None = None):
        self.pasta = Path(pasta) if pasta else pasta_recebidas()

    def hashes_existentes(self) -> set[str]:
        vistos: set[str] = set()
        if not self.pasta.exists():
            return vistos
        for arq in self.pasta.glob("*.jsonl"):
            for linha in arq.read_text(encoding="utf-8").splitlines():
                try:
                    h = json.loads(linha).get("hash")
                except (json.JSONDecodeError, AttributeError):
                    continue
                if h:
                    vistos.add(h)
        return vistos

    def salvar(self, grupo: str, mensagens: list[MensagemLida],
               lido_em: datetime) -> int:
        """Anexa só as novas; devolve quantas entraram."""
        lg = obter_logger("whatsapp")
        vistos = self.hashes_existentes()
        novas = 0
        for m in mensagens:
            texto = (m.texto or "").strip()
            if not texto or e_mensagem_claude(texto):
                continue
            h = hash_mensagem(grupo, m.autor, m.hora, texto)
            if h in vistos:
                continue
            dia = data_da_hora(m.hora) or lido_em.date()
            reg = {"hash": h, "grupo": nfc(grupo), "autor": m.autor, "hora": m.hora,
                   "direcao": "saida" if m.saida else "entrada", "texto": texto,
                   "lido_em": lido_em.isoformat(timespec="seconds")}
            arq = garantir(self.pasta) / f"{dia.isoformat()}.jsonl"
            with open(arq, "a", encoding="utf-8") as f:
                f.write(json.dumps(reg, ensure_ascii=False) + "\n")
            vistos.add(h)
            novas += 1
            lg.info("recebida nova: grupo=%s hash=%s tamanho=%d", nfc(grupo), h[:12], len(texto))
        return novas

    def resumo(self) -> dict[str, int]:
        """{"2026-09-30": 3, ...} — quantas mensagens salvas por dia."""
        if not self.pasta.exists():
            return {}
        return {a.stem: sum(1 for l in a.read_text(encoding="utf-8").splitlines() if l.strip())
                for a in sorted(self.pasta.glob("*.jsonl"))}
