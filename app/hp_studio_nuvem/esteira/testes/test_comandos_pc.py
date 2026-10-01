"""Golden tests do comandos_pc (a linha de comando REAL dos scripts do PC, §4.4), a varredura
dos argumentos proibidos e a esteira em --simular com o pedido real do plano_corte_exemplo.json."""
from __future__ import annotations

import inspect
import json
import os
import subprocess
from pathlib import Path

import pytest
from hpbase import ler_json, raiz_drive, raiz_local

from esteira import comandos_pc as cp
from esteira.config import COMANDOS_PADRAO, carregar_config
from esteira.constantes import EDICAO, LEGENDA, PEDIDOS, REVISAO
from esteira.pedido import criar_pedido, normalizar_pedido, validar_pedido
from esteira.plugins import BaixadorYtdlp, DesignerScript, DubladorScript, montar_comando
from esteira.testes.conftest import TIMEOUTS_TESTE

PC_REAL = Path(__file__).resolve().parents[4] / "tests" / "fixtures" / "pc_real"
PY = cp.PYTHON_PC
FMT = "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080]/b"
PROIBIDOS = {"ytdlp.py": ("--saida",), "dublar.py": ("--srt", "--texto-arquivo"),
             "estaticos.py": ("--pedido",)}
SEMPRE_PROIBIDOS = ("--srt", "--texto-arquivo", "--pedido")


def s(nome: str) -> str:
    return str(cp.scripts_pc() / nome)


@pytest.fixture
def plano() -> dict:
    return json.loads((PC_REAL / "plano_corte_exemplo.json").read_text(encoding="utf-8"))


@pytest.fixture
def config_json() -> dict:
    return json.loads((PC_REAL / "config_trecho.json").read_text(encoding="utf-8"))


# --- constantes, hms, tempos -------------------------------------------------------------------
def test_constantes_do_pc_e_scripts_respeitam_hp_drive(monkeypatch, tmp_path):
    assert cp.PYTHON_PC.endswith(r"Programs\Python\Python312\python.exe")
    if os.name != "nt":
        assert cp.PYTHON_PC.startswith("%LOCALAPPDATA%")      # no Linux fica literal
    assert cp.scripts_pc() == raiz_drive() / "06 Projeto" / "scripts"
    monkeypatch.setenv("HP_DRIVE", str(tmp_path / "G"))
    assert cp.scripts_pc() == tmp_path / "G" / "06 Projeto" / "scripts"
    assert cp.SCRIPTS_PC.name == "scripts" and cp.SCRIPTS_PC.parent.name == "06 Projeto"


def test_hms_e_segundos():
    assert cp.hms(202) == "00:03:22.000" and cp.hms(248) == "00:04:08.000"
    assert cp.hms(3723.5) == "01:02:03.500" and cp.hms(-3) == "00:00:00.000"
    assert cp.segundos("03:26") == 206 and cp.segundos("1:02:03") == 3723
    assert cp.segundos("07:02.5") == 422.5 and cp.segundos(6.08) == 6.08 and cp.segundos("46,04") == 46.04
    with pytest.raises(ValueError):
        cp.segundos("1:2:3:4")
    with pytest.raises(ValueError):
        cp.segundos(None)


def test_janela_e_id_do_video():
    assert cp.janela({"corte": [6.08, 46.04]}) == (6.08, 46.04)
    assert cp.janela({"corte": {"inicio": 2, "fim": 30}}) == (2.0, 30.0)
    assert cp.janela({"corte": {"fim": 30}}) == (0.0, 30.0) and cp.janela({}) is None
    assert cp.id_do_video({"video": "c0Com9SMv1s"}) == "c0Com9SMv1s"
    assert cp.id_do_video({"fonte_url": "https://youtu.be/abc123XYZ"}) == "abc123XYZ"
    assert cp.id_do_video({"fonte_url": "https://www.youtube.com/shorts/Qw3rtyUiop1"}) == "Qw3rtyUiop1"


# --- golden: baixar ---------------------------------------------------------------------------
def test_argv_baixar_exemplo_da_secao_4_4():
    pedido = {"video": "abc", "streamer": "davyjones", "inicio": "03:26", "fim": "04:04"}
    assert cp.argv_baixar(pedido, r"H:\HypadoLocal\brutos\davyjones_abc_206.mp4") == [
        PY, s("ytdlp.py"), "-f", FMT, "--merge-output-format", "mp4",
        "-o", r"H:\HypadoLocal\brutos\davyjones_abc_206.mp4", "--no-playlist", "--no-warnings",
        "--download-sections", "*00:03:22.000-00:04:08.000", "--force-keyframes-at-cuts",
        "https://www.youtube.com/watch?v=abc"]


