"""Orquestra a coleta: cada conta × rede é isolada — a falha de uma rede vira
só um status ("erro:<mensagem mascarada>", "nao_autorizado", "sem_token") e as
outras seguem normalmente.

Saídas em H:\\HypadoLocal\\metricas\\:
- AAAA-MM-DD.json  (foto do dia; coleta sob demanda no mesmo dia MESCLA)
- ultimo.json      (cópia da foto mais recente)
- metricas_painel.json (resumo para o painel; ver painel.py)
"""
from __future__ import annotations

import json
from pathlib import Path

from hpbase import agora as agora_brasilia, escrever_json, ler_json, obter_logger
from hpbase import pasta_segredos as hp_pasta_segredos

from . import calculos, chaves_pc, facebook, instagram, painel, threads, youtube
from .cliente import ClienteHTTP, ErroNaoAutorizado
from .config import (REDES, Contexto, Credenciais, carregar_config,
                     pasta_metricas)
from .modelos import SemToken

VERSAO = 1
COLETORES = {"instagram": instagram.coletar, "threads": threads.coletar,
             "facebook": facebook.coletar, "youtube": youtube.coletar}


def escolher(pedido, todos, nome: str) -> list:
    if not pedido:
        return list(todos)
    lista = [pedido] if isinstance(pedido, str) else list(pedido)
    desconhecidos = [x for x in lista if x not in todos]
    if desconhecidos:
        raise ValueError(f"{nome} desconhecida: {', '.join(desconhecidos)} "
                         f"(válidas: {', '.join(todos)})")
    return lista


def _mensagem(e, cred: Credenciais) -> str:
    return " ".join(cred.mascarar(str(e) or type(e).__name__).split())[:200]


def coletar_rede(cliente, conta: str, rede: str, cfg_rede: dict, cred, ctx) -> dict:
    try:
        res = COLETORES[rede](cliente, conta, cfg_rede, cred, ctx)
    except SemToken as e:
        res = {"status": "sem_token", "detalhe": _mensagem(e, cred)}
    except ErroNaoAutorizado as e:
        res = {"status": "nao_autorizado", "detalhe": _mensagem(e, cred)}
    except Exception as e:  # noqa: BLE001 — uma rede nunca derruba as outras
        res = {"status": f"erro:{_mensagem(e, cred)}"}
    res["fonte"] = "api"
    res["coletado_em"] = ctx.agora.isoformat(timespec="seconds")
    if res["status"] == "ok":
        posts = res.setdefault("posts", [])
        for p in posts:
            p["taxa_engajamento"] = calculos.taxa_engajamento(p)
        res["totais"] = calculos.totais(posts)
        res["avisos"] = [_mensagem(a, cred) for a in res.get("avisos") or []]
    return res


def _sanear(foto: dict, cred: Credenciais) -> dict:
    """Última barreira: nenhum valor lido de segredo entra no JSON."""
    texto = json.dumps(foto, ensure_ascii=False)
    limpo = texto
    for v in sorted(cred._lidos, key=len, reverse=True):
        limpo = limpo.replace(json.dumps(v, ensure_ascii=False)[1:-1], "***")
    return foto if limpo == texto else json.loads(limpo)


def salvar(foto: dict, pasta: Path, cfg: dict | None = None) -> Path:
    """Grava a foto do dia, o ultimo.json e o metricas_painel.json."""
    pasta = Path(pasta)
    foto["analise"] = calculos.analise(foto, pasta)
    arq = escrever_json(pasta / f"{foto['data']}.json", foto)
    ultimo = ler_json(pasta / "ultimo.json", None) or {}
    if str(ultimo.get("data") or "") <= foto["data"]:
        escrever_json(pasta / "ultimo.json", foto)
        painel.exportar(foto, pasta, cfg)
    return arq


