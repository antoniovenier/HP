"""Arte do Futebol | HP com Pillow: estilo, fontes, texto, caixas, fundos.

Tudo o que aparece escrito no vídeo é desenhado aqui como imagem (PNG/RGBA)
e depois sobreposto — assim o montador não depende de libass/fontconfig do
ffmpeg (que no Windows costumam dar problema).
"""
from __future__ import annotations

import colorsys
import copy
import hashlib
import os
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

from reel_futebol_base import (ALTURA, LARGURA, MARGEM, ZONA_Y0, ZONA_Y1,
                               ErroReel, ler_json, raiz_local)
from hpbase import marca   # o reel_futebol_base já pôs o hpbase no sys.path

# ------------------------------------------------------------------ estilo
# A paleta vem da marca única (hpbase/marca.py, Seção 4.6): verde #1ED760 do
# posts_futebol.py como destaque (o amarelo #FFD23F da rodada 1 não vale mais),
# fundo (10,16,12) e verde escuro #12A850 só como tom do degradê do fundo
# (misturado 25 % no fundo, para o texto branco continuar legível).
_FUTEBOL = marca.CANAIS["futebol"]
ESTILO_PADRAO: dict = {
    "marca": "FUTEBOL | HP",
    "arroba": _FUTEBOL["handle"],
    "cores": {
        "fundo": _FUTEBOL["fundo"],                       # #0A100C verde quase preto
        "fundo2": marca.hex_de(marca.misturar(_FUTEBOL["fundo"],
                                              _FUTEBOL["extras"]["verde_escuro"], 0.25)),
        "linhas": "#FFFFFF",      # linhas do campo (bem transparentes)
        "destaque": _FUTEBOL["destaque"],                 # #1ED760 verde HP
        "verde_escuro": _FUTEBOL["extras"]["verde_escuro"],   # #12A850 moldura/aspas/faixas
        "texto": "#FFFFFF",
        "texto2": "#BFD8CB",
        "escuro": _FUTEBOL["extras"]["preto"],            # #08090B
        "caixa": _FUTEBOL["extras"]["caixa"],             # caixa de legenda (semitransparente)
        "positivo": "#22C55E",
        "negativo": "#EF4444",
        "neutro": "#3B82F6",
        "alerta": "#F97316",
    },
    "caixa_opacidade": 0.62,
    "fonte": "",            # caminho de uma TTF negrito (vazio = procurar)
    "fonte_normal": "",     # caminho de uma TTF normal (vazio = procurar)
    "alvo_lufs": -14.0,
    "true_peak": -1.5,
    "lra": 11.0,
    "musica_db_relativo": -20.0,   # música fica 20 dB abaixo do alvo
    "musica_sozinha_db_relativo": -6.0,  # reel só com música (notícia): −20 LUFS, baixa mas audível
    "pasta_musicas": "",           # vazio = <HypadoLocal>\musicas_livres
    "video": {"preset": "veryfast", "crf": 20},
    "audio_kbps": 192,
    "duracao_max_s": 90,
    "limite_render_s": 600,
    "legenda_auto_cmd": ["{python}", "-X", "utf8", "{script}", "legenda_video", "{roteiro}"],
}


def _mesclar(dest: dict, novo: dict) -> dict:
    for k, v in (novo or {}).items():
        if isinstance(v, dict) and isinstance(dest.get(k), dict):
            _mesclar(dest[k], v)
        else:
            dest[k] = v
    return dest


def caminho_estilo_padrao() -> Path:
    return raiz_local() / "canais" / "futebol" / "estilo_reel.json"