def test_argv_baixar_pedido_real_do_plano(plano):
    argv = cp.argv_baixar(cp.pedido_de_plano(plano), "/tmp/x/bruto.mp4")
    assert argv[-3:] == ["*00:06:58.000-00:07:52.000", "--force-keyframes-at-cuts",
                         "https://www.youtube.com/watch?v=c0Com9SMv1s"]
    assert argv[argv.index("--download-sections") + 1] == "*00:06:58.000-00:07:52.000"   # 07:02−4 .. 07:48+4
    assert argv[-1] == "https://www.youtube.com/watch?v=c0Com9SMv1s"
    assert argv[argv.index("-o") + 1] == "/tmp/x/bruto.mp4"


def test_argv_baixar_inicio_perto_de_zero_e_sem_trecho():
    argv = cp.argv_baixar({"fonte_url": "https://youtu.be/q", "inicio": 2, "fim": "00:30"}, "b.mp4")
    assert argv[argv.index("--download-sections") + 1] == "*00:00:00.000-00:00:34.000"
    inteiro = cp.argv_baixar({"fonte_url": "https://youtu.be/q"}, "b.mp4")
    assert "--download-sections" not in inteiro and "--force-keyframes-at-cuts" not in inteiro
    assert inteiro[-1] == "https://youtu.be/q" and inteiro[:3] == [PY, s("ytdlp.py"), "-f"]
    with pytest.raises(ValueError, match="sem vídeo"):
        cp.argv_baixar({"titulo": "x"}, "b.mp4")


def test_pedido_com_arquivo_nao_baixa_e_copia_trecho(tmp_path):
    bruto = tmp_path / "brutos" / "tgg_c0Com9SMv1s_422.mp4"
    bruto.parent.mkdir()
    bruto.write_bytes(b"video")
    pedido = {"arquivo": str(bruto), "video_url": "https://youtu.be/q", "inicio": "07:02", "fim": "07:48"}
    assert cp.argv_baixar(pedido, tmp_path / "x.mp4") is None
    copia = cp.copiar_trecho(pedido, tmp_path / "item" / "bruto.mp4")
    assert copia.read_bytes() == b"video" and bruto.exists()
    relativo = {"arquivo": "tgg_c0Com9SMv1s_422.mp4"}
    assert cp.copiar_trecho(relativo, tmp_path / "y.mp4", brutos=tmp_path / "brutos").exists()
    with pytest.raises(FileNotFoundError):
        cp.copiar_trecho({"arquivo": "nao_existe.mp4"}, tmp_path / "z.mp4", brutos=tmp_path)


# --- golden: transcrever, cortar, versao_upload, dublar ------------------------------------------
def test_argv_transcrever():
    assert cp.argv_transcrever(r"H:\HypadoLocal\brutos\tgg_c0Com9SMv1s_883.mp4", "tgg") == [
        PY, s("transcrever.py"), r"H:\HypadoLocal\brutos\tgg_c0Com9SMv1s_883.mp4", "--id-streamer", "tgg"]
    assert cp.argv_transcrever("a.mp4") == [PY, s("transcrever.py"), "a.mp4"]


