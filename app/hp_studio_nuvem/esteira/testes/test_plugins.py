"""Adaptadores de subprocesso (sem rodar os scripts de verdade) e Legendador."""
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from hpbase import ler_json

import esteira.plugins as plugins
from esteira import comandos_pc as cp
from esteira.config import carregar_config
from esteira.constantes import ERROS, LEGENDA
from esteira.erros import ErroEtapa, ErroPermanente
from esteira.legendas import ler_srt
from esteira.midia import gerar_audio_teste, info_midia
from esteira.pedido import criar_pedido
from esteira.plugins import (BaixadorYtdlp, DesignerScript, DubladorScript,
                             LegendadorWhisper, NarradorToqueHP, montar_comando)
from esteira.testes.conftest import TIMEOUTS_TESTE, pedido_reel


@pytest.fixture
def cfg(tmp_path):
    c = carregar_config()
    c.timeouts.update(TIMEOUTS_TESTE)
    c.pasta_scripts = tmp_path / "scripts"
    c.pasta_scripts.mkdir()
    return c


def rodar_falso(registro, cria=None, codigo=0, stderr=b""):
    def rodar(cmd, timeout=None, cwd=None, **kw):
        registro.append({"cmd": cmd, "cwd": cwd})
        if cria:
            cria(cmd)
        return subprocess.CompletedProcess(cmd, codigo, b"", stderr)
    return rodar


# --- Legendador ------------------------------------------------------------------
def test_legendador_sem_faster_whisper_da_erro_claro(cfg, monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "faster_whisper", None)  # import falha
    with pytest.raises(ErroPermanente, match="pip install faster-whisper"):
        LegendadorWhisper(cfg).legendar(tmp_path / "a.wav", tmp_path)


def test_sem_faster_whisper_o_item_vai_para_99_com_a_mensagem(amb, monkeypatch):
    monkeypatch.setitem(sys.modules, "faster_whisper", None)
    amb.trocar(legendador=LegendadorWhisper(amb.cfg))
    item = criar_pedido(pedido_reel())
    amb.ciclo()
    assert amb.itens(ERROS) == [item.name]
    e = ler_json(amb.pasta(ERROS) / item.name / "erro.json")
    assert e["etapa"] == LEGENDA and "pip install faster-whisper" in e["mensagem"]


def test_legenda_manual_dispensa_o_whisper(amb, monkeypatch):
    monkeypatch.setitem(sys.modules, "faster_whisper", None)
    amb.trocar(legendador=LegendadorWhisper(amb.cfg))
    item = criar_pedido(pedido_reel())
    (item / "legenda_manual.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nOi\n")
    amb.ciclo()
    assert amb.itens(ERROS) == []


def test_legendador_com_modelo_falso(cfg, tmp_path):
    seg = SimpleNamespace
    modelo = SimpleNamespace(transcribe=lambda *a, **k: (
        iter([seg(start=0.0, end=2.0, text=" Olá pessoal"),
              seg(start=2.0, end=8.0, text=" " + "essa é uma frase bem comprida " * 4)]),
        SimpleNamespace(language="pt")))
    srt = LegendadorWhisper(cfg, fabrica_modelo=lambda: modelo).legendar(tmp_path / "a.wav",
                                                                        tmp_path)
    falas = ler_srt(srt)
    assert falas[0].texto == "Olá pessoal" and len(falas) >= 3
    assert all(len(l) <= 42 for f in falas for l in f.texto.split("\n"))
    t = ler_json(tmp_path / "transcricao.json")
    assert t["idioma"] == "pt" and len(t["segmentos"]) == 2


# --- Baixador ------------------------------------------------------------------------
def test_baixador_usa_scripts_ytdlp(cfg, tmp_path):
    (cfg.pasta_scripts / "ytdlp.py").write_text("# existe")
    reg = []

    def cria(cmd):
        Path(cmd[cmd.index("-o") + 1]).write_bytes(b"v" * 100)   # o argv real usa -o, não --saida
    b = BaixadorYtdlp(cfg, rodar_falso(reg, cria))
    arq = b.baixar("https://youtu.be/abc", tmp_path / "baixando")
    assert arq.name == "bruto.mp4"
    cmd = reg[0]["cmd"]
    assert cmd[0] == cfg.python and cmd[1].endswith("ytdlp.py") and cmd[-1] == "https://youtu.be/abc"
    assert "--saida" not in cmd and "--download-sections" not in cmd   # sem inicio/fim: vídeo inteiro
    # com o pedido do lote (inicio/fim) baixa só o trecho, com a folga de 4 s
    cmd = b.comando("https://youtu.be/abc", tmp_path, {"inicio": "03:26", "fim": "04:04"})
    assert cmd == cp.argv_baixar({"video_url": "https://youtu.be/abc", "inicio": "03:26", "fim": "04:04"},
                                 tmp_path / "bruto.mp4", python=cfg.python, scripts=cfg.pasta_scripts)
    assert cmd[cmd.index("--download-sections") + 1] == "*00:03:22.000-00:04:08.000"


