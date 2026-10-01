"""chaves_pc + patch do config.py: nomes reais da §4.3 (IG_<handle>, FB_<canal>, youtube.json),
antigos da rodada 1 valendo depois, Instagram em graph.instagram.com, e a PROVA de que nenhum
valor falso (FAKE_NAO_E_TOKEN_n) aparece em stdout, stderr, log, exceção nem arquivo."""
from __future__ import annotations

import hashlib
import json

import pytest

from hpbase import pasta_logs, pasta_segredos
from hpbase.fila_api_pc import CANAIS

from metricas import chaves_pc, config
from metricas.cli import main
from metricas.cliente import ErroAPI
from metricas.coleta import coletar, plano
from metricas.config import Contexto, Credenciais, carregar_config, chaves, pasta_metricas, token_e_id
from metricas.modelos import SemToken

from .falso import AGORA, IG_ID, PAGE_ID, TH_ID, ClienteFalso, cliente_completo, config_teste

PERFIS = ("gta", "futebol", "filmes", "receitas", "carros", "destinos")
FALSO = "FAKE_NAO_E_TOKEN"


def _h(s) -> str:
    return hashlib.sha256(str(s).encode("utf-8")).hexdigest()


def escrever_segredos_reais(pasta, refresh_para=("gta",), com_antigos=False, sem=()):
    """Os arquivos da §4.3 com valores FAKE_NAO_E_TOKEN_<n>. Devolve {chave: n} (só para o
    teste comparar por hash; os valores nunca saem daqui)."""
    pasta.mkdir(parents=True, exist_ok=True)
    n = [0]

    def v():
        n[0] += 1
        return f"{FALSO}_{n[0]}"

    numeros = {}
    meta = ["# tokens da Meta (teste)"]
    fb = ["# tokens das Páginas (teste)"]
    meta_json = {"contas": {}, "ultima_checagem_renovacao": "2026-10-01 06:00", "ultimo_teste": "2026-10-01 06:00"}
    paginas = {}
    yt = {"canais": {}, "oauth": {"client_id": "123-abc.apps.googleusercontent.com",
                                  "client_secret": v(), "refresh_tokens": {}}}
    numeros["oauth/client_secret"] = n[0]
    yt_canais = {}
    for i, conta in enumerate(PERFIS, 1):
        handle = CANAIS[conta][0]
        ig_id = IG_ID if conta == "gta" else f"1784140000000000{i}"
        th_id = TH_ID if conta == "gta" else f"260000000000000{i}"
        pg_id = PAGE_ID if conta == "gta" else f"100000000000000{i}"
        if f"IG_{handle}" not in sem:
            meta.append(f"IG_{handle}={v()}")
            numeros[f"IG_{handle}"] = n[0]
        if f"TH_{handle}" not in sem:
            # uma conta com @ e aspas, como o publicador aceita
            meta.append(f'TH_@{handle}="{v()}"' if conta == "futebol" else f"TH_{handle}={v()}")
            numeros[f"TH_{handle}"] = n[0]
        meta_json["contas"][f"IG_{handle}"] = {"id": ig_id, "username": handle, "visto_em": "2026-10-01"}
        meta_json["contas"][f"TH_{handle}"] = {"id": th_id, "username": handle}
        if f"FB_{conta}" not in sem:
            fb.append(f"FB_{conta}={v()}")
            numeros[f"FB_{conta}"] = n[0]
        paginas[conta] = {"id": pg_id, "nome": f"{conta} | HP", "expira": "nunca"}
        yt["canais"][conta] = "UCgta" if conta == "gta" else f"UC{conta}0000000000000000000"
        yt_canais[conta] = {"id": yt["canais"][conta], "titulo": f"{conta} | HP"}
        if conta in refresh_para:
            yt["oauth"]["refresh_tokens"][conta] = v()
            numeros[f"oauth/refresh_tokens/{conta}"] = n[0]
    (pasta / "meta_tokens.txt").write_text("\n".join(meta) + "\n", encoding="utf-8")
    (pasta / "facebook_tokens.txt").write_text("\n".join(fb) + "\n", encoding="utf-8")
    (pasta / "meta_tokens_meta.json").write_text(json.dumps(meta_json, ensure_ascii=False, indent=1),
                                                 encoding="utf-8")
    (pasta / "facebook_paginas.json").write_text(json.dumps(paginas, ensure_ascii=False), encoding="utf-8")
    (pasta / "youtube.json").write_text(json.dumps(yt, ensure_ascii=False, indent=1), encoding="utf-8")
    (pasta / "youtube_canais.json").write_text(json.dumps(yt_canais, ensure_ascii=False), encoding="utf-8")
    if com_antigos:
        (pasta / "meta_tokens.txt").open("a", encoding="utf-8").write(
            f"IG_GTA_TOKEN={v()}\nIG_GTA_ID=999\n")
        numeros["IG_GTA_TOKEN"] = n[0]
    return numeros


