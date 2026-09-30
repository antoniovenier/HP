"""JSON atômico, hora de Brasília e histórico em linha."""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
    FUSO = ZoneInfo("America/Sao_Paulo")
except Exception:  # Windows sem tzdata: Brasília sem horário de verão
    FUSO = timezone(timedelta(hours=-3), "BRT")


def agora() -> datetime:
    return datetime.now(FUSO)


def agora_iso() -> str:
    return agora().isoformat(timespec="seconds")


def ler_json(p: Path, padrao=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return padrao
    except json.JSONDecodeError:
        if padrao is not None:
            return padrao
        raise


def escrever_json(p: Path, dados) -> Path:
    """Grava em arquivo temporário e troca (nunca deixa JSON pela metade)."""
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp_", dir=p.parent)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    os.replace(tmp, p)
    return p


def anexar_linha(p: Path, texto: str) -> None:
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(f"{agora_iso()} {texto}\n")
