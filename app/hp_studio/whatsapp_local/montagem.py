"""Montagem dos textos SEM Claude (funções puras, testáveis).

1) Aviso "no ar": a partir do agendados.json + texto-modelo do AVISO.md.
2) Resumo do dia anterior e resumo de sábado: a partir do metricas_painel.json.

agendados.json (lista, ou {"posts": [...]}) — cada post:
    {"id": "opcional", "canal": "GTA 6 | HP" (ou "gta"), "titulo": "...",
     "horario": "2026-09-30T18:30:00-03:00",
     "links": {"instagram": "https://...", "tiktok": "https://..."},
     "grupo": "opcional", "status": "opcional (cancelado/erro = ignora)"}
  (aceita também: conta, title, publicado_em, quando, urls, e links como
   lista [{"rede": "instagram", "url": "..."}])

Métricas — preferência para as fotos diárias do módulo metricas
(H:\\HypadoLocal\\metricas\\AAAA-MM-DD.json, ver normalizar_fotos_diarias);
senão, um metricas_painel.json num destes formatos:
  a) {"dias": {"2026-09-29": {"GTA 6 | HP": {"instagram": {"seguidores": 10000,
        "views": 30000, "curtidas": 1200, "comentarios": 80, "posts": 2}, ...}}}}
  b) {"registros": [{"dia": "2026-09-29", "canal": "gta", "rede": "instagram",
        "seguidores": 10000, "views": 30000, ...}]}   (ou só a lista)
  Os números de views/curtidas/comentários/posts são DO DIA; seguidores é o
  total no fim do dia.
"""
from __future__ import annotations

import hashlib
import re
from datetime import date, datetime, timedelta
from pathlib import Path

from hpbase import FUSO, ler_json

from .config import (MODELO_EXEMPLO, NOMES_CANAIS, ORDEM_CANAIS, PREFIXO,
                     arquivo_modelo_aviso, nfc)
from .fila import nome_seguro

ORDEM_REDES = ["instagram", "tiktok", "youtube", "facebook", "threads", "pinterest"]
NOMES_REDES = {"instagram": "Instagram", "tiktok": "TikTok", "youtube": "YouTube",
               "facebook": "Facebook", "threads": "Threads", "pinterest": "Pinterest"}
DIAS_SEMANA = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
STATUS_IGNORAR = {"cancelado", "cancelada", "erro", "falhou", "removido", "rascunho"}

MODELO_PADRAO = ("*Claude - * 🚀 No ar agora — {canal}\n\n"
                 "🎬 {titulo}\n🕒 {horario}\n\n{links}")


# ================================================================ datas
def ler_datahora(valor) -> datetime | None:
    """ISO (com ou sem fuso), '2026-09-30 18:30' ou '30/09/2026 18:30' → Brasília."""
    if not valor:
        return None
    if isinstance(valor, datetime):
        d = valor
    else:
        s = str(valor).strip().replace("Z", "+00:00")
        d = None
        try:
            d = datetime.fromisoformat(s)
        except ValueError:
            for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y"):
                try:
                    d = datetime.strptime(s, fmt)
                    break
                except ValueError:
                    continue
        if d is None:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=FUSO)
    return d.astimezone(FUSO)


def nome_canal(canal) -> str:
    c = nfc(canal)
    return NOMES_CANAIS.get(c.lower(), c)


def _ordem_canal(nome: str):
    return (ORDEM_CANAIS.index(nome) if nome in ORDEM_CANAIS else len(ORDEM_CANAIS), nome)


# ================================================================ modelo
def extrair_modelo(texto_md: str) -> str:
    """Tira o modelo de dentro do AVISO.md.

    Ordem: 1) entre <!-- MODELO_WHATSAPP --> e <!-- FIM_MODELO -->;
           2) o primeiro bloco de código ``` ... ```;
           3) o arquivo inteiro.
    """
    t = (texto_md or "").replace("\r\n", "\n")
    m = re.search(r"<!--\s*MODELO_WHATSAPP\s*-->\n?(.*?)\n?<!--\s*FIM_MODELO\s*-->", t, re.S)
    if m:
        return m.group(1).strip("\n")
    m = re.search(r"```[^\n]*\n(.*?)\n```", t, re.S)
    if m:
        return m.group(1)
    return t.strip("\n")


