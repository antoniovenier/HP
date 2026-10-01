"""Ações de fora (CLI, gancho do motor, Claude): pedido, status, aprovar,
refazer, tiktok-ok, confirmar, liberar, reprocessar, prioridade.

As ações só gravam arquivos na pasta do item e, quando possível, já
processam aquele item na hora (segurando a trava do vigia). Se um vigia
estiver rodando, ele aplica no próximo ciclo.
"""
from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path

from hpbase import agora_iso, escrever_json, garantir, ler_json

from .config import Config, carregar_config
from .constantes import (AGENDADOS, ARQ_AGUARDANDO_CURADOR, ARQ_APROVADO,
                         ARQ_CONFIRMACOES, ARQ_ERRO, ARQ_MARCADOR, ARQ_PEDIDO,
                         ARQ_REFAZER, ERROS, ETAPAS, POSTADOS,
                         PRIORIDADES, REDES, REVISAO, TODAS_AS_PASTAS)
from .erros import ErroEsteira, PedidoInvalido
from .pastas import (achar_item, historico, ler_estado, ler_nome, listar, mover,
                     salvar_estado)
from .pedido import criar_pedido, ler_pedido
from .revisao import (calcular_media, normalizar_etapa, validar_notas,
                      veredito_da_media)
from .vigia import com_trava_vigia


def _cfg(cfg: Config | None) -> Config:
    c = cfg or carregar_config()
    c.garantir_pastas()
    return c


def ler_notas(textos) -> dict[str, float]:
    """['gancho=9', 'legenda=8,5'] ou 'gancho=9,legenda=8' -> dict."""
    if isinstance(textos, dict):
        return validar_notas(textos)
    if isinstance(textos, str):
        textos = [textos]
    pares = {}
    for t in textos or []:
        for parte in re.split(r"[;\s]+|,(?=\s*[A-Za-z_])", str(t)):
            parte = parte.strip()
            if not parte:
                continue
            if "=" not in parte and ":" not in parte:
                raise ErroEsteira(f"nota '{parte}' fora do formato criterio=nota")
            k, v = re.split(r"[=:]", parte, maxsplit=1)
            pares[k.strip()] = v.strip()
    return validar_notas(pares)


def _processar_agora(cfg: Config, item: Path, simular: bool = False,
                     agora: datetime | None = None, plugins=None) -> str:
    from .motor import Esteira

    def rodar():
        etapa = item.parent.name
        e = Esteira(cfg, plugins, simular, agora)
        trab = e.trabalhos.get(etapa)
        if trab is None or not item.exists() or not trab.acionavel(item):
            return "nada a fazer agora"
        if trab.eh_pesado(item):
            return "etapa pesada: o vigia processa no próximo ciclo"
        res = e.processar(item, etapa, False)
        return f"{res.status}: {res.mensagem}"
    ok, r = com_trava_vigia(cfg, rodar)
    return r if ok else f"o vigia aplica no próximo ciclo ({r})"


# --- pedido e status --------------------------------------------------------------
def novo_pedido(dados: dict, cfg: Config | None = None) -> Path:
    return criar_pedido(dados, raiz=_cfg(cfg).raiz)


def _situacao(item: Path, etapa: str) -> str:
    est = ler_estado(item)
    partes = []
    if (item / ARQ_AGUARDANDO_CURADOR).exists():
        partes.append("aguardando Curador (liberar)")
    if est.get("voltas"):
        partes.append(f"voltas {est['voltas']}")
    if etapa == ERROS:
        partes.append((ler_json(item / ARQ_ERRO, {}) or {}).get("mensagem", "erro"))
    elif est.get("aguardando"):
        partes.append(est["aguardando"].split(": ", 1)[-1])
    if (item / ARQ_MARCADOR).exists():
        partes.append("em andamento")
    tent = {k: v for k, v in est.get("tentativas", {}).items() if v}
    if tent:
        partes.append("tentativas " + ", ".join(f"{k}={v}" for k, v in tent.items()))
    return " · ".join(partes)


def status(cfg: Config | None = None) -> dict:
    cfg = _cfg(cfg)
    saida = {}
    for etapa in TODAS_AS_PASTAS:
        itens = []
        for item in listar(cfg.pasta(etapa)):
            info = ler_nome(item.name)
            itens.append({"item": item.name,
                          "prioridade": info.prioridade if info else "?",
                          "horario": f"{info.data} {info.hora[:2]}:{info.hora[2:]}" if info else "?",
                          "situacao": _situacao(item, etapa)})
        saida[etapa] = itens
    return saida


