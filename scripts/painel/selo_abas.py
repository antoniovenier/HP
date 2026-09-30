"""Selo (contador) das abas do painel HP — mesma regra do selo_abas.js.

Regra: o selo mostra a contagem REAL de itens da aba e some quando é 0
(ex.: a aba "Não urgentes" vazia não pode mostrar "1").

Causa provável do "1" na aba vazia (painel de hoje):
  * o selo é `<b class="num">${g[k].length}</b>` — conta tudo o que está na
    lista, inclusive item vazio, e mostra até o 0;
  * a lista `sistema.pendencias.voce` pode chegar com um item vazio ou de
    "lista vazia": em Python `"".split("\\n")` dá `[""]` (tamanho 1), e um
    `{"texto": ""}` ou "Nenhum item" também vira 1. Sem data, esse item cai
    no grupo "nao" (Não urgentes) e aparece como "1" (no selo e no numerador
    amarelo da lista, que fica sem texto ao lado).

Três formas de aplicar (dá para usar as três juntas):
  1. na origem:  limpar_pendencias(dados) antes de gravar o dados.json;
  2. no HTML gerado:  corrigir_html_painel(html) (troca o selo e pula item vazio);
  3. em HTML montado em Python:  html_selo(n) devolve "" quando n == 0.

CLI:
  python scripts\\painel\\selo_abas.py contar dados.json --caminho sistema.pendencias.voce
  python scripts\\painel\\selo_abas.py limpar dados.json
  python scripts\\painel\\selo_abas.py corrigir painel.html
  python scripts\\painel\\selo_abas.py html 3
"""
from __future__ import annotations

import argparse
import contextlib
import html as _html
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

AQUI = Path(__file__).resolve().parent
ARQUIVO_JS = AQUI / "selo_abas.js"

CHAVES_TEXTO = ("texto", "titulo", "title", "text", "nome", "rotulo", "label")
CHAVES_ABA = ("aba", "grupo")

# idênticas às do selo_abas.js (os testes conferem as duas com os mesmos casos)
RX_PLACEHOLDER = [re.compile(p) for p in (
    r"^$",
    r"^[-—–_.·…]+$",
    r"^nenhum(?:a|as|os)?(?: [a-z0-9/]+){0,3}$",
    r"^nada(?: (?:aqui|por aqui|pendente|urgente|urgente para hoje|na fila|nesta data"
    r"|nesta data para este canal|concluido ainda|a fazer|agendado|por enquanto|para hoje))?$",
    r"^sem (?:itens?|pendencias?|tarefas?|nada|dados|posts?|conteudo)(?: (?:agora|hoje|por enquanto))?$",
    r"^(?:vazio|vazia|carregando|tudo em dia|tudo certo|n/?a|nao ha itens|nao ha pendencias)$",
)]


def normalizar_texto(s: Any) -> str:
    """'  Nenhuma Pendência. ' -> 'nenhuma pendencia'."""
    t = unicodedata.normalize("NFD", "" if s is None else str(s))
    t = re.sub(r"[̀-ͯ]", "", t).lower()
    t = re.sub(r"\s+", " ", t).strip()
    return re.sub(r"[.!…:;]+$", "", t).strip()


def eh_placeholder(texto: Any) -> bool:
    t = normalizar_texto(texto)
    return any(rx.search(t) for rx in RX_PLACEHOLDER)


def eh_item_real(item: Any) -> bool:
    """True se o item conta no selo."""
    if item is None or isinstance(item, bool):
        return False
    if isinstance(item, (int, float)):
        return item == item and item not in (float("inf"), float("-inf"))
    if isinstance(item, str):
        return not eh_placeholder(item)
    if isinstance(item, (list, tuple)):
        return any(eh_item_real(x) for x in item)
    if isinstance(item, dict):
        if item.get("placeholder") or item.get("vazio") or item.get("_placeholder"):
            return False
        tipo = normalizar_texto(item.get("tipo") or item.get("type") or "")
        if tipo in ("placeholder", "vazio", "empty"):
            return False
        tem_texto = False
        for k in CHAVES_TEXTO:
            if k in item:
                tem_texto = True
                if item[k] is not None:
                    return not eh_placeholder(item[k])
        if tem_texto:
            return False
        return len(item) > 0
    return False


def _aba_do_item(item: Any):
    if isinstance(item, dict):
        for k in CHAVES_ABA:
            if k in item:
                return item[k]
    return None


