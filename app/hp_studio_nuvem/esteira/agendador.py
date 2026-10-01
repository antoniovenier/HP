"""Adaptador da fila da API (H:\\HypadoLocal\\fila_api\\) — ISOLADO de propósito.

Quem publica é o scripts\\publicador_meta.py, que JÁ EXISTE e NÃO pode ser
reescrito. O formato exato da fila dele não estava disponível na nuvem, então
o formato abaixo é SUPOSTO. Para casar com o formato real, mude só as duas
funções `montar_registro_fila` e `ler_confirmacao` (o resto da esteira não
sabe nada da fila).

FORMATO SUPOSTO — 1 arquivo JSON por post e por rede:
  fila_api\\<item>__<rede>.json
  {
    "id": "P1_2026-09-30_1830_gta_rockstar-quinta__instagram",
    "origem": "hp_studio.esteira",
    "rede": "instagram",              instagram | threads | facebook | youtube
    "conta": "@hpgta6",
    "canal": "gta",
    "tipo": "reel",                   reel | carrossel | story | estatico | threads_texto
    "midia": ["H:\\\\HypadoLocal\\\\fila_api\\\\midia\\\\<item>\\\\final.mp4"],
    "capa": "H:\\\\...\\\\capa.jpg" ou null,
    "legenda": "texto do post (com crédito e hashtags)",
    "titulo": "...",
    "agendar_para": "2026-09-30T18:30-03:00",
    "status": "pendente",
    "criado_em": "2026-09-30T15:02:11-03:00"
  }
A mídia é copiada para fila_api\\midia\\<item>\\ (config copiar_midia_para_fila),
para o caminho continuar valendo mesmo depois que a pasta do item andar na
esteira.

CONFIRMAÇÃO SUPOSTA: o publicador_meta.py muda "status" para "publicado"
(ou "agendado"/"ok"/"feito") e grava "permalink"/"link"/"url" no mesmo
arquivo, OU move o arquivo para fila_api\\feitos\\ (ou publicados\\,
enviados\\, ok\\). "status": "erro"/"falhou" = falha definitiva.

Modo sombra (padrão): grava em esteira\\sombra\\fila_api\\ (o publicador nunca
lê) e confirma na hora com status "sombra" — nada vai ao ar.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from hpbase import agora_iso, escrever_json, garantir, ler_json

STATUS_OK = ("publicado", "agendado", "ok", "feito", "postado", "sucesso", "publicada")
STATUS_FALHA = ("erro", "falhou", "falha", "cancelado")
SUBPASTAS_FEITOS = ("feitos", "publicados", "enviados", "ok")


def id_fila(post: dict, rede: str) -> str:
    return f"{post['item']}__{rede}"


def montar_registro_fila(post: dict, rede: str, midia: list[str],
                         capa: str | None) -> dict:
    """ÚNICO lugar que conhece o formato da fila do publicador_meta.py."""
    return {
        "id": id_fila(post, rede),
        "origem": "hp_studio.esteira",
        "rede": rede,
        "conta": post["conta"],
        "canal": post["canal"],
        "tipo": post["tipo"],
        "midia": midia,
        "capa": capa,
        "legenda": post["legenda"],
        "titulo": post["titulo"],
        "agendar_para": post["horario_alvo"],
        "status": "pendente",
        "criado_em": agora_iso(),
    }


def ler_confirmacao(dados: dict) -> dict | None:
    """ÚNICO lugar que sabe ler a resposta do publicador. None = ainda não."""
    if not isinstance(dados, dict):
        return None
    st = str(dados.get("status") or "").strip().lower()
    if st in STATUS_OK:
        return {"status": st,
                "link": dados.get("permalink") or dados.get("link") or dados.get("url"),
                "em": dados.get("publicado_em") or dados.get("atualizado_em") or agora_iso(),
                "fonte": "fila_api"}
    if st in STATUS_FALHA:
        return {"status": "erro", "mensagem": str(dados.get("erro") or dados.get("mensagem")
                                                  or "publicador marcou erro"),
                "fonte": "fila_api"}
    return None


class AgendadorFilaApi:
    def __init__(self, cfg, forcar_sombra: bool = False):
        self.cfg = cfg
        self.sombra = forcar_sombra or not cfg.real

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
        arq = pasta / f"{id_fila(post, rede)}.json"
        if not arq.exists():  # idempotente: nunca regrava o que o publicador já pegou
            midia, capa = self._midia(item, post)
            escrever_json(arq, montar_registro_fila(post, rede, midia, capa))
        return {"arquivo_fila": str(arq), "id_fila": id_fila(post, rede),
                "modo": "sombra" if self.sombra else "real", "em": agora_iso()}

    def conferir(self, item: Path, post: dict, rede: str, registro: dict) -> dict | None:
        if self.sombra or registro.get("modo") == "sombra":
            return {"status": "sombra", "link": None, "em": agora_iso(),
                    "fonte": "modo sombra (nada foi publicado)"}
        arq = Path(registro["arquivo_fila"])
        for c in [arq] + [arq.parent / sub / arq.name for sub in SUBPASTAS_FEITOS]:
            d = ler_json(c, None)
            if d is None:
                continue
            conf = ler_confirmacao(d)
            if conf is None and c != arq:
                conf = {"status": "publicado", "link": d.get("permalink") or d.get("link"),
                        "em": agora_iso(), "fonte": f"fila_api/{c.parent.name}"}
            if conf:
                return conf
        return None
