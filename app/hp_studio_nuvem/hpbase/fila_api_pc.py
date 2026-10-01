"""fila_api_pc — a fila REAL da API do Instagram e do Threads (H:\\HypadoLocal\\fila_api\\).

O que faz: monta, valida, grava e lê os itens da fila do `scripts\\publicador_meta.py`
(que está em produção e NÃO é reescrito) com as MESMAS regras e as MESMAS mensagens do
`_validar` dele (Seção 4.1 e 4.2 do enunciado da rodada 2), e dá um adaptador seguro para
chamar o `publicar_item` real por fora, sem nunca passar `simular=True` para ele.

Uso (de outro módulo):
    from hpbase import fila_api_pc as fa
    item = fa.montar_item("hp.futebol", "instagram", "feed", ["frase_feed.jpg"], "legenda...",
                          "2026-09-30 23:20", canal="futebol", titulo="Jorge Jesus...")
    fa.gravar_item(item, pasta_fila)                 # grava <pasta_fila>\\<id>.json (atômico)
    fa.ler_confirmacao(item["id"], pasta_fila)       # {"estado": "no_ar"|"erro"|"pendente"|"desconhecido", ...}
    publicar = fa.publicador_adaptado(publicador_meta.publicar_item,
                                      ler_tokens=publicador_meta.ler_tokens,
                                      meta=fa.ler_meta)                # meta só leitura (nunca regrava)
    publicar(item)  -> {"media_id", "permalink", "publicado_em"}

Formato do item (4.1): id, conta (handle sem @), rede, tipo, arquivos[], legenda, quando
("AAAA-MM-DD HH:MM", hora de Brasília, sem fuso), canal, grupo_whatsapp, titulo (opcional),
capa (opcional, reel), depende_de (opcional). Ids: canais <canal>_<AAAA-MM-DD>_<HHMM>_<slug>_<ig|th>_<tipo>;
GTA gta_<AAAA-MM-DD>_<ig|th>_<tipo>_<HHMM>; texto do Threads dos canais <canal>_th_<AAAA-MM-DD>_<HHMM>_<lote>_<n>.

Regras:
- rede só instagram ou threads (Facebook continua pelo Business Suite); tipo feed|carrossel|reel|story|texto;
  arquivo relativo resolve contra a pasta da fila e tem que existir; legenda <= 2200 (IG) e <= 500 (Threads);
  feed = 1 imagem, reel = 1 vídeo, story = 1 arquivo, carrossel 2-10 (IG) ou 2-20 (Threads), texto sem arquivo.
- Token: aqui só existe o NOME da chave (IG_<handle> / TH_<handle>). `token_do_item` devolve o valor
  só a quem pediu, por função injetada; nada neste módulo imprime, loga ou grava token.
- `publicador_adaptado` NUNCA chama o publicador com simular=True (no PC o simular ainda sobe o arquivo
  para a hospedagem temporária): em simulação devolve um resultado falso sem chamar nada.
- Não importa o publicador_meta (ErroAPI é reconhecido pelo nome da classe) nem usa o `carregar_meta`
  dele (que regrava o meta_tokens_meta.json): o id da conta vem de `id_da_conta(chave, dict)`.
"""
from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path, PureWindowsPath

from .arquivos import FUSO, escrever_json
from .caminhos import pasta_segredos, raiz_local
from .registro import mascarar
from .segredos import SegredoAusente

# --- tabelas reais do publicador_meta.py (4.2) --------------------------------------------
# canal -> (conta, grupo do WhatsApp). O publicador real guarda também a pasta do agendados.json;
# ela está em PASTA_CANAL (nome da pasta em 07 Canais; None = 06 Projeto, caso do GTA).
CANAIS = {
    "gta": ("hpgta6", "HP | Comissão 🚀"),
    "futebol": ("hp.futebol", "HP | Futebol ⚽"),
    "filmes": ("hp.filmes", "HP | Filmes 🎬"),
    "receitas": ("hp.receitas", "HP | Receitas 🍔"),
    "carros": ("hp.carros", "HP | Carros 🏎️"),
    "destinos": ("hp.destinos", "HP | Destinos ✈️"),
}
PASTA_CANAL = {"gta": None, "futebol": "Futebol", "filmes": "Filmes e Series",
               "receitas": "Gastronomia", "carros": "Carros", "destinos": "Viagens"}
