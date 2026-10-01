"""Fila REAL da API (4.1) com as fixtures do PC (tests/fixtures/pc_real): cada item passa por
montar_item -> gravar numa fila temporária -> ler_confirmacao; os erros dão a mensagem IDÊNTICA
ao _validar do publicador; limite_24h.json e publicador.log têm leitores; o adaptador do
publicador nunca chama com simular=True e nunca deixa token em mensagem."""
import io
import json
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from hpbase import FUSO, SegredoAusente
from hpbase import fila_api_pc as fa

PC_REAL = Path(__file__).resolve().parents[4] / "tests" / "fixtures" / "pc_real"
FAKE1, FAKE2 = "FAKE_NAO_E_TOKEN_1", "FAKE_NAO_E_TOKEN_2"
CAMPOS = ("id", "conta", "rede", "tipo", "arquivos", "legenda", "quando", "canal",
          "grupo_whatsapp", "titulo")


def sempre(_caminho):
    return True


def fixture(nome):
    return json.loads((PC_REAL / f"fila_api_{nome}.json").read_text(encoding="utf-8"))


def montar(d, existe=sempre, **troca):
    kw = dict(conta=d.get("conta"), rede=d["rede"], tipo=d["tipo"], arquivos=d["arquivos"],
              legenda=d.get("legenda", ""), quando=d["quando"], canal=d.get("canal"),
              titulo=d.get("titulo"), capa=d.get("capa"), id_=d["id"],
              grupo_whatsapp=d.get("grupo_whatsapp"), existe=existe)
    kw.update(troca)
    return fa.montar_item(**kw)


def igual_a_fixture(item, d):
    for k in CAMPOS:
        if k in d:
            assert item[k] == d[k], k
    assert set(item) <= set(d) | {"capa", "depende_de"}   # nada inventado além do real


def ok(**troca):
    base = dict(conta="hp.futebol", rede="instagram", tipo="feed", arquivos=["H:\\x\\a.jpg"],
                legenda="oi", quando="2026-10-01 12:00", existe=sempre)
    base.update(troca)
    return base


# --- conta, handle, token, id ---------------------------------------------------------------
def test_normalizar_conta_e_tabelas():
    assert fa.normalizar_conta("@HP.Futebol") == "hp.futebol"
    assert fa.normalizar_conta("futebol") == "hp.futebol" and fa.normalizar_conta("GTA") == "hpgta6"
    assert fa.normalizar_conta(None) == ""
    assert fa.CANAIS["carros"] == ("hp.carros", "HP | Carros 🏎️")
    assert fa.CONTA_CANAL["hp.destinos"] == "destinos" and len(fa.PERFIS) == 6


def test_handle_de_conta_ou_canal():
    assert fa.handle({"conta": "hp.futebol"}) == "hp.futebol"
    assert fa.handle({"canal": "futebol"}) == "hp.futebol"
    assert fa.handle({"canal": "gta"}) == "hpgta6"
    assert fa.handle({"conta": "@hpgta6", "canal": "futebol"}) == "hpgta6"   # conta vence


def test_chave_token():
    assert fa.chave_token(fixture("reel_pendente_gta")) == "IG_hpgta6"
    assert fa.chave_token(fixture("feitos_th_feed_futebol")) == "TH_hp.futebol"
    assert fa.chave_token({"canal": "carros", "rede": "threads"}) == "TH_hp.carros"
    with pytest.raises(fa.ErroFilaApi, match="instagram ou threads"):
        fa.chave_token({"conta": "hp.carros", "rede": "facebook"})


