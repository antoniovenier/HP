"""Linha de comando: python -m metricas <comando> (ajuda: python -m metricas -h)."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path, PureWindowsPath

from hpbase import ler_json, obter_logger

from .config import REDES, carregar_config, pasta_metricas

NOME_TAREFA = r"HP\Metricas 6h"
PYTHONW_PADRAO = r"%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe"
AGENDADO_PADRAO = r"G:\Meu Drive\Hypado\06 Projeto\app\hp_studio_nuvem\metricas\agendado.py"


class _Formatador(argparse.RawDescriptionHelpFormatter):
    def add_usage(self, usage, actions, groups, prefix=None):
        return super().add_usage(usage, actions, groups,
                                 "uso: " if prefix is None else prefix)


def _em_portugues(ap: argparse.ArgumentParser) -> argparse.ArgumentParser:
    ap._positionals.title = "argumentos"
    ap._optionals.title = "opções"
    ap.add_argument("-h", "--help", action="help", help="mostra esta ajuda e sai")
    return ap


def _parser(**kw) -> argparse.ArgumentParser:
    return _em_portugues(argparse.ArgumentParser(formatter_class=_Formatador,
                                                 add_help=False, **kw))


def montar_parser() -> argparse.ArgumentParser:
    ap = _parser(prog="python -m metricas",
                 description="Métricas do HP Studio (etapa 6): Instagram, Threads, Facebook "
                             "e YouTube pela API oficial; TikTok por importação manual.")
    sub = ap.add_subparsers(dest="comando", metavar="comando", title="comandos")
    sub.required = True

    def novo(nome, ajuda):
        return _em_portugues(sub.add_parser(nome, help=ajuda, description=ajuda,
                                            formatter_class=_Formatador, add_help=False))

    c = novo("coletar", "coleta agora e grava a foto do dia (todas as contas/redes ou só as escolhidas)")
    c.add_argument("--conta", action="append", help="só esta conta (gta, futebol, filmes, "
                                                    "receitas, carros, destinos); pode repetir")
    c.add_argument("--rede", action="append", choices=REDES, help="só esta rede; pode repetir")
    c.add_argument("--simular", action="store_true",
                   help="não chama a API nem grava: só mostra o que faria e se os tokens existem")
    c.add_argument("--contas", help="outro contas.json")
    c.add_argument("--saida", help=r"pasta de saída (padrão H:\HypadoLocal\metricas)")

    r = novo("resumo", "mostra o resumo de um dia (seguidores, deltas, status e top posts)")
    r.add_argument("--data", help="AAAA-MM-DD (padrão: a foto mais recente)")
    r.add_argument("--json", action="store_true", help="imprime a análise em JSON")
    r.add_argument("--saida", help="pasta das fotos")

    t = novo("importar-tiktok", "importa um CSV/JSON manual do TikTok para a foto do dia")
    t.add_argument("arquivo", help="caminho do .csv ou .json")
    t.add_argument("--conta", help="conta de todas as linhas (se o arquivo não tiver a coluna conta)")
    t.add_argument("--data", help="AAAA-MM-DD da foto (padrão: hoje)")
    t.add_argument("--contas", help="outro contas.json")
    t.add_argument("--saida", help="pasta das fotos")

    a = novo("agendar-6h", "imprime o comando schtasks para agendar a coleta diária (não executa)")
    a.add_argument("--hora", default="06:00", help="HH:MM (padrão 06:00)")

    k = novo("chaves", "mostra quais chaves de token existem em segredos\\ (só os nomes, nunca o valor)")
    k.add_argument("--conta", action="append", help="só esta conta; pode repetir")
    k.add_argument("--rede", action="append", choices=REDES, help="só esta rede; pode repetir")
    k.add_argument("--json", action="store_true", help="imprime o inventário em JSON")
    k.add_argument("--contas", help="outro contas.json")
    k.add_argument("--segredos", help=r"outra pasta de segredos (padrão H:\HypadoLocal\segredos)")
    return ap


def _fmt(n) -> str:
    if n is None:
        return "—"
    return f"{n:,.0f}".replace(",", ".") if isinstance(n, (int, float)) else str(n)


def _delta(n) -> str:
    return "—" if n is None else f"{'+' if n >= 0 else ''}{_fmt(n) if n >= 0 else '-' + _fmt(-n)}"


def texto_resumo(foto: dict, cfg: dict | None = None) -> str:
    from .painel import montar
    p = montar(foto, cfg)
    linhas = [f"Métricas de {foto.get('data')} (coletado em {foto.get('coletado_em')})"]
    for conta, c in p["contas"].items():
        linhas.append(f"\n{c['nome']}  — seguidores {_fmt(c['seguidores_total'])} "
                      f"({_delta(c['delta_dia_total'])} no dia)")
        for rede, r in c["redes"].items():
            eng = r.get("taxa_engajamento")
            linhas.append(f"  {rede:<10} {str(r['status'])[:40]:<24} seg. {_fmt(r['seguidores'])}"
                          f"  dia {_delta(r['delta_dia'])}  7d {_delta(r['delta_7d'])}"
                          f"  views 24h {_fmt(r['views_24h'])}"
                          f"  engaj. {'—' if eng is None else f'{eng * 100:.1f}%'}")
    for janela in ("24h", "7d"):
        linhas.append(f"\nTop 5 por views ({janela}):")
        for i, t in enumerate(p["top_posts"][janela], 1):
            linhas.append(f"  {i}. {_fmt(t['views'])} views  {t['conta']}/{t['rede']}  "
                          f"{t.get('tipo')}  {t.get('legenda_inicio') or ''}  {t.get('link') or ''}")
        if not p["top_posts"][janela]:
            linhas.append("  (nenhum post com views)")
    return "\n".join(linhas)


def comando_schtasks(hora: str = "06:00") -> list:
    if os.name == "nt":
        pythonw = str(Path(sys.executable).with_name("pythonw.exe"))
        script = str(Path(__file__).resolve().with_name("agendado.py"))
    else:
        pythonw, script = PYTHONW_PADRAO, str(PureWindowsPath(AGENDADO_PADRAO))
    tr = f'\\"{pythonw}\\" \\"{script}\\" coletar'
    return [
        "Cole no PowerShell (uma linha só; o --% faz o PowerShell não mexer nas aspas):",
        f'schtasks --% /Create /TN "{NOME_TAREFA}" /SC DAILY /ST {hora} /F /TR "{tr}"',
        "",
        "(No Prompt de Comando - cmd - é a mesma linha sem o --%.)",
        "Opcional, para rodar assim que o PC ligar se ele estava desligado às 6h:",
        "$t = Get-ScheduledTask -TaskPath '\\HP\\' -TaskName 'Metricas 6h'; "
        "$t.Settings.StartWhenAvailable = $true; Set-ScheduledTask -InputObject $t",
        f'Conferir: schtasks /Query /TN "{NOME_TAREFA}"   Rodar agora: schtasks /Run /TN "{NOME_TAREFA}"',
        f'Remover:  schtasks /Delete /TN "{NOME_TAREFA}" /F',
    ]


def main(argv=None) -> int:
    args = montar_parser().parse_args(argv)
    log = obter_logger("metricas")
    try:
        if args.comando == "coletar":
            from .coleta import coletar, plano
            cfg = carregar_config(args.contas)
            if args.simular:
                print("SIMULAR — nada será chamado nem gravado:")
                for l in plano(args.conta, args.rede, cfg):
                    print("  " + l)
                return 0
            foto = coletar(args.conta, args.rede, config=cfg, saida=args.saida)
            for conta, redes in foto["contas"].items():
                if args.conta and conta not in args.conta:
                    continue
                for rede, r in redes.items():
                    if args.rede and rede not in args.rede:
                        continue
                    print(f"{conta}/{rede}: {r.get('status')} "
                          f"(seguidores {_fmt(r.get('seguidores'))}, posts {len(r.get('posts') or [])})")
            print(f"Gravado em {pasta_metricas(args.saida) / (foto['data'] + '.json')}")
            return 0
        if args.comando == "resumo":
            pasta = pasta_metricas(args.saida)
            foto = ler_json(pasta / f"{date.fromisoformat(args.data)}.json" if args.data
                            else pasta / "ultimo.json", None)
            if not foto:
                print("Nenhuma foto encontrada para essa data.")
                return 1
            if args.json:
                print(json.dumps(foto.get("analise") or {}, ensure_ascii=False, indent=2))
            else:
                print(texto_resumo(foto, carregar_config()))
            return 0
        if args.comando == "importar-tiktok":
            from .tiktok import importar
            res = importar(args.arquivo, conta=args.conta, data=args.data, saida=args.saida,
                           config=carregar_config(args.contas))
            for conta, n in res.items():
                print(f"tiktok/{conta}: {n} posts importados (fonte: manual)")
            return 0
        if args.comando == "agendar-6h":
            print("\n".join(comando_schtasks(args.hora)))
            return 0
        if args.comando == "chaves":
            from hpbase import pasta_segredos
            from .chaves_pc import inventario, resumo
            cfg = carregar_config(args.contas)
            inv = inventario(args.segredos or pasta_segredos(), cfg, args.conta, args.rede)
            if args.json:
                print(json.dumps(inv, ensure_ascii=False, indent=2))
            else:
                print("Chaves em segredos\\ (só os nomes; o valor nunca é lido aqui):")
                for linha in resumo(inv):
                    print("  " + linha)
            return 0
    except (ValueError, FileNotFoundError) as e:
        log.warning(f"{args.comando}: {e}")
        print(f"Erro: {e}", file=sys.stderr)
        return 2
    except Exception as e:  # noqa: BLE001
        log.error(f"{args.comando} falhou: {type(e).__name__}: {e}")
        print(f"Erro: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
