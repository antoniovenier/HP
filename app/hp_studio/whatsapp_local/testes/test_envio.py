"""Envio real (com o navegador falso): cabeçalho, ritmo, tentativas, login."""
import json
import os
import time
from datetime import datetime

from whatsapp_local.config import (GRUPO_COMISSAO, PREFIXO, Config, arquivo_estado,
                                   arquivo_ritmo, arquivo_trava, pasta_fila)
from whatsapp_local.enviador import Enviador, mesmo_texto
from whatsapp_local.navegador import NavegadorIndisponivel
from whatsapp_local.navegador_falso import NavegadorFalso

from .auxiliares import GRUPO_GTA, fabrica_de


def _pendentes():
    return sorted(p.name for p in pasta_fila().glob("*.json"))


def _ler(p):
    return json.loads(p.read_text(encoding="utf-8"))


def _nav(**kw):
    return NavegadorFalso({GRUPO_COMISSAO: [], GRUPO_GTA: []}, **kw)


def test_envia_confere_cabecalho_e_move_para_enviadas(grupos, enfileirar, relogio, cfg_real):
    d = enfileirar(ident="m1")
    nav = _nav()
    res = Enviador(cfg_real, fabrica_de(nav), relogio).ciclo("real", ler_todos_grupos=False)
    assert res.enviadas == 1 and res.falhas == 0
    assert nav.enviadas == [{"grupo": GRUPO_COMISSAO, "texto": d["texto"], "anexos": []}]
    ordem = nav.nomes_chamadas()
    assert ordem.index("abrir_conversa") < ordem.index("titulo_conversa") < ordem.index("enviar_texto")
    assert ordem[-1] == "fechar"
    enviada = _ler(pasta_fila() / "enviadas" / "m1.json")
    assert enviada["enviado_em"] == "2026-09-30T10:00:00-03:00" and enviada["tentativas"] == 1
    assert _pendentes() == []


def test_cabecalho_divergente_nao_envia(grupos, enfileirar, relogio, cfg_real):
    enfileirar(ident="m1")
    # a busca abriu uma conversa parecida, mas não a certa
    nav = _nav(titulos={GRUPO_COMISSAO: "HP | Comissão"})
    res = Enviador(cfg_real, fabrica_de(nav), relogio).ciclo("real", ler_todos_grupos=False)
    assert res.enviadas == 0 and res.falhas == 1
    assert "enviar_texto" not in nav.nomes_chamadas() and nav.enviadas == []
    dados = _ler(pasta_fila() / "m1.json")
    assert dados["tentativas"] == 1 and "CabecalhoDivergente" in dados["ultimo_erro"]
    # nada registrado no ritmo: não houve envio
    assert not arquivo_ritmo().exists() or _ler(arquivo_ritmo())["envios"] == []


def test_cabecalho_com_emoji_faltando_nao_passa(grupos, enfileirar, relogio, cfg_real):
    enfileirar(ident="m1")
    nav = _nav(titulos={GRUPO_COMISSAO: "HP | Comissão "})   # o emoji sumiu
    Enviador(cfg_real, fabrica_de(nav), relogio).ciclo("real", ler_todos_grupos=False)
    assert nav.enviadas == []


def test_contato_individual_nao_recebe(grupos, enfileirar, relogio, cfg_real):
    enfileirar(ident="m1", grupo=GRUPO_GTA)
    nav = _nav(tipos={GRUPO_GTA: False})
    res = Enviador(cfg_real, fabrica_de(nav), relogio).ciclo("real", ler_todos_grupos=False)
    assert res.falhas == 1 and nav.enviadas == []
    assert "NaoEGrupo" in _ler(pasta_fila() / "m1.json")["ultimo_erro"]


def test_ritmo_minimo_20s_entre_mensagens(grupos, enfileirar, relogio):
    for i in range(3):
        enfileirar(ident=f"m{i}", criado_em=f"2026-09-30T09:0{i}:00-03:00")
    cfg = Config(modo="real", ler_recebidas=False, intervalo_min_seg=5)  # 5 vira 20
    nav = _nav()
    res = Enviador(cfg, fabrica_de(nav), relogio).ciclo("real", ler_todos_grupos=False)
    assert res.enviadas == 3
    assert relogio.dormidas == [20.0, 20.0]
    envios = [datetime.fromisoformat(s) for s in _ler(arquivo_ritmo())["envios"]]
    assert [(b - a).total_seconds() for a, b in zip(envios, envios[1:])] == [20.0, 20.0]
    assert [e["texto"].split("— ")[1] for e in nav.enviadas] == ["m0", "m1", "m2"]  # ordem da fila


