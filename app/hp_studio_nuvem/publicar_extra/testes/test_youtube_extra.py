"""Testes do youtube_extra (tarefa B da rodada 2) — tudo com ClienteFalso, sem rede, sem relógio.

Cada chamada à API tem URL, método, parâmetros (consulta) e corpo (json_/corpo) conferidos;
paginação, idempotência (0 POST na segunda vez), cache de playlists lido/gravado, snippet completo
e publishAt em UTC, validações antes da API, os 3 diagnósticos de "travado", SRT golden com a
fixture real do PC, legenda desligada por padrão, cota a 80 %, tradução de erros e a prova de
que o token FAKE_NAO_E_TOKEN_1 nunca aparece em resultado, exceção, log do cliente nem arquivo.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

_HP = str(Path(__file__).resolve().parents[2])  # ...\app\hp_studio_nuvem
if _HP not in sys.path:
    sys.path.insert(0, _HP)
from hpbase.pytest_raizes import raizes_temporarias  # noqa: E402,F401  (autouse: H:/G: → pastas temporárias)
from hpbase import FUSO, pasta_app  # noqa: E402
from publicar_extra.contrato_pc import ClienteFalso, ErroRede, Resposta  # noqa: E402
from publicar_extra import youtube_extra as ye  # noqa: E402

TOKEN = "FAKE_NAO_E_TOKEN_1"
API = ye.API
RAIZ = Path(__file__).resolve().parents[4]
FIXTURE_TRANSCRICAO = RAIZ / "tests" / "fixtures" / "pc_real" / "transcricao_exemplo.json"
AGORA = datetime(2026, 10, 1, 10, 0, tzinfo=FUSO)   # 01/10/2026 10:00 Brasília = 13:00Z
TITULO = "GTA 6 — Notícias"


# ------------------------------------------------------------------ apoio
def erro_google(status: int, reason: str, msg: str = "erro do Google") -> Resposta:
    return Resposta(status, {"error": {"code": status, "message": msg,
                                       "errors": [{"reason": reason, "domain": "youtube"}]}})


def video(vid: str, privacy="private", publish_at=None, upload="processed", **status_extra) -> dict:
    st = {"privacyStatus": privacy, "uploadStatus": upload, "license": "youtube", "embeddable": True,
          "publicStatsViewable": True, "selfDeclaredMadeForKids": False,
          "containsSyntheticMedia": True}
    if publish_at:
        st["publishAt"] = publish_at
    st.update(status_extra)
    return {"id": vid, "snippet": {"title": "Antigo", "description": "desc", "tags": ["a"],
                                   "categoryId": "20", "defaultLanguage": "pt",
                                   "publishedAt": "2026-09-30T12:00:00Z", "channelId": "UCx"},
            "status": st}


def sem_token(*coisas) -> None:
    for c in coisas:
        s = str(c)
        assert TOKEN not in s, "token vazou"
        assert "FAKE_NAO_E_TOKEN" not in s, "token vazou"


def bearer_ok(cliente: ClienteFalso) -> None:
    assert cliente.chamadas, "nenhuma chamada"
    for ch in cliente.chamadas:
        assert ch.cabecalhos["Authorization"] == f"Bearer {TOKEN}"
        assert TOKEN not in ch.url and "access_token" not in ch.url
        assert TOKEN not in json.dumps(ch.consulta or {})
        assert "access_token" not in (ch.consulta or {}) and "key" not in (ch.consulta or {})
        assert TOKEN not in json.dumps(ch.json_, default=str)


@pytest.fixture
def cliente() -> ClienteFalso:
    return ClienteFalso()


@pytest.fixture
def cache() -> ye.CacheMemoria:
    return ye.CacheMemoria()


@pytest.fixture
def cont() -> ye.Contador:
    return ye.Contador()


# ================================================================== B1 playlists
def test_playlist_lista_url_metodo_parametros_e_bearer(cliente, cache):
    cliente.responder("GET", r"/playlists$", {"items": [{"id": "PL1", "snippet": {"title": TITULO}}]})
    assert ye.playlist_do_canal(cliente, TOKEN, "gta", TITULO, cache=cache) == "PL1"
    ch = cliente.chamadas[0]
    assert (ch.metodo, ch.url) == ("GET", f"{API}/playlists")
    assert ch.consulta == {"part": "snippet", "mine": "true", "maxResults": 50}
    assert len(cliente.chamadas) == 1 and not cliente.chamadas_de("POST")
    bearer_ok(cliente)


def test_playlist_paginacao_duas_paginas(cliente, cache):
    cliente.responder("GET", r"/playlists$", [
        {"items": [{"id": "PLa", "snippet": {"title": "Outra"}}], "nextPageToken": "pag2"},
        {"items": [{"id": "PL2", "snippet": {"title": TITULO}}]},
    ])
    assert ye.playlist_do_canal(cliente, TOKEN, "gta", TITULO, cache=cache) == "PL2"
    gets = cliente.chamadas_de("GET", r"/playlists$")
    assert len(gets) == 2
    assert "pageToken" not in gets[0].consulta
    assert gets[1].consulta["pageToken"] == "pag2"
    assert not cliente.chamadas_de("POST")


def test_playlist_compara_titulo_sem_acento_maiuscula_e_espacos(cliente, cache):
    cliente.responder("GET", r"/playlists$", {"items": [{"id": "PLx", "snippet": {"title": "  gta 6 — NOTICIAS "}}]})
    assert ye.playlist_do_canal(cliente, TOKEN, "gta", TITULO, cache=cache) == "PLx"
    assert not cliente.chamadas_de("POST")
    assert ye.normalizar_titulo("  Notícias   de GTA ") == "noticias de gta"


def test_playlist_cria_quando_nao_existe_com_corpo_exato(cliente, cache):
    cliente.responder("GET", r"/playlists$", {"items": []})
    cliente.responder("POST", r"/playlists$", {"id": "PLNOVA"})
    assert ye.playlist_do_canal(cliente, TOKEN, "gta", TITULO, cache=cache) == "PLNOVA"
    post = cliente.chamadas_de("POST")[0]
    assert post.url == f"{API}/playlists"
    assert post.consulta == {"part": "snippet,status"}
    assert post.json_ == {"snippet": {"title": TITULO, "description": ""},
                          "status": {"privacyStatus": "public"}}
    bearer_ok(cliente)


def test_playlist_nao_cria_com_criar_false(cliente, cache):
    cliente.responder("GET", r"/playlists$", {"items": []})
    assert ye.playlist_do_canal(cliente, TOKEN, "gta", TITULO, criar=False, cache=cache) is None
    assert not cliente.chamadas_de("POST")
    assert cache.gravacoes == 0


def test_playlist_idempotente_segunda_vez_zero_post_e_zero_chamadas(cliente, cache):
    cliente.responder("GET", r"/playlists$", {"items": []})
    cliente.responder("POST", r"/playlists$", {"id": "PLNOVA"})
    a = ye.playlist_do_canal(cliente, TOKEN, "gta", TITULO, cache=cache)
    n = len(cliente.chamadas)
    b = ye.playlist_do_canal(cliente, TOKEN, "gta", TITULO, cache=cache)
    assert a == b == "PLNOVA"
    assert len(cliente.chamadas_de("POST")) == 1
    assert len(cliente.chamadas) == n, "segunda vez não deve chamar a API (cache)"


def test_playlist_cache_consultado_antes_da_api(cliente):
    cache = ye.CacheMemoria({"gta": {"gta 6 — noticias": "PLC"}})
    assert ye.playlist_do_canal(cliente, TOKEN, "gta", TITULO, cache=cache) == "PLC"
    assert cliente.chamadas == []
    # canal diferente não aproveita o cache do outro
    cliente.responder("GET", r"/playlists$", {"items": [{"id": "PLF", "snippet": {"title": TITULO}}]})
    assert ye.playlist_do_canal(cliente, TOKEN, "futebol", TITULO, cache=cache) == "PLF"
    assert len(cliente.chamadas) == 1


def test_playlist_cache_gravado_no_formato_canal_titulo_id(cliente, cache):
    cliente.responder("GET", r"/playlists$", {"items": []})
    cliente.responder("POST", r"/playlists$", {"id": "PLNOVA"})
    ye.playlist_do_canal(cliente, TOKEN, "gta", TITULO, cache=cache)
    assert cache.dados == {"gta": {TITULO: "PLNOVA"}}
    assert cache.gravacoes == 1


def test_playlist_cache_arquivo_padrao_em_pasta_app(cliente):
    cliente.responder("GET", r"/playlists$", {"items": [{"id": "PL1", "snippet": {"title": TITULO}}]})
    assert ye.playlist_do_canal(cliente, TOKEN, "gta", TITULO) == "PL1"
    arq = pasta_app() / "publicar" / "youtube_playlists.json"
    assert arq.exists(), "cache padrão: app\\publicar\\youtube_playlists.json (abaixo de HP_LOCAL)"
    assert json.loads(arq.read_text(encoding="utf-8")) == {"gta": {TITULO: "PL1"}}
    assert not list(arq.parent.glob(".tmp_*")), "gravação atômica não deixa .tmp"
    sem_token(arq.read_text(encoding="utf-8"))
    # segunda vez lê o arquivo e não chama a API
    n = len(cliente.chamadas)
    assert ye.playlist_do_canal(cliente, TOKEN, "gta", TITULO) == "PL1"
    assert len(cliente.chamadas) == n


def test_playlist_registra_cota(cliente, cache, cont):
    cliente.responder("GET", r"/playlists$", {"items": []})
    cliente.responder("POST", r"/playlists$", {"id": "PLNOVA"})
    ye.playlist_do_canal(cliente, TOKEN, "gta", TITULO, cache=cache, registrar=cont.registrar)
    assert cont.chamadas == ["playlists.list", "playlists.insert"]
    assert cont.resumo()["total"] == 51


def test_playlist_erro_http_vira_portugues_sem_token(cliente, cache):
    cliente.responder("GET", r"/playlists$", ErroRede(f"HTTP 403 forbidden Bearer {TOKEN}", status=403))
    with pytest.raises(ye.ErroYouTube) as exc:
        ye.playlist_do_canal(cliente, TOKEN, "gta", TITULO, cache=cache)
    assert "permissão" in str(exc.value)
    sem_token(exc.value, repr(exc.value), cliente.texto_de_tudo())


def test_playlist_titulo_vazio_recusa_antes_da_api(cliente, cache):
    with pytest.raises(ValueError):
        ye.playlist_do_canal(cliente, TOKEN, "gta", "   ", cache=cache)
    assert cliente.chamadas == []


def test_adicionar_confere_antes_com_get_parametros(cliente):
    cliente.responder("GET", r"/playlistItems$", {"items": []})
    cliente.responder("POST", r"/playlistItems$", {"id": "PI9"})
    ye.adicionar_na_playlist(cliente, TOKEN, "PL1", "v1")
    get = cliente.chamadas[0]
    assert (get.metodo, get.url) == ("GET", f"{API}/playlistItems")
    assert get.consulta == {"part": "snippet", "playlistId": "PL1", "videoId": "v1", "maxResults": 50}


def test_adicionar_post_corpo_exato_e_resultado(cliente):
    cliente.responder("GET", r"/playlistItems$", {"items": []})
    cliente.responder("POST", r"/playlistItems$", {"id": "PI9"})
    r = ye.adicionar_na_playlist(cliente, TOKEN, "PL1", "v1")
    post = cliente.chamadas_de("POST")[0]
    assert post.url == f"{API}/playlistItems" and post.consulta == {"part": "snippet"}
    assert post.json_ == {"snippet": {"playlistId": "PL1",
                                      "resourceId": {"kind": "youtube#video", "videoId": "v1"}}}
    assert r["status"] == "adicionado" and r["id"] == "PI9" and r["erro"] is None
    assert r["link"] == "https://www.youtube.com/watch?v=v1&list=PL1"
    assert set(r) >= {"status", "link", "id", "erro"}
    bearer_ok(cliente)


def test_adicionar_ja_estava_nao_posta(cliente):
    cliente.responder("GET", r"/playlistItems$", {"items": [{"id": "PI1"}]})
    r = ye.adicionar_na_playlist(cliente, TOKEN, "PL1", "v1")
    assert r["status"] == "ja_estava" and r["id"] == "PI1" and r["erro"] is None
    assert not cliente.chamadas_de("POST")


@pytest.mark.parametrize("resposta", [
    erro_google(409, "duplicate"),
    erro_google(409, "videoAlreadyInPlaylist"),
    ErroRede("HTTP 409 duplicate", status=409),
])
def test_adicionar_409_duplicate_nao_e_falha(cliente, resposta):
    cliente.responder("GET", r"/playlistItems$", {"items": []})
    cliente.responder("POST", r"/playlistItems$", resposta)
    r = ye.adicionar_na_playlist(cliente, TOKEN, "PL1", "v1")
    assert r["status"] == "ja_estava" and r["erro"] is None


def test_adicionar_idempotente_duas_vezes_um_post(cliente):
    cliente.responder("GET", r"/playlistItems$", [{"items": []}, {"items": [{"id": "PI9"}]}])
    cliente.responder("POST", r"/playlistItems$", {"id": "PI9"})
    a = ye.adicionar_na_playlist(cliente, TOKEN, "PL1", "v1")
    b = ye.adicionar_na_playlist(cliente, TOKEN, "PL1", "v1")
    assert (a["status"], b["status"]) == ("adicionado", "ja_estava")
    assert len(cliente.chamadas_de("POST")) == 1


def test_adicionar_erro_de_cota_vira_entrada_erro(cliente, cont):
    cliente.responder("GET", r"/playlistItems$", erro_google(403, "quotaExceeded"))
    r = ye.adicionar_na_playlist(cliente, TOKEN, "PL1", "v1", registrar=cont.registrar)
    assert r["status"] == "erro" and "cota diária" in r["erro"]
    assert cont.chamadas == ["playlistItems.list"]
    sem_token(r, cliente.texto_de_tudo())


# ================================================================== B2 atualizar_video
def test_atualizar_le_e_manda_snippet_e_status_completos(cliente):
    cliente.responder("GET", r"/videos$", {"items": [video("v1")]})
    cliente.responder("PUT", r"/videos$", {"id": "v1", "status": {"privacyStatus": "private"}})
    r = ye.atualizar_video(cliente, TOKEN, "v1", titulo="Novo título")
    get, put = cliente.chamadas
    assert (get.metodo, get.url, get.consulta) == ("GET", f"{API}/videos", {"part": "snippet,status", "id": "v1"})
    assert (put.metodo, put.url, put.consulta) == ("PUT", f"{API}/videos", {"part": "snippet,status"})
    assert put.json_["id"] == "v1"
    assert put.json_["snippet"] == {"title": "Novo título", "description": "desc", "tags": ["a"],
                                    "categoryId": "20", "defaultLanguage": "pt"}
    assert put.json_["status"] == {"privacyStatus": "private", "license": "youtube", "embeddable": True,
                                   "publicStatsViewable": True, "selfDeclaredMadeForKids": False,
                                   "containsSyntheticMedia": True}
    assert "uploadStatus" not in put.json_["status"] and "publishedAt" not in put.json_["snippet"]
    assert r["status"] == "atualizado" and r["id"] == "v1" and r["erro"] is None
    bearer_ok(cliente)


@pytest.mark.parametrize("publicar_em", [datetime(2026, 10, 2, 9, 0), "2026-10-02 09:00",
                                         datetime(2026, 10, 2, 9, 0, tzinfo=FUSO)])
def test_atualizar_publish_at_em_utc_z_com_private(cliente, publicar_em):
    cliente.responder("GET", r"/videos$", {"items": [video("v1")]})
    cliente.responder("PUT", r"/videos$", lambda ch: Resposta(200, {"id": "v1", "status": ch.json_["status"]}))
    r = ye.atualizar_video(cliente, TOKEN, "v1", publicar_em=publicar_em, agora=AGORA)
    st = cliente.chamadas_de("PUT")[0].json_["status"]
    assert st["publishAt"] == "2026-10-02T12:00:00Z" and st["privacyStatus"] == "private"
    assert r["status"] == "agendado" and r["publishAt"] == "2026-10-02T12:00:00Z"
    assert r["publicar_em"] == "2026-10-02 09:00"


def test_atualizar_titulo_101_recusa_antes_da_api(cliente):
    r = ye.atualizar_video(cliente, TOKEN, "v1", titulo="x" * 101)
    assert r["status"] == "invalido" and "101" in r["erro"] and "100" in r["erro"]
    assert cliente.chamadas == []
    cliente.responder("GET", r"/videos$", {"items": [video("v1")]})
    cliente.responder("PUT", r"/videos$", {"id": "v1"})
    assert ye.atualizar_video(cliente, TOKEN, "v1", titulo="x" * 100)["status"] == "atualizado"  # 100 passa


def test_atualizar_titulo_com_menor_ou_maior_recusa(cliente):
    for t in ("a <b> c", "a > b"):
        r = ye.atualizar_video(cliente, TOKEN, "v1", titulo=t)
        assert r["status"] == "invalido" and "<" in r["erro"]
    assert cliente.chamadas == []


def test_atualizar_descricao_acima_de_5000_bytes_com_acento(cliente):
    desc = "é" * 2600   # 2.600 caracteres, 5.200 bytes em UTF-8
    r = ye.atualizar_video(cliente, TOKEN, "v1", descricao=desc)
    assert r["status"] == "invalido" and "5200 bytes" in r["erro"] and "2600 caracteres" in r["erro"]
    assert cliente.chamadas == []
    cliente.responder("GET", r"/videos$", {"items": [video("v1")]})
    cliente.responder("PUT", r"/videos$", {"id": "v1"})
    assert ye.atualizar_video(cliente, TOKEN, "v1", descricao="a" * 5000)["status"] == "atualizado"


def test_contar_tags_como_o_youtube():
    assert ye.contar_tags(["Foo-Baz"]) == 7
    assert ye.contar_tags(["Foo Baz"]) == 9          # aspas contam
    assert ye.contar_tags(["a", "b"]) == 3           # vírgula conta
    assert ye.contar_tags([]) == 0


def test_atualizar_tags_acima_de_500_recusa(cliente):
    r = ye.atualizar_video(cliente, TOKEN, "v1", tags=["abcdefghi"] * 51)   # 459 + 50 vírgulas = 509
    assert r["status"] == "invalido" and "509" in r["erro"]
    r = ye.atualizar_video(cliente, TOKEN, "v1", tags=["ab cd"] * 70)       # 70×7 + 69 = 559
    assert r["status"] == "invalido" and "559" in r["erro"]
    r = ye.atualizar_video(cliente, TOKEN, "v1", tags=["a", ""])
    assert r["status"] == "invalido" and "vazia" in r["erro"]
    r = ye.atualizar_video(cliente, TOKEN, "v1", tags="a,b")
    assert r["status"] == "invalido" and "lista" in r["erro"]
    assert cliente.chamadas == []


def test_atualizar_categoria_nao_numerica_recusa(cliente):
    r = ye.atualizar_video(cliente, TOKEN, "v1", categoria="Jogos")
    assert r["status"] == "invalido" and "número" in r["erro"]
    assert cliente.chamadas == []


def test_atualizar_publicar_em_no_passado_recusa(cliente):
    r = ye.atualizar_video(cliente, TOKEN, "v1", publicar_em=AGORA - timedelta(hours=1), agora=AGORA)
    assert r["status"] == "invalido" and "já passou" in r["erro"]
    assert cliente.chamadas == []


def test_atualizar_video_publico_nao_agenda(cliente):
    cliente.responder("GET", r"/videos$", {"items": [video("v1", privacy="public")]})
    r = ye.atualizar_video(cliente, TOKEN, "v1", publicar_em=datetime(2026, 10, 2, 9, 0), agora=AGORA)
    assert r["status"] == "invalido" and "public" in r["erro"]
    assert not cliente.chamadas_de("PUT")


def test_atualizar_privacidade_public_tira_publish_at(cliente):
    cliente.responder("GET", r"/videos$", {"items": [video("v1", publish_at="2026-10-02T12:00:00Z")]})
    cliente.responder("PUT", r"/videos$", {"id": "v1"})
    r = ye.atualizar_video(cliente, TOKEN, "v1", privacidade="public")
    st = cliente.chamadas_de("PUT")[0].json_["status"]
    assert st["privacyStatus"] == "public" and "publishAt" not in st
    assert r["status"] == "atualizado"


def test_atualizar_video_nao_encontrado(cliente):
    cliente.responder("GET", r"/videos$", {"items": []})
    r = ye.atualizar_video(cliente, TOKEN, "v1", titulo="x")
    assert r["status"] == "erro" and "não encontrado" in r["erro"]
    assert not cliente.chamadas_de("PUT")


def test_atualizar_401_token_vencido(cliente):
    cliente.responder("GET", r"/videos$", {"items": [video("v1")]})
    cliente.responder("PUT", r"/videos$", erro_google(401, "authError"))
    r = ye.atualizar_video(cliente, TOKEN, "v1", titulo="x")
    assert r["status"] == "erro" and "token vencido: o PC renova" in r["erro"]
    sem_token(r, cliente.texto_de_tudo())


def test_atualizar_registra_cota(cliente, cont):
    cliente.responder("GET", r"/videos$", {"items": [video("v1")]})
    cliente.responder("PUT", r"/videos$", {"id": "v1"})
    ye.atualizar_video(cliente, TOKEN, "v1", titulo="x", registrar=cont.registrar)
    assert cont.chamadas == ["videos.list", "videos.update"]
    assert cont.resumo()["total"] == 51


# ================================================================== B3 conferir_lote
def _esperado(ids, status_pedido="agendado", publicar_em="2026-10-02 09:00"):
    return {v: {"status_pedido": status_pedido, "publicar_em": publicar_em} for v in ids}


def test_conferir_120_ids_em_3_chamadas_com_part_e_ids(cliente):
    ids = [f"v{i:03d}" for i in range(120)]
    cliente.responder("GET", r"/videos$", lambda ch: Resposta(200, {
        "items": [video(v, publish_at="2026-10-02T12:00:00Z") for v in ch.consulta["id"].split(",")]}))
    r = ye.conferir_lote(cliente, TOKEN, _esperado(ids), agora=AGORA)
    gets = cliente.chamadas_de("GET", r"/videos$")
    assert len(gets) == 3 and r["resumo"]["chamadas"] == 3
    for g in gets:
        assert g.consulta["part"] == "status,snippet,processingDetails"
        assert g.consulta["maxResults"] == 50
    assert gets[0].consulta["id"] == ",".join(ids[:50])
    assert gets[2].consulta["id"] == ",".join(ids[100:])
    assert r["resumo"]["ok"] == 120 and r["resumo"]["total"] == 120
    assert all(r[v]["status"] == "ok" for v in ids)
    bearer_ok(cliente)


def test_conferir_agendado_ficou_privado_sem_publish_at(cliente):
    cliente.responder("GET", r"/videos$", {"items": [video("v1")]})
    r = ye.conferir_lote(cliente, TOKEN, _esperado(["v1"]), agora=AGORA)
    assert r["v1"]["status"] == "travado_privado"
    assert ye.TRAVADO in r["v1"]["diagnostico"]
    assert r["v1"]["privacy"] == "private" and r["v1"]["publishAt"] is None
    assert r["resumo"]["travado_privado"] == 1


def test_conferir_publico_ficou_privado(cliente):
    cliente.responder("GET", r"/videos$", {"items": [video("v1")]})
    r = ye.conferir_lote(cliente, TOKEN, _esperado(["v1"], "publico", None), agora=AGORA)
    assert r["v1"]["status"] == "travado_privado" and ye.TRAVADO in r["v1"]["diagnostico"]


def test_conferir_agendado_passou_do_horario_e_continua_privado(cliente):
    cliente.responder("GET", r"/videos$", {"items": [video("v1", publish_at="2026-10-01T12:00:00Z")]})  # 09:00 BR
    r = ye.conferir_lote(cliente, TOKEN, _esperado(["v1"], publicar_em="2026-10-01 09:00"), agora=AGORA)
    assert r["v1"]["status"] == "travado_privado"
    assert ye.TRAVADO in r["v1"]["diagnostico"] and "2026-10-01 09:00" in r["v1"]["diagnostico"]


def test_conferir_agendado_no_futuro_ok(cliente):
    cliente.responder("GET", r"/videos$", {"items": [video("v1", publish_at="2026-10-02T12:00:00Z")]})
    r = ye.conferir_lote(cliente, TOKEN, _esperado(["v1"]), agora=AGORA)
    assert r["v1"]["status"] == "ok" and "2026-10-02 09:00" in r["v1"]["diagnostico"]
    assert r["v1"]["publicar_em"] == "2026-10-02 09:00"
    assert r["v1"]["link"] == "https://www.youtube.com/watch?v=v1"


def test_conferir_publicado_e_privado_como_pedido(cliente):
    cliente.responder("GET", r"/videos$", {"items": [video("v1", privacy="public"), video("v2")]})
    esperado = {"v1": {"status_pedido": "publico", "publicar_em": None},
                "v2": {"status_pedido": "privado", "publicar_em": None}}
    r = ye.conferir_lote(cliente, TOKEN, esperado, agora=AGORA)
    assert r["v1"]["status"] == "ok" and r["v1"]["diagnostico"] == "publicado"
    assert r["v2"]["status"] == "ok" and "privado" in r["v2"]["diagnostico"]


def test_conferir_rejeitado_duplicate_em_portugues(cliente):
    cliente.responder("GET", r"/videos$", {"items": [video("v1", upload="rejected", rejectionReason="duplicate")]})
    r = ye.conferir_lote(cliente, TOKEN, _esperado(["v1"]), agora=AGORA)
    assert r["v1"]["status"] == "rejeitado" and "duplicado" in r["v1"]["diagnostico"]
    assert r["v1"]["uploadStatus"] == "rejected"


def test_conferir_falhou_codec(cliente):
    cliente.responder("GET", r"/videos$", {"items": [video("v1", upload="failed", failureReason="codec")]})
    r = ye.conferir_lote(cliente, TOKEN, _esperado(["v1"]), agora=AGORA)
    assert r["v1"]["status"] == "falhou" and "codec" in r["v1"]["diagnostico"]


def test_conferir_processando(cliente):
    it = video("v1", upload="uploaded")
    it["processingDetails"] = {"processingStatus": "processing",
                               "processingProgress": {"partsTotal": "4", "partsProcessed": "1"}}
    cliente.responder("GET", r"/videos$", {"items": [it]})
    r = ye.conferir_lote(cliente, TOKEN, _esperado(["v1"]), agora=AGORA)
    assert r["v1"]["status"] == "processando" and "25 %" in r["v1"]["diagnostico"]


def test_conferir_nao_encontrado_e_resumo(cliente):
    cliente.responder("GET", r"/videos$", {"items": [video("v1", publish_at="2026-10-02T12:00:00Z"),
                                                      video("v2")]})
    r = ye.conferir_lote(cliente, TOKEN, _esperado(["v1", "v2", "sumiu"]), agora=AGORA)
    assert r["sumiu"]["status"] == "nao_encontrado" and r["sumiu"]["link"].endswith("sumiu")
    assert r["resumo"] == {"total": 3, "nao_encontrado": 1, "ok": 1, "travado_privado": 1, "chamadas": 1}


@pytest.mark.parametrize("motivo,texto", sorted(ye.REJEICOES.items()))
def test_conferir_traduz_todas_as_rejeicoes(motivo, texto):
    d = ye.diagnosticar_video(video("v", upload="rejected", rejectionReason=motivo), {"status_pedido": "publico"}, AGORA)
    assert d["status"] == "rejeitado" and texto in d["diagnostico"]


@pytest.mark.parametrize("motivo,texto", sorted(ye.FALHAS.items()))
def test_conferir_traduz_todas_as_falhas(motivo, texto):
    d = ye.diagnosticar_video(video("v", upload="failed", failureReason=motivo), {"status_pedido": "publico"}, AGORA)
    assert d["status"] == "falhou" and texto in d["diagnostico"]


def test_conferir_lista_oficial_de_motivos_coberta():
    oficiais = {"claim", "copyright", "duplicate", "inappropriate", "legal", "length", "termsOfUse",
                "trademark", "uploaderAccountClosed", "uploaderAccountSuspended"}   # docs/videos 2026-10-01
    assert oficiais <= set(ye.REJEICOES)
    assert {"codec", "conversion", "emptyFile", "invalidFile", "tooSmall", "uploadAborted"} == set(ye.FALHAS)


def test_conferir_erro_de_cota_no_lote_nao_estoura(cliente):
    cliente.responder("GET", r"/videos$", erro_google(403, "quotaExceeded"))
    r = ye.conferir_lote(cliente, TOKEN, _esperado(["v1"]), agora=AGORA)
    assert r["v1"]["status"] == "erro" and "cota diária" in r["v1"]["diagnostico"]
    assert "cota diária" in r["resumo"]["erro"]
    sem_token(r, cliente.texto_de_tudo())


# ================================================================== B4 legenda
@pytest.fixture
def transcricao() -> dict:
    return json.loads(FIXTURE_TRANSCRICAO.read_text(encoding="utf-8"))


GOLDEN_4 = ("1\n00:00:00,740 --> 00:00:03,200\nAproveitando Red Dead Redemption,\n\n"
            "2\n00:00:03,380 --> 00:00:04,280\nanimais com\n")
GOLDEN_2 = ("1\n00:00:00,740 --> 00:00:01,970\nAproveitando Red\n\n"
            "2\n00:00:01,970 --> 00:00:03,200\nDead Redemption,\n\n"
            "3\n00:00:03,380 --> 00:00:04,280\nanimais com\n")
RX_TEMPO = re.compile(r"^(\d\d):(\d\d):(\d\d),(\d{3}) --> (\d\d):(\d\d):(\d\d),(\d{3})$")


def _blocos(srt: str) -> list[tuple[int, int, str]]:
    out = []
    for bloco in [b for b in srt.strip().split("\n\n") if b.strip()]:
        n, tempo, *texto = bloco.split("\n")
        m = RX_TEMPO.match(tempo)
        assert m, tempo
        g = [int(x) for x in m.groups()]
        a = ((g[0] * 60 + g[1]) * 60 + g[2]) * 1000 + g[3]
        b = ((g[4] * 60 + g[5]) * 60 + g[6]) * 1000 + g[7]
        out.append((a, b, "\n".join(texto)))
    return out


def test_srt_golden_com_a_fixture_real_do_pc(transcricao):
    assert ye.transcricao_para_srt(transcricao, 4.0, 9.0) == GOLDEN_4


def test_srt_max_palavras_2(transcricao):
    assert ye.transcricao_para_srt(transcricao, 4.0, 9.0, max_palavras=2) == GOLDEN_2


def test_srt_recorta_na_borda_e_tempos_relativos(transcricao):
    assert ye.transcricao_para_srt(transcricao, 5.8, 6.1) == "1\n00:00:00,000 --> 00:00:00,300\nRed Dead\n"


def test_srt_fora_do_trecho_vazio(transcricao):
    assert ye.transcricao_para_srt(transcricao, 20, 30) == ""
    assert ye.transcricao_para_srt({"segmentos": []}, 0, 10) == ""


def test_srt_sem_sobreposicao_e_sem_bloco_vazio():
    dados = {"segmentos": [
        {"inicio": 1.0, "fim": 3.0, "texto": "a b c",
         "palavras": [{"inicio": 1.0, "fim": 2.0, "texto": "a"}, {"inicio": 1.5, "fim": 1.5, "texto": "b"},
                      {"inicio": 1.6, "fim": 2.5, "texto": " "}, {"inicio": 2.4, "fim": 3.0, "texto": "c"}]},
        {"inicio": 2.9, "fim": 4.0, "texto": "d", "palavras": [{"inicio": 2.9, "fim": 4.0, "texto": "d"}]},
    ]}
    blocos = _blocos(ye.transcricao_para_srt(dados, 1.0, 4.0, max_palavras=1))
    assert [t for _, _, t in blocos] == ["a", "b", "c", "d"]
    fim_ant = 0
    for a, b, texto in blocos:
        assert texto.strip() and b > a and a >= fim_ant
        fim_ant = b


def test_srt_segmento_sem_palavras_vira_bloco_unico():
    dados = {"segmentos": [{"inicio": 2.0, "fim": 3.5, "texto": "  sem   palavras aqui "}]}
    assert ye.transcricao_para_srt(dados, 2.0, 4.0) == "1\n00:00:00,000 --> 00:00:01,500\nsem palavras aqui\n"


def test_srt_formato_com_virgula_e_numeracao(transcricao):
    srt = ye.transcricao_para_srt(transcricao, 4.0, 9.0, max_palavras=1)
    blocos = srt.strip().split("\n\n")
    assert [b.split("\n")[0] for b in blocos] == [str(i) for i in range(1, len(blocos) + 1)]
    assert "." not in "".join(b.split("\n")[1] for b in blocos)   # só vírgula nos tempos
    assert ye._tempo_srt(3661.24) == "01:01:01,240"


def test_enviar_legenda_desligada_por_padrao(cliente):
    r = ye.enviar_legenda(cliente, TOKEN, "v1", GOLDEN_4)
    assert r["status"] == "desligado" and "400 unidades" in r["erro"] and "desligada" in r["erro"]
    assert cliente.chamadas == []


def test_enviar_legenda_ligada_multipart_related(cliente, cont):
    cliente.responder("POST", r"/upload/youtube/v3/captions$", {"id": "CAP1"})
    r = ye.enviar_legenda(cliente, TOKEN, "v1", GOLDEN_4, ligado=True, registrar=cont.registrar)
    ch = cliente.chamadas[0]
    assert (ch.metodo, ch.url) == ("POST", f"{ye.API_UPLOAD}/captions")
    assert ch.consulta == {"part": "snippet", "uploadType": "multipart"}
    assert ch.cabecalhos["Content-Type"].startswith("multipart/related; boundary=")
    assert isinstance(ch.corpo, bytes)
    corpo = ch.corpo.decode("utf-8")
    meta = json.loads(re.search(r"\{.*\}", corpo, re.S).group(0).split("\r\n--")[0])
    assert meta == {"snippet": {"videoId": "v1", "language": "pt-BR", "name": "Português", "isDraft": False}}
    assert GOLDEN_4 in corpo and "Content-Type: application/json" in corpo
    assert r["status"] == "enviado" and r["id"] == "CAP1"
    assert cont.chamadas == ["captions.insert"] and cont.resumo()["total"] == 400
    bearer_ok(cliente)


def test_enviar_legenda_409_ja_existe_nao_e_falha(cliente):
    cliente.responder("POST", r"/captions$", erro_google(409, "captionExists"))
    r = ye.enviar_legenda(cliente, TOKEN, "v1", GOLDEN_4, ligado=True)
    assert r["status"] == "ja_existe" and r["erro"] is None


def test_enviar_legenda_vazia_ou_erro(cliente):
    assert ye.enviar_legenda(cliente, TOKEN, "v1", "   ", ligado=True)["status"] == "invalido"
    assert cliente.chamadas == []
    cliente.responder("POST", r"/captions$", erro_google(403, "forbidden"))
    r = ye.enviar_legenda(cliente, TOKEN, "v1", GOLDEN_4, ligado=True)
    assert r["status"] == "erro" and "permissão" in r["erro"]


# ================================================================== B5 cota
def test_custos_confirmados_com_fonte_e_data():
    assert ye.CUSTOS_CONFIRMADOS_EM == "2026-10-01"
    esperado = {"videos.list": 1, "channels.list": 1, "playlists.list": 1, "playlistItems.list": 1,
                "thumbnails.set": 50, "videos.update": 50, "playlists.insert": 50,
                "playlistItems.insert": 50, "captions.insert": 400}
    for tipo, custo in esperado.items():
        c = ye.CUSTOS[tipo]
        assert c["custo"] == custo, tipo
        assert c["fonte"].startswith("https://developers.google.com/youtube/v3/"), tipo
        assert c["confirmado_em"] == ye.CUSTOS_CONFIRMADOS_EM and c["confirmar"] is False, tipo
    assert ye.CUSTOS["videos.insert"]["balde"] == "envios" and ye.CUSTOS["videos.insert"]["custo"] == 0
    assert ye.LIMITE_DIA == 10000 and ye.LIMITE_ENVIOS_DIA == 100
    assert ye.CUSTO_LEGENDA == 400


def test_registro_de_cota_soma_por_tipo():
    r = ye.registro_de_cota(["videos.list", "videos.list", "videos.update", "playlistItems.insert"])
    assert r["total"] == 102 and r["avisar"] is False
    assert r["por_tipo"]["videos.list"] == {"n": 2, "unidades": 2}
    assert r["por_tipo"]["videos.update"] == {"n": 1, "unidades": 50}
    assert r["restante"] == 9898 and "102 de 10000" in r["mensagem"]


def test_registro_de_cota_avisa_em_80_por_cento():
    assert ye.registro_de_cota(["videos.update"] * 159 + ["videos.list"] * 49)["avisar"] is False   # 7999
    r = ye.registro_de_cota(["videos.update"] * 160)                                               # 8000
    assert r["avisar"] is True and "AVISO" in r["mensagem"] and "80 %" in r["mensagem"]
    r = ye.registro_de_cota(["videos.update"] * 4, limite_dia=250, aviso_em=0.8)                   # 200/250
    assert r["avisar"] is True


def test_registro_de_cota_videos_insert_balde_proprio():
    r = ye.registro_de_cota(["videos.insert"] * 90 + ["videos.list"])
    assert r["total"] == 1 and r["envios"] == 90 and r["por_tipo"]["videos.insert"]["unidades"] == 0
    assert r["avisar"] is True and "90 de 100 envios" in r["mensagem"]
    assert ye.registro_de_cota(["videos.insert"] * 10)["avisar"] is False


def test_registro_de_cota_tipo_desconhecido_conta_1():
    r = ye.registro_de_cota({"videos.list": 3, "x.y": 2})
    assert r["total"] == 5 and r["desconhecidos"] == ["x.y"] and "x.y" in r["mensagem"]
    assert r["confirmar"] == []


def test_contador_integra_varias_funcoes(cliente, cache, cont):
    cliente.responder("GET", r"/playlists$", {"items": []})
    cliente.responder("POST", r"/playlists$", {"id": "PL1"})
    cliente.responder("GET", r"/playlistItems$", {"items": []})
    cliente.responder("POST", r"/playlistItems$", {"id": "PI1"})
    cliente.responder("GET", r"/videos$", {"items": [video("v1", publish_at="2026-10-02T12:00:00Z")]})
    pid = ye.playlist_do_canal(cliente, TOKEN, "gta", TITULO, cache=cache, registrar=cont.registrar)
    ye.adicionar_na_playlist(cliente, TOKEN, pid, "v1", registrar=cont.registrar)
    ye.conferir_lote(cliente, TOKEN, _esperado(["v1"]), agora=AGORA, registrar=cont.registrar)
    assert cont.chamadas == ["playlists.list", "playlists.insert", "playlistItems.list",
                             "playlistItems.insert", "videos.list"]
    assert cont.resumo()["total"] == 103


# ================================================================== erros em português
@pytest.mark.parametrize("x,trecho", [
    (erro_google(403, "quotaExceeded"), "cota diária da API do YouTube esgotada (10.000 unidades); volta à meia-noite da Califórnia"),
    (erro_google(400, "uploadLimitExceeded"), "limite de envios"),
    (erro_google(409, "duplicate"), "duplicado"),
    (erro_google(401, "authError"), "token vencido: o PC renova"),
    (Resposta(401, {"error": {"message": "Invalid Credentials"}}), "token vencido: o PC renova"),
    (erro_google(403, "forbidden"), "sem permissão (403)"),
    (erro_google(403, "insufficientPermissions"), "youtube.force-ssl"),
    (Resposta(403, {"error": {"message": "x", "errors": [{"reason": "algoNovo"}]}}), "permissão negada (403)"),
    (erro_google(404, "videoNotFound"), "vídeo não encontrado"),
    (erro_google(400, "invalidPublishAt"), "horário de publicação inválido"),
    (Resposta(503, "<html>Service Unavailable</html>"), "fora do ar"),
    (ErroRede("HTTP 403 quotaExceeded", status=403), "cota diária"),
    (ErroRede("curl: (6) não resolveu o host"), "falha de rede"),
    (ErroRede("timeout", transitorio=True, status=429), "espere um minuto"),
])
def test_erro_youtube_traduz(x, trecho):
    msg = ye.erro_youtube(x)
    assert trecho in msg, msg
    sem_token(msg)


def test_erro_youtube_nunca_mostra_token():
    msg = ye.erro_youtube(ErroRede(f"HTTP 401 Authorization: Bearer {TOKEN} access_token={TOKEN}", status=401))
    sem_token(msg)
    e = ye.ErroYouTube(f"erro com Bearer {TOKEN}", 401, "authError")
    sem_token(e, repr(e), e.mensagem, e.args)


# ================================================================== token nunca vaza
def test_nenhum_token_em_resultado_excecao_log_nem_arquivo(cliente, cont):
    """Roda tudo (caminho feliz e de erro) e varre str(resultado), str(exceção),
    cliente.texto_de_tudo() e o arquivo de cache."""
    cliente.responder("GET", r"/playlists$", [{"items": []}, ErroRede(f"HTTP 500 Bearer {TOKEN}", status=500)])
    cliente.responder("POST", r"/playlists$", {"id": "PL1"})
    cliente.responder("GET", r"/playlistItems$", {"items": []})
    cliente.responder("POST", r"/playlistItems$", [{"id": "PI1"}, erro_google(403, "quotaExceeded", f"tok {TOKEN}")])
    cliente.responder("GET", r"/videos$", [{"items": [video("v1")]}, {"items": [video("v1")]},
                                          ErroRede(f"HTTP 401 {TOKEN}", status=401)])
    cliente.responder("PUT", r"/videos$", erro_google(401, "authError", f"Bearer {TOKEN}"))
    cliente.responder("POST", r"/captions$", ErroRede(f"403 {TOKEN}", status=403))
    saidas = []
    saidas.append(ye.playlist_do_canal(cliente, TOKEN, "gta", TITULO, registrar=cont.registrar))
    with pytest.raises(ye.ErroYouTube) as exc:
        ye.playlist_do_canal(cliente, TOKEN, "gta", "Outra", registrar=cont.registrar)
    saidas += [exc.value, repr(exc.value), exc.value.args]
    saidas.append(ye.adicionar_na_playlist(cliente, TOKEN, "PL1", "v1", registrar=cont.registrar))
    saidas.append(ye.adicionar_na_playlist(cliente, TOKEN, "PL1", "v2", registrar=cont.registrar))
    saidas.append(ye.atualizar_video(cliente, TOKEN, "v1", titulo="x", registrar=cont.registrar))
    saidas.append(ye.conferir_lote(cliente, TOKEN, _esperado(["v1"]), agora=AGORA, registrar=cont.registrar))
    saidas.append(ye.conferir_lote(cliente, TOKEN, _esperado(["v1"]), agora=AGORA, registrar=cont.registrar))
    saidas.append(ye.enviar_legenda(cliente, TOKEN, "v1", GOLDEN_4, ligado=True, registrar=cont.registrar))
    saidas.append(ye.enviar_legenda(cliente, TOKEN, "v1", GOLDEN_4))
    saidas.append(cont.resumo())
    assert {s["status"] for s in saidas if isinstance(s, dict) and "status" in s} >= {"erro", "adicionado", "desligado"}
    sem_token(*saidas, cliente.texto_de_tudo(), cont.chamadas)
    arq = pasta_app() / "publicar" / "youtube_playlists.json"
    sem_token(arq.read_text(encoding="utf-8"))
    bearer_ok(cliente)


def test_token_so_no_cabecalho_nunca_na_url_nem_na_consulta(cliente):
    cliente.responder("GET", r"/playlists$", {"items": [{"id": "PL1", "snippet": {"title": TITULO}}]})
    cliente.responder("GET", r"/playlistItems$", {"items": [{"id": "PI1"}]})
    cliente.responder("GET", r"/videos$", {"items": [video("v1")]})
    cliente.responder("PUT", r"/videos$", {"id": "v1"})
    ye.playlist_do_canal(cliente, TOKEN, "gta", TITULO, cache=ye.CacheMemoria())
    ye.adicionar_na_playlist(cliente, TOKEN, "PL1", "v1")
    ye.atualizar_video(cliente, TOKEN, "v1", titulo="x")
    assert len(cliente.chamadas) == 4
    bearer_ok(cliente)
    for ch in cliente.chamadas:
        assert "?" not in ch.url, "parâmetros vão em consulta=, não na URL"
    sem_token(cliente.texto_de_tudo())