def tabela_status(st: dict) -> str:
    linhas = [f"{'ETAPA':<22}{'QTD':>4}  ITENS", "-" * 78]
    for etapa, itens in st.items():
        if not itens:
            linhas.append(f"{etapa:<22}{0:>4}")
            continue
        for i, it in enumerate(itens):
            cab = f"{etapa:<22}{len(itens):>4}" if i == 0 else " " * 26
            sit = f"  [{it['situacao']}]" if it["situacao"] else ""
            linhas.append(f"{cab}  {it['item']}{sit}")
    return "\n".join(linhas)


# --- revisão ------------------------------------------------------------------------
def _na_etapa(item: Path, etapa: str) -> None:
    if item.parent.name != etapa:
        raise ErroEsteira(f"{item.name} está em {item.parent.name}, não em {etapa}")


def aprovar(ref: str, notas, motivo: str = "", revisor: str = "Claude",
            cfg: Config | None = None, processar: bool = True, simular: bool = False,
            agora: datetime | None = None, plugins=None) -> dict:
    cfg = _cfg(cfg)
    item = achar_item(cfg.raiz, ref)
    _na_etapa(item, REVISAO)
    n = ler_notas(notas)
    media = calcular_media(n)
    dados = {"notas": n, "media": media, "veredito": veredito_da_media(media),
             "motivo": motivo, "revisor": revisor, "criado_em": agora_iso()}
    escrever_json(item / ARQ_APROVADO, dados)
    historico(item, f"[{REVISAO}] aprovado.json gravado por {revisor} "
                    f"(média {media}, {dados['veredito']})")
    r = _processar_agora(cfg, item, simular, agora, plugins) if processar else "gravado"
    return {"item": item.name, "media": media, "veredito": dados["veredito"], "resultado": r}


def refazer(ref: str, motivo: str, etapa: str | None = None, notas=None,
            ajustes: dict | None = None, revisor: str = "Claude",
            cfg: Config | None = None, processar: bool = True, simular: bool = False,
            agora: datetime | None = None, plugins=None) -> dict:
    cfg = _cfg(cfg)
    item = achar_item(cfg.raiz, ref)
    _na_etapa(item, REVISAO)
    dados = {"motivo": motivo, "revisor": revisor, "criado_em": agora_iso()}
    if notas:
        n = ler_notas(notas)
        dados.update({"notas": n, "media": calcular_media(n)})
        dados["veredito"] = veredito_da_media(dados["media"])
    if etapa:
        e = normalizar_etapa(etapa)
        if e not in ETAPAS[:4]:
            raise ErroEsteira(f"etapa '{etapa}' inválida para refazer (use 01 a 04)")
        dados["etapa_destino"] = e
    if ajustes:
        dados["ajustes"] = ajustes
    escrever_json(item / ARQ_REFAZER, dados)
    historico(item, f"[{REVISAO}] refazer.json gravado por {revisor}: {motivo}")
    r = _processar_agora(cfg, item, simular, agora, plugins) if processar else "gravado"
    return {"item": item.name, "resultado": r, **{k: dados.get(k) for k in
                                                   ("media", "veredito", "etapa_destino")}}


# --- agendamento ------------------------------------------------------------------------
def confirmar(ref: str, rede: str, link: str | None = None, status_rede: str = "agendado",
              agendado_para: str | None = None, por: str = "Claude",
              cfg: Config | None = None, processar: bool = True, simular: bool = False,
              agora: datetime | None = None, plugins=None) -> dict:
    """Confirma uma rede do item. TikTok/Pinterest: grava <rede>_ok.json (o que
    o Claude faz depois de agendar pelo Chrome). Rede de API: confirmação
    manual direto em confirmacoes.json."""
    cfg = _cfg(cfg)
    rede = rede.strip().lower()
    if rede not in REDES:
        raise ErroEsteira(f"rede '{rede}' desconhecida (use {', '.join(REDES)})")
    item = achar_item(cfg.raiz, ref)
    if item.parent.name not in (AGENDADOS, POSTADOS):
        raise ErroEsteira(f"{item.name} está em {item.parent.name}; só dá para "
                          f"confirmar em {AGENDADOS}")
    dados = {"rede": rede, "status": status_rede, "link": link,
             "agendado_para": agendado_para, "por": por, "em": agora_iso()}
    if rede in cfg.redes_api:
        conf = ler_json(item / ARQ_CONFIRMACOES, {}) or {}
        conf[rede] = {**dados, "fonte": "manual"}
        escrever_json(item / ARQ_CONFIRMACOES, conf)
    else:
        escrever_json(item / f"{rede}_ok.json", dados)
    historico(item, f"[{item.parent.name}] {rede} confirmado por {por}"
                    f"{' (' + link + ')' if link else ''}")
    r = _processar_agora(cfg, item, simular, agora, plugins) if processar else "gravado"
    return {"item": item.name, "rede": rede, "resultado": r}


