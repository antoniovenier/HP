"""pedido.json: esquema, regras de conteúdo e criação do item em 01_pedidos.

Campos obrigatórios (depois de `normalizar_pedido`):
  id, canal, tipo, prioridade, titulo, redes, horario_alvo, dublar,
  narrar_toque_hp, observacoes, credito, fonte_url (ou null), arquivos (lista)
Opcionais: slug, legenda_post, hashtags, texto (threads_texto/estáticos),
  roteiro_narracao {abertura, trecho, fecho}, corte {inicio, fim},
  capa_tempo, fonte_oficial (futebol), fonte_propria, legendar, laminas.
"""
from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path

from hpbase import FUSO, agora_iso, escrever_json, garantir, ler_json, obter_logger

from . import pedido_pc
from .constantes import (ARQ_PEDIDO, CANAIS, CANAIS_COM_VOZ, CANAIS_PINTEREST,
                         PEDIDOS, PRIORIDADES, REDES, TIPOS, TIPOS_ESTATICOS)
from .erros import PedidoInvalido
from .pastas import (existe_em_alguma_etapa, historico, montar_nome,
                     slugificar)

RX_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.\-]*$")
RX_MOEDA = re.compile(r"(R\$|US\$|U\$|€|£)\s?\d|\$\s?\d")
AVISO_VALORES = "Valores aproximados"
PALAVRAS_VAZAMENTO = ("vazad", "vazament", "leak")
LIMITE_THREADS = 500
LIMITE_HASHTAGS = 30


def ler_horario(valor) -> datetime:
    """'2026-09-30T18:30:00-03:00', '2026-09-30 18:30'... -> hora de Brasília."""
    if isinstance(valor, datetime):
        dt = valor
    else:
        dt = datetime.fromisoformat(str(valor).strip().replace("Z", "+00:00"))
    if dt.tzinfo is None:
        return dt.replace(tzinfo=FUSO)
    return dt.astimezone(FUSO)


def fonte_externa(p: dict) -> bool:
    """Há fonte de outra pessoa/empresa? (então o crédito é obrigatório)."""
    if p.get("fonte_url"):
        return True
    return bool(p.get("arquivos")) and not p.get("fonte_propria", False)


def eh_estatico(p: dict) -> bool:
    return p.get("tipo") in TIPOS_ESTATICOS


def normalizar_pedido(dados: dict, config_json: dict | None = None) -> dict:
    """Preenche padrões e arruma formatos, sem inventar conteúdo.

    Pedido no formato REAL do PC (§4.5: "tipo": "corte"/"texto", "data" AAAA-MM-DDTHH:MM ou
    prioridade inteira, sem horario_alvo) passa antes por pedido_pc.para_esteira, que converte e
    recusa com ErroParametro (Flow Games, criador não autorizado, vazamento, data inválida).
    `config_json` = dict do config.json do PC (None = lê <Drive>\\06 Projeto\\config.json).
    """
    if pedido_pc.eh_pedido_pc(dados):
        dados = pedido_pc.para_esteira(dados, config=config_json)
    p = dict(dados)
    pri = p.get("prioridade", "P1")
    if isinstance(pri, int) and not isinstance(pri, bool):
        pri = f"P{pri}"
    p["prioridade"] = str(pri).upper().strip()
    for k in ("canal", "tipo"):
        if isinstance(p.get(k), str):
            p[k] = p[k].strip().lower()
    if isinstance(p.get("redes"), str):
        p["redes"] = [r.strip() for r in p["redes"].split(",") if r.strip()]
    if isinstance(p.get("redes"), list):
        p["redes"] = [str(r).strip().lower() for r in p["redes"]]
    p.setdefault("dublar", False)
    p.setdefault("narrar_toque_hp", False)
    p.setdefault("observacoes", "")
    p.setdefault("credito", "")
    p.setdefault("fonte_url", None)
    p.setdefault("arquivos", [])
    if p.get("fonte_url") == "":
        p["fonte_url"] = None
    if isinstance(p.get("arquivos"), str):
        p["arquivos"] = [p["arquivos"]]
    try:
        h = ler_horario(p["horario_alvo"])
        p["horario_alvo"] = h.isoformat(timespec="minutes")
    except Exception:
        pass  # a validação acusa
    if not p.get("id") and p.get("canal") and p.get("titulo") and \
            isinstance(p.get("horario_alvo"), str):
        try:
            h = ler_horario(p["horario_alvo"])
            slug = slugificar(p.get("slug") or p["titulo"])
            p["id"] = montar_nome("P1", h, p["canal"], slug)[3:]
        except Exception:
            pass
    return p


