"""esteira — etapa 3 do HP Studio: esteira de pastas P0/P1/P2.

H:\\HypadoLocal\\esteira\\ 01_pedidos -> 02_baixados -> 03_legenda_dublagem ->
04_edicao -> 05_revisao -> 06_agendados -> 07_postados (e 99_erros).
Cada item é uma pasta (P1_2026-09-30_1830_gta_rockstar-quinta) com tudo dentro.

Uso rápido:
    from esteira import criar_pedido, ciclo
    criar_pedido({...})       # pasta em 01_pedidos com pedido.json validado
    ciclo()                   # uma passada em todas as etapas
Linha de comando: python -m esteira --help
Motor do HP Studio: esteira.gancho.executar({"acao": "ciclo"})
"""
from .config import Config, carregar_config
from .constantes import ETAPAS, ERROS
from .erros import ErroEsteira, ErroEtapa, ErroPermanente, PedidoInvalido
from .motor import Esteira
from .pedido import criar_pedido, validar_pedido
from .resultado import Resultado
from .vigia import ciclo, vigiar

__all__ = ["Config", "carregar_config", "ETAPAS", "ERROS", "ErroEsteira", "ErroEtapa",
           "ErroPermanente", "PedidoInvalido", "Esteira", "criar_pedido",
           "validar_pedido", "Resultado", "ciclo", "vigiar"]