@pytest.fixture
def segredos(raizes_temporarias):
    local, _ = raizes_temporarias
    numeros = escrever_segredos_reais(local / "segredos")
    return local / "segredos", numeros


def _textos_gravados():
    textos = [p.read_text(encoding="utf-8") for p in pasta_metricas().glob("*.json")]
    textos += [p.read_text(encoding="utf-8") for p in pasta_logs().glob("metricas_*.log")]
    return textos


# --- leitura de nomes (nunca de valores) --------------------------------------------------
def test_nomes_no_txt_devolve_so_nomes_aceita_arroba_aspas_e_comentario(tmp_path):
    p = tmp_path / "meta_tokens.txt"
    p.write_text(f"# comentário\nIG_@HP.Futebol = \"{FALSO}_1\"\n\nTH_hpgta6={FALSO}_2\nlinha sem igual\n",
                 encoding="utf-8")
    nomes = chaves_pc.nomes_no_txt(p)
    assert nomes == ["ig_hp.futebol", "th_hpgta6"]
    assert FALSO not in json.dumps(nomes)
    assert chaves_pc.existe(tmp_path, "meta_tokens.txt", "IG_hp.futebol")
    assert chaves_pc.existe(tmp_path, "meta_tokens.txt", "ig_@hp.futebol")
    assert not chaves_pc.existe(tmp_path, "meta_tokens.txt", "IG_hpgta6")


def test_nomes_no_json_sao_caminhos_sem_valores(segredos):
    pasta, _ = segredos
    nomes = chaves_pc.nomes_no_json(pasta / "youtube.json")
    assert "oauth/refresh_tokens/gta" in nomes and "oauth/client_secret" in nomes
    assert "oauth/refresh_tokens/futebol" not in nomes
    assert "canais/gta" in nomes
    assert FALSO not in json.dumps(nomes)
    assert chaves_pc.nomes_no_json(pasta / "nao_existe.json") == []


def test_handle_vem_do_contas_json_ou_da_tabela_canais():
    cfg = carregar_config()["contas"]
    assert chaves_pc.handle_da_conta("futebol", cfg["futebol"]) == "hp.futebol"
    assert chaves_pc.handle_da_conta("gta", {"instagram": {"usuario": "@HPGTA6"}}) == "hpgta6"
    assert chaves_pc.handle_da_conta("destinos") == CANAIS["destinos"][0] == "hp.destinos"
    assert chaves_pc.handle_da_conta("@Fulano.X") == "fulano.x"


def test_chaves_do_config_reais_primeiro_antigos_depois():
    assert chaves("instagram", "futebol")["token"] == ["IG_hp.futebol", "IG_FUTEBOL_TOKEN", "IG_TOKEN", "META_TOKEN"]
    assert chaves("instagram", "futebol")["id"] == ["contas/IG_hp.futebol/id", "IG_FUTEBOL_ID"]
    assert chaves("threads", "gta", {"usuario": "hpgta6"})["token"][:2] == ["TH_hpgta6", "TH_GTA_TOKEN"]
    assert chaves("facebook", "carros")["token"][:2] == ["FB_carros", "FB_CARROS_TOKEN"]
    assert chaves("facebook", "carros")["id"] == ["carros/id", "FB_CARROS_ID"]
    k = chaves("youtube", "gta")
    assert k["refresh"] == ["oauth/refresh_tokens/gta", "YT_GTA_REFRESH_TOKEN", "YT_REFRESH_TOKEN"]
    assert k["canal"][:2] == ["canais/gta", "gta/id"] and k["client_secret"][0] == "oauth/client_secret"
    # override do contas.json vem antes de tudo
    assert chaves("instagram", "gta", {"chave_token": "MEU_TOKEN"})["token"][0] == "MEU_TOKEN"


