"""Montagem sem Claude: aviso "no ar" (agendados.json + AVISO.md) e resumos."""
import json
from datetime import date, datetime

from hpbase import FUSO, escrever_json, raiz_drive, raiz_local
from whatsapp_local.config import (GRUPO_COMISSAO, MODELO_EXEMPLO, PREFIXO, Config,
                                   carregar_grupos_permitidos, pasta_fila)
from whatsapp_local.montagem import (carregar_modelo_aviso, extrair_modelo, fmt_compacto,
                                     montar_no_ar, montar_resumo_dia, montar_resumo_sabado,
                                     normalizar_metricas, normalizar_post, preencher,
                                     sabado_de_referencia)
from whatsapp_local.tarefas import (enfileirar_no_ar, enfileirar_resumo_dia,
                                    enfileirar_resumo_sabado, tarefas_automaticas)
from whatsapp_local.validacao import validar_mensagem

AGORA = datetime(2026, 9, 30, 19, 0, tzinfo=FUSO)


def _agendados(tmp_path):
    posts = [
        {"id": "gta-0930-1830", "canal": "gta", "titulo": "Rockstar confirma novidade",
         "horario": "2026-09-30T18:30:00-03:00",
         "links": {"tiktok": "https://tiktok.com/@hpgta6/1", "instagram": "https://instagram.com/p/1"}},
        {"canal": "Futebol | HP", "titulo": "Golaço do fim de semana",
         "horario": "2026-09-30T21:00:00-03:00", "links": {"instagram": "https://instagram.com/p/2"}},
        {"canal": "Receitas | HP", "titulo": "Bolo de caneca", "horario": "2026-09-30 17:00",
         "links": {}},
        {"canal": "Carros | HP", "titulo": "Cancelado", "horario": "2026-09-30T17:00:00-03:00",
         "status": "cancelado", "links": {"instagram": "https://instagram.com/p/3"}},
        {"canal": "Destinos | HP", "titulo": "Velho", "horario": "2026-09-27T10:00:00-03:00",
         "links": {"instagram": "https://instagram.com/p/4"}},
    ]
    p = tmp_path / "agendados.json"
    escrever_json(p, {"posts": posts})
    return p


def test_no_ar_a_partir_do_agendados(tmp_path):
    msgs = enfileirar_no_ar(_agendados(tmp_path), Config(), AGORA)
    assert len(msgs) == 1 and msgs[0]["_situacao"] == "enfileirada"
    m = msgs[0]
    assert m["tipo"] == "no_ar" and m["grupo"] == GRUPO_COMISSAO
    t = m["texto"]
    assert t.startswith(PREFIXO)
    assert "GTA 6 | HP" in t and "Rockstar confirma novidade" in t and "18:30" in t
    # links em ordem fixa: Instagram antes de TikTok
    assert t.index("Instagram: https://instagram.com/p/1") < t.index("TikTok: https://tiktok.com/@hpgta6/1")
    assert "{" not in t
    # a mensagem montada passa na validação dura
    assert validar_mensagem(m, carregar_grupos_permitidos()) == []
    arquivo = pasta_fila() / f"{m['id']}.json"
    assert json.loads(arquivo.read_text(encoding="utf-8"))["texto"] == t


def test_no_ar_nao_duplica(tmp_path):
    ag = _agendados(tmp_path)
    enfileirar_no_ar(ag, Config(), AGORA)
    de_novo = enfileirar_no_ar(ag, Config(), AGORA)
    assert [m["_situacao"] for m in de_novo] == ["já existia"]
    assert len(list(pasta_fila().glob("*.json"))) == 1


def test_no_ar_so_mostrar_nao_enfileira(tmp_path):
    msgs = enfileirar_no_ar(_agendados(tmp_path), Config(), AGORA, so_mostrar=True)
    assert msgs and list(pasta_fila().glob("*.json")) == []


def test_grupo_por_canal_e_grupo_forcado(tmp_path):
    cfg = Config(grupo_por_canal={"GTA 6 | HP": "HP | GTA 6"})
    assert enfileirar_no_ar(_agendados(tmp_path), cfg, AGORA, so_mostrar=True)[0]["grupo"] == "HP | GTA 6"
    assert enfileirar_no_ar(_agendados(tmp_path), cfg, AGORA, grupo="HP | X",
                            so_mostrar=True)[0]["grupo"] == "HP | X"


