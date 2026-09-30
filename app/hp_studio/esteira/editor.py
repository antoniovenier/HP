"""Editor (manual 03) com ffmpeg de verdade.

Entrada (na pasta do item): bruto.<ext>, legenda.srt (ou legenda_pt.srt /
legenda_manual.srt), dublagem.wav e narracao.wav quando houver, capa_manual.jpg
opcional. Saída: final.mp4 1080x1920 30 fps H.264 + AAC 48 kHz, legenda e
crédito queimados, loudness -14 LUFS (loudnorm em 2 passadas, modo linear),
capa.jpg 1080x1920 e edicao.json com os números (para o QA de paridade).

Fundo: quando o vídeo não é 9:16, a versão "desfoque" põe o próprio vídeo
ampliado e borrado atrás (padrão dos reels); "preto" põe tarjas pretas.
"""
from __future__ import annotations

import os
from pathlib import Path

from hpbase import agora_iso, escrever_json

from .conteudo import achar_bruto, janela_corte, texto_credito
from .erros import ErroEtapa, ErroPermanente
from .legendas import deslocar, gerar_ass, ler_srt
from .midia import extrair_quadro, ffmpeg, info_midia, ler_json_loudnorm
from .pedido import fonte_externa

SILENCIO_LUFS = -70.0


def escolher_legenda(item: Path) -> Path | None:
    """legenda_manual.srt (corrigida pelo revisor) > legenda_pt.srt (tradução
    da dublagem) > legenda.srt (transcrição)."""
    for nome in ("legenda_manual.srt", "legenda_pt.srt", "legenda.srt"):
        p = Path(item) / nome
        if p.exists() and p.stat().st_size > 0:
            return p
    return None


