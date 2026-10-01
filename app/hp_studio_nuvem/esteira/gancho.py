"""Gancho para o motor já existente do HP Studio (etapa 1).

O motor chama `executar(trabalho: dict) -> dict` e nunca recebe exceção:
a resposta sempre tem "ok" (True/False).

Exemplos de trabalho:
  {"tipo": "esteira", "acao": "ciclo"}                       -> uma passada
  {"tipo": "esteira", "acao": "ciclo", "simular": true, "max_trabalhos": 5}
  {"acao": "pedido", "dados": {...pedido.json...}}
  {"acao": "status"}
  {"acao": "aprovar", "item": "P1_...", "notas": {"gancho": 9, ...}, "motivo": "..."}
  {"acao": "refazer", "item": "P1_...", "motivo": "...", "etapa": "04", "notas": {...}}
  {"acao": "tiktok_ok", "item": "P1_...", "link": "https://..."}
  {"acao": "confirmar", "item": "P1_...", "rede": "pinterest", "link": "..."}
  {"acao": "liberar", "item": "..."} · {"acao": "reprocessar", "item": "...", "etapa": "04"}
  {"acao": "prioridade", "item": "...", "prioridade": "P0"}
"""
from __future__ import annotations

import json
from pathlib import Path

from hpbase import mascarar, obter_logger

from . import acoes, vigia

ACOES = ("ciclo", "pedido", "status", "aprovar", "refazer", "tiktok_ok", "confirmar",
         "liberar", "reprocessar", "prioridade")


def _serializavel(obj):
    return json.loads(json.dumps(obj, ensure_ascii=False, default=str))


def executar(trabalho: dict) -> dict:
    trabalho = dict(trabalho or {})
    acao = str(trabalho.get("acao") or "").strip().lower().replace("-", "_")
    if not acao:
        tipo = str(trabalho.get("tipo") or "").strip().lower().replace("-", "_")
        acao = tipo if tipo in ACOES else "ciclo"
    sim = bool(trabalho.get("simular", False))
    kw_proc = {"simular": sim}
    try:
        if acao == "ciclo":
            r = vigia.ciclo(simular=sim, max_trabalhos=trabalho.get("max_trabalhos"))
        elif acao == "pedido":
            r = {"item": acoes.novo_pedido(trabalho["dados"]).name}
        elif acao == "status":
            r = acoes.status()
        elif acao == "aprovar":
            r = acoes.aprovar(trabalho["item"], trabalho["notas"], trabalho.get("motivo", ""),
                              trabalho.get("revisor", "Claude"), **kw_proc)
        elif acao == "refazer":
            r = acoes.refazer(trabalho["item"], trabalho.get("motivo", ""),
                              trabalho.get("etapa"), trabalho.get("notas"),
                              trabalho.get("ajustes"), trabalho.get("revisor", "Claude"),
                              **kw_proc)
        elif acao == "tiktok_ok":
            r = acoes.tiktok_ok(trabalho["item"], trabalho.get("link"),
                                trabalho.get("agendado_para"), **kw_proc)
        elif acao == "confirmar":
            r = acoes.confirmar(trabalho["item"], trabalho["rede"], trabalho.get("link"),
                                **kw_proc)
        elif acao == "liberar":
            r = acoes.liberar(trabalho["item"])
        elif acao == "reprocessar":
            r = acoes.reprocessar(trabalho["item"], trabalho.get("etapa"))
        elif acao == "prioridade":
            r = acoes.mudar_prioridade(trabalho["item"], trabalho["prioridade"])
        else:
            return {"ok": False, "acao": acao,
                    "erro": f"ação desconhecida (use {', '.join(ACOES)})"}
        if isinstance(r, Path):
            r = str(r)
        return {"ok": True, "acao": acao, "resultado": _serializavel(r)}
    except KeyError as e:
        return {"ok": False, "acao": acao, "erro": f"falta o campo {e} no trabalho"}
    except Exception as e:  # noqa: BLE001 — o motor nunca recebe exceção
        obter_logger("esteira").error("gancho %s falhou: %s", acao, e)
        return {"ok": False, "acao": acao, "erro": mascarar(f"{type(e).__name__}: {e}")}
