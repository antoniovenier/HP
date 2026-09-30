"""Testes do selo das abas (scripts/painel/selo_abas.py e selo_abas.js).

Os mesmos casos (selo_casos.json) rodam na versão Python e, se houver node,
na versão JavaScript: as duas têm de dar o mesmo número.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PASTA = Path(__file__).resolve().parents[1] / "painel"
if str(PASTA) not in sys.path:
    sys.path.insert(0, str(PASTA))

import selo_abas as sa  # noqa: E402

CASOS = json.loads((PASTA / "selo_casos.json").read_text(encoding="utf-8"))
NODE = shutil.which("node")


@pytest.fixture(autouse=True)
def _raizes(tmp_path, monkeypatch):
    monkeypatch.setenv("HP_LOCAL", str(tmp_path / "HypadoLocal"))
    monkeypatch.setenv("HP_DRIVE", str(tmp_path / "Drive"))


def rodar_node(codigo: str):
    if not NODE:
        pytest.skip("node não está instalado neste ambiente")
    r = subprocess.run([NODE, "-e", codigo, str(PASTA)], capture_output=True, text=True,
                       encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


# ---------------------------------------------------------------- Python
def test_zero_nao_mostra_selo():
    assert sa.contar_selo([]) == 0
    assert sa.texto_selo(0) == ""
    assert sa.html_selo(0) == ""
    assert sa.html_selo(sa.contar_selo({"nao": []}, "nao")) == ""


def test_um_item_mostra_1():
    assert sa.contar_selo([{"texto": "Criar o TikTok do Futebol"}]) == 1
    assert sa.html_selo(1) == '<b class="num">1</b>'
    assert sa.html_selo(150) == '<b class="num">99+</b>'


def test_placeholder_nao_conta():
    # o bug do painel: aba "Não urgentes" vazia mostrava "1"
    assert sa.contar_selo([""]) == 0                       # "".split("\n") -> [""]
    assert sa.contar_selo("".split("\n")) == 0
    assert sa.contar_selo(["Nenhum item"]) == 0
    assert sa.contar_selo([{"texto": "Nada aqui."}]) == 0
    assert sa.contar_selo([{"texto": "x", "placeholder": True}]) == 0
    assert sa.contar_selo(["Nenhum item", "Pagar o domínio"]) == 1


@pytest.mark.parametrize("caso", CASOS["casos"], ids=[c["nome"] for c in CASOS["casos"]])
def test_casos_compartilhados_python(caso):
    assert sa.contar_selo(caso["itens"], caso["aba"]) == caso["esperado"]


@pytest.mark.parametrize("selo", CASOS["selos"], ids=[str(s["n"]) for s in CASOS["selos"]])
def test_texto_do_selo(selo):
    assert sa.texto_selo(selo["n"]) == selo["texto"]


def test_html_aba_pronta():
    assert sa.html_aba("Não urgentes", [""], "nao") == \
        '<button class="tab" type="button" role="tab" aria-selected="false" data-k="nao">Não urgentes</button>'
    assert sa.html_aba("Hoje", ["a", "b"], "hoje", selecionada=True).endswith(
        'data-k="hoje">Hoje <b class="num">2</b></button>')
    assert "&lt;" in sa.html_aba("<x>", [], "k")


def test_limpar_pendencias_na_origem():
    dados = {"sistema": {"pendencias": {
        "voce": [{"data": "2026-09-30", "texto": "Outlook de Carros"}, "", {"texto": ""}, "Nenhum item"],
        "diretor": ["Emulador pronto", "  "]}}}
    rem = sa.limpar_pendencias(dados)
    assert rem == {"voce": 3, "diretor": 1}
    assert dados["sistema"]["pendencias"]["voce"] == [{"data": "2026-09-30", "texto": "Outlook de Carros"}]
    assert sa.limpar_pendencias({}) == {}


MODELO = """<style>.num{display:inline-flex}</style>
<div id="tarefasDias"></div>
<script>
function tarefasPorDia(){
  for(const bruto of p.voce || []){
    const o = typeof bruto === "string" ? {texto:bruto} : {...bruto};
    const g = (o.todo_dia || o.urgente || (o.data && o.data <= hoje)) ? "hoje" : o.data ? o.data : "nao";
    (grupos[g] ||= []).push(o);
  }
}
function renderTarefas(){
  x = botoes.map(([k, nome]) => `<button class="tab" data-k="${k}">${esc(nome)} <b class="num">${g[k].length}</b></button>`);
}
</script>"""


def test_corrigir_html_do_painel():
    novo, rel = sa.corrigir_html_painel(MODELO)
    assert rel == {"script": True, "selo": "corrigido", "pular_vazio": "corrigido"}
    assert '<b class="num">${g[k].length}</b>' not in novo
    assert "${SeloAbas.htmlSelo(SeloAbas.contarSelo(g, k))}" in novo
    assert "    if(!SeloAbas.ehItemReal(o.texto)) continue;\n    const g = (o.todo_dia" in novo
    # o script do selo entra ANTES do código do painel
    assert novo.index("selo-abas-js") < novo.index("function tarefasPorDia")
    # rodar de novo não duplica nada
    de_novo, rel2 = sa.corrigir_html_painel(novo)
    assert de_novo == novo
    assert rel2 == {"script": True, "selo": "ja_estava", "pular_vazio": "ja_estava"}


def test_corrigir_html_modelo_diferente_so_avisa():
    novo, rel = sa.corrigir_html_painel("<div>outro painel</div><script>1</script>")
    assert rel["selo"] == "nao_encontrado" and rel["pular_vazio"] == "nao_encontrado"
    assert "<div>outro painel</div>" in novo


def test_cli(tmp_path, capsys):
    arq = tmp_path / "dados.json"
    arq.write_text(json.dumps({"sistema": {"pendencias": {"voce": ["", "Tarefa A"]}}}), encoding="utf-8")
    assert sa.main(["contar", str(arq)]) == 0
    assert capsys.readouterr().out.strip() == "1"
    assert sa.main(["limpar", str(arq)]) == 0
    assert json.loads(arq.read_text(encoding="utf-8"))["sistema"]["pendencias"]["voce"] == ["Tarefa A"]
    html = tmp_path / "painel.html"
    html.write_text(MODELO, encoding="utf-8")
    assert sa.main(["corrigir", str(html)]) == 0
    assert "SeloAbas.htmlSelo" in html.read_text(encoding="utf-8")
    capsys.readouterr()
    assert sa.main(["html", "0"]) == 0
    assert capsys.readouterr().out.strip() == ""
    with pytest.raises(SystemExit) as e:
        sa.main(["--help"])
    assert e.value.code == 0 and "uso:" in capsys.readouterr().out


# ---------------------------------------------------------------- JavaScript (node)
def test_casos_compartilhados_js():
    res = rodar_node("""
      const path = require('path'), fs = require('fs'), pasta = process.argv[1];
      const S = require(path.join(pasta, 'selo_abas.js'));
      const casos = JSON.parse(fs.readFileSync(path.join(pasta, 'selo_casos.json'), 'utf8'));
      console.log(JSON.stringify({
        contagens: casos.casos.map(c => S.contarSelo(c.itens, c.aba)),
        selos: casos.selos.map(s => S.textoSelo(s.n)),
        html0: S.htmlSelo(0), html3: S.htmlSelo(3)
      }));
    """)
    assert res["contagens"] == [c["esperado"] for c in CASOS["casos"]]
    assert res["selos"] == [s["texto"] for s in CASOS["selos"]]
    assert res["html0"] == "" and res["html3"] == '<b class="num">3</b>'


def test_render_selo_js_some_no_zero():
    res = rodar_node("""
      const S = require(require('path').join(process.argv[1], 'selo_abas.js'));
      function el(){ return {hidden:false, textContent:'1', attrs:{}, style:{display:'inline-flex',
        removeProperty(k){ this[k] = ''; }}, setAttribute(k, v){ this.attrs[k] = v; },
        removeAttribute(k){ delete this.attrs[k]; }}; }
      const a = S.renderSelo(el(), S.contarSelo({nao: ['']}, 'nao'));
      const b = S.renderSelo(el(), 1);
      const c = S.renderSelo(el(), 250);
      console.log(JSON.stringify([
        {t: a.textContent, h: a.hidden, d: a.style.display, ah: a.attrs['aria-hidden'] || null},
        {t: b.textContent, h: b.hidden, d: b.style.display, ah: b.attrs['aria-hidden'] || null},
        {t: c.textContent}]));
    """)
    assert res[0] == {"t": "", "h": True, "d": "none", "ah": "true"}
    assert res[1] == {"t": "1", "h": False, "d": "", "ah": None}
    assert res[2] == {"t": "99+"}


def test_js_e_python_concordam_em_placeholders():
    frases = ["Nenhuma pendência.", "Nada urgente para hoje.", "carregando…", "—", "...",
              "Sem tarefas hoje", "Nada de trailer puro", "Nenhum post pode sair sem crédito do clube",
              "Tudo em dia!", "N/A", "Revisar a legenda"]
    res = rodar_node("""
      const S = require(require('path').join(process.argv[1], 'selo_abas.js'));
      const frases = %s;
      console.log(JSON.stringify(frases.map(S.ehPlaceholder)));
    """ % json.dumps(frases, ensure_ascii=False))
    assert res == [sa.eh_placeholder(f) for f in frases]
    assert res == [True, True, True, True, True, True, False, False, True, True, False]