def coletar(contas=None, redes=None, cliente=None, config: dict | None = None,
            agora=None, saida=None, pasta_segredos=None, gravar: bool = True) -> dict:
    cfg = config if config is not None else carregar_config()
    agora = agora or agora_brasilia()
    pasta = pasta_metricas(saida)
    data = agora.date().isoformat()
    foto = ler_json(pasta / f"{data}.json", None) or {}
    foto.setdefault("contas", {})
    foto.update({"data": data, "versao": VERSAO})
    cliente = cliente or ClienteHTTP(timeout=cfg.get("timeout", 30))
    cred = Credenciais(cfg["arquivos_segredo"], pasta_segredos)
    ctx = Contexto(agora, cfg)
    log = obter_logger("metricas")
    for conta in escolher(contas, cfg["contas"], "conta"):
        cfg_conta = cfg["contas"].get(conta) or {}
        destino = foto["contas"].setdefault(conta, {})
        for rede in escolher(redes, REDES, "rede"):
            cfg_rede = cfg_conta.get(rede)
            if not isinstance(cfg_rede, dict) or not cfg_rede.get("ativo", True):
                continue
            if rede == "tiktok":  # sem API: só marca a fonte; dados vêm do importar-tiktok
                atual = destino.get("tiktok") or {}
                if atual.get("status") != "ok":
                    destino["tiktok"] = {"fonte": "manual", "status": "aguardando_importacao",
                                         "seguidores": None, "posts": []}
                continue
            res = coletar_rede(cliente, conta, rede, cfg_rede, cred, ctx)
            anterior = destino.get(rede)
            if res["status"] != "ok" and isinstance(anterior, dict) \
                    and anterior.get("status") == "ok":
                # coleta sob demanda falhou: mantém os números da coleta boa do dia
                res = {**anterior, "status": res["status"], "detalhe": res.get("detalhe"),
                       "dados_de": anterior.get("coletado_em"),
                       "coletado_em": res["coletado_em"]}
            destino[rede] = res
            log.info(_mensagem(f"{conta}/{rede}: {res['status']} "
                               f"({len(res.get('posts') or [])} posts)", cred))
    foto["coletado_em"] = agora.isoformat(timespec="seconds")
    foto = _sanear(foto, cred)
    if gravar:
        salvar(foto, pasta, cfg)
    return foto


def _onde(e: dict) -> str:
    nomes = e.get("nomes") or [e.get("chave_token")]
    antigo = next((n for n in nomes[1:] if n.upper() != nomes[0].upper()), None)
    return f"{nomes[0]}{f' (ou o antigo {antigo})' if antigo else ''} em {e.get('arquivo')}"


def plano(contas=None, redes=None, config: dict | None = None, pasta_segredos=None) -> list:
    """O que o `coletar` faria (modo --simular): não chama API nem grava nada. Usa o
    inventário de chaves_pc (só NOMES das chaves; nenhum valor é lido)."""
    cfg = config if config is not None else carregar_config()
    inv = chaves_pc.inventario(pasta_segredos or hp_pasta_segredos(), cfg,
                               escolher(contas, cfg["contas"], "conta"),
                               escolher(redes, REDES, "rede"))
    linhas = []
    for conta, por_rede in inv.items():
        for rede, e in por_rede.items():
            st = e["status"]
            if st == "inativo":
                continue
            if st == "manual":
                situacao = "manual (use importar-tiktok)"
            elif rede == "youtube":
                if st == "nao_autorizado":
                    situacao = 'pularia: nao_autorizado ("autorizado": false)'
                else:
                    o = e["oauth"]
                    oauth = all(o.values())
                    canal = bool(e.get("id"))
                    situacao = ("coletaria" if st == "ok" else "sem_token") + \
                        f" (canal: {'ok' if canal else 'falta ' + e['nomes_id'][0]}," \
                        f" chave: {'ok' if e['api_key'] else 'falta'}," \
                        f" analytics: {'ok' if oauth else 'nao_autorizado'}" \
                        f"{'' if oauth else ' — falta ' + _onde(e)})"
            else:
                tok = "token" not in e["falta"]
                ident = "id" not in e["falta"]
                situacao = ("coletaria" if st == "ok" else "sem_token") + \
                    f" (token: {'ok' if tok else 'falta ' + _onde(e)}," \
                    f" id: {'ok' if ident else 'falta ' + e['nomes_id'][0]})"
            linhas.append(f"{conta}/{rede}: {situacao}")
    return linhas