def carregar_modelo_aviso(caminho: Path | None = None) -> tuple[str, str]:
    """(modelo, de_onde_veio). Usa 06 Projeto\\AVISO.md; se não existir ou
    não tiver os marcadores {titulo}/{links}, usa o exemplo do pacote."""
    for p in ([Path(caminho)] if caminho else []) + [arquivo_modelo_aviso(), MODELO_EXEMPLO]:
        try:
            modelo = extrair_modelo(p.read_text(encoding="utf-8-sig"))
        except OSError:
            continue
        if "{titulo}" in modelo or "{links}" in modelo:
            return modelo, str(p)
    return MODELO_PADRAO, "padrão embutido"


def preencher(modelo: str, valores: dict) -> str:
    """Troca {marcador} pelos valores; marcador desconhecido fica como está."""
    return re.sub(r"\{(\w+)\}",
                  lambda m: str(valores[m.group(1)]) if m.group(1) in valores else m.group(0),
                  modelo)


def garantir_prefixo(texto: str) -> str:
    t = texto.strip()
    return t if t.startswith(PREFIXO) else f"{PREFIXO} {t}"


def _limpar_texto(texto: str) -> str:
    linhas = [l.rstrip() for l in texto.replace("\r\n", "\n").split("\n")]
    t = "\n".join(linhas)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


# ============================================================== no ar
def normalizar_links(links) -> dict[str, str]:
    if isinstance(links, list):
        links = {str(i.get("rede", "")): i.get("url") or i.get("link")
                 for i in links if isinstance(i, dict)}
    if not isinstance(links, dict):
        return {}
    return {str(k).strip().lower(): str(v).strip() for k, v in links.items()
            if k and v and str(v).strip()}


def ordenar_redes(links: dict) -> list[str]:
    conhecidas = [r for r in ORDEM_REDES if r in links]
    return conhecidas + sorted(r for r in links if r not in ORDEM_REDES)


def formatar_links(links: dict) -> str:
    return "\n".join(f"{NOMES_REDES.get(r, r.capitalize())}: {links[r]}"
                     for r in ordenar_redes(links))


def _lista_bonita(itens: list[str]) -> str:
    if len(itens) <= 1:
        return "".join(itens)
    return ", ".join(itens[:-1]) + " e " + itens[-1]


def normalizar_post(p) -> dict | None:
    if not isinstance(p, dict):
        return None
    return {
        "id": p.get("id") or p.get("post_id"),
        "canal": nome_canal(p.get("canal") or p.get("conta") or ""),
        "titulo": nfc(p.get("titulo") or p.get("título") or p.get("title") or ""),
        "horario": ler_datahora(p.get("horario") or p.get("horário") or p.get("publicado_em")
                                or p.get("quando") or p.get("data_hora")),
        "links": normalizar_links(p.get("links") or p.get("urls") or {}),
        "grupo": p.get("grupo"),
        "status": nfc(p.get("status") or "").lower(),
    }


def carregar_agendados(caminho: Path) -> list[dict]:
    dados = ler_json(Path(caminho), [])
    if isinstance(dados, dict):
        dados = dados.get("posts") or dados.get("agendados") or []
    return [p for p in (normalizar_post(x) for x in (dados or [])) if p]


def posts_prontos(posts: list[dict], agora: datetime, janela_horas: float = 24) -> list[dict]:
    """Posts que JÁ estão no ar (horário passou, há pelo menos 1 link) e
    não são velhos demais (janela)."""
    saida = []
    for p in posts:
        h = p.get("horario")
        if not (h and p.get("canal") and p.get("titulo") and p.get("links")):
            continue
        if p.get("status") in STATUS_IGNORAR:
            continue
        if h > agora or agora - h > timedelta(hours=janela_horas):
            continue
        saida.append(p)
    return sorted(saida, key=lambda p: p["horario"])


def chave_post(p: dict) -> str:
    if p.get("id"):
        return nome_seguro(str(p["id"]))
    base = f"{p['canal']}|{p['titulo']}|{p['horario'].isoformat() if p.get('horario') else ''}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:12]


def id_mensagem(tipo: str, chave: str, grupo: str) -> str:
    g = hashlib.sha1(nfc(grupo).encode("utf-8")).hexdigest()[:6]
    return f"{tipo}_{chave}_{g}"


