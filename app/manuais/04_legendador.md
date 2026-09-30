# Manual 04 — Legendador

> **Hypado (HP) · HP Studio · Manuais dos cargos**
> Versão 1.0 · 30/09/2026 · Situação: **rascunho para revisão** (passa a valer depois de revisado e de 7 dias em modo sombra).
> Ler junto com: **01 Curador** (escolhe o vídeo), **02 Pauteiro** (monta o `pedido.json`), **03 Editor** (queima a legenda no vídeo final), **05 Tradutor e dublador** (quando o vídeo não está em português), **06 Narrador "Toque HP"** (pergunta de abertura e de fecho) e **09 Revisor de qualidade** (dá a nota).
> Vale para os 6 perfis: **GTA 6 | HP** (@hpgta6), **Futebol | HP** (@hp.futebol), **Filmes e Séries | HP** (@hp.filmes), **Receitas | HP** (@hp.receitas), **Carros | HP** (@hp.carros) e **Destinos | HP** (@hp.destinos).

**Resumo em 5 linhas (para quem tem pressa):**
1. O Legendador pega o vídeo cru (`bruto.mp4`) que está em `H:\HypadoLocal\esteira\03_legenda_dublagem\<item>\`.
2. Transcreve a fala (o computador "escuta" e escreve o que foi dito, com o tempo de cada palavra) e grava `transcricao.json`.
3. Corrige os nomes próprios (Lucia, Jason, Arrascaeta, Jericoacoara…) com o dicionário do canal; só o que o app não tem certeza vai para o Claude olhar.
4. Quebra o texto em blocos curtos de 2 a 4 palavras, pinta a palavra falada na cor do canal, põe o crédito do criador e grava `legenda.ass` (a que vai queimada no vídeo) e `legenda.srt` (a legenda "de texto", para o YouTube e para conferência).
5. Faz uma prévia, confere os números (tempo, tamanho, zona segura) e anota tudo no `historico.log`. Aí o item segue para `04_edicao`.

**Como ler este manual:** as seções vão de 1 a 9, sempre na mesma ordem em todos os manuais da HP. Se você só vai executar, vá direto para a **seção 3 (passo a passo)**. Se vai conferir o trabalho de alguém, use a **seção 5 (notas)** e a **seção 9 (testes)**. Palavra difícil? Está no **Glossário**, no fim.

**Convenção dos marcadores usados aqui:**
- **(a criar)** = ferramenta, arquivo ou comando que ainda NÃO existe; está descrito para quem for programar a etapa 3 do app. Enquanto não existir, faça pelo caminho manual que o passo indica.
- **(existente)** = já existe e funciona no PC do Antônio; só usar, não reescrever.
- **[BLOQUEIA]** = regra inviolável; se quebrar, o item não sai, não importa a nota do resto.

---

## 1. Objetivo do cargo

### 1.1 Em uma frase
Fazer com que **qualquer pessoa entenda o vídeo inteiro com o som desligado**, lendo uma legenda **certa, no tempo exato da fala, bonita, no padrão HP e na cor do canal**, sem nunca errar nome próprio e sem nunca esquecer o crédito do criador.

### 1.2 Por que isso importa para a HP
- Grande parte das pessoas rola o Instagram, o TikTok e o Facebook **com o som desligado** (no ônibus, no trabalho, na cama do lado de alguém). Sem legenda, elas passam o vídeo em 1 segundo. Com legenda, ficam — e **tempo assistido é o que faz o algoritmo mostrar o vídeo para mais gente**, que é o que leva à monetização (objetivo nº 1 da HP).
- A legenda queimada no **estilo HP** (branca, contorno preto, a palavra falada acesa na cor do canal) é a "cara" da marca: quem vê reconhece que é da HP antes de ler o @.
- Erro de nome próprio ("Lussia" em vez de "Lucia", "Arascaeta" em vez de "Arrascaeta") gera comentário de deboche, derruba a confiança e faz o Revisor mandar o vídeo de volta — perde-se o horário de postagem.
- O crédito do criador na tela é regra da empresa **e** proteção: mostra que a HP não está se passando pelo dono do vídeo.

### 1.3 O que o Legendador FAZ
1. Transcreve a fala do `bruto.mp4` com tempo por palavra → `transcricao.json`.
2. Revisa o texto: nomes próprios, números, termos do canal, palavrões (suaviza), trechos que o computador não entendeu.
3. Decide, pela regra fixa da seção 2.12, se a legenda é **da fala original** (vídeo em português) ou **da tradução** (vídeo estrangeiro — aí ele recebe o texto pronto do Tradutor, manual 05).
4. Inclui na legenda as falas do **Toque HP** (pergunta de abertura, trecho narrado e fecho — manual 06), quando o pedido tiver.
5. Quebra o texto em blocos (2 a 4 palavras, no máximo 2 linhas, no máximo 22 caracteres por linha), com tempos mínimos e máximos.
6. Pinta a palavra falada na hora com a cor do canal (efeito "karaokê").
7. Põe a linha de crédito ("Vídeo: @criador") e, quando aparecer dinheiro, o aviso "Valores aproximados…".
8. Gera `legenda.ass` (para queimar) e `legenda.srt` (texto simples com tempos).
9. Faz uma prévia rápida, tira 3 quadros e confere tudo contra a lista da seção 9.
10. Anota cada ação no `historico.log` do item.

### 1.4 O que o Legendador NÃO FAZ (é de outro cargo)
| Não faz | Quem faz | Manual |
|---|---|---|
| Escolher o vídeo, decidir se pode usar | Curador | 01 |
| Montar o `pedido.json`, definir horário e prioridade | Pauteiro | 02 |
| Baixar e cortar o trecho (`bruto.mp4`) | App (ytdlp/cortar) | 02/03 |
| Traduzir o texto estrangeiro e dublar | Tradutor e dublador | 05 |
| Escrever e gravar a pergunta de abertura/fecho | Narrador "Toque HP" | 06 |
| Queimar a legenda no vídeo final em 1080x1920, mixar música, fazer o `final.mp4` | Editor | 03 |
| Fazer a capa | Designer | 07 |
| Escrever o texto do post (a "legenda do post", com hashtags) | Redator | 08 |
| Dar a nota final e aprovar | Revisor | 09 |

> Atenção para não confundir: na HP, **"legenda"** neste manual é **o texto que aparece em cima do vídeo**. O texto que vai embaixo do post (com hashtags) é o **"texto do post"**, feito pelo Redator (manual 08).

### 1.5 Onde o Legendador fica na esteira
```
01_pedidos → 02_baixados → [03_legenda_dublagem] → 04_edicao → 05_revisao → 06_agendados → 07_postados
                                    ▲                                            │
                                    └──────── refazer.json (volta) ◄─────────────┘
```
Dentro da etapa **03_legenda_dublagem** a ordem é sempre esta (os três cargos trabalham na mesma pasta):
1. **Legendador — parte 1:** transcrever (`transcricao.json`) e revisar nomes.
2. **Tradutor e dublador (05):** só se o vídeo não for em português → `traducao.json` e, quando permitido, `dublagem.wav`.
3. **Narrador "Toque HP" (06):** só se o pedido pedir → `toque_hp.json` e, quando permitido, `toque_hp.wav`.
4. **Legendador — parte 2:** juntar tudo (fala original ou tradução + Toque HP + crédito + aviso de valores) e gerar `legenda.ass` e `legenda.srt`.
5. O app move a pasta para `04_edicao`.

### 1.6 Quando o trabalho está pronto (definição de "pronto")
O item só sai da etapa 03 quando **todos** estes itens forem verdade:
- [ ] `transcricao.json` existe, tem `"revisado": true` e zero pendências abertas.
- [ ] `legenda.ass` e `legenda.srt` existem, abrem sem erro e têm o mesmo texto.
- [ ] Nenhuma linha passa de 22 caracteres; nenhum bloco tem mais de 2 linhas.
- [ ] Todos os blocos começam no máximo 80 ms depois do começo da primeira palavra falada (e nunca antes de 40 ms antes dela).
- [ ] A linha de crédito existe e bate com `pedido.json → fonte.criador_arroba`.
- [ ] Se aparece valor em dinheiro, o aviso "Valores aproximados…" aparece junto.
- [ ] A prévia foi gerada e os 3 quadros conferidos (fonte certa, cor certa, dentro da zona segura).
- [ ] O `historico.log` tem as linhas da etapa 03 com os números da checagem.

---

## 2. Entradas e saídas

### 2.1 A esteira de pastas (visão geral)
Tudo acontece em `H:\HypadoLocal\esteira\` (disco H:, nunca no C:). Cada vídeo é **uma pasta** que anda de uma etapa para a próxima:

```
H:\HypadoLocal\esteira\
├── 01_pedidos\            ← o Claude/Pauteiro só larga o pedido.json; o app baixa sozinho
├── 02_baixados\           ← bruto.mp4 pronto (já cortado no trecho certo)
├── 03_legenda_dublagem\   ← AQUI TRABALHAM o Legendador (04), o Tradutor (05) e o Narrador (06)
├── 04_edicao\             ← o Editor (03) monta o final.mp4 e queima a legenda
├── 05_revisao\            ← o Revisor (09) grava aprovado.json ou refazer.json
├── 06_agendados\          ← o app agenda pela API (TikTok espera tiktok_ok.json)
├── 07_postados\           ← daqui sai o aviso "no ar"
└── 99_erros\              ← o que deu errado e precisa de gente olhar
```

### 2.2 Nome da pasta do item (e a prioridade)
Formato: `<PRIORIDADE>_<AAAA-MM-DD>_<HHMM>_<canal>_<apelido-curto>`

- **Prioridade** (sempre na frente, porque o app ordena as pastas pelo nome):
  - `P0_` = **urgente / ao vivo** (gol, placar, lançamento, notícia bombástica). **Fura a fila inteira** ("faixa expressa"): se aparecer um P0 enquanto você faz um P1, termine o passo em que está, salve, e passe para o P0.
  - `P1_` = **do dia** (sai hoje no horário marcado).
  - `P2_` = **programado** (sai em outro dia; faz quando não houver P0 nem P1).
- **Data e hora** = dia e horário de postagem previstos (hora de Brasília, 24 h, sem dois-pontos).
- **Canal** = um destes 6 apelidos, sempre minúsculo: `gta`, `futebol`, `filmes`, `receitas`, `carros`, `destinos`.
- **Apelido curto** = 2 a 4 palavras sem acento, separadas por hífen.

Exemplos reais de nome (um por canal):
| Canal | Exemplo de pasta |
|---|---|
| GTA 6 \| HP | `P1_2026-09-30_1830_gta_rockstar-quinta` |
| Futebol \| HP | `P0_2026-09-30_2240_futebol_gol-arrascaeta` |
| Filmes e Séries \| HP | `P2_2026-10-02_1200_filmes_duna-bastidores` |
| Receitas \| HP | `P1_2026-09-30_1100_receitas_pao-sem-sovar` |
| Carros \| HP | `P2_2026-10-01_0900_carros_corolla-cross-teste` |
| Destinos \| HP | `P1_2026-09-30_1500_destinos_jericoacoara-por-do-sol` |

> Regra de ouro: o Legendador **nunca renomeia** a pasta do item. Quem muda prioridade é o Pauteiro (02) ou o Antônio.

### 2.3 O que tem dentro da pasta do item
| Arquivo | Quem cria | Em que etapa | O Legendador… |
|---|---|---|---|
| `pedido.json` | Pauteiro (02) | 01 | **lê** (nunca altera) |
| `bruto.mp4` | App (ytdlp/cortar) | 02 | **lê** (nunca altera) |
| `transcricao.json` | **Legendador** | 03 | **cria** |
| `traducao.json` | Tradutor (05) | 03 | lê (se existir) |
| `dublagem.wav` | Tradutor (05) | 03 | não mexe |
| `toque_hp.json` / `toque_hp.wav` | Narrador (06) | 03 | lê o `.json` (se existir) |
| `legenda.ass` | **Legendador** | 03 | **cria** |
| `legenda.srt` | **Legendador** | 03 | **cria** |
| `checagem_legenda.json` | **Legendador** (app) | 03 | **cria** (a criar no app) |
| `previa_legenda.mp4` | **Legendador** | 03 | **cria** (apagada depois da revisão) |
| `quadros\` (3 imagens .jpg) | **Legendador** | 03 | **cria** |
| `final.mp4` | Editor (03) | 04 | não mexe |
| `capa.jpg` | Designer (07) | 04 | não mexe |
| `post.json` | Redator (08) / Publicador (10) | 04–06 | não mexe |
| `aprovado.json` / `refazer.json` | Revisor (09) | 05 | lê o `refazer.json` quando o item volta |
| `historico.log` | todos | todas | **acrescenta linhas** (nunca apaga) |

### 2.4 Entrada principal: `pedido.json` (exemplo completo)
O `pedido.json` é definido pelo **manual 02 (Pauteiro)** — se houver diferença, o manual 02 manda. Abaixo, um exemplo completo do GTA, com os campos que o Legendador usa marcados na tabela logo depois.

```json
{
  "versao": 1,
  "id": "P1_2026-09-30_1830_gta_rockstar-quinta",
  "prioridade": "P1",
  "criado_em": "2026-09-30T14:05:12-03:00",
  "criado_por": "pauteiro",
  "canal": "gta",
  "conta": "@hpgta6",
  "tipo": "reel",
  "origem": "criador",
  "titulo_interno": "Rockstar mostra Vice City à noite",
  "fonte": {
    "url": "https://www.youtube.com/watch?v=EXEMPLO0001",
    "plataforma": "youtube",
    "criador_nome": "Rockstar Games",
    "criador_arroba": "@rockstargames",
    "oficial": true,
    "trecho": {"inicio": "00:00:12.000", "fim": "00:00:41.500"}
  },
  "idioma_origem": "en",
  "audio": {
    "tratamento": "legenda_traduzida",
    "manter_audio_original": true,
    "voz_sintetica_permitida": false
  },
  "legenda": {
    "queimar": true,
    "gerar_srt": true,
    "estilo": "hp_padrao",
    "posicao": "baixo"
  },
  "toque_hp": {"usar": true, "modo": "texto"},
  "valores_citados": false,
  "publicar_em": "2026-09-30T18:30:00-03:00",
  "redes": ["instagram", "facebook", "tiktok", "youtube", "threads"],
  "observacoes": "Só material oficial da Rockstar. Nada de vazamento. Não é trailer puro: tem Toque HP e legenda."
}
```

Campos que o Legendador usa:
| Campo | Para quê | Valores possíveis | Exemplo |
|---|---|---|---|
| `id` | Conferir que o pedido é desta pasta | igual ao nome da pasta | `P1_2026-09-30_1830_gta_rockstar-quinta` |
| `canal` | Escolher cor, dicionário de nomes, regras do canal | `gta`, `futebol`, `filmes`, `receitas`, `carros`, `destinos` | `gta` |
| `tipo` | Estáticos (carrossel, story de arte, texto do Threads) **não têm legenda**: pular | `reel`, `video`, `carrossel`, `story`, `threads` | `reel` |
| `fonte.criador_arroba` | Texto do crédito na tela | um @ | `@rockstargames` |
| `fonte.criador_nome` | Crédito quando não há @ (ex.: canal do YouTube sem @) | texto | `Rockstar Games` |
| `idioma_origem` | Idioma para a transcrição; se não for `pt`, chama o Tradutor | `pt`, `en`, `es`, `it`, `fr`, `ja`… | `en` |
| `audio.tratamento` | Diz se a legenda é da fala original, da tradução ou da dublagem | `original`, `legenda_traduzida`, `dublagem`, `sem_fala` | `legenda_traduzida` |
| `legenda.queimar` | Se `false`, só gera o SRT (raro: vídeo que já vem legendado pelo criador) | `true`/`false` | `true` |
| `legenda.posicao` | Onde a legenda fica | `baixo` (padrão), `meio`, `alto` | `baixo` |
| `toque_hp.usar` / `modo` | Se entra texto do Toque HP na legenda | `usar`: `true`/`false`; `modo`: `voz`, `texto` | `true` / `texto` |
| `valores_citados` | Se há preço/valor no vídeo → aviso "Valores aproximados…" | `true`/`false` | `false` |
| `publicar_em` | Saber quanto tempo resta (prazo) | data ISO | `2026-09-30T18:30:00-03:00` |

> Se `valores_citados` estiver `false` mas você **ouvir** um valor em dinheiro no vídeo, trate como `true` (ponha o aviso) e anote no `historico.log`: `legendador: valor citado encontrado sem marcação no pedido — aviso incluído`.

### 2.5 Saída 1: `transcricao.json` (exemplo completo)
Tempo sempre **em segundos, com 3 casas decimais**, contado a partir do início do `bruto.mp4` (o segundo 0 é o primeiro quadro do bruto).

```json
{
  "versao": 1,
  "item": "P1_2026-09-30_1830_gta_rockstar-quinta",
  "arquivo_fonte": "bruto.mp4",
  "duracao_s": 29.500,
  "idioma_pedido": "en",
  "idioma_detectado": "en",
  "prob_idioma": 0.98,
  "motor": "faster-whisper",
  "modelo": "small",
  "calculo": "int8",
  "criado_em": "2026-09-30T14:21:03-03:00",
  "confianca_media": 0.91,
  "revisado": true,
  "revisado_por": ["app:dicionario_gta", "claude:pendencias"],
  "segmentos": [
    {
      "id": 1,
      "inicio": 0.412,
      "fim": 2.980,
      "texto": "Welcome back to Vice City.",
      "palavras": [
        {"p": "Welcome", "inicio": 0.412, "fim": 0.780, "conf": 0.97},
        {"p": "back",    "inicio": 0.780, "fim": 1.020, "conf": 0.99},
        {"p": "to",      "inicio": 1.020, "fim": 1.140, "conf": 0.99},
        {"p": "Vice",    "inicio": 1.140, "fim": 1.620, "conf": 0.88},
        {"p": "City.",   "inicio": 1.620, "fim": 2.980, "conf": 0.93}
      ]
    },
    {
      "id": 2,
      "inicio": 3.410,
      "fim": 5.870,
      "texto": "Lucia knows every street in Leonida.",
      "palavras": [
        {"p": "Lucia",   "inicio": 3.410, "fim": 3.900, "conf": 0.71},
        {"p": "knows",   "inicio": 3.900, "fim": 4.180, "conf": 0.98},
        {"p": "every",   "inicio": 4.180, "fim": 4.470, "conf": 0.99},
        {"p": "street",  "inicio": 4.470, "fim": 4.860, "conf": 0.97},
        {"p": "in",      "inicio": 4.860, "fim": 4.990, "conf": 0.99},
        {"p": "Leonida.", "inicio": 4.990, "fim": 5.870, "conf": 0.64}
      ]
    }
  ],
  "correcoes": [
    {"segmento": 2, "de": "Lusia", "para": "Lucia", "por": "app:dicionario_gta"},
    {"segmento": 2, "de": "Leonidas", "para": "Leonida", "por": "claude:pendencias"}
  ],
  "pendencias": [],
  "trechos_sem_fala": [{"inicio": 0.000, "fim": 0.412}, {"inicio": 5.870, "fim": 29.500}],
  "observacoes": "Depois de 5,87 s só tem música e efeitos: sem legenda de fala nesse trecho (entra só crédito e Toque HP)."
}
```

Campos explicados:
| Campo | O que é | Regra |
|---|---|---|
| `idioma_detectado` / `prob_idioma` | O idioma que o computador achou e a certeza (0 a 1) | Se diferente de `idioma_pedido` e `prob_idioma` ≥ 0,80 → vale o detectado e avisa no histórico |
| `confianca_media` | Média da certeza de todas as palavras | Abaixo de 0,75 → áudio ruim: mais pendências, olhar com calma |
| `palavras[].conf` | Certeza de cada palavra (0 a 1) | Abaixo de 0,60 vira **pendência**, a não ser que o dicionário resolva |
| `revisado` | Se já passou pela revisão de nomes e pendências | Só vira `true` com `pendencias` vazia |
| `correcoes` | Tudo o que foi trocado, de quê para quê e por quem | Serve para o app aprender (vira entrada nova no dicionário) |
| `trechos_sem_fala` | Onde não tem voz (música, efeito, silêncio) | Nesses trechos, legenda de fala não aparece |

### 2.6 Saída 2: `legenda.srt` (exemplo completo)
O SRT é a legenda **"de frase"**: frases inteiras, no máximo 2 linhas de até 42 caracteres, cada uma entre 1,0 s e 6,0 s na tela. Serve para: subir como legenda (closed caption) no YouTube, para o `qa_paridade` (a criar) comparar texto e tempo, e como registro. **O texto é exatamente o mesmo da legenda queimada** (só a quebra é diferente).

Exemplo do mesmo vídeo do GTA (a legenda sai em português, porque o vídeo é estrangeiro e o tratamento é `legenda_traduzida`):
```
1
00:00:00,000 --> 00:00:01,900
Você reconheceria essa cidade à noite?

