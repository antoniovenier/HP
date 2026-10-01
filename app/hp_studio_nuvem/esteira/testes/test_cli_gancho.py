"""Linha de comando (python -m esteira ...) e gancho do motor do HP Studio."""
import json

import pytest
from hpbase import ler_json

import esteira.motor
import hpbase.trava
from esteira import gancho, vigia
from esteira.cli import main
from esteira.constantes import AGENDADOS, PEDIDOS, POSTADOS, REVISAO
from esteira.testes.conftest import pedido_reel


@pytest.fixture
def sem_janela(monkeypatch):
    """A CLI usa o relógio de verdade: tira a janela 18h-22h30 do caminho."""
    monkeypatch.setattr(esteira.motor, "janela_proibida", lambda *a, **k: False)
    monkeypatch.setattr(hpbase.trava, "janela_proibida", lambda *a, **k: False)


def rodar(capsys, *args):
    codigo = main(list(args))
    saida = capsys.readouterr()
    return codigo, saida.out, saida.err


def test_help_em_portugues(capsys):
    with pytest.raises(SystemExit) as e:
        main(["--help"])
    assert e.value.code == 0
    out = capsys.readouterr().out
    assert "uso:" in out and "opções:" in out and "comandos:" in out
    assert rodar(capsys, )[0] == 2  # sem comando: mostra ajuda


def test_cli_fluxo_completo_simulado(capsys, tmp_path, sem_janela):
    assert rodar(capsys, "iniciar")[0] == 0
    arq = tmp_path / "pedido.json"
    arq.write_text(json.dumps(pedido_reel()), encoding="utf-8")
    c, out, _ = rodar(capsys, "pedido", "--json", str(arq))
    assert c == 0 and "P1_2026-09-30_1830_gta_rockstar-quinta" in out
    c, out, _ = rodar(capsys, "--simular", "ciclo")
    assert c == 0 and "05_revisao" in out
    c, out, _ = rodar(capsys, "status")
    assert "05_revisao" in out and "rockstar-quinta" in out and "aguardando" in out
    c, out, _ = rodar(capsys, "aprovar", "rockstar", "--notas", "gancho=9", "legenda=8,5",
                      "--simular")
    assert c == 0 and "Bom" in out
    rodar(capsys, "ciclo", "--simular")
    c, out, _ = rodar(capsys, "tiktok-ok", "rockstar", "--link", "https://tiktok.com/1",
                      "--simular")
    assert c == 0
    c, out, _ = rodar(capsys, "--json", "status")
    st = json.loads(out)
    assert st[POSTADOS][0]["item"] == "P1_2026-09-30_1830_gta_rockstar-quinta"


def test_cli_refazer_e_erros(capsys, tmp_path, sem_janela):
    arq = tmp_path / "p.json"
    arq.write_text(json.dumps(pedido_reel()), encoding="utf-8")
    rodar(capsys, "pedido", "--json", str(arq))
    c, _, err = rodar(capsys, "aprovar", "rockstar", "--notas", "gancho=9")
    assert c == 1 and "não em 05_revisao" in err
    rodar(capsys, "--simular", "ciclo")
    c, out, _ = rodar(capsys, "refazer", "rockstar", "--motivo", "capa escura", "--etapa", "04",
                      "--simular", "--json")
    assert c == 0 and json.loads(out)["etapa_destino"] == "04_edicao"
    c, _, err = rodar(capsys, "aprovar", "nada-disso", "--notas", "a=1")
    assert c == 1 and "nenhum item" in err
    c, _, err = rodar(capsys, "pedido", "--json", str(tmp_path / "nao_existe.json"))
    assert c == 1
    ruim = tmp_path / "ruim.json"
    ruim.write_text(json.dumps(pedido_reel(canal="futebol", dublar=True)), encoding="utf-8")
    c, _, err = rodar(capsys, "pedido", "--json", str(ruim))
    assert c == 1 and "futebol" in err


def test_cli_vigiar_uma_vez(capsys, sem_janela):
    c, out, _ = rodar(capsys, "--simular", "vigiar", "--uma-vez")
    assert c == 0 and "executados" in out


