"""Modo sombra: o app só MONTA o texto e compara com o que o plantão mandou.

Não abre navegador, não envia nada. Pastas (em H:\\HypadoLocal\\whatsapp_sombra\\):
  app\\        o que o app TERIA mandado (as mensagens da fila vêm para cá)
  plantao\\    o que o plantão (Claude) mandou de verdade — o plantão grava
               aqui 1 arquivo por mensagem:
                 .json  {"grupo", "tipo", "texto", "enviado_em"} (ou lista deles)
                 .jsonl 1 objeto desses por linha
                 .txt / .md  só o texto (dia = data do arquivo; tipo adivinhado)
  relatorios\\ AAAA-MM-DD.md (legível) e AAAA-MM-DD.json (números), refeitos a
               cada ciclo: pares app x plantão, % de similaridade (difflib) e diff.
"""
from __future__ import annotations

import difflib
import json
import unicodedata
from datetime import date, datetime
from pathlib import Path

from hpbase import FUSO, escrever_json, garantir, ler_json

from .config import (nfc, pasta_sombra_app, pasta_sombra_plantao,
                     pasta_sombra_relatorios)
from .montagem import ler_datahora

SIMILARIDADE_MINIMA_PAR = 20.0   # abaixo disso não é "a mesma mensagem"


def normalizar_texto(t: str) -> str:
    linhas = [l.rstrip() for l in nfc(t).replace("\r\n", "\n").split("\n")]
    return "\n".join(linhas).strip()


def similaridade(a: str, b: str) -> float:
    """0 a 100 (%), com difflib.SequenceMatcher."""
    a, b = normalizar_texto(a), normalizar_texto(b)
    if not a and not b:
        return 100.0
    return round(difflib.SequenceMatcher(None, a, b, autojunk=False).ratio() * 100, 1)


def veredito(pct: float) -> str:
    if pct >= 100:
        return "idêntico"
    if pct >= 90:
        return "quase igual"
    if pct >= 70:
        return "parecido"
    return "diferente"


def diferencas(plantao: str, app: str) -> str:
    return "\n".join(difflib.unified_diff(
        normalizar_texto(plantao).split("\n"), normalizar_texto(app).split("\n"),
        fromfile="plantão", tofile="app", lineterm="", n=2))


def inferir_tipo(texto: str) -> str | None:
    t = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode().lower()
    if "no ar" in t:
        return "no_ar"
    if "semana" in t or "sabado" in t:
        return "resumo_sabado"
    if "resumo" in t:
        return "resumo_dia"
    return None


def _dia_de(d: dict, arquivo: Path, *chaves: str) -> date:
    for k in chaves:
        dt = ler_datahora(d.get(k)) if isinstance(d, dict) else None
        if dt:
            return dt.date()
    return datetime.fromtimestamp(arquivo.stat().st_mtime, FUSO).date()


def _item(origem: str, d: dict, arquivo: Path, *chaves: str) -> dict | None:
    texto = d.get("texto") if isinstance(d, dict) else None
    if not isinstance(texto, str) or not texto.strip():
        return None
    return {"origem": origem, "texto": texto, "grupo": nfc(d.get("grupo")) or None,
            "tipo": d.get("tipo") or inferir_tipo(texto), "dia": _dia_de(d, arquivo, *chaves)}


def carregar_plantao(pasta: Path | None = None) -> list[dict]:
    pasta = Path(pasta) if pasta else pasta_sombra_plantao()
    saida: list[dict] = []
    if not pasta.exists():
        return saida
    chaves = ("enviado_em", "criado_em", "data", "quando")
    for p in sorted(pasta.rglob("*")):
        if not p.is_file() or p.name.startswith("."):
            continue
        suf = p.suffix.lower()
        try:
            if suf == ".json":
                dados = ler_json(p, None)
                lista = dados if isinstance(dados, list) else [dados]
                for i, d in enumerate(lista):
                    it = _item(p.name if len(lista) == 1 else f"{p.name}#{i + 1}", d, p, *chaves)
                    if it:
                        saida.append(it)
            elif suf == ".jsonl":
                for i, linha in enumerate(p.read_text(encoding="utf-8-sig").splitlines()):
                    if linha.strip():
                        it = _item(f"{p.name}#{i + 1}", json.loads(linha), p, *chaves)
                        if it:
                            saida.append(it)
            elif suf in (".txt", ".md"):
                it = _item(p.name, {"texto": p.read_text(encoding="utf-8-sig")}, p)
                if it:
                    saida.append(it)
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            continue
    return saida


def carregar_app(pasta: Path | None = None) -> list[dict]:
    pasta = Path(pasta) if pasta else pasta_sombra_app()
    saida = []
    for p in sorted(pasta.glob("*.json")) if pasta.exists() else []:
        d = ler_json(p, None)
        if isinstance(d, dict):
            it = _item(d.get("id") or p.stem, d, p, "criado_em", "sombra_em")
            if it:
                saida.append(it)
    return saida


