"""Base comum do montador de reels do Futebol | HP (arquivos reel_futebol*.py).

- põe o hpbase no sys.path: primeiro a variável HP_APP (pasta do app ou a
  própria hp_studio_nuvem), depois ../app/hp_studio_nuvem relativo a este arquivo
  (como no repositório) e ../06 Projeto/app/hp_studio_nuvem (como no PC do Antônio);
- constantes do formato de saída (1080x1920, 30 fps, AAC 48 kHz, safe zones);
- exceções do montador.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent


def caminho_hp_studio() -> Path | None:
    """Acha a pasta que contém o pacote hpbase e põe no sys.path."""
    cands: list[Path] = []
    env = os.environ.get("HP_APP")
    if env:
        cands += [Path(env), Path(env) / "hp_studio_nuvem", Path(env) / "hp_studio"]
    cands += [AQUI.parent / "app" / "hp_studio_nuvem",
              AQUI.parent / "06 Projeto" / "app" / "hp_studio_nuvem",
              AQUI.parent / "app" / "hp_studio",
              AQUI.parent / "06 Projeto" / "app" / "hp_studio"]
    for c in cands:
        if (c / "hpbase" / "__init__.py").exists():
            if str(c) not in sys.path:
                sys.path.insert(0, str(c))
            return c
    return None


caminho_hp_studio()

from hpbase import (TravaPesada, TravaOcupada, achar_ffmpeg, agora_iso,  # noqa: E402
                    escrever_json, garantir, ler_json, obter_logger,
                    raiz_drive, raiz_local, rodar, SEM_JANELA)

# ---------------------------------------------------------------- formato
LARGURA, ALTURA = 1080, 1920
FPS = 30
TAXA_AUDIO = 48000
SAFE_TOPO = 250          # topo livre para a interface do Reels
SAFE_BASE = 350          # base livre (legenda do post, botões)
ZONA_Y0 = SAFE_TOPO                 # 250
ZONA_Y1 = ALTURA - SAFE_BASE        # 1570
MARGEM = 60

MODOS = ("gol", "noticia", "debate", "estatistica", "resultado", "tabela")
FONTES_VIDEO_OK = ("oficial_clube", "oficial_cbf", "oficial_liga")
# foto pode ser oficial ou arte própria da HP (nunca print de TV)
FONTES_FOTO_OK = FONTES_VIDEO_OK + ("propria",)
FONTES_PROIBIDAS = ("transmissao_tv", "tv", "print_tv", "transmissao")

NOME_LOG = "reel_futebol"

__all__ = [
    "AQUI", "caminho_hp_studio", "TravaPesada", "TravaOcupada", "achar_ffmpeg",
    "agora_iso", "escrever_json", "garantir", "ler_json", "obter_logger",
    "raiz_drive", "raiz_local", "rodar", "SEM_JANELA", "LARGURA", "ALTURA",
    "FPS", "TAXA_AUDIO", "SAFE_TOPO", "SAFE_BASE", "ZONA_Y0", "ZONA_Y1",
    "MARGEM", "MODOS", "FONTES_VIDEO_OK", "FONTES_FOTO_OK", "FONTES_PROIBIDAS",
    "NOME_LOG", "ErroReel", "RoteiroInvalido", "n_quadros", "dur_exata",
    "log",
]


class ErroReel(RuntimeError):
    """Erro do montador (mensagem sempre em português, sem segredo)."""


class RoteiroInvalido(ErroReel):
    def __init__(self, erros, avisos=()):
        self.erros = list(erros)
        self.avisos = list(avisos)
        super().__init__("roteiro inválido: " + "; ".join(self.erros))


def n_quadros(duracao: float) -> int:
    """Número de quadros (30 fps) de uma duração, no mínimo 1."""
    return max(1, int(round(float(duracao) * FPS)))


def dur_exata(duracao: float) -> float:
    """Arredonda a duração para um número inteiro de quadros."""
    return n_quadros(duracao) / FPS


def log():
    return obter_logger(NOME_LOG)
