"""Testes da marca única (hpbase/marca.py) contra a tabela da Seção 4.6 do prompt da rodada 2.

Cada valor da tabela (cor do canal, cor nos posts, fundo, extras, fontes) é comparado
literalmente; contraste WCAG de texto branco sobre cada fundo; resolvedor de fontes caindo
no DejaVu (Linux) sem quebrar e achando a fonte "exata" quando HP_FONTES tem o arquivo.
Nenhum teste usa rede, nem o cache HP_FONTES_CACHE (as variáveis são trocadas por pastas
temporárias vazias).
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from hpbase import marca

# --- a tabela da §4.6, copiada literalmente (RGB da tabela -> hex) -------------------------
TABELA = {
    "gta": {
        "nome": "GTA 6 | HP", "handle": "@hpgta6",
        "cor_canal": (255, 60, 170),      # #FF3CAA (arte de perfil "vice")
        "cor_post": (255, 72, 160),       # #FF48A0
        "fundo": (16, 18, 52),            # noite #101234
        "extras": {"laranja": (255, 176, 84), "ciano": (70, 225, 235), "texto": "#FFE9F3",
                   "corpo": (245, 242, 255)},
        "ceu": [(52, 40, 110), (28, 24, 72), (16, 18, 52)],
        "fontes": {"titulo": "Bauhaus 93", "tema": "Segoe UI Black", "texto": "Segoe UI Bold",
                   "hp": "Segoe UI Black Italic"},
    },
    "futebol": {
        "nome": "Futebol | HP", "handle": "@hp.futebol",
        "cor_canal": (30, 215, 96), "cor_post": (30, 215, 96), "fundo": (10, 16, 12),
        "extras": {"verde_escuro": (18, 168, 80), "preto": (8, 9, 11),
                   "estudio": [(24, 27, 33), (6, 7, 9)]},
        "fontes": {"titulo": "Anton", "texto": "Barlow Medium", "subtitulo": "Barlow SemiBold",
                   "destaque": "Barlow ExtraBold", "condensada": "Barlow Condensed Bold",
                   "condensada_forte": "Barlow Condensed ExtraBold"},
    },
    "filmes": {
        "nome": "Filmes e Séries | HP", "handle": "@hp.filmes",
        "cor_canal": (245, 179, 1), "cor_post": (245, 179, 1), "fundo": (14, 12, 10),
        "extras": {"painel_claro": (239, 239, 239)},
        "fontes": {"titulo": "Barlow ExtraBold", "texto": "Barlow Medium", "poster": "Anton"},
    },
    "receitas": {
        "nome": "Receitas | HP", "handle": "@hp.receitas",
        "cor_canal": (255, 122, 26), "cor_post": (255, 122, 26), "fundo": (18, 12, 9),
        "extras": {"faixa_amarela": (255, 226, 18), "creme": (255, 246, 214),
                   "roxo": (124, 58, 237), "azul": (37, 72, 255)},
        "fontes": {"titulo": "DM Serif Display", "titulo_italico": "DM Serif Display Italic",
                   "texto": "Barlow ExtraBold"},
    },
    "carros": {
        "nome": "Carros | HP", "handle": "@hp.carros",
        "cor_canal": (255, 45, 45),       # #FF2D2D perfil/capa
        "cor_post": (230, 30, 45),        # #E61E2D o da referência
        "fundo": (14, 14, 16),
        "extras": {"amarelo": (255, 214, 0)},
        "fontes": {"titulo": "Anton", "condensada": "Barlow Condensed ExtraBold", "texto": "Barlow"},
    },
    "destinos": {
        "nome": "Destinos | HP", "handle": "@hp.destinos",
        "cor_canal": (0, 194, 209), "cor_post": (0, 194, 209), "fundo": (8, 16, 20),
        "extras": {"ciano_claro": (120, 225, 255), "marinho": (10, 38, 110),
                   "azul": (21, 84, 200), "claro": (236, 243, 251)},
        "fontes": {"titulo": "Barlow ExtraBold", "texto": "Barlow SemiBold",
                   "condensada": "Barlow Condensed ExtraBold"},
    },
}
# a cor de destaque (não tem coluna própria na tabela: é a cor "viva" que a tabela cita)
DESTAQUE = {"gta": "#FFB054", "futebol": "#1ED760", "filmes": "#F5B301", "receitas": "#FFE212",
            "carros": "#FFD600", "destinos": "#78E1FF"}
CANAIS = tuple(TABELA)


def _hex(v) -> str:
    return marca.hex_de(v)


# --- cores ---------------------------------------------------------------------------------
def test_os_6_canais_na_ordem_da_tabela():
    assert tuple(marca.CANAIS) == CANAIS == marca.ORDEM_CANAIS
    assert set(marca.CANAIS["gta"]) >= {"nome", "handle", "cor_canal", "cor_post", "fundo",
                                        "destaque", "extras", "fontes"}


@pytest.mark.parametrize("canal", CANAIS)
def test_nome_e_handle_da_tabela(canal):
    assert marca.CANAIS[canal]["nome"] == TABELA[canal]["nome"]
    assert marca.CANAIS[canal]["handle"] == TABELA[canal]["handle"]
    assert marca.canal_por_handle(TABELA[canal]["handle"]) == canal


@pytest.mark.parametrize("canal", CANAIS)
def test_cor_do_canal_perfil_e_capa(canal):
    assert _hex(marca.CANAIS[canal]["cor_canal"]) == _hex(TABELA[canal]["cor_canal"])
    assert _hex(marca.cor_do_canal(canal, "perfil")) == _hex(TABELA[canal]["cor_canal"])


@pytest.mark.parametrize("canal", CANAIS)
def test_cor_nos_posts_e_stories(canal):
    assert _hex(marca.CANAIS[canal]["cor_post"]) == _hex(TABELA[canal]["cor_post"])
    assert _hex(marca.cor_do_canal(canal, "post")) == _hex(TABELA[canal]["cor_post"])


@pytest.mark.parametrize("canal", CANAIS)
def test_fundo_da_tabela(canal):
    assert _hex(marca.CANAIS[canal]["fundo"]) == _hex(TABELA[canal]["fundo"])


@pytest.mark.parametrize("canal", CANAIS)
def test_extras_do_codigo(canal):
    extras = marca.CANAIS[canal]["extras"]
    for nome, valor in TABELA[canal]["extras"].items():
        assert nome in extras, f"{canal}: falta o extra '{nome}'"
        if isinstance(valor, list):
            assert [_hex(x) for x in extras[nome]] == [_hex(x) for x in valor], f"{canal}.{nome}"
        else:
            assert _hex(extras[nome]) == _hex(valor), f"{canal}.{nome}"


@pytest.mark.parametrize("canal", CANAIS)
def test_destaque_por_canal(canal):
    assert _hex(marca.CANAIS[canal]["destaque"]) == DESTAQUE[canal]


@pytest.mark.parametrize("canal", CANAIS)
def test_fontes_da_tabela(canal):
    fontes = marca.CANAIS[canal]["fontes"]
    for papel, nome in TABELA[canal]["fontes"].items():
        assert fontes.get(papel) == nome, f"{canal}: fonte '{papel}' deveria ser {nome!r}"
        assert nome in marca.ARQUIVOS_FONTE, f"{nome!r} não tem arquivo no resolvedor"


def test_gta6_e_o_ceu_em_degrade():
    assert _hex(marca.GTA6["rosa"]) == "#FF48A0" == marca.GTA_ROSA_POST
    assert _hex(marca.GTA6["laranja"]) == "#FFB054"
    assert _hex(marca.GTA6["noite"]) == "#101234"
    assert _hex(marca.GTA6["ciano"]) == "#46E1EB"
    assert _hex(marca.GTA6["texto"]) == "#FFE9F3"
    assert _hex(marca.GTA6["corpo"]) == _hex((245, 242, 255))
    assert [_hex(c) for c in marca.GTA6["ceu"]] == [_hex(c) for c in TABELA["gta"]["ceu"]]
    assert marca.CANAIS["gta"]["extras"]["ceu"] == marca.GTA6["ceu"]
    # título com degradê vertical rosa -> laranja + contorno noite
    assert [_hex(c) for c in marca.CANAIS["gta"]["extras"]["titulo_degrade"]] == ["#FF48A0", "#FFB054"]
    assert _hex(marca.CANAIS["gta"]["extras"]["contorno_titulo"]) == "#101234"


def test_constantes_de_conflito_expostas():
    assert marca.CARROS_COR_PERFIL == "#FF2D2D" and marca.CARROS_COR_POST == "#E61E2D"
    assert marca.GTA_ROSA_POST == "#FF48A0" and marca.GTA_ROSA_PERFIL == "#FF3CAA"
    assert marca.GTA_ROSA_SITE == "#FF3D8B"
    assert marca.FUTEBOL_VERDE == "#1ED760" and marca.FUTEBOL_AMARELO_RODADA1 == "#FFD23F"
    # os dois valores de cada conflito continuam diferentes (ninguém "resolveu" por conta própria)
    assert marca.CARROS_COR_PERFIL != marca.CARROS_COR_POST
    assert len({marca.GTA_ROSA_POST, marca.GTA_ROSA_PERFIL, marca.GTA_ROSA_SITE}) == 3
    # e a tabela usa o lado certo de cada conflito
    assert marca.CANAIS["carros"]["cor_canal"] == marca.CARROS_COR_PERFIL
    assert marca.CANAIS["carros"]["cor_post"] == marca.CARROS_COR_POST
    assert marca.CANAIS["gta"]["cor_canal"] == marca.GTA_ROSA_PERFIL
    assert marca.CANAIS["gta"]["cor_post"] == marca.GTA_ROSA_POST
    assert marca.CANAIS["futebol"]["destaque"] == marca.FUTEBOL_VERDE


def test_selo_hp_e_tratamento_de_foto():
    assert _hex(marca.SELO_HP["fundo"]) == "#FFFFFF" and _hex(marca.SELO_HP["texto"]) == _hex((15, 15, 18))
    assert marca.SELO_HP["fonte"] == "Bahnschrift Bold" and marca.SELO_HP["fonte_handle"] == "Bahnschrift SemiBold"
    assert marca.SELO_HP_GTA["fonte"] == "Segoe UI Black Italic"
    assert marca.TRATAMENTO_FOTO == {"contraste": 1.12, "cor": 1.10, "brilho": 0.96, "vinheta": 0.55}


# --- contraste -----------------------------------------------------------------------------
@pytest.mark.parametrize("canal", CANAIS)
def test_texto_branco_sobre_o_fundo_passa_wcag(canal):
    assert marca.contraste("#FFFFFF", marca.CANAIS[canal]["fundo"]) >= 4.5


def test_contraste_wcag_e_simetrico_e_tem_os_extremos():
    assert marca.contraste("#000000", "#FFFFFF") == pytest.approx(21.0)
    assert marca.contraste("#FFFFFF", "#000000") == pytest.approx(21.0)
    assert marca.contraste("#777777", "#777777") == pytest.approx(1.0)
    assert marca.luminancia("#FFFFFF") == pytest.approx(1.0)
    # o painel claro do Filmes com texto preto também passa
    assert marca.contraste("#000000", marca.CANAIS["filmes"]["extras"]["painel_claro"]) >= 4.5


def test_rgb_hex_e_misturar():
    assert marca.rgb("#FF48A0") == (255, 72, 160) and marca.rgb((1, 2, 3, 4)) == (1, 2, 3, 4)
    assert marca.rgb("#fff") == (255, 255, 255)
    assert marca.hex_de((255, 72, 160)) == "#FF48A0"
    assert marca.misturar("#000000", "#FFFFFF", 0.5) == (128, 128, 128)
    assert marca.misturar("#000000", "#FFFFFF", 0.0) == (0, 0, 0)
    assert marca.misturar("#000000", "#FFFFFF", 2.0) == (255, 255, 255)  # t fora de 0..1 é travado
    with pytest.raises(ValueError):
        marca.rgb("verde")


# --- tamanhos e zonas ----------------------------------------------------------------------
def test_tamanhos_da_tabela():
    assert marca.TAMANHOS["feed"] == marca.TAMANHOS["carrossel"] == (1080, 1350)
    for t in ("story", "reel", "capa_reel", "destaque", "carrossel_tiktok"):
        assert marca.TAMANHOS[t] == (1080, 1920)
    assert marca.TAMANHOS["perfil"] == (1080, 1080)
    assert marca.TAMANHOS["capa_youtube"] == (2560, 1440)
    assert marca.TAMANHOS["capa_youtube_segura"] == (1546, 423)
    assert marca.TAMANHOS["capa_facebook"] == (1640, 624)
    assert (marca.LARGURA_STORY, marca.ALTURA_STORY) == (1080, 1920)


def test_zonas_seguras_do_story():
    assert marca.SAFE_TOPO == 250 and marca.SAFE_BASE == 350
    assert marca.zona_segura() == (0, 250, 1080, 1570)
    assert marca.ZONA_ENQUETE == (110, 930, 970, 1480)
    assert marca.dentro_da_zona_segura(marca.ZONA_ENQUETE)
    # zona da figurinha de link (tarefa D): o retângulo que o prompt define, dentro do quadro,
    # abaixo da zona da enquete (sem sobreposição). A base dela (1640) entra nos 350 px de baixo
    # porque é onde o Instagram põe a figurinha de link — por isso NÃO passa em dentro_da_zona_segura.
    assert marca.ZONA_LINK == (140, 1500, 940, 1640)
    x0, y0, x1, y1 = marca.ZONA_LINK
    assert 0 <= x0 < x1 <= 1080 and 0 <= y0 < y1 <= 1920
    assert y0 >= marca.ZONA_ENQUETE[3]
    assert y0 >= marca.SAFE_TOPO
    assert not marca.dentro_da_zona_segura((0, 100, 1080, 300))     # invade o topo
    assert not marca.dentro_da_zona_segura((0, 300, 1080, 1600))    # invade a base


# --- texto ---------------------------------------------------------------------------------
def test_sem_emoji_tira_emoji_e_mantem_acento():
    assert marca.sem_emoji("Gol do Flamengo ⚽🔥 hoje!") == "Gol do Flamengo hoje!"
    assert marca.sem_emoji("Receita ☕️ de café") == "Receita de café"
    assert marca.sem_emoji("Ação, coração, pão") == "Ação, coração, pão"
    assert marca.sem_emoji("🇧🇷 Brasil") == "Brasil"
    assert marca.sem_emoji(None) == ""
    assert marca.tem_emoji("ok 🚀") and not marca.tem_emoji("só texto")


# --- resolvedor de fontes ------------------------------------------------------------------
@pytest.fixture
def sem_fontes_da_marca(tmp_path, monkeypatch):
    """Nenhuma fonte da marca em lugar nenhum: HP_FONTES, WINDIR e HP_FONTES_CACHE apontam para
    pastas temporárias vazias. Só o DejaVu do sistema (ou o padrão do Pillow) sobra."""
    for var in ("HP_FONTES", "WINDIR", "HP_FONTES_CACHE"):
        p = tmp_path / var.lower()
        p.mkdir()
        monkeypatch.setenv(var, str(p))
    marca.limpar_cache_fontes()
    yield tmp_path
    marca.limpar_cache_fontes()


def _dejavu_existe() -> bool:
    return any((p / n).is_file() for p in marca.DEJAVU_PASTAS for n in marca.DEJAVU_NEGRITO + marca.DEJAVU_NORMAL)


def test_resolvedor_cai_no_dejavu_sem_quebrar(sem_fontes_da_marca):
    for nome in ("Anton", "Barlow Medium", "Bauhaus 93", "Segoe UI Black Italic", "Bahnschrift Bold",
                 "DM Serif Display", "fonte-que-nao-existe"):
        r = marca.resolver_fonte(nome)
        assert r.exata is False and r.nome == nome
        assert r.origem in ("dejavu", "pillow")
        if _dejavu_existe():
            assert r.origem == "dejavu" and Path(r.caminho).is_file()
        f = marca.fonte(nome, 48)            # nunca levanta exceção
        assert f is not None and hasattr(f, "getbbox")
    assert marca.fontes_faltando(["Anton", "Barlow"]) == ["Anton", "Barlow"]


def test_dejavu_negrito_para_fonte_pesada_e_normal_para_leve(sem_fontes_da_marca):
    if not _dejavu_existe():
        pytest.skip("sem DejaVu nesta máquina")
    assert marca.resolver_fonte("Anton").usada == "DejaVu Sans Bold"
    assert marca.resolver_fonte("Barlow ExtraBold").usada == "DejaVu Sans Bold"
    assert marca.resolver_fonte("Barlow").usada == "DejaVu Sans"


def test_hp_fontes_com_o_arquivo_renomeado_acha_a_fonte_exata(sem_fontes_da_marca, monkeypatch):
    origem = next((p / n for p in marca.DEJAVU_PASTAS for n in marca.DEJAVU_NEGRITO if (p / n).is_file()), None)
    if origem is None:
        pytest.skip("sem DejaVu para copiar")
    pasta = Path(sem_fontes_da_marca) / "hp_fontes"           # é o que HP_FONTES aponta
    shutil.copy(origem, pasta / "Anton-Regular.ttf")
    marca.limpar_cache_fontes()
    r = marca.resolver_fonte("Anton")
    assert r.exata is True and r.origem == "pc" and r.usada == "Anton"
    assert Path(r.caminho) == pasta / "Anton-Regular.ttf"
    f = marca.fonte("Anton", 40)
    assert f is not None and f.getbbox("HP")[2] > 0
    assert marca.fontes_faltando(["Anton"]) == []
    # e o cache do Pillow devolve o mesmo objeto para o mesmo pedido
    assert marca.fonte("Anton", 40) is f
    # a ordem de procura: (1) HP_FONTES (2) Windows (3) cache (4) DejaVu
    assert marca.pastas_de_fontes()[:3] == [pasta, Path(sem_fontes_da_marca) / "windir" / "Fonts",
                                            Path(sem_fontes_da_marca) / "hp_fontes_cache"]


def test_substituta_na_ordem_antes_do_dejavu(sem_fontes_da_marca):
    origem = next((p / n for p in marca.DEJAVU_PASTAS for n in marca.DEJAVU_NEGRITO if (p / n).is_file()), None)
    if origem is None:
        pytest.skip("sem DejaVu para copiar")
    cache = Path(sem_fontes_da_marca) / "hp_fontes_cache"
    shutil.copy(origem, cache / "Anton-Regular.ttf")
    marca.limpar_cache_fontes()
    r = marca.resolver_fonte("Bauhaus 93")      # não existe fora do Windows: substituta Anton (do cache)
    assert r.exata is False and r.usada == "Anton" and r.origem == "cache"


def test_baixar_fontes_sem_transporte_nao_baixa_nada(sem_fontes_da_marca):
    destino = Path(sem_fontes_da_marca) / "hp_fontes_cache"
    faltam = marca.baixar_fontes_ofl(destino, transporte=None)
    assert set(faltam) == set(marca.FONTES_OFL)
    assert list(destino.iterdir()) == []                       # nada gravado, nada de rede
    # com transporte injetado grava de forma atômica (sem .tmp sobrando)
    chamadas = []

    def transporte(url):
        chamadas.append(url)
        return b"x" * 2000
    feitas = marca.baixar_fontes_ofl(destino, transporte, so_faltando=False)
    assert set(feitas) == set(marca.FONTES_OFL)
    assert all(u.startswith(marca.URL_GOOGLE_FONTS_RAW + "ofl/") for u in chamadas)
    assert not list(destino.glob("*.tmp")) and (destino / "Anton-Regular.ttf").stat().st_size == 2000


def test_resumo_e_cli_cores(capsys):
    linhas = marca.resumo()
    assert len(linhas) == 6 and linhas[0].startswith("gta") and "#FF48A0" in linhas[0]
    assert marca.main(["cores"]) == 0
    assert "hp.futebol" in capsys.readouterr().out
