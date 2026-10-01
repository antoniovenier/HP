# A2b — Pedido real do PC (`esteira/pedido_pc`) e lote real de estáticos (`scripts/story_post_lote`) — tarefa A4

Agente A2b, rodada 2, 01/10/2026. Trabalho em `/home/user/HP` (branch `claude/relaxed-cray-0fkcdu`), sem commit.
Cobre a tarefa **A4** do `docs/PROMPT_NUVEM_2.md` (§4.5 pedido real, lote de estáticos e post.json; §4.9 esteira).

## 1. Feito / pela metade / não deu

| Critério de pronto | Situação |
|---|---|
| `esteira/pedido_pc.py` aceita o pedido REAL do `hp_studio\esteira\pedido.py` (tipo corte/carrossel/story/texto, prioridade 0/1/2, data `AAAA-MM-DDTHH:MM`, video/link/arquivo, streamer, inicio, fim, gancho, titulo, legenda, redes; opcionais corte, trechos, zoom, cobrir, bipes, tarjas, fade_saida, dublar, idioma, hashtags, textos, correcoes, apelido; estáticos spec/tiktok, arte/opcoes, texto) com as constantes reais `TIPOS`, `REDES`, `REDES_PADRAO`, `ARTES_STORY`, `CAMPOS_DO_PLANO` | **Feito** |
| (a) `para_esteira` → modelo interno (reel/carrossel/story/threads_texto, P0/P1/P2, `horario_alvo` ISO com fuso de Brasília, `fonte_url`, `credito` do config.json, `dublar` pela regra do lote (idioma `en`), `corte {inicio, fim}`, `slug`, campos do PC preservados para o `comandos_pc`) | **Feito** |
| (b) `para_post_json` → post.json de §4.5 (canal, tipo, quando `AAAA-MM-DD HH:MM`, titulo, legenda, arquivos, capa, tags, dublado, redes; apelidos ig/fb/th/yt/shorts/tt/pin, short→reel, foto→feed, longo→video; `textos` → `redes` objeto); aceita também o pedido interno já convertido | **Feito** |
| Recusa com `ErroParametro` em português: Flow Games nos 5 campos (`streamer, credito, link, gancho, titulo`), criador sem `autorizado: true` (config injetado ou `06 Projeto\config.json`; fixture `config_trecho.json`), vazamento de GTA, data inválida (+ tipo/rede/prioridade/canal desconhecidos, corte sem vídeo, story sem arte, texto sem texto, carrossel sem spec) | **Feito** (`ErroParametro` é um `PedidoInvalido`: o item vai para `99_erros`) |
| `nome_da_pasta(pedido)` = `P<n>_AAAA-MM-DD_HHMM_<canal(até 20)>_<apelido(até 40)>` ASCII sem espaço, apelido = slug do apelido/gancho/título; igual ao nome que `criar_pedido` dá | **Feito** |
| `ler_pedido_pc(caminho, agora)` só lê pedido solto parado há ≥ 2 s (`mtime` injetável: valor ou função) | **Feito** (não liguei ao `motor.importar_pedidos_soltos` — ver seção 8) |
| Integração: `esteira/pedido.normalizar_pedido` reconhece o formato real (`"tipo": "corte"/"texto"`, `"data"` ou prioridade inteira sem `horario_alvo`) chamando `pedido_pc` — patch pequeno | **Feito** (seção 3) |
| `esteira/testes/test_pedido_pc.py` ≥ 20: corte gringo, corte com arquivo, com link, carrossel, story interativo, texto, Flow Games (25 combinações), não autorizado, redes padrão por tipo, apelidos, nome ASCII, 2 s parado, post.json, criação de pasta e importação pelo motor | **Feito** — 29 funções de teste / 60 casos do pytest (Flow Games 5 textos × 5 campos, 8 datas inválidas) |
| `scripts/story_post_lote.py` (módulo + CLI `python story_post_lote.py <lote.json> [--limite 25]`): `ler_interativo` (chave `interativo` real E formato antigo `story_enquete`), `pergunta_da_figurinha` (1 `pergunta_curta` se couber; 2 `encurtar_pergunta` determinístico: nunca no meio de palavra, tira vocativo/introdução, prefere a ÚLTIMA oração com "?"; 3 `PerguntaImpossivel` em português), `opcoes_da_figurinha` (2–4, cada ≤ 25, senão recusa com motivo), `decidir` (+ arte, horário, destaque, conta/canal), `itens_do_lote` (stories hora/arquivo/tema, carrossel com campos reais, instagram/facebook como texto livre) | **Feito** — lote real → `"O que você faz?"` (15) |
| PATCH `scripts/story_post.py::carregar_enquete` usa `story_post_lote`; comportamento antigo como plano B; antes/depois descrito | **Feito** (seção 3) |
| `scripts/testes/test_story_post.py` atualizado onde o formato antigo era suposto, verde | **Feito** (45 testes; `lote_enquete` grava o formato real por padrão, o antigo por `formato="antigo"`) |
| `scripts/testes/test_story_post_lote.py` ≥ 20: acentos, emoji, pontuação, opções longas, 1 e 5 opções, pergunta_curta vence, lote real → "O que você faz?", impossível → recusa, formato antigo, itens do lote, CLI | **Feito** — 26 testes |
| Pendência para o Diretor: texto pronto do SKILL `hypado-estaticos` gravando `interativo.pergunta_curta` | **Feito** (seção 7) |
| Rodar `esteira` e os dois arquivos de teste dos scripts e relatar números | **Feito** (seção 4) |

