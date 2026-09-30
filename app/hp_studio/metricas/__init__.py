"""metricas — etapa 6 do HP Studio: métricas por API oficial.

Coleta diária (6h, tarefa agendada) e sob demanda de Instagram, Threads,
Facebook (Páginas) e YouTube; TikTok entra por importação manual.
Foto diária em H:\\HypadoLocal\\metricas\\AAAA-MM-DD.json, ultimo.json e
metricas_painel.json. Detalhes no LEIA.md.

Gancho para o motor do app: `executar(trabalho: dict) -> dict`.
"""
from __future__ import annotations


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
