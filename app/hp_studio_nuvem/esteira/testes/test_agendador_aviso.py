"""Fila da API no formato REAL de 4.1 (via hpbase.fila_api_pc) e aviso 'no ar' no WhatsApp."""
import json

import pytest
from hpbase import escrever_json, ler_json

from esteira import acoes
from esteira.agendador import AgendadorFilaApi, id_fila, ler_confirmacao, montar_registro_fila
from esteira.aviso import AvisadorWhatsApp, montar_aviso
from esteira.constantes import AGENDADOS, ERROS, POSTADOS
from esteira.erros import ErroPermanente
from esteira.pedido import criar_pedido
from esteira.testes.conftest import MANHA, pedido_reel

ID_IG = "gta_2026-09-30_ig_reel_1830"      # convenção real do GTA: gta_<data>_<ig|th>_<tipo>_<HHMM>
ID_TH = "gta_2026-09-30_th_reel_1830"
CAMPOS_REAIS = ["id", "conta", "rede", "tipo", "arquivos", "legenda", "quando", "canal",
                "grupo_whatsapp", "titulo", "capa"]


def post_exemplo(item):
    (item / "final.mp4").write_bytes(b"video")
    (item / "capa.jpg").write_bytes(b"capa")
    return {"id": "x", "item": item.name, "canal": "gta", "conta": "@hpgta6", "tipo": "reel",
            "redes": ["instagram", "threads"], "horario_alvo": "2026-09-30T18:30-03:00",
            "titulo": "T", "legenda": "L", "arquivos": ["final.mp4"], "capa": "capa.jpg",
            "nome_canal": "GTA 6 | HP"}


def _publicador_pos_em_feitos(arq, link, media_id="181", publicado_em="2026-09-30 18:31"):
    """O publicador real MOVE o item para feitos\\ com status no_ar + resultado."""
    d = ler_json(arq)
    escrever_json(arq.parent / "feitos" / arq.name, {**d, "status": "no_ar", "resultado": {
        "media_id": media_id, "permalink": link, "publicado_em": publicado_em}})
    arq.unlink()


def _publicador_pos_em_erros(arq, **campos):
    escrever_json(arq.parent / "erros" / arq.name, {**ler_json(arq), **campos})
    arq.unlink()


def test_fila_api_modo_real_formato(amb, tmp_path):
    amb.cfg.modo = "real"
    item = tmp_path / "P1_2026-09-30_1830_gta_x"
    item.mkdir()
    post = post_exemplo(item)
    ag = AgendadorFilaApi(amb.cfg)
    reg = ag.agendar(item, post, "instagram")
    arq = amb.cfg.fila_api / f"{ID_IG}.json"
    assert reg["arquivo_fila"] == str(arq) and reg["modo"] == "real" and reg["id_fila"] == ID_IG
    d = ler_json(arq)
    assert list(d) == CAMPOS_REAIS
    assert d["conta"] == "hpgta6" and d["rede"] == "instagram" and d["tipo"] == "reel"
    assert d["quando"] == "2026-09-30 18:30" and d["canal"] == "gta"
    assert d["grupo_whatsapp"] == "HP | Comissão 🚀" and d["titulo"] == "T" and d["legenda"] == "L"
    for antigo in ("status", "agendar_para", "midia", "origem", "criado_em"):
        assert antigo not in d
    # mídia copiada para a fila (caminho não quebra quando a pasta anda)
    assert d["arquivos"] == [str(amb.cfg.fila_api / "midia" / item.name / "final.mp4")]
    assert d["capa"] == str(amb.cfg.fila_api / "midia" / item.name / "capa.jpg")
    assert ag.conferir(item, post, "instagram", reg) is None  # ainda na raiz: pendente
    _publicador_pos_em_feitos(arq, "https://instagram.com/p/1")
    c = ag.conferir(item, post, "instagram", reg)
    assert c["status"] == "publicado" and c["link"] == "https://instagram.com/p/1"
    assert c["em"] == "2026-09-30 18:31" and c["media_id"] == "181" and c["fonte"] == "fila_api/feitos"
    # idempotente: agendar de novo não recria o que o publicador já moveu para feitos\
    assert ag.agendar(item, post, "instagram")["id_fila"] == ID_IG
    assert not arq.exists()


