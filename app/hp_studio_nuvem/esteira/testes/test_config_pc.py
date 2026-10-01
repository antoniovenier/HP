"""A6 (§3.2): a raiz da esteira é hpbase.pasta_esteira() (esteira_sombra) e pasta_scripts
aponta para 06 Projeto\\scripts quando a pasta existe."""
from hpbase import pasta_esteira, raiz_drive, raiz_local

from esteira.config import Config, carregar_config, pasta_scripts_padrao


def test_raiz_padrao_e_esteira_sombra(monkeypatch):
    monkeypatch.delenv("HP_ESTEIRA_NOME", raising=False)
    cfg = carregar_config()
    assert cfg.raiz == pasta_esteira() == raiz_local() / "esteira_sombra"
    assert cfg.raiz.name != "esteira"                       # a do PC tem outro conteúdo
    monkeypatch.setenv("HP_ESTEIRA_NOME", "esteira_x")
    assert carregar_config().raiz == raiz_local() / "esteira_x"
    assert carregar_config(raiz=raiz_local() / "outra").raiz == raiz_local() / "outra"


def test_pasta_scripts_06_projeto_quando_existe():
    antiga = raiz_drive() / "scripts"
    assert pasta_scripts_padrao() == antiga                  # sem a pasta nova: o antigo
    assert Config(raiz=raiz_local() / "e").pasta_scripts == antiga
    nova = raiz_drive() / "06 Projeto" / "scripts"
    nova.mkdir(parents=True)
    assert pasta_scripts_padrao() == nova
    assert carregar_config().pasta_scripts == nova
    assert Config(raiz=raiz_local() / "e", pasta_scripts=antiga).pasta_scripts == antiga  # explícito vence
