"""pedido_pc — o pedido REAL do hp_studio\\esteira\\pedido.py do PC (§4.5) na esteira da nuvem.

O que faz: aceita o pedido.json que o Claude larga em 01_pedidos no formato do PC
  Corte:  {"tipo": "corte", "canal": "gta", "prioridade": 2, "data": "2026-09-30T18:30",
           "video": "<id do YouTube>" (ou "link": "https://..." ou "arquivo": "H:\\...\\trecho.mp4"),
           "streamer": "davyjones", "inicio": "03:26", "fim": "04:04", "gancho", "titulo", "legenda",
           "redes": [...]}  + opcionais do plano (corte, trechos, zoom, cobrir, bipes, tarjas, fade_saida,
           dublar, n) e outros (idioma "en", hashtags, textos {rede: texto}, correcoes, apelido)
  Estáticos (pulam o vídeo): "carrossel" (spec, tiktok), "story" (arte, opcoes), "texto" (texto)
e faz duas coisas:
  (a) para_esteira(pedido, config)  -> o pedido.json que esteira.pedido.normalizar_pedido entende
      (tipo reel/carrossel/story/threads_texto, prioridade P0/P1/P2, horario_alvo ISO, fonte_url, credito,
      dublar, corte {inicio, fim}, slug...). normalizar_pedido chama isto sozinho quando reconhece o formato.
  (b) para_post_json(pedido)        -> o post.json do contrato com o `publicar` do PC (canal, tipo, quando
      "AAAA-MM-DD HH:MM", titulo, legenda, arquivos, capa, tags, dublado, redes com apelidos).

Recusa com ErroParametro (mensagem em português, como o normalizar() do PC):
  Flow Games (flow games|flowgames|flow podcast|flowpodcast|flow_games em streamer, credito, link, gancho,
  titulo), criador sem "autorizado": true no config.json, vazamento de GTA, data inválida, tipo/rede/
  prioridade desconhecidos, corte sem vídeo.

Uso:
    from esteira import pedido_pc
    p = pedido_pc.para_esteira(pedido, config=config_json)   # dict pronto para normalizar_pedido/criar_pedido
    post = pedido_pc.para_post_json(pedido)                   # post.json (§4.5)
    pedido_pc.nome_da_pasta(pedido)                           # P2_2026-09-30_1830_gta_<apelido>  (ASCII)
    pedido_pc.ler_pedido_pc(caminho, agora=..., mtime=...)    # None enquanto o .json solto não parou 2 s
    python -m esteira ...                                     # a esteira aceita o formato real sem flag

Regras:
- Constantes reais do PC: TIPOS, REDES, REDES_PADRAO, ARTES_STORY, CAMPOS_DO_PLANO (não invente outras).
- config.json: injete `config=` (dict) ou ele lê <Drive>\\06 Projeto\\config.json (a variável HP_CONFIG_PC
  troca o caminho). SEM config nenhum criador está autorizado: corte é recusado; estáticos passam.
- Nome da pasta: P<n>_AAAA-MM-DD_HHMM_<canal(até 20)>_<apelido(até 40)>, tudo ASCII sem espaço
  (apelido = "apelido" do pedido, senão slug do gancho/título).
- Nada roda, nada lê rede; relógio (`agora`) e data de modificação (`mtime`) são injetáveis.
"""
from __future__ import annotations

import os
import re
import time
from datetime import datetime
from pathlib import Path

from hpbase import FUSO, ler_json, raiz_drive

from . import comandos_pc as cp
from .constantes import CANAIS
from .erros import PedidoInvalido
from .pastas import montar_nome, slugificar

