"""esquema_radar — valida a config real do radar (07 Canais\\radar\\<canal>.json, §4.10).

O que faz: confere, sem rodar nada e sem rede, que um dicionário tem as chaves e os tipos
da config do radar_hp.py (a fixture tests/fixtures/pc_real/radar_gta.json é a referência:
as dos outros canais têm as mesmas chaves). Serve para o teste de contrato do PC e para
conferir uma config nova antes de gravar em 07 Canais\\radar\\.

Uso:
    from esquema_radar import validar_config_radar, conferir_config_radar, ConfigRadarInvalida
    problemas = validar_config_radar(dados)            # [] = ok; senão ["campo X: ...", ...]
    conferir_config_radar(dados, nome="radar_gta.json")  # levanta ConfigRadarInvalida com a lista
    python radar_fontes\\esquema_radar.py <config.json> [...]   # 0 ok · 1 problema

Regras:
- Chaves obrigatórias (CHAVES): as da config real do GTA menos `rockstar_newswire`, que só o GTA
  tem (nos outros canais é opcional).
- `canal` ∈ gta|futebol|filmes|carros (o radar_hp.py ainda não conhece Receitas e Destinos).
- `rss`: {nome, url, oficial, filtrar, peso}; `youtube`: {nome, url (@handle do YouTube),
  channel_id (UC + 22), peso, oficial, video_reutilizavel, nota_uso?}; `google_news`: {q, lingua, filtrar?}.
- Flow Games nunca entra (nome ou URL de fonte) — é erro, não aviso.
- Mensagens em português, uma por problema, sempre com o nome do campo.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CANAIS_DO_RADAR = ("gta", "futebol", "filmes", "carros")
LINGUAS = ("pt", "en")
RX_CHANNEL_ID = re.compile(r"^UC[A-Za-z0-9_-]{22}$")
RX_URL = re.compile(r"^https?://\S+$")
RX_HANDLE_YT = re.compile(r"^https?://(www\.)?youtube\.com/@[^/\s]+/?$")
RX_JANELA = re.compile(r"^\d+(h|d|m)$")
RX_FLOW = re.compile(r"flow\s*games|flowgames|flow_games|flowpodcast|flow\s*podcast", re.I)

# chave -> tipo(s) esperado(s); "numero" aceita int e float (sem bool)
CHAVES = {
    "canal": str, "nome": str, "ativo": bool, "google_news_janela": str,
    "google_news": list, "rss": list, "youtube": list, "criadores_do_config": bool,
    "youtube_busca": list, "trends": bool, "palavras": dict, "entidades": dict,
    "bombasticas": list, "fato_novo": list, "negativas": list, "genericas": list,
    "dominios_oficiais": list, "limiares": dict, "max_alertas_dia": int, "max_p0_dia": int,
    "validade_h": dict, "complemento": dict, "yt_html_intervalo_min": int,
    "yt_html_intervalo_oficial_min": int, "yt_refinar_max": int, "yt_refinar_horas": int,
    "dedup": dict, "perguntas": list, "pergunta_padrao": str, "interacoes": list,
    "interacao_padrao": str, "chamadas": dict,
}
OPCIONAIS = {"rockstar_newswire": bool}
LIMIARES = ("P0", "P1", "vph_min", "vph_cheio", "relevancia_min")
COMPLEMENTO = ("min_veiculos_novos_2h", "vph_min", "intervalo_h", "max_partes_dia", "encerrar_sem_calor_h")
CHAMADAS = ("furo", "complemento", "fato_novo")
RSS = {"nome": str, "url": str, "oficial": bool, "filtrar": bool, "peso": "numero"}
YOUTUBE = {"nome": str, "url": str, "channel_id": str, "peso": "numero", "oficial": bool,
           "video_reutilizavel": bool}
GOOGLE_NEWS = {"q": str, "lingua": str}


class ConfigRadarInvalida(ValueError):
    """A config não tem o formato de §4.10 (a mensagem lista cada campo errado)."""


def _tipo_ok(valor, tipo) -> bool:
    if tipo == "numero":
        return isinstance(valor, (int, float)) and not isinstance(valor, bool)
    if tipo is int:
        return isinstance(valor, int) and not isinstance(valor, bool)
    return isinstance(valor, tipo)


def _nome_tipo(tipo) -> str:
    return {str: "texto", bool: "verdadeiro/falso", int: "inteiro", list: "lista", dict: "objeto",
            "numero": "número"}.get(tipo, str(tipo))


def _lista_de_textos(valor, campo, problemas: list[str]) -> None:
    if not isinstance(valor, list):
        problemas.append(f"campo {campo}: tem que ser lista de textos")
    elif any(not isinstance(x, str) or not x.strip() for x in valor):
        problemas.append(f"campo {campo}: todo item tem que ser texto não vazio")


def _dict_de_numeros(valor, campo, problemas: list[str]) -> None:
    if not isinstance(valor, dict):
        problemas.append(f"campo {campo}: tem que ser objeto {{texto: número}}")
        return
    for k, v in valor.items():
        if not isinstance(k, str) or not k.strip():
            problemas.append(f"campo {campo}: chave vazia")
        if not _tipo_ok(v, "numero"):
            problemas.append(f"campo {campo}.{k}: peso tem que ser número (veio {type(v).__name__})")


def _entradas(lista, campo, modelo: dict, problemas: list[str]) -> None:
    if not isinstance(lista, list):
        return
    for i, ent in enumerate(lista):
        onde = f"{campo}[{i}]"
        if not isinstance(ent, dict):
            problemas.append(f"campo {onde}: tem que ser objeto")
            continue
        for k, tipo in modelo.items():
            if k not in ent:
                problemas.append(f"campo {onde}.{k}: faltando")
            elif not _tipo_ok(ent[k], tipo):
                problemas.append(f"campo {onde}.{k}: esperado {_nome_tipo(tipo)}, veio {type(ent[k]).__name__}")
        texto = " ".join(str(ent.get(k) or "") for k in ("nome", "url", "q"))
        if RX_FLOW.search(texto):
            problemas.append(f"campo {onde}: Flow Games nunca entra como fonte")


def validar_config_radar(dados) -> list[str]:
    """Lista de problemas (vazia = a config tem o formato de §4.10). Nunca levanta exceção."""
    p: list[str] = []
    if not isinstance(dados, dict):
        return ["a config tem que ser um objeto JSON {...}"]
    for chave, tipo in CHAVES.items():
        if chave not in dados:
            p.append(f"campo {chave}: faltando")
        elif not _tipo_ok(dados[chave], tipo):
            p.append(f"campo {chave}: esperado {_nome_tipo(tipo)}, veio {type(dados[chave]).__name__}")
    for chave, tipo in OPCIONAIS.items():
        if chave in dados and not _tipo_ok(dados[chave], tipo):
            p.append(f"campo {chave}: esperado {_nome_tipo(tipo)}, veio {type(dados[chave]).__name__}")
    if p and any(m.endswith("faltando") for m in p):
        return p            # sem as chaves de base não adianta olhar o resto
    if dados["canal"] not in CANAIS_DO_RADAR:
        p.append(f"campo canal: tem que ser um de {', '.join(CANAIS_DO_RADAR)} (veio {dados['canal']!r}); "
                 "o radar_hp.py ainda não conhece Receitas e Destinos")
    if not RX_JANELA.match(str(dados["google_news_janela"])):
        p.append(f"campo google_news_janela: esperado '12h' (número + h/d/m), veio {dados['google_news_janela']!r}")
    _entradas(dados["google_news"], "google_news", GOOGLE_NEWS, p)
    for i, ent in enumerate(dados["google_news"] if isinstance(dados["google_news"], list) else []):
        if isinstance(ent, dict) and ent.get("lingua") not in LINGUAS:
            p.append(f"campo google_news[{i}].lingua: tem que ser pt ou en (veio {ent.get('lingua')!r})")
        if isinstance(ent, dict) and "filtrar" in ent and not isinstance(ent["filtrar"], bool):
            p.append(f"campo google_news[{i}].filtrar: esperado verdadeiro/falso")
    _entradas(dados["rss"], "rss", RSS, p)
    for i, ent in enumerate(dados["rss"] if isinstance(dados["rss"], list) else []):
        if isinstance(ent, dict) and isinstance(ent.get("url"), str) and not RX_URL.match(ent["url"]):
            p.append(f"campo rss[{i}].url: não é uma URL http(s) ({ent['url']!r})")
    _entradas(dados["youtube"], "youtube", YOUTUBE, p)
    for i, ent in enumerate(dados["youtube"] if isinstance(dados["youtube"], list) else []):
        if not isinstance(ent, dict):
            continue
        if isinstance(ent.get("url"), str) and not RX_HANDLE_YT.match(ent["url"]):
            p.append(f"campo youtube[{i}].url: esperado https://www.youtube.com/@handle (veio {ent['url']!r})")
        if isinstance(ent.get("channel_id"), str) and not RX_CHANNEL_ID.match(ent["channel_id"]):
            p.append(f"campo youtube[{i}].channel_id: esperado UC + 22 caracteres (veio {ent['channel_id']!r})")
        if "nota_uso" in ent and not isinstance(ent["nota_uso"], str):
            p.append(f"campo youtube[{i}].nota_uso: esperado texto")
        if ent.get("video_reutilizavel") is True and not str(ent.get("nota_uso") or "").strip():
            p.append(f"campo youtube[{i}].nota_uso: obrigatório quando video_reutilizavel é verdadeiro")
    for campo in ("youtube_busca", "bombasticas", "fato_novo", "negativas", "genericas", "dominios_oficiais"):
        _lista_de_textos(dados[campo], campo, p)
    for campo in ("palavras", "entidades"):
        _dict_de_numeros(dados[campo], campo, p)
    for campo, chaves in (("limiares", LIMIARES), ("complemento", COMPLEMENTO)):
        d = dados[campo]
        if isinstance(d, dict):
            for k in chaves:
                if k not in d:
                    p.append(f"campo {campo}.{k}: faltando")
                elif not _tipo_ok(d[k], "numero"):
                    p.append(f"campo {campo}.{k}: esperado número, veio {type(d[k]).__name__}")
    if isinstance(dados["validade_h"], dict):
        for k in ("P0", "P1"):
            if not _tipo_ok(dados["validade_h"].get(k), "numero"):
                p.append(f"campo validade_h.{k}: esperado número de horas")
    if isinstance(dados["dedup"], dict):
        _lista_de_textos(dados["dedup"].get("prefixos_fila"), "dedup.prefixos_fila", p)
    if isinstance(dados["chamadas"], dict):
        for k in CHAMADAS:
            if not isinstance(dados["chamadas"].get(k), str) or not dados["chamadas"][k].strip():
                p.append(f"campo chamadas.{k}: esperado texto não vazio")
    for i, q in enumerate(dados["perguntas"] if isinstance(dados["perguntas"], list) else []):
        onde = f"perguntas[{i}]"
        if not isinstance(q, dict):
            p.append(f"campo {onde}: tem que ser objeto {{se, pergunta, opcoes}}")
            continue
        _lista_de_textos(q.get("se"), f"{onde}.se", p)
        if not isinstance(q.get("pergunta"), str) or not q["pergunta"].strip():
            p.append(f"campo {onde}.pergunta: esperado texto não vazio")
        _lista_de_textos(q.get("opcoes"), f"{onde}.opcoes", p)
        if isinstance(q.get("opcoes"), list) and not 2 <= len(q["opcoes"]) <= 4:
            p.append(f"campo {onde}.opcoes: enquete tem 2 a 4 opções (veio {len(q['opcoes'])})")
    for i, it in enumerate(dados["interacoes"] if isinstance(dados["interacoes"], list) else []):
        onde = f"interacoes[{i}]"
        if not isinstance(it, dict):
            p.append(f"campo {onde}: tem que ser objeto {{se, texto}}")
            continue
        _lista_de_textos(it.get("se"), f"{onde}.se", p)
        if not isinstance(it.get("texto"), str) or not it["texto"].strip():
            p.append(f"campo {onde}.texto: esperado texto não vazio")
    for campo in ("pergunta_padrao", "interacao_padrao", "nome"):
        if not str(dados[campo]).strip():
            p.append(f"campo {campo}: vazio")
    return p


def conferir_config_radar(dados, nome: str = "config do radar") -> dict:
    """Devolve a própria config; levanta ConfigRadarInvalida("<nome> mudou de formato: campo X ...")."""
    problemas = validar_config_radar(dados)
    if problemas:
        raise ConfigRadarInvalida(f"{nome} mudou de formato: " + "; ".join(problemas))
    return dados


def chaves_desconhecidas(dados) -> list[str]:
    """Chaves que a §4.10 não descreve (não é erro: o PC pode ter chaves novas; é para o relatório)."""
    if not isinstance(dados, dict):
        return []
    conhecidas = set(CHAVES) | set(OPCIONAIS)
    return sorted(k for k in dados if k not in conhecidas)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python radar_fontes\\esquema_radar.py",
                                 description="Confere o formato de configs do radar (07 Canais\\radar\\<canal>.json).")
    ap.add_argument("arquivos", nargs="+")
    args = ap.parse_args(argv)
    codigo = 0
    for a in args.arquivos:
        p = Path(a)
        try:
            dados = json.loads(p.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"{p.name}: não consegui ler ({type(e).__name__})")
            codigo = 1
            continue
        problemas = validar_config_radar(dados)
        extras = chaves_desconhecidas(dados)
        if problemas:
            codigo = 1
            print(f"{p.name}: {len(problemas)} problema(s)")
            for m in problemas:
                print(f"  - {m}")
        else:
            print(f"{p.name}: ok" + (f" (chaves fora da §4.10: {', '.join(extras)})" if extras else ""))
    return codigo


if __name__ == "__main__":
    sys.exit(main())
