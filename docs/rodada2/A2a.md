# A2a — Tokens reais (`metricas/chaves_pc`) + comandos reais dos scripts (`esteira/comandos_pc`)

Agente A2a, rodada 2, 01/10/2026. Trabalho em `/home/user/HP` (branch `claude/relaxed-cray-0fkcdu`), sem commit.
Cobre as tarefas **A2** (tokens, §4.3) e **A3** (scripts reais, §4.4) do `docs/PROMPT_NUVEM_2.md`.

## 1. Feito / pela metade / não deu

### A2 — Tokens

| Critério de pronto | Situação |
|---|---|
| `metricas/chaves_pc.py`: dado o diretório de segredos (injetado), diz QUAIS chaves existem sem ler o valor (só o lado esquerdo do `=` / só os nomes das chaves do JSON; nunca devolve nem guarda valor) e monta por conta e rede `{"chave_token", "id", "host", "versao", "arquivo", "status"}` | **Feito** (`inventario(pasta, cfg)`; extras: `arquivo_id`, `falta`, `nomes`, `handle`; YouTube também `oauth{refresh_token, client_id, client_secret}`, `api_key`, `autorizado`) |
| IG `IG_<handle>` em `meta_tokens.txt` + `contas/IG_<handle>/id` do `meta_tokens_meta.json`, host `graph.instagram.com` v21.0; Threads `TH_<handle>` + id, `graph.threads.net` v1.0; Facebook `FB_<canal>` em `facebook_tokens.txt` + `<canal>/id` em `facebook_paginas.json`, `graph.facebook.com` v26.0; YouTube `oauth/refresh_tokens/<canal>` + `oauth/client_id` + `oauth/client_secret` em `youtube.json`, id em `canais/<canal>` ou `youtube_canais.json:<canal>/id` | **Feito** (`nomes_token`, `nomes_id`, `nomes_youtube`, `HOSTS`, `GRUPOS`) |
| YouTube só coleta com `"autorizado": true`; senão `nao_autorizado` | **Feito** (inventário, `plano` e `youtube.coletar` — nada é chamado com a flag falsa) |
| Nomes antigos da rodada 1 valem DEPOIS dos reais | **Feito** (`chaves()` devolve `["IG_hp.futebol", "IG_FUTEBOL_TOKEN", "IG_TOKEN", "META_TOKEN"]`; `youtube_tokens.txt` continua lido depois do `youtube.json`) |
| PATCH `metricas/config.py`: `chaves()` reais primeiro; Instagram em `https://graph.instagram.com` (`host_instagram` no `PADRAO` e em `instagram.base_url`); `token_e_id` aceita id do `meta_tokens_meta.json` (via `chaves_pc`) e do `facebook_paginas.json`; YouTube via `youtube.json` além do `youtube_tokens.txt` | **Feito** (seção 3) |
| LEIA.md do `metricas` só no trecho das chaves | **Feito** (seção "Segredos" reescrita com a tabela da §4.3 + linha do comando `chaves`; o cabeçalho `## contas.json` virou `## O arquivo contas.json` por causa da regra 8 do formato de entrega) |
| Handle do `metricas/contas.json` (`usuario`) ou de `fila_api_pc.CANAIS` | **Feito** (`handle_da_conta`) |
| `python -m metricas coletar --simular` sobre pasta temporária com 6 contas × IG/Threads/Facebook (`FAKE_NAO_E_TOKEN_n`) → 0 `sem_token`; YouTube `nao_autorizado` com a flag falsa e `coletaria` com a verdadeira | **Feito** (`test_cli_simular_6_contas_zero_sem_token`: 18 linhas `coletaria (token: ok, id: ok)`, 0 `sem_token`; `test_cli_simular_youtube_coletaria_com_a_flag_verdadeira`) |
| Teste que captura stdout, stderr e o log (`app/logs` em tmp) e PROVA que nenhum valor falso aparece | **Feito** (`test_nenhum_valor_falso_em_stdout_stderr_log_excecao_nem_arquivo`: `--simular`, `chaves`, coleta com API ecoando o token, exceção `SemToken`, JSON gravado e `metricas_*.log` — nenhum `FAKE_NAO_E_TOKEN` em lugar nenhum, `***` presente) |
| ≥ 12 testes em `metricas/testes/test_chaves_pc.py` | **Feito** — 21 testes |
| Suíte do `metricas` continua verde (testes antigos atualizados se dependiam dos nomes antigos) | **Feito** — 51 passed (30 antigos intactos: os nomes antigos continuam valendo, então **nenhum teste antigo precisou mudar**) |