**Pela metade / não deu:** nada. O que é suposição está na seção 5; o que é decisão de produto, na 8.

## 2. Arquivos

**Novos**
- `app/hp_studio_nuvem/esteira/pedido_pc.py`
- `app/hp_studio_nuvem/esteira/LEIA_pedido_pc.md`
- `app/hp_studio_nuvem/esteira/testes/test_pedido_pc.py` (60 testes)
- `scripts/story_post_lote.py`
- `scripts/LEIA_story_post_lote.md`
- `scripts/testes/test_story_post_lote.py` (26 testes)
- `docs/rodada2/A2b.md` (este)

**Da rodada 1, alterados**
- `app/hp_studio_nuvem/esteira/pedido.py` (1 import + cabeçalho de `normalizar_pedido`)
- `scripts/story_post.py` (1 import + `carregar_enquete` reescrita)
- `scripts/testes/test_story_post.py` (`lote_enquete`, `test_pergunta_da_enquete_maior_que_25_aborta`, +2 testes)
- `scripts/LEIA_story_post.md` (linha do comando `enquete` e passo 1 da instalação)

Não toquei em `hpbase`, `metricas`, `qa_paridade`, `whatsapp_local`, `esteira/motor.py`, `esteira/constantes.py`, `tests/conftest.py`, `.claude`.

## 3. Patches (arquivo da rodada 1 → função → o que muda → por quê → teste → antes/depois)

### Patch 1 — esteira, arquivo pedido.py → `normalizar_pedido` (+ import)

