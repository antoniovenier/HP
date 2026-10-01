"""verificar_fontes — prova que cada fonte do radar (RSS/Atom e canal de YouTube) vale.

O que faz: refaz a verificação das fontes candidatas do `radar_hp.py` (Seção 4.10) antes de
elas entrarem no `07 Canais\\radar\\<canal>.json`, e aplica as regras de classificação
(`oficial`, `video_reutilizavel`, Flow Games nunca entra). Nada aqui inventa id nem URL:
o que não passa vai para `descartadas` com o motivo, em português.

Uso (CLI, na pasta do projeto):
    python radar_fontes\\verificar_fontes.py verificar radar_fontes\\futebol_fontes_novas.json [--gravar] [--json]
    python radar_fontes\\verificar_fontes.py canal @Flamengo [--id UCxxxx] [--nome "Flamengo"] [--json]
    python radar_fontes\\verificar_fontes.py rss https://www.ign.com/rss/articles/feed [--json]
    python radar_fontes\\verificar_fontes.py candidatos candidatos.txt [--canal futebol] [--json]
        (uma linha por candidato: "tipo|nome|url|oficial|reutilizavel[|channel_id[|peso]]")
Códigos de saída: 0 = ok · 1 = erro ou alguma fonte não passou.

Uso (de outro módulo, sem rede — o transporte é injetado):
    from verificar_fontes import verificar_rss, verificar_canal_youtube, verificar_arquivo
    r = verificar_rss(url, transporte, hoje)              # r["ok"], r["motivo"], r["titulo"], r["mais_novo"]
    c = verificar_canal_youtube("@Flamengo", "UC...", transporte, nome="Flamengo")
    dados = verificar_arquivo(caminho, transporte, hoje)  # JSON de 4.10 + verificado_em/evidencia/verificado_por
`transporte(url) -> (status, bytes, cabecalhos)`; o real (`transporte_real`, urllib; ou `transporte_curl`
com `--curl`, para o PC com antivírus) só é usado pela CLI, nunca pelos testes.

Regras:
- Canal de YouTube: (1) o feed `feeds/videos.xml?channel_id=` com 200 + XML válido + <title> batendo
  com o nome (sem acento/maiúscula; aceita um conter o outro) -> verificado_por "feed"; (2) se o feed
  falhar (na nuvem ele responde 404 para qualquer canal), a página https://www.youtube.com/@handle:
  o id que a PRÓPRIA página declara (externalId / canonical) tem que ser igual ao esperado, ou é
  descoberto quando não foi dado -> verificado_por "pagina_canal"; (3) senão descarta com motivo.
- RSS/Atom: 200 + XML válido (RSS 2.0, RSS 1.0 ou Atom; tolera BOM e namespaces) + ao menos 1 item
  com data (pubDate / dc:date / published / updated) nos últimos 30 dias -> verificado_por "rss"|"atom".
- `oficial: true` só para canal/sala da própria marca, clube, liga ou federação; site/canal de notícia
  (ge, Omelete, Autoesporte, IGN...) é sempre oficial=false e video_reutilizavel=false.
- `video_reutilizavel: true` só para vídeo oficial de clube/CBF/liga (futebol: com crédito e áudio
  original) ou trailer/clipe oficial de estúdio (filmes, gta: sempre com comentário nosso, nunca trailer
  puro) — e sempre com `nota_uso`. Fora disso (ex.: montadora) fica false.
- Flow Games nunca entra: rejeitado pelo nome ou pela URL.
- Windows: pathlib, encoding utf-8 em todo arquivo, gravação atômica (.tmp + os.replace), Python 3.11/3.12.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import ssl
import sys
import tempfile
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

try:
    from zoneinfo import ZoneInfo
    FUSO = ZoneInfo("America/Sao_Paulo")
except Exception:  # Windows sem tzdata: Brasília sem horário de verão
    FUSO = timezone(timedelta(hours=-3), "BRT")

# --- constantes --------------------------------------------------------------------------
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
TIMEOUT_SEG = 30
JANELA_DIAS = 30
CA_PADRAO = "/root/.ccr/ca-bundle.crt"          # proxy da nuvem; no PC não existe e vale o truststore
YT_PAGINA = "https://www.youtube.com/{handle}"
YT_CANAL = "https://www.youtube.com/channel/{id}"
YT_FEED = "https://www.youtube.com/feeds/videos.xml?channel_id={id}"
RE_CHANNEL_ID = re.compile(r"UC[0-9A-Za-z_-]{22}")
RE_HANDLE = re.compile(r"@([A-Za-z0-9._\-]+)")
CANAIS_RADAR = ("gta", "futebol", "filmes", "carros")

# nota_uso obrigatória quando video_reutilizavel=true (só estes canais admitem reutilizar vídeo)
NOTA_USO_PADRAO = {
    "futebol": "só vídeo oficial do clube/CBF/liga, com crédito e áudio original; nunca imagem de TV",
    "filmes": "trailer/clipe só com comentário nosso; nunca trailer puro",
    "gta": "trailer só com comentário nosso; nunca trailer puro",
}

# sites/canais de notícia: nunca oficial, nunca vídeo reutilizável. Token com até 5 letras só casa
# exato (nome, @handle ou rótulo do domínio); maior que isso casa por "contém".
SITES_NOTICIA = (
    "ge", "globoesporte", "globo", "g1", "omelete", "omeletetv", "adorocinema", "autoesporte",
    "quatrorodas", "ign", "ignbrasil", "gamespot", "deadline", "variety", "cinepop", "legiaodosherois",
    "motor1", "carscoops", "thedrive", "noticiasautomotivas", "acelerados", "carwow", "topgear",
    "espn", "espnbrasil", "lance", "lancenet", "uol", "cnn", "cnnbrasil", "folha", "estadao", "terra",
    "r7", "band", "bandsports", "sbt", "record", "tntsports", "cazetv", "kotaku", "polygon",
    "eurogamer", "screenrant", "collider", "hollywoodreporter", "jalopnik", "motortrend",
    "caranddriver", "autoblog", "flatout", "webmotors", "icarros", "mobiauto", "techtudo",
    "theenemy", "voxel", "gameblast", "canaltech", "tecmundo", "olhardigital", "meusjogos",
)
TOKENS_EXATOS = ("motor1",)                       # só casam a chave inteira (F4: "greatwallmotor1853" não é o Motor1)
PROIBIDOS = ("flowgames", "flowpodcast")        # Flow Games nunca entra (regra 6 do enunciado)

Transporte = Callable[[str], Tuple[int, bytes, dict]]


# --- texto e datas -----------------------------------------------------------------------
def normalizar(texto: Optional[str]) -> str:
    """Minúsculas, sem acento, só letras e números ("São Paulo FC" -> "saopaulofc")."""
    if not texto:
        return ""
    s = unicodedata.normalize("NFKD", str(texto))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    s = re.sub(r"\s*-\s*youtube$", "", s.strip())
    return re.sub(r"[^a-z0-9]+", "", s)


def nomes_batem(a: Optional[str], b: Optional[str]) -> bool:
    """Iguais depois de normalizar, ou um contém o outro (o menor precisa ter 3+ caracteres)."""
    na, nb = normalizar(a), normalizar(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    menor, maior = (na, nb) if len(na) <= len(nb) else (nb, na)
    return len(menor) >= 3 and menor in maior


def analisar_data(texto: Optional[str]) -> Optional[datetime]:
    """RFC 2822 (pubDate) ou ISO 8601 (published/updated, com Z). Sem fuso = UTC. Inválida -> None."""
    if not texto:
        return None
    t = str(texto).strip()
    if not t:
        return None
    dt = None
    try:
        dt = parsedate_to_datetime(t)
    except (ValueError, TypeError, IndexError):
        dt = None
    if dt is None:
        iso = t[:-1] + "+00:00" if t.endswith(("Z", "z")) else t
        try:
            dt = datetime.fromisoformat(iso)
        except ValueError:
            dt = _data_por_extenso(t)
            if dt is None:
                return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


_MESES = {
    "janeiro": 1, "fevereiro": 2, "marco": 3, "março": 3, "abril": 4, "maio": 5, "junho": 6, "julho": 7,
    "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "fev": 2, "feb": 2, "mar": 3, "abr": 4, "apr": 4, "mai": 5, "jun": 6, "jul": 7, "ago": 8,
    "aug": 8, "set": 9, "sep": 9, "out": 10, "oct": 10, "nov": 11, "dez": 12, "dec": 12,
}
_RX_EXTENSO_PT = re.compile(r"(\d{1,2})(?:\s+de)?\s+([a-zç]+)\.?(?:\s+de)?\s+(\d{4})")
_RX_EXTENSO_EN = re.compile(r"([a-z]+)\.?\s+(\d{1,2}),?\s+(\d{4})")


def _data_por_extenso(texto: str) -> Optional[datetime]:
    """'30 de setembro de 2026', '30 set 2026', 'September 30, 2026' -> datetime UTC (F4, feed da Netflix pt_br)."""
    t = texto.strip().lower()
    m = _RX_EXTENSO_PT.search(t)
    if m and m.group(2) in _MESES:
        dia, mes, ano = int(m.group(1)), _MESES[m.group(2)], int(m.group(3))
    else:
        m = _RX_EXTENSO_EN.search(t)
        if not (m and m.group(1) in _MESES):
            return None
        mes, dia, ano = _MESES[m.group(1)], int(m.group(2)), int(m.group(3))
    try:
        return datetime(ano, mes, dia, tzinfo=timezone.utc)
    except ValueError:
        return None


def _hoje(hoje: Optional[datetime]) -> datetime:
    if hoje is None:
        return datetime.now(FUSO)
    return hoje if hoje.tzinfo else hoje.replace(tzinfo=timezone.utc)


def _carimbo(hoje: datetime) -> str:
    return hoje.isoformat(timespec="seconds")


# --- XML / feeds -------------------------------------------------------------------------
def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def analisar_xml(dados) -> Optional[ET.Element]:
    """Raiz do XML ou None se não for XML. Tolera BOM, espaço antes da declaração e str."""
    if dados is None:
        return None
    if isinstance(dados, str):
        dados = dados.encode("utf-8")
    dados = dados.lstrip(b"\xef\xbb\xbf").lstrip()
    if not dados.startswith(b"<"):
        return None
    try:
        return ET.fromstring(dados)
    except ET.ParseError:
        return None


def parece_html(dados) -> bool:
    """Página HTML no lugar de um feed (erro 404 bonito, login, bloqueio)."""
    if isinstance(dados, str):
        dados = dados.encode("utf-8", errors="replace")
    inicio = (dados or b"")[:400].lstrip(b"\xef\xbb\xbf").lstrip().lower()
    return inicio.startswith((b"<!doctype html", b"<html")) or b"<html" in inicio[:100]


def _texto(el: Optional[ET.Element], *nomes: str) -> str:
    if el is None:
        return ""
    for filho in el:
        if _local(filho.tag) in nomes:
            return (filho.text or "").strip()
    return ""


def _data_do_item(item: ET.Element) -> Optional[datetime]:
    for nome in ("pubDate", "published", "date", "issued", "created", "updated", "modified"):
        for filho in item:
            if _local(filho.tag) == nome:
                dt = analisar_data(filho.text)
                if dt:
                    return dt
    return None


def _link_do_item(item: ET.Element) -> str:
    alternativo = ""
    for filho in item:
        if _local(filho.tag) != "link":
            continue
        href = (filho.get("href") or "").strip()
        rel = filho.get("rel") or "alternate"
        if href and rel == "alternate":
            return href
        if not href and (filho.text or "").strip():
            return filho.text.strip()
        alternativo = alternativo or href
    return alternativo


def analisar_feed(dados) -> Optional[dict]:
    """{"tipo": "rss"|"atom", "titulo", "itens": [{"titulo","data","link"}], "channel_id"} ou None."""
    raiz = analisar_xml(dados)
    if raiz is None:
        return None
    nome = _local(raiz.tag)
    if nome == "rss":
        canal = next((f for f in raiz if _local(f.tag) == "channel"), None)
        if canal is None:
            return None
        titulo, fonte, tipo = _texto(canal, "title"), canal, "rss"
    elif nome == "RDF":
        canal = next((f for f in raiz if _local(f.tag) == "channel"), None)
        titulo, fonte, tipo = _texto(canal, "title"), raiz, "rss"
    elif nome == "feed":
        titulo, fonte, tipo = _texto(raiz, "title"), raiz, "atom"
    else:
        return None
    etiqueta = "item" if tipo == "rss" else "entry"
    itens = []
    for el in fonte:
        if _local(el.tag) != etiqueta:
            continue
        itens.append({"titulo": _texto(el, "title"), "data": _data_do_item(el), "link": _link_do_item(el)})
    channel_id = _texto(fonte, "channelId") if tipo == "atom" else ""
    return {"tipo": tipo, "titulo": html.unescape(titulo), "itens": itens, "channel_id": channel_id}


def _buscar(transporte: Optional[Transporte], url: str) -> Tuple[int, bytes, dict, Optional[str]]:
    """Chama o transporte e nunca deixa exceção passar: devolve (status, bytes, cabeçalhos, erro)."""
    if transporte is None:
        raise ValueError("verificar_fontes: falta o transporte (rede só entra por transporte injetado)")
    try:
        resposta = transporte(url)
    except Exception as e:  # noqa: BLE001 — qualquer falha de rede vira motivo
        return 0, b"", {}, f"erro de rede: {e}"
    try:
        status, dados, cab = resposta
    except (TypeError, ValueError):
        return 0, b"", {}, "transporte devolveu resposta fora do formato (status, bytes, cabecalhos)"
    if isinstance(dados, str):
        dados = dados.encode("utf-8")
    if not status:
        return 0, dados or b"", cab or {}, f"sem conexão: {(cab or {}).get('erro', 'sem resposta')}"
    return int(status), dados or b"", cab or {}, None


def verificar_rss(url: str, transporte: Transporte, hoje: Optional[datetime] = None,
                  dias: int = JANELA_DIAS) -> dict:
    """200 + XML válido (RSS/Atom) + >= 1 item com data nos últimos `dias`. Senão ok=False e motivo."""
    hoje = _hoje(hoje)
    saida = {"ok": False, "url": url, "titulo": "", "tipo": None, "n_itens": 0, "mais_novo": None,
             "motivo": None, "verificado_por": None, "verificado_em": _carimbo(hoje)}
    status, dados, _cab, erro = _buscar(transporte, url)
    if erro:
        saida["motivo"] = erro
        return saida
    if status != 200:
        saida["motivo"] = f"HTTP {status}"
        return saida
    if parece_html(dados):
        saida["motivo"] = "não é XML (veio uma página HTML)"
        return saida
    if analisar_xml(dados) is None:
        saida["motivo"] = "não é XML"
        return saida
    feed = analisar_feed(dados)
    if feed is None:
        saida["motivo"] = "XML não é RSS nem Atom"
        return saida
    saida.update(titulo=feed["titulo"], tipo=feed["tipo"], n_itens=len(feed["itens"]))
    if not feed["itens"]:
        saida["motivo"] = "feed sem itens"
        return saida
    datas = [i["data"] for i in feed["itens"] if i["data"]]
    if not datas:
        saida["motivo"] = "nenhum item com data"
        return saida
    mais_novo = max(datas)
    saida["mais_novo"] = mais_novo.isoformat(timespec="seconds")
    if mais_novo < hoje - timedelta(days=dias):
        saida["motivo"] = f"sem item nos últimos {dias} dias (mais novo: {mais_novo.date().isoformat()})"
        return saida
    saida.update(ok=True, verificado_por=feed["tipo"])
    return saida


# --- YouTube -----------------------------------------------------------------------------
def interpretar_canal(texto: str) -> dict:
    """"@x", "x", "https://www.youtube.com/@x/videos", ".../channel/UC..." -> {handle, channel_id, pagina}."""
    t = (texto or "").strip()
    saida = {"handle": None, "channel_id": None, "pagina": None}
    if not t:
        return saida
    m = re.search(r"/channel/(UC[0-9A-Za-z_-]{22})", t)
    if m:
        saida["channel_id"] = m.group(1)
    elif RE_CHANNEL_ID.fullmatch(t):
        saida["channel_id"] = t
    m = RE_HANDLE.search(t)
    if m:
        saida["handle"] = "@" + m.group(1).rstrip(".")
    elif "/" not in t and not saida["channel_id"] and re.fullmatch(r"[A-Za-z0-9._\-]+", t):
        saida["handle"] = "@" + t
    if saida["handle"]:
        saida["pagina"] = YT_PAGINA.format(handle=saida["handle"])
    elif saida["channel_id"]:
        saida["pagina"] = YT_CANAL.format(id=saida["channel_id"])
    elif t.startswith(("http://", "https://")) and "youtube.com/" in t:
        saida["pagina"] = t.split("?", 1)[0].split("#", 1)[0]   # /c/Nome ou /user/Nome (legado)
    return saida


def analisar_pagina_canal(pagina) -> dict:
    """Extrai da página do canal o id que ela própria declara, o título e o @handle."""
    if isinstance(pagina, bytes):
        pagina = pagina.decode("utf-8", errors="replace")
    pagina = pagina or ""
    channel_id = None
    for padrao in (r'"externalId"\s*:\s*"(UC[0-9A-Za-z_-]{22})"',
                   r'<link[^>]+rel="canonical"[^>]+href="https://www\.youtube\.com/channel/(UC[0-9A-Za-z_-]{22})"',
                   r'feeds/videos\.xml\?channel_id=(UC[0-9A-Za-z_-]{22})'):
        m = re.search(padrao, pagina)
        if m:
            channel_id = m.group(1)
            break
    titulo = ""
    for padrao in (r'<meta\s+property="og:title"\s+content="([^"]*)"',
                   r'<meta\s+name="title"\s+content="([^"]*)"',
                   r'<meta\s+itemprop="name"\s+content="([^"]*)"',
                   r"<title>([^<]*)</title>"):
        m = re.search(padrao, pagina)
        if m and m.group(1).strip():
            titulo = html.unescape(m.group(1).strip())
            titulo = re.sub(r"\s*-\s*YouTube$", "", titulo)
            break
    handle = None
    for padrao in (r'"canonicalBaseUrl"\s*:\s*"/(@[A-Za-z0-9._\-]+)"',
                   r'"vanityChannelUrl"\s*:\s*"https?://www\.youtube\.com/(@[A-Za-z0-9._\-]+)"',
                   r'<meta\s+property="og:url"\s+content="https://www\.youtube\.com/(@[A-Za-z0-9._\-]+)"'):
        m = re.search(padrao, pagina)
        if m:
            handle = m.group(1)
            break
    return {"channel_id": channel_id, "titulo": titulo, "handle": handle}


def _mesmo_id(a: Optional[str], b: Optional[str]) -> bool:
    """O feed do YouTube às vezes escreve o id sem o prefixo UC."""
    if not a or not b:
        return False
    return a[2:] == b[2:] if (a.startswith("UC") and b.startswith("UC")) else a.lstrip("UC") == b.lstrip("UC")


def _verificar_feed_youtube(channel_id: str, transporte: Transporte, nome: Optional[str]) -> dict:
    url = YT_FEED.format(id=channel_id)
    status, dados, _cab, erro = _buscar(transporte, url)
    if erro:
        return {"ok": False, "motivo": f"feed: {erro}", "url": url}
    if status != 200:
        return {"ok": False, "motivo": f"feed: HTTP {status}", "url": url}
    feed = analisar_feed(dados)
    if feed is None:
        return {"ok": False, "motivo": "feed: não é XML de feed", "url": url}
    if feed["channel_id"] and not _mesmo_id(feed["channel_id"], channel_id):
        return {"ok": False, "motivo": f"feed: declara o id {feed['channel_id']}, não {channel_id}", "url": url}
    if not feed["titulo"]:
        return {"ok": False, "motivo": "feed: sem <title>", "url": url}
    if nome and not nomes_batem(nome, feed["titulo"]):
        return {"ok": False, "motivo": f"feed: título '{feed['titulo']}' não bate com o nome '{nome}'", "url": url}
    return {"ok": True, "titulo": feed["titulo"], "url": url, "motivo": None}


def verificar_canal_youtube(handle_ou_url: str, channel_id: Optional[str] = None,
                            transporte: Optional[Transporte] = None, nome: Optional[str] = None,
                            hoje: Optional[datetime] = None) -> dict:
    """Feed (200 + título batendo) -> "feed"; senão a página do canal (id declarado == esperado, ou
    descoberto) -> "pagina_canal"; senão ok=False com motivo. `nome` é o nome esperado (opcional:
    sem ele não se confere título, só o id)."""
    hoje = _hoje(hoje)
    info = interpretar_canal(handle_ou_url)
    channel_id = (channel_id or "").strip() or info["channel_id"]
    handle = info["handle"]
    saida = {"ok": False, "nome": nome or (handle or "").lstrip("@") or channel_id, "handle": handle,
             "url": None, "channel_id": channel_id, "titulo": "", "verificado_por": None,
             "evidencia": None, "motivo": None, "verificado_em": _carimbo(hoje)}
    motivos: List[str] = []
    if channel_id and not RE_CHANNEL_ID.fullmatch(channel_id):
        saida["motivo"] = f"channel_id '{channel_id}' não tem o formato UC + 22 caracteres"
        return saida

    def pronto(por: str, titulo: str, evidencia: str) -> dict:
        saida.update(ok=True, channel_id=channel_id, titulo=titulo, verificado_por=por, evidencia=evidencia,
                     url=YT_PAGINA.format(handle=handle) if handle else YT_CANAL.format(id=channel_id))
        saida["handle"] = handle
        return saida

    if channel_id:
        r = _verificar_feed_youtube(channel_id, transporte, nome)
        if r["ok"]:
            return pronto("feed", r["titulo"], r["url"])
        motivos.append(r["motivo"])
    if not info["pagina"]:
        motivos.append("sem @handle nem URL para abrir a página do canal")
        saida["motivo"] = "; ".join(motivos)
        return saida

    status, dados, _cab, erro = _buscar(transporte, info["pagina"])
    if erro:
        motivos.append(f"página do canal: {erro}")
    elif status != 200:
        motivos.append(f"página do canal: HTTP {status}")
    else:
        pag = analisar_pagina_canal(dados)
        if not pag["channel_id"]:
            motivos.append("página do canal sem id (externalId/canonical)")
        elif channel_id and pag["channel_id"] != channel_id:
            motivos.append(f"a página de {handle or info['pagina']} declara o id {pag['channel_id']}, "
                           f"diferente do esperado {channel_id}")
        elif nome and pag["titulo"] and not nomes_batem(nome, pag["titulo"]):
            motivos.append(f"página: título '{pag['titulo']}' não bate com o nome '{nome}'")
        else:
            handle = handle or pag["handle"]
            if not channel_id:
                channel_id = pag["channel_id"]
                r = _verificar_feed_youtube(channel_id, transporte, nome)
                if r["ok"]:
                    saida["titulo"] = r["titulo"]
                    return pronto("feed", r["titulo"], info["pagina"])
            return pronto("pagina_canal", pag["titulo"], info["pagina"])
    saida["motivo"] = "; ".join(motivos)
    return saida


# --- regras de classificação (funções puras) ---------------------------------------------
def _bool(valor) -> bool:
    if isinstance(valor, bool):
        return valor
    if valor is None:
        return False
    if isinstance(valor, (int, float)):
        return bool(valor)
    return str(valor).strip().lower() in ("1", "true", "sim", "s", "yes", "y", "verdadeiro", "x")


def _chaves(nome: Optional[str], url: Optional[str]) -> List[str]:
    """Pedaços onde procurar um site de notícia: nome, @handle e rótulos do domínio (fora do YouTube)."""
    chaves = [normalizar(nome)]
    u = (url or "").strip()
    m = RE_HANDLE.search(u)
    if m:
        chaves.append(normalizar(m.group(1)))
    host = ""
    if u:
        try:
            host = urllib.parse.urlsplit(u if "://" in u else "https://" + u).hostname or ""
        except ValueError:
            host = ""
    host = host.lower()
    if host and "youtube.com" not in host and "youtu.be" not in host:
        if host.startswith("www."):
            host = host[4:]
        chaves.append(normalizar(host))
        chaves.extend(normalizar(p) for p in host.split("."))
    return [c for c in chaves if c]


def e_flow_games(nome: Optional[str], url: Optional[str] = None) -> bool:
    chaves = _chaves(nome, url)
    return any(p in c for c in chaves for p in PROIBIDOS) or normalizar(nome) == "flow"


def e_site_noticia(nome: Optional[str], url: Optional[str] = None) -> bool:
    chaves = _chaves(nome, url)
    for token in SITES_NOTICIA:
        if len(token) <= 5 or token in TOKENS_EXATOS:
            if any(c == token for c in chaves):
                return True
        elif any(token in c for c in chaves):
            return True
    return False


def _tipo_de(entrada: dict) -> str:
    tipo = str(entrada.get("tipo") or "").strip().lower()
    if tipo in ("youtube", "rss"):
        return tipo
    url = str(entrada.get("url") or "")
    return "youtube" if (entrada.get("channel_id") or "youtube.com" in url or url.startswith("@")) else "rss"


def oficial(entrada: dict) -> bool:
    """True só para canal/sala da própria marca, clube, liga ou federação (nunca site de notícia)."""
    nome, url = entrada.get("nome"), entrada.get("url")
    if e_flow_games(nome, url) or e_site_noticia(nome, url):
        return False
    return _bool(entrada.get("oficial"))


def video_reutilizavel(entrada: dict, canal: str = "") -> bool:
    """True só para canal de YouTube oficial de clube/CBF/liga (futebol) ou estúdio (filmes, gta)."""
    if _tipo_de(entrada) != "youtube" or not oficial(entrada):
        return False
    return (canal or "").strip().lower() in NOTA_USO_PADRAO and _bool(entrada.get("video_reutilizavel"))


def classificar(entrada: dict, canal: str = "") -> dict:
    """Aplica as regras: {"rejeitar": motivo|None, "oficial", "video_reutilizavel", "nota_uso", "avisos"}."""
    nome, url = entrada.get("nome", ""), entrada.get("url", "")
    canal = (canal or "").strip().lower()
    if e_flow_games(nome, url):
        return {"rejeitar": "Flow Games nunca entra no radar", "oficial": False, "video_reutilizavel": False,
                "nota_uso": None, "avisos": []}
    avisos: List[str] = []
    noticia = e_site_noticia(nome, url)
    ofi = oficial(entrada)
    if _bool(entrada.get("oficial")) and noticia:
        avisos.append(f"{nome}: site/canal de notícia não é oficial (oficial passou a false)")
    reut = video_reutilizavel(entrada, canal)
    if _bool(entrada.get("video_reutilizavel")) and not reut:
        if _tipo_de(entrada) != "youtube":
            avisos.append(f"{nome}: vídeo reutilizável só vale para canal de YouTube (passou a false)")
        elif not ofi:
            avisos.append(f"{nome}: vídeo reutilizável exige fonte oficial"
                          + (" — site de notícia" if noticia else "") + " (passou a false)")
        else:
            avisos.append(f"{nome}: no canal '{canal or '?'}' vídeo reutilizável não vale — só clube/CBF/liga "
                          f"(futebol) ou trailer de estúdio (filmes, gta) (passou a false)")
    nota = (entrada.get("nota_uso") or "").strip() or None
    if reut and not nota:
        nota = NOTA_USO_PADRAO[canal]
    return {"rejeitar": None, "oficial": ofi, "video_reutilizavel": reut, "nota_uso": nota, "avisos": avisos}


# --- entradas no formato de 4.10 ---------------------------------------------------------
def _peso(entrada: dict, ofi: bool) -> float:
    try:
        return float(entrada["peso"]) if entrada.get("peso") not in (None, "") else (1.5 if ofi else 1.0)
    except (TypeError, ValueError):
        return 1.5 if ofi else 1.0


MARCAS_HUMANAS = ("ja_existe", "nota_conferir")   # anotações do Antônio: sobrevivem ao --gravar (F4)


def _manter_marcas(entrada: dict, saida: dict) -> None:
    for k in MARCAS_HUMANAS:
        if k in entrada:
            saida[k] = entrada[k]


def verificar_entrada_rss(entrada: dict, canal: str, transporte: Transporte,
                          hoje: Optional[datetime] = None) -> Tuple[Optional[dict], Optional[dict], List[str]]:
    """-> (entrada verificada | None, descartada | None, avisos)."""
    nome, url = str(entrada.get("nome") or "").strip(), str(entrada.get("url") or "").strip()
    cls = classificar({**entrada, "tipo": "rss"}, canal)
    if cls["rejeitar"]:
        return None, {"nome": nome, "url": url, "motivo": cls["rejeitar"]}, cls["avisos"]
    if not url:
        return None, {"nome": nome, "url": url, "motivo": "sem url"}, cls["avisos"]
    r = verificar_rss(url, transporte, hoje)
    if not r["ok"]:
        return None, {"nome": nome, "url": url, "motivo": r["motivo"]}, cls["avisos"]
    ofi = cls["oficial"]
    saida = {
        "nome": nome or r["titulo"], "url": url, "oficial": ofi,
        "filtrar": _bool(entrada["filtrar"]) if "filtrar" in entrada else (not ofi),
        "peso": _peso(entrada, ofi), "verificado_em": r["verificado_em"],
        "evidencia": str(entrada.get("evidencia") or "").strip() or url, "verificado_por": r["verificado_por"],
    }
    _manter_marcas(entrada, saida)
    return saida, None, cls["avisos"]


def verificar_entrada_youtube(entrada: dict, canal: str, transporte: Transporte,
                              hoje: Optional[datetime] = None) -> Tuple[Optional[dict], Optional[dict], List[str]]:
    """-> (entrada verificada | None, descartada | None, avisos)."""
    nome = str(entrada.get("nome") or "").strip()
    url = str(entrada.get("url") or "").strip()
    cid = str(entrada.get("channel_id") or "").strip() or None
    cls = classificar({**entrada, "tipo": "youtube"}, canal)
    descarte = {"nome": nome}                 # 4.10: {nome, url|channel_id, motivo} — só o que se sabe
    if url:
        descarte["url"] = url
    if cid:
        descarte["channel_id"] = cid
    if cls["rejeitar"]:
        return None, {**descarte, "motivo": cls["rejeitar"]}, cls["avisos"]
    if not url and not cid:
        return None, {**descarte, "motivo": "sem url (@handle) nem channel_id"}, cls["avisos"]
    r = verificar_canal_youtube(url or cid, cid, transporte, nome=nome or None, hoje=hoje)
    if not r["ok"]:
        return None, {**descarte, "motivo": r["motivo"]}, cls["avisos"]
    ofi = cls["oficial"]
    saida = {"nome": nome or r["titulo"], "url": r["url"], "channel_id": r["channel_id"],
             "peso": _peso(entrada, ofi), "oficial": ofi, "video_reutilizavel": cls["video_reutilizavel"]}
    if cls["nota_uso"]:
        saida["nota_uso"] = cls["nota_uso"]
    saida.update(verificado_em=r["verificado_em"],
                 evidencia=str(entrada.get("evidencia") or "").strip() or r["evidencia"],
                 verificado_por=r["verificado_por"])
    _manter_marcas(entrada, saida)
    return saida, None, cls["avisos"]


def _chave_descarte(d: dict) -> str:
    return (d.get("channel_id") or d.get("url") or d.get("nome") or "").strip().lower()


def verificar_lista(canal: str, rss: List[dict], youtube: List[dict], transporte: Transporte,
                    hoje: Optional[datetime] = None, descartadas: Optional[List[dict]] = None
                    ) -> Tuple[dict, List[str]]:
    """Verifica tudo e devolve (JSON no formato de 4.10 + campos novos, avisos)."""
    hoje = _hoje(hoje)
    saida = {"canal": canal, "verificado_em": _carimbo(hoje), "rss": [], "youtube": [], "descartadas": []}
    avisos: List[str] = []
    vistas = set()
    for d in descartadas or []:
        if isinstance(d, dict) and _chave_descarte(d) not in vistas:
            vistas.add(_chave_descarte(d))
            saida["descartadas"].append(d)
    for entrada in rss or []:
        ok, ruim, av = verificar_entrada_rss(entrada, canal, transporte, hoje)
        avisos.extend(av)
        if ok:
            saida["rss"].append(ok)
        elif _chave_descarte(ruim) not in vistas:
            vistas.add(_chave_descarte(ruim))
            saida["descartadas"].append(ruim)
    for entrada in youtube or []:
        ok, ruim, av = verificar_entrada_youtube(entrada, canal, transporte, hoje)
        avisos.extend(av)
        if ok:
            saida["youtube"].append(ok)
        elif _chave_descarte(ruim) not in vistas:
            vistas.add(_chave_descarte(ruim))
            saida["descartadas"].append(ruim)
    return saida, avisos


def gravar_json(caminho: Path, dados) -> Path:
    """Grava em .tmp na mesma pasta e troca (nunca deixa JSON pela metade)."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp_", suffix=".json", dir=str(caminho.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=1)
            f.write("\n")
        os.replace(tmp, caminho)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return caminho


