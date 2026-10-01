"""`status`: foto do enviador sem abrir navegador nem importar o Playwright."""
from __future__ import annotations

import importlib.util

from hpbase import ler_json

from .config import (arquivo_estado, arquivo_grupos, carregar_config,
                     carregar_grupos_permitidos, pasta_perfil,
                     pasta_sombra_relatorios)
from .fila import Fila
from .recebidas import ArquivoRecebidas
from .ritmo import ControleRitmo, Relogio


def playwright_instalado() -> bool:
    # find_spec não importa o pacote (o Playwright nunca carrega no status)
    return importlib.util.find_spec("playwright") is not None


def coletar_status(relogio: Relogio | None = None) -> dict:
    cfg = carregar_config()
    ritmo = ControleRitmo(relogio or Relogio(), cfg.intervalo_min_seg, cfg.max_por_hora)
    estado = ler_json(arquivo_estado(), {}) or {}
    relatorios = sorted(pasta_sombra_relatorios().glob("*.md")) \
        if pasta_sombra_relatorios().exists() else []
    perfil = pasta_perfil()
    return {
        "modo": cfg.modo,
        "fila": Fila().contar(),
        "envios_ultima_hora": len(ritmo.envios_ultima_hora()),
        "max_por_hora": cfg.max_por_hora,
        "intervalo_min_seg": ritmo.intervalo,
        "grupos_permitidos": carregar_grupos_permitidos(),
        "arquivo_grupos_existe": arquivo_grupos().exists(),
        "perfil_existe": perfil.exists() and any(perfil.iterdir()),
        "playwright_instalado": playwright_instalado(),
        "logado": estado.get("logado"),
        "precisa_login": bool(estado.get("precisa_login")),
        "ultimo_ciclo": estado.get("ultimo_ciclo"),
        "ultimo_resultado": estado.get("ultimo_resultado"),
        "ultima_leitura_recebidas": estado.get("ultima_leitura_recebidas"),
        "recebidas_por_dia": ArquivoRecebidas().resumo(),
        "ultimo_relatorio_sombra": str(relatorios[-1]) if relatorios else None,
    }


def texto_status(s: dict) -> str:
    f = s["fila"]
    sim = {True: "sim", False: "não", None: "ainda não sei"}
    linhas = [
        f"Modo: {s['modo']}" + ("  (só monta e compara; não abre o navegador)"
                                if s["modo"] == "sombra" else "  (ENVIA de verdade)"),
        f"Fila: {f['pendentes']} pendentes · {f['enviadas']} enviadas · "
        f"{f['rejeitadas']} rejeitadas · {f['erros']} com erro · {f['sombra']} na sombra",
        f"Ritmo: {s['envios_ultima_hora']} envios na última hora (máx. {s['max_por_hora']}) · "
        f"intervalo mínimo {int(s['intervalo_min_seg'])} s",
        f"Grupos permitidos ({len(s['grupos_permitidos'])}): " + ", ".join(s["grupos_permitidos"]),
        f"Perfil do navegador: {'ok' if s['perfil_existe'] else 'vazio (rode: python -m whatsapp_local login)'}",
        f"Playwright: {'instalado' if s['playwright_instalado'] else 'NÃO instalado (pip install playwright)'}",
        f"Logado no WhatsApp Web: {sim.get(s['logado'], '?')}"
        + ("  → PRECISA LOGIN" if s["precisa_login"] else ""),
        f"Último ciclo: {s['ultimo_ciclo'] or '—'}",
    ]
    r = s.get("ultimo_resultado") or {}
    if r.get("erro"):
        linhas.append(f"Último erro: {r['erro']}")
    rec = s["recebidas_por_dia"]
    if rec:
        ult = sorted(rec)[-1]
        linhas.append(f"Recebidas salvas: {sum(rec.values())} (último dia {ult}: {rec[ult]})")
    if s["ultimo_relatorio_sombra"]:
        linhas.append(f"Último relatório da sombra: {s['ultimo_relatorio_sombra']}")
    return "\n".join(linhas)