def test_token_do_item_so_devolve_a_quem_pediu_e_nunca_mostra(capsys):
    pedidos = []

    def ler(chave):
        pedidos.append(chave)
        return FAKE1 if chave == "IG_hpgta6" else None
    item = fixture("reel_pendente_gta")
    saida, erros = io.StringIO(), io.StringIO()
    with redirect_stdout(saida), redirect_stderr(erros):
        assert fa.token_do_item(item, ler) == FAKE1
        with pytest.raises(SegredoAusente) as e:
            fa.token_do_item({**item, "rede": "threads"}, ler)
    assert pedidos == ["IG_hpgta6", "TH_hpgta6"]
    assert "TH_hpgta6" in str(e.value) and FAKE1 not in str(e.value) and FAKE1 not in repr(e.value)
    assert FAKE1 not in saida.getvalue() + erros.getvalue() + capsys.readouterr().out

    def quebra(chave):
        raise KeyError(chave)
    with pytest.raises(SegredoAusente):
        fa.token_do_item(item, quebra)


def test_leitor_de_tokens_le_como_o_publicador(tmp_path, capsys):
    (tmp_path / "meta_tokens.txt").write_text(
        f'# tokens\nIG_@HPGTA6 = "{FAKE1}"\nTH_hp.futebol={FAKE2}\nIG_vazio=\nlixo sem igual\n',
        encoding="utf-8")
    ler = fa.leitor_de_tokens(pasta=tmp_path)
    assert ler("ig_hpgta6") == FAKE1 and ler("IG_@hpgta6") == FAKE1
    assert ler("TH_hp.futebol") == FAKE2
    assert ler("IG_vazio") is None and ler("IG_outro") is None
    assert fa.leitor_de_tokens(pasta=tmp_path / "nao")("IG_hpgta6") is None
    assert FAKE1 not in capsys.readouterr().out


def test_id_da_conta_e_ler_meta_sem_regravar(tmp_path):
    meta = {"contas": {"IG_hpgta6": {"id": 17841400000000001, "username": "hpgta6"},
                       "TH_hp.futebol": {"id": "26000000000000002"}},
            "ultima_checagem_renovacao": "2026-09-30T10:00"}
    assert fa.id_da_conta("IG_hpgta6", meta) == "17841400000000001"
    assert fa.id_da_conta("ig_@HPGTA6", meta) == "17841400000000001"
    assert fa.id_da_conta("TH_hp.futebol", meta) == "26000000000000002"
    assert fa.id_da_conta("IG_hp.carros", meta) is None and fa.id_da_conta("IG_x", {}) is None
    arq = tmp_path / "meta_tokens_meta.json"
    texto = json.dumps(meta, indent=1)
    arq.write_text(texto, encoding="utf-8")
    assert fa.ler_meta(tmp_path) == meta
    assert arq.read_text(encoding="utf-8") == texto      # só leitura
    assert fa.ler_meta(tmp_path / "nao") == {}


def test_inicio_aceita_T_e_hora_de_brasilia_sem_fuso():
    alvo = datetime(2026, 10, 2, 12, 0)
    assert fa.inicio({"quando": "2026-10-02 12:00"}) == alvo
    assert fa.inicio({"quando": "2026-10-02T12:00"}) == alvo
    assert fa.inicio({"quando": "2026-10-02T12:00:00-03:00"}) == alvo and alvo.tzinfo is None
    with pytest.raises(fa.ErroFilaApi, match="campo 'quando' faltando"):
        fa.inicio({"quando": ""})
    with pytest.raises(fa.ErroFilaApi):
        fa.inicio({"quando": "02/10/2026 12:00"})


def test_id_padrao_pelas_convencoes():
    q = datetime(2026, 10, 1, 12, 0)
    assert fa.id_padrao("gta", "threads", "texto", q) == "gta_2026-10-01_th_texto_1200"
    assert fa.id_padrao("gta", "instagram", "reel", datetime(2026, 10, 2, 12, 0)) == "gta_2026-10-02_ig_reel_1200"
    assert fa.id_padrao("carros", "instagram", "carrossel", datetime(2026, 9, 30, 23, 15),
                        slug_="novo-bmw-serie-3") == "carros_2026-09-30_2315_novo-bmw-serie-3_ig_carrossel"
    assert fa.id_padrao("carros", "threads", "texto", q, lote="lote-01", n=3) == "carros_th_2026-10-01_1200_lote-01_3"
    assert fa.slug("O novo BMW Série 3 chegou!") == "o-novo-bmw-serie-3-chegou"
    item = fa.montar_item(**ok(titulo="Jorge Jesus: \"Quem decide sou eu\"", quando="2026-09-30 23:20"))
    assert item["id"] == "futebol_2026-09-30_2320_jorge-jesus-quem-decide-sou-eu_ig_feed"


