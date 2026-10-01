"""comentarios_ig_threads — a mesma regra de comentários (C2) para Instagram e Threads (tarefa C3).

O QUE FAZ
    Instagram (graph.instagram.com, token IG da conta — o `IG_<conta>` do meta_tokens.txt):
        ig_ler_comentarios()   GET /{media-id}/comments (paginado)
        ig_responder()         POST /{comment-id}/replies {"message"}
        ig_ocultar()           POST /{comment-id} {"hide": true}
        ig_executar()          comentarios.executar com responder do IG; a API do Instagram NÃO curte
                               comentário, então toda ação "curtir" é pulada (fica registrado no resultado)
    Threads (graph.threads.net, token TH da conta — o `TH_<conta>`):
        th_ler_respostas()     GET /{media-id}/replies (ordem cronológica, reverse=false)
        th_responder()         POST /me/threads {media_type: TEXT, text, reply_to_id} -> container
                               POST /me/threads_publish {creation_id} -> id da resposta
        th_ocultar()           POST /{reply-id}/manage_reply {"hide": true}
        th_executar()          idem ao IG (Threads também não curte pela API)
    A classificação é a mesma: comentarios.classificar_comentario / comentarios.planejar.

USO
    from publicar_extra import comentarios as co, comentarios_ig_threads as igth
    lidos = igth.ig_ler_comentarios(cliente, token_ig, media_id)
    acoes = co.planejar(lidos, estado.conjunto_tratados(), cfg, posts_nossos={media_id})
    igth.ig_executar(cliente, token_ig, acoes, cfg, estado)               # simulado
    igth.ig_executar(cliente, token_ig, acoes, cfg, estado, enviar=True)  # o PC liga

PERMISSÕES (doc da Meta lida em 01/10/2026, ver DOCS)
    Instagram com login do Instagram (o que o publicador_meta usa): instagram_business_basic +
    instagram_business_manage_comments. Com login do Facebook: instagram_basic +
    instagram_manage_comments + pages_read_engagement. Threads: threads_read_replies + threads_manage_replies
    (o app do Threads já tem as duas, §C3 do prompt).

REGRAS
    - Token só no access_token da consulta/form; nunca na URL (o paging.next é limpo). Erros em português
      via facebook_extra.erro_graph (IG e Threads devolvem o mesmo {"error": {...}} da Graph).
    - Versões/hosts em constantes no topo (API_IG, API_TH): a doc do IG mostra v26.0 nos exemplos e a do
      Threads mostra o host graph.threads.com; aqui ficam os valores que o PC usa hoje (v21.0 / threads.net).
    - Nada é enviado sem enviar=True (o PC liga).
"""
from __future__ import annotations

from .contrato_pc import entrada
from .facebook_extra import ErroGraph, _entrada_erro, _paginar, _pedir, hora_brasilia
from . import comentarios as co

API_IG = "https://graph.instagram.com/v21.0"     # a doc mostra v26.0; o PC usa v21.0 (confirmar com o publicador_meta)
API_TH = "https://graph.threads.net/v1.0"       # a doc (02/2026) mostra graph.threads.com; o PC usa threads.net
DOCS = {
    "ig_comentarios": "https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/comment-moderation",
    "th_respostas": "https://developers.facebook.com/docs/threads/reply-management",
}
PERMISSOES_IG = {
    "login_instagram": ("instagram_business_basic", "instagram_business_manage_comments"),
    "login_facebook": ("instagram_basic", "instagram_manage_comments", "pages_read_engagement"),
}
PERMISSOES_TH = ("threads_read_replies", "threads_manage_replies")
CAMPOS_IG = "id,text,username,timestamp,like_count,from{id,username},hidden,parent_id"
CAMPOS_TH = "id,text,username,timestamp,has_replies,hide_status,is_reply,replied_to,root_post"
LIMITE_PAGINA = 50


# ============================================================================ Instagram
def _normalizar_ig(bruto: dict, media_id: str) -> dict:
    de = bruto.get("from") or {}
    return {"id": str(bruto.get("id") or ""), "texto": bruto.get("text") or "",
            "autor_id": str(de.get("id")) if de.get("id") else (bruto.get("username") or None),
            "autor_nome": de.get("username") or bruto.get("username"),
            "criado_em": hora_brasilia(bruto.get("timestamp")), "curtidas": bruto.get("like_count"),
            "respostas": None, "post_id": str(media_id), "oculto": bruto.get("hidden"), "bruto": bruto}


def ig_ler_comentarios(cliente, token: str, media_id: str, limite: int = 200) -> list[dict]:
    """GET /{media-id}/comments -> mesma forma de comentarios.ler_comentarios. Levanta ErroGraph."""
    consulta = {"fields": CAMPOS_IG, "limit": min(LIMITE_PAGINA, max(1, limite))}
    saida = []
    for bruto in _paginar(cliente, token, f"{API_IG}/{media_id}/comments", consulta, limite=limite,
                          acao="ler_comentarios"):
        c = _normalizar_ig(bruto, media_id)
        if c.get("oculto"):
            continue
        saida.append(c)
    return saida


