"""Testes do reenvio_seguro (dormir falso, nada de rede)."""
import json
import sys
import types
from datetime import datetime, timedelta
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import reenvio_seguro as rs  # noqa: E402
from hpbase import FUSO  # noqa: E402  (o reenvio_seguro já pôs o hp_studio no caminho)

INICIO = datetime(2026, 9, 30, 18, 30, tzinfo=FUSO)
LEGENDA = ("GTA 6: o trailer 3 chegou ❤️🔥  tudo o que sabemos até agora sobre o mapa, "
           "os carros e a data de lançamento #gta6 #rockstar")
TOKEN = "FAKE_NAO_E_TOKEN_1"
TOKEN_TH = "FAKE_NAO_E_TOKEN_2"
ID_ITEM = "gta_2026-09-30_ig_reel_1830"      # convenção real (4.1): gta_<data>_<ig|th>_<tipo>_<HHMM>


@pytest.fixture(autouse=True)
def local_temporario(tmp_path, monkeypatch):
    local = tmp_path / "HypadoLocalReenvio"
    local.mkdir()
    monkeypatch.setenv("HP_LOCAL", str(local))
    monkeypatch.setenv("HP_DRIVE", str(tmp_path / "DriveReenvio"))
    return local


class Dormir:
    def __init__(self):
        self.esperas = []

    def __call__(self, s):
        self.esperas.append(s)


class Roteiro:
    """Função falsa que devolve (ou levanta) os resultados em ordem."""

    def __init__(self, *resultados):
        self.resultados = list(resultados)
        self.chamadas = []

    def __call__(self, *args):
        self.chamadas.append(args)
        r = self.resultados.pop(0) if self.resultados else None
        if isinstance(r, BaseException):
            raise r
        return r


class ErroHTTP(Exception):
    def __init__(self, status):
        super().__init__(f"HTTP {status}")
        self.status_code = status


class GraphFalso:
    def __init__(self, data):
        self.data = data
        self.pedidos = []

    def get(self, caminho, params=None):
        self.pedidos.append((caminho, dict(params or {})))
        return {"data": self.data}


def _midia(id_, legenda, ts):
    return {"id": id_, "caption": legenda, "timestamp": ts,
            "permalink": f"https://www.instagram.com/p/{id_}/"}


# ------------------------------------------------------------ publicar_com_reenvio
def test_sai_de_primeira():
    pub, conf, dormir = Roteiro("111"), Roteiro(), Dormir()
    rel = {}
    assert rs.publicar_com_reenvio(pub, conf, dormir=dormir, relatorio=rel) == "111"
    assert len(pub.chamadas) == 1 and conf.chamadas == [] and dormir.esperas == []
    assert rel["tentativas"] == 1 and rel["ja_tinha_saido"] is False


def test_tempo_esgotado_mas_ja_tinha_saido_nao_duplica():
    pub = Roteiro(TimeoutError("The read operation timed out"))
    conf = Roteiro({"id": "222", "permalink": "https://www.instagram.com/p/222/"})
    dormir, rel = Dormir(), {}
    assert rs.publicar_com_reenvio(pub, conf, dormir=dormir, relatorio=rel) == "222"
    assert len(pub.chamadas) == 1          # não publicou de novo
    assert dormir.esperas == [60]          # esperou 1 min antes de conferir
    assert rel["ja_tinha_saido"] is True


def test_tres_tempos_esgotados_e_a_quarta_sai():
    pub = Roteiro(TimeoutError(), ErroHTTP(502), rs.TempoEsgotado("sem resposta"), "444")
    conf, dormir, rel = Roteiro(None, None, None), Dormir(), {}
    assert rs.publicar_com_reenvio(pub, conf, dormir=dormir, relatorio=rel) == "444"
    assert len(pub.chamadas) == 4 and len(conf.chamadas) == 3
    assert dormir.esperas == [60, 300, 900]
    assert rel["tentativas"] == 4


def test_quatro_falhas_da_erro_final():
    pub = Roteiro(*[TimeoutError("timed out")] * 4)
    conf, dormir = Roteiro(None, None, None, None), Dormir()
    with pytest.raises(rs.ReenvioEsgotado) as e:
        rs.publicar_com_reenvio(pub, conf, dormir=dormir)
    assert e.value.tentativas == 4 and len(pub.chamadas) == 4
    assert dormir.esperas == [60, 300, 900, 60]  # + conferida final
    assert len(conf.chamadas) == 4


