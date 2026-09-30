"""Itens da esteira = pastas.

Nome: P1_2026-09-30_1830_gta_rockstar-quinta
      │  │          │    │   └ slug (do título)
      │  │          │    └ canal
      │  │          └ hora alvo (HHMM, Brasília)
      │  └ data alvo
      └ prioridade: P0 urgente/ao vivo (faixa expressa), P1 do dia, P2 programado

Movimento de pasta: os.replace na mesma unidade (atômico: a pasta está
inteira na origem ou inteira no destino, nunca pela metade) e idempotente
(mover de novo algo que já foi movido não faz nada).
"""
from __future__ import annotations

import errno
import os
import re
import shutil
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from hpbase import anexar_linha, escrever_json, garantir, ler_json

from .constantes import (ARQ_ESTADO, ARQ_HISTORICO, ETAPAS, PRIORIDADES,
                         TODAS_AS_PASTAS)
from .erros import ErroEtapa, ItemNaoEncontrado

RX_NOME = re.compile(r"^(P[0-2])_(\d{4}-\d{2}-\d{2})_(\d{4})_([a-z0-9]+)_(.+)$")


@dataclass(frozen=True)
class InfoNome:
    nome: str
    prioridade: str
    data: str
    hora: str
    canal: str
    slug: str

    @property
    def sem_prioridade(self) -> str:
        return self.nome[3:]

    @property
    def nivel(self) -> int:
        return PRIORIDADES.index(self.prioridade)


def ler_nome(nome: str) -> InfoNome | None:
    m = RX_NOME.match(nome)
    if not m:
        return None
    return InfoNome(nome, *m.groups())


def slugificar(texto: str, maximo: int = 40) -> str:
    """'Rockstar: quinta-feira!' -> 'rockstar-quinta-feira' (sem acento)."""
    t = unicodedata.normalize("NFKD", str(texto))
    t = t.encode("ascii", "ignore").decode("ascii").lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    if len(t) > maximo:
        t = t[:maximo]
        if "-" in t[maximo // 2:]:
            t = t[: t.rfind("-")]
        t = t.strip("-")
    return t or "item"


def montar_nome(prioridade: str, horario: datetime, canal: str, slug: str) -> str:
    return f"{prioridade}_{horario:%Y-%m-%d}_{horario:%H%M}_{canal}_{slug}"


def chave_ordem(nome: str, indice_etapa: int = 0) -> tuple:
    """Ordem de processamento: prioridade, depois horário alvo, depois quem
    está mais adiantado na esteira, depois nome. Nome fora do padrão vai por
    último."""
    info = ler_nome(nome)
    if info is None:
        return (9, "9999-99-99_9999", -indice_etapa, nome)
    return (info.nivel, f"{info.data}_{info.hora}", -indice_etapa, nome)


def eh_item(p: Path) -> bool:
    return p.is_dir() and not p.name.startswith((".", "_"))


def listar(pasta_etapa: Path) -> list[Path]:
    """Itens de uma etapa já na ordem certa (P0 primeiro)."""
    if not pasta_etapa.exists():
        return []
    itens = [p for p in pasta_etapa.iterdir() if eh_item(p)]
    return sorted(itens, key=lambda p: chave_ordem(p.name))


def etapa_do_item(item: Path) -> str:
    return Path(item).parent.name


def achar_item(raiz: Path, ref: str) -> Path:
    """Acha o item pelo nome completo, pelo nome sem P0_/P1_/P2_ ou por um
    pedaço único do nome, em qualquer etapa (inclusive 99_erros)."""
    ref = str(ref).strip().rstrip("/\\")
    ref = Path(ref).name if ("/" in ref or "\\" in ref) else ref
    todos = []
    for etapa in TODAS_AS_PASTAS:
        todos.extend(listar(Path(raiz) / etapa))
    exatos = [p for p in todos if p.name == ref]
    if exatos:
        return exatos[0]
    sem_p = [p for p in todos if p.name[3:] == ref]
    if len(sem_p) == 1:
        return sem_p[0]
    parciais = [p for p in todos if ref in p.name]
    if len(parciais) == 1:
        return parciais[0]
    if len(parciais) > 1:
        nomes = ", ".join(p.name for p in parciais[:5])
        raise ItemNaoEncontrado(f"'{ref}' é ambíguo: {nomes}")
    raise ItemNaoEncontrado(f"nenhum item '{ref}' na esteira")


def existe_em_alguma_etapa(raiz: Path, nome_sem_prioridade: str) -> Path | None:
    for etapa in TODAS_AS_PASTAS:
        pasta = Path(raiz) / etapa
        if not pasta.exists():
            continue
        for p in pasta.iterdir():
            if p.is_dir() and p.name[3:] == nome_sem_prioridade:
                return p
            if p.is_dir() and p.name.startswith(nome_sem_prioridade + "__"):
                return p
    return None


# --- histórico e estado ---------------------------------------------------
def historico(item: Path, texto: str) -> None:
    anexar_linha(Path(item) / ARQ_HISTORICO, texto)


def ler_estado(item: Path) -> dict:
    est = ler_json(Path(item) / ARQ_ESTADO, {}) or {}
    est.setdefault("voltas", 0)
    est.setdefault("tentativas", {})
    est.setdefault("revisoes", [])
    return est


def salvar_estado(item: Path, estado: dict) -> None:
    escrever_json(Path(item) / ARQ_ESTADO, estado)


# --- movimento -----------------------------------------------------------
def nome_livre(pasta: Path, nome: str) -> str:
    """Se já existe uma pasta com esse nome (só em 99_erros), usa __2, __3..."""
    if not (pasta / nome).exists():
        return nome
    n = 2
    while (pasta / f"{nome}__{n}").exists():
        n += 1
    return f"{nome}__{n}"


def mover(item: Path, pasta_destino: Path, novo_nome: str | None = None) -> Path:
    """Move a pasta inteira de forma atômica (os.replace) e idempotente.

    - origem sumiu e destino existe  -> já foi movido: devolve o destino;
    - destino já existe com outra pasta -> erro (não sobrescreve nada);
    - arquivo aberto por outro programa (Windows) -> ErroEtapa (tenta depois);
    - unidades diferentes (não deveria acontecer) -> copia para
      .movendo_<nome> no destino, renomeia e só então apaga a origem.
    """
    item = Path(item)
    pasta_destino = Path(pasta_destino)
    destino = pasta_destino / (novo_nome or item.name)
    if not item.exists():
        if destino.exists():
            return destino
        raise FileNotFoundError(f"item sumiu: {item}")
    if destino.exists():
        if destino.resolve() == item.resolve():
            return destino
        raise ErroEtapa(f"já existe {destino.name} em {pasta_destino.name}")
    garantir(pasta_destino)
    try:
        os.replace(item, destino)
    except PermissionError as e:
        raise ErroEtapa(f"não consegui mover {item.name} (arquivo aberto em outro "
                        f"programa?): {e}") from e
    except OSError as e:
        if e.errno != errno.EXDEV:
            raise
        temp = pasta_destino / f".movendo_{destino.name}"
        if temp.exists():
            shutil.rmtree(temp)
        shutil.copytree(item, temp)
        os.replace(temp, destino)
        shutil.rmtree(item, ignore_errors=True)
    return destino


def garantir_estrutura(raiz: Path) -> None:
    for etapa in TODAS_AS_PASTAS:
        garantir(Path(raiz) / etapa)


def indice_etapa(etapa: str) -> int:
    return ETAPAS.index(etapa) if etapa in ETAPAS else len(ETAPAS)
