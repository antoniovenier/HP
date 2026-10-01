"""SSIM próprio (numpy) e casamento ótimo (húngaro) — sem ffmpeg."""
import itertools

import numpy as np
import pytest

from qa_paridade.laminas import casamento_otimo
from qa_paridade.limites import nota_por_pontos
from qa_paridade.ssim import janela_gaussiana, pior_regiao, ssim, ssim_mapa


def _imagem_suave(alt=120, larg=90, semente=0):
    rng = np.random.default_rng(semente)
    y = np.linspace(0, 1, alt)[:, None]
    x = np.linspace(0, 1, larg)[None, :]
    img = 60 + 120 * x * y + 40 * np.sin(8 * x) * np.cos(6 * y)
    img[30:60, 20:50] = 220
    return np.clip(img + rng.normal(0, 2, img.shape), 0, 255)


def _ssim_forca_bruta(a, b, tamanho=7, sigma=1.5):
    """Conta direta janela por janela (lenta), para validar a versão rápida."""
    g = janela_gaussiana(tamanho, sigma)
    w2 = np.outer(g, g)
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    alt, larg = a.shape
    saida = np.zeros((alt - tamanho + 1, larg - tamanho + 1))
    for i in range(saida.shape[0]):
        for j in range(saida.shape[1]):
            pa = a[i:i + tamanho, j:j + tamanho]
            pb = b[i:i + tamanho, j:j + tamanho]
            ma, mb = (w2 * pa).sum(), (w2 * pb).sum()
            va = (w2 * (pa - ma) ** 2).sum()
            vb = (w2 * (pb - mb) ** 2).sum()
            cov = (w2 * (pa - ma) * (pb - mb)).sum()
            saida[i, j] = ((2 * ma * mb + c1) * (2 * cov + c2)
                           / ((ma ** 2 + mb ** 2 + c1) * (va + vb + c2)))
    return saida


def test_imagem_igual_da_1():
    a = _imagem_suave()
    assert ssim(a, a) == pytest.approx(1.0, abs=1e-12)
    ruido = np.random.default_rng(5).integers(0, 256, (64, 64))
    assert ssim(ruido, ruido.copy()) == pytest.approx(1.0, abs=1e-12)


def test_imagem_com_ruido_fica_abaixo_de_0_9():
    a = _imagem_suave()
    b = np.clip(a + np.random.default_rng(1).normal(0, 25, a.shape), 0, 255)
    v = ssim(a, b)
    assert v < 0.9
    assert v > 0.0


def test_ruido_leve_fica_alto_e_ordem_faz_sentido():
    a = _imagem_suave()
    rng = np.random.default_rng(2)
    leve = ssim(a, np.clip(a + rng.normal(0, 3, a.shape), 0, 255))
    forte = ssim(a, np.clip(a + rng.normal(0, 30, a.shape), 0, 255))
    assert 0.9 < leve < 1.0
    assert forte < leve


def test_versao_rapida_igual_a_forca_bruta():
    rng = np.random.default_rng(3)
    a = rng.integers(0, 256, (20, 17)).astype(float)
    b = np.clip(a + rng.normal(0, 20, a.shape), 0, 255)
    np.testing.assert_allclose(ssim_mapa(a, b), _ssim_forca_bruta(a, b), rtol=1e-9, atol=1e-12)


def test_simetrico_e_na_faixa():
    rng = np.random.default_rng(4)
    a = rng.integers(0, 256, (40, 30))
    b = 255 - a
    assert ssim(a, b) == pytest.approx(ssim(b, a))
    mapa = ssim_mapa(a, b)
    assert mapa.min() >= -1.0 - 1e-9 and mapa.max() <= 1.0 + 1e-9
    assert ssim(a, b) < 0  # imagem invertida: estrutura oposta


def test_janela_gaussiana_soma_1():
    g = janela_gaussiana(7, 1.5)
    assert len(g) == 7 and g.sum() == pytest.approx(1.0)
    assert g[3] == g.max()


def test_tamanhos_diferentes_ou_pequenos_dao_erro():
    with pytest.raises(ValueError):
        ssim(np.zeros((10, 10)), np.zeros((10, 11)))
    with pytest.raises(ValueError):
        ssim(np.zeros((5, 5)), np.zeros((5, 5)))


def test_pior_regiao_acha_onde_mudou():
    a = _imagem_suave(90, 90)
    b = a.copy()
    b[65:88, 65:88] = np.random.default_rng(7).integers(0, 256, (23, 23))
    assert pior_regiao(ssim_mapa(a, b)) == "base-direita"
    c = a.copy()
    c[2:25, 2:25] = 0
    assert pior_regiao(ssim_mapa(a, c)) == "topo-esquerda"


def test_nota_por_pontos_nos_dois_sentidos():
    crescente = [[0.8, 0], [0.9, 5], [0.97, 9], [0.985, 10]]
    assert nota_por_pontos(1.0, crescente) == 10
    assert nota_por_pontos(0.5, crescente) == 0
    assert nota_por_pontos(0.85, crescente) == 2.5
    decrescente = [[0.1, 10], [0.25, 9], [2.0, 0]]
    assert nota_por_pontos(0.0, decrescente) == 10
    assert nota_por_pontos(0.1, decrescente) == 10
    assert nota_por_pontos(5.0, decrescente) == 0
    assert 9 < nota_por_pontos(0.2, decrescente) < 10


def _melhor_forca_bruta(s):
    n, m = len(s), len(s[0])
    melhor = -1
    if n <= m:
        for perm in itertools.permutations(range(m), n):
            melhor = max(melhor, sum(s[i][perm[i]] for i in range(n)))
    else:
        for perm in itertools.permutations(range(n), m):
            melhor = max(melhor, sum(s[perm[j]][j] for j in range(m)))
    return melhor


@pytest.mark.parametrize("n,m,semente", [(4, 4, 0), (5, 5, 1), (3, 5, 2), (5, 3, 3), (1, 4, 4), (6, 6, 5)])
def test_casamento_otimo_igual_forca_bruta(n, m, semente):
    s = np.random.default_rng(semente).random((n, m)).tolist()
    pares = casamento_otimo(s)
    assert len(pares) == min(n, m)
    assert len({i for i, _ in pares}) == len(pares) == len({j for _, j in pares})
    assert sum(s[i][j] for i, j in pares) == pytest.approx(_melhor_forca_bruta(s))


def test_casamento_acha_troca():
    s = [[1.0, 0.1, 0.2], [0.1, 0.2, 0.95], [0.2, 0.9, 0.1]]
    assert casamento_otimo(s) == [(0, 0), (1, 2), (2, 1)]
    assert casamento_otimo([]) == []