def verificar_arquivo(caminho, transporte: Transporte, hoje: Optional[datetime] = None,
                      gravar: bool = False) -> dict:
    """Relê <canal>_fontes_novas.json, refaz a verificação de tudo e devolve o JSON atualizado.
    Entradas que falharem vão para `descartadas` (as já descartadas ficam). Com gravar=True regrava
    o arquivo (atômico). Os avisos de classificação ficam em dados["_avisos"] só na memória."""
    caminho = Path(caminho)
    dados = json.loads(caminho.read_text(encoding="utf-8-sig"))
    if not isinstance(dados, dict):
        raise ValueError(f"{caminho.name}: o JSON precisa ser um objeto com canal/rss/youtube")
    canal = str(dados.get("canal") or caminho.name.split("_", 1)[0]).strip().lower()
    saida, avisos = verificar_lista(canal, dados.get("rss") or [], dados.get("youtube") or [], transporte,
                                    hoje, dados.get("descartadas") or [])
    for chave, valor in dados.items():      # chaves extras do arquivo ficam depois das de 4.10
        if chave not in saida and not chave.startswith("_"):
            saida[chave] = valor
    if gravar:
        gravar_json(caminho, saida)
    saida["_avisos"] = avisos
    return saida


def ler_candidatos(texto: str, canal: str = "") -> Tuple[List[dict], List[dict], List[str]]:
    """Linhas "tipo|nome|url|oficial|reutilizavel[|channel_id[|peso]]" -> (rss, youtube, erros).
    Linha vazia ou começando com # é ignorada."""
    rss, youtube, erros = [], [], []
    for n, linha in enumerate(texto.splitlines(), 1):
        l = linha.strip()
        if not l or l.startswith("#"):
            continue
        partes = [p.strip() for p in l.split("|")]
        if len(partes) < 3:
            erros.append(f"linha {n}: esperava tipo|nome|url|oficial|reutilizavel, veio '{l}'")
            continue
        tipo = partes[0].lower()
        if tipo not in ("rss", "youtube", "yt"):
            erros.append(f"linha {n}: tipo '{partes[0]}' desconhecido (use rss ou youtube)")
            continue
        entrada = {"tipo": "youtube" if tipo in ("youtube", "yt") else "rss", "nome": partes[1], "url": partes[2],
                   "oficial": _bool(partes[3]) if len(partes) > 3 else False,
                   "video_reutilizavel": _bool(partes[4]) if len(partes) > 4 else False}
        if len(partes) > 5 and partes[5]:
            entrada["channel_id"] = partes[5]
        if len(partes) > 6 and partes[6]:
            entrada["peso"] = partes[6]
        (youtube if entrada["tipo"] == "youtube" else rss).append(entrada)
    return rss, youtube, erros


