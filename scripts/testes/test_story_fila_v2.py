# -*- coding: utf-8 -*-
"""Testes do story_fila_v2.py (esquema v2 da fila_story): sem rede, sem adb, sem relógio real.
Usa as fixtures reais do PC: fila_story_pedido_real.json, fila_story_pedido_real_carrossel.json e
lote_estaticos_2026-10-01.json. Rodar: cd scripts && python -m pytest -q testes/test_story_fila_v2.py
"""
from __future__ import annotations

import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
for _p in (AQUI.parent, AQUI.parent.parent / "app" / "hp_studio_nuvem"):
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import story_fila_v2 as fv  # noqa: E402
from hpbase import FUSO, ler_json  # noqa: E402

PC_REAL = AQUI.parent.parent / "tests" / "fixtures" / "pc_real"
AGORA = datetime(2026, 10, 1, 7, 30, tzinfo=FUSO)
LINK = "https://www.instagram.com/p/Dd7J4uso3bI/"


@pytest.fixture(autouse=True)
def _raizes(tmp_path, monkeypatch):
    local, drive = tmp_path / "HypadoLocal", tmp_path / "Drive"
    local.mkdir(exist_ok=True)
    drive.mkdir(exist_ok=True)
    monkeypatch.setenv("HP_LOCAL", str(local))
    monkeypatch.setenv("HP_DRIVE", str(drive))


@pytest.fixture
def real():
    return ler_json(PC_REAL / "fila_story_pedido_real.json")


@pytest.fixture
def lote():
    return ler_json(PC_REAL / "lote_estaticos_2026-10-01.json")


def exemplo_v2() -> dict:
    """O JSON do enunciado da tarefa E3."""
    return {
        "post_id": "carros_2026-09-30_2315_novo-bmw-serie-3_ig_carrossel", "conta": "hp.carros", "canal": "carros",
        "link": "https://www.instagram.com/p/Dd7ytwrlQye/", "publicado_em": "2026-09-30 23:03",
        "titulo": "O novo BMW Série 3 chegou", "destaque": None, "criado_em": "2026-09-30 23:11",
        "stories": [
            {"quando": "2026-10-01 09:40", "tipo": "chamada_post", "arte": "H:\\HypadoLocal\\stories\\story_chamada.jpg",
             "zonas": "H:\\HypadoLocal\\stories\\story_chamada_zonas.json", "texto": "Toque pra ver",
             "figurinha": {"tipo": "link", "url": "https://www.instagram.com/p/Dd7ytwrlQye/", "rotulo": "Ver post",
                           "opcoes": None},
             "pergunta_publico": None, "destaque": None},
            {"quando": "2026-10-01 16:00", "tipo": "enquete", "arte": "H:\\HypadoLocal\\stories\\story_enquete.jpg",
             "zonas": None, "texto": "Furacão chegando em Leonida. O que você faz?",
             "figurinha": {"tipo": "enquete", "url": None, "rotulo": None, "opcoes": ["Vou ver de perto", "Fujo pro outro lado"]},
             "pergunta_publico": "O que você faz?", "destaque": "Enquetes"},
        ],
    }


def motivos(func, *a, **kw) -> list:
    with pytest.raises(fv.FilaInvalida) as e:
        func(*a, **kw)
    return e.value.motivos


# ===========================================================================
# validar_v2
# ===========================================================================
def test_exemplo_do_enunciado_e_valido_e_normalizado():
    out = fv.validar_v2(exemplo_v2())
    assert out["versao"] == 2 and out["conta"] == "hp.carros" and len(out["stories"]) == 2
    s0, s1 = out["stories"]
    assert s0["quando"] == "2026-10-01 09:40" and s0["figurinha"]["tipo"] == "link" and s0["figurinha"]["rotulo"] == "Ver post"
    assert s1["zonas"] == "H:\\HypadoLocal\\stories\\story_enquete_zonas.json"      # zonas derivadas da arte
    assert s1["figurinha"]["opcoes"] == ["Vou ver de perto", "Fujo pro outro lado"] and s1["pergunta_publico"] == "O que você faz?"