def test_argv_cortar_igual_ao_lote_renderizar():
    base = [PY, s("cortar.py"), r"H:\HypadoLocal\brutos\tgg_c0Com9SMv1s_883.mp4", "--inicio", "6.08",
            "--fim", "46.04", "--gancho", "GTA 6 tem corrida de DEMOLIÇÃO", "--id-streamer", "tgg",
            "--saida", r"G:\Meu Drive\Hypado\01 Fila para postar\Reserva\x.mp4"]
    arq = r"H:\HypadoLocal\brutos\tgg_c0Com9SMv1s_883.mp4"
    saida = r"G:\Meu Drive\Hypado\01 Fila para postar\Reserva\x.mp4"
    assert cp.argv_cortar(arq, 6.08, 46.04, "GTA 6 tem corrida de DEMOLIÇÃO", "tgg", saida) == base
    # gringo: --dublar no fim
    assert cp.argv_cortar(arq, 6.08, 46.04, "GTA 6 tem corrida de DEMOLIÇÃO", "tgg", saida,
                          dublar=True) == base + ["--dublar"]
    # fade_saida
    assert cp.argv_cortar(arq, 6.08, 46.04, "GTA 6 tem corrida de DEMOLIÇÃO", "tgg", saida,
                          fade_saida=0.1) == base + ["--fade-saida", "0.1"]
    # emenda (trechos): --transcricao antes de tudo; ordem --transcricao, --fade-saida, --dublar
    assert cp.argv_cortar(arq, 6.08, 46.04, "GTA 6 tem corrida de DEMOLIÇÃO", "tgg", saida,
                          transcricao=r"H:\HypadoLocal\brutos\tgg_c0Com9SMv1s_883_ed1.json",
                          fade_saida=0.1, dublar=True) == base + [
        "--transcricao", r"H:\HypadoLocal\brutos\tgg_c0Com9SMv1s_883_ed1.json",
        "--fade-saida", "0.1", "--dublar"]
    # caminho com espaço vai SEM aspas na lista; para_humano cita
    assert all('"' not in p for p in base)
    humano = cp.para_humano(base)
    assert '"G:\\Meu Drive\\Hypado\\01 Fila para postar\\Reserva\\x.mp4"' in humano
    assert '"GTA 6 tem corrida de DEMOLIÇÃO"' in humano and humano.startswith(PY if " " not in PY else '"')


def test_argv_versao_upload_e_dublar_avulso():
    assert cp.argv_versao_upload(r"G:\x\corte.mp4") == [PY, s("versao_upload.py"), r"G:\x\corte.mp4"]
    assert "--help" not in cp.argv_versao_upload("c.mp4")
    assert cp.argv_dublar_avulso("corte.mp4", "trad_pt.json", 6.08, 46.04) == [
        PY, s("dublar.py"), "corte.mp4", "--transcricao", "trad_pt.json", "--inicio", "6.08", "--fim", "46.04"]
    assert cp.argv_dublar_avulso("corte.mp4", "trad_pt.json", "4", "44", "dub.mp4")[-2:] == ["--saida", "dub.mp4"]


# --- golden: estáticos, posts, story clicável, lote ------------------------------------------------
def test_argv_estaticos_carrossel():
    assert cp.argv_estaticos_carrossel(r"H:\u\carrossel_spec.json", r"H:\u\carrossel_2026-10-01") == [
        PY, s("estaticos.py"), "carrossel", r"H:\u\carrossel_spec.json", r"H:\u\carrossel_2026-10-01"]
    assert cp.argv_estaticos_carrossel("spec.json", "out", tiktok=True)[-1] == "--tiktok"


def test_argv_estaticos_story_tipos_e_opcoes():
    assert cp.argv_estaticos_story("interativo", r"H:\u\story_interativo.jpg",
                                   titulo="Furacão chegando em Leonida. O que você faz?") == [
        PY, s("estaticos.py"), "story", "interativo", r"H:\u\story_interativo.jpg",
        "--titulo", "Furacão chegando em Leonida. O que você faz?"]
    assert cp.argv_estaticos_story("contagem", "0900_contagem.jpg", data="2026-11-19", hoje="2026-10-01")[5:] == [
        "--data", "2026-11-19", "--hoje", "2026-10-01"]
    assert cp.argv_estaticos_story("novo_video", "s.jpg", titulo="Dá pra ficar GORDO no GTA 6",
                                   video=r"H:\v.mp4")[5:] == ["--titulo", "Dá pra ficar GORDO no GTA 6",
                                                              "--video", r"H:\v.mp4"]
    # a ordem é fixa (--titulo --texto --imagem --video --fonte --data --hoje --selo), não a do kwargs
    argv = cp.argv_estaticos_story("noticia", "n.jpg", selo="NOVO", fonte="Game Informer",
                                   texto="t", imagem="i.jpg", titulo="T")
    assert argv[5:] == ["--titulo", "T", "--texto", "t", "--imagem", "i.jpg", "--fonte", "Game Informer",
                        "--selo", "NOVO"]
    assert cp.argv_estaticos_story("noticia", "n.jpg", titulo="T", selo=True)[-1] == "--selo"
    with pytest.raises(ValueError, match="tipo de story"):
        cp.argv_estaticos_story("feed", "n.jpg")
    with pytest.raises(ValueError, match="opção desconhecida"):
        cp.argv_estaticos_story("noticia", "n.jpg", pedido="x")


