"""qa_paridade — teste de paridade do HP Studio (app x Claude).

Compara o vídeo/arte feito pelo app com o feito 100% pelo Claude
(referência) e dá nota de 0 a 10 por métrica: duração, SSIM por quadro,
loudness (LUFS/true peak), legenda (texto e tempos), lâminas (quantidade e
ordem) e formato. Registra o modo sombra por tarefa: só com 7 dias corridos
seguidos aprovados a tarefa é liberada para o app.

Uso rápido:
    from qa_paridade import comparar_video, registrar, status_tarefa
    rel = comparar_video("app.mp4", "ref.mp4")
    registrar("editor_reel", rel, id="post123")
    status_tarefa("editor_reel")["liberada"]
"""
import os.path as _op
import sys as _sys

# hpbase e os módulos irmãos são importados pelo nome curto (from hpbase import ...);
# garante o hp_studio no sys.path mesmo quando este pacote é importado como
# hp_studio.<modulo> pelo hp/motor já existente.
_HP = _op.dirname(_op.dirname(_op.abspath(__file__)))
if _HP not in _sys.path:
    _sys.path.insert(0, _HP)

from .comparar import comparar_imagem, comparar_laminas, comparar_legenda, comparar_video
from .limites import carregar_limites, nota_por_pontos
from .midia import ErroMidia, info_midia
from .motor import executar
from .relatorio import para_markdown
from .sombra import listar_tarefas, registrar, status_tarefa
from .ssim import ssim

__all__ = [
    "comparar_video", "comparar_imagem", "comparar_laminas", "comparar_legenda",
    "carregar_limites", "nota_por_pontos", "info_midia", "ErroMidia", "executar",
    "para_markdown", "registrar", "status_tarefa", "listar_tarefas", "ssim",
]