def test_baixador_sem_script_e_sem_ytdlp(cfg, tmp_path, monkeypatch):
    monkeypatch.setattr(plugins.shutil, "which", lambda n: None)
    with pytest.raises(ErroPermanente, match="yt-dlp"):
        BaixadorYtdlp(cfg, rodar_falso([])).baixar("https://x", tmp_path)


def test_baixador_usa_ytdlp_do_path(cfg, tmp_path, monkeypatch):
    monkeypatch.setattr(plugins.shutil, "which", lambda n: "/usr/bin/yt-dlp")
    cmd = BaixadorYtdlp(cfg).comando("https://x", tmp_path)
    assert cmd[0] == "/usr/bin/yt-dlp" and "--no-playlist" in cmd and cmd[-1] == "https://x"


def test_baixador_falha_sem_vazar_segredo(cfg, tmp_path):
    (cfg.pasta_scripts / "ytdlp.py").write_text("")
    rod = rodar_falso([], codigo=1, stderr=b"HTTP 403 access_token=EAAsegredo123")
    with pytest.raises(ErroEtapa) as e:
        BaixadorYtdlp(cfg, rod).baixar("https://x", tmp_path)
    assert "EAAsegredo123" not in str(e.value) and "403" in str(e.value)


def test_baixador_terminou_sem_video(cfg, tmp_path):
    (cfg.pasta_scripts / "ytdlp.py").write_text("")
    with pytest.raises(ErroEtapa, match="nenhum vídeo"):
        BaixadorYtdlp(cfg, rodar_falso([])).baixar("https://x", tmp_path)


# --- Dublador / Narrador ----------------------------------------------------------------
def test_dublador_sem_script(cfg, tmp_path):
    with pytest.raises(ErroPermanente, match="dublar.py"):
        DubladorScript(cfg).dublar(tmp_path, tmp_path / "legenda.srt", {})


def test_dublador_chama_script(cfg, tmp_path):
    (cfg.pasta_scripts / "dublar.py").write_text("")
    reg = []

    def cria(cmd):
        Path(cmd[cmd.index("--saida") + 1]).write_bytes(b"mp4")
    (tmp_path / "final.mp4").write_bytes(b"mp4")
    (tmp_path / "transcricao_pt.json").write_text('{"segmentos": []}', encoding="utf-8")
    d = DubladorScript(cfg, rodar_falso(reg, cria))
    # o dublar.py REAL dubla um corte já renderizado: <corte> --transcricao <json> --inicio --fim [--saida]
    saida = d.dublar(tmp_path, tmp_path / "legenda.srt", {"corte": {"inicio": 6.08, "fim": 46.04}})
    assert saida == tmp_path / "final_dublado.mp4"
    cmd = reg[0]["cmd"]
    assert cmd == cp.argv_dublar_avulso(tmp_path / "final.mp4", tmp_path / "transcricao_pt.json", 6.08,
                                        46.04, saida, python=cfg.python, scripts=cfg.pasta_scripts)
    assert "--srt" not in cmd and "--texto-arquivo" not in cmd
    # sem corte renderizado: erro claro (na esteira o gringo é dublado pelo cortar.py --dublar)
    with pytest.raises(ErroPermanente, match="cortar.py --dublar"):
        d.dublar(tmp_path / "outro", tmp_path / "l.srt", {})


def test_narrador_planejar(cfg):
    n = NarradorToqueHP(cfg, sintetizar=lambda t, s: s)
    p = n.planejar({"abertura": 1.5, "trecho": 3.0, "fecho": 1.5}, 12.0)
    assert p["abertura"] == {"inicio": 0.0, "fim": 1.5, "tempo": 1.0}
    assert p["trecho"]["inicio"] == 2.3 and p["fecho"]["fim"] == 11.7
    p = n.planejar({"abertura": 2.4, "fecho": 1.0}, 10.0)
    assert p["abertura"]["tempo"] == 1.2 and p["abertura"]["fim"] == 2.0
    with pytest.raises(ErroPermanente, match="2s"):
        n.planejar({"abertura": 3.0, "fecho": 1.0}, 10.0)
    with pytest.raises(ErroPermanente, match="curto demais"):
        n.planejar({"abertura": 1.5, "trecho": 5.0, "fecho": 2.0}, 8.0)