def test_quarta_falha_mas_conferida_final_acha_o_post():
    pub = Roteiro(*[TimeoutError()] * 4)
    conf = Roteiro(None, None, None, "999")
    assert rs.publicar_com_reenvio(pub, conf, dormir=Dormir()) == "999"


@pytest.mark.parametrize("erro", [ValueError("legenda inválida"), ErroHTTP(400),
                                  PermissionError("token vencido")])
def test_erro_que_nao_e_tempo_esgotado_sobe_na_hora(erro):
    pub, conf, dormir = Roteiro(erro), Roteiro(), Dormir()
    with pytest.raises(type(erro)):
        rs.publicar_com_reenvio(pub, conf, dormir=dormir)
    assert len(pub.chamadas) == 1 and conf.chamadas == [] and dormir.esperas == []


def test_erro_comum_depois_de_um_tempo_esgotado_tambem_sobe():
    pub, conf = Roteiro(TimeoutError(), ValueError("mídia recusada")), Roteiro(None)
    with pytest.raises(ValueError):
        rs.publicar_com_reenvio(pub, conf, dormir=Dormir())
    assert len(pub.chamadas) == 2


def test_modo_simular_nao_publica():
    pub, conf, dormir, rel = Roteiro("x"), Roteiro(), Dormir(), {}
    assert rs.publicar_com_reenvio(pub, conf, simular=True, dormir=dormir, relatorio=rel) is None
    assert pub.chamadas == [] and conf.chamadas == [] and dormir.esperas == []
    assert rel["simulado"] is True and "SIMULAR" in rel["eventos"][0]
    assert "1, 5, 15 min" in rel["eventos"][0]


def test_sem_conseguir_conferir_nao_republica_as_cegas():
    pub = Roteiro(TimeoutError(), "555")
    conf = Roteiro(RuntimeError("API fora do ar"), None)
    dormir = Dormir()
    assert rs.publicar_com_reenvio(pub, conf, dormir=dormir) == "555"
    assert len(pub.chamadas) == 2 and dormir.esperas == [60, 300]


def test_classifica_tempo_esgotado():
    class ReadTimeout(OSError):
        pass

    class Resp:
        status_code = 503

    class ComResposta(Exception):
        response = Resp()

    sim = [TimeoutError(), ReadTimeout("x"), ErroHTTP(503), ComResposta("x"),
           Exception("HTTPSConnectionPool: Read timed out."), Exception("HTTP 502 Bad Gateway"),
           rs.TempoEsgotado()]
    nao = [ValueError("x"), ErroHTTP(400), ErroHTTP(429), Exception("(#100) legenda")]
    assert all(rs.eh_tempo_esgotado(e) for e in sim)
    assert not any(rs.eh_tempo_esgotado(e) for e in nao)


# ------------------------------------------------------------ ja_publicado
def test_normalizar_legenda_ignora_espacos_e_variacoes_de_emoji():
    a = rs.normalizar_legenda("GTA 6 ❤️ chegou\n\n#gta6")
    b = rs.normalizar_legenda("GTA  6 ❤ chegou #gta6 ")
    assert a == b == "gta6❤chegou#gta6"
    assert len(rs.normalizar_legenda("x" * 300)) == 80


def test_ja_publicado_confere_legenda_e_horario():
    variante = LEGENDA.replace("❤️", "❤").replace("  ", " ") + " (texto extra depois dos 80)"
    cliente = GraphFalso([
        _midia("OUTRO", "Outro post qualquer", "2026-09-30T21:35:00+0000"),
        _midia("VELHO", LEGENDA, "2026-09-30T21:27:59+0000"),   # 18:27:59 < 18:28 (início − 2 min)
        _midia("NOVO", variante, "2026-09-30T21:28:30+0000"),   # 18:28:30 ≥ 18:28
    ])
    achado = rs.ja_publicado(cliente, "1784IG", LEGENDA, INICIO)
    assert achado["id"] == "NOVO" and achado["permalink"].endswith("/NOVO/")
    caminho, params = cliente.pedidos[0]
    assert caminho == "/1784IG/media"
    assert params == {"fields": "id,caption,timestamp,permalink", "limit": 5}
    # aceita epoch em segundos também
    assert rs.ja_publicado(cliente, "1784IG", LEGENDA, INICIO.timestamp())["id"] == "NOVO"
    # só o velho → não conta
    velho = GraphFalso([_midia("VELHO", LEGENDA, "2026-09-30T21:00:00+0000")])
    assert rs.ja_publicado(velho, "1784IG", LEGENDA, INICIO) is None
    assert rs.ja_publicado(cliente, "1784IG", "Legenda totalmente diferente", INICIO) is None


