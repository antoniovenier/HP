"""whatsapp_local — enviador local de WhatsApp da HP (ticket P0).

Janela própria do WhatsApp Web (página oficial, Playwright, perfil separado,
fora da tela e sem som) que lê a fila H:\\HypadoLocal\\whatsapp_fila\\ e envia
sozinha, com validação dura (*Claude - *, 3 tipos, só grupos permitidos),
conferência do cabeçalho da conversa, ritmo baixo e modo sombra (padrão).
Monta o aviso "no ar" e os resumos sem Claude e salva as mensagens novas do
Antônio nos grupos HP.

Uso: python -m whatsapp_local --help   (ver LEIA.md)
"""
import os.path as _op
import sys as _sys

# hpbase e os módulos irmãos são importados pelo nome curto (from hpbase import ...);
# garante o hp_studio no sys.path mesmo quando este pacote é importado como
# hp_studio.<modulo> pelo hp/motor já existente.
_HP = _op.dirname(_op.dirname(_op.abspath(__file__)))
if _HP not in _sys.path:
    _sys.path.insert(0, _HP)

from .config import (GRUPO_COMISSAO, PREFIXO, TIPOS_PERMITIDOS, Config,
                     carregar_config)
from .enviador import Enviador, ResultadoCiclo
from .gancho import executar
from .navegador import Navegador
from .navegador_falso import NavegadorFalso
from .validacao import validar_mensagem

__all__ = ["GRUPO_COMISSAO", "PREFIXO", "TIPOS_PERMITIDOS", "Config",
           "carregar_config", "Enviador", "ResultadoCiclo", "executar",
           "Navegador", "NavegadorFalso", "validar_mensagem"]
