"""Integração da prévia no celular com o HTML do painel (e a página de demonstração).

O montar_painel_publico.py (no PC) gera o HTML do painel. Para ligar a prévia:

    from previa_celular import ligar_no_painel
    html, rel = ligar_no_painel(html)      # embute CSS+JS e troca o clique da capa

- embute previa_celular.css + previa_celular.js num bloco marcado (idempotente:
  rodar de novo troca o bloco, não duplica);
- troca o clique da miniatura (que hoje só amplia a capa) para abrir a prévia
  no celular; o botão "Ampliar capa" dentro da prévia continua abrindo o zoom;
- se o modelo do painel mudar e o trecho não for achado, nada quebra: o
  relatório avisa e o painel segue como estava.

CLI:
  python scripts\\painel\\previa_celular.py demo                   (regrava previa_demo.html)
  python scripts\\painel\\previa_celular.py embutir painel.html --painel
  python scripts\\painel\\previa_celular.py bloco > bloco.html
"""
from __future__ import annotations

import argparse
import contextlib
import html as _html
import json
import re
import sys
from pathlib import Path
from typing import Any

AQUI = Path(__file__).resolve().parent
ARQ_CSS = AQUI / "previa_celular.css"
ARQ_JS = AQUI / "previa_celular.js"
ARQ_DEMO = AQUI / "previa_demo.html"

MARCA_INI = "<!-- previa-celular:inicio -->"
MARCA_FIM = "<!-- previa-celular:fim -->"

# trecho do painel de hoje (renderAgenda) que abre o zoom da capa
CLIQUE_ANTIGO = "const abrir = () => ampliar(E.dados.agenda[dia].itens[+t.dataset.zoom]);"
CLIQUE_NOVO = "const abrir = () => abrirPrevia(E.dados.agenda[dia].itens[+t.dataset.zoom], t);"
TITULO_ANTIGO = 'title="Ampliar a capa"'
TITULO_NOVO = 'title="Ver prévia no celular"'

# ponte: usa as constantes do painel (BY, E, ampliar) só na hora do clique
PONTE = """function abrirPrevia(x, origem){
  if(!x) return;
  if(!window.PreviaCelular){ ampliar(x); return; }
  PreviaCelular.abrir(PreviaCelular.deItemAgenda(x, BY, {avatares: E.dados && E.dados.avatares}), {
    origem: origem, tema: "escuro",
    acaoExtra: {rotulo: "Ampliar capa", executar: function(){ ampliar(x); }}
  });
}"""


def _sem_fechar_script(txt: str, nome: str) -> str:
    if "</script" in txt.lower() or "</style" in txt.lower():
        raise ValueError(f"{nome} não pode conter </script ou </style")
    return txt


def bloco_previa(com_ponte: bool = False) -> str:
    """<style> + <script> da prévia, entre marcadores (para embutir no HTML)."""
    css = _sem_fechar_script(ARQ_CSS.read_text(encoding="utf-8"), ARQ_CSS.name)
    js = _sem_fechar_script(ARQ_JS.read_text(encoding="utf-8"), ARQ_JS.name)
    partes = [MARCA_INI, f'<style id="previa-celular-css">\n{css}</style>',
              f'<script id="previa-celular-js">\n{js}</script>']
    if com_ponte:
        partes.append(f'<script id="previa-celular-ponte">\n{PONTE}\n</script>')
    partes.append(MARCA_FIM)
    return "\n".join(partes)


def inserir_bloco(html: str, bloco: str, ini: str = MARCA_INI, fim: str = MARCA_FIM) -> str:
    """Põe (ou troca) o bloco: antes do </head>, senão antes do 1º <script>, senão no fim."""
    rx = re.compile(re.escape(ini) + r".*?" + re.escape(fim), re.S)
    if rx.search(html):
        return rx.sub(lambda _m: bloco, html, count=1)
    m = re.search(r"</head\s*>", html, re.I) or re.search(r"<script\b", html, re.I)
    if m:
        return html[:m.start()] + bloco + "\n" + html[m.start():]
    return html + "\n" + bloco + "\n"


def embutir_previa(html: str, com_ponte: bool = False) -> str:
    return inserir_bloco(html, bloco_previa(com_ponte))


