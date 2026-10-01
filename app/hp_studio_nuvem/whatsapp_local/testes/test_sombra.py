"""Modo sombra: só monta e compara com o plantão; o navegador nunca abre."""
import json
import sys

import pytest

from hpbase import escrever_json
from whatsapp_local import cli, executar
from whatsapp_local import navegador_playwright as npw
from whatsapp_local.config import (GRUPO_COMISSAO, PREFIXO, arquivo_config, pasta_fila,
                                   pasta_sombra_app, pasta_sombra_plantao,
                                   pasta_sombra_relatorios)
from whatsapp_local.enviador import Enviador
from whatsapp_local.sombra import (carregar_plantao, diferencas, inferir_tipo, parear,
                                   similaridade)

from .auxiliares import fabrica_proibida

TEXTO_APP = (f"{PREFIXO} 🚀 No ar agora — GTA 6 | HP\n\n🎬 Rockstar confirma novidade\n"
             "🕒 18:30\n\nInstagram: https://instagram.com/p/1\nTikTok: https://tiktok.com/p/1")
TEXTO_PLANTAO = (f"{PREFIXO} 🚀 No ar — GTA 6 | HP\n\n🎬 Rockstar confirma novidade\n"
                 "🕒 18:30\n\nInstagram: https://instagram.com/p/1")


@pytest.fixture
def plantao():
    def _f(nome, texto, **kw):
        escrever_json(pasta_sombra_plantao() / nome,
                      {"grupo": GRUPO_COMISSAO, "tipo": "no_ar", "texto": texto,
                       "enviado_em": "2026-09-30T18:32:00-03:00", **kw})
    return _f


def _relatorio_json():
    return json.loads((pasta_sombra_relatorios() / "2026-09-30.json").read_text(encoding="utf-8"))


def test_sombra_gera_relatorio_de_diferencas(enfileirar, plantao, relogio, capsys):
    enfileirar(ident="no_ar_gta", texto=TEXTO_APP)
    plantao("gta_1830.json", TEXTO_PLANTAO)
    rc = cli.main(["enviar", "--uma-vez", "--sombra"], fabrica_navegador=fabrica_proibida,
                  relogio=relogio)
    assert rc == 0
    assert list(pasta_fila().glob("*.json")) == []                    # saiu da fila
    assert (pasta_sombra_app() / "no_ar_gta.json").exists()          # foi para a sombra
    num = _relatorio_json()
    assert num["total_app"] == 1 and num["total_plantao"] == 1 and len(num["pares"]) == 1
    par = num["pares"][0]
    assert 70 <= par["similaridade"] < 100 and par["veredito"] in ("parecido", "quase igual")
    md = (pasta_sombra_relatorios() / "2026-09-30.md").read_text(encoding="utf-8")
    assert "```diff" in md and "+TikTok: https://tiktok.com/p/1" in md
    assert "-*Claude - * 🚀 No ar — GTA 6 | HP" in md
    assert "%" in md
    assert "sombra: 1" in capsys.readouterr().out


def test_sombra_identica_da_100(enfileirar, plantao, relogio):
    enfileirar(ident="a", texto=TEXTO_APP)
    plantao("a.json", TEXTO_APP + "\n")
    Enviador(fabrica_navegador=fabrica_proibida, relogio=relogio).ciclo("sombra")
    par = _relatorio_json()["pares"][0]
    assert par["similaridade"] == 100.0 and par["veredito"] == "idêntico"
    assert "Sem diferença." in (pasta_sombra_relatorios() / "2026-09-30.md").read_text(encoding="utf-8")


def test_sombra_lista_quem_ficou_sem_par(enfileirar, plantao, relogio):
    enfileirar(ident="a", texto=TEXTO_APP)
    plantao("resumo.json", f"{PREFIXO} 📊 Resumo de terça", tipo="resumo_dia")
    Enviador(fabrica_navegador=fabrica_proibida, relogio=relogio).ciclo("sombra")
    num = _relatorio_json()
    assert num["pares"] == [] and num["sem_par_app"] == ["a"]
    assert num["sem_par_plantao"] == ["resumo.json"]


