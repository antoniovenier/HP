"""Testes do comentarios (tarefa C2 da rodada 2) — ClienteFalso, sem rede, sem relógio, sem IA.

Banco de 114 comentários inventados (comentarios_banco.json) parametrizado: a falha nomeia o comentário;
ZERO "responder" em ofensivo e nenhum "responder" em emoji puro; caixa alta e gíria não mudam a classe;
URL/método/parâmetros/corpo de ler/curtir/responder/ocultar; paginação; `desde`; planejar (1 por pessoa,
máximo por passada, só post nosso, já tratados, redator); executar sem enviar = 0 POST; enviar=True
idempotente (segunda passada = 0 POST) com estado em JSON atômico; intervalo via dormir injetado;
para em token vencido; e o token FAKE_NAO_E_TOKEN_1 nunca aparece em URL, log, resultado nem arquivo.
"""
from __future__ import annotations

import dataclasses
import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

_HP = str(Path(__file__).resolve().parents[2])  # ...\app\hp_studio_nuvem
if _HP not in sys.path:
    sys.path.insert(0, _HP)
from hpbase.pytest_raizes import raizes_temporarias  # noqa: E402,F401  (autouse: H:/G: → pastas temporárias)
from hpbase import FUSO  # noqa: E402
from publicar_extra.contrato_pc import ClienteFalso, Resposta  # noqa: E402
from publicar_extra import comentarios as co  # noqa: E402
from publicar_extra.facebook_extra import API, ErroGraph  # noqa: E402

TOKEN = "FAKE_NAO_E_TOKEN_1"
POST = "1000123_555"
AGORA = datetime(2026, 10, 1, 10, 0, tzinfo=FUSO)
BANCO = json.loads((Path(__file__).with_name("comentarios_banco.json")).read_text(encoding="utf-8"))["itens"]


# ------------------------------------------------------------------ apoio
def erro_meta(code, message="erro", subcode=None, status=400):
    err = {"message": message, "type": "OAuthException", "code": code, "fbtrace_id": "T1"}
    if subcode is not None:
        err["error_subcode"] = subcode
    return Resposta(status, {"error": err})


def sem_token(*coisas) -> None:
    for c in coisas:
        s = c if isinstance(c, str) else json.dumps(c, ensure_ascii=False, default=str)
        assert TOKEN not in s, "token vazou"
        assert "FAKE_NAO_E_TOKEN" not in s, "token vazou"


def bruto(cid, msg, autor="u1", nome="Ana", quando="2026-10-01T12:00:00+0000"):
    return {"id": cid, "message": msg, "from": {"id": autor, "name": nome}, "created_time": quando,
            "like_count": 0, "comment_count": 0}


def com(cid, texto, autor="u1", post=POST):
    return {"id": cid, "texto": texto, "autor_id": autor, "autor_nome": "Ana", "criado_em": "2026-10-01 09:00",
            "curtidas": 0, "respostas": 0, "post_id": post, "bruto": {}}


# ================================================================== classificar (banco)
@pytest.mark.parametrize("item", BANCO, ids=[f"{i['grupo']}:{i['texto'][:28]}" for i in BANCO])
def test_banco_de_comentarios(item):
    d = co.classificar_detalhado(item["texto"])
    assert d["classe"] == item["classe"], (f"comentário {item['texto']!r} ({item['grupo']}): esperado "
                                           f"{item['classe']}, saiu {d['classe']} — motivo: {d['motivo']}")


def test_banco_tem_pelo_menos_60_e_todos_os_grupos():
    assert len(BANCO) >= 60
    grupos = {i["grupo"].split("_")[0] for i in BANCO}
    for g in ("elogio", "emoji", "pergunta", "critica", "ofensa", "spam", "giria", "caixa", "marcacao", "sarcasmo"):
        assert g in grupos, g


def test_zero_falso_responder_em_ofensivo_e_nenhum_em_emoji_puro():
    for it in BANCO:
        classe = co.classificar_comentario(it["texto"])
        if it["grupo"].startswith("ofensa"):
            assert classe == "ignorar", f"ofensivo não ignorado: {it['texto']!r} -> {classe}"
        if it["grupo"] == "emoji":
            assert classe != "responder", f"responder em emoji puro: {it['texto']!r}"
            assert classe == "curtir"


