"""Mensagens novas do Antônio → recebidas\\AAAA-MM-DD.jsonl, sem duplicar, sem log do texto."""
import json
import unicodedata

from hpbase import pasta_logs
from whatsapp_local import cli
from whatsapp_local.config import GRUPO_COMISSAO, Config, pasta_recebidas
from whatsapp_local.enviador import Enviador
from whatsapp_local.navegador_falso import NavegadorFalso
from whatsapp_local.recebidas import data_da_hora, e_mensagem_claude, hash_mensagem

from .auxiliares import GRUPO_GTA, fabrica_de, msg_lida

SEGREDO_DO_ANTONIO = "Posta o vídeo do Neymar às 19h, beleza?"


def _linhas(dia="2026-09-30"):
    arq = pasta_recebidas() / f"{dia}.jsonl"
    return [json.loads(l) for l in arq.read_text(encoding="utf-8").splitlines()] if arq.exists() else []


def _conversas():
    return {
        GRUPO_COMISSAO: [
            msg_lida(SEGREDO_DO_ANTONIO, saida=True),                       # do celular dele
            msg_lida("Claude - 📊 Resumo de ontem", saida=True),           # do app (negrito na tela)
            msg_lida("*Claude - * 🚀 No ar", saida=True),
            msg_lida("Bom dia", autor="Fulano", hora="08:00, 30/09/2026"),
        ],
        GRUPO_GTA: [msg_lida("Muda a capa do GTA", hora="09:40, 29/09/2026")],
    }


def test_salva_so_as_novas_e_nunca_as_do_claude(grupos, relogio):
    nav = NavegadorFalso(_conversas())
    cfg = Config(modo="real")
    res = Enviador(cfg, fabrica_de(nav), relogio).ler_recebidas("real")
    assert res.recebidas_novas == 3 and not res.erro
    hoje = _linhas()
    assert [l["texto"] for l in hoje] == [SEGREDO_DO_ANTONIO, "Bom dia"]
    assert hoje[0]["direcao"] == "saida" and hoje[1]["direcao"] == "entrada"
    assert hoje[0]["grupo"] == GRUPO_COMISSAO and hoje[0]["hash"]
    assert [l["texto"] for l in _linhas("2026-09-29")] == ["Muda a capa do GTA"]   # dia da mensagem
    # de novo: nada duplica
    res = Enviador(cfg, fabrica_de(nav), relogio).ler_recebidas("real")
    assert res.recebidas_novas == 0 and len(_linhas()) == 2
    # chega uma nova
    nav.conversas[GRUPO_COMISSAO].append(msg_lida("E o resumo?", hora="10:05, 30/09/2026", saida=True))
    res = Enviador(cfg, fabrica_de(nav), relogio).ler_recebidas("real")
    assert res.recebidas_novas == 1 and len(_linhas()) == 3
    assert "enviar_texto" not in nav.nomes_chamadas()          # nunca responde nada


def test_log_nao_tem_o_texto_do_antonio(grupos, relogio):
    nav = NavegadorFalso(_conversas())
    Enviador(Config(modo="real"), fabrica_de(nav), relogio).ler_recebidas("real")
    log = "".join(p.read_text(encoding="utf-8") for p in pasta_logs().glob("whatsapp_*.log"))
    assert "Neymar" not in log and "Bom dia" not in log
    h = _linhas()[0]["hash"][:12]
    assert f"hash={h}" in log and f"tamanho={len(SEGREDO_DO_ANTONIO)}" in log


def test_grupo_com_cabecalho_errado_nao_e_lido(grupos, relogio):
    nav = NavegadorFalso(_conversas(), titulos={GRUPO_GTA: "Outro grupo"})
    Enviador(Config(modo="real"), fabrica_de(nav), relogio).ler_recebidas("real")
    assert _linhas("2026-09-29") == []            # não salvou mensagens de conversa errada
    assert len(_linhas()) == 2


def test_depois_de_enviar_le_o_grupo(grupos, enfileirar, relogio):
    enfileirar(ident="m1")
    nav = NavegadorFalso(_conversas())
    res = Enviador(Config(modo="real"), fabrica_de(nav), relogio).ciclo("real", ler_todos_grupos=False)
    assert res.enviadas == 1 and res.recebidas_novas == 2      # a própria mensagem enviada não entra
    assert all("No ar agora" not in l["texto"] for l in _linhas())


def test_vigia_le_todos_os_grupos_a_cada_30_min(grupos, relogio):
    nav = NavegadorFalso(_conversas())
    cfg = Config(modo="real", ler_recebidas_a_cada_min=30)
    assert Enviador(cfg, fabrica_de(nav), relogio).ciclo("real").recebidas_novas == 3
    nav.chamadas.clear()
    relogio.avancar(minutes=10)
    Enviador(cfg, fabrica_de(nav), relogio).ciclo("real")
    assert nav.chamadas == []                                   # fila vazia e ainda não é hora
    relogio.avancar(minutes=25)
    Enviador(cfg, fabrica_de(nav), relogio).ciclo("real")
    assert "ler_mensagens" in nav.nomes_chamadas()


def test_ler_recebidas_pela_cli(grupos, relogio, capsys):
    nav = NavegadorFalso(_conversas())
    assert cli.main(["ler-recebidas", "--real"], fabrica_navegador=fabrica_de(nav), relogio=relogio) == 0
    assert "recebidas novas: 3" in capsys.readouterr().out


def test_hash_e_datas():
    nfd = unicodedata.normalize("NFD", "Antônio")
    assert hash_mensagem("G", nfd, "10:00", "oi") == hash_mensagem("G", "Antônio", "10:00", "oi")
    assert hash_mensagem("G", "A", "10:00", "oi") != hash_mensagem("G", "A", "10:01", "oi")
    assert str(data_da_hora("10:32, 30/09/2026")) == "2026-09-30"
    assert data_da_hora("10:32") is None
    assert e_mensagem_claude("*Claude - * x") and e_mensagem_claude("Claude - x")
    assert not e_mensagem_claude("O Claude - disse")
