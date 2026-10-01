"""Personalidade de cada canal nas artes de story (scripts/story_artes_canais.py).

O que faz: traduz a tabela da marca (hpbase/marca.py, Seção 4.6) em "estilo" de
desenho por canal — fundo (céu do GTA com brilho, estúdio do Futebol, azul com
curvas do Destinos, faixas amarelas do Receitas, faixa vermelha do Carros,
noite do Filmes), cores de texto/destaque/pílula/CTA, fontes por papel, forma
do marcador e o selo HP + @ do canal. Nenhuma cor é inventada aqui: tudo vem
de marca.CANAIS / marca.GTA6 / marca.SELO_HP.

Uso: est = estilo("futebol", cor_destaque="#C8102E"); fundo = pintar_fundo(est).

Regras: fundo determinístico (random só com semente fixa); nada decorativo
dentro das zonas das figurinhas (link e enquete) nem atrás dos textos que
precisam de contraste; cor_destaque (cor do clube) só vale no Futebol e é
clareada até ler (WCAG 4.5) sobre o fundo.
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw

from story_artes_base import (ALTURA, LARGURA, SAFE_TOPO, Tela, bloco_texto, brilho_radial,
                              clarear_ate_ler, degrade_vertical, fonte, legivel_sobre, marca,
                              pilula_imagem, rgba, tokens_destaque)

C = marca.CANAIS
GTA = marca.GTA6
BRANCO, CINZA_CLARO = "#FFFFFF", "#D2D4DA"

# ------------------------------------------------------------------ estilos
ESTILOS: dict = {
    "gta": {
        "texto": GTA["texto"], "texto2": GTA["corpo"], "destaque": GTA["ciano"],
        "acento": C["gta"]["cor_post"],
        "fontes": {"titulo": "Bauhaus 93", "texto": "Segoe UI Bold", "pilula": "Segoe UI Black",
                   "numero": "Bauhaus 93", "hp": "Segoe UI Black Italic", "handle": "Segoe UI Bold"},
        "titulo": {"degrade": C["gta"]["extras"]["titulo_degrade"],
                   "contorno": C["gta"]["extras"]["contorno_titulo"], "contorno_largura": 4},
        "pilula": {"fundo": C["gta"]["cor_post"], "texto": GTA["noite"], "forma": "pilula"},
        "caixa": None, "faixa": None,
        "cta": {"fundo": C["gta"]["cor_post"], "texto": GTA["noite"], "forma": "pilula"},
        "selo": "gta", "marcador": "losango", "cartao_contorno": None,
        "capa_gerada": (GTA["ceu"][0], GTA["noite"], C["gta"]["cor_post"]),
        "cores_fundo": [GTA["noite"], *GTA["ceu"]],
    },
    "futebol": {
        "texto": BRANCO, "texto2": CINZA_CLARO, "destaque": marca.FUTEBOL_VERDE,
        "acento": marca.FUTEBOL_VERDE,
        "fontes": {"titulo": "Anton", "texto": "Barlow Medium", "pilula": "Barlow Condensed ExtraBold",
                   "numero": "Anton", "hp": marca.SELO_HP["fonte"], "handle": marca.SELO_HP["fonte_handle"]},
        "titulo": {},
        "pilula": {"fundo": marca.FUTEBOL_VERDE, "texto": C["futebol"]["extras"]["preto"], "forma": "pilula"},
        "caixa": {"fundo": C["futebol"]["extras"]["caixa"], "alpha": C["futebol"]["extras"]["caixa_opacidade"],
                  "contorno": C["futebol"]["extras"]["contorno_caixa"], "contorno_largura": 2,
                  "contorno_alpha": 110},
        "faixa": None,
        "cta": {"fundo": marca.FUTEBOL_VERDE, "texto": C["futebol"]["extras"]["preto"], "forma": "pilula"},
        "selo": "padrao", "marcador": "circulo", "cartao_contorno": (BRANCO, 90),
        "capa_gerada": (C["futebol"]["extras"]["estudio"][0], C["futebol"]["fundo"],
                        C["futebol"]["extras"]["verde_escuro"]),
        "cores_fundo": [C["futebol"]["fundo"], *C["futebol"]["extras"]["estudio"], C["futebol"]["extras"]["preto"]],
    },
    "filmes": {
        "texto": BRANCO, "texto2": CINZA_CLARO, "destaque": C["filmes"]["cor_post"],
        "acento": C["filmes"]["cor_post"],
        "fontes": {"titulo": "Barlow ExtraBold", "texto": "Barlow Medium", "pilula": "Barlow ExtraBold",
                   "numero": "Anton", "hp": marca.SELO_HP["fonte"], "handle": marca.SELO_HP["fonte_handle"]},
        "titulo": {},
        "pilula": {"fundo": C["filmes"]["cor_post"], "texto": C["filmes"]["extras"]["preto"], "forma": "pilula"},
        # caixa amarela com contorno preto; com *destaque* vira a variação escura (caixa preta)
        "caixa": {"fundo": C["filmes"]["cor_post"], "alpha": 255, "contorno": C["filmes"]["extras"]["preto"],
                  "contorno_largura": 5, "contorno_alpha": 255, "texto": C["filmes"]["extras"]["preto"],
                  "escuro": {"fundo": C["filmes"]["extras"]["variacao_escuro"]["caixa"], "alpha": 235,
                             "contorno": C["filmes"]["cor_post"], "contorno_largura": 5, "contorno_alpha": 255,
                             "texto": C["filmes"]["extras"]["variacao_escuro"]["texto"]}},
        "faixa": None,
        "cta": {"fundo": C["filmes"]["cor_post"], "texto": C["filmes"]["extras"]["preto"], "forma": "pilula"},
        "selo": "padrao", "marcador": "quadrado", "cartao_contorno": None,
        "capa_gerada": (C["filmes"]["fundo"], "#2A2420", C["filmes"]["cor_post"]),
        "cores_fundo": [C["filmes"]["fundo"]],
    },
    "receitas": {
        "texto": C["receitas"]["extras"]["creme"], "texto2": CINZA_CLARO, "destaque": C["receitas"]["cor_post"],
        "acento": C["receitas"]["cor_post"],
        "fontes": {"titulo": "DM Serif Display", "texto": "Barlow ExtraBold", "pilula": "Barlow ExtraBold",
                   "numero": "DM Serif Display", "hp": marca.SELO_HP["fonte"],
                   "handle": marca.SELO_HP["fonte_handle"]},
        "titulo": {},
        "pilula": {"fundo": C["receitas"]["cor_post"], "texto": C["receitas"]["fundo"], "forma": "pilula"},
        "caixa": None,
        "faixa": {"fundo": C["receitas"]["extras"]["faixa_amarela"], "texto": C["receitas"]["fundo"]},
        "cta": {"fundo": C["receitas"]["extras"]["faixa_amarela"], "texto": C["receitas"]["fundo"], "forma": "caixa"},
        "selo": "padrao", "marcador": "traco", "cartao_contorno": None,
        "capa_gerada": (C["receitas"]["cor_post"], C["receitas"]["fundo"], C["receitas"]["extras"]["faixa_amarela"]),
        "cores_fundo": [C["receitas"]["fundo"]],
    },
    "carros": {
        "texto": BRANCO, "texto2": CINZA_CLARO, "destaque": C["carros"]["extras"]["amarelo"],
        "acento": C["carros"]["cor_post"],
        "fontes": {"titulo": "Anton", "texto": "Barlow Medium", "pilula": "Barlow Condensed ExtraBold",
                   "numero": "Anton", "hp": marca.SELO_HP["fonte"], "handle": marca.SELO_HP["fonte_handle"]},
        "titulo": {"italico": 0.18, "traco": C["carros"]["extras"]["traco"]},
        "pilula": {"fundo": C["carros"]["extras"]["etiqueta"], "texto": BRANCO, "forma": "etiqueta"},
        "caixa": None, "faixa": None,
        "cta": {"fundo": C["carros"]["extras"]["etiqueta"], "texto": BRANCO, "forma": "etiqueta"},
        "selo": "carros", "marcador": "traco", "cartao_contorno": None,
        "capa_gerada": ("#2A2A2E", C["carros"]["fundo"], C["carros"]["cor_post"]),
        "cores_fundo": [C["carros"]["fundo"]],
    },
    "destinos": {
        "texto": BRANCO, "texto2": C["destinos"]["extras"]["claro"], "destaque": C["destinos"]["cor_post"],
        "acento": C["destinos"]["cor_post"],
        "fontes": {"titulo": "Barlow ExtraBold", "texto": "Barlow SemiBold", "pilula": "Barlow Condensed ExtraBold",
                   "numero": "Barlow ExtraBold", "hp": marca.SELO_HP["fonte"],
                   "handle": marca.SELO_HP["fonte_handle"]},
        "titulo": {"barra": C["destinos"]["cor_post"]},
        "pilula": {"fundo": C["destinos"]["cor_post"], "texto": C["destinos"]["extras"]["marinho"], "forma": "pilula"},
        "caixa": None, "faixa": None,
        "cta": {"fundo": C["destinos"]["cor_post"], "texto": C["destinos"]["extras"]["marinho"], "forma": "pilula"},
        "selo": "padrao", "marcador": "circulo", "cartao_contorno": None,
        "capa_gerada": (C["destinos"]["extras"]["azul"], C["destinos"]["extras"]["marinho"],
                        C["destinos"]["extras"]["ciano_claro"]),
        "cores_fundo": [*C["destinos"]["extras"]["fundo_curvas"], C["destinos"]["fundo"]],
    },
}


def estilo(canal: str, cor_destaque: str | None = None) -> dict:
    """Estilo resolvido do canal; cor_destaque (clube) só muda o Futebol."""
    if canal not in ESTILOS:
        raise KeyError(canal)
    est = {k: (dict(v) if isinstance(v, dict) else v) for k, v in ESTILOS[canal].items()}
    est["canal"] = canal
    est["handle"] = C[canal]["handle"]
    est["fundo"] = C[canal]["fundo"]
    est["cor_post"] = C[canal]["cor_post"]
    if canal == "futebol" and cor_destaque:
        cor = marca.hex_de(cor_destaque)
        legivel = marca.hex_de(clarear_ate_ler(cor, est["cores_fundo"][0]))
        est["acento"] = cor
        est["destaque"] = legivel
        est["pilula"] = {"fundo": cor, "texto": legivel_sobre(cor), "forma": "pilula"}
        est["cta"] = {"fundo": cor, "texto": legivel_sobre(cor), "forma": "pilula"}
    return est


# ------------------------------------------------------------------- fundos
def _estrelas(img: Image.Image, n: int, cor, y_max: int, semente: int = 7) -> None:
    """Pontinhos determinísticos (semente fixa) só na faixa do topo."""
    rng = np.random.default_rng(semente)
    d = ImageDraw.Draw(img)
    for _ in range(n):
        x = int(rng.integers(0, LARGURA))
        y = int(rng.integers(0, y_max))
        r = float(rng.uniform(1.0, 2.6))
        a = int(rng.integers(90, 200))
        d.ellipse([x - r, y - r, x + r, y + r], fill=rgba(cor, a))


def _poligono(img: Image.Image, pontos, cor, alpha: int = 255) -> None:
    cam = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(cam).polygon(pontos, fill=rgba(cor, alpha))
    img.alpha_composite(cam)


def _curvas(img: Image.Image, centro: tuple, raios, cor, alpha: int, largura: int) -> None:
    cam = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(cam)
    cx, cy = centro
    for r in raios:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=rgba(cor, alpha), width=largura)
    img.alpha_composite(cam)


def pintar_fundo(est: dict) -> Image.Image:
    """Fundo 1080x1920 do canal (RGBA), sem nada dentro das zonas das figurinhas."""
    canal = est["canal"]
    tam = (LARGURA, ALTURA)
    if canal == "gta":
        ceu = GTA["ceu"]
        img = degrade_vertical(tam, [(0.0, ceu[0]), (0.13, ceu[1]), (0.27, ceu[2]), (1.0, GTA["noite"])]).convert("RGBA")
        img.alpha_composite(brilho_radial(tam, (540, 30), 430, C["gta"]["cor_post"], 0.55))
        _estrelas(img, 70, GTA["texto"], SAFE_TOPO - 20)
        img.alpha_composite(brilho_radial(tam, (1080, 1920), 420, C["gta"]["extras"]["laranja"], 0.30))
        return img
    if canal == "futebol":
        est_ = C["futebol"]["extras"]["estudio"]
        img = degrade_vertical(tam, [(0.0, est_[0]), (1.0, est_[1])]).convert("RGBA")
        img.alpha_composite(brilho_radial(tam, (0, 1920), 520, C["futebol"]["extras"]["verde_escuro"], 0.35))
        _poligono(img, [(0, 0), (LARGURA, 0), (LARGURA, 10), (0, 10)], est["acento"])
        return img
    if canal == "filmes":
        img = Image.new("RGBA", tam, rgba(C["filmes"]["fundo"]))
        am = C["filmes"]["cor_post"]
        _poligono(img, [(700, 0), (LARGURA, 0), (LARGURA, 150)], am)             # canto do topo
        _poligono(img, [(0, 1800), (0, ALTURA), (300, ALTURA)], am)              # canto da base
        d = ImageDraw.Draw(img)
        for i in range(12):                                                       # perfuração de filme
            x = 360 + i * 60
            d.rounded_rectangle([x, 1850, x + 36, 1880], radius=6, fill=rgba("#2A2622"))
        return img
    if canal == "receitas":
        img = Image.new("RGBA", tam, rgba(C["receitas"]["fundo"]))
        am = C["receitas"]["extras"]["faixa_amarela"]
        _poligono(img, [(0, 0), (LARGURA, 0), (LARGURA, 60), (0, 140)], am)      # faixa do topo (inclinada)
        _poligono(img, [(0, 1860), (LARGURA, 1760), (LARGURA, ALTURA), (0, ALTURA)], am)  # faixa da base
        _poligono(img, [(0, 150), (LARGURA, 70), (LARGURA, 84), (0, 164)], C["receitas"]["cor_post"])
        return img
    if canal == "carros":
        img = Image.new("RGBA", tam, rgba(C["carros"]["fundo"]))
        vm = C["carros"]["cor_post"]
        _poligono(img, [(620, 0), (LARGURA, 0), (LARGURA, 160), (760, 160)], vm)  # trapézio do topo
        _poligono(img, [(0, 1700), (LARGURA, 1700), (LARGURA, 1712), (0, 1712)], vm)  # traço da base
        _poligono(img, [(0, 1712), (LARGURA, 1712), (LARGURA, ALTURA), (0, ALTURA)], "#161618")
        return img
    if canal == "destinos":
        az, ma = C["destinos"]["extras"]["fundo_curvas"]
        img = degrade_vertical(tam, [(0.0, az), (0.27, ma), (1.0, ma)]).convert("RGBA")
        cl = C["destinos"]["extras"]["ciano_claro"]
        _curvas(img, (-150, -250), (520, 640, 760), cl, 60, 14)
        _curvas(img, (1380, 2280), (480, 600, 720), cl, 60, 14)
        return img
    raise KeyError(canal)


# -------------------------------------------------------------------- selo
def selo_hp(tela: Tela, est: dict, x_dir: int, y_centro: int) -> tuple:
    """Selo HP + @ do canal, encostado à direita em x_dir. Devolve o bbox do conjunto."""
    tipo = est["selo"]
    f_handle = fonte(est["fontes"]["handle"], 30)
    img_h, cores_h = bloco_texto([tokens_destaque(est["handle"])], f_handle, est["texto"])
    f_hp = fonte(est["fontes"]["hp"], 34)
    if tipo == "gta":
        img_hp, cores_hp = bloco_texto([tokens_destaque("HP")], fonte(est["fontes"]["hp"], 40), BRANCO, italico=0.2)
        w_total = img_hp.width + 14 + img_h.width
        x = x_dir - w_total
        y_hp = y_centro - img_hp.height // 2
        tela.texto("selo_hp", img_hp, (x, y_hp), cores_hp)
        tela.texto("handle", img_h, (x + img_hp.width + 14, y_centro - img_h.height // 2), cores_h)
        return (x, min(y_hp, y_centro - img_h.height // 2), x_dir, max(y_hp + img_hp.height, y_centro + img_h.height // 2))
    if tipo == "carros":
        fundo, cor_txt, forma = C["carros"]["extras"]["etiqueta"], BRANCO, "etiqueta"
    else:
        fundo, cor_txt, forma = marca.SELO_HP["fundo"], marca.SELO_HP["texto"], "pilula"
    img_hp, cores_hp = bloco_texto([tokens_destaque("HP")], f_hp, cor_txt)
    pw, ph = img_hp.width + 44, img_hp.height + 14
    w_total = pw + 16 + img_h.width
    x = x_dir - w_total
    y0 = y_centro - ph // 2
    tela.elemento("selo_hp_fundo", pilula_imagem((pw, ph), fundo, forma=forma), (x, y0), [fundo])
    tela.texto("selo_hp", img_hp, (x + 22, y0 + 7), cores_hp)
    tela.texto("handle", img_h, (x + pw + 16, y_centro - img_h.height // 2), cores_h)
    return (x, y0, x_dir, y0 + ph)


def marcador(est: dict, tam: int = 22) -> Image.Image:
    """Marcador dos fatos (bolinha, quadrado, losango ou traço) na cor do canal."""
    cor = rgba(est["acento"])
    forma = est["marcador"]
    img = Image.new("RGBA", (tam + 4, tam + 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if forma == "quadrado":
        d.rectangle([2, 2, tam + 1, tam + 1], fill=cor)
    elif forma == "losango":
        m = tam / 2.0 + 2
        d.polygon([(m, 2), (tam + 2, m), (m, tam + 2), (2, m)], fill=cor)
    elif forma == "traco":
        y0 = tam // 2 - 1
        d.rounded_rectangle([2, y0, tam + 2, y0 + 7], radius=3, fill=cor)
    else:
        d.ellipse([2, 2, tam + 1, tam + 1], fill=cor)
    return img


__all__ = ["ESTILOS", "estilo", "pintar_fundo", "selo_hp", "marcador", "BRANCO", "CINZA_CLARO"]