@pytest.mark.parametrize("a, b", [
    ("top demais", "TOP DEMAIS"), ("quando sai o trailer?", "QUANDO SAI O TRAILER?"),
    ("que lixo de canal", "QUE LIXO DE CANAL"), ("chama no pv", "CHAMA NO PV"),
    ("ficou muito bom", "ficou mt bom mano"), ("não entendi", "n entendi slk"),
])
def test_caixa_alta_e_giria_nao_mudam_a_classe(a, b):
    assert co.classificar_comentario(a) == co.classificar_comentario(b)


def test_lexico_injetado_e_arquivo_padrao():
    lx = {"ofensivos": ["xablau"], "elogio": ["bacana"], "pergunta_marcas": ["?"]}
    assert co.classificar_comentario("seu xablau", lx) == "ignorar"
    assert co.classificar_comentario("bacana", lx) == "curtir"
    assert co.classificar_comentario("que merda", lx) == "curtir"          # o léxico injetado manda
    assert co.classificar_comentario("que merda") == "ignorar"             # o do arquivo
    dados = json.loads(co.ARQUIVO_LEXICO.read_text(encoding="utf-8"))
    for chave in ("ofensivos", "spam", "spam_regex", "pergunta_marcas", "elogio",
                  "critica_que_vale_conversa", "emoji_puro_regex"):
        assert chave in dados
    assert len(dados["ofensivos"]) >= 60 and len(dados["spam"]) >= 40
    for lista in dados.values():
        if isinstance(lista, list):
            for linha in lista:
                assert not str(linha).startswith("## "), linha


@pytest.mark.parametrize("texto, esperado", [
    ("f.d.p", "fdp"), ("f d p", "fdp"), ("v t n c", "vtnc"), ("m3rda", "merda"), ("b0sta", "bosta"),
    ("merdaaaaa", "merda"), ("gta 6 em 2026", "gta 6 em 2026"), ("p0rra kkkk", "porra k"),
])
def test_desmascarar(texto, esperado):
    assert co.desmascarar(co.normalizar(texto)) == esperado


def test_classificar_e_pura_e_devolve_so_as_tres_classes():
    for it in BANCO[:30]:
        assert co.classificar_comentario(it["texto"]) in co.CLASSES
        assert co.classificar_comentario(it["texto"]) == co.classificar_comentario(it["texto"])
    assert co.classificar_comentario(None) == "ignorar"
    assert co.classificar_comentario("") == "ignorar"


# ================================================================== API: ler / curtir / responder / ocultar
def test_ler_comentarios_url_parametros_e_normalizacao():
    c = ClienteFalso().responder("GET", rf"/{POST}/comments$", {"data": [bruto("c1", "Top!", quando="2026-10-01T13:05:00+0000")]})
    lidos = co.ler_comentarios(c, TOKEN, POST)
    ch = c.ultima
    assert ch.metodo == "GET" and ch.url == f"{API}/{POST}/comments"
    assert ch.consulta == {"fields": co.CAMPOS_COMENTARIOS, "filter": "stream", "order": "chronological",
                           "limit": 100, "access_token": TOKEN}
    assert TOKEN not in ch.url and ch.form is None
    assert lidos == [{"id": "c1", "texto": "Top!", "autor_id": "u1", "autor_nome": "Ana",
                      "criado_em": "2026-10-01 10:05", "curtidas": 0, "respostas": 0, "post_id": POST,
                      "bruto": lidos[0]["bruto"]}]


def test_ler_comentarios_paginacao_limite_e_sem_from():
    c = ClienteFalso()
    prox = f"{API}/{POST}/comments?limit=100&after=B&access_token={TOKEN}"
    pagina1 = {"data": [bruto(f"c{i}", f"m{i}") for i in range(3)], "paging": {"next": prox}}
    pagina2 = {"data": [{"id": "c9", "message": "sem autor", "created_time": "2026-10-01T13:00:00+0000"}]}
    c.responder("GET", r"/comments$", [pagina1, pagina2])
    lidos = co.ler_comentarios(c, TOKEN, POST, limite=4)
    assert [l["id"] for l in lidos] == ["c0", "c1", "c2", "c9"]
    assert lidos[3]["autor_id"] is None
    assert len(c.chamadas) == 2 and c.chamadas[1].consulta["after"] == "B" and TOKEN not in c.chamadas[1].url
    c2 = ClienteFalso().responder("GET", r"/comments$", [pagina1, pagina2])
    assert len(co.ler_comentarios(c2, TOKEN, POST, limite=2)) == 2 and len(c2.chamadas) == 1


