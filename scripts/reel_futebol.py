"""Montador de reels do Futebol | HP (@hp.futebol) — ffmpeg + Pillow.

Saída: 1080x1920, H.264 yuv420p, AAC 48 kHz, 30 fps, -14 LUFS (loudnorm em
2 passadas), render em no máximo 10 min, trabalho pesado 1 por vez
(pesado.lock) e nunca das 18h às 22h30.

Comandos (no PC: python scripts\\reel_futebol.py ...):
  montar roteiro.json [--saida x.mp4] [--simular] [--legenda-auto] [--estilo e.json]
  validar roteiro.json [--legenda-auto]
  exemplos [--destino pasta]
  esquema [modo]

Gancho do motor do HP Studio: executar(trabalho: dict) -> dict.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
import time
from contextlib import nullcontext
from datetime import datetime
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from reel_futebol_arte import carregar_estilo  # noqa: E402
from reel_futebol_base import (MODOS, ErroReel, RoteiroInvalido,  # noqa: E402
                               TravaOcupada, TravaPesada, agora_iso, dur_exata,
                               escrever_json, garantir, log, raiz_local)
from reel_futebol_exemplos import (AVISO_MODELO, gerar_midia_sintetica,  # noqa: E402
                                   roteiro_exemplo, roteiro_modelo)
from reel_futebol_midia import (Orcamento, comandos_simulados, info_midia,  # noqa: E402
                                loudness_arquivo, render_plano)
from reel_futebol_modos import construir_plano  # noqa: E402
from reel_futebol_roteiro import (carregar_roteiro, normalizar,  # noqa: E402
                                  obter_legenda_auto, resolver, validar_roteiro)

MODOS_EXEMPLO = ("gol", "noticia", "debate", "estatistica")
TOLERANCIA_DURACAO = 0.2


def pasta_modelos() -> Path:
    return raiz_local() / "canais" / "futebol" / "modelos_reel"


def _estilo_do_roteiro(r: dict, base: Path, estilo_arq=None) -> dict:
    extra = r.get("estilo") if isinstance(r.get("estilo"), dict) else None
    arq = estilo_arq
    if arq is None and isinstance(r.get("estilo"), str) and r["estilo"].strip():
        arq = resolver(r["estilo"], base)
    return carregar_estilo(arq, extra)


def _saida_padrao(r: dict, caminho_rot: Path | None) -> Path:
    if caminho_rot is not None:
        return caminho_rot.with_suffix(".mp4")
    nome = str(r.get("id") or f"{r.get('modo', 'reel')}_{datetime.now():%Y%m%d_%H%M%S}")
    return raiz_local() / "canais" / "futebol" / "reels" / f"{nome}.mp4"


def _sem_inf(v):
    if isinstance(v, float) and not math.isfinite(v):
        return None
    return v


def validar(roteiro, legenda_auto: bool = False, estilo_arq=None, base=None):
    """(erros, avisos) — lista de erros vazia quer dizer 'pode montar'."""
    r, pasta, _cam = carregar_roteiro(roteiro, base)
    estilo = _estilo_do_roteiro(r, pasta, estilo_arq)
    return validar_roteiro(r, pasta, estilo, legenda_auto or bool(r.get("legenda_auto")))


def montar(roteiro, saida=None, simular: bool = False, legenda_auto: bool = False,
           agora: datetime | None = None, trava: bool = True, estilo_arq=None,
           manter_temp: bool = False, base=None, executor_legenda=None) -> dict:
    """Valida, monta o plano e renderiza (ou só imprime, com simular=True).

    agora/trava existem para os testes (a trava do PC fica em
    HypadoLocal\\app\\pesado.lock e respeita 18h-22h30).
    """
    lg = log()
    r, pasta, caminho_rot = carregar_roteiro(roteiro, base)
    estilo = _estilo_do_roteiro(r, pasta, estilo_arq)
    legenda_auto = legenda_auto or bool(r.get("legenda_auto"))
    erros, avisos = validar_roteiro(r, pasta, estilo, legenda_auto)
    if erros:
        lg.warning("roteiro recusado (%s): %s", caminho_rot or r.get("id"), "; ".join(erros))
        raise RoteiroInvalido(erros, avisos)
    rn = normalizar(r, pasta, estilo)
    cmd_legenda = None
    if rn["modo"] == "gol" and legenda_auto:
        if simular:
            rn["legenda"] = "(legenda automática do posts_futebol.py legenda_video)"
            cmd_legenda = "posts_futebol.py legenda_video <roteiro> (rodaria antes do render)"
        else:
            rn["legenda"] = obter_legenda_auto(caminho_rot, r, estilo, executor_legenda)
    saida = Path(saida or (resolver(r["saida"], pasta) if r.get("saida") else _saida_padrao(r, caminho_rot)))
    plano = construir_plano(rn, estilo, saida)
    dmax = float(estilo.get("duracao_max_s", 90))
    if plano.duracao > dmax + 1e-6:
        raise RoteiroInvalido([f"reel com {plano.duracao:.1f}s passa do máximo de {dmax:.0f}s "
                               "(corte o vídeo com inicio/fim ou use menos fotos)"], avisos)
    if simular:
        pasta_sim = raiz_local() / "app" / "tmp" / "reel_futebol_SIMULADO"
        cmds = comandos_simulados(plano, pasta_sim)
        if cmd_legenda:
            cmds.insert(0, f"# {cmd_legenda}")
        lg.info("simulado %s (%s, %.2fs)", saida.name, plano.modo, plano.duracao)
        return {"ok": True, "simulado": True, "modo": plano.modo, "saida": str(saida),
                "duracao_planejada": round(plano.duracao, 3), "comandos": cmds,
                "segmentos": [{"nome": s.nome, "duracao": round(dur_exata(s.duracao), 3),
                               "descricao": s.descricao} for s in plano.segmentos],
                "avisos": avisos}

    ctx = TravaPesada("reel_futebol", agora=agora) if trava else nullcontext()
    t0 = time.monotonic()
    with ctx:
        orc = Orcamento(float(estilo.get("limite_render_s", 600)))
        garantir(saida.parent)
        tmp_base = garantir(raiz_local() / "app" / "tmp")  # nunca no C:
        if manter_temp:
            pasta_tmp = Path(tempfile.mkdtemp(prefix="reel_futebol_", dir=tmp_base))
            med = render_plano(plano, pasta_tmp, orc)
        else:
            with tempfile.TemporaryDirectory(prefix="reel_futebol_", dir=tmp_base) as tmp:
                med = render_plano(plano, Path(tmp), orc)
    tempo = time.monotonic() - t0
    info = info_midia(saida)
    if (info["largura"], info["altura"]) != (1080, 1920):
        raise ErroReel(f"saída com tamanho errado: {info['largura']}x{info['altura']}")
    if not info["tem_audio"]:
        raise ErroReel("saída sem trilha de áudio")
    if info["duracao"] is not None and abs(info["duracao"] - plano.duracao) > TOLERANCIA_DURACAO:
        avisos.append(f"duração {info['duracao']:.2f}s diferente do planejado {plano.duracao:.2f}s")
    lufs = _sem_inf(loudness_arquivo(saida, estilo))
    rel = {
        "ok": True, "modo": plano.modo, "roteiro": str(caminho_rot) if caminho_rot else None,
        "saida": str(saida), "gerado_em": agora_iso(),
        "duracao_planejada": round(plano.duracao, 3), "duracao_medida": info["duracao"],
        "largura": info["largura"], "altura": info["altura"], "fps": info["fps"],
        "codec_video": info["codec_video"], "pix_fmt": info["pix_fmt"],
        "codec_audio": info["codec_audio"], "taxa_audio": info["taxa_audio"],
        "lufs_saida": round(lufs, 2) if lufs is not None else None,
        "alvo_lufs": estilo["alvo_lufs"],
        "loudnorm_passadas": med["loudnorm_passadas"],
        "ganho_musica_db": med["ganho_musica_db"],
        "musica": ({"arquivo": str(plano.musica.arquivo), "licenca": plano.musica.licenca}
                   if plano.musica else None),
        "tempo_render_s": round(tempo, 2), "tempos_s": med["tempos_s"],
        "segmentos": [{"nome": s.nome, "duracao": round(dur_exata(s.duracao), 3),
                       "descricao": s.descricao} for s in plano.segmentos],
        "avisos": avisos,
        **{k: v for k, v in plano.info.items()},
        "regras": ["sem imagem de TV", "vídeo oficial com crédito e áudio original",
                   "sem narração/voz sintética", "música só livre com licença registrada",
                   "textos fora das safe zones (topo 250 px, base 350 px)"],
    }
    if r.get("_aviso"):
        rel["_aviso"] = r["_aviso"]
    escrever_json(saida.with_suffix(".relatorio.json"), rel)
    lg.info("reel %s pronto: %s (%.2fs de vídeo, %.1fs de render, %s LUFS)",
            plano.modo, saida, plano.duracao, tempo, rel["lufs_saida"])
    return rel


def gerar_exemplos(destino=None, agora: datetime | None = None, trava: bool = True,
                   dur_clipe: float = 8.0, modos=MODOS_EXEMPLO, curto: bool = False) -> list[dict]:
    """Os 4 modelos (gol, noticia, debate, estatistica) com mídia sintética.

    curto=True: clipe de 2 s e durações mínimas (conferência rápida/testes)."""
    if curto:
        dur_clipe = min(dur_clipe, 2.0)
    destino = garantir(Path(destino) if destino else pasta_modelos())
    ctx = TravaPesada("reel_futebol", agora=agora) if trava else nullcontext()
    resultados = []
    with ctx:
        midia = gerar_midia_sintetica(destino / "midia_sintetica", dur_clipe)
        for modo in modos:
            r = roteiro_modelo(modo, midia, curto)
            arq = destino / f"MODELO_{modo}.json"
            escrever_json(arq, r)
            resultados.append(montar(arq, saida=destino / f"MODELO_{modo}.mp4", trava=False))
    linhas = [AVISO_MODELO, "",
              "Arquivos desta pasta (gerados por: python scripts\\reel_futebol.py exemplos):"]
    for res in resultados:
        linhas.append(f"- {Path(res['saida']).name}: {res['modo']}, {res['duracao_planejada']:.1f}s "
                      f"de vídeo, render em {res['tempo_render_s']:.1f}s, "
                      f"{res['lufs_saida']} LUFS")
    linhas += ["- MODELO_<formato>.json: o roteiro usado (copie e troque pela mídia real)",
               "- midia_sintetica\\: clipe testsrc + seno 440 Hz, fotos de cores e trilha "
               "sintética (licença registrada em musicas_livres\\licencas.json)"]
    (destino / "LEIA_MODELOS.txt").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return resultados


def executar(trabalho: dict) -> dict:
    """Gancho do motor do HP Studio.

    trabalho = {"acao": "montar"|"validar"|"exemplos", "roteiro": caminho ou dict,
                "saida": opcional, "simular": bool, "legenda_auto": bool,
                "base": pasta dos arquivos relativos quando roteiro é dict}
    Devolve sempre um dict com "ok" (nunca levanta exceção).
    """
    acao = trabalho.get("acao", "montar")
    try:
        if acao == "exemplos":
            res = gerar_exemplos(trabalho.get("destino"), curto=bool(trabalho.get("curto")))
            return {"ok": True, "resultados": res}
        if acao == "validar":
            erros, avisos = validar(trabalho["roteiro"], bool(trabalho.get("legenda_auto")),
                                    base=trabalho.get("base"))
            return {"ok": not erros, "erros": erros, "avisos": avisos}
        return montar(trabalho["roteiro"], saida=trabalho.get("saida"),
                      simular=bool(trabalho.get("simular")),
                      legenda_auto=bool(trabalho.get("legenda_auto")),
                      base=trabalho.get("base"))
    except RoteiroInvalido as e:
        return {"ok": False, "tipo": "roteiro_invalido", "erro": str(e), "erros": e.erros,
                "avisos": e.avisos}
    except TravaOcupada as e:
        return {"ok": False, "tipo": "trava_ocupada", "erro": str(e), "tentar_depois": True}
    except (ErroReel, KeyError, OSError) as e:
        log().error("executar falhou: %s", e)
        return {"ok": False, "tipo": "erro", "erro": str(e)}


# ---------------------------------------------------------------------- CLI
def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="reel_futebol.py",
        description="Montador de reels do Futebol | HP (1080x1920, -14 LUFS). "
                    "Regras: sem imagem de TV, vídeo oficial com crédito e áudio original, "
                    "nunca voz sintética, música só livre com licença.")
    sub = p.add_subparsers(dest="comando", metavar="comando")
    m = sub.add_parser("montar", help="monta o reel a partir do roteiro JSON")
    m.add_argument("roteiro", help="caminho do roteiro .json")
    m.add_argument("--saida", help="arquivo .mp4 de saída (padrão: ao lado do roteiro)")
    m.add_argument("--simular", action="store_true",
                   help="só valida e imprime os comandos do ffmpeg, sem renderizar")
    m.add_argument("--legenda-auto", action="store_true",
                   help="gol: pede a legenda ao posts_futebol.py legenda_video")
    m.add_argument("--estilo", help="JSON de estilo (cores/fonte) no lugar do padrão")
    m.add_argument("--manter-temp", action="store_true",
                   help="não apaga os segmentos intermediários (para investigar erro)")
    v = sub.add_parser("validar", help="confere o roteiro sem renderizar")
    v.add_argument("roteiro")
    v.add_argument("--legenda-auto", action="store_true")
    v.add_argument("--estilo")
    e = sub.add_parser("exemplos", help="gera os 4 modelos (gol, noticia, debate, estatistica) "
                                        "com mídia sintética em HypadoLocal\\canais\\futebol\\modelos_reel")
    e.add_argument("--destino", help="outra pasta para os modelos")
    e.add_argument("--curto", action="store_true",
                   help="versão curta (clipe de 2 s, fotos de 1 s) só para conferir rápido")
    q = sub.add_parser("esquema", help="imprime um roteiro de exemplo do formato")
    q.add_argument("modo", nargs="?", choices=MODOS, help="formato (sem nada = todos)")
    return p


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass
    args = _parser().parse_args(argv)
    if not args.comando:
        _parser().print_help()
        return 0
    try:
        if args.comando == "esquema":
            modos = [args.modo] if args.modo else list(MODOS)
            dados = {m: roteiro_exemplo(m) for m in modos}
            print(json.dumps(dados[modos[0]] if len(modos) == 1 else dados,
                             ensure_ascii=False, indent=2))
            return 0
        if args.comando == "validar":
            erros, avisos = validar(args.roteiro, args.legenda_auto, args.estilo)
            for a in avisos:
                print(f"AVISO: {a}")
            if erros:
                print("RECUSADO:")
                for e in erros:
                    print(f"  - {e}")
                return 1
            print("OK: roteiro válido")
            return 0
        if args.comando == "montar":
            res = montar(args.roteiro, saida=args.saida, simular=args.simular,
                         legenda_auto=args.legenda_auto, estilo_arq=args.estilo,
                         manter_temp=args.manter_temp)
            for a in res.get("avisos", []):
                print(f"AVISO: {a}")
            if res.get("simulado"):
                print(f"# SIMULADO — nada foi renderizado. {res['modo']}, "
                      f"{res['duracao_planejada']:.2f}s, saída seria {res['saida']}")
                for c in res["comandos"]:
                    print(c)
            else:
                print(f"OK: {res['saida']} ({res['duracao_planejada']:.2f}s, "
                      f"{res['largura']}x{res['altura']}, {res['lufs_saida']} LUFS, "
                      f"render {res['tempo_render_s']:.1f}s)")
            return 0
        if args.comando == "exemplos":
            for res in gerar_exemplos(args.destino, curto=args.curto):
                print(f"OK: {res['saida']} ({res['duracao_planejada']:.1f}s, render "
                      f"{res['tempo_render_s']:.1f}s, {res['lufs_saida']} LUFS)")
            return 0
    except RoteiroInvalido as e:
        print("RECUSADO:")
        for err in e.erros:
            print(f"  - {err}")
        return 1
    except TravaOcupada as e:
        print(f"ESPERAR: {e}")
        return 3
    except ErroReel as e:
        print(f"ERRO: {e}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
