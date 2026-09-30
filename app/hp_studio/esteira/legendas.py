"""Legendas: ler/escrever SRT, quebrar falas para celular e gerar ASS.

O Editor queima a legenda com o filtro `ass` do ffmpeg (libass). O ASS é
gerado aqui com o tamanho do quadro (1080x1920), fonte, contorno e margem
fixos, mais a linha de crédito no topo durante o vídeo inteiro.
"""
from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass
from pathlib import Path

RX_TEMPO = re.compile(r"(\d+):(\d+):(\d+)[,.](\d{1,3})")


@dataclass
class Fala:
    inicio: float
    fim: float
    texto: str


def _seg(h, m, s, ms) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms.ljust(3, "0")) / 1000


def ler_srt(caminho: Path) -> list[Fala]:
    txt = Path(caminho).read_text(encoding="utf-8-sig")
    falas = []
    for bloco in re.split(r"\n\s*\n", txt.replace("\r\n", "\n").strip()):
        linhas = [l for l in bloco.split("\n") if l.strip()]
        for i, l in enumerate(linhas):
            if "-->" in l:
                a, b = l.split("-->")
                ma, mb = RX_TEMPO.search(a), RX_TEMPO.search(b)
                if not (ma and mb):
                    break
                texto = "\n".join(linhas[i + 1:]).strip()
                if texto:
                    falas.append(Fala(_seg(*ma.groups()), _seg(*mb.groups()), texto))
                break
    return falas


def tempo_srt(s: float) -> str:
    ms = int(round(max(0.0, s) * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    seg, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{seg:02d},{ms:03d}"


def tempo_ass(s: float) -> str:
    cs = int(round(max(0.0, s) * 100))
    h, cs = divmod(cs, 360_000)
    m, cs = divmod(cs, 6000)
    seg, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{seg:02d}.{cs:02d}"


def escrever_srt(falas: list[Fala], caminho: Path) -> Path:
    partes = []
    for i, f in enumerate(falas, 1):
        partes.append(f"{i}\n{tempo_srt(f.inicio)} --> {tempo_srt(f.fim)}\n{f.texto}\n")
    Path(caminho).write_text("\n".join(partes), encoding="utf-8")
    return Path(caminho)


def quebrar_falas(segmentos: list[Fala], max_caracteres: int = 42) -> list[Fala]:
    """Fala longa vira várias de no máximo 2 linhas, com o tempo dividido
    proporcionalmente ao número de letras (leitura no celular)."""
    saida: list[Fala] = []
    for seg in segmentos:
        texto = " ".join(seg.texto.split())
        if not texto:
            continue
        linhas = textwrap.wrap(texto, max_caracteres) or [texto]
        blocos = ["\n".join(linhas[i:i + 2]) for i in range(0, len(linhas), 2)]
        total = sum(len(b) for b in blocos) or 1
        t = seg.inicio
        dur = max(seg.fim - seg.inicio, 0.01)
        for b in blocos:
            fim = t + dur * len(b) / total
            saida.append(Fala(round(t, 3), round(fim, 3), b))
            t = fim
    return saida


def deslocar(falas: list[Fala], inicio: float, duracao: float) -> list[Fala]:
    """Ajusta as falas a um corte [inicio, inicio+duracao] do vídeo."""
    saida = []
    for f in falas:
        a, b = f.inicio - inicio, f.fim - inicio
        if b <= 0 or a >= duracao:
            continue
        saida.append(Fala(max(0.0, a), min(duracao, b), f.texto))
    return saida


def _esc_ass(t: str) -> str:
    return t.replace("\\", "\\\\").replace("{", "(").replace("}", ")") \
            .replace("\n", "\\N")


def gerar_ass(falas: list[Fala], saida: Path, duracao: float,
              credito: str | None = None, largura: int = 1080, altura: int = 1920,
              fonte: str = "Arial", tamanho: int = 68, margem: int = 480,
              tamanho_credito: int = 40) -> Path:
    cab = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {largura}
PlayResY: {altura}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Legenda,{fonte},{tamanho},&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,6,0,2,80,80,{margem},1
Style: Credito,{fonte},{tamanho_credito},&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,3,0,8,60,60,140,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    linhas = []
    if credito:
        linhas.append(f"Dialogue: 1,{tempo_ass(0)},{tempo_ass(duracao)},Credito,,0,0,0,,"
                      f"{_esc_ass(credito)}")
    for f in falas:
        linhas.append(f"Dialogue: 0,{tempo_ass(f.inicio)},{tempo_ass(f.fim)},Legenda,,0,0,0,,"
                      f"{_esc_ass(f.texto)}")
    Path(saida).write_text(cab + "\n".join(linhas) + "\n", encoding="utf-8")
    return Path(saida)