def montar_no_ar(post: dict, modelo: str = MODELO_PADRAO) -> str:
    """Texto do aviso "no ar" de UM post (sempre começa com *Claude - *)."""
    links = post.get("links") or {}
    redes = ordenar_redes(links)
    h = post.get("horario")
    valores = {
        "canal": post.get("canal", ""),
        "titulo": post.get("titulo", ""),
        "horario": h.strftime("%H:%M") if h else "",
        "data": h.strftime("%d/%m") if h else "",
        "links": formatar_links(links),
        "redes": _lista_bonita([NOMES_REDES.get(r, r.capitalize()) for r in redes]),
        "link": links[redes[0]] if redes else "",
    }
    for r, url in links.items():
        valores[f"link_{r}"] = url
    return garantir_prefixo(_limpar_texto(preencher(modelo, valores)))


def mensagem_fila(tipo: str, grupo: str, texto: str, ident: str,
                  criado_em: datetime, anexos: list[str] | None = None) -> dict:
    return {"id": ident, "grupo": nfc(grupo), "texto": texto, "anexos": list(anexos or []),
            "tipo": tipo, "criado_em": criado_em.isoformat(timespec="seconds")}


# ============================================================ métricas
CAMPOS = {
    "seguidores": ("seguidores", "followers", "seguidores_total"),
    "views": ("views", "visualizacoes", "visualizações", "plays", "reproducoes", "reproduções"),
    "curtidas": ("curtidas", "likes"),
    "comentarios": ("comentarios", "comentários", "comments"),
    "posts": ("posts", "publicacoes", "publicações", "postagens"),
}


def _numero(v):
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return v
    s = str(v).strip()
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", s):      # 1.234.567 (milhar BR)
        s = s.replace(".", "")
    elif "," in s:                                   # 1.234,5 ou 12,5
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _valores(bruto: dict) -> dict:
    saida = {}
    for campo, nomes in CAMPOS.items():
        for n in nomes:
            if n in bruto and _numero(bruto[n]) is not None:
                saida[campo] = _numero(bruto[n])
                break
    return saida


def normalizar_metricas(dados) -> dict:
    """→ {"AAAA-MM-DD": {"GTA 6 | HP": {"instagram": {campo: número}}}}"""
    saida: dict = {}

    def por(dia, canal, rede, bruto):
        if not (dia and canal and isinstance(bruto, dict)):
            return
        v = _valores(bruto)
        if v:
            saida.setdefault(str(dia)[:10], {}).setdefault(nome_canal(canal), {})[
                str(rede or "total").lower()] = v

    if isinstance(dados, dict) and isinstance(dados.get("dias"), dict):
        for dia, canais in dados["dias"].items():
            for canal, redes in (canais or {}).items():
                if not isinstance(redes, dict):
                    continue
                if any(not isinstance(v, dict) for v in redes.values()):
                    por(dia, canal, "total", redes)       # canal sem separar por rede
                else:
                    for rede, bruto in redes.items():
                        por(dia, canal, rede, bruto)
    registros = dados if isinstance(dados, list) else (
        dados.get("registros") if isinstance(dados, dict) else None)
    for r in registros or []:
        if isinstance(r, dict):
            por(r.get("dia") or r.get("data"), r.get("canal") or r.get("conta"),
                r.get("rede"), r)
    return saida


_FOTO_DIA = re.compile(r"^\d{4}-\d{2}-\d{2}\.json$")


