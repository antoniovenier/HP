"""Base do gerador de artes de story (scripts/story_artes*.py): zonas, spec, texto, formas.

O que faz: tudo o que os 3 modelos (chamada, maissobre, interacao) e os 6 canais
compartilham — acha o hpbase (marca.py) no PC ou no repositório, valida o spec,
quebra e ajusta texto (reduz a letra até um mínimo e recusa em português se não
couber), desenha pílula, cartão com cantos arredondados, seta vetorial, selo HP,
trata a foto (marca.TRATAMENTO_FOTO, cor natural) e guarda cada texto numa camada
própria com o bbox (é assim que os testes conferem zona segura e contraste sem
olhar a imagem).

Uso: só importado por story_artes.py, story_artes_modelos.py e story_artes_canais.py.

Regras: nada de hora, random sem semente ou caminho absoluto dentro da imagem
(a mesma entrada dá o mesmo SHA-256); sem emoji (marca.sem_emoji); nenhum texto
nos 250 px do topo nem nos 350 px da base; fontes só por marca.fonte()
(no Linux de teste cai no DejaVu; no PC saem as fontes reais).
"""
from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

AQUI = Path(__file__).resolve().parent


def caminho_hp_studio() -> Path | None:
    """Acha a pasta que contém o pacote hpbase e põe no sys.path (mesmo truque do reel_futebol_base)."""
    cands: list[Path] = []
    env = os.environ.get("HP_APP")
    if env:
        cands += [Path(env), Path(env) / "hp_studio_nuvem", Path(env) / "hp_studio"]
    cands += [AQUI.parent / "app" / "hp_studio_nuvem",
              AQUI.parent / "06 Projeto" / "app" / "hp_studio_nuvem",
              AQUI.parent / "app" / "hp_studio",
              AQUI.parent / "06 Projeto" / "app" / "hp_studio"]
    for c in cands:
        if (c / "hpbase" / "__init__.py").exists():
            if str(c) not in sys.path:
                sys.path.insert(0, str(c))
            return c
    return None


caminho_hp_studio()

from hpbase import escrever_json, ler_json  # noqa: E402
from hpbase import marca  # noqa: E402

# ---------------------------------------------------------------- formato
LARGURA, ALTURA = marca.TAMANHOS["story"]          # 1080 x 1920
SAFE_TOPO, SAFE_BASE = marca.SAFE_TOPO, marca.SAFE_BASE
Y_SEGURO0 = SAFE_TOPO                 # 250
Y_SEGURO1 = ALTURA - SAFE_BASE        # 1570
ZONA_LINK = tuple(marca.ZONA_LINK)        # (140, 1500, 940, 1640)
ZONA_ENQUETE = tuple(marca.ZONA_ENQUETE)  # (110, 930, 970, 1480)
MARGEM = 110                          # margem lateral dos elementos
X0, X1 = MARGEM, LARGURA - MARGEM     # 110 .. 970 (largura útil 860)
TIPOS = ("chamada", "maissobre", "interacao")
FIGURINHAS = ("link", "enquete")
FIGURINHAS_PADRAO = {"chamada": ["link"], "maissobre": ["link"], "interacao": ["enquete"]}
ROTULO_PADRAO = {"chamada": "NOVO POST", "maissobre": "MAIS SOBRE", "interacao": "SUA VEZ"}
CTA_PADRAO = {"maissobre": "Salva o post", "interacao": "Responde aí"}
# limite de caracteres por campo (texto já sem emoji e sem os asteriscos de destaque)
LIMITES = {"chamada": 45, "fato": 70, "pergunta": 60, "rotulo": 22, "cta": 24,
           "legenda": 48, "valor": 14, "credito_foto": 60}
QUALIDADE_JPG = 92
RAIO_CARTAO = 36


class ErroStory(ValueError):
    """Erro do gerador: mensagem sempre em português, para leigo."""


# ------------------------------------------------------------------ cores
def rgba(cor, a: int = 255) -> tuple:
    return tuple(marca.rgb(cor)[:3]) + (int(a),)


