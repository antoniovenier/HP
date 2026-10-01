"""youtube_extra — o que falta no YouTube além do envio (que o PC já faz).

O QUE FAZ
    B1  playlist_do_canal()      acha (ou cria, sem duplicar) a playlist de um canal pelo título
        adicionar_na_playlist()  põe um vídeo na playlist (confere antes; "já está" não é falha)
    B2  atualizar_video()        corrige título/descrição/tags/categoria/agenda de vídeo já enviado
    B3  conferir_lote()          confere N vídeos de uma vez (1 chamada por 50 ids) com o diagnóstico
                                 do PC: "travado como privado (projeto sem auditoria)", rejeitado, falhou…
    B4  transcricao_para_srt()   transcrição (formato 4.5) -> SRT, função pura
        enviar_legenda()         captions.insert (400 unidades!) — DESLIGADA por padrão
    B5  registro_de_cota()       soma as unidades gastas por tipo de chamada e avisa a 80 % do dia
        Contador                 contador injetável: cada função registra suas chamadas nele
    erro_youtube()               traduz erro HTTP/JSON do Google para português de leigo

USO (o PC injeta o cliente e o token; aqui ninguém faz rede nem lê segredo):
    from publicar_extra.youtube_extra import playlist_do_canal, adicionar_na_playlist, Contador
    cont = Contador()
    pid = playlist_do_canal(cliente, token_de("gta"), "gta", "GTA 6 — notícias", registrar=cont.registrar)
    r = adicionar_na_playlist(cliente, token_de("gta"), pid, "abc123XYZ", registrar=cont.registrar)
    print(cont.resumo()["mensagem"])

REGRAS
    - Token só no cabeçalho `Authorization: Bearer …` (nunca na URL nem na consulta); toda mensagem
      de erro passa por mascarar(); o módulo NUNCA lê refresh token (isso é do PC: token_de(canal)).
    - Nada de rede própria: tudo passa por cliente.pedir(...) (contrato em contrato_pc.py).
    - Resultados no formato entrada() do PC: {"status", "link", "id", "erro", ...}.
    - Validação (título ≤ 100 sem < >, descrição ≤ 5.000 bytes, tags ≤ 500 contando como o YouTube,
      categoria numérica) acontece ANTES de qualquer chamada.
    - Custos de cota confirmados na documentação oficial em CUSTOS_CONFIRMADOS_EM (tabela CUSTOS).
    - publishAt só vale com privacyStatus=private e vídeo nunca publicado; vai em UTC "…Z".
    - Caminho do PC só na constante NOME_CACHE_PLAYLISTS (abaixo de hpbase.pasta_app()).
"""
from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from hpbase import FUSO, escrever_json, ler_json, pasta_app
from hpbase import agora as _agora_brasilia

from .contrato_pc import ErroRede, Resposta, entrada, mascarar

API = "https://www.googleapis.com/youtube/v3"
API_UPLOAD = "https://www.googleapis.com/upload/youtube/v3"
# H:\HypadoLocal\app\publicar\youtube_playlists.json  (pasta_app() honra HP_LOCAL nos testes)
NOME_CACHE_PLAYLISTS = Path("publicar") / "youtube_playlists.json"

LIMITE_TITULO = 100          # caracteres
LIMITE_DESCRICAO_BYTES = 5000
LIMITE_TAGS = 500            # caracteres somados, contados como o YouTube (ver contar_tags)
IDS_POR_CHAMADA = 50

# ----------------------------------------------------------------------------- cota (B5)
# Confirmado lendo as páginas oficiais em CUSTOS_CONFIRMADOS_EM (curl, só leitura). Páginas
# "Last updated 2026-09-14/15/16 UTC". O videos.insert tem balde próprio (100 envios/dia,
# custo 1 unidade NESSE balde) e NÃO gasta as 10.000 unidades do dia — o PC já tinha visto
# isso em 15/09/2026. Valor sem confirmação ficaria {"custo": N, "confirmar": True}.
CUSTOS_CONFIRMADOS_EM = "2026-10-01"
_URL_QUOTA = "https://developers.google.com/youtube/v3/determine_quota_cost"
_URL_REF = "https://developers.google.com/youtube/v3/docs/"
LIMITE_DIA = 10000           # unidades por projeto por dia; zera à meia-noite da Califórnia (PT)
LIMITE_ENVIOS_DIA = 100      # balde do videos.insert (e do search.list)


def _c(custo, fonte, balde=None):
    d = {"custo": custo, "fonte": fonte, "confirmado_em": CUSTOS_CONFIRMADOS_EM, "confirmar": False}
    if balde:
        d["balde"] = balde
    return d


CUSTOS = {
    "videos.list": _c(1, _URL_QUOTA),
    "channels.list": _c(1, _URL_QUOTA),
    "playlists.list": _c(1, _URL_REF + "playlists/list"),
    "playlistItems.list": _c(1, _URL_QUOTA),
    "captions.list": _c(50, _URL_QUOTA),
    "thumbnails.set": _c(50, _URL_QUOTA),
    "videos.update": _c(50, _URL_REF + "videos/update"),
    "playlists.insert": _c(50, _URL_REF + "playlists/insert"),
    "playlistItems.insert": _c(50, _URL_REF + "playlistItems/insert"),
    "captions.insert": _c(400, _URL_REF + "captions/insert"),
    # balde próprio: "100 calls per day. A call to this method has a quota cost of 1 unit in the
    # Video Uploads quota bucket" (videos/insert, 2026-10-01). Não entra no total das 10.000.
    "videos.insert": _c(0, _URL_REF + "videos/insert", balde="envios"),
}