def test_modelo_do_drive_e_marcador_desconhecido(tmp_path):
    aviso = raiz_drive() / "06 Projeto" / "AVISO.md"
    aviso.parent.mkdir(parents=True)
    aviso.write_text("# Meu modelo\n\n```text\n*Claude - * {canal} no ar!\n{titulo} ({redes})\n"
                     "{link_tiktok}\n{naoexiste}\n```\n", encoding="utf-8")
    modelo, origem = carregar_modelo_aviso()
    assert origem == str(aviso)
    msg = enfileirar_no_ar(_agendados(tmp_path), Config(), AGORA, so_mostrar=True)[0]
    assert msg["texto"] == ("*Claude - * GTA 6 | HP no ar!\nRockstar confirma novidade "
                            "(Instagram e TikTok)\nhttps://tiktok.com/@hpgta6/1\n{naoexiste}")


def test_modelo_sem_marcadores_usa_o_exemplo():
    aviso = raiz_drive() / "06 Projeto" / "AVISO.md"
    aviso.parent.mkdir(parents=True)
    aviso.write_text("Anotações soltas, sem modelo.", encoding="utf-8")
    modelo, origem = carregar_modelo_aviso()
    assert origem == str(MODELO_EXEMPLO) and "{titulo}" in modelo


def test_extrair_modelo_e_prefixo_garantido():
    assert extrair_modelo("x\n<!-- MODELO_WHATSAPP -->\nA {titulo}\n<!-- FIM_MODELO -->\ny") == "A {titulo}"
    assert extrair_modelo("```\nB\n```") == "B"
    assert preencher("{a} {b}", {"a": 1}) == "1 {b}"
    post = normalizar_post({"canal": "receitas", "titulo": "T", "horario": "30/09/2026 12:00",
                            "links": [{"rede": "pinterest", "url": "https://pin.it/1"}]})
    t = montar_no_ar(post, "Saiu {titulo}\n\n\n\n{links}")
    assert t == f"{PREFIXO} Saiu T\n\nPinterest: https://pin.it/1"
    assert post["canal"] == "Receitas | HP"


def _metricas():
    return {"dias": {
        "2026-09-28": {"GTA 6 | HP": {"instagram": {"seguidores": 10000}, "tiktok": {"seguidores": 2000}},
                       "Futebol | HP": {"instagram": {"seguidores": 500}}},
        "2026-09-29": {"GTA 6 | HP": {"instagram": {"seguidores": 10100, "views": 30000, "posts": 2},
                                      "tiktok": {"seguidores": 2020, "views": 15600, "posts": 1}},
                       "Futebol | HP": {"instagram": {"seguidores": 495, "views": 800, "posts": 1}}},
    }}


def test_resumo_do_dia():
    t = montar_resumo_dia(normalizar_metricas(_metricas()), date(2026, 9, 29))
    linhas = t.split("\n")
    assert linhas[0] == f"{PREFIXO} 📊 Resumo de terça, 29/09"
    assert "• GTA 6 | HP: 12.120 seguidores (+120) · 45,6 mil views · 3 posts" in linhas
    assert "• Futebol | HP: 495 seguidores (-5) · 800 views · 1 post" in linhas
    assert linhas.index("• GTA 6 | HP: 12.120 seguidores (+120) · 45,6 mil views · 3 posts") < \
        linhas.index("• Futebol | HP: 495 seguidores (-5) · 800 views · 1 post")
    assert "Total: 12.615 seguidores (+115) · 46,4 mil views · 4 posts" in linhas
    assert linhas[-1] == "🏆 Destaque: GTA 6 | HP (+120 seguidores)"
    assert montar_resumo_dia(normalizar_metricas(_metricas()), date(2026, 9, 1)) is None


def test_formato_registros_da_mesmo_resultado():
    regs = []
    for dia, canais in _metricas()["dias"].items():
        for canal, redes in canais.items():
            for rede, v in redes.items():
                regs.append({"dia": dia, "canal": {"GTA 6 | HP": "gta"}.get(canal, canal),
                             "rede": rede, **v})
    assert normalizar_metricas({"registros": regs}) == normalizar_metricas(_metricas())
    assert normalizar_metricas(regs) == normalizar_metricas(_metricas())


def test_resumo_de_sabado():
    dias = {}
    for i in range(8):   # sexta 25/09 (base) até sexta 02/10
        d = date(2026, 9, 25 + i) if 25 + i <= 30 else date(2026, 10, 25 + i - 30)
        dias[d.isoformat()] = {"GTA 6 | HP": {"instagram": {"seguidores": 1000 + 100 * i, "views": 1000, "posts": 1}},
                               "Carros | HP": {"instagram": {"seguidores": 300 + i, "views": 10, "posts": 1}}}
    t = montar_resumo_sabado(normalizar_metricas({"dias": dias}), date(2026, 10, 3))
    assert t.startswith(f"{PREFIXO} 🗓️ Resumo da semana — 26/09 a 02/10")
    assert "• GTA 6 | HP: 1.700 seguidores (+700 na semana) · 7.000 views · 7 posts" in t
    assert "• Carros | HP: 307 seguidores (+7 na semana) · 70 views · 7 posts" in t
    assert "🏆 Quem mais cresceu: GTA 6 | HP (+700)" in t
    assert "📉 Precisa de atenção: Carros | HP (+7)" in t
    assert "de 7 dias" not in t
    assert montar_resumo_sabado({}, date(2026, 10, 3)) is None


