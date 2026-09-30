# Manual 09 — Revisor de qualidade (HP Studio)

> **Versão:** 1.0 — 30/09/2026 · **Cargo nº 09 da esteira** · vale para os 6 canais da Hypado (HP)
> **Onde este arquivo mora no PC:** `G:\Meu Drive\Hypado\06 Projeto\app\manuais\09_revisor_qualidade.md`
> **Status:** manual novo, ainda não revisado pelo Antônio. Tudo o que está marcado **(a criar)** ainda **não existe** no PC. O resto já existe e funciona hoje.
> **Quem usa:** o Claude (hoje, com o app fazendo as medições quando a etapa 3 estiver pronta), o app HP Studio (pré-revisão automática) e qualquer pessoa leiga que precise revisar à mão.

---

## Sumário

1. Objetivo do cargo
2. Entradas e saídas (a regra central, a lista completa de critérios, a tabela critério → etapa, o esquema JSON completo, 7 exemplos completos)
3. Passo a passo numerado para leigo (62 passos)
4. Regras que nunca se quebram
5. Critérios de qualidade com nota
6. Erros comuns e o que fazer
7. O que o app faz sozinho x o que o Claude decide
8. Ferramentas existentes que já fazem cada passo
9. Testes de aceitação
10. Glossário

---

## Como ler este manual (se você nunca fez isso)

- Cada passo da seção 3 tem 4 partes: **Abra**, **Rode** (comando do PowerShell), **Confira**, **Deve aparecer**. Deu diferente? Seção 6.
- **PowerShell**: `Windows + X` → **Terminal**. Colar = botão direito ou `Ctrl + V`, depois `Enter`.
- O Revisor **não conserta nada**. Ele mede, dá nota, decide e **manda de volta para quem sabe consertar**. Se você se pegar editando legenda, capa ou texto, pare: não é o seu papel.
- Nota vai de **0 a 10**, de meio em meio ponto (7, 7,5, 8…). Nos arquivos JSON o decimal é com **ponto** (`7.5`); no texto do manual, com vírgula (7,5).
- **Quadro** é uma foto tirada de dentro do vídeo num instante. O Revisor olha **3 quadros** (início, meio e fim) — não precisa assistir o vídeo inteiro, a não ser que um quadro levante dúvida.

---

## 1. Objetivo do cargo

### 1.1 Em uma frase

O Revisor é **o último portão antes do ar**: olha 3 quadros do vídeo (início, meio e fim), a capa e todos os textos do item, confere as medidas automáticas (duração, som, tamanho, limites), dá **nota de 0 a 10 em cada critério**, calcula a **média** e grava na pasta do item **`aprovado.json`** (vai para agendar) ou **`refazer.json`** (volta para a etapa certa, com o motivo e o que refazer) — no máximo **2 voltas**; na 3ª reprovação o item é **descartado e registrado**.

### 1.2 A regra central (decore)

| Média das notas | Classe | O que acontece |
|---|---|---|
| **≥ 9,00** | **Excelente** | **aprovado** → `06_agendados` |
| **7,00 a 8,99** | **Bom** | **aprovado** → `06_agendados` |
| **5,00 a 6,99** | **Médio** | **refazer** → volta para a **etapa do critério de menor nota** |
| **< 5,00** | **Razoável** | **refazer** → volta ao **Curador** (`01_pedidos`) |
| — | — | **Máximo 2 voltas.** Na **3ª** reprovação: **descarta** (`99_erros`) **e registra** |

Mais duas **travas** que protegem a conta (seção 2.5): conteúdo proibido que não tem conserto (vazamento de GTA 6, Flow Games, imagem de TV no Futebol) é descartado na hora; e item com média boa **não** passa se tiver crédito faltando, valor sem aviso, música com direito autoral, regra de conteúdo quebrada ou qualquer nota abaixo de 5.

### 1.3 Por que isso importa para a monetização

- **Um post errado custa mais que dez posts bons rendem.** Um vídeo com vazamento, sem crédito ou com imagem de TV pode gerar denúncia, remoção e perda de alcance da conta toda — e isso atrasa a monetização por semanas.
- **Qualidade constante é o que faz o algoritmo confiar no perfil.** Áudio baixo, legenda atrasada e capa cortada derrubam retenção; retenção baixa derruba distribuição.
- **O Revisor é quem ensina a esteira.** Cada `refazer.json` diz exatamente o que corrigir e quem corrige. Os números (quais critérios mais reprovam) vão para o Analista de resultados (manual 11) e viram melhoria nos outros manuais.
- **Token é dinheiro.** O Revisor bem feito olha **uma imagem** (a folha com 3 quadros + capa) e **o texto**, em vez de assistir o vídeo inteiro. O app faz todas as medições. O Claude só julga.

### 1.4 O que o Revisor NÃO faz

- **Não conserta** nada (nem uma vírgula). Ele manda de volta com instrução clara.
- **Não escolhe tema** (Curador), **não publica** (Publicador), **não agenda** (app / Claude pelo Chrome no TikTok).
- **Não revisa o próprio trabalho**: se o mesmo Claude fez a legenda e vai revisar, a revisão segue este manual à risca, com as medições automáticas, sem "passar porque eu sei que está bom".
- **Não muda a regra central.** Nada de "aprovar com 6,8 porque é P0". P0 tem pressa, não tem desconto.

### 1.5 Metas com número

| Meta | Número |
|---|---|
| Posts no ar com violação de regra inviolável | **0** |
| Tempo de revisão (Claude) | P0 ≤ 3 min · P1/P2 ≤ 6 min por item |
| Tempo da pré-revisão automática (app) | ≤ 60 s por vídeo de até 90 s; ≤ 10 s por estático |
| Aprovados na 1ª revisão | ≥ 80% dos itens (se for menos, os outros cargos precisam de ajuste — é aviso para o Analista) |
| Itens descartados por limite de voltas | ≤ 2% dos itens do mês |
| Concordância app x Claude no modo sombra | veredito igual em ≥ 95% dos itens; média com diferença ≤ 0,5 ponto |
| `refazer.json` com instrução que o cargo consegue seguir sem perguntar | 100% |

---

## 2. Entradas e saídas

### 2.1 A esteira e onde o Revisor fica

```
H:\HypadoLocal\esteira\
├── 01_pedidos            ← Curador larga o pedido; o app baixa sozinho          ◄── volta "Razoável" e critérios do Curador
├── 02_baixados           ← bruto chegou; corte do trecho e transcrição            ◄── volta de "trecho_corte"
├── 03_legenda_dublagem   ← legenda, tradução, dublagem, narração "Toque HP"       ◄── volta de "legenda" e "traducao_dublagem"
├── 04_edicao             ← Editor (final.mp4), Designer (capa, artes), Redator (post.json)   ◄── volta dos demais critérios
├── 05_revisao            ← REVISOR: 3 quadros + texto → aprovado.json ou refazer.json
├── 06_agendados          ← aprovado: o app agenda pela API (TikTok: o Claude pelo Chrome + tiktok_ok.json)
├── 07_postados           ← no ar; daqui sai o aviso "no ar"
└── 99_erros              ← erro de máquina ou item DESCARTADO (com descartado.json)
```

- **Vídeo** (reel): chega em `05_revisao` depois de passar por 01 → 02 → 03 → 04.
- **Estático** (carrossel, arte de feed, story, story de enquete, contagem regressiva, pin, imagem do Threads, texto puro do Threads): entra em `01_pedidos` com o campo `tipo`, **pula 02 e 03** e chega em `05_revisao` depois de 04. Por isso, estático só volta para `01_pedidos` ou `04_edicao`.

### 2.2 O nome da pasta do item

`P1_2026-09-30_1830_gta_rockstar-quinta` = prioridade (`P0_` urgente/ao vivo — gol, placar, lançamento, bombástica — fura a fila de tudo; `P1_` do dia; `P2_` programado) + data de postagem + hora de postagem + canal (`gta`, `futebol`, `filmes`, `receitas`, `carros`, `destinos`) + apelido. Ordenando por nome, o mais urgente fica em cima: **sempre revise de cima para baixo**.

### 2.3 O que o Revisor lê (entradas)

| Arquivo | Quem fez | Tipo de item | O Revisor usa para… |
|---|---|---|---|
| `pedido.json` | Curador | todos | tema, canal, tipo, redes, fonte, voz, valores |
| `bruto.*` | app (download) | vídeo | só se precisar comparar com a fonte (raro) |
| `transcricao.json` | app | vídeo com fala | conferir que texto e legenda dizem o que o vídeo diz |
| `legenda.srt` / `legenda.ass` | Legendador | vídeo | texto e tempos da legenda |
| `dublagem.wav` | Tradutor/dublador ou Narrador | vídeo com voz nova | ouvir só se o quadro/tempo levantar dúvida |
| `final.mp4` | Editor | vídeo | medidas automáticas + 3 quadros |
| `capa.jpg` | Designer | vídeo | nota da capa |
| `lamina_01.jpg`… / `story.jpg` / `pin.jpg` / `threads.jpg` | Designer | estático | nota das artes |
| `design.json` | Designer | todos com arte | medidas da arte (tamanho, contraste, zona segura) sem abrir a imagem |
| `conferencia_*.jpg` | Designer | todos com arte | zona segura desenhada |
| `post.json` | Redator | todos | todos os textos por rede |
| `historico.log` | todos | todos | o que já aconteceu com o item |
| `refazer_volta1.json`, `refazer_volta2.json` | Revisor (antes) | itens que voltaram | contar as voltas e ver se o que foi pedido foi feito |