class Contador:
    """Contador injetável de chamadas: `registrar(tipo)` é o que cada função deste módulo chama."""

    def __init__(self):
        self.chamadas: list[str] = []

    def registrar(self, tipo: str) -> None:
        self.chamadas.append(str(tipo))

    def resumo(self, limite_dia: int = LIMITE_DIA, aviso_em: float = 0.8) -> dict:
        return registro_de_cota(self.chamadas, limite_dia, aviso_em)


def registro_de_cota(chamadas, limite_dia: int = LIMITE_DIA, aviso_em: float = 0.8) -> dict:
    """Soma as unidades por tipo de chamada e avisa a `aviso_em` (80 %) do dia.

    `chamadas` = lista de tipos ("videos.list", "videos.update", …) ou dict {tipo: quantidade}.
    Tipo desconhecido conta 1 unidade (a API cobra pelo menos 1 por pedido, até inválido) e sai
    em "desconhecidos". videos.insert vai no balde "envios" (100/dia), fora do total.
    """
    if isinstance(chamadas, dict):
        contagem = Counter({str(k): int(v) for k, v in chamadas.items()})
    else:
        contagem = Counter(str(t) for t in chamadas)
    total, por_tipo, desconhecidos, confirmar, envios = 0, {}, [], [], 0
    for tipo, n in sorted(contagem.items()):
        regra = CUSTOS.get(tipo)
        if regra is None:
            unidades = n
            desconhecidos.append(tipo)
        elif regra.get("balde") == "envios":
            unidades = 0
            envios += n
        else:
            unidades = regra["custo"] * n
        if regra and regra.get("confirmar"):
            confirmar.append(tipo)
        por_tipo[tipo] = {"n": n, "unidades": unidades}
        total += unidades
    pct = (100.0 * total / limite_dia) if limite_dia else 0.0
    avisar = limite_dia > 0 and total >= limite_dia * aviso_em
    msg = f"cota do YouTube: {total} de {limite_dia} unidades usadas ({pct:.0f} %)"
    if envios:
        msg += f"; {envios} de {LIMITE_ENVIOS_DIA} envios (balde do videos.insert)"
    if avisar:
        msg += (f" — AVISO: passou de {int(aviso_em * 100)} % do dia; deixe para amanhã o que não é "
                f"urgente (zera à meia-noite da Califórnia)")
    if envios >= LIMITE_ENVIOS_DIA * aviso_em:
        avisar = True
        msg += f" — AVISO: {envios} envios, perto do limite de {LIMITE_ENVIOS_DIA} por dia"
    if desconhecidos:
        msg += f"; tipos sem custo conhecido (contados como 1): {', '.join(desconhecidos)}"
    return {"total": total, "por_tipo": por_tipo, "avisar": avisar, "mensagem": msg,
            "envios": envios, "limite_dia": limite_dia, "restante": max(limite_dia - total, 0),
            "desconhecidos": desconhecidos, "confirmar": confirmar}


# ---------------------------------------------------------------------- erros (português)
MOTIVOS = {
    "quotaExceeded": ("cota diária da API do YouTube esgotada (10.000 unidades); "
                      "volta à meia-noite da Califórnia"),
    "dailyLimitExceeded": ("cota diária da API do YouTube esgotada (10.000 unidades); "
                           "volta à meia-noite da Califórnia"),
    "rateLimitExceeded": "muitas chamadas seguidas na API do YouTube; espere um minuto e tente de novo",
    "userRateLimitExceeded": "muitas chamadas seguidas na API do YouTube; espere um minuto e tente de novo",
    "uploadLimitExceeded": ("limite de envios do YouTube atingido (100 envios por dia no balde do "
                            "videos.insert); volta à meia-noite da Califórnia"),
    "duplicate": "já existe igual no YouTube (recusado como duplicado)",
    "videoAlreadyInPlaylist": "o vídeo já está na playlist",
    "captionExists": "o vídeo já tem legenda com esse idioma e nome",
    "authError": "token vencido: o PC renova",
    "invalidCredentials": "token vencido: o PC renova",
    "expired": "token vencido: o PC renova",
    "forbidden": ("sem permissão (403): escopo do OAuth insuficiente, canal errado ou projeto sem "
                  "auditoria da API"),
    "insufficientPermissions": ("sem permissão (403): escopo do OAuth insuficiente (precisa do "
                                "youtube.force-ssl) ou projeto sem auditoria"),
    "forbiddenPrivacySetting": ("o YouTube não aceitou essa privacidade (403): projeto sem auditoria "
                                "deixa o vídeo preso como privado"),
    "playlistItemsNotAccessible": "sem permissão para mexer nessa playlist (403)",
    "playlistContainsMaximumNumberOfVideos": "a playlist já está cheia",
    "playlistNotFound": "playlist não encontrada no YouTube",
    "videoNotFound": "vídeo não encontrado no YouTube",
    "invalidTitle": "título inválido ou vazio (máximo 100 caracteres, sem < e >)",
    "invalidDescription": "descrição inválida (máximo 5.000 bytes, sem < e >)",
    "invalidTags": "tags inválidas (máximo 500 caracteres somados)",
    "invalidCategoryId": "categoria inválida (tem que ser o número de uma categoria do YouTube)",
    "invalidPublishAt": "horário de publicação inválido (só com vídeo privado, no futuro, em UTC)",
    "invalidVideoMetadata": "dados do vídeo inválidos",
    "contentRequired": "legenda vazia",
    "nameTooLong": "nome da legenda muito longo (máximo 150 caracteres)",
    "invalidMetadata": "dados da legenda inválidos (idioma, nome ou id do vídeo)",
}
_POR_STATUS = {
    401: "token vencido: o PC renova",
    403: "permissão negada (403): escopo, canal ou auditoria do projeto",
    404: "não encontrado no YouTube",
    409: "já existe (conflito)",
    429: "muitas chamadas seguidas; espere um minuto",
}
_MOTIVOS_JA_EXISTE = ("duplicate", "videoAlreadyInPlaylist", "captionExists")