def test_narrador_monta_narracao_com_ffmpeg(cfg, tmp_path):
    def sintetizar(texto, saida):
        return gerar_audio_teste(saida, 1.0 if "?" in texto else 2.0, 500)
    n = NarradorToqueHP(cfg, sintetizar=sintetizar)
    wav = n.narrar(tmp_path, {"abertura": "Já viu?", "trecho": "Olha só.", "fecho": "E aí?"}, 8.0)
    i = info_midia(wav, usar_ffprobe=False)
    assert abs(i.duracao - 8.0) < 0.05
    assert wav.stat().st_size < 8.0 * 48000 * 4 * 1.1  # nunca maior que 8 s de WAV
    assert ler_json(tmp_path / "narracao.json")["plano"]["fecho"]["inicio"] == 6.7


# --- Designer ---------------------------------------------------------------------------
def test_designer_threads_texto(cfg, tmp_path):
    arqs = DesignerScript(cfg).gerar(tmp_path, {"tipo": "threads_texto", "texto": "Oi"})
    assert arqs[0].read_text(encoding="utf-8") == "Oi\n"


def test_designer_usa_imagens_prontas(cfg, tmp_path):
    (tmp_path / "a.png").write_bytes(b"png")
    arqs = DesignerScript(cfg, rodar_falso([])).gerar(tmp_path, {"tipo": "estatico",
                                                                 "arquivos": ["a.png"]})
    assert [a.name for a in arqs] == ["arte_01.png"]


def test_designer_chama_estaticos(cfg, tmp_path):
    (cfg.pasta_scripts / "estaticos.py").write_text("")
    reg = []

    def cria(cmd):
        pasta = Path(cmd[-1])                      # estaticos.py carrossel <spec> <pasta_saida>
        for i in (2, 1):
            (pasta / f"{i:02d}.jpg").write_bytes(b"x")
    pedido = {"tipo": "carrossel", "canal": "gta", "titulo": "Linha do tempo",
              "laminas": [{"titulo": "2022", "texto": "anúncio"}]}
    arqs = DesignerScript(cfg, rodar_falso(reg, cria)).gerar(tmp_path, pedido)
    assert [a.name for a in arqs] == ["01.jpg", "02.jpg"]
    cmd = reg[0]["cmd"]
    assert cmd == cp.argv_estaticos_carrossel(tmp_path / "spec_carrossel.json", tmp_path / "arte",
                                              python=cfg.python, scripts=cfg.pasta_scripts)
    assert "--pedido" not in cmd
    spec = ler_json(tmp_path / "spec_carrossel.json")
    assert spec["capa"]["titulo"] == "Linha do tempo" and spec["laminas"][0]["texto"] == "anúncio"


def test_designer_sem_script(cfg, tmp_path):
    with pytest.raises(ErroPermanente, match="estaticos.py"):
        DesignerScript(cfg).gerar(tmp_path, {"tipo": "carrossel", "canal": "gta", "titulo": "x"})
    with pytest.raises(ErroPermanente, match='"spec"'):
        DesignerScript(cfg).gerar(tmp_path, {"tipo": "carrossel", "canal": "futebol", "titulo": "x"})


# --- comandos configuráveis --------------------------------------------------------------
def test_montar_comando_e_config_json(tmp_path):
    from hpbase import escrever_json, pasta_esteira
    escrever_json(pasta_esteira() / "config.json",
                  {"comandos": {"baixar": ["{python}", "{scripts}/ytdlp.py", "-o", "{saida}",
                                           "{url}"]},
                   "editor": {"crf": 18}})
    c = carregar_config()
    assert c.editor["crf"] == 18 and c.editor["lufs"] == -14.0  # mescla com o padrão
    cmd = montar_comando(c, "baixar", url="U", saida="S")
    assert cmd[-3:] == ["-o", "S", "U"]
    c.comandos["baixar"] = ["{naoexiste}"]
    with pytest.raises(ErroPermanente, match="naoexiste"):
        montar_comando(c, "baixar", url="U")


def test_config_padrao_e_sombra():
    c = carregar_config()
    assert c.modo == "sombra" and c.aviso_no_ar_habilitado is False
    assert c.max_voltas == 2 and c.editor["lufs"] == -14.0
    assert c.raiz.name == "esteira_sombra"
    with pytest.raises(ValueError):
        carregar_config(modo="turbo")