def _textos(p: dict) -> str:
    partes = [p.get("titulo"), p.get("legenda_post"), p.get("texto"),
              p.get("observacoes"), p.get("fonte_url"), p.get("credito")]
    rot = p.get("roteiro_narracao")
    if isinstance(rot, dict):
        partes.extend(str(v) for v in rot.values())
    return " ".join(str(x) for x in partes if x)


def validar_pedido(p: dict) -> list[str]:
    """Devolve a lista de problemas (vazia = pedido ok)."""
    e: list[str] = []
    if not isinstance(p, dict):
        return ["pedido.json tem que ser um objeto JSON"]

    # --- esquema ---------------------------------------------------------
    pid = p.get("id")
    if not isinstance(pid, str) or not RX_ID.match(pid or ""):
        e.append("id obrigatório (letras, números, _ . -)")
    canal = p.get("canal")
    if canal not in CANAIS:
        e.append(f"canal tem que ser um de {', '.join(CANAIS)}")
    tipo = p.get("tipo")
    if tipo not in TIPOS:
        e.append(f"tipo tem que ser um de {', '.join(TIPOS)}")
    if p.get("prioridade") not in PRIORIDADES:
        e.append("prioridade tem que ser P0, P1 ou P2")
    titulo = p.get("titulo")
    if not isinstance(titulo, str) or not titulo.strip():
        e.append("titulo obrigatório")
    elif len(titulo) > 200:
        e.append("titulo passa de 200 caracteres")
    redes = p.get("redes")
    if not isinstance(redes, list) or not redes:
        e.append("redes obrigatório (lista, ex.: [\"instagram\", \"tiktok\"])")
        redes = []
    else:
        ruins = [r for r in redes if r not in REDES]
        if ruins:
            e.append(f"rede desconhecida: {', '.join(map(str, ruins))} "
                     f"(use {', '.join(REDES)})")
        if len(set(redes)) != len(redes):
            e.append("rede repetida em redes")
    try:
        ler_horario(p.get("horario_alvo"))
    except Exception:
        e.append("horario_alvo obrigatório no formato 2026-09-30T18:30:00-03:00")
    for k in ("dublar", "narrar_toque_hp"):
        if not isinstance(p.get(k), bool):
            e.append(f"{k} tem que ser true ou false")
    if not isinstance(p.get("observacoes", ""), str):
        e.append("observacoes tem que ser texto")
    fonte = p.get("fonte_url")
    if fonte is not None and (not isinstance(fonte, str)
                              or not re.match(r"^https?://", fonte)):
        e.append("fonte_url tem que começar com http:// ou https://")
    arqs = p.get("arquivos", [])
    if not isinstance(arqs, list) or not all(isinstance(a, str) and a for a in arqs):
        e.append("arquivos tem que ser uma lista de caminhos")
    if not isinstance(p.get("credito", ""), str):
        e.append("credito tem que ser texto")
    tags = p.get("hashtags")
    if tags is not None:
        if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
            e.append("hashtags tem que ser lista de textos")
        elif len(tags) > LIMITE_HASHTAGS:
            e.append(f"no máximo {LIMITE_HASHTAGS} hashtags (limite do Instagram)")
    corte = p.get("corte")
    if corte is not None:
        try:
            ini = float(corte.get("inicio", 0))
            fim = corte.get("fim")
            if ini < 0 or (fim is not None and float(fim) <= ini):
                raise ValueError
        except Exception:
            e.append("corte tem que ser {\"inicio\": s, \"fim\": s} com fim > inicio")
    capa = p.get("capa_tempo")
    if capa is not None and (isinstance(capa, bool) or not isinstance(capa, (int, float))
                             or capa < 0):
        e.append("capa_tempo tem que ser um número de segundos >= 0")

    if e:
        return e  # sem esquema certo não dá para checar as regras

    dublar = p["dublar"]
    narrar = p["narrar_toque_hp"]
    estatico = tipo in TIPOS_ESTATICOS

    # --- regras de conteúdo (CLAUDE.md) ----------------------------------
    if canal == "futebol" and (dublar or narrar):
        e.append("futebol nunca leva voz sintética: dublar e narrar_toque_hp "
                 "têm que ser false (usa o áudio original do vídeo oficial)")
    elif (dublar or narrar) and canal not in CANAIS_COM_VOZ:
        e.append("dublagem/voz sintética só em gta, destinos, receitas, carros e filmes")
    if estatico and (dublar or narrar):
        e.append(f"{tipo} é estático: não tem dublagem nem narração")
    if narrar:
        rot = p.get("roteiro_narracao")
        if not isinstance(rot, dict) or not str(rot.get("abertura", "")).strip() \
                or not str(rot.get("fecho", "")).strip():
            e.append("narrar_toque_hp=true pede roteiro_narracao com abertura "
                     "(pergunta dos 2 primeiros segundos), trecho e fecho (pergunta)")
        else:
            for parte in ("abertura", "fecho"):
                if not str(rot[parte]).strip().endswith("?"):
                    e.append(f"roteiro_narracao.{parte} tem que ser uma pergunta (terminar com ?)")
    if fonte_externa(p) and not p.get("credito", "").strip():
        e.append("crédito obrigatório quando há fonte externa (fonte_url ou arquivos "
                 "de terceiros); se o material é nosso, use fonte_propria=true")
    if canal == "futebol" and fonte_externa(p) and p.get("fonte_oficial") is not True:
        e.append("futebol: só vídeo/foto oficial de clube, CBF ou liga (nunca "
                 "transmissão de TV) — confirme com fonte_oficial=true")
    textos = _textos(p).lower()
    if "flow games" in textos or "flowgames" in textos:
        e.append("nada do Flow Games")
    if canal == "gta" and any(x in textos for x in PALAVRAS_VAZAMENTO):
        e.append("GTA 6: nada de vazamento (leak)")

    # --- tipo x fonte x redes --------------------------------------------
    if tipo == "reel" and not (p.get("fonte_url") or p.get("arquivos")):
        e.append("reel precisa de fonte_url ou arquivos (o vídeo bruto)")
    if tipo == "threads_texto":
        if redes != ["threads"]:
            e.append("threads_texto só vai para a rede threads")
        texto = p.get("texto")
        if not isinstance(texto, str) or not texto.strip():
            e.append("threads_texto precisa do campo texto")
        elif len(texto) > LIMITE_THREADS:
            e.append(f"texto do Threads passa de {LIMITE_THREADS} caracteres")
        elif RX_MOEDA.search(texto) and AVISO_VALORES.lower() not in texto.lower():
            e.append("valor citado leva 'Valores aproximados…' no texto")
    if tipo == "story" and any(r not in ("instagram", "facebook") for r in redes):
        e.append("story só vai para instagram e facebook")
    if "youtube" in redes and tipo != "reel":
        e.append("youtube só recebe reel (Shorts)")
    if "pinterest" in redes and canal not in CANAIS_PINTEREST:
        e.append("pinterest só em receitas, carros e destinos")
    return e


