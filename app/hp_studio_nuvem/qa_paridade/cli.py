"""Linha de comando: python -m qa_paridade <comando> ...

Códigos de saída: 0 = aprovado (passa no dia) / status ok, 1 = não passou,
2 = erro de entrada (arquivo/pasta não encontrado, mídia ilegível),
3 = PC ocupado com outro trabalho pesado ou horário proibido (18h-22h30).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from hpbase import TravaOcupada

from . import motor, sombra
from .limites import carregar_limites
from .midia import ErroMidia
from .util import NOMES, br

DESCRICAO = ("Teste de paridade do HP Studio: compara o que o app fez com o que o "
             "Claude fez (referência) e dá nota de 0 a 10 por métrica. Com --tarefa, "
             "registra o dia no modo sombra (7 dias aprovados seguidos liberam a tarefa).")


class _Formatador(argparse.HelpFormatter):
    def add_usage(self, usage, actions, groups, prefix=None):
        return super().add_usage(usage, actions, groups,
                                 "uso: " if prefix is None else prefix)


class _Parser(argparse.ArgumentParser):
    """ArgumentParser com a ajuda e os erros em português."""

    def __init__(self, *a, **kw):
        kw.setdefault("formatter_class", _Formatador)
        kw["add_help"] = False
        super().__init__(*a, **kw)
        self._positionals.title = "argumentos"
        self._optionals.title = "opções"
        self.add_argument("-h", "--help", action="help", help="mostra esta ajuda e sai")

    def error(self, message):
        trocas = {"the following arguments are required": "faltam os argumentos",
                  "unrecognized arguments": "argumentos desconhecidos",
                  "invalid choice": "opção inválida",
                  "expected one argument": "falta o valor"}
        for en, pt in trocas.items():
            message = message.replace(en, pt)
        self.print_usage(sys.stderr)
        self.exit(2, f"erro: {message}\n")


def _comuns(p: argparse.ArgumentParser) -> None:
    p.add_argument("--tarefa", help="nome da tarefa no modo sombra (ex.: editor_reel); "
                                    "sem isso o relatório vai para paridade\\_avulsos")
    p.add_argument("--id", help="identificador da comparação (ex.: id do post); "
                                "padrão: hora HHMMSS")
    p.add_argument("--saida", help="pasta para o relatório quando não há --tarefa")
    p.add_argument("--limites", help="arquivo JSON com limites que trocam os do limites.json")
    p.add_argument("--json", action="store_true", help="imprime o relatório inteiro em JSON")


def montar_parser() -> argparse.ArgumentParser:
    p = _Parser(prog="python -m qa_paridade", description=DESCRICAO)
    sub = p.add_subparsers(dest="comando", metavar="comando", required=True,
                         title="comandos", parser_class=_Parser)

    v = sub.add_parser("video", help="compara dois vídeos (duração, SSIM, loudness, legenda, formato)",
                       description="Compara o vídeo do app com o de referência.")
    v.add_argument("app", help="vídeo feito pelo app")
    v.add_argument("ref", help="vídeo de referência (feito 100%% pelo Claude)")
    v.add_argument("--legenda-app", help="legenda do app (.srt/.ass/.vtt)")
    v.add_argument("--legenda-ref", help="legenda da referência (.srt/.ass/.vtt)")
    _comuns(v)

    i = sub.add_parser("imagem", help="compara duas artes/lâminas (SSIM e resolução)",
                       description="Compara a arte do app com a de referência.")
    i.add_argument("app", help="imagem feita pelo app")
    i.add_argument("ref", help="imagem de referência")
    _comuns(i)

    l = sub.add_parser("laminas", help="compara duas pastas de lâminas (quantidade, ordem, SSIM)",
                       description="Compara as lâminas (carrossel/estáticos) de duas pastas, "
                                   "na ordem natural do nome.")
    l.add_argument("app", help="pasta com as lâminas do app")
    l.add_argument("ref", help="pasta com as lâminas de referência")
    _comuns(l)

    g = sub.add_parser("legenda", help="compara duas legendas (texto, tempos, blocos)",
                       description="Compara duas legendas .srt/.ass/.vtt (ou vídeos com faixa "
                                   "de legenda).")
    g.add_argument("app", help="legenda do app")
    g.add_argument("ref", help="legenda de referência")
    _comuns(g)

    s = sub.add_parser("status", help="tabela do modo sombra (dias seguidos, falta, liberada)",
                       description="Mostra, por tarefa, quantos dias aprovados seguidos já tem, "
                                   "quantos faltam e se está liberada para o app.")
    s.add_argument("--tarefa", help="só esta tarefa")
    s.add_argument("--json", action="store_true", help="saída em JSON")
    return p


def _imprimir(texto: str) -> None:
    try:
        print(texto)
    except UnicodeEncodeError:  # console antigo do Windows
        print(texto.encode("ascii", "replace").decode("ascii"))


def _resumo_texto(rel: dict, res: dict) -> str:
    linhas = [f"Veredito: {rel['veredito']}  |  nota final {br(rel['nota_final'])}  |  "
              f"passa no dia: {'SIM' if rel['aprovado'] else 'NÃO'}"]
    for nome, m in rel["metricas"].items():
        nota = br(m["nota"]) if m.get("aplica") else "n/a"
        linhas.append(f"  {NOMES.get(nome, nome):<18} {nota:>6}  {m.get('resumo', '')}")
    linhas.append(f"Relatório: {res['json']}")
    linhas.append(f"           {res['md']}")
    st = res.get("status")
    if st:
        linhas.append(f"Sombra '{st['tarefa']}': {st['dias_seguidos']} dia(s) aprovado(s) seguido(s), "
                      f"falta(m) {st['falta']}, liberada: {'sim' if st['liberada'] else 'não'}"
                      + (f" ({st['observacao']})" if st.get("observacao") else ""))
    return "\n".join(linhas)


def main(argv: list[str] | None = None, usar_trava: bool = True,
         agora: datetime | None = None) -> int:
    """Ponto de entrada. `usar_trava`/`agora` existem para os testes."""
    args = montar_parser().parse_args(argv)
    try:
        lim = carregar_limites(getattr(args, "limites", None))
    except (OSError, ValueError) as e:
        _imprimir(f"ERRO: limites inválidos: {e}")
        return 2

    if args.comando == "status":
        tarefas = [args.tarefa] if args.tarefa else sombra.listar_tarefas()
        lista = [sombra.status_tarefa(t, limites=lim) for t in tarefas]
        if args.json:
            _imprimir(json.dumps(lista, ensure_ascii=False, indent=2))
        else:
            _imprimir(sombra.tabela_status(lista))
        return 0

    try:
        rel = motor.comparar_por_tipo(args.comando, args.app, args.ref, lim,
                                      getattr(args, "legenda_app", None),
                                      getattr(args, "legenda_ref", None),
                                      usar_trava=usar_trava, agora_trava=agora)
        res = motor.salvar_resultado(rel, args.tarefa, args.id, lim, saida=args.saida)
    except TravaOcupada as e:
        _imprimir(f"OCUPADO: {e}. Tente de novo mais tarde.")
        return 3
    except (FileNotFoundError, ErroMidia, ValueError) as e:
        _imprimir(f"ERRO: {e}")
        return 2
    if args.json:
        _imprimir(json.dumps(rel, ensure_ascii=False, indent=2, default=str))
    else:
        _imprimir(_resumo_texto(rel, res))
    return 0 if rel["aprovado"] else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
