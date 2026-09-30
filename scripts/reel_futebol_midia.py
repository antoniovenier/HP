"""ffmpeg do montador de reels do Futebol | HP.

- medir mídia SEM ffprobe (lê o stderr do `ffmpeg -i`): duração, tamanho,
  áudio, volume, loudness;
- segmentos: SegQuadros (quadros desenhados no Pillow, enviados por pipe) e
  SegClipe (vídeo oficial + moldura PNG + legendas PNG, com o áudio original);
- montagem final: emenda os segmentos com cópia do vídeo (sem recodificar)
  e trata o áudio (loudnorm em 2 passadas a -14 LUFS + música livre baixa).
"""
from __future__ import annotations

import io
import json
import math
import os
import re
import shlex
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image

from reel_futebol_arte import Sprite, compor, hex_ffmpeg
from reel_futebol_base import (ALTURA, FPS, LARGURA, SEM_JANELA, TAXA_AUDIO,
                               ErroReel, achar_ffmpeg, dur_exata, log,
                               n_quadros, rodar)


def ffmpeg() -> str:
    return achar_ffmpeg()


def texto_comando(cmd) -> str:
    """Comando pronto para colar no terminal (PowerShell/cmd ou bash)."""
    cmd = [str(c) for c in cmd]
    return subprocess.list2cmdline(cmd) if os.name == "nt" else shlex.join(cmd)


# --------------------------------------------------------------- orçamento
class Orcamento:
    """Limite de tempo do render inteiro (padrão 10 min)."""

    def __init__(self, limite_s: float = 600):
        self.limite = float(limite_s)
        self.ini = time.monotonic()

    @property
    def gasto(self) -> float:
        return time.monotonic() - self.ini

    def restante(self) -> float:
        return self.limite - self.gasto

    def conferir(self, onde: str = "") -> None:
        if self.restante() <= 0:
            raise ErroReel(f"render passou do limite de {self.limite / 60:.0f} min"
                           + (f" ({onde})" if onde else ""))


def rodar_ffmpeg(cmd, orc: Orcamento | None = None, onde: str = "ffmpeg",
                 timeout: float | None = None) -> subprocess.CompletedProcess:
    lim = timeout
    if orc is not None:
        orc.conferir(onde)
        lim = orc.restante() if lim is None else min(lim, orc.restante())
    try:
        r = rodar(cmd, timeout=lim)
    except subprocess.TimeoutExpired as e:
        raise ErroReel(f"{onde}: passou do tempo limite") from e
    if r.returncode != 0:
        linhas = r.stderr.decode("utf-8", "replace").strip().splitlines()
        raise ErroReel(f"{onde}: ffmpeg falhou (código {r.returncode}): "
                       + " | ".join(linhas[-6:]))
    return r


