"""Trabalho pesado: 1 por vez (pesado.lock) e nunca das 18h às 22h30.

O pesado.lock é compartilhado com os scripts do PC, que gravam
    {"quem": "cortar.py", "desde": "AAAA-MM-DDTHH:MM"}            (sem pid; abandonada após 30 min)
e a rodada 1 gravava
    {"dono": "esteira:editar", "pid": 1234, "desde": <epoch>}     (com pid; morto ou mais de 3 h)
Agora lê os DOIS e grava os campos dos dois: quem + desde (ISO) + dono + pid + desde_epoch.
Trava ilegível (JSON quebrado, data absurda) usa a data de modificação do arquivo e NUNCA
é considerada velha de graça. O relógio é injetável (`agora=`) para os testes.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, time as hora
from pathlib import Path

from .caminhos import garantir, pasta_app

INICIO_PROIBIDO = hora(18, 0)
FIM_PROIBIDO = hora(22, 30)
TRAVA_VELHA_SEG = 3 * 3600       # com pid: dono morto OU mais de 3 h = abandonada
TRAVA_SEM_PID_SEG = 30 * 60      # formato do PC (sem pid): mais de 30 min = abandonada
FORMATO_DESDE = "%Y-%m-%dT%H:%M"


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


def _desde(dados: dict, mtime: float) -> tuple[datetime, bool]:
    """(quando a trava começou, legível?) em hora local sem fuso. Qualquer coisa estranha
    (texto fora do formato, epoch absurdo) cai na data de modificação do arquivo."""
    candidatos = [dados.get("desde_epoch"), dados.get("desde")]
    for bruto in candidatos:
        if bruto is None or isinstance(bruto, bool):
            continue
        try:
            if isinstance(bruto, (int, float)):
                return datetime.fromtimestamp(float(bruto)), True
            txt = str(bruto).strip()
            try:
                return datetime.strptime(txt, FORMATO_DESDE), True
            except ValueError:
                d = datetime.fromisoformat(txt)
                return (d.astimezone().replace(tzinfo=None) if d.tzinfo else d), True
        except (OverflowError, OSError, ValueError, TypeError):
            continue
    return datetime.fromtimestamp(mtime), False


def ler_trava(caminho: Path) -> dict | None:
    """{"quem", "pid", "desde": datetime, "legivel": bool} do pesado.lock; None se não existe."""
    caminho = Path(caminho)
    try:
        mtime = caminho.stat().st_mtime
        bruto = caminho.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        return None
    except OSError:
        return {"quem": "?", "pid": 0, "desde": datetime.now(), "legivel": False}
    try:
        dados = json.loads(bruto)
        if not isinstance(dados, dict):
            dados = {}
    except (json.JSONDecodeError, ValueError):
        dados = {}
    desde, legivel = _desde(dados, mtime)
    try:
        pid = int(dados.get("pid") or 0)
    except (TypeError, ValueError):
        pid = 0
    quem = str(dados.get("quem") or dados.get("dono") or "?")
    return {"quem": quem, "pid": pid, "desde": desde, "legivel": legivel and bool(dados)}


def trava_abandonada(info: dict, agora: datetime) -> bool:
    """Sem pid (formato do PC ou ilegível): mais de 30 min. Com pid: processo morto ou mais de 3 h."""
    idade = (agora - info["desde"]).total_seconds()
    if info["pid"]:
        return idade > TRAVA_VELHA_SEG or not _pid_vivo(info["pid"])
    return idade > TRAVA_SEM_PID_SEG


class TravaPesada:
    """Uso:  with TravaPesada("esteira:editar"): ...

    - respeita a janela 18h-22h30 (a menos que ignorar_horario=True, usado
      só pelo story, que é leve e pode sair a qualquer hora);
    - cria pesado.lock de forma atômica; se já existe e está abandonada
      (ver trava_abandonada), assume a trava;
    - `agora` (datetime, hora local) é o relógio: vale para a janela e para
      a idade da trava — os testes não dependem do relógio de verdade.
    """

    def __init__(self, dono: str, caminho: Path | None = None,
                 ignorar_horario: bool = False, agora: datetime | None = None):
        self.dono = dono
        self.caminho = Path(caminho) if caminho else pasta_app() / "pesado.lock"
        self.ignorar_horario = ignorar_horario
        self.agora = agora
        self._minha = False

    def _agora(self) -> datetime:
        return self.agora or datetime.now()

    def _ler(self) -> dict | None:
        return ler_trava(self.caminho)

    def adquirir(self) -> None:
        agora = self._agora()
        if not self.ignorar_horario and janela_proibida(agora):
            raise TravaOcupada("horário proibido (18h-22h30) para trabalho pesado")
        garantir(self.caminho.parent)
        dados = json.dumps({"quem": self.dono, "desde": agora.strftime(FORMATO_DESDE),
                            "dono": self.dono, "pid": os.getpid(),
                            "desde_epoch": agora.timestamp()}, ensure_ascii=False)
        for _ in range(2):
            try:
                fd = os.open(self.caminho, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                atual = self._ler()
                if atual is None or trava_abandonada(atual, agora):
                    try:
                        self.caminho.unlink()
                    except FileNotFoundError:
                        pass
                    continue
                raise TravaOcupada(f"pesado.lock com '{atual['quem']}' desde "
                                   f"{atual['desde']:%d/%m %H:%M}")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(dados)
            self._minha = True
            return
        raise TravaOcupada("não consegui pegar a trava")

    def soltar(self) -> None:
        if self._minha:
            atual = self._ler() or {}
            minha = atual.get("pid") == os.getpid() or (not atual.get("pid") and atual.get("quem") == self.dono)
            if minha:
                try:
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
