"""Funções de mídia com ffmpeg (reaproveitáveis por outros módulos).

- info_midia(): duração, resolução, fps, se tem vídeo/áudio. Usa ffprobe se
  existir; se não (plano B), roda `ffmpeg -i arquivo` e lê o texto que o
  ffmpeg escreve no stderr.
- medir_loudness(): loudness integrado (LUFS), pico e LRA via loudnorm.
- extrair_audio(), extrair_quadro(), quadros_revisao(), reduzir_imagem().
- gerar_video_teste(): vídeo sintético (testsrc + sine) para testes.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from hpbase import achar_ffmpeg, achar_ffprobe, mascarar, rodar

from .erros import ErroEtapa, ErroPermanente

RX_DURACAO = re.compile(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")
RX_RESOLUCAO = re.compile(r"[,\s](\d{2,5})x(\d{2,5})(?=[\s,\[]|$)")
RX_FPS = re.compile(r"(\d+(?:\.\d+)?)\s*fps")
RX_TBR = re.compile(r"(\d+(?:\.\d+)?)\s*tbr")


@dataclass
class InfoMidia:
    duracao: float | None = None
    largura: int | None = None
    altura: int | None = None
    fps: float | None = None
    tem_video: bool = False
    tem_audio: bool = False
    codec_video: str | None = None
    codec_audio: str | None = None
    fonte: str = "ffmpeg"

    def como_dict(self) -> dict:
        return asdict(self)


def _cauda(b: bytes | str, linhas: int = 8) -> str:
    txt = b.decode("utf-8", "replace") if isinstance(b, bytes) else str(b)
    return mascarar("\n".join(txt.strip().splitlines()[-linhas:]))


def ffmpeg(args: list, timeout: float = 3600, cwd: Path | None = None,
           o_que: str = "ffmpeg"):
    """Roda o ffmpeg (sem janela) e levanta ErroEtapa com o fim do log se falhar."""
    exe = achar_ffmpeg()
    r = rodar([exe, "-hide_banner", "-nostdin", *args], timeout=timeout, cwd=cwd)
    if r.returncode != 0:
        raise ErroEtapa(f"{o_que} falhou (código {r.returncode}): {_cauda(r.stderr)}")
    return r


def interpretar_saida_ffmpeg(txt: str) -> InfoMidia:
    """Lê o texto de `ffmpeg -i arquivo` (stderr). Função pura (testável)."""
    info = InfoMidia(fonte="ffmpeg")
    m = RX_DURACAO.search(txt)
    if m:
        h, mi, s = m.groups()
        info.duracao = int(h) * 3600 + int(mi) * 60 + float(s)
    for linha in txt.splitlines():
        if "Stream #" not in linha:
            continue
        if ": Video:" in linha and not info.tem_video and "attached pic" not in linha:
            info.tem_video = True
            depois = linha.split(": Video:", 1)[1]
            info.codec_video = depois.strip().split()[0].strip(",") if depois.strip() else None
            r = RX_RESOLUCAO.search(depois)
            if r:
                info.largura, info.altura = int(r.group(1)), int(r.group(2))
            f = RX_FPS.search(depois) or RX_TBR.search(depois)
            if f:
                info.fps = float(f.group(1))
        elif ": Audio:" in linha and not info.tem_audio:
            info.tem_audio = True
            depois = linha.split(": Audio:", 1)[1].strip()
            info.codec_audio = depois.split()[0].strip(",") if depois else None
    return info


def _info_ffprobe(exe: str, arquivo: Path) -> InfoMidia:
    r = rodar([exe, "-v", "error", "-print_format", "json", "-show_format",
               "-show_streams", str(arquivo)], timeout=60)
    if r.returncode != 0:
        raise ValueError(_cauda(r.stderr))
    d = json.loads(r.stdout.decode("utf-8", "replace") or "{}")
    info = InfoMidia(fonte="ffprobe")
    dur = (d.get("format") or {}).get("duration")
    info.duracao = float(dur) if dur not in (None, "N/A") else None
    for s in d.get("streams", []):
        if s.get("codec_type") == "video" and not info.tem_video and \
                not (s.get("disposition") or {}).get("attached_pic"):
            info.tem_video = True
            info.codec_video = s.get("codec_name")
            info.largura, info.altura = s.get("width"), s.get("height")
            taxa = s.get("avg_frame_rate") or s.get("r_frame_rate") or "0/1"
            try:
                n, dd = taxa.split("/")
                info.fps = round(float(n) / float(dd), 3) if float(dd) else None
            except Exception:
                info.fps = None
        elif s.get("codec_type") == "audio" and not info.tem_audio:
            info.tem_audio = True
            info.codec_audio = s.get("codec_name")
    return info


def info_midia(arquivo: Path, usar_ffprobe: bool = True) -> InfoMidia:
    """Informações do arquivo; plano B com `ffmpeg -i` quando não há ffprobe."""
    arquivo = Path(arquivo)
    if not arquivo.exists():
        raise ErroPermanente(f"arquivo não existe: {arquivo.name}")
    probe = achar_ffprobe() if usar_ffprobe else None
    if probe:
        try:
            return _info_ffprobe(probe, arquivo)
        except Exception:
            pass  # cai no plano B
    r = rodar([achar_ffmpeg(), "-hide_banner", "-nostdin", "-i", str(arquivo)],
              timeout=120)
    txt = r.stderr.decode("utf-8", "replace")
    info = interpretar_saida_ffmpeg(txt)
    if not info.tem_video and not info.tem_audio:
        raise ErroPermanente(f"{arquivo.name} não é vídeo/áudio/imagem válido: "
                             f"{_cauda(txt, 2)}")
    return info


def ler_json_loudnorm(txt: str) -> dict:
    """Pega o bloco JSON que o loudnorm (print_format=json) escreve no stderr."""
    blocos = re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", txt, re.S)
    if not blocos:
        raise ErroEtapa("não achei a medição do loudnorm na saída do ffmpeg")
    d = json.loads(blocos[-1])

    def num(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return float("-inf")
    return {k: num(v) if k != "normalization_type" else v for k, v in d.items()}


def medir_loudness(arquivo: Path, alvo: float = -14.0, tp: float = -1.5,
                   lra: float = 11.0) -> dict:
    """Loudness integrado do arquivo (LUFS) e afins, via 1ª passada do loudnorm."""
    r = ffmpeg(["-nostats", "-i", str(arquivo), "-vn", "-af",
                f"loudnorm=I={alvo}:TP={tp}:LRA={lra}:print_format=json",
                "-f", "null", "-"], timeout=900, o_que="medição de loudness")
    return ler_json_loudnorm(r.stderr.decode("utf-8", "replace"))


def extrair_audio(video: Path, saida: Path) -> Path:
    """Áudio mono 16 kHz (o que o faster-whisper usa)."""
    saida = Path(saida)
    tmp = saida.with_name(f"_tmp_{saida.name}")
    ffmpeg(["-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000",
            "-c:a", "pcm_s16le", str(tmp)], timeout=1800, o_que="extração de áudio")
    os.replace(tmp, saida)
    return saida


def extrair_quadro(video: Path, segundo: float, saida: Path,
                   largura: int | None = None) -> Path:
    saida = Path(saida)
    tmp = saida.with_name(f"_tmp_{saida.name}")
    filtro = ["-vf", f"scale={largura}:-2"] if largura else []
    ffmpeg(["-y", "-ss", f"{max(0.0, segundo):.3f}", "-i", str(video),
            "-frames:v", "1", *filtro, "-q:v", "3", str(tmp)],
           timeout=120, o_que="extração de quadro")
    if not tmp.exists():
        raise ErroEtapa(f"o ffmpeg não gerou o quadro de {segundo:.1f}s")
    os.replace(tmp, saida)
    return saida


def tempos_quadros(duracao: float) -> list[float]:
    """Início, meio e fim (um pouco para dentro, para não pegar tela preta)."""
    d = max(float(duracao or 0), 0.1)
    borda = min(1.0, d * 0.1)
    return [round(borda, 3), round(d / 2, 3), round(max(0.0, d - borda), 3)]


def quadros_revisao(video: Path, pasta: Path, largura: int = 540) -> list[dict]:
    """3 quadros jpg (início/meio/fim) para o revisor olhar."""
    info = info_midia(video)
    nomes = ("quadro_1_inicio.jpg", "quadro_2_meio.jpg", "quadro_3_fim.jpg")
    saida = []
    for nome, t in zip(nomes, tempos_quadros(info.duracao or 0)):
        extrair_quadro(video, t, Path(pasta) / nome, largura)
        saida.append({"arquivo": nome, "segundo": t})
    return saida


def reduzir_imagem(imagem: Path, saida: Path, largura: int = 540) -> Path:
    saida = Path(saida)
    tmp = saida.with_name(f"_tmp_{saida.name}")
    ffmpeg(["-y", "-i", str(imagem), "-vf", f"scale={largura}:-2", "-frames:v", "1",
            "-q:v", "3", str(tmp)], timeout=120, o_que="redução de imagem")
    os.replace(tmp, saida)
    return saida


def gerar_video_teste(saida: Path, duracao: float = 2.0, largura: int = 320,
                      altura: int = 180, audio: bool = True, freq: int = 440,
                      volume: float = 0.5) -> Path:
    """Vídeo sintético (barras testsrc + tom sine) para testes e diagnóstico."""
    args = ["-y", "-f", "lavfi", "-i",
            f"testsrc=size={largura}x{altura}:rate=25:duration={duracao}"]
    if audio:
        args += ["-f", "lavfi", "-i", f"sine=frequency={freq}:duration={duracao}"]
        args += ["-af", f"volume={volume}"]
    args += ["-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p"]
    if audio:
        args += ["-c:a", "aac", "-shortest"]
    args.append(str(saida))
    ffmpeg(args, timeout=120, o_que="vídeo de teste")
    return Path(saida)


def gerar_audio_teste(saida: Path, duracao: float = 1.0, freq: int = 660) -> Path:
    ffmpeg(["-y", "-f", "lavfi", "-i", f"sine=frequency={freq}:duration={duracao}",
            "-ac", "2", "-ar", "48000", str(saida)], timeout=60, o_que="áudio de teste")
    return Path(saida)


class MidiaFFmpeg:
    """Plugin de mídia (conferência do bruto, áudio, quadros) com ffmpeg real."""

    def info(self, arquivo: Path) -> dict:
        return info_midia(arquivo).como_dict()

    def extrair_audio(self, video: Path, saida: Path) -> Path:
        return extrair_audio(video, saida)

    def quadros(self, video: Path, pasta: Path, largura: int = 540) -> list[dict]:
        return quadros_revisao(video, pasta, largura)

    def reduzir_imagem(self, imagem: Path, saida: Path, largura: int = 540) -> Path:
        return reduzir_imagem(imagem, saida, largura)

    def loudness(self, arquivo: Path) -> float | None:
        try:
            v = medir_loudness(arquivo)["input_i"]
            return None if v == float("-inf") else round(v, 2)
        except Exception:
            return None