def test_fila_api_threads_e_confirmacao_por_feitos(amb, tmp_path):
    amb.cfg.modo = "real"
    item = tmp_path / "P1_2026-09-30_1830_gta_x"
    item.mkdir()
    post = post_exemplo(item)
    ag = AgendadorFilaApi(amb.cfg)
    reg = ag.agendar(item, post, "threads")
    arq = amb.cfg.fila_api / f"{ID_TH}.json"
    assert ler_json(arq)["rede"] == "threads" and ler_json(arq)["conta"] == "hpgta6"
    _publicador_pos_em_feitos(arq, "https://www.threads.com/@hpgta6/post/A")
    c = ag.conferir(item, post, "threads", reg)
    assert c["status"] == "publicado" and c["link"] == "https://www.threads.com/@hpgta6/post/A"


def test_publicador_marcou_erro(amb, tmp_path):
    amb.cfg.modo = "real"
    item = tmp_path / "P1_2026-09-30_1830_gta_x"
    item.mkdir()
    post = post_exemplo(item)
    ag = AgendadorFilaApi(amb.cfg)
    reg = ag.agendar(item, post, "instagram")
    arq = amb.cfg.fila_api / f"{ID_IG}.json"
    _publicador_pos_em_erros(arq, erro="arquivo não existe: H:\\x\\final.mp4")
    c = ag.conferir(item, post, "instagram", reg)
    assert c == {"status": "erro", "mensagem": "arquivo não existe: H:\\x\\final.mp4",
                 "fonte": "fila_api/erros"}
    (amb.cfg.fila_api / "erros" / arq.name).unlink()
    reg = ag.agendar(item, post, "instagram")                   # volta para a raiz
    _publicador_pos_em_erros(arq, ultimo_erro="HTTP 500: fora do ar", tentativas=2)
    assert ag.conferir(item, post, "instagram", reg)["mensagem"] == "HTTP 500: fora do ar"


def test_ler_confirmacao(tmp_path):
    base = {"id": ID_IG, "conta": "hpgta6", "rede": "instagram", "tipo": "reel"}
    assert ler_confirmacao(ID_IG, tmp_path) is None                                   # sumiu: espera
    escrever_json(tmp_path / f"{ID_IG}.json", base)
    assert ler_confirmacao(ID_IG, tmp_path) is None                                   # na raiz: pendente
    escrever_json(tmp_path / "feitos" / f"{ID_IG}.json",
                  {**base, "status": "no_ar", "resultado": {"permalink": "L", "media_id": "1",
                                                            "publicado_em": "2026-09-30 18:31"}})
    c = ler_confirmacao(ID_IG, tmp_path)
    assert c["status"] == "publicado" and c["link"] == "L" and c["em"] == "2026-09-30 18:31"
    escrever_json(tmp_path / "erros" / f"{ID_TH}.json", {**base, "erro": "token vencido"})
    assert ler_confirmacao(ID_TH, tmp_path) == {"status": "erro", "mensagem": "token vencido",
                                                "fonte": "fila_api/erros"}


def test_montar_registro_fila_valida_como_o_publicador(tmp_path):
    item = tmp_path / "P1_2026-09-30_1830_gta_rockstar-quinta"
    item.mkdir()
    post = post_exemplo(item)
    final, capa = str(item / "final.mp4"), str(item / "capa.jpg")
    d = montar_registro_fila(post, "instagram", [final], capa)
    assert d["id"] == ID_IG and d["arquivos"] == [final] and d["capa"] == capa
    with pytest.raises(ErroPermanente, match="instagram ou threads"):
        montar_registro_fila(post, "facebook", [final], capa)
    with pytest.raises(ErroPermanente, match="reel = exatamente 1 vídeo"):
        montar_registro_fila(post, "instagram", [final, final], capa)
    with pytest.raises(ErroPermanente, match="arquivo não existe"):
        montar_registro_fila(post, "instagram", [str(item / "nao.mp4")], None)
    # tipos da esteira -> tipos da fila; canal -> id na convenção dos canais
    texto = {**post, "tipo": "threads_texto", "canal": "carros", "conta": "@hp.carros",
             "item": "P1_2026-09-30_1830_carros_hb20-x-onix", "legenda": "Qual carro?"}
    d = montar_registro_fila(texto, "threads", [str(item / "texto.txt")], None)
    assert d["tipo"] == "texto" and d["arquivos"] == [] and d["conta"] == "hp.carros"
    assert d["id"] == "carros_2026-09-30_1830_hb20-x-onix_th_texto" and "capa" not in d
    (item / "arte_01.png").write_bytes(b"png")
    d = montar_registro_fila({**post, "tipo": "estatico"}, "instagram", [str(item / "arte_01.png")], None)
    assert d["tipo"] == "feed" and d["id"] == "gta_2026-09-30_ig_feed_1830"
    bruto = montar_registro_fila(post, "youtube", [final], capa, validar=False)
    assert bruto["rede"] == "youtube" and bruto["arquivos"] == [final]


