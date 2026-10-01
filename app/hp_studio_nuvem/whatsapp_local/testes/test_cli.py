"""CLI e gancho do motor."""
import pytest

from hpbase import escrever_json
from whatsapp_local import cli, executar
from whatsapp_local.config import GRUPO_COMISSAO, arquivo_estado, pasta_fila
from whatsapp_local.navegador_falso import NavegadorFalso

from .auxiliares import fabrica_de


def test_ajuda_em_portugues(capsys):
    with pytest.raises(SystemExit) as e:
        cli.main(["--help"])
    assert e.value.code == 0
    out = capsys.readouterr().out
    assert "mostra esta ajuda" in out and "uso:" in out and "montar-no-ar" in out


def test_status(capsys, relogio):
    assert cli.main(["status"], relogio=relogio) == 0
    out = capsys.readouterr().out
    assert "Modo: sombra" in out and "HP | Comissão 🚀" in out and "Fila: 0 pendentes" in out


def test_login_abre_visivel_e_so_espera_o_qr(relogio, capsys):
    nav = NavegadorFalso(esta_logado=False, login_escaneado=True)
    visivel = []
    assert cli.main(["login", "--timeout", "5"], fabrica_navegador=fabrica_de(nav, visivel),
                    relogio=relogio) == 0
    assert visivel == [True]
    assert nav.nomes_chamadas() == ["abrir", "logado", "esperar_login", "fechar"]
    assert "Aparelhos conectados" in capsys.readouterr().out


def test_login_nao_escaneado_devolve_2(relogio):
    nav = NavegadorFalso(esta_logado=False, login_escaneado=False)
    assert cli.main(["login"], fabrica_navegador=fabrica_de(nav), relogio=relogio) == 2


def test_enviar_real_pela_cli_e_codigo_de_login(grupos, enfileirar, relogio):
    enfileirar(ident="m1")
    nav = NavegadorFalso({GRUPO_COMISSAO: []}, esta_logado=False)
    assert cli.main(["enviar", "--uma-vez", "--real"], fabrica_navegador=fabrica_de(nav),
                    relogio=relogio) == 2
    nav.esta_logado = True
    assert cli.main(["enviar", "--uma-vez", "--real"], fabrica_navegador=fabrica_de(nav),
                    relogio=relogio) == 0
    assert (pasta_fila() / "enviadas" / "m1.json").exists()


def test_vigiar_dorme_o_intervalo_entre_ciclos(relogio):
    assert cli.main(["vigiar", "--ciclos", "3", "--intervalo", "60", "--sombra"], relogio=relogio) == 0
    assert relogio.dormidas == [60, 60]


def test_montar_no_ar_pela_cli(tmp_path, relogio, capsys):
    ag = tmp_path / "agendados.json"
    escrever_json(ag, [{"canal": "gta", "titulo": "X", "horario": "2026-09-30T09:30:00-03:00",
                        "links": {"instagram": "https://instagram.com/p/9"}}])
    assert cli.main(["montar-no-ar", str(ag), "--so-mostrar"], relogio=relogio) == 0
    assert "Instagram: https://instagram.com/p/9" in capsys.readouterr().out
    assert list(pasta_fila().glob("*.json")) == []
    assert cli.main(["montar-no-ar", str(tmp_path / "nao.json")], relogio=relogio) == 1


def test_montar_resumo_sem_metricas(relogio, capsys):
    assert cli.main(["montar-resumo"], relogio=relogio) == 1
    assert "Sem métricas" in capsys.readouterr().out


def test_gancho_executar(relogio):
    r = executar({"acao": "status"}, relogio=relogio)
    assert r["ok"] and r["modo"] == "sombra"
    assert executar({"acao": "nao_existe"})["ok"] is False
    r = executar({"acao": "enviar"}, relogio=relogio)
    assert r["ok"] and r["modo"] == "sombra"
    assert arquivo_estado().exists()