def test_sabado_de_referencia_e_numeros():
    assert sabado_de_referencia(date(2026, 10, 3)) == date(2026, 10, 3)   # sábado
    assert sabado_de_referencia(date(2026, 9, 30)) == date(2026, 9, 26)   # quarta
    assert fmt_compacto(1_250_000) == "1,2 mi" and fmt_compacto(20000) == "20 mil"
    assert fmt_compacto(9999) == "9.999"


def test_enfileirar_resumos_do_arquivo():
    escrever_json(raiz_local() / "metricas" / "metricas_painel.json", _metricas())
    m = enfileirar_resumo_dia(Config(), datetime(2026, 9, 30, 8, 0, tzinfo=FUSO))
    assert m["_situacao"] == "enfileirada" and m["tipo"] == "resumo_dia"
    assert validar_mensagem(m, carregar_grupos_permitidos()) == []
    assert enfileirar_resumo_dia(Config(), datetime(2026, 9, 30, 9, 0, tzinfo=FUSO))["_situacao"] == "já existia"
    s = enfileirar_resumo_sabado(Config(), datetime(2026, 10, 3, 10, 0, tzinfo=FUSO))
    assert s["tipo"] == "resumo_sabado" and "(números de 2 de 7 dias)" in s["texto"]


def test_sem_metricas_devolve_none():
    assert enfileirar_resumo_dia(Config(), AGORA) is None


def test_tarefas_automaticas_do_vigia(tmp_path):
    escrever_json(raiz_local() / "metricas" / "metricas_painel.json", _metricas())
    cfg = Config(arquivo_agendados=str(_agendados(tmp_path)), hora_resumo_dia="08:00")
    assert tarefas_automaticas(cfg, datetime(2026, 9, 30, 7, 0, tzinfo=FUSO)) == 0   # nada no ar, cedo
    assert tarefas_automaticas(cfg, AGORA) == 2          # no ar do GTA + resumo de ontem
    assert tarefas_automaticas(cfg, AGORA) == 0          # sem duplicar


def _foto(data, seguidores, posts):
    """Foto diária no formato gravado pelo módulo metricas (etapa 6)."""
    return {"data": data, "coletado_em": f"{data}T06:00:00-03:00",
            "contas": {"gta": {"instagram": {"status": "ok", "seguidores": seguidores,
                                             "posts": posts}}}}


def test_resumo_a_partir_das_fotos_diarias_do_modulo_metricas():
    from whatsapp_local.montagem import montar_resumo_dia, normalizar_fotos_diarias
    pasta = raiz_local() / "metricas"
    p1 = {"id": "1", "publicado_em": "2026-09-29T12:00:00-03:00", "views": 1000,
          "curtidas": 100, "comentarios": 10}
    p2 = {"id": "2", "publicado_em": "2026-09-29T19:00:00-03:00", "views": 500,
          "curtidas": 50, "comentarios": 5}
    escrever_json(pasta / "2026-09-29.json", _foto("2026-09-29", 9900, [dict(p1, views=100)]))
    escrever_json(pasta / "2026-09-30.json", _foto("2026-09-30", 10000, [p1, p2]))
    escrever_json(pasta / "metricas_painel.json", {"versao": 1, "contas": {}})  # ignorado
    m = normalizar_fotos_diarias(pasta)
    dia = m["2026-09-29"]["GTA 6 | HP"]["instagram"]
    # seguidores do dia 29 = foto das 6h do dia 30; views = posts publicados no dia 29,
    # com os números da foto mais recente
    assert dia == {"seguidores": 10000, "posts": 2, "views": 1500, "curtidas": 150,
                   "comentarios": 15}
    assert m["2026-09-28"]["GTA 6 | HP"]["instagram"]["seguidores"] == 9900
    m2 = enfileirar_resumo_dia(Config(), datetime(2026, 9, 30, 8, 0, tzinfo=FUSO))
    assert m2 and m2["tipo"] == "resumo_dia" and m2["texto"].startswith(PREFIXO)
    assert montar_resumo_dia(m, date(2026, 9, 29))