def test_argv_estaticos_destaques_e_story_clicavel_e_lote():
    assert cp.argv_estaticos_destaques(r"H:\u\destaques") == [PY, s("estaticos.py"), "destaques", r"H:\u\destaques"]
    assert cp.argv_story_clicavel_fila() == [PY, s("story_clicavel.py"), "fila"]
    assert cp.argv_story_clicavel_fila("2026-09-30") == [PY, s("story_clicavel.py"), "fila", "--desde", "2026-09-30"]
    assert cp.argv_lote(r"G:\lotes\2026-10-01_diario.json", "renderizar", [402, 405]) == [
        PY, s("lote.py"), r"G:\lotes\2026-10-01_diario.json", "renderizar", "--so", "402,405"]
    assert cp.argv_lote("p.json", "preparar") == [PY, s("lote.py"), "p.json", "preparar"]
    assert cp.argv_lote("p.json", "renderizar", "402")[-2:] == ["--so", "402"]
    with pytest.raises(ValueError):
        cp.argv_lote("p.json", "--help")


def test_argv_posts_render_por_canal_e_posts_canais():
    for canal, script in (("futebol", "posts_futebol.py"), ("filmes", "posts_filmes.py"),
                          ("receitas", "posts_receitas.py"), ("carros", "posts_carros.py"),
                          ("destinos", "posts_destinos.py")):
        assert cp.argv_posts_render(canal, rf"H:\c\{canal}\post.json") == [
            PY, s(script), "render", rf"H:\c\{canal}\post.json"]
    with pytest.raises(ValueError, match="estaticos.py"):
        cp.argv_posts_render("gta", "x.json")
    assert cp.argv_posts_canais("render", "post.json") == [PY, s("posts_canais.py"), "render", "post.json"]
    assert cp.argv_posts_canais("destaques", "receitas", r"H:\d") == [
        PY, s("posts_canais.py"), "destaques", "receitas", r"H:\d"]
    assert cp.argv_posts_canais("placar", "p.json")[2:] == ["placar", "p.json"]
    assert cp.argv_posts_canais("gol", "g.json")[2:] == ["gol", "g.json"]
    with pytest.raises(ValueError):
        cp.argv_posts_canais("voar")


def test_python_e_scripts_injetaveis_e_espaco_no_caminho(tmp_path):
    sc = tmp_path / "06 Projeto" / "scripts"
    argv = cp.argv_versao_upload("c.mp4", python=r"C:\Python312\python.exe", scripts=sc)
    assert argv == [r"C:\Python312\python.exe", str(sc / "versao_upload.py"), "c.mp4"]
    assert " " in argv[1] and '"' not in argv[1]
    assert cp.para_humano(argv).count('"') == 2


# --- regras do lote ------------------------------------------------------------------------------
def test_dublar_por_padrao(config_json):
    assert cp.dublar_por_padrao({"streamer": "tmartn2"}, config_json) is True
    assert cp.dublar_por_padrao({"streamer": "tmartn2", "dublar": False}, config_json) is False
    assert cp.dublar_por_padrao({"streamer": "davyjones"}, config_json) is False
    assert cp.dublar_por_padrao({"streamer": "desconhecido"}, config_json) is False
    assert cp.dublar_por_padrao({"streamer": "TmarTn2", "dublar": True}, config_json) is True
    assert cp.dublar_por_padrao({"streamer": "tmartn2"}, None) is False


def test_nomes_do_bruto_transcricao_e_corte(plano):
    pedido = cp.pedido_de_plano(plano)
    assert cp.nome_bruto(pedido) == "tgg_c0Com9SMv1s_422"
    assert cp.arquivo_bruto(pedido) == raiz_local() / "brutos" / "tgg_c0Com9SMv1s_422.mp4"
    assert cp.arquivo_transcricao(pedido) == raiz_local() / "transcricoes" / "tgg_c0Com9SMv1s_422.json"
    assert cp.nome_bruto({"streamer": "tgg", "video": "c0Com9SMv1s", "inicio": "14:43"}) == "tgg_c0Com9SMv1s_883"
    # o caminho do corte bate com o "arquivo" real do plano (01 Fila para postar\AAAA\MM Mês\...)
    corte = cp.arquivo_corte(pedido)
    assert corte == raiz_drive() / "01 Fila para postar" / "2026" / "10 Outubro" / \
        "02.10.2026 09h00 GTA 6 tem corrida de DEMOLIÇÃO.mp4"
    assert str(corte.relative_to(raiz_drive() / "01 Fila para postar")) == \
        plano["arquivo"].replace("\\", os.sep)
    assert cp.arquivo_corte({"gancho": "Sem data"}) == raiz_drive() / "01 Fila para postar" / "Reserva" / "Sem data.mp4"


