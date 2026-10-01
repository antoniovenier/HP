import json

import pytest

from hpbase import pasta_logs

from metricas.cliente import ErroAPI, ErroNaoAutorizado, ErroTemporario, paginar
from metricas.coleta import coletar
from metricas.config import pasta_metricas

from .falso import (AGORA, IG_ID, OAUTH, PAGINA3, TOKENS, ClienteFalso, cliente_completo,
                    config_teste, escrever_segredos)


@pytest.fixture
def local(raizes_temporarias):
    local, _ = raizes_temporarias
    escrever_segredos(local)
    return local


def _coletar(cliente=None, **kw):
    kw.setdefault("config", config_teste())
    return coletar(["gta"], cliente=cliente or cliente_completo(), agora=AGORA, **kw)


def test_coleta_completa(local):
    cliente = cliente_completo()
    foto = _coletar(cliente)
    gta = foto["contas"]["gta"]
    assert foto["data"] == "2026-09-30"
    assert {r: gta[r]["status"] for r in gta} == {
        "instagram": "ok", "threads": "ok", "facebook": "ok", "youtube": "ok",
        "tiktok": "aguardando_importacao"}
    assert gta["tiktok"]["fonte"] == "manual"

    ig = gta["instagram"]
    assert ig["seguidores"] == 1500 and ig["usuario"] == "hpgta6"
    assert [p["id"] for p in ig["posts"]] == ["M1", "M2", "M3"]  # M4 é velho (> 7 dias)
    m1 = ig["posts"][0]
    campos = {"id", "legenda_inicio", "tipo", "publicado_em", "link", "curtidas", "comentarios",
              "views", "salvamentos", "compartilhamentos", "alcance"}
    assert campos <= set(m1)
    assert (m1["tipo"], m1["views"], m1["alcance"], m1["salvamentos"],
            m1["compartilhamentos"]) == ("reels", 9000, 5000, 60, 100)
    assert m1["publicado_em"] == "2026-09-29T22:00:00-03:00"  # hora de Brasília
    assert m1["taxa_engajamento"] == round((300 + 40 + 60 + 100) / 5000, 4)
    assert ig["totais"]["posts"] == 3 and ig["totais"]["curtidas"] == 500

    th = gta["threads"]
    assert th["seguidores"] == 800 and [p["id"] for p in th["posts"]] == ["T1"]  # sem repost
    t1 = th["posts"][0]
    assert (t1["views"], t1["curtidas"], t1["comentarios"], t1["compartilhamentos"]) == \
        (1200, 50, 12, 4)

    fb = gta["facebook"]
    assert fb["seguidores"] == 3000
    ids = [p["id"] for p in fb["posts"]]
    assert ids == ["555", f"{'1000000000000001'}_777"]  # reel não aparece duplicado
    assert fb["posts"][0]["views"] == 5000 and fb["posts"][0]["tipo"] == "reels"
    assert fb["posts"][0]["link"] == "https://www.facebook.com/reel/555"
    assert fb["posts"][1]["alcance"] == 900 and fb["posts"][1]["views"] is None

    yt = gta["youtube"]
    assert yt["seguidores"] == 2500 and yt["analytics"] == "ok"
    assert [(p["id"], p["tipo"], p["views"], p["compartilhamentos"]) for p in yt["posts"]] == \
        [("V1", "shorts", 7000, 55), ("V2", "video", 1500, 5)]

    pasta = pasta_metricas()
    for nome in ("2026-09-30.json", "ultimo.json", "metricas_painel.json"):
        assert (pasta / nome).exists(), nome
    gravado = json.loads((pasta / "2026-09-30.json").read_text(encoding="utf-8"))
    assert gravado["contas"]["gta"]["instagram"]["seguidores"] == 1500
    assert "analise" in gravado and gravado["analise"]["gta"]["instagram"]["seguidores"] == 1500
    assert cliente.contar(PAGINA3) == 0


def test_paginacao_segue_paging_next_e_para_no_limite():
    c = ClienteFalso({
        "/X/media": {"data": [{"id": 1}, {"id": 2}], "paging": {"next": "https://h/p2"}},
        "https://h/p2": {"data": [{"id": 3}, {"id": 4}], "paging": {"next": "https://h/p3"}},
        "https://h/p3": {"data": [{"id": 5}]},
    })
    assert [i["id"] for i in paginar(c, "https://h/v21.0/X/media", {"limit": 2})] == [1, 2, 3, 4, 5]
    assert c.chamadas[1] == ("https://h/p2", {})  # o next já traz os parâmetros
    c.chamadas.clear()
    assert [i["id"] for i in paginar(c, "https://h/v21.0/X/media", limite=3)] == [1, 2, 3]
    assert len(c.chamadas) == 2


def test_limite_posts_da_config(local):
    cfg = config_teste()
    cfg["limite_posts"] = 1
    foto = _coletar(config=cfg)
    assert [p["id"] for p in foto["contas"]["gta"]["instagram"]["posts"]] == ["M1"]