def test_pedido_v1_real_nao_passa_sem_migrar(real):
    m = motivos(fv.validar_v2, real)
    assert any("stories" in x and "migrar_v1" in x for x in m)


def test_validar_recusa_com_mensagens_em_portugues_e_indice():
    d = exemplo_v2()
    d["stories"][0]["tipo"] = "reels"
    d["stories"][1]["quando"] = "amanhã"
    longa = "Furacão chegando em Leonida, o que você faz agora?"
    d["stories"][1]["pergunta_publico"] = longa
    d["destaque"] = 5
    m = motivos(fv.validar_v2, d)
    assert len(m) >= 4
    assert any(x.startswith("stories[0]: tipo 'reels' não existe") and "compartilhar_post" in x for x in m)
    assert any(x.startswith("stories[1]: 'quando' inválido") for x in m)
    assert any(f"stories[1]: 'pergunta_publico' tem {len(longa)} caracteres (máximo 25)" in x for x in m)
    assert any("'destaque' precisa ser texto" in x for x in m)
    assert fv.validar_v2(d if False else exemplo_v2(), limite_pergunta=60)   # o limite é configurável (A4)
    d = exemplo_v2()
    d["stories"][1]["pergunta_publico"] = "Furacão chegando em Leonida. O que você faz?"
    assert fv.validar_v2(d, limite_pergunta=60)["stories"][1]["pergunta_publico"].endswith("faz?")


def test_validar_figurinhas():
    d = exemplo_v2()
    d["stories"][0]["figurinha"] = {"tipo": "balao"}
    assert any("figurinha 'balao' não existe" in x for x in motivos(fv.validar_v2, d))
    d = exemplo_v2()
    d["stories"][0]["figurinha"] = {"tipo": "link"}                 # sem url: usa o link do pedido
    assert fv.validar_v2(d)["stories"][0]["figurinha"]["url"] == "https://www.instagram.com/p/Dd7ytwrlQye/"
    d["link"] = None
    assert any("precisa de 'url'" in x for x in motivos(fv.validar_v2, d))
    d = exemplo_v2()
    d["stories"][1]["figurinha"]["opcoes"] = ["Só uma"]
    assert any("2 a 4 opções" in x for x in motivos(fv.validar_v2, d))
    d["stories"][1]["figurinha"]["opcoes"] = ["a", "b", "c", "d", "e"]
    assert any("2 a 4 opções" in x for x in motivos(fv.validar_v2, d))
    longa = "Vou ver de perto com os meus amigos"
    d["stories"][1]["figurinha"]["opcoes"] = [longa, "Fujo"]
    assert any(f"opção 1 da enquete tem {len(longa)} caracteres (máximo 25)" in x for x in motivos(fv.validar_v2, d))
    d["stories"][1]["figurinha"] = None
    assert any("precisa de figurinha enquete" in x for x in motivos(fv.validar_v2, d))
    d = exemplo_v2()
    d["stories"][1]["pergunta_publico"] = ""
    assert any("precisa de 'pergunta_publico'" in x for x in motivos(fv.validar_v2, d))


def test_validar_tipos_contagem_compartilhar_e_arte():
    d = exemplo_v2()
    d["stories"] = [{"quando": "2026-10-01 09:00", "tipo": "contagem", "arte": "H:\\a.jpg",
                     "figurinha": {"tipo": "contagem", "rotulo": "Lançamento do GTA 6"}}]
    assert any("precisa de 'data'" in x for x in motivos(fv.validar_v2, d))
    d["stories"][0]["figurinha"]["data"] = "2026-11-19"
    assert fv.validar_v2(d)["stories"][0]["figurinha"]["data"] == "2026-11-19"
    d["stories"] = [{"quando": "2026-10-01 12:10", "tipo": "compartilhar_post"}]
    d["link"] = None
    assert any("falta o link do post" in x for x in motivos(fv.validar_v2, d))
    d["stories"][0]["link"] = LINK
    assert fv.validar_v2(d)["stories"][0]["link"] == LINK
    d["stories"] = [{"quando": "2026-10-01 12:10", "tipo": "mais_sobre"}]
    assert any("precisa de 'arte'" in x for x in motivos(fv.validar_v2, d))
    d["stories"] = [{"quando": "2026-10-01 12:10", "tipo": "interacao", "arte": "H:\\a.jpg",
                     "figurinha": {"tipo": "link", "url": LINK}}]
    assert any("story de interação leva figurinha" in x for x in motivos(fv.validar_v2, d))


