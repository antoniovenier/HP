"""Lâminas (carrossel/estáticos) e imagem única."""
import numpy as np
import pytest

from qa_paridade import comparar_imagem, comparar_laminas
from qa_paridade.laminas import listar_laminas

from .apoio import imagem_teste, salvar_png


def _pasta(tmp_path, nome, sementes, nomes=None):
    d = tmp_path / nome
    d.mkdir()
    for k, s in enumerate(sementes):
        arq = (nomes[k] if nomes else f"lamina_{k + 1}.png")
        salvar_png(imagem_teste(s), d / arq)
    return d


def test_ordem_natural_do_nome(tmp_path):
    d = _pasta(tmp_path, "x", [1, 2, 3], ["lamina_10.png", "lamina_2.png", "lamina_1.png"])
    (d / "leia.txt").write_text("não é imagem")
    assert [p.name for p in listar_laminas(d)] == ["lamina_1.png", "lamina_2.png", "lamina_10.png"]


def test_laminas_iguais(tmp_path):
    ref = _pasta(tmp_path, "ref", [1, 2, 3, 4, 5])
    app = _pasta(tmp_path, "app", [1, 2, 3, 4, 5])
    rel = comparar_laminas(app, ref)
    m = rel["metricas"]["laminas"]
    assert m["nota"] == 10
    assert m["detalhes"]["ordem_correta"] is True
    assert m["detalhes"]["faltando_no_app"] == [] and m["detalhes"]["sobrando_no_app"] == []
    assert rel["veredito"] == "IDENTICO" and rel["aprovado"]


def test_laminas_trocadas_de_ordem(tmp_path):
    ref = _pasta(tmp_path, "ref", [1, 2, 3, 4, 5])
    app = _pasta(tmp_path, "app", [1, 3, 2, 4, 5])  # 2 e 3 trocadas
    rel = comparar_laminas(app, ref)
    m = rel["metricas"]["laminas"]
    d = m["detalhes"]
    assert d["ordem_correta"] is False
    assert {(f["posicao_app"], f["posicao_ref"]) for f in d["fora_de_ordem"]} == {(2, 3), (3, 2)}
    assert m["subnotas"]["ordem"] < 9
    assert m["subnotas"]["ssim_media"] == 10  # o conteúdo é o mesmo, só a ordem mudou
    # pela ordem do nome, as posições 2 e 3 ficam bem diferentes
    por_nome = {p["posicao"]: p["ssim"] for p in d["pares_por_nome"]}
    assert por_nome[2] < 0.9 and por_nome[1] == 1.0
    assert rel["veredito"] == "DIFERENTE" and not rel["aprovado"]
    assert "ORDEM TROCADA" in m["resumo"]


def test_lamina_faltando(tmp_path):
    ref = _pasta(tmp_path, "ref", [1, 2, 3, 4])
    app = _pasta(tmp_path, "app", [1, 2, 4], ["lamina_1.png", "lamina_2.png", "lamina_4.png"])
    m = comparar_laminas(app, ref)["metricas"]["laminas"]
    assert m["detalhes"]["faltando_no_app"] == ["lamina_3.png"]
    assert m["detalhes"]["ordem_correta"] is True
    assert m["subnotas"]["quantidade"] < 9
    assert m["nota"] < 9


def test_lamina_sobrando_e_lamina_estranha(tmp_path):
    ref = _pasta(tmp_path, "ref", [1, 2, 3])
    app = _pasta(tmp_path, "app", [1, 2, 3, 99])
    m = comparar_laminas(app, ref)["metricas"]["laminas"]
    assert m["detalhes"]["sobrando_no_app"] == ["lamina_4.png"]
    assert m["nota"] < 9
    # mesma quantidade, mas uma lâmina com outro conteúdo: faltando + sobrando
    app2 = _pasta(tmp_path, "app2", [1, 99, 3])
    m2 = comparar_laminas(app2, ref)["metricas"]["laminas"]
    assert m2["detalhes"]["faltando_no_app"] == ["lamina_2.png"]
    assert m2["detalhes"]["sobrando_no_app"] == ["lamina_2.png"]
    assert m2["nota"] < 9


def test_pasta_vazia_ou_inexistente(tmp_path):
    ref = _pasta(tmp_path, "ref", [1, 2])
    vazia = tmp_path / "vazia"
    vazia.mkdir()
    rel = comparar_laminas(vazia, ref)
    assert rel["metricas"]["laminas"]["nota"] == 0 and not rel["aprovado"]
    with pytest.raises(FileNotFoundError):
        comparar_laminas(tmp_path / "nao_existe", ref)


def test_imagem_igual_e_com_ruido(tmp_path):
    arr = imagem_teste(10)
    a = salvar_png(arr, tmp_path / "a.png")
    b = salvar_png(arr.copy(), tmp_path / "b.png")
    rel = comparar_imagem(a, b)
    assert rel["metricas"]["ssim"]["nota"] == 10 and rel["veredito"] == "IDENTICO"
    ruidosa = np.clip(arr + np.random.default_rng(0).normal(0, 30, arr.shape), 0, 255)
    c = salvar_png(ruidosa.astype(np.uint8), tmp_path / "c.png")
    rel2 = comparar_imagem(c, a)
    assert rel2["metricas"]["ssim"]["detalhes"]["ssim"] < 0.9
    assert rel2["veredito"] == "DIFERENTE"


def test_imagem_jpeg_de_boa_qualidade_passa(tmp_path):
    from PIL import Image
    arr = imagem_teste(11)
    a = salvar_png(arr, tmp_path / "a.png")
    Image.fromarray(arr).save(tmp_path / "a.jpg", quality=95)
    rel = comparar_imagem(tmp_path / "a.jpg", a)
    assert rel["aprovado"], rel["metricas"]["ssim"]["resumo"]


def test_imagem_com_resolucao_diferente(tmp_path):
    from PIL import Image
    arr = imagem_teste(12)
    a = salvar_png(arr, tmp_path / "a.png")
    Image.fromarray(arr).resize((108, 135)).save(tmp_path / "pequena.png")
    rel = comparar_imagem(tmp_path / "pequena.png", a)
    assert rel["metricas"]["formato"]["nota"] == 0
    assert rel["veredito"] == "DIFERENTE"
