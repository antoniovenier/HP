"""Legendas: leitura (SRT/VTT/ASS) e comparação de texto e tempos."""
import pytest

from qa_paridade import comparar_legenda
from qa_paridade.legenda import (Bloco, comparar_blocos, ler_ass_texto, ler_legenda,
                                 ler_srt_texto, normalizar)
from qa_paridade.limites import carregar_limites

from .apoio import SRT_REF

ASS = """[Script Info]
Title: teste
PlayResX: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize
Style: Default,Arial,60

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Comment: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,isto é comentário
Dialogue: 0,0:00:01.20,0:00:02.40,Default,,0,0,0,,{\\b1}Bolo de cenoura{\\b0}\\Ncom cobertura de chocolate
Dialogue: 0,0:00:00.00,0:00:01.20,Default,,0,0,0,,Olá, pessoal! Hoje tem receita nova.
Dialogue: 0,0:00:02.40,0:00:03.00,Default,,0,0,0,,Salva pra não perder!
"""


@pytest.fixture
def lim():
    return carregar_limites()


def _escrever(tmp_path, nome, texto, cod="utf-8"):
    p = tmp_path / nome
    p.write_bytes(texto.encode(cod))
    return p


def test_le_srt_com_bom_crlf_e_tags():
    txt = "﻿" + SRT_REF.replace("Olá, pessoal!", "<i>Olá</i>, pessoal!").replace("\n", "\r\n")
    b = ler_srt_texto(txt)
    assert len(b) == 3
    assert b[0] == Bloco(0, 1200, "Olá, pessoal! Hoje tem receita nova.")
    assert b[2].inicio_ms == 2400 and b[2].fim_ms == 3000


def test_le_vtt():
    vtt = ("WEBVTT\n\n00:00.000 --> 00:01.200\nOlá, pessoal! Hoje tem receita nova.\n\n"
           "00:01.200 --> 00:02.400 align:center\nBolo de cenoura\n")
    b = ler_srt_texto(vtt)
    assert [x.inicio_ms for x in b] == [0, 1200]
    assert b[1].texto == "Bolo de cenoura"


def test_le_ass_na_ordem_certa():
    b = ler_ass_texto(ASS)
    assert len(b) == 3
    assert b[0].texto.startswith("Olá")
    assert b[1] == Bloco(1200, 2400, "Bolo de cenoura com cobertura de chocolate")


def test_normalizar():
    assert normalizar("Olá, MUNDO!!  Ação...") == "ola mundo acao"
    assert normalizar("R$ 10,50 — ótimo 🚀") == "r 10 50 otimo"


def test_srt_identico_nota_10(tmp_path, lim):
    a = _escrever(tmp_path, "a.srt", SRT_REF)
    b = _escrever(tmp_path, "b.srt", SRT_REF, "cp1252")  # mesmo texto, outra codificação
    rel = comparar_legenda(a, b)
    assert rel["metricas"]["legenda"]["nota"] == 10
    assert rel["veredito"] == "IDENTICO" and rel["aprovado"]


def test_srt_e_ass_com_mesmo_conteudo_sao_iguais(tmp_path, lim):
    a = _escrever(tmp_path, "a.ass", ASS)
    b = _escrever(tmp_path, "b.srt", SRT_REF)
    assert comparar_legenda(a, b)["metricas"]["legenda"]["nota"] == 10


def test_srt_deslocado_500ms(tmp_path, lim):
    ref = ler_srt_texto(SRT_REF)
    app = [Bloco(b.inicio_ms + 500, b.fim_ms + 500, b.texto) for b in ref]
    m = comparar_blocos(app, ref, lim)
    assert m["subnotas"]["texto"] == 10
    assert m["detalhes"]["desvio_medio_ms"] == 500
    assert m["detalhes"]["desvio_maximo_ms"] == 500
    assert m["subnotas"]["tempo_medio"] < 9
    assert m["nota"] < 9


def test_desvio_pequeno_passa(lim):
    ref = ler_srt_texto(SRT_REF)
    app = [Bloco(b.inicio_ms + 30, b.fim_ms - 20, b.texto) for b in ref]
    m = comparar_blocos(app, ref, lim)
    assert m["nota"] >= 9.5


def test_texto_trocado(lim):
    ref = ler_srt_texto(SRT_REF)
    app = [Bloco(b.inicio_ms, b.fim_ms, b.texto) for b in ref]
    app[1] = Bloco(1200, 2400, "Torta de limão com merengue queimado")
    m = comparar_blocos(app, ref, lim)
    assert m["detalhes"]["similaridade_texto"] < 0.9
    assert m["subnotas"]["texto"] < 9
    assert m["subnotas"]["tempo_medio"] == 10  # o bloco trocado continua pareado
    assert m["detalhes"]["diferencas_texto"][0]["tipo"] == "trocado"
    assert m["nota"] < 9


def test_so_acento_caixa_pontuacao_nao_conta(lim):
    ref = ler_srt_texto(SRT_REF)
    app = [Bloco(b.inicio_ms, b.fim_ms, b.texto.upper().replace("Á", "A").replace("!", ""))
           for b in ref]
    assert comparar_blocos(app, ref, lim)["nota"] == 10


def test_bloco_faltando(lim):
    ref = ler_srt_texto(SRT_REF)
    m = comparar_blocos(ref[:2], ref, lim)
    assert m["detalhes"]["blocos_app"] == 2 and m["detalhes"]["blocos_ref"] == 3
    assert m["subnotas"]["blocos"] < 9
    assert m["detalhes"]["diferencas_texto"][0]["tipo"] == "faltando no app"


def test_legenda_vazia(lim):
    assert comparar_blocos([], [], lim)["aplica"] is False
    assert comparar_blocos([], ler_srt_texto(SRT_REF), lim)["nota"] == 0


def test_le_legenda_de_video(midia):
    b = ler_legenda(midia["ref_leg"])
    assert len(b) == 3 and b[1].inicio_ms == 1200
    with pytest.raises(ValueError):
        ler_legenda(midia["ref"])  # vídeo sem faixa de legenda