2
00:00:00,412 --> 00:00:02,980
Bem-vindo de volta a Vice City.

3
00:00:03,410 --> 00:00:05,870
A Lucia conhece cada rua de Leonida.

4
00:00:26,600 --> 00:00:29,500
Vai jogar em 19/11? Comenta aí.
```
Regras do SRT:
- Numeração começa em 1 e vai de 1 em 1, sem pular.
- Tempo no formato `HH:MM:SS,mmm` (com **vírgula** antes dos milésimos — no ASS é ponto).
- Uma linha em branco entre um bloco e outro; o arquivo termina com uma linha em branco.
- Codificação **UTF-8** (senão "ç" e "ã" viram símbolos estranhos).
- O bloco 1 acima é a pergunta do Toque HP em modo texto (manual 06); no GTA ela não tem voz, só aparece escrita — por isso ela pode ficar por cima do começo da fala (bloco 2): na tela ela usa o estilo `Pergunta`, lá em cima.

### 2.7 Saída 3: `legenda.ass` (exemplo completo)
O ASS é a legenda **"de reels"**: é ela que o Editor (manual 03) queima no vídeo. Tem estilos (fonte, cor, tamanho, posição) e um "evento" (linha `Dialogue`) para cada bloco que aparece na tela. Tempo no formato `H:MM:SS.cc` (com **ponto** e **centésimos** de segundo: `0:00:03.41` = 3 segundos e 41 centésimos).

Exemplo completo — o mesmo vídeo do GTA (legenda traduzida; por ser tradução, **não tem karaokê**: a palavra-chave de cada bloco fica fixa na cor do canal, veja 2.12):
```
[Script Info]
; HP Studio - Legendador (manual 04) - item P1_2026-09-30_1830_gta_rockstar-quinta
Title: P1_2026-09-30_1830_gta_rockstar-quinta
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: HP,Montserrat ExtraBold,72,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,2,2,80,160,560,1
Style: Pergunta,Montserrat ExtraBold,72,&H00FFFFFF,&H00FFFFFF,&H00882EFF,&H00000000,-1,0,0,0,100,100,0,0,3,18,0,8,80,160,330,1
Style: Credito,Montserrat SemiBold,40,&H26FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,3,1,7,80,160,240,1
Style: Aviso,Montserrat SemiBold,38,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,3,1,2,80,160,490,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 2,0:00:00.00,0:00:29.50,Credito,,0,0,0,,Vídeo: @rockstargames
Dialogue: 1,0:00:00.00,0:00:01.90,Pergunta,,0,0,0,,Você reconheceria\Nessa cidade à noite?
Dialogue: 0,0:00:00.41,0:00:02.01,HP,,0,0,0,,Bem-vindo de volta
Dialogue: 0,0:00:02.01,0:00:02.98,HP,,0,0,0,,a {\c&H00882EFF&}Vice City{\r}
Dialogue: 0,0:00:03.41,0:00:04.50,HP,,0,0,0,,A {\c&H00882EFF&}Lucia{\r} conhece
Dialogue: 0,0:00:04.50,0:00:05.87,HP,,0,0,0,,cada rua de {\c&H00882EFF&}Leonida{\r}
Dialogue: 1,0:00:26.60,0:00:29.50,Pergunta,,0,0,0,,Vai jogar em 19/11?\NComenta aí
```

Como ler uma linha `Dialogue` (para leigo):
| Pedaço | Significa | No exemplo |
|---|---|---|
| `Dialogue: 0,` | "Camada" 0 (o que tem número maior fica por cima) | legenda normal = 0, pergunta = 1, crédito = 2 |
| `0:00:03.41,0:00:04.50,` | Aparece em 3,41 s e some em 4,50 s | — |
| `HP,` | Nome do estilo (fonte, cor, posição) | `HP`, `Pergunta`, `Credito`, `Aviso` |
| `,0,0,0,,` | Margens próprias (0 = usa as do estilo) e efeito (vazio) | sempre assim |
| `{\c&H00882EFF&}Lucia{\r}` | Pinta "Lucia" na cor do canal e depois volta ao normal | `\c` = cor; `\r` = volta ao estilo |
| `\N` | Quebra de linha forçada | "Você reconheceria\Nessa cidade à noite?" |

**Karaokê (vídeo em português ou dublado): um evento por palavra.** Quando a fala é em português (ou é a voz da dublagem em português), cada palavra acende na cor do canal **no instante em que é falada**. O app faz isso gerando um evento para cada palavra, todos com o bloco inteiro, mudando só qual palavra está pintada. Exemplo do Receitas (cor laranja `&H00008AFF&`), bloco "Mistura a farinha" falado entre 1,20 s e 2,10 s:
```
Dialogue: 0,0:00:01.20,0:00:01.64,HP,,0,0,0,,{\c&H00008AFF&}Mistura a{\r} farinha
Dialogue: 0,0:00:01.64,0:00:02.10,HP,,0,0,0,,Mistura a {\c&H00008AFF&}farinha{\r}
```
Repare: a palavra "a" durou menos de 120 ms, então ela **acende junto** com "Mistura" (regra da seção 2.12, para não piscar).

### 2.8 Saída 4: `checagem_legenda.json` (a criar no app)
Relatório automático que o app grava depois de gerar a legenda. É o que o Revisor (09) e o `qa_paridade` (a criar) leem primeiro, sem precisar abrir o vídeo.
```json
{
  "versao": 1,
  "item": "P1_2026-09-30_1830_gta_rockstar-quinta",
  "criado_em": "2026-09-30T14:32:40-03:00",
  "modo": "legenda_traduzida",
  "canal": "gta",
  "cor_canal": "#FF2E88",
  "blocos": 4,
  "blocos_toque_hp": 2,
  "max_caracteres_linha": 19,
  "max_linhas_bloco": 2,
  "max_largura_px": 742,
  "limite_largura_px": 840,
  "cps_max": 14.8,
  "duracao_min_bloco_s": 0.97,
  "duracao_max_bloco_s": 1.60,
  "desvio_inicio_ms": {"medio": 12, "maximo": 38, "limite": 80},
  "blocos_antes_da_fala_ms_max": 0,
  "sobreposicoes_fala": 0,
  "buracos_curtos": 0,
  "fora_zona_segura": 0,
  "fonte_pedida": "Montserrat ExtraBold",
  "fonte_usada": "Montserrat ExtraBold",
  "credito": {"texto": "Vídeo: @rockstargames", "confere_pedido": true, "tempo_na_tela_s": 29.5},
  "aviso_valores": {"necessario": false, "presente": false},
  "nomes": {"do_dicionario": 3, "corrigidos": 2, "pendentes": 0},
  "texto_srt_igual_ass": true,
  "notas_previas": {"L1_texto": 10, "L2_nomes": 10, "L3_sincronia": 10, "L4_quebra": 10, "L5_leitura": 10, "L6_estilo": 10, "L7_zona": 10, "L8_credito": 10, "L9_valores": 10, "L10_toque": 10, "L11_arquivos": 10},
  "resultado": "ok",
  "problemas": []
}
```
Se `resultado` for `"falhou"`, a lista `problemas` diz o quê, por exemplo: `["bloco 7: linha com 26 caracteres (máx. 22)", "bloco 12 começa 140 ms depois da fala (máx. 80)"]`.

### 2.9 O `historico.log` (o diário do item)
Cada linha começa com a data e hora (o app põe sozinho, pela função `anexar_linha` do `hpbase`), depois `[03]` (a etapa) e o cargo. **Nunca apague linhas** — só acrescente. Exemplo do que o Legendador deixa:
```
2026-09-30T14:18:40-03:00 [03] legendador: início (P1, prazo 18:30, restam 4h11)
2026-09-30T14:18:41-03:00 [03] legendador: trava pesada pega (dono=esteira:legendar)
2026-09-30T14:21:03-03:00 [03] legendador: transcrição ok (faster-whisper small int8, idioma en 0,98, 11 palavras, conf. média 0,91, 142 s de processamento)
2026-09-30T14:21:04-03:00 [03] legendador: dicionário gta aplicou 1 correção (Lusia→Lucia); 1 pendência (Leonidas?)
2026-09-30T14:24:10-03:00 [03] legendador: pendência resolvida pelo Claude (Leonidas→Leonida)
2026-09-30T14:24:11-03:00 [03] legendador: aguardando traducao.json (tradutor, manual 05)
2026-09-30T14:29:55-03:00 [03] legendador: traducao.json recebida (3 segmentos)
2026-09-30T14:30:02-03:00 [03] legendador: toque_hp.json recebido (modo texto, 2 falas)
2026-09-30T14:32:40-03:00 [03] legendador: legenda.ass e legenda.srt gerados (4 blocos + 2 do Toque HP; máx. 19 caracteres/linha; desvio máx. 38 ms)
2026-09-30T14:34:15-03:00 [03] legendador: prévia e 3 quadros conferidos (fonte ok, zona segura ok, crédito ok)
2026-09-30T14:34:16-03:00 [03] legendador: fim; trava solta; pronto para 04_edicao
```

### 2.10 Entrada de volta: `refazer.json` (quando o Revisor devolve)
Quando o Revisor (manual 09) dá nota "Médio" e o critério de menor nota é de legenda, a pasta volta para `03_legenda_dublagem` com um `refazer.json`. Exemplo:
```json
{
  "versao": 1,
  "item": "P0_2026-09-30_2240_futebol_gol-arrascaeta",
  "revisor": "claude",
  "criado_em": "2026-09-30T22:51:10-03:00",
  "volta_numero": 1,
  "max_voltas": 2,
  "media": 6.4,
  "etapa_destino": "03_legenda_dublagem",
  "criterio_menor_nota": "L2_nomes",
  "nota_criterio": 0,
  "motivo": "Na legenda está 'Arascaeta' (bloco 3, 00:04,2). O certo é 'Arrascaeta'.",
  "quadros": ["quadros/q1_00s.jpg", "quadros/q2_meio.jpg", "quadros/q3_fim.jpg"],
  "o_que_fazer": "Corrigir o nome, regravar legenda.ass/.srt e acrescentar a variação errada no dicionário do futebol."
}
```
Regras da volta:
- Leia o `motivo` e corrija **só** o que foi apontado (e o que for consequência direta dele). Não refaça tudo "por garantia": isso gasta tempo e pode criar erro novo.
- Anote no `historico.log`: `legendador: volta 1 — corrigido L2_nomes (Arascaeta→Arrascaeta); dicionário atualizado`.
- **Não apague** o `refazer.json`: renomeie para `refazer_1_feito.json` (na segunda volta, `refazer_2_feito.json`). Assim o Revisor sabe que é a segunda passada.
- Se já é a **volta 2** e o problema continua, não tente a terceira: mova para `99_erros` e avise (seção 6).

### 2.11 Arquivos de apoio (ficam fora da pasta do item)
| Arquivo | Onde | Para quê | Situação |
|---|---|---|---|
| Dicionário de nomes por canal | `G:\Meu Drive\Hypado\06 Projeto\app\dicionarios\nomes_<canal>.txt` | Trocar automaticamente os erros comuns de nome próprio | (a criar) |
| Palavras para "dica" da transcrição | mesmo arquivo (a primeira coluna) | O motor de transcrição recebe a lista de nomes do canal como dica | (a criar) |
| Estilos por canal | `G:\Meu Drive\Hypado\06 Projeto\app\config\estilos_legenda.json` | Cor, fonte, tamanhos e margens em um só lugar | (a criar) |
| Lista de palavrões e trocas | `G:\Meu Drive\Hypado\06 Projeto\app\dicionarios\suavizar.txt` | Palavrão na tela vira versão com asterisco | (a criar) |
| Modelos de transcrição | `H:\HypadoLocal\modelos\whisper\` | Os "cérebros" do faster-whisper, baixados uma vez | (a criar a pasta) |
| Fontes | `H:\HypadoLocal\ferramentas\fontes\` + instaladas no Windows | Montserrat ExtraBold e SemiBold | (a instalar, se faltar) |

Formato do dicionário de nomes (um nome por linha; à esquerda o jeito certo, à direita, separados por `;`, os jeitos errados que o computador costuma escrever; `#` = comentário):
```
# nomes_gta.txt — forma certa | erros comuns
GTA 6 | GTA VI; GTA seis; GTA Six; gê tê á seis
Lucia | Lúcia; Lussia; Lusia; Lucía; Lutia
Jason | Jayson; Jeison; Jasão; Jeisson
Leonida | Leônida; Leonidas; Leonída; Leônidas
Vice City | Vais City; Vice Siti; Vicecity; Vaice City
Rockstar Games | Rock Star; Rockstar Gamers; Roquestar
Take-Two | Take Two; Teique Tu; Take 2
Port Gellhorn | Port Gelhorn; Porto Gellhorn
Grassrivers | Grass Rivers; Grasrivers
Leonida Keys | Leonida Kiss; Leonida Quis
```
Exemplos de linhas dos outros canais:
```
# nomes_futebol.txt
Arrascaeta | Arascaeta; Arrasqueta; Arrascaéta
Vini Jr. | Vinícius Júnior; Vini Júnior; Vinicius Jr; Vini Junior
Estêvão | Estevão; Estevam
Endrick | Endric; Hendrick; Endrik
Carlo Ancelotti | Ancelote; Ancheloti; Anceloti
Abel Ferreira | Abel Ferrera
Libertadores | Libertadoris; Liberta Dores
Brasileirão | Brasileirao; Brasilerão

# nomes_filmes.txt
Timothée Chalamet | Timothy Chalamet; Timoti Chalamê; Timothee Chalamet
Denis Villeneuve | Dênis Vilnev; Denis Vilneuve
Wagner Moura | Vagner Moura
Fernanda Torres | Fernanda Tores
Ainda Estou Aqui | Ainda Tô Aqui
Pedro Pascal | Pedro Pascoal

# nomes_receitas.txt
muçarela | mussarela; mozarela; muzarela
shoyu | xoiú; shoyo; shoio
páprica | paprica; pápica
ciabatta | chabata; ciabata
air fryer | airfryer; ér fraier; air frier

# nomes_carros.txt
Porsche | Porche; Porshe; Pórche
BYD | Biwaidi; B Y D; Baidi
Volkswagen | Volks Wagen; Volksvagen
Corolla Cross | Corola Cross; Corolla Cros
cv | CV; c.v.; cavalos-vapor (quando for a unidade)

# nomes_destinos.txt
Jericoacoara | Jericuacoara; Jeri Coacoara; Jericoaquara
Lençóis Maranhenses | Lençóis Maranhense; Lençois Maranhenses
Fernando de Noronha | Fernando de Noronia
Machu Picchu | Machu Pichu; Machupicchu; Machu Pitchu
Capadócia | Cappadocia; Capadocia
```

