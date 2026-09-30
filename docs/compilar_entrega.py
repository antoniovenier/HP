"""Compila toda a entrega num único .md (índice + código completo + testes + passo a passo).

Uso:  python docs/compilar_entrega.py  →  ENTREGA_NUVEM_HP_STUDIO.md na raiz do repositório.
"""
from __future__ import annotations

from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "ENTREGA_NUVEM_HP_STUDIO.md"

# (título, lista de globs relativos à raiz) na ordem do prompt
SECOES = [
    ("0. Base comum `hpbase` e convenções", ["docs/CONVENCOES.md", "app/conftest.py",
                                             "app/hp_studio/hpbase/**/*"]),
    ("A. Manuais 04–13 + índice", ["app/manuais/README.md", "app/manuais/0*.md",
                                   "app/manuais/1*.md"]),
    ("B. Etapa 3 — esteira P0/P1/P2", ["app/hp_studio/esteira/**/*"]),
    ("C. Etapa 6 — métricas por API", ["app/hp_studio/metricas/**/*"]),
    ("D. Teste de qualidade / paridade", ["app/hp_studio/qa_paridade/**/*"]),
    ("E. Enviador local de WhatsApp", ["app/hp_studio/whatsapp_local/**/*"]),
    ("F. story_post.py — story pelo emulador", ["scripts/LEIA_story_post.md",
                                               "scripts/story_post*.py",
                                               "scripts/testes/test_story_post.py"]),
    ("G. reel_futebol.py — reels do Futebol", ["scripts/LEIA_reel_futebol.md",
                                              "scripts/reel_futebol*.py",
                                              "scripts/testes/test_reel_futebol.py"]),
    ("H. Publicador — reenvio seguro", ["scripts/LEIA_reenvio_seguro.md",
                                       "scripts/reenvio_seguro.py",
                                       "scripts/testes/test_reenvio_seguro.py"]),
    ("I. Painel público", ["scripts/painel/**/*", "scripts/testes/test_painel_*.py"]),
    ("J. Página de links", ["scripts/pagina_links/**/*",
                            "scripts/testes/test_pagina_links.py"]),
]

LING = {".py": "python", ".js": "javascript", ".css": "css", ".html": "html",
        ".json": "json", ".ps1": "powershell", ".md": "markdown", ".xml": "xml",
        ".srt": "text", ".txt": "text", ".jsonl": "json"}
BINARIO = {".png", ".jpg", ".jpeg", ".mp4", ".wav", ".sqlite", ".pyc", ".ttf"}


def arquivos(globs):
    vistos = []
    for g in globs:
        for p in sorted(RAIZ.glob(g)):
            if (p.is_file() and p not in vistos and "__pycache__" not in p.parts
                    and ".pytest_cache" not in p.parts and p.suffix not in BINARIO):
                vistos.append(p)
    return vistos


def cerca(texto: str) -> str:
    n = 3
    while "`" * n in texto:
        n += 1
    return "`" * max(n, 4)


def main() -> None:
    partes = [
        "# HP Studio — entrega da sessão da nuvem (30/09/2026)\n",
        "Compilado único para a sessão **HP GESTÃO** integrar no PC e rodar o modo sombra.\n",
        "Leia primeiro `ENTREGA.md` (passo a passo de instalação e integração) — está logo abaixo.\n",
    ]
    entrega = RAIZ / "ENTREGA.md"
    if entrega.exists():
        partes.append("\n---\n\n" + entrega.read_text(encoding="utf-8") + "\n")
    partes.append("\n---\n\n## Índice dos arquivos\n")
    corpo = []
    for titulo, globs in SECOES:
        lst = arquivos(globs)
        partes.append(f"\n### {titulo}\n")
        for p in lst:
            rel = p.relative_to(RAIZ).as_posix()
            ancora = rel.replace("/", "-").replace(".", "-").replace("_", "-").lower()
            partes.append(f"- [`{rel}`](#{ancora}) — {p.stat().st_size / 1024:.1f} KB\n")
        corpo.append(f"\n---\n\n# {titulo}\n")
        for p in lst:
            rel = p.relative_to(RAIZ).as_posix()
            txt = p.read_text(encoding="utf-8")
            if p.suffix == ".md":
                corpo.append(f"\n## {rel}\n\n{cerca(txt)}markdown\n{txt}\n{cerca(txt)}\n")
            else:
                c = cerca(txt)
                corpo.append(f"\n## {rel}\n\n{c}{LING.get(p.suffix, '')}\n{txt}\n{c}\n")
    SAIDA.write_text("".join(partes) + "".join(corpo), encoding="utf-8")
    print(f"{SAIDA.name}: {SAIDA.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
