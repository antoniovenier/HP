"""Esquema do pedido.json, regras de conteúdo e criação do item."""
import json

import pytest

from esteira.constantes import PEDIDOS
from esteira.erros import PedidoInvalido
from esteira.pedido import (criar_pedido, ler_horario, normalizar_pedido,
                            validar_pedido)
from esteira.testes.conftest import pedido_carrossel, pedido_reel


def erros(**kw):
    return validar_pedido(normalizar_pedido(pedido_reel(**kw)))


def tem(lista, trecho):
    return any(trecho in e for e in lista)


def test_reel_valido_sem_erros():
    assert erros() == []


def test_normalizar_preenche_padroes_e_id():
    p = normalizar_pedido({"canal": "GTA", "tipo": "Reel", "titulo": "Olá Mundo",
                           "redes": "instagram, tiktok", "prioridade": 0,
                           "horario_alvo": "2026-09-30 18:30"})
    assert p["canal"] == "gta" and p["tipo"] == "reel" and p["prioridade"] == "P0"
    assert p["redes"] == ["instagram", "tiktok"]
    assert p["dublar"] is False and p["narrar_toque_hp"] is False
    assert p["observacoes"] == "" and p["arquivos"] == [] and p["fonte_url"] is None
    assert p["id"] == "2026-09-30_1830_gta_ola-mundo"


def test_campos_obrigatorios_faltando():
    e = validar_pedido(normalizar_pedido({"canal": "xbox", "tipo": "video"}))
    for trecho in ("id", "canal", "tipo", "titulo", "redes", "horario_alvo"):
        assert tem(e, trecho), trecho


def test_bool_estrito():
    assert tem(erros(dublar="true"), "dublar tem que ser true ou false")


def test_rede_desconhecida_e_repetida():
    assert tem(erros(redes=["orkut"]), "rede desconhecida")
    assert tem(erros(redes=["instagram", "instagram"]), "repetida")


@pytest.mark.parametrize("campo", ["dublar", "narrar_toque_hp"])
def test_futebol_nunca_com_voz_sintetica(campo):
    e = erros(canal="futebol", fonte_oficial=True, credito="@flamengo", **{campo: True},
              roteiro_narracao={"abertura": "Viu?", "fecho": "E aí?"})
    assert tem(e, "futebol nunca leva voz sintética")


def test_voz_so_em_destinos_receitas_carros_filmes():
    assert not tem(erros(canal="gta", dublar=True), "voz sintética")  # rodada 2: o GTA dubla gringo
    assert tem(erros(canal="futebol", dublar=True), "futebol nunca leva voz sintética")
    for canal in ("destinos", "receitas", "carros", "filmes"):
        assert erros(canal=canal, dublar=True) == [], canal


def test_narracao_pede_roteiro_com_perguntas():
    assert tem(erros(canal="destinos", narrar_toque_hp=True), "roteiro_narracao")
    e = erros(canal="destinos", narrar_toque_hp=True,
              roteiro_narracao={"abertura": "Olha isso.", "fecho": "Iria?"})
    assert tem(e, "abertura tem que ser uma pergunta")
    assert erros(canal="destinos", narrar_toque_hp=True,
                 roteiro_narracao={"abertura": "Já viu isso?", "trecho": "É lindo.",
                                   "fecho": "Você iria?"}) == []


def test_credito_obrigatorio_com_fonte_externa():
    assert tem(erros(credito=""), "crédito obrigatório")
    # arquivos de terceiros também pedem crédito; material próprio não
    base = dict(fonte_url=None, arquivos=["bruto.mp4"], credito="")
    assert tem(erros(**base), "crédito obrigatório")
    assert erros(**base, fonte_propria=True) == []


def test_futebol_so_fonte_oficial():
    e = erros(canal="futebol", credito="@flamengo")
    assert tem(e, "fonte_oficial=true")
    assert erros(canal="futebol", credito="@flamengo", fonte_oficial=True) == []


