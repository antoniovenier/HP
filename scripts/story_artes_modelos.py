"""Os 3 modelos de story (chamada, maissobre, interacao) — scripts/story_artes_modelos.py.

O que faz: monta cada modelo em cima de uma Tela (story_artes_base) com o estilo do
canal (story_artes_canais): cabeçalho (rótulo em pílula + selo HP + @), cartão da
capa com cantos arredondados (foto tratada e enquadrada pelo foco), chamada /
pergunta / fatos com a letra ajustada, seta vetorial para a zona do link,
contorno fino das zonas das figurinhas, crédito da foto.

Linhas do quadro (1080x1920): tudo entre y=250 e y=1570 (zonas seguras da marca);
cabeçalho em y 268-330; zona da enquete (110,930)-(970,1480); zona do link
(140,1500)-(940,1640).

Uso: montar(tela, est, spec, imagens) -> None (os textos ficam em camadas da Tela).
Regras: todo texto passa por ajustar() (reduz até o mínimo e recusa em português);
nada escrito dentro das zonas das figurinhas; crédito só quando houver credito_foto.
"""
from __future__ import annotations

from PIL import Image, ImageDraw

from story_artes_base import (ALTURA, ErroStory, RAIO_CARTAO, Tela, X0, X1, Y_SEGURO1, ZONA_ENQUETE,
                              ZONA_LINK, ajustar, altura_linha, arredondar, bloco_texto, capa_gerada,
                              contorno_arredondado, enquadrar, fonte, largura_texto, marca, pilula_imagem,
                              quebrar, rgba, seta_imagem, tokens_destaque, tratar_foto)
from story_artes_canais import marcador, selo_hp

Y_CAB = 268            # topo do cabeçalho (rótulo e selo)
Y_CORPO = 352          # começo do corpo
Y_CTA0, Y_CTA1 = 1408, 1488   # linha do CTA / "toque pra ver" (acima da zona do link)
CONTORNO_ZONA = ("#FFFFFF", 90, 3)   # cor, alpha, largura do contorno das zonas


# ---------------------------------------------------------------- pedaços
def pilula_texto(tela: Tela, nome: str, texto: str, est: dict, estilo_pilula: dict, x: int, y: int,
                 tam_max: int = 32, tam_min: int = 22, largura_max: int = 520, pad=(30, 12),
                 campo: str = "rotulo") -> tuple:
    """Pílula/etiqueta/caixa com texto dentro; devolve o retângulo da forma."""
    f, linhas, _ = ajustar(texto, est["fontes"]["pilula"], largura_max - 2 * pad[0], 1, tam_max, tam_min, campo)
    img, cores = bloco_texto(linhas, f, estilo_pilula["texto"])
    bb = img.getbbox() or (0, 0, img.width, img.height)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    pw, ph = w + 2 * pad[0], h + 2 * pad[1]
    forma = estilo_pilula.get("forma", "pilula")
    tela.elemento(f"{nome}_fundo", pilula_imagem((pw, ph), estilo_pilula["fundo"], forma=forma), (x, y),
                  [estilo_pilula["fundo"]])
    tela.texto(nome, img, (x + pad[0] - bb[0], y + pad[1] - bb[1]), cores)
    return (x, y, x + pw, y + ph)


def cabecalho(tela: Tela, est: dict, spec: dict) -> int:
    """Rótulo em pílula à esquerda, selo HP + @ à direita. Devolve o y de baixo."""
    ret = pilula_texto(tela, "rotulo", spec["rotulo"], est, est["pilula"], X0, Y_CAB)
    y_centro = (ret[1] + ret[3]) // 2
    selo = selo_hp(tela, est, X1, y_centro)
    return max(ret[3], selo[3])


def cartao(tela: Tela, nome: str, capa: Image.Image | None, caixa: tuple, foco, est: dict,
           credito: str = "") -> tuple:
    """Capa do post (tratada e enquadrada) como cartão arredondado; crédito dentro, embaixo."""
    x0, y0, x1, y1 = caixa
    tam = (x1 - x0, y1 - y0)
    if capa is not None:
        img = tratar_foto(enquadrar(capa, tam, foco))
    else:
        a, b, c = est["capa_gerada"]
        img = capa_gerada(tam, a, b, c)
    img = arredondar(img, RAIO_CARTAO)
    tela.elemento(nome, img, (x0, y0))
    if est.get("cartao_contorno"):
        cor, alpha = est["cartao_contorno"]
        tela.elemento(f"{nome}_contorno", contorno_arredondado(tam, RAIO_CARTAO, cor, 2, alpha), (x0, y0))
    if credito:
        f = fonte(est["fontes"]["texto"], 24)
        img_c, cores = bloco_texto([tokens_destaque("Foto: " + credito.replace("*", ""))], f, "#FFFFFF")
        bb = img_c.getbbox() or (0, 0, img_c.width, img_c.height)
        w, h = bb[2] - bb[0], bb[3] - bb[1]
        pw, ph = min(w + 32, tam[0] - 40), h + 16
        px, py = x0 + 20, y1 - 20 - ph
        tela.elemento("credito_fundo", pilula_imagem((pw, ph), "#000000", alpha=200), (px, py), ["#000000"])
        tela.texto("credito_foto", img_c, (px + 16 - bb[0], py + 8 - bb[1]), cores)
    return caixa


