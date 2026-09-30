"""Mídia sintética para os testes (gerada 1 vez por sessão, pequena).

Vídeo base: testsrc2 180x320 (em pé, como reel), 25 fps, 3 s, com seno de
440 Hz em ~-14 LUFS. As variações simulam os erros que o app pode cometer.
"""
import sys as _sys
from pathlib import Path as _Path

_HP = str(_Path(__file__).resolve().parents[2])  # ...\app\hp_studio
if _HP not in _sys.path:
    _sys.path.insert(0, _HP)
from hpbase.pytest_raizes import raizes_temporarias  # noqa: E402,F401  (autouse: H:/G: → pastas temporárias)
import shutil

import pytest

from .apoio import FF, SRT_REF, codec_video, ff


@pytest.fixture(scope="session")
def midia(tmp_path_factory):
    if not FF:
        pytest.skip("ffmpeg não está no PATH")
    d = tmp_path_factory.mktemp("midia")
    cv = codec_video()

    def gerar(nome, dur=3.0, vf=None, volume="7.8dB", audio=True, taxa=25,
              dur_video=None, trim=None):
        entradas = ["-f", "lavfi", "-i",
                    f"testsrc2=size=180x320:rate={taxa}:duration={dur_video or dur}"]
        if audio:
            entradas += ["-f", "lavfi", "-i", f"sine=frequency=440:sample_rate=48000:duration={dur}"]
        filtros = []
        if trim:
            filtros.append(f"trim=start={trim},setpts=PTS-STARTPTS")
        if vf:
            filtros.append(vf)
        args = entradas + (["-vf", ",".join(filtros)] if filtros else []) + cv
        if audio:
            args += ["-af", f"volume={volume}", "-ac", "2", "-c:a", "aac", "-b:a", "128k"]
        ff(*args, d / nome)
        return d / nome

    m = {"pasta": d}
    m["ref"] = gerar("ref.mp4")
    m["igual"] = d / "igual.mp4"
    shutil.copy(m["ref"], m["igual"])
    m["caixa"] = gerar("caixa.mp4", vf="drawbox=x=20:y=120:w=140:h=60:color=white:t=fill")
    m["ruido"] = gerar("ruido.mp4", vf="noise=alls=40:allf=t")
    m["deslocado"] = gerar("deslocado.mp4", dur_video=3.5, trim=0.5)
    m["curto"] = gerar("curto.mp4", dur=2.4)
    m["baixo"] = gerar("baixo.mp4", volume="1.8dB")  # 6 dB abaixo da referência
    m["sem_audio"] = gerar("sem_audio.mp4", audio=False)

    # legendas em arquivo e embutidas (faixa mov_text)
    m["srt_ref"] = d / "ref.srt"
    m["srt_ref"].write_text(SRT_REF, encoding="utf-8")
    m["srt_desloc"] = d / "desloc.srt"
    m["srt_desloc"].write_text(SRT_REF.replace("00:00:00,000 -->", "00:00:00,500 -->")
                               .replace("00:00:01,200", "00:00:01,700")
                               .replace("00:00:02,400", "00:00:02,900")
                               .replace("--> 00:00:03,000", "--> 00:00:03,500"),
                               encoding="utf-8")
    for nome, srt in (("ref_leg.mp4", m["srt_ref"]), ("app_leg.mp4", m["srt_desloc"])):
        ff("-i", m["ref"], "-i", srt, "-map", "0", "-map", "1", "-c", "copy",
           "-c:s", "mov_text", d / nome)
    m["ref_leg"] = d / "ref_leg.mp4"
    m["app_leg"] = d / "app_leg.mp4"
    return m