def contar_selo(itens: Any, aba: str | None = None) -> int:
    """Conta os itens reais (lista, {aba: lista} ou texto com 1 item por linha)."""
    if itens is None or isinstance(itens, bool):
        return 0
    if isinstance(itens, (int, float)):
        return int(itens) if itens == itens and 0 < itens < float("inf") else 0
    if isinstance(itens, str):
        return sum(1 for linha in re.split(r"\r?\n", itens) if eh_item_real(linha))
    if isinstance(itens, (list, tuple)):
        n = 0
        for it in itens:
            if aba not in (None, ""):
                a = _aba_do_item(it)
                if isinstance(it, dict) and any(k in it for k in CHAVES_ABA) \
                        and str(a) != str(aba):
                    continue
            if eh_item_real(it):
                n += 1
        return n
    if isinstance(itens, dict):
        if aba not in (None, ""):
            return contar_selo(itens[aba], None) if aba in itens else 0
        return sum(contar_selo(v, None) for v in itens.values())
    return 0


def texto_selo(n: Any) -> str:
    """'' quando 0 (o selo some), '99+' acima de 99."""
    try:
        n = float(n)
    except (TypeError, ValueError):
        return ""
    if n != n or n <= 0 or n == float("inf"):
        return ""
    n = int(n)
    return "99+" if n > 99 else str(n)


def html_selo(n: Any, classe: str = "num", tag: str = "b") -> str:
    """HTML do selo (igual ao do painel: <b class="num">3</b>) ou '' quando 0."""
    t = texto_selo(n)
    if not t:
        return ""
    return f'<{tag} class="{_html.escape(classe, quote=True)}">{t}</{tag}>'


def html_aba(rotulo: str, itens: Any, chave: str, selecionada: bool = False,
             aba: str | None = None) -> str:
    """Botão de aba pronto, no mesmo formato do painel, com o selo já certo."""
    n = contar_selo(itens, aba)
    return (f'<button class="tab" type="button" role="tab" '
            f'aria-selected="{"true" if selecionada else "false"}" '
            f'data-k="{_html.escape(chave, quote=True)}">{_html.escape(rotulo)}'
            f'{" " + html_selo(n) if n else ""}</button>')


def limpar_itens(itens: Any) -> list:
    """Tira da lista o que não é item de verdade (vazio, 'Nenhum item', ...)."""
    if itens is None:
        return []
    if isinstance(itens, str):
        return [l for l in re.split(r"\r?\n", itens) if eh_item_real(l)]
    return [it for it in itens if eh_item_real(it)]


def limpar_pendencias(dados: dict) -> dict:
    """Limpa sistema.pendencias.voce/diretor do dados.json do painel (na origem).

    Devolve {"voce": removidos, "diretor": removidos}. Mexe no próprio dict.
    """
    removidos = {}
    pend = ((dados or {}).get("sistema") or {}).get("pendencias")
    if isinstance(pend, dict):
        for k in ("voce", "diretor"):
            if k in pend:
                antes = pend[k]
                depois = limpar_itens(antes)
                qtd_antes = len(antes) if isinstance(antes, (list, tuple)) else \
                    (len(re.split(r"\r?\n", antes)) if isinstance(antes, str) else 0)
                removidos[k] = qtd_antes - len(depois)
                pend[k] = depois
    return removidos


# --------------------------------------------------------------------------
# correção automática do HTML gerado pelo montar_painel_publico.py
# --------------------------------------------------------------------------
MARCA_INI = "<!-- selo-abas:inicio -->"
MARCA_FIM = "<!-- selo-abas:fim -->"
SELO_ANTIGO = '<b class="num">${g[k].length}</b>'
SELO_NOVO = "${SeloAbas.htmlSelo(SeloAbas.contarSelo(g, k))}"
RX_GRUPO = re.compile(r'^(?P<ind>[ \t]*)(?P<linha>const g = \(o\.todo_dia \|\| o\.urgente)', re.M)
PULAR_VAZIO = "if(!SeloAbas.ehItemReal(o.texto)) continue;"


def bloco_js() -> str:
    js = ARQUIVO_JS.read_text(encoding="utf-8")
    if "</script" in js.lower():
        raise ValueError("selo_abas.js não pode conter '</script'")
    return f'{MARCA_INI}\n<script id="selo-abas-js">\n{js}</script>\n{MARCA_FIM}'


def inserir_bloco(html: str, bloco: str, ini: str, fim: str) -> str:
    """Põe (ou troca) o bloco: antes do </head>, senão antes do 1º <script>."""
    rx = re.compile(re.escape(ini) + r".*?" + re.escape(fim), re.S)
    if rx.search(html):
        return rx.sub(lambda _m: bloco, html, count=1)
    m = re.search(r"</head\s*>", html, re.I) or re.search(r"<script\b", html, re.I)
    if m:
        return html[:m.start()] + bloco + "\n" + html[m.start():]
    return html + "\n" + bloco + "\n"


