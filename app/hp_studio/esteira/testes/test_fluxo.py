"""Fluxos completos com plugins falsos (nenhum ffmpeg, script ou rede)."""
import json

from hpbase import ler_json

from esteira import acoes
from esteira.constantes import (AGENDADOS, BAIXADOS, EDICAO, ERROS, LEGENDA,
                                PEDIDOS, POSTADOS, REVISAO)
from esteira.erros import ErroEtapa, ErroPermanente
from esteira.pedido import criar_pedido
from esteira.testes.conftest import MANHA, pedido_carrossel, pedido_reel


def historico(p):
    return (p / "historico.log").read_text(encoding="utf-8")


def test_reel_fluxo_completo(amb):
    item = criar_pedido(pedido_reel(redes=["instagram", "threads", "tiktok"]))
    r = amb.ciclo()
    assert r["erros"] == []
    assert amb.itens(REVISAO) == [item.name]
    # passou por todas as etapas de vídeo, na ordem
    etapas = [a.split(":")[0] for a in r["avancaram"]]
    assert etapas == [f"{PEDIDOS} -> {BAIXADOS}", f"{BAIXADOS} -> {LEGENDA}",
                      f"{LEGENDA} -> {EDICAO}", f"{EDICAO} -> {REVISAO}"]
    usados = [c[0] for c in amb.chamadas]
    for plugin in ("baixador", "midia", "legendador", "editor"):
        assert plugin in usados
    assert "dublador" not in usados and "narrador" not in usados

    rev = amb.pasta(REVISAO) / item.name
    for q in ("quadro_1_inicio.jpg", "quadro_2_meio.jpg", "quadro_3_fim.jpg"):
        assert (rev / "revisao" / q).exists()
    texto = (rev / "texto_revisao.md").read_text(encoding="utf-8")
    assert "Rodada: 1" in texto and "aprovado.json" in texto and "1080x1920" in texto
    post = ler_json(rev / "post.json")
    assert post["conta"] == "@hpgta6" and post["arquivos"] == ["final.mp4"]
    assert "Crédito: @rockstargames" in post["legenda"]

    # revisor aprova (só as notas: o app calcula média e veredito)
    (rev / "aprovado.json").write_text(json.dumps({"notas": {"gancho": 9, "legenda": 9,
                                                             "audio": 8}}))
    r = amb.ciclo()
    ag = amb.pasta(AGENDADOS) / item.name
    assert ag.exists()
    decisao = ler_json(ag / "revisao" / "decisao_rodada_1.json")
    assert decisao["media"] == 8.67 and decisao["veredito"] == "Bom"
    # API confirmou (sombra); TikTok espera o Claude
    conf = ler_json(ag / "confirmacoes.json")
    assert set(conf) == {"instagram", "threads"}
    assert any("tiktok (tiktok_ok.json)" in a for a in r["aguardando"])
    amb.ciclo()
    assert ag.exists()  # continua esperando

    (ag / "tiktok_ok.json").write_text(json.dumps({"link": "https://tiktok.com/@hpgta6/1"}))
    amb.ciclo()
    fim = amb.pasta(POSTADOS) / item.name
    assert fim.exists() and not ag.exists()
    aviso = ler_json(fim / "aviso_no_ar.json")
    assert aviso["status"] == "sombra"
    msg = aviso["mensagem"]
    assert msg["texto"].startswith("*Claude - *") and msg["grupo"] == "HP | Comissão 🚀"
    assert msg["tipo"] == "no_ar" and msg["anexos"] == [] and "criado_em" in msg
    assert "https://tiktok.com/@hpgta6/1" in msg["texto"]
    # modo sombra: nada na fila de verdade
    assert not (amb.cfg.whatsapp_fila).exists() or not list(amb.cfg.whatsapp_fila.iterdir())
    assert len(list((amb.cfg.pasta_sombra / "whatsapp_fila").glob("*.json"))) == 1
    h = historico(fim)
    for trecho in ("pedido criado", "-> 02_baixados", "-> 05_revisao", "-> 06_agendados",
                   "aguardando: tiktok", "-> 07_postados", "aviso 'no ar'"):
        assert trecho in h, trecho
    # aviso sai uma vez só
    amb.ciclo()
    assert len(list((amb.cfg.pasta_sombra / "whatsapp_fila").glob("*.json"))) == 1