# --- constantes REAIS do hp_studio\esteira\pedido.py do PC (§4.5) -------------------------
TIPOS = ("corte", "carrossel", "story", "texto")
REDES = ("instagram", "facebook", "threads", "youtube", "tiktok")
REDES_PADRAO = {
    "corte": list(REDES),
    "carrossel": ["instagram", "facebook"],
    "story": ["instagram", "facebook"],
    "texto": ["threads"],
}
ARTES_STORY = ("novo_video", "contagem", "noticia", "interativo")
CAMPOS_DO_PLANO = ("corte", "trechos", "zoom", "cobrir", "bipes", "tarjas", "fade_saida", "dublar", "n")
PRIORIDADES = (0, 1, 2)          # 0 urgente/ao vivo (faixa expressa), 1 do dia, 2 programado (padrão)
PRIORIDADE_PADRAO = 2
FORMATO_DATA = "AAAA-MM-DDTHH:MM"
PARADO_SEG = 2.0                 # pedido solto só é lido depois de 2 s parado (nada meio gravado)
RX_FLOW = re.compile(r"flow games|flowgames|flow podcast|flowpodcast|flow_games", re.I)
CAMPOS_FLOW = ("streamer", "credito", "link", "gancho", "titulo")
PALAVRAS_VAZAMENTO = ("vazad", "vazament", "leak")
CANAL_PADRAO = "gta"             # SUPOSIÇÃO: o config.json/esteira do PC é o do GTA

# --- post.json (hp_studio\publicar\post.py do PC) -------------------------------------------
TIPOS_POST = ("reel", "carrossel", "feed", "story", "texto", "video", "comunidade")
REDES_POST = ("instagram", "facebook", "threads", "youtube", "tiktok", "pinterest", "youtube_comunidade")
APELIDOS_REDE = {"ig": "instagram", "fb": "facebook", "th": "threads", "yt": "youtube",
                 "shorts": "youtube", "tt": "tiktok", "pin": "pinterest",
                 "comunidade": "youtube_comunidade"}
APELIDOS_TIPO = {"short": "reel", "foto": "feed", "longo": "video"}
TIPO_INTERNO = {"corte": "reel", "carrossel": "carrossel", "story": "story", "texto": "threads_texto"}
TIPO_POST = {"corte": "reel", "carrossel": "carrossel", "story": "story", "texto": "texto",
             "reel": "reel", "threads_texto": "texto", "estatico": "feed"}
ARQUIVOS_POST_PADRAO = {"corte": ["final.mp4"]}      # SUPOSIÇÃO: docstring do post.py ("final.mp4")
CAPA_POST_PADRAO = {"corte": "capa.jpg"}

# só aqui: o caminho do PC (a variável HP_CONFIG_PC troca; HP_DRIVE muda a raiz)
CONFIG_PC = raiz_drive() / "06 Projeto" / "config.json"   # valor na importação; use caminho_config_pc()

_RX_DATA = re.compile(r"^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::(\d{2}))?$")
_RX_HASHTAG = re.compile(r"#(\w+)")


class ErroParametro(PedidoInvalido):
    """Pedido mal feito, com o motivo em português (igual ao ErroParametro do pedido.py do PC).
    É um PedidoInvalido: a esteira manda o item para 99_erros sem tentar de novo."""

    def __init__(self, mensagem: str):
        self.erros = [str(mensagem)]
        ValueError.__init__(self, str(mensagem))


# --- reconhecer e ler -------------------------------------------------------------------------
def eh_pedido_pc(dados) -> bool:
    """O dict está no formato do PC? ("tipo": corte/texto, ou "data"/prioridade inteira sem horario_alvo)."""
    if not isinstance(dados, dict):
        return False
    tipo = str(dados.get("tipo") or "").strip().lower()
    if tipo in ("corte", "texto"):
        return True
    if "horario_alvo" in dados:
        return False
    pri = dados.get("prioridade")
    return "data" in dados or (isinstance(pri, int) and not isinstance(pri, bool))


def caminho_config_pc() -> Path:
    env = os.environ.get("HP_CONFIG_PC")
    return Path(env) if env else raiz_drive() / "06 Projeto" / "config.json"


def ler_config_pc(caminho=None) -> dict | None:
    """config.json do PC (06 Projeto\\config.json) ou None se não existe."""
    p = Path(caminho) if caminho else caminho_config_pc()
    if not p.is_file():
        return None
    try:
        dados = ler_json(p)
    except ValueError as e:
        raise ErroParametro(f"config.json ilegível em {p}: {e}") from e
    return dados if isinstance(dados, dict) else None


