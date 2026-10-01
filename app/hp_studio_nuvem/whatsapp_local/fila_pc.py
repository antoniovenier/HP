"""fila_pc — adaptador da fila REAL do WhatsApp do PC e do agendados.json real (§4.5 e §4.8).

O que faz:
  1. Fila real -> pasta. O plantão de hoje guarda UMA LISTA em
     H:\\HypadoLocal\\temp\\whatsapp_fila.json: [{"grupo", "texto", "enviar_apos"}]. O whatsapp_local lê
     uma pasta com 1 JSON por mensagem (H:\\HypadoLocal\\whatsapp_fila\\, formato de fila.py:
     {id, grupo, texto, anexos, tipo, criado_em}). `para_pasta()` converte uma mensagem (campo novo
     `enviar_apos` preservado) e `importar_fila_pc()` enfileira a lista inteira sem duplicar.
  2. Pasta -> fila real. `exportar_fila()` devolve as pendentes como a lista do PC, sem perder
     `enviar_apos`; `exportar_para_pc()` grava de forma atômica.
  3. Validação (`validar_mensagem_pc`): o texto começa EXATAMENTE com "*Claude - *"; o grupo é um
     dos 6 nomes reais (comparação em NFC): "HP | Comissão 🚀", "HP | Futebol ⚽", "HP | Filmes 🎬",
     "HP | Receitas 🍔", "HP | Carros 🏎️", "HP | Destinos ✈️"; `enviar_apos` (se vier) no formato
     "AAAA-MM-DD HH:MM" (hora de Brasília, sem fuso).
  4. Madrugada: de 0h às 7h30 NADA vai para o WhatsApp. Mensagem criada nessa janela sem
     `enviar_apos` ganha "AAAA-MM-DD 07:30" do mesmo dia (`enviar_apos_padrao(agora)`), e
     `pronta_para_enviar(msg, agora)` só libera depois do horário (o relógio é sempre injetado).
  5. Id determinístico (`id_mensagem_pc`): hash de grupo + texto + enviar_apos — importar duas vezes
     não duplica.
  6. agendados.json real: os 6 lugares (GTA em <Drive>\\06 Projeto\\agendados.json e os 5 canais em
     <Drive>\\07 Canais\\<Pasta>\\agendados.json), todos {"itens": [...]}; `ler_agendados_todos()` junta.
     avisos_enviados.json: lista de nomes de arquivo já avisados, tolerando a lista embrulhada pelo
     PowerShell [{"value": [...], "Count": N}] (`ler_avisos_enviados`).
  7. `montar_aviso_no_ar(item, nome_canal=None)`: o texto LITERAL do AVISO.md (§4.8): só as redes em
     que o post saiu, na ordem Instagram, Facebook, TikTok, YouTube, Threads; YouTube
     https://youtube.com/shorts/<id>, TikTok https://www.tiktok.com/@<handle>/video/<id>, Instagram e
     Threads do `links` do item; rede em `redes` sem link usa o link do PERFIL (não atrasa o aviso).

Uso:
    from whatsapp_local import fila_pc
    fila_pc.importar_fila_pc(agora=agora)                  # whatsapp_fila.json -> whatsapp_fila\\*.json
    fila_pc.exportar_fila()                                # pendentes -> [{grupo, texto, enviar_apos}]
    fila_pc.montar_aviso_no_ar(item)                       # item do agendados.json -> texto do aviso
    python -m whatsapp_local.fila_pc importar|exportar|agendados|avisos [--agora "AAAA-MM-DD HH:MM"]

Regras:
- Nunca lê relógio real por conta própria: `agora` é injetado (datetime com ou sem fuso; sem fuso =
  Brasília). Nada aqui abre navegador nem rede.
- Caminhos do PC só nas funções de config.py (arquivo_fila_pc, arquivos_agendados_pc); HP_LOCAL/HP_DRIVE
  trocam a raiz nos testes.
- Gravação sempre atômica (hpbase.escrever_json). Texto em utf-8 com BOM tolerado na leitura.
- SUPOSIÇÕES marcadas no código: cabeçalho do aviso dos canais (CABECALHO_CANAL), links de perfil
  (PERFIL), tipo das mensagens que não são resumo/no ar (TIPO_PADRAO = "aviso").
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, time
from pathlib import Path

from hpbase import FUSO, escrever_json, ler_json, raiz_drive

from .config import (GRUPOS_CANAIS, GRUPOS_REAIS, NOMES_CANAIS, PREFIXO, arquivo_fila_pc,
                     arquivos_agendados_pc, nfc)
from .fila import Fila, nome_seguro

# ------------------------------------------------------------------ constantes (§4.8)
FORMATO_ENVIAR_APOS = "%Y-%m-%d %H:%M"
MADRUGADA_INICIO = time(0, 0)
MADRUGADA_FIM = time(7, 30)          # até 7h29 nada sai; 7h30 em diante pode
TIPO_PADRAO = "aviso"                # SUPOSIÇÃO: mensagem que não é resumo nem "no ar" (ver LEIA)
TIPOS_POR_TEXTO = (                  # (trecho no texto em minúsculas, tipo da fila local)
    ("resumo da semana", "resumo_sabado"),
    ("resumo de ", "resumo_dia"),
    ("resumo do dia", "resumo_dia"),
    ("no ar", "no_ar"),
)
GRUPOS_NFC = {nfc(g): canal for canal, g in GRUPOS_CANAIS.items()}
HANDLES = {"gta": "hpgta6", "futebol": "hp.futebol", "filmes": "hp.filmes",
           "receitas": "hp.receitas", "carros": "hp.carros", "destinos": "hp.destinos"}
HANDLE_CANAL = {h: c for c, h in HANDLES.items()}

# Aviso "no ar" (modelo literal do AVISO.md, §4.8)
CABECALHO_GTA = "🎬 *Novo vídeo no ar!*"
# SUPOSIÇÃO a confirmar com o Antônio: o AVISO.md só descreve o GTA; para os canais o modelo é o
# mesmo trocando o título. Troque aqui se ele quiser outra frase.
CABECALHO_CANAL = "🎬 *Novo post no ar — {canal}!*"
CORPO_AVISO = "Acabou de ser publicado nas nossas redes. Já está no ar nas redes abaixo 🚀"
REDES_AVISO = ("instagram", "facebook", "tiktok", "youtube", "threads")   # nesta ordem
LINHA_REDE = {"instagram": "📸 *Instagram:*", "facebook": "📘 *Facebook:*", "tiktok": "🎵 *TikTok:*",
              "youtube": "▶️ *YouTube:*", "threads": "🧵 *Threads:*"}
LINK_YOUTUBE = "https://youtube.com/shorts/{id}"
LINK_TIKTOK = "https://www.tiktok.com/@{handle}/video/{id}"
# SUPOSIÇÃO: link do perfil de cada rede (usado quando a rede está em `redes` mas não tem link).
# O do Facebook é palpite (a página pode ter outro endereço): confira no facebook_paginas.json.
PERFIL = {"instagram": "https://www.instagram.com/{handle}/",
          "facebook": "https://www.facebook.com/{handle}",
          "tiktok": "https://www.tiktok.com/@{handle}",
          "youtube": "https://www.youtube.com/@{handle}",
          "threads": "https://www.threads.com/@{handle}"}
APELIDOS_REDE = {"ig": "instagram", "fb": "facebook", "tt": "tiktok", "yt": "youtube", "shorts": "youtube",
                 "th": "threads"}
_RX_CANAL_NO_ID = re.compile(r"^(gta|futebol|filmes|receitas|carros|destinos)_")
_RX_URL = re.compile(r"^https?://", re.I)


# ------------------------------------------------------------------ relógio
def _naive(agora: datetime) -> datetime:
    """Hora de Brasília sem fuso (a fila do PC não tem fuso)."""
    if agora.tzinfo is not None:
        agora = agora.astimezone(FUSO).replace(tzinfo=None)
    return agora.replace(second=0, microsecond=0)


def ler_enviar_apos(valor) -> datetime | None:
    """"AAAA-MM-DD HH:MM" (aceita "T" e segundos) -> datetime sem fuso; vazio -> None; inválido -> ValueError."""
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return None
    if isinstance(valor, datetime):
        return _naive(valor)
    s = str(valor).strip().replace("T", " ")
    for fmt in (FORMATO_ENVIAR_APOS, "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s[:19 if fmt.endswith("%S") else 16], fmt)
        except ValueError:
            continue
    raise ValueError(f"enviar_apos inválido: {valor!r} (esperado AAAA-MM-DD HH:MM)")


def texto_enviar_apos(quando: datetime | None) -> str | None:
    return _naive(quando).strftime(FORMATO_ENVIAR_APOS) if quando else None


def madrugada(agora: datetime) -> bool:
    """True entre 0h00 e 7h29 (hora de Brasília): nada vai para o WhatsApp."""
    h = _naive(agora).time()
    return MADRUGADA_INICIO <= h < MADRUGADA_FIM


def enviar_apos_padrao(agora: datetime) -> str | None:
    """Mensagem criada de madrugada ganha "AAAA-MM-DD 07:30" do mesmo dia; fora dela, None."""
    if not madrugada(agora):
        return None
    a = _naive(agora)
    return a.replace(hour=MADRUGADA_FIM.hour, minute=MADRUGADA_FIM.minute).strftime(FORMATO_ENVIAR_APOS)


def pronta_para_enviar(msg: dict, agora: datetime, bloquear_madrugada: bool = True) -> bool:
    """Pode sair agora? Respeita `enviar_apos` (vazio = já) e, por padrão, a madrugada.
    `enviar_apos` inválido = nunca está pronta (a validação explica o motivo)."""
    a = _naive(agora)
    if bloquear_madrugada and madrugada(a):
        return False
    try:
        alvo = ler_enviar_apos((msg or {}).get("enviar_apos"))
    except ValueError:
        return False
    return alvo is None or a >= alvo


# ------------------------------------------------------------------ validação
def grupo_valido(grupo) -> bool:
    return isinstance(grupo, str) and nfc(grupo) in GRUPOS_NFC


def canal_do_grupo(grupo) -> str | None:
    return GRUPOS_NFC.get(nfc(grupo)) if isinstance(grupo, str) else None


def validar_enviar_apos(msg) -> list[str]:
    try:
        ler_enviar_apos((msg or {}).get("enviar_apos"))
    except ValueError as e:
        return [str(e)]
    return []


def validar_mensagem_pc(msg) -> list[str]:
    """Motivos de rejeição (lista vazia = válida): prefixo, grupo ∈ os 6, enviar_apos no formato."""
    if not isinstance(msg, dict):
        return ["a mensagem não é um objeto JSON {…}"]
    motivos: list[str] = []
    texto = msg.get("texto")
    if not isinstance(texto, str):
        motivos.append("sem texto")
    elif not texto.startswith(PREFIXO):
        motivos.append(f"texto não começa exatamente com '{PREFIXO}'")
    elif not texto[len(PREFIXO):].strip():
        motivos.append("texto vazio depois do cabeçalho")
    grupo = msg.get("grupo")
    if not isinstance(grupo, str) or not nfc(grupo):
        motivos.append("sem grupo")
    elif not grupo_valido(grupo):
        motivos.append(f"grupo '{nfc(grupo)}' não é um dos 6 grupos HP ({', '.join(GRUPOS_REAIS)})")
    motivos += validar_enviar_apos(msg)
    return motivos


# ------------------------------------------------------------------ ida: lista do PC -> pasta
def id_mensagem_pc(grupo, texto, enviar_apos=None) -> str:
    """Id determinístico: o mesmo grupo + texto + enviar_apos dá sempre o mesmo id."""
    base = "\n".join([nfc(grupo), str(texto or ""), str(enviar_apos or "")])
    return "pc_" + hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]


def tipo_da_mensagem(texto) -> str:
    t = str(texto or "").lower()
    for trecho, tipo in TIPOS_POR_TEXTO:
        if trecho in t:
            return tipo
    return TIPO_PADRAO


def para_pasta(msg: dict, agora: datetime, tipo: str | None = None) -> dict:
    """Mensagem da lista do PC -> JSON da pasta (formato de fila.py + enviar_apos + origem).
    De madrugada, sem enviar_apos, ganha o 07:30 do dia."""
    grupo = nfc(msg.get("grupo"))
    texto = str(msg.get("texto") or "")
    enviar_apos = msg.get("enviar_apos")
    if isinstance(enviar_apos, str) and not enviar_apos.strip():
        enviar_apos = None
    if enviar_apos is None:
        enviar_apos = enviar_apos_padrao(agora)
    elif isinstance(enviar_apos, datetime):
        enviar_apos = texto_enviar_apos(enviar_apos)
    dados = {
        "id": id_mensagem_pc(grupo, texto, enviar_apos),
        "grupo": grupo,
        "texto": texto,
        "anexos": [str(a) for a in (msg.get("anexos") or [])],
        "tipo": tipo or msg.get("tipo") or tipo_da_mensagem(texto),
        "criado_em": (agora if agora.tzinfo else agora.replace(tzinfo=FUSO)).isoformat(timespec="seconds"),
        "enviar_apos": enviar_apos,
        "origem": "whatsapp_fila.json",
    }
    return dados


def para_lista(dados: dict) -> dict:
    """JSON da pasta -> {grupo, texto, enviar_apos} (o formato do PC; enviar_apos nunca se perde)."""
    return {"grupo": nfc(dados.get("grupo")), "texto": str(dados.get("texto") or ""),
            "enviar_apos": dados.get("enviar_apos") or None}


def ler_fila_pc(arquivo: Path | None = None) -> list[dict]:
    """A lista do whatsapp_fila.json ([] se não existe; tolera {"fila"|"itens"|"mensagens": [...]})."""
    dados = ler_json(Path(arquivo) if arquivo else arquivo_fila_pc(), [])
    if isinstance(dados, dict):
        for chave in ("fila", "itens", "mensagens", "value"):
            if isinstance(dados.get(chave), list):
                dados = dados[chave]
                break
    return [m for m in dados if isinstance(m, dict)] if isinstance(dados, list) else []


def gravar_fila_pc(lista: list[dict], arquivo: Path | None = None) -> Path:
    """Grava a lista no formato do PC, de forma atômica."""
    return escrever_json(Path(arquivo) if arquivo else arquivo_fila_pc(),
                         [para_lista(m) if "id" in m else {"grupo": nfc(m.get("grupo")),
                                                           "texto": str(m.get("texto") or ""),
                                                           "enviar_apos": m.get("enviar_apos") or None}
                          for m in lista])


def importar_fila_pc(arquivo: Path | None = None, fila: Fila | None = None, agora: datetime | None = None,
                     so_mostrar: bool = False, limpar: bool = False) -> list[dict]:
    """Lê whatsapp_fila.json e enfileira cada mensagem válida na pasta (1 JSON por mensagem).
    Devolve a lista convertida com "_situacao": enfileirada | já existia | só mostrar | rejeitada: <motivo>.
    Inválida vai para rejeitadas\\ com o motivo. `limpar=True` esvazia o arquivo do PC depois
    (só quando o plantão antigo NÃO roda mais; senão as duas filas mandariam a mesma coisa)."""
    if agora is None:
        raise ValueError("passe agora= (o relógio é injetado; nada aqui lê a hora real)")
    fila = fila or Fila()
    arquivo = Path(arquivo) if arquivo else arquivo_fila_pc()
    saida = []
    for bruto in ler_fila_pc(arquivo):
        motivos = validar_mensagem_pc(bruto)
        dados = para_pasta(bruto, agora) if not motivos else {**bruto, "id": id_mensagem_pc(
            bruto.get("grupo"), bruto.get("texto"), bruto.get("enviar_apos"))}
        if motivos:
            motivo = "; ".join(motivos)
            if not so_mostrar:
                fila.preparar()
                escrever_json(fila.rejeitadas / f"{nome_seguro(dados['id'])}.json",
                              {**dados, "motivo_rejeicao": motivo,
                               "rejeitada_em": (agora if agora.tzinfo else agora.replace(tzinfo=FUSO)
                                                ).isoformat(timespec="seconds")})
            saida.append({**dados, "_situacao": f"rejeitada: {motivo}"})
            continue
        if so_mostrar:
            saida.append({**dados, "_situacao": "só mostrar"})
        elif fila.ja_existe(dados["id"]):
            saida.append({**dados, "_situacao": "já existia"})
        else:
            fila.enfileirar(dados)
            saida.append({**dados, "_situacao": "enfileirada"})
    if limpar and not so_mostrar and arquivo.exists():
        escrever_json(arquivo, [])
    return saida


# ------------------------------------------------------------------ volta: pasta -> lista do PC
def exportar_fila(fila: Fila | None = None) -> list[dict]:
    """As mensagens pendentes da pasta como a lista do PC [{grupo, texto, enviar_apos}]."""
    fila = fila or Fila()
    return [para_lista(i.dados) for i in fila.pendentes() if isinstance(i.dados, dict)]


def exportar_para_pc(arquivo: Path | None = None, fila: Fila | None = None) -> Path:
    return gravar_fila_pc(exportar_fila(fila), arquivo)


# ------------------------------------------------------------------ agendados.json real (§4.5)
def canal_do_item(item: dict) -> str | None:
    """gta|futebol|...: pelo prefixo do id, pelo grupo_whatsapp, pela conta ou pelo campo canal."""
    if not isinstance(item, dict):
        return None
    c = str(item.get("canal") or "").strip().lower()
    if c in NOMES_CANAIS:
        return c
    m = _RX_CANAL_NO_ID.match(str(item.get("id") or ""))
    if m:
        return m.group(1)
    g = canal_do_grupo(item.get("grupo_whatsapp") or item.get("grupo"))
    if g:
        return g
    h = str(item.get("conta") or "").strip().lstrip("@").lower()
    return HANDLE_CANAL.get(h)


def ler_agendados(caminho: Path) -> list[dict]:
    """Um agendados.json real ({"itens": [...]}; tolera lista solta e {"posts": [...]}) -> itens com
    "canal" e "arquivo_agendados" preenchidos. Arquivo ausente ou quebrado -> []."""
    p = Path(caminho)
    try:
        dados = json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return []
    if isinstance(dados, dict):
        lista = dados.get("itens")
        if not isinstance(lista, list):
            lista = dados.get("posts") or dados.get("agendados") or []
    else:
        lista = dados if isinstance(dados, list) else []
    saida = []
    for it in lista:
        if isinstance(it, dict):
            novo = dict(it)
            novo["canal"] = canal_do_item(it) or it.get("canal")
            novo["arquivo_agendados"] = str(p)
            saida.append(novo)
    return saida


def ler_agendados_todos(arquivos: list[Path] | None = None) -> list[dict]:
    """Junta os itens dos 6 agendados.json (os que existirem), na ordem dos canais."""
    saida: list[dict] = []
    for p in (arquivos if arquivos is not None else arquivos_agendados_pc()):
        saida += ler_agendados(p)
    return saida


def arquivo_avisos_enviados() -> Path:
    return raiz_drive() / "06 Projeto" / "avisos_enviados.json"


def _desembrulhar(dados) -> list:
    """[...] | [{"value": [...], "Count": N}] | {"value": [...]} -> lista de textos."""
    if isinstance(dados, dict):
        dados = dados.get("value") if isinstance(dados.get("value"), list) else \
            dados.get("avisos") or dados.get("itens") or []
    if not isinstance(dados, list):
        return []
    saida: list = []
    for x in dados:
        if isinstance(x, dict) and isinstance(x.get("value"), list):
            saida += _desembrulhar(x["value"])
        elif isinstance(x, (str, int, float)):
            saida.append(str(x))
    return saida


def ler_avisos_enviados(caminho: Path | None = None) -> list[str]:
    """Lista de nomes de arquivo já avisados, tolerando a lista embrulhada pelo PowerShell."""
    p = Path(caminho) if caminho else arquivo_avisos_enviados()
    try:
        dados = json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return []
    vistos: list[str] = []
    for x in _desembrulhar(dados):
        if x not in vistos:
            vistos.append(x)
    return vistos


def gravar_avisos_enviados(caminho: Path | None, lista: list[str]) -> Path:
    """Grava a lista LISA (sem embrulho), atômica."""
    return escrever_json(Path(caminho) if caminho else arquivo_avisos_enviados(), list(lista))


def chave_do_aviso(item: dict) -> str:
    """O que vai para avisos_enviados.json: o nome do arquivo do item (como o plantão); sem arquivo, o id."""
    arq = str(item.get("arquivo") or "").replace("\\", "/").split("/")[-1]
    return arq or str(item.get("id") or "")


def ja_avisado(item: dict, avisados: list[str]) -> bool:
    marcas = {str(a) for a in avisados}
    return chave_do_aviso(item) in marcas or str(item.get("id") or "") in marcas


def marcar_avisado(item: dict, caminho: Path | None = None) -> list[str]:
    lista = ler_avisos_enviados(caminho)
    chave = chave_do_aviso(item)
    if chave and chave not in lista:
        lista.append(chave)
        gravar_avisos_enviados(caminho, lista)
    return lista


def itens_para_avisar(itens: list[dict], avisados: list[str]) -> list[dict]:
    """Itens no ar (status no_ar, ou sem status, com algum link) que ainda não foram avisados."""
    saida = []
    for it in itens:
        status = str(it.get("status") or "no_ar").strip().lower()
        if status not in ("no_ar", "publicado", "agendado", "pendente_chrome"):
            continue
        if not _links_normalizados(it) and not it.get("redes"):
            continue
        if ja_avisado(it, avisados):
            continue
        saida.append(it)
    return saida


# ------------------------------------------------------------------ aviso "no ar" (§4.8)
def _rede(nome) -> str:
    n = str(nome or "").strip().lower()
    return APELIDOS_REDE.get(n, n)


def _links_normalizados(item: dict) -> dict[str, str]:
    links = item.get("links") or item.get("urls") or {}
    if isinstance(links, list):
        links = {i.get("rede"): i.get("url") or i.get("link") for i in links if isinstance(i, dict)}
    if not isinstance(links, dict):
        return {}
    return {_rede(k): str(v).strip() for k, v in links.items() if k and v and str(v).strip()}


def handle_do_item(item: dict) -> str:
    conta = str(item.get("conta") or "").strip().lstrip("@")
    if conta:
        return conta
    return HANDLES.get(canal_do_item(item) or "", "hpgta6")


def link_da_rede(item: dict, rede: str) -> str | None:
    """Link do post naquela rede: `links[rede]` (URL pronta ou só o id, que vira a URL de §4.8),
    ou `ids[rede]`/`<rede>_id`; sem nada, o link do PERFIL (nunca None para as 5 redes do aviso)."""
    rede = _rede(rede)
    handle = handle_do_item(item)
    valor = _links_normalizados(item).get(rede)
    if not valor:
        ids = item.get("ids") if isinstance(item.get("ids"), dict) else {}
        valor = str(ids.get(rede) or item.get(f"{rede}_id") or item.get(f"id_{rede}") or "").strip()
    if valor:
        if _RX_URL.match(valor):
            return valor
        if rede == "youtube":
            return LINK_YOUTUBE.format(id=valor)
        if rede == "tiktok":
            return LINK_TIKTOK.format(handle=handle, id=valor)
        return valor
    modelo = PERFIL.get(rede)
    return modelo.format(handle=handle) if modelo else None


def redes_do_item(item: dict) -> list[str]:
    """As redes em que o post saiu, na ordem de §4.8: `redes` do item; sem `redes`, as que têm link."""
    pedidas = [_rede(r) for r in (item.get("redes") or [])]
    if not pedidas:
        pedidas = list(_links_normalizados(item))
    return [r for r in REDES_AVISO if r in pedidas]


def links_do_aviso(item: dict) -> list[tuple[str, str]]:
    """[(rede, link)] só das redes em que o post saiu, na ordem fixa, com o perfil quando falta link."""
    saida = []
    for r in redes_do_item(item):
        link = link_da_rede(item, r)
        if link:
            saida.append((r, link))
    return saida


def nome_do_canal(item: dict, nome_canal: str | None = None) -> str | None:
    """Nome bonito do canal para o cabeçalho (None = GTA, que usa o cabeçalho literal do AVISO.md)."""
    if nome_canal:
        return nfc(nome_canal)
    canal = canal_do_item(item)
    if not canal or canal == "gta":
        return None
    return NOMES_CANAIS[canal]


def montar_aviso_no_ar(item: dict, nome_canal: str | None = None) -> str:
    """O texto literal do aviso "no ar" (§4.8). Aceita o item cru do agendados.json ou o post
    normalizado pelo montagem.carregar_agendados (que guarda o cru em "item")."""
    if isinstance(item, dict) and isinstance(item.get("item"), dict):
        item = item["item"]
    canal = nome_do_canal(item, nome_canal)
    cabecalho = CABECALHO_GTA if canal is None else CABECALHO_CANAL.format(canal=canal)
    titulo = nfc(item.get("titulo") or item.get("title") or item.get("id") or "")
    linhas = [f"{PREFIXO}{cabecalho}", f"*{titulo}*", "", CORPO_AVISO, ""]
    linhas += [f"{LINHA_REDE[r]} {link}" for r, link in links_do_aviso(item)]
    return "\n".join(linhas)


def grupo_do_item(item: dict) -> str:
    """grupo_whatsapp do item; senão o grupo do canal; senão a Comissão."""
    g = item.get("grupo_whatsapp") or item.get("grupo")
    if grupo_valido(g):
        return nfc(g)
    return GRUPOS_CANAIS.get(canal_do_item(item) or "gta", GRUPOS_CANAIS["gta"])


def mensagem_no_ar(item: dict, agora: datetime, nome_canal: str | None = None) -> dict:
    """O aviso pronto para a pasta (formato de fila.py): tipo no_ar, id determinístico pelo id do
    item, enviar_apos 07:30 se for madrugada."""
    grupo = grupo_do_item(item)
    texto = montar_aviso_no_ar(item, nome_canal)
    chave = nome_seguro(str(item.get("id") or chave_do_aviso(item) or texto))
    dados = para_pasta({"grupo": grupo, "texto": texto}, agora, tipo="no_ar")
    dados["id"] = f"no_ar_{chave}"
    dados["origem"] = str(item.get("arquivo_agendados") or "agendados.json")
    return dados


# ------------------------------------------------------------------ CLI
def _ler_agora(txt: str | None) -> datetime:
    if not txt:
        raise SystemExit("passe --agora \"AAAA-MM-DD HH:MM\" (hora de Brasília): nada aqui lê o relógio sozinho")
    return ler_enviar_apos(txt)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m whatsapp_local.fila_pc",
                                 description="Fila real do PC <-> pasta do whatsapp_local; agendados reais.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("importar", help="whatsapp_fila.json -> whatsapp_fila\\ (1 JSON por mensagem)")
    i.add_argument("--arquivo", help="padrão H:\\HypadoLocal\\temp\\whatsapp_fila.json")
    i.add_argument("--agora", help="AAAA-MM-DD HH:MM (obrigatório)")
    i.add_argument("--so-mostrar", action="store_true")
    i.add_argument("--limpar", action="store_true", help="esvazia o arquivo do PC depois de importar")
    e = sub.add_parser("exportar", help="pendentes da pasta -> lista do PC (imprime ou grava)")
    e.add_argument("--arquivo", help="grava aqui (sem isto só imprime)")
    sub.add_parser("agendados", help="lista os itens dos 6 agendados.json")
    a = sub.add_parser("avisos", help="mostra os avisos 'no ar' que ainda não foram mandados")
    a.add_argument("--agora", help="AAAA-MM-DD HH:MM (obrigatório)")
    args = ap.parse_args(argv)
    if args.cmd == "importar":
        res = importar_fila_pc(Path(args.arquivo) if args.arquivo else None, agora=_ler_agora(args.agora),
                               so_mostrar=args.so_mostrar, limpar=args.limpar)
        for m in res:
            print(f"{m['_situacao']:<14} {m.get('grupo')} | enviar_apos={m.get('enviar_apos')} | "
                  f"{str(m.get('texto'))[:60]!r}")
        print(f"{len(res)} mensagem(ns)")
        return 0
    if args.cmd == "exportar":
        if args.arquivo:
            print(exportar_para_pc(Path(args.arquivo)))
        else:
            print(json.dumps(exportar_fila(), ensure_ascii=False, indent=1))
        return 0
    if args.cmd == "agendados":
        for it in ler_agendados_todos():
            print(f"{it.get('canal'):<9} {it.get('status'):<8} {it.get('id')}  {it.get('arquivo_agendados')}")
        return 0
    if args.cmd == "avisos":
        agora = _ler_agora(args.agora)
        for it in itens_para_avisar(ler_agendados_todos(), ler_avisos_enviados()):
            print("-" * 60)
            print(mensagem_no_ar(it, agora)["texto"])
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