# --- os itens reais de 4.1: montar_item -> gravar -> ler_confirmacao -------------------------
def test_reel_pendente_gta(tmp_path):
    d = fixture("reel_pendente_gta")
    item = montar(d)
    igual_a_fixture(item, d)
    assert montar(d, id_=None)["id"] == d["id"]           # id padrão do GTA bate com o real
    assert fa.gravar_item(item, tmp_path) == tmp_path / f"{d['id']}.json"
    c = fa.ler_confirmacao(d["id"], tmp_path)
    assert c["estado"] == "pendente" and c["pasta"] == "raiz" and c["link"] is None


def test_feitos_ig_feed_futebol(tmp_path):
    d = fixture("feitos_ig_feed_futebol")
    item = montar(d)
    igual_a_fixture(item, d)
    assert montar(d, id_=None, slug_="jj-quem-decide")["id"] == d["id"]
    fa.gravar_item(d, tmp_path, "feitos")
    c = fa.ler_confirmacao(d["id"], tmp_path)
    assert c == {"estado": "no_ar", "link": "https://www.instagram.com/p/Dd70ZtCFSND/",
                 "erro": None, "publicado_em": "2026-09-30 23:18", "media_id": "18100000000000001",
                 "pasta": "feitos"}


def test_feitos_ig_carrossel_carros_7_laminas(tmp_path):
    d = fixture("feitos_ig_carrossel_carros")
    item = montar(d)
    igual_a_fixture(item, d)
    assert len(item["arquivos"]) == 7
    fa.gravar_item(d, tmp_path, "feitos")
    c = fa.ler_confirmacao(d["id"], tmp_path)
    assert c["estado"] == "no_ar" and c["media_id"] == "18100000000000002"
    assert c["link"] == "https://www.instagram.com/p/Dd7ytwrlQye/"


def test_feitos_th_feed_futebol(tmp_path):
    d = fixture("feitos_th_feed_futebol")
    item = montar(d)
    igual_a_fixture(item, d)
    assert fa.chave_token(item) == "TH_hp.futebol" and len(item["legenda"]) <= 500
    fa.gravar_item(d, tmp_path, "feitos")
    c = fa.ler_confirmacao(d["id"], tmp_path)
    assert c["estado"] == "no_ar" and c["link"] == "https://www.threads.com/@hp.futebol/post/Dd70cgAlbPX"
    assert c["publicado_em"] == "2026-09-30 23:18"


def test_feitos_ig_story_futebol(tmp_path):
    d = fixture("feitos_ig_story_futebol")
    item = montar(d)
    igual_a_fixture(item, d)
    assert item["legenda"] == ""                                    # story sem legenda é válido
    assert fa.post_que_falta(item, tmp_path) is None                # story avulso: sem irmão
    fa.gravar_item(d, tmp_path, "feitos")
    c = fa.ler_confirmacao(d["id"], tmp_path)
    assert c["estado"] == "no_ar"
    assert c["link"] == "https://www.instagram.com/stories/hp.futebol/3990000000000000001"


def test_erro_th_carrossel_mensagem_identica(tmp_path):
    d = fixture("erros_th_carrossel_carros")
    with pytest.raises(fa.ErroFilaApi) as e:
        montar(d, existe=lambda p: not p.endswith("01.jpg"))
    assert str(e.value) == d["erro"]
    assert str(e.value) == ("arquivo não existe: H:\\HypadoLocal\\canais\\carros\\lancamentos\\"
                            "2026-10-01_0930_bmw-serie-3-o-que-mudou\\01.jpg")
    igual_a_fixture(montar(d), d)                                   # com a mídia gerada, passa
    fa.gravar_item(d, tmp_path, "erros")
    c = fa.ler_confirmacao(d["id"], tmp_path)
    assert c["estado"] == "erro" and c["erro"] == d["erro"] and c["pasta"] == "erros"
    assert c["link"] is None and c["tentativas"] is None