def test_ler_comentarios_desde_usa_since_epoch_e_filtra():
    desde = datetime(2026, 10, 1, 9, 30, tzinfo=FUSO)      # 12:30Z
    c = ClienteFalso().responder("GET", r"/comments$", {"data": [
        bruto("velho", "antes", quando="2026-10-01T12:00:00+0000"),
        bruto("novo", "depois", quando="2026-10-01T13:00:00+0000")]})
    lidos = co.ler_comentarios(c, TOKEN, POST, desde=desde)
    assert c.ultima.consulta["since"] == int(desde.timestamp())
    assert [l["id"] for l in lidos] == ["novo"]


def test_ler_comentarios_erro_levanta_erro_graph():
    c = ClienteFalso().responder("GET", r"/comments$", erro_meta(10, "(#10) requires pages_read_engagement"))
    with pytest.raises(ErroGraph) as ex:
        co.ler_comentarios(c, TOKEN, POST)
    assert ex.value.permissao == "pages_read_engagement" and "pages_read_engagement" in str(ex.value)


def test_curtir_responder_ocultar_url_metodo_form():
    c = ClienteFalso()
    c.responder("POST", r"/c1/likes$", {"success": True})
    c.responder("POST", r"/c1/comments$", {"id": "c1_resp"})
    c.responder("POST", r"/c1$", {"success": True})
    r1 = co.curtir(c, TOKEN, "c1")
    r2 = co.responder(c, TOKEN, "c1", "Valeu! Sai dia 5.")
    r3 = co.ocultar(c, TOKEN, "c1")
    a, b, d = c.chamadas
    assert (a.metodo, a.url, a.form) == ("POST", f"{API}/c1/likes", {"access_token": TOKEN})
    assert (b.metodo, b.url, b.form) == ("POST", f"{API}/c1/comments", {"message": "Valeu! Sai dia 5.", "access_token": TOKEN})
    assert (d.metodo, d.url, d.form) == ("POST", f"{API}/c1", {"is_hidden": "true", "access_token": TOKEN})
    for ch in (a, b, d):
        assert ch.consulta is None and TOKEN not in ch.url
    assert r1["status"] == "curtido" and r1["id"] == "c1"
    assert r2["status"] == "respondido" and r2["id"] == "c1_resp" and r2["comentario_id"] == "c1"
    assert r3["status"] == "ocultado"
    assert co.ocultar(c, TOKEN, "c1", oculto=False)["status"] == "reexibido" and c.ultima.form["is_hidden"] == "false"


def test_responder_vazio_nao_chama_e_erros_viram_portugues():
    c = ClienteFalso()
    assert co.responder(c, TOKEN, "c1", "   ")["status"] == "erro" and not c.chamadas
    c.responder("POST", r"/c1/likes$", erro_meta(368, "deemed abusive"))
    c.responder("POST", r"/c1/comments$", erro_meta(200, "Permissions error"))
    r1 = co.curtir(c, TOKEN, "c1")
    r2 = co.responder(c, TOKEN, "c1", "oi")
    assert r1["status"] == "erro" and r1["categoria"] == "bloqueio" and "bloqueou" in r1["erro"]
    assert r2["status"] == "erro" and r2["permissao"] == "pages_manage_engagement"


# ================================================================== configuração
def test_config_e_dataclass_com_os_campos_pedidos():
    cfg = co.ConfigComentarios()
    campos = {f.name: f.default for f in dataclasses.fields(cfg)}
    assert campos["max_respostas_por_passada"] == 25
    assert campos["uma_resposta_por_pessoa"] is True
    assert campos["so_posts_nossos"] is True
    assert campos["intervalo_entre_respostas_s"] == 20
    assert campos["curtir_elogios"] is True
    assert campos["enviar"] is False
    assert co.ConfigComentarios(max_respostas_por_passada=3).max_respostas_por_passada == 3


