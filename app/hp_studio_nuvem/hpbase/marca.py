"""Marca única da Hypado: paleta, fontes, tamanhos e zonas seguras dos 6 canais.

A verdade está no código do PC (posts_*.py, estaticos.py, arte_perfil.py,
arte_canais.py); esta tabela é a cópia fiel (Seção 4.6 do prompt da rodada 2)
para NENHUM módulo da nuvem duplicar cor ou fonte. Quem desenha importa daqui:

    from hpbase import marca
    cor = marca.CANAIS["futebol"]["cor_post"]       # "#1ED760"
    f = marca.fonte("Anton", 72)                    # ImageFont (fallback no Linux)

Conflitos que existem hoje no PC (ficam EXPOSTOS, não resolvidos aqui;
decisão do Antônio/Diretor marcada no ENTREGA.md):
  1. Carros: CARROS_COR_PERFIL (#FF2D2D, perfil e capa) x CARROS_COR_POST (#E61E2D,
     posts e stories). Arte nova de post/story usa CARROS_COR_POST.
  2. GTA: GTA_ROSA_POST (#FF48A0, config.json e estaticos.py) x GTA_ROSA_PERFIL
     (#FF3CAA, arte_perfil.py) x GTA_ROSA_SITE (#FF3D8B, página de links).
     Arte nova de post/story usa GTA_ROSA_POST.
  3. Futebol: o reel da rodada 1 usava amarelo #FFD23F; vale o verde #1ED760 do
     posts_futebol.py (pedido do Antônio em 28/09).

Resolvedor de fontes `fonte(nome, tamanho)` procura nesta ordem:
  (1) HP_FONTES ou G:\\Meu Drive\\Hypado\\06 Projeto\\marca\\fontes\\ (OFL do PC);
  (2) C:\\Windows\\Fonts\\ (Bauhaus 93, Segoe UI, Bahnschrift);
  (3) a pasta de cache com as OFL baixadas do Google Fonts
      (HP_FONTES_CACHE ou H:\\HypadoLocal\\fontes\\) — o download é um comando
      à parte (`baixar_fontes_ofl`, transporte injetado): fonte() NUNCA usa rede;
  (4) DejaVu (Linux) como último recurso, só para teste.
Pillow não desenha emoji colorido: `sem_emoji()` tira emoji de texto de arte.
"""
from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from .caminhos import raiz_drive, raiz_local

# --------------------------------------------------------------------- cores
# Conflitos expostos como constantes nomeadas (ver docstring)
CARROS_COR_PERFIL = "#FF2D2D"   # posts_canais.py / arte_canais.py (perfil e capa)
CARROS_COR_POST = "#E61E2D"     # posts_carros.py (posts e stories)
GTA_ROSA_POST = "#FF48A0"       # config.json e estaticos.py (carrosséis e stories)
GTA_ROSA_PERFIL = "#FF3CAA"     # arte_perfil.py (só perfil e capa)
GTA_ROSA_SITE = "#FF3D8B"       # página de links (só o site)
FUTEBOL_VERDE = "#1ED760"       # posts_futebol.py (vale este)
FUTEBOL_AMARELO_RODADA1 = "#FFD23F"  # reel_futebol_arte.py da rodada 1: NÃO usar mais

GTA6 = {
    "rosa": GTA_ROSA_POST, "laranja": "#FFB054", "noite": "#101234", "ciano": "#46E1EB",
    "texto": "#FFE9F3", "corpo": "#F5F2FF",
    "ceu": ["#34286E", "#1C1848", "#101234"],   # degradê do céu, de cima para baixo
}

