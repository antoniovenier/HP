"""pedido_pc: o pedido REAL do hp_studio\\esteira\\pedido.py do PC (§4.5) entrando na esteira da nuvem,
o post.json do publicar, as recusas (Flow Games, não autorizado, vazamento, data), o nome da pasta
ASCII e a leitura do pedido solto só depois de 2 s parado. Sem rede, sem relógio real."""
from __future__ import annotations

import json

from esteira.testes.conftest import envelhecer
from datetime import datetime
from pathlib import Path

import pytest
from hpbase import escrever_json, ler_json, raiz_drive

from esteira import pedido_pc as pp
from esteira.constantes import ERROS, PEDIDOS
from esteira.erros import PedidoInvalido
from esteira.pedido import criar_pedido, normalizar_pedido, validar_pedido

PC_REAL = Path(__file__).resolve().parents[4] / "tests" / "fixtures" / "pc_real"


@pytest.fixture
def config() -> dict:
    return json.loads((PC_REAL / "config_trecho.json").read_text(encoding="utf-8"))


def corte(**kw) -> dict:
    """O corte da docstring real do pedido.py do PC (davyjones = autorizado, PT)."""
    p = {"tipo": "corte", "canal": "gta", "prioridade": 2, "data": "2026-09-30T18:30",
         "video": "c0Com9SMv1s", "streamer": "davyjones", "inicio": "03:26", "fim": "04:04",
         "gancho": "GTA 6 tem corrida de DEMOLIÇÃO",
         "titulo": "GTA 6 vai ter corrida de demolição #gta6 #shorts",
         "legenda": "O norte do mapa é um parque 🏁 Crédito: @DavyJonesGTA6 #gta6 #gtavi",
         "redes": ["instagram", "tiktok", "youtube"]}
    p.update(kw)
    return p


def erros(p: dict, config=None) -> list[str]:
    return validar_pedido(normalizar_pedido(p, config_json=config))


# --- constantes reais --------------------------------------------------------------------------
def test_constantes_reais_do_pc():
    assert pp.TIPOS == ("corte", "carrossel", "story", "texto")
    assert pp.REDES == ("instagram", "facebook", "threads", "youtube", "tiktok")
    assert pp.REDES_PADRAO["corte"] == list(pp.REDES)
    assert pp.REDES_PADRAO["carrossel"] == ["instagram", "facebook"] == pp.REDES_PADRAO["story"]
    assert pp.REDES_PADRAO["texto"] == ["threads"]
    assert pp.ARTES_STORY == ("novo_video", "contagem", "noticia", "interativo")
    assert pp.CAMPOS_DO_PLANO == ("corte", "trechos", "zoom", "cobrir", "bipes", "tarjas",
                                  "fade_saida", "dublar", "n")
    assert pp.PRIORIDADE_PADRAO == 2 and pp.PARADO_SEG == 2.0
    assert issubclass(pp.ErroParametro, PedidoInvalido)


# --- (a) conversão para o modelo interno --------------------------------------------------------
def test_corte_gringo_vira_reel_dublado(config):
    p = pp.para_esteira(corte(streamer="tmartn2", idioma="en", prioridade=1), config=config)
    assert p["tipo"] == "reel" and p["prioridade"] == "P1"
    assert p["horario_alvo"] == "2026-09-30T18:30-03:00"
    assert p["fonte_url"] == "https://www.youtube.com/watch?v=c0Com9SMv1s" and p["arquivos"] == []
    assert p["credito"] == "@TmarTn2"              # crédito do config.json
    assert p["dublar"] is True and p["idioma"] == "en"
    assert p["legenda_post"].startswith("O norte") and "hashtags" not in p   # só se vier explícito
    assert pp.para_esteira(corte(hashtags=["#gta6", "gtavi"]), config=config)["hashtags"] == ["gta6", "gtavi"]
    # os campos que os comandos reais usam continuam lá
    for k in ("inicio", "fim", "video", "gancho"):
        assert p[k] == corte()[k]
    assert p["streamer"] == "tmartn2"
    assert p["slug"] == "gta-6-tem-corrida-de-demolicao" and p["formato_origem"] == "pc"


def test_corte_gringo_pelo_config_sem_idioma_no_pedido(config):
    # criador "en" no config.json e corte sem "dublar": false -> dublado (regra do lote.py)
    assert pp.para_esteira(corte(streamer="tmartn2"), config=config)["dublar"] is True
    assert pp.para_esteira(corte(streamer="tmartn2", dublar=False), config=config)["dublar"] is False
    assert pp.para_esteira(corte(), config=config)["dublar"] is False       # davyjones é PT