# --- transporte real (só a CLI usa) ------------------------------------------------------
_CTX_SSL = None


def _contexto_ssl() -> ssl.SSLContext:
    """Nuvem: CA do proxy (SSL_CERT_FILE ou CA_PADRAO). PC: truststore do Windows, se instalado."""
    global _CTX_SSL
    if _CTX_SSL is not None:
        return _CTX_SSL
    try:
        import truststore  # type: ignore
        truststore.inject_into_ssl()
    except Exception:  # noqa: BLE001 — sem truststore vale a CA padrão do Python
        pass
    cafile = os.environ.get("SSL_CERT_FILE") or CA_PADRAO
    if cafile and Path(cafile).exists():
        _CTX_SSL = ssl.create_default_context(cafile=cafile)
    else:
        _CTX_SSL = ssl.create_default_context()
    return _CTX_SSL


def transporte_real(url: str, timeout: float = TIMEOUT_SEG) -> Tuple[int, bytes, dict]:
    """urllib com User-Agent de navegador; respeita HTTPS_PROXY do ambiente. Falha de rede -> status 0."""
    pedido = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT, "Accept": "*/*", "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"})
    try:
        with urllib.request.urlopen(pedido, timeout=timeout, context=_contexto_ssl()) as r:
            return int(r.status), r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        try:
            corpo = e.read() or b""
        except Exception:  # noqa: BLE001
            corpo = b""
        return int(e.code), corpo, dict(e.headers or {})
    except (urllib.error.URLError, OSError, ValueError) as e:
        return 0, b"", {"erro": str(e)}


