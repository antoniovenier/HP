"""Testes do espelho local do banco do painel (scripts/painel/espelho_banco.py)."""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

PASTA = Path(__file__).resolve().parents[1] / "painel"
if str(PASTA) not in sys.path:
    sys.path.insert(0, str(PASTA))

import espelho_banco as eb  # noqa: E402


@pytest.fixture(autouse=True)
def _raizes(tmp_path, monkeypatch):
    """Nada toca no H: nem no G: (vale mesmo sem o conftest do app)."""
    monkeypatch.setenv("HP_LOCAL", str(tmp_path / "HypadoLocal"))
    monkeypatch.setenv("HP_DRIVE", str(tmp_path / "Drive"))


class Relogio:
    def __init__(self):
        self.n = 0

    def __call__(self) -> str:
        self.n += 1
        return f"2026-09-30T10:{self.n:02d}:00-03:00"


@pytest.fixture
def banco(tmp_path):
    b = eb.EspelhoBanco(tmp_path / "espelho.sqlite", relogio=Relogio())
    yield b
    b.fechar()


def test_caminho_padrao_fica_em_hp_local_app(tmp_path):
    with eb.EspelhoBanco() as b:
        b.set("canais", "gta", {"nome": "GTA 6 | HP"})
    assert (tmp_path / "HypadoLocal" / "app" / "painel_espelho.sqlite").exists()
    # tabela com as colunas combinadas
    con = sqlite3.connect(tmp_path / "HypadoLocal" / "app" / "painel_espelho.sqlite")
    cols = [c[1] for c in con.execute("PRAGMA table_info(docs)")]
    con.close()
    assert cols == ["colecao", "doc_id", "dados", "atualizado_em", "versao"]


def test_crud_basico(banco):
    r = banco.set("canais", "gta", {"nome": "GTA 6 | HP", "status": "ok"})
    assert r == {"id": "gta", "versao": 1, "mudou": True}
    assert banco.get("canais", "gta") == {"nome": "GTA 6 | HP", "status": "ok"}
    assert banco.get("canais", "nao_existe") is None

    banco.update("canais", "gta", {"status": "atencao", "prontos": 3})
    assert banco.get("canais", "gta") == {"nome": "GTA 6 | HP", "status": "atencao", "prontos": 3}
    assert banco.registro("canais", "gta")["versao"] == 2

    banco.set("canais", "futebol", {"nome": "Futebol | HP"})
    assert [r["id"] for r in banco.list("canais")] == ["futebol", "gta"]
    assert [r["id"] for r in banco.list("canais", limite=1, apos="futebol")] == ["gta"]

    assert banco.delete("canais", "gta") is True
    assert banco.delete("canais", "gta") is False
    assert banco.get("canais", "gta") is None


def test_documento_pode_ser_texto_ou_lista(banco):
    banco.set("avatares", "gta", "data:image/webp;base64,AAAA")
    banco.set("config", "dias", ["2026-09-30", "2026-10-01"])
    assert banco.get("avatares", "gta").startswith("data:image")
    assert banco.get("config", "dias") == ["2026-09-30", "2026-10-01"]


def test_set_igual_e_idempotente(banco):
    banco.set("canais", "gta", {"a": 1, "b": [1, 2]})
    antes = banco.registro("canais", "gta")
    r = banco.set("canais", "gta", {"b": [1, 2], "a": 1})  # mesma coisa, outra ordem
    assert r["mudou"] is False
    assert banco.registro("canais", "gta") == antes
    banco.update("canais", "gta", {"a": 1})
    assert banco.registro("canais", "gta")["versao"] == 1


def test_update_raso_e_profundo(banco):
    banco.set("canais", "gta", {"redes": {"instagram": {"seguidores": 10, "views": 5}}})
    banco.update("canais", "gta", {"redes": {"instagram": {"seguidores": 12}}}, profundo=True)
    assert banco.get("canais", "gta")["redes"]["instagram"] == {"seguidores": 12, "views": 5}
    banco.update("canais", "gta", {"redes": {"tiktok": {}}})
    assert banco.get("canais", "gta")["redes"] == {"tiktok": {}}
    with pytest.raises(eb.ErroEspelho):
        banco.update("canais", "gta", ["nao", "e", "objeto"])  # type: ignore[arg-type]
    with pytest.raises(eb.ErroEspelho):
        banco.update("canais", "novo", {"x": 1}, criar=False)


