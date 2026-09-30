"""Seguro contra queda: marcador .em_andamento, diário 'pendente', idempotência."""
import json
import os
import time

from hpbase import escrever_json, ler_json

from esteira.constantes import (AGENDADOS, BAIXADOS, EDICAO, ERROS, LEGENDA,
                                PEDIDOS, REVISAO)
from esteira.pastas import ler_estado, salvar_estado
from esteira.pedido import criar_pedido
from esteira.testes.conftest import pedido_reel


def ate(amb, etapa_final):
    """Cria um reel e leva até etapa_final, um passo por vez."""
    item = criar_pedido(pedido_reel())
    ordem = [PEDIDOS, BAIXADOS, LEGENDA, EDICAO, REVISAO]
    for etapa in ordem[:ordem.index(etapa_final)]:
        amb.esteira().processar(amb.pasta(etapa) / item.name, etapa)
    return amb.pasta(etapa_final) / item.name


def test_queda_no_meio_do_trabalho_refaz(amb):
    item = ate(amb, EDICAO)
    # app caiu editando: sobrou marcador e um final pela metade
    escrever_json(item / ".em_andamento", {"etapa": EDICAO, "trabalho": "edicao",
                                           "pid": 999999, "desde": "2026-09-30T10:00"})
    (item / "_final_tmp.mp4").write_bytes(b"lixo")
    amb.chamadas.clear()
    amb.ciclo(max_trabalhos=1)
    novo = amb.pasta(REVISAO) / item.name
    assert novo.exists() and not (novo / ".em_andamento").exists()
    assert ("editor", "editar", item.name) in amb.chamadas
    h = (novo / "historico.log").read_text(encoding="utf-8")
    assert "retomada após queda" in h and "(1/3)" in h


def test_queda_depois_do_movimento_so_limpa(amb):
    item = ate(amb, LEGENDA)
    # marcador sobrou da etapa anterior (caiu logo depois do os.replace)
    escrever_json(item / ".em_andamento", {"etapa": BAIXADOS, "pid": 999999})
    amb.ciclo(max_trabalhos=1)
    novo = amb.pasta(EDICAO) / item.name
    assert novo.exists()
    assert ler_estado(novo)["tentativas"] == {}
    assert "retomada" not in (novo / "historico.log").read_text(encoding="utf-8")


def test_queda_entre_trabalho_e_movimento_nao_refaz(amb):
    item = ate(amb, EDICAO)
    est = ler_estado(item)
    est["pendente"] = {"origem": EDICAO, "destino": REVISAO, "mensagem": "final pronto"}
    salvar_estado(item, est)
    escrever_json(item / ".em_andamento", {"etapa": EDICAO, "pid": 999999})
    amb.chamadas.clear()
    amb.ciclo(max_trabalhos=1)
    novo = amb.pasta(REVISAO) / item.name
    assert novo.exists()
    assert not any(c[0] == "editor" for c in amb.chamadas)  # não editou de novo
    est = ler_estado(novo)
    assert "pendente" not in est
    assert "completando movimento" in (novo / "historico.log").read_text(encoding="utf-8")


def test_pendente_de_outra_etapa_e_limpo(amb):
    item = ate(amb, LEGENDA)
    est = ler_estado(item)
    est["pendente"] = {"origem": BAIXADOS, "destino": LEGENDA}
    salvar_estado(item, est)
    amb.ciclo(max_trabalhos=1)
    assert amb.itens(EDICAO) == [item.name]


def test_queda_repetida_vai_para_99(amb):
    item = ate(amb, BAIXADOS)
    est = ler_estado(item)
    est["tentativas"][BAIXADOS] = 2  # já caiu 2 vezes nesta etapa
    salvar_estado(item, est)
    escrever_json(item / ".em_andamento", {"etapa": BAIXADOS, "pid": 999999})
    amb.esteira().processar(item, BAIXADOS)
    assert amb.itens(ERROS) == [item.name]
    e = ler_json(amb.pasta(ERROS) / item.name / "erro.json")
    assert "caiu 3 vezes" in e["mensagem"] and e["tentativas"] == 3


