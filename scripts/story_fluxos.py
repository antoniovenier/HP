# -*- coding: utf-8 -*-
"""story_fluxos.py — os fluxos do story no celular (emulador ou celular real) em cima do story_dispositivo.

O que faz: cada passo que o story_post dá dentro do Instagram vira uma função que recebe o aparelho
(`Dispositivo` do story_dispositivo.py, tarefa E1) e usa SÓ os bounds do dump (nunca coordenada fixa)
e os seletores do story_post_seletores.py (os ids confirmados da §4.7: row_feed_button_share,
your_story_share_shortcut_button, action_bar_username_container, asset_button, poll_sticker_v2_question,
done_button, toolbar_highlights_button, reel_viewer_timestamp, reel_viewer_title,
self_toolbar_reshare_button_container; o resto é palpite marcado em IDS_PALPITE e confirmado pela coleta E4).

Fluxos:
  trocar_conta(disp, handle)            perfil -> nome da conta -> @handle na lista -> LÊ o @ ativo de volta;
                                        diferente -> ContaErrada (aborta). Tela de login -> para (código 3), nunca digita senha.
  story_da_arte(disp, arte, figurinhas, destaque=None, zonas=None, registrar=None, chave=None, conta=None)
                                        arte -> galeria (a mais recente) -> editor -> figurinhas (asset_button): link
                                        (URL + rótulo curto "Ver post") e/ou enquete (pergunta <= 25 pelo story_post_lote,
                                        opções, done_button) e/ou contagem -> arrasta a figurinha pelos bounds reais até
                                        a zona do <arte>_zonas.json (D) convertida para a tela real -> "Seu story" ->
                                        espera o envio sumir. registrar(chave, etapa) é chamado com "antes_do_toque"
                                        ANTES do toque final (devolver False = já saiu: não repete) e depois com
                                        "tocado" ou "a_conferir" (falhou depois do toque: nunca toca de novo).
  compartilhar_post_no_story(disp, link, handle, titulo=None, registrar=None, chave=None, destaque=None)
                                        deep link (am start VIEW) ou grade do perfil (plano B, conferindo o título) ->
                                        row_feed_button_share -> "Add to story"/"Adicionar ao story" -> "Seu story".
  adicionar_ao_destaque(disp, nome, conta)
                                        abre o próprio story (foto do perfil), confere que é o DE AGORA pelo carimbo
                                        (reel_viewer_timestamp "3m"/"Now"/"agora", content-desc "<conta>'s story,
                                        N minutes ago", N <= 5) e que reel_viewer_title == conta -> toolbar_highlights_button
                                        ("Highlight") -> destaque pelo nome (ou cria) -> confirma ("Added to"/"Adicionado").
  conferir_pela_api(get_json, ig_user_id, desde, tentativas=3, espera_s=20, dormir=...)
                                        GET https://graph.instagram.com/v21.0/<ig-user-id>/stories?fields=id,media_type,
                                        permalink,timestamp pelo get_json(url, params) INJETADO (nunca faz rede aqui) e
                                        devolve o story mais novo com timestamp >= desde; nada -> None ("a conferir").
  rodar_item_v2(disp, item_v2, story, contexto)
                                        um story da fila v2 (story_fila_v2) pelo tipo: chamada_post/mais_sobre/interacao/
                                        enquete -> story_da_arte; compartilhar_post -> compartilhar_post_no_story;
                                        contagem -> story_da_arte com figurinha de contagem. Respeita as regras abaixo.
  rodar_pedido_v2(pedido, contexto, abrir_aparelho, desligar_emulador=None)
                                        o pedido inteiro: pesado.lock (TravaPesada, ignorar_horario=True; ocupado -> código 2
                                        SEM ligar o aparelho), liga só depois da trava, desliga o EMULADOR sempre (mesmo em
                                        erro) e NUNCA desliga celular real.

Regras (relógio injetado em tudo; o estado fica num JSON injetável, o mesmo story_post_estado.json da rodada 1):
  - 3 min entre dois stories (qualquer conta); <= 5 min por story (orçamento; estourou -> OrcamentoEstourado);
  - conta conferida depois da troca (lê o @ do perfil; diferente -> aborta);
  - 1 story por post: o post é REGISTRADO antes do toque em "Seu story"; segunda chamada não repete (PostJaFeito, código 2);
  - 3 falhas no mesmo post tiram o post da fila automática (ForaDaFila, código 2);
  - aviso da Meta / login / código / termos -> o story_dispositivo grava a parada e sobe AvisoMetaDetectado (código 3);
  - celular bloqueado / 2 aparelhos / teclado de acento ausente -> código 4 (o Antônio resolve);
  - acento e emoji: política do story_dispositivo (padrão: letra sem acento + aviso no log).

Uso (CLI; --simular imprime o roteiro completo sem chamar o adb):
  python scripts\\story_fluxos.py trocar-conta hp.futebol [--simular] [--serial S | --emulador | --celular]
  python scripts\\story_fluxos.py arte H:\\...\\story_chamada.jpg --link https://... --rotulo "Ver post" [--destaque N] --conta hp.carros
  python scripts\\story_fluxos.py arte H:\\...\\story_enquete.jpg --enquete "O que você faz?" --opcao Jogo --opcao Durmo --conta hpgta6
  python scripts\\story_fluxos.py compartilhar https://www.instagram.com/p/XXXX/ --conta hp.futebol [--destaque Noticias]
  python scripts\\story_fluxos.py destaque Enquetes --conta hp.futebol
  python scripts\\story_fluxos.py pedido H:\\HypadoLocal\\emulador\\fila_story\\<post_id>.json [--esperar-intervalo]
Códigos de saída: 0 ok · 1 erro · 2 bloqueado (trava, intervalo, já feito, fora da fila) · 3 aviso da rede · 4 precisa do Antônio.
"""
from __future__ import annotations

import argparse
import logging
import re
import sys
import time
from contextlib import nullcontext
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Callable

AQUI = Path(__file__).resolve().parent
if str(AQUI) not in sys.path:
    sys.path.insert(0, str(AQUI))

import story_dispositivo as sd  # noqa: E402  (acha o hpbase sozinho)
import story_post_seletores as SEL  # noqa: E402
import story_fila_v2 as fila  # noqa: E402
import story_post_lote as LOTE  # noqa: E402
from story_dispositivo import No, achar, achar_todos, normalizar  # noqa: E402
from hpbase import FUSO, TravaOcupada, TravaPesada, escrever_json, ler_json, marca, raiz_local  # noqa: E402

OK, ERRO, BLOQUEADO, AVISO_META, PRECISA_ANTONIO = 0, 1, 2, 3, 4
INTERVALO_MIN_SEG = 180            # 3 min entre dois stories (qualquer conta)
ORCAMENTO_SEG = 300                # no máximo 5 min por story
MAX_TENTATIVAS = 3                 # 3 falhas no mesmo post -> fora da fila automática
LIMITE_MIN_AGORA = getattr(SEL, "TIMESTAMP_RECENTE_MAX_MIN", 5)   # "3m" conta como "de agora"; "7m" não
LIMITE_PERGUNTA = LOTE.LIMITE_PERGUNTA                             # 25 (A4)
MAX_STORIES_AVANCAR = 40
ARRASTAR_MS = 1200
API_STORIES = "https://graph.instagram.com/v21.0/{ig_user_id}/stories"
CAMPOS_API = "id,media_type,permalink,timestamp"
ARQUIVO_ESTADO_NOME = "story_post_estado.json"     # o mesmo da rodada 1 (H:\HypadoLocal\emulador\)
PACOTE = SEL.PACOTE
TEMPOS = {"elemento": 20.0, "abrir_app": 45.0, "post": 30.0, "editor": 30.0, "publicar": 30.0,
          "upload": 60.0, "bandeja": 6.0, "confirmacao": 10.0, "leitura": 1.0}
ZONA_DA_FIGURINHA = {"link": "link", "enquete": "enquete", "quiz": "enquete", "pergunta": "enquete",
                     "contagem": "enquete"}
TIPOS_COM_ARTE = ("chamada_post", "mais_sobre", "interacao", "enquete", "contagem")

# ids que NÃO estão no story_post_seletores.py e ainda são PALPITE (a coleta E4 confirma; ver docs/rodada2/E2.md)
IDS_PALPITE = {
    "link_url": ["link_sticker_url_edit_text", "link_sticker_url", "url_edit_text"],
    "link_rotulo_botao": ["link_sticker_custom_text_button", "link_sticker_customize_text"],
    "link_rotulo": ["link_sticker_custom_text_edit_text", "link_sticker_custom_text"],
    "lista_conta_linha": ["row_user_container", "row_user_textview", "account_row"],
    "folha_add_story": ["direct_share_sheet_add_to_story", "add_to_story_button"],
    "destaque_item": ["highlight_title", "highlight_name", "reel_item_title"],
    "destaque_novo": ["highlight_new", "new_highlight_button"],
    "cabecalho_story": ["reel_viewer_text_container"],
    "titulo_story": ["reel_viewer_title"],
    "midia_story": ["reel_viewer_media_container", "reel_viewer_image_view", "reel_viewer_media_layout"],
    "area_arte_editor": ["camera_preview", "story_preview", "edit_media_container"],
    "bandeja_item": ["asset_item", "sticker_item"],
}
TEXTOS_EXTRA = {
    "figurinha_link": ["link"],
    "figurinha_quiz": ["quiz"],
    "figurinha_pergunta": ["perguntas", "questions", "pergunta", "question"],
    "busca_link": ["link"],
    "busca_quiz": ["quiz"],
    "busca_pergunta": ["pergunta", "question"],
    "rotulo_link": ["Customize sticker text", "Personalizar texto", "Sticker text", "Texto da figurinha"],
    "destaque_novo": ["New", "Novo", "Nova", "Criar novo", "Add new"],
    "destaque_confirmar": ["Add", "Adicionar", "Done", "Concluir", "OK"],
    "preview_arte": ["Story preview", "Prévia do story", "Previa"],
}
_RX_MIN = re.compile(r"^(\d+)\s*(m|min|mins|minuto|minutos|minute|minutes)$")
_RX_SEG = re.compile(r"^(\d+)\s*(s|seg|segs|segundo|segundos|sec|secs|second|seconds)$")
_RX_DESC_MIN = re.compile(r"(\d+)\s*(m|min|mins|minuto|minutos|minute|minutes)\s+(ago|atras)\b")
_RX_DESC_SEG = re.compile(r"(\d+)\s*(s|seg|segundo|segundos|sec|second|seconds)\s+(ago|atras)\b")
_RX_DONO = re.compile(r"^(.+?)'s story", re.I)
_RX_EMULADOR = re.compile(r"^emulator-\d+$")
_MESES_PT = ["janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho", "agosto", "setembro",
             "outubro", "novembro", "dezembro"]
