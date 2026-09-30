# Manual 06 — Narrador "Toque HP"

> **Hypado (HP) · HP Studio · Manuais dos cargos**
> Versão 1.0 · 30/09/2026 · Situação: **rascunho para revisão** (passa a valer depois de revisado e de 7 dias em modo sombra).
> Ler junto com: **01 Curador** (diz se o vídeo é próprio), **02 Pauteiro** (pede o Toque HP no `pedido.json`), **03 Editor** (usa a trilha final), **04 Legendador** (põe as perguntas na tela), **05 Tradutor e dublador** (mesma voz, mesmas regras de pronúncia e de mistura), **09 Revisor** (dá a nota) e **11 Analista de resultados** (diz quais perguntas dão mais comentário).
> Vale para os 6 perfis: **GTA 6 | HP**, **Futebol | HP**, **Filmes e Séries | HP**, **Receitas | HP**, **Carros | HP** e **Destinos | HP** — com **voz** só em 4 deles (Destinos, Receitas, Carros e Filmes, e só em vídeo próprio). Em GTA e Futebol o Toque HP é **só escrito**.

**Resumo em 6 linhas (para quem tem pressa):**
1. O "Toque HP" é a marca da casa em cada vídeo: **uma pergunta nos 2 primeiros segundos** (para a pessoa parar de rolar), **um trecho narrado com voz neutra** (um fato que dá contexto) e **um fecho com pergunta** (para a pessoa comentar).
2. Você escreve as três partes em `toque_hp.json`: o texto que aparece na tela e o texto que a voz fala.
3. **Voz** só com a Piper pt-BR já instalada, pelo `scripts\dublar.py`, e só em **Destinos, Receitas, Carros e Filmes**, em **vídeo próprio**. **Futebol nunca** tem narração sintética; **GTA** também não tem voz — nos dois, o Toque HP é só texto na tela.
4. Tudo que é dito tem que ser **verdade verificável** (nada de vazamento do GTA, nada de "isca" mentirosa).
5. Com voz: gera as falas, encaixa nos espaços **sem fala** do vídeo, monta `toque_hp.wav` e a trilha final `mix_toque.wav` a **−14 LUFS**.
6. O Legendador põe as perguntas na tela (estilo `Pergunta`, cor do canal); o item segue para `04_edicao`.

**Marcadores:** **(a criar)** = ainda não existe; **(existente)** = já funciona no PC do Antônio; **[BLOQUEIA]** = regra inviolável, o item não sai se quebrar.

---

## 1. Objetivo do cargo

### 1.1 Em uma frase
Transformar qualquer vídeo que a HP publica num vídeo **com a cara da HP**: que **segura a pessoa nos 2 primeiros segundos** com uma pergunta, **explica o que ela está vendo** com um trecho curto numa voz neutra (quando a regra permite) e **termina puxando o comentário** com outra pergunta.

### 1.2 Por que isso importa para a HP
- **Os 2 primeiros segundos decidem tudo.** Se a pessoa não para de rolar, o vídeo morre. Uma pergunta específica no primeiro quadro ("Já fez pão sem sovar?") faz o cérebro querer a resposta — e ela fica.
- **Comentário é combustível.** As redes mostram mais o vídeo que gera conversa. Um fecho com uma pergunta de verdade ("Compraria ou não?") transforma quem assistiu em quem comenta.
- **É o que faz o vídeo ser da HP.** Pegar um vídeo bom e só repostar não constrói marca. A pergunta, o contexto e o fecho são a contribuição da HP — é isso que o público reconhece e segue.
- **Tudo isso leva à monetização** (objetivo nº 1): mais tempo assistido + mais comentários + mais seguidores.

### 1.3 As 3 partes do Toque HP
| Parte | Onde fica | Duração | O que é | Exemplo (Receitas) |
|---|---|---|---|---|
| **Abertura** | **0,00 s** até no máximo **2,00 s** | 1,2 a 2,0 s | Uma **pergunta** específica sobre o vídeo, na tela (e falada, quando pode) | "Já fez pão sem sovar?" |
| **Trecho narrado** | Num trecho **sem fala** do vídeo, normalmente entre 3 s e o meio | 4 a 12 s | 1 a 3 frases com **um fato** que dá contexto, em voz neutra (quando pode) | "O segredo é o tempo: a massa descansa de doze a dezoito horas, e o glúten se forma sozinho." |
| **Fecho** | Últimos **2 a 3 s** do vídeo | 2,0 a 3,0 s | Uma **pergunta** para a pessoa responder nos comentários + no máximo 1 convite neutro | "Você faria esse pão hoje?" / tela: "Faria hoje?" + "Salva pra depois" |

### 1.4 Os 4 modos
| Modo | Abertura | Trecho | Fecho | Quando |
|---|---|---|---|---|
| `voz` | Escrita **e** falada | Falado (e legendado com karaokê) | Escrito **e** falado | Destinos, Receitas, Carros, Filmes — vídeo próprio — e os 2 primeiros segundos livres de outra fala |
| `misto` | **Só escrita** | Falado | Escrito e falado | Mesmos canais do `voz`, mas o vídeo já tem fala (original ou dublada) antes de 2,10 s |
| `texto` | Só escrita | **Não tem** (o contexto vai para o texto do post, pelo Redator) | Só escrito | **GTA e Futebol sempre**; qualquer vídeo que não seja próprio; P0 com pressa |
| `nenhum` | — | — | — | Casos da seção 1.7 (tragédia, conteúdo sensível, vídeo que já tem pergunta do criador, etc.) |

### 1.5 O que o Narrador FAZ e NÃO FAZ
**Faz:**
1. Decide o modo (`voz`, `misto`, `texto` ou `nenhum`) pela regra fixa.
2. Escreve a pergunta de abertura, o trecho e o fecho (texto da tela e texto da voz).
3. Confere que tudo é verdade e cabe no tempo.
4. Com voz: gera as falas pelo `scripts\dublar.py`, encaixa nos espaços sem fala, monta `toque_hp.wav` e mistura a trilha final `mix_toque.wav` (−14 LUFS).
5. Deixa recado para o Legendador (tempos e textos) e para o Editor (qual trilha usar).
6. Registra tudo no `historico.log` e no banco de perguntas (para o app aprender o que funciona).

**Não faz:**
| Não faz | Quem faz | Manual |
|---|---|---|
| Pedir ou não pedir o Toque HP | Pauteiro | 02 |
| Dizer se o vídeo é próprio | Curador | 01 |
| Traduzir a fala do vídeo / dublar o vídeo | Tradutor e dublador | 05 |
| Desenhar a pergunta na tela (arquivo `.ass`) | Legendador | 04 |
| Montar o vídeo final, música | Editor | 03 |
| Escrever o texto do post (pode repetir a pergunta do fecho) | Redator | 08 |
| Medir quais perguntas funcionam | Analista de resultados | 11 |

### 1.6 Onde fica na esteira
```
01_pedidos → 02_baixados → [03_legenda_dublagem] → 04_edicao → 05_revisao → 06_agendados → 07_postados
```
Ordem dentro de `03_legenda_dublagem`:
1. **Legendador (04)** transcreve → `transcricao.json`.
2. **Tradutor (05)** (se estrangeiro) → `traducao.json`, e se dublado `dublagem.wav` e `mix_dublado.wav`.
3. **Narrador (06) — você** → `toque_hp.json`; com voz: `toque_hp.wav` e `mix_toque.wav`.
4. **Legendador (04)** junta tudo na legenda (`legenda.ass`/`.srt`).
5. O app move para `04_edicao`.

### 1.7 Quando usar e quando NÃO usar
**Por canal:**
| Canal | Toque HP | Voz? | Por quê |
|---|---|---|---|
| GTA 6 \| HP | **Sim, modo `texto`** | **Nunca** | Voz sintética só em Destinos, Receitas, Carros e Filmes. E o conteúdo nunca pode vir de vazamento |
| Futebol \| HP | **Sim, modo `texto`** | **Nunca** | Futebol **nunca** tem narração sintética; o áudio original do clube fica intacto |
| Filmes e Séries \| HP | Sim | Só em vídeo próprio (`voz`/`misto`); em trailer, cena e entrevista: `texto` | Não se põe voz sintética em cima de ator falando |
| Receitas \| HP | Sim | Só em vídeo próprio | — |
| Carros \| HP | Sim | Só em vídeo próprio | Valor citado leva "Valores aproximados…" |
| Destinos \| HP | Sim | Só em vídeo próprio | Valor citado leva "Valores aproximados…" |

**Modo `nenhum` (não usar Toque HP) quando:**
1. O vídeo é sobre **tragédia, morte, acidente, violência real, doença grave** — pergunta ali é desrespeito.
2. O vídeo envolve **criança** como assunto principal.
3. O assunto é **política, religião** ou algo que vire briga ofensiva nos comentários.
4. O vídeo **já abre com uma pergunta do próprio criador** nos 2 primeiros segundos (duas perguntas brigam) — aí o Toque HP fica só no fecho (`texto`, sem abertura) — ou nenhum.
5. O vídeo tem **menos de 6 s** (não cabe abertura + fecho sem tapar o conteúdo).
6. É **story**, **carrossel** ou **texto do Threads** (não é vídeo; o Redator cuida da pergunta no texto).
7. É **P0 com menos de 20 minutos** para o horário: modo `texto` só com abertura, ou nenhum.

**Sem voz (vira `texto`) mesmo nos 4 canais permitidos quando:**
- O vídeo **não é próprio** (`origem` ≠ `proprio`) — repost de criador mantém a voz do criador.
- Há **pessoa real falando** na tela no trecho em que a voz entraria.
- Não existe trecho **sem fala** de pelo menos 4 s para o trecho narrado e não há 2 s livres no fim para o fecho falado.
- `audio.voz_sintetica_permitida` ≠ `true` no pedido.