def _compativeis(a: dict, p: dict) -> bool:
    if a.get("tipo") and p.get("tipo") and a["tipo"] != p["tipo"]:
        return False
    if a.get("grupo") and p.get("grupo") and nfc(a["grupo"]) != nfc(p["grupo"]):
        return False
    return True


def parear(app: list[dict], plantao: list[dict]):
    """Casa cada mensagem do app com a do plantão mais parecida (guloso)."""
    candidatos = []
    for i, a in enumerate(app):
        for j, p in enumerate(plantao):
            if _compativeis(a, p):
                s = similaridade(a["texto"], p["texto"])
                if s >= SIMILARIDADE_MINIMA_PAR:
                    candidatos.append((s, i, j))
    candidatos.sort(key=lambda x: (-x[0], x[1], x[2]))
    usados_a, usados_p, pares = set(), set(), []
    for s, i, j in candidatos:
        if i in usados_a or j in usados_p:
            continue
        usados_a.add(i)
        usados_p.add(j)
        pares.append((app[i], plantao[j], s))
    pares.sort(key=lambda x: x[0]["origem"])
    sem_app = [a for i, a in enumerate(app) if i not in usados_a]
    sem_plantao = [p for j, p in enumerate(plantao) if j not in usados_p]
    return pares, sem_app, sem_plantao


def _pct(x: float) -> str:
    return f"{x:.1f}".replace(".", ",") + "%"


def gerar_relatorio(dia: date, agora_iso: str, pasta_app: Path | None = None,
                    pasta_plantao: Path | None = None,
                    pasta_relatorios: Path | None = None,
                    pular_vazio: bool = False) -> Path | None:
    """Refaz relatorios\\AAAA-MM-DD.md e .json do dia. Devolve o .md
    (ou None se pular_vazio e o dia não tem nenhuma mensagem)."""
    app = [a for a in carregar_app(pasta_app) if a["dia"] == dia]
    plantao = [p for p in carregar_plantao(pasta_plantao) if p["dia"] == dia]
    if pular_vazio and not app and not plantao:
        return None
    pares, sem_app, sem_plantao = parear(app, plantao)
    media = round(sum(s for *_, s in pares) / len(pares), 1) if pares else None

    pasta = garantir(Path(pasta_relatorios) if pasta_relatorios else pasta_sombra_relatorios())
    numeros = {
        "dia": dia.isoformat(), "gerado_em": agora_iso,
        "total_app": len(app), "total_plantao": len(plantao),
        "media_similaridade": media,
        "pares": [{"app": a["origem"], "plantao": p["origem"], "tipo": a.get("tipo") or p.get("tipo"),
                   "grupo": a.get("grupo") or p.get("grupo"), "similaridade": s,
                   "veredito": veredito(s)} for a, p, s in pares],
        "sem_par_app": [a["origem"] for a in sem_app],
        "sem_par_plantao": [p["origem"] for p in sem_plantao],
    }
    escrever_json(pasta / f"{dia.isoformat()}.json", numeros)

    md = [f"# Sombra do WhatsApp — {dia:%d/%m/%Y}", "",
          f"Gerado em {agora_iso}. Mensagens do app: {len(app)} · do plantão: "
          f"{len(plantao)} · pares: {len(pares)} · similaridade média: "
          f"{_pct(media) if media is not None else '—'}", ""]
    if pares:
        md += ["| # | Tipo | Grupo | Similaridade | Veredito | App | Plantão |",
               "|---|---|---|---|---|---|---|"]
        for n, (a, p, s) in enumerate(pares, 1):
            md.append(f"| {n} | {a.get('tipo') or p.get('tipo') or '?'} | "
                      f"{(a.get('grupo') or p.get('grupo') or '?').replace('|', '¦')} | "
                      f"{_pct(s)} | {veredito(s)} | {a['origem']} | {p['origem']} |")
        for n, (a, p, s) in enumerate(pares, 1):
            md += ["", f"## {n}. {a.get('tipo') or '?'} — {_pct(s)} ({veredito(s)})", ""]
            d = diferencas(p["texto"], a["texto"])
            md += (["Sem diferença."] if not d else ["```diff", d, "```"])
    if sem_app:
        md += ["", "## O app montou e o plantão não mandou", ""]
        md += [f"- {a['origem']} ({a.get('tipo') or '?'})" for a in sem_app]
    if sem_plantao:
        md += ["", "## O plantão mandou e o app não montou", ""]
        md += [f"- {p['origem']} ({p.get('tipo') or '?'})" for p in sem_plantao]
    arq = pasta / f"{dia.isoformat()}.md"
    arq.write_text("\n".join(md) + "\n", encoding="utf-8")
    return arq