### 2.4 O que o Revisor escreve (saídas)

| Arquivo | Quando | Onde |
|---|---|---|
| `quadro_inicio.jpg`, `quadro_meio.jpg`, `quadro_fim.jpg` | todo vídeo | pasta do item |
| `folha_revisao.jpg` | todo vídeo (3 quadros + capa lado a lado — é **a** imagem que o Claude olha) | pasta do item |
| **`aprovado.json`** | média ≥ 7 e nenhuma trava | pasta do item (o app move para `06_agendados`) |
| **`refazer.json`** | Médio, Razoável ou trava, com voltas < 2 | pasta do item (o app move para a `etapa_destino`) |
| **`descartado.json`** | conteúdo irreparável, ou 3ª reprovação | pasta do item (o app move para `99_erros`) |
| 1 linha no `historico.log` | sempre | pasta do item |
| 1 linha em `descartes.csv` | só no descarte | `H:\HypadoLocal\esteira\99_erros\descartes.csv` (o app cria o arquivo se não existir) |
| log do dia | sempre (o app) | `H:\HypadoLocal\app\logs\revisor_<dia>.log` (pelo `obter_logger("revisor")` do `hpbase`) |

Os três arquivos de veredito (`aprovado.json`, `refazer.json`, `descartado.json`) usam **o mesmo esquema** (seção 2.9). Só muda o nome e o `veredito` de dentro.

### 2.5 O algoritmo do veredito (a ordem exata das decisões)

Siga **nesta ordem**. A primeira regra que se aplicar decide.

1. **Conteúdo irreparável?** O item tem vazamento de GTA 6, qualquer coisa do Flow Games, imagem de transmissão de TV no Futebol, ou material de fonte proibida sem substituto possível → **`descartar`** → `99_erros`. Não conta volta, não adianta refazer. (Critério `regras_conteudo` = 0 com a trava `conteudo_irreparavel`.)
2. **Calcule a média** das notas dos critérios que **se aplicam** (os que não se aplicam ficam `null` e **não entram** na conta). Use a média **exata** para decidir; no arquivo ela é gravada **truncada** em 2 casas (8,999 vira 8,99 — nunca 9,00).
3. **Média < 5 (Razoável)** → **`refazer`** → `01_pedidos`, cargo `curador`.
4. **Média de 5 a 6,99 (Médio)** → **`refazer`** → a etapa do **critério de menor nota**. Empate entre critérios de etapas diferentes: vence a etapa **mais cedo** da esteira (01 antes de 02 antes de 03 antes de 04), porque consertar lá em cima obriga o item a passar de novo por tudo que vem depois.
5. **Média ≥ 7, mas com trava** → **`refazer`** → a etapa do critério travado de menor nota (empate: a mais cedo). Travas:
   - **eliminatório abaixo do mínimo:** `regras_conteudo` < 10 · `credito` < 7 · `valores` < 7 · `musica_direitos` < 7;
   - **nota mínima:** qualquer critério com nota < 5.
6. **Média ≥ 7 sem trava** → **`aprovado`** → `06_agendados`, cargo `publicador`.
7. **Limite de voltas:** se os passos 3, 4 ou 5 deram `refazer` **e o item já voltou 2 vezes** (existem `refazer_volta1.json` e `refazer_volta2.json`), o veredito vira **`descartar`** → `99_erros`, com a trava `limite_voltas`, e o descarte é **registrado** (seção 2.12).

**O que entra em `o_que_refazer`:**
- **Médio ou trava:** uma ação para o critério de menor nota (obrigatória) **mais** uma ação para cada outro critério com nota < 7 cuja etapa seja **igual ou posterior** à etapa de destino (o item vai passar por lá de novo). Critérios < 7 de etapas **anteriores** ao destino vão só em `observacoes` (o item não volta lá).
- **Razoável:** **uma** ação para o Curador (refazer o pedido ou descartar). As notas de todos os critérios ficam registradas para cada cargo ver.
- **Aprovado e descartado:** lista vazia `[]`. Sugestões de melhoria para os próximos posts vão em `observacoes`.

### 2.6 Lista completa de critérios

#### 2.6.1 Vídeo (`tipo: "reel"`) — 20 critérios

| # | Código (no JSON) | Nome | O que se avalia | Quando **não** se aplica |
|---|---|---|---|---|
| 1 | `tema` | Tema e atualidade | assunto certo para o canal, quente (P0/P1 do dia), não repetido, com potencial | nunca |
| 2 | `fonte_direitos` | Fonte e direitos | origem permitida, crédito possível, qualidade de origem (≥ 1080p de preferência, nunca < 720p) | nunca |
| 3 | `regras_conteudo` | Regras de conteúdo (**eliminatório**) | vazamento GTA 6, Flow Games, TV no Futebol, trailer puro, narração sintética no Futebol, voz clonada, voz sintética fora de Destinos/Receitas/Carros/Filmes próprios, spoiler sem aviso, clickbait mentiroso, ofensa | nunca |
| 4 | `trecho_corte` | Trecho escolhido e corte | começa no ponto certo, sem enrolação, sem cortar fala no meio, duração adequada | vídeo próprio montado de fotos (sem bruto) |
| 5 | `gancho` | Gancho (0 a 2 s) | nos 2 primeiros segundos há ação/imagem forte + texto ou fala que cria curiosidade; nada de tela preta, logo parado, "oi gente" | nunca |
| 6 | `legenda` | Legenda do vídeo | texto igual à fala, ortografia, sincronia, até 2 linhas, posição dentro da zona segura, legível | vídeo sem fala e sem texto falado |
| 7 | `traducao_dublagem` | Tradução, dublagem, narração | tradução fiel, voz permitida (Piper pt-BR, só onde pode), pronúncia, "Toque HP" (pergunta nos 2 primeiros segundos, trecho narrado com voz neutra, fecho com pergunta) | `voz: "nenhuma"` e sem tradução |
| 8 | `audio_loudness` | Áudio e volume | volume integrado −14 LUFS (±1), pico real ≤ −1 dBTP, voz clara, sem estouro, sem silêncio longo | nunca (vídeo sem áudio = nota 0) |
| 9 | `musica_direitos` | Música (**eliminatório**) | só música livre de direitos, volume abaixo da voz, sem música em cima de áudio original do Futebol | sem música adicionada |
| 10 | `imagem_nitidez` | Imagem e nitidez | 1080x1920, 30 fps (23–60 aceito), nítido, sem barras pretas, sem marca d'água de outro perfil/rede | nunca |
| 11 | `enquadramento_safe` | Enquadramento e zona segura | assunto principal enquadrado no 9:16; textos queimados dentro de x 60–930, y 250–1500 | nunca |
| 12 | `texto_tela` | Texto na tela | cartões, títulos e números queimados: ortografia, tempo para ler (≥ 1,5 s por linha curta), coerência | vídeo sem texto na tela além da legenda |
| 13 | `credito` | Crédito (**eliminatório**) | "Vídeo: @criador" (ou Foto/Imagem) visível na tela **e** em todas as redes do `post.json` | material 100% próprio da HP |
| 14 | `valores` | Valores aproximados (**eliminatório**) | todo valor em dinheiro (tela, capa, texto) acompanhado de "Valores aproximados…" | nenhum valor citado |
| 15 | `capa` | Capa | 1080x1920, título legível na grade 3:4, zona segura, contraste ≥ 4,5, herói forte (manual 07) | nunca |
| 16 | `titulo_capa` | Título da capa | verdadeiro, ≤ 36 caracteres e ≤ 6 palavras, gancho claro, palavra de busca (manual 08) | nunca |
| 17 | `texto_post` | Texto do post | legenda por rede, limites, hashtags, CTA "comenta aí", tom, crédito e aviso de valores no texto (manual 08) | nunca |
| 18 | `formato_rede` | Formato por rede | MP4 H.264 + AAC, 9:16, duração padrão HP 7–90 s, arquivo ≤ 100 MB, Pinterest só nos 3 canais | nunca |
| 19 | `final_retencao` | Final e retenção | termina ≤ 0,5 s depois da última fala/ação, sem tela preta, com pergunta/CTA, ritmo sem "barriga" no meio | nunca |
| 20 | `identidade` | Identidade do canal | selo, cores e fontes do canal nos cartões e na capa (manual 07, tabela 2.9) | nunca |

#### 2.6.2 Estático (`carrossel`, `feed`, `story`, `story_enquete`, `story_contagem`, `pin`, `threads_imagem`) — até 12 critérios