### 1.8 Quando o trabalho está pronto
- [ ] `toque_hp.json` existe, com `modo` e `motivo_modo` preenchidos.
- [ ] Abertura: começa em **0,00 s**, termina em **≤ 2,00 s**; texto da tela em no máximo 2 linhas de 20 caracteres; é uma pergunta (termina com "?").
- [ ] Fecho: nos últimos 2 a 3 s; pergunta de verdade; no máximo 1 convite neutro; nada de "isca" ("Comenta SIM", "Marca 3 amigos").
- [ ] Tudo o que é afirmado é verdade e tem fonte anotada (`fonte_do_fato`).
- [ ] Se há voz: `toque_hp.wav` (48 kHz, mono, duração do bruto ± 0,02 s) e `mix_toque.wav` (−14 LUFS ± 1, pico ≤ −1,5 dBTP); nenhuma fala do Toque por cima de outra fala.
- [ ] Registro no `historico.log` e no banco de perguntas.

---

## 2. Entradas e saídas

### 2.1 A esteira
```
H:\HypadoLocal\esteira\
├── 01_pedidos\            ← o Pauteiro larga o pedido.json (com o bloco toque_hp)
├── 02_baixados\           ← bruto.mp4 pronto
├── 03_legenda_dublagem\   ← AQUI: Legendador (04), Tradutor (05), Narrador (06)
├── 04_edicao\             ← Editor (03)
├── 05_revisao\            ← Revisor (09)
├── 06_agendados\          ← app agenda
├── 07_postados\           ← aviso "no ar"
└── 99_erros\
```

### 2.2 Nome da pasta do item
`<P0_|P1_|P2_><AAAA-MM-DD>_<HHMM>_<canal>_<apelido>`. Exemplos com Toque HP:
| Canal | Pasta | Modo do Toque |
|---|---|---|
| GTA | `P1_2026-09-30_1830_gta_rockstar-quinta` | `texto` |
| Futebol | `P0_2026-09-30_2240_futebol_gol-arrascaeta` | `texto` (só abertura e fecho escritos) |
| Filmes | `P2_2026-10-02_1200_filmes_duna-curiosidades` | `voz` (vídeo próprio de curiosidades) |
| Receitas | `P1_2026-09-30_1100_receitas_pao-sem-sovar` | `voz` |
| Carros | `P2_2026-10-01_0900_carros_suv-hibrido-imprensa` | `voz` |
| Destinos | `P1_2026-09-30_1500_destinos_cinque-terre-trilha` | `misto` (a fala dublada começa em 0,52 s) |

O Narrador **nunca** renomeia a pasta. Ordem: P0 → P1 → P2; dentro da prioridade, o horário mais cedo.

### 2.3 Arquivos da pasta que o Narrador usa
| Arquivo | Quem cria | O Narrador… |
|---|---|---|
| `pedido.json` | Pauteiro (02) | **lê** (bloco `toque_hp`, `canal`, `origem`, `audio`) |
| `bruto.mp4` | App | **lê** (assiste; tira o áudio para a mistura) |
| `transcricao.json` | Legendador (04) | **lê** (`trechos_sem_fala`, início da 1ª fala) |
| `traducao.json` | Tradutor (05) | **lê** se existir (`para_o_narrador`, tempos da dublagem) |
| `dublagem.wav` | Tradutor (05) | **lê** se existir (entra na mistura final) |
| `toque_hp.json` | **Narrador** | **cria** |
| `toque\abertura.wav`, `toque\trecho.wav`, `toque\fecho.wav` | **Narrador** (pelo `dublar.py`) | **cria** (só modo `voz`/`misto`) |
| `toque_hp.wav` | **Narrador** | **cria** (só a voz do Toque, no tempo) |
| `mix_toque.wav` | **Narrador** | **cria** (trilha final: original abaixado + todas as vozes, −14 LUFS) |
| `legenda.ass`/`.srt` | Legendador | não mexe |
| `refazer.json` | Revisor (09) | **lê** quando volta |
| `historico.log` | todos | **acrescenta** |

> **Qual trilha o Editor usa:** a mais completa que existir — `mix_toque.wav` > `mix_dublado.wav` > áudio do `bruto.mp4`. O Narrador escreve isso em `toque_hp.json → para_o_editor` (e o manual 03 deve seguir essa ordem; se não seguir, abrir ticket para alinhar).

### 2.4 Entrada: `pedido.json` (exemplo completo — Receitas, vídeo próprio, modo voz)
Formato oficial no **manual 02**; se houver diferença, vale o 02.
```json
{
  "versao": 1,
  "id": "P1_2026-09-30_1100_receitas_pao-sem-sovar",
  "prioridade": "P1",
  "criado_em": "2026-09-30T07:50:00-03:00",
  "criado_por": "pauteiro",
  "canal": "receitas",
  "conta": "@hp.receitas",
  "tipo": "reel",
  "origem": "proprio",
  "titulo_interno": "Pão sem sovar de geladeira",
  "fonte": {
    "url": "",
    "plataforma": "banco_hp",
    "criador_nome": "Imagens do banco da HP",
    "criador_arroba": "",
    "oficial": false,
    "licenca": "imagens próprias/livres de direitos",
    "trecho": {"inicio": "00:00:00.000", "fim": "00:00:30.000"}
  },
  "idioma_origem": "pt",
  "audio": {
    "tratamento": "sem_fala",
    "manter_audio_original": true,
    "voz_sintetica_permitida": true,
    "narracao_em_off": true
  },
  "legenda": {"queimar": true, "gerar_srt": true, "estilo": "hp_padrao", "posicao": "baixo"},
  "toque_hp": {
    "usar": true,
    "modo": "voz",
    "tema": "pão sem sovar, fermentação longa na geladeira",
    "fato_sugerido": "a massa fermenta de 12 a 18 horas e o glúten se desenvolve sem sovar",
    "fonte_do_fato": "roteiro da própria receita (vídeo mostra '12 h' na etiqueta do pote aos 00:05)"
  },
  "valores_citados": false,
  "publicar_em": "2026-09-30T11:00:00-03:00",
  "redes": ["instagram", "facebook", "tiktok", "youtube", "threads", "pinterest"],
  "observacoes": "Vídeo sem fala, só som ambiente. Toque HP completo com voz."
}
```
> Neste exemplo o vídeo é todo feito com imagens da própria HP, por isso o crédito fica "Imagens: HP" (o Legendador decide a linha de crédito pelo manual 04; quando o vídeo é 100% próprio, não existe @ de terceiro para creditar).

Campos que o Narrador usa:
| Campo | Para quê | Exemplo |
|---|---|---|
| `canal` | Voz permitida? Tom e banco de perguntas do canal | `receitas` |
| `origem` | Voz só em `proprio` | `proprio` |
| `audio.voz_sintetica_permitida` | Precisa ser `true` para voz | `true` |
| `audio.tratamento` | Se há fala original/dublagem (onde a voz do Toque **não** pode entrar) | `sem_fala` |
| `toque_hp.usar` | Se o Pauteiro pediu | `true` |
| `toque_hp.modo` | O modo pedido (o Narrador pode **rebaixar** de `voz` para `misto`/`texto`/`nenhum` pela regra, **nunca subir**) | `voz` |
| `toque_hp.tema` / `fato_sugerido` / `fonte_do_fato` | Ponto de partida do trecho narrado | — |
| `valores_citados` | Se alguma parte cita dinheiro → aviso | `false` |
| `publicar_em` | Prazo | — |

### 2.5 Entradas dos outros cargos (o que olhar)
- **`transcricao.json`** (manual 04): `segmentos[0].inicio` (quando começa a primeira fala: se for antes de 2,10 s, a abertura não pode ser falada) e `trechos_sem_fala` (onde cabe o trecho narrado e o fecho falado).
- **`traducao.json`** (manual 05), se existir: `dublagem.segmentos[].inicio_planejado` e `fim_real` (onde já tem voz dublada) e o recado `para_o_narrador` (ex.: "Espaço livre de voz para o fecho: de 18,30 s a 21,50 s").

