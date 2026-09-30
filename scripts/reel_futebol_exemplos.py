"""Roteiros-modelo (um por formato) e mídia sintética para os exemplos/testes.

A mídia sintética é gerada na hora (testsrc do ffmpeg, cores do Pillow e
seno): nada de vídeo, foto ou música real. Os times e jogadores dos modelos
são FICTÍCIOS (Azul FC, Verde EC...), para ninguém confundir com notícia.
"""
from __future__ import annotations

import copy
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from reel_futebol_arte import fonte
from reel_futebol_base import agora_iso, escrever_json, garantir
from reel_futebol_midia import ffmpeg, rodar_ffmpeg

AVISO_MODELO = ("MODELO — feito com mídia sintética (testsrc do ffmpeg, cores e "
                "seno) e times fictícios. NÃO PUBLICAR: serve só para conferir "
                "visual, tempos e áudio do montador.")
MARCA_MODELO = "MODELO · MÍDIA SINTÉTICA"

_PADRAO_MIDIA = {
    "clipe": "clipe_oficial_do_clube.mp4",
    "foto1": "foto_oficial_1.jpg", "foto2": "foto_oficial_2.jpg",
    "foto3": "foto_oficial_3.jpg", "foto4": "foto_oficial_4.jpg",
    "musica": "trilha_livre.mp3",
}


def roteiro_exemplo(modo: str, midia: dict | None = None) -> dict:
    """Roteiro completo de exemplo do formato (esquema preenchido)."""
    m = dict(_PADRAO_MIDIA)
    m.update(midia or {})
    musica = {"arquivo": m["musica"], "inicio": 0}
    base = {"versao": 1, "canal": "futebol", "modo": modo}
    if modo == "gol":
        base.update({
            "id": "2026-09-30_gol_azul_silva",
            "mandante": {"nome": "Azul FC", "sigla": "AZU", "gols": 2, "cor": "#1D4ED8"},
            "visitante": {"nome": "Verde EC", "sigla": "VER", "gols": 1, "cor": "#15803D"},
            "time_do_gol": "mandante",
            "minuto": 67,
            "autor": "Silva",
            "campeonato": "Campeonato Exemplo 2026 · 28ª rodada",
            "duracao_cartao": 2.0,
            "video": {"arquivo": m["clipe"], "fonte_tipo": "oficial_clube",
                      "credito": "@azulfc", "link_origem": "https://www.instagram.com/p/EXEMPLO/",
                      "inicio": 0, "fim": None},
            "legenda": "Silva sobe mais que a zaga e testa no canto: o Azul vira o jogo "
                       "no fim e segue na briga pelo título!",
        })
    elif modo == "noticia":
        base.update({
            "id": "2026-09-30_noticia_renovacao_silva",
            "titulo": "Azul FC renova com o artilheiro Silva até 2029",
            "fonte": "Fonte: site oficial do Azul FC",
            "fotos": [
                {"arquivo": m["foto1"], "credito": "Foto: Fotógrafo Exemplo / Azul FC",
                 "fonte_tipo": "oficial_clube"},
                {"arquivo": m["foto2"], "credito": "Foto: Fotógrafo Exemplo / Azul FC",
                 "fonte_tipo": "oficial_clube"},
                {"arquivo": m["foto3"], "credito": "Foto: Assessoria / Azul FC",
                 "fonte_tipo": "oficial_clube"},
            ],
            "legendas": ["O camisa 9 assinou nesta terça-feira",
                         "São 21 gols no campeonato, líder da artilharia",
                         "Novo contrato vai até dezembro de 2029"],
            "duracao_por_foto": 4.0,
            "musica": musica,
        })
    elif modo == "debate":
        base.update({
            "id": "2026-09-30_debate_camisa9",
            "titulo": "Quem é o melhor camisa 9 do campeonato?",
            "recortes": [
                {"nome": "Silva", "time": "Azul FC", "numero": "21", "rotulo": "gols no campeonato",
                 "foto": {"arquivo": m["foto2"], "credito": "Foto: Azul FC",
                          "fonte_tipo": "oficial_clube"}},
                {"nome": "Costa", "time": "Verde EC", "numero": "17", "rotulo": "gols no campeonato",
                 "clipe": {"arquivo": m["clipe"], "fonte_tipo": "oficial_clube",
                           "credito": "@verdeec", "inicio": 0}},
                {"nome": "Souza", "time": "Rubro AC", "numero": "0,71", "rotulo": "gols por jogo",
                 "foto": {"arquivo": m["foto4"], "credito": "Foto: Rubro AC",
                          "fonte_tipo": "oficial_clube"}},
            ],
            "duracao_recorte": 3.0,
            "duracao_final": 2.5,
            "pergunta_final": "Qual deles é o melhor? Comenta aí!",
            "musica": musica,
        })
    elif modo == "estatistica":
        base.update({
            "id": "2026-09-30_estatistica_silva",
            "titulo": "Artilheiro do campeonato",
            "valor": 21, "casas_decimais": 0, "prefixo": "", "sufixo": "",
            "rotulo": "gols de Silva em 27 jogos pelo Azul FC",
            "fonte": "Fonte: tabela oficial da liga",
            "duracao": 5.0, "duracao_contagem": 2.5,
            "musica": musica,
        })
    elif modo == "resultado":
        base.update({
            "id": "2026-09-30_resultado_azul_verde",
            "campeonato": "Campeonato Exemplo 2026 · 28ª rodada",
            "mandante": {"nome": "Azul FC", "sigla": "AZU", "gols": 2, "cor": "#1D4ED8"},
            "visitante": {"nome": "Verde EC", "sigla": "VER", "gols": 1, "cor": "#15803D"},
            "gols": [{"time": "mandante", "autor": "Silva", "minuto": 12},
                     {"time": "visitante", "autor": "Costa", "minuto": "45+2", "tipo": "penalti"},
                     {"time": "mandante", "autor": "Souza", "minuto": 81}],
            "estadio": "Estádio Exemplo", "data": "30/09/2026",
            "duracao": 5.0,
        })
    elif modo == "tabela":
        times = ["Azul FC", "Verde EC", "Rubro AC", "Alvinegro SC", "Tricolor FC",
                 "Celeste EC", "Dourado FC", "Grená AC", "Laranja SC", "Prata FC"]
        base.update({
            "id": "2026-09-30_tabela_rodada28",
            "titulo": "Classificação do Campeonato Exemplo",
            "subtitulo": "após a 28ª rodada",
            "top": 10,
            "linhas": [{"pos": i + 1, "time": t, "pts": 60 - 3 * i, "j": 28,
                        "v": 18 - i, "sg": 30 - 4 * i} for i, t in enumerate(times)],
            "zonas": {"libertadores": [1, 4], "pre_libertadores": [5, 6],
                      "sulamericana": [7, 12], "rebaixamento": [17, 20]},
            "destaque": ["Azul FC"],
            "fonte": "Fonte: tabela oficial da liga",
            "duracao": 6.0,
        })
    else:
        raise ValueError(f"modo desconhecido: {modo}")
    return copy.deepcopy(base)


