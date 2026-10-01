# -*- coding: utf-8 -*-
"""story_post_lote.py — lê o lote REAL de estáticos do GTA (lotes\\AAAA-MM-DD_estaticos.json, §4.5)
e decide o que vai na figurinha de enquete do story interativo das 16h.

O story da enquete NÃO é um item "story_enquete" (suposição da rodada 1): é a chave "interativo"
do lote, e a pergunta completa tem ~46 caracteres enquanto a figurinha aceita ~25. Este módulo:
  ler_interativo(lote)             -> a chave "interativo" do lote real OU o item "story_enquete" antigo
  pergunta_da_figurinha(it, 25)    -> (1) interativo.pergunta_curta se existir e couber;
                                      (2) encurtar_pergunta(pergunta): determinística, nunca corta no
                                          meio de palavra, tira vocativo/introdução e emoji, prefere a
                                          ÚLTIMA oração terminada em "?";
                                      (3) se nada couber -> PerguntaImpossivel (explica em português;
                                          NÃO corta no escuro)
  opcoes_da_figurinha(it, 25)      -> 2 a 4 opções, cada uma <= 25 (senão OpcoesInvalidas com o motivo)
  decidir(lote)                    -> tudo junto: pergunta, opções, arte, horário, destaque, conta/canal
  itens_do_lote(lote)              -> stories[] (hora, arquivo, tema), carrossel, threads[], comunidade;
                                      as chaves instagram/facebook são TEXTO LIVRE de status

Uso:
  python scripts\\story_post_lote.py lotes\\2026-10-01_estaticos.json [--limite 25] [--limite-opcao 25] [--json]
    imprime a decisão (código 0 = dá para postar; 1 = não dá: pergunta impossível, opções fora do
    limite, lote sem interativo ou ilegível)
  O story_post.py (comando `enquete`) usa este módulo; o formato antigo continua valendo como plano B.

Regras:
- Só biblioteca padrão; não toca em rede, adb, relógio nem H:\\ (o lote chega por caminho ou dict).
- Caminhos do PC (H:\\HypadoLocal\\..., G:\\Meu Drive\\Hypado\\...) viram a raiz da máquina (HP_LOCAL /
  HP_DRIVE) por `traduzir_caminho_pc`, para os testes e para outra máquina.
- Emoji sai da pergunta e das opções (a figurinha é texto puro e o adb não digita emoji direito).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

LIMITE_PERGUNTA = 25
LIMITE_OPCAO = 25
MIN_OPCOES, MAX_OPCOES = 2, 4
CANAL_PADRAO = "gta"
FIGURINHA_PADRAO = "enquete"
PREFIXO_VIDEO_NOVO = "vídeo novo:"
RAIZ_LOCAL_PC = r"H:\HypadoLocal"           # só aqui (HP_LOCAL troca)
RAIZ_DRIVE_PC = r"G:\Meu Drive\Hypado"      # só aqui (HP_DRIVE troca)
CHAVES_LISTA_ANTIGA = ("itens", "items", "estaticos", "posts")
TIPO_ANTIGO = "story_enquete"
CHAVES_STATUS = ("instagram", "facebook", "tiktok", "threads", "youtube", "status")

# palavras que, sozinhas antes de "," ou ":", são vocativo/introdução (sem acento, minúsculas)
PALAVRAS_DE_ABERTURA = frozenset("""
e ai entao agora olha so bora vamos la responde fala diz conta me pra pro gente galera pessoal
amigo amiga amigos amigas familia turma povo rapaziada mano mana hp hypado hypados fa fas torcida
comissao jogador jogadores gamer gamers pergunta enquete do dia da hoje voce voces ser sendo
sincero sincera sinceramente ok
""".split())
# fecho que não acrescenta nada: "..., hein?" / "..., galera?"
VOCATIVOS_DE_FECHO = frozenset("""
hein ne neh em galera gente pessoal amigo amiga amigos familia turma povo rapaziada mano mana hp
hypado hypados torcida comissao
""".split())

_RX_EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\U0001FB00-\U0001FBFF"
    "\u2600-\u27BF\u2B00-\u2BFF\u2300-\u23FF\u2190-\u21FF"
    "\u2934\u2935\u3030\u303D\u3297\u3299\u00A9\u00AE\u2122\u2139"
    "\u231A\u231B\u24C2\u25AA-\u25FE"
    "\uFE0E\uFE0F\u200D\u20E3"
    "\U0001F1E6-\U0001F1FF\U000E0020-\U000E007F]")
_RX_HANDLE = re.compile(r"@([A-Za-z0-9._]+)")
_RX_FIM_FRASE = re.compile(r"(?<=[.!?…])\s+")
_RX_ABERTURA = re.compile(r"^([^,:;.!?]{1,40}?)\s*[,:;]\s+(.+)$")
_RX_FECHO = re.compile(r"^(.+?)\s*,\s*([^,;:?!]{1,20})\?$")


# ===========================================================================
# Erros (mensagem em português, para leigo)
# ===========================================================================
class LoteErro(ValueError):
    """Base: o lote não serve para a figurinha."""


class LoteInvalido(LoteErro):
    """Lote ilegível, sem interativo ou com figurinha que o story_post não sabe fazer."""


class PerguntaImpossivel(LoteErro):
    """Nenhuma forma honesta da pergunta cabe no limite: quem escreve o lote precisa dar
    interativo.pergunta_curta."""


class OpcoesInvalidas(LoteErro):
    """Menos de 2 ou mais de 4 opções, opção vazia, repetida ou maior que o limite."""


# ===========================================================================
# Texto
# ===========================================================================
def normalizar(s) -> str:
    """minúsculas, sem acento, espaços simples (para comparar palavras)."""
    s = unicodedata.normalize("NFKD", str(s or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s.casefold()).strip()


def sem_emoji(texto) -> str:
    t = _RX_EMOJI.sub("", str(texto or ""))
    t = "".join(ch for ch in t if unicodedata.category(ch) not in ("So", "Cs", "Co"))
    return re.sub(r"\s+", " ", t).strip()


def limpar(texto) -> str:
    """Espaços simples, sem emoji, sem aspas em volta, '?!'/'??' -> '?'."""
    t = sem_emoji(texto)
    t = t.replace("\u2019", "'").replace("\u2018", "'").replace("\xa0", " ")
    t = t.strip(" \"'“”«»")
    t = re.sub(r"[?!]*\?[?!]*", "?", t)
    t = re.sub(r"\s+([?!,.;:])", r"\1", t)
    return re.sub(r"\s+", " ", t).strip()


def _maiuscula(t: str) -> str:
    return t[:1].upper() + t[1:] if t else t


def oracoes(texto: str) -> list[str]:
    """'Furacão chegando. O que você faz?' -> ['Furacão chegando.', 'O que você faz?']"""
    return [o.strip() for o in _RX_FIM_FRASE.split(limpar(texto)) if o.strip()]


def sem_vocativo(oracao: str) -> str:
    """'Galera, o que você faz?' -> 'O que você faz?'; 'Me conta: vai jogar?' -> 'Vai jogar?';
    'O que você faz, hein?' -> 'O que você faz?'. Só mexe se o que sobra continua pergunta."""
    t = limpar(oracao)
    anterior = None
    while t != anterior:
        anterior = t
        m = _RX_ABERTURA.match(t)
        if m and m.group(2).endswith("?"):
            palavras = normalizar(m.group(1)).split()
            if palavras and all(p in PALAVRAS_DE_ABERTURA for p in palavras):
                t = _maiuscula(m.group(2).strip())
                continue
        m = _RX_FECHO.match(t)
        if m and normalizar(m.group(2)) in VOCATIVOS_DE_FECHO and " " in m.group(1):
            t = m.group(1).rstrip(" ,;") + "?"
    return t


def candidatos(pergunta) -> list[tuple[str, str]]:
    """Formas honestas da pergunta, da mais fiel para a mais curta: (texto, origem).
    inteira -> última oração com "?" -> orações anteriores com "?" (cada uma também sem vocativo)."""
    base = limpar(pergunta)
    if not base:
        return []
    lista: list[tuple[str, str]] = [(base, "inteira")]
    com_interrogacao = [o for o in oracoes(base) if o.endswith("?")]
    if len(com_interrogacao) >= 1 and com_interrogacao[-1] != base:
        lista.append((com_interrogacao[-1], "ultima_oracao"))
    for o in reversed(com_interrogacao[:-1]):
        lista.append((o, "oracao_anterior"))
    saida: list[tuple[str, str]] = []
    vistos: set[str] = set()
    for texto, origem in lista:
        # sem vocativo primeiro: "Galera, o que você faz?" vira "O que você faz?" mesmo quando cabe
        for t in (sem_vocativo(texto), texto):
            if t and t not in vistos:
                vistos.add(t)
                saida.append((t, origem if t == texto else origem + "_sem_vocativo"))
    return saida


def encurtar_pergunta(pergunta, limite: int = LIMITE_PERGUNTA) -> str:
    """Primeira forma honesta que cabe no limite (ver `candidatos`); nunca corta palavra.
    Nada cabe -> PerguntaImpossivel."""
    return decidir_pergunta_texto(pergunta, limite)[0]


def decidir_pergunta_texto(pergunta, limite: int = LIMITE_PERGUNTA) -> tuple[str, str]:
    """(texto que vai na figurinha, origem: inteira | ultima_oracao | oracao_anterior [_sem_vocativo])."""
    limite = int(limite)
    cands = candidatos(pergunta)
    if not cands:
        raise PerguntaImpossivel("o interativo não tem pergunta (chave 'pergunta' vazia)")
    for texto, origem in cands:
        if len(texto) <= limite:
            return texto, origem
    inteira = cands[0][0]
    mais_curta = min((c for c, _ in cands), key=len)
    raise PerguntaImpossivel(
        f"a pergunta não cabe na figurinha de enquete: {len(inteira)} caracteres, máximo {limite}: "
        f"'{inteira}'. A forma mais curta que achei sem cortar palavra foi '{mais_curta}' "
        f"({len(mais_curta)}). Não corto no escuro: grave 'pergunta_curta' no interativo do lote com "
        f"uma pergunta de até {limite} caracteres que feche sozinha (ex.: 'O que você faz?').")


def decidir_pergunta(interativo: dict, limite: int = LIMITE_PERGUNTA) -> tuple[str, str]:
    """(1) pergunta_curta se existir e couber; (2) encurtar_pergunta(pergunta); (3) PerguntaImpossivel."""
    limite = int(limite)
    curta = limpar(interativo.get("pergunta_curta"))
    if curta and len(curta) <= limite:
        return curta, "pergunta_curta"
    pergunta = interativo.get("pergunta")
    if not limpar(pergunta):
        if curta:
            raise PerguntaImpossivel(
                f"'pergunta_curta' tem {len(curta)} caracteres (máximo {limite}) e o interativo não tem "
                f"'pergunta' para encurtar: '{curta}'")
        raise PerguntaImpossivel("o interativo não tem 'pergunta' nem 'pergunta_curta'")
    try:
        return decidir_pergunta_texto(pergunta, limite)
    except PerguntaImpossivel as e:
        if curta:
            raise PerguntaImpossivel(f"'pergunta_curta' também não cabe ({len(curta)} caracteres, "
                                     f"máximo {limite}): '{curta}'. {e}") from e
        raise


def pergunta_da_figurinha(interativo: dict, limite: int = LIMITE_PERGUNTA) -> str:
    return decidir_pergunta(interativo, limite)[0]


def opcoes_da_figurinha(interativo: dict, limite: int = LIMITE_OPCAO) -> list[str]:
    """2 a 4 opções, cada uma com até `limite` caracteres, sem emoji, sem repetição. Nunca corta."""
    limite = int(limite)
    brutas = interativo.get("opcoes")
    if isinstance(brutas, str):
        brutas = [brutas]
    if not isinstance(brutas, (list, tuple)):
        raise OpcoesInvalidas("o interativo não tem 'opcoes' (lista de 2 a 4 textos)")
    if not MIN_OPCOES <= len(brutas) <= MAX_OPCOES:
        raise OpcoesInvalidas(f"a enquete precisa de {MIN_OPCOES} a {MAX_OPCOES} opções (veio "
                              f"{len(brutas)}): {list(brutas)}")
    saida: list[str] = []
    for i, o in enumerate(brutas, 1):
        t = limpar(o)
        if not t:
            raise OpcoesInvalidas(f"opção {i} está vazia")
        if len(t) > limite:
            raise OpcoesInvalidas(f"opção {i} tem {len(t)} caracteres (máximo {limite}): '{t}'. "
                                  "Encurte no lote; não corto opção.")
        if normalizar(t) in {normalizar(x) for x in saida}:
            raise OpcoesInvalidas(f"opção {i} repetida: '{t}'")
        saida.append(t)
    return saida


# ===========================================================================
# Lote: ler, achar o interativo, listar itens
# ===========================================================================
def ler_lote(lote) -> dict | list:
    """Caminho (str/Path) -> JSON lido (utf-8, aceita BOM); dict/list -> ele mesmo."""
    if isinstance(lote, (dict, list)):
        return lote
    p = Path(str(lote))
    if not p.is_file():
        raise LoteInvalido(f"lote não encontrado: {p}")
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except (ValueError, OSError) as e:
        raise LoteInvalido(f"lote ilegível ({p.name}): {e}") from e


def traduzir_caminho_pc(caminho) -> Path:
    """'H:\\HypadoLocal\\upload\\x.jpg' -> <HP_LOCAL>\\upload\\x.jpg (no PC fica igual).
    'G:\\Meu Drive\\Hypado\\lotes\\y' -> <HP_DRIVE>\\lotes\\y. Outros caminhos voltam como estão."""
    txt = str(caminho or "").strip()
    for raiz_pc, env in ((RAIZ_LOCAL_PC, "HP_LOCAL"), (RAIZ_DRIVE_PC, "HP_DRIVE")):
        rx = re.compile("^" + re.escape(raiz_pc).replace("\\\\", r"[\\/]") + r"(?:[\\/]+|$)", re.I)
        m = rx.match(txt)
        if m:
            raiz = Path(os.environ.get(env, raiz_pc))
            resto = txt[m.end():]
            return raiz.joinpath(*[x for x in re.split(r"[\\/]+", resto) if x]) if resto else raiz
    return Path(txt)


def conta_do_texto(rede) -> str | None:
    """'Instagram @hpgta6 (compartilhar no Facebook)' -> 'hpgta6'."""
    m = _RX_HANDLE.search(str(rede or ""))
    return m.group(1).rstrip(".").lower() if m else None


def _lista_antiga(dados) -> list:
    if isinstance(dados, list):
        return dados
    if isinstance(dados, dict):
        for k in CHAVES_LISTA_ANTIGA:
            if isinstance(dados.get(k), list):
                return dados[k]
        if "tipo" in dados:
            return [dados]
    return []


def ler_interativo(lote) -> dict | None:
    """A enquete do lote, num formato só:
    {"formato": "real"|"rodada1", "arquivo", "rede", "conta", "compartilhar_facebook", "horario",
     "figurinha", "pergunta", "pergunta_curta", "opcoes", "destaque", "canal", "quem_manda",
     "caixa_enquete", "data"}. None se o lote não tem "interativo" nem item "story_enquete"."""
    dados = ler_lote(lote)
    if isinstance(dados, dict) and isinstance(dados.get("interativo"), dict):
        it = dados["interativo"]
        rede = str(it.get("rede") or "")
        return {
            "formato": "real",
            "arquivo": it.get("arquivo"),
            "rede": rede or None,
            "conta": it.get("conta") or conta_do_texto(rede),
            "compartilhar_facebook": bool(it.get("compartilhar_facebook", "facebook" in rede.lower())),
            "horario": it.get("horario") or it.get("hora"),
            "figurinha": str(it.get("figurinha") or FIGURINHA_PADRAO).strip().lower(),
            "pergunta": it.get("pergunta"),
            "pergunta_curta": it.get("pergunta_curta"),
            "opcoes": it.get("opcoes"),
            "destaque": it.get("destaque"),
            "canal": it.get("canal") or dados.get("canal") or CANAL_PADRAO,
            "quem_manda": it.get("quem_manda"),
            "caixa_enquete": it.get("caixa_enquete"),
            "data": dados.get("data") or dados.get("dia"),
        }
    for it in _lista_antiga(dados):
        if isinstance(it, dict) and normalizar(it.get("tipo")) == TIPO_ANTIGO:
            return {
                "formato": "rodada1",
                "arquivo": it.get("arquivo"),
                "rede": it.get("rede"),
                "conta": it.get("conta"),
                "compartilhar_facebook": bool(it.get("compartilhar_facebook", False)),
                "horario": it.get("horario") or it.get("hora"),
                "figurinha": FIGURINHA_PADRAO,
                "pergunta": it.get("pergunta"),
                "pergunta_curta": it.get("pergunta_curta"),
                "opcoes": it.get("opcoes"),
                "destaque": it.get("destaque"),
                "canal": it.get("canal") or CANAL_PADRAO,
                "quem_manda": it.get("quem_manda"),
                "caixa_enquete": it.get("caixa_enquete"),
                "data": (dados.get("dia") or dados.get("data")) if isinstance(dados, dict) else None,
            }
    return None


def _status(d: dict) -> dict:
    """As chaves instagram/facebook/tiktok... são texto livre de status (não objeto)."""
    return {k: str(d[k]) for k in CHAVES_STATUS if isinstance(d.get(k), str)}


def itens_do_lote(lote) -> list[dict]:
    """Tudo o que o lote programa, numa lista com "tipo" e "hora" (ordem do dia):
    story (hora, arquivo, tema, novo_video, status), interativo, carrossel (tema, arquivos, spec,
    legenda, status), threads (hora, texto, status), comunidade_youtube (hora, imagem, texto, status).
    Formato antigo (lista de itens com "tipo"): devolve os itens como vieram, com "hora"."""
    dados = ler_lote(lote)
    saida: list[dict] = []
    if isinstance(dados, dict) and any(k in dados for k in ("stories", "carrossel", "interativo", "threads")):
        for s in dados.get("stories") or []:
            if not isinstance(s, dict):
                continue
            tema = str(s.get("tema") or "")
            novo = normalizar(tema).startswith(normalizar(PREFIXO_VIDEO_NOVO))
            saida.append({"tipo": "story", "hora": s.get("hora"), "arquivo": s.get("arquivo"), "tema": tema,
                          "novo_video": novo,
                          "video_titulo": tema[len(PREFIXO_VIDEO_NOVO):].strip() if novo else None,
                          "status": _status(s)})
        it = dados.get("interativo")
        if isinstance(it, dict):
            saida.append({"tipo": "interativo", "hora": it.get("horario"), "arquivo": it.get("arquivo"),
                          "figurinha": it.get("figurinha") or FIGURINHA_PADRAO, "pergunta": it.get("pergunta"),
                          "pergunta_curta": it.get("pergunta_curta"), "opcoes": it.get("opcoes"),
                          "rede": it.get("rede"), "destaque": it.get("destaque"), "status": _status(it)})
        c = dados.get("carrossel")
        if isinstance(c, dict):
            saida.append({"tipo": "carrossel", "hora": c.get("horario"), "tema": c.get("tema"),
                          "arquivos": c.get("arquivos"), "spec": c.get("spec"), "legenda": c.get("legenda"),
                          "status": _status(c)})
        for t in dados.get("threads") or []:
            if isinstance(t, dict):
                saida.append({"tipo": "threads", "hora": t.get("hora"), "texto": t.get("texto"),
                              "status": _status(t)})
        cy = dados.get("comunidade_youtube")
        if isinstance(cy, dict):
            saida.append({"tipo": "comunidade_youtube", "hora": cy.get("horario"), "imagem": cy.get("imagem"),
                          "texto": cy.get("texto"), "tipo_post": cy.get("tipo"), "status": _status(cy)})
    else:
        for it in _lista_antiga(dados):
            if isinstance(it, dict):
                d = dict(it)
                d.setdefault("hora", it.get("horario"))
                d["tipo"] = normalizar(it.get("tipo")) or "?"
                saida.append(d)
    ordem = sorted(enumerate(saida), key=lambda par: (str(par[1].get("hora") or "99:99"), par[0]))
    return [d for _, d in ordem]


# ===========================================================================
# Decisão
# ===========================================================================
def decidir(lote, limite: int = LIMITE_PERGUNTA, limite_opcao: int = LIMITE_OPCAO) -> dict:
    """O que o story_post vai fazer com a enquete do lote (ou LoteErro explicando por que não dá)."""
    it = ler_interativo(lote)
    if it is None:
        raise LoteInvalido("o lote não tem a chave 'interativo' nem item com tipo 'story_enquete'")
    if it["figurinha"] != FIGURINHA_PADRAO:
        raise LoteInvalido(f"figurinha '{it['figurinha']}' não é enquete: o story_post só sabe fazer enquete")
    pergunta, origem = decidir_pergunta(it, limite)
    opcoes = opcoes_da_figurinha(it, limite_opcao)
    return {
        "pergunta": pergunta, "origem_pergunta": origem, "pergunta_completa": it.get("pergunta"),
        "opcoes": opcoes, "arte": it.get("arquivo"), "horario": it.get("horario"),
        "destaque": it.get("destaque"), "canal": it.get("canal"), "conta": it.get("conta"),
        "rede": it.get("rede"), "compartilhar_facebook": it.get("compartilhar_facebook"),
        "figurinha": it["figurinha"], "formato": it["formato"], "data": it.get("data"),
        "caixa_enquete": it.get("caixa_enquete"), "limite": int(limite), "limite_opcao": int(limite_opcao),
    }


ORIGENS = {"pergunta_curta": "pergunta_curta do lote", "inteira": "a pergunta inteira cabe",
           "ultima_oracao": "última oração com ?", "oracao_anterior": "oração anterior com ?"}


def texto_da_decisao(d: dict) -> str:
    origem = ORIGENS.get(d["origem_pergunta"].replace("_sem_vocativo", ""), d["origem_pergunta"])
    if d["origem_pergunta"].endswith("_sem_vocativo"):
        origem += ", sem vocativo"
    linhas = [f"Story interativo das {d.get('horario') or '?'} — enquete em @{d.get('conta') or '?'}"
              f" (canal {d.get('canal')}{', compartilhar no Facebook' if d.get('compartilhar_facebook') else ''})",
              f"  arte: {d.get('arte')}",
              f"  pergunta completa ({len(str(d.get('pergunta_completa') or ''))}): {d.get('pergunta_completa')}",
              f"  pergunta na figurinha ({len(d['pergunta'])}/{d['limite']}): {d['pergunta']}   [{origem}]",
              "  opções: " + " | ".join(f"{o} ({len(o)})" for o in d["opcoes"]),
              f"  destaque: {d.get('destaque') or '(nenhum)'}"]
    return "\n".join(linhas)


def texto_dos_itens(itens: list[dict]) -> str:
    linhas = ["Itens do lote:"]
    for it in itens:
        hora = it.get("hora") or "--:--"
        if it["tipo"] == "story":
            linhas.append(f"  {hora} story: {it.get('tema')} ({Path(str(it.get('arquivo') or '')).name})")
        elif it["tipo"] == "carrossel":
            linhas.append(f"  {hora} carrossel: {it.get('tema')} ({it.get('arquivos')})")
        elif it["tipo"] == "interativo":
            linhas.append(f"  {hora} interativo ({it.get('figurinha')}): {it.get('pergunta')}")
        elif it["tipo"] == "threads":
            linhas.append(f"  {hora} threads: {str(it.get('texto') or '').splitlines()[0][:60]}")
        else:
            linhas.append(f"  {hora} {it['tipo']}")
        for rede, st in (it.get("status") or {}).items():
            linhas.append(f"      {rede}: {st}")
    return "\n".join(linhas)


# ===========================================================================
# CLI
# ===========================================================================
def _parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="story_post_lote.py",
                                 description="Lê o lote de estáticos e decide a enquete da figurinha.")
    ap.add_argument("lote", help=r"lotes\AAAA-MM-DD_estaticos.json")
    ap.add_argument("--limite", type=int, default=LIMITE_PERGUNTA, help="máximo da pergunta (padrão 25)")
    ap.add_argument("--limite-opcao", type=int, default=LIMITE_OPCAO, help="máximo de cada opção (padrão 25)")
    ap.add_argument("--json", action="store_true", help="imprime a decisão em JSON")
    return ap


def main(argv: list | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        d = decidir(args.lote, args.limite, args.limite_opcao)
        itens = itens_do_lote(args.lote)
    except LoteErro as e:
        print(f"NÃO DÁ: {e}")
        return 1
    if args.json:
        print(json.dumps({"decisao": d, "itens": itens}, ensure_ascii=False, indent=1))
    else:
        print(texto_da_decisao(d))
        print(texto_dos_itens(itens))
    return 0


if __name__ == "__main__":
    sys.exit(main())