# ================================================================== planejar
def test_planejar_classes_motivos_e_redator():
    cs = [com("c1", "quando sai no pc?", "u1"), com("c2", "top demais", "u2"), com("c3", "chama no pv", "u3"),
          com("c4", "🔥", "u4"), com("c5", "seu idiota", "u5")]
    acoes = co.planejar(cs, set(), co.ConfigComentarios(), {POST})
    assert [a["acao"] for a in acoes] == ["responder", "curtir", "ignorar", "curtir", "ignorar"]
    assert acoes[0]["texto_resposta"] == co.A_REDIGIR and acoes[0]["motivo"] == "pergunta"
    assert "texto_resposta" not in acoes[1]
    assert "ofensivo" in acoes[4]["motivo"] and "spam" in acoes[2]["motivo"]
    assert acoes[0]["comentario_id"] == "c1" and acoes[0]["autor_id"] == "u1" and acoes[0]["post_id"] == POST

    def redator(c):
        return "Sai dia 5!" if "pc" in c["texto"] else None
    acoes = co.planejar(cs, set(), co.ConfigComentarios(), {POST}, redator=redator)
    assert acoes[0]["texto_resposta"] == "Sai dia 5!"

    def redator_quebrado(c):
        raise RuntimeError(f"boom {TOKEN}")
    acoes = co.planejar(cs[:1], set(), co.ConfigComentarios(), {POST}, redator=redator_quebrado)
    assert acoes[0]["texto_resposta"] == co.A_REDIGIR and "redator falhou" in acoes[0]["motivo"]
    sem_token(acoes)


def test_planejar_uma_resposta_por_pessoa():
    cs = [com("c1", "quando sai?", "u1"), com("c2", "e no xbox, quando?", "u1"), com("c3", "qual o preço?", "u2")]
    acoes = co.planejar(cs, set(), co.ConfigComentarios(), {POST})
    assert [a["acao"] for a in acoes] == ["responder", "curtir", "responder"]
    assert "1 por pessoa" in acoes[1]["motivo"]
    acoes2 = co.planejar(cs, {"autor:u1"}, co.ConfigComentarios(), {POST})         # já respondida antes
    assert [a["acao"] for a in acoes2] == ["curtir", "curtir", "responder"]
    acoes3 = co.planejar(cs, set(), co.ConfigComentarios(uma_resposta_por_pessoa=False), {POST})
    assert [a["acao"] for a in acoes3] == ["responder", "responder", "responder"]


def test_planejar_maximo_de_respostas_por_passada():
    cs = [com(f"c{i}", f"quando sai a parte {i}?", f"u{i}") for i in range(30)]
    acoes = co.planejar(cs, set(), co.ConfigComentarios(), {POST})
    assert sum(a["acao"] == "responder" for a in acoes) == 25
    sobra = [a for a in acoes if a["acao"] == "ignorar"]
    assert len(sobra) == 5 and all("próxima passada" in a["motivo"] for a in sobra)
    acoes3 = co.planejar(cs, set(), co.ConfigComentarios(max_respostas_por_passada=3), {POST})
    assert sum(a["acao"] == "responder" for a in acoes3) == 3


def test_planejar_so_post_nosso_ja_tratados_e_nossa_pagina():
    cs = [com("c1", "quando sai?", "u1", post="outro_post"), com("c2", "top", "u2"), com("c3", "massa", "u3"),
          com("c4", "quando sai?", "pagina_hp")]
    acoes = co.planejar(cs, {"c2"}, co.ConfigComentarios(), {POST}, nossos_ids={"pagina_hp"})
    assert [(a["comentario_id"], a["acao"]) for a in acoes] == [("c1", "ignorar"), ("c3", "curtir")]
    assert acoes[0]["motivo"] == "post não é nosso"
    acoes2 = co.planejar(cs[:1], set(), co.ConfigComentarios(so_posts_nossos=False), set())
    assert acoes2[0]["acao"] == "responder"


def test_planejar_curtidas_desligadas_e_limite_de_curtidas():
    cs = [com(f"c{i}", "top demais", f"u{i}") for i in range(5)]
    acoes = co.planejar(cs, set(), co.ConfigComentarios(curtir_elogios=False), {POST})
    assert all(a["acao"] == "ignorar" and "desligadas" in a["motivo"] for a in acoes)
    acoes2 = co.planejar(cs, set(), co.ConfigComentarios(max_curtidas_por_passada=2), {POST})
    assert [a["acao"] for a in acoes2] == ["curtir", "curtir", "ignorar", "ignorar", "ignorar"]


# ================================================================== executar
def _acoes():
    return [{"acao": "responder", "comentario_id": "c1", "autor_id": "u1", "texto_resposta": "Sai dia 5!", "motivo": "pergunta"},
            {"acao": "curtir", "comentario_id": "c2", "autor_id": "u2", "motivo": "elogio"},
            {"acao": "responder", "comentario_id": "c3", "autor_id": "u3", "texto_resposta": co.A_REDIGIR, "motivo": "pergunta"},
            {"acao": "ignorar", "comentario_id": "c4", "autor_id": "u4", "motivo": "ofensivo"},
            {"acao": "responder", "comentario_id": "c5", "autor_id": "u5", "texto_resposta": "Olá!", "motivo": "pedido"}]