# canal -> {nome, handle, cor_canal (perfil/capa), cor_post (posts e stories),
#           fundo, destaque, extras, fontes}
CANAIS = {
    "gta": {
        "nome": "GTA 6 | HP", "handle": "@hpgta6",
        "cor_canal": GTA_ROSA_PERFIL, "cor_post": GTA_ROSA_POST,
        "fundo": "#101234", "destaque": "#FFB054",
        "extras": {"laranja": "#FFB054", "ciano": "#46E1EB", "texto": "#FFE9F3",
                   "corpo": "#F5F2FF", "ceu": GTA6["ceu"],
                   "titulo_degrade": [GTA_ROSA_POST, "#FFB054"], "contorno_titulo": "#101234"},
        "fontes": {"titulo": "Bauhaus 93", "tema": "Segoe UI Black", "texto": "Segoe UI Bold",
                   "hp": "Segoe UI Black Italic"},
    },
    "futebol": {
        "nome": "Futebol | HP", "handle": "@hp.futebol",
        "cor_canal": FUTEBOL_VERDE, "cor_post": FUTEBOL_VERDE,
        "fundo": "#0A100C", "destaque": FUTEBOL_VERDE,
        "extras": {"verde_escuro": "#12A850", "preto": "#08090B",
                   "estudio": ["#181B21", "#060709"], "prata": "#C0C4CC",
                   "caixa": "#000000", "caixa_opacidade": 150, "contorno_caixa": "#FFFFFF",
                   "regra_clube": "a cor do post segue o clube do post (nunca a de um rival); "
                                  "clube preto e branco = prata; jogo entre dois = neutra; "
                                  "sem clube = verde HP"},
        "fontes": {"titulo": "Anton", "texto": "Barlow Medium", "subtitulo": "Barlow SemiBold",
                   "destaque": "Barlow ExtraBold", "condensada": "Barlow Condensed Bold",
                   "condensada_forte": "Barlow Condensed ExtraBold"},
    },
    "filmes": {
        "nome": "Filmes e Séries | HP", "handle": "@hp.filmes",
        "cor_canal": "#F5B301", "cor_post": "#F5B301",
        "fundo": "#0E0C0A", "destaque": "#F5B301",
        "extras": {"painel_claro": "#EFEFEF", "preto": "#000000", "branco": "#FFFFFF",
                   "foto_fracao": 0.58, "variacao_escuro": {"caixa": "#000000", "texto": "#FFFFFF"}},
        "fontes": {"titulo": "Barlow ExtraBold", "texto": "Barlow Medium", "poster": "Anton"},
    },
    "receitas": {
        "nome": "Receitas | HP", "handle": "@hp.receitas",
        "cor_canal": "#FF7A1A", "cor_post": "#FF7A1A",
        "fundo": "#120C09", "destaque": "#FFE212",
        "extras": {"faixa_amarela": "#FFE212", "creme": "#FFF6D6", "roxo": "#7C3AED",
                   "azul": "#2548FF"},
        "fontes": {"titulo": "DM Serif Display", "titulo_italico": "DM Serif Display Italic",
                   "texto": "Barlow ExtraBold"},
    },
    "carros": {
        "nome": "Carros | HP", "handle": "@hp.carros",
        "cor_canal": CARROS_COR_PERFIL, "cor_post": CARROS_COR_POST,
        "fundo": "#0E0E10", "destaque": "#FFD600",
        "extras": {"amarelo": "#FFD600", "etiqueta": CARROS_COR_POST, "traco": CARROS_COR_POST},
        "fontes": {"titulo": "Anton", "condensada": "Barlow Condensed ExtraBold",
                   "texto": "Barlow", "texto_medio": "Barlow Medium"},
    },
    "destinos": {
        "nome": "Destinos | HP", "handle": "@hp.destinos",
        "cor_canal": "#00C2D1", "cor_post": "#00C2D1",
        "fundo": "#081014", "destaque": "#78E1FF",
        "extras": {"ciano_claro": "#78E1FF", "marinho": "#0A266E", "azul": "#1554C8",
                   "claro": "#ECF3FB", "fundo_curvas": ["#1554C8", "#0A266E"],
                   "pilula_ida_volta": "#00C2D1", "selo_baixou": "#FFD600"},
        "fontes": {"titulo": "Barlow ExtraBold", "texto": "Barlow SemiBold",
                   "condensada": "Barlow Condensed ExtraBold"},
    },
}
ORDEM_CANAIS = ("gta", "futebol", "filmes", "receitas", "carros", "destinos")
HANDLE_CANAL = {c["handle"].lstrip("@"): k for k, c in CANAIS.items()}  # "hp.futebol" -> "futebol"

# Selo "HP" dos 5 canais (arte_canais.selo_hp) e do GTA (arte_perfil.selo_hp)
SELO_HP = {"fundo": "#FFFFFF", "texto": "#0F0F12", "fonte": "Bahnschrift Bold",
           "fonte_handle": "Bahnschrift SemiBold"}
SELO_HP_GTA = {"texto": "#FFFFFF", "fonte": "Segoe UI Black Italic", "opacidade": 195}