Extra: `python -m metricas chaves [--json] [--conta] [--rede] [--contas] [--segredos]` imprime o inventário (nunca um valor).

### A3 — Comandos reais

| Critério de pronto | Situação |
|---|---|
| `esteira/comandos_pc.py` com funções PURAS `argv_*` que devolvem a LISTA exata (§4.4) | **Feito** — `argv_baixar`, `argv_transcrever`, `argv_cortar`, `argv_versao_upload`, `argv_dublar_avulso`, `argv_estaticos_carrossel`, `argv_estaticos_story`, `argv_estaticos_destaques`, `argv_posts_render`, `argv_posts_canais`, `argv_story_clicavel_fila`, `argv_lote` |
| `argv_baixar(pedido, destino)` = `[PYTHON, ytdlp.py, "-f", "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080]/b", "--merge-output-format", "mp4", "-o", destino, "--no-playlist", "--no-warnings", "--download-sections", "*INI-FIM", "--force-keyframes-at-cuts", url]`, INI = hms(inicio−4), FIM = hms(fim+4), `hms` = HH:MM:SS.mmm; inicio/fim "MM:SS" / "HH:MM:SS" / segundos; pedido com `arquivo` → `None` + `copiar_trecho()` | **Feito** (golden com o exemplo da §4.4: `*00:03:22.000-00:04:08.000`; com o plano real: `*00:06:58.000-00:07:52.000`) |
| `argv_cortar(arq, ini, fim, gancho, streamer, saida, transcricao=None, fade_saida=None, dublar=False)` com extra na ordem `--transcricao`, `--fade-saida`, `--dublar` | **Feito** (igual ao argv de `lote.renderizar`) |
| `argv_estaticos_story(tipo, saida, **opcoes)` tipos novo_video/contagem/noticia/interativo, opções `--titulo --texto --imagem --video --fonte --data --hoje --selo` (ordem fixa) | **Feito** (tipo/opção desconhecidos → `ValueError` em português) |
| `argv_posts_render(canal, spec_json)` por canal (`posts_futebol.py` … `posts_destinos.py render <spec>`); `posts_canais.py` só genérico via `argv_posts_canais(subcomando, ...)` | **Feito** (GTA → `ValueError` apontando `estaticos.py`) |
| Constantes no topo: `PYTHON_PC` (`%LOCALAPPDATA%\Programs\Python\Python312\python.exe` via `os.path.expandvars`; literal no Linux) e `SCRIPTS_PC` = `raiz_drive()/"06 Projeto"/"scripts"` respeitando `HP_DRIVE` | **Feito** (`SCRIPTS_PC` é o valor na importação; `scripts_pc()` relê `HP_DRIVE` a cada chamada e é o padrão das funções) |
| Caminho com espaço SEM aspas na lista; `para_humano(argv)` cita | **Feito** |
| `dublar_por_padrao(pedido, config_json)` = criador `"idioma": "en"` sem `"dublar": false` | **Feito** |
| Proibidos: `ytdlp.py --saida`, `dublar.py --srt`, `--texto-arquivo`, `estaticos.py --pedido` — teste que varre TODAS as funções com vários pedidos | **Feito** (`test_nenhuma_funcao_usa_argumento_proibido`: descobre toda `argv_*` por `inspect`, falha se aparecer função nova sem amostra; 48 saídas + `COMANDOS_PADRAO`) |
| PATCH `esteira/config.py`: `COMANDOS_PADRAO` reflete os comandos reais (lista com marcadores) | **Feito** (`COMANDOS_PADRAO = deepcopy(comandos_pc.MODELOS)`; teste prova `montar_comando(cfg, nome, …)` == `argv_*`) |
| PATCH `esteira/plugins.py` (`BaixadorYtdlp.comando`, `DubladorScript`, `DesignerScript`) monta o argv via `comandos_pc`, mantendo `montar_comando` para `config.json → comandos` | **Feito** (`personalizado(cfg, nome)` decide: modelo igual ao padrão → `comandos_pc`; modelo trocado no `config.json` → `montar_comando`) |
| Testes golden em `esteira/testes/test_comandos_pc.py` (≥ 20 casos: pedido com arquivo, gringo `--dublar`, `fade_saida`, trechos/emenda com `--transcricao`, carrossel, story interativo, posts por canal) | **Feito** — 23 testes (vários casos cada: 4 variantes do `cortar`, 6 do `story`, 5 canais do `posts_render`, 5 subcomandos do `posts_canais`…) |
| 1 teste que roda a esteira em `--simular` (plugins simulados/espionados do conftest) com o pedido real de `tests/fixtures/pc_real/plano_corte_exemplo.json` convertido para pedido e confere o argv de cada etapa | **Feito** (`test_esteira_simulada_com_o_pedido_real_confere_o_argv_de_cada_etapa`: `pedido_de_plano` → `criar_pedido` → `amb.ciclo()` com `BaixadorYtdlp` real + `rodar` falso → argv do `ytdlp.py` registrado == `argv_baixar`; item chega a `05_revisao`; `argvs_do_pedido` confere `transcrever`, `cortar` (com `--transcricao` por causa do `cobrir`) e `versao_upload`) |
| Suíte da esteira continua verde | **Feito** — 179 passed (156 antigos + 23 novos) |

