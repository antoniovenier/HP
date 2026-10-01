"""Fila da API (formato suposto, adaptador isolado) e aviso 'no ar' no WhatsApp."""
import json

import pytest
from hpbase import escrever_json, ler_json

from esteira import acoes
from esteira.agendador import AgendadorFilaApi, ler_confirmacao
from esteira.aviso import AvisadorWhatsApp, montar_aviso
from esteira.constantes import AGENDADOS, ERROS, POSTADOS
from esteira.erros import ErroPermanente
from esteira.pedido import criar_pedido
from esteira.testes.conftest import MANHA, pedido_reel


def post_exemplo(item):
    (item / "final.mp4").write_bytes(b"video")
    (item / "capa.jpg").write_bytes(b"capa")
    return {"id": "x", "item": item.name, "canal": "gta", "conta": "@hpgta6", "tipo": "reel",
            "redes": ["instagram", "threads"], "horario_alvo": "2026-09-30T18:30-03:00",
            "titulo": "T", "legenda": "L", "arquivos": ["final.mp4"], "capa": "capa.jpg",
            "nome_canal": "GTA 6 | HP"}


def test_fila_api_modo_real_formato(amb, tmp_path):
    amb.cfg.modo = "real"
    item = tmp_path / "P1_2026-09-30_1830_gta_x"
    item.mkdir()
    post = post_exemplo(item)
    ag = AgendadorFilaApi(amb.cfg)
    reg = ag.agendar(item, post, "instagram")
    arq = amb.cfg.fila_api / "P1_2026-09-30_1830_gta_x__instagram.json"
    assert reg["arquivo_fila"] == str(arq) and reg["modo"] == "real"
    d = ler_json(arq)
    for campo in ("id", "rede", "conta", "canal", "tipo", "midia", "capa", "legenda",
                  "agendar_para", "status", "criado_em"):
        assert campo in d, campo
    assert d["status"] == "pendente" and d["rede"] == "instagram"
    # mídia copiada para a fila (caminho não quebra quando a pasta anda)
    assert d["midia"][0].endswith("fila_api/midia/P1_2026-09-30_1830_gta_x/final.mp4".replace(
        "/", __import__("os").sep))
    assert ag.conferir(item, post, "instagram", reg) is None  # ainda pendente
    # publicador marca publicado no mesmo arquivo
    escrever_json(arq, {**d, "status": "publicado", "permalink": "https://instagram.com/p/1"})
    c = ag.conferir(item, post, "instagram", reg)
    assert c["status"] == "publicado" and c["link"] == "https://instagram.com/p/1"
    # idempotente: agendar de novo não regrava o que o publicador já mexeu
    ag.agendar(item, post, "instagram")
    assert ler_json(arq)["status"] == "publicado"


def test_fila_api_confirmacao_por_subpasta_feitos(amb, tmp_path):
    amb.cfg.modo = "real"
    item = tmp_path / "item"
    item.mkdir()
    post = post_exemplo(item)
    ag = AgendadorFilaApi(amb.cfg)
    reg = ag.agendar(item, post, "threads")
    arq = amb.cfg.fila_api / f"{item.name}__threads.json"
    (amb.cfg.fila_api / "feitos").mkdir()
    arq.rename(amb.cfg.fila_api / "feitos" / arq.name)
    assert ag.conferir(item, post, "threads", reg)["status"] == "publicado"


def test_ler_confirmacao():
    assert ler_confirmacao({"status": "pendente"}) is None
    assert ler_confirmacao({"status": "Agendado", "link": "L"})["link"] == "L"
    assert ler_confirmacao({"status": "erro", "erro": "token vencido"})["status"] == "erro"


def test_modo_sombra_nao_toca_na_fila_real(amb, tmp_path):
    item = tmp_path / "item"
    item.mkdir()
    post = post_exemplo(item)
    ag = AgendadorFilaApi(amb.cfg)
    reg = ag.agendar(item, post, "instagram")
    assert not amb.cfg.fila_api.exists()
    assert (amb.cfg.pasta_sombra / "fila_api" / f"{item.name}__instagram.json").exists()
    assert ag.conferir(item, post, "instagram", reg)["status"] == "sombra"