def test_sensivel_separa_token_de_id():
    assert chaves_pc.sensivel("IG_hpgta6", "meta_tokens.txt")
    assert chaves_pc.sensivel("FB_gta", "facebook_tokens.txt")
    assert chaves_pc.sensivel("oauth/refresh_tokens/gta", "youtube.json")
    assert chaves_pc.sensivel("oauth/client_secret", "youtube.json")
    assert chaves_pc.sensivel("IG_x_idol", "meta_tokens.txt")   # handle com "_id" no meio ainda é token
    assert not chaves_pc.sensivel("contas/IG_hpgta6/id", "meta_tokens_meta.json")
    assert not chaves_pc.sensivel("IG_GTA_ID", "meta_tokens.txt")
    assert not chaves_pc.sensivel("oauth/client_id", "youtube.json")
    assert not chaves_pc.sensivel("canais/gta", "youtube.json")


# --- inventário -----------------------------------------------------------------------------
def test_inventario_6_contas_x_3_redes_sem_valor(segredos):
    pasta, _ = segredos
    cfg = carregar_config()
    inv = chaves_pc.inventario(pasta, cfg)
    for conta in PERFIS:
        handle = CANAIS[conta][0]
        ig, th, fb = inv[conta]["instagram"], inv[conta]["threads"], inv[conta]["facebook"]
        assert (ig["status"], th["status"], fb["status"]) == ("ok", "ok", "ok")
        assert ig["chave_token"] == f"IG_{handle}" and ig["arquivo"] == "meta_tokens.txt"
        assert th["chave_token"] == f"TH_{handle}"
        assert fb["chave_token"] == f"FB_{conta}" and fb["arquivo"] == "facebook_tokens.txt"
        assert (ig["host"], ig["versao"]) == ("https://graph.instagram.com", "v21.0")
        assert (th["host"], th["versao"]) == ("https://graph.threads.net", "v1.0")
        assert (fb["host"], fb["versao"]) == ("https://graph.facebook.com", "v26.0")
        assert ig["id"] and ig["arquivo_id"] == "meta_tokens_meta.json"
        assert fb["id"] and fb["arquivo_id"] == "facebook_paginas.json"
        assert inv[conta]["tiktok"]["status"] == "manual"
    assert inv["gta"]["instagram"]["id"] == IG_ID and inv["gta"]["facebook"]["id"] == PAGE_ID
    assert FALSO not in json.dumps(inv, ensure_ascii=False)
    assert "sem_token" not in {e["status"] for r in inv.values() for e in r.values()}


def test_inventario_youtube_nao_autorizado_e_autorizado(segredos):
    pasta, _ = segredos
    cfg = carregar_config()
    yt = chaves_pc.inventario(pasta, cfg, "gta", "youtube")["gta"]["youtube"]
    assert yt["status"] == "nao_autorizado" and yt["autorizado"] is False
    assert yt["chave_token"] == "oauth/refresh_tokens/gta" and yt["arquivo"] == "youtube.json"
    assert yt["id"] == "UCgta" and yt["oauth"] == {"refresh_token": True, "client_id": True, "client_secret": True}
    cfg["contas"]["gta"]["youtube"]["autorizado"] = True
    cfg["contas"]["futebol"]["youtube"]["autorizado"] = True
    inv = chaves_pc.inventario(pasta, cfg, ["gta", "futebol"], "youtube")
    assert inv["gta"]["youtube"]["status"] == "ok"
    fut = inv["futebol"]["youtube"]           # só o GTA tem refresh token no PC
    assert fut["status"] == "sem_token" and fut["falta"] == ["token"] and fut["id"].startswith("UC")
    assert FALSO not in json.dumps(inv)


