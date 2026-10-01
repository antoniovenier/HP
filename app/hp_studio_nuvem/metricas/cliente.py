"""Cliente HTTP das métricas.

- `requests` com timeout;
- repete com espera crescente em 429 / 5xx / queda de rede (respeita Retry-After);
- paginação por `paging.next` (Graph API) na função `paginar`;
- NENHUMA mensagem de erro carrega token: todo valor de `access_token`,
  `key`, `client_secret` ou `refresh_token` que passa pelo cliente é guardado
  e trocado por *** em qualquer texto de erro (além do `mascarar` do hpbase).

Os testes injetam um cliente falso (qualquer objeto com `get(url, params)`)
ou uma `sessao` falsa no lugar do `requests.Session`.
"""
from __future__ import annotations

import time
from urllib.parse import parse_qsl, urlsplit

from hpbase import mascarar

CHAVES_SECRETAS = {"access_token", "key", "client_secret", "refresh_token",
                   "token", "input_token"}

# Códigos da Graph API que significam "token/permissão" (e não defeito do pedido)
CODIGOS_AUTORIZACAO = {10, 102, 190} | set(range(200, 300))
# Motivos do Google que são cota (não autorização)
MOTIVOS_COTA = {"quotaExceeded", "dailyLimitExceeded", "rateLimitExceeded",
                "userRateLimitExceeded"}


