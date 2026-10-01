import json

import pytest

from metricas import executar
from metricas.cli import comando_schtasks, main
from metricas.config import pasta_metricas
from metricas.modelos import numero
from metricas.tiktok import importar

from .falso import AGORA, TOKENS, config_teste, escrever_segredos

CSV = """Conta;Seguidores;ID;Legenda;Publicado_em;Link;Visualizações;Curtidas;Comentários;Compartilhamentos;Salvamentos
gta;12.345;7001;Trailer GTA 6 reagindo;2026-09-29 19:00;https://tiktok.com/@hpgta6/video/7001;1,2 mil;150;12;9;20
@hp.carros;;8001;Carro novo;29/09/2026 10:00;https://tiktok.com/@hp.carros/video/8001;5.400;300;25;11;
"""


def test_numero_aceita_formatos_brasileiros():
    assert [numero(x) for x in ("12.345", "1,2 mil", "3,4K", "1M", "1.234,5", "", "—", 7)] == \
        [12345, 1200, 3400, 1_000_000, 1234.5, None, None, 7]


def test_importar_tiktok_csv():
    arq = pasta_metricas() / "tiktok.csv"
    arq.write_text(CSV, encoding="utf-8")
    res = importar(arq, config=config_teste(), agora=AGORA)
    assert res == {"gta": 1, "carros": 1}
    foto = json.loads((pasta_metricas() / "2026-09-30.json").read_text(encoding="utf-8"))
    tk = foto["contas"]["gta"]["tiktok"]
    assert tk["fonte"] == "manual" and tk["status"] == "ok" and tk["seguidores"] == 12345
    p = tk["posts"][0]
    assert (p["id"], p["views"], p["curtidas"], p["salvamentos"], p["tipo"]) == \
        ("7001", 1200, 150, 20, "video")
    assert p["publicado_em"] == "2026-09-29T19:00:00-03:00"
    assert foto["contas"]["carros"]["tiktok"]["posts"][0]["views"] == 5400
    assert foto["contas"]["carros"]["tiktok"]["posts"][0]["publicado_em"] == \
        "2026-09-29T10:00:00-03:00"
    painel = json.loads((pasta_metricas() / "metricas_painel.json").read_text(encoding="utf-8"))
    assert painel["contas"]["gta"]["redes"]["tiktok"]["seguidores"] == 12345


def test_importar_tiktok_json_com_conta_na_linha_de_comando():
    arq = pasta_metricas() / "tk.json"
    arq.write_text(json.dumps({"seguidores": 900, "posts": [
        {"id": "9", "views": 100, "likes": 7, "descricao": "receita",
         "data": "2026-09-29T12:00:00-03:00"}]}), encoding="utf-8")
    assert importar(arq, conta="receitas", config=config_teste(), agora=AGORA) == {"receitas": 1}
    tk = json.loads((pasta_metricas() / "ultimo.json").read_text(encoding="utf-8"))
    assert tk["contas"]["receitas"]["tiktok"]["posts"][0]["curtidas"] == 7


def test_importar_sem_conta_da_erro():
    arq = pasta_metricas() / "x.csv"
    arq.write_text("id;views\n1;10\n", encoding="utf-8")
    with pytest.raises(ValueError):
        importar(arq, config=config_teste(), agora=AGORA)


def test_cli_simular_nao_chama_nem_grava(raizes_temporarias, capsys):
    local, _ = raizes_temporarias
    escrever_segredos(local, sem=("TH_GTA_TOKEN",))
    assert main(["coletar", "--conta", "gta", "--simular"]) == 0
    out = capsys.readouterr().out
    assert "gta/instagram: coletaria (token: ok, id: ok)" in out
    assert "gta/threads: sem_token" in out and "TH_GTA_TOKEN" in out
    assert "gta/youtube: pularia: nao_autorizado" in out
    assert "gta/tiktok: manual" in out
    for v in TOKENS.values():
        assert v not in out
    assert not list(pasta_metricas().glob("*.json"))


def test_cli_agendar_6h_imprime_schtasks_com_pythonw(capsys):
    assert main(["agendar-6h"]) == 0
    out = capsys.readouterr().out
    assert "schtasks --% /Create" in out and "/SC DAILY /ST 06:00" in out
    assert "pythonw.exe" in out and "agendado.py" in out and "coletar" in out
    linha = [l for l in comando_schtasks("05:45") if l.startswith("schtasks")][0]
    assert "/ST 05:45" in linha


def test_cli_resumo(capsys):
    arq = pasta_metricas() / "t.csv"
    arq.write_text(CSV, encoding="utf-8")
    importar(arq, config=config_teste(), agora=AGORA)
    assert main(["resumo"]) == 0
    out = capsys.readouterr().out
    assert "GTA 6 | HP" in out and "tiktok" in out and "12.345" in out
    assert "Top 5 por views (24h)" in out
    assert main(["resumo", "--data", "2026-01-01"]) == 1


def test_executar_gancho_do_motor(raizes_temporarias):
    local, _ = raizes_temporarias
    escrever_segredos(local)
    r = executar({"acao": "coletar", "simular": True, "conta": "gta"})
    assert r["ok"] and r["simulado"] and any("gta/instagram" in l for l in r["plano"])
    assert executar({"acao": "voar"})["ok"] is False
