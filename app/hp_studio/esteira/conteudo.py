"""Conteúdo do post: crédito, legenda do post (caption), post.json e o bruto."""
from __future__ import annotations

from pathlib import Path

from hpbase import agora_iso, escrever_json

from .constantes import ARQ_POST, CONTAS, EXT_VIDEO, NOMES_CANAIS
from .erros import ErroPermanente
from .pedido import RX_MOEDA, fonte_externa

AVISO_VALORES_TEXTO = "Valores aproximados, sujeitos a variação."
LIMITE_LEGENDA = {"threads": 500, "instagram": 2200, "tiktok": 2200,
                  "facebook": 63206, "youtube": 5000, "pinterest": 500}


def texto_credito(pedido: dict) -> str | None:
    """'Vídeo: @clube' no futebol, 'Crédito: @criador' no resto."""
    c = (pedido.get("credito") or "").strip()
    if not c:
        return None
    if ":" in c.split()[0] or c.lower().startswith(("crédito", "credito", "vídeo", "video", "fonte", "foto")):
        return c
    return f"Vídeo: {c}" if pedido.get("canal") == "futebol" else f"Crédito: {c}"


def legenda_do_post(pedido: dict) -> str:
    """Texto que vai junto do post (caption)."""
    if pedido.get("tipo") == "threads_texto":
        return pedido["texto"].strip()
    corpo = (pedido.get("legenda_post") or pedido["titulo"]).strip()
    partes = [corpo]
    cred = texto_credito(pedido) if (fonte_externa(pedido) or pedido.get("credito")) else None
    if cred and cred.lower() not in corpo.lower():
        partes.append(cred)
    tudo = " ".join(partes + [pedido.get("titulo", "")])
    if RX_MOEDA.search(tudo) and "valores aproximados" not in corpo.lower():
        partes.append(AVISO_VALORES_TEXTO)
    tags = [t.strip() for t in pedido.get("hashtags") or [] if t.strip()]
    if tags:
        partes.append(" ".join("#" + t.lstrip("#") for t in tags))
    return "\n\n".join(partes)


def conferir_limites(legenda: str, redes: list[str]) -> None:
    for r in redes:
        lim = LIMITE_LEGENDA.get(r)
        if lim and len(legenda) > lim:
            raise ErroPermanente(f"legenda do post tem {len(legenda)} caracteres; "
                                 f"o limite do {r} é {lim}")


def montar_post(item: Path, pedido: dict, arquivos: list[str],
                capa: str | None = None, **extra) -> dict:
    """Grava post.json (caminhos relativos à pasta do item)."""
    legenda = legenda_do_post(pedido)
    conferir_limites(legenda, pedido["redes"])
    post = {
        "id": pedido["id"],
        "item": Path(item).name,
        "canal": pedido["canal"],
        "nome_canal": NOMES_CANAIS[pedido["canal"]],
        "conta": CONTAS[pedido["canal"]],
        "tipo": pedido["tipo"],
        "prioridade": pedido["prioridade"],
        "redes": list(pedido["redes"]),
        "horario_alvo": pedido["horario_alvo"],
        "titulo": pedido["titulo"],
        "legenda": legenda,
        "credito": texto_credito(pedido),
        "arquivos": list(arquivos),
        "capa": capa,
        "gerado_em": agora_iso(),
    }
    post.update(extra)
    escrever_json(Path(item) / ARQ_POST, post)
    return post


def achar_bruto(item: Path) -> Path | None:
    for p in sorted(Path(item).glob("bruto.*")):
        if p.suffix.lower() in EXT_VIDEO and p.is_file():
            return p
    return None


def janela_corte(pedido: dict, duracao: float | None) -> tuple[float, float]:
    """(início, duração) do trecho usado, a partir de pedido.corte."""
    total = float(duracao or 0)
    corte = pedido.get("corte") or {}
    ini = float(corte.get("inicio", 0) or 0)
    fim = corte.get("fim")
    fim = min(float(fim), total) if fim is not None else total
    if fim - ini < 0.3:
        raise ErroPermanente(f"trecho curto demais (início {ini:.1f}s, fim {fim:.1f}s, "
                             f"vídeo de {total:.1f}s)")
    return ini, round(fim - ini, 3)
