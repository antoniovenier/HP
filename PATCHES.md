# PATCHES.md — rodada 2 (01/10/2026): o que mudou nos arquivos da rodada 1

Regra 5 do enunciado: arquivo da rodada 1 que muda **não é reenviado inteiro**; vai aqui, por função,
com o motivo e o teste que cobre. O diff unificado de TODOS os arquivos alterados está em
`patches/rodada2_rodada1_alterados.diff` (gerado por `git diff c0aba96..HEAD`): no PC dá para aplicar
com `git apply` (ou à mão, função por função, seguindo este arquivo). Os únicos arquivos da rodada 1
que mudaram **mais da metade** e por isso vêm inteiros no compilado: `app/hp_studio_nuvem/hpbase/trava.py`, `app/hp_studio_nuvem/esteira/agendador.py`, `app/hp_studio_nuvem/esteira/testes/test_agendador_aviso.py` e `app/hp_studio_nuvem/metricas/config.py`
(o compilador decide pelo `git diff -M50%`: menos de 50 % igual = reescrito; a lista exata está no
cabeçalho do `ENTREGA_NUVEM_HP_STUDIO_2.md`).

Como ler cada entrada: **arquivo → função → o que muda → por quê → teste que cobre** (antes/depois
curto quando ajuda). "Sessão" = feito pela sessão principal; A1/A2a/A2b/A3/E2 = agente da rodada 2
(relatório completo em `docs/rodada2/<agente>.md`).

## 0. Renomeio do pacote e caminhos (sessão)

- **`app/hp_studio/` → `app/hp_studio_nuvem/`** (git mv, 100 % igual): o repositório passa a ter o
  mesmo nome do pacote irmão do PC. Nada muda nos imports curtos (`from hpbase import …`,
  `import esteira`): cada `testes/conftest.py` usa `parents[2]`, e os `__init__.py` de `esteira`,
  `metricas`, `qa_paridade` e `whatsapp_local` põem a própria pasta-mãe no `sys.path`.
- **Scripts que procuram o pacote** ganharam `hp_studio_nuvem` ANTES de `hp_studio` na lista de
  candidatos (função, antes → depois):
  - `scripts/story_post.py::_achar_hp_studio` — `cands += [AQUI.parent/"app"/"hp_studio", …]` →
    `[AQUI.parent/"app"/"hp_studio_nuvem", AQUI.parent/"06 Projeto"/"app"/"hp_studio_nuvem",
    Path(r"G:\Meu Drive\Hypado\06 Projeto\app\hp_studio_nuvem"), …os antigos]`; `HP_APP` também aceita `HP_APP\hp_studio_nuvem`.
  - `scripts/reel_futebol_base.py::caminho_hp_studio` — idem.
  - `scripts/reenvio_seguro.py::_por_hp_studio_no_caminho` — `for p in (Path(c), Path(c)/"hp_studio")` →
    `(Path(c), Path(c)/"hp_studio_nuvem", Path(c)/"hp_studio")`.
  - `scripts/painel/espelho_banco.py::_preparar_hpbase` e `scripts/pagina_links/gerar_fundos.py::_preparar_hpbase` — idem.
  - `scripts/testes/test_story_post.py` (topo): `APP/"hp_studio_nuvem"` antes de `APP/"hp_studio"`.
  - Teste que cobre: a suíte inteira dos scripts (`cd scripts && python -m pytest -q testes`) importa o `hpbase` por esse caminho.