def _epoch(valor) -> float:
    if valor is None:
        return time.time()
    if isinstance(valor, datetime):
        return valor.timestamp()
    return float(valor)


def ler_pedido_pc(caminho, agora=None, mtime=None, parado_seg: float = PARADO_SEG) -> dict | None:
    """Lê um pedido solto (.json em 01_pedidos) SÓ se ele está parado há >= 2 s (nada meio gravado).

    Devolve None enquanto o arquivo ainda é recente. `agora` (datetime ou epoch) e `mtime` (epoch,
    datetime ou função(caminho) -> epoch) são injetáveis; sem eles usa o relógio e o disco.
    """
    p = Path(caminho)
    if not p.is_file():
        raise ErroParametro(f"pedido não encontrado: {p}")
    if callable(mtime):
        m = mtime(p)
    elif mtime is None:
        m = p.stat().st_mtime
    else:
        m = mtime
    if _epoch(agora) - _epoch(m) < float(parado_seg):
        return None
    try:
        dados = ler_json(p)
    except ValueError as e:
        raise ErroParametro(f"pedido {p.name} ilegível (JSON quebrado): {e}") from e
    if not isinstance(dados, dict):
        raise ErroParametro(f"pedido {p.name} tem que ser um objeto JSON")
    return dados


# --- pedaços -----------------------------------------------------------------------------------
def ler_data(valor) -> datetime:
    """'2026-09-30T18:30' -> datetime (hora de Brasília, sem fuso). Aceita espaço no lugar do T e
    segundos; qualquer outra coisa é ErroParametro."""
    if isinstance(valor, datetime):
        return valor.replace(tzinfo=None) if valor.tzinfo is None else valor.astimezone(FUSO).replace(tzinfo=None)
    txt = str(valor or "").strip()
    m = _RX_DATA.match(txt)
    if not m:
        raise ErroParametro(f"data inválida: use {FORMATO_DATA} (veio '{txt or 'vazio'}')")
    try:
        a, me, d, h, mi, s = (int(x or 0) for x in m.groups())
        return datetime(a, me, d, h, mi, s)
    except ValueError as e:
        raise ErroParametro(f"data inválida: {txt} ({e}); use {FORMATO_DATA}") from e


def tipo_pc(valor) -> str:
    t = str(valor or "").strip().lower()
    if t not in TIPOS:
        raise ErroParametro(f"tipo tem que ser um de {', '.join(TIPOS)} (veio '{t or 'vazio'}')")
    return t


def prioridade_pc(valor) -> int:
    """0, 1, 2 (padrão 2). Aceita '1' e 'P1' por tolerância."""
    if valor is None or valor == "":
        return PRIORIDADE_PADRAO
    if isinstance(valor, bool):
        raise ErroParametro("prioridade tem que ser 0, 1 ou 2")
    txt = str(valor).strip().upper()
    if txt.startswith("P"):
        txt = txt[1:]
    try:
        n = int(txt)
    except ValueError:
        raise ErroParametro(f"prioridade tem que ser 0, 1 ou 2 (veio '{valor}')") from None
    if n not in PRIORIDADES:
        raise ErroParametro(f"prioridade tem que ser 0, 1 ou 2 (veio {n})")
    return n


def normalizar_rede(nome) -> str:
    """'ig' -> 'instagram', 'shorts' -> 'youtube'... (apelidos do post.py do PC)."""
    r = str(nome or "").strip().lower()
    r = APELIDOS_REDE.get(r, r)
    if r not in REDES_POST:
        raise ErroParametro(f"rede desconhecida: '{nome}' (use {', '.join(REDES)} ou os apelidos "
                            f"{', '.join(APELIDOS_REDE)})")
    return r


def normalizar_tipo_post(tipo) -> str:
    """'short' -> 'reel', 'foto' -> 'feed', 'longo' -> 'video'; corte -> reel; threads_texto -> texto."""
    t = str(tipo or "").strip().lower()
    t = APELIDOS_TIPO.get(t, TIPO_POST.get(t, t))
    if t not in TIPOS_POST:
        raise ErroParametro(f"tipo de post desconhecido: '{tipo}' (use {', '.join(TIPOS_POST)})")
    return t


