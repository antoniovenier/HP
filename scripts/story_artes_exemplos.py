"""Exemplos dos 18 stories (3 modelos x 6 canais), capas sintéticas e a prancha.

O que faz: dá o spec de exemplo de cada canal/modelo (textos curtos de verdade,
na voz do canal), gera capas sintéticas determinísticas (formas e degradês, sem
foto real e sem texto) para os exemplos não dependerem de arquivo nenhum, e monta
a _prancha_story.jpg (grade 6 colunas x 3 linhas, miniaturas rotuladas).

Uso: from story_artes_exemplos import specs_exemplo, capa_sintetica, prancha
Regras: tudo determinístico (semente fixa); nada de rede; a prancha é só para o
Antônio conferir de olho (os testes não olham imagem).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from story_artes_base import degrade_diagonal, fonte, gravar_imagem, marca, rgba

TIPOS = ("chamada", "maissobre", "interacao")

_EXEMPLOS: dict = {
    "gta": {
        "chamada": {"rotulo": "NOVO VÍDEO", "chamada": "Trailer 3 do *GTA 6* ganha data",
                    "credito_foto": "Rockstar Games", "figurinhas": ["link", "enquete"], "foco": [0.5, 0.35]},
        "maissobre": {"rotulo": "MAIS SOBRE", "fatos": ["Lançamento confirmado para 19 de novembro",
                                                         "Leonida tem 2 cidades e *70 km* de costa",
                                                         "Primeira protagonista mulher da série"],
                      "dado_forte": {"valor": "19/11", "legenda": "data de lançamento (Rockstar)"},
                      "credito_foto": "Rockstar Games"},
        "interacao": {"rotulo": "SUA VEZ", "pergunta": "Qual trailer te deixou mais *ansioso*?",
                      "fotos_prefere": True},
    },
    "futebol": {
        "chamada": {"rotulo": "NOVO REEL", "chamada": "Flamengo fecha *reforço* de R$ 80 mi",
                    "credito_foto": "Flamengo oficial", "cor_destaque": "#C8102E", "foco": [0.5, 0.3]},
        "maissobre": {"rotulo": "MAIS SOBRE", "fatos": ["Contrato até *2029*, com opção de mais um ano",
                                                         "Chega para a vaga do meio-campo",
                                                         "Estreia prevista no clássico de domingo",
                                                         "Valores aproximados, segundo a imprensa"],
                      "dado_forte": {"valor": "R$ 80 mi", "legenda": "valor aproximado da compra"},
                      "credito_foto": "Flamengo oficial"},
        "interacao": {"rotulo": "ENQUETE", "pergunta": "Vale os *R$ 80 milhões*?"},
    },
    "filmes": {
        "chamada": {"rotulo": "NOVA SÉRIE", "chamada": "*Duna 3* ganha teaser e data",
                    "credito_foto": "Warner Bros.", "foco": [0.5, 0.4]},
        "maissobre": {"rotulo": "MAIS SOBRE", "fatos": ["Estreia em *dezembro de 2026* nos cinemas",
                                                         "Fecha a trilogia de Denis Villeneuve",
                                                         "Baseado em Messias de Duna"],
                      "dado_forte": {"valor": "18/12", "legenda": "estreia nos cinemas"},
                      "credito_foto": "Warner Bros."},
        "interacao": {"rotulo": "SUA VEZ", "pergunta": "Cinema ou *streaming* pra esse?",
                      "fotos_prefere": True},
    },
    "receitas": {
        "chamada": {"rotulo": "NOVA RECEITA", "chamada": "Bolo de *cenoura* em 40 minutos",
                    "credito_foto": "Receitas | HP", "foco": [0.5, 0.5]},
        "maissobre": {"rotulo": "DICAS", "fatos": ["Rende *12 pedaços* numa forma média",
                                                    "Cobertura: chocolate e leite condensado",
                                                    "Fica 3 dias fora da geladeira"],
                      "dado_forte": {"valor": "40 min", "legenda": "do começo ao bolo pronto"},
                      "credito_foto": "Receitas | HP"},
        "interacao": {"rotulo": "SUA VEZ", "pergunta": "Cobertura de *chocolate* ou brigadeiro?"},
    },
    "carros": {
        "chamada": {"rotulo": "NOVIDADE", "chamada": "Novo *Civic* chega por R$ 240 mil",
                    "credito_foto": "Honda", "foco": [0.5, 0.55]},
        "maissobre": {"rotulo": "FICHA", "fatos": ["Motor 2.0 híbrido de *184 cv*",
                                                    "Consumo de 17 km/l na cidade",
                                                    "Valores aproximados, podem mudar"],
                      "dado_forte": {"valor": "184 cv", "legenda": "potência combinada"},
                      "credito_foto": "Honda"},
        "interacao": {"rotulo": "ENQUETE", "pergunta": "Vale mais que o *Corolla*?", "fotos_prefere": True},
    },
    "destinos": {
        "chamada": {"rotulo": "PASSAGEM", "chamada": "Lisboa por *R$ 2.990* ida e volta",
                    "credito_foto": "Turismo de Lisboa", "foco": [0.5, 0.45]},
        "maissobre": {"rotulo": "COMO ACHAR", "fatos": ["Saindo de *São Paulo* em março",
                                                         "Bagagem de mão incluída",
                                                         "Preço visto hoje; pode mudar"],
                      "dado_forte": {"valor": "R$ 2.990", "legenda": "ida e volta, taxas inclusas"},
                      "credito_foto": "Turismo de Lisboa"},
        "interacao": {"rotulo": "SUA VEZ", "pergunta": "Praia ou *cidade histórica* nas férias?"},
    },
}


def specs_exemplo(canal: str | None = None) -> list[dict]:
    """Os specs de exemplo (sem 'saida'/'capa'; quem gera preenche)."""
    canais = [canal] if canal else list(marca.ORDEM_CANAIS)
    out = []
    for c in canais:
        if c not in _EXEMPLOS:
            raise KeyError(c)
        for tipo in TIPOS:
            s = {"canal": c, "tipo": tipo, "nome": f"{c}_{tipo}"}
            s.update(_EXEMPLOS[c][tipo])
            out.append(s)
    return out


def capa_sintetica(canal: str, variante: int = 0, tam=(1080, 1350)) -> Image.Image:
    """'Foto' de mentira do post: degradê + formas com semente fixa (sem texto, sem rede)."""
    c = marca.CANAIS[canal]
    rng = np.random.default_rng(hash_fixo(canal) + variante)
    peq = (tam[0] // 6, tam[1] // 6)
    cores = {
        "gta": ("#5A3C9A", "#1C1848"), "futebol": ("#2F7A3F", "#0D2A18"), "filmes": ("#6A4A2A", "#161210"),
        "receitas": ("#C9772E", "#4A2412"), "carros": ("#7A7F8A", "#1A1B20"), "destinos": ("#3A8FD8", "#13306B"),
    }[canal]
    img = degrade_diagonal(peq, cores[0], cores[1]).convert("RGBA")
    d = ImageDraw.Draw(img)
    for _ in range(6):
        x, y = int(rng.integers(0, peq[0])), int(rng.integers(0, peq[1]))
        r = int(rng.integers(peq[0] // 6, peq[0] // 2))
        cor = marca.misturar(c["cor_post"], "#FFFFFF", float(rng.uniform(0.0, 0.5)))
        d.ellipse([x - r, y - r, x + r, y + r], fill=rgba(cor, int(rng.integers(40, 120))))
    # "assunto" no centro: um retângulo claro arredondado (lembra um objeto/pessoa)
    cx, cy = peq[0] // 2, int(peq[1] * 0.45)
    d.rounded_rectangle([cx - peq[0] // 5, cy - peq[1] // 6, cx + peq[0] // 5, cy + peq[1] // 4], radius=8,
                        fill=rgba(marca.misturar(cores[0], "#FFFFFF", 0.55), 230))
    img = img.filter(ImageFilter.GaussianBlur(1.2))
    return img.resize(tam, Image.BICUBIC).convert("RGB")


def hash_fixo(texto: str) -> int:
    """Semente estável entre execuções (hash() do Python muda a cada processo)."""
    h = 0
    for ch in texto:
        h = (h * 31 + ord(ch)) % 1_000_003
    return h


def preparar_capas(pasta: Path, canal: str | None = None) -> dict:
    """Grava as capas sintéticas em <pasta>/_capas e devolve {canal: {"capa": p, "a": p, "b": p}}."""
    pasta = Path(pasta) / "_capas"
    pasta.mkdir(parents=True, exist_ok=True)
    out = {}
    for c in ([canal] if canal else list(marca.ORDEM_CANAIS)):
        caminhos = {}
        for nome, var in (("capa", 0), ("a", 1), ("b", 2)):
            p = pasta / f"{c}_{nome}.jpg"
            if not p.exists():
                gravar_imagem(capa_sintetica(c, var), p, "jpg")
            caminhos[nome] = p
        out[c] = caminhos
    return out


def specs_para_pasta(pasta: Path, canal: str | None = None) -> list[dict]:
    """Specs de exemplo prontos para renderizar em <pasta> (com capas sintéticas)."""
    capas = preparar_capas(pasta, canal)
    specs = []
    for s in specs_exemplo(canal):
        s = dict(s)
        s["saida"] = str(pasta)
        s["capa"] = str(capas[s["canal"]]["capa"])
        if s.get("fotos_prefere") is True:
            s["fotos_prefere"] = [str(capas[s["canal"]]["a"]), str(capas[s["canal"]]["b"])]
        specs.append(s)
    return specs


def prancha(jpgs: dict, destino: Path, escala: float = 2 / 9) -> Path:
    """Grade 6 colunas (canais) x 3 linhas (modelos) com miniaturas rotuladas -> _prancha_story.jpg."""
    tw, th = int(1080 * escala), int(1920 * escala)
    marg, gut, rot = 30, 24, 44
    cols, rows = list(marca.ORDEM_CANAIS), list(TIPOS)
    W = marg * 2 + len(cols) * tw + (len(cols) - 1) * gut
    H = marg * 2 + len(rows) * (th + rot) + (len(rows) - 1) * gut
    img = Image.new("RGB", (W, H), (28, 28, 32))
    d = ImageDraw.Draw(img)
    f = fonte("Barlow SemiBold", 22)
    for j, tipo in enumerate(rows):
        for i, canal in enumerate(cols):
            x = marg + i * (tw + gut)
            y = marg + j * (th + rot + gut)
            p = jpgs.get((canal, tipo))
            if p and Path(p).exists():
                mini = Image.open(p).convert("RGB").resize((tw, th), Image.LANCZOS)
                img.paste(mini, (x, y))
            else:
                d.rectangle([x, y, x + tw, y + th], fill=(60, 30, 30))
            d.text((x, y + th + 10), f"{canal} - {tipo}", font=f, fill=(235, 235, 240))
    destino = Path(destino)
    return gravar_imagem(img, destino, "jpg")


__all__ = ["TIPOS", "specs_exemplo", "capa_sintetica", "preparar_capas", "specs_para_pasta", "prancha",
           "hash_fixo"]
