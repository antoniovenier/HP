# Manual 08 — Redator (HP Studio)

> **Versão:** 1.0 — 30/09/2026 · **Cargo nº 08 da esteira** · vale para os 6 canais da Hypado (HP)
> **Onde este arquivo mora no PC:** `G:\Meu Drive\Hypado\06 Projeto\app\manuais\08_redator.md`
> **Status:** manual novo, ainda não revisado pelo Antônio. Tudo o que está marcado **(a criar)** ainda **não existe** no PC. O resto já existe e funciona hoje.
> **Quem usa:** o Claude (hoje), o app HP Studio (depois dos 7 dias de modo sombra, nas partes que são regra) e qualquer pessoa leiga que precise escrever à mão.

---

## Sumário

1. Objetivo do cargo
2. Entradas e saídas (arquivos, `post.json` completo, limites de cada rede, tom e hashtags de cada canal)
3. Passo a passo numerado para leigo (60 passos)
4. Regras que nunca se quebram
5. Critérios de qualidade com nota
6. Erros comuns e o que fazer
7. O que o app faz sozinho x o que o Claude decide
8. Ferramentas existentes que já fazem cada passo
9. Testes de aceitação
10. Glossário

---

## Como ler este manual (se você nunca fez isso)

- Cada passo da seção 3 tem 4 partes: **Abra** (o que abrir), **Rode** (comando para copiar e colar no PowerShell, quando houver), **Confira** (o que olhar), **Deve aparecer** (o resultado certo). Deu diferente? Seção 6.
- **PowerShell**: aperte `Windows + X` → **Terminal**. Colar = botão direito ou `Ctrl + V`, depois `Enter`.
- **Caractere** é cada letra, número, espaço, sinal ou emoji. "Comenta aí 👇" tem 12 caracteres (o emoji conta 1 no nosso contador; algumas redes contam 2 — por isso a HP sempre deixa folga).
- **Legenda do post** (o texto embaixo do vídeo, que alguns chamam de "caption" ou "descrição") **não é** a legenda do vídeo (as letrinhas queimadas na imagem, que são do Legendador, manual 04). Neste manual, "legenda" é sempre **o texto do post**.
- Nunca escreva sobre um vídeo que você não viu (ou cuja transcrição você não leu). É assim que nasce o clickbait mentiroso.

---

## 1. Objetivo do cargo

### 1.1 Em uma frase

O Redator escreve **todo texto que acompanha um post da HP** — título da capa, gancho de tela, legenda de cada rede (Instagram, Facebook, TikTok, YouTube Shorts, Threads, Pinterest), título e descrição do YouTube, hashtags, CTA "comenta aí", crédito "Vídeo: @criador", aviso "Valores aproximados…", pergunta e opções da enquete do story e o título curto do aviso "no ar" — **no tom informal brasileiro, dentro do limite de cada rede, sem mentir, sem vazamento de GTA 6 e sem nada do Flow Games**.

### 1.2 Por que isso importa para a monetização

- **O texto é metade do gancho.** O título da capa e a primeira linha da legenda decidem se a pessoa assiste, abre o carrossel ou passa.
- **Comentário empurra alcance.** Toda rede mostra mais o post que gera conversa. Uma pergunta boa no fim ("comenta aí: vai comprar no dia 19/11?") transforma espectador em comentário.
- **Busca é crescimento de graça.** YouTube, Pinterest e TikTok funcionam como buscadores. Título e descrição com as palavras que as pessoas procuram ("bolo de cenoura fofinho", "carro mais barato 2026", "Gramado barato") trazem visualização por meses.
- **Mentira mata o perfil.** Clickbait mentiroso gera "não tenho interesse", denúncia e perda de alcance — e afasta a monetização. A HP ganha confiança sendo **rápida e certa**.
- **Crédito protege a conta.** Post sem crédito leva denúncia de direito autoral; três denúncias podem derrubar a conta — e com ela a monetização.

### 1.3 O que o Redator escreve (por tipo de item)

| Tipo do item | O que o Redator entrega no `post.json` |
|---|---|
| `reel` | `titulo_capa`, `subtitulo_capa` (opcional), `gancho_tela`, legenda de cada rede em `redes`, título e descrição do YouTube, crédito, hashtags, `aviso.titulo_curto` |
| `carrossel` | legenda de cada rede, crédito(s), hashtags, revisão de ortografia e tom do texto das lâminas (no `pedido.json`, passo 20), `aviso.titulo_curto` |
| `story` | texto da arte (quando o pedido não trouxe) — curto, até 25 palavras |
| `story_enquete` (GTA 16h) | `enquete.pergunta` (até ~25 caracteres), `enquete.opcoes` (2 opções curtas), `enquete.pergunta_longa` para a arte |
| `pin` | título do pin, descrição, texto alternativo, link |
| `threads_texto` | o texto do Threads (até 500 caracteres) e o tópico |
| `threads_imagem` | o texto do Threads que acompanha a imagem |

### 1.4 O que o Redator NÃO faz

- **Não escolhe o tema** (Curador, manual 01) e **não inventa fato**: tudo que ele escreve tem que estar no vídeo, na transcrição, no pedido ou numa fonte oficial citada no pedido.
- **Não faz a legenda queimada do vídeo** (Legendador, manual 04), **não narra** (Narrador, manual 06), **não faz a arte** (Designer, manual 07).
- **Não publica** (Publicador, manual 10) e **não manda o aviso "no ar"** — o aviso é montado a partir do modelo em `06 Projeto\AVISO.md`; o Redator só entrega o título curto que entra nele.
- **Não aprova o próprio texto** (Revisor, manual 09).

### 1.5 Metas com número

| Meta | Número |
|---|---|
| Textos dentro do limite de cada rede | 100% |
| Posts com crédito correto em todas as redes | 100% |
| Posts com valor citado sem "Valores aproximados…" | 0 |
| Posts com qualquer menção a vazamento de GTA 6 ou ao Flow Games | 0 |
| Posts com pergunta de CTA no fim | 100% (exceto P0 de gol, em que a pergunta pode ser o próprio placar: "e aí, foi golaço?") |
| Nota do Revisor nos critérios "Texto do post" e "Título da capa" | média ≥ 9 na semana |
| Tempo por item (Claude) | reel ≤ 6 min · carrossel ≤ 8 min · P0 ≤ 3 min |
| Tempo por item (app, partes de regra) | ≤ 10 s |

---

## 2. Entradas e saídas

### 2.1 A esteira em 1 minuto

Cada post é **uma pasta** em `H:\HypadoLocal\esteira\` que anda por estas etapas:

```
01_pedidos  →  02_baixados  →  03_legenda_dublagem  →  04_edicao  →  05_revisao  →  06_agendados  →  07_postados
(Curador)      (bruto+corte)   (legenda, dublagem,      (Editor,       (Revisor:       (app agenda;      (aviso "no ar")
                                narração)                DESIGNER,      aprovado ou     TikTok pelo
                                                         REDATOR)       refazer)        Chrome)
                                                                                                  99_erros (erro ou descarte)
```

**Onde o Redator entra:** na etapa `04_edicao`. Para vídeo, ele escreve assim que existir a transcrição (`transcricao.json`) ou o `final.mp4` — não precisa esperar a edição terminar. O Designer depende do `titulo_capa` dele, então **o Redator trabalha antes do Designer**. Para estáticos (carrossel, story, pin, Threads), o item entra em `01_pedidos` com o campo `tipo`, pula as etapas de vídeo (02 e 03) e cai direto em `04_edicao`.

**Nome da pasta do item:** `P1_2026-09-30_1830_gta_rockstar-quinta` = prioridade (`P0_` urgente/ao vivo, `P1_` do dia, `P2_` programado) + data de postagem + hora de postagem + canal + apelido. Ordenando por nome, o mais urgente fica em cima.

### 2.2 O que o Redator lê e o que escreve

| Arquivo | Quem cria | O Redator… | Para quê |
|---|---|---|---|
| `pedido.json` | Curador | **lê** (e, só em carrossel, corrige ortografia/tom das lâminas) | tema, canal, redes, fonte/criador, valores, observações |
| `transcricao.json` | app (etapa 02) | **lê** | saber exatamente o que o vídeo diz — base de todo texto |
| `legenda.srt` | Legendador | **lê** (opcional) | conferir nomes próprios e números como aparecem no vídeo |
| `final.mp4` | Editor | **assiste** (quando já existir) | conferir que o texto promete só o que o vídeo mostra |
| `post.json` | **Redator** | **escreve** | todos os textos do post, por rede |
| `historico.log` | todos | **acrescenta 1 linha** | registro |
| `refazer.json` | Revisor | **lê** quando o item volta | saber o que corrigir |
| `06 Projeto\AVISO.md` | já existe | **lê** | modelo do aviso "no ar" |
| `07 Canais\<Canal>\…` | já existe | **lê** | plano e orientações de cada canal (ex.: `07 Canais\Futebol\PLANO_CRESCIMENTO.md`) |

### 2.3 Exemplo de `transcricao.json` (entrada)

O app grava a transcrição na etapa 02. O Redator só lê o campo `texto` e, se precisar, os trechos com tempo.

```json
{
  "esquema": "hp.transcricao/1",
  "item": "P1_2026-09-30_1830_gta_rockstar-quinta",
  "idioma": "pt-BR",
  "duracao_s": 38.4,
  "texto": "A Rockstar acabou de postar que quinta-feira tem novidade do GTA 6. Ela não disse o que é, mas da última vez que fez isso veio trailer. Faltam cinquenta dias pro lançamento, dezenove de novembro. O que você acha que vem aí?",
  "trechos": [
    {"inicio": 0.0, "fim": 4.2, "texto": "A Rockstar acabou de postar que quinta-feira tem novidade do GTA 6."},
    {"inicio": 4.2, "fim": 9.8, "texto": "Ela não disse o que é, mas da última vez que fez isso veio trailer."},
    {"inicio": 9.8, "fim": 15.1, "texto": "Faltam cinquenta dias pro lançamento, dezenove de novembro."},
    {"inicio": 15.1, "fim": 18.0, "texto": "O que você acha que vem aí?"}
  ]
}
```

Repare: o vídeo **não** diz que vem trailer; diz que "da última vez veio". Então o título **não pode** ser "TRAILER 3 NA QUINTA!" (seria mentira). Pode ser "ROCKSTAR SOLTA NOVIDADE NA QUINTA?".

### 2.4 Saída: `post.json` completo (exemplo real de reel do GTA 6)

O `post.json` é **o** arquivo do Redator. O Publicador posta **exatamente** o `texto_final` de cada rede (letra por letra). As `partes` existem para o app e o Revisor conferirem sem precisar "ler" o texto: o app junta as partes e confere se dá igual ao `texto_final`.

```json
{
  "esquema": "hp.post/1",
  "item": "P1_2026-09-30_1830_gta_rockstar-quinta",
  "canal": "gta",
  "conta": "@hpgta6",
  "tipo": "reel",
  "status": "pronto",
  "versao": 1,
  "titulo_capa": "ROCKSTAR SOLTA NOVIDADE NA QUINTA?",
  "subtitulo_capa": "o que dá pra esperar",
  "gancho_tela": "A Rockstar marcou quinta. E agora?",
  "credito": {
    "rotulo": "Vídeo",
    "nome": "Criador Exemplo",
    "por_rede": {
      "instagram": "@criadorexemplo",
      "facebook": "Criador Exemplo",
      "tiktok": "@criadorexemplo",
      "youtube": "@CriadorExemplo",
      "threads": "@criadorexemplo"
    }
  },
  "valores_aproximados": false,
  "texto_valores": null,
  "redes": {
    "instagram": {
      "texto_final": "A Rockstar marcou quinta-feira pra soltar novidade do GTA 6 👀\n\nEla não disse o que é. Da última vez que fez isso, veio trailer. E faltam 50 dias pro lançamento (19/11).\n\nComenta aí: o que você acha que vem na quinta?\n\nVídeo: @criadorexemplo\n\n#gta6 #gtavi #rockstargames #gta #vicecity",
      "partes": {
        "gancho": "A Rockstar marcou quinta-feira pra soltar novidade do GTA 6 👀",
        "corpo": "Ela não disse o que é. Da última vez que fez isso, veio trailer. E faltam 50 dias pro lançamento (19/11).",
        "cta": "Comenta aí: o que você acha que vem na quinta?",
        "credito": "Vídeo: @criadorexemplo",
        "valores": null,
        "hashtags": ["#gta6", "#gtavi", "#rockstargames", "#gta", "#vicecity"]
      }
    },
    "facebook": {
      "texto_final": "A Rockstar marcou quinta-feira pra soltar novidade do GTA 6 👀 Da última vez que fez isso, veio trailer. Faltam 50 dias pro lançamento!\n\nComenta aí: o que você acha que vem?\n\nVídeo: Criador Exemplo\n\n#gta6 #rockstargames",
      "partes": {
        "gancho": "A Rockstar marcou quinta-feira pra soltar novidade do GTA 6 👀",
        "corpo": "Da última vez que fez isso, veio trailer. Faltam 50 dias pro lançamento!",
        "cta": "Comenta aí: o que você acha que vem?",
        "credito": "Vídeo: Criador Exemplo",
        "valores": null,
        "hashtags": ["#gta6", "#rockstargames"]
      }
    },
    "tiktok": {
      "texto_final": "Rockstar marcou QUINTA pra novidade do GTA 6 👀 o que vem aí? Comenta aí! Vídeo: @criadorexemplo #gta6 #gtavi #rockstargames #gta",
      "partes": {
        "gancho": "Rockstar marcou QUINTA pra novidade do GTA 6 👀",
        "corpo": "o que vem aí?",
        "cta": "Comenta aí!",
        "credito": "Vídeo: @criadorexemplo",
        "valores": null,
        "hashtags": ["#gta6", "#gtavi", "#rockstargames", "#gta"]
      }
    },
    "youtube": {
      "titulo": "Rockstar marcou quinta: o que vem aí no GTA 6? #gta6",
      "descricao": "A Rockstar avisou que quinta-feira (01/10) tem novidade do GTA 6. Ela não disse o que é — da última vez que fez isso, veio trailer. O lançamento é em 19/11/2026: faltam 50 dias.\n\nComenta aí: o que você acha que vem?\n\nVídeo: @CriadorExemplo\n\n#gta6 #gtavi #rockstargames",
      "tags": ["gta 6", "gta vi", "rockstar games", "gta 6 lançamento", "gta 6 trailer", "novidade gta 6"],
      "partes": {
        "gancho": "A Rockstar avisou que quinta-feira (01/10) tem novidade do GTA 6.",
        "cta": "Comenta aí: o que você acha que vem?",
        "credito": "Vídeo: @CriadorExemplo",
        "valores": null,
        "hashtags": ["#gta6", "#gtavi", "#rockstargames"]
      }
    },
    "threads": {
      "texto_final": "A Rockstar marcou quinta pra soltar novidade do GTA 6. Não disse o que é. Da última vez, veio trailer.\n\nO que você acha que vem? Comenta aí 👇\n\nVídeo: @criadorexemplo",
      "topico": "GTA 6",
      "partes": {
        "gancho": "A Rockstar marcou quinta pra soltar novidade do GTA 6.",
        "corpo": "Não disse o que é. Da última vez, veio trailer.",
        "cta": "O que você acha que vem? Comenta aí 👇",
        "credito": "Vídeo: @criadorexemplo",
        "valores": null,
        "hashtags": []
      }
    },
    "pinterest": null
  },
  "enquete": null,
  "aviso": {"titulo_curto": "Rockstar solta novidade do GTA 6 na quinta?"},
  "conferencias": {
    "limites_ok": true,
    "hashtags_ok": true,
    "proibidas_ok": true,
    "credito_ok": true,
    "valores_ok": "nao_se_aplica",
    "cta_ok": true,
    "fatos_conferidos_na_transcricao": true
  },
  "feito_por": "redator-claude",
  "modo": "valendo",
  "feito_em": "2026-09-30T15:48:02-03:00",
  "duracao_s": 305,
  "observacoes": ""
}
```

**Campos, um por um:**

| Campo | Obrigatório? | Regras |
|---|---|---|
| `esquema` | sim | sempre `"hp.post/1"` |
| `item` | sim | igual ao nome da pasta |
| `canal`, `conta`, `tipo` | sim | copiados do `pedido.json` |
| `status` | sim | `"rascunho"` (escrevendo), `"pronto"` (pode ir para Designer e revisão), `"travado"` (falta informação — explique em `observacoes`) |
| `versao` | sim | começa em 1; sobe 1 a cada volta do Revisor |
| `titulo_capa` | reel, story, pin | até 36 caracteres, até 6 palavras, cabendo em até 3 linhas de 18 caracteres (o Designer quebra assim) |
| `subtitulo_capa` | opcional | até 28 caracteres |
| `gancho_tela` | reel | frase dos 2 primeiros segundos para o Editor/Narrador usar na tela, até 45 caracteres |
| `credito.rotulo` | sim quando há material de terceiro | `"Vídeo"`, `"Foto"` ou `"Imagem"` |
| `credito.por_rede` | sim | o @ **daquela rede**; se o criador não tem conta ali, o nome dele + a rede de origem: `"Criador Exemplo (YouTube)"` |
| `valores_aproximados` | sim | `true` se qualquer texto ou arte cita valor em dinheiro |
| `texto_valores` | se `true` | o texto exato do aviso (ver 2.8) |
| `redes.<rede>.texto_final` | uma por rede do pedido | o texto exato que vai ao ar |
| `redes.<rede>.partes` | sim | gancho, corpo, cta, credito, valores, hashtags — juntando tudo tem que dar o `texto_final` |
| `redes.youtube.titulo` / `descricao` / `tags` | se `youtube` nas redes | limites da tabela 2.5 |
| `redes.threads.topico` | se `threads` nas redes | 1 tópico só (o Threads aceita uma tag por post) |
| `redes.pinterest` | só Receitas, Carros, Destinos | `titulo`, `descricao`, `texto_alternativo`, `link` |
| `enquete` | só `story_enquete` | `pergunta` (≤ ~25), `opcoes` (2), `pergunta_longa` (para a arte) |
| `aviso.titulo_curto` | sim | até 50 caracteres, entra no aviso "no ar" |
| `conferencias` | sim | resultado das conferências dos passos 45–52 |
| `feito_por` | sim | `redator-claude`, `redator-app`, `redator-antonio` |
| `modo` | sim | `"valendo"` ou `"sombra"` |

### 2.5 Limites de caracteres de cada rede (e o limite da HP)

O **limite da rede** é o máximo que ela aceita (passou disso, o post falha ou corta). O **limite HP** é o que a gente usa de verdade — menor, porque texto curto é lido e texto longo é pulado.

| Rede | Campo | Limite da rede | Limite HP | O que aparece antes do "…mais" | Hashtags |
|---|---|---|---|---|---|
| **Instagram** | legenda (reel, carrossel, foto) | 2.200 caracteres | reel: 150–600 · carrossel: 300–1.200 | ~125 caracteres (a 1ª linha é o gancho) | máximo **5** (limite atual da rede, que caiu de 30 para 5 no fim de 2025); HP usa **3 a 5**, no fim |
| **Facebook** | texto do post/reel | 63.206 caracteres | 80–500 | ~80–125 caracteres no reel | **0 a 3** |
| **TikTok** | legenda | 4.000 caracteres | 80–300 | ~70–100 caracteres | **3 a 5**, no fim |
| **YouTube Shorts** | título | 100 caracteres | **até 60** (ideal 40–55) | o título quase todo no Shorts | pode ter 1 no título (ex.: `#gta6`) |
| **YouTube Shorts** | descrição | 5.000 caracteres | 200–700 | 1ª linha | **3** na descrição (mais de 60 = o YouTube ignora todas) |
| **YouTube** | tags (campo escondido) | 500 caracteres somando todas | 5–10 tags, até 300 caracteres | não aparece | — |
| **Threads** | texto | 500 caracteres por post | 120–300 | tudo (não tem "mais" até 500) | **1 tópico** por post (regra da rede), sem `#` no texto |
| **Pinterest** | título do pin | 100 caracteres | **até 60** (os ~40 primeiros aparecem no feed) | — | não usar (o Pinterest funciona por palavra-chave) |
| **Pinterest** | descrição | 500 caracteres | 150–400 | ~50–60 caracteres | 0 (use palavras de busca no texto) |
| **Pinterest** | texto alternativo | 500 caracteres | 80–200 | não aparece (é para leitor de tela e busca) | 0 |
| **Story (enquete)** | pergunta da figurinha | ~25 caracteres (o que cabe) | **até 25** | — | — |
| **Story (enquete)** | cada opção | curta (o que cabe na figurinha) | **até 20** (confirmar na tela do Instagram) | — | — |
| **Aviso "no ar"** | `titulo_curto` | — | **até 50** | — | — |