# ------------------------------------------------------------ mídia sintética
def _foto(caminho: Path, tam, c1, c2, texto: str) -> Path:
    w, h = tam
    y = np.linspace(0, 1, h)[:, None, None]
    x = np.linspace(0, 1, w)[None, :, None]
    k = (0.6 * y + 0.4 * x)
    arr = (np.array(c1) * (1 - k) + np.array(c2) * k).astype(np.uint8)
    img = Image.fromarray(np.ascontiguousarray(np.broadcast_to(arr, (h, w, 3))), "RGB")
    d = ImageDraw.Draw(img)
    for i in range(6):
        r = int(min(w, h) * (0.08 + 0.05 * i))
        cx, cy = int(w * (0.2 + 0.12 * i)), int(h * (0.3 + 0.08 * (i % 3)))
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 255, 255), width=6)
    d.rectangle((0, int(h * 0.78), w, h), fill=(20, 90, 40))
    f = fonte(int(min(w, h) * 0.08), True)
    d.text((w / 2, h / 2), texto, font=f, anchor="mm", fill=(255, 255, 255),
           stroke_width=4, stroke_fill=(0, 0, 0))
    img.save(caminho, quality=90)
    return caminho


def _musica(caminho: Path, dur: float = 20.0, taxa: int = 48000) -> Path:
    """Trilha sintética (acordes suaves) — domínio público, gerada aqui."""
    t = np.arange(int(dur * taxa)) / taxa
    acordes = [(261.63, 329.63, 392.00), (196.00, 246.94, 293.66),
               (220.00, 261.63, 329.63), (174.61, 220.00, 261.63)]
    sinal = np.zeros_like(t)
    for i, ac in enumerate(acordes * int(dur // 8 + 1)):
        ini, fim = i * 2.0, (i + 1) * 2.0
        if ini >= dur:
            break
        m = (t >= ini) & (t < fim)
        tt = t[m] - ini
        env = np.minimum(1, tt / 0.05) * np.exp(-tt * 0.9)
        for f in ac:
            sinal[m] += np.sin(2 * np.pi * f * tt) * env / 3
    batida = (np.sin(2 * np.pi * 2 * t) > 0.97) * np.sin(2 * np.pi * 60 * t) * 0.3
    sinal = 0.5 * (sinal + batida)
    pcm = (np.clip(sinal, -1, 1) * 32767 * 0.8).astype("<i2")
    estereo = np.repeat(pcm[:, None], 2, axis=1)
    with wave.open(str(caminho), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(taxa)
        w.writeframes(estereo.tobytes())
    return caminho


def gerar_clipe(caminho: Path, dur: float = 8.0, tam=(1280, 720), freq: int = 440) -> Path:
    """Clipe testsrc2 com seno (faz o papel do vídeo oficial do clube)."""
    rodar_ffmpeg([ffmpeg(), "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
                  "-i", f"testsrc2=size={tam[0]}x{tam[1]}:rate=30:duration={dur}",
                  "-f", "lavfi", "-i", f"sine=frequency={freq}:sample_rate=48000:duration={dur}",
                  "-filter:a", "volume=3", "-c:v", "libx264", "-preset", "veryfast",
                  "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest",
                  str(caminho)], onde="gerar clipe sintético")
    return caminho


def gerar_midia_sintetica(pasta: Path, dur_clipe: float = 8.0) -> dict:
    """Cria clipe, 4 fotos e 1 música (com licença registrada) em `pasta`.

    Devolve os caminhos RELATIVOS à pasta-mãe (onde ficam os roteiros).
    """
    pasta = garantir(Path(pasta))
    gerar_clipe(pasta / "clipe_oficial_SINTETICO.mp4", dur_clipe)
    fotos = [((1600, 1200), (20, 60, 160), (10, 20, 60)),
             ((1080, 1440), (160, 30, 30), (40, 10, 10)),
             ((1600, 900), (20, 120, 60), (5, 40, 20)),
             ((1200, 1500), (150, 100, 20), (40, 25, 5))]
    for i, (tam, c1, c2) in enumerate(fotos, 1):
        _foto(pasta / f"foto_SINTETICA_{i}.jpg", tam, c1, c2, f"FOTO SINTÉTICA {i}")
    ml = garantir(pasta / "musicas_livres")
    _musica(ml / "trilha_SINTETICA.wav")
    escrever_json(ml / "licencas.json", {"trilha_SINTETICA.wav": {
        "licenca": "domínio público (sintetizada localmente)",
        "fonte": "gerada pelo reel_futebol.py exemplos (síntese de senos)",
        "autor": "HP (sintética)", "registrada_em": agora_iso()}})
    rel = pasta.name
    return {"clipe": f"{rel}/clipe_oficial_SINTETICO.mp4",
            "foto1": f"{rel}/foto_SINTETICA_1.jpg", "foto2": f"{rel}/foto_SINTETICA_2.jpg",
            "foto3": f"{rel}/foto_SINTETICA_3.jpg", "foto4": f"{rel}/foto_SINTETICA_4.jpg",
            "musica": f"{rel}/musicas_livres/trilha_SINTETICA.wav"}


def roteiro_modelo(modo: str, midia: dict) -> dict:
    """Roteiro de exemplo + avisos de MODELO (arquivo e marca d'água)."""
    r = roteiro_exemplo(modo, midia)
    r = {"_aviso": AVISO_MODELO, **r}
    r["id"] = f"MODELO_{modo}"
    r["marca_dagua"] = MARCA_MODELO
    for f in r.get("fotos") or []:
        f["fonte_tipo"] = "propria"
    for it in r.get("recortes") or []:
        if it.get("foto"):
            it["foto"]["fonte_tipo"] = "propria"
    return r
