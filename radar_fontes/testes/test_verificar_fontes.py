"""Testes do verificar_fontes: respostas gravadas (XML/HTML sintéticos), sem rede e sem relógio real."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import verificar_fontes as vf

HOJE = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
ID_ROCKSTAR = "UC6VcWc1rAoWdBCM0JxrRQ3A"
ID_OUTRO = "UCzzzzzzzzzzzzzzzzzzzzzz"

RSS2 = b"""\xef\xbb\xbf<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/" version="2.0">
 <channel>
  <title>GameSpot - All News</title>
  <link>https://www.gamespot.com/feeds/news</link>
  <atom:link href="https://www.gamespot.com/feeds/news" rel="self" type="application/rss+xml"/>
  <item><title>Not&#237;cia nova</title><link>https://www.gamespot.com/a/1</link>
        <pubDate>Tue, 29 Sep 2026 10:00:00 +0000</pubDate></item>
  <item><title>Not&#237;cia velha</title><link>https://www.gamespot.com/a/2</link>
        <pubDate>Mon, 01 Jun 2026 10:00:00 +0000</pubDate></item>
 </channel>
</rss>"""

RSS_DC = b"""<?xml version="1.0"?>
<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/"><channel><title>Sala de Imprensa BMW</title>
<item><title>Novo X3</title><link>https://press.bmwgroup.com/1</link><dc:date>2026-09-15T08:30:00Z</dc:date></item>
</channel></rss>"""

RSS_VELHO = b"""<?xml version="1.0"?><rss version="2.0"><channel><title>Parado</title>
<item><title>Antigo</title><pubDate>Sat, 01 Aug 2026 10:00:00 +0000</pubDate></item>
<item><title>Mais antigo</title><pubDate>Thu, 01 Jan 2026 10:00:00 +0000</pubDate></item>
</channel></rss>"""

RSS_SEM_DATA = b"""<?xml version="1.0"?><rss version="2.0"><channel><title>Sem data</title>
<item><title>Um</title><link>https://x/1</link></item></channel></rss>"""

ATOM = b"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
 <title>Deadline</title>
 <link href="https://deadline.com/"/>
 <updated>2026-09-30T12:00:00Z</updated>
 <entry><title>Furo de Hollywood</title><link rel="alternate" href="https://deadline.com/a/1"/>
        <published>2026-09-28T09:00:00Z</published><updated>2026-09-29T09:00:00Z</updated></entry>
 <entry><title>S\xc3\xb3 updated</title><link href="https://deadline.com/a/2"/>
        <updated>2026-09-05T09:00:00+02:00</updated></entry>
</feed>"""

FEED_YT = ("""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns:media="http://search.yahoo.com/mrss/" xmlns="http://www.w3.org/2005/Atom">
 <link rel="self" href="http://www.youtube.com/feeds/videos.xml?channel_id=%(id)s"/>
 <id>yt:channel:%(id)s</id>
 <yt:channelId>%(id)s</yt:channelId>
 <title>%(titulo)s</title>
 <link rel="alternate" href="https://www.youtube.com/channel/%(id)s"/>
 <author><name>%(titulo)s</name><uri>https://www.youtube.com/channel/%(id)s</uri></author>
 <published>2007-02-23T22:07:14+00:00</published>
 <entry><id>yt:video:abc</id><yt:videoId>abc</yt:videoId><yt:channelId>%(id)s</yt:channelId>
  <title>GTA VI Trailer</title><link rel="alternate" href="https://www.youtube.com/watch?v=abc"/>
  <published>2026-09-20T15:00:00+00:00</published><updated>2026-09-21T00:00:00+00:00</updated></entry>