- **`app/hp_studio_nuvem/metricas/cli.py`**: `AGENDADO_PADRAO = r"G:\…\app\hp_studio\metricas\agendado.py"` → `…\app\hp_studio_nuvem\metricas\agendado.py` (é o caminho que o `agendar-6h` imprime para o `schtasks`).
- **Textos** (`LEIA.md` de cada módulo, `scripts/LEIA_*.md`, `app/manuais/*.md`, `docs/CONVENCOES.md`, `docs/compilar_entrega.py`): toda menção a `app\hp_studio\` virou `app\hp_studio_nuvem\` (substituição literal; nenhuma outra linha mudou nos manuais).

## 1. hpbase (A1, A3, sessão)

### `hpbase/trava.py` — REESCRITO (vem inteiro) — A1
- **Funções novas** `_desde(dados, mtime)`, `ler_trava(caminho)`, `trava_abandonada(info, agora)`; **mudam** `TravaPesada.adquirir` e `soltar`.
- **O que muda:** lê os DOIS formatos de `pesado.lock` — o do PC `{"quem", "desde": "AAAA-MM-DDTHH:MM"}` (sem pid, vale 30 min) e o da rodada 1 `{"dono", "pid", "desde": epoch}` (com pid: "processo morto ou 3 h"); grava `quem` + `desde` ISO + `dono` + `pid` + `desde_epoch`; lock ilegível (JSON quebrado, `desde` absurdo) usa a data de modificação do arquivo e NUNCA vira "velha" de graça; `agora=` injetado vale para a janela 18h–22h30 E para a idade da trava.
- **Por quê:** §3.2 — o lock do PC sem pid quebrava a nossa trava com `ValueError`.
- **Teste:** `hpbase/testes/test_trava_pc.py` (13) + `test_hpbase.py` e `esteira/testes/test_trava.py` (antigos, verdes).
- Antes: `velha = time.time() - float(atual.get("desde", 0)) > TRAVA_VELHA_SEG; if velha or not _pid_vivo(...)`. Depois: `atual = ler_trava(self.caminho); if atual is None or trava_abandonada(atual, agora): unlink`.

### `hpbase/caminhos.py` e `hpbase/__init__.py` — A1
- Novas `pasta_esteira()` = `raiz_local()/HP_ESTEIRA_NOME` (padrão `esteira_sombra`) e `pasta_paridade()` = `pasta_app()/HP_PARIDADE_NOME` (padrão `paridade_nuvem`); exportadas no `__init__` junto com `ler_trava`, `trava_abandonada`. Por quê: §3.2 (o PC já usa `H:\HypadoLocal\esteira` e `app\paridade`). Teste: `test_trava_pc.py::test_pasta_esteira_e_paridade_padrao/_por_variavel`.

### `hpbase/marca.py` — NOVO (sessão) e `hpbase/testes/test_marca.py` — NOVO (A3)
- Não é patch: entra inteiro. Citado aqui porque `scripts/reel_futebol_arte.py` passa a depender dele (abaixo).

## 2. esteira (A1, A2a, A2b, sessão)

### `esteira/agendador.py` — REESCRITO (vem inteiro) — A1
- `id_fila(post, rede)`: `f"{post['item']}__{rede}"` → `fila_api_pc.id_padrao(canal, rede, tipo, quando, slug)` (convenção de §4.1: `gta_2026-09-30_ig_reel_1830`, `carros_2026-09-30_1830_hb20-x-onix_th_texto`).
- `montar_registro_fila(post, rede, midia, capa, pasta_fila=None, existe=None, validar=True)`: montava o dict SUPOSTO (`origem, midia, agendar_para, status`) → chama `fila_api_pc.montar_item` (conta = handle, `arquivos[]`, `quando "AAAA-MM-DD HH:MM"` em Brasília, `estatico→feed`, `threads_texto→texto` com `arquivos: []`, `capa` só no reel) e converte `ErroFilaApi` em `ErroPermanente("<rede>: <mensagem do publicador>")`.
- `ler_confirmacao(id_, pasta_fila)`: olhava `status in STATUS_OK/STATUS_FALHA` no dict → `fila_api_pc.ler_confirmacao` (`feitos\` = publicado + link + media_id; `erros\` = erro + mensagem; resto `None`).
- `AgendadorFilaApi.agendar/conferir`: em modo real rede ∉ {instagram, threads} → `ErroPermanente` antes de copiar mídia; idempotência olha TODAS as subpastas (o publicador MOVE o arquivo para `feitos\`); sombra continua em `esteira_sombra\sombra\fila_api`.
- **Por quê:** §4.1/§4.2 (formato real da fila). **Teste:** `esteira/testes/test_agendador_aviso.py` (13), `test_fluxo.py`, `test_retomada.py`.

### `esteira/config.py` — A1, A2a, sessão
- `pasta_scripts_padrao()` (nova): `<Drive>\06 Projeto\scripts` quando existe, senão `<Drive>\scripts`; `Config.__post_init__` usa ela (A1; §3.2). `carregar_config`: raiz padrão = `hpbase.pasta_esteira()` (A1). Teste: `esteira/testes/test_config_pc.py`.
- `COMANDOS_PADRAO`: os 4 modelos palpite (`ytdlp.py --saida`, `dublar.py --srt`, `--texto-arquivo`, `estaticos.py --pedido`) → `copy.deepcopy(comandos_pc.MODELOS)`: 12 modelos reais (`baixar, transcrever, cortar, dublar, versao_upload, estaticos_carrossel, estaticos_story, estaticos_destaques, posts_render, posts_canais, story_clicavel_fila, lote`), sem `falar` (A2a; §4.4). Teste: `test_comandos_pc.py::test_modelos_do_config_batem_com_as_funcoes`, `::test_nenhuma_funcao_usa_argumento_proibido`.
- `Config.redes_api` / `redes_manuais`: `["instagram","threads","facebook","youtube"]` / `["tiktok","pinterest"]` → `["instagram","threads"]` / `["facebook","youtube","tiktok","pinterest"]` (sessão): a fila real só aceita IG e Threads (§4.2 `_validar`); em modo real, Facebook/YouTube iam para `99_erros`; agora esperam `<rede>_ok.json` até o `publicar\` do PC ser plugado. Teste: suíte da esteira (351).

### `esteira/plugins.py` — A2a
- `Baixador` (Protocol) e `BaixadorYtdlp.comando/baixar(url, destino, pedido=None)`: `ytdlp.py <url> --saida <pasta>` → `comandos_pc.argv_baixar(...)` (`-f … -o <pasta>\bruto.mp4 --no-playlist --no-warnings [--download-sections "*INI-FIM" --force-keyframes-at-cuts] <url>`); yt-dlp do PATH continua como plano B.
- `montar_comando`: preenche pelo `comandos_pc.preencher`; `personalizado(cfg, nome)` (nova) decide se o `config.json` trocou o modelo (aí vale o `config.json`).
- `DubladorScript`: `dublar.py --srt … --saida …` (não existe) → `argv_dublar_avulso` sobre um corte já renderizado (`dublar_corte`); `dublar(item, legenda, pedido)` exige `final.mp4` + transcrição PT, senão `ErroPermanente` explicando que o gringo sai pelo `cortar.py --dublar`.
- `NarradorToqueHP._sintetizar_script`: sem `comandos.falar` → `ErroPermanente` claro (o `dublar.py` não tem `--texto-arquivo`).
- `DesignerScript.comando/gerar`: `estaticos.py --pedido` → GTA carrossel = `spec_carrossel.json` + `argv_estaticos_carrossel`; GTA story = `argv_estaticos_story(modelo, …)`; canais = `post_spec.json` + `argv_posts_render(canal, spec)`.
- **Teste:** `test_plugins.py` (3 reescritos), `test_comandos_pc.py::test_esteira_simulada_com_o_pedido_real_confere_o_argv_de_cada_etapa`.

### `esteira/simulados.py` (1 linha) e `esteira/trabalhos.py` (1 linha) — A2a
- `BaixadorSimulado.baixar(url, destino, pedido=None)` e `TrabalhoBaixar.executar`: `baixar(pedido["fonte_url"], tmp, pedido=pedido)` (o baixador real precisa de `inicio/fim`).

### `esteira/pedido.py` — A2b, sessão
- `normalizar_pedido(dados, config_json=None)`: se `pedido_pc.eh_pedido_pc(dados)` (tipo `corte`/`texto`, `data` ou prioridade inteira sem `horario_alvo`) converte com `pedido_pc.para_esteira` antes do resto (A2b; §4.5 "a sua esteira tem que aceitar este formato"). Import novo `from . import pedido_pc`. Teste: `test_pedido_pc.py::test_normalizar_pedido_reconhece_o_formato_real` e os 22 antigos.
- `validar_pedido`: mensagem `"dublagem/voz sintética só em destinos, receitas, carros e filmes"` → `"… só em gta, destinos, receitas, carros e filmes"` (sessão; ver `constantes.py`).

### `esteira/constantes.py` — sessão
- `CANAIS_COM_VOZ = ("destinos", "receitas", "carros", "filmes")` → `("gta", "destinos", "receitas", "carros", "filmes")`. Por quê: o `config.json` real do GTA (§4.5) tem `"dublagem"` com `"credito": "dublado por HP"` e 19 criadores `"idioma": "en"` que "saem dublados"; a regra de conteúdo só proíbe voz sintética no futebol. Teste: `test_pedido.py` (gta dubla, futebol não), `test_pedido_pc.py::test_gringo_no_gta_dubla_como_o_pc`, `test_comandos_pc.py` (plano real com Toque HP valida).

### `esteira/motor.py` — sessão
- `_importar_json`: `dados = ler_json(arq)` → `dados = pedido_pc.ler_pedido_pc(arq, agora=time.time()); if dados is None: return []`. Por quê: §4.5 "pedido solto só é lido depois de 2 s parado (nada meio gravado)". Teste: `test_fluxo.py::test_pedido_solto_em_01_vira_item` (recém-gravado não entra; envelhecido entra), `test_pedido_pc.py::test_pedido_solto_real_importado_pelo_motor…`, `test_retomada.py`.

### `esteira/LEIA.md` — A1, A2a
- Linhas da fila (`esteira_sombra`, formato real), `comandos` (12 modelos reais), itens 10.3 e 11.3.

### Testes da esteira alterados
- `test_agendador_aviso.py` (fila reescrita; aviso intacto), `test_plugins.py` (3 testes), `test_fluxo.py`, `test_cli_gancho.py` (assinatura `baixar(..., pedido=None)`), `test_pedido.py` (voz no GTA), `test_retomada.py` e `conftest.py` (`envelhecer`: regra dos 2 s).

## 3. metricas (A2a, sessão)

### `metricas/config.py`
- `PADRAO`: + `host_instagram = https://graph.instagram.com`, `versao_instagram = v21.0`; `versao_graph` (Facebook) `v21.0` → `v26.0`; `arquivos_segredo` com os 7 grupos de `chaves_pc.ARQUIVOS_PADRAO`.
- `_sensivel(chave, arquivo)`: delega a `chaves_pc.sensivel` — toda linha de `*_tokens.txt` é segredo (menos `*_ID`/`*_CANAL`). Antes `IG_hpgta6` não era mascarado.
- `Credenciais.__init__/obter`: `arquivos[grupo]` aceita lista; `.txt` por `chaves_pc.valor_txt` (aceita `@`, aspas, `#`), `.json` por `chaves_pc.valor_json` (caminho `a/b/c`).
- `chaves(rede, conta, cfg_rede)`: override do `contas.json` → nomes REAIS (`IG_hp.futebol`, `contas/IG_hp.futebol/id`, `oauth/refresh_tokens/gta`…) → antigos (`IG_FUTEBOL_TOKEN`…).
- `token_e_id`: lê pelos grupos reais (`meta_tokens_meta.json` → `meta_tokens.txt`; `facebook_tokens.txt` + `facebook_paginas.json`); a mensagem do `SemToken` cita o nome real e o antigo, nunca o valor.
- `Contexto.base_instagram` (nova). **Teste:** `metricas/testes/test_chaves_pc.py` (21) + os 30 antigos sem mudar.

