"""metricas — etapa 6 do HP Studio: métricas por API oficial.

Coleta diária (6h, tarefa agendada) e sob demanda de Instagram, Threads,
Facebook (Páginas) e YouTube; TikTok entra por importação manual.
Foto diária em H:\\HypadoLocal\\metricas\\AAAA-MM-DD.json, ultimo.json e
metricas_painel.json. Detalhes no LEIA.md.

Gancho para o motor do app: `executar(trabalho: dict) -> dict`.
"""
from __future__ import annotations
import os.path as _op
import sys as _sys

# hpbase e os módulos irmãos são importados pelo nome curto (from hpbase import ...);
# garante o hp_studio no sys.path mesmo quando este pacote é importado como
# hp_studio.<modulo> pelo hp/motor já existente.
_HP = _op.dirname(_op.dirname(_op.abspath(__file__)))
if _HP not in _sys.path:
    _sys.path.insert(0, _HP)



def executar(trabalho: dict) -> dict:
    """Trabalho do motor. Exemplos:
    {"acao": "coletar"} · {"acao": "coletar", "conta": "gta", "rede": "instagram"}
    {"acao": "coletar", "simular": true} · {"acao": "importar_tiktok", "arquivo": "...csv"}
    """
    from .coleta import coletar, plano
    from .config import pasta_metricas
    from .tiktok import importar

    acao = trabalho.get("acao", "coletar")
    try:
        if acao == "coletar":
            if trabalho.get("simular"):
                return {"ok": True, "simulado": True,
                        "plano": plano(trabalho.get("conta"), trabalho.get("rede"))}
            foto = coletar(trabalho.get("conta"), trabalho.get("rede"),
                           saida=trabalho.get("saida"))
            status = {f"{c}/{r}": v.get("status") for c, redes in foto["contas"].items()
                      for r, v in redes.items()}
            return {"ok": True, "data": foto["data"], "status": status,
                    "arquivo": str(pasta_metricas(trabalho.get("saida")) / f"{foto['data']}.json")}
        if acao == "importar_tiktok":
            res = importar(trabalho["arquivo"], conta=trabalho.get("conta"),
                           data=trabalho.get("data"), saida=trabalho.get("saida"))
            return {"ok": True, "importados": res}
        return {"ok": False, "erro": f"ação desconhecida: {acao}"}
    except Exception as e:  # noqa: BLE001 — o motor só quer saber se deu certo
        from hpbase import mascarar
        return {"ok": False, "erro": mascarar(f"{type(e).__name__}: {e}")[:300]}