**Folga de emoji:** algumas redes contam um emoji como 2 caracteres. Por isso a HP nunca encosta no limite da rede: o limite HP está sempre bem abaixo.

### 2.6 Tom de voz: informal BR, do jeito da HP

**O tom da casa (vale para os 6):**
- Português do Brasil, **informal e claro**, como quem conta a novidade para um amigo: "tá", "pra", "a gente", "olha isso" podem; palavrão não.
- **Frases curtas** (até ~15 palavras). Uma ideia por frase.
- **Você**, nunca "vocês todos", nunca "prezados".
- **Verbo no presente e na ativa:** "A Rockstar marcou quinta" (e não "Foi marcada pela Rockstar…").
- **Número em algarismo:** "50 dias", "R$ 18", "3 ingredientes", "2x0".
- **Emoji:** 1 a 3 por legenda, com função (👀 curiosidade, ⚽ gol, 🎬 estreia, 🍰 doce, 🚗 carro, ✈️ viagem, 👇 comenta). Nunca uma fileira de emojis.
- **Maiúsculas:** só no título da capa (quando o molde do canal usa) e em **uma** palavra de ênfase na legenda ("QUINTA"). Legenda inteira em maiúscula é proibida (parece grito e cansa).
- **Sem jargão sem explicar:** "FIPE" pode, com "tabela FIPE" na primeira vez; "DLC", "remake", "spin-off", "G4", "Z4" podem no canal certo (o público conhece).

**O tom de cada canal:**

| Canal | Voz | Pode | Evitar | Emojis da casa |
|---|---|---|---|---|
| **GTA 6 \| HP** (@hpgta6) | fã empolgado, mas que só fala o que é oficial | "rapaziada", "olha isso", "Vice City", "faltam X dias" | "VAZOU", "insider disse", "confirmado" sem fonte oficial | 👀 🔥 🎮 🌴 |
| **Futebol \| HP** (@hp.futebol) | torcedor apaixonado **por futebol**, não por um clube; respeita todas as torcidas | "golaço", "virada", "segue o líder", "comenta aí seu palpite" | provocação de torcida, ofensa a jogador/juiz, "FECHADO" sem anúncio oficial | ⚽ 🔥 🏆 📊 |
| **Filmes e Séries \| HP** (@hp.filmes) | amigo cinéfilo que dá dica boa | "vale a pena?", "chega dia X", "onde assistir" | spoiler sem aviso, "o melhor filme da história" | 🎬 🍿 📺 ⭐ |
| **Receitas \| HP** (@hp.receitas) | vó prática e moderna: acolhe e é exata nas medidas | "fica fofinho", "rende 12 fatias", "salva pra fazer" | medida vaga ("um pouco de farinha"), promessa de saúde ("emagrece") | 🍰 🍲 🧁 👩‍🍳 |
| **Carros \| HP** (@hp.carros) | amigo que entende de carro e fala em números | "a partir de R$", "consumo", "vale o preço?" | "o melhor carro do Brasil", preço sem "Valores aproximados…" | 🚗 ⛽ 🔧 📉 |
| **Destinos \| HP** (@hp.destinos) | viajante que ensina a gastar pouco | "roteiro de 3 dias", "melhor época", "salva pra sua próxima viagem" | "paraíso secreto que ninguém conhece" (mentira), preço sem aviso | ✈️ 🏖️ 🗺️ 🌄 |

### 2.7 Hashtags de cada canal

Regra: **3 a 5** no Instagram e no TikTok, **0 a 3** no Facebook, **3** na descrição do YouTube, **nenhuma** no texto do Threads (usa o campo `topico`) e **nenhuma** no Pinterest. Sempre no **fim** do texto. Metade fixa (identidade do canal) + metade do assunto do post.

| Canal | Fixas (use 2–3) | Do assunto (use 1–2, exemplos) | Tópico do Threads |
|---|---|---|---|
| GTA 6 | `#gta6` `#gtavi` `#rockstargames` | `#gta` `#vicecity` `#jasonelucia` `#gtaonline` | GTA 6 |
| Futebol | `#futebol` `#futebolbrasileiro` | `#brasileirao` `#libertadores` `#copadobrasil` `#flamengo` (nome do clube do post) | Futebol |
| Filmes e Séries | `#filmes` `#series` | `#netflix` `#primevideo` `#disneyplus` `#maxbrasil` `#cinema` `#estreia` (a plataforma do post) | Filmes e Séries |
| Receitas | `#receitas` `#receitafacil` | `#bolodecenoura` `#sobremesa` `#comidacaseira` `#airfryer` | Receitas |
| Carros | `#carros` `#carros2026` | `#carrobarato` `#suv` `#hatch` `#fipe` `#eletrico` | Carros |
| Destinos | `#viagem` `#destinos` | `#gramado` `#viajarbarato` `#praia` `#turismo` `#serragaucha` | Viagem |

Proibidas em qualquer canal: hashtag do Flow Games ou de pessoas ligadas a ele; `#leak`, `#gta6leak`, `#vazou`; hashtag sem relação com o post só porque está em alta (a rede pune e o público estranha); hashtag de outra marca como se fosse parceria.

### 2.8 Crédito e "Valores aproximados…" — os textos exatos

**Crédito (sempre em linha própria, antes das hashtags):**

| Situação | Texto |
|---|---|
| Vídeo de criador | `Vídeo: @criador` (o @ daquela rede) |
| Criador sem conta naquela rede | `Vídeo: Nome do Criador (YouTube)` |
| Vídeo oficial de clube/CBF/liga (Futebol) | `Vídeo: @clube` (ex.: `Vídeo: @flamengo`) |
| Material oficial da Rockstar | `Vídeo: Rockstar Games` ou `Imagem: Rockstar Games` |
| Filme/série | `Imagem: divulgação/<plataforma ou estúdio>` |
| Foto de divulgação de montadora | `Imagem: divulgação/<montadora>` |
| Foto/vídeo próprio da HP | não precisa de crédito (pode pôr `Foto: @hp.receitas` na arte) |
| Vários autores (carrossel) | `Fotos: @autor1, @autor2 e divulgação/Toyota` |

**Valores aproximados (sempre que o post citar dinheiro):**

- Texto padrão HP: **`Valores aproximados, pesquisados em <mês/ano>. Podem mudar.`** — ex.: `Valores aproximados, pesquisados em set/2026. Podem mudar.`
- Se a fonte é específica, pode completar: `Valores aproximados (tabela FIPE de set/2026). Podem mudar.` · `Valores aproximados, pesquisados em set/2026 em mercados de SP. Podem mudar.`
- Vai na legenda de **todas** as redes onde o valor aparece, em linha própria, **antes** do crédito.
- Vale para: preço de produto, carro, jogo, passagem, diária, ingresso, custo de receita, salário, valor de contratação de jogador, bilheteria convertida em reais, preço de assinatura de streaming.

### 2.9 Exemplo de `post.json` de estático (carrossel de Receitas com Pinterest)

