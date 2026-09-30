"""Testes: hp_studio no sys.path e H:/G: trocados por pastas temporárias."""
import sys as _sys
from pathlib import Path as _Path

_HP = str(_Path(__file__).resolve().parents[2])  # ...\app\hp_studio
if _HP not in _sys.path:
    _sys.path.insert(0, _HP)
from hpbase.pytest_raizes import raizes_temporarias  # noqa: E402,F401  (autouse: H:/G: → pastas temporárias)