def test_query_filtro_operadores_e_ordem(banco):
    banco.set("agenda", "a", {"hora": "09:00", "status": "postado", "redes": ["instagram"]})
    banco.set("agenda", "b", {"hora": "12:30", "status": "agendado", "redes": ["tiktok", "youtube"]})
    banco.set("agenda", "c", {"hora": "18:00", "status": "postado", "redes": ["threads"],
                              "extra": {"n": 7}})
    assert [r["id"] for r in banco.query("agenda", {"status": "postado"})] == ["a", "c"]
    assert [r["id"] for r in banco.query("agenda", {"hora": {"$gte": "12:00"}})] == ["b", "c"]
    assert [r["id"] for r in banco.query("agenda", {"redes": {"$contem": "tiktok"}})] == ["b"]
    assert [r["id"] for r in banco.query("agenda", {"extra.n": {"$gt": 5}})] == ["c"]
    assert [r["id"] for r in banco.query("agenda", {"status": {"$in": ["agendado"]}})] == ["b"]
    assert [r["id"] for r in banco.query("agenda", {}, ordenar="hora", desc=True, limite=2)] == ["c", "b"]
    with pytest.raises(eb.ErroEspelho):
        banco.query("agenda", {"hora": {"$qualquer": 1}})


def test_nomes_invalidos(banco):
    for ruim in ("", "gerado", "_espelho", "com espaço", "a/b"):
        with pytest.raises(eb.ErroEspelho):
            banco.set(ruim, "x", {})
    with pytest.raises(eb.ErroEspelho):
        banco.set("canais", "", {})
    with pytest.raises(eb.ErroEspelho):
        banco.set("canais", "x", {"n": float("nan")})


def test_batch_grava_tudo_junto(banco):
    banco.set("canais", "gta", {"status": "ok"})
    res = banco.batch([
        {"op": "set", "colecao": "canais", "doc_id": "futebol", "dados": {"status": "ok"}},
        {"op": "update", "colecao": "canais", "doc_id": "gta", "dados": {"prontos": 2}},
        {"action": "delete", "collection": "canais", "id": "futebol"},
        {"action": "set", "collection": "sistema", "id": "saude", "data": {"status": "ok"}},
    ])
    assert len(res) == 4
    assert banco.get("canais", "gta") == {"status": "ok", "prontos": 2}
    assert banco.get("canais", "futebol") is None
    assert banco.get("sistema", "saude") == {"status": "ok"}


def test_batch_com_erro_desfaz_tudo(banco):
    banco.set("canais", "gta", {"status": "ok"})
    antes = banco.tudo()
    with pytest.raises(eb.ErroEspelho):
        banco.batch([
            {"op": "set", "colecao": "canais", "doc_id": "futebol", "dados": {"status": "ok"}},
            {"op": "update", "colecao": "canais", "doc_id": "gta", "dados": {"status": "erro"}},
            {"op": "delete", "colecao": "canais", "doc_id": "gta"},
            {"op": "voar", "colecao": "canais", "doc_id": "x"},          # inválida -> rollback
        ])
    assert banco.tudo() == antes
    assert banco.registro("canais", "gta")["versao"] == 1
    # segredo no meio do lote também desfaz tudo
    with pytest.raises(eb.SegredoNoDado):
        banco.batch([
            {"op": "set", "colecao": "canais", "doc_id": "futebol", "dados": {"ok": 1}},
            {"op": "set", "colecao": "canais", "doc_id": "carros", "dados": {"access_token": "abc123"}},
        ])
    assert banco.tudo() == antes


def test_transacao_manual_com_rollback(banco):
    with pytest.raises(RuntimeError):
        with banco.transacao():
            banco.set("a", "1", {"x": 1})
            banco.set("a", "2", {"x": 2})
            raise RuntimeError("falhou no meio")
    assert banco.list("a") == []


def test_sem_segredo_no_painel_publico(banco):
    with pytest.raises(eb.SegredoNoDado) as e:
        banco.set("sistema", "cfg", {"api": {"token": "segredo-de-verdade"}})
    assert "segredo-de-verdade" not in str(e.value)
    with pytest.raises(eb.SegredoNoDado):
        banco.set("sistema", "cfg", {"nota": "EAA" + "B" * 40})
    with pytest.raises(eb.SegredoNoDado):
        banco.set("sistema", "cfg", {"url": "https://x/?access_token=abc"})
    assert banco.get("sistema", "cfg") is None
    # base64 de imagem pode formar "EAA..." por acaso: não é segredo
    banco.set("avatares", "gta", "data:image/webp;base64,AAAA/EAA" + "Q" * 40 + "==")
    # campo vazio com nome de segredo não é segredo
    banco.set("sistema", "cfg", {"token": ""})