class ErroYouTube(Exception):
    """Erro da API já traduzido (mensagem sem segredo). `.status`, `.motivo` (reason do Google)."""

    def __init__(self, mensagem: str, status: int | None = None, motivo: str | None = None):
        self.mensagem = mascarar(str(mensagem))
        self.status = status
        self.motivo = motivo
        super().__init__(self.mensagem)

    def __str__(self) -> str:
        return self.mensagem

    @property
    def ja_existe(self) -> bool:
        return self.motivo in _MOTIVOS_JA_EXISTE or self.status == 409


def _detalhes_erro(x) -> tuple[int | None, str | None, str]:
    """(status, reason do Google, mensagem crua) de uma Resposta ou ErroRede."""
    status, motivo, texto = None, None, ""
    if isinstance(x, Resposta):
        status = x.status
        dados = None
        try:
            dados = x.json()
        except ValueError:
            texto = str(x.dados or "")
        if isinstance(dados, dict):
            err = dados.get("error")
            if isinstance(err, dict):
                texto = str(err.get("message") or "")
                lista = err.get("errors") or []
                if lista and isinstance(lista[0], dict):
                    motivo = lista[0].get("reason")
                if not motivo:
                    motivo = err.get("status")
            elif err is not None:
                texto = str(err)
            else:
                texto = str(dados.get("message") or "")
    elif isinstance(x, ErroRede):
        status = x.status
        texto = x.mensagem
    else:
        texto = str(x)
    if not motivo:
        for m in MOTIVOS:
            if re.search(r"\b" + re.escape(m) + r"\b", texto):
                motivo = m
                break
    return status, motivo, texto


def erro_youtube(x) -> str:
    """Resposta 4xx/5xx, ErroRede ou exceção -> frase em português (sem segredo)."""
    status, motivo, texto = _detalhes_erro(x)
    if motivo in MOTIVOS:
        base = MOTIVOS[motivo]
    elif status in _POR_STATUS:
        base = _POR_STATUS[status]
    elif status is not None and status >= 500:
        base = "YouTube fora do ar (HTTP 5xx); tente de novo mais tarde"
    elif status == 400:
        base = "pedido inválido para a API do YouTube"
    elif isinstance(x, ErroRede) and status is None:
        base = "falha de rede ao falar com o YouTube"
    else:
        base = "erro na API do YouTube"
    detalhe = " ".join(p for p in (f"HTTP {status}" if status else "", motivo or "") if p)
    msg = base
    if detalhe:
        msg += f" ({detalhe})"
    if texto and not motivo and status not in _POR_STATUS:
        msg += f": {texto[:160]}"
    return mascarar(msg)


# -------------------------------------------------------------------------- chamada base
def _cabecalhos(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}


def _chamar(cliente, token: str, metodo: str, url: str, tipo: str, registrar=None, *,
            consulta=None, json_=None, corpo=None, cabecalhos=None, tempo: float = 120) -> Resposta:
    """Uma chamada à Data API: registra a cota, põe o Bearer no cabeçalho e traduz falha."""
    if registrar is not None:
        registrar(tipo)
    cab = _cabecalhos(token)
    if cabecalhos:
        cab.update(cabecalhos)
    try:
        r = cliente.pedir(metodo, url, consulta=consulta, json_=json_, corpo=corpo,
                          cabecalhos=cab, tempo=tempo)
    except ErroRede as e:
        st, motivo, _ = _detalhes_erro(e)
        raise ErroYouTube(erro_youtube(e), st, motivo) from None
    if r.status >= 400:
        st, motivo, _ = _detalhes_erro(r)
        raise ErroYouTube(erro_youtube(r), st, motivo)
    return r