def _lista(valor) -> list:
    if valor is None or valor == "":
        return []
    if isinstance(valor, str):
        return [x.strip() for x in re.split(r"[,\s]+", valor) if x.strip()]
    return [str(x).strip() for x in valor if str(x).strip()]


def redes_do_pedido(pedido: dict, tipo: str | None = None) -> list[str]:
    """Redes do pedido (ou as REDES_PADRAO do tipo), já sem apelidos e só as que o PC aceita."""
    tipo = tipo or tipo_pc(pedido.get("tipo"))
    vindas = _lista(pedido.get("redes"))
    if not vindas:
        return list(REDES_PADRAO[tipo])
    saida: list[str] = []
    for r in vindas:
        n = normalizar_rede(r)
        if n not in REDES:
            raise ErroParametro(f"rede '{r}' não vale num pedido (o PC aceita {', '.join(REDES)})")
        if n not in saida:
            saida.append(n)
    return saida


def hashtags_do_pedido(pedido: dict) -> list[str]:
    """['#gta6', 'gtavi'] -> ['gta6', 'gtavi']; texto '#a #b' também vale."""
    tags = pedido.get("hashtags")
    if isinstance(tags, str):
        tags = _RX_HASHTAG.findall(tags) or _lista(tags)
    return [str(t).strip().lstrip("#") for t in (tags or []) if str(t).strip().lstrip("#")]


def _primeira_linha(texto, maximo: int = 100) -> str:
    linha = str(texto or "").strip().splitlines()
    return (linha[0].strip() if linha else "")[:maximo]


def titulo_do_pedido(pedido: dict, tipo: str | None = None) -> str:
    """titulo, senão gancho, senão a 1ª linha da legenda/texto, senão '<tipo> <data>'."""
    tipo = tipo or str(pedido.get("tipo") or "").lower()
    spec = pedido.get("spec") if isinstance(pedido.get("spec"), dict) else {}
    opcoes = pedido.get("opcoes") if isinstance(pedido.get("opcoes"), dict) else {}
    for cand in (pedido.get("titulo"), pedido.get("gancho"), opcoes.get("titulo"),
                 _primeira_linha(pedido.get("legenda")), _primeira_linha(pedido.get("texto")),
                 spec.get("titulo"), spec.get("tema")):
        if cand and str(cand).strip():
            return str(cand).strip()
    return f"{tipo} {pedido.get('data') or ''}".strip()


def apelido_do_pedido(pedido: dict) -> str:
    """Slug ASCII (até 40) do "apelido", senão do gancho/título."""
    if pedido.get("apelido"):
        return slugificar(pedido["apelido"], 40)
    if pedido.get("gancho"):
        return slugificar(pedido["gancho"], 40)
    return slugificar(titulo_do_pedido(pedido), 40)


def nome_da_pasta(pedido: dict) -> str:
    """P<n>_AAAA-MM-DD_HHMM_<canal(até 20)>_<apelido(até 40)>, tudo ASCII sem espaço."""
    pri = prioridade_pc(pedido.get("prioridade"))
    h = ler_data(pedido.get("data"))
    canal = slugificar(pedido.get("canal") or CANAL_PADRAO, 20)
    return montar_nome(f"P{pri}", h, canal, apelido_do_pedido(pedido))


# --- regras de conteúdo (CLAUDE.md + pedido.py do PC) -------------------------------------------
def conferir_flow_games(pedido: dict) -> None:
    for campo in CAMPOS_FLOW:
        v = pedido.get(campo)
        if v and RX_FLOW.search(str(v)):
            raise ErroParametro(f"nada do Flow Games (achei em '{campo}': {str(v)[:60]})")


def conferir_vazamento(pedido: dict, canal: str) -> None:
    if canal != "gta":
        return
    for campo in ("gancho", "titulo", "legenda", "texto", "link", "obs", "observacoes"):
        v = str(pedido.get(campo) or "").lower()
        for palavra in PALAVRAS_VAZAMENTO:
            if palavra in v:
                raise ErroParametro(f"GTA 6: nada de vazamento (leak) — achei '{palavra}' em '{campo}'")