def test_corte_com_arquivo_nao_precisa_de_inicio_fim(config):
    pedido = corte(arquivo=r"H:\HypadoLocal\brutos\trecho.mp4")
    pedido.pop("video"), pedido.pop("inicio"), pedido.pop("fim")
    p = pp.para_esteira(pedido, config=config)
    assert p["arquivos"] == [r"H:\HypadoLocal\brutos\trecho.mp4"] and p["fonte_url"] is None
    assert erros(pedido, config) == []
    with pytest.raises(pp.ErroParametro, match="precisa de 'video'"):
        pp.para_esteira({k: v for k, v in pedido.items() if k != "arquivo"}, config=config)


def test_corte_com_link_e_campos_do_plano(config):
    pedido = corte(link="https://www.youtube.com/watch?v=abc123xyz", corte=[6.08, 46.04],
                   trechos=[[0, 10]], fade_saida=1.5, n=801, apelido="Demolição GTA")
    pedido.pop("video")
    p = pp.para_esteira(pedido, config=config)
    assert p["fonte_url"] == "https://www.youtube.com/watch?v=abc123xyz"
    assert p["corte"] == {"inicio": 6.08, "fim": 46.04} and p["trechos"] == [[0, 10]]
    assert p["fade_saida"] == 1.5 and p["lote_n"] == 801 and "n" not in p
    assert p["slug"] == "demolicao-gta"
    with pytest.raises(pp.ErroParametro, match="http"):
        pp.para_esteira(dict(pedido, link="youtube.com/x"), config=config)


def test_carrossel_pula_video_e_passa_na_validacao():
    pedido = {"tipo": "carrossel", "canal": "gta", "prioridade": 2, "data": "2026-10-01T15:00",
              "spec": r"H:\HypadoLocal\upload\carrossel_spec_2026-10-01.json", "tiktok": True,
              "legenda": "1.749 dias. É o tempo entre o anúncio e o lançamento. #gta6 #gtavi"}
    p = pp.para_esteira(pedido)          # sem config: estático não tem criador
    assert p["tipo"] == "carrossel" and p["redes"] == ["instagram", "facebook"]
    assert p["fonte_url"] is None and p["arquivos"] == [] and p["dublar"] is False
    assert p["spec"] == pedido["spec"] and p["tiktok"] is True
    assert p["titulo"] == "1.749 dias. É o tempo entre o anúncio e o lançamento. #gta6 #gtavi"
    assert erros(pedido) == []
    with pytest.raises(pp.ErroParametro, match="spec"):
        pp.para_esteira({k: v for k, v in pedido.items() if k != "spec"})


def test_story_interativo():
    pedido = {"tipo": "story", "data": "2026-10-01T16:00", "arte": "interativo",
              "opcoes": {"titulo": "Furacão chegando em Leonida. O que você faz?"}}
    p = pp.para_esteira(pedido)
    assert p["tipo"] == "story" and p["modelo"] == "interativo" and p["canal"] == "gta"
    assert p["opcoes"]["titulo"].startswith("Furacão") and p["redes"] == ["instagram", "facebook"]
    assert p["titulo"] == "Furacão chegando em Leonida. O que você faz?"
    assert erros(pedido) == []
    with pytest.raises(pp.ErroParametro, match="novo_video, contagem, noticia, interativo"):
        pp.para_esteira(dict(pedido, arte="enquete"))


def test_texto_vira_threads_texto():
    pedido = {"tipo": "texto", "data": "2026-10-01T09:00",
              "texto": "Faltam 49 dias pro GTA 6. 🗓️\n\nJá decidiu se vai jogar no lançamento?"}
    p = pp.para_esteira(pedido)
    assert p["tipo"] == "threads_texto" and p["redes"] == ["threads"]
    assert p["texto"] == pedido["texto"] and p["titulo"] == "Faltam 49 dias pro GTA 6. 🗓️"
    assert erros(pedido) == []
    with pytest.raises(pp.ErroParametro, match="campo 'texto'"):
        pp.para_esteira({"tipo": "texto", "data": "2026-10-01T09:00", "texto": "  "})


