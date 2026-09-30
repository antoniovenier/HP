# Manual 05 — Tradutor e dublador

> **Hypado (HP) · HP Studio · Manuais dos cargos**
> Versão 1.0 · 30/09/2026 · Situação: **rascunho para revisão** (passa a valer depois de revisado e de 7 dias em modo sombra).
> Ler junto com: **01 Curador** (decide se o vídeo é "próprio" e se pode ter voz), **02 Pauteiro** (monta o `pedido.json`), **03 Editor** (usa a trilha mixada no vídeo final), **04 Legendador** (transcreve antes de você e legenda depois de você), **06 Narrador "Toque HP"** (usa a mesma voz e as mesmas regras de pronúncia) e **09 Revisor de qualidade** (dá a nota).
> Vale para os 6 perfis: **GTA 6 | HP**, **Futebol | HP**, **Filmes e Séries | HP**, **Receitas | HP**, **Carros | HP** e **Destinos | HP** — mas a **dublagem** só existe em 4 deles (Destinos, Receitas, Carros e Filmes) e só em vídeo próprio.

**Resumo em 6 linhas (para quem tem pressa):**
1. Quando o vídeo não está em português, o Tradutor transforma a fala em **português do Brasil natural**, adaptado (medidas, moedas, títulos, gírias) — **nunca palavra por palavra**.
2. Primeiro decide, por regra fixa: **legendar** (padrão, vale para todos os canais) ou **dublar** (só Destinos, Receitas, Carros e Filmes, só vídeo próprio, só narração em off).
3. Grava tudo em `traducao.json` (texto da legenda, texto da voz, tempos).
4. Se for dublar: gera a voz **só** com a voz Piper pt-BR gratuita já instalada, **pelo `scripts\dublar.py`** — nunca outra voz, **nunca clonar voz de ninguém**.
5. Encaixa cada frase no tempo da fala original, monta `dublagem.wav` e mistura com o áudio original **abaixado** → `mix_dublado.wav` a **−14 LUFS**.
6. Anota tudo no `historico.log`; o Legendador (04) faz a legenda em cima do seu texto; o item segue para `04_edicao`.

**Marcadores:** **(a criar)** = ainda não existe, está descrito para quem for programar; **(existente)** = já funciona no PC do Antônio, só usar; **[BLOQUEIA]** = regra inviolável — se quebrar, o item não sai.

---

## 1. Objetivo do cargo

### 1.1 Em uma frase
Fazer um brasileiro entender e **curtir** um vídeo que foi feito em outra língua, como se ele tivesse sido feito aqui: com frases naturais, medidas e valores que ele entende, nomes certos e — quando a regra permitir — uma voz em português clara, no tempo certo e com o som original baixinho por trás.

### 1.2 Por que isso importa para a HP
- Muito do melhor conteúdo de GTA (Rockstar), de filmes (estúdios), de carros (montadoras), de receitas e de viagens nasce em inglês, espanhol, italiano, japonês. Quem traz isso **bem traduzido e primeiro** para o Brasil ganha seguidor.
- Tradução ruim (literal, com "1 cup", "350 °F", "0 a 60 mph") faz o brasileiro rolar o vídeo ou comentar deboche. Tradução adaptada faz ele salvar e compartilhar — e **salvamento e compartilhamento** são o que mais empurra o vídeo no algoritmo, rumo à monetização.
- A dublagem com voz neutra transforma um vídeo estrangeiro de paisagem ou de receita num **vídeo próprio da HP em português**, que prende quem não gosta de ler legenda.
- As regras de voz existem para proteger a empresa: voz sintética mal usada (no futebol, imitando alguém, em cima de pessoa real falando) gera denúncia, perda de confiança e risco de conta.

### 1.3 O que o Tradutor e dublador FAZ
1. Confere o idioma do vídeo (junto com a transcrição do Legendador, manual 04).
2. Decide **legendar ou dublar** pela tabela fixa da seção 1.6.
3. Traduz com **adaptação**: sentido, tom, gíria, medidas, moedas, títulos brasileiros, nomes oficiais.
4. Ajusta o tamanho do texto para caber: na legenda (22 caracteres por linha, 17 caracteres por segundo) e na voz (a frase falada tem que caber no tempo da original).
5. Escreve `traducao.json` com o texto da legenda, o texto da voz e os tempos.
6. Se for dublar: prepara o "texto para a voz" (números e siglas por extenso), gera a voz pelo `scripts\dublar.py`, encaixa cada frase no tempo, monta `dublagem.wav`, mistura com o original abaixado (`mix_dublado.wav`) e mede o volume final (−14 LUFS).
7. Confere tudo com números e anota no `historico.log`.

### 1.4 O que o Tradutor e dublador NÃO FAZ
| Não faz | Quem faz | Manual |
|---|---|---|
| Escolher o vídeo e dizer se é "próprio" | Curador | 01 |
| Montar o `pedido.json` | Pauteiro | 02 |
| Transcrever a fala original | Legendador | 04 |
| Montar os blocos da legenda e o arquivo `.ass` | Legendador | 04 |
| Escrever a pergunta de abertura/fecho | Narrador "Toque HP" | 06 |
| Pôr música, montar o `final.mp4`, queimar a legenda | Editor | 03 |
| Escrever o texto do post (com a tradução do título, hashtags) | Redator | 08 |
| Dar nota e aprovar | Revisor | 09 |

### 1.5 Onde fica na esteira
```
01_pedidos → 02_baixados → [03_legenda_dublagem] → 04_edicao → 05_revisao → 06_agendados → 07_postados
```
Ordem dentro de `03_legenda_dublagem` (todos na mesma pasta do item):
1. **Legendador (04)** transcreve → `transcricao.json` (no idioma original, com tempo por palavra).
2. **Tradutor e dublador (05) — você** → `traducao.json` e, se permitido, `dublagem.wav` + `mix_dublado.wav`.
3. **Narrador (06)** → `toque_hp.json` (e `toque_hp.wav` se tiver voz).
4. **Legendador (04)** junta tudo → `legenda.ass` e `legenda.srt`.
5. O app move a pasta para `04_edicao`.

### 1.6 A grande decisão: legendar ou dublar
**Regra geral: na dúvida, LEGENDA.** Dublar só quando **todas** as 6 condições forem verdade:

| # | Condição | Onde conferir | Se não for verdade |
|---|---|---|---|
| 1 | Canal é **Destinos, Receitas, Carros ou Filmes** | `pedido.json → canal` | Legenda (GTA e Futebol **nunca** dublam) |
| 2 | Vídeo é **próprio** da HP | `pedido.json → origem` = `"proprio"` (decidido pelo Curador) | Legenda (vídeo de criador é repostado com a voz dele) |
| 3 | O pedido permite voz sintética | `audio.voz_sintetica_permitida` = `true` | Legenda |
| 4 | A voz original é **narração em off** (narrador que não aparece falando) | Olhar o vídeo: ninguém mexe a boca na tela enquanto a voz fala | Legenda (**nunca** pôr voz sintética em cima de pessoa real falando na tela) |
| 5 | A fala cabe no tempo (seção 2.12: no máximo 15% mais rápida) | Cálculo do passo 38 | Legenda, ou pedir ao Claude para enxugar o texto |
| 6 | Não é P0 com prazo menor que 40 minutos | Nome da pasta e `publicar_em` | Legenda agora (dá para republicar dublado depois, se valer a pena) |

**Resumo por canal:**
| Canal | Estrangeiro de criador/fonte oficial | Vídeo próprio com narração em off estrangeira | Entrevista / pessoa real falando |
|---|---|---|---|
| GTA 6 \| HP | Legenda traduzida | Legenda traduzida (GTA não tem voz sintética) | Legenda traduzida |
| Futebol \| HP | Legenda traduzida + **áudio original sempre** | Legenda traduzida (futebol **nunca** tem narração sintética) | Legenda traduzida |
| Filmes e Séries \| HP | Legenda traduzida | **Pode dublar** | Legenda traduzida |
| Receitas \| HP | Legenda traduzida | **Pode dublar** | Legenda traduzida |
| Carros \| HP | Legenda traduzida | **Pode dublar** | Legenda traduzida |
| Destinos \| HP | Legenda traduzida | **Pode dublar** | Legenda traduzida |

> **O que é "vídeo próprio" (para este manual):** vídeo que a HP monta com material que tem direito de usar (imagens livres de direitos, material oficial de divulgação com uso permitido e crédito, gravação cedida) e cuja narração passa a ser da HP. Quem marca `origem: "proprio"` é o **Curador** (manual 01). O Tradutor **nunca** muda esse campo. Repost de vídeo de criador (com crédito) **não** é vídeo próprio, mesmo que a HP ponha legenda e Toque HP.

### 1.7 Quando o trabalho está pronto
- [ ] `traducao.json` existe, com `decisao.modo` preenchido (`legenda` ou `dublagem`) e o motivo.
- [ ] Todo segmento da `transcricao.json` tem tradução (mesmos `id`, nenhum faltando).
- [ ] Toda linha de legenda planejada cabe em 22 caracteres por linha e 17 caracteres por segundo.
- [ ] Medidas, moedas, títulos e nomes adaptados pela tabela da seção 2.11; valor citado marcado para o aviso "Valores aproximados…".
- [ ] Se dublagem: `dublagem.wav` (48 kHz, mono, do tamanho do bruto ± 20 ms) e `mix_dublado.wav` (−14 LUFS ± 1, pico ≤ −1,5 dBTP) existem; cada frase começa a no máximo 200 ms do planejado; velocidade entre 0,85 e 1,15.
- [ ] `historico.log` com as linhas `[03] tradutor:` e os números.

---

## 2. Entradas e saídas

### 2.1 A esteira (visão geral)
```
H:\HypadoLocal\esteira\
├── 01_pedidos\            ← o Claude/Pauteiro larga o pedido.json; o app baixa sozinho
├── 02_baixados\           ← bruto.mp4 pronto
├── 03_legenda_dublagem\   ← AQUI: Legendador (04), Tradutor e dublador (05), Narrador (06)
├── 04_edicao\             ← Editor (03) monta o final.mp4
├── 05_revisao\            ← Revisor (09): aprovado.json ou refazer.json
├── 06_agendados\          ← app agenda (TikTok espera tiktok_ok.json)
├── 07_postados\           ← aviso "no ar"
└── 99_erros\              ← problemas para gente olhar
```

### 2.2 Nome da pasta do item
`<P0_|P1_|P2_><AAAA-MM-DD>_<HHMM>_<canal>_<apelido>` — ex.: `P1_2026-09-30_1500_destinos_cinque-terre-trilha`.
- `P0_` urgente/ao vivo (fura a fila) · `P1_` do dia · `P2_` programado.
- O Tradutor **nunca** renomeia a pasta.
- Ordem de trabalho: P0 → P1 → P2; dentro da mesma prioridade, o horário de postagem mais cedo.

Exemplos de itens que passam pelo Tradutor:
| Canal | Pasta | Idioma | Decisão |
|---|---|---|---|
| GTA | `P1_2026-09-30_1830_gta_rockstar-quinta` | en | Legenda |
| Futebol | `P1_2026-10-01_1200_futebol_real-madrid-treino` | es | Legenda (áudio original) |
| Filmes | `P2_2026-10-02_1200_filmes_duna-bastidores` | en | Legenda (entrevista) |
| Receitas | `P1_2026-09-30_1100_receitas_focaccia-italiana` | it | Dublagem (vídeo próprio, narração em off) |
| Carros | `P2_2026-10-01_0900_carros_eletrico-japones` | ja | Dublagem (vídeo próprio com material de imprensa, narração em off) |
| Destinos | `P1_2026-09-30_1500_destinos_cinque-terre-trilha` | it | Dublagem (vídeo próprio, narração em off) |

### 2.3 Arquivos da pasta que o Tradutor usa
| Arquivo | Quem cria | O Tradutor… |
|---|---|---|
| `pedido.json` | Pauteiro (02) | **lê** (nunca altera) |
| `bruto.mp4` | App | **lê** (tira o áudio original para a mixagem) |
| `transcricao.json` | Legendador (04) | **lê** (só começa quando `"revisado": true`) |
| `traducao.json` | **Tradutor** | **cria** |
| `dublagem\seg_001.wav`, `seg_002.wav`… | **Tradutor** (pelo `dublar.py`) | **cria** (uma fala por arquivo; apagadas no fim) |
| `dublagem.wav` | **Tradutor** | **cria** (só a voz, no tempo certo) |
| `mix_dublado.wav` | **Tradutor** | **cria** (voz + original abaixado, −14 LUFS) |
| `previa_dublagem.mp4` | **Tradutor** | **cria** (conferência; apagada depois da revisão) |
| `legenda.ass` / `.srt` | Legendador (04) | não mexe |
| `toque_hp.*` | Narrador (06) | não mexe |
| `refazer.json` | Revisor (09) | **lê** quando o item volta |
| `historico.log` | todos | **acrescenta linhas** |

### 2.4 Entrada: `pedido.json` (exemplo completo — Destinos, vídeo próprio dublado)
O formato oficial é o do **manual 02 (Pauteiro)**; se houver diferença, vale o 02.
```json
{
  "versao": 1,
  "id": "P1_2026-09-30_1500_destinos_cinque-terre-trilha",
  "prioridade": "P1",
  "criado_em": "2026-09-30T09:40:00-03:00",
  "criado_por": "pauteiro",
  "canal": "destinos",
  "conta": "@hp.destinos",
  "tipo": "reel",
  "origem": "proprio",
  "titulo_interno": "Cinque Terre: a trilha azul entre 5 vilas",
  "fonte": {
    "url": "https://www.youtube.com/watch?v=EXEMPLO0002",
    "plataforma": "youtube",
    "criador_nome": "Turismo Exemplo (fictício)",
    "criador_arroba": "@exemplo.turismo",
    "oficial": true,
    "licenca": "material de divulgação; uso permitido com crédito",
    "trecho": {"inicio": "00:00:05.000", "fim": "00:00:26.500"}
  },
  "idioma_origem": "it",
  "audio": {
    "tratamento": "dublagem",
    "manter_audio_original": true,
    "voz_sintetica_permitida": true,
    "narracao_em_off": true
  },
  "legenda": {"queimar": true, "gerar_srt": true, "estilo": "hp_padrao", "posicao": "baixo"},
  "toque_hp": {"usar": true, "modo": "voz"},
  "valores_citados": true,
  "cotacao": {"moeda": "EUR", "reais": 6.30, "data": "2026-09-30", "fonte": "informada pelo Pauteiro"},
  "publicar_em": "2026-09-30T15:00:00-03:00",
  "redes": ["instagram", "facebook", "tiktok", "youtube", "threads", "pinterest"],
  "observacoes": "Narração em off em italiano. Dublar com a voz padrão. Ingresso citado: pôr aviso de valores."
}
```
> O valor da cotação acima é só um exemplo. A cotação de verdade vem do Pauteiro (ou do Antônio) no dia; o Tradutor **nunca inventa** cotação. Sem `cotacao` no pedido, o valor fica na moeda original ("cerca de € 15") e leva o aviso do mesmo jeito.

