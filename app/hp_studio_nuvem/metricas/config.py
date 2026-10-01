"""Configuração das contas (contas.json) e leitura das credenciais.

Ordem de procura do contas.json:
1) caminho passado em --contas;
2) H:\\HypadoLocal\\metricas\\contas.json (cópia do Antônio, se existir);
3) o contas.json de exemplo que vem junto deste pacote (sem segredo).

Os NOMES das chaves (reais da §4.3 primeiro, antigos da rodada 1 depois) vêm de
chaves_pc.py; aqui só se lê o valor, na hora, pela classe Credenciais.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from hpbase import garantir, ler_json, mascarar, pasta_segredos, raiz_local

from . import chaves_pc
from .chaves_pc import GRUPOS  # noqa: F401  (re-exportado: rede -> campo -> grupos de arquivos)

PERFIS = ("gta", "futebol", "filmes", "receitas", "carros", "destinos")
REDES = ("instagram", "threads", "facebook", "youtube", "tiktok")
REDES_API = ("instagram", "threads", "facebook", "youtube")

PADRAO = {
    "versao_instagram": "v21.0",                      # graph.instagram.com (§4.3)
    "host_instagram": "https://graph.instagram.com",
    "versao_graph": "v26.0",                          # Facebook (Páginas), graph.facebook.com
    "host_graph": "https://graph.facebook.com",
    "versao_threads": "v1.0",
    "host_threads": "https://graph.threads.net",
    "dias_posts": 7,
    "limite_posts": 50,
    "timeout": 30,
    "arquivos_segredo": dict(chaves_pc.ARQUIVOS_PADRAO),
    "contas": {},
}


def pasta_metricas(saida=None) -> Path:
    return garantir(Path(saida) if saida else raiz_local() / "metricas")


def caminho_config(caminho=None) -> Path:
    if caminho:
        return Path(caminho)
    local = raiz_local() / "metricas" / "contas.json"
    return local if local.exists() else Path(__file__).with_name("contas.json")


def carregar_config(caminho=None) -> dict:
    cfg = copy.deepcopy(PADRAO)
    dados = ler_json(caminho_config(caminho), {}) or {}
    for k, v in dados.items():
        if k.startswith("_"):
            continue
        if isinstance(v, dict) and isinstance(cfg.get(k), dict):
            cfg[k] = {**cfg[k], **v}
        else:
            cfg[k] = v
    return cfg


def _sensivel(chave: str, arquivo: str = "") -> bool:
    """IDs (contas/IG_x/id, IG_GTA_ID, YT_GTA_CANAL, oauth/client_id) não são segredo;
    token/chave/senha e toda linha de *_tokens.txt são (regra em chaves_pc.sensivel)."""
    return chaves_pc.sensivel(chave, arquivo)


class Credenciais:
    """Lê token/id dos arquivos em H:\\HypadoLocal\\segredos\\ sem nunca mostrar.

    `arquivos` = grupo -> arquivo (ou lista de arquivos, procurados em ordem); arquivo .txt é
    CHAVE=valor (aceita @ no nome, aspas, linhas #), arquivo .json é lido por caminho a/b/c
    (ex.: oauth/refresh_tokens/gta). Guarda os valores sensíveis lidos só para poder
    APAGÁ-LOS de qualquer mensagem (`mascarar`) antes de ir para log ou JSON.
    """

    def __init__(self, arquivos: dict, pasta=None):
        self.arquivos = {g: ([a] if isinstance(a, str) else list(a)) for g, a in dict(arquivos).items()}
        self.pasta = pasta
        self._lidos: set[str] = set()

    def _pasta(self) -> Path:
        return Path(self.pasta) if self.pasta else pasta_segredos()

    def _arquivos(self, grupos) -> list[str]:
        saida = []
        for g in ([grupos] if isinstance(grupos, str) else grupos):
            saida.extend(self.arquivos.get(g, [g]))
        return saida

    def obter(self, grupos, *chaves: str) -> str | None:
        """Primeiro valor que existe: grupos em ordem (reais antes dos antigos) e, dentro de
        cada arquivo, as chaves em ordem. `grupos` é um nome ou uma tupla de nomes."""
        for arquivo in self._arquivos(grupos):
            for chave in chaves:
                if not chave:
                    continue
                v = chaves_pc.valor(self._pasta(), arquivo, chave)
                if v:
                    if _sensivel(chave, arquivo):
                        self.guardar(v)
                    return v
        return None

    def guardar(self, valor) -> None:
        """Valor sensível obtido em tempo de execução (ex.: token OAuth renovado)."""
        if valor and len(str(valor)) >= 6:
            self._lidos.add(str(valor))

    def tem(self, grupos, *chaves: str) -> bool:
        return self.obter(grupos, *chaves) is not None

    def mascarar(self, texto) -> str:
        s = str(texto)
        for v in sorted(self._lidos, key=len, reverse=True):
            s = s.replace(v, "***")
        return mascarar(s)


def chaves(rede: str, conta: str, cfg_rede: dict | None = None) -> dict:
    """Nomes das chaves, em ordem de procura: o override do contas.json ("chave_token",
    "chave_id", "chave_api"), depois os NOMES REAIS da §4.3 (IG_<handle> com ponto e minúsculo,
    FB_<canal>, oauth/refresh_tokens/<canal>...) e por último os antigos da rodada 1
    (IG_<CONTA>_TOKEN, IG_<CONTA>_ID, YT_<CONTA>_REFRESH_TOKEN...). Em que arquivo procurar
    cada campo está em GRUPOS[rede][campo] (chaves_pc)."""
    cfg_rede = cfg_rede or {}
    handle = chaves_pc.handle_da_conta(conta, None, rede)
    if cfg_rede.get("usuario"):
        handle = str(cfg_rede["usuario"]).strip().lstrip("@").lower()
    if rede == "youtube":
        k = chaves_pc.nomes_youtube(conta)
        if cfg_rede.get("chave_id"):
            k["canal"] = [cfg_rede["chave_id"]] + k["canal"]
        if cfg_rede.get("chave_api"):
            k["chave_api"] = [cfg_rede["chave_api"]] + k["chave_api"]
        return k
    tok = ([cfg_rede["chave_token"]] if cfg_rede.get("chave_token") else []) \
        + chaves_pc.nomes_token(rede, conta, handle)
    ids = ([cfg_rede["chave_id"]] if cfg_rede.get("chave_id") else []) \
        + chaves_pc.nomes_id(rede, conta, handle)
    return {"token": tok, "id": ids}


def _onde(nomes: list[str], arquivo: str) -> str:
    """'IG_hpgta6 (ou o antigo IG_GTA_TOKEN) em meta_tokens.txt' — só nomes, nunca valor."""
    real = nomes[0]
    antigo = next((n for n in nomes[1:] if n.upper() != real.upper()), None)
    return f"{real}{f' (ou o antigo {antigo})' if antigo else ''} em {arquivo}"


def token_e_id(rede: str, conta: str, cfg_rede: dict, cred: Credenciais) -> tuple[str, str]:
    """Token e id da conta na rede; sem algum dos dois → SemToken (a mensagem só tem nomes).

    O id aceita, nesta ordem: "id" no contas.json, o meta_tokens_meta.json (contas/IG_<handle>/id),
    o facebook_paginas.json (<canal>/id) e os nomes antigos IG_<CONTA>_ID no meta_tokens.txt."""
    from .modelos import SemToken
    k = chaves(rede, conta, cfg_rede)
    g = GRUPOS[rede]
    token = cred.obter(g["token"], *k["token"])
    ident = cfg_rede.get("id") or cred.obter(g["id"], *k["id"])
    faltam = [n for n, v in (("token", token), ("id", ident)) if not v]
    if faltam:
        onde = _onde(k["token"], cred._arquivos(g["token"])[0]) if "token" in faltam \
            else _onde(k["id"], cred._arquivos(g["id"])[0])
        raise SemToken(f"{rede}/{conta}: falta {' e '.join(faltam)} (chave {onde})")
    return token, str(ident)


@dataclass
class Contexto:
    agora: datetime
    cfg: dict
    insights: dict = field(default_factory=dict)  # rede → InsightsTolerante

    @property
    def desde(self) -> datetime:
        return self.agora - timedelta(days=int(self.cfg.get("dias_posts", 7)))

    @property
    def limite_posts(self) -> int:
        return int(self.cfg.get("limite_posts", 50))

    @property
    def base_graph(self) -> str:
        """Facebook (Páginas): https://graph.facebook.com/v26.0"""
        return f"{self.cfg['host_graph'].rstrip('/')}/{self.cfg['versao_graph']}"

    @property
    def base_instagram(self) -> str:
        """Instagram fala com https://graph.instagram.com/v21.0 (§4.3), não com o host do Facebook."""
        host = self.cfg.get("host_instagram") or chaves_pc.HOSTS["instagram"][0]
        versao = self.cfg.get("versao_instagram") or chaves_pc.HOSTS["instagram"][1]
        return f"{str(host).rstrip('/')}/{versao}"

    @property
    def base_threads(self) -> str:
        return f"{self.cfg['host_threads'].rstrip('/')}/{self.cfg['versao_threads']}"

    def tolerante(self, rede: str, cliente):
        from .insights import InsightsTolerante
        if rede not in self.insights:
            self.insights[rede] = InsightsTolerante(cliente)
        return self.insights[rede]