**Pela metade / não deu:** nada. O que é suposição está na seção 5; o que é decisão de produto, na 8.

## 2. Arquivos

**Novos**
- `app/hp_studio_nuvem/metricas/chaves_pc.py`
- `app/hp_studio_nuvem/metricas/testes/test_chaves_pc.py` (21 testes)
- `app/hp_studio_nuvem/esteira/comandos_pc.py`
- `app/hp_studio_nuvem/esteira/testes/test_comandos_pc.py` (23 testes)
- `docs/rodada2/A2a.md` (este)

**Da rodada 1, alterados**
- `app/hp_studio_nuvem/metricas/config.py`
- `app/hp_studio_nuvem/metricas/coleta.py`
- `app/hp_studio_nuvem/metricas/youtube.py`
- `app/hp_studio_nuvem/metricas/instagram.py`
- `app/hp_studio_nuvem/metricas/cli.py`
- `app/hp_studio_nuvem/metricas/contas.json` (exemplo sem segredo)
- `app/hp_studio_nuvem/metricas/LEIA.md` (só a seção "Segredos" + 1 linha na tabela de comandos + 1 cabeçalho)
- `app/hp_studio_nuvem/esteira/config.py`
- `app/hp_studio_nuvem/esteira/plugins.py`
- `app/hp_studio_nuvem/esteira/simulados.py` (1 linha)
- `app/hp_studio_nuvem/esteira/trabalhos.py` (1 linha)
- `app/hp_studio_nuvem/esteira/LEIA.md` (itens 6/"comandos", 10.3 e 11.3)
- `app/hp_studio_nuvem/esteira/testes/test_plugins.py` (3 testes reescritos)
- `app/hp_studio_nuvem/esteira/testes/test_fluxo.py`, `test_cli_gancho.py` (assinatura dos falsos de `baixar`)

Não toquei em `hpbase`, `qa_paridade`, `whatsapp_local`, `scripts/`, `tests/conftest.py`, `.claude`.

## 3. Patches (arquivo da rodada 1 → função → o que muda → por quê → teste → antes/depois)

### Patch 1 — `metricas/config.py`