def carregar_estilo(caminho: str | Path | None = None,
                    extra: dict | None = None) -> dict:
    """Estilo padrão + JSON do canal (se existir) + ajustes do roteiro."""
    est = copy.deepcopy(ESTILO_PADRAO)
    if caminho is None and caminho_estilo_padrao().exists():
        caminho = caminho_estilo_padrao()
    if caminho:
        dados = ler_json(Path(caminho))
        if not isinstance(dados, dict):
            raise ErroReel(f"estilo não encontrado ou inválido: {caminho}")
        _mesclar(est, dados)
    if extra:
        _mesclar(est, extra)
    for nome, valor in est["cores"].items():
        try:
            rgb(valor)
        except ErroReel as e:
            raise ErroReel(f"estilo: cor '{nome}' inválida ({valor!r})") from e
    return est


# ------------------------------------------------------------------- cores
def rgb(c) -> tuple:
    if isinstance(c, (list, tuple)):
        return tuple(int(x) for x in c[:3])
    s = str(c).strip().lstrip("#")
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    if len(s) != 6:
        raise ErroReel(f"cor inválida: {c!r}")
    try:
        return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError as e:
        raise ErroReel(f"cor inválida: {c!r}") from e


def rgba(c, a: int = 255) -> tuple:
    return rgb(c) + (int(a),)


def cor(estilo: dict, nome: str, a: int = 255) -> tuple:
    """Cor do estilo pelo nome ('destaque', 'texto'...) ou hex direto."""
    return rgba(estilo["cores"].get(nome, nome), a)


def hex_ffmpeg(c) -> str:
    r, g, b = rgb(c)
    return f"0x{r:02X}{g:02X}{b:02X}"


def cor_de_time(nome: str) -> str:
    """Cor estável para um time sem cor definida (hash do nome)."""
    h = int(hashlib.md5(nome.encode("utf-8")).hexdigest()[:6], 16)
    r, g, b = colorsys.hsv_to_rgb((h % 360) / 360, 0.65, 0.62)
    return "#%02X%02X%02X" % (int(r * 255), int(g * 255), int(b * 255))


def sem_acento(s: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFD", s)
                   if unicodedata.category(ch) != "Mn")


def sigla_de(nome: str) -> str:
    letras = [ch for ch in sem_acento(nome).upper() if ch.isalnum()]
    return "".join(letras[:3]) or "?"


# ------------------------------------------------------------------ fontes
NOMES_NEGRITO = ["arialbd.ttf", "segoeuib.ttf", "seguisb.ttf",
                 "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf",
                 "Arial Bold.ttf", "FreeSansBold.ttf", "NotoSans-Bold.ttf"]
NOMES_NORMAL = ["arial.ttf", "segoeui.ttf", "DejaVuSans.ttf",
                "LiberationSans-Regular.ttf", "Arial.ttf", "FreeSans.ttf",
                "NotoSans-Regular.ttf"]
PASTAS_UNIX = ["/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/dejavu",
               "/usr/share/fonts/TTF", "/usr/share/fonts/truetype/liberation",
               "/usr/share/fonts/truetype/freefont",
               "/usr/share/fonts/truetype/noto", "/Library/Fonts",
               "/System/Library/Fonts/Supplemental"]