def ligar_no_painel(html: str) -> tuple[str, dict]:
    """Embute a prévia e troca o clique da capa do painel. Idempotente."""
    rel = {"bloco": True, "clique": "nao_encontrado", "titulo": "nao_encontrado"}
    html = embutir_previa(html, com_ponte=True)
    if CLIQUE_NOVO in html:
        rel["clique"] = "ja_estava"
    elif CLIQUE_ANTIGO in html:
        html = html.replace(CLIQUE_ANTIGO, CLIQUE_NOVO)
        rel["clique"] = "ligado"
    if TITULO_NOVO in html:
        rel["titulo"] = "ja_estava"
    elif TITULO_ANTIGO in html:
        html = html.replace(TITULO_ANTIGO, TITULO_NOVO)
        rel["titulo"] = "trocado"
    return html, rel


def atributo_previa(post: dict, sem_capa: bool = True) -> str:
    """data-previa="{...}" para pôr na capa quando o HTML é montado em Python.

    sem_capa=True tira a capa do JSON (o JS usa a <img> da própria capa), para
    não repetir imagem em base64 no HTML.
    """
    dados = {k: v for k, v in post.items() if v not in (None, "", [])}
    if sem_capa:
        dados.pop("capa", None)
    return 'data-previa="' + _html.escape(json.dumps(dados, ensure_ascii=False), quote=True) + '"'