Exemplo de `estilos_legenda.json` (a criar) — o app lê daqui em vez de ter cor escrita no código:
```json
{
  "versao": 1,
  "fonte_texto": "Montserrat ExtraBold",
  "fonte_apoio": "Montserrat SemiBold",
  "tamanho_texto": 72,
  "tamanho_pergunta": 72,
  "tamanho_credito": 40,
  "tamanho_aviso": 38,
  "contorno": 6,
  "sombra": 2,
  "max_caracteres_linha": 22,
  "max_linhas": 2,
  "max_largura_px": 840,
  "margens": {"esquerda": 80, "direita": 160, "baixo": 560, "alto": 420, "credito_topo": 240, "aviso_baixo": 490},
  "zona_segura": {"topo": 220, "base": 480, "esquerda": 80, "direita": 160},
  "canais": {
    "gta":      {"cor": "#FF2E88", "ass": "&H00882EFF"},
    "futebol":  {"cor": "#00D26A", "ass": "&H006AD200"},
    "filmes":   {"cor": "#FFC83D", "ass": "&H003DC8FF"},
    "receitas": {"cor": "#FF8A00", "ass": "&H00008AFF"},
    "carros":   {"cor": "#1E90FF", "ass": "&H00FF901E"},
    "destinos": {"cor": "#00C2D1", "ass": "&H00D1C200"}
  }
}
```

### 2.12 O padrão HP de legenda (a especificação completa)
Esta tabela é **a** regra. Quem programar o app usa estes números; quem revisar confere estes números.

| Item | Padrão HP | Por quê |
|---|---|---|
| Tamanho do vídeo de referência | 1080 x 1920 (vertical 9:16), `PlayResX: 1080`, `PlayResY: 1920` | É o tamanho de Reels, TikTok e Shorts |
| Fonte do texto | **Montserrat ExtraBold** (grátis, Google Fonts). Se não estiver instalada, **pare e instale** (passo 6) — não aceite troca silenciosa | Letra grossa lê bem em tela pequena |
| Tamanho do texto | 72 px (no vídeo 1080x1920) | Lê no celular sem ocupar a tela toda |
| Cor do texto | Branco `#FFFFFF` | Contraste com qualquer fundo |
| Contorno | Preto, 6 px; sombra 2 px preta a 50% | Lê até em fundo branco (neve, prato, céu) |
| Cor de destaque | A cor do canal (tabela abaixo) | Identidade de cada perfil |
| Palavras por bloco | **2 a 4** (nunca 1 sozinha, a não ser palavra final de frase ou exclamação: "Golaço!") | Leitura em "tiros" rápidos, ritmo de reels |
| Caracteres por linha | **Máximo 22** (contando espaços) **e** no máximo 840 px de largura medida (medido com a Montserrat ExtraBold 72: "cada rua de Leonida" = 777 px; "fogem pela Vice City" = 794 px; "Mistura a farinha com" = 835 px — no limite) | Cabe entre as margens com a fonte 72; letras largas (m, W) estouram antes dos 22, por isso vale a medida em px |
| Linhas por bloco | **Máximo 2**; o normal é 1 | Mais que isso tapa o vídeo |
| Pirâmide | Com 2 linhas, a de baixo igual ou maior que a de cima, quando der | Leitura mais natural |
| Tempo mínimo na tela | 0,50 s por bloco (exceção: última palavra de frase muito rápida, 0,35 s) | Dá tempo de ler |
| Tempo máximo na tela | 3,0 s por bloco; depois disso, some mesmo que a pessoa ainda esteja na mesma palavra | Legenda parada parece travada |
| Velocidade de leitura (CPS) | Máximo **17 caracteres por segundo** por bloco | Acima disso ninguém acompanha |
| Início do bloco | **Entre 40 ms antes e 80 ms depois** do início da 1ª palavra do bloco | "Sincronia": texto e boca juntos |
| Fim do bloco | Fim da última palavra + 0,25 s de "rabo", ou o início do próximo bloco (o que vier primeiro) | Não some antes de terminar de ler |
| Buraco entre blocos | Se o intervalo for menor que 0,30 s, o bloco anterior "estica" até o próximo (sem piscar tela vazia) | Evita pisca-pisca |
| Sobreposição | Dois blocos de fala **nunca** ao mesmo tempo no estilo `HP` | Confunde |
| Karaokê (palavra ativa) | Só quando a fala da legenda está em **português** (original ou dublagem). Palavra com menos de 120 ms acende junto com a vizinha | A pessoa "lê junto" |
| Legenda traduzida (vídeo estrangeiro sem dublagem) | **Sem karaokê**; a palavra-chave do bloco (nome, número, lugar) fica fixa na cor do canal | O tempo das palavras em português não bate com a boca em inglês |
| Caixa (maiúsculas) | Frase normal: maiúscula só no início da frase e em nome próprio. **Não** usar tudo em caixa alta | Caixa alta cansa e esconde nome próprio |
| Pontuação | Sem ponto final no fim do bloco; mantém `?`, `!` e `…`; vírgula no fim do bloco pode sair | Visual limpo |
| Números | Em algarismo: "3 gols", "200 km/h", "R$ 50 mil", "19/11". Nunca "três gols" na tela | Lê mais rápido |
| Emojis | **Nunca** dentro da legenda queimada | O motor de legenda não desenha emoji colorido; vira quadrado |
| Palavrão | Suavizado com asterisco na tela: "p*rra", "c*ralho" | Proteção da marca e da monetização |
| Posição padrão (`baixo`) | Centro, 560 px acima da borda de baixo (`MarginV 560`, `Alignment 2`) | Fica acima do texto do post e dos botões |
| Posição `meio` | Centro da tela (`Alignment 5`) | Quando embaixo tem algo importante (placar, ingrediente escrito) |
| Posição `alto` | Topo, 420 px abaixo da borda de cima (`Alignment 8`) | Quando embaixo e meio estão ocupados |
| Zona segura | Nada escrito nos 220 px de cima, nos 480 px de baixo, nos 80 px da esquerda e nos 160 px da direita | Ali ficam os botões e textos do aplicativo |
| Crédito | "Vídeo: @criador", Montserrat SemiBold 40 px, branco 85%, canto de cima à esquerda, 240 px do topo, **do começo ao fim do vídeo** | Regra da empresa: crédito sempre |
| Aviso de valores | "Valores aproximados…", Montserrat SemiBold 38 px, logo abaixo da legenda, durante todo bloco que tem valor e mais 2 s | Regra da empresa |
| Pergunta do Toque HP | Estilo `Pergunta`: 72 px, texto branco numa caixa da cor do canal, topo (330 px); **no máximo 20 caracteres por linha** (a caixa soma 18 px de cada lado) | Destaca o gancho (manual 06) |
| Codificação | UTF-8 | Acentos certos |

**Cores por canal** (a cor oficial de cada canal é a que está em `scripts\posts_canais.py`/`scripts\estaticos.py`; se forem diferentes destas, **vale a do script** e esta tabela e o `estilos_legenda.json` devem ser corrigidos no mesmo dia):
| Canal | Cor (como se escreve normalmente) | Cor no ASS (`&H00` + azul + verde + vermelho) | Nome |
|---|---|---|---|
| GTA 6 \| HP | `#FF2E88` | `&H00882EFF` | rosa neon |
| Futebol \| HP | `#00D26A` | `&H006AD200` | verde gramado |
| Filmes e Séries \| HP | `#FFC83D` | `&H003DC8FF` | amarelo pipoca |
| Receitas \| HP | `#FF8A00` | `&H00008AFF` | laranja |
| Carros \| HP | `#1E90FF` | `&H00FF901E` | azul elétrico |
| Destinos \| HP | `#00C2D1` | `&H00D1C200` | turquesa |

> **Como converter uma cor para o ASS (para leigo):** a cor normal `#RRGGBB` tem 3 pares: vermelho (RR), verde (GG), azul (BB). O ASS escreve **ao contrário** — azul, verde, vermelho — e põe `&H00` na frente (o `00` é "sem transparência"). Exemplo: `#FF2E88` → pares `FF`, `2E`, `88` → invertido `88 2E FF` → `&H00882EFF`. Errar essa ordem é o erro nº 1 de cor (o rosa vira azul).

**Regras de quebra (onde pode e onde não pode cortar a frase):**
- **Não separe** artigo do nome: ~~"o \| carro"~~ → "o carro".
- **Não separe** preposição do que vem depois: ~~"de \| São Paulo"~~ → "de São Paulo".
- **Não separe** número da unidade: ~~"200 \| km/h"~~, ~~"R$ \| 50 mil"~~, ~~"3 \| gols"~~.
- **Não separe** nome e sobrenome ou nome composto: ~~"Vini \| Jr."~~, ~~"Vice \| City"~~, ~~"Fernando de \| Noronha"~~.
- **Não termine bloco** com: `e`, `de`, `do`, `da`, `que`, `o`, `a`, `os`, `as`, `um`, `uma`, `no`, `na`, `com`, `pra`, `por`, `em`, `se`, `mas`.
- **Prefira** cortar depois de pontuação (vírgula, ponto, interrogação) ou antes de "e", "mas", "porque", "que".
- Se não houver jeito de cumprir tudo, a ordem de prioridade é: (1) não passar de 22 caracteres; (2) não separar número da unidade e nome próprio; (3) tempo mínimo; (4) o resto.

### 2.13 Como fica em cada canal (exemplos concretos)
| Canal | Vídeo típico | Tratamento de áudio | Particularidades da legenda | Exemplo de blocos |
|---|---|---|---|---|
| **GTA 6 \| HP** | Material oficial da Rockstar (inglês), vídeo de criador brasileiro comentando | Estrangeiro → `legenda_traduzida` (nunca dublagem: GTA não está na lista da voz sintética). Criador brasileiro → `original` com karaokê | Sempre "GTA 6" (nunca "GTA VI" na legenda); nomes oficiais apenas (Lucia, Jason, Vice City, Leonida); **nada** que venha de vazamento — se o áudio citar algo vazado, o item para e volta ao Curador | "Bem-vindo de volta" / "a **Vice City**" / "A **Lucia** conhece" |
| **Futebol \| HP** | Vídeo oficial do clube/CBF/liga (gol, bastidor, entrevista) | **Sempre áudio original**, legenda da fala (ou traduzida se for clube estrangeiro). **Nunca** voz sintética | A legenda não pode tapar o placar nem o escudo: se o placar estiver embaixo, use `meio`. No modo "gol" do `reel_futebol.py` (a criar) a caixa vem do `posts_futebol.py legenda_video` (existente) — a legenda de fala fica acima dela | "Que **golaço**" / "do **Arrascaeta**!" / "**3 gols**" / "em **20 minutos**" |
| **Filmes e Séries \| HP** | Trailer oficial legendável, bastidor, entrevista, vídeo próprio de curiosidades | Estrangeiro → legenda traduzida; vídeo próprio → pode ter dublagem (manual 05) e aí tem karaokê | Título **como saiu no Brasil** ("Divertida Mente 2", não "Inside Out 2"); nomes de personagem como na versão brasileira | "O detalhe" / "que ninguém viu" / "em **Duna: Parte Dois**" |
| **Receitas \| HP** | Criador cozinhando (pt ou estrangeiro), vídeo próprio | pt → karaokê; estrangeiro → legenda traduzida ou dublagem se vídeo próprio | Medidas brasileiras ("1 xícara", "180 °C"); ingrediente escrito pelo criador na tela → legenda vai para `meio` ou `alto` | "Mistura a **farinha**" / "com **300 ml**" / "de água morna" |
| **Carros \| HP** | Review, teste de aceleração, lançamento | pt → karaokê; estrangeiro → legenda traduzida ou dublagem se vídeo próprio | Unidades brasileiras (km/h, cv, km/l); **valor → aviso "Valores aproximados…"** | "De **0 a 96 km/h**" / "em **3,2 segundos**" / + aviso se citar preço |
| **Destinos \| HP** | Paisagem com narração, vídeo próprio | Vídeo próprio → dublagem permitida (manual 05) ou legenda | Nomes de lugares com acento certo; valores de ingresso/diária → aviso "Valores aproximados…" | "O pôr do sol" / "mais famoso" / "de **Jericoacoara**" |

---

## 3. Passo a passo numerado (para leigo)

> **Como usar esta seção:** faça os passos na ordem. Cada passo diz **o que abrir**, **o que clicar ou rodar**, **o que conferir** e **o que deve aparecer**. Onde houver um bloco cinza com comando, copie a linha inteira, cole no PowerShell (botão direito do mouse cola) e aperte **Enter**.
> Os passos 1 a 10 (Fase A) são feitos **uma vez só** (ou quando trocar de PC). Do dia a dia em diante, comece no passo 11.
> Quando o módulo do app da etapa 3 existir (a criar), ele fará sozinho quase todos os passos marcados com **[APP]**; os marcados com **[CLAUDE]** continuam sendo julgamento. Até lá, quem executa segue os mesmos passos à mão.

### Fase A — Preparar o PC (uma vez só)

**Passo 1 — Abrir o PowerShell.**
- Abrir: menu Iniciar (tecla Windows) → digitar `PowerShell` → clicar em **Windows PowerShell** (não precisa "Executar como administrador").
- Deve aparecer: uma janela azul com algo como `PS C:\Users\antonio>`.
- Conferir: se a janela for preta com "Prompt de Comando", você abriu o programa errado; feche e repita.

**Passo 2 — Criar os atalhos da sessão.** Copie e cole as 5 linhas (elas valem só enquanto esta janela estiver aberta; toda vez que abrir o PowerShell de novo, cole outra vez):
```powershell
$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
$ff = "H:\HypadoLocal\ferramentas\ffmpeg\bin\ffmpeg.exe"
$scripts = "G:\Meu Drive\Hypado\scripts"
$esteira = "H:\HypadoLocal\esteira"
$prov = "H:\HypadoLocal\app\provisorio"
```
- Conferir: rode `Test-Path $py; Test-Path $ff; Test-Path $scripts; Test-Path $esteira`
- Deve aparecer: quatro linhas `True`.
- Se a 2ª linha der `False` (ffmpeg em outro lugar), rode `(Get-Command ffmpeg -ErrorAction SilentlyContinue).Source`; se aparecer um caminho, use-o: `$ff = "<caminho que apareceu>"`. Se não aparecer nada, pare e abra um ticket (passo 63).

**Passo 3 — Conferir o Python.**
```powershell
& $py --version
```
- Deve aparecer: `Python 3.12.` e um número (ex.: `Python 3.12.6`).
- Se aparecer erro vermelho "não é reconhecido", o caminho do Python mudou: pare e avise.

**Passo 4 — Conferir se o ffmpeg sabe queimar legenda e medir volume.**
```powershell
& $ff -hide_banner -filters | Select-String " ass | loudnorm | ebur128 "
```
- Deve aparecer: 3 linhas, uma com `ass ... Render ASS subtitles`, uma com `loudnorm` e uma com `ebur128`.
- Se faltar a linha `ass`, esse ffmpeg não serve para legenda (foi compilado sem a biblioteca de legenda): avise antes de continuar.

**Passo 5 — Conferir o motor de transcrição (faster-whisper).**
```powershell
& $py -m pip show faster-whisper
```
- Deve aparecer: `Name: faster-whisper` e `Version: ...`.
- Se aparecer `WARNING: Package(s) not found`, instale (gratuito, roda no próprio PC; precisa de internet só para instalar):
```powershell
& $py -m pip install faster-whisper
```
- Conferir de novo com o primeiro comando. Deve aparecer o nome e a versão.

