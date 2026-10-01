"""Constantes da esteira: etapas, canais, tipos, redes, contas e critérios."""
from __future__ import annotations

# --- etapas (cada uma é uma pasta dentro de H:\HypadoLocal\esteira\) -------
PEDIDOS = "01_pedidos"
BAIXADOS = "02_baixados"
LEGENDA = "03_legenda_dublagem"
EDICAO = "04_edicao"
REVISAO = "05_revisao"
AGENDADOS = "06_agendados"
POSTADOS = "07_postados"
ERROS = "99_erros"

ETAPAS = (PEDIDOS, BAIXADOS, LEGENDA, EDICAO, REVISAO, AGENDADOS, POSTADOS)
TODAS_AS_PASTAS = ETAPAS + (ERROS,)

# apelidos aceitos na linha de comando (--etapa edicao, --etapa 04 ...)
APELIDOS_ETAPA = {
    "01": PEDIDOS, "pedidos": PEDIDOS, "pedido": PEDIDOS, "curador": PEDIDOS,
    "02": BAIXADOS, "baixados": BAIXADOS, "baixar": BAIXADOS,
    "03": LEGENDA, "legenda": LEGENDA, "dublagem": LEGENDA,
    "legenda_dublagem": LEGENDA,
    "04": EDICAO, "edicao": EDICAO, "edição": EDICAO, "editor": EDICAO,
    "05": REVISAO, "revisao": REVISAO, "revisão": REVISAO,
    "06": AGENDADOS, "agendados": AGENDADOS,
    "07": POSTADOS, "postados": POSTADOS,
    "99": ERROS, "erros": ERROS,
}

# --- pedidos ---------------------------------------------------------------
CANAIS = ("gta", "futebol", "filmes", "receitas", "carros", "destinos")
TIPOS = ("reel", "carrossel", "story", "threads_texto", "estatico")
TIPOS_ESTATICOS = ("carrossel", "story", "threads_texto", "estatico")
TIPOS_VIDEO = ("reel",)
REDES = ("instagram", "facebook", "tiktok", "youtube", "threads", "pinterest")
PRIORIDADES = ("P0", "P1", "P2")

# voz sintética (Piper, scripts\dublar.py) só nestes canais — nunca no futebol
CANAIS_COM_VOZ = ("destinos", "receitas", "carros", "filmes")
# Pinterest só em Receitas, Carros e Destinos
CANAIS_PINTEREST = ("receitas", "carros", "destinos")

CONTAS = {
    "gta": "@hpgta6",
    "futebol": "@hp.futebol",
    "filmes": "@hp.filmes",
    "receitas": "@hp.receitas",
    "carros": "@hp.carros",
    "destinos": "@hp.destinos",
}
NOMES_CANAIS = {
    "gta": "GTA 6 | HP",
    "futebol": "Futebol | HP",
    "filmes": "Filmes e Séries | HP",
    "receitas": "Receitas | HP",
    "carros": "Carros | HP",
    "destinos": "Destinos | HP",
}

# --- revisão ---------------------------------------------------------------
# critério -> etapa para onde o item volta quando esse critério tem a menor
# nota (faixa "Médio"). O revisor pode usar só os critérios que se aplicam.
CRITERIO_ETAPA = {
    "assunto": PEDIDOS,         # escolha do tema, momento, relevância
    "fonte_credito": PEDIDOS,   # fonte oficial, crédito certo, regras de conteúdo
    "gancho": EDICAO,           # os 2 primeiros segundos prendem?
    "legenda": LEGENDA,         # texto, ortografia, sincronia da legenda
    "voz": LEGENDA,             # dublagem / narração Toque HP
    "audio": EDICAO,            # mixagem, volume, loudness
    "enquadramento": EDICAO,    # 1080x1920, nada importante cortado
    "ritmo": EDICAO,            # cortes, duração
    "capa": EDICAO,
    "arte": EDICAO,             # estáticos: design, leitura no celular
    "texto_post": EDICAO,       # legenda do post, hashtags, crédito no texto
}
FAIXAS = (  # (nota mínima, veredito)
    (9.0, "Excelente"),
    (7.0, "Bom"),
    (5.0, "Médio"),
    (0.0, "Razoável"),
)
VEREDITOS_APROVADOS = ("Excelente", "Bom")

# --- arquivos dentro de cada item -----------------------------------------
ARQ_PEDIDO = "pedido.json"
ARQ_POST = "post.json"
ARQ_HISTORICO = "historico.log"
ARQ_ESTADO = "estado.json"
ARQ_ERRO = "erro.json"
ARQ_MARCADOR = ".em_andamento"
ARQ_APROVADO = "aprovado.json"
ARQ_REFAZER = "refazer.json"
ARQ_AGUARDANDO_CURADOR = "aguardando_curador.json"
ARQ_AGENDADOS = "agendados.json"
ARQ_CONFIRMACOES = "confirmacoes.json"
ARQ_AVISO = "aviso_no_ar.json"
ARQ_TEXTO_REVISAO = "texto_revisao.md"

EXT_VIDEO = (".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi")
EXT_IMAGEM = (".png", ".jpg", ".jpeg", ".webp")

LARGURA, ALTURA = 1080, 1920
