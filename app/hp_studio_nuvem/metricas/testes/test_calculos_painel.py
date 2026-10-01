import json

from hpbase import escrever_json

from metricas import calculos, painel
from metricas.coleta import coletar
from metricas.config import pasta_metricas

from .falso import AGORA, cliente_completo, config_teste, escrever_segredos


def _foto_antiga(data, seg_ig, posts=()):
    return {"data": data, "coletado_em": f"{data}T06:00:00-03:00",
            "contas": {"gta": {"instagram": {"status": "ok", "seguidores": seg_ig,
                                             "posts": list(posts)},
                               "threads": {"status": "ok", "seguidores": 790, "posts": []}}}}


def test_taxa_de_engajamento_e_totais():
    p = {"curtidas": 10, "comentarios": 5, "salvamentos": 3, "compartilhamentos": 2,
         "alcance": 200, "views": 400}
    assert calculos.taxa_engajamento(p) == 0.1
    assert calculos.taxa_engajamento({**p, "alcance": 0}) is None
    assert calculos.taxa_engajamento({"curtidas": 3, "alcance": 30, "salvamentos": None}) == 0.1
    t = calculos.totais([p, {"curtidas": 1, "views": None, "alcance": None}])
    assert t["posts"] == 2 and t["curtidas"] == 11 and t["views"] == 400
    assert t["taxa_engajamento"] == 0.1  # só posts com alcance entram na taxa
    assert calculos.totais([])["taxa_engajamento"] is None


def test_media_de_views_por_formato_e_por_hora():
    posts = [
        {"tipo": "reels", "views": 100, "publicado_em": "2026-09-29T12:10:00-03:00"},
        {"tipo": "reels", "views": 300, "publicado_em": "2026-09-28T12:50:00-03:00"},
        {"tipo": "carrossel", "views": 50, "publicado_em": "2026-09-28T18:00:00-03:00"},
        {"tipo": "carrossel", "views": None, "publicado_em": "2026-09-28T18:00:00-03:00"},
    ]
    assert calculos.views_por_formato(posts) == {
        "carrossel": {"media": 50.0, "posts": 1}, "reels": {"media": 200.0, "posts": 2}}
    assert calculos.views_por_hora(posts) == {
        "12h": {"media": 200.0, "posts": 2}, "18h": {"media": 50.0, "posts": 1}}


def test_deltas_de_seguidores_dia_e_7d(raizes_temporarias):
    local, _ = raizes_temporarias
    escrever_segredos(local)
    pasta = pasta_metricas()
    velho = {"id": "OLD1", "tipo": "reels", "views": 1000,
             "publicado_em": "2026-09-25T10:00:00-03:00"}
    escrever_json(pasta / "2026-09-29.json", _foto_antiga("2026-09-29", 1400))
    escrever_json(pasta / "2026-09-25.json", _foto_antiga("2026-09-25", 1100, [velho]))
    escrever_json(pasta / "2026-09-23.json", _foto_antiga("2026-09-23", 1000))

    foto = coletar(["gta"], cliente=cliente_completo(), agora=AGORA, config=config_teste())
    a = foto["analise"]["gta"]
    assert (a["instagram"]["delta_dia"], a["instagram"]["delta_7d"]) == (100, 500)
    assert (a["threads"]["delta_dia"], a["threads"]["delta_7d"]) == (10, 10)
    assert a["facebook"]["delta_dia"] is None  # não havia foto do Facebook ontem
    # a média por formato junta o histórico (OLD1, de 25/09) com os posts de hoje
    assert a["instagram"]["views_por_formato"]["reels"] == {"media": 5000.0, "posts": 2}
    assert a["instagram"]["views_por_hora"]["22h"] == {"media": 9000.0, "posts": 1}
    assert a["instagram"]["taxa_engajamento"] is not None

    p = json.loads((pasta / "metricas_painel.json").read_text(encoding="utf-8"))
    ig = p["contas"]["gta"]["redes"]["instagram"]
    assert (ig["seguidores"], ig["delta_dia"], ig["delta_7d"]) == (1500, 100, 500)
    assert p["contas"]["gta"]["nome"] == "GTA 6 | HP"
    assert [t["id"] for t in p["top_posts"]["24h"]] == ["M1", "V1", "555", "T1"]
    assert [t["id"] for t in p["top_posts"]["7d"]] == ["M1", "V1", "555", "V2", "T1"]
    assert p["top_posts"]["24h"][0]["rede"] == "instagram"
    assert p["totais"]["seguidores"] == 1500 + 800 + 3000 + 2500


def test_exportacao_do_painel_top5_e_janelas():
    posts = [{"id": f"P{i}", "views": v, "publicado_em": d, "tipo": "reels",
              "legenda_inicio": f"post {i}", "link": f"https://x/{i}"}
             for i, (v, d) in enumerate([
                 (10, "2026-09-29T10:00:00-03:00"), (70, "2026-09-29T09:00:00-03:00"),
                 (30, "2026-09-29T20:00:00-03:00"), (90, "2026-09-26T09:00:00-03:00"),
                 (50, "2026-09-29T08:00:00-03:00"), (60, "2026-09-29T07:00:00-03:00"),
                 (99, "2026-09-10T07:00:00-03:00"), (80, "2026-09-29T11:00:00-03:00")])]
    foto = {"data": "2026-09-30", "coletado_em": "2026-09-30T06:00:00-03:00",
            "contas": {"carros": {"instagram": {"status": "ok", "seguidores": 10, "posts": posts},
                                  "tiktok": {"fonte": "manual", "status": "ok",
                                             "seguidores": 5, "posts": []}}},
            "analise": {"carros": {"instagram": {"delta_dia": 2, "delta_7d": None}}}}
    p = painel.montar(foto, {"contas": {"carros": {"nome": "Carros | HP"}}})
    assert [t["id"] for t in p["top_posts"]["24h"]] == ["P7", "P1", "P5", "P4", "P2"]
    assert [t["id"] for t in p["top_posts"]["7d"]] == ["P3", "P7", "P1", "P5", "P4"]
    c = p["contas"]["carros"]
    assert c["nome"] == "Carros | HP" and c["seguidores_total"] == 15
    assert c["redes"]["tiktok"]["fonte"] == "manual"
    assert c["redes"]["instagram"]["views_24h"] == 10 + 70 + 30 + 50 + 60 + 80
    assert c["redes"]["instagram"]["posts_24h"] == 6
    assert c["delta_dia_total"] == 2 and p["totais"]["delta_dia"] == 2
    assert len(c["top_7d"]) == 5