def test_vigiar_loop_para(sem_janela):
    dormidas = []
    r = vigia.vigiar(intervalo=30, simular=True, dormir=dormidas.append, max_ciclos=3)
    assert len(r) == 3 and dormidas == [30.0, 30.0]


def test_gancho(sem_janela):
    r = gancho.executar({"acao": "pedido", "dados": pedido_reel()})
    assert r["ok"] and r["resultado"]["item"] == "P1_2026-09-30_1830_gta_rockstar-quinta"
    r = gancho.executar({"tipo": "esteira", "simular": True})  # sem acao = ciclo
    assert r["ok"] and r["acao"] == "ciclo" and r["resultado"]["executados"]
    st = gancho.executar({"acao": "status"})["resultado"]
    assert st[REVISAO][0]["item"].endswith("rockstar-quinta")
    r = gancho.executar({"acao": "aprovar", "item": "rockstar", "notas": {"gancho": 10},
                         "simular": True})
    assert r["ok"] and r["resultado"]["veredito"] == "Excelente"
    assert gancho.executar({"acao": "status"})["resultado"][AGENDADOS]
    # nunca levanta exceção
    assert gancho.executar({"acao": "voar"})["ok"] is False
    r = gancho.executar({"acao": "aprovar"})
    assert r["ok"] is False and "item" in r["erro"]
    r = gancho.executar({"acao": "pedido", "dados": {"canal": "x"}})
    assert r["ok"] is False and "pedido inválido" in r["erro"]
    json.dumps(gancho.executar({"acao": "ciclo", "simular": True}))  # serializável


def test_gancho_prioridade_e_reprocessar(sem_janela):
    gancho.executar({"acao": "pedido", "dados": pedido_reel()})
    r = gancho.executar({"acao": "prioridade", "item": "rockstar", "prioridade": "P0"})
    assert r["ok"] and r["resultado"]["item"].startswith("P0_")
    r = gancho.executar({"acao": "reprocessar", "item": "rockstar"})
    assert r["ok"] is False and "não em 99_erros" in r["erro"]


def test_fluxo_real_com_ffmpeg(amb):
    """Baixador e Legendador falsos, mas conferência, áudio, edição e quadros
    de revisão com ffmpeg de verdade."""
    from esteira.editor import EditorFFmpeg
    from esteira.legendas import Fala, escrever_srt
    from esteira.midia import MidiaFFmpeg, gerar_video_teste, info_midia
    from esteira.pedido import criar_pedido

    class BaixadorSintetico:
        def baixar(self, url, destino):
            destino.mkdir(parents=True, exist_ok=True)
            return gerar_video_teste(destino / "v.mp4", 2.0, 320, 180)

    class LegendadorFixo:
        def legendar(self, audio, pasta, idioma=None):
            assert audio.exists()
            return escrever_srt([Fala(0.1, 1.5, "Chegou a quinta!")], pasta / "legenda.srt")

    amb.trocar(baixador=BaixadorSintetico(), midia=MidiaFFmpeg(),
               legendador=LegendadorFixo(), editor=EditorFFmpeg(amb.cfg))
    item = criar_pedido(pedido_reel())
    r = amb.ciclo()
    assert r["erros"] == [], r["erros"]
    rev = amb.pasta(REVISAO) / item.name
    i = info_midia(rev / "final.mp4", usar_ffprobe=False)
    assert (i.largura, i.altura) == (1080, 1920) and abs(i.duracao - 2.0) < 0.15
    q = info_midia(rev / "revisao" / "quadro_2_meio.jpg", usar_ffprobe=False)
    assert (q.largura, q.altura) == (540, 960)
    texto = (rev / "texto_revisao.md").read_text(encoding="utf-8")
    assert "1080x1920 (ok)" in texto and "LUFS (alvo -14.0; ok)" in texto
    assert "Chegou a quinta!" in texto
    assert ler_json(rev / "midia.json")["largura"] == 320
    assert (amb.pasta(PEDIDOS)).exists()