def normalizar_fotos_diarias(pasta: Path) -> dict:
    """Lê as fotos diárias do módulo metricas (H:\\HypadoLocal\\metricas\\AAAA-MM-DD.json).

    Formato da foto: {"data": D, "contas": {"gta": {"instagram": {"seguidores": N,
    "posts": [{"publicado_em", "views", "curtidas", "comentarios"}]}}}}.
    - seguidores do dia d = o da foto do dia d+1 (tirada às 6h, ≈ fim do dia d);
      sem essa foto, vale a do próprio dia d;
    - views/curtidas/comentários/posts do dia d = soma dos posts PUBLICADOS no dia d,
      com os números da foto mais recente que tiver cada post.
    """
    fotos = {}
    for arq in sorted(Path(pasta).glob("*.json")):
        if _FOTO_DIA.match(arq.name):
            dados = ler_json(arq, {})
            if isinstance(dados, dict) and isinstance(dados.get("contas"), dict):
                fotos[arq.stem] = dados
    saida: dict = {}
    seguidores: dict = {}   # (dia, canal, rede) -> (prioridade, valor)
    posts: dict = {}        # (canal, rede, id) -> (data_foto, post)
    for dia_foto, foto in sorted(fotos.items()):
        ontem = (date.fromisoformat(dia_foto) - timedelta(days=1)).isoformat()
        for canal, redes in foto["contas"].items():
            for rede, r in (redes or {}).items():
                if not isinstance(r, dict):
                    continue
                seg = _numero(r.get("seguidores"))
                if seg is not None:
                    for dia, prio in ((ontem, 2), (dia_foto, 1)):
                        chave = (dia, canal, rede)
                        if prio >= seguidores.get(chave, (0, None))[0]:
                            seguidores[chave] = (prio, seg)
                for i, post in enumerate(r.get("posts") or []):
                    if isinstance(post, dict):
                        posts[(canal, rede, post.get("id") or f"{dia_foto}#{i}")] = post
    for (dia, canal, rede), (_, seg) in seguidores.items():
        saida.setdefault(dia, {}).setdefault(nome_canal(canal), {}).setdefault(
            rede, {})["seguidores"] = seg
    for (canal, rede, _), post in posts.items():
        quando = ler_datahora(post.get("publicado_em"))
        if not quando:
            continue
        v = saida.setdefault(quando.date().isoformat(), {}).setdefault(
            nome_canal(canal), {}).setdefault(rede, {})
        v["posts"] = v.get("posts", 0) + 1
        for campo in ("views", "curtidas", "comentarios"):
            n = _numero(post.get(campo))
            if n is not None:
                v[campo] = v.get(campo, 0) + n
    return saida


def carregar_metricas(caminho: Path | None, candidatos: list[Path]) -> dict | None:
    """Preferência: as fotos diárias do módulo metricas (pasta com AAAA-MM-DD.json);
    depois um arquivo nos formatos a) ou b) acima."""
    alvos = [Path(caminho)] if caminho else candidatos
    for p in alvos:
        pasta = p if p.is_dir() else p.parent
        if pasta.is_dir() and any(_FOTO_DIA.match(a.name) for a in pasta.glob("*.json")):
            dados = normalizar_fotos_diarias(pasta)
            if dados:
                return dados
        if p.is_file():
            dados = normalizar_metricas(ler_json(p, {}))
            if dados:
                return dados
    return None


def fmt_int(n) -> str:
    return f"{int(round(n)):,}".replace(",", ".")


def fmt_compacto(n) -> str:
    n = float(n)
    for lim, suf in ((1e6, " mi"), (1e4, " mil")):
        if abs(n) >= lim:
            s = f"{n / (lim if lim == 1e6 else 1e3):.1f}".replace(".", ",")
            return (s[:-2] if s.endswith(",0") else s) + suf
    return fmt_int(n)


def fmt_delta(n) -> str:
    return ("+" if n >= 0 else "-") + fmt_int(abs(n))


def _somar(redes: dict, campo: str):
    vals = [v[campo] for v in redes.values() if campo in v]
    return sum(vals) if vals else None


def _delta_seguidores(fim: dict, inicio: dict):
    """Diferença só nas redes que existem nos dois dias."""
    comuns = [r for r in fim if r in inicio and "seguidores" in fim[r]
              and "seguidores" in inicio[r]]
    if not comuns:
        return None
    return sum(fim[r]["seguidores"] - inicio[r]["seguidores"] for r in comuns)


def _linha(canal: str, seg, delta, views, posts, sufixo_delta="") -> str:
    partes = []
    if seg is not None:
        partes.append(f"{fmt_int(seg)} seguidores"
                      + (f" ({fmt_delta(delta)}{sufixo_delta})" if delta is not None else ""))
    if views is not None:
        partes.append(f"{fmt_compacto(views)} views")
    if posts is not None:
        partes.append(f"{fmt_int(posts)} post" + ("" if int(posts) == 1 else "s"))
    return f"• {canal}: " + (" · ".join(partes) if partes else "sem números")