def test_inventario_nomes_antigos_valem_depois_dos_reais(raizes_temporarias):
    local, _ = raizes_temporarias
    from .falso import escrever_segredos
    escrever_segredos(local)                                    # só os nomes da rodada 1
    cfg = carregar_config()
    e = chaves_pc.inventario(pasta_segredos(), cfg, "gta", "instagram")["gta"]["instagram"]
    assert e["status"] == "ok" and e["chave_token"] == "IG_GTA_TOKEN" and e["id"] == IG_ID
    assert e["arquivo"] == "meta_tokens.txt" and e["arquivo_id"] == "meta_tokens.txt"
    yt = chaves_pc.inventario(pasta_segredos(), config_teste(), "gta", "youtube")["gta"]["youtube"]
    assert yt["status"] == "ok" and yt["chave_token"] == "YT_GTA_REFRESH_TOKEN"
    assert yt["arquivo"] == "youtube_tokens.txt" and yt["id"] == "UCgta"
    # os dois juntos: o real ganha
    escrever_segredos_reais(pasta_segredos(), com_antigos=True)
    e = chaves_pc.inventario(pasta_segredos(), cfg, "gta", "instagram")["gta"]["instagram"]
    assert e["chave_token"] == "IG_hpgta6" and e["id"] == IG_ID


def test_inventario_sem_pasta_nao_quebra_e_diz_o_nome_esperado(tmp_path):
    inv = chaves_pc.inventario(tmp_path / "nao_existe", carregar_config(), "receitas")
    e = inv["receitas"]["instagram"]
    assert e["status"] == "sem_token" and e["falta"] == ["token", "id"]
    assert e["chave_token"] == "IG_hp.receitas" and e["arquivo"] == "meta_tokens.txt"
    assert inv["receitas"]["facebook"]["chave_token"] == "FB_receitas"
    assert chaves_pc.resumo(inv)[0].startswith("receitas/instagram: sem_token")


# --- --simular e CLI -----------------------------------------------------------------------
def test_cli_simular_6_contas_zero_sem_token(segredos, capsys):
    assert main(["coletar", "--simular"]) == 0
    saida = capsys.readouterr()
    linhas = [l.strip() for l in saida.out.splitlines() if "/" in l]
    assert "sem_token" not in saida.out
    assert sum(1 for l in linhas if l.endswith("coletaria (token: ok, id: ok)")) == 18
    for conta in PERFIS:
        assert f'{conta}/youtube: pularia: nao_autorizado ("autorizado": false)' in saida.out
        assert f"{conta}/tiktok: manual (use importar-tiktok)" in saida.out
    assert FALSO not in saida.out and FALSO not in saida.err
    assert not list(pasta_metricas().glob("*.json"))


def test_cli_simular_youtube_coletaria_com_a_flag_verdadeira(segredos, capsys):
    cfg = carregar_config()
    cfg["contas"]["gta"]["youtube"]["autorizado"] = True
    cfg["contas"]["carros"]["youtube"]["autorizado"] = True
    arq = pasta_metricas() / "contas_teste.json"
    arq.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
    assert main(["coletar", "--simular", "--rede", "youtube", "--contas", str(arq)]) == 0
    out = capsys.readouterr().out
    assert "gta/youtube: coletaria (canal: ok, chave: falta, analytics: ok)" in out
    assert "carros/youtube: sem_token" in out and "oauth/refresh_tokens/carros" in out
    assert "futebol/youtube: pularia: nao_autorizado" in out
    assert FALSO not in out


def test_cli_chaves_mostra_inventario_sem_valor(segredos, capsys):
    assert main(["chaves", "--json", "--conta", "futebol"]) == 0
    out = capsys.readouterr().out
    inv = json.loads(out)
    assert inv["futebol"]["instagram"]["chave_token"] == "IG_hp.futebol"
    assert inv["futebol"]["threads"]["chave_token"] == "TH_hp.futebol"   # veio com @ e aspas no arquivo
    assert FALSO not in out
    assert main(["chaves", "--rede", "facebook"]) == 0
    out = capsys.readouterr().out
    assert "gta/facebook: ok  token ok FB_gta (facebook_tokens.txt)  id ok" in out
    assert FALSO not in out


def test_plano_sem_token_diz_o_nome_real_e_o_antigo(raizes_temporarias):
    local, _ = raizes_temporarias
    escrever_segredos_reais(local / "segredos", sem=("TH_hp.filmes",))
    linhas = plano("filmes", "threads")
    assert linhas == ["filmes/threads: sem_token (token: falta TH_hp.filmes (ou o antigo "
                      "TH_FILMES_TOKEN) em meta_tokens.txt, id: ok)"]