class ErroAPI(Exception):
    """Erro de chamada à API. A mensagem já vem mascarada."""

    def __init__(self, mensagem: str, status: int | None = None,
                 codigo: int | None = None, subcodigo: int | None = None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status
        self.codigo = codigo
        self.subcodigo = subcodigo

    def __str__(self) -> str:
        return self.mensagem


class ErroNaoAutorizado(ErroAPI):
    """Token vencido/inválido ou permissão que falta (vira status nao_autorizado)."""


class ErroTemporario(ErroAPI):
    """429, 5xx ou rede caída — mesmo depois de todas as tentativas."""


def _eh_falha_de_rede(e: BaseException) -> bool:
    if isinstance(e, OSError):  # TimeoutError, ConnectionError, socket.timeout
        return True
    return any(c.__name__ == "RequestException" for c in type(e).__mro__)


class ClienteHTTP:
    """Uso: `ClienteHTTP().get(url, {"fields": "...", "access_token": tok})`."""

    def __init__(self, timeout: float = 30, esperas=(2, 10, 30),
                 dormir=time.sleep, sessao=None, espera_max: float = 120):
        self.timeout = timeout
        self.esperas = tuple(esperas)
        self.dormir = dormir
        self.espera_max = espera_max
        self._sessao = sessao
        self._segredos: set[str] = set()
        self.chamadas = 0

    # --- segredos -------------------------------------------------------
    @property
    def sessao(self):
        if self._sessao is None:
            import requests  # só na hora (os testes nem precisam dele)
            self._sessao = requests.Session()
        return self._sessao

    def registrar_segredo(self, valor) -> None:
        if valor and len(str(valor)) >= 6:
            self._segredos.add(str(valor))

    def mascarar(self, texto) -> str:
        s = str(texto)
        for v in sorted(self._segredos, key=len, reverse=True):
            s = s.replace(v, "***")
        return mascarar(s)

    def _registrar_de(self, url: str = "", params: dict | None = None) -> None:
        for k, v in (params or {}).items():
            if str(k).lower() in CHAVES_SECRETAS:
                self.registrar_segredo(v)
        if url and "?" in url:
            for k, v in parse_qsl(urlsplit(url).query):
                if k.lower() in CHAVES_SECRETAS:
                    self.registrar_segredo(v)

    # --- chamadas -------------------------------------------------------
    def get(self, url: str, params: dict | None = None) -> dict:
        return self._pedir("GET", url, params=params)

    def post(self, url: str, dados: dict | None = None) -> dict:
        return self._pedir("POST", url, dados=dados)

    def _espera(self, i: int, resposta=None) -> float:
        base = self.esperas[i] if i < len(self.esperas) else self.esperas[-1]
        try:
            ra = (resposta.headers or {}).get("Retry-After") if resposta is not None else None
            if ra is not None:
                return min(float(ra), self.espera_max)
        except (TypeError, ValueError, AttributeError):
            pass
        return base

    def _pedir(self, metodo: str, url: str, params=None, dados=None) -> dict:
        self._registrar_de(url, params)
        self._registrar_de("", dados)
        caminho = self.mascarar(urlsplit(url).path or url)
        ultimo: ErroAPI | None = None
        for i in range(len(self.esperas) + 1):
            espera = None
            self.chamadas += 1
            try:
                if metodo == "GET":
                    r = self.sessao.get(url, params=params, timeout=self.timeout)
                else:
                    r = self.sessao.post(url, data=dados, timeout=self.timeout)
            except Exception as e:  # noqa: BLE001 — classificado logo abaixo
                if not _eh_falha_de_rede(e):
                    msg = self.mascarar(f"{caminho}: {type(e).__name__}: {e}")
                    ultimo = ErroAPI(msg[:300])
                    break
                msg = self.mascarar(f"{caminho}: falha de rede ({type(e).__name__}: {e})")
                ultimo = ErroTemporario(msg[:300])
                espera = self._espera(i)
            else:
                status = int(getattr(r, "status_code", 0) or 0)
                if status == 429 or status >= 500:
                    ultimo = ErroTemporario(f"HTTP {status} em {caminho}"
                                            f"{self._resumo_erro(r)}", status=status)
                    espera = self._espera(i, r)
                elif status >= 400:
                    raise self._erro(status, r, caminho)
                else:
                    try:
                        return r.json()
                    except ValueError:
                        raise ErroAPI(f"{caminho}: resposta não é JSON", status=status)
            if espera is not None and i < len(self.esperas):
                self.dormir(espera)
        assert ultimo is not None
        raise ultimo

    def _corpo(self, r) -> dict:
        try:
            c = r.json()
            return c if isinstance(c, dict) else {}
        except Exception:  # noqa: BLE001
            return {}

    def _resumo_erro(self, r) -> str:
        err = self._corpo(r).get("error")
        if isinstance(err, dict) and err.get("message"):
            return ": " + self.mascarar(str(err["message"]))[:200]
        return ""

    def _erro(self, status: int, r, caminho: str) -> ErroAPI:
        err = self._corpo(r).get("error")
        codigo = subcodigo = None
        motivos: set[str] = set()
        texto = ""
        if isinstance(err, dict):
            texto = str(err.get("message") or "")
            codigo = err.get("code")
            subcodigo = err.get("error_subcode")
            for d in err.get("errors") or []:
                if isinstance(d, dict) and d.get("reason"):
                    motivos.add(str(d["reason"]))
        elif isinstance(err, str):  # OAuth do Google: {"error": "invalid_grant"}
            texto = err
        msg = self.mascarar(f"HTTP {status} em {caminho}: {texto}".strip())[:300]
        cod = codigo if isinstance(codigo, int) else None
        if motivos & MOTIVOS_COTA:
            return ErroAPI(msg, status, cod, subcodigo)
        if status in (401, 403) or cod in CODIGOS_AUTORIZACAO:
            return ErroNaoAutorizado(msg, status, cod, subcodigo)
        return ErroAPI(msg, status, cod, subcodigo)


def paginar(cliente, url: str, params: dict | None = None,
            limite: int | None = None, max_paginas: int = 50):
    """Rende os itens de `data` seguindo `paging.next` (que já traz os parâmetros)."""
    n = 0
    paginas = 0
    while url and paginas < max_paginas:
        resp = cliente.get(url, params) or {}
        paginas += 1
        for item in resp.get("data") or []:
            yield item
            n += 1
            if limite and n >= limite:
                return
        url = (resp.get("paging") or {}).get("next")
        params = None
