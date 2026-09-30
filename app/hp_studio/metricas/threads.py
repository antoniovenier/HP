"""Threads (API oficial em graph.threads.net): seguidores + posts com insights."""
from __future__ import annotations

from .cliente import ErroAPI, ErroNaoAutorizado, ErroTemporario, paginar
from .config import token_e_id
from .insights import ler_valores
from .modelos import ler_data, novo_post

CAMPOS = "id,text,media_type,media_product_type,timestamp,permalink,is_quote_post"
METRICAS = ("views", "likes", "replies", "reposts", "quotes")


def tipo_threads(m: dict) -> str:
    return {"TEXT_POST": "texto", "IMAGE": "imagem", "VIDEO": "video",
            "CAROUSEL_ALBUM": "carrossel", "AUDIO": "audio"}.get(
        (m.get("media_type") or "").upper(), (m.get("media_type") or "outro").lower())


def coletar(cliente, conta: str, cfg_rede: dict, cred, ctx) -> dict:
    token, uid = token_e_id("threads", conta, cfg_rede, cred)
    base = ctx.base_threads
    auth = {"access_token": token}
    perfil = cliente.get(f"{base}/{uid}", {"fields": "username", **auth}) or {}
    seg = ler_valores(cliente.get(f"{base}/{uid}/threads_insights",
                                  {"metric": "followers_count", **auth}))
    tolerante = ctx.tolerante("threads", cliente)
    posts, avisos, insights_ok = [], [], True
    for m in paginar(cliente, f"{base}/{uid}/threads",
                     {"fields": CAMPOS, "limit": 25, **auth}, limite=ctx.limite_posts):
        if (m.get("media_type") or "").upper() == "REPOST_FACADE":
            continue  # repost de post dos outros: não é nosso
        pub = ler_data(m.get("timestamp"))
        if pub and pub < ctx.desde:
            break
        post = novo_post(m.get("id"), m.get("text"), tipo_threads(m), pub, m.get("permalink"))
        if insights_ok:
            try:
                v = tolerante.buscar(f"{base}/{m.get('id')}/insights", METRICAS,
                                     tipo_threads(m), auth)
            except ErroNaoAutorizado as e:
                insights_ok = False
                avisos.append(f"insights nao_autorizado: {e}")
            except ErroTemporario as e:
                insights_ok = False
                avisos.append(f"insights interrompidos: {e}")
            except ErroAPI as e:
                avisos.append(f"insights de {m.get('id')}: {e}")
            else:
                post["views"] = v.get("views")
                post["curtidas"] = v.get("likes")
                post["comentarios"] = v.get("replies")
                rep = [v.get(k) for k in ("reposts", "quotes") if v.get(k) is not None]
                post["compartilhamentos"] = sum(rep) if rep else None
                post["reposts"], post["citacoes"] = v.get("reposts"), v.get("quotes")
        posts.append(post)
    return {"status": "ok", "usuario": perfil.get("username"),
            "seguidores": seg.get("followers_count"), "posts": posts, "avisos": avisos}
