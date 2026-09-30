"""Editor com ffmpeg REAL em vídeo sintético (testsrc + sine), curto."""
import pytest
from hpbase import ler_json

from esteira.config import carregar_config
from esteira.editor import EditorFFmpeg
from esteira.legendas import Fala, escrever_srt
from esteira.midia import (gerar_audio_teste, gerar_video_teste, info_midia,
                           medir_loudness)
from esteira.testes.conftest import TIMEOUTS_TESTE


@pytest.fixture
def editor():
    cfg = carregar_config()
    cfg.editor["preset"] = "ultrafast"
    cfg.timeouts.update(TIMEOUTS_TESTE)
    return EditorFFmpeg(cfg)


def pedido(**kw):
    p = {"canal": "gta", "tipo": "reel", "credito": "@rockstargames",
         "fonte_url": "https://youtube.com/x", "dublar": False, "narrar_toque_hp": False}
    p.update(kw)
    return p


def test_editor_16x9_vira_1080x1920_com_legenda_e_loudness(tmp_path, editor):
    item = tmp_path / "P1_2026-09-30_1830_gta_teste"
    item.mkdir()
    gerar_video_teste(item / "bruto.mp4", 2.0, 320, 180, audio=True, volume=0.1)
    escrever_srt([Fala(0.2, 1.6, "Legenda de teste")], item / "legenda.srt")
    d = editor.editar(item, pedido())
    info = info_midia(item / "final.mp4", usar_ffprobe=False)
    assert (info.largura, info.altura) == (1080, 1920)
    assert abs(info.duracao - 2.0) < 0.15
    assert info.tem_audio and info.codec_video == "h264" and info.fps == 30
    assert d["legenda_queimada"] and d["credito"] == "Crédito: @rockstargames"
    assert abs(d["lufs"] - (-14.0)) <= 1.0  # loudnorm 2 passadas no alvo
    capa = info_midia(item / "capa.jpg", usar_ffprobe=False)
    assert (capa.largura, capa.altura) == (1080, 1920)
    assert (item / "legenda.ass").read_text(encoding="utf-8").count("Dialogue:") == 2
    assert ler_json(item / "edicao.json")["alvo_lufs"] == -14.0
    assert not (item / "_final_tmp.mp4").exists()


def test_editor_corte_e_video_vertical(tmp_path, editor):
    item = tmp_path / "item"
    item.mkdir()
    gerar_video_teste(item / "bruto.mp4", 3.0, 360, 640, audio=True)
    d = editor.editar(item, pedido(corte={"inicio": 0.5, "fim": 2.0}, capa_tempo=0.5))
    info = info_midia(item / "final.mp4", usar_ffprobe=False)
    assert (info.largura, info.altura) == (1080, 1920)
    assert abs(info.duracao - 1.5) < 0.15 and d["corte"] == {"inicio": 0.5, "duracao": 1.5}


def test_editor_video_sem_audio(tmp_path, editor):
    item = tmp_path / "item"
    item.mkdir()
    gerar_video_teste(item / "bruto.mp4", 1.5, 320, 240, audio=False)
    d = editor.editar(item, pedido(credito="", fonte_url=None, fonte_propria=True))
    info = info_midia(item / "final.mp4", usar_ffprobe=False)
    assert d["silencioso"] is True and d["lufs"] is None
    assert info.tem_audio  # trilha silenciosa: as redes aceitam melhor
    assert not d["legenda_queimada"] and d["credito"] is None


def test_editor_mistura_dublagem_e_narracao(tmp_path, editor):
    item = tmp_path / "item"
    item.mkdir()
    gerar_video_teste(item / "bruto.mp4", 2.0, 320, 180, audio=True)
    gerar_audio_teste(item / "dublagem.wav", 2.0, 700)
    gerar_audio_teste(item / "narracao.wav", 2.0, 900)
    d = editor.editar(item, pedido(canal="destinos", dublar=True, narrar_toque_hp=True))
    assert d["dublagem"] and d["narracao"]
    assert abs(d["lufs"] - (-14.0)) <= 1.0
    assert abs(medir_loudness(item / "final.mp4")["input_i"] - (-14.0)) <= 1.0


def test_editor_sem_bruto(tmp_path, editor):
    from esteira.erros import ErroPermanente
    with pytest.raises(ErroPermanente, match="bruto"):
        editor.editar(tmp_path, pedido())


def test_editor_legenda_manual_tem_preferencia(tmp_path, editor):
    item = tmp_path / "item"
    item.mkdir()
    gerar_video_teste(item / "bruto.mp4", 1.0, 320, 180)
    escrever_srt([Fala(0, 0.8, "automática")], item / "legenda.srt")
    escrever_srt([Fala(0, 0.8, "corrigida pelo revisor")], item / "legenda_manual.srt")
    editor.editar(item, pedido())
    assert "corrigida pelo revisor" in (item / "legenda.ass").read_text(encoding="utf-8")


def test_todo_ffmpeg_tem_saida_finita(tmp_path, editor, monkeypatch):
    """Regressão: apad gerava WAV infinito (encheu o disco) ou curto demais.
    Nenhum grafo usa apad, toda saída tem -t, toda fonte anullsrc tem -t e todo
    ffmpeg tem timeout curto."""
    import esteira.midia as midia
    from esteira.plugins import NarradorToqueHP
    comandos = []
    real = midia.rodar

    def espiao(cmd, timeout=None, **kw):
        comandos.append((cmd, timeout))
        assert timeout is not None and timeout <= 90  # teto HP_FFMPEG_TIMEOUT_MAX
        return real(cmd, timeout=timeout, **kw)
    monkeypatch.setattr(midia, "rodar", espiao)
    item = tmp_path / "item"
    item.mkdir()
    gerar_video_teste(item / "bruto.mp4", 2.0, 320, 180)
    gerar_audio_teste(item / "dublagem.wav", 2.0, 700)
    NarradorToqueHP(editor.cfg, sintetizar=lambda t, s: gerar_audio_teste(s, 0.5, 800)) \
        .narrar(item, {"abertura": "Viu?", "fecho": "E aí?"}, 2.0)
    editor.editar(item, pedido(canal="destinos", dublar=True, narrar_toque_hp=True))
    grafos = [[str(x) for x in c] for c, _ in comandos if "-filter_complex" in map(str, c)]
    assert len(grafos) >= 3  # narração + 2 passadas do editor
    for txt in grafos:
        assert not any("apad" in x for x in txt)  # apad já gerou WAV infinito
        assert "-t" in txt  # saída sempre com duração
        for i, x in enumerate(txt):
            if x.startswith("anullsrc"):
                assert "-t" in txt[max(0, i - 4):i]  # fonte infinita sempre limitada
    assert abs(info_midia(item / "narracao.wav", usar_ffprobe=False).duracao - 2.0) < 0.05
    assert (item / "narracao.wav").stat().st_size < 2_000_000