</feed>""")

PAGINA_CANAL = ("""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">
<title>%(titulo)s - YouTube</title>
<link rel="canonical" href="https://www.youtube.com/channel/%(id)s">
<meta property="og:title" content="%(titulo)s">
<meta property="og:url" content="https://www.youtube.com/channel/%(id)s">
<link rel="alternate" type="application/rss+xml" title="RSS" href="https://www.youtube.com/feeds/videos.xml?channel_id=%(id)s">
</head><body><script>var ytInitialData = {"metadata":{"channelMetadataRenderer":{"title":"%(titulo)s",
"externalId":"%(id)s","vanityChannelUrl":"http://www.youtube.com/%(handle)s"}},"header":{"c":{"canonicalBaseUrl":"/%(handle)s"}}};
</script></body></html>""")

HTML_404 = (b"<!DOCTYPE html>\n<html lang=en>\n  <meta charset=utf-8>\n  <title>Error 404 (Not Found)!!1</title>\n"
            b"  <p><b>404.</b> <ins>That\xe2\x80\x99s an error.</ins></body></html>")


def feed_yt(id_=ID_ROCKSTAR, titulo="Rockstar Games") -> bytes:
    return (FEED_YT % {"id": id_, "titulo": titulo}).encode("utf-8")


def pagina(id_=ID_ROCKSTAR, titulo="Rockstar Games", handle="@RockstarGames") -> bytes:
    return (PAGINA_CANAL % {"id": id_, "titulo": titulo, "handle": handle}).encode("utf-8")


def transporte_de(respostas: dict, registro: list | None = None):
    """Transporte falso: dict url -> (status, bytes, cabecalhos) | bytes (=200) | int (=status sem corpo)."""
    def _t(url):
        if registro is not None:
            registro.append(url)
        r = respostas.get(url, (404, HTML_404, {}))
        if isinstance(r, bytes):
            return 200, r, {"content-type": "application/xml"}
        if isinstance(r, int):
            return r, HTML_404, {}
        if isinstance(r, Exception):
            raise r
        return r
    return _t


# --- texto e datas -----------------------------------------------------------------------
def test_normalizar_tira_acento_maiuscula_e_sufixo_youtube():
    assert vf.normalizar("São Paulo FC") == "saopaulofc"
    assert vf.normalizar("Atlético-MG") == "atleticomg"
    assert vf.normalizar("Rockstar Games - YouTube") == "rockstargames"
    assert vf.normalizar(None) == ""


def test_nomes_batem_igual_contido_e_curto():
    assert vf.nomes_batem("Rockstar Games", "RockstarGames")
    assert vf.nomes_batem("Palmeiras", "TV Palmeiras/FAM")
    assert vf.nomes_batem("CBF TV", "CBF")
    assert vf.nomes_batem("ge", "ge")
    assert not vf.nomes_batem("ge", "gente")          # nome curto só casa exato
    assert not vf.nomes_batem("Flamengo", "Fluminense")
    assert not vf.nomes_batem("", "Flamengo")


def test_analisar_data_rfc2822_iso_com_z_e_invalida():
    rfc = vf.analisar_data("Tue, 29 Sep 2026 10:00:00 +0000")
    assert rfc == datetime(2026, 9, 29, 10, 0, tzinfo=timezone.utc)
    iso = vf.analisar_data("2026-09-15T08:30:00Z")
    assert iso == datetime(2026, 9, 15, 8, 30, tzinfo=timezone.utc)
    assert vf.analisar_data("2026-09-05T09:00:00+02:00").utcoffset() == timedelta(hours=2)
    assert vf.analisar_data("2026-09-05").tzinfo is timezone.utc   # sem fuso = UTC
    assert vf.analisar_data("ontem de tarde") is None
    assert vf.analisar_data("") is None and vf.analisar_data(None) is None


# --- XML / feeds -------------------------------------------------------------------------
def test_analisar_xml_tolera_bom_e_recusa_html_e_quebrado():
    assert vf.analisar_xml(RSS2) is not None
    assert vf.analisar_xml(b"   \n<rss/>") is not None
    assert vf.analisar_xml(HTML_404) is None          # HTML sem fechar não é XML
    assert vf.parece_html(HTML_404) and vf.parece_html(b"\xef\xbb\xbf <html><body/></html>") and not vf.parece_html(RSS2)
    assert vf.analisar_xml(b"<rss><channel></rss>") is None
    assert vf.analisar_xml(b"isso nao e xml") is None
    assert vf.analisar_xml(b"") is None


def test_analisar_feed_rss2():
    f = vf.analisar_feed(RSS2)
    assert f["tipo"] == "rss" and f["titulo"] == "GameSpot - All News"
    assert [i["titulo"] for i in f["itens"]] == ["Notícia nova", "Notícia velha"]
    assert f["itens"][0]["data"] == datetime(2026, 9, 29, 10, 0, tzinfo=timezone.utc)
    assert f["itens"][0]["link"] == "https://www.gamespot.com/a/1"


def test_analisar_feed_atom_com_namespace_published_e_updated():
    f = vf.analisar_feed(ATOM)
    assert f["tipo"] == "atom" and f["titulo"] == "Deadline"
    assert len(f["itens"]) == 2
    assert f["itens"][0]["data"] == datetime(2026, 9, 28, 9, 0, tzinfo=timezone.utc)   # published antes de updated
    assert f["itens"][0]["link"] == "https://deadline.com/a/1"
    assert f["itens"][1]["data"].isoformat() == "2026-09-05T09:00:00+02:00"
    assert f["itens"][1]["titulo"] == "Só updated"


def test_analisar_feed_rss_com_dc_date_e_feed_do_youtube():
    f = vf.analisar_feed(RSS_DC)
    assert f["titulo"] == "Sala de Imprensa BMW"
    assert f["itens"][0]["data"] == datetime(2026, 9, 15, 8, 30, tzinfo=timezone.utc)
    y = vf.analisar_feed(feed_yt())
    assert y["tipo"] == "atom" and y["titulo"] == "Rockstar Games" and y["channel_id"] == ID_ROCKSTAR
    assert vf.analisar_feed(b"<html><body>oi</body></html>") is None     # XML, mas não é feed


# --- verificar_rss -----------------------------------------------------------------------
def test_verificar_rss_ok_rss2_com_bom():
    r = vf.verificar_rss("https://www.gamespot.com/feeds/news/", transporte_de({"https://www.gamespot.com/feeds/news/": RSS2}), HOJE)
    assert r["ok"] is True and r["verificado_por"] == "rss"
    assert r["titulo"] == "GameSpot - All News" and r["n_itens"] == 2
    assert r["mais_novo"] == "2026-09-29T10:00:00+00:00"
    assert r["verificado_em"] == "2026-10-01T12:00:00+00:00" and r["motivo"] is None


def test_verificar_rss_ok_atom():
    r = vf.verificar_rss("https://deadline.com/feed/", transporte_de({"https://deadline.com/feed/": ATOM}), HOJE)
    assert r["ok"] and r["verificado_por"] == "atom" and r["titulo"] == "Deadline" and r["n_itens"] == 2


def test_verificar_rss_404_nao_xml_e_erro_de_rede():
    assert vf.verificar_rss("https://x/404", transporte_de({"https://x/404": 404}), HOJE)["motivo"] == "HTTP 404"
    assert vf.verificar_rss("https://x/403", transporte_de({"https://x/403": (403, b"<rss/>", {})}), HOJE)["motivo"] == "HTTP 403"
    r = vf.verificar_rss("https://x/html", transporte_de({"https://x/html": HTML_404}), HOJE)
    assert r["ok"] is False and r["motivo"] == "não é XML (veio uma página HTML)"
    r = vf.verificar_rss("https://x/q", transporte_de({"https://x/q": b"<?xml version='1.0'?><rss><channel>"}), HOJE)
    assert r["motivo"] == "não é XML"
    r = vf.verificar_rss("https://x/x", transporte_de({"https://x/x": b"<html><body>fechado</body></html>"}), HOJE)
    assert r["motivo"] == "não é XML (veio uma página HTML)"
    r = vf.verificar_rss("https://x/boom", transporte_de({"https://x/boom": OSError("timed out")}), HOJE)
    assert r["ok"] is False and r["motivo"] == "erro de rede: timed out"
    r = vf.verificar_rss("https://x/off", transporte_de({"https://x/off": (0, b"", {"erro": "sem DNS"})}), HOJE)
    assert r["motivo"] == "sem conexão: sem DNS"


def test_verificar_rss_item_velho_sem_data_sem_itens_e_nao_feed():
    r = vf.verificar_rss("https://x/velho", transporte_de({"https://x/velho": RSS_VELHO}), HOJE)
    assert r["ok"] is False and r["motivo"] == "sem item nos últimos 30 dias (mais novo: 2026-08-01)"
    assert r["titulo"] == "Parado" and r["n_itens"] == 2
    # a janela depende de `hoje` injetado, não do relógio: 20 dias depois do item ainda passa
    assert vf.verificar_rss("https://x/velho", transporte_de({"https://x/velho": RSS_VELHO}),
                            datetime(2026, 8, 21, tzinfo=timezone.utc))["ok"] is True
    assert vf.verificar_rss("https://x/sd", transporte_de({"https://x/sd": RSS_SEM_DATA}), HOJE)["motivo"] == "nenhum item com data"
    vazio = b"<rss version='2.0'><channel><title>Vazio</title></channel></rss>"
    assert vf.verificar_rss("https://x/v", transporte_de({"https://x/v": vazio}), HOJE)["motivo"] == "feed sem itens"
    assert vf.verificar_rss("https://x/n", transporte_de({"https://x/n": b"<urlset><url/></urlset>"}), HOJE)["motivo"] == "XML não é RSS nem Atom"


def test_verificar_rss_exige_transporte():
    with pytest.raises(ValueError):
        vf.verificar_rss("https://x", None, HOJE)


# --- YouTube -----------------------------------------------------------------------------
def test_interpretar_canal_handle_url_e_channel():
    assert vf.interpretar_canal("@Flamengo") == {"handle": "@Flamengo", "channel_id": None,
                                                 "pagina": "https://www.youtube.com/@Flamengo"}
    assert vf.interpretar_canal("https://www.youtube.com/@Flamengo/videos")["handle"] == "@Flamengo"
    assert vf.interpretar_canal("Flamengo")["handle"] == "@Flamengo"
    c = vf.interpretar_canal(f"https://www.youtube.com/channel/{ID_ROCKSTAR}")
    assert c == {"handle": None, "channel_id": ID_ROCKSTAR, "pagina": f"https://www.youtube.com/channel/{ID_ROCKSTAR}"}
    assert vf.interpretar_canal(ID_ROCKSTAR)["channel_id"] == ID_ROCKSTAR
    assert vf.interpretar_canal("https://www.youtube.com/c/CBF?x=1")["pagina"] == "https://www.youtube.com/c/CBF"
    assert vf.interpretar_canal("")["pagina"] is None


def test_analisar_pagina_canal_externalid_canonical_og_title_e_handle():
    p = vf.analisar_pagina_canal(pagina())
    assert p == {"channel_id": ID_ROCKSTAR, "titulo": "Rockstar Games", "handle": "@RockstarGames"}
    so_canonical = f'<html><head><link rel="canonical" href="https://www.youtube.com/channel/{ID_OUTRO}"><title>S&#227;o Paulo FC - YouTube</title></head></html>'
    p = vf.analisar_pagina_canal(so_canonical)
    assert p["channel_id"] == ID_OUTRO and p["titulo"] == "São Paulo FC" and p["handle"] is None
    assert vf.analisar_pagina_canal(HTML_404) == {"channel_id": None, "titulo": "Error 404 (Not Found)!!1", "handle": None}
    assert vf.analisar_pagina_canal(b"") == {"channel_id": None, "titulo": "", "handle": None}


def test_canal_verificado_pelo_feed_quando_titulo_bate():
    chamadas = []
    t = transporte_de({vf.YT_FEED.format(id=ID_ROCKSTAR): feed_yt()}, chamadas)
    r = vf.verificar_canal_youtube("@RockstarGames", ID_ROCKSTAR, t, nome="Rockstar Games", hoje=HOJE)
    assert r["ok"] and r["verificado_por"] == "feed" and r["channel_id"] == ID_ROCKSTAR
    assert r["titulo"] == "Rockstar Games" and r["url"] == "https://www.youtube.com/@RockstarGames"
    assert r["evidencia"] == vf.YT_FEED.format(id=ID_ROCKSTAR) and r["verificado_em"] == "2026-10-01T12:00:00+00:00"
    assert chamadas == [vf.YT_FEED.format(id=ID_ROCKSTAR)]          # não abriu a página à toa


def test_canal_feed_404_cai_para_pagina_com_id_igual():
    t = transporte_de({"https://www.youtube.com/@RockstarGames": pagina()})   # feed -> 404
    r = vf.verificar_canal_youtube("https://www.youtube.com/@RockstarGames", ID_ROCKSTAR, t, nome="Rockstar Games", hoje=HOJE)
    assert r["ok"] and r["verificado_por"] == "pagina_canal" and r["channel_id"] == ID_ROCKSTAR
    assert r["titulo"] == "Rockstar Games" and r["evidencia"] == "https://www.youtube.com/@RockstarGames"


def test_canal_pagina_declara_outro_id_descarta_com_motivo():
    t = transporte_de({"https://www.youtube.com/@RockstarGames": pagina(id_=ID_OUTRO)})
    r = vf.verificar_canal_youtube("@RockstarGames", ID_ROCKSTAR, t, nome="Rockstar Games", hoje=HOJE)
    assert r["ok"] is False and r["verificado_por"] is None
    assert "feed: HTTP 404" in r["motivo"] and f"declara o id {ID_OUTRO}" in r["motivo"] and ID_ROCKSTAR in r["motivo"]


def test_canal_sem_id_descobre_na_pagina_e_tenta_o_feed():
    chamadas = []
    t = transporte_de({"https://www.youtube.com/@RockstarGames": pagina()}, chamadas)
    r = vf.verificar_canal_youtube("@RockstarGames", None, t, nome="Rockstar Games", hoje=HOJE)
    assert r["ok"] and r["channel_id"] == ID_ROCKSTAR and r["verificado_por"] == "pagina_canal"
    assert chamadas == ["https://www.youtube.com/@RockstarGames", vf.YT_FEED.format(id=ID_ROCKSTAR)]
    # no PC o feed responde: aí o id descoberto sobe para "feed"
    t2 = transporte_de({"https://www.youtube.com/@RockstarGames": pagina(), vf.YT_FEED.format(id=ID_ROCKSTAR): feed_yt()})
    assert vf.verificar_canal_youtube("@RockstarGames", transporte=t2, nome="Rockstar Games", hoje=HOJE)["verificado_por"] == "feed"
    # URL legada /channel/UC...: a página devolve o @handle e a url sai como @handle
    t3 = transporte_de({f"https://www.youtube.com/channel/{ID_ROCKSTAR}": pagina()})
    r3 = vf.verificar_canal_youtube(f"https://www.youtube.com/channel/{ID_ROCKSTAR}", transporte=t3, hoje=HOJE)
    assert r3["ok"] and r3["url"] == "https://www.youtube.com/@RockstarGames" and r3["handle"] == "@RockstarGames"


def test_canal_titulo_nao_bate_descarta_no_feed_e_na_pagina():
    t = transporte_de({vf.YT_FEED.format(id=ID_ROCKSTAR): feed_yt(titulo="Canal Fake"),
                       "https://www.youtube.com/@RockstarGames": pagina(titulo="Canal Fake")})
    r = vf.verificar_canal_youtube("@RockstarGames", ID_ROCKSTAR, t, nome="Rockstar Games", hoje=HOJE)
    assert r["ok"] is False
    assert "título 'Canal Fake' não bate com o nome 'Rockstar Games'" in r["motivo"]
    # sem nome esperado, não há o que conferir: o id declarado pela página basta
    assert vf.verificar_canal_youtube("@RockstarGames", ID_ROCKSTAR, t, hoje=HOJE)["ok"] is True


def test_canal_tudo_404_ou_sem_id_descarta():
    r = vf.verificar_canal_youtube("@NaoExiste", ID_ROCKSTAR, transporte_de({}), hoje=HOJE)
    assert r["ok"] is False and r["motivo"] == "feed: HTTP 404; página do canal: HTTP 404"
    t = transporte_de({"https://www.youtube.com/@x": b"<html><head><title>x</title></head></html>"})
    assert vf.verificar_canal_youtube("@x", transporte=t, hoje=HOJE)["motivo"] == "página do canal sem id (externalId/canonical)"
    assert "formato UC" in vf.verificar_canal_youtube("@x", "123", transporte_de({}), hoje=HOJE)["motivo"]
    r = vf.verificar_canal_youtube("@x", transporte=transporte_de({"https://www.youtube.com/@x": OSError("reset")}), hoje=HOJE)
    assert r["motivo"] == "página do canal: erro de rede: reset"


def test_canal_feed_com_outro_channel_id_ou_sem_titulo_cai():
    t = transporte_de({vf.YT_FEED.format(id=ID_ROCKSTAR): feed_yt(id_=ID_OUTRO)})
    r = vf.verificar_canal_youtube("@RockstarGames", ID_ROCKSTAR, t, nome="Rockstar Games", hoje=HOJE)
    assert f"declara o id {ID_OUTRO}" in r["motivo"]
    assert vf._mesmo_id("UCabc", "abc") and vf._mesmo_id(ID_ROCKSTAR, ID_ROCKSTAR) and not vf._mesmo_id(ID_ROCKSTAR, ID_OUTRO)


# --- regras de classificação -------------------------------------------------------------
def test_regra_flow_games_nunca_entra():
    assert vf.e_flow_games("Flow Games", "https://www.youtube.com/@flowgames")
    assert vf.e_flow_games("Qualquer", "https://www.youtube.com/@FlowGamesOficial")
    assert vf.e_flow_games("flow_games", None)
    assert vf.e_flow_games("Flow", None)
    assert not vf.e_flow_games("Flamengo", "https://www.youtube.com/@Flamengo")
    assert vf.classificar({"nome": "Flow Games", "url": "https://flowgames.gg/rss", "oficial": True}, "gta")["rejeitar"] == "Flow Games nunca entra no radar"
    ok, ruim, _ = vf.verificar_entrada_youtube({"nome": "Flow Games", "url": "@flowgames", "channel_id": ID_OUTRO}, "gta", transporte_de({}), HOJE)
    assert ok is None and ruim["motivo"] == "Flow Games nunca entra no radar"


def test_regra_site_de_noticia_nunca_e_oficial_nem_reutilizavel():
    assert vf.e_site_noticia("ge", "https://www.youtube.com/@ge")
    assert vf.e_site_noticia("Globo Esporte", "https://ge.globo.com/rss/ge/")
    assert vf.e_site_noticia("Omelete", "https://www.youtube.com/@OmeleteTV")
    assert vf.e_site_noticia("Autoesporte", "https://revistaautoesporte.globo.com/rss/")
    assert vf.e_site_noticia("IGN", "https://www.ign.com/rss/articles/feed")
    assert not vf.e_site_noticia("Flamengo", "https://www.youtube.com/@Flamengo")
    assert not vf.e_site_noticia("BMW Group PressClub", "https://www.press.bmwgroup.com/global/rss")
    assert not vf.e_site_noticia("Gerdau", "https://www.gerdau.com/rss")   # "ge" só casa exato
    for e in ({"nome": "ge", "url": "https://www.youtube.com/@ge", "oficial": True, "video_reutilizavel": True},
              {"nome": "Omelete", "url": "https://www.omelete.com.br/feed", "oficial": True}):
        assert vf.oficial(e) is False
        assert vf.video_reutilizavel(e, "futebol") is False
    c = vf.classificar({"nome": "ge", "url": "https://www.youtube.com/@ge", "oficial": True, "video_reutilizavel": True}, "futebol")
    assert c["oficial"] is False and c["video_reutilizavel"] is False and c["rejeitar"] is None
    assert any("não é oficial" in a for a in c["avisos"]) and any("exige fonte oficial" in a for a in c["avisos"])


def test_regra_oficial_e_video_reutilizavel_por_canal():
    clube = {"nome": "Flamengo", "url": "https://www.youtube.com/@Flamengo", "oficial": True, "video_reutilizavel": True}
    assert vf.oficial(clube) is True and vf.video_reutilizavel(clube, "futebol") is True
    c = vf.classificar(clube, "futebol")
    assert c["video_reutilizavel"] is True and c["nota_uso"] == vf.NOTA_USO_PADRAO["futebol"] and c["avisos"] == []
    estudio = {"nome": "Netflix Brasil", "url": "https://www.youtube.com/@NetflixBrasil", "oficial": True,
               "video_reutilizavel": True, "nota_uso": "só trailer com comentário"}
    assert vf.classificar(estudio, "filmes")["nota_uso"] == "só trailer com comentário"   # nota do agente prevalece
    assert vf.classificar(estudio, "gta")["video_reutilizavel"] is True
    montadora = {"nome": "BMW", "url": "https://www.youtube.com/@BMW", "oficial": True, "video_reutilizavel": True}
    c = vf.classificar(montadora, "carros")
    assert c["oficial"] is True and c["video_reutilizavel"] is False and c["nota_uso"] is None
    assert any("só clube/CBF/liga" in a for a in c["avisos"])
    nao_oficial = {"nome": "Canal do Zé", "url": "https://www.youtube.com/@canaldoze", "oficial": False, "video_reutilizavel": True}
    assert vf.video_reutilizavel(nao_oficial, "futebol") is False
    rss_oficial = {"nome": "CBF", "url": "https://www.cbf.com.br/rss", "oficial": "sim", "video_reutilizavel": "sim"}
    assert vf.oficial(rss_oficial) is True and vf.video_reutilizavel(rss_oficial, "futebol") is False
    assert vf._bool("true") and vf._bool("Sim") and vf._bool(1) and not vf._bool("nao") and not vf._bool(None)


# --- entradas, arquivo e candidatos ------------------------------------------------------
def test_verificar_entrada_rss_monta_formato_de_4_10():
    t = transporte_de({"https://www.gamespot.com/feeds/news/": RSS2, "https://press.bmwgroup.com/rss": RSS_DC})
    ok, ruim, _ = vf.verificar_entrada_rss({"nome": "GameSpot", "url": "https://www.gamespot.com/feeds/news/", "oficial": False}, "gta", t, HOJE)
    assert ruim is None and list(ok) == ["nome", "url", "oficial", "filtrar", "peso", "verificado_em", "evidencia", "verificado_por"]
    assert ok["oficial"] is False and ok["filtrar"] is True and ok["peso"] == 1.0
    assert ok["evidencia"] == "https://www.gamespot.com/feeds/news/" and ok["verificado_por"] == "rss"
    ok, _, _ = vf.verificar_entrada_rss({"nome": "BMW Group PressClub", "url": "https://press.bmwgroup.com/rss", "oficial": True,
                                         "evidencia": "https://www.press.bmwgroup.com/global", "peso": 2}, "carros", t, HOJE)
    assert ok["oficial"] is True and ok["filtrar"] is False and ok["peso"] == 2.0 and ok["evidencia"] == "https://www.press.bmwgroup.com/global"
    ok, ruim, _ = vf.verificar_entrada_rss({"nome": "Parado", "url": "https://x/velho", "oficial": True}, "carros",
                                           transporte_de({"https://x/velho": RSS_VELHO}), HOJE)
    assert ok is None and ruim == {"nome": "Parado", "url": "https://x/velho", "motivo": "sem item nos últimos 30 dias (mais novo: 2026-08-01)"}


def test_verificar_entrada_youtube_monta_formato_de_4_10():
    t = transporte_de({"https://www.youtube.com/@RockstarGames": pagina()})
    ok, ruim, _ = vf.verificar_entrada_youtube({"nome": "Rockstar Games", "url": "https://www.youtube.com/@RockstarGames",
                                                "channel_id": ID_ROCKSTAR, "oficial": True, "video_reutilizavel": True,
                                                "peso": 1.5, "evidencia": "https://www.rockstargames.com/"}, "gta", t, HOJE)
    assert ruim is None
    assert list(ok) == ["nome", "url", "channel_id", "peso", "oficial", "video_reutilizavel", "nota_uso",
                        "verificado_em", "evidencia", "verificado_por"]
    assert ok["nota_uso"] == "trailer só com comentário nosso; nunca trailer puro"
    assert ok["evidencia"] == "https://www.rockstargames.com/" and ok["verificado_por"] == "pagina_canal"
    ok2, _, _ = vf.verificar_entrada_youtube({"nome": "Rockstar Games", "url": "@RockstarGames", "oficial": False}, "gta", t, HOJE)
    assert "nota_uso" not in ok2 and ok2["peso"] == 1.0 and ok2["channel_id"] == ID_ROCKSTAR
    ok3, ruim3, _ = vf.verificar_entrada_youtube({"nome": "Sumido", "url": "@sumido", "channel_id": ID_OUTRO}, "gta", t, HOJE)
    assert ok3 is None and ruim3 == {"nome": "Sumido", "url": "@sumido", "channel_id": ID_OUTRO,
                                     "motivo": "feed: HTTP 404; página do canal: HTTP 404"}


def test_verificar_arquivo_atualiza_e_manda_quem_falhou_para_descartadas(tmp_path: Path):
    arq = tmp_path / "gta_fontes_novas.json"
    arq.write_text(json.dumps({
        "canal": "gta",
        "verificado_em": "2026-09-01T00:00:00-03:00",
        "rss": [{"nome": "GameSpot", "url": "https://www.gamespot.com/feeds/news/", "oficial": False, "filtrar": True, "peso": 1.0},
                {"nome": "Parado", "url": "https://x/velho", "oficial": True, "filtrar": False, "peso": 1.5}],
        "youtube": [{"nome": "Rockstar Games", "url": "https://www.youtube.com/@RockstarGames", "channel_id": ID_ROCKSTAR,
                     "peso": 1.5, "oficial": True, "video_reutilizavel": True},
                    {"nome": "Sumido", "url": "https://www.youtube.com/@sumido", "channel_id": ID_OUTRO, "peso": 1.0, "oficial": True}],
        "descartadas": [{"nome": "Antigo", "url": "https://x/antigo", "motivo": "HTTP 410"}],
        "observacao": "fica",
    }, ensure_ascii=False), encoding="utf-8")
    t = transporte_de({"https://www.gamespot.com/feeds/news/": RSS2, "https://x/velho": RSS_VELHO,
                       vf.YT_FEED.format(id=ID_ROCKSTAR): feed_yt()})
    dados = vf.verificar_arquivo(arq, t, HOJE)
    assert list(dados)[:5] == ["canal", "verificado_em", "rss", "youtube", "descartadas"]
    assert dados["canal"] == "gta" and dados["verificado_em"] == "2026-10-01T12:00:00+00:00" and dados["observacao"] == "fica"
    assert [e["nome"] for e in dados["rss"]] == ["GameSpot"] and [e["nome"] for e in dados["youtube"]] == ["Rockstar Games"]
    assert dados["youtube"][0]["verificado_por"] == "feed" and dados["youtube"][0]["nota_uso"]
    assert [d["nome"] for d in dados["descartadas"]] == ["Antigo", "Parado", "Sumido"]
    assert dados["descartadas"][1]["motivo"].startswith("sem item nos últimos 30 dias")
    assert dados["_avisos"] == []
    # sem gravar=True o arquivo não muda; com gravar=True regrava atômico (sem .tmp sobrando) e sem _avisos
    assert json.loads(arq.read_text(encoding="utf-8"))["verificado_em"] == "2026-09-01T00:00:00-03:00"
    vf.verificar_arquivo(arq, t, HOJE, gravar=True)
    gravado = json.loads(arq.read_text(encoding="utf-8"))
    assert gravado["verificado_em"] == "2026-10-01T12:00:00+00:00" and "_avisos" not in gravado
    assert len(gravado["descartadas"]) == 3 and not list(tmp_path.glob(".tmp_*"))
    # rodar de novo não duplica descartadas
    assert len(vf.verificar_arquivo(arq, t, HOJE)["descartadas"]) == 3


def test_ler_candidatos_formato_de_linha():
    texto = """# tipo|nome|url|oficial|reutilizavel