# Tratamento de foto (arte_canais.tratar)
TRATAMENTO_FOTO = {"contraste": 1.12, "cor": 1.10, "brilho": 0.96, "vinheta": 0.55}

# ------------------------------------------------------------------ tamanhos
TAMANHOS = {
    "feed": (1080, 1350), "carrossel": (1080, 1350),
    "story": (1080, 1920), "reel": (1080, 1920), "capa_reel": (1080, 1920),
    "destaque": (1080, 1920), "carrossel_tiktok": (1080, 1920),
    "perfil": (1080, 1080),
    "capa_youtube": (2560, 1440), "capa_youtube_segura": (1546, 423),
    "capa_facebook": (1640, 624),
}
LARGURA_STORY, ALTURA_STORY = TAMANHOS["story"]
SAFE_TOPO = 250     # perfil e barra de progresso do story/reel
SAFE_BASE = 350     # campo de resposta
ZONA_ENQUETE = (110, 930, 970, 1480)     # estaticos.py interativo: retângulo livre da figurinha
ZONA_LINK = (140, 1500, 940, 1640)       # tarefa D: zona reservada da figurinha de link


def zona_segura(largura: int = LARGURA_STORY, altura: int = ALTURA_STORY) -> tuple:
    """(x0, y0, x1, y1) onde pode haver texto/elemento importante num 9:16."""
    return (0, SAFE_TOPO, largura, altura - SAFE_BASE)


def dentro_da_zona_segura(caixa: tuple, altura: int = ALTURA_STORY) -> bool:
    x0, y0, x1, y1 = caixa
    return y0 >= SAFE_TOPO and y1 <= altura - SAFE_BASE


# --------------------------------------------------------------------- cores
def rgb(cor) -> tuple:
    """'#FF48A0' | (255,72,160) | (255,72,160,200) -> tupla RGB(A)."""
    if isinstance(cor, (tuple, list)):
        return tuple(int(c) for c in cor)
    s = str(cor).strip().lstrip("#")
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    if len(s) not in (6, 8):
        raise ValueError(f"cor inválida: {cor!r}")
    return tuple(int(s[i:i + 2], 16) for i in range(0, len(s), 2))


def hex_de(cor) -> str:
    r, g, b = rgb(cor)[:3]
    return f"#{r:02X}{g:02X}{b:02X}"


def luminancia(cor) -> float:
    """Luminância relativa (WCAG 2.x)."""
    def canal(v: int) -> float:
        c = v / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb(cor)[:3]
    return 0.2126 * canal(r) + 0.7152 * canal(g) + 0.0722 * canal(b)


def contraste(cor_a, cor_b) -> float:
    """Razão de contraste WCAG (1 a 21). Texto normal precisa de >= 4.5."""
    la, lb = luminancia(cor_a), luminancia(cor_b)
    claro, escuro = max(la, lb), min(la, lb)
    return (claro + 0.05) / (escuro + 0.05)


def misturar(cor_a, cor_b, t: float) -> tuple:
    """Interpola RGB entre a (t=0) e b (t=1)."""
    a, b = rgb(cor_a)[:3], rgb(cor_b)[:3]
    t = max(0.0, min(1.0, float(t)))
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


# --------------------------------------------------------------------- texto
_RX_EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\U0001FB00-\U0001FBFF"     # pictogramas, emoticons, símbolos
    "\u2600-\u27BF\u2B00-\u2BFF\u2300-\u23FF\u2190-\u21FF"  # misc symbols, setas, técnicos
    "\u2934\u2935\u3030\u303D\u3297\u3299\u00A9\u00AE\u2122\u2139"
    "\u231A\u231B\u24C2\u25AA-\u25FE"
    "\uFE0E\uFE0F\u200D\u20E3"                       # variantes, ZWJ, keycap
    "\U0001F1E6-\U0001F1FF\U000E0020-\U000E007F]"      # bandeiras, tags
)


def sem_emoji(texto) -> str:
    """Tira emoji e pictogramas (Pillow não desenha emoji colorido); mantém acento."""
    t = _RX_EMOJI.sub("", str(texto or ""))
    t = "".join(ch for ch in t if unicodedata.category(ch) not in ("So", "Cs", "Co"))
    t = re.sub(r"[ \t]{2,}", " ", t)
    t = re.sub(r" +\n", "\n", t)
    return t.strip()


