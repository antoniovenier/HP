"""Configuração das contas (contas.json) e leitura das credenciais.

Ordem de procura do contas.json:
1) caminho passado em --contas;
2) H:\\HypadoLocal\\metricas\\contas.json (cópia do Antônio, se existir);
3) o contas.json de exemplo que vem junto deste pacote (sem segredo).
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from hpbase import SegredoAusente, garantir, ler_json, ler_segredo, mascarar, raiz_local

PERFIS = ("gta", "futebol", "filmes", "receitas", "carros", "destinos")
REDES = ("instagram", "threads", "facebook", "youtube", "tiktok")
REDES_API = ("instagram", "threads", "facebook", "youtube")

PADRAO = {
    "versao_graph": "v21.0",
    "host_graph": "https://graph.facebook.com",
    "versao_threads": "v1.0",
    "host_threads": "https://graph.threads.net",
    "dias_posts": 7,
    "limite_posts": 50,
    "timeout": 30,
    "arquivos_segredo": {"meta": "meta_tokens.txt", "youtube": "youtube_tokens.txt"},
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


def _sensivel(chave: str) -> bool:
    """IDs (IG_GTA_ID, YT_GTA_CANAL, YT_CLIENT_ID) não são segredo; token/chave/senha são."""
    c = chave.upper()
    return any(x in c for x in ("TOKEN", "KEY", "SECRET", "SENHA", "PASS", "REFRESH"))


class Credenciais:
    """Lê token/id dos arquivos em H:\\HypadoLocal\\segredos\\ sem nunca mostrar.

    Guarda os valores lidos só para poder APAGÁ-LOS de qualquer mensagem
    (`mascarar`) antes de ir para log ou JSON.
    """

    def __init__(self, arquivos: dict, pasta=None):
        self.arquivos = dict(arquivos)
        self.pasta = pasta
        self._lidos: set[str] = set()

    def obter(self, grupo: str, *chaves: str) -> str | None:
        arquivo = self.arquivos.get(grupo, grupo)
        for chave in chaves:
            if not chave:
                continue
            try:
                v = ler_segredo(arquivo, chave, pasta=self.pasta)
            except SegredoAusente:
                continue
            if v:
                if _sensivel(chave):
                    self.guardar(v)
                return v
        return None

    def guardar(self, valor) -> None:
        """Valor sensível obtido em tempo de execução (ex.: token OAuth renovado)."""
        if valor and len(str(valor)) >= 6:
            self._lidos.add(str(valor))

    def tem(self, grupo: str, *chaves: str) -> bool:
        return self.obter(grupo, *chaves) is not None

    def mascarar(self, texto) -> str:
        s = str(texto)
        for v in sorted(self._lidos, key=len, reverse=True):
            s = s.replace(v, "***")
        return mascarar(s)


# nomes das chaves no meta_tokens.txt / youtube_tokens.txt (ver LEIA.md)
def chaves(rede: str, conta: str, cfg_rede: dict | None = None) -> dict:
    c = conta.upper()
    cfg_rede = cfg_rede or {}
    pref = {"instagram": "IG", "threads": "TH", "facebook": "FB", "youtube": "YT"}[rede]
    tok = [cfg_rede.get("chave_token"), f"{pref}_{c}_TOKEN", f"{pref}_TOKEN"]
    if rede in ("instagram", "facebook"):
        tok.append("META_TOKEN")
    ids = [cfg_rede.get("chave_id"), f"{pref}_{c}_ID"]
    if rede == "youtube":
        return {"canal": [cfg_rede.get("chave_id"), f"YT_{c}_CANAL", f"YT_{c}_ID"],
                "chave_api": [cfg_rede.get("chave_api"), f"YT_{c}_KEY", "YT_API_KEY"],
                "refresh": [f"YT_{c}_REFRESH_TOKEN", "YT_REFRESH_TOKEN"],
                "client_id": ["YT_CLIENT_ID"], "client_secret": ["YT_CLIENT_SECRET"]}
    return {"token": tok, "id": ids}


def token_e_id(rede: str, conta: str, cfg_rede: dict, cred: Credenciais) -> tuple[str, str]:
    """Token e id da conta na rede; sem algum dos dois → SemToken."""
    from .modelos import SemToken
    k = chaves(rede, conta, cfg_rede)
    token = cred.obter("meta", *k["token"])
    ident = cfg_rede.get("id") or cred.obter("meta", *k["id"])
    faltam = [n for n, v in (("token", token), ("id", ident)) if not v]
    if faltam:
        raise SemToken(f"{rede}/{conta}: falta {' e '.join(faltam)} "
                       f"(chave {k['token'][1] if 'token' in faltam else k['id'][1]})")
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
        return f"{self.cfg['host_graph'].rstrip('/')}/{self.cfg['versao_graph']}"

    @property
    def base_threads(self) -> str:
        return f"{self.cfg['host_threads'].rstrip('/')}/{self.cfg['versao_threads']}"

    def tolerante(self, rede: str, cliente):
        from .insights import InsightsTolerante
        if rede not in self.insights:
            self.insights[rede] = InsightsTolerante(cliente)
        return self.insights[rede]
