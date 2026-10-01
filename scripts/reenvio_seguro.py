"""reenvio_seguro — publicador da API sem post duplicado (ticket H).

O `publicador_meta.py` (que já funciona e NÃO é reescrito) importa daqui:

- `ja_publicado(cliente, ig_id, legenda, desde_ts)` → confere na API (GET
  /<ig_id>/media?fields=id,caption,timestamp,permalink&limit=5) se o post já saiu,
  comparando a legenda normalizada (primeiros 80 caracteres, sem espaços nem
  variações invisíveis de emoji) e o horário (≥ início da tentativa − 2 min).
- `publicar_com_reenvio(publicar_fn, conferir_fn, ...)` → 4 tentativas no total
  (1 + 3 reenvios esperando 1, 5 e 15 min). Antes de cada reenvio confere; se já
  saiu, devolve o id encontrado sem publicar de novo. Só "tempo esgotado"
  (timeout / HTTP 5xx) é repetido; qualquer outro erro sobe na hora.
- `fila_story_apos_post(...)` → grava H:\\HypadoLocal\\emulador\\fila_story\\<post_id>.json
  (o story de divulgação só sai DEPOIS do post).

Linha de comando (ajuda: python scripts\\reenvio_seguro.py -h):
    python scripts\\reenvio_seguro.py reenviar <id> [--fila H:\\HypadoLocal\\fila_api] [--simular]
    python scripts\\reenvio_seguro.py story <post_id> --conta gta --canal instagram --link URL ...
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _por_hp_studio_no_caminho() -> None:
    """Acha o app (hpbase) no PC (06 Projeto\\app) ou no repositório (app\\)."""
    aqui = Path(__file__).resolve().parent
    candidatos = [os.environ.get("HP_APP"), aqui.parent / "06 Projeto" / "app",
                  aqui.parent / "app"]
    for c in candidatos:
        if not c:
            continue
        for p in (Path(c), Path(c) / "hp_studio_nuvem", Path(c) / "hp_studio"):
            if (p / "hpbase").is_dir():
                if str(p) not in sys.path:
                    sys.path.insert(0, str(p))
                return


_por_hp_studio_no_caminho()

from hpbase import (FUSO, SegredoAusente, agora, agora_iso, escrever_json,  # noqa: E402
                    ler_json, ler_segredo, mascarar, obter_logger, raiz_local)

ESPERAS_PADRAO = (60, 300, 900)   # 1, 5 e 15 minutos
ESPERA_FINAL = 60                 # última conferida depois da 4ª falha
FOLGA_SEG = 120                   # timestamp ≥ início da tentativa − 2 min
TAM_COMPARACAO = 80

# espaços invisíveis, seletores de variação de emoji, tons de pele e "tags"
_INVISIVEIS = re.compile("[\u00ad\u200b-\u200f\u2060-\u2064\ufe00-\ufe0f"
                         "\U0001f3fb-\U0001f3ff\U000e0000-\U000e007f]")
_NOMES_TIMEOUT = {"Timeout", "ReadTimeout", "ConnectTimeout", "TimeoutError",
                  "ReadTimeoutError", "ConnectTimeoutError", "TempoEsgotado"}


class TempoEsgotado(Exception):
    """O publicador pode levantar esta para dizer 'não sei se saiu'."""


class ReenvioEsgotado(RuntimeError):
    """4 tentativas com tempo esgotado e o post não apareceu na conferência."""

    def __init__(self, mensagem: str, tentativas: int = 0):
        super().__init__(mensagem)
        self.tentativas = tentativas


class ErroGraph(Exception):
    def __init__(self, mensagem: str, status: int | None = None):
        super().__init__(mensagem)
        self.status = status


# ---------------------------------------------------------------- legenda e tempo
def normalizar_legenda(texto, n: int = TAM_COMPARACAO) -> str:
    """Primeiros n caracteres sem espaço nenhum, sem variações invisíveis de emoji."""
    s = unicodedata.normalize("NFKC", str(texto or ""))
    s = _INVISIVEIS.sub("", s)
    s = "".join(s.split())
    return s.casefold()[:n]


def para_datetime(valor) -> datetime:
    """Aceita epoch (segundos), datetime (sem fuso = Brasília) ou texto ISO/Graph."""
    if isinstance(valor, datetime):
        d = valor
    elif isinstance(valor, (int, float)):
        d = datetime.fromtimestamp(valor, tz=timezone.utc)
    else:
        s = str(valor).strip().replace("Z", "+00:00")
        s = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", s)
        d = datetime.fromisoformat(s)
    return d if d.tzinfo else d.replace(tzinfo=FUSO)


def _id_de(resultado):
    if resultado is None or resultado is False:
        return None
    if isinstance(resultado, dict):
        return resultado.get("id") or resultado.get("media_id") or resultado.get("post_id")
    return str(resultado)


# ---------------------------------------------------------------- conferência na API
def ja_publicado(cliente, ig_id, legenda, desde_ts, rede: str = "instagram",
                 limite: int = 5) -> dict | None:
    """Devolve {"id", "permalink", "timestamp"} do post se ele já saiu; senão None.

    `cliente` é qualquer objeto com `get(caminho, params) -> dict` que já cuida do
    host, da versão e do token (ex.: `ClienteGraph`).
    """
    desde = para_datetime(desde_ts) - timedelta(seconds=FOLGA_SEG)
    if rede == "threads":
        caminho, campo = f"/{ig_id}/threads", "text"
    else:
        caminho, campo = f"/{ig_id}/media", "caption"
    resp = cliente.get(caminho, {"fields": f"id,{campo},timestamp,permalink",
                                 "limit": limite}) or {}
    alvo = normalizar_legenda(legenda)
    for m in resp.get("data") or []:
        try:
            ts = para_datetime(m.get("timestamp"))
        except (TypeError, ValueError):
            continue
        if ts >= desde and normalizar_legenda(m.get(campo)) == alvo:
            return {"id": m.get("id"), "permalink": m.get("permalink"),
                    "timestamp": m.get("timestamp")}
    return None


class ClienteGraph:
    """GET simples na Graph API (Instagram ou Threads). O token nunca sai em erro."""

    def __init__(self, token: str, versao: str = "v21.0",
                 host: str = "https://graph.facebook.com", timeout: float = 30, sessao=None):
        self._token = token
        self.versao, self.host, self.timeout = versao, host.rstrip("/"), timeout
        self._sessao = sessao

    @property
    def sessao(self):
        if self._sessao is None:
            import requests
            self._sessao = requests.Session()
        return self._sessao

    def _mascarar(self, texto) -> str:
        s = str(texto)
        if self._token:
            s = s.replace(self._token, "***")
        return mascarar(s)

    def get(self, caminho: str, params: dict | None = None) -> dict:
        url = caminho if caminho.startswith("http") else \
            f"{self.host}/{self.versao}/{caminho.lstrip('/')}"
        try:
            r = self.sessao.get(url, params={**(params or {}), "access_token": self._token},
                                timeout=self.timeout)
        except Exception as e:  # noqa: BLE001 — só a mensagem mascarada sobe
            erro = e
        else:
            erro = None
            if r.status_code >= 400:
                try:
                    msg = (r.json().get("error") or {}).get("message", "")
                except Exception:  # noqa: BLE001
                    msg = ""
                raise ErroGraph(self._mascarar(f"HTTP {r.status_code} em {caminho}: {msg}")[:300],
                                status=r.status_code)
            return r.json()
        tipo = TempoEsgotado if eh_tempo_esgotado(erro) else ErroGraph
        raise tipo(self._mascarar(f"{type(erro).__name__}: {erro}")[:300])


# ---------------------------------------------------------------- tempo esgotado
def _nome_timeout(e: BaseException) -> bool:
    return isinstance(e, TimeoutError) or bool(
        {c.__name__ for c in type(e).__mro__} & _NOMES_TIMEOUT)


def status_http(e: BaseException) -> int | None:
    for attr in ("status", "status_code", "codigo_http", "http_status"):
        v = getattr(e, attr, None)
        if isinstance(v, int):
            return v
    v = getattr(getattr(e, "response", None), "status_code", None)
    return v if isinstance(v, int) else None


def eh_tempo_esgotado(e: BaseException) -> bool:
    """Timeout ou HTTP 5xx = 'não sei se saiu'. Qualquer outra coisa sobe na hora."""
    if _nome_timeout(e):
        return True
    st = status_http(e)
    if st is not None:
        return 500 <= st <= 599
    msg = str(e).lower()
    return bool(re.search(r"timed out|timeout|tempo esgotado|\b(http|status)\s*5\d\d\b", msg))


# ---------------------------------------------------------------- publicar com reenvio
def publicar_com_reenvio(publicar_fn, conferir_fn, esperas=ESPERAS_PADRAO, simular=False,
                         dormir=time.sleep, relatorio: dict | None = None, log=None,
                         espera_final: float = ESPERA_FINAL):
    """Publica com até 1 + len(esperas) tentativas, sem nunca duplicar.

    Devolve o id do post (o publicado agora ou o que já tinha saído). Em `simular`
    não publica nem espera: devolve None e descreve o que faria em `relatorio`.
    Levanta ReenvioEsgotado depois da última falha (e de uma conferida final).
    """
    rel = relatorio if relatorio is not None else {}
    rel.update({"tentativas": 0, "ja_tinha_saido": False, "simulado": bool(simular),
                "eventos": []})

    def evento(txt):
        txt = mascarar(txt)
        rel["eventos"].append(txt)
        if log:
            log.info(txt)

    def conferir():
        ident = _id_de(conferir_fn())
        if ident:
            rel["ja_tinha_saido"] = True
            evento(f"conferido: o post já tinha saído ({ident}); não republico")
        return ident

    if simular:
        mins = ", ".join(f"{e / 60:g}" for e in esperas)
        evento(f"SIMULAR: publicaria com até {1 + len(esperas)} tentativas "
               f"(esperas de {mins} min), conferindo na API antes de cada reenvio")
        return None

    for i in range(len(esperas) + 1):
        if i > 0:
            evento(f"esperando {esperas[i - 1]} s para conferir se saiu")
            dormir(esperas[i - 1])
            try:
                ident = conferir()
            except Exception as e:  # noqa: BLE001 — sem conferir, não republica às cegas
                evento(f"não deu para conferir ({type(e).__name__}: {e}); não republico agora")
                continue
            if ident:
                return ident
        rel["tentativas"] += 1
        try:
            ident = _id_de(publicar_fn())
        except Exception as e:  # noqa: BLE001
            if not eh_tempo_esgotado(e):
                evento(f"tentativa {rel['tentativas']}: erro que não é tempo esgotado "
                       f"({type(e).__name__}); parou")
                raise
            evento(f"tentativa {rel['tentativas']}: tempo esgotado ({type(e).__name__}: "
                   f"{str(e)[:150]})")
            continue
        evento(f"publicado na tentativa {rel['tentativas']}: {ident}")
        return ident

    if espera_final:
        dormir(espera_final)
    try:
        ident = conferir()
    except Exception as e:  # noqa: BLE001
        ident = None
        evento(f"conferida final falhou ({type(e).__name__}: {e})")
    if ident:
        return ident
    raise ReenvioEsgotado(f"{rel['tentativas']} tentativas com tempo esgotado e o post não "
                          f"apareceu na API", rel["tentativas"])


# ---------------------------------------------------------------- fila da API
CAMPOS_LEGENDA = ("legenda", "caption", "texto", "text")
CAMPOS_INICIO = ("tentativa_inicio", "inicio_tentativa", "tentado_em", "iniciado_em",
                 "agendado_para")


def pasta_fila_padrao() -> Path:
    return raiz_local() / "fila_api"


def achar_item(fila, item_id: str) -> Path:
    fila = Path(fila) if fila else pasta_fila_padrao()
    direto = fila / f"{item_id}.json"
    if direto.exists():
        return direto
    for p in sorted(fila.rglob(f"{item_id}.json")):
        return p
    for p in sorted(fila.rglob("*.json"))[:5000]:
        dados = ler_json(p, {}) or {}
        if isinstance(dados, dict) and str(dados.get("id")) == str(item_id):
            return p
    raise FileNotFoundError(f"item {item_id} não encontrado em {fila}")


def legenda_do_item(item: dict) -> str:
    for k in CAMPOS_LEGENDA:
        if item.get(k):
            return str(item[k])
    return ""


def inicio_do_item(item: dict, agora_=None) -> datetime:
    for k in CAMPOS_INICIO:
        if item.get(k):
            try:
                return para_datetime(item[k])
            except (TypeError, ValueError):
                continue
    return (agora_ or agora()) - timedelta(hours=24)  # sem data: janela larga (a legenda decide)


def cliente_e_id(item: dict, arquivo_segredo: str = "meta_tokens.txt"):
    """Monta o ClienteGraph da conta do item lendo o token (nunca mostrado)."""
    rede = (item.get("rede") or "instagram").lower()
    conta = str(item.get("conta") or "").upper()
    pref = "TH" if rede == "threads" else "IG"

    def ler(*chaves):
        for c in chaves:
            if not c:
                continue
            try:
                return ler_segredo(arquivo_segredo, c)
            except SegredoAusente:
                continue
        return None

    token = ler(item.get("chave_token"), f"{pref}_{conta}_TOKEN", f"{pref}_TOKEN",
                "META_TOKEN" if pref == "IG" else None)
    ident = item.get("ig_id") or item.get("conta_id") or ler(item.get("chave_id"),
                                                              f"{pref}_{conta}_ID")
    if not token or not ident:
        raise SegredoAusente(f"{arquivo_segredo}:{pref}_{conta}_TOKEN/{pref}_{conta}_ID")
    if rede == "threads":
        return ClienteGraph(token, versao="v1.0", host="https://graph.threads.net"), str(ident)
    return ClienteGraph(token), str(ident)


def achar_publicador():
    """Função do publicador_meta.py que publica UM item da fila e devolve o id."""
    import publicador_meta  # noqa: PLC0415 — está em scripts\, ao lado deste arquivo
    for nome in ("publicar_item", "publicar_da_fila", "publicar"):
        fn = getattr(publicador_meta, nome, None)
        if callable(fn):
            return fn
    raise RuntimeError("publicador_meta.py não tem publicar_item(item) -> id; "
                       "veja LEIA_reenvio_seguro.md, passo 'Integração'")


def _marcar(arq: Path, item: dict, **reenvio) -> None:
    item = dict(item)
    item["reenvio"] = {**(item.get("reenvio") or {}), **reenvio, "quando": agora_iso()}
    if reenvio.get("status") == "publicado":
        item["status"] = "publicado"
        item["media_id"] = reenvio.get("media_id")
        if reenvio.get("permalink"):
            item["permalink"] = reenvio["permalink"]
    escrever_json(arq, item)


def reenviar(item_id: str, fila=None, simular: bool = False, cliente=None, ig_id=None,
             publicar_fn=None, esperas=ESPERAS_PADRAO, dormir=time.sleep,
             saida=print, agora_=None) -> dict:
    """Confere se o item saiu; só republica se não saiu. Em `simular` só diz o que faria."""
    log = obter_logger("reenvio_seguro")

    def dizer(txt):
        txt = mascarar(txt)
        log.info(f"{item_id}: {txt}")
        if saida:
            saida(txt)

    arq = achar_item(fila, item_id)
    item = ler_json(arq) or {}
    rede = (item.get("rede") or "instagram").lower()
    if cliente is None:
        cliente, ig_id = cliente_e_id(item)
    ig_id = ig_id or item.get("ig_id") or item.get("conta_id")
    legenda = legenda_do_item(item)
    desde = inicio_do_item(item, agora_)
    prefixo = "SIMULAR — " if simular else ""

    achado = ja_publicado(cliente, ig_id, legenda, desde, rede=rede)
    if achado:
        dizer(f"{prefixo}já saiu: {achado.get('permalink') or achado['id']} — não republico.")
        if not simular:
            _marcar(arq, item, status="publicado", media_id=achado["id"],
                    permalink=achado.get("permalink"), ja_tinha_saido=True, tentativas=0)
        return {"acao": "nada", "ja_tinha_saido": True, "id": achado["id"], "simulado": simular}
    if simular:
        dizer(f"{prefixo}não saiu. Republicaria {rede}/{item.get('conta')} com até "
              f"{1 + len(esperas)} tentativas (esperas de "
              f"{', '.join(f'{e / 60:g}' for e in esperas)} min), conferindo antes de cada reenvio.")
        return {"acao": "republicaria", "ja_tinha_saido": False, "id": None, "simulado": True}

    publicar = publicar_fn or achar_publicador()
    rel: dict = {}
    try:
        novo = publicar_com_reenvio(lambda: publicar(item),
                                    lambda: ja_publicado(cliente, ig_id, legenda, desde, rede=rede),
                                    esperas=esperas, dormir=dormir, relatorio=rel, log=log)
    except Exception as e:
        _marcar(arq, item, status="erro", erro=mascarar(f"{type(e).__name__}: {e}")[:300],
                tentativas=rel.get("tentativas"))
        dizer(f"falhou: {type(e).__name__}: {e}")
        raise
    _marcar(arq, item, status="publicado", media_id=novo, ja_tinha_saido=rel["ja_tinha_saido"],
            tentativas=rel["tentativas"])
    dizer(("já tinha saído: " if rel["ja_tinha_saido"] else "republicado: ") + str(novo))
    return {"acao": "ja_tinha_saido" if rel["ja_tinha_saido"] else "republicado",
            "ja_tinha_saido": rel["ja_tinha_saido"], "id": novo, "simulado": False,
            "tentativas": rel["tentativas"]}


# ---------------------------------------------------------------- story depois do post
def pasta_fila_story() -> Path:
    return raiz_local() / "emulador" / "fila_story"


def fila_story_apos_post(post_id, conta, canal, link, publicado_em, titulo, destaque=None,
                         pasta=None) -> Path:
    """Põe o story de divulgação na fila do emulador (só com o post já no ar).

    Nunca sobrescreve: se o <post_id>.json já existe (na fila ou em feitos\\), não
    faz nada — assim não sai story duplicado.
    """
    if not post_id or not link:
        raise ValueError("story só depois do post: faltam o id e/ou o link do post")
    pasta = Path(pasta) if pasta else pasta_fila_story()
    nome = re.sub(r"[^A-Za-z0-9_.-]", "_", str(post_id))
    arq = pasta / f"{nome}.json"
    if arq.exists() or (pasta / "feitos" / f"{nome}.json").exists():
        return arq
    quando = publicado_em.isoformat(timespec="seconds") if isinstance(publicado_em, datetime) \
        else publicado_em
    escrever_json(arq, {"post_id": str(post_id), "conta": conta, "canal": canal, "link": link,
                        "publicado_em": quando, "titulo": titulo, "destaque": destaque,
                        "status": "pendente", "criado_em": agora_iso(),
                        "origem": "reenvio_seguro.fila_story_apos_post"})
    obter_logger("reenvio_seguro").info(f"story na fila: {arq.name} ({conta}/{canal})")
    return arq


# ---------------------------------------------------------------- linha de comando
class _Formatador(argparse.HelpFormatter):
    def add_usage(self, usage, actions, groups, prefix=None):
        return super().add_usage(usage, actions, groups, "uso: " if prefix is None else prefix)


def _pt(ap):
    ap._positionals.title = "argumentos"
    ap._optionals.title = "opções"
    ap.add_argument("-h", "--help", action="help", help="mostra esta ajuda e sai")
    return ap


def montar_parser() -> argparse.ArgumentParser:
    ap = _pt(argparse.ArgumentParser(
        prog="python scripts\\reenvio_seguro.py", add_help=False, formatter_class=_Formatador,
        description="Reenvio seguro do publicador da API (sem post duplicado) e fila do story."))
    sub = ap.add_subparsers(dest="comando", metavar="comando", title="comandos")
    sub.required = True
    r = _pt(sub.add_parser("reenviar", add_help=False, formatter_class=_Formatador,
                           help="confere se o item da fila saiu e só republica se não saiu"))
    r.add_argument("id", help="id do item da fila (nome do .json)")
    r.add_argument("--fila", help=r"pasta da fila (padrão H:\HypadoLocal\fila_api)")
    r.add_argument("--simular", action="store_true",
                   help="só confere e diz o que faria; não publica nem grava")
    s = _pt(sub.add_parser("story", add_help=False, formatter_class=_Formatador,
                           help="põe o story de divulgação na fila do emulador (após o post)"))
    s.add_argument("post_id")
    s.add_argument("--conta", required=True)
    s.add_argument("--canal", required=True)
    s.add_argument("--link", required=True)
    s.add_argument("--publicado-em", required=True, dest="publicado_em")
    s.add_argument("--titulo", default="")
    s.add_argument("--destaque", default=None)
    return ap


def main(argv=None) -> int:
    args = montar_parser().parse_args(argv)
    try:
        if args.comando == "reenviar":
            reenviar(args.id, fila=args.fila, simular=args.simular)
            return 0
        if args.comando == "story":
            arq = fila_story_apos_post(args.post_id, args.conta, args.canal, args.link,
                                       args.publicado_em, args.titulo, args.destaque)
            print(f"story na fila: {arq}")
            return 0
    except (FileNotFoundError, SegredoAusente, ValueError) as e:
        print(f"Erro: {mascarar(str(e))}", file=sys.stderr)
        return 2
    except Exception as e:  # noqa: BLE001
        print(f"Erro: {mascarar(f'{type(e).__name__}: {e}')}", file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