| # | Código | Nome | O que se avalia | Quando não se aplica |
|---|---|---|---|---|
| 1 | `tema` | Tema e atualidade | igual ao vídeo | nunca |
| 2 | `fonte_direitos` | Fonte e direitos | fotos oficiais/divulgação/próprias/licença livre | nunca |
| 3 | `regras_conteudo` | Regras de conteúdo (**eliminatório**) | igual ao vídeo | nunca |
| 4 | `arte_medidas` | Medidas da arte | tamanho exato, JPG sRGB, zona segura, contraste (pelo `design.json` + conferências) | nunca |
| 5 | `texto_arte` | Texto da arte | ortografia, até 40 palavras por lâmina, número em algarismo, unidades iguais | arte sem texto |
| 6 | `sequencia_laminas` | Sequência das lâminas | numeração "n/N", ordem, 5–10 lâminas, lâmina 1 gancho, última CTA | tudo que não é carrossel |
| 7 | `capa` | Capa / lâmina 1 / arte principal | para o olho no feed, legível na miniatura | nunca |
| 8 | `credito` | Crédito (**eliminatório**) | em toda imagem de terceiro e no texto | material 100% próprio |
| 9 | `valores` | Valores aproximados (**eliminatório**) | rodapé na arte e aviso no texto | sem valor |
| 10 | `identidade` | Identidade do canal | molde do canal | nunca |
| 11 | `texto_post` | Texto do post | manual 08 | story sem texto de post |
| 12 | `formato_rede` | Formato por rede | JPG, tamanho por rede, Pinterest só nos 3 canais | nunca |
| 13 | `enquete` | Enquete (só `story_enquete`) | pergunta ≤ 25 caracteres, 2 opções curtas, caixa em x 140–940 y 1050–1450 | tudo que não é enquete |

#### 2.6.3 Texto puro do Threads (`threads_texto`) — 4 a 6 critérios

`tema`, `regras_conteudo`, `texto_post`, `formato_rede` (até 500 caracteres, 1 tópico, sem hashtag no texto) e, se houver, `credito` e `valores`.

### 2.7 Tabela critério → etapa de destino → cargo

| Critério | Etapa de destino | Cargo que conserta | Observação |
|---|---|---|---|
| `tema` | `01_pedidos` | curador | assunto frio, repetido ou fora do canal |
| `fonte_direitos` | `01_pedidos` | curador | se só falta baixar em qualidade melhor da **mesma** fonte: cargo `app_download` |
| `regras_conteudo` | `01_pedidos` | curador | irreparável (vazamento, Flow Games, TV) = **descartar** na hora, não volta |
| `trecho_corte` | `02_baixados` | editor | refazer o corte do bruto (e a transcrição do trecho novo) |
| `legenda` | `03_legenda_dublagem` | legendador | texto, sincronia, posição, quebra |
| `traducao_dublagem` | `03_legenda_dublagem` | tradutor_dublador ou narrador | narrador quando é o "Toque HP" |
| `gancho` | `04_edicao` | editor | se o gancho ruim é a pergunta falada do "Toque HP": `03_legenda_dublagem`, cargo narrador |
| `audio_loudness` | `04_edicao` | editor | mixagem e normalização |
| `musica_direitos` | `04_edicao` | editor | trocar a música por livre / baixar volume / tirar do Futebol |
| `imagem_nitidez` | `04_edicao` | editor | se a causa é a fonte ruim (480p): `01_pedidos`, cargo curador |
| `enquadramento_safe` | `04_edicao` | editor | reposicionar texto/recorte |
| `texto_tela` | `04_edicao` | editor | cartões e textos queimados |
| `credito` | `04_edicao` | editor (tela), designer (arte), redator (texto) | escolha o cargo pela peça onde faltou |
| `valores` | `04_edicao` | redator (texto), editor (tela), designer (arte) | escolha o cargo pela peça onde faltou |
| `capa` | `04_edicao` | designer | manual 07 |
| `titulo_capa` | `04_edicao` | redator | manual 08 |
| `texto_post` | `04_edicao` | redator | manual 08 |
| `formato_rede` | `04_edicao` | editor | codec, duração, tamanho; Pinterest indevido: redator/designer |
| `final_retencao` | `04_edicao` | editor | corte do fim, CTA final |
| `identidade` | `04_edicao` | designer (moldes) ou editor (cartões) | |
| `arte_medidas` | `04_edicao` | designer | |
| `texto_arte` | `04_edicao` | redator | o Designer gera a arte de novo depois |
| `sequencia_laminas` | `04_edicao` | designer | se o problema é o conteúdo das lâminas (faltam fatos): `01_pedidos`, curador |
| `enquete` | `04_edicao` | redator (pergunta/opções) ou designer (caixa) | |
| **média < 5 (Razoável)** | **`01_pedidos`** | **curador** | sempre, qualquer que seja o critério de menor nota |

### 2.8 Como as voltas são contadas

- Quando o Revisor grava `refazer.json`, o app move a pasta para a `etapa_destino`.
- Quando o item **volta** para `05_revisao`, o app **renomeia** o `refazer.json` antigo para `refazer_volta1.json` (na segunda volta, `refazer_volta2.json`). Assim a pasta sempre tem, no máximo, **um** arquivo de veredito "vivo".
- **Voltas = quantidade de arquivos `refazer_volta*.json` na pasta.** `revisao_n = voltas + 1`.
- Sem o app (hoje), quem move a pasta de volta para `05_revisao` faz a renomeação à mão (passo 58).

| Situação da pasta ao chegar em `05_revisao` | `voltas` | `revisao_n` | Se reprovar agora… |
|---|---|---|---|
| nenhum `refazer_volta*.json` | 0 | 1 | volta (1ª volta) |
| `refazer_volta1.json` | 1 | 2 | volta (2ª volta — a última) |
| `refazer_volta1.json` + `refazer_volta2.json` | 2 | 3 | **descarta e registra** |

### 2.9 O esquema JSON completo (`hp.revisao/1`)

