"""Os trabalhos da esteira — um por pasta. Interface: executar(item) -> Resultado.

| pasta               | trabalho                                   | vai para            |
|---------------------|--------------------------------------------|---------------------|
| 01_pedidos          | Baixador (vídeo); estático só valida       | 02 (vídeo) / 04     |
| 02_baixados         | confere o bruto, extrai áudio              | 03_legenda_dublagem |
| 03_legenda_dublagem | Legendador + Dublador + Narrador Toque HP  | 04_edicao           |
| 04_edicao           | Editor (vídeo) / Designer (estático)       | 05_revisao          |
| 05_revisao          | 3 quadros + texto_revisao.md; lê decisão   | 06 / volta / 99     |
| 06_agendados        | Agendador (API) + espera tiktok_ok.json    | 07_postados         |
| 07_postados         | aviso "no ar" (fila do WhatsApp/sombra)    | fim                 |

Pesados (TravaPesada, nunca 18h-22h30): baixar, conferir, legenda/dublagem,
edição de vídeo. Leves: estáticos, revisão, agendamento, aviso.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path

from hpbase import agora, agora_iso, escrever_json, garantir, ler_json

from .constantes import (AGENDADOS, ARQ_AGENDADOS, ARQ_AGUARDANDO_CURADOR,
                         ARQ_APROVADO, ARQ_AVISO, ARQ_CONFIRMACOES, ARQ_PEDIDO,
                         ARQ_POST, ARQ_REFAZER, ARQ_TEXTO_REVISAO, BAIXADOS,
                         CANAIS_COM_VOZ, CONTAS, EDICAO, ERROS,
                         EXT_IMAGEM, EXT_VIDEO, LEGENDA, NOMES_CANAIS, PEDIDOS,
                         POSTADOS, REVISAO)
from .conteudo import achar_bruto, janela_corte, montar_post
from .erros import ErroPermanente, PedidoInvalido
from .pastas import historico, ler_estado, salvar_estado
from .pedido import (eh_estatico, ler_pedido, normalizar_pedido,
                     validar_ou_erro)
from .resultado import Resultado
from .revisao import RevisaoInvalida, decidir


def _tipo_rapido(item: Path) -> str | None:
    d = ler_json(Path(item) / ARQ_PEDIDO, {}) or {}
    return str(d.get("tipo") or "").lower() or None


class Trabalho:
    etapa: str = ""
    nome: str = ""
    pesado_video: bool = False  # pesado quando o item é vídeo

    def __init__(self, esteira):
        self.e = esteira
        self.cfg = esteira.cfg
        self.p = esteira.plugins
        self.log = esteira.log

    def eh_pesado(self, item: Path) -> bool:
        if not self.pesado_video:
            return False
        tipo = _tipo_rapido(item)
        return tipo is None or tipo == "reel"

    def acionavel(self, item: Path) -> bool:
        return True

    def executar(self, item: Path) -> Resultado:  # pragma: no cover
        raise NotImplementedError


# --- 01_pedidos ---------------------------------------------------------------
class TrabalhoBaixar(Trabalho):
    etapa, nome, pesado_video = PEDIDOS, "baixar", True

    def acionavel(self, item: Path) -> bool:
        # voltou do Revisor com nota < 5: espera o Curador ajustar e liberar
        return not (Path(item) / ARQ_AGUARDANDO_CURADOR).exists()

    def executar(self, item: Path) -> Resultado:
        pedido = ler_pedido(item)
        if eh_estatico(pedido):
            return Resultado.avancar(EDICAO, f"{pedido['tipo']} é estático: pula as "
                                             f"etapas de vídeo e vai direto para a arte")
        fonte = {"fonte_url": pedido.get("fonte_url"), "arquivos": pedido.get("arquivos")}
        reg = ler_json(item / "baixado.json", {}) or {}
        bruto = achar_bruto(item)
        if bruto is not None and reg.get("fonte") == fonte:
            return Resultado.avancar(BAIXADOS, f"bruto já estava baixado ({bruto.name})")
        destino = self._locais(item, pedido.get("arquivos") or [])
        if destino is None and pedido.get("fonte_url"):
            tmp = item / "_baixando"
            if tmp.exists():
                shutil.rmtree(tmp)
            baixado = Path(self.p.baixador.baixar(pedido["fonte_url"], tmp))
            destino = self._trocar_bruto(item, baixado)
            shutil.rmtree(tmp, ignore_errors=True)
        if destino is None:
            raise ErroPermanente("nenhum vídeo: arquivos não tem vídeo e não há fonte_url")
        escrever_json(item / "baixado.json", {"fonte": fonte, "arquivo": destino.name,
                                              "bytes": destino.stat().st_size,
                                              "em": agora_iso()})
        mb = destino.stat().st_size / 1e6
        return Resultado.avancar(BAIXADOS, f"bruto pronto: {destino.name} ({mb:.1f} MB)")

    def _trocar_bruto(self, item: Path, arquivo: Path) -> Path:
        destino = item / f"bruto{arquivo.suffix.lower()}"
        for velho in item.glob("bruto.*"):
            if velho.resolve() != Path(arquivo).resolve() and velho != destino:
                velho.unlink()
        if Path(arquivo).resolve() != destino.resolve():
            os.replace(arquivo, destino)
        return destino

    def _locais(self, item: Path, arquivos: list[str]) -> Path | None:
        for a in arquivos:
            src = Path(a) if Path(a).is_absolute() else item / a
            if not src.exists():
                raise ErroPermanente(f"arquivo do pedido não encontrado: {a}")
            if src.suffix.lower() in EXT_VIDEO:
                destino = item / f"bruto{src.suffix.lower()}"
                if src.resolve() != destino.resolve():
                    tmp = item / f"_tmp_bruto{src.suffix.lower()}"
                    shutil.copy2(src, tmp)
                    return self._trocar_bruto(item, tmp)
                return destino
        return None


# --- 02_baixados --------------------------------------------------------------
class TrabalhoConferir(Trabalho):
    etapa, nome, pesado_video = BAIXADOS, "conferir_bruto", True

    def executar(self, item: Path) -> Resultado:
        pedido = ler_pedido(item)
        bruto = achar_bruto(item)
        if bruto is None:
            raise ErroPermanente("não há bruto.* na pasta (o download não chegou)")
        info = self.p.midia.info(bruto)
        if not info.get("tem_video"):
            raise ErroPermanente(f"{bruto.name} não tem imagem de vídeo")
        dur = info.get("duracao") or 0
        if dur < 0.5:
            raise ErroPermanente(f"{bruto.name} tem {dur:.2f}s: vazio ou corrompido")
        janela_corte(pedido, dur)  # valida o corte contra a duração real
        escrever_json(item / "midia.json", info)
        extra = ""
        if info.get("tem_audio"):
            self.p.midia.extrair_audio(bruto, item / "audio.wav")
            extra = ", com áudio"
        return Resultado.avancar(LEGENDA, f"bruto ok: {dur:.1f}s "
                                          f"{info.get('largura')}x{info.get('altura')}{extra}")


# --- 03_legenda_dublagem -----------------------------------------------------------
class TrabalhoLegendaDublagem(Trabalho):
    etapa, nome, pesado_video = LEGENDA, "legenda_dublagem", True

    def executar(self, item: Path) -> Resultado:
        pedido = ler_pedido(item)
        msgs = []
        legenda = None
        manual = item / "legenda_manual.srt"
        audio = item / "audio.wav"
        if manual.exists():
            legenda = manual
            msgs.append("legenda manual (legenda_manual.srt)")
        elif pedido.get("legendar", True) and audio.exists():
            legenda = Path(self.p.legendador.legendar(audio, item, pedido.get("idioma")))
            msgs.append("legenda gerada")
        else:
            msgs.append("sem legenda (sem áudio ou legendar=false)")
        if pedido["dublar"] or pedido["narrar_toque_hp"]:
            # 2ª trava (a 1ª é a validação do pedido): voz sintética nunca no futebol
            if pedido["canal"] not in CANAIS_COM_VOZ:
                raise ErroPermanente(f"voz sintética proibida no canal {pedido['canal']}")
        if pedido["dublar"]:
            if legenda is None:
                raise ErroPermanente("dublar=true precisa de legenda/transcrição")
            self.p.dublador.dublar(item, legenda, pedido)
            msgs.append("dublagem ok")
        if pedido["narrar_toque_hp"]:
            midia = ler_json(item / "midia.json", {}) or {}
            _, dur = janela_corte(pedido, midia.get("duracao"))
            self.p.narrador.narrar(item, pedido["roteiro_narracao"], dur)
            msgs.append("narração Toque HP ok")
        return Resultado.avancar(EDICAO, "; ".join(msgs))


# --- 04_edicao ---------------------------------------------------------------------
class TrabalhoEdicao(Trabalho):
    etapa, nome, pesado_video = EDICAO, "edicao", True

    def executar(self, item: Path) -> Resultado:
        pedido = ler_pedido(item)
        if eh_estatico(pedido):
            arquivos = [Path(a) for a in self.p.designer.gerar(item, pedido)]
            rel = [a.resolve().relative_to(Path(item).resolve()).as_posix() for a in arquivos]
            imgs = [r for r in rel if Path(r).suffix.lower() in EXT_IMAGEM]
            montar_post(item, pedido, rel, imgs[0] if imgs else None)
            return Resultado.avancar(REVISAO, f"{pedido['tipo']}: {len(rel)} arquivo(s) pronto(s)")
        dados = self.p.editor.editar(item, pedido)
        montar_post(item, pedido, [dados["final"]], dados.get("capa"),
                    duracao=dados.get("duracao"))
        lufs = dados.get("lufs")
        return Resultado.avancar(REVISAO, f"final.mp4 {dados.get('largura')}x{dados.get('altura')} "
                                          f"{dados.get('duracao')}s "
                                          f"{'%s LUFS' % lufs if lufs is not None else 'sem áudio'}")


# --- 05_revisao --------------------------------------------------------------------
class TrabalhoRevisao(Trabalho):
    etapa, nome = REVISAO, "revisao"

    def executar(self, item: Path) -> Resultado:
        pedido = ler_pedido(item)
        estado = ler_estado(item)
        decisoes = [n for n in (ARQ_REFAZER, ARQ_APROVADO) if (item / n).exists()]
        if len(decisoes) == 2:
            historico(item, f"[{REVISAO}] aprovado.json e refazer.json juntos: vale o "
                            f"refazer (o aprovado.json foi arquivado)")
            self._arquivar(item, ARQ_APROVADO, estado["voltas"] + 1, "ignorado_")
            decisoes = [ARQ_REFAZER]
        for nome in decisoes[:1]:
            arq = item / nome
            bruto = arq.read_bytes()
            assinatura = hashlib.sha1(bruto).hexdigest()
            if assinatura in {r.get("assinatura") for r in estado["revisoes"]}:
                # decisão antiga que ficou para trás (queda logo depois do movimento)
                self._arquivar(item, nome, estado["voltas"])
                historico(item, f"[{REVISAO}] {nome} antigo arquivado (já tinha sido aplicado)")
                break
            return self._decidir(item, pedido, estado, nome, bruto, assinatura)
        rodada = estado["voltas"] + 1
        pronto = ler_json(item / "revisao" / "pronto.json", {}) or {}
        if pronto.get("rodada") != rodada or not (item / ARQ_TEXTO_REVISAO).exists():
            self._material(item, pedido, estado, rodada)
            return Resultado.aguardar(f"material de revisão pronto (rodada {rodada}): "
                                      f"aguardando aprovado.json ou refazer.json")
        return Resultado.aguardar("aguardando aprovado.json ou refazer.json")

    def _arquivar(self, item: Path, nome: str, rodada: int, prefixo: str = "") -> None:
        arq = Path(item) / nome
        if arq.exists():
            destino = garantir(Path(item) / "revisao" / "decisoes")
            alvo = destino / f"rodada_{rodada}_{prefixo}{nome}"
            n = 2
            while alvo.exists():
                alvo = destino / f"rodada_{rodada}_{n}_{prefixo}{nome}"
                n += 1
            os.replace(arq, alvo)

    def _decidir(self, item: Path, pedido: dict, estado: dict, nome: str,
                 bruto: bytes, assinatura: str) -> Resultado:
        tipo = "refazer" if nome == ARQ_REFAZER else "aprovado"
        try:
            dados = json.loads(bruto.decode("utf-8-sig"))
            dec = decidir(dados, tipo, estado["voltas"], self.cfg.max_voltas,
                          self.cfg.criterio_etapa, eh_estatico(pedido))
        except (ValueError, RevisaoInvalida) as ex:
            invalido = item / nome.replace(".json", ".invalido.json")
            os.replace(item / nome, invalido)
            historico(item, f"[{REVISAO}] {nome} inválido ({ex}); renomeado para {invalido.name}")
            return Resultado.aguardar(f"{nome} inválido: {ex}")
        rodada = estado["voltas"] + 1
        registro = {"rodada": rodada, "arquivo": nome, "assinatura": assinatura,
                    "acao": dec["acao"], "destino": dec["destino"], "media": dec["media"],
                    "veredito": dec["veredito"], "criterio_menor": dec["criterio_menor"],
                    "motivo": dec["motivo"], "revisor": dados.get("revisor"),
                    "em": agora_iso()}
        completo = dict(dados)
        completo.update({"media": dec["media"], "veredito": dec["veredito"],
                         "etapa_destino": dec["destino"], "decisao": dec["acao"],
                         "observacoes_app": dec["observacoes"]})
        escrever_json(item / "revisao" / f"decisao_rodada_{rodada}.json", completo)
        for o in dec["observacoes"]:
            historico(item, f"[{REVISAO}] obs: {o}")
        estado["revisoes"].append(registro)
        media_txt = f"média {dec['media']} ({dec['veredito']})" if dec["media"] is not None \
            else "sem notas"

        if dec["acao"] == "aprovar":
            estado["pendente"] = {"origem": REVISAO, "destino": AGENDADOS,
                                  "mensagem": f"aprovado: {media_txt}"}
            salvar_estado(item, estado)
            return Resultado.avancar(AGENDADOS, f"aprovado: {media_txt}")

        if dec["acao"] == "erro":
            erro = {"etapa": REVISAO, "trabalho": "revisao", "mensagem": dec["motivo"],
                    "traceback": "", "tentativas": rodada, "permanente": True,
                    "em": agora_iso()}
            estado["pendente"] = {"origem": REVISAO, "destino": ERROS,
                                  "mensagem": f"ERRO: {dec['motivo']}", "erro": erro}
            salvar_estado(item, estado)
            res = Resultado.erro(dec["motivo"], permanente=True)
            res.dados["erro_info"] = erro
            return res

        # volta
        destino = dec["destino"]
        msg = f"refazer ({media_txt}; volta {estado['voltas'] + 1}/{self.cfg.max_voltas}): {dec['motivo']}"
        self._ajustes(item, dados.get("ajustes"))  # antes do estado: refazer é idempotente
        if destino == PEDIDOS:
            escrever_json(item / ARQ_AGUARDANDO_CURADOR, {
                "motivo": dec["motivo"], "media": dec["media"], "veredito": dec["veredito"],
                "notas": dec["notas"], "em": agora_iso(),
                "o_que_fazer": "Curador: ajuste pedido.json (ou troque a fonte) e rode "
                               "`python -m esteira liberar <item>`"})
        estado["voltas"] += 1
        estado["pendente"] = {"origem": REVISAO, "destino": destino, "mensagem": msg}
        salvar_estado(item, estado)
        volta = estado["voltas"]
        res = Resultado.avancar(destino, msg)
        res.apos_mover = lambda novo: self._arquivar(novo, nome, volta)
        return res

    def _ajustes(self, item: Path, ajustes) -> None:
        if not ajustes:
            return
        if not isinstance(ajustes, dict):
            raise ErroPermanente("ajustes do refazer.json tem que ser um objeto")
        atual = ler_json(item / ARQ_PEDIDO, {}) or {}
        novo = dict(atual)
        novo.update({k: v for k, v in ajustes.items() if k not in ("id",)})
        novo = normalizar_pedido(novo)
        try:
            validar_ou_erro(novo)
        except PedidoInvalido as ex:
            raise ErroPermanente(f"ajustes deixam o pedido inválido: {ex}") from ex
        escrever_json(item / ARQ_PEDIDO, novo)
        historico(item, f"[{REVISAO}] ajustes aplicados ao pedido: {', '.join(ajustes)}")

    def _material(self, item: Path, pedido: dict, estado: dict, rodada: int) -> None:
        pasta = garantir(item / "revisao")
        for velho in pasta.glob("quadro_*.jpg"):
            velho.unlink()
        post = ler_json(item / ARQ_POST, {}) or {}
        largura = int(self.cfg.largura_quadro_revisao)
        quadros: list[dict] = []
        if not eh_estatico(pedido):
            final = item / (post.get("arquivos") or ["final.mp4"])[0]
            if not final.exists():
                raise ErroPermanente("final.mp4 não existe: volte para 04_edicao")
            quadros = self.p.midia.quadros(final, pasta, largura)
        else:
            imgs = [a for a in post.get("arquivos", []) if Path(a).suffix.lower() in EXT_IMAGEM]
            escolhidas = imgs if len(imgs) <= 3 else [imgs[0], imgs[len(imgs) // 2], imgs[-1]]
            nomes = ("quadro_1_inicio.jpg", "quadro_2_meio.jpg", "quadro_3_fim.jpg")
            for nome, img in zip(nomes, escolhidas):
                self.p.midia.reduzir_imagem(item / img, pasta / nome, largura)
                quadros.append({"arquivo": nome, "origem": img})
        texto = texto_revisao(item, pedido, post, estado, rodada, quadros,
                              ler_json(item / "edicao.json", {}) or {},
                              self.cfg.criterio_etapa, self.cfg.max_voltas)
        (item / ARQ_TEXTO_REVISAO).write_text(texto, encoding="utf-8")
        escrever_json(pasta / "pronto.json", {"rodada": rodada, "quadros": quadros,
                                              "em": agora_iso()})


def texto_revisao(item: Path, pedido: dict, post: dict, estado: dict, rodada: int,
                  quadros: list[dict], edicao: dict, mapa: dict, max_voltas: int) -> str:
    L = [f"# Revisão — {Path(item).name}", ""]
    L.append(f"- Rodada: {rodada} (voltas até agora: {estado['voltas']} de {max_voltas})")
    L.append(f"- Canal: {NOMES_CANAIS[pedido['canal']]} ({CONTAS[pedido['canal']]}) · "
             f"tipo: {pedido['tipo']} · prioridade: {pedido['prioridade']}")
    L.append(f"- Horário alvo: {pedido['horario_alvo']} · redes: {', '.join(pedido['redes'])}")
    L.append(f"- Título: {pedido['titulo']}")
    L.append(f"- Crédito: {pedido.get('credito') or '(sem fonte externa)'}")
    if pedido.get("fonte_url"):
        L.append(f"- Fonte: {pedido['fonte_url']}")
    if pedido.get("observacoes"):
        L.append(f"- Observações do pedido: {pedido['observacoes']}")
    L += ["", "## Conferência automática"]
    if edicao:
        res_ok = (edicao.get("largura"), edicao.get("altura")) == (1080, 1920)
        L.append(f"- Resolução: {edicao.get('largura')}x{edicao.get('altura')} "
                 f"({'ok' if res_ok else 'FORA do 1080x1920'})")
        L.append(f"- Duração: {edicao.get('duracao')} s")
        lufs = edicao.get("lufs")
        if lufs is None:
            L.append("- Loudness: sem áudio")
        else:
            ok = abs(float(lufs) - float(edicao.get("alvo_lufs", -14))) <= 1.0
            L.append(f"- Loudness: {lufs} LUFS (alvo {edicao.get('alvo_lufs', -14)}; "
                     f"{'ok' if ok else 'FORA do alvo'})")
        L.append(f"- Legenda queimada: {'sim' if edicao.get('legenda_queimada') else 'não'}"
                 f" ({edicao.get('falas', 0)} falas) · dublagem: "
                 f"{'sim' if edicao.get('dublagem') else 'não'} · narração Toque HP: "
                 f"{'sim' if edicao.get('narracao') else 'não'}")
    else:
        L.append(f"- Arquivos: {', '.join(post.get('arquivos', []))}")
    if quadros:
        L += ["", "## Quadros (olhe os 3)"]
        for q in quadros:
            quando = f" ({q['segundo']} s)" if "segundo" in q else f" ({q.get('origem')})"
            L.append(f"- revisao/{q['arquivo']}{quando}")
    leg = next((Path(item) / n for n in ("legenda_manual.srt", "legenda_pt.srt", "legenda.srt")
                if (Path(item) / n).exists()), None)
    if leg is not None:
        L += ["", f"## Legenda queimada ({leg.name})", "```",
              leg.read_text(encoding="utf-8").strip()[:4000], "```"]
    if post.get("legenda"):
        L += ["", "## Legenda do post", "```", post["legenda"], "```"]
    L += ["", "## Como responder",
          "Grave UM arquivo nesta pasta (ou use a linha de comando):",
          "- `aprovado.json` — `python -m esteira aprovar <item> --notas gancho=9 legenda=8 ...`",
          "- `refazer.json` — `python -m esteira refazer <item> --motivo \"...\" --notas ...`",
          "", "```json",
          '{"notas": {"assunto": 9, "fonte_credito": 10, "gancho": 8, "legenda": 7}, '
          '"motivo": "...", "etapa_destino": "(opcional)", "ajustes": {}, "revisor": "Claude"}',
          "```", "",
          "Faixas: média >= 9 Excelente, 7 a 8,9 Bom (aprovado); 5 a 6,9 Médio (volta "
          "para a etapa do critério de menor nota); abaixo de 5 Razoável (volta ao "
          f"Curador). Máximo {max_voltas} voltas; na seguinte vai para 99_erros.", "",
          "| critério | volta para |", "|---|---|"]
    for crit, etapa in mapa.items():
        L.append(f"| {crit} | {etapa} |")
    return "\n".join(L) + "\n"


# --- 06_agendados --------------------------------------------------------------------
class TrabalhoAgendar(Trabalho):
    etapa, nome = AGENDADOS, "agendar"

    def executar(self, item: Path) -> Resultado:
        post = ler_json(item / ARQ_POST, None)
        if not post:
            raise ErroPermanente("post.json não existe (a edição não terminou)")
        agendados = ler_json(item / ARQ_AGENDADOS, {}) or {}
        conf = ler_json(item / ARQ_CONFIRMACOES, {}) or {}
        mudou = False
        for rede in post["redes"]:
            if rede in conf:
                continue
            if rede not in self.cfg.redes_api:
                ok = ler_json(item / f"{rede}_ok.json", None)
                if ok is not None:
                    conf[rede] = {"status": ok.get("status", "agendado"), "link": ok.get("link"),
                                  "agendado_para": ok.get("agendado_para"),
                                  "em": ok.get("em") or agora_iso(), "fonte": f"{rede}_ok.json"}
                    mudou = True
                continue
            if rede not in agendados:
                agendados[rede] = self.p.agendador.agendar(item, post, rede)
                escrever_json(item / ARQ_AGENDADOS, agendados)
                historico(item, f"[{AGENDADOS}] {rede}: na fila ({agendados[rede].get('modo')})")
            c = self.p.agendador.conferir(item, post, rede, agendados[rede])
            if c:
                if c.get("status") == "erro":
                    if mudou:
                        escrever_json(item / ARQ_CONFIRMACOES, conf)
                    raise ErroPermanente(f"{rede}: o publicador marcou erro: {c.get('mensagem')}")
                conf[rede] = c
                mudou = True
        if mudou:
            escrever_json(item / ARQ_CONFIRMACOES, conf)
        faltam = [r for r in post["redes"] if r not in conf]
        if not faltam:
            return Resultado.avancar(POSTADOS, "todas as redes confirmadas: " +
                                     ", ".join(f"{r}={conf[r].get('status')}" for r in post["redes"]))
        como = [f"{r} ({r}_ok.json)" if r not in self.cfg.redes_api else f"{r} (API)"
                for r in faltam]
        return Resultado.aguardar("aguardando: " + ", ".join(como))


# --- 07_postados ------------------------------------------------------------------------
class TrabalhoAvisoNoAr(Trabalho):
    etapa, nome = POSTADOS, "aviso_no_ar"

    def acionavel(self, item: Path) -> bool:
        aviso = ler_json(Path(item) / ARQ_AVISO, {}) or {}
        return aviso.get("status") not in ("na_fila", "sombra")

    def executar(self, item: Path) -> Resultado:
        from .aviso import montar_aviso
        post = ler_json(item / ARQ_POST, None)
        if not post:
            raise ErroPermanente("post.json não existe")
        conf = ler_json(item / ARQ_CONFIRMACOES, {}) or {}
        aviso = ler_json(item / ARQ_AVISO, {}) or {}
        nome = aviso.get("arquivo_nome") if aviso.get("status") == "preparando" else None
        if not nome:
            nome = f"{agora():%Y%m%d-%H%M%S}_no_ar_{item.name}.json"
        msg = montar_aviso(post, conf, self.cfg.grupo_whatsapp)
        escrever_json(item / ARQ_AVISO, {"status": "preparando", "arquivo_nome": nome,
                                         "mensagem": msg})
        caminho, modo = self.p.avisador.enviar(item, msg, nome)
        escrever_json(item / ARQ_AVISO, {"status": modo, "arquivo_nome": nome,
                                         "arquivo": str(caminho), "mensagem": msg,
                                         "em": agora_iso()})
        onde = "na fila do WhatsApp" if modo == "na_fila" else "em modo sombra (não enviado)"
        return Resultado.final(f"aviso 'no ar' {onde}: {caminho.name}")


TODOS = (TrabalhoBaixar, TrabalhoConferir, TrabalhoLegendaDublagem, TrabalhoEdicao,
         TrabalhoRevisao, TrabalhoAgendar, TrabalhoAvisoNoAr)
