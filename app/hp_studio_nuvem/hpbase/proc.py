"""Subprocesso sem janela preta (CREATE_NO_WINDOW) e localização do ffmpeg."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

SEM_JANELA = 0x08000000 if os.name == "nt" else 0  # CREATE_NO_WINDOW


def rodar(cmd: list, timeout: float | None = 600, entrada: bytes | None = None,
          cwd: str | Path | None = None) -> subprocess.CompletedProcess:
    """Roda um comando capturando saída; no Windows nunca abre console."""
    kw = {}
    if os.name == "nt":
        kw["creationflags"] = SEM_JANELA
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        kw["startupinfo"] = si
    return subprocess.run([str(c) for c in cmd], capture_output=True,
                          timeout=timeout, input=entrada, cwd=cwd, **kw)


def _achar(nome: str, var: str) -> str | None:
    cand = os.environ.get(var)
    if cand and Path(cand).exists():
        return cand
    achado = shutil.which(nome)
    if achado:
        return achado
    # instalação padrão do PC do Antônio
    for p in (Path(r"H:\HypadoLocal\ferramentas\ffmpeg\bin") / f"{nome}.exe",):
        if p.exists():
            return str(p)
    return None


def achar_ffmpeg() -> str:
    exe = _achar("ffmpeg", "HP_FFMPEG")
    if not exe:
        raise FileNotFoundError("ffmpeg não encontrado (defina HP_FFMPEG)")
    return exe


def achar_ffprobe() -> str | None:
    """Pode faltar; quem usa precisa ter plano B com o próprio ffmpeg."""
    return _achar("ffprobe", "HP_FFPROBE")