_MESES_EN = ["january", "february", "march", "april", "may", "june", "july", "august", "september",
             "october", "november", "december"]


# ===========================================================================
# Erros (código de saída em .codigo; mensagem em português)
# ===========================================================================
class FluxoErro(Exception):
    codigo = ERRO


class ContaErrada(FluxoErro):
    """A conta ativa não é a esperada (ou o post aberto é de outra conta): aborta."""


class OrcamentoEstourado(FluxoErro):
    """Passou dos 5 min por story."""


class StoryNaoDeAgora(FluxoErro):
    """No visualizador não apareceu o story recém-publicado (carimbo <= 5 min)."""


class DadosInvalidos(FluxoErro):
    pass


class PostJaFeito(FluxoErro):
    """1 story por post: já foi registrado (tocado/publicado/a conferir); nunca repete."""
    codigo = BLOQUEADO


class ForaDaFila(FluxoErro):
    """3 falhas no mesmo post: sai da fila automática até o Antônio olhar."""
    codigo = BLOQUEADO


class IntervaloCurto(FluxoErro):
    codigo = BLOQUEADO


# ===========================================================================
# Texto, carimbo de tempo
# ===========================================================================
def limpar_handle(s) -> str:
    """'@HP.Futebol ' -> 'hp.futebol' (só letras, números, ponto e _)."""
    t = normalizar(s).lstrip("@")
    return re.sub(r"[^a-z0-9._]", "", t)


def _limpo(txt) -> str:
    t = normalizar(txt)
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"^ha\s+", "", t)
    return re.sub(r"\s+(atras|ago)$", "", t).strip()


def minutos_de(texto, desc: str = "") -> float | None:
    """Minutos do carimbo do story: '3m'->3, 'Now'/'agora'->0, '1 min'->1, '30 s'->0; pelo content-desc
    '<conta>'s story, 3 minutes ago'->3. Hora/dia (1h, 2d) ou nada legível -> None."""
    t = _limpo(texto)
    if t:
        if t in {normalizar(x) for x in SEL.TIMESTAMP_AGORA}:
            return 0.0
        if _RX_SEG.match(t):
            return 0.0
        m = _RX_MIN.match(t)
        if m:
            return float(m.group(1))
    d = normalizar(desc)
    if d:
        if any(normalizar(x) in d for x in SEL.TIMESTAMP_AGORA):
            return 0.0
        if _RX_DESC_SEG.search(d):
            return 0.0
        m = _RX_DESC_MIN.search(d)
        if m:
            return float(m.group(1))
    return None


def eh_timestamp_de_agora(texto, desc: str = "", limite_min: float = LIMITE_MIN_AGORA) -> bool:
    """True se o carimbo diz que o story é de agora: 'Now', 'Just now', 'agora', 'agora mesmo', '^\\d+m$' com
    <= limite_min (o real é '3m'), '30 s', ou o content-desc '<conta>'s story, N minutes ago' com N <= limite_min.
    '7m', '1h', '2d' -> False."""
    m = minutos_de(texto, desc)
    return m is not None and m <= float(limite_min)


def dono_do_story(nos: list) -> str | None:
    """@ de quem é o story aberto: reel_viewer_title (confirmado) ou o content-desc "<conta>'s story, ...."""
    t = achar(nos, id=IDS_PALPITE["titulo_story"])
    if t and t.texto.strip():
        return limpar_handle(t.texto)
    c = achar(nos, id=IDS_PALPITE["cabecalho_story"])
    if c and c.desc:
        m = _RX_DONO.match(c.desc.strip())
        if m:
            return limpar_handle(m.group(1))
    return None


def eh_emulador(serial) -> bool:
    return bool(_RX_EMULADOR.match(str(serial or "")))


# ===========================================================================
# Relógio, orçamento, estado (JSON injetável)
# ===========================================================================
class RelogioReal:
    """monotonic/sleep (como o time) + agora() em hora de Brasília. Os testes injetam um falso."""

    def monotonic(self) -> float:
        return time.monotonic()

    def sleep(self, seg: float) -> None:
        if seg > 0:
            time.sleep(seg)

    def agora(self) -> datetime:
        return datetime.now(FUSO)


def _agora_de(relogio) -> datetime:
    f = getattr(relogio, "agora", None)
    return f() if callable(f) else datetime.now(FUSO)


class Orcamento:
    """<= 5 min por story (relógio injetado)."""

    def __init__(self, limite_seg: float, relogio):
        self.limite = float(limite_seg)
        self.relogio = relogio
        self.inicio = relogio.monotonic()

    def gasto(self) -> float:
        return self.relogio.monotonic() - self.inicio

    def restante(self) -> float:
        return max(0.0, self.limite - self.gasto())

    def verificar(self, onde: str = "") -> None:
        g = self.gasto()
        if g > self.limite:
            raise OrcamentoEstourado(f"passou do tempo máximo por story ({self.limite:.0f}s; já foram {g:.0f}s)"
                                     + (f" no passo '{onde}'" if onde else ""))


def arquivo_estado_padrao() -> Path:
    return raiz_local() / "emulador" / ARQUIVO_ESTADO_NOME


def arquivo_parada_padrao() -> Path:
    return sd.arquivo_parada_padrao()


def _dt(v) -> datetime | None:
    """ISO (com ou sem fuso; 'Z'; '+0000' da API da Meta) ou datetime -> datetime com fuso."""
    if v in (None, ""):
        return None
    if isinstance(v, datetime):
        d = v
    else:
        txt = str(v).strip().replace("Z", "+00:00")
        m = re.match(r"^(.*)([+-]\d{2})(\d{2})$", txt)
        if m and ":" not in txt[-5:]:
            txt = f"{m.group(1)}{m.group(2)}:{m.group(3)}"
        try:
            d = datetime.fromisoformat(txt)
        except ValueError:
            try:
                d = datetime.strptime(txt, "%Y-%m-%d %H:%M")
            except ValueError:
                return None
    return d if d.tzinfo else d.replace(tzinfo=FUSO)


class Estado:
    """O JSON de estado (postados, tentativas, ultimo_story_em, falhas) — o mesmo da rodada 1.

    caminho=None usa H:\\HypadoLocal\\emulador\\story_post_estado.json; dados= injeta o conteúdo
    (teste); gravar=False mantém só em memória (--simular). Gravação atômica pelo hpbase.
    """

    ETAPAS_FEITAS = ("antes_do_toque", "tocado", "publicado", "a_conferir")

    def __init__(self, caminho: Path | None = None, dados: dict | None = None, gravar: bool = True):
        self.caminho = Path(caminho) if caminho else (arquivo_estado_padrao() if gravar else None)
        self.gravar_em_disco = bool(gravar)
        self.dados = self._completar(dict(dados) if dados is not None else (self._ler() if self.caminho else {}))

    @staticmethod
    def _completar(e: dict) -> dict:
        e.setdefault("ultimo_story_em", None)
        for k, tipo in (("postados", dict), ("tentativas", dict), ("falhas", list)):
            if not isinstance(e.get(k), tipo):
                e[k] = tipo()
        return e

    def _ler(self) -> dict:
        d = ler_json(self.caminho, {}) if self.caminho else {}
        return d if isinstance(d, dict) else {}

    def gravar(self) -> None:
        if self.gravar_em_disco and self.caminho:
            self.dados["falhas"] = (self.dados.get("falhas") or [])[-50:]
            escrever_json(self.caminho, self.dados)

    def ja_postado(self, chave: str) -> str | None:
        """Etapa registrada ('tocado', 'publicado', 'a_conferir'...) ou None."""
        p = self.dados["postados"].get(str(chave))
        return (p.get("estado") or "registrado") if isinstance(p, dict) else None

    def registrar(self, chave: str, etapa: str, agora: datetime | None = None, **extra) -> bool:
        """Grava a etapa do story. etapa 'antes_do_toque' com o story já registrado -> False (não repete)."""
        chave = str(chave)
        agora = agora or datetime.now(FUSO)
        postados = self.dados["postados"]
        if etapa == "antes_do_toque":
            if chave in postados:
                return False
            postados[chave] = {"estado": "antes_do_toque", "quando": agora.isoformat(timespec="seconds"),
                               "feito": None, **extra}
            self.dados["ultimo_story_em"] = agora.isoformat(timespec="seconds")
        else:
            p = postados.setdefault(chave, {"quando": agora.isoformat(timespec="seconds"), "feito": None})
            p["estado"] = etapa
            p[f"{etapa}_em"] = agora.isoformat(timespec="seconds")
            p.update(extra)
        self.gravar()
        return True

    def tentativas(self, chave: str) -> int:
        try:
            return int(self.dados["tentativas"].get(str(chave), 0))
        except (TypeError, ValueError):
            return 0

    def fora_da_fila(self, chave: str, max_tentativas: int = MAX_TENTATIVAS) -> bool:
        return self.ja_postado(chave) is None and self.tentativas(chave) >= int(max_tentativas)

    def registrar_falha(self, chave: str, erro, passo: str = "", agora: datetime | None = None) -> int:
        """Conta a tentativa (só se o story ainda não foi registrado como tocado) e guarda a falha."""
        chave = str(chave)
        agora = agora or datetime.now(FUSO)
        if self.ja_postado(chave) is None:
            self.dados["tentativas"][chave] = self.tentativas(chave) + 1
        self.dados["falhas"].append({"quando": agora.isoformat(timespec="seconds"), "story": chave,
                                     "passo": passo, "erro": f"{type(erro).__name__}: {erro}"})
        self.gravar()
        return self.tentativas(chave)

    def falta_intervalo(self, agora: datetime, intervalo_seg: float = INTERVALO_MIN_SEG) -> float:
        """Segundos que faltam para poder soltar outro story (0 = liberado)."""
        ult = _dt(self.dados.get("ultimo_story_em"))
        if not ult:
            return 0.0
        return max(0.0, float(intervalo_seg) - (agora - ult).total_seconds())