def rgb(cor) -> tuple:
    return tuple(marca.rgb(cor)[:3])


def legivel_sobre(fundo, claro="#FFFFFF", escuro="#0F0F12") -> str:
    """Texto claro ou escuro, o que contrasta mais com o fundo."""
    return claro if marca.contraste(claro, fundo) >= marca.contraste(escuro, fundo) else escuro


def clarear_ate_ler(cor, fundo, minimo: float = 4.5) -> tuple:
    """Clareia a cor (mistura com branco) até contrastar >= minimo com o fundo."""
    c = rgb(cor)
    for i in range(0, 21):
        t = i / 20.0
        m = marca.misturar(c, "#FFFFFF", t)
        if marca.contraste(m, fundo) >= minimo:
            return m
    return (255, 255, 255)


# ------------------------------------------------------------------- spec
def _texto(v) -> str:
    return marca.sem_emoji(str(v if v is not None else "")).strip()


def _sem_asterisco(t: str) -> str:
    return t.replace("*", "")


def _conferir_tamanho(campo: str, valor: str, limite: int) -> None:
    n = len(_sem_asterisco(valor))
    if n > limite:
        raise ErroStory(f"O campo '{campo}' tem {n} caracteres e o máximo é {limite}. "
                        f"Encurte o texto: \"{_sem_asterisco(valor)[:40]}…\"")


def _fracao(par, nome: str) -> tuple:
    if par is None:
        return (0.5, 0.5)
    try:
        x, y = float(par[0]), float(par[1])
    except (TypeError, ValueError, IndexError):
        raise ErroStory(f"O campo '{nome}' precisa ser [x, y] (ex.: [0.5, 0.4]); veio {par!r}.") from None
    if x > 1.0 or y > 1.0:   # veio em pixels da capa? deixa; enquadrar() trata >1 como pixel
        return (x, y)
    return (max(0.0, x), max(0.0, y))