def test_pedido_de_plano_vira_pedido_da_esteira(plano, config_json):
    p = normalizar_pedido(cp.pedido_de_plano(plano, config_json))
    assert p["canal"] == "gta" and p["tipo"] == "reel" and p["prioridade"] == "P1"
    assert p["fonte_url"] == "https://www.youtube.com/watch?v=c0Com9SMv1s"
    assert p["horario_alvo"] == "2026-10-02T09:00-03:00" and p["redes"] == ["youtube", "facebook"]
    assert p["credito"] == "@TGG_" and p["corte"] == {"inicio": 6.08, "fim": 46.04}
    assert p["narrar_toque_hp"] is True and p["roteiro_narracao"]["abertura"].endswith("?")
    assert p["dublar"] is False          # tgg não está no config_trecho.json (33 criadores no real)
    assert p["lote_n"] == 801 and p["streamer"] == "tgg" and p["inicio"] == "07:02" and p["cobrir"]
    for k in ("arquivo", "upload", "render_status", "agendado", "status", "n"):
        assert k not in p            # resultado do lote, não pedido
    assert p["legenda_post"].startswith("O norte do mapa")
    # item ainda não renderizado com "arquivo" = trecho já baixado -> vira arquivos[] da esteira
    p2 = cp.pedido_de_plano({"n": 1, "video": "x", "streamer": "tmartn2", "inicio": "01:00", "fim": "01:30",
                             "gancho": "G", "titulo": "T", "data": "2026-10-02T09:00",
                             "arquivo": r"H:\HypadoLocal\brutos\tmartn2_x_60.mp4"}, config_json)
    assert p2["arquivos"] == [r"H:\HypadoLocal\brutos\tmartn2_x_60.mp4"] and p2["dublar"] is True
    assert p2["credito"] == "@TmarTn2" and p2["narrar_toque_hp"] is False


def test_argvs_do_pedido_cobre_as_4_etapas(plano, config_json, tmp_path):
    pedido = cp.pedido_de_plano(plano, config_json)
    bruto = tmp_path / "brutos" / "tgg_c0Com9SMv1s_422.mp4"
    saida = tmp_path / "corte.mp4"
    a = cp.argvs_do_pedido(pedido, config_json, bruto=bruto, saida=saida)
    assert set(a) == {"baixar", "transcrever", "cortar", "versao_upload"}
    assert a["baixar"][a["baixar"].index("-o") + 1] == str(bruto)
    assert a["transcrever"] == [PY, s("transcrever.py"), str(bruto), "--id-streamer", "tgg"]
    # tem "cobrir" -> emenda: cortar.py recebe <bruto>_ed801.mkv e --transcricao <bruto>_ed801.json
    assert a["cortar"] == [PY, s("cortar.py"), str(bruto.with_name("tgg_c0Com9SMv1s_422_ed801.mkv")),
                           "--inicio", "6.08", "--fim", "46.04", "--gancho", "GTA 6 tem corrida de DEMOLIÇÃO",
                           "--id-streamer", "tgg", "--saida", str(saida),
                           "--transcricao", str(bruto.with_name("tgg_c0Com9SMv1s_422_ed801.json"))]
    assert a["versao_upload"] == [PY, s("versao_upload.py"), str(saida)]
    # gringo sem emenda e sem corte: --dublar e janela [4, 4 + (fim − inicio)]
    g = cp.argvs_do_pedido({"video": "v", "streamer": "tmartn2", "inicio": "01:00", "fim": "01:30",
                            "gancho": "G", "fade_saida": 0.1}, config_json, bruto="b.mp4", saida="s.mp4")
    assert g["cortar"][3:7] == ["--inicio", "4.0", "--fim", "34.0"]
    assert g["cortar"][-3:] == ["--fade-saida", "0.1", "--dublar"] and "--transcricao" not in g["cortar"]
    # com "arquivo" não baixa
    assert cp.argvs_do_pedido({**pedido, "arquivo": "x.mp4"}, config_json, bruto="b", saida="s")["baixar"] is None