def test_executar_sem_enviar_nao_faz_post_e_diz_o_que_faria():
    c = ClienteFalso()
    r = co.executar(c, TOKEN, _acoes(), co.ConfigComentarios(), co.EstadoComentarios())
    assert c.chamadas == []
    assert r["simulado"] is True and r["respondidas"] == 2 and r["curtidas"] == 1 and r["puladas"] == 1
    assert r["resumo"].startswith("SIMULADO")
    assert [x["resultado"] for x in r["resultados"]] == ["simulado (enviar=False)", "simulado (enviar=False)",
                                                         "pulado", "nada a fazer", "simulado (enviar=False)"]
    assert "a redigir" in r["resultados"][2]["porque"]
    r2 = co.executar(c, TOKEN, _acoes(), co.ConfigComentarios(enviar=False), None, enviar=False)
    assert c.chamadas == [] and r2["simulado"] is True


def test_executar_enviar_idempotente_segunda_passada_zero_post(tmp_path):
    c = ClienteFalso()
    c.responder("POST", r"/c\d/likes$", {"success": True})
    c.responder("POST", r"/c\d/comments$", lambda ch: Resposta(200, {"id": ch.url.split("/")[-2] + "_r"}))
    arq = tmp_path / "pasta com espaço" / "comentarios_estado.json"
    estado = co.EstadoComentarios(arq)
    esperas = []
    r = co.executar(c, TOKEN, _acoes(), co.ConfigComentarios(), estado, enviar=True, dormir=esperas.append, agora=AGORA)
    posts = c.chamadas_de("POST")
    assert [p.url.split("/")[-2:] for p in posts] == [["c1", "comments"], ["c2", "likes"], ["c5", "comments"]]
    assert r["simulado"] is False and r["respondidas"] == 2 and r["curtidas"] == 1 and r["erros"] == 0
    assert esperas == [20]                                                      # só entre respostas
    gravado = json.loads(arq.read_text(encoding="utf-8"))
    assert set(gravado["comentarios"]) == {"c1", "c2", "c5"}
    assert gravado["comentarios"]["c1"] == {"acao": "responder", "autor_id": "u1", "quando": "2026-10-01 10:00"}
    assert set(gravado["autores_respondidos"]) == {"u1", "u5"}
    assert not list(arq.parent.glob(".tmp_*"))                                   # gravação atômica sem sobra
    sem_token(arq.read_text(encoding="utf-8"))
    # segunda passada, mesmo estado relido do arquivo: 0 POST
    c2 = ClienteFalso()
    r2 = co.executar(c2, TOKEN, _acoes(), co.ConfigComentarios(), co.EstadoComentarios(arq), enviar=True, dormir=esperas.append)
    assert c2.chamadas == [] and r2["puladas"] == 4 and r2["respondidas"] == 0 and r2["curtidas"] == 0
    assert all("idempotente" in x["porque"] for x in r2["resultados"] if x["resultado"] == "pulado" and x["comentario_id"] != "c3")


def test_executar_uma_resposta_por_pessoa_vira_curtida_e_planejar_le_o_estado():
    estado = co.EstadoComentarios()
    estado.registrar("antigo", "responder", "u1", AGORA)
    assert estado.conjunto_tratados() == {"antigo", "autor:u1"}
    c = ClienteFalso().responder("POST", r"/c1/likes$", {"success": True})
    acoes = [{"acao": "responder", "comentario_id": "c1", "autor_id": "u1", "texto_resposta": "oi", "motivo": "pergunta"}]
    r = co.executar(c, TOKEN, acoes, co.ConfigComentarios(), estado, enviar=True, dormir=lambda s: None)
    assert [ch.url for ch in c.chamadas] == [f"{API}/c1/likes"]
    assert r["resultados"][0]["acao"] == "curtir" and "já recebeu resposta" in r["resultados"][0]["porque"]
    assert estado.tratado("c1")


def test_executar_para_em_token_vencido_e_segue_em_erro_comum():
    c = ClienteFalso()
    c.responder("POST", r"/c1/comments$", erro_meta(100, "bad param"))
    c.responder("POST", r"/c2/likes$", erro_meta(190, "token expired"))
    c.responder("POST", r"/c5/comments$", {"id": "x"})
    estado = co.EstadoComentarios()
    r = co.executar(c, TOKEN, _acoes(), co.ConfigComentarios(), estado, enviar=True, dormir=lambda s: None)
    assert r["erros"] == 2 and r["parou"] and "vencido" in r["parou"]
    assert not c.chamadas_de("POST", "/c5/")                                     # parou antes do c5
    assert not estado.tratado("c1") and not estado.tratado("c2")                # erro não marca
    sem_token(r)


