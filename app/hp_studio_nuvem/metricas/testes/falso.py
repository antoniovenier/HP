"""Cliente falso (nenhum acesso à rede) e dados de exemplo para a conta gta."""
from __future__ import annotations

import copy
from datetime import datetime
from urllib.parse import urlsplit

from hpbase import FUSO

from metricas.cliente import ErroAPI
from metricas.config import carregar_config

AGORA = datetime(2026, 9, 30, 6, 0, tzinfo=FUSO)

IG_ID, TH_ID, PAGE_ID, CANAL = "17841400000000001", "2600000000000001", "1000000000000001", "UCgta"
TOKENS = {
    "IG_GTA_TOKEN": "EAABsegredoInstagram0123456789abcdef",
    "TH_GTA_TOKEN": "THAAsegredoThreads0123456789",
    "FB_GTA_TOKEN": "EAABsegredoPagina0123456789abcdefgh",
    "YT_API_KEY": "AIzaSegredoGoogle0123456789abcdefghijk",
    "YT_CLIENT_SECRET": "GOCSPX-segredoCliente123",
    "YT_GTA_REFRESH_TOKEN": "1//segredoRefresh0123456789",
}
OAUTH = "ya29.segredoAcesso0123456789"


def escrever_segredos(local, sem=()):
    pasta = local / "segredos"
    pasta.mkdir(parents=True, exist_ok=True)
    meta = {"IG_GTA_TOKEN": TOKENS["IG_GTA_TOKEN"], "IG_GTA_ID": IG_ID,
            "TH_GTA_TOKEN": TOKENS["TH_GTA_TOKEN"], "TH_GTA_ID": TH_ID,
            "FB_GTA_TOKEN": TOKENS["FB_GTA_TOKEN"], "FB_GTA_ID": PAGE_ID}
    yt = {"YT_API_KEY": TOKENS["YT_API_KEY"], "YT_GTA_CANAL": CANAL,
          "YT_CLIENT_ID": "123-abc.apps.googleusercontent.com",
          "YT_CLIENT_SECRET": TOKENS["YT_CLIENT_SECRET"],
          "YT_GTA_REFRESH_TOKEN": TOKENS["YT_GTA_REFRESH_TOKEN"]}
    for nome, dados in (("meta_tokens.txt", meta), ("youtube_tokens.txt", yt)):
        linhas = ["# teste"] + [f"{k}={v}" for k, v in dados.items() if k not in sem]
        (pasta / nome).write_text("\n".join(linhas) + "\n", encoding="utf-8")


def config_teste(youtube_autorizado=True) -> dict:
    cfg = copy.deepcopy(carregar_config())
    cfg["contas"]["gta"]["youtube"]["autorizado"] = youtube_autorizado
    return cfg


def erro_400(metrica):
    return ErroAPI(f"HTTP 400: (#100) The metric {metrica} is not supported", status=400, codigo=100)


def insights(valores: dict, recusadas=()):
    """Rota de insights: recusa (400) o pedido inteiro se tiver métrica recusada."""
    def responder(params):
        pedidas = params["metric"].split(",")
        ruins = [m for m in pedidas if m in recusadas]
        if ruins:
            raise erro_400(ruins[0])
        return {"data": [{"name": m, "period": "lifetime", "values": [{"value": valores[m]}]}
                         for m in pedidas if m in valores]}
    return responder


class ClienteFalso:
    """Responde por caminho (sem host/versão) ou por URL completa (paging.next)."""

    def __init__(self, rotas=None, rotas_post=None):
        self.rotas = dict(rotas or {})
        self.rotas_post = dict(rotas_post or {})
        self.chamadas: list = []

    def _achar(self, rotas, url):
        if url in rotas:
            return rotas[url]
        caminho = urlsplit(url).path
        for chave in sorted(rotas, key=len, reverse=True):
            if not chave.startswith("http") and caminho.endswith(chave):
                return rotas[chave]
        return None

    def _responder(self, rotas, url, params):
        self.chamadas.append((url, dict(params or {})))
        r = self._achar(rotas, url)
        if r is None:
            raise ErroAPI(f"HTTP 404 rota falsa inexistente: {urlsplit(url).path}", status=404)
        if callable(r):
            r = r(dict(params or {}))
        if isinstance(r, Exception):
            raise r
        return copy.deepcopy(r)

    def get(self, url, params=None):
        return self._responder(self.rotas, url, params)

    def post(self, url, dados=None):
        return self._responder(self.rotas_post, url, dados)

    def contar(self, trecho: str) -> int:
        return sum(1 for u, _ in self.chamadas if trecho in u)


PAGINA2 = (f"https://graph.facebook.com/v21.0/{IG_ID}/media?after=CUR2"
           f"&access_token={TOKENS['IG_GTA_TOKEN']}")
PAGINA3 = f"https://graph.facebook.com/v21.0/{IG_ID}/media?after=CUR3"