def corrigir_html_painel(html: str) -> tuple[str, dict]:
    """Aplica a correção do selo no HTML do painel. Idempotente.

    Devolve (html_novo, relatorio) — o relatório diz o que foi trocado e o que
    não foi encontrado (se o modelo do painel mudar, nada quebra: só avisa).
    """
    rel = {"script": False, "selo": "nao_encontrado", "pular_vazio": "nao_encontrado"}
    html = inserir_bloco(html, bloco_js(), MARCA_INI, MARCA_FIM)
    rel["script"] = True
    if SELO_NOVO in html:
        rel["selo"] = "ja_estava"
    elif SELO_ANTIGO in html:
        html = html.replace(SELO_ANTIGO, SELO_NOVO)
        rel["selo"] = "corrigido"
    if PULAR_VAZIO in html:
        rel["pular_vazio"] = "ja_estava"
    else:
        html, n = RX_GRUPO.subn(lambda m: f"{m['ind']}{PULAR_VAZIO}\n{m['ind']}{m['linha']}",
                                html, count=1)
        if n:
            rel["pular_vazio"] = "corrigido"
    return html, rel


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
class _Formato(argparse.RawDescriptionHelpFormatter):
    def add_usage(self, usage, actions, groups, prefix=None):
        return super().add_usage(usage, actions, groups, prefix or "uso: ")


def _sub(sub, nome: str, ajuda: str) -> argparse.ArgumentParser:
    sp = sub.add_parser(nome, help=ajuda, description=ajuda, add_help=False,
                        formatter_class=_Formato)
    sp._positionals.title = "argumentos"
    sp._optionals.title = "opções"
    sp.add_argument("-h", "--help", action="help", help="mostra esta ajuda e sai")
    return sp


def _pegar(d: Any, caminho: str | None) -> Any:
    for parte in (caminho or "").split("."):
        if not parte:
            continue
        d = d.get(parte) if isinstance(d, dict) else None
    return d


def main(argv: list[str] | None = None) -> int:
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    p = argparse.ArgumentParser(prog="selo_abas.py", add_help=False, formatter_class=_Formato,
                                description="Selo das abas do painel: conta só item de verdade e some no 0.")
    p._positionals.title = "argumentos"
    p._optionals.title = "opções"
    p.add_argument("-h", "--help", action="help", help="mostra esta ajuda e sai")
    sub = p.add_subparsers(dest="cmd", metavar="comando", title="comandos")
    s = _sub(sub, "contar", "conta itens reais de uma lista dentro de um JSON")
    s.add_argument("arquivo")
    s.add_argument("--caminho", default="sistema.pendencias.voce",
                   help="onde está a lista (padrão: sistema.pendencias.voce)")
    s.add_argument("--aba", help="chave da aba, se o caminho apontar para {aba: lista}")
    s = _sub(sub, "limpar", "tira itens vazios/placeholder das pendências do dados.json")
    s.add_argument("arquivo")
    s.add_argument("--saida", help="grava em outro arquivo (padrão: o mesmo)")
    s = _sub(sub, "corrigir", "corrige o selo no HTML gerado do painel")
    s.add_argument("html")
    s.add_argument("--saida", help="grava em outro arquivo (padrão: o mesmo)")
    s = _sub(sub, "html", "mostra o HTML do selo para um número")
    s.add_argument("n")
    a = p.parse_args(argv)
    if not a.cmd:
        p.print_help()
        return 2
    try:
        if a.cmd == "contar":
            dados = json.loads(Path(a.arquivo).read_text(encoding="utf-8-sig"))
            print(contar_selo(_pegar(dados, a.caminho), a.aba))
        elif a.cmd == "limpar":
            origem = Path(a.arquivo)
            dados = json.loads(origem.read_text(encoding="utf-8-sig"))
            rem = limpar_pendencias(dados)
            Path(a.saida or origem).write_text(json.dumps(dados, ensure_ascii=False, indent=2),
                                               encoding="utf-8")
            print(json.dumps({"removidos": rem}, ensure_ascii=False))
        elif a.cmd == "corrigir":
            origem = Path(a.html)
            novo, rel = corrigir_html_painel(origem.read_text(encoding="utf-8"))
            Path(a.saida or origem).write_text(novo, encoding="utf-8")
            print(json.dumps(rel, ensure_ascii=False))
        elif a.cmd == "html":
            print(html_selo(a.n))
    except (OSError, json.JSONDecodeError, ValueError) as e:
        print(f"erro: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