def test_ritmo_vale_entre_processos(grupos, enfileirar, relogio, cfg_real):
    enfileirar(ident="a")
    Enviador(cfg_real, fabrica_de(_nav()), relogio).ciclo("real", ler_todos_grupos=False)
    relogio.avancar(seconds=5)
    enfileirar(ident="b")
    relogio.dormidas.clear()
    # outro processo (outro Enviador) lê o ritmo.json e espera o que falta
    res = Enviador(cfg_real, fabrica_de(_nav()), relogio).ciclo("real", ler_todos_grupos=False)
    assert res.enviadas == 1 and relogio.dormidas == [15.0]


def test_teto_por_hora(grupos, enfileirar, relogio):
    for i in range(4):
        enfileirar(ident=f"m{i}", criado_em=f"2026-09-30T09:0{i}:00-03:00")
    cfg = Config(modo="real", ler_recebidas=False, max_por_hora=2)
    nav = _nav()
    res = Enviador(cfg, fabrica_de(nav), relogio).ciclo("real", ler_todos_grupos=False)
    assert res.enviadas == 2 and res.adiadas == 2
    assert _pendentes() == ["m2.json", "m3.json"]
    assert max(relogio.dormidas) <= 20            # nunca dorme 1 hora esperando
    relogio.avancar(minutes=30)
    res = Enviador(cfg, fabrica_de(nav), relogio).ciclo("real", ler_todos_grupos=False)
    assert res.enviadas == 0 and res.adiadas == 2    # ainda dentro da hora
    relogio.avancar(minutes=31)
    res = Enviador(cfg, fabrica_de(nav), relogio).ciclo("real", ler_todos_grupos=False)
    assert res.enviadas == 2 and _pendentes() == []


def test_tres_tentativas_vai_para_erros(grupos, enfileirar, relogio, cfg_real):
    enfileirar(ident="m1")
    nav = _nav(falhas_envio=99)
    for n in (1, 2):
        res = Enviador(cfg_real, fabrica_de(nav), relogio).ciclo("real", ler_todos_grupos=False)
        assert res.falhas == 1 and res.para_erros == 0
        assert _ler(pasta_fila() / "m1.json")["tentativas"] == n
        relogio.avancar(minutes=5)
    res = Enviador(cfg_real, fabrica_de(nav), relogio).ciclo("real", ler_todos_grupos=False)
    assert res.para_erros == 1 and _pendentes() == []
    erro = _ler(pasta_fila() / "erros" / "m1.json")
    assert erro["tentativas"] == 3 and len(erro["historico"]) == 3
    assert "ErroEnvio" in erro["erro_final"] and erro["erro_em"]
    assert nav.enviadas == []


def test_falha_uma_vez_e_depois_envia(grupos, enfileirar, relogio, cfg_real):
    enfileirar(ident="m1")
    nav = _nav(falhas_envio=1)
    Enviador(cfg_real, fabrica_de(nav), relogio).ciclo("real", ler_todos_grupos=False)
    relogio.avancar(minutes=1)
    res = Enviador(cfg_real, fabrica_de(nav), relogio).ciclo("real", ler_todos_grupos=False)
    assert res.enviadas == 1
    assert _ler(pasta_fila() / "enviadas" / "m1.json")["tentativas"] == 2


def test_retentativa_nao_duplica_quando_o_envio_anterior_saiu(grupos, enfileirar, relogio, cfg_real):
    enfileirar(ident="m1")
    nav = _nav(falhas_envio=1, falha_depois_de_enviar=True)   # saiu mas não confirmou
    Enviador(cfg_real, fabrica_de(nav), relogio).ciclo("real", ler_todos_grupos=False)
    assert len(nav.enviadas) == 1
    relogio.avancar(minutes=1)
    res = Enviador(cfg_real, fabrica_de(nav), relogio).ciclo("real", ler_todos_grupos=False)
    assert res.enviadas == 1
    assert len(nav.enviadas) == 1                 # não mandou de novo
    assert "não reenviado" in _ler(pasta_fila() / "enviadas" / "m1.json")["obs"]


def test_mesmo_texto_como_aparece_na_tela():
    enviado = f"{PREFIXO} 🚀 No ar agora\n\nInstagram: https://x"
    assert mesmo_texto("Claude - 🚀 No ar agora Instagram: https://x", enviado)
    assert not mesmo_texto("Claude - outra coisa", enviado)
    longo = f"{PREFIXO} " + "palavra " * 100
    assert mesmo_texto("Claude - " + "palavra " * 30 + "... Ler mais", longo)