def tem_emoji(texto) -> bool:
    return sem_emoji(texto) != re.sub(r"[ \t]{2,}", " ", str(texto or "")).strip()


# -------------------------------------------------------------------- fontes
# nome lógico -> (arquivos candidatos, variação do Bahnschrift ou None)
ARQUIVOS_FONTE = {
    "Anton": (["Anton-Regular.ttf"], None),
    "Barlow": (["Barlow-Regular.ttf"], None),
    "Barlow Regular": (["Barlow-Regular.ttf"], None),
    "Barlow Medium": (["Barlow-Medium.ttf"], None),
    "Barlow SemiBold": (["Barlow-SemiBold.ttf"], None),
    "Barlow Bold": (["Barlow-Bold.ttf"], None),
    "Barlow ExtraBold": (["Barlow-ExtraBold.ttf"], None),
    "Barlow Condensed SemiBold": (["BarlowCondensed-SemiBold.ttf"], None),
    "Barlow Condensed Bold": (["BarlowCondensed-Bold.ttf"], None),
    "Barlow Condensed ExtraBold": (["BarlowCondensed-ExtraBold.ttf"], None),
    "DM Serif Display": (["DMSerifDisplay-Regular.ttf"], None),
    "DM Serif Display Italic": (["DMSerifDisplay-Italic.ttf"], None),
    "Bauhaus 93": (["BAUHS93.TTF", "bauhs93.ttf"], None),
    "Segoe UI": (["segoeui.ttf"], None),
    "Segoe UI Bold": (["segoeuib.ttf"], None),
    "Segoe UI Black": (["seguibl.ttf"], None),
    "Segoe UI Black Italic": (["seguibli.ttf"], None),
    "Segoe UI Emoji": (["seguiemj.ttf"], None),
    "Bahnschrift": (["bahnschrift.ttf"], "Regular"),
    "Bahnschrift SemiBold": (["bahnschrift.ttf"], "SemiBold"),
    "Bahnschrift Bold": (["bahnschrift.ttf"], "Bold"),
    "Bahnschrift Bold Condensed": (["bahnschrift.ttf"], "Bold Condensed"),
}
# quando a fonte pedida não existe (ex.: Bauhaus 93 fora do Windows), tenta estas
SUBSTITUTAS = {
    "Bauhaus 93": ["Anton", "Barlow ExtraBold"],
    "Segoe UI Black": ["Barlow ExtraBold", "Barlow Bold"],
    "Segoe UI Black Italic": ["Barlow ExtraBold", "Barlow Bold"],
    "Segoe UI Bold": ["Barlow Bold", "Barlow SemiBold"],
    "Segoe UI": ["Barlow", "Barlow Medium"],
    "Bahnschrift": ["Barlow Condensed SemiBold", "Barlow Medium"],
    "Bahnschrift SemiBold": ["Barlow Condensed SemiBold", "Barlow SemiBold"],
    "Bahnschrift Bold": ["Barlow Condensed Bold", "Barlow Bold"],
    "Bahnschrift Bold Condensed": ["Barlow Condensed ExtraBold", "Barlow Condensed Bold"],
    "Segoe UI Emoji": [],
}
# OFL no repositório google/fonts (o download é um comando à parte, nunca dentro de fonte())
FONTES_OFL = {
    "Anton-Regular.ttf": "ofl/anton/Anton-Regular.ttf",
    "Barlow-Regular.ttf": "ofl/barlow/Barlow-Regular.ttf",
    "Barlow-Medium.ttf": "ofl/barlow/Barlow-Medium.ttf",
    "Barlow-SemiBold.ttf": "ofl/barlow/Barlow-SemiBold.ttf",
    "Barlow-Bold.ttf": "ofl/barlow/Barlow-Bold.ttf",
    "Barlow-ExtraBold.ttf": "ofl/barlow/Barlow-ExtraBold.ttf",
    "BarlowCondensed-SemiBold.ttf": "ofl/barlowcondensed/BarlowCondensed-SemiBold.ttf",
    "BarlowCondensed-Bold.ttf": "ofl/barlowcondensed/BarlowCondensed-Bold.ttf",
    "BarlowCondensed-ExtraBold.ttf": "ofl/barlowcondensed/BarlowCondensed-ExtraBold.ttf",
    "DMSerifDisplay-Regular.ttf": "ofl/dmserifdisplay/DMSerifDisplay-Regular.ttf",
    "DMSerifDisplay-Italic.ttf": "ofl/dmserifdisplay/DMSerifDisplay-Italic.ttf",
}
URL_GOOGLE_FONTS_RAW = "https://raw.githubusercontent.com/google/fonts/main/"

