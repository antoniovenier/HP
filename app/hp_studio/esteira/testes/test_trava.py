"""Trabalho pesado: nunca 18h-22h30 (exceto P0, decisão de 30/09), 1 por vez (pesado.lock)."""
import json
import os
from datetime import datetime

from hpbase import pasta_app

from esteira.constantes import AGENDADOS, EDICAO, PEDIDOS, REVISAO
from esteira.pedido import criar_pedido
from esteira.testes.conftest import NOITE, pedido_carrossel, pedido_reel


def test_p0_roda_na_janela_e_p1_espera(amb):
    p1 = criar_pedido(pedido_reel(titulo="Normal"))
    p0 = criar_pedido(pedido_reel(prioridade="P0", titulo="Gol"))
    r = amb.ciclo(agora=NOITE)
    assert amb.itens(REVISAO) == [p0.name]          # P0 foi até a revisão às 19h
    assert amb.itens(PEDIDOS) == [p1.name]          # P1 espera 22h30
    assert r["adiados_pesado"] == [f"{PEDIDOS}/{p1.name}"]


def test_p0_na_janela_respeita_pesado_lock(amb):
    (pasta_app()).mkdir(parents=True, exist_ok=True)
    (pasta_app() / "pesado.lock").write_text(json.dumps(
        {"dono": "outro", "pid": os.getpid(), "desde": 9e18}))
    p0 = criar_pedido(pedido_reel(prioridade="P0", titulo="Gol"))
    amb.ciclo(agora=NOITE)
    assert amb.itens(PEDIDOS) == [p0.name]          # 1 pesado por vez, mesmo P0


def test_janela_proibida_segura_o_p0_se_desligado(amb):
    amb.cfg.p0_na_janela = False
    p0 = criar_pedido(pedido_reel(prioridade="P0", titulo="Gol"))
    r = amb.ciclo(agora=NOITE)
    assert amb.itens(PEDIDOS) == [p0.name]
    assert r["adiados_pesado"] == [f"{PEDIDOS}/{p0.name}"]
    assert "janela proibida" in r["motivo_pesado"]
    assert amb.chamadas == []


def test_janela_deixa_o_leve_andar(amb):
    reel = criar_pedido(pedido_reel())
    amb.ciclo()  # de manhã: vai até a revisão
    rev = amb.pasta(REVISAO) / reel.name
    (rev / "aprovado.json").write_text(json.dumps({"notas": {"gancho": 9}}))
    est = criar_pedido(pedido_carrossel())
    novo = criar_pedido(pedido_reel(titulo="Outro"))
    r = amb.ciclo(agora=NOITE)
    # leves: aprovação, agendamento e estático (arte) andam às 19h
    assert amb.itens(AGENDADOS) == [reel.name]
    assert amb.itens(REVISAO) == [est.name]
    # pesado (download do reel novo) espera
    assert amb.itens(PEDIDOS) == [novo.name]
    assert r["adiados_pesado"] == [f"{PEDIDOS}/{novo.name}"]


def test_22h30_libera(amb):
    item = criar_pedido(pedido_reel())
    amb.ciclo(agora=datetime(2026, 9, 30, 22, 29))
    assert amb.itens(PEDIDOS) == [item.name]
    amb.ciclo(agora=datetime(2026, 9, 30, 22, 30))
    assert amb.itens(REVISAO) == [item.name]


def test_pesado_lock_ocupado_por_outro_programa(amb):
    trava = pasta_app() / "pesado.lock"
    trava.parent.mkdir(parents=True, exist_ok=True)
    # dono vivo (este próprio processo) e recente: ninguém pode pegar
    trava.write_text(json.dumps({"dono": "cortar.py", "pid": os.getpid(),
                                 "desde": __import__("time").time()}))
    reel = criar_pedido(pedido_reel())
    est = criar_pedido(pedido_carrossel())
    r = amb.ciclo()
    assert amb.itens(PEDIDOS) == [reel.name]
    assert amb.itens(REVISAO) == [est.name]  # leve não precisa da trava
    assert "cortar.py" in r["motivo_pesado"]
    trava.unlink()
    amb.ciclo()
    assert sorted(amb.itens(REVISAO)) == sorted([reel.name, est.name])


def test_trava_do_pesado_e_solta_depois(amb):
    criar_pedido(pedido_reel())
    amb.ciclo()
    assert not (pasta_app() / "pesado.lock").exists()


def test_um_vigia_por_vez(amb):
    trava = amb.cfg.trava_vigia
    trava.write_text(json.dumps({"dono": "esteira:vigia", "pid": os.getpid(),
                                 "desde": __import__("time").time()}))
    criar_pedido(pedido_reel())
    r = amb.ciclo()
    assert r.get("ocupado") is True and amb.chamadas == []
    trava.unlink()
    assert "executados" in amb.ciclo()


def test_estatico_nao_e_pesado(amb):
    est = criar_pedido(pedido_carrossel())
    reel = criar_pedido(pedido_reel())
    e = amb.esteira()
    assert e.trabalhos[PEDIDOS].eh_pesado(est) is False
    assert e.trabalhos[PEDIDOS].eh_pesado(reel) is True
    assert e.trabalhos[REVISAO].eh_pesado(reel) is False
    assert e.trabalhos[EDICAO].eh_pesado(reel) is True
