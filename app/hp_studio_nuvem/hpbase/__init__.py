"""hpbase — base comum dos módulos novos do HP Studio (entrega da sessão da nuvem).

Tudo o que os módulos esteira, metricas, qa_paridade, whatsapp_local e os
scripts novos precisam em comum: caminhos, log sem segredo, trava do trabalho
pesado, janela proibida (18h-22h30), subprocesso sem janela preta e leitura
de segredo que nunca mostra o valor.
"""
from .caminhos import (raiz_local, raiz_drive, pasta_app, pasta_logs,
                       pasta_segredos, pasta_esteira, pasta_paridade, garantir)
from .registro import obter_logger, mascarar
from .trava import TravaPesada, TravaOcupada, janela_proibida, ler_trava, trava_abandonada
from .proc import rodar, achar_ffmpeg, achar_ffprobe, SEM_JANELA
from .segredos import ler_segredo, SegredoAusente
from .arquivos import (ler_json, escrever_json, agora, agora_iso,
                       anexar_linha, FUSO)

__all__ = [
    "raiz_local", "raiz_drive", "pasta_app", "pasta_logs", "pasta_segredos",
    "pasta_esteira", "pasta_paridade",
    "garantir", "obter_logger", "mascarar", "TravaPesada", "TravaOcupada",
    "janela_proibida", "ler_trava", "trava_abandonada", "rodar", "achar_ffmpeg",
    "achar_ffprobe", "SEM_JANELA",
    "ler_segredo", "SegredoAusente", "ler_json", "escrever_json", "agora",
    "agora_iso", "anexar_linha", "FUSO",
]
