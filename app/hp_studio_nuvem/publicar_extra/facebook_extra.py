"""facebook_extra — o que falta na Página do Facebook além de postar (que o PC já faz).

O QUE FAZ (tarefa C1 da rodada 2)
    listar_agendados()            GET /{page}/scheduled_posts (paginado) + tentativa de reels agendados
    cancelar_agendado()           DELETE /{id}
    reagendar()                   POST /{id} com scheduled_publish_time (epoch UTC) + is_published=false,
                                  validando a janela da Meta: 10 min a 75 dias (reel: 10 min a 29 dias)
    comparar_com_agendados_json() agenda da API x agendados.json do canal -> buracos, duplicados,
                                  hora errada, sobras e ok (o que o conferente-de-agenda faz no Planner)
    erro_graph()                  qualquer erro da Graph API (Resposta ou ErroRede) em português de leigo,
                                  com os códigos de reel do PC (1363040 proporção, 1363127 resolução,
                                  1363128 duração, 1363129 fps), 190 token, 10/200-299 permissão (diz QUAL),
                                  4/17/32/613 limite, 100 parâmetro, 368 bloqueio e genérico

USO (o PC injeta o cliente e o token; aqui ninguém faz rede nem lê segredo):
    from publicar_extra.facebook_extra import listar_agendados, comparar_com_agendados_json
    itens = listar_agendados(cliente, token_de("gta"), pagina_id)
    rel = comparar_com_agendados_json(itens, ler_json(pasta_canal / "agendados.json"))
    print(rel["resumo"])

REGRAS
    - Token SEMPRE no parâmetro access_token da consulta (GET/DELETE) ou do form (POST); nunca na URL.
      O paging.next que a Meta devolve vem com access_token dentro: a URL é limpa antes de ir ao cliente
      (e ao log) e o token volta pela consulta.
    - Toda mensagem de erro passa por mascarar(); resultados no formato entrada() do PC
      ({"status", "link", "id", "erro", ...}); listar_agendados levanta ErroGraph (mensagem em português).
    - Horas: a API fala em epoch UTC / ISO +0000; aqui tudo vira "AAAA-MM-DD HH:MM" de Brasília (hpbase.FUSO).
      reagendar recebe `agora=` injetado nos testes (nunca relógio real escondido).
    - Documentação oficial conferida em DOC_CONFERIDA_EM (URLs em DOCS). Onde a doc não diz
      (reels agendados), o item sai com "confirmar": True.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from hpbase import FUSO, ler_json
from hpbase import agora as _agora_brasilia

from .contrato_pc import ErroRede, Resposta, entrada, mascarar

API = "https://graph.facebook.com/v26.0"

# Páginas oficiais lidas em 01/10/2026 (curl, só leitura) — ver docs/rodada2/C.md
DOC_CONFERIDA_EM = "2026-10-01"
DOCS = {
    "scheduled_posts": "https://developers.facebook.com/docs/graph-api/reference/page/scheduled_posts/",
    "pages_posts": "https://developers.facebook.com/docs/pages-api/posts/",
    "page_feed": "https://developers.facebook.com/docs/graph-api/reference/v26.0/page/feed",
    "reels": "https://developers.facebook.com/docs/video-api/guides/reels-publishing/",
    "video_reels": "https://developers.facebook.com/docs/graph-api/reference/v26.0/page/video_reels",
    "comments": "https://developers.facebook.com/docs/graph-api/reference/v26.0/object/comments",
    "comment": "https://developers.facebook.com/docs/graph-api/reference/v26.0/comment",
}
# A referência do feed (page_feed) diz 10 min a 75 dias; o guia pages_posts diz 10 min a 30 dias.
# O PC já usa 75 (post) e 29 (reel, video_state=SCHEDULED). Reel agendado LISTADO: a doc não diz
# como (video_reels "Reading: You can't perform this operation"); fica a tentativa com "confirmar".
JANELA_MINUTOS_MIN = 10
JANELA_DIAS_POST = 75
JANELA_DIAS_REEL = 29
REELS_AGENDADOS_CONFIRMADO = False

CAMPOS_AGENDADOS = ("id,message,scheduled_publish_time,created_time,permalink_url,is_published,"
                    "attachments{media_type,url}")
CAMPOS_REELS_AGENDADOS = "id,title,description,scheduled_publish_time,video_status,permalink_url"
LIMITE_PAGINA = 100
MAX_PAGINAS = 20

# Permissão que cada ação pede (doc da Meta, DOC_CONFERIDA_EM): usada quando a Meta não diz qual falta.
PERMISSOES = {
    "listar_agendados": ("pages_read_engagement", "pages_read_user_content"),
    "cancelar_agendado": ("pages_manage_posts",),
    "reagendar": ("pages_manage_posts",),
    "ler_comentarios": ("pages_read_engagement", "pages_read_user_content"),
    "curtir": ("pages_manage_engagement",),
    "responder": ("pages_manage_engagement",),
    "ocultar": ("pages_manage_engagement",),
    "publicar": ("pages_manage_posts", "pages_read_engagement", "pages_show_list"),
}
_RX_PERMISSAO = re.compile(r"\b(pages_[a-z_]+|publish_video|business_management|instagram_[a-z_]+|"
                           r"threads_[a-z_]+|read_page_mailboxes|ads_management)\b")

CODIGOS_TOKEN = {190, 102}
CODIGOS_LIMITE = {4, 17, 32, 613, 80001, 80004, 80005, 80006, 80008}
CODIGOS_PASSAGEIRO = {1, 2}
CODIGOS_BLOQUEIO = {368}
CODIGOS_REEL = {
    1363040: "Reel recusado: a proporção do vídeo não é aceita (precisa ficar entre 16:9 e 9:16; "
             "reel é 9:16 = 1080x1920)",
    1363127: "Reel recusado: resolução baixa (mínimo 540x960; recomendado 1080x1920)",
    1363128: "Reel recusado: duração fora do permitido (entre 3 e 90 segundos)",
    1363129: "Reel recusado: taxa de quadros fora do permitido (entre 24 e 60 fps)",
}


class ErroGraph(Exception):
    """Erro da Graph API já traduzido (mensagem em português, sem token)."""

    def __init__(self, detalhe: dict):
        self.detalhe = dict(detalhe)
        self.mensagem = mascarar(detalhe.get("mensagem") or "erro da Meta")
        self.codigo = detalhe.get("codigo")
        self.subcodigo = detalhe.get("subcodigo")
        self.categoria = detalhe.get("categoria") or "generico"
        self.permissao = detalhe.get("permissao")
        self.transitorio = bool(detalhe.get("transitorio"))
        super().__init__(self.mensagem)

    def __str__(self) -> str:
        return self.mensagem


# ----------------------------------------------------------------------------- erros
def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _permissao_faltando(texto_meta: str, acao: str | None) -> tuple[str, bool]:
    """(permissão, a Meta disse?) — primeiro o que a própria mensagem da Meta cita; senão a da ação."""
    achadas = []
    for p in _RX_PERMISSAO.findall(texto_meta or ""):
        if p not in achadas:
            achadas.append(p)
    if achadas:
        return " e/ou ".join(achadas), True
    if acao and PERMISSOES.get(acao):
        return PERMISSOES[acao][0], False
    return "", False


def detalhar_erro_graph(erro, acao: str | None = None) -> dict:
    """Resposta | ErroRede | dict (o JSON {"error": {...}}) -> {categoria, codigo, subcodigo, tipo,
    mensagem_meta, fbtrace, permissao, transitorio, mensagem (português)}."""
    d = {"categoria": "generico", "codigo": None, "subcodigo": None, "tipo": None,
         "mensagem_meta": "", "fbtrace": None, "permissao": None, "transitorio": False,
         "status": None, "acao": acao}
    if isinstance(erro, ErroRede):
        d.update(categoria="rede", transitorio=bool(erro.transitorio), status=erro.status,
                 mensagem=f"Falha de rede ao falar com a Meta: {mascarar(erro.mensagem)}")
        return d
    err = None
    if isinstance(erro, Resposta):
        d["status"] = erro.status
        try:
            corpo = erro.json()
        except ValueError:
            corpo = {}
        err = corpo.get("error") if isinstance(corpo, dict) else None
        if err is None and not erro.ok:
            d.update(categoria="http", transitorio=erro.status >= 500,
                     mensagem=f"HTTP {erro.status} da Meta sem detalhe"
                              + (f": {mascarar(str(erro.dados))[:160]}" if erro.dados else ""))
            return d
    elif isinstance(erro, dict):
        err = erro.get("error", erro)
    elif isinstance(erro, BaseException):
        d.update(categoria="excecao", mensagem=f"Erro inesperado: {mascarar(str(erro))[:200]}")
        return d
    if not isinstance(err, dict):
        err = {"message": str(err or "")}
    codigo = _int(err.get("code"))
    sub = _int(err.get("error_subcode"))
    tipo = err.get("type")
    msg = mascarar(str(err.get("message") or err.get("error_user_msg") or ""))
    titulo = err.get("error_user_title")
    d.update(codigo=codigo, subcodigo=sub, tipo=tipo, mensagem_meta=msg, fbtrace=err.get("fbtrace_id"))
    cod_str = f"código {codigo}" + (f"/{sub}" if sub else "") if codigo is not None else "sem código"

    reel = CODIGOS_REEL.get(codigo) or CODIGOS_REEL.get(sub)
    if reel:
        d.update(categoria="reel", mensagem=f"{reel} ({cod_str}).")
    elif codigo in CODIGOS_TOKEN:
        d.update(categoria="token",
                 mensagem=f"Token da Página vencido ou inválido ({cod_str}). Gere outro com "
                          f"`hp publicar facebook-token` e cole em facebook_token_usuario.txt. "
                          f"Meta: {msg}".rstrip(": "))
    elif codigo == 10 or (codigo is not None and 200 <= codigo <= 299):
        perm, disse = _permissao_faltando(msg, acao)
        d["permissao"] = perm or None
        if perm and disse:
            texto = f"Falta a permissão {perm} no token da Página ({cod_str})."
        elif perm:
            texto = (f"Permissão negada ({cod_str}); a Meta não disse qual, mas para {acao} "
                     f"é preciso {' + '.join(PERMISSOES[acao])}.")
        else:
            texto = f"Permissão negada ({cod_str})."
        d.update(categoria="permissao",
                 mensagem=texto + " No app \"HP Publicador\" (developers.facebook.com) peça essa "
                                  "permissão e gere o token da Página de novo." + (f" Meta: {msg}" if msg else ""))
    elif codigo in CODIGOS_LIMITE:
        d.update(categoria="limite", transitorio=True,
                 mensagem=f"Limite de chamadas da Meta atingido ({cod_str}). Espere uns minutos "
                          f"(até 1 hora) e tente de novo; não repita em massa.")
    elif codigo in CODIGOS_BLOQUEIO:
        d.update(categoria="bloqueio",
                 mensagem=f"A Meta bloqueou esta ação temporariamente ({cod_str}: considerada abusiva "
                          f"ou spam). Pare por algumas horas e não insista." + (f" Meta: {msg}" if msg else ""))
    elif codigo == 100:
        if sub == 33 or "does not exist" in msg.lower() or "cannot be loaded" in msg.lower():
            d.update(categoria="nao_existe",
                     mensagem=f"O post/comentário não existe mais ou o token não o enxerga ({cod_str}).")
        else:
            d.update(categoria="parametro",
                     mensagem=f"Parâmetro inválido no pedido ({cod_str}): {msg}")
    elif codigo in CODIGOS_PASSAGEIRO:
        d.update(categoria="passageiro", transitorio=True,
                 mensagem=f"Erro passageiro da Meta ({cod_str}); tente de novo em alguns minutos."
                          + (f" Meta: {msg}" if msg else ""))
    else:
        partes = [f"Erro da Meta ({cod_str}" + (f", tipo {tipo}" if tipo else "") + ")"]
        if titulo:
            partes.append(str(titulo))
        if msg:
            partes.append(msg)
        d.update(categoria="generico", mensagem=": ".join(partes))
    if d.get("fbtrace"):
        d["mensagem"] += f" [fbtrace {d['fbtrace']}]"
    d["mensagem"] = mascarar(d["mensagem"])
    return d


def erro_graph(erro, acao: str | None = None) -> str:
    """Resposta de erro da Graph API (ou ErroRede) -> uma frase em português, sem token."""
    return detalhar_erro_graph(erro, acao)["mensagem"]


# ----------------------------------------------------------------------------- HTTP
def _url_sem_token(url: str) -> tuple[str, dict]:
    """Tira access_token (e afins) da URL do paging.next; devolve (url limpa, parâmetros restantes)."""
    partes = urlsplit(url)
    pares = [(k, v) for k, v in parse_qsl(partes.query, keep_blank_values=True)
             if k.lower() not in ("access_token", "appsecret_proof")]
    limpa = urlunsplit((partes.scheme, partes.netloc, partes.path, "", ""))
    return limpa, dict(pares)


def _pedir(cliente, metodo: str, url: str, token: str, *, consulta: dict | None = None,
           form: dict | None = None, tempo: float = 60, acao: str | None = None) -> dict:
    """cliente.pedir com o token no lugar certo; devolve o JSON ou levanta ErroGraph."""
    metodo = metodo.upper()
    consulta = dict(consulta or {})
    if metodo == "POST":
        form = dict(form or {})
        form["access_token"] = token
    else:
        consulta["access_token"] = token
    try:
        resp = cliente.pedir(metodo, url, consulta=consulta or None, form=form or None, tempo=tempo)
    except ErroRede as e:
        raise ErroGraph(detalhar_erro_graph(e, acao)) from None
    try:
        corpo = resp.json()
    except ValueError:
        corpo = None
    if not resp.ok or (isinstance(corpo, dict) and "error" in corpo):
        raise ErroGraph(detalhar_erro_graph(resp, acao))
    return corpo if isinstance(corpo, dict) else {"dados": corpo}


def _paginar(cliente, token: str, url: str, consulta: dict, *, max_paginas: int = MAX_PAGINAS,
             limite: int | None = None, acao: str | None = None):
    """Rende os itens de `data` seguindo paging.next (token sempre fora da URL)."""
    n = 0
    consulta = dict(consulta)
    for _ in range(max_paginas):
        corpo = _pedir(cliente, "GET", url, token, consulta=consulta, acao=acao)
        for item in corpo.get("data") or []:
            yield item
            n += 1
            if limite and n >= limite:
                return
        prox = (corpo.get("paging") or {}).get("next")
        if not prox:
            return
        url, consulta = _url_sem_token(prox)


def _entrada_erro(e: ErroGraph, **extra) -> dict:
    return entrada("erro", erro=e.mensagem, codigo=e.codigo, categoria=e.categoria,
                   permissao=e.permissao, transitorio=e.transitorio, **extra)


# ----------------------------------------------------------------------------- horas
_RX_ISO = re.compile(r"^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::(\d{2}))?(?:\.\d+)?"
                     r"(Z|[+-]\d{2}:?\d{2})?$")


def ler_hora(valor, fuso_padrao=FUSO) -> datetime | None:
    """epoch (int/float/str de dígitos), ISO da Meta ("2026-10-02T18:30:00+0000"), "AAAA-MM-DD HH:MM"
    (Brasília) ou datetime -> datetime com fuso. Naive = Brasília."""
    if valor is None or valor == "":
        return None
    if isinstance(valor, datetime):
        return valor if valor.tzinfo else valor.replace(tzinfo=fuso_padrao)
    if isinstance(valor, (int, float)) or (isinstance(valor, str) and valor.strip().isdigit()):
        try:
            return datetime.fromtimestamp(float(valor), tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    m = _RX_ISO.match(str(valor).strip())
    if not m:
        return None
    a, mes, d, h, mi, s, tz = m.groups()
    dt = datetime(int(a), int(mes), int(d), int(h), int(mi), int(s or 0))
    if not tz or tz == "Z":
        return dt.replace(tzinfo=timezone.utc if tz == "Z" else fuso_padrao)
    sinal = 1 if tz[0] == "+" else -1
    tz = tz[1:].replace(":", "")
    return dt.replace(tzinfo=timezone(sinal * timedelta(hours=int(tz[:2]), minutes=int(tz[2:]))))


def hora_brasilia(valor) -> str | None:
    """-> "AAAA-MM-DD HH:MM" em Brasília (ou None)."""
    dt = ler_hora(valor)
    return dt.astimezone(FUSO).strftime("%Y-%m-%d %H:%M") if dt else None


def epoch_utc(valor) -> int | None:
    dt = ler_hora(valor)
    return int(dt.astimezone(timezone.utc).timestamp()) if dt else None


# ----------------------------------------------------------------------------- C1 agenda
def _link_fb(url: str | None) -> str | None:
    if not url:
        return None
    return "https://www.facebook.com" + url if url.startswith("/") else url


def _normalizar_agendado(bruto: dict, tipo: str) -> dict:
    anexos = ((bruto.get("attachments") or {}).get("data") or [{}])
    media = (anexos[0] or {}).get("media_type") if anexos else None
    link = _link_fb(bruto.get("permalink_url"))
    if tipo == "post" and (media == "video_reel" or (link and "/reel/" in link)):
        tipo = "reel"
    texto = bruto.get("message") or bruto.get("description") or bruto.get("title") or ""
    return {"id": str(bruto.get("id") or ""), "tipo": tipo,
            "quando": hora_brasilia(bruto.get("scheduled_publish_time")),
            "texto": texto, "link": link, "bruto": bruto}


def listar_agendados(cliente, token: str, pagina_id: str, *, incluir_reels: bool = True,
                     max_paginas: int = MAX_PAGINAS, avisos: list | None = None) -> list[dict]:
    """Posts agendados da Página: [{id, tipo (post|reel), quando (Brasília "AAAA-MM-DD HH:MM"),
    texto, link, bruto}], em ordem de hora. Levanta ErroGraph (português) se a lista principal falhar.

    Reels agendados: a doc oficial (DOCS["video_reels"], DOC_CONFERIDA_EM) não diz como listá-los;
    fica a tentativa GET /{page}/video_reels filtrando scheduled_publish_time no futuro, cada item
    com "confirmar": True. Se essa chamada falhar, entra em `avisos` e a lista principal vale."""
    itens: list[dict] = []
    url = f"{API}/{pagina_id}/scheduled_posts"
    for bruto in _paginar(cliente, token, url, {"fields": CAMPOS_AGENDADOS, "limit": LIMITE_PAGINA},
                          max_paginas=max_paginas, acao="listar_agendados"):
        itens.append(_normalizar_agendado(bruto, "post"))
    if incluir_reels:
        try:
            url = f"{API}/{pagina_id}/video_reels"
            for bruto in _paginar(cliente, token, url,
                                  {"fields": CAMPOS_REELS_AGENDADOS, "limit": LIMITE_PAGINA},
                                  max_paginas=max_paginas, acao="listar_agendados"):
                if not bruto.get("scheduled_publish_time"):
                    continue
                st = bruto.get("video_status")
                st = (st.get("video_status") if isinstance(st, dict) else st) or ""
                if str(st).lower() in ("published", "live", "ready_published"):
                    continue
                it = _normalizar_agendado(bruto, "reel")
                it["confirmar"] = not REELS_AGENDADOS_CONFIRMADO
                itens.append(it)
        except ErroGraph as e:
            if avisos is not None:
                avisos.append(f"reels agendados não listados: {e.mensagem}")
    vistos: set[str] = set()
    saida = []
    for it in itens:
        chave = it["id"].split("_")[-1]
        if chave in vistos:
            continue
        vistos.add(chave)
        saida.append(it)
    saida.sort(key=lambda i: (i["quando"] or "9999", i["id"]))
    return saida


def cancelar_agendado(cliente, token: str, post_id: str) -> dict:
    """DELETE /{id} -> entrada("cancelado") ou entrada("erro", erro=português)."""
    try:
        corpo = _pedir(cliente, "DELETE", f"{API}/{post_id}", token, acao="cancelar_agendado")
    except ErroGraph as e:
        return _entrada_erro(e, id=post_id)
    if corpo.get("success") is False:
        return entrada("erro", id=post_id, erro="A Meta respondeu success=false ao cancelar.")
    return entrada("cancelado", id=post_id)


def validar_janela(nova_hora, agora=None, tipo: str = "post") -> str | None:
    """None se a hora cabe na janela da Meta; senão a frase em português do que está errado."""
    nova = ler_hora(nova_hora)
    if nova is None:
        return f"Hora inválida: {nova_hora!r} (use \"AAAA-MM-DD HH:MM\" de Brasília)."
    agora = ler_hora(agora) if agora is not None else _agora_brasilia()
    dias_max = JANELA_DIAS_REEL if tipo == "reel" else JANELA_DIAS_POST
    delta = nova - agora
    minutos = delta.total_seconds() / 60
    janela = f"entre {JANELA_MINUTOS_MIN} minutos e {dias_max} dias a partir de agora"
    if minutos < JANELA_MINUTOS_MIN:
        if minutos < 0:
            quanto = f"já passou ({hora_brasilia(nova)} é antes de agora)"
        else:
            quanto = f"está a só {int(minutos)} min"
        return (f"A Meta só aceita agendar {'reel' if tipo == 'reel' else 'post'} {janela}; "
                f"a hora pedida ({hora_brasilia(nova)}) {quanto}.")
    if delta > timedelta(days=dias_max):
        return (f"A Meta só aceita agendar {'reel' if tipo == 'reel' else 'post'} {janela}; "
                f"a hora pedida ({hora_brasilia(nova)}) está a {delta.days} dias.")
    return None


def reagendar(cliente, token: str, post_id: str, nova_hora, agora=None, tipo: str = "post") -> dict:
    """POST /{id} com scheduled_publish_time (epoch UTC) + is_published=false.
    nova_hora: "AAAA-MM-DD HH:MM" (Brasília) ou datetime; agora: injetado (testes); tipo: post|reel."""
    problema = validar_janela(nova_hora, agora, tipo)
    if problema:
        return entrada("erro", id=post_id, erro=problema, categoria="janela")
    epoch = epoch_utc(nova_hora)
    form = {"scheduled_publish_time": epoch, "is_published": "false"}
    try:
        corpo = _pedir(cliente, "POST", f"{API}/{post_id}", token, form=form, acao="reagendar")
    except ErroGraph as e:
        return _entrada_erro(e, id=post_id)
    if corpo.get("success") is False:
        return entrada("erro", id=post_id, erro="A Meta respondeu success=false ao reagendar.")
    return entrada("agendado", id=post_id, quando=hora_brasilia(nova_hora), epoch=epoch, tipo=tipo)


# ----------------------------------------------------------------------------- comparar
_RX_ID_LINK = [re.compile(r"/posts/(?:pfbid)?(\d{6,})"), re.compile(r"/videos/(\d{6,})"),
               re.compile(r"/reel/(\d{6,})"), re.compile(r"story_fbid=(\d{6,})"),
               re.compile(r"[?&]v=(\d{6,})"), re.compile(r"/(\d{6,})/?$")]


def _id_do_link(link: str | None) -> str | None:
    if not link:
        return None
    for rx in _RX_ID_LINK:
        m = rx.search(str(link))
        if m:
            return m.group(1)
    return None


def _sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def chave_texto(texto, tamanho: int = 40) -> str:
    """Início do texto normalizado (minúsculo, sem acento, só letras/números) para casar posts."""
    s = _sem_acento(str(texto or "")).lower()
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return s[:tamanho].strip()


def _textos_casam(a: str, b: str, minimo: int = 8) -> bool:
    if len(a) < minimo or len(b) < minimo:
        return False
    return a.startswith(b) or b.startswith(a)


def itens_do_agendados_json(dados) -> list[dict]:
    """{"itens": [...]} (real), lista solta, {"posts": [...]}, {"agendados": [...]} ou Path -> itens."""
    if isinstance(dados, (str, Path)):
        dados = ler_json(Path(dados), [])
    if isinstance(dados, dict):
        lista = dados.get("itens")
        if not isinstance(lista, list):
            lista = dados.get("posts") or dados.get("agendados") or []
    else:
        lista = dados if isinstance(dados, list) else []
    return [x for x in lista if isinstance(x, dict)]


def _link_facebook_do_item(it: dict) -> str | None:
    links = it.get("links") or it.get("urls") or {}
    if isinstance(links, list):
        for l in links:
            if isinstance(l, dict) and str(l.get("rede", "")).lower() in ("facebook", "fb"):
                return l.get("url") or l.get("link")
        return None
    if isinstance(links, dict):
        return links.get("facebook") or links.get("fb")
    return None


def _item_json_normalizado(it: dict) -> dict:
    redes = it.get("redes")
    if isinstance(redes, dict):
        redes = list(redes)
    redes = [str(r).lower() for r in (redes or [])]
    link = _link_facebook_do_item(it)
    ids = it.get("ids") if isinstance(it.get("ids"), dict) else {}
    id_fb = ids.get("facebook") or _id_do_link(link)
    quando = (it.get("data_post") or it.get("quando") or it.get("horario") or it.get("data_hora")
              or (f"{it.get('data')} {it.get('hora')}" if it.get("data") and it.get("hora") else it.get("data")))
    texto = it.get("titulo") or it.get("legenda") or it.get("texto") or it.get("title") or ""
    relevante = (not redes) or any(r in ("facebook", "fb") for r in redes) or bool(link)
    return {"id_json": it.get("id"), "titulo": texto, "chave": chave_texto(texto),
            "quando_json": hora_brasilia(quando), "dt": ler_hora(quando), "id_fb": str(id_fb) if id_fb else None,
            "link": link, "relevante": relevante, "status": it.get("status")}


def _diferenca_min(a: datetime | None, b: datetime | None) -> int | None:
    if a is None or b is None:
        return None
    return int(round(abs((a - b).total_seconds()) / 60))


def comparar_com_agendados_json(agendados_api: list[dict], agendados_json_do_canal,
                                tolerancia_min: int = 5) -> dict:
    """Agenda da API (listar_agendados) x agendados.json do canal ->
    {"buracos": [itens do JSON sem post na API], "duplicados": [mesmo texto/hora 2x na API],
     "hora_errada": [pares com diferença > tolerância], "sobras": [na API e não no JSON],
     "ok": [...], "ignorados": [itens do JSON que não são do Facebook], "resumo": "…"}.
    Casa por id (link do Facebook / ids.facebook) ou pelo início do texto normalizado."""
    api = []
    for a in agendados_api or []:
        api.append({"id_api": str(a.get("id") or ""), "sufixo": str(a.get("id") or "").split("_")[-1],
                    "chave": chave_texto(a.get("texto")), "quando_api": a.get("quando"),
                    "dt": ler_hora(a.get("quando")), "tipo": a.get("tipo"), "link": a.get("link"),
                    "texto": (a.get("texto") or "")[:80]})
    itens = [_item_json_normalizado(it) for it in itens_do_agendados_json(agendados_json_do_canal)]

    # duplicados na API: mesma chave de texto e hora dentro da tolerância
    duplicados = []
    usados_dup: set[int] = set()
    for i, a in enumerate(api):
        if i in usados_dup or not a["chave"]:
            continue
        grupo = [a]
        for j in range(i + 1, len(api)):
            b = api[j]
            if j in usados_dup or not _textos_casam(a["chave"], b["chave"]):
                continue
            dif = _diferenca_min(a["dt"], b["dt"])
            if dif is not None and dif <= tolerancia_min:
                grupo.append(b)
                usados_dup.add(j)
        if len(grupo) > 1:
            usados_dup.add(i)
            duplicados.append({"ids": [g["id_api"] for g in grupo], "quando": a["quando_api"],
                               "texto": a["texto"], "quantos": len(grupo)})

    ok, hora_errada, buracos, ignorados = [], [], [], []
    casados_api: set[int] = set()
    for it in itens:
        if not it["relevante"]:
            ignorados.append({"id_json": it["id_json"], "titulo": it["titulo"],
                              "motivo": "não é do Facebook (redes sem facebook e sem link)"})
            continue
        if str(it.get("status") or "").lower() in ("cancelado", "cancelada", "erro", "removido"):
            ignorados.append({"id_json": it["id_json"], "titulo": it["titulo"],
                              "motivo": f"status {it['status']}"})
            continue
        achado = None
        if it["id_fb"]:
            for i, a in enumerate(api):
                if i in casados_api:
                    continue
                if a["sufixo"] == it["id_fb"] or a["id_api"] == it["id_fb"] or \
                        (it["link"] and a["link"] and it["link"].rstrip("/") == a["link"].rstrip("/")):
                    achado = i
                    break
        if achado is None and it["chave"]:
            candidatos = [i for i, a in enumerate(api)
                          if i not in casados_api and _textos_casam(a["chave"], it["chave"])]
            if candidatos:  # o de hora mais próxima
                candidatos.sort(key=lambda i: _diferenca_min(api[i]["dt"], it["dt"]) or 0)
                achado = candidatos[0]
        if achado is None:
            buracos.append({"id_json": it["id_json"], "titulo": it["titulo"], "quando_json": it["quando_json"],
                            "motivo": "está no agendados.json e não apareceu na agenda da Página"})
            continue
        casados_api.add(achado)
        a = api[achado]
        dif = _diferenca_min(a["dt"], it["dt"])
        par = {"id_api": a["id_api"], "id_json": it["id_json"], "quando_api": a["quando_api"],
               "quando_json": it["quando_json"], "texto": a["texto"] or it["titulo"], "diferenca_min": dif}
        if dif is not None and dif > tolerancia_min:
            par["motivo"] = f"hora diferente: JSON {it['quando_json']} x Página {a['quando_api']} ({dif} min)"
            hora_errada.append(par)
        else:
            ok.append(par)
    sobras = [{"id_api": a["id_api"], "quando_api": a["quando_api"], "texto": a["texto"], "tipo": a["tipo"],
               "motivo": "está na agenda da Página e não no agendados.json"}
              for i, a in enumerate(api) if i not in casados_api]
    resumo = (f"{len(ok)} ok, {len(buracos)} buraco(s), {len(duplicados)} duplicado(s), "
              f"{len(hora_errada)} hora(s) errada(s), {len(sobras)} sobra(s) na Página"
              + (f", {len(ignorados)} ignorado(s)" if ignorados else "") + ".")
    return {"buracos": buracos, "duplicados": duplicados, "hora_errada": hora_errada, "sobras": sobras,
            "ok": ok, "ignorados": ignorados, "tolerancia_min": tolerancia_min, "resumo": resumo}
