"""Lâminas (carrossel/estáticos): quantidade, ordem e conteúdo.

As duas pastas são lidas em ordem natural do nome ("lamina_2" antes de
"lamina_10"). Cada lâmina do app é comparada com cada lâmina da
referência (SSIM); o casamento ótimo (algoritmo húngaro, feito à mão)
mostra se a ordem foi trocada e quais lâminas faltam ou sobram.
"""
from __future__ import annotations

import re
from pathlib import Path

from .limites import nota_por_pontos
from .midia import EXT_IMAGEM, dimensoes_imagem, ler_imagem_cinza, tamanho_reduzido
from .ssim import ssim
from .util import br, metrica, nao_se_aplica


def chave_natural(nome: str) -> list:
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", nome)]


def listar_laminas(pasta) -> list[Path]:
    p = Path(pasta)
    if not p.is_dir():
        raise FileNotFoundError(f"pasta não encontrada: {p}")
    arquivos = [f for f in p.iterdir() if f.is_file() and f.suffix.lower() in EXT_IMAGEM
                and not f.name.startswith(".")]
    return sorted(arquivos, key=lambda f: chave_natural(f.name))


def _hungaro(custo: list[list[float]]) -> list[tuple[int, int]]:
    """Designação de menor custo total para matriz n x m com n <= m.

    Versão clássica O(n²·m) com potenciais (Kuhn-Munkres). Devolve pares
    (linha, coluna); toda linha recebe uma coluna.
    """
    n, m = len(custo), len(custo[0])
    inf = float("inf")
    u = [0.0] * (n + 1)
    v = [0.0] * (m + 1)
    p = [0] * (m + 1)       # p[j] = linha casada com a coluna j (1-based)
    caminho = [0] * (m + 1)
    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = [inf] * (m + 1)
        usado = [False] * (m + 1)
        while True:
            usado[j0] = True
            i0, delta, j1 = p[j0], inf, 0
            for j in range(1, m + 1):
                if not usado[j]:
                    cur = custo[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j], caminho[j] = cur, j0
                    if minv[j] < delta:
                        delta, j1 = minv[j], j
            for j in range(m + 1):
                if usado[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = caminho[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break
    return sorted((p[j] - 1, j - 1) for j in range(1, m + 1) if p[j] != 0)


def casamento_otimo(similaridade: list[list[float]]) -> list[tuple[int, int]]:
    """Pares (i_app, j_ref) que maximizam a soma das similaridades.

    Aceita matriz retangular: sobra lâmina do lado maior.
    """
    n = len(similaridade)
    m = len(similaridade[0]) if n else 0
    if n == 0 or m == 0:
        return []
    if n <= m:
        return _hungaro([[1.0 - s for s in linha] for linha in similaridade])
    transposta = [[1.0 - similaridade[i][j] for i in range(n)] for j in range(m)]
    return sorted((i, j) for j, i in _hungaro(transposta))


def comparar_pastas(pasta_app, pasta_ref, lim: dict) -> tuple[dict, dict]:
    """Devolve (métrica 'laminas', métrica 'formato') para duas pastas."""
    cfg = lim["laminas"]
    app = listar_laminas(pasta_app)
    ref = listar_laminas(pasta_ref)
    if not app and not ref:
        return (nao_se_aplica("laminas", "as duas pastas estão sem imagem"),
                nao_se_aplica("formato", "sem imagem"))
    if not ref or not app:
        quem = "app" if not app else "referência"
        m = metrica("laminas", {"quantidade": 0.0},
                    {"quantidade_app": len(app), "quantidade_ref": len(ref)},
                    f"pasta do {quem} sem imagem", nota_forcada=0.0)
        return m, nao_se_aplica("formato", "sem par para comparar")

    dims_app = [dimensoes_imagem(f) for f in app]
    dims_ref = [dimensoes_imagem(f) for f in ref]
    w, h = tamanho_reduzido(*dims_ref[0], lado_max=int(cfg["lado_max"]))
    img_app = [ler_imagem_cinza(f, w, h) for f in app]
    img_ref = [ler_imagem_cinza(f, w, h) for f in ref]
    janela, sigma = int(lim["ssim"]["janela"]), float(lim["ssim"]["sigma"])
    matriz = [[ssim(a, r, janela, sigma) for r in img_ref] for a in img_app]

    pares = casamento_otimo(matriz)
    # Lâminas do mesmo carrossel usam o mesmo modelo (fundo, logo): duas
    # lâminas DIFERENTES já se parecem. O limiar para "é a mesma lâmina" fica
    # acima da maior semelhança entre lâminas diferentes da própria referência.
    limiar = float(cfg["limiar_par"])
    entre_ref = [ssim(img_ref[a], img_ref[b], janela, sigma)
                 for a in range(len(img_ref)) for b in range(a + 1, len(img_ref))]
    if entre_ref:
        limiar = max(limiar, min(float(cfg["limiar_teto"]),
                                 max(entre_ref) + float(cfg["margem_modelo"])))
    validos = [(i, j) for i, j in pares if matriz[i][j] >= limiar]
    fracos = [(i, j) for i, j in pares if matriz[i][j] < limiar]
    casados_app = {i for i, _ in validos}
    casados_ref = {j for _, j in validos}
    faltando = [ref[j].name for j in range(len(ref)) if j not in casados_ref]
    sobrando = [app[i].name for i in range(len(app)) if i not in casados_app]

    # ordem: posição relativa no app x posição relativa na referência
    por_app = sorted(validos)
    por_ref = sorted(validos, key=lambda p: p[1])
    rank_ref = {par: k for k, par in enumerate(por_ref)}
    fora = [{"posicao_app": i + 1, "arquivo_app": app[i].name,
             "posicao_ref": j + 1, "arquivo_ref": ref[j].name}
            for k, (i, j) in enumerate(por_app) if rank_ref[(i, j)] != k]
    ordem_ok = not fora

    valores = [matriz[i][j] for i, j in pares] or [0.0]
    media = sum(valores) / len(valores)
    minimo = min(valores)
    cfg_s = lim["ssim"]
    sub = {"quantidade": nota_por_pontos(abs(len(app) - len(ref)), cfg["pontos_quantidade"]),
           "ordem": 10.0 if ordem_ok else float(cfg["nota_ordem_trocada"]),
           "ssim_media": nota_por_pontos(media, cfg_s["pontos_media"]),
           "ssim_minimo": nota_por_pontos(minimo, cfg_s["pontos_minimo"])}
    if faltando or sobrando:
        sub["faltando_sobrando"] = nota_por_pontos(max(len(faltando), len(sobrando)),
                                                   cfg["pontos_quantidade"])
    detalhes = {
        "quantidade_app": len(app), "quantidade_ref": len(ref),
        "tamanho_comparado": f"{w}x{h}",
        "limiar_mesma_lamina": round(limiar, 4),
        "semelhanca_max_entre_laminas_ref": round(max(entre_ref), 4) if entre_ref else None,
        "ordem_correta": ordem_ok,
        "fora_de_ordem": fora,
        "faltando_no_app": faltando,
        "sobrando_no_app": sobrando,
        "pares_fracos": [{"arquivo_app": app[i].name, "arquivo_ref": ref[j].name,
                          "ssim": round(matriz[i][j], 4)} for i, j in fracos],
        "ssim_media": round(media, 4), "ssim_minimo": round(minimo, 4),
        "casamento": [{"posicao_app": i + 1, "arquivo_app": app[i].name,
                       "posicao_ref": j + 1, "arquivo_ref": ref[j].name,
                       "ssim": round(matriz[i][j], 4)} for i, j in pares],
        "pares_por_nome": [{"posicao": k + 1, "arquivo_app": app[k].name,
                            "arquivo_ref": ref[k].name, "ssim": round(matriz[k][k], 4)}
                           for k in range(min(len(app), len(ref)))],
    }
    partes = [f"{len(app)} x {len(ref)} lâminas", f"SSIM médio {br(media, 3)}"]
    if not ordem_ok:
        partes.append("ORDEM TROCADA: " + ", ".join(
            f"pos. {d['posicao_app']} do app = lâmina {d['posicao_ref']} da ref" for d in fora))
    if faltando:
        partes.append("faltando: " + ", ".join(faltando))
    if sobrando:
        partes.append("sobrando: " + ", ".join(sobrando))
    m_laminas = metrica("laminas", sub, detalhes, "; ".join(partes))

    diferentes = [{"arquivo_app": app[i].name, "arquivo_ref": ref[j].name,
                   "app": f"{dims_app[i][0]}x{dims_app[i][1]}",
                   "ref": f"{dims_ref[j][0]}x{dims_ref[j][1]}"}
                  for i, j in pares if tuple(dims_app[i]) != tuple(dims_ref[j])]
    nota_fmt = float(lim["formato"]["nota_resolucao_diferente"]) if diferentes else 10.0
    m_formato = metrica("formato", {"resolucao": nota_fmt},
                        {"resolucoes_diferentes": diferentes},
                        "resoluções iguais" if not diferentes
                        else f"{len(diferentes)} lâmina(s) com resolução diferente")
    return m_laminas, m_formato