def test_reel_com_dublagem_e_narracao(amb):
    item = criar_pedido(pedido_reel(canal="destinos", dublar=True, narrar_toque_hp=True,
                                    roteiro_narracao={"abertura": "Já foi a Gramado?",
                                                      "fecho": "Você iria?"}))
    amb.ciclo()
    usados = [c[0] for c in amb.chamadas]
    assert "dublador" in usados and "narrador" in usados
    assert "dublagem ok; narração Toque HP ok" in historico(amb.pasta(REVISAO) / item.name)


def test_estatico_pula_etapas_de_video(amb):
    item = criar_pedido(pedido_carrossel())
    r = amb.ciclo()
    assert r["avancaram"][0].startswith(f"{PEDIDOS} -> {EDICAO}")
    assert amb.itens(REVISAO) == [item.name]
    usados = {c[0] for c in amb.chamadas}
    assert "baixador" not in usados and "legendador" not in usados and "editor" not in usados
    assert "designer" in usados
    rev = amb.pasta(REVISAO) / item.name
    post = ler_json(rev / "post.json")
    assert post["arquivos"] == ["arte/arte_01.png", "arte/arte_02.png", "arte/arte_03.png"]
    assert post["capa"] == "arte/arte_01.png"
    assert len(list((rev / "revisao").glob("quadro_*.jpg"))) == 3
    assert "pula as etapas de vídeo" in historico(rev)
    acoes.aprovar(item.name, {"arte": 9, "texto_post": 9}, cfg=amb.cfg, plugins=amb.plugins,
                  agora=MANHA)
    amb.ciclo()
    ag = amb.pasta(AGENDADOS) / item.name
    assert "pinterest (pinterest_ok.json)" in ler_json(ag / "estado.json")["aguardando"]
    acoes.confirmar(item.name, "pinterest", "https://pin.it/x", cfg=amb.cfg,
                    plugins=amb.plugins, agora=MANHA)
    amb.ciclo()
    assert amb.itens(POSTADOS) == [item.name]


def test_threads_texto(amb):
    item = criar_pedido(pedido_carrossel(tipo="threads_texto", redes=["threads"],
                                         texto="Qual carro você levaria?", canal="carros"))
    amb.ciclo()
    rev = amb.pasta(REVISAO) / item.name
    assert (rev / "texto_threads.txt").read_text(encoding="utf-8").startswith("Qual carro")
    assert ler_json(rev / "post.json")["legenda"] == "Qual carro você levaria?"


def test_p0_fura_a_fila(amb):
    p1a = criar_pedido(pedido_reel(titulo="Cedo", horario_alvo="2026-09-30T08:00:00-03:00"))
    p1b = criar_pedido(pedido_reel(titulo="Tarde", horario_alvo="2026-09-30T15:00:00-03:00"))
    p2 = criar_pedido(pedido_reel(titulo="Programado", prioridade="P2",
                                  horario_alvo="2026-09-30T07:00:00-03:00"))
    p0 = criar_pedido(pedido_reel(titulo="Gol agora", prioridade="P0", canal="futebol",
                                  fonte_oficial=True, credito="@flamengo",
                                  horario_alvo="2026-09-30T23:50:00-03:00"))
    r = amb.ciclo(max_trabalhos=1)
    assert r["executados"] == [f"{PEDIDOS}/{p0.name}"]
    assert amb.itens(BAIXADOS) == [p0.name]
    assert set(amb.itens(PEDIDOS)) == {p1a.name, p1b.name, p2.name}