def _pastas_fontes() -> list[Path]:
    pastas: list[Path] = []
    if os.name == "nt":
        pastas.append(Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts")
        loc = os.environ.get("LOCALAPPDATA")
        if loc:
            pastas.append(Path(loc) / "Microsoft" / "Windows" / "Fonts")
    pastas += [Path(p) for p in PASTAS_UNIX]
    return pastas


def achar_fonte(negrito: bool = True, preferida: str | None = None) -> str | None:
    """Procura uma fonte TTF, nesta ordem:

    1. a do estilo (campo "fonte"/"fonte_normal");
    2. variável HP_FONTE (negrito) / HP_FONTE_NORMAL;
    3. Windows: Arial Bold (arialbd.ttf), Segoe UI Bold;
    4. Linux: DejaVuSans-Bold, Liberation Sans; macOS: Arial Bold.
    Devolve None se nada existir (aí usa a fonte embutida do Pillow).
    """
    cands: list[Path] = []
    if preferida:
        cands.append(Path(preferida))
    env = os.environ.get("HP_FONTE" if negrito else "HP_FONTE_NORMAL")
    if env:
        cands.append(Path(env))
    nomes = NOMES_NEGRITO if negrito else NOMES_NORMAL
    for pasta in _pastas_fontes():
        cands += [pasta / n for n in nomes]
    for c in cands:
        try:
            if c.is_file():
                return str(c)
        except OSError:
            continue
    return None


@lru_cache(maxsize=16)
def _fonte_achada(negrito: bool, preferida: str | None) -> str | None:
    return achar_fonte(negrito, preferida)


@lru_cache(maxsize=512)
def _carregar_fonte(caminho: str | None, tam: int):
    if caminho:
        try:
            return ImageFont.truetype(caminho, tam)
        except OSError:
            pass
    try:  # Pillow >= 10.1 traz uma TTF embutida
        return ImageFont.load_default(size=tam)
    except TypeError:
        return ImageFont.load_default()


def fonte(tam: int, negrito: bool = True, estilo: dict | None = None):
    pref = (estilo or {}).get("fonte" if negrito else "fonte_normal") or None
    return _carregar_fonte(_fonte_achada(negrito, pref), max(8, int(tam)))


# ------------------------------------------------------------------- texto
_RASCUNHO = ImageDraw.Draw(Image.new("L", (4, 4)))


def larg(s: str, f) -> float:
    return _RASCUNHO.textlength(s, font=f)


def metricas(f) -> tuple[int, int]:
    try:
        return f.getmetrics()
    except AttributeError:  # fonte bitmap antiga
        return (f.size if hasattr(f, "size") else 11), 2


def altura_linha(f, fator: float = 1.12) -> int:
    a, d = metricas(f)
    return int(round((a + d) * fator))


def quebrar(texto: str, f, largura: float) -> list[str]:
    """Quebra automática por palavra (e por letra se a palavra não cabe)."""
    linhas: list[str] = []
    for par in str(texto).split("\n"):
        palavras = par.split()
        if not palavras:
            linhas.append("")
            continue
        atual = ""
        for p in palavras:
            teste = p if not atual else f"{atual} {p}"
            if larg(teste, f) <= largura:
                atual = teste
                continue
            if atual:
                linhas.append(atual)
            while larg(p, f) > largura and len(p) > 1:
                corte = len(p) - 1
                while corte > 1 and larg(p[:corte] + "-", f) > largura:
                    corte -= 1
                linhas.append(p[:corte] + "-")
                p = p[corte:]
            atual = p
        linhas.append(atual)
    return linhas


def ajustar(texto: str, largura: float, max_linhas: int, tam_max: int,
            tam_min: int, negrito: bool = True, estilo: dict | None = None):
    """Maior fonte (de tam_max até tam_min) em que o texto cabe em
    max_linhas; se nem no mínimo couber, corta com reticências."""
    tam = tam_max
    while True:
        f = fonte(tam, negrito, estilo)
        linhas = quebrar(texto, f, largura)
        if len(linhas) <= max_linhas or tam <= tam_min:
            break
        tam = max(tam_min, tam - max(2, tam // 12))
    if len(linhas) > max_linhas:
        linhas = linhas[:max_linhas]
        ult = linhas[-1]
        while ult and larg(ult + "…", f) > largura:
            ult = ult[:-1].rstrip()
        linhas[-1] = ult + "…"
    return f, linhas


def bloco_texto(linhas: list[str], f, cor_txt, alinhamento: str = "centro",
                contorno: int = 0, cor_contorno=(0, 0, 0, 255),
                fator: float = 1.12, largura: int | None = None) -> Image.Image:
    """Várias linhas numa imagem RGBA transparente do tamanho do texto."""
    lh = altura_linha(f, fator)
    a, d = metricas(f)
    w = largura or int(max([larg(l, f) for l in linhas] + [1])) + 2 * contorno + 4
    h = lh * (len(linhas) - 1) + a + d + 2 * contorno + 4
    img = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    for i, linha in enumerate(linhas):
        y = contorno + 2 + i * lh
        if alinhamento == "centro":
            x, anc = w / 2, "ma"
        elif alinhamento == "direita":
            x, anc = w - contorno - 2, "ra"
        else:
            x, anc = contorno + 2, "la"
        dr.text((x, y), linha, font=f, fill=cor_txt, anchor=anc,
                stroke_width=contorno, stroke_fill=cor_contorno)
    return img


def texto_ajustado(texto: str, estilo: dict, largura: int, max_linhas: int,
                   tam_max: int, tam_min: int, cor_txt="texto",
                   negrito: bool = True, alinhamento: str = "centro",
                   contorno: int = 0, fator: float = 1.1) -> Image.Image:
    f, linhas = ajustar(texto, largura - 2 * contorno - 4, max_linhas,
                        tam_max, tam_min, negrito, estilo)
    c = cor(estilo, cor_txt) if isinstance(cor_txt, str) else cor_txt
    return bloco_texto(linhas, f, c, alinhamento, contorno,
                       (0, 0, 0, 255), fator, largura=largura)


def caixa_texto(texto: str, estilo: dict, largura: int = LARGURA - 2 * MARGEM,
                tam_max: int = 54, tam_min: int = 34, max_linhas: int = 4,
                pad_x: int = 36, pad_y: int = 24, raio: int = 28,
                cor_fundo: str | None = None, opacidade: float | None = None,
                cor_txt: str = "texto", negrito: bool = True,
                alinhamento: str = "centro") -> Image.Image:
    """Caixa semitransparente com texto quebrado automaticamente."""
    f, linhas = ajustar(texto, largura - 2 * pad_x, max_linhas, tam_max,
                        tam_min, negrito, estilo)
    txt = bloco_texto(linhas, f, cor(estilo, cor_txt), alinhamento,
                      largura=largura - 2 * pad_x)
    h = txt.height + 2 * pad_y
    img = Image.new("RGBA", (largura, h), (0, 0, 0, 0))
    op = estilo["caixa_opacidade"] if opacidade is None else opacidade
    fundo = cor_fundo or estilo["cores"]["caixa"]
    ImageDraw.Draw(img).rounded_rectangle((0, 0, largura - 1, h - 1), raio,
                                          fill=rgba(estilo["cores"].get(fundo, fundo),
                                                    int(255 * op)))
    img.alpha_composite(txt, (pad_x, pad_y))
    return img


def pilula(texto: str, estilo: dict, tam: int = 34, fundo: str = "destaque",
           cor_txt: str = "escuro", pad_x: int = 24, pad_y: int = 12,
           opacidade: float = 1.0, negrito: bool = True,
           larg_max: int | None = None) -> Image.Image:
    """Etiqueta arredondada de uma linha (marca, crédito, minuto...)."""
    f = fonte(tam, negrito, estilo)
    while larg_max and tam > 16 and larg(texto, f) + 2 * pad_x > larg_max:
        tam -= 2
        f = fonte(tam, negrito, estilo)
    ref = f.getbbox("ÁgHj", anchor="ls")
    h = (ref[3] - ref[1]) + 2 * pad_y
    w = int(larg(texto, f)) + 2 * pad_x
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    dr.rounded_rectangle((0, 0, w - 1, h - 1), h // 2,
                         fill=cor(estilo, fundo, int(255 * opacidade)))
    bb = f.getbbox(texto, anchor="ls")
    base_y = h / 2 - (bb[1] + bb[3]) / 2
    dr.text((w / 2, base_y), texto, font=f, fill=cor(estilo, cor_txt), anchor="ms")
    return img


def formatar_numero(v: float, casas: int = 0) -> str:
    """1234.5 -> '1.234,5' (padrão brasileiro)."""
    s = f"{abs(float(v)):,.{int(casas)}f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return ("-" if float(v) < 0 else "") + s


def clamp01(p: float) -> float:
    return 0.0 if p < 0 else 1.0 if p > 1 else float(p)


def suave(p: float) -> float:
    """Desaceleração (ease-out cúbico)."""
    p = clamp01(p)
    return 1 - (1 - p) ** 3


# ----------------------------------------------------------------- sprites
@dataclass
class Sprite:
    """Imagem RGBA posicionada no quadro 1080x1920."""
    img: Image.Image
    x: int
    y: int
    _partes: tuple | None = field(default=None, repr=False)

    def __post_init__(self):
        self.x, self.y = int(round(self.x)), int(round(self.y))
        if self.img.mode != "RGBA":
            self.img = self.img.convert("RGBA")

    @property
    def w(self) -> int:
        return self.img.width

    @property
    def h(self) -> int:
        return self.img.height

    @property
    def base(self) -> int:
        return self.y + self.img.height

    def partes(self):
        if self._partes is None:
            self._partes = (self.img.convert("RGB"), self.img.getchannel("A"))
        return self._partes


def colar(quadro: Image.Image, sprites, alfa: float = 1.0) -> Image.Image:
    """Cola sprites num quadro RGB (in-place) respeitando a transparência."""
    for s in sprites:
        cor_img, a = s.partes()
        if alfa < 1.0:
            a = a.point(lambda v, k=alfa: int(v * k))
        quadro.paste(cor_img, (s.x, s.y), a)
    return quadro


def compor(sprites, tam=(LARGURA, ALTURA), base: Image.Image | None = None) -> Image.Image:
    """Junta sprites numa imagem RGBA do tamanho do quadro."""
    tela = base.convert("RGBA") if base is not None else Image.new("RGBA", tam, (0, 0, 0, 0))
    for s in sprites:
        tela.alpha_composite(s.img, (max(0, s.x), max(0, s.y)))
    return tela


def conferir_zona(sprites, onde: str = "") -> None:
    """Nada escrito nos 250 px do topo nem nos 350 px da base (Reels)."""
    for s in sprites:
        bb = s.img.getchannel("A").getbbox()
        if not bb:
            continue
        x0, y0, x1, y1 = s.x + bb[0], s.y + bb[1], s.x + bb[2], s.y + bb[3]
        if y0 < ZONA_Y0 or y1 > ZONA_Y1 or x0 < 0 or x1 > LARGURA:
            raise ErroReel(f"{onde}: elemento fora da área segura "
                           f"(y {y0}-{y1}, x {x0}-{x1}; a área livre é "
                           f"y {ZONA_Y0}-{ZONA_Y1})")


# ------------------------------------------------------------------ fundos
@lru_cache(maxsize=8)
def _fundo_cache(c1: tuple, c2: tuple, linhas: tuple) -> Image.Image:
    y = np.linspace(0.0, 1.0, ALTURA)[:, None, None]
    k = np.sin(np.pi * y) ** 1.4
    arr = np.array(c1, dtype=np.float32) * (1 - k) + np.array(c2, dtype=np.float32) * k
    arr = np.broadcast_to(arr, (ALTURA, LARGURA, 3)).astype(np.uint8)
    img = Image.fromarray(np.ascontiguousarray(arr), "RGB").convert("RGBA")
    ov = Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    cl = linhas + (20,)
    cx, cy = LARGURA // 2, ALTURA // 2
    d.line((0, cy, LARGURA, cy), fill=cl, width=6)
    d.ellipse((cx - 250, cy - 250, cx + 250, cy + 250), outline=cl, width=6)
    d.ellipse((cx - 12, cy - 12, cx + 12, cy + 12), fill=cl)
    d.rectangle((190, -10, 890, 330), outline=cl, width=6)
    d.rectangle((190, ALTURA - 330, 890, ALTURA + 10), outline=cl, width=6)
    return Image.alpha_composite(img, ov).convert("RGB")


def fundo_marca(estilo: dict) -> Image.Image:
    """Fundo do canal: degradê verde com linhas de campo bem suaves."""
    c = estilo["cores"]
    return _fundo_cache(rgb(c["fundo"]), rgb(c["fundo2"]), rgb(c["linhas"])).copy()


def degrade(altura: int, alfa_ini: int, alfa_fim: int, c=(0, 0, 0),
            largura: int = LARGURA) -> Image.Image:
    """Faixa RGBA com transparência em degradê (escurece atrás do texto)."""
    a = np.linspace(alfa_ini, alfa_fim, altura, dtype=np.float32)[:, None]
    a = np.broadcast_to(a, (altura, largura)).astype(np.uint8)
    img = Image.new("RGBA", (largura, altura), tuple(c) + (0,))
    img.putalpha(Image.fromarray(np.ascontiguousarray(a), "L"))
    return img


def abrir_rgb(caminho) -> Image.Image:
    try:
        img = Image.open(caminho)
        img.draft("RGB", (2400, 2400))  # JPEG grande abre mais rápido
        return ImageOps.exif_transpose(img).convert("RGB")
    except (OSError, ValueError) as e:
        raise ErroReel(f"não consegui abrir a imagem {caminho}: {e}") from e


def fundo_desfocado(caminho, estilo: dict, escurecer: float = 0.55) -> Image.Image:
    """A própria foto, desfocada e escurecida, cobrindo a tela."""
    img = abrir_rgb(caminho)
    peq = ImageOps.fit(img, (216, 384), Image.BILINEAR)
    peq = peq.filter(ImageFilter.GaussianBlur(9))
    grande = peq.resize((LARGURA, ALTURA), Image.BICUBIC)
    escuro = Image.new("RGB", (LARGURA, ALTURA), rgb(estilo["cores"]["fundo"]))
    return Image.blend(grande, escuro, escurecer)


class FotoKB:
    """Zoom lento (Ken Burns) feito no Pillow, quadro a quadro.

    Usa recorte com coordenadas fracionárias (resize com box), então o
    movimento é liso, sem a tremida do zoompan do ffmpeg — e é mais rápido.
    """

    def __init__(self, caminho, largura: int, altura: int,
                 zoom_ini: float = 1.0, zoom_fim: float = 1.10,
                 deriva=(0.0, 0.0), foco=(0.5, 0.5)):
        img = abrir_rgb(caminho)
        self.largura, self.altura = int(largura), int(altura)
        self.zi, self.zf = float(zoom_ini), float(zoom_fim)
        self.deriva = (float(deriva[0]), float(deriva[1]))
        zmax = max(self.zi, self.zf, 1.0)
        ar = self.largura / self.altura
        w0, h0 = img.size
        if w0 / h0 > ar:
            cw, ch = h0 * ar, float(h0)
        else:
            cw, ch = float(w0), w0 / ar
        cx = min(max(float(foco[0]) * w0, cw / 2), w0 - cw / 2)
        cy = min(max(float(foco[1]) * h0, ch / 2), h0 - ch / 2)
        caixa = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
        caixa = (max(0.0, caixa[0]), max(0.0, caixa[1]),
                 min(float(w0), caixa[2]), min(float(h0), caixa[3]))
        self.base = img.resize((round(self.largura * zmax), round(self.altura * zmax)),
                               Image.BICUBIC, box=caixa)

    def quadro(self, p: float) -> Image.Image:
        p = clamp01(p)
        z = self.zi + (self.zf - self.zi) * p
        bw, bh = self.base.size
        vw, vh = bw / z, bh / z
        cx = bw / 2 + self.deriva[0] * (bw - vw) / 2
        cy = bh / 2 + self.deriva[1] * (bh - vh) / 2
        x0 = min(max(0.0, cx - vw / 2), bw - vw)
        y0 = min(max(0.0, cy - vh / 2), bh - vh)
        caixa = (max(0.0, x0), max(0.0, y0), min(float(bw), x0 + vw), min(float(bh), y0 + vh))
        return self.base.resize((self.largura, self.altura), Image.BILINEAR, box=caixa)


def arredondar_cantos(img: Image.Image, raio: int) -> Image.Image:
    """Devolve RGBA com cantos arredondados."""
    img = img.convert("RGBA")
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, img.width - 1, img.height - 1), raio, fill=255)
    img.putalpha(m)
    return img


# ----------------------------------------------------------- peças comuns
Y_CABECALHO = ZONA_Y0 + 18


def cabecalho(estilo: dict, etiqueta: str | None) -> tuple[list[Sprite], int]:
    """Marca do canal à esquerda e etiqueta do formato à direita."""
    marca = pilula(estilo["marca"], estilo, tam=32, fundo="destaque", cor_txt="escuro")
    sprites = [Sprite(marca, MARGEM, Y_CABECALHO)]
    if etiqueta:
        et = pilula(etiqueta.upper(), estilo, tam=32, fundo="caixa",
                    cor_txt="texto", opacidade=0.55)
        sprites.append(Sprite(et, LARGURA - MARGEM - et.width, Y_CABECALHO))
    return sprites, Y_CABECALHO + marca.height


def marca_dagua(texto: str, estilo: dict) -> Sprite:
    """Texto diagonal translúcido (usado para marcar MODELO)."""
    f = fonte(58, True, estilo)
    w = int(larg(texto, f)) + 40
    img = Image.new("RGBA", (w, 100), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((w / 2, 50), texto, font=f, anchor="mm",
                             fill=(255, 255, 255, 95), stroke_width=2,
                             stroke_fill=(0, 0, 0, 95))
    rot = img.rotate(28, expand=True, resample=Image.BICUBIC)
    if rot.width > LARGURA - 80:
        k = (LARGURA - 80) / rot.width
        rot = rot.resize((int(rot.width * k), int(rot.height * k)), Image.BICUBIC)
    return Sprite(rot, (LARGURA - rot.width) // 2, ALTURA // 2 - rot.height // 2)


def escudo(time: dict, tam: int, estilo: dict) -> Image.Image:
    """Escudo do arquivo (se houver) ou círculo com a sigla na cor do time."""
    arq = time.get("escudo")
    tela = Image.new("RGBA", (tam, tam), (0, 0, 0, 0))
    if arq:
        try:
            img = ImageOps.exif_transpose(Image.open(arq)).convert("RGBA")
            img.thumbnail((tam, tam), Image.LANCZOS)
            tela.alpha_composite(img, ((tam - img.width) // 2, (tam - img.height) // 2))
            return tela
        except OSError as e:
            raise ErroReel(f"não consegui abrir o escudo {arq}: {e}") from e
    nome = str(time.get("nome", "?"))
    c = time.get("cor") or cor_de_time(nome)
    d = ImageDraw.Draw(tela)
    d.ellipse((4, 4, tam - 5, tam - 5), fill=rgba(c), outline=cor(estilo, "texto"),
              width=max(3, tam // 40))
    sig = str(time.get("sigla") or sigla_de(nome)).upper()[:4]
    f = fonte(int(tam * 0.34), True, estilo)
    while larg(sig, f) > tam * 0.78 and f.size > 12:
        f = fonte(f.size - 2, True, estilo)
    d.text((tam / 2, tam / 2), sig, font=f, anchor="mm", fill=cor(estilo, "texto"),
           stroke_width=2, stroke_fill=(0, 0, 0, 160))
    return tela


def seta_para_baixo(tam: int, c) -> Image.Image:
    img = Image.new("RGBA", (tam, tam), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    haste = tam // 5
    d.rectangle((tam / 2 - haste / 2, 0, tam / 2 + haste / 2, tam * 0.55), fill=c)
    d.polygon([(tam * 0.1, tam * 0.45), (tam * 0.9, tam * 0.45), (tam / 2, tam - 1)], fill=c)
    return img
