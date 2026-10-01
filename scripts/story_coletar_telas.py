# -*- coding: utf-8 -*-
"""story_coletar_telas.py — coleta assistida das telas reais do Instagram (tarefa E4), para leigo.

O que faz: um roteiro passo a passo. Para cada tela da lista, o script imprime a instrução ("Abra o
perfil da conta e aperte ENTER"), ESPERA o ENTER, e só então roda `uiautomator dump` e `screencap`
no aparelho, gravando H:\\HypadoLocal\\android\\telas\\coleta\\<NN>_<nome>.xml e .png e o índice
coleta.json. Quem navega no celular é o Antônio (ou o Diretor); o script NUNCA toca em nada, NUNCA
digita, NUNCA abre app ou link — só lê a tela e tira a foto. Se vir tela de login, pedido de código,
termos ou aviso da Meta, para (código 3) sem tocar em nada e nunca pede senha.

Para que serve: os dumps reais substituem as telas SINTÉTICAS de tests/fixtures/android/ (nome com
"sintetico") e confirmam os seletores que ainda são palpite (A_CONFIRMAR do story_post_seletores.py
e IDS_PALPITE do story_fluxos.py). Cada tela da lista diz quais chaves ela confirma; o índice anota,
para cada tela, quais ids/textos apareceram de verdade.

Uso:
  python scripts\\story_coletar_telas.py [--serial S | --emulador | --celular] [--pasta H:\\...\\coleta]
  python scripts\\story_coletar_telas.py --simular          (imprime o roteiro; não chama o adb)
  python scripts\\story_coletar_telas.py --so 05            (só a tela 05; pode repetir)
Durante a coleta: ENTER grava a tela; escrever "pular" pula a tela; "sair" encerra (o que já foi gravado fica).
Códigos de saída: 0 ok · 1 erro · 3 parou por login/aviso da Meta · 4 aparelho bloqueado / precisa do Antônio.
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable

AQUI = Path(__file__).resolve().parent
if str(AQUI) not in sys.path:
    sys.path.insert(0, str(AQUI))

import story_dispositivo as sd  # noqa: E402
import story_post_seletores as SEL  # noqa: E402
from hpbase import FUSO, escrever_json, raiz_local  # noqa: E402

OK, ERRO, BLOQUEADO, AVISO_META, PRECISA_ANTONIO = 0, 1, 2, 3, 4
ARQUIVO_INDICE = "coleta.json"
COMANDOS_PERMITIDOS = ("uiautomator", "cat", "screencap", "wm", "dumpsys", "getprop", "mkdir")   # nada de input/am/monkey

# As 12 telas da tarefa E4, na ordem em que se chega a elas no app, as chaves do story_post_seletores.py
# (A_CONFIRMAR) / IDS_PALPITE do story_fluxos.py que cada uma confirma e a tela SINTÉTICA de
# tests/fixtures/android/ (adb_falso.py do E1) que o dump real substitui (None = o E1 não inventou essa tela).
TELAS = [
    {"nome": "perfil_proprio", "sintetica": "perfil",
     "instrucao": "Abra o Instagram na conta certa (ex.: @hp.futebol) e toque na aba Perfil (o boneco, embaixo à direita). "
                  "Deixe o perfil inteiro à vista, com o nome da conta lá em cima.",
     "confirma": ["aba_perfil", "conta_container", "conta_titulo", "avatar_perfil", "grade_item", "criar"]},
    {"nome": "menu_mais", "sintetica": None,
     "instrucao": "No perfil, toque no + (criar) lá em cima. Deixe o menu aberto (Reel, Publicação, Story...). "
                  "NÃO escolha nada ainda.",
     "confirma": ["criar", "menu_story"]},
    {"nome": "galeria", "sintetica": "galeria",
     "instrucao": "Toque em Story. Se abrir a câmera, toque na miniatura da galeria (canto inferior esquerdo) até ver "
                  "a grade de fotos do aparelho.",
     "confirma": ["galeria", "galeria_item"]},
    {"nome": "editor_story", "sintetica": "editor",
     "instrucao": "Toque na foto mais recente. A arte abre no editor de story (ícones em cima: Aa, figurinhas, "
                  "rabisco). Deixe assim.",
     "confirma": ["figurinhas", "publicar_seu_story", "area_arte_editor"]},
    {"nome": "bandeja_figurinhas", "sintetica": "figurinhas",
     "instrucao": "Toque no ícone de figurinhas (carinha quadrada, em cima). A bandeja com ENQUETE, LINK, "
                  "CONTAGEM... abre.",
     "confirma": ["busca_figurinha", "figurinha_enquete", "figurinha_contagem", "figurinha_link", "bandeja_item"]},
    {"nome": "busca_link", "sintetica": None,
     "instrucao": "Toque na busca da bandeja e escreva a palavra link (só isso; não toque em mais nada).",
     "confirma": ["busca_figurinha"]},
    {"nome": "figurinha_link_aberta", "sintetica": "link",
     "instrucao": "Toque na figurinha LINK. O campo da URL aparece (e o de personalizar o texto). Não escreva nada.",
     "confirma": ["link_url", "link_rotulo", "link_rotulo_botao", "concluir"]},
    {"nome": "figurinha_enquete_aberta", "sintetica": "enquete",
     "instrucao": "Volte (seta), abra as figurinhas de novo e toque em ENQUETE (POLL). A pergunta e as opções "
                  "aparecem. Não escreva nada.",
     "confirma": ["enquete_pergunta", "enquete_opcao", "enquete_add_opcao", "concluir"]},
    {"nome": "botao_seu_story", "sintetica": "editor",
     "instrucao": "Toque em Concluir e volte ao editor com a arte: a barra de baixo mostra 'Seu story' / 'Your story' "
                  "e 'Amigos próximos'. NÃO toque em Seu story.",
     "confirma": ["publicar_seu_story"]},
    {"nome": "folha_envio_post", "sintetica": "folha_send",
     "instrucao": "Feche o editor (X e Descartar). Abra um post da própria conta (toque numa foto da grade) e toque "
                  "no aviãozinho (Enviar). A folha com 'Adicionar ao story' e a lista de amigos abre.",
     "confirma": ["compartilhar", "autor_post", "add_story", "folha_add_story"]},
    {"nome": "seletor_destaque", "sintetica": "destaques",
     "instrucao": "Feche a folha e volte ao perfil. Toque na foto do perfil para abrir o seu próprio story e toque em "
                  "Destaque (Highlight) embaixo. A lista de destaques (com 'Novo') abre. NÃO escolha nenhum.",
     "confirma": ["story_timestamp", "story_destaque", "titulo_story", "cabecalho_story", "midia_story",
                  "destaque_item", "destaque_novo", "destaque_ok"]},
    {"nome": "lista_contas", "sintetica": "lista_contas",
     "instrucao": "Volte ao perfil e toque no nome da conta lá em cima (abre a lista de contas logadas). "
                  "NÃO toque em 'Adicionar conta' nem em Entrar.",
     "confirma": ["conta_container", "lista_conta_linha"]},
]


def pasta_coleta_padrao() -> Path:
    return raiz_local() / "android" / "telas" / "coleta"


def nome_arquivo(n: int, nome: str, ext: str) -> str:
    return f"{n:02d}_{nome}.{ext}"


def tela_que_confirma(chave: str, telas: list | None = None) -> list:
    """['01_perfil_proprio', ...]: as telas da coleta que confirmam a chave (do seletores ou IDS_PALPITE)."""
    out = []
    for n, t in enumerate(telas or TELAS, 1):
        if chave in t["confirma"]:
            out.append(f"{n:02d}_{t['nome']}")
    return out


def alternativas_de(chave: str) -> tuple:
    """('id'|'texto', [alternativas]) da chave, no story_post_seletores ou no IDS_PALPITE do story_fluxos."""
    if chave in SEL.IDS:
        return "id", list(SEL.IDS[chave])
    if chave in SEL.TEXTOS:
        return "texto", list(SEL.TEXTOS[chave])
    try:
        import story_fluxos as sf  # só para a lista de palpites; nada roda
        if chave in sf.IDS_PALPITE:
            return "id", list(sf.IDS_PALPITE[chave])
        if chave in sf.TEXTOS_EXTRA:
            return "texto", list(sf.TEXTOS_EXTRA[chave])
    except ImportError:
        pass
    return "id", [chave]


def ids_vistos(nos: list, chaves: list) -> dict:
    """{chave: [alternativas que apareceram no dump]} — o que a tela confirmou de verdade."""
    out = {}
    for ch in chaves:
        tipo, alts = alternativas_de(ch)
        vistas = []
        for a in alts:
            if tipo == "id":
                achou = sd.achar_todos(nos, id=[a], visivel=False)
            else:
                achou = sd.achar_todos(nos, rotulo=[a], visivel=False)
            if achou:
                vistas.append(a)
        out[ch] = vistas
    return out


def resumo_ids(nos: list, limite: int = 60) -> list:
    """Os ids da tela (sem repetição, na ordem), para o índice."""
    vistos = []
    for n in nos:
        if n.id and n.id not in vistos:
            vistos.append(n.id)
    return vistos[:limite]


def coletar(disp, pasta, entrada: Callable | None = None, saida: Callable = print, telas: list | None = None,
            so: list | None = None, agora: Callable | None = None) -> tuple:
    """Roda o roteiro. Devolve (código, índice). Só `uiautomator dump`, `cat` e `screencap` vão ao aparelho."""
    telas = telas or TELAS
    entrada = entrada or input
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    quando = (agora() if agora else datetime.now(FUSO)).isoformat(timespec="seconds")
    W, H = disp.tamanho_tela()
    indice = {"serial": disp.serial, "tela": [W, H], "iniciado_em": quando, "pasta": str(pasta),
              "telas": [], "parado": None, "sinteticas_que_substitui": []}
    arq_indice = pasta / ARQUIVO_INDICE
    escrever_json(arq_indice, indice)
    codigo = OK
    saida(f"Coleta de telas em {pasta} (aparelho {disp.serial}, tela {W}x{H}).")
    saida("Eu NÃO toco em nada: você navega no celular, eu só leio a tela e tiro a foto quando você apertar ENTER.")
    saida("Escreva 'pular' para pular uma tela ou 'sair' para encerrar. Nunca escreva senha nem código aqui.")
    for n, t in enumerate(telas, 1):
        rotulo = f"{n:02d}_{t['nome']}"
        if so and n not in so and f"{n:02d}" not in so and t["nome"] not in so:
            continue
        saida("")
        saida(f"[{n}/{len(telas)}] {t['instrucao']}")
        saida("Quando a tela estiver assim, aperte ENTER.")
        resp = str(entrada() or "").strip().lower()
        if resp in ("sair", "q", "quit"):
            saida("encerrando a coleta (o que já foi gravado fica).")
            break
        if resp in ("pular", "p", "skip"):
            indice["telas"].append({"n": n, "nome": t["nome"], "pulada": True})
            escrever_json(arq_indice, indice)
            saida(f"pulei {rotulo}.")
            continue
        try:
            nos = disp.dump(checar_aviso=False)
            achado = sd.detectar_aviso(nos, disp.avisos_extra)
            if achado:
                frase, trecho = achado
                saida(f"PAREI em {rotulo}: a tela mostra '{frase}' ({trecho[:60]}). Não toco em nada e não peço senha. "
                      "Resolva no celular e rode de novo.")
                xml = pasta / nome_arquivo(n, t["nome"] + "_AVISO", "xml")
                xml.write_text(disp.ultimo_xml, encoding="utf-8")
                indice["parado"] = {"tela": rotulo, "frase": frase, "trecho": trecho[:300], "xml": xml.name}
                escrever_json(arq_indice, indice)
                disp.parar_por_aviso(nos, rotulo)          # grava a parada (função injetada) e levanta
                codigo = AVISO_META
                break
            xml = pasta / nome_arquivo(n, t["nome"], "xml")
            xml.write_text(disp.ultimo_xml, encoding="utf-8")
            png = disp.screencap(pasta / nome_arquivo(n, t["nome"], "png"))
        except sd.AvisoMetaDetectado:
            codigo = AVISO_META
            break
        vistos = ids_vistos(nos, t["confirma"])
        confirmadas = [k for k, v in vistos.items() if v]
        faltam = [k for k, v in vistos.items() if not v]
        item = {"n": n, "nome": t["nome"], "xml": xml.name, "png": png.name, "nos": len(nos),
                "confirma": t["confirma"], "vistos": vistos, "confirmadas": confirmadas, "faltam": faltam,
                "ids_da_tela": resumo_ids(nos)}
        indice["telas"].append(item)
        if t.get("sintetica"):                       # a tela inventada do E1 que este dump real substitui
            indice["sinteticas_que_substitui"].append(f"{t['sintetica']}_sintetico_{W}x{H}.xml")
        escrever_json(arq_indice, indice)
        saida(f"gravei {xml.name} e {png.name} ({len(nos)} elementos). Confirmados: {', '.join(confirmadas) or 'nenhum'}"
              + (f"; não vi: {', '.join(faltam)}" if faltam else ""))
    indice["terminado_em"] = (agora() if agora else datetime.now(FUSO)).isoformat(timespec="seconds")
    indice["codigo"] = codigo
    escrever_json(arq_indice, indice)
    saida("")
    saida(f"índice: {arq_indice} ({len(indice['telas'])} telas; código {codigo})")
    return codigo, indice


def comandos_fora_da_lista(historico: list) -> list:
    """Comandos adb do histórico que NÃO são só leitura (para o teste provar que a coleta não toca em nada)."""
    ruins = []
    for argv in historico:
        resto = [str(a) for a in argv][1:]
        if resto[:1] == ["-s"]:
            resto = resto[2:]
        if not resto:
            continue
        if resto[0] == "shell":
            if resto[1:2] and resto[1] not in COMANDOS_PERMITIDOS:
                ruins.append(" ".join(resto[1:]))
        elif resto[0] not in ("devices", "pull"):
            ruins.append(" ".join(resto))
    return ruins


def _argumentos(argv) -> argparse.Namespace:
    ap = argparse.ArgumentParser(prog="python scripts\\story_coletar_telas.py",
                                 description="Coleta assistida das telas do Instagram (só dump e foto; nenhum toque).")
    ap.add_argument("--serial")
    ap.add_argument("--emulador", action="store_true")
    ap.add_argument("--celular", action="store_true")
    ap.add_argument("--pasta", help="padrão: H:\\HypadoLocal\\android\\telas\\coleta")
    ap.add_argument("--adb", help="caminho do adb.exe (padrão: HP_ADB ou o do PC)")
    ap.add_argument("--so", action="append", default=[], help="só estas telas (número NN ou nome); pode repetir")
    ap.add_argument("--simular", action="store_true", help="imprime o roteiro; não chama o adb nem espera ENTER")
    return ap.parse_args(argv)


def main(argv=None, saida: Callable = print, entrada: Callable | None = None, runner: Callable | None = None,
         env=None) -> int:
    args = _argumentos(argv)
    pasta = Path(args.pasta) if args.pasta else pasta_coleta_padrao()
    log = logging.getLogger("hp.story_coletar_telas")
    try:
        if args.simular:
            saida("== SIMULAÇÃO: nada é lido do aparelho; este é o roteiro ==")
            runner = runner or sd.runner_roteiro(saida)
            serial = args.serial or "emulator-5554"
            entrada = entrada or (lambda: "")
            disp = sd.Dispositivo(runner, serial, log=log)
        else:
            runner = runner or sd.runner_real(args.adb or sd.achar_adb())
            pref = "emulador" if args.emulador else ("celular" if args.celular else None)
            serial = sd.escolher_serial(runner, args.serial, env=env, preferencia=pref)
            disp = sd.Dispositivo(runner, serial, log=log, gravar_parada=sd.gravar_parada_padrao())
            disp.tela_acesa_e_destravada(tentar=False)       # bloqueado -> código 4; sem acordar, sem PIN
        so = [s.strip() for s in args.so if s.strip()]
        codigo, _ = coletar(disp, pasta, entrada=entrada, saida=saida, so=so or None)
        return int(codigo)
    except sd.AvisoMetaDetectado as e:
        saida(f"PARADO: {e}")
        return AVISO_META
    except sd.DispositivoErro as e:
        saida(f"{type(e).__name__}: {e}")
        return int(getattr(e, "codigo", ERRO))


if __name__ == "__main__":
    raise SystemExit(main())