### `metricas/instagram.py::base_url` — `graph.facebook.com/v21.0` → `ctx.base_instagram` (`https://graph.instagram.com/v21.0`).
### `metricas/youtube.py::_token_oauth, coletar` — lê `youtube.json` (`oauth/refresh_tokens/<canal>`, `oauth/client_id`, `oauth/client_secret`, `canais/<canal>`) → `youtube_canais.json` → `youtube_tokens.txt` antigo.
### `metricas/coleta.py::plano` — usa `chaves_pc.inventario` (só NOMES; não abre valores); mensagem `sem_token` cita o nome real e o antigo.
### `metricas/cli.py` — subcomando novo `chaves` (`--conta --rede --json --contas --segredos`); `AGENDADO_PADRAO` (seção 0).
### `metricas/contas.json` → **`metricas/contas_exemplo.json`** (sessão; regra 3 da Seção 2: nome de segredo bloqueia a cópia no PC)
- O exemplo sem segredo mudou de nome e vem INTEIRO como arquivo novo; **apagar** `06 Projeto\app\hp_studio_nuvem\metricas\contas.json` no PC se ele existir. `metricas/config.py::caminho_config`: `Path(__file__).with_name("contas.json")` → `with_name("contas_exemplo.json")` (a cópia do Antônio continua em `H:\HypadoLocal\metricas\contas.json`, que não é deste repositório). Conteúdo (A2a): `_leia`, `host_instagram`, `versao_graph v26.0`, 7 grupos em `arquivos_segredo`.
### `metricas/LEIA.md` — seção "Segredos" com a tabela da §4.3; `## contas.json` → `## O arquivo contas.json` (regra 8 do formato); menção ao `contas_exemplo.json`.