**Passo 6 — Criar as pastas no H: (para nada ir para o C:).**
```powershell
New-Item -ItemType Directory -Force "H:\HypadoLocal\modelos\whisper", "H:\HypadoLocal\modelos\hf", "H:\HypadoLocal\ferramentas\fontes", $prov | Out-Null
$env:HF_HOME = "H:\HypadoLocal\modelos\hf"
```
- Conferir: `Test-Path "H:\HypadoLocal\modelos\whisper"` → `True`.
- Por quê: o motor de transcrição baixa o "cérebro" (modelo) na primeira vez. Sem isso, ele baixaria no C:, o que é proibido na HP. A linha `$env:HF_HOME` também precisa ser colada toda vez que abrir o PowerShell para transcrever (junto com o passo 2).

**Passo 7 — Instalar as fontes Montserrat.**
- Abrir: no navegador, `https://fonts.google.com/specimen/Montserrat` → **Get font** → **Download all**. (É gratuita; não precisa criar conta — se o site pedir login, feche e avise: **nunca** criar conta nem aceitar termos em nome da HP.)
- Descompactar o `.zip` e copiar `Montserrat-ExtraBold.ttf` e `Montserrat-SemiBold.ttf` (ficam dentro da pasta `static`) para `H:\HypadoLocal\ferramentas\fontes\`.
- Conferir:
```powershell
Get-ChildItem "H:\HypadoLocal\ferramentas\fontes" -Filter "Montserrat-*.ttf" | Select-Object Name
```
- Deve aparecer: `Montserrat-ExtraBold.ttf` e `Montserrat-SemiBold.ttf`.
- Se a queima de legenda (passo 53) não achar a fonte por esse caminho, instale no Windows também: botão direito em cada `.ttf` → **Instalar**.

**Passo 8 — Conferir os dicionários de nomes.**
```powershell
Get-ChildItem "G:\Meu Drive\Hypado\06 Projeto\app\dicionarios" -Filter "nomes_*.txt" | Select-Object Name, Length
```
- Deve aparecer: 6 arquivos (`nomes_gta.txt`, `nomes_futebol.txt`, `nomes_filmes.txt`, `nomes_receitas.txt`, `nomes_carros.txt`, `nomes_destinos.txt`).
- Se a pasta ou algum arquivo não existir (a criar): abra o Bloco de Notas, cole as linhas de exemplo da seção 2.11 daquele canal, e salve com **Salvar como** → Codificação **UTF-8** → nome `nomes_<canal>.txt` nessa pasta.

**Passo 9 — Instalar o roteiro provisório de transcrição.**
- Enquanto o módulo do app não existe, a transcrição roda por um roteiro curto (o texto completo está na seção 8.6).
- Abra o Bloco de Notas, cole o texto da seção 8.6, **Salvar como** → Codificação **UTF-8** → `H:\HypadoLocal\app\provisorio\transcrever.py`.
- Conferir:
```powershell
& $py "$prov\transcrever.py" --help
```
- Deve aparecer: a ajuda em português ("Transcreve o bruto.mp4 de um item…") com as opções `--item`, `--canal`, `--idioma`, `--modelo`.

**Passo 10 — Teste de fumaça (confere que queimar legenda funciona no PC).**
```powershell
$t = "H:\HypadoLocal\app\teste_legenda"; New-Item -ItemType Directory -Force $t | Out-Null; Set-Location $t
& $ff -hide_banner -loglevel error -y -f lavfi -i "color=c=0x334455:s=1080x1920:r=30:d=4" -f lavfi -i "sine=frequency=300:sample_rate=48000:d=4" -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest teste.mp4
```
- Depois crie no Bloco de Notas um `teste.ass` (UTF-8) com o conteúdo do exemplo da seção 2.7 (pode ser só o cabeçalho, os estilos e 2 linhas `Dialogue`) e rode:
```powershell
& $ff -hide_banner -y -i teste.mp4 -vf "ass=teste.ass:fontsdir='H\:/HypadoLocal/ferramentas/fontes'" -c:v libx264 -preset veryfast -c:a copy teste_legendado.mp4 2>&1 | Select-String "fontselect"
Invoke-Item teste_legendado.mp4
```
- Deve aparecer: linhas `fontselect: (Montserrat ExtraBold, 700, 0) -> ...Montserrat-ExtraBold.ttf` e o vídeo abre com a legenda branca de contorno preto.
- Se a linha disser `-> ...arial.ttf` ou `DejaVuSans` ou qualquer outra fonte, **a Montserrat não foi achada**: volte ao passo 7.

### Fase B — Pegar o item certo (todo dia, a partir daqui)

**Passo 11 — Conferir o horário.**
```powershell
Get-Date -Format "HH:mm"
```
- Se estiver **entre 18:00 e 22:29**: **não** rode transcrição nem prévia (passos 19–23 e 53–55) — é trabalho pesado, proibido nesse horário, **inclusive para P0**. Você pode fazer só o que é leve: ler pedido, revisar nomes (passos 28–37), conferir texto. O P0 que chegar nessa janela é o primeiro da fila às 22:30.
- Deve aparecer: a hora atual. Anote mentalmente.

**Passo 12 — Ver a fila da etapa 03.** (Cole o passo 2 antes, se abriu o PowerShell agora.)
```powershell
Get-ChildItem "$esteira\03_legenda_dublagem" -Directory | Sort-Object Name | Select-Object Name
```
- Deve aparecer: a lista de pastas, com os `P0_` primeiro, depois `P1_`, depois `P2_` (a ordem alfabética já faz isso).
- Escolha **a primeira da lista** que ainda não tem `legenda.ass` **ou** que tem `refazer.json`. Para saber quais faltam:
```powershell
Get-ChildItem "$esteira\03_legenda_dublagem" -Directory | Sort-Object Name | ForEach-Object { "{0}  ass={1}  refazer={2}" -f $_.Name, (Test-Path "$($_.FullName)\legenda.ass"), (Test-Path "$($_.FullName)\refazer.json") }
```
- Dentro da mesma prioridade, pegue o de **horário de postagem mais cedo** (o `HHMM` no nome).

**Passo 13 — Entrar na pasta do item.** (Troque o nome pelo item escolhido.)
```powershell
$item = "$esteira\03_legenda_dublagem\P1_2026-09-30_1830_gta_rockstar-quinta"
Set-Location $item; Get-ChildItem | Select-Object Name, Length
```
- Deve aparecer: pelo menos `pedido.json`, `bruto.mp4` e `historico.log`.
- Se faltar `bruto.mp4` ou `pedido.json`: o item está quebrado → passo 62 (mandar para `99_erros`).

**Passo 14 — Ver se o PC está livre para trabalho pesado.**
```powershell
if (Test-Path "H:\HypadoLocal\app\pesado.lock") { Get-Content "H:\HypadoLocal\app\pesado.lock" } else { "livre" }
```
- Deve aparecer: `livre`, ou um texto com `"dono": "..."` dizendo quem está usando.
- Se estiver ocupado: **não apague o arquivo**. Faça os passos leves (15–18) e volte depois. O roteiro de transcrição pega e solta a trava sozinho; se a trava tiver mais de 3 horas ou o dono já tiver fechado, ele assume sozinho.

**Passo 15 — Ler o pedido.**
```powershell
Get-Content pedido.json -Encoding UTF8
```
- Conferir, um por um (anote num papel ou no Bloco de Notas):
  1. `id` é **igual** ao nome da pasta? (Se não for → passo 62.)
  2. `canal` (um dos 6).
  3. `tipo` — se for `carrossel`, `story` ou `threads`, **não há legenda a fazer**: escreva no histórico `legendador: tipo <x> não tem legenda — pulado` e passe para o próximo item.
  4. `idioma_origem` (`pt` = português; qualquer outro = vai ter Tradutor).
  5. `audio.tratamento` (`original`, `legenda_traduzida`, `dublagem` ou `sem_fala`).
  6. `toque_hp.usar` e `toque_hp.modo`.
  7. `fonte.criador_arroba` (vai no crédito).
  8. `valores_citados`.
  9. `publicar_em` (prazo).

**Passo 16 — Conferir as travas de conteúdo [BLOQUEIA].**
- **Pedido com voz onde a voz é proibida** — `canal` = `futebol` ou `gta` com `audio.tratamento` = `dublagem` ou `toque_hp.modo` = `voz`; ou `dublagem` com `origem` ≠ `proprio`:
  - o item **não para** por isso: o Tradutor (manual 05) faz **legenda** no lugar da dublagem e o Narrador (manual 06) **rebaixa** o Toque HP para `texto`. Os dois escrevem o motivo;
  - o Legendador **confere**, antes de gerar a legenda (passo 41), que nesses casos **não existe** `dublagem.wav` nem `toque_hp.wav` na pasta, e que `traducao.json → decisao.modo` = `legenda` e `toque_hp.json → modo` = `texto`/`nenhum`;
  - se existir arquivo de voz nesses canais → **pare** e mande para `99_erros` (passo 62), motivo `voz sintética em canal/vídeo proibido`.
- **Sem crédito** — `fonte.criador_arroba` **e** `fonte.criador_nome` vazios → pare, `99_erros` (sem crédito não sai).
- **Vazamento** — `observacoes` fala em "vazamento", "leak", "vazou" no GTA → pare, volta ao Curador (`99_erros` com o motivo).
- Exemplos de linha no histórico:
  - `legendador: pedido com toque_hp.modo=voz no futebol — conferido: Narrador rebaixou para texto; sem toque_hp.wav`
  - `legendador: BLOQUEADO — sem crédito (fonte.criador_arroba e criador_nome vazios)`

**Passo 17 — Conferir o vídeo cru.**
```powershell
& $ff -hide_banner -i bruto.mp4 2>&1 | Select-String "Duration|Stream"
```
- Deve aparecer: `Duration: 00:00:29.50` (a duração), uma linha `Video:` (com o tamanho, ex. `1080x1920`) e uma linha `Audio:`.
- Se **não** houver linha `Audio:`: o vídeo não tem som. Só vale seguir se `audio.tratamento` = `sem_fala` (aí a legenda terá só crédito, Toque HP e aviso). Se o pedido disser outra coisa → `99_erros` com o motivo "bruto sem áudio".
- Se a duração for **0** ou der erro "Invalid data" → arquivo corrompido → `99_erros`.

**Passo 18 — Ver se é uma volta do Revisor.**
```powershell
if (Test-Path refazer.json) { Get-Content refazer.json -Encoding UTF8 } else { "primeira passada" }
```
- Se aparecer o conteúdo do `refazer.json`: leia `criterio_menor_nota` e `motivo`, e vá **direto** para o passo que resolve (tabela abaixo). Não refaça a transcrição se o problema não for de transcrição.

| Critério no `refazer.json` | Vá para o passo |
|---|---|
| `L1_texto` (palavra errada) | 28 |
| `L2_nomes` (nome próprio) | 30 |
| `L3_sincronia` (tempo) | 43 |
| `L4_quebra` (corte de linha) | 42 |
| `L5_leitura` (rápido demais) | 43 |
| `L6_estilo` (fonte/cor) | 49 |
| `L7_zona` (tapando algo) | 48 |
| `L8_credito` | 46 |
| `L9_valores` | 47 |
| `L10_toque` | 45 |
| `L11_arquivos` | 49 |

### Fase C — Transcrever [APP]

**Passo 19 — Tirar o áudio do vídeo** (formato que o motor de transcrição gosta: 16 mil amostras por segundo, 1 canal).
```powershell
& $ff -hide_banner -loglevel error -y -i bruto.mp4 -vn -ac 1 -ar 16000 -c:a pcm_s16le audio_16k.wav
Get-Item audio_16k.wav | Select-Object Name, Length
```
- Deve aparecer: `audio_16k.wav` com cerca de 1 MB para cada 30 s de vídeo (32 KB por segundo).

**Passo 20 — Conferir se tem voz (ou só silêncio).**
```powershell
& $ff -hide_banner -nostats -i audio_16k.wav -af volumedetect -f null - 2>&1 | Select-String "mean_volume|max_volume"
```
- Deve aparecer: `mean_volume: -24.3 dB` e `max_volume: -3.1 dB` (números parecidos).
- Se `max_volume` for **menor que -50 dB**: é praticamente mudo. Trate como `sem_fala` e anote no histórico.
- Se `mean_volume` for **maior que -10 dB**: o áudio está estourado; a transcrição pode errar mais. Siga, mas espere mais pendências.

**Passo 21 — Escolher o modelo de transcrição.**
| Situação | Modelo | Por quê |
|---|---|---|
| Padrão (fala clara, até 90 s de vídeo) | `small` | Bom e rápido no processador |
| Áudio difícil (torcida, vento, música alta, sotaque forte) ou `confianca_media` < 0,75 na 1ª tentativa | `medium` | Erra menos, mas leva 2 a 3 vezes mais tempo |
| P0 com pressa e fala muito clara | `small` (nunca menor que isso) | `tiny` e `base` erram nomes demais |
- O modelo `small` ocupa cerca de 0,5 GB e o `medium`, cerca de 1,5 GB em `H:\HypadoLocal\modelos\whisper\` (baixados uma vez só).

**Passo 22 — Rodar a transcrição.** (Troque `gta` e `en` pelo canal e pelo `idioma_origem` do pedido.)
```powershell
$env:HF_HOME = "H:\HypadoLocal\modelos\hf"
& $py "$prov\transcrever.py" --item $item --canal gta --idioma en --modelo small
```
- Na **primeira vez** o modelo é baixado (precisa de internet; alguns minutos).
- Tempo esperado depois disso: num PC comum, de 20 s a 2 min para um vídeo de 30 s.
- Deve aparecer no fim: `OK: 11 palavras, conf. media 0.91, idioma en (0.98), 1 correcoes, 1 pendencias` e, se houver, as linhas `PENDENCIA seg 2 em 4.99 s: Leonidas.`
- Se aparecer `TravaOcupada: horário proibido` → você está entre 18h e 22h30; espere.
- Se aparecer `TravaOcupada: pesado.lock com '...'` → outro trabalho pesado está rodando; espere e tente de novo em 5 minutos.

**Passo 23 — Conferir o `transcricao.json`.**
```powershell
notepad transcricao.json
```
- Conferir: `idioma_detectado`, `confianca_media`, a lista `segmentos` (o texto faz sentido?), `correcoes` e `pendencias`.
- Deve aparecer: o texto que você ouve no vídeo, dividido em frases, cada palavra com `inicio` e `fim`.

**Passo 24 — Se o idioma detectado for diferente do pedido.**
- Ex.: pedido diz `en`, detectado `es` com `prob_idioma` 0,95 → o vídeo é em espanhol. O roteiro usa o detectado quando a certeza é ≥ 0,80.
- Anote no histórico: `legendador: idioma do pedido en, detectado es (0,95) — usado es; avisar Tradutor`.
- Se o detectado for `pt` e o pedido dizia outro: não há tradução a fazer; mude mentalmente o tratamento para `original` e anote.

**Passo 25 — Se a confiança média estiver baixa (< 0,75).**
- Rode de novo com o modelo `medium` (passo 22 trocando `small` por `medium`).
- Se continuar abaixo de 0,75: áudio ruim. Siga para a revisão (Fase D) com mais atenção. Se continuar abaixo de **0,55**, o vídeo provavelmente não serve para legenda confiável → avise o Curador pelo histórico e mande para `99_erros` com o motivo "áudio ininteligível (conf. 0,52)".

**Passo 26 — Tirar o que não é fala.**
- Letra de música **não** vira legenda (direitos autorais e distração). Se o vídeo tiver música cantada, apague esses segmentos do `transcricao.json` e anote em `trechos_sem_fala`.
- O motor às vezes "inventa" frases em silêncio ou música, como "Legendas pela comunidade Amara.org", "Obrigado por assistir", "Inscreva-se". O roteiro já tira as mais comuns; se aparecer outra frase que ninguém fala no vídeo, apague o segmento.
- No **futebol**, grito de torcida e cântico não viram legenda; só fala de gente (jogador, técnico, repórter do clube).

**Passo 27 — Conferir que é mesmo material permitido (o ouvido do Legendador é o primeiro filtro) [BLOQUEIA].**
- **Futebol:** se você ouvir **narração de transmissão de TV** (narrador de jogo de emissora, vinheta de canal), o vídeo não é oficial do clube: pare, `99_erros`, motivo "áudio de transmissão de TV".
- **GTA:** se a fala cita informação de **vazamento** ("vazou", "leak", "build de teste", "gameplay vazado"), pare, `99_erros`, motivo "conteúdo de vazamento".
- **Qualquer canal:** se a fala tiver ofensa a grupo de pessoas, conteúdo sexual, violência real ou algo que você não mostraria para a sua família, pare e mande de volta ao Curador.

### Fase D — Revisar texto e nomes [APP + CLAUDE]

**Passo 28 — Ler o texto inteiro ouvindo o vídeo.**
- Abra o vídeo (`Invoke-Item bruto.mp4`) e o `transcricao.json` lado a lado.
- Confira palavra por palavra. Corrija palavra errada (ex.: "concerto" x "conserto", "mais" x "mas", "há" x "a").
- Regra: **a legenda escreve o que foi dito, com ortografia certa**. Não "melhore" a fala do criador; só tire vícios que atrapalham ("é… é…", "tipo, tipo") quando não mudam o sentido.

**Passo 29 — Conferir as correções automáticas do dicionário.**
- Na lista `correcoes`, cada linha mostra `de` → `para`. Confirme que fazem sentido no contexto (ex.: no Carros, "CV" pode ser "currículo" numa fala solta — raro, mas confira).

**Passo 30 — Resolver as pendências (nomes e palavras com pouca certeza) [CLAUDE].**
- Para cada `PENDENCIA`, recorte 3 segundos em volta do tempo indicado e ouça (troque `4.0` pelo tempo da pendência menos 1 segundo):
```powershell
& $ff -hide_banner -loglevel error -y -ss 4.0 -t 3 -i bruto.mp4 -c:v libx264 -preset veryfast -c:a aac trecho_pendencia.mp4
Invoke-Item trecho_pendencia.mp4
```
- Decida a palavra certa. Para nome próprio, **a fonte oficial manda**:
  - GTA: site oficial da Rockstar (`rockstargames.com/VI`) e as redes oficiais da Rockstar.
  - Futebol: site oficial do clube ou da CBF (grafia do nome no elenco).
  - Filmes: pôster/título oficial no Brasil (distribuidora).
  - Receitas: grafia do dicionário (VOLP) — ex.: "muçarela".
  - Carros: site oficial da montadora no Brasil.
  - Destinos: nome oficial do lugar (prefeitura, ICMBio, órgão de turismo).
- Se não der para ter certeza: **não chute**. Deixe a palavra fora da legenda ou troque por algo genérico e certo ("o atacante", "a personagem") e anote.

**Passo 31 — Gravar a correção no `transcricao.json`.**
- No Bloco de Notas, troque a palavra em `"p": "..."` **e** no `"texto"` do segmento; acrescente uma linha em `correcoes` com `"por": "claude:pendencias"` e tire o item da lista `pendencias`.
- Cuidado: não apague aspas, vírgulas nem chaves. Salve (Ctrl+S) e confira se o arquivo continua válido:
```powershell
& $py -m json.tool transcricao.json | Out-Null; if ($LASTEXITCODE -eq 0) { "JSON OK" } else { "JSON QUEBRADO - desfaça a última mudança" }
```
- Deve aparecer: `JSON OK`.

**Passo 32 — Ensinar o dicionário.** Toda correção de nome feita à mão vira uma variação nova no dicionário do canal, para o app acertar sozinho da próxima vez.
- Abra `G:\Meu Drive\Hypado\06 Projeto\app\dicionarios\nomes_<canal>.txt`, ache a linha do nome certo e acrescente a variação errada depois de um `;`. Ex.: `Leonida | Leônida; Leonidas; Leonída; Leônidas`.
- Nome novo (que ainda não existe no arquivo): acrescente uma linha nova: `Ambrosia | Ambrósia; Ambrozia`.
- Salve em UTF-8.

**Passo 33 — Conferir os números.**
- Todo número ouvido vira **algarismo**: "vinte e três" → `23`; "dois a um" → `2 a 1`; "cento e oitenta quilômetros por hora" → `180 km/h`; "dezenove de novembro" → `19/11`.
- Confira o número com o que aparece na imagem (placar, preço na etiqueta, velocímetro). Se o áudio e a imagem discordarem, vale a imagem — e anote.

**Passo 34 — Suavizar palavrão.**
- Palavrão na tela ganha asterisco na 2ª letra: "p*rra", "c*ralho", "m*rda". A fala (áudio) não se mexe.
- Lista de trocas em `dicionarios\suavizar.txt` (a criar). Se o vídeo inteiro for cheio de palavrão, avise o Curador: talvez não sirva para a marca.

**Passo 35 — Padronizar os termos de cada canal.**
| Canal | Sempre escrever | Nunca escrever |
|---|---|---|
| GTA | `GTA 6`, `Rockstar`, `Vice City`, `Lucia`, `Jason`, `19/11` | `GTA VI`, `GTA6`, "Rock Star", "Lúcia" |
| Futebol | nome como está no elenco oficial do clube; `Vini Jr.`; placar `2 a 1` | apelido pejorativo, nome de narrador de TV |
| Filmes | título brasileiro oficial (`Divertida Mente 2`) | título em inglês quando existe o brasileiro |
| Receitas | `xícara`, `colher (sopa)`, `°C`, `g`, `ml`, `muçarela` | `cup`, `°F`, `oz`, "mussarela" |
| Carros | `km/h`, `cv`, `km/l`, `R$` + "Valores aproximados…" | `mph`, `hp` sozinho, `mpg` |
| Destinos | nome oficial com acento (`Lençóis Maranhenses`) | nome sem acento, nome em inglês de lugar brasileiro |

**Passo 36 — Olhar a transcrição inteira uma última vez, com o som desligado.**
- Pergunta-teste: "se eu só lesse isso, entenderia o vídeo?" Se não, falta algo (uma frase não transcrita, um trecho confuso) → volte ao passo 28.

**Passo 37 — Marcar como revisado.**
- No `transcricao.json`: `"revisado": true`, `"pendencias": []` e, em `revisado_por`, acrescente `"claude:pendencias"` se o Claude resolveu alguma.
- Confira com o comando do passo 31 (`JSON OK`).
- Histórico:
```powershell
Add-Content -Path historico.log -Encoding UTF8 -Value "$(Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz') [03] legendador: transcrição revisada (2 correções, 0 pendências)"
```

### Fase E — Esperar a tradução e o Toque HP [APP]

**Passo 38 — Se o vídeo não é em português: esperar o `traducao.json`.**
```powershell
Test-Path traducao.json
```
- `False` → o Tradutor (manual 05) ainda está trabalhando. Anote `legendador: aguardando traducao.json` e passe para outro item; volte depois.
- `True` → abra (`notepad traducao.json`) e confira que tem um bloco `legenda` com o texto em português de **cada** segmento da transcrição (mesmos `id`).

**Passo 39 — Se o pedido tem Toque HP: esperar o `toque_hp.json`.**
```powershell
Test-Path toque_hp.json
```
- `False` → o Narrador (manual 06) ainda não terminou. Espere.
- `True` → confira: `modo` (`voz`, `misto`, `texto` ou `nenhum`), `abertura.texto_tela` (≤ 2 linhas de ≤ 20 caracteres), `fecho.texto_tela`, e os tempos (`abertura.inicio` = 0,00 e `abertura.fim` ≤ 2,00).

**Passo 40 — Conferir se tudo combina.**
- Os `id` dos segmentos da tradução batem com os da transcrição? (Mesmo número de segmentos.)
- O trecho narrado do Toque HP (se `modo` = `voz`) cai num lugar **sem fala** do vídeo? (Compare `trecho.inicio`/`fim` com `trechos_sem_fala` da transcrição.) Se cair em cima de fala, devolva ao Narrador com o motivo.
- Se houver `dublagem.wav`: o Tradutor já gravou em `traducao.json → dublagem.segmentos` o início e o fim de cada frase dublada. Esses tempos é que valem para a legenda.

### Fase F — Montar os blocos da legenda [APP]

**Passo 41 — Escolher de onde vem o texto e o tempo.**
| `audio.tratamento` | Texto da legenda vem de | Tempo vem de | Karaokê? |
|---|---|---|---|
| `original` (vídeo em pt) | `transcricao.json` (revisado) | palavras da transcrição | **Sim** |
| `legenda_traduzida` | `traducao.json → legenda` | início/fim de cada segmento da transcrição, repartido entre os blocos pelo número de letras | **Não** (palavra-chave fixa na cor) |
| `dublagem` | `traducao.json → dublagem.texto` | palavras da voz dublada (o app transcreve o `dublagem.wav`, que é português) | **Sim** |
| `sem_fala` | nada de fala; só Toque HP, crédito e aviso | — | — |

**Passo 42 — Dividir o texto em blocos (a "quebra").**
- Siga a tabela e as regras de quebra da seção 2.12. Receita prática:
  1. Pegue a frase: "A Lucia conhece cada rua de Leonida".
  2. Corte em pedaços de 2 a 4 palavras sem quebrar as regras: "A Lucia conhece" | "cada rua de Leonida".
  3. Conte os caracteres de cada pedaço (espaços contam): 15 e 19 → ambos ≤ 22. OK.
  4. Nenhum pedaço termina com "de", "que", "o"…: OK.
- Exemplos de quebra certa x errada:
| Frase | Errado | Certo |
|---|---|---|
| "O Corolla Cross faz 12 km/l na estrada" | "O Corolla" / "Cross faz 12" / "km/l na estrada" | "O Corolla Cross" / "faz 12 km/l" / "na estrada" |
| "Gol do Arrascaeta aos 20 minutos" | "Gol do" / "Arrascaeta aos 20" / "minutos" | "Gol do Arrascaeta" / "aos 20 minutos" |
| "Leve ao forno a 180 °C por 40 minutos" | "Leve ao forno a" / "180 °C por 40" / "minutos" | "Leve ao forno" / "a 180 °C" / "por 40 minutos" |
| "A entrada custa cerca de R$ 50" | "A entrada custa cerca de R$" / "50" | "A entrada custa" / "cerca de R$ 50" |
| "Timothée Chalamet volta em Duna" | "Timothée" / "Chalamet volta em Duna" | "Timothée Chalamet" / "volta em Duna" |
| "Jason e Lucia fogem pela Vice City" | "Jason e" / "Lucia fogem pela" / "Vice City" | "Jason e Lucia" / "fogem pela Vice City" |

**Passo 43 — Pôr o tempo em cada bloco.**
- **Início** = início da 1ª palavra do bloco (pode adiantar no máximo 40 ms; nunca atrasar mais que 80 ms).
- **Fim** = fim da última palavra + 0,25 s, **ou** o início do próximo bloco, o que vier primeiro.
- Se o bloco ficar com **menos de 0,50 s**: junte com o vizinho (se couber em 22 caracteres) ou estique o fim até 0,50 s (se não bater no próximo).
- Se ficar com **mais de 3,0 s**: corte o fim em 3,0 s.
- Calcule a **velocidade (CPS)** = número de caracteres ÷ duração em segundos. Ex.: "cada rua de Leonida" = 19 caracteres em 1,37 s → 13,9 CPS. OK (limite 17). Se passar de 17: junte blocos em 2 linhas (dá mais tempo por bloco) ou, na tradução, peça ao Tradutor uma frase mais curta.
- Buraco menor que 0,30 s entre dois blocos: o primeiro estica até o segundo.
- Na **legenda traduzida**, cada segmento da transcrição vira 1 ou mais blocos; o tempo do segmento é repartido **pelo número de letras** de cada bloco e o corte é "puxado" para o início de palavra mais próximo no áudio original (até 150 ms de ajuste). Ex.: segmento de 3,41 s a 5,87 s (2,46 s), blocos de 15 e 19 letras → 1,09 s e 1,37 s → "A Lucia conhece" de 3,41 a 4,50; "cada rua de Leonida" de 4,50 a 5,87.

**Passo 44 — Pintar a palavra certa na cor do canal.**
- **Com karaokê** (fala em português): 1 evento por palavra; a palavra falada naquele instante fica na cor do canal; as outras, brancas. Palavra de menos de 120 ms acende junto com a vizinha.
- **Sem karaokê** (tradução): em cada bloco, **uma** palavra-chave fixa na cor do canal: nome próprio > número > lugar > verbo principal. Bloco sem nada disso fica todo branco.
- Confira a cor pela tabela da seção 2.12 (lembrando que no ASS a ordem é azul-verde-vermelho).

**Passo 45 — Pôr as falas do Toque HP (se houver).**
- **Abertura (pergunta)**: estilo `Pergunta`, de 0:00:00.00 até o `abertura.fim` do `toque_hp.json` (no máximo 0:00:02.00), texto `abertura.texto_tela`, com `\N` na quebra.
- **Trecho narrado** (só nos modos `voz` e `misto`): vira legenda normal (estilo `HP`, com karaokê sobre o `toque_hp.wav`), nos tempos do `toque_hp.json`. No modo `misto`, a abertura é só escrita (a fala do vídeo começa antes de 2,10 s).
- **Fecho (pergunta final)**: estilo `Pergunta`, nos tempos do `fecho` (normalmente os últimos 2 a 3 s do vídeo).
- Enquanto a pergunta de abertura está na tela (topo), a legenda de fala continua normal (embaixo). Nunca duas perguntas ao mesmo tempo.
- Exemplos por canal (tudo vem do manual 06; aqui só confira os limites):
| Canal | Abertura (na tela) | Fecho (na tela) | Modo |
|---|---|---|---|
| GTA | "Você reconheceria\Nessa cidade à noite?" | "Vai jogar em 19/11?\NComenta aí" | texto |
| Futebol | "Foi pênalti\Nou não foi?" | "Acertou o placar?\NComenta aí" | texto |
| Filmes | "Você viu esse\Ndetalhe no filme?" | "Qual cena te pegou?\NComenta aí" | voz ou texto |
| Receitas | "Já fez pão\Nsem sovar?" | "Faria hoje?\NSalva pra depois" | voz ou texto |
| Carros | "Você pagaria\Nisso num carro?" | "Compraria ou não?\NComenta aí" | voz ou texto |
| Destinos | "Conhece a praia\Nmais azul do Brasil?" | "Iria ou passaria?\NConta aí" | voz ou texto |

**Passo 46 — Pôr o crédito do criador [BLOQUEIA se faltar].**
- Estilo `Credito`, do **primeiro ao último** segundo do vídeo, camada 2 (por cima de tudo).
- Texto: `Vídeo: ` + `fonte.criador_arroba` (ex.: `Vídeo: @rockstargames`). Sem @: `Vídeo: ` + `fonte.criador_nome` (ex.: `Vídeo: Rockstar Games`).
- Futebol: `Vídeo: @<clube>` (ex.: `Vídeo: @flamengo`). Vídeo próprio da HP feito com imagens de terceiros: `Imagens: @fonte1, @fonte2` (no máximo 2; se forem mais, "Imagens: @fonte1 e outros" e a lista completa vai no texto do post, manual 08).
- O crédito tem que ser **igual** ao do pedido (letra por letra). Não invente @.

**Passo 47 — Pôr o aviso de valores (se houver dinheiro no vídeo).**
- Sempre que um bloco tiver `R$`, `US$`, `€`, "reais", "dólares", "mil", "milhões" referente a preço/salário/valor: estilo `Aviso`, texto `Valores aproximados…`, do início desse bloco até 2 s depois do fim dele (junte avisos que fiquem a menos de 2 s um do outro).
- Exemplos: Carros "Custa R$ 289 mil" · Destinos "Diária de R$ 450" · Futebol "Contrato de € 40 milhões" · Receitas "Tudo por menos de R$ 30".

**Passo 48 — Escolher a posição (e não tapar nada importante) [CLAUDE quando houver conflito].**
- Padrão: `baixo`.
- Tire 3 quadros do bruto (início, meio, fim) e olhe onde a legenda cairia:
```powershell
New-Item -ItemType Directory -Force quadros | Out-Null
$d = (Get-Content transcricao.json -Raw -Encoding UTF8 | ConvertFrom-Json).duracao_s
$meio = ([math]::Round($d / 2, 2)).ToString([cultureinfo]::InvariantCulture)
$fim = ([math]::Round($d - 1.5, 2)).ToString([cultureinfo]::InvariantCulture)
& $ff -hide_banner -loglevel error -y -ss 1 -i bruto.mp4 -frames:v 1 quadros\b1_inicio.jpg
& $ff -hide_banner -loglevel error -y -ss $meio -i bruto.mp4 -frames:v 1 quadros\b2_meio.jpg
& $ff -hide_banner -loglevel error -y -ss $fim -i bruto.mp4 -frames:v 1 quadros\b3_fim.jpg
Invoke-Item quadros
```
- Olhe as 3 imagens. Na faixa de baixo (entre 60% e 75% da altura) tem: placar (futebol), texto do próprio criador (receita escrita), rosto, legenda original do criador? → mude para `meio`. Se o meio também estiver ocupado → `alto`.
- Vídeo que já vem com legenda queimada do criador **em português**: não ponha outra por cima; escreva no pedido do histórico `legenda do criador já existe — só crédito e Toque HP` e peça confirmação ao Curador.
- Vídeo com legenda queimada **em outro idioma**: a nossa vai **por cima**, com a posição escolhida para tapar a original quando possível (normalmente `baixo`); se não der para tapar, o Editor (manual 03) põe uma tarja.

### Fase G — Gerar os arquivos [APP]

**Passo 49 — Gerar o `legenda.ass`.**
- Pelo módulo do app (a criar): o comando será algo como `python -m esteira legendar --item <pasta>` (nome provisório; o nome final é o do módulo da etapa 3).
- Até lá: quem gera é o Claude, seguindo **exatamente** o modelo da seção 2.7 (cabeçalho, os 4 estilos, cor do canal) com os blocos dos passos 42 a 48, e grava em **UTF-8**.
- Conferir o cabeçalho: `PlayResX: 1080`, `PlayResY: 1920`, `WrapStyle: 2`, os 4 estilos (`HP`, `Pergunta`, `Credito`, `Aviso`) e a cor do canal no estilo `Pergunta` (4º campo de cor = `OutlineColour`).

**Passo 50 — Gerar o `legenda.srt`.**
- Mesmo texto do ASS, mas em frases (seção 2.6): até 2 linhas de até 42 caracteres, de 1,0 a 6,0 s cada, sem cor e sem códigos `{\...}`.
- Numeração 1, 2, 3…; tempo com **vírgula** (`00:00:03,410`); UTF-8.

**Passo 51 — Conferir a codificação.**
- Abra os dois no Bloco de Notas. No canto de baixo à direita deve aparecer **UTF-8**. Se aparecer "ANSI", **Salvar como** → Codificação UTF-8.
- Acentos (ç, ã, é) aparecem certos? Se aparecer `Ã§` no lugar de `ç`, a codificação está errada.

**Passo 52 — Conferência automática dos números.**
- Pelo app (a criar): gera `checagem_legenda.json` (seção 2.8) e só deixa seguir se `resultado` = `ok`.
- À mão, as 3 conferências mais importantes:
```powershell
# 1) as 5 linhas mais compridas (tem que ser <= 22 caracteres)
Get-Content legenda.ass -Encoding UTF8 | Where-Object { $_ -like "Dialogue:*" -and $_ -notlike "*,Credito,*" -and $_ -notlike "*,Aviso,*" } | ForEach-Object { (($_ -split ",", 10)[9] -replace "\{[^}]*\}", "") -split "\\N" } | Sort-Object Length -Descending | Select-Object -First 5 | ForEach-Object { "{0,3} : {1}" -f $_.Length, $_ }
# 2) quantos blocos de fala e de pergunta
(Get-Content legenda.ass -Encoding UTF8 | Select-String ",HP,").Count; (Get-Content legenda.ass -Encoding UTF8 | Select-String ",Pergunta,").Count
# 3) o crédito
Get-Content legenda.ass -Encoding UTF8 | Select-String ",Credito,"
```
- Deve aparecer: (1) números **≤ 22** na frente de cada linha; (2) a contagem de eventos (com karaokê, são muitos: um por palavra); (3) uma linha com `Vídeo: @...` começando em `0:00:00.00` e terminando na duração do vídeo.

### Fase H — Prévia e conferência visual [APP + CLAUDE]

**Passo 53 — Fazer a prévia queimada (em tamanho pequeno, rápida).**
```powershell
& $ff -hide_banner -y -i bruto.mp4 -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,ass=legenda.ass:fontsdir='H\:/HypadoLocal/ferramentas/fontes',scale=540:960" -c:v libx264 -preset veryfast -crf 26 -c:a aac -b:a 96k previa_legenda.mp4 2>&1 | Select-String "fontselect|Error|error"
```
- Deve aparecer: linhas `fontselect: (Montserrat ExtraBold, 700, 0) -> ...Montserrat-ExtraBold.ttf` e `(Montserrat SemiBold, ...) -> ...Montserrat-SemiBold.ttf`, e **nenhuma** linha com "Error".
- Esta prévia **não é** o vídeo final: é só para conferir. O final (1080x1920, qualidade alta) é feito pelo Editor (manual 03) com o mesmo `legenda.ass`.

**Passo 54 — Assistir à prévia duas vezes.**
```powershell
Invoke-Item previa_legenda.mp4
```
- 1ª vez **com som**: a legenda entra junto com a fala? A palavra acesa é a que está sendo dita?
- 2ª vez **sem som**: dá para entender tudo só lendo? Dá tempo de ler cada bloco?

**Passo 55 — Tirar os 3 quadros de conferência (os mesmos que o Revisor vai olhar).**
```powershell
& $ff -hide_banner -loglevel error -y -ss 1 -i previa_legenda.mp4 -frames:v 1 quadros\q1_01s.jpg
& $ff -hide_banner -loglevel error -y -ss $meio -i previa_legenda.mp4 -frames:v 1 quadros\q2_meio.jpg
& $ff -hide_banner -loglevel error -y -ss $fim -i previa_legenda.mp4 -frames:v 1 quadros\q3_fim.jpg
Invoke-Item quadros
```
- (Se fechou o PowerShell depois do passo 48, recalcule `$meio` e `$fim` com as 3 linhas de lá.)

**Passo 56 — Conferir cada quadro com esta lista.**
- [ ] Fonte grossa (Montserrat), branca, com contorno preto.
- [ ] Cor de destaque é a do canal (rosa no GTA, verde no Futebol, amarelo no Filmes, laranja no Receitas, azul no Carros, turquesa no Destinos).
- [ ] Crédito no canto de cima à esquerda, legível, e **não** colado na borda.
- [ ] Nada escrito na faixa de baixo (os últimos 25% da tela) nem colado na direita (onde ficam os botões).
- [ ] A legenda não tapa rosto, placar, escudo, preço na etiqueta ou texto importante do vídeo.
- [ ] No quadro 1 (1 s), a pergunta do Toque HP aparece (se o pedido tiver).
- [ ] No quadro 3 (fim), a pergunta de fecho aparece (se o pedido tiver).
- [ ] Aviso "Valores aproximados…" aparece onde tem dinheiro.

**Passo 57 — Conferir a sincronia com números (quando houver dúvida).**
- Escolha 3 blocos (começo, meio, fim). Para cada um, compare o início do bloco no `legenda.ass` com o `inicio` da 1ª palavra no `transcricao.json`.
- A diferença tem que ficar **entre −40 ms e +80 ms**. Ex.: palavra "Lucia" começa em 3,410 s; bloco começa em `0:00:03.41` → diferença 0 ms. OK.
- O app (a criar) faz isso para **todos** os blocos e grava em `checagem_legenda.json → desvio_inicio_ms`.

**Passo 58 — Corrigir o que falhou.**
- Voltou algum "não" nos passos 54 a 57? Corrija no passo correspondente (quebra → 42; tempo → 43; cor → 44; posição → 48; crédito → 46), gere de novo (49–50) e refaça a prévia (53).
- No máximo 3 rodadas de correção nesta etapa. Se na 3ª ainda houver problema, algo está errado no material ou na ferramenta → passo 62.

### Fase I — Entregar

**Passo 59 — Escrever no histórico o resultado com números.**
```powershell
Add-Content -Path historico.log -Encoding UTF8 -Value "$(Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz') [03] legendador: legenda.ass e legenda.srt gerados (4 blocos + 2 do Toque HP; máx. 19 caracteres/linha; desvio máx. 38 ms; fonte ok; zona segura ok; crédito ok)"
```
- Troque os números pelos do seu item.

**Passo 60 — Limpar o que é temporário.**
```powershell
Remove-Item audio_16k.wav, trecho_pendencia.mp4 -ErrorAction SilentlyContinue
```
- **Não apague**: `transcricao.json`, `legenda.ass`, `legenda.srt`, `previa_legenda.mp4`, `quadros\`, `historico.log`, nem nada que outro cargo criou. A prévia e os quadros são apagados pelo app depois que o item for postado.
- Se era uma volta do Revisor: `Rename-Item refazer.json refazer_1_feito.json` (ou `refazer_2_feito.json` na segunda volta).

**Passo 61 — Passar o item para a edição.**
- Só quando **tudo** da etapa 03 estiver pronto: `legenda.ass` + `legenda.srt` e, se o pedido pedir, `traducao.json`/`dublagem.wav` (manual 05) e `toque_hp.json`/`toque_hp.wav` (manual 06).
- O app (a criar) move sozinho. À mão:
```powershell
Set-Location $esteira
Move-Item $item "$esteira\04_edicao\"
Test-Path "$esteira\04_edicao\$(Split-Path $item -Leaf)"
```
- Deve aparecer: `True`.
- Se aparecer erro "sendo usado por outro processo": feche o vídeo/prévia que estiver aberto (e o Bloco de Notas) e tente de novo.
- Anote no histórico (agora dentro da pasta nova): `legendador: fim; pronto para 04_edicao`.

**Passo 62 — Quando algo dá errado: mandar para `99_erros`.**
- Crie um `erro.json` na pasta do item (Bloco de Notas, UTF-8):
```json
{
  "etapa": "03_legenda_dublagem",
  "cargo": "legendador",
  "quando": "2026-09-30T14:40:00-03:00",
  "motivo": "áudio de transmissão de TV no futebol",
  "passo": 27,
  "o_que_tentou": "ouvi o trecho de 0 a 10 s: narrador de emissora e vinheta",
  "precisa_de": "Curador escolher outro vídeo oficial do clube"
}
```
- Mova: `Set-Location $esteira; Move-Item $item "$esteira\99_erros\"`.
- Histórico: `legendador: enviado para 99_erros — <motivo>`.