@dataclass
class Contexto:
    """O que os fluxos precisam além do aparelho: estado, relógio, conferência pela API, limites."""
    estado: Estado
    relogio: object = field(default_factory=RelogioReal)
    log: object = None
    saida: Callable = print
    intervalo_min_seg: float = INTERVALO_MIN_SEG
    orcamento_seg: float = ORCAMENTO_SEG
    max_tentativas: int = MAX_TENTATIVAS
    get_json: Callable | None = None        # get_json(url, params) -> dict (no PC: publicador_meta.api)
    ig_user_id: str | None = None           # meta_tokens_meta.json -> contas["IG_<handle>"].id (só o id, nunca o token)
    ig_user_ids: dict = field(default_factory=dict)   # {handle: id} quando o pedido tem várias contas
    tentativas_api: int = 3
    espera_api_s: float = 20.0
    arquivo_parada: Path | None = None
    limite_pergunta: int = LIMITE_PERGUNTA
    tempos: dict = field(default_factory=lambda: dict(TEMPOS))

    def __post_init__(self):
        self.log = self.log or logging.getLogger("hp.story_fluxos")

    def parada(self) -> Path:
        return Path(self.arquivo_parada) if self.arquivo_parada else arquivo_parada_padrao()

    def agora(self) -> datetime:
        return _agora_de(self.relogio)

    def id_da_conta(self, conta: str) -> str | None:
        return self.ig_user_ids.get(limpar_handle(conta)) or self.ig_user_id

    def registrador(self, chave: str, **extra) -> Callable:
        """registrar(chave, etapa) que os fluxos chamam: grava no Estado com o relógio injetado."""
        def _r(ch, etapa, **mais):
            return self.estado.registrar(ch, etapa, agora=self.agora(), **{**extra, **mais})
        return _r


# ===========================================================================
# Ajudantes de tela (todos passam pelo aparelho; --simular devolve nós sintéticos e imprime o passo)
# ===========================================================================
def _tempos(t: dict | None) -> dict:
    out = dict(TEMPOS)
    if t:
        out.update({k: float(v) for k, v in t.items()})
    return out


def _sim(disp) -> bool:
    return bool(getattr(disp, "simular", False))


def _saida(disp) -> Callable:
    return getattr(disp, "saida", None) or print


def _passo(disp, texto: str) -> None:
    disp.passo = texto
    disp.log.info("passo: %s", texto)
    if _sim(disp):
        _saida(disp)(f"-> {texto}")
    orc = getattr(disp, "orcamento", None)
    if orc is not None:
        orc.verificar(texto)


