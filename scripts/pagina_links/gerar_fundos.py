"""Fundos clarinhos e botões por canal para a página de links (Google Sites).

Página: https://sites.google.com/view/hpcanais — o Google Sites não se edita
por código; este script só GERA as imagens. Quem aplica é o Antônio, com o
PASSO_A_PASSO.md (ninguém faz login por ele).

Gera em H:\\HypadoLocal\\pagina_links\\:
  fundos\\<canal>_1600x400.jpg   faixa (fundo de seção)
  fundos\\<canal>_1080x1080.jpg  quadrado (fundo de item / bloco com imagem)
  botoes\\<canal>_botao.png      botão 1000x200 na cor do canal, com o nome
  cartoes\\<canal>_cartao.jpg    faixa clarinha com o botão já em cima (1 imagem com link)
  previa.html                    como fica no celular, para conferir antes

Fundo: com foto do canal (fotos\\<canal>.jpg|png|webp) a foto é clareada
(mistura com branco 75-85% + leve desfoque); sem foto, degradê suave na cor
do canal com um padrão discreto. Sempre clarinho: luminância média > 200.

Cores em cores_canais.json. O contraste do texto do botão (WCAG AA >= 4,5:1)
é CALCULADO e VERIFICADO aqui: cor que não passa é recusada.

Uso (PowerShell):
  python scripts\\pagina_links\\gerar_fundos.py                  (gera tudo)
  python scripts\\pagina_links\\gerar_fundos.py gerar --canal receitas --foto receitas=C:\\fotos\\bolo.jpg
  python scripts\\pagina_links\\gerar_fundos.py contraste         (confere as cores)
  python scripts\\pagina_links\\gerar_fundos.py botao receitas "Receitas no TikTok"
  python scripts\\pagina_links\\gerar_fundos.py gerar --simular   (só mostra o que faria)
"""
from __future__ import annotations

import argparse
import contextlib
import html as _html
import json
import math
import os
import sys
from pathlib import Path
from typing import Iterable


def _preparar_hpbase() -> None:
    aqui = Path(__file__).resolve().parent
    candidatos: list[Path] = []
    env = os.environ.get("HP_APP")
    if env:
        candidatos += [Path(env), Path(env) / "hp_studio"]
    scripts = aqui.parent
    candidatos += [scripts.parent / "app" / "hp_studio",
                   scripts.parent / "06 Projeto" / "app" / "hp_studio"]
    for c in candidatos:
        if (c / "hpbase" / "__init__.py").exists():
            if str(c) not in sys.path:
                sys.path.insert(0, str(c))
            return


_preparar_hpbase()
from hpbase import garantir, obter_logger, raiz_local  # noqa: E402

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageStat  # noqa: E402

AQUI = Path(__file__).resolve().parent
ARQ_CORES = AQUI / "cores_canais.json"
TAMANHOS_FUNDO = ((1600, 400), (1080, 1080))
TAMANHO_BOTAO = (1000, 200)
CONTRASTE_MINIMO = 4.5          # WCAG AA, texto normal
CONTRASTE_BORDA = 3.0           # WCAG 1.4.11: contorno do botão x fundo claro
LUMINANCIA_ALVO = 218           # média desejada do fundo (0-255); teste exige > 200
BRANCO_MIN, BRANCO_MAX = 0.75, 0.85
EXT_FOTO = (".jpg", ".jpeg", ".png", ".webp")


class ErroContraste(ValueError):
    """Cor de texto do botão sem contraste AA (>= 4,5:1)."""


# --------------------------------------------------------------------------
# cor e contraste (fórmula oficial da WCAG 2.x)
# --------------------------------------------------------------------------
def hex_para_rgb(cor: str) -> tuple[int, int, int]:
    s = cor.strip().lstrip("#")
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    if len(s) != 6:
        raise ValueError(f"cor inválida: {cor!r} (use #RRGGBB)")
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


def rgb_para_hex(rgb: Iterable[float]) -> str:
    return "#" + "".join(f"{max(0, min(255, round(c))):02X}" for c in rgb)


def luminancia_relativa(cor: str) -> float:
    def canal(c: int) -> float:
        v = c / 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = hex_para_rgb(cor)
    return 0.2126 * canal(r) + 0.7152 * canal(g) + 0.0722 * canal(b)


