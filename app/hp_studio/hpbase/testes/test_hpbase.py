import json
import os
from datetime import datetime

import pytest

from hpbase import (TravaPesada, TravaOcupada, janela_proibida, mascarar,
                    ler_segredo, SegredoAusente, escrever_json, ler_json,
                    obter_logger, pasta_logs, pasta_segredos, garantir, rodar)


def test_janela_proibida():
    assert janela_proibida(datetime(2026, 9, 30, 18, 0))
    assert janela_proibida(datetime(2026, 9, 30, 22, 29))
    assert not janela_proibida(datetime(2026, 9, 30, 22, 30))
    assert not janela_proibida(datetime(2026, 9, 30, 17, 59))


def test_trava_um_por_vez():
    manha = datetime(2026, 9, 30, 10, 0)
    with TravaPesada("a", agora=manha):
        with pytest.raises(TravaOcupada):
            TravaPesada("b", agora=manha).adquirir()
    with TravaPesada("c", agora=manha):
        pass


def test_trava_respeita_horario():
    with pytest.raises(TravaOcupada):
        TravaPesada("x", agora=datetime(2026, 9, 30, 19, 0)).adquirir()
    with TravaPesada("story", agora=datetime(2026, 9, 30, 19, 0), ignorar_horario=True):
        pass


def test_trava_de_processo_morto_e_assumida(tmp_path):
    p = tmp_path / "pesado.lock"
    p.write_text(json.dumps({"dono": "morto", "pid": 999999, "desde": 0}))
    with TravaPesada("novo", caminho=p, agora=datetime(2026, 9, 30, 9, 0)):
        assert json.loads(p.read_text())["dono"] == "novo"
    assert not p.exists()


def test_mascarar():
    s = mascarar("GET /me?access_token=EAABsecreto123&x=1 Bearer abc.def senha: 1234")
    assert "EAABsecreto123" not in s and "abc.def" not in s and "1234" not in s
    assert "EAA" + "B" * 30 not in mascarar("tok EAA" + "B" * 30)


def test_segredo_nunca_na_mensagem():
    garantir(pasta_segredos())
    (pasta_segredos() / "meta_tokens.txt").write_text("# x\nIG_TOKEN=valorsecreto\n")
    assert ler_segredo("meta_tokens.txt", "ig_token") == "valorsecreto"
    with pytest.raises(SegredoAusente) as e:
        ler_segredo("meta_tokens.txt", "outro")
    assert "valorsecreto" not in str(e.value)


def test_json_atomico(tmp_path):
    p = tmp_path / "a" / "b.json"
    escrever_json(p, {"á": 1})
    assert ler_json(p) == {"á": 1}
    assert ler_json(tmp_path / "nao.json", {}) == {}


def test_log_sem_segredo():
    lg = obter_logger("teste")
    lg.info("token=%s", "EAAsegredo")
    for h in lg.handlers:
        h.flush()
    txt = "".join(p.read_text(encoding="utf-8") for p in pasta_logs().glob("teste_*.log"))
    assert "EAAsegredo" not in txt and "token=***" in txt


def test_rodar():
    import sys
    r = rodar([sys.executable, "-c", "print('oi')"])
    assert r.returncode == 0 and b"oi" in r.stdout
