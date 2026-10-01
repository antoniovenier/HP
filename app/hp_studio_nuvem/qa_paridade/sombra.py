"""Modo sombra: registro das comparações e a regra dos 7 dias.

Cada comparação de uma tarefa vira um arquivo
    H:\\HypadoLocal\\app\\paridade\\<tarefa>\\AAAA-MM-DD_<id>.json  (+ .md)
e o `resumo.json` da tarefa é refeito a cada registro.

Regra (limites.json, bloco "sombra"): a tarefa só é LIBERADA PARA O APP
com 7 dias corridos seguidos de sombra, cada dia com pelo menos 1
comparação e todas aprovadas.
- Duas ou mais comparações no mesmo dia contam como 1 dia.
- Um dia com qualquer comparação reprovada ZERA a contagem (e, se a tarefa
  já estava liberada, ela volta para a sombra).
- Dia sem comparação quebra a sequência (recomeça do 1) enquanto ela não
  chegou aos 7; depois de liberada, falta de comparação não tira a liberação.
- Hoje ainda sem comparação não quebra nada (o dia não acabou).
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from pathlib import Path

from hpbase import agora, agora_iso, escrever_json, garantir, ler_json, obter_logger, pasta_app

from . import relatorio
from .limites import carregar_limites
from .util import br

_RX_ARQ = re.compile(r"^(\d{4}-\d{2}-\d{2})_(.+)\.json$")


def pasta_paridade() -> Path:
    return pasta_app() / "paridade"


def nome_seguro(txt: str) -> str:
    """Só letras, números, _ . - (vira nome de pasta/arquivo no Windows)."""
    limpo = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(txt)).strip("._")
    return limpo[:80] or "sem_nome"


def pasta_tarefa(tarefa: str) -> Path:
    return pasta_paridade() / nome_seguro(tarefa)


def registrar(tarefa: str, rel: dict, id: str | None = None,
              quando: datetime | None = None, limites: dict | None = None) -> dict:
    """Grava a comparação no histórico da tarefa e atualiza o resumo.json.

    Devolve {"json": caminho, "md": caminho, "status": status_tarefa}.
    """
    quando = quando or agora()
    dia = quando.date().isoformat()
    ident = nome_seguro(id or quando.strftime("%H%M%S"))
    pasta = garantir(pasta_tarefa(tarefa))
    base, n = f"{dia}_{ident}", 2
    while (pasta / f"{base}.json").exists():
        base = f"{dia}_{ident}_{n}"
        n += 1
    rel = dict(rel)
    rel["sombra"] = {"tarefa": nome_seguro(tarefa), "id": base[len(dia) + 1:], "dia": dia,
                     "quando": quando.isoformat(timespec="seconds")}
    pj, pm = relatorio.salvar(rel, pasta, base)
    st = atualizar_resumo(tarefa, hoje=quando.date(), limites=limites)
    obter_logger("qa_paridade").info(
        "sombra %s %s: %s nota %s aprovado=%s | seguidos %s falta %s liberada %s",
        nome_seguro(tarefa), base, rel.get("veredito"), rel.get("nota_final"),
        rel.get("aprovado"), st["dias_seguidos"], st["falta"], st["liberada"])
    return {"json": pj, "md": pm, "status": st}


def ler_registros(tarefa: str) -> list[dict]:
    """Registros da tarefa (só o essencial), em ordem de dia e nome."""
    pasta = pasta_tarefa(tarefa)
    if not pasta.is_dir():
        return []
    saida = []
    for f in sorted(pasta.glob("*.json")):
        m = _RX_ARQ.match(f.name)
        if not m:
            continue  # resumo.json e outros
        try:
            dia = date.fromisoformat(m.group(1))
        except ValueError:
            continue
        dados = ler_json(f, {}) or {}
        if "aprovado" not in dados:
            continue  # arquivo estranho/corrompido não conta
        saida.append({"dia": dia, "id": m.group(2), "arquivo": str(f),
                      "aprovado": bool(dados.get("aprovado")),
                      "nota_final": dados.get("nota_final"),
                      "veredito": dados.get("veredito"),
                      "quando": (dados.get("sombra") or {}).get("quando") or dados.get("quando")})
    saida.sort(key=lambda r: (r["dia"], r["quando"] or "", r["id"]))
    return saida


def calcular_status(registros: list[dict], hoje: date, dias_necessarios: int = 7,
                    minimo_por_dia: int = 1) -> dict:
    """Aplica a regra dos 7 dias sobre os registros (função pura)."""
    por_dia: dict[date, dict] = {}
    for r in registros:
        d = por_dia.setdefault(r["dia"], {"comparacoes": 0, "aprovadas": 0, "reprovadas": 0})
        d["comparacoes"] += 1
        d["aprovadas" if r["aprovado"] else "reprovadas"] += 1

    seguidos, ultimo_contado = 0, None
    liberada, liberada_em, observacao = False, None, ""
    historico = []
    for dia in sorted(por_dia):
        info = por_dia[dia]
        if info["reprovadas"]:
            situacao = "reprovado"
            seguidos, ultimo_contado = 0, None
            if liberada:
                observacao = f"reprovado em {dia} tirou a liberação"
            else:
                observacao = f"reprovado em {dia} zerou a contagem"
            liberada, liberada_em = False, None
        elif info["comparacoes"] < minimo_por_dia:
            if dia >= hoje:
                situacao = "pendente"  # o dia ainda não acabou
            else:
                situacao = "incompleto"
                if not liberada:
                    seguidos, ultimo_contado = 0, None
                    observacao = f"{dia} teve menos de {minimo_por_dia} comparação(ões)"
        else:
            situacao = "aprovado"
            if liberada or (ultimo_contado is not None and dia == ultimo_contado + timedelta(days=1)):
                seguidos += 1
            else:
                if ultimo_contado is not None and not liberada:
                    observacao = f"faltou comparação entre {ultimo_contado} e {dia}: recomeçou"
                seguidos = 1
            ultimo_contado = dia
            if seguidos >= dias_necessarios and not liberada:
                liberada, liberada_em = True, dia
                observacao = f"liberada em {dia}"
        historico.append({"dia": dia.isoformat(), "situacao": situacao, **info})

    if not liberada and ultimo_contado is not None and ultimo_contado < hoje - timedelta(days=1):
        observacao = f"sequência quebrada: sem comparação aprovada desde {ultimo_contado}"
        seguidos = 0
    ultimo = registros[-1] if registros else None
    return {
        "dias_necessarios": dias_necessarios,
        "comparacoes_minimas_por_dia": minimo_por_dia,
        "dias_seguidos": seguidos,
        "falta": 0 if liberada else max(0, dias_necessarios - seguidos),
        "liberada": liberada,
        "liberada_em": liberada_em.isoformat() if liberada_em else None,
        "comparacoes": len(registros),
        "dias_com_comparacao": len(por_dia),
        "ultimo_dia": ultimo["dia"].isoformat() if ultimo else None,
        "ultima_nota": ultimo["nota_final"] if ultimo else None,
        "ultimo_veredito": ultimo["veredito"] if ultimo else None,
        "observacao": observacao,
        "dias": historico,
    }


def status_tarefa(tarefa: str, hoje: date | None = None, limites: dict | None = None) -> dict:
    """Situação da tarefa no modo sombra (dias seguidos, falta, liberada)."""
    lim = limites or carregar_limites()
    cfg = lim["sombra"]
    st = calcular_status(ler_registros(tarefa), hoje or agora().date(),
                         int(cfg["dias_necessarios"]), int(cfg["comparacoes_minimas_por_dia"]))
    return {"tarefa": nome_seguro(tarefa), **st}


def atualizar_resumo(tarefa: str, hoje: date | None = None, limites: dict | None = None) -> dict:
    """Refaz o resumo.json da tarefa a partir dos registros (fonte da verdade)."""
    st = status_tarefa(tarefa, hoje=hoje, limites=limites)
    st["atualizado_em"] = agora_iso()
    st["regra"] = (f"{st['dias_necessarios']} dias corridos seguidos, todos aprovados, "
                   f"no mínimo {st['comparacoes_minimas_por_dia']} comparação por dia; "
                   "um reprovado zera a contagem")
    escrever_json(garantir(pasta_tarefa(tarefa)) / "resumo.json", st)
    return st


def listar_tarefas() -> list[str]:
    raiz = pasta_paridade()
    if not raiz.is_dir():
        return []
    return sorted(p.name for p in raiz.iterdir()
                  if p.is_dir() and not p.name.startswith(("_", ".")))


def tabela_status(lista: list[dict]) -> str:
    """Tabela de texto simples (cabe no PowerShell)."""
    cab = ["tarefa", "dias aprovados seguidos", "falta", "liberada", "ultimo dia",
           "ultima nota", "observacao"]
    linhas = [[s["tarefa"], str(s["dias_seguidos"]), str(s["falta"]),
               "sim" if s["liberada"] else "não", s["ultimo_dia"] or "-",
               br(s["ultima_nota"]) if s["ultima_nota"] is not None else "-",
               s["observacao"] or ""] for s in lista]
    larg = [max(len(c), *(len(l[i]) for l in linhas)) if linhas else len(c)
            for i, c in enumerate(cab)]
    fmt = lambda cols: "  ".join(c.ljust(larg[i]) for i, c in enumerate(cols)).rstrip()
    saida = [fmt(cab), fmt(["-" * w for w in larg])]
    saida += [fmt(l) for l in linhas]
    if not linhas:
        saida.append("(nenhuma tarefa em modo sombra ainda)")
    return "\n".join(saida)
