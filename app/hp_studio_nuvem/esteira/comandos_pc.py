"""comandos_pc — a linha de comando EXATA dos scripts do PC (§4.4), como funções puras.

O que faz: cada `argv_*` recebe o pedido normalizado (ou os caminhos) e devolve a LISTA de
argumentos que o PC usa — sem rodar nada, sem aspas, sem string montada. A esteira
(plugins.py) chama estas funções; o `config.json -> "comandos"` pode sobrepor um modelo
(mesmos marcadores de MODELOS: {python} {scripts} {url} {entrada} {saida} {inicio} {fim}...).

Uso:
    from esteira import comandos_pc as cp
    cp.argv_baixar(pedido, destino)                 # ytdlp.py ... --download-sections "*INI-FIM" ... url
    cp.argv_cortar(arq, 6.08, 46.04, "gancho", "tgg", saida, transcricao=None, fade_saida=None, dublar=False)
    cp.argv_estaticos_story("interativo", saida, titulo="Pergunta?")
    cp.argv_posts_render("futebol", spec_json)      # posts_futebol.py render <spec>
    cp.para_humano(argv)                            # texto para imprimir (cita o que tem espaço)
    cp.pedido_de_plano(item_do_plano, config_json)  # item de lote.py (4.5) -> pedido.json da esteira
    cp.argvs_do_pedido(pedido, config_json)         # {"baixar", "transcrever", "cortar", "versao_upload"}

Regras:
- PYTHON_PC = %LOCALAPPDATA%\\Programs\\Python\\Python312\\python.exe (expandido no Windows; no
  Linux fica literal). SCRIPTS_PC = <Drive>\\06 Projeto\\scripts via hpbase.raiz_drive (HP_DRIVE);
  `scripts_pc()` relê a variável a cada chamada (os testes trocam o Drive por pasta temporária).
- Caminho com espaço sai SEM aspas na lista (subprocess por lista não precisa); `para_humano` cita.
- INI = hms(inicio − 4) e FIM = hms(fim + 4) (FOLGA do lote.py), hms = HH:MM:SS.mmm; inicio/fim do
  pedido podem vir como "MM:SS", "HH:MM:SS" ou segundos.
- Pedido com "arquivo" (trecho já baixado): argv_baixar devolve None e copiar_trecho() copia.
- Extra do cortar.py sempre na ordem --transcricao, --fade-saida, --dublar (lote.renderizar).
- Dublagem por padrão: criador com "idioma": "en" no config.json e corte sem "dublar": false.
- PROIBIDOS (não existem nos scripts): ytdlp.py --saida, dublar.py --srt, --texto-arquivo,
  estaticos.py --pedido. lote.py e versao_upload.py não têm --help; emenda.py é só módulo.
"""
from __future__ import annotations

import os
import re
import shutil
from datetime import datetime
from pathlib import Path, PureWindowsPath

from hpbase import raiz_drive, raiz_local

# --- constantes do PC (só aqui) -----------------------------------------------------------
PYTHON_PC = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python312\python.exe")
SCRIPTS_PC = raiz_drive() / "06 Projeto" / "scripts"      # valor na importação; use scripts_pc()
FOLGA = 4.0                                                # s baixados antes e depois do trecho
FORMATO_YTDLP = "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080]/b"
POSTS_POR_CANAL = {"futebol": "posts_futebol.py", "filmes": "posts_filmes.py",
                   "receitas": "posts_receitas.py", "carros": "posts_carros.py",
                   "destinos": "posts_destinos.py"}
SUBCOMANDOS_POSTS_CANAIS = ("render", "exemplos", "destaques", "placar", "gol")
TIPOS_STORY = ("novo_video", "contagem", "noticia", "interativo")
OPCOES_STORY = ("titulo", "texto", "imagem", "video", "fonte", "data", "hoje", "selo")
ACOES_LOTE = ("preparar", "renderizar")
CAMPOS_EMENDA = ("trechos", "zoom", "cobrir", "bipes", "tarjas", "selos")
# campos que o lote.py grava DEPOIS de renderizar/agendar (resultado, não pedido)
CAMPOS_RESULTADO = ("upload", "upload_mb", "duracao_seg", "render_status", "agendado",
                    "agendado_em", "status", "legenda_status", "obs_editor")
MESES = ("Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto",
         "Setembro", "Outubro", "Novembro", "Dezembro")