- **O que muda:** ganha o parâmetro opcional `config_json=None` e, antes de qualquer coisa, se `pedido_pc.eh_pedido_pc(dados)` (tipo `corte`/`texto`, ou `data`/prioridade inteira sem `horario_alvo`) converte com `pedido_pc.para_esteira(dados, config=config_json)`. O resto da função (padrões, id, horário) continua igual e roda sobre o pedido convertido. Import novo: `from . import pedido_pc` (o `pedido_pc` não importa o `pedido`: sem ciclo).
- **Por quê:** §4.5 — "a sua esteira tem que aceitar este formato"; assim `criar_pedido`, `ler_pedido`, o `.json` solto do motor e a CLI aceitam o pedido real sem flag. `ErroParametro` herda de `PedidoInvalido`: pedido ruim vai para `99_erros` com a mensagem em português.
- **Teste:** `test_pedido_pc.py::test_normalizar_pedido_reconhece_o_formato_real` (inclui o formato interno com prioridade inteira + `horario_alvo` intacto), `::test_criar_pedido_real_cria_a_pasta_com_o_nome_do_pc`, `::test_pedido_solto_real_importado_pelo_motor_e_recusado_quando_ruim`; os 22 antigos de `test_pedido.py` passam sem mudar.
- Antes:
  ```python
  def normalizar_pedido(dados: dict) -> dict:
      """Preenche padrões e arruma formatos, sem inventar conteúdo."""
      p = dict(dados)
  ```
- Depois:
  ```python
  def normalizar_pedido(dados: dict, config_json: dict | None = None) -> dict:
      """... (docstring explica o formato real) ..."""
      if pedido_pc.eh_pedido_pc(dados):
          dados = pedido_pc.para_esteira(dados, config=config_json)
      p = dict(dados)
  ```

### Patch 2 — scripts, arquivo story_post.py → `carregar_enquete` (linha ~1979 aqui; no PC a mesma função fica perto da ~1989) + import

- **O que muda:** em vez de `_item_do_lote(cfg, dia, "story_enquete")` + `validar_texto_curto` (que cortava a pergunta às cegas com `--cortar` ou abortava), a função acha o arquivo com `_achar_estaticos` e usa o `story_post_lote`: `LOTE.ler_interativo(p)` (chave `interativo` do lote real OU item `story_enquete` antigo), `LOTE.decidir_pergunta(it, limite)` (pergunta_curta → encurtar sem cortar palavra → `PerguntaImpossivel`), `LOTE.opcoes_da_figurinha(it, limite_opcao)`. `PerguntaImpossivel` vira `PerguntaLonga` (com a explicação e a dica `--cortar`); **com `--cortar`/`cortar_pergunta` vale o plano B antigo** (`validar_texto_curto(..., True, ...)`, corte por palavra). `OpcoesInvalidas`/`LoteInvalido` viram `DadosInvalidos`. A arte passa por `LOTE.traduzir_caminho_pc` (`H:\HypadoLocal\...` → raiz da máquina; no PC fica igual). Figurinha que não é enquete é recusada. O dicionário devolvido ganha `origem_pergunta` e `horario`; `destaque` usa `or` (lote sem destaque → `destaque_enquetes` do config). `_item_do_lote` continua existindo (a contagem usa).
  Import novo logo depois de `story_post_seletores`: `import story_post_lote as LOTE`.
- **Por quê:** §4.5 — o story da enquete NÃO é um item `story_enquete`: é a chave `interativo`, e a pergunta real tem ~46 caracteres (a figurinha aceita ~25). "Não corta no escuro".
- **Teste:** `test_story_post.py::test_enquete_lote_real_encurta_sem_cortar_e_le_pergunta_curta` (fixture real `lote_estaticos_2026-10-01.json` → `"O que você faz?"`, arte traduzida, fluxo completo no InstagramFalso, `pergunta_curta` vence), `::test_enquete_formato_antigo_continua_valendo`, `::test_pergunta_da_enquete_maior_que_25_aborta` (recusa explica `pergunta_curta`; `--cortar` ainda dá `"Qual vai ser o preço do"`), `::test_enquete_fluxo_completo` e `::test_simular_enquete_mostra_digitacao_e_arrasto` (agora sobre o formato real) passam.
- Antes (trecho central):
  ```python
  it, p = _item_do_lote(cfg, dia, "story_enquete")
  ...
  if not it:
      raise DadosInvalidos(f"{p.name} não tem item com tipo 'story_enquete'")
  pergunta = validar_texto_curto(it.get("pergunta"), int(cfg["limite_pergunta"]),
                                 bool(cortar), "pergunta")
  opcoes = [validar_texto_curto(o, int(cfg["limite_opcao"]), False, "opção")
            for o in (it.get("opcoes") or [])]
  if not 2 <= len(opcoes) <= 4:
      raise DadosInvalidos("a enquete precisa de 2 a 4 opções")
  ...
  return {"arte": _resolver_arte(it.get("arquivo"), p), "pergunta": pergunta, "opcoes": opcoes,
          "handle": handle, "caixa": ..., "destaque": it.get("destaque", cfg["destaque_enquetes"])}
  ```
