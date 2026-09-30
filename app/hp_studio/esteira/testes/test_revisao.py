"""Revisor de qualidade: faixas, etapa de volta, limite de 2 voltas."""
import json

import pytest
from hpbase import ler_json

from esteira import acoes
from esteira.constantes import (AGENDADOS, CRITERIO_ETAPA, EDICAO, ERROS,
                                LEGENDA, PEDIDOS, REVISAO)
from esteira.pedido import criar_pedido
from esteira.revisao import (RevisaoInvalida, calcular_media, decidir,
                             etapa_da_menor_nota, validar_notas,
                             veredito_da_media)
from esteira.testes.conftest import MANHA, pedido_carrossel, pedido_reel


@pytest.mark.parametrize("media,veredito", [
    (10, "Excelente"), (9.0, "Excelente"), (8.96, "Excelente"), (8.9, "Bom"), (7.0, "Bom"),
    (6.95, "Bom"), (6.9, "Médio"), (5.0, "Médio"), (4.9, "Razoável"), (0, "Razoável")])
def test_faixas(media, veredito):
    assert veredito_da_media(media) == veredito


def test_media_calculada():
    assert calcular_media({"a": 9, "b": 8, "c": 8}) == 8.33
    assert calcular_media({"a": 7, "b": 7, "c": 6}) == 6.67


def test_notas_invalidas():
    for ruim in ({}, {"a": 11}, {"a": -1}, {"a": "x"}, {"a": True}, [1, 2]):
        with pytest.raises(RevisaoInvalida):
            validar_notas(ruim)
    assert validar_notas({"Gancho": "8,5"}) == {"gancho": 8.5}


def test_menor_nota_e_empate_vai_para_tras():
    assert etapa_da_menor_nota({"gancho": 6, "legenda": 5, "capa": 8}, CRITERIO_ETAPA) == \
        ("legenda", LEGENDA)
    # empate entre capa (04) e fonte_credito (01): vai para a etapa mais para trás
    assert etapa_da_menor_nota({"capa": 5, "fonte_credito": 5}, CRITERIO_ETAPA)[1] == PEDIDOS


def dec(dados, tipo="refazer", voltas=0, estatico=False):
    return decidir(dados, tipo, voltas, 2, CRITERIO_ETAPA, estatico)


def test_decidir_aprovado():
    d = dec({"notas": {"gancho": 9, "legenda": 8}}, "aprovado")
    assert d["acao"] == "aprovar" and d["destino"] == AGENDADOS and d["veredito"] == "Bom"
    assert dec({"notas": {"gancho": 10, "legenda": 9}}, "aprovado")["veredito"] == "Excelente"


def test_aprovado_com_media_baixa_vira_refazer():
    d = dec({"notas": {"gancho": 6, "legenda": 5}}, "aprovado")
    assert d["acao"] == "voltar" and d["destino"] == LEGENDA
    assert any("vale como refazer" in o for o in d["observacoes"])


def test_aprovado_sem_notas_invalido():
    with pytest.raises(RevisaoInvalida):
        dec({"motivo": "ok"}, "aprovado")


def test_medio_volta_para_etapa_da_menor_nota():
    d = dec({"notas": {"gancho": 7, "legenda": 5, "audio": 7}, "motivo": "erros de digitação"})
    assert d["veredito"] == "Médio" and d["destino"] == LEGENDA and d["criterio_menor"] == "legenda"
    d = dec({"notas": {"gancho": 5, "legenda": 7, "audio": 7}})
    assert d["destino"] == EDICAO


def test_razoavel_volta_ao_curador():
    d = dec({"notas": {"gancho": 4, "legenda": 5, "audio": 4}, "etapa_destino": "04"})
    assert d["veredito"] == "Razoável" and d["destino"] == PEDIDOS


def test_etapa_destino_do_revisor_vale_no_medio():
    d = dec({"notas": {"gancho": 6, "legenda": 6}, "etapa_destino": "edicao"})
    assert d["destino"] == EDICAO
    d = dec({"notas": {"gancho": 6}, "etapa_destino": "06_agendados"})
    assert d["destino"] == EDICAO and any("inválida" in o for o in d["observacoes"])


def test_refazer_sem_notas():
    assert dec({"motivo": "trocar fonte"})["destino"] == PEDIDOS
    assert dec({"motivo": "capa", "etapa_destino": "04"})["destino"] == EDICAO


def test_estatico_nunca_volta_para_etapa_de_video():
    d = dec({"notas": {"legenda": 5, "arte": 8}}, estatico=True)
    assert d["destino"] == EDICAO


def test_limite_de_voltas():
    assert dec({"notas": {"gancho": 6}}, voltas=1)["acao"] == "voltar"
    d = dec({"notas": {"gancho": 6}, "motivo": "ainda ruim"}, voltas=2)
    assert d["acao"] == "erro" and "limite de 2 voltas" in d["motivo"]
    assert "ainda ruim" in d["motivo"]


# --- integração com a esteira ---------------------------------------------------
def na_revisao(amb, **kw):
    item = criar_pedido(pedido_reel(**kw))
    amb.ciclo()
    return amb.pasta(REVISAO) / item.name


def gravar(item, nome, dados):
    (item / nome).write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")


