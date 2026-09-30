"""Instagram (Graph API oficial): seguidores + posts dos últimos dias com insights."""
from __future__ import annotations

from .cliente import ErroAPI, ErroNaoAutorizado, ErroTemporario, paginar
from .config import token_e_id
from .modelos import ler_data, novo_post

CAMPOS_MIDIA = ("id,caption,media_type,media_product_type,timestamp,permalink,"
                "like_count,comments_count")
METRICAS = ("reach", "saved", "shares", "views", "total_interactions")
MAPA = {"reach": "alcance", "saved": "salvamentos", "shares": "compartilhamentos",
        "views": "views"}


def tipo_ig(m: dict) -> str:
    prod = (m.get("media_product_type") or "").upper()
    mt = (m.get("media_type") or "").upper()
    if prod == "REELS":
        return "reels"
    if prod == "STORY":
        return "story"
    return {"CAROUSEL_ALBUM": "carrossel", "IMAGE": "imagem",
            "VIDEO": "video"}.get(mt, (mt or prod or "outro").lower())


def base_url(cfg_rede: dict, ctx) -> str:
    host = (cfg_rede.get("host") or ctx.cfg["host_graph"]).rstrip("/")
    return f"{host}/{ctx.cfg['versao_graph']}"


def coletar(cliente, conta: str, cfg_rede: dict, cred, ctx) -> dict:
    token, ig_id = token_e_id("instagram", conta, cfg_rede, cred)
    base = base_url(cfg_rede, ctx)
    auth = {"access_token": token}
    perfil = cliente.get(f"{base}/{ig_id}",
                         {"fields": "followers_count,media_count,username", **auth}) or {}
    tolerante = ctx.tolerante("instagram", cliente)
    posts, avisos, insights_ok = [], [], True
    for m in paginar(cliente, f"{base}/{ig_id}/media",
                     {"fields": CAMPOS_MIDIA, "limit": 25, **auth},
                     limite=ctx.limite_posts):
        pub = ler_data(m.get("timestamp"))
        if pub and pub < ctx.desde:
            break  # a lista vem do mais novo para o mais velho
        post = novo_post(m.get("id"), m.get("caption"), tipo_ig(m), pub, m.get("permalink"),
                         curtidas=m.get("like_count"), comentarios=m.get("comments_count"))
        if insights_ok:
            tipo_api = f"{m.get('media_product_type')}/{m.get('media_type')}"
            try:
                v = tolerante.buscar(f"{base}/{m.get('id')}/insights", METRICAS,
                                     tipo_api, auth)
            except ErroNaoAutorizado as e:
                insights_ok = False
                avisos.append(f"insights nao_autorizado: {e}")
            except ErroTemporario as e:
                insights_ok = False
                avisos.append(f"insights interrompidos: {e}")
            except ErroAPI as e:
                avisos.append(f"insights de {m.get('id')}: {e}")
            else:
                for api, campo in MAPA.items():
                    if v.get(api) is not None:
                        post[campo] = v[api]
                if v.get("total_interactions") is not None:
                    post["interacoes"] = v["total_interactions"]
        posts.append(post)
    return {"status": "ok", "usuario": perfil.get("username"),
            "seguidores": perfil.get("followers_count"),
            "posts_total": perfil.get("media_count"),
            "posts": posts, "avisos": avisos}
