"""whatsapp_local — enviador local de WhatsApp da HP (ticket P0).

Janela própria do WhatsApp Web (página oficial, Playwright, perfil separado,
fora da tela e sem som) que lê a fila H:\\HypadoLocal\\whatsapp_fila\\ e envia
sozinha, com validação dura (*Claude - *, 3 tipos, só grupos permitidos),
conferência do cabeçalho da conversa, ritmo baixo e modo sombra (padrão).
Monta o aviso "no ar" e os resumos sem Claude e salva as mensagens novas do
Antônio nos grupos HP.

Uso: python -m whatsapp_local --help   (ver LEIA.md)
"""
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
