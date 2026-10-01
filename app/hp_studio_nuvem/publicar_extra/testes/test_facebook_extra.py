"""Testes do facebook_extra (tarefa C1 da rodada 2) — tudo com ClienteFalso, sem rede, sem relógio.

URL, método, parâmetros e corpo de cada chamada; paginação (token tirado do paging.next);
reels agendados como tentativa marcada "confirmar"; janelas de reagendar (9 min, 76 dias, reel 30 dias);
erro_graph com os códigos de reel, token, permissão (diz qual), limite, parâmetro, bloqueio e genérico;
comparar_com_agendados_json com a fixture real (buraco, duplicado, hora errada, ok, sobras, formato antigo);
e a prova de que FAKE_NAO_E_TOKEN_1 nunca aparece em URL, log do cliente, resultado nem exceção.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

_HP = str(Path(__file__).resolve().parents[2])  # ...\app\hp_studio_nuvem
if _HP not in sys.path:
    sys.path.insert(0, _HP)
from hpbase.pytest_raizes import raizes_temporarias  # noqa: E402,F401  (autouse: H:/G: → pastas temporárias)
from hpbase import FUSO  # noqa: E402
from publicar_extra.contrato_pc import ClienteFalso, ErroRede, Resposta  # noqa: E402
from publicar_extra import facebook_extra as fb  # noqa: E402

TOKEN = "FAKE_NAO_E_TOKEN_1"
API = fb.API
PAGE = "1000123"
RAIZ = Path(__file__).resolve().parents[4]
FIXTURE_AGENDADOS = RAIZ / "tests" / "fixtures" / "pc_real" / "agendados_exemplo.json"
AGORA = datetime(2026, 10, 1, 10, 0, tzinfo=FUSO)   # 01/10/2026 10:00 Brasília = 13:00Z


# ------------------------------------------------------------------ apoio
def erro_meta(code, message="erro", subcode=None, status=400, tipo="OAuthException"):
    err = {"message": message, "type": tipo, "code": code, "fbtrace_id": "AbC123"}
    if subcode is not None:
        err["error_subcode"] = subcode
    return Resposta(status, {"error": err})


def sem_token(*coisas) -> None:
    for c in coisas:
        s = c if isinstance(c, str) else json.dumps(c, ensure_ascii=False, default=str)
        assert TOKEN not in s, "token vazou"
        assert "FAKE_NAO_E_TOKEN" not in s, "token vazou"


def post_agendado(pid, epoch, msg, link=None, media=None):
    d = {"id": f"{PAGE}_{pid}", "message": msg, "scheduled_publish_time": epoch,
         "created_time": "2026-09-30T12:00:00+0000", "is_published": False,
         "permalink_url": link or f"https://www.facebook.com/{PAGE}/posts/{pid}"}
    if media:
        d["attachments"] = {"data": [{"media_type": media, "url": "https://www.facebook.com/x"}]}
    return d


def epoch(ano, mes, dia, h, m):   # hora de Brasília -> epoch UTC
    return int(datetime(ano, mes, dia, h, m, tzinfo=FUSO).timestamp())


# ================================================================== listar_agendados
def test_listar_agendados_url_metodo_parametros_e_token_fora_da_url():
    c = ClienteFalso()
    c.responder("GET", rf"/{PAGE}/scheduled_posts$", {"data": [post_agendado("1", epoch(2026, 10, 2, 18, 30), "Oi")]})
    c.responder("GET", rf"/{PAGE}/video_reels$", {"data": []})
    itens = fb.listar_agendados(c, TOKEN, PAGE)
    ch = c.chamadas[0]
    assert ch.metodo == "GET" and ch.url == f"{API}/{PAGE}/scheduled_posts"
    assert ch.consulta["fields"] == fb.CAMPOS_AGENDADOS
    assert ch.consulta["limit"] == 100 and ch.consulta["access_token"] == TOKEN
    assert "access_token" not in ch.url and TOKEN not in ch.url
    assert ch.form is None
    assert itens[0]["id"] == f"{PAGE}_1" and itens[0]["tipo"] == "post"
    assert itens[0]["quando"] == "2026-10-02 18:30" and itens[0]["texto"] == "Oi"
    assert itens[0]["link"] == f"https://www.facebook.com/{PAGE}/posts/1"
    assert itens[0]["bruto"]["is_published"] is False


def test_listar_agendados_paginacao_tira_o_token_do_paging_next():
    c = ClienteFalso()
    prox = (f"{API}/{PAGE}/scheduled_posts?fields=id%2Cmessage&limit=100&access_token={TOKEN}"
            f"&after=CURSOR_B")
    c.responder("GET", rf"/{PAGE}/scheduled_posts$", [
        {"data": [post_agendado("1", epoch(2026, 10, 3, 9, 0), "A")], "paging": {"next": prox}},
        {"data": [post_agendado("2", epoch(2026, 10, 2, 9, 0), "B")]},
    ])
    c.responder("GET", rf"/{PAGE}/video_reels$", {"data": []})
    itens = fb.listar_agendados(c, TOKEN, PAGE)
    pags = c.chamadas_de("GET", "scheduled_posts")
    assert len(pags) == 2
    assert pags[1].url == f"{API}/{PAGE}/scheduled_posts"            # URL limpa, sem query
    assert pags[1].consulta["after"] == "CURSOR_B" and pags[1].consulta["access_token"] == TOKEN
    assert TOKEN not in pags[1].url
    assert [i["texto"] for i in itens] == ["B", "A"]                 # ordenado pela hora
    sem_token(c.texto_de_tudo(), [c.url for c in c.chamadas])


def test_listar_agendados_normaliza_hora_iso_link_relativo_e_reel_por_permalink():
    c = ClienteFalso()
    bruto = post_agendado("7", "2026-10-02T21:30:00+0000", "Reel", link=f"/reel/{PAGE}7")
    c.responder("GET", r"/scheduled_posts$", {"data": [bruto]})
    c.responder("GET", r"/video_reels$", {"data": []})
    it = fb.listar_agendados(c, TOKEN, PAGE)[0]
    assert it["quando"] == "2026-10-02 18:30"                         # 21:30Z = 18:30 Brasília
    assert it["link"] == f"https://www.facebook.com/reel/{PAGE}7"
    assert it["tipo"] == "reel"


def test_listar_agendados_tenta_reels_marcados_confirmar_e_nao_duplica():
    c = ClienteFalso()
    c.responder("GET", r"/scheduled_posts$", {"data": [post_agendado("5", epoch(2026, 10, 5, 12, 0), "Post")]})
    c.responder("GET", r"/video_reels$", {"data": [
        {"id": "900", "title": "Reel 1", "description": "desc", "scheduled_publish_time": epoch(2026, 10, 4, 20, 0),
         "video_status": {"video_status": "ready"}},
        {"id": "901", "description": "publicado", "updated_time": 1},           # sem agenda: fora
        {"id": "5", "description": "mesmo id do post", "scheduled_publish_time": epoch(2026, 10, 5, 12, 0)},
    ]})
    itens = fb.listar_agendados(c, TOKEN, PAGE)
    reels = c.chamadas_de("GET", "video_reels")
    assert reels[0].consulta["fields"] == fb.CAMPOS_REELS_AGENDADOS and reels[0].consulta["access_token"] == TOKEN
    assert [i["id"] for i in itens] == ["900", f"{PAGE}_5"]
    r = itens[0]
    assert r["tipo"] == "reel" and r["confirmar"] is True and r["quando"] == "2026-10-04 20:00"
    assert r["texto"] == "desc"
    assert "confirmar" not in itens[1]
    assert fb.REELS_AGENDADOS_CONFIRMADO is False


def test_listar_agendados_reels_falhando_vira_aviso_e_pode_desligar():
    c = ClienteFalso()
    c.responder("GET", r"/scheduled_posts$", {"data": [post_agendado("1", epoch(2026, 10, 2, 18, 30), "A")]})
    c.responder("GET", r"/video_reels$", erro_meta(100, "(#100) Tried accessing nonexisting field (video_reels)"))
    avisos = []
    itens = fb.listar_agendados(c, TOKEN, PAGE, avisos=avisos)
    assert len(itens) == 1 and len(avisos) == 1 and "reels" in avisos[0]
    sem_token(avisos)
    c2 = ClienteFalso().responder("GET", r"/scheduled_posts$", {"data": []})
    assert fb.listar_agendados(c2, TOKEN, PAGE, incluir_reels=False) == []
    assert not c2.chamadas_de("GET", "video_reels")


def test_listar_agendados_erro_principal_levanta_erro_graph_em_portugues():
    c = ClienteFalso().responder("GET", r"/scheduled_posts$",
                                 erro_meta(190, f"Error validating access token {TOKEN}", subcode=463))
    with pytest.raises(fb.ErroGraph) as ex:
        fb.listar_agendados(c, TOKEN, PAGE)
    assert ex.value.categoria == "token" and ex.value.codigo == 190 and ex.value.subcodigo == 463
    assert "vencido" in str(ex.value) and "facebook-token" in str(ex.value)
    sem_token(str(ex.value), ex.value.detalhe, c.texto_de_tudo())


def test_listar_agendados_erro_de_rede():
    c = ClienteFalso().responder("GET", r"/scheduled_posts$", ErroRede("curl: (28) timeout", transitorio=True))
    with pytest.raises(fb.ErroGraph) as ex:
        fb.listar_agendados(c, TOKEN, PAGE)
    assert ex.value.categoria == "rede" and ex.value.transitorio is True
    assert "Falha de rede" in str(ex.value)


# ================================================================== cancelar / reagendar
def test_cancelar_agendado_delete_com_token_na_consulta():
    c = ClienteFalso().responder("DELETE", rf"/{PAGE}_9$", {"success": True})
    r = fb.cancelar_agendado(c, TOKEN, f"{PAGE}_9")
    ch = c.ultima
    assert ch.metodo == "DELETE" and ch.url == f"{API}/{PAGE}_9"
    assert ch.consulta == {"access_token": TOKEN} and ch.form is None
    assert r["status"] == "cancelado" and r["id"] == f"{PAGE}_9" and r["erro"] is None


def test_cancelar_agendado_erro_permissao_diz_qual_falta():
    c = ClienteFalso().responder("DELETE", r"/x$", erro_meta(200, "(#200) Requires pages_manage_posts permission"))
    r = fb.cancelar_agendado(c, TOKEN, "x")
    assert r["status"] == "erro" and r["categoria"] == "permissao" and r["permissao"] == "pages_manage_posts"
    assert "pages_manage_posts" in r["erro"] and "HP Publicador" in r["erro"]


def test_reagendar_post_form_epoch_utc_is_published_false_token_no_form():
    c = ClienteFalso().responder("POST", rf"/{PAGE}_9$", {"success": True})
    r = fb.reagendar(c, TOKEN, f"{PAGE}_9", "2026-10-02 18:30", agora=AGORA)
    ch = c.ultima
    assert ch.metodo == "POST" and ch.url == f"{API}/{PAGE}_9"
    esperado = int(datetime(2026, 10, 2, 21, 30, tzinfo=timezone.utc).timestamp())   # 18:30 BRT = 21:30Z
    assert ch.form == {"scheduled_publish_time": esperado, "is_published": "false", "access_token": TOKEN}
    assert ch.consulta is None and TOKEN not in ch.url
    assert r["status"] == "agendado" and r["quando"] == "2026-10-02 18:30" and r["epoch"] == esperado


@pytest.mark.parametrize("nova, tipo, ok, trecho", [
    (AGORA + timedelta(minutes=9), "post", False, "10 minutos e 75 dias"),
    (AGORA + timedelta(minutes=10), "post", True, ""),
    (AGORA - timedelta(minutes=5), "post", False, "já passou"),
    (AGORA + timedelta(days=75), "post", True, ""),
    (AGORA + timedelta(days=76), "post", False, "76 dias"),
    (AGORA + timedelta(days=29), "reel", True, ""),
    (AGORA + timedelta(days=30), "reel", False, "10 minutos e 29 dias"),
    (AGORA + timedelta(minutes=9), "reel", False, "reel"),
])
def test_reagendar_janela_da_meta(nova, tipo, ok, trecho):
    c = ClienteFalso().responder("POST", r"/p1$", {"success": True})
    r = fb.reagendar(c, TOKEN, "p1", nova, agora=AGORA, tipo=tipo)
    if ok:
        assert r["status"] == "agendado" and len(c.chamadas) == 1
    else:
        assert r["status"] == "erro" and r["categoria"] == "janela" and not c.chamadas
        assert trecho in r["erro"] and "Meta" in r["erro"]


def test_reagendar_hora_invalida_e_erro_da_api():
    c = ClienteFalso().responder("POST", r"/p1$", erro_meta(100, "(#100) Invalid parameter"))
    r = fb.reagendar(c, TOKEN, "p1", "amanhã de tarde", agora=AGORA)
    assert r["status"] == "erro" and "Hora inválida" in r["erro"] and not c.chamadas
    r2 = fb.reagendar(c, TOKEN, "p1", "2026-10-02T18:30", agora=AGORA)
    assert r2["status"] == "erro" and r2["codigo"] == 100 and "Parâmetro inválido" in r2["erro"]


# ================================================================== erro_graph
@pytest.mark.parametrize("resp, categoria, trecho", [
    (erro_meta(1363040, "aspect ratio"), "reel", "proporção"),
    (erro_meta(1363127, "resolution"), "reel", "resolução"),
    (erro_meta(1363128, "duration"), "reel", "duração"),
    (erro_meta(1363129, "frame rate"), "reel", "fps"),
    (erro_meta(1, "video", subcode=1363128), "reel", "3 e 90 segundos"),
    (erro_meta(190, "Invalid OAuth 2.0 Access Token"), "token", "vencido"),
    (erro_meta(102, "Session key invalid"), "token", "vencido"),
    (erro_meta(10, "(#10) This endpoint requires pages_read_engagement"), "permissao", "pages_read_engagement"),
    (erro_meta(200, "(#200) Requires pages_manage_engagement permission"), "permissao", "pages_manage_engagement"),
    (erro_meta(283, "requires the extended permission pages_read_engagement and/or pages_read_user_content"),
     "permissao", "pages_read_engagement e/ou pages_read_user_content"),
    (erro_meta(4, "Application request limit reached"), "limite", "Limite de chamadas"),
    (erro_meta(17, "User request limit reached"), "limite", "Espere"),
    (erro_meta(32, "Page request limit reached"), "limite", "Limite"),
    (erro_meta(613, "Calls to this api have exceeded the rate limit"), "limite", "Limite"),
    (erro_meta(80001, "too many calls to this Page"), "limite", "Limite"),
    (erro_meta(100, "(#100) Invalid parameter: fields"), "parametro", "Parâmetro inválido"),
    (erro_meta(100, "Unsupported post request. Object with ID 'x' does not exist", subcode=33), "nao_existe", "não existe"),
    (erro_meta(368, "The action attempted has been deemed abusive"), "bloqueio", "bloqueou"),
    (erro_meta(2, "Service temporarily unavailable"), "passageiro", "passageiro"),
    (erro_meta(9999, "Something odd", tipo="GraphMethodException"), "generico", "9999"),
    (Resposta(500, "<html>bad gateway</html>"), "http", "HTTP 500"),
    (ErroRede("curl: (6) Could not resolve host", transitorio=True), "rede", "Falha de rede"),
])
def test_erro_graph_vira_portugues(resp, categoria, trecho):
    d = fb.detalhar_erro_graph(resp)
    assert d["categoria"] == categoria, d
    assert trecho in d["mensagem"], d["mensagem"]
    assert fb.erro_graph(resp) == d["mensagem"]
    if categoria in ("limite", "passageiro", "rede"):
        assert d["transitorio"] is True


def test_erro_graph_permissao_sem_nome_usa_a_da_acao_e_fbtrace():
    d = fb.detalhar_erro_graph(erro_meta(200, "Permissions error"), acao="responder")
    assert d["permissao"] == "pages_manage_engagement" and "não disse qual" in d["mensagem"]
    assert "fbtrace AbC123" in d["mensagem"]
    d2 = fb.detalhar_erro_graph(erro_meta(200, "Permissions error"))
    assert d2["permissao"] is None and "Permissão negada" in d2["mensagem"]


def test_erro_graph_aceita_dict_e_nunca_vaza_token():
    d = fb.detalhar_erro_graph({"error": {"message": f"token {TOKEN} inválido access_token={TOKEN}",
                                          "code": 190, "type": "OAuthException"}})
    assert d["categoria"] == "token"
    sem_token(d["mensagem"], d["mensagem_meta"], d)
    assert fb.erro_graph(Resposta(400, {"error": {"message": f"Bearer {TOKEN}", "code": 1}}))


def test_erro_graph_classe_erro_graph_e_entrada_de_erro():
    e = fb.ErroGraph(fb.detalhar_erro_graph(erro_meta(613, "rate")))
    r = fb._entrada_erro(e, id="x")
    assert r == {"status": "erro", "link": None, "id": "x", "erro": e.mensagem, "codigo": 613,
                 "categoria": "limite", "permissao": None, "transitorio": True}


# ================================================================== horas
@pytest.mark.parametrize("valor, esperado", [
    (epoch(2026, 10, 2, 18, 30), "2026-10-02 18:30"),
    (str(epoch(2026, 10, 2, 18, 30)), "2026-10-02 18:30"),
    ("2026-10-02T21:30:00+0000", "2026-10-02 18:30"),
    ("2026-10-02T21:30:00Z", "2026-10-02 18:30"),
    ("2026-10-02T18:30:00-03:00", "2026-10-02 18:30"),
    ("2026-10-02 18:30", "2026-10-02 18:30"),
    ("2026-10-02T18:30", "2026-10-02 18:30"),
    (datetime(2026, 10, 2, 18, 30), "2026-10-02 18:30"),
    (None, None), ("", None), ("ontem", None),
])
def test_ler_hora_e_hora_brasilia(valor, esperado):
    assert fb.hora_brasilia(valor) == esperado


# ================================================================== comparar_com_agendados_json
def _api(pid, quando, texto, tipo="post"):
    return {"id": f"{PAGE}_{pid}", "tipo": tipo, "quando": quando, "texto": texto,
            "link": f"https://www.facebook.com/{PAGE}/posts/{pid}", "bruto": {}}


def _json_facebook():
    """A fixture real, com os 2 itens marcados também para o Facebook (+1 só do Facebook)."""
    dados = json.loads(FIXTURE_AGENDADOS.read_text(encoding="utf-8"))
    itens = dados["itens"]
    itens[0]["redes"] = ["instagram", "facebook"]
    itens[0]["links"]["facebook"] = f"https://www.facebook.com/{PAGE}/posts/777"
    itens[1]["redes"] = ["instagram", "facebook"]                 # sem link do FB: casa pelo texto
    itens.append({"id": "futebol_2026-10-02_1800_sem-par", "titulo": "Fla x Flu: escalação confirmada",
                  "data_post": "2026-10-02T18:00", "redes": ["facebook"], "links": {}, "status": "agendado"})
    return dados


def test_comparar_fixture_real_sem_facebook_tudo_ignorado():
    dados = json.loads(FIXTURE_AGENDADOS.read_text(encoding="utf-8"))
    rel = fb.comparar_com_agendados_json([], dados)
    assert len(rel["ignorados"]) == 2 and rel["buracos"] == [] and rel["ok"] == []
    assert "2 ignorado(s)" in rel["resumo"]


def test_comparar_ok_por_id_do_link_e_por_texto_hora_errada_buraco_duplicado_sobra():
    api = [
        _api("777", "2026-09-30 23:18", "Jorge Jesus: \"Quem decide sou eu\" (treta com CR7) #futebol"),
        _api("778", "2026-09-29 17:10", "gta_2026-09-29_ig_story_1700"),            # 12 min de diferença
        _api("779", "2026-10-03 12:00", "Notícia solta que não está no JSON"),
        _api("780", "2026-10-03 12:02", "Notícia solta que não está no JSON "),     # duplicado (2 min)
    ]
    rel = fb.comparar_com_agendados_json(api, _json_facebook(), tolerancia_min=5)
    assert [o["id_api"] for o in rel["ok"]] == [f"{PAGE}_777"]
    assert rel["ok"][0]["id_json"] == "futebol_2026-09-30_2320_jj-quem-decide_ig_feed"
    assert rel["ok"][0]["diferenca_min"] == 0
    assert len(rel["hora_errada"]) == 1
    he = rel["hora_errada"][0]
    assert he["id_api"] == f"{PAGE}_778" and he["diferenca_min"] == 12 and "16:58" in he["motivo"]
    assert [b["id_json"] for b in rel["buracos"]] == ["futebol_2026-10-02_1800_sem-par"]
    assert len(rel["duplicados"]) == 1 and rel["duplicados"][0]["ids"] == [f"{PAGE}_779", f"{PAGE}_780"]
    assert sorted(s["id_api"] for s in rel["sobras"]) == [f"{PAGE}_779", f"{PAGE}_780"]
    assert rel["resumo"].startswith("1 ok, 1 buraco(s), 1 duplicado(s), 1 hora(s) errada(s), 2 sobra(s)")


def test_comparar_tolerancia_e_status_cancelado():
    api = [_api("778", "2026-09-29 17:10", "gta_2026-09-29_ig_story_1700")]
    dados = _json_facebook()
    rel = fb.comparar_com_agendados_json(api, dados, tolerancia_min=15)
    assert len(rel["ok"]) == 1 and rel["hora_errada"] == []
    dados["itens"][1]["status"] = "cancelado"
    rel2 = fb.comparar_com_agendados_json(api, dados, tolerancia_min=15)
    assert rel2["ok"] == [] and len(rel2["sobras"]) == 1 and any("cancelado" in i["motivo"] for i in rel2["ignorados"])


@pytest.mark.parametrize("formato", ["lista", "posts", "agendados", "itens"])
def test_comparar_aceita_formatos_antigos(formato, tmp_path):
    item = {"id": "x1", "titulo": "Post antigo do formato velho", "horario": "2026-10-02T18:30:00-03:00",
            "links": {"facebook": f"https://www.facebook.com/{PAGE}/posts/5"}}
    dados = [item] if formato == "lista" else {formato: [item]}
    api = [_api("5", "2026-10-02 18:30", "Post antigo do formato velho")]
    rel = fb.comparar_com_agendados_json(api, dados)
    assert len(rel["ok"]) == 1 and rel["ok"][0]["id_json"] == "x1"
    arq = tmp_path / "agendados.json"
    arq.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    assert len(fb.comparar_com_agendados_json(api, arq)["ok"]) == 1       # Path também


def test_chave_texto_e_id_do_link():
    assert fb.chave_texto("  Jorge Jesus: \"Quem DECIDE sou eu\" (treta) 🔥") == "jorge jesus quem decide sou eu treta"
    assert fb._id_do_link("https://www.facebook.com/hpgta6/posts/123456789") == "123456789"
    assert fb._id_do_link("https://www.facebook.com/reel/987654321/") == "987654321"
    assert fb._id_do_link("https://www.facebook.com/watch/?v=555555555") == "555555555"
    assert fb._id_do_link(None) is None


# ================================================================== token nunca vaza
def test_token_nunca_aparece_em_url_log_resultado_ou_excecao():
    c = ClienteFalso()
    c.responder("GET", r"/scheduled_posts$", {"data": [post_agendado("1", epoch(2026, 10, 2, 18, 30), "A")],
                                               "paging": {"next": f"{API}/x/scheduled_posts?access_token={TOKEN}&after=Z"}})
    c.responder("GET", r"/video_reels$", erro_meta(200, f"perm {TOKEN}"))
    c.responder("DELETE", r"/d$", erro_meta(190, f"bad {TOKEN}"))
    c.responder("POST", r"/p$", {"success": True})
    avisos = []
    itens = fb.listar_agendados(c, TOKEN, PAGE, avisos=avisos)
    r1 = fb.cancelar_agendado(c, TOKEN, "d")
    r2 = fb.reagendar(c, TOKEN, "p", AGORA + timedelta(hours=2), agora=AGORA)
    for ch in c.chamadas:
        assert TOKEN not in ch.url
    sem_token(c.texto_de_tudo(), itens, avisos, r1, r2, [ch.url for ch in c.chamadas])