- Depois (trecho central):
  ```python
  p = _achar_estaticos(cfg, dia)
  ...
  it = LOTE.ler_interativo(p)          # LoteInvalido -> DadosInvalidos
  if not it:
      raise DadosInvalidos(f"{p.name} não tem a chave 'interativo' nem item com tipo 'story_enquete'")
  try:
      pergunta, origem = LOTE.decidir_pergunta(it, limite)
  except LOTE.PerguntaImpossivel as e:
      if not cortar:
          raise PerguntaLonga(f"{e} (ou rode com --cortar)") from e
      pergunta = validar_texto_curto(it.get("pergunta") or it.get("pergunta_curta"), limite, True, "pergunta")
      origem = "cortada"                 # plano B antigo
  opcoes = LOTE.opcoes_da_figurinha(it, int(cfg["limite_opcao"]))   # OpcoesInvalidas -> DadosInvalidos
  ...
  return {"arte": _resolver_arte(LOTE.traduzir_caminho_pc(it.get("arquivo")), p), "pergunta": pergunta,
          "origem_pergunta": origem, "opcoes": opcoes, "handle": handle, "caixa": ...,
          "destaque": it.get("destaque") or cfg["destaque_enquetes"], "horario": it.get("horario")}
  ```

### Patch 3 — scripts, arquivo testes/test_story_post.py

- `lote_enquete(drive, pergunta, opcoes, formato="real", **kw)`: grava o lote no formato REAL (`data`, `carrossel`, `stories`, `interativo` com `rede: "Instagram @hpgta6 (compartilhar no Facebook)"`, `horario`, `figurinha`, `destaque: "Enquetes"`, mais `caixa_enquete` como chave extra para o teste do arrasto); `formato="antigo"` grava o item `story_enquete` de antes. Antes: só o formato antigo.
- `test_pergunta_da_enquete_maior_que_25_aborta`: a recusa agora tem que citar `pergunta_curta` e `--cortar`; o plano B com `cortar=True` continua `"Qual vai ser o preço do"` e marca `origem_pergunta == "cortada"`.
- Novos: `test_enquete_lote_real_encurta_sem_cortar_e_le_pergunta_curta`, `test_enquete_formato_antigo_continua_valendo`.

### Patch 4 — scripts, arquivo LEIA_story_post.md

- Linha do comando `enquete` explica que lê a chave `interativo` pelo `story_post_lote.py`; passo 1 da instalação inclui copiar `story_post_lote.py`.

## 4. Testes (números reais, saída do pytest)

| Comando | passed | failed | skipped | tempo |
|---|---|---|---|---|
| `cd app/hp_studio_nuvem && python3 -m pytest -q -p no:cacheprovider esteira` (**pedido da tarefa**) | **239** | 0 | 0 | **15,50 s** |
| `cd scripts && python3 -m pytest -q -p no:cacheprovider testes/test_story_post.py testes/test_story_post_lote.py` (**pedido da tarefa**) | **71** | 0 | 0 | **1,04 s** |
| `cd app/hp_studio_nuvem && python3 -m pytest -q -p no:cacheprovider esteira/testes/test_pedido_pc.py` (só os novos) | 60 | 0 | 0 | 0,17 s |
| `cd scripts && python3 -m pytest -q -p no:cacheprovider testes/test_story_post_lote.py` (só os novos) | 26 | 0 | 0 | 0,37 s |
| `cd scripts && python3 -m pytest -q -p no:cacheprovider testes` (suíte inteira dos scripts, inclui os de outros agentes já presentes) | 348 | 0 | 0 | 40,69 s |