def test_p0_faixa_expressa_anda_antes_de_qualquer_p1(amb):
    criar_pedido(pedido_reel(titulo="Cedo", horario_alvo="2026-09-30T08:00:00-03:00"))
    p0 = criar_pedido(pedido_reel(titulo="Placar", prioridade="P0",
                                  horario_alvo="2026-09-30T21:00:00-03:00"))
    amb.ciclo()
    itens = [c[2] for c in amb.chamadas if c[2]]
    ultimo_p0 = max(i for i, n in enumerate(itens) if n == p0.name)
    primeiro_p1 = min(i for i, n in enumerate(itens) if n.startswith("P1_"))
    assert ultimo_p0 < primeiro_p1  # o P0 foi até a revisão antes do P1 começar


def test_p0_na_frente_em_qualquer_etapa(amb):
    """P1 já adiantado (04_edicao) espera o P0 que acabou de chegar em 01."""
    p1 = criar_pedido(pedido_reel(titulo="Adiantado"))
    amb.esteira().processar(p1, PEDIDOS)
    p1 = amb.pasta(BAIXADOS) / p1.name
    amb.esteira().processar(p1, BAIXADOS)
    p0 = criar_pedido(pedido_reel(titulo="Bomba", prioridade="P0"))
    amb.chamadas.clear()
    amb.ciclo(max_trabalhos=1)
    assert amb.chamadas[0][2] == p0.name


def test_pedido_solto_em_01_vira_item(amb):
    (amb.pasta(PEDIDOS) / "pedido_do_claude.json").write_text(
        json.dumps(pedido_reel(titulo="Solto")), encoding="utf-8")
    (amb.pasta(PEDIDOS) / "ruim.json").write_text(
        json.dumps(pedido_reel(titulo="Ruim", canal="futebol", dublar=True)), encoding="utf-8")
    r = amb.ciclo(max_trabalhos=0)
    assert r["importados"] == ["P1_2026-09-30_1830_gta_solto"]
    item = amb.pasta(PEDIDOS) / "P1_2026-09-30_1830_gta_solto"
    assert (item / "pedido_original.json").exists()
    assert not list(amb.pasta(PEDIDOS).glob("*.json"))
    erros = amb.itens(ERROS)
    assert erros == ["entrada_invalida_ruim"]
    e = ler_json(amb.pasta(ERROS) / erros[0] / "erro.json")
    assert "futebol" in e["mensagem"] and e["etapa"] == PEDIDOS


def test_pasta_fora_do_padrao_ganha_nome(amb):
    p = amb.pasta(PEDIDOS) / "meu pedido"
    p.mkdir()
    (p / "pedido.json").write_text(json.dumps(pedido_reel(titulo="Manual")), encoding="utf-8")
    r = amb.ciclo(max_trabalhos=0)
    assert r["importados"] == ["P1_2026-09-30_1830_gta_manual"]


def test_erro_permanente_vai_para_99(amb):
    class Quebrado:
        def baixar(self, url, destino):
            raise ErroPermanente("vídeo privado")
    amb.trocar(baixador=Quebrado())
    item = criar_pedido(pedido_reel())
    r = amb.ciclo()
    assert amb.itens(ERROS) == [item.name] and len(r["erros"]) == 1
    e = ler_json(amb.pasta(ERROS) / item.name / "erro.json")
    assert e["etapa"] == PEDIDOS and e["mensagem"] == "vídeo privado"
    assert e["tentativas"] == 1 and e["permanente"] is True
    assert "ErroPermanente" in e["traceback"]
    assert "ERRO: vídeo privado" in historico(amb.pasta(ERROS) / item.name)


