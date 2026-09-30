"""Gancho para o motor do HP Studio: `executar(trabalho) -> dict`.

Exemplo de trabalho (vem da fila do motor):
    {"tipo": "video", "app": "...\\\\app.mp4", "ref": "...\\\\ref.mp4",
     "tarefa": "editor_reel", "id": "post123",
     "legenda_app": "...srt", "legenda_ref": "...srt"}
tipo: video | imagem | laminas | legenda. Sem "tarefa" só gera o relatório
(em paridade\\_avulsos). Nunca levanta exceção: devolve ok=False e, se o
PC estiver ocupado ou no horário proibido, adiar=True (o motor tenta depois).
"""
from __future__ import annotations

from datetime import datetime

from hpbase import TravaOcupada, agora, obter_logger

from . import comparar, relatorio, sombra
from .limites import carregar_limites
from .midia import ErroMidia


def comparar_por_tipo(tipo: str, app, ref, limites: dict, legenda_app=None,
                      legenda_ref=None, usar_trava: bool = True,
                      agora_trava: datetime | None = None) -> dict:
    if tipo == "video":
        return comparar.comparar_video(app, ref, legenda_app, legenda_ref, limites,
                                       usar_trava=usar_trava, agora=agora_trava)
    if tipo == "imagem":
        return comparar.comparar_imagem(app, ref, limites)
    if tipo == "laminas":
        return comparar.comparar_laminas(app, ref, limites)
    if tipo == "legenda":
        return comparar.comparar_legenda(app, ref, limites)
    raise ValueError(f"tipo desconhecido: {tipo} (use video, imagem, laminas ou legenda)")


def salvar_resultado(rel: dict, tarefa: str | None, ident: str | None,
                     limites: dict, quando: datetime | None = None, saida=None) -> dict:
    """Com tarefa: registra na sombra. Sem tarefa: grava em _avulsos (ou --saida)."""
    if tarefa:
        return sombra.registrar(tarefa, rel, id=ident, quando=quando, limites=limites)
    quando = quando or agora()
    pasta = saida or (sombra.pasta_paridade() / "_avulsos")
    base = f"{quando.date().isoformat()}_{sombra.nome_seguro(ident or quando.strftime('%H%M%S'))}"
    pj, pm = relatorio.salvar(rel, pasta, base)
    return {"json": pj, "md": pm, "status": None}


def executar(trabalho: dict, usar_trava: bool = True, agora_trava: datetime | None = None) -> dict:
    log = obter_logger("qa_paridade")
    tipo = trabalho.get("tipo", "video")
    try:
        lim = carregar_limites(trabalho.get("limites"))
        rel = comparar_por_tipo(tipo, trabalho["app"], trabalho["ref"], lim,
                                trabalho.get("legenda_app"), trabalho.get("legenda_ref"),
                                usar_trava=usar_trava, agora_trava=agora_trava)
        res = salvar_resultado(rel, trabalho.get("tarefa"), trabalho.get("id"), lim)
    except TravaOcupada as e:
        log.info("adiado: %s", e)
        return {"ok": False, "adiar": True, "erro": str(e)}
    except (KeyError, ValueError, FileNotFoundError, ErroMidia, OSError) as e:
        log.warning("erro no trabalho %s: %s", tipo, e)
        return {"ok": False, "adiar": False, "erro": f"{type(e).__name__}: {e}"}
    return {"ok": True, "adiar": False, "tipo": tipo, "aprovado": rel["aprovado"],
            "veredito": rel["veredito"], "nota_final": rel["nota_final"],
            "json": str(res["json"]), "md": str(res["md"]), "status": res["status"]}
