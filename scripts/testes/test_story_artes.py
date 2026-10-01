"""Testes do gerador de artes de story (scripts/story_artes*.py).

Rodar:  cd scripts && python -m pytest -q testes/test_story_artes.py
Sem rede, sem olhar imagem a olho: tudo é conferido por número (bbox das camadas
de texto, contraste WCAG contra o fundo amostrado, variância dentro das zonas das
figurinhas, cor dominante, SHA-256). Capas sintéticas feitas aqui, em tmp_path.
Rodam com o fallback de fonte (DejaVu): HP_FONTES / HP_FONTES_CACHE são apagadas.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import story_artes as sa  # noqa: E402  (põe o hpbase no sys.path)
import story_artes_base as sb  # noqa: E402
import story_artes_canais as sc  # noqa: E402
from story_artes_exemplos import capa_sintetica, prancha, specs_exemplo  # noqa: E402
from hpbase import marca  # noqa: E402

CANAIS = list(marca.ORDEM_CANAIS)
TIPOS = list(sb.TIPOS)
COMBOS = [(c, t) for c in CANAIS for t in TIPOS]
IDS = [f"{c}-{t}" for c, t in COMBOS]


# ------------------------------------------------------------------ fixtures
@pytest.fixture(autouse=True)
def raizes_do_teste(tmp_path, monkeypatch):
    """Nada toca no H:/G: nem nas fontes reais (fallback DejaVu)."""
    local, drive = tmp_path / "HypadoLocal", tmp_path / "Drive"
    local.mkdir(exist_ok=True)
    drive.mkdir(exist_ok=True)
    monkeypatch.setenv("HP_LOCAL", str(local))
    monkeypatch.setenv("HP_DRIVE", str(drive))
    for var in ("HP_FONTES", "HP_FONTES_CACHE", "HP_APP"):
        monkeypatch.delenv(var, raising=False)
    return local, drive


@pytest.fixture(scope="module")
def capas(tmp_path_factory):
    """Capas sintéticas (1080x1350) de cada canal + duas fotos para o 'você prefere'."""
    pasta = tmp_path_factory.mktemp("capas")
    out = {}
    for c in CANAIS:
        out[c] = {}
        for nome, var in (("capa", 0), ("a", 1), ("b", 2)):
            p = pasta / f"{c}_{nome}.jpg"
            capa_sintetica(c, var).save(p, "JPEG", quality=90)
            out[c][nome] = str(p)
    return out


def spec_base(canal: str, tipo: str, capas: dict, **extra) -> dict:
    """Spec mínimo de cada modelo (sem cor_destaque), com capa sintética."""
    s = {"canal": canal, "tipo": tipo, "capa": capas[canal]["capa"], "credito_foto": "Divulgação",
         "nome": f"{canal}_{tipo}"}
    if tipo == "chamada":
        s.update({"rotulo": "NOVO POST", "chamada": "Chegou a *novidade* que você pediu"})
    elif tipo == "maissobre":
        s.update({"rotulo": "MAIS SOBRE", "fatos": ["Primeiro fato *curto* do post", "Segundo fato do post",
                                                     "Terceiro fato, um pouco mais longo que os outros"],
                  "dado_forte": {"valor": "R$ 1.990", "legenda": "valor aproximado"}})
    else:
        s.update({"rotulo": "SUA VEZ", "pergunta": "Qual dos dois você *prefere*?"})
    s.update(extra)
    return s


@pytest.fixture(scope="module")
def renders(tmp_path_factory, capas):
    """Os 18 combos renderizados uma vez (com camadas), para os testes parametrizados."""
    import os
    os.environ.pop("HP_FONTES", None)
    os.environ.pop("HP_FONTES_CACHE", None)
    pasta = tmp_path_factory.mktemp("renders")
    out = {}
    for canal, tipo in COMBOS:
        s = spec_base(canal, tipo, capas)
        if tipo == "chamada" and canal in ("gta", "filmes"):
            s["figurinhas"] = ["link", "enquete"]
        if tipo == "interacao" and canal in ("carros", "destinos"):
            s["fotos_prefere"] = [capas[canal]["a"], capas[canal]["b"]]
        out[(canal, tipo)] = sa.render(s, saida=pasta, devolver_camadas=True)
    return out


def textos(res: dict) -> list[dict]:
    return [c for c in res["camadas"] if c["texto"] and c["bbox"]]


def media_atras(res: dict, bbox) -> tuple:
    x0, y0, x1, y1 = bbox
    arr = np.asarray(res["fundo"].crop((x0, y0, x1, y1))).astype(np.float64)
    return tuple(arr.reshape(-1, 3).mean(axis=0))


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ------------------------------------------------------------ os 18 (invariantes)
@pytest.mark.parametrize("canal,tipo", COMBOS, ids=IDS)
def test_tamanho_1080x1920(renders, canal, tipo):
    res = renders[(canal, tipo)]
    assert res["imagem"].size == (1080, 1920)
    with Image.open(res["jpg"]) as im:
        assert im.size == (1080, 1920)


@pytest.mark.parametrize("canal,tipo", COMBOS, ids=IDS)
def test_todo_texto_na_zona_segura(renders, canal, tipo):
    res = renders[(canal, tipo)]
    ts = textos(res)
    assert len(ts) >= 3, [c["nome"] for c in res["camadas"]]
    for c in ts:
        x0, y0, x1, y1 = c["bbox"]
        assert y0 >= marca.SAFE_TOPO, (c["nome"], c["bbox"])
        assert y1 <= 1920 - marca.SAFE_BASE, (c["nome"], c["bbox"])
        assert 0 <= x0 < x1 <= 1080, (c["nome"], c["bbox"])
    # elementos (cartão, pílulas, seta, CTA) também; só os contornos das zonas podem descer
    for c in res["camadas"]:
        if c["bbox"] and not c["nome"].startswith("zona_"):
            assert c["bbox"][1] >= marca.SAFE_TOPO and c["bbox"][3] <= 1920 - marca.SAFE_BASE, (c["nome"], c["bbox"])


@pytest.mark.parametrize("canal,tipo", COMBOS, ids=IDS)
def test_contraste_wcag_de_cada_texto(renders, canal, tipo):
    res = renders[(canal, tipo)]
    for c in textos(res):
        fundo = media_atras(res, c["bbox"])
        assert c["cores"], c["nome"]
        for cor in c["cores"]:
            razao = marca.contraste(cor, fundo)
            assert razao >= 4.5, f"{canal}/{tipo} '{c['nome']}' {cor} sobre {tuple(int(v) for v in fundo)}: {razao:.2f}"


@pytest.mark.parametrize("canal,tipo", COMBOS, ids=IDS)
def test_zonas_das_figurinhas_sem_texto(renders, canal, tipo):
    res = renders[(canal, tipo)]
    z = res["zonas_dict"]
    arr = np.asarray(res["imagem"]).astype(np.float64)
    for nome in ("link", "enquete"):
        if nome not in z:
            continue
        x0, y0, x1, y1 = z[nome]
        dentro = arr[y0 + 10:y1 - 10, x0 + 10:x1 - 10]        # fora do contorno fino
        variacao = dentro.reshape(-1, 3).std(axis=0).max()     # variância espacial, canal a canal
        assert variacao <= 10.0, (nome, variacao)
        for c in res["camadas"]:
            if c["bbox"] and not c["nome"].startswith("zona_"):
                bx0, by0, bx1, by1 = c["bbox"]
                cruza = bx0 < x1 and bx1 > x0 and by0 < y1 and by1 > y0
                assert not cruza, (nome, c["nome"], c["bbox"])
        # o contorno existe (a borda é diferente do miolo)
        borda = arr[y0:y0 + 3, x0 + 40:x1 - 40].mean()
        assert abs(borda - dentro.mean()) > 5


@pytest.mark.parametrize("canal", CANAIS)
def test_cor_dominante_e_destaque_casam_com_o_canal(renders, canal):
    res = renders[(canal, "maissobre")]
    arr = np.asarray(res["imagem"].resize((135, 240), Image.NEAREST)).reshape(-1, 3)
    bins = (arr // 16) * 16 + 8
    valores, contagens = np.unique(bins, axis=0, return_counts=True)
    dominante = valores[contagens.argmax()]
    esperadas = [marca.rgb(c) for c in sc.ESTILOS[canal]["cores_fundo"]]
    dist = min(np.linalg.norm(dominante - np.array(e)) for e in esperadas)
    assert dist <= 48, (canal, dominante.tolist(), esperadas)
    # a cor do canal (posts/stories) aparece de verdade (pílula, marcadores, destaque)
    cheio = np.asarray(res["imagem"]).reshape(-1, 3).astype(np.float64)
    alvo = np.array(marca.rgb(marca.CANAIS[canal]["cor_post"]), np.float64)
    perto = (np.linalg.norm(cheio - alvo, axis=1) <= 40).sum()
    assert perto >= 1500, (canal, perto)


@pytest.mark.parametrize("canal,tipo", COMBOS, ids=IDS)
def test_zonas_json_ao_lado_do_jpg(renders, canal, tipo):
    res = renders[(canal, tipo)]
    p = Path(res["zonas"])
    assert p.exists() and p.name == f"{canal}_{tipo}_zonas.json"
    z = json.loads(p.read_text(encoding="utf-8"))
    assert z["largura"] == 1080 and z["altura"] == 1920
    figs = res["spec"]["figurinhas"]
    for nome in figs:
        ret = z[nome]
        frac = z[nome + "_fracao"]
        assert ret == list(marca.ZONA_LINK if nome == "link" else marca.ZONA_ENQUETE)
        assert frac == [round(ret[0] / 1080, 4), round(ret[1] / 1920, 4), round(ret[2] / 1080, 4), round(ret[3] / 1920, 4)]
        assert ret[1] >= marca.SAFE_TOPO and ret[3] <= 1920 and 0 <= ret[0] < ret[2] <= 1080
    if "enquete" in figs:
        assert z["enquete"][3] <= 1920 - marca.SAFE_BASE
    if "link" in figs and "enquete" in figs:
        assert z["enquete"][3] <= z["link"][1]          # enquete acima do link, sem cruzar


# ------------------------------------------------------------------ regras
def test_entrada_com_emoji_sai_sem_emoji(tmp_path, capas):
    s = spec_base("gta", "chamada", capas, rotulo="NOVO 🔥 VÍDEO", chamada="GTA 6 🎮 ganha *data* 🚀",
                  credito_foto="Rockstar 📸")
    res = sa.render(s, saida=tmp_path, devolver_camadas=True)
    for campo in ("rotulo", "chamada", "credito_foto"):
        assert not marca.tem_emoji(res["spec"][campo]), res["spec"][campo]
    assert res["spec"]["chamada"] == "GTA 6 ganha *data*"
    s2 = spec_base("futebol", "maissobre", capas, fatos=["Gol aos 90 ⚽", "Título 🏆 confirmado"],
                   pergunta="")
    res2 = sa.render(s2, saida=tmp_path)
    assert all(not marca.tem_emoji(f) for f in res2["spec"]["fatos"])


def test_deterministico_sha256_igual_em_dois_renders(tmp_path, capas):
    s = spec_base("carros", "chamada", capas)
    a = sa.render(s, saida=tmp_path / "a", png=True)
    b = sa.render(s, saida=tmp_path / "b", png=True)
    assert sha(a["png"]) == sha(b["png"])
    assert sha(a["jpg"]) == sha(b["jpg"])
    assert (tmp_path / "a" / "carros_chamada.png").exists()


def test_png_so_quando_pedido(tmp_path, capas):
    res = sa.render(spec_base("filmes", "interacao", capas), saida=tmp_path)
    assert res["png"] is None and not (tmp_path / "filmes_interacao.png").exists()
    assert Path(res["jpg"]).exists()


def test_texto_longo_demais_da_erro_em_portugues(tmp_path, capas):
    s = spec_base("futebol", "chamada", capas, chamada="Uma chamada comprida demais para caber no story")
    with pytest.raises(sb.ErroStory) as e:
        sa.render(s, saida=tmp_path)
    assert "caracteres" in str(e.value) and "máximo" in str(e.value)
    # cabe no limite de caracteres, mas é uma palavra só que não cabe na largura nem no mínimo
    s = spec_base("futebol", "chamada", capas, chamada="Supercalifragilisticoexpialidocioso2026")
    with pytest.raises(sb.ErroStory) as e:
        sa.render(s, saida=tmp_path)
    assert "não cabe" in str(e.value) and "Encurte" in str(e.value)


def test_fato_longo_e_pergunta_longa_recusados(tmp_path, capas):
    s = spec_base("gta", "maissobre", capas, fatos=["x" * 71, "ok"])
    with pytest.raises(sb.ErroStory, match="fatos\\[1\\]"):
        sa.render(s, saida=tmp_path)
    s = spec_base("gta", "interacao", capas, pergunta="p" * 61)
    with pytest.raises(sb.ErroStory, match="pergunta"):
        sa.render(s, saida=tmp_path)


def test_os_18_exemplos_e_prancha_em_menos_de_60s(tmp_path):
    t0 = time.perf_counter()
    res = sa.render_exemplos(tmp_path)
    dt = time.perf_counter() - t0
    assert dt < 60, dt
    assert len(res["resultados"]) == 18
    jpgs = sorted(p.name for p in tmp_path.glob("*.jpg") if not p.name.startswith("_"))
    assert len(jpgs) == 18 and "gta_chamada.jpg" in jpgs and "destinos_interacao.jpg" in jpgs
    assert len(list(tmp_path.glob("*_zonas.json"))) == 18
    with Image.open(res["prancha"]) as im:
        assert im.size == (1620, 1518)          # 6 colunas x 3 linhas de miniaturas rotuladas


def test_chamada_com_enquete_encolhe_o_cartao(renders):
    normal = renders[("futebol", "chamada")]       # só link
    compacto = renders[("gta", "chamada")]          # link + enquete
    c1 = next(c for c in normal["camadas"] if c["nome"] == "cartao")["bbox"]
    c2 = next(c for c in compacto["camadas"] if c["nome"] == "cartao")["bbox"]
    assert 840 <= c1[2] - c1[0] <= 870
    assert 500 <= c2[2] - c2[0] <= 540 and c2[1] >= 290 and c2[3] <= 900
    assert "enquete" in compacto["zonas_dict"] and "enquete" not in normal["zonas_dict"]
    assert any(c["nome"] == "zona_enquete" for c in compacto["camadas"])
    assert any(c["nome"] == "seta" for c in normal["camadas"]) and any(c["nome"] == "seta" for c in compacto["camadas"])


def test_seta_vetorial_aponta_para_a_zona_do_link(renders):
    for chave in (("futebol", "chamada"), ("gta", "chamada")):
        res = renders[chave]
        seta = next(c for c in res["camadas"] if c["nome"] == "seta")
        x0, y0, x1, y1 = seta["bbox"]
        lx0, ly0, lx1, ly1 = marca.ZONA_LINK
        assert ly0 - 60 <= y1 < ly0, seta["bbox"]              # a ponta termina logo acima da zona
        assert y1 - y0 >= 60                                     # é uma seta desenhada, não um emoji
        assert seta["cores"] == [marca.hex_de(sc.estilo(chave[0])["acento"])]


def test_cor_destaque_so_vale_no_futebol(tmp_path, capas):
    magenta = np.array([255, 0, 255], np.float64)

    def quantos(res):
        arr = np.asarray(res["imagem"]).reshape(-1, 3).astype(np.float64)
        return int((np.linalg.norm(arr - magenta, axis=1) <= 40).sum())

    fut = sa.render(spec_base("futebol", "chamada", capas, cor_destaque="#FF00FF"), saida=tmp_path / "f",
                    devolver_camadas=True)
    car = sa.render(spec_base("carros", "chamada", capas, cor_destaque="#FF00FF"), saida=tmp_path / "c",
                    devolver_camadas=True)
    assert fut["spec"]["cor_destaque"] == "#FF00FF" and car["spec"]["cor_destaque"] is None
    assert quantos(fut) >= 1500 and quantos(car) < 50
    assert car["avisos"] and "Futebol" in car["avisos"][0]
    assert sc.estilo("gta", "#FF00FF")["acento"] == marca.CANAIS["gta"]["cor_post"]


def test_cor_do_clube_escura_e_clareada_ate_ler():
    est = sc.estilo("futebol", "#0A0A50")
    assert marca.contraste(est["destaque"], marca.CANAIS["futebol"]["fundo"]) >= 4.5
    assert est["pilula"]["fundo"] == "#0A0A50" and est["pilula"]["texto"] == "#FFFFFF"


def test_capa_ausente_usa_fundo_gerado(tmp_path, capas):
    s = spec_base("destinos", "chamada", capas)
    del s["capa"]
    res = sa.render(s, saida=tmp_path, devolver_camadas=True)
    cart = next(c for c in res["camadas"] if c["nome"] == "cartao")
    assert cart["bbox"][2] - cart["bbox"][0] >= 840
    s2 = spec_base("destinos", "maissobre", capas, capa=None, dado_forte=None)
    res2 = sa.render(s2, saida=tmp_path, devolver_camadas=True)
    assert Path(res2["jpg"]).exists()


def test_foco_muda_o_enquadramento(tmp_path, capas):
    a = sa.render(spec_base("receitas", "chamada", capas, foco=[0.0, 0.0], nome="a"), saida=tmp_path,
                  devolver_camadas=True)
    b = sa.render(spec_base("receitas", "chamada", capas, foco=[1.0, 1.0], nome="b"), saida=tmp_path,
                  devolver_camadas=True)
    bb = next(c for c in a["camadas"] if c["nome"] == "cartao")["bbox"]
    ra = np.asarray(a["imagem"].crop(bb)).astype(np.int16)
    rb = np.asarray(b["imagem"].crop(bb)).astype(np.int16)
    assert np.abs(ra - rb).mean() > 2.0


def test_credito_da_foto_so_quando_houver(tmp_path, capas):
    com = sa.render(spec_base("filmes", "chamada", capas, credito_foto="Warner"), saida=tmp_path, devolver_camadas=True)
    sem = sa.render(spec_base("filmes", "chamada", capas, credito_foto="", nome="sem"), saida=tmp_path,
                    devolver_camadas=True)
    assert any(c["nome"] == "credito_foto" for c in com["camadas"])
    assert not any(c["nome"] == "credito_foto" for c in sem["camadas"])


def test_tratamento_da_foto_e_cor_natural_com_vinheta():
    cinza = Image.new("RGB", (400, 300), (128, 128, 128))
    out = sb.tratar_foto(cinza)
    arr = np.asarray(out).astype(np.float64)
    centro = arr[150, 200]
    canto = arr[2, 2]
    assert abs(centro[0] - 128 * marca.TRATAMENTO_FOTO["brilho"]) <= 4     # brilho x0.96, cor não muda o cinza
    assert centro[0] == centro[1] == centro[2]                              # continua neutro (nunca tingida)
    assert canto[0] < centro[0] * 0.6                                       # vinheta 0.55 nos cantos
    colorida = Image.new("RGB", (400, 300), (200, 80, 60))
    c2 = np.asarray(sb.tratar_foto(colorida))[150, 200].astype(int)
    assert c2[0] > c2[1] > c2[2]                                            # a cor segue a da foto


def test_enquadrar_respeita_tamanho_e_foco():
    img = sb.degrade_diagonal((1080, 1350), "#000000", "#FFFFFF")
    a = sb.enquadrar(img, (860, 820), (0.0, 0.0))
    b = sb.enquadrar(img, (860, 820), (1.0, 1.0))
    assert a.size == b.size == (860, 820)
    assert np.asarray(a).mean() < np.asarray(b).mean()
    c = sb.enquadrar(img, (860, 820), (540, 1300))     # foco em pixels da imagem original também vale
    assert c.size == (860, 820) and np.asarray(c).mean() > np.asarray(a).mean()


def test_api_de_camadas_devolve_nome_e_bbox(renders):
    res = renders[("receitas", "maissobre")]
    nomes = {c["nome"] for c in res["camadas"]}
    for n in ("rotulo", "handle", "selo_hp", "fato_1", "fato_2", "fato_3", "dado_forte_valor", "cta", "miniatura",
              "zona_link"):
        assert n in nomes, nomes
    for c in res["camadas"]:
        assert set(c) == {"nome", "bbox", "texto", "cores"}
        if c["texto"]:
            assert len(c["bbox"]) == 4 and c["cores"]
    # o texto está mesmo lá: a imagem final difere do fundo dentro do bbox
    fato = next(c for c in res["camadas"] if c["nome"] == "fato_1")
    x0, y0, x1, y1 = fato["bbox"]
    a = np.asarray(res["imagem"].crop((x0, y0, x1, y1))).astype(np.int16)
    b = np.asarray(res["fundo"].crop((x0, y0, x1, y1))).astype(np.int16)
    assert np.abs(a - b).max() > 100


def test_interacao_com_fotos_prefere(renders):
    res = renders[("carros", "interacao")]
    nomes = [c["nome"] for c in res["camadas"]]
    assert "foto_a" in nomes and "foto_b" in nomes
    fa = next(c for c in res["camadas"] if c["nome"] == "foto_a")["bbox"]
    fb = next(c for c in res["camadas"] if c["nome"] == "foto_b")["bbox"]
    assert fa[2] <= fb[0] and fa[3] <= marca.ZONA_ENQUETE[1] and fb[3] <= marca.ZONA_ENQUETE[1]
    sem = renders[("futebol", "interacao")]
    assert not any(c["nome"].startswith("foto_") for c in sem["camadas"])
    assert any(c["nome"] == "cta" for c in sem["camadas"])


def test_personalidade_por_canal(renders):
    gta = renders[("gta", "interacao")]
    perg = next(c for c in gta["camadas"] if c["nome"] == "pergunta")
    assert set(perg["cores"]) >= {marca.GTA_ROSA_POST, marca.GTA6["laranja"]}      # degradê rosa->laranja
    fut = renders[("futebol", "chamada")]
    assert any(c["nome"] == "chamada_caixa" for c in fut["camadas"])                 # caixa escura translúcida
    assert any(c["nome"] == "cartao_contorno" for c in fut["camadas"])
    fil = renders[("filmes", "interacao")]
    caixa = next(c for c in fil["camadas"] if c["nome"] == "pergunta_caixa")
    assert caixa["cores"] == ["#000000"]                                               # com *destaque*: variação escura
    rec = renders[("receitas", "chamada")]
    assert any(c["nome"] == "chamada_faixa" and c["cores"] == ["#FFE212"] for c in rec["camadas"])
    car = renders[("carros", "chamada")]
    assert any(c["nome"] == "chamada_traco" and c["cores"] == [marca.CARROS_COR_POST] for c in car["camadas"])
    assert any(c["nome"] == "selo_hp_fundo" and c["cores"] == [marca.CARROS_COR_POST] for c in car["camadas"])
    des = renders[("destinos", "chamada")]
    assert any(c["nome"] == "chamada_barra" and c["cores"] == ["#00C2D1"] for c in des["camadas"])


def test_filmes_sem_destaque_usa_caixa_amarela(tmp_path, capas):
    res = sa.render(spec_base("filmes", "interacao", capas, pergunta="Cinema ou streaming?"), saida=tmp_path,
                    devolver_camadas=True)
    caixa = next(c for c in res["camadas"] if c["nome"] == "pergunta_caixa")
    assert caixa["cores"] == [marca.CANAIS["filmes"]["cor_post"]]
    perg = next(c for c in res["camadas"] if c["nome"] == "pergunta")
    assert perg["cores"] == ["#000000"]


def test_destinos_pilula_ida_e_volta_so_em_preco(tmp_path, capas):
    com = sa.render(spec_base("destinos", "maissobre", capas), saida=tmp_path, devolver_camadas=True)
    sem = sa.render(spec_base("destinos", "maissobre", capas, nome="sem", dado_forte={"valor": "7 dias", "legenda": "x"}),
                    saida=tmp_path, devolver_camadas=True)
    outro = sa.render(spec_base("futebol", "maissobre", capas), saida=tmp_path, devolver_camadas=True)
    assert any(c["nome"] == "ida_volta" for c in com["camadas"])
    assert not any(c["nome"] == "ida_volta" for c in sem["camadas"])
    assert not any(c["nome"] == "ida_volta" for c in outro["camadas"])


def test_rotulo_e_cta_padrao_por_modelo(tmp_path, capas):
    s = spec_base("gta", "maissobre", capas)
    del s["rotulo"]
    res = sa.render(s, saida=tmp_path)
    assert res["spec"]["rotulo"] == "MAIS SOBRE" and res["spec"]["cta"] == "Salva o post"
    s = spec_base("gta", "chamada", capas)
    del s["rotulo"]
    assert sa.render(s, saida=tmp_path)["spec"]["rotulo"] == "NOVO POST"
    s = spec_base("gta", "interacao", capas, cta="Leia a legenda")
    del s["rotulo"]
    r = sa.render(s, saida=tmp_path)
    assert r["spec"]["rotulo"] == "SUA VEZ" and r["spec"]["cta"] == "Leia a legenda"


# --------------------------------------------------------------- spec/validação
@pytest.mark.parametrize("campo,valor,trecho", [
    ("canal", "tiktok", "Canal 'tiktok' não existe"),
    ("tipo", "capa", "Tipo 'capa' não existe"),
    ("figurinhas", ["gif"], "Figurinha 'gif' não existe"),
    ("nome", "com espaço", "nome"),
    ("cor_destaque", "azul", "cor_destaque inválida"),
    ("foco", "centro", "foco"),
])
def test_spec_invalido_erro_em_portugues(capas, campo, valor, trecho):
    s = spec_base("futebol", "chamada", capas)
    s[campo] = valor
    with pytest.raises(sb.ErroStory, match=trecho):
        sb.normalizar_spec(s)


def test_spec_campos_obrigatorios_por_modelo(capas):
    with pytest.raises(sb.ErroStory, match="'chamada'"):
        sb.normalizar_spec({"canal": "gta", "tipo": "chamada"})
    with pytest.raises(sb.ErroStory, match="2 a 4"):
        sb.normalizar_spec({"canal": "gta", "tipo": "maissobre", "fatos": ["um"]})
    with pytest.raises(sb.ErroStory, match="2 a 4"):
        sb.normalizar_spec({"canal": "gta", "tipo": "maissobre", "fatos": ["1", "2", "3", "4", "5"]})
    with pytest.raises(sb.ErroStory, match="'pergunta'"):
        sb.normalizar_spec({"canal": "gta", "tipo": "interacao"})
    with pytest.raises(sb.ErroStory, match="enquete"):
        sb.normalizar_spec({"canal": "gta", "tipo": "maissobre", "fatos": ["a", "b"], "figurinhas": ["link", "enquete"]})
    with pytest.raises(sb.ErroStory, match="dado_forte"):
        sb.normalizar_spec({"canal": "gta", "tipo": "maissobre", "fatos": ["a", "b"], "dado_forte": "19/11"})
    with pytest.raises(sb.ErroStory, match="fotos_prefere"):
        sb.normalizar_spec({"canal": "gta", "tipo": "interacao", "pergunta": "x?", "fotos_prefere": ["so_uma.jpg"]})


def test_spec_normalizado_padroes_e_handle():
    s = sb.normalizar_spec({"canal": "@hp.futebol", "tipo": "interacao", "pergunta": "Vai?", "figurinhas": ["link"]})
    assert s["canal"] == "futebol" and s["figurinhas"] == ["enquete", "link"]
    assert s["nome"] == "story_futebol_interacao" and s["foco"] == (0.5, 0.5) and s["cta"] == "Responde aí"
    s = sb.normalizar_spec({"canal": "carros", "tipo": "chamada", "chamada": "Ok", "figurinhas": "link"})
    assert s["figurinhas"] == ["link"] and s["rotulo"] == "NOVO POST"


def test_zonas_de_em_pixels_e_fracao():
    z = sb.zonas_de(["link", "enquete"])
    assert z["link"] == [140, 1500, 940, 1640] and z["enquete"] == [110, 930, 970, 1480]
    assert z["link_fracao"] == [round(140 / 1080, 4), round(1500 / 1920, 4), round(940 / 1080, 4), round(1640 / 1920, 4)]
    assert z["enquete_fracao"][1] == round(930 / 1920, 4)
    assert "enquete" not in sb.zonas_de(["link"]) and "link_fracao" not in sb.zonas_de(["enquete"])


def test_tokens_destaque_cola_pontuacao():
    toks = sb.tokens_destaque("Vale os *R$ 80 milhões*? (*sim*)")
    planos = ["".join(t for t, _ in p) for p in toks]
    assert planos == ["Vale", "os", "R$", "80", "milhões?", "(sim)"]
    assert toks[4] == [("milhões", True), ("?", False)]
    assert toks[5] == [("(", False), ("sim", True), (")", False)]


def test_ajustar_reduz_a_letra_ate_caber_e_recusa():
    f, linhas, tam = sb.ajustar("Uma chamada que precisa de duas linhas aqui", "Anton", 600, 2, 96, 40, "chamada")
    assert len(linhas) <= 2 and 40 <= tam <= 96
    f2, linhas2, tam2 = sb.ajustar("Curta", "Anton", 600, 2, 96, 40, "chamada")
    assert tam2 == 96 and len(linhas2) == 1
    with pytest.raises(sb.ErroStory, match="não cabe"):
        sb.ajustar("Palavra " * 12, "Anton", 300, 1, 40, 30, "chamada")
    with pytest.raises(sb.ErroStory, match="vazio"):
        sb.ajustar("   ", "Anton", 300, 1, 40, 30, "chamada")


def test_bloco_texto_degrade_italico_e_sublinhado():
    f = sb.fonte("Anton", 60)
    linhas = sb.tokens_destaque("Trailer *novo* hoje")
    img, cores = sb.bloco_texto([linhas], f, "#FFFFFF", "#46E1EB", degrade=["#FF48A0", "#FFB054"], contorno="#101234",
                                contorno_largura=3)
    assert img.mode == "RGBA" and img.getbbox() and set(cores) == {(255, 72, 160), (255, 176, 84), (70, 225, 235)}
    reto, _ = sb.bloco_texto([linhas], f, "#FFFFFF")
    ital, _ = sb.bloco_texto([linhas], f, "#FFFFFF", italico=0.2)
    assert ital.width > reto.width
    sub, cores_sub = sb.bloco_texto([linhas], f, "#120C09", "#120C09", sublinhado="#FF7A1A")
    arr = np.asarray(sub)
    laranja = ((arr[..., 0] == 255) & (arr[..., 1] == 122) & (arr[..., 3] > 0)).sum()
    assert laranja > 100 and cores_sub == [(18, 12, 9), (18, 12, 9)]


def test_fontes_vem_do_resolvedor_da_marca_com_fallback():
    r = marca.resolver_fonte("Bauhaus 93")
    assert r.origem in ("dejavu", "cache", "pc", "windows", "pillow")
    f = sb.fonte("Bauhaus 93", 40)
    assert f.getbbox("HP")[2] > 0


# --------------------------------------------------------------------- CLI
def test_cli_render_codigo_0_e_1(tmp_path, capas, capsys):
    spec = spec_base("futebol", "chamada", capas, saida=str(tmp_path / "out"))
    p = tmp_path / "spec.json"
    p.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
    assert sa.main(["render", str(p), "--png"]) == 0
    assert (tmp_path / "out" / "futebol_chamada.jpg").exists()
    assert (tmp_path / "out" / "futebol_chamada.png").exists()
    assert (tmp_path / "out" / "futebol_chamada_zonas.json").exists()
    saida = capsys.readouterr().out
    assert "ok:" in saida and "zonas:" in saida
    assert sa.main(["render", str(tmp_path / "nao_existe.json")]) == 1
    assert "Não achei" in capsys.readouterr().err
    ruim = tmp_path / "ruim.json"
    ruim.write_text(json.dumps({"canal": "futebol", "tipo": "chamada", "chamada": "x" * 60, "saida": str(tmp_path)}),
                    encoding="utf-8")
    assert sa.main(["render", str(ruim)]) == 1
    assert "erro:" in capsys.readouterr().err
    quebrado = tmp_path / "quebrado.json"
    quebrado.write_text("{isso nao e json", encoding="utf-8")
    assert sa.main(["render", str(quebrado)]) == 1
    assert sa.main([]) == 1


def test_cli_render_sem_saida_usa_a_pasta_do_spec(tmp_path, capas, capsys):
    spec = spec_base("gta", "interacao", capas)
    p = tmp_path / "spec.json"
    p.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
    assert sa.main(["render", str(p)]) == 0
    assert (tmp_path / "gta_interacao.jpg").exists()
    assert sa.main(["render", str(p), "--saida", str(tmp_path / "outra")]) == 0
    assert (tmp_path / "outra" / "gta_interacao.jpg").exists()


def test_cli_todas_e_exemplos(tmp_path, capsys):
    assert sa.main(["todas", "receitas", str(tmp_path / "r")]) == 0
    nomes = sorted(p.name for p in (tmp_path / "r").glob("receitas_*.jpg"))
    assert nomes == ["receitas_chamada.jpg", "receitas_interacao.jpg", "receitas_maissobre.jpg"]
    assert sa.main(["todas", "tiktok", str(tmp_path / "x")]) == 1
    assert "não existe" in capsys.readouterr().err
    assert sa.main(["spec-exemplo"]) == 0
    dados = json.loads(capsys.readouterr().out)
    assert dados["canal"] == "futebol" and dados["tipo"] == "chamada"


def test_cli_aviso_cor_destaque_fora_do_futebol(tmp_path, capas, capsys):
    spec = spec_base("gta", "chamada", capas, cor_destaque="#123456", saida=str(tmp_path))
    p = tmp_path / "spec.json"
    p.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
    assert sa.main(["render", str(p)]) == 0
    assert "aviso: cor_destaque só vale no Futebol" in capsys.readouterr().out


def test_exemplos_cobrem_os_18_e_sao_validos():
    specs = specs_exemplo()
    assert len(specs) == 18 and {(s["canal"], s["tipo"]) for s in specs} == set(COMBOS)
    for s in specs:
        n = sb.normalizar_spec(dict(s, fotos_prefere=None))
        assert n["nome"] == f"{s['canal']}_{s['tipo']}"


def test_prancha_marca_miniatura_faltando(tmp_path):
    p = prancha({}, tmp_path / "_prancha_story.jpg")
    with Image.open(p) as im:
        assert im.size == (1620, 1518)