def test_erro_de_rede_ultimo_erro_e_tentativas(tmp_path):
    d = {**fixture("reel_pendente_gta"), "ultimo_erro": "HTTP 500: {\"message\": \"fora do ar\"}",
         "tentativas": 2}
    fa.gravar_item(d, tmp_path, "erros")
    c = fa.ler_confirmacao(d["id"], tmp_path)
    assert c["estado"] == "erro" and c["erro"].startswith("HTTP 500") and c["tentativas"] == 2
    # 1 falha só: fica na raiz com ultimo_erro (ainda pendente)
    fa.gravar_item({**d, "tentativas": 1}, tmp_path / "outra")
    c = fa.ler_confirmacao(d["id"], tmp_path / "outra")
    assert c["estado"] == "pendente" and c["tentativas"] == 1 and c["erro"].startswith("HTTP 500")


def test_texto_th_gta(tmp_path):
    d = fixture("texto_th_gta")
    item = montar(d)
    igual_a_fixture(item, d)
    assert item["arquivos"] == [] and montar(d, id_=None)["id"] == d["id"]
    with pytest.raises(fa.ErroFilaApi, match="^post de texto sem legenda$"):
        montar(d, legenda="")
    fa.gravar_item(item, tmp_path)
    assert fa.ler_confirmacao(d["id"], tmp_path)["estado"] == "pendente"


def test_story_clicavel_parqueado(tmp_path):
    d = fixture("story_clicavel_parqueado")
    item = montar(d)
    igual_a_fixture(item, d)
    assert "parqueado_em" not in item and "origem_pasta" not in item
    fa.gravar_item(d, tmp_path, "story_clicavel")
    c = fa.ler_confirmacao(d["id"], tmp_path)
    assert c["estado"] == "pendente" and c["pasta"] == "story_clicavel"


def test_ler_confirmacao_nas_outras_pastas(tmp_path):
    d = fixture("reel_pendente_gta")
    assert fa.ler_confirmacao(d["id"], tmp_path)["estado"] == "desconhecido"
    assert fa.ler_confirmacao(d["id"], tmp_path / "nao_existe")["estado"] == "desconhecido"
    fa.gravar_item(d, tmp_path, "reserva_largada")
    c = fa.ler_confirmacao(d["id"], tmp_path)
    assert c["estado"] == "pendente" and c["pasta"] == "reserva_largada"
    fa.gravar_item(d, tmp_path / "removidos" / "api_bloqueada_2026-09-29")
    (tmp_path / "reserva_largada" / f"{d['id']}.json").unlink()
    c = fa.ler_confirmacao(d["id"], tmp_path)
    assert c["estado"] == "erro" and "api_bloqueada_2026-09-29" in c["erro"]
    assert c["pasta"] == "removidos/api_bloqueada_2026-09-29"
    # feitos vence tudo; JSON quebrado não derruba
    (tmp_path / "feitos").mkdir()
    (tmp_path / "feitos" / f"{d['id']}.json").write_text("{quebrado", encoding="utf-8")
    assert fa.ler_confirmacao(d["id"], tmp_path)["estado"] == "erro"
    fa.gravar_item({**d, "status": "no_ar", "resultado": {"permalink": "https://i/p/1"}}, tmp_path, "feitos")
    assert fa.ler_confirmacao(d["id"], tmp_path)["link"] == "https://i/p/1"


# --- as mensagens do _validar e as regras por tipo -----------------------------------------
def test_rede_facebook_nao_entra_por_esta_fila():
    with pytest.raises(fa.ErroFilaApi) as e:
        fa.montar_item(**ok(rede="facebook"))
    assert str(e.value) == "rede tem que ser instagram ou threads (Facebook continua pelo Business Suite)"
    with pytest.raises(fa.ErroFilaApi, match="instagram ou threads"):
        fa.montar_item(**ok(rede="youtube"))