**Passo 63 — Erro que se repete: abrir ticket.**
- Se o mesmo problema acontecer 2 vezes na semana (ex.: fonte sumindo, motor de transcrição travando, dicionário não sendo lido), abra um ticket na área do app com a ferramenta existente `scripts\tickets.py` (veja as opções com `& $py "$scripts\tickets.py" --help`). O ticket vai para `08 Empresa\tickets\<area>\novo\`.
- Nunca escreva senha, token ou dado pessoal no ticket.

---

## 4. Regras que nunca se quebram

1. **[BLOQUEIA] Crédito do criador sempre.** Todo vídeo com imagem de terceiro sai com "Vídeo: @criador" na tela do começo ao fim, igual ao `pedido.json`. Sem crédito, não sai.
2. **[BLOQUEIA] Futebol nunca tem narração sintética.** Nem dublagem, nem Toque HP com voz. A legenda do futebol é sempre da fala original (ou tradução dela, em texto). Se o pedido vier com voz no futebol, a voz é trocada por legenda/texto (manuais 05 e 06); se aparecer arquivo de voz sintética num item de futebol, o item para.
3. **[BLOQUEIA] Voz sintética só em Destinos, Receitas, Carros e Filmes, e só em vídeo próprio.** GTA e Futebol: nunca. Na legenda, isso aparece assim: só existe karaokê "de dublagem" nesses 4 canais.
4. **[BLOQUEIA] Nada de vazamento do GTA 6.** Se a fala cita material vazado, o item volta ao Curador. A legenda nunca escreve informação de vazamento, nem "dizem que vazou".
5. **[BLOQUEIA] Futebol sem imagem nem áudio de transmissão de TV.** Se ouvir narrador de emissora, para.
6. **[BLOQUEIA] Valor citado leva "Valores aproximados…".** Todo preço, salário, diária ou multa na legenda vem com o aviso.
7. **Nunca inventar fala.** A legenda só escreve o que foi dito (ou a tradução fiel do sentido). Frase que o motor inventou em silêncio ou música é apagada.
8. **Nunca chutar nome próprio.** Na dúvida, fonte oficial; sem fonte, não escreve o nome.
9. **Nunca legendar letra de música.** Música de fundo não vira texto.
10. **Nunca apagar nem sobrescrever arquivo de outro cargo** (`pedido.json`, `bruto.mp4`, `traducao.json`, `dublagem.wav`, `toque_hp.*`, `final.mp4`, `capa.jpg`, `post.json`).
11. **Nunca apagar linha do `historico.log`.** Só acrescentar.
12. **Nunca renomear a pasta do item** nem mudar a prioridade (`P0_`/`P1_`/`P2_`).
13. **Trabalho pesado 1 por vez e nunca das 18h às 22h30** — transcrição e prévia respeitam o `pesado.lock`. Nem P0 fura esse horário.
14. **Nada no disco C:.** Modelos, fontes, arquivos temporários: tudo no H: (ou no G:, para o que é conhecimento, como dicionários).
15. **Nenhuma janela preta piscando na tela do Antônio.** Rotina automática roda sem console (`pythonw` + `CREATE_NO_WINDOW`, que a função `rodar()` do `hpbase` já faz).
16. **Nunca emoji dentro da legenda queimada.** Vira quadradinho.
17. **Nunca mais de 2 linhas, nunca mais de 22 caracteres por linha.**
18. **Nunca legenda de fala com menos de 0,50 s nem mais de 3,0 s** (exceção única: 0,35 s para a última palavra de frase muito rápida).
19. **Nunca a fonte substituta.** Se a Montserrat não for achada (linha `fontselect` com outra fonte), não entrega.
20. **Sem senha, token ou dado pessoal** em legenda, log, ticket ou arquivo do item.
21. **O texto do SRT é sempre igual ao do ASS** (só muda a quebra).
22. **Toda correção de nome feita à mão vai para o dicionário** no mesmo dia (é assim que o app fica independente da IA).
23. **Nada vai para o app sem 7 dias de modo sombra com qualidade idêntica comprovada** (teste de paridade com números — seção 9).

---

## 5. Critérios de qualidade com nota

**Como funciona:** o Revisor (manual 09) dá nota de 0 a 10 em cada critério abaixo (o app já sugere uma nota prévia em `checagem_legenda.json → notas_previas`). As notas da legenda entram na média geral do vídeo junto com as dos outros cargos (média simples, todos com o mesmo peso, a menos que o manual 09 defina outro peso).
- Média **≥ 9** = **Excelente** → aprovado.
- Média **7 a 8,9** = **Bom** → aprovado.
- Média **5 a 6,9** = **Médio** → volta para a etapa do **critério de menor nota** (se for um destes, volta para `03_legenda_dublagem`, para o Legendador).
- Média **< 5** = **Razoável** → volta ao **Curador** (manual 01).
- Máximo de **2 voltas**; na 3ª, o item vai para `99_erros`.
- Critério marcado **[BLOQUEIA]** com nota 0 = o item não sai, qualquer que seja a média (o Revisor devolve direto à etapa responsável ou ao Curador, conforme o motivo).

| Cód. | Critério | Como medir | Nota 10 | Nota 7 | Nota 5 | Nota 0 | Volta para |
|---|---|---|---|---|---|---|---|
| L1 | Texto fiel à fala | Ler a legenda ouvindo o vídeo; contar palavras erradas (fora nomes) | 0 erros | 1 erro que não muda o sentido | 2 a 3 erros, ou 1 que muda o sentido | 4+ erros, ou frase inventada (alucinação), ou letra de música legendada | 03 (Legendador) |
| L2 | Nomes próprios | Conferir cada nome com o dicionário/fonte oficial | Todos certos | 1 acento faltando em nome secundário | 1 nome secundário com grafia errada | Nome principal errado ("Arascaeta", "Lussia") ou nome inventado | 03 (Legendador) |
| L3 | Sincronia | `desvio_inicio_ms` do `checagem_legenda.json` (ou 3 blocos à mão, passo 57) | Máx. ≤ 80 ms e média ≤ 40 ms; nenhum bloco antes de −40 ms | Máx. ≤ 150 ms | Máx. ≤ 250 ms | Máx. > 250 ms, ou legenda "adiantada" mais de 200 ms | 03 (Legendador) |
| L4 | Quebra de linha | Maior linha (passo 52) e regras de quebra (seção 2.12) | Todas ≤ 22 caracteres e 0 quebra proibida | 1 quebra feia ("…de" / "São Paulo"), todas ≤ 22 | 2 a 3 quebras feias, ou 1 linha de 23 a 26 | Linha > 26, ou bloco com 3 linhas, ou número separado da unidade em 2+ blocos | 03 (Legendador) |
| L5 | Tempo de leitura | Duração de cada bloco (0,50–3,0 s) e CPS (≤ 17) | Todos dentro | 1 a 2 blocos fora (CPS ≤ 20) | 3 a 5 blocos fora | Mais de 5 fora, ou algum com CPS > 25, ou pisca-pisca | 03 (Legendador) |
| L6 | Estilo HP | Quadros + linha `fontselect` + cabeçalho do ASS | Fonte, tamanho, contorno e cor do canal exatamente como 2.12 | 1 desvio pequeno (tamanho ± 4 px, sombra diferente) | Cor de outro canal, ou caixa alta no texto todo | Fonte substituta (Arial/DejaVu), texto sem contorno ilegível, ou emoji virando quadrado | 03 (Legendador) |
| L7 | Zona segura / não tapar | 3 quadros com a moldura da zona segura | Nada fora da zona e nada importante tapado | Tapa parte de algo secundário (canto de logo) | 1 bloco na área dos botões ou do texto do post | Tapa placar, rosto principal, preço ou texto cortado na borda | 03 (Legendador) |
| L8 | Crédito [BLOQUEIA] | Linha `Credito` do ASS e quadros | Presente 100% do tempo, @ igual ao pedido, legível | Presente, mas some antes do fim (≥ 80% do tempo) | Presente < 80% do tempo, ou pouco legível | Ausente ou @ errado | 03 (Legendador) |
| L9 | "Valores aproximados…" [BLOQUEIA] | Procurar R$, US$, €, "mil", "milhões" e conferir o aviso | Todo valor com aviso (ou não há valor) | Aviso presente, mas some antes de 2 s depois do valor | (não existe meio-termo: ou tem, ou não tem) | Valor sem aviso | 03 (Legendador) |
| L10 | Toque HP na legenda | Tempos do estilo `Pergunta` x `toque_hp.json` | Pergunta de 0,00 a ≤ 2,00 s, fecho no final, texto igual ao do Narrador | Pergunta entra até 0,30 s atrasada ou dura até 2,5 s | Pergunta entra depois de 0,5 s, ou fecho ausente | Toque pedido e ausente; ou legenda de voz sintética em Futebol/GTA [BLOQUEIA] | 03 (Narrador, manual 06, se o texto estiver errado; Legendador, se for tempo/estilo) |
| L11 | Arquivos e técnica | ASS e SRT abrem, UTF-8, mesmo texto; `checagem_legenda.json` = `ok` | Tudo certo | Diferença só de pontuação entre SRT e ASS | SRT faltando, ou texto diferente entre SRT e ASS | ASS não abre, acentos quebrados (`Ã§`), ou tempos negativos | 03 (Legendador) |

**Exemplo de cálculo (só da parte da legenda):** L1=10, L2=10, L3=7, L4=10, L5=10, L6=10, L7=10, L8=10, L9=10, L10=10, L11=10 → soma 107 ÷ 11 = **9,7 → Excelente**.
**Exemplo com nome errado:** L2=0 ("Arascaeta" no lugar de "Arrascaeta") e o resto 10 → soma 100 ÷ 11 = 9,1. Pela média, seria aprovado. Mas nome principal errado é erro público (vira deboche nos comentários). Por isso este manual recomenda ao Revisor (manual 09): **nota 0 em L2 devolve para 03, mesmo com média ≥ 7**.
**Exemplo de volta pela média:** L3=5 (sincronia de 200 ms), L4=5, L5=5, o resto 7 → soma 15 + 56 = 71 ÷ 11 = 6,5 → Médio → volta para a etapa do critério de menor nota (L3/L4/L5, todos do Legendador) → `03_legenda_dublagem`, com `refazer.json`.

**Nota prévia automática (a criar):** o app calcula L3, L4, L5, L6 (fonte), L8, L9 (procura de símbolos de dinheiro) e L11 sozinho, com os números acima. L1, L2, L7 e L10 (texto) precisam de olho: o app dá uma nota provisória com base na confiança da transcrição e o Revisor confirma.

---

## 6. Erros comuns e o que fazer

| Sintoma (o que você vê) | Causa provável | Solução |
|---|---|---|
| A legenda aparece em Arial ou outra letra fina | Montserrat não achada; a linha `fontselect` mostra outra fonte | Passo 7 (copiar os `.ttf` para `H:\HypadoLocal\ferramentas\fontes\` ou instalar no Windows) e refazer a prévia |
| Erro `Unable to open legenda.ass` ou `No such file` no ffmpeg | O PowerShell não está dentro da pasta do item, ou o nome está errado | `Set-Location $item` e confira com `Get-ChildItem` |
| Erro de caminho com `fontsdir` (`Invalid argument`) | O `:` do `H:` precisa de `\` antes, dentro de aspas simples | Use exatamente `fontsdir='H\:/HypadoLocal/ferramentas/fontes'`; se não resolver, instale as fontes no Windows e tire o `:fontsdir=...` |
| Acentos viram `Ã§`, `Ã£`, `Ã©` | Arquivo salvo em ANSI em vez de UTF-8 | Bloco de Notas → Salvar como → Codificação UTF-8 |
| O rosa do GTA saiu azul (ou o azul do Carros saiu laranja) | Cor escrita na ordem normal (RGB) em vez da ordem do ASS (BGR) | Converter como na seção 2.12: `#FF2E88` → `&H00882EFF` |
| Legenda atrasada em relação à boca | Tempo pego do segmento e não da palavra; ou o Editor pôs algo antes do vídeo (cartão de 2 s) e não deslocou a legenda | Usar o tempo da palavra; se o Editor inseriu algo antes, ele desloca a legenda pelo mesmo tempo (manual 03) |
| Legenda adiantada (aparece antes da fala) | Adiantamento maior que 40 ms, ou motor marcou o início da palavra cedo demais em fala após silêncio | Limitar o adiantamento a 40 ms; conferir o bloco no passo 57 e corrigir à mão |
| Aparece "Legendas pela comunidade Amara.org" ou "Obrigado por assistir" | "Alucinação" do motor em silêncio ou música | Apagar o segmento (passo 26) e acrescentar a frase à lista `ALUCINACOES` do roteiro |
| Transcrição em inglês de um vídeo em português (ou o contrário) | Detecção de idioma errou (áudio curto, música no começo) | Rodar de novo com `--idioma pt` (o roteiro força o idioma quando a certeza é baixa) |
| `confianca_media` abaixo de 0,75 | Áudio com torcida, vento, música alta, sotaque | Rodar com `--modelo medium`; revisar com calma; abaixo de 0,55 → `99_erros` |
| Nome sempre errado do mesmo jeito | Falta a variação no dicionário | Passo 32 (acrescentar a variação) |
| Pisca-pisca (blocos aparecendo e sumindo muito rápido) | Blocos de 1 palavra ou buracos < 0,30 s não emendados | Juntar blocos (mínimo 2 palavras) e esticar até o próximo |
| Linha com mais de 22 caracteres | Palavras longas ("desenvolvimento", "Fernando de Noronha") em bloco de 3–4 palavras | Bloco de 2 palavras, ou 2 linhas (pirâmide) |
| Legenda em cima do placar / do ingrediente escrito | Posição `baixo` em vídeo que tem informação embaixo | Passo 48: mudar para `meio` ou `alto` |
| Crédito com @ diferente do pedido | Digitado à mão, ou copiado de outro item | Copiar de `pedido.json → fonte.criador_arroba` (nunca digitar) |
| Crédito some no meio | Tempo final do crédito menor que a duração | `End` do crédito = `duracao_s` do bruto |
| "Valores aproximados…" faltando | Preço falado não marcado no pedido | Procurar R$/US$/€/"mil" na legenda (passo 47) e sempre pôr o aviso |
| `TravaOcupada: horário proibido` | Tentou trabalho pesado entre 18h e 22h30 | Esperar 22h30; fazer só passos leves |
| `TravaOcupada: pesado.lock com 'esteira:editar'` | Outro trabalho pesado rodando | Esperar 5 min; nunca apagar o `pesado.lock` à mão |
| `ModuleNotFoundError: No module named 'faster_whisper'` | Motor não instalado nesse Python | Passo 5 |
| `ModuleNotFoundError: No module named 'hpbase'` | Caminho do app diferente no roteiro | Conferir a linha `sys.path.insert` do roteiro (seção 8.6) com o caminho real de `06 Projeto\app\hp_studio` |
| A transcrição baixou o modelo no C: | Faltou `$env:HF_HOME` ou o `download_root` | Passo 6; apagar a cópia do C: (`%USERPROFILE%\.cache\huggingface`) depois de conferir que a do H: existe |
| Transcrição muito lenta (> 5 min para 30 s) | Modelo `medium`/`large` num PC ocupado, ou outro programa pesado aberto | Usar `small`; conferir no Gerenciador de Tarefas; nunca rodar 2 ao mesmo tempo |
| `JSON QUEBRADO` depois de editar | Faltou vírgula, aspas ou chave | Desfazer (Ctrl+Z) até voltar a `JSON OK` |
| Não consegue mover a pasta ("em uso") | Vídeo, prévia ou Bloco de Notas abertos com arquivo da pasta; ou o PowerShell está dentro dela | Fechar tudo e `Set-Location $esteira` antes do `Move-Item` |
| Legenda do criador (em outro idioma) aparece embaixo da nossa | Vídeo já veio legendado | Posicionar a nossa por cima da dele; se não der, pedir tarja ao Editor (manual 03) |
| Revisor devolveu 2 vezes pelo mesmo motivo | Correção incompleta, ou problema no material | Não tentar a 3ª: `99_erros` + ticket (passo 63) |

