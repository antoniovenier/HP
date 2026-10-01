"""Compila a entrega da rodada 2 num único .md no formato da Seção 2 do prompt.

Uso:  python docs/compilar_entrega_2.py [--saida ENTREGA_NUVEM_HP_STUDIO_2.md] [--base c0aba96]

Regra do desempacotar.py do PC: cada arquivo = uma linha `## caminho/relativo/arquivo.ext`
(só letras, números, _ . / -) seguida de UM bloco de código. Por isso:
- só entram arquivos NOVOS desde a rodada 1 (commit base) e os 3 documentos de controle
  (ENTREGA.md, PATCHES.md, PENDENCIAS_PARA_O_DIRETOR.md) no começo;
- arquivo da rodada 1 que mudou NÃO é reenviado inteiro (vai descrito no PATCHES.md e no diff
  unificado `patches/rodada2_rodada1_alterados.diff`), a não ser que mais da metade dele
  tenha mudado — aí entra inteiro e o PATCHES.md diz isso;
- o compilador RECUSA (sai com 1) se algum arquivo tiver linha começando com `## nome.ext`,
  nome com espaço/acento, ou nome de segredo (contas.json, tokens*, segredos*, *.env);
- cerca externa de 5 crases quando o conteúdo tem cercas de 3 (ou mais, se precisar).
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BASE_PADRAO = "c0aba96"          # último commit da rodada 1
CONTROLE = ["ENTREGA.md", "PATCHES.md", "PENDENCIAS_PARA_O_DIRETOR.md"]
IGNORAR = {"ENTREGA_NUVEM_HP_STUDIO.md", "ENTREGA_NUVEM_HP_STUDIO_2.md", "docs/PROMPT_NUVEM_2.md",
           "docs/PROMPT_NUVEM.md", "docs/ENTREGA_rodada1.md", ".gitignore"}
LING = {".py": "python", ".js": "javascript", ".css": "css", ".html": "html", ".json": "json",
        ".ps1": "powershell", ".md": "markdown", ".xml": "xml", ".txt": "text", ".log": "text",
        ".diff": "diff", ".cfg": "ini", ".toml": "toml", ".jsonl": "json", ".csv": "text"}
BINARIO = {".png", ".jpg", ".jpeg", ".mp4", ".wav", ".sqlite", ".pyc", ".ttf", ".zip", ".gif", ".webp"}
RX_NOME_OK = re.compile(r"^[A-Za-z0-9_./-]+$")
RX_HEADER_FALSO = re.compile(r"^## [A-Za-z0-9_./-]+\.[A-Za-z0-9]{1,6}\s*$")
RX_SEGREDO = re.compile(r"^(contas\.json|tokens.*|segredos.*|.*\.env)$", re.I)

# ordem das seções (prefixo do caminho -> título); o que não casar vai em "Outros"
SECOES = [
    ("tests/", "Fixtures reais do PC e teste de contrato (A8)"),
    ("app/hp_studio_nuvem/hpbase/", "A. hpbase: fila_api_pc, marca, trava e caminhos"),
    ("app/hp_studio_nuvem/esteira/", "A. esteira: comandos_pc, pedido_pc"),
    ("app/hp_studio_nuvem/metricas/", "A. metricas: chaves_pc"),
    ("app/hp_studio_nuvem/whatsapp_local/", "A. whatsapp_local: fila_pc"),
    ("app/hp_studio_nuvem/publicar_extra/", "B e C. publicar_extra: YouTube e Facebook"),
    ("scripts/story_artes", "D. story_artes"),
    ("scripts/LEIA_story_artes", "D. story_artes"),
    ("scripts/testes/test_story_artes", "D. story_artes"),
    ("scripts/story_", "E. story no celular (dispositivo, fluxos, fila v2, coleta de telas, lote)"),
    ("scripts/LEIA_story_", "E. story no celular"),
    ("scripts/testes/test_story_", "E. story no celular"),
    ("scripts/ui_dump", "E. story no celular"),
    ("scripts/", "Scripts: outros"),
    ("radar_fontes/", "F. radar_fontes: fontes verificadas e verificador"),
    ("patches/", "Patches (diff unificado dos arquivos da rodada 1 que mudaram)"),
    ("docs/", "Docs e ferramentas da entrega"),
]


def git(*a: str) -> str:
    return subprocess.run(["git", *a], cwd=RAIZ, capture_output=True, text=True,
                          encoding="utf-8", check=True).stdout


RENOME = ("app/hp_studio/", "app/hp_studio_nuvem/")   # a rodada 2 renomeou o pacote


def _novo_de(antigo: str) -> str:
    return antigo.replace(RENOME[0], RENOME[1], 1) if antigo.startswith(RENOME[0]) else antigo


def arquivos_desde(base: str) -> tuple[list[str], list[str], dict]:
    """(novos, alterados, numstat) relativos à raiz, já sem binários/ignorados.

    `git diff -M50%` pareia o caminho antigo (app/hp_studio/X) com o novo (app/hp_studio_nuvem/X)
    enquanto ≥ 50 % do arquivo for igual; abaixo disso o git mostra D + A, e aqui o par é remontado
    pelo caminho: virou "reescrito" (mais da metade mudou → vem inteiro, copiar por cima no PC).
    """
    novos, alterados, removidos, reescritos = [], [], [], []
    antigo_de: dict[str, str] = {}
    apagados, adicionados = [], []
    for linha in git("diff", "--name-status", "-M50%", base).splitlines():
        partes = linha.split("\t")
        st = partes[0]
        if st.startswith("R"):
            antigo, novo = partes[1], partes[2]
            if Path(antigo).name != Path(novo).name:
                novos.append(novo)             # mudou de nome (ex.: contas.json -> contas_exemplo.json): vai inteiro
                removidos.append(antigo)
            elif st == "R100":
                continue                       # só renomeado (hp_studio -> hp_studio_nuvem)
            else:
                alterados.append(novo)
                antigo_de[novo] = antigo
        elif st == "A":
            adicionados.append(partes[1])
        elif st == "M":
            alterados.append(partes[1])
            antigo_de[partes[1]] = partes[1]
        elif st == "D":
            apagados.append(partes[1])
    for antigo in apagados:
        novo = _novo_de(antigo)
        if novo in adicionados:                # D + A do mesmo arquivo: reescrito (< 50 % igual)
            reescritos.append(novo)
            antigo_de[novo] = antigo
            adicionados.remove(novo)
        else:
            removidos.append(antigo)
    novos.extend(adicionados)
    for linha in git("ls-files", "--others", "--exclude-standard").splitlines():
        if linha and linha not in novos:
            novos.append(linha)
    numstat = {}
    for linha in git("diff", "--numstat", "-M50%", base).splitlines():
        a, r, nome = linha.split("\t")
        if " => " in nome:                       # "app/{hp_studio => hp_studio_nuvem}/x.py"
            m = re.match(r"^(.*)\{(.*) => (.*)\}(.*)$", nome)
            nome = f"{m.group(1)}{m.group(3)}{m.group(4)}" if m else nome.split(" => ")[-1]
        numstat[nome] = (int(a) if a != "-" else 0, int(r) if r != "-" else 0)
    arquivos_desde.removidos = [_novo_de(r) for r in removidos if r not in CONTROLE and r not in IGNORAR]
    arquivos_desde.reescritos = reescritos
    arquivos_desde.antigo_de = antigo_de

    def ok(p: str) -> bool:
        return (p not in IGNORAR and Path(p).suffix.lower() not in BINARIO
                and "__pycache__" not in p and not p.startswith("docs/rodada2/"))
    return sorted(filter(ok, novos)), sorted(filter(ok, alterados)), numstat


def mudou_mais_da_metade(rel: str, numstat: dict) -> bool:
    p = RAIZ / rel
    if not p.exists():
        return False
    total = max(1, len(p.read_text(encoding="utf-8", errors="replace").splitlines()))
    add, rem = numstat.get(rel, (0, 0))
    return max(add, rem) > total / 2


def cerca(texto: str) -> str:
    n = 3
    while "`" * n in texto:
        n += 1
    return "`" * max(n, 5 if "```" in texto else 3)


def checar(rel: str, texto: str) -> list[str]:
    erros = []
    if not RX_NOME_OK.match(rel):
        erros.append(f"{rel}: nome com caractere fora de [A-Za-z0-9_./-]")
    if RX_SEGREDO.match(Path(rel).name):
        erros.append(f"{rel}: nome de segredo (o classificador do PC bloqueia)")
    for i, linha in enumerate(texto.splitlines(), 1):
        if RX_HEADER_FALSO.match(linha):
            erros.append(f"{rel}:{i}: linha começa com '## nome.ext' (quebra o desempacotar): {linha[:60]}")
    return erros


def secao_de(rel: str) -> str:
    for prefixo, titulo in SECOES:
        if rel.startswith(prefixo):
            return titulo
    return "Outros"


def bloco(rel: str, texto: str) -> str:
    c = cerca(texto)
    lang = LING.get(Path(rel).suffix.lower(), "")
    if not texto.endswith("\n"):
        texto += "\n"
    return f"\n## {rel}\n\n{c}{lang}\n{texto}{c}\n"


def gerar_diff(base: str, alterados: list[str]) -> str:
    if not alterados:
        return ""
    antigo_de = getattr(arquivos_desde, "antigo_de", {})
    caminhos = sorted({c for a in alterados for c in (a, antigo_de.get(a, a))})
    return git("diff", "-M50%", base, "--", *caminhos)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--saida", default="ENTREGA_NUVEM_HP_STUDIO_2.md")
    ap.add_argument("--base", default=BASE_PADRAO)
    ap.add_argument("--so-checar", action="store_true", help="só valida; não grava")
    args = ap.parse_args(argv)

    novos, alterados, numstat = arquivos_desde(args.base)
    inteiros = sorted({a for a in alterados if mudou_mais_da_metade(a, numstat)}
                      | set(getattr(arquivos_desde, "reescritos", [])))
    so_diff = [a for a in alterados if a not in inteiros]

    erros: list[str] = []
    for c in CONTROLE:
        if not (RAIZ / c).exists():
            erros.append(f"falta o documento de controle {c}")
    partes = []
    cabecalho = (f"# HP Studio — entrega da nuvem, rodada 2 (01/10/2026)\n\n"
                 f"Um único .md para o `desempacotar.py` do PC: cada `## caminho/arquivo.ext` abre um arquivo. "
                 f"Primeiro os 3 documentos de controle, depois só o que é NOVO desde a rodada 1 "
                 f"(commit `{args.base}`). Arquivos da rodada 1 que mudaram estão descritos em `PATCHES.md` "
                 f"e no diff `patches/rodada2_rodada1_alterados.diff`"
                 + (f"; estes mudaram MAIS DA METADE e vêm inteiros (copiar por cima no PC): "
                    f"{', '.join(f'`{i}`' for i in inteiros)}" if inteiros else "")
                 + ".\n")
    partes.append(cabecalho)
    indice = []
    conteudo = []
    for c in CONTROLE:
        p = RAIZ / c
        if p.exists():
            txt = p.read_text(encoding="utf-8")
            erros += checar(c, txt)
            conteudo.append(bloco(c, txt))
            indice.append(c)
    # diff dos alterados (gerado na hora, vai como arquivo de texto)
    diff = gerar_diff(args.base, so_diff + inteiros)
    pasta_patches = RAIZ / "patches"
    if diff and not args.so_checar:
        pasta_patches.mkdir(exist_ok=True)
        (pasta_patches / "rodada2_rodada1_alterados.diff").write_text(diff, encoding="utf-8")
        if "patches/rodada2_rodada1_alterados.diff" not in novos:
            novos.append("patches/rodada2_rodada1_alterados.diff")
    por_secao: dict[str, list[str]] = {}
    for rel in sorted(set(novos) | set(inteiros)):
        if rel in CONTROLE:
            continue
        por_secao.setdefault(secao_de(rel), []).append(rel)
    ordem = [t for _, t in SECOES if t in por_secao] + [t for t in por_secao if t not in {t2 for _, t2 in SECOES}]
    vistos = set()
    for titulo in ordem:
        if titulo in vistos:
            continue
        vistos.add(titulo)
        conteudo.append(f"\n---\n\n# {titulo}\n")
        for rel in por_secao[titulo]:
            p = RAIZ / rel
            try:
                txt = p.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                erros.append(f"{rel}: não é UTF-8 (binário?)")
                continue
            erros += checar(rel, txt)
            conteudo.append(bloco(rel, txt))
            indice.append(rel)
    if erros:
        print("ERROS (nada gravado):", file=sys.stderr)
        for e in erros:
            print("  " + e, file=sys.stderr)
        return 1
    partes.append("\n## Índice\n\n" + "\n".join(f"- `{r}`" for r in indice) + "\n")
    partes.append(f"\nArquivos da rodada 1 alterados (ver PATCHES.md e o diff): "
                  + (", ".join(f"`{a}`" for a in so_diff) if so_diff else "nenhum") + "\n")
    rem = getattr(arquivos_desde, "removidos", [])
    if rem:
        partes.append("\nArquivos da rodada 1 que saem (apagar no PC; ver PATCHES.md): "
                      + ", ".join(f"`{a}`" for a in rem) + "\n")
    saida = RAIZ / args.saida
    texto = "".join(partes) + "".join(conteudo)
    if args.so_checar:
        print(f"ok: {len(indice)} arquivos, {len(texto) / 1024:.0f} KB (não gravado)")
        return 0
    saida.write_text(texto, encoding="utf-8")
    print(f"{saida.name}: {len(indice)} arquivos, {saida.stat().st_size / 1024:.0f} KB; "
          f"alterados só no diff: {len(so_diff)}; inteiros: {len(inteiros)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
