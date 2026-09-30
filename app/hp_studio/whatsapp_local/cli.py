"""Linha de comando: python -m whatsapp_local <comando> [opções]

Pensado para rodar com pythonw (sem console) pelo Agendador de Tarefas:
nada aqui depende de console; tudo vai para o log
H:\\HypadoLocal\\app\\logs\\whatsapp_<dia>.log.
Códigos de saída: 0 ok · 1 erro · 2 precisa login (QR).
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from .config import candidatos_metricas, carregar_config, preparar_pastas
from .enviador import Enviador, ResultadoCiclo
from .fila import Fila
from .recebidas import ArquivoRecebidas
from .ritmo import Relogio
from .situacao import coletar_status, texto_status
from .sombra import gerar_relatorio
from .tarefas import enfileirar_no_ar, enfileirar_resumo_dia, enfileirar_resumo_sabado


class _Formatador(argparse.RawDescriptionHelpFormatter):
    def add_usage(self, usage, actions, groups, prefix=None):
        return super().add_usage(usage, actions, groups,
                                 "uso: " if prefix is None else prefix)


def _novo(p: argparse.ArgumentParser) -> argparse.ArgumentParser:
    p._positionals.title = "argumentos"
    p._optionals.title = "opções"
    p.add_argument("-h", "--help", action="help", help="mostra esta ajuda e sai")
    return p


def _modo(p: argparse.ArgumentParser) -> None:
    g = p.add_mutually_exclusive_group()
    g.add_argument("--sombra", dest="modo", action="store_const", const="sombra",
                   help="só monta e compara com o plantão; NÃO abre o navegador")
    g.add_argument("--real", dest="modo", action="store_const", const="real",
                   help="envia de verdade pelo WhatsApp Web")
    p.set_defaults(modo=None)


def montar_parser() -> argparse.ArgumentParser:
    p = _novo(argparse.ArgumentParser(
        prog="python -m whatsapp_local", add_help=False, formatter_class=_Formatador,
        description="Enviador local de WhatsApp da HP (página oficial web.whatsapp.com).\n"
                    "Só 3 tipos de mensagem (resumo_dia, no_ar, resumo_sabado), sempre\n"
                    "começando com '*Claude - *', só para os grupos permitidos.\n"
                    "Sem --sombra/--real vale o 'modo' do config.json (padrão: sombra)."))
    sub = p.add_subparsers(dest="comando", metavar="comando", title="comandos")
    sub.required = True

    def cmd(nome, ajuda):
        return _novo(sub.add_parser(nome, help=ajuda, description=ajuda, add_help=False,
                                    formatter_class=_Formatador))

    s = cmd("login", "abre o WhatsApp Web VISÍVEL e espera o Antônio escanear o QR (1 vez)")
    s.add_argument("--timeout", type=int, default=None,
                   help="segundos esperando o QR (padrão: 300)")

    s = cmd("enviar", "processa a fila (valida, envia ou faz a sombra)")
    s.add_argument("--uma-vez", action="store_true",
                   help="uma passada na fila e sai (use no Agendador de Tarefas)")
    _modo(s)

    s = cmd("vigiar", "fica rodando: 1 ciclo a cada --intervalo segundos")
    s.add_argument("--intervalo", type=int, default=60, help="segundos entre ciclos (padrão 60)")
    s.add_argument("--ciclos", type=int, default=0, help="para depois de N ciclos (0 = nunca)")
    _modo(s)

    s = cmd("montar-no-ar", "monta o aviso 'no ar' dos posts que já entraram no ar e põe na fila")
    s.add_argument("agendados", help="caminho do agendados.json")
    s.add_argument("--grupo", help="grupo de destino (padrão: do post, grupo_por_canal ou Comissão)")
    s.add_argument("--modelo", help="AVISO.md alternativo (padrão: 06 Projeto\\AVISO.md)")
    s.add_argument("--janela-horas", type=float, default=None,
                   help="ignora posts mais velhos que isso (padrão 24)")
    s.add_argument("--so-mostrar", action="store_true", help="só mostra o texto, não enfileira")

    for nome, ajuda, campo in (("montar-resumo", "monta o resumo do dia (padrão: ontem)", "--dia"),
                               ("montar-sabado", "monta o resumo da semana (sábado)", "--sabado")):
        s = cmd(nome, ajuda)
        s.add_argument(campo, help="data AAAA-MM-DD")
        s.add_argument("--metricas", help="caminho do metricas_painel.json")
        s.add_argument("--grupo", help="grupo de destino (padrão: HP | Comissão 🚀)")
        s.add_argument("--so-mostrar", action="store_true", help="só mostra o texto, não enfileira")

    cmd("status", "mostra modo, fila, ritmo, login e últimos resultados")

    s = cmd("ler-recebidas", "lê os grupos permitidos e salva as mensagens novas do Antônio")
    _modo(s)

    s = cmd("relatorio-sombra", "refaz o relatório de diferenças app x plantão de um dia")
    s.add_argument("--dia", help="data AAAA-MM-DD (padrão: hoje)")
    return p


def _dizer(*linhas: str) -> None:
    # Com pythonw não existe console (sys.stdout é None): print não faz nada.
    for l in linhas:
        print(l)


def _saida_segura() -> None:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(errors="replace")   # emoji em console cp850 não derruba
        except Exception:
            pass


def _codigo(res: ResultadoCiclo) -> int:
    return 2 if res.precisa_login else (1 if res.erro else 0)


def _data(s: str | None) -> date | None:
    return date.fromisoformat(s) if s else None


def main(argv=None, fabrica_navegador=None, relogio: Relogio | None = None) -> int:
    _saida_segura()
    args = montar_parser().parse_args(argv)
    relogio = relogio or Relogio()
    preparar_pastas()

    def enviador() -> Enviador:  # config relida a cada uso (trocar o modo sem reiniciar)
        return Enviador(carregar_config(), fabrica_navegador, relogio)

    c = args.comando
    if c == "login":
        ok = enviador().login(args.timeout, avisar=_dizer)
        _dizer("Login OK: o WhatsApp Web ficou guardado no perfil." if ok else
               "O login não terminou (QR não escaneado a tempo). Rode de novo.")
        return 0 if ok else 2

    if c == "enviar":
        while True:
            res = enviador().ciclo(args.modo)
            _dizer(res.resumo())
            if args.uma_vez or res.erro or res.precisa_login or not Fila().pendentes():
                return _codigo(res)
            relogio.dormir(60)

    if c == "vigiar":
        n = 0
        while True:
            res = enviador().ciclo(args.modo)
            _dizer(f"[{relogio.agora():%d/%m %H:%M:%S}] {res.resumo()}")
            n += 1
            if args.ciclos and n >= args.ciclos:
                return _codigo(res)
            relogio.dormir(max(10, args.intervalo))

    cfg = carregar_config()
    agora = relogio.agora()
    if c == "montar-no-ar":
        if not Path(args.agendados).exists():
            _dizer(f"Não achei o arquivo: {args.agendados}")
            return 1
        msgs = enfileirar_no_ar(Path(args.agendados), cfg, agora, grupo=args.grupo,
                                modelo=Path(args.modelo) if args.modelo else None,
                                janela_horas=args.janela_horas, so_mostrar=args.so_mostrar)
        if not msgs:
            _dizer("Nenhum post no ar com link dentro da janela.")
        for m in msgs:
            _dizer(f"--- {m['_situacao']}: {m['id']} → {m['grupo']}", m["texto"])
        return 0

    if c in ("montar-resumo", "montar-sabado"):
        kw = dict(metricas=Path(args.metricas) if args.metricas else None,
                  grupo=args.grupo, so_mostrar=args.so_mostrar)
        m = (enfileirar_resumo_dia(cfg, agora, dia=_data(args.dia), **kw) if c == "montar-resumo"
             else enfileirar_resumo_sabado(cfg, agora, sabado=_data(args.sabado), **kw))
        if not m:
            _dizer("Sem métricas para esse período. Procurei em: "
                   + (args.metricas or ", ".join(str(p) for p in candidatos_metricas())))
            return 1
        _dizer(f"--- {m['_situacao']}: {m['id']} → {m['grupo']}", m["texto"])
        return 0

    if c == "status":
        _dizer(texto_status(coletar_status(relogio)))
        return 0

    if c == "ler-recebidas":
        e = enviador()
        if e.modo(args.modo) == "sombra":
            resumo = ArquivoRecebidas().resumo()
            _dizer("Modo sombra: o navegador não abre. Use --real para ler os grupos.",
                   f"Recebidas já salvas: {sum(resumo.values())} em {len(resumo)} dia(s).")
            return 0
        res = e.ler_recebidas("real")
        _dizer(res.resumo())
        return _codigo(res)

    if c == "relatorio-sombra":
        arq = gerar_relatorio(_data(args.dia) or agora.date(), agora.isoformat(timespec="seconds"))
        _dizer(f"Relatório: {arq}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