def normalizar_spec(spec: dict) -> dict:
    """Preenche padrões, tira emoji e valida tudo (erro em português)."""
    if not isinstance(spec, dict):
        raise ErroStory("O spec precisa ser um objeto JSON (chaves canal, tipo, ...).")
    s = dict(spec)
    canal = str(s.get("canal", "")).strip().lower()
    if canal.startswith("@"):
        canal = marca.canal_por_handle(canal) or canal
    if canal not in marca.CANAIS:
        raise ErroStory(f"Canal '{s.get('canal')}' não existe. Use um destes: "
                        + ", ".join(marca.ORDEM_CANAIS) + ".")
    tipo = str(s.get("tipo", "")).strip().lower()
    if tipo not in TIPOS:
        raise ErroStory(f"Tipo '{s.get('tipo')}' não existe. Use chamada, maissobre ou interacao.")
    figs = s.get("figurinhas")
    if figs is None:
        figs = list(FIGURINHAS_PADRAO[tipo])
    if isinstance(figs, str):
        figs = [figs]
    figs = [str(f).strip().lower() for f in figs]
    for f in figs:
        if f not in FIGURINHAS:
            raise ErroStory(f"Figurinha '{f}' não existe. Use 'link' e/ou 'enquete'.")
    figs = list(dict.fromkeys(figs))
    if tipo == "maissobre" and "enquete" in figs:
        raise ErroStory("O modelo 'maissobre' não tem lugar para a enquete; use só [\"link\"] "
                        "ou faça um story 'interacao'.")
    if tipo == "interacao" and "enquete" not in figs:
        figs = ["enquete", *figs]

    out = {
        "canal": canal, "tipo": tipo, "figurinhas": figs,
        "capa": str(s["capa"]) if s.get("capa") else None,
        "rotulo": _texto(s.get("rotulo") or ROTULO_PADRAO[tipo]).upper(),
        "chamada": _texto(s.get("chamada")),
        "fatos": [_texto(f) for f in (s.get("fatos") or []) if _texto(f)],
        "pergunta": _texto(s.get("pergunta")),
        "credito_foto": _texto(s.get("credito_foto")),
        "cta": _texto(s.get("cta") or CTA_PADRAO.get(tipo, "")),
        "saida": str(s["saida"]) if s.get("saida") else None,
        "nome": _texto(s.get("nome")) or f"story_{canal}_{tipo}",
        "foco": _fracao(s.get("foco"), "foco"),
        "fotos_prefere": None,
        "dado_forte": None,
        "cor_destaque": None,
        "avisos": [],
    }
    nome_ok = all(ch.isalnum() or ch in "_-." for ch in out["nome"])
    if not nome_ok:
        raise ErroStory(f"O 'nome' do arquivo só pode ter letras, números, '_', '-' e '.': veio {out['nome']!r}.")
    _conferir_tamanho("rotulo", out["rotulo"], LIMITES["rotulo"])
    if out["cta"]:
        _conferir_tamanho("cta", out["cta"], LIMITES["cta"])
    if out["credito_foto"]:
        _conferir_tamanho("credito_foto", out["credito_foto"], LIMITES["credito_foto"])

    cd = s.get("cor_destaque")
    if cd:
        try:
            marca.rgb(cd)
        except ValueError:
            raise ErroStory(f"cor_destaque inválida: {cd!r} (use '#RRGGBB').") from None
        if canal == "futebol":
            out["cor_destaque"] = marca.hex_de(cd)
        else:
            out["avisos"].append(f"cor_destaque só vale no Futebol (cor do clube); no canal {canal} foi ignorada.")

    if tipo == "chamada":
        if not out["chamada"]:
            raise ErroStory("O modelo 'chamada' precisa do campo 'chamada' (a frase do post, até 45 caracteres).")
        _conferir_tamanho("chamada", out["chamada"], LIMITES["chamada"])
    elif tipo == "maissobre":
        n = len(out["fatos"])
        if n < 2 or n > 4:
            raise ErroStory(f"O modelo 'maissobre' precisa de 2 a 4 'fatos'; vieram {n}.")
        for i, f in enumerate(out["fatos"], 1):
            _conferir_tamanho(f"fatos[{i}]", f, LIMITES["fato"])
        df = s.get("dado_forte")
        if df:
            if not isinstance(df, dict) or not _texto(df.get("valor")):
                raise ErroStory("'dado_forte' precisa ser {\"valor\": \"...\", \"legenda\": \"...\"}.")
            valor, legenda = _texto(df.get("valor")), _texto(df.get("legenda"))
            _conferir_tamanho("dado_forte.valor", valor, LIMITES["valor"])
            if legenda:
                _conferir_tamanho("dado_forte.legenda", legenda, LIMITES["legenda"])
            out["dado_forte"] = {"valor": valor, "legenda": legenda}
        if out["chamada"]:
            _conferir_tamanho("chamada", out["chamada"], LIMITES["chamada"])
    else:  # interacao
        if not out["pergunta"]:
            raise ErroStory("O modelo 'interacao' precisa do campo 'pergunta' (até 60 caracteres).")
        _conferir_tamanho("pergunta", out["pergunta"], LIMITES["pergunta"])
        fp = s.get("fotos_prefere")
        if fp:
            if not isinstance(fp, (list, tuple)) or len(fp) != 2:
                raise ErroStory("'fotos_prefere' precisa ser uma lista com 2 imagens [a, b].")
            out["fotos_prefere"] = [str(fp[0]), str(fp[1])]
    return out


# ------------------------------------------------------------------ texto
def fonte(nome: str, tamanho: int):
    return marca.fonte(nome, tamanho)


def tokens_destaque(texto: str) -> list[list[tuple[str, bool]]]:
    """Palavras com pedaços marcados: '*GTA 6*, já' -> [[('GTA',True)], [('6',True), (',',False)], [('já',False)]].

    Cada palavra é uma lista de pedaços (texto, destaque) desenhados sem espaço entre si,
    para a pontuação colada ao *destaque* não ganhar espaço ("milhões*?" fica "milhões?").
    """
    palavras: list[list[tuple[str, bool]]] = []
    atual: list[tuple[str, bool]] = []
    for i, parte in enumerate(str(texto).split("*")):
        dest = (i % 2 == 1)
        if not parte:
            continue
        if parte[0].isspace() and atual:
            palavras.append(atual)
            atual = []
        for j, pedaco in enumerate(parte.split()):
            if j > 0 and atual:
                palavras.append(atual)
                atual = []
            atual.append((pedaco, dest))
        if parte[-1].isspace() and atual:
            palavras.append(atual)
            atual = []
    if atual:
        palavras.append(atual)
    return palavras