CONTA_CANAL = {conta: canal for canal, (conta, _grupo) in CANAIS.items()}
PERFIS = tuple(CONTA_CANAL)
REDES = ("instagram", "threads")
TIPOS = ("feed", "carrossel", "reel", "story", "texto")
EXT_VIDEO = {".mp4", ".mov"}
EXT_IMAGEM = {".jpg", ".jpeg", ".png", ".webp"}
LIMITE_LEGENDA_IG = 2200
LIMITE_TEXTO_TH = 500
CARROSSEL_MAX = {"instagram": 10, "threads": 20}
LIMITE_IG_24H = 100      # posts por conta a cada 24 h via API (carrossel conta 1)
LIMITE_TH_24H = 250
TOLERANCIA = timedelta(minutes=2)
ATRASO_MAX = timedelta(hours=12)
LIMITE_JSON = "limite_24h.json"
LOG = "publicador.log"
SUBPASTAS = ("feitos", "erros", "story_clicavel", "reserva_largada", "removidos")
FORMATO_QUANDO = "%Y-%m-%d %H:%M"
MSG_REDE = "rede tem que ser instagram ou threads (Facebook continua pelo Business Suite)"
RX_STORY_DE_POST = re.compile(r"^(?P<base>.+)_(?P<rede>ig|th)_story$")


class ErroFilaApi(ValueError):
    """Item inválido — a mensagem é a mesma que o publicador gravaria em erros\\<id>.json ("erro")."""


class ErroPublicador(RuntimeError):
    """O publicador real levantou ErroAPI (a mensagem já vem sem token)."""


class LimiteDaConta(ErroPublicador):
    """100 posts do IG / 250 do Threads nas últimas 24 h: o item fica na fila para a próxima volta."""


# --- conta, handle, token ------------------------------------------------------------------
def normalizar_conta(conta) -> str:
    """'@HP.Futebol' -> 'hp.futebol'; aceita o nome do canal ('futebol') no lugar da conta."""
    conta = str(conta or "").strip().lstrip("@").lower()
    if conta in CANAIS:
        conta = CANAIS[conta][0]
    return conta


def handle(item: dict) -> str:
    """Handle da conta ('hp.futebol') a partir de `conta` ou, se faltar, de `canal`."""
    return normalizar_conta(item.get("conta") or item.get("canal"))


def _rede(item: dict) -> str:
    rede = str(item.get("rede") or "").strip().lower()
    if rede not in REDES:
        raise ErroFilaApi(MSG_REDE)
    return rede


def chave_token(item: dict) -> str:
    """IG_<handle> (rede instagram) ou TH_<handle> (rede threads) — o nome da linha em meta_tokens.txt."""
    return ("IG_" if _rede(item) == "instagram" else "TH_") + handle(item)


def normalizar_chave(chave: str) -> str:
    """'ig_@HP.Futebol' -> 'IG_hp.futebol' (como o ler_tokens real faz)."""
    m = re.match(r"^(IG|TH)_@?(.+)$", str(chave or "").strip(), re.I)
    if not m:
        return str(chave or "").strip()
    return f"{m.group(1).upper()}_{normalizar_conta(m.group(2))}"


def token_do_item(item: dict, ler_token) -> str:
    """Devolve o token da conta do item SÓ a quem chamou, pela função injetada `ler_token(chave)`.

    Nunca imprime, loga nem grava. Sem token (None, vazio ou KeyError/SegredoAusente do leitor)
    levanta SegredoAusente só com o NOME da chave.
    """
    chave = chave_token(item)
    try:
        tok = ler_token(chave)
    except (KeyError, FileNotFoundError):
        tok = None
    if not tok:
        raise SegredoAusente(f"meta_tokens.txt:{chave}")
    return str(tok)