```json
{
  "esquema": "hp.post/1",
  "item": "P2_2026-10-02_1130_receitas_bolo-cenoura-carrossel",
  "canal": "receitas",
  "conta": "@hp.receitas",
  "tipo": "carrossel",
  "status": "pronto",
  "versao": 1,
  "titulo_capa": "Bolo de cenoura de liquidificador",
  "subtitulo_capa": null,
  "gancho_tela": null,
  "credito": {"rotulo": "Foto", "nome": "HP Receitas", "por_rede": {"instagram": "@hp.receitas", "facebook": "Receitas | HP", "threads": "@hp.receitas", "pinterest": "Receitas | HP"}},
  "valores_aproximados": true,
  "texto_valores": "Valores aproximados, pesquisados em set/2026 em mercados de SP. Podem mudar.",
  "redes": {
    "instagram": {
      "texto_final": "Bolo de cenoura de liquidificador com cobertura que endurece 🍰\n\nArrasta pro lado: ingredientes, preparo e quanto custa (uns R$ 18 o bolo todo, R$ 1,50 a fatia).\n\nSalva pra fazer no fim de semana e comenta aí: com ou sem cobertura?\n\nValores aproximados, pesquisados em set/2026 em mercados de SP. Podem mudar.\n\n#receitas #receitafacil #bolodecenoura #comidacaseira",
      "partes": {
        "gancho": "Bolo de cenoura de liquidificador com cobertura que endurece 🍰",
        "corpo": "Arrasta pro lado: ingredientes, preparo e quanto custa (uns R$ 18 o bolo todo, R$ 1,50 a fatia).",
        "cta": "Salva pra fazer no fim de semana e comenta aí: com ou sem cobertura?",
        "credito": null,
        "valores": "Valores aproximados, pesquisados em set/2026 em mercados de SP. Podem mudar.",
        "hashtags": ["#receitas", "#receitafacil", "#bolodecenoura", "#comidacaseira"]
      }
    },
    "facebook": {
      "texto_final": "Bolo de cenoura de liquidificador com cobertura que endurece 🍰 Rende 12 fatias e sai por uns R$ 18.\n\nComenta aí: com ou sem cobertura?\n\nValores aproximados, pesquisados em set/2026 em mercados de SP. Podem mudar.\n\n#receitas #bolodecenoura",
      "partes": {"gancho": "Bolo de cenoura de liquidificador com cobertura que endurece 🍰", "corpo": "Rende 12 fatias e sai por uns R$ 18.", "cta": "Comenta aí: com ou sem cobertura?", "credito": null, "valores": "Valores aproximados, pesquisados em set/2026 em mercados de SP. Podem mudar.", "hashtags": ["#receitas", "#bolodecenoura"]}
    },
    "threads": {
      "texto_final": "Bolo de cenoura de liquidificador: 3 cenouras, 3 ovos, 1 xícara de óleo, 2 de açúcar, 2 de farinha. 40 min a 180 °C. Sai por uns R$ 18 🍰\n\nCom ou sem cobertura? Comenta aí 👇\n\nValores aproximados, pesquisados em set/2026. Podem mudar.",
      "topico": "Receitas",
      "partes": {"gancho": "Bolo de cenoura de liquidificador: 3 cenouras, 3 ovos, 1 xícara de óleo, 2 de açúcar, 2 de farinha.", "corpo": "40 min a 180 °C. Sai por uns R$ 18 🍰", "cta": "Com ou sem cobertura? Comenta aí 👇", "credito": null, "valores": "Valores aproximados, pesquisados em set/2026. Podem mudar.", "hashtags": []}
    },
    "pinterest": {
      "titulo": "Bolo de cenoura de liquidificador fofinho com cobertura",
      "descricao": "Receita de bolo de cenoura de liquidificador fofinho, com cobertura de chocolate que endurece. Rende 12 fatias, 40 minutos de forno a 180 °C. Custo aproximado de R$ 18 o bolo todo. Valores aproximados, pesquisados em set/2026. Podem mudar.",
      "texto_alternativo": "Fatia de bolo de cenoura com cobertura de chocolate brilhante sobre um prato branco",
      "link": null
    }
  },
  "enquete": null,
  "aviso": {"titulo_curto": "Bolo de cenoura de liquidificador (carrossel)"},
  "conferencias": {"limites_ok": true, "hashtags_ok": true, "proibidas_ok": true, "credito_ok": true, "valores_ok": "ok", "cta_ok": true, "fatos_conferidos_na_transcricao": "nao_se_aplica"},
  "feito_por": "redator-claude",
  "modo": "valendo",
  "feito_em": "2026-09-30T13:58:10-03:00",
  "duracao_s": 420,
  "observacoes": "Revisei ortografia das lâminas 2 e 5 no pedido.json (xícara, manteiga)."
}
```

### 2.10 Exemplo de `enquete` (story das 16h do GTA)

Trecho do `post.json` de um item `story_enquete` (o resto do arquivo segue o modelo da seção 2.4):

```json
{
  "enquete": {
    "pergunta": "Vai comprar no dia 19/11?",
    "opcoes": ["Sim, no dia 🔥", "Vou esperar"],
    "pergunta_longa": "VAI COMPRAR O GTA 6 NO DIA DO LANÇAMENTO?",
    "destaque": "Enquetes"
  }
}
```

- `pergunta`: 25 caracteres (no limite). Vai digitada na figurinha pelo robô do emulador (`story_post.py`, **a criar — módulo F**).
- `pergunta_longa`: vai na arte (o Designer usa).
- `destaque`: em qual destaque o story fica guardado.

### 2.11 Linha que o Redator acrescenta no `historico.log`

```
2026-09-30T15:48:02-03:00 [redator] post.json v1 pronto (IG 284, FB 218, TT 128, YT título 52, Threads 165 caracteres; crédito ok) - redator-claude
```

---

## 3. Passo a passo numerado para leigo

São **60 passos** em 15 partes. Um reel usa quase todas; um carrossel pula a parte do YouTube e do TikTok (quando essas redes não estão no pedido); um story de enquete usa só A, B, K, M, N.

> **Todos os exemplos de notícia deste manual (placar, gol, estreia, preço) são fictícios**, só para mostrar o formato. Na vida real, cada fato vem do vídeo, da transcrição ou da fonte oficial do pedido.

| Parte | Passos | O quê |
|---|---|---|
| A — Preparar | 1–5 | PowerShell, atalhos, data, plano do canal |
| B — Achar o trabalho | 6–10 | fila, item, pedido, volta do Revisor |
| C — Entender o conteúdo | 11–16 | transcrição, vídeo, fatos, criador, valores, proibições |
| D — Título da capa, gancho e lâminas | 17–22 | ganchos, 3 opções, revisão das lâminas |
| E — Instagram | 23–29 | a legenda-mãe, bloco por bloco |
| F — Facebook | 30–31 | adaptar |
| G — TikTok | 32–34 | adaptar |
| H — YouTube Shorts | 35–38 | título, descrição, tags |
| I — Threads | 39–41 | texto de conversa e texto puro |
| J — Pinterest | 42–44 | título, descrição, texto alternativo |
| K — Story e enquete | 45–46 | texto curto e figurinha |
| L — Aviso "no ar" | 47 | o título curto e o modelo |
| M — Montar e conferir o `post.json` | 48–56 | gravar e checar com números |
| N — Entregar | 57–58 | status, histórico |
| O — Volta do Revisor | 59–60 | corrigir só o que foi pedido |

### Parte A — Preparar

#### Passo 1 — Abrir o PowerShell
- **Abra:** `Windows + X` → **Terminal**.
- **Deve aparecer:** a janela com o cursor piscando.

#### Passo 2 — Criar os atalhos da sessão
- **Rode:**
```powershell
$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
$E  = "H:\HypadoLocal\esteira"
$S  = "G:\Meu Drive\Hypado\scripts"
$env:PYTHONIOENCODING = "utf-8"
Set-Location "G:\Meu Drive\Hypado"
```
- **Confira:** o `PYTHONIOENCODING` evita erro quando o Python imprime emoji ou acento no PowerShell 5.1.
- **Deve aparecer:** `PS G:\Meu Drive\Hypado>`.

#### Passo 3 — Conferir o Python
- **Rode:** `& $py --version`
- **Deve aparecer:** `Python 3.12.x`. Se não: seção 6, erro R01.

#### Passo 4 — Conferir a data de hoje e a contagem do GTA 6
Todo texto do GTA 6 que fala de "faltam X dias" usa a conta do computador, nunca a memória.
- **Rode:**
```powershell
Get-Date -Format "dddd, dd/MM/yyyy HH:mm"
((Get-Date "2026-11-19") - (Get-Date).Date).Days
```
- **Deve aparecer:** por exemplo `quarta-feira, 30/09/2026 15:40` e `50`.
- **Regra da contagem:** 2 ou mais → "faltam X dias"; 1 → "falta 1 dia"; 0 → "é hoje!"; negativo → não usar contagem.

#### Passo 5 — Ler o plano do canal (uma vez por semana ou quando mudar)
- **Rode:**
```powershell
Get-ChildItem "G:\Meu Drive\Hypado\07 Canais" -Directory | Select-Object Name
Get-ChildItem "G:\Meu Drive\Hypado\07 Canais\Futebol" -File | Select-Object Name
```
- **Abra** o plano do canal que você vai escrever (ex.: `notepad "G:\Meu Drive\Hypado\07 Canais\Futebol\PLANO_CRESCIMENTO.md"`).
- **Confira:** metas, formatos que funcionam, palavras e assuntos que o canal quer puxar. O que estiver no plano do canal **manda** sobre os exemplos deste manual (o plano é mais recente e feito com os números).
- **Deve aparecer:** a lista de pastas dos canais e os arquivos do Futebol (incluindo `PLANO_CRESCIMENTO.md`).

### Parte B — Achar o trabalho

#### Passo 6 — Ver quais itens estão sem texto pronto
- **Rode:**
```powershell
Get-ChildItem "$E\04_edicao" -Directory | Sort-Object Name | ForEach-Object {
  $p = Join-Path $_.FullName "post.json"
  $st = if (Test-Path $p) { (Get-Content $p -Raw -Encoding UTF8 | ConvertFrom-Json).status } else { "FALTA" }
  "{0,-9} {1}" -f $st, $_.Name
}
```
- **Confira:** os que aparecem com `FALTA`, `rascunho` ou `travado` precisam de você. Comece pelo de cima (P0 antes de P1 antes de P2).
- **Deve aparecer:** por exemplo:
```
FALTA     P0_2026-09-30_2147_futebol_gol-flamengo-pedro
pronto    P1_2026-09-30_1830_gta_rockstar-quinta
FALTA     P1_2026-09-30_1900_filmes_estreias-outubro
FALTA     P2_2026-10-02_1130_receitas_bolo-cenoura-carrossel
```

#### Passo 7 — Escolher o item
- **Rode** (troque pelo nome escolhido):
```powershell
$item = "$E\04_edicao\P0_2026-09-30_2147_futebol_gol-flamengo-pedro"
Test-Path $item
Get-ChildItem $item | Select-Object Name, Length
```
- **Deve aparecer:** `True` e a lista de arquivos da pasta.

#### Passo 8 — Ver se é volta do Revisor
- **Rode:**
```powershell
$ref = Get-ChildItem $item -Filter "refazer*.json" | Sort-Object LastWriteTime | Select-Object -Last 1
$ref | Select-Object Name, LastWriteTime
if (Test-Path "$item\post.json") { (Get-Item "$item\post.json").LastWriteTime } else { "sem post.json" }
```
- **Confira:** um arquivo de volta (`refazer.json`, ou `refazer_1_feito.json`/`refazer_2_feito.json` quando o Legendador ou o Tradutor — manuais 04 e 05 — já renomearam) **mais novo** que o `post.json` = o item voltou e você ainda não corrigiu. Vá para a Parte O (passo 59). Não reescreva tudo.
- **Deve aparecer (trabalho novo):** nenhuma linha de arquivo de volta e `sem post.json`.

#### Passo 9 — Ler o pedido
- **Rode:**
```powershell
$pedido = Get-Content "$item\pedido.json" -Raw -Encoding UTF8 | ConvertFrom-Json
$pedido | Select-Object canal, conta, tipo, prioridade, postar_em, tema, observacoes | Format-List
$pedido.redes
$pedido.fonte | Format-List
```
- **Confira:** canal (tom e hashtags da seção 2.6/2.7), redes (quais textos escrever), fonte (quem é o criador), observações do Curador (ex.: "destacar a quinta-feira").
- **Deve aparecer:** os campos preenchidos. Sem `-Encoding UTF8`, acento sai torto (erro R03).

#### Passo 10 — Decidir o que escrever
- **Confira** na tabela 1.3 quais campos o `tipo` exige e, na lista `redes`, quais redes precisam de texto. Anote num papel:
  - Reel do Futebol, redes `instagram facebook tiktok youtube threads` → título da capa, gancho de tela, 5 textos, título+descrição+tags do YouTube, tópico do Threads, título curto do aviso.
  - Carrossel de Receitas, redes `instagram facebook threads pinterest` → revisar lâminas, 3 textos, título+descrição+texto alternativo do pin, título curto do aviso.

### Parte C — Entender o conteúdo

#### Passo 11 — Ler a transcrição inteira
- **Rode:**
```powershell
$tr = Get-Content "$item\transcricao.json" -Raw -Encoding UTF8 | ConvertFrom-Json
$tr.duracao_s
$tr.texto
```
- **Confira:** leia **tudo**, do começo ao fim. Sublinhe (num papel) nomes, números, datas e o que é fato x opinião.
- **Deve aparecer:** a duração (ex.: `38.4`) e o texto falado.
- **Se não existir** `transcricao.json` (vídeo sem fala, ex.: gol só com som de torcida): vá direto ao passo 12.

#### Passo 12 — Assistir o vídeo (quando existir)
- **Rode:** `Invoke-Item "$item\final.mp4"` (ou `"$item\bruto.mp4"` se o final ainda não saiu).
- **Confira:** o que **aparece** (não só o que é falado): placar na tela, nome do jogador, o prato, o carro, a paisagem. Tudo que você for escrever tem que estar aqui ou na transcrição.
- **Deve aparecer:** o vídeo tocando.

