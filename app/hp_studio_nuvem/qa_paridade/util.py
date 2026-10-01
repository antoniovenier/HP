"""Pedaços comuns: formato brasileiro de número e o dicionário de métrica."""
from __future__ import annotations

NOMES = {
    "duracao": "Duração",
    "ssim": "Imagem (SSIM)",
    "loudness": "Áudio (loudness)",
    "legenda": "Legenda",
    "laminas": "Lâminas",
    "formato": "Formato",
}


def br(valor, casas: int = 2) -> str:
    """12.345 -> '12,35' (vírgula decimal, como o Antônio lê)."""
    if valor is None:
        return "-"
    return f"{float(valor):.{casas}f}".replace(".", ",")


def tempo_txt(seg: float | None) -> str:
    """75.25 -> '1:15.25' (minuto:segundo)."""
    if seg is None:
        return "-"
    m, s = divmod(round(float(seg), 2), 60)
    return f"{int(m)}:{s:05.2f}"


def metrica(nome: str, subnotas: dict, detalhes: dict, resumo: str,
            nota_forcada: float | None = None) -> dict:
    """Métrica aplicada: nota = menor subnota (ou a nota forçada)."""
    subnotas = {k: round(float(v), 2) for k, v in subnotas.items()}
    nota = nota_forcada if nota_forcada is not None else min(subnotas.values())
    return {"nome": nome, "aplica": True, "nota": round(float(nota), 2),
            "subnotas": subnotas, "detalhes": detalhes, "resumo": resumo}


def nao_se_aplica(nome: str, motivo: str) -> dict:
    return {"nome": nome, "aplica": False, "nota": None, "subnotas": {},
            "detalhes": {}, "resumo": motivo}
