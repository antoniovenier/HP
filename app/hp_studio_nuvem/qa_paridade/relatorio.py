"""Relatório: nota final (média ponderada), veredito, JSON e Markdown."""
from __future__ import annotations

from pathlib import Path

from hpbase import agora_iso, escrever_json, garantir

from .util import NOMES, br

VERSAO = 1


def criterio_texto(lim: dict) -> str:
    v = lim["veredito"]
    return (f"todas as métricas >= {br(v['aprovacao_minima_metrica'], 1)} "
            f"e média >= {br(v['aprovacao_media'], 1)}")


def calcular_veredito(metricas: dict, lim: dict) -> dict:
    """Nota final ponderada, menor nota, veredito e se passa no dia."""
    v = lim["veredito"]
    pesos = lim["pesos"]
    aplicadas = {k: m for k, m in metricas.items() if m.get("aplica") and m.get("nota") is not None}
    if not aplicadas:
        raise ValueError("nenhuma métrica se aplica a esta comparação")
    soma_pesos = sum(float(pesos.get(k, 1.0)) for k in aplicadas)
    final = sum(float(pesos.get(k, 1.0)) * m["nota"] for k, m in aplicadas.items()) / soma_pesos
    final = round(final, 2)
    pior_nome = min(aplicadas, key=lambda k: aplicadas[k]["nota"])
    pior = aplicadas[pior_nome]["nota"]
    if final >= v["identico"] and pior >= v["nota_minima_metrica"]:
        veredito = "IDENTICO"
    elif final >= v["equivalente"] and pior >= v["nota_minima_metrica"]:
        veredito = "EQUIVALENTE"
    else:
        veredito = "DIFERENTE"
    aprovado = final >= v["aprovacao_media"] and pior >= v["aprovacao_minima_metrica"]
    reprovadas = [k for k, m in aplicadas.items() if m["nota"] < v["aprovacao_minima_metrica"]]
    return {"nota_final": final, "menor_nota": {"metrica": pior_nome, "nota": pior},
            "veredito": veredito, "aprovado": bool(aprovado),
            "metricas_reprovadas": reprovadas,
            "pesos_usados": {k: float(pesos.get(k, 1.0)) for k in aplicadas}}


def montar(tipo: str, entradas: dict, metricas: dict, lim: dict) -> dict:
    rel = {"versao": VERSAO, "tipo": tipo, "quando": agora_iso(), **entradas,
           "metricas": metricas}
    rel.update(calcular_veredito(metricas, lim))
    rel["criterio"] = criterio_texto(lim)
    rel["limites_veredito"] = dict(lim["veredito"])
    return rel


# ---------------------------------------------------------------- Markdown
def _linha_detalhe(nome: str, m: dict) -> list[str]:
    d = m.get("detalhes") or {}
    out = []
    if nome == "ssim" and d.get("piores_quadros"):
        out.append("Piores quadros:")
        for q in d["piores_quadros"]:
            out.append(f"- {q['tempo']} — SSIM {br(q['ssim'], 4)} (pior região: {q['pior_regiao']})")
    if nome == "legenda":
        for dif in d.get("diferencas_texto", []):
            out.append(f"- texto {dif['tipo']}: app \"{dif['app']}\" / ref \"{dif['ref']}\"")
        for b in d.get("piores_blocos", [])[:3]:
            if b["desvio_inicio_ms"] or b["desvio_fim_ms"]:
                out.append(f"- bloco {b['bloco_ref']} ({b['inicio_ref']}): início "
                           f"{b['desvio_inicio_ms']:+d} ms, fim {b['desvio_fim_ms']:+d} ms")
    if nome == "laminas":
        for f in d.get("fora_de_ordem", []):
            out.append(f"- posição {f['posicao_app']} do app ({f['arquivo_app']}) = "
                       f"lâmina {f['posicao_ref']} da referência ({f['arquivo_ref']})")
        for x in d.get("faltando_no_app", []):
            out.append(f"- faltando no app: {x}")
        for x in d.get("sobrando_no_app", []):
            out.append(f"- sobrando no app: {x}")
        for c in d.get("casamento", []):
            out.append(f"- app {c['posicao_app']} ({c['arquivo_app']}) x ref "
                       f"{c['posicao_ref']} ({c['arquivo_ref']}): SSIM {br(c['ssim'], 4)}")
    return out


def para_markdown(rel: dict) -> str:
    sim_nao = "SIM" if rel["aprovado"] else "NÃO"
    linhas = [f"# Paridade — {rel['tipo']} — {rel['veredito']}", "",
              f"- Quando: {rel['quando']}",
              f"- App: `{rel['app'].get('arquivo') or rel['app'].get('pasta')}`",
              f"- Referência (Claude): `{rel['ref'].get('arquivo') or rel['ref'].get('pasta')}`",
              f"- **Nota final: {br(rel['nota_final'])}** — veredito **{rel['veredito']}**",
              f"- Passa no dia: **{sim_nao}** (critério: {rel['criterio']})"]
    if rel.get("sombra"):
        s = rel["sombra"]
        linhas.append(f"- Sombra: tarefa `{s['tarefa']}`, dia {s['dia']}, id `{s['id']}`")
    linhas += ["", "| Métrica | Nota | Peso | Resumo |", "|---|---|---|---|"]
    for nome, m in rel["metricas"].items():
        nota = br(m["nota"]) if m.get("aplica") else "não se aplica"
        peso = br(rel["pesos_usados"].get(nome), 1) if m.get("aplica") else "-"
        marca = " ⚠" if m.get("aplica") and nome in rel.get("metricas_reprovadas", []) else ""
        linhas.append(f"| {NOMES.get(nome, nome)}{marca} | {nota} | {peso} | {m.get('resumo', '')} |")
    for nome, m in rel["metricas"].items():
        if not m.get("aplica"):
            continue
        linhas += ["", f"## {NOMES.get(nome, nome)} — {br(m['nota'])}"]
        if m.get("subnotas"):
            linhas.append("Subnotas: " + ", ".join(f"{k} {br(v)}" for k, v in m["subnotas"].items()))
        linhas += _linha_detalhe(nome, m)
    v = rel.get("limites_veredito") or {"identico": 9.5, "equivalente": 9.0,
                                        "nota_minima_metrica": 9.0}
    linhas += ["", f"Veredito: IDENTICO (média >= {br(v['identico'], 1)} e todas >= "
               f"{br(v['nota_minima_metrica'], 1)}), EQUIVALENTE (média >= "
               f"{br(v['equivalente'], 1)} e todas >= {br(v['nota_minima_metrica'], 1)}), "
               "DIFERENTE (o resto). Limites em qa_paridade/limites.json.", ""]
    return "\n".join(linhas)


def salvar(rel: dict, pasta, nome_base: str) -> tuple[Path, Path]:
    """Grava <nome_base>.json e <nome_base>.md na pasta (JSON atômico)."""
    pasta = garantir(Path(pasta))
    pj = escrever_json(pasta / f"{nome_base}.json", rel)
    pm = pasta / f"{nome_base}.md"
    tmp = pm.with_suffix(".md.tmp")
    tmp.write_text(para_markdown(rel), encoding="utf-8")
    tmp.replace(pm)
    return pj, pm
