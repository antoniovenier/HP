"""Validação DURA de cada mensagem da fila, antes de qualquer envio.

Regras (do CLAUDE.md da empresa):
- o texto começa EXATAMENTE com "*Claude - *" (nada antes, nem espaço);
- o tipo é um dos 3 permitidos: resumo_dia, no_ar, resumo_sabado;
- o grupo é "HP | Comissão 🚀" ou está na lista "HP | Grupos"
  (grupos_permitidos.json); nunca contato individual;
- anexos existem de verdade.
Qualquer falha → a mensagem vai para rejeitadas\\ com o motivo.
"""
from __future__ import annotations

import re
from pathlib import Path

from hpbase import raiz_local

from .config import (LIMITE_TEXTO, MAX_ANEXOS, PREFIXO, TIPOS_PERMITIDOS, nfc)

# "+55 11 91234-5678", "5511912345678" etc. = cara de contato individual
_RX_TELEFONE = re.compile(r"^\+?[\d\s().\-]{8,}$")


def parece_telefone(nome: str) -> bool:
    return bool(_RX_TELEFONE.match(nfc(nome)))


def grupo_permitido(grupo: str, permitidos: list[str]) -> bool:
    alvo = nfc(grupo)
    return bool(alvo) and alvo in {nfc(g) for g in permitidos}


def resolver_anexo(caminho: str) -> Path:
    """Caminho absoluto fica como está; relativo é relativo a H:\\HypadoLocal."""
    p = Path(caminho)
    return p if p.is_absolute() else raiz_local() / p


def validar_mensagem(dados, permitidos: list[str]) -> list[str]:
    """Devolve a lista de motivos de rejeição (vazia = pode enviar)."""
    if not isinstance(dados, dict):
        return ["o arquivo não é um objeto JSON {…}"]
    motivos: list[str] = []

    tipo = dados.get("tipo")
    if tipo not in TIPOS_PERMITIDOS:
        motivos.append(f"tipo '{tipo}' não permitido (WhatsApp só para: "
                       f"{', '.join(TIPOS_PERMITIDOS)})")

    grupo = dados.get("grupo")
    if not isinstance(grupo, str) or not nfc(grupo):
        motivos.append("sem grupo")
    elif parece_telefone(grupo):
        motivos.append("destino parece contato individual (telefone); só grupos")
    elif not grupo_permitido(grupo, permitidos):
        motivos.append(f"grupo '{nfc(grupo)}' fora da lista permitida "
                       "(HP | Comissão 🚀 + grupos_permitidos.json)")

    texto = dados.get("texto")
    if not isinstance(texto, str):
        motivos.append("sem texto")
    else:
        if not texto.startswith(PREFIXO):
            motivos.append(f"texto não começa exatamente com '{PREFIXO}'")
        elif not texto[len(PREFIXO):].strip():
            motivos.append("texto vazio depois do cabeçalho")
        if len(texto) > LIMITE_TEXTO:
            motivos.append(f"texto grande demais ({len(texto)} > {LIMITE_TEXTO} caracteres)")

    anexos = dados.get("anexos", [])
    if anexos is None:
        anexos = []
    if not isinstance(anexos, list) or not all(isinstance(a, str) for a in anexos):
        motivos.append("anexos precisa ser uma lista de caminhos")
    else:
        if len(anexos) > MAX_ANEXOS:
            motivos.append(f"anexos demais ({len(anexos)} > {MAX_ANEXOS})")
        for a in anexos:
            if not resolver_anexo(a).is_file():
                motivos.append(f"anexo não encontrado: {Path(a).name}")

    ident = dados.get("id")
    if ident is not None and (not isinstance(ident, str) or not ident.strip()):
        motivos.append("id inválido")
    return motivos
