"""Loudness (LUFS) e true peak."""
import pytest

from qa_paridade.limites import carregar_limites
from qa_paridade.loudness import (interpretar_ebur128, interpretar_loudnorm, medir_loudness,
                                  metrica_loudness)

LOUDNORM = """[Parsed_loudnorm_0 @ 0x55]
{
	"input_i" : "-16.52",
	"input_tp" : "-1.73",
	"input_lra" : "4.20",
	"input_thresh" : "-26.60",
	"output_i" : "-14.00",
	"target_offset" : "0.00"
}
"""

LOUDNORM_SILENCIO = LOUDNORM.replace('"-16.52"', '"-inf"').replace('"-1.73"', '"-inf"')

EBUR128 = """[Parsed_ebur128_0 @ 0x1] t: 2.9 TARGET:-23 LUFS M: -14.8 S: -14.8 I: -14.8 LUFS
[Parsed_ebur128_0 @ 0x1] Summary:

  Integrated loudness:
    I:         -14.8 LUFS
    Threshold: -24.8 LUFS

  Loudness range:
    LRA:         0.3 LU
    Threshold: -34.8 LUFS

  True peak:
    Peak:      -13.8 dBFS
"""


def test_interpreta_loudnorm():
    m = interpretar_loudnorm("lixo antes\n" + LOUDNORM)
    assert m == {"integrado_lufs": -16.52, "true_peak_dbtp": -1.73, "lra_lu": 4.2,
                 "metodo": "loudnorm"}
    s = interpretar_loudnorm(LOUDNORM_SILENCIO)
    assert s["integrado_lufs"] is None and s["true_peak_dbtp"] is None
    assert interpretar_loudnorm("sem json") is None


def test_interpreta_ebur128():
    m = interpretar_ebur128(EBUR128)
    assert m["integrado_lufs"] == -14.8
    assert m["true_peak_dbtp"] == -13.8
    assert m["lra_lu"] == 0.3
    assert interpretar_ebur128(EBUR128.replace("-14.8 LUFS\n    Thr", "-70.0 LUFS\n    Thr"))[
        "integrado_lufs"] is None
    assert interpretar_ebur128("nada") is None


def test_mede_video_sintetico_perto_de_menos_14(midia):
    m = medir_loudness(midia["ref"])
    assert m["integrado_lufs"] == pytest.approx(-14.0, abs=0.7)
    assert m["true_peak_dbtp"] < -1
    b = medir_loudness(midia["baixo"])
    assert m["integrado_lufs"] - b["integrado_lufs"] == pytest.approx(6.0, abs=0.3)
    assert medir_loudness(midia["sem_audio"]) is None


def _m(i, tp=-2.0):
    return {"integrado_lufs": i, "true_peak_dbtp": tp, "lra_lu": 3.0, "metodo": "teste"}


def test_notas_do_loudness():
    lim = carregar_limites()
    assert metrica_loudness(_m(-14.0), _m(-14.1), lim)["nota"] == 10
    seis = metrica_loudness(_m(-20.0), _m(-14.0), lim)
    assert seis["nota"] < 9 and seis["subnotas"]["diferenca"] == 0
    # iguais entre si, mas longe do alvo -14: reprova pelo alvo
    longe = metrica_loudness(_m(-23.0), _m(-23.0), lim)
    assert longe["subnotas"]["diferenca"] == 10 and longe["subnotas"]["alvo"] == 0
    # estourando (true peak acima de 0 dBTP)
    assert metrica_loudness(_m(-14.0, 1.5), _m(-14.0), lim)["subnotas"]["true_peak"] < 9
    # sem áudio
    assert metrica_loudness(None, None, lim)["aplica"] is False
    assert metrica_loudness(None, _m(-14.0), lim)["nota"] == 0
    assert metrica_loudness(_m(None), _m(-14.0), lim)["nota"] == 0


def test_alvo_configuravel():
    lim = carregar_limites(extra={"loudness": {"alvo_lufs": -23.0}})
    assert metrica_loudness(_m(-23.0), _m(-23.0), lim)["nota"] == 10
    sem_alvo = carregar_limites(extra={"loudness": {"usar_alvo": False}})
    assert "alvo" not in metrica_loudness(_m(-30.0), _m(-30.0), sem_alvo)["subnotas"]
