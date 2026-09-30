"""Testes da página de links: cores (contraste AA), fundos clarinhos e botões."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

PASTA = Path(__file__).resolve().parents[1] / "pagina_links"
if str(PASTA) not in sys.path:
    sys.path.insert(0, str(PASTA))

import gerar_fundos as gf  # noqa: E402

NOMES = ["GTA 6 | HP", "Futebol | HP", "Filmes e Séries | HP", "Receitas | HP", "Carros | HP", "Destinos | HP"]


@pytest.fixture(autouse=True)
def _raizes(tmp_path, monkeypatch):
    monkeypatch.setenv("HP_LOCAL", str(tmp_path / "HypadoLocal"))
    monkeypatch.setenv("HP_DRIVE", str(tmp_path / "Drive"))


@pytest.fixture(scope="module")
def gerado(tmp_path_factory):
    """Gera tudo uma vez (sem foto) numa pasta temporária."""
    base = tmp_path_factory.mktemp("links")
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("HP_LOCAL", str(base / "HypadoLocal"))
        res = gf.gerar_tudo()
    return res


def _foto_teste(caminho: Path, escura: bool = True) -> Path:
    """Foto de mentira com formas e cores (escura, para testar o clareamento)."""
    img = Image.new("RGB", (1200, 900), (15, 20, 30) if escura else (240, 240, 235))
    d = ImageDraw.Draw(img)
    d.ellipse([100, 100, 700, 700], fill=(200, 30, 40))
    d.rectangle([600, 300, 1150, 850], fill=(10, 90, 30))
    d.line([(0, 0), (1200, 900)], fill=(250, 250, 0), width=40)
    img.save(caminho, "JPEG", quality=90)
    return caminho


# ---------------------------------------------------------------- contraste
def test_formula_de_contraste_wcag():
    assert gf.contraste("#000000", "#FFFFFF") == pytest.approx(21.0)
    assert gf.contraste("#FFFFFF", "#000000") == pytest.approx(21.0)
    assert gf.contraste("#777777", "#FFFFFF") == pytest.approx(4.48, abs=0.01)   # clássico "quase AA"
    assert gf.contraste("#767676", "#FFFFFF") == pytest.approx(4.54, abs=0.01)   # menor cinza AA
    assert gf.contraste("#FF3D8B", "#FF3D8B") == pytest.approx(1.0)
    assert gf.hex_para_rgb("#abc") == (0xAA, 0xBB, 0xCC)
    with pytest.raises(ValueError):
        gf.hex_para_rgb("#12345")


def test_todas_as_cores_tem_contraste_aa():
    canais = gf.carregar_cores()
    assert [c["nome"] for c in canais] == NOMES
    for c in canais:
        calc = gf.contraste(c["cor"], c["cor_texto_botao"])
        assert calc >= 4.5, c["nome"]
        assert c["contraste"] == pytest.approx(calc, abs=0.01), "número anotado no JSON bate com o cálculo"
        # contorno do botão aparece sobre fundo claro (WCAG 1.4.11, >= 3:1)
        assert gf.contraste(c["cor_borda"], "#FFFFFF") >= 3.0
        assert gf.contraste(gf.escolher_cor_texto(c["cor"]), c["cor"]) >= 4.5


def test_cor_sem_contraste_e_recusada(tmp_path):
    ruim = tmp_path / "cores.json"
    ruim.write_text(json.dumps({"canais": [
        {"slug": "x", "nome": "X | HP", "cor": "#F5B301", "cor_texto_botao": "#FFFFFF"}]}), encoding="utf-8")
    with pytest.raises(gf.ErroContraste) as e:
        gf.carregar_cores(ruim)
    assert "Sugestão: #141413" in str(e.value)
    errado = tmp_path / "cores2.json"
    errado.write_text(json.dumps({"canais": [
        {"slug": "x", "nome": "X | HP", "cor": "#FF3D8B", "cor_texto_botao": "#141413", "contraste": 9.9}]}),
        encoding="utf-8")
    with pytest.raises(gf.ErroContraste):
        gf.carregar_cores(errado)
    with pytest.raises(gf.ErroContraste):
        gf.gerar_botao({"nome": "X", "cor": "#F5B301", "cor_texto_botao": "#FFFFFF"})


def test_cli_contraste(capsys, tmp_path):
    assert gf.main(["contraste"]) == 0
    out = capsys.readouterr().out
    assert out.count("OK (AA)") == 6
    ruim = tmp_path / "cores.json"
    ruim.write_text(json.dumps({"canais": [
        {"slug": "x", "nome": "X | HP", "cor": "#1ED760", "cor_texto_botao": "#FFFFFF"}]}), encoding="utf-8")
    assert gf.main(["contraste", "--cores", str(ruim)]) == 1
    assert "FALHOU" in capsys.readouterr().out


# ---------------------------------------------------------------- fundos
def test_fundos_sem_foto_tamanho_e_clarinhos(gerado):
    assert set(gerado["canais"]) == {"gta", "futebol", "filmes", "receitas", "carros", "destinos"}
    for slug, item in gerado["canais"].items():
        assert item["foto"] is None
        for chave, tam in (("faixa", (1600, 400)), ("quadrado", (1080, 1080))):
            p = Path(item[chave])
            assert p.exists() and p.parent.name == "fundos" and p.parent.parent.name == "pagina_links"
            with Image.open(p) as img:
                assert img.size == tam, (slug, chave)
                assert gf.luminancia_media(img) > 200, (slug, chave)
                # não é branco chapado: tem a cor do canal (algum pixel mais escuro que 245)
                assert min(img.convert("L").getextrema()) < 245


def test_fundo_com_foto_escura_fica_clarinho(tmp_path):
    foto = _foto_teste(tmp_path / "escura.jpg")
    canal = {c["slug"]: c for c in gf.carregar_cores()}["futebol"]
    assert gf.luminancia_media(Image.open(foto)) < 100
    for tam in gf.TAMANHOS_FUNDO:
        img = gf.gerar_fundo(canal, tam, foto)
        assert img.size == tam
        assert gf.luminancia_media(img) > 200
    # clara também continua clara e não vira branco puro
    clara = gf.gerar_fundo(canal, (1600, 400), _foto_teste(tmp_path / "clara.jpg", escura=False))
    assert 200 < gf.luminancia_media(clara) < 255


def test_foto_na_pasta_e_foto_por_parametro(tmp_path):
    pasta = tmp_path / "HypadoLocal" / "pagina_links" / "fotos"
    pasta.mkdir(parents=True)
    _foto_teste(pasta / "receitas.jpg")
    outra = _foto_teste(tmp_path / "carro.jpg")
    res = gf.gerar_tudo(fotos={"carros": outra}, somente=["receitas", "carros", "gta"])
    assert set(res["canais"]) == {"receitas", "carros", "gta"}
    assert res["canais"]["receitas"]["foto"].endswith("receitas.jpg")
    assert res["canais"]["carros"]["foto"] == str(outra)
    assert res["canais"]["gta"]["foto"] is None
    for item in res["canais"].values():
        assert item["luminancia_faixa"] > 200 and item["luminancia_quadrado"] > 200
    assert (tmp_path / "HypadoLocal" / "pagina_links" / "fundos" / "receitas_1080x1080.jpg").exists()


def test_simular_nao_grava_nada(tmp_path):
    res = gf.gerar_tudo(simular=True)
    assert res["simulado"] is True and len(res["canais"]) == 6
    assert not (tmp_path / "HypadoLocal" / "pagina_links" / "fundos").exists()


def test_erros_claros(tmp_path):
    with pytest.raises(ValueError):
        gf.gerar_tudo(somente=["inexistente"])
    with pytest.raises(FileNotFoundError):
        gf.gerar_tudo(fotos={"gta": tmp_path / "nao_existe.jpg"}, somente=["gta"])


# ---------------------------------------------------------------- botões
def test_botoes_gerados(gerado):
    canais = {c["slug"]: c for c in gf.carregar_cores()}
    for slug, item in gerado["canais"].items():
        p = Path(item["botao"])
        assert p.exists() and p.suffix == ".png"
        with Image.open(p) as img:
            assert img.size == (1000, 200)
            assert img.mode == "RGBA"
            assert img.getpixel((0, 0))[3] == 0            # canto transparente (botão arredondado)
            rgb = img.convert("RGB")
            cor = gf.hex_para_rgb(canais[slug]["cor"])
            txt = gf.hex_para_rgb(canais[slug]["cor_texto_botao"])
            miolo = [rgb.getpixel((x, y)) for x in range(100, 900, 4) for y in range(30, 170, 4)]

            def perto(a, b, tol=40):
                return sum(abs(i - j) for i, j in zip(a, b)) <= tol
            n_cor = sum(perto(px, cor) for px in miolo)
            n_txt = sum(perto(px, txt) for px in miolo)
            assert n_cor / len(miolo) > 0.5, slug            # botão na cor do canal
            assert n_txt / len(miolo) > 0.03, slug           # tem texto escrito
            # o pixel do texto contra o do botão passa AA de verdade
            assert gf.contraste(gf.rgb_para_hex(cor), gf.rgb_para_hex(txt)) >= 4.5


def test_botao_texto_longo_cabe(tmp_path):
    canal = gf.carregar_cores()[2]
    img = gf.gerar_botao(canal, "Filmes e Séries | HP no TikTok, YouTube e Threads")
    assert img.size == (1000, 200)
    # nenhum pixel de texto encosta nas pontas (texto coube)
    txt = gf.hex_para_rgb(canal["cor_texto_botao"])
    borda = [img.getpixel((x, y))[:3] for x in list(range(0, 60)) + list(range(940, 1000)) for y in range(0, 200, 5)]
    assert not any(sum(abs(i - j) for i, j in zip(px, txt)) < 30 for px in borda)


def test_cartoes_prontos(gerado):
    canais = {c["slug"]: c for c in gf.carregar_cores()}
    for slug, item in gerado["canais"].items():
        with Image.open(item["cartao"]) as img:
            assert img.size == (1600, 400)
            rgb = img.convert("RGB")
            # meio = botão na cor do canal; canto = fundo clarinho
            meio = rgb.getpixel((340, 200))          # ponta esquerda do botão, longe do texto
            assert sum(abs(i - j) for i, j in zip(meio, gf.hex_para_rgb(canais[slug]["cor"]))) < 45, slug
            assert sum(rgb.getpixel((20, 20))) / 3 > 200


def test_previa_html(gerado):
    previa = Path(gerado["previa"])
    html = previa.read_text(encoding="utf-8")
    for slug in gerado["canais"]:
        assert f"fundos/{slug}_1600x400.jpg" in html and f"botoes/{slug}_botao.png" in html
    assert 'name="viewport"' in html and "http" not in html


def test_cli_gerar_e_botao(tmp_path, capsys):
    assert gf.main(["--canal", "destinos"]) == 0                      # sem comando = gerar
    res = json.loads(capsys.readouterr().out)
    assert list(res["canais"]) == ["destinos"]
    assert gf.main(["botao", "receitas", "Receitas no TikTok"]) == 0
    arq = Path(capsys.readouterr().out.strip())
    assert arq.exists() and Image.open(arq).size == (1000, 200)
    assert gf.main(["botao", "nada", "x"]) == 1
    assert gf.main(["gerar", "--foto", "semigual"]) == 1
    capsys.readouterr()
    with pytest.raises(SystemExit) as e:
        gf.main(["--help"])
    assert e.value.code == 0 and "uso:" in capsys.readouterr().out
    logs = list((tmp_path / "HypadoLocal" / "app" / "logs").glob("pagina_links_*.log"))
    assert logs