def transporte_curl(url: str, timeout: float = TIMEOUT_SEG, curl: str = "curl") -> Tuple[int, bytes, dict]:
    """Alternativa do PC (o Avast quebra o HTTPS do Python): curl.exe por subprocesso em LISTA, sem janela.
    Ligue com `--curl` na CLI. Falha -> status 0 com o erro em cabecalhos["erro"]."""
    import subprocess
    fd, corpo = tempfile.mkstemp(prefix=".curl_", suffix=".bin")
    os.close(fd)
    cmd = [curl, "-sS", "-L", "--max-time", str(int(timeout)), "-A", USER_AGENT,
           "-o", corpo, "-w", "%{http_code}", url]
    kw = {"capture_output": True, "timeout": timeout + 5}
    if os.name == "nt":
        kw["creationflags"] = 0x08000000           # CREATE_NO_WINDOW
    try:
        r = subprocess.run(cmd, **kw)
        dados = Path(corpo).read_bytes() if Path(corpo).exists() else b""
        status = int((r.stdout or b"").decode("ascii", errors="ignore").strip()[-3:] or 0)
        if r.returncode != 0 and not status:
            return 0, b"", {"erro": (r.stderr or b"").decode("utf-8", errors="replace").strip() or f"curl saiu com {r.returncode}"}
        return status, dados, {}
    except (OSError, ValueError, subprocess.SubprocessError) as e:
        return 0, b"", {"erro": str(e)}
    finally:
        try:
            os.unlink(corpo)
        except OSError:
            pass


