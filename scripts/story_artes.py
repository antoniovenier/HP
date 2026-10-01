"""Artes de story profissionais por canal (1080x1920, Pillow) — scripts/story_artes.py.

O que faz: gera a imagem de story que o story_post.py põe no celular (as figurinhas
de link/enquete vão por cima, nas zonas marcadas). 3 modelos x 6 canais, na paleta
e nas fontes da marca (hpbase/marca.py, Seção 4.6):
  chamada    capa do post em cartão + rótulo + chamada (<= 45 caracteres, *destaque*)
             + seta vetorial para a zona da figurinha de link; com "enquete" nas
             figurinhas o cartão encolhe e sobra a zona da enquete.
  maissobre  2 a 4 fatos (<= 70 caracteres) com marcador, dado forte opcional,
             miniatura do post e CTA ("Salva o post" / "Leia a legenda").
  interacao  pergunta grande (<= 60 caracteres) + zona livre da enquete; opcional
             "você prefere" com duas fotos lado a lado.

Uso (PowerShell, na pasta G:\\Meu Drive\\Hypado):
  python scripts\\story_artes.py render spec.json [--png]
  python scripts\\story_artes.py todas futebol <pasta> [--png]
  python scripts\\story_artes.py exemplos <pasta> [--png]      (18 artes + _prancha_story.jpg)
  python scripts\\story_artes.py spec-exemplo                   (imprime um spec para copiar)
Spec (JSON): {"canal", "tipo": "chamada|maissobre|interacao", "capa": <imagem, opcional>,
  "rotulo", "chamada", "fatos": [...], "dado_forte": {"valor", "legenda"}, "pergunta",
  "credito_foto", "figurinhas": ["link"] ou ["link","enquete"], "cor_destaque": null
  (só Futebol: cor do clube), "saida": <pasta>, "nome": <prefixo>, "foco": [x, y] opcional,
  "fotos_prefere": [a, b] opcional, "cta" opcional}.
Saída: <saida>/<nome>.jpg, <nome>_zonas.json (zonas das figurinhas em pixels e em
fração da tela) e, com --png, <nome>.png (determinístico: mesma entrada, mesmo SHA-256).
Códigos de saída: 0 ok · 1 erro (mensagem em português).

Regras: nada importante nos 250 px do topo nem nos 350 px da base; texto sempre cabe
(reduz a letra até um mínimo e, se não couber, recusa explicando); sem emoji
(marca.sem_emoji); crédito da foto quando houver credito_foto; foto de cor natural
(marca.TRATAMENTO_FOTO); capa ausente -> fundo gerado no degradê do canal.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from story_artes_base import (ALTURA, LARGURA, ErroStory, Tela, abrir_imagem, escrever_json, gravar_imagem,
                              ler_json, marca, normalizar_spec, zonas_de)
from story_artes_canais import estilo, pintar_fundo
from story_artes_modelos import montar


# ------------------------------------------------------------------ render
def _carregar_imagens(spec: dict) -> dict:
    imgs: dict = {"capa": None, "fotos_prefere": None}
    if spec["capa"]:
        imgs["capa"] = abrir_imagem(spec["capa"])
    if spec["fotos_prefere"]:
        imgs["fotos_prefere"] = [abrir_imagem(p) for p in spec["fotos_prefere"]]
    return imgs


def desenhar(spec: dict) -> tuple[Tela, dict]:
    """Só desenha (sem gravar): devolve (Tela, spec normalizado)."""
    spec = normalizar_spec(spec)
    est = estilo(spec["canal"], spec["cor_destaque"])
    tela = Tela(pintar_fundo(est))
    montar(tela, est, spec, _carregar_imagens(spec))
    return tela, spec


def render(spec: dict | str | Path, saida: str | Path | None = None, png: bool = False,
           devolver_camadas: bool = False) -> dict:
    """Gera <saida>/<nome>.jpg + <nome>_zonas.json (+ .png com png=True).

    Devolve {"jpg", "png", "zonas", "zonas_dict", "spec", "avisos"} e, com
    devolver_camadas=True, também "camadas" (lista de {"nome","bbox","texto","cores"}),
    "imagem" (PIL, a arte final) e "fundo" (PIL, a arte sem os textos — para conferir
    contraste). Erros saem como ErroStory, em português.
    """
    if isinstance(spec, (str, Path)):
        p = Path(spec)
        if not p.is_file():
            raise ErroStory(f"Não achei o spec: {p}")
        try:
            dados = ler_json(p)
        except Exception as e:  # noqa: BLE001
            raise ErroStory(f"O spec {p.name} não é um JSON válido: {e}") from e
        if not isinstance(dados, dict):
            raise ErroStory(f"O spec {p.name} precisa ser um objeto JSON.")
        spec = dados
        if saida is None and not spec.get("saida"):
            saida = p.parent
    if saida is not None:
        spec = dict(spec, saida=str(saida))
    tela, spec_n = desenhar(spec)
    if not spec_n["saida"]:
        raise ErroStory("Faltou a pasta de saída: informe \"saida\" no spec ou render(..., saida=...).")
    pasta = Path(spec_n["saida"])
    pasta.mkdir(parents=True, exist_ok=True)
    final = tela.compor()
    jpg = gravar_imagem(final, pasta / f"{spec_n['nome']}.jpg", "jpg")
    png_p = gravar_imagem(final, pasta / f"{spec_n['nome']}.png", "png") if png else None
    zonas = zonas_de(spec_n["figurinhas"])
    zonas_p = escrever_json(pasta / f"{spec_n['nome']}_zonas.json", zonas)
    out = {"jpg": jpg, "png": png_p, "zonas": zonas_p, "zonas_dict": zonas, "spec": spec_n,
           "avisos": list(spec_n["avisos"])}
    if devolver_camadas:
        out["camadas"] = [c.resumo() for c in tela.camadas]
        out["imagem"] = final
        out["fundo"] = tela.fundo_sem_texto()
    return out


def render_todas(canal: str, pasta: str | Path, png: bool = False) -> list[dict]:
    """Os 3 modelos do canal com os specs de exemplo (capas sintéticas)."""
    from story_artes_exemplos import specs_para_pasta
    canal = str(canal).strip().lower()
    if canal not in marca.CANAIS:
        raise ErroStory(f"Canal '{canal}' não existe. Use um destes: " + ", ".join(marca.ORDEM_CANAIS) + ".")
    pasta = Path(pasta)
    return [render(s, png=png) for s in specs_para_pasta(pasta, canal)]


def render_exemplos(pasta: str | Path, png: bool = False) -> dict:
    """Os 18 exemplos + _prancha_story.jpg. Devolve {"resultados": [...], "prancha": Path, "segundos": float}."""
    from story_artes_exemplos import prancha, specs_para_pasta
    t0 = time.perf_counter()
    pasta = Path(pasta)
    resultados = [render(s, png=png) for s in specs_para_pasta(pasta)]
    jpgs = {(r["spec"]["canal"], r["spec"]["tipo"]): r["jpg"] for r in resultados}
    p = prancha(jpgs, pasta / "_prancha_story.jpg")
    return {"resultados": resultados, "prancha": p, "segundos": time.perf_counter() - t0}


# --------------------------------------------------------------------- CLI
def _spec_exemplo() -> dict:
    return {"canal": "futebol", "tipo": "chamada", "capa": "C:/caminho/da/capa_do_post.jpg",
            "rotulo": "NOVO REEL", "chamada": "Flamengo fecha *reforço* de R$ 80 mi",
            "fatos": [], "pergunta": "", "credito_foto": "Flamengo oficial",
            "figurinhas": ["link"], "cor_destaque": None, "saida": "C:/caminho/de/saida",
            "nome": "futebol_reforco", "foco": [0.5, 0.3]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python scripts\\story_artes.py",
                                 description="Artes de story (1080x1920) por canal, 3 modelos.")
    sub = ap.add_subparsers(dest="cmd")
    r = sub.add_parser("render", help="gera a arte de um spec JSON")
    r.add_argument("spec", help="arquivo .json do spec")
    r.add_argument("--png", action="store_true", help="grava também o PNG (para conferir o SHA-256)")
    r.add_argument("--saida", help="pasta de saída (vale mais que o 'saida' do spec)")
    t = sub.add_parser("todas", help="os 3 modelos de um canal, com os textos de exemplo")
    t.add_argument("canal", help="gta, futebol, filmes, receitas, carros ou destinos")
    t.add_argument("pasta")
    t.add_argument("--png", action="store_true")
    e = sub.add_parser("exemplos", help="os 18 exemplos + _prancha_story.jpg")
    e.add_argument("pasta")
    e.add_argument("--png", action="store_true")
    sub.add_parser("spec-exemplo", help="imprime um spec de exemplo para copiar")
    args = ap.parse_args(argv)
    if not args.cmd:
        ap.print_help()
        return 1
    try:
        if args.cmd == "render":
            out = render(args.spec, saida=args.saida, png=args.png)
            print(f"ok: {out['jpg']}")
            print(f"zonas: {out['zonas']}")
            for a in out["avisos"]:
                print(f"aviso: {a}")
            return 0
        if args.cmd == "todas":
            for out in render_todas(args.canal, args.pasta, args.png):
                print(f"ok: {out['jpg']}")
            return 0
        if args.cmd == "exemplos":
            res = render_exemplos(args.pasta, args.png)
            for out in res["resultados"]:
                print(f"ok: {out['jpg']}")
            print(f"prancha: {res['prancha']}  ({res['segundos']:.1f} s)")
            return 0
        if args.cmd == "spec-exemplo":
            print(json.dumps(_spec_exemplo(), ensure_ascii=False, indent=2))
            return 0
    except ErroStory as e:
        print(f"erro: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"erro ao ler/gravar arquivo: {e}", file=sys.stderr)
        return 1
    return 1


__all__ = ["render", "render_todas", "render_exemplos", "desenhar", "main", "ErroStory", "LARGURA", "ALTURA"]

if __name__ == "__main__":
    raise SystemExit(main())