# --- coleta de verdade (cliente falso) ---------------------------------------------------------
def test_token_e_id_le_o_real_primeiro_e_o_id_do_meta_json(segredos):
    pasta, numeros = segredos
    escrever_segredos_reais(pasta, com_antigos=True)
    cfg = carregar_config()
    cred = Credenciais(cfg["arquivos_segredo"], pasta)
    token, ident = token_e_id("instagram", "gta", cfg["contas"]["gta"]["instagram"], cred)
    igual_ao_real = _h(token) == _h(f"{FALSO}_{numeros['IG_hpgta6']}")
    assert igual_ao_real and ident == IG_ID          # não é o antigo IG_GTA_TOKEN nem o id 999
    assert cred.mascarar(f"x={token} y") == "x=*** y"
    token, ident = token_e_id("threads", "futebol", cfg["contas"]["futebol"]["threads"], cred)
    assert _h(token) == _h(f"{FALSO}_{numeros['TH_hp.futebol']}") and ident == "2600000000000002"


def test_token_e_id_facebook_le_facebook_tokens_e_paginas(segredos):
    pasta, numeros = segredos
    cfg = carregar_config()
    cred = Credenciais(cfg["arquivos_segredo"], pasta)
    token, ident = token_e_id("facebook", "destinos", cfg["contas"]["destinos"]["facebook"], cred)
    assert _h(token) == _h(f"{FALSO}_{numeros['FB_destinos']}") and ident == "1000000000000006"
    assert FALSO not in cred.mascarar(f"erro com {token}")


def test_sem_token_mensagem_so_com_nomes(segredos):
    pasta, _ = segredos
    escrever_segredos_reais(pasta, sem=("IG_hp.carros", "FB_carros"))
    cfg = carregar_config()
    cred = Credenciais(cfg["arquivos_segredo"], pasta)
    with pytest.raises(SemToken) as e:
        token_e_id("instagram", "carros", cfg["contas"]["carros"]["instagram"], cred)
    assert str(e.value) == "instagram/carros: falta token (chave IG_hp.carros (ou o antigo IG_CARROS_TOKEN) em meta_tokens.txt)"
    with pytest.raises(SemToken) as e:
        token_e_id("facebook", "carros", cfg["contas"]["carros"]["facebook"], cred)
    assert "FB_carros (ou o antigo FB_CARROS_TOKEN) em facebook_tokens.txt" in str(e.value)
    assert FALSO not in str(e.value)


def test_instagram_fala_com_graph_instagram_e_facebook_v26(segredos):
    cliente = cliente_completo()
    foto = coletar(["gta"], cliente=cliente, agora=AGORA, config=carregar_config(), gravar=False)
    gta = foto["contas"]["gta"]
    assert gta["instagram"]["status"] == "ok" and gta["instagram"]["seguidores"] == 1500
    assert gta["threads"]["status"] == "ok" and gta["facebook"]["status"] == "ok"
    urls = [u for u, _ in cliente.chamadas]
    assert urls[0] == f"https://graph.instagram.com/v21.0/{IG_ID}"
    assert any(u.startswith(f"https://graph.threads.net/v1.0/{TH_ID}") for u in urls)
    assert any(u.startswith(f"https://graph.facebook.com/v26.0/{PAGE_ID}") for u in urls)
    assert not any("graph.facebook.com" in u and IG_ID in u and "after=" not in u for u in urls)
    ctx = Contexto(AGORA, carregar_config())
    assert ctx.base_instagram == "https://graph.instagram.com/v21.0"
    assert ctx.base_graph == "https://graph.facebook.com/v26.0"
    assert FALSO not in json.dumps(foto)