def test_campo_quando_faltando():
    for q in ("", None):
        with pytest.raises(fa.ErroFilaApi) as e:
            fa.montar_item(**ok(quando=q))
        assert str(e.value) == "campo 'quando' faltando"
    with pytest.raises(fa.ErroFilaApi, match="does not match format"):
        fa.montar_item(**ok(quando="01/10/2026 12:00"))


def test_conta_desconhecida_e_canal_no_lugar_da_conta():
    with pytest.raises(fa.ErroFilaApi) as e:
        fa.montar_item(**ok(conta="fulano"))
    assert str(e.value) == "conta desconhecida: fulano"
    item = fa.montar_item(**ok(conta=None, canal="futebol"))
    assert item["conta"] == "hp.futebol" and item["canal"] == "futebol"
    item = fa.montar_item(**ok(conta="@HP.Carros", canal=None))
    assert item["conta"] == "hp.carros" and item["canal"] == "carros"
    assert item["grupo_whatsapp"] == "HP | Carros 🏎️"


def test_carrossel_2_a_10_no_instagram_e_2_a_20_no_threads():
    jpg = [f"H:\\x\\{i:02d}.jpg" for i in range(1, 22)]
    with pytest.raises(fa.ErroFilaApi) as e:
        fa.montar_item(**ok(tipo="carrossel", arquivos=jpg[:1]))
    assert str(e.value) == "carrossel precisa de 2 a 10 arquivos (veio 1)"
    with pytest.raises(fa.ErroFilaApi, match=r"carrossel precisa de 2 a 10 arquivos \(veio 11\)"):
        fa.montar_item(**ok(tipo="carrossel", arquivos=jpg[:11]))
    assert len(fa.montar_item(**ok(tipo="carrossel", arquivos=jpg[:10]))["arquivos"]) == 10
    assert len(fa.montar_item(**ok(rede="threads", tipo="carrossel", arquivos=jpg[:20]))["arquivos"]) == 20
    with pytest.raises(fa.ErroFilaApi) as e:
        fa.montar_item(**ok(rede="threads", tipo="carrossel", arquivos=jpg[:21]))
    assert str(e.value) == "carrossel precisa de 2 a 20 arquivos (veio 21)"


def test_limites_de_legenda():
    with pytest.raises(fa.ErroFilaApi) as e:
        fa.montar_item(**ok(legenda="x" * 2201))
    assert str(e.value) == "legenda com 2201 caracteres (máx. 2200 no Instagram)"
    assert len(fa.montar_item(**ok(legenda="x" * 2200))["legenda"]) == 2200
    with pytest.raises(fa.ErroFilaApi) as e:
        fa.montar_item(**ok(rede="threads", legenda="y" * 501))
    assert str(e.value) == "texto com 501 caracteres (máx. 500 no Threads)"
    assert fa.montar_item(**ok(rede="threads", legenda="y" * 500))["rede"] == "threads"


def test_feed_reel_e_story():
    with pytest.raises(fa.ErroFilaApi, match="^feed = exatamente 1 imagem"):
        fa.montar_item(**ok(arquivos=["H:\\x\\a.jpg", "H:\\x\\b.jpg"]))
    with pytest.raises(fa.ErroFilaApi, match="^feed = exatamente 1 imagem"):
        fa.montar_item(**ok(arquivos=["H:\\x\\a.mp4"]))
    with pytest.raises(fa.ErroFilaApi) as e:
        fa.montar_item(**ok(tipo="reel", arquivos=["H:\\x\\a.jpg"]))
    assert str(e.value) == "reel = exatamente 1 vídeo"
    with pytest.raises(fa.ErroFilaApi, match="^reel = exatamente 1 vídeo$"):
        fa.montar_item(**ok(tipo="reel", arquivos=[]))
    assert fa.montar_item(**ok(tipo="reel", arquivos=["H:\\x\\a.mov"], capa="H:\\x\\capa.jpg"))["capa"] == "H:\\x\\capa.jpg"
    with pytest.raises(fa.ErroFilaApi) as e:
        fa.montar_item(**ok(tipo="story", arquivos=["H:\\x\\a.jpg", "H:\\x\\b.jpg"]))
    assert str(e.value) == "story = exatamente 1 arquivo"
    assert fa.montar_item(**ok(tipo="story", arquivos=["H:\\x\\a.mp4"], legenda=""))["tipo"] == "story"