- **`PADRAO`**: ganha `host_instagram = https://graph.instagram.com`, `versao_instagram = v21.0`; `versao_graph` (Facebook) passa de `v21.0` para `v26.0`; `arquivos_segredo` passa a ter os 7 grupos de `chaves_pc.ARQUIVOS_PADRAO` (`meta`, `meta_meta`, `facebook`, `facebook_paginas`, `youtube_oauth`, `youtube_canais`, `youtube`). Por quê: §4.3. Teste: `test_instagram_fala_com_graph_instagram_e_facebook_v26`.
- **`_sensivel(chave, arquivo)`**: delega a `chaves_pc.sensivel` — toda linha de `*_tokens.txt` é segredo (menos `*_ID`/`*_CANAL`); caminhos de id (`contas/…/id`, `canais/…`, `oauth/client_id`) não são. Antes `IG_hpgta6` não contava como sensível (não tem "TOKEN" no nome) e o valor **não seria apagado** das mensagens. Teste: `test_sensivel_separa_token_de_id`, `test_credenciais_aceita_lista_de_arquivos_e_json_por_caminho`.
- **`Credenciais.__init__/obter`**: `arquivos[grupo]` aceita string ou lista; `obter(grupos, *chaves)` aceita um grupo ou tupla de grupos (procura em ordem: reais antes dos antigos); `.txt` lido por `chaves_pc.valor_txt` (aceita `@` no nome, aspas, `#`) e `.json` por `chaves_pc.valor_json` (caminho `a/b/c`). Antes só `ler_segredo(arquivo, chave)` em um arquivo.
  - Antes: `arquivo = self.arquivos.get(grupo, grupo); for chave in chaves: v = ler_segredo(arquivo, chave, pasta=self.pasta)`
  - Depois: `for arquivo in self._arquivos(grupos): for chave in chaves: v = chaves_pc.valor(self._pasta(), arquivo, chave)`
- **`chaves(rede, conta, cfg_rede)`**: devolve override do `contas.json` → nomes reais → antigos (`chaves_pc.nomes_token/nomes_id/nomes_youtube`). Antes: `[cfg.chave_token, f"{pref}_{c}_TOKEN", f"{pref}_TOKEN", "META_TOKEN"]`. Depois (IG futebol): `["IG_hp.futebol", "IG_FUTEBOL_TOKEN", "IG_TOKEN", "META_TOKEN"]`; id `["contas/IG_hp.futebol/id", "IG_FUTEBOL_ID"]`; YouTube `refresh = ["oauth/refresh_tokens/gta", "YT_GTA_REFRESH_TOKEN", "YT_REFRESH_TOKEN"]`. Teste: `test_chaves_do_config_reais_primeiro_antigos_depois`.
- **`token_e_id`**: lê token em `GRUPOS[rede]["token"]` e id em `GRUPOS[rede]["id"]` (`meta_tokens_meta.json` → `meta_tokens.txt`; Facebook `facebook_tokens.txt` → `meta_tokens.txt` e `facebook_paginas.json` → `meta_tokens.txt`); a mensagem do `SemToken` diz o nome real **e** o antigo e o arquivo, nunca o valor: `instagram/carros: falta token (chave IG_hp.carros (ou o antigo IG_CARROS_TOKEN) em meta_tokens.txt)`. Teste: `test_token_e_id_le_o_real_primeiro_e_o_id_do_meta_json`, `test_token_e_id_facebook_le_facebook_tokens_e_paginas`, `test_sem_token_mensagem_so_com_nomes`; o antigo `test_sem_token_e_youtube_nao_autorizado` (que exige `TH_GTA_TOKEN` no detalhe) continua passando sem mudar.
- **`Contexto.base_instagram`** (nova): `https://graph.instagram.com/v21.0`. `base_graph` fica para o Facebook.

### Patch 2 — `metricas/instagram.py` → `base_url(cfg_rede, ctx)`
- Antes: `host = cfg_rede.get("host") or ctx.cfg["host_graph"]; f"{host}/{ctx.cfg['versao_graph']}"` (falava com `graph.facebook.com`).
- Depois: `return ctx.base_instagram` (ou `host`/`versao` da conta se vierem). Teste: `test_instagram_fala_com_graph_instagram_e_facebook_v26` (1ª chamada = `https://graph.instagram.com/v21.0/<id>`).

