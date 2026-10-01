"""Ritmo de envio: devagar e pouco (parecer gente, não robô).

- nunca menos de 20 s entre uma mensagem e outra;
- no máximo N mensagens por hora (config max_por_hora);
- a contagem fica em ritmo.json, então vale entre processos (o vigiar e o
  `enviar --uma-vez` do Agendador de Tarefas respeitam o mesmo teto).

O relógio é injetável: nos testes o RelogioFalso "dorme" sem esperar.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta
from pathlib import Path

from hpbase import FUSO, agora, escrever_json, ler_json

from .config import INTERVALO_MIN_ABSOLUTO, arquivo_ritmo

UMA_HORA = timedelta(hours=1)


class Relogio:
    def agora(self) -> datetime:
        return agora()

    def dormir(self, segundos: float) -> None:
        if segundos > 0:
            time.sleep(segundos)


class RelogioFalso(Relogio):
    """Relógio de teste: dormir() só avança o ponteiro."""

    def __init__(self, inicio: datetime | None = None):
        self.t = inicio or datetime(2026, 9, 30, 10, 0, tzinfo=FUSO)
        self.dormidas: list[float] = []

    def agora(self) -> datetime:
        return self.t

    def dormir(self, segundos: float) -> None:
        self.dormidas.append(segundos)
        if segundos > 0:
            self.t += timedelta(seconds=segundos)

    def avancar(self, **kw) -> None:
        self.t += timedelta(**kw)


class ControleRitmo:
    def __init__(self, relogio: Relogio | None = None, intervalo_min_seg: float = 20,
                 max_por_hora: int = 10, arquivo: Path | None = None):
        self.relogio = relogio or Relogio()
        self.intervalo = max(float(INTERVALO_MIN_ABSOLUTO), float(intervalo_min_seg))
        self.max_por_hora = max(1, int(max_por_hora))
        self.arquivo = Path(arquivo) if arquivo else arquivo_ritmo()

    # --------------------------------------------------------- estado
    def _carregar(self) -> list[datetime]:
        dados = ler_json(self.arquivo, {}) or {}
        saida = []
        for s in dados.get("envios", []) if isinstance(dados, dict) else []:
            try:
                d = datetime.fromisoformat(s)
                saida.append(d if d.tzinfo else d.replace(tzinfo=FUSO))
            except (TypeError, ValueError):
                continue
        return sorted(saida)

    def _salvar(self, envios: list[datetime]) -> None:
        limite = self.relogio.agora() - 2 * UMA_HORA
        escrever_json(self.arquivo, {"envios": [d.isoformat(timespec="seconds")
                                                for d in envios if d >= limite]})

    def envios_ultima_hora(self) -> list[datetime]:
        agora_ = self.relogio.agora()
        return [d for d in self._carregar() if agora_ - d < UMA_HORA]

    # --------------------------------------------------------- decisão
    def situacao(self) -> tuple[str, float]:
        """("ok", 0) | ("intervalo", segundos a esperar) | ("limite_hora", segundos)."""
        agora_ = self.relogio.agora()
        todos = self._carregar()
        hora = [d for d in todos if agora_ - d < UMA_HORA]
        if len(hora) >= self.max_por_hora:
            libera = hora[0] + UMA_HORA
            return "limite_hora", max(0.0, (libera - agora_).total_seconds())
        if todos:
            passou = (agora_ - todos[-1]).total_seconds()
            if 0 <= passou < self.intervalo:
                return "intervalo", self.intervalo - passou
            if passou < 0:        # relógio voltou para trás: espera o intervalo cheio
                return "intervalo", self.intervalo
        return "ok", 0.0

    def esperar_vez(self) -> bool:
        """Dorme o intervalo se precisar. False = bateu o teto da hora (não
        dorme 1 hora: o ciclo acaba e as mensagens ficam para o próximo)."""
        for _ in range(5):
            estado, espera = self.situacao()
            if estado == "ok":
                return True
            if estado == "limite_hora":
                return False
            self.relogio.dormir(espera)
        return self.situacao()[0] == "ok"

    def registrar_envio(self) -> None:
        envios = self._carregar()
        envios.append(self.relogio.agora())
        self._salvar(envios)