def test_revisao_caiu_depois_de_decidir_nao_conta_volta_duas_vezes(amb):
    item = ate(amb, REVISAO)
    amb.ciclo()  # gera material
    (item / "refazer.json").write_text(json.dumps({"notas": {"capa": 6}, "motivo": "capa"}))
    e = amb.esteira()
    trab = e.trabalhos[REVISAO]
    res = trab.executar(item)  # decidiu, gravou estado com pendente... e "caiu" aqui
    assert res.destino == EDICAO
    assert ler_estado(item)["voltas"] == 1
    amb.ciclo()
    est = ler_estado(amb.pasta(REVISAO) / item.name)
    assert est["voltas"] == 1 and len(est["revisoes"]) == 1


def test_refazer_antigo_esquecido_nao_conta_de_novo(amb):
    item = ate(amb, REVISAO)
    conteudo = json.dumps({"notas": {"capa": 6}, "motivo": "capa"})
    (item / "refazer.json").write_text(conteudo)
    amb.ciclo()  # volta 1: vai para 04 e já volta para 05
    rev = amb.pasta(REVISAO) / item.name
    # simula queda antes de arquivar: o mesmo refazer.json reaparece
    (rev / "refazer.json").write_text(conteudo)
    amb.ciclo()
    est = ler_estado(rev)
    assert est["voltas"] == 1 and rev.exists()
    assert "antigo arquivado" in (rev / "historico.log").read_text(encoding="utf-8")


def test_pasta_criando_velha_e_apagada(amb):
    velha = amb.pasta(PEDIDOS) / ".criando_P1_2026-09-30_1830_gta_x"
    velha.mkdir()
    antigo = time.time() - 7200
    os.utime(velha, (antigo, antigo))
    nova = amb.pasta(PEDIDOS) / ".criando_P1_2026-09-30_1830_gta_y"
    nova.mkdir()
    amb.ciclo(max_trabalhos=0)
    assert not velha.exists() and nova.exists()


def test_json_solto_ja_importado_nao_duplica(amb):
    dados = pedido_reel(titulo="Solto")
    item = criar_pedido(dados)  # caiu depois de criar a pasta e antes de tirar o .json
    solto = amb.pasta(PEDIDOS) / "solto.json"
    solto.write_text(json.dumps(dados), encoding="utf-8")
    r = amb.ciclo(max_trabalhos=0)
    assert r["importados"] == [item.name]
    assert amb.itens(PEDIDOS) == [item.name] and amb.itens(ERROS) == []
    assert (item / "pedido_original.json").exists() and not solto.exists()


def test_aviso_no_ar_nao_duplica_depois_de_queda(amb):
    item = ate(amb, REVISAO)
    amb.ciclo()
    (item / "aprovado.json").write_text(json.dumps({"notas": {"gancho": 9}}))
    amb.ciclo()
    ag = amb.pasta(AGENDADOS) / item.name
    (ag / "tiktok_ok.json").write_text("{}")
    amb.ciclo()
    fila = amb.cfg.pasta_sombra / "whatsapp_fila"
    assert len(list(fila.glob("*.json"))) == 1
    # simula queda entre "preparando" e a gravação na fila
    from esteira.constantes import POSTADOS
    fim = amb.pasta(POSTADOS) / item.name
    aviso = ler_json(fim / "aviso_no_ar.json")
    escrever_json(fim / "aviso_no_ar.json", {"status": "preparando",
                                             "arquivo_nome": aviso["arquivo_nome"],
                                             "mensagem": aviso["mensagem"]})
    amb.ciclo()
    assert len(list(fila.glob("*.json"))) == 1  # regravou o mesmo arquivo