def test_prioridade_0_1_2_e_padrao(config):
    assert pp.prioridade_pc(None) == 2 and pp.prioridade_pc("1") == 1 and pp.prioridade_pc("P0") == 0
    for pri, esperado in ((0, "P0"), (1, "P1"), (2, "P2")):
        assert pp.para_esteira(corte(prioridade=pri), config=config)["prioridade"] == esperado
    for ruim in (3, -1, "alta", True):
        with pytest.raises(pp.ErroParametro, match="0, 1 ou 2"):
            pp.prioridade_pc(ruim)


# --- recusas ------------------------------------------------------------------------------------
@pytest.mark.parametrize("campo", pp.CAMPOS_FLOW)
@pytest.mark.parametrize("texto", ["Flow Games", "flowgames", "FLOW PODCAST", "flowpodcast", "flow_games"])
def test_flow_games_recusado_em_cada_campo(config, campo, texto):
    pedido = corte(**{campo: f"corte do {texto} de ontem"})
    if campo == "link":
        pedido["link"] = f"https://youtube.com/{texto.replace(' ', '')}"
        pedido.pop("video")
    with pytest.raises(pp.ErroParametro, match="Flow Games") as e:
        pp.para_esteira(pedido, config=config)
    assert campo in str(e.value)


def test_criador_nao_autorizado_recusado(config):
    with pytest.raises(pp.ErroParametro, match="não está no config.json"):
        pp.para_esteira(corte(streamer="alanzoka"), config=config)
    cfg = dict(config, streamers=[dict(config["streamers"][0], autorizado=False)])
    with pytest.raises(pp.ErroParametro, match='sem "autorizado": true'):
        pp.para_esteira(corte(), config=cfg)
    cfg = dict(config, streamers=[{k: v for k, v in config["streamers"][0].items() if k != "autorizado"}])
    with pytest.raises(pp.ErroParametro, match='sem "autorizado": true'):
        pp.para_esteira(corte(), config=cfg)
    with pytest.raises(pp.ErroParametro, match="precisa de 'streamer'"):
        pp.para_esteira(corte(streamer=""), config=config)


def test_sem_config_json_nenhum_criador_e_autorizado(monkeypatch, tmp_path):
    monkeypatch.setenv("HP_CONFIG_PC", str(tmp_path / "nao_existe.json"))
    with pytest.raises(pp.ErroParametro, match="config.json não encontrado"):
        pp.para_esteira(corte())
    # com o config.json do PC no lugar (HP_CONFIG_PC) o mesmo pedido passa
    monkeypatch.setenv("HP_CONFIG_PC", str(PC_REAL / "config_trecho.json"))
    assert pp.para_esteira(corte())["credito"] == "@DavyJonesGTA6"
    assert pp.ler_config_pc()["marca"]["handle"] == "@hpgta6"


def test_vazamento_de_gta_recusado(config):
    for campo, texto in (("titulo", "GTA 6 vazado: mapa"), ("gancho", "LEAK do GTA 6"),
                         ("legenda", "o vazamento mostra")):
        with pytest.raises(pp.ErroParametro, match="vazamento"):
            pp.para_esteira(corte(**{campo: texto}), config=config)
    # fora do GTA a palavra não é bloqueada por aqui
    assert pp.para_esteira({"tipo": "texto", "canal": "carros", "data": "2026-10-01T09:00",
                            "texto": "Vazou o novo Onix. Valores aproximados."})["canal"] == "carros"


@pytest.mark.parametrize("data", ["30/09/2026", "2026-09-30", "2026-13-01T10:00", "2026-09-31T10:00",
                                  "2026-09-30T25:00", "", None, "amanhã"])
def test_data_invalida_recusada(config, data):
    with pytest.raises(pp.ErroParametro, match="data"):
        pp.para_esteira(corte(data=data), config=config)


def test_data_aceita_espaco_e_segundos(config):
    assert pp.ler_data("2026-09-30 18:30") == datetime(2026, 9, 30, 18, 30)
    assert pp.ler_data("2026-09-30T18:30:45") == datetime(2026, 9, 30, 18, 30, 45)
    p = pp.para_esteira(corte(data="2026-09-30 18:30"), config=config)
    assert p["horario_alvo"] == "2026-09-30T18:30-03:00"


def test_tipo_rede_e_canal_desconhecidos(config):
    with pytest.raises(pp.ErroParametro, match="corte, carrossel, story, texto"):
        pp.para_esteira(corte(tipo="reel"), config=config)
    with pytest.raises(pp.ErroParametro, match="rede desconhecida"):
        pp.para_esteira(corte(redes=["orkut"]), config=config)
    with pytest.raises(pp.ErroParametro, match="não vale num pedido"):
        pp.para_esteira(corte(redes=["pinterest"]), config=config)
    with pytest.raises(pp.ErroParametro, match="canal"):
        pp.para_esteira(corte(canal="xbox"), config=config)
    with pytest.raises(pp.ErroParametro, match="fim"):
        pp.para_esteira(corte(inicio="04:04", fim="03:26"), config=config)