## 4. qa_paridade (A1)
- `qa_paridade/sombra.py::pasta_paridade` (local) → `hpbase.pasta_paridade`; `qa_paridade/limites.py::arquivo_local` → `pasta_paridade()/"limites.json"`. Testes `test_cli.py`, `test_limites.py`, `test_sombra.py` trocam `pasta_app()/"paridade"` por `pasta_paridade()`. Por quê: §3.2 (`H:\HypadoLocal\app\paridade_nuvem`).

## 5. whatsapp_local (A3, sessão)

### `whatsapp_local/config.py`
- Constantes novas `GRUPOS_CANAIS` (canal → nome EXATO do grupo com emoji), `GRUPOS_REAIS`, `PASTAS_CANAIS_DRIVE`; funções `arquivo_fila_pc()` (= `H:\HypadoLocal\temp\whatsapp_fila.json`) e `arquivos_agendados_pc()` (os 6 `agendados.json`); `candidatos_agendados()` devolve os 6 reais primeiro (A3; §4.5/§4.8).
- `TIPOS_PERMITIDOS = ("resumo_dia", "no_ar", "resumo_sabado")` → `+ "aviso"` (sessão): as 2 mensagens reais da fila do PC (fixture) são avisos ao Antônio ("Pinterest pronto", "conteúdo de amanhã"); §4.8 diz "mais: responder o Antônio e avisar quando algo precisa dele". Sem isso o enviador rejeitaria a fila real inteira.
### `whatsapp_local/montagem.py::normalizar_post, carregar_agendados` — aceita `{"itens": [...]}` e o item real (`data_post`, `grupo_whatsapp`, canal pelo prefixo do id), marca `formato: "pc"`.
### `whatsapp_local/tarefas.py::enfileirar_no_ar, resolver_agendados_todos (nova), tarefas_automaticas` — post `formato == "pc"` usa `fila_pc.montar_aviso_no_ar` (texto literal de §4.8) e ganha `enviar_apos` 07:30 de madrugada; o vigia lê TODOS os `agendados.json` que existem.
### `whatsapp_local/enviador.py::_validar_fila` — `validar_enviar_apos` nos motivos; `pronta_para_enviar` ADIA (não rejeita) o que ainda não chegou na hora e segura tudo de madrugada.
### `whatsapp_local/LEIA.md` — seção nova no fim apontando para `LEIA_fila_pc.md`.
- **Teste:** `whatsapp_local/testes/test_fila_pc.py` (22) + os 90 antigos sem mudar.