def palavra_plana(palavra) -> str:
    return "".join(t for t, _ in palavra)


def largura_texto(texto: str, f) -> float:
    return float(f.getlength(texto))


def altura_linha(f, fator: float = 1.06) -> int:
    asc, desc = f.getmetrics()
    return int(round((asc + desc) * fator))


def quebrar(tokens, f, largura: float, max_linhas: int):
    """Quebra por palavra; None se uma palavra não cabe ou passa de max_linhas."""
    linhas: list[list] = []
    atual: list = []
    for tok in tokens:
        cand = atual + [tok]
        if largura_texto(" ".join(palavra_plana(t) for t in cand), f) <= largura:
            atual = cand
            continue
        if not atual or largura_texto(palavra_plana(tok), f) > largura:
            return None
        linhas.append(atual)
        atual = [tok]
    if atual:
        linhas.append(atual)
    if len(linhas) > max_linhas:
        return None
    return linhas


def ajustar(texto: str, nome_fonte: str, largura: int, max_linhas: int,
            tam_max: int, tam_min: int, campo: str = "texto", passo: int = 2,
            alt_max: int | None = None, entrelinha: float = 1.06):
    """Maior letra em que o texto cabe em (largura, max_linhas[, alt_max]); erro em português se não couber."""
    toks = tokens_destaque(texto)
    if not toks:
        raise ErroStory(f"O campo '{campo}' está vazio.")
    for tam in range(int(tam_max), int(tam_min) - 1, -passo):
        f = fonte(nome_fonte, tam)
        linhas = quebrar(toks, f, largura, max_linhas)
        if linhas is None:
            continue
        if alt_max is not None and len(linhas) * altura_linha(f, entrelinha) > alt_max:
            continue
        return f, linhas, tam
    plano = _sem_asterisco(texto)
    raise ErroStory(f"O texto \"{plano[:48]}\" não cabe em {max_linhas} linha(s) de {largura} px "
                    f"nem com a letra no mínimo ({tam_min} px). Encurte o '{campo}'.")


@dataclass
class Camada:
    """Um texto (ou elemento) desenhado numa camada própria, com o bbox já na tela."""
    nome: str
    bbox: tuple | None
    texto: bool
    cores: list = field(default_factory=list)
    imagem: Image.Image | None = None     # RGBA recortada no bbox (só texto)
    pos: tuple = (0, 0)

    def resumo(self) -> dict:
        return {"nome": self.nome, "bbox": list(self.bbox) if self.bbox else None,
                "texto": self.texto, "cores": [marca.hex_de(c) for c in self.cores]}


