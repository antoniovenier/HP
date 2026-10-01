# -*- coding: utf-8 -*-
"""story_post_lote: o lote REAL de estáticos (chave "interativo", §4.5) e o antigo (item
"story_enquete"), a pergunta que cabe na figurinha (25) sem cortar no escuro, as opções, os itens
do lote e a CLI. Sem rede, sem adb, sem relógio."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
SCRIPTS = AQUI.parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import story_post_lote as spl  # noqa: E402

PC_REAL = SCRIPTS.parent / "tests" / "fixtures" / "pc_real"
LOTE_REAL = PC_REAL / "lote_estaticos_2026-10-01.json"


@pytest.fixture
def lote_real() -> dict:
    return json.loads(LOTE_REAL.read_text(encoding="utf-8"))


def interativo(**kw) -> dict:
    it = {"arquivo": r"H:\HypadoLocal\upload\story_interativo_2026-10-01.jpg",
          "rede": "Instagram @hpgta6 (compartilhar no Facebook)", "horario": "16:00",
          "figurinha": "enquete", "pergunta": "Furacão chegando em Leonida. O que você faz?",
          "opcoes": ["Vou ver de perto", "Fujo pro outro lado"], "destaque": "Enquetes"}
    it.update(kw)
    return it


def lote(**kw) -> dict:
    return {"data": "2026-10-01", "interativo": interativo(**kw)}


def antigo(pergunta="Vai comprar no 1º dia?", opcoes=("Sim", "Não"), **kw) -> dict:
    item = {"tipo": "story_enquete", "canal": "gta", "arquivo": "arte_enquete_0930.png",
            "pergunta": pergunta, "opcoes": list(opcoes), "caixa_enquete": [540, 1650], **kw}
    return {"dia": "2026-09-30", "itens": [{"tipo": "carrossel", "arquivo": "x.png"}, item]}


# ===========================================================================
# 1. lote real
# ===========================================================================
def test_ler_interativo_do_lote_real(lote_real):
    it = spl.ler_interativo(lote_real)
    assert it["formato"] == "real" and it["figurinha"] == "enquete"
    assert it["arquivo"] == r"H:\HypadoLocal\upload\story_interativo_2026-10-01.jpg"
    assert it["horario"] == "16:00" and it["destaque"] == "Enquetes" and it["data"] == "2026-10-01"
    assert it["conta"] == "hpgta6" and it["canal"] == "gta" and it["compartilhar_facebook"] is True
    assert it["pergunta"] == "Furacão chegando em Leonida. O que você faz?" and it["pergunta_curta"] is None
    assert it["opcoes"] == ["Vou ver de perto", "Fujo pro outro lado"]
    assert it["quem_manda"] == "hypado-resumo-7h (item 4) em 01/10"
    # pelo caminho do arquivo dá o mesmo
    assert spl.ler_interativo(LOTE_REAL) == it


def test_lote_real_pergunta_vira_o_que_voce_faz(lote_real):
    it = spl.ler_interativo(lote_real)
    assert len(it["pergunta"]) > 25
    assert spl.pergunta_da_figurinha(it) == "O que você faz?"
    assert spl.decidir_pergunta(it) == ("O que você faz?", "ultima_oracao")
    assert spl.opcoes_da_figurinha(it) == ["Vou ver de perto", "Fujo pro outro lado"]


def test_decidir_lote_real_devolve_tudo(lote_real):
    d = spl.decidir(lote_real)
    assert d["pergunta"] == "O que você faz?" and d["origem_pergunta"] == "ultima_oracao"
    assert d["pergunta_completa"] == "Furacão chegando em Leonida. O que você faz?"
    assert d["opcoes"] == ["Vou ver de perto", "Fujo pro outro lado"]
    assert d["arte"].endswith("story_interativo_2026-10-01.jpg") and d["horario"] == "16:00"
    assert d["destaque"] == "Enquetes" and d["conta"] == "hpgta6" and d["canal"] == "gta"
    assert d["compartilhar_facebook"] is True and d["formato"] == "real" and d["caixa_enquete"] is None


def test_pergunta_curta_vence_quando_cabe():
    it = interativo(pergunta_curta="Furacão: o que você faz?")
    assert spl.decidir_pergunta(it) == ("Furacão: o que você faz?", "pergunta_curta")
    # pergunta_curta grande demais -> cai para o encurtador da pergunta completa
    it = interativo(pergunta_curta="Com o furacão chegando, o que você faz?")
    assert spl.decidir_pergunta(it) == ("O que você faz?", "ultima_oracao")
    # pergunta_curta grande e sem pergunta completa -> recusa citando a curta
    with pytest.raises(spl.PerguntaImpossivel, match="pergunta_curta.*máximo 25"):
        spl.decidir_pergunta(interativo(pergunta=None, pergunta_curta="Com o furacão chegando, o que você faz?"))


# ===========================================================================
# 2. encurtar_pergunta: determinística, nunca no meio de palavra
# ===========================================================================
def test_acentos_preservados():
    assert spl.encurtar_pergunta("Você já viu o trailer? Lúcia ou Jason, quem é você?") == "Você já viu o trailer?"
    assert spl.encurtar_pergunta("Coração ou razão?") == "Coração ou razão?"
    assert spl.encurtar_pergunta("Ação em Leonida. Vai de avião?") == "Vai de avião?"


def test_emoji_sai_da_pergunta_e_das_opcoes():
    assert spl.encurtar_pergunta("O que você faz? 😱🌀") == "O que você faz?"
    assert spl.encurtar_pergunta("🌀 Furacão em Leonida 🌴. O que você faz? 🤔") == "O que você faz?"
    assert spl.opcoes_da_figurinha(interativo(opcoes=["Vou ver de perto 👀", "Fujo 🏃"])) == \
        ["Vou ver de perto", "Fujo"]


def test_pontuacao_aspas_e_interrogacoes_repetidas():
    assert spl.encurtar_pergunta("Bora pro Leonida?!") == "Bora pro Leonida?"
    assert spl.encurtar_pergunta("O que você faz???") == "O que você faz?"
    assert spl.encurtar_pergunta("“Vai de moto ou de carro?”") == "Vai de moto ou de carro?"
    assert spl.encurtar_pergunta("  O  que   você faz ?  ") == "O que você faz?"
    assert spl.encurtar_pergunta("Furacão chegando… O que você faz?") == "O que você faz?"


def test_tira_vocativo_e_introducao():
    assert spl.encurtar_pergunta("Galera, o que você faz?") == "O que você faz?"
    assert spl.encurtar_pergunta("Me conta: vai jogar no dia 1?") == "Vai jogar no dia 1?"
    assert spl.encurtar_pergunta("E aí, galera, Lúcia ou Jason?") == "Lúcia ou Jason?"
    assert spl.encurtar_pergunta("Pergunta do dia: o que você faz primeiro?") == "O que você faz primeiro?"
    assert spl.encurtar_pergunta("O que você faz, hein?") == "O que você faz?"
    assert spl.encurtar_pergunta("Vai jogar no dia 1, galera?") == "Vai jogar no dia 1?"
    # nome próprio antes da vírgula NÃO é vocativo: fica, e a última oração resolve
    assert spl.encurtar_pergunta("Leonida, a nova cidade. O que você faz?") == "O que você faz?"
    assert spl.sem_vocativo("Leonida, você vai?") == "Leonida, você vai?"


def test_prefere_a_ultima_oracao_com_interrogacao():
    assert spl.encurtar_pergunta("Vai jogar no dia 1? Ou espera?") == "Ou espera?"
    assert spl.encurtar_pergunta("Furacão chegando em Leonida. O que você faz?") == "O que você faz?"
    # a última não cabe -> a anterior com "?"
    assert spl.encurtar_pergunta("Você já viu? Qual cidade você prefere: Vice City ou Leonida?") == "Você já viu?"
    assert spl.decidir_pergunta_texto("Você já viu? Qual cidade você prefere: Vice City ou Leonida?") == \
        ("Você já viu?", "oracao_anterior")
    # cabe inteira -> inteira (sem mexer)
    assert spl.decidir_pergunta_texto("Vai jogar no dia 1?") == ("Vai jogar no dia 1?", "inteira")


def test_nunca_corta_no_meio_de_palavra_e_e_deterministica():
    pergunta = "Qual vai ser o preço do GTA 6 no Brasil?"
    for texto, _ in spl.candidatos(pergunta):
        assert all(len(t) <= 40 for t in texto.split()) and not texto.endswith(" ")
        assert texto in pergunta or texto == spl.sem_vocativo(texto)
    assert spl.candidatos(pergunta) == spl.candidatos(pergunta)
    assert spl.candidatos("Galera, o que você faz? Sério?") == spl.candidatos("Galera, o que você faz? Sério?")


def test_impossivel_recusa_com_explicacao():
    with pytest.raises(spl.PerguntaImpossivel) as e:
        spl.encurtar_pergunta("Qual vai ser o preço do GTA 6 no Brasil?")
    msg = str(e.value)
    assert "40 caracteres" in msg and "máximo 25" in msg and "pergunta_curta" in msg
    assert "Qual vai ser o preço do GTA 6 no Brasil?" in msg and "não corto" in msg.lower()
    # sem "?" nenhum e longa: também impossível (não inventa corte)
    with pytest.raises(spl.PerguntaImpossivel):
        spl.encurtar_pergunta("Diga o que você faria com um furacão chegando em Leonida")
    with pytest.raises(spl.PerguntaImpossivel, match="não tem pergunta"):
        spl.encurtar_pergunta("   ")
    with pytest.raises(spl.PerguntaImpossivel, match="não tem 'pergunta'"):
        spl.decidir_pergunta({"opcoes": ["a", "b"]})


def test_limite_diferente_de_25():
    assert spl.encurtar_pergunta("Furacão chegando em Leonida. O que você faz?", limite=15) == "O que você faz?"
    with pytest.raises(spl.PerguntaImpossivel, match="máximo 14"):
        spl.encurtar_pergunta("Furacão chegando em Leonida. O que você faz?", limite=14)
    assert spl.encurtar_pergunta("Furacão chegando em Leonida. O que você faz?", limite=60) == \
        "Furacão chegando em Leonida. O que você faz?"


# ===========================================================================
# 3. opções
# ===========================================================================
def test_opcoes_2_e_4_valem():
    assert spl.opcoes_da_figurinha(interativo(opcoes=["Sim", "Não"])) == ["Sim", "Não"]
    quatro = ["Vice City", "Leonida", "Port Gellhorn", "Ambrosia"]
    assert spl.opcoes_da_figurinha(interativo(opcoes=quatro)) == quatro


@pytest.mark.parametrize("opcoes", [["Só uma"], ["a", "b", "c", "d", "e"], [], None, "Sim"])
def test_opcoes_1_ou_5_recusadas(opcoes):
    with pytest.raises(spl.OpcoesInvalidas, match="2 a 4 opções|não tem 'opcoes'"):
        spl.opcoes_da_figurinha(interativo(opcoes=opcoes))


def test_opcao_longa_vazia_ou_repetida_recusada():
    with pytest.raises(spl.OpcoesInvalidas) as e:
        spl.opcoes_da_figurinha(interativo(opcoes=["Vou ver de perto", "Fujo pro outro lado correndo muito"]))
    assert "opção 2 tem 34 caracteres (máximo 25)" in str(e.value) and "não corto" in str(e.value)
    with pytest.raises(spl.OpcoesInvalidas, match="opção 1 está vazia"):
        spl.opcoes_da_figurinha(interativo(opcoes=["  ", "Fujo"]))
    with pytest.raises(spl.OpcoesInvalidas, match="repetida"):
        spl.opcoes_da_figurinha(interativo(opcoes=["Sim", "sim"]))
    assert spl.opcoes_da_figurinha(interativo(opcoes=["Fujo pro outro lado", "x"]), limite=19) == \
        ["Fujo pro outro lado", "x"]
    with pytest.raises(spl.OpcoesInvalidas, match="máximo 18"):
        spl.opcoes_da_figurinha(interativo(opcoes=["Fujo pro outro lado", "x"]), limite=18)


# ===========================================================================
# 4. formato antigo (rodada 1), lote sem interativo, itens do lote
# ===========================================================================
def test_formato_antigo_story_enquete():
    it = spl.ler_interativo(antigo())
    assert it["formato"] == "rodada1" and it["pergunta"] == "Vai comprar no 1º dia?"
    assert it["opcoes"] == ["Sim", "Não"] and it["caixa_enquete"] == [540, 1650]
    assert it["canal"] == "gta" and it["conta"] is None and it["arquivo"] == "arte_enquete_0930.png"
    assert it["data"] == "2026-09-30" and it["destaque"] is None and it["figurinha"] == "enquete"
    d = spl.decidir(antigo())
    assert d["pergunta"] == "Vai comprar no 1º dia?" and d["origem_pergunta"] == "inteira"
    # lista pura e item solto também valem
    assert spl.ler_interativo(antigo()["itens"])["pergunta"] == "Vai comprar no 1º dia?"
    assert spl.ler_interativo(antigo()["itens"][1])["formato"] == "rodada1"


def test_lote_sem_interativo_e_lote_ruim(tmp_path):
    assert spl.ler_interativo({"data": "2026-10-01", "stories": []}) is None
    assert spl.ler_interativo([{"tipo": "carrossel"}]) is None
    with pytest.raises(spl.LoteInvalido, match="não tem a chave 'interativo'"):
        spl.decidir({"data": "2026-10-01"})
    with pytest.raises(spl.LoteInvalido, match="não é enquete"):
        spl.decidir(lote(figurinha="quiz"))
    with pytest.raises(spl.LoteInvalido, match="não encontrado"):
        spl.ler_interativo(tmp_path / "nada.json")
    ruim = tmp_path / "ruim.json"
    ruim.write_text("{", encoding="utf-8")
    with pytest.raises(spl.LoteInvalido, match="ilegível"):
        spl.ler_interativo(ruim)
    com_bom = tmp_path / "bom.json"
    com_bom.write_text("\ufeff" + json.dumps(lote(), ensure_ascii=False), encoding="utf-8")
    assert spl.ler_interativo(com_bom)["conta"] == "hpgta6"


def test_itens_do_lote_real(lote_real):
    itens = spl.itens_do_lote(lote_real)
    assert [(i["tipo"], i["hora"]) for i in itens] == [
        ("story", "09:00"), ("threads", "09:00"), ("comunidade_youtube", "10:00"), ("story", "12:10"),
        ("carrossel", "15:00"), ("interativo", "16:00")]
    s1, s2 = itens[0], itens[3]
    assert s1["arquivo"].endswith("0900_contagem.jpg") and s1["tema"] == "contagem 49 dias"
    assert s1["novo_video"] is False and s2["novo_video"] is True
    assert s2["video_titulo"] == "Dá pra ficar GORDO no GTA 6"
    # instagram/facebook são texto livre de status, não objeto
    assert s1["status"]["instagram"].startswith("na fila da API (publicador_meta) para 01/10 09:00")
    assert s1["status"]["facebook"].startswith("programado 01/10 09:00")
    car = itens[4]
    assert car["tema"].startswith("Linha do tempo") and car["arquivos"].endswith("01-09.jpg")
    assert car["spec"].endswith("carrossel_spec_2026-10-01.json") and car["legenda"].startswith("1.749 dias")
    assert car["status"] == {"instagram": "na fila da API para 01/10 15:00 — id gta_2026-10-01_ig_carrossel",
                             "facebook": "programado 01/10 15:00 (Planner do Business Suite conferido, so Pagina, 9 imagens)",
                             "tiktok": "pausado (modo recuperação até 02/10)"}
    assert itens[1]["texto"].startswith("Faltam 49 dias") and "id gta_2026-10-01_th_texto_0900" in itens[1]["status"]["status"]
    assert itens[5]["pergunta"].startswith("Furacão") and itens[5]["rede"].startswith("Instagram @hpgta6")


def test_itens_do_lote_formato_antigo():
    itens = spl.itens_do_lote(antigo())
    assert [i["tipo"] for i in itens] == ["carrossel", "story_enquete"]
    assert itens[1]["pergunta"] == "Vai comprar no 1º dia?" and itens[1]["hora"] is None


def test_traduzir_caminho_pc(monkeypatch, tmp_path):
    monkeypatch.setenv("HP_LOCAL", str(tmp_path / "L"))
    monkeypatch.setenv("HP_DRIVE", str(tmp_path / "D"))
    assert spl.traduzir_caminho_pc(r"H:\HypadoLocal\upload\story.jpg") == tmp_path / "L" / "upload" / "story.jpg"
    assert spl.traduzir_caminho_pc("h:/hypadolocal/upload/story.jpg") == tmp_path / "L" / "upload" / "story.jpg"
    assert spl.traduzir_caminho_pc(r"G:\Meu Drive\Hypado\lotes\a.json") == tmp_path / "D" / "lotes" / "a.json"
    assert spl.traduzir_caminho_pc("arte.png") == Path("arte.png")
    assert spl.traduzir_caminho_pc(r"H:\Outra\x.jpg") == Path(r"H:\Outra\x.jpg")
    assert spl.conta_do_texto("Instagram @HP.Futebol. (compartilhar)") == "hp.futebol"
    assert spl.conta_do_texto("Instagram") is None


# ===========================================================================
# 5. CLI
# ===========================================================================
def test_cli_lote_real_imprime_a_decisao(capsys):
    assert spl.main([str(LOTE_REAL)]) == 0
    out = capsys.readouterr().out
    assert "pergunta na figurinha (15/25): O que você faz?" in out and "[última oração com ?]" in out
    assert "Vou ver de perto (16) | Fujo pro outro lado (19)" in out and "@hpgta6" in out
    assert "12:10 story: vídeo novo: Dá pra ficar GORDO no GTA 6" in out
    assert "tiktok: pausado (modo recuperação até 02/10)" in out
    assert spl.main([str(LOTE_REAL), "--json"]) == 0
    dados = json.loads(capsys.readouterr().out)
    assert dados["decisao"]["pergunta"] == "O que você faz?" and len(dados["itens"]) == 6


def test_cli_impossivel_e_lote_ruim(tmp_path, capsys):
    arq = tmp_path / "2026-10-02_estaticos.json"
    arq.write_text(json.dumps(lote(pergunta="Qual vai ser o preço do GTA 6 no Brasil?"), ensure_ascii=False),
                   encoding="utf-8")
    assert spl.main([str(arq)]) == 1
    out = capsys.readouterr().out
    assert out.startswith("NÃO DÁ:") and "pergunta_curta" in out
    arq.write_text(json.dumps(lote(opcoes=["Só uma"]), ensure_ascii=False), encoding="utf-8")
    assert spl.main([str(arq)]) == 1 and "2 a 4 opções" in capsys.readouterr().out
    assert spl.main([str(tmp_path / "nada.json")]) == 1 and "não encontrado" in capsys.readouterr().out
    # com --limite maior a mesma pergunta passa
    arq.write_text(json.dumps(lote(pergunta="Qual vai ser o preço do GTA 6 no Brasil?"), ensure_ascii=False),
                   encoding="utf-8")
    assert spl.main([str(arq), "--limite", "40"]) == 0
    assert "(40/40): Qual vai ser o preço do GTA 6 no Brasil?" in capsys.readouterr().out