---

## 7. O que o app faz sozinho x o que o Claude decide

**Meta:** o app fazer tudo o que é regra fixa (tempos, quebra, cor, arquivos, conferência com números); o Claude entra só no que é julgamento (nome duvidoso, posição quando há conflito na imagem, frase ambígua). Quanto mais o dicionário cresce, menos o Claude é chamado.

| Passo(s) | Tarefa | App sozinho | Claude decide | Observação |
|---|---|---|---|---|
| 11–14 | Horário, fila por prioridade, trava | 100% | 0% | Regra fixa (`TravaPesada`, ordem por nome) |
| 15–16 | Ler pedido e travas de conteúdo | 100% | 0% | Regras [BLOQUEIA] são automáticas |
| 17–18 | Conferir bruto e `refazer.json` | 100% | 0% | |
| 19–22 | Extrair áudio e transcrever | 100% | 0% | faster-whisper + dicionário como dica |
| 23–25 | Idioma e confiança | 95% | 5% | Claude só quando conf. < 0,55 (decidir se serve) |
| 26 | Tirar alucinação e letra de música | 85% | 15% | Lista fixa de frases; música cantada precisa de ouvido |
| 27 | Conteúdo proibido no áudio (TV, vazamento) | 30% | 70% | App procura palavras ("vazou", "leak", nomes de emissora); o ouvido decide |
| 28–29 | Texto fiel e correções automáticas | 80% | 20% | Com conf. ≥ 0,85 o app confia; abaixo, amostra para o Claude |
| 30–32 | Nomes próprios e pendências | 85% | 15% | Dicionário resolve a maioria; Claude só nas pendências (poucas palavras, pouco token) |
| 33–35 | Números, palavrão, termos do canal | 95% | 5% | Tabelas fixas |
| 36–37 | Leitura final e "revisado" | 60% | 40% | Claude lê o texto (não o vídeo): barato |
| 38–40 | Esperar e conferir tradução e Toque HP | 100% | 0% | |
| 41–44 | Blocos, tempos, CPS, karaokê, cor | 100% | 0% | Regras da seção 2.12 |
| 45–47 | Toque HP, crédito, aviso de valores | 100% | 0% | Tudo vem do pedido e do `toque_hp.json` |
| 48 | Posição (conflito com placar/texto) | 70% | 30% | App usa a regra do canal (futebol → `meio` quando `modo`=gol); Claude olha 3 quadros quando em dúvida |
| 49–52 | Gerar ASS/SRT e conferência | 100% | 0% | `checagem_legenda.json` |
| 53–57 | Prévia, quadros, sincronia | 90% | 10% | App mede; Claude olha os 3 quadros só se o app acusar algo |
| 58–63 | Corrigir, entregar, erros, ticket | 90% | 10% | |
| **Total ponderado** | | **≈ 90%** | **≈ 10%** | Meta em 3 meses: 95% / 5% (dicionários maiores e posição automática por canal) |

