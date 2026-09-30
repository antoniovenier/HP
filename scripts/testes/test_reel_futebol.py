"""Testes do montador de reels do Futebol | HP (scripts/reel_futebol.py).

Rodar a partir de app/:  python -m pytest -q ../scripts/testes/test_reel_futebol.py
Não usa rede nem mídia real: clipe testsrc2 + seno 440 Hz, fotos de cores e
trilha sintética, tudo gerado na hora. Sem ffprobe (só ffmpeg).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import reel_futebol as rf  # noqa: E402  (põe o hpbase no sys.path)
from hpbase import TravaOcupada, TravaPesada  # noqa: E402
from reel_futebol_arte import (ESTILO_PADRAO, Sprite, achar_fonte,  # noqa: E402
                               caixa_texto, carregar_estilo, conferir_zona,
                               fonte, formatar_numero, quebrar)
from reel_futebol_base import ErroReel, RoteiroInvalido  # noqa: E402
from reel_futebol_exemplos import (gerar_clipe, gerar_midia_sintetica,  # noqa: E402
                                   roteiro_exemplo)
from reel_futebol_midia import (extrair_audio, extrair_quadro, ffmpeg,  # noqa: E402
                                info_midia, medir_volume)
from reel_futebol_modos import arte_cartao_gol  # noqa: E402
from reel_futebol_roteiro import normalizar, obter_legenda_auto  # noqa: E402

MANHA = datetime(2026, 9, 30, 10, 0)
NOITE = datetime(2026, 9, 30, 19, 0)
TOL = 0.2


@pytest.fixture(autouse=True)
def raizes_do_teste(tmp_path, monkeypatch):
    """Nada toca no H:/G: de verdade. Repete o que o conftest de app/ faz,
    para o teste funcionar também quando ele não é carregado."""
    local, drive = tmp_path / "HypadoLocal", tmp_path / "Drive"
    local.mkdir(exist_ok=True)
    drive.mkdir(exist_ok=True)
    monkeypatch.setenv("HP_LOCAL", str(local))
    monkeypatch.setenv("HP_DRIVE", str(drive))
    for var in ("HP_MUSICAS_LIVRES", "HP_POSTS_FUTEBOL"):
        monkeypatch.delenv(var, raising=False)
    return local, drive


@pytest.fixture(scope="session")
def pasta_midia(tmp_path_factory):
    """Mídia sintética criada uma vez: clipe de 3 s com seno 440 Hz etc."""
    raiz = tmp_path_factory.mktemp("reels")
    midia = gerar_midia_sintetica(raiz / "midia", dur_clipe=3.0)
    return raiz, midia


@pytest.fixture
def roteiros(pasta_midia, tmp_path):
    """Copia a mídia para a pasta do teste e devolve fábrica de roteiros."""
    raiz, midia = pasta_midia
    shutil.copytree(raiz / "midia", tmp_path / "midia")

    def fazer(modo: str, **mudancas) -> dict:
        r = roteiro_exemplo(modo, midia)
        r.update(mudancas)
        return r
    return fazer


def gravar(tmp_path: Path, r: dict, nome: str = "roteiro.json") -> Path:
    p = tmp_path / nome
    p.write_text(json.dumps(r, ensure_ascii=False), encoding="utf-8")
    return p


def erros_de(tmp_path: Path, r: dict, **kw) -> list[str]:
    erros, _av = rf.validar(gravar(tmp_path, r), **kw)
    return erros


def conferir_saida(res: dict, dur: float) -> dict:
    info = info_midia(res["saida"])
    assert (info["largura"], info["altura"]) == (1080, 1920)
    assert info["codec_video"] == "h264" and info["pix_fmt"] == "yuv420p"
    assert info["codec_audio"] == "aac" and info["taxa_audio"] == 48000
    assert info["fps"] == 30
    assert abs(info["duracao"] - dur) <= TOL, info["duracao"]
    erro = subprocess.run([ffmpeg(), "-v", "error", "-nostdin", "-i", res["saida"], "-f",
                           "null", "-"], capture_output=True, timeout=120)
    assert erro.returncode == 0 and not erro.stderr.strip(), erro.stderr[-400:]
    assert Path(res["saida"]).with_suffix(".relatorio.json").exists()
    return info


# ----------------------------------------------------------------- validação
def test_esquemas_de_exemplo_sao_validos(roteiros, tmp_path):
    for modo in rf.MODOS:
        assert erros_de(tmp_path, roteiros(modo)) == [], modo


def test_futebol_com_voz_sintetica_e_recusado(roteiros, tmp_path):
    r = roteiros("gol", narracao={"arquivo": "voz_piper.wav"})
    erros = erros_de(tmp_path, r)
    assert any("voz sintética" in e for e in erros)
    r2 = roteiros("noticia", audios=[{"tipo": "tts", "arquivo": "x.wav"}])
    assert any("voz sintética" in e for e in erros_de(tmp_path, r2))
    with pytest.raises(RoteiroInvalido):
        rf.montar(gravar(tmp_path, r), agora=MANHA)


def test_transmissao_de_tv_e_recusada(roteiros, tmp_path):
    r = roteiros("gol")
    r["video"]["fonte_tipo"] = "transmissao_tv"
    erros = erros_de(tmp_path, r)
    assert any("transmissão de TV" in e for e in erros)
    r = roteiros("debate")
    r["recortes"][1]["clipe"]["fonte_tipo"] = "transmissao_tv"
    assert any("transmissão de TV" in e for e in erros_de(tmp_path, r))
    r = roteiros("gol")
    r["video"]["fonte_tipo"] = "youtube_qualquer"
    assert any("fonte_tipo" in e for e in erros_de(tmp_path, r))


def test_musica_sem_licenca_e_recusada(roteiros, tmp_path):
    pasta = tmp_path / "outra" / "musicas_livres"
    pasta.mkdir(parents=True)
    shutil.copy(tmp_path / "midia" / "musicas_livres" / "trilha_SINTETICA.wav",
                pasta / "sem_licenca.wav")
    r = roteiros("noticia", musica={"arquivo": "outra/musicas_livres/sem_licenca.wav"})
    assert any("licença" in e for e in erros_de(tmp_path, r))
    # licença registrada mas "desconhecida" também não vale
    (pasta / "licencas.json").write_text(json.dumps(
        {"sem_licenca.wav": {"licenca": "desconhecida", "fonte": "?"}}), encoding="utf-8")
    assert any("licença" in e for e in erros_de(tmp_path, r))
    # fora da pasta musicas_livres: recusa
    shutil.copy(pasta / "sem_licenca.wav", tmp_path / "solta.wav")
    r = roteiros("noticia", musica={"arquivo": str(tmp_path / "solta.wav")})
    assert any("musicas_livres" in e for e in erros_de(tmp_path, r))


def test_musica_nome_solto_vem_da_pasta_padrao(roteiros, tmp_path, raizes_do_teste):
    local, _ = raizes_do_teste
    ml = local / "musicas_livres"
    shutil.copytree(tmp_path / "midia" / "musicas_livres", ml)
    r = roteiros("estatistica", musica={"arquivo": "trilha_SINTETICA.wav"})
    assert erros_de(tmp_path, r) == []


def test_gol_sem_credito_e_recusado(roteiros, tmp_path):
    r = roteiros("gol")
    r["video"]["credito"] = "  "
    assert any("crédito" in e for e in erros_de(tmp_path, r))
    r = roteiros("noticia")
    del r["fotos"][0]["credito"]
    assert any("crédito da foto" in e for e in erros_de(tmp_path, r))


@pytest.mark.parametrize("modo", ["noticia", "debate", "estatistica", "tabela"])
def test_titulo_vazio_e_recusado(roteiros, tmp_path, modo):
    r = roteiros(modo, titulo="   ")
    assert any("título vazio" in e for e in erros_de(tmp_path, r))


def test_gol_regras_do_audio_original(roteiros, tmp_path):
    mudo = tmp_path / "mudo.mp4"
    subprocess.run([ffmpeg(), "-y", "-v", "error", "-f", "lavfi", "-i",
                    "testsrc2=size=320x240:rate=30:duration=1", "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", str(mudo)], check=True, timeout=60)
    r = roteiros("gol")
    r["video"]["arquivo"] = str(mudo)
    assert any("não tem áudio" in e for e in erros_de(tmp_path, r))
    r = roteiros("gol", musica={"arquivo": "midia/musicas_livres/trilha_SINTETICA.wav"})
    assert any("gol: sem música" in e for e in erros_de(tmp_path, r))
    r = roteiros("gol")
    del r["legenda"]
    assert any("legenda" in e for e in erros_de(tmp_path, r))
    assert not any("legenda" in e for e in erros_de(tmp_path, r, legenda_auto=True))


def test_outras_recusas(roteiros, tmp_path):
    r = roteiros("resultado")
    r["mandante"]["gols"] = 3
    assert any("placar não bate" in e for e in erros_de(tmp_path, r))
    r = roteiros("debate")
    r["recortes"] = r["recortes"][:2]
    assert any("exatamente 3" in e for e in erros_de(tmp_path, r))
    r = roteiros("noticia")
    r["fotos"] = r["fotos"][:1]
    assert any("2 a 4 fotos" in e for e in erros_de(tmp_path, r))
    assert any("modo" in e for e in erros_de(tmp_path, {"modo": "podcast"}))
    r = roteiros("gol")
    r["video"]["fim"] = 99
    assert any("trecho inválido" in e for e in erros_de(tmp_path, r))


# ------------------------------------------------------------ arte e ajudas
def test_fonte_com_fallback():
    assert achar_fonte(True) is not None
    assert achar_fonte(True, preferida="/nao/existe.ttf") is not None
    f = fonte(40)
    assert f.getbbox("Gol")[2] > 0
    from reel_futebol_arte import _carregar_fonte
    assert _carregar_fonte(None, 30).getbbox("x")[2] > 0  # fonte embutida do Pillow


def test_quebra_de_linha_caixa_e_safe_zone():
    est = carregar_estilo()
    f = fonte(50)
    linhas = quebrar("Pedro sobe mais que todo mundo e testa no canto do goleiro", f, 500)
    assert len(linhas) >= 2 and all(len(l) > 0 for l in linhas)
    cx = caixa_texto("texto " * 80, est, largura=900, max_linhas=4)
    assert cx.width == 900 and cx.getpixel((450, 5))[3] > 100  # caixa semitransparente
    assert cx.getpixel((450, 5))[3] < 255
    conferir_zona([Sprite(cx, 60, 1570 - cx.height)])
    with pytest.raises(ErroReel):
        conferir_zona([Sprite(cx, 60, 100)])     # invade os 250 px do topo
    with pytest.raises(ErroReel):
        conferir_zona([Sprite(cx, 60, 1500)])    # invade os 350 px da base
    assert formatar_numero(1234.5, 1) == "1.234,5"


def test_estilo_do_canal_sobrescreve(tmp_path):
    p = tmp_path / "estilo.json"
    p.write_text(json.dumps({"cores": {"destaque": "#FF0000"}, "marca": "TESTE"}), encoding="utf-8")
    est = carregar_estilo(p)
    assert est["cores"]["destaque"] == "#FF0000" and est["cores"]["fundo"] == ESTILO_PADRAO["cores"]["fundo"]
    p.write_text(json.dumps({"cores": {"destaque": "vermelho"}}), encoding="utf-8")
    with pytest.raises(ErroReel):
        carregar_estilo(p)


def test_info_midia_sem_ffprobe(roteiros, tmp_path):
    info = info_midia(tmp_path / "midia" / "clipe_oficial_SINTETICO.mp4")
    assert (info["largura"], info["altura"]) == (1280, 720)
    assert abs(info["duracao"] - 3.0) < 0.1 and info["tem_audio"]


# --------------------------------------------------------- simular/CLI/trava
def test_simular_so_imprime(roteiros, tmp_path, capsys):
    p = gravar(tmp_path, roteiros("gol"))
    res = rf.montar(p, simular=True)
    assert res["simulado"] and abs(res["duracao_planejada"] - 5.0) < 1e-6
    texto = "\n".join(res["comandos"])
    assert "ffmpeg" in texto and "loudnorm" in texto and "-c:v copy" in texto
    assert not p.with_suffix(".mp4").exists()
    assert rf.main(["montar", str(p), "--simular"]) == 0
    assert "SIMULADO" in capsys.readouterr().out
    assert not p.with_suffix(".mp4").exists()


def test_cli_validar_e_esquema(roteiros, tmp_path, capsys):
    assert rf.main(["validar", str(gravar(tmp_path, roteiros("tabela")))]) == 0
    r = roteiros("gol")
    r["video"]["fonte_tipo"] = "transmissao_tv"
    assert rf.main(["validar", str(gravar(tmp_path, r, "ruim.json"))]) == 1
    assert "RECUSADO" in capsys.readouterr().out
    assert rf.main(["esquema", "noticia"]) == 0
    assert json.loads(capsys.readouterr().out)["modo"] == "noticia"


def test_trava_pesada_e_horario(roteiros, tmp_path):
    p = gravar(tmp_path, roteiros("estatistica"))
    with TravaPesada("outro_trabalho", agora=MANHA):
        with pytest.raises(TravaOcupada):
            rf.montar(p, agora=MANHA)
    with pytest.raises(TravaOcupada):
        rf.montar(p, agora=NOITE)
    assert not p.with_suffix(".mp4").exists()
    res = rf.executar({"roteiro": str(p), "simular": True})
    assert res["ok"] and res["simulado"]


def test_executar_nunca_levanta(tmp_path):
    res = rf.executar({"roteiro": {"modo": "gol", "canal": "futebol"}, "base": str(tmp_path)})
    assert res["ok"] is False and res["tipo"] == "roteiro_invalido"
    assert rf.executar({"roteiro": str(tmp_path / "nao_existe.json")})["ok"] is False


def test_legenda_auto_chama_posts_futebol(roteiros, tmp_path, monkeypatch):
    falso = tmp_path / "posts_futebol.py"
    falso.write_text(
        "import sys, json\n"
        "assert sys.argv[1] == 'legenda_video'\n"
        "r = json.load(open(sys.argv[2], encoding='utf-8'))\n"
        "print('Golaço de ' + r['autor'] + ' ⚽')\n", encoding="utf-8")
    monkeypatch.setenv("HP_POSTS_FUTEBOL", str(falso))
    r = roteiros("gol")
    del r["legenda"]
    p = gravar(tmp_path, r)
    assert obter_legenda_auto(p, r, carregar_estilo()) == "Golaço de Silva ⚽"
    falso.write_text("import json; print(json.dumps({'legenda': 'via JSON'}))\n", encoding="utf-8")
    assert obter_legenda_auto(None, r, carregar_estilo()) == "via JSON"
    monkeypatch.setenv("HP_POSTS_FUTEBOL", str(tmp_path / "nao_tem.py"))
    with pytest.raises(ErroReel):
        obter_legenda_auto(p, r, carregar_estilo())


# --------------------------------------------------------- renders de verdade
def test_render_gol_cartao_2s_e_audio_original(roteiros, tmp_path):
    r = roteiros("gol", legenda=[{"texto": "Primeira parte da legenda", "inicio": 0, "fim": 1.5},
                                 {"texto": "Segunda parte", "inicio": 1.5, "fim": 3.0}])
    p = gravar(tmp_path, r)
    res = rf.montar(p, agora=MANHA)
    conferir_saida(res, 5.0)   # 2 s de cartão + 3 s de vídeo oficial
    # cartão de 2 s: quadro em 1 s é o cartão; em 3,5 s já é o vídeo
    rn = normalizar(r, tmp_path, carregar_estilo())
    cartao = np.asarray(arte_cartao_gol(rn, carregar_estilo()), dtype=np.float32)
    q1 = np.asarray(extrair_quadro(res["saida"], 1.0), dtype=np.float32)
    q2 = np.asarray(extrair_quadro(res["saida"], 3.5), dtype=np.float32)
    assert np.abs(q1 - cartao).mean() < 6
    assert np.abs(q2 - cartao).mean() > 15
    assert np.abs(np.asarray(extrair_quadro(res["saida"], 1.95), dtype=np.float32) - cartao).mean() < 6
    # áudio: cartão em silêncio, depois o ÁUDIO ORIGINAL (seno 440 Hz), não mudo
    assert medir_volume(res["saida"], 0.0, 1.8)["pico_db"] < -60
    vol = medir_volume(res["saida"], 2.3, 2.5)
    assert vol["media_db"] > -30
    a = extrair_audio(res["saida"], 2.5, 1.5)
    freq = np.fft.rfftfreq(len(a), 1 / 48000)[np.abs(np.fft.rfft(a)).argmax()]
    assert abs(freq - 440) < 5
    assert abs(res["lufs_saida"] - (-14)) < 1.5 and res["loudnorm_passadas"] == 2
    assert res["creditos"] == ["@azulfc"] and res["fonte_tipo"] == "oficial_clube"


def test_render_noticia_musica_baixa_sem_voz(roteiros, tmp_path):
    r = roteiros("noticia", duracao_por_foto=1.5)
    r["fotos"] = r["fotos"][:2]
    res = rf.montar(gravar(tmp_path, r), agora=MANHA)
    conferir_saida(res, 3.0)
    assert res["musica"]["licenca"]["licenca"].startswith("domínio público")
    # música livre 20 dB abaixo do alvo de -14 LUFS (não tem voz para abafar)
    assert res["lufs_saida"] is not None and abs(res["lufs_saida"] - (-34)) < 3
    q0 = np.asarray(extrair_quadro(res["saida"], 0.2), dtype=np.float32)
    q1 = np.asarray(extrair_quadro(res["saida"], 2.8), dtype=np.float32)
    assert np.abs(q0 - q1).mean() > 5   # trocou de foto


def test_render_debate(roteiros, tmp_path):
    r = roteiros("debate", duracao_recorte=1.0, duracao_final=1.0)
    del r["musica"]
    res = rf.montar(gravar(tmp_path, r), agora=MANHA)
    conferir_saida(res, 4.0)
    assert [s["nome"] for s in res["segmentos"]] == ["recorte1", "recorte2", "recorte3", "comenta_ai"]
    assert medir_volume(res["saida"], 1.1, 0.8)["media_db"] > -35   # clipe com áudio original
    assert medir_volume(res["saida"], 3.1, 0.8)["pico_db"] < -60    # tela final muda


def test_render_estatistica_contador(roteiros, tmp_path):
    r = roteiros("estatistica", duracao=2.0, duracao_contagem=1.0)
    del r["musica"]
    res = rf.montar(gravar(tmp_path, r), agora=MANHA)
    conferir_saida(res, 2.0)
    q0 = np.asarray(extrair_quadro(res["saida"], 0.05), dtype=np.float32)
    q1 = np.asarray(extrair_quadro(res["saida"], 1.5), dtype=np.float32)
    q2 = np.asarray(extrair_quadro(res["saida"], 1.9), dtype=np.float32)
    assert np.abs(q0 - q1).mean() > 1.0      # número subiu
    assert np.abs(q1 - q2).mean() < 1.0      # parado no valor final


def test_render_gol_video_em_pe_cobre_a_tela(roteiros, tmp_path):
    gerar_clipe(tmp_path / "em_pe.mp4", 1.5, (360, 640))
    r = roteiros("gol", duracao_cartao=1.5)
    r["video"]["arquivo"] = str(tmp_path / "em_pe.mp4")
    res = rf.montar(gravar(tmp_path, r), agora=MANHA)
    conferir_saida(res, 3.0)
    assert medir_volume(res["saida"], 1.7, 1.0)["media_db"] > -30   # áudio original


def test_render_resultado_com_escudo(roteiros, tmp_path):
    from PIL import Image
    Image.new("RGBA", (300, 360), (200, 20, 40, 255)).save(tmp_path / "escudo.png")
    r = roteiros("resultado", duracao=2.0)
    r["mandante"]["escudo"] = "escudo.png"
    res = rf.montar(gravar(tmp_path, r), agora=MANHA)
    conferir_saida(res, 2.0)
    q = np.asarray(extrair_quadro(res["saida"], 1.9))
    vermelho = (q[..., 0] > 170) & (q[..., 1] < 60) & (q[..., 2] < 80)
    assert vermelho.sum() > 5000   # o escudo em arquivo apareceu


def test_render_tabela_linha_a_linha(roteiros, tmp_path):
    res = rf.montar(gravar(tmp_path, roteiros("tabela", duracao=2.0)), agora=MANHA)
    conferir_saida(res, 2.0)
    q0 = np.asarray(extrair_quadro(res["saida"], 0.1), dtype=np.float32)
    q1 = np.asarray(extrair_quadro(res["saida"], 1.9), dtype=np.float32)
    assert np.abs(q0 - q1).mean() > 3


def test_exemplos_sao_marcados_como_modelo(raizes_do_teste):
    local, _ = raizes_do_teste
    res = rf.gerar_exemplos(agora=MANHA, curto=True)
    pasta = local / "canais" / "futebol" / "modelos_reel"
    assert sorted(Path(x["saida"]).name for x in res) == [
        "MODELO_debate.mp4", "MODELO_estatistica.mp4", "MODELO_gol.mp4", "MODELO_noticia.mp4"]
    for x in res:
        assert (x["largura"], x["altura"]) == (1080, 1920)
        roteiro = json.loads((pasta / Path(x["saida"]).with_suffix(".json").name).read_text("utf-8"))
        assert "MODELO" in roteiro["_aviso"] and "MODELO" in roteiro["marca_dagua"]
    assert "NÃO PUBLICAR" in (pasta / "LEIA_MODELOS.txt").read_text("utf-8")
    assert not (local / "app" / "pesado.lock").exists()
