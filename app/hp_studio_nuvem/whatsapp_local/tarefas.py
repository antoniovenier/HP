"""Monta os textos (montagem.py) e põe na fila, sem nunca duplicar.

O id de cada mensagem é determinístico (tipo + post/dia + grupo): se o
mesmo aviso/resumo já está na fila, já foi enviado, rejeitado, deu erro ou
passou pela sombra, ele NÃO entra de novo. Assim dá para rodar
`montar-no-ar` a cada minuto sem medo.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

from hpbase import obter_logger

from .config import Config, candidatos_agendados, candidatos_metricas, nfc
from .fila import Fila
from .montagem import (carregar_agendados, carregar_metricas, carregar_modelo_aviso,
                       chave_post, id_mensagem, mensagem_fila, montar_no_ar,
                       montar_resumo_dia, montar_resumo_sabado, posts_prontos)


def grupo_do_post(post: dict, cfg: Config, grupo_forcado: str | None = None) -> str:
    """--grupo da linha de comando > grupo do post > grupo_por_canal > padrão."""
    if grupo_forcado:
        return nfc(grupo_forcado)
    if post.get("grupo"):
        return nfc(post["grupo"])
    mapa = {nfc(k): v for k, v in (cfg.grupo_por_canal or {}).items()}
    return nfc(mapa.get(nfc(post.get("canal")), cfg.grupo_padrao))


def _entregar(msg: dict, fila: Fila, so_mostrar: bool) -> dict:
    if so_mostrar:
        return {**msg, "_situacao": "só mostrar"}
    if fila.ja_existe(msg["id"]):
        return {**msg, "_situacao": "já existia"}
    fila.enfileirar(msg)
    obter_logger("whatsapp").info("enfileirada: id=%s tipo=%s grupo=%s tamanho=%d",
                                  msg["id"], msg["tipo"], msg["grupo"], len(msg["texto"]))
    return {**msg, "_situacao": "enfileirada"}


def enfileirar_no_ar(agendados: Path, cfg: Config, agora: datetime, *,
                     grupo: str | None = None, modelo: Path | None = None,
                     janela_horas: float | None = None, so_mostrar: bool = False,
                     fila: Fila | None = None) -> list[dict]:
    fila = fila or Fila()
    texto_modelo, _origem = carregar_modelo_aviso(modelo)
    janela = cfg.janela_no_ar_horas if janela_horas is None else janela_horas
    saida = []
    for post in posts_prontos(carregar_agendados(agendados), agora, janela):
        g = grupo_do_post(post, cfg, grupo)
        msg = mensagem_fila("no_ar", g, montar_no_ar(post, texto_modelo),
                            id_mensagem("no_ar", chave_post(post), g), agora)
        saida.append(_entregar(msg, fila, so_mostrar))
    return saida


def _metricas(cfg: Config, caminho: Path | None):
    return carregar_metricas(caminho or (Path(cfg.arquivo_metricas) if cfg.arquivo_metricas else None),
                             candidatos_metricas())


def enfileirar_resumo_dia(cfg: Config, agora: datetime, *, dia: date | None = None,
                          metricas: Path | None = None, grupo: str | None = None,
                          so_mostrar: bool = False, fila: Fila | None = None) -> dict | None:
    """Resumo do dia (padrão: ontem). None = sem métricas desse dia."""
    dia = dia or (agora.date() - timedelta(days=1))
    dados = _metricas(cfg, metricas)
    texto = montar_resumo_dia(dados, dia) if dados else None
    if not texto:
        return None
    g = nfc(grupo or cfg.grupo_padrao)
    msg = mensagem_fila("resumo_dia", g, texto, id_mensagem("resumo_dia", dia.isoformat(), g), agora)
    return _entregar(msg, fila or Fila(), so_mostrar)


def enfileirar_resumo_sabado(cfg: Config, agora: datetime, *, sabado: date | None = None,
                             metricas: Path | None = None, grupo: str | None = None,
                             so_mostrar: bool = False, fila: Fila | None = None) -> dict | None:
    from .montagem import sabado_de_referencia
    sabado = sabado or sabado_de_referencia(agora.date())
    dados = _metricas(cfg, metricas)
    texto = montar_resumo_sabado(dados, sabado) if dados else None
    if not texto:
        return None
    g = nfc(grupo or cfg.grupo_padrao)
    msg = mensagem_fila("resumo_sabado", g, texto,
                        id_mensagem("resumo_sabado", sabado.isoformat(), g), agora)
    return _entregar(msg, fila or Fila(), so_mostrar)


def resolver_agendados(cfg: Config) -> Path | None:
    """cfg.arquivo_agendados: caminho, "auto" (procura nos lugares de sempre) ou None."""
    valor = cfg.arquivo_agendados
    if not valor:
        return None
    cands = candidatos_agendados() if str(valor).lower() == "auto" else [Path(valor)]
    return next((p for p in cands if p.is_file()), None)


def tarefas_automaticas(cfg: Config, agora: datetime, fila: Fila | None = None) -> int:
    """O que o vigia monta sozinho, se estiver ligado na config.json:
    - arquivo_agendados → aviso "no ar" dos posts que entraram no ar;
    - hora_resumo_dia ("08:00") → resumo de ontem, depois desse horário;
    - hora_resumo_sabado ("10:00") → resumo da semana, no sábado.
    Devolve quantas mensagens novas entraram na fila."""
    fila = fila or Fila()
    novas = 0
    lg = obter_logger("whatsapp")
    hhmm = agora.strftime("%H:%M")
    try:
        arq = resolver_agendados(cfg)
        if arq:
            novas += sum(1 for m in enfileirar_no_ar(arq, cfg, agora, fila=fila)
                         if m["_situacao"] == "enfileirada")
        if cfg.hora_resumo_dia and hhmm >= cfg.hora_resumo_dia:
            m = enfileirar_resumo_dia(cfg, agora, fila=fila)
            novas += bool(m and m["_situacao"] == "enfileirada")
        if cfg.hora_resumo_sabado and agora.weekday() == 5 and hhmm >= cfg.hora_resumo_sabado:
            m = enfileirar_resumo_sabado(cfg, agora, fila=fila)
            novas += bool(m and m["_situacao"] == "enfileirada")
    except Exception as e:  # montagem nunca derruba o envio
        lg.error("tarefas automáticas falharam: %s: %s", type(e).__name__, e)
    return novas
