"""Auxiliares (não-fixtures) dos testes do whatsapp_local."""
from whatsapp_local.config import GRUPO_COMISSAO, PREFIXO
from whatsapp_local.navegador import MensagemLida

GRUPO_GTA = "HP | GTA 6"


def nova_msg(ident="m1", grupo=GRUPO_COMISSAO, texto=None, tipo="no_ar", anexos=None, **extra):
    d = {"id": ident, "grupo": grupo,
         "texto": texto if texto is not None else f"{PREFIXO} 🚀 No ar agora — {ident}",
         "anexos": anexos or [], "tipo": tipo,
         "criado_em": "2026-09-30T09:00:00-03:00"}
    d.update(extra)
    return d


def fabrica_de(nav, registro=None):
    """Fábrica que entrega sempre o mesmo navegador falso (e anota se veio visível)."""
    def _fabrica(cfg, visivel=False):
        if registro is not None:
            registro.append(visivel)
        return nav
    return _fabrica


def fabrica_proibida(cfg, visivel=False):
    raise AssertionError("o navegador NÃO pode ser criado aqui")


def msg_lida(texto, autor="Antônio", hora="09:15, 30/09/2026", saida=False):
    return MensagemLida(autor=autor, hora=hora, texto=texto, saida=saida)
