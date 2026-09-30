"""Testes da prévia no celular (scripts/painel/previa_celular.*).

A parte em Python (integração com o HTML do painel e a demo) roda sempre; as
funções do JavaScript rodam com node, se houver (senão, pula).
"""
from __future__ import annotations

import html as _html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PASTA = Path(__file__).resolve().parents[1] / "painel"
if str(PASTA) not in sys.path:
    sys.path.insert(0, str(PASTA))

import previa_celular as pc  # noqa: E402

NODE = shutil.which("node")
JS = (PASTA / "previa_celular.js").read_text(encoding="utf-8")
CSS = (PASTA / "previa_celular.css").read_text(encoding="utf-8")


@pytest.fixture(autouse=True)
def _raizes(tmp_path, monkeypatch):
    monkeypatch.setenv("HP_LOCAL", str(tmp_path / "HypadoLocal"))
    monkeypatch.setenv("HP_DRIVE", str(tmp_path / "Drive"))


def rodar_node(corpo: str, dados=None):
    if not NODE:
        pytest.skip("node não está instalado neste ambiente")
    codigo = ("const P = require(require('path').join(process.argv[1], 'previa_celular.js'));\n"
              "const D = JSON.parse(process.argv[2] || 'null');\n" + corpo)
    r = subprocess.run([NODE, "-e", codigo, str(PASTA), json.dumps(dados, ensure_ascii=False)],
                       capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


# ---------------------------------------------------------------- arquivos e demo
def test_demo_autocontida_e_em_dia():
    demo = (PASTA / "previa_demo.html").read_text(encoding="utf-8")
    assert demo == pc.montar_demo_html(), "rode: python scripts/painel/previa_celular.py demo"
    assert not re.search(r"<script[^>]+src=", demo, re.I)      # nenhum script externo
    assert not re.search(r"<link[^>]+stylesheet", demo, re.I)   # nenhum CSS externo
    assert not re.search(r"https?://", demo)                    # nada da internet
    assert "<title>Prévia no celular</title>" in demo
    assert ':root[data-theme="dark"]' in demo and "prefers-color-scheme: dark" in demo


def test_sem_logos_nem_scripts_externos():
    for txt in (JS, CSS):
        assert "</script" not in txt.lower()
        assert not re.search(r"https?://", txt)
        assert "import " not in txt
    # só rótulos de texto para as redes (nenhuma imagem/logo embutida)
    assert "data:image" not in JS and "data:image" not in CSS
    for rotulo in ("Instagram Reels", "Instagram Feed", "Instagram Story", "TikTok", "YouTube Shorts",
                   "Facebook", "Threads", "Pinterest"):
        assert f'"{rotulo}"' in JS


def test_css_acessivel_e_responsivo():
    assert '[data-pc-tema="escuro"]' in CSS                       # tema escuro
    assert "prefers-reduced-motion" in CSS
    assert "@media (max-width: 720px)" in CSS                     # tela cheia no celular
    assert ":focus-visible" in CSS
    assert "aspect-ratio: 9 / 19.5" in CSS                        # formato de smartphone


def test_bloco_e_embutir_idempotente():
    html = "<div class=wrap></div>\n<script>const BY = {};</script>"
    h1 = pc.embutir_previa(html)
    assert h1.index("previa-celular-js") < h1.index("const BY")
    assert h1.count(pc.MARCA_INI) == 1 and "previa-celular-css" in h1
    assert pc.embutir_previa(h1) == h1
    com_head = pc.embutir_previa("<html><head><title>x</title></head><body></body></html>")
    assert com_head.index("previa-celular-js") < com_head.index("</head>")


MODELO_PAINEL = """<div class="lista" id="agenda"></div>
<script>
function renderAgenda(){
  const zoom = (x.capa_zoom || x.capa_img) ? ` role="button" tabindex="0" title="Ampliar a capa" data-zoom="1"` : "";
  $("agenda").querySelectorAll(".thumb.zoom").forEach(t => {
    const abrir = () => ampliar(E.dados.agenda[dia].itens[+t.dataset.zoom]);
    t.onclick = abrir;
  });
}
</script>"""


def test_ligar_no_painel():
    novo, rel = pc.ligar_no_painel(MODELO_PAINEL)
    assert rel == {"bloco": True, "clique": "ligado", "titulo": "trocado"}
    assert pc.CLIQUE_NOVO in novo and pc.CLIQUE_ANTIGO not in novo
    assert 'title="Ver prévia no celular"' in novo
    assert "function abrirPrevia(x, origem)" in novo
    assert "Ampliar capa" in novo                                  # o zoom continua disponível
    de_novo, rel2 = pc.ligar_no_painel(novo)
    assert de_novo == novo
    assert rel2 == {"bloco": True, "clique": "ja_estava", "titulo": "ja_estava"}


def test_ligar_em_modelo_diferente_so_avisa():
    novo, rel = pc.ligar_no_painel("<div>outro</div>")
    assert rel["clique"] == "nao_encontrado" and "<div>outro</div>" in novo


def test_atributo_previa_escapado_e_sem_capa():
    post = {"capa": "data:image/webp;base64,AAAA", "legenda": 'Diz "oi" <b>', "conta": "@hp.receitas",
            "redes": ["instagram"], "video": ""}
    attr = pc.atributo_previa(post)
    valor = re.match(r'data-previa="(.*)"$', attr).group(1)
    assert '"' not in valor and "<" not in valor
    volta = json.loads(_html.unescape(valor))
    assert volta == {"legenda": 'Diz "oi" <b>', "conta": "@hp.receitas", "redes": ["instagram"]}
    assert "capa" in json.loads(_html.unescape(pc.atributo_previa(post, sem_capa=False)[13:-1]))


def test_cli(tmp_path, capsys):
    destino = tmp_path / "demo.html"
    assert pc.main(["demo", "--saida", str(destino)]) == 0
    assert destino.read_text(encoding="utf-8") == pc.montar_demo_html()
    arq = tmp_path / "painel.html"
    arq.write_text(MODELO_PAINEL, encoding="utf-8")
    capsys.readouterr()
    assert pc.main(["embutir", str(arq), "--painel"]) == 0
    assert json.loads(capsys.readouterr().out)["clique"] == "ligado"
    with pytest.raises(SystemExit) as e:
        pc.main(["--help"])
    assert e.value.code == 0 and "uso:" in capsys.readouterr().out


# ---------------------------------------------------------------- JavaScript (node)
def test_cortar_legenda():
    casos = [
        ["Curta demais", 55, 1],
        ["No GTA 6 um NPC pode ROUBAR o seu carro enquanto você está parado no semáforo? Olha", 55, 1],
        ["Linha 1\nLinha 2\nLinha 3", 125, 2],
        ["😳" * 60, 55, 0],
        ["Texto qualquer", 0, 0],
        ["palavra" * 20, 30, 0],
        ["", 55, 1],
    ]
    res = rodar_node("console.log(JSON.stringify(D.map(c => P.cortarLegenda(c[0], c[1], c[2]))));", casos)
    assert res[0] == {"visivel": "Curta demais", "cortou": False, "total": 12}
    assert res[1]["cortou"] is True
    assert res[1]["visivel"] == "No GTA 6 um NPC pode ROUBAR o seu carro enquanto você"   # corta na palavra
    assert len(res[1]["visivel"]) <= 55
    assert res[2] == {"visivel": "Linha 1\nLinha 2", "cortou": True, "total": 23}
    assert res[3]["total"] == 60 and res[3]["cortou"] is True           # emoji conta como 1
    assert len(list(res[3]["visivel"])) == 55
    assert res[4] == {"visivel": "", "cortou": True, "total": 14}       # Story: não mostra legenda
    assert len(res[5]["visivel"]) == 30                                  # palavra gigante: corta seco
    assert res[6] == {"visivel": "", "cortou": False, "total": 0}


def test_redes_do_post():
    posts = [
        {"tipo": "reels", "redes": ["instagram", "tiktok", "youtube", "facebook", "threads"]},
        {"tipo": "story", "redes": ["instagram", "facebook"]},
        {"tipo": "carrossel", "redes": ["instagram", "facebook", "threads", "pinterest"]},
        {"tipo": "texto", "redes": ["threads"]},
        {"redes": "Reels, Instagram Feed, YouTube Shorts, desconhecida"},
        {},
        {"video": "v.mp4", "redes": ["Instagram"]},
    ]
    res = rodar_node("console.log(JSON.stringify(D.map(p => P.redesDoPost(p))));", posts)
    assert res[0] == ["instagram_reels", "tiktok", "youtube_shorts", "facebook_reels", "threads"]
    assert res[1] == ["instagram_story", "facebook_story"]
    assert res[2] == ["instagram_feed", "facebook", "threads", "pinterest"]
    assert res[3] == ["threads"]
    assert res[4] == ["instagram_reels", "instagram_feed", "youtube_shorts"]
    assert res[5] == ["instagram_reels", "instagram_feed", "instagram_story", "tiktok", "youtube_shorts",
                      "facebook", "threads", "pinterest"]                  # sem redes: as 8
    assert res[6] == ["instagram_reels"]


def test_tabela_de_redes_proporcoes():
    res = rodar_node("const o = {}; for (const k in P.REDES) o[k] = [P.REDES[k].proporcao, P.REDES[k].limite,"
                     " !!P.REDES[k].zonas]; console.log(JSON.stringify(o));")
    assert res["instagram_reels"][0] == "9:16" and res["instagram_reels"][2] is True
    assert res["instagram_feed"][0] == "4:5"
    assert res["instagram_story"][:2] == ["9:16", 0]
    assert res["tiktok"][0] == "9:16" and res["youtube_shorts"][0] == "9:16"
    assert res["threads"][0] == "1:1"
    assert res["pinterest"][0] == "2:3"
    assert {v[0] for v in res.values()} == {"9:16", "4:5", "1:1", "2:3"}


def test_calcular_corte_da_capa():
    res = rodar_node("console.log(JSON.stringify([P.calcularCorte(1080,1920,'4:5'), P.calcularCorte(1080,1080,'4:5'),"
                     " P.calcularCorte(1080,1350,'4:5'), P.calcularCorte(1000,1500,'9:16'), P.calcularCorte(0,0,'4:5')]));")
    assert res[0] == {"perde": 30, "onde": "em cima e embaixo"}   # 9:16 no feed 4:5
    assert res[1] == {"perde": 20, "onde": "dos lados"}
    assert res[2] == {"perde": 0, "onde": "nada"}
    assert res[3]["onde"] == "dos lados"
    assert res[4] is None


def test_de_item_agenda_do_painel():
    item = {"canal": "receitas", "hora": "09:00", "redes": ["instagram", "threads"], "tipo": "carrossel",
            "titulo": "Bolo que não afunda", "capa_img": "data:image/webp;base64,AA",
            "capa_zoom": "z/abc.webp", "laminas": ["z/abc.webp", "z/def.webp"], "n_laminas": 2}
    canais = {"receitas": {"id": "receitas", "nome": "Receitas | HP", "handle": "@hp.receitas", "cor": "#ff7a1a"}}
    res = rodar_node("console.log(JSON.stringify(P.deItemAgenda(D.item, D.canais, {avatares: {receitas: 'av'}})));",
                     {"item": item, "canais": canais})
    assert res["capa"] == "z/abc.webp" and res["capa_rapida"] == "data:image/webp;base64,AA"
    assert res["conta"] == "@hp.receitas" and res["canal"] == "Receitas | HP" and res["cor"] == "#ff7a1a"
    assert res["laminas"] == ["z/abc.webp", "z/def.webp"] and res["avatar"] == "av"
    assert res["legenda"] == "" and res["titulo"] == "Bolo que não afunda"


def test_telas_de_todas_as_redes():
    post = {"canal": "GTA 6 | HP", "conta": "@hpgta6", "tipo": "reels", "capa": "c.jpg",
            "titulo": "Título do vídeo", "legenda": "Legenda comprida " * 20 + "#gta6 @rockstar <script>x</script>"}
    res = rodar_node("""
      const o = {};
      for (const k of P.ORDEM) o[k] = P.montarTela(D, k, {expandida: false, lamina: 0});
      o.expandida = P.montarTela(D, 'instagram_feed', {expandida: true, lamina: 0});
      console.log(JSON.stringify(o));
    """, post)
    for k in ("instagram_reels", "instagram_feed", "tiktok", "facebook", "facebook_reels"):
        assert 'data-pc-acao="mais"' in res[k], k                 # legenda cortada com "mais"
        assert "data-pc-midia" in res[k]
    assert "Ver mais" in res["facebook"]
    assert "Inscrever-se" in res["youtube_shorts"] and "Título do vídeo" in res["youtube_shorts"]
    assert 'data-pc-acao="mais"' not in res["instagram_story"]     # story não mostra legenda
    assert "Enviar mensagem" in res["instagram_story"]
    assert "pc-z-dir" in res["tiktok"] and "pc-z-topo" in res["instagram_story"]
    assert "<script>" not in json.dumps(res) and "&lt;script&gt;" in res["threads"]
    assert '<span class="pc-tag">#gta6</span>' in res["expandida"]
    assert 'data-pc-acao="mais"' not in res["expandida"]
    for k, tela in res.items():
        assert "pc-status" in tela, k
        assert ("pc-nav" in tela) == ("story" not in k), k           # story não tem barra de baixo