def test_duas_voltas_e_a_terceira_vai_para_99(amb):
    rev = na_revisao(amb)
    nome = rev.name
    gravar(rev, "refazer.json", {"notas": {"gancho": 8, "legenda": 5}, "motivo": "legenda errada"})
    r = amb.ciclo()
    # volta para 03, refaz legenda e edição e volta para a revisão (rodada 2)
    assert f"{REVISAO} -> {LEGENDA}: {nome}" in r["avancaram"]
    assert amb.itens(REVISAO) == [nome]
    est = ler_json(rev / "estado.json")
    assert est["voltas"] == 1 and est["revisoes"][0]["destino"] == LEGENDA
    assert (rev / "revisao" / "decisoes" / "rodada_1_refazer.json").exists()
    assert not (rev / "refazer.json").exists()
    assert "Rodada: 2" in (rev / "texto_revisao.md").read_text(encoding="utf-8")

    gravar(rev, "refazer.json", {"notas": {"gancho": 6, "capa": 7}, "motivo": "gancho fraco"})
    amb.ciclo()
    assert ler_json(rev / "estado.json")["voltas"] == 2
    assert amb.itens(REVISAO) == [nome]

    gravar(rev, "refazer.json", {"notas": {"gancho": 6}, "motivo": "gancho ainda fraco"})
    amb.ciclo()
    assert amb.itens(ERROS) == [nome]
    e = ler_json(amb.pasta(ERROS) / nome / "erro.json")
    assert e["etapa"] == REVISAO and "limite de 2 voltas" in e["mensagem"]
    assert "gancho ainda fraco" in e["mensagem"]


def test_razoavel_espera_o_curador(amb):
    rev = na_revisao(amb)
    gravar(rev, "refazer.json", {"notas": {"assunto": 3, "gancho": 5}, "motivo": "tema fraco"})
    amb.ciclo()
    item = amb.pasta(PEDIDOS) / rev.name
    assert item.exists() and (item / "aguardando_curador.json").exists()
    amb.chamadas.clear()
    amb.ciclo()
    amb.ciclo()
    assert item.exists() and amb.chamadas == []  # ninguém mexe até o Curador liberar
    assert "aguardando Curador" in acoes.status(amb.cfg)[PEDIDOS][0]["situacao"]
    acoes.liberar(rev.name, cfg=amb.cfg)
    amb.ciclo()
    assert amb.itens(REVISAO) == [rev.name]


def test_ajustes_do_refazer_vao_para_o_pedido(amb):
    rev = na_revisao(amb)
    gravar(rev, "refazer.json", {"notas": {"capa": 6}, "motivo": "capa ruim",
                                 "ajustes": {"capa_tempo": 3.5}})
    amb.ciclo()
    assert ler_json(amb.pasta(REVISAO) / rev.name / "pedido.json")["capa_tempo"] == 3.5


def test_arquivo_invalido_fica_esperando(amb):
    rev = na_revisao(amb)
    (rev / "aprovado.json").write_text("{não é json", encoding="utf-8")
    r = amb.ciclo()
    assert amb.itens(REVISAO) == [rev.name]
    assert (rev / "aprovado.invalido.json").exists()
    assert any("inválido" in a for a in r["aguardando"])
    gravar(rev, "aprovado.json", {"notas": {"gancho": 12}})
    amb.ciclo()
    assert amb.itens(REVISAO) == [rev.name]


def test_refazer_vence_aprovado(amb):
    rev = na_revisao(amb)
    gravar(rev, "aprovado.json", {"notas": {"gancho": 10}})
    gravar(rev, "refazer.json", {"notas": {"capa": 6}, "motivo": "capa"})
    amb.ciclo()
    # voltou para 04 e já está de novo na revisão, esperando (o aprovado velho não vale)
    assert amb.itens(REVISAO) == [rev.name]
    est = ler_json(rev / "estado.json")
    assert [r["arquivo"] for r in est["revisoes"]] == ["refazer.json"]
    assert (rev / "revisao" / "decisoes" / "rodada_1_ignorado_aprovado.json").exists()
    assert not (rev / "aprovado.json").exists()


def test_cli_aprovar_e_refazer_gravam_e_aplicam(amb):
    rev = na_revisao(amb)
    r = acoes.refazer(rev.name, "capa escura", etapa="04", notas=["capa=6", "gancho=9"],
                      cfg=amb.cfg, plugins=amb.plugins, agora=MANHA)
    assert r["etapa_destino"] == EDICAO and r["resultado"].startswith("avancar")
    assert amb.itens(EDICAO) == [rev.name]
    amb.ciclo()
    r = acoes.aprovar(rev.name, "gancho=9,legenda=8,5", cfg=amb.cfg, plugins=amb.plugins,
                      agora=MANHA)
    assert r["media"] == 8.75 and r["veredito"] == "Bom"
    assert amb.itens(AGENDADOS) == [rev.name]


def test_estatico_na_revisao(amb):
    item = criar_pedido(pedido_carrossel())
    amb.ciclo()
    rev = amb.pasta(REVISAO) / item.name
    gravar(rev, "refazer.json", {"notas": {"legenda": 5, "arte": 7}})
    amb.ciclo()
    est = ler_json(amb.pasta(REVISAO) / item.name / "estado.json")
    assert est["revisoes"][0]["destino"] == EDICAO