Os três arquivos de veredito seguem este esquema (padrão JSON Schema, versão 2020-12). O app **recusa** gravar ou mover um item cujo veredito não passe por ele **(validação a criar — etapa 3)**. O esquema também fica salvo como arquivo para o app usar: `G:\Meu Drive\Hypado\06 Projeto\app\hp_studio\esteira\esquemas\revisao.schema.json` **(a criar — etapa 3; o conteúdo é exatamente o bloco abaixo)**.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "hp.revisao/1",
  "title": "Veredito do Revisor da HP (aprovado.json, refazer.json ou descartado.json)",
  "type": "object",
  "additionalProperties": false,
  "required": ["esquema", "item", "canal", "tipo", "prioridade", "revisao_n", "voltas", "voltas_max",
               "notas", "media", "classe", "veredito", "criterio_menor", "etapa_destino", "cargo_destino",
               "motivo", "o_que_refazer", "travas", "medidas", "quadros", "textos_conferidos",
               "revisor", "versao_manual", "modo", "data"],
  "properties": {
    "esquema": {"const": "hp.revisao/1"},
    "item": {"type": "string", "pattern": "^P[012]_[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{4}_(gta|futebol|filmes|receitas|carros|destinos)_[a-z0-9-]+$"},
    "canal": {"enum": ["gta", "futebol", "filmes", "receitas", "carros", "destinos"]},
    "tipo": {"enum": ["reel", "carrossel", "feed", "story", "story_enquete", "story_contagem", "pin", "threads_imagem", "threads_texto"]},
    "prioridade": {"enum": ["P0", "P1", "P2"]},
    "revisao_n": {"type": "integer", "minimum": 1, "maximum": 3, "description": "1 = primeira revisão; 3 = última possível"},
    "voltas": {"type": "integer", "minimum": 0, "maximum": 2, "description": "quantas vezes o item JÁ voltou antes desta revisão (= revisao_n - 1)"},
    "voltas_max": {"const": 2},
    "notas": {
      "type": "object",
      "minProperties": 1,
      "propertyNames": {"enum": ["tema", "fonte_direitos", "regras_conteudo", "trecho_corte", "gancho", "legenda",
                                  "traducao_dublagem", "audio_loudness", "musica_direitos", "imagem_nitidez",
                                  "enquadramento_safe", "texto_tela", "credito", "valores", "capa", "titulo_capa",
                                  "texto_post", "formato_rede", "final_retencao", "identidade",
                                  "arte_medidas", "texto_arte", "sequencia_laminas", "enquete"]},
      "additionalProperties": {"$ref": "#/$defs/nota"}
    },
    "media": {"type": "number", "minimum": 0, "maximum": 10, "description": "média dos critérios que se aplicam, truncada em 2 casas"},
    "classe": {"enum": ["Excelente", "Bom", "Médio", "Razoável"]},
    "veredito": {"enum": ["aprovado", "refazer", "descartar"]},
    "criterio_menor": {"type": ["string", "null"]},
    "etapa_destino": {"enum": ["06_agendados", "01_pedidos", "02_baixados", "03_legenda_dublagem", "04_edicao", "99_erros"]},
    "cargo_destino": {"$ref": "#/$defs/cargo_ou_fim"},
    "motivo": {"type": "string", "minLength": 10, "maxLength": 600},
    "o_que_refazer": {"type": "array", "items": {"$ref": "#/$defs/acao"}},
    "travas": {"type": "array", "items": {"$ref": "#/$defs/trava"}},
    "medidas": {"$ref": "#/$defs/medidas"},
    "quadros": {"type": "array", "maxItems": 4, "items": {"type": "string"}},
    "textos_conferidos": {"type": "array", "items": {"type": "string"}},
    "revisor": {"enum": ["claude", "app", "antonio"]},
    "versao_manual": {"type": "string"},
    "modo": {"enum": ["valendo", "sombra"]},
    "data": {"type": "string", "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}-03:00$"},
    "duracao_revisao_s": {"type": "integer", "minimum": 0},
    "anteriores": {"type": "array", "items": {"type": "string", "pattern": "^refazer_volta[12]\\.json$"}},
    "observacoes": {"type": "string"}
  },
  "$defs": {
    "cargo": {"enum": ["curador", "editor", "legendador", "tradutor_dublador", "narrador", "designer", "redator", "app_download"]},
    "cargo_ou_fim": {"enum": ["curador", "editor", "legendador", "tradutor_dublador", "narrador", "designer", "redator", "app_download", "publicador", "nenhum"]},
    "nota": {
      "type": "object",
      "additionalProperties": false,
      "required": ["nota", "aplica", "etapa", "cargo"],
      "properties": {
        "nota": {"type": ["number", "null"], "minimum": 0, "maximum": 10, "multipleOf": 0.5},
        "aplica": {"type": "boolean"},
        "etapa": {"enum": ["01_pedidos", "02_baixados", "03_legenda_dublagem", "04_edicao"]},
        "cargo": {"$ref": "#/$defs/cargo"},
        "como_medi": {"type": "string"},
        "obs": {"type": "string"}
      },
      "if": {"properties": {"aplica": {"const": false}}},
      "then": {"properties": {"nota": {"const": null}}},
      "else": {"properties": {"nota": {"type": "number"}}}
    },
    "acao": {
      "type": "object",
      "additionalProperties": false,
      "required": ["criterio", "peca", "cargo", "instrucao"],
      "properties": {
        "criterio": {"type": "string"},
        "peca": {"type": "string"},
        "cargo": {"$ref": "#/$defs/cargo"},
        "instrucao": {"type": "string", "minLength": 15}
      }
    },
    "trava": {
      "type": "object",
      "additionalProperties": false,
      "required": ["tipo", "criterio", "descricao"],
      "properties": {
        "tipo": {"enum": ["conteudo_irreparavel", "eliminatorio", "nota_minima", "limite_voltas"]},
        "criterio": {"type": "string"},
        "descricao": {"type": "string"}
      }
    },
    "medidas": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "duracao_s": {"type": ["number", "null"]},
        "largura": {"type": ["integer", "null"]},
        "altura": {"type": ["integer", "null"]},
        "fps": {"type": ["number", "null"]},
        "codec_video": {"type": ["string", "null"]},
        "codec_audio": {"type": ["string", "null"]},
        "lufs": {"type": ["number", "null"]},
        "pico_dbtp": {"type": ["number", "null"]},
        "tamanho_mb": {"type": ["number", "null"]},
        "tela_preta_s": {"type": ["number", "null"]},
        "silencio_s": {"type": ["number", "null"]},
        "caracteres": {"type": "object", "additionalProperties": {"type": "integer"}},
        "hashtags": {"type": "object", "additionalProperties": {"type": "integer"}},
        "laminas": {"type": ["integer", "null"]},
        "capa": {"type": ["string", "null"]}
      }
    }
  },
  "allOf": [
    {"if": {"properties": {"veredito": {"const": "aprovado"}}},
     "then": {"properties": {"etapa_destino": {"const": "06_agendados"}, "cargo_destino": {"const": "publicador"},
                             "media": {"minimum": 7}, "classe": {"enum": ["Excelente", "Bom"]},
                             "o_que_refazer": {"maxItems": 0}}}},
    {"if": {"properties": {"veredito": {"const": "refazer"}}},
     "then": {"properties": {"etapa_destino": {"enum": ["01_pedidos", "02_baixados", "03_legenda_dublagem", "04_edicao"]},
                             "cargo_destino": {"$ref": "#/$defs/cargo"},
                             "o_que_refazer": {"minItems": 1}, "voltas": {"maximum": 1}}}},
    {"if": {"properties": {"veredito": {"const": "descartar"}}},
     "then": {"properties": {"etapa_destino": {"const": "99_erros"}, "cargo_destino": {"const": "nenhum"},
                             "travas": {"minItems": 1}}}},
    {"if": {"properties": {"classe": {"const": "Razoável"}, "veredito": {"const": "refazer"}}, "required": ["classe", "veredito"]},
     "then": {"properties": {"etapa_destino": {"const": "01_pedidos"}, "cargo_destino": {"const": "curador"}}}}
  ]
}
```

**Os campos, em português:**

| Campo | Tipo | Obrigatório | O que é | Exemplo |
|---|---|---|---|---|
| `esquema` | texto fixo | sim | versão do formato | `"hp.revisao/1"` |
| `item` | texto | sim | nome exato da pasta | `"P1_2026-09-30_1830_gta_rockstar-quinta"` |
| `canal` | lista fechada | sim | `gta`, `futebol`, `filmes`, `receitas`, `carros`, `destinos` | `"gta"` |
| `tipo` | lista fechada | sim | do `pedido.json` | `"reel"` |
| `prioridade` | `P0`/`P1`/`P2` | sim | do nome da pasta | `"P1"` |
| `revisao_n` | inteiro 1–3 | sim | qual revisão é esta | `1` |
| `voltas` | inteiro 0–2 | sim | quantas voltas o item **já** teve antes desta revisão | `0` |
| `voltas_max` | fixo `2` | sim | lembrete da regra | `2` |
| `notas` | objeto | sim | uma entrada por critério; cada uma com `nota` (0–10, de 0,5 em 0,5, ou `null`), `aplica` (`true`/`false`), `etapa`, `cargo`, `como_medi`, `obs` | ver exemplos |
| `media` | número | sim | média dos critérios que se aplicam, **truncada** em 2 casas | `9.55` |
| `classe` | lista fechada | sim | `Excelente` (≥ 9), `Bom` (7–8,99), `Médio` (5–6,99), `Razoável` (< 5) | `"Excelente"` |
| `veredito` | lista fechada | sim | `aprovado`, `refazer`, `descartar` | `"aprovado"` |
| `criterio_menor` | texto ou `null` | sim | o critério que decidiu o destino (menor nota; em trava, o travado de menor nota) | `"legenda"` |
| `etapa_destino` | lista fechada | sim | `06_agendados`, `01_pedidos`, `02_baixados`, `03_legenda_dublagem`, `04_edicao`, `99_erros` | `"03_legenda_dublagem"` |
| `cargo_destino` | lista fechada | sim | quem age a seguir | `"legendador"` |
| `motivo` | texto 10–600 | sim | a explicação curta, para humano ler | `"Médio (6,55): legenda atrasada…"` |
| `o_que_refazer` | lista | sim | ações `{criterio, peca, cargo, instrucao}`; vazia se aprovado/descartado | ver exemplos |
| `travas` | lista | sim | travas acionadas `{tipo, criterio, descricao}`; tipos: `conteudo_irreparavel`, `eliminatorio`, `nota_minima`, `limite_voltas` | `[]` |
| `medidas` | objeto | sim | as medidas automáticas (duração, tamanho, fps, codecs, LUFS, pico, tamanho em MB, tela preta, silêncio, caracteres e hashtags por rede, lâminas, tamanho da capa) | ver exemplos |
| `quadros` | lista | sim | os quadros olhados | `["quadro_inicio.jpg", "quadro_meio.jpg", "quadro_fim.jpg"]` |
| `textos_conferidos` | lista | sim | os arquivos de texto/arte lidos | `["post.json", "legenda.srt", "capa.jpg"]` |
| `revisor` | lista fechada | sim | `claude`, `app` ou `antonio` | `"claude"` |
| `versao_manual` | texto | sim | versão deste manual usada | `"09 v1.0"` |
| `modo` | `valendo`/`sombra` | sim | `sombra` = revisão do app que só serve para comparar (não move nada) | `"valendo"` |
| `data` | data e hora com fuso de Brasília | sim | quando o veredito foi gravado | `"2026-09-30T16:20:05-03:00"` |
| `duracao_revisao_s` | inteiro | não | quanto tempo levou | `184` |
| `anteriores` | lista | não | os `refazer_volta*.json` que existiam | `["refazer_volta1.json"]` |
| `observacoes` | texto | não | sugestões que não obrigam ninguém; critérios < 7 de etapas anteriores ao destino | `"Sugestão: cortar 0,5 s do fim"` |

### 2.10 Exemplos completos (um de cada situação)

> Todos os fatos (placar, preços, títulos) são **fictícios**, só para mostrar o formato. As contas de média foram conferidas: some as notas com `aplica: true` e divida pela quantidade.

#### Exemplo 1 — `aprovado.json`, **Excelente** (GTA 6, reel)

17 critérios se aplicam; soma 162,5; média 9,558… → gravada **9.55** → Excelente → aprovado.

```json
{
  "esquema": "hp.revisao/1",
  "item": "P1_2026-09-30_1830_gta_rockstar-quinta",
  "canal": "gta",
  "tipo": "reel",
  "prioridade": "P1",
  "revisao_n": 1,
  "voltas": 0,
  "voltas_max": 2,
  "notas": {
    "tema": {"nota": 10, "aplica": true, "etapa": "01_pedidos", "cargo": "curador", "como_medi": "pedido + data de hoje", "obs": "novidade do dia, oficial"},
    "fonte_direitos": {"nota": 9, "aplica": true, "etapa": "01_pedidos", "cargo": "curador", "como_medi": "pedido.fonte", "obs": "criador com crédito; fonte 1080p"},
    "regras_conteudo": {"nota": 10, "aplica": true, "etapa": "01_pedidos", "cargo": "curador", "como_medi": "checklist 4.x + palavras proibidas", "obs": "nada de vazamento, nada de Flow Games"},
    "trecho_corte": {"nota": 9, "aplica": true, "etapa": "02_baixados", "cargo": "editor", "como_medi": "duração e quadro de início", "obs": "começa na fala certa"},
    "gancho": {"nota": 9, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "quadro_inicio + gancho_tela", "obs": "pergunta clara em 0,5 s"},
    "legenda": {"nota": 9.5, "aplica": true, "etapa": "03_legenda_dublagem", "cargo": "legendador", "como_medi": "legenda.srt x quadros", "obs": "sem erro; 1 bloco um pouco longo"},
    "traducao_dublagem": {"nota": null, "aplica": false, "etapa": "03_legenda_dublagem", "cargo": "tradutor_dublador", "como_medi": "", "obs": "não se aplica"},
    "audio_loudness": {"nota": 10, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "ebur128", "obs": "-14,2 LUFS, pico -1,4 dBTP"},
    "musica_direitos": {"nota": null, "aplica": false, "etapa": "04_edicao", "cargo": "editor", "como_medi": "", "obs": "não se aplica"},
    "imagem_nitidez": {"nota": 9, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "quadros + Video:", "obs": "1080x1920 30 fps, nítido"},
    "enquadramento_safe": {"nota": 10, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "quadros", "obs": "textos queimados dentro da zona"},
    "texto_tela": {"nota": 9, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "quadros", "obs": "cartão inicial ok"},
    "credito": {"nota": 10, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "quadros + post.json", "obs": "Vídeo: @criadorexemplo na tela e em todas as redes"},
    "valores": {"nota": null, "aplica": false, "etapa": "04_edicao", "cargo": "redator", "como_medi": "", "obs": "não se aplica"},
    "capa": {"nota": 9.5, "aplica": true, "etapa": "04_edicao", "cargo": "designer", "como_medi": "capa.jpg + design.json", "obs": "contraste 7,11, dentro do 3:4"},
    "titulo_capa": {"nota": 10, "aplica": true, "etapa": "04_edicao", "cargo": "redator", "como_medi": "post.json x transcrição", "obs": "promete só o que o vídeo mostra"},
    "texto_post": {"nota": 10, "aplica": true, "etapa": "04_edicao", "cargo": "redator", "como_medi": "contadores do manual 08", "obs": "limites e hashtags ok"},
    "formato_rede": {"nota": 10, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "Video: + tamanho", "obs": "H.264/AAC, 38,4 s, 21 MB"},
    "final_retencao": {"nota": 8.5, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "quadro_fim", "obs": "termina na pergunta; último 0,5 s parado"},
    "identidade": {"nota": 10, "aplica": true, "etapa": "04_edicao", "cargo": "designer", "como_medi": "quadros + capa", "obs": "selo e cores do GTA"}
  },
  "media": 9.55,
  "classe": "Excelente",
  "veredito": "aprovado",
  "criterio_menor": "final_retencao",
  "etapa_destino": "06_agendados",
  "cargo_destino": "publicador",
  "motivo": "Excelente: gancho claro, crédito em tudo, áudio no alvo. Só o fim poderia cortar 0,5 s.",
  "o_que_refazer": [],
  "travas": [],
  "medidas": {"duracao_s": 38.4, "largura": 1080, "altura": 1920, "fps": 30, "codec_video": "h264", "codec_audio": "aac", "lufs": -14.2, "pico_dbtp": -1.4, "tamanho_mb": 21.3, "tela_preta_s": 0.0, "silencio_s": 0.0, "caracteres": {"instagram": 284, "facebook": 218, "tiktok": 128, "youtube_titulo": 52, "youtube_descricao": 268, "threads": 165}, "hashtags": {"instagram": 5, "facebook": 2, "tiktok": 4, "youtube": 3, "threads": 0}, "laminas": null, "capa": "1080x1920"},
  "quadros": ["quadro_inicio.jpg", "quadro_meio.jpg", "quadro_fim.jpg"],
  "textos_conferidos": ["post.json", "legenda.srt", "capa.jpg"],
  "revisor": "claude",
  "versao_manual": "09 v1.0",
  "modo": "valendo",
  "data": "2026-09-30T16:20:05-03:00",
  "duracao_revisao_s": 184,
  "anteriores": [],
  "observacoes": "Sugestão para o Editor (não obrigatória): cortar os 0,5 s finais parados."
}
```

#### Exemplo 2 — `aprovado.json`, **Bom** (Destinos, reel próprio com narração "Toque HP")

19 critérios; soma 159,5; média 8,394… → **8.39** → Bom → aprovado (nenhuma nota abaixo de 7, nenhuma trava).

```json
{
  "esquema": "hp.revisao/1",
  "item": "P2_2026-10-04_1000_destinos_gramado-barato",
  "canal": "destinos",
  "tipo": "reel",
  "prioridade": "P2",
  "revisao_n": 1,
  "voltas": 0,
  "voltas_max": 2,
  "notas": {
    "tema": {"nota": 8, "aplica": true, "etapa": "01_pedidos", "cargo": "curador", "como_medi": "pedido", "obs": "bom para outubro; assunto já feito há 40 dias por outro ângulo"},
    "fonte_direitos": {"nota": 9, "aplica": true, "etapa": "01_pedidos", "cargo": "curador", "como_medi": "pedido.fonte", "obs": "fotos com crédito e vídeo do criador autorizado"},
    "regras_conteudo": {"nota": 10, "aplica": true, "etapa": "01_pedidos", "cargo": "curador", "como_medi": "checklist", "obs": "voz Piper em vídeo próprio de Destinos: permitido"},
    "trecho_corte": {"nota": null, "aplica": false, "etapa": "02_baixados", "cargo": "editor", "como_medi": "", "obs": "não se aplica"},
    "gancho": {"nota": 7, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "quadro_inicio + narração", "obs": "pergunta do Toque HP começa em 1,8 s (limite 2 s)"},
    "legenda": {"nota": 8, "aplica": true, "etapa": "03_legenda_dublagem", "cargo": "legendador", "como_medi": "legenda.srt", "obs": "ok; 2 blocos com 3 linhas"},
    "traducao_dublagem": {"nota": 7.5, "aplica": true, "etapa": "03_legenda_dublagem", "cargo": "narrador", "como_medi": "narração (manual 06)", "obs": "voz neutra ok; 'Gramado' com sílaba forte errada 1 vez"},
    "audio_loudness": {"nota": 8, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "ebur128", "obs": "-15,3 LUFS (fora do ±1 por 0,3)"},
    "musica_direitos": {"nota": 9, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "pedido + editor", "obs": "música livre registrada; volume ok"},
    "imagem_nitidez": {"nota": 8, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "quadros", "obs": "2 fotos levemente suaves"},
    "enquadramento_safe": {"nota": 9, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "quadros", "obs": "ok"},
    "texto_tela": {"nota": 8, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "quadros", "obs": "ok"},
    "credito": {"nota": 9, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "quadros + post.json", "obs": "ok; crédito da tela pequeno"},
    "valores": {"nota": 9, "aplica": true, "etapa": "04_edicao", "cargo": "redator", "como_medi": "post.json + quadros", "obs": "aviso presente em todas as redes"},
    "capa": {"nota": 7.5, "aplica": true, "etapa": "04_edicao", "cargo": "designer", "como_medi": "capa.jpg", "obs": "título na faixa, foto sem emoção"},
    "titulo_capa": {"nota": 8, "aplica": true, "etapa": "04_edicao", "cargo": "redator", "como_medi": "post.json", "obs": "ok"},
    "texto_post": {"nota": 8.5, "aplica": true, "etapa": "04_edicao", "cargo": "redator", "como_medi": "contadores", "obs": "ok"},
    "formato_rede": {"nota": 10, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "Video:", "obs": "ok"},
    "final_retencao": {"nota": 7, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "quadro_fim", "obs": "fecho com pergunta, mas termina em foto parada 2 s"},
    "identidade": {"nota": 9, "aplica": true, "etapa": "04_edicao", "cargo": "designer", "como_medi": "quadros", "obs": "ok"}
  },
  "media": 8.39,
  "classe": "Bom",
  "veredito": "aprovado",
  "criterio_menor": "gancho",
  "etapa_destino": "06_agendados",
  "cargo_destino": "publicador",
  "motivo": "Bom: aprovado. Pontos a melhorar nos próximos: gancho mais cedo (antes de 1 s), capa com mais emoção, fim sem foto parada.",
  "o_que_refazer": [],
  "travas": [],
  "medidas": {"duracao_s": 44.0, "largura": 1080, "altura": 1920, "fps": 30, "codec_video": "h264", "codec_audio": "aac", "lufs": -15.3, "pico_dbtp": -1.9, "tamanho_mb": 27.8, "tela_preta_s": 0.0, "silencio_s": 0.0, "caracteres": {"instagram": 301, "facebook": 190, "tiktok": 142, "youtube_titulo": 43, "youtube_descricao": 344, "threads": 210, "pinterest_titulo": 38, "pinterest_descricao": 260}, "hashtags": {"instagram": 4, "facebook": 2, "tiktok": 4, "youtube": 3, "threads": 0, "pinterest": 0}, "laminas": null, "capa": "1080x1920"},
  "quadros": ["quadro_inicio.jpg", "quadro_meio.jpg", "quadro_fim.jpg"],
  "textos_conferidos": ["post.json", "legenda.srt", "capa.jpg", "pin.jpg"],
  "revisor": "claude",
  "versao_manual": "09 v1.0",
  "modo": "valendo",
  "data": "2026-10-02T10:12:40-03:00",
  "duracao_revisao_s": 262,
  "anteriores": [],
  "observacoes": "Nenhuma nota abaixo de 7. Registrado para o Analista (manual 11)."
}
```

#### Exemplo 3 — `refazer.json`, **Médio** (Receitas, reel) → volta para `03_legenda_dublagem`

20 critérios; soma 131; média **6.55** → Médio. Menor nota: `legenda` (3) → etapa `03_legenda_dublagem`, cargo `legendador`. Como o item vai passar de novo por 03 e 04, entram em `o_que_refazer` todos os critérios com nota < 7 dessas etapas.

```json
{
  "esquema": "hp.revisao/1",
  "item": "P1_2026-10-01_1130_receitas_pao-queijo-frigideira",
  "canal": "receitas",
  "tipo": "reel",
  "prioridade": "P1",
  "revisao_n": 1,
  "voltas": 0,
  "voltas_max": 2,
  "notas": {
    "tema": {"nota": 8, "aplica": true, "etapa": "01_pedidos", "cargo": "curador", "como_medi": "pedido", "obs": "receita procurada"},
    "fonte_direitos": {"nota": 8, "aplica": true, "etapa": "01_pedidos", "cargo": "curador", "como_medi": "pedido.fonte", "obs": "vídeo próprio + crédito da receita original"},
    "regras_conteudo": {"nota": 10, "aplica": true, "etapa": "01_pedidos", "cargo": "curador", "como_medi": "checklist", "obs": "ok"},
    "trecho_corte": {"nota": 7, "aplica": true, "etapa": "02_baixados", "cargo": "editor", "como_medi": "quadro_inicio", "obs": "começa 1 s antes da ação"},
    "gancho": {"nota": 6, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "quadro_inicio", "obs": "gancho de tela só em 2,5 s"},
    "legenda": {"nota": 3, "aplica": true, "etapa": "03_legenda_dublagem", "cargo": "legendador", "como_medi": "legenda.srt x quadros", "obs": "legenda atrasada ~1 s o vídeo todo; 'polvilho' escrito 'povilho'"},
    "traducao_dublagem": {"nota": 5, "aplica": true, "etapa": "03_legenda_dublagem", "cargo": "narrador", "como_medi": "narração (manual 06)", "obs": "narração cortada no fim; fecho sem pergunta"},
    "audio_loudness": {"nota": 5, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "ebur128", "obs": "-19,8 LUFS (muito baixo)"},
    "musica_direitos": {"nota": 8, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "pedido + editor", "obs": "livre"},
    "imagem_nitidez": {"nota": 7, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "quadros", "obs": "ok"},
    "enquadramento_safe": {"nota": 6, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "quadros", "obs": "medida '1 xícara' atrás dos botões (x 960)"},
    "texto_tela": {"nota": 5, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "quadros", "obs": "'2 colheres' e '2 colher' na mesma tela"},
    "credito": {"nota": 8, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "quadros + post.json", "obs": "ok"},
    "valores": {"nota": 7, "aplica": true, "etapa": "04_edicao", "cargo": "redator", "como_medi": "post.json", "obs": "aviso presente, sem mês/ano no TikTok"},
    "capa": {"nota": 5, "aplica": true, "etapa": "04_edicao", "cargo": "designer", "como_medi": "capa.jpg + conferencia_capa.jpg", "obs": "título encosta na faixa de baixo (y 1480)"},
    "titulo_capa": {"nota": 6, "aplica": true, "etapa": "04_edicao", "cargo": "redator", "como_medi": "post.json", "obs": "'Pão de queijo fácil' genérico"},
    "texto_post": {"nota": 6, "aplica": true, "etapa": "04_edicao", "cargo": "redator", "como_medi": "contadores", "obs": "Instagram com 7 hashtags"},
    "formato_rede": {"nota": 9, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "Video:", "obs": "ok"},
    "final_retencao": {"nota": 5, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "quadro_fim", "obs": "termina com 1,5 s de tela preta"},
    "identidade": {"nota": 7, "aplica": true, "etapa": "04_edicao", "cargo": "designer", "como_medi": "quadros", "obs": "ok"}
  },
  "media": 6.55,
  "classe": "Médio",
  "veredito": "refazer",
  "criterio_menor": "legenda",
  "etapa_destino": "03_legenda_dublagem",
  "cargo_destino": "legendador",
  "motivo": "Médio (6,55): a legenda está atrasada cerca de 1 s no vídeo todo e com erro de ortografia; volta ao Legendador. Na passagem pela edição, corrigir também áudio, textos na tela, capa, título, legenda do post e o fim.",
  "o_que_refazer": [
    {"criterio": "legenda", "peca": "legenda.srt / legenda.ass", "cargo": "legendador", "instrucao": "Adiantar todos os blocos em ~1,0 s (conferir com o áudio); corrigir 'povilho' para 'polvilho'."},
    {"criterio": "traducao_dublagem", "peca": "dublagem.wav", "cargo": "narrador", "instrucao": "Refazer o fecho: a narração corta no fim e falta a pergunta final do Toque HP."},
    {"criterio": "audio_loudness", "peca": "final.mp4", "cargo": "editor", "instrucao": "Normalizar para -14 LUFS (±1) com pico ≤ -1 dBTP; está em -19,8."},
    {"criterio": "texto_tela", "peca": "final.mp4", "cargo": "editor", "instrucao": "Padronizar '2 colheres' em todos os cartões."},
    {"criterio": "capa", "peca": "capa.jpg", "cargo": "designer", "instrucao": "Subir o título para a faixa y 420–1000; hoje termina em y 1480."},
    {"criterio": "final_retencao", "peca": "final.mp4", "cargo": "editor", "instrucao": "Cortar 1,5 s de tela preta no fim; terminar na pergunta."},
    {"criterio": "gancho", "peca": "final.mp4", "cargo": "editor", "instrucao": "Gancho de tela aparecer até 1 s (hoje 2,5 s)."},
    {"criterio": "enquadramento_safe", "peca": "final.mp4", "cargo": "editor", "instrucao": "Tirar '1 xícara' de x 960: manter textos até x 930."},
    {"criterio": "titulo_capa", "peca": "post.json", "cargo": "redator", "instrucao": "Título mais específico (ex.: 'Pão de queijo de frigideira em 10 min')."},
    {"criterio": "texto_post", "peca": "post.json", "cargo": "redator", "instrucao": "Instagram com 7 hashtags: deixar 3 a 5; pôr mês/ano no aviso de valores do TikTok."}
  ],
  "travas": [],
  "medidas": {"duracao_s": 52.7, "largura": 1080, "altura": 1920, "fps": 30, "codec_video": "h264", "codec_audio": "aac", "lufs": -19.8, "pico_dbtp": -4.1, "tamanho_mb": 33.0, "tela_preta_s": 1.5, "silencio_s": 0.0, "caracteres": {"instagram": 512, "facebook": 230, "tiktok": 160, "youtube_titulo": 49, "youtube_descricao": 301, "threads": 240}, "hashtags": {"instagram": 7, "facebook": 2, "tiktok": 4, "youtube": 3, "threads": 0}, "laminas": null, "capa": "1080x1920"},
  "quadros": ["quadro_inicio.jpg", "quadro_meio.jpg", "quadro_fim.jpg"],
  "textos_conferidos": ["post.json", "legenda.srt", "capa.jpg"],
  "revisor": "claude",
  "versao_manual": "09 v1.0",
  "modo": "valendo",
  "data": "2026-10-01T09:41:17-03:00",
  "duracao_revisao_s": 305,
  "anteriores": [],
  "observacoes": ""
}
```

#### Exemplo 4 — `refazer.json`, **Razoável** (Futebol, reel) → volta ao Curador

17 critérios; soma 78; média 4,588… → **4.58** → Razoável → `01_pedidos`, cargo `curador`, com **uma** ação (refazer o pedido ou descartar). As menores notas empataram em 2 (`tema`, `gancho`, `final_retencao`) — vence `tema`, a etapa mais cedo.

```json
{
  "esquema": "hp.revisao/1",
  "item": "P1_2026-10-01_2230_futebol_debate-rodada",
  "canal": "futebol",
  "tipo": "reel",
  "prioridade": "P1",
  "revisao_n": 1,
  "voltas": 0,
  "voltas_max": 2,
  "notas": {
    "tema": {"nota": 2, "aplica": true, "etapa": "01_pedidos", "cargo": "curador", "como_medi": "pedido + data", "obs": "debate de rodada de 3 dias atrás; assunto frio"},
    "fonte_direitos": {"nota": 6, "aplica": true, "etapa": "01_pedidos", "cargo": "curador", "como_medi": "pedido.fonte", "obs": "vídeos oficiais, mas 1 recorte sem clube identificado"},
    "regras_conteudo": {"nota": 10, "aplica": true, "etapa": "01_pedidos", "cargo": "curador", "como_medi": "checklist", "obs": "sem TV, sem narração sintética"},
    "trecho_corte": {"nota": 3, "aplica": true, "etapa": "02_baixados", "cargo": "editor", "como_medi": "quadros", "obs": "recortes longos e sem o lance principal"},
    "gancho": {"nota": 2, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "quadro_inicio", "obs": "começa com escudo parado 3 s"},
    "legenda": {"nota": 5, "aplica": true, "etapa": "03_legenda_dublagem", "cargo": "legendador", "como_medi": "legenda.srt", "obs": "ok, mas pouco útil"},
    "traducao_dublagem": {"nota": null, "aplica": false, "etapa": "03_legenda_dublagem", "cargo": "tradutor_dublador", "como_medi": "", "obs": "não se aplica"},
    "audio_loudness": {"nota": 4, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "ebur128", "obs": "-22 LUFS, áudio original muito baixo"},
    "musica_direitos": {"nota": null, "aplica": false, "etapa": "04_edicao", "cargo": "editor", "como_medi": "", "obs": "não se aplica"},
    "imagem_nitidez": {"nota": 5, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "quadros", "obs": "1 recorte 720p ampliado"},
    "enquadramento_safe": {"nota": 5, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "quadros", "obs": "nome do jogador atrás da legenda do post"},
    "texto_tela": {"nota": 4, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "quadros", "obs": "sem o número pedido no modo debate"},
    "credito": {"nota": 8, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "quadros + post.json", "obs": "ok"},
    "valores": {"nota": null, "aplica": false, "etapa": "04_edicao", "cargo": "redator", "como_medi": "", "obs": "não se aplica"},
    "capa": {"nota": 3, "aplica": true, "etapa": "04_edicao", "cargo": "designer", "como_medi": "capa.jpg", "obs": "3 rostos pequenos, título ilegível na grade"},
    "titulo_capa": {"nota": 3, "aplica": true, "etapa": "04_edicao", "cargo": "redator", "como_medi": "post.json", "obs": "'Rodada polêmica' genérico"},
    "texto_post": {"nota": 4, "aplica": true, "etapa": "04_edicao", "cargo": "redator", "como_medi": "contadores + leitura", "obs": "sem pergunta de CTA"},
    "formato_rede": {"nota": 6, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "Video:", "obs": "98 s (acima do padrão HP de 90 s)"},
    "final_retencao": {"nota": 2, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "quadro_fim", "obs": "termina no meio de uma frase"},
    "identidade": {"nota": 6, "aplica": true, "etapa": "04_edicao", "cargo": "designer", "como_medi": "quadros", "obs": "ok"}
  },
  "media": 4.58,
  "classe": "Razoável",
  "veredito": "refazer",
  "criterio_menor": "tema",
  "etapa_destino": "01_pedidos",
  "cargo_destino": "curador",
  "motivo": "Razoável (4,58): assunto frio (rodada de domingo, 3 dias atrás) e montagem sem gancho nem fecho. Volta ao Curador para decidir se vale refazer com a rodada de hoje ou descartar.",
  "o_que_refazer": [
    {"criterio": "tema", "peca": "pedido.json", "cargo": "curador", "instrucao": "Trocar para a rodada de quarta (01/10) ou descartar; se refizer, seguir o modo debate: 3 recortes com nome e 1 número + 'comenta aí'."}
  ],
  "travas": [],
  "medidas": {"duracao_s": 98.0, "largura": 1080, "altura": 1920, "fps": 30, "codec_video": "h264", "codec_audio": "aac", "lufs": -22.0, "pico_dbtp": -6.5, "tamanho_mb": 61.2, "tela_preta_s": 0.0, "silencio_s": 2.1, "caracteres": {"instagram": 140, "facebook": 120, "tiktok": 90, "youtube_titulo": 16, "youtube_descricao": 120, "threads": 100}, "hashtags": {"instagram": 3, "facebook": 1, "tiktok": 3, "youtube": 1, "threads": 0}, "laminas": null, "capa": "1080x1920"},
  "quadros": ["quadro_inicio.jpg", "quadro_meio.jpg", "quadro_fim.jpg"],
  "textos_conferidos": ["post.json", "legenda.srt", "capa.jpg"],
  "revisor": "claude",
  "versao_manual": "09 v1.0",
  "modo": "valendo",
  "data": "2026-10-01T20:05:02-03:00",
  "duracao_revisao_s": 240,
  "anteriores": [],
  "observacoes": ""
}
```

#### Exemplo 5 — `refazer.json` por **trava** (Filmes e Séries, carrossel) — média Bom, mas crédito faltando

11 critérios; soma 96; média 8,727… → **8.72** (Bom), mas `credito` = 3 está abaixo do mínimo 7 (eliminatório) → refazer → `04_edicao`, cargo `designer` (o crédito faltou na **arte**).

```json
{
  "esquema": "hp.revisao/1",
  "item": "P1_2026-10-01_1200_filmes_estreias-carrossel",
  "canal": "filmes",
  "tipo": "carrossel",
  "prioridade": "P1",
  "revisao_n": 1,
  "voltas": 0,
  "voltas_max": 2,
  "notas": {
    "tema": {"nota": 9, "aplica": true, "etapa": "01_pedidos", "cargo": "curador", "como_medi": "pedido", "obs": "estreias do mês, procurado"},
    "fonte_direitos": {"nota": 9, "aplica": true, "etapa": "01_pedidos", "cargo": "curador", "como_medi": "pedido.fonte", "obs": "pôsteres de divulgação"},
    "regras_conteudo": {"nota": 10, "aplica": true, "etapa": "01_pedidos", "cargo": "curador", "como_medi": "checklist", "obs": "sem spoiler"},
    "arte_medidas": {"nota": 9, "aplica": true, "etapa": "04_edicao", "cargo": "designer", "como_medi": "design.json + conferencia_carrossel_margens.jpg", "obs": "1080x1350, margens ok"},
    "texto_arte": {"nota": 9, "aplica": true, "etapa": "04_edicao", "cargo": "redator", "como_medi": "folha do carrossel", "obs": "ok"},
    "sequencia_laminas": {"nota": 9, "aplica": true, "etapa": "04_edicao", "cargo": "designer", "como_medi": "folha do carrossel", "obs": "1/7 a 7/7 em ordem"},
    "capa": {"nota": 9, "aplica": true, "etapa": "04_edicao", "cargo": "designer", "como_medi": "lamina_01.jpg", "obs": "gancho claro"},
    "credito": {"nota": 3, "aplica": true, "etapa": "04_edicao", "cargo": "designer", "como_medi": "lâminas + post.json", "obs": "lâminas 3 e 5 sem 'Imagem: divulgação/…'"},
    "valores": {"nota": null, "aplica": false, "etapa": "04_edicao", "cargo": "redator", "como_medi": "", "obs": "não se aplica"},
    "identidade": {"nota": 10, "aplica": true, "etapa": "04_edicao", "cargo": "designer", "como_medi": "folha", "obs": "ok"},
    "texto_post": {"nota": 9, "aplica": true, "etapa": "04_edicao", "cargo": "redator", "como_medi": "contadores", "obs": "ok"},
    "formato_rede": {"nota": 10, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "design.json", "obs": "JPG sRGB, 7 lâminas"}
  },
  "media": 8.72,
  "classe": "Bom",
  "veredito": "refazer",
  "criterio_menor": "credito",
  "etapa_destino": "04_edicao",
  "cargo_destino": "designer",
  "motivo": "Média 8,72 (Bom), mas o crédito é eliminatório: as lâminas 3 e 5 usam pôster de divulgação sem crédito. Volta ao Designer só para acrescentar o crédito.",
  "o_que_refazer": [
    {"criterio": "credito", "peca": "lamina_03.jpg, lamina_05.jpg", "cargo": "designer", "instrucao": "Acrescentar 'Imagem: divulgação/<plataforma>' embaixo à esquerda (28–32 px), igual às outras lâminas; não mexer no resto."}
  ],
  "travas": [
    {"tipo": "eliminatorio", "criterio": "credito", "descricao": "nota 3 (mínimo 7): crédito faltando em material de terceiro"}
  ],
  "medidas": {"duracao_s": null, "largura": 1080, "altura": 1350, "fps": null, "codec_video": null, "codec_audio": null, "lufs": null, "pico_dbtp": null, "tamanho_mb": 3.9, "tela_preta_s": null, "silencio_s": null, "caracteres": {"instagram": 402, "facebook": 210, "threads": 190}, "hashtags": {"instagram": 4, "facebook": 2, "threads": 0}, "laminas": 7, "capa": "1080x1350"},
  "quadros": ["conferencia_carrossel.jpg"],
  "textos_conferidos": ["post.json", "design.json", "pedido.json"],
  "revisor": "claude",
  "versao_manual": "09 v1.0",
  "modo": "valendo",
  "data": "2026-10-01T10:02:55-03:00",
  "duracao_revisao_s": 150,
  "anteriores": [],
  "observacoes": ""
}
```

#### Exemplo 6 — `descartado.json` na **3ª reprovação** (Carros, reel)

Já existem `refazer_volta1.json` e `refazer_volta2.json` (voltas = 2, revisão nº 3). 20 critérios; soma 132; média **6.60** → Médio → seria refazer, mas o limite de voltas acabou → **descartar** → `99_erros`, trava `limite_voltas`, registro em `descartes.csv`.

```json
{
  "esquema": "hp.revisao/1",
  "item": "P2_2026-10-03_1200_carros_5-mais-baratos-2026",
  "canal": "carros",
  "tipo": "reel",
  "prioridade": "P2",
  "revisao_n": 3,
  "voltas": 2,
  "voltas_max": 2,
  "notas": {
    "tema": {"nota": 8, "aplica": true, "etapa": "01_pedidos", "cargo": "curador", "como_medi": "pedido", "obs": "procurado"},
    "fonte_direitos": {"nota": 5, "aplica": true, "etapa": "01_pedidos", "cargo": "curador", "como_medi": "pedido.fonte", "obs": "vídeo de divulgação só existe em 480p"},
    "regras_conteudo": {"nota": 10, "aplica": true, "etapa": "01_pedidos", "cargo": "curador", "como_medi": "checklist", "obs": "ok"},
    "trecho_corte": {"nota": 7, "aplica": true, "etapa": "02_baixados", "cargo": "editor", "como_medi": "quadros", "obs": "ok"},
    "gancho": {"nota": 6, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "quadro_inicio", "obs": "ok, mas imagem borrada tira a força"},
    "legenda": {"nota": 7, "aplica": true, "etapa": "03_legenda_dublagem", "cargo": "legendador", "como_medi": "legenda.srt", "obs": "ok"},
    "traducao_dublagem": {"nota": 6, "aplica": true, "etapa": "03_legenda_dublagem", "cargo": "narrador", "como_medi": "narração (manual 06)", "obs": "ok, fecho corrido"},
    "audio_loudness": {"nota": 7, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "ebur128", "obs": "-15,0 LUFS"},
    "musica_direitos": {"nota": 8, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "editor", "obs": "livre"},
    "imagem_nitidez": {"nota": 3, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "quadros + Video:", "obs": "480p ampliado: borrado nas 3 voltas"},
    "enquadramento_safe": {"nota": 6, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "quadros", "obs": "preço perto dos botões"},
    "texto_tela": {"nota": 6, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "quadros", "obs": "ok"},
    "credito": {"nota": 8, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "quadros + post.json", "obs": "ok"},
    "valores": {"nota": 8, "aplica": true, "etapa": "04_edicao", "cargo": "redator", "como_medi": "post.json", "obs": "ok"},
    "capa": {"nota": 5, "aplica": true, "etapa": "04_edicao", "cargo": "designer", "como_medi": "capa.jpg", "obs": "quadro borrado"},
    "titulo_capa": {"nota": 7, "aplica": true, "etapa": "04_edicao", "cargo": "redator", "como_medi": "post.json", "obs": "ok"},
    "texto_post": {"nota": 7, "aplica": true, "etapa": "04_edicao", "cargo": "redator", "como_medi": "contadores", "obs": "ok"},
    "formato_rede": {"nota": 6, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "Video:", "obs": "ok, mas bitrate baixo"},
    "final_retencao": {"nota": 5, "aplica": true, "etapa": "04_edicao", "cargo": "editor", "como_medi": "quadro_fim", "obs": "ok"},
    "identidade": {"nota": 7, "aplica": true, "etapa": "04_edicao", "cargo": "designer", "como_medi": "quadros", "obs": "ok"}
  },
  "media": 6.6,
  "classe": "Médio",
  "veredito": "descartar",
  "criterio_menor": "imagem_nitidez",
  "etapa_destino": "99_erros",
  "cargo_destino": "nenhum",
  "motivo": "3ª revisão ainda Médio (6,60): a imagem continua borrada porque a fonte só existe em 480p. Já teve 2 voltas: descartado e registrado.",
  "o_que_refazer": [],
  "travas": [
    {"tipo": "limite_voltas", "criterio": "imagem_nitidez", "descricao": "reprovado na 3ª revisão (voltas = 2)"}
  ],
  "medidas": {"duracao_s": 61.2, "largura": 1080, "altura": 1920, "fps": 30, "codec_video": "h264", "codec_audio": "aac", "lufs": -15.0, "pico_dbtp": -1.2, "tamanho_mb": 18.4, "tela_preta_s": 0.0, "silencio_s": 0.0, "caracteres": {"instagram": 350, "facebook": 200, "tiktok": 150, "youtube_titulo": 42, "youtube_descricao": 320, "threads": 220, "pinterest_titulo": 41, "pinterest_descricao": 250}, "hashtags": {"instagram": 3, "facebook": 2, "tiktok": 3, "youtube": 3, "threads": 0, "pinterest": 0}, "laminas": null, "capa": "1080x1920"},
  "quadros": ["quadro_inicio.jpg", "quadro_meio.jpg", "quadro_fim.jpg"],
  "textos_conferidos": ["post.json", "legenda.srt", "capa.jpg", "pin.jpg"],
  "revisor": "claude",
  "versao_manual": "09 v1.0",
  "modo": "valendo",
  "data": "2026-10-02T15:30:44-03:00",
  "duracao_revisao_s": 130,
  "anteriores": ["refazer_volta1.json", "refazer_volta2.json"],
  "observacoes": "Sugestão ao Curador: se o tema voltar, buscar fonte ≥ 1080p antes de pedir."
}
```

#### Exemplo 7 — `descartado.json` **na hora** (GTA 6, conteúdo irreparável)

O vídeo mostra material de vazamento. Não precisa dar nota nos outros critérios: basta `regras_conteudo` = 0 com a trava `conteudo_irreparavel`. Não conta volta.

```json
{
  "esquema": "hp.revisao/1",
  "item": "P1_2026-10-01_1830_gta_mapa-leonida",
  "canal": "gta",
  "tipo": "reel",
  "prioridade": "P1",
  "revisao_n": 1,
  "voltas": 0,
  "voltas_max": 2,
  "notas": {
    "regras_conteudo": {"nota": 0, "aplica": true, "etapa": "01_pedidos", "cargo": "curador", "como_medi": "quadros + transcrição", "obs": "o vídeo mostra mapa de origem não oficial (vazamento)"}
  },
  "media": 0.0,
  "classe": "Razoável",
  "veredito": "descartar",
  "criterio_menor": "regras_conteudo",
  "etapa_destino": "99_erros",
  "cargo_destino": "nenhum",
  "motivo": "Descartado na hora: conteúdo de vazamento do GTA 6 (regra inviolável). Não conta volta; não pode ser consertado.",
  "o_que_refazer": [],
  "travas": [
    {"tipo": "conteudo_irreparavel", "criterio": "regras_conteudo", "descricao": "vazamento de GTA 6"}
  ],
  "medidas": {"duracao_s": 29.9, "largura": 1080, "altura": 1920, "fps": 30, "codec_video": "h264", "codec_audio": "aac", "lufs": null, "pico_dbtp": null, "tamanho_mb": 15.1, "tela_preta_s": null, "silencio_s": null, "caracteres": {}, "hashtags": {}, "laminas": null, "capa": null},
  "quadros": ["quadro_inicio.jpg", "quadro_meio.jpg", "quadro_fim.jpg"],
  "textos_conferidos": ["transcricao.json"],
  "revisor": "claude",
  "versao_manual": "09 v1.0",
  "modo": "valendo",
  "data": "2026-10-01T14:10:09-03:00",
  "duracao_revisao_s": 60,
  "anteriores": [],
  "observacoes": "Avisar o Curador para bloquear a fonte."
}
```

### 2.11 A linha do `historico.log`

Uma linha por revisão, sempre neste formato (a data e a hora vêm no começo):

```
2026-09-30T16:20:05-03:00 [revisor] aprovado media=9.55 classe=Excelente destino=06_agendados revisao=1 - claude
2026-10-01T09:41:17-03:00 [revisor] refazer media=6.55 classe=Médio menor=legenda destino=03_legenda_dublagem revisao=1 - claude
2026-10-02T15:30:44-03:00 [revisor] descartar media=6.60 classe=Médio menor=imagem_nitidez destino=99_erros revisao=3 trava=limite_voltas - claude
```

### 2.12 O registro de descarte (`descartes.csv`)

Todo descarte ganha uma linha em `H:\HypadoLocal\esteira\99_erros\descartes.csv` (separado por ponto e vírgula, para abrir direto no Excel em português). O Analista de resultados (manual 11) usa esse arquivo para achar o que mais faz item ser descartado.

```
data;item;canal;tipo;revisao_n;media;classe;criterio_menor;trava;motivo
2026-10-01T14:10:09-03:00;P1_2026-10-01_1830_gta_mapa-leonida;gta;reel;1;0.00;Razoável;regras_conteudo;conteudo_irreparavel;vazamento de GTA 6
2026-10-02T15:30:44-03:00;P2_2026-10-03_1200_carros_5-mais-baratos-2026;carros;reel;3;6.60;Médio;imagem_nitidez;limite_voltas;fonte só em 480p
```