def bloco_texto(linhas, f, cor, cor_destaque=None, largura: int | None = None,
                alinhamento: str = "esq", degrade=None, contorno=None, contorno_largura: int = 0,
                italico: float = 0.0, entrelinha: float = 1.06, sublinhado=None) -> tuple[Image.Image, list]:
    """Desenha as linhas (palavras com pedaços marcados) numa imagem RGBA transparente.

    cor / cor_destaque: cor dos pedaços normais / dos *destacados*;
    degrade=[c1, c2]: pedaços normais pintados com degradê vertical (título do GTA);
    contorno: cor do contorno (stroke) de largura contorno_largura;
    italico: cisalhamento (0.2 = itálico falso para fonte sem versão itálica);
    sublinhado: cor de um traço grosso sob os *destacados* (quando a cor de destaque não
    lê sobre a superfície, ex.: faixa amarela do Receitas).
    Devolve (imagem, cores de texto usadas).
    """
    lh = altura_linha(f, entrelinha)
    asc, _ = f.getmetrics()
    sw = int(contorno_largura) if contorno else 0
    larguras = [largura_texto(" ".join(palavra_plana(t) for t in ln), f) for ln in linhas]
    w_cont = int(math.ceil(max(larguras))) + 2 * sw + 4
    W = int(largura) if largura else w_cont
    W = max(W, w_cont)
    H = lh * len(linhas) + 2 * sw + 6
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    mask = Image.new("L", (W, H), 0) if degrade else None
    d = ImageDraw.Draw(img)
    dm = ImageDraw.Draw(mask) if mask is not None else None
    cor_n = rgb(cor) if cor is not None else None
    cor_d = rgb(cor_destaque) if cor_destaque is not None else cor_n
    espaco = largura_texto(" ", f)
    esp_sub = max(4, int(f.size * 0.09))
    usados_normais = usados_dest = False
    for i, ln in enumerate(linhas):
        lw = larguras[i]
        if alinhamento == "centro":
            x = (W - lw) / 2.0
        elif alinhamento == "dir":
            x = W - lw - sw - 2
        else:
            x = sw + 2
        y = sw + 2 + i * lh
        for palavra in ln:
            for pedaco, dest in palavra:
                wp = largura_texto(pedaco, f)
                if dest:
                    usados_dest = True
                    d.text((x, y), pedaco, font=f, fill=cor_d + (255,),
                           stroke_width=sw, stroke_fill=rgba(contorno) if sw else None)
                    if sublinhado is not None:
                        yb = y + asc + 3
                        d.rounded_rectangle([x, yb, x + wp, yb + esp_sub], radius=esp_sub // 2,
                                            fill=rgba(sublinhado))
                elif degrade:
                    usados_normais = True
                    if sw:
                        d.text((x, y), pedaco, font=f, fill=rgba(contorno),
                               stroke_width=sw, stroke_fill=rgba(contorno))
                    dm.text((x, y), pedaco, font=f, fill=255)
                else:
                    usados_normais = True
                    d.text((x, y), pedaco, font=f, fill=cor_n + (255,),
                           stroke_width=sw, stroke_fill=rgba(contorno) if sw else None)
                x += wp
            x += espaco
    cores_usadas: list = []
    if degrade and usados_normais:
        c1, c2 = rgb(degrade[0]), rgb(degrade[1])
        t = np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None, None]
        arr = (np.array(c1, dtype=np.float32)[None, None, :] * (1 - t)
               + np.array(c2, dtype=np.float32)[None, None, :] * t)
        arr = np.repeat(arr, W, axis=1)
        grad = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
        img.paste(grad, (0, 0), mask)
        cores_usadas += [c1, c2]
    elif usados_normais and cor_n is not None:
        cores_usadas.append(cor_n)
    if usados_dest and cor_d is not None:
        cores_usadas.append(cor_d)
    if italico:
        k = float(italico)
        extra = int(math.ceil(k * H))
        img = img.transform((W + extra, H), Image.AFFINE, (1, k, -k * H, 0, 1, 0),
                            resample=Image.BICUBIC)
    return img, cores_usadas


