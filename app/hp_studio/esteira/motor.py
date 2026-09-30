"""Motor da esteira: escolhe o próximo item, roda o trabalho da etapa e move.

Ordem: a cada passo o motor olha TODAS as etapas e pega o item de maior
prioridade (P0 antes de P1 antes de P2), depois o de horário alvo mais cedo,
depois o mais adiantado na esteira. Assim um P0 fura a fila em qualquer
etapa e, dentro do mesmo ciclo, anda até onde der (faixa expressa).

Segurança contra queda (o app pode cair a qualquer momento):
- `.em_andamento` (marcador) é gravado na pasta do item antes do trabalho;
  se o app cair no meio, o próximo ciclo acha o marcador, anota "retomada"
  no historico.log e refaz a etapa (os trabalhos gravam com nome temporário
  + os.replace, então refazer é seguro). Queda repetida conta tentativa.
- `estado.json` -> "pendente" (diário de movimento) é gravado antes de mover;
  se cair entre o fim do trabalho e o movimento, o próximo ciclo só completa
  o movimento, sem refazer o trabalho.
- o movimento em si é os.replace da pasta inteira (atômico).
"""
from __future__ import annotations

import os
import shutil
import time
import traceback
from contextlib import nullcontext
from datetime import datetime, timedelta
from pathlib import Path

from hpbase import (TravaOcupada, TravaPesada, agora_iso, escrever_json,
                    janela_proibida, ler_json, obter_logger)
from hpbase import agora as hp_agora

from .config import Config, carregar_config
from .constantes import (ARQ_ERRO, ARQ_MARCADOR, ARQ_PEDIDO, ERROS, ETAPAS,
                         PEDIDOS, POSTADOS)
from .erros import ErroEtapa, ErroPermanente, PedidoInvalido
from .pastas import (chave_ordem, eh_item, historico, indice_etapa, ler_estado,
                     ler_nome, listar, mover, nome_livre, salvar_estado)
from .pedido import criar_pedido, ler_pedido, nome_do_item, normalizar_pedido
from .resultado import AGUARDAR, AVANCAR, ERRO, FINAL, Resultado
from .trabalhos import TODOS

CRIANDO_VELHO_SEG = 3600


def resumo_traceback(limite: int = 6) -> str:
    linhas = traceback.format_exc().strip().splitlines()
    return "\n".join(linhas[-limite:])


