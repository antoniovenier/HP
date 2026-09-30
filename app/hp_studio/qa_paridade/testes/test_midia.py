"""Leitura de mídia só com o ffmpeg (sem ffprobe)."""
import pytest

from hpbase import achar_ffmpeg
from qa_paridade.midia import (ErroMidia, _duracao_decodificando, dimensoes_imagem,
                               extrair_quadros, info_midia, interpretar_info_ffmpeg,
                               ler_imagem_cinza, tamanho_reduzido, tempos_das_amostras)

STDERR_CELULAR = """ffmpeg version 7.0 Copyright (c) 2000-2024
Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'C:\\\\Users\\\\x\\\\VID_2026.mp4':
  Metadata:
    major_brand     : mp42
  Duration: 00:01:02.53, start: 0.000000, bitrate: 17123 kb/s
  Stream #0:0[0x1](eng): Video: hevc (Main) (hvc1 / 0x31637668), yuv420p(tv, bt709), 1920x1080, 16900 kb/s, 29.97 fps, 29.97 tbr, 90k tbn (default)
      Metadata:
        rotate          : 90
      Side data:
        displaymatrix: rotation of -90.00 degrees
  Stream #0:1[0x2](eng): Audio: aac (LC) (mp4a / 0x6134706D), 48000 Hz, stereo, fltp, 256 kb/s (default)
  Stream #0:2[0x3](und): Subtitle: mov_text (tx3g / 0x67337874), 0 kb/s
At least one output file must be specified
"""

STDERR_MP3_COM_CAPA = """Input #0, mp3, from 'musica.mp3':
  Duration: 00:02:05.12, start: 0.025057, bitrate: 320 kb/s
  Stream #0:0: Audio: mp3 (mp3float), 44100 Hz, stereo, fltp, 320 kb/s
  Stream #0:1: Video: mjpeg (Baseline), yuvj420p(pc, bt470bg/unknown/unknown), 500x500 [SAR 1:1 DAR 1:1], 90k tbr, 90k tbn (attached pic)
"""

STDERR_SEM_DURACAO = """Input #0, h264, from 'cru.h264':
  Duration: N/A, bitrate: N/A
  Stream #0:0: Video: h264 (High), yuv420p(progressive), 1080x1920, 30 tbr, 1200k tbn
Input #1, wav, from 'outro.wav':
  Duration: 00:00:09.00, bitrate: 1536 kb/s
  Stream #1:0: Audio: pcm_s16le, 48000 Hz, 2 channels, s16, 1536 kb/s
"""


def test_interpreta_celular_girado_com_legenda():
    i = interpretar_info_ffmpeg(STDERR_CELULAR, "x.mp4")
    assert i.duracao == pytest.approx(62.53)
    assert (i.largura, i.altura) == (1080, 1920)  # girado 90° -> em pé
    assert i.fps == pytest.approx(29.97)
    assert i.tem_video and i.tem_audio and i.tem_legenda
    assert i.codec_video == "hevc" and i.codec_audio == "aac"
    assert i.rotacao == 90
    so_matriz = STDERR_CELULAR.replace("rotate          : 90", "")
    assert interpretar_info_ffmpeg(so_matriz).rotacao == 90


def test_capa_de_mp3_nao_conta_como_video():
    i = interpretar_info_ffmpeg(STDERR_MP3_COM_CAPA)
    assert i.tem_audio and not i.tem_video
    assert i.duracao == pytest.approx(125.12)
    assert i.largura is None


def test_sem_duracao_usa_tbr_e_so_le_o_primeiro_arquivo():
    i = interpretar_info_ffmpeg(STDERR_SEM_DURACAO)
    assert i.duracao is None
    assert (i.largura, i.altura) == (1080, 1920)
    assert i.fps == 30
    assert not i.tem_audio  # o áudio é do Input #1, não conta


def test_info_do_video_sintetico(midia):
    i = info_midia(midia["ref"])
    assert i.duracao == pytest.approx(3.0, abs=0.05)
    assert (i.largura, i.altura) == (180, 320)
    assert i.fps == pytest.approx(25)
    assert i.tem_video and i.tem_audio and not i.tem_legenda
    assert info_midia(midia["ref_leg"]).tem_legenda
    assert not info_midia(midia["sem_audio"]).tem_audio


def test_plano_b_da_duracao_decodificando(midia):
    dur = _duracao_decodificando(midia["ref"], achar_ffmpeg(), 60)
    assert dur == pytest.approx(3.0, abs=0.1)


def test_arquivo_inexistente_e_arquivo_que_nao_e_midia(tmp_path):
    with pytest.raises(FileNotFoundError):
        info_midia(tmp_path / "nao_existe.mp4")
    lixo = tmp_path / "lixo.mp4"
    lixo.write_text("isto não é vídeo")
    with pytest.raises(ErroMidia):
        info_midia(lixo)


def test_tamanho_reduzido():
    assert tamanho_reduzido(1080, 1920) == (270, 480)
    assert tamanho_reduzido(1920, 1080) == (480, 270)
    assert tamanho_reduzido(180, 320) == (180, 320)  # nunca aumenta
    assert tamanho_reduzido(1080, 1350, 400) == (320, 400)
    assert tamanho_reduzido(None, None) == (270, 480)


def test_extrair_quadros_alinhados(midia):
    q = extrair_quadros(midia["ref"], 90, 160, 0.5, 6)
    assert q.shape == (6, 160, 90)
    assert q.dtype.name == "uint8"
    assert tempos_das_amostras(0.5, 6) == [0.25, 0.75, 1.25, 1.75, 2.25, 2.75]
    # pedir mais quadros do que o vídeo tem devolve só os que existem
    assert len(extrair_quadros(midia["ref"], 90, 160, 1.0, 10)) <= 4


def test_imagem_com_transparencia_vira_branco(tmp_path):
    from PIL import Image
    im = Image.new("RGBA", (40, 30), (0, 0, 0, 0))
    im.paste((255, 0, 0, 255), (0, 0, 20, 30))
    p = tmp_path / "t.png"
    im.save(p)
    arr = ler_imagem_cinza(p)
    assert arr.shape == (30, 40)
    assert arr[:, 25:].min() == 255  # transparente conta como branco
    assert dimensoes_imagem(p) == (40, 30)
    assert ler_imagem_cinza(p, 20, 16).shape == (16, 20)