def test_validar_campos_do_pedido_e_lista_vazia():
    assert "o pedido precisa ser um objeto JSON" in motivos(fv.validar_v2, [1, 2])
    d = exemplo_v2()
    d["stories"] = []
    assert "'stories' está vazio: nada para fazer" in motivos(fv.validar_v2, d)
    d = exemplo_v2()
    del d["post_id"]
    d["link"] = "instagram.com/p/x"
    d["criado_em"] = "ontem"
    m = motivos(fv.validar_v2, d)
    assert "falta o campo 'post_id'" in m and any("'link' precisa começar com https://" in x for x in m)
    assert any("'criado_em' inválido" in x for x in m)


# ===========================================================================
# migrar_v1 (pedido real da §4.7)
# ===========================================================================
def test_migrar_v1_do_pedido_real(real):
    out = fv.migrar_v1(real)
    assert out["versao"] == 2 and out["migrado_de"] == "v1" and len(out["stories"]) == 1
    s = out["stories"][0]
    assert s["tipo"] == "compartilhar_post" and s["quando"] == "2026-09-30 17:07" and s["link"] == LINK
    assert s["arte"] is None and s["figurinha"] is None and s["destaque"] is None
    assert s["texto"] == "CR7 deixa a concentração de Portugal após a coletiva de Jorge Jesus"
    for c in fv.CAMPOS_V1:                      # os campos de hoje continuam valendo, sem mexer
        assert out[c] == real[c]
    assert fv.migrar_v1(out) == out             # idempotente (já v2 só valida)


def test_migrar_v1_do_carrossel_real():
    out = fv.migrar_v1(ler_json(PC_REAL / "fila_story_pedido_real_carrossel.json"))
    assert out["conta"] == "hp.carros" and out["stories"][0]["quando"] == "2026-09-30 23:03"


@pytest.mark.parametrize("publicado_em", ["2026-09-30 17:07", "2026-09-30T17:07:00-03:00", "2026-09-30T20:07:00+00:00",
                                          "2026-09-30T20:07:00Z"])
def test_migrar_aceita_sem_fuso_e_iso_com_fuso(real, publicado_em):
    d = dict(real, publicado_em=publicado_em)
    assert fv.migrar_v1(d)["stories"][0]["quando"] == "2026-09-30 17:07"
    assert fv.migrar_v1(d)["publicado_em"] == publicado_em     # o campo original não muda


def test_migrar_v1_incompleto_recusa(real):
    d = dict(real)
    del d["link"]
    assert "falta o campo 'link' do pedido v1" in motivos(fv.migrar_v1, d)
    assert any("'publicado_em' inválido" in x for x in motivos(fv.migrar_v1, dict(real, publicado_em="30/09")))
    assert "o pedido precisa ser um objeto JSON" in motivos(fv.migrar_v1, "x")


def test_normalizar_quando():
    assert fv.normalizar_quando("2026-09-30 17:07").isoformat() == "2026-09-30T17:07:00-03:00"
    assert fv.formatar_quando(datetime(2026, 9, 30, 20, 7, tzinfo=timezone.utc)) == "2026-09-30 17:07"
    with pytest.raises(ValueError):
        fv.normalizar_quando("")
    with pytest.raises(ValueError):
        fv.normalizar_quando("2026-13-01 10:00")