Antes dos meus arquivos: `esteira` 179 passed (13,99 s) e `test_story_post.py` 43 passed (0,93 s). Depois: esteira +60 (nenhum antigo mudou), `test_story_post.py` 45 (43 antigos verdes, 1 ajustado, 2 novos) + 26 do `test_story_post_lote.py` = 71. Módulos da rodada 1 que toquei: `esteira` (239) e `scripts/story_post` (45) — verdes. Nenhum teste usa rede, adb, relógio real (`agora`/`mtime` injetados), Windows, ffmpeg nem segredo.

## 5. Suposições que sobraram

| Suposição | Arquivo | Onde trocar |
|---|---|---|
| Pedido sem `canal` é do GTA (`"gta"`), porque o `config.json` e o `estaticos.py` do PC são do GTA | `esteira/pedido_pc.py` | `CANAL_PADRAO`, `validar_pc` |
| Corte exige `streamer` (id do criador); estático só confere criador se trouxer `streamer` | `esteira/pedido_pc.py` | `validar_pc`, `criador_autorizado` |
| **Sem `config.json`** (ou `HP_CONFIG_PC` apontando para nada) nenhum criador é autorizado → corte recusado com a mensagem dizendo o caminho procurado (regra 6: "só criador com autorizado: true") | `esteira/pedido_pc.py` | `criador_autorizado` |
| Corte com `video`/`link` exige `inicio` e `fim` (o `ytdlp.py` baixa só o trecho); com `arquivo` (trecho pronto) são opcionais | `esteira/pedido_pc.py` | `validar_pc` |
| `story` exige `arte` ∈ `ARTES_STORY`; `carrossel` exige `spec` (caminho ou dict); `texto` exige `texto` | `esteira/pedido_pc.py` | `validar_pc` |
| Apelidos `ig/fb/th/yt/shorts/tt/pin` valem também no pedido (não só no post.json); `pinterest` é recusado no pedido do PC (não está em `REDES`); `redes` pode vir como texto "instagram, tiktok" | `esteira/pedido_pc.py` | `redes_do_pedido` |
| `prioridade` aceita `"1"` e `"P1"` além do inteiro; `data` aceita espaço no lugar do `T` e segundos | `esteira/pedido_pc.py` | `prioridade_pc`, `ler_data` (`_RX_DATA`) |
| Vazamento: `vazad|vazament|leak` em gancho/titulo/legenda/texto/link/obs, só no canal gta (mesma regra do `validar_pedido` da rodada 1) | `esteira/pedido_pc.py` | `conferir_vazamento`, `PALAVRAS_VAZAMENTO` |
| `toque_hp` (dict) no pedido do PC vira `narrar_toque_hp` + `roteiro_narracao`, como o `pedido_de_plano` do A2a | `esteira/pedido_pc.py` | `para_esteira` |
| `titulo` interno = titulo → gancho → `opcoes.titulo` (story) → 1ª linha da legenda/texto → `spec.titulo/tema` → `"<tipo> <data>"`; apelido = `apelido` → gancho → esse título | `esteira/pedido_pc.py` | `titulo_do_pedido`, `apelido_do_pedido` |
| post.json do corte: `arquivos = ["final.mp4"]` e `capa = "capa.jpg"` (docstring do `post.py`; o PC também gera `upload.mp4` ≤ 10 MB — não sei qual o `publicar` prefere); estáticos sem `arquivo` ficam com lista vazia (a etapa 06 completa com a arte); `tags` = `hashtags` do pedido, senão as `#` da legenda; `titulo` não é cortado em 100 (quem corta é o `publicar`) | `esteira/pedido_pc.py` | `ARQUIVOS_POST_PADRAO`, `CAPA_POST_PADRAO`, `para_post_json` |
| `textos {rede: texto}` para rede que não está em `redes` é descartado em silêncio | `esteira/pedido_pc.py` | `para_post_json` (laço `por_rede`) |
| A figurinha recebe texto puro: **emoji sai** da pergunta e das opções (o adb não digita emoji); o vocativo/introdução sai **mesmo quando a pergunta cabe** ("Galera, o que você faz?" → "O que você faz?") | `scripts/story_post_lote.py` | `limpar`/`sem_emoji`, `candidatos` (ordem `sem_vocativo` antes de `texto`) |
| Lista de vocativos/introduções (galera, gente, pessoal, me conta, e aí, pergunta do dia, hein…) — só segmentos feitos SÓ dessas palavras antes de `,`/`:` e o que sobra tem que terminar em `?` | `scripts/story_post_lote.py` | `PALAVRAS_DE_ABERTURA`, `VOCATIVOS_DE_FECHO`, `sem_vocativo` |
| Se a ÚLTIMA oração com "?" não cabe, tenta as anteriores com "?" (da última para a primeira) antes de recusar | `scripts/story_post_lote.py` | `candidatos` |
| Opção repetida (ignorando acento/maiúscula) é recusada | `scripts/story_post_lote.py` | `opcoes_da_figurinha` |
| No lote real a conta é o `@` dentro do texto `rede` (`"Instagram @hpgta6 (compartilhar no Facebook)"` → `hpgta6`), `compartilhar_facebook` = "facebook" nesse texto, canal = `gta` | `scripts/story_post_lote.py` | `ler_interativo`, `conta_do_texto`, `CANAL_PADRAO` |
| `figurinha` diferente de `enquete` é recusada (o story_post só sabe enquete) | `scripts/story_post_lote.py`, `scripts/story_post.py` | `decidir`, `carregar_enquete` |
| O lote real não tem `caixa_enquete`: vale `caixa_enquete` do `story_post_config.json` (ou a chave extra dentro de `interativo`, se alguém gravar) | `scripts/story_post.py` | `carregar_enquete` |
| `len()` da pergunta da fixture dá **44** (o enunciado diz 46 — provavelmente o texto real era um pouco maior); a decisão é a mesma | `tests/fixtures/pc_real/lote_estaticos_2026-10-01.json` | — |

