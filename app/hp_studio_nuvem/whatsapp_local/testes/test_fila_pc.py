"""Testes do adaptador da fila real do PC (whatsapp_local/fila_pc.py) — §4.5 e §4.8.

Fixtures reais: tests/fixtures/pc_real/whatsapp_fila_real.json e agendados_exemplo.json.
Nenhum teste lê relógio real (agora= injetado), rede, navegador nem H:/G: de verdade
(a fixture autouse troca as raízes por pastas temporárias).
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from hpbase import FUSO, escrever_json, raiz_drive, raiz_local
from whatsapp_local import fila_pc
from whatsapp_local.config import (GRUPO_COMISSAO, GRUPOS_CANAIS, PREFIXO, Config, arquivo_fila_pc,
                                   arquivo_grupos, arquivos_agendados_pc, candidatos_agendados, nfc)
from whatsapp_local.enviador import Enviador
from whatsapp_local.fila import Fila
from whatsapp_local.montagem import carregar_agendados, posts_prontos
from whatsapp_local.navegador_falso import NavegadorFalso
from whatsapp_local.ritmo import RelogioFalso
from whatsapp_local.tarefas import enfileirar_no_ar, tarefas_automaticas
from whatsapp_local.validacao import validar_mensagem

PC_REAL = Path(__file__).resolve().parents[4] / "tests" / "fixtures" / "pc_real"
FILA_REAL = PC_REAL / "whatsapp_fila_real.json"
AGENDADOS_REAL = PC_REAL / "agendados_exemplo.json"
DIA = datetime(2026, 9, 30, 10, 0, tzinfo=FUSO)
MADRUGADA = datetime(2026, 9, 30, 3, 15, tzinfo=FUSO)

GRUPOS_6 = ["HP | Comissão 🚀", "HP | Futebol ⚽", "HP | Filmes 🎬", "HP | Receitas 🍔",
            "HP | Carros 🏎️", "HP | Destinos ✈️"]

# --- o texto esperado, literal (golden) para os 2 itens do agendados_exemplo.json ------------
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


def _fila_real() -> list[dict]:
    return json.loads(FILA_REAL.read_text(encoding="utf-8"))


# ================================================================ validação
def test_os_6_grupos_exatos_em_nfc():
    assert list(GRUPOS_CANAIS.values()) == GRUPOS_6
    for g in GRUPOS_6:
        assert fila_pc.grupo_valido(g)
        assert fila_pc.grupo_valido(g.replace("ã", "a\u0303"))      # NFD -> NFC: continua válido
    assert fila_pc.canal_do_grupo("HP | Futebol ⚽") == "futebol"
    assert fila_pc.canal_do_grupo(GRUPO_COMISSAO) == "gta"
    assert not fila_pc.grupo_valido("Hypado | Comissão 🟣")          # o antigo não recebe mais nada
    assert not fila_pc.grupo_valido("HP | Futebol")                  # sem o emoji não é o mesmo nome
    assert not fila_pc.grupo_valido(None)


def test_validar_mensagem_pc_prefixo_grupo_e_enviar_apos():
    ok = {"grupo": "HP | Comissão 🚀", "texto": "*Claude - *oi", "enviar_apos": "2026-09-29 07:30"}
    assert fila_pc.validar_mensagem_pc(ok) == []
    assert fila_pc.validar_mensagem_pc({**ok, "enviar_apos": None}) == []
    assert fila_pc.validar_mensagem_pc({**ok, "enviar_apos": ""}) == []
    assert any("*Claude - *" in m for m in fila_pc.validar_mensagem_pc({**ok, "texto": " *Claude - *oi"}))
    assert any("*Claude - *" in m for m in fila_pc.validar_mensagem_pc({**ok, "texto": "Claude - oi"}))
    assert any("vazio" in m for m in fila_pc.validar_mensagem_pc({**ok, "texto": "*Claude - *   "}))
    assert any("grupo" in m for m in fila_pc.validar_mensagem_pc({**ok, "grupo": "HP | GTA 6"}))
    assert any("sem grupo" in m for m in fila_pc.validar_mensagem_pc({**ok, "grupo": ""}))
    assert any("enviar_apos" in m for m in fila_pc.validar_mensagem_pc({**ok, "enviar_apos": "amanhã"}))
    assert fila_pc.validar_mensagem_pc("texto") == ["a mensagem não é um objeto JSON {…}"]
    # a fixture real passa inteira
    for m in _fila_real():
        assert fila_pc.validar_mensagem_pc(m) == []


def test_enviar_apos_formatos():
    assert fila_pc.ler_enviar_apos("2026-09-29 07:30") == datetime(2026, 9, 29, 7, 30)
    assert fila_pc.ler_enviar_apos("2026-09-29T07:30") == datetime(2026, 9, 29, 7, 30)
    assert fila_pc.ler_enviar_apos("2026-09-29 07:30:15") == datetime(2026, 9, 29, 7, 30)
    assert fila_pc.ler_enviar_apos(datetime(2026, 9, 29, 7, 30, tzinfo=FUSO)) == datetime(2026, 9, 29, 7, 30)
    assert fila_pc.ler_enviar_apos(None) is None and fila_pc.ler_enviar_apos("  ") is None
    with pytest.raises(ValueError):
        fila_pc.ler_enviar_apos("29/09/2026 07:30")
    assert fila_pc.texto_enviar_apos(datetime(2026, 9, 29, 7, 30)) == "2026-09-29 07:30"


# ================================================================ madrugada e enviar_apos
def test_madrugada_e_o_padrao_das_07h30():
    assert fila_pc.madrugada(datetime(2026, 9, 30, 0, 0)) is True
    assert fila_pc.madrugada(datetime(2026, 9, 30, 7, 29)) is True
    assert fila_pc.madrugada(datetime(2026, 9, 30, 7, 30)) is False
    assert fila_pc.madrugada(datetime(2026, 9, 30, 23, 59)) is False
    assert fila_pc.madrugada(MADRUGADA) is True                   # com fuso também
    assert fila_pc.enviar_apos_padrao(MADRUGADA) == "2026-09-30 07:30"
    assert fila_pc.enviar_apos_padrao(DIA) is None


def test_mensagem_de_madrugada_sem_enviar_apos_ganha_07h30_do_mesmo_dia():
    msg = {"grupo": "HP | Receitas 🍔", "texto": "*Claude - *📊 Resumo de terça, 29/09"}
    d = fila_pc.para_pasta(msg, MADRUGADA)
    assert d["enviar_apos"] == "2026-09-30 07:30"
    assert d["tipo"] == "resumo_dia" and d["criado_em"].startswith("2026-09-30T03:15:00")
    assert d["grupo"] == "HP | Receitas 🍔" and d["anexos"] == [] and d["origem"] == "whatsapp_fila.json"
    # de dia, sem enviar_apos, fica None (pode sair já); enviar_apos dado é preservado tal qual
    assert fila_pc.para_pasta(msg, DIA)["enviar_apos"] is None
    assert fila_pc.para_pasta({**msg, "enviar_apos": "2026-10-01 09:00"}, MADRUGADA)["enviar_apos"] == "2026-10-01 09:00"


def test_pronta_para_enviar_respeita_enviar_apos_e_madrugada():
    msg = {"enviar_apos": "2026-09-30 07:30"}
    assert fila_pc.pronta_para_enviar(msg, datetime(2026, 9, 30, 7, 29)) is False
    assert fila_pc.pronta_para_enviar(msg, datetime(2026, 9, 30, 7, 30)) is True
    assert fila_pc.pronta_para_enviar(msg, datetime(2026, 9, 30, 7, 30, tzinfo=FUSO)) is True
    assert fila_pc.pronta_para_enviar({}, DIA) is True                       # sem enviar_apos = já
    assert fila_pc.pronta_para_enviar({}, MADRUGADA) is False                # madrugada: nada sai
    assert fila_pc.pronta_para_enviar({}, MADRUGADA, bloquear_madrugada=False) is True
    assert fila_pc.pronta_para_enviar({"enviar_apos": "xx"}, DIA) is False   # inválido nunca sai
    # a fixture real (enviar_apos 29/09 07:30) já pode sair no dia 30 às 10h
    assert all(fila_pc.pronta_para_enviar(m, DIA) for m in _fila_real())


# ================================================================ ida e volta
def test_id_deterministico():
    a = fila_pc.id_mensagem_pc("HP | Comissão 🚀", "*Claude - *oi", "2026-09-29 07:30")
    b = fila_pc.id_mensagem_pc("HP | Comissa\u0303o 🚀", "*Claude - *oi", "2026-09-29 07:30")
    assert a == b and a.startswith("pc_") and len(a) == 19
    assert a != fila_pc.id_mensagem_pc("HP | Comissão 🚀", "*Claude - *oi", "2026-09-29 07:31")
    assert a != fila_pc.id_mensagem_pc("HP | Comissão 🚀", "*Claude - *oi!", "2026-09-29 07:30")
    assert a != fila_pc.id_mensagem_pc("HP | Carros 🏎️", "*Claude - *oi", "2026-09-29 07:30")


def test_ida_e_volta_da_fixture_real_sem_perder_enviar_apos(tmp_path):
    fila = Fila(tmp_path / "fila")
    original = _fila_real()
    res = fila_pc.importar_fila_pc(FILA_REAL, fila, agora=DIA)
    assert [m["_situacao"] for m in res] == ["enfileirada", "enfileirada"]
    arquivos = sorted(p.name for p in (tmp_path / "fila").glob("*.json"))
    assert len(arquivos) == 2 and all(n.startswith("pc_") for n in arquivos)
    for p in (tmp_path / "fila").glob("*.json"):
        d = json.loads(p.read_text(encoding="utf-8"))
        assert d["enviar_apos"] == "2026-09-29 07:30" and d["texto"].startswith(PREFIXO)
        assert set(d) >= {"id", "grupo", "texto", "anexos", "tipo", "criado_em", "enviar_apos"}
    # volta: pasta -> lista do PC, igual à original (grupo, texto, enviar_apos)
    volta = fila_pc.exportar_fila(fila)
    assert sorted(volta, key=lambda m: m["texto"]) == sorted(original, key=lambda m: m["texto"])
    saida = fila_pc.exportar_para_pc(tmp_path / "whatsapp_fila.json", fila)
    assert json.loads(saida.read_text(encoding="utf-8")) == volta
    assert not list(tmp_path.glob(".tmp_*"))                       # gravação atômica, sem resto


def test_importar_duas_vezes_nao_duplica_e_rejeita_invalida(tmp_path):
    fila = Fila(tmp_path / "fila")
    lista = _fila_real() + [{"grupo": "Hypado | Comissão 🟣", "texto": "*Claude - *x", "enviar_apos": None},
                            {"grupo": "HP | Carros 🏎️", "texto": "sem prefixo", "enviar_apos": None}]
    arq = tmp_path / "whatsapp_fila.json"
    escrever_json(arq, lista)
    res = fila_pc.importar_fila_pc(arq, fila, agora=DIA)
    assert [m["_situacao"].split(":")[0] for m in res] == ["enfileirada", "enfileirada", "rejeitada", "rejeitada"]
    assert "não é um dos 6 grupos" in res[2]["_situacao"] and "*Claude - *" in res[3]["_situacao"]
    assert len(list((tmp_path / "fila" / "rejeitadas").glob("*.json"))) == 2
    de_novo = fila_pc.importar_fila_pc(arq, fila, agora=DIA)
    assert [m["_situacao"] for m in de_novo[:2]] == ["já existia", "já existia"]
    assert len(list((tmp_path / "fila").glob("*.json"))) == 2
    # só mostrar não grava nada; limpar esvazia o arquivo do PC
    assert all(m["_situacao"] == "só mostrar" for m in fila_pc.importar_fila_pc(FILA_REAL, Fila(tmp_path / "f2"), agora=DIA, so_mostrar=True))
    assert not (tmp_path / "f2").exists()
    fila_pc.importar_fila_pc(arq, fila, agora=DIA, limpar=True)
    assert json.loads(arq.read_text(encoding="utf-8")) == []
    with pytest.raises(ValueError):
        fila_pc.importar_fila_pc(arq, fila)                          # agora é obrigatório


def test_ler_fila_pc_tolerante_e_caminho_padrao():
    assert fila_pc.ler_fila_pc(Path("nao_existe.json")) == []
    assert arquivo_fila_pc() == raiz_local() / "temp" / "whatsapp_fila.json"
    escrever_json(arquivo_fila_pc(), {"fila": [{"grupo": "x", "texto": "y"}, "lixo"]})
    assert fila_pc.ler_fila_pc() == [{"grupo": "x", "texto": "y"}]
    escrever_json(arquivo_fila_pc(), [])
    assert fila_pc.ler_fila_pc() == []
    assert fila_pc.tipo_da_mensagem("*Claude - *🚀 No ar agora") == "no_ar"
    assert fila_pc.tipo_da_mensagem("*Claude - *🗓️ Resumo da semana") == "resumo_sabado"
    assert fila_pc.tipo_da_mensagem("*Claude - *📊 Resumo de terça") == "resumo_dia"
    assert fila_pc.tipo_da_mensagem("*Claude - *📌 Pinterest pronto") == fila_pc.TIPO_PADRAO


def test_enviador_adia_enviar_apos_futuro_e_madrugada(tmp_path):
    """A mensagem com enviar_apos no futuro fica na fila (adiada), não é rejeitada nem enviada."""
    escrever_json(arquivo_grupos(), {"grupos": GRUPOS_6})
    relogio = RelogioFalso(datetime(2026, 9, 30, 7, 0, tzinfo=FUSO))     # madrugada
    fila = Fila()
    fila.enfileirar(fila_pc.para_pasta({"grupo": "HP | Futebol ⚽", "texto": "*Claude - *🚀 No ar agora"},
                                       relogio.agora()))
    pendente = fila.pendentes()[0].dados
    assert pendente["enviar_apos"] == "2026-09-30 07:30"
    nav = NavegadorFalso({"HP | Futebol ⚽": []})
    env = Enviador(Config(modo="real", ler_recebidas=False), fabrica_navegador=lambda cfg, visivel=False: nav,
                   relogio=relogio)
    res = env.ciclo()
    assert res.adiadas == 1 and res.enviadas == 0 and res.rejeitadas == 0
    assert len(fila.pendentes()) == 1
    relogio.avancar(minutes=31)                                            # 07:31
    res = env.ciclo()
    assert res.enviadas == 1 and res.adiadas == 0 and len(fila.pendentes()) == 0
    assert nav.enviadas and nav.enviadas[0]["grupo"] == "HP | Futebol ⚽"
    # enviar_apos inválido é rejeitado com motivo claro
    fila.enfileirar({**pendente, "id": "ruim", "enviar_apos": "amanhã"})
    res = env.ciclo()
    assert res.rejeitadas == 1
    motivo = json.loads(next(fila.rejeitadas.glob("ruim*.json")).read_text(encoding="utf-8"))["motivo_rejeicao"]
    assert "enviar_apos inválido" in motivo


# ================================================================ agendados.json real
def test_os_6_lugares_do_agendados():
    d = raiz_drive()
    assert arquivos_agendados_pc() == [
        d / "06 Projeto" / "agendados.json",
        d / "07 Canais" / "Futebol" / "agendados.json",
        d / "07 Canais" / "Filmes e Series" / "agendados.json",
        d / "07 Canais" / "Gastronomia" / "agendados.json",
        d / "07 Canais" / "Carros" / "agendados.json",
        d / "07 Canais" / "Viagens" / "agendados.json",
    ]
    assert candidatos_agendados()[:6] == arquivos_agendados_pc()
    assert len(candidatos_agendados()) == len(set(candidatos_agendados()))


def test_ler_agendados_real_e_todos_os_lugares(tmp_path):
    itens = fila_pc.ler_agendados(AGENDADOS_REAL)
    assert [i["id"] for i in itens] == ["futebol_2026-09-30_2320_jj-quem-decide_ig_feed", "gta_2026-09-29_ig_story_1700"]
    assert [i["canal"] for i in itens] == ["futebol", "gta"]
    assert itens[0]["grupo_whatsapp"] == "HP | Futebol ⚽" and itens[0]["arquivo_agendados"] == str(AGENDADOS_REAL)
    assert fila_pc.ler_agendados(tmp_path / "nao_existe.json") == []
    (tmp_path / "quebrado.json").write_text("{itens: ", encoding="utf-8")
    assert fila_pc.ler_agendados(tmp_path / "quebrado.json") == []
    # os 6 lugares: GTA em 06 Projeto, canais em 07 Canais\<Pasta>; só os que existem entram
    alvos = arquivos_agendados_pc()
    escrever_json(alvos[0], {"itens": [{"id": "gta_2026-09-30_ig_reel_1200", "titulo": "t", "redes": ["instagram"],
                                        "links": {"instagram": "https://www.instagram.com/p/A/"}, "status": "no_ar",
                                        "data_post": "2026-09-30T12:00"}]})
    escrever_json(alvos[4], {"itens": [{"id": "carros_2026-09-30_1500_x_ig_feed", "titulo": "c", "redes": ["instagram"],
                                        "links": {"instagram": "https://www.instagram.com/p/B/"}, "status": "no_ar",
                                        "data_post": "2026-09-30T15:00", "grupo_whatsapp": "HP | Carros 🏎️"}]})
    todos = fila_pc.ler_agendados_todos()
    assert [(i["canal"], i["id"]) for i in todos] == [("gta", "gta_2026-09-30_ig_reel_1200"),
                                                      ("carros", "carros_2026-09-30_1500_x_ig_feed")]


def test_canal_do_item_por_id_grupo_conta_ou_campo():
    assert fila_pc.canal_do_item({"id": "filmes_2026-09-30_1200_x_ig_feed"}) == "filmes"
    assert fila_pc.canal_do_item({"grupo_whatsapp": "HP | Destinos ✈️"}) == "destinos"
    assert fila_pc.canal_do_item({"conta": "@hp.receitas"}) == "receitas"
    assert fila_pc.canal_do_item({"canal": "carros"}) == "carros"
    assert fila_pc.canal_do_item({"id": "x"}) is None
    assert fila_pc.grupo_do_item({"id": "futebol_x"}) == "HP | Futebol ⚽"
    assert fila_pc.grupo_do_item({"id": "x"}) == GRUPO_COMISSAO
    assert fila_pc.grupo_do_item({"grupo_whatsapp": "HP | Carros 🏎️"}) == "HP | Carros 🏎️"


def test_avisos_enviados_tolera_lista_embrulhada(tmp_path):
    p = tmp_path / "avisos_enviados.json"
    escrever_json(p, ["frase_feed.jpg", "1700_contagem.jpg"])
    assert fila_pc.ler_avisos_enviados(p) == ["frase_feed.jpg", "1700_contagem.jpg"]
    escrever_json(p, [{"value": ["a.jpg", "b.jpg"], "Count": 2}])
    assert fila_pc.ler_avisos_enviados(p) == ["a.jpg", "b.jpg"]
    escrever_json(p, {"value": ["c.jpg"], "Count": 1})
    assert fila_pc.ler_avisos_enviados(p) == ["c.jpg"]
    escrever_json(p, [{"value": ["a.jpg"], "Count": 1}, "b.jpg", "a.jpg"])
    assert fila_pc.ler_avisos_enviados(p) == ["a.jpg", "b.jpg"]
    assert fila_pc.ler_avisos_enviados(tmp_path / "nao.json") == []
    # gravar devolve a lista lisa; marcar não repete
    item = {"id": "x", "arquivo": "H:\\HypadoLocal\\x\\frase_feed.jpg"}
    assert fila_pc.chave_do_aviso(item) == "frase_feed.jpg"
    escrever_json(p, [{"value": ["a.jpg"], "Count": 1}])
    assert fila_pc.marcar_avisado(item, p) == ["a.jpg", "frase_feed.jpg"]
    assert fila_pc.marcar_avisado(item, p) == ["a.jpg", "frase_feed.jpg"]
    assert json.loads(p.read_text(encoding="utf-8")) == ["a.jpg", "frase_feed.jpg"]
    assert fila_pc.ja_avisado(item, ["frase_feed.jpg"]) and fila_pc.ja_avisado({"id": "y"}, ["y"])
    assert not fila_pc.ja_avisado(item, ["outro.jpg"])
    assert fila_pc.arquivo_avisos_enviados() == raiz_drive() / "06 Projeto" / "avisos_enviados.json"


def test_itens_para_avisar_pula_avisados_cancelados_e_sem_link():
    itens = fila_pc.ler_agendados(AGENDADOS_REAL)
    assert [i["id"] for i in fila_pc.itens_para_avisar(itens, [])] == [i["id"] for i in itens]
    assert [i["id"] for i in fila_pc.itens_para_avisar(itens, ["frase_feed.jpg"])] == ["gta_2026-09-29_ig_story_1700"]
    extra = [{"id": "a", "status": "erro", "links": {"instagram": "u"}}, {"id": "b", "status": "no_ar", "links": {}}]
    assert fila_pc.itens_para_avisar(extra, []) == []


# ================================================================ aviso "no ar" literal (§4.8)
def test_golden_agendados_exemplo_vira_exatamente_o_texto_esperado():
    itens = fila_pc.ler_agendados(AGENDADOS_REAL)
    assert fila_pc.montar_aviso_no_ar(itens[0]) == ESPERADO_FUTEBOL
    assert fila_pc.montar_aviso_no_ar(itens[1]) == ESPERADO_GTA
    # e pelo caminho do montagem (carregar_agendados -> post normalizado) sai o mesmo texto
    posts = carregar_agendados(AGENDADOS_REAL)
    assert [p["formato"] for p in posts] == ["pc", "pc"]
    assert fila_pc.montar_aviso_no_ar(posts[0]) == ESPERADO_FUTEBOL
    assert fila_pc.montar_aviso_no_ar(posts[1]) == ESPERADO_GTA
    for texto in (ESPERADO_FUTEBOL, ESPERADO_GTA):
        assert texto.startswith("*Claude - *🎬") and "\n\n" in texto and not texto.endswith("\n")


def test_aviso_ordem_das_redes_e_links_de_youtube_e_tiktok():
    item = {"id": "gta_2026-10-02_ig_reel_1200", "titulo": "A Rockstar mandou um presente",
            "redes": ["threads", "youtube", "tiktok", "facebook", "instagram"],
            "links": {"instagram": "https://www.instagram.com/reel/X/", "threads": "https://www.threads.com/@hpgta6/post/Y",
                      "youtube": "abc123DEF45", "tiktok": "7300000000000000001",
                      "facebook": "https://www.facebook.com/hpgta6/videos/1"}}
    t = fila_pc.montar_aviso_no_ar(item)
    linhas = t.split("\n")
    assert linhas[0] == "*Claude - *🎬 *Novo vídeo no ar!*" and linhas[1] == "*A Rockstar mandou um presente*"
    assert linhas[2] == "" and linhas[3] == fila_pc.CORPO_AVISO and linhas[4] == ""
    assert linhas[5:] == [
        "📸 *Instagram:* https://www.instagram.com/reel/X/",
        "📘 *Facebook:* https://www.facebook.com/hpgta6/videos/1",
        "🎵 *TikTok:* https://www.tiktok.com/@hpgta6/video/7300000000000000001",
        "▶️ *YouTube:* https://youtube.com/shorts/abc123DEF45",
        "🧵 *Threads:* https://www.threads.com/@hpgta6/post/Y",
    ]
    # URL pronta do YouTube/TikTok fica como veio; id em `ids` também vale
    assert fila_pc.link_da_rede({"links": {"youtube": "https://youtube.com/shorts/Q"}}, "youtube") == "https://youtube.com/shorts/Q"
    assert fila_pc.link_da_rede({"id": "carros_x", "ids": {"tiktok": "9"}}, "tt") == "https://www.tiktok.com/@hp.carros/video/9"


def test_aviso_so_redes_com_link_e_perfil_quando_falta():
    # a rede está em redes[] mas não tem link: usa o perfil e NÃO atrasa; rede fora de redes[] não aparece
    item = {"id": "futebol_x", "titulo": "Gol", "redes": ["instagram", "youtube"],
            "links": {"instagram": "https://www.instagram.com/p/A/", "threads": "https://www.threads.com/@hp.futebol/post/B"}}
    t = fila_pc.montar_aviso_no_ar(item)
    assert "📸 *Instagram:* https://www.instagram.com/p/A/" in t
    assert "▶️ *YouTube:* https://www.youtube.com/@hp.futebol" in t
    assert "Threads" not in t and t.count("\n") == 6
    assert t.split("\n")[0] == "*Claude - *🎬 *Novo post no ar — Futebol | HP!*"
    # nome_canal explícito manda no cabeçalho; sem redes[] valem as redes com link
    t2 = fila_pc.montar_aviso_no_ar({"titulo": "x", "links": {"tiktok": "https://t/1"}}, nome_canal="Receitas | HP")
    assert t2.split("\n")[0] == "*Claude - *🎬 *Novo post no ar — Receitas | HP!*"
    assert t2.split("\n")[-1] == "🎵 *TikTok:* https://t/1"
    assert fila_pc.montar_aviso_no_ar({"titulo": "x", "redes": [], "links": {}}).split("\n")[-1] == ""


def test_mensagem_no_ar_vai_para_o_grupo_do_item_com_id_fixo_e_passa_na_validacao_dura():
    escrever_json(arquivo_grupos(), {"grupos": GRUPOS_6})
    itens = fila_pc.ler_agendados(AGENDADOS_REAL)
    m = fila_pc.mensagem_no_ar(itens[0], MADRUGADA)
    assert m["grupo"] == "HP | Futebol ⚽" and m["tipo"] == "no_ar"
    assert m["id"] == "no_ar_futebol_2026-09-30_2320_jj-quem-decide_ig_feed"
    assert m["texto"] == ESPERADO_FUTEBOL and m["enviar_apos"] == "2026-09-30 07:30"
    assert m["origem"] == str(AGENDADOS_REAL)
    assert fila_pc.mensagem_no_ar(itens[0], DIA)["id"] == m["id"]      # determinístico
    from whatsapp_local.config import carregar_grupos_permitidos
    assert validar_mensagem(m, carregar_grupos_permitidos()) == []
    g = fila_pc.mensagem_no_ar(itens[1], DIA)
    assert g["grupo"] == GRUPO_COMISSAO and g["enviar_apos"] is None and g["texto"] == ESPERADO_GTA


# ================================================================ integração com o vigia
def test_vigia_le_os_6_lugares_e_monta_o_texto_literal():
    escrever_json(arquivo_grupos(), {"grupos": GRUPOS_6})
    alvos = arquivos_agendados_pc()
    escrever_json(alvos[1], json.loads(AGENDADOS_REAL.read_text(encoding="utf-8")))   # 07 Canais\Futebol
    escrever_json(alvos[5], {"itens": [{"id": "destinos_2026-09-30_0900_jeri_ig_carrossel", "titulo": "Jeri em 4 dias",
                                        "data_post": "2026-09-30T09:00", "redes": ["instagram"],
                                        "links": {"instagram": "https://www.instagram.com/p/J/"}, "status": "no_ar",
                                        "grupo_whatsapp": "HP | Destinos ✈️", "tipo": "carrossel", "arquivo": "01.jpg"}]})
    agora = datetime(2026, 9, 30, 23, 30, tzinfo=FUSO)
    cfg = Config(janela_no_ar_horas=48)                         # o story do GTA é de 29/09 16:58
    fila = Fila()
    assert tarefas_automaticas(cfg, agora, fila) == 3            # 2 do Futebol + 1 do Destinos
    assert tarefas_automaticas(cfg, agora, fila) == 0            # não duplica
    assert tarefas_automaticas(Config(), agora, Fila(raiz_local() / "outra_fila")) == 2   # janela de 24 h pula o de 29/09
    por_grupo = {}
    for i in fila.pendentes():
        por_grupo.setdefault(i.dados["grupo"], []).append(i.dados)
    assert set(por_grupo) == {"HP | Futebol ⚽", GRUPO_COMISSAO, "HP | Destinos ✈️"}
    assert por_grupo["HP | Futebol ⚽"][0]["texto"] == ESPERADO_FUTEBOL
    assert por_grupo[GRUPO_COMISSAO][0]["texto"] == ESPERADO_GTA
    assert por_grupo["HP | Destinos ✈️"][0]["texto"].startswith("*Claude - *🎬 *Novo post no ar — Destinos | HP!*\n*Jeri em 4 dias*")
    assert all(d.get("enviar_apos") is None for ds in por_grupo.values() for d in ds)
    # com caminho explícito só aquele arquivo vale; o formato antigo (rodada 1) continua pelo modelo
    msgs = enfileirar_no_ar(alvos[1], cfg, agora, so_mostrar=True)
    assert [m["grupo"] for m in msgs] == [GRUPO_COMISSAO, "HP | Futebol ⚽"]   # ordem pelo horário
    posts = posts_prontos(carregar_agendados(alvos[1]), agora, 48)
    assert [p["canal"] for p in posts] == ["GTA 6 | HP", "Futebol | HP"]


def test_cli_do_fila_pc(tmp_path, capsys):
    escrever_json(arquivo_fila_pc(), _fila_real())
    assert fila_pc.main(["importar", "--agora", "2026-09-30 10:00", "--so-mostrar"]) == 0
    out = capsys.readouterr().out
    assert out.count("só mostrar") == 2 and "2 mensagem(ns)" in out and "FAKE" not in out
    assert fila_pc.main(["importar", "--agora", "2026-09-30 10:00"]) == 0
    assert capsys.readouterr().out.count("enfileirada") == 2
    assert fila_pc.main(["exportar"]) == 0
    assert len(json.loads(capsys.readouterr().out)) == 2
    assert fila_pc.main(["exportar", "--arquivo", str(tmp_path / "x.json")]) == 0
    assert len(json.loads((tmp_path / "x.json").read_text(encoding="utf-8"))) == 2
    with pytest.raises(SystemExit):
        fila_pc.main(["importar"])                                  # sem --agora não roda
    escrever_json(arquivos_agendados_pc()[0], json.loads(AGENDADOS_REAL.read_text(encoding="utf-8")))
    assert fila_pc.main(["agendados"]) == 0 and "futebol" in capsys.readouterr().out
    assert fila_pc.main(["avisos", "--agora", "2026-09-30 10:00"]) == 0
    assert ESPERADO_GTA in capsys.readouterr().out