def test_sem_login_nao_toca_na_fila(grupos, enfileirar, relogio, cfg_real):
    enfileirar(ident="m1")
    nav = _nav(esta_logado=False)
    res = Enviador(cfg_real, fabrica_de(nav), relogio).ciclo("real", ler_todos_grupos=False)
    assert res.precisa_login and res.enviadas == 0
    assert "tentativas" not in _ler(pasta_fila() / "m1.json")
    assert _ler(arquivo_estado())["precisa_login"] is True
    assert "abrir_conversa" not in nav.nomes_chamadas() and nav.nomes_chamadas()[-1] == "fechar"


def test_navegador_que_nao_abre_nao_gasta_tentativa(grupos, enfileirar, relogio, cfg_real):
    enfileirar(ident="m1")

    class NaoAbre(NavegadorFalso):
        def abrir(self):
            raise NavegadorIndisponivel("Playwright não instalado")

    res = Enviador(cfg_real, fabrica_de(NaoAbre()), relogio).ciclo("real", ler_todos_grupos=False)
    assert "Playwright" in res.erro
    assert "tentativas" not in _ler(pasta_fila() / "m1.json")


def test_id_repetido_depois_de_enviado_e_rejeitado(grupos, enfileirar, relogio, cfg_real):
    enfileirar(ident="m1")
    nav = _nav()
    Enviador(cfg_real, fabrica_de(nav), relogio).ciclo("real", ler_todos_grupos=False)
    enfileirar(ident="m1")
    res = Enviador(cfg_real, fabrica_de(nav), relogio).ciclo("real", ler_todos_grupos=False)
    assert res.rejeitadas == 1 and len(nav.enviadas) == 1
    assert "duplicado" in _ler(pasta_fila() / "rejeitadas" / "m1.json")["motivo_rejeicao"]


def test_anexo_vai_com_o_texto_de_legenda(grupos, enfileirar, relogio, cfg_real, tmp_path):
    capa = tmp_path / "capa.jpg"
    capa.write_bytes(b"x")
    d = enfileirar(ident="m1", anexos=[str(capa)])
    nav = _nav()
    Enviador(cfg_real, fabrica_de(nav), relogio).ciclo("real", ler_todos_grupos=False)
    assert "enviar_texto" not in nav.nomes_chamadas()
    assert nav.enviadas == [{"grupo": GRUPO_COMISSAO, "texto": d["texto"], "anexos": [str(capa)]}]


def test_texto_longo_vai_separado_do_anexo_com_intervalo(grupos, enfileirar, relogio, cfg_real, tmp_path):
    capa = tmp_path / "capa.jpg"
    capa.write_bytes(b"x")
    texto = f"{PREFIXO} " + "a" * 1500
    enfileirar(ident="m1", texto=texto, anexos=[str(capa)])
    nav = _nav()
    Enviador(cfg_real, fabrica_de(nav), relogio).ciclo("real", ler_todos_grupos=False)
    assert [e["texto"] for e in nav.enviadas][0] == texto
    assert nav.enviadas[1]["texto"].startswith(PREFIXO) and nav.enviadas[1]["anexos"] == [str(capa)]
    assert relogio.dormidas == [20.0]


def test_outro_processo_rodando_nao_mexe_em_nada(grupos, enfileirar, relogio, cfg_real):
    enfileirar(ident="m1")
    arquivo_trava().parent.mkdir(parents=True, exist_ok=True)
    arquivo_trava().write_text(json.dumps({"dono": "whatsapp:vigia", "pid": os.getpid(),
                                           "desde": time.time()}), encoding="utf-8")
    nav = _nav()
    res = Enviador(cfg_real, fabrica_de(nav), relogio).ciclo("real", ler_todos_grupos=False)
    assert "outro processo" in res.erro and nav.chamadas == []
    assert _pendentes() == ["m1.json"]


def test_fila_vazia_nao_abre_janela(grupos, relogio, cfg_real):
    nav = _nav()
    res = Enviador(cfg_real, fabrica_de(nav), relogio).ciclo("real", ler_todos_grupos=False)
    assert res.erro is None and nav.chamadas == []


def test_ordem_pela_data_de_criacao(grupos, enfileirar, relogio, cfg_real):
    enfileirar(ident="zz_primeira", criado_em="2026-09-30T08:00:00-03:00")
    enfileirar(ident="aa_segunda", criado_em="2026-09-30T08:30:00-03:00")
    nav = _nav()
    Enviador(cfg_real, fabrica_de(nav), relogio).ciclo("real", ler_todos_grupos=False)
    assert [e["texto"].split("— ")[1] for e in nav.enviadas] == ["zz_primeira", "aa_segunda"]