## 6. scripts (A1, A2b, A3, sessão; E2 abaixo)

### `scripts/reenvio_seguro.py` — A1
- Constantes `IG_VER` (`HP_IG_VER`, `v21.0`), `TH_VER`, `IG_BASE = https://graph.instagram.com`, `TH_BASE`; `ClienteGraph` nasce com `host=IG_BASE` (antes `graph.facebook.com`).
- `CAMPOS_INICIO` ganha `"quando"`; `inicio_do_item` usa `fila_api_pc.inicio(item)`.
- `cliente_e_id(item, arquivo_segredo, meta=None, pasta=None)`: `IG_<CONTA>_TOKEN/ID` → `fila_api_pc.chave_token` (`IG_<handle>`/`TH_<handle>`) + `token_do_item` + `id_da_conta(chave, ler_meta())`.
- `achar_publicador(simular=False)`: devolvia `publicar_item` cru (assinatura `(item, toks, meta, simular)`) → `fila_api_pc.publicador_adaptado(publicar_item, ler_tokens=publicador_meta.ler_tokens, meta=fila_api_pc.ler_meta, simular=simular)`.
- **Teste:** `scripts/testes/test_reenvio_seguro.py` (25; 4 novos). `LEIA_reenvio_seguro.md`: passo "Integração" atualizado.

