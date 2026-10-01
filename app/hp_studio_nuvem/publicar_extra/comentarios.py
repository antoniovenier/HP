"""comentarios — comentários da Página do Facebook: ler, classificar (sem IA), planejar e executar.

REGRA DO ANTÔNIO (30/09/2026 11:52, vale para todas as contas HP):
    "antes de responder, veja se precisaria de resposta, ou somente a curtida sirva;
     se for algo ofensivo, não faça nada de curtida nem nada"

O QUE FAZ (tarefa C2 da rodada 2)
    ler_comentarios()        GET /{post}/comments (filter=stream, chronological, paginado, since=desde)
    curtir()                 POST /{comentario}/likes
    responder()              POST /{comentario}/comments {"message"}
    ocultar()                POST /{comentario} {"is_hidden": true}      (não é usado por padrão)
    classificar_comentario() texto -> "responder" | "curtir" | "ignorar"   FUNÇÃO PURA, conservadora,
                             sem IA, com o léxico em lexico_comentarios.json (o Antônio revisa)
    planejar()               comentários -> lista de ações (só a PROPOSTA; nada é enviado)
    executar()               por padrão NÃO envia (devolve o que faria); com enviar=True curte/responde,
                             grava o estado (idempotente: nunca curte nem responde duas vezes) e espera
                             o intervalo entre respostas

USO
    from publicar_extra import comentarios as co
    cfg = co.ConfigComentarios()                      # enviar=False: só proposta
    lidos = co.ler_comentarios(cliente, token, post_id, desde=ontem)
    estado = co.EstadoComentarios(pasta_app() / "publicar" / "comentarios_estado.json")
    acoes = co.planejar(lidos, estado.conjunto_tratados(), cfg, posts_nossos={post_id})
    co.executar(cliente, token, acoes, cfg, estado)   # simulado
    co.executar(cliente, token, acoes, cfg, estado, enviar=True, dormir=time.sleep)   # o PC liga

REGRAS
    - Classes: responder = pergunta, dúvida, pedido ou crítica que vale conversa; curtir = elogio,
      emoji puro, marcação de amigo; ignorar = ofensivo (SEM curtida e SEM resposta), spam/link,
      sarcasmo. Na dúvida: curtir. Caixa alta e gíria não mudam a classe.
    - Execução: 1 resposta por pessoa, no máximo 25 respostas por passada, só em post NOSSO, nunca em
      massa (intervalo entre respostas), tudo em campos da dataclass ConfigComentarios.
    - Token só no access_token da consulta/form (nunca na URL); erros em português via erro_graph.
    - Permissões (doc da Meta, 01/10/2026): ler = pages_read_engagement (+ pages_read_user_content);
      curtir/responder/ocultar = pages_manage_engagement (quem pede o token precisa da tarefa MODERATE
      na Página). pages_manage_posts NÃO é exigida para responder comentário.
"""
from __future__ import annotations

import json
import re
import time
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from hpbase import escrever_json, ler_json
from hpbase import agora as _agora_brasilia

from .contrato_pc import entrada, mascarar
from .facebook_extra import API, ErroGraph, _entrada_erro, _paginar, _pedir, epoch_utc, hora_brasilia, ler_hora

ARQUIVO_LEXICO = Path(__file__).with_name("lexico_comentarios.json")
CAMPOS_COMENTARIOS = "id,message,from,created_time,like_count,comment_count"
LIMITE_PAGINA = 100
A_REDIGIR = "a redigir"
CLASSES = ("responder", "curtir", "ignorar")
PERMISSOES_LEIGO = {
    "pages_read_engagement": "ler os comentários dos posts da Página",
    "pages_read_user_content": "ver o texto de quem comentou (conteúdo de usuários na Página)",
    "pages_manage_engagement": "curtir, responder e ocultar comentários como a Página",
}


# ============================================================================ léxico
def _sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", str(s)) if not unicodedata.combining(c))