def criador_autorizado(config: dict | None, id_streamer) -> dict:
    """Devolve o criador do config.json; ErroParametro se não existe ou não tem autorizado: true."""
    alvo = str(id_streamer or "").strip()
    if not alvo:
        raise ErroParametro("corte precisa de 'streamer' (id do criador no config.json)")
    if config is None:
        raise ErroParametro(f"config.json não encontrado em {caminho_config_pc()}: não dá para conferir "
                            f"se o criador '{alvo}' está autorizado")
    s = cp.criador_do_config(config, alvo)
    if s is None:
        raise ErroParametro(f"criador '{alvo}' não está no config.json (streamers): peça autorização "
                            "e cadastre antes de cortar")
    if s.get("autorizado") is not True:
        raise ErroParametro(f"criador '{alvo}' sem \"autorizado\": true no config.json — não corta")
    return s


def credito_do_pedido(pedido: dict, config: dict | None) -> str:
    """credito do pedido, senão o do criador no config.json, senão @<streamer>."""
    if pedido.get("credito"):
        return str(pedido["credito"]).strip()
    s = cp.criador_do_config(config, pedido.get("streamer")) or {}
    if s.get("credito"):
        return str(s["credito"]).strip()
    return f"@{pedido['streamer']}" if pedido.get("streamer") else ""


def dublar_do_pedido(pedido: dict, config: dict | None) -> bool:
    """"dublar" explícito vale; senão gringo = "idioma": "en" no pedido ou criador "en" no config."""
    if isinstance(pedido.get("dublar"), bool):
        return pedido["dublar"]
    if str(pedido.get("idioma") or "").strip().lower() == "en":
        return True
    return cp.dublar_por_padrao(pedido, config)


# --- validação do formato do PC --------------------------------------------------------------------
def validar_pc(pedido: dict, config: dict | None = None, conferir_criador: bool = True) -> dict:
    """Confere o pedido no formato do PC e devolve uma cópia normalizada (tipo, canal, prioridade int,
    data canônica, redes, hashtags). Qualquer problema vira ErroParametro em português."""
    if not isinstance(pedido, dict):
        raise ErroParametro("pedido tem que ser um objeto JSON")
    v = dict(pedido)
    tipo = tipo_pc(v.get("tipo"))
    canal = str(v.get("canal") or CANAL_PADRAO).strip().lower()
    if canal not in CANAIS:
        raise ErroParametro(f"canal tem que ser um de {', '.join(CANAIS)} (veio '{canal}')")
    pri = prioridade_pc(v.get("prioridade"))
    if "data" not in v or v.get("data") in (None, ""):
        raise ErroParametro(f"data obrigatória no formato {FORMATO_DATA}")
    h = ler_data(v["data"])
    conferir_flow_games(v)
    conferir_vazamento(v, canal)
    redes = redes_do_pedido(v, tipo)
    if tipo == "corte":
        fontes = [k for k in ("video", "link", "arquivo") if v.get(k)]
        if not fontes:
            raise ErroParametro("corte precisa de 'video' (id do YouTube), 'link' ou 'arquivo'")
        if v.get("link") and not re.match(r"^https?://", str(v["link"]).strip()):
            raise ErroParametro(f"link tem que começar com http:// ou https:// (veio '{v['link']}')")
        if not v.get("arquivo"):
            for campo in ("inicio", "fim"):
                if v.get(campo) in (None, ""):
                    raise ErroParametro(f"corte precisa de '{campo}' (MM:SS) para baixar só o trecho")
            try:
                if cp.segundos(v["fim"]) <= cp.segundos(v["inicio"]):
                    raise ErroParametro(f"fim ({v['fim']}) tem que ser depois do inicio ({v['inicio']})")
            except ValueError as e:
                raise ErroParametro(f"inicio/fim inválidos: {e}") from e
        if conferir_criador:
            criador_autorizado(config, v.get("streamer"))
    elif v.get("streamer") and conferir_criador:
        criador_autorizado(config, v.get("streamer"))
    if tipo == "story":
        arte = str(v.get("arte") or "").strip().lower()
        if arte not in ARTES_STORY:
            raise ErroParametro(f"story precisa de 'arte' igual a um de {', '.join(ARTES_STORY)} "
                                f"(veio '{arte or 'vazio'}')")
        v["arte"] = arte
    if tipo == "texto" and not str(v.get("texto") or "").strip():
        raise ErroParametro("texto precisa do campo 'texto' (o post do Threads)")
    if tipo == "carrossel" and not v.get("spec"):
        raise ErroParametro("carrossel precisa de 'spec' (o JSON do estaticos.py carrossel)")
    corte = v.get("corte")
    if corte is not None:
        jan = cp.janela(v)
        if jan is None or jan[1] <= jan[0]:
            raise ErroParametro("corte tem que ser [inicio, fim] em segundos com fim > inicio")
    v.update({"tipo": tipo, "canal": canal, "prioridade": pri, "data": h.strftime("%Y-%m-%dT%H:%M"),
              "redes": redes, "hashtags": hashtags_do_pedido(v)})
    return v