# --- redes -------------------------------------------------------------------------------------
def test_redes_padrao_por_tipo(config):
    assert pp.para_esteira(corte(redes=None), config=config)["redes"] == list(pp.REDES)
    assert pp.para_esteira(corte(redes=[]), config=config)["redes"] == list(pp.REDES)
    base = {"data": "2026-10-01T10:00"}
    assert pp.redes_do_pedido(dict(base, tipo="carrossel", spec="x")) == ["instagram", "facebook"]
    assert pp.redes_do_pedido(dict(base, tipo="story", arte="noticia")) == ["instagram", "facebook"]
    assert pp.redes_do_pedido(dict(base, tipo="texto", texto="oi")) == ["threads"]
    assert pp.redes_do_pedido(corte(redes="instagram, tiktok")) == ["instagram", "tiktok"]


def test_apelidos_de_rede_e_de_tipo():
    for apelido, rede in (("ig", "instagram"), ("fb", "facebook"), ("th", "threads"), ("yt", "youtube"),
                          ("shorts", "youtube"), ("tt", "tiktok"), ("pin", "pinterest"),
                          ("comunidade", "youtube_comunidade"), ("Instagram", "instagram")):
        assert pp.normalizar_rede(apelido) == rede
    for apelido, tipo in (("short", "reel"), ("foto", "feed"), ("longo", "video"), ("corte", "reel"),
                          ("threads_texto", "texto"), ("comunidade", "comunidade")):
        assert pp.normalizar_tipo_post(apelido) == tipo
    with pytest.raises(pp.ErroParametro, match="tipo de post"):
        pp.normalizar_tipo_post("album")
    p = pp.para_esteira(corte(redes=["IG", "yt", "tt", "ig"]), config=json.loads(
        (PC_REAL / "config_trecho.json").read_text(encoding="utf-8")))
    assert p["redes"] == ["instagram", "youtube", "tiktok"]


# --- nome da pasta ------------------------------------------------------------------------------
def test_nome_da_pasta_ascii_sem_espaco():
    nome = pp.nome_da_pasta(corte(gancho="Ação & Demolição: GTA 6 é LOUCO 🔥!!"))
    assert nome == "P2_2026-09-30_1830_gta_acao-demolicao-gta-6-e-louco"
    assert nome.isascii() and " " not in nome
    longo = pp.nome_da_pasta(corte(prioridade=0, gancho="x" * 100, canal="destinos"))
    pri, data, hora, canal, apelido = longo.split("_", 4)
    assert (pri, data, hora, canal) == ("P0", "2026-09-30", "1830", "destinos")
    assert len(apelido) <= 40 and len(canal) <= 20
    assert pp.nome_da_pasta(corte(apelido="gol do mengão")).endswith("_gta_gol-do-mengao")
    assert pp.nome_da_pasta({"tipo": "texto", "data": "2026-10-01T09:00", "texto": "Faltam 49 dias!"}) \
        == "P2_2026-10-01_0900_gta_faltam-49-dias"


def test_nome_da_pasta_bate_com_o_id_da_esteira(config):
    pedido = corte(prioridade=1)
    n = normalizar_pedido(pedido, config_json=config)
    assert pp.nome_da_pasta(pedido) == "P1_" + n["id"]


# --- pedido solto: 2 s parado -------------------------------------------------------------------
def test_ler_pedido_pc_so_depois_de_2s_parado(tmp_path):
    arq = tmp_path / "pedido.json"
    arq.write_text(json.dumps(corte()), encoding="utf-8")
    t0 = 1_800_000_000.0
    assert pp.ler_pedido_pc(arq, agora=t0 + 0.5, mtime=t0) is None          # ainda gravando?
    assert pp.ler_pedido_pc(arq, agora=t0 + 1.99, mtime=t0) is None
    assert pp.ler_pedido_pc(arq, agora=t0 + 2.0, mtime=t0)["streamer"] == "davyjones"
    assert pp.ler_pedido_pc(arq, agora=t0 + 60, mtime=lambda p: t0)["tipo"] == "corte"
    # datetime também vale para os dois
    agora = datetime(2026, 10, 1, 12, 0, 5)
    assert pp.ler_pedido_pc(arq, agora=agora, mtime=datetime(2026, 10, 1, 12, 0, 4)) is None
    assert pp.ler_pedido_pc(arq, agora=agora, mtime=datetime(2026, 10, 1, 12, 0, 3)) is not None
    # mtime do disco: arquivo recém-gravado com agora = agora do disco -> None; 1 h depois -> lê
    m = arq.stat().st_mtime
    assert pp.ler_pedido_pc(arq, agora=m + 1) is None
    assert pp.ler_pedido_pc(arq, agora=m + 3600) is not None
    assert pp.ler_pedido_pc(arq, agora=t0 + 10, mtime=t0, parado_seg=30) is None