def com_cache(transporte: Transporte) -> Transporte:
    """Mesma URL só é buscada uma vez por execução."""
    cache: Dict[str, Tuple[int, bytes, dict]] = {}

    def _t(url: str):
        if url not in cache:
            cache[url] = transporte(url)
        return cache[url]
    return _t


# --- CLI ---------------------------------------------------------------------------------
def _json(dados) -> str:
    return json.dumps(dados, ensure_ascii=False, indent=1)


def _imprimir_avisos(avisos: List[str]) -> None:
    for a in avisos:
        print(f"aviso: {a}", file=sys.stderr)


def _canal_do_nome(caminho: Path) -> str:
    primeiro = caminho.name.split("_", 1)[0].lower()
    return primeiro if primeiro in CANAIS_RADAR + ("receitas", "destinos") else ""


def _cmd_verificar(args, transporte, hoje) -> int:
    caminho = Path(args.arquivo)
    if not caminho.exists():
        print(f"Arquivo não encontrado: {caminho}", file=sys.stderr)
        return 1
    try:
        antes = json.loads(caminho.read_text(encoding="utf-8-sig"))
        dados = verificar_arquivo(caminho, transporte, hoje, gravar=args.gravar)
    except (ValueError, OSError) as e:
        print(f"Não consegui ler {caminho.name}: {e}", file=sys.stderr)
        return 1
    avisos = dados.pop("_avisos", [])
    n_antes = len(antes.get("descartadas") or []) if isinstance(antes, dict) else 0
    novas = dados["descartadas"][n_antes:]
    if args.json:
        print(_json(dados))
    else:
        print(f"canal {dados['canal']}: rss ok {len(dados['rss'])} · youtube ok {len(dados['youtube'])} · "
              f"descartadas {len(dados['descartadas'])} (novas nesta rodada: {len(novas)})")
        for d in novas:
            print(f"  - caiu: {d.get('nome')} ({d.get('channel_id') or d.get('url')}): {d.get('motivo')}")
        if args.gravar:
            print(f"gravado em {caminho}")
    _imprimir_avisos(avisos)
    return 1 if novas else 0