def test_exportar_importar_ida_e_volta(banco, tmp_path):
    banco.set("canais", "gta", {"nome": "GTA 6 | HP", "redes": {"instagram": {"seguidores": 12}}})
    banco.set("canais", "futebol", {"nome": "Futebol | HP"})
    banco.set("agenda", "2026-09-30", {"itens": [{"hora": "09:00", "titulo": "Olá </script>"}]})
    banco.set("avatares", "gta", "data:image/webp;base64,AAAA")
    saida = tmp_path / "painel_dados.json"
    r1 = banco.exportar(saida, gerado="2026-09-30T18:00:00-03:00")
    assert r1["mudou"] is True and r1["documentos"] == 4
    dados = json.loads(saida.read_text(encoding="utf-8"))
    assert dados["gerado"] == "2026-09-30T18:00:00-03:00"
    assert dados["canais"]["gta"]["redes"]["instagram"]["seguidores"] == 12   # mesmo formato do dados.json
    assert dados["_espelho"]["formato"] == eb.FORMATO

    # exportar de novo sem mudança: mesma assinatura, mudou=False
    r2 = banco.exportar(saida)
    assert r2["assinatura"] == r1["assinatura"] and r2["mudou"] is False

    with eb.EspelhoBanco(tmp_path / "outro.sqlite") as novo:
        res = novo.importar(saida)
        assert res["documentos"] == 4
        assert any("gerado" in i for i in res["ignorados"])
        assert novo.tudo() == banco.tudo()
        assert novo.assinatura() == banco.assinatura()
        # importar de novo é idempotente
        assert novo.importar(saida)["mudaram"] == 0
        assert novo.registro("canais", "gta")["versao"] == 1


def test_exportar_caminho_padrao(banco, tmp_path):
    banco.set("canais", "gta", {"a": 1})
    r = banco.exportar()
    assert Path(r["caminho"]) == tmp_path / "HypadoLocal" / "app" / "painel_dados.json"


def test_importar_formatos_aceitos(banco, tmp_path):
    # 1) o dados.json do painel de hoje (dias e gerado não são coleções)
    painel = {"gerado": "2026-09-30T16:42:29-03:00", "dias": ["2026-09-30"],
              "canais": {"gta": {"status": "ok"}}, "eventos": {},
              "sistema": {"pendencias": {"voce": [{"texto": "x"}]}}}
    r = banco.importar(painel)
    assert r["documentos"] == 2 and r["colecoes"] == ["canais", "sistema"]
    assert banco.get("sistema", "pendencias") == {"voce": [{"texto": "x"}]}
    # 2) lista de registros (estilo ArtifactData)
    banco.importar([{"collection": "tarefas", "doc_id": "t1", "data": {"texto": "a"}},
                    {"colecao": "tarefas", "id": "t2", "dados": {"texto": "b"}}])
    assert banco.get("tarefas", "t2") == {"texto": "b"}
    # 3) coleção como lista com id nos campos e {"documents": [...]}
    banco.importar({"colecoes": {"fila": [{"id": "f1", "texto": "a", "status": "fazendo"}],
                                 "notas": {"documents": [{"_id": "n1", "data": {"t": 1}}]}}})
    assert banco.get("fila", "f1") == {"texto": "a", "status": "fazendo"}
    assert banco.get("notas", "n1") == {"t": 1}
    # arquivo em disco com BOM (PowerShell grava assim)
    arq = tmp_path / "export.json"
    arq.write_text(json.dumps({"canais": {"carros": {"status": "ok"}}}), encoding="utf-8-sig")
    banco.importar(arq)
    assert banco.get("canais", "carros") == {"status": "ok"}


def test_importar_substituir(banco):
    banco.set("canais", "velho", {"a": 1})
    banco.set("outra", "fica", {"b": 2})
    banco.importar({"canais": {"gta": {"a": 2}}}, substituir=True)
    assert [r["id"] for r in banco.list("canais")] == ["gta"]
    assert banco.get("outra", "fica") == {"b": 2}


def test_importar_com_erro_nao_grava_nada(banco):
    banco.set("canais", "gta", {"a": 1})
    with pytest.raises(eb.SegredoNoDado):
        banco.importar({"canais": {"futebol": {"a": 1}, "carros": {"password": "x1"}}})
    assert [r["id"] for r in banco.list("canais")] == ["gta"]


def test_comparar_modo_sombra(banco):
    real = {"canais": {"gta": {"a": 1}, "futebol": {"a": 2}}}
    banco.importar(real)
    assert banco.comparar(real)["iguais"] is True
    banco.update("canais", "gta", {"a": 9})
    banco.set("canais", "novo", {"a": 3})
    r = banco.comparar({"canais": {"gta": {"a": 1}, "futebol": {"a": 2}, "filmes": {}}})
    assert r["iguais"] is False
    assert r["diferentes"] == ["canais/gta"]
    assert r["so_no_arquivo"] == ["canais/filmes"]
    assert r["so_no_espelho"] == ["canais/novo"]


