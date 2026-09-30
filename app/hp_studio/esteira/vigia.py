"""Vigia: roda ciclos da esteira (uma vez ou a cada N segundos).

Só um vigia por vez (esteira\\.vigia.lock, mesma lógica do pesado.lock:
trava de processo morto ou com mais de 3 h é assumida). A trava do vigia
não tem horário proibido — o que respeita 18h-22h30 é cada trabalho pesado.
"""
from __future__ import annotations

import time
from datetime import datetime
from typing import Callable

from hpbase import TravaOcupada, TravaPesada, obter_logger

from .config import Config, carregar_config


def com_trava_vigia(cfg: Config, fn: Callable):
    """Roda fn() segurando a trava do vigia. Devolve (True, retorno) ou
    (False, motivo) se outro vigia estiver rodando."""
    cfg.garantir_pastas()
    try:
        with TravaPesada("esteira:vigia", caminho=cfg.trava_vigia, ignorar_horario=True):
            return True, fn()
    except TravaOcupada as e:
        return False, f"outro vigia está rodando ({e})"


def ciclo(cfg: Config | None = None, simular: bool = False, agora: datetime | None = None,
          plugins=None, max_trabalhos: int | None = None) -> dict:
    """Uma passada em todas as etapas (P0 primeiro, trava do pesado, janela)."""
    from .motor import Esteira
    cfg = cfg or carregar_config()
    ok, r = com_trava_vigia(cfg, lambda: Esteira(cfg, plugins, simular, agora)
                            .ciclo(max_trabalhos))
    if not ok:
        return {"ocupado": True, "mensagem": r}
    return r


def vigiar(intervalo: float = 30, uma_vez: bool = False, simular: bool = False,
           cfg: Config | None = None, parar: Callable[[], bool] | None = None,
           dormir: Callable[[float], None] = time.sleep, max_ciclos: int | None = None,
           ao_terminar_ciclo: Callable[[dict], None] | None = None) -> list[dict]:
    """Loop do vigia. `parar`/`max_ciclos` existem para os testes."""
    log = obter_logger("esteira")
    log.info("vigia iniciado (intervalo %ss, simular=%s)", intervalo, simular)
    resumos = []
    n = 0
    while True:
        try:
            r = ciclo(cfg or carregar_config(), simular=simular)
        except Exception as e:  # noqa: BLE001 — o vigia nunca morre por um ciclo ruim
            log.exception("ciclo falhou: %s", e)
            r = {"erro_ciclo": str(e)}
        resumos.append(r)
        if ao_terminar_ciclo:
            ao_terminar_ciclo(r)
        n += 1
        if uma_vez or (max_ciclos is not None and n >= max_ciclos) or (parar and parar()):
            return resumos
        dormir(max(1.0, float(intervalo)))
        if parar and parar():
            return resumos
