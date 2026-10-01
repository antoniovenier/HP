"""Leitura de mídia só com o ffmpeg (o ffprobe pode não existir).

- `info_midia`: duração, largura, altura, fps, áudio e legenda lendo o
  texto que o `ffmpeg -i arquivo` escreve no stderr (plano B: decodificar
  tudo e ler o tempo final do `-progress`).
- `extrair_quadros`: quadros em escala de cinza, reduzidos, alinhados por
  tempo, vindos pelo pipe como rawvideo (nada vai para o disco).
- `ler_imagem_cinza`: arte/lâmina com Pillow (plano B: ffmpeg).
- `extrair_legenda_srt`: primeira faixa de legenda de um vídeo como texto SRT.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from fractions import Fraction
from pathlib import Path

import numpy as np

from hpbase import achar_ffmpeg, mascarar, rodar

EXT_IMAGEM = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff"}
EXT_LEGENDA = {".srt", ".ass", ".ssa", ".vtt"}


class ErroMidia(RuntimeError):
    """O ffmpeg não conseguiu ler o arquivo (corrompido, formato estranho...)."""


@dataclass
class InfoMidia:
    arquivo: str
    duracao: float | None = None
    largura: int | None = None
    altura: int | None = None
    fps: float | None = None
    tem_video: bool = False
    tem_audio: bool = False
    tem_legenda: bool = False
    codec_video: str | None = None
    codec_audio: str | None = None
    rotacao: int = 0

    def como_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------- ffmpeg -i
_RX_DUR = re.compile(r"Duration:\s*(\d+):(\d{2}):(\d{2}(?:\.\d+)?)")
_RX_STREAM = re.compile(
    r"Stream\s+#\d+:\d+(?:\[[^\]]*\])?(?:\([^)]*\))?\s*:\s*"
    r"(Video|Audio|Subtitle|Data|Attachment)\s*:\s*(.*)")
_RX_DIM = re.compile(r",\s*(\d{2,5})x(\d{2,5})(?![\dx])")
_RX_FPS = re.compile(r"(\d+(?:\.\d+)?)\s*fps\b")
_RX_TBR = re.compile(r"(\d+(?:\.\d+)?)(k?)\s*tbr\b")
_RX_ROT = re.compile(r"rotation of\s*(-?\d+(?:\.\d+)?)\s*degrees|\brotate\s*:\s*(-?\d+)")
_FIM_ENTRADA = ("Input #1", "Output #", "Stream mapping", "At least one output")


def _secao_entrada(texto: str) -> str:
    """Só o pedaço do stderr que descreve o primeiro arquivo (Input #0)."""
    linhas = texto.splitlines()
    ini = next((i for i, l in enumerate(linhas) if l.lstrip().startswith("Input #0")), 0)
    saida = []
    for l in linhas[ini:]:
        if saida and any(l.lstrip().startswith(m) for m in _FIM_ENTRADA):
            break
        saida.append(l)
    return "\n".join(saida)


def interpretar_info_ffmpeg(texto: str, arquivo: str = "") -> InfoMidia:
    """Transforma o stderr do `ffmpeg -i` em InfoMidia (função pura, testável)."""
    sec = _secao_entrada(texto)
    info = InfoMidia(arquivo=str(arquivo))
    m = _RX_DUR.search(sec)
    if m:
        info.duracao = round(int(m.group(1)) * 3600 + int(m.group(2)) * 60
                             + float(m.group(3)), 3)
    for tipo, resto in _RX_STREAM.findall(sec):
        if tipo == "Video":
            if "attached pic" in resto or info.tem_video:
                continue  # capa de mp3/m4a não é vídeo; só a 1ª faixa conta
            info.tem_video = True
            info.codec_video = resto.split(",")[0].split()[0] if resto.strip() else None
            d = _RX_DIM.search(resto)
            if d:
                info.largura, info.altura = int(d.group(1)), int(d.group(2))
            f = _RX_FPS.search(resto)
            if f:
                info.fps = float(f.group(1))
            else:
                t = _RX_TBR.search(resto)
                if t:
                    info.fps = float(t.group(1)) * (1000 if t.group(2) else 1)
        elif tipo == "Audio" and not info.tem_audio:
            info.tem_audio = True
            info.codec_audio = resto.split(",")[0].split()[0] if resto.strip() else None
        elif tipo == "Subtitle":
            info.tem_legenda = True
    r = _RX_ROT.search(sec)
    if r:
        # "rotate: 90" (metadado antigo) = "rotation of -90.00 degrees" (displaymatrix)
        graus = (int(round(-float(r.group(1)))) if r.group(1) else int(r.group(2))) % 360
        info.rotacao = graus
        if graus in (90, 270) and info.largura and info.altura:
            # o ffmpeg gira sozinho ao decodificar: o quadro sai "em pé"
            info.largura, info.altura = info.altura, info.largura
    return info


def _decodificar(saida: bytes) -> str:
    return saida.decode("utf-8", errors="replace")


def _conferir_arquivo(arquivo) -> Path:
    p = Path(arquivo)
    if not p.is_file():
        raise FileNotFoundError(f"arquivo não encontrado: {p}")
    return p


def _duracao_decodificando(arquivo: Path, ffmpeg: str, timeout: float) -> float | None:
    """Plano B: decodifica tudo e pega o maior out_time do -progress."""
    cmd = [ffmpeg, "-hide_banner", "-nostdin", "-v", "error", "-i", str(arquivo),
           "-map", "0:v?", "-map", "0:a?", "-f", "null", "-",
           "-progress", "pipe:1", "-nostats"]
    r = rodar(cmd, timeout=timeout)
    tempos = [int(x) for x in re.findall(r"out_time_us=(\d+)", _decodificar(r.stdout))]
    if not tempos:
        tempos = [int(x) * 1000 for x in re.findall(r"out_time_ms=(\d+)", _decodificar(r.stdout))]
    return round(max(tempos) / 1_000_000, 3) if tempos and max(tempos) > 0 else None


def info_midia(arquivo, ffmpeg: str | None = None, timeout: float = 120) -> InfoMidia:
    """Duração (s), dimensões, fps, áudio e legenda — só com o ffmpeg."""
    p = _conferir_arquivo(arquivo)
    ff = ffmpeg or achar_ffmpeg()
    r = rodar([ff, "-hide_banner", "-nostdin", "-i", str(p)], timeout=timeout)
    texto = _decodificar(r.stderr)
    info = interpretar_info_ffmpeg(texto, str(p))
    if not (info.tem_video or info.tem_audio):
        final = texto.strip().splitlines()[-1:] or [""]
        raise ErroMidia(mascarar(f"ffmpeg não leu {p.name}: {final[0][:200]}"))
    eh_imagem = p.suffix.lower() in EXT_IMAGEM
    if info.duracao is None and not eh_imagem:
        info.duracao = _duracao_decodificando(p, ff, timeout)
    return info


# ---------------------------------------------------------------- quadros
def tamanho_reduzido(largura: int | None, altura: int | None,
                     lado_max: int = 480) -> tuple[int, int]:
    """Tamanho reduzido mantendo a proporção, par, sem nunca aumentar.

    1080x1920 -> 270x480 (padrão). Sem dimensões conhecidas -> 270x480.
    """
    if not largura or not altura:
        return 270, 480
    fator = min(1.0, float(lado_max) / max(largura, altura))
    w = max(16, int(round(largura * fator / 2.0)) * 2)
    h = max(16, int(round(altura * fator / 2.0)) * 2)
    return w, h


def tempos_das_amostras(passo: float, quantidade: int) -> list[float]:
    """Tempo (s) de cada quadro devolvido por `extrair_quadros`: o centro de
    cada fatia de `passo` segundos -> (k + 0,5)·passo."""
    return [round((k + 0.5) * passo, 3) for k in range(int(quantidade))]


def extrair_quadros(arquivo, largura: int, altura: int, passo: float,
                    quantidade: int, ffmpeg: str | None = None,
                    timeout: float = 900) -> np.ndarray:
    """Quadros em cinza (N, altura, largura) nos tempos (k + 0,5)·passo.

    Filtro `fps` com taxa racional exata 1/passo (arredondamento "near"):
    a saída k recebe o quadro que está na tela logo antes de (k + 0,5)·passo
    — o mesmo instante nos dois vídeos, mesmo com fps diferentes (erro de no
    máximo 1 quadro). Depois `scale` (área) e `format=gray`; tudo pelo pipe.
    Pode devolver menos quadros que o pedido se o vídeo acabar antes.
    """
    p = _conferir_arquivo(arquivo)
    ff = ffmpeg or achar_ffmpeg()
    taxa = Fraction(1.0 / passo).limit_denominator(1000)
    filtro = (f"fps=fps={taxa.numerator}/{taxa.denominator},"
              f"scale={largura}:{altura}:flags=area,format=gray")
    cmd = [ff, "-hide_banner", "-nostdin", "-v", "error", "-i", str(p),
           "-map", "0:v:0", "-an", "-sn", "-dn", "-vf", filtro,
           "-frames:v", str(int(quantidade)),
           "-f", "rawvideo", "-pix_fmt", "gray", "pipe:1"]
    r = rodar(cmd, timeout=timeout)
    if r.returncode != 0:
        erro = _decodificar(r.stderr).strip().splitlines()[-1:] or ["?"]
        raise ErroMidia(mascarar(f"falha ao extrair quadros de {p.name}: {erro[0][:200]}"))
    tam = largura * altura
    n = len(r.stdout) // tam
    return np.frombuffer(r.stdout[:n * tam], dtype=np.uint8).reshape(n, altura, largura)


# ---------------------------------------------------------------- imagem
def _para_cinza(im):
    from PIL import Image, ImageOps
    im = ImageOps.exif_transpose(im)
    if im.mode in ("RGBA", "LA", "PA") or (im.mode == "P" and "transparency" in im.info):
        im = im.convert("RGBA")
        fundo = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(fundo, im)  # transparente conta como branco
    return im.convert("L")


def dimensoes_imagem(arquivo) -> tuple[int, int]:
    """(largura, altura) já considerando a rotação EXIF."""
    p = _conferir_arquivo(arquivo)
    try:
        from PIL import Image, ImageOps
        with Image.open(p) as im:
            im = ImageOps.exif_transpose(im)
            return im.size
    except Exception:
        info = info_midia(p)
        if not info.largura:
            raise ErroMidia(f"não consegui ler as dimensões de {p.name}")
        return info.largura, info.altura


def ler_imagem_cinza(arquivo, largura: int | None = None,
                     altura: int | None = None) -> np.ndarray:
    """Imagem em cinza (uint8), opcionalmente reduzida para largura x altura."""
    p = _conferir_arquivo(arquivo)
    try:
        from PIL import Image
        with Image.open(p) as im:
            cinza = _para_cinza(im)
            if largura and altura and cinza.size != (largura, altura):
                cinza = cinza.resize((largura, altura), Image.Resampling.BOX)
            return np.asarray(cinza, dtype=np.uint8).copy()
    except (ImportError, OSError):
        pass
    # plano B: o ffmpeg lê quase tudo (avif, heic com build completa...)
    if not (largura and altura):
        largura, altura = dimensoes_imagem(p)
    return extrair_quadros_imagem_ffmpeg(p, largura, altura)


def extrair_quadros_imagem_ffmpeg(arquivo, largura: int, altura: int,
                                  ffmpeg: str | None = None) -> np.ndarray:
    ff = ffmpeg or achar_ffmpeg()
    cmd = [ff, "-hide_banner", "-nostdin", "-v", "error", "-i", str(arquivo),
           "-frames:v", "1", "-vf", f"scale={largura}:{altura}:flags=area,format=gray",
           "-f", "rawvideo", "-pix_fmt", "gray", "pipe:1"]
    r = rodar(cmd, timeout=120)
    if r.returncode != 0 or len(r.stdout) < largura * altura:
        raise ErroMidia(f"não consegui ler a imagem {Path(arquivo).name}")
    return np.frombuffer(r.stdout[:largura * altura], dtype=np.uint8).reshape(altura, largura).copy()


# ---------------------------------------------------------------- legenda
def extrair_legenda_srt(arquivo, ffmpeg: str | None = None, timeout: float = 120) -> str | None:
    """Primeira faixa de legenda do vídeo convertida para SRT (None se não há)."""
    p = _conferir_arquivo(arquivo)
    ff = ffmpeg or achar_ffmpeg()
    cmd = [ff, "-hide_banner", "-nostdin", "-v", "error", "-i", str(p),
           "-map", "0:s:0", "-f", "srt", "pipe:1"]
    r = rodar(cmd, timeout=timeout)
    if r.returncode != 0:
        return None
    return r.stdout.decode("utf-8", errors="replace")