def test_estatico_nao_tem_voz():
    e = validar_pedido(normalizar_pedido(pedido_carrossel(canal="destinos", dublar=True)))
    assert tem(e, "é estático")


def test_reel_precisa_de_fonte():
    assert tem(erros(fonte_url=None, credito=""), "reel precisa de fonte_url ou arquivos")


def test_regras_de_redes_por_tipo_e_canal():
    assert tem(erros(redes=["pinterest"]), "pinterest só em receitas")
    story = normalizar_pedido(pedido_carrossel(tipo="story", redes=["instagram", "tiktok"]))
    assert tem(validar_pedido(story), "story só vai para instagram e facebook")
    car = normalizar_pedido(pedido_carrossel(redes=["youtube"]))
    assert tem(validar_pedido(car), "youtube só recebe reel")


def test_threads_texto():
    base = pedido_carrossel(tipo="threads_texto", redes=["threads"], texto="Oi, gente")
    assert validar_pedido(normalizar_pedido(base)) == []
    assert tem(validar_pedido(normalizar_pedido({**base, "redes": ["instagram"]})),
               "só vai para a rede threads")
    assert tem(validar_pedido(normalizar_pedido({**base, "texto": ""})), "precisa do campo texto")
    assert tem(validar_pedido(normalizar_pedido({**base, "texto": "x" * 501})), "500")
    assert tem(validar_pedido(normalizar_pedido({**base, "texto": "Custa R$ 20 mil"})),
               "Valores aproximados")
    ok = {**base, "texto": "Custa R$ 20 mil. Valores aproximados."}
    assert validar_pedido(normalizar_pedido(ok)) == []


def test_flow_games_e_vazamento_de_gta():
    assert tem(erros(observacoes="corte do Flow Games"), "Flow Games")
    assert tem(erros(titulo="GTA 6 vazado: mapa"), "vazamento")
    assert tem(erros(titulo="Leak do GTA 6"), "vazamento")


def test_hashtags_corte_capa():
    assert tem(erros(hashtags=["x"] * 31), "30 hashtags")
    assert tem(erros(corte={"inicio": 5, "fim": 2}), "corte")
    assert tem(erros(capa_tempo=-1), "capa_tempo")


def test_horario_converte_para_brasilia():
    assert ler_horario("2026-09-30T21:30:00Z").strftime("%H%M") == "1830"
    assert ler_horario("2026-09-30 18:30").strftime("%H%M") == "1830"


def test_criar_pedido_cria_pasta_com_nome_certo(amb):
    item = criar_pedido(pedido_reel(titulo="Rockstar: quinta-feira é dia!"))
    assert item.parent == amb.pasta(PEDIDOS)
    assert item.name == "P1_2026-09-30_1830_gta_rockstar-quinta-feira-e-dia"
    dados = json.loads((item / "pedido.json").read_text(encoding="utf-8"))
    assert dados["id"] == item.name[3:] and dados["dublar"] is False
    assert "pedido criado" in (item / "historico.log").read_text(encoding="utf-8")
    assert not list(amb.pasta(PEDIDOS).glob(".criando_*"))


def test_criar_pedido_p0_e_utc():
    item = criar_pedido(pedido_reel(prioridade="P0", titulo="Gol do Mengão",
                                    canal="futebol", fonte_oficial=True,
                                    credito="@flamengo",
                                    horario_alvo="2026-09-30T23:05:00+00:00"))
    assert item.name == "P0_2026-09-30_2005_futebol_gol-do-mengao"


def test_criar_pedido_duplicado_e_invalido(amb):
    criar_pedido(pedido_reel())
    with pytest.raises(PedidoInvalido, match="já existe"):
        criar_pedido(pedido_reel(prioridade="P0"))
    with pytest.raises(PedidoInvalido) as e:
        criar_pedido(pedido_reel(canal="futebol", dublar=True, titulo="Outro"))
    assert any("futebol" in x for x in e.value.erros)
    assert amb.itens(PEDIDOS) == ["P1_2026-09-30_1830_gta_rockstar-quinta"]
