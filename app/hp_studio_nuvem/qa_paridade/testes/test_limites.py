"""limites.json: padrão, ajuste local e --limites."""
import json

from hpbase import escrever_json, pasta_paridade
from qa_paridade.cli import main
from qa_paridade.limites import PADRAO, carregar_limites
from qa_paridade.relatorio import calcular_veredito
from qa_paridade.util import metrica


def test_padrao_documentado_e_sem_comentarios():
    bruto = json.loads(PADRAO.read_text(encoding="utf-8"))
    assert all("_leia" in v for k, v in bruto.items() if isinstance(v, dict))
    lim = carregar_limites()
    assert "_leia" not in lim and "_leia" not in lim["ssim"]
    assert lim["veredito"] == {"identico": 9.5, "equivalente": 9.0, "nota_minima_metrica": 9.0,
                               "aprovacao_media": 9.5, "aprovacao_minima_metrica": 9.0}
    assert lim["sombra"]["dias_necessarios"] == 7


def test_ajuste_local_mescla_por_cima():
    escrever_json(pasta_paridade() / "limites.json",
                  {"pesos": {"ssim": 5}, "sombra": {"dias_necessarios": 10}})
    lim = carregar_limites()
    assert lim["pesos"]["ssim"] == 5 and lim["pesos"]["duracao"] == 1.0
    assert lim["sombra"]["dias_necessarios"] == 10


def _m(nome, nota):
    return metrica(nome, {"x": nota}, {}, "")


def test_veredito_e_criterio_do_dia():
    lim = carregar_limites()
    tudo10 = {"duracao": _m("duracao", 10), "ssim": _m("ssim", 10)}
    assert calcular_veredito(tudo10, lim)["veredito"] == "IDENTICO"
    # média 9,25 com todas >= 9: EQUIVALENTE, mas não passa no dia (média < 9,5)
    eq = calcular_veredito({"duracao": _m("duracao", 9.5), "ssim": _m("ssim", 9.0)},
                           {**lim, "pesos": {"duracao": 1, "ssim": 1}})
    assert eq["veredito"] == "EQUIVALENTE" and eq["aprovado"] is False
    # média alta mas uma métrica < 9: DIFERENTE e reprovado
    dif = calcular_veredito({"duracao": _m("duracao", 8.5), "ssim": _m("ssim", 10)}, lim)
    assert dif["nota_final"] >= 9.5
    assert dif["veredito"] == "DIFERENTE" and dif["aprovado"] is False
    assert dif["metricas_reprovadas"] == ["duracao"]


def test_limites_pela_cli(midia, tmp_path, capsys):
    frouxo = tmp_path / "frouxo.json"
    frouxo.write_text(json.dumps({"duracao": {"pontos": [[1.0, 10], [3.0, 0]]}}), encoding="utf-8")
    assert main(["video", str(midia["curto"]), str(midia["ref"])], usar_trava=False) == 1
    assert main(["video", str(midia["curto"]), str(midia["ref"]), "--limites", str(frouxo)],
                usar_trava=False) == 0
    capsys.readouterr()