def normalizar(texto) -> str:
    """minúsculo, sem acento, espaços colapsados (o que o léxico compara)."""
    s = _sem_acento(str(texto or "")).lower().replace(" ", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


_LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s"})


def desmascarar(texto_norm: str) -> str:
    """Tira os disfarces de palavrão: f.d.p / f d p -> fdp, m3rda -> merda, m*rda -> m.rda (coringa),
    merdaaaa -> merda (letras repetidas 3+ viram 1)."""
    s = texto_norm
    s = re.sub(r"(?<![a-z0-9])([a-z])[\.\s\*\-_]+([a-z])[\.\s\*\-_]+([a-z])(?:[\.\s\*\-_]+([a-z]))?(?![a-z0-9])",
               lambda m: "".join(g for g in m.groups() if g), s)
    palavras = []
    for p in s.split(" "):
        if any(c.isalpha() for c in p) and any(c in "013457@$" for c in p):
            p = p.translate(_LEET)
        palavras.append(p)
    s = " ".join(palavras)
    s = re.sub(r"([a-z])\1{2,}", r"\1", s)
    return s


def _compilar_termos(lista) -> re.Pattern | None:
    termos = sorted({normalizar(t) for t in (lista or []) if normalizar(t)}, key=len, reverse=True)
    if not termos:
        return None
    corpo = "|".join(re.escape(t).replace(r"\ ", r"\s+") for t in termos)
    return re.compile(r"(?<![a-z0-9])(?:" + corpo + r")(?![a-z0-9])")


def _compilar_regex(lista) -> list[re.Pattern]:
    return [re.compile(r, re.I) for r in (lista or [])]


class Lexico:
    """Léxico compilado (de um dict do lexico_comentarios.json)."""

    def __init__(self, dados: dict):
        self.dados = dados
        self.ofensivos = _compilar_termos(dados.get("ofensivos"))
        self.ofensivos_regex = _compilar_regex(dados.get("ofensivos_regex"))
        self.spam = _compilar_termos(dados.get("spam"))
        self.spam_regex = _compilar_regex(dados.get("spam_regex"))
        self.pergunta = _compilar_termos([t for t in dados.get("pergunta_marcas", []) if t != "?"])
        self.pergunta_inicio = _compilar_regex(dados.get("pergunta_inicio_regex"))
        self.retorica = {normalizar(t) for t in dados.get("pergunta_retorica", [])}
        self.risada = re.compile(dados.get("risada_regex") or r"^(k{2,}|ha(ha)+h?|rs(rs)*|lol)$", re.I)
        self.pedido = _compilar_termos(dados.get("pedido_marcas"))
        self.critica = _compilar_termos(dados.get("critica_que_vale_conversa"))
        self.elogio = _compilar_termos(dados.get("elogio"))
        self.sarcasmo = _compilar_termos(dados.get("sarcasmo"))
        self.sarcasmo_regex = _compilar_regex(dados.get("sarcasmo_regex"))
        self.emoji_puro = re.compile(dados.get("emoji_puro_regex") or r"^[\W_\d]+$")
        self.marcacao = re.compile(dados.get("marcacao_regex") or r"(?<![\w.])@[\w.]{2,}")
        self.nossos = re.compile(dados.get("nossos_handles_regex") or r"^@?hp[\w.]*$", re.I)


@lru_cache(maxsize=4)
def _lexico_do_arquivo(caminho: str) -> Lexico:
    return Lexico(json.loads(Path(caminho).read_text(encoding="utf-8")))


def carregar_lexico(caminho: Path | str | None = None) -> Lexico:
    return _lexico_do_arquivo(str(caminho or ARQUIVO_LEXICO))


def _lexico(lexico) -> Lexico:
    if lexico is None:
        return carregar_lexico()
    if isinstance(lexico, Lexico):
        return lexico
    if isinstance(lexico, dict):
        return Lexico(lexico)
    return carregar_lexico(lexico)


# ============================================================================ classificar
def tem_emoji(texto: str) -> bool:
    for c in str(texto or ""):
        o = ord(c)
        if o >= 0x1F000 or unicodedata.category(c) in ("So", "Sk") or 0x2600 <= o <= 0x27BF:
            return True
    return False


def _bate(rx: re.Pattern | None, *textos: str) -> bool:
    return bool(rx) and any(rx.search(t) for t in textos if t)


def _bate_regex(lista: list[re.Pattern], *textos: str) -> bool:
    return any(rx.search(t) for rx in lista for t in textos if t)


def _so_retorica(texto_norm: str, lx: Lexico) -> bool:
    """"sério?", "é mesmo?", "jura??" — pergunta de espanto, não é dúvida para responder."""
    limpo = re.sub(r"[^a-z0-9 ]+", " ", texto_norm).strip()
    palavras = [p for p in limpo.split() if not lx.risada.match(p)]   # "jura?! kkkk" -> "jura"
    if not palavras:
        return True
    if " ".join(palavras) in lx.retorica:
        return True
    return len(palavras) <= 3 and all(p in lx.retorica for p in palavras)


def classificar_detalhado(texto, lexico=None) -> dict:
    """-> {"classe": responder|curtir|ignorar, "motivo": "..."} (função pura; o léxico é dado)."""
    lx = _lexico(lexico)
    bruto = str(texto or "")
    norm = normalizar(bruto)
    if not norm:
        return {"classe": "ignorar", "motivo": "comentário vazio"}

    # marcações: tira as nossas (@hp…) e guarda as de amigos
    mencoes = lx.marcacao.findall(bruto)
    amigos = [m for m in mencoes if not lx.nossos.match(m)]
    sem_mencao = normalizar(lx.marcacao.sub(" ", bruto))
    desm = desmascarar(sem_mencao)

    if _bate(lx.ofensivos, sem_mencao, desm) or _bate_regex(lx.ofensivos_regex, sem_mencao, desm):
        return {"classe": "ignorar", "motivo": "ofensivo (sem curtida e sem resposta)"}
    if _bate(lx.spam, sem_mencao) or _bate_regex(lx.spam_regex, norm, desm):
        return {"classe": "ignorar", "motivo": "spam ou link"}
    if lx.emoji_puro.match(sem_mencao or norm):
        if tem_emoji(bruto):
            return {"classe": "curtir", "motivo": "só emoji"}
        if amigos:
            return {"classe": "curtir", "motivo": "marcação de amigo"}
        return {"classe": "ignorar", "motivo": "só pontuação ou número, nada a dizer"}
    n_palavras = len(sem_mencao.split())
    if amigos and (n_palavras <= 4 or (n_palavras <= 6 and "?" not in sem_mencao)):
        return {"classe": "curtir", "motivo": "marcação de amigo"}   # "@pedrao kkkk tu viu?" é pro amigo
    if _bate(lx.sarcasmo, sem_mencao) or _bate_regex(lx.sarcasmo_regex, sem_mencao):
        return {"classe": "ignorar", "motivo": "sarcasmo (nem curtida nem resposta)"}
    marca_forte = _bate(lx.pergunta, sem_mencao) or _bate_regex(lx.pergunta_inicio, sem_mencao)
    if "?" in sem_mencao:
        if _so_retorica(sem_mencao, lx) and not marca_forte:
            return {"classe": "curtir", "motivo": "pergunta de espanto (retórica)"}
        return {"classe": "responder", "motivo": "pergunta"}
    if marca_forte:
        return {"classe": "responder", "motivo": "dúvida"}
    if _bate(lx.pedido, sem_mencao):
        return {"classe": "responder", "motivo": "pedido"}
    if _bate(lx.critica, sem_mencao):
        return {"classe": "responder", "motivo": "crítica que vale conversa"}
    if amigos:
        return {"classe": "curtir", "motivo": "marcação de amigo"}
    if _bate(lx.elogio, sem_mencao):
        return {"classe": "curtir", "motivo": "elogio"}
    return {"classe": "curtir", "motivo": "na dúvida, curtir"}


def classificar_comentario(texto, lexico=None) -> str:
    """"responder" | "curtir" | "ignorar" — pura, conservadora, sem IA (regras no topo do módulo)."""
    return classificar_detalhado(texto, lexico)["classe"]


# ============================================================================ API
def _normalizar_comentario(bruto: dict, post_id: str | None) -> dict:
    de = bruto.get("from") or {}
    return {"id": str(bruto.get("id") or ""), "texto": bruto.get("message") or "",
            "autor_id": str(de.get("id")) if de.get("id") else None, "autor_nome": de.get("name"),
            "criado_em": hora_brasilia(bruto.get("created_time")),
            "curtidas": bruto.get("like_count"), "respostas": bruto.get("comment_count"),
            "post_id": str(post_id) if post_id else None, "bruto": bruto}


def ler_comentarios(cliente, token: str, post_id: str, desde: datetime | None = None,
                    limite: int = 200) -> list[dict]:
    """GET /{post}/comments?fields=…&filter=stream&order=chronological&limit=100 (paginado; since=desde).
    -> [{id, texto, autor_id, autor_nome, criado_em (Brasília), curtidas, respostas, post_id, bruto}].
    Levanta ErroGraph (português) em erro."""
    consulta = {"fields": CAMPOS_COMENTARIOS, "filter": "stream", "order": "chronological",
                "limit": min(LIMITE_PAGINA, max(1, limite))}
    dt_desde = ler_hora(desde) if desde is not None else None
    if dt_desde:
        consulta["since"] = epoch_utc(dt_desde)
    saida = []
    for bruto in _paginar(cliente, token, f"{API}/{post_id}/comments", consulta, limite=limite,
                          acao="ler_comentarios"):
        c = _normalizar_comentario(bruto, post_id)
        if dt_desde:
            criado = ler_hora(bruto.get("created_time"))
            if criado and criado < dt_desde:
                continue
        saida.append(c)
    return saida


def curtir(cliente, token: str, comentario_id: str) -> dict:
    """POST /{id}/likes -> entrada("curtido") | entrada("erro", erro=português)."""
    try:
        _pedir(cliente, "POST", f"{API}/{comentario_id}/likes", token, form={}, acao="curtir")
    except ErroGraph as e:
        return _entrada_erro(e, id=comentario_id)
    return entrada("curtido", id=comentario_id)


def responder(cliente, token: str, comentario_id: str, texto: str) -> dict:
    """POST /{id}/comments {"message": texto} -> entrada("respondido", id=<id da resposta>)."""
    texto = str(texto or "").strip()
    if not texto:
        return entrada("erro", id=comentario_id, erro="Resposta vazia: nada enviado.")
    try:
        corpo = _pedir(cliente, "POST", f"{API}/{comentario_id}/comments", token,
                       form={"message": texto}, acao="responder")
    except ErroGraph as e:
        return _entrada_erro(e, id=comentario_id)
    return entrada("respondido", id=corpo.get("id"), comentario_id=comentario_id, texto=texto)


def ocultar(cliente, token: str, comentario_id: str, oculto: bool = True) -> dict:
    """POST /{id} {"is_hidden": true} -> entrada("ocultado"). Só se o Antônio mandar (não é padrão)."""
    try:
        _pedir(cliente, "POST", f"{API}/{comentario_id}", token,
               form={"is_hidden": "true" if oculto else "false"}, acao="ocultar")
    except ErroGraph as e:
        return _entrada_erro(e, id=comentario_id)
    return entrada("ocultado" if oculto else "reexibido", id=comentario_id)


# ============================================================================ configuração e estado
@dataclass
class ConfigComentarios:
    """Campos (não constantes soltas). enviar=False: o módulo só propõe; o PC liga o envio."""
    max_respostas_por_passada: int = 25
    uma_resposta_por_pessoa: bool = True
    so_posts_nossos: bool = True
    intervalo_entre_respostas_s: float = 20
    intervalo_entre_curtidas_s: float = 3
    max_curtidas_por_passada: int = 60
    curtir_elogios: bool = True
    enviar: bool = False
    parar_em: tuple = ("token", "permissao", "bloqueio", "limite")   # categorias de erro que param a passada


class EstadoComentarios:
    """Ids já tratados (por comentário e por autor). Arquivo JSON injetável, gravado atômico
    (hpbase.escrever_json). Sem caminho = só memória (testes/simulação)."""

    def __init__(self, caminho: Path | str | None = None):
        self.caminho = Path(caminho) if caminho else None
        self.dados = {"versao": 1, "comentarios": {}, "autores_respondidos": {}}
        if self.caminho:
            lido = ler_json(self.caminho, {})      # ausente ou quebrado = começa vazio
            if isinstance(lido, dict):
                self.dados["comentarios"] = dict(lido.get("comentarios") or {})
                self.dados["autores_respondidos"] = dict(lido.get("autores_respondidos") or {})

    @classmethod
    def de(cls, estado) -> "EstadoComentarios":
        if isinstance(estado, cls):
            return estado
        return cls(estado)

    def tratado(self, comentario_id) -> bool:
        return str(comentario_id) in self.dados["comentarios"]

    def autor_respondido(self, autor_id) -> bool:
        return bool(autor_id) and str(autor_id) in self.dados["autores_respondidos"]

    def registrar(self, comentario_id, acao: str, autor_id=None, agora=None) -> None:
        quando = (ler_hora(agora) or _agora_brasilia()).strftime("%Y-%m-%d %H:%M")
        self.dados["comentarios"][str(comentario_id)] = {"acao": acao, "autor_id": autor_id, "quando": quando}
        if acao == "responder" and autor_id:
            self.dados["autores_respondidos"][str(autor_id)] = {"comentario_id": str(comentario_id),
                                                                "quando": quando}

    def conjunto_tratados(self) -> set:
        """ids dos comentários tratados + "autor:<id>" de quem já recebeu resposta (para planejar)."""
        s = set(self.dados["comentarios"])
        s |= {f"autor:{a}" for a in self.dados["autores_respondidos"]}
        return s

    def salvar(self) -> Path | None:
        if self.caminho:
            escrever_json(self.caminho, self.dados)
        return self.caminho


# ============================================================================ planejar / executar
def _acao(acao: str, c: dict, motivo: str, texto_resposta: str | None = None) -> dict:
    d = {"acao": acao, "comentario_id": c.get("id"), "autor_id": c.get("autor_id"),
         "post_id": c.get("post_id"), "texto": (c.get("texto") or "")[:200], "motivo": motivo}
    if acao == "responder":
        d["texto_resposta"] = texto_resposta or A_REDIGIR
    return d


def planejar(comentarios: list[dict], ja_tratados: set | None, cfg: ConfigComentarios | None,
             posts_nossos: set | None, redator=None, lexico=None, nossos_ids: set | None = None) -> list[dict]:
    """Comentários (de ler_comentarios) -> [{"acao": curtir|responder|ignorar, "comentario_id", "autor_id",
    "texto_resposta" (só em responder: o que o redator injetado devolver, senão "a redigir"), "motivo"}].
    Respeita 1 resposta por pessoa, o máximo por passada, só post nosso; nunca envia nada."""
    cfg = cfg or ConfigComentarios()
    ja = set(ja_tratados or ())
    nossos = {str(p) for p in (posts_nossos or ())}
    nossos_ids = {str(i) for i in (nossos_ids or ())}
    saida: list[dict] = []
    respondidos_agora: set[str] = set()
    n_resp = n_curt = 0
    for c in comentarios or []:
        cid = str(c.get("id") or "")
        if not cid or cid in ja:
            continue  # já tratado: nem entra na lista
        autor = str(c["autor_id"]) if c.get("autor_id") else None
        if autor and autor in nossos_ids:
            continue  # comentário da própria Página
        if cfg.so_posts_nossos and str(c.get("post_id") or "") not in nossos:
            saida.append(_acao("ignorar", c, "post não é nosso"))
            continue
        cl = classificar_detalhado(c.get("texto"), lexico)
        classe, motivo = cl["classe"], cl["motivo"]
        if classe == "responder":
            if cfg.uma_resposta_por_pessoa and autor and (f"autor:{autor}" in ja or autor in respondidos_agora):
                classe, motivo = "curtir", f"{motivo}; essa pessoa já recebeu resposta (1 por pessoa)"
            elif n_resp >= cfg.max_respostas_por_passada:
                saida.append(_acao("ignorar", c, f"{motivo}; fica para a próxima passada "
                                                  f"(limite de {cfg.max_respostas_por_passada} respostas)"))
                continue
        if classe == "responder":
            texto = None
            if redator is not None:
                try:
                    texto = redator(c)
                except Exception as e:  # noqa: BLE001 — redator é externo; a proposta não pode cair
                    motivo += f"; redator falhou: {mascarar(str(e))[:80]}"
            texto = str(texto).strip() if texto else None
            saida.append(_acao("responder", c, motivo, texto))
            n_resp += 1
            if autor:
                respondidos_agora.add(autor)
        elif classe == "curtir":
            if not cfg.curtir_elogios:
                saida.append(_acao("ignorar", c, f"{motivo}; curtidas desligadas na configuração"))
            elif n_curt >= cfg.max_curtidas_por_passada:
                saida.append(_acao("ignorar", c, f"{motivo}; fica para a próxima passada "
                                                  f"(limite de {cfg.max_curtidas_por_passada} curtidas)"))
            else:
                saida.append(_acao("curtir", c, motivo))
                n_curt += 1
        else:
            saida.append(_acao("ignorar", c, motivo))
    return saida


def executar(cliente, token: str, acoes: list[dict], cfg: ConfigComentarios | None = None,
             estado=None, enviar: bool = False, dormir=None, agora=None, funcoes: dict | None = None) -> dict:
    """Executa a proposta de planejar(). Por padrão (enviar=False e cfg.enviar=False) NÃO manda nada:
    devolve o que faria. Com enviar=True: curte/responde, grava o estado depois de cada envio (atômico)
    e espera cfg.intervalo_entre_respostas_s entre respostas (dormir injetado). Idempotente: o que já
    está no estado não é curtido nem respondido de novo. `funcoes` troca curtir/responder (Instagram,
    Threads); None numa delas = essa rede não tem a ação."""
    cfg = cfg or ConfigComentarios()
    est = EstadoComentarios.de(estado)
    envia = bool(enviar or cfg.enviar)
    dormir = dormir if dormir is not None else (time.sleep if envia else (lambda s: None))
    fn = {"curtir": curtir, "responder": responder}
    if funcoes:
        fn.update(funcoes)
    resultados = []
    n = {"curtidas": 0, "respondidas": 0, "puladas": 0, "ignoradas": 0, "erros": 0}
    parou = None
    for a in acoes or []:
        acao = a.get("acao")
        cid = str(a.get("comentario_id") or "")
        autor = a.get("autor_id")
        linha = dict(a)
        if acao not in ("curtir", "responder") or not cid:
            linha["resultado"] = "nada a fazer"
            n["ignoradas"] += 1
            resultados.append(linha)
            continue
        if est.tratado(cid):
            linha.update(resultado="pulado", porque="já tratado antes (idempotente)")
            n["puladas"] += 1
            resultados.append(linha)
            continue
        if acao == "responder" and cfg.uma_resposta_por_pessoa and est.autor_respondido(autor):
            linha.update(acao="curtir", porque="essa pessoa já recebeu resposta; vira curtida")
            acao = "curtir"
        if acao == "responder":
            if n["respondidas"] >= cfg.max_respostas_por_passada:
                linha.update(resultado="pulado", porque=f"limite de {cfg.max_respostas_por_passada} respostas")
                n["puladas"] += 1
                resultados.append(linha)
                continue
            texto = str(a.get("texto_resposta") or "").strip()
            if not texto or texto.lower() == A_REDIGIR:
                linha.update(resultado="pulado", porque="sem texto de resposta (a redigir)")
                n["puladas"] += 1
                resultados.append(linha)
                continue
        elif n["curtidas"] >= cfg.max_curtidas_por_passada:
            linha.update(resultado="pulado", porque=f"limite de {cfg.max_curtidas_por_passada} curtidas")
            n["puladas"] += 1
            resultados.append(linha)
            continue
        if fn.get(acao) is None:
            linha.update(resultado="pulado", porque=f"esta rede não tem a ação {acao}")
            n["puladas"] += 1
            resultados.append(linha)
            continue
        if not envia:
            linha["resultado"] = "simulado (enviar=False)"
            n["respondidas" if acao == "responder" else "curtidas"] += 1
            resultados.append(linha)
            continue
        if acao == "responder" and n["respondidas"] > 0 and cfg.intervalo_entre_respostas_s:
            dormir(cfg.intervalo_entre_respostas_s)
        elif acao == "curtir" and n["curtidas"] > 0 and cfg.intervalo_entre_curtidas_s:
            dormir(cfg.intervalo_entre_curtidas_s)
        if acao == "responder":
            r = fn["responder"](cliente, token, cid, a.get("texto_resposta"))
        else:
            r = fn["curtir"](cliente, token, cid)
        linha["retorno"] = r
        if r.get("status") == "erro":
            linha.update(resultado="erro", porque=r.get("erro"))
            n["erros"] += 1
            resultados.append(linha)
            if r.get("categoria") in cfg.parar_em:
                parou = r.get("erro")
                break
            continue
        est.registrar(cid, acao, autor, agora)
        est.salvar()
        linha["resultado"] = "enviado"
        n["respondidas" if acao == "responder" else "curtidas"] += 1
        resultados.append(linha)
    return {"simulado": not envia, **n, "parou": parou, "resultados": resultados,
            "resumo": (("SIMULADO: " if not envia else "") + f"{n['respondidas']} resposta(s), "
                       f"{n['curtidas']} curtida(s), {n['puladas']} pulada(s), {n['erros']} erro(s)"
                       + (f"; parou: {parou}" if parou else ""))}
