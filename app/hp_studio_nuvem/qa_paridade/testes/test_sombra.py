"""Modo sombra: registro e a regra dos 7 dias."""
from datetime import date

import pytest

from hpbase import ler_json, pasta_paridade
from qa_paridade.sombra import calcular_status, listar_tarefas, registrar, status_tarefa

from .apoio import dia, relatorio_falso

OK = relatorio_falso(True)
RUIM = relatorio_falso(False)


def _dias(tarefa, dias_ok, reprovados=(), hoje=None):
    for n in sorted(set(dias_ok) | set(reprovados)):
        registrar(tarefa, RUIM if n in reprovados else OK, id=f"d{n}", quando=dia(n))
    return status_tarefa(tarefa, hoje=hoje or dia(max(set(dias_ok) | set(reprovados))).date())


def test_relatorio_falso_tem_veredito_certo():
    assert OK["aprovado"] and OK["veredito"] == "IDENTICO"
    assert not RUIM["aprovado"] and RUIM["veredito"] == "DIFERENTE"


def test_seis_dias_nao_libera():
    st = _dias("editor_reel", range(1, 7))
    assert st["dias_seguidos"] == 6
    assert st["falta"] == 1
    assert st["liberada"] is False


def test_sete_dias_libera():
    st = _dias("editor_reel", range(1, 8))
    assert st["dias_seguidos"] == 7
    assert st["falta"] == 0
    assert st["liberada"] is True
    assert st["liberada_em"] == "2026-09-07"


def test_reprovado_no_meio_zera():
    st = _dias("editor_reel", [1, 2, 3, 5, 6, 7, 8, 9, 10], reprovados=[4])
    assert st["dias_seguidos"] == 6
    assert st["liberada"] is False
    assert st["falta"] == 1
    assert "reprovado em 2026-09-04 zerou" in st["observacao"]
    registrar("editor_reel", OK, id="d11", quando=dia(11))
    assert status_tarefa("editor_reel", hoje=date(2026, 9, 11))["liberada"] is True


def test_dois_no_mesmo_dia_contam_um():
    registrar("legendador", OK, id="a", quando=dia(1, 9))
    registrar("legendador", OK, id="b", quando=dia(1, 15))
    for n in range(2, 7):
        registrar("legendador", OK, id="x", quando=dia(n))
    st = status_tarefa("legendador", hoje=date(2026, 9, 6))
    assert st["comparacoes"] == 7
    assert st["dias_com_comparacao"] == 6
    assert st["dias_seguidos"] == 6
    assert st["liberada"] is False


def test_um_reprovado_no_mesmo_dia_derruba_o_dia():
    for n in range(1, 7):
        registrar("t", OK, id="ok", quando=dia(n))
    registrar("t", OK, id="manha", quando=dia(7, 9))
    registrar("t", RUIM, id="tarde", quando=dia(7, 16))
    st = status_tarefa("t", hoje=date(2026, 9, 7))
    assert st["dias_seguidos"] == 0 and st["falta"] == 7 and not st["liberada"]
    assert st["dias"][-1]["situacao"] == "reprovado"


def test_dia_sem_comparacao_quebra_a_sequencia():
    st = _dias("t", [1, 2, 3, 5, 6, 7, 8])  # faltou o dia 4
    assert st["dias_seguidos"] == 4
    assert not st["liberada"]
    assert "faltou" in st["observacao"]


def test_sequencia_parada_ha_dias_zera_mas_hoje_ainda_vale():
    for n in (1, 2, 3):
        registrar("t", OK, id="x", quando=dia(n))
    assert status_tarefa("t", hoje=date(2026, 9, 4))["dias_seguidos"] == 3  # hoje ainda dá
    parada = status_tarefa("t", hoje=date(2026, 9, 6))
    assert parada["dias_seguidos"] == 0 and parada["falta"] == 7
    assert "quebrada" in parada["observacao"]


def test_depois_de_liberada_so_reprovado_tira():
    _dias("t", range(1, 8))
    registrar("t", OK, id="checagem", quando=dia(20))  # conferência esporádica
    st = status_tarefa("t", hoje=date(2026, 9, 25))
    assert st["liberada"] is True
    registrar("t", RUIM, id="falhou", quando=dia(26))
    st = status_tarefa("t", hoje=date(2026, 9, 26))
    assert st["liberada"] is False and st["dias_seguidos"] == 0
    assert "tirou a liberação" in st["observacao"]


def test_arquivos_e_resumo():
    res = registrar("editor reel/v2", OK, id="post 123", quando=dia(3))
    pasta = pasta_paridade() / "editor_reel_v2"
    assert res["json"] == pasta / "2026-09-03_post_123.json"
    assert res["md"].exists() and res["md"].read_text(encoding="utf-8").startswith("# Paridade")
    dados = ler_json(res["json"])
    assert dados["sombra"] == {"tarefa": "editor_reel_v2", "id": "post_123", "dia": "2026-09-03",
                               "quando": "2026-09-03T10:00:00-03:00"}
    # mesmo id no mesmo dia não sobrescreve
    res2 = registrar("editor reel/v2", OK, id="post 123", quando=dia(3, 11))
    assert res2["json"].name == "2026-09-03_post_123_2.json"
    resumo = ler_json(pasta / "resumo.json")
    assert resumo["comparacoes"] == 2 and resumo["dias_seguidos"] == 1
    assert resumo["falta"] == 6 and resumo["liberada"] is False
    assert "regra" in resumo and "atualizado_em" in resumo
    assert listar_tarefas() == ["editor_reel_v2"]


def test_tarefa_sem_registro():
    st = status_tarefa("nunca_rodou", hoje=date(2026, 9, 30))
    assert st["dias_seguidos"] == 0 and st["falta"] == 7 and not st["liberada"]
    assert st["ultimo_dia"] is None


def test_arquivo_estranho_na_pasta_nao_conta():
    registrar("t", OK, id="a", quando=dia(1))
    pasta = pasta_paridade() / "t"
    (pasta / "2026-09-02_lixo.json").write_text("{nao é json", encoding="utf-8")
    (pasta / "anotacao.json").write_text("{}", encoding="utf-8")
    assert status_tarefa("t", hoje=date(2026, 9, 2))["comparacoes"] == 1


@pytest.mark.parametrize("minimo,esperado", [(1, 3), (2, 1)])
def test_minimo_de_comparacoes_por_dia(minimo, esperado):
    regs = [{"dia": date(2026, 9, d), "aprovado": True, "nota_final": 10, "veredito": "IDENTICO",
             "quando": None, "id": "x"} for d in (1, 2, 3)]
    regs.append(dict(regs[-1]))  # dia 3 com 2 comparações
    st = calcular_status(regs, date(2026, 9, 3), 7, minimo)
    assert st["dias_seguidos"] == esperado


def test_dias_necessarios_configuravel():
    regs = [{"dia": date(2026, 9, d), "aprovado": True, "nota_final": 10, "veredito": "IDENTICO",
             "quando": None, "id": "x"} for d in (1, 2, 3)]
    assert calcular_status(regs, date(2026, 9, 3), 3, 1)["liberada"] is True