def _total(linhas_dados: list[tuple], sufixo_delta="") -> str:
    seg = sum(d[1] for d in linhas_dados if d[1] is not None)
    deltas = [d[2] for d in linhas_dados if d[2] is not None]
    views = [d[3] for d in linhas_dados if d[3] is not None]
    posts = [d[4] for d in linhas_dados if d[4] is not None]
    partes = [f"{fmt_int(seg)} seguidores"
              + (f" ({fmt_delta(sum(deltas))}{sufixo_delta})" if deltas else "")]
    if views:
        partes.append(f"{fmt_compacto(sum(views))} views")
    if posts:
        partes.append(f"{fmt_int(sum(posts))} posts")
    return "Total: " + " · ".join(partes)


def montar_resumo_dia(metricas: dict, dia: date) -> str | None:
    """Resumo do dia `dia` (normalmente ontem). None se não há números."""
    d = dia.isoformat()
    if d not in metricas:
        return None
    anterior = metricas.get((dia - timedelta(days=1)).isoformat(), {})
    dados = []
    for canal in sorted(metricas[d], key=_ordem_canal):
        redes = metricas[d][canal]
        dados.append((canal, _somar(redes, "seguidores"),
                      _delta_seguidores(redes, anterior.get(canal, {})),
                      _somar(redes, "views"), _somar(redes, "posts")))
    linhas = [f"{PREFIXO} 📊 Resumo de {DIAS_SEMANA[dia.weekday()]}, {dia:%d/%m}", ""]
    linhas += [_linha(*x) for x in dados]
    linhas += ["", _total(dados)]
    cresceu = [x for x in dados if x[2] is not None and x[2] > 0]
    if cresceu:
        top = max(cresceu, key=lambda x: x[2])
        linhas.append(f"🏆 Destaque: {top[0]} ({fmt_delta(top[2])} seguidores)")
    return "\n".join(linhas)


def semana_do_sabado(sabado: date) -> tuple[date, date]:
    """Semana resumida no sábado: do sábado anterior até a sexta (7 dias)."""
    return sabado - timedelta(days=7), sabado - timedelta(days=1)


def montar_resumo_sabado(metricas: dict, sabado: date) -> str | None:
    ini, fim = semana_do_sabado(sabado)
    dias = [(ini + timedelta(days=i)).isoformat() for i in range(7)]
    dias_com = [d for d in dias if d in metricas]
    if not dias_com:
        return None
    base_dia = (ini - timedelta(days=1)).isoformat()
    canais = sorted({c for d in dias_com for c in metricas[d]}, key=_ordem_canal)
    dados = []
    for canal in canais:
        com_canal = [d for d in dias_com if canal in metricas[d]]
        ultimo = metricas[com_canal[-1]][canal]
        if canal in metricas.get(base_dia, {}):
            inicio = metricas[base_dia][canal]
        elif len(com_canal) > 1:
            inicio = metricas[com_canal[0]][canal]
        else:
            inicio = None
        views = [_somar(metricas[d][canal], "views") for d in com_canal]
        posts = [_somar(metricas[d][canal], "posts") for d in com_canal]
        views = [v for v in views if v is not None]
        posts = [p for p in posts if p is not None]
        dados.append((canal, _somar(ultimo, "seguidores"),
                      _delta_seguidores(ultimo, inicio) if inicio else None,
                      sum(views) if views else None, sum(posts) if posts else None))
    linhas = [f"{PREFIXO} 🗓️ Resumo da semana — {ini:%d/%m} a {fim:%d/%m}", ""]
    linhas += [_linha(*x, sufixo_delta=" na semana") for x in dados]
    linhas += ["", _total(dados, sufixo_delta=" na semana")]
    com_delta = [x for x in dados if x[2] is not None]
    if com_delta:
        top = max(com_delta, key=lambda x: x[2])
        linhas.append(f"🏆 Quem mais cresceu: {top[0]} ({fmt_delta(top[2])})")
        if len(com_delta) > 1:
            baixo = min(com_delta, key=lambda x: x[2])
            if baixo[0] != top[0]:
                linhas.append(f"📉 Precisa de atenção: {baixo[0]} ({fmt_delta(baixo[2])})")
    if len(dias_com) < 7:
        linhas.append(f"(números de {len(dias_com)} de 7 dias)")
    return "\n".join(linhas)


def sabado_de_referencia(hoje: date) -> date:
    """Sábado mais recente (hoje, se hoje for sábado)."""
    return hoje - timedelta(days=(hoje.weekday() - 5) % 7)
