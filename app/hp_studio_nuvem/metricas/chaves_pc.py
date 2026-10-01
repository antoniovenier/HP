"""chaves_pc — quais chaves de token existem em H:\\HypadoLocal\\segredos\\ (só os NOMES).

O que faz: dado o diretório de segredos (injetado), lista os nomes das chaves que existem
em cada arquivo SEM devolver nem guardar valor nenhum, e monta por conta e rede o que o
coletor vai usar: {"chave_token", "id", "host", "versao", "arquivo", "status"} (§4.3 do
enunciado da rodada 2). Também é a fonte dos NOMES reais (e dos antigos da rodada 1) que o
metricas/config.py usa para ler o token na hora da coleta.

Uso:
    from metricas.chaves_pc import inventario
    inv = inventario(pasta_segredos, cfg)          # cfg = metricas.config.carregar_config()
    inv["futebol"]["instagram"] -> {"chave_token": "IG_hp.futebol", "id": "1784...",
                                    "host": "https://graph.instagram.com", "versao": "v21.0",
                                    "arquivo": "meta_tokens.txt", "status": "ok"}
    python -m metricas chaves [--json]             # imprime o inventário (nunca um valor)

Regras:
- Nomes reais primeiro, antigos depois. Instagram/Threads: IG_<handle> / TH_<handle> em
  meta_tokens.txt (handle sem @, minúsculo, pode ter ponto: IG_hpgta6, TH_hp.futebol), depois
  IG_<CONTA>_TOKEN, IG_TOKEN, META_TOKEN. Facebook: FB_<canal> em facebook_tokens.txt (canal =
  gta|futebol|..., não é handle), depois FB_<CONTA>_TOKEN, FB_TOKEN, META_TOKEN. YouTube:
  oauth/refresh_tokens/<canal> + oauth/client_id + oauth/client_secret em youtube.json, depois
  YT_<CONTA>_REFRESH_TOKEN, YT_CLIENT_ID, YT_CLIENT_SECRET em youtube_tokens.txt.
- Id de conta não é segredo: contas/IG_<handle>/id (meta_tokens_meta.json), <canal>/id
  (facebook_paginas.json), canais/<canal> (youtube.json) ou <canal>/id (youtube_canais.json);
  antigos IG_<CONTA>_ID, FB_<CONTA>_ID, YT_<CONTA>_CANAL.
- YouTube só coleta com "autorizado": true na config de contas; senão status nao_autorizado.
- O handle vem do contas.json ("usuario") ou da tabela hpbase.fila_api_pc.CANAIS.
- Este módulo nunca imprime, loga nem devolve valor de token. Quem lê o valor, só na hora da
  chamada à API, é a classe Credenciais do config.py (que o apaga de toda mensagem).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from hpbase.fila_api_pc import CANAIS

PERFIS = ("gta", "futebol", "filmes", "receitas", "carros", "destinos")
REDES = ("instagram", "threads", "facebook", "youtube", "tiktok")

# host e versão reais (§4.3); o contas.json pode sobrepor com host_<rede>/versao_<rede>
# (Facebook usa os nomes antigos host_graph/versao_graph)
HOSTS = {
    "instagram": ("https://graph.instagram.com", "v21.0"),
    "threads": ("https://graph.threads.net", "v1.0"),
    "facebook": ("https://graph.facebook.com", "v26.0"),
    "youtube": ("https://www.googleapis.com", "v3"),   # SUPOSIÇÃO: §4.3 não diz host do YouTube
}
CHAVE_HOST = {"instagram": ("host_instagram", "versao_instagram"),
              "threads": ("host_threads", "versao_threads"),
              "facebook": ("host_graph", "versao_graph"),
              "youtube": ("host_youtube", "versao_youtube")}

# grupo lógico -> arquivo(s) em segredos\ (o contas.json pode trocar em "arquivos_segredo")
ARQUIVOS_PADRAO = {
    "meta": "meta_tokens.txt",                 # IG_<handle>= / TH_<handle>= (e os antigos)
    "meta_meta": "meta_tokens_meta.json",      # contas/IG_<handle>/id (sem token)
    "facebook": "facebook_tokens.txt",         # FB_<canal>=
    "facebook_paginas": "facebook_paginas.json",   # <canal>/id (sem token)
    "youtube_oauth": "youtube.json",           # oauth/refresh_tokens/<canal>, api_key, canais/<canal>
    "youtube_canais": "youtube_canais.json",   # <canal>/id (sem token)
    "youtube": "youtube_tokens.txt",           # antigo da rodada 1 (YT_<CONTA>_...)
}
# por rede e campo: em que grupos procurar, nesta ordem (reais antes dos antigos)
GRUPOS = {
    "instagram": {"token": ("meta",), "id": ("meta_meta", "meta")},
    "threads": {"token": ("meta",), "id": ("meta_meta", "meta")},
    "facebook": {"token": ("facebook", "meta"), "id": ("facebook_paginas", "meta")},
    "youtube": {"canal": ("youtube_oauth", "youtube_canais", "youtube"),
                "chave_api": ("youtube_oauth", "youtube"),
                "refresh": ("youtube_oauth", "youtube"),
                "client_id": ("youtube_oauth", "youtube"),
                "client_secret": ("youtube_oauth", "youtube")},
}
# arquivos cujas linhas são SEMPRE token (menos as que terminam em _ID/_CANAL)
ARQUIVOS_DE_TOKEN = ("meta_tokens.txt", "facebook_tokens.txt", "pinterest_tokens.txt",
                     "facebook_token_usuario.txt")
_RX_SENSIVEL = re.compile(r"TOKEN|KEY|SECRET|SENHA|PASS|REFRESH", re.I)
_RX_ID = re.compile(r"(_ID$|_CANAL$|/id$|^contas/|^canais/|client_id$)", re.I)


# --- handle, nomes ---------------------------------------------------------------------
def handle_da_conta(conta: str, cfg_conta: dict | None = None, rede: str = "instagram") -> str:
    """Handle sem @ e minúsculo: contas.json -> <rede>.usuario (ou instagram.usuario), senão
    a tabela CANAIS do publicador (gta -> hpgta6, futebol -> hp.futebol...)."""
    cfg_conta = cfg_conta or {}
    for r in (rede, "instagram", "threads", "tiktok"):
        bloco = cfg_conta.get(r)
        if isinstance(bloco, dict) and bloco.get("usuario"):
            return str(bloco["usuario"]).strip().lstrip("@").lower()
    if conta in CANAIS:
        return CANAIS[conta][0]
    return str(conta).strip().lstrip("@").lower()


def nomes_token(rede: str, conta: str, handle: str | None = None) -> list[str]:
    """Nomes da chave do token, do real para o antigo (sem o override do contas.json)."""
    c = conta.upper()
    h = handle or handle_da_conta(conta)
    if rede == "instagram":
        return [f"IG_{h}", f"IG_{c}_TOKEN", "IG_TOKEN", "META_TOKEN"]
    if rede == "threads":
        return [f"TH_{h}", f"TH_{c}_TOKEN", "TH_TOKEN"]
    if rede == "facebook":
        return [f"FB_{conta}", f"FB_{c}_TOKEN", "FB_TOKEN", "META_TOKEN"]
    if rede == "youtube":
        return [f"oauth/refresh_tokens/{conta}", f"YT_{c}_REFRESH_TOKEN", "YT_REFRESH_TOKEN"]
    return []


def nomes_id(rede: str, conta: str, handle: str | None = None) -> list[str]:
    """Nomes/caminhos do id da conta (não é segredo), do real para o antigo."""
    c = conta.upper()
    h = handle or handle_da_conta(conta)
    if rede == "instagram":
        return [f"contas/IG_{h}/id", f"IG_{c}_ID"]
    if rede == "threads":
        return [f"contas/TH_{h}/id", f"TH_{c}_ID"]
    if rede == "facebook":
        return [f"{conta}/id", f"FB_{c}_ID"]
    if rede == "youtube":
        return [f"canais/{conta}", f"{conta}/id", f"YT_{c}_CANAL", f"YT_{c}_ID"]
    return []


def nomes_youtube(conta: str) -> dict:
    c = conta.upper()
    return {"canal": nomes_id("youtube", conta),
            "chave_api": ["api_key", f"YT_{c}_KEY", "YT_API_KEY"],
            "refresh": nomes_token("youtube", conta),
            "client_id": ["oauth/client_id", "YT_CLIENT_ID"],
            "client_secret": ["oauth/client_secret", "YT_CLIENT_SECRET"]}


def sensivel(chave: str, arquivo: str = "") -> bool:
    """A chave guarda segredo? Tudo que tem TOKEN/KEY/SECRET/REFRESH... e toda linha dos
    arquivos *_tokens.txt (menos *_ID/*_CANAL e os caminhos de id) é segredo."""
    k = str(chave or "")
    if _RX_SENSIVEL.search(k):
        return True
    if _RX_ID.search(k):
        return False
    return Path(str(arquivo or "")).name.lower() in ARQUIVOS_DE_TOKEN


def normalizar_nome(chave: str) -> str:
    """'ig_@HP.Futebol' -> 'ig_hp.futebol' (como o ler_tokens do publicador: sem @, sem
    maiúscula). Comparação de nomes é sempre por este valor."""
    k = str(chave or "").strip().strip('"').strip("'")
    m = re.match(r"^(IG|TH|FB|PIN|YT)_@?(.+)$", k, re.I)
    if m:
        k = f"{m.group(1)}_{m.group(2)}"
    return k.lower()


# --- leitura de NOMES (nunca de valores) ------------------------------------------------
def _linhas(p: Path) -> list[str]:
    try:
        texto = Path(p).read_text(encoding="utf-8-sig")
    except (FileNotFoundError, NotADirectoryError, UnicodeDecodeError, OSError):
        return []
    return [l.strip() for l in texto.splitlines() if l.strip() and not l.strip().startswith("#")]


def nomes_no_txt(p: Path) -> list[str]:
    """Só o lado esquerdo do '=' de cada linha (o valor é descartado na hora)."""
    nomes = []
    for linha in _linhas(p):
        if "=" not in linha:
            continue
        nome = normalizar_nome(linha.split("=", 1)[0])
        if nome and nome not in nomes:
            nomes.append(nome)
    return nomes


def _json(p: Path):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, NotADirectoryError, json.JSONDecodeError, UnicodeDecodeError, OSError):
        return None


def _caminhos(dados, prefixo: str = "") -> list[str]:
    """Chaves de um JSON como caminhos a/b/c (só os nomes; valor escalar é descartado)."""
    saida = []
    if isinstance(dados, dict):
        for k, v in dados.items():
            cam = f"{prefixo}/{k}" if prefixo else str(k)
            saida.append(cam)
            saida.extend(_caminhos(v, cam))
    return saida


def nomes_no_json(p: Path) -> list[str]:
    return [normalizar_nome(c) for c in _caminhos(_json(p))]


def nomes_no_arquivo(p: Path) -> list[str]:
    p = Path(p)
    return nomes_no_json(p) if p.suffix.lower() == ".json" else nomes_no_txt(p)


def existe(pasta: Path, arquivo: str, chave: str) -> bool:
    return normalizar_nome(chave) in nomes_no_arquivo(Path(pasta) / arquivo)


# --- leitura de valor (usada SÓ pela Credenciais; id não é segredo) ----------------------
def valor_txt(p: Path, chave: str) -> str | None:
    """Valor de CHAVE=valor (aceita @ no nome, aspas no valor, linhas #). Devolve só a quem
    chamou; nunca imprime."""
    alvo = normalizar_nome(chave)
    for linha in _linhas(p):
        if "=" not in linha:
            continue
        k, v = linha.split("=", 1)
        if normalizar_nome(k) == alvo:
            v = v.strip().strip('"').strip("'")
            return v or None
    return None


def valor_json(p: Path, caminho: str) -> str | None:
    """Valor escalar em um caminho a/b/c do JSON (compara os nomes sem maiúscula e sem @)."""
    dados = _json(p)
    for parte in str(caminho).split("/"):
        if not isinstance(dados, dict):
            return None
        alvo = normalizar_nome(parte)
        achado = None
        for k in dados:
            if normalizar_nome(k) == alvo:
                achado = k
                break
        if achado is None:
            return None
        dados = dados[achado]
    if dados is None or isinstance(dados, (dict, list, bool)):
        return None
    s = str(dados).strip()
    return s or None


def valor(pasta: Path, arquivo: str, chave: str) -> str | None:
    p = Path(pasta) / arquivo
    return valor_json(p, chave) if p.suffix.lower() == ".json" else valor_txt(p, chave)


# --- inventário por conta e rede -----------------------------------------------------------
def _arquivos(cfg: dict, grupo: str) -> list[str]:
    a = (cfg.get("arquivos_segredo") or {}).get(grupo, ARQUIVOS_PADRAO.get(grupo, grupo))
    return [a] if isinstance(a, str) else list(a)


def _achar(pasta: Path, cfg: dict, grupos, nomes: list[str]) -> tuple[str | None, str | None]:
    """(nome, arquivo) do primeiro nome que existe, nos grupos em ordem; (None, None) se nada."""
    for g in grupos:
        for arq in _arquivos(cfg, g):
            lista = nomes_no_arquivo(Path(pasta) / arq)
            for n in nomes:
                if n and normalizar_nome(n) in lista:
                    return n, arq
    return None, None


def _ler_id(pasta: Path, cfg: dict, grupos, nomes: list[str]) -> tuple[str | None, str | None]:
    for g in grupos:
        for arq in _arquivos(cfg, g):
            for n in nomes:
                v = valor(pasta, arq, n)
                if v:
                    return v, arq
    return None, None


def host_versao(rede: str, cfg: dict, cfg_rede: dict | None = None) -> tuple[str | None, str | None]:
    cfg_rede = cfg_rede or {}
    if rede not in HOSTS:
        return None, None
    kh, kv = CHAVE_HOST[rede]
    host = cfg_rede.get("host") or cfg.get(kh) or HOSTS[rede][0]
    versao = cfg_rede.get("versao") or cfg.get(kv) or HOSTS[rede][1]
    return str(host).rstrip("/"), str(versao)


def _candidatos_token(rede, conta, cfg_rede, handle) -> list[str]:
    extra = [cfg_rede.get("chave_token")] if cfg_rede.get("chave_token") else []
    return extra + nomes_token(rede, conta, handle)


def _candidatos_id(rede, conta, cfg_rede, handle) -> list[str]:
    extra = [cfg_rede.get("chave_id")] if cfg_rede.get("chave_id") else []
    return extra + nomes_id(rede, conta, handle)


def _entrada_meta(pasta, cfg, rede, conta, cfg_rede, handle) -> dict:
    host, versao = host_versao(rede, cfg, cfg_rede)
    cand = _candidatos_token(rede, conta, cfg_rede, handle)
    nome, arq = _achar(pasta, cfg, GRUPOS[rede]["token"], cand)
    ident, arq_id = (str(cfg_rede["id"]), "contas.json") if cfg_rede.get("id") else (None, None)
    if not ident:
        ident, arq_id = _ler_id(pasta, cfg, GRUPOS[rede]["id"], _candidatos_id(rede, conta, cfg_rede, handle))
    falta = [x for x, ok in (("token", nome), ("id", ident)) if not ok]
    return {"chave_token": nome or cand[0], "id": ident, "host": host, "versao": versao,
            "arquivo": arq or _arquivos(cfg, GRUPOS[rede]["token"][0])[0],
            "arquivo_id": arq_id, "status": "ok" if not falta else "sem_token", "falta": falta,
            "nomes": cand, "nomes_id": _candidatos_id(rede, conta, cfg_rede, handle),
            "handle": handle}


def _entrada_youtube(pasta, cfg, conta, cfg_rede) -> dict:
    host, versao = host_versao("youtube", cfg, cfg_rede)
    k = nomes_youtube(conta)
    if cfg_rede.get("chave_api"):
        k["chave_api"] = [cfg_rede["chave_api"]] + k["chave_api"]
    if cfg_rede.get("chave_id"):
        k["canal"] = [cfg_rede["chave_id"]] + k["canal"]
    g = GRUPOS["youtube"]
    refresh, arq = _achar(pasta, cfg, g["refresh"], k["refresh"])
    cid, _ = _achar(pasta, cfg, g["client_id"], k["client_id"])
    csec, _ = _achar(pasta, cfg, g["client_secret"], k["client_secret"])
    chave_api, _ = _achar(pasta, cfg, g["chave_api"], k["chave_api"])
    canal, arq_id = (str(cfg_rede["id"]), "contas.json") if cfg_rede.get("id") else (None, None)
    if not canal:
        canal, arq_id = _ler_id(pasta, cfg, g["canal"], k["canal"])
    oauth = bool(refresh and cid and csec)
    falta = []
    if not canal:
        falta.append("id")
    if not (chave_api or oauth):
        falta.append("token")
    if not cfg_rede.get("autorizado", False):
        status = "nao_autorizado"
    else:
        status = "ok" if not falta else "sem_token"
    return {"chave_token": refresh or k["refresh"][0], "id": canal, "host": host, "versao": versao,
            "arquivo": arq or _arquivos(cfg, g["refresh"][0])[0], "arquivo_id": arq_id,
            "status": status, "falta": falta, "autorizado": bool(cfg_rede.get("autorizado", False)),
            "oauth": {"refresh_token": bool(refresh), "client_id": bool(cid), "client_secret": bool(csec)},
            "api_key": bool(chave_api), "nomes": k["refresh"], "nomes_id": k["canal"]}


def inventario(pasta_segredos, cfg: dict, contas=None, redes=None) -> dict:
    """{conta: {rede: {"chave_token", "id", "host", "versao", "arquivo", "status", ...}}}.

    status: ok | sem_token (campo "falta" diz se é o token, o id ou os dois) | nao_autorizado
    (YouTube com "autorizado": false) | inativo ("ativo": false) | manual (TikTok).
    Nenhum valor de token é lido para montar isto: só os nomes das linhas/chaves.
    """
    pasta = Path(pasta_segredos)
    contas = [contas] if isinstance(contas, str) else list(contas or cfg.get("contas") or PERFIS)
    redes = [redes] if isinstance(redes, str) else list(redes or REDES)
    saida: dict = {}
    for conta in contas:
        cfg_conta = (cfg.get("contas") or {}).get(conta) or {}
        bloco = saida.setdefault(conta, {})
        for rede in redes:
            cfg_rede = cfg_conta.get(rede)
            if not isinstance(cfg_rede, dict):
                continue
            handle = handle_da_conta(conta, cfg_conta, rede)
            if not cfg_rede.get("ativo", True):
                bloco[rede] = {"chave_token": None, "id": None, "host": None, "versao": None,
                               "arquivo": None, "status": "inativo", "handle": handle}
            elif rede == "tiktok":
                bloco[rede] = {"chave_token": None, "id": None, "host": None, "versao": None,
                               "arquivo": None, "status": "manual", "handle": handle}
            elif rede == "youtube":
                bloco[rede] = _entrada_youtube(pasta, cfg, conta, cfg_rede)
            elif rede in GRUPOS:
                bloco[rede] = _entrada_meta(pasta, cfg, rede, conta, cfg_rede, handle)
    return saida


def resumo(inv: dict) -> list[str]:
    """Linhas para a tela: 'gta/instagram: ok  IG_hpgta6 (meta_tokens.txt)  id ok'."""
    linhas = []
    for conta, redes in inv.items():
        for rede, e in redes.items():
            if e["status"] in ("manual", "inativo"):
                linhas.append(f"{conta}/{rede}: {e['status']}")
                continue
            ident = "ok" if e.get("id") else "falta"
            tok = "ok" if "token" not in e.get("falta", []) else "falta"
            linhas.append(f"{conta}/{rede}: {e['status']}  token {tok} {e['chave_token']} "
                          f"({e['arquivo']})  id {ident}  {e['host']}/{e['versao']}")
    return linhas