def test_plantao_em_txt_e_jsonl():
    p = pasta_sombra_plantao()
    p.mkdir(parents=True, exist_ok=True)
    (p / "aviso.txt").write_text(TEXTO_PLANTAO, encoding="utf-8")
    (p / "dia.jsonl").write_text(
        json.dumps({"texto": f"{PREFIXO} Resumo da semana", "enviado_em": "2026-09-26T10:00:00-03:00"},
                   ensure_ascii=False) + "\n", encoding="utf-8")
    itens = {i["origem"]: i for i in carregar_plantao()}
    assert itens["aviso.txt"]["tipo"] == "no_ar"
    assert itens["dia.jsonl#1"]["tipo"] == "resumo_sabado"
    assert str(itens["dia.jsonl#1"]["dia"]) == "2026-09-26"


def test_similaridade_e_pareamento():
    assert similaridade("a\n", "a") == 100.0
    assert similaridade("abc", "xyz") == 0.0
    assert inferir_tipo("*Claude - * Resumo de ontem") == "resumo_dia"
    app = [{"origem": "1", "texto": "no ar: post A link a", "tipo": "no_ar", "grupo": None},
           {"origem": "2", "texto": "no ar: post B link b", "tipo": "no_ar", "grupo": None}]
    pl = [{"origem": "x", "texto": "no ar: post B link b", "tipo": "no_ar", "grupo": None},
          {"origem": "y", "texto": "no ar: post A link a!", "tipo": "no_ar", "grupo": None}]
    pares, sem_a, sem_p = parear(app, pl)
    assert [(a["origem"], p["origem"]) for a, p, _ in pares] == [("1", "y"), ("2", "x")]
    assert not sem_a and not sem_p
    assert diferencas("a\nb", "a\nc").count("\n") >= 3


def test_navegador_real_nunca_e_chamado_em_sombra(enfileirar, relogio, monkeypatch, capsys):
    """Nem o NavegadorPlaywright nem o Playwright podem ser tocados em sombra."""
    def explode(*a, **k):
        raise AssertionError("NavegadorPlaywright chamado em modo sombra!")

    monkeypatch.setattr(npw.NavegadorPlaywright, "__init__", explode)
    monkeypatch.setattr(npw.NavegadorPlaywright, "abrir", explode)
    sys.modules.pop("playwright", None)
    escrever_json(arquivo_config(), {"modo": "sombra"})
    enfileirar(ident="s1")
    # fábrica padrão (a real) em todos os comandos que poderiam abrir a janela
    assert cli.main(["enviar", "--uma-vez"], relogio=relogio) == 0
    enfileirar(ident="s2")
    assert cli.main(["enviar"], relogio=relogio) == 0
    enfileirar(ident="s3")
    assert cli.main(["vigiar", "--ciclos", "2", "--intervalo", "60"], relogio=relogio) == 0
    assert cli.main(["ler-recebidas"], relogio=relogio) == 0
    assert executar({"acao": "enviar"}, relogio=relogio)["ok"] is True
    assert executar({"acao": "ler_recebidas"}, relogio=relogio)["ok"] is True
    assert cli.main(["status"], relogio=relogio) == 0
    assert len(list(pasta_sombra_app().glob("*.json"))) == 3
    assert "playwright" not in sys.modules
    assert "Modo sombra: o navegador não abre" in capsys.readouterr().out


def test_config_invalida_cai_para_sombra():
    escrever_json(arquivo_config(), {"modo": "REAL!!", "intervalo_min_seg": 1})
    from whatsapp_local.config import carregar_config
    cfg = carregar_config()
    assert cfg.modo == "sombra" and cfg.intervalo_min_seg == 20