def test_youtube_coleta_pelo_youtube_json_oauth(segredos):
    pasta, numeros = segredos
    cfg = carregar_config()
    cfg["contas"]["gta"]["youtube"]["autorizado"] = True
    cliente = cliente_completo()
    foto = coletar(["gta"], ["youtube"], cliente=cliente, agora=AGORA, config=cfg, gravar=False)
    yt = foto["contas"]["gta"]["youtube"]
    assert yt["status"] == "ok" and yt["canal"] == "UCgta" and yt["analytics"] == "ok"
    pedido_token = [d for u, d in cliente.chamadas if u.endswith("/token")][0]
    assert _h(pedido_token["refresh_token"]) == _h(f"{FALSO}_{numeros['oauth/refresh_tokens/gta']}")
    assert _h(pedido_token["client_secret"]) == _h(f"{FALSO}_{numeros['oauth/client_secret']}")
    assert pedido_token["client_id"] == "123-abc.apps.googleusercontent.com"
    assert FALSO not in json.dumps(foto)
    # com a flag falsa nada é chamado
    cfg["contas"]["gta"]["youtube"]["autorizado"] = False
    cliente = cliente_completo()
    foto = coletar(["gta"], ["youtube"], cliente=cliente, agora=AGORA, config=cfg, gravar=False)
    assert foto["contas"]["gta"]["youtube"]["status"] == "nao_autorizado" and cliente.chamadas == []


def test_nenhum_valor_falso_em_stdout_stderr_log_excecao_nem_arquivo(segredos, capsys):
    pasta, numeros = segredos
    # 1) simulação e inventário pela CLI
    assert main(["coletar", "--simular"]) == 0
    assert main(["chaves"]) == 0
    # 2) coleta real com a API devolvendo erro que ecoa o token e um SemToken
    tok_falso = f"{FALSO}_{numeros['IG_hpgta6']}"
    vazou = ErroAPI(f"falhou GET https://graph.instagram.com/v21.0/{IG_ID}?access_token={tok_falso} "
                    f"(token {tok_falso})", status=400)
    cliente = cliente_completo(**{f"/{IG_ID}": vazou, "/youtube/v3/channels": RuntimeError(
        f"quebrou com refresh {FALSO}_{numeros['oauth/refresh_tokens/gta']}")})
    cfg = carregar_config()
    cfg["contas"]["gta"]["youtube"]["autorizado"] = True
    foto = coletar(["gta"], cliente=cliente, agora=AGORA, config=cfg)
    st = foto["contas"]["gta"]["instagram"]["status"]
    assert st.startswith("erro:") and "***" in st
    assert "***" in foto["contas"]["gta"]["youtube"]["status"]
    # 3) exceção de token ausente
    cred = Credenciais(cfg["arquivos_segredo"], pasta)
    with pytest.raises(SemToken) as e:
        token_e_id("instagram", "gta", {"chave_token": "NAO_EXISTE", "usuario": "ninguem"}, cred)
    saida = capsys.readouterr()
    textos = [saida.out, saida.err, str(e.value), json.dumps(foto, ensure_ascii=False)] + _textos_gravados()
    assert len(textos) >= 6 and any("metricas_" in str(p) for p in pasta_logs().glob("*.log"))
    for t in textos:
        assert FALSO not in t
    assert "***" in " ".join(_textos_gravados())


def test_credenciais_aceita_lista_de_arquivos_e_json_por_caminho(segredos):
    pasta, numeros = segredos
    cred = Credenciais({"yt": ["youtube.json", "youtube_tokens.txt"], "ids": "meta_tokens_meta.json"}, pasta)
    v = cred.obter("yt", "oauth/refresh_tokens/gta")
    assert _h(v) == _h(f"{FALSO}_{numeros['oauth/refresh_tokens/gta']}")
    assert cred.obter(("ids", "yt"), "contas/IG_hpgta6/id") == IG_ID
    assert cred.obter("yt", "oauth/refresh_tokens/futebol", "nada") is None
    assert cred.obter("yt", "oauth") is None            # dict não é valor
    assert cred.mascarar(f"a {v} b") == "a *** b"      # refresh é sensível, id não
    assert cred.mascarar(f"id {IG_ID}") == f"id {IG_ID}"


def test_cliente_falso_nao_recebe_token_antigo_quando_ha_real(segredos):
    pasta, numeros = segredos
    escrever_segredos_reais(pasta, com_antigos=True)
    cliente = ClienteFalso({f"/{IG_ID}": {"followers_count": 1, "media_count": 0, "username": "hpgta6"},
                            f"/{IG_ID}/media": {"data": []}})
    coletar(["gta"], ["instagram"], cliente=cliente, agora=AGORA, config=carregar_config(), gravar=False)
    usado = cliente.chamadas[0][1]["access_token"]
    assert _h(usado) == _h(f"{FALSO}_{numeros['IG_hpgta6']}")