### 2.6 Saída principal: `toque_hp.json` (exemplo completo — Receitas, modo voz)
Tempo em segundos, contado do início do `bruto.mp4`.
```json
{
  "versao": 1,
  "item": "P1_2026-09-30_1100_receitas_pao-sem-sovar",
  "criado_em": "2026-09-30T08:40:00-03:00",
  "canal": "receitas",
  "duracao_s": 30.000,
  "modo_pedido": "voz",
  "modo": "voz",
  "motivo_modo": "receitas + vídeo próprio + voz permitida + vídeo sem fala (0 a 30 s livres)",
  "tipo_pergunta": "experiencia",
  "modelo_banco": "receitas.experiencia.03",
  "abertura": {
    "inicio": 0.000,
    "fim": 1.850,
    "texto_tela": "Já fez pão\\Nsem sovar?",
    "texto_voz": "Já fez pão sem sovar?",
    "caracteres_tela_por_linha": [10, 10],
    "caracteres_voz": 21,
    "falada": true
  },
  "trecho": {
    "usar": true,
    "inicio": 6.200,
    "fim": 12.700,
    "texto_tela": "O segredo é o tempo: a massa descansa de 12 a 18 horas, e o glúten se forma sozinho",
    "texto_voz": "O segredo é o tempo: a massa descansa de doze a dezoito horas, e o glúten se forma sozinho.",
    "caracteres_voz": 91,
    "imagem_no_momento": "pote de massa entrando na geladeira com etiqueta '12 h' (00:05 a 00:13)",
    "fonte_do_fato": "roteiro da receita (pedido.json → toque_hp.fonte_do_fato); fermentação longa desenvolve o glúten sem sova",
    "falada": true
  },
  "fecho": {
    "inicio": 27.200,
    "fim": 30.000,
    "texto_tela": "Faria hoje?\\NSalva pra depois",
    "texto_voz": "Você faria esse pão hoje?",
    "caracteres_tela_por_linha": [11, 16],
    "caracteres_voz": 25,
    "convite": "Salva pra depois",
    "falada": true
  },
  "valores": false,
  "voz": {
    "ferramenta": "scripts\\dublar.py",
    "cps_voz": 14.0,
    "falas": [
      {"id": "abertura", "arquivo": "toque/abertura.wav", "inicio_planejado": 0.050, "duracao_estimada_s": 1.500, "duracao_real_s": 1.480, "velocidade": 1.00, "desvio_inicio_ms": 6},
      {"id": "trecho",   "arquivo": "toque/trecho.wav",   "inicio_planejado": 6.200, "duracao_estimada_s": 6.500, "duracao_real_s": 6.310, "velocidade": 1.00, "desvio_inicio_ms": 11},
      {"id": "fecho",    "arquivo": "toque/fecho.wav",    "inicio_planejado": 27.300, "duracao_estimada_s": 1.786, "duracao_real_s": 1.820, "velocidade": 1.00, "desvio_inicio_ms": 9}
    ],
    "mixagem": {
      "base": "bruto.mp4 (sem dublagem)",
      "original_normalizado_lufs": -20,
      "voz_normalizada_lufs": -16,
      "abaixamento": "sidechaincompress threshold=0.05 ratio=4 attack=15 release=450",
      "alvo_lufs": -14,
      "pico_max_dbtp": -1.5
    },
    "medicao": {
      "segmentos": 3,
      "fora_do_limite": 0,
      "limite_ms": 200,
      "desvio_max_ms": 11,
      "toque_hp_wav_duracao_s": 30.000,
      "mix_lufs_integrado": -14.1,
      "mix_pico_dbtp": -2.4,
      "sobreposicao_com_outras_falas_s": 0.0
    }
  },
  "checagem": {
    "abertura_comeca_em_0": true,
    "abertura_termina_ate_2s": true,
    "tela_max_20_por_linha": true,
    "voz_abertura_max_28": true,
    "e_pergunta": true,
    "fecho_nos_ultimos_3s": true,
    "sem_isca": true,
    "fato_com_fonte": true,
    "canal_permite_voz": true,
    "resultado": "ok"
  },
  "para_o_legendador": "Abertura e fecho no estilo Pergunta (laranja). Trecho narrado de 6,20 a 12,70 s: legenda normal com karaokê sobre toque_hp.wav.",
  "para_o_editor": "Usar mix_toque.wav como trilha (é a mais completa)."
}
```
Campos explicados:
| Campo | O que é | Regra |
|---|---|---|
| `modo_pedido` / `modo` | O que o Pauteiro pediu / o que foi feito | `modo` pode ser igual ou "menor" (voz → misto → texto → nenhum), nunca "maior" |
| `motivo_modo` | Por que esse modo | Sempre preenchido |
| `tipo_pergunta` | Tipo da pergunta (seção 2.12) | Um dos 7 tipos |
| `modelo_banco` | Qual modelo do banco de perguntas foi usado | Para o Analista (11) medir o resultado |
| `texto_tela` | O que aparece escrito (com `\N` na quebra de linha) | Máximo 2 linhas de 20 caracteres (abertura e fecho) |
| `texto_voz` | O que a voz fala | Números e siglas por extenso (`pronuncia.txt`) |
| `imagem_no_momento` | O que o vídeo mostra quando o trecho é falado | O trecho fala do que está na tela (± 1 s) |
| `fonte_do_fato` | De onde vem a informação do trecho | Obrigatório; sem fonte, sem trecho |
| `sobreposicao_com_outras_falas_s` | Quantos segundos a voz do Toque ficou por cima de outra fala | Tem que ser **0,0** |

**Exemplo em modo `texto` (GTA):**
```json
{
  "versao": 1,
  "item": "P1_2026-09-30_1830_gta_rockstar-quinta",
  "canal": "gta",
  "duracao_s": 29.500,
  "modo_pedido": "texto",
  "modo": "texto",
  "motivo_modo": "GTA: voz sintética não permitida; Toque só escrito",
  "tipo_pergunta": "reconhecimento",
  "modelo_banco": "gta.reconhecimento.02",
  "abertura": {"inicio": 0.000, "fim": 1.900, "texto_tela": "Você reconheceria\\Nessa cidade à noite?", "falada": false},
  "trecho": {"usar": false, "contexto_para_o_redator": "Trecho oficial da Rockstar mostrando Vice City à noite; GTA 6 sai em 19/11/2026."},
  "fecho": {"inicio": 26.600, "fim": 29.500, "texto_tela": "Vai jogar em 19/11?\\NComenta aí", "convite": "Comenta aí", "falada": false},
  "valores": false,
  "checagem": {"abertura_comeca_em_0": true, "abertura_termina_ate_2s": true, "tela_max_20_por_linha": true, "e_pergunta": true, "fecho_nos_ultimos_3s": true, "sem_isca": true, "sem_vazamento": true, "canal_permite_voz": false, "resultado": "ok"},
  "para_o_legendador": "Abertura e fecho no estilo Pergunta (rosa). Sem trecho narrado.",
  "para_o_editor": "Sem voz do Toque: usar a trilha do bruto (áudio original)."
}
```

### 2.7 Saídas de áudio (só modos `voz` e `misto`)
| Arquivo | Formato | Duração | Conteúdo | Volume |
|---|---|---|---|---|
| `toque\abertura.wav`, `toque\trecho.wav`, `toque\fecho.wav` | O que o `dublar.py` gera (normalmente 22 050 Hz, mono) | A da fala | Uma parte por arquivo | Pico ≤ −1 dBFS |
| `toque_hp.wav` | WAV 48 000 Hz, mono, 16 bits | Igual à do bruto ± 0,02 s | Só as falas do Toque, cada uma no seu tempo | Pico ≤ −1 dBFS |
| `mix_toque.wav` | WAV 48 000 Hz, estéreo, 16 bits | Igual à do bruto ± 0,02 s | Original abaixado + dublagem (se houver) + Toque | **−14 LUFS ± 1**, pico **≤ −1,5 dBTP** |

### 2.8 O `historico.log` (linhas do Narrador)
```
2026-09-30T08:31:00-03:00 [03] narrador: início (P1, prazo 11:00; pedido toque voz)
2026-09-30T08:31:01-03:00 [03] narrador: modo = voz (receitas, próprio, voz permitida, 0–30 s sem fala)
2026-09-30T08:38:30-03:00 [03] narrador: roteiro ok (tipo experiencia, modelo receitas.experiencia.03; abertura 21 car. voz; trecho 91 car.; fecho 25 car.; fonte do fato anotada)
2026-09-30T08:40:10-03:00 [03] narrador: toque_hp.wav montada (3 falas, desvio máx. 11 ms, 0 fora do limite)
2026-09-30T08:41:00-03:00 [03] narrador: mix_toque.wav ok (−14,1 LUFS, pico −2,4 dBTP, sobreposição 0,0 s)
2026-09-30T08:41:30-03:00 [03] narrador: fim — com o Legendador
```
Exemplos de modo rebaixado:
```
2026-09-30T22:41:00-03:00 [03] narrador: modo = texto (futebol: nunca narração sintética)
2026-09-30T10:40:00-03:00 [03] narrador: modo = misto (a fala dublada começa em 0,52 s; abertura só escrita)
2026-10-01T09:20:00-03:00 [03] narrador: modo = nenhum (vídeo sobre acidente real — pergunta seria desrespeitosa)
```

### 2.9 Entrada de volta: `refazer.json`
```json
{
  "versao": 1,
  "item": "P2_2026-10-01_0900_carros_suv-hibrido-imprensa",
  "revisor": "claude",
  "criado_em": "2026-10-01T07:40:00-03:00",
  "volta_numero": 1,
  "max_voltas": 2,
  "media": 6.6,
  "etapa_destino": "03_legenda_dublagem",
  "criterio_menor_nota": "N1_gancho",
  "nota_criterio": 5,
  "motivo": "A abertura 'Olha só esse carro!' não é pergunta e é genérica; a pergunta só aparece em 2,6 s.",
  "o_que_fazer": "Trocar por pergunta específica que caiba em 2 s (ex.: 'Você pagaria isso nele?') e refazer a voz da abertura."
}
```
- Corrija só o apontado; se o texto mudou, avise o Legendador (a legenda muda junto).
- Renomeie para `refazer_1_feito.json`; na volta 2 que falhar: `99_erros`.

