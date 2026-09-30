"""Falsos e atalhos dos testes da esteira (o conftest de app/ já aponta
HP_LOCAL e HP_DRIVE para pastas temporárias)."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from esteira import simulados, vigia
from esteira.config import carregar_config
from esteira.motor import Esteira
from esteira.pastas import ler_nome
from esteira.plugins import Plugins

TIMEOUTS_TESTE = {"ffmpeg": 90, "ffmpeg_curto": 30, "baixar": 30, "dublar": 30,
                  "falar": 30, "estaticos": 30}
MANHA = datetime(2026, 9, 30, 10, 0)
NOITE = datetime(2026, 9, 30, 19, 0)


def pedido_reel(**kw) -> dict:
    p = {"canal": "gta", "tipo": "reel", "prioridade": "P1",
         "titulo": "Rockstar quinta", "fonte_url": "https://www.youtube.com/watch?v=x",
         "credito": "@rockstargames", "redes": ["instagram", "tiktok"],
         "horario_alvo": "2026-09-30T18:30:00-03:00", "dublar": False,
         "narrar_toque_hp": False, "observacoes": ""}
    p.update(kw)
    return p


def pedido_carrossel(**kw) -> dict:
    p = {"canal": "receitas", "tipo": "carrossel", "prioridade": "P1",
         "titulo": "5 bolos de caneca", "redes": ["instagram", "pinterest"],
         "horario_alvo": "2026-09-30T12:00:00-03:00",
         "laminas": [{"texto": "1"}, {"texto": "2"}, {"texto": "3"}]}
    p.update(kw)
    return p


def _nome_item(args) -> str | None:
    for a in args:
        if isinstance(a, (str, Path)) and ("/" in str(a) or "\\" in str(a)):
            p = Path(a)
            for q in [p, *p.parents]:
                if ler_nome(q.name):
                    return q.name
    return None


class Espiao:
    """Embrulha um plugin e anota (plugin, método, item) de cada chamada."""

    def __init__(self, nome, alvo, chamadas):
        self._nome, self._alvo, self._chamadas = nome, alvo, chamadas

    def __getattr__(self, attr):
        f = getattr(self._alvo, attr)
        if not callable(f):
            return f

        def chamar(*a, **kw):
            self._chamadas.append((self._nome, attr, _nome_item(a)))
            return f(*a, **kw)
        return chamar


def plugins_espionados(cfg, chamadas, **troca) -> Plugins:
    base = simulados.plugins_simulados(cfg)
    campos = {}
    for nome in ("baixador", "midia", "legendador", "dublador", "narrador", "editor",
                 "designer", "agendador", "avisador"):
        alvo = troca.get(nome, getattr(base, nome))
        campos[nome] = Espiao(nome, alvo, chamadas)
    return Plugins(**campos)


@pytest.fixture(autouse=True)
def ffmpeg_com_teto(monkeypatch):
    """Nenhum ffmpeg dos testes da esteira passa de 90 s (nunca fica pendurado)."""
    monkeypatch.setenv("HP_FFMPEG_TIMEOUT_MAX", "90")


@pytest.fixture
def amb():
    cfg = carregar_config()
    cfg.editor["preset"] = "ultrafast"
    cfg.timeouts.update(TIMEOUTS_TESTE)  # ffmpeg nunca fica pendurado nos testes
    cfg.garantir_pastas()
    chamadas: list = []
    ns = SimpleNamespace(cfg=cfg, chamadas=chamadas)
    ns.plugins = plugins_espionados(cfg, chamadas)

    def trocar(**troca):
        ns.plugins = plugins_espionados(cfg, chamadas, **troca)
        return ns.plugins

    def esteira(agora=MANHA):
        return Esteira(cfg, ns.plugins, agora=agora)

    def ciclo(agora=MANHA, **kw):
        return vigia.ciclo(cfg, plugins=ns.plugins, agora=agora, **kw)

    def pasta(etapa):
        return cfg.pasta(etapa)

    def itens(etapa):
        return sorted(p.name for p in cfg.pasta(etapa).iterdir()
                      if p.is_dir() and not p.name.startswith((".", "_")))

    ns.trocar, ns.esteira, ns.ciclo, ns.pasta, ns.itens = trocar, esteira, ciclo, pasta, itens
    return ns
