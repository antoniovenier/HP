"""Os 6 formatos do Futebol | HP: gol, noticia, debate, estatistica,
resultado e tabela. Cada função recebe o roteiro já validado e normalizado
(caminhos absolutos) e devolve um Plano (lista de segmentos + música).

Layout 1080x1920: nada escrito nos 250 px do topo nem nos 350 px da base
(área da interface do Reels) — conferido por conferir_zona() em cada arte.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

from reel_futebol_arte import (FotoKB, Sprite, abrir_rgb, bloco_texto,
                               cabecalho, caixa_texto, clamp01, colar, compor,
                               conferir_zona, cor, cor_de_time, degrade, escudo,
                               fonte, formatar_numero, fundo_desfocado,
                               fundo_marca, larg, marca_dagua, metricas,
                               pilula, rgb, rgba, seta_para_baixo, sigla_de,
                               suave, texto_ajustado)
from reel_futebol_base import (ALTURA, LARGURA, MARGEM, ZONA_Y1, ErroReel)
from reel_futebol_midia import Musica, Plano, SegClipe, SegQuadros, info_midia
from reel_futebol_roteiro import _num, licenca_da_musica, normalizar_legendas

LARG_UTIL = LARGURA - 2 * MARGEM   # 960
XFADE = 0.4                        # troca suave entre fotos (s)


# ------------------------------------------------------------------ ajudas
def _preguicoso(fn):
    """Calcula só na primeira vez (o --simular não desenha nada pesado)."""
    cache = {}

    def f():
        if "v" not in cache:
            cache["v"] = fn()
        return cache["v"]
    return f


def _extra(r: dict, estilo: dict) -> list[Sprite]:
    txt = (r.get("marca_dagua") or "").strip()
    return [marca_dagua(txt, estilo)] if txt else []


def empilhar(itens, y0: int, y1: int, x_centro: int = LARGURA // 2) -> list[Sprite]:
    """[(imagem, espaço_antes)] centralizados na vertical entre y0 e y1."""
    itens = [(img, esp) for img, esp in itens if img is not None]
    total = sum(img.height for img, _ in itens) + sum(esp for _, esp in itens[1:])
    y = y0 + max(0, (y1 - y0 - total) // 2)
    saida = []
    for k, (img, esp) in enumerate(itens):
        if k:
            y += esp
        saida.append(Sprite(img, x_centro - img.width // 2, y))
        y += img.height
    return saida


def credito_video(c: str) -> str:
    c = str(c).strip()
    if not c.startswith("@") and " " not in c:
        c = "@" + c
    return c if c.lower().startswith("vídeo") else f"Vídeo: {c}"


def credito_foto(c: str) -> str:
    c = str(c).strip()
    baixo = c.lower()
    if baixo.startswith(("foto", "imagem", "crédito", "credito", "vídeo", "video")):
        return c
    return f"Foto: {c}"


def fmt_minuto(m) -> str:
    s = str(m).strip()
    return s if s.endswith("'") else s + "'"


def _tam_foto(caminho) -> tuple[int, int]:
    with Image.open(caminho) as im:
        w, h = im.size
        try:
            if im.getexif().get(0x0112) in (5, 6, 7, 8):
                w, h = h, w
        except Exception:
            pass
    return w, h


def _mascara_cantos(w: int, h: int, raio: int = 26) -> Image.Image:
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), raio, fill=255)
    return m


def _moldura_com_janela(estilo: dict, vis, sprites, raio: int = 26) -> Image.Image:
    """Fundo do canal com um 'buraco' (cantos arredondados) onde passa o vídeo."""
    base = fundo_marca(estilo).convert("RGBA")
    a = base.getchannel("A")
    x, y, w, h = vis
    ImageDraw.Draw(a).rounded_rectangle((x, y, x + w - 1, y + h - 1), raio, fill=0)
    base.putalpha(a)
    return compor(sprites, base=base)


def _musica(r: dict) -> Musica | None:
    m = r.get("musica")
    if not m:
        return None
    p = Path(m["arquivo"])
    return Musica(p, float(m.get("inicio") or 0.0), licenca_da_musica(p) or {})


def _creditos(r: dict) -> list[str]:
    cred = []

    def add(x):
        if isinstance(x, dict) and x.get("credito"):
            cred.append(str(x["credito"]).strip())
    add(r.get("video"))
    add(r.get("foto"))
    for f in r.get("fotos") or []:
        add(f)
    for it in r.get("recortes") or []:
        add(it.get("foto"))
        add(it.get("clipe"))
    return cred


def _time(r: dict, lado: str) -> dict:
    t = dict(r[lado])
    t.setdefault("sigla", sigla_de(t["nome"]))
    return t


def linha_placar(mand: dict, vis: dict, estilo: dict, tam_escudo: int = 220,
                 lado_destaque: str | None = None, largura: int = LARG_UTIL) -> Image.Image:
    """Escudo + nome | placar | escudo + nome (o lado do gol em destaque)."""
    colw = int(largura * 0.32)
    nm = texto_ajustado(mand["nome"].upper(), estilo, colw, 2, 40, 26, contorno=2)
    nv = texto_ajustado(vis["nome"].upper(), estilo, colw, 2, 40, 26, contorno=2)
    h = tam_escudo + 14 + max(nm.height, nv.height)
    img = Image.new("RGBA", (largura, h), (0, 0, 0, 0))
    cx_m, cx_v, cx_c = colw // 2, largura - colw // 2, largura // 2
    img.alpha_composite(escudo(mand, tam_escudo, estilo), (cx_m - tam_escudo // 2, 0))
    img.alpha_composite(escudo(vis, tam_escudo, estilo), (cx_v - tam_escudo // 2, 0))
    img.alpha_composite(nm, (cx_m - nm.width // 2, tam_escudo + 14))
    img.alpha_composite(nv, (cx_v - nv.width // 2, tam_escudo + 14))
    d = ImageDraw.Draw(img)
    fn = fonte(int(tam_escudo * 0.66), True, estilo)
    fx = fonte(int(tam_escudo * 0.36), True, estilo)
    gm, gv = str(mand["gols"]), str(vis["gols"])
    while larg(gm, fn) + larg(gv, fn) + 90 > largura - 2 * colw + 40 and fn.size > 40:
        fn = fonte(fn.size - 6, True, estilo)
    cm = cor(estilo, "destaque") if lado_destaque == "mandante" else cor(estilo, "texto")
    cv = cor(estilo, "destaque") if lado_destaque == "visitante" else cor(estilo, "texto")
    ym = tam_escudo // 2
    esc = cor(estilo, "escuro")
    d.text((cx_c - 42, ym), gm, font=fn, anchor="rm", fill=cm, stroke_width=5, stroke_fill=esc)
    d.text((cx_c, ym), "x", font=fx, anchor="mm", fill=cor(estilo, "texto2"))
    d.text((cx_c + 42, ym), gv, font=fn, anchor="lm", fill=cv, stroke_width=5, stroke_fill=esc)
    return img


# --------------------------------------------------------------------- gol
def arte_cartao_gol(r: dict, estilo: dict) -> Image.Image:
    """Cartão de abertura (2 s): GOL!, time, placar, autor e minuto."""
    img = fundo_marca(estilo)
    topo, y_cab = cabecalho(estilo, "GOL")
    lado = r["time_do_gol"].lower()
    t = _time(r, lado)
    gol = bloco_texto(["GOL!"], fonte(230, True, estilo), cor(estilo, "destaque"),
                      contorno=8, cor_contorno=cor(estilo, "escuro"))
    artigo = str(t.get("artigo") or "do").upper()
    do_time = texto_ajustado(f"{artigo} {t['nome'].upper()}", estilo, LARG_UTIL, 1, 70, 40,
                             contorno=3)
    placar = linha_placar(_time(r, "mandante"), _time(r, "visitante"), estilo, 220, lado)
    autor = pilula(f"{str(r['autor']).upper()}  ·  {fmt_minuto(r['minuto'])}", estilo,
                   tam=60, fundo="destaque", cor_txt="escuro", pad_x=36, pad_y=18,
                   larg_max=LARG_UTIL)
    camp = (texto_ajustado(r["campeonato"], estilo, LARG_UTIL, 2, 40, 28, cor_txt="texto2")
            if r.get("campeonato") else None)
    corpo = empilhar([(gol, 0), (do_time, 0), (placar, 56), (autor, 56), (camp, 34)],
                     y_cab + 30, ZONA_Y1 - 20)
    sprites = topo + corpo + _extra(r, estilo)
    conferir_zona(sprites, "cartão do gol")
    return colar(img, sprites)


def faixa_placar_gol(r: dict, estilo: dict, largura: int = LARG_UTIL) -> Image.Image:
    """Faixa do topo durante o vídeo: 'FLA 2 x 1 PAL' + 'GOL DE PEDRO · 67''."""
    m, v = _time(r, "mandante"), _time(r, "visitante")
    lado = r["time_do_gol"].lower()
    f1 = fonte(62, True, estilo)
    l2 = texto_ajustado(f"GOL DE {str(r['autor']).upper()}  ·  {fmt_minuto(r['minuto'])}",
                        estilo, largura - 60, 1, 42, 28, cor_txt="destaque")
    a1, d1 = metricas(f1)
    h = 22 + a1 + d1 + 6 + l2.height + 18
    img = Image.new("RGBA", (largura, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, largura - 1, h - 1), 30,
                        fill=rgba(estilo["cores"]["caixa"], int(255 * estilo["caixa_opacidade"])))
    cx, y = largura // 2, 22
    cm = cor(estilo, "destaque") if lado == "mandante" else cor(estilo, "texto")
    cv = cor(estilo, "destaque") if lado == "visitante" else cor(estilo, "texto")
    d.text((cx - 36, y), f"{m['sigla']}  {m['gols']}", font=f1, anchor="ra", fill=cm)
    d.text((cx, y + 6), "x", font=fonte(44, True, estilo), anchor="ma", fill=cor(estilo, "texto2"))
    d.text((cx + 36, y), f"{v['gols']}  {v['sigla']}", font=f1, anchor="la", fill=cv)
    img.alpha_composite(l2, ((largura - l2.width) // 2, 22 + a1 + d1 + 6))
    return img


def plano_gol(r: dict, estilo: dict, saida: Path) -> Plano:
    v = r["video"]
    arq = Path(v["arquivo"])
    info = info_midia(arq)
    ini = float(v.get("inicio") or 0.0)
    fim = float(v["fim"]) if v.get("fim") is not None else float(info["duracao"])
    dclip = fim - ini
    dcart = float(r.get("duracao_cartao") or 2.0)
    cartao = _preguicoso(lambda: arte_cartao_gol(r, estilo))
    seg_cartao = SegQuadros("cartao_gol", dcart, lambda t: cartao(), chave=lambda t: 0,
                            descricao="cartão de 2 s (placar, times, minuto, autor)")

    legs = normalizar_legendas(r["legenda"], dclip)
    caixas = [caixa_texto(t, estilo, tam_max=50, tam_min=34, max_linhas=4) for t, _a, _b in legs]
    h_leg = max(c.height for c in caixas)
    cred = pilula(credito_video(v["credito"]), estilo, tam=30, fundo="caixa", cor_txt="texto",
                  opacidade=0.75, larg_max=LARG_UTIL)
    topo, y_cab = cabecalho(estilo, "GOL")
    faixa = faixa_placar_gol(r, estilo)
    y_faixa = y_cab + 18
    extra = _extra(r, estilo)
    ow, oh = info["largura"], info["altura"]
    fixos = topo + [Sprite(faixa, (LARGURA - faixa.width) // 2, y_faixa)]

    if ow / oh >= 0.9:
        # vídeo deitado/quadrado: janela no meio, fundo do canal em volta
        y0 = y_faixa + faixa.height + 26
        y_fim = ZONA_Y1 - 12
        hmax = y_fim - y0 - (12 + cred.height + 16 + h_leg)
        k = min(LARGURA / ow, hmax / oh)
        vw, vh = int(ow * k) // 2 * 2, int(oh * k) // 2 * 2
        bloco = vh + 12 + cred.height + 16 + h_leg
        yb = y0 + max(0, (y_fim - y0 - bloco) // 2)
        seg = SegClipe("gol_video", arq, ini, dclip, (ow, oh),
                       janela=((LARGURA - vw) // 2, yb, vw, vh), ajuste="encaixar",
                       cor_fundo=estilo["cores"]["fundo"], tem_audio=True,
                       descricao="vídeo oficial com o áudio original")
        vx, vy, vw2, vh2 = seg.geometria()["vis"]
        y_cred = vy + vh2 + 12
        x_cred = min(vx + vw2, LARGURA - MARGEM) - cred.width
        y_leg = y_cred + cred.height + 16
        fixos.append(Sprite(cred, x_cred, y_cred))
        pos_leg = [(MARGEM, y_leg) for _c in caixas]
        base_moldura = lambda: _moldura_com_janela(estilo, (vx, vy, vw2, vh2), [])  # noqa: E731
    else:
        # vídeo em pé: cobre a tela; degradês escuros atrás dos textos
        seg = SegClipe("gol_video", arq, ini, dclip, (ow, oh), janela=(0, 0, LARGURA, ALTURA),
                       ajuste="cobrir", cor_fundo=estilo["cores"]["fundo"], tem_audio=True,
                       descricao="vídeo oficial com o áudio original")
        pos_leg = [(MARGEM, ZONA_Y1 - 12 - c.height) for c in caixas]
        y_cred = ZONA_Y1 - 12 - h_leg - 12 - cred.height
        fixos.append(Sprite(cred, LARGURA - MARGEM - cred.width, y_cred))
        y_top = y_faixa + faixa.height + 80

        def base_moldura():
            b = Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, 0))
            b.alpha_composite(degrade(y_top, 170, 0), (0, 0))
            y_b = y_cred - 140
            b.alpha_composite(degrade(ALTURA - y_b, 0, 190), (0, y_b))
            return b

    legs_sprites = [Sprite(c, x, y) for c, (x, y) in zip(caixas, pos_leg)]
    conferir_zona(fixos + legs_sprites + extra, "gol")
    if len(legs) == 1:
        fixos.append(legs_sprites[0])
        seg.temporizados = []
    else:
        seg.temporizados = [((lambda s=s: s), a, b) for s, (_t, a, b) in zip(legs_sprites, legs)]
    seg.moldura = lambda: compor(fixos + extra, base=base_moldura())
    return Plano("gol", [seg_cartao, seg], saida, estilo, None,
                 {"creditos": _creditos(r), "fonte_tipo": v.get("fonte_tipo"),
                  "legenda": [t for t, _a, _b in legs],
                  "video_origem": {"arquivo": str(arq), "inicio": ini, "fim": fim,
                                   "largura": ow, "altura": oh}})


# ----------------------------------------------------------------- notícia
def plano_noticia(r: dict, estilo: dict, saida: Path) -> Plano:
    fotos = r["fotos"]
    n = len(fotos)
    dpf = float(r["duracao_por_foto"])
    dur = n * dpf
    topo, y_cab = cabecalho(estilo, r.get("etiqueta") or "NOTÍCIA")
    tit = texto_ajustado(r["titulo"], estilo, LARG_UTIL, 3, 84, 50, contorno=4)
    y_tit = y_cab + 24
    fixos = topo + [Sprite(tit, MARGEM, y_tit)]
    y_apos = y_tit + tit.height
    if r.get("fonte"):
        ft = texto_ajustado(str(r["fonte"]), estilo, LARG_UTIL, 1, 32, 24, cor_txt="texto2", contorno=2)
        fixos.append(Sprite(ft, MARGEM, y_apos + 6))
        y_apos += 6 + ft.height
    legs = normalizar_legendas(r["legendas"], dur)
    caixas = [(caixa_texto(t, estilo, tam_max=50, tam_min=34, max_linhas=3), a, b)
              for t, a, b in legs]
    h_leg = max(c.height for c, _a, _b in caixas)
    leg_sprites = [(Sprite(c, MARGEM, ZONA_Y1 - 12 - c.height), a, b) for c, a, b in caixas]
    creds = [pilula(credito_foto(f["credito"]), estilo, tam=28, fundo="caixa", cor_txt="texto",
                    opacidade=0.75, larg_max=LARG_UTIL) for f in fotos]
    y_cred = ZONA_Y1 - 12 - h_leg - 12 - max(c.height for c in creds)
    cred_sprites = [Sprite(c, LARGURA - MARGEM - c.width, y_cred) for c in creds]
    extra = _extra(r, estilo)
    conferir_zona(fixos + cred_sprites + [s for s, _a, _b in leg_sprites] + extra, "notícia")

    area_y0, area_y1 = y_apos + 30, y_cred - 16
    grad = [Sprite(degrade(y_apos + 90, 200, 0), 0, 0),
            Sprite(degrade(ALTURA - (y_cred - 160), 0, 210), 0, y_cred - 160)]
    camadas = []
    for i, f in enumerate(fotos):
        w, h = _tam_foto(f["arquivo"])
        zoom = (1.0, 1.10) if i % 2 == 0 else (1.10, 1.0)
        deriva = [(0.5, 0.2), (-0.5, -0.2), (0.4, -0.3), (-0.4, 0.3)][i % 4]
        foco = tuple(f.get("foco") or (0.5, 0.4))
        if w / h >= 0.9:
            hj = min(round(LARGURA * h / w), area_y1 - area_y0)
            yj = area_y0 + (area_y1 - area_y0 - hj) // 2
            camadas.append({"modo": "encaixar", "y": yj,
                            "fundo": _preguicoso(lambda a=f["arquivo"]: fundo_desfocado(a, estilo)),
                            "kb": _preguicoso(lambda a=f["arquivo"], hj=hj, z=zoom, dv=deriva, fc=foco:
                                              FotoKB(a, LARGURA, hj, z[0], z[1], dv, fc))})
        else:
            camadas.append({"modo": "cobrir",
                            "kb": _preguicoso(lambda a=f["arquivo"], z=zoom, dv=deriva, fc=foco:
                                              FotoKB(a, LARGURA, ALTURA, z[0], z[1], dv, fc))})

    def foto_em(i: int, t: float) -> Image.Image:
        c = camadas[i]
        p = clamp01((t - i * dpf) / dpf)
        if c["modo"] == "encaixar":
            q = c["fundo"]().copy()
            q.paste(c["kb"]().quadro(p), (0, c["y"]))
            return q
        return colar(c["kb"]().quadro(p), grad)

    def gerador(t: float) -> Image.Image:
        i = min(int(t // dpf), n - 1)
        dom = i
        if i < n - 1 and t > (i + 1) * dpf - XFADE / 2:
            a = (t - ((i + 1) * dpf - XFADE / 2)) / XFADE
            q = Image.blend(foto_em(i, t), foto_em(i + 1, t), clamp01(a))
            dom = i if a < 0.5 else i + 1
        elif i > 0 and t < i * dpf + XFADE / 2:
            a = (t - (i * dpf - XFADE / 2)) / XFADE
            q = Image.blend(foto_em(i - 1, t), foto_em(i, t), clamp01(a))
            dom = i - 1 if a < 0.5 else i
        else:
            q = foto_em(i, t)
        colar(q, fixos)
        colar(q, [cred_sprites[dom]])
        colar(q, [s for s, a, b in leg_sprites if a <= t < b])
        return colar(q, extra)

    seg = SegQuadros("noticia", dur, gerador,
                     descricao=f"{n} fotos com zoom lento, título e legenda queimada")
    return Plano("noticia", [seg], saida, estilo, _musica(r),
                 {"creditos": _creditos(r), "legenda": [t for t, _a, _b in legs]})


# ------------------------------------------------------------------ debate
def painel_jogador(it: dict, i: int, n: int, estilo: dict, largura: int = LARG_UTIL) -> Image.Image:
    pad = 30
    ind = pilula(f"{i + 1}/{n}", estilo, tam=30, fundo="destaque", cor_txt="escuro")
    nome = texto_ajustado(str(it["nome"]).upper(), estilo, largura - 2 * pad - ind.width - 20,
                          1, 60, 34, alinhamento="esquerda")
    time_img = (texto_ajustado(str(it["time"]), estilo, largura - 2 * pad, 1, 36, 26,
                               cor_txt="texto2", negrito=False, alinhamento="esquerda")
                if it.get("time") else None)
    num_txt = str(it["numero"]).strip()
    fn = fonte(150, True, estilo)
    while larg(num_txt, fn) > largura * 0.55 and fn.size > 60:
        fn = fonte(fn.size - 8, True, estilo)
    num = bloco_texto([num_txt], fn, cor(estilo, "destaque"), contorno=4,
                      cor_contorno=cor(estilo, "escuro"))
    rot = (texto_ajustado(str(it["rotulo"]), estilo, largura - 2 * pad - num.width - 26, 3, 44, 28,
                          alinhamento="esquerda") if it.get("rotulo") else None)
    h1 = max(ind.height, nome.height)
    h = pad + h1 + (6 + time_img.height if time_img else 0) + 8 + max(num.height, rot.height if rot else 0) + pad
    img = Image.new("RGBA", (largura, h), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle(
        (0, 0, largura - 1, h - 1), 30,
        fill=rgba(estilo["cores"]["caixa"], int(255 * estilo["caixa_opacidade"])))
    img.alpha_composite(ind, (pad, pad + (h1 - ind.height) // 2))
    img.alpha_composite(nome, (pad + ind.width + 20, pad + (h1 - nome.height) // 2))
    y = pad + h1
    if time_img:
        img.alpha_composite(time_img, (pad, y + 6))
        y += 6 + time_img.height
    y += 8
    hb = max(num.height, rot.height if rot else 0)
    img.alpha_composite(num, (pad - 4, y + (hb - num.height) // 2))
    if rot:
        img.alpha_composite(rot, (pad + num.width + 22, y + (hb - rot.height) // 2))
    return img


def arte_final_debate(r: dict, estilo: dict) -> Image.Image:
    img = fundo_marca(estilo)
    topo, y_cab = cabecalho(estilo, "DEBATE")
    perg = texto_ajustado(r.get("pergunta_final") or r["titulo"], estilo, LARG_UTIL, 3, 72, 46,
                          contorno=3)
    itens = [(perg, 0)]
    for i, it in enumerate(r["recortes"]):
        txt = f"{i + 1}.  {it['nome']} — {it['numero']}"
        if it.get("rotulo"):
            txt += f" {it['rotulo']}"
        itens.append((caixa_texto(txt, estilo, tam_max=44, tam_min=30, max_linhas=2,
                                  alinhamento="esquerda", pad_y=20), 44 if i == 0 else 16))
    comenta = bloco_texto(["COMENTA AÍ!"], fonte(118, True, estilo), cor(estilo, "destaque"),
                          contorno=6, cor_contorno=cor(estilo, "escuro"))
    if comenta.width > LARG_UTIL:
        k = LARG_UTIL / comenta.width
        comenta = comenta.resize((LARG_UTIL, int(comenta.height * k)), Image.LANCZOS)
    itens += [(comenta, 50), (seta_para_baixo(110, cor(estilo, "destaque")), 14)]
    sprites = topo + empilhar(itens, y_cab + 30, ZONA_Y1 - 20) + _extra(r, estilo)
    conferir_zona(sprites, "tela final do debate")
    return colar(img, sprites)


def plano_debate(r: dict, estilo: dict, saida: Path) -> Plano:
    rec = r["recortes"]
    dr, dfin = float(r["duracao_recorte"]), float(r["duracao_final"])
    topo, y_cab = cabecalho(estilo, "DEBATE")
    tit = texto_ajustado(r["titulo"], estilo, LARG_UTIL, 2, 66, 44, contorno=3)
    y_tit = y_cab + 22
    y_m0 = y_tit + tit.height + 22
    paineis = [painel_jogador(it, i, len(rec), estilo) for i, it in enumerate(rec)]
    y_pan = ZONA_Y1 - 12 - max(p.height for p in paineis)
    y_m1 = y_pan - 22
    y_m0 += y_m0 % 2
    jw, jh = LARG_UTIL, (y_m1 - y_m0) // 2 * 2
    extra = _extra(r, estilo)
    comuns = topo + [Sprite(tit, MARGEM, y_tit)]
    mascara = _mascara_cantos(jw, jh)
    segs = []
    for i, it in enumerate(rec):
        pan = Sprite(paineis[i], MARGEM, y_pan)
        midia = it.get("foto") or it.get("clipe")
        txt_cred = credito_foto(midia["credito"]) if it.get("foto") else credito_video(midia["credito"])
        cp = pilula(txt_cred, estilo, tam=26, fundo="caixa", cor_txt="texto", opacidade=0.75,
                    larg_max=jw - 28)
        cred = Sprite(cp, MARGEM + jw - 14 - cp.width, y_m0 + jh - 14 - cp.height)
        conferir_zona(comuns + [pan, cred] + extra, f"debate recorte {i + 1}")
        if it.get("foto"):
            z = (1.0, 1.10) if i % 2 == 0 else (1.10, 1.0)
            kb = _preguicoso(lambda a=midia["arquivo"], z=z, fc=tuple(midia.get("foco") or (0.5, 0.3)):
                             FotoKB(a, jw, jh, z[0], z[1], (0.3, -0.3), fc))
            base = _preguicoso(lambda pan=pan: colar(fundo_marca(estilo), comuns + [pan]))

            def gerador(t, kb=kb, base=base, cred=cred):
                q = base().copy()
                q.paste(kb().quadro(t / dr), (MARGEM, y_m0), mascara)
                return colar(q, [cred] + extra)
            segs.append(SegQuadros(f"recorte{i + 1}", dr, gerador,
                                   descricao=f"foto de {it['nome']} com zoom lento"))
        else:
            info = info_midia(midia["arquivo"])
            ini = float(midia.get("inicio") or 0.0)
            seg = SegClipe(f"recorte{i + 1}", Path(midia["arquivo"]), ini, dr,
                           (info["largura"], info["altura"]), janela=(MARGEM, y_m0, jw, jh),
                           ajuste="cobrir", cor_fundo=estilo["cores"]["fundo"],
                           tem_audio=bool(info["tem_audio"]),
                           descricao=f"clipe oficial de {it['nome']} com áudio original")
            vis = seg.geometria()["vis"]
            seg.moldura = (lambda vis=vis, pan=pan, cred=cred:
                           _moldura_com_janela(estilo, vis, comuns + [pan, cred] + extra))
            segs.append(seg)
    final = _preguicoso(lambda: arte_final_debate(r, estilo))
    segs.append(SegQuadros("comenta_ai", dfin, lambda t: final(), chave=lambda t: 0,
                           descricao="tela final 'comenta aí'"))
    return Plano("debate", segs, saida, estilo, _musica(r), {"creditos": _creditos(r)})


# ------------------------------------------------------------- estatística
def plano_estatistica(r: dict, estilo: dict, saida: Path) -> Plano:
    dur, dc = float(r["duracao"]), float(r["duracao_contagem"])
    valor = float(_num(r["valor"]))
    casas = int(r.get("casas_decimais") or 0)
    pre, suf = str(r.get("prefixo") or ""), str(r.get("sufixo") or "")
    topo, y_cab = cabecalho(estilo, r.get("etiqueta") or "ESTATÍSTICA")
    tit = texto_ajustado(r["titulo"], estilo, LARG_UTIL, 3, 76, 48, contorno=3)
    y_tit = y_cab + 26
    rot = texto_ajustado(r["rotulo"], estilo, LARG_UTIL - 60, 3, 56, 36, contorno=2)
    sprites = topo + [Sprite(tit, MARGEM, y_tit)]
    y_base = ZONA_Y1 - 16
    if r.get("fonte"):
        ft = texto_ajustado(str(r["fonte"]), estilo, LARG_UTIL, 1, 32, 24, cor_txt="texto2",
                            contorno=2)
        y_base -= ft.height
        sprites.append(Sprite(ft, (LARGURA - ft.width) // 2, y_base))
        y_base -= 12
    if r.get("foto"):
        cp = pilula(credito_foto(r["foto"]["credito"]), estilo, tam=26, fundo="caixa",
                    cor_txt="texto", opacidade=0.75, larg_max=LARG_UTIL)
        y_base -= cp.height
        sprites.append(Sprite(cp, LARGURA - MARGEM - cp.width, y_base))
        y_base -= 12
    final_txt = f"{pre}{formatar_numero(valor, casas)}{suf}"
    fn = fonte(300, True, estilo)
    while larg(final_txt, fn) > LARG_UTIL and fn.size > 60:
        fn = fonte(fn.size - 10, True, estilo)
    a, d = metricas(fn)
    h_num = a + d
    barra_w, barra_h = 700, 18
    y0 = y_tit + tit.height + 30
    bloco = h_num + 26 + barra_h + 44 + rot.height
    y_num = y0 + max(0, (y_base - y0 - bloco) // 2)
    y_barra = y_num + h_num + 26
    y_rot = y_barra + barra_h + 44
    sprites.append(Sprite(rot, (LARGURA - rot.width) // 2, y_rot))
    extra = _extra(r, estilo)
    conferir_zona(sprites + extra, "estatística")
    if y_num < y0 - 1 or y_rot + rot.height > y_base + 1:
        raise ErroReel("estatística: texto grande demais para a tela (encurte título/rótulo)")
    xb = (LARGURA - barra_w) // 2

    def fazer_base():
        if r.get("foto"):
            foto = ImageOps.fit(abrir_rgb(r["foto"]["arquivo"]), (LARGURA, ALTURA), Image.BICUBIC,
                                centering=tuple(r["foto"].get("foco") or (0.5, 0.35)))
            b = Image.blend(foto, Image.new("RGB", (LARGURA, ALTURA), rgb(estilo["cores"]["fundo"])), 0.62)
        else:
            b = fundo_marca(estilo)
        colar(b, sprites)
        ImageDraw.Draw(b).rounded_rectangle((xb, y_barra, xb + barra_w, y_barra + barra_h),
                                            barra_h // 2, fill=rgb(estilo["cores"]["fundo2"]))
        return b
    base = _preguicoso(fazer_base)
    ce, cd = cor(estilo, "destaque"), cor(estilo, "escuro")

    def progresso(t):
        return suave(t / dc) if dc > 0 else 1.0

    def gerador(t):
        p = progresso(t)
        q = base().copy()
        dr_ = ImageDraw.Draw(q)
        s = f"{pre}{formatar_numero(valor * p, casas)}{suf}"
        dr_.text((LARGURA // 2, y_num), s, font=fn, anchor="ma", fill=ce, stroke_width=6,
                 stroke_fill=cd)
        dr_.rounded_rectangle((xb, y_barra, xb + max(barra_h, int(barra_w * p)), y_barra + barra_h),
                              barra_h // 2, fill=ce)
        return colar(q, extra)

    def chave(t):
        p = progresso(t)
        return (formatar_numero(valor * p, casas), int(barra_w * p))
    seg = SegQuadros("estatistica", dur, gerador, chave,
                     descricao=f"contador de 0 a {final_txt} em {dc:.1f}s")
    return Plano("estatistica", [seg], saida, estilo, _musica(r), {"creditos": _creditos(r)})


# --------------------------------------------------------------- resultado
def _linha_gol(g: dict, estilo: dict, tam: int, largura: int, direita: bool) -> Image.Image:
    """'Pedro 12'' com uma bolinha; coluna da direita fica espelhada."""
    tipo = str(g.get("tipo") or "").strip().lower()
    suf = {"penalti": " (pên.)", "pênalti": " (pên.)", "contra": " (contra)"}.get(
        tipo, f" ({tipo})" if tipo else "")
    txt = f"{g['autor']} {fmt_minuto(g['minuto'])}{suf}"
    icone = tam // 2 + 4
    t = texto_ajustado(txt, estilo, largura - icone - 14, 1, tam, max(22, tam - 14),
                       alinhamento="direita" if direita else "esquerda")
    h = max(t.height, icone)
    img = Image.new("RGBA", (largura, h), (0, 0, 0, 0))
    yi = (h - icone) // 2
    if direita:
        img.alpha_composite(t, (0, (h - t.height) // 2))
        xi = largura - icone
    else:
        img.alpha_composite(t, (icone + 14, (h - t.height) // 2))
        xi = 0
    ImageDraw.Draw(img).ellipse((xi, yi, xi + icone, yi + icone), fill=cor(estilo, "texto"),
                                outline=cor(estilo, "escuro"), width=3)
    return img


def plano_resultado(r: dict, estilo: dict, saida: Path) -> Plano:
    dur = float(r["duracao"])
    m, v = _time(r, "mandante"), _time(r, "visitante")
    topo, y_cab = cabecalho(estilo, "RESULTADO")
    fim = pilula(str(r.get("etiqueta_placar") or "FIM DE JOGO"), estilo, tam=40, fundo="destaque",
                 cor_txt="escuro", pad_x=30, pad_y=14)
    camp = (texto_ajustado(str(r["campeonato"]), estilo, LARG_UTIL, 2, 42, 30, cor_txt="texto2")
            if r.get("campeonato") else None)
    venc = "mandante" if m["gols"] > v["gols"] else "visitante" if v["gols"] > m["gols"] else None
    placar = linha_placar(m, v, estilo, 250, venc)
    rodape_txt = " · ".join(str(x) for x in (r.get("estadio"), r.get("data")) if x)
    rodape = (texto_ajustado(rodape_txt, estilo, LARG_UTIL, 1, 36, 24, cor_txt="texto2")
              if rodape_txt else None)
    y_ini = y_cab + 30
    y_lim = ZONA_Y1 - 16 - (rodape.height + 20 if rodape else 0)
    gols = r.get("gols") or []
    pad = 26
    colw = (LARG_UTIL - 2 * pad) // 2 - 10
    por_lado = max([sum(1 for g in gols if str(g["time"]).lower() == lado)
                    for lado in ("mandante", "visitante")] + [0])
    fixo_h = fim.height + 16 + (camp.height if camp else 0) + 40 + placar.height
    tam = 50
    while tam > 26 and fixo_h + 46 + por_lado * (tam * 1.2 + 14) + 2 * pad > y_lim - y_ini:
        tam -= 4
    linhas_gol = [(g, _linha_gol(g, estilo, tam, colw, str(g["time"]).lower() == "visitante"))
                  for g in gols]
    alt_lado = {lado: sum(img.height + 14 for g, img in linhas_gol
                          if str(g["time"]).lower() == lado) - 14
                for lado in ("mandante", "visitante")}
    caixa_h = (max(alt_lado.values()) + 2 * pad) if linhas_gol else 0
    total = fixo_h + (46 + caixa_h if caixa_h else 0)
    y = y_ini + max(0, (y_lim - y_ini - total) // 2)
    fixos = topo + [Sprite(fim, (LARGURA - fim.width) // 2, y)]
    y += fim.height + 16
    if camp:
        fixos.append(Sprite(camp, (LARGURA - camp.width) // 2, y))
        y += camp.height
    y += 40
    fixos.append(Sprite(placar, MARGEM, y))
    y += placar.height + 46
    if rodape:
        fixos.append(Sprite(rodape, (LARGURA - rodape.width) // 2, y_lim + 20))
    gol_sprites = []
    if caixa_h:
        cx_img = Image.new("RGBA", (LARG_UTIL, caixa_h), (0, 0, 0, 0))
        ImageDraw.Draw(cx_img).rounded_rectangle(
            (0, 0, LARG_UTIL - 1, caixa_h - 1), 28,
            fill=rgba(estilo["cores"]["caixa"], int(255 * 0.38)))
        fixos.append(Sprite(cx_img, MARGEM, y))
        ys = {"mandante": y + pad, "visitante": y + pad}
        for g, img in linhas_gol:
            lado = str(g["time"]).lower()
            x = MARGEM + pad if lado == "mandante" else LARGURA - MARGEM - pad - colw
            gol_sprites.append(Sprite(img, x, ys[lado]))
            ys[lado] += img.height + 14
    extra = _extra(r, estilo)
    conferir_zona(fixos + gol_sprites + extra, "resultado")
    base = _preguicoso(lambda: colar(fundo_marca(estilo), fixos))
    inicios = [0.5 + 0.35 * k for k in range(len(gol_sprites))]

    def alfas(t):
        return [clamp01((t - t0) / 0.3) for t0 in inicios]

    def gerador(t):
        q = base().copy()
        for s, a in zip(gol_sprites, alfas(t)):
            if a > 0:
                colar(q, [s], alfa=a)
        return colar(q, extra)
    seg = SegQuadros("resultado", dur, gerador, lambda t: tuple(round(a * 12) for a in alfas(t)),
                     descricao="placar final com escudos e gols entrando um a um")
    return Plano("resultado", [seg], saida, estilo, _musica(r), {"creditos": _creditos(r)})


# ------------------------------------------------------------------ tabela
CORES_ZONA = {"libertadores": "#3B82F6", "pre_libertadores": "#93C5FD",
              "sulamericana": "#22C55E", "rebaixamento": "#EF4444", "acesso": "#22C55E"}
NOMES_ZONA = {"libertadores": "Libertadores", "pre_libertadores": "Pré-Libertadores",
              "sulamericana": "Sul-Americana", "rebaixamento": "Rebaixamento",
              "acesso": "Acesso"}
ROTULOS_COL = {"pts": "P", "j": "J", "v": "V", "e": "E", "d": "D", "sg": "SG", "gp": "GP"}


def _zonas(r: dict) -> list[dict]:
    saida = []
    for nome, z in (r.get("zonas") or {}).items():
        if isinstance(z, dict):
            de, ate = int(z.get("de", 0)), int(z.get("ate", 0))
            c, rot = z.get("cor"), z.get("rotulo")
        else:
            de, ate = int(z[0]), int(z[1])
            c, rot = None, None
        saida.append({"de": de, "ate": ate, "cor": c or CORES_ZONA.get(nome) or cor_de_time(nome),
                      "rotulo": rot or NOMES_ZONA.get(nome, nome.replace("_", " ").title())})
    return saida


def plano_tabela(r: dict, estilo: dict, saida: Path) -> Plano:
    dur = float(r["duracao"])
    linhas = sorted(r["linhas"], key=lambda x: _num(x["pos"]))
    top = int(r.get("top") or min(len(linhas), 10))
    linhas = linhas[:top]
    n = len(linhas)
    zonas = _zonas(r)
    destaque = {str(x).lower() for x in (r.get("destaque") or [])}
    cols = [c for c in ("pts", "j", "v", "sg") if c == "pts" or all(c in ln for ln in linhas)]
    topo, y_cab = cabecalho(estilo, "TABELA")
    tit = texto_ajustado(r["titulo"], estilo, LARG_UTIL, 2, 64, 44, contorno=3)
    y = y_cab + 22
    fixos = topo + [Sprite(tit, MARGEM, y)]
    y += tit.height
    if r.get("subtitulo"):
        sub = texto_ajustado(str(r["subtitulo"]), estilo, LARG_UTIL, 1, 36, 26, cor_txt="texto2")
        fixos.append(Sprite(sub, MARGEM, y + 4))
        y += 4 + sub.height
    y += 22
    y_lim = ZONA_Y1 - 14
    if r.get("fonte"):
        ft = texto_ajustado(str(r["fonte"]), estilo, LARG_UTIL, 1, 28, 22, cor_txt="texto2")
        y_lim -= ft.height
        fixos.append(Sprite(ft, (LARGURA - ft.width) // 2, y_lim))
        y_lim -= 10
    if zonas:
        fz = fonte(26, True, estilo)
        partes = []
        for z in zonas:
            w = 26 + 10 + int(larg(z["rotulo"], fz)) + 30
            im = Image.new("RGBA", (w, 34), (0, 0, 0, 0))
            dz = ImageDraw.Draw(im)
            dz.rounded_rectangle((0, 4, 26, 30), 6, fill=rgba(z["cor"]))
            dz.text((36, 17), z["rotulo"], font=fz, anchor="lm", fill=cor(estilo, "texto2"))
            partes.append(im)
        wl = sum(p.width for p in partes)
        leg = Image.new("RGBA", (max(1, wl), 34), (0, 0, 0, 0))
        x = 0
        for p in partes:
            leg.alpha_composite(p, (x, 0))
            x += p.width
        if leg.width > LARG_UTIL:
            leg = leg.resize((LARG_UTIL, int(34 * LARG_UTIL / leg.width)), Image.LANCZOS)
        y_lim -= leg.height
        fixos.append(Sprite(leg, (LARGURA - leg.width) // 2, y_lim))
        y_lim -= 12
    # cabeçalho das colunas
    col_w = 92
    x_cols = [LARG_UTIL - 24 - col_w * (len(cols) - 1 - k) for k in range(len(cols))]
    fcab = fonte(28, True, estilo)
    hdr = Image.new("RGBA", (LARG_UTIL, 40), (0, 0, 0, 0))
    dh = ImageDraw.Draw(hdr)
    dh.text((44, 20), "#", font=fcab, anchor="mm", fill=cor(estilo, "texto2"))
    dh.text((92, 20), "TIME", font=fcab, anchor="lm", fill=cor(estilo, "texto2"))
    for c, xc in zip(cols, x_cols):
        dh.text((xc, 20), ROTULOS_COL[c], font=fcab, anchor="rm", fill=cor(estilo, "texto2"))
    fixos.append(Sprite(hdr, MARGEM, y))
    y += hdr.height + 6
    passo = min(92, (y_lim - y) // max(1, n))
    if passo < 30:
        raise ErroReel("tabela: linhas demais para a tela (use 'top' menor)")
    alt = passo - max(4, passo // 12)
    fs = max(18, int(alt * 0.5))
    fb, fnrm = fonte(fs, True, estilo), fonte(fs, False, estilo)
    larg_nome = x_cols[0] - col_w + 20 - 92
    linhas_sp = []
    for k, ln in enumerate(linhas):
        pos = int(_num(ln["pos"]))
        img = Image.new("RGBA", (LARG_UTIL, alt), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        e_dest = str(ln["time"]).lower() in destaque
        fundo_l = rgba(estilo["cores"]["destaque"], 70) if e_dest else \
            rgba(estilo["cores"]["caixa"], 150 if k % 2 == 0 else 105)
        d.rounded_rectangle((0, 0, LARG_UTIL - 1, alt - 1), min(18, alt // 3), fill=fundo_l,
                            outline=cor(estilo, "destaque") if e_dest else None,
                            width=3 if e_dest else 0)
        for z in zonas:
            if z["de"] <= pos <= z["ate"]:
                d.rounded_rectangle((0, 0, 10, alt - 1), 5, fill=rgba(z["cor"]))
                break
        cy = alt // 2
        d.text((44, cy), str(pos), font=fb, anchor="mm", fill=cor(estilo, "texto"))
        nome = str(ln["time"])
        while larg(nome, fnrm if not e_dest else fb) > larg_nome and len(nome) > 3:
            nome = nome[:-2] + "…"
        d.text((92, cy), nome, font=fb if e_dest else fnrm, anchor="lm", fill=cor(estilo, "texto"))
        for c, xc in zip(cols, x_cols):
            val = ln.get(c, "")
            d.text((xc, cy), str(val), font=fb if c == "pts" else fnrm, anchor="rm",
                   fill=cor(estilo, "destaque") if c == "pts" else cor(estilo, "texto"))
        linhas_sp.append(Sprite(img, MARGEM, y + k * passo))
    extra = _extra(r, estilo)
    conferir_zona(fixos + linhas_sp + extra, "tabela")
    base = _preguicoso(lambda: colar(fundo_marca(estilo), fixos))
    inicios = [0.3 + min(0.1, 2.0 / max(1, n)) * k for k in range(n)]

    def alfas(t):
        return [clamp01((t - t0) / 0.35) for t0 in inicios]

    def gerador(t):
        q = base().copy()
        for s, a in zip(linhas_sp, alfas(t)):
            if a <= 0:
                continue
            desl = int((1 - suave(a)) * 80)
            cimg, al = s.partes()
            if a < 1:
                al = al.point(lambda px, k=a: int(px * k))
            q.paste(cimg, (s.x + desl, s.y), al)
        return colar(q, extra)
    seg = SegQuadros("tabela", dur, gerador, lambda t: tuple(round(a * 20) for a in alfas(t)),
                     descricao=f"classificação (top {n}) entrando linha a linha")
    return Plano("tabela", [seg], saida, estilo, _musica(r), {"creditos": _creditos(r)})


CONSTRUTORES = {"gol": plano_gol, "noticia": plano_noticia, "debate": plano_debate,
                "estatistica": plano_estatistica, "resultado": plano_resultado,
                "tabela": plano_tabela}


def construir_plano(r: dict, estilo: dict, saida: Path) -> Plano:
    return CONSTRUTORES[r["modo"]](r, estilo, Path(saida))