# -------------------------------------------------------- medir sem ffprobe
_RX_DUR = re.compile(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")
_RX_STREAM = re.compile(r"Stream #\d+:\d+.*?: (Video|Audio): (\w+)(.*)")
_RX_TAM = re.compile(r"(?<![\w])(\d{2,5})x(\d{2,5})(?![\w])")
_RX_FPS = re.compile(r"(\d+(?:\.\d+)?)\s*fps")
_RX_TBR = re.compile(r"(\d+(?:\.\d+)?)\s*tbr")
_RX_HZ = re.compile(r"(\d+)\s*Hz")
_RX_PIX = re.compile(r"\b(yuvj?\d{3}p\w*|yuva\d{3}p\w*|rgba?\d*|bgra?\d*|gray\w*|nv\d+|pal8)\b")
_RX_ROT = re.compile(r"rotation of (-?\d+(?:\.\d+)?) degrees")
_RX_ROTATE = re.compile(r"^\s*rotate\s*:\s*(-?\d+)", re.M)


def info_midia(caminho) -> dict:
    """Duração, tamanho e áudio de um arquivo usando só o `ffmpeg -i`."""
    p = Path(caminho)
    if not p.exists():
        raise ErroReel(f"arquivo não encontrado: {p}")
    r = rodar([ffmpeg(), "-hide_banner", "-nostdin", "-i", str(p)], timeout=60)
    txt = r.stderr.decode("utf-8", "replace")
    if "Input #0" not in txt:
        raise ErroReel(f"não é um arquivo de mídia válido: {p.name}")
    info = {"duracao": None, "largura": None, "altura": None, "fps": None,
            "tem_video": False, "tem_audio": False, "codec_video": None,
            "codec_audio": None, "taxa_audio": None, "canais": None,
            "pix_fmt": None, "rotacao": 0}
    m = _RX_DUR.search(txt)
    if m:
        info["duracao"] = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    for linha in txt.splitlines():
        ms = _RX_STREAM.search(linha)
        if not ms:
            continue
        tipo, codec, resto = ms.groups()
        if tipo == "Video" and not info["tem_video"] and "attached pic" not in resto:
            info["tem_video"] = True
            info["codec_video"] = codec
            mt = _RX_TAM.search(resto)
            if mt:
                info["largura"], info["altura"] = int(mt.group(1)), int(mt.group(2))
            mf = _RX_FPS.search(resto) or _RX_TBR.search(resto)
            if mf:
                info["fps"] = float(mf.group(1))
            mp = _RX_PIX.search(resto)
            if mp:
                info["pix_fmt"] = mp.group(1)
        elif tipo == "Audio" and not info["tem_audio"]:
            info["tem_audio"] = True
            info["codec_audio"] = codec
            mh = _RX_HZ.search(resto)
            if mh:
                info["taxa_audio"] = int(mh.group(1))
            if "stereo" in resto:
                info["canais"] = 2
            elif "mono" in resto:
                info["canais"] = 1
    mr = _RX_ROT.search(txt) or _RX_ROTATE.search(txt)
    if mr:
        info["rotacao"] = int(round(float(mr.group(1)))) % 360
        if info["rotacao"] in (90, 270) and info["largura"]:
            info["largura"], info["altura"] = info["altura"], info["largura"]
    return info


def _num(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return float("-inf")


def medir_volume(caminho, inicio: float | None = None,
                 duracao: float | None = None) -> dict:
    """Volume médio e pico (dB) via volumedetect. Sem áudio = -inf."""
    cmd = [ffmpeg(), "-hide_banner", "-nostdin"]
    if inicio:
        cmd += ["-ss", f"{inicio:.3f}"]
    if duracao:
        cmd += ["-t", f"{duracao:.3f}"]
    cmd += ["-i", str(caminho), "-vn", "-af", "volumedetect", "-f", "null", "-"]
    r = rodar(cmd, timeout=300)
    txt = r.stderr.decode("utf-8", "replace")
    media = re.search(r"mean_volume:\s*(-?[\d.]+|-inf)\s*dB", txt)
    pico = re.search(r"max_volume:\s*(-?[\d.]+|-inf)\s*dB", txt)
    return {"media_db": _num(media.group(1)) if media else float("-inf"),
            "pico_db": _num(pico.group(1)) if pico else float("-inf")}


def medir_loudness(entrada: list, estilo: dict, orc: Orcamento | None = None,
                   onde: str = "loudnorm (passada 1)") -> dict | None:
    """1ª passada do loudnorm: devolve input_i/tp/lra/thresh e offset."""
    cmd = [ffmpeg(), "-hide_banner", "-nostdin", *entrada, "-vn", "-af",
           f"loudnorm=I={estilo['alvo_lufs']}:TP={estilo['true_peak']}:"
           f"LRA={estilo['lra']}:print_format=json", "-f", "null", "-"]
    r = rodar_ffmpeg(cmd, orc, onde)
    txt = r.stderr.decode("utf-8", "replace")
    ini, fim = txt.rfind("{"), txt.rfind("}")
    if ini < 0 or fim < ini:
        return None
    try:
        d = json.loads(txt[ini:fim + 1])
    except json.JSONDecodeError:
        return None
    return {k: _num(d.get(k)) for k in ("input_i", "input_tp", "input_lra",
                                        "input_thresh", "target_offset")}


def loudness_arquivo(caminho, estilo: dict) -> float:
    med = medir_loudness(["-i", str(caminho)], estilo, onde="medir loudness")
    return med["input_i"] if med else float("-inf")


def extrair_quadro(caminho, t: float) -> Image.Image:
    """Um quadro do vídeo no instante t (RGB)."""
    r = rodar([ffmpeg(), "-v", "error", "-nostdin", "-ss", f"{t:.3f}", "-i",
               str(caminho), "-frames:v", "1", "-f", "image2pipe", "-vcodec",
               "png", "-"], timeout=60)
    if r.returncode != 0 or not r.stdout:
        raise ErroReel(f"não consegui extrair quadro em {t:.2f}s de {caminho}")
    return Image.open(io.BytesIO(r.stdout)).convert("RGB")


def extrair_audio(caminho, inicio: float = 0.0, duracao: float | None = None,
                  taxa: int = TAXA_AUDIO) -> np.ndarray:
    """Amostras mono float32 (-1..1) de um trecho do arquivo."""
    cmd = [ffmpeg(), "-v", "error", "-nostdin", "-ss", f"{inicio:.3f}"]
    if duracao:
        cmd += ["-t", f"{duracao:.3f}"]
    cmd += ["-i", str(caminho), "-vn", "-ac", "1", "-ar", str(taxa), "-f", "s16le", "-"]
    r = rodar(cmd, timeout=120)
    return np.frombuffer(r.stdout, dtype="<i2").astype(np.float32) / 32768.0


# --------------------------------------------------------------- codificar
VF_RGB_BT709 = "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p"
TAGS_COR = ["-colorspace", "bt709", "-color_primaries", "bt709",
            "-color_trc", "bt709", "-color_range", "tv"]
ENC_AUDIO_PCM = ["-c:a", "pcm_s16le", "-ar", str(TAXA_AUDIO), "-ac", "2"]


def enc_video(estilo: dict) -> list:
    """Parâmetros IGUAIS em todos os segmentos (a emenda final copia o vídeo)."""
    v = estilo.get("video", {})
    return ["-c:v", "libx264", "-preset", str(v.get("preset", "veryfast")),
            "-crf", str(v.get("crf", 20)), "-profile:v", "high", "-level:v", "4.0",
            "-pix_fmt", "yuv420p", "-r", str(FPS), "-g", str(FPS * 2), *TAGS_COR]


def _popen_ffmpeg(cmd, arq_erro):
    kw = {}
    if os.name == "nt":  # nunca abrir janela preta
        kw["creationflags"] = SEM_JANELA
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        kw["startupinfo"] = si
    return subprocess.Popen([str(c) for c in cmd], stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=arq_erro, **kw)


def _par(v: float) -> int:
    return max(2, int(round(v / 2.0)) * 2)


# --------------------------------------------------------------- segmentos
@dataclass
class SegQuadros:
    """Trecho desenhado no Pillow (cartão, fotos com zoom, contador...).

    gerador(t) devolve o quadro RGB 1080x1920 do instante t; chave(t) (opcional)
    diz quando o quadro não mudou (reaproveita os bytes, fica mais rápido).
    O áudio deste trecho é silêncio (a música entra só na montagem final).
    """
    nome: str
    duracao: float
    gerador: Callable[[float], Image.Image]
    chave: Callable[[float], object] | None = None
    tem_audio: bool = False
    descricao: str = ""

    def comando(self, saida: Path, estilo: dict, pasta: Path | None = None) -> list:
        d = dur_exata(self.duracao)
        return [ffmpeg(), "-y", "-hide_banner", "-nostdin", "-loglevel", "error",
                "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{LARGURA}x{ALTURA}",
                "-framerate", str(FPS), "-i", "-",
                "-f", "lavfi", "-i", f"anullsrc=r={TAXA_AUDIO}:cl=stereo",
                "-map", "0:v", "-map", "1:a", "-vf", VF_RGB_BT709,
                *enc_video(estilo), *ENC_AUDIO_PCM, "-t", f"{d:.3f}", str(saida)]

    def render(self, saida: Path, estilo: dict, orc: Orcamento, pasta: Path) -> Path:
        n = n_quadros(self.duracao)
        cmd = self.comando(saida, estilo)
        with tempfile.TemporaryFile(dir=pasta) as err:
            proc = _popen_ffmpeg(cmd, err)
            ult_chave, ult_bytes = object(), None
            try:
                for i in range(n):
                    if i % 10 == 0:
                        orc.conferir(self.nome)
                    t = i / FPS
                    k = self.chave(t) if self.chave else None
                    if self.chave is None or ult_bytes is None or k != ult_chave:
                        img = self.gerador(t)
                        if img.mode != "RGB":
                            img = img.convert("RGB")
                        if img.size != (LARGURA, ALTURA):
                            raise ErroReel(f"{self.nome}: quadro com tamanho {img.size}")
                        ult_bytes, ult_chave = img.tobytes(), k
                    proc.stdin.write(ult_bytes)
                proc.stdin.close()
                cod = proc.wait(timeout=max(5.0, orc.restante()))
            except BrokenPipeError:
                cod = proc.wait()
            except BaseException:
                proc.kill()
                proc.wait()
                raise
            if cod != 0:
                err.seek(0)
                cauda = err.read().decode("utf-8", "replace").strip().splitlines()[-6:]
                raise ErroReel(f"{self.nome}: ffmpeg falhou (código {cod}): " + " | ".join(cauda))
        return saida


@dataclass
class SegClipe:
    """Vídeo (oficial) com moldura PNG por cima e o ÁUDIO ORIGINAL.

    janela = (x, y, largura, altura) onde o vídeo aparece; ajuste
    "encaixar" mostra o vídeo inteiro (sem cortar), "cobrir" preenche a
    janela cortando as sobras. moldura() devolve um RGBA 1080x1920 (texto,
    caixas, crédito); temporizados = [(fn -> Sprite, inicio, fim)].
    """
    nome: str
    arquivo: Path
    inicio: float
    duracao: float
    tam_origem: tuple
    janela: tuple = (0, 0, LARGURA, ALTURA)
    ajuste: str = "encaixar"
    cor_fundo: str = "#000000"
    moldura: Callable[[], Image.Image] | None = None
    temporizados: list = field(default_factory=list)
    tem_audio: bool = True
    descricao: str = ""

    def geometria(self) -> dict:
        x, y, w, h = self.janela
        ow, oh = self.tam_origem
        if self.ajuste == "cobrir":
            k = max(w / ow, h / oh)
            cw, ch = w - w % 2, h - h % 2
            sw, sh = max(_par(ow * k), cw), max(_par(oh * k), ch)
            px, py = (x // 2) * 2, (y // 2) * 2
            return {"escala": (sw, sh), "corte": (cw, ch, (sw - cw) // 2, (sh - ch) // 2),
                    "pos": (px, py), "vis": (px, py, cw, ch)}
        k = min(w / ow, h / oh)
        sw = min(_par(ow * k), w - w % 2)
        sh = min(_par(oh * k), h - h % 2)
        px = ((x + (w - sw) // 2) // 2) * 2
        py = ((y + (h - sh) // 2) // 2) * 2
        return {"escala": (sw, sh), "corte": None, "pos": (px, py), "vis": (px, py, sw, sh)}

    def _arquivos(self, pasta: Path) -> tuple[Path, list[Path]]:
        return (pasta / f"{self.nome}_moldura.png",
                [pasta / f"{self.nome}_leg{i:02d}.png" for i in range(len(self.temporizados))])

    def preparar(self, pasta: Path) -> None:
        mold, legs = self._arquivos(pasta)
        img = self.moldura() if self.moldura else Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, 0))
        img.save(mold)
        self._pos_leg = []
        for (fn, _a, _b), arq in zip(self.temporizados, legs):
            s: Sprite = fn()
            s.img.save(arq)
            self._pos_leg.append((s.x, s.y))

    def comando(self, saida: Path, estilo: dict, pasta: Path) -> list:
        d = dur_exata(self.duracao)
        mold, legs = self._arquivos(pasta)
        g = self.geometria()
        sw, sh = g["escala"]
        px, py = g["pos"]
        cadeia = f"[0:v]setpts=PTS-STARTPTS,fps={FPS},scale={sw}:{sh}:flags=bicubic"
        if g["corte"]:
            cw, ch, cx, cy = g["corte"]
            cadeia += f",crop={cw}:{ch}:{cx}:{cy}"
        cadeia += (f",setsar=1,pad={LARGURA}:{ALTURA}:{px}:{py}:color={hex_ffmpeg(self.cor_fundo)}"
                   f",tpad=stop_mode=clone:stop_duration={d:.3f}[b0]")
        partes = [cadeia,
                  "[1:v]format=rgba,scale=out_color_matrix=bt709:out_range=tv,format=yuva420p[m0]",
                  "[b0][m0]overlay=0:0:format=yuv420[b1]"]
        pos = getattr(self, "_pos_leg", None) or [(0, 0)] * len(legs)
        atual = "b1"
        for i, ((_fn, a, b), (lx, ly)) in enumerate(zip(self.temporizados, pos)):
            partes.append(f"[{i + 2}:v]format=rgba,scale=out_color_matrix=bt709:"
                          f"out_range=tv,format=yuva420p[l{i}]")
            prox = f"b{i + 2}"
            partes.append(f"[{atual}][l{i}]overlay={lx}:{ly}:format=yuv420:"
                          f"enable='between(t,{a:.3f},{b:.3f})'[{prox}]")
            atual = prox
        partes.append(f"[{atual}]format=yuv420p[v]")
        entradas = ["-ss", f"{self.inicio:.3f}", "-t", f"{d:.3f}", "-i", str(self.arquivo),
                    "-i", str(mold)]
        for arq in legs:
            entradas += ["-i", str(arq)]
        if self.tem_audio:
            partes.append(f"[0:a]asetpts=PTS-STARTPTS,aresample={TAXA_AUDIO},"
                          "aformat=sample_fmts=s16:channel_layouts=stereo,apad[a]")
            mapa_a = "[a]"
        else:
            entradas += ["-f", "lavfi", "-i", f"anullsrc=r={TAXA_AUDIO}:cl=stereo"]
            mapa_a = f"{len(legs) + 2}:a"
        return [ffmpeg(), "-y", "-hide_banner", "-nostdin", "-loglevel", "error",
                *entradas, "-filter_complex", ";".join(partes),
                "-map", "[v]", "-map", mapa_a, *enc_video(estilo), *ENC_AUDIO_PCM,
                "-t", f"{d:.3f}", str(saida)]

    def render(self, saida: Path, estilo: dict, orc: Orcamento, pasta: Path) -> Path:
        self.preparar(pasta)
        rodar_ffmpeg(self.comando(saida, estilo, pasta), orc, self.nome)
        return saida


# ------------------------------------------------------------ plano/montar
@dataclass
class Musica:
    arquivo: Path
    inicio: float = 0.0
    licenca: dict = field(default_factory=dict)


@dataclass
class Plano:
    modo: str
    segmentos: list
    saida: Path
    estilo: dict
    musica: Musica | None = None
    info: dict = field(default_factory=dict)

    @property
    def duracao(self) -> float:
        return sum(dur_exata(s.duracao) for s in self.segmentos)

    @property
    def tem_audio_principal(self) -> bool:
        return any(getattr(s, "tem_audio", False) for s in self.segmentos)


def _entrada_musica(m: Musica, dur: float) -> list:
    return ["-stream_loop", "-1", "-ss", f"{m.inicio:.3f}", "-t", f"{dur:.3f}",
            "-i", str(m.arquivo)]


def _filtro_audio(plano: Plano, principal: dict | None, ganho_musica: float | None) -> str:
    est = plano.estilo
    dur = plano.duracao
    partes = []
    if principal is not None:
        lra = min(50.0, max(float(est["lra"]), principal["input_lra"] + 1.0))
        ln = (f"loudnorm=I={est['alvo_lufs']}:TP={est['true_peak']}:LRA={lra:.1f}")
        if math.isfinite(principal.get("input_thresh", float("-inf"))):
            ln += (f":measured_I={principal['input_i']:.2f}:measured_TP={principal['input_tp']:.2f}"
                   f":measured_LRA={principal['input_lra']:.2f}"
                   f":measured_thresh={principal['input_thresh']:.2f}"
                   f":offset={principal['target_offset']:.2f}:linear=true")
        partes.append(f"[0:a]{ln},aresample={TAXA_AUDIO}[p]")
    if ganho_musica is not None:
        fade = min(1.5, dur / 3)
        partes.append(f"[1:a]aresample={TAXA_AUDIO},aformat=channel_layouts=stereo,"
                      f"volume={ganho_musica:.2f}dB,afade=t=in:d={min(0.6, dur / 4):.2f},"
                      f"afade=t=out:st={max(0.0, dur - fade):.3f}:d={fade:.2f},"
                      f"apad,atrim=0:{dur:.3f}[m]")
    if principal is not None and ganho_musica is not None:
        partes.append("[p][m]amix=inputs=2:duration=first:normalize=0[a]")
    elif principal is not None:
        partes[-1] = partes[-1].replace("[p]", "[a]")
    elif ganho_musica is not None:
        partes[-1] = partes[-1].replace("[m]", "[a]")
    else:
        partes.append("[0:a]anull[a]")
    return ";".join(partes)


def comando_final(plano: Plano, lista: Path, principal: dict | None,
                  ganho_musica: float | None) -> list:
    est = plano.estilo
    dur = plano.duracao
    cmd = [ffmpeg(), "-y", "-hide_banner", "-nostdin", "-loglevel", "error",
           "-f", "concat", "-safe", "0", "-i", str(lista)]
    if ganho_musica is not None and plano.musica:
        cmd += _entrada_musica(plano.musica, dur)
    cmd += ["-filter_complex", _filtro_audio(plano, principal, ganho_musica),
            "-map", "0:v", "-map", "[a]", "-c:v", "copy",
            "-c:a", "aac", "-b:a", f"{int(est.get('audio_kbps', 192))}k",
            "-ar", str(TAXA_AUDIO), "-ac", "2", "-movflags", "+faststart",
            "-t", f"{dur:.3f}", str(plano.saida)]
    return cmd


def comandos_simulados(plano: Plano, pasta: Path) -> list[str]:
    """O que seria rodado, em texto (modo --simular: nada é renderizado)."""
    linhas = []
    for i, s in enumerate(plano.segmentos, 1):
        saida = pasta / f"seg{i:02d}_{s.nome}.mov"
        if isinstance(s, SegClipe):
            s._pos_leg = [(sp.x, sp.y) for sp in (fn() for fn, _a, _b in s.temporizados)]
            extra = f"# segmento {i}: {s.nome} ({dur_exata(s.duracao):.2f}s) — vídeo com áudio original + moldura PNG"
        else:
            extra = (f"# segmento {i}: {s.nome} ({dur_exata(s.duracao):.2f}s) — "
                     "quadros desenhados no Pillow enviados pelo stdin")
        linhas += [extra, texto_comando(s.comando(saida, plano.estilo, pasta))]
    lista = pasta / "lista.txt"
    ref = {"input_i": -20.0, "input_tp": -3.0, "input_lra": 5.0,
           "input_thresh": -30.0, "target_offset": 0.0}
    principal = ref if plano.tem_audio_principal else None
    ganho = 0.0 if plano.musica else None
    if principal:
        linhas += ["# loudnorm passada 1 (mede o áudio original)",
                   texto_comando([ffmpeg(), "-hide_banner", "-nostdin", "-f", "concat",
                                  "-safe", "0", "-i", str(lista), "-vn", "-af",
                                  f"loudnorm=I={plano.estilo['alvo_lufs']}:TP={plano.estilo['true_peak']}:"
                                  f"LRA={plano.estilo['lra']}:print_format=json", "-f", "null", "-"])]
    if plano.musica:
        linhas += ["# mede a música (ganho = alvo + musica_db_relativo - medido)",
                   texto_comando([ffmpeg(), "-hide_banner", "-nostdin",
                                  *_entrada_musica(plano.musica, plano.duracao), "-vn", "-af",
                                  "loudnorm=print_format=json", "-f", "null", "-"])]
    final = texto_comando(comando_final(plano, lista, principal, ganho))
    for chave, valor in (("measured_I", "-20.00"), ("measured_TP", "-3.00"),
                         ("measured_LRA", "5.00"), ("measured_thresh", "-30.00"),
                         ("offset", "0.00")):
        final = final.replace(f"{chave}={valor}", f"{chave}=<medido>")
    final = final.replace("volume=0.00dB", "volume=<ganho>dB")
    linhas += ["# montagem final (vídeo copiado, áudio normalizado; os <medido> e o "
               "<ganho> da música saem das medições acima)", final]
    return linhas


def render_plano(plano: Plano, pasta: Path, orc: Orcamento) -> dict:
    """Renderiza os segmentos, emenda e trata o áudio. Devolve medições."""
    lg = log()
    caminhos = []
    tempos = {}
    for i, s in enumerate(plano.segmentos, 1):
        t0 = time.monotonic()
        saida = pasta / f"seg{i:02d}_{s.nome}.mov"
        s.render(saida, plano.estilo, orc, pasta)
        caminhos.append(saida)
        tempos[f"seg{i:02d}_{s.nome}"] = round(time.monotonic() - t0, 2)
        lg.info("segmento %s pronto em %.1fs", s.nome, tempos[f"seg{i:02d}_{s.nome}"])
    lista = pasta / "lista.txt"
    lista.write_text("".join(f"file '{c.name}'\n" for c in caminhos), encoding="utf-8")
    est = plano.estilo
    principal = None
    passadas = 0
    if plano.tem_audio_principal:
        principal = medir_loudness(["-f", "concat", "-safe", "0", "-i", str(lista)], est, orc)
        if principal is None:
            lg.warning("loudnorm: passada 1 sem JSON; usando 1 passada (dinâmica)")
            principal = {"input_thresh": float("-inf"), "input_lra": 0.0}
            passadas = 1
        elif not math.isfinite(principal["input_i"]) or principal["input_i"] < -70:
            lg.warning("áudio principal em silêncio (%.1f LUFS)", principal["input_i"])
            principal = None
        else:
            passadas = 2
    ganho = None
    if plano.musica:
        med = medir_loudness(_entrada_musica(plano.musica, plano.duracao), est, orc,
                             "medir música")
        alvo = float(est["alvo_lufs"]) + float(est["musica_db_relativo"])
        if med and math.isfinite(med["input_i"]):
            ganho = max(-40.0, min(30.0, alvo - med["input_i"]))
        else:
            ganho = float(est["musica_db_relativo"])
    t0 = time.monotonic()
    rodar_ffmpeg(comando_final(plano, lista, principal, ganho), orc, "montagem final")
    tempos["montagem_final"] = round(time.monotonic() - t0, 2)
    return {"tempos_s": tempos, "loudnorm_passadas": passadas,
            "loudness_principal_medida": principal.get("input_i") if principal else None,
            "ganho_musica_db": round(ganho, 2) if ganho is not None else None}


def composto_png(sprites, caminho: Path) -> Path:
    compor(sprites).save(caminho)
    return caminho