def _sintetico(disp, crit: dict) -> No:
    w, h = disp.tamanho_tela()
    rot = (sd._lista(crit.get("rotulo")) or sd._lista(crit.get("texto")) or sd._lista(crit.get("desc")) or [""])[0]
    rid = (sd._lista(crit.get("id")) or [""])[0]
    return No(bounds=(w // 4, h // 4, 3 * w // 4, 3 * h // 4), id=str(rid), rid=str(rid), texto=str(rot),
              desc=str(rot), clicavel=True, classe="View")


def _esperar_qualquer(disp, alternativas: list, timeout_s: float) -> tuple:
    """(nó, índice da alternativa que apareceu)."""
    if _sim(disp):
        _saida(disp)("  esperar " + " ou ".join(sd.descrever(c) for c in alternativas))
        return _sintetico(disp, alternativas[0]), 0
    orc = getattr(disp, "orcamento", None)
    if orc is not None:
        orc.verificar("esperar " + sd.descrever(alternativas[0]))
    no = disp.esperar_qualquer(alternativas, timeout_s, disp_intervalo(disp))
    for i, crit in enumerate(alternativas):
        if no in achar_todos(disp.ultimos_nos, **crit):
            return no, i
    return no, 0


def _esperar(disp, timeout_s: float, **crit) -> No:
    return _esperar_qualquer(disp, [crit], timeout_s)[0]


def _esperar_sumir(disp, timeout_s: float, levantar: bool = True, **crit) -> bool:
    if _sim(disp):
        _saida(disp)(f"  esperar sumir {sd.descrever(crit)}")
        return True
    try:
        return disp.esperar_sumir(timeout_s, disp_intervalo(disp), **crit)
    except sd.ElementoNaoApareceu:
        if levantar:
            raise
        return False


def _condicao(disp, func: Callable, descricao: str, timeout_s: float, simulado=None, levantar: bool = True):
    """Lê a tela até func(nos) devolver algo verdadeiro (relógio injetado)."""
    if _sim(disp):
        _saida(disp)(f"  esperar {descricao}")
        return simulado if simulado is not None else True
    rel = disp.relogio
    fim = rel.monotonic() + float(timeout_s)
    while True:
        orc = getattr(disp, "orcamento", None)
        if orc is not None:
            orc.verificar(descricao)
        r = func(disp.dump())
        if r:
            return r
        if rel.monotonic() >= fim:
            if levantar:
                raise sd.ElementoNaoApareceu(f"não apareceu: {descricao}; o Instagram mudou?")
            return None
        rel.sleep(disp_intervalo(disp))


def _achar(disp, nos: list, **crit) -> No | None:
    if _sim(disp):
        return _sintetico(disp, crit)
    return achar(nos, **crit)


def disp_intervalo(disp) -> float:
    return float(getattr(disp, "intervalo_leitura", TEMPOS["leitura"]))


def _dentro(no: No, caixa: tuple) -> bool:
    b = no.bounds
    return b[0] >= caixa[0] and b[1] >= caixa[1] and b[2] <= caixa[2] and b[3] <= caixa[3]


def _clicavel_de(nos: list, no: No) -> No:
    """O próprio nó se for clicável; senão o menor nó clicável que o contém (a linha/botão de verdade)."""
    if no.clicavel:
        return no
    cands = [c for c in nos if c.clicavel and c.area > 0 and c is not no and _dentro(no, c.bounds)]
    return min(cands, key=lambda c: c.area) if cands else no


def _topo(nos: list) -> No | None:
    vis = [n for n in nos if n.area > 0]
    return min(vis, key=lambda n: (n.bounds[1], n.bounds[0])) if vis else None


def _ponto_em(caixa: tuple, fx: float, fy: float) -> tuple:
    return (int(round(caixa[0] + fx * (caixa[2] - caixa[0]))), int(round(caixa[1] + fy * (caixa[3] - caixa[1]))))


# ===========================================================================
# Perfil e troca de conta
# ===========================================================================
def conta_ativa(nos: list) -> str | None:
    """O @ do perfil aberto: texto dentro do action_bar_username_container (confirmado) ou conta_titulo (palpite)."""
    c = achar(nos, id=SEL.IDS["conta_container"])
    if c:
        for n in nos:
            if n is not c and n.area > 0 and n.texto.strip() and _dentro(n, c.bounds):
                h = limpar_handle(n.texto)
                if h:
                    return h
        h = limpar_handle(c.texto or c.desc)
        if h:
            return h
    t = achar(nos, id=SEL.IDS["conta_titulo"])
    if t is not None and t.texto:
        return limpar_handle(t.texto) or None
    return None


def linha_da_conta(nos: list, handle: str) -> No | None:
    """A linha do @handle na lista de contas (fora do cabeçalho do perfil), já como nó clicável."""
    handle = limpar_handle(handle)
    c = achar(nos, id=SEL.IDS["conta_container"])
    for n in nos:
        if n.area <= 0 or (c and (n is c or _dentro(n, c.bounds))):
            continue
        if n.texto and limpar_handle(n.texto) == handle:
            return _clicavel_de(nos, n)
    for n in nos:
        if n.area <= 0 or (c and (n is c or _dentro(n, c.bounds))):
            continue
        d = normalizar(n.desc).lstrip("@")
        if d and (d == handle or d.startswith(handle + ",") or d.startswith(handle + " ")):
            return _clicavel_de(nos, n)
    return None


def ir_para_perfil(disp, tempos: dict | None = None) -> list:
    """Aba Perfil (profile_tab, palpite) até o action_bar_username_container (confirmado) aparecer."""
    t = _tempos(tempos)
    nos = disp.dump()
    if not _sim(disp) and achar(nos, id=SEL.IDS["conta_container"]):
        return nos
    aba = None
    for _ in range(4):
        aba = _achar(disp, nos, id=SEL.IDS["aba_perfil"]) or _achar(disp, nos, desc=["Profile", "Perfil"], contem=False)
        if aba or _sim(disp):
            break
        disp.voltar()
        nos = disp.dump()
    disp.tocar(aba, "aba Perfil")
    _esperar(disp, t["elemento"], id=SEL.IDS["conta_container"])
    return disp.ultimos_nos


def trocar_conta(disp, handle: str, tempos: dict | None = None) -> str:
    """Perfil -> nome da conta -> @handle na lista -> LÊ de volta o @ ativo (diferente -> ContaErrada).

    Tela de login/código/termos: o dump() do aparelho grava a parada e sobe AvisoMetaDetectado (código 3);
    aqui nunca se digita senha nem se toca em Entrar.
    """
    t = _tempos(tempos)
    handle = limpar_handle(handle)
    if not handle:
        raise DadosInvalidos("conta vazia: não sei para qual @ trocar")
    _passo(disp, f"trocar para @{handle}")
    nos = ir_para_perfil(disp, t)
    atual = conta_ativa(nos)
    if atual == handle and not _sim(disp):
        disp.log.info("já estava em @%s", handle)
        return handle
    disp.tocar(_achar(disp, nos, id=SEL.IDS["conta_container"]), "nome da conta (abre a lista de contas)")
    linha = _condicao(disp, lambda ns: linha_da_conta(ns, handle), f"@{handle} na lista de contas",
                      t["elemento"], simulado=_sintetico(disp, {"texto": handle}), levantar=False)
    if linha is None:
        raise ContaErrada(f"@{handle} não aparece na lista de contas do aparelho: o Antônio faz login nela uma vez, "
                          "à mão (o script nunca digita senha). Abortei sem trocar.")
    disp.tocar(linha, f"conta @{handle}")
    ok = _condicao(disp, lambda ns: conta_ativa(ns) == handle, f"perfil ativo = @{handle}", t["elemento"],
                   simulado=True, levantar=False)
    if not ok:
        atual = conta_ativa(disp.ultimos_nos)
        raise ContaErrada(f"depois da troca a conta ativa é @{atual or '?'}, esperado @{handle}: abortei")
    disp.log.info("conta conferida: @%s", handle)
    return handle


# ===========================================================================
# Story a partir da arte: galeria -> editor -> figurinhas -> zona -> Seu story
# ===========================================================================
def enviar_arte_para_galeria(disp, arte) -> dict:
    _passo(disp, f"mandar a arte {Path(str(arte)).name} para a galeria")
    return disp.empurrar_arte(arte)


def abrir_editor_da_galeria(disp, tempos: dict | None = None) -> list:
    """Perfil -> + (criar) -> [Story] -> [galeria] -> foto mais recente -> editor (asset_button à vista)."""
    t = _tempos(tempos)
    _passo(disp, "criar story: + > Story > galeria > arte mais recente")
    nos = ir_para_perfil(disp, t)
    criar = _achar(disp, nos, id=SEL.IDS["criar"]) or _achar(disp, nos, desc=SEL.TEXTOS["criar_desc"], contem=False)
    disp.tocar(criar, "Criar (+)")
    alternativas = [{"id": SEL.IDS["galeria_item"]}, {"rotulo": SEL.TEXTOS["menu_story"], "contem": False},
                    {"id": SEL.IDS["galeria"]}, {"desc": SEL.TEXTOS["galeria_desc"]}]
    no, i = _esperar_qualquer(disp, alternativas, t["editor"])
    if i == 1:                                   # menu do "+": Story
        disp.tocar(no, "Story")
        no, i = _esperar_qualquer(disp, [alternativas[0], alternativas[2], alternativas[3]], t["editor"])
        i = 0 if i == 0 else 2
    if i >= 2:                                   # câmera: botão da galeria
        disp.tocar(no, "galeria")
        _esperar(disp, t["editor"], id=SEL.IDS["galeria_item"])
    itens = achar_todos(disp.ultimos_nos, id=SEL.IDS["galeria_item"]) if not _sim(disp) else [no]
    mais_recente = _topo(itens) or no
    disp.tocar(mais_recente, "arte mais recente da galeria")
    _esperar(disp, t["editor"], id=SEL.IDS["figurinhas"])
    return disp.ultimos_nos


def area_da_arte(nos: list, tela: tuple) -> tuple:
    """Onde a arte aparece no editor (nó da prévia, palpite) — senão a tela inteira."""
    W, H = tela
    for n in achar_todos(nos, id=IDS_PALPITE["area_arte_editor"]) + achar_todos(nos, desc=TEXTOS_EXTRA["preview_arte"]):
        if n.area >= 0.4 * W * H:
            return n.bounds
    return (0, 0, W, H)


def _figurinha_na_bandeja(nos: list, textos: list) -> No | None:
    for n in achar_todos(nos, rotulo=textos):
        if n.classe.endswith("EditText") or sd._casa_id(n, SEL.IDS["busca_figurinha"]):
            continue
        return _clicavel_de(nos, n)
    return None


def abrir_figurinha(disp, tipo: str, tempos: dict | None = None) -> No:
    """asset_button (confirmado) -> figurinha na bandeja; não está à vista -> busca ("link", "poll"...)."""
    t = _tempos(tempos)
    textos = SEL.TEXTOS.get(f"figurinha_{tipo}") or TEXTOS_EXTRA.get(f"figurinha_{tipo}") or [tipo]
    buscas = SEL.TEXTOS.get(f"busca_{tipo}") or TEXTOS_EXTRA.get(f"busca_{tipo}") or [tipo]
    _passo(disp, f"figurinha de {tipo}")
    disp.tocar(_esperar(disp, t["editor"], id=SEL.IDS["figurinhas"]), "figurinhas (asset_button)")
    alvo = _condicao(disp, lambda ns: _figurinha_na_bandeja(ns, textos), f"figurinha de {tipo} na bandeja",
                     t["bandeja"], simulado=_sintetico(disp, {"texto": textos[0]}), levantar=False)
    if alvo is None:
        busca, _ = _esperar_qualquer(disp, [{"id": SEL.IDS["busca_figurinha"]}, {"rotulo": SEL.TEXTOS["busca_rotulo"]}],
                                     t["elemento"])
        for i, termo in enumerate(buscas):
            disp.digitar(termo, campo=busca, limpar=bool(i))
            alvo = _condicao(disp, lambda ns: _figurinha_na_bandeja(ns, textos), f"resultado da busca '{termo}'",
                             t["bandeja"], levantar=False)
            if alvo:
                break
    if alvo is None:
        raise sd.ElementoNaoApareceu(f"não achei a figurinha de {tipo} na bandeja nem pela busca")
    disp.tocar(alvo, f"figurinha de {tipo}")
    return alvo


def _campo_texto(nos: list, ids: list, textos: list | None = None, excluir: No | None = None) -> No | None:
    n = achar(nos, id=ids)
    if n:
        return n
    campos = [c for c in nos if c.classe.endswith("EditText") and c.area > 0 and c is not excluir]
    if textos:
        for c in campos:
            if sd._casa_texto(c.texto, textos, True) or sd._casa_texto(c.desc, textos, True):
                return c
    for c in campos:
        if c.focado:
            return c
    return campos[0] if campos else None


def preencher_link(disp, url: str, rotulo: str | None = None, tempos: dict | None = None) -> None:
    """Campo da URL -> URL (ASCII) -> rótulo curto ("Ver post", se o campo existir) -> Concluir."""
    t = _tempos(tempos)
    url = str(url or "").strip()
    if not re.match(r"^https?://\S+$", url):
        raise DadosInvalidos(f"url da figurinha de link inválida: {url!r}")
    _passo(disp, "figurinha de link: URL e rótulo")
    campo = _condicao(disp, lambda ns: _campo_texto(ns, IDS_PALPITE["link_url"], ["URL", "Link", "http"]),
                      "campo da URL", t["elemento"], simulado=_sintetico(disp, {"id": IDS_PALPITE["link_url"][0]}))
    disp.digitar(url, campo=campo)
    if rotulo and str(rotulo).strip():
        rot = str(rotulo).strip()[:fila.LIMITE_ROTULO]
        nos = disp.dump()
        btn = _achar(disp, nos, id=IDS_PALPITE["link_rotulo_botao"]) or _achar(disp, nos, rotulo=TEXTOS_EXTRA["rotulo_link"])
        if btn is not None:
            disp.tocar(btn, "personalizar o texto do link")
        campo2 = _condicao(disp, lambda ns: _campo_texto(ns, IDS_PALPITE["link_rotulo"], ["Sticker text", "Texto"],
                                                          excluir=achar(ns, id=IDS_PALPITE["link_url"])),
                           "campo do rótulo do link", t["bandeja"],
                           simulado=_sintetico(disp, {"id": IDS_PALPITE["link_rotulo"][0]}), levantar=False)
        if campo2 is not None and campo2 is not campo:
            disp.digitar(rot, campo=campo2)
        else:
            disp.log.warning("o campo do rótulo do link não apareceu; o link sai sem rótulo '%s'", rot)
    disp.tocar(_esperar(disp, t["elemento"], id=SEL.IDS["concluir"]), "Concluir (done_button)")


def _campos_opcoes(nos: list) -> list:
    por_id = achar_todos(nos, id=SEL.IDS["enquete_opcao"])
    if por_id:
        return sorted(por_id, key=lambda n: (n.bounds[1], n.bounds[0]))
    perg = achar(nos, id=SEL.IDS["enquete_pergunta"])
    topo = perg.bounds[3] if perg else 0
    campos = [n for n in nos if n.classe.endswith("EditText") and n.area > 0
              and not sd._casa_id(n, SEL.IDS["enquete_pergunta"]) and n.bounds[1] >= topo]
    return sorted(campos, key=lambda n: (n.bounds[1], n.bounds[0]))


def pergunta_para_figurinha(pergunta, limite: int = LIMITE_PERGUNTA) -> str:
    """<= limite pelo story_post_lote (nunca corta palavra; não cabe -> DadosInvalidos)."""
    limpa = LOTE.limpar(pergunta)
    if not limpa:
        raise DadosInvalidos("a enquete está sem pergunta")
    if len(limpa) <= int(limite):
        return limpa
    try:
        return LOTE.encurtar_pergunta(limpa, int(limite))
    except LOTE.LoteErro as e:
        raise DadosInvalidos(str(e)) from None


def preencher_enquete(disp, pergunta: str, opcoes: list, limite: int = LIMITE_PERGUNTA,
                      tempos: dict | None = None) -> str:
    """poll_sticker_v2_question (<= 25) + opções (2 a 4; "Add option" quando faltar campo) -> done_button."""
    t = _tempos(tempos)
    texto = pergunta_para_figurinha(pergunta, limite)
    ops = [LOTE.limpar(o) for o in (opcoes or [])]
    if not (LOTE.MIN_OPCOES <= len(ops) <= LOTE.MAX_OPCOES) or any(not o for o in ops):
        raise DadosInvalidos(f"a enquete precisa de {LOTE.MIN_OPCOES} a {LOTE.MAX_OPCOES} opções não vazias (veio {ops})")
    _passo(disp, f"enquete: '{texto}' com {len(ops)} opções")
    disp.digitar(texto, campo=_esperar(disp, t["elemento"], id=SEL.IDS["enquete_pergunta"]))
    sint = [_sintetico(disp, {"texto": f"opcao {i + 1}"}) for i in range(len(ops))]
    for i, op in enumerate(ops):
        campos = _condicao(disp, lambda ns, i=i: (lambda c: c if len(c) > i else None)(_campos_opcoes(ns)),
                           f"campo da opção {i + 1}", t["bandeja"] / 2, simulado=sint, levantar=False)
        if not campos:
            disp.tocar(_esperar(disp, t["elemento"], rotulo=SEL.TEXTOS["enquete_add_opcao"]), "adicionar opção")
            campos = _condicao(disp, lambda ns, i=i: (lambda c: c if len(c) > i else None)(_campos_opcoes(ns)),
                               f"campo da opção {i + 1}", t["elemento"], simulado=sint)
        disp.digitar(op, campo=campos[i], limpar=True)
    disp.tocar(_esperar(disp, t["elemento"], id=SEL.IDS["concluir"]), "Concluir (done_button)")
    return texto


def _mes_ano_na_tela(nos: list, alvo: date) -> bool:
    nomes = (_MESES_PT[alvo.month - 1], _MESES_EN[alvo.month - 1], _MESES_EN[alvo.month - 1][:3])
    ano = str(alvo.year)
    for n in nos:
        for campo in (n.texto, n.desc):
            t = normalizar(campo)
            if t and ano in t and any(nome in t for nome in nomes):
                return True
    return False


def _achar_dia(nos: list, alvo: date) -> No | None:
    dia = str(alvo.day)
    nomes = (_MESES_PT[alvo.month - 1], _MESES_EN[alvo.month - 1])
    for n in nos:
        if n.area <= 0:
            continue
        d = normalizar(n.desc)
        if d and re.search(r"\b0?%s\b" % dia, d) and any(nome in d for nome in nomes):
            return _clicavel_de(nos, n)
    for n in nos:
        if n.area > 0 and n.texto.strip() == dia and n.largura < 400:
            return _clicavel_de(nos, n)
    return None


def escolher_data(disp, alvo: date, tempos: dict | None = None, max_meses: int = 14) -> None:
    """Calendário do Android: avança de mês (android:id/next) até o mês/ano certo e toca no dia -> OK."""
    t = _tempos(tempos)
    _passo(disp, f"calendário: {alvo.isoformat()}")
    if _sim(disp):
        disp.tocar(_sintetico(disp, {"texto": str(alvo.day)}), f"dia {alvo.day}")
        disp.tocar(_sintetico(disp, {"id": SEL.IDS["data_ok"][0]}), "OK do calendário")
        return
    for _ in range(max_meses):
        nos = disp.dump()
        if _mes_ano_na_tela(nos, alvo):
            dia = _achar_dia(nos, alvo)
            if dia is None:
                raise sd.ElementoNaoApareceu(
                    f"o calendário mostra {alvo.strftime('%m/%Y')} mas não expõe o dia {alvo.day} no dump "
                    "(DatePicker desenha os dias): coletar essa tela (E4) e ajustar escolher_data")
            disp.tocar(dia, f"dia {alvo.day}")
            disp.tocar(_esperar(disp, t["elemento"], id=SEL.IDS["data_ok"]), "OK do calendário")
            return
        prox = achar(nos, id=SEL.IDS["data_proximo_mes"]) or achar(nos, desc=["Next month", "Próximo mês", "Proximo mes"])
        if prox is None:
            raise sd.ElementoNaoApareceu("não achei o botão de próximo mês no calendário (android:id/next)")
        disp.tocar(prox, "próximo mês")
    raise sd.ElementoNaoApareceu(f"não cheguei a {alvo.strftime('%m/%Y')} em {max_meses} meses")


def preencher_contagem(disp, titulo: str, data_fim, tempos: dict | None = None) -> None:
    """Título (<= 30) -> data final pelo calendário -> done_button. Ids de contagem são palpite (E4)."""
    t = _tempos(tempos)
    titulo = str(titulo or "").strip()[:fila.LIMITE_ROTULO]
    alvo = data_fim if isinstance(data_fim, date) else datetime.strptime(str(data_fim), "%Y-%m-%d").date()
    _passo(disp, f"contagem regressiva: '{titulo}' até {alvo.isoformat()}")
    campo = _condicao(disp, lambda ns: _campo_texto(ns, SEL.IDS["contagem_titulo"], ["Countdown", "Contagem", "Title", "Título"]),
                      "campo do título da contagem", t["elemento"],
                      simulado=_sintetico(disp, {"id": SEL.IDS["contagem_titulo"][0]}))
    disp.digitar(titulo, campo=campo)
    nos = disp.dump()
    data = _achar(disp, nos, id=SEL.IDS["contagem_data"]) or _achar(disp, nos, rotulo=SEL.TEXTOS["definir_data"])
    disp.tocar(data, "data final da contagem")
    escolher_data(disp, alvo, t)
    disp.tocar(_esperar(disp, t["elemento"], id=SEL.IDS["concluir"]), "Concluir (done_button)")


def figurinha_nova(antes: list, depois: list, area: tuple, pistas: list | None = None) -> No | None:
    """O nó da figurinha que acabou de entrar no editor: está em `depois`, não estava em `antes`, dentro da
    área da arte, nem minúsculo nem a área inteira; prefere o que traz uma pista (rótulo/pergunta/"link"/"poll")."""
    def chave(n: No):
        return (n.id, n.texto, n.desc, n.bounds)
    vistos = {chave(n) for n in antes}
    aw, ah = max(1, area[2] - area[0]), max(1, area[3] - area[1])
    novos = [n for n in depois if chave(n) not in vistos and n.area > 0 and _dentro(n, area)
             and 0.002 * aw * ah <= n.area <= 0.8 * aw * ah]
    if not novos:
        return None
    pistas = [p for p in (pistas or []) if p]
    com_pista = [n for n in novos if pistas and sd._casa_texto(n.rotulo, pistas, True)]
    if com_pista:
        return max(com_pista, key=lambda n: n.area)
    return max(novos, key=lambda n: n.area)


def posicionar_figurinha(disp, antes: list, zona: list | tuple | None, tipo: str, pistas: list | None = None,
                         ms: int = ARRASTAR_MS) -> dict:
    """Arrasta a figurinha (centro dos bounds reais, lidos no dump depois do Concluir) até o centro da zona."""
    _passo(disp, f"posicionar a figurinha de {tipo} na zona da arte")
    res = {"tipo": tipo, "arrastada": False, "zona": list(zona) if zona else None, "na_zona": None}
    if not zona:
        disp.log.warning("a arte não tem zona para a figurinha de %s; deixo onde o Instagram pôs", tipo)
        return res
    tela = disp.tamanho_tela()
    if _sim(disp):
        fig = _sintetico(disp, {"desc": f"figurinha de {tipo}"})
    else:
        fig = figurinha_nova(antes, disp.dump(), area_da_arte(disp.ultimos_nos, tela), pistas)
    if fig is None:
        disp.log.warning("não achei a figurinha de %s no dump do editor; não arrasto (confira na tela)", tipo)
        return res
    destino = fila.centro_zona(zona)
    disp.deslizar(fig.centro, destino, ms=int(ms))
    res.update({"arrastada": True, "de": list(fig.centro), "para": list(destino), "rotulo": fig.rotulo or fig.id})
    if not _sim(disp):
        depois = disp.dump()
        mesma = [n for n in depois if (n.id, n.texto, n.desc) == (fig.id, fig.texto, fig.desc) and n.area > 0]
        if mesma:
            cx, cy = mesma[0].centro
            res["na_zona"] = bool(zona[0] <= cx <= zona[2] and zona[1] <= cy <= zona[3])
            if not res["na_zona"]:
                disp.log.warning("a figurinha de %s ficou em (%d,%d), fora da zona %s; confira na tela antes de confiar",
                                 tipo, cx, cy, list(zona))
    return res


def publicar_seu_story(disp, chave: str, registrar: Callable | None = None, tempos: dict | None = None) -> str:
    """Registra ANTES do toque ("antes_do_toque"; False = já saiu, não repete) -> toca em "Seu story"
    (your_story_share_shortcut_button) -> espera o botão e o indicador de envio sumirem -> "tocado".
    Falhou DEPOIS do toque -> "a_conferir" (nunca toca de novo)."""
    t = _tempos(tempos)
    _passo(disp, "publicar: Seu story")
    botao = _esperar(disp, t["editor"], id=SEL.IDS["publicar_seu_story"])
    if registrar is not None and registrar(chave, "antes_do_toque") is False:
        raise PostJaFeito(f"o story {chave} já foi registrado (1 story por post): não toco de novo")
    disp.tocar(botao, "Seu story (publicar)")
    estado = "tocado"
    try:
        _esperar_sumir(disp, t["publicar"], id=SEL.IDS["publicar_seu_story"])
        _passo(disp, "esperar o envio terminar")
        _esperar_sumir(disp, t["upload"], rotulo=SEL.TEXTOS["enviando"])
    except sd.AvisoMetaDetectado:
        if registrar is not None:
            registrar(chave, "a_conferir", motivo="aviso da Meta depois do toque")
        raise
    except (sd.ElementoNaoApareceu, sd.DumpFalhou, OrcamentoEstourado) as e:
        estado = "a_conferir"
        disp.log.warning("depois de tocar em 'Seu story' não confirmei o envio (%s): fica 'a conferir', não repito", e)
    if registrar is not None:
        registrar(chave, estado)
    return estado


def _lista_figurinhas(figurinhas) -> list:
    if figurinhas is None:
        return []
    if isinstance(figurinhas, dict):
        figurinhas = [figurinhas]
    out = []
    for f in figurinhas:
        if isinstance(f, str):
            f = {"tipo": f}
        if not isinstance(f, dict):
            raise DadosInvalidos(f"figurinha inválida: {f!r}")
        tipo = normalizar(f.get("tipo"))
        if not tipo or tipo == "null":
            continue
        if tipo not in fila.FIGURINHAS:
            raise DadosInvalidos(f"figurinha '{tipo}' não existe; use {', '.join(fila.FIGURINHAS)}")
        out.append({**f, "tipo": tipo})
    return out


def zonas_da_arte(disp, arte, zonas, figs: list, nos_editor: list) -> dict:
    """As zonas do <arte>_zonas.json já na tela real (fração × área onde a arte aparece no editor)."""
    if not figs:
        return {}
    tela = disp.tamanho_tela()
    area = area_da_arte(nos_editor, tela)
    try:
        return fila.ler_zonas(zonas or arte, tela, area)
    except fila.FilaInvalida as e:
        if not _sim(disp):
            raise DadosInvalidos(str(e)) from None
        # --simular sem o _zonas.json: usa as zonas padrão da marca (§4.6) só para mostrar o roteiro
        disp.log.warning("(simular) sem o _zonas.json (%s): zonas padrão da marca", e)
        la, al = fila.TELA_ARTE
        out = {}
        for nome, ret in (("link", marca.ZONA_LINK), ("enquete", marca.ZONA_ENQUETE)):
            fr = [ret[0] / la, ret[1] / al, ret[2] / la, ret[3] / al]
            out[nome] = fila.converter_zona(fr, tela, area)
        return out


def story_da_arte(disp, arte, figurinhas, destaque: str | None = None, zonas=None, registrar: Callable | None = None,
                  chave: str | None = None, conta: str | None = None, tempos: dict | None = None,
                  limite_pergunta: int = LIMITE_PERGUNTA) -> dict:
    """Arte -> galeria (a mais recente) -> editor -> figurinhas -> zona -> "Seu story" -> envio -> [destaque]."""
    t = _tempos(tempos)
    figs = _lista_figurinhas(figurinhas)
    chave = str(chave or Path(str(arte)).stem)
    res = {"chave": chave, "arte": str(arte), "figurinhas": [], "estado": None, "conta": conta}
    _passo(disp, f"story da arte {Path(str(arte)).name} ({', '.join(f['tipo'] for f in figs) or 'sem figurinha'})")
    res["galeria"] = enviar_arte_para_galeria(disp, arte)
    antes = abrir_editor_da_galeria(disp, t)
    zonas_px = zonas_da_arte(disp, arte, zonas, figs, antes)
    for f in figs:
        tipo = f["tipo"]
        abrir_figurinha(disp, tipo, t)
        pistas = []
        if tipo == "link":
            preencher_link(disp, f.get("url"), f.get("rotulo") or fila.ROTULO_LINK_PADRAO, t)
            pistas = [f.get("rotulo") or fila.ROTULO_LINK_PADRAO, "link"]
        elif tipo in ("enquete", "quiz"):
            texto = preencher_enquete(disp, f.get("pergunta") or f.get("pergunta_publico") or f.get("texto"),
                                      f.get("opcoes"), limite_pergunta, t)
            pistas = [texto, "poll", "enquete", "quiz"]
        elif tipo == "pergunta":
            campo = _condicao(disp, lambda ns: _campo_texto(ns, [], ["Ask me", "Pergunte", "question"]),
                              "campo da pergunta", t["elemento"], simulado=_sintetico(disp, {"texto": "Ask me"}))
            disp.digitar(pergunta_para_figurinha(f.get("pergunta") or f.get("pergunta_publico"), limite_pergunta), campo=campo)
            disp.tocar(_esperar(disp, t["elemento"], id=SEL.IDS["concluir"]), "Concluir (done_button)")
            pistas = ["question", "pergunta"]
        elif tipo == "contagem":
            preencher_contagem(disp, f.get("rotulo") or f.get("titulo") or "", f.get("data"), t)
            pistas = [f.get("rotulo") or "", "countdown", "contagem"]
        zona = zonas_px.get(ZONA_DA_FIGURINHA.get(tipo, "link")) or zonas_px.get("link") or zonas_px.get("enquete")
        res["figurinhas"].append(posicionar_figurinha(disp, antes, zona, tipo, pistas))
        antes = disp.ultimos_nos
    res["estado"] = publicar_seu_story(disp, chave, registrar, t)
    if destaque and res["estado"] == "tocado":
        try:
            res["destaque"] = adicionar_ao_destaque(disp, destaque, conta, tempos=t)
        except (sd.ElementoNaoApareceu, StoryNaoDeAgora, ContaErrada, sd.DumpFalhou, OrcamentoEstourado) as e:
            res["destaque"] = {"destaque": destaque, "erro": f"{type(e).__name__}: {e}"}
            disp.log.warning("o story saiu, mas o destaque '%s' falhou: %s", destaque, e)
    return res


# ===========================================================================
# Compartilhar um post no story (fluxo da rodada 1, no aparelho escolhido)
# ===========================================================================
def _primeiro_da_grade(nos: list) -> No | None:
    itens = [n for n in achar_todos(nos, id=SEL.IDS["grade_item"]) if not re.search(r"fixad|pinned", normalizar(n.desc))]
    return _topo(itens)


def abrir_post_pela_grade(disp, handle: str, titulo: str | None, tempos: dict | None = None) -> None:
    """Plano B: primeiro post (não fixado) da grade do perfil, conferindo o título na legenda."""
    t = _tempos(tempos)
    if not titulo:
        raise sd.ElementoNaoApareceu("o link não abriu o post e sem título não dá para conferir na grade: abortei")
    _passo(disp, "plano B: abrir o post pela grade do perfil")
    nos = ir_para_perfil(disp, t)
    item = _condicao(disp, _primeiro_da_grade, "primeiro post da grade", t["elemento"],
                     simulado=_sintetico(disp, {"id": SEL.IDS["grade_item"][0]}))
    disp.tocar(item, "primeiro post da grade")
    _esperar(disp, t["post"], id=SEL.IDS["compartilhar"])
    alvo = normalizar(titulo)[:30]
    achou = _condicao(disp, lambda ns: any(alvo in normalizar(n.texto) for n in ns), "legenda com o título do post",
                      8, simulado=True, levantar=False)
    if not achou:
        raise sd.ElementoNaoApareceu("plano B: o post aberto não tem o título esperado; não compartilho post errado")


def abrir_post(disp, link: str, handle: str, titulo: str | None = None, tempos: dict | None = None) -> None:
    """Deep link (am start -a VIEW -d <link> -p com.instagram.android); plano B pela grade; confere o autor."""
    t = _tempos(tempos)
    _passo(disp, "abrir o post pelo link")
    disp.abrir_link(link)
    try:
        _esperar(disp, t["post"], id=SEL.IDS["compartilhar"])
    except sd.ElementoNaoApareceu:
        disp.log.warning("o link não abriu o post; tentando a grade do perfil")
        abrir_post_pela_grade(disp, handle, titulo, t)
    autor = _topo(achar_todos(disp.ultimos_nos, id=SEL.IDS["autor_post"]))
    if autor is not None and autor.texto and limpar_handle(autor.texto) != limpar_handle(handle):
        raise ContaErrada(f"o post aberto é de @{limpar_handle(autor.texto)}, não de @{limpar_handle(handle)}: abortei")


def compartilhar_post_no_story(disp, link: str, handle: str, titulo: str | None = None, registrar: Callable | None = None,
                               chave: str | None = None, destaque: str | None = None, tempos: dict | None = None) -> dict:
    """Post -> Enviar (row_feed_button_share) -> "Add to story"/"Adicionar ao story" -> "Seu story" -> [destaque]."""
    t = _tempos(tempos)
    handle = limpar_handle(handle)
    chave = str(chave or link)
    res = {"chave": chave, "link": link, "conta": handle, "estado": None}
    abrir_post(disp, link, handle, titulo, t)
    _passo(disp, "Enviar > Adicionar ao story > Seu story")
    disp.tocar(_topo(achar_todos(disp.ultimos_nos, id=SEL.IDS["compartilhar"])) if not _sim(disp)
               else _sintetico(disp, {"id": SEL.IDS["compartilhar"]}), "Enviar")
    add, _ = _esperar_qualquer(disp, [{"rotulo": SEL.TEXTOS["add_story"]}, {"id": IDS_PALPITE["folha_add_story"]}],
                               t["elemento"])
    disp.tocar(_clicavel_de(disp.ultimos_nos, add) if not _sim(disp) else add, "Adicionar ao story")
    res["estado"] = publicar_seu_story(disp, chave, registrar, t)
    if destaque and res["estado"] == "tocado":
        try:
            res["destaque"] = adicionar_ao_destaque(disp, destaque, handle, tempos=t)
        except (sd.ElementoNaoApareceu, StoryNaoDeAgora, ContaErrada, sd.DumpFalhou, OrcamentoEstourado) as e:
            res["destaque"] = {"destaque": destaque, "erro": f"{type(e).__name__}: {e}"}
            disp.log.warning("o story saiu, mas o destaque '%s' falhou: %s", destaque, e)
    return res


# ===========================================================================
# Destaque: o próprio story de agora -> Highlight -> nome
# ===========================================================================
def _ponto_avancar(nos: list, tela: tuple) -> tuple:
    """Onde tocar para passar o story: 92 % da largura, 30 % da altura da MÍDIA (bounds do dump); sem o nó da
    mídia, a mesma fração da tela do aparelho (wm size). Nunca um número fixo."""
    m = achar(nos, id=IDS_PALPITE["midia_story"])
    caixa = m.bounds if m and m.area > 0 else (0, 0, tela[0], tela[1])
    return _ponto_em(caixa, 0.92, 0.30)


def avancar_ate_story_de_agora(disp, conta: str | None = None, limite_min: float = LIMITE_MIN_AGORA,
                               max_avancos: int = MAX_STORIES_AVANCAR, tempos: dict | None = None) -> No:
    """No visualizador do próprio story, passa até o carimbo dizer "de agora" (3m, Now...). Confere o dono."""
    t = _tempos(tempos)
    _passo(disp, f"achar o story de agora (carimbo <= {limite_min:.0f} min)")
    if _sim(disp):
        return _sintetico(disp, {"id": SEL.IDS["story_timestamp"][0], "texto": "Now"})
    _esperar(disp, t["elemento"], id=SEL.IDS["story_timestamp"])
    sumiu = 0
    conta = limpar_handle(conta) if conta else None
    for _ in range(int(max_avancos)):
        nos = disp.dump()
        ts = achar(nos, id=SEL.IDS["story_timestamp"])
        if ts is None:
            sumiu += 1
            if sumiu >= 3:
                raise sd.ElementoNaoApareceu("o visualizador do story fechou antes de achar o story de agora")
            disp.relogio.sleep(disp_intervalo(disp))
            continue
        sumiu = 0
        dono = dono_do_story(nos)
        if conta and dono and dono != conta:
            raise ContaErrada(f"o story aberto é de @{dono}, não de @{conta}: não mexo no destaque de outra conta")
        cab = achar(nos, id=IDS_PALPITE["cabecalho_story"])
        if eh_timestamp_de_agora(ts.texto, cab.desc if cab else "", limite_min):
            disp.log.info("story de agora: carimbo '%s' (%s)", ts.texto, cab.desc if cab else "")
            return ts
        disp.log.info("carimbo '%s' não é de agora; próximo story", ts.texto)
        disp.tocar(_ponto_avancar(nos, disp.tamanho_tela()), "próximo story")
    raise StoryNaoDeAgora(f"não achei o story de agora (carimbo <= {limite_min:.0f} min) em {max_avancos} stories")


def _item_destaque(nos: list, nome: str) -> No | None:
    for n in achar_todos(nos, texto=[nome], contem=False):
        return _clicavel_de(nos, n)
    for n in achar_todos(nos, id=IDS_PALPITE["destaque_item"]):
        if normalizar(n.rotulo) == normalizar(nome):
            return _clicavel_de(nos, n)
    return None


def adicionar_ao_destaque(disp, nome: str, conta: str | None = None, limite_min: float = LIMITE_MIN_AGORA,
                          tempos: dict | None = None) -> dict:
    """Foto do perfil -> próprio story -> o DE AGORA (carimbo) e do dono certo (reel_viewer_title) ->
    toolbar_highlights_button ("Highlight") -> destaque pelo nome (ou cria) -> confirma."""
    t = _tempos(tempos)
    nome = str(nome or "").strip()
    if not nome:
        raise DadosInvalidos("nome do destaque vazio")
    _passo(disp, f"destaque '{nome}'")
    nos = ir_para_perfil(disp, t)
    disp.tocar(_achar(disp, nos, id=SEL.IDS["avatar_perfil"]), "foto do perfil (abre o meu story)")
    ts = avancar_ate_story_de_agora(disp, conta, limite_min, tempos=t)
    disp.tocar(_esperar(disp, t["elemento"], id=SEL.IDS["story_destaque"]), "Highlight (toolbar_highlights_button)")
    res = {"destaque": nome, "carimbo": ts.texto, "criado": False, "confirmado": False}
    alvo = _condicao(disp, lambda ns: _item_destaque(ns, nome), f"destaque '{nome}' na lista", t["elemento"],
                     simulado=_sintetico(disp, {"texto": nome}), levantar=False)
    if alvo is not None:
        disp.tocar(alvo, f"destaque '{nome}'")
    else:
        nos = disp.ultimos_nos
        novo = achar(nos, id=IDS_PALPITE["destaque_novo"]) or achar(nos, rotulo=TEXTOS_EXTRA["destaque_novo"], contem=False)
        if novo is None:
            raise sd.ElementoNaoApareceu(f"o destaque '{nome}' não existe e não achei o botão de criar um novo")
        disp.tocar(_clicavel_de(nos, novo), "novo destaque")
        campo = _condicao(disp, lambda ns: _campo_texto(ns, [], ["Highlights", "Destaques", "Title", "Nome"]),
                          "campo do nome do destaque", t["elemento"])
        disp.digitar(nome, campo=campo)
        ok, _ = _esperar_qualquer(disp, [{"rotulo": TEXTOS_EXTRA["destaque_confirmar"], "contem": False},
                                         {"id": SEL.IDS["concluir"]}], t["elemento"])
        disp.tocar(ok, "confirmar o novo destaque")
        res["criado"] = True
    confirmou = _condicao(disp, lambda ns: bool(achar(ns, rotulo=SEL.TEXTOS["destaque_ok"]) or not _item_destaque(ns, nome)),
                          "confirmação do destaque", t["confirmacao"], simulado=True, levantar=False)
    res["confirmado"] = bool(confirmou)
    if not confirmou:
        disp.log.warning("não vi a confirmação do destaque '%s' ('Added to'/'Adicionado'); confira na tela", nome)
    return res


# ===========================================================================
# A prova de que saiu: API do Instagram (get_json injetado; nunca faz rede aqui)
# ===========================================================================
def story_mais_novo(resposta, desde) -> dict | None:
    """Entre os stories da resposta, o mais novo com timestamp >= desde (ou None)."""
    dados = resposta.get("data") if isinstance(resposta, dict) else resposta
    if not isinstance(dados, list):
        return None
    desde_dt = _dt(desde)
    melhor = None
    for s in dados:
        if not isinstance(s, dict):
            continue
        ts = _dt(s.get("timestamp"))
        if ts is None or (desde_dt and ts < desde_dt):
            continue
        if melhor is None or ts > melhor[0]:
            melhor = (ts, s)
    if melhor is None:
        return None
    s = dict(melhor[1])
    s["timestamp_dt"] = melhor[0].isoformat(timespec="seconds")
    return s


def conferir_pela_api(get_json: Callable, ig_user_id: str, desde, tentativas: int = 3, espera_s: float = 20,
                      dormir: Callable | None = None, log=None) -> dict | None:
    """GET /v21.0/<ig-user-id>/stories?fields=id,media_type,permalink,timestamp pelo get_json(url, params)
    injetado. Devolve o story mais novo com timestamp >= desde, ou None depois de `tentativas` (quem chama
    marca "a conferir" e NUNCA repete o toque). Nada aqui faz rede nem sabe de token."""
    if not callable(get_json):
        raise DadosInvalidos("conferir_pela_api precisa do get_json(url, params) injetado (no PC: publicador_meta.api)")
    ig_user_id = str(ig_user_id or "").strip()
    if not re.fullmatch(r"[0-9]+", ig_user_id):
        raise DadosInvalidos(f"ig_user_id inválido: {ig_user_id!r} (vem de meta_tokens_meta.json -> contas['IG_<handle>'].id)")
    log = log or logging.getLogger("hp.story_fluxos")
    dormir = dormir or time.sleep
    url = API_STORIES.format(ig_user_id=ig_user_id)
    params = {"fields": CAMPOS_API}
    for i in range(1, max(1, int(tentativas)) + 1):
        try:
            resp = get_json(url, params)
        except Exception as e:  # a API caiu: tenta de novo, nunca repete o toque
            log.warning("conferência pela API falhou (%d/%d): %s", i, tentativas, sd.mascarar(str(e))[:200])
            resp = None
        novo = story_mais_novo(resp, desde) if resp is not None else None
        if novo:
            novo["tentativa"] = i
            log.info("story confirmado pela API: %s (%s)", novo.get("permalink") or novo.get("id"), novo.get("timestamp"))
            return novo
        if i < tentativas:
            dormir(float(espera_s))
    log.warning("a API não mostrou story novo desde %s em %d tentativas: fica 'a conferir'", desde, tentativas)
    return None


# ===========================================================================
# Fila v2: um item e o pedido inteiro
# ===========================================================================
def chave_do_story(pedido: dict, story: dict, indice: int | None = None) -> str:
    """compartilhar_post -> o post_id (a mesma chave da rodada 1: não repete o que ela já postou);
    os outros -> post_id#tipo@quando."""
    pid = str(pedido.get("post_id") or "")
    if story.get("tipo") == "compartilhar_post":
        return pid
    quando = re.sub(r"[^0-9]", "", str(story.get("quando") or ""))[:12] or f"i{indice if indice is not None else 0}"
    return f"{pid}#{story.get('tipo')}@{quando}"


def figurinhas_do_story(story: dict, pedido: dict | None = None) -> list:
    f = story.get("figurinha")
    if not f or not isinstance(f, dict) or normalizar(f.get("tipo")) in ("", "null"):
        return []
    f = dict(f)
    tipo = normalizar(f.get("tipo"))
    if tipo in ("enquete", "quiz", "pergunta"):
        f["pergunta"] = story.get("pergunta_publico") or story.get("texto")
    if tipo == "link":
        f["url"] = f.get("url") or story.get("link") or (pedido or {}).get("link")
        f["rotulo"] = f.get("rotulo") or fila.ROTULO_LINK_PADRAO
    return [f]


def rodar_item_v2(disp, item_v2: dict, story: dict, contexto: Contexto, indice: int | None = None) -> dict:
    """Um story da fila v2 pelo tipo. Antes de encostar no aparelho confere: parada, já feito, 3 falhas, intervalo."""
    chave = chave_do_story(item_v2, story, indice)
    conta = limpar_handle(story.get("conta") or item_v2.get("conta"))
    tipo = normalizar(story.get("tipo"))
    rel = contexto.relogio
    res = {"story": chave, "chave": chave, "conta": f"@{conta}", "tipo": tipo, "ok": False, "codigo": ERRO, "estado": None}
    contexto.saida(f"Story {chave} ({tipo}) em @{conta}")
    est = contexto.estado
    if contexto.parada().exists():
        return {**res, "codigo": AVISO_META, "erro": f"parado por aviso da Meta ({contexto.parada()}); só o Antônio apaga"}
    ja = est.ja_postado(chave)
    if ja:
        return {**res, "codigo": BLOQUEADO, "estado": ja, "erro": f"story {chave} já saiu ({ja}): 1 story por post, nunca repete"}
    if est.fora_da_fila(chave, contexto.max_tentativas):
        return {**res, "codigo": BLOQUEADO, "erro": f"{est.tentativas(chave)} falhas em {chave}: fora da fila automática; "
                                                   "o Antônio olha o log e zera 'tentativas' no estado"}
    falta = est.falta_intervalo(contexto.agora(), contexto.intervalo_min_seg)
    if falta > 0:
        return {**res, "codigo": BLOQUEADO, "erro": f"intervalo mínimo de {contexto.intervalo_min_seg / 60:.0f} min entre "
                                                   f"stories: faltam {falta:.0f}s", "faltam_s": falta}
    if not conta:
        return {**res, "erro": "o story não diz a conta (@)"}
    contexto.orcamento = Orcamento(contexto.orcamento_seg, rel)
    disp.orcamento = contexto.orcamento
    registrar = contexto.registrador(chave, conta=conta, link=story.get("link") or item_v2.get("link"), tipo=tipo)
    inicio = contexto.agora()
    try:
        disp.tela_acesa_e_destravada()
        trocar_conta(disp, conta, contexto.tempos)
        destaque = story.get("destaque") or item_v2.get("destaque")
        if tipo == "compartilhar_post":
            r = compartilhar_post_no_story(disp, story.get("link") or item_v2.get("link"), conta,
                                           story.get("texto") or item_v2.get("titulo"), registrar, chave, destaque, contexto.tempos)
        elif tipo in TIPOS_COM_ARTE:
            figs = figurinhas_do_story(story, item_v2)
            if tipo == "contagem" and (not figs or figs[0]["tipo"] != "contagem"):
                raise DadosInvalidos("story de contagem sem figurinha de contagem (com 'data')")
            r = story_da_arte(disp, story.get("arte"), figs, destaque, story.get("zonas"), registrar, chave, conta,
                              contexto.tempos, contexto.limite_pergunta)
        else:
            raise DadosInvalidos(f"tipo de story desconhecido: '{tipo}' (use {', '.join(fila.TIPOS)})")
        res.update({k: v for k, v in r.items() if k not in ("conta",)})
        estado = r["estado"]
        ig_id = contexto.id_da_conta(conta)
        if estado == "tocado" and contexto.get_json and ig_id:
            prova = conferir_pela_api(contexto.get_json, ig_id, inicio, contexto.tentativas_api, contexto.espera_api_s,
                                      dormir=rel.sleep, log=contexto.log)
            if prova:
                estado = "publicado"
                res["api"] = prova
                registrar(chave, "publicado", permalink=prova.get("permalink"), story_id=prova.get("id"))
            else:
                estado = "a_conferir"
                registrar(chave, "a_conferir", motivo="a API não mostrou o story novo")
        res["estado"] = estado
        res["ok"] = estado in ("tocado", "publicado")
        res["codigo"] = OK if res["ok"] else ERRO
        if estado == "a_conferir":
            res["a_conferir"] = "tocou em 'Seu story' mas não confirmou; confira no Instagram (não repito)"
    except sd.AvisoMetaDetectado as e:
        res.update({"erro": str(e), "codigo": AVISO_META, "aviso_meta": True, "estado": est.ja_postado(chave)})
        contexto.saida(f"PARADO: aviso na tela ('{e.frase}'); {contexto.parada()} gravado; só o Antônio apaga")
    except (sd.CelularBloqueado, sd.DispositivoAmbiguo, sd.TecladoAcentoIndisponivel) as e:
        res.update({"erro": str(e), "codigo": PRECISA_ANTONIO, "precisa_antonio": True})
    except (PostJaFeito, ForaDaFila, IntervaloCurto) as e:
        res.update({"erro": str(e), "codigo": e.codigo, "estado": est.ja_postado(chave)})
    except (FluxoErro, sd.DispositivoErro, fila.FilaInvalida, LOTE.LoteErro) as e:
        n = est.registrar_falha(chave, e, disp.passo, agora=contexto.agora())
        res.update({"erro": f"{type(e).__name__}: {e}", "codigo": getattr(e, "codigo", ERRO), "tentativas": n,
                    "estado": est.ja_postado(chave)})
        if n >= contexto.max_tentativas and not est.ja_postado(chave):
            res["fora_da_fila"] = True
    except Exception as e:  # inesperado: registra e segue (o aparelho é desligado por quem chamou)
        contexto.log.exception("erro inesperado em %s", chave)
        n = est.registrar_falha(chave, e, disp.passo, agora=contexto.agora())
        res.update({"erro": f"inesperado: {e!r}", "codigo": ERRO, "tentativas": n, "estado": est.ja_postado(chave)})
    finally:
        disp.orcamento = None
    return res


def desligar_emulador_padrao(disp) -> None:
    """adb emu kill (o PC pode trocar pelo desligar_emulador.ps1 passando desligar_emulador=)."""
    disp.log.info("desligando o emulador %s", disp.serial)
    disp.executar("emu", "kill")


def rodar_pedido_v2(pedido, contexto: Contexto, abrir_aparelho: Callable, desligar_emulador: Callable | None = None,
                    esperar_intervalo: bool = False, trava=None) -> dict:
    """Todos os stories de um pedido v2: pesado.lock primeiro (ocupado -> código 2, SEM ligar o aparelho),
    liga/abre o aparelho só depois da trava, roda item a item, e no fim desliga o EMULADOR sempre (mesmo em
    erro); celular real (serial que não é emulator-NNNN) NUNCA é desligado."""
    dados = fila.ler_pedido(pedido) if not isinstance(pedido, dict) else fila.migrar_v1(pedido)
    resultados = []
    desligar = desligar_emulador or desligar_emulador_padrao
    if trava is None:
        trava = TravaPesada("story_fluxos", ignorar_horario=True, agora=contexto.agora().replace(tzinfo=None))
    disp = None
    try:
        with trava:
            disp = abrir_aparelho()
            try:
                for i, story in enumerate(dados["stories"]):
                    falta = contexto.estado.falta_intervalo(contexto.agora(), contexto.intervalo_min_seg)
                    if falta > 0 and esperar_intervalo:
                        contexto.log.info("esperando %.0fs de intervalo entre stories", falta)
                        contexto.relogio.sleep(falta)
                    res = rodar_item_v2(disp, dados, story, contexto, i)
                    resultados.append(res)
                    contexto.saida(("OK " if res["ok"] else "NÃO SAIU ") + f"{res['chave']} {res['conta']}"
                                   + (f" - {res['erro']}" if res.get("erro") else ""))
                    if res.get("aviso_meta") or res.get("precisa_antonio"):
                        break
            finally:
                if disp is not None:
                    if eh_emulador(disp.serial):
                        try:
                            desligar(disp)
                        except Exception as e:  # desligar nunca esconde o erro de verdade
                            contexto.log.error("não consegui desligar o emulador: %s", e)
                    else:
                        contexto.log.info("celular real (%s): não desligo", disp.serial)
    except TravaOcupada as e:
        return {"ok": False, "codigo": BLOQUEADO, "resultados": [],
                "mensagem": f"outro trabalho pesado está rodando ({e}); não liguei o aparelho; tento na próxima rodada"}
    if any(r.get("aviso_meta") for r in resultados):
        return {"ok": False, "codigo": AVISO_META, "mensagem": "parado por aviso da Meta", "resultados": resultados}
    if any(r.get("precisa_antonio") for r in resultados):
        return {"ok": False, "codigo": PRECISA_ANTONIO, "mensagem": "o Antônio precisa agir no aparelho", "resultados": resultados}
    tudo_ok = bool(resultados) and all(r.get("ok") for r in resultados)
    codigo = OK if tudo_ok else (BLOQUEADO if resultados and all(r.get("codigo") == BLOQUEADO for r in resultados) else ERRO)
    return {"ok": tudo_ok, "codigo": codigo, "mensagem": "ok" if tudo_ok else "houve story que não saiu (veja o log)",
            "resultados": resultados}


# ===========================================================================
# --simular: o aparelho de roteiro (imprime cada comando adb e cada passo; não executa nada)
# ===========================================================================
class DispositivoRoteiro(sd.Dispositivo):
    """Dispositivo com runner_roteiro: cada comando vira uma linha "[simular] adb ..."; as esperas são
    anunciadas e consideradas satisfeitas; nada chama o adb de verdade."""
    simular = True

    def __init__(self, saida: Callable = print, tela: tuple = (1080, 2400), serial: str = "emulator-5554", **kw):
        kw.setdefault("relogio", _RelogioRoteiro())
        super().__init__(sd.runner_roteiro(saida, tela, serial), serial, **kw)
        self.saida = saida

    def empurrar_arte(self, arquivo_local, nome_ascii: str | None = None, espera_s: float = 1.0) -> dict:
        nome = nome_ascii or sd.nome_ascii_de(re.split(r"[\\/]", str(arquivo_local))[-1])
        remoto = f"{self.pasta_fotos}/{nome}"
        self.shell("mkdir", "-p", self.pasta_fotos)
        self.executar("push", str(arquivo_local), remoto)
        self.shell(*self.planos_mediastore(remoto)[0][1])
        return {"remoto": remoto, "nome": nome, "plano": "principal (simulado)"}


class _RelogioRoteiro:
    def __init__(self):
        self.t = 0.0

    def monotonic(self) -> float:
        return self.t

    def sleep(self, s: float) -> None:
        self.t += max(0.0, float(s))

    def agora(self) -> datetime:
        return datetime.now(FUSO)


def abrir_aparelho_real(serial: str | None = None, preferencia: str | None = None, adb_exe: str | None = None,
                        runner: Callable | None = None, env=None, log=None) -> sd.Dispositivo:
    """Escolhe o aparelho (--serial > HP_ANDROID_SERIAL > o único ligado) e espera o boot. Não liga o emulador
    (isso é o ligar_emulador.ps1 do PC, chamado por quem orquestra)."""
    runner = runner or sd.runner_real(adb_exe or sd.achar_adb())
    serial = sd.escolher_serial(runner, serial, env=env, preferencia=preferencia)
    disp = sd.Dispositivo(runner, serial, relogio=RelogioReal(), log=log, gravar_parada=sd.gravar_parada_padrao())
    disp.esperar_boot()
    return disp


def _argumentos(argv) -> tuple:
    ap = argparse.ArgumentParser(prog="python scripts\\story_fluxos.py",
                                 description="Fluxos do story no celular por ADB (emulador ou celular real).")
    comum = argparse.ArgumentParser(add_help=False)
    comum.add_argument("--simular", action="store_true", help="imprime o roteiro completo; não chama o adb")
    comum.add_argument("--serial")
    comum.add_argument("--emulador", action="store_true")
    comum.add_argument("--celular", action="store_true")
    comum.add_argument("--adb", help="caminho do adb.exe (padrão: HP_ADB ou o do PC)")
    comum.add_argument("--estado", help="JSON de estado (padrão: H:\\HypadoLocal\\emulador\\story_post_estado.json)")
    comum.add_argument("--tela", default="1080x2400", help="só no --simular: LARGURAxALTURA do aparelho de roteiro")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("trocar-conta", parents=[comum], help="perfil -> lista de contas -> @ -> confere")
    p.add_argument("handle")
    p = sub.add_parser("arte", parents=[comum], help="story a partir de uma arte com figurinhas")
    p.add_argument("arte")
    p.add_argument("--conta", required=True)
    p.add_argument("--link", help="figurinha de link (URL)")
    p.add_argument("--rotulo", default=fila.ROTULO_LINK_PADRAO)
    p.add_argument("--enquete", help="pergunta da enquete (<= 25 depois de encurtar)")
    p.add_argument("--opcao", action="append", default=[])
    p.add_argument("--contagem", help="título da contagem regressiva")
    p.add_argument("--data", help="data final da contagem AAAA-MM-DD")
    p.add_argument("--zonas", help="<arte>_zonas.json (padrão: ao lado da arte)")
    p.add_argument("--destaque")
    p.add_argument("--chave", help="chave do estado (padrão: nome da arte)")
    p = sub.add_parser("compartilhar", parents=[comum], help="compartilha um post no story")
    p.add_argument("link")
    p.add_argument("--conta", required=True)
    p.add_argument("--titulo")
    p.add_argument("--destaque")
    p = sub.add_parser("destaque", parents=[comum], help="põe o story de agora num destaque")
    p.add_argument("nome")
    p.add_argument("--conta", required=True)
    p = sub.add_parser("pedido", parents=[comum], help="roda todos os stories de um pedido v2 (ou v1 migrado)")
    p.add_argument("arquivo")
    p.add_argument("--esperar-intervalo", action="store_true")
    return ap.parse_args(argv), ap


def main(argv=None, saida: Callable = print, runner: Callable | None = None, env=None, relogio=None) -> int:
    args, ap = _argumentos(argv)
    if not args.cmd:
        ap.print_help()
        return ERRO
    log = logging.getLogger("hp.story_fluxos")
    try:
        if args.simular:
            saida("== SIMULAÇÃO: nada é enviado ao aparelho ==")
            tela = fila._tela(args.tela)
            estado = Estado(dados={}, gravar=False)
            disp = DispositivoRoteiro(saida, tela, args.serial or "emulator-5554", log=log)

            def abrir():
                return disp
        else:
            estado = Estado(Path(args.estado) if args.estado else None)
            pref = "emulador" if args.emulador else ("celular" if args.celular else None)

            def abrir():
                return abrir_aparelho_real(args.serial, pref, args.adb, runner, env, log)
            disp = None
        ctx = Contexto(estado=estado, log=log, saida=saida, relogio=relogio or RelogioReal())
        if args.cmd == "pedido":
            r = rodar_pedido_v2(Path(args.arquivo), ctx, abrir, esperar_intervalo=args.esperar_intervalo,
                                trava=nullcontext() if args.simular else None)   # --simular não toca no pesado.lock
            saida(f"{'OK' if r['ok'] else 'NÃO SAIU'}: {r['mensagem']}")
            return int(r["codigo"])
        if disp is None:
            disp = abrir()
        if args.cmd == "trocar-conta":
            saida(f"conta ativa: @{trocar_conta(disp, args.handle)}")
            return OK
        if args.cmd == "destaque":
            trocar_conta(disp, args.conta)
            r = adicionar_ao_destaque(disp, args.nome, args.conta)
            saida(f"destaque: {r}")
            return OK
        if args.cmd == "compartilhar":
            chave = args.link
            registrar = ctx.registrador(chave, conta=limpar_handle(args.conta), link=args.link)
            trocar_conta(disp, args.conta)
            r = compartilhar_post_no_story(disp, args.link, args.conta, args.titulo, registrar, chave, args.destaque)
        else:
            figs = []
            if args.link:
                figs.append({"tipo": "link", "url": args.link, "rotulo": args.rotulo})
            if args.enquete:
                figs.append({"tipo": "enquete", "pergunta": args.enquete, "opcoes": args.opcao})
            if args.contagem:
                figs.append({"tipo": "contagem", "rotulo": args.contagem, "data": args.data})
            chave = args.chave or Path(args.arte).stem
            registrar = ctx.registrador(chave, conta=limpar_handle(args.conta), link=args.link)
            trocar_conta(disp, args.conta)
            r = story_da_arte(disp, args.arte, figs, args.destaque, args.zonas, registrar, chave, args.conta)
        saida(f"estado do story {r['chave']}: {r['estado']}")
        return OK if r["estado"] in ("tocado", "publicado") else ERRO
    except TravaOcupada as e:
        saida(f"BLOQUEADO: {e}")
        return BLOQUEADO
    except (FluxoErro, sd.DispositivoErro, fila.FilaInvalida, LOTE.LoteErro) as e:
        saida(f"{type(e).__name__}: {e}")
        return int(getattr(e, "codigo", ERRO))


if __name__ == "__main__":
    raise SystemExit(main())