def ig_responder(cliente, token: str, comentario_id: str, texto: str) -> dict:
    """POST /{comment-id}/replies {"message"} -> entrada("respondido", id=<id da resposta>)."""
    texto = str(texto or "").strip()
    if not texto:
        return entrada("erro", id=comentario_id, erro="Resposta vazia: nada enviado.")
    try:
        corpo = _pedir(cliente, "POST", f"{API_IG}/{comentario_id}/replies", token,
                       form={"message": texto}, acao="responder")
    except ErroGraph as e:
        return _entrada_erro(e, id=comentario_id, rede="instagram")
    return entrada("respondido", id=corpo.get("id"), comentario_id=comentario_id, texto=texto, rede="instagram")


def ig_ocultar(cliente, token: str, comentario_id: str, oculto: bool = True) -> dict:
    """POST /{comment-id} {"hide": true|false}."""
    try:
        _pedir(cliente, "POST", f"{API_IG}/{comentario_id}", token,
               form={"hide": "true" if oculto else "false"}, acao="ocultar")
    except ErroGraph as e:
        return _entrada_erro(e, id=comentario_id, rede="instagram")
    return entrada("ocultado" if oculto else "reexibido", id=comentario_id, rede="instagram")


def ig_curtir(cliente, token: str, comentario_id: str) -> dict:
    """A API do Instagram não tem curtida de comentário: devolve erro explicado (nunca chama a rede)."""
    return entrada("erro", id=comentario_id, categoria="sem_acao",
                   erro="A API do Instagram não curte comentários; só responder ou ocultar.")


def ig_executar(cliente, token: str, acoes: list[dict], cfg: co.ConfigComentarios | None = None,
                estado=None, enviar: bool = False, dormir=None, agora=None) -> dict:
    """comentarios.executar com o responder do Instagram; "curtir" é pulado (a API não tem)."""
    r = co.executar(cliente, token, acoes, cfg, estado, enviar=enviar, dormir=dormir, agora=agora,
                    funcoes={"responder": ig_responder, "curtir": None})
    r["rede"] = "instagram"
    return r


# ============================================================================ Threads
def _normalizar_th(bruto: dict, media_id: str) -> dict:
    return {"id": str(bruto.get("id") or ""), "texto": bruto.get("text") or "",
            "autor_id": bruto.get("username") or None, "autor_nome": bruto.get("username"),
            "criado_em": hora_brasilia(bruto.get("timestamp")), "curtidas": None,
            "respostas": None, "post_id": str(media_id), "oculto": bruto.get("hide_status") == "HIDDEN",
            "bruto": bruto}


def th_ler_respostas(cliente, token: str, media_id: str, limite: int = 200) -> list[dict]:
    """GET /{media-id}/replies (reverse=false = cronológica) -> mesma forma de ler_comentarios."""
    consulta = {"fields": CAMPOS_TH, "reverse": "false", "limit": min(LIMITE_PAGINA, max(1, limite))}
    saida = []
    for bruto in _paginar(cliente, token, f"{API_TH}/{media_id}/replies", consulta, limite=limite,
                          acao="ler_comentarios"):
        c = _normalizar_th(bruto, media_id)
        if c.get("oculto"):
            continue
        saida.append(c)
    return saida


def th_responder(cliente, token: str, reply_to_id: str, texto: str, espera_s: float = 0, dormir=None) -> dict:
    """POST /me/threads {media_type: TEXT, text, reply_to_id} -> container; POST /me/threads_publish
    {creation_id} -> id. `espera_s` (dormir injetado) entre os dois passos, se o PC quiser."""
    texto = str(texto or "").strip()
    if not texto:
        return entrada("erro", id=reply_to_id, erro="Resposta vazia: nada enviado.")
    try:
        cont = _pedir(cliente, "POST", f"{API_TH}/me/threads", token,
                      form={"media_type": "TEXT", "text": texto, "reply_to_id": reply_to_id}, acao="responder")
        creation_id = cont.get("id")
        if not creation_id:
            return entrada("erro", id=reply_to_id, erro="O Threads não devolveu o id do contêiner da resposta.")
        if espera_s and dormir is not None:
            dormir(espera_s)
        pub = _pedir(cliente, "POST", f"{API_TH}/me/threads_publish", token,
                     form={"creation_id": creation_id}, acao="responder")
    except ErroGraph as e:
        return _entrada_erro(e, id=reply_to_id, rede="threads")
    return entrada("respondido", id=pub.get("id"), comentario_id=reply_to_id, texto=texto, rede="threads",
                   creation_id=creation_id)


def th_ocultar(cliente, token: str, reply_id: str, oculto: bool = True) -> dict:
    """POST /{reply-id}/manage_reply {"hide": true|false} (só resposta de 1º nível, diz a doc)."""
    try:
        _pedir(cliente, "POST", f"{API_TH}/{reply_id}/manage_reply", token,
               form={"hide": "true" if oculto else "false"}, acao="ocultar")
    except ErroGraph as e:
        return _entrada_erro(e, id=reply_id, rede="threads")
    return entrada("ocultado" if oculto else "reexibido", id=reply_id, rede="threads")


def th_executar(cliente, token: str, acoes: list[dict], cfg: co.ConfigComentarios | None = None,
                estado=None, enviar: bool = False, dormir=None, agora=None) -> dict:
    """comentarios.executar com o responder do Threads; "curtir" é pulado (a API não tem)."""
    r = co.executar(cliente, token, acoes, cfg, estado, enviar=enviar, dormir=dormir, agora=agora,
                    funcoes={"responder": th_responder, "curtir": None})
    r["rede"] = "threads"
    return r