# ===========================================================================
# de_lote_estaticos (lote real de 2026-10-01)
# ===========================================================================
def test_lote_real_vira_3_itens_contagem_compartilhar_post_e_enquete(lote):
    r = fv.de_lote_estaticos(lote)
    assert r["data"] == "2026-10-01" and r["canal"] == "gta" and r["conta"] == "hpgta6" and r["recusados"] == []
    assert [s["tipo"] for s in r["stories"]] == ["contagem", "compartilhar_post", "enquete"]
    c, v, e = r["stories"]
    assert c["quando"] == "2026-10-01 09:00" and c["arte"] == "H:\\HypadoLocal\\upload\\stories_2026-10-01\\0900_contagem.jpg"
    assert c["zonas"] == "H:\\HypadoLocal\\upload\\stories_2026-10-01\\0900_contagem_zonas.json"
    assert c["figurinha"] == {"tipo": "contagem", "url": None, "rotulo": None, "opcoes": None, "data": "2026-11-19", "dias": 49}
    assert v["quando"] == "2026-10-01 12:10" and v["texto"] == "Dá pra ficar GORDO no GTA 6" and v["link"] is None
    assert v["pendencias"] == ["link do post do vídeo (vem da fila_story quando o post sair)"]
    assert e["quando"] == "2026-10-01 16:00" and e["pergunta_publico"] == "O que você faz?"
    assert e["figurinha"] == {"tipo": "enquete", "url": None, "rotulo": None, "opcoes": ["Vou ver de perto", "Fujo pro outro lado"]}
    assert e["texto"] == "Furacão chegando em Leonida. O que você faz?" and e["destaque"] == "Enquetes" and e["conta"] == "hpgta6"
    assert e["arte"] == "H:\\HypadoLocal\\upload\\story_interativo_2026-10-01.jpg"


def test_pedido_de_lote_valida_so_com_o_link_do_video(lote, tmp_path):
    m = motivos(fv.pedido_de_lote, lote, agora=AGORA)
    assert any("stories[1] (compartilhar_post): falta o link do post" in x for x in m)
    p = fv.pedido_de_lote(lote, agora=AGORA, links={"12:10": LINK}, titulo_contagem="Lançamento do GTA 6")
    assert p["post_id"] == "gta_2026-10-01_estaticos" and p["conta"] == "hpgta6" and p["criado_em"] == "2026-10-01 07:30"
    assert p["stories"][1]["link"] == LINK and p["stories"][0]["figurinha"]["rotulo"] == "Lançamento do GTA 6"
    assert p["origem"]["recusados"] == [] and p["versao"] == 2
    arq = fv.gravar_pedido(tmp_path / "fila_story" / "gta_2026-10-01_estaticos.json", p)
    assert fv.ler_pedido(arq) == p
    sem = fv.pedido_de_lote(lote, validar=False)
    assert sem["criado_em"] is None and len(sem["stories"]) == 3


def test_lote_temas_comenta_ai_tipo_explicito_e_desconhecido(lote):
    d = copy.deepcopy(lote)
    d["stories"] += [
        {"hora": "18:30", "arquivo": "H:\\x\\1830.jpg", "tema": "Comenta aí: qual mapa você quer?"},
        {"hora": "19:00", "arquivo": "H:\\x\\1900.jpg", "tema": "bastidores", "tipo": "mais_sobre"},
        {"hora": "20:00", "arquivo": "H:\\x\\2000.jpg", "tema": "qualquer coisa"},
        {"hora": "21:00", "tema": "vídeo novo: sem arquivo"},
        {"hora": "25:00", "arquivo": "H:\\x\\2500.jpg", "tema": "contagem 3 dias"},
        {"hora": "22:00", "arquivo": "H:\\x\\2200.jpg", "tema": "contagem", "tipo": "contagem"},
        "não sou objeto",
    ]
    r = fv.de_lote_estaticos(d)
    tipos = {s["quando"]: s["tipo"] for s in r["stories"]}
    assert tipos["2026-10-01 18:30"] == "interacao" and tipos["2026-10-01 19:00"] == "mais_sobre"
    assert [s["quando"] for s in r["stories"]] == sorted(s["quando"] for s in r["stories"])
    rec = {x["origem"]: x["motivo"] for x in r["recusados"]}
    assert "não sei o tipo do story pelo tema 'qualquer coisa'" in rec["stories[4]"]
    assert rec["stories[5]"] == "item incompleto: falta arquivo"
    assert "hora '25:00' fora do formato" in rec["stories[6]"]
    assert rec["stories[7]"] == "contagem sem 'data' nem 'N dias' no tema"
    assert rec["stories[8]"] == "item não é um objeto"


