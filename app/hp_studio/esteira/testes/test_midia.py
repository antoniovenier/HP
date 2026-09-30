"""Mídia: plano B sem ffprobe (ffmpeg -i), quadros, loudness, legendas."""
import pytest

import esteira.midia as midia
from esteira.erros import ErroPermanente
from esteira.legendas import (Fala, deslocar, gerar_ass, ler_srt, quebrar_falas,
                              tempo_ass, tempo_srt, escrever_srt)

SAIDA_FFMPEG = """Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'bruto.mp4':
  Duration: 00:01:02.50, start: 0.000000, bitrate: 300 kb/s
  Stream #0:0[0x1](und): Video: h264 (High) (avc1 / 0x31637661), yuv420p(tv, progressive), 1920x1080 [SAR 1:1 DAR 16:9], 219 kb/s, 29.97 fps, 29.97 tbr, 12800 tbn (default)
  Stream #0:1[0x2](und): Audio: aac (LC) (mp4a / 0x6134706D), 44100 Hz, stereo, fltp, 69 kb/s (default)
At least one output file must be specified
"""


def test_interpretar_saida_do_ffmpeg():
    i = midia.interpretar_saida_ffmpeg(SAIDA_FFMPEG)
    assert i.duracao == 62.5 and (i.largura, i.altura) == (1920, 1080)
    assert i.fps == 29.97 and i.tem_video and i.tem_audio
    assert i.codec_video == "h264" and i.codec_audio == "aac"


def test_interpretar_imagem_e_capa_anexada():
    txt = ("  Duration: N/A, bitrate: N/A\n"
           "  Stream #0:0: Video: png, rgba(pc), 1080x1920, 25 tbr, 25 tbn\n")
    i = midia.interpretar_saida_ffmpeg(txt)
    assert i.duracao is None and (i.largura, i.altura) == (1080, 1920)
    txt2 = ("  Duration: 00:00:03.00\n  Stream #0:0: Audio: mp3, 44100 Hz\n"
            "  Stream #0:1: Video: mjpeg, yuvj420p, 500x500, 90k tbr (attached pic)\n")
    i2 = midia.interpretar_saida_ffmpeg(txt2)
    assert i2.tem_audio and not i2.tem_video


def test_info_midia_plano_b_sem_ffprobe(tmp_path, monkeypatch):
    monkeypatch.setattr(midia, "achar_ffprobe", lambda: None)
    v = midia.gerar_video_teste(tmp_path / "v.mp4", 1.0, 320, 180)
    i = midia.info_midia(v)
    assert i.fonte == "ffmpeg" and abs(i.duracao - 1.0) < 0.1
    assert (i.largura, i.altura) == (320, 180) and i.tem_audio


def test_info_midia_arquivo_ruim(tmp_path):
    ruim = tmp_path / "x.mp4"
    ruim.write_text("não sou vídeo")
    with pytest.raises(ErroPermanente):
        midia.info_midia(ruim, usar_ffprobe=False)
    with pytest.raises(ErroPermanente):
        midia.info_midia(tmp_path / "nao_existe.mp4")


def test_quadros_de_revisao(tmp_path):
    v = midia.gerar_video_teste(tmp_path / "v.mp4", 2.0, 1080, 1920, audio=False)
    qs = midia.quadros_revisao(v, tmp_path, largura=540)
    assert [q["arquivo"] for q in qs] == ["quadro_1_inicio.jpg", "quadro_2_meio.jpg",
                                          "quadro_3_fim.jpg"]
    for q in qs:
        i = midia.info_midia(tmp_path / q["arquivo"], usar_ffprobe=False)
        assert (i.largura, i.altura) == (540, 960)
    assert midia.tempos_quadros(10) == [1.0, 5.0, 9.0]


def test_extrair_audio_e_loudness(tmp_path):
    v = midia.gerar_video_teste(tmp_path / "v.mp4", 1.0, 160, 120)
    a = midia.extrair_audio(v, tmp_path / "audio.wav")
    i = midia.info_midia(a, usar_ffprobe=False)
    assert i.tem_audio and not i.tem_video
    m = midia.medir_loudness(v)
    assert -40 < m["input_i"] < 0


def test_ler_json_loudnorm():
    txt = 'lixo\n[Parsed_loudnorm_0 @ 0x1]\n{\n\t"input_i" : "-inf",\n\t"input_tp" : "-3.0"\n}\n'
    d = midia.ler_json_loudnorm(txt)
    assert d["input_i"] == float("-inf") and d["input_tp"] == -3.0


def test_srt_ida_e_volta(tmp_path):
    falas = [Fala(0.0, 1.5, "Olá"), Fala(1.5, 3.25, "tudo bem?\nsim")]
    escrever_srt(falas, tmp_path / "a.srt")
    lidas = ler_srt(tmp_path / "a.srt")
    assert [(f.inicio, f.fim, f.texto) for f in lidas] == [(0.0, 1.5, "Olá"),
                                                           (1.5, 3.25, "tudo bem?\nsim")]
    assert tempo_srt(3661.5) == "01:01:01,500" and tempo_ass(61.25) == "0:01:01.25"


def test_quebrar_e_deslocar_falas():
    longa = Fala(0, 6, "uma frase bem comprida " * 6)
    partes = quebrar_falas([longa], 20)
    assert len(partes) > 1 and all(len(l) <= 20 for p in partes for l in p.texto.split("\n"))
    assert all(p.texto.count("\n") <= 1 for p in partes)
    assert partes[0].inicio == 0 and abs(partes[-1].fim - 6) < 0.01
    d = deslocar([Fala(0, 1, "a"), Fala(2, 4, "b"), Fala(9, 10, "c")], 1.5, 3.0)
    assert [(f.inicio, f.fim, f.texto) for f in d] == [(0.5, 2.5, "b")]


def test_gerar_ass_escapa_chaves(tmp_path):
    gerar_ass([Fala(0, 1, "{\\b1}oi\nlinha 2")], tmp_path / "a.ass", 1.0, "Crédito: @x")
    txt = (tmp_path / "a.ass").read_text(encoding="utf-8")
    assert "PlayResX: 1080" in txt and "PlayResY: 1920" in txt
    assert "{" not in txt.split("[Events]")[1] and "\\N" in txt and "Crédito: @x" in txt