# ------------------------------------------------------------------- tela
class Tela:
    """O quadro 1080x1920: fundo + elementos (no fundo) + textos (camadas próprias)."""

    def __init__(self, fundo: Image.Image | None = None):
        self.base = (fundo.convert("RGBA") if fundo is not None
                     else Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, 255)))
        self.camadas: list[Camada] = []

    # elementos não-texto vão direto no fundo (registrados com bbox)
    def elemento(self, nome: str, img: Image.Image, pos: tuple, cores=()) -> tuple | None:
        img = img if img.mode == "RGBA" else img.convert("RGBA")
        bb = img.getbbox()
        self.base.alpha_composite(img, dest=(int(pos[0]), int(pos[1])))
        bbox = None
        if bb:
            bbox = (bb[0] + int(pos[0]), bb[1] + int(pos[1]), bb[2] + int(pos[0]), bb[3] + int(pos[1]))
        self.camadas.append(Camada(nome, bbox, False, [rgb(c) for c in cores]))
        return bbox

    def desenho(self) -> ImageDraw.ImageDraw:
        return ImageDraw.Draw(self.base)

    def registrar(self, nome: str, bbox: tuple, cores=()) -> None:
        """Registra um elemento desenhado direto com desenho()."""
        self.camadas.append(Camada(nome, tuple(int(v) for v in bbox), False, [rgb(c) for c in cores]))

    def texto(self, nome: str, img: Image.Image, pos: tuple, cores) -> tuple | None:
        bb = img.getbbox()
        if not bb:
            self.camadas.append(Camada(nome, None, True, [rgb(c) for c in cores]))
            return None
        rec = img.crop(bb)
        x, y = int(pos[0]) + bb[0], int(pos[1]) + bb[1]
        bbox = (x, y, x + rec.width, y + rec.height)
        self.camadas.append(Camada(nome, bbox, True, [rgb(c) for c in cores], rec, (x, y)))
        return bbox

    def fundo_sem_texto(self) -> Image.Image:
        return self.base.convert("RGB")

    def compor(self) -> Image.Image:
        final = self.base.copy()
        for c in self.camadas:
            if c.texto and c.imagem is not None:
                final.alpha_composite(c.imagem, dest=c.pos)
        return final.convert("RGB")

    def textos(self) -> list[Camada]:
        return [c for c in self.camadas if c.texto]


# ----------------------------------------------------------------- formas
def degrade_vertical(tam: tuple, paradas: list) -> Image.Image:
    """paradas = [(y_fracao, cor), ...] de cima para baixo -> imagem RGB."""
    w, h = tam
    ys = np.arange(h, dtype=np.float32) / max(1, h - 1)
    pts = sorted((float(p), rgb(c)) for p, c in paradas)
    canais = []
    for k in range(3):
        xp = [p for p, _ in pts]
        fp = [c[k] for _, c in pts]
        canais.append(np.interp(ys, xp, fp))
    col = np.stack(canais, axis=-1).astype(np.float32)       # (h, 3)
    arr = np.repeat(col[:, None, :], w, axis=1)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def degrade_diagonal(tam: tuple, c1, c2) -> Image.Image:
    w, h = tam
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    t = (xx / max(1, w - 1) + yy / max(1, h - 1)) / 2.0
    a, b = np.array(rgb(c1), np.float32), np.array(rgb(c2), np.float32)
    arr = a[None, None, :] * (1 - t[..., None]) + b[None, None, :] * t[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def brilho_radial(tam: tuple, centro: tuple, raio: float, cor, forca: float = 0.5) -> Image.Image:
    """Camada RGBA com um brilho suave (alpha cai com o quadrado da distância)."""
    w, h = tam
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt((xx - centro[0]) ** 2 + (yy - centro[1]) ** 2) / float(raio)
    a = np.clip(1.0 - d, 0.0, 1.0) ** 2 * forca * 255.0
    r, g, b = rgb(cor)
    arr = np.zeros((h, w, 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = r, g, b
    arr[..., 3] = a.astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def pilula_imagem(tam: tuple, cor_fundo, contorno=None, contorno_largura: int = 0,
                  forma: str = "pilula", alpha: int = 255) -> Image.Image:
    """Forma de fundo de uma etiqueta: 'pilula' (cantos redondos), 'etiqueta' (paralelogramo), 'caixa'."""
    w, h = tam
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    fill = rgba(cor_fundo, alpha) if cor_fundo is not None else None
    out = rgba(contorno) if contorno else None
    if forma == "etiqueta":
        k = int(h * 0.28)
        d.polygon([(k, 0), (w - 1, 0), (w - 1 - k, h - 1), (0, h - 1)], fill=fill,
                  outline=out, width=max(1, contorno_largura) if out else 0)
    elif forma == "caixa":
        d.rectangle([0, 0, w - 1, h - 1], fill=fill, outline=out, width=contorno_largura if out else 0)
    else:
        d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=fill, outline=out,
                            width=contorno_largura if out else 0)
    return img


def arredondar(img: Image.Image, raio: int = RAIO_CARTAO) -> Image.Image:
    img = img.convert("RGBA")
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, img.width - 1, img.height - 1], radius=raio, fill=255)
    img.putalpha(mask)
    return img


