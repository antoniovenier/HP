"""Entrada da tarefa agendada das 6h (roda com pythonw.exe, sem console).

Uso (o `python -m metricas agendar-6h` imprime o comando pronto):
    pythonw.exe "...\\hp_studio\\metricas\\agendado.py" coletar
"""
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
# tira a própria pasta do caminho (tem módulos com nomes curtos) e põe hp_studio
sys.path[:] = [p for p in sys.path if Path(p or ".").resolve() != AQUI]
sys.path.insert(0, str(AQUI.parent))

from metricas.cli import main  # noqa: E402

if __name__ == "__main__":
    try:
        codigo = main(sys.argv[1:] or ["coletar"])
    except Exception as e:  # noqa: BLE001 — sem console: vai para o log
        from hpbase import obter_logger
        obter_logger("metricas").error(f"tarefa agendada falhou: {type(e).__name__}: {e}")
        codigo = 1
    sys.exit(codigo)