Campos que o Tradutor usa:
| Campo | Para quê | Exemplo |
|---|---|---|
| `canal` | Condição 1 da dublagem; glossário do canal | `destinos` |
| `origem` | Condição 2 (`proprio` x `criador`) | `proprio` |
| `idioma_origem` | Idioma de partida (confere com a transcrição) | `it` |
| `audio.tratamento` | O que o Pauteiro pediu: `legenda_traduzida` ou `dublagem` | `dublagem` |
| `audio.voz_sintetica_permitida` | Condição 3 | `true` |
| `audio.narracao_em_off` | Condição 4 (o Tradutor **confere no vídeo**) | `true` |
| `audio.manter_audio_original` | Sempre `true` na HP: o original fica por baixo | `true` |
| `valores_citados` / `cotacao` | Aviso de valores e conversão de moeda | `true` / `{...}` |
| `toque_hp.modo` | Se o Narrador também vai usar a voz (mesma voz, mesmo volume) | `voz` |
| `publicar_em` | Condição 6 (prazo) | `2026-09-30T15:00:00-03:00` |

> **Se o pedido pedir `dublagem` e alguma condição da seção 1.6 falhar**, o Tradutor **não dubla**: faz legenda, escreve o motivo em `traducao.json → decisao` e no histórico. Se o motivo for de regra (futebol, GTA, pessoa real na tela), é **[BLOQUEIA]** para a dublagem — o item segue só com legenda.

### 2.5 Entrada: `transcricao.json` (do Legendador)
Formato completo no manual 04, seção 2.5. O Tradutor usa: `idioma_detectado`, `segmentos[].id`, `inicio`, `fim`, `texto`, `palavras` (para saber onde a pessoa respira) e `trechos_sem_fala` (onde cabe voz sem atrapalhar). Trecho do exemplo em italiano:
```json
{
  "item": "P1_2026-09-30_1500_destinos_cinque-terre-trilha",
  "duracao_s": 21.500,
  "idioma_detectado": "it",
  "prob_idioma": 0.99,
  "revisado": true,
  "segmentos": [
    {"id": 1, "inicio": 0.520, "fim": 4.100, "texto": "Le Cinque Terre sono cinque borghi sospesi tra mare e montagna."},
    {"id": 2, "inicio": 4.600, "fim": 9.300, "texto": "Il Sentiero Azzurro collega Monterosso a Riomaggiore: circa dodici chilometri."},
    {"id": 3, "inicio": 9.800, "fim": 12.400, "texto": "Il biglietto costa circa quindici euro al giorno."},
    {"id": 4, "inicio": 13.000, "fim": 16.200, "texto": "In primavera, i limoni profumano tutta la costa."}
  ],
  "trechos_sem_fala": [{"inicio": 0.000, "fim": 0.520}, {"inicio": 16.200, "fim": 21.500}]
}
```

### 2.6 Saída principal: `traducao.json` (exemplo completo)
```json
{
  "versao": 1,
  "item": "P1_2026-09-30_1500_destinos_cinque-terre-trilha",
  "criado_em": "2026-09-30T10:32:00-03:00",
  "idioma_origem": "it",
  "idioma_destino": "pt-BR",
  "duracao_s": 21.500,
  "tradutor": "claude",
  "decisao": {
    "modo": "dublagem",
    "condicoes": {
      "canal_permitido": true,
      "origem_proprio": true,
      "voz_permitida": true,
      "narracao_em_off": true,
      "cabe_no_tempo": true,
      "prazo_ok": true
    },
    "motivo": "Destinos + vídeo próprio + narração em off; as 6 condições ok"
  },
  "glossario_usado": "glossario_destinos.txt",
  "segmentos": [
    {
      "id": 1, "inicio": 0.520, "fim": 4.100,
      "original": "Le Cinque Terre sono cinque borghi sospesi tra mare e montagna.",
      "literal": "As Cinco Terras são cinco burgos suspensos entre mar e montanha.",
      "legenda": "As Cinque Terre são cinco vilas entre o mar e a montanha",
      "voz": "As Cinque Terre são cinco vilas entre o mar e a montanha.",
      "notas": "Nome do lugar mantido em italiano (é como aparece nos guias brasileiros). 'Borghi sospesi' virou 'vilas entre' (natural em pt-BR).",
      "valor": false
    },
    {
      "id": 2, "inicio": 4.600, "fim": 9.300,
      "original": "Il Sentiero Azzurro collega Monterosso a Riomaggiore: circa dodici chilometri.",
      "literal": "O Caminho Azul liga Monterosso a Riomaggiore: cerca de doze quilômetros.",
      "legenda": "A Trilha Azul liga Monterosso a Riomaggiore: uns 12 km",
      "voz": "A Trilha Azul liga Monterosso a Riomaggiore: uns doze quilômetros.",
      "notas": "'Sentiero' = trilha. Número em algarismo na legenda, por extenso na voz.",
      "valor": false
    },
    {
      "id": 3, "inicio": 9.800, "fim": 12.400,
      "original": "Il biglietto costa circa quindici euro al giorno.",
      "literal": "O bilhete custa cerca de quinze euros por dia.",
      "legenda": "Ingresso: cerca de € 15 por dia (≈ R$ 95)",
      "voz": "Ingresso: cerca de quinze euros por dia.",
      "notas": "Enxugado para caber na janela de 3,05 s. Conversão com a cotação do pedido (6,30): 15 x 6,30 = 94,50 → ≈ R$ 95. Aviso de valores obrigatório.",
      "valor": true
    },
    {
      "id": 4, "inicio": 13.000, "fim": 16.200,
      "original": "In primavera, i limoni profumano tutta la costa.",
      "literal": "Na primavera, os limões perfumam toda a costa.",
      "legenda": "Na primavera de lá (março a junho), os limões perfumam a costa",
      "voz": "Na primavera de lá, de março a junho, os limões perfumam toda a costa.",
      "notas": "Adaptação de hemisfério: a primavera europeia é março-junho; no Brasil é setembro-dezembro.",
      "valor": false
    }
  ],
  "conversoes": [
    {"segmento": 2, "de": "dodici chilometri", "para_legenda": "12 km", "para_voz": "doze quilômetros"},
    {"segmento": 3, "de": "quindici euro", "para_legenda": "€ 15 (≈ R$ 95)", "para_voz": "quinze euros", "cotacao": 6.30},
    {"segmento": 4, "de": "primavera", "para_legenda": "primavera de lá (março a junho)", "para_voz": "primavera de lá, de março a junho"}
  ],
  "dublagem": {
    "ferramenta": "scripts\\dublar.py",
    "voz": "Piper pt-BR (o modelo já instalado; nome em config\\voz.json)",
    "cps_voz": 14.0,
    "margem_entre_falas_s": 0.15,
    "segmentos": [
      {"id": 1, "arquivo": "dublagem/seg_001.wav", "texto_voz": "As Cinque Terre são cinco vilas entre o mar e a montanha.", "caracteres": 57, "inicio_planejado": 0.520, "janela_s": 3.930, "duracao_estimada_s": 4.071, "duracao_real_s": 3.880, "velocidade": 1.00, "fim_real": 4.400, "desvio_inicio_ms": 14},
      {"id": 2, "arquivo": "dublagem/seg_002.wav", "texto_voz": "A Trilha Azul liga Monterosso a Riomaggiore: uns doze quilômetros.", "caracteres": 66, "inicio_planejado": 4.600, "janela_s": 5.050, "duracao_estimada_s": 4.714, "duracao_real_s": 4.620, "velocidade": 1.00, "fim_real": 9.220, "desvio_inicio_ms": 9},
      {"id": 3, "arquivo": "dublagem/seg_003.wav", "texto_voz": "Ingresso: cerca de quinze euros por dia.", "caracteres": 40, "inicio_planejado": 9.800, "janela_s": 3.050, "duracao_estimada_s": 2.857, "duracao_real_s": 2.910, "velocidade": 1.00, "fim_real": 12.710, "desvio_inicio_ms": 21},
      {"id": 4, "arquivo": "dublagem/seg_004.wav", "texto_voz": "Na primavera de lá, de março a junho, os limões perfumam toda a costa.", "caracteres": 70, "inicio_planejado": 13.000, "janela_s": 5.350, "duracao_estimada_s": 5.000, "duracao_real_s": 5.140, "velocidade": 1.00, "fim_real": 18.140, "desvio_inicio_ms": 38}
    ],
    "mixagem": {
      "original_normalizado_lufs": -20,
      "voz_normalizada_lufs": -16,
      "abaixamento": "sidechaincompress threshold=0.05 ratio=4 attack=15 release=450",
      "alvo_lufs": -14,
      "pico_max_dbtp": -1.5
    },
    "medicao": {
      "segmentos": 4,
      "fora_do_limite": 0,
      "limite_ms": 200,
      "desvio_max_ms": 38,
      "velocidade_min": 1.00,
      "velocidade_max": 1.00,
      "dublagem_wav_duracao_s": 21.500,
      "mix_lufs_integrado": -14.0,
      "mix_pico_dbtp": -2.1,
      "voz_menos_fundo_lu": 14.4
    }
  },
  "para_o_legendador": "Legenda sai da dublagem (karaokê sobre a voz em português). Segmento 3 tem valor: aviso 'Valores aproximados…'.",
  "para_o_narrador": "A fala dublada começa em 0,52 s: a pergunta de abertura do Toque HP fica só escrita. Espaço livre de voz para o fecho: de 18,30 s a 21,50 s."
}
```

Campos explicados (os mais importantes):
| Campo | O que é | Regra |
|---|---|---|
| `decisao.modo` | `legenda` ou `dublagem` | Pela tabela da seção 1.6; na dúvida, `legenda` |
| `segmentos[].literal` | Tradução "ao pé da letra" (só para conferência) | **Nunca** vai para a tela nem para a voz |
| `segmentos[].legenda` | Texto que o Legendador vai quebrar em blocos | Números em algarismo, símbolos (km, R$, °C), sem ponto final |
| `segmentos[].voz` | Texto que a voz vai falar | Mesma ideia da legenda, com números e siglas **por extenso** (seção 2.12) |
| `segmentos[].valor` | Se tem dinheiro | `true` → aviso "Valores aproximados…" |
| `dublagem.cps_voz` | Quantos caracteres por segundo a voz fala | Medido no passo 8 e guardado em `config\voz.json` |
| `janela_s` | Tempo disponível para a fala: do início dela até o início da próxima menos 0,15 s (a última: até o fim do vídeo menos 0,30 s, ou até o fecho do Toque HP) | A fala dublada tem que caber aqui |
| `duracao_estimada_s` | `caracteres ÷ cps_voz` | Se passar da janela em mais de 15%: enxugar o texto |
| `velocidade` | 1,00 = normal; 1,10 = 10% mais rápido | Só entre **0,85 e 1,15** |
| `desvio_inicio_ms` | Diferença entre onde a fala devia começar e onde começou | No máximo **±200 ms** |
| `voz_menos_fundo_lu` | Quanto a voz está mais alta que o som original nos trechos falados | Entre **12 e 20 LU** |

### 2.7 Saídas de áudio (especificação)
| Arquivo | Formato | Duração | Conteúdo | Volume |
|---|---|---|---|---|
| `dublagem\seg_NNN.wav` | O que o `dublar.py` gera (normalmente 22 050 Hz, mono) | A da fala | Uma fala por arquivo, sem silêncio grande antes/depois | Pico ≤ −1 dBFS |
| `dublagem.wav` | WAV, 48 000 Hz, mono, 16 bits | **Igual à do `bruto.mp4` ± 0,02 s** | Só a voz em português, cada fala no seu tempo; silêncio no resto | Pico ≤ −1 dBFS |
| `mix_dublado.wav` | WAV, 48 000 Hz, estéreo, 16 bits | Igual à do bruto ± 0,02 s | Original abaixado + voz | **−14 LUFS ± 1**, pico real **≤ −1,5 dBTP** |
| `previa_dublagem.mp4` | MP4 (vídeo do bruto + `mix_dublado.wav`) | Igual à do bruto | Só para conferir | — |

> **Quem usa o quê:** o Editor (manual 03) usa o `mix_dublado.wav` como trilha do vídeo final (e, se puser música livre de direitos, põe bem baixa e confere de novo o −14 LUFS no `final.mp4`). O Legendador (04) usa o `dublagem.wav` para achar o tempo de cada palavra em português (karaokê).

### 2.8 O `historico.log` (linhas do Tradutor)
```
2026-09-30T10:05:02-03:00 [03] tradutor: início (P1, prazo 15:00, restam 4h55; idioma it)
2026-09-30T10:05:03-03:00 [03] tradutor: decisão = dublagem (destinos, próprio, voz permitida, narração em off, cabe, prazo ok)
2026-09-30T10:31:40-03:00 [03] tradutor: tradução ok (4 segmentos, 3 conversões, 1 valor → aviso; glossário destinos)
2026-09-30T10:33:15-03:00 [03] tradutor: voz gerada pelo dublar.py (4 falas, 16,55 s de fala; velocidade 1,00 em todas)
2026-09-30T10:33:40-03:00 [03] tradutor: dublagem.wav montada (4 falas, desvio máx. 38 ms, 0 fora do limite)
2026-09-30T10:34:30-03:00 [03] tradutor: mix_dublado.wav ok (−14,0 LUFS, pico −2,1 dBTP, voz 14,4 LU acima do fundo)
2026-09-30T10:36:00-03:00 [03] tradutor: prévia conferida (escuta com e sem fone); fim — com o Legendador e o Narrador
```
Exemplo de item que **não** dubla:
```
2026-09-30T14:22:00-03:00 [03] tradutor: decisão = legenda (canal gta: voz sintética não permitida)
2026-10-01T09:10:00-03:00 [03] tradutor: decisão = legenda (pedido pedia dublagem, mas há pessoa real falando na tela de 3 a 11 s — condição 4)
```