def test_regras_do_texto_e_tipo_invalido():
    with pytest.raises(fa.ErroFilaApi, match="^post de texto sem legenda$"):
        fa.montar_item(**ok(rede="threads", tipo="texto", arquivos=[], legenda="  "))
    with pytest.raises(fa.ErroFilaApi, match="só no Threads"):
        fa.montar_item(**ok(tipo="texto", arquivos=[]))
    with pytest.raises(fa.ErroFilaApi, match="não leva arquivo"):
        fa.montar_item(**ok(rede="threads", tipo="texto"))
    with pytest.raises(fa.ErroFilaApi, match="tipo tem que ser"):
        fa.montar_item(**ok(tipo="video"))


def test_arquivo_relativo_resolve_contra_a_pasta_da_fila(tmp_path):
    (tmp_path / "a.jpg").write_bytes(b"x")
    item = fa.montar_item(**ok(arquivos=["a.jpg"], existe=None, pasta_fila=tmp_path))
    assert item["arquivos"] == [str(tmp_path / "a.jpg")]
    with pytest.raises(fa.ErroFilaApi) as e:
        fa.montar_item(**ok(arquivos=["b.jpg"], existe=None, pasta_fila=tmp_path))
    assert str(e.value) == f"arquivo não existe: {tmp_path / 'b.jpg'}"
    win = "H:\\HypadoLocal\\upload\\a.jpg"                      # absoluto do Windows fica como está
    assert fa.montar_item(**ok(arquivos=[win], pasta_fila=tmp_path))["arquivos"] == [win]
    with pytest.raises(fa.ErroFilaApi) as e:                     # capa também tem que existir
        fa.montar_item(**ok(tipo="reel", arquivos=["H:\\x\\a.mp4"], capa="H:\\x\\capa.jpg",
                            existe=lambda p: not p.endswith("capa.jpg")))
    assert str(e.value) == "arquivo não existe: H:\\x\\capa.jpg"


def test_quando_aceita_T_datetime_e_converte_fuso():
    assert fa.montar_item(**ok(quando="2026-10-02T12:00"))["quando"] == "2026-10-02 12:00"
    assert fa.montar_item(**ok(quando=datetime(2026, 10, 2, 12, 0)))["quando"] == "2026-10-02 12:00"
    utc = datetime(2026, 10, 2, 15, 0, tzinfo=timezone.utc)      # 15:00 UTC = 12:00 em Brasília
    assert fa.montar_item(**ok(quando=utc))["quando"] == "2026-10-02 12:00"
    assert fa.montar_item(**ok(quando=datetime(2026, 10, 2, 12, 0, tzinfo=FUSO)))["quando"] == "2026-10-02 12:00"


# --- regras do rodar(): story espera o post, hora e vencimento ----------------------------
def test_post_que_falta_story_irmao(tmp_path):
    story = fixture("story_clicavel_parqueado")                   # carros_..._hb20-x-onix_ig_story
    irmao = story["id"][: -len("_ig_story")] + "_ig_carrossel"
    assert fa.post_que_falta(story, tmp_path) is None             # irmão em lugar nenhum: story avulso
    fa.gravar_item({"id": irmao}, tmp_path)                        # irmão esperando na raiz
    assert fa.post_que_falta(story, tmp_path) == irmao
    (tmp_path / f"{irmao}.json").rename((tmp_path / "erros").mkdir() or tmp_path / "erros" / f"{irmao}.json")
    assert fa.post_que_falta(story, tmp_path) == irmao            # em erros\\ também segura
    fa.gravar_item({"id": irmao}, tmp_path, "feitos")
    assert fa.post_que_falta(story, tmp_path) is None             # saiu: libera
    outro = {**story, "depende_de": "gta_2026-10-01_th_texto_1200"}
    fa.gravar_item({"id": "gta_2026-10-01_th_texto_1200"}, tmp_path, "reserva_largada")
    assert fa.post_que_falta(outro, tmp_path) == "gta_2026-10-01_th_texto_1200"


