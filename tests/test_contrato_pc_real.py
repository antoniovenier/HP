"""Teste de contrato com os formatos REAIS do PC (tests/fixtures/pc_real/, Seção 4 do prompt).

É o que o PC roda depois de cada integração: carrega TODAS as fixtures e passa cada uma pelo
adaptador responsável. Se uma fixture mudar de formato, a falha diz qual campo quebrou
("fixture X mudou de formato: campo Y"). Um teste falha se aparecer fixture nova sem adaptador.

Nada aqui toca rede, adb, segredos, Windows, ffmpeg nem relógio real (hora sempre injetada;
H:/G: viram pastas temporárias pelo conftest).
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from hpbase import FUSO, escrever_json, marca
from hpbase import fila_api_pc as fa
from esteira import comandos_pc as cp
from esteira import legendas, pedido_pc
from whatsapp_local import fila_pc
from whatsapp_local.fila import Fila
import esquema_radar
import story_post
import story_post_lote
import ui_dump

RAIZ = Path(__file__).resolve().parents[1]
PC_REAL = RAIZ / "tests" / "fixtures" / "pc_real"

# fixture (regex sobre o nome) -> adaptador responsável (só para o relatório da falha)
ADAPTADORES = [
    (r"^fila_api_limite_24h\.json$", "hpbase.fila_api_pc.ler_limite_24h"),
    (r"^fila_api_publicador\.log$", "hpbase.fila_api_pc.ler_log"),
    (r"^fila_api_.*\.json$", "hpbase.fila_api_pc.montar_item + ler_confirmacao"),
    (r"^config_trecho\.json$", "esteira.pedido_pc (criadores) + hpbase.marca"),
    (r"^transcricao_exemplo\.json$", "esteira.legendas (segmentos/palavras)"),
    (r"^plano_corte_exemplo\.json$", "esteira.pedido_pc + esteira.comandos_pc.argv_cortar"),
    (r"^lote_estaticos_.*\.json$", "scripts/story_post_lote"),
    (r"^agendados_exemplo\.json$", "whatsapp_local.fila_pc.montar_aviso_no_ar"),
    (r"^whatsapp_fila_real\.json$", "whatsapp_local.fila_pc (ida e volta)"),
    (r"^fila_story_pedido_real.*\.json$", "scripts/story_post.resolver_conta/validar_link"),
    (r"^ui_.*\.txt$", "scripts/ui_dump.ler_linhas_ui"),
    (r"^radar_.*\.json$", "radar_fontes/esquema_radar.validar_config_radar"),
]
AGORA = datetime(2026, 10, 1, 12, 0)


def _fixtures() -> list[Path]:
    return sorted(p for p in PC_REAL.iterdir() if p.is_file())


def _adaptador(nome: str) -> str | None:
    return next((a for rx, a in ADAPTADORES if re.match(rx, nome)), None)


def _json(nome: str):
    try:
        return json.loads((PC_REAL / nome).read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        pytest.fail(f"fixture {nome} mudou de formato: não é JSON válido ({e})")


def _campo(nome: str, dados: dict, campo: str, tipo=None, nao_vazio: bool = False):
    """Lê `campo` de uma fixture com mensagem clara se faltar ou mudar de tipo."""
    if not isinstance(dados, dict) or campo not in dados:
        pytest.fail(f"fixture {nome} mudou de formato: campo {campo} faltando")
    v = dados[campo]
    if tipo is not None and not isinstance(v, tipo):
        pytest.fail(f"fixture {nome} mudou de formato: campo {campo} deveria ser {tipo.__name__}, "
                    f"veio {type(v).__name__}")
    if nao_vazio and not v:
        pytest.fail(f"fixture {nome} mudou de formato: campo {campo} vazio")
    return v


# ================================================================ cobertura
def test_todas_as_20_fixtures_tem_adaptador():
    fixtures = _fixtures()
    assert len(fixtures) >= 20, f"faltam fixtures em {PC_REAL}: {[p.name for p in fixtures]}"
    sem = [p.name for p in fixtures if _adaptador(p.name) is None]
    assert not sem, f"fixture sem adaptador (inclua em ADAPTADORES e escreva o teste): {sem}"


@pytest.mark.parametrize("nome", [p.name for p in _fixtures()])
def test_fixture_e_texto_utf8_e_json_valido(nome):
    texto = (PC_REAL / nome).read_text(encoding="utf-8-sig")          # falha se não for utf-8
    assert texto.strip(), f"fixture {nome} está vazia"
    if nome.endswith(".json"):
        assert isinstance(_json(nome), (dict, list))


# ================================================================ 4.1 fila da API
ITENS_FILA = sorted(p.name for p in PC_REAL.glob("fila_api_*.json") if "limite" not in p.name)


def _subpasta(nome: str) -> str | None:
    for sub in ("feitos", "erros", "story_clicavel"):
        if f"_{sub}_" in nome:
            return sub
    return None


@pytest.mark.parametrize("nome", ITENS_FILA)
def test_item_da_fila_passa_por_montar_item_e_ler_confirmacao(nome, tmp_path):
    d = _json(nome)
    for campo, tipo in (("id", str), ("conta", str), ("rede", str), ("tipo", str), ("arquivos", list),
                        ("legenda", str), ("quando", str), ("canal", str), ("grupo_whatsapp", str)):
        _campo(nome, d, campo, tipo)
    extras = {k: v for k, v in d.items() if k not in ("id", "conta", "rede", "tipo", "arquivos", "legenda",
                                                        "quando", "canal", "grupo_whatsapp", "titulo")}
    item = fa.montar_item(d["conta"], d["rede"], d["tipo"], d["arquivos"], d["legenda"], d["quando"],
                          canal=d["canal"], titulo=d.get("titulo"), grupo_whatsapp=d["grupo_whatsapp"],
                          id_=d["id"], pasta_fila=tmp_path, existe=lambda p: True, **extras)
    assert item["id"] == d["id"] and item["conta"] == d["conta"] and item["rede"] == d["rede"]
    assert item["arquivos"] == d["arquivos"], f"fixture {nome}: caminho absoluto do H: mudou ao montar"
    assert item["grupo_whatsapp"] in fila_pc.GRUPOS_REAIS, f"fixture {nome}: grupo_whatsapp fora dos 6"
    assert fa.handle(item) == d["conta"] and fa.chave_token(item).startswith(("IG_", "TH_"))
    assert fa.inicio(item) == datetime.strptime(d["quando"], "%Y-%m-%d %H:%M")
    # vencido só 12 h depois da hora marcada
    assert fa.esta_vencido(item, fa.inicio(item)) is False
    assert fa.esta_vencido(item, fa.inicio(item) + timedelta(hours=13)) is True
    # grava onde o PC teria deixado e lê a confirmação
    sub = _subpasta(nome)
    fa.gravar_item(item, tmp_path, sub)
    conf = fa.ler_confirmacao(d["id"], tmp_path)
    if sub == "feitos":
        res = _campo(nome, d, "resultado", dict)
        assert conf["estado"] == "no_ar" and conf["link"] == _campo(nome, res, "permalink", str, True)
        assert conf["publicado_em"] == _campo(nome, res, "publicado_em", str, True)
        assert conf["media_id"] == _campo(nome, res, "media_id", str, True)
        assert _campo(nome, d, "status", str) == "no_ar"
    elif sub == "erros":
        assert conf["estado"] == "erro" and conf["erro"] == _campo(nome, d, "erro", str, True)
        assert conf["erro"].startswith("arquivo não existe: ")
    else:
        assert conf["estado"] == "pendente" and conf["pasta"] == (sub or "raiz")
    if sub == "story_clicavel":
        _campo(nome, d, "parqueado_em", str, True)
        assert _campo(nome, d, "origem_pasta", str) == "raiz"
    # item desconhecido e post de que depende
    assert fa.ler_confirmacao("nao_existe", tmp_path)["estado"] == "desconhecido"
    assert fa.post_que_falta(item, tmp_path) is None


def test_story_clicavel_espera_o_post_irmao(tmp_path):
    d = _json("fila_api_story_clicavel_parqueado.json")
    item = fa.montar_item(d["conta"], d["rede"], d["tipo"], d["arquivos"], d["legenda"], d["quando"],
                          canal=d["canal"], id_=d["id"], pasta_fila=tmp_path, existe=lambda p: True)
    irmao = d["id"].replace("_ig_story", "_ig_carrossel")
    assert fa.post_que_falta(item, tmp_path) is None                 # irmão não existe: story avulso
    escrever_json(tmp_path / f"{irmao}.json", {"id": irmao})         # irmão ainda na fila: espera
    assert fa.post_que_falta(item, tmp_path) == irmao
    (tmp_path / f"{irmao}.json").unlink()
    escrever_json(tmp_path / "feitos" / f"{irmao}.json", {"id": irmao, "status": "no_ar"})
    assert fa.post_que_falta(item, tmp_path) is None                 # irmão no ar: pode sair


def test_fila_api_rejeita_facebook_e_mensagens_do_validar():
    d = _json("fila_api_reel_pendente_gta.json")
    with pytest.raises(fa.ErroFilaApi, match="rede tem que ser instagram ou threads"):
        fa.montar_item(d["conta"], "facebook", d["tipo"], d["arquivos"], d["legenda"], d["quando"],
                       existe=lambda p: True)
    with pytest.raises(fa.ErroFilaApi, match="arquivo não existe: "):
        fa.montar_item(d["conta"], d["rede"], d["tipo"], d["arquivos"], d["legenda"], d["quando"],
                       existe=lambda p: False)


def test_limite_24h(tmp_path):
    nome = "fila_api_limite_24h.json"
    d = _json(nome)
    for chave, lista in d.items():
        assert re.match(r"^(IG|TH)_[a-z0-9.]+$", chave), f"fixture {nome} mudou de formato: chave {chave!r}"
        assert isinstance(lista, list), f"fixture {nome} mudou de formato: campo {chave} não é lista"
        for t in lista:
            datetime.strptime(t, "%Y-%m-%d %H:%M")
    escrever_json(tmp_path / fa.LIMITE_JSON, d)
    lido = fa.ler_limite_24h(tmp_path)
    assert lido == d
    agora = datetime(2026, 9, 30, 23, 30)
    assert fa.publicacoes_24h(lido, "IG_hp.futebol", agora) == 3
    assert fa.publicacoes_24h(lido, "TH_hp.carros", agora) == 2
    assert fa.publicacoes_24h(lido, "IG_hpgta6", agora) == 0
    assert not fa.no_limite(lido, "IG_hp.futebol", agora)
    assert fa.ler_limite_24h(tmp_path / "nao") == {}


def test_publicador_log():
    nome = "fila_api_publicador.log"
    eventos = fa.ler_log(PC_REAL / nome)
    assert [e["evento"] for e in eventos] == ["hospedado", "no_ar", "publicando", "no_ar", "invalido"], \
        f"fixture {nome} mudou de formato: sequência de eventos {[e['evento'] for e in eventos]}"
    assert eventos[0]["servico"] == "uguu" and eventos[0]["arquivo"] == "04.jpg"
    assert eventos[1]["id"] == "carros_2026-09-30_2315_novo-bmw-serie-3_th_carrossel"
    assert eventos[1]["link"].startswith("https://www.threads.com/@hp.carros/post/")
    assert eventos[2]["rede"] == "instagram" and eventos[2]["tipo"] == "feed" and eventos[2]["conta"] == "hp.futebol"
    assert eventos[2]["marcado"] == "2026-09-30 23:20"
    assert eventos[3]["link"] == "https://www.instagram.com/p/Dd70ZtCFSND/"
    assert eventos[4]["erro"].startswith("arquivo não existe: H:\\HypadoLocal\\canais\\carros")
    assert all(isinstance(e["quando"], datetime) for e in eventos)


# ================================================================ 4.5 config.json (trecho)
def test_config_trecho_criadores_autorizados_e_idioma():
    nome = "config_trecho.json"
    cfg = _json(nome)
    for campo in ("marca", "pastas", "video", "legenda", "dublagem", "transcricao", "estilo", "agendamento"):
        _campo(nome, cfg, campo, dict)
    streamers = _campo(nome, cfg, "streamers", list, True)
    for s in streamers:
        for campo in ("id", "nome", "credito", "autorizado"):
            _campo(nome, s, campo)
    assert pedido_pc.criador_autorizado(cfg, "davyjones")["credito"] == "@DavyJonesGTA6"
    assert pedido_pc.criador_autorizado(cfg, "tmartn2")["idioma"] == "en"
    assert pedido_pc.dublar_do_pedido({"streamer": "tmartn2"}, cfg) is True        # gringo: dubla
    assert pedido_pc.dublar_do_pedido({"streamer": "davyjones"}, cfg) is False
    assert pedido_pc.dublar_do_pedido({"streamer": "tmartn2", "dublar": False}, cfg) is False
    assert cp.dublar_por_padrao({"streamer": "tmartn2"}, cfg) is True
    with pytest.raises(pedido_pc.ErroParametro, match="não está no config.json"):
        pedido_pc.criador_autorizado(cfg, "ninguem")
    nao = dict(cfg)
    nao["streamers"] = [{**streamers[0], "autorizado": False}]
    with pytest.raises(pedido_pc.ErroParametro, match="autorizado"):
        pedido_pc.criador_autorizado(nao, streamers[0]["id"])
    # a marca do config.json bate com a marca única (rosa do post, laranja, noite, texto)
    m = cfg["marca"]
    assert m["cor_principal"] == marca.GTA_ROSA_POST and m["cor_clara"] == marca.GTA6["laranja"]
    assert m["cor_escura"] == marca.GTA6["noite"] and m["cor_texto"] == marca.GTA6["texto"]
    assert m["handle"] == marca.CANAIS["gta"]["handle"] and m["nome"] == marca.CANAIS["gta"]["nome"]
    assert Path(m["fonte_cartao"]).name in marca.ARQUIVOS_FONTE["Bauhaus 93"][0]
    assert cfg["legenda"]["fonte"] in marca.ARQUIVOS_FONTE
    assert cfg["agendamento"]["timezone"] == "America/Sao_Paulo"
    assert set(cfg["agendamento"]["redes"]) <= set(pedido_pc.REDES)


# ================================================================ 4.5 transcrição
def test_transcricao_todo_segmento_com_inicio_fim_texto_e_palavras():
    nome = "transcricao_exemplo.json"
    t = _json(nome)
    assert isinstance(_campo(nome, t, "duracao_seg"), (int, float))
    segs = _campo(nome, t, "segmentos", list, True)
    falas = []
    for i, s in enumerate(segs):
        for campo, tipo in (("inicio", (int, float)), ("fim", (int, float)), ("texto", str), ("palavras", list)):
            v = _campo(nome, s, campo)
            assert isinstance(v, tipo), f"fixture {nome} mudou de formato: segmentos[{i}].{campo}"
        assert s["inicio"] < s["fim"] <= t["duracao_seg"], f"fixture {nome}: segmentos[{i}] fora de ordem"
        for j, p in enumerate(s["palavras"]):
            for campo in ("inicio", "fim", "texto"):
                _campo(nome, p, campo)
            assert s["inicio"] <= p["inicio"] <= p["fim"] <= s["fim"], \
                f"fixture {nome}: segmentos[{i}].palavras[{j}] fora do segmento"
        falas.append(legendas.Fala(s["inicio"], s["fim"], s["texto"]))
    quebradas = legendas.quebrar_falas(falas, 42)
    assert len(quebradas) >= len(falas) and all(f.texto for f in quebradas)
    assert legendas.tempo_srt(falas[0].inicio) == "00:00:04,740"
    assert _campo(nome, t, "revisao", str)


# ================================================================ 4.5 plano do lote
def test_plano_corte_vira_pedido_e_argv_cortar(tmp_path):
    nome = "plano_corte_exemplo.json"
    item = _json(nome)
    for campo in ("n", "video", "streamer", "inicio", "fim", "gancho", "titulo", "legenda", "redes", "data",
                  "video_url", "corte", "cobrir", "arquivo", "upload", "status"):
        _campo(nome, item, campo)
    cfg = _json("config_trecho.json")
    pedido = cp.pedido_de_plano(item, cfg)
    assert pedido["tipo"] == "reel" and pedido["canal"] == "gta" and pedido["fonte_url"] == item["video_url"]
    assert pedido["corte"] == {"inicio": 6.08, "fim": 46.04} and pedido["credito"] == "@TGG_"
    assert pedido["narrar_toque_hp"] is True and pedido["horario_alvo"] == "2026-10-02T09:00"
    argvs = cp.argvs_do_pedido(pedido, cfg, bruto=tmp_path / "bruto.mp4", saida=tmp_path / "corte.mp4",
                               python="python.exe", scripts=tmp_path / "scripts")
    cortar = argvs["cortar"]
    esperado = cp.argv_cortar(tmp_path / "bruto_ed801.mkv", 6.08, 46.04, item["gancho"], "tgg",
                              tmp_path / "corte.mp4", transcricao=tmp_path / "bruto_ed801.json",
                              python="python.exe", scripts=tmp_path / "scripts")
    assert cortar == esperado, f"fixture {nome}: o argv do cortar.py mudou ({cortar})"
    assert cortar[1].endswith("cortar.py") and "--inicio" in cortar and "6.08" in cortar
    assert "--transcricao" in cortar and "--dublar" not in cortar      # tgg não está no config: não dubla
    assert argvs["baixar"][-1] == item["video_url"] and "*00:06:58.000-00:07:52.000" in argvs["baixar"]
    for proibido in ("--saida", "--srt", "--texto-arquivo", "--pedido"):
        assert proibido not in argvs["baixar"] + argvs["transcrever"]
    # o pedido do PC equivalente passa na validação (sem conferir criador) e é recusado com o config
    bruto = {**item, "tipo": "corte", "canal": "gta"}
    v = pedido_pc.validar_pc(bruto, cfg, conferir_criador=False)
    assert v["tipo"] == "corte" and v["data"] == "2026-10-02T09:00" and v["redes"] == ["youtube", "facebook"]
    with pytest.raises(pedido_pc.ErroParametro, match="tgg"):
        pedido_pc.validar_pc(bruto, cfg)                               # criador tgg não está autorizado


# ================================================================ 4.5 lote de estáticos
def test_lote_estaticos_pergunta_da_figurinha():
    nome = next(p.name for p in PC_REAL.glob("lote_estaticos_*.json"))
    lote = _json(nome)
    for campo in ("data", "carrossel", "stories", "interativo", "threads", "comunidade_youtube"):
        _campo(nome, lote, campo)
    for campo in ("arquivo", "rede", "horario", "figurinha", "pergunta", "opcoes", "destaque"):
        _campo(nome, lote["interativo"], campo)
    it = story_post_lote.ler_interativo(PC_REAL / nome)
    assert it["formato"] == "real" and it["figurinha"] == "enquete" and it["conta"] == "hpgta6"
    assert story_post_lote.pergunta_da_figurinha(it) == "O que você faz?"
    assert story_post_lote.opcoes_da_figurinha(it) == ["Vou ver de perto", "Fujo pro outro lado"]
    assert story_post_lote.pergunta_da_figurinha({**it, "pergunta_curta": "Vai jogar?"}) == "Vai jogar?"
    tipos = [i["tipo"] for i in story_post_lote.itens_do_lote(PC_REAL / nome)]
    assert sorted(tipos) == ["carrossel", "comunidade_youtube", "interativo", "story", "story", "threads"]


# ================================================================ 4.5/4.8 agendados -> aviso "no ar"
ESPERADO_FUTEBOL = (
    "*Claude - *🎬 *Novo post no ar — Futebol | HP!*\n"
    "*Jorge Jesus: \"Quem decide sou eu\" (treta com CR7)*\n"
    "\n"
    "Acabou de ser publicado nas nossas redes. Já está no ar nas redes abaixo 🚀\n"
    "\n"
    "📸 *Instagram:* https://www.instagram.com/p/Dd70ZtCFSND/"
)
ESPERADO_GTA = (
    "*Claude - *🎬 *Novo vídeo no ar!*\n"
    "*gta_2026-09-29_ig_story_1700*\n"
    "\n"
    "Acabou de ser publicado nas nossas redes. Já está no ar nas redes abaixo 🚀\n"
    "\n"
    "📸 *Instagram:* https://www.instagram.com/stories/hpgta6/3990000000000000002"
)


def test_agendados_exemplo_golden():
    nome = "agendados_exemplo.json"
    d = _json(nome)
    itens = _campo(nome, d, "itens", list, True)
    for i, it in enumerate(itens):
        for campo in ("id", "titulo", "data_post", "redes", "links", "status", "origem", "grupo_whatsapp", "tipo", "arquivo"):
            assert campo in it, f"fixture {nome} mudou de formato: itens[{i}].{campo} faltando"
        datetime.strptime(it["data_post"], "%Y-%m-%dT%H:%M")
        assert it["grupo_whatsapp"] in fila_pc.GRUPOS_REAIS
    lidos = fila_pc.ler_agendados(PC_REAL / nome)
    assert [fila_pc.montar_aviso_no_ar(i) for i in lidos] == [ESPERADO_FUTEBOL, ESPERADO_GTA]
    assert [i["canal"] for i in lidos] == ["futebol", "gta"]


# ================================================================ 4.8 fila do WhatsApp
def test_whatsapp_fila_real_ida_e_volta(tmp_path):
    nome = "whatsapp_fila_real.json"
    lista = _json(nome)
    assert isinstance(lista, list) and lista, f"fixture {nome} mudou de formato: não é lista"
    for i, m in enumerate(lista):
        for campo in ("grupo", "texto", "enviar_apos"):
            assert campo in m, f"fixture {nome} mudou de formato: [{i}].{campo} faltando"
        assert fila_pc.validar_mensagem_pc(m) == [], f"fixture {nome}: mensagem {i} inválida"
    fila = Fila(tmp_path / "fila")
    res = fila_pc.importar_fila_pc(PC_REAL / nome, fila, agora=datetime(2026, 9, 30, 10, 0, tzinfo=FUSO))
    assert [r["_situacao"] for r in res] == ["enfileirada"] * len(lista)
    volta = fila_pc.exportar_fila(fila)
    assert sorted(volta, key=lambda m: m["texto"]) == sorted(lista, key=lambda m: m["texto"])
    assert all(m["enviar_apos"] == "2026-09-29 07:30" for m in volta)


# ================================================================ 4.7 fila_story do celular
@pytest.mark.parametrize("nome", sorted(p.name for p in PC_REAL.glob("fila_story_pedido_real*.json")))
def test_fila_story_pedido_real(nome):
    d = _json(nome)
    for campo in ("post_id", "conta", "canal", "link", "publicado_em", "titulo", "destaque", "criado_em"):
        _campo(nome, d, campo)
    assert story_post.resolver_conta(story_post.CONFIG_PADRAO, d) == d["conta"]
    assert story_post.validar_link(d["link"]) == d["link"]
    pub = story_post._parse_dt(d["publicado_em"])                   # "AAAA-MM-DD HH:MM" sem fuso: Brasília
    assert pub == datetime.strptime(d["publicado_em"], "%Y-%m-%d %H:%M").replace(tzinfo=FUSO)
    assert pub.strftime("%Y-%m-%d %H:%M") == d["publicado_em"]
    assert d["post_id"].startswith(f"{d['canal']}_") and d["post_id"].endswith(("_ig_feed", "_ig_carrossel", "_ig_reel"))
    assert d["destaque"] is None or isinstance(d["destaque"], str)
    with pytest.raises(story_post.DadosInvalidos):
        story_post.validar_link("http://instagram.com/p/x")


# ================================================================ 4.7 dump do ui.py
def test_ui_dump_do_visualizador_de_story():
    nome = "ui_story_visualizador_hp_futebol.txt"
    texto = (PC_REAL / nome).read_text(encoding="utf-8")
    nos = ui_dump.ler_linhas_ui(texto)
    linhas = [l for l in texto.splitlines() if l.strip()]
    assert len(nos) == len(linhas), f"fixture {nome} mudou de formato: linha fora de 'x,y | classe | texto | desc | id | clic'"
    def no(id_):
        n = ui_dump.achar(nos, id=id_)
        assert n is not None, f"fixture {nome} mudou de formato: id {id_} sumiu"
        return n
    assert no("toolbar_highlights_button")["desc"] == "Highlight" and no("toolbar_highlights_button")["clicavel"]
    assert no("reel_viewer_timestamp")["texto"] == "3m"
    assert no("reel_viewer_title")["texto"] == "hp.futebol"
    assert no("reel_viewer_text_container")["desc"] == "hp.futebol's story, 3 minutes ago"
    assert no("self_toolbar_reshare_button_container")["desc"] == "Send story"
    assert re.match(r"^\d+m$", no("reel_viewer_timestamp")["texto"]) and int(no("reel_viewer_timestamp")["texto"][:-1]) <= 5


# ================================================================ 4.10 radar
def test_radar_gta_config_valida():
    nome = "radar_gta.json"
    d = _json(nome)
    problemas = esquema_radar.validar_config_radar(d)
    assert problemas == [], f"fixture {nome} mudou de formato: " + "; ".join(problemas)
    assert esquema_radar.conferir_config_radar(d, nome) is d
    assert esquema_radar.chaves_desconhecidas(d) == []
    assert d["canal"] == "gta" and d["youtube"][0]["channel_id"].startswith("UC")
    quebrada = dict(d)
    del quebrada["limiares"]
    with pytest.raises(esquema_radar.ConfigRadarInvalida, match="radar_gta.json mudou de formato: campo limiares"):
        esquema_radar.conferir_config_radar(quebrada, nome)
    flow = dict(d)
    flow["youtube"] = d["youtube"] + [{"nome": "Flow Games", "url": "https://www.youtube.com/@flowgames",
                                       "channel_id": "UC" + "x" * 22, "peso": 1, "oficial": False,
                                       "video_reutilizavel": False}]
    assert any("Flow Games" in m for m in esquema_radar.validar_config_radar(flow))