def test_modo_real_recusa_rede_fora_da_api(amb, tmp_path):
    amb.cfg.modo = "real"
    item = tmp_path / "P1_2026-09-30_1830_gta_x"
    item.mkdir()
    post = post_exemplo(item)
    ag = AgendadorFilaApi(amb.cfg)
    with pytest.raises(ErroPermanente, match="facebook: rede tem que ser instagram ou threads"):
        ag.agendar(item, post, "facebook")
    with pytest.raises(ErroPermanente, match="youtube"):
        ag.agendar(item, post, "youtube")
    assert not list(amb.cfg.fila_api.glob("*.json")) and not (amb.cfg.fila_api / "midia").exists()


def test_modo_sombra_nao_toca_na_fila_real(amb, tmp_path):
    item = tmp_path / "P1_2026-09-30_1830_gta_x"
    item.mkdir()
    post = post_exemplo(item)
    ag = AgendadorFilaApi(amb.cfg)
    reg = ag.agendar(item, post, "instagram")
    assert not amb.cfg.fila_api.exists()
    sombra = amb.cfg.pasta_sombra / "fila_api"
    assert ler_json(sombra / f"{ID_IG}.json")["conta"] == "hpgta6"
    assert ag.conferir(item, post, "instagram", reg)["status"] == "sombra"
    # rede fora da API: na sombra registra com aviso (em vez de erro)
    reg = ag.agendar(item, post, "facebook")
    arquivos = sorted(p.name for p in sombra.glob("*.json"))
    assert len(arquivos) == 2
    fb = ler_json(sombra / [a for a in arquivos if a != f"{ID_IG}.json"][0])
    assert fb["rede"] == "facebook" and "instagram ou threads" in fb["aviso"]
    assert ag.conferir(item, post, "facebook", reg)["status"] == "sombra"


def test_publicador_marcou_erro_vai_para_99(amb):
    amb.cfg.modo = "real"
    amb.trocar(agendador=AgendadorFilaApi(amb.cfg))
    item = criar_pedido(pedido_reel(redes=["instagram"]))
    amb.ciclo()
    acoes.aprovar(item.name, {"gancho": 9}, cfg=amb.cfg, plugins=amb.plugins, agora=MANHA)
    amb.ciclo()  # 06: grava na fila da API
    post = ler_json(amb.pasta(AGENDADOS) / item.name / "post.json")
    arq = amb.cfg.fila_api / f"{id_fila(post, 'instagram')}.json"
    assert arq.name == "gta_2026-09-30_ig_reel_1830.json"
    d = ler_json(arq)
    assert d["conta"] == "hpgta6" and d["quando"] == "2026-09-30 18:30" and "status" not in d
    amb.ciclo()
    assert amb.itens(AGENDADOS) == [item.name]  # esperando o publicador
    _publicador_pos_em_erros(arq, erro="mídia recusada")
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
    arq = amb.cfg.fila_api / "gta_2026-09-30_ig_reel_1830.json"
    _publicador_pos_em_feitos(arq, "https://ig/p/9")
    acoes.tiktok_ok(item.name, "https://tiktok.com/9", cfg=amb.cfg, plugins=amb.plugins,
                    agora=MANHA)
    assert amb.itens(POSTADOS) == [item.name]
    conf = ler_json(amb.pasta(POSTADOS) / item.name / "confirmacoes.json")
    assert conf["instagram"]["link"] == "https://ig/p/9" and conf["instagram"]["fonte"] == "fila_api/feitos"
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
