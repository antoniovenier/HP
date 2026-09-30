"""Linha de comando: python -m esteira <comando> ...   (--help em cada um)"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from hpbase import ler_json

from . import acoes, vigia
from .config import carregar_config, salvar_config_padrao
from .erros import ErroEsteira

DESCRICAO = """Esteira de pastas do HP Studio (etapa 3).
Pastas em H:\\HypadoLocal\\esteira\\: 01_pedidos -> 02_baixados ->
03_legenda_dublagem -> 04_edicao -> 05_revisao -> 06_agendados ->
07_postados (e 99_erros). Prioridade no nome: P0 (urgente, fura a fila),
P1 (do dia), P2 (programado)."""


def _parser() -> argparse.ArgumentParser:
    comum = argparse.ArgumentParser(add_help=False)
    comum.add_argument("--simular", action="store_true", default=argparse.SUPPRESS,
                       help="não chama nada externo (nem ffmpeg, nem scripts, nem filas "
                            "de verdade): só move e registra")
    comum.add_argument("--json", action="store_true", default=argparse.SUPPRESS,
                       dest="saida_json", help="resposta em JSON")

    p = argparse.ArgumentParser(prog="python -m esteira", description=DESCRICAO,
                                parents=[comum],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="comando", metavar="comando")

    sub.add_parser("iniciar", parents=[comum],
                   help="cria as pastas e o config.json padrão (modo sombra)")

    s = sub.add_parser("pedido", parents=[comum], help="cria um item em 01_pedidos")
    s.add_argument("--json", dest="arquivo", required=True,
                   help="arquivo pedido.json (ou - para ler da entrada padrão)")

    sub.add_parser("status", parents=[comum], help="tabela de itens por etapa")

    s = sub.add_parser("aprovar", parents=[comum], help="grava aprovado.json (05_revisao)")
    s.add_argument("item", help="nome do item (ou pedaço único do nome)")
    s.add_argument("--notas", nargs="+", required=True,
                   help="criterio=nota (0 a 10), ex.: gancho=9 legenda=8,5 audio=9")
    s.add_argument("--motivo", default="")
    s.add_argument("--revisor", default="Claude")

    s = sub.add_parser("refazer", parents=[comum], help="grava refazer.json (05_revisao)")
    s.add_argument("item")
    s.add_argument("--motivo", required=True)
    s.add_argument("--etapa", help="para onde volta: 01, 02, 03 ou 04 (opcional)")
    s.add_argument("--notas", nargs="+", help="criterio=nota (opcional)")
    s.add_argument("--ajustes", help='JSON mesclado no pedido, ex.: {"capa_tempo": 3}')
    s.add_argument("--revisor", default="Claude")

    s = sub.add_parser("tiktok-ok", parents=[comum],
                       help="o Claude agendou no TikTok pelo Chrome: grava tiktok_ok.json")
    s.add_argument("item")
    s.add_argument("--link")
    s.add_argument("--agendado-para", dest="agendado_para")

    s = sub.add_parser("confirmar", parents=[comum],
                       help="confirma uma rede à mão (pinterest, ou API em caso de dúvida)")
    s.add_argument("item")
    s.add_argument("rede")
    s.add_argument("--link")

    s = sub.add_parser("liberar", parents=[comum],
                       help="Curador ajustou o pedido depois de nota < 5: solta o item")
    s.add_argument("item")

    s = sub.add_parser("reprocessar", parents=[comum],
                       help="tira um item de 99_erros e devolve para a etapa")
    s.add_argument("item")
    s.add_argument("--etapa", help="01 a 07 (padrão: a etapa do erro)")

    s = sub.add_parser("prioridade", parents=[comum], help="muda P0/P1/P2 de um item")
    s.add_argument("item")
    s.add_argument("nova", choices=["P0", "P1", "P2", "p0", "p1", "p2"])

    s = sub.add_parser("ciclo", parents=[comum], help="roda UMA passada agora")
    s.add_argument("--max", type=int, default=None, help="no máximo N trabalhos")

    s = sub.add_parser("vigiar", parents=[comum], help="roda ciclos em loop")
    g = s.add_mutually_exclusive_group()
    g.add_argument("--uma-vez", action="store_true", help="uma passada e sai")
    g.add_argument("--intervalo", type=float, default=30, help="segundos entre ciclos (30)")
    return p


def _imprimir(obj, como_json: bool) -> None:
    if como_json:
        print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, list):
                print(f"{k}: {len(v)}")
                for x in v:
                    print(f"  - {x}")
            else:
                print(f"{k}: {v}")
    else:
        print(obj)


def main(argv: list[str] | None = None) -> int:
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(errors="replace")  # console do Windows (cp1252)
        except Exception:  # noqa: BLE001
            pass
    p = _parser()
    a = p.parse_args(argv)
    if not a.comando:
        p.print_help()
        return 2
    sim = getattr(a, "simular", False)
    js = getattr(a, "saida_json", False)
    kw = {"simular": sim}
    try:
        if a.comando == "iniciar":
            cfg = carregar_config()
            cfg.garantir_pastas()
            _imprimir({"pastas": str(cfg.raiz), "config": str(salvar_config_padrao(cfg)),
                       "modo": cfg.modo}, js)
        elif a.comando == "pedido":
            if a.arquivo == "-":
                dados = json.loads(sys.stdin.read())
            else:
                dados = ler_json(Path(a.arquivo))
                if dados is None:
                    raise ErroEsteira(f"arquivo não encontrado: {a.arquivo}")
            item = acoes.novo_pedido(dados)
            _imprimir({"criado": item.name, "pasta": str(item)}, js)
        elif a.comando == "status":
            st = acoes.status()
            print(json.dumps(st, ensure_ascii=False, indent=2) if js else acoes.tabela_status(st))
        elif a.comando == "aprovar":
            _imprimir(acoes.aprovar(a.item, a.notas, a.motivo, a.revisor, **kw), js)
        elif a.comando == "refazer":
            ajustes = json.loads(a.ajustes) if a.ajustes else None
            _imprimir(acoes.refazer(a.item, a.motivo, a.etapa, a.notas, ajustes,
                                    a.revisor, **kw), js)
        elif a.comando == "tiktok-ok":
            _imprimir(acoes.tiktok_ok(a.item, a.link, a.agendado_para, **kw), js)
        elif a.comando == "confirmar":
            _imprimir(acoes.confirmar(a.item, a.rede, a.link, **kw), js)
        elif a.comando == "liberar":
            _imprimir(acoes.liberar(a.item), js)
        elif a.comando == "reprocessar":
            _imprimir(acoes.reprocessar(a.item, a.etapa), js)
        elif a.comando == "prioridade":
            _imprimir(acoes.mudar_prioridade(a.item, a.nova), js)
        elif a.comando == "ciclo":
            _imprimir(vigia.ciclo(simular=sim, max_trabalhos=a.max), js)
        elif a.comando == "vigiar":
            ao_fim = (lambda r: _imprimir(r, js)) if a.uma_vez else None
            vigia.vigiar(a.intervalo, a.uma_vez, sim, ao_terminar_ciclo=ao_fim)
        return 0
    except (ErroEsteira, ValueError) as e:
        print(f"erro: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
