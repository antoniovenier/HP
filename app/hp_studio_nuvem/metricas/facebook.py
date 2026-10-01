"""Facebook (Páginas, Graph API): seguidores da Página + posts + reels com insights.

As métricas de insights do Facebook mudam de nome com frequência; por isso a
lista fica no contas.json ("metricas_post" / "metricas_reel") e o pedido é
tolerante: o que a API recusar para aquele tipo é simplesmente pulado.
"""
from __future__ import annotations

from .cliente import ErroAPI, ErroNaoAutorizado, ErroTemporario, paginar
from .config import token_e_id
from .modelos import ler_data, novo_post

CAMPOS_POST = ("id,message,created_time,permalink_url,status_type,shares,"
               "reactions.summary(total_count).limit(0),"
               "comments.summary(total_count).limit(0)")
CAMPOS_REEL = ("id,description,created_time,permalink_url,"
               "likes.summary(total_count).limit(0),comments.summary(total_count).limit(0)")
METRICAS_POST = {"post_impressions_unique": "alcance", "post_video_views": "views"}
METRICAS_REEL = {"blue_reels_play_count": "views", "post_impressions_unique": "alcance"}


def _total(no, chave="summary"):
    if not isinstance(no, dict):
        return None
    return (no.get(chave) or {}).get("total_count")


def tipo_fb(status_type: str | None) -> str:
    return {"added_video": "video", "added_photos": "imagem",
            "mobile_status_update": "texto", "shared_story": "link"}.get(
        status_type or "", (status_type or "outro").lower())


def _insights(tol, url, mapa, tipo, auth, post, avisos, estado):
    if not estado["ok"]:
        return
    try:
        v = tol.buscar(url, list(mapa), tipo, auth)
    except ErroNaoAutorizado as e:
        estado["ok"] = False
        avisos.append(f"insights nao_autorizado: {e}")
    except ErroTemporario as e:
        estado["ok"] = False
        avisos.append(f"insights interrompidos: {e}")
    except ErroAPI as e:
        avisos.append(f"insights de {post['id']}: {e}")
    else:
        for api, campo in mapa.items():
            if v.get(api) is not None and post.get(campo) is None:
                post[campo] = v[api]


def coletar(cliente, conta: str, cfg_rede: dict, cred, ctx) -> dict:
    token, page_id = token_e_id("facebook", conta, cfg_rede, cred)
    base = ctx.base_graph
    auth = {"access_token": token}
    pagina = cliente.get(f"{base}/{page_id}",
                         {"fields": "followers_count,fan_count,name", **auth}) or {}
    tol = ctx.tolerante("facebook", cliente)
    # {"nome_da_metrica_na_api": "campo_nosso"} — trocável no contas.json
    mapa_post = cfg_rede.get("metricas_post") or METRICAS_POST
    mapa_reel = cfg_rede.get("metricas_reel") or METRICAS_REEL
    avisos, estado = [], {"ok": True}

    reels = []
    if cfg_rede.get("reels", True):
        try:
            for m in paginar(cliente, f"{base}/{page_id}/video_reels",
                             {"fields": CAMPOS_REEL, "limit": 25, **auth},
                             limite=ctx.limite_posts):
                pub = ler_data(m.get("created_time"))
                if pub and pub < ctx.desde:
                    break
                link = m.get("permalink_url")
                if link and link.startswith("/"):
                    link = "https://www.facebook.com" + link
                post = novo_post(m.get("id"), m.get("description"), "reels", pub, link,
                                 curtidas=_total(m.get("likes")),
                                 comentarios=_total(m.get("comments")))
                _insights(tol, f"{base}/{m.get('id')}/video_insights", mapa_reel, "reels",
                          auth, post, avisos, estado)
                reels.append(post)
        except ErroNaoAutorizado:
            raise
        except ErroAPI as e:
            avisos.append(f"reels: {e}")

    ids_reels = {p["id"] for p in reels}
    posts = []
    for m in paginar(cliente, f"{base}/{page_id}/posts",
                     {"fields": CAMPOS_POST, "limit": 25, **auth}, limite=ctx.limite_posts):
        pub = ler_data(m.get("created_time"))
        if pub and pub < ctx.desde:
            break
        if str(m.get("id", "")).split("_")[-1] in ids_reels:
            continue  # o mesmo reel aparece no feed com outro id
        tipo = tipo_fb(m.get("status_type"))
        post = novo_post(m.get("id"), m.get("message"), tipo, pub, m.get("permalink_url"),
                         curtidas=_total(m.get("reactions")),
                         comentarios=_total(m.get("comments")),
                         compartilhamentos=(m.get("shares") or {}).get("count", 0))
        _insights(tol, f"{base}/{m.get('id')}/insights", mapa_post, tipo, auth, post,
                  avisos, estado)
        posts.append(post)
    todos = sorted(reels + posts, key=lambda p: p.get("publicado_em") or "", reverse=True)
    return {"status": "ok", "usuario": pagina.get("name"),
            "seguidores": pagina.get("followers_count"), "curtidas_pagina": pagina.get("fan_count"),
            "posts": todos, "avisos": avisos}