def test_ja_publicado_no_threads_usa_text():
    cliente = GraphFalso([{"id": "T1", "text": "Qual carro?", "timestamp": "2026-09-30T21:31:00+0000",
                           "permalink": "https://www.threads.net/t/T1"}])
    assert rs.ja_publicado(cliente, "26TH", "Qual  carro?", INICIO, rede="threads")["id"] == "T1"
    assert cliente.pedidos[0] == ("/26TH/threads",
                                  {"fields": "id,text,timestamp,permalink", "limit": 5})


# ------------------------------------------------------------ reenviar (fila)
def _item_na_fila(local, **extra):
    """Item no formato REAL da fila (4.1), em erros\\ depois de 2 tempos esgotados."""
    fila = local / "fila_api" / "erros"
    fila.mkdir(parents=True)
    item = {"id": ID_ITEM, "conta": "hpgta6", "rede": "instagram", "tipo": "reel",
            "arquivos": ["H:\\HypadoLocal\\upload\\30_09_2026_18h30_trailer_3.mp4"],
            "legenda": LEGENDA, "quando": "2026-09-30 18:30", "canal": "gta",
            "grupo_whatsapp": "HP | Comissão 🚀", "ultimo_erro": "HTTP 504: tempo esgotado",
            "tentativas": 2, "ig_id": "1784IG", **extra}
    arq = fila / f"{item['id']}.json"
    arq.write_text(json.dumps(item, ensure_ascii=False), encoding="utf-8")
    return item, arq


def _segredos(local, meta=True):
    seg = local / "segredos"
    seg.mkdir(exist_ok=True)
    (seg / "meta_tokens.txt").write_text(
        f"# tokens (4.3)\nIG_hpgta6={TOKEN}\nTH_@hpgta6 = \"{TOKEN_TH}\"\nIG_hp.carros=\n",
        encoding="utf-8")
    if meta:
        (seg / "meta_tokens_meta.json").write_text(json.dumps({"contas": {
            "IG_hpgta6": {"id": "1784IG", "username": "hpgta6"},
            "TH_hpgta6": {"id": "26TH", "username": "hpgta6"}}}), encoding="utf-8")
    return seg


def test_inicio_do_item_usa_quando_da_fila_real():
    assert rs.inicio_do_item({"quando": "2026-09-30 18:30"}) == INICIO
    assert rs.inicio_do_item({"quando": "2026-09-30T18:30"}) == INICIO
    preciso = {"quando": "2026-09-30 18:30", "tentativa_inicio": "2026-09-30T18:31:05-03:00"}
    assert rs.inicio_do_item(preciso) == datetime(2026, 9, 30, 18, 31, 5, tzinfo=FUSO)
    agora = datetime(2026, 10, 1, 12, 0, tzinfo=FUSO)
    assert rs.inicio_do_item({"quando": "ontem"}, agora) == agora - timedelta(hours=24)
    assert rs.inicio_do_item({}, agora) == agora - timedelta(hours=24)


def test_reenviar_simular_so_diz_o_que_faria(local_temporario):
    item, arq = _item_na_fila(local_temporario)
    antes = arq.read_text(encoding="utf-8")
    pub, falas = Roteiro("NOVO"), []
    r = rs.reenviar(item["id"], simular=True, cliente=GraphFalso([]), publicar_fn=pub,
                    saida=falas.append)
    assert r["acao"] == "republicaria" and pub.chamadas == []
    assert "SIMULAR" in falas[0] and "Republicaria" in falas[0]
    assert arq.read_text(encoding="utf-8") == antes

    saiu = GraphFalso([_midia("JA", LEGENDA, "2026-09-30T21:31:00+0000")])
    r = rs.reenviar(item["id"], simular=True, cliente=saiu, publicar_fn=pub, saida=falas.append)
    assert r == {"acao": "nada", "ja_tinha_saido": True, "id": "JA", "simulado": True}
    assert pub.chamadas == [] and arq.read_text(encoding="utf-8") == antes