def test_executar_limite_por_passada_e_intervalo_de_curtidas():
    c = ClienteFalso()
    c.responder("POST", r"/likes$", {"success": True})
    c.responder("POST", r"/comments$", {"id": "r"})
    acoes = [{"acao": "responder", "comentario_id": f"r{i}", "autor_id": f"u{i}", "texto_resposta": "oi", "motivo": "m"} for i in range(4)]
    acoes += [{"acao": "curtir", "comentario_id": f"l{i}", "autor_id": f"v{i}", "motivo": "m"} for i in range(3)]
    esperas = []
    cfg = co.ConfigComentarios(max_respostas_por_passada=2, intervalo_entre_respostas_s=7, intervalo_entre_curtidas_s=1)
    r = co.executar(c, TOKEN, acoes, cfg, co.EstadoComentarios(), enviar=True, dormir=esperas.append)
    assert r["respondidas"] == 2 and r["puladas"] == 2 and r["curtidas"] == 3
    assert esperas == [7, 1, 1]


def test_executar_funcoes_injetadas_para_outra_rede():
    chamadas = []

    def resp(cliente, token, cid, texto):
        chamadas.append((cid, texto))
        return {"status": "respondido", "id": "n", "link": None, "erro": None}
    r = co.executar(None, TOKEN, _acoes(), co.ConfigComentarios(), co.EstadoComentarios(), enviar=True,
                    dormir=lambda s: None, funcoes={"responder": resp, "curtir": None})
    assert chamadas == [("c1", "Sai dia 5!"), ("c5", "Olá!")]
    assert r["curtidas"] == 0 and any("não tem a ação curtir" in x.get("porque", "") for x in r["resultados"])


def test_estado_le_arquivo_quebrado_ou_ausente(tmp_path):
    arq = tmp_path / "estado.json"
    assert co.EstadoComentarios(arq).dados["comentarios"] == {}
    arq.write_text("{quebrado", encoding="utf-8")
    assert co.EstadoComentarios(arq).dados["comentarios"] == {}
    assert co.EstadoComentarios.de(None).caminho is None
    e = co.EstadoComentarios(arq)
    assert co.EstadoComentarios.de(e) is e


# ================================================================== permissões / token
def test_permissoes_documentadas_para_leigo():
    assert set(co.PERMISSOES_LEIGO) == {"pages_read_engagement", "pages_read_user_content", "pages_manage_engagement"}
    from publicar_extra.facebook_extra import PERMISSOES
    assert PERMISSOES["responder"] == ("pages_manage_engagement",)
    assert PERMISSOES["curtir"] == ("pages_manage_engagement",)
    assert "pages_manage_posts" not in PERMISSOES["responder"]


def test_token_nunca_aparece_em_nada(tmp_path):
    c = ClienteFalso()
    c.responder("GET", r"/comments$", {"data": [bruto("c1", "quando sai?")],
                                        "paging": {"next": f"{API}/{POST}/comments?after=X&access_token={TOKEN}"}}, vezes=1)
    c.responder("GET", r"/comments$", erro_meta(190, f"expired {TOKEN}"))
    lidos = []
    with pytest.raises(ErroGraph) as ex:
        lidos = co.ler_comentarios(c, TOKEN, POST)
    c.responder("POST", r"/likes$", erro_meta(4, f"limit {TOKEN}"))
    c.responder("POST", r"/comments$", {"id": "r"})
    arq = tmp_path / "estado.json"
    acoes = co.planejar([com("c1", "quando sai?"), com("c2", "top", "u2")], set(), co.ConfigComentarios(), {POST},
                        redator=lambda c: "logo")
    r = co.executar(c, TOKEN, acoes, co.ConfigComentarios(), co.EstadoComentarios(arq), enviar=True, dormir=lambda s: None)
    for ch in c.chamadas:
        assert TOKEN not in ch.url
    sem_token(str(ex.value), ex.value.detalhe, c.texto_de_tudo(), lidos, acoes, r,
              arq.read_text(encoding="utf-8") if arq.exists() else "", [ch.url for ch in c.chamadas])