def test_ler_pedido_pc_ilegivel_ou_inexistente(tmp_path):
    arq = tmp_path / "quebrado.json"
    arq.write_text('{"tipo": "corte", ', encoding="utf-8")
    with pytest.raises(pp.ErroParametro, match="JSON quebrado"):
        pp.ler_pedido_pc(arq, agora=1e9 + 10, mtime=1e9)
    arq.write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(pp.ErroParametro, match="objeto JSON"):
        pp.ler_pedido_pc(arq, agora=1e9 + 10, mtime=1e9)
    with pytest.raises(pp.ErroParametro, match="não encontrado"):
        pp.ler_pedido_pc(tmp_path / "nada.json", agora=1e9)


# --- (b) post.json ------------------------------------------------------------------------------
def test_post_json_do_corte(config):
    post = pp.para_post_json(corte(streamer="tmartn2", redes=["ig", "shorts", "tt"]), config=config)
    assert post == {
        "canal": "gta", "tipo": "reel", "quando": "2026-09-30 18:30",
        "titulo": "GTA 6 vai ter corrida de demolição #gta6 #shorts",
        "legenda": "O norte do mapa é um parque 🏁 Crédito: @DavyJonesGTA6 #gta6 #gtavi",
        "arquivos": ["final.mp4"], "capa": "capa.jpg", "tags": ["gta6", "gtavi"],
        "dublado": True, "redes": ["instagram", "youtube", "tiktok"],
    }
    assert set(post) == {"canal", "tipo", "quando", "titulo", "legenda", "arquivos", "capa", "tags",
                         "dublado", "redes"}
    # hashtags explícitas valem como tags; arquivos/capa podem ser sobrepostos
    post = pp.para_post_json(corte(hashtags=["#gta6", "vicecity"]), arquivos=["upload.mp4"], capa="c.jpg",
                             config=config)
    assert post["tags"] == ["gta6", "vicecity"] and post["arquivos"] == ["upload.mp4"] and post["capa"] == "c.jpg"


def test_post_json_textos_por_rede_vira_objeto(config):
    post = pp.para_post_json(corte(redes=["instagram", "threads"],
                                   textos={"th": "Pergunta pro Threads?", "youtube": "ignorado"}),
                             config=config)
    assert post["redes"] == {"instagram": {}, "threads": {"legenda": "Pergunta pro Threads?"}}


def test_post_json_dos_estaticos_e_do_pedido_interno(config):
    texto = {"tipo": "texto", "data": "2026-10-01T09:00", "texto": "Faltam 49 dias pro GTA 6.\n\nJá decidiu?"}
    post = pp.para_post_json(texto)
    assert post["tipo"] == "texto" and post["redes"] == ["threads"] and post["arquivos"] == []
    assert post["legenda"] == texto["texto"] and post["titulo"] == "Faltam 49 dias pro GTA 6." and "capa" not in post
    story = pp.para_post_json({"tipo": "story", "data": "2026-10-01T16:00", "arte": "interativo",
                               "arquivo": r"H:\HypadoLocal\upload\story.jpg"})
    assert story["tipo"] == "story" and story["arquivos"] == [r"H:\HypadoLocal\upload\story.jpg"]
    assert story["quando"] == "2026-10-01 16:00" and story["dublado"] is False
    # o pedido interno (já convertido, horario_alvo com fuso) dá o mesmo post.json
    interno = normalizar_pedido(corte(streamer="tmartn2"), config_json=config)
    assert pp.para_post_json(interno) == pp.para_post_json(corte(streamer="tmartn2"), config=config)
    utc = dict(interno, horario_alvo="2026-09-30T21:30:00+00:00")
    assert pp.para_post_json(utc)["quando"] == "2026-09-30 18:30"


