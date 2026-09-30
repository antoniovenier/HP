"""Validação dura: cabeçalho *Claude - *, tipo, grupo, anexos → rejeitadas\\."""
import json
import unicodedata

import pytest

from hpbase import raiz_local
from whatsapp_local.config import GRUPO_COMISSAO, PREFIXO, carregar_grupos_permitidos, pasta_fila
from whatsapp_local.enviador import Enviador
from whatsapp_local.navegador_falso import NavegadorFalso
from whatsapp_local.validacao import validar_mensagem

from .auxiliares import GRUPO_GTA, fabrica_de, fabrica_proibida, nova_msg


@pytest.mark.parametrize("texto", [
    "Claude - oi",                 # sem os asteriscos
    " *Claude - * oi",             # espaço antes
    "*claude - * oi",              # minúscula
    "*Claude -* oi",               # sem o espaço de dentro
    "oi *Claude - *",              # no fim
    "*Claude - *",                 # nada depois
    "*Claude - *    ",
])
def test_texto_sem_cabecalho_exato_e_rejeitado(texto, grupos):
    motivos = validar_mensagem(nova_msg(texto=texto), carregar_grupos_permitidos())
    assert motivos and any("Claude" in m or "vazio" in m for m in motivos)


def test_texto_com_cabecalho_exato_passa(grupos):
    assert validar_mensagem(nova_msg(texto=f"{PREFIXO} Tudo certo"), carregar_grupos_permitidos()) == []


@pytest.mark.parametrize("tipo", ["promo", "afiliados", "", None, "NO_AR"])
def test_tipo_fora_dos_3_e_rejeitado(tipo, grupos):
    motivos = validar_mensagem(nova_msg(tipo=tipo), carregar_grupos_permitidos())
    assert any("tipo" in m for m in motivos)


@pytest.mark.parametrize("tipo", ["resumo_dia", "no_ar", "resumo_sabado"])
def test_os_3_tipos_permitidos_passam(tipo, grupos):
    assert validar_mensagem(nova_msg(tipo=tipo), carregar_grupos_permitidos()) == []


def test_grupo_fora_da_lista_e_rejeitado(grupos):
    motivos = validar_mensagem(nova_msg(grupo="HP | Outro Grupo"), carregar_grupos_permitidos())
    assert any("fora da lista" in m for m in motivos)


def test_contato_individual_rejeitado_mesmo_se_estiver_na_lista(grupos):
    assert "+55 11 91234-5678" in carregar_grupos_permitidos()   # o Antônio errou a lista
    motivos = validar_mensagem(nova_msg(grupo="+55 11 91234-5678"), carregar_grupos_permitidos())
    assert any("contato individual" in m for m in motivos)


def test_comissao_sempre_permitida_e_nome_normalizado_nfc():
    # sem grupos_permitidos.json: só a Comissão
    assert carregar_grupos_permitidos() == [GRUPO_COMISSAO]
    nfd = unicodedata.normalize("NFD", GRUPO_COMISSAO)
    assert nfd != GRUPO_COMISSAO
    assert validar_mensagem(nova_msg(grupo=nfd), carregar_grupos_permitidos()) == []


def test_grupo_da_lista_do_antonio_passa(grupos):
    assert validar_mensagem(nova_msg(grupo=GRUPO_GTA), carregar_grupos_permitidos()) == []


def test_anexo_que_nao_existe_e_rejeitado(grupos, tmp_path):
    motivos = validar_mensagem(nova_msg(anexos=[str(tmp_path / "nao.jpg")]), carregar_grupos_permitidos())
    assert any("anexo não encontrado" in m for m in motivos)
    capa = raiz_local() / "capas" / "capa.jpg"
    capa.parent.mkdir(parents=True)
    capa.write_bytes(b"jpg")
    assert validar_mensagem(nova_msg(anexos=["capas/capa.jpg"]), carregar_grupos_permitidos()) == []


def test_ciclo_move_invalidas_para_rejeitadas_com_motivo(grupos, enfileirar, relogio):
    enfileirar(ident="ruim_grupo", grupo="Família")
    enfileirar(ident="ruim_tipo", tipo="propaganda")
    enfileirar(ident="ruim_texto", texto="Oi pessoal")
    (pasta_fila() / "quebrado.json").write_text("{isso não é json", encoding="utf-8")
    res = Enviador(fabrica_navegador=fabrica_proibida, relogio=relogio).ciclo("sombra")
    assert res.rejeitadas == 4 and res.sombra == 0
    rej = pasta_fila() / "rejeitadas"
    for ident, pedaco in (("ruim_grupo", "fora da lista"), ("ruim_tipo", "tipo"),
                          ("ruim_texto", "Claude")):
        dados = json.loads((rej / f"{ident}.json").read_text(encoding="utf-8"))
        assert pedaco in dados["motivo_rejeicao"] and dados["rejeitada_em"]
    assert (rej / "quebrado.json").exists()
    assert "JSON inválido" in json.loads((rej / "quebrado.motivo.json").read_text(encoding="utf-8"))["motivo_rejeicao"]
    assert list(pasta_fila().glob("*.json")) == []


def test_em_modo_real_invalida_nem_chega_no_navegador(grupos, enfileirar, relogio, cfg_real):
    enfileirar(ident="ruim", grupo="Família")
    nav = NavegadorFalso({"Família": []})
    res = Enviador(cfg_real, fabrica_de(nav), relogio).ciclo("real", ler_todos_grupos=False)
    assert res.rejeitadas == 1
    assert nav.chamadas == []           # nem abriu a janela
    assert nav.enviadas == []