**Como a parte do Claude diminui com o tempo:**
1. Toda correção vira dicionário (passo 32) → menos pendências.
2. O Analista de resultados (manual 11) não interfere aqui; mas o Revisor (09) registra os motivos de volta: se "L7 posição" aparecer muito num canal, vira regra fixa desse canal.
3. Frases de alucinação novas vão para a lista fixa.

---

## 8. Ferramentas existentes que já fazem cada passo

### 8.1 Tabela rápida
| Passo | Ferramenta | Situação |
|---|---|---|
| Baixar e cortar o bruto (antes da etapa 03) | `scripts\ytdlp.py`, `scripts\cortar.py`, `scripts\lote.py` | (existente) |
| 11–14 (trava, horário) | `hpbase.TravaPesada`, `hpbase.janela_proibida` | (existente) |
| 17, 19, 20, 48, 53, 55 | **ffmpeg** (`H:\HypadoLocal\ferramentas\ffmpeg\bin\ffmpeg.exe`) | (existente) |
| 17 (duração) | **ffprobe** — pode não existir no PC; plano B é o próprio ffmpeg (`-i arquivo`, linha `Duration`) | (pode faltar) |
| 22 (transcrição) | **faster-whisper** + roteiro provisório `H:\HypadoLocal\app\provisorio\transcrever.py` (seção 8.6) | (a instalar, se faltar) / (provisório) |
| 28–32 (nomes) | Dicionários `06 Projeto\app\dicionarios\nomes_<canal>.txt` | (a criar) |
| 41–52 (gerar ASS/SRT e checagem) | Módulo legendador da esteira (etapa 3 do app) | (a criar) |
| 45 (Toque HP) | Saída do Narrador (manual 06) | (a criar no app) |
| Caixa de legenda do Futebol (modo gol) | `scripts\posts_futebol.py legenda_video` | (existente) |
| Montador de reels do Futebol | `reel_futebol.py` | (a criar — ticket do módulo G) |
| Queima final no vídeo | Editor (manual 03), com o mesmo `legenda.ass` | (existente no processo do Claude; no app, a criar) |
| Comparar com o vídeo feito 100% pelo Claude | `qa_paridade` | (a criar — módulo D) |
| Registrar histórico e JSON | `hpbase.anexar_linha`, `hpbase.escrever_json` | (existente) |
| Subprocesso sem janela preta | `hpbase.rodar` (usa `CREATE_NO_WINDOW`) | (existente) |
| Tickets | `scripts\tickets.py` | (existente) |
| Painel local | `scripts\painel_local.py` | (existente) |