## 6. Depende do Antônio

Nenhum token, permissão ou clique. Na próxima cópia para o PC (leigo):

1. Copiar `scripts\story_post_lote.py` para `G:\Meu Drive\Hypado\scripts\` (ao lado do `story_post.py`) — sem ele o `story_post.py` novo não abre (`import story_post_lote`).
2. Copiar `app\hp_studio_nuvem\esteira\pedido_pc.py` junto com o `esteira\pedido.py` novo para `06 Projeto\app\hp_studio_nuvem\esteira\`.
3. Conferir que `G:\Meu Drive\Hypado\06 Projeto\config.json` existe (é o de sempre); em outra máquina, `set HP_CONFIG_PC=<caminho do config.json>`.
4. Conferir a enquete do dia antes das 16h: `python scripts\story_post_lote.py lotes\2026-10-01_estaticos.json` — tem que terminar sem "NÃO DÁ".

## 7. Pendências para o Diretor

Texto pronto para o SKILL `hypado-estaticos` (colar em `.claude\skills\hypado-estaticos\SKILL.md`, na parte que escreve o story interativo do lote `lotes\AAAA-MM-DD_estaticos.json`):

```
### Story interativo (chave "interativo" do lote): grave DUAS perguntas

Além de "pergunta" (a pergunta completa, com contexto, como hoje), grave SEMPRE
"pergunta_curta": a pergunta que vai na figurinha de enquete do Instagram.

