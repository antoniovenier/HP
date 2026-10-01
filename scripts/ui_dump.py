"""ui_dump — lê a saída do ui.py do celular (H:\\HypadoLocal\\android\\ui.py, §4.7) sem adb.

O que faz: o ui.py imprime uma linha por elemento da tela do emulador no formato
    centro_x,centro_y | classe | texto | desc | id | clicavel
(texto e desc cortados em 60 caracteres; "clic" na última coluna quando o elemento é clicável;
linhas sem texto, desc e id são omitidas pelo próprio ui.py). Este módulo transforma esse texto
na mesma lista de nós que o ui.ler() devolve — {x, y, classe, texto, desc, id, clicavel} — para
quem precisa decidir onde tocar a partir de um dump salvo (testes, story_post, relatórios),
sem abrir adb nem emulador.

Uso:
    from ui_dump import ler_linhas_ui, achar, ler_arquivo
    nos = ler_linhas_ui(texto)                       # texto = saída do ui.py
    no = achar(nos, id="toolbar_highlights_button")  # {"x": 530, "y": 2190, "desc": "Highlight", ...}
    achar(nos, texto="3m") / achar(nos, desc="minutes ago", contem=True)
    python scripts\\ui_dump.py <arquivo.txt> [filtro]   # imprime os nós (JSON)

Regras:
- Não roda nada, não lê rede, não toca em adb: só texto.
- Coordenadas são o centro do elemento, como o ui.py imprime; a tela do emulador é 1080x2400
  (nunca use coordenada fixa: sempre a do dump).
- Busca ignora maiúscula e acento; `contem=True` aceita trecho.
- Linha fora do formato é ignorada (não derruba quem chama); um texto com " | " dentro é
  reconstruído e marcado com "ambiguo": True.
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

SEPARADOR = " | "
COLUNAS = ("x", "y", "classe", "texto", "desc", "id", "clicavel")
MARCA_CLICAVEL = "clic"
_RX_COORD = re.compile(r"^\s*(-?\d+),(-?\d+)\s*$")


def _normalizar(s) -> str:
    t = unicodedata.normalize("NFD", str(s or ""))
    return "".join(ch for ch in t if unicodedata.category(ch) != "Mn").casefold().strip()


def ler_linha_ui(linha: str) -> dict | None:
    """Uma linha do ui.py -> nó {x, y, classe, texto, desc, id, clicavel} (None se não é uma linha dele)."""
    l = str(linha or "").rstrip("\r\n")
    if not l.strip():
        return None
    if l.endswith(" |"):            # editor tirou o espaço final da coluna 'clicavel' vazia
        l += " "
    partes = l.split(SEPARADOR)
    if len(partes) < 6:
        return None
    m = _RX_COORD.match(partes[0])
    if not m:
        return None
    ambiguo = len(partes) > 6
    if ambiguo:                      # " | " dentro do texto/desc: recompõe o meio
        meio = partes[2:-2]
        texto, desc = SEPARADOR.join(meio[:-1]), meio[-1]
    else:
        texto, desc = partes[2], partes[3]
    no = {
        "x": int(m.group(1)), "y": int(m.group(2)),
        "classe": partes[1].strip(),
        "texto": texto.strip(), "desc": desc.strip(),
        "id": partes[-2].strip(),
        "clicavel": partes[-1].strip() == MARCA_CLICAVEL,
    }
    if ambiguo:
        no["ambiguo"] = True
    return no


def ler_linhas_ui(texto: str) -> list[dict]:
    """A saída inteira do ui.py -> lista de nós, na ordem da tela."""
    saida = []
    for linha in str(texto or "").splitlines():
        no = ler_linha_ui(linha)
        if no is not None:
            saida.append(no)
    return saida


def ler_arquivo(caminho) -> list[dict]:
    return ler_linhas_ui(Path(caminho).read_text(encoding="utf-8-sig"))


def achar(nos: list[dict], id: str | None = None, texto: str | None = None, desc: str | None = None,
          contem: bool = False, clicavel: bool | None = None) -> dict | None:
    """Primeiro nó que casa com TODOS os critérios dados (id exato; texto/desc ignorando maiúscula e
    acento; contem=True aceita trecho). None se não achar."""
    for no in achar_todos(nos, id=id, texto=texto, desc=desc, contem=contem, clicavel=clicavel):
        return no
    return None


def achar_todos(nos: list[dict], id: str | None = None, texto: str | None = None, desc: str | None = None,
                contem: bool = False, clicavel: bool | None = None) -> list[dict]:
    def bate(valor, alvo) -> bool:
        if alvo is None:
            return True
        v, a = _normalizar(valor), _normalizar(alvo)
        return (a in v) if contem else (v == a)
    saida = []
    for no in nos:
        if id is not None and no.get("id") != id:
            continue
        if not bate(no.get("texto"), texto) or not bate(no.get("desc"), desc):
            continue
        if clicavel is not None and bool(no.get("clicavel")) != clicavel:
            continue
        saida.append(no)
    return saida


def centro(no: dict) -> tuple[int, int]:
    """(x, y) para o `adb shell input tap` — sempre o centro que veio do dump."""
    return int(no["x"]), int(no["y"])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python scripts\\ui_dump.py",
                                 description="Lê a saída salva do ui.py e lista os nós (JSON).")
    ap.add_argument("arquivo", help="arquivo .txt com a saída do ui.py")
    ap.add_argument("filtro", nargs="?", default="", help="só nós cujo id/texto/desc contém isto")
    args = ap.parse_args(argv)
    nos = ler_arquivo(args.arquivo)
    if args.filtro:
        f = _normalizar(args.filtro)
        nos = [n for n in nos if f in _normalizar(f"{n['id']} {n['texto']} {n['desc']}")]
    print(json.dumps(nos, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