class Esteira:
    def __init__(self, cfg: Config | None = None, plugins=None, simular: bool = False,
                 agora: datetime | None = None):
        self.cfg = cfg or carregar_config()
        self.simular = simular
        if plugins is None:
            if simular:
                from .simulados import plugins_simulados
                plugins = plugins_simulados(self.cfg)
            else:
                from .plugins import plugins_reais
                plugins = plugins_reais(self.cfg)
        self.plugins = plugins
        self._agora = agora
        self.log = obter_logger("esteira")
        self.cfg.garantir_pastas()
        self.trabalhos = {t.etapa: t(self) for t in TODOS}

    def agora(self) -> datetime:
        return self._agora or datetime.now()

    # --- ciclo ------------------------------------------------------------
    def ciclo(self, max_trabalhos: int | None = None) -> dict:
        """Uma passada: importa pedidos soltos e processa o que der, em ordem
        de prioridade, respeitando a trava do pesado e a janela 18h-22h30."""
        resumo = {"inicio": agora_iso(), "simular": self.simular, "modo": self.cfg.modo,
                  "importados": self.importar_pedidos_soltos(),
                  "arquivados": self.arquivar_postados(), "executados": [],
                  "avancaram": [], "aguardando": [], "erros": [], "adiados_pesado": [],
                  "motivo_pesado": None}
        bloqueio = None
        if janela_proibida(self.agora()):
            bloqueio = "janela proibida (18h-22h30): trabalho pesado espera, inclusive P0"
        # (item, etapa) -> voltas: cada item passa 1 vez por etapa no ciclo; depois
        # de uma volta da revisão pode passar de novo (as voltas são limitadas)
        feitos: dict[tuple[str, str], int] = {}
        n = 0
        while max_trabalhos is None or n < max_trabalhos:
            prox = self._proximo(feitos)
            if prox is None:
                break
            etapa, item = prox
            feitos[(item.name, etapa)] = ler_estado(item)["voltas"]
            pesado = self.trabalhos[etapa].eh_pesado(item)
            if pesado and bloqueio:
                resumo["adiados_pesado"].append(f"{etapa}/{item.name}")
                continue
            try:
                res = self.processar(item, etapa, pesado)
            except TravaOcupada as e:
                bloqueio = str(e)
                resumo["adiados_pesado"].append(f"{etapa}/{item.name}")
                continue
            n += 1
            resumo["executados"].append(f"{etapa}/{item.name}")
            linha = f"{etapa}/{item.name}: {res.mensagem}"
            if res.status == AVANCAR:
                resumo["avancaram"].append(f"{etapa} -> {res.destino}: {item.name}")
            elif res.status == ERRO:
                resumo["erros"].append(linha)
            else:
                resumo["aguardando"].append(linha)
        resumo["motivo_pesado"] = bloqueio
        resumo["fim"] = agora_iso()
        if resumo["executados"] or resumo["importados"] or resumo["erros"]:
            self.log.info("ciclo: %d executados, %d avançaram, %d erros, %d pesados adiados",
                          len(resumo["executados"]), len(resumo["avancaram"]),
                          len(resumo["erros"]), len(resumo["adiados_pesado"]))
        return resumo

    def _proximo(self, feitos: dict) -> tuple[str, Path] | None:
        melhor = None
        for etapa in ETAPAS:
            trab = self.trabalhos[etapa]
            idx = indice_etapa(etapa)
            for item in listar(self.cfg.pasta(etapa)):
                ja = feitos.get((item.name, etapa))
                if ja is not None and ja == ler_estado(item)["voltas"]:
                    continue
                if not trab.acionavel(item):
                    continue
                chave = chave_ordem(item.name, idx)
                if melhor is None or chave < melhor[0]:
                    melhor = (chave, etapa, item)
        return None if melhor is None else (melhor[1], melhor[2])

    # --- um item ------------------------------------------------------------
    def processar(self, item: Path, etapa: str, pesado: bool | None = None) -> Resultado:
        item = Path(item)
        trab = self.trabalhos[etapa]
        if pesado is None:
            pesado = trab.eh_pesado(item)
        estado = ler_estado(item)

        # 1) diário: movimento que ficou pela metade
        pend = estado.get("pendente")
        if pend:
            if pend.get("origem") == etapa and pend.get("destino"):
                historico(item, f"[{etapa}] retomada: completando movimento para {pend['destino']}")
                return self._mover_seguro(item, etapa, pend["destino"],
                                          pend.get("mensagem", ""), pend.get("erro"))
            estado.pop("pendente", None)
            salvar_estado(item, estado)

        # 2) marcador de trabalho interrompido
        marcador = item / ARQ_MARCADOR
        if marcador.exists():
            m = ler_json(marcador, {}) or {}
            marcador.unlink(missing_ok=True)
            if m.get("etapa") == etapa:
                n = estado["tentativas"].get(etapa, 0) + 1
                estado["tentativas"][etapa] = n
                salvar_estado(item, estado)
                historico(item, f"[{etapa}] retomada após queda (desde {m.get('desde')}): "
                                f"refazendo '{trab.nome}' ({n}/{self.cfg.max_tentativas})")
                self.log.warning("retomada após queda: %s em %s", item.name, etapa)
                if n >= self.cfg.max_tentativas:
                    return self._para_erros(item, etapa, trab.nome,
                                            f"caiu {n} vezes nesta etapa", "", n, True)

        # 3) trabalho (com a trava do pesado quando precisa)
        trava = TravaPesada(f"esteira:{etapa}:{item.name}", agora=self.agora()) \
            if pesado else nullcontext()
        with trava:
            escrever_json(marcador, {"etapa": etapa, "trabalho": trab.nome,
                                     "pid": os.getpid(), "desde": agora_iso()})
            try:
                res = trab.executar(item)
            except ErroPermanente as e:
                res = Resultado.erro(str(e), permanente=True)
                res.dados["traceback"] = resumo_traceback()
            except Exception as e:  # noqa: BLE001 — qualquer falha vira registro
                res = Resultado.erro(f"{type(e).__name__}: {e}", permanente=False)
                res.dados["traceback"] = resumo_traceback()
            return self._aplicar(item, etapa, trab, res)

    def _aplicar(self, item: Path, etapa: str, trab, res: Resultado) -> Resultado:
        marcador = item / ARQ_MARCADOR
        if res.status == AVANCAR:
            estado = ler_estado(item)
            estado["tentativas"].pop(etapa, None)
            salvar_estado(item, estado)
            return self._mover_seguro(item, etapa, res.destino, res.mensagem,
                                      apos=res.apos_mover)
        if res.status in (AGUARDAR, FINAL):
            marcador.unlink(missing_ok=True)
            estado = ler_estado(item)
            chave = f"{etapa}: {res.mensagem}"
            if estado.get("aguardando") != chave:
                historico(item, f"[{etapa}] {res.mensagem}")
                self.log.info("%s %s: %s", etapa, item.name, res.mensagem)
                estado["aguardando"] = chave
                if res.status == FINAL:
                    estado["concluido_em"] = agora_iso()
                salvar_estado(item, estado)
            return res
        # erro
        estado = ler_estado(item)
        n = estado["tentativas"].get(etapa, 0) + 1
        estado["tentativas"][etapa] = n
        salvar_estado(item, estado)
        if not res.permanente and n < self.cfg.max_tentativas:
            marcador.unlink(missing_ok=True)
            historico(item, f"[{etapa}] falhou (tentativa {n}/{self.cfg.max_tentativas}; "
                            f"tenta de novo no próximo ciclo): {res.mensagem}")
            self.log.warning("%s %s falhou (%d/%d): %s", etapa, item.name, n,
                             self.cfg.max_tentativas, res.mensagem)
            res.dados["vai_tentar_de_novo"] = True
            return res
        info = res.dados.get("erro_info")
        return self._para_erros(item, etapa, trab.nome, res.mensagem,
                                res.dados.get("traceback", ""), n, res.permanente, info)

    def _para_erros(self, item: Path, etapa: str, trabalho: str, mensagem: str,
                    tb: str, tentativas: int, permanente: bool,
                    info: dict | None = None) -> Resultado:
        erro = info or {"etapa": etapa, "trabalho": trabalho, "mensagem": mensagem,
                        "traceback": tb, "tentativas": tentativas,
                        "permanente": permanente, "em": agora_iso()}
        self.log.error("%s %s -> 99_erros: %s", etapa, item.name, mensagem)
        res = self._mover_seguro(item, etapa, ERROS, f"ERRO: {mensagem}", erro)
        if res.status != AGUARDAR:
            res.status = ERRO
        return res

    def _mover_seguro(self, item: Path, etapa: str, destino: str, mensagem: str,
                      erro: dict | None = None, apos=None) -> Resultado:
        try:
            return self._mover(item, etapa, destino, mensagem, erro, apos)
        except ErroEtapa as e:
            (item / ARQ_MARCADOR).unlink(missing_ok=True)
            historico(item, f"[{etapa}] movimento para {destino} adiado: {e}")
            self.log.warning("movimento adiado %s: %s", item.name, e)
            return Resultado.aguardar(f"movimento para {destino} adiado: {e}")

    def _mover(self, item: Path, etapa: str, destino: str, mensagem: str,
               erro: dict | None = None, apos=None) -> Resultado:
        estado = ler_estado(item)
        estado["pendente"] = {"origem": etapa, "destino": destino, "mensagem": mensagem}
        if erro:
            estado["pendente"]["erro"] = erro
        salvar_estado(item, estado)
        if erro:
            escrever_json(item / ARQ_ERRO, erro)
        historico(item, f"[{etapa}] -> {destino}: {mensagem}")
        pasta = self.cfg.pasta(destino)
        novo_nome = nome_livre(pasta, item.name) if destino == ERROS else None
        novo = mover(item, pasta, novo_nome)
        (novo / ARQ_MARCADOR).unlink(missing_ok=True)
        est = ler_estado(novo)
        est.pop("pendente", None)
        est.pop("aguardando", None)
        est.setdefault("passagens", []).append({"etapa": destino, "em": agora_iso()})
        salvar_estado(novo, est)
        if apos is not None:
            try:
                apos(novo)
            except Exception as e:  # noqa: BLE001
                self.log.warning("pós-movimento de %s falhou: %s", novo.name, e)
        if destino != ERROS:
            self.log.info("%s -> %s: %s (%s)", etapa, destino, novo.name, mensagem)
        st = ERRO if destino == ERROS else AVANCAR
        return Resultado(st, destino, mensagem, {"item": str(novo)})

    # --- 07_postados antigos vão para _arquivo (o vigia não relê para sempre) ----
    def arquivar_postados(self) -> list[str]:
        dias = int(self.cfg.arquivar_postados_dias or 0)
        if dias <= 0:
            return []
        limite = hp_agora() - timedelta(days=dias)
        pasta = self.cfg.pasta(POSTADOS)
        feitos = []
        for item in listar(pasta):
            fim = ler_estado(item).get("concluido_em")
            try:
                quando = datetime.fromisoformat(fim) if fim else None
            except ValueError:
                quando = None
            if quando is None or quando.tzinfo is None or quando > limite:
                continue
            destino = pasta / "_arquivo" / quando.strftime("%Y-%m")
            mover(item, destino, nome_livre(destino, item.name) if destino.exists() else None)
            feitos.append(item.name)
        return feitos

    # --- pedidos soltos e pastas fora do padrão em 01_pedidos -------------------
    def importar_pedidos_soltos(self) -> list[str]:
        """O Claude pode largar só um .json em 01_pedidos: vira item aqui.
        Pasta criada à mão com nome fora do padrão ganha o nome certo."""
        pasta = self.cfg.pasta(PEDIDOS)
        feitos: list[str] = []
        if not pasta.exists():
            return feitos
        for p in sorted(pasta.iterdir()):
            if p.name.startswith(".criando_") and p.is_dir():
                if time.time() - p.stat().st_mtime > CRIANDO_VELHO_SEG:
                    shutil.rmtree(p, ignore_errors=True)
                continue
            if p.name.startswith((".", "_")):
                continue
            if p.is_file() and p.suffix.lower() == ".json":
                feitos.extend(self._importar_json(p))
            elif eh_item(p) and ler_nome(p.name) is None:
                feitos.extend(self._renomear_pasta(p))
        return feitos

    def _importar_json(self, arq: Path) -> list[str]:
        try:
            dados = ler_json(arq)
            try:
                novo = criar_pedido(dados, raiz=self.cfg.raiz)
            except PedidoInvalido:
                ja = self._ja_importado(dados)
                if ja is None:
                    raise
                novo = ja
            os.replace(arq, novo / "pedido_original.json")
            return [novo.name]
        except Exception as e:  # noqa: BLE001
            self._erro_de_entrada(arq, f"pedido solto {arq.name} inválido: {e}")
            return []

    def _ja_importado(self, dados: dict) -> Path | None:
        """Queda entre criar a pasta e tirar o .json solto: completa sem duplicar."""
        try:
            nome = nome_do_item(normalizar_pedido(dados))
        except Exception:  # noqa: BLE001
            return None
        cand = self.cfg.pasta(PEDIDOS) / nome
        if cand.exists() and not (cand / "pedido_original.json").exists():
            atual = ler_json(cand / ARQ_PEDIDO, {}) or {}
            if atual.get("id") == normalizar_pedido(dados).get("id"):
                return cand
        return None

    def _renomear_pasta(self, p: Path) -> list[str]:
        try:
            pedido = ler_pedido(p)
            nome = nome_do_item(pedido)
            destino = p.parent / nome
            if destino.exists():
                raise PedidoInvalido(f"já existe {nome}")
            os.replace(p, destino)
            historico(destino, f"[{PEDIDOS}] pasta '{p.name}' renomeada para o padrão")
            return [nome]
        except Exception as e:  # noqa: BLE001
            self._erro_de_entrada(p, f"pasta {p.name} em 01_pedidos inválida: {e}")
            return []

    def _erro_de_entrada(self, origem: Path, mensagem: str) -> None:
        erros = self.cfg.pasta(ERROS)
        base = origem.stem if origem.is_file() else origem.name
        nome = nome_livre(erros, f"entrada_invalida_{base}")
        if origem.is_dir():
            os.replace(origem, erros / nome)
            alvo = erros / nome
        else:
            alvo = erros / nome
            alvo.mkdir(parents=True)
            os.replace(origem, alvo / origem.name)
        escrever_json(alvo / ARQ_ERRO, {"etapa": PEDIDOS, "trabalho": "importar",
                                        "mensagem": mensagem, "traceback": "",
                                        "tentativas": 1, "permanente": True,
                                        "em": agora_iso()})
        historico(alvo, f"[{PEDIDOS}] -> {ERROS}: {mensagem}")
        self.log.error(mensagem)
