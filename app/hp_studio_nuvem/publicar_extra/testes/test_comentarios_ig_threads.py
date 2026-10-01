"""Testes do comentarios_ig_threads (tarefa C3) — ClienteFalso, sem rede.

URL/método/parâmetros/corpo do Instagram (comments, replies, hide) e do Threads (replies, me/threads +
threads_publish com reply_to_id/creation_id, manage_reply); paginação com token fora da URL; o planejar
reaproveitado; executar sem enviar = 0 POST; "curtir" pulado nas duas redes; idempotência; token nunca vaza.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_HP = str(Path(__file__).resolve().parents[2])
if _HP not in sys.path:
    sys.path.insert(0, _HP)
from hpbase.pytest_raizes import raizes_temporarias  # noqa: E402,F401
from publicar_extra.contrato_pc import ClienteFalso, Resposta  # noqa: E402
from publicar_extra import comentarios as co  # noqa: E402
from publicar_extra import comentarios_ig_threads as igth  # noqa: E402
from publicar_extra.facebook_extra import ErroGraph  # noqa: E402

TOKEN = "FAKE_NAO_E_TOKEN_1"
MEDIA = "17900000000000001"


def sem_token(*coisas):
    for c in coisas:
        s = c if isinstance(c, str) else json.dumps(c, ensure_ascii=False, default=str)
        assert "FAKE_NAO_E_TOKEN" not in s, "token vazou"


def erro_meta(code, message):
    return Resposta(400, {"error": {"message": message, "type": "OAuthException", "code": code}})


# ================================================================== Instagram
def test_ig_ler_comentarios_url_campos_paginacao_e_oculto_fora():
    c = ClienteFalso()
    prox = f"{igth.API_IG}/{MEDIA}/comments?after=B&access_token={TOKEN}"
    c.responder("GET", rf"/{MEDIA}/comments$", [
        {"data": [{"id": "c1", "text": "quando sai?", "username": "ana", "timestamp": "2026-10-01T13:00:00+0000",
                   "like_count": 2, "from": {"id": "u1", "username": "ana"}},
                  {"id": "c2", "text": "oculto", "username": "x", "hidden": True}],
         "paging": {"next": prox}},
        {"data": [{"id": "c3", "text": "🔥", "username": "bia"}]},
    ])
    lidos = igth.ig_ler_comentarios(c, TOKEN, MEDIA)
    a, b = c.chamadas
    assert a.metodo == "GET" and a.url == f"{igth.API_IG}/{MEDIA}/comments"
    assert a.consulta == {"fields": igth.CAMPOS_IG, "limit": 50, "access_token": TOKEN}
    assert b.url == f"{igth.API_IG}/{MEDIA}/comments" and b.consulta["after"] == "B" and TOKEN not in b.url
    assert [l["id"] for l in lidos] == ["c1", "c3"]
    assert lidos[0] == {"id": "c1", "texto": "quando sai?", "autor_id": "u1", "autor_nome": "ana",
                        "criado_em": "2026-10-01 10:00", "curtidas": 2, "respostas": None, "post_id": MEDIA,
                        "oculto": None, "bruto": lidos[0]["bruto"]}
    assert lidos[1]["autor_id"] == "bia"                       # sem from: usa o username


def test_ig_responder_ocultar_e_curtir_sem_api():
    c = ClienteFalso()
    c.responder("POST", r"/c1/replies$", {"id": "r1"})
    c.responder("POST", r"/c1$", {"success": True})
    r = igth.ig_responder(c, TOKEN, "c1", "Sai dia 5!")
    o = igth.ig_ocultar(c, TOKEN, "c1")
    a, b = c.chamadas
    assert (a.metodo, a.url, a.form) == ("POST", f"{igth.API_IG}/c1/replies", {"message": "Sai dia 5!", "access_token": TOKEN})
    assert (b.metodo, b.url, b.form) == ("POST", f"{igth.API_IG}/c1", {"hide": "true", "access_token": TOKEN})
    assert r["status"] == "respondido" and r["id"] == "r1" and r["rede"] == "instagram"
    assert o["status"] == "ocultado"
    assert igth.ig_curtir(c, TOKEN, "c1")["status"] == "erro" and len(c.chamadas) == 2
    assert igth.ig_responder(c, TOKEN, "c1", "")["status"] == "erro" and len(c.chamadas) == 2


def test_ig_erro_de_permissao_diz_qual():
    c = ClienteFalso().responder("GET", r"/comments$", erro_meta(10, "(#10) requires instagram_business_manage_comments"))
    with pytest.raises(ErroGraph) as ex:
        igth.ig_ler_comentarios(c, TOKEN, MEDIA)
    assert ex.value.permissao == "instagram_business_manage_comments"
    assert igth.PERMISSOES_IG["login_instagram"] == ("instagram_business_basic", "instagram_business_manage_comments")


def test_ig_executar_reaproveita_classificacao_sem_enviar_e_com_enviar(tmp_path):
    lidos = [{"id": "c1", "texto": "quando sai no pc?", "autor_id": "u1", "post_id": MEDIA},
             {"id": "c2", "texto": "top demais", "autor_id": "u2", "post_id": MEDIA},
             {"id": "c3", "texto": "vai se foder", "autor_id": "u3", "post_id": MEDIA}]
    acoes = co.planejar(lidos, set(), co.ConfigComentarios(), {MEDIA}, redator=lambda c: "Dia 5!")
    assert [a["acao"] for a in acoes] == ["responder", "curtir", "ignorar"]
    c = ClienteFalso()
    r = igth.ig_executar(c, TOKEN, acoes, co.ConfigComentarios(), co.EstadoComentarios())
    assert c.chamadas == [] and r["simulado"] is True and r["rede"] == "instagram"
    c.responder("POST", r"/c1/replies$", {"id": "r1"})
    est = co.EstadoComentarios(tmp_path / "ig_estado.json")
    r2 = igth.ig_executar(c, TOKEN, acoes, co.ConfigComentarios(), est, enviar=True, dormir=lambda s: None)
    assert [ch.url for ch in c.chamadas] == [f"{igth.API_IG}/c1/replies"]
    assert r2["respondidas"] == 1 and r2["curtidas"] == 0
    assert any("não tem a ação curtir" in x.get("porque", "") for x in r2["resultados"])
    c2 = ClienteFalso()
    r3 = igth.ig_executar(c2, TOKEN, acoes, co.ConfigComentarios(), co.EstadoComentarios(tmp_path / "ig_estado.json"),
                          enviar=True, dormir=lambda s: None)
    assert c2.chamadas == [] and r3["respondidas"] == 0


# ================================================================== Threads
def test_th_ler_respostas_url_campos_e_oculto_fora():
    c = ClienteFalso().responder("GET", rf"/{MEDIA}/replies$", {"data": [
        {"id": "t1", "text": "qual a fonte?", "username": "carlos", "timestamp": "2026-10-01T13:00:00+0000",
         "hide_status": "NOT_HUSHED", "is_reply": True, "root_post": {"id": MEDIA}},
        {"id": "t2", "text": "spam", "username": "bot", "hide_status": "HIDDEN"}]})
    lidos = igth.th_ler_respostas(c, TOKEN, MEDIA)
    ch = c.ultima
    assert ch.metodo == "GET" and ch.url == f"{igth.API_TH}/{MEDIA}/replies"
    assert ch.consulta == {"fields": igth.CAMPOS_TH, "reverse": "false", "limit": 50, "access_token": TOKEN}
    assert [l["id"] for l in lidos] == ["t1"]
    assert lidos[0]["autor_id"] == "carlos" and lidos[0]["criado_em"] == "2026-10-01 10:00"


def test_th_responder_dois_passos_reply_to_id_e_creation_id():
    c = ClienteFalso()
    c.responder("POST", r"/me/threads$", {"id": "CONT1"})
    c.responder("POST", r"/me/threads_publish$", {"id": "PUB1"})
    esperas = []
    r = igth.th_responder(c, TOKEN, "t1", "A fonte é a Rockstar.", espera_s=5, dormir=esperas.append)
    a, b = c.chamadas
    assert (a.metodo, a.url) == ("POST", f"{igth.API_TH}/me/threads")
    assert a.form == {"media_type": "TEXT", "text": "A fonte é a Rockstar.", "reply_to_id": "t1", "access_token": TOKEN}
    assert (b.metodo, b.url, b.form) == ("POST", f"{igth.API_TH}/me/threads_publish", {"creation_id": "CONT1", "access_token": TOKEN})
    assert esperas == [5]
    assert r["status"] == "respondido" and r["id"] == "PUB1" and r["creation_id"] == "CONT1" and r["rede"] == "threads"
    c2 = ClienteFalso().responder("POST", r"/me/threads$", {"id": "CONT1"}).responder(
        "POST", r"/me/threads_publish$", erro_meta(368, "abusive"))
    r2 = igth.th_responder(c2, TOKEN, "t1", "x")
    assert r2["status"] == "erro" and r2["categoria"] == "bloqueio"


def test_th_ocultar_manage_reply_e_executar():
    c = ClienteFalso()
    c.responder("POST", r"/t1/manage_reply$", {"success": True})
    o = igth.th_ocultar(c, TOKEN, "t1")
    assert c.ultima.url == f"{igth.API_TH}/t1/manage_reply" and c.ultima.form == {"hide": "true", "access_token": TOKEN}
    assert o["status"] == "ocultado"
    acoes = [{"acao": "responder", "comentario_id": "t1", "autor_id": "carlos", "texto_resposta": "oi", "motivo": "pergunta"},
             {"acao": "curtir", "comentario_id": "t2", "autor_id": "bia", "motivo": "elogio"}]
    c.responder("POST", r"/me/threads$", {"id": "C"})
    c.responder("POST", r"/me/threads_publish$", {"id": "P"})
    est = co.EstadoComentarios()
    r = igth.th_executar(c, TOKEN, acoes, co.ConfigComentarios(), est, enviar=True, dormir=lambda s: None)
    assert r["respondidas"] == 1 and r["curtidas"] == 0 and r["rede"] == "threads" and est.tratado("t1")
    assert [ch.url.split("/")[-1] for ch in c.chamadas_de("POST")] == ["manage_reply", "threads", "threads_publish"]
    assert igth.PERMISSOES_TH == ("threads_read_replies", "threads_manage_replies")


def test_token_nunca_aparece_nas_duas_redes():
    c = ClienteFalso()
    c.responder("GET", r"/comments$", erro_meta(190, f"expired {TOKEN}"))
    c.responder("GET", r"/replies$", {"data": [{"id": "t1", "text": "oi", "username": "a"}],
                                       "paging": {"next": f"{igth.API_TH}/{MEDIA}/replies?after=Z&access_token={TOKEN}"}}, vezes=1)
    c.responder("GET", r"/replies$", {"data": []})
    c.responder("POST", r"/replies$", erro_meta(4, f"limit {TOKEN}"))
    with pytest.raises(ErroGraph) as ex:
        igth.ig_ler_comentarios(c, TOKEN, MEDIA)
    lidos = igth.th_ler_respostas(c, TOKEN, MEDIA)
    r = igth.ig_responder(c, TOKEN, "c1", "oi")
    for ch in c.chamadas:
        assert TOKEN not in ch.url
    sem_token(str(ex.value), c.texto_de_tudo(), lidos, r, [ch.url for ch in c.chamadas])