def test_publicador_marcou_erro_vai_para_99(amb):
    amb.cfg.modo = "real"
    amb.trocar(agendador=AgendadorFilaApi(amb.cfg))
    item = criar_pedido(pedido_reel(redes=["instagram"]))
    amb.ciclo()
    acoes.aprovar(item.name, {"gancho": 9}, cfg=amb.cfg, plugins=amb.plugins, agora=MANHA)
    amb.ciclo()  # 06: grava na fila da API
    arq = amb.cfg.fila_api / f"{item.name}__instagram.json"
    assert ler_json(arq)["status"] == "pendente"
    amb.ciclo()
    assert amb.itens(AGENDADOS) == [item.name]  # esperando o publicador
    escrever_json(arq, {**ler_json(arq), "status": "erro", "erro": "mídia recusada"})
    amb.ciclo()
    assert amb.itens(ERROS) == [item.name]
    assert "mídia recusada" in ler_json(amb.pasta(ERROS) / item.name / "erro.json")["mensagem"]


def test_modo_real_fluxo_com_publicador_e_tiktok(amb):
    amb.cfg.modo = "real"
    amb.trocar(agendador=AgendadorFilaApi(amb.cfg))
    item = criar_pedido(pedido_reel(redes=["instagram", "tiktok"]))
    amb.ciclo()
    acoes.aprovar(item.name, {"gancho": 9}, cfg=amb.cfg, plugins=amb.plugins, agora=MANHA)
    amb.ciclo()
    arq = amb.cfg.fila_api / f"{item.name}__instagram.json"
    escrever_json(arq, {**ler_json(arq), "status": "publicado", "permalink": "https://ig/p/9"})
    acoes.tiktok_ok(item.name, "https://tiktok.com/9", cfg=amb.cfg, plugins=amb.plugins,
                    agora=MANHA)
    assert amb.itens(POSTADOS) == [item.name]
    conf = ler_json(amb.pasta(POSTADOS) / item.name / "confirmacoes.json")
    assert conf["instagram"]["link"] == "https://ig/p/9"
    assert conf["tiktok"]["fonte"] == "tiktok_ok.json"


# --- aviso "no ar" -----------------------------------------------------------------------------
def test_montar_aviso():
    post = {"item": "i", "titulo": "Trailer 2", "canal": "gta", "conta": "@hpgta6",
            "nome_canal": "GTA 6 | HP", "redes": ["instagram", "tiktok"]}
    m = montar_aviso(post, {"instagram": {"link": "https://ig/1"}, "tiktok": {"status": "agendado"}},
                     "HP | Comissão 🚀")
    assert m["texto"].startswith("*Claude - * No ar: Trailer 2")
    assert "Instagram: https://ig/1" in m["texto"] and "TikTok: agendado" in m["texto"]
    assert m["grupo"] == "HP | Comissão 🚀" and m["tipo"] == "no_ar" and m["anexos"] == []


@pytest.mark.parametrize("modo,habilitado,real", [("sombra", False, False),
                                                   ("sombra", True, False),
                                                   ("real", False, False),
                                                   ("real", True, True)])
def test_aviso_so_vai_para_a_fila_real_quando_habilitado(amb, tmp_path, modo, habilitado, real):
    amb.cfg.modo, amb.cfg.aviso_no_ar_habilitado = modo, habilitado
    msg = {"grupo": "HP | Comissão 🚀", "texto": "*Claude - * oi", "anexos": [], "tipo": "no_ar"}
    p, st = AvisadorWhatsApp(amb.cfg).enviar(tmp_path, msg, "a.json")
    assert (p.parent == amb.cfg.whatsapp_fila) is real
    assert st == ("na_fila" if real else "sombra")


def test_aviso_recusa_grupo_e_cabecalho_errados(amb, tmp_path):
    av = AvisadorWhatsApp(amb.cfg)
    with pytest.raises(ErroPermanente, match="Claude"):
        av.enviar(tmp_path, {"grupo": "HP | Comissão 🚀", "texto": "oi"}, "a.json")
    with pytest.raises(ErroPermanente, match="grupo"):
        av.enviar(tmp_path, {"grupo": "Família", "texto": "*Claude - * oi"}, "a.json")


def test_aviso_real_no_fluxo(amb):
    amb.cfg.modo, amb.cfg.aviso_no_ar_habilitado = "real", True
    amb.trocar(avisador=AvisadorWhatsApp(amb.cfg))  # agendador segue o simulado
    item = criar_pedido(pedido_reel(redes=["instagram"]))
    amb.ciclo()
    acoes.aprovar(item.name, {"gancho": 9}, cfg=amb.cfg, plugins=amb.plugins, agora=MANHA)
    amb.ciclo()
    fila = list(amb.cfg.whatsapp_fila.glob("*.json"))
    assert len(fila) == 1 and fila[0].name.endswith(f"_no_ar_{item.name}.json")
    m = json.loads(fila[0].read_text(encoding="utf-8"))
    assert m["texto"].startswith("*Claude - *") and m["tipo"] == "no_ar"
    assert ler_json(amb.pasta(POSTADOS) / item.name / "aviso_no_ar.json")["status"] == "na_fila"