def test_chegou_a_hora_e_vencido():
    item = {"quando": "2026-10-02 12:00"}
    assert fa.chegou_a_hora(item, datetime(2026, 10, 2, 11, 58))
    assert not fa.chegou_a_hora(item, datetime(2026, 10, 2, 11, 57, 59))
    assert not fa.esta_vencido(item, datetime(2026, 10, 3, 0, 0))
    assert fa.esta_vencido(item, datetime(2026, 10, 3, 0, 0, 1))
    assert not fa.esta_vencido({**item, "publicar_mesmo_atrasado": True}, datetime(2026, 10, 4, 0, 0))
    assert fa.esta_vencido(item, datetime(2026, 10, 2, 13, 1), atraso_max=timedelta(hours=1))
    assert fa.mensagem_vencido() == "venceu há mais de 12:00:00 e não saiu (decidir se ainda vale)"


# --- limite_24h.json e publicador.log ------------------------------------------------------
def test_ler_limite_24h(tmp_path):
    (tmp_path / "limite_24h.json").write_text((PC_REAL / "fila_api_limite_24h.json").read_text(encoding="utf-8"),
                                              encoding="utf-8")
    lim = fa.ler_limite_24h(tmp_path)
    assert lim["IG_hp.futebol"] == ["2026-09-30 11:00", "2026-09-30 11:08", "2026-09-30 23:18"]
    assert lim["IG_hpgta6"] == []
    agora = datetime(2026, 10, 1, 11, 5)
    assert fa.publicacoes_24h(lim, "IG_hp.futebol", agora) == 2          # 11:00 de ontem já caiu
    assert fa.publicacoes_24h(lim, "ig_@hp.futebol", datetime(2026, 9, 30, 23, 30)) == 3
    assert fa.publicacoes_24h(lim, "TH_hp.carros", agora) == 1 and fa.publicacoes_24h(lim, "IG_hpgta6", agora) == 0
    assert not fa.no_limite(lim, "IG_hp.futebol", agora)
    cheio = {"IG_hp.futebol": ["2026-10-01 10:00"] * 100}
    assert fa.no_limite(cheio, "IG_hp.futebol", agora) and not fa.no_limite(cheio, "TH_hp.futebol", agora)
    assert fa.ler_limite_24h(tmp_path / "nao") == {}


def test_ler_log_do_publicador(tmp_path):
    evs = fa.ler_log(PC_REAL / "fila_api_publicador.log")
    assert [e["evento"] for e in evs] == ["hospedado", "no_ar", "publicando", "no_ar", "invalido"]
    assert evs[0]["quando"] == datetime(2026, 9, 30, 23, 4, 38) and evs[0]["servico"] == "uguu"
    assert evs[1]["id"] == "carros_2026-09-30_2315_novo-bmw-serie-3_th_carrossel"
    assert evs[1]["link"] == "https://www.threads.com/@hp.carros/post/Dd7y-0jlRrY"
    assert evs[2] == {"quando": datetime(2026, 9, 30, 23, 18, 8), "evento": "publicando",
                      "texto": evs[2]["texto"], "id": "futebol_2026-09-30_2320_jj-quem-decide_ig_feed",
                      "rede": "instagram", "tipo": "feed", "conta": "hp.futebol", "marcado": "2026-09-30 23:20"}
    assert evs[3]["link"] == "https://www.instagram.com/p/Dd70ZtCFSND/"
    assert evs[4]["id"] == "carros_2026-10-01_0930_bmw-serie-3-o-que-mudou_ig_carrossel"
    assert evs[4]["erro"] == fixture("erros_th_carrossel_carros")["erro"]
    (tmp_path / "publicador.log").write_text("linha sem data\n2026-10-01 10:00:00 oi\n", encoding="utf-8")
    assert [e["evento"] for e in fa.ler_log(tmp_path)] == ["outro"]       # pela pasta da fila
    assert fa.ler_log(tmp_path / "nao.log") == []


