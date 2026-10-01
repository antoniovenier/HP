"""Ajudantes dos testes do qa_paridade (mídia sintética, datas, relatórios falsos)."""
import shutil
import subprocess
from datetime import datetime

import numpy as np

from hpbase import FUSO

FF = shutil.which("ffmpeg")

SRT_REF = """1
00:00:00,000 --> 00:00:01,200
Olá, pessoal! Hoje tem receita nova.

2
00:00:01,200 --> 00:00:02,400
Bolo de cenoura com cobertura de chocolate

3
00:00:02,400 --> 00:00:03,000
Salva pra não perder!
"""


def ff(*args):
    subprocess.run([FF, "-hide_banner", "-nostdin", "-v", "error", "-y", *map(str, args)],
                   check=True, capture_output=True)


def codec_video():
    saida = subprocess.run([FF, "-hide_banner", "-encoders"], capture_output=True).stdout
    if b"libx264" in saida:
        return ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "18", "-pix_fmt", "yuv420p"]
    return ["-c:v", "mpeg4", "-q:v", "2", "-pix_fmt", "yuv420p"]


def imagem_teste(semente: int, largura: int = 216, altura: int = 270) -> np.ndarray:
    """Lâmina sintética RGB: fundo em degradê + retângulos coloridos da semente."""
    rng = np.random.default_rng(semente)
    y = np.linspace(0, 1, altura)[:, None]
    x = np.linspace(0, 1, largura)[None, :]
    base = np.stack([80 + 120 * y + 0 * x, 60 + 100 * x + 0 * y, 160 - 90 * y + 0 * x], -1)
    img = base.copy()
    for _ in range(14):
        w, h = rng.integers(20, largura // 2), rng.integers(15, altura // 3)
        x0, y0 = rng.integers(0, largura - w), rng.integers(0, altura - h)
        img[y0:y0 + h, x0:x0 + w] = rng.integers(0, 256, 3)
    return np.clip(img, 0, 255).astype(np.uint8)


def salvar_png(arr: np.ndarray, caminho):
    from PIL import Image
    Image.fromarray(arr).save(caminho)
    return caminho


def dia(n: int, hora: int = 10) -> datetime:
    """Setembro/2026, dia n, no fuso de Brasília."""
    return datetime(2026, 9, n, hora, 0, tzinfo=FUSO)


def relatorio_falso(aprovado: bool = True) -> dict:
    """Relatório mínimo e verdadeiro (montado pelo próprio pacote) para a sombra."""
    from qa_paridade import relatorio
    from qa_paridade.limites import carregar_limites
    from qa_paridade.util import metrica
    nota = 10.0 if aprovado else 5.0
    lim = carregar_limites()
    return relatorio.montar("video", {"app": {"arquivo": "app.mp4"}, "ref": {"arquivo": "ref.mp4"}},
                            {"duracao": metrica("duracao", {"diferenca": nota}, {}, "teste")}, lim)