def _cmd_canal(args, transporte, hoje) -> int:
    r = verificar_canal_youtube(args.canal, args.id, transporte, nome=args.nome, hoje=hoje)
    if args.json:
        print(_json(r))
    elif r["ok"]:
        print(f"id: {r['channel_id']}\ntítulo: {r['titulo']}\nurl: {r['url']}\nverificado_por: {r['verificado_por']}")
    else:
        print(f"não verificado: {r['motivo']}")
    return 0 if r["ok"] else 1


def _cmd_rss(args, transporte, hoje) -> int:
    r = verificar_rss(args.url, transporte, hoje)
    if args.json:
        print(_json(r))
    elif r["ok"]:
        print(f"título: {r['titulo']}\nitens: {r['n_itens']}\nmais novo: {r['mais_novo']}\ntipo: {r['tipo']}")
    else:
        print(f"não verificado: {r['motivo']}" + (f" (título: {r['titulo']})" if r["titulo"] else ""))
    return 0 if r["ok"] else 1


def _cmd_candidatos(args, transporte, hoje) -> int:
    caminho = Path(args.arquivo)
    if not caminho.exists():
        print(f"Arquivo não encontrado: {caminho}", file=sys.stderr)
        return 1
    canal = (args.canal or _canal_do_nome(caminho)).lower()
    rss, youtube, erros = ler_candidatos(caminho.read_text(encoding="utf-8-sig"), canal)
    for e in erros:
        print(f"aviso: {e}", file=sys.stderr)
    if not rss and not youtube:
        print("Nenhum candidato válido no arquivo (linhas: tipo|nome|url|oficial|reutilizavel).", file=sys.stderr)
        return 1
    dados, avisos = verificar_lista(canal, rss, youtube, transporte, hoje)
    if not args.json:
        for e in dados["rss"]:
            print(f"ok rss      {e['nome']} ({e['verificado_por']})", file=sys.stderr)
        for e in dados["youtube"]:
            print(f"ok youtube  {e['nome']} {e['channel_id']} ({e['verificado_por']})", file=sys.stderr)
        for d in dados["descartadas"]:
            print(f"caiu        {d.get('nome')}: {d.get('motivo')}", file=sys.stderr)
    _imprimir_avisos(avisos)
    print(_json(dados))
    return 0 if (dados["rss"] or dados["youtube"]) and not dados["descartadas"] and not erros else 1


