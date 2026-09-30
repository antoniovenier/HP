"""Regra do Revisor de qualidade (manual 09) — funções puras.

aprovado.json / refazer.json (gravados pelo Claude/revisor na pasta do item):
{
  "notas": {"assunto": 9, "fonte_credito": 10, "gancho": 8, "legenda": 7, ...},
  "media": 8.5,              (opcional: o app recalcula sempre a partir das notas)
  "veredito": "Bom",         (opcional: idem)
  "motivo": "texto curto",
  "etapa_destino": "04_edicao",  (opcional, só no refazer)
  "ajustes": {"capa_tempo": 3.0},  (opcional: mesclado no pedido.json antes de refazer)
  "revisor": "Claude"
}
Faixas: média >= 9 Excelente, 7-8,9 Bom -> aprovado (06_agendados);
5-6,9 Médio -> volta para a etapa do critério de menor nota (ou etapa_destino);
< 5 Razoável -> volta para 01_pedidos (Curador). Máximo de 2 voltas: na 3ª
reprovação o item vai para 99_erros com o motivo.
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from .constantes import (AGENDADOS, APELIDOS_ETAPA, BAIXADOS, EDICAO, ETAPAS,
                         FAIXAS, LEGENDA, PEDIDOS, VEREDITOS_APROVADOS)
from .erros import ErroEsteira

ETAPAS_DE_VOLTA = (PEDIDOS, BAIXADOS, LEGENDA, EDICAO)


class RevisaoInvalida(ErroEsteira, ValueError):
    """aprovado.json / refazer.json fora do esquema."""


def _arred(v: float, casas: str) -> float:
    return float(Decimal(str(v)).quantize(Decimal(casas), rounding=ROUND_HALF_UP))


def validar_notas(notas) -> dict[str, float]:
    if not isinstance(notas, dict) or not notas:
        raise RevisaoInvalida("notas tem que ser um objeto {criterio: nota de 0 a 10}")
    saida = {}
    for k, v in notas.items():
        if isinstance(v, bool):
            raise RevisaoInvalida(f"nota de '{k}' tem que ser número de 0 a 10")
        try:
            n = float(str(v).replace(",", "."))
        except (TypeError, ValueError):
            raise RevisaoInvalida(f"nota de '{k}' tem que ser número de 0 a 10") from None
        if not 0 <= n <= 10:
            raise RevisaoInvalida(f"nota de '{k}' fora de 0 a 10: {v}")
        saida[str(k).strip().lower()] = n
    return saida


def calcular_media(notas: dict[str, float]) -> float:
    return _arred(sum(notas.values()) / len(notas), "0.01")


def veredito_da_media(media: float) -> str:
    m = _arred(media, "0.1")
    for minimo, nome in FAIXAS:
        if m >= minimo:
            return nome
    return FAIXAS[-1][1]


def normalizar_etapa(valor) -> str | None:
    if not valor:
        return None
    v = str(valor).strip().lower()
    if v in ETAPAS:
        return v
    return APELIDOS_ETAPA.get(v)


def etapa_da_menor_nota(notas: dict[str, float], mapa: dict,
                        padrao: str = EDICAO) -> tuple[str, str]:
    """(critério de menor nota, etapa). Empate: a etapa mais para trás."""
    menor = min(notas.values())
    empatados = [c for c, n in notas.items() if n == menor]
    melhor = min(empatados, key=lambda c: ETAPAS.index(mapa.get(c, padrao)))
    return melhor, mapa.get(melhor, padrao)


def decidir(dados: dict, tipo: str, voltas: int, max_voltas: int, mapa: dict,
            estatico: bool = False) -> dict:
    """tipo: 'aprovado' ou 'refazer'. Devolve a decisão:
    {"acao": "aprovar"|"voltar"|"erro", "destino", "media", "veredito",
     "criterio_menor", "notas", "motivo", "observacoes": [...]}"""
    if not isinstance(dados, dict):
        raise RevisaoInvalida("o arquivo tem que ser um objeto JSON")
    obs: list[str] = []
    motivo = str(dados.get("motivo") or "").strip()
    notas = validar_notas(dados["notas"]) if dados.get("notas") not in (None, {}) else None
    if notas is None and tipo == "aprovado":
        raise RevisaoInvalida("aprovado.json precisa das notas por critério (0 a 10)")
    media = calcular_media(notas) if notas else None
    veredito = veredito_da_media(media) if notas else None
    if notas and dados.get("media") is not None:
        try:
            if abs(float(dados["media"]) - media) > 0.05:
                obs.append(f"média informada {dados['media']} recalculada para {media}")
        except (TypeError, ValueError):
            obs.append("média informada inválida; recalculada")
    criterio_menor = None
    if notas:
        criterio_menor, _ = etapa_da_menor_nota(notas, mapa)
        desconhecidos = [c for c in notas if c not in mapa]
        if desconhecidos:
            obs.append(f"critério(s) fora do mapa ({', '.join(desconhecidos)}) "
                       f"contam como {EDICAO}")

    base = {"media": media, "veredito": veredito, "notas": notas,
            "criterio_menor": criterio_menor, "motivo": motivo, "observacoes": obs}

    if tipo == "aprovado" and veredito in VEREDITOS_APROVADOS:
        return {**base, "acao": "aprovar", "destino": AGENDADOS}
    if tipo == "aprovado":
        obs.append(f"aprovado.json com média {media} ({veredito}): pela regra das "
                   f"faixas não passa, vale como refazer")

    # --- volta -------------------------------------------------------------
    pedida = normalizar_etapa(dados.get("etapa_destino"))
    if dados.get("etapa_destino") and pedida not in ETAPAS_DE_VOLTA:
        obs.append(f"etapa_destino '{dados.get('etapa_destino')}' inválida; ignorada")
        pedida = None
    if veredito == "Razoável":
        destino = PEDIDOS
    elif pedida:
        destino = pedida
    elif notas:
        destino = etapa_da_menor_nota(notas, mapa)[1]
    else:
        destino = PEDIDOS  # refazer sem notas e sem etapa: o Curador decide
    if estatico and destino in (BAIXADOS, LEGENDA):
        destino = EDICAO
    if not motivo:
        motivo = (f"menor nota: {criterio_menor}" if criterio_menor else "refazer")
        base["motivo"] = motivo
    if voltas >= max_voltas:
        return {**base, "acao": "erro", "destino": None,
                "motivo": f"limite de {max_voltas} voltas atingido (reprovado "
                          f"{voltas + 1}x): {motivo}"}
    return {**base, "acao": "voltar", "destino": destino}