# --- integração com a esteira -------------------------------------------------------------------
def test_normalizar_pedido_reconhece_o_formato_real(config):
    assert pp.eh_pedido_pc(corte()) and pp.eh_pedido_pc({"tipo": "carrossel", "data": "x"})
    assert pp.eh_pedido_pc({"tipo": "story", "prioridade": 1, "arte": "noticia"})
    assert not pp.eh_pedido_pc({"tipo": "reel", "prioridade": 0, "horario_alvo": "2026-09-30 18:30"})
    assert not pp.eh_pedido_pc({"tipo": "carrossel", "prioridade": "P1"}) and not pp.eh_pedido_pc([1])
    n = normalizar_pedido(corte(), config_json=config)
    assert n["tipo"] == "reel" and n["prioridade"] == "P2" and n["dublar"] is False
    assert n["id"] == "2026-09-30_1830_gta_gta-6-tem-corrida-de-demolicao"
    assert validar_pedido(n) == []
    with pytest.raises(PedidoInvalido, match="Flow Games"):
        normalizar_pedido(corte(gancho="o Flow Games falou"), config_json=config)
    # o formato interno da rodada 1 continua intacto (prioridade inteira + horario_alvo)
    p = normalizar_pedido({"canal": "GTA", "tipo": "Reel", "titulo": "Olá Mundo", "redes": "instagram, tiktok",
                           "prioridade": 0, "horario_alvo": "2026-09-30 18:30"})
    assert p["tipo"] == "reel" and p["prioridade"] == "P0" and p["id"] == "2026-09-30_1830_gta_ola-mundo"


def test_gringo_no_gta_dubla_como_o_pc(config):
    """O PC dubla criador 'en' no GTA (config.json real: "dublagem" + criadores "en"); a esteira
    da nuvem passou a aceitar (CANAIS_COM_VOZ tem gta desde a rodada 2). Futebol continua proibido."""
    n = normalizar_pedido(corte(streamer="tmartn2"), config_json=config)
    assert n["dublar"] is True
    assert validar_pedido(n) == []
    assert any("futebol nunca leva voz sintética" in e
               for e in validar_pedido({**n, "canal": "futebol", "fonte_oficial": True}))


def test_criar_pedido_real_cria_a_pasta_com_o_nome_do_pc(amb, config):
    escrever_json(raiz_drive() / "06 Projeto" / "config.json", config)      # o config.json do PC
    item = criar_pedido(corte(prioridade=0, apelido="corrida de demolição"))
    assert item.parent == amb.pasta(PEDIDOS)
    assert item.name == "P0_2026-09-30_1830_gta_corrida-de-demolicao" == pp.nome_da_pasta(
        corte(prioridade=0, apelido="corrida de demolição"))
    dados = ler_json(item / "pedido.json")
    assert dados["tipo"] == "reel" and dados["fonte_url"].endswith("c0Com9SMv1s")
    assert dados["streamer"] == "davyjones" and dados["inicio"] == "03:26"
    with pytest.raises(PedidoInvalido, match="não está no config.json"):
        criar_pedido(corte(streamer="alanzoka", gancho="outro"))


def test_pedido_solto_real_importado_pelo_motor_e_recusado_quando_ruim(amb, config):
    escrever_json(raiz_drive() / "06 Projeto" / "config.json", config)
    (amb.pasta(PEDIDOS) / "pedido_do_claude.json").write_text(
        json.dumps(corte(), ensure_ascii=False), encoding="utf-8")
    (amb.pasta(PEDIDOS) / "flow.json").write_text(
        json.dumps(corte(streamer="flowgames", gancho="flow")), encoding="utf-8")
    (amb.pasta(PEDIDOS) / "texto.json").write_text(
        json.dumps({"tipo": "texto", "data": "2026-10-01T09:00", "texto": "Faltam 49 dias."}), encoding="utf-8")
    assert amb.ciclo(max_trabalhos=0)["importados"] == []      # < 2 s parado: ainda não lê (4.5)
    envelhecer(*amb.pasta(PEDIDOS).glob("*.json"))
    r = amb.ciclo(max_trabalhos=0)
    assert sorted(r["importados"]) == ["P2_2026-09-30_1830_gta_gta-6-tem-corrida-de-demolicao",
                                       "P2_2026-10-01_0900_gta_faltam-49-dias"]
    assert amb.itens(ERROS) == ["entrada_invalida_flow"]
    e = ler_json(amb.pasta(ERROS) / "entrada_invalida_flow" / "erro.json")
    assert "Flow Games" in e["mensagem"] and e["permanente"] is True
