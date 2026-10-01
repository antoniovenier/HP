"""Caminhos da operação HP.

No PC do Antônio: pesado em H:\\HypadoLocal, Drive em G:\\Meu Drive\\Hypado.
Em teste (ou em outra máquina) as variáveis de ambiente HP_LOCAL e HP_DRIVE
mudam a raiz — assim nenhum teste toca no H: ou no G: de verdade.
"""
from __future__ import annotations

import os
from pathlib import Path

PADRAO_LOCAL = r"H:\HypadoLocal"
PADRAO_DRIVE = r"G:\Meu Drive\Hypado"


def raiz_local() -> Path:
    return Path(os.environ.get("HP_LOCAL", PADRAO_LOCAL))


def raiz_drive() -> Path:
    return Path(os.environ.get("HP_DRIVE", PADRAO_DRIVE))


def garantir(p: Path) -> Path:
    """Cria a pasta (e as de cima) se não existir e devolve o caminho."""
    p = Path(p)
    p.mkdir(parents=True, exist_ok=True)
    return p


def pasta_app() -> Path:
    return raiz_local() / "app"


def pasta_logs() -> Path:
    return pasta_app() / "logs"


def pasta_segredos() -> Path:
    return raiz_local() / "segredos"