### Patch 3 — `metricas/youtube.py` → `_token_oauth`, `coletar`
- `cred.obter("youtube", …)` vira `cred.obter(GRUPOS["youtube"]["refresh"|"client_id"|"client_secret"|"canal"|"chave_api"], …)`: `youtube.json` (`oauth/refresh_tokens/<canal>`, `oauth/client_id`, `oauth/client_secret`, `api_key`, `canais/<canal>`) → `youtube_canais.json` → `youtube_tokens.txt` antigo. Mensagens de `SemToken` citam os nomes novos. Teste: `test_youtube_coleta_pelo_youtube_json_oauth` (o POST ao `/token` leva o refresh e o client_secret do `youtube.json`, comparados por hash; com a flag falsa `chamadas == []`); o antigo `test_youtube_sem_oauth_pula_analytics` continua verde.

### Patch 4 — `metricas/coleta.py` → `plano()` (+ import)
- Antes: lia cada chave com `cred.tem(...)` (abria os valores). Depois: usa `chaves_pc.inventario(pasta_segredos, cfg, contas, redes)` (só nomes) e imprime, mantendo o formato antigo (`gta/instagram: coletaria (token: ok, id: ok)`), com o nome real e o antigo quando falta: `filmes/threads: sem_token (token: falta TH_hp.filmes (ou o antigo TH_FILMES_TOKEN) em meta_tokens.txt, id: ok)`; YouTube: `coletaria (canal: ok, chave: falta, analytics: ok)`. `plano` também tira o import de `chaves` que não usa mais. Teste: `test_plano_sem_token_diz_o_nome_real_e_o_antigo`, `test_cli_simular_6_contas_zero_sem_token`; o antigo `test_cli_simular_nao_chama_nem_grava` passa sem mudar.

### Patch 5 — `metricas/cli.py` → `montar_parser`, `main`
- Subcomando novo `chaves` (`--conta`, `--rede`, `--json`, `--contas`, `--segredos`) que imprime `chaves_pc.inventario`/`resumo`. Teste: `test_cli_chaves_mostra_inventario_sem_valor`.

### Patch 6 — `metricas/contas.json` (exemplo) e `metricas/LEIA.md`
- `contas.json`: `_leia` reescrito; `versao_instagram`/`host_instagram`; `versao_graph: v26.0`; `arquivos_segredo` com os 7 grupos. As 6 contas não mudam.
- `LEIA.md`: seção "Segredos (formato esperado — suposição…)" vira "Segredos (formato REAL do PC — §4.3…)" com a tabela por rede; linha `python -m metricas chaves` na tabela de comandos; `## contas.json` → `## O arquivo contas.json` (regra 8: nenhuma linha `## nome.ext`).

### Patch 7 — `esteira/config.py` → `COMANDOS_PADRAO`
- Antes (palpite da rodada 1, com os 4 argumentos proibidos):
  `{"baixar": ["{python}", "{scripts}/ytdlp.py", "{url}", "--saida", "{saida}"], "dublar": [..., "--srt", ...], "falar": [..., "--texto-arquivo", ...], "estaticos": [..., "--pedido", ...]}`
- Depois: `COMANDOS_PADRAO = copy.deepcopy(comandos_pc.MODELOS)` — 12 modelos reais (`baixar`, `transcrever`, `cortar`, `dublar`, `versao_upload`, `estaticos_carrossel`, `estaticos_story`, `estaticos_destaques`, `posts_render`, `posts_canais`, `story_clicavel_fila`, `lote`) com marcadores `{python} {scripts} {url} {entrada} {saida} {inicio} {fim} {gancho} {streamer} {transcricao} {tipo} {script} {subcomando} {acao}`. **Sem `falar`** (o `dublar.py` não sintetiza frase avulsa). Teste: `test_modelos_do_config_batem_com_as_funcoes`, `test_nenhuma_funcao_usa_argumento_proibido`; o antigo `test_montar_comando_e_config_json` (modelo personalizado no `config.json`) continua verde.