#### Passo 13 — Escrever a "ficha de 3 linhas" (rascunho, no papel ou no Bloco de Notas)
1. **O que aconteceu** (1 frase, com sujeito e verbo): "Pedro marcou de cabeça aos 32 do 2º tempo."
2. **O número principal:** "Flamengo 2x0 Palmeiras."
3. **Por que importa:** "Com a vitória, o Flamengo assume a liderança."
- Se você não consegue escrever a ficha só com o vídeo e a transcrição (e o pedido), **pare**: falta informação. Grave `status: "travado"` (passo 48, com a observação "falta fonte para: …").

#### Passo 14 — Conferir o criador em cada rede
- **Confira** o `pedido.fonte`: `criador` (o @ principal) e `plataforma` (onde o vídeo foi publicado).
- Para cada rede do pedido, o crédito precisa do @ **daquela rede**. Se o pedido só trouxe o @ do YouTube e você vai postar no TikTok: abra o perfil oficial do criador (só olhar a página pública no navegador; nunca entrar em conta, nunca digitar senha) e veja se ele tem TikTok com o mesmo nome e selo/ligação na bio.
  - Achou → use o @ de lá.
  - Não achou ou ficou em dúvida → `Vídeo: Nome do Criador (YouTube)`.
- **Futebol:** o crédito é do clube/CBF/liga que publicou o vídeo oficial: `Vídeo: @flamengo` (Instagram), `Vídeo: Flamengo` (Facebook), `Vídeo: @flamengo` (TikTok), `Vídeo: @Flamengo` (YouTube). **Nunca** crédito de emissora de TV — se o vídeo é de TV, ele não pode ser usado (regra 4.3): marque `travado` e avise.

#### Passo 15 — Achar valores em dinheiro
- **Rode:**
```powershell
$tr.texto | Select-String -Pattern 'R\$|reais|real|d[oó]lar|pre[cç]o|custa|FIPE|mil|milh' -AllMatches | ForEach-Object { $_.Matches.Value } | Sort-Object -Unique
$pedido.valores
```
- **Confira:** se aparecer qualquer valor que você vai citar, marque `valores_aproximados = true` e prepare o texto do aviso (seção 2.8). "Mil" e "milhão" aparecem também em outros contextos ("mil gols", "1 milhão de views"): confira se é dinheiro.
- **Deve aparecer:** a lista de palavras encontradas (ex.: `R$`, `reais`) ou nada.

#### Passo 16 — Conferir as proibições do assunto antes de escrever uma linha
Marque (tudo tem que ser "não"):
- [ ] O assunto é **vazamento** do GTA 6 (material não oficial, "print de dev", "data-mining", "insider mostrou")? → **não escreva**; `travado`, observação "assunto proibido: vazamento".
- [ ] Tem **Flow Games** no vídeo, na fonte, no criador ou no assunto? → **não escreva**; `travado`, "assunto proibido: Flow Games".
- [ ] No Futebol, o vídeo é de **transmissão de TV**? → `travado`, "vídeo de TV proibido".
- [ ] O texto só funcionaria **mentindo** (o vídeo não tem o que o título precisaria prometer)? → peça outro corte ou outro tema ao Curador (`travado`).
- [ ] É **rumor**? Pode, desde que escrito como rumor e com fonte (ver regra 4.6) — nunca rumor sobre conteúdo vazado.

### Parte D — Título da capa, gancho de tela e lâminas

#### Passo 17 — Escolher o tipo de gancho
Gancho é a frase que faz a pessoa parar de rolar. Escolha **uma** fórmula que seja **verdadeira** para o conteúdo:

| Fórmula | Quando usar | Exemplo |
|---|---|---|
| **Pergunta direta** | novidade que ainda não se sabe o que é | "ROCKSTAR SOLTA NOVIDADE NA QUINTA?" |
| **Número + promessa** | lista, carrossel, receita | "5 ESTREIAS DE OUTUBRO QUE VALEM" |
| **Fato quente** (P0) | aconteceu agora | "PEDRO DE NOVO! FLAMENGO 2x0" |
| **Contraste** | antes x depois, caro x barato | "GRAMADO GASTANDO POUCO" |
| **Curiosidade específica** | detalhe real que pouca gente viu | "O DETALHE DO TRAILER QUE PASSOU BATIDO" (só se o detalhe existe e é oficial) |
| **Opinião / debate** | assunto que divide | "QUEM FOI O MELHOR DA RODADA?" |
| **Utilidade** | receita, dica, roteiro | "BOLO FOFINHO EM 3 PASSOS" |
| **Contagem** | datas marcadas | "FALTAM 50 DIAS PRO GTA 6" |

#### Passo 18 — Escrever 3 opções de título da capa
- **Regras:** até **36 caracteres**, até **6 palavras** (e que caiba em 3 linhas de até 18 caracteres), a palavra mais forte no começo ou no fim, número em algarismo, sem ponto final (pergunta e exclamação podem).
- **Rode** (mede as 3 de uma vez; troque pelos seus textos):
```powershell
"PEDRO DE NOVO! FLAMENGO 2x0", "GOL DO PEDRO E O FLA NA FRENTE", "FLAMENGO 2x0 COM GOL DE PEDRO" | ForEach-Object { "{0,3} car. {1} pal.  {2}" -f $_.Length, ($_ -split '\s+').Count, $_ }
```
- **Deve aparecer:**
```
 27 car. 5 pal.  PEDRO DE NOVO! FLAMENGO 2x0
 30 car. 8 pal.  GOL DO PEDRO E O FLA NA FRENTE
 29 car. 6 pal.  FLAMENGO 2x0 COM GOL DE PEDRO
```
  A 2ª tem 8 palavras: eliminada.

Bancos de títulos por canal (modelos para adaptar — **o fato tem que ser verdadeiro no dia**):

| Canal | Títulos-modelo bons | Títulos proibidos (e por quê) |
|---|---|---|
| GTA 6 | "ROCKSTAR SOLTA NOVIDADE NA QUINTA?" · "FALTAM 50 DIAS PRO GTA 6" · "O QUE JÁ É OFICIAL DO GTA 6" · "JASON E LUCIA: O QUE SABEMOS" · "PREÇO DO GTA 6 NO BRASIL" (só com preço oficial) | "VAZOU O MAPA DO GTA 6" (vazamento) · "GTA 6 ADIADO?!" (se não foi) · "TRAILER 3 AMANHÃ!" (se não foi anunciado) |
| Futebol | "PEDRO DE NOVO! FLAMENGO 2x0" · "QUEM CAI? A TABELA DO Z4" · "VIRADA HISTÓRICA NO MINEIRÃO" · "SEU TIME AINDA SONHA?" | "FECHADO! CRAQUE NO TIMÃO" (sem anúncio oficial) · "JUIZ LADRÃO" (ofensa) |
| Filmes e Séries | "5 ESTREIAS DE OUTUBRO QUE VALEM" · "VALE A PENA VER?" · "CHEGA HOJE NA NETFLIX" · "SÉRIE PRA MARATONAR NO FERIADO" | "O FINAL QUE NINGUÉM ESPERAVA" com spoiler na capa · "O MELHOR FILME DA HISTÓRIA" |
| Receitas | "Bolo de cenoura de liquidificador" · "Jantar em 15 minutos" · "3 ingredientes e pronto" · "Pão de queijo de frigideira" | "Receita que emagrece 5 kg" (promessa de saúde) · "Chef famoso não quer que você saiba" |
| Carros | "OS 5 CARROS MAIS BARATOS DE 2026" · "SUV ATÉ R$ 150 MIL VALE?" · "QUANTO GASTA DE VERDADE" · "ELÉTRICO OU HÍBRIDO?" | "CARRO DE GRAÇA" · "O MELHOR CARRO DO BRASIL" (sem critério) |
| Destinos | "Gramado gastando pouco" · "Praia sem fila em outubro" · "Roteiro de 3 dias em Salvador" · "Quanto custa ir pra Bonito" | "Paraíso secreto que ninguém conhece" (se é conhecido) · "Viagem de graça" |

#### Passo 19 — Testar as 3 opções e escolher 1
Para cada opção, responda (todas têm que ser "sim"):
1. **É verdade?** Está no vídeo/transcrição/pedido? (Se é pergunta, a resposta está no vídeo ou o vídeo discute a pergunta?)
2. **Cabe?** ≤ 36 caracteres e ≤ 6 palavras.
3. **Tem a palavra que a pessoa procuraria?** (GTA 6, Flamengo, bolo de cenoura, Gramado, SUV…)
4. **Dá vontade de ver?** Imagine rolando o feed às 22h: você pararia?
5. **Fica bem com a quebra em 3 linhas de até 18 caracteres?** (o Designer vai quebrar assim — ver manual 07, passo 16)
- **Grave** a escolhida como `titulo_capa`. Se o canal usa maiúsculas no molde (GTA, Futebol, Filmes, Carros), escreva em maiúsculas; Receitas e Destinos em "Primeira maiúscula".