def test_metrica_nao_suportada_cai_para_subconjunto(local):
    cliente = cliente_completo()
    foto = _coletar(cliente, config=config_teste())
    m2, m3 = foto["contas"]["gta"]["instagram"]["posts"][1:]
    assert (m2["alcance"], m2["salvamentos"], m2["compartilhamentos"], m2["views"]) == \
        (2000, 30, 40, None)
    assert m3["alcance"] == 1000
    # M2: 1 pedido completo recusado + 5 uma a uma; M3 já sabe que "views" não vale
    assert cliente.contar("/M2/insights") == 6
    assert cliente.contar("/M3/insights") == 1
    pedido_m3 = [p for u, p in cliente.chamadas if "/M3/insights" in u][0]
    assert "views" not in pedido_m3["metric"].split(",")
    assert foto["contas"]["gta"]["instagram"]["avisos"] == []


def test_token_nunca_aparece_no_log_nem_no_json(local):
    tok = TOKENS["IG_GTA_TOKEN"]
    vazou = ErroAPI(f"falhou GET https://graph.facebook.com/v21.0/{IG_ID}?access_token={tok} "
                    f"(token {tok})", status=400)
    cliente = cliente_completo(**{f"/{IG_ID}": vazou})
    foto = _coletar(cliente)
    st = foto["contas"]["gta"]["instagram"]["status"]
    assert st.startswith("erro:") and "***" in st
    textos = [p.read_text(encoding="utf-8") for p in pasta_metricas().glob("*.json")]
    textos += [p.read_text(encoding="utf-8") for p in pasta_logs().glob("metricas_*.log")]
    assert textos
    for valor in list(TOKENS.values()) + [OAUTH]:
        for t in textos:
            assert valor not in t


def test_falha_de_uma_rede_nao_derruba_as_outras(local):
    cliente = cliente_completo(**{
        f"/{IG_ID}": ErroTemporario("HTTP 503 em /v21.0/x", status=503),
        "/1000000000000001": ErroNaoAutorizado("HTTP 400: (#190) token vencido", status=400,
                                               codigo=190),
        "/youtube/v3/channels": RuntimeError("quebrou"),
    })
    gta = _coletar(cliente)["contas"]["gta"]
    assert gta["instagram"]["status"].startswith("erro:HTTP 503")
    assert gta["facebook"]["status"] == "nao_autorizado"
    assert "190" in gta["facebook"]["detalhe"]
    assert gta["youtube"]["status"] == "erro:quebrou"
    assert gta["threads"]["status"] == "ok" and gta["threads"]["seguidores"] == 800


def test_sem_token_e_youtube_nao_autorizado(raizes_temporarias):
    local, _ = raizes_temporarias
    escrever_segredos(local, sem=("TH_GTA_TOKEN",))
    cliente = cliente_completo()
    gta = coletar(["gta"], cliente=cliente, agora=AGORA,
                  config=config_teste(youtube_autorizado=False))["contas"]["gta"]
    assert gta["threads"]["status"] == "sem_token"
    assert "TH_GTA_TOKEN" in gta["threads"]["detalhe"]
    assert gta["youtube"]["status"] == "nao_autorizado"
    assert cliente.contar("googleapis") == 0 and cliente.contar("threads") == 0
    assert gta["instagram"]["status"] == "ok"


def test_youtube_sem_oauth_pula_analytics(raizes_temporarias):
    local, _ = raizes_temporarias
    escrever_segredos(local, sem=("YT_GTA_REFRESH_TOKEN",))
    cliente = cliente_completo()
    yt = _coletar(cliente, redes=["youtube"])["contas"]["gta"]["youtube"]
    assert yt["status"] == "ok" and yt["analytics"] == "nao_autorizado"
    assert yt["posts"][0]["compartilhamentos"] is None
    assert cliente.contar("/v2/reports") == 0


def test_insights_sem_permissao_vira_aviso(local):
    cliente = cliente_completo(**{"/M1/insights": ErroNaoAutorizado(
        "HTTP 403: (#10) sem instagram_manage_insights", status=403, codigo=10)})
    ig = _coletar(cliente, redes=["instagram"])["contas"]["gta"]["instagram"]
    assert ig["status"] == "ok" and len(ig["posts"]) == 3
    assert ig["avisos"] and "nao_autorizado" in ig["avisos"][0]
    assert cliente.contar("/M2/insights") == 0  # parou de pedir insights


def test_coleta_sob_demanda_mescla_e_preserva(local):
    _coletar()
    # à tarde: só instagram, e a API cai → mantém os números da manhã
    cliente = cliente_completo(**{f"/{IG_ID}": ErroTemporario("HTTP 502", status=502)})
    foto = _coletar(cliente, redes=["instagram"])
    gta = foto["contas"]["gta"]
    assert gta["threads"]["status"] == "ok"  # não foi coletado de novo, mas continua lá
    assert gta["instagram"]["status"].startswith("erro:")
    assert gta["instagram"]["seguidores"] == 1500
    assert gta["instagram"]["dados_de"] == "2026-09-30T06:00:00-03:00"


def test_conta_ou_rede_desconhecida():
    with pytest.raises(ValueError):
        coletar(["xyz"], cliente=ClienteFalso(), agora=AGORA, config=config_teste(), gravar=False)
