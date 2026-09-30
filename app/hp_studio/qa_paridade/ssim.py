"""SSIM (índice de similaridade estrutural) feito à mão com numpy.

Fórmula de Wang, Bovik, Sheikh e Simoncelli (2004), com janela gaussiana
7x7 e sigma 1,5 (a mesma ideia do artigo original, só com a janela menor
para ficar rápido). Não depende de scikit-image nem de scipy.

    SSIM(x, y) = (2·μx·μy + C1)(2·σxy + C2) / ((μx² + μy² + C1)(σx² + σy² + C2))

- μ = média local (ponderada pela janela gaussiana)
- σ² = variância local, σxy = covariância local
- C1 = (0,01·L)², C2 = (0,03·L)², L = 255 para imagem de 8 bits

O resultado vai de -1 a 1: 1,0 = imagens iguais pixel a pixel. A conta é
feita só onde a janela cabe inteira (sem borda inventada).
"""
from __future__ import annotations

import numpy as np

K1 = 0.01
K2 = 0.03
FAIXA_8BITS = 255.0

LINHAS_REGIAO = ("topo", "meio", "base")
COLUNAS_REGIAO = ("esquerda", "centro", "direita")


def janela_gaussiana(tamanho: int = 7, sigma: float = 1.5) -> np.ndarray:
    """Núcleo gaussiano 1D normalizado (soma 1). O 2D é o produto externo."""
    x = np.arange(tamanho, dtype=np.float64) - (tamanho - 1) / 2.0
    g = np.exp(-(x ** 2) / (2.0 * sigma ** 2))
    return g / g.sum()


def _filtrar(img: np.ndarray, g: np.ndarray) -> np.ndarray:
    """Convolução separável 'valid' nas duas últimas dimensões.

    Soma deslocada (shift-and-add): para cada peso g[k] soma a fatia
    deslocada de k pixels. Funciona também para lote (N, A, L).
    """
    t = len(g)
    alt, larg = img.shape[-2], img.shape[-1]
    sl = larg - t + 1
    horiz = g[0] * img[..., :, 0:sl]
    for k in range(1, t):
        horiz = horiz + g[k] * img[..., :, k:k + sl]
    sa = alt - t + 1
    saida = g[0] * horiz[..., 0:sa, :]
    for k in range(1, t):
        saida = saida + g[k] * horiz[..., k:k + sa, :]
    return saida


def ssim_mapa(a, b, tamanho: int = 7, sigma: float = 1.5,
              faixa: float = FAIXA_8BITS) -> np.ndarray:
    """Mapa de SSIM local (uma nota por posição da janela)."""
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    if a.shape != b.shape:
        raise ValueError(f"imagens com tamanhos diferentes: {a.shape} x {b.shape}")
    if a.ndim < 2 or min(a.shape[-2:]) < tamanho:
        raise ValueError(f"imagem menor que a janela de {tamanho}x{tamanho}")
    g = janela_gaussiana(tamanho, sigma)
    c1 = (K1 * faixa) ** 2
    c2 = (K2 * faixa) ** 2
    mu_a = _filtrar(a, g)
    mu_b = _filtrar(b, g)
    mu_aa = mu_a * mu_a
    mu_bb = mu_b * mu_b
    mu_ab = mu_a * mu_b
    var_a = _filtrar(a * a, g) - mu_aa
    var_b = _filtrar(b * b, g) - mu_bb
    cov_ab = _filtrar(a * b, g) - mu_ab
    num = (2.0 * mu_ab + c1) * (2.0 * cov_ab + c2)
    den = (mu_aa + mu_bb + c1) * (var_a + var_b + c2)
    return num / den


def ssim(a, b, tamanho: int = 7, sigma: float = 1.5,
         faixa: float = FAIXA_8BITS) -> float:
    """SSIM médio entre duas imagens em escala de cinza do mesmo tamanho."""
    return float(ssim_mapa(a, b, tamanho, sigma, faixa).mean())


def ssim_com_regiao(a, b, tamanho: int = 7, sigma: float = 1.5) -> tuple[float, str]:
    """SSIM médio e o nome da pior região (grade 3x3, ex.: 'topo-direita')."""
    mapa = ssim_mapa(a, b, tamanho, sigma)
    return float(mapa.mean()), pior_regiao(mapa)


def pior_regiao(mapa: np.ndarray) -> str:
    """Divide o mapa em 3x3 e devolve a região com menor SSIM médio."""
    faixas_l = np.array_split(np.arange(mapa.shape[0]), 3)
    faixas_c = np.array_split(np.arange(mapa.shape[1]), 3)
    pior, nome = None, ""
    for i, fl in enumerate(faixas_l):
        for j, fc in enumerate(faixas_c):
            if len(fl) == 0 or len(fc) == 0:
                continue
            m = float(mapa[fl[0]:fl[-1] + 1, fc[0]:fc[-1] + 1].mean())
            if pior is None or m < pior:
                pior, nome = m, f"{LINHAS_REGIAO[i]}-{COLUNAS_REGIAO[j]}"
    return nome