### `scripts/story_post.py` — A2b (E2 acrescenta abaixo)
- Import novo `import story_post_lote as LOTE` (logo depois de `story_post_seletores`).
- `carregar_enquete` (≈ linha 1979 aqui; no PC ≈ 1989): `_item_do_lote(cfg, dia, "story_enquete")` + `validar_texto_curto` → `LOTE.ler_interativo(p)` (chave `interativo` real OU item `story_enquete` antigo) + `LOTE.decidir_pergunta(it, limite)` (pergunta_curta → encurtar sem cortar palavra → `PerguntaImpossivel`, que vira `PerguntaLonga` com a dica `--cortar`; com `--cortar` vale o plano B antigo) + `LOTE.opcoes_da_figurinha`; arte por `LOTE.traduzir_caminho_pc`; devolve também `origem_pergunta` e `horario`; `destaque` com `or`.
- **Teste:** `scripts/testes/test_story_post.py` (45: `lote_enquete` grava o formato real; +2 testes) e `test_story_post_lote.py` (26). `LEIA_story_post.md`: linha do `enquete` e passo 1 da instalação (copiar `story_post_lote.py`).

### `scripts/story_post_seletores.py` — E2
- Constante nova ao lado de `TIMESTAMP_AGORA`: `TIMESTAMP_RECENTE_MAX_MIN = 5` (o carimbo REAL do story recém-publicado é `3m`; "de agora" = até 5 min, num lugar só; `story_fluxos.eh_timestamp_de_agora` lê daqui). `TIMESTAMP_AGORA` já tinha `agora`, `agora mesmo`, `now`, `just now`. Teste: `test_story_fluxos.py::test_fixture_real_3m_vira_3_minutos_no_story_post_e_no_story_fluxos`.

### `scripts/story_post.py` — E2 (3 trechos, +14/−3 linhas)
- `CONFIG_PADRAO["recente_max_min"]`: `2` → `5`. Por quê: `minutos_do_timestamp("3m")` já devolvia 3.0, mas `avancar_ate_story_de_agora` só aceitava ≤ 2 min: com o carimbo real `3m` passaria o próprio story e tentaria o seguinte.
- Função nova `_de_agora(texto, desc, limite_min)` (logo após `minutos_do_timestamp`): usa `story_fluxos.eh_timestamp_de_agora` (texto `^\d+m$` ≤ 5, Now/Just now/agora, e o content-desc `"<conta>'s story, N minutes ago"`); sem o módulo (PC só com a rodada 1) cai no `minutos_do_timestamp` de sempre.
- `avancar_ate_story_de_agora`: `m = minutos_do_timestamp(ts.texto); if m is not None and m <= lim: return ts` → `cab = ctx.tela.achar(nos=nos, id=["reel_viewer_text_container"]); if _de_agora(ts.texto, cab.desc if cab else "", lim): return ts`.
- Teste: `test_story_post.py` (45, inalterados e verdes) + o teste acima. O resto da migração do `story_post.py` para o aparelho real (`Dispositivo`/`story_fluxos`) está **descrito linha a linha, não aplicado**, em `docs/rodada2/E2.md` seção 3 "Patch (b)" (tabela "Onde → Hoje → Passa a ser", com os números de linha da versão atual).

### `scripts/reel_futebol_arte.py::ESTILO_PADRAO` — A3
- `from hpbase import marca`; `"fundo": "#06170F"` → `marca.CANAIS["futebol"]["fundo"]` (`#0A100C`); `"destaque": "#FFD23F"` → `#1ED760` (verde HP); `fundo2` = `misturar(fundo, verde_escuro #12A850, 0.25)` = `#0C361D`; chave nova `verde_escuro`; `escuro`/`caixa`/`arroba` da marca. Por quê: §4.6 conflito 3 (vale o verde do `posts_futebol.py`). **Teste:** `test_reel_futebol.py::test_paleta_do_reel_vem_da_marca_unica` (+29 antigos). `LEIA_reel_futebol.md`: parágrafo "Padrão embutido" e o `estilo_reel.json` de exemplo.

### Arquivos de lookup do pacote — sessão (seção 0).

## 7. publicar_extra (sessão, depois de B e C)
- `publicar_extra/testes/conftest.py` (novo; igual ao do `metricas`) e `publicar_extra/LEIA.md` (índice do pacote): B e C rodaram em paralelo e não podiam criar os dois. Não é patch de rodada 1.

## 8. docs (sessão)
- `docs/CONVENCOES.md`: seção "Rodada 2". `docs/compilar_entrega.py` (o da rodada 1): globs `app/hp_studio/` → `app/hp_studio_nuvem/` (ainda compila a rodada 1 inteira, se alguém precisar). `docs/compilar_entrega_2.py` e `docs/desempacotar_check.py` são novos.