def leitor_de_tokens(arquivo: str = "meta_tokens.txt", pasta: Path | None = None):
    """Função `ler(chave) -> token | None` que lê meta_tokens.txt como o publicador real
    (IG_<conta>=<token>, aceita @, aspas e linhas #). Lê só na hora da chamada e nada mostra."""
    def ler(chave: str):
        p = Path(pasta or pasta_segredos()) / arquivo
        alvo = normalizar_chave(chave)
        if not p.exists():
            return None
        for linha in p.read_text(encoding="utf-8-sig").splitlines():
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            k, v = linha.split("=", 1)
            v = v.strip().strip('"').strip("'")
            if v and normalizar_chave(k) == alvo:
                return v
        return None
    return ler


def ler_meta(pasta: Path | None = None) -> dict:
    """meta_tokens_meta.json como dict, SÓ LEITURA (o carregar_meta do publicador regrava o arquivo)."""
    p = Path(pasta or pasta_segredos()) / "meta_tokens_meta.json"
    return _json(p) or {}


def id_da_conta(chave: str, meta_json: dict) -> str | None:
    """contas[chave].id do meta_tokens_meta.json (o id da conta não é segredo); None se não tem."""
    contas = (meta_json or {}).get("contas") or {}
    dados = contas.get(chave) or contas.get(normalizar_chave(chave)) or {}
    ident = dados.get("id") if isinstance(dados, dict) else None
    return str(ident) if ident else None


# --- hora ----------------------------------------------------------------------------------
def inicio(item: dict) -> datetime:
    """datetime (sem fuso, hora de Brasília) de `quando` = "AAAA-MM-DD HH:MM"; aceita "T" no meio."""
    q = item.get("quando")
    if not q:
        raise ErroFilaApi("campo 'quando' faltando")
    try:
        return datetime.strptime(str(q).replace("T", " ")[:16], FORMATO_QUANDO)
    except ValueError as e:
        raise ErroFilaApi(str(e)) from None


def quando_texto(quando) -> str:
    """datetime (com fuso vira Brasília) ou texto (aceita "T") -> "AAAA-MM-DD HH:MM".
    Texto que não é data volta como veio (o validar_item dá a mensagem certa)."""
    if isinstance(quando, datetime):
        if quando.tzinfo is not None:
            quando = quando.astimezone(FUSO).replace(tzinfo=None)
        return quando.strftime(FORMATO_QUANDO)
    txt = str(quando or "").strip()
    try:
        return datetime.strptime(txt.replace("T", " ")[:16], FORMATO_QUANDO).strftime(FORMATO_QUANDO)
    except ValueError:
        return txt


def chegou_a_hora(item: dict, agora: datetime, tolerancia: timedelta = TOLERANCIA) -> bool:
    """Regra do rodar(): sai quando `quando - 2 min <= agora`."""
    return not (inicio(item) - tolerancia > agora)


def esta_vencido(item: dict, agora: datetime, atraso_max: timedelta = ATRASO_MAX) -> bool:
    """Regra do rodar(): venceu há mais de 12 h e não traz publicar_mesmo_atrasado -> vai para erros\\."""
    return agora - inicio(item) > atraso_max and not item.get("publicar_mesmo_atrasado")


def mensagem_vencido(atraso_max: timedelta = ATRASO_MAX) -> str:
    return f"venceu há mais de {atraso_max} e não saiu (decidir se ainda vale)"


