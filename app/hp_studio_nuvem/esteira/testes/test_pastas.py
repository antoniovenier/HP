"""Nome do item, ordem de prioridade, busca e movimento atômico."""
from datetime import datetime

import pytest

from esteira.constantes import ERROS, PEDIDOS
from esteira.erros import ErroEtapa, ItemNaoEncontrado
from esteira.pastas import (achar_item, chave_ordem, ler_nome, listar,
                            montar_nome, mover, nome_livre, slugificar)


def test_nome_ida_e_volta():
    n = montar_nome("P1", datetime(2026, 9, 30, 18, 30), "gta", "rockstar-quinta")
    assert n == "P1_2026-09-30_1830_gta_rockstar-quinta"
    i = ler_nome(n)
    assert (i.prioridade, i.data, i.hora, i.canal, i.slug) == \
        ("P1", "2026-09-30", "1830", "gta", "rockstar-quinta")
    assert i.sem_prioridade == "2026-09-30_1830_gta_rockstar-quinta"
    assert ler_nome("pasta_qualquer") is None


def test_slug():
    assert slugificar("Ação: São Paulo x Grêmio!!") == "acao-sao-paulo-x-gremio"
    s = slugificar("palavra " * 20)
    assert len(s) <= 40 and not s.endswith("-")
    assert slugificar("???") == "item"


def test_ordem_p0_antes_de_tudo_depois_horario():
    nomes = ["P2_2026-09-30_0800_gta_a", "P1_2026-09-30_2100_gta_b",
             "P0_2026-10-01_2300_futebol_gol", "P1_2026-09-30_0900_gta_c", "fora_do_padrao"]
    ordem = sorted(nomes, key=chave_ordem)
    assert ordem == ["P0_2026-10-01_2300_futebol_gol", "P1_2026-09-30_0900_gta_c",
                     "P1_2026-09-30_2100_gta_b", "P2_2026-09-30_0800_gta_a", "fora_do_padrao"]


def test_mesma_prioridade_e_horario_mais_adiantado_primeiro():
    n = "P1_2026-09-30_0900_gta_x"
    assert chave_ordem(n, 4) < chave_ordem(n, 0)


def test_listar_ignora_ocultas_e_ordena(amb):
    p = amb.pasta(PEDIDOS)
    for n in ("P2_2026-09-30_0800_gta_a", "P0_2026-09-30_2000_gta_b", ".criando_x", "_tmp"):
        (p / n).mkdir()
    (p / "solto.json").write_text("{}")
    assert [x.name for x in listar(p)] == ["P0_2026-09-30_2000_gta_b", "P2_2026-09-30_0800_gta_a"]


def test_achar_item(amb):
    (amb.pasta(PEDIDOS) / "P1_2026-09-30_1830_gta_rockstar-quinta").mkdir()
    (amb.pasta(ERROS) / "P1_2026-09-30_1900_gta_rockstar-sexta").mkdir()
    assert achar_item(amb.cfg.raiz, "P1_2026-09-30_1830_gta_rockstar-quinta").parent.name == PEDIDOS
    assert achar_item(amb.cfg.raiz, "2026-09-30_1830_gta_rockstar-quinta").name.startswith("P1_")
    assert achar_item(amb.cfg.raiz, "sexta").parent.name == ERROS
    with pytest.raises(ItemNaoEncontrado, match="ambíguo"):
        achar_item(amb.cfg.raiz, "rockstar")
    with pytest.raises(ItemNaoEncontrado):
        achar_item(amb.cfg.raiz, "nada")


def test_mover_atomico_e_idempotente(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    item = a / "P1_2026-09-30_1830_gta_x"
    item.mkdir(parents=True)
    (item / "arquivo.txt").write_text("oi")
    novo = mover(item, b)
    assert novo == b / item.name and (novo / "arquivo.txt").read_text() == "oi"
    assert not item.exists()
    assert mover(item, b) == novo  # de novo: já movido, não faz nada
    with pytest.raises(FileNotFoundError):
        mover(a / "nao_existe", b)


def test_mover_nao_sobrescreve(tmp_path):
    (tmp_path / "a" / "x").mkdir(parents=True)
    (tmp_path / "b" / "x").mkdir(parents=True)
    with pytest.raises(ErroEtapa, match="já existe"):
        mover(tmp_path / "a" / "x", tmp_path / "b")
    assert (tmp_path / "a" / "x").exists()


def test_nome_livre(tmp_path):
    (tmp_path / "x").mkdir()
    (tmp_path / "x__2").mkdir()
    assert nome_livre(tmp_path, "x") == "x__3"
    assert nome_livre(tmp_path, "y") == "y"