# --- proibidos: varre TODAS as argv_* com vários pedidos -------------------------------------------
PEDIDOS_VARIADOS = [
    {"video": "a", "streamer": "tgg", "inicio": "07:02", "fim": "07:48", "gancho": "G 1"},
    {"fonte_url": "https://youtu.be/b", "inicio": 10, "fim": 40, "gancho": "g", "trechos": [[1, 2]], "fade_saida": 0.2},
    {"fonte_url": "https://youtu.be/c", "titulo": "sem trecho"},
    {"video": "d", "streamer": "tmartn2", "inicio": "00:10", "fim": "00:50", "corte": [2, 30], "gancho": "x/y:z"},
]


def _chamadas_de_todas():
    """Uma chamada (ou várias) por função argv_* do módulo; falha se aparecer função nova sem amostra."""
    cfg = json.loads((PC_REAL / "config_trecho.json").read_text(encoding="utf-8"))
    amostras = {
        "argv_baixar": [((p, "d.mp4"), {}) for p in PEDIDOS_VARIADOS],
        "argv_transcrever": [(("b.mp4", "tgg"), {}), (("b.mp4",), {})],
        "argv_cortar": [(("b.mp4", 1, 2, "g", "s", "o.mp4"), {}),
                        (("b.mp4", 1, 2, "g", "s", "o.mp4"), {"transcricao": "t.json", "fade_saida": 0.1, "dublar": True})],
        "argv_versao_upload": [(("c.mp4",), {})],
        "argv_dublar_avulso": [(("c.mp4", "t.json", 1, 2), {}), (("c.mp4", "t.json", 1, 2, "o.mp4"), {})],
        "argv_estaticos_carrossel": [(("s.json", "out"), {}), (("s.json", "out", True), {})],
        "argv_estaticos_story": [(("noticia", "n.jpg"), {"titulo": "T", "texto": "t", "imagem": "i", "fonte": "f", "selo": "s"}),
                                 (("contagem", "c.jpg"), {"data": "2026-11-19", "hoje": "2026-10-01"}),
                                 (("interativo", "i.jpg"), {"titulo": "?"}), (("novo_video", "v.jpg"), {"video": "v.mp4"})],
        "argv_estaticos_destaques": [(("out",), {})],
        "argv_posts_render": [((c, "p.json"), {}) for c in cp.POSTS_POR_CANAL],
        "argv_posts_canais": [((sub, "x"), {}) for sub in cp.SUBCOMANDOS_POSTS_CANAIS],
        "argv_story_clicavel_fila": [((), {}), (("2026-09-30",), {})],
        "argv_lote": [(("p.json", "preparar"), {}), (("p.json", "renderizar", [1, 2]), {})],
    }
    funcoes = {n: f for n, f in inspect.getmembers(cp, inspect.isfunction) if n.startswith("argv_")}
    assert set(funcoes) == set(amostras), "função argv_* nova sem amostra na varredura"
    saidas = []
    for nome, f in funcoes.items():
        for args, kw in amostras[nome]:
            saidas.append((nome, f(*args, **kw)))
    for p in PEDIDOS_VARIADOS:
        for nome, argv in cp.argvs_do_pedido(p, cfg, bruto="b.mp4", saida="s.mp4").items():
            saidas.append((f"argvs_do_pedido/{nome}", argv))
    return saidas


def test_nenhuma_funcao_usa_argumento_proibido():
    saidas = _chamadas_de_todas()
    assert len(saidas) >= 30
    for nome, argv in saidas:
        if argv is None:
            continue
        assert isinstance(argv, list) and all(isinstance(x, str) for x in argv), nome
        script = Path(argv[1]).name
        for ruim in PROIBIDOS.get(script, ()) + SEMPRE_PROIBIDOS:
            assert ruim not in argv, f"{nome}: {script} com {ruim}"
    for nome, modelo in COMANDOS_PADRAO.items():
        texto = " ".join(modelo)
        assert "--srt" not in texto and "--texto-arquivo" not in texto and "--pedido" not in texto, nome
        if "ytdlp.py" in texto:
            assert "--saida" not in texto
        assert "--help" not in texto
    assert "falar" not in COMANDOS_PADRAO     # dublar.py não sintetiza frase avulsa


