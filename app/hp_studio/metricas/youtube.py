"""YouTube: Data API v3 (inscritos, vídeos, views, curtidas, comentários) e,
quando houver autorização OAuth, YouTube Analytics (compartilhamentos e tempo médio).

Enquanto a auditoria da API do YouTube não termina, o contas.json fica com
"autorizado": false e a rede sai com status "nao_autorizado" (sem chamar nada).
"""
from __future__ import annotations

import re

from .cliente import ErroAPI, ErroNaoAutorizado
from .config import chaves
from .modelos import SemToken, ler_data, novo_post, numero

API = "https://www.googleapis.com/youtube/v3"
ANALYTICS = "https://youtubeanalytics.googleapis.com/v2/reports"
URL_TOKEN = "https://oauth2.googleapis.com/token"
LIMITE_SHORTS_SEG = 180  # Shorts podem ter até 3 min


def duracao_seg(iso_dur) -> int | None:
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", str(iso_dur or ""))
    if not m or not any(m.groups()):
        return None
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


def _token_oauth(cliente, cred, k) -> str | None:
    refresh = cred.obter("youtube", *k["refresh"])
    cid = cred.obter("youtube", *k["client_id"])
    csec = cred.obter("youtube", *k["client_secret"])
    if not (refresh and cid and csec) or not hasattr(cliente, "post"):
        return None
    resp = cliente.post(URL_TOKEN, {"client_id": cid, "client_secret": csec,
                                    "refresh_token": refresh,
                                    "grant_type": "refresh_token"}) or {}
    tok = resp.get("access_token")
    if tok:
        cred.guardar(tok)
        if hasattr(cliente, "registrar_segredo"):
            cliente.registrar_segredo(tok)
    return tok


def _analytics(cliente, oauth: str, posts: list, ctx) -> None:
    por_id = {p["id"]: p for p in posts}
    r = cliente.get(ANALYTICS, {
        "ids": "channel==MINE", "startDate": ctx.desde.date().isoformat(),
        "endDate": ctx.agora.date().isoformat(),
        "metrics": "views,likes,comments,shares,averageViewDuration",
        "dimensions": "video", "filters": "video==" + ",".join(por_id),
        "maxResults": 200, "sort": "-views", "access_token": oauth}) or {}
    cols = [c.get("name") for c in r.get("columnHeaders") or []]
    for linha in r.get("rows") or []:
        d = dict(zip(cols, linha))
        p = por_id.get(d.get("video"))
        if p:
            p["compartilhamentos"] = numero(d.get("shares"))
            p["duracao_media_vista_seg"] = numero(d.get("averageViewDuration"))


def coletar(cliente, conta: str, cfg_rede: dict, cred, ctx) -> dict:
    if not cfg_rede.get("autorizado", False):
        raise ErroNaoAutorizado('YouTube ainda não autorizado (contas.json: "autorizado": false)')
    k = chaves("youtube", conta, cfg_rede)
    canal = cfg_rede.get("id") or cred.obter("youtube", *k["canal"])
    chave_api = cred.obter("youtube", *k["chave_api"])
    avisos = []
    oauth = None
    try:
        oauth = _token_oauth(cliente, cred, k)
    except ErroAPI as e:
        avisos.append(f"analytics nao_autorizado: {e}")
    if not canal:
        raise SemToken(f"youtube/{conta}: falta o id do canal ({k['canal'][1]})")
    if not (chave_api or oauth):
        raise SemToken(f"youtube/{conta}: falta YT_API_KEY (ou refresh token OAuth)")
    auth = {"key": chave_api} if chave_api else {"access_token": oauth}

    ch = cliente.get(f"{API}/channels",
                     {"part": "statistics,contentDetails,snippet", "id": canal, **auth}) or {}
    itens = ch.get("items") or []
    if not itens:
        raise ErroAPI(f"canal {canal} não encontrado")
    st = itens[0].get("statistics") or {}
    uploads = ((itens[0].get("contentDetails") or {}).get("relatedPlaylists") or {}).get("uploads")

    ids, pagina = [], None
    while uploads and len(ids) < ctx.limite_posts:
        params = {"part": "contentDetails", "playlistId": uploads, "maxResults": 50, **auth}
        if pagina:
            params["pageToken"] = pagina
        r = cliente.get(f"{API}/playlistItems", params) or {}
        parar = False
        for it in r.get("items") or []:
            cd = it.get("contentDetails") or {}
            pub = ler_data(cd.get("videoPublishedAt"))
            if pub and pub < ctx.desde:
                parar = True
                break
            if cd.get("videoId"):
                ids.append(cd["videoId"])
            if len(ids) >= ctx.limite_posts:
                parar = True
                break
        pagina = r.get("nextPageToken")
        if parar or not pagina:
            break

    posts = []
    for i in range(0, len(ids), 50):
        r = cliente.get(f"{API}/videos", {"part": "statistics,snippet,contentDetails",
                                          "id": ",".join(ids[i:i + 50]), **auth}) or {}
        for v in r.get("items") or []:
            s, sn = v.get("statistics") or {}, v.get("snippet") or {}
            dur = duracao_seg((v.get("contentDetails") or {}).get("duration"))
            shorts = dur is not None and dur <= LIMITE_SHORTS_SEG
            link = (f"https://youtube.com/shorts/{v['id']}" if shorts
                    else f"https://www.youtube.com/watch?v={v['id']}")
            posts.append(novo_post(v["id"], sn.get("title"), "shorts" if shorts else "video",
                                   sn.get("publishedAt"), link, views=s.get("viewCount"),
                                   curtidas=s.get("likeCount"),
                                   comentarios=s.get("commentCount"), duracao_seg=dur))

    analytics = "nao_autorizado"
    if oauth and posts and cfg_rede.get("analytics", True):
        try:
            _analytics(cliente, oauth, posts, ctx)
            analytics = "ok"
        except ErroNaoAutorizado as e:
            avisos.append(f"analytics nao_autorizado: {e}")
        except ErroAPI as e:
            analytics = "erro"
            avisos.append(f"analytics: {e}")
    oculto = st.get("hiddenSubscriberCount")
    return {"status": "ok", "canal": canal,
            "seguidores": None if oculto else numero(st.get("subscriberCount")),
            "posts_total": numero(st.get("videoCount")),
            "views_canal": numero(st.get("viewCount")),
            "posts": posts, "analytics": analytics, "avisos": avisos}