def titulo(tela: Tela, est: dict, nome: str, texto: str, x: int, y: int, largura: int, alt_max: int,
           max_linhas: int, tam_max: int, tam_min: int, alinhamento: str = "esq",
           campo: str = "chamada", usar_caixa: bool = True, centrar_vertical: bool = False) -> tuple:
    """Chamada/pergunta no estilo do canal (degradê GTA, itálico+traço Carros, caixa Futebol/Filmes,
    faixa Receitas, barra Destinos). Devolve o bbox ocupado (forma + texto)."""
    t = est.get("titulo") or {}
    caixa = est.get("caixa") if usar_caixa else None
    faixa = est.get("faixa") if usar_caixa else None
    tem_destaque = "*" in texto
    cor_txt, cor_dest, sublinhado = est["texto"], est["destaque"], None
    superficie = None
    if caixa:
        if caixa.get("escuro") and tem_destaque:
            caixa = caixa["escuro"]            # Filmes: com *destaque* vira a variação escura
        cor_txt = caixa.get("texto", cor_txt)
        superficie = caixa["fundo"] if caixa.get("alpha", 255) >= 200 else None
    if faixa:
        cor_txt = faixa["texto"]
        superficie = faixa["fundo"]
    if superficie is not None and marca.contraste(cor_dest, superficie) < 4.5:
        sublinhado, cor_dest = cor_dest, cor_txt   # destaque não lê na superfície: vira traço embaixo
    pad = 28 if (caixa or faixa) else 0
    f, linhas, _ = ajustar(texto, est["fontes"]["titulo"], largura - 2 * pad, max_linhas, tam_max, tam_min, campo,
                           alt_max=alt_max - 2 * pad)
    img, cores = bloco_texto(linhas, f, cor_txt, cor_dest, largura=largura - 2 * pad, alinhamento=alinhamento,
                             degrade=t.get("degrade"), contorno=t.get("contorno"),
                             contorno_largura=t.get("contorno_largura", 0), italico=t.get("italico", 0.0),
                             sublinhado=sublinhado)
    bb = img.getbbox() or (0, 0, img.width, img.height)
    h_txt = bb[3] - bb[1]
    extra = 20 if t.get("traco") else 0
    if centrar_vertical:
        y = y + max(0, (alt_max - (h_txt + 2 * pad + extra)) // 2)
    if caixa:
        ph = h_txt + 2 * pad
        tela.elemento(f"{nome}_caixa",
                      pilula_imagem((largura, ph), caixa["fundo"], caixa.get("contorno"),
                                    caixa.get("contorno_largura", 0), "caixa", caixa.get("alpha", 255)),
                      (x, y), [caixa["fundo"]])
    elif faixa:
        ph = h_txt + 2 * pad
        tela.elemento(f"{nome}_faixa", pilula_imagem((largura, ph), faixa["fundo"], forma="caixa"), (x, y),
                      [faixa["fundo"]])
    y_txt = y + pad - bb[1]
    bbox = tela.texto(nome, img, (x, y_txt), cores)
    fim = y + pad + h_txt + pad
    if t.get("traco") and bbox:
        d = tela.desenho()
        d.rounded_rectangle([bbox[0], fim + 6, bbox[0] + 180, fim + 16], radius=5, fill=rgba(t["traco"]))
        tela.registrar(f"{nome}_traco", (bbox[0], fim + 6, bbox[0] + 180, fim + 16), [t["traco"]])
        fim += extra
    if t.get("barra") and bbox:
        d = tela.desenho()
        bx = max(0, bbox[0] - 26)
        d.rounded_rectangle([bx, bbox[1], bx + 10, bbox[3]], radius=5, fill=rgba(t["barra"]))
        tela.registrar(f"{nome}_barra", (bx, bbox[1], bx + 10, bbox[3]), [t["barra"]])
    return (x, y, x + largura, fim)


def zona(tela: Tela, nome: str, ret: tuple) -> None:
    """Contorno fino e translúcido da zona da figurinha (nada escrito dentro)."""
    cor, alpha, larg = CONTORNO_ZONA
    x0, y0, x1, y1 = ret
    tela.elemento(f"zona_{nome}", contorno_arredondado((x1 - x0, y1 - y0), 24, cor, larg, alpha), (x0, y0))


def texto_simples(tela: Tela, nome: str, texto: str, est: dict, nome_fonte: str, tam: int, cor, x: int, y: int,
                  largura: int, max_linhas: int = 1, tam_min: int | None = None, alinhamento: str = "esq",
                  campo: str | None = None) -> tuple | None:
    f, linhas, _ = ajustar(texto, nome_fonte, largura, max_linhas, tam, tam_min or max(16, tam - 10),
                           campo or nome)
    img, cores = bloco_texto(linhas, f, cor, est["destaque"], largura=largura, alinhamento=alinhamento)
    return tela.texto(nome, img, (x, y), cores)


def cta(tela: Tela, est: dict, texto: str, x: int, y: int) -> tuple:
    return pilula_texto(tela, "cta", texto, est, est["cta"], x, y, tam_max=34, tam_min=24, largura_max=600,
                        pad=(34, 14), campo="cta")


# ---------------------------------------------------------------- modelos
def modelo_chamada(tela: Tela, est: dict, spec: dict, imagens: dict) -> None:
    figs = spec["figurinhas"]
    compacto = "enquete" in figs
    cabecalho(tela, est, spec)
    capa = imagens.get("capa")
    if not compacto:
        cartao(tela, "cartao", capa, (X0, Y_CORPO, X1, 1172), spec["foco"], est, spec["credito_foto"])
        titulo(tela, est, "chamada", spec["chamada"], X0, 1198, X1 - X0, 200, 2, 96, 40, "esq", "chamada",
               centrar_vertical=True)
        # "toque pra ver" + seta vetorial descendo para a zona do link
        f = fonte(est["fontes"]["texto"], 34)
        img, cores = bloco_texto([tokens_destaque("toque pra ver")], f, est["texto2"])
        bb = tela.texto("toque", img, (X0, 1424), cores)
        x_seta = (bb[2] if bb else X0 + 200) + 40
        seta, bbs = seta_imagem((x_seta, 1424), (x_seta + 150, 1494), est["acento"], 14, -0.40, 48)
        tela.elemento("seta", seta, (0, 0), [est["acento"]])
    else:
        cartao(tela, "cartao", capa, (X0, 350, X0 + 520, 900), spec["foco"], est, spec["credito_foto"])
        xc, wc = X0 + 520 + 36, X1 + 50 - (X0 + 520 + 36)      # coluna da direita: 666..1020
        ret = titulo(tela, est, "chamada", spec["chamada"], xc, 350, wc, 400, 4, 60, 32, "esq", "chamada")
        f = fonte(est["fontes"]["texto"], 30)
        img, cores = bloco_texto([tokens_destaque("toque pra ver")], f, est["texto2"])
        y_t = min(ret[3] + 24, 850)
        tela.texto("toque", img, (xc, y_t), cores)
        seta, bbs = seta_imagem((1010, y_t + 60), (1010, 1492), est["acento"], 12, 0.06, 44)
        tela.elemento("seta", seta, (0, 0), [est["acento"]])
        zona(tela, "enquete", ZONA_ENQUETE)
    if "link" in figs:
        zona(tela, "link", ZONA_LINK)


def _ajustar_fatos(fatos: list, nome_fonte: str, largura: int, alt_disp: int, tam_max: int, tam_min: int,
                   gap: int):
    for tam in range(tam_max, tam_min - 1, -2):
        f = fonte(nome_fonte, tam)
        lh = altura_linha(f)
        blocos = []
        total = 0
        ok = True
        for fato in fatos:
            linhas = quebrar(tokens_destaque(fato), f, largura, 2)
            if linhas is None:
                ok = False
                break
            blocos.append(linhas)
            total += len(linhas) * lh
        total += gap * (len(fatos) - 1)
        if ok and total <= alt_disp:
            return f, blocos
    raise ErroStory(f"Os {len(fatos)} fatos não cabem no quadro nem com a letra no mínimo ({tam_min} px). "
                    "Encurte os fatos (até 70 caracteres, de preferência 1 linha cada).")


def modelo_maissobre(tela: Tela, est: dict, spec: dict, imagens: dict) -> None:
    cabecalho(tela, est, spec)
    capa = imagens.get("capa")
    df = spec["dado_forte"]
    y = Y_CORPO
    tem_mini = capa is not None or df is not None or bool(spec["chamada"])
    if tem_mini:
        cartao(tela, "miniatura", capa, (X0, y, X0 + 320, y + 348), spec["foco"], est, spec["credito_foto"])
        xd = X0 + 320 + 40
        wd = X1 - xd
        if df:
            ret = titulo(tela, est, "dado_forte_valor", df["valor"], xd, y - 6, wd, 190, 1, 150, 48, "esq",
                         "dado_forte.valor", usar_caixa=False)
            yl = ret[3] + 10
            if df["legenda"]:
                bb = texto_simples(tela, "dado_forte_legenda", df["legenda"], est, est["fontes"]["texto"], 36,
                                   est["texto2"], xd, yl, wd, 2, 26, "esq", "dado_forte.legenda")
                yl = (bb[3] if bb else yl) + 14
            if est["canal"] == "destinos" and "R$" in df["valor"] and spec.get("ida_volta", True):
                pilula_texto(tela, "ida_volta", "IDA E VOLTA", est, est["pilula"], xd, min(yl, y + 290),
                             tam_max=26, tam_min=20, largura_max=wd, pad=(22, 8), campo="ida_volta")
        elif spec["chamada"]:
            titulo(tela, est, "chamada", spec["chamada"], xd, y, wd, 348, 3, 64, 34, "esq", "chamada",
                   usar_caixa=False)
        y += 348 + 40
    alt_disp = Y_CTA0 - 24 - y
    f, blocos = _ajustar_fatos(spec["fatos"], est["fontes"]["texto"], X1 - (X0 + 64), alt_disp, 54, 30, 26)
    lh = altura_linha(f)
    for i, linhas in enumerate(blocos, 1):
        img, cores = bloco_texto(linhas, f, est["texto"], est["destaque"], largura=X1 - (X0 + 64))
        bb = tela.texto(f"fato_{i}", img, (X0 + 64, y), cores)
        m = marcador(est, 22)
        ym = int(bb[1] + lh * 0.42) - m.height // 2 if bb else y + lh // 2
        tela.elemento(f"marcador_{i}", m, (X0 + 8, ym), [est["acento"]])
        y += len(linhas) * lh + 26
    if spec["cta"]:
        cta(tela, est, spec["cta"], X0, Y_CTA0)
    if "link" in spec["figurinhas"]:
        zona(tela, "link", ZONA_LINK)


def modelo_interacao(tela: Tela, est: dict, spec: dict, imagens: dict) -> None:
    cabecalho(tela, est, spec)
    fotos = imagens.get("fotos_prefere")
    if fotos:
        titulo(tela, est, "pergunta", spec["pergunta"], X0, Y_CORPO, X1 - X0, 220, 2, 76, 40, "centro", "pergunta")
        w = (X1 - X0 - 40) // 2
        cartao(tela, "foto_a", fotos[0], (X0, 592, X0 + w, 900), (0.5, 0.5), est)
        cartao(tela, "foto_b", fotos[1], (X1 - w, 592, X1, 900), (0.5, 0.5), est)
    else:
        titulo(tela, est, "pergunta", spec["pergunta"], X0, Y_CORPO, X1 - X0, 540, 3, 100, 48, "centro",
               "pergunta", centrar_vertical=True)
    zona(tela, "enquete", ZONA_ENQUETE)
    if "link" in spec["figurinhas"]:
        zona(tela, "link", ZONA_LINK)
    elif spec["cta"]:
        f = fonte(est["fontes"]["texto"], 34)
        toks = tokens_destaque(spec["cta"])
        img, cores = bloco_texto([toks], f, est["texto2"], est["destaque"], largura=X1 - X0, alinhamento="centro")
        tela.texto("cta", img, (X0, 1506), cores)


MODELOS = {"chamada": modelo_chamada, "maissobre": modelo_maissobre, "interacao": modelo_interacao}


def montar(tela: Tela, est: dict, spec: dict, imagens: dict) -> None:
    MODELOS[spec["tipo"]](tela, est, spec, imagens)


__all__ = ["montar", "MODELOS", "modelo_chamada", "modelo_maissobre", "modelo_interacao", "cabecalho",
           "cartao", "titulo", "zona", "cta", "pilula_texto", "texto_simples", "Y_CAB", "Y_CORPO",
           "Y_CTA0", "Y_CTA1", "CONTORNO_ZONA"]