def contorno_arredondado(tam: tuple, raio: int, cor, largura: int = 3, alpha: int = 255) -> Image.Image:
    w, h = tam
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle([0, 0, w - 1, h - 1], radius=raio, outline=rgba(cor, alpha),
                                          width=largura)
    return img


def seta_imagem(p0: tuple, p1: tuple, cor, largura: int = 12, curva: float = 0.35,
                ponta: int = 44) -> tuple[Image.Image, tuple]:
    """Seta vetorial (bezier quadrática + ponta triangular) numa camada RGBA do tamanho da tela.

    Devolve (imagem, bbox na tela). p0 = começo, p1 = ponta.
    """
    x0, y0 = float(p0[0]), float(p0[1])
    x1, y1 = float(p1[0]), float(p1[1])
    dx, dy = x1 - x0, y1 - y0
    dist = math.hypot(dx, dy) or 1.0
    # ponto de controle deslocado na perpendicular (curva > 0 = barriga para a direita)
    mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    px, py = -dy / dist, dx / dist
    cx, cy = mx + px * curva * dist, my + py * curva * dist
    pts = []
    for i in range(41):
        t = i / 40.0
        bx = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t ** 2 * x1
        by = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t ** 2 * y1
        pts.append((bx, by))
    # encurta o traço para a ponta não ficar grossa
    tx, ty = pts[-1][0] - pts[-3][0], pts[-1][1] - pts[-3][1]
    tn = math.hypot(tx, ty) or 1.0
    tx, ty = tx / tn, ty / tn
    fim = (x1 - tx * ponta * 0.75, y1 - ty * ponta * 0.75)
    linha = [p for p in pts[:-3]] + [fim]
    img = Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = rgba(cor)
    d.line(linha, fill=c, width=largura, joint="curve")
    r = largura / 2.0
    d.ellipse([x0 - r, y0 - r, x0 + r, y0 + r], fill=c)
    bx, by = x1 - tx * ponta, y1 - ty * ponta
    nx, ny = -ty, tx
    meia = ponta * 0.58
    d.polygon([(x1, y1), (bx + nx * meia, by + ny * meia), (bx - nx * meia, by - ny * meia)], fill=c)
    return img, img.getbbox()


# ------------------------------------------------------------------- fotos
def abrir_imagem(caminho) -> Image.Image:
    p = Path(caminho)
    if not p.is_file():
        raise ErroStory(f"Não achei a imagem: {p}")
    try:
        img = Image.open(p)
        img.load()
    except Exception as e:  # noqa: BLE001 - mensagem para leigo
        raise ErroStory(f"Não consegui abrir a imagem {p.name}: {e}") from e
    return img.convert("RGB")