DEJAVU_PASTAS = [Path("/usr/share/fonts/truetype/dejavu"), Path("/usr/share/fonts/dejavu"),
                 Path("/usr/share/fonts/TTF"), Path("/Library/Fonts"), Path("/System/Library/Fonts")]
DEJAVU_NEGRITO = ["DejaVuSans-Bold.ttf", "DejaVuSansCondensed-Bold.ttf"]
DEJAVU_NORMAL = ["DejaVuSans.ttf", "DejaVuSansCondensed.ttf"]
_PESADAS = ("Bold", "Black", "ExtraBold", "Anton", "Bauhaus", "DM Serif")


def pasta_fontes_pc() -> Path:
    env = os.environ.get("HP_FONTES")
    return Path(env) if env else raiz_drive() / "06 Projeto" / "marca" / "fontes"


def pasta_fontes_windows() -> Path:
    return Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"


def pasta_fontes_cache() -> Path:
    env = os.environ.get("HP_FONTES_CACHE")
    return Path(env) if env else raiz_local() / "fontes"


def pastas_de_fontes() -> list[Path]:
    """A ordem de procura (1) PC/OFL (2) Windows (3) cache (4) DejaVu."""
    return [pasta_fontes_pc(), pasta_fontes_windows(), pasta_fontes_cache(), *DEJAVU_PASTAS]


@dataclass(frozen=True)
class FonteResolvida:
    nome: str           # o que foi pedido
    caminho: str        # arquivo .ttf usado
    variacao: str | None
    exata: bool         # True = a própria fonte; False = substituta ou DejaVu
    origem: str         # "pc" | "windows" | "cache" | "dejavu" | "pillow"
    usada: str          # nome lógico da fonte realmente usada


def _procurar(arquivos: list[str]) -> tuple[Path, str] | None:
    pastas = pastas_de_fontes()
    for i, pasta in enumerate(pastas):
        for nome in arquivos:
            p = pasta / nome
            if p.is_file():
                origem = ("pc", "windows", "cache")[i] if i < 3 else "dejavu"
                return p, origem
        # Windows e caches às vezes guardam em minúsculas/maiúsculas diferentes
        if pasta.is_dir():
            baixos = {n.lower() for n in arquivos}
            try:
                for p in pasta.iterdir():
                    if p.name.lower() in baixos and p.is_file():
                        origem = ("pc", "windows", "cache")[i] if i < 3 else "dejavu"
                        return p, origem
            except OSError:
                continue
    return None


def resolver_fonte(nome: str) -> FonteResolvida:
    """Acha o arquivo da fonte pelo nome lógico; nunca quebra (cai no DejaVu)."""
    pedida = str(nome or "").strip()
    cadeia = [pedida, *SUBSTITUTAS.get(pedida, [])]
    for i, candidata in enumerate(cadeia):
        arqs, variacao = ARQUIVOS_FONTE.get(candidata, ([candidata] if candidata.lower().endswith(".ttf") else [], None))
        if not arqs:
            continue
        achado = _procurar(arqs)
        if achado:
            p, origem = achado
            return FonteResolvida(pedida, str(p), variacao, exata=(i == 0), origem=origem,
                                  usada=candidata)
    pesada = any(x.lower() in pedida.lower() for x in _PESADAS)
    achado = _procurar(DEJAVU_NEGRITO if pesada else DEJAVU_NORMAL)
    if achado:
        return FonteResolvida(pedida, str(achado[0]), None, False, "dejavu",
                              "DejaVu Sans Bold" if pesada else "DejaVu Sans")
    return FonteResolvida(pedida, "", None, False, "pillow", "padrão do Pillow")


_cache_fontes: dict = {}