# --------------------------------------------------------------------------
# página de demonstração autocontida (abre direto no navegador, sem internet)
# --------------------------------------------------------------------------
DEMO_MODELO = r"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Prévia no celular</title>
<meta name="description" content="Demonstração da prévia do post em moldura de celular, por rede (gerado por previa_celular.py demo).">
<style>
:root{
  --fundo:#f6f5f1; --superficie:#ffffff; --texto:#17161a; --suave:#5d5a66; --linha:#e4e2ea; --realce:#c2185b;
  color-scheme:light;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --fundo:#0d0a14; --superficie:#161120; --texto:#f5f1fb; --suave:#b3a9c6; --linha:#2b2339; --realce:#ff4d94;
    color-scheme:dark;
  }
}
:root[data-theme="dark"]{
  --fundo:#0d0a14; --superficie:#161120; --texto:#f5f1fb; --suave:#b3a9c6; --linha:#2b2339; --realce:#ff4d94;
  color-scheme:dark;
}
*{box-sizing:border-box}
body{margin:0;background:var(--fundo);color:var(--texto);font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.demo{max-width:880px;margin:0 auto;padding:20px 16px 48px;display:grid;gap:18px}
.demo-topo{display:flex;flex-wrap:wrap;gap:12px;align-items:flex-end;justify-content:space-between}
.demo h1{margin:0;font-size:clamp(24px,5vw,32px);line-height:1.1}
.demo p{margin:0;color:var(--suave)}
.temas{display:flex;gap:6px}
.temas button{min-height:40px;padding:8px 14px;border-radius:99px;border:1px solid var(--linha);background:var(--superficie);color:var(--texto);font-family:inherit;font-size:14px;font-weight:600;line-height:1;cursor:pointer}
.temas button[aria-pressed="true"]{border-color:var(--realce);box-shadow:inset 0 0 0 1px var(--realce)}
.lista{display:grid;gap:0;background:var(--superficie);border:1px solid var(--linha);border-radius:18px;padding:6px 14px}
.item{display:grid;grid-template-columns:64px 1fr;gap:14px;align-items:center;padding:12px 0;border-top:1px solid var(--linha)}
.item:first-child{border-top:0}
.capa{width:64px;height:80px;border-radius:10px;overflow:hidden;background:var(--linha);cursor:pointer;display:block;padding:0;border:0}
.capa img{width:100%;height:100%;object-fit:cover;display:block}
.capa:focus-visible,.temas button:focus-visible{outline:3px solid var(--realce);outline-offset:2px}
.item b{display:block;overflow-wrap:anywhere}
.item small{color:var(--suave)}
.dica{font-size:13.5px}
</style>
{{BLOCO}}
</head>
<body>
<div class="demo">
  <div class="demo-topo">
    <div><h1>Prévia no celular</h1><p>Toque numa capa para ver como o post fica em cada rede.</p></div>
    <div class="temas" role="group" aria-label="Tema">
      <button type="button" data-tema="auto" aria-pressed="true">Automático</button>
      <button type="button" data-tema="light" aria-pressed="false">Claro</button>
      <button type="button" data-tema="dark" aria-pressed="false">Escuro</button>
    </div>
  </div>
  <div class="lista" id="lista"></div>
  <p class="dica">Teclado: Tab até a capa e Enter abre; setas trocam a rede; Esc fecha. Tudo funciona sem internet.</p>
</div>
<script>
(function(){
  /* capas de exemplo desenhadas na hora (nada vem da internet) */
  function capa(w, h, c1, c2, texto, rotulo){
    var cv = document.createElement("canvas"); cv.width = w; cv.height = h;
    var g = cv.getContext("2d"), gr = g.createLinearGradient(0, 0, w, h);
    gr.addColorStop(0, c1); gr.addColorStop(1, c2); g.fillStyle = gr; g.fillRect(0, 0, w, h);
    g.globalAlpha = .18; g.fillStyle = "#fff";
    for (var i = 0; i < 7; i++){ g.beginPath(); g.arc((i*173)%w, (i*291)%h, w*(.12+.05*(i%3)), 0, 7); g.fill(); }
    g.globalAlpha = 1; g.fillStyle = "#fff"; g.textAlign = "center"; g.textBaseline = "middle";
    var tam = Math.round(w*.095); g.font = "800 " + tam + "px system-ui, sans-serif";
    var palavras = texto.split(" "), linhas = [], l = "";
    palavras.forEach(function(p){ var t = l ? l + " " + p : p; if (g.measureText(t).width > w*.84 && l){ linhas.push(l); l = p; } else l = t; });
    linhas.push(l);
    var y0 = h/2 - (linhas.length-1)*tam*.6;
    linhas.forEach(function(t, i){ g.fillText(t, w/2, y0 + i*tam*1.2); });
    if (rotulo){ g.font = "600 " + Math.round(w*.045) + "px system-ui, sans-serif"; g.globalAlpha=.85; g.fillText(rotulo, w/2, h*.9); }
    return cv.toDataURL("image/jpeg", .86);
  }
  var POSTS = [
    {canal:"GTA 6 | HP", conta:"@hpgta6", cor:"#ff3d8b", tipo:"reels", redes:["instagram","tiktok","youtube","facebook","threads"],
     titulo:"No GTA 6 um NPC pode ROUBAR seu carro",
     legenda:"No GTA 6 um NPC pode ROUBAR o seu carro enquanto você está parado no semáforo? 😳 Olha o que apareceu no trailer 2 e o que isso muda na Vice City.\n\nComenta aí: você ia atrás ou deixava ir?\n\n#gta6 #gta #vicecity #rockstar #games",
     capa: capa(540, 960, "#ff3d8b", "#5b21b6", "NPC ROUBA SEU CARRO?", "9:16")},
    {canal:"Receitas | HP", conta:"@hp.receitas", cor:"#ff7a1a", tipo:"carrossel", redes:["instagram","facebook","threads","pinterest"],
     titulo:"Bolo de cenoura de liquidificador que não afunda",
     legenda:"Bolo de cenoura de liquidificador que NÃO afunda 🥕🍫\n\nSalva pra fazer no fim de semana! Ingredientes na 2ª foto, modo de preparo na 3ª e a cobertura de chocolate na última.\n\nValores aproximados. #receitas #bolodecenoura #receitafacil",
     laminas:[capa(540,675,"#ff7a1a","#b45309","BOLO QUE NÃO AFUNDA","1/4"), capa(540,675,"#f59e0b","#92400e","INGREDIENTES","2/4"), capa(540,675,"#ea580c","#7c2d12","MODO DE PREPARO","3/4"), capa(540,675,"#78350f","#451a03","COBERTURA","4/4")]},
    {canal:"Futebol | HP", conta:"@hp.futebol", cor:"#1ed760", tipo:"story", redes:["instagram","facebook"],
     titulo:"Placar: 2 x 1", legenda:"",
     capa: capa(540, 960, "#15803d", "#052e16", "FIM DE JOGO 2 x 1", "story 9:16")},
    {canal:"Destinos | HP", conta:"@hp.destinos", cor:"#00c2d1", tipo:"pin", redes:["pinterest"],
     titulo:"Jericoacoara em 4 dias: roteiro barato com dunas, lagoas e pôr do sol na Duna do Pôr do Sol",
     legenda:"Roteiro de 4 dias em Jeri com dicas de onde ficar. Valores aproximados.",
     capa: capa(500, 750, "#00c2d1", "#0e7490", "JERI EM 4 DIAS", "2:3")},
    {canal:"Filmes e Séries | HP", conta:"@hp.filmes", cor:"#f5b301", tipo:"texto", redes:["threads"],
     titulo:"Qual série você recomeçaria do zero?",
     legenda:"Se você pudesse apagar da memória UMA série só pra assistir de novo como se fosse a primeira vez, qual seria? 🍿\n\nA minha: Dark. E a sua?"},
    {canal:"Carros | HP", conta:"@hp.carros", cor:"#ff3b3b", tipo:"estatico",
     titulo:"Opala: a história do rei das ruas",
     legenda:"Opala: a história do rei das ruas 🏁 Por que o Chevrolet Opala virou lenda no Brasil e quanto custa um hoje (valores aproximados). Arrasta pro lado!",
     capa: capa(720, 720, "#ff3b3b", "#7f1d1d", "OPALA, O REI DAS RUAS", "1:1 (sem redes: mostra todas)")}
  ];
  var lista = document.getElementById("lista");
  POSTS.forEach(function(p, i){
    var d = document.createElement("div"); d.className = "item";
    var b = document.createElement("button"); b.type = "button"; b.className = "capa";
    b.setAttribute("aria-label", "Ver prévia no celular: " + p.titulo);
    var src = p.capa || (p.laminas && p.laminas[0]);
    if (src){ var im = document.createElement("img"); im.alt = ""; im.src = src; b.appendChild(im); }
    else { b.textContent = "Aa"; b.style.fontWeight = "800"; }
    b.addEventListener("click", function(){ PreviaCelular.abrir(POSTS[i], {origem: b}); });
    var t = document.createElement("div");
    t.innerHTML = "<b></b><small></small>";
    t.firstChild.textContent = p.titulo;
    t.lastChild.textContent = p.canal + " · " + (p.tipo || "") + " · " + ((p.redes && p.redes.join(", ")) || "todas as redes");
    d.appendChild(b); d.appendChild(t); lista.appendChild(d);
  });
  /* tema da página (a prévia segue sozinha) */
  var bts = document.querySelectorAll(".temas button");
  Array.prototype.forEach.call(bts, function(bt){
    bt.addEventListener("click", function(){
      var t = bt.getAttribute("data-tema");
      if (t === "auto") document.documentElement.removeAttribute("data-theme");
      else document.documentElement.setAttribute("data-theme", t);
      Array.prototype.forEach.call(bts, function(x){ x.setAttribute("aria-pressed", String(x === bt)); });
    });
  });
})();
</script>
</body>
</html>
"""


def montar_demo_html() -> str:
    return DEMO_MODELO.replace("{{BLOCO}}", bloco_previa())


def montar_demo(destino: str | Path | None = None) -> Path:
    destino = Path(destino) if destino else ARQ_DEMO
    destino.write_text(montar_demo_html(), encoding="utf-8", newline="\n")
    return destino


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
class _Formato(argparse.RawDescriptionHelpFormatter):
    def add_usage(self, usage, actions, groups, prefix=None):
        return super().add_usage(usage, actions, groups, prefix or "uso: ")


def _sub(sub, nome: str, ajuda: str) -> argparse.ArgumentParser:
    sp = sub.add_parser(nome, help=ajuda, description=ajuda, add_help=False, formatter_class=_Formato)
    sp._positionals.title = "argumentos"
    sp._optionals.title = "opções"
    sp.add_argument("-h", "--help", action="help", help="mostra esta ajuda e sai")
    return sp


def main(argv: list[str] | None = None) -> int:
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    p = argparse.ArgumentParser(prog="previa_celular.py", add_help=False, formatter_class=_Formato,
                                description="Prévia do post em moldura de celular: demo e integração com o painel.")
    p._positionals.title = "argumentos"
    p._optionals.title = "opções"
    p.add_argument("-h", "--help", action="help", help="mostra esta ajuda e sai")
    sub = p.add_subparsers(dest="cmd", metavar="comando", title="comandos")
    s = _sub(sub, "demo", "regrava previa_demo.html (autocontido)")
    s.add_argument("--saida", help="outro arquivo de saída")
    s = _sub(sub, "embutir", "embute a prévia num HTML")
    s.add_argument("html")
    s.add_argument("--painel", action="store_true",
                   help="também troca o clique da capa do painel para abrir a prévia")
    s.add_argument("--saida", help="grava em outro arquivo (padrão: o mesmo)")
    _sub(sub, "bloco", "mostra o bloco <style>+<script> para colar à mão")
    a = p.parse_args(argv)
    if not a.cmd:
        p.print_help()
        return 2
    try:
        if a.cmd == "demo":
            print(montar_demo(a.saida))
        elif a.cmd == "embutir":
            origem = Path(a.html)
            html = origem.read_text(encoding="utf-8")
            if a.painel:
                html, rel = ligar_no_painel(html)
            else:
                html, rel = embutir_previa(html), {"bloco": True}
            Path(a.saida or origem).write_text(html, encoding="utf-8")
            print(json.dumps(rel, ensure_ascii=False))
        elif a.cmd == "bloco":
            print(bloco_previa())
    except (OSError, ValueError) as e:
        print(f"erro: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
