"""O enviador: 1 ciclo = validar a fila → (sombra) comparar | (real) enviar.

Modo SOMBRA (padrão): valida, move as válidas para whatsapp_sombra\\app\\ e
refaz o relatório de diferenças com o plantão. NUNCA abre o navegador.

Modo REAL, para cada mensagem válida:
  1. espera a vez (≥ 20 s desde a última; teto por hora — senão fica para o
     próximo ciclo);
  2. abre a conversa pela busca e confere o CABEÇALHO: título exatamente
     igual ao grupo (Unicode NFC) e não é contato individual — se não bater,
     NÃO envia (conta 1 tentativa);
  3. na retentativa, antes de reenviar, olha se a mensagem já está na
     conversa (evita duplicar quando o envio anterior saiu mas não confirmou);
  4. envia; deu certo → enviadas\\; falhou 3 vezes → erros\\;
  5. lê as últimas mensagens do grupo e salva as do Antônio (recebidas).
Sem login (apareceu o QR) ou sem navegador: nada é tocado na fila.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import timedelta

from hpbase import (TravaOcupada, TravaPesada, escrever_json, ler_json,
                    obter_logger)

from .config import (LIMITE_LEGENDA, PREFIXO, Config, arquivo_estado,
                     arquivo_trava, carregar_config, carregar_grupos_permitidos,
                     nfc, pasta_perfil)
from .fila import Fila, ItemFila
from .fila_pc import pronta_para_enviar, validar_enviar_apos
from .montagem import ler_datahora
from .navegador import (CabecalhoDivergente, NaoEGrupo, Navegador,
                        NavegadorIndisponivel)
from .recebidas import ArquivoRecebidas, hash_curto
from .ritmo import ControleRitmo, Relogio
from .sombra import gerar_relatorio
from .tarefas import tarefas_automaticas
from .validacao import resolver_anexo, validar_mensagem

_FORMATACAO = re.compile(r"[*_~]")
_LER_MAIS = re.compile(r"\s*(…|\.\.\.)?\s*(ler mais|read more)\s*$", re.I)


def _comparavel(t: str) -> str:
    t = re.sub(r"\s+", " ", _FORMATACAO.sub("", nfc(t))).strip()
    return _LER_MAIS.sub("", t).rstrip("… ").strip()


def mesmo_texto(lido: str, enviado: str) -> bool:
    """O texto lido da tela é o mesmo que mandamos? (a tela tira os * do
    negrito e corta mensagem longa com "Ler mais")."""
    a, b = _comparavel(lido), _comparavel(enviado)
    if not a:
        return False
    return a == b or (len(a) >= 150 and b.startswith(a))


def fabrica_padrao(cfg: Config, visivel: bool = False) -> Navegador:
    """Navegador real (o Playwright só é importado quando abrir)."""
    from .navegador_playwright import NavegadorPlaywright
    return NavegadorPlaywright(pasta_perfil(), visivel=visivel, canal=cfg.canal_navegador,
                               minimizar=cfg.minimizar_janela)


@dataclass
class ResultadoCiclo:
    modo: str
    enviadas: int = 0
    rejeitadas: int = 0
    falhas: int = 0
    para_erros: int = 0
    adiadas: int = 0
    sombra: int = 0
    montadas: int = 0
    recebidas_novas: int = 0
    precisa_login: bool = False
    erro: str | None = None
    relatorios: list = field(default_factory=list)

    def como_dict(self) -> dict:
        return asdict(self)

    def resumo(self) -> str:
        partes = [f"modo {self.modo}"]
        for nome in ("montadas", "enviadas", "sombra", "rejeitadas", "falhas",
                     "para_erros", "adiadas", "recebidas_novas"):
            v = getattr(self, nome)
            if v:
                partes.append(f"{nome.replace('_', ' ')}: {v}")
        if self.precisa_login:
            partes.append("PRECISA LOGIN (rode: python -m whatsapp_local login)")
        if self.erro:
            partes.append(f"erro: {self.erro}")
        return " · ".join(partes)


class Enviador:
    def __init__(self, cfg: Config | None = None, fabrica_navegador=None,
                 relogio: Relogio | None = None, fila: Fila | None = None):
        self.cfg = cfg or carregar_config()
        self.fabrica = fabrica_navegador or fabrica_padrao
        self.relogio = relogio or Relogio()
        self.fila = fila or Fila()
        self.ritmo = ControleRitmo(self.relogio, self.cfg.intervalo_min_seg,
                                   self.cfg.max_por_hora)
        self.recebidas = ArquivoRecebidas()
        self.lg = obter_logger("whatsapp")

    # ------------------------------------------------------------ apoio
    def _agora_iso(self) -> str:
        return self.relogio.agora().isoformat(timespec="seconds")

    def modo(self, modo: str | None = None) -> str:
        return "real" if (modo or self.cfg.modo) == "real" else "sombra"

    @staticmethod
    def _trava(dono: str) -> TravaPesada:
        # Não é trabalho pesado: vale a qualquer hora, mas 1 processo por vez
        # (o perfil do navegador não pode ser aberto duas vezes).
        return TravaPesada(f"whatsapp:{dono}", caminho=arquivo_trava(), ignorar_horario=True)

    def estado(self) -> dict:
        return ler_json(arquivo_estado(), {}) or {}

    def _gravar_estado(self, **kw) -> None:
        d = self.estado()
        d.update(kw)
        escrever_json(arquivo_estado(), d)

    # ------------------------------------------------------------ ciclo
    def ciclo(self, modo: str | None = None, ler_todos_grupos: bool | None = None) -> ResultadoCiclo:
        modo = self.modo(modo)
        res = ResultadoCiclo(modo=modo)
        try:
            with self._trava("ciclo"):
                res.montadas = tarefas_automaticas(self.cfg, self.relogio.agora(), self.fila)
                validos = self._validar_fila(res)
                if modo == "sombra":
                    self._ciclo_sombra(validos, res)
                else:
                    if ler_todos_grupos is None:
                        ler_todos_grupos = self._hora_de_ler_todos()
                    self._ciclo_real(validos, res, ler_todos_grupos)
        except TravaOcupada:
            res.erro = "outro processo do WhatsApp está rodando (enviador.lock)"
        except NavegadorIndisponivel as e:
            res.erro = str(e)
        except Exception as e:  # o vigia nunca pode cair
            res.erro = f"{type(e).__name__}: {str(e)[:300]}"
            self.lg.exception("ciclo falhou")
        self._gravar_estado(ultimo_ciclo=self._agora_iso(), modo=modo,
                            ultimo_resultado=res.como_dict())
        self.lg.info("ciclo: %s", res.resumo())
        return res

    def _validar_fila(self, res: ResultadoCiclo) -> list[ItemFila]:
        self.fila.preparar()
        permitidos = carregar_grupos_permitidos()
        validos = []
        agora = self.relogio.agora()
        for item in self.fila.pendentes():
            motivos = [item.erro_leitura] if item.erro_leitura else \
                validar_mensagem(item.dados, permitidos) + validar_enviar_apos(item.dados)
            if not motivos and self.fila.ja_processada(item.id):
                motivos = [f"id '{item.id}' já foi enviado/processado antes (duplicado)"]
            if motivos:
                motivo = "; ".join(motivos)
                self.fila.rejeitar(item, motivo, self._agora_iso())
                res.rejeitadas += 1
                self.lg.warning("rejeitada: arquivo=%s motivo=%s", item.caminho.name, motivo)
                continue
            # §4.8: `enviar_apos` respeitado e de madrugada (0h-7h30) nada sai — fica na fila
            if not pronta_para_enviar(item.dados, agora):
                res.adiadas += 1
                self.lg.info("adiada: id=%s enviar_apos=%s", item.id, item.dados.get("enviar_apos"))
                continue
            validos.append(item)
        return validos

    # ----------------------------------------------------------- sombra
    def _ciclo_sombra(self, validos: list[ItemFila], res: ResultadoCiclo) -> None:
        agora = self.relogio.agora()
        dias = {agora.date(), (agora - timedelta(days=1)).date()}
        for item in validos:
            d = item.dados
            self.fila.para_sombra(item, self._agora_iso())
            res.sombra += 1
            criado = ler_datahora(d.get("criado_em"))
            if criado:
                dias.add(criado.date())
            self.lg.info("sombra (não enviada): id=%s tipo=%s grupo=%s tamanho=%d",
                         item.id, d.get("tipo"), nfc(d.get("grupo")), len(d.get("texto", "")))
        for dia in sorted(dias):
            arq = gerar_relatorio(dia, self._agora_iso(), pular_vazio=True)
            if arq:
                res.relatorios.append(str(arq))

    # ------------------------------------------------------------- real
    def _hora_de_ler_todos(self) -> bool:
        if not self.cfg.ler_recebidas:
            return False
        ult = ler_datahora(self.estado().get("ultima_leitura_recebidas"))
        return ult is None or self.relogio.agora() - ult >= timedelta(
            minutes=self.cfg.ler_recebidas_a_cada_min)

    def _ciclo_real(self, validos: list[ItemFila], res: ResultadoCiclo,
                    ler_todos: bool) -> None:
        if not validos and not ler_todos:
            return                        # nada a fazer: nem abre a janela
        nav = self.fabrica(self.cfg, visivel=False)
        nav.abrir()                       # NavegadorIndisponivel sobe: fila intacta
        try:
            if not nav.logado(self.cfg.timeout_carregar_seg):
                res.precisa_login = True
                self._gravar_estado(logado=False, precisa_login=True)
                self.lg.warning("WhatsApp Web sem login (QR na tela): "
                                "rode 'python -m whatsapp_local login'")
                return
            self._gravar_estado(logado=True, precisa_login=False)
            lidos: set[str] = set()
            for n, item in enumerate(validos):
                if not self.ritmo.esperar_vez():
                    res.adiadas = len(validos) - n
                    self.lg.info("teto de %d mensagens/hora: %d ficam para o próximo ciclo",
                                 self.ritmo.max_por_hora, res.adiadas)
                    break
                grupo = nfc(item.dados["grupo"])
                try:
                    obs = self._enviar_uma(nav, item)
                except Exception as e:
                    motivo = f"{type(e).__name__}: {str(e)[:300]}"
                    foi = self.fila.registrar_falha(item, motivo, self.cfg.max_tentativas,
                                                    self._agora_iso())
                    res.falhas += 1
                    res.para_erros += int(foi)
                    self.lg.warning("falhou: id=%s grupo=%s tentativa=%s motivo=%s%s",
                                    item.id, grupo, item.dados.get("tentativas"), motivo,
                                    " → erros" if foi else "")
                    continue
                self.fila.marcar_enviada(item, self._agora_iso(), obs)
                res.enviadas += 1
                self.lg.info("enviada: id=%s tipo=%s grupo=%s tamanho=%d%s", item.id,
                             item.dados.get("tipo"), grupo, len(item.dados["texto"]),
                             f" ({obs})" if obs else "")
                if self.cfg.ler_recebidas and grupo not in lidos:
                    res.recebidas_novas += self._salvar_conversa_aberta(nav, grupo)
                    lidos.add(grupo)
            if ler_todos:
                for grupo in carregar_grupos_permitidos():
                    if grupo in lidos:
                        continue
                    try:
                        self._abrir_e_conferir(nav, grupo)
                        res.recebidas_novas += self._salvar_conversa_aberta(nav, grupo)
                    except Exception as e:
                        self.lg.warning("não li as recebidas de %s: %s", grupo, type(e).__name__)
                self._gravar_estado(ultima_leitura_recebidas=self._agora_iso())
        finally:
            nav.fechar()

    @staticmethod
    def _titulo_para_log(titulo: str) -> str:
        """Nome de conversa que não é grupo HP não vai para o log (só um hash)."""
        t = nfc(titulo)
        if not t:
            return "(vazio)"
        return f"'{t[:60]}'" if t.upper().startswith("HP") else f"outra conversa (hash {hash_curto(t)})"

    def _abrir_e_conferir(self, nav: Navegador, grupo: str) -> None:
        """Abre pela busca e confere o cabeçalho. Levanta se não bater."""
        nav.abrir_conversa(grupo)
        titulo = nav.titulo_conversa()
        if nfc(titulo) != nfc(grupo):
            raise CabecalhoDivergente(
                f"cabeçalho da conversa {self._titulo_para_log(titulo)} diferente do grupo "
                f"'{nfc(grupo)}'; nada enviado")
        if nav.conversa_e_grupo() is False:
            raise NaoEGrupo(f"'{nfc(grupo)}' parece contato individual; nada enviado")

    def _ja_consta(self, nav: Navegador, texto: str) -> bool:
        try:
            msgs = nav.ler_mensagens(self.cfg.ultimas_mensagens)
        except Exception:
            return False
        return any(m.saida and mesmo_texto(m.texto, texto) for m in msgs)

    def _enviar_uma(self, nav: Navegador, item: ItemFila) -> str | None:
        dados = item.dados
        grupo = nfc(dados["grupo"])
        texto = dados["texto"]
        anexos = [resolver_anexo(a) for a in (dados.get("anexos") or [])]
        junto = bool(anexos) and len(texto) <= LIMITE_LEGENDA   # texto vira legenda
        self._abrir_e_conferir(nav, grupo)

        texto_ja = bool(dados.get("texto_ja_enviado"))
        if int(dados.get("tentativas", 0) or 0) > 0 and not texto_ja \
                and self._ja_consta(nav, texto):
            if not anexos or junto:
                return "já estava na conversa (tentativa anterior saiu); não reenviado"
            texto_ja = True

        if junto:
            self.ritmo.registrar_envio()
            nav.enviar_anexos(anexos, texto)
            return None
        if not texto_ja:
            self.ritmo.registrar_envio()
            nav.enviar_texto(texto)
            dados["texto_ja_enviado"] = True     # se o anexo falhar, não repete o texto
        if anexos:
            self.relogio.dormir(self.ritmo.intervalo)
            if nfc(nav.titulo_conversa()) != grupo:
                raise CabecalhoDivergente("cabeçalho mudou antes do anexo; anexo não enviado")
            self.ritmo.registrar_envio()
            nav.enviar_anexos(anexos, f"{PREFIXO} 📎 anexo")
        return None

    def _salvar_conversa_aberta(self, nav: Navegador, grupo: str) -> int:
        try:
            msgs = nav.ler_mensagens(self.cfg.ultimas_mensagens)
        except Exception as e:
            self.lg.warning("não li as mensagens de %s: %s", grupo, type(e).__name__)
            return 0
        return self.recebidas.salvar(grupo, msgs, self.relogio.agora())

    # ---------------------------------------------------- outros comandos
    def ler_recebidas(self, modo: str | None = None) -> ResultadoCiclo:
        """Passa em todos os grupos permitidos e salva as mensagens novas.
        Em sombra não abre o navegador (só devolve o resultado vazio)."""
        modo = self.modo(modo)
        res = ResultadoCiclo(modo=modo)
        if modo == "sombra":
            return res
        try:
            with self._trava("ler_recebidas"):
                self._ciclo_real([], res, ler_todos=True)
        except TravaOcupada:
            res.erro = "outro processo do WhatsApp está rodando (enviador.lock)"
        except NavegadorIndisponivel as e:
            res.erro = str(e)
        self.lg.info("ler-recebidas: %s", res.resumo())
        return res

    def login(self, timeout_s: float | None = None, avisar=print) -> bool:
        """Abre VISÍVEL e espera o Antônio escanear o QR. Não digita nada."""
        with self._trava("login"):
            nav = self.fabrica(self.cfg, visivel=True)
            nav.abrir()
            try:
                if nav.logado(min(60, self.cfg.timeout_carregar_seg)):
                    ok = True
                    avisar("Já está logado. Nada a fazer.")
                else:
                    avisar("Abri o WhatsApp Web. No celular: WhatsApp > Configurações > "
                           "Aparelhos conectados > Conectar um aparelho, e aponte para o QR "
                           f"da tela. Esperando até {int(timeout_s or self.cfg.timeout_login_seg)} s...")
                    ok = nav.esperar_login(timeout_s or self.cfg.timeout_login_seg)
            finally:
                nav.fechar()
        self._gravar_estado(logado=ok, precisa_login=not ok, ultimo_login=self._agora_iso())
        self.lg.info("login: %s", "ok" if ok else "não concluído")
        return ok
