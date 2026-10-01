import pytest

from metricas.cliente import (ClienteHTTP, ErroAPI, ErroNaoAutorizado, ErroTemporario)
from metricas.insights import InsightsTolerante, ler_valores

TOKEN = "EAABtokenSuperSecreto0123456789abcdef"


class Resposta:
    def __init__(self, status=200, corpo=None, headers=None):
        self.status_code = status
        self._corpo = corpo if corpo is not None else {}
        self.headers = headers or {}

    def json(self):
        if isinstance(self._corpo, Exception):
            raise self._corpo
        return self._corpo


class SessaoFalsa:
    """Imita requests.Session: devolve as respostas em ordem (ou levanta)."""

    def __init__(self, *respostas):
        self.respostas = list(respostas)
        self.pedidos = []

    def get(self, url, params=None, timeout=None):
        self.pedidos.append((url, params, timeout))
        r = self.respostas.pop(0)
        if isinstance(r, BaseException):
            raise r
        return r

    post = get


class RequestException(Exception):
    """Mesmo nome da base de erros do requests (o cliente reconhece pelo nome)."""


class TempoEsgotadoRequests(RequestException):
    pass


def cliente(*respostas, esperas=(2, 10, 30)):
    dormidas = []
    c = ClienteHTTP(timeout=7, esperas=esperas, dormir=dormidas.append,
                    sessao=SessaoFalsa(*respostas))
    return c, dormidas


def test_ok_devolve_json_com_timeout():
    c, dormidas = cliente(Resposta(200, {"a": 1}))
    assert c.get("https://graph.facebook.com/v21.0/1", {"access_token": TOKEN}) == {"a": 1}
    assert c.sessao.pedidos[0][2] == 7 and dormidas == []


def test_429_repete_com_espera_e_respeita_retry_after():
    c, dormidas = cliente(Resposta(429, headers={"Retry-After": "3"}),
                          Resposta(503), Resposta(200, {"ok": True}))
    assert c.get("https://x/v21.0/1", {"access_token": TOKEN}) == {"ok": True}
    assert dormidas == [3.0, 10]
    assert len(c.sessao.pedidos) == 3


def test_5xx_esgota_as_tentativas():
    c, dormidas = cliente(*[Resposta(500, {"error": {"message": f"falhou {TOKEN}"}})] * 4)
    with pytest.raises(ErroTemporario) as e:
        c.get("https://x/v21.0/1", {"access_token": TOKEN})
    assert dormidas == [2, 10, 30] and e.value.status == 500
    assert TOKEN not in str(e.value)


def test_queda_de_rede_repete_e_mascara_token():
    url = f"https://graph.facebook.com/v21.0/1/media?after=X&access_token={TOKEN}"
    falha = TempoEsgotadoRequests(f"HTTPSConnectionPool: Read timed out. (url: {url})")
    c, dormidas = cliente(falha, falha, esperas=(1,))
    with pytest.raises(ErroTemporario) as e:
        c.get(url)
    msg = str(e.value)
    assert "falha de rede" in msg and TOKEN not in msg and "***" in msg
    assert e.value.__cause__ is None and e.value.__context__ is None
    assert dormidas == [1]


def test_400_nao_repete_e_classifica():
    c, dormidas = cliente(Resposta(400, {"error": {"message": "(#100) metric bad",
                                                   "code": 100}}))
    with pytest.raises(ErroAPI) as e:
        c.get("https://x/v21.0/M/insights", {"access_token": TOKEN, "metric": "bad"})
    assert type(e.value) is ErroAPI and e.value.status == 400 and e.value.codigo == 100
    assert dormidas == []

    c, _ = cliente(Resposta(400, {"error": {"message": f"Invalid OAuth {TOKEN}", "code": 190}}))
    with pytest.raises(ErroNaoAutorizado) as e:
        c.get("https://x/v21.0/1", {"access_token": TOKEN})
    assert TOKEN not in str(e.value)

    c, _ = cliente(Resposta(403, {"error": {"code": 403, "message": "cota",
                                            "errors": [{"reason": "quotaExceeded"}]}}))
    with pytest.raises(ErroAPI) as e:
        c.get("https://www.googleapis.com/youtube/v3/channels", {"key": "AIzaQualquerCoisa"})
    assert not isinstance(e.value, ErroNaoAutorizado)


def test_ler_valores_aceita_values_e_total_value():
    assert ler_valores({"data": [
        {"name": "views", "values": [{"value": 10}]},
        {"name": "followers_count", "total_value": {"value": 5}},
        {"name": "quebrado", "values": [{"value": {"a": 1, "b": 2}}]}]}) == \
        {"views": 10, "followers_count": 5, "quebrado": 3}


def test_insights_todas_falham_nao_marca_o_tipo():
    class C:
        def get(self, url, params):
            raise ErroAPI("HTTP 400 mídia antiga", status=400)
    t = InsightsTolerante(C())
    assert t.buscar("u", ["reach", "views"], "FEED/IMAGE") == {}
    assert t.recusadas["FEED/IMAGE"] == set()