### 2.9 Entrada de volta: `refazer.json`
```json
{
  "versao": 1,
  "item": "P1_2026-09-30_1100_receitas_focaccia-italiana",
  "revisor": "claude",
  "criado_em": "2026-09-30T13:02:00-03:00",
  "volta_numero": 1,
  "max_voltas": 2,
  "media": 6.8,
  "etapa_destino": "03_legenda_dublagem",
  "criterio_menor_nota": "T6_sincronia",
  "nota_criterio": 5,
  "motivo": "A voz da fala 5 ('Regue com azeite...') entra 0,4 s antes da mão aparecer com o azeite e atropela o começo da fala 6.",
  "o_que_fazer": "Enxugar a fala 5 e reencaixar; conferir desvio ≤ 200 ms e nenhuma sobreposição."
}
```
- Corrija **só** o apontado (e o que depender dele: se a fala 5 mudou, a legenda também muda — avise o Legendador pelo histórico).
- Renomeie para `refazer_1_feito.json` ao terminar. Na volta 2 que falhar: `99_erros`.

### 2.10 Arquivos de apoio (fora da pasta do item)
| Arquivo | Onde | Para quê | Situação |
|---|---|---|---|
| `scripts\dublar.py` | `G:\Meu Drive\Hypado\scripts\` | **A única porta** para gerar voz (Piper pt-BR) | (existente) |
| Modelo de voz Piper pt-BR (`.onnx` + `.onnx.json`) | Onde o `dublar.py` já procura (veja o `--help`) | A voz em si | (existente, já instalado) |
| `config\voz.json` | `G:\Meu Drive\Hypado\06 Projeto\app\config\` | Nome do modelo, velocidade medida (cps), parâmetros padrão | (a criar) |
| Glossário por canal | `G:\Meu Drive\Hypado\06 Projeto\app\dicionarios\glossario_<canal>.txt` | Como traduzir termos do canal sempre do mesmo jeito | (a criar) |
| Tabela de conversões | `G:\Meu Drive\Hypado\06 Projeto\app\config\conversoes.json` | Medidas e unidades (xícara, °F→°C, mph→km/h…) | (a criar) |
| Lista de pronúncia | `G:\Meu Drive\Hypado\06 Projeto\app\dicionarios\pronuncia.txt` | Como a voz deve ler siglas, números e estrangeirismos (usada também pelo Narrador, manual 06) | (a criar) |
| Dicionário de nomes | `...\dicionarios\nomes_<canal>.txt` | Grafia certa dos nomes (o mesmo do Legendador) | (a criar) |
| Roteiro de montagem da faixa | `H:\HypadoLocal\app\provisorio\montar_faixa.py` | Junta as falas no tempo e mede o desvio (seção 8.7) | (provisório) |

Exemplo de `config\voz.json` (a criar):
```json
{
  "versao": 1,
  "motor": "piper",
  "porta": "scripts\\dublar.py",
  "modelo": "pt_BR-<nome-do-modelo-instalado>.onnx",
  "amostragem_hz": 22050,
  "cps_medido": 14.0,
  "medido_em": "2026-09-30",
  "frase_teste": "A Trilha Azul liga Monterosso a Riomaggiore: uns doze quilômetros.",
  "velocidade_padrao": 1.00,
  "velocidade_min": 0.85,
  "velocidade_max": 1.15,
  "pausa_entre_frases_s": 0.20
}
```

Exemplo de glossário (`glossario_receitas.txt`, formato "original = como a HP escreve"):
```
# glossario_receitas.txt
all-purpose flour = farinha de trigo
baking powder = fermento químico em pó
baking soda = bicarbonato de sódio
heavy cream = creme de leite fresco
sour cream = creme azedo (ou creme de leite com limão)
scallions = cebolinha
cilantro = coentro
zucchini = abobrinha
eggplant = berinjela
broil = gratinar (grill do forno)
stick of butter = 113 g de manteiga
lievito di birra = fermento biológico
farina 00 = farinha de trigo tipo 00 (ou farinha de trigo comum)
q.b. (quanto basta) = a gosto
```
Exemplo de `pronuncia.txt` (formato "como está escrito = como a voz deve falar"):
```
# pronuncia.txt — vale para a voz do Tradutor (05) e do Narrador (06)
km/h = quilômetros por hora
km/l = quilômetros por litro
cv = cavalos
°C = graus
kg = quilos
g = gramas
ml = mililitros
R$ = reais (depois do número: "R$ 95" = "noventa e cinco reais")
US$ = dólares (depois do número)
€ = euros (depois do número)
SUV = ésse u vê
4x4 = quatro por quatro
0 a 96 km/h = de zero a noventa e seis quilômetros por hora
Dr. = doutor
nº = número
airfryer = air fráier
shoyu = xoiú
```

### 2.11 O padrão HP de tradução (a especificação)
| Item | Padrão HP | Exemplo |
|---|---|---|
| Registro | Português do Brasil falado, informal e correto: "você", "a gente", "pra" (na voz), "para" (na legenda pode ser "pra" se couber melhor) | "Hey guys, today we're making…" → "Hoje a gente vai fazer…" |
| Fidelidade | **Ao sentido**, não à palavra. Nunca inventar informação que não está no original | "It's a game changer" → "Isso muda tudo" (e não "É um trocador de jogo") |
| Tamanho | Cabe na legenda (22 caracteres/linha, 17 caracteres/s) e na voz (janela). Cortar enfeite, nunca o fato | "What I'm going to show you right now is actually really, really impressive" → "Olha que impressionante" |
| Números | Legenda: algarismo. Voz: por extenso (a voz lê melhor) | "twelve kilometers" → legenda "12 km"; voz "doze quilômetros" |
| Decimais | Vírgula brasileira: 3,2 s; 1,5 L | "3.2 seconds" → "3,2 s" |
| Milhar | Ponto ou palavra: 12.000 ou 12 mil | "12,000 dollars" → "US$ 12 mil" |
| Unidades | Sempre as brasileiras (tabela abaixo) | "350 °F" → "180 °C" |
| Moeda | Mantém a moeda original + conversão só se o pedido trouxer `cotacao`; **sempre** o aviso "Valores aproximados…" | "15 euros" → "€ 15 (≈ R$ 95)" |
| Títulos de filme/série | O título **oficial no Brasil** | "Inside Out 2" → "Divertida Mente 2"; "Dune: Part Two" → "Duna: Parte Dois" |
| Personagens | Como na versão brasileira oficial | "Joy" (Inside Out) → "Alegria" |
| Nomes de pessoas | Nunca traduz | "Timothée Chalamet", "Lucia", "Jason" |
| Lugares | Forma usada no Brasil quando existe; senão, a original | "Cappadocia" → "Capadócia"; "Cinque Terre" fica "Cinque Terre" |
| GTA | "GTA 6", nomes oficiais em inglês (Vice City, Leonida), gírias do jogo em português | "heist" → "assalto"; "cops" → "polícia"; "wanted level" → "nível de procurado" |
| Futebol | Termos do futebol brasileiro | "golazo" → "golaço"; "fichaje" → "contratação"; "cantera" → "base"; "mister" → "técnico"; "clean sheet" → "sem sofrer gol" |
| Gíria/expressão | Equivalente brasileiro | "piece of cake" → "moleza"; "break a leg" → "boa sorte"; "no way!" → "não acredito!" |
| Trocadilho intraduzível | Troca por outro que funcione em português **ou** explica curto; nunca deixa sem sentido | — |
| Palavrão | Tradução equivalente, suavizada na tela (manual 04) | "damn" → "caramba" |
| Estação do ano | Diz "de lá" + meses quando o lugar é do outro hemisfério | "in summer" (Itália) → "no verão europeu (junho a agosto)" |
| Datas | DD/MM | "November 19" → "19/11" |
| Horas | 24 h: "8 PM" → "20h" | — |

**Tabela de conversões (as que mais aparecem):**
| De | Para | Conta | Exemplo |
|---|---|---|---|
| °F | °C | (°F − 32) × 5 ÷ 9, arredondar para a dezena de forno | 350 °F → 177 → **180 °C**; 400 °F → **200 °C**; 425 °F → **220 °C** |
| cup (xícara americana) | xícara (chá) + gramas quando for sólido | 1 cup ≈ 240 ml; farinha ≈ 120 g; açúcar ≈ 200 g; manteiga ≈ 225 g | "2 cups of flour" → "2 xícaras de farinha (≈ 240 g)" |
| tablespoon / teaspoon | colher (sopa) / colher (chá) | 1 tbsp ≈ 15 ml; 1 tsp ≈ 5 ml | "1 tbsp" → "1 colher (sopa)" |
| oz (peso) | g | × 28,35 | 8 oz → **227 g** |
| fl oz | ml | × 29,57 | 12 fl oz → **355 ml** |
| lb | kg | × 0,4536 | 2 lb → **0,9 kg** |
| stick of butter | g | 1 stick = 113 g | "a stick" → "113 g de manteiga" |
| mph | km/h | × 1,609 | 60 mph → **96 km/h** (dá 96,6; a imprensa brasileira usa 96). Atenção: **0–60 mph é 0 a 96 km/h, NÃO 0 a 100** |
| mpg (EUA) | km/l | × 0,425 | 30 mpg → **12,8 km/l** |
| hp | cv | × 1,014 | 500 hp → **507 cv** (na legenda: "500 hp (≈ 507 cv)") |
| lb-ft | kgfm | × 0,138 | 400 lb-ft → **55,3 kgfm** |
| miles | km | × 1,609 | 5 miles → **8 km** |
| feet | m | × 0,3048 | 1.000 ft → **305 m** |
| inches | cm | × 2,54 | 20 in (roda) → "aro 20" (em roda de carro, **não** converte: "aro 20") |
| gallons (EUA) | litros | × 3,785 | 15 gal → **57 L** |

> Arredonde para um número "falável": 96 km/h e não 96,56 km/h; 180 °C e não 176,7 °C. Em carro, mantenha 1 casa quando o número for de desempenho (3,2 s; 12,8 km/l).

### 2.12 O padrão HP de dublagem (a especificação)
| Item | Padrão HP | Por quê |
|---|---|---|
| Voz | **Só** a voz Piper pt-BR gratuita já instalada, **gerada pelo `scripts\dublar.py`** | Regra da empresa; custo zero; sem risco de imitar pessoa |
| Clonar voz | **[BLOQUEIA] Nunca.** Nem do Antônio, nem de famoso, nem do narrador original, nem "parecida com" | Regra da empresa; risco legal e de confiança |
| Outras vozes | Nunca voz paga, voz de site, voz de aplicativo, nem modelo novo baixado sem aprovação do Antônio | Regra: só a gratuita já instalada |
| Estilo | "Voz por cima" de documentário (voice-over): o original continua baixinho por trás | É o jeito honesto e o que fica natural com voz sintética |
| Velocidade | 1,00 padrão; permitido de **0,85** (15% mais lenta) a **1,15** (15% mais rápida). Fora disso, enxugar o texto | Mais rápido que isso fica robótico; mais lento, arrastado |
| Início de cada fala | No início da fala original (± 200 ms) | Sincronia com a imagem |
| Fim de cada fala | Antes do início da próxima menos 0,15 s | Nunca duas falas por cima uma da outra |
| Texto para a voz | Números, unidades, moedas e siglas **por extenso** pela `pronuncia.txt` | A voz lê "km/h" errado; lê "quilômetros por hora" certo |
| Pontuação para a voz | Vírgula = pausa curta; ponto = pausa maior. Frases de até 20 palavras | Respiração natural |
| Nível da voz antes da mistura | Normalizada a −16 LUFS | Voz sempre com o mesmo volume |
| Nível do original antes da mistura | Normalizado a −20 LUFS | Original nunca "grita" mais que a voz |
| Abaixamento ("ducking") | Automático, só enquanto a voz fala: `sidechaincompress threshold=0.05 ratio=4 attack=15 release=450` | O original volta a subir nas pausas |
| Voz x fundo | Voz **12 a 20 LU** acima do fundo nos trechos falados | Entende a voz sem perder o clima do original |
| Volume final | **−14 LUFS integrado ± 1**, pico real **≤ −1,5 dBTP** | Padrão das redes; nem baixo, nem estourado |
| Formato final | `mix_dublado.wav`, 48 kHz, estéreo, 16 bits | O que o Editor espera |
| Pessoa real falando na tela | **Nunca** dublar por cima; legenda | Não pôr voz sintética na boca de alguém |
| Toque HP com voz | Mesma voz, mesmo nível (−16 LUFS), nunca por cima de fala dublada | Coerência (manual 06) |
| Aviso de IA | Marcar `voz_sintetica: true` para o Publicador (manual 10) decidir o rótulo de conteúdo sintético em cada rede | Transparência |

### 2.13 Como fica em cada canal (exemplos concretos)
**GTA 6 | HP — sempre legenda (nunca voz).**
| Original (inglês) | Literal (errado) | Padrão HP (legenda) |
|---|---|---|
| "Welcome back to Vice City." | "Bem-vindo de volta à Cidade do Vício." | "Bem-vindo de volta a Vice City" |
| "Lucia knows every street in Leonida." | "Lucia sabe toda rua em Leonida." | "A Lucia conhece cada rua de Leonida" |
| "The heist is on." | "O roubo está ligado." | "O assalto vai rolar" |
| "GTA VI comes out on November 19." | "GTA VI sai em 19 de novembro." | "GTA 6 chega em 19/11" |

**Futebol | HP — sempre legenda, áudio original sempre, nunca voz.**
| Original (espanhol) | Padrão HP |
|---|---|
| "¡Qué golazo de Vinícius!" | "Que golaço do Vini Jr.!" |
| "El mister habló con la cantera." | "O técnico conversou com a base" |
| "Nuevo fichaje del club." | "Nova contratação do clube" |
| "Ganamos 3 a 1 fuera de casa." | "Vencemos por 3 a 1 fora de casa" |

**Filmes e Séries | HP — legenda (entrevistas e trailers); dublagem só em vídeo próprio com narração em off.**
| Original (inglês) | Padrão HP |
|---|---|
| "Inside Out 2 broke the box office record." | "Divertida Mente 2 bateu o recorde de bilheteria" |
| "Joy and Sadness are back." | "Alegria e Tristeza estão de volta" |
| "Dune: Part Two was shot in Jordan." | "Duna: Parte Dois foi filmado na Jordânia" |
| "It grossed over a billion dollars." | "Faturou mais de US$ 1 bilhão" + aviso "Valores aproximados…" |

**Receitas | HP — legenda ou dublagem (vídeo próprio).**
| Original | Padrão HP (legenda) | Padrão HP (voz) |
|---|---|---|
| "Preheat the oven to 350 °F." | "Preaqueça o forno a 180 °C" | "Preaqueça o forno a cento e oitenta graus." |
| "Add 2 cups of flour and a stick of butter." | "2 xícaras de farinha (≈ 240 g) e 113 g de manteiga" | "Junte duas xícaras de farinha e cento e treze gramas de manteiga." |
| "Aggiungi il lievito di birra." (italiano) | "Junte o fermento biológico" | "Junte o fermento biológico." |
| "Sale q.b." (italiano) | "Sal a gosto" | "Sal a gosto." |

**Carros | HP — legenda ou dublagem (vídeo próprio, ex.: material de imprensa da montadora com narração em off).**
| Original | Padrão HP (legenda) | Padrão HP (voz) |
|---|---|---|
| "0 to 60 in 3.2 seconds." | "De 0 a 96 km/h em 3,2 s" | "De zero a noventa e seis quilômetros por hora em três vírgula dois segundos." |
| "It makes 500 horsepower." | "500 hp (≈ 507 cv)" | "São quinhentos cavalos de potência." |
| "It gets 30 mpg on the highway." | "12,8 km/l na estrada" | "Faz doze vírgula oito quilômetros por litro na estrada." |
| "Starting at $45,000." | "A partir de US$ 45 mil" + aviso | "A partir de quarenta e cinco mil dólares." |

**Destinos | HP — legenda ou dublagem (vídeo próprio).**
| Original | Padrão HP (legenda) | Padrão HP (voz) |
|---|---|---|
| "It's a 20-minute walk from the station." | "Fica a uns 20 minutos a pé da estação" | "Fica a uns vinte minutos a pé da estação." |
| "Best visited in fall." (Japão) | "Melhor no outono de lá (set. a nov.)" | "O melhor é no outono de lá, de setembro a novembro." |
| "Entry is about 15 euros." | "Entrada: cerca de € 15" + aviso | "A entrada custa cerca de quinze euros." |
| "Cappadocia's balloons fly at sunrise." | "Os balões da Capadócia sobem ao nascer do sol" | "Os balões da Capadócia sobem ao nascer do sol." |

---

## 3. Passo a passo numerado (para leigo)

> **Como usar:** faça na ordem. Cada passo diz o que abrir, o que rodar, o que conferir e o que deve aparecer. Copie o comando inteiro, cole no PowerShell (botão direito cola) e aperte **Enter**.
> Passos 1 a 10: **uma vez só**. Do dia a dia: a partir do 11.
> **[APP]** = o app fará sozinho quando o módulo da etapa 3 existir (a criar). **[CLAUDE]** = julgamento (tradução, enxugar texto). Até o módulo existir, quem executa segue os passos à mão.
> **Se o item for só legenda** (GTA, Futebol, ou qualquer um que não passe nas 6 condições), você faz os passos 11 a 38 e pula para o 60.

### Fase A — Preparar o PC (uma vez só)

**Passo 1 — Abrir o PowerShell.** Menu Iniciar → digitar `PowerShell` → **Windows PowerShell**. Deve aparecer uma janela azul com `PS C:\Users\...>`.

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
- Se `$dublar` der `False`: **pare**. Sem o `dublar.py` não existe dublagem na HP (só legenda). Avise o Antônio/abra ticket (passo 64).

**Passo 3 — Conferir o Python.** `& $py --version` → deve aparecer `Python 3.12.x`.

**Passo 4 — Ler a ajuda do `dublar.py` e anotar como ele funciona.**
```powershell
& $py $dublar --help
```
- Deve aparecer: a lista de opções do script (em português).
- Anote no Bloco de Notas, **com os nomes exatos que aparecerem**: (a) como passar o **texto** de uma fala; (b) como dizer o **arquivo de saída**; (c) se existe opção de **velocidade** (no Piper ela se chama "length scale": número **menor** que 1 = fala **mais rápida**); (d) onde fica o **modelo de voz** pt-BR.
- Esses nomes vão para o `config\voz.json` (passo 9). **Este manual não inventa os nomes dos parâmetros do `dublar.py`**: nos exemplos abaixo eles aparecem como `OPCAO_TEXTO`, `OPCAO_SAIDA` e `OPCAO_VELOCIDADE` — troque pelos nomes exatos que o `--help` mostrou (senão o comando dá erro).
- Se o `--help` mostrar que o `dublar.py` só dubla o vídeo inteiro de uma vez (sem aceitar uma fala por vez), use-o assim mesmo só se ele respeitar os tempos de cada frase; se não respeitar, abra ticket pedindo a opção "uma fala por arquivo" (a criar) e, até lá, faça **legenda** em vez de dublagem.

**Passo 5 — Conferir se o ffmpeg tem os filtros de áudio usados aqui.**
```powershell
& $ff -hide_banner -filters | Select-String " sidechaincompress | loudnorm | ebur128 | atempo | silencedetect | adelay | amix "
```
- Deve aparecer: 7 linhas (uma para cada filtro).
- Se faltar alguma, esse ffmpeg é antigo/incompleto: avise antes de dublar.

**Passo 6 — Conferir que a voz pt-BR está instalada.**
```powershell
Get-ChildItem "H:\HypadoLocal\ferramentas" -Recurse -Filter "pt_BR*.onnx" -ErrorAction SilentlyContinue | Select-Object FullName, Length
```
- Deve aparecer: pelo menos 1 arquivo `pt_BR-...onnx` (dezenas de MB), com um `.onnx.json` do mesmo nome ao lado.
- Se não aparecer nada aí, procure onde o `--help` do passo 4 disse. **Não baixe outra voz** sem ordem do Antônio: a regra é usar a que já está instalada.

**Passo 7 — Gerar a frase de teste.**
```powershell
$t = "H:\HypadoLocal\app\teste_voz"; New-Item -ItemType Directory -Force $t | Out-Null; Set-Location $t
& $py $dublar OPCAO_TEXTO "A Trilha Azul liga Monterosso a Riomaggiore: uns doze quilômetros." OPCAO_SAIDA "$t\teste.wav"
Invoke-Item "$t\teste.wav"
```
- Deve aparecer: o arquivo `teste.wav` e, ao abrir, a voz lendo a frase.
- Conferir de ouvido: a voz é clara, sem chiado, sem cortar o começo ou o fim.

**Passo 8 — Medir a velocidade da voz (caracteres por segundo).**
```powershell
& $ff -hide_banner -i "$t\teste.wav" 2>&1 | Select-String "Duration"
```
- Deve aparecer algo como `Duration: 00:00:04.62`.
- Conta: a frase tem **66 caracteres** (contando espaços e pontuação). Velocidade = 66 ÷ 4,62 = **14,3 caracteres por segundo**.
- Repita com mais 2 frases diferentes (uma curta, uma longa) e faça a média. Esse número é o `cps_medido`.

**Passo 9 — Gravar o `config\voz.json`** (a criar; Bloco de Notas, UTF-8), no modelo da seção 2.10, com: o nome do modelo (passo 6), os nomes das opções do `dublar.py` (passo 4), a amostragem (normalmente 22050) e o `cps_medido` (passo 8).
```powershell
& $py -m json.tool "$cfg\voz.json" | Out-Null; if ($LASTEXITCODE -eq 0) { "JSON OK" } else { "JSON QUEBRADO" }
```
- Deve aparecer: `JSON OK`.

**Passo 10 — Instalar o roteiro provisório de montagem e conferir os arquivos de apoio.**
- Copie o texto da seção 8.7 para `H:\HypadoLocal\app\provisorio\montar_faixa.py` (UTF-8) e confira:
```powershell
& $py "$prov\montar_faixa.py" --help
Get-ChildItem $dic -Filter "glossario_*.txt" | Select-Object Name; Test-Path "$dic\pronuncia.txt"; Test-Path "$cfg\conversoes.json"
```
- Deve aparecer: a ajuda do roteiro; os 6 glossários (a criar — se faltarem, crie com os exemplos da seção 2.10); `True` para a pronúncia e as conversões (se `False`, crie a partir das seções 2.10 e 2.11).

### Fase B — Pegar o item certo

**Passo 11 — Conferir o horário.** `Get-Date -Format "HH:mm"`
- Entre **18:00 e 22:29**: pode **traduzir** (é leve: passos 23 a 43), mas **não pode** gerar voz, montar faixa nem mixar (passos 44 a 59 — trabalho pesado), nem para P0. Isso vale também para o `dublar.py`.

**Passo 12 — Achar os itens que precisam de tradução.**
```powershell
Get-ChildItem "$esteira\03_legenda_dublagem" -Directory | Sort-Object Name | ForEach-Object {
  $p = Get-Content "$($_.FullName)\pedido.json" -Raw -Encoding UTF8 | ConvertFrom-Json
  $tr = Test-Path "$($_.FullName)\transcricao.json"
  $td = Test-Path "$($_.FullName)\traducao.json"
  if ($p.idioma_origem -ne "pt") { "{0}  idioma={1}  transcricao={2}  traducao={3}  tratamento={4}" -f $_.Name, $p.idioma_origem, $tr, $td, $p.audio.tratamento }
}
```
- Deve aparecer: uma linha por item estrangeiro. Pegue o **primeiro** com `transcricao=True` e `traducao=False` (os `P0_` aparecem primeiro).
- Item com `transcricao=False`: o Legendador ainda não transcreveu; espere.

**Passo 13 — Entrar na pasta.**
```powershell
$item = "$esteira\03_legenda_dublagem\P1_2026-09-30_1500_destinos_cinque-terre-trilha"
Set-Location $item; Get-ChildItem | Select-Object Name, Length
```
- Deve aparecer: `pedido.json`, `bruto.mp4`, `transcricao.json`, `historico.log`.

**Passo 14 — Ler o pedido e anotar.**
```powershell
Get-Content pedido.json -Encoding UTF8
```
- Anote: `canal`, `origem`, `idioma_origem`, `audio.tratamento`, `audio.voz_sintetica_permitida`, `audio.narracao_em_off`, `valores_citados`, `cotacao` (se tiver), `toque_hp.modo`, `publicar_em`.

**Passo 15 — Conferir que a transcrição está pronta.**
```powershell
$tr = Get-Content transcricao.json -Raw -Encoding UTF8 | ConvertFrom-Json
"revisado={0}  idioma={1}  segmentos={2}  duracao={3}" -f $tr.revisado, $tr.idioma_detectado, $tr.segmentos.Count, $tr.duracao_s
```
- Deve aparecer: `revisado=True`, o idioma, o número de segmentos e a duração.
- `revisado=False` → não comece; o Legendador ainda tem pendências.
- Idioma detectado diferente do pedido (ex.: pedido `en`, detectado `es`) → vale o detectado (manual 04, passo 24).

**Passo 16 — Ver se é volta do Revisor.** `if (Test-Path refazer.json) { Get-Content refazer.json -Encoding UTF8 } else { "primeira passada" }`
- Se for volta: leia `criterio_menor_nota` e vá direto ao passo que resolve:
| Critério | Passo |
|---|---|
| `T1_sentido`, `T2_naturalidade` | 26 |
| `T3_adaptacao` | 27–31 |
| `T4_nomes` | 29 |
| `T5_cabimento` | 32 (legenda) ou 42 (voz) |
| `T6_sincronia` | 51–53 |
| `T7_voz` | 47–49 |
| `T8_mixagem` | 54, 57 |
| `T9_loudness` | 55–56 |
| `T11_valores` | 28 |

### Fase C — Decidir: legendar ou dublar [APP]

**Passo 17 — Condição 1: o canal.**
- `gta` ou `futebol` → **legenda**. Fim da decisão. Anote no histórico: `tradutor: decisão = legenda (canal <x>: voz sintética não permitida)`.
- `destinos`, `receitas`, `carros`, `filmes` → siga.

**Passo 18 — Condições 2 e 3: vídeo próprio e voz permitida.**
- `origem` ≠ `proprio` **ou** `voz_sintetica_permitida` ≠ `true` → **legenda**.
- O Tradutor **nunca** muda esses campos. Se achar que o vídeo devia ser próprio, escreva no histórico para o Curador olhar da próxima vez.

**Passo 19 — Condição 4: é narração em off? (olhe o vídeo inteiro).**
```powershell
Invoke-Item bruto.mp4
```
- Assista **com som**. Enquanto a voz fala, aparece alguém com a boca mexendo, falando para a câmera, dando entrevista? Se **sim**, em qualquer trecho → aquele trecho é de **pessoa real falando** → **nada de voz sintética nele**.
- Se o vídeo inteiro for pessoa falando → **legenda**.
- Se só um pedaço for pessoa falando (ex.: 3 s de entrevista no meio de narração em off) → ou legenda no vídeo todo (mais simples, **padrão**), ou dublagem só dos trechos em off + legenda no trecho da pessoa (só se o Claude decidir que vale; anote em `decisao.motivo`).

**Passo 20 — Condição 5: cabe no tempo? (estimativa rápida).**
- Some os caracteres do texto original e multiplique por **1,2** (português costuma ser uns 20% mais comprido que inglês/italiano). Divida pelo `cps_medido` (ex.: 14). Compare com o tempo total de fala (soma de `fim − inicio` dos segmentos + as pausas entre eles).
- Ex.: original com 220 caracteres → 264 em português → 264 ÷ 14 = 18,9 s. Tempo disponível: 17,5 s. Diferença 8% → **cabe** (limite 15%, e dá para enxugar).
- Se passar de 30%: é fala muito corrida (típico de review de carro americano) → **legenda** é o mais seguro.

**Passo 21 — Condição 6: dá tempo?**
- Veja `publicar_em`. Se faltam **menos de 40 minutos** e é P0 → **legenda** agora.

**Passo 22 — Gravar a decisão.**
- Comece o `traducao.json` (Bloco de Notas, UTF-8) com o cabeçalho e o bloco `decisao` da seção 2.6.
- Histórico:
```powershell
Add-Content -Path historico.log -Encoding UTF8 -Value "$(Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz') [03] tradutor: decisão = dublagem (destinos, próprio, voz permitida, narração em off, cabe, prazo ok)"
```

### Fase D — Traduzir [CLAUDE]

**Passo 23 — Ler a transcrição inteira antes de traduzir qualquer frase.**
- Entenda do que o vídeo fala, quem fala, o tom (sério, engraçado, empolgado), o público.
- Uma frase isolada engana ("It's sick!" pode ser "É doente!" — errado — ou "Que irado!").

**Passo 24 — Abrir o glossário do canal e o dicionário de nomes.**
```powershell
notepad "$dic\glossario_destinos.txt"; notepad "$dic\nomes_destinos.txt"
```
- Todo termo que estiver no glossário é traduzido **sempre** do jeito que está lá.

**Passo 25 — (Só na cabeça ou no campo `literal`) fazer a tradução ao pé da letra.**
- Serve só para você não perder informação. **Nunca** vai para a tela ou para a voz.

**Passo 26 — Traduzir pelo sentido, em português do Brasil natural.**
- Pergunta-guia: "como um brasileiro diria isso num vídeo?".
- Exemplos:
  - "Let's get right into it" → "Bora lá" (e não "Vamos entrar direto nisso").
  - "This place is absolutely breathtaking" → "Esse lugar é de tirar o fôlego".
  - "Trust me, you don't want to miss this" → "Confia, você não vai querer perder".
  - "Le Cinque Terre sono cinque borghi sospesi tra mare e montagna" → "As Cinque Terre são cinco vilas entre o mar e a montanha".
- Não "melhore" o conteúdo: não acrescente fato, opinião ou exagero que não estão no original.

**Passo 27 — Adaptar medidas e unidades** (tabela da seção 2.11). Exemplos que mais aparecem:
- Receitas: "350 °F" → "180 °C"; "1 cup" → "1 xícara"; "a stick of butter" → "113 g de manteiga".
- Carros: "0 to 60 in 3.2" → "0 a 96 km/h em 3,2 s"; "500 hp" → "500 hp (≈ 507 cv)"; "30 mpg" → "12,8 km/l".
- Destinos: "5 miles" → "8 km"; "1,000 feet" → "305 m".
- Registre cada conversão na lista `conversoes` do `traducao.json`.

**Passo 28 — Tratar dinheiro [BLOQUEIA se faltar o aviso].**
- Mantenha a moeda original: "US$ 45 mil", "€ 15", "¥ 3.000".
- Converta para reais **só** se o pedido trouxer `cotacao`: 15 × 6,30 = 94,50 → "(≈ R$ 95)". Sem cotação no pedido, não converte (nunca pesquise cotação por conta própria e nunca invente).
- Marque `"valor": true` no segmento → o Legendador põe "Valores aproximados…" na tela.

**Passo 29 — Nomes, títulos e lugares.**
- Pessoas: nunca traduzir ("Timothée Chalamet", "Lucia").
- Filme/série: título **oficial no Brasil**. Na dúvida, confira no pôster oficial brasileiro / site da distribuidora.
- Lugar: forma usada no Brasil se existir ("Capadócia"); senão, a original ("Cinque Terre", "Riomaggiore").
- Conferir cada nome no `nomes_<canal>.txt`; nome novo certo → acrescentar lá.

**Passo 30 — Gírias, piadas e expressões.** Troque pelo equivalente brasileiro ("piece of cake" → "moleza"). Piada que não funciona em português: troque por outra que funcione ou corte, **nunca** deixe sem sentido.

**Passo 31 — Datas, horas e estações.** "November 19" → "19/11"; "8 PM" → "20h"; estação de outro hemisfério → "de lá" + meses ("primavera de lá, de março a junho").

**Passo 32 — Caber na legenda.**
- Para cada segmento: CPS = número de caracteres da `legenda` ÷ (`fim` − `inicio`).
- Ex.: segmento 3: "Ingresso: cerca de € 15 por dia (≈ R$ 95)" = 42 caracteres; 9,80 a 12,40 = 2,60 s → 16,2 CPS. OK (limite 17).
- Passou de 17? Enxugue: tire enfeite ("realmente", "na verdade", "basicamente"), troque por palavras curtas ("utilizar" → "usar"), use símbolo ("quilômetros" → "km").
- Nenhuma palavra sozinha com mais de 20 letras (não cabe numa linha de 22).

**Passo 33 — Conferir números com a imagem.** Placar, preço na etiqueta, velocímetro, temperatura no forno: se a imagem mostra outro número, vale a imagem (e anote).

**Passo 34 — Ler a tradução em voz alta, do começo ao fim.** Soa como um brasileiro falando? Tem frase travada, repetida, estranha? Arrume.

**Passo 35 — "Tradução de volta".** Leia a frase em português e pergunte: "ela diz o mesmo que o original?" Se perdeu um fato (número, nome, negação), volte ao passo 26. Cuidado especial com **negação** ("not", "non", "no"): trocar "não" por "sim" é o erro mais grave de tradução.

**Passo 36 — Escrever os segmentos no `traducao.json`.**
- Para cada segmento: `id`, `inicio`, `fim` (copiados da transcrição), `original`, `literal`, `legenda`, `voz` (por enquanto igual à legenda; ajustada no passo 39), `notas`, `valor`.
- Mesmo número de segmentos e mesmos `id` da transcrição. **Nenhum** pode faltar.

**Passo 37 — Conferir se o JSON está válido.**
```powershell
& $py -m json.tool traducao.json | Out-Null; if ($LASTEXITCODE -eq 0) { "JSON OK" } else { "JSON QUEBRADO" }
```
- Deve aparecer: `JSON OK`.

**Passo 38 — Se a decisão é LEGENDA: fechar aqui.**
```powershell
Add-Content -Path historico.log -Encoding UTF8 -Value "$(Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz') [03] tradutor: tradução ok (4 segmentos, 3 conversões, 1 valor → aviso) — só legenda; com o Legendador"
```
- Vá para o passo 60. (Os passos 39 a 59 são só de dublagem.)

### Fase E — Preparar o texto da voz (só dublagem)

**Passo 39 — Escrever o "texto para a voz" de cada segmento (campo `voz`).**
- Parte da `legenda`, mas troca tudo o que a voz lê mal, usando a `pronuncia.txt`:
| Legenda (tela) | Voz (falada) |
|---|---|
| "uns 12 km" | "uns doze quilômetros" |
| "€ 15 (≈ R$ 95)" | "quinze euros" (a conversão fica só na tela) |
| "180 °C" | "cento e oitenta graus" |
| "De 0 a 96 km/h em 3,2 s" | "De zero a noventa e seis quilômetros por hora em três vírgula dois segundos" |
| "500 hp (≈ 507 cv)" | "quinhentos cavalos de potência" |
| "SUV 4x4" | "ésse u vê quatro por quatro" |
| "19/11" | "dezenove de novembro" |
| "20h" | "oito da noite" |
- Termine cada fala com ponto (a voz faz a pausa final certa). Vírgula onde uma pessoa respiraria.

**Passo 40 — Calcular a janela de cada fala.**
- **Janela** = início da próxima fala − 0,15 s − início desta fala. Para a última: fim do vídeo − 0,30 s − início dela (ou o início do fecho do Toque HP, se o Narrador for usar voz no fim).
- Exemplo (Cinque Terre):
| Fala | Início | Início da próxima | Janela |
|---|---|---|---|
| 1 | 0,52 | 4,60 | 4,60 − 0,15 − 0,52 = **3,93 s** |
| 2 | 4,60 | 9,80 | **5,05 s** |
| 3 | 9,80 | 13,00 | **3,05 s** |
| 4 | 13,00 | fecho do Toque HP em 18,50 | 18,50 − 0,15 − 13,00 = **5,35 s** |

**Passo 41 — Estimar quanto cada fala vai durar.**
- **Duração estimada** = caracteres do texto da voz ÷ `cps_medido`.
- Ex.: fala 3 "O ingresso custa cerca de quinze euros por dia." = 47 caracteres ÷ 14 = **3,36 s** > janela de 3,05 s → estouro de 10%.
- Regra: estouro **até 15%** → resolve com velocidade (passo 49). **Mais de 15%** → enxugar (passo 42). Mesmo com estouro pequeno, **prefira enxugar** se der sem perder informação (a voz no normal soa melhor).

**Passo 42 — Enxugar a fala que não cabe [CLAUDE].**
- Ex.: "O ingresso custa cerca de quinze euros por dia." (47) → "Ingresso: cerca de quinze euros por dia." (40 caracteres → 2,86 s ≤ 3,05 s). Cabe.
- Técnicas: tirar artigo e verbo de ligação quando fica natural ("O ingresso custa" → "Ingresso:"); trocar palavra longa por curta ("aproximadamente" → "uns"); tirar enfeite.
- **Nunca** tirar número, nome, negação ou a informação principal.
- Mudou a voz? Veja se a legenda deve mudar junto (o texto da tela e o da voz têm que dizer a mesma coisa; a legenda pode ter a conversão em reais a mais).

**Passo 43 — Combinar com o Toque HP (manual 06).**
- Se o pedido tem `toque_hp.modo` = `voz`:
  - A pergunta de abertura falada ocupa **0,00 a 2,00 s**. Se a primeira fala dublada começa **antes de 2,10 s**, a abertura fica **só escrita** (o Narrador decide; você só avisa).
  - O fecho falado ocupa os últimos 2 a 3 s. A última fala dublada tem que terminar antes dele (a janela do passo 40 já considera isso).
- Escreva em `traducao.json → para_o_narrador` onde há espaço livre de voz (ex.: "Espaço livre de voz para o fecho: de 18,30 s a 21,50 s").

### Fase F — Gerar a voz [APP]

**Passo 44 — Conferir horário e trava** (a partir daqui é trabalho pesado).
```powershell
Get-Date -Format "HH:mm"; if (Test-Path "H:\HypadoLocal\app\pesado.lock") { Get-Content "H:\HypadoLocal\app\pesado.lock" } else { "livre" }
```
- Tem que estar **fora** de 18:00–22:29 e aparecer `livre`. Senão, espere (nunca apague o `pesado.lock`).

**Passo 45 — Gerar uma fala por arquivo com o `dublar.py`.**
```powershell
New-Item -ItemType Directory -Force "$item\dublagem" | Out-Null
$td = Get-Content traducao.json -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($s in $td.segmentos) {
  $saida = "$item\dublagem\seg_{0:D3}.wav" -f [int]$s.id
  & $py $dublar OPCAO_TEXTO $s.voz OPCAO_SAIDA $saida
}
Get-ChildItem "$item\dublagem" | Select-Object Name, Length
```
- (Troque `OPCAO_TEXTO` e `OPCAO_SAIDA` pelos nomes exatos que o `--help` mostrou no passo 4.)
- Deve aparecer: `seg_001.wav`, `seg_002.wav`… um por segmento, cada um com dezenas ou centenas de KB.
- Se algum não aparecer ou tiver 0 bytes: rode de novo só aquele; se falhar 2 vezes, veja a seção 6.

**Passo 46 — Medir a duração de cada fala gerada.**
```powershell
Get-ChildItem "$item\dublagem\seg_*.wav" | ForEach-Object {
  $d = (& $ff -hide_banner -i $_.FullName 2>&1 | Select-String "Duration: ([\d:.]+)").Matches[0].Groups[1].Value
  "{0}  {1}" -f $_.Name, $d
}
```
- Deve aparecer: cada arquivo com a duração (ex.: `seg_003.wav  00:00:02.91`).
- Compare com a janela (passo 40): `seg_003` = 2,91 s ≤ 3,05 s → **cabe**.

**Passo 47 — Ouvir cada fala (com fone, se possível).**
```powershell
Invoke-Item "$item\dublagem\seg_001.wav"
```
- Conferir: (1) a voz leu **exatamente** o texto; (2) pronunciou certo nomes e números; (3) não cortou o começo nem o fim; (4) sem chiado, estalo ou "robô engasgado"; (5) a entonação da pergunta sobe no fim (quando é pergunta).

**Passo 48 — Corrigir pronúncia errada.**
- A voz leu "Riomaggiore" como "Rio-ma-gió-re" esquisito? Escreva na `pronuncia.txt` como deve soar (ex.: `Riomaggiore = Riomadjôre`) e gere de novo **só aquela fala** (passo 45 com um único segmento).
- Atenção: a correção de pronúncia muda **só o texto da voz**, nunca a legenda (na tela continua "Riomaggiore").

**Passo 49 — Ajustar a velocidade da fala que ainda não coube (até 15%).**
- Velocidade necessária = duração real ÷ janela. Ex.: 3,36 ÷ 3,05 = **1,10** (10% mais rápida). Permitido: de 0,85 a 1,15.
- Jeito 1 (preferido, se o `dublar.py` tiver opção de velocidade): gere de novo com a opção de velocidade. No Piper, "length scale" = 1 ÷ velocidade → 1 ÷ 1,10 = **0,91**.
- Jeito 2 (se não tiver): acelere o arquivo pronto com o ffmpeg, sem mudar o tom da voz:
```powershell
& $ff -hide_banner -loglevel error -y -i "$item\dublagem\seg_003.wav" -af "atempo=1.10" "$item\dublagem\seg_003_rapido.wav"
Move-Item -Force "$item\dublagem\seg_003_rapido.wav" "$item\dublagem\seg_003.wav"
```
- Deve aparecer: nada (sem erro). Meça de novo (passo 46).
- Precisou de mais de 1,15? **Não force.** Volte ao passo 42 e enxugue o texto.

**Passo 50 — Anotar as medidas no `traducao.json`.**
- Para cada fala, no bloco `dublagem.segmentos`: `arquivo`, `texto_voz`, `caracteres`, `inicio_planejado`, `janela_s`, `duracao_estimada_s`, `duracao_real_s`, `velocidade` (modelo da seção 2.6).
- Confira o JSON (comando do passo 37) → `JSON OK`.

### Fase G — Montar a faixa da dublagem [APP]

**Passo 51 — Definir onde cada fala começa.**
- `inicio_planejado` = `inicio` do segmento original (a voz em português entra junto com a original, que é abaixada).
- Exceção: se a pergunta de abertura do Toque HP for **falada**, nenhuma fala dublada começa antes de 2,10 s (passo 43).

**Passo 52 — Rodar o roteiro de montagem.**
```powershell
& $py "$prov\montar_faixa.py" --item $item
```
- Deve aparecer: `OK: 4 falas; desvio max 38 ms; 0 fora do limite de 200 ms`.
- O roteiro grava `dublagem.wav` (48 kHz, mono, com a duração exata do vídeo), mede onde cada fala começou de verdade e anota em `traducao.json → dublagem.medicao` e no `historico.log`.
- `TravaOcupada` → horário proibido ou outro pesado rodando: espere.

**Passo 53 — Conferir a faixa montada.**
```powershell
& $ff -hide_banner -i dublagem.wav 2>&1 | Select-String "Duration|Stream"
& $ff -hide_banner -i bruto.mp4 2>&1 | Select-String "Duration"
```
- Deve aparecer: `48000 Hz, mono` e a **mesma duração** nos dois (diferença ≤ 0,02 s).
- `fora do limite` maior que 0: alguma fala começou mais de 200 ms fora do lugar — normalmente porque o arquivo da fala tem silêncio no começo. Veja a seção 6.

### Fase H — Mixar com o original abaixado e medir o volume [APP]

**Passo 54 — Fazer a mistura (original baixinho + voz) já no volume final.**
```powershell
& $ff -hide_banner -loglevel error -y -i bruto.mp4 -i dublagem.wav -filter_complex "[0:a]aresample=48000,loudnorm=I=-20:TP=-2:LRA=11,aresample=48000[orig];[1:a]aresample=48000,loudnorm=I=-16:TP=-2:LRA=11,aresample=48000,asplit=2[voz][sc];[orig][sc]sidechaincompress=threshold=0.05:ratio=4:attack=15:release=450[fundo];[fundo][voz]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]" -map "[a]" -ac 2 -c:a pcm_s16le mix_dublado.wav
```
- O que esse comando faz, em português:
  1. `[orig]`: pega o som original e deixa em −20 LUFS (volume padrão, baixo).
  2. `[voz]`: pega a dublagem e deixa em −16 LUFS (4 pontos acima do original).
  3. `sidechaincompress`: **enquanto a voz fala, o original abaixa sozinho** (cerca de 10 dB); nas pausas, volta.
  4. `amix`: junta os dois.
  5. `loudnorm=I=-14`: deixa o resultado no volume padrão das redes (−14 LUFS), sem estourar (pico −1,5).
- Deve aparecer: nada (sem erro) e o arquivo `mix_dublado.wav`.
- Se aparecer erro com `normalize`: o ffmpeg é antigo; tire `:normalize=0` e ponha `,volume=2` logo depois do `amix=...first` (e avise para atualizar o ffmpeg).

**Passo 55 — Medir o volume final.**
```powershell
& $ff -hide_banner -nostats -i mix_dublado.wav -af ebur128=peak=true -f null - 2>&1 | Select-String "^\s+I:|^\s+Peak:"
```
- Deve aparecer: `I: -14.x LUFS` e `Peak: -x.x dBFS`.
- Aceito: **I entre −15,0 e −13,0**; **Peak ≤ −1,5**.

**Passo 56 — Acertar o volume se ficou fora do alvo (ou para cravar em −14).**
- Correção = −14 − I medido. Ex.: I = −14,9 → correção **+0,9 dB**.
```powershell
& $ff -hide_banner -loglevel error -y -i mix_dublado.wav -af "volume=0.9dB" -c:a pcm_s16le mix_ajustado.wav
& $ff -hide_banner -nostats -i mix_ajustado.wav -af ebur128=peak=true -f null - 2>&1 | Select-String "^\s+I:|^\s+Peak:"
```
- Deve aparecer: `I: -14.0 LUFS`. Se o Peak continuar ≤ −1,5: `Move-Item -Force mix_ajustado.wav mix_dublado.wav`.
- Se o Peak passar de −1,5 depois de subir o volume: não suba; refaça o passo 54 (o `loudnorm` segura o pico) e aceite o I que der entre −15 e −13.

**Passo 57 — Medir se a voz está bem acima do fundo (12 a 20 LU).**
```powershell
& $ff -hide_banner -loglevel error -y -i bruto.mp4 -i dublagem.wav -filter_complex "[0:a]aresample=48000,loudnorm=I=-20:TP=-2:LRA=11,aresample=48000[orig];[1:a]aresample=48000,loudnorm=I=-16:TP=-2:LRA=11,aresample=48000,asplit=2[sc][vozout];[orig][sc]sidechaincompress=threshold=0.05:ratio=4:attack=15:release=450[fundo]" -map "[fundo]" fundo_abaixado.wav -map "[vozout]" voz_nivelada.wav
```
- Agora meça os dois **no trecho da fala mais longa** (ex.: fala 2, de 4,60 s, durando 4,6 s):
```powershell
foreach ($f in "fundo_abaixado.wav", "voz_nivelada.wav") { $f; & $ff -hide_banner -nostats -ss 4.6 -t 4.6 -i $f -af ebur128 -f null - 2>&1 | Select-String "^\s+I:" }
```
- Deve aparecer: dois números, ex.: fundo `I: -29.9 LUFS` e voz `I: -15.5 LUFS` → diferença **14,4 LU**. Aceito: **12 a 20**.
- Menos de 12 (voz "brigando" com o fundo): use `ratio=6` no passo 54 e refaça. Mais de 20 (o original sumiu): use `ratio=3`. Anote o que usou em `dublagem.mixagem`.
- Depois apague os dois arquivos de medição: `Remove-Item fundo_abaixado.wav, voz_nivelada.wav`.

**Passo 58 — Fazer a prévia com vídeo.**
```powershell
& $ff -hide_banner -loglevel error -y -i bruto.mp4 -i mix_dublado.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 160k -shortest previa_dublagem.mp4
Invoke-Item previa_dublagem.mp4
```

**Passo 59 — Assistir à prévia e conferir.**
- [ ] Cada fala entra junto com a imagem certa (a voz fala do azeite quando aparece o azeite).
- [ ] Nenhuma fala por cima da outra; nenhuma cortada.
- [ ] O som original aparece baixinho por trás e volta nas pausas (o clima do vídeo continua).
- [ ] Nenhuma voz sintética em cima de pessoa real falando na tela.
- [ ] Volume confortável: nem precisa aumentar, nem assusta.
- [ ] Ouça também no **alto-falante do celular** (mande o arquivo para você mesmo pelo Drive — nunca pelo WhatsApp da HP): a voz continua clara?
- Algum "não"? Volte ao passo que resolve (encaixe → 49–52; mistura → 54–57; pronúncia → 48).

### Fase I — Entregar

**Passo 60 — Escrever no histórico o resultado com números.**
```powershell
Add-Content -Path historico.log -Encoding UTF8 -Value "$(Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz') [03] tradutor: mix_dublado.wav ok (-14,0 LUFS, pico -2,1 dBTP, voz 14,4 LU acima do fundo; desvio máx. 38 ms; velocidade 1,00 a 1,10)"
```
- (Para item só de legenda, a linha do passo 38 já basta.)

**Passo 61 — Limpar o que é temporário.**
- Apague: `mix_ajustado.wav` (se sobrou), `fundo_abaixado.wav`, `voz_nivelada.wav`.
- **Mantenha** até o item ser postado: `traducao.json`, `dublagem\`, `dublagem.wav`, `mix_dublado.wav`, `previa_dublagem.mp4` (o Revisor pode pedir ajuste de uma fala só). O app apaga `dublagem\` e a prévia depois da postagem.
- Se era volta do Revisor: `Rename-Item refazer.json refazer_1_feito.json`.

**Passo 62 — Passar para o Legendador e o Narrador.**
- Não é preciso mandar mensagem: eles veem o `traducao.json` na pasta. Confira que os campos `para_o_legendador` e `para_o_narrador` estão preenchidos.
- Quem move a pasta para `04_edicao` é o app (ou o Legendador, no passo 61 do manual 04), quando os três cargos terminarem.

**Passo 63 — Deu errado: `99_erros`.** Crie `erro.json` (UTF-8) e mova a pasta:
```json
{
  "etapa": "03_legenda_dublagem",
  "cargo": "tradutor",
  "quando": "2026-09-30T10:50:00-03:00",
  "motivo": "dublar.py não gera arquivo (erro ao carregar o modelo de voz)",
  "passo": 45,
  "o_que_tentou": "2 tentativas; --help funciona; teste do passo 7 também falha",
  "precisa_de": "conferir instalação da voz Piper; enquanto isso, o item pode sair só com legenda"
}
```
```powershell
Set-Location $esteira; Move-Item $item "$esteira\99_erros\"
```
- Atenção: se o problema é **só da voz**, a alternativa mais rápida é **legenda** (mude `decisao.modo` para `legenda`, escreva o motivo) em vez de travar o item. Só mande para `99_erros` se nem a legenda der.

**Passo 64 — Problema que se repete: ticket.** Com `scripts\tickets.py` (existente; veja `& $py "$scripts\tickets.py" --help`), área do app. Exemplos: "dublar.py sem opção de uma fala por arquivo", "voz lendo números errado", "ffmpeg sem sidechaincompress". Nunca ponha senha, token ou dado pessoal no ticket.

---

## 4. Regras que nunca se quebram

1. **[BLOQUEIA] Nunca clonar voz.** Nem do Antônio, nem de famoso, nem do narrador original, nem "uma voz parecida com a de fulano". Nunca treinar voz nova a partir de gravação de ninguém.
2. **[BLOQUEIA] Voz sintética só a Piper pt-BR gratuita já instalada, e só pelo `scripts\dublar.py`.** Nada de voz paga, voz de site, voz de aplicativo, ou modelo novo sem ordem do Antônio.
3. **[BLOQUEIA] Dublagem só em Destinos, Receitas, Carros e Filmes, e só em vídeo próprio** (`origem: "proprio"`, decidido pelo Curador).
4. **[BLOQUEIA] Futebol nunca tem narração sintética.** Vídeo de futebol vai **sempre com o áudio original** e, se estrangeiro, com legenda traduzida.
5. **[BLOQUEIA] GTA nunca tem voz sintética.** Legenda traduzida sempre. E nada de vazamento: se a fala original trouxer informação vazada, o item volta ao Curador.
6. **[BLOQUEIA] Nunca pôr voz sintética em cima de pessoa real falando na tela** (entrevista, depoimento, apresentador). Pessoa real = legenda.
7. **[BLOQUEIA] Valor citado leva "Valores aproximados…".** E cotação só a que vier no pedido — nunca inventada.
8. **Nunca inventar informação** que não está no original; nunca "melhorar" o fato. Tradução é fiel ao sentido.
9. **Nunca trocar negação** (o erro mais grave): "não" tem que continuar "não".
10. **O áudio original nunca é apagado** — na dublagem ele fica por baixo (abaixado), e volta nas pausas.
11. **Velocidade da voz só entre 0,85 e 1,15.** Não coube? Enxuga o texto.
12. **Nenhuma fala dublada por cima de outra.** Janela = até o início da próxima menos 0,15 s.
13. **Volume final −14 LUFS ± 1 e pico ≤ −1,5 dBTP.**
14. **Crédito do criador sempre** (quem põe na tela é o Legendador; o Tradutor nunca tira o crédito nem traduz o @).
15. **Na dúvida entre legendar e dublar: legenda.**
16. **Trabalho pesado (gerar voz, montar faixa, mixar) 1 por vez e nunca das 18h às 22h30**, nem para P0.
17. **Nada no disco C:**; tudo no H: (áudio, temporários) ou G: (glossários, configuração).
18. **Nunca alterar** `pedido.json`, `bruto.mp4`, `transcricao.json` ou arquivos de outro cargo; nunca renomear a pasta do item.
19. **Nunca apagar linha do `historico.log`.**
20. **Nada de token, senha ou dado pessoal** em arquivo, log ou ticket.
21. **Marcar `voz_sintetica: true`** para o Publicador (manual 10) quando houver dublagem.
22. **Nada passa para o app sem 7 dias de modo sombra** com qualidade idêntica comprovada por números.

---

## 5. Critérios de qualidade com nota

**Como funciona:** o Revisor (manual 09) dá nota de 0 a 10 em cada critério. Em item **só de legenda**, os critérios T6, T7, T8 e T9 **não se aplicam** (não entram na média). As notas entram na média geral do vídeo junto com as dos outros cargos.
- Média **≥ 9** = Excelente → aprovado · **7 a 8,9** = Bom → aprovado · **5 a 6,9** = Médio → volta para a etapa do critério de menor nota (se for um destes, `03_legenda_dublagem`, para o Tradutor) · **< 5** = Razoável → volta ao Curador · máximo **2 voltas**.
- **[BLOQUEIA]** com nota 0 = o item não sai, qualquer que seja a média.

| Cód. | Critério | Como medir | Nota 10 | Nota 7 | Nota 5 | Nota 0 | Volta para |
|---|---|---|---|---|---|---|---|
| T1 | Sentido fiel | Comparar cada segmento com o original (campo `literal` ajuda) | 0 erro de sentido | 1 nuance perdida, sem mudar fato | 1 fato secundário errado ou omitido | Fato principal errado, negação invertida ou informação inventada | 03 (Tradutor) |
| T2 | Naturalidade (pt-BR) | Ler em voz alta | Soa como brasileiro falando | 1 a 2 frases duras | 3+ frases com cara de tradução | Literal a ponto de ficar sem sentido ("trocador de jogo") | 03 (Tradutor) |
| T3 | Adaptação (unidades, moedas, títulos, estações, datas) | Procurar °F, cup, oz, mph, mpg, lb, datas em inglês, título original | 100% adaptado | 1 arredondamento esquisito (176,7 °C) | 1 unidade estrangeira sem conversão | Conversão que muda o fato (0–60 mph virou "0 a 100 km/h"; forno em °F) | 03 (Tradutor) |
| T4 | Nomes, títulos e termos do canal | Dicionário de nomes + glossário + título oficial no Brasil | Todos certos | 1 acento faltando em nome secundário | 1 termo fora do glossário ou título secundário errado | Nome principal ou título do filme errado | 03 (Tradutor) |
| T5 | Cabimento | Legenda: CPS de cada segmento (≤ 17). Voz: duração ≤ janela | Tudo dentro | 1 a 2 segmentos com CPS 17–20, ou voz até 5% além da janela sem sobrepor | 3+ segmentos fora, ou voz 5–15% além | CPS > 25, fala cortada ou sobreposta | 03 (Tradutor) |
| T6 | Sincronia da dublagem | `dublagem.medicao.desvio_max_ms` + prévia | Todas as falas ≤ 200 ms e 0 sobreposição | 1 fala entre 200 e 300 ms | 2+ falas entre 200 e 400 ms | Fala > 400 ms fora, falas sobrepostas, ou falando de algo que não está na imagem | 03 (Tradutor) |
| T7 | Qualidade da voz | Ouvir todas as falas | Clara, pronúncia certa, velocidade 0,85–1,15 | 1 palavra secundária mal pronunciada | 2–3 palavras ou 1 nome mal pronunciado | Voz cortada, estalando, "engasgada", ou velocidade fora de 0,85–1,15 | 03 (Tradutor) |
| T8 | Mixagem voz x fundo | Passo 57 (diferença em LU nos trechos falados) | 12 a 20 LU | 10–12 ou 20–24 LU | 8–10 ou mais de 24 LU | Menos de 8 LU (voz brigando), ou original sumiu por completo, ou original acima da voz | 03 (Tradutor) |
| T9 | Volume final (loudness) | `ebur128` no `mix_dublado.wav` (e no `final.mp4`, pelo Editor) | −14 ± 0,5 LUFS e pico ≤ −1,5 dBTP | −14 ± 1 e pico ≤ −1,0 | −14 ± 2 | Fora de ± 2 ou pico > −1,0 (estourando) | 03 (Tradutor) ou 04 (Editor, se o erro surgiu na música) |
| T10 | Regras de voz [BLOQUEIA] | Decisão x tabela da seção 1.6 | Decisão certa e registrada | (não existe meio-termo) | (não existe meio-termo) | Voz em Futebol/GTA, em vídeo não próprio, sobre pessoa real, ou outra voz / voz clonada | 03 (Tradutor), para refazer como legenda; se o erro veio do pedido, avisar o Curador (01) |
| T11 | "Valores aproximados…" [BLOQUEIA] | Todo segmento com dinheiro tem `"valor": true` | Todos marcados (ou não há valor) | (não existe meio-termo) | (não existe meio-termo) | Valor sem marcação, ou cotação inventada | 03 (Tradutor) |

**Exemplo (item dublado):** T1=10, T2=10, T3=10, T4=10, T5=7, T6=10, T7=7, T8=10, T9=10, T10=10, T11=10 → 104 ÷ 11 = **9,5 → Excelente**.
**Exemplo (item só de legenda):** T1=10, T2=7, T3=5, T4=10, T5=10, T10=10, T11=10 → 62 ÷ 7 = **8,9 → Bom** (aprovado). Se T3 fosse 0 ("0 a 100 km/h" errado): 57 ÷ 7 = 8,1 — aprovado pela média, **mas** este manual recomenda ao Revisor tratar conversão que muda o fato como erro público: **nota 0 em T1 ou T3 devolve para 03, mesmo com média ≥ 7**.

---

## 6. Erros comuns e o que fazer

| Sintoma | Causa provável | Solução |
|---|---|---|
| Tradução "robótica" ("Nós vamos entrar direto nisso") | Tradução ao pé da letra | Passo 26: traduzir pelo sentido; ler em voz alta |
| "0 a 100 km/h" num carro americano | Converteu 0–60 mph para o número "redondo" brasileiro | 0–60 mph = **0 a 96 km/h**; nunca 0 a 100 |
| Forno em °F na legenda | Esqueceu a conversão | Tabela da seção 2.11: 350 °F → 180 °C |
| Título do filme em inglês | Não conferiu o título brasileiro | Pôster oficial brasileiro; glossário de Filmes |
| Voz lê "km/h" como "ká-ême-barra-agá" | Texto da voz com símbolo | Passo 39: por extenso pela `pronuncia.txt` |
| Voz lê número em inglês ou esquisito ("3.2") | Ponto decimal | Escrever "três vírgula dois" no texto da voz |
| Nome estrangeiro pronunciado errado | A voz lê com regra do português | `pronuncia.txt` com a grafia "como soa" (só no texto da voz) |
| Fala dublada não cabe na janela | Português mais comprido que o original | Passo 42 (enxugar); velocidade até 1,15 (passo 49) |
| Duas falas dubladas se atropelam | Janela calculada sem a margem de 0,15 s, ou velocidade não aplicada | Refazer passos 40–41 e 49; `montar_faixa.py` de novo |
| `fora do limite` > 0 no `montar_faixa.py` | O `.wav` da fala tem silêncio no começo (a voz começa depois do planejado) | Cortar o silêncio do começo: `& $ff -y -i seg.wav -af "silenceremove=start_periods=1:start_threshold=-45dB" seg_limpo.wav` e remontar |
| `dublar.py` não gera arquivo | Modelo de voz não encontrado, caminho com acento, ou opção errada | Rodar o teste do passo 7; conferir as opções no `--help`; se persistir: legenda + ticket |
| `dublar.py` só aceita o vídeo inteiro | Script feito para outro uso | Ticket pedindo "uma fala por arquivo" (a criar); até lá, legenda |
| Voz some ou fica muito baixa na mistura | Ordem das entradas trocada no `sidechaincompress` (a voz foi abaixada no lugar do fundo) | A ordem é `[orig][sc]sidechaincompress` (primeiro o que abaixa, depois o que manda) |
| O original some por completo | Abaixamento forte demais (`ratio` alto) | `ratio=3` no passo 54; conferir no passo 57 (12 a 20 LU) |
| Voz "brigando" com o original | Abaixamento fraco | `ratio=6`; conferir no passo 57 |
| Volume final −16 ou −12 LUFS | `loudnorm` de uma passada em vídeo curto errou | Passo 56 (correção com `volume=`) |
| Pico acima de −1,5 dBTP | Correção de volume empurrou o pico | Não subir o volume; refazer o passo 54 e aceitar I entre −15 e −13 |
| Erro "Option normalize not found" | ffmpeg antigo | Tirar `:normalize=0` e pôr `,volume=2` depois do `amix`; ticket para atualizar |
| `dublagem.wav` com duração diferente do vídeo | Duração errada no `traducao.json` | Copiar `duracao_s` da transcrição e remontar (o roteiro corta/completa no tamanho exato) |
| Chiado ou "clique" no início de cada fala | Corte seco do arquivo | Gerar de novo; se persistir, `afade=t=in:d=0.02` no começo da fala |
| Pessoa falando na tela com voz sintética por cima | Não conferiu a condição 4 | [BLOQUEIA] — refazer como legenda |
| Pedido de futebol com `tratamento: dublagem` | Erro do pedido | Não dublar; legenda + histórico com o motivo; avisar o Pauteiro |
| Cotação "chutada" | Pedido sem `cotacao` | Nunca inventar: deixar a moeda original + aviso |
| Idioma errado (vídeo em espanhol tratado como português de Portugal) | Detecção de idioma | Conferir `idioma_detectado`; pt-PT → legenda em pt-BR adaptando palavras ("autocarro" → "ônibus") |
| `TravaOcupada` | Horário proibido ou outro pesado rodando | Esperar; nunca apagar o `pesado.lock` |
| Revisor devolveu 2 vezes | Problema no material ou na ferramenta | Não tentar a 3ª: `99_erros` + ticket |

---

## 7. O que o app faz sozinho x o que o Claude decide

**Meta:** o app fazer toda a parte mecânica (decidir pela tabela, conversões, pronúncia, gerar voz, encaixar, mixar, medir). O Claude fica com o que é linguagem (traduzir pelo sentido, enxugar, gírias, piadas).

| Passo(s) | Tarefa | App sozinho | Claude decide | Observação |
|---|---|---|---|---|
| 11–16 | Horário, fila, pedido, transcrição, volta | 100% | 0% | Regras fixas |
| 17–18, 21 | Condições 1, 2, 3 e 6 da decisão | 100% | 0% | Campos do pedido |
| 19 | Condição 4: pessoa real falando na tela? | 40% | 60% | O app pode sugerir pelo `narracao_em_off` do pedido; confirmação é visual (Claude olha 3–5 quadros) |
| 20 | Condição 5: cabe no tempo? (estimativa) | 100% | 0% | Conta com `cps_medido` |
| 23–26 | Traduzir pelo sentido | 0% | 100% | Parte mais cara em token; um dia pode haver rascunho offline (seção 8.6) |
| 27, 31 | Unidades, datas, estações | 90% | 10% | Tabela `conversoes.json`; Claude confere o contexto (ex.: "aro 20" não converte) |
| 28 | Moeda e aviso | 95% | 5% | Cotação vem do pedido; marcação automática de `valor` por símbolo |
| 29 | Nomes e títulos | 80% | 20% | Dicionários e glossários; nome novo = Claude |
| 30 | Gírias, piadas | 10% | 90% | Glossário cobre as frequentes |
| 32 | Caber na legenda (CPS) | 70% | 30% | App mede e aponta; Claude enxuga |
| 33–35 | Conferir números, reler, "tradução de volta" | 30% | 70% | App compara números do original com os da tradução |
| 36–38 | Gravar JSON, validar, histórico | 100% | 0% | |
| 39 | Texto da voz (por extenso) | 95% | 5% | `pronuncia.txt` + número por extenso automático |
| 40–41 | Janela e duração estimada | 100% | 0% | |
| 42 | Enxugar fala que não cabe | 0% | 100% | Julgamento de linguagem |
| 43 | Combinar com Toque HP | 100% | 0% | Regra fixa (2,10 s; fecho) |
| 44–50 | Gerar voz, medir, pronúncia, velocidade | 90% | 10% | Claude só ouve fala que o app marcar (ex.: palavra fora do dicionário) |
| 51–53 | Montar faixa e medir desvio | 100% | 0% | `montar_faixa.py` (provisório) → módulo (a criar) |
| 54–57 | Mixar e medir LUFS e voz x fundo | 100% | 0% | Números fixos |
| 58–59 | Prévia e escuta | 60% | 40% | App mede tudo; escuta final é humana/Claude até o fim da sombra |
| 60–64 | Entregar, erros, ticket | 90% | 10% | |
| **Total (item dublado)** | | **≈ 65%** | **≈ 35%** | A tradução em si é o grosso da parte do Claude |
| **Total (item só de legenda)** | | **≈ 45%** | **≈ 55%** | Meta em 3 meses: glossários maiores → 55% / 45% |

**Como gastar menos token aqui:**
1. O Claude recebe **só o texto** da transcrição (não o vídeo) + o glossário do canal + a tabela de conversões — nunca o arquivo de áudio.
2. Uma chamada por vídeo (todos os segmentos de uma vez), pedindo de volta **só** os campos `legenda`, `voz` e `notas`.
3. Enxugar fala (passo 42) vai numa chamada curta, só com as falas que estouraram.
4. Todo termo que o Claude traduziu de um jeito bom e que vai se repetir entra no glossário (o app passa a fazer sozinho).

---

## 8. Ferramentas existentes que já fazem cada passo

### 8.1 Tabela rápida
| Passo | Ferramenta | Situação |
|---|---|---|
| Transcrição do original (antes do Tradutor) | faster-whisper + roteiro do manual 04 | (a instalar, se faltar) / (provisório) |
| 45–49 (gerar voz) | **`scripts\dublar.py`** com a voz **Piper pt-BR** já instalada | (existente) |
| 46, 53, 55, 57 (medir) | **ffmpeg** (`Duration`, `ebur128`, `silencedetect`) | (existente) |
| 49 (acelerar sem mudar o tom) | ffmpeg `atempo` | (existente) |
| 52 (montar faixa) | `H:\HypadoLocal\app\provisorio\montar_faixa.py` (seção 8.7) | (provisório) |
| 54 (mixar e nivelar) | ffmpeg `loudnorm`, `sidechaincompress`, `amix` | (existente) |
| 27–31 (conversões, glossário, pronúncia) | `config\conversoes.json`, `dicionarios\glossario_<canal>.txt`, `dicionarios\pronuncia.txt` | (a criar) |
| Trava e horário | `hpbase.TravaPesada` | (existente) |
| JSON e histórico | `hpbase.escrever_json`, `hpbase.anexar_linha` | (existente) |
| Subprocesso sem janela preta | `hpbase.rodar` | (existente) |
| Módulo tradutor da esteira (tudo automático) | etapa 3 do app | (a criar) |
| Comparar com o feito pelo Claude (7 dias) | `qa_paridade` (duração, loudness, texto e tempos) | (a criar — módulo D) |
| Tickets | `scripts\tickets.py` | (existente) |

### 8.2 `scripts\dublar.py` (a porta da voz)
É o script da HP que transforma texto em fala em português usando a voz Piper já instalada no PC. **É a única forma permitida de gerar voz na HP.** Não reescreva e não contorne: se faltar alguma opção (por exemplo, uma fala por arquivo ou velocidade), abra ticket para acrescentar. Os nomes exatos das opções estão no `--help` e ficam anotados no `config\voz.json`.

### 8.3 Piper (explicado para leigo)
É um programa gratuito que "lê em voz alta" um texto, usando um arquivo de voz (`.onnx`, com um `.onnx.json` ao lado que descreve a voz). Roda no próprio PC, sem internet e sem pagar nada. A voz é **sintética** (não é de uma pessoa específica), o que é exatamente o que a regra "nunca clonar voz" exige. Ajustes que o Piper conhece (o `dublar.py` pode ou não repassar):
- **length scale**: velocidade. 1,0 = normal; **menor que 1 = mais rápido** (0,91 ≈ 10% mais rápido); maior que 1 = mais lento.
- **sentence silence**: pausa depois de cada frase (em segundos).
- **noise scale / noise w**: variação da voz; deixe no padrão (mexer deixa a voz instável).
A saída normalmente é WAV de 22 050 Hz, mono. O `montar_faixa.py` converte para 48 000 Hz.

### 8.4 ffmpeg: os filtros de áudio usados neste manual
| Filtro | Para quê (em português) |
|---|---|
| `aresample=48000` | Converte para 48 mil amostras por segundo (o padrão de vídeo) |
| `aformat=channel_layouts=mono` | Deixa em 1 canal |
| `adelay=4600` | Atrasa a fala 4.600 ms (ela começa em 4,6 s) |
| `amix` | Junta vários sons num só (`normalize=0` = não abaixa cada um) |
| `apad` / `atrim` | Completa com silêncio / corta, para ter a duração exata |
| `loudnorm` | Deixa o volume "percebido" no alvo (−20, −16, −14 LUFS) |
| `sidechaincompress` | Abaixa um som (o original) **enquanto** outro (a voz) toca |
| `ebur128` | Mede o volume percebido (LUFS) e o pico |
| `silencedetect` | Acha onde tem silêncio (e, portanto, onde a voz começa) |
| `atempo` | Acelera ou desacelera **sem** mudar o tom da voz |
| `silenceremove` | Tira silêncio do começo de um arquivo |
| `afade` | Entrada/saída suave (tira o "clique") |

### 8.5 faster-whisper (uso no Tradutor)
Não é o Tradutor que roda, mas ele depende disso: o Legendador (manual 04) usa para transcrever o original e **para achar o tempo de cada palavra da voz dublada** (karaokê sobre a dublagem). Também é ele que diz o idioma do vídeo (`idioma_detectado`).

### 8.6 Tradução automática offline (não instalada — a avaliar)
Existem tradutores gratuitos que rodam no PC sem internet (por exemplo, o Argos Translate). **Não estão instalados e não fazem parte do processo hoje.** Podem ser avaliados no futuro só para fazer um **rascunho** que o Claude corrige (economia de token), e só depois de 7 dias de sombra provando que a nota T1/T2 não cai. Até lá: tradução = Claude.

### 8.7 Roteiro provisório de montagem da faixa (`H:\HypadoLocal\app\provisorio\montar_faixa.py`)
Usado no passo 52. Lê `traducao.json → dublagem.segmentos` (`inicio_planejado` e `arquivo` de cada fala) e `duracao_s`, monta `dublagem.wav` (48 kHz, mono, duração exata), mede o início real de cada fala (`silencedetect`) e grava o desvio. Copie exatamente (salvar em UTF-8):
```python
"""montar_faixa.py - PROVISORIO (manual 05, Tradutor e dublador).

Junta as falas dubladas (um .wav por segmento, gerados pelo scripts\\dublar.py)
numa faixa unica do tamanho do bruto (dublagem.wav, 48 kHz mono), cada fala
no seu tempo, e mede onde cada fala comecou de verdade (desvio em ms).
Vale ate o modulo tradutor da etapa 3 do app existir.

Uso (PowerShell):
  & $py H:\\HypadoLocal\\app\\provisorio\\montar_faixa.py --item <pasta>
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, r"G:\Meu Drive\Hypado\06 Projeto\app\hp_studio")

LIMITE_DESVIO_MS = 200


def montar_comando(ffmpeg, segmentos, duracao, saida):
    """Monta o comando do ffmpeg: cada fala atrasada ate o seu inicio e somada."""
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y"]
    for s in segmentos:
        cmd += ["-i", s["arquivo"]]
    partes, rotulos = [], []
    for n, s in enumerate(segmentos):
        atraso = max(0, int(round(s["inicio"] * 1000)))
        partes.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=mono,"
                      f"adelay={atraso}[s{n}]")
        rotulos.append(f"[s{n}]")
    d = f"{duracao:.3f}"
    partes.append("".join(rotulos) + f"amix=inputs={len(segmentos)}:duration=longest:"
                  f"normalize=0,apad=whole_dur={d},atrim=0:{d}[a]")
    cmd += ["-filter_complex", ";".join(partes), "-map", "[a]",
            "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(saida)]
    return cmd


def inicios_de_fala(texto_ffmpeg):
    """Le a saida do silencedetect e devolve os instantes em que a voz comeca."""
    comecos = re.findall(r"silence_start: (-?[\d.]+)", texto_ffmpeg)
    inicios = [0.0] if not comecos or float(comecos[0]) > 0.05 else []
    inicios += [float(x) for x in re.findall(r"silence_end: ([\d.]+)", texto_ffmpeg)]
    return inicios


def comparar(planejados, medidos):
    """Para cada inicio planejado, acha o medido mais perto e devolve o desvio em ms."""
    saida = []
    for p in planejados:
        if not medidos:
            saida.append(None)
            continue
        m = min(medidos, key=lambda x: abs(x - p))
        saida.append(int(round((m - p) * 1000)))
    return saida


def main():
    ap = argparse.ArgumentParser(description="Monta a faixa dublagem.wav de um item (manual 05).")
    ap.add_argument("--item", required=True, help="pasta do item na esteira")
    a = ap.parse_args()
    from hpbase import (TravaPesada, rodar, achar_ffmpeg, ler_json, escrever_json,
                        anexar_linha)
    item = Path(a.item)
    trad = ler_json(item / "traducao.json")
    dub = trad["dublagem"]
    segs = [{"id": s["id"], "inicio": s["inicio_planejado"],
             "arquivo": str(item / s["arquivo"])} for s in dub["segmentos"]]
    ff = achar_ffmpeg()
    saida = item / "dublagem.wav"
    with TravaPesada("tradutor:montar_faixa"):
        r = rodar(montar_comando(ff, segs, trad["duracao_s"], saida), timeout=600)
        if r.returncode != 0:
            print(r.stderr.decode("utf-8", "replace")[-800:])
            sys.exit(1)
        r2 = rodar([ff, "-hide_banner", "-nostats", "-i", str(saida), "-af",
                    "silencedetect=noise=-40dB:d=0.25", "-f", "null", "-"], timeout=300)
    medidos = inicios_de_fala(r2.stderr.decode("utf-8", "replace"))
    desvios = comparar([s["inicio"] for s in segs], medidos)
    ruins = 0
    for s, d in zip(dub["segmentos"], desvios):
        s["desvio_inicio_ms"] = d
        if d is None or abs(d) > LIMITE_DESVIO_MS:
            ruins += 1
    dub["medicao"] = {"segmentos": len(segs), "fora_do_limite": ruins,
                      "limite_ms": LIMITE_DESVIO_MS,
                      "desvio_max_ms": max((abs(d) for d in desvios if d is not None), default=None)}
    escrever_json(item / "traducao.json", trad)
    anexar_linha(item / "historico.log",
                 f"[03] tradutor: dublagem.wav montada ({len(segs)} falas, "
                 f"desvio max {dub['medicao']['desvio_max_ms']} ms, {ruins} fora do limite)")
    print(f"OK: {len(segs)} falas; desvio max {dub['medicao']['desvio_max_ms']} ms; "
          f"{ruins} fora do limite de {LIMITE_DESVIO_MS} ms")


if __name__ == "__main__":
    main()
```

---

## 9. Testes de aceitação

Uma entrega do Tradutor e dublador só é aceita se passar em **todos** os testes que se aplicam ao item. Para o app assumir a tarefa: **7 dias seguidos de modo sombra** passando em tudo, com o `qa_paridade` (a criar) comparando com o feito pelo Claude.

### 9.1 Decisão e regras
1. 100% dos itens de **Futebol** e **GTA** com `decisao.modo` = `legenda` (0 dublagem, 0 voz sintética).
2. 100% dos itens dublados com `canal` ∈ {destinos, receitas, carros, filmes}, `origem` = `proprio`, `voz_sintetica_permitida` = `true` e `narracao_em_off` confirmada.
3. 0 fala dublada sobre trecho com pessoa real falando na tela (conferido nos quadros da prévia).
4. 0 voz gerada fora do `scripts\dublar.py`; 0 modelo de voz diferente do registrado em `config\voz.json`.
5. `decisao.motivo` preenchido em 100% dos itens.
6. 0 trabalho pesado (gerar voz, montar, mixar) registrado no `historico.log` entre 18:00 e 22:29.

### 9.2 Tradução
7. 100% dos segmentos da transcrição traduzidos (mesmos `id`, mesma quantidade).
8. Em 5 vídeos de teste conferidos por gente: **0** erro de fato principal, **0** negação invertida, **0** informação inventada.
9. **0** unidade estrangeira sem conversão na legenda (°F, cup, oz, lb, mph, mpg, miles, feet, gallons).
10. **100%** das conversões dentro de **± 2%** do valor exato (ex.: 350 °F → 180 °C está a 1,9% de 176,7 °C: ok; 0–60 mph → 0–100 km/h está 3,6% fora: **reprova**).
11. **100%** dos títulos de filme/série no título oficial brasileiro.
12. **100%** dos segmentos com dinheiro marcados `"valor": true`; 0 cotação que não veio do pedido.
13. CPS da legenda **≤ 17** em pelo menos **95%** dos segmentos e **≤ 20** em 100%.

### 9.3 Voz e encaixe (só itens dublados)
14. Cada fala: duração real **≤ janela** (início da próxima − 0,15 s).
15. Velocidade de cada fala entre **0,85 e 1,15**.
16. Desvio do início de cada fala **≤ ± 200 ms** (medido pelo `montar_faixa.py`); média **≤ 80 ms**.
17. **0** sobreposição entre falas dubladas.
18. `dublagem.wav`: **48 000 Hz, mono**, duração = duração do `bruto.mp4` **± 0,02 s**, pico ≤ −1 dBFS.
19. Em 5 vídeos de teste: **0** nome próprio mal pronunciado e no máximo **1** palavra comum estranha por vídeo.
20. Nenhuma fala com silêncio de mais de **0,30 s** no começo do arquivo.

### 9.4 Mixagem e volume (só itens dublados)
21. `mix_dublado.wav`: **48 000 Hz, estéreo**, mesma duração do bruto ± 0,02 s.
22. Volume integrado **−14 LUFS ± 1** (meta ± 0,5).
23. Pico real **≤ −1,5 dBTP**.
24. Voz **12 a 20 LU** acima do fundo no trecho da fala mais longa (passo 57).
25. Fundo presente: nas pausas de mais de 1 s entre falas, o original volta a pelo menos **−26 LUFS** (não pode sumir o clima).

### 9.5 Arquivos e registro
26. `traducao.json` válido (`json.tool` sai com código 0) com todos os campos da seção 2.6 que se aplicam.
27. `historico.log` com pelo menos 2 linhas `[03] tradutor:` (decisão e resultado) com números.
28. `para_o_legendador` e `para_o_narrador` preenchidos.
29. Nenhum arquivo de outro cargo alterado (comparar data de modificação de `pedido.json`, `bruto.mp4`, `transcricao.json` antes e depois).

### 9.6 Desempenho (para o app)
30. Gerar voz de 20 s de fala: **≤ 1 min** no PC do Antônio.
31. Montar faixa + mixar + medir, vídeo de 30 s: **≤ 1 min**.
32. Na paridade de 7 dias: nota média T1–T11 do app **≥ nota média do Claude − 0,2**, e **0** item do app com T10 ou T11 em 0.

### 9.7 Casos de teste obrigatórios
| # | Caso | O que tem que acontecer |
|---|---|---|
| D1 | GTA, Rockstar em inglês, pedido pede `dublagem` por engano | Decisão = legenda; motivo "GTA: voz sintética não permitida"; legenda com "GTA 6" e nomes oficiais |
| D2 | Futebol, clube espanhol, entrevista | Legenda traduzida; áudio original intacto; "golaço", "técnico", "contratação" |
| D3 | Filmes, entrevista de ator em inglês | Legenda (pessoa real falando); título brasileiro |
| D4 | Receitas, vídeo próprio com narração em off em inglês com °F e cups | Dublagem; 180 °C e xícaras/gramas na legenda; por extenso na voz; −14 LUFS |
| D5 | Carros, material de imprensa com narração em off, "0 to 60 in 3.2" e preço | Dublagem; "0 a 96 km/h"; "US$ 45 mil" + aviso; voz 12–20 LU acima do fundo |
| D6 | Destinos, vídeo próprio em italiano (Cinque Terre) | Dublagem; estação "de lá" com meses; € com conversão da cotação do pedido; desvio ≤ 200 ms |
| D7 | Destinos, vídeo próprio com 3 s de entrevista no meio | Legenda no vídeo todo (padrão) ou dublagem só no off + legenda na entrevista, com motivo registrado |
| D8 | Fala que estoura a janela em 25% | Texto enxugado (não velocidade 1,25); velocidade final ≤ 1,15 |
| D9 | `dublar.py` falhando | Item sai com legenda (decisão mudada e registrada) ou vai para `99_erros` com `erro.json`; ticket aberto |
| D10 | Volta do Revisor por T6 | Só a fala apontada refeita; `refazer_1_feito.json` criado; desvio medido de novo |

---

## Glossário

| Palavra | O que quer dizer |
|---|---|
| **Adaptação** | Traduzir mudando o que precisa para o brasileiro entender (medidas, moedas, títulos, gírias), sem mudar o fato. |
| **Áudio original** | O som que veio no vídeo (voz, ambiente, música). Na HP ele nunca é apagado. |
| **Abaixamento (ducking)** | Baixar o som original automaticamente só enquanto a voz em português fala. |
| **Cotação** | Quanto vale 1 unidade de moeda estrangeira em reais naquele dia. Só a que vem no pedido. |
| **CPS** | Caracteres por segundo: quantas letras a pessoa precisa ler (legenda) ou a voz precisa falar (dublagem) por segundo. |
| **dBTP / pico real** | O ponto mais alto do som. Acima de −1,5 dBTP pode "estourar" (chiar) nos celulares. |
| **Dublagem** | Trocar a fala estrangeira por uma voz em português. Na HP: voz Piper, "por cima" do original abaixado. |
| **`dublar.py`** | O script da HP que gera a voz em português (a única porta permitida). |
| **Enxugar** | Dizer a mesma coisa com menos palavras. |
| **Glossário** | Lista de termos com a tradução oficial da HP para cada canal. |
| **Janela** | O tempo que uma fala dublada tem para caber: do início dela até o início da próxima menos 0,15 s. |
| **Legenda traduzida** | Manter o áudio original e pôr o texto em português na tela. |
| **LU / LUFS** | Unidades de volume "percebido". −14 LUFS é o padrão das redes; "LU" é a diferença entre dois volumes. |
| **Literal / ao pé da letra** | Tradução palavra por palavra (serve só para conferência; nunca vai para o vídeo). |
| **Mixagem (mistura)** | Juntar a voz e o som original num arquivo só, cada um no volume certo. |
| **Narração em off** | Voz de narrador que não aparece falando na tela. Só ela pode ser dublada. |
| **Negação invertida** | Erro de trocar "não" por "sim" (ou o contrário) na tradução. O mais grave. |
| **Piper** | Programa gratuito, instalado no PC, que lê texto em voz alta com uma voz sintética pt-BR. |
| **Pronúncia (`pronuncia.txt`)** | Lista de como a voz deve falar siglas, números, símbolos e nomes estrangeiros. |
| **Retrotradução ("tradução de volta")** | Ler o português e conferir se diz o mesmo que o original. |
| **Sincronia** | A fala entrar junto com a imagem certa. Na dublagem: até 200 ms de diferença. |
| **Vídeo próprio** | Vídeo montado pela HP com material que ela pode usar, cuja narração é da HP. Marcado pelo Curador (`origem: "proprio"`). |
| **Voice-over ("voz por cima")** | Estilo de documentário: a voz traduzida fala por cima do original abaixado. |
| **Voz clonada** | Voz feita para imitar uma pessoa real. **Proibida** na HP. |
| **Voz sintética** | Voz gerada por computador (a Piper). Só em Destinos, Receitas, Carros e Filmes, só em vídeo próprio. |
