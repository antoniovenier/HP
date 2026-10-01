"""Gancho para o motor do HP Studio: `executar(trabalho: dict) -> dict`.

O motor/fila SQLite do `hp` (que já existe no PC) cria um trabalho e chama:

    from whatsapp_local import executar
    executar({"acao": "enviar"})                       # 1 ciclo (modo da config)
    executar({"acao": "enviar", "modo": "real"})
    executar({"acao": "montar_no_ar", "agendados": r"H:\\...\\agendados.json"})
    executar({"acao": "montar_resumo", "dia": "2026-09-29"})
    executar({"acao": "montar_sabado"})
    executar({"acao": "ler_recebidas", "modo": "real"})
    executar({"acao": "relatorio_sombra", "dia": "2026-09-30"})
    executar({"acao": "status"})

Devolve sempre um dict com "ok" (bool) e os detalhes. Nunca pede nada a
ninguém (nada de aprovação manual dentro de rotina).
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from .config import carregar_config, preparar_pastas
from .enviador import Enviador
from .ritmo import Relogio
from .situacao import coletar_status
from .sombra import gerar_relatorio
from .tarefas import enfileirar_no_ar, enfileirar_resumo_dia, enfileirar_resumo_sabado


def _data(v):
    return date.fromisoformat(v) if v else None


def executar(trabalho: dict, fabrica_navegador=None, relogio: Relogio | None = None) -> dict:
    trabalho = dict(trabalho or {})
    acao = trabalho.get("acao", "enviar")
    relogio = relogio or Relogio()
    preparar_pastas()
    cfg = carregar_config()
    agora = relogio.agora()
    try:
        if acao == "enviar":
            res = Enviador(cfg, fabrica_navegador, relogio).ciclo(trabalho.get("modo"))
            return {"ok": not res.erro and not res.precisa_login, **res.como_dict()}
        if acao == "ler_recebidas":
            res = Enviador(cfg, fabrica_navegador, relogio).ler_recebidas(trabalho.get("modo"))
            return {"ok": not res.erro and not res.precisa_login, **res.como_dict()}
        if acao == "montar_no_ar":
            msgs = enfileirar_no_ar(Path(trabalho["agendados"]), cfg, agora,
                                    grupo=trabalho.get("grupo"),
                                    so_mostrar=bool(trabalho.get("so_mostrar")))
            return {"ok": True, "mensagens": msgs}
        if acao == "montar_resumo":
            m = enfileirar_resumo_dia(cfg, agora, dia=_data(trabalho.get("dia")),
                                      grupo=trabalho.get("grupo"),
                                      so_mostrar=bool(trabalho.get("so_mostrar")))
            return {"ok": m is not None, "mensagem": m}
        if acao == "montar_sabado":
            m = enfileirar_resumo_sabado(cfg, agora, sabado=_data(trabalho.get("sabado")),
                                         grupo=trabalho.get("grupo"),
                                         so_mostrar=bool(trabalho.get("so_mostrar")))
            return {"ok": m is not None, "mensagem": m}
        if acao == "relatorio_sombra":
            arq = gerar_relatorio(_data(trabalho.get("dia")) or agora.date(),
                                  agora.isoformat(timespec="seconds"))
            return {"ok": True, "relatorio": str(arq)}
        if acao == "status":
            return {"ok": True, **coletar_status(relogio)}
    except Exception as e:
        return {"ok": False, "erro": f"{type(e).__name__}: {str(e)[:300]}"}
    return {"ok": False, "erro": f"ação desconhecida: {acao}"}