Regras da "pergunta_curta":
- Até 25 caracteres, contando espaço, acento e pontuação (conte antes de gravar).
- Uma frase só, terminada em "?", que fecha sozinha: dá para entender sem ler a arte nem a
  pergunta completa. Ex.: "O que você faz?" (15), "Vai jogar no dia 1?" (19), "Vice City ou Leonida?" (21).
- Sem emoji, sem "#", sem vocativo ("galera,", "gente,") nem introdução ("me conta:", "e aí,").
- Não terminar em vírgula, dois-pontos ou reticências; nunca cortar palavra no meio.
- "opcoes": 2 a 4, cada uma com até 25 caracteres, sem emoji e sem repetir.

Exemplo:
  "interativo": {
    "pergunta": "Furacão chegando em Leonida. O que você faz?",
    "pergunta_curta": "O que você faz?",
    "opcoes": ["Vou ver de perto", "Fujo pro outro lado"],
    ...
  }

Antes de fechar o lote, rode: python scripts\story_post_lote.py lotes\AAAA-MM-DD_estaticos.json
Tem que terminar com código 0 e mostrar a pergunta escolhida. Se aparecer "NÃO DÁ", arrume
"pergunta_curta"/"opcoes" e rode de novo. Sem "pergunta_curta" o story_post tenta encurtar a
pergunta completa pela última oração com "?"; se nada couber em 25, o story NÃO sai.
```

## 8. Decisões em aberto / conflitos

1. **Gringo no GTA × `CANAIS_COM_VOZ`** (mesmo conflito da decisão 1 do A2a): o pedido real de criador `en` (ex.: `tmartn2`) sai `dublar: true` pelo `pedido_pc`, mas `esteira/pedido.validar_pedido` recusa ("dublagem/voz sintética só em destinos, receitas, carros e filmes") porque `CANAIS_COM_VOZ` (rodada 1) não tem `gta`. O teste `test_gringo_no_gta_esbarra_na_regra_de_voz_da_rodada_1` registra isso. Resolver = incluir `"gta"` em `esteira/constantes.py::CANAIS_COM_VOZ` (1 linha; não fiz por ser regra de conteúdo — o CLAUDE.md só proíbe voz sintética no futebol, e o `config.json` do GTA tem `dublagem` com `"credito": "dublado por HP"`).
2. **`ler_pedido_pc` não está ligado ao motor.** `motor.importar_pedidos_soltos` lê o `.json` solto na hora (pode pegar arquivo meio gravado). Ligar são ~3 linhas em `_importar_json` (`if pedido_pc.ler_pedido_pc(arq, agora=time.time()) is None: return []`), usando `time.time()` como a limpeza de `.criando_` já faz (o `agora` injetado dos testes está no passado em relação ao mtime real). Não mexi em `motor.py` (arquivo da rodada 1 fora do patch pedido).
3. **Sem `config.json` o corte é recusado.** Alternativa mais leniente: pular a checagem do criador quando o config não existe. Mantive o recusar (regra 6) — se o Diretor preferir, é `conferir_criador=False` em `validar_pc` quando `config is None`.
4. **Emoji e vocativo saem sempre** da pergunta da figurinha (mesmo quando cabe). Se o Antônio quiser a pergunta exatamente como foi escrita quando couber, inverter a ordem em `story_post_lote.candidatos` (texto antes de `sem_vocativo`) e tirar o `sem_emoji` de `limpar`.
5. **post.json do corte publica `final.mp4`** (docstring do `post.py`). Se o `publicar` do PC preferir o `upload.mp4` (≤ 10 MB), trocar `ARQUIVOS_POST_PADRAO["corte"]`.
6. **`tags` do post.json** saem das `#` da legenda quando o pedido não traz `hashtags` — pode duplicar o que o `publicar` já faz; é só trocar `hashtags_do_pedido(v) or _RX_HASHTAG.findall(legenda)` por `hashtags_do_pedido(v)`.