def test_lote_interativo_pergunta_impossivel_e_limite_maior(lote):
    r = fv.de_lote_estaticos(lote, limite_pergunta=10)
    assert [s["tipo"] for s in r["stories"]] == ["contagem", "compartilhar_post"]
    assert r["recusados"][0]["origem"] == "interativo" and "não cabe na figurinha" in r["recusados"][0]["motivo"]
    r = fv.de_lote_estaticos(lote, limite_pergunta=60)
    assert r["stories"][2]["pergunta_publico"] == "Furacão chegando em Leonida. O que você faz?"
    d = copy.deepcopy(lote)
    d["interativo"]["figurinha"] = "quiz"
    assert "não é enquete" in fv.de_lote_estaticos(d)["recusados"][0]["motivo"]
    d = copy.deepcopy(lote)
    d["interativo"]["opcoes"] = ["Só uma"]
    assert "2 a 4 opções" in fv.de_lote_estaticos(d)["recusados"][0]["motivo"]


def test_lote_sem_data_ou_sem_nada_recusa(lote):
    d = copy.deepcopy(lote)
    del d["data"]
    assert any("não tem 'data'" in x for x in motivos(fv.de_lote_estaticos, d))
    assert any("nenhum story aproveitável" in x for x in motivos(fv.pedido_de_lote, {"data": "2026-10-01", "stories": []}))


# ===========================================================================
# ler_zonas (saída do story_artes, D) -> tela real
# ===========================================================================
def zonas_da_d(tmp_path, figurinhas=("link", "enquete")) -> Path:
    base = pytest.importorskip("story_artes_base")
    z = base.zonas_de(list(figurinhas))
    arte = tmp_path / "story_chamada.jpg"
    arte.write_bytes(b"\xff\xd8")
    (tmp_path / "story_chamada_zonas.json").write_text(json.dumps(z), encoding="utf-8")
    return arte


@pytest.mark.parametrize("tela, link, enquete", [((1080, 2400), [140, 1875, 940, 2050], [110, 1163, 970, 1850]),
                                                 ((1080, 2340), [140, 1828, 940, 1999], [110, 1133, 970, 1804])])
