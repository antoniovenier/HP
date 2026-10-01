"""Linha de comando e o gancho executar() do motor."""
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from hpbase import agora, ler_json, pasta_app
from qa_paridade import executar
from qa_paridade.cli import main

from .apoio import imagem_teste, salvar_png

PASTA_HP_STUDIO = Path(__file__).resolve().parents[2]
MANHA = datetime(2026, 9, 30, 10, 0)


def test_help_em_portugues():
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run([sys.executable, "-m", "qa_paridade", "--help"], cwd=PASTA_HP_STUDIO,
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=env, timeout=60)
    assert r.returncode == 0
    assert "uso:" in r.stdout and "mostra esta ajuda" in r.stdout
    for cmd in ("video", "imagem", "laminas", "legenda", "status"):
        assert cmd in r.stdout


def test_video_com_tarefa_registra_e_status(midia, capsys):
    rc = main(["video", str(midia["igual"]), str(midia["ref"]), "--tarefa", "editor_reel",
               "--id", "t1"], usar_trava=False)
    saida = capsys.readouterr().out
    assert rc == 0
    assert "IDENTICO" in saida and "passa no dia: SIM" in saida
    hoje = agora().date().isoformat()
    pasta = pasta_app() / "paridade" / "editor_reel"
    assert (pasta / f"{hoje}_t1.json").exists()
    assert (pasta / f"{hoje}_t1.md").exists()
    assert ler_json(pasta / "resumo.json")["dias_seguidos"] == 1

    assert main(["status"]) == 0
    tabela = capsys.readouterr().out
    assert "editor_reel" in tabela and "não" in tabela
    linha = next(l for l in tabela.splitlines() if l.startswith("editor_reel"))
    assert linha.split()[1:4] == ["1", "6", "não"]

    assert main(["status", "--tarefa", "editor_reel", "--json"]) == 0
    dados = json.loads(capsys.readouterr().out)
    assert dados[0]["tarefa"] == "editor_reel" and dados[0]["falta"] == 6


def test_video_diferente_sai_com_1_e_json(midia, capsys):
    rc = main(["video", str(midia["caixa"]), str(midia["ref"]), "--json"], usar_trava=False)
    assert rc == 1
    rel = json.loads(capsys.readouterr().out)
    assert rel["veredito"] == "DIFERENTE"
    assert list((pasta_app() / "paridade" / "_avulsos").glob("*.json"))


def test_video_com_legendas_pela_cli(midia, capsys):
    rc = main(["video", str(midia["igual"]), str(midia["ref"]),
               "--legenda-app", str(midia["srt_desloc"]), "--legenda-ref", str(midia["srt_ref"]),
               "--saida", str(pasta_app() / "saida_teste")], usar_trava=False)
    assert rc == 1
    assert "Legenda" in capsys.readouterr().out
    assert list((pasta_app() / "saida_teste").glob("*.md"))


def test_trava_na_cli(midia, capsys):
    assert main(["video", str(midia["igual"]), str(midia["ref"])],
                agora=datetime(2026, 9, 30, 19, 30)) == 3
    assert "OCUPADO" in capsys.readouterr().out
    assert main(["video", str(midia["igual"]), str(midia["ref"])], agora=MANHA) == 0
    assert not (pasta_app() / "pesado.lock").exists()


def test_legenda_imagem_laminas_pela_cli(midia, tmp_path, capsys):
    assert main(["legenda", str(midia["srt_ref"]), str(midia["srt_ref"])]) == 0
    assert main(["legenda", str(midia["srt_desloc"]), str(midia["srt_ref"])]) == 1
    a = salvar_png(imagem_teste(1), tmp_path / "a.png")
    assert main(["imagem", str(a), str(a), "--tarefa", "estaticos"]) == 0
    ref, app = tmp_path / "ref", tmp_path / "app"
    ref.mkdir()
    app.mkdir()
    for k, s in enumerate([1, 2, 3], 1):
        salvar_png(imagem_teste(s), ref / f"{k}.png")
    for k, s in enumerate([1, 3, 2], 1):
        salvar_png(imagem_teste(s), app / f"{k}.png")
    assert main(["laminas", str(app), str(ref)]) == 1
    assert "ORDEM TROCADA" in capsys.readouterr().out


def test_erros_de_entrada(tmp_path, capsys):
    assert main(["imagem", str(tmp_path / "nao.png"), str(tmp_path / "nem.png")]) == 2
    assert "ERRO" in capsys.readouterr().out


def test_executar_do_motor(midia):
    r = executar({"tipo": "video", "app": str(midia["igual"]), "ref": str(midia["ref"]),
                  "tarefa": "editor_reel", "id": "motor1"}, usar_trava=False)
    assert r["ok"] and r["aprovado"] and r["veredito"] == "IDENTICO"
    assert Path(r["json"]).exists() and r["status"]["dias_seguidos"] == 1
    adiado = executar({"tipo": "video", "app": str(midia["igual"]), "ref": str(midia["ref"])},
                      agora_trava=datetime(2026, 9, 30, 20, 0))
    assert adiado == {"ok": False, "adiar": True, "erro": adiado["erro"]}
    ruim = executar({"tipo": "video", "app": "nao_existe.mp4", "ref": str(midia["ref"])},
                    usar_trava=False)
    assert not ruim["ok"] and not ruim["adiar"]
    assert not executar({"tipo": "podcast", "app": "a", "ref": "b"})["ok"]
