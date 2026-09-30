"""Comparação de vídeo de ponta a ponta com mídia sintética."""
from datetime import datetime

import pytest

from hpbase import TravaOcupada, pasta_app
from qa_paridade import comparar_video


def _cmp(midia, app, **kw):
    return comparar_video(midia[app], midia["ref"], usar_trava=False, **kw)


def test_video_identico_nota_10(midia):
    rel = _cmp(midia, "igual")
    assert rel["veredito"] == "IDENTICO"
    assert rel["aprovado"] is True
    assert rel["nota_final"] == 10
    for nome in ("duracao", "ssim", "loudness", "formato"):
        assert rel["metricas"][nome]["nota"] == 10, nome
    assert rel["metricas"]["ssim"]["detalhes"]["media"] == 1.0
    assert rel["metricas"]["ssim"]["detalhes"]["quadros_comparados"] >= 6
    assert rel["metricas"]["legenda"]["aplica"] is False


@pytest.mark.parametrize("app", ["caixa", "ruido", "deslocado"])
def test_video_alterado_ssim_menor_e_diferente(midia, app):
    rel = _cmp(midia, app)
    s = rel["metricas"]["ssim"]
    assert s["detalhes"]["media"] < 0.95
    assert s["nota"] < 9
    assert rel["veredito"] == "DIFERENTE"
    assert rel["aprovado"] is False
    assert "ssim" in rel["metricas_reprovadas"]
    pior = s["detalhes"]["piores_quadros"][0]
    assert 0 < pior["tempo_s"] < 3 and pior["pior_regiao"]
    # o resto continua igual: o problema está só na imagem
    assert rel["metricas"]["duracao"]["nota"] == 10
    assert rel["metricas"]["loudness"]["nota"] == 10


def test_caixa_sobreposta_aponta_o_meio_da_tela(midia):
    rel = _cmp(midia, "caixa")
    assert rel["metricas"]["ssim"]["detalhes"]["piores_quadros"][0]["pior_regiao"].startswith("meio")


def test_ruido_e_bem_pior_que_caixa(midia):
    caixa = _cmp(midia, "caixa")["metricas"]["ssim"]["detalhes"]["media"]
    ruido = _cmp(midia, "ruido")["metricas"]["ssim"]["detalhes"]["media"]
    assert ruido < caixa < 1.0


def test_duracao_diferente(midia):
    rel = _cmp(midia, "curto")
    d = rel["metricas"]["duracao"]
    assert d["detalhes"]["diferenca_s"] == pytest.approx(0.6, abs=0.06)
    assert d["nota"] < 9
    assert "mais curto" in d["resumo"]
    assert rel["veredito"] == "DIFERENTE" and not rel["aprovado"]


def test_audio_6db_mais_baixo_reprova_loudness(midia):
    rel = _cmp(midia, "baixo")
    l = rel["metricas"]["loudness"]
    assert l["detalhes"]["diferenca_lu"] == pytest.approx(6.0, abs=0.5)
    assert l["nota"] < 9
    assert rel["metricas"]["ssim"]["nota"] == 10
    assert not rel["aprovado"]
    assert rel["veredito"] == "DIFERENTE"


def test_sem_audio_no_app(midia):
    rel = _cmp(midia, "sem_audio")
    assert rel["metricas"]["loudness"]["nota"] == 0
    assert rel["metricas"]["formato"]["subnotas"]["audio"] == 0
    assert not rel["aprovado"]


def test_legenda_em_arquivo_entra_na_nota(midia):
    ok = comparar_video(midia["igual"], midia["ref"], midia["srt_ref"], midia["srt_ref"],
                        usar_trava=False)
    assert ok["metricas"]["legenda"]["nota"] == 10 and ok["veredito"] == "IDENTICO"
    ruim = comparar_video(midia["igual"], midia["ref"], midia["srt_desloc"], midia["srt_ref"],
                          usar_trava=False)
    assert ruim["metricas"]["legenda"]["nota"] < 9
    assert ruim["veredito"] == "DIFERENTE"


def test_legenda_extraida_da_faixa_do_video(midia):
    rel = comparar_video(midia["app_leg"], midia["ref_leg"], usar_trava=False)
    leg = rel["metricas"]["legenda"]
    assert leg["aplica"]
    assert leg["subnotas"]["texto"] == 10
    assert leg["detalhes"]["desvio_medio_ms"] == pytest.approx(500, abs=5)
    assert leg["nota"] < 9


def test_trava_pesada_pega_e_solta(midia):
    trava = pasta_app() / "pesado.lock"
    rel = comparar_video(midia["igual"], midia["ref"], agora=datetime(2026, 9, 30, 10, 0))
    assert rel["veredito"] == "IDENTICO"
    assert not trava.exists()


def test_trava_respeita_horario_proibido(midia):
    with pytest.raises(TravaOcupada):
        comparar_video(midia["igual"], midia["ref"], agora=datetime(2026, 9, 30, 19, 0))


def test_arquivo_que_falta(midia, tmp_path):
    with pytest.raises(FileNotFoundError):
        comparar_video(tmp_path / "nao.mp4", midia["ref"], usar_trava=False)