def test_erro_transitorio_tenta_de_novo_e_depois_99(amb):
    class Instavel:
        n = 0

        def baixar(self, url, destino):
            Instavel.n += 1
            raise ErroEtapa("conexão caiu")
    amb.trocar(baixador=Instavel())
    item = criar_pedido(pedido_reel())
    amb.ciclo()
    amb.ciclo()
    assert amb.itens(PEDIDOS) == [item.name]
    assert ler_json(item / "estado.json")["tentativas"][PEDIDOS] == 2
    amb.ciclo()
    assert amb.itens(ERROS) == [item.name] and Instavel.n == 3
    e = ler_json(amb.pasta(ERROS) / item.name / "erro.json")
    assert e["tentativas"] == 3 and e["permanente"] is False
    h = historico(amb.pasta(ERROS) / item.name)
    assert "tentativa 1/3" in h and "tentativa 2/3" in h


def test_reprocessar_tira_de_99(amb):
    class Quebrado:
        def baixar(self, url, destino):
            raise ErroPermanente("fora do ar")
    amb.trocar(baixador=Quebrado())
    item = criar_pedido(pedido_reel())
    amb.ciclo()
    r = acoes.reprocessar(item.name, cfg=amb.cfg)
    assert r["etapa"] == PEDIDOS and amb.itens(PEDIDOS) == [item.name]
    assert not (item / "erro.json").exists() and list((item / "erros_anteriores").iterdir())
    amb.trocar()
    amb.ciclo()
    assert amb.itens(REVISAO) == [item.name]


def test_arquivos_locais_em_vez_de_download(amb, tmp_path):
    video = tmp_path / "meu.mp4"
    video.write_bytes(b"x" * 10)
    item = criar_pedido(pedido_reel(fonte_url=None, arquivos=[str(video)]))
    amb.esteira().processar(item, PEDIDOS)
    b = amb.pasta(BAIXADOS) / item.name
    assert (b / "bruto.mp4").read_bytes() == b"x" * 10
    assert "baixador" not in {c[0] for c in amb.chamadas}


def test_mudar_prioridade(amb):
    item = criar_pedido(pedido_reel())
    r = acoes.mudar_prioridade(item.name, "P0", cfg=amb.cfg)
    assert r["item"] == "P0" + item.name[2:]
    assert ler_json(amb.pasta(PEDIDOS) / r["item"] / "pedido.json")["prioridade"] == "P0"


def test_simular_nao_chama_nada_externo(amb, monkeypatch):
    import esteira.midia as midia
    import hpbase

    def proibido(*a, **k):
        raise AssertionError("chamou subprocesso em --simular")
    monkeypatch.setattr(hpbase, "rodar", proibido)
    monkeypatch.setattr(midia, "rodar", proibido)
    from esteira import vigia
    item = criar_pedido(pedido_reel(redes=["instagram"]))
    vigia.ciclo(amb.cfg, simular=True, agora=MANHA)
    acoes.aprovar(item.name, {"gancho": 10}, cfg=amb.cfg, simular=True, agora=MANHA)
    vigia.ciclo(amb.cfg, simular=True, agora=MANHA)
    assert amb.itens(POSTADOS) == [item.name]
    assert not amb.cfg.fila_api.exists()


def test_postados_antigos_vao_para_o_arquivo(amb):
    from esteira.pastas import ler_estado, salvar_estado
    velho = amb.pasta(POSTADOS) / "P1_2026-09-01_1000_gta_velho"
    novo = amb.pasta(POSTADOS) / "P1_2026-09-30_1000_gta_novo"
    for p, quando in ((velho, "2026-09-01T10:30:00-03:00"), (novo, None)):
        p.mkdir()
        (p / "aviso_no_ar.json").write_text('{"status": "sombra"}')
        est = ler_estado(p)
        est["concluido_em"] = quando or __import__("hpbase").agora_iso()
        salvar_estado(p, est)
    r = amb.ciclo(max_trabalhos=0)
    assert r["arquivados"] == [velho.name]
    assert (amb.pasta(POSTADOS) / "_arquivo" / "2026-09" / velho.name).exists()
    assert amb.itens(POSTADOS) == [novo.name]