def test_modelos_do_config_batem_com_as_funcoes(tmp_path):
    """montar_comando(cfg, nome, ...) com os modelos padrão == argv_* (uma fonte só)."""
    cfg = carregar_config()
    assert cfg.comandos == cp.MODELOS and COMANDOS_PADRAO == cp.MODELOS
    py, sc = cfg.python, cfg.pasta_scripts
    assert montar_comando(cfg, "cortar", entrada="b.mp4", inicio=1, fim=2, gancho="g", streamer="s", saida="o") == \
        cp.argv_cortar("b.mp4", 1, 2, "g", "s", "o", python=py, scripts=sc)
    assert montar_comando(cfg, "baixar", url="u", saida="o", inicio="00:00:01.000", fim="00:00:09.000") == \
        cp.argv_baixar({"video_url": "u", "inicio": 5, "fim": 5}, "o", python=py, scripts=sc)
    assert montar_comando(cfg, "estaticos_story", tipo="noticia", saida="n.jpg") == \
        cp.argv_estaticos_story("noticia", "n.jpg", python=py, scripts=sc)
    assert montar_comando(cfg, "posts_render", script="posts_carros.py", entrada="p.json") == \
        cp.argv_posts_render("carros", "p.json", python=py, scripts=sc)
    assert montar_comando(cfg, "lote", entrada="p.json", acao="preparar") == \
        cp.argv_lote("p.json", "preparar", python=py, scripts=sc)
    # {scripts}/x.py vira caminho com a barra do sistema
    assert montar_comando(cfg, "versao_upload", entrada="c.mp4")[1] == str(Path(sc) / "versao_upload.py")


# --- plugins + esteira em --simular com o pedido real ------------------------------------------------
def rodar_falso(registro, cria=None):
    def rodar(cmd, timeout=None, cwd=None, **kw):
        registro.append(list(cmd))
        if cria:
            cria(cmd)
        return subprocess.CompletedProcess(cmd, 0, b"", b"")
    return rodar


def test_esteira_simulada_com_o_pedido_real_confere_o_argv_de_cada_etapa(amb, plano, config_json):
    cfg = amb.cfg
    cfg.pasta_scripts = cfg.raiz / "scripts"
    cfg.pasta_scripts.mkdir()
    (cfg.pasta_scripts / "ytdlp.py").write_text("# o do PC\n", encoding="utf-8")
    cfg.timeouts.update(TIMEOUTS_TESTE)

    pedido = cp.pedido_de_plano(plano, config_json)
    # rodada 2: o plano real narra o Toque HP e dubla gringo no GTA; CANAIS_COM_VOZ tem gta.
    assert validar_pedido(normalizar_pedido(pedido)) == []

    registro = []

    def cria(cmd):
        Path(cmd[cmd.index("-o") + 1]).write_bytes(b"v" * 64)
    amb.trocar(baixador=BaixadorYtdlp(cfg, rodar_falso(registro, cria)))
    item = criar_pedido(pedido, raiz=cfg.raiz)
    r = amb.ciclo()
    assert r["erros"] == [] and amb.itens(REVISAO) == [item.name]
    etapas = [a.split(":")[0] for a in r["avancaram"]]
    assert etapas[0] == f"{PEDIDOS} -> 02_baixados" and f"{LEGENDA} -> {EDICAO}" in etapas

    # 01_pedidos: o Baixador real montou o argv do ytdlp.py com o trecho do plano (07:02−4 .. 07:48+4)
    assert len(registro) == 1
    destino = amb.pasta(REVISAO) / item.name / "_baixando" / "bruto.mp4"
    esperado = cp.argv_baixar(pedido, destino, python=cfg.python, scripts=cfg.pasta_scripts)
    # a pasta do item mudou de etapa; compara tudo menos o caminho de saída e confere o nome dele
    assert registro[0][:7] == esperado[:7] and registro[0][8:] == esperado[8:]
    assert Path(registro[0][7]).name == "bruto.mp4" and item.name in registro[0][7]
    assert registro[0][registro[0].index("--download-sections") + 1] == "*00:06:58.000-00:07:52.000"
    assert registro[0][-1] == "https://www.youtube.com/watch?v=c0Com9SMv1s"
    assert registro[0][:2] == [cfg.python, str(cfg.pasta_scripts / "ytdlp.py")]

    # as outras etapas do PC para o mesmo item (transcrever, cortar, versao_upload), a partir do pedido gravado
    pasta = amb.pasta(REVISAO) / item.name
    gravado = ler_json(pasta / "pedido.json")
    bruto = pasta / "bruto.mp4"
    assert bruto.exists() and gravado["corte"] == {"inicio": 6.08, "fim": 46.04}
    a = cp.argvs_do_pedido(gravado, config_json, bruto=bruto, saida=pasta / "final.mp4",
                           python=cfg.python, scripts=cfg.pasta_scripts)
    assert a["transcrever"] == [cfg.python, str(cfg.pasta_scripts / "transcrever.py"), str(bruto), "--id-streamer", "tgg"]
    assert a["cortar"][2] == str(bruto.with_name("bruto_ed801.mkv"))        # "cobrir" -> emenda
    assert a["cortar"][3:13] == ["--inicio", "6.08", "--fim", "46.04", "--gancho", "GTA 6 tem corrida de DEMOLIÇÃO",
                                 "--id-streamer", "tgg", "--saida", str(pasta / "final.mp4")]
    assert a["cortar"][13:] == ["--transcricao", str(bruto.with_name("bruto_ed801.json"))]
    assert a["versao_upload"] == [cfg.python, str(cfg.pasta_scripts / "versao_upload.py"), str(pasta / "final.mp4")]
    for argv in a.values():
        for ruim in SEMPRE_PROIBIDOS + ("--saida",) if argv and Path(argv[1]).name == "ytdlp.py" else SEMPRE_PROIBIDOS:
            assert ruim not in (argv or [])
    post = ler_json(pasta / "post.json")
    assert post["conta"] == "@hpgta6" and "Crédito: @TGG_" in post["legenda"]