# --- adaptador do publicador real -------------------------------------------------------------
class ErroAPI(Exception):       # mesmo NOME da classe do publicador_meta (duck typing)
    pass


def test_publicador_adaptado_em_simulacao_nao_chama_nada():
    def publicar_item(*a, **k):
        raise AssertionError("chamou o publicador real em simulação")
    publicar = fa.publicador_adaptado(publicar_item, simular=True, agora=datetime(2026, 10, 1, 12, 0))
    assert publicar(fixture("reel_pendente_gta")) == {"media_id": "SIMULADO", "permalink": "https://simulado",
                                                      "publicado_em": "2026-10-01 12:00"}
    assert publicar({"id": "x"})["publicado_em"] == "2026-10-01 12:00"


def test_publicador_adaptado_real_nunca_com_simular_true(capsys):
    chamadas, lidos = [], []

    def publicar_item(item, toks, meta, simular=False):
        chamadas.append((item["id"], toks, meta, simular))
        return {"media_id": "181", "permalink": "https://www.instagram.com/p/X/",
                "publicado_em": "2026-10-01 12:01", "extra": 1}

    def ler_tokens():
        lidos.append(1)
        return {"IG_hpgta6": FAKE1}
    publicar = fa.publicador_adaptado(publicar_item, ler_tokens=ler_tokens, meta={"contas": {}})
    item = fixture("reel_pendente_gta")
    assert publicar(item) == {"media_id": "181", "permalink": "https://www.instagram.com/p/X/",
                              "publicado_em": "2026-10-01 12:01"}
    assert chamadas == [(item["id"], {"IG_hpgta6": FAKE1}, {"contas": {}}, False)]
    publicar(item)
    assert len(lidos) == 2                                       # token lido só na hora de usar
    assert FAKE1 not in capsys.readouterr().out


def test_publicador_adaptado_limite_erroapi_e_token_nunca_na_mensagem():
    toks = {"IG_hpgta6": FAKE1}

    def limite(item, toks, meta, simular=False):
        return "limite"
    with pytest.raises(fa.LimiteDaConta, match="IG_hpgta6"):
        fa.publicador_adaptado(limite, ler_tokens=toks)(fixture("reel_pendente_gta"))

    def erro_api(item, toks, meta, simular=False):
        raise ErroAPI(f"HTTP 400: token {FAKE1} inválido access_token={FAKE1}")
    with pytest.raises(fa.ErroPublicador) as e:
        fa.publicador_adaptado(erro_api, ler_tokens=lambda: toks)(fixture("reel_pendente_gta"))
    assert FAKE1 not in str(e.value) and "***" in str(e.value) and "HTTP 400" in str(e.value)
    assert e.value.__cause__ is None and e.value.__suppress_context__   # o ErroAPI original não vaza
    assert isinstance(e.value, fa.ErroPublicador) and not isinstance(e.value, fa.LimiteDaConta)

    def tempo(item, toks, meta, simular=False):
        raise TimeoutError("timed out")
    with pytest.raises(TimeoutError):                            # o que não é ErroAPI sobe como veio
        fa.publicador_adaptado(tempo, ler_tokens=toks)(fixture("reel_pendente_gta"))

    def estranho(item, toks, meta, simular=False):
        return "ok"
    with pytest.raises(fa.ErroPublicador, match="inesperada"):
        fa.publicador_adaptado(estranho, ler_tokens=toks)(fixture("reel_pendente_gta"))


def test_gravar_item_e_atomico_e_em_subpasta(tmp_path):
    item = fa.montar_item(**ok())
    p = fa.gravar_item(item, tmp_path, "feitos")
    assert p == tmp_path / "feitos" / f"{item['id']}.json"
    assert json.loads(p.read_text(encoding="utf-8")) == item
    assert not list(tmp_path.glob("**/.tmp_*"))
    assert list(item) == ["id", "conta", "rede", "tipo", "arquivos", "legenda", "quando", "canal",
                          "grupo_whatsapp"]                        # ordem dos campos de 4.1