youtube|Flamengo|https://www.youtube.com/@Flamengo|sim|sim
yt|CBF TV|@CBF|true|true|UCjAnPrhYxdQMcJ0Ckq1bzfQ
rss|ge|https://ge.globo.com/rss/ge/|false|false

rss|Sala BMW|https://press.bmwgroup.com/rss|1|0||2.0
bobagem
foto|x|https://x
"""
    rss, yt, erros = vf.ler_candidatos(texto)
    assert [e["nome"] for e in yt] == ["Flamengo", "CBF TV"] and yt[0]["oficial"] is True and yt[0]["video_reutilizavel"] is True
    assert yt[1]["channel_id"] == "UCjAnPrhYxdQMcJ0Ckq1bzfQ" and yt[1]["tipo"] == "youtube"
    assert [e["nome"] for e in rss] == ["ge", "Sala BMW"] and rss[0]["oficial"] is False and rss[1]["peso"] == "2.0"
    assert len(erros) == 2 and "linha 7" in erros[0] and "linha 8" in erros[1] and "desconhecido" in erros[1]


# --- CLI ---------------------------------------------------------------------------------
def test_cli_canal_imprime_id_titulo_e_verificado_por(capsys):
    t = transporte_de({"https://www.youtube.com/@RockstarGames": pagina()})
    assert vf.main(["canal", "@RockstarGames", "--id", ID_ROCKSTAR], transporte=t, hoje=HOJE) == 0
    saida = capsys.readouterr().out
    assert f"id: {ID_ROCKSTAR}" in saida and "título: Rockstar Games" in saida and "verificado_por: pagina_canal" in saida
    assert vf.main(["canal", "@RockstarGames", "--json"], transporte=t, hoje=HOJE) == 0
    assert json.loads(capsys.readouterr().out)["channel_id"] == ID_ROCKSTAR
    assert vf.main(["canal", "@NaoExiste", "--id", ID_OUTRO], transporte=t, hoje=HOJE) == 1
    assert "não verificado: feed: HTTP 404; página do canal: HTTP 404" in capsys.readouterr().out


def test_cli_rss_imprime_titulo_itens_e_mais_novo(capsys):
    t = transporte_de({"https://www.gamespot.com/feeds/news/": RSS2, "https://x/velho": RSS_VELHO})
    assert vf.main(["rss", "https://www.gamespot.com/feeds/news/"], transporte=t, hoje=HOJE) == 0
    saida = capsys.readouterr().out
    assert "título: GameSpot - All News" in saida and "itens: 2" in saida and "mais novo: 2026-09-29T10:00:00+00:00" in saida
    assert vf.main(["rss", "https://x/velho", "--json"], transporte=t, hoje=HOJE) == 1
    assert json.loads(capsys.readouterr().out)["motivo"].startswith("sem item nos últimos 30 dias")


def test_cli_verificar_e_candidatos(tmp_path: Path, capsys):
    t = transporte_de({"https://www.gamespot.com/feeds/news/": RSS2, "https://www.youtube.com/@RockstarGames": pagina(),
                       "https://ge.globo.com/rss/ge/": RSS_DC})
    arq = tmp_path / "gta_fontes_novas.json"
    arq.write_text(json.dumps({"canal": "gta", "rss": [{"nome": "GameSpot", "url": "https://www.gamespot.com/feeds/news/", "oficial": False}],
                               "youtube": [{"nome": "Rockstar Games", "url": "@RockstarGames", "channel_id": ID_ROCKSTAR, "oficial": True},
                                           {"nome": "Sumido", "url": "@sumido", "channel_id": ID_OUTRO, "oficial": True}]}), encoding="utf-8")
    assert vf.main(["verificar", str(arq), "--gravar"], transporte=t, hoje=HOJE) == 1     # 1 = alguém caiu
    saida = capsys.readouterr().out
    assert "rss ok 1 · youtube ok 1 · descartadas 1 (novas nesta rodada: 1)" in saida and "caiu: Sumido" in saida
    gravado = json.loads(arq.read_text(encoding="utf-8"))
    assert gravado["descartadas"][0]["nome"] == "Sumido" and gravado["verificado_em"] == "2026-10-01T12:00:00+00:00"
    assert vf.main(["verificar", str(arq), "--json"], transporte=t, hoje=HOJE) == 0       # nada novo caiu
    assert json.loads(capsys.readouterr().out)["canal"] == "gta"
    assert vf.main(["verificar", str(tmp_path / "nao_existe.json")], transporte=t, hoje=HOJE) == 1
    cand = tmp_path / "futebol_candidatos.txt"
    cand.write_text("rss|ge|https://ge.globo.com/rss/ge/|true|true\nyoutube|Rockstar Games|@RockstarGames|sim|sim\n", encoding="utf-8")
    assert vf.main(["candidatos", str(cand), "--json"], transporte=t, hoje=HOJE) == 0
    capturado = capsys.readouterr()
    dados = json.loads(capturado.out)
    assert dados["canal"] == "futebol" and dados["rss"][0]["oficial"] is False and dados["rss"][0]["video_reutilizavel" if False else "oficial"] is False
    assert dados["youtube"][0]["video_reutilizavel"] is True and dados["youtube"][0]["nota_uso"] == vf.NOTA_USO_PADRAO["futebol"]
    assert "não é oficial" in capturado.err
    cand.write_text("youtube|Sumido|@sumido|sim|nao|%s\n" % ID_OUTRO, encoding="utf-8")
    assert vf.main(["candidatos", str(cand), "--canal", "gta"], transporte=t, hoje=HOJE) == 1
    assert json.loads(capsys.readouterr().out)["descartadas"][0]["channel_id"] == ID_OUTRO


def test_transporte_real_nao_e_chamado_pela_cli_quando_injetado(monkeypatch, capsys):
    def explode(url, timeout=30):
        raise AssertionError("rede real chamada nos testes: " + url)
    monkeypatch.setattr(vf, "transporte_real", explode)
    t = transporte_de({"https://www.gamespot.com/feeds/news/": RSS2})
    assert vf.main(["rss", "https://www.gamespot.com/feeds/news/"], transporte=t, hoje=HOJE) == 0
    capsys.readouterr()


def test_com_cache_busca_cada_url_uma_vez():
    chamadas = []
    t = vf.com_cache(transporte_de({"https://a": RSS2}, chamadas))
    t("https://a"); t("https://a"); t("https://b")
    assert chamadas == ["https://a", "https://b"]


def test_gravar_json_atomico_utf8(tmp_path: Path):
    alvo = tmp_path / "sub" / "x.json"
    vf.gravar_json(alvo, {"nome": "São Paulo"})
    assert alvo.read_text(encoding="utf-8").startswith('{\n "nome": "São Paulo"')
    assert not list((tmp_path / "sub").glob(".tmp_*"))


def test_transporte_curl_e_lista_sem_janela_e_le_o_corpo(monkeypatch):
    import subprocess
    visto = {}

    def run_falso(cmd, **kw):
        visto["cmd"], visto["kw"] = cmd, kw
        Path(cmd[cmd.index("-o") + 1]).write_bytes(RSS2)
        return subprocess.CompletedProcess(cmd, 0, stdout=b"200", stderr=b"")
    monkeypatch.setattr(subprocess, "run", run_falso)
    status, dados, cab = vf.transporte_curl("https://www.gamespot.com/feeds/news/")
    assert status == 200 and dados == RSS2 and cab == {}
    assert isinstance(visto["cmd"], list) and visto["cmd"][-1] == "https://www.gamespot.com/feeds/news/"
    assert ("creationflags" in visto["kw"]) == (vf.os.name == "nt")
    assert not Path(visto["cmd"][visto["cmd"].index("-o") + 1]).exists()      # temporário apagado

    def run_quebrado(cmd, **kw):
        return subprocess.CompletedProcess(cmd, 6, stdout=b"000", stderr=b"curl: (6) Could not resolve host")
    monkeypatch.setattr(subprocess, "run", run_quebrado)
    assert vf.transporte_curl("https://nao.existe/")[0] == 0 and "resolve" in vf.transporte_curl("https://nao.existe/")[2]["erro"]
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: (_ for _ in ()).throw(OSError("curl não encontrado")))
    assert vf.transporte_curl("https://x/")[2]["erro"] == "curl não encontrado"


# --- correções pedidas pelo F4 (rodada 2) -------------------------------------------------
def test_handle_com_motor1_nao_e_site_noticia():
    """'greatwallmotor1853' contém 'motor1', mas é o canal oficial da GWM; 'Motor1' continua site."""
    assert vf.e_site_noticia("GWM Global", "https://www.youtube.com/@greatwallmotor1853") is False
    assert vf.e_site_noticia("Motor1", "https://www.motor1.com/rss") is True
    assert vf.oficial({"nome": "GWM Global", "url": "https://www.youtube.com/@greatwallmotor1853",
                       "oficial": True}) is True


def test_analisar_data_por_extenso_pt_e_en():
    """O feed pt_br da Netflix usa '30 de setembro de 2026'."""
    assert vf.analisar_data("30 de setembro de 2026") == datetime(2026, 9, 30, tzinfo=timezone.utc)
    assert vf.analisar_data("1 de março de 2026") == datetime(2026, 3, 1, tzinfo=timezone.utc)
    assert vf.analisar_data("30 set 2026") == datetime(2026, 9, 30, tzinfo=timezone.utc)
    assert vf.analisar_data("September 30, 2026") == datetime(2026, 9, 30, tzinfo=timezone.utc)
    assert vf.analisar_data("31 de fevereiro de 2026") is None
    assert vf.analisar_data("ontem") is None
    rss = (b'<?xml version="1.0"?><rss version="2.0"><channel><title>Netflix</title>'
           b'<item><title>Novo</title><link>https://about.netflix.com/1</link>'
           b'<pubDate>30 de setembro de 2026</pubDate></item></channel></rss>')
    r = vf.verificar_rss("https://about.netflix.com/pt_br/feed.xml",
                         transporte_de({"https://about.netflix.com/pt_br/feed.xml": rss}), HOJE)
    assert r["ok"], r


def test_marcas_ja_existe_e_nota_conferir_sobrevivem_ao_gravar(tmp_path: Path):
    arq = tmp_path / "gta_fontes_novas.json"
    arq.write_text(json.dumps({
        "canal": "gta", "verificado_em": "2026-09-01T00:00:00-03:00",
        "rss": [{"nome": "GameSpot", "url": "https://www.gamespot.com/feeds/news/", "oficial": False,
                 "filtrar": True, "peso": 1.0, "nota_conferir": "conferir o peso"}],
        "youtube": [{"nome": "Rockstar Games", "url": "https://www.youtube.com/@RockstarGames",
                     "channel_id": ID_ROCKSTAR, "peso": 1.5, "oficial": True, "video_reutilizavel": True,
                     "ja_existe": True, "nota_conferir": "mesmo id da fixture"}],
        "descartadas": [],
    }, ensure_ascii=False), encoding="utf-8")
    t = transporte_de({"https://www.gamespot.com/feeds/news/": RSS2, vf.YT_FEED.format(id=ID_ROCKSTAR): feed_yt()})
    vf.verificar_arquivo(arq, t, HOJE, gravar=True)
    gravado = json.loads(arq.read_text(encoding="utf-8"))
    assert gravado["youtube"][0]["ja_existe"] is True
    assert gravado["youtube"][0]["nota_conferir"] == "mesmo id da fixture"
    assert gravado["rss"][0]["nota_conferir"] == "conferir o peso"
    assert "ja_existe" not in gravado["rss"][0]