def _json(r: Resposta) -> dict:
    try:
        d = r.json()
    except ValueError:
        return {}
    return d if isinstance(d, dict) else {}


def link_video(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def link_playlist(playlist_id: str, video_id: str | None = None) -> str:
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}&list={playlist_id}"
    return f"https://www.youtube.com/playlist?list={playlist_id}"


# ------------------------------------------------------------------------- datas (UTC/BR)
def _aware_brasilia(dt) -> datetime:
    """datetime (ou 'AAAA-MM-DD HH:MM' / ISO) de Brasília -> datetime com fuso."""
    if isinstance(dt, str):
        s = dt.strip().replace("T", " ")
        try:
            dt = datetime.strptime(s, "%Y-%m-%d %H:%M")
        except ValueError:
            dt = datetime.fromisoformat(dt.strip().replace("Z", "+00:00"))
    if not isinstance(dt, datetime):
        raise ValueError("publicar_em tem que ser datetime ou 'AAAA-MM-DD HH:MM' (Brasília)")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=FUSO)
    return dt


def para_utc_z(dt) -> str:
    """Brasília -> '2026-10-02T12:00:00Z' (o formato que a API aceita em status.publishAt)."""
    return _aware_brasilia(dt).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _de_utc(s) -> datetime | None:
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _brasilia_txt(dt: datetime | None) -> str | None:
    return dt.astimezone(FUSO).strftime("%Y-%m-%d %H:%M") if dt else None


def _agora(agora) -> datetime:
    if agora is None:
        return _agora_brasilia()
    return _aware_brasilia(agora)