def rotas_instagram():
    return {
        f"/{IG_ID}": {"followers_count": 1500, "media_count": 120, "username": "hpgta6"},
        f"/{IG_ID}/media": {"data": [
            {"id": "M1", "caption": "Trailer 3 do GTA 6: tudo o que sabemos #gta6",
             "media_type": "VIDEO", "media_product_type": "REELS",
             "timestamp": "2026-09-30T01:00:00+0000", "permalink": "https://instagram.com/reel/M1",
             "like_count": 300, "comments_count": 40},
            {"id": "M2", "caption": "Carrossel: 10 carros do GTA 6", "media_type": "CAROUSEL_ALBUM",
             "media_product_type": "FEED", "timestamp": "2026-09-28T15:00:00+0000",
             "permalink": "https://instagram.com/p/M2", "like_count": 120, "comments_count": 10},
        ], "paging": {"next": PAGINA2}},
        PAGINA2: {"data": [
            {"id": "M3", "caption": "Outro carrossel", "media_type": "CAROUSEL_ALBUM",
             "media_product_type": "FEED", "timestamp": "2026-09-26T15:00:00+0000",
             "permalink": "https://instagram.com/p/M3", "like_count": 80, "comments_count": 5},
            {"id": "M4", "caption": "Velho", "media_type": "IMAGE", "media_product_type": "FEED",
             "timestamp": "2026-09-20T15:00:00+0000", "permalink": "https://instagram.com/p/M4",
             "like_count": 1, "comments_count": 0},
        ], "paging": {"next": PAGINA3}},
        PAGINA3: ErroAPI("não deveria buscar a página 3", status=500),
        "/M1/insights": insights({"reach": 5000, "saved": 60, "shares": 100, "views": 9000,
                                  "total_interactions": 500}),
        "/M2/insights": insights({"reach": 2000, "saved": 30, "shares": 40,
                                  "total_interactions": 200}, recusadas=("views",)),
        "/M3/insights": insights({"reach": 1000, "saved": 10, "shares": 10,
                                  "total_interactions": 105}, recusadas=("views",)),
    }


def rotas_threads():
    return {
        f"/{TH_ID}": {"username": "hpgta6", "id": TH_ID},
        f"/{TH_ID}/threads_insights": {"data": [{"name": "followers_count",
                                                 "total_value": {"value": 800}}]},
        f"/{TH_ID}/threads": {"data": [
            {"id": "T0", "media_type": "REPOST_FACADE", "timestamp": "2026-09-30T02:00:00+0000"},
            {"id": "T1", "text": "Qual carro você quer no GTA 6?", "media_type": "TEXT_POST",
             "timestamp": "2026-09-29T20:00:00+0000", "permalink": "https://threads.net/t/T1"},
        ]},
        "/T1/insights": insights({"views": 1200, "likes": 50, "replies": 12, "reposts": 3,
                                  "quotes": 1}),
    }


def rotas_facebook():
    return {
        f"/{PAGE_ID}": {"followers_count": 3000, "fan_count": 2900, "name": "GTA 6 | HP"},
        f"/{PAGE_ID}/video_reels": {"data": [
            {"id": "555", "description": "Reel no Facebook", "created_time": "2026-09-29T18:00:00+0000",
             "permalink_url": "/reel/555", "likes": {"summary": {"total_count": 40}},
             "comments": {"summary": {"total_count": 4}}}]},
        "/555/video_insights": insights({"blue_reels_play_count": 5000,
                                         "post_impressions_unique": 4000}),
        f"/{PAGE_ID}/posts": {"data": [
            {"id": f"{PAGE_ID}_555", "message": "Reel no Facebook", "status_type": "added_video",
             "created_time": "2026-09-29T18:00:00+0000"},
            {"id": f"{PAGE_ID}_777", "message": "Foto do mapa", "status_type": "added_photos",
             "created_time": "2026-09-27T18:00:00+0000",
             "permalink_url": "https://facebook.com/777",
             "reactions": {"summary": {"total_count": 30}},
             "comments": {"summary": {"total_count": 3}}, "shares": {"count": 2}}]},
        f"/{PAGE_ID}_777/insights": insights({"post_impressions_unique": 900},
                                             recusadas=("post_video_views",)),
    }


def rotas_youtube():
    def playlist(params):
        if params.get("pageToken") == "P2":
            return {"items": [{"contentDetails": {"videoId": "V3",
                                                  "videoPublishedAt": "2026-09-10T10:00:00Z"}}]}
        return {"items": [
            {"contentDetails": {"videoId": "V1", "videoPublishedAt": "2026-09-29T22:00:00Z"}},
            {"contentDetails": {"videoId": "V2", "videoPublishedAt": "2026-09-27T22:00:00Z"}}],
            "nextPageToken": "P2"}

    def videos(params):
        base = {"V1": ("Shorts GTA", "PT45S", "7000", "400", "20"),
                "V2": ("Vídeo longo", "PT12M3S", "1500", "90", "15")}
        itens = []
        for vid in params["id"].split(","):
            t, d, v, l, c = base[vid]
            itens.append({"id": vid, "snippet": {"title": t, "publishedAt":
                                                  "2026-09-29T22:00:00Z" if vid == "V1"
                                                  else "2026-09-27T22:00:00Z"},
                          "contentDetails": {"duration": d},
                          "statistics": {"viewCount": v, "likeCount": l, "commentCount": c}})
        return {"items": itens}

    return {
        "/youtube/v3/channels": {"items": [{
            "statistics": {"subscriberCount": "2500", "videoCount": "80", "viewCount": "100000",
                           "hiddenSubscriberCount": False},
            "contentDetails": {"relatedPlaylists": {"uploads": "UUgta"}}}]},
        "/youtube/v3/playlistItems": playlist,
        "/youtube/v3/videos": videos,
        "/v2/reports": {"columnHeaders": [{"name": "video"}, {"name": "views"}, {"name": "likes"},
                                          {"name": "comments"}, {"name": "shares"},
                                          {"name": "averageViewDuration"}],
                        "rows": [["V1", 7000, 400, 20, 55, 30], ["V2", 1500, 90, 15, 5, 240]]},
    }


def cliente_completo(**trocas) -> ClienteFalso:
    rotas = {}
    for f in (rotas_instagram, rotas_threads, rotas_facebook, rotas_youtube):
        rotas.update(f())
    rotas.update(trocas)
    return ClienteFalso(rotas, {"/token": {"access_token": OAUTH, "expires_in": 3599}})
