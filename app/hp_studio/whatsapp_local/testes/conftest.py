"""Fixtures dos testes do whatsapp_local (o conftest de app/ já troca
H:\\ e G:\\ por pastas temporárias)."""
from datetime import datetime

import pytest

from hpbase import FUSO, escrever_json
from whatsapp_local.config import GRUPO_COMISSAO, Config, arquivo_grupos, pasta_fila
from whatsapp_local.ritmo import RelogioFalso

from .auxiliares import GRUPO_GTA, nova_msg


@pytest.fixture
def relogio():
    return RelogioFalso(datetime(2026, 9, 30, 10, 0, tzinfo=FUSO))


@pytest.fixture
def grupos():
    # o telefone na lista serve para provar que contato individual é barrado
    escrever_json(arquivo_grupos(), {"grupos": [GRUPO_GTA, "+55 11 91234-5678"]})
    return [GRUPO_COMISSAO, GRUPO_GTA]


@pytest.fixture
def enfileirar():
    def _f(**kw):
        d = nova_msg(**kw)
        escrever_json(pasta_fila() / f"{d['id']}.json", d)
        return d
    return _f


@pytest.fixture
def cfg_real():
    return Config(modo="real", ler_recebidas=False)