class EditorFFmpeg:
    def __init__(self, cfg):
        self.cfg = cfg
        self.o = cfg.editor

    # --- partes do filtro ------------------------------------------------
    def _filtro_video(self, largura_src, altura_src, ass: str | None) -> str:
        L, A = int(self.o["largura"]), int(self.o["altura"])
        prop_src = (largura_src / altura_src) if (largura_src and altura_src) else 0
        if self.o.get("fundo", "desfoque") == "desfoque" and abs(prop_src - L / A) > 0.01:
            v = (f"[0:v]split=2[fundo][frente];"
                 f"[fundo]scale={L}:{A}:force_original_aspect_ratio=increase,"
                 f"crop={L}:{A},boxblur=40:2,eq=brightness=-0.08[fb];"
                 f"[frente]scale={L}:{A}:force_original_aspect_ratio=decrease[ff];"
                 f"[fb][ff]overlay=(W-w)/2:(H-h)/2")
        else:
            v = (f"[0:v]scale={L}:{A}:force_original_aspect_ratio=decrease,"
                 f"pad={L}:{A}:(ow-iw)/2:(oh-ih)/2:black")
        v += f",fps={int(self.o['fps'])},setsar=1,format=yuv420p"
        if ass:
            v += f",ass={ass}"
        return v + "[v]"

    def _audio(self, tem_audio: bool, ini: float, dur: float,
               dublagem: Path | None, narracao: Path | None):
        """Monta entradas extras e o grafo de áudio até o rótulo final."""
        fmt = "aformat=sample_rates=48000:channel_layouts=stereo"
        entradas: list[str] = []
        partes: list[str] = []
        idx = 1
        base = None
        if tem_audio:
            partes.append(f"[0:a]{fmt}[orig]")
            base = "orig"
        if dublagem:
            entradas += ["-ss", f"{ini:.3f}", "-t", f"{dur:.3f}", "-i", str(dublagem)]
            partes.append(f"[{idx}:a]{fmt}[dub]")
            idx += 1
            if base:
                vol = float(self.o["volume_original_com_dublagem"])
                partes.append(f"[{base}]volume={vol}[origb];"
                              f"[origb][dub]amix=inputs=2:normalize=0:duration=longest[mixd]")
                base = "mixd"
            else:
                base = "dub"
        if narracao:
            entradas += ["-i", str(narracao)]
            if base:
                partes.append(f"[{idx}:a]{fmt},asplit=2[narr1][narr2]")
                partes.append(f"[{base}][narr1]sidechaincompress=threshold=0.02:ratio=8:"
                              f"attack=20:release=400[duck];"
                              f"[duck][narr2]amix=inputs=2:normalize=0:duration=longest[mixn]")
                base = "mixn"
            else:
                partes.append(f"[{idx}:a]{fmt}[narr]")
                base = "narr"
            idx += 1
        silencioso = base is None
        if silencioso:
            entradas += ["-f", "lavfi", "-t", f"{dur:.3f}", "-i",
                         "anullsrc=r=48000:cl=stereo"]
            partes.append(f"[{idx}:a]{fmt}[sil]")
            base = "sil"
            idx += 1
        partes.append(f"[{base}]apad,atrim=end={dur:.3f}[amix]")
        return entradas, ";".join(partes), silencioso

    def _loudnorm(self, medido: dict | None, json_saida: bool = False) -> str:
        o = self.o
        f = f"loudnorm=I={o['lufs']}:TP={o['true_peak']}:LRA={o['lra']}"
        if medido:
            f += (f":measured_I={medido['input_i']}:measured_TP={medido['input_tp']}"
                  f":measured_LRA={medido['input_lra']}"
                  f":measured_thresh={medido['input_thresh']}"
                  f":offset={medido['target_offset']}:linear=true")
        f += ":print_format=json" if json_saida else ":print_format=summary"
        return f

    # --- trabalho --------------------------------------------------------
    def editar(self, item: Path, pedido: dict) -> dict:
        item = Path(item).resolve()  # o ffmpeg roda com cwd=item
        bruto = achar_bruto(item)
        if bruto is None:
            raise ErroPermanente("não há bruto.* (vídeo) na pasta do item")
        info = info_midia(bruto)
        if not info.tem_video:
            raise ErroPermanente(f"{bruto.name} não tem vídeo")
        ini, dur = janela_corte(pedido, info.duracao)
        timeout = self.cfg.timeouts.get("ffmpeg", 3600)

        # legenda + crédito -> legenda.ass (caminho relativo: roda com cwd=item)
        leg = escolher_legenda(item)
        falas = deslocar(ler_srt(leg), ini, dur) if leg else []
        credito = texto_credito(pedido) if (fonte_externa(pedido) or pedido.get("credito")) else None
        ass = None
        if falas or credito:
            gerar_ass(falas, item / "legenda.ass", dur, credito,
                      int(self.o["largura"]), int(self.o["altura"]),
                      self.o["fonte_legenda"], int(self.o["tamanho_legenda"]),
                      int(self.o["margem_legenda"]), int(self.o["tamanho_credito"]))
            ass = "legenda.ass"

        dub = item / "dublagem.wav"
        dub = dub if (pedido.get("dublar") and dub.exists()) else None
        narr = item / "narracao.wav"
        narr = narr if (pedido.get("narrar_toque_hp") and narr.exists()) else None
        if pedido.get("dublar") and dub is None:
            raise ErroEtapa("dublar=true mas dublagem.wav não existe")
        if pedido.get("narrar_toque_hp") and narr is None:
            raise ErroEtapa("narrar_toque_hp=true mas narracao.wav não existe")

        entrada0 = ["-ss", f"{ini:.3f}", "-t", f"{dur:.3f}", "-i", str(bruto)]
        extras, grafo_audio, silencioso = self._audio(info.tem_audio, ini, dur, dub, narr)

        # 1ª passada: mede o loudness do áudio já mixado
        medido = None
        if not silencioso:
            r = ffmpeg(["-nostats", "-y", *entrada0, *extras, "-filter_complex",
                        f"{grafo_audio};[amix]{self._loudnorm(None, True)}[med]",
                        "-map", "[med]", "-f", "null", "-"],
                       timeout=timeout, cwd=item, o_que="medição de loudness")
            medido = ler_json_loudnorm(r.stderr.decode("utf-8", "replace"))
            if medido["input_i"] <= SILENCIO_LUFS:
                medido = None
                silencioso = True

        # 2ª passada: vídeo final
        cadeia_a = "[amix]"
        if medido:
            cadeia_a += self._loudnorm(medido) + ","
        cadeia_a += "aresample=48000[a]"
        filtro = ";".join([self._filtro_video(info.largura, info.altura, ass),
                           grafo_audio, cadeia_a])
        tmp = item / "_final_tmp.mp4"
        o = self.o
        ffmpeg(["-nostats", "-y", *entrada0, *extras, "-filter_complex", filtro,
                "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-preset", str(o["preset"]), "-crf", str(o["crf"]),
                "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", str(o["fps"]),
                "-c:a", "aac", "-b:a", str(o["bitrate_audio"]), "-ar", "48000", "-ac", "2",
                "-movflags", "+faststart", "-t", f"{dur:.3f}", tmp.name],
               timeout=timeout, cwd=item, o_que="edição (ffmpeg)")

        # confere o resultado antes de aceitar
        fi = info_midia(tmp)
        L, A = int(o["largura"]), int(o["altura"])
        if (fi.largura, fi.altura) != (L, A):
            raise ErroEtapa(f"final saiu {fi.largura}x{fi.altura}, esperado {L}x{A}")
        if fi.duracao is None or abs(fi.duracao - dur) > max(0.25, dur * 0.02):
            raise ErroEtapa(f"final saiu com {fi.duracao}s, esperado {dur:.2f}s")
        final = item / "final.mp4"
        os.replace(tmp, final)

        capa = self._capa(item, final, pedido, dur)
        lufs = None
        if not silencioso:
            from .midia import medir_loudness
            v = medir_loudness(final, o["lufs"], o["true_peak"], o["lra"])["input_i"]
            lufs = None if v == float("-inf") else round(v, 2)
        dados = {
            "final": final.name, "capa": capa.name if capa else None,
            "duracao": round(fi.duracao, 3), "largura": fi.largura, "altura": fi.altura,
            "fps": fi.fps, "lufs": lufs, "alvo_lufs": o["lufs"],
            "silencioso": silencioso, "legenda_queimada": bool(falas),
            "falas": len(falas), "credito": credito,
            "dublagem": dub is not None, "narracao": narr is not None,
            "corte": {"inicio": ini, "duracao": dur}, "bruto": bruto.name,
            "gerado_em": agora_iso(),
        }
        escrever_json(item / "edicao.json", dados)
        return dados

    def _capa(self, item: Path, final: Path, pedido: dict, dur: float) -> Path:
        capa = item / "capa.jpg"
        L, A = int(self.o["largura"]), int(self.o["altura"])
        for nome in ("capa_manual.jpg", "capa_manual.png"):
            manual = item / nome
            if manual.exists():
                tmp = item / "_tmp_capa.jpg"
                ffmpeg(["-y", "-i", str(manual), "-vf",
                        f"scale={L}:{A}:force_original_aspect_ratio=increase,crop={L}:{A}",
                        "-frames:v", "1", "-q:v", "2", str(tmp)], timeout=120,
                       o_que="capa manual")
                os.replace(tmp, capa)
                return capa
        t = pedido.get("capa_tempo")
        if t is None:
            t = min(float(self.o["capa_segundo"]), dur / 3)
        t = min(float(t), max(0.0, dur - 0.1))
        return extrair_quadro(final, t, capa)