#### Passo 20 — (Só carrossel) Revisar o texto das lâminas no `pedido.json`
O texto das lâminas é escrito pelo Curador no `pedido.json`. O Redator revisa **antes** do Designer gerar as imagens. É a única vez em que o Redator mexe no arquivo de outro cargo — e só em ortografia, tom e tamanho, nunca no fato.
- **Rode:**
```powershell
$pedido.laminas | ForEach-Object { "--- {0} ({1}) ---`n{2}`n{3}`n[{4} palavras]" -f $_.n, $_.papel, $_.titulo, $_.texto, (($_.texto -split '\s+') | Where-Object { $_ }).Count }
```
- **Confira** em cada lâmina: ortografia (xícara, manteiga, açúcar, quilômetros), até 40 palavras, uma ideia, número em algarismo, unidade escrita igual em todas ("xícara" sempre, não "xíc." numa e "xícara" noutra), e que a lâmina com valor vai ter o rodapé (avise o Designer se o `pedido.valores.tem_valor` estiver `false` por engano).
- **Se precisar corrigir:** abra `notepad "$item\pedido.json"`, corrija **só** o texto, salve, e valide:
```powershell
Get-Content "$item\pedido.json" -Raw -Encoding UTF8 | ConvertFrom-Json | Out-Null; "pedido.json ok"
Add-Content "$item\historico.log" ("{0} [redator] revisei ortografia das lâminas no pedido.json" -f (Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz")) -Encoding UTF8
```
- **Deve aparecer:** `pedido.json ok`.

#### Passo 21 — Escrever o gancho de tela (só reel)
É a frase que aparece nos 2 primeiros segundos do vídeo (o Editor/Narrador usa). Até **45 caracteres**. Diferente do título da capa (a pessoa já viu a capa; o gancho de tela continua a conversa).

| Canal | `titulo_capa` | `gancho_tela` |
|---|---|---|
| GTA 6 | ROCKSTAR SOLTA NOVIDADE NA QUINTA? | A Rockstar marcou quinta. E agora? |
| Futebol | PEDRO DE NOVO! FLAMENGO 2x0 | Olha a cabeçada do Pedro ⚽ |
| Filmes e Séries | 5 ESTREIAS DE OUTUBRO QUE VALEM | A 3ª é a que eu mais espero |
| Receitas | Bolo de cenoura de liquidificador | Tudo no liquidificador, sério |
| Carros | OS 5 CARROS MAIS BARATOS DE 2026 | O 1º custa menos que você pensa |
| Destinos | Gramado gastando pouco | Dá pra ir a Gramado sem gastar muito |

- **Atenção:** "O 1º custa menos que você pensa" só pode se o vídeo mostra o preço e ele é de fato baixo para a categoria. Se não, troque.

#### Passo 22 — Medir tudo o que escreveu até aqui
- **Rode:**
```powershell
$titulo = "PEDRO DE NOVO! FLAMENGO 2x0"
$gancho = "Olha a cabeçada do Pedro ⚽"
"titulo_capa: $($titulo.Length) (máx 32) · gancho_tela: $($gancho.Length) (máx 45)"
```
- **Deve aparecer:** os dois números dentro do máximo. (O PowerShell conta emoji como 2; se deu 1 acima do máximo por causa do emoji, tudo bem — o contador do passo 50 é o oficial.)

### Parte E — Instagram (a legenda-mãe)

A legenda do Instagram é a **legenda-mãe**: as outras redes são adaptações dela. Escreva ela primeiro.

#### Passo 23 — Conhecer a estrutura de 6 blocos
```
[1] GANCHO — 1 linha, até 125 caracteres (é o que aparece antes do "mais")
(linha em branco)
[2] CORPO — 1 a 3 frases curtas: o fato, o número, por que importa
(linha em branco)
[3] CTA — pergunta + "comenta aí" (ou "salva…" no carrossel)
(linha em branco)
[4] VALORES — "Valores aproximados…" (só se citou dinheiro)
[5] CRÉDITO — "Vídeo: @criador" (só se tem material de terceiro)
(linha em branco)
[6] HASHTAGS — 3 a 5, no fim
```

Legendas completas de exemplo, uma por canal (exemplos fictícios):

**GTA 6 | HP** — ver `post.json` da seção 2.4.

**Futebol | HP** (P0, gol):
```
GOL DO FLAMENGO! ⚽ Pedro de cabeça aos 32 do 2º tempo.

Flamengo 2x0 Palmeiras no Maracanã. Com o resultado, o Fla assume a liderança do Brasileirão.

Foi golaço? Comenta aí 👇

Vídeo: @flamengo

#futebol #brasileirao #flamengo #futebolbrasileiro
```

**Filmes e Séries | HP** (reel de lista):
```
5 estreias de outubro que valem o seu fim de semana 🎬

Tem suspense, comédia e a volta de uma série que muita gente esperava. Todas com data e onde assistir no vídeo.

Qual você vai ver primeiro? Comenta aí 👇

Imagens: divulgação/Netflix, Prime Video e Max

#filmes #series #estreia #netflix
```

**Receitas | HP** (reel):
```
Bolo de cenoura de liquidificador com cobertura que endurece 🍰

3 cenouras, 3 ovos e 1 xícara de óleo no liquidificador. 40 minutos a 180 °C. Rende 12 fatias e sai por uns R$ 18.

Com ou sem cobertura? Comenta aí e salva pra fazer no fim de semana!

Valores aproximados, pesquisados em set/2026 em mercados de SP. Podem mudar.

#receitas #receitafacil #bolodecenoura #comidacaseira
```

**Carros | HP** (reel):
```
Os 5 carros mais baratos do Brasil em 2026 🚗

O mais em conta sai a partir de R$ 79 mil. No vídeo: preço, consumo e o que vem de série em cada um.

Qual desses você compraria? Comenta aí 👇

Valores aproximados (tabela de preços das montadoras, set/2026). Podem mudar.
Imagens: divulgação/montadoras

#carros #carros2026 #carrobarato
```

**Destinos | HP** (reel):
```
Dá pra ir a Gramado gastando pouco ✈️

Diária a partir de R$ 180 em pousada no centro, 3 passeios de graça e o melhor mês pra ir sem fila.

Você iria em que época? Comenta aí e salva pra sua próxima viagem!

Valores aproximados, pesquisados em set/2026. Podem mudar.
Vídeo: @criadorviagens

#viagem #destinos #gramado #viajarbarato
```

#### Passo 24 — Escrever o gancho (bloco 1)
- Até **125 caracteres**. Precisa funcionar **sozinho** (é o que aparece antes do "mais").
- Pode repetir a ideia do título da capa com mais informação ("Pedro de cabeça aos 32 do 2º tempo").
- 1 emoji no fim, no máximo.
- **Proibido começar com:** "Olá pessoal", "Hoje vou mostrar", "Neste vídeo", "Você sabia que…" (fraco e batido), o nome do canal.

#### Passo 25 — Escrever o corpo (bloco 2)
- 1 a 3 frases curtas: **o fato + o número + por que importa** (a ficha do passo 13).
- Tudo verificável no vídeo/transcrição/pedido.
- Rumor escrito como rumor: "segundo o [veículo]", "ainda não é oficial".
- Spoiler (Filmes): nunca no corpo. Se o post é sobre o final, a 1ª linha avisa: "⚠️ Tem spoiler do final da 2ª temporada".

#### Passo 26 — Escrever o CTA (bloco 3)
O CTA da HP é **uma pergunta verdadeira + "comenta aí"**. A pergunta tem que ser fácil de responder (uma palavra, um nome, um número).

| Canal | CTAs-modelo |
|---|---|
| GTA 6 | "Comenta aí: vai comprar no dia 19/11?" · "O que você acha que vem na quinta? Comenta aí 👇" · "Jason ou Lucia? Comenta aí" |
| Futebol | "Foi golaço? Comenta aí 👇" · "Quem cai? Comenta aí seu palpite" · "Seu time ainda sonha? Comenta aí" |
| Filmes e Séries | "Qual você vai ver primeiro? Comenta aí" · "Vale a pena ou não? Comenta aí" · "Salva pra não esquecer a data" |
| Receitas | "Com ou sem cobertura? Comenta aí" · "Salva pra fazer no fim de semana" · "Qual receita você quer amanhã? Comenta aí" |
| Carros | "Qual desses você compraria? Comenta aí" · "Vale o preço? Comenta aí" · "Manda pra quem tá procurando carro" |
| Destinos | "Você iria em que época? Comenta aí" · "Salva pra sua próxima viagem" · "Manda pra quem vai com você" |

**Proibido (a Meta chama de "isca de engajamento" e derruba o alcance):** "Comenta SIM se…", "Marca 3 amigos", "Curte se você…", "Compartilha pra ajudar o canal", "Digita 1 pra…".

#### Passo 27 — Escrever o aviso de valores (bloco 4), se houver dinheiro
- Texto da seção 2.8. Linha própria, **antes** do crédito.
- Confira que o mês/ano é o da pesquisa (`pedido.valores.referencia`).

#### Passo 28 — Escrever o crédito (bloco 5)
- `Vídeo: @criador` com o @ do **Instagram** (passo 14).
- Uma linha só. Nunca escondido no meio das hashtags.

#### Passo 29 — Escolher as hashtags (bloco 6)
- 3 a 5 (tabela 2.7): 2–3 fixas do canal + 1–2 do assunto.
- **Rode** (conta as hashtags do texto que você escreveu):
```powershell
$ig = @"
GOL DO FLAMENGO! ⚽ Pedro de cabeça aos 32 do 2º tempo.

Flamengo 2x0 Palmeiras no Maracanã. Com o resultado, o Fla assume a liderança do Brasileirão.

Foi golaço? Comenta aí 👇

Vídeo: @flamengo

#futebol #brasileirao #flamengo #futebolbrasileiro
"@
([regex]::Matches($ig, '#\w+')).Count
$ig.Length
```
- **Deve aparecer:** `4` hashtags e o total de caracteres (`246` neste exemplo — o PowerShell conta cada emoji como 2; o contador oficial do passo 50 dá `245`).
- **Atenção ao `@"` e `"@`:** o `"@` de fechar tem que estar **sozinho no começo da linha**, sem espaço antes (erro R07).

### Parte F — Facebook

#### Passo 30 — Adaptar a legenda-mãe para o Facebook
- **Mais curta:** gancho + 1 frase + CTA (80–500 caracteres).
- **Hashtags:** 0 a 3.
- **Crédito:** o nome da página/perfil do criador no Facebook, se existir (`Vídeo: Criador Exemplo`); senão, `Vídeo: @criador (Instagram)`.
- Exemplo (Futebol):
```
GOL DO FLAMENGO! ⚽ Pedro de cabeça aos 32 do 2º tempo: Flamengo 2x0 Palmeiras.

Foi golaço? Comenta aí 👇

Vídeo: Flamengo

#futebol #flamengo
```

#### Passo 31 — Conferir "isca de engajamento" no Facebook
O Facebook é o mais rígido com isso. Confira que o texto **não** tem: "comenta SIM", "marca", "compartilha se", "curte se", "digita". A pergunta verdadeira do CTA ("Foi golaço?") pode.

### Parte G — TikTok

#### Passo 32 — Escrever a legenda do TikTok
- **Curta e de busca:** 80–300 caracteres. O TikTok funciona como buscador: coloque as palavras que a pessoa digitaria ("gol do Pedro Flamengo", "bolo de cenoura fofinho", "carro mais barato 2026").
- Formato: gancho + pergunta/CTA + crédito + hashtags, tudo em 1–3 linhas.
- Exemplos:
  - GTA: `Rockstar marcou QUINTA pra novidade do GTA 6 👀 o que vem aí? Comenta aí! Vídeo: @criadorexemplo #gta6 #gtavi #rockstargames #gta`
  - Futebol: `Gol do Pedro de cabeça! Flamengo 2x0 Palmeiras ⚽ foi golaço? Vídeo: @flamengo #futebol #brasileirao #flamengo`
  - Receitas: `Bolo de cenoura de liquidificador fofinho com cobertura que endurece 🍰 com ou sem cobertura? Valores aproximados, set/2026. #receitas #bolodecenoura #receitafacil`

#### Passo 33 — Hashtags do TikTok
- 3 a 5, no fim, iguais ou parecidas com as do Instagram.
- Não use hashtag de desafio/tendência que não tem nada a ver com o vídeo.

#### Passo 34 — Crédito no TikTok
- `Vídeo: @criador` com o @ **do TikTok**. Se o criador não tem TikTok: `Vídeo: Nome (YouTube)`.
- **Lembrete:** o TikTok **não** é agendado pela API; o Claude agenda pelo Chrome (e grava `tiktok_ok.json`). O texto que ele cola é exatamente o `redes.tiktok.texto_final` — por isso ele tem que estar perfeito aqui.

### Parte H — YouTube Shorts

#### Passo 35 — Título do YouTube
- **Até 60 caracteres** (limite da rede: 100). A **palavra de busca primeiro**: "Gol do Pedro: Flamengo 2x0 Palmeiras".
- Pode ter **1** hashtag no fim (ex.: `#gta6`), se couber.
- Sem MAIÚSCULAS no título inteiro (o YouTube pune e parece spam); só 1 palavra de ênfase, se precisar.
- Exemplos:

| Canal | Título do YouTube |
|---|---|
| GTA 6 | `Rockstar marcou quinta: o que vem aí no GTA 6? #gta6` (52) |
| Futebol | `Gol do Pedro de cabeça: Flamengo 2x0 Palmeiras` (46) |
| Filmes e Séries | `5 estreias de outubro que valem a pena` (38) |
| Receitas | `Bolo de cenoura de liquidificador fofinho (com cobertura)` (57) |
| Carros | `Os 5 carros mais baratos do Brasil em 2026` (42) |
| Destinos | `Gramado gastando pouco: quanto custa 3 dias` (43) |

#### Passo 36 — Descrição do YouTube
- **1ª linha:** resumo com as palavras de busca (é o que aparece).
- Depois: o fato completo (2–4 frases), o CTA, os valores (se houver), o crédito e **3 hashtags** no fim.
- 200–700 caracteres.

#### Passo 37 — Tags do YouTube (campo escondido)
- 5 a 10 tags, somando até 300 caracteres (limite da rede: 500).
- Minúsculas, com acento, do mais específico ao mais geral: `"gol pedro flamengo", "flamengo x palmeiras", "brasileirão 2026", "gols do brasileirão", "futebol"`.

#### Passo 38 — `#shorts` precisa?
- Não é obrigatório: o YouTube reconhece o Short pelo formato vertical e pela duração. Se sobrar espaço, pode ser a 3ª hashtag da descrição. Nunca no lugar de uma hashtag do assunto.

### Parte I — Threads

#### Passo 39 — Texto do Threads que acompanha vídeo/imagem
- O Threads é **conversa**: escreva como quem puxa assunto, não como anúncio.
- 120–300 caracteres (limite da rede: 500).
- **Sem hashtag no texto**: use o campo `topico` (1 por post — regra da rede).
- Termine com pergunta.
- Exemplo (Carros): `O carro mais barato do Brasil hoje sai por uns R$ 79 mil. Dez anos atrás, dava pra comprar dois com isso. Você compraria carro zero agora ou espera? 👇` + `Valores aproximados, pesquisados em set/2026. Podem mudar.` · tópico: `Carros`.

#### Passo 40 — Escolher o tópico do Threads
- Use o da tabela 2.7 (GTA 6, Futebol, Filmes e Séries, Receitas, Carros, Viagem). Um só.

#### Passo 41 — Texto puro do Threads (`tipo: "threads_texto"`)
Post só de texto, sem vídeo. Serve para puxar conversa entre um vídeo e outro.
- **Estrutura:** 1 afirmação ou opinião curta + 1 dado + 1 pergunta.
- Exemplos:
  - GTA: `Faltam 50 dias pro GTA 6. Qual a primeira coisa que você vai fazer em Vice City? Eu vou direto pra praia 🌴`
  - Futebol: `Rodada de quarta com 3 jogos que mexem no Z4. Quem você acha que dorme fora da zona hoje?`
  - Filmes: `Série boa é a que você termina e fica 2 dias pensando. Qual foi a última que fez isso com você?`
  - Receitas: `Bolo de cenoura: com cobertura de chocolate ou puro com café? Não tem resposta errada (tem sim).`
  - Carros: `Hatch ou SUV pequeno pelo mesmo preço? Me convence nos comentários.`
  - Destinos: `Viagem boa em outubro: serra ou praia? Conta aí onde você iria.`
- Grave em `redes.threads.texto_final` e deixe as outras redes de fora do `post.json` (só as redes do pedido entram).

### Parte J — Pinterest (só Receitas, Carros e Destinos)

#### Passo 42 — Título do pin
- Até **60 caracteres**, com as palavras exatas de busca: "Bolo de cenoura de liquidificador fofinho com cobertura" (55).
- Sem emoji, sem hashtag.

#### Passo 43 — Descrição do pin
- 150–400 caracteres, frases completas, com palavras de busca naturais ("receita de bolo de cenoura fácil", "roteiro barato em Gramado", "carro mais barato do Brasil").
- Inclua o aviso de valores se citar dinheiro.
- Sem hashtag.

#### Passo 44 — Texto alternativo e link
- **Texto alternativo:** descreva a imagem para quem não enxerga (80–200 caracteres): "Fatia de bolo de cenoura com cobertura de chocolate brilhante sobre um prato branco".
- **Link:** `null`, a não ser que o pedido traga um link oficial (site de turismo, página da montadora). **Nunca** link de afiliado (afiliados é assunto futuro — nada agora).

### Parte K — Story e enquete

#### Passo 45 — Texto de story (quando o pedido não trouxe)
- Até **25 palavras**, 1 ideia, pode ter 1 pergunta.
- Exemplos: GTA `A ROCKSTAR MEXEU NO SITE HOJE` · Futebol `FLA 2x0 PAL — FIM DE JOGO` · Filmes `CHEGOU HOJE: VALE A PENA?` · Receitas `3 INGREDIENTES, 10 MINUTOS` · Carros `R$ 79 MIL: O MAIS BARATO DO BRASIL` (+ aviso de valores) · Destinos `PRAIA SEM FILA EM OUTUBRO`.

#### Passo 46 — Enquete do story das 16h (GTA 6)
- **Pergunta:** até 25 caracteres, termina com `?`. **Rode** para medir: `"Vai comprar no dia 19/11?".Length` → `25`.
- **Opções:** 2, curtas (até 20 caracteres cada), que respondam a pergunta sem ambiguidade.
- **Pergunta longa** (para a arte): pode ser maior e em maiúsculas.
- Banco de enquetes (uma por dia, sem repetir na mesma semana):

| Pergunta (≤ 25) | Opções |
|---|---|
| Vai comprar no dia 19/11? | Sim, no dia 🔥 · Vou esperar |
| Jason ou Lucia? | Jason · Lucia |
| Físico ou digital? | Físico 💿 · Digital ☁️ |
| História ou online? | História · Online |
| Carro ou moto? | Carro 🚗 · Moto 🏍️ |
| Vai jogar no PS5 ou Xbox? | PS5 · Xbox |

  (Conferir cada pergunta com a medida: "Primeiro: história ou online?" tem 29 caracteres → **reprovada**; use "História ou online?" com 19. "Carro ou moto em Vice City?" tem 27 → **reprovada**; use "Carro ou moto?" com 14.)

### Parte L — Aviso "no ar"

#### Passo 47 — Escrever o título curto do aviso e conhecer o modelo
- **O que o Redator faz:** preenche `aviso.titulo_curto` (até **50 caracteres**), a versão curta e sem hashtag do título, que entra na mensagem.
- **Quem monta e manda o aviso:** o aviso é montado a partir do modelo oficial em `G:\Meu Drive\Hypado\06 Projeto\AVISO.md` com os links dos posts (hoje pelo plantão do Claude; depois pelo enviador local de WhatsApp — **a criar, módulo E**, que monta o texto sozinho a partir de `agendados.json`/links, sem IA). **O modelo do `AVISO.md` manda**; o exemplo abaixo só mostra o jeito.
- **Regras do aviso** (valem para quem monta):
  - Começa **exatamente** com `*Claude - *`.
  - Só vai para o grupo "HP | Comissão 🚀" e para os grupos da lista "HP | Grupos".
  - WhatsApp só serve para 3 mensagens: resumo do dia anterior, aviso "no ar" e resumo de sábado. Nada além disso.
  - Só depois que o post está **no ar** (etapa `07_postados`), com os links reais.
  - Nada de problema interno, erro ou bastidor no aviso.
- **Exemplo de formato** (fictício):
```
*Claude - * ✅ No ar — GTA 6 | HP (30/09, 18:30)
Rockstar solta novidade do GTA 6 na quinta?

Instagram: https://www.instagram.com/reel/XXXXXXXXXXX/
Facebook: https://www.facebook.com/reel/XXXXXXXXXXXXXXX
TikTok: https://www.tiktok.com/@hpgta6/video/XXXXXXXXXXXXXXXXXXX
YouTube: https://youtube.com/shorts/XXXXXXXXXXX
Threads: https://www.threads.net/@hpgta6/post/XXXXXXXXXXX
```
- **Exemplo de vários posts juntos** (fim de tarde):
```
*Claude - * ✅ No ar hoje (30/09)
• GTA 6 | HP — Rockstar solta novidade do GTA 6 na quinta? — https://www.instagram.com/reel/XXXXXXXXXXX/
• Filmes e Séries | HP — 5 estreias de outubro que valem — https://www.instagram.com/reel/XXXXXXXXXXX/
• Futebol | HP — Gol do Pedro: Flamengo 2x0 Palmeiras — https://www.instagram.com/reel/XXXXXXXXXXX/
```
- **Títulos curtos por canal (modelos):** `Rockstar solta novidade do GTA 6 na quinta?` (43) · `Gol do Pedro: Flamengo 2x0 Palmeiras` (36) · `5 estreias de outubro que valem` (31) · `Bolo de cenoura de liquidificador` (33) · `Os 5 carros mais baratos de 2026` (32) · `Gramado gastando pouco` (22).

### Parte M — Montar e conferir o `post.json`

#### Passo 48 — Montar o arquivo
O jeito mais seguro para quem não é programador: copiar o modelo e preencher no Bloco de Notas.
- **Rode:**
```powershell
notepad "$item\post.json"
```
- Se o Bloco de Notas perguntar "Deseja criar um novo arquivo?", clique **Sim**.
- **Cole** o modelo da seção 2.4 (reel) ou 2.9 (estático) e troque os textos pelos seus.
- **Cuidados ao escrever dentro do JSON:**
  - Quebra de linha dentro de um texto vira `\n` (barra invertida + n). Linha em branco = `\n\n`.
  - Aspas dentro de um texto viram `\"` (ex.: `"texto_final": "Ele disse \"quinta\" no vídeo"`).
  - Barra invertida dentro de texto vira `\\`.
  - Entre um campo e outro vai vírgula; depois do **último** campo de um bloco, **não** vai vírgula.
  - Rede que não está no pedido: `null` (ex.: `"pinterest": null`) ou fora do arquivo.
  - `status` começa como `"rascunho"`; só vira `"pronto"` no passo 57.
- **Salve:** `Ctrl + S`. Confira no rodapé do Bloco de Notas que está escrito **UTF-8**. Feche.
- **Deve aparecer:** o arquivo `post.json` na pasta do item.
- **Com o app (a criar — etapa 3):** o comando `montar` do trabalho `redator` junta as `partes` de cada rede no formato certo (linhas em branco no Instagram, tudo corrido no TikTok) e grava o `texto_final` sozinho; o Claude só escreve as partes.

#### Passo 49 — Validar se o JSON está certo
- **Rode:**
```powershell
$post = Get-Content "$item\post.json" -Raw -Encoding UTF8 | ConvertFrom-Json; "post.json ok"
```
- **Deve aparecer:** `post.json ok`.
- **Se aparecer** "Primitivo JSON inválido" ou "Caractere inválido": tem vírgula sobrando/faltando ou aspas sem `\` dentro do texto. Seção 6, erro R05.

#### Passo 50 — Contar os caracteres de cada rede (o contador oficial)
- **Rode:**
```powershell
& $py -c "import json,sys;p=json.load(open(sys.argv[1],encoding='utf-8-sig'));[print(k,{c:len(x) for c,x in v.items() if isinstance(x,str)}) for k,v in p['redes'].items() if v]" "$item\post.json"
```
- **Confira** cada número com o **limite HP** da tabela 2.5.
- **Deve aparecer** (exemplo do GTA da seção 2.4):
```
instagram {'texto_final': 284}
facebook {'texto_final': 218}
tiktok {'texto_final': 128}
youtube {'titulo': 52, 'descricao': 268}
threads {'texto_final': 165, 'topico': 5}
```
  Todos dentro: Instagram 150–600 ✔, Facebook 80–500 ✔, TikTok 80–300 ✔, título do YouTube ≤ 60 ✔, descrição 200–700 ✔, Threads 120–300 ✔.

#### Passo 51 — Contar as hashtags de cada rede
- **Rode:**
```powershell
& $py -c "import json,sys,re;p=json.load(open(sys.argv[1],encoding='utf-8-sig'));[print(k,len(re.findall(r'#\w+',v.get('texto_final') or v.get('descricao') or ''))) for k,v in p['redes'].items() if v]" "$item\post.json"
```
- **Deve aparecer:** Instagram 3–5, Facebook 0–3, TikTok 3–5, YouTube 3 (na descrição), Threads 0, Pinterest 0. Exemplo do GTA: `instagram 5`, `facebook 2`, `tiktok 4`, `youtube 3`, `threads 0`.

#### Passo 52 — Procurar palavras proibidas e palavras de alerta
- **Rode** (proibidas — tem que dar `nenhuma`):
```powershell
& $py -c "import json,sys,re;s=json.dumps(json.load(open(sys.argv[1],encoding='utf-8-sig')),ensure_ascii=False).lower();print(sorted(set(m.group(0) for m in re.finditer(r'flow ?games|vaz(ou|amento|ado)|leak|datamin|comenta sim|marca [0-9a-z]+ amig|compartilha se|curte se|digita [0-9]',s))) or 'nenhuma')" "$item\post.json"
```
- **Rode** (alerta — pode aparecer, mas cada uma exige conferência humana):
```powershell
& $py -c "import json,sys,re;s=json.dumps(json.load(open(sys.argv[1],encoding='utf-8-sig')),ensure_ascii=False).lower();print(sorted(set(m.group(0) for m in re.finditer(r'urgente|confirmad\w*|oficial\w*|adiad\w*|fechad\w*|exclusiv\w*|spoiler|rumor|segredo|ningu[eé]m',s))) or 'nenhuma')" "$item\post.json"
```
- **Confira** cada palavra de alerta que aparecer:

| Palavra de alerta | Só pode se… |
|---|---|
| "confirmado", "oficial" | a fonte oficial (Rockstar, clube, CBF, liga, estúdio, montadora) disse — e o pedido traz a fonte |
| "adiado" | foi adiado de verdade, anunciado oficialmente |
| "fechado" (Futebol) | o clube anunciou oficialmente a contratação |
| "exclusivo" | a HP tem mesmo algo que ninguém tem (quase nunca) |
| "spoiler" | é um aviso de spoiler ("⚠️ tem spoiler"), nunca promessa de spoiler na capa |
| "rumor" | está escrito como rumor, com a fonte ("segundo o …") |
| "ninguém", "segredo" | é verdade (ex.: "ninguém marcou tantos gols nesta edição" com o número) |
| "urgente" | P0 de verdade (aconteceu agora) — e mesmo assim prefira o fato ao grito |

- **Deve aparecer (proibidas):** `nenhuma`. Qualquer outra coisa: reescreva o trecho.

#### Passo 53 — Conferir o crédito em todas as redes
- **Rode:**
```powershell
& $py -c "import json,sys;p=json.load(open(sys.argv[1],encoding='utf-8-sig'));[print(k,'ok' if any(r in (v.get('texto_final') or v.get('descricao') or '') for r in ('Vídeo:','Vídeos:','Foto:','Fotos:','Imagem:','Imagens:')) else 'SEM CREDITO') for k,v in p['redes'].items() if v and k!='pinterest']" "$item\post.json"
```
- **Deve aparecer:** `ok` em todas as redes quando o post usa material de terceiro. `SEM CREDITO` só é aceitável quando **todo** o material é próprio da HP (ex.: o carrossel do bolo com fotos próprias).
- **Confira também** (olhando): o @ de cada rede é o daquela rede (passo 14).

#### Passo 54 — Conferir o aviso de valores
- **Rode:**
```powershell
& $py -c "import json,sys,re;p=json.load(open(sys.argv[1],encoding='utf-8-sig'));[print(k,'FALTA AVISO DE VALORES' if re.search(r'R\x24|reais|US\x24|d[oó]lar',t) and 'Valores aproximados' not in t else 'ok') for k,v in p['redes'].items() if v for t in [' '.join(x for x in v.values() if isinstance(x,str))]]" "$item\post.json"
```
- **Deve aparecer:** `ok` em todas. `FALTA AVISO DE VALORES` = acrescente o texto da seção 2.8 naquela rede.
- **Confira também:** se `valores_aproximados` está `true` quando tem valor (e `false` quando não tem).

#### Passo 55 — Conferir que as partes estão dentro do texto final
- **Rode:**
```powershell
& $py -c "import json,sys;p=json.load(open(sys.argv[1],encoding='utf-8-sig'));[print(k,c,'FORA DO TEXTO') for k,v in p['redes'].items() if v and v.get('partes') for c,x in v['partes'].items() for y in (x if isinstance(x,list) else [x]) if y and y not in (v.get('texto_final') or v.get('descricao') or '')];print('conferido')" "$item\post.json"
```
- **Deve aparecer:** só `conferido`. Se aparecer `instagram cta FORA DO TEXTO`, você mudou o CTA no `texto_final` e esqueceu de mudar nas `partes` (ou o contrário). Deixe os dois iguais.

#### Passo 56 — Ler em voz alta (a conferência que nenhum programa faz)
Leia cada texto **em voz alta**, uma rede por vez, e responda:
- [ ] Soa como gente falando? (Se você não falaria isso para um amigo, reescreva.)
- [ ] Tudo o que está escrito aparece no vídeo, na transcrição ou na fonte do pedido?
- [ ] O título da capa e a primeira linha prometem **só** o que o vídeo entrega?
- [ ] Nenhum spoiler sem aviso (Filmes)? Nenhuma provocação a torcida (Futebol)? Nenhuma promessa de saúde (Receitas)? Nenhum "melhor do mundo" sem critério (Carros)? Nenhum "paraíso secreto" (Destinos)? Nada de vazamento (GTA)?
- [ ] Nome próprio escrito certo (Lucia, Jason, Rockstar Games, Pedro, Maracanã, Gramado, Toyota)?
- [ ] Número igual ao do vídeo (placar, preço, data, dias que faltam)?
- [ ] A pergunta do CTA é fácil de responder?

### Parte N — Entregar

#### Passo 57 — Marcar como pronto e registrar
- **Abra** `notepad "$item\post.json"`, troque `"status": "rascunho"` por `"status": "pronto"`, preencha o bloco `conferencias` com o resultado dos passos 50–55 (`true`/`"ok"`/`"nao_se_aplica"`), `feito_em` com a data e hora de agora (formato `2026-09-30T15:48:02-03:00`) e salve.
- **Rode:**
```powershell
$post = Get-Content "$item\post.json" -Raw -Encoding UTF8 | ConvertFrom-Json; $post.status
$ig = $post.redes.instagram.texto_final.Length
Add-Content "$item\historico.log" ("{0} [redator] post.json v{1} pronto (IG {2} car.; crédito e valores conferidos) - redator-claude" -f (Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz"), $post.versao, $ig) -Encoding UTF8
Get-Content "$item\historico.log" -Encoding UTF8 -Tail 2
```
- **Deve aparecer:** `pronto` e a sua linha no fim do histórico.

#### Passo 58 — Liberar para o Designer e para a revisão
- **Com o app (a criar — etapa 3):** nada a fazer. Assim que o `post.json` fica `pronto`, o app chama o Designer (capa) e, quando `final.mp4`, `post.json` e `design.json` estão prontos, move o item para `05_revisao`.
- **Sem o app (hoje):** avise quem faz o papel de Designer que o `titulo_capa` está pronto (no mesmo plantão do Claude, é só seguir para o manual 07). **Não mova** a pasta: quem move para `05_revisao` é o último a terminar (normalmente o Designer, manual 07, passo 55).

### Parte O — Volta do Revisor

#### Passo 59 — Ler o que o Revisor pediu e guardar a versão antiga
- **Rode:**
```powershell
$r = Get-Content $ref.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
$r.classe; $r.media; $r.criterio_menor; $r.cargo_destino; $r.motivo
$r.o_que_refazer | Where-Object { $_.cargo -eq "redator" } | Format-List
$r.voltas
Copy-Item "$item\post.json" "$item\post_v$((Get-Content "$item\post.json" -Raw -Encoding UTF8 | ConvertFrom-Json).versao).json"
```
- **Confira:** as ações com `cargo: "redator"` são as suas. Se não aparecer nenhuma (o item voltou por causa de outro cargo, ex.: `legendador`), não é com você — não mexa no `post.json`.
- **Deve aparecer:** a classe (ex.: `Médio`), a média, o critério de menor nota (ex.: `texto_post`), o motivo e o que refazer; e uma cópia `post_v1.json` na pasta.
- **Atenção:** se `voltas` é `2`, é a **última chance**: na próxima reprovação o item é descartado (manual 09).

#### Passo 60 — Corrigir só o que foi pedido e entregar de novo
- **Abra** `notepad "$item\post.json"`, corrija **somente** o que está em `o_que_refazer`, suba `versao` em 1 (ex.: de `1` para `2`), deixe `status` em `pronto`, atualize `feito_em` e escreva em `observacoes` o que mudou.
- **Rode** de novo os passos 49 a 55 (todas as conferências).
- **Rode:**
```powershell
Add-Content "$item\historico.log" ("{0} [redator] post.json v{1} refeito a pedido do revisor ({2})" -f (Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz"), (Get-Content "$item\post.json" -Raw -Encoding UTF8 | ConvertFrom-Json).versao, $r.criterio_menor) -Encoding UTF8
```
- **Deve aparecer:** nenhum erro. Com o app, o item volta sozinho para `05_revisao` (e o app renomeia `refazer.json` para `refazer_volta1.json`). **Não apague nem renomeie** o arquivo de volta (os manuais 04 e 05 usam o nome `refazer_1_feito.json`; os dois valem).

---

## 4. Regras que nunca se quebram

**4.1 Nunca escrever o que não está no conteúdo.** Todo fato, número, nome e data tem que estar no vídeo, na transcrição, no pedido ou na fonte oficial citada no pedido. Na dúvida, não escreva.

**4.2 Nada de vazamento de GTA 6.** Não usar, não citar, não descrever, não linkar, não "comentar o que dizem que vazou", nem com a palavra "suposto". Só informação oficial da Rockstar/Take-Two ou reportagem de veículo grande sobre anúncio oficial.

**4.3 Nada do Flow Games.** Nem nome, nem hashtag, nem crédito, nem menção a pessoas ligadas, nem resposta a comentário sobre isso.

**4.4 Nada de clickbait mentiroso.** O título e a primeira linha prometem **só** o que o conteúdo entrega. Pergunta no título é permitida quando o vídeo discute a pergunta; exagero que vira mentira ("ADIADO!", "VAZOU!", "FECHADO!", "GRÁTIS!") é proibido.

**4.5 Crédito sempre.** "Vídeo: @criador" (ou Foto/Imagem) em linha própria, em **todas** as redes, com o @ daquela rede. Futebol: o clube/CBF/liga que publicou o vídeo oficial.

**4.6 Rumor é rumor.** Se não é oficial, escreva "rumor", "segundo o [veículo]", "ainda não é oficial". Nunca transforme rumor em fato. Nunca rumor baseado em vazamento.

**4.7 Valor citado leva "Valores aproximados…".** Em todas as redes onde o valor aparece, com o mês/ano da pesquisa.

**4.8 Dentro do limite de cada rede e do limite HP** (tabela 2.5). Instagram com no máximo 5 hashtags; Threads com 1 tópico e sem hashtag no texto; título do YouTube até 60.

**4.9 Tom informal BR, sem palavrão, sem ofensa.** Nada de ofender torcida, jogador, juiz, ator, cidade, estado, país, religião, gênero, cor, origem. Futebol: a HP não torce por clube nas legendas.

**4.10 Sem isca de engajamento.** Nada de "comenta SIM", "marca 3 amigos", "compartilha se…", "curte se…", "digita 1". O CTA é sempre uma pergunta verdadeira + "comenta aí" (ou "salva…" / "manda pra alguém…").

**4.11 Spoiler só com aviso** (Filmes e Séries): "⚠️ Tem spoiler de…" na primeira linha; nunca na capa.

**4.12 Nada de promessa de saúde, dinheiro fácil ou resultado garantido** (Receitas: "emagrece", "cura"; Carros: "não gasta nada"; Destinos: "de graça").

**4.13 Futebol: nada de TV e nada de narração sintética.** O Redator não escreve texto para narrar vídeo de futebol (o áudio é sempre o original do vídeo oficial). Se o pedido pedir narração no Futebol, marque `travado`.

**4.14 Nada de link de afiliado nem "publi".** Afiliados é assunto futuro. Nenhum link de loja, cupom ou "compre aqui".

**4.15 O aviso "no ar" segue o modelo oficial** (`06 Projeto\AVISO.md`), começa com `*Claude - *`, só sai para "HP | Comissão 🚀" e a lista "HP | Grupos", e só depois que o post está no ar. O Redator não manda mensagem nenhuma.

**4.16 Segredos não são assunto do Redator.** Nunca abrir `H:\HypadoLocal\segredos\`, nunca colar token em texto, nunca entrar em conta de rede social para "ver como fica".

**4.17 Nunca apagar versão anterior.** Volta do Revisor = `post_v1.json` guardado.

**4.18 Não escrever no arquivo de outro cargo**, com uma exceção: ortografia/tom das lâminas no `pedido.json` (passo 20), registrado no histórico.

**4.19 Nada quebra o que funciona.** O formato do `post.json` que o Publicador já lê não muda sem 7 dias de modo sombra. Se algum dia o Publicador precisar de campo novo, ele é **acrescentado**, nunca renomeado.

**4.20 Contagem e datas pela máquina.** "Faltam X dias", "hoje", "amanhã", dia da semana: sempre conferidos pelo passo 4, nunca de memória.

---

## 5. Critérios de qualidade com nota

Cada `post.json` recebe nota de 0 a 10 em cada critério. A média é a nota do Redator no item, que o Revisor usa nos critérios **"Texto do post"** e **"Título da capa"** do manual 09. Meta: **média ≥ 9**.

| # | Critério | Como medir | Nota 10 | Nota 7 | Nota 5 | Nota 0 |
|---|---|---|---|---|---|---|
| R1 | **Verdade** (tudo confere com a fonte) | comparar cada fato/número com transcrição, vídeo e pedido (passo 56) | 100% confere | 1 detalhe impreciso sem importância (ex.: "no fim do jogo" quando foi aos 40 do 2º) | 1 número errado que não muda o sentido | fato inventado, número principal errado, rumor como fato (**eliminatório**) |
| R2 | **Gancho** (título da capa + 1ª linha) | as 5 perguntas do passo 19 | as 5 "sim"; fórmula clara; palavra de busca presente | 4 de 5 | 3 de 5 | promete o que não entrega (**eliminatório**) |
| R3 | **Limites de caracteres** | passo 50 x tabela 2.5 | todas as redes dentro do limite HP | 1 rede até 10% acima do limite HP (e dentro do limite da rede) | 1 rede mais de 10% acima do limite HP | alguma rede acima do limite da **rede** (post falha) |
| R4 | **Hashtags** | passo 51 x tabela 2.7 | quantidade certa em todas, fixas + assunto, no fim | 1 rede com 1 a mais ou a menos | hashtag sem relação com o post | hashtag proibida (leak, Flow Games) ou mais de 5 no Instagram |
| R5 | **Crédito** | passo 53 + conferência do @ | todas as redes, @ certo de cada rede | crédito em todas, mas com o @ do Instagram em outra rede | crédito faltando em 1 rede | sem crédito em material de terceiro (**eliminatório**) |
| R6 | **Valores aproximados** | passo 54 | aviso em todas as redes com valor, com mês/ano | aviso sem mês/ano | aviso faltando em 1 rede | valor sem aviso em nenhuma rede (**eliminatório**) |
| R7 | **CTA** | olhar o bloco 3 | pergunta verdadeira, fácil + "comenta aí"/"salva" | CTA genérico ("comenta aí o que achou") | CTA confuso ou 3 pedidos ao mesmo tempo | isca de engajamento ("comenta SIM", "marca 3 amigos") |
| R8 | **Tom** | leitura em voz alta (passo 56) + tabela 2.6 | soa como o canal, informal BR, frases curtas | 1 frase dura/formal | parece texto de robô ou de anúncio | ofensa, palavrão, provocação de torcida (**eliminatório**) |
| R9 | **Ortografia e gramática** | leitura letra por letra | 0 erro | 1 vírgula ou acento em palavra comum | 2–3 erros | erro em nome próprio, número ou no título da capa |
| R10 | **Busca (SEO)** | a palavra que a pessoa digitaria aparece no título do YouTube, no começo do TikTok e no pin | presente nos 3 | presente em 2 | presente em 1 | ausente (título genérico: "Olha isso!") |
| R11 | **Adaptação por rede** | comparar os textos | cada rede no seu formato (Threads conversa, TikTok curto, YouTube com busca) | 1 rede com texto copiado sem adaptar | 3 redes com o mesmo texto | texto do Instagram colado em todas (com 5 hashtags no Threads) |
| R12 | **Regras de conteúdo** | passo 16 + passo 52 | nenhuma violação | — | — | vazamento, Flow Games, TV no futebol, spoiler sem aviso (**eliminatório**) |
| R13 | **Arquivo** (`post.json`) | passos 49 e 55 | JSON válido, partes = texto final, `conferencias` preenchido | 1 campo opcional faltando | `partes` diferentes do `texto_final` | JSON inválido (o Publicador não lê) |
| R14 | **Enquete** (só `story_enquete`) | medir pergunta e opções | pergunta ≤ 25, 2 opções ≤ 20, sem ambiguidade | pergunta boa, opção longa | pergunta com 26–29 | pergunta que não cabe ou opções que não respondem |

**Exemplo de nota (reel do GTA da seção 2.4):** R1 10, R2 10, R3 10, R4 10, R5 10, R6 não se aplica, R7 10, R8 10, R9 10, R10 9 ("GTA 6" aparece no título do YouTube e no TikTok, mas não no começo da legenda do TikTok), R11 10, R12 10, R13 10, R14 não se aplica → soma 119 ÷ 12 critérios = **9,92 (Excelente)**.

**Exemplo de nota ruim (fictício):** título "TRAILER 3 NA QUINTA!" para o mesmo vídeo → R2 = 0 (promete o que não entrega) → eliminatório → o Revisor devolve ao Redator mesmo que a média dê 9.

---

## 6. Erros comuns e o que fazer

| Código | Sintoma | Causa | Solução |
|---|---|---|---|
| R01 | `& $py --version` não funciona | atalho não criado nesta janela | rode o passo 2; se persistir, `Get-ChildItem "$env:LOCALAPPDATA\Programs\Python"` e ajuste o caminho |
| R02 | Python dá `UnicodeEncodeError` ao imprimir emoji | falta `PYTHONIOENCODING` | `$env:PYTHONIOENCODING = "utf-8"` (passo 2) |
| R03 | acentos aparecem como `Ã§`, `Ã©` | leitura sem `-Encoding UTF8` no PowerShell 5.1 | sempre `Get-Content ... -Encoding UTF8` |
| R04 | o Bloco de Notas salvou como "ANSI" e os acentos quebraram | codificação errada ao salvar | **Arquivo → Salvar como** → Codificação: **UTF-8** → Salvar |
| R05 | "Primitivo JSON inválido" no passo 49 | vírgula sobrando/faltando, aspas sem `\` dentro do texto, quebra de linha "de verdade" dentro de um texto | procure a linha do erro; troque quebras reais por `\n` e aspas internas por `\"`; tire vírgula depois do último campo |
| R06 | o Publicador postou o texto com `\n` aparecendo literalmente | escreveu `\\n` (duas barras) no JSON | use uma barra só: `\n` |
| R07 | PowerShell fica esperando (`>>`) depois do `@"` | o `"@` de fechar não está sozinho no começo da linha | escreva `"@` na primeira coluna da linha, sem espaço antes; ou aperte `Ctrl + C` e comece de novo |
| R08 | passo 50 mostra Instagram com 2.400 | texto longo demais (ou legenda de carrossel virou artigo) | corte o corpo para 1–3 frases; o detalhe fica nas lâminas |
| R09 | Instagram com 7 hashtags | copiou lista antiga (de quando o limite era 30) | deixe 3–5 (limite atual da rede: 5) |
| R10 | Threads com hashtags no texto | copiou a legenda do Instagram | tire as hashtags; use o campo `topico` |
| R11 | título do YouTube cortado na tela | mais de 60 caracteres | reescreva com a palavra de busca primeiro e até 60 |
| R12 | Revisor devolveu por "crédito com @ errado" | usou o @ do Instagram no TikTok/YouTube | refaça o passo 14 para cada rede |
| R13 | Revisor devolveu por "valor sem aviso" | citou R$ em uma rede e esqueceu o aviso nela | passo 54 acusa; acrescente o texto da seção 2.8 |
| R14 | Revisor devolveu por "promete mais que o vídeo" | título/1ª linha exagerados | volte à ficha de 3 linhas (passo 13) e escreva só o que está nela |
| R15 | o pedido é sobre "vazamento" ou tem Flow Games | Curador errou | não escreva; `status: "travado"` com a observação; o Revisor/Curador descarta |
| R16 | o criador não tem conta na rede X | normal | `Vídeo: Nome do Criador (YouTube)` |
| R17 | não sei se é rumor ou oficial | fonte não diz | trate como rumor ("ainda não é oficial") ou não publique o fato; pergunte ao Curador pelo `travado` |
| R18 | a contagem de dias ficou errada | escrita de memória ou relógio do PC errado | passo 4; confira o relógio do Windows (fuso de Brasília) |
| R19 | enquete com pergunta de 29 caracteres | pergunta longa | encurte (tabela do passo 46) |
| R20 | TikTok: o Claude colou o texto e a rede cortou | passou de 4.000 (raro) ou tem caractere especial que a rede recusa | mantenha 80–300; evite caracteres raros (setas e símbolos incomuns) |
| R21 | Facebook reduziu o alcance | isca de engajamento ou link externo no texto | tire as frases proibidas (passo 31); não coloque link no texto do reel |
| R22 | `Copy-Item` do passo 59 sobrescreveu `post_v1.json` | já existia v1 (segunda volta) | o comando usa a `versao` atual: na 2ª volta cria `post_v2.json`; confira antes com `Get-ChildItem "$item\post_v*.json"` |
| R23 | "Legenda" no pedido do Revisor se refere às letrinhas do vídeo | confusão de nome | se o critério é `legenda` (do vídeo), é do Legendador (manual 04), não seu; o seu é `texto_post` |
| R24 | o `post.json` ficou com `"status": "pronto"` mas o Designer não começou | app desligado (hoje) ou vigia parado | sem o app: siga para o manual 07; com o app: confira a tela `http://127.0.0.1:8770` |
| R25 | nome do jogador/ator com grafia diferente em cada rede | digitação | copie e cole o nome de uma fonte oficial uma vez e reutilize |
| R26 | texto em inglês no vídeo (Filmes, GTA) | fonte estrangeira | o post é sempre em português BR; nome de filme/série: o título oficial no Brasil (se não houver, o original entre aspas) |
| R27 | o texto ficou igual ao de um post anterior | reaproveitamento | cada post tem texto próprio; repetir legenda faz a rede tratar como conteúdo repetido |

---

## 7. O que o app faz sozinho x o que o Claude decide

O Redator é o cargo em que o **julgamento** mais pesa (escolher o gancho, soar humano, não mentir). Por isso a meta não é 100% de app: é o app fazer **toda a parte de regra** (medir, contar, conferir, montar por rede, bloquear o proibido) e o Claude escrever **só o miolo** (título, gancho, corpo, pergunta) — em poucas linhas, gastando pouco token.

| Passo(s) | O que é | App sozinho | O Claude decide | % app (meta) |
|---|---|---|---|---|
| 1–5 | preparar, data, contagem, plano do canal | tudo (contagem de dias calculada) | nada | 100% |
| 6–10 | achar o item, ler o pedido, decidir campos | tudo | nada | 100% |
| 11–12 | transcrição e vídeo | entrega a transcrição pronta (etapa 02) | ler/assistir | 50% |
| 13 | ficha de 3 linhas | rascunho automático da transcrição (frases com número e nome próprio) | confirmar o que importa | 40% |
| 14 | crédito por rede | preenche a partir de uma tabela de criadores já usados (`criadores.json`, **a criar**) com o @ de cada rede | criador novo: conferir na página pública | 80% |
| 15 | achar valores | tudo (regex) | nada | 100% |
| 16 | proibições do assunto | bloqueia por lista (Flow Games, vazamento, emissoras de TV) | casos duvidosos | 85% |
| 17–19 | título da capa | mede, bloqueia palavras proibidas, sugere modelos por canal e fórmula | escolher e escrever o título | 30% |
| 20 | revisar lâminas | ortografia básica (corretor), contagem de palavras, unidades padronizadas | tom | 70% |
| 21–22 | gancho de tela e medidas | medir | escrever | 30% |
| 23–29 | legenda-mãe do Instagram | monta os blocos na ordem, põe CTA-modelo do canal, valores, crédito e hashtags fixas | gancho e corpo (2–4 frases) | 60% |
| 30–31 | Facebook | adapta da legenda-mãe por regra (corta corpo, 0–3 hashtags, crédito por nome), bloqueia isca | nada | 95% |
| 32–34 | TikTok | adapta por regra (1–3 linhas, hashtags, crédito do TikTok) | palavra de busca, quando não está no título | 85% |
| 35–38 | YouTube | título = título da capa em "Frase" + palavra de busca (se couber em 60); descrição e tags por regra | título quando a regra não coube | 75% |
| 39–41 | Threads | adapta por regra; texto puro usa banco de perguntas do canal | texto puro de opinião | 60% |
| 42–44 | Pinterest | título/descrição por regra com palavras de busca; texto alternativo da arte | nada | 85% |
| 45–46 | story e enquete | mede, banco de enquetes do GTA sem repetir na semana | pergunta nova | 80% |
| 47 | título curto do aviso | deriva do título do YouTube (≤ 50) | nada | 100% |
| 48–55 | montar e conferir | tudo (monta `texto_final`, conta, bloqueia, confere crédito/valores/partes) | nada | 100% |
| 56 | leitura em voz alta | — | tudo | 0% |
| 57–58 | entregar | tudo | nada | 100% |
| 59–60 | volta do Revisor | corrige sozinho o que é regra (limite, hashtag, crédito, aviso) | corrige gancho/tom/verdade | 60% |
| **Total ponderado** | | | | **≈ 70%** (o Claude escreve ~5 linhas por post em vez de ~30) |

**Como o app chega lá (modo sombra de 7 dias):** o app monta, em paralelo, um `post_sombra.json` a partir das mesmas partes que o Claude escreveu e o `qa_paridade` (**a criar — módulo D**) compara com o `post.json` do Claude: `texto_final` idêntico nas redes de regra (Facebook, TikTok, Pinterest, aviso), mesmas hashtags, mesmos créditos, mesmos avisos. Só depois de 7 dias com **100% de igualdade nos campos de regra** e **nota do Revisor ≥ 9** o app assume essas partes.

---

## 8. Ferramentas existentes que já fazem cada passo

| Passo | Ferramenta | Já existe? | Onde | Para quê |
|---|---|---|---|---|
| 3, 50–55 | Python 3.12 | sim | `%LOCALAPPDATA%\Programs\Python\Python312\python.exe` | contadores e conferências (linhas de comando deste manual) |
| 11 | transcrição (`transcricao.json`) | **(a criar — etapa 3, na etapa 02 da esteira)** | pasta do item | texto do vídeo com tempos |
| 12 | player de vídeo do Windows | sim | — | assistir `final.mp4` |
| 5, 47 | `07 Canais\<Canal>\…` e `06 Projeto\AVISO.md` | sim | `G:\Meu Drive\Hypado\` | plano do canal e modelo do aviso |
| 23, 32 | `scripts\posts_futebol.py` (`legenda_video`) | sim | `G:\Meu Drive\Hypado\scripts\` | caixa de legenda nos vídeos do Futebol (o Redator mantém o texto do post coerente com ela) |
| 34 | agendamento do TikTok pelo Chrome (Claude) + `tiktok_ok.json` | sim (processo) | — | usa o `redes.tiktok.texto_final` |
| — | `scripts\publicador_meta.py` | sim | `G:\Meu Drive\Hypado\scripts\` | publica no Instagram e Threads o `texto_final` (fila em `H:\HypadoLocal\fila_api\`) |
| — | Facebook e YouTube pela API | **em andamento no PC (etapa 4 — não mexer)** | — | vão usar `redes.facebook` e `redes.youtube` |
| 46 | `story_post.py` (robô da enquete no emulador) | **(a criar — módulo F)** | `scripts\` | digita `enquete.pergunta` e `enquete.opcoes` na figurinha |
| 47 | enviador local de WhatsApp (monta o aviso sem IA) | **(a criar — módulo E)** | `app\hp_studio\whatsapp_local\` | usa `aviso.titulo_curto` + links |
| 15, 16, 48–55 | trabalho `redator` da esteira (montar por rede, contar, bloquear, conferir) | **(a criar — etapa 3)** | `app\hp_studio\esteira\` | fazer sozinho tudo o que é regra |
| 14 | `criadores.json` (tabela de criadores com o @ de cada rede) | **(a criar — etapa 3)** | `H:\HypadoLocal\app\` | crédito automático para criador já usado |
| paridade | `qa_paridade` | **(a criar — módulo D)** | `app\hp_studio\qa_paridade\` | comparar `post_sombra.json` x `post.json` |
| — | `scripts\tickets.py` | sim | `G:\Meu Drive\Hypado\scripts\` | abrir ticket quando uma ferramenta falhar |
| — | `scripts\painel_local.py` e tela `http://127.0.0.1:8770` | sim | — | ver a fila e a prévia |

---

## 9. Testes de aceitação

O trabalho `redator` do app só assume as partes de regra quando **todos** os testes passam.

| # | Teste | Como rodar | Passa se |
|---|---|---|---|
| T01 | Limites | 30 `post.json` (5 por canal) montados pelo app | 30 de 30 com todas as redes dentro do limite HP da tabela 2.5 |
| T02 | Limite da rede nunca | forçar um corpo de 3.000 caracteres | o app recusa o Instagram (> 2.200), o Threads (> 500) e o título do YouTube (> 100) e marca `travado` |
| T03 | Hashtags | os 30 posts | Instagram 3–5 · Facebook 0–3 · TikTok 3–5 · YouTube 3 · Threads 0 · Pinterest 0, em 100% |
| T04 | Hashtag proibida | incluir `#gta6leak` e `#flowgames` num teste | o app bloqueia os 2 (0 posts com elas) |
| T05 | Crédito | 20 posts com material de terceiro | 20 de 20 com crédito em todas as redes; o @ certo de cada rede em 100% dos criadores de `criadores.json` |
| T06 | Crédito ausente | 1 pedido com fonte e sem criador | `status: "travado"`, observação "falta criador" |
| T07 | Valores | 10 posts com valor (2 por canal de Receitas, Carros, Destinos + 2 Futebol com valor de contratação + 2 GTA com preço oficial) | 10 de 10 com "Valores aproximados…" em todas as redes onde há valor |
| T08 | Sem aviso à toa | 10 posts sem valor | 0 com o aviso |
| T09 | Proibidas | 12 textos-armadilha ("vazou", "leak", "Flow Games", "comenta SIM", "marca 3 amigos", "compartilha se") | 12 de 12 bloqueados |
| T10 | Palavras de alerta | 6 textos com "confirmado", "adiado", "fechado", "exclusivo", "spoiler", "rumor" | 6 de 6 marcados para conferência humana (não passam direto) |
| T11 | Contagem do GTA | gerar texto em 30/09/2026, 18/11/2026, 19/11/2026, 20/11/2026 | "faltam 50 dias", "falta 1 dia", "é hoje!", sem contagem |
| T12 | Enquete | 10 enquetes | 10 de 10 com pergunta ≤ 25 e 2 opções ≤ 20; nenhuma repetida na mesma semana |
| T13 | Partes = texto | 30 posts | 30 de 30 com todas as partes dentro do `texto_final` |
| T14 | JSON | 30 posts | 30 de 30 lidos sem erro pelo `publicador_meta.py` em modo simular |
| T15 | Threads | 10 posts com Threads | 10 de 10 com 0 hashtag no texto e 1 `topico` |
| T16 | Pinterest só onde pode | pedidos com Pinterest para GTA, Futebol, Filmes | 0 textos de Pinterest gerados; observação registrada |
| T17 | Aviso "no ar" | 6 títulos curtos | 6 de 6 com até 50 caracteres; aviso montado começa com `*Claude - *` |
| T18 | Tempo | 30 posts | partes de regra montadas e conferidas em ≤ 10 s por post |
| T19 | Paridade (modo sombra) | 7 dias seguidos, todos os posts do dia | campos de regra 100% idênticos aos do Claude; nota do Revisor nos critérios "Texto do post" ≥ 9 em cada um dos 7 dias; 0 eliminatório |
| T20 | Volta do Revisor | `refazer.json` pedindo "tirar 2 hashtags do Instagram" | só `redes.instagram` muda; `versao` sobe 1; `post_v1.json` guardado |

---

## 10. Glossário

| Palavra | O que quer dizer |
|---|---|
| **Legenda (do post)** | o texto embaixo do vídeo/foto na rede social (também chamado de "caption" ou descrição) |
| **Legenda (do vídeo)** | as letrinhas queimadas na imagem — é do Legendador, não do Redator |
| **Título da capa** | o texto grande que o Designer põe na capa |
| **Gancho** | a frase que faz a pessoa parar de rolar |
| **Gancho de tela** | a frase dos 2 primeiros segundos do vídeo |
| **CTA** | "chamada para ação": a pergunta + "comenta aí", "salva", "manda pra alguém" |
| **Isca de engajamento** | pedido falso de interação ("comenta SIM", "marca 3 amigos") que as redes punem |
| **Clickbait mentiroso** | título que promete o que o conteúdo não tem |
| **Hashtag** | palavra com `#` que agrupa posts do mesmo assunto |
| **Tópico (Threads)** | a "hashtag" do Threads — só uma por post |
| **SEO / busca** | escrever com as palavras que as pessoas digitam para achar o assunto |
| **Tags (YouTube)** | palavras escondidas que ajudam o YouTube a entender o vídeo |
| **Texto alternativo** | descrição da imagem para quem não enxerga (e para a busca do Pinterest) |
| **Crédito** | "Vídeo: @criador" — quem fez o material original |
| **Valores aproximados…** | o aviso obrigatório quando o post cita dinheiro |
| **Rumor** | informação não oficial — só pode ser publicada como rumor, com fonte |
| **Vazamento** | material não oficial de GTA 6 — proibido sempre |
| **Spoiler** | revelar parte importante da história de um filme/série |
| **Enquete** | figurinha de votação do story |
| **Aviso "no ar"** | a mensagem de WhatsApp que avisa que os posts foram publicados, com os links |
| **`post.json`** | o arquivo do Redator com todos os textos, por rede |
| **`texto_final`** | o texto exato que vai ao ar naquela rede |
| **`partes`** | os blocos do texto (gancho, corpo, CTA, valores, crédito, hashtags) usados para conferir |
| **Esteira** | as pastas numeradas por onde cada post passa |
| **P0 / P1 / P2** | urgente/ao vivo · do dia · programado |
| **Modo sombra** | o app faz o trabalho em paralelo, sem valer, para comparar com o do Claude |
| **Paridade** | quando o trabalho do app fica igual ao do Claude, medido com números |
| **JSON** | formato de arquivo de texto com campos entre chaves `{ }`, que o app lê |