### Patch 8 — `esteira/plugins.py`
- **`Baixador` (Protocol)** e **`BaixadorYtdlp.comando/baixar`**: assinatura `baixar(url, destino, pedido=None)`; `comando` devolve `comandos_pc.argv_baixar({**pedido, "video_url": url}, destino/"bruto.mp4", python=cfg.python, scripts=cfg.pasta_scripts)` quando `scripts\ytdlp.py` existe (ou `montar_comando` se o `config.json` personalizou `baixar`); yt-dlp do PATH continua como plano B.
  - Antes: `return montar_comando(self.cfg, "baixar", url=url, saida=destino)` (= `ytdlp.py <url> --saida <pasta>`).
  - Depois: `-f … -o <pasta>\bruto.mp4 --no-playlist --no-warnings [--download-sections "*INI-FIM" --force-keyframes-at-cuts] <url>`.
  - Teste: `test_baixador_usa_scripts_ytdlp` (reescrito: `-o`, sem `--saida`; com `inicio/fim` do lote o argv == `argv_baixar`), `test_esteira_simulada_com_o_pedido_real_confere_o_argv_de_cada_etapa`.
- **`montar_comando`**: preenche pelo `comandos_pc.preencher` (`{scripts}/x.py` vira `Path(scripts)/"x.py"`, barra certa no Windows); `KeyError` continua virando `ErroPermanente`. **`personalizado(cfg, nome)`** (nova): o modelo do `config.json` é diferente do padrão?
- **`DubladorScript`**: antes `dublar(item, legenda, pedido)` rodava `dublar.py --srt legenda --saida dublagem.wav` (não existe). Agora: `comando(corte, transcricao, inicio, fim, saida)` = `argv_dublar_avulso`; `dublar_corte(...)` roda o `dublar.py` real sobre um corte já renderizado; `dublar(item, legenda, pedido)` (interface da etapa 03) só funciona com `item/final.mp4` + transcrição PT (`.json`) e devolve `final_dublado.mp4` — sem corte, `ErroPermanente` explicando que na esteira o gringo sai pelo `cortar.py --dublar`. Teste: `test_dublador_chama_script` (reescrito), `test_dublador_sem_script` (passa sem mudar).
- **`NarradorToqueHP._sintetizar_script`**: sem `comandos.falar` no `config.json` → `ErroPermanente` claro ("o dublar.py do PC não tem --texto-arquivo: configure comandos.falar … ou injete sintetizar="). `test_narrador_*` (sintetizador injetado) passam sem mudar.
- **`DesignerScript`** (+ `spec_carrossel_gta(pedido)`): `comando(item, pedido, pasta) -> (argv, script, alvo)`; GTA carrossel → grava `spec_carrossel.json` (de `laminas`/`spec`) e `argv_estaticos_carrossel(spec, arte, tiktok=)`; GTA story → `argv_estaticos_story(modelo, arte/story.jpg, titulo=…, **opcoes)`; GTA `estatico` → `ErroPermanente` (não há arte avulsa de feed no `estaticos.py`); canais → grava `post_spec.json` (do `pedido["spec"]`, com `saida` = `arte\`) e `argv_posts_render(canal, spec)`; `gerar` filtra `_feed`/`_story`/`_NN` conforme o tipo. Antes: `estaticos.py --pedido pedido.json --saida arte\`. Teste: `test_designer_chama_estaticos` (reescrito), `test_designer_sem_script` (reescrito), `test_designer_posts_por_canal_e_story_gta`.

### Patch 9 — `esteira/simulados.py` → `BaixadorSimulado.baixar` e `esteira/trabalhos.py` → `TrabalhoBaixar.executar`
- `baixar(url, destino, pedido=None)` (1 linha) e `self.p.baixador.baixar(pedido["fonte_url"], tmp, pedido=pedido)` (1 linha): o Baixador real precisa do `inicio`/`fim` do pedido para baixar só o trecho. Os 4 falsos de `baixar` em `test_fluxo.py` (3) e `test_cli_gancho.py` (1) ganharam `pedido=None`. Teste: toda a suíte da esteira.

### Patch 10 — `esteira/LEIA.md`
- Linha `comandos` da tabela de `config.json`, item 10.3 (era a lista dos 4 comandos proibidos; agora descreve o que o app roda de verdade e as suposições que sobraram) e item 11.3.

## 4. Testes (números reais, saída do pytest)

| Comando | passed | failed | skipped | tempo |
|---|---|---|---|---|
| `cd app/hp_studio_nuvem && python3 -m pytest -q -p no:cacheprovider metricas esteira` (**o pedido da tarefa**) | **230** | 0 | 0 | **13,95 s** |
| `… metricas` (só o pacote: 30 antigos + 21 novos) | 51 | 0 | 0 | 0,22 s |
| `… esteira/testes/test_comandos_pc.py esteira/testes/test_plugins.py` | 42 | 0 | 0 | 0,77 s |
| `… hpbase qa_paridade` (vizinhos que importam `esteira.config`/`hpbase`; não toquei) | 150 | 0 | 0 | 12,51 s |
| `cd /home/user/HP && python3 -m pytest -q -p no:cacheprovider tests` | (só `conftest.py` + fixtures: "no tests ran") | — | — | — |

Antes dos meus patches o mesmo comando dava 186 passed (13,41 s): +44 testes (21 + 23), nenhum antigo removido. Módulos da rodada 1 que toquei: `metricas` (51) e `esteira` (179, dentro dos 230) — verdes. Nenhum teste usa rede, relógio real, Windows, ffmpeg (os de `comandos_pc` são puros; o de esteira usa os plugins simulados + `rodar` falso) nem segredo real (valores `FAKE_NAO_E_TOKEN_n` em `tmp_path`).

## 5. Suposições que sobraram

| Suposição | Arquivo | Onde trocar |
|---|---|---|
| Host/versão do YouTube no inventário: `https://www.googleapis.com` / `v3` (a §4.3 não diz) | `metricas/chaves_pc.py` | `HOSTS["youtube"]` (e `CHAVE_HOST`) |
| Nomes dos grupos novos em `arquivos_segredo` (`meta_meta`, `facebook`, `facebook_paginas`, `youtube_oauth`, `youtube_canais`) — escolhidos para não colidir com `meta`/`youtube` da rodada 1 que uma cópia antiga do `contas.json` do Antônio possa sobrepor | `metricas/chaves_pc.py` | `ARQUIVOS_PADRAO`, `GRUPOS` |
| Falta de **id** também sai como `sem_token` (com `"falta": ["id"]`), como o coletor já reportava | `metricas/chaves_pc.py` | `_entrada_meta` / `_entrada_youtube` |
| Facebook coleta em `v26.0` (`versao_graph`); o `metricas_api.py` do PC pode usar outra | `metricas/config.py` | `PADRAO["versao_graph"]` e `contas.json` |
| `transcrever.py`: positional `arquivo` antes de `--id-streamer` (argparse aceita as duas ordens; a §4.4 só dá o `usage`) | `esteira/comandos_pc.py` | `MODELOS["transcrever"]` |
| `estaticos.py story --selo`: valor quando vem texto, bandeira solta quando `True` | `esteira/comandos_pc.py` | `argv_estaticos_story` |
| `argv_baixar` sem `inicio`/`fim` baixa o vídeo inteiro (sem `--download-sections`), como `baixar.py` sem `--so-trecho`; `inicio − 4 < 0` vira `00:00:00.000` | `esteira/comandos_pc.py` | `argv_baixar`, `hms` |
| Sem `corte` no pedido, a janela do `cortar.py` é `[4, 4 + (fim − inicio)]` (o `lote.py` encosta em frases pela transcrição — não é puro) | `esteira/comandos_pc.py` | `argvs_do_pedido` |
| Emenda (`trechos/zoom/cobrir/bipes/tarjas/selos`): `cortar.py` recebe `<bruto>_ed<n>.mkv` + `--transcricao <bruto>_ed<n>.json`, com `n` = número do item no plano (`"n"`/`lote_n`) | `esteira/comandos_pc.py` | `argvs_do_pedido` (`CAMPOS_EMENDA`) |
| `arquivo_corte`: caracteres proibidos no Windows no gancho viram espaço; mês por extenso em `MESES` | `esteira/comandos_pc.py` | `arquivo_corte` |
| `pedido_de_plano`: item com `render_status`/`agendado`/`upload` é "concluído" e o `arquivo` dele é o corte pronto (descartado); sem isso, `arquivo` = trecho já baixado → `arquivos: [arquivo]`; crédito = `Crédito: @x` da legenda, senão o do `config.json`, senão `@<streamer>` | `esteira/comandos_pc.py` | `pedido_de_plano`, `CAMPOS_RESULTADO`, `_RX_CREDITO` |
| Designer GTA: story usa `modelo` (padrão `noticia`) e `opcoes` do pedido; `estatico` não tem comando no `estaticos.py` (erro); canais exigem `pedido["spec"]` (JSON do `posts_<canal>.py`) — não inventei o spec por modelo | `esteira/plugins.py` | `DesignerScript.comando`, `spec_carrossel_gta` |
| `DubladorScript.dublar` na etapa 03 só com `final.mp4` + `transcricao_pt.json`/`transcricao.json` | `esteira/plugins.py` | `DubladorScript.dublar` |

## 6. Depende do Antônio

Nenhum token, permissão, clique ou instalação novos para esta tarefa. Na próxima integração no PC (para leigo):

1. Abrir o PowerShell em `G:\Meu Drive\Hypado\06 Projeto\app\hp_studio_nuvem` e rodar `python -m metricas chaves`. Ele lista, por conta e rede, o **nome** da chave e em que arquivo está (nunca mostra o valor). Tudo `ok` = pode coletar. `sem_token` com `falta: id` = o `publicador_meta.py` ainda não gravou o id daquela conta no `meta_tokens_meta.json` (rode o `publicador_meta.py` uma vez) ou falta o `facebook_paginas.json` (`hp publicar facebook-token`).
2. YouTube continua `nao_autorizado` até o Google aprovar a auditoria; quando aprovar, trocar `"autorizado": true` no `contas.json` de cada canal e rodar `hp publicar youtube-autorizar --canal <canal>` (hoje só o GTA tem refresh token).
3. Se existir `H:\HypadoLocal\metricas\contas.json` copiado na rodada 1, apagar ou recopiar o novo exemplo (o antigo tem `versao_graph: v21.0` e só 2 arquivos em `arquivos_segredo`; os grupos novos continuam valendo, mas o Facebook ficaria em v21.0).
4. Esteira: `python -m esteira iniciar` grava os 12 modelos reais no `config.json` (se o `config.json` da rodada 1 existir com `comandos` antigos — `--saida`, `--srt`, `--pedido` — apagar a chave `comandos` dele).

## 7. Pendências para o Diretor

Nenhuma (nada mexe em `.claude\`).

## 8. Decisões em aberto / conflitos

1. **Voz no GTA.** O plano real (`plano_corte_exemplo.json`) tem `toque_hp` (narração) e criadores gringos dublados no canal GTA, mas a regra da rodada 1 (`esteira/constantes.py → CANAIS_COM_VOZ = destinos, receitas, carros, filmes`) faz `validar_pedido` recusar `narrar_toque_hp`/`dublar` no GTA ("dublagem/voz sintética só em destinos, receitas, carros e filmes"). O teste da esteira registra o conflito (`assert any("voz sintética" in e …)`) e roda com `narrar_toque_hp = False`. Resolver é 1 linha (incluir `"gta"` em `CANAIS_COM_VOZ`); não fiz por ser regra de conteúdo — o CLAUDE.md só proíbe voz sintética no **futebol**.
2. **Quem renderiza na esteira da nuvem.** O Editor continua o ffmpeg próprio (`editor.py`); não há plugin que chame o `cortar.py` do PC. `argv_cortar` está pronto e um `EditorCortar` (1 classe: `argv_cortar(... dublar=dublar_por_padrao(...))` + `rodar`) daria paridade total com o PC, mas mudaria a "segunda opinião" em cópia — decisão do Diretor.
3. **Narrador Toque HP** não tem sintetizador no PC pelo `dublar.py` (sem `--texto-arquivo`). Para rodar de verdade falta o comando do Piper (`H:\HypadoLocal\modelos\piper`, `pylib`) em `comandos.falar` do `config.json` (`{entrada}` texto, `{saida}` wav) — ninguém sabe o argv real; o plugin dá erro claro até lá.
4. **Status do inventário** mistura `sem_token` (token) e `sem_token` com `falta: ["id"]`; se o painel quiser distinguir, basta ler `falta` — ou trocar para `sem_id` em `chaves_pc._entrada_meta` (o `coletar` seguiria igual).