# --- (a) modelo interno da esteira ------------------------------------------------------------------
def para_esteira(pedido: dict, config: dict | None = None) -> dict:
    """Pedido do PC -> dict que esteira.pedido.normalizar_pedido/validar_pedido entendem.

    Mantém os campos do PC que os comandos reais usam (streamer, inicio, fim, video, gancho, trechos,
    zoom, cobrir, bipes, tarjas, fade_saida, idioma, textos, correcoes, spec, tiktok, arte, opcoes).
    `config` = dict do config.json (None = lê o do PC; sem ele nenhum criador é autorizado).
    """
    if config is None:
        config = ler_config_pc()
    v = validar_pc(pedido, config)
    tipo = v["tipo"]
    h = ler_data(v["data"])
    p = {k: val for k, val in v.items()
         if k not in ("tipo", "prioridade", "data", "redes", "link", "arquivo", "legenda", "apelido",
                      "n", "obs")}
    p.update({
        "formato_origem": "pc",
        "canal": v["canal"],
        "tipo": TIPO_INTERNO[tipo],
        "prioridade": f"P{v['prioridade']}",
        "horario_alvo": h.replace(tzinfo=FUSO).isoformat(timespec="minutes"),
        "titulo": titulo_do_pedido(v, tipo)[:200],
        "slug": apelido_do_pedido(v),
        "redes": list(v["redes"]),
        "observacoes": str(v.get("obs") or v.get("observacoes") or ""),
        "narrar_toque_hp": False,
        "fonte_url": None,
        "arquivos": [],
        "credito": "",
        "dublar": False,
    })
    if v.get("legenda"):
        p["legenda_post"] = str(v["legenda"])
    if not v.get("hashtags"):
        p.pop("hashtags", None)
    if "n" in v:
        p["lote_n"] = v["n"]
    if tipo == "corte":
        if v.get("arquivo"):
            p["arquivos"] = [str(v["arquivo"])]
        else:
            p["fonte_url"] = str(v.get("link") or "").strip() or cp.url_do_pedido(v)
        p["credito"] = credito_do_pedido(v, config)
        p["dublar"] = dublar_do_pedido(v, config)
        jan = cp.janela(v)
        if jan:
            p["corte"] = {"inicio": jan[0], "fim": jan[1]}
        toque = v.get("toque_hp") if isinstance(v.get("toque_hp"), dict) else None
        if toque:
            p["narrar_toque_hp"] = True
            p["roteiro_narracao"] = {"abertura": toque.get("pergunta_abertura"),
                                     "trecho": toque.get("narracao"), "fecho": toque.get("fecho")}
    else:
        p.pop("corte", None)
        p["dublar"] = False
        if v.get("credito"):
            p["credito"] = str(v["credito"]).strip()
        if tipo == "story":
            p["modelo"] = v["arte"]                 # o DesignerScript usa "modelo" + "opcoes"
            if isinstance(v.get("opcoes"), dict):
                p["opcoes"] = dict(v["opcoes"])
        if tipo == "texto":
            p["texto"] = str(v["texto"])
    if isinstance(v.get("textos"), dict):
        p["textos"] = {normalizar_rede(k): str(t) for k, t in v["textos"].items()}
    return p