### 2.10 Arquivos de apoio
| Arquivo | Onde | Para quê | Situação |
|---|---|---|---|
| `scripts\dublar.py` | `G:\Meu Drive\Hypado\scripts\` | Única porta para a voz (Piper pt-BR) | (existente) |
| `config\voz.json` | `G:\Meu Drive\Hypado\06 Projeto\app\config\` | Modelo, opções do `dublar.py`, velocidade medida | (a criar — feito no manual 05, passos 4 a 9) |
| `dicionarios\pronuncia.txt` | `G:\Meu Drive\Hypado\06 Projeto\app\dicionarios\` | Como a voz fala siglas, números e nomes | (a criar — o mesmo do manual 05) |
| Banco de perguntas | `G:\Meu Drive\Hypado\06 Projeto\app\config\perguntas_<canal>.json` | Modelos de abertura e fecho que já funcionaram, com os números | (a criar) |
| Lista de proibidos | `G:\Meu Drive\Hypado\06 Projeto\app\config\toque_proibidos.txt` | Palavras e temas que o Toque nunca usa (iscas, temas sensíveis) | (a criar) |
| Roteiro de montagem | `H:\HypadoLocal\app\provisorio\montar_faixa.py` com `--tipo toque` | Monta `toque_hp.wav` e mede o desvio | (provisório — texto completo no manual 05, seção 8.7) |

Exemplo de banco de perguntas (`perguntas_receitas.json`, a criar). O **Analista de resultados (manual 11)** atualiza os números toda semana; o app escolhe primeiro os modelos com mais comentários por mil visualizações.
```json
{
  "versao": 1,
  "canal": "receitas",
  "atualizado_em": "2026-09-28",
  "regra_de_escolha": "maior comentarios_por_mil entre os ativos com usos >= 3; não repetir o mesmo modelo no canal em 7 dias",
  "modelos": [
    {"id": "receitas.experiencia.03", "tipo": "experiencia", "abertura": "Já fez {prato} {jeito}?", "fecho_tela": "Faria hoje?\\NSalva pra depois", "fecho_voz": "Você faria {prato} hoje?", "usos": 9, "comentarios_por_mil": 4.1, "retencao_3s": 0.72, "ativo": true},
    {"id": "receitas.escolha.01", "tipo": "escolha", "abertura": "{opcao_a} ou {opcao_b}?", "fecho_tela": "Qual você prefere?\\NComenta aí", "fecho_voz": "Qual você prefere?", "usos": 6, "comentarios_por_mil": 5.3, "retencao_3s": 0.69, "ativo": true},
    {"id": "receitas.desafio.02", "tipo": "desafio", "abertura": "Consegue fazer\\Nem {minutos} minutos?", "fecho_tela": "Topa o desafio?\\NConta aí", "fecho_voz": "Topa o desafio?", "usos": 4, "comentarios_por_mil": 2.2, "retencao_3s": 0.64, "ativo": true},
    {"id": "receitas.numero.01", "tipo": "numero", "abertura": "Quanto sai\\Nessa receita?", "fecho_tela": "Achou barato?\\NComenta aí", "fecho_voz": "Achou barato?", "usos": 2, "comentarios_por_mil": 3.0, "retencao_3s": 0.70, "ativo": true}
  ]
}
```
> Os números acima são **exemplos do formato**, não resultados reais. Os reais vêm do manual 11.

Exemplo de `toque_proibidos.txt` (a criar):
```
# iscas de engajamento (as redes rebaixam)
comenta sim
comente sim
curte se
curta se
marca 3 amigos
marca um amigo que
compartilha se
compartilhe se
digita 1
# promessas falsas / apelação
você não vai acreditar
ninguém sabe disso
o final vai te chocar
proibido
# temas que nunca viram pergunta
morte
acidente
tragédia
político
religião
# GTA
vazou
vazamento
leak
build de teste
```

### 2.11 O padrão HP do Toque (a especificação)
| Item | Padrão HP | Por quê |
|---|---|---|
| **Abertura — tempo** | Aparece no **quadro 1 (0,00 s)** e some em **≤ 2,00 s** | Os 2 primeiros segundos decidem se a pessoa fica |
| Abertura — tela | Estilo `Pergunta` (manual 04): 72 px, branco numa caixa da cor do canal, topo; **máximo 2 linhas de 20 caracteres** | Leitura em 1 olhada |
| Abertura — voz | **No máximo 28 caracteres** (≈ 2,0 s a 14 caracteres/s); começa **até 0,15 s** depois do início | Tem que terminar dentro dos 2 s |
| Abertura — conteúdo | **Pergunta** (termina com "?"), **específica** do vídeo (tem um substantivo do vídeo: "pão", "praia", "Vice City"), de 3 a 8 palavras | "Você sabia?" genérico não segura ninguém |
| Abertura — tela x voz | Dizem **a mesma pergunta**; a tela pode ter um detalhe a mais (um número), a voz pode ser mais curta | Coerência sem estourar o tempo |
| **Trecho — tempo** | De **4 a 12 s** de fala; começa **depois de 3,0 s**; só em trecho **sem fala** (0,3 s de folga antes e depois); termina **pelo menos 1 s antes** do fecho | Não brigar com a abertura, com a fala original nem com o fecho |
| Trecho — tamanho | 1 a 3 frases; **50 a 160 caracteres** de voz; frases de até 20 palavras | Cabe e respira |
| Trecho — conteúdo | **Um fato** verificável que ajuda a entender o vídeo, com fonte anotada; falando do que **aparece na tela naquele momento** (± 1 s); no máximo 1 número principal | Contexto, não opinião |
| Trecho — tom | Neutro, informativo. Sem "incrível", "inacreditável", "surreal", "você não vai acreditar" | É a "voz neutra" da HP |
| **Fecho — tempo** | Começa entre **duração − 3,0 s** e **duração − 2,0 s**; termina até **duração − 0,2 s** (tela até o fim) | Última coisa que a pessoa vê |
| Fecho — tela | Estilo `Pergunta`; máximo 2 linhas de 20 caracteres | — |
| Fecho — voz | **No máximo 40 caracteres** (≈ 2,8 s) | Cabe nos últimos 3 s |
| Fecho — conteúdo | Pergunta **de verdade** (opinião, escolha, experiência) + **no máximo 1** convite neutro: "Comenta aí", "Conta aí", "Salva pra depois" | Puxa comentário sem ser isca |
| Fecho — proibido | "Comenta SIM", "Curte se…", "Marca 3 amigos", "Compartilha se…", "Digita 1" | As redes rebaixam "isca de engajamento" |
| **Voz** | Só Piper pt-BR, pelo `scripts\dublar.py`; velocidade **1,00** (aceito **0,95 a 1,10**); sem efeito nenhum (nada de eco, grave, agudo) | "Voz neutra" = a voz padrão, sem enfeite |
| Nível da voz | −16 LUFS antes da mistura (igual à dublagem) | Mesma voz, mesmo volume em tudo |
| Mistura | Mesma receita do manual 05 (original a −20 LUFS, abaixamento automático, final a −14 LUFS) | Coerência |
| Sobreposição | **0,0 s** de voz do Toque por cima de qualquer outra fala (original ou dublada) | Duas vozes juntas = ninguém entende |
| Valores | Se falar de dinheiro: aviso "Valores aproximados…" na tela (o Legendador põe) | Regra da empresa |
| Repetição | O mesmo modelo de pergunta **não se repete** no mesmo canal em 7 dias | O público percebe e cansa |

### 2.12 Os 7 tipos de pergunta (e como escrever cada um)
| Tipo | Fórmula | Bom exemplo | Exemplo ruim (e por quê) |
|---|---|---|---|
| **Experiência** | "Já fez/foi/viu {coisa específica}?" | "Já fez pão sem sovar?" | "Já fez isso?" (genérico) |
| **Escolha (A ou B)** | "{A} ou {B}?" | "Lucia ou Jason?" · "Praia ou montanha?" | "Qual é melhor?" (sem as opções) |
| **Opinião / julgamento** | "{Coisa} vale/foi {x}?" | "Foi pênalti ou não foi?" · "Vale R$ 190 mil?" | "O que acham?" (vago) |
| **Aposta / previsão** | "Quem/quando/vai {x}?" | "Vai jogar em 19/11?" · "Quem leva o clássico?" | "Será que vai?" (sem sujeito) |
| **Número / palpite** | "Quanto {custa/pesa/demora} {coisa}?" (o vídeo responde) | "Quanto custa uma noite aqui?" | "Quanto você acha?" (de quê?) |
| **Reconhecimento** | "Sabe/reconhece {lugar/cena}?" | "Sabe que praia é essa?" · "Reconheceu essa cena?" | "Sabe o que é?" (vago) |
| **Desafio leve** | "Consegue {x} em {tempo}?" | "Consegue fazer em 10 minutos?" | "Duvido você fazer!" (provocação) |

**Regras para qualquer tipo:**
1. Tem **substantivo do vídeo** (a pessoa entende do que se trata sem ver o resto).
2. O vídeo **responde ou dá contexto** para a pergunta de abertura — nunca prometer o que o vídeo não mostra.
3. Nunca pergunta sobre **aparência, corpo, dinheiro pessoal ou vida privada** de alguém.
4. Nunca pergunta que incentive **ofensa** a torcida, time, árbitro, grupo de pessoas.
5. Nunca **spoiler** de filme/série de estreia (menos de 30 dias do lançamento no Brasil).
6. Nunca afirmação disfarçada de pergunta com informação falsa ("Sabia que o GTA 6 vai ter X?" quando X não é oficial).

### 2.13 Roteiros por canal (com exemplos)
> **Importante:** os trechos narrados abaixo mostram o **formato** (tamanho, tom, estrutura). No vídeo real, **cada fato precisa de fonte** (material oficial, site oficial, a própria imagem do vídeo) anotada em `fonte_do_fato` — sem fonte, o trecho não entra (vira modo sem trecho). Os limites de caracteres já estão conferidos: toda linha de tela tem no máximo 20.

#### 2.13.1 GTA 6 | HP — modo `texto` (sempre)
- **Tom:** empolgado, de fã para fã, contagem para 19/11/2026.
- **Regras do canal:** **nunca voz**; **nada de vazamento** (nem citar que existe); só material e informação **oficial** da Rockstar; nada de "trailer puro" (o Toque HP é parte do que transforma o vídeo). Sempre "GTA 6".
- **Aberturas (tela, ≤ 2 linhas de 20):**
  1. "Você reconheceria\Nessa cidade à noite?" (reconhecimento)
  2. "Lucia ou Jason?" (escolha)
  3. "Vai jogar\Nno lançamento?" (aposta)
  4. "Viu esse detalhe\Nde Vice City?" (reconhecimento)
  5. "Quanto falta\Npro GTA 6?" (número — o vídeo mostra a contagem)
  6. "PS5 ou esperar\No PC?" (escolha — só se o vídeo for sobre plataformas oficiais)
- **Contexto (vai para o Redator, não é narrado):** "Imagens oficiais da Rockstar; GTA 6 chega em 19/11/2026 para PS5 e Xbox Series X|S."
- **Fechos:**
  1. "Vai jogar em 19/11?\NComenta aí"
  2. "Com quem você fica?\NComenta aí"
  3. "Qual detalhe você viu?\N..." → **não** (23 caracteres na 1ª linha); certo: "Que detalhe viu?\NConta aí"
  4. "Pré-venda ou espera?\NComenta aí"
  5. "Nota de 0 a 10?\NComenta aí"
- **Nunca:** "Vazou gameplay?", "Sabia que no GTA 6 vai ter…?" (com informação não oficial), "Rockstar escondeu isso?" (teoria como fato).

**Roteiro completo (GTA, 29,5 s, material oficial em inglês com legenda traduzida):**
| Tempo | Parte | Tela | Voz |
|---|---|---|---|
| 0,00–1,90 | Abertura | "Você reconheceria / essa cidade à noite?" | — (sem voz) |
| 0,41–5,87 | (fala original legendada) | legenda do Legendador | áudio original da Rockstar |
| 26,60–29,50 | Fecho | "Vai jogar em 19/11? / Comenta aí" | — |

#### 2.13.2 Futebol | HP — modo `texto` (sempre)
- **Tom:** torcedor bem informado, provocação **saudável**, sem ofensa.
- **Regras do canal:** **nunca narração sintética** (nem na abertura, nem no fecho); **áudio original do clube sempre**; nada de imagem de transmissão de TV; no modo "gol" do `reel_futebol.py` (a criar), a abertura escrita entra **no cartão de 2 s** do início (o Editor posiciona) e não pode tapar o placar; transferência só se **oficial** (anunciada pelo clube).
- **Aberturas:**
  1. "Foi pênalti\Nou não foi?" (opinião)
  2. "Golaço ou\Nfrango?" (escolha — só se o lance for mesmo discutível)
  3. "Quem leva\No clássico?" (aposta)
  4. "Viu esse passe\Ndo Arrascaeta?" (reconhecimento)
  5. "Quantos gols\Nele fez no ano?" (número — o vídeo mostra)
  6. "Melhor gol\Nda rodada?" (opinião)
- **Fechos:**
  1. "Acertou o placar?\NComenta aí"
  2. "Nota pro gol?\NComenta aí"
  3. "Quem foi o melhor?\NComenta aí"
  4. "E o seu time?\NConta aí"
  5. "Vai ser campeão?\NComenta aí"
- **Nunca:** "Juiz ladrão?", "Torcida X é a pior?", qualquer coisa sobre aparência/vida pessoal de jogador, "Fulano vai para o clube Y?" sem anúncio oficial, pergunta sobre briga ou violência.

**Roteiro completo (Futebol, gol oficial do clube, 24 s, com cartão de 2 s do Editor):**
| Tempo (no vídeo final) | Parte | Tela | Voz |
|---|---|---|---|
| 0,00–2,00 | Abertura (no cartão) | "Viu esse passe / do Arrascaeta?" | **nenhuma** (áudio original do vídeo do clube a partir de 2,00 s) |
| 2,00–21,00 | Vídeo oficial do clube | caixa do `posts_futebol.py legenda_video` + crédito "Vídeo: @clube" | áudio original |
| 21,00–24,00 | Fecho | "Nota pro gol? / Comenta aí" | — |
> Tempo no vídeo final: como o Editor põe o cartão de 2 s **antes** do vídeo do clube, tudo o que vem do bruto anda 2 s para frente (o Editor desloca a legenda — manual 03). No `toque_hp.json`, marque `"no_cartao": true` na abertura.

#### 2.13.3 Filmes e Séries | HP — `voz` só em vídeo próprio; `texto` em trailer, cena e entrevista
- **Tom:** cinéfilo curioso, sem pedantismo; **sem spoiler** de estreia.
- **Aberturas:**
  1. "Você viu esse\Ndetalhe no filme?" (reconhecimento)
  2. "Reconheceu\Nessa cena?" (reconhecimento)
  3. "Filme ou série:\Nqual foi melhor?" (escolha)
  4. "Sabe quanto\Ncustou essa cena?" (número — o vídeo responde)
  5. "Já viu no\Ncinema?" (experiência)
  6. "Duna ou\NDuna: Parte Dois?" (escolha)
- **Trechos narrados (só vídeo próprio):**
  1. "Essa cena foi gravada no deserto da Jordânia, sem tela verde para o fundo." (fato de bastidor com fonte: entrevista oficial/making of)
  2. "O diretor pediu que o elenco não visse o roteiro inteiro antes de gravar." (só com fonte oficial citável)
  3. "A trilha sonora foi gravada antes das filmagens, e os atores ouviam no set." (idem)
- **Fechos:**
  1. "Qual cena te pegou?\NComenta aí"
  2. "Nota de 0 a 10?\NComenta aí"
  3. "Vê de novo?\NSalva pra depois"
  4. "Qual filme vem agora?\N..." → **não** (21 caracteres); certo: "Qual vem agora?\NComenta aí"
- **Nunca:** revelar final/virada de filme ou série com menos de 30 dias; voz sintética por cima de ator falando; título em inglês quando existe o brasileiro.

**Roteiro completo (Filmes, vídeo próprio de curiosidades, 35 s, modo voz):**
| Tempo | Parte | Tela | Voz |
|---|---|---|---|
| 0,00–1,80 | Abertura | "Você viu esse / detalhe no filme?" | "Você viu esse detalhe?" (22 car.) |
| 4,50–10,80 | Trecho | legenda com karaokê | "Essa cena foi gravada no deserto da Jordânia, sem tela verde para o fundo." (74 car. ≈ 5,3 s) |
| 32,20–35,00 | Fecho | "Qual cena te pegou? / Comenta aí" | "Qual cena te pegou?" (19 car.) |

#### 2.13.4 Receitas | HP — `voz` em vídeo próprio; `texto` em repost de criador
- **Tom:** amigo que cozinha bem, prático, acolhedor.
- **Regras do canal:** medidas brasileiras; nada de promessa de saúde ("emagrece", "cura", "desintoxica"); preço de ingrediente → "Valores aproximados…".
- **Aberturas:**
  1. "Já fez pão\Nsem sovar?" (experiência)
  2. "Doce ou\Nsalgado?" (escolha)
  3. "Consegue fazer\Nem 10 minutos?" (desafio)
  4. "Quanto sai\Nessa receita?" (número)
  5. "Airfryer ou\Nforno?" (escolha)
  6. "Sabe o segredo\Ndesse bolo fofo?" (reconhecimento — o trecho responde)
- **Trechos narrados:**
  1. "O segredo é o tempo: a massa descansa de doze a dezoito horas, e o glúten se forma sozinho."
  2. "Clara em neve dobrada com cuidado é o que deixa o bolo alto e fofinho."
  3. "Selar a carne em fogo alto antes de assar dá cor e sabor por fora."
- **Fechos:**
  1. "Faria hoje?\NSalva pra depois"
  2. "Qual você prefere?\NComenta aí"
  3. "Topa o desafio?\NConta aí"
  4. "Já tem tudo aí?\NSalva pra depois"
  5. "Que nota você dá?\NComenta aí"
- **Nunca:** "Essa receita emagrece?", "Cura gripe?", pergunta que culpe quem erra a receita.

**Roteiro completo (Receitas, vídeo próprio, 30 s, modo voz):** o do exemplo da seção 2.6.

#### 2.13.5 Carros | HP — `voz` em vídeo próprio (ex.: material de imprensa da montadora); `texto` em review de criador
- **Tom:** entusiasta que entende de número, direto.
- **Regras do canal:** unidades brasileiras (km/h, cv, km/l); **todo preço → "Valores aproximados…"**; dado técnico só da montadora ou de teste citável ("segundo a montadora"); nada de incentivar racha ou excesso de velocidade.
- **Aberturas:**
  1. "Você pagaria\NR$ 190 mil nele?" (opinião + número; valor = aviso) — voz curta: "Você pagaria isso nele?"
  2. "Elétrico ou\Nhíbrido?" (escolha)
  3. "Sabe quanto ele\Nfaz por litro?" (número — o trecho responde)
  4. "SUV ou\Nsedã?" (escolha)
  5. "Já dirigiu\Num elétrico?" (experiência)
  6. "Reconhece esse\Nclássico?" (reconhecimento)
- **Trechos narrados:**
  1. "Segundo a montadora, esse híbrido faz cerca de dezessete quilômetros por litro na cidade." (valor técnico com fonte)
  2. "O motor elétrico entra sozinho nas saídas e nas baixas velocidades, e o de combustão assume na estrada."
  3. "A bateria carrega até oitenta por cento em cerca de trinta minutos num carregador rápido, segundo a fabricante."
- **Fechos:**
  1. "Compraria ou não?\NComenta aí"
  2. "Vale o preço?\NComenta aí" (com aviso de valores se o preço apareceu)
  3. "Qual você leva?\NComenta aí"
  4. "Nota pro design?\NComenta aí"
  5. "Troca o seu?\NConta aí"
- **Nunca:** "Quanto ele faz de 0 a 200 na rua?", pergunta que incentive dirigir perigosamente, número técnico sem fonte.

**Roteiro completo (Carros, vídeo próprio com material de imprensa, 28 s, modo voz, com preço):**
| Tempo | Parte | Tela | Voz |
|---|---|---|---|
| 0,00–1,80 | Abertura | "Você pagaria / R$ 190 mil nele?" + aviso "Valores aproximados…" | "Você pagaria isso nele?" (23 car.) |
| 5,00–11,60 | Trecho | legenda com karaokê | "Segundo a montadora, esse híbrido faz cerca de dezessete quilômetros por litro na cidade." (89 car. ≈ 6,4 s) |
| 25,20–28,00 | Fecho | "Compraria ou não? / Comenta aí" | "Compraria ou não?" (17 car.) |
> O preço e o consumo aqui são **exemplos de formato**. No vídeo real, o número vem do material oficial citado no pedido.

#### 2.13.6 Destinos | HP — `voz` em vídeo próprio; `texto` em repost de criador
- **Tom:** amigo viajante, inspirador e prático.
- **Regras do canal:** nome do lugar com acento certo; **preço de ingresso, diária, passagem → "Valores aproximados…"**; estação do ano "de lá" quando for outro hemisfério; nada de incentivar invadir área proibida ou arriscar a vida por foto.
- **Aberturas:**
  1. "Conhece a praia\Nmais azul do Brasil?" (reconhecimento — o vídeo mostra qual)
  2. "Praia ou\Nmontanha?" (escolha)
  3. "Iria sozinho\Nou com alguém?" (escolha)
  4. "Quanto custa\Numa noite aqui?" (número — o trecho responde, com aviso)
  5. "Já viu esse\Npôr do sol?" (experiência)
  6. "Sabe onde\Nfica isso?" (reconhecimento)
- **Trechos narrados:**
  1. "As Cinque Terre são cinco vilas na costa da Itália, ligadas por uma trilha de uns doze quilômetros."
  2. "Em Jericoacoara, o pôr do sol é visto do alto da duna, e o vento forte da tarde é o que atrai os kitesurfistas."
  3. "Uma das melhores épocas para ver os balões da Capadócia é de abril a junho, com o tempo mais estável de manhã."
- **Fechos:**
  1. "Iria ou passaria?\NConta aí"
  2. "Com quem você iria?\NConta aí"
  3. "Já foi pra lá?\NConta aí"
  4. "Vai pra lista?\NSalva pra depois"
  5. "Nota pro lugar?\NComenta aí"
- **Nunca:** "Marca quem vai com você" (isca de marcação), pergunta que incentive foto em lugar perigoso, preço sem aviso.

**Roteiro completo (Destinos, vídeo próprio dublado em italiano, 21,5 s, modo `misto`):**
| Tempo | Parte | Tela | Voz |
|---|---|---|---|
| 0,00–1,90 | Abertura | "Conhece as vilas / da Trilha Azul?" | **nenhuma** (a fala dublada começa em 0,52 s) |
| 0,52–18,14 | Falas dubladas (manual 05) | legenda com karaokê | voz dublada |
| — | Trecho | não usado (não há 4 s livres de fala) | — |
| 18,60–21,30 | Fecho | "Iria ou passaria? / Conta aí" | "Iria ou passaria?" (17 car.) |

---

## 3. Passo a passo numerado (para leigo)

> **Como usar:** faça na ordem. Cada passo diz o que abrir, o que rodar, o que conferir e o que deve aparecer. Copie o comando inteiro, cole no PowerShell (botão direito cola) e aperte **Enter**.
> Passos 1 a 7: **uma vez só**. Dia a dia: a partir do 8.
> **[APP]** = o app fará sozinho quando o módulo da etapa 3 existir (a criar). **[CLAUDE]** = julgamento (escrever a pergunta e o fato).
> **Modo `texto`** (GTA, Futebol, repost): passos 8 a 38 e depois 54 a 58. **Modo `voz`/`misto`**: todos.

### Fase A — Preparar o PC (uma vez só)

**Passo 1 — Abrir o PowerShell.** Menu Iniciar → `PowerShell` → **Windows PowerShell**. Deve aparecer `PS C:\Users\...>`.

**Passo 2 — Criar os atalhos da sessão** (cole toda vez que abrir o PowerShell):
```powershell
$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
$ff = "H:\HypadoLocal\ferramentas\ffmpeg\bin\ffmpeg.exe"
$scripts = "G:\Meu Drive\Hypado\scripts"
$dublar = "G:\Meu Drive\Hypado\scripts\dublar.py"
$esteira = "H:\HypadoLocal\esteira"
$prov = "H:\HypadoLocal\app\provisorio"
$cfg = "G:\Meu Drive\Hypado\06 Projeto\app\config"
$dic = "G:\Meu Drive\Hypado\06 Projeto\app\dicionarios"
```
- Conferir: `Test-Path $py; Test-Path $ff; Test-Path $dublar; Test-Path $esteira` → quatro `True`.

**Passo 3 — Conferir a voz e o `config\voz.json`.**
```powershell
Get-Content "$cfg\voz.json" -Encoding UTF8
```
- Deve aparecer: o modelo da voz, os nomes das opções do `dublar.py` e o `cps_medido` (ex.: 14.0).
- Se o arquivo não existir: faça os passos 4 a 9 do **manual 05** (é o mesmo arquivo, a mesma voz).

**Passo 4 — Conferir a lista de pronúncia.** `Test-Path "$dic\pronuncia.txt"` → `True`. Se `False`, crie com o exemplo da seção 2.10 do manual 05.

**Passo 5 — Conferir o banco de perguntas (a criar).**
```powershell
Get-ChildItem $cfg -Filter "perguntas_*.json" | Select-Object Name
```
- Deve aparecer: 6 arquivos (`perguntas_gta.json`, `perguntas_futebol.json`, `perguntas_filmes.json`, `perguntas_receitas.json`, `perguntas_carros.json`, `perguntas_destinos.json`).
- Se faltarem: crie cada um no formato da seção 2.10, com 4 a 6 modelos tirados da seção 2.13 do canal (sem números de resultado ainda: `"usos": 0`, `"comentarios_por_mil": null`).

**Passo 6 — Conferir a lista de proibidos (a criar).** `Test-Path "$cfg\toque_proibidos.txt"` → `True`. Se `False`, crie com o exemplo da seção 2.10 (UTF-8).

**Passo 7 — Conferir o roteiro de montagem com a opção do Toque.**
```powershell
& $py "$prov\montar_faixa.py" --help
```
- Deve aparecer: a ajuda com a opção `--tipo {dublagem,toque}`.
- Se não existir ou não tiver `--tipo`: copie a versão da seção 8.7 do **manual 05** (é o mesmo arquivo, serve aos dois manuais).

### Fase B — Pegar o item certo

**Passo 8 — Conferir o horário.** `Get-Date -Format "HH:mm"`
- Entre **18:00 e 22:29**: pode **escrever** o Toque (passos 9 a 38, leves), mas **não** gerar voz, montar nem mixar (passos 39 a 53), nem para P0.

**Passo 9 — Achar os itens que pedem Toque HP e ainda não têm.**
```powershell
Get-ChildItem "$esteira\03_legenda_dublagem" -Directory | Sort-Object Name | ForEach-Object {
  $p = Get-Content "$($_.FullName)\pedido.json" -Raw -Encoding UTF8 | ConvertFrom-Json
  if ($p.toque_hp.usar) {
    "{0}  modo_pedido={1}  transcricao={2}  traducao={3}  toque={4}" -f $_.Name, $p.toque_hp.modo, (Test-Path "$($_.FullName)\transcricao.json"), (Test-Path "$($_.FullName)\traducao.json"), (Test-Path "$($_.FullName)\toque_hp.json")
  }
}
```
- Pegue o **primeiro** com `toque=False` e `transcricao=True`. Se o vídeo for estrangeiro (`idioma_origem` ≠ `pt`), espere também `traducao=True`.

**Passo 10 — Entrar na pasta.**
```powershell
$item = "$esteira\03_legenda_dublagem\P1_2026-09-30_1100_receitas_pao-sem-sovar"
Set-Location $item; Get-ChildItem | Select-Object Name, Length
```

**Passo 11 — Ler o pedido.** `Get-Content pedido.json -Encoding UTF8` — anote: `canal`, `origem`, `audio.voz_sintetica_permitida`, `audio.tratamento`, `toque_hp` (modo, tema, fato sugerido, fonte), `valores_citados`, `publicar_em`.

**Passo 12 — Ver quando começa a primeira fala e onde não tem fala.**
```powershell
$tr = Get-Content transcricao.json -Raw -Encoding UTF8 | ConvertFrom-Json
"duracao: {0}" -f $tr.duracao_s
if ($tr.segmentos.Count -gt 0) { "primeira fala em: {0}" -f $tr.segmentos[0].inicio } else { "sem fala no vídeo" }
$tr.trechos_sem_fala | ForEach-Object { "sem fala: {0} a {1} ({2:N2} s)" -f $_.inicio, $_.fim, ($_.fim - $_.inicio) }
```
- Deve aparecer: a duração, quando começa a primeira fala e a lista de trechos sem fala.

**Passo 13 — Se houver dublagem, ver onde a voz dublada já está.**
```powershell
if (Test-Path traducao.json) {
  $td = Get-Content traducao.json -Raw -Encoding UTF8 | ConvertFrom-Json
  "decisao: {0}" -f $td.decisao.modo
  $td.para_o_narrador
  if ($td.dublagem) { $td.dublagem.segmentos | ForEach-Object { "fala dublada {0}: {1} a {2}" -f $_.id, $_.inicio_planejado, $_.fim_real } }
}
```
- Com dublagem, os trechos "sem fala" de verdade são os que também não têm voz dublada. O recado `para_o_narrador` já diz onde há espaço.

**Passo 14 — Ver se é volta do Revisor.** `if (Test-Path refazer.json) { Get-Content refazer.json -Encoding UTF8 } else { "primeira passada" }`
| Critério | Vá para o passo |
|---|---|
| `N1_gancho`, `N2_limites` | 24–28 |
| `N3_verdade` | 29–31 |
| `N4_trecho` | 29–32 |
| `N5_fecho` | 33–35 |
| `N6_voz` | 42–44 |
| `N7_tempos` | 45–47 |
| `N8_mistura` | 49–52 |
| `N10_canal` | 36 |

### Fase C — Decidir o modo [APP]

**Passo 15 — Canal.** `gta` ou `futebol` → modo **`texto`** (sem voz, sem trecho). Anote e pule para o passo 23.

**Passo 16 — Vídeo próprio e voz permitida.** `origem` ≠ `proprio` **ou** `voz_sintetica_permitida` ≠ `true` → **`texto`**.

**Passo 17 — Tema sensível ou vídeo curto (modo `nenhum`).** Assista ao vídeo (`Invoke-Item bruto.mp4`). Se for tragédia, morte, acidente, violência real, doença grave, criança como assunto principal, política, religião, ou se o vídeo tiver **menos de 6 s**, ou já abrir com pergunta do criador → **`nenhum`** (ou só fecho). Escreva o motivo e pule para o passo 54.

**Passo 18 — Prazo.** P0 com menos de 20 minutos para `publicar_em` → **`texto`** só com abertura (ou `nenhum`).

**Passo 19 — Pessoa real falando na tela?** Se no trecho em que a voz do Toque entraria alguém aparece falando para a câmera, a voz **não** entra ali (procure outro trecho; se não houver, sem trecho).

**Passo 20 — A abertura pode ser falada?** Primeira fala (original ou dublada) começa **antes de 2,10 s** → abertura **só escrita** → modo **`misto`** (se o trecho e/ou o fecho puderem ser falados) ou `texto`.

**Passo 21 — Existe lugar para o trecho narrado?** Procure, na lista do passo 12 (e sem voz dublada, passo 13), um trecho sem fala que:
- comece **depois de 3,0 s**;
- tenha pelo menos **4,6 s** (4 s de fala + 0,3 s de folga de cada lado);
- termine **pelo menos 1 s antes** do fecho.
Não existe? → sem trecho (`trecho.usar = false`), o contexto vai para o Redator.

**Passo 22 — Existe lugar para o fecho falado?** Os últimos 3 s do vídeo precisam estar **sem fala**. Se não estiverem, o fecho fica **só escrito**.
- Registre a decisão:
```powershell
Add-Content -Path historico.log -Encoding UTF8 -Value "$(Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz') [03] narrador: modo = voz (receitas, próprio, voz permitida, 0–30 s sem fala)"
```

### Fase D — Escrever o Toque [CLAUDE]

**Passo 23 — Assistir ao vídeo inteiro, com som, e anotar "a coisa mais interessante".**
- Pergunte: "o que faz alguém parar de rolar aqui?" (o lugar, o preço, o gol, o detalhe escondido, o truque da receita).
- Anote também **em que segundo** as coisas importantes aparecem (vai precisar no trecho).

**Passo 24 — Olhar o banco de perguntas do canal.**
```powershell
$banco = Get-Content "$cfg\perguntas_receitas.json" -Raw -Encoding UTF8 | ConvertFrom-Json
$banco.modelos | Where-Object { $_.ativo } | Sort-Object comentarios_por_mil -Descending | Select-Object id, tipo, abertura, fecho_tela, usos, comentarios_por_mil | Format-Table -AutoSize
```
- Deve aparecer: os modelos do canal, do que mais dá comentário para o que menos dá.
- Prefira o **primeiro da lista** que combine com o vídeo e que **não** foi usado no canal nos últimos 7 dias (procure o `modelo_banco` nos `toque_hp.json` dos itens da última semana em `07_postados`).
- Nenhum combina? Escreva uma pergunta nova pelos 7 tipos da seção 2.12 e, depois, acrescente-a ao banco como modelo novo (`"usos": 0`).

**Passo 25 — Escrever a abertura (tela).**
- Regras: pergunta; específica (tem substantivo do vídeo); 3 a 8 palavras; **no máximo 2 linhas de 20 caracteres** (`\N` separa as linhas).
- Contar os caracteres (troque o texto):
```powershell
"Já fez pão".Length; "sem sovar?".Length
```
- Deve aparecer: `10` e `10` (cada linha ≤ 20).

**Passo 26 — Escrever a abertura (voz)**, só nos modos `voz` com abertura falada.
- Mesma pergunta, **no máximo 28 caracteres**, números e siglas por extenso (`pronuncia.txt`).
- Ex.: tela "Você pagaria\NR$ 190 mil nele?" → voz "Você pagaria isso nele?" (23). Por extenso ("cento e noventa mil reais") daria 44 caracteres ≈ 3,1 s: **não cabe**.
```powershell
"Você pagaria isso nele?".Length
```

**Passo 27 — Testar a abertura com a pergunta-guia.** "Se eu visse só isso, pararia de rolar? Dá para entender do que o vídeo trata?" Se a resposta for "não", troque.
- Ruins → bons: "Olha isso!" → "Já viu esse pôr do sol?"; "Você sabia?" → "Sabe quanto custa uma noite aqui?"; "Incrível!" → "Golaço ou frango?".

**Passo 28 — Conferir que o vídeo responde à abertura.** Se a abertura pergunta "Quanto custa uma noite aqui?", o vídeo (ou o trecho) tem que dizer o valor — com aviso "Valores aproximados…". Se não diz, troque a pergunta (senão vira promessa falsa).

**Passo 29 — Escrever o trecho narrado** (só se o passo 21 achou lugar).
- **Um fato** que ajuda a entender o que aparece na tela **naquele momento**. Ponto de partida: `toque_hp.fato_sugerido` do pedido.
- 1 a 3 frases, **50 a 160 caracteres**, tom neutro, no máximo 1 número principal.
- Texto da tela (vai para a legenda com karaokê): números em algarismo. Texto da voz: por extenso.
- Ex. (Receitas): tela "O segredo é o tempo: a massa descansa de 12 a 18 horas, e o glúten se forma sozinho"; voz "O segredo é o tempo: a massa descansa de doze a dezoito horas, e o glúten se forma sozinho."

**Passo 30 — Conferir o fato e anotar a fonte [BLOQUEIA sem fonte].**
- De onde veio? A própria imagem do vídeo, o material oficial citado no pedido, o site oficial (Rockstar, clube, montadora, órgão de turismo), a ficha técnica oficial.
- Escreva em `trecho.fonte_do_fato`. **Sem fonte = sem trecho.** Nunca "ouvi dizer", nunca rumor, nunca vazamento.

**Passo 31 — Encaixar o trecho no tempo.**
- Duração estimada = caracteres da voz ÷ `cps_medido` (ex.: 91 ÷ 14 = **6,5 s**).
- Escolha o início dentro do trecho sem fala do passo 21, **alinhado com a imagem** de que ele fala (ex.: começa em 6,20 s, quando o pote entra na geladeira).
- Início + duração + 0,3 s tem que caber antes da próxima fala e 1 s antes do fecho.
- Não cabe? Enxugue (tire enfeite, troque palavra longa) ou corte uma frase.

**Passo 32 — Ler o trecho em voz alta.** Soa neutro? Tem "incrível", "surreal", "você não vai acreditar"? Tire. Tem opinião ("o melhor do mundo")? Troque por fato ("o mais visitado do país, segundo o órgão de turismo").

**Passo 33 — Escrever o fecho (tela e voz).**
- Tela: pergunta de verdade + no máximo 1 convite neutro ("Comenta aí", "Conta aí", "Salva pra depois"); 2 linhas de até 20 caracteres.
- Voz (se falado): a pergunta, **no máximo 40 caracteres**.
- Ex.: tela "Faria hoje?\NSalva pra depois"; voz "Você faria esse pão hoje?" (25).

**Passo 34 — Tempo do fecho.** Começa entre **duração − 3,0 s** e **duração − 2,0 s** (ex.: vídeo de 30,0 s → entre 27,0 e 28,0 s). A tela fica até o fim; a voz termina até **duração − 0,2 s**.

**Passo 35 — Procurar isca e palavra proibida.** (Depois de gravar o `toque_hp.json` no passo 37, rode:)
```powershell
$t = Get-Content toque_hp.json -Raw -Encoding UTF8 | ConvertFrom-Json
$tudo = (@($t.abertura.texto_tela, $t.abertura.texto_voz, $t.trecho.texto_tela, $t.trecho.texto_voz, $t.fecho.texto_tela, $t.fecho.texto_voz) -join " ").ToLower()
Get-Content "$cfg\toque_proibidos.txt" -Encoding UTF8 | Where-Object { $_ -and -not $_.StartsWith("#") } | Where-Object { $tudo.Contains($_.ToLower()) }
```
- Deve aparecer: **nada**. Se aparecer alguma palavra, reescreva a parte que a contém.

**Passo 36 — Conferência do canal.**
| Canal | Conferir |
|---|---|
| GTA | Sem voz; "GTA 6"; **nada** de vazamento nem teoria como fato; só informação oficial |
| Futebol | Sem voz; nada de ofensa a time, torcida ou árbitro; transferência só se oficial; não tapar placar |
| Filmes | Sem spoiler de estreia (< 30 dias); título brasileiro; sem voz por cima de ator |
| Receitas | Sem promessa de saúde; medidas brasileiras |
| Carros | Preço → aviso de valores; dado técnico com fonte; nada que incentive velocidade na rua |
| Destinos | Preço → aviso; nada que incentive risco por foto; estação "de lá" quando for outro hemisfério |

**Passo 37 — Gravar o `toque_hp.json`** (Bloco de Notas, UTF-8) no modelo da seção 2.6 (modo `voz`/`misto`) ou do exemplo em modo `texto`. No modo `texto`, preencha `trecho.contexto_para_o_redator` com o fato (o Redator usa no texto do post).
```powershell
& $py -m json.tool toque_hp.json | Out-Null; if ($LASTEXITCODE -eq 0) { "JSON OK" } else { "JSON QUEBRADO" }
```
- Deve aparecer: `JSON OK`.

**Passo 38 — Conferir os limites com números.**
```powershell
$t = Get-Content toque_hp.json -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($p in "abertura", "fecho") { ($t.$p.texto_tela -split '\\N') | ForEach-Object { "{0,-9} tela {1,2} car.: {2}" -f $p, $_.Length, $_ } }
if ($t.abertura.texto_voz) { "abertura voz: {0} car. (máx. 28)" -f $t.abertura.texto_voz.Length }
if ($t.trecho.usar) { "trecho voz: {0} car. (50 a 160)" -f $t.trecho.texto_voz.Length }
if ($t.fecho.texto_voz) { "fecho voz: {0} car. (máx. 40)" -f $t.fecho.texto_voz.Length }
"abertura: {0} a {1} s (tem que ser 0 e no máx. 2)" -f $t.abertura.inicio, $t.abertura.fim
"fecho: {0} a {1} s (duração {2})" -f $t.fecho.inicio, $t.fecho.fim, $t.duracao_s
```
- Deve aparecer: todas as linhas de tela com **≤ 20**, a voz da abertura **≤ 28**, o trecho entre **50 e 160**, o fecho **≤ 40**, abertura de **0** a **≤ 2**, fecho começando entre duração − 3 e duração − 2.
- Modo `texto`: termine aqui e vá para o passo 54.

### Fase E — Gerar a voz [APP] (modos `voz` e `misto`)

**Passo 39 — Horário e trava.**
```powershell
Get-Date -Format "HH:mm"; if (Test-Path "H:\HypadoLocal\app\pesado.lock") { Get-Content "H:\HypadoLocal\app\pesado.lock" } else { "livre" }
```
- Fora de 18:00–22:29 e `livre`. Senão, espere.

**Passo 40 — Gerar as falas com o `dublar.py`** (troque `OPCAO_TEXTO` e `OPCAO_SAIDA` pelos nomes exatos anotados no `voz.json`):
```powershell
New-Item -ItemType Directory -Force "$item\toque" | Out-Null
$t = Get-Content toque_hp.json -Raw -Encoding UTF8 | ConvertFrom-Json
if ($t.abertura.falada) { & $py $dublar OPCAO_TEXTO $t.abertura.texto_voz OPCAO_SAIDA "$item\toque\abertura.wav" }
if ($t.trecho.usar -and $t.trecho.falada) { & $py $dublar OPCAO_TEXTO $t.trecho.texto_voz OPCAO_SAIDA "$item\toque\trecho.wav" }
if ($t.fecho.falada) { & $py $dublar OPCAO_TEXTO $t.fecho.texto_voz OPCAO_SAIDA "$item\toque\fecho.wav" }
Get-ChildItem "$item\toque" | Select-Object Name, Length
```
- Deve aparecer: um `.wav` para cada parte falada.

**Passo 41 — Medir a duração de cada fala.**
```powershell
Get-ChildItem "$item\toque\*.wav" | ForEach-Object {
  $d = (& $ff -hide_banner -i $_.FullName 2>&1 | Select-String "Duration: ([\d:.]+)").Matches[0].Groups[1].Value
  "{0}  {1}" -f $_.Name, $d
}
```
- Limites: `abertura.wav` **≤ 1,95 s** (começa em 0,05 e tem que acabar até 2,00); `trecho.wav` **≤ o espaço** escolhido no passo 31; `fecho.wav` **≤ 2,8 s**.

**Passo 42 — Ouvir cada fala.** `Invoke-Item "$item\toque\abertura.wav"` (e as outras). Conferir: leu o texto exato; a pergunta **sobe no fim** (entonação de pergunta); pronúncia certa; sem corte, estalo ou chiado.

**Passo 43 — Corrigir pronúncia.** Palavra lida errado → acrescente na `pronuncia.txt` (ex.: `Riomaggiore = Riomadjôre`) e gere de novo só aquela parte (passo 40, uma linha).

**Passo 44 — Pergunta sem entonação de pergunta?** A voz sintética às vezes lê a pergunta "reta". Tente: (1) pergunta mais curta; (2) começar com palavra de pergunta ("Você…", "Qual…", "Já…"); (3) terminar com "?" colado na palavra. Se continuar reta, a fala ainda é aceitável (nota 7 em N6) — não use efeito de voz para "consertar" (proibido).

**Passo 45 — Ajustar a velocidade da fala que não coube** (limite do Toque: **0,95 a 1,10**, mais estreito que a dublagem, porque a voz do Toque é a "cara" da HP).
- Velocidade = duração real ÷ espaço. Ex.: abertura de 2,10 s para 1,95 s → 1,08. Permitido.
```powershell
& $ff -hide_banner -loglevel error -y -i "$item\toque\abertura.wav" -af "atempo=1.08" "$item\toque\abertura_r.wav"
Move-Item -Force "$item\toque\abertura_r.wav" "$item\toque\abertura.wav"
```
- Precisou de mais que 1,10? Encurte o texto (passos 26, 29 ou 33).

**Passo 46 — Preencher o bloco `voz.falas` no `toque_hp.json`** com, para cada parte falada: `id` (`abertura`, `trecho`, `fecho`), `arquivo` (`toque/abertura.wav`…), `inicio_planejado` (abertura **0,05**; trecho = o do passo 31; fecho = início do fecho + 0,10), `duracao_estimada_s`, `duracao_real_s`, `velocidade`. Parte não falada: `"arquivo": null`. Confira com o comando do passo 37 (`JSON OK`).

**Passo 47 — Montar a faixa do Toque.**
```powershell
& $py "$prov\montar_faixa.py" --item $item --tipo toque
```
- Deve aparecer: `OK: 3 falas; desvio max 11 ms; 0 fora do limite de 200 ms`.
- O roteiro grava `toque_hp.wav` (48 kHz, mono, duração do vídeo) e as medidas em `toque_hp.json → voz.medicao`.

**Passo 48 — Conferir que a voz do Toque não cai em cima de outra fala.**
- Compare os tempos: cada fala do Toque (`inicio_planejado` até `inicio_planejado + duracao_real_s`) **não pode cruzar** nenhum segmento de fala original (`transcricao.json`) nem fala dublada (`traducao.json → dublagem.segmentos`, de `inicio_planejado` a `fim_real`), com 0,15 s de folga.
- Anote `sobreposicao_com_outras_falas_s` = **0,0** em `voz.medicao`. Se não for 0, mude o início do trecho ou encurte o texto e remonte.

### Fase F — Misturar a trilha final [APP]

**Passo 49 — Fazer a trilha `mix_toque.wav`.**
- **Sem dublagem** (vídeo sem fala ou com fala original):
```powershell
& $ff -hide_banner -loglevel error -y -i bruto.mp4 -i toque_hp.wav -filter_complex "[0:a]aresample=48000,loudnorm=I=-20:TP=-2:LRA=11,aresample=48000[orig];[1:a]aresample=48000,loudnorm=I=-16:TP=-2:LRA=11,aresample=48000,asplit=2[voz][sc];[orig][sc]sidechaincompress=threshold=0.05:ratio=4:attack=15:release=450[fundo];[fundo][voz]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]" -map "[a]" -ac 2 -c:a pcm_s16le mix_toque.wav
```
- **Com dublagem** (existe `dublagem.wav` do manual 05 — as duas vozes são somadas e tratadas como uma só, para ficarem no mesmo volume):
```powershell
& $ff -hide_banner -loglevel error -y -i bruto.mp4 -i dublagem.wav -i toque_hp.wav -filter_complex "[1:a][2:a]amix=inputs=2:duration=first:normalize=0[vozes];[0:a]aresample=48000,loudnorm=I=-20:TP=-2:LRA=11,aresample=48000[orig];[vozes]aresample=48000,loudnorm=I=-16:TP=-2:LRA=11,aresample=48000,asplit=2[voz][sc];[orig][sc]sidechaincompress=threshold=0.05:ratio=4:attack=15:release=450[fundo];[fundo][voz]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]" -map "[a]" -ac 2 -c:a pcm_s16le mix_toque.wav
```
- Deve aparecer: nada (sem erro) e o arquivo `mix_toque.wav`.
- Se o vídeo **não tem som nenhum** (sem faixa de áudio no bruto — veja o passo 17 do manual 04): use só a voz: `& $ff -hide_banner -loglevel error -y -i toque_hp.wav -af "aresample=48000,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000" -ac 2 -c:a pcm_s16le mix_toque.wav`.

**Passo 50 — Medir o volume.**
```powershell
& $ff -hide_banner -nostats -i mix_toque.wav -af ebur128=peak=true -f null - 2>&1 | Select-String "^\s+I:|^\s+Peak:"
```
- Aceito: **I entre −15,0 e −13,0 LUFS**; **Peak ≤ −1,5**.

**Passo 51 — Acertar o volume** (se precisar). Correção = −14 − I (ex.: I = −15,2 → `volume=1.2dB`):
```powershell
& $ff -hide_banner -loglevel error -y -i mix_toque.wav -af "volume=1.2dB" -c:a pcm_s16le mix_ajustado.wav
& $ff -hide_banner -nostats -i mix_ajustado.wav -af ebur128=peak=true -f null - 2>&1 | Select-String "^\s+I:|^\s+Peak:"
```
- Se `I` ≈ −14,0 e `Peak` ≤ −1,5: `Move-Item -Force mix_ajustado.wav mix_toque.wav`. Se o pico passar de −1,5, não suba: aceite o I entre −15 e −13.

**Passo 52 — Prévia com vídeo.**
```powershell
& $ff -hide_banner -loglevel error -y -i bruto.mp4 -i mix_toque.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 160k -shortest previa_toque.mp4
Invoke-Item previa_toque.mp4
```

**Passo 53 — Assistir e conferir.**
- [ ] A pergunta de abertura é **a primeira coisa** que se ouve (em até 0,15 s).
- [ ] A abertura termina antes de 2 s.
- [ ] O trecho fala do que aparece na tela naquele momento.
- [ ] Nenhuma voz por cima de outra.
- [ ] O som original continua por trás e volta nas pausas.
- [ ] O fecho está nos últimos 3 s e soa como pergunta.
- [ ] Volume confortável (celular e fone).

### Fase G — Entregar

**Passo 54 — Histórico com números.**
```powershell
Add-Content -Path historico.log -Encoding UTF8 -Value "$(Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz') [03] narrador: fim — modo voz; abertura 21 car. (0,05–1,53 s); trecho 91 car.; fecho 25 car.; mix -14,1 LUFS; sobreposição 0,0 s"
```

**Passo 55 — Recados para o Legendador e o Editor.** Confira em `toque_hp.json` os campos `para_o_legendador` (cor, estilo, tempos) e `para_o_editor` (qual trilha usar). Não é preciso mandar mensagem.

**Passo 56 — Limpar.** Apague `mix_ajustado.wav` (se sobrou). **Mantenha** até a postagem: `toque_hp.json`, `toque\`, `toque_hp.wav`, `mix_toque.wav`, `previa_toque.mp4`. Se era volta: `Rename-Item refazer.json refazer_1_feito.json`.

**Passo 57 — Deu errado: `99_erros`.** Crie `erro.json` (modelo do manual 04, passo 62, com `"cargo": "narrador"`) e mova a pasta: `Set-Location $esteira; Move-Item $item "$esteira\99_erros\"`.
- Atenção: se o problema for **só da voz**, rebaixe para modo **`texto`** (abertura e fecho escritos) em vez de travar o item — e anote o motivo.

**Passo 58 — Problema que se repete: ticket.** `scripts\tickets.py` (existente; veja o `--help`), área do app. Ex.: "voz lê perguntas sem entonação", "banco de perguntas sem números do Analista há 2 semanas". Nada de senha, token ou dado pessoal.
