"""Desempacota um .md no formato da Seção 2 (## caminho + bloco) e PROVA que não há
arquivo "sem bloco", arquivo falso nem perda de conteúdo.

Uso:  python docs/desempacotar_check.py ENTREGA_NUVEM_HP_STUDIO_2.md [--destino <pasta>] [--comparar-com <raiz>]

- Corta pelos cabeçalhos `## caminho/arquivo.ext` que estão FORA de cercas de código.
- O 1º bloco depois do cabeçalho abre e o seu fecho (mesmo número de crases) fecha o arquivo.
- Falha (código 1) se: cabeçalho sem bloco; linha `## nome.ext` DENTRO de um bloco (o
  desempacotar ingênuo do PC criaria um arquivo falso); nome com espaço/acento; nome de
  segredo; ou, com --comparar-com, se algum arquivo extraído difere do original.
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

RX_HEADER = re.compile(r"^## ([A-Za-z0-9_./-]+\.[A-Za-z0-9]{1,6})\s*$")
RX_HEADER_QUALQUER = re.compile(r"^## (\S+)\s*$")
RX_FENCE = re.compile(r"^(`{3,})(\S*)\s*$")
RX_SEGREDO = re.compile(r"^(contas\.json|tokens.*|segredos.*|.*\.env)$", re.I)


def desempacotar(texto: str) -> tuple[dict, list[str]]:
    """-> ({caminho: conteudo}, problemas)."""
    arquivos: dict[str, str] = {}
    problemas: list[str] = []
    linhas = texto.split("\n")
    i, n = 0, len(linhas)
    while i < n:
        m = RX_HEADER.match(linhas[i])
        if not m:
            mq = RX_HEADER_QUALQUER.match(linhas[i])
            if mq and "." in mq.group(1) and " " not in mq.group(1):
                problemas.append(f"linha {i + 1}: cabeçalho com nome inválido: {linhas[i][:60]}")
            i += 1
            continue
        nome = m.group(1)
        if RX_SEGREDO.match(Path(nome).name):
            problemas.append(f"linha {i + 1}: nome de segredo: {nome}")
        # acha a cerca de abertura (só linhas em branco entre o cabeçalho e ela)
        j = i + 1
        while j < n and linhas[j].strip() == "":
            j += 1
        mf = RX_FENCE.match(linhas[j]) if j < n else None
        if not mf:
            problemas.append(f"linha {i + 1}: '{nome}' sem bloco de código logo depois")
            i += 1
            continue
        cerca = mf.group(1)
        k = j + 1
        corpo = []
        while k < n and linhas[k] != cerca:
            if RX_HEADER.match(linhas[k]):
                problemas.append(f"linha {k + 1}: dentro de '{nome}' há uma linha '## x.ext' "
                                 f"(arquivo falso no PC): {linhas[k][:60]}")
            corpo.append(linhas[k])
            k += 1
        if k >= n:
            problemas.append(f"linha {j + 1}: bloco de '{nome}' nunca fecha")
            break
        if nome in arquivos:
            problemas.append(f"linha {i + 1}: '{nome}' aparece duas vezes")
        arquivos[nome] = "\n".join(corpo) + "\n"
        i = k + 1
    return arquivos, problemas


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("md")
    ap.add_argument("--destino", help="pasta onde gravar (padrão: temporária)")
    ap.add_argument("--comparar-com", help="raiz do repositório para conferir byte a byte")
    args = ap.parse_args(argv)
    texto = Path(args.md).read_text(encoding="utf-8")
    arquivos, problemas = desempacotar(texto)
    destino = Path(args.destino) if args.destino else Path(tempfile.mkdtemp(prefix="hp_desempacotar_"))
    for nome, corpo in arquivos.items():
        p = destino / nome
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(corpo, encoding="utf-8")
    diferentes = []
    if args.comparar_com:
        raiz = Path(args.comparar_com)
        for nome, corpo in arquivos.items():
            orig = raiz / nome
            if not orig.exists():
                diferentes.append(f"{nome}: não existe no repositório")
                continue
            o = orig.read_text(encoding="utf-8")
            if not o.endswith("\n"):
                o += "\n"
            if o != corpo:
                diferentes.append(f"{nome}: conteúdo difere do original")
    print(f"{len(arquivos)} arquivos extraídos para {destino}")
    for p in problemas:
        print("PROBLEMA:", p)
    for d in diferentes:
        print("DIFERENTE:", d)
    if problemas or diferentes:
        return 1
    print("ok: nenhum arquivo sem bloco, nenhum arquivo falso, nenhum nome inválido"
          + (", todos idênticos ao repositório" if args.comparar_com else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