def test_ler_zonas_converte_fracao_vezes_wm_size(tmp_path, tela, link, enquete):
    z = fv.ler_zonas(zonas_da_d(tmp_path), tela)
    assert z["link"] == link and z["enquete"] == enquete and z["tela"] == list(tela) and z["arte"] == [1080, 1920]
    assert z["centro_link"] == [540, (link[1] + link[3]) // 2 if (link[1] + link[3]) % 2 == 0 else round((link[1] + link[3]) / 2)]
    assert z["link_fracao"] == [0.1296, 0.7812, 0.8704, 0.8542] and z["figurinhas"] == ["link", "enquete"]


def test_ler_zonas_com_area_da_arte_na_tela_e_so_pixels(tmp_path):
    arte = zonas_da_d(tmp_path, ("link",))
    z = fv.ler_zonas(arte, (1080, 2400), area=(0, 240, 1080, 2160))     # a arte ocupa só parte da tela
    assert z["link"] == [140, 1740, 940, 1880] and "enquete" not in z
    (tmp_path / "so_px_zonas.json").write_text(json.dumps({"enquete": [110, 930, 970, 1480]}), encoding="utf-8")
    z = fv.ler_zonas(tmp_path / "so_px_zonas.json", (1080, 2400))
    assert z["enquete"] == [110, 1163, 970, 1850] and z["enquete_fracao"] == [0.1019, 0.4844, 0.8981, 0.7708]
    assert z["arquivo"].endswith("so_px_zonas.json")


def test_ler_zonas_erros_em_portugues(tmp_path):
    with pytest.raises(fv.FilaInvalida) as e:
        fv.ler_zonas(tmp_path / "nao_existe.jpg", (1080, 2400))
    assert "não achei as zonas da arte" in str(e.value) and "story_artes" in str(e.value)
    (tmp_path / "ruim_zonas.json").write_text("{", encoding="utf-8")
    with pytest.raises(fv.FilaInvalida):
        fv.ler_zonas(tmp_path / "ruim.jpg", (1080, 2400))
    (tmp_path / "vazia_zonas.json").write_text('{"largura": 1080}', encoding="utf-8")
    with pytest.raises(fv.FilaInvalida) as e:
        fv.ler_zonas(tmp_path / "vazia.jpg", (1080, 2400))
    assert "não tem zona" in str(e.value)
    with pytest.raises(fv.FilaInvalida):
        fv.ler_zonas(zonas_da_d(tmp_path), (0, 2400))
    assert fv.caminho_zonas("H:\\x\\arte.JPG") == "H:\\x\\arte_zonas.json" and fv.caminho_zonas("a_zonas.json") == "a_zonas.json"


# ===========================================================================
# Arquivo atômico e CLI
# ===========================================================================
def test_gravar_e_ler_atomico_e_migracao_na_leitura(tmp_path, real):
    pasta = tmp_path / "fila_story"
    p = fv.gravar_pedido(pasta / "x.json", exemplo_v2())
    assert ler_json(p)["versao"] == 2 and not list(pasta.glob(".tmp_*"))
    with pytest.raises(fv.FilaInvalida):
        fv.gravar_pedido(pasta / "y.json", {"stories": []})
    assert not (pasta / "y.json").exists()
    (pasta / "v1.json").write_text(json.dumps(real, ensure_ascii=False), encoding="utf-8")
    assert fv.ler_pedido(pasta / "v1.json")["stories"][0]["tipo"] == "compartilhar_post"
    with pytest.raises(fv.FilaInvalida):
        fv.ler_pedido(pasta / "v1.json", migrar=False)
    with pytest.raises(fv.FilaInvalida) as e:
        fv.ler_pedido(pasta / "nada.json")
    assert "não achei o pedido" in str(e.value)


def test_cli(tmp_path, real, lote):
    out = []
    v2 = tmp_path / "v2.json"
    v2.write_text(json.dumps(exemplo_v2(), ensure_ascii=False), encoding="utf-8")
    v1 = tmp_path / "v1.json"
    v1.write_text(json.dumps(real, ensure_ascii=False), encoding="utf-8")
    assert fv.main(["validar", str(v2)], saida=out.append) == 0 and out[-1] == "ok: pedido v2 válido"
    assert fv.main(["validar", str(v1)], saida=out.append) == 1 and out[-2] == "pedido inválido:"
    assert fv.main(["migrar", str(v1), "--saida", str(tmp_path / "m.json")], saida=out.append) == 0
    assert ler_json(tmp_path / "m.json")["stories"][0]["quando"] == "2026-09-30 17:07"
    lote_p = tmp_path / "lote.json"
    lote_p.write_text(json.dumps(lote, ensure_ascii=False), encoding="utf-8")
    assert fv.main(["de-lote", str(lote_p), "--agora", "2026-10-01 07:30"], saida=out.append) == 1   # sem o link do vídeo
    assert any("falta o link do post" in l for l in out)
    assert fv.main(["de-lote", str(lote_p), "--limite", "10"], saida=out.append) == 1
    assert fv.main(["zonas", str(zonas_da_d(tmp_path)), "--tela", "1080x2400"], saida=out.append) == 0
    assert json.loads(out[-1])["link"] == [140, 1875, 940, 2050]
    assert fv.main([], saida=out.append) == 1
    assert fv.main(["migrar", str(tmp_path / "nao.json")], saida=out.append) == 1