_RX_VIDEO = re.compile(r"(?:v=|youtu\.be/|/shorts/|/live/)([A-Za-z0-9_-]{6,})")
_RX_CREDITO = re.compile(r"cr[ée]dito:\s*(@[\w.]+)", re.I)
_RX_RUIM_WIN = re.compile(r'[<>:"/\\|?*]')

# Modelos com marcadores = o que vai para config.json -> "comandos" (COMANDOS_PADRAO) e o que
# as argv_* preenchem. "{scripts}/x.py" vira Path(scripts) / "x.py" (barra certa no Windows).
MODELOS = {
    "baixar": ["{python}", "{scripts}/ytdlp.py", "-f", FORMATO_YTDLP, "--merge-output-format", "mp4",
               "-o", "{saida}", "--no-playlist", "--no-warnings",
               "--download-sections", "*{inicio}-{fim}", "--force-keyframes-at-cuts", "{url}"],
    "transcrever": ["{python}", "{scripts}/transcrever.py", "{entrada}", "--id-streamer", "{streamer}"],
    "cortar": ["{python}", "{scripts}/cortar.py", "{entrada}", "--inicio", "{inicio}", "--fim", "{fim}",
               "--gancho", "{gancho}", "--id-streamer", "{streamer}", "--saida", "{saida}"],
    "dublar": ["{python}", "{scripts}/dublar.py", "{entrada}", "--transcricao", "{transcricao}",
               "--inicio", "{inicio}", "--fim", "{fim}"],
    "versao_upload": ["{python}", "{scripts}/versao_upload.py", "{entrada}"],
    "estaticos_carrossel": ["{python}", "{scripts}/estaticos.py", "carrossel", "{entrada}", "{saida}"],
    "estaticos_story": ["{python}", "{scripts}/estaticos.py", "story", "{tipo}", "{saida}"],
    "estaticos_destaques": ["{python}", "{scripts}/estaticos.py", "destaques", "{saida}"],
    "posts_render": ["{python}", "{scripts}/{script}", "render", "{entrada}"],
    "posts_canais": ["{python}", "{scripts}/posts_canais.py", "{subcomando}"],
    "story_clicavel_fila": ["{python}", "{scripts}/story_clicavel.py", "fila"],
    "lote": ["{python}", "{scripts}/lote.py", "{entrada}", "{acao}"],
}


# --- base -----------------------------------------------------------------------------------
def scripts_pc() -> Path:
    """<Drive>\\06 Projeto\\scripts, lendo HP_DRIVE na hora."""
    return raiz_drive() / "06 Projeto" / "scripts"


def _base(python, scripts) -> tuple[str, Path]:
    return (str(python) if python else PYTHON_PC), (Path(scripts) if scripts else scripts_pc())


def preencher(modelo, **valores) -> list[str]:
    """Troca os marcadores do modelo pelos valores (todos viram texto). Falta de marcador
    levanta KeyError com o nome dele."""
    vals = {k: str(v) for k, v in valores.items()}
    saida = []
    for parte in modelo:
        parte = str(parte)
        if parte.startswith("{scripts}/"):
            saida.append(str(Path(vals["scripts"]) / parte[len("{scripts}/"):].format(**vals)))
        else:
            saida.append(parte.format(**vals))
    return saida