def validar_ou_erro(p: dict) -> dict:
    erros = validar_pedido(p)
    if erros:
        raise PedidoInvalido(erros)
    return p


def ler_pedido(item: Path) -> dict:
    """Lê e valida o pedido.json do item (erro permanente se inválido)."""
    arq = Path(item) / ARQ_PEDIDO
    if not arq.exists():
        raise PedidoInvalido(f"{ARQ_PEDIDO} não existe em {Path(item).name}")
    try:
        dados = ler_json(arq)
    except Exception as ex:
        raise PedidoInvalido(f"{ARQ_PEDIDO} ilegível: {ex}") from ex
    return validar_ou_erro(normalizar_pedido(dados))


def nome_do_item(p: dict) -> str:
    h = ler_horario(p["horario_alvo"])
    slug = slugificar(p.get("slug") or p["titulo"])
    return montar_nome(p["prioridade"], h, p["canal"], slug)


def criar_pedido(dados: dict, raiz: Path | None = None) -> Path:
    """Cria a pasta do item em 01_pedidos com pedido.json validado.

    A pasta nasce como .criando_<nome> e só ganha o nome final (os.replace)
    quando está completa: se o app cair no meio, o vigia nunca vê pedido
    pela metade.
    """
    from .config import carregar_config  # evita import circular

    raiz = Path(raiz) if raiz else carregar_config().raiz
    p = normalizar_pedido(dados)
    validar_ou_erro(p)
    nome = nome_do_item(p)
    ja = existe_em_alguma_etapa(raiz, nome[3:])
    if ja is not None:
        raise PedidoInvalido(f"já existe um item {ja.name} em {ja.parent.name}")
    pasta = garantir(raiz / PEDIDOS)
    temp = pasta / f".criando_{nome}"
    garantir(temp)
    p.setdefault("criado_em", agora_iso())
    escrever_json(temp / ARQ_PEDIDO, p)
    historico(temp, f"[{PEDIDOS}] pedido criado ({p['tipo']}, {p['prioridade']}, "
                    f"redes: {', '.join(p['redes'])})")
    final = pasta / nome
    os.replace(temp, final)
    obter_logger("esteira").info("pedido criado: %s", nome)
    return final