def test_reenviar_so_republica_se_nao_saiu(local_temporario):
    item, arq = _item_na_fila(local_temporario)
    pub = Roteiro("NOVO123")
    r = rs.reenviar(item["id"], cliente=GraphFalso([]), publicar_fn=pub, dormir=Dormir(),
                    saida=None)
    assert r["acao"] == "republicado" and r["id"] == "NOVO123" and r["tentativas"] == 1
    assert pub.chamadas[0][0]["id"] == item["id"]  # recebeu o item da fila
    gravado = json.loads(arq.read_text(encoding="utf-8"))
    assert gravado["status"] == "publicado" and gravado["media_id"] == "NOVO123"
    assert gravado["reenvio"]["status"] == "publicado"


def test_reenviar_quando_ja_saiu_nao_publica(local_temporario):
    item, arq = _item_na_fila(local_temporario)
    pub = Roteiro("NAO_DEVIA")
    saiu = GraphFalso([_midia("JA", LEGENDA, "2026-09-30T21:31:00+0000")])
    r = rs.reenviar(item["id"], cliente=saiu, publicar_fn=pub, saida=None)
    assert r["acao"] == "nada" and pub.chamadas == []
    gravado = json.loads(arq.read_text(encoding="utf-8"))
    assert gravado["media_id"] == "JA" and gravado["reenvio"]["ja_tinha_saido"] is True


def test_cliente_da_fila_le_token_do_segredo_e_nunca_mostra(local_temporario, capsys):
    _segredos(local_temporario)
    cliente, ident = rs.cliente_e_id({"rede": "instagram", "conta": "hpgta6"})
    assert ident == "1784IG"                                     # id vem do meta_tokens_meta.json
    assert cliente.host == "https://graph.instagram.com" and cliente.versao == "v21.0"
    cliente_th, ident_th = rs.cliente_e_id({"rede": "threads", "canal": "gta"})   # canal -> handle
    assert ident_th == "26TH" and cliente_th.host == "https://graph.threads.net"
    assert cliente_th.versao == "v1.0" and cliente_th._token == TOKEN_TH

    class Sessao:
        def __init__(self):
            self.params = None

        def get(self, url, params=None, timeout=None):
            self.params = params
            raise OSError(f"falhou {url}?access_token={params['access_token']}")

    cliente._sessao = Sessao()
    with pytest.raises(rs.ErroGraph) as e:
        cliente.get("/1784IG/media", {"limit": 5})
    assert cliente._sessao.params["access_token"] == TOKEN  # o token vai para a API...
    assert TOKEN not in str(e.value) and "***" in str(e.value)  # ...mas nunca para o erro
    assert TOKEN not in repr(vars(e.value))
    assert cliente._sessao.params["access_token"] == TOKEN

    with pytest.raises(rs.SegredoAusente) as e:                  # linha vazia = sem token
        rs.cliente_e_id({"rede": "instagram", "conta": "hp.carros"})
    assert "IG_hp.carros" in str(e.value)
    with pytest.raises(rs.SegredoAusente, match="meta_tokens_meta"):   # token sem id
        rs.cliente_e_id({"rede": "threads", "conta": "hpgta6"}, meta={"contas": {}})
    assert rs.cliente_e_id({"rede": "threads", "conta": "hpgta6", "ig_id": "X"}, meta={})[1] == "X"
    with pytest.raises(ValueError, match="instagram ou threads"):
        rs.cliente_e_id({"rede": "facebook", "conta": "hpgta6"})
    saida = capsys.readouterr()
    assert TOKEN not in saida.out + saida.err and TOKEN_TH not in saida.out + saida.err


def _publicador_meta_falso(monkeypatch, chamadas, resultado=None, erro=None):
    """Um publicador_meta.py de mentira em sys.modules (o real só existe no PC)."""
    mod = types.ModuleType("publicador_meta")

    class ErroAPI(Exception):
        pass

    def publicar_item(item, toks, meta, simular=False):
        chamadas.append({"id": item["id"], "toks": toks, "meta": meta, "simular": simular})
        if erro:
            raise ErroAPI(erro)
        return resultado or {"media_id": "181", "permalink": "https://www.instagram.com/p/N/",
                             "publicado_em": "2026-09-30 18:35"}
    mod.ErroAPI, mod.publicar_item = ErroAPI, publicar_item
    mod.ler_tokens = lambda: {"IG_hpgta6": TOKEN}
    monkeypatch.setitem(sys.modules, "publicador_meta", mod)
    return mod


