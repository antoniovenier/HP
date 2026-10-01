"""TikTok: sem API (continua pelo Chrome). Aqui só importamos um CSV ou JSON
que o Claude/Antônio exporta à mão, e ele entra na foto do dia com
"fonte": "manual".

CSV (separador ; ou ,), uma linha por vídeo; colunas aceitas (maiúscula e
acento não importam): conta, seguidores, id, legenda, tipo, publicado_em,
link, views, curtidas, comentarios, compartilhamentos, salvamentos, alcance.
Sinônimos aceitos: perfil/canal, followers, descricao/titulo, data, url,
visualizacoes/plays, likes, comments, shares, saves/favoritos.

JSON: lista de linhas como acima, ou {"conta": "gta", "seguidores": N, "posts": [...]},
ou {"contas": {"gta": {"seguidores": N, "posts": [...]}}}.
"""
from __future__ import annotations

import csv
import io
from datetime import date
from pathlib import Path

from hpbase import agora as agora_brasilia, ler_json

from . import calculos
from .config import carregar_config, pasta_metricas
from .modelos import novo_post, numero, sem_acento

SINONIMOS = {
    "conta": ("conta", "perfil", "canal"),
    "seguidores": ("seguidores", "followers", "seguidores_total"),
    "id": ("id", "video_id", "id_video"),
    "legenda": ("legenda", "descricao", "caption", "titulo", "texto"),
    "tipo": ("tipo", "formato"),
    "publicado_em": ("publicado_em", "data", "data_publicacao", "publicado", "postado_em"),
    "link": ("link", "url"),
    "views": ("views", "visualizacoes", "plays", "video_views", "reproducoes"),
    "curtidas": ("curtidas", "likes"),
    "comentarios": ("comentarios", "comments"),
    "compartilhamentos": ("compartilhamentos", "shares"),
    "salvamentos": ("salvamentos", "saves", "favoritos"),
    "alcance": ("alcance", "reach"),
}


def _linha(bruta: dict) -> dict:
    norm = {sem_acento(k).replace(" ", "_"): v for k, v in bruta.items() if k}
    out = {}
    for campo, nomes in SINONIMOS.items():
        for n in nomes:
            if norm.get(n) not in (None, ""):
                out[campo] = norm[n]
                break
    return out


def ler_arquivo(arquivo) -> list:
    p = Path(arquivo)
    if p.suffix.lower() == ".json":
        dados = ler_json(p)
        if isinstance(dados, list):
            return [_linha(x) for x in dados if isinstance(x, dict)]
        linhas = []
        blocos = dados.get("contas") if isinstance(dados.get("contas"), dict) \
            else {dados.get("conta"): dados}
        for conta, bloco in blocos.items():
            if bloco.get("seguidores") is not None:
                linhas.append({"conta": conta, "seguidores": bloco["seguidores"]})
            for post in bloco.get("posts") or []:
                linhas.append({**_linha(post), **({"conta": conta} if conta else {})})
        return linhas
    texto = p.read_text(encoding="utf-8-sig")
    try:
        dialeto = csv.Sniffer().sniff(texto[:2000], delimiters=";,\t")
    except csv.Error:
        dialeto = csv.excel
    return [_linha(x) for x in csv.DictReader(io.StringIO(texto), dialect=dialeto)]


def resolver_conta(valor, cfg: dict) -> str:
    v = sem_acento(str(valor or "")).lstrip("@")
    if v in cfg["contas"]:
        return v
    for conta, c in cfg["contas"].items():
        nomes = {sem_acento(c.get("nome", ""))}
        nomes |= {sem_acento(r.get("usuario", "")).lstrip("@")
                  for r in c.values() if isinstance(r, dict)}
        if v and v in nomes:
            return conta
    raise ValueError(f"conta desconhecida no arquivo: {valor!r} (use --conta)")


def importar(arquivo, conta: str | None = None, data: str | None = None, saida=None,
             config: dict | None = None, agora=None) -> dict:
    from .coleta import VERSAO, salvar  # evita import circular

    cfg = config if config is not None else carregar_config()
    agora = agora or agora_brasilia()
    dia = date.fromisoformat(data) if data else agora.date()
    pasta = pasta_metricas(saida)
    grupos: dict = {}
    for i, l in enumerate(ler_arquivo(arquivo), 1):
        c = resolver_conta(l.get("conta") or conta, cfg)
        g = grupos.setdefault(c, {"seguidores": None, "posts": []})
        if numero(l.get("seguidores")) is not None:
            g["seguidores"] = numero(l["seguidores"])
        if any(l.get(k) not in (None, "") for k in ("id", "link", "views")):
            g["posts"].append(novo_post(
                l.get("id") or l.get("link") or f"linha{i}", l.get("legenda"),
                (l.get("tipo") or "video").lower(), l.get("publicado_em"), l.get("link"),
                **{k: l.get(k) for k in ("views", "curtidas", "comentarios",
                                         "compartilhamentos", "salvamentos", "alcance")}))
    if not grupos:
        raise ValueError("arquivo sem nenhuma linha útil")
    arq_dia = pasta / f"{dia.isoformat()}.json"
    foto = ler_json(arq_dia, None) or {"data": dia.isoformat(), "versao": VERSAO, "contas": {}}
    foto.setdefault("contas", {})
    foto.setdefault("coletado_em", agora.isoformat(timespec="seconds"))
    resumo = {}
    for c, g in grupos.items():
        for p in g["posts"]:
            p["taxa_engajamento"] = calculos.taxa_engajamento(p)
        foto["contas"].setdefault(c, {})["tiktok"] = {
            "fonte": "manual", "status": "ok", "arquivo": Path(arquivo).name,
            "importado_em": agora.isoformat(timespec="seconds"),
            "coletado_em": agora.isoformat(timespec="seconds"),
            "seguidores": g["seguidores"], "posts": g["posts"],
            "totais": calculos.totais(g["posts"])}
        resumo[c] = len(g["posts"])
    salvar(foto, pasta, cfg)
    return resumo