def montar_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="verificar_fontes.py",
                                description="Verifica fontes do radar (RSS/Atom e canais de YouTube).")
    p.add_argument("--curl", action="store_true", help="usa curl.exe em vez do urllib (PC com antivírus que quebra o HTTPS)")
    sub = p.add_subparsers(dest="comando", required=True)
    v = sub.add_parser("verificar", help="relê um <canal>_fontes_novas.json e refaz a verificação")
    v.add_argument("arquivo")
    v.add_argument("--gravar", action="store_true", help="regrava o arquivo com o resultado")
    v.add_argument("--json", action="store_true")
    c = sub.add_parser("canal", help="verifica um canal de YouTube (@handle ou URL)")
    c.add_argument("canal")
    c.add_argument("--id", default=None, help="channel_id esperado (UC...)")
    c.add_argument("--nome", default=None, help="nome esperado (confere com o título)")
    c.add_argument("--json", action="store_true")
    r = sub.add_parser("rss", help="verifica um feed RSS/Atom")
    r.add_argument("url")
    r.add_argument("--json", action="store_true")
    k = sub.add_parser("candidatos", help="verifica um .txt de candidatos e imprime o JSON pronto")
    k.add_argument("arquivo")
    k.add_argument("--canal", default=None, help="gta|futebol|filmes|carros (padrão: prefixo do arquivo)")
    k.add_argument("--json", action="store_true")
    return p


def main(argv: Optional[List[str]] = None, transporte: Optional[Transporte] = None,
         hoje: Optional[datetime] = None) -> int:
    for fluxo in (sys.stdout, sys.stderr):      # PowerShell 5.1 sai em ANSI; forçamos UTF-8
        try:
            fluxo.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    args = montar_parser().parse_args(argv)
    transporte = com_cache(transporte or (transporte_curl if args.curl else transporte_real))
    comandos = {"verificar": _cmd_verificar, "canal": _cmd_canal, "rss": _cmd_rss, "candidatos": _cmd_candidatos}
    try:
        return comandos[args.comando](args, transporte, hoje)
    except KeyboardInterrupt:
        print("Interrompido.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