### 8.2 ffmpeg (explicado para leigo)
É um programa gratuito, sem janela, que faz "tudo" com vídeo e áudio: corta, junta, tira o som, mede o volume, tira foto de um instante e **queima a legenda** no vídeo. A HP usa o que está em `H:\HypadoLocal\ferramentas\ffmpeg\bin\`. Você fala com ele pelo PowerShell, e a resposta vem em texto. Partes do comando que aparecem neste manual:
- `-i bruto.mp4` = "abra este arquivo".
- `-y` = "pode sobrescrever o arquivo de saída sem perguntar".
- `-hide_banner -loglevel error` = "fale pouco; só mostre erro".
- `-vn` = "sem vídeo" (só o som). `-ac 1 -ar 16000` = 1 canal, 16 mil amostras por segundo.
- `-ss 4.0 -t 3` = "comece em 4,0 s e pegue 3 s".
- `-frames:v 1` = "só 1 quadro" (uma foto).
- `-vf "ass=legenda.ass"` = "desenhe esta legenda em cima do vídeo".
- `-af volumedetect` = "meça o volume".
- `-c:v libx264 -crf 26 -preset veryfast` = "grave em H.264, qualidade média, rápido" (bom para prévia).

### 8.3 libass (a parte do ffmpeg que desenha a legenda)
Vem dentro do ffmpeg (filtro `ass`). Lê o `legenda.ass`, procura a fonte pedida e desenha as letras com contorno e cor. Quando não acha a fonte, **troca sem avisar** por outra — por isso o passo 53 manda procurar a linha `fontselect`.

### 8.4 faster-whisper (o "ouvido" do computador)
Biblioteca gratuita de Python que transforma fala em texto **no próprio PC** (depois de baixar o modelo, não usa internet e não gasta token). Dá o tempo de início e fim de cada palavra e a "certeza" (de 0 a 1). Opções usadas:
- `modelo` = tamanho do "cérebro": `small` (padrão) ou `medium` (mais preciso, mais lento).
- `compute_type="int8"` = jeito leve de calcular, para rodar no processador.
- `word_timestamps=True` = tempo por palavra (necessário para o karaokê).
- `vad_filter=True` = pula os trechos sem voz (diminui as "alucinações").
- `initial_prompt` = uma "dica" com os nomes do canal, para ele acertar mais nomes próprios.
- `download_root` = onde guarda o modelo (sempre no H:).

### 8.5 hpbase (a base comum do app — existente)
Funções prontas que o roteiro e o futuro módulo usam: `TravaPesada` (1 trabalho pesado por vez e nada das 18h às 22h30), `rodar` (roda o ffmpeg sem abrir janela preta), `achar_ffmpeg`/`achar_ffprobe` (acham os programas; o ffprobe pode faltar), `escrever_json` (grava JSON sem deixar arquivo pela metade), `anexar_linha` (escreve no `historico.log` com data e hora de Brasília), `obter_logger` (log em `H:\HypadoLocal\app\logs\` sem segredo).

### 8.6 Roteiro provisório de transcrição (`H:\HypadoLocal\app\provisorio\transcrever.py`)
Usado no passo 22 enquanto o módulo do app não existe. Copie exatamente (salvar em UTF-8):
```python
"""transcrever.py - PROVISORIO (manual 04, Legendador).

Transcreve o bruto.mp4 de um item da esteira com o faster-whisper, aplica o
dicionario de nomes do canal e grava transcricao.json. Vale ate o modulo
legendador da etapa 3 do app existir.

Uso (PowerShell):
  & $py H:\\HypadoLocal\\app\\provisorio\\transcrever.py --item <pasta> --canal gta --idioma en
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, r"G:\Meu Drive\Hypado\06 Projeto\app\hp_studio")

DIC = Path(r"G:\Meu Drive\Hypado\06 Projeto\app\dicionarios")
MODELOS = Path(r"H:\HypadoLocal\modelos\whisper")
# frases que o motor "inventa" em silencio ou musica: nunca viram legenda
ALUCINACOES = ("amara.org", "legendas pela comunidade", "obrigado por assistir",
               "inscreva-se", "thanks for watching", "subtitles by")
LIMITE_CONF = 0.60


def _limpa(t):
    return re.sub(r"[^\w\s/-]", "", t, flags=re.UNICODE).strip().lower()


def ler_dicionario(canal, pasta=DIC):
    """Devolve (lista de formas certas, {variacao_errada_minuscula: forma certa})."""
    certos, trocas = [], {}
    p = Path(pasta) / f"nomes_{canal}.txt"
    if not p.exists():
        return certos, trocas
    for linha in p.read_text(encoding="utf-8-sig").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#"):
            continue
        forma, _, erros = linha.partition("|")
        forma = forma.strip()
        if not forma:
            continue
        certos.append(forma)
        for e in erros.split(";"):
            e = e.split("(")[0].strip()
            if e:
                trocas[_limpa(e)] = forma
    return certos, trocas


def aplicar_dicionario(palavras, trocas, certos):
    """Troca erros comuns (ate 3 palavras seguidas) pela forma certa."""
    certos_min = {c.lower() for c in certos}
    saida, correcoes, i = [], [], 0
    while i < len(palavras):
        feito = False
        for n in (3, 2, 1):
            grupo = palavras[i:i + n]
            if len(grupo) < n:
                continue
            junto = _limpa(" ".join(w["p"] for w in grupo))
            if junto in trocas and junto not in certos_min:
                final = re.findall(r"[.,!?…]+$", grupo[-1]["p"])
                nova = dict(grupo[0])
                nova["p"] = trocas[junto] + (final[0] if final else "")
                nova["fim"] = grupo[-1]["fim"]
                nova["conf"] = 1.0
                correcoes.append({"de": " ".join(w["p"] for w in grupo),
                                  "para": nova["p"], "por": "app:dicionario"})
                saida.append(nova)
                i += n
                feito = True
                break
        if not feito:
            saida.append(palavras[i])
            i += 1
    return saida, correcoes


def main():
    ap = argparse.ArgumentParser(description="Transcreve o bruto.mp4 de um item (manual 04).")
    ap.add_argument("--item", required=True, help="pasta do item na esteira")
    ap.add_argument("--canal", required=True,
                    choices=["gta", "futebol", "filmes", "receitas", "carros", "destinos"])
    ap.add_argument("--idioma", default="pt", help="idioma do pedido (pt, en, es...)")
    ap.add_argument("--modelo", default="small", help="tiny, base, small, medium, large-v3")
    ap.add_argument("--audio", default="audio_16k.wav", help="wav 16 kHz mono (passo 19)")
    a = ap.parse_args()

    from hpbase import TravaPesada, escrever_json, agora_iso, anexar_linha
    from faster_whisper import WhisperModel

    item = Path(a.item)
    certos, trocas = ler_dicionario(a.canal)
    dica = ("Nomes: " + ", ".join(certos[:40]) + ".") if certos else None
    with TravaPesada("legendador:transcrever"):
        modelo = WhisperModel(a.modelo, device="cpu", compute_type="int8",
                              download_root=str(MODELOS))
        segs, info = modelo.transcribe(str(item / a.audio), language=None,
                                       word_timestamps=True, vad_filter=True,
                                       initial_prompt=dica, beam_size=5)
        idioma = info.language
        if idioma != a.idioma and info.language_probability < 0.80:
            segs, _ = modelo.transcribe(str(item / a.audio), language=a.idioma,
                                            word_timestamps=True, vad_filter=True,
                                            initial_prompt=dica, beam_size=5)
            idioma = a.idioma
        segmentos, todas_corr, pend, confs = [], [], [], []
        for s in segs:
            if any(x in s.text.lower() for x in ALUCINACOES):
                continue
            pal = [{"p": w.word.strip(), "inicio": round(w.start, 3),
                    "fim": round(w.end, 3), "conf": round(w.probability, 2)}
                   for w in (s.words or []) if w.word.strip()]
            pal, corr = aplicar_dicionario(pal, trocas, certos)
            n = len(segmentos) + 1
            for c in corr:
                c["segmento"] = n
            todas_corr += corr
            for w in pal:
                confs.append(w["conf"])
                if w["conf"] < LIMITE_CONF:
                    pend.append({"segmento": n, "palavra": w["p"], "inicio": w["inicio"]})
            if pal:
                segmentos.append({"id": n, "inicio": pal[0]["inicio"], "fim": pal[-1]["fim"],
                                  "texto": " ".join(w["p"] for w in pal), "palavras": pal})
    media = round(sum(confs) / len(confs), 2) if confs else 0.0
    escrever_json(item / "transcricao.json", {
        "versao": 1, "item": item.name, "arquivo_fonte": "bruto.mp4",
        "duracao_s": round(info.duration, 3), "idioma_pedido": a.idioma,
        "idioma_detectado": info.language,
        "prob_idioma": round(info.language_probability, 2),
        "idioma_usado": idioma, "motor": "faster-whisper", "modelo": a.modelo,
        "calculo": "int8", "criado_em": agora_iso(), "confianca_media": media,
        "revisado": not pend, "revisado_por": ["app:dicionario_" + a.canal],
        "segmentos": segmentos, "correcoes": todas_corr, "pendencias": pend,
    })
    anexar_linha(item / "historico.log",
                 f"[03] legendador: transcricao ok (faster-whisper {a.modelo} int8, "
                 f"idioma {idioma}, {len(confs)} palavras, conf. media {media}, "
                 f"{len(todas_corr)} correcoes, {len(pend)} pendencias)")
    print(f"OK: {len(confs)} palavras, conf. media {media}, idioma {idioma} "
          f"({info.language_probability:.2f}), {len(todas_corr)} correcoes, "
          f"{len(pend)} pendencias")
    for p in pend:
        print(f"  PENDENCIA seg {p['segmento']} em {p['inicio']:.2f} s: {p['palavra']}")


if __name__ == "__main__":
    main()
```

---

## 9. Testes de aceitação

Uma entrega do Legendador (feita à mão, pelo Claude ou pelo app) só é aceita se passar em **todos** os testes abaixo. Para o app assumir a tarefa, os testes 1 a 30 têm que passar em **todos os itens de 7 dias seguidos de modo sombra** (o app faz em paralelo, sem publicar, e o `qa_paridade` — a criar — compara com o que foi feito pelo Claude).

### 9.1 Arquivos
1. `transcricao.json`, `legenda.ass` e `legenda.srt` existem na pasta do item e têm mais de 0 bytes.
2. Os três abrem como UTF-8 sem erro; `python -m json.tool transcricao.json` sai com código 0.
3. `transcricao.json` tem `"revisado": true` e `"pendencias": []`.
4. O ASS tem `PlayResX: 1080`, `PlayResY: 1920` e os 4 estilos `HP`, `Pergunta`, `Credito`, `Aviso`.
5. O SRT tem numeração contínua começando em 1, tempo `HH:MM:SS,mmm` e nenhum tempo negativo ou com fim ≤ início.
6. O texto do SRT, sem pontuação e sem quebras, é **100% igual** ao texto dos eventos `HP` + `Pergunta` do ASS (sem os códigos `{\...}` e sem repetir os eventos de karaokê).
7. `historico.log` tem pelo menos 3 linhas novas `[03] legendador:` (início, transcrição, legenda gerada) com números.

### 9.2 Texto
8. Taxa de erro de palavras (WER) da legenda contra a fala conferida por gente em 5 vídeos de teste: **≤ 3%** em áudio limpo e **≤ 8%** em áudio difícil (torcida, vento).
9. Nomes próprios: **100%** certos nos 5 vídeos de teste (0 erro de nome principal).
10. Nenhuma frase da lista de alucinações ("Amara.org", "Obrigado por assistir", "Inscreva-se"…) na legenda.
11. Todo número falado aparece em algarismo (0 números por extenso na legenda queimada).
12. 0 emoji na legenda queimada.
13. 0 palavrão sem asterisco.

### 9.3 Tempo
14. Desvio de início de **cada** bloco de fala em relação ao início da 1ª palavra: **entre −40 ms e +80 ms**; média ≤ **40 ms**.
15. Duração de cada bloco de fala: **≥ 0,50 s** (≥ 0,35 s só para última palavra de frase) e **≤ 3,0 s**.
16. CPS de cada bloco **≤ 17**.
17. 0 sobreposição entre blocos do estilo `HP`.
18. 0 buraco menor que 0,30 s entre blocos (tem que estar emendado).
19. Pergunta de abertura do Toque HP (quando pedida): começa em **0,00 s** e termina em **≤ 2,00 s**.
20. Crédito: começa em **0,00 s** e termina na duração do vídeo **± 0,05 s**.
21. Aviso "Valores aproximados…": presente em **100%** dos blocos com valor, até **≥ 2,0 s** depois do fim do bloco.

### 9.4 Forma
22. Nenhuma linha com mais de **22 caracteres** (contando espaços) e nenhuma com largura medida acima de **840 px** na fonte Montserrat ExtraBold 72.
23. Nenhum bloco com mais de **2 linhas**.
24. 0 quebra proibida (artigo/preposição/número/nome separados; bloco terminando em "de", "que", "o"…) — conferido pela lista da seção 2.12.
25. A linha `fontselect` da prévia mostra **Montserrat ExtraBold** e **Montserrat SemiBold** (0 fontes substitutas).
26. A cor de destaque no ASS é exatamente a do canal na tabela da seção 2.12 (ex.: GTA `&H00882EFF`).
27. 0 texto nas faixas proibidas: 220 px de cima, 480 px de baixo, 80 px da esquerda, 160 px da direita (conferido nos 3 quadros com a moldura da zona segura).
28. Karaokê só quando a fala é em português (original ou dublada); legenda traduzida sem karaokê e com no máximo 1 palavra colorida por bloco.

### 9.5 Regras
29. 0 item de Futebol ou GTA com legenda de voz sintética (dublagem ou Toque HP com voz).
30. 0 item sem crédito; 0 crédito diferente de `pedido.json → fonte.criador_arroba` (ou `criador_nome`).
31. 0 transcrição ou prévia rodada entre 18:00 e 22:29 (conferir as horas no `historico.log`).
32. 0 arquivo gravado no disco C: pelo processo (modelos em `H:\HypadoLocal\modelos\`).
33. 0 janela preta aberta durante a rotina automática.

### 9.6 Desempenho (para o app)
34. Transcrição de um vídeo de 30 s com o modelo `small`: **≤ 2 min** no PC do Antônio.
35. Geração de ASS + SRT + checagem: **≤ 10 s** por item.
36. Prévia de 30 s em 540x960: **≤ 1 min**.
37. Na paridade de 7 dias: nota média do Revisor para os critérios L1–L11 do app **≥ nota média do Claude − 0,2** e **nenhum** item do app com critério [BLOQUEIA] em 0.

### 9.7 Casos de teste obrigatórios (um de cada, no mínimo)
| # | Caso | O que tem que acontecer |
|---|---|---|
| T1 | GTA, material oficial em inglês, Toque HP em texto | Legenda traduzida sem karaokê, "GTA 6", "Vice City" em rosa, pergunta de 0 a ≤ 2 s, crédito @rockstargames |
| T2 | Futebol, gol em vídeo oficial do clube com placar embaixo | Legenda em `meio`, sem voz sintética, crédito do clube, "Arrascaeta" certo |
| T3 | Futebol com pedido de Toque HP `voz` | Toque rebaixado para `texto` pelo Narrador; legenda só com a pergunta escrita; nenhum `toque_hp.wav` na pasta; motivo no histórico (se existir `toque_hp.wav` → `99_erros`) |
| T4 | Filmes, entrevista em inglês | Título brasileiro do filme; nomes certos; legenda traduzida |
| T5 | Receitas, criador brasileiro com ingredientes escritos na tela | Karaokê laranja; legenda fora da área dos ingredientes; "muçarela"; números em algarismo |
| T6 | Carros, review com preço | Aviso "Valores aproximados…"; `km/h` e `cv`; azul |
| T7 | Destinos, vídeo próprio dublado | Karaokê sobre a voz dublada; "Jericoacoara" certo; turquesa |
| T8 | Vídeo só com música (sem fala) | Nenhum bloco de fala; só crédito e Toque HP; nenhuma letra de música |
| T9 | Vídeo com palavrão | Asterisco na tela; áudio intacto |
| T10 | Volta do Revisor com `refazer.json` de L2 | Só o nome corrigido; dicionário atualizado; `refazer_1_feito.json` criado |

---

## Glossário

| Palavra | O que quer dizer |
|---|---|
| **ASS** | Tipo de arquivo de legenda que guarda, além do texto e do tempo, a fonte, a cor, o tamanho e a posição. É o que queimamos no vídeo. |
| **Alucinação** | Quando o programa de transcrição "inventa" uma frase que ninguém disse (comum em silêncio e música). |
| **Bloco** | Cada pedacinho de legenda que aparece de uma vez na tela (2 a 4 palavras no padrão HP). |
| **Bruto** (`bruto.mp4`) | O vídeo baixado e cortado no trecho certo, ainda sem nada da HP. |
| **Caixa alta** | Texto todo em letra maiúscula. |
| **Closed caption (CC)** | Legenda que a pessoa liga e desliga no aplicativo (o nosso SRT no YouTube). O contrário da legenda queimada. |
| **Confiança (conf.)** | Número de 0 a 1 que o programa dá para dizer o quanto tem certeza de uma palavra. |
| **CPS** | Caracteres por segundo: quantas letras a pessoa precisa ler a cada segundo. Máximo 17. |
| **Crédito** | O "Vídeo: @criador" na tela, dizendo de quem é o vídeo original. |
| **Dicionário de nomes** | Arquivo com a forma certa dos nomes próprios de cada canal e os erros comuns, para o app corrigir sozinho. |
| **Esteira** | O caminho de pastas por onde cada vídeo passa (01 a 07, e 99 para erros). |
| **faster-whisper** | Programa gratuito que transforma fala em texto no próprio PC. |
| **ffmpeg / ffprobe** | Programas gratuitos, sem janela, que mexem em vídeo e áudio (o ffprobe só lê informações; pode faltar). |
| **Fonte** | O desenho das letras (a da HP é a Montserrat). |
| **fontselect** | Linha que o ffmpeg mostra dizendo qual fonte ele realmente usou. |
| **JSON** | Arquivo de texto organizado em "campo": "valor", que tanto gente quanto programa conseguem ler. |
| **Karaokê** | Efeito em que a palavra falada naquele instante acende na cor do canal. |
| **Legenda queimada** | Legenda desenhada dentro do vídeo; não dá para desligar. |
| **libass** | Parte do ffmpeg que desenha a legenda ASS no vídeo. |
| **LUFS** | Unidade de medida do volume "percebido" (usada pelo Editor e pelo Tradutor; aqui só aparece de passagem). |
| **Modelo** (de transcrição) | O "cérebro" que o faster-whisper baixa uma vez (`small`, `medium`…). |
| **Modo sombra** | O app faz o trabalho em paralelo, sem publicar, só para comparar com o feito pelo Claude durante 7 dias. |
| **P0 / P1 / P2** | Prioridade no nome da pasta: urgente/ao vivo, do dia, programado. |
| **Paridade** | Prova com números de que o app faz igual ao Claude (`qa_paridade`, a criar). |
| **Pendência** | Palavra que o app não teve certeza e precisa de alguém olhar. |
| **pesado.lock** | Arquivo-trava que garante que só 1 trabalho pesado roda por vez. |
| **PlayRes** | O tamanho de tela que o ASS usa como referência (1080x1920). |
| **Prévia** | Versão pequena e rápida do vídeo com a legenda, só para conferir. |
| **PowerShell** | A janela azul do Windows onde se digitam comandos. |
| **Quebra** | Onde a frase é cortada para virar blocos e linhas. |
| **SRT** | Tipo simples de arquivo de legenda: número, tempo e texto. |
| **Toque HP** | A pergunta de abertura (até 2 s), o trecho narrado e a pergunta de fecho que a HP põe no vídeo (manual 06). |
| **Transcrição** | O texto de tudo o que foi falado no vídeo, com o tempo de cada palavra. |
| **UTF-8** | Jeito de gravar texto que guarda os acentos certinho. |
| **VAD** | "Detector de voz": parte do faster-whisper que pula os trechos sem fala. |
| **WER** | Taxa de erro de palavras: quantas palavras em cada 100 estão erradas. |
| **Zona segura** | A parte da tela onde nenhum botão ou texto do aplicativo cobre o vídeo. |