def fonte(nome: str, tamanho: int, variacao: str | None = None):
    """ImageFont pronto para o Pillow. Nunca levanta exceção por fonte ausente."""
    from PIL import ImageFont
    tamanho = max(1, int(tamanho))
    r = resolver_fonte(nome)
    chave = (r.caminho, tamanho, variacao or r.variacao)
    if chave in _cache_fontes:
        return _cache_fontes[chave]
    if not r.caminho:
        try:
            f = ImageFont.load_default(size=tamanho)
        except TypeError:  # Pillow antigo
            f = ImageFont.load_default()
    else:
        f = ImageFont.truetype(r.caminho, tamanho)
        var = variacao or r.variacao
        if var:
            try:
                f.set_variation_by_name(var)
            except (OSError, ValueError, AttributeError):
                pass  # fonte não variável (substituta): segue sem variação
    _cache_fontes[chave] = f
    return f


def limpar_cache_fontes() -> None:
    _cache_fontes.clear()


def fontes_faltando(nomes=None) -> list[str]:
    """Quais fontes lógicas não existem de verdade (saem com substituta/DejaVu)."""
    nomes = list(nomes) if nomes else list(ARQUIVOS_FONTE)
    return [n for n in nomes if not resolver_fonte(n).exata]


def baixar_fontes_ofl(destino: Path | None = None, transporte=None, so_faltando: bool = True) -> list[str]:
    """Baixa as OFL do Google Fonts (repositório google/fonts) para a pasta de cache.

    `transporte(url) -> bytes` é injetado; sem ele NADA é baixado (devolve a lista
    do que faltaria). No PC as fontes já estão em 06 Projeto\\marca\\fontes, então
    este comando só serve para a nuvem/testes de render. Gravação atômica.
    """
    destino = Path(destino) if destino else pasta_fontes_cache()
    faltam = [a for a in FONTES_OFL if not so_faltando or _procurar([a]) is None]
    if transporte is None:
        return faltam
    destino.mkdir(parents=True, exist_ok=True)
    baixadas = []
    for arq in faltam:
        dados = transporte(URL_GOOGLE_FONTS_RAW + FONTES_OFL[arq])
        if not dados or len(dados) < 1000:
            continue
        tmp = destino / f"{arq}.tmp"
        tmp.write_bytes(dados)
        os.replace(tmp, destino / arq)
        baixadas.append(arq)
    limpar_cache_fontes()
    return baixadas


# ------------------------------------------------------------------- consultas
def canal_por_handle(handle: str) -> str | None:
    h = str(handle or "").strip().lstrip("@").lower()
    return HANDLE_CANAL.get(h)


def cor_do_canal(canal: str, onde: str = "post") -> str:
    """onde = "post" (arte de post/story) ou "perfil" (perfil e capa)."""
    c = CANAIS[canal]
    return c["cor_post"] if onde == "post" else c["cor_canal"]


def resumo() -> list[str]:
    """Uma linha por canal (para o CLI `python -m hpbase.marca`)."""
    linhas = []
    for k in ORDEM_CANAIS:
        c = CANAIS[k]
        linhas.append(f"{k:<9} {c['handle']:<13} perfil {c['cor_canal']}  post {c['cor_post']}  "
                      f"fundo {c['fundo']}  destaque {c['destaque']}  "
                      f"contraste branco/fundo {contraste('#FFFFFF', c['fundo']):.1f}")
    return linhas


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog="python -m hpbase.marca",
                                 description="Paleta e fontes da HP (tabela única).")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("cores", help="mostra a paleta de cada canal")
    sub.add_parser("fontes", help="mostra onde cada fonte foi achada (ou a substituta)")
    b = sub.add_parser("baixar-fontes", help="baixa as OFL do Google Fonts para a pasta de cache")
    b.add_argument("--destino", help="pasta de cache (padrão HP_FONTES_CACHE ou H:\\HypadoLocal\\fontes)")
    args = ap.parse_args(argv)
    if args.cmd == "fontes":
        for n in ARQUIVOS_FONTE:
            r = resolver_fonte(n)
            print(f"{n:<28} {'ok' if r.exata else 'substituta: ' + r.usada:<40} {r.origem:<8} {r.caminho}")
        return 0
    if args.cmd == "baixar-fontes":
        import urllib.request

        def transporte(url: str) -> bytes:
            with urllib.request.urlopen(url, timeout=60) as r:  # só aqui, por comando explícito
                return r.read()
        feitas = baixar_fontes_ofl(args.destino, transporte)
        print(f"{len(feitas)} fonte(s) baixada(s) para {args.destino or pasta_fontes_cache()}")
        return 0
    print("\n".join(resumo()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