def contraste(cor1: str, cor2: str) -> float:
    l1, l2 = sorted((luminancia_relativa(cor1), luminancia_relativa(cor2)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


def misturar(cor: str, outra: str, t: float) -> str:
    """t=0 -> cor; t=1 -> outra."""
    a, b = hex_para_rgb(cor), hex_para_rgb(outra)
    return rgb_para_hex(x + (y - x) * t for x, y in zip(a, b))


def escolher_cor_texto(fundo: str, candidatas: Iterable[str] = ("#FFFFFF", "#141413")) -> str:
    """A candidata de maior contraste com o fundo."""
    return max(candidatas, key=lambda c: contraste(fundo, c))


def cor_borda(cor: str, fundo: str = "#FFFFFF") -> str:
    """Escurece a cor até o contorno se destacar do fundo claro (>= 3:1)."""
    for i in range(0, 101):
        c = misturar(cor, "#000000", i / 100)
        if contraste(c, fundo) >= CONTRASTE_BORDA:
            return c
    return "#000000"


def carregar_cores(caminho: str | Path | None = None) -> list[dict]:
    """Lê cores_canais.json e VERIFICA o contraste de cada canal.

    Levanta ErroContraste se o texto do botão não tiver >= 4,5:1, ou se o
    valor de "contraste" anotado no arquivo não bater com o cálculo.
    """
    dados = json.loads(Path(caminho or ARQ_CORES).read_text(encoding="utf-8-sig"))
    canais = dados["canais"]
    slugs = set()
    for c in canais:
        for campo in ("slug", "nome", "cor", "cor_texto_botao"):
            if not c.get(campo):
                raise ValueError(f"canal sem '{campo}': {c}")
        if c["slug"] in slugs:
            raise ValueError(f"canal repetido: {c['slug']}")
        slugs.add(c["slug"])
        hex_para_rgb(c["cor"])
        hex_para_rgb(c["cor_texto_botao"])
        calc = round(contraste(c["cor"], c["cor_texto_botao"]), 2)
        if calc < CONTRASTE_MINIMO:
            melhor = escolher_cor_texto(c["cor"])
            raise ErroContraste(
                f"{c['nome']}: texto {c['cor_texto_botao']} sobre {c['cor']} tem {calc}:1 "
                f"(mínimo {CONTRASTE_MINIMO}:1). Sugestão: {melhor} "
                f"({contraste(c['cor'], melhor):.2f}:1)")
        if "contraste" in c and abs(float(c["contraste"]) - calc) > 0.01:
            raise ErroContraste(f"{c['nome']}: 'contraste' anotado {c['contraste']} não bate com o "
                                f"calculado {calc}: troque o número para {calc} (ou apague o campo)")
        c["contraste_calculado"] = calc
        c["cor_borda"] = cor_borda(c["cor"])
    return canais


# --------------------------------------------------------------------------
# fontes (Windows: Segoe UI / Arial; Linux dos testes: DejaVu)
# --------------------------------------------------------------------------
_FONTES = [
    os.environ.get("HP_FONTE", ""),
    r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\seguisb.ttf",
    r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\calibrib.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "/Library/Fonts/Arial Bold.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]


def achar_fonte(tamanho: int) -> ImageFont.ImageFont:
    for f in _FONTES:
        if f and Path(f).exists():
            with contextlib.suppress(OSError):
                return ImageFont.truetype(f, tamanho)
    return ImageFont.load_default(size=tamanho)  # Pillow >= 10.1


# --------------------------------------------------------------------------
# fundos
# --------------------------------------------------------------------------
def luminancia_media(img: Image.Image) -> float:
    return ImageStat.Stat(img.convert("L")).mean[0]


def _clarear_foto(foto: Image.Image, tamanho: tuple[int, int], cor: str) -> Image.Image:
    w, h = tamanho
    img = ImageOps.exif_transpose(foto).convert("RGB")
    img = ImageOps.fit(img, tamanho, Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    img = img.filter(ImageFilter.GaussianBlur(radius=max(2.0, max(w, h) / 450)))
    # um toque da cor do canal (8%) para a foto "conversar" com o botão
    img = Image.blend(img, Image.new("RGB", tamanho, hex_para_rgb(cor)), 0.08)
    lf = luminancia_media(img)
    t = (LUMINANCIA_ALVO - lf) / max(1.0, 255 - lf)
    t = min(BRANCO_MAX, max(BRANCO_MIN, t))
    return Image.blend(img, Image.new("RGB", tamanho, (255, 255, 255)), t)


def _degrade(tamanho: tuple[int, int], c1: str, c2: str) -> Image.Image:
    """Degradê diagonal suave de c1 (canto de cima à esquerda) para c2."""
    a, b = hex_para_rgb(c1), hex_para_rgb(c2)
    n = 32
    m = Image.new("L", (n, n))
    m.putdata([round((x + y) / (2 * (n - 1)) * 255) for y in range(n) for x in range(n)])
    m = m.resize(tamanho, Image.Resampling.BILINEAR)
    return Image.composite(Image.new("RGB", tamanho, b), Image.new("RGB", tamanho, a), m)


def _padrao(slug: str, tamanho: tuple[int, int]) -> Image.Image:
    """Máscara (L) do padrão discreto do canal, desenhada em 2x para ficar lisa."""
    w, h = tamanho[0] * 2, tamanho[1] * 2
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    u = min(w, h) / 20          # unidade do desenho
    lw = max(2, int(u / 6))
    if slug == "gta":            # listras diagonais (pôr do sol de Vice City)
        passo = int(u * 1.6)
        for x in range(-h, w + h, passo):
            d.line([(x, 0), (x + h, h)], fill=255, width=lw)
    elif slug == "futebol":      # linhas do campo
        d.line([(w / 2, 0), (w / 2, h)], fill=255, width=lw)
        r = h * 0.28
        d.ellipse([w / 2 - r, h / 2 - r, w / 2 + r, h / 2 + r], outline=255, width=lw)
        ah, aw = h * 0.6, min(w * 0.12, h * 0.35)
        d.rectangle([-lw, (h - ah) / 2, aw, (h + ah) / 2], outline=255, width=lw)
        d.rectangle([w - aw, (h - ah) / 2, w + lw, (h + ah) / 2], outline=255, width=lw)
        d.rectangle([lw, lw, w - lw, h - lw], outline=255, width=lw)
    elif slug == "filmes":       # furinhos de filme em cima e embaixo
        fw, fh, passo = u * 0.9, u * 0.6, u * 1.6
        for y in (u * 0.5, h - u * 0.5 - fh):
            x = u * 0.4
            while x < w:
                d.rounded_rectangle([x, y, x + fw, y + fh], radius=fh / 4, fill=255)
                x += passo
    elif slug == "carros":       # quadriculado de chegada que some para a direita
        lado = u * 1.1
        colunas = int(w / lado) + 1
        for i in range(colunas):
            for j in range(int(h / lado) + 1):
                if (i + j) % 2 == 0 and i < colunas * 0.35:
                    d.rectangle([i * lado, j * lado, (i + 1) * lado, (j + 1) * lado],
                                fill=int(255 * max(0.0, 1 - i / (colunas * 0.35))))
    elif slug == "destinos":     # ondas
        passo = u * 1.5
        y = passo / 2
        while y < h + passo:
            pts = [(x, y + math.sin(x / (u * 2.2)) * u * 0.45) for x in range(0, w + 8, 8)]
            d.line(pts, fill=255, width=lw)
            y += passo
    else:                        # receitas e demais: bolinhas
        passo = u * 1.4
        r = u * 0.18
        for j, y in enumerate(range(0, h + int(passo), int(passo))):
            for x in range(0, w + int(passo), int(passo)):
                cx = x + (passo / 2 if j % 2 else 0)
                d.ellipse([cx - r, y - r, cx + r, y + r], fill=255)
    return m.resize(tamanho, Image.Resampling.LANCZOS)


def _sem_foto(canal: dict, tamanho: tuple[int, int]) -> Image.Image:
    cor = canal["cor"]
    img = _degrade(tamanho, misturar(cor, "#FFFFFF", 0.90), misturar(cor, "#FFFFFF", 0.80))
    # padrão discreto na cor do canal (10% de opacidade)
    mascara = _padrao(canal["slug"], tamanho).point(lambda v: int(v * 0.10))
    img.paste(Image.new("RGB", tamanho, hex_para_rgb(cor)), (0, 0), mascara)
    # duas manchas de luz branca (dá profundidade sem pesar)
    luz = Image.new("L", tamanho, 0)
    dl = ImageDraw.Draw(luz)
    w, h = tamanho
    for cx, cy, r in ((w * 0.82, h * 0.2, min(w, h) * 0.55), (w * 0.12, h * 0.9, min(w, h) * 0.4)):
        dl.ellipse([cx - r, cy - r, cx + r, cy + r], fill=110)
    luz = luz.filter(ImageFilter.GaussianBlur(radius=min(w, h) * 0.18))
    img.paste(Image.new("RGB", tamanho, (255, 255, 255)), (0, 0), luz)
    return img


def gerar_fundo(canal: dict, tamanho: tuple[int, int], foto: str | Path | Image.Image | None = None) -> Image.Image:
    if foto is not None:
        im = foto if isinstance(foto, Image.Image) else Image.open(foto)
        img = _clarear_foto(im, tamanho, canal["cor"])
    else:
        img = _sem_foto(canal, tamanho)
    # garantia final: se ainda ficou escuro, clareia mais (nunca passa de 85% de branco no total)
    if luminancia_media(img) <= 200:
        img = Image.blend(img, Image.new("RGB", tamanho, (255, 255, 255)), 0.5)
    return img


# --------------------------------------------------------------------------
# botões
# --------------------------------------------------------------------------
def gerar_botao(canal: dict, texto: str | None = None, tamanho: tuple[int, int] = TAMANHO_BOTAO) -> Image.Image:
    """Botão arredondado na cor do canal, texto com contraste >= 4,5:1, fundo transparente."""
    cor, cor_txt = canal["cor"], canal["cor_texto_botao"]
    if contraste(cor, cor_txt) < CONTRASTE_MINIMO:
        raise ErroContraste(f"{canal['nome']}: contraste {contraste(cor, cor_txt):.2f}:1 < 4,5:1")
    borda = canal.get("cor_borda") or cor_borda(cor)
    texto = texto or canal["nome"]
    k = 2                                             # desenha em 2x e reduz (borda lisa)
    w, h = tamanho[0] * k, tamanho[1] * k
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    esp = 6 * k
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=hex_para_rgb(borda))
    d.rounded_rectangle([esp, esp, w - 1 - esp, h - 1 - esp], radius=h // 2 - esp, fill=hex_para_rgb(cor))
    tam = int(h * 0.42)
    largura_max = w - h * 1.1                         # sobra das pontas arredondadas
    while True:
        fonte = achar_fonte(tam)
        x0, y0, x1, y1 = d.textbbox((0, 0), texto, font=fonte)
        if x1 - x0 <= largura_max or tam <= 20:
            break
        tam -= 4
    d.text(((w - (x1 - x0)) / 2 - x0, (h - (y1 - y0)) / 2 - y0), texto, font=fonte,
           fill=hex_para_rgb(cor_txt))
    return img.resize(tamanho, Image.Resampling.LANCZOS)


def gerar_cartao(faixa: Image.Image, botao: Image.Image) -> Image.Image:
    """Faixa clarinha com o botão no meio: vira 1 imagem só, com link, no Google Sites."""
    cartao = faixa.convert("RGBA")
    cartao.alpha_composite(botao.convert("RGBA"), ((cartao.width - botao.width) // 2,
                                                   (cartao.height - botao.height) // 2))
    return cartao.convert("RGB")


# --------------------------------------------------------------------------
# tudo junto
# --------------------------------------------------------------------------
def pasta_saida() -> Path:
    return raiz_local() / "pagina_links"


def achar_foto(slug: str, pasta: Path | None) -> Path | None:
    if not pasta or not Path(pasta).is_dir():
        return None
    for ext in EXT_FOTO:
        for nome in (slug + ext, slug + ext.upper()):
            p = Path(pasta) / nome
            if p.exists():
                return p
    return None


def _previa_html(canais: list[dict], arquivos: dict) -> str:
    """Página local para ver os fundos com os botões numa largura de celular."""
    blocos = []
    for c in canais:
        a = arquivos.get(c["slug"], {})
        if not a:
            continue
        blocos.append(
            f'<section style="background-image:url(\'fundos/{Path(a["faixa"]).name}\')">'
            f'<a href="#" aria-label="{_html.escape(c["nome"])}"><img src="botoes/{Path(a["botao"]).name}" '
            f'alt="{_html.escape(c["nome"])}"></a></section>')
    return ("<!doctype html><html lang=\"pt-BR\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>Prévia da página de links</title>"
            "<style>body{margin:0;background:#fff;font:15px system-ui,sans-serif;color:#141413}"
            ".cel{max-width:390px;margin:16px auto;border:1px solid #ddd;border-radius:24px;overflow:hidden}"
            "h1{font-size:18px;margin:16px;text-align:center}"
            "section{background-size:cover;background-position:center;padding:28px 16px;display:grid;place-items:center}"
            "section img{width:100%;max-width:340px;height:auto;display:block}"
            "p{margin:12px 16px;color:#5d5a66;font-size:13px}</style></head><body><div class=\"cel\">"
            "<h1>HP Canais</h1>" + "".join(blocos) +
            "<p>Prévia local (largura de celular). Confira também no Google Sites &gt; Visualizar &gt; Telefone.</p>"
            "</div></body></html>")


def gerar_tudo(saida: str | Path | None = None, pasta_fotos: str | Path | None = None,
               fotos: dict[str, str | Path] | None = None, somente: Iterable[str] | None = None,
               simular: bool = False, arq_cores: str | Path | None = None) -> dict:
    """Gera fundos (2 tamanhos) e botão de cada canal. Devolve o que gerou."""
    log = obter_logger("pagina_links")
    canais = carregar_cores(arq_cores)
    base = Path(saida) if saida else pasta_saida()
    pasta_fotos = Path(pasta_fotos) if pasta_fotos else base / "fotos"
    fotos = {k: Path(v) for k, v in (fotos or {}).items()}
    somente = set(somente or [])
    desconhecidos = somente - {c["slug"] for c in canais}
    if desconhecidos:
        raise ValueError(f"canal desconhecido: {', '.join(sorted(desconhecidos))}")
    res: dict = {"pasta": str(base), "simulado": simular, "canais": {}}
    for c in canais:
        if somente and c["slug"] not in somente:
            continue
        foto = fotos.get(c["slug"]) or achar_foto(c["slug"], pasta_fotos)
        if foto is not None and not Path(foto).exists():
            raise FileNotFoundError(f"foto não encontrada: {foto}")
        item = {"foto": str(foto) if foto else None,
                "faixa": str(base / "fundos" / f"{c['slug']}_1600x400.jpg"),
                "quadrado": str(base / "fundos" / f"{c['slug']}_1080x1080.jpg"),
                "botao": str(base / "botoes" / f"{c['slug']}_botao.png"),
                "cartao": str(base / "cartoes" / f"{c['slug']}_cartao.jpg"),
                "contraste": c["contraste_calculado"]}
        if not simular:
            for sub in ("fundos", "botoes", "cartoes"):
                garantir(base / sub)
            imgs = {}
            for (w, h), chave in zip(TAMANHOS_FUNDO, ("faixa", "quadrado")):
                imgs[chave] = img = gerar_fundo(c, (w, h), foto)
                img.save(item[chave], "JPEG", quality=90, optimize=True, progressive=True)
                item[f"luminancia_{chave}"] = round(luminancia_media(img), 1)
            botao = gerar_botao(c)
            botao.save(item["botao"], "PNG", optimize=True)
            gerar_cartao(imgs["faixa"], botao).save(item["cartao"], "JPEG", quality=92, optimize=True)
        res["canais"][c["slug"]] = item
        log.info("%s %s: foto=%s contraste=%.2f", "simular" if simular else "gerado",
                 c["slug"], "sim" if foto else "não", c["contraste_calculado"])
    if not simular:
        previa = base / "previa.html"
        previa.write_text(_previa_html(canais, res["canais"]), encoding="utf-8")
        res["previa"] = str(previa)
    return res


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
class _Formato(argparse.RawDescriptionHelpFormatter):
    def add_usage(self, usage, actions, groups, prefix=None):
        return super().add_usage(usage, actions, groups, prefix or "uso: ")


def _sub(sub, nome: str, ajuda: str) -> argparse.ArgumentParser:
    sp = sub.add_parser(nome, help=ajuda, description=ajuda, add_help=False, formatter_class=_Formato)
    sp._positionals.title = "argumentos"
    sp._optionals.title = "opções"
    sp.add_argument("-h", "--help", action="help", help="mostra esta ajuda e sai")
    return sp


def main(argv: list[str] | None = None) -> int:
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0].startswith("--") and argv[0] not in ("--help", "-h"):
        argv = ["gerar"] + argv                       # sem comando = gerar tudo
    p = argparse.ArgumentParser(prog="gerar_fundos.py", add_help=False, formatter_class=_Formato,
                                description="Fundos clarinhos e botões por canal para a página de links.")
    p._positionals.title = "argumentos"
    p._optionals.title = "opções"
    p.add_argument("-h", "--help", action="help", help="mostra esta ajuda e sai")
    sub = p.add_subparsers(dest="cmd", metavar="comando", title="comandos")
    s = _sub(sub, "gerar", "gera fundos (1600x400 e 1080x1080) e botões (1000x200)")
    s.add_argument("--canal", action="append", help="só este canal (pode repetir): gta, futebol, ...")
    s.add_argument("--fotos", help="pasta com <canal>.jpg (padrão: H:\\HypadoLocal\\pagina_links\\fotos)")
    s.add_argument("--foto", action="append", default=[], metavar="CANAL=ARQUIVO",
                   help="foto de um canal, ex.: receitas=C:\\fotos\\bolo.jpg")
    s.add_argument("--saida", help="pasta de saída (padrão: H:\\HypadoLocal\\pagina_links)")
    s.add_argument("--simular", action="store_true", help="só mostra o que faria, sem gravar")
    s = _sub(sub, "contraste", "confere o contraste das cores de cores_canais.json")
    s.add_argument("--cores", help="outro arquivo de cores")
    s = _sub(sub, "botao", "gera um botão com texto próprio")
    s.add_argument("canal")
    s.add_argument("texto")
    s.add_argument("--saida", help="arquivo PNG (padrão: botoes\\<canal>_<texto>.png)")
    a = p.parse_args(argv)
    try:
        if a.cmd == "gerar":
            fotos = {}
            for par in a.foto:
                if "=" not in par:
                    raise ValueError(f"use CANAL=ARQUIVO em --foto (recebi {par!r})")
                k, v = par.split("=", 1)
                fotos[k.strip()] = v.strip()
            res = gerar_tudo(a.saida, a.fotos, fotos, a.canal, simular=a.simular)
            print(json.dumps(res, ensure_ascii=False, indent=2))
        elif a.cmd == "contraste":
            ok = True
            try:
                canais = carregar_cores(a.cores)
            except ErroContraste as e:
                print(f"FALHOU: {e}")
                return 1
            for c in canais:
                print(f"{c['nome']:<22} botão {c['cor']} texto {c['cor_texto_botao']}  "
                      f"{c['contraste_calculado']:.2f}:1  {'OK (AA)' if c['contraste_calculado'] >= 4.5 else 'FALHOU'}"
                      f"  contorno {c['cor_borda']}")
            return 0 if ok else 1
        elif a.cmd == "botao":
            canais = {c["slug"]: c for c in carregar_cores()}
            if a.canal not in canais:
                raise ValueError(f"canal desconhecido: {a.canal}")
            destino = Path(a.saida) if a.saida else pasta_saida() / "botoes" / (
                f"{a.canal}_" + "".join(ch if ch.isalnum() else "_" for ch in a.texto.lower())[:40] + ".png")
            garantir(destino.parent)
            gerar_botao(canais[a.canal], a.texto).save(destino, "PNG", optimize=True)
            print(destino)
    except (ErroContraste, ValueError, FileNotFoundError, OSError) as e:
        print(f"erro: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
