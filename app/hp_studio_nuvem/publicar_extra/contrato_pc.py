"""Contrato mínimo com o `hp_studio\\publicar\\http` do PC: cópias de `Resposta`,
`ErroRede` e um `ClienteFalso` para os testes.

NO PC, IMPORTAR DE `hp_studio.publicar.http`:
    from hp_studio.publicar.http import Resposta, ErroRede
Os módulos deste pacote fazem `from .contrato_pc import Resposta, ErroRede, entrada`;
na integração basta trocar essas duas classes pelas do PC neste único arquivo
(as assinaturas abaixo são as que a Seção B do prompt descreve como contrato).

O que o PC entrega ao nosso código:
    cliente.pedir(metodo, url, *, consulta=None, form=None, multipart=None, json_=None,
                  corpo=None, cabecalhos=None, tempo=120) -> Resposta
        Resposta.status (int) · .dados (dict ou texto) · .cabecalhos (chaves minúsculas)
        · .json() (dict; levanta ValueError se o corpo não for JSON)
        levanta ErroRede(mensagem, transitorio=False, status=None) em falha de rede/HTTP
    token_de(canal) -> str      (o PC faz o OAuth/refresh; nós NUNCA tocamos em refresh token)
Resultado por rede no formato do `entrada()` do PC: {"status", "link", "id", "erro", ...}.

Regras: o token vai no cabeçalho `Authorization: Bearer …` (YouTube) ou no parâmetro
`access_token` (Graph), nunca na URL de log; `mascarar()` tira os dois de qualquer texto.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

STATUS_FEITO = ("agendado", "publicado", "pendente_chrome")   # os 3 que contam como feito no PC


class ErroRede(Exception):
    """Falha de rede/HTTP vinda do cliente do PC. `transitorio=True` = vale tentar de novo."""

    def __init__(self, mensagem: str, transitorio: bool = False, status: int | None = None):
        super().__init__(mascarar(str(mensagem)))
        self.mensagem = mascarar(str(mensagem))
        self.transitorio = bool(transitorio)
        self.status = status

    def __str__(self) -> str:
        return self.mensagem


@dataclass
class Resposta:
    status: int
    dados: object = None                      # dict/list (JSON já lido) ou texto
    cabecalhos: dict = field(default_factory=dict)

    def __post_init__(self):
        self.status = int(self.status)
        self.cabecalhos = {str(k).lower(): v for k, v in (self.cabecalhos or {}).items()}

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300

    def json(self):
        if isinstance(self.dados, (dict, list)):
            return self.dados
        if isinstance(self.dados, (str, bytes)):
            try:
                return json.loads(self.dados)
            except (ValueError, TypeError) as e:
                raise ValueError(f"resposta HTTP {self.status} não é JSON") from e
        if self.dados is None:
            return {}
        raise ValueError(f"resposta HTTP {self.status} não é JSON")


def entrada(status: str, link: str | None = None, id: str | None = None,
            erro: str | None = None, **extra) -> dict:
    """O dict por rede que o PC grava em publicar.json (contrato `entrada()` do PC)."""
    d = {"status": str(status), "link": link, "id": None if id is None else str(id),
         "erro": None if erro is None else mascarar(str(erro))}
    d.update(extra)
    return d


# ------------------------------------------------------------------ segredos
_RX_SEGREDO = [
    (re.compile(r"(access_token|refresh_token|client_secret|key|token)(\s*[=:]\s*)([^\s&\"',;}]+)", re.I),
     r"\1\2***"),
    (re.compile(r"Bearer\s+[A-Za-z0-9._\-]+", re.I), "Bearer ***"),
    (re.compile(r"\bEAA[A-Za-z0-9]{20,}"), "EAA***"),
    (re.compile(r"\bya29\.[0-9A-Za-z_\-]+"), "ya29.***"),
    (re.compile(r"\bFAKE_NAO_E_TOKEN_\w+"), "***"),   # os valores falsos dos testes também somem
]


def mascarar(texto) -> str:
    s = str(texto)
    for rx, troca in _RX_SEGREDO:
        s = rx.sub(troca, s)
    return s


# ------------------------------------------------------------- cliente falso
@dataclass
class Chamada:
    metodo: str
    url: str
    consulta: dict | None = None
    form: dict | None = None
    multipart: dict | None = None
    json_: object = None
    corpo: object = None
    cabecalhos: dict | None = None
    tempo: float = 120

    @property
    def caminho(self) -> str:
        return self.url.split("?", 1)[0]

    def resumo(self) -> str:
        """Uma linha sem segredo (para mensagens de teste e log)."""
        partes = [self.metodo, self.url]
        if self.consulta:
            partes.append("consulta=" + json.dumps(self.consulta, ensure_ascii=False, sort_keys=True))
        if self.form:
            partes.append("form=" + json.dumps(self.form, ensure_ascii=False, sort_keys=True))
        if self.json_ is not None:
            partes.append("json=" + json.dumps(self.json_, ensure_ascii=False, sort_keys=True))
        return mascarar(" ".join(partes))


class ClienteFalso:
    """Imita o cliente do PC nos testes: `pedir(...)` devolve a próxima resposta que casa.

    Regras (na ordem de cadastro; a primeira que casa responde):
        c.responder("GET", r"/playlists$", {"items": []})                 # dados = JSON
        c.responder("POST", r"/playlists$", {"id": "PL1"}, status=200)
        c.responder("GET", r"/videos$", ErroRede("HTTP 403 quotaExceeded", status=403))
        c.responder("GET", r"/x$", lambda ch: Resposta(200, {...}))     # função(chamada)
        c.responder("GET", r"/pag$", [{"nextPageToken": "b"}, {"items": []}])  # lista = uma por vez
    `vezes=N` limita quantas vezes a regra vale. Chamada sem regra levanta AssertionError
    com o resumo (sem segredo). Tudo fica em `c.chamadas` (lista de Chamada).
    """

    def __init__(self):
        self.regras: list = []
        self.chamadas: list[Chamada] = []

    def responder(self, metodo: str, url_regex: str, resposta=None, status: int = 200,
                  cabecalhos: dict | None = None, vezes: int | None = None):
        self.regras.append({"metodo": metodo.upper(), "rx": re.compile(url_regex),
                            "resposta": resposta, "status": status,
                            "cabecalhos": cabecalhos or {}, "vezes": vezes})
        return self

    def _montar(self, regra: dict, chamada: Chamada) -> Resposta:
        r = regra["resposta"]
        if isinstance(r, list):
            if not r:
                raise AssertionError(f"ClienteFalso: a lista de respostas acabou para {chamada.resumo()}")
            r = r.pop(0)
        if callable(r) and not isinstance(r, Exception):
            r = r(chamada)
        if isinstance(r, BaseException):
            raise r
        if isinstance(r, Resposta):
            return r
        return Resposta(regra["status"], r, regra["cabecalhos"])

    def pedir(self, metodo: str, url: str, *, consulta=None, form=None, multipart=None,
              json_=None, corpo=None, cabecalhos=None, tempo: float = 120) -> Resposta:
        chamada = Chamada(metodo.upper(), url, consulta, form, multipart, json_, corpo,
                          cabecalhos, tempo)
        self.chamadas.append(chamada)
        for regra in self.regras:
            if regra["metodo"] != chamada.metodo or not regra["rx"].search(url):
                continue
            if regra["vezes"] is not None:
                if regra["vezes"] <= 0:
                    continue
                regra["vezes"] -= 1
            return self._montar(regra, chamada)
        raise AssertionError(f"ClienteFalso: nenhuma regra para {chamada.resumo()}")

    # atalhos para os testes
    @property
    def ultima(self) -> Chamada | None:
        return self.chamadas[-1] if self.chamadas else None

    def chamadas_de(self, metodo: str | None = None, url_regex: str | None = None) -> list[Chamada]:
        rx = re.compile(url_regex) if url_regex else None
        return [c for c in self.chamadas
                if (metodo is None or c.metodo == metodo.upper()) and (rx is None or rx.search(c.url))]

    def texto_de_tudo(self) -> str:
        """Tudo que passou pelo cliente, como texto (para provar que o token não vaza em log)."""
        return "\n".join(c.resumo() for c in self.chamadas)