def test_embutir_no_html_idempotente_e_seguro():
    html = "<div id=app></div>\n<script>const x = 1;</script>"
    d1 = {"titulo": "fim </script><script>alert(1)</script>", "n": 1}
    h1 = eb.embutir_no_html(html, d1)
    assert h1.index('id="painel-dados"') < h1.index("const x")        # antes do código
    assert "</script><script>alert" not in h1
    bloco = h1.split('id="painel-dados">')[1].split("</script>")[0]
    assert json.loads(bloco) == d1                                     # volta igual no JSON.parse
    h2 = eb.embutir_no_html(h1, {"n": 2})
    assert h2.count('id="painel-dados"') == 1 and '"n":2' in h2
    assert eb.embutir_no_html("<p>oi</p><!--PAINEL_DADOS-->", {"a": 1}).startswith(
        '<p>oi</p><script type="application/json"')


def test_cli(tmp_path, capsys):
    b = str(tmp_path / "cli.sqlite")
    assert eb.main(["--banco", b, "set", "canais", "gta", '{"status": "ok"}']) == 0
    assert eb.main(["--banco", b, "update", "canais", "gta", '{"prontos": 1}']) == 0
    capsys.readouterr()
    assert eb.main(["--banco", b, "listar", "canais", "--so-ids"]) == 0
    assert json.loads(capsys.readouterr().out) == ["gta"]
    assert eb.main(["--banco", b, "get", "canais", "gta"]) == 0
    assert json.loads(capsys.readouterr().out)["dados"] == {"status": "ok", "prontos": 1}
    assert eb.main(["--banco", b, "get", "canais", "nada"]) == 1
    # JSON quebrado (aspas comidas pelo PowerShell 5.1) -> erro claro, código 1
    assert eb.main(["--banco", b, "set", "canais", "x", "{status: ok}"]) == 1
    assert "PowerShell" in capsys.readouterr().err
    arq = tmp_path / "doc.json"
    arq.write_text('{"nome": "Carros | HP"}', encoding="utf-8")
    assert eb.main(["--banco", b, "set", "canais", "carros", "--arquivo", str(arq)]) == 0
    saida = tmp_path / "saida.json"
    assert eb.main(["--banco", b, "exportar", "--saida", str(saida)]) == 0
    assert json.loads(saida.read_text(encoding="utf-8"))["canais"]["carros"] == {"nome": "Carros | HP"}
    b2 = str(tmp_path / "cli2.sqlite")
    assert eb.main(["--banco", b2, "importar", str(saida)]) == 0
    assert eb.main(["--banco", b2, "comparar", str(saida)]) == 0
    lote = tmp_path / "lote.json"
    lote.write_text(json.dumps([{"op": "delete", "colecao": "canais", "doc_id": "gta"}]), encoding="utf-8")
    assert eb.main(["--banco", b2, "batch", str(lote)]) == 0
    assert eb.main(["--banco", b2, "comparar", str(saida)]) == 1
    capsys.readouterr()
    with pytest.raises(SystemExit) as e:
        eb.main(["--help"])
    assert e.value.code == 0
    out = capsys.readouterr().out
    assert "uso:" in out and "comandos" in out and "importar" in out


def test_cli_embutir(tmp_path, capsys):
    b = str(tmp_path / "cli.sqlite")
    saida = tmp_path / "painel_dados.json"
    eb.main(["--banco", b, "set", "canais", "gta", '{"status": "ok"}'])
    eb.main(["--banco", b, "exportar", "--saida", str(saida)])
    html = tmp_path / "painel.html"
    html.write_text("<div></div><script>1</script>", encoding="utf-8")
    assert eb.main(["embutir", str(html), "--dados", str(saida)]) == 0
    assert 'id="painel-dados"' in html.read_text(encoding="utf-8")


def test_log_sem_dados_do_painel(banco, tmp_path):
    banco.set("canais", "gta", {"observacao": "texto que não precisa ir para o log"})
    banco.batch([{"op": "set", "colecao": "canais", "doc_id": "x", "dados": {"a": 1}}])
    banco.exportar(tmp_path / "x.json")
    logs = list((tmp_path / "HypadoLocal" / "app" / "logs").glob("painel_espelho_*.log"))
    assert logs
    txt = "".join(p.read_text(encoding="utf-8") for p in logs)
    assert "exportar" in txt and "texto que não precisa" not in txt