def hms(seg) -> str:
    """Segundos -> HH:MM:SS.mmm (igual ao lote.hms; negativo vira 0)."""
    seg = max(0.0, float(seg))
    h, r = divmod(seg, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"


def segundos(valor) -> float:
    """'MM:SS', 'HH:MM:SS', 'MM:SS.m', 46.04, '46,04' -> segundos (float)."""
    if isinstance(valor, bool) or valor is None:
        raise ValueError(f"tempo inválido: {valor!r}")
    if isinstance(valor, (int, float)):
        return float(valor)
    s = str(valor).strip().replace(",", ".")
    if not s:
        raise ValueError("tempo vazio")
    if ":" in s:
        partes = s.split(":")
        if len(partes) not in (2, 3):
            raise ValueError(f"tempo inválido: {valor!r} (use MM:SS ou HH:MM:SS)")
        total = 0.0
        for p in partes:
            total = total * 60 + float(p)
        return total
    return float(s)


def janela(pedido: dict) -> tuple[float, float] | None:
    """(ini, fim) do campo corte: [ini, fim] (lote.py) ou {"inicio", "fim"} (esteira); None se não há."""
    c = pedido.get("corte")
    if isinstance(c, (list, tuple)) and len(c) == 2:
        return float(c[0]), float(c[1])
    if isinstance(c, dict) and c.get("fim") is not None:
        return float(c.get("inicio", 0) or 0), float(c["fim"])
    return None


def id_do_video(pedido: dict) -> str | None:
    if pedido.get("video"):
        return str(pedido["video"])
    m = _RX_VIDEO.search(str(pedido.get("video_url") or pedido.get("fonte_url") or ""))
    return m.group(1) if m else None


def url_do_pedido(pedido: dict) -> str:
    url = pedido.get("video_url") or pedido.get("fonte_url")
    if not url and pedido.get("video"):
        url = f"https://www.youtube.com/watch?v={pedido['video']}"
    if not url:
        raise ValueError("pedido sem vídeo: informe video_url, fonte_url ou video (id do YouTube)")
    return str(url)


def _absoluto(caminho) -> bool:
    return Path(caminho).is_absolute() or PureWindowsPath(str(caminho)).is_absolute()


# --- os argv (§4.4) --------------------------------------------------------------------------
def argv_baixar(pedido: dict, destino, python=None, scripts=None) -> list[str] | None:
    """ytdlp.py com o trecho (inicio−4 .. fim+4). Pedido com "arquivo" (trecho já baixado) -> None
    (use copiar_trecho). SUPOSIÇÃO: sem inicio/fim baixa o vídeo inteiro (baixar.py sem --so-trecho)."""
    if pedido.get("arquivo"):
        return None
    py, sc = _base(python, scripts)
    vals = {"python": py, "scripts": sc, "saida": str(destino), "url": url_do_pedido(pedido)}
    modelo = list(MODELOS["baixar"])
    ini, fim = pedido.get("inicio"), pedido.get("fim")
    if ini is None or fim is None:
        i = modelo.index("--download-sections")
        del modelo[i:i + 3]
        return preencher(modelo, **vals)
    vals["inicio"] = hms(segundos(ini) - FOLGA)
    vals["fim"] = hms(segundos(fim) + FOLGA)
    return preencher(modelo, **vals)


def copiar_trecho(pedido: dict, destino, brutos=None) -> Path:
    """Pedido com "arquivo": copia o trecho já baixado para `destino` (relativo resolve em
    H:\\HypadoLocal\\brutos). Não baixa nada."""
    origem = Path(str(pedido["arquivo"]))
    if not _absoluto(origem):
        origem = Path(brutos) if brutos else raiz_local() / "brutos"
        origem = origem / str(pedido["arquivo"])
    if not origem.exists():
        raise FileNotFoundError(f"trecho já baixado não encontrado: {origem}")
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(origem, destino)
    return destino


def argv_transcrever(bruto, id_streamer=None, python=None, scripts=None) -> list[str]:
    """transcrever.py <bruto> [--id-streamer X] (Whisper local; grava transcricoes\\<nome>.json)."""
    py, sc = _base(python, scripts)
    modelo = list(MODELOS["transcrever"])
    if not id_streamer:
        modelo = modelo[:modelo.index("--id-streamer")]
    return preencher(modelo, python=py, scripts=sc, entrada=str(bruto), streamer=id_streamer or "")


def argv_cortar(arq, ini, fim, gancho, streamer, saida, transcricao=None, fade_saida=None,
                dublar=False, python=None, scripts=None) -> list[str]:
    """O argv EXATO do lote.renderizar: cortar.py <arq> --inicio --fim --gancho --id-streamer --saida
    + extra na ordem --transcricao, --fade-saida, --dublar."""
    py, sc = _base(python, scripts)
    argv = preencher(MODELOS["cortar"], python=py, scripts=sc, entrada=str(arq), inicio=str(ini),
                     fim=str(fim), gancho=str(gancho), streamer=str(streamer), saida=str(saida))
    if transcricao:
        argv += ["--transcricao", str(transcricao)]
    if fade_saida is not None and fade_saida is not False:
        argv += ["--fade-saida", str(fade_saida)]
    if dublar:
        argv += ["--dublar"]
    return argv


def argv_versao_upload(final, python=None, scripts=None) -> list[str]:
    """versao_upload.py <corte.mp4> (sem argparse: nunca passe --help)."""
    py, sc = _base(python, scripts)
    return preencher(MODELOS["versao_upload"], python=py, scripts=sc, entrada=str(final))


def argv_dublar_avulso(corte, transcricao, inicio, fim, saida=None, python=None, scripts=None) -> list[str]:
    """dublar.py <corte já renderizado> --transcricao <json PT> --inicio --fim [--saida]."""
    py, sc = _base(python, scripts)
    argv = preencher(MODELOS["dublar"], python=py, scripts=sc, entrada=str(corte),
                     transcricao=str(transcricao), inicio=str(inicio), fim=str(fim))
    if saida:
        argv += ["--saida", str(saida)]
    return argv


def argv_estaticos_carrossel(spec, saida, tiktok=False, python=None, scripts=None) -> list[str]:
    """estaticos.py carrossel <spec.json> <pasta_saida> [--tiktok]."""
    py, sc = _base(python, scripts)
    argv = preencher(MODELOS["estaticos_carrossel"], python=py, scripts=sc, entrada=str(spec), saida=str(saida))
    if tiktok:
        argv.append("--tiktok")
    return argv


def argv_estaticos_story(tipo, saida, python=None, scripts=None, **opcoes) -> list[str]:
    """estaticos.py story <tipo> <saida.jpg> [--titulo --texto --imagem --video --fonte --data --hoje --selo].
    tipo: novo_video | contagem | noticia | interativo. Opção True = só a bandeira; None/False = fora."""
    if tipo not in TIPOS_STORY:
        raise ValueError(f"tipo de story tem que ser um de {', '.join(TIPOS_STORY)} (veio {tipo!r})")
    ruins = [k for k in opcoes if k not in OPCOES_STORY]
    if ruins:
        raise ValueError(f"opção desconhecida do estaticos.py story: {', '.join(ruins)} "
                         f"(aceita {', '.join('--' + o for o in OPCOES_STORY)})")
    py, sc = _base(python, scripts)
    argv = preencher(MODELOS["estaticos_story"], python=py, scripts=sc, tipo=tipo, saida=str(saida))
    for nome in OPCOES_STORY:
        v = opcoes.get(nome)
        if v is None or v is False:
            continue
        argv.append(f"--{nome}")
        if v is not True:
            argv.append(str(v))
    return argv


def argv_estaticos_destaques(saida, python=None, scripts=None) -> list[str]:
    """estaticos.py destaques <pasta_saida>."""
    py, sc = _base(python, scripts)
    return preencher(MODELOS["estaticos_destaques"], python=py, scripts=sc, saida=str(saida))


def argv_posts_render(canal, spec_json, python=None, scripts=None) -> list[str]:
    """posts_<canal>.py render <spec.json> — futebol, filmes, receitas, carros, destinos.
    GTA não entra aqui (usa estaticos.py); modelo genérico é argv_posts_canais."""
    c = str(canal or "").strip().lower()
    if c not in POSTS_POR_CANAL:
        raise ValueError(f"não há posts_{c}.py: use futebol, filmes, receitas, carros ou destinos "
                         f"(GTA = estaticos.py; genérico = argv_posts_canais)")
    py, sc = _base(python, scripts)
    return preencher(MODELOS["posts_render"], python=py, scripts=sc, script=POSTS_POR_CANAL[c],
                     entrada=str(spec_json))


def argv_posts_canais(subcomando, *args, python=None, scripts=None) -> list[str]:
    """posts_canais.py (molde genérico): render <post.json> | exemplos [pasta] |
    destaques <canal> <pasta> | placar <post.json> | gol <gol.json>."""
    if subcomando not in SUBCOMANDOS_POSTS_CANAIS:
        raise ValueError(f"subcomando do posts_canais.py tem que ser um de "
                         f"{', '.join(SUBCOMANDOS_POSTS_CANAIS)} (veio {subcomando!r})")
    py, sc = _base(python, scripts)
    return preencher(MODELOS["posts_canais"], python=py, scripts=sc, subcomando=subcomando) \
        + [str(a) for a in args]


def argv_story_clicavel_fila(desde=None, python=None, scripts=None) -> list[str]:
    """story_clicavel.py fila [--desde AAAA-MM-DD]."""
    py, sc = _base(python, scripts)
    argv = preencher(MODELOS["story_clicavel_fila"], python=py, scripts=sc)
    if desde:
        argv += ["--desde", str(desde)]
    return argv


def argv_lote(plano, acao, so=None, python=None, scripts=None) -> list[str]:
    """lote.py <plano.json> preparar|renderizar [--so 402,405] (sem argparse: nunca --help)."""
    if acao not in ACOES_LOTE:
        raise ValueError(f"ação do lote.py tem que ser {' ou '.join(ACOES_LOTE)} (veio {acao!r})")
    py, sc = _base(python, scripts)
    argv = preencher(MODELOS["lote"], python=py, scripts=sc, entrada=str(plano), acao=acao)
    if so:
        lista = so if isinstance(so, (list, tuple)) else [so]
        argv += ["--so", ",".join(str(x) for x in lista)]
    return argv


def para_humano(argv) -> str:
    """Linha para imprimir/colar: cita (aspas duplas) o que tem espaço ou aspas."""
    def citar(p) -> str:
        s = str(p)
        if not s:
            return '""'
        if any(ch.isspace() for ch in s) or '"' in s:
            return '"' + s.replace('"', '\\"') + '"'
        return s
    return " ".join(citar(p) for p in argv)


# --- regras do lote.py -----------------------------------------------------------------------
def criador_do_config(config_json: dict | None, id_streamer) -> dict | None:
    alvo = str(id_streamer or "").strip().lower()
    for s in (config_json or {}).get("streamers") or []:
        if isinstance(s, dict) and str(s.get("id", "")).strip().lower() == alvo and alvo:
            return s
    return None


def dublar_por_padrao(pedido: dict, config_json: dict | None) -> bool:
    """Criador com "idioma": "en" no config.json e corte sem "dublar": false -> dublado em PT."""
    if pedido.get("dublar") is False:
        return False
    s = criador_do_config(config_json, pedido.get("streamer") or pedido.get("id_streamer"))
    return bool(s) and str(s.get("idioma") or "").strip().lower() == "en"


def nome_bruto(pedido: dict) -> str:
    """<streamer>_<id do vídeo>_<início em s inteiros> (ex.: tgg_c0Com9SMv1s_883) — nome do bruto
    e da transcrição do lote.py."""
    streamer = pedido.get("streamer") or pedido.get("id_streamer") or "avulso"
    video = id_do_video(pedido) or "video"
    ini = int(segundos(pedido["inicio"])) if pedido.get("inicio") is not None else 0
    return f"{streamer}_{video}_{ini}"


def arquivo_bruto(pedido: dict, brutos=None) -> Path:
    """H:\\HypadoLocal\\brutos\\<nome_bruto>.mp4"""
    pasta = Path(brutos) if brutos else raiz_local() / "brutos"
    return pasta / f"{nome_bruto(pedido)}.mp4"


def arquivo_transcricao(pedido: dict, transcricoes=None) -> Path:
    pasta = Path(transcricoes) if transcricoes else raiz_local() / "transcricoes"
    return pasta / f"{nome_bruto(pedido)}.json"


def _data(pedido: dict) -> datetime | None:
    txt = pedido.get("data") or pedido.get("horario_alvo")
    if not txt:
        return None
    try:
        return datetime.fromisoformat(str(txt).replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def arquivo_corte(pedido: dict, cortes=None) -> Path:
    """01 Fila para postar\\AAAA\\MM Mês\\dd.mm.aaaa HHhMM <gancho>.mp4 (sem data: Reserva\\<gancho>.mp4).
    SUPOSIÇÃO: caracteres proibidos no Windows viram espaço."""
    pasta = Path(cortes) if cortes else raiz_drive() / "01 Fila para postar"
    gancho = " ".join(_RX_RUIM_WIN.sub(" ", str(pedido.get("gancho") or pedido.get("titulo") or "corte")).split())
    d = _data(pedido)
    if d is None:
        return pasta / "Reserva" / f"{gancho}.mp4"
    return pasta / f"{d:%Y}" / f"{d.month:02d} {MESES[d.month - 1]}" / f"{d:%d.%m.%Y %Hh%M} {gancho}.mp4"


def argvs_do_pedido(pedido: dict, config_json: dict | None = None, bruto=None, saida=None,
                    python=None, scripts=None, brutos=None, cortes=None) -> dict:
    """Os 4 comandos que o PC roda para um corte: baixar (None se já tem "arquivo"), transcrever,
    cortar e versao_upload. `bruto`/`saida` sobrepõem os caminhos padrão do PC.
    SUPOSIÇÕES: sem "corte" o trecho é [FOLGA, FOLGA + (fim−inicio)] (o lote encosta em frases pela
    transcrição); com emenda (trechos/zoom/cobrir/bipes/tarjas/selos) o cortar.py recebe
    <bruto>_ed<n>.mkv e --transcricao <bruto>_ed<n>.json (n = número do item no plano)."""
    bruto = Path(bruto) if bruto else arquivo_bruto(pedido, brutos)
    saida = Path(saida) if saida else arquivo_corte(pedido, cortes)
    streamer = pedido.get("streamer") or pedido.get("id_streamer")
    jan = janela(pedido)
    if jan is None:
        dur = segundos(pedido["fim"]) - segundos(pedido["inicio"]) \
            if pedido.get("inicio") is not None and pedido.get("fim") is not None else 0.0
        jan = (FOLGA, FOLGA + dur)
    arq, transcricao = bruto, None
    if any(pedido.get(c) for c in CAMPOS_EMENDA):
        n = pedido.get("n") or pedido.get("lote_n") or 1
        arq = bruto.with_name(f"{bruto.stem}_ed{n}.mkv")
        transcricao = arq.with_suffix(".json")
    dublar = dublar_por_padrao(pedido, config_json) if config_json is not None else bool(pedido.get("dublar"))
    return {
        "baixar": argv_baixar(pedido, bruto, python, scripts),
        "transcrever": argv_transcrever(bruto, streamer, python, scripts),
        "cortar": argv_cortar(arq, jan[0], jan[1], pedido.get("gancho") or pedido.get("titulo") or "",
                              streamer or "", saida, transcricao=transcricao,
                              fade_saida=pedido.get("fade_saida"), dublar=dublar,
                              python=python, scripts=scripts),
        "versao_upload": argv_versao_upload(saida, python, scripts),
    }


def pedido_de_plano(item: dict, config_json: dict | None = None, canal: str = "gta",
                    prioridade: str = "P1") -> dict:
    """Item do plano do lote.py (4.5) -> pedido.json da esteira (normalizar_pedido completa o resto).

    Mantém os campos do lote (streamer, gancho, inicio, fim, video, trechos, zoom, cobrir, fade_saida,
    toque_hp...) para as argv_* e traduz: titulo/legenda -> titulo/legenda_post; video_url -> fonte_url;
    data -> horario_alvo; corte [a, b] -> {"inicio", "fim"}; toque_hp -> narrar_toque_hp + roteiro_narracao;
    dublar pela regra do lote (criador "en"). Crédito: "Crédito: @x" da legenda, senão o do config, senão
    @<streamer>. SUPOSIÇÃO: item já renderizado (render_status/agendado/upload) tem "arquivo" = corte
    pronto na fila do Drive, que é descartado; item sem isso com "arquivo" = trecho já baixado."""
    concluido = any(k in item for k in ("render_status", "agendado", "upload"))
    p = {k: v for k, v in item.items() if k not in CAMPOS_RESULTADO}
    if concluido:
        p.pop("arquivo", None)
    if "n" in p:
        p["lote_n"] = p.pop("n")
    titulo = str(item.get("titulo") or item.get("gancho") or "").strip()
    legenda = str(item.get("legenda") or "")
    streamer = item.get("streamer") or item.get("id_streamer") or ""
    m = _RX_CREDITO.search(legenda)
    cfg_criador = criador_do_config(config_json, streamer) or {}
    credito = m.group(1) if m else (cfg_criador.get("credito") or (f"@{streamer}" if streamer else ""))
    toque = item.get("toque_hp") if isinstance(item.get("toque_hp"), dict) else None
    p.update({
        "canal": canal, "tipo": "reel", "prioridade": prioridade, "titulo": titulo[:200],
        "legenda_post": legenda or None, "fonte_url": url_do_pedido(item),
        "redes": list(item.get("redes") or []), "horario_alvo": item.get("data"),
        "credito": credito, "dublar": dublar_por_padrao(item, config_json),
        "narrar_toque_hp": bool(toque), "observacoes": str(item.get("obs") or ""),
    })
    if p.get("legenda_post") is None:
        p.pop("legenda_post")
    if toque:
        p["roteiro_narracao"] = {"abertura": toque.get("pergunta_abertura"),
                                 "trecho": toque.get("narracao"), "fecho": toque.get("fecho")}
    jan = janela(item)
    if jan:
        p["corte"] = {"inicio": jan[0], "fim": jan[1]}
    if p.get("arquivo"):
        p["arquivos"] = [str(p["arquivo"])]
    return p