# ----------------------------------------------------------------------- B1 playlists
def normalizar_titulo(t) -> str:
    """Sem acento, sem maiúscula, espaços colapsados — é assim que dois títulos são "iguais"."""
    s = unicodedata.normalize("NFKD", str(t or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.casefold().split())


class CacheArquivo:
    """Cache {canal: {titulo: id}} em JSON (padrão: app\\publicar\\youtube_playlists.json), atômico."""

    def __init__(self, caminho: Path | None = None):
        self.caminho = Path(caminho) if caminho else pasta_app() / NOME_CACHE_PLAYLISTS

    def ler(self) -> dict:
        d = ler_json(self.caminho, {})
        return d if isinstance(d, dict) else {}

    def gravar(self, dados: dict) -> None:
        escrever_json(self.caminho, dados)


class CacheMemoria:
    """Cache só em memória (testes e uso avulso)."""

    def __init__(self, dados: dict | None = None):
        self.dados = dict(dados or {})
        self.gravacoes = 0

    def ler(self) -> dict:
        return json.loads(json.dumps(self.dados))

    def gravar(self, dados: dict) -> None:
        self.dados = json.loads(json.dumps(dados))
        self.gravacoes += 1


def _cache_busca(dados: dict, canal: str, chave: str) -> str | None:
    for titulo, pid in (dados.get(canal) or {}).items():
        if normalizar_titulo(titulo) == chave and pid:
            return str(pid)
    return None


def playlist_do_canal(cliente, token: str, canal: str, titulo: str, criar: bool = True,
                      cache=None, registrar=None, descricao: str | None = None,
                      privacidade: str = "public") -> str | None:
    """Id da playlist com esse título no canal autorizado pelo token. NUNCA duplica:
    1) cache (`{canal: {titulo: id}}`), 2) playlists.list mine=true (todas as páginas),
    3) só então playlists.insert — e só se criar=True (senão devolve None).
    Levanta ErroYouTube (mensagem em português) se a API falhar."""
    chave = normalizar_titulo(titulo)
    if not chave:
        raise ValueError("título da playlist vazio")
    cache = cache if cache is not None else CacheArquivo()
    dados = cache.ler() or {}
    achado = _cache_busca(dados, canal, chave)
    if achado:
        return achado
    pagina = None
    while achado is None:
        consulta = {"part": "snippet", "mine": "true", "maxResults": IDS_POR_CHAMADA}
        if pagina:
            consulta["pageToken"] = pagina
        d = _json(_chamar(cliente, token, "GET", f"{API}/playlists", "playlists.list", registrar,
                          consulta=consulta))
        for it in d.get("items") or []:
            if normalizar_titulo((it.get("snippet") or {}).get("title")) == chave and it.get("id"):
                achado = str(it["id"])
                break
        pagina = d.get("nextPageToken")
        if not pagina:
            break
    if achado is None:
        if not criar:
            return None
        corpo = {"snippet": {"title": str(titulo).strip(), "description": descricao or ""},
                 "status": {"privacyStatus": privacidade}}
        d = _json(_chamar(cliente, token, "POST", f"{API}/playlists", "playlists.insert", registrar,
                          consulta={"part": "snippet,status"}, json_=corpo))
        if not d.get("id"):
            raise ErroYouTube("o YouTube criou a playlist mas não devolveu o id", motivo="semId")
        achado = str(d["id"])
    dados.setdefault(canal, {})[str(titulo).strip()] = achado
    cache.gravar(dados)
    return achado


def adicionar_na_playlist(cliente, token: str, playlist_id: str, video_id: str,
                          registrar=None) -> dict:
    """Põe o vídeo na playlist. Confere antes (playlistItems.list, 1 unidade) para não duplicar;
    "já está na playlist" (409/duplicate) devolve status ja_estava, não é falha."""
    link = link_playlist(playlist_id, video_id)
    try:
        d = _json(_chamar(cliente, token, "GET", f"{API}/playlistItems", "playlistItems.list",
                          registrar, consulta={"part": "snippet", "playlistId": playlist_id,
                                               "videoId": video_id, "maxResults": IDS_POR_CHAMADA}))
        itens = d.get("items") or []
        if itens:
            return entrada("ja_estava", link=link, id=itens[0].get("id"), playlist=playlist_id)
        corpo = {"snippet": {"playlistId": playlist_id,
                             "resourceId": {"kind": "youtube#video", "videoId": video_id}}}
        d = _json(_chamar(cliente, token, "POST", f"{API}/playlistItems", "playlistItems.insert",
                          registrar, consulta={"part": "snippet"}, json_=corpo))
    except ErroYouTube as e:
        if e.ja_existe:
            return entrada("ja_estava", link=link, id=None, playlist=playlist_id, aviso=str(e))
        return entrada("erro", link=link, erro=str(e), playlist=playlist_id)
    return entrada("adicionado", link=link, id=d.get("id"), playlist=playlist_id)


# ------------------------------------------------------------------ B2 atualizar vídeo
def contar_tags(tags) -> int:
    """Conta como o YouTube (docs videos#snippet.tags[], lida em 2026-10-01): soma dos tamanhos
    das tags + 1 vírgula entre cada par + 2 aspas em cada tag que tem espaço
    ("Foo-Baz" = 7, "Foo Baz" = 9)."""
    tags = [str(t) for t in (tags or [])]
    if not tags:
        return 0
    return sum(len(t) + (2 if " " in t else 0) for t in tags) + (len(tags) - 1)


def validar_metadados(titulo=None, descricao=None, tags=None, categoria=None) -> str | None:
    """Mensagem em português do primeiro problema, ou None. Só valida o que veio (não None)."""
    if titulo is not None:
        t = str(titulo)
        if not t.strip():
            return "título vazio"
        if len(t) > LIMITE_TITULO:
            return f"título com {len(t)} caracteres (máximo {LIMITE_TITULO})"
        if "<" in t or ">" in t:
            return "título não pode ter < nem > (o YouTube recusa)"
    if descricao is not None:
        d = str(descricao)
        n = len(d.encode("utf-8"))
        if n > LIMITE_DESCRICAO_BYTES:
            return (f"descrição com {n} bytes em UTF-8 (máximo {LIMITE_DESCRICAO_BYTES}; acento e "
                    f"emoji contam mais de 1 byte — são {len(d)} caracteres)")
        if "<" in d or ">" in d:
            return "descrição não pode ter < nem > (o YouTube recusa)"
    if tags is not None:
        if isinstance(tags, str):
            return "tags têm que ser uma lista de textos, não um texto só"
        lista = [str(t) for t in tags]
        if any(not t.strip() for t in lista):
            return "tag vazia na lista (o YouTube responde 400)"
        n = contar_tags(lista)
        if n > LIMITE_TAGS:
            return (f"tags somam {n} caracteres (máximo {LIMITE_TAGS}; vírgulas e aspas de tag com "
                    f"espaço contam)")
    if categoria is not None and not re.fullmatch(r"\d+", str(categoria).strip()):
        return f"categoria tem que ser o número da categoria do YouTube (ex.: 20 = Jogos), não {categoria!r}"
    return None


_STATUS_MUTAVEL = ("privacyStatus", "publishAt", "license", "embeddable", "publicStatsViewable",
                   "selfDeclaredMadeForKids", "containsSyntheticMedia")
_SNIPPET_MUTAVEL = ("title", "description", "tags", "categoryId", "defaultLanguage")


def atualizar_video(cliente, token: str, video_id: str, titulo=None, descricao=None, tags=None,
                    categoria=None, publicar_em=None, agora=None, registrar=None,
                    privacidade: str | None = None) -> dict:
    """Lê o vídeo (videos.list), mescla e manda videos.update com snippet e status COMPLETOS
    (a API apaga o que faltar na parte enviada; exige title e categoryId). publicar_em = datetime
    (ou 'AAAA-MM-DD HH:MM') de Brasília -> publishAt em UTC "Z" com privacyStatus=private.
    Valida antes de chamar a API; erro de validação sai como status "invalido" com 0 chamadas."""
    link = link_video(video_id)
    erro = validar_metadados(titulo, descricao, tags, categoria)
    if erro:
        return entrada("invalido", link=link, id=video_id, erro=erro)
    quando = None
    if publicar_em is not None:
        try:
            quando = _aware_brasilia(publicar_em)
        except ValueError as e:
            return entrada("invalido", link=link, id=video_id, erro=str(e))
        if quando <= _agora(agora):
            return entrada("invalido", link=link, id=video_id,
                           erro=f"publicar_em {_brasilia_txt(quando)} já passou: o YouTube publicaria "
                                f"na hora, não agendaria")
    try:
        d = _json(_chamar(cliente, token, "GET", f"{API}/videos", "videos.list", registrar,
                          consulta={"part": "snippet,status", "id": video_id}))
        itens = d.get("items") or []
        if not itens:
            return entrada("erro", link=link, id=video_id,
                           erro=f"vídeo {video_id} não encontrado no YouTube (apagado, id errado ou de outro canal)")
        atual = itens[0]
        sn_atual = atual.get("snippet") or {}
        st_atual = atual.get("status") or {}
        snippet = {k: sn_atual[k] for k in _SNIPPET_MUTAVEL if k in sn_atual}
        if titulo is not None:
            snippet["title"] = str(titulo)
        if descricao is not None:
            snippet["description"] = str(descricao)
        if tags is not None:
            snippet["tags"] = [str(t) for t in tags]
        if categoria is not None:
            snippet["categoryId"] = str(categoria).strip()
        snippet.setdefault("description", "")
        snippet.setdefault("tags", [])
        erro = validar_metadados(snippet.get("title"), None, None, snippet.get("categoryId"))
        if erro:
            return entrada("invalido", link=link, id=video_id,
                           erro=f"o vídeo no YouTube está sem dado obrigatório: {erro}")
        status = {k: st_atual[k] for k in _STATUS_MUTAVEL if k in st_atual}
        if quando is not None:
            if st_atual.get("privacyStatus") != "private":
                return entrada("invalido", link=link, id=video_id,
                               erro=f"o vídeo está {st_atual.get('privacyStatus')}: o YouTube só agenda "
                                    f"vídeo privado que nunca foi publicado")
            status["privacyStatus"] = "private"
            status["publishAt"] = para_utc_z(quando)
        elif privacidade:
            status["privacyStatus"] = privacidade
            if privacidade != "private":
                status.pop("publishAt", None)
        if not status.get("privacyStatus"):
            status["privacyStatus"] = "private"
        corpo = {"id": video_id, "snippet": snippet, "status": status}
        d = _json(_chamar(cliente, token, "PUT", f"{API}/videos", "videos.update", registrar,
                          consulta={"part": "snippet,status"}, json_=corpo))
    except ErroYouTube as e:
        return entrada("erro", link=link, id=video_id, erro=str(e))
    st_novo = d.get("status") or status
    return entrada("agendado" if quando is not None else "atualizado", link=link, id=video_id,
                   privacy=st_novo.get("privacyStatus"), publishAt=st_novo.get("publishAt"),
                   publicar_em=_brasilia_txt(_de_utc(st_novo.get("publishAt"))))


# ------------------------------------------------------------------ B3 conferência
TRAVADO = "travado como privado (projeto sem auditoria)"
UPLOAD_STATUS = {"uploaded": "enviado, ainda processando", "processed": "processado",
                 "failed": "envio falhou", "rejected": "rejeitado pelo YouTube", "deleted": "apagado"}
REJEICOES = {
    "claim": "reivindicação de direitos (Content ID)",
    "copyright": "direitos autorais (copyright)",
    "duplicate": "duplicado (já existe um vídeo igual no canal)",
    "inappropriate": "conteúdo impróprio",
    "legal": "problema legal",
    "length": "longo demais (conta sem verificação por telefone só sobe até 15 min)",
    "size": "arquivo grande demais",   # não está na lista oficial de 2026-10-01; fica por segurança
    "termsOfUse": "violação dos termos de uso",
    "trademark": "marca registrada",
    "uploaderAccountClosed": "conta do YouTube encerrada",
    "uploaderAccountSuspended": "conta do YouTube suspensa",
}
FALHAS = {"codec": "codec de vídeo/áudio não aceito", "conversion": "falha na conversão",
          "emptyFile": "arquivo vazio", "invalidFile": "arquivo inválido",
          "tooSmall": "arquivo pequeno demais", "uploadAborted": "envio interrompido no meio"}
STATUS_PEDIDO = ("agendado", "publico", "privado")


def diagnosticar_video(item: dict, pedido: dict, agora=None) -> dict:
    """Diagnóstico de UM item do videos.list contra o que foi pedido (mesma régua do PC)."""
    agora = _agora(agora)
    st = item.get("status") or {}
    sn = item.get("snippet") or {}
    proc = item.get("processingDetails") or {}
    vid = item.get("id")
    privacy = st.get("privacyStatus")
    publish_at = st.get("publishAt")
    quando = _de_utc(publish_at)
    upload = st.get("uploadStatus")
    pedido = pedido or {}
    status_pedido = str(pedido.get("status_pedido") or "publico").lower()
    base = {"privacy": privacy, "publishAt": publish_at, "publicar_em": _brasilia_txt(quando),
            "uploadStatus": upload, "link": link_video(vid), "titulo": sn.get("title")}

    def fim(status, diag):
        return {"status": status, "diagnostico": diag, **base}

    if upload == "rejected":
        motivo = st.get("rejectionReason")
        return fim("rejeitado", f"rejeitado pelo YouTube: {REJEICOES.get(motivo, motivo or 'motivo não informado')}")
    if upload == "failed":
        motivo = st.get("failureReason")
        return fim("falhou", f"envio falhou: {FALHAS.get(motivo, motivo or 'motivo não informado')}")
    if upload == "deleted":
        return fim("nao_encontrado", "vídeo apagado no YouTube")
    if upload == "uploaded" or proc.get("processingStatus") == "processing":
        prog = proc.get("processingProgress") or {}
        parte = ""
        if prog.get("partsTotal"):
            try:
                parte = f" ({100 * int(prog.get('partsProcessed') or 0) // int(prog['partsTotal'])} %)"
            except (TypeError, ValueError, ZeroDivisionError):
                parte = ""
        return fim("processando", f"ainda processando no YouTube{parte}; confira de novo em alguns minutos")
    if proc.get("processingStatus") in ("failed", "terminated"):
        return fim("falhou", f"processamento {proc.get('processingStatus')}: "
                             f"{(proc.get('processingFailureReason') or 'motivo não informado')}")

    if privacy == "private":
        if status_pedido == "privado":
            return fim("ok", "privado, como pedido")
        if quando is None:
            return fim("travado_privado", f"{TRAVADO}: ficou privado sem publishAt (pedido: {status_pedido})")
        if quando <= agora:
            return fim("travado_privado", f"{TRAVADO}: era para publicar às {_brasilia_txt(quando)} "
                                          f"e continua privado")
        txt = f"agendado para {_brasilia_txt(quando)} (Brasília)"
        pedido_em = pedido.get("publicar_em")
        if pedido_em and str(pedido_em) != _brasilia_txt(quando):
            txt += f" — pedido era {pedido_em}"
        return fim("ok", txt)
    if privacy == "public":
        if status_pedido == "privado":
            return fim("ok", "PÚBLICO, mas o pedido era privado — confira")
        return fim("ok", "publicado")
    if privacy == "unlisted":
        return fim("ok", f"não listado (pedido: {status_pedido}) — confira")
    return fim("ok", f"privacidade desconhecida: {privacy!r}")


def conferir_lote(cliente, token: str, esperado: dict, agora=None, registrar=None) -> dict:
    """esperado = {video_id: {"status_pedido": "agendado"|"publico"|"privado",
                              "publicar_em": "AAAA-MM-DD HH:MM" (Brasília) ou None}}.
    Uma chamada videos.list (1 unidade) a cada 50 ids. Devolve {video_id: {...}} + "resumo"."""
    agora = _agora(agora)
    ids = [str(v) for v in esperado]
    vistos: dict = {}
    erro_lote = None
    for i in range(0, len(ids), IDS_POR_CHAMADA):
        lote = ids[i:i + IDS_POR_CHAMADA]
        try:
            d = _json(_chamar(cliente, token, "GET", f"{API}/videos", "videos.list", registrar,
                              consulta={"part": "status,snippet,processingDetails",
                                        "id": ",".join(lote), "maxResults": IDS_POR_CHAMADA}))
        except ErroYouTube as e:
            erro_lote = str(e)
            for v in lote:
                vistos[v] = {"__erro__": erro_lote}
            continue
        for it in d.get("items") or []:
            if it.get("id"):
                vistos[str(it["id"])] = it
    resultado: dict = {}
    contagem: Counter = Counter()
    for vid in ids:
        it = vistos.get(vid)
        if it is None:
            r = {"status": "nao_encontrado",
                 "diagnostico": "não veio na resposta do YouTube (apagado, id errado ou de outro canal)",
                 "privacy": None, "publishAt": None, "publicar_em": None, "uploadStatus": None,
                 "link": link_video(vid), "titulo": None}
        elif "__erro__" in it:
            r = {"status": "erro", "diagnostico": it["__erro__"], "privacy": None, "publishAt": None,
                 "publicar_em": None, "uploadStatus": None, "link": link_video(vid), "titulo": None}
        else:
            r = diagnosticar_video(it, esperado.get(vid) or {}, agora)
        resultado[vid] = r
        contagem[r["status"]] += 1
    resultado["resumo"] = {"total": len(ids), **dict(sorted(contagem.items())),
                           "chamadas": (len(ids) + IDS_POR_CHAMADA - 1) // IDS_POR_CHAMADA}
    if erro_lote:
        resultado["resumo"]["erro"] = erro_lote
    return resultado


# ------------------------------------------------------------------------- B4 legenda
def _tempo_srt(seg: float) -> str:
    ms = int(round(max(seg, 0.0) * 1000))
    h, resto = divmod(ms, 3600000)
    m, resto = divmod(resto, 60000)
    s, ms = divmod(resto, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def transcricao_para_srt(dados: dict, inicio: float, fim: float, max_palavras: int = 4) -> str:
    """Transcrição no formato 4.5 (segmentos com palavras cronometradas, tempos do bruto) -> SRT.
    Blocos de até max_palavras palavras (nunca cruzam segmento), tempos relativos a `inicio`,
    só palavras dentro de inicio..fim (recortadas na borda), sem bloco vazio, sem sobreposição.
    Segmento sem `palavras` entra como um bloco só com o texto do segmento. Função pura."""
    inicio, fim = float(inicio), float(fim)
    max_palavras = max(int(max_palavras), 1)
    blocos: list[tuple[float, float, str]] = []
    for seg in (dados or {}).get("segmentos") or []:
        palavras = seg.get("palavras")
        if not palavras:
            txt = " ".join(str(seg.get("texto") or "").split())
            if txt:
                palavras = [{"inicio": seg.get("inicio"), "fim": seg.get("fim"), "texto": txt}]
            else:
                continue
        grupo: list[dict] = []
        for p in palavras:
            try:
                pi, pf = float(p.get("inicio")), float(p.get("fim"))
            except (TypeError, ValueError):
                continue
            txt = " ".join(str(p.get("texto") or "").split())
            if not txt or pf <= inicio or pi >= fim:
                continue
            grupo.append({"inicio": max(pi, inicio), "fim": min(pf, fim), "texto": txt})
            if len(grupo) >= max_palavras:
                blocos.append((grupo[0]["inicio"], grupo[-1]["fim"], " ".join(g["texto"] for g in grupo)))
                grupo = []
        if grupo:
            blocos.append((grupo[0]["inicio"], grupo[-1]["fim"], " ".join(g["texto"] for g in grupo)))
    linhas = []
    fim_anterior = 0
    n = 0
    for ini, fi, texto in blocos:
        a = int(round((ini - inicio) * 1000))
        b = int(round((fi - inicio) * 1000))
        a = max(a, fim_anterior)
        if b <= a:
            b = a + 1
        n += 1
        linhas.append(f"{n}\n{_tempo_srt(a / 1000)} --> {_tempo_srt(b / 1000)}\n{texto}")
        fim_anterior = b
    return "\n\n".join(linhas) + ("\n" if linhas else "")


CUSTO_LEGENDA = CUSTOS["captions.insert"]["custo"]
FRONTEIRA_PADRAO = "hp_legenda_fronteira_7f3a"


def corpo_multipart_related(metadata: dict, arquivo: bytes, tipo_arquivo: str = "application/octet-stream",
                            fronteira: str = FRONTEIRA_PADRAO) -> bytes:
    """Corpo multipart/related (uploadType=multipart do Google): parte 1 JSON, parte 2 o arquivo."""
    meta = json.dumps(metadata, ensure_ascii=False).encode("utf-8")
    f = fronteira.encode("ascii")
    return (b"--" + f + b"\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n" + meta
            + b"\r\n--" + f + b"\r\nContent-Type: " + tipo_arquivo.encode("ascii") + b"\r\n\r\n"
            + arquivo + b"\r\n--" + f + b"--\r\n")


def enviar_legenda(cliente, token: str, video_id: str, srt: str, idioma: str = "pt-BR",
                   nome: str = "Português", ligado: bool = False, registrar=None,
                   fronteira: str = FRONTEIRA_PADRAO) -> dict:
    """captions.insert (multipart/related: JSON {"snippet": {videoId, language, name, isDraft}} +
    o SRT). Custa 400 unidades (4 % do dia) — por isso vem DESLIGADA: ligado=False devolve
    entrada("desligado") sem chamar nada."""
    link = link_video(video_id)
    if not ligado:
        return entrada("desligado", link=link, id=video_id,
                       erro=f"legenda por API desligada: custa {CUSTO_LEGENDA} unidades "
                            f"({100 * CUSTO_LEGENDA // LIMITE_DIA} % da cota do dia); chame com ligado=True")
    if not str(srt or "").strip():
        return entrada("invalido", link=link, id=video_id, erro="legenda vazia (SRT sem blocos)")
    meta = {"snippet": {"videoId": video_id, "language": idioma, "name": nome, "isDraft": False}}
    corpo = corpo_multipart_related(meta, str(srt).encode("utf-8"), "application/octet-stream", fronteira)
    try:
        d = _json(_chamar(cliente, token, "POST", f"{API_UPLOAD}/captions", "captions.insert", registrar,
                          consulta={"part": "snippet", "uploadType": "multipart"}, corpo=corpo,
                          cabecalhos={"Content-Type": f"multipart/related; boundary={fronteira}"}))
    except ErroYouTube as e:
        if e.ja_existe:
            return entrada("ja_existe", link=link, id=video_id, aviso=str(e))
        return entrada("erro", link=link, id=video_id, erro=str(e))
    return entrada("enviado", link=link, id=d.get("id"), video=video_id, idioma=idioma)


__all__ = [
    "API", "API_UPLOAD", "CUSTOS", "CUSTOS_CONFIRMADOS_EM", "LIMITE_DIA", "LIMITE_ENVIOS_DIA",
    "Contador", "registro_de_cota", "ErroYouTube", "erro_youtube", "MOTIVOS",
    "CacheArquivo", "CacheMemoria", "normalizar_titulo", "playlist_do_canal", "adicionar_na_playlist",
    "contar_tags", "validar_metadados", "atualizar_video", "para_utc_z",
    "diagnosticar_video", "conferir_lote", "TRAVADO", "REJEICOES", "FALHAS", "UPLOAD_STATUS",
    "transcricao_para_srt", "enviar_legenda", "corpo_multipart_related", "CUSTO_LEGENDA",
    "link_video", "link_playlist",
]
