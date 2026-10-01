"""Adaptador da fila REAL da API (H:\\HypadoLocal\\fila_api\\) — ISOLADO de propósito.

Quem publica é o scripts\\publicador_meta.py, que JÁ EXISTE e NÃO pode ser
reescrito. O formato da fila é o REAL (Seção 4.1 do enunciado da rodada 2) e mora
em `hpbase.fila_api_pc`: este arquivo só traduz o post.json da esteira para
`fila_api_pc.montar_item` (que valida como o publicador valida) e lê a resposta
com `fila_api_pc.ler_confirmacao`. O resto da esteira não sabe nada da fila.

FORMATO REAL — 1 arquivo JSON por post e por rede, <id>.json na raiz da fila:
  {
    "id": "gta_2026-09-30_ig_reel_1830",       canais: <canal>_<data>_<HHMM>_<slug>_<ig|th>_<tipo>
    "conta": "hpgta6",                          handle sem @
    "rede": "instagram",                        só instagram | threads (Facebook fica no Business Suite)
    "tipo": "reel",                             feed | carrossel | reel | story | texto
    "arquivos": ["H:\\\\HypadoLocal\\\\fila_api\\\\midia\\\\<item>\\\\final.mp4"],
    "legenda": "texto do post (com crédito e hashtags)",
    "quando": "2026-09-30 18:30",               hora de Brasília, sem fuso
    "canal": "gta", "grupo_whatsapp": "HP | Comissão 🚀", "titulo": "...", "capa": "..." (reel)
  }
A mídia é copiada para fila_api\\midia\\<item>\\ (config copiar_midia_para_fila),
para o caminho continuar valendo mesmo depois que a pasta do item andar na esteira.

CONFIRMAÇÃO REAL: o publicador move o arquivo para fila_api\\feitos\\ (ganha
"status": "no_ar" e "resultado" {media_id, permalink, publicado_em}) ou para
fila_api\\erros\\ ("erro" de validação/atraso, ou "ultimo_erro" + "tentativas").

Modo real: rede fora de instagram/threads é RECUSADA (ErroPermanente) — o item vai
para 99_erros com a mesma mensagem do publicador. Modo sombra (padrão): grava o
mesmo formato em esteira_sombra\\sombra\\fila_api\\ (o publicador nunca lê) e
confirma na hora com status "sombra"; rede fora da API ganha um "aviso" no
registro em vez de erro — nada vai ao ar.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from hpbase import FUSO, agora_iso, escrever_json, garantir
from hpbase import fila_api_pc as fa

from .erros import ErroPermanente
from .pastas import ler_nome
from .pedido import ler_horario

# tipo da esteira -> tipo da fila (os demais — reel, carrossel, story — têm o mesmo nome)
TIPO_FILA = {"estatico": "feed", "threads_texto": "texto"}


def tipo_fila(post: dict) -> str:
    return TIPO_FILA.get(post["tipo"], post["tipo"])


def quando_fila(horario_alvo):
    """horario_alvo da esteira (ISO com fuso) -> datetime de Brasília sem fuso (o que a fila usa)."""
    return ler_horario(horario_alvo).astimezone(FUSO).replace(tzinfo=None)


def slug_do_post(post: dict) -> str:
    """Slug do nome do item (P1_<data>_<hora>_<canal>_<slug>) ou, sem ele, do título."""
    info = ler_nome(str(post.get("item") or ""))
    return info.slug if info else fa.slug(post.get("titulo") or "post")


def id_fila(post: dict, rede: str) -> str:
    """Id na convenção real: gta_<data>_<ig|th>_<tipo>_<HHMM> ou <canal>_<data>_<HHMM>_<slug>_<ig|th>_<tipo>."""
    return fa.id_padrao(post["canal"], rede, tipo_fila(post), quando_fila(post["horario_alvo"]),
                        slug_=slug_do_post(post))


def montar_registro_fila(post: dict, rede: str, midia: list[str], capa: str | None,
                         pasta_fila=None, existe=None, validar: bool = True) -> dict:
    """ÚNICO lugar que traduz post.json -> item da fila real (fila_api_pc.montar_item).

    Valida com as regras e mensagens do publicador (ErroPermanente se não passa).
    `validar=False` (só o modo sombra, para redes fora da fila) monta sem validar.
    """
    tipo = tipo_fila(post)
    kw = dict(conta=post["conta"], rede=rede, tipo=tipo,
              arquivos=[] if tipo == "texto" else list(midia),   # texto do Threads: arquivos vazio
              legenda=post.get("legenda") or "", quando=quando_fila(post["horario_alvo"]),
              canal=post["canal"], titulo=post.get("titulo"),
              capa=capa if tipo == "reel" else None,               # capa só existe para reel
              id_=id_fila(post, rede))
    if not validar:
        return fa.montar_bruto(**kw)
    try:
        return fa.montar_item(pasta_fila=pasta_fila, existe=existe, **kw)
    except fa.ErroFilaApi as e:
        raise ErroPermanente(f"{rede}: {e}") from None


def ler_confirmacao(id_: str, pasta_fila) -> dict | None:
    """ÚNICO lugar que lê a resposta do publicador (feitos\\ e erros\\ via fila_api_pc).
    None = ainda não (na raiz, em story_clicavel\\, reserva_largada\\ ou sumiu)."""
    c = fa.ler_confirmacao(id_, pasta_fila)
    if c["estado"] == "no_ar":
        return {"status": "publicado", "link": c["link"], "em": c["publicado_em"] or agora_iso(),
                "media_id": c["media_id"], "fonte": "fila_api/feitos"}
    if c["estado"] == "erro":
        return {"status": "erro", "mensagem": str(c["erro"]), "fonte": f"fila_api/{c['pasta']}"}
    return None


class AgendadorFilaApi:
    def __init__(self, cfg, forcar_sombra: bool = False, existe=None):
        self.cfg = cfg
        self.sombra = forcar_sombra or not cfg.real
        self.existe = existe  # função injetável "arquivo existe?" (padrão Path.exists)

    @property
    def pasta(self) -> Path:
        return self.cfg.pasta_sombra / "fila_api" if self.sombra else Path(self.cfg.fila_api)

    def _midia(self, item: Path, post: dict) -> tuple[list[str], str | None]:
        item = Path(item).resolve()
        arquivos = [item / a for a in post["arquivos"]]
        capa = item / post["capa"] if post.get("capa") else None
        if not self.cfg.copiar_midia_para_fila:
            return [str(a) for a in arquivos], (str(capa) if capa else None)
        destino = garantir(self.pasta / "midia" / post["item"])

        def copiar(src: Path) -> str:
            dst = destino / src.name
            if not dst.exists() or dst.stat().st_size != src.stat().st_size:
                tmp = destino / f"_tmp_{src.name}"
                shutil.copy2(src, tmp)
                os.replace(tmp, dst)
            return str(dst)
        return [copiar(a) for a in arquivos], (copiar(capa) if capa else None)

    def agendar(self, item: Path, post: dict, rede: str) -> dict:
        pasta = garantir(self.pasta)
        id_ = id_fila(post, rede)
        arq = pasta / f"{id_}.json"
        # idempotente: nunca regrava o que o publicador já pegou — o item pode ter saído da raiz
        # (feitos\, erros\, story_clicavel\, reserva_largada\, removidos\), então olha todas
        if fa.ler_confirmacao(id_, pasta)["estado"] == "desconhecido":
            if rede not in fa.REDES and not self.sombra:
                raise ErroPermanente(f"{rede}: {fa.MSG_REDE}")
            midia, capa = self._midia(item, post)
            if rede in fa.REDES:
                registro = montar_registro_fila(post, rede, midia, capa, pasta_fila=pasta,
                                                existe=self.existe)
            else:  # sombra: registra o que iria, sem validar como item da API
                registro = montar_registro_fila(post, rede, midia, capa, validar=False)
                registro["aviso"] = f"{fa.MSG_REDE}; gravado só na sombra"
            escrever_json(arq, registro)
        return {"arquivo_fila": str(arq), "id_fila": id_,
                "modo": "sombra" if self.sombra else "real", "em": agora_iso()}

    def conferir(self, item: Path, post: dict, rede: str, registro: dict) -> dict | None:
        if self.sombra or registro.get("modo") == "sombra":
            return {"status": "sombra", "link": None, "em": agora_iso(),
                    "fonte": "modo sombra (nada foi publicado)"}
        arq = Path(registro["arquivo_fila"])
        return ler_confirmacao(registro.get("id_fila") or arq.stem, arq.parent)