# --- (b) post.json ---------------------------------------------------------------------------------
def _quando(pedido: dict) -> str:
    valor = pedido.get("data") if "data" in pedido else pedido.get("horario_alvo")
    if valor is None and "horario_alvo" in pedido:
        valor = pedido["horario_alvo"]
    if isinstance(valor, str) and re.search(r"[+-]\d{2}:\d{2}$|Z$", valor.strip()):
        dt = datetime.fromisoformat(valor.strip().replace("Z", "+00:00")).astimezone(FUSO)
        return dt.strftime("%Y-%m-%d %H:%M")
    return ler_data(valor).strftime("%Y-%m-%d %H:%M")


def para_post_json(pedido: dict, arquivos=None, capa=None, config: dict | None = None) -> dict:
    """post.json do contrato esteira -> publicar do PC (§4.5).

    Aceita o pedido do PC ou o interno já convertido (tipo reel/threads_texto, horario_alvo).
    `arquivos`/`capa` sobrepõem o padrão (corte: ["final.mp4"] e "capa.jpg"; estáticos: o que vier em
    "arquivo"/"arquivos", senão lista vazia — quem grava o post.json na etapa 06 completa com a arte).
    "textos" {rede: texto} vira "redes" como objeto ({"threads": {"legenda": "..."}}).
    """
    if eh_pedido_pc(pedido):
        v = validar_pc(pedido, config, conferir_criador=False)
        tipo_pc_ = v["tipo"]
        redes = list(v["redes"])
        legenda = v.get("texto") if tipo_pc_ == "texto" else v.get("legenda")
        dublado = dublar_do_pedido(v, config) if tipo_pc_ == "corte" else False
    else:
        v = dict(pedido)
        if not v.get("tipo"):
            raise ErroParametro("pedido sem 'tipo'")
        tipo_pc_ = {"reel": "corte", "threads_texto": "texto"}.get(str(v["tipo"]).lower(),
                                                                   str(v["tipo"]).lower())
        redes = [normalizar_rede(r) for r in _lista(v.get("redes"))]
        legenda = v.get("texto") if tipo_pc_ == "texto" else (v.get("legenda_post") or v.get("legenda"))
        dublado = bool(v.get("dublar"))
    tipo = normalizar_tipo_post(v["tipo"])
    canal = str(v.get("canal") or CANAL_PADRAO).strip().lower()
    if canal not in CANAIS:
        raise ErroParametro(f"canal tem que ser um de {', '.join(CANAIS)} (veio '{canal}')")
    legenda = str(legenda or "")
    tags = hashtags_do_pedido(v) or _RX_HASHTAG.findall(legenda)
    if arquivos is None:
        if v.get("arquivos"):
            arquivos = [str(a) for a in v["arquivos"]]
        elif v.get("arquivo") and tipo_pc_ != "corte":
            arquivos = [str(v["arquivo"])]
        else:
            arquivos = list(ARQUIVOS_POST_PADRAO.get(tipo_pc_, []))
    if capa is None:
        capa = CAPA_POST_PADRAO.get(tipo_pc_)
    post = {
        "canal": canal,
        "tipo": tipo,
        "quando": _quando(v),
        "titulo": titulo_do_pedido(v, tipo_pc_),
        "legenda": legenda,
        "arquivos": [str(a) for a in arquivos],
        "tags": tags,
        "dublado": bool(dublado),
        "redes": redes,
    }
    if capa:
        post["capa"] = str(capa)
    textos = v.get("textos") if isinstance(v.get("textos"), dict) else None
    if textos:
        por_rede = {normalizar_rede(k): str(t) for k, t in textos.items()}
        post["redes"] = {r: ({"legenda": por_rede[r]} if r in por_rede else {}) for r in redes}
    return post
