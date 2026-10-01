# -*- coding: utf-8 -*-
"""story_fila_v2.py — o pedido da fila_story ganha a lista `stories[]` (esquema v2, tarefa E3).

O que faz: valida, migra e monta o JSON que o story_post consome em
H:\\HypadoLocal\\emulador\\fila_story\\<post_id>.json. Os campos de hoje (§4.7: post_id, conta,
canal, link, publicado_em, titulo, destaque, criado_em) continuam valendo; a v2 acrescenta
`stories[]`, um item por story a fazer:

  {"quando": "2026-10-01 09:40", "tipo": "chamada_post|mais_sobre|interacao|enquete|contagem|compartilhar_post",
   "arte": "H:\\...\\story_chamada.jpg", "zonas": "H:\\...\\story_chamada_zonas.json", "texto": "...",
   "figurinha": {"tipo": "link|enquete|quiz|contagem|pergunta|null", "url": "https://...", "rotulo": "Ver post",
                 "opcoes": ["...", "..."]},
   "pergunta_publico": "O que você faz?", "destaque": "Enquetes"}

Funções:
  validar_v2(dados, limite_pergunta=25, limite_opcao=25) -> cópia normalizada ou FilaInvalida (motivos em
      português, um por linha, com o índice do story: "stories[1]: ...")
  migrar_v1(dados)            -> pedido real da §4.7 (fixture fila_story_pedido_real.json) vira v2 com UM story
                                 compartilhar_post em `publicado_em` (sem fuso = Brasília; ISO com fuso também vale)
  de_lote_estaticos(lote, limite_pergunta=25, ...) -> stories[] (hora, arquivo, tema) + interativo do lote real
      (lotes\\AAAA-MM-DD_estaticos.json, §4.5) em itens v2: tema "vídeo novo: X" -> compartilhar_post;
      "comenta aí" -> interacao; "contagem N dias" -> contagem (data = dia do lote + N); interativo -> enquete com
      pergunta_publico de story_post_lote.pergunta_da_figurinha. Item incompleto é RECUSADO com o motivo
      (lista "recusados"), nunca inventado.
  pedido_de_lote(lote, agora=...) -> o pedido v2 inteiro a partir do lote (post_id "<canal>_<data>_estaticos")
  ler_zonas(arte, tela, area=None) -> lê <arte>_zonas.json do story_artes (D) e converte para a tela REAL do
      aparelho: fração × tamanho da tela (wm size), ou × `area` (bounds de onde a arte aparece no dump)
  gravar_pedido / ler_pedido   -> JSON atômico (hpbase.escrever_json), validando; ler_pedido migra v1 sozinho

Uso (CLI, código 0 ok / 1 erro):
  python scripts\\story_fila_v2.py validar fila_story\\<post_id>.json
  python scripts\\story_fila_v2.py migrar  fila_story\\<post_id>.json [--saida ARQ]
  python scripts\\story_fila_v2.py de-lote lotes\\2026-10-01_estaticos.json [--limite 25] [--saida ARQ]
  python scripts\\story_fila_v2.py zonas   <arte.jpg> --tela 1080x2400

Regras: só biblioteca padrão + hpbase; nada de rede, adb nem relógio real (quem chama passa `agora=`);
caminhos do PC ficam como texto (não são abertos aqui, só o _zonas.json); em dúvida sobre um campo,
recusa e explica em português, em vez de adivinhar.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

AQUI = Path(__file__).resolve().parent


def caminho_hp_studio() -> Path | None:
    """Acha a pasta que contém o pacote hpbase e põe no sys.path (mesmo truque do story_artes_base)."""
    cands: list[Path] = []
    env = os.environ.get("HP_APP")
    if env:
        cands += [Path(env), Path(env) / "hp_studio_nuvem", Path(env) / "hp_studio"]
    cands += [AQUI.parent / "app" / "hp_studio_nuvem",
              AQUI.parent / "06 Projeto" / "app" / "hp_studio_nuvem",
              AQUI.parent / "app" / "hp_studio",
              AQUI.parent / "06 Projeto" / "app" / "hp_studio"]
    for c in cands:
        if (c / "hpbase" / "__init__.py").exists():
            if str(c) not in sys.path:
                sys.path.insert(0, str(c))
            return c
    return None


caminho_hp_studio()
if str(AQUI) not in sys.path:
    sys.path.insert(0, str(AQUI))

from hpbase import FUSO, escrever_json, ler_json  # noqa: E402
from hpbase import marca  # noqa: E402
import story_post_lote as LOTE  # noqa: E402

VERSAO = 2
TIPOS = ("chamada_post", "mais_sobre", "interacao", "enquete", "contagem", "compartilhar_post")
FIGURINHAS = ("link", "enquete", "quiz", "contagem", "pergunta")
TIPOS_SEM_ARTE = ("compartilhar_post",)
LIMITE_PERGUNTA = LOTE.LIMITE_PERGUNTA      # 25 (A4)
LIMITE_OPCAO = LOTE.LIMITE_OPCAO            # 25
LIMITE_ROTULO = 30                          # rótulo da figurinha de link ("Ver post"); palpite, ver E1.md
MIN_OPCOES, MAX_OPCOES = LOTE.MIN_OPCOES, LOTE.MAX_OPCOES
ROTULO_LINK_PADRAO = "Ver post"
PREFIXO_VIDEO_NOVO = LOTE.PREFIXO_VIDEO_NOVO     # "vídeo novo:"
SUFIXO_ZONAS = "_zonas.json"
TELA_ARTE = tuple(marca.TAMANHOS["story"])       # (1080, 1920)
CAMPOS_V1 = ("post_id", "conta", "canal", "link", "publicado_em", "titulo", "destaque", "criado_em")
CHAVES_STORY = ("quando", "tipo", "arte", "zonas", "texto", "figurinha", "pergunta_publico", "destaque")
CHAVES_FIGURINHA = ("tipo", "url", "rotulo", "opcoes")

_RX_HORA = re.compile(r"^(\d{1,2}):(\d{2})$")
_RX_DIA = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_RX_CONTAGEM = re.compile(r"contagem\s+(\d+)\s+dias?")
_RX_LINK = re.compile(r"^https?://\S+$", re.I)
_RX_TELA = re.compile(r"^\s*(\d+)\s*[xX]\s*(\d+)\s*$")


class FilaInvalida(ValueError):
    """O pedido (ou o lote) não serve: a mensagem lista os motivos em português."""

    def __init__(self, motivos):
        if isinstance(motivos, str):
            motivos = [motivos]
        self.motivos = list(motivos)
        super().__init__("\n".join(self.motivos))


# ===========================================================================
# Datas (hora de Brasília; ISO com fuso também vale)
# ===========================================================================
def normalizar_quando(valor) -> datetime:
    """'2026-09-30 17:07' (Brasília, sem fuso) ou ISO com fuso -> datetime com fuso de Brasília."""
    if isinstance(valor, datetime):
        dt = valor
    else:
        txt = str(valor or "").strip()
        if not txt:
            raise ValueError("data vazia")
        try:
            dt = datetime.fromisoformat(txt.replace("Z", "+00:00"))
        except ValueError:
            try:
                dt = datetime.strptime(txt, "%Y-%m-%d %H:%M")
            except ValueError:
                raise ValueError(f"data '{txt}' fora do formato AAAA-MM-DD HH:MM (ou ISO com fuso)") from None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=FUSO)
    return dt.astimezone(FUSO)


def formatar_quando(dt: datetime) -> str:
    return normalizar_quando(dt).strftime("%Y-%m-%d %H:%M")


def _dia(valor) -> str:
    txt = str(valor or "").strip()
    m = _RX_DIA.match(txt)
    if not m:
        raise ValueError(f"dia '{txt}' fora do formato AAAA-MM-DD")
    datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))  # valida
    return txt


def _hora(valor) -> str:
    txt = str(valor or "").strip()
    m = _RX_HORA.match(txt)
    if not m or not (0 <= int(m.group(1)) <= 23 and 0 <= int(m.group(2)) <= 59):
        raise ValueError(f"hora '{txt}' fora do formato HH:MM")
    return f"{int(m.group(1)):02d}:{m.group(2)}"


# ===========================================================================
# Validação do esquema v2
# ===========================================================================
def e_v2(dados) -> bool:
    return isinstance(dados, dict) and isinstance(dados.get("stories"), list)


def _texto(v) -> str:
    return str(v).strip() if isinstance(v, str) else ""


def _validar_figurinha(f, onde: str, erros: list, limite_pergunta: int, limite_opcao: int,
                       pergunta_publico: str, link_pai: str | None) -> dict | None:
    if f is None:
        return None
    if not isinstance(f, dict):
        erros.append(f"{onde}: 'figurinha' precisa ser um objeto ou null")
        return None
    out = {k: f.get(k) for k in CHAVES_FIGURINHA}
    for k, v in f.items():
        if k not in out:
            out[k] = v
    tipo = _texto(f.get("tipo")).lower()
    if not tipo or tipo == "null":
        return None
    if tipo not in FIGURINHAS:
        erros.append(f"{onde}: figurinha '{tipo}' não existe; use uma destas: {', '.join(FIGURINHAS)} ou null")
        return None
    out["tipo"] = tipo
    if tipo == "link":
        url = _texto(f.get("url")) or (link_pai or "")
        if not _RX_LINK.match(url):
            erros.append(f"{onde}: a figurinha de link precisa de 'url' (https://...)")
        out["url"] = url or None
        rot = _texto(f.get("rotulo")) or ROTULO_LINK_PADRAO
        if len(rot) > LIMITE_ROTULO:
            erros.append(f"{onde}: o rótulo do link tem {len(rot)} caracteres (máximo {LIMITE_ROTULO}): '{rot}'")
        out["rotulo"] = rot
    if tipo in ("enquete", "quiz"):
        ops = f.get("opcoes")
        if not isinstance(ops, list) or not (MIN_OPCOES <= len(ops) <= MAX_OPCOES):
            erros.append(f"{onde}: a figurinha de {tipo} precisa de {MIN_OPCOES} a {MAX_OPCOES} opções em 'opcoes'")
        else:
            limpas = []
            for i, o in enumerate(ops, 1):
                t = LOTE.limpar(o)
                if not t:
                    erros.append(f"{onde}: opção {i} da {tipo} está vazia")
                elif len(t) > limite_opcao:
                    erros.append(f"{onde}: opção {i} da {tipo} tem {len(t)} caracteres (máximo {limite_opcao}): '{t}'")
                limpas.append(t)
            out["opcoes"] = limpas
    if tipo in ("enquete", "quiz", "pergunta"):
        if not pergunta_publico:
            erros.append(f"{onde}: figurinha de {tipo} precisa de 'pergunta_publico' (o texto que vai na figurinha)")
        elif len(pergunta_publico) > limite_pergunta:
            erros.append(f"{onde}: 'pergunta_publico' tem {len(pergunta_publico)} caracteres (máximo "
                         f"{limite_pergunta}): '{pergunta_publico}'. Encurte (ver story_post_lote.py)")
    if tipo == "contagem":
        data = f.get("data")
        try:
            out["data"] = _dia(data)
        except ValueError as e:
            erros.append(f"{onde}: a figurinha de contagem precisa de 'data' (AAAA-MM-DD): {e}")
        rot = _texto(f.get("rotulo"))
        if rot and len(rot) > LIMITE_ROTULO:
            erros.append(f"{onde}: o título da contagem tem {len(rot)} caracteres (máximo {LIMITE_ROTULO})")
        out["rotulo"] = rot or None
    return out


def _validar_story(s, i: int, erros: list, limite_pergunta: int, limite_opcao: int,
                   link_pai: str | None) -> dict:
    onde = f"stories[{i}]"
    if not isinstance(s, dict):
        erros.append(f"{onde}: precisa ser um objeto")
        return {}
    out = {k: s.get(k) for k in CHAVES_STORY}
    for k, v in s.items():
        if k not in out:
            out[k] = v
    try:
        out["quando"] = formatar_quando(normalizar_quando(s.get("quando")))
    except ValueError as e:
        erros.append(f"{onde}: 'quando' inválido ({e})")
    tipo = _texto(s.get("tipo")).lower()
    if tipo not in TIPOS:
        erros.append(f"{onde}: tipo '{tipo}' não existe; use um destes: {', '.join(TIPOS)}")
    out["tipo"] = tipo
    arte = _texto(s.get("arte"))
    out["arte"] = arte or None
    if tipo and tipo not in TIPOS_SEM_ARTE and not arte:
        erros.append(f"{onde}: story do tipo '{tipo}' precisa de 'arte' (caminho do JPG do story_artes)")
    zonas = _texto(s.get("zonas"))
    out["zonas"] = zonas or (caminho_zonas(arte) if arte else None)
    out["texto"] = _texto(s.get("texto")) or None
    pergunta = LOTE.limpar(s.get("pergunta_publico"))
    out["pergunta_publico"] = pergunta or None
    dest = s.get("destaque")
    if dest is not None and not isinstance(dest, str):
        erros.append(f"{onde}: 'destaque' precisa ser texto (nome do destaque) ou null")
    out["destaque"] = _texto(dest) or None
    link = _texto(s.get("link")) or link_pai
    if tipo == "compartilhar_post":
        if not link or not _RX_LINK.match(link):
            erros.append(f"{onde} (compartilhar_post): falta o link do post (campo 'link' do story ou do pedido)")
        out["link"] = link or None
    out["figurinha"] = _validar_figurinha(s.get("figurinha"), onde, erros, limite_pergunta, limite_opcao,
                                          pergunta, link)
    ftipo = (out["figurinha"] or {}).get("tipo")
    if tipo == "enquete" and ftipo not in ("enquete", "quiz"):
        erros.append(f"{onde}: story do tipo 'enquete' precisa de figurinha enquete (ou quiz)")
    if tipo == "contagem" and ftipo != "contagem":
        erros.append(f"{onde}: story do tipo 'contagem' precisa de figurinha contagem (com 'data')")
    if tipo == "compartilhar_post" and ftipo not in (None, "link"):
        erros.append(f"{onde}: compartilhar_post não leva figurinha '{ftipo}' (só link ou null)")
    if tipo == "interacao" and ftipo not in (None, "enquete", "quiz", "pergunta"):
        erros.append(f"{onde}: story de interação leva figurinha enquete, quiz, pergunta ou null (veio '{ftipo}')")
    return out


def validar_v2(dados, limite_pergunta: int = LIMITE_PERGUNTA, limite_opcao: int = LIMITE_OPCAO) -> dict:
    """Devolve uma cópia normalizada do pedido v2 ou levanta FilaInvalida com TODOS os motivos."""
    erros: list[str] = []
    if not isinstance(dados, dict):
        raise FilaInvalida("o pedido precisa ser um objeto JSON")
    out = copy.deepcopy(dados)
    for campo in ("post_id", "conta", "canal", "titulo"):
        if not _texto(dados.get(campo)):
            erros.append(f"falta o campo '{campo}'")
    out["conta"] = LOTE.normalizar(dados.get("conta")).lstrip("@") if _texto(dados.get("conta")) else None
    link = _texto(dados.get("link")) or None
    if link and not _RX_LINK.match(link):
        erros.append(f"'link' precisa começar com https:// (veio '{link}')")
    out["link"] = link
    for campo in ("publicado_em", "criado_em"):
        v = dados.get(campo)
        if v not in (None, ""):
            try:
                normalizar_quando(v)
            except ValueError as e:
                erros.append(f"'{campo}' inválido ({e})")
    dest = dados.get("destaque")
    if dest is not None and not isinstance(dest, str):
        erros.append("'destaque' precisa ser texto (nome do destaque) ou null")
    stories = dados.get("stories")
    if not isinstance(stories, list):
        erros.append("falta a lista 'stories' (esquema v2); para o formato antigo use migrar_v1")
        stories = []
    elif not stories:
        erros.append("'stories' está vazio: nada para fazer")
    out["stories"] = [_validar_story(s, i, erros, int(limite_pergunta), int(limite_opcao), link)
                      for i, s in enumerate(stories)]
    out["versao"] = VERSAO
    if erros:
        raise FilaInvalida(erros)
    return out


# ===========================================================================
# Migração da v1 (pedido real da §4.7)
# ===========================================================================
def migrar_v1(dados, limite_pergunta: int = LIMITE_PERGUNTA, limite_opcao: int = LIMITE_OPCAO) -> dict:
    """Pedido v1 -> v2 com um story compartilhar_post em publicado_em. Já v2: só valida (idempotente)."""
    if not isinstance(dados, dict):
        raise FilaInvalida("o pedido precisa ser um objeto JSON")
    if e_v2(dados):
        return validar_v2(dados, limite_pergunta, limite_opcao)
    erros = [f"falta o campo '{c}' do pedido v1" for c in ("post_id", "conta", "canal", "link", "publicado_em")
             if not _texto(dados.get(c))]
    if erros:
        raise FilaInvalida(erros)
    try:
        quando = formatar_quando(normalizar_quando(dados["publicado_em"]))
    except ValueError as e:
        raise FilaInvalida(f"'publicado_em' inválido ({e})") from None
    out = copy.deepcopy(dados)
    out.setdefault("titulo", "")
    out.setdefault("destaque", None)
    out.setdefault("criado_em", None)
    out["stories"] = [{
        "quando": quando, "tipo": "compartilhar_post", "arte": None, "zonas": None,
        "texto": _texto(dados.get("titulo")) or None, "figurinha": None, "pergunta_publico": None,
        "destaque": _texto(dados.get("destaque")) or None, "link": _texto(dados["link"]),
    }]
    out["versao"] = VERSAO
    out["migrado_de"] = "v1"
    return validar_v2(out, limite_pergunta, limite_opcao)


# ===========================================================================
# Zonas das figurinhas (arte 1080x1920 -> tela real do aparelho)
# ===========================================================================
def caminho_zonas(arte) -> str:
    """'H:\\...\\story.jpg' -> 'H:\\...\\story_zonas.json' (texto; o separador do caminho é mantido)."""
    txt = str(arte or "")
    if txt.endswith(SUFIXO_ZONAS):
        return txt
    raiz, ext = os.path.splitext(txt)
    return raiz + SUFIXO_ZONAS


def _ret(v, nome: str) -> list:
    if not isinstance(v, (list, tuple)) or len(v) != 4:
        raise FilaInvalida(f"zona '{nome}' precisa ter 4 números [x0, y0, x1, y1]")
    return [float(x) for x in v]


def converter_zona(fracao: list, tela: tuple, area: tuple | None = None) -> list:
    """Fração da arte (0-1) -> pixels da tela: fração × área onde a arte aparece (padrão: a tela toda)."""
    ax0, ay0, ax1, ay1 = area if area else (0, 0, tela[0], tela[1])
    w, h = ax1 - ax0, ay1 - ay0
    f = _ret(fracao, "fracao")
    return [int(round(ax0 + f[0] * w)), int(round(ay0 + f[1] * h)),
            int(round(ax0 + f[2] * w)), int(round(ay0 + f[3] * h))]


def centro_zona(z) -> tuple:
    r = _ret(z, "zona")
    return (int(round((r[0] + r[2]) / 2)), int(round((r[1] + r[3]) / 2)))


def ler_zonas(arte, tela: tuple, area: tuple | None = None) -> dict:
    """Lê <arte>_zonas.json (D) e devolve as zonas na tela REAL do aparelho.

    tela = (largura, altura) lida do `wm size` (nunca 1080x2400 fixo). `area` = (x0, y0, x1, y1) de
    onde a arte aparece na tela (bounds do nó da mídia no dump); sem `area`, a arte é tratada como
    ocupando a tela inteira. Devolve {"link": [...], "enquete": [...], "<nome>_fracao": [...],
    "tela": [W, H], "area": [...], "arte": [1080, 1920], "arquivo": caminho}.
    """
    p = Path(caminho_zonas(arte))
    if not p.is_file():
        raise FilaInvalida(f"não achei as zonas da arte: {p} (gere a arte com scripts\\story_artes.py; "
                           f"ela grava o {SUFIXO_ZONAS} ao lado do JPG)")
    try:
        z = json.loads(p.read_text(encoding="utf-8-sig"))
    except (ValueError, OSError) as e:
        raise FilaInvalida(f"zonas ilegíveis em {p}: {e}") from None
    if not isinstance(z, dict):
        raise FilaInvalida(f"zonas ilegíveis em {p}: esperava um objeto JSON")
    W, H = int(tela[0]), int(tela[1])
    if W <= 0 or H <= 0:
        raise FilaInvalida(f"tamanho de tela inválido: {tela}")
    la = int(z.get("largura") or TELA_ARTE[0])
    al = int(z.get("altura") or TELA_ARTE[1])
    ar = tuple(int(v) for v in area) if area else (0, 0, W, H)
    out = {"tela": [W, H], "area": list(ar), "arte": [la, al], "arquivo": str(p),
           "figurinhas": list(z.get("figurinhas") or [])}
    for nome in ("link", "enquete"):
        fr = z.get(nome + "_fracao")
        if fr is None and z.get(nome) is not None:
            px = _ret(z[nome], nome)
            fr = [px[0] / la, px[1] / al, px[2] / la, px[3] / al]
        if fr is None:
            continue
        fr = [round(v, 4) for v in _ret(fr, nome + "_fracao")]   # 4 casas, como o _zonas.json do story_artes
        out[nome + "_fracao"] = fr
        out[nome] = converter_zona(fr, (W, H), ar)
        out["centro_" + nome] = list(centro_zona(out[nome]))
    if not any(n in out for n in ("link", "enquete")):
        raise FilaInvalida(f"{p} não tem zona 'link' nem 'enquete'")
    return out


# ===========================================================================
# Lote real de estáticos (§4.5) -> itens v2
# ===========================================================================
def _handle_do_canal(canal: str) -> str | None:
    c = marca.CANAIS.get(canal)
    return str(c["handle"]).lstrip("@") if c and c.get("handle") else None


def _tipo_do_tema(tema: str) -> tuple:
    """(tipo, texto, extras) inferidos do tema; tipo None quando não dá para saber."""
    t = str(tema or "").strip()
    n = LOTE.normalizar(t)
    if n.startswith(LOTE.normalizar(PREFIXO_VIDEO_NOVO)):
        return "compartilhar_post", t[len(PREFIXO_VIDEO_NOVO):].strip() or t, {}
    if "comenta ai" in n:
        return "interacao", t, {}
    m = _RX_CONTAGEM.search(n)
    if m:
        return "contagem", t, {"dias": int(m.group(1))}
    return None, t, {}


def de_lote_estaticos(lote, limite_pergunta: int = LIMITE_PERGUNTA, limite_opcao: int = LIMITE_OPCAO,
                      links: dict | None = None, canal: str | None = None, conta: str | None = None,
                      titulo_contagem: str | None = None) -> dict:
    """stories[] e interativo do lote real -> {"data", "canal", "conta", "stories": [itens v2], "recusados"}.

    links: {"HH:MM": "https://..."} dá o link do post para os itens compartilhar_post (o lote não traz);
    sem ele o item sai com link null e "pendencias": ["link do post do vídeo"].
    """
    dados = LOTE.ler_lote(lote)
    if not isinstance(dados, dict):
        raise FilaInvalida("o lote precisa ser um objeto JSON com 'data' e 'stories'/'interativo'")
    try:
        data = _dia(dados.get("data") or dados.get("dia"))
    except ValueError as e:
        raise FilaInvalida(f"o lote não tem 'data' válida: {e}") from None
    canal = LOTE.normalizar(canal or dados.get("canal") or LOTE.CANAL_PADRAO)
    links = {_hora(k): v for k, v in (links or {}).items()}
    itens: list[dict] = []
    recusados: list[dict] = []
    dia0 = datetime.strptime(data, "%Y-%m-%d")

    for i, s in enumerate(dados.get("stories") or []):
        origem = f"stories[{i}]"
        if not isinstance(s, dict):
            recusados.append({"origem": origem, "motivo": "item não é um objeto"})
            continue
        faltas = [c for c in ("hora", "arquivo", "tema") if not _texto(s.get(c))]
        if faltas:
            recusados.append({"origem": origem, "motivo": "item incompleto: falta " + ", ".join(faltas),
                              "tema": s.get("tema")})
            continue
        try:
            hora = _hora(s["hora"])
        except ValueError as e:
            recusados.append({"origem": origem, "motivo": str(e), "tema": s.get("tema")})
            continue
        tipo = LOTE.normalizar(s.get("tipo")) if _texto(s.get("tipo")) else None
        if tipo and tipo not in TIPOS:
            recusados.append({"origem": origem, "motivo": f"tipo '{tipo}' não existe; use um destes: "
                              f"{', '.join(TIPOS)}", "tema": s.get("tema")})
            continue
        texto, extras = s["tema"].strip(), {}
        if not tipo:
            tipo, texto, extras = _tipo_do_tema(s["tema"])
        if not tipo:
            recusados.append({"origem": origem, "motivo": f"não sei o tipo do story pelo tema '{s['tema']}' "
                              "(use 'vídeo novo: ...', 'comenta aí' ou 'contagem N dias', ou dê 'tipo' no item)",
                              "tema": s.get("tema")})
            continue
        item = {"quando": f"{data} {hora}", "tipo": tipo, "arte": str(s["arquivo"]).strip(),
                "zonas": caminho_zonas(s["arquivo"]), "texto": texto, "figurinha": None,
                "pergunta_publico": None, "destaque": _texto(s.get("destaque")) or None,
                "origem": f"lote.{origem}"}
        if tipo == "compartilhar_post":
            link = _texto(s.get("link")) or links.get(hora)
            item["link"] = link or None
            if not link:
                item["pendencias"] = ["link do post do vídeo (vem da fila_story quando o post sair)"]
        elif tipo == "contagem":
            dias = extras.get("dias", s.get("dias"))
            data_fim = _texto(s.get("data")) or ((dia0 + timedelta(days=int(dias))).strftime("%Y-%m-%d")
                                                  if dias is not None else None)
            if not data_fim:
                recusados.append({"origem": origem, "motivo": "contagem sem 'data' nem 'N dias' no tema",
                                  "tema": s.get("tema")})
                continue
            item["figurinha"] = {"tipo": "contagem", "url": None, "rotulo": titulo_contagem, "opcoes": None,
                                 "data": data_fim, "dias": int(dias) if dias is not None else None}
        itens.append(item)

    it = LOTE.ler_interativo(dados)
    if it is not None:
        origem = "interativo"
        motivo = None
        if it["figurinha"] != LOTE.FIGURINHA_PADRAO:
            motivo = f"figurinha '{it['figurinha']}' não é enquete: só sei fazer enquete"
        elif not _texto(it.get("arquivo")):
            motivo = "interativo sem 'arquivo' (a arte do story)"
        elif not _texto(it.get("horario")):
            motivo = "interativo sem 'horario'"
        pergunta = opcoes = None
        hora = None
        if motivo is None:
            try:
                hora = _hora(it["horario"])
                pergunta = LOTE.pergunta_da_figurinha(it, int(limite_pergunta))
                opcoes = LOTE.opcoes_da_figurinha(it, int(limite_opcao))
            except (ValueError, LOTE.LoteErro) as e:
                motivo = str(e)
        if motivo:
            recusados.append({"origem": origem, "motivo": motivo, "tema": it.get("pergunta")})
        else:
            itens.append({"quando": f"{data} {hora}", "tipo": "enquete", "arte": str(it["arquivo"]).strip(),
                          "zonas": caminho_zonas(it["arquivo"]), "texto": LOTE.limpar(it.get("pergunta")),
                          "figurinha": {"tipo": "enquete", "url": None, "rotulo": None, "opcoes": opcoes},
                          "pergunta_publico": pergunta, "destaque": _texto(it.get("destaque")) or None,
                          "conta": it.get("conta"), "origem": "lote.interativo"})
            if it.get("conta") and not conta:
                conta = it["conta"]
    itens.sort(key=lambda d: d["quando"])
    return {"data": data, "canal": canal, "conta": LOTE.normalizar(conta).lstrip("@") if conta else _handle_do_canal(canal),
            "stories": itens, "recusados": recusados}


def pedido_de_lote(lote, agora: datetime | None = None, validar: bool = True, **kw) -> dict:
    """O pedido v2 inteiro a partir do lote (post_id '<canal>_<data>_estaticos'). `agora` vira criado_em."""
    r = de_lote_estaticos(lote, **kw)
    if not r["stories"]:
        raise FilaInvalida(["o lote não deu nenhum story aproveitável"]
                           + [f"{x['origem']}: {x['motivo']}" for x in r["recusados"]])
    pedido = {
        "post_id": f"{r['canal']}_{r['data']}_estaticos", "conta": r["conta"], "canal": r["canal"],
        "link": None, "publicado_em": None, "titulo": f"Estáticos de {r['data']}", "destaque": None,
        "criado_em": formatar_quando(agora) if agora else None, "stories": r["stories"],
        "origem": {"lote": str(lote) if not isinstance(lote, (dict, list)) else "dict",
                   "recusados": r["recusados"]},
        "versao": VERSAO,
    }
    return validar_v2(pedido, kw.get("limite_pergunta", LIMITE_PERGUNTA),
                      kw.get("limite_opcao", LIMITE_OPCAO)) if validar else pedido


# ===========================================================================
# Arquivo (atômico, pelo hpbase)
# ===========================================================================
def gravar_pedido(caminho, dados, **kw) -> Path:
    """Valida e grava (tmp + os.replace). Pedido inválido não toca no disco."""
    ok = validar_v2(dados, **kw)
    return escrever_json(Path(caminho), ok)


def ler_pedido(caminho, migrar: bool = True, **kw) -> dict:
    p = Path(caminho)
    dados = ler_json(p)
    if dados is None:
        raise FilaInvalida(f"não achei o pedido: {p}")
    if not e_v2(dados) and migrar:
        return migrar_v1(dados, **kw)
    return validar_v2(dados, **kw)


# ===========================================================================
# CLI
# ===========================================================================
def _tela(txt: str) -> tuple:
    m = _RX_TELA.match(txt or "")
    if not m:
        raise argparse.ArgumentTypeError("tela no formato LARGURAxALTURA, ex.: 1080x2400")
    return (int(m.group(1)), int(m.group(2)))


def main(argv=None, saida=print) -> int:
    ap = argparse.ArgumentParser(prog="python scripts\\story_fila_v2.py",
                                 description="Pedido da fila_story, esquema v2 (stories[]).")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("validar", help="confere um pedido v2 (código 0 ok, 1 inválido)")
    p.add_argument("arquivo")
    p = sub.add_parser("migrar", help="pedido v1 (§4.7) -> v2 com um story compartilhar_post")
    p.add_argument("arquivo")
    p.add_argument("--saida", help="grava aqui (padrão: imprime)")
    p = sub.add_parser("de-lote", help="lote real de estáticos -> pedido v2")
    p.add_argument("arquivo")
    p.add_argument("--limite", type=int, default=LIMITE_PERGUNTA)
    p.add_argument("--limite-opcao", type=int, default=LIMITE_OPCAO)
    p.add_argument("--agora", help="AAAA-MM-DD HH:MM para criado_em (padrão: vazio)")
    p.add_argument("--saida")
    p = sub.add_parser("zonas", help="zonas da arte na tela real")
    p.add_argument("arte")
    p.add_argument("--tela", type=_tela, required=True, help="ex.: 1080x2400 (do wm size)")
    args = ap.parse_args(argv)
    if not args.cmd:
        ap.print_help()
        return 1
    try:
        if args.cmd == "validar":
            validar_v2(ler_json(Path(args.arquivo)) or {})
            saida("ok: pedido v2 válido")
            return 0
        if args.cmd == "migrar":
            dados = ler_json(Path(args.arquivo))
            if dados is None:
                raise FilaInvalida(f"não achei o pedido: {args.arquivo}")
            out = migrar_v1(dados)
        elif args.cmd == "de-lote":
            agora = normalizar_quando(args.agora) if args.agora else None
            out = pedido_de_lote(args.arquivo, agora=agora, limite_pergunta=args.limite,
                                 limite_opcao=args.limite_opcao)
            for r in out["origem"]["recusados"]:
                saida(f"recusado {r['origem']}: {r['motivo']}")
        else:
            out = ler_zonas(args.arte, args.tela)
        if getattr(args, "saida", None):
            escrever_json(Path(args.saida), out)
            saida(f"gravado: {args.saida}")
        else:
            saida(json.dumps(out, ensure_ascii=False, indent=1))
        return 0
    except FilaInvalida as e:
        saida("pedido inválido:")
        for m in e.motivos:
            saida("  - " + m)
        return 1
    except (ValueError, LOTE.LoteErro) as e:
        saida(f"erro: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