def tiktok_ok(ref: str, link: str | None = None, agendado_para: str | None = None,
              **kw) -> dict:
    return confirmar(ref, "tiktok", link=link, agendado_para=agendado_para, **kw)


# --- manutenção ------------------------------------------------------------------------
def liberar(ref: str, cfg: Config | None = None) -> dict:
    """Curador ajustou o pedido depois de um 'Razoável': solta o item em 01."""
    cfg = _cfg(cfg)
    item = achar_item(cfg.raiz, ref)
    marcador = item / ARQ_AGUARDANDO_CURADOR
    if not marcador.exists():
        return {"item": item.name, "resultado": "não estava aguardando o Curador"}
    try:
        ler_pedido(item)
    except PedidoInvalido as e:
        raise ErroEsteira(f"pedido.json ainda inválido, não liberei: {e}") from e
    destino = garantir(item / "revisao" / "decisoes")
    os.replace(marcador, destino / f"aguardando_curador_{datetime.now():%Y%m%d%H%M%S}.json")
    historico(item, f"[{item.parent.name}] liberado pelo Curador")
    return {"item": item.name, "resultado": "liberado"}


def reprocessar(ref: str, etapa: str | None = None, cfg: Config | None = None) -> dict:
    """Tira um item de 99_erros e devolve para a etapa do erro (ou outra)."""
    cfg = _cfg(cfg)
    item = achar_item(cfg.raiz, ref)
    _na_etapa(item, ERROS)
    erro = ler_json(item / ARQ_ERRO, {}) or {}
    destino = normalizar_etapa(etapa) if etapa else erro.get("etapa")
    if destino not in ETAPAS:
        raise ErroEsteira("diga a etapa com --etapa (não achei no erro.json)")
    if not (item / ARQ_PEDIDO).exists():
        raise ErroEsteira("item sem pedido.json: crie um pedido novo")
    nome = re.sub(r"__\d+$", "", item.name)
    if (cfg.pasta(destino) / nome).exists():
        raise ErroEsteira(f"já existe {nome} em {destino}")
    if (item / ARQ_ERRO).exists():
        arq = garantir(item / "erros_anteriores")
        os.replace(item / ARQ_ERRO, arq / f"erro_{datetime.now():%Y%m%d%H%M%S}.json")
    est = ler_estado(item)
    est["tentativas"] = {}
    est.pop("pendente", None)
    est.pop("aguardando", None)
    salvar_estado(item, est)
    (item / ARQ_MARCADOR).unlink(missing_ok=True)
    historico(item, f"[{ERROS}] reprocessar -> {destino}")
    novo = mover(item, cfg.pasta(destino), nome)
    return {"item": novo.name, "etapa": destino}


def mudar_prioridade(ref: str, nova: str, cfg: Config | None = None) -> dict:
    """P1 -> P0 quando vira bombástica, por exemplo (renomeia a pasta)."""
    cfg = _cfg(cfg)
    nova = nova.strip().upper()
    if nova not in PRIORIDADES:
        raise ErroEsteira("prioridade tem que ser P0, P1 ou P2")
    item = achar_item(cfg.raiz, ref)
    info = ler_nome(item.name)
    if info is None:
        raise ErroEsteira(f"{item.name} está fora do padrão de nome")
    if info.prioridade == nova:
        return {"item": item.name, "resultado": "já estava assim"}

    def trocar():
        ped = ler_json(item / ARQ_PEDIDO, {}) or {}
        ped["prioridade"] = nova
        escrever_json(item / ARQ_PEDIDO, ped)
        novo = item.parent / (nova + item.name[2:])
        os.replace(item, novo)
        historico(novo, f"[{novo.parent.name}] prioridade {info.prioridade} -> {nova}")
        return novo.name
    ok, r = com_trava_vigia(cfg, trocar)
    if not ok:
        raise ErroEsteira(r)
    return {"item": r, "resultado": f"prioridade {nova}"}
