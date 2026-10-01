"""Fila local do WhatsApp: H:\\HypadoLocal\\whatsapp_fila\\ (1 JSON por mensagem).

Formato de cada arquivo (quem produz grava de forma atômica, ex. com
hpbase.escrever_json — arquivo temporário e troca de nome):
    {
      "id": "no_ar_ab12cd34ef56_1a2b3c",
      "grupo": "HP | Comissão 🚀",
      "texto": "*Claude - * ...",
      "anexos": ["H:\\\\HypadoLocal\\\\...\\\\capa.jpg"],
      "tipo": "no_ar",                 # resumo_dia | no_ar | resumo_sabado
      "criado_em": "2026-09-30T18:31:00-03:00"
    }
Destinos:
    rejeitadas\\  inválida (o motivo vai dentro do JSON: motivo_rejeicao)
    enviadas\\    enviada (enviado_em = horário)
    erros\\       falhou 3 vezes (historico com cada erro)
    ..\\whatsapp_sombra\\app\\  modo sombra: o que o app TERIA mandado
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from hpbase import agora_iso, escrever_json, garantir

from .config import pasta_fila, pasta_sombra_app


def nome_seguro(ident: str) -> str:
    """Id → nome de arquivo válido no Windows."""
    s = re.sub(r"[^\w.\-]+", "_", str(ident)).strip("._")
    return (s or "mensagem")[:120]


@dataclass
class ItemFila:
    caminho: Path
    dados: object            # dict quando o JSON leu; None quando quebrado
    erro_leitura: str | None = None

    @property
    def id(self) -> str:
        if isinstance(self.dados, dict):
            i = self.dados.get("id")
            if isinstance(i, str) and i.strip():
                return i.strip()
        return self.caminho.stem

    @property
    def ordem(self) -> float:
        if isinstance(self.dados, dict) and self.dados.get("criado_em"):
            try:
                return datetime.fromisoformat(str(self.dados["criado_em"])).timestamp()
            except (ValueError, TypeError):
                pass
        try:
            return self.caminho.stat().st_mtime
        except OSError:
            return 0.0


class Fila:
    def __init__(self, raiz: Path | None = None, pasta_sombra: Path | None = None):
        self.raiz = Path(raiz) if raiz else pasta_fila()
        self.rejeitadas = self.raiz / "rejeitadas"
        self.enviadas = self.raiz / "enviadas"
        self.erros = self.raiz / "erros"
        self.sombra = Path(pasta_sombra) if pasta_sombra else pasta_sombra_app()

    def preparar(self) -> None:
        for p in (self.raiz, self.rejeitadas, self.enviadas, self.erros):
            garantir(p)

    # ---------------------------------------------------------- leitura
    @staticmethod
    def _carregar(p: Path) -> ItemFila:
        try:
            return ItemFila(p, json.loads(p.read_text(encoding="utf-8-sig")))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            return ItemFila(p, None, f"JSON inválido ({type(e).__name__})")
        except OSError as e:
            return ItemFila(p, None, f"não consegui ler ({type(e).__name__})")

    def pendentes(self) -> list[ItemFila]:
        if not self.raiz.exists():
            return []
        itens = [self._carregar(p) for p in self.raiz.glob("*.json")
                 if p.is_file() and not p.name.startswith((".", "_"))]
        itens.sort(key=lambda i: (i.ordem, i.caminho.name))
        return itens

    def _contar(self, pasta: Path) -> int:
        if not pasta.exists():
            return 0
        return sum(1 for p in pasta.glob("*.json")
                   if not p.name.endswith(".motivo.json") and not p.name.startswith("."))

    def contar(self) -> dict:
        return {"pendentes": len(self.pendentes()) if self.raiz.exists() else 0,
                "enviadas": self._contar(self.enviadas),
                "rejeitadas": self._contar(self.rejeitadas),
                "erros": self._contar(self.erros),
                "sombra": self._contar(self.sombra)}

    def ja_processada(self, ident: str) -> bool:
        """Já foi enviada (ou já passou pela sombra) com este id?"""
        nome = f"{nome_seguro(ident)}.json"
        return any((p / nome).exists() for p in (self.enviadas, self.sombra))

    def ja_existe(self, ident: str) -> bool:
        """Id já está em qualquer lugar (para não enfileirar de novo)."""
        nome = f"{nome_seguro(ident)}.json"
        return any((p / nome).exists() for p in
                   (self.raiz, self.enviadas, self.erros, self.rejeitadas, self.sombra))

    # ---------------------------------------------------------- escrita
    def enfileirar(self, dados: dict) -> Path:
        if not dados.get("id"):
            raise ValueError("mensagem sem id")
        garantir(self.raiz)
        return escrever_json(self.raiz / f"{nome_seguro(dados['id'])}.json", dados)

    @staticmethod
    def _destino(pasta: Path, nome: str) -> Path:
        dst = pasta / nome
        n = 2
        while dst.exists():
            dst = pasta / f"{Path(nome).stem}__{n}.json"
            n += 1
        return dst

    def mover(self, item: ItemFila, pasta: Path, extra: dict | None = None,
              nome: str | None = None) -> Path:
        garantir(pasta)
        dst = self._destino(pasta, nome or item.caminho.name)
        if isinstance(item.dados, dict):
            novo = dict(item.dados)
            novo.update(extra or {})
            escrever_json(dst, novo)
            try:
                item.caminho.unlink()
            except FileNotFoundError:
                pass
            item.dados = novo
        else:  # JSON quebrado: move o arquivo como está + motivo ao lado
            os.replace(item.caminho, dst)
            if extra:
                escrever_json(dst.with_name(dst.stem + ".motivo.json"), extra)
        item.caminho = dst
        return dst

    def rejeitar(self, item: ItemFila, motivo: str, quando: str | None = None) -> Path:
        return self.mover(item, self.rejeitadas,
                          {"motivo_rejeicao": motivo, "rejeitada_em": quando or agora_iso()})

    def marcar_enviada(self, item: ItemFila, quando: str, obs: str | None = None) -> Path:
        dados = item.dados if isinstance(item.dados, dict) else {}
        extra = {"enviado_em": quando,
                 "tentativas": int(dados.get("tentativas", 0) or 0) + 1}
        if obs:
            extra["obs"] = obs
        return self.mover(item, self.enviadas, extra, nome=f"{nome_seguro(item.id)}.json")

    def para_sombra(self, item: ItemFila, quando: str) -> Path:
        return self.mover(item, self.sombra, {"sombra_em": quando},
                          nome=f"{nome_seguro(item.id)}.json")

    def registrar_falha(self, item: ItemFila, motivo: str, max_tentativas: int,
                        quando: str | None = None) -> bool:
        """Conta 1 tentativa. Devolve True se a mensagem foi para erros\\."""
        quando = quando or agora_iso()
        dados = dict(item.dados) if isinstance(item.dados, dict) else {}
        n = int(dados.get("tentativas", 0) or 0) + 1
        hist = list(dados.get("historico") or [])
        hist.append({"quando": quando, "erro": motivo})
        dados.update({"tentativas": n, "ultimo_erro": motivo, "historico": hist})
        item.dados = dados
        if n >= max_tentativas:
            self.mover(item, self.erros, {"erro_final": motivo, "erro_em": quando})
            return True
        escrever_json(item.caminho, dados)
        return False