# --- id -----------------------------------------------------------------------------------
def slug(texto, maximo: int = 40) -> str:
    """'Novo BMW Série 3!' -> 'novo-bmw-serie-3' (sem acento, só a-z 0-9 e hífen)."""
    t = unicodedata.normalize("NFKD", str(texto or ""))
    t = t.encode("ascii", "ignore").decode("ascii").lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    if len(t) > maximo:
        t = t[:maximo]
        if "-" in t[maximo // 2:]:
            t = t[: t.rfind("-")]
        t = t.strip("-")
    return t or "post"


def id_padrao(canal: str, rede: str, tipo: str, quando: datetime, slug_: str | None = None,
              lote=None, n=None) -> str:
    """Convenção de 4.1: canais <canal>_<data>_<HHMM>_<slug>_<ig|th>_<tipo>; GTA gta_<data>_<ig|th>_<tipo>_<HHMM>;
    texto do Threads dos canais (com lote) <canal>_th_<data>_<HHMM>_<lote>_<n>."""
    r = "ig" if rede == "instagram" else "th"
    data, hora = quando.strftime("%Y-%m-%d"), quando.strftime("%H%M")
    if canal == "gta":
        return f"gta_{data}_{r}_{tipo}_{hora}"
    if tipo == "texto" and r == "th" and lote is not None:
        return f"{canal}_th_{data}_{hora}_{lote}_{1 if n is None else n}"
    return f"{canal}_{data}_{hora}_{slug_ or 'post'}_{r}_{tipo}"


# --- montar e validar ----------------------------------------------------------------------
def pasta_fila_padrao() -> Path:
    return raiz_local() / "fila_api"


def _absoluto(caminho: str) -> bool:
    """Caminho absoluto no Windows (H:\\...) OU no sistema atual (os testes rodam no Linux)."""
    return Path(caminho).is_absolute() or PureWindowsPath(caminho).is_absolute()


def resolver_arquivo(caminho, pasta_fila: Path) -> str:
    """Como o _validar: absoluto fica como está; relativo resolve contra a pasta da fila."""
    s = str(caminho)
    return s if _absoluto(s) else str(Path(pasta_fila) / s)


def montar_bruto(conta, rede, tipo, arquivos, legenda, quando, canal=None, titulo=None, capa=None,
                 depende_de=None, id_=None, grupo_whatsapp=None, slug_=None, lote=None, n=None,
                 **extras) -> dict:
    """O dict de 4.1 SEM validar (o modo sombra da esteira usa para redes fora da fila)."""
    conta_n = normalizar_conta(conta or canal)
    canal_n = str(canal or CONTA_CANAL.get(conta_n) or "").strip().lower()
    item = {
        "id": id_ or "",
        "conta": conta_n,
        "rede": str(rede or "").strip().lower(),
        "tipo": str(tipo or "").strip().lower(),
        "arquivos": [str(a) for a in (arquivos or [])],
        "legenda": "" if legenda is None else str(legenda),
        "quando": quando_texto(quando),
        "canal": canal_n,
        "grupo_whatsapp": grupo_whatsapp or (CANAIS[canal_n][1] if canal_n in CANAIS else ""),
    }
    if not item["id"] and item["quando"]:
        try:
            item["id"] = id_padrao(canal_n, item["rede"], item["tipo"], inicio(item),
                                   slug_ or (slug(titulo) if titulo else None), lote, n)
        except ErroFilaApi:
            pass  # quando inválido: o validar_item dá a mensagem certa
    if titulo:
        item["titulo"] = str(titulo)
    if capa:
        item["capa"] = str(capa)
    if depende_de:
        item["depende_de"] = str(depende_de)
    item.update(extras)
    return item


def _validar_tipo(item: dict) -> None:
    """Regras por tipo (ig_publicar/th_publicar do PC; mensagens da tarefa A1)."""
    tipo, rede = item["tipo"], item["rede"]
    arqs = item["arquivos"]
    n = len(arqs)
    legenda = item.get("legenda") or ""
    ext = Path(arqs[0]).suffix.lower() if n == 1 else ""
    if tipo not in TIPOS:
        raise ErroFilaApi(f"tipo tem que ser feed, carrossel, reel, story ou texto (veio {tipo})")
    if tipo == "carrossel":
        maximo = CARROSSEL_MAX[rede]
        if not 2 <= n <= maximo:
            raise ErroFilaApi(f"carrossel precisa de 2 a {maximo} arquivos (veio {n})")
    elif tipo == "feed":
        if n != 1 or ext not in EXT_IMAGEM:
            raise ErroFilaApi("feed = exatamente 1 imagem (vídeo vai como reel)")
    elif tipo == "reel":
        if n != 1 or ext not in EXT_VIDEO:
            raise ErroFilaApi("reel = exatamente 1 vídeo")
    elif tipo == "story":
        if n != 1:
            raise ErroFilaApi("story = exatamente 1 arquivo")
    elif tipo == "texto":
        if rede != "threads":
            raise ErroFilaApi("post de texto só no Threads")
        if n:
            raise ErroFilaApi(f"post de texto não leva arquivo (veio {n})")
        if not legenda.strip():
            raise ErroFilaApi("post de texto sem legenda")
    if rede == "instagram" and len(legenda) > LIMITE_LEGENDA_IG:
        raise ErroFilaApi(f"legenda com {len(legenda)} caracteres (máx. {LIMITE_LEGENDA_IG} no Instagram)")
    if rede == "threads" and len(legenda) > LIMITE_TEXTO_TH:
        raise ErroFilaApi(f"texto com {len(legenda)} caracteres (máx. {LIMITE_TEXTO_TH} no Threads)")


def validar_item(item: dict, pasta_fila=None, existe=None) -> dict:
    """O _validar real (mesma ordem, mesmas mensagens) + as regras por tipo. Muda o item como ele
    (conta normalizada, canal padrão, arquivos resolvidos) e o devolve. `existe(caminho) -> bool`
    é injetável (padrão: Path.exists) para os testes não precisarem do H:."""
    existe = existe or (lambda p: Path(p).exists())
    pasta_fila = Path(pasta_fila) if pasta_fila else pasta_fila_padrao()
    for campo in ("id", "rede", "tipo", "quando"):
        if not item.get(campo):
            raise ErroFilaApi(f"campo '{campo}' faltando")
    if item["rede"] not in REDES:
        raise ErroFilaApi(MSG_REDE)
    inicio(item)
    item["conta"] = normalizar_conta(item.get("conta") or item.get("canal"))
    if item["conta"] not in PERFIS:
        raise ErroFilaApi(f"conta desconhecida: {item['conta']}")
    if not item.get("canal"):
        item["canal"] = CONTA_CANAL[item["conta"]]
    item["arquivos"] = [resolver_arquivo(a, pasta_fila) for a in item.get("arquivos") or []]
    for a in item["arquivos"] + ([item["capa"]] if item.get("capa") else []):
        if not existe(a):
            raise ErroFilaApi(f"arquivo não existe: {a}")
    _validar_tipo(item)
    return item


def montar_item(conta, rede, tipo, arquivos, legenda, quando, canal=None, titulo=None, capa=None,
                depende_de=None, id_=None, grupo_whatsapp=None, slug_=None, lote=None, n=None,
                pasta_fila=None, existe=None, **extras) -> dict:
    """Devolve o dict de 4.1 já validado como o publicador valida (levanta ErroFilaApi).

    `quando`: "AAAA-MM-DD HH:MM" (aceita "T"; hora de Brasília, sem fuso) ou datetime.
    `arquivos` relativos resolvem contra `pasta_fila` (padrão H:\\HypadoLocal\\fila_api).
    `existe(caminho)` é a função que diz se o arquivo existe (padrão Path.exists).
    """
    if not quando_texto(quando):
        raise ErroFilaApi("campo 'quando' faltando")
    inicio({"quando": quando_texto(quando)})   # formato errado: a mensagem do strptime, como no PC
    item = montar_bruto(conta, rede, tipo, arquivos, legenda, quando, canal, titulo, capa,
                        depende_de, id_, grupo_whatsapp, slug_, lote, n, **extras)
    return validar_item(item, pasta_fila, existe)


# --- gravar e ler a fila -------------------------------------------------------------------
def _json(p: Path):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, NotADirectoryError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def gravar_item(item: dict, pasta_fila, subpasta: str | None = None) -> Path:
    """Grava <pasta_fila>\\[subpasta\\]<id>.json de forma atômica e devolve o caminho."""
    pasta = Path(pasta_fila) / subpasta if subpasta else Path(pasta_fila)
    return escrever_json(pasta / f"{item['id']}.json", item)


def _confirmacao(estado, pasta=None, link=None, erro=None, publicado_em=None, media_id=None, **mais):
    d = {"estado": estado, "link": link, "erro": erro, "publicado_em": publicado_em,
         "media_id": media_id, "pasta": pasta}
    d.update(mais)
    return d


def ler_confirmacao(id_: str, pasta_fila) -> dict:
    """Onde o item está e o que aconteceu com ele:
    feitos\\ -> "no_ar" (link, publicado_em, media_id); erros\\ -> "erro" (erro ou ultimo_erro);
    raiz, story_clicavel\\ e reserva_largada\\ -> "pendente"; removidos\\<motivo>\\ -> "erro"
    (tirado à mão); em lugar nenhum -> "desconhecido". `pasta` diz onde achou."""
    pasta = Path(pasta_fila)
    nome = f"{id_}.json"
    d = _json(pasta / "feitos" / nome)
    if isinstance(d, dict):
        res = d.get("resultado") or {}
        return _confirmacao("no_ar", "feitos", link=res.get("permalink"), media_id=res.get("media_id"),
                            publicado_em=res.get("publicado_em"))
    d = _json(pasta / "erros" / nome)
    if isinstance(d, dict):
        return _confirmacao("erro", "erros", erro=d.get("erro") or d.get("ultimo_erro") or "erro sem descrição",
                            tentativas=d.get("tentativas"))
    for sub in ("", "story_clicavel", "reserva_largada"):
        d = _json((pasta / sub / nome) if sub else (pasta / nome))
        if isinstance(d, dict):
            return _confirmacao("pendente", sub or "raiz", erro=d.get("ultimo_erro"),
                                tentativas=d.get("tentativas"))
    for p in sorted((pasta / "removidos").glob(f"*/{nome}")) if (pasta / "removidos").is_dir() else []:
        motivo = p.parent.name
        return _confirmacao("erro", f"removidos/{motivo}", erro=f"tirado da fila à mão (removidos\\{motivo})")
    return _confirmacao("desconhecido")


def post_que_falta(item: dict, pasta_fila) -> str | None:
    """Id do post de que este item depende e que ainda NÃO está no ar; None se pode sair
    (regra real: story irmão <base>_ig_story espera <base>_ig_carrossel|reel|feed em feitos\\)."""
    pasta = Path(pasta_fila)
    ids = [item["depende_de"]] if item.get("depende_de") else []
    if not ids and item.get("tipo") == "story":
        m = RX_STORY_DE_POST.match(str(item.get("id") or ""))
        if m:
            ids = [f"{m['base']}_{m['rede']}_{t}" for t in ("carrossel", "reel", "feed")]
    falta = None
    for i in ids:
        if (pasta / "feitos" / f"{i}.json").exists():
            return None
        if any((p / f"{i}.json").exists() for p in (pasta, pasta / "erros", pasta / "reserva_largada",
                                                     pasta / "removidos")):
            falta = falta or i
    return falta  # None também quando o post irmão não existe em lugar nenhum (story avulso)


def ler_limite_24h(pasta_fila) -> dict:
    """limite_24h.json: {"IG_<conta>": ["AAAA-MM-DD HH:MM", ...]} ({} se não existe)."""
    d = _json(Path(pasta_fila) / LIMITE_JSON)
    return d if isinstance(d, dict) else {}


def publicacoes_24h(limite: dict, chave: str, agora: datetime) -> int:
    """Quantas publicações a conta fez nas últimas 24 h (contadas a partir de `agora`)."""
    n = 0
    for txt in (limite or {}).get(normalizar_chave(chave)) or []:
        try:
            q = datetime.strptime(str(txt)[:16], FORMATO_QUANDO)
        except ValueError:
            continue
        if timedelta(0) <= agora - q <= timedelta(hours=24):
            n += 1
    return n


def no_limite(limite: dict, chave: str, agora: datetime) -> bool:
    """True quando a conta já bateu 100 (IG) / 250 (Threads) nas últimas 24 h."""
    teto = LIMITE_IG_24H if normalizar_chave(chave).startswith("IG_") else LIMITE_TH_24H
    return publicacoes_24h(limite, chave, agora) >= teto


_RX_LINHA = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (.*)$")
_RX_NO_AR = re.compile(r"^NO AR (?P<id>\S+): (?P<link>\S+)$")
_RX_PUBLICANDO = re.compile(r"^publicando (?P<id>\S+) \((?P<rede>\w+) (?P<tipo>\w+) @(?P<conta>\S+), "
                            r"marcado (?P<marcado>\d{4}-\d{2}-\d{2} \d{2}:\d{2})\)$")
_RX_INVALIDO = re.compile(r"^fila: (?P<id>\S+)\.json inválido: (?P<erro>.*)$")
_RX_HOSPEDADO = re.compile(r"^hospedado \((?P<servico>[^,]+), (?P<tamanho>[^)]+)\): (?P<arquivo>.+?) -> (?P<link>\S+)$")


def ler_log(caminho) -> list[dict]:
    """publicador.log ("AAAA-MM-DD HH:MM:SS texto") -> [{"quando": datetime, "texto", "evento", ...}].
    evento: no_ar (id, link) | publicando (id, rede, tipo, conta, marcado) | invalido (id, erro) |
    hospedado (servico, tamanho, arquivo, link) | outro. `caminho` pode ser a pasta da fila."""
    p = Path(caminho)
    if p.is_dir():
        p = p / LOG
    if not p.exists():
        return []
    saida = []
    for linha in p.read_text(encoding="utf-8", errors="replace").splitlines():
        m = _RX_LINHA.match(linha.strip())
        if not m:
            continue
        quando = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
        texto = m.group(2)
        ev = {"quando": quando, "texto": texto, "evento": "outro"}
        for nome, rx in (("no_ar", _RX_NO_AR), ("publicando", _RX_PUBLICANDO),
                         ("invalido", _RX_INVALIDO), ("hospedado", _RX_HOSPEDADO)):
            mm = rx.match(texto)
            if mm:
                ev["evento"] = nome
                ev.update(mm.groupdict())
                break
        saida.append(ev)
    return saida


# --- adaptador do publicador real -----------------------------------------------------------
def _eh_erro_api(e: BaseException) -> bool:
    """ErroAPI do publicador_meta, por duck typing (não importamos o publicador)."""
    return any(c.__name__ == "ErroAPI" for c in type(e).__mro__)


def _sem_token(texto, toks: dict) -> str:
    s = str(texto)
    for v in (toks or {}).values():
        if v and isinstance(v, str) and len(v) >= 8:
            s = s.replace(v, "***")
    return mascarar(s)


def publicador_adaptado(publicar_item_real, ler_tokens=None, meta=None, simular=False, agora=None):
    """Devolve `publicar(item) -> {"media_id", "permalink", "publicado_em"}` em cima do
    `publicar_item(item, toks, meta, simular=False)` real, injetado.

    - `ler_tokens`: dict ou função que devolve {"IG_<conta>": token, ...} (lida só na hora da chamada);
    - `meta`: dict ou função que devolve o meta_tokens_meta.json (use `ler_meta`, que não regrava);
    - "limite" vira LimiteDaConta; ErroAPI (pelo nome da classe) vira ErroPublicador sem token na mensagem;
    - `simular=True`: devolve {"media_id": "SIMULADO", "permalink": "https://simulado", "publicado_em": ...}
      SEM chamar o publicador (no PC o simular dele ainda sobe o arquivo para a hospedagem temporária);
    - `agora`: datetime ou função (só para o publicado_em da simulação ser determinístico nos testes).
    """
    def _hora() -> str:
        a = agora() if callable(agora) else agora
        return quando_texto(a or datetime.now())

    def _obter(x):
        return x() if callable(x) else (x or {})

    def publicar(item: dict) -> dict:
        if simular:
            return {"media_id": "SIMULADO", "permalink": "https://simulado", "publicado_em": _hora()}
        toks = _obter(ler_tokens)
        try:
            res = publicar_item_real(item, toks, _obter(meta), simular=False)
        except Exception as e:  # noqa: BLE001 — só o ErroAPI é traduzido; o resto sobe como veio
            if _eh_erro_api(e):
                raise ErroPublicador(_sem_token(e, toks)) from None
            raise
        if res == "limite":
            raise LimiteDaConta(f"limite de 24 h da conta {chave_token(item)} (fica na fila)")
        if not isinstance(res, dict):
            raise ErroPublicador(f"resposta inesperada do publicador: {type(res).__name__}")
        return {"media_id": res.get("media_id"), "permalink": res.get("permalink"),
                "publicado_em": res.get("publicado_em")}
    return publicar