def test_designer_posts_por_canal_e_story_gta(tmp_path):
    cfg = carregar_config()
    cfg.pasta_scripts = tmp_path / "scripts"
    cfg.pasta_scripts.mkdir()
    for n in ("posts_receitas.py", "estaticos.py"):
        (cfg.pasta_scripts / n).write_text("")
    reg = []

    def cria(cmd):
        specs = [c for c in cmd if c.endswith(".json")]
        if specs:                                   # posts_<canal>.py render <spec>: lê "saida" do spec
            pasta = Path(ler_json(specs[0])["saida"])
            for nome in ("frango_feed.jpg", "frango_story.jpg", "frango_01.jpg", "frango_02.jpg"):
                (pasta / nome).write_bytes(b"x")
        else:                                       # estaticos.py story <tipo> <saida.jpg> ...
            Path([c for c in cmd if c.endswith(".jpg")][0]).write_bytes(b"x")
    d = DesignerScript(cfg, rodar_falso(reg, cria))
    item = tmp_path / "item"
    item.mkdir()
    spec = {"id": "2026-10-01_1000_frango-assado", "slides": [{"tipo": "capa", "titulo": "Frango"}], "reel": True}
    arqs = d.gerar(item, {"tipo": "carrossel", "canal": "receitas", "id": "x", "spec": spec})
    assert [a.name for a in arqs] == ["frango_01.jpg", "frango_02.jpg"]
    assert reg[0] == cp.argv_posts_render("receitas", item / "post_spec.json", python=cfg.python, scripts=cfg.pasta_scripts)
    gravado = ler_json(item / "post_spec.json")
    assert gravado["canal"] == "receitas" and gravado["saida"] == str(item / "arte") and gravado["slides"]
    arqs = d.gerar(item, {"tipo": "story", "canal": "receitas", "spec": spec})
    assert [a.name for a in arqs] == ["frango_story.jpg"]
    arqs = d.gerar(item, {"tipo": "story", "canal": "gta", "titulo": "Furacão chegando. O que você faz?",
                          "modelo": "interativo"})
    assert [a.name for a in arqs] == ["story.jpg"]
    assert reg[-1] == cp.argv_estaticos_story("interativo", item / "arte" / "story.jpg", python=cfg.python,
                                              scripts=cfg.pasta_scripts, titulo="Furacão chegando. O que você faz?")
    from esteira.erros import ErroPermanente
    with pytest.raises(ErroPermanente, match="carrossel"):
        d.gerar(item, {"tipo": "estatico", "canal": "gta", "titulo": "x"})
    # config.json personalizou o comando: vale o modelo do config
    cfg.comandos["posts_render"] = ["{python}", "{scripts}/{script}", "render", "{entrada}", "--rapido"]
    d.gerar(item, {"tipo": "carrossel", "canal": "receitas", "spec": spec})
    assert reg[-1][-1] == "--rapido"
