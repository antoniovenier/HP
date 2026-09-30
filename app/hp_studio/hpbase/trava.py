"""Trabalho pesado: 1 por vez (pesado.lock) e nunca das 18h às 22h30."""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, time as hora
from pathlib import Path

from .caminhos import garantir, pasta_app

INICIO_PROIBIDO = hora(18, 0)
FIM_PROIBIDO = hora(22, 30)
TRAVA_VELHA_SEG = 3 * 3600  # trava com mais de 3 h é considerada abandonada


class TravaOcupada(RuntimeError):
    """Outro trabalho pesado está rodando (ou é horário proibido)."""


def janela_proibida(agora: datetime | None = None) -> bool:
    """True das 18:00 até 22:29:59 (horário do PC)."""
    t = (agora or datetime.now()).time()
    return INICIO_PROIBIDO <= t < FIM_PROIBIDO


def _pid_vivo(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        k = ctypes.windll.kernel32  # type: ignore[attr-defined]
        h = k.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        codigo = ctypes.c_ulong()
        k.GetExitCodeProcess(h, ctypes.byref(codigo))
        k.CloseHandle(h)
        return codigo.value == 259  # STILL_ACTIVE
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


class TravaPesada:
    """Uso:  with TravaPesada("esteira:editar"): ...

    - respeita a janela 18h-22h30 (a menos que ignorar_horario=True, usado
      só pelo story, que é leve e pode sair a qualquer hora);
    - cria pesado.lock de forma atômica; se já existe e o dono morreu ou
      a trava tem mais de 3 h, assume a trava.
    """

    def __init__(self, dono: str, caminho: Path | None = None,
                 ignorar_horario: bool = False, agora: datetime | None = None):
        self.dono = dono
        self.caminho = Path(caminho) if caminho else pasta_app() / "pesado.lock"
        self.ignorar_horario = ignorar_horario
        self.agora = agora
        self._minha = False

    def _ler(self) -> dict:
        try:
            return json.loads(self.caminho.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def adquirir(self) -> None:
        if not self.ignorar_horario and janela_proibida(self.agora):
            raise TravaOcupada("horário proibido (18h-22h30) para trabalho pesado")
        garantir(self.caminho.parent)
        dados = json.dumps({"dono": self.dono, "pid": os.getpid(),
                            "desde": time.time()}, ensure_ascii=False)
        for _ in range(2):
            try:
                fd = os.open(self.caminho, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                atual = self._ler()
                velha = time.time() - float(atual.get("desde", 0)) > TRAVA_VELHA_SEG
                if velha or not _pid_vivo(int(atual.get("pid", 0))):
                    try:
                        self.caminho.unlink()
                    except FileNotFoundError:
                        pass
                    continue
                raise TravaOcupada(f"pesado.lock com '{atual.get('dono', '?')}'")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(dados)
            self._minha = True
            return
        raise TravaOcupada("não consegui pegar a trava")

    def soltar(self) -> None:
        if self._minha:
            try:
                if self._ler().get("pid") == os.getpid():
                    self.caminho.unlink()
            except FileNotFoundError:
                pass
            self._minha = False

    def __enter__(self):
        self.adquirir()
        return self

    def __exit__(self, *exc):
        self.soltar()
        return False