def tratar_foto(img: Image.Image) -> Image.Image:
    """marca.TRATAMENTO_FOTO: contraste x1.12, cor x1.10, brilho x0.96, vinheta 0.55 (cor natural)."""
    t = marca.TRATAMENTO_FOTO
    img = img.convert("RGB")
    img = ImageEnhance.Contrast(img).enhance(t["contraste"])
    img = ImageEnhance.Color(img).enhance(t["cor"])
    img = ImageEnhance.Brightness(img).enhance(t["brilho"])
    w, h = img.size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    nx = (xx - (w - 1) / 2.0) / (w / 2.0)
    ny = (yy - (h - 1) / 2.0) / (h / 2.0)
    dist = np.sqrt(nx ** 2 + ny ** 2) / math.sqrt(2.0)
    fator = 1.0 - float(t["vinheta"]) * np.clip(dist, 0.0, 1.0) ** 2
    arr = np.asarray(img).astype(np.float32) * fator[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def enquadrar(img: Image.Image, tam: tuple, foco=(0.5, 0.5)) -> Image.Image:
    """Recorta no tamanho pedido mantendo o foco (fração 0-1, ou pixels da imagem original)."""
    tw, th = int(tam[0]), int(tam[1])
    W, H = img.size
    fx, fy = float(foco[0]), float(foco[1])
    if fx > 1.0:
        fx = fx / max(1, W)
    if fy > 1.0:
        fy = fy / max(1, H)
    fx, fy = min(1.0, max(0.0, fx)), min(1.0, max(0.0, fy))
    escala = max(tw / W, th / H)
    nw, nh = max(tw, int(math.ceil(W * escala))), max(th, int(math.ceil(H * escala)))
    img = img.resize((nw, nh), Image.LANCZOS)
    cx, cy = fx * nw, fy * nh
    x0 = int(round(min(max(cx - tw / 2.0, 0), nw - tw)))
    y0 = int(round(min(max(cy - th / 2.0, 0), nh - th)))
    return img.crop((x0, y0, x0 + tw, y0 + th))


def capa_gerada(tam: tuple, cor_a, cor_b, cor_brilho) -> Image.Image:
    """Capa de reserva quando o post não tem imagem: degradê do canal com brilhos (sem texto)."""
    w, h = int(tam[0]), int(tam[1])
    peq = (max(8, w // 8), max(8, h // 8))
    base = degrade_diagonal(peq, cor_a, cor_b).convert("RGBA")
    for cx, cy, r, forca in ((0.78, 0.28, 0.55, 0.55), (0.18, 0.82, 0.45, 0.35)):
        g = brilho_radial(peq, (cx * peq[0], cy * peq[1]), r * peq[0], cor_brilho, forca)
        base.alpha_composite(g)
    base = base.filter(ImageFilter.GaussianBlur(2))
    return base.resize((w, h), Image.BICUBIC).convert("RGB")


# ------------------------------------------------------------------- zonas
def zonas_de(figurinhas: list) -> dict:
    """{"link": [...], "link_fracao": [...], "enquete": ...} só das figurinhas pedidas."""
    z: dict = {"largura": LARGURA, "altura": ALTURA, "figurinhas": list(figurinhas)}
    for nome, ret in (("link", ZONA_LINK), ("enquete", ZONA_ENQUETE)):
        if nome in figurinhas:
            z[nome] = [int(v) for v in ret]
            z[nome + "_fracao"] = [round(ret[0] / LARGURA, 4), round(ret[1] / ALTURA, 4),
                                   round(ret[2] / LARGURA, 4), round(ret[3] / ALTURA, 4)]
    return z


def gravar_imagem(img: Image.Image, caminho: Path, formato: str) -> Path:
    """Grava JPG (qualidade fixa) ou PNG de forma atômica e determinística (sem data, sem EXIF)."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tmp = caminho.with_name(caminho.name + ".tmp")
    if formato == "png":
        img.save(tmp, format="PNG", optimize=False, compress_level=6)
    else:
        img.save(tmp, format="JPEG", quality=QUALIDADE_JPG, subsampling=0, optimize=False)
    os.replace(tmp, caminho)
    return caminho


__all__ = [
    "AQUI", "caminho_hp_studio", "marca", "escrever_json", "ler_json",
    "LARGURA", "ALTURA", "SAFE_TOPO", "SAFE_BASE", "Y_SEGURO0", "Y_SEGURO1",
    "ZONA_LINK", "ZONA_ENQUETE", "MARGEM", "X0", "X1", "TIPOS", "FIGURINHAS",
    "FIGURINHAS_PADRAO", "ROTULO_PADRAO", "CTA_PADRAO", "LIMITES", "QUALIDADE_JPG",
    "RAIO_CARTAO", "ErroStory", "rgba", "rgb", "legivel_sobre", "clarear_ate_ler",
    "normalizar_spec", "fonte", "tokens_destaque", "largura_texto", "altura_linha",
    "quebrar", "ajustar", "palavra_plana", "Camada", "bloco_texto", "Tela", "degrade_vertical",
    "degrade_diagonal", "brilho_radial", "pilula_imagem", "arredondar",
    "contorno_arredondado", "seta_imagem", "abrir_imagem", "tratar_foto", "enquadrar",
    "capa_gerada", "zonas_de", "gravar_imagem",
]