def test_achar_publicador_usa_o_adaptador(local_temporario, monkeypatch):
    _segredos(local_temporario)
    chamadas = []
    _publicador_meta_falso(monkeypatch, chamadas)
    item, _ = _item_na_fila(local_temporario)
    publicar = rs.achar_publicador()
    assert publicar(item) == {"media_id": "181", "permalink": "https://www.instagram.com/p/N/",
                              "publicado_em": "2026-09-30 18:35"}
    assert chamadas == [{"id": ID_ITEM, "toks": {"IG_hpgta6": TOKEN}, "simular": False,
                         "meta": {"contas": {"IG_hpgta6": {"id": "1784IG", "username": "hpgta6"},
                                             "TH_hpgta6": {"id": "26TH", "username": "hpgta6"}}}}]
    # simular: o real NUNCA é chamado (no PC o simular dele ainda sobe o arquivo)
    assert rs.achar_publicador(simular=True)(item)["media_id"] == "SIMULADO"
    assert len(chamadas) == 1
    # ErroAPI do publicador vira ErroPublicador sem token
    _publicador_meta_falso(monkeypatch, chamadas, erro=f"HTTP 400: access_token={TOKEN} vencido")
    with pytest.raises(rs.fa.ErroPublicador) as e:
        rs.achar_publicador()(item)
    assert TOKEN not in str(e.value) and "HTTP 400" in str(e.value)
    monkeypatch.setitem(sys.modules, "publicador_meta", types.ModuleType("publicador_meta"))
    with pytest.raises(RuntimeError, match="publicar_item"):
        rs.achar_publicador()


def test_reenviar_pelo_adaptador_sem_publicar_fn(local_temporario, monkeypatch):
    chamadas = []
    _publicador_meta_falso(monkeypatch, chamadas)
    item, arq = _item_na_fila(local_temporario)
    r = rs.reenviar(item["id"], cliente=GraphFalso([]), dormir=Dormir(), saida=None)
    assert r["acao"] == "republicado" and r["id"] == "181" and chamadas[0]["simular"] is False
    assert json.loads(arq.read_text(encoding="utf-8"))["media_id"] == "181"


def test_cli_reenviar_simular_e_item_inexistente(local_temporario, monkeypatch, capsys):
    item, _ = _item_na_fila(local_temporario)
    monkeypatch.setattr(rs, "cliente_e_id", lambda it, *a, **k: (GraphFalso([]), "1784IG"))
    assert rs.main(["reenviar", item["id"], "--simular"]) == 0
    assert "Republicaria" in capsys.readouterr().out
    assert rs.main(["reenviar", "nao-existe", "--simular"]) == 2


# ------------------------------------------------------------ story depois do post
def test_fila_story_apos_post(local_temporario):
    arq = rs.fila_story_apos_post("17900000001", "hpgta6", "gta",
                                  "https://www.instagram.com/reel/ABC/",
                                  INICIO, "Trailer 3 do GTA 6", "GTA 6")
    assert arq == local_temporario / "emulador" / "fila_story" / "17900000001.json"
    dados = json.loads(arq.read_text(encoding="utf-8"))
    assert {k: dados[k] for k in ("post_id", "conta", "canal", "link", "publicado_em", "titulo",
                                  "destaque", "status")} == {
        "post_id": "17900000001", "conta": "hpgta6", "canal": "gta",
        "link": "https://www.instagram.com/reel/ABC/", "publicado_em": "2026-09-30T18:30:00-03:00",
        "titulo": "Trailer 3 do GTA 6", "destaque": "GTA 6", "status": "pendente"}
    # chamar de novo não sobrescreve (nunca 2 stories do mesmo post)
    rs.fila_story_apos_post("17900000001", "hpgta6", "gta", "https://x", INICIO, "outro", None)
    assert json.loads(arq.read_text(encoding="utf-8"))["titulo"] == "Trailer 3 do GTA 6"
    with pytest.raises(ValueError):
        rs.fila_story_apos_post("", "hpgta6", "gta", "", INICIO, "t", None)


def test_cli_story(local_temporario, capsys):
    assert rs.main(["story", "179X", "--conta", "hp.carros", "--canal", "carros",
                    "--link", "https://www.instagram.com/p/X/",
                    "--publicado-em", "2026-09-30T12:00:00-03:00", "--titulo", "Carro"]) == 0
    assert (local_temporario / "emulador" / "fila_story" / "179X.json").exists()
