# Manual 07 — Designer (HP Studio)

> **Versão:** 1.0 — 30/09/2026 · **Cargo nº 07 da esteira** · vale para os 6 canais da Hypado (HP)
> **Onde este arquivo mora no PC:** `G:\Meu Drive\Hypado\06 Projeto\app\manuais\07_designer.md`
> **Status:** manual novo, ainda não revisado pelo Antônio. Tudo o que está marcado **(a criar)** ainda **não existe** no PC — é o que o app vai ganhar na etapa 3 (esteira). O resto já existe e funciona hoje.
> **Quem usa:** o Claude (hoje), o app HP Studio (depois dos 7 dias de modo sombra) e qualquer pessoa leiga que precise fazer o trabalho à mão.

---

## Sumário

1. Objetivo do cargo
2. Entradas e saídas (arquivos, campos JSON, pastas, tamanhos, zonas seguras, identidade de cada canal)
3. Passo a passo numerado para leigo (58 passos)
4. Regras que nunca se quebram
5. Critérios de qualidade com nota
6. Erros comuns e o que fazer
7. O que o app faz sozinho x o que o Claude decide
8. Ferramentas existentes que já fazem cada passo
9. Testes de aceitação
10. Glossário

---

## Como ler este manual (se você nunca fez isso)

- Cada passo da seção 3 tem sempre 4 partes:
  - **Abra:** o que abrir (pasta, arquivo, programa).
  - **Rode:** o comando para copiar e colar no PowerShell (quando houver).
  - **Confira:** o que olhar com atenção.
  - **Deve aparecer:** o resultado certo. Se aparecer outra coisa, vá para a seção 6 (erros comuns).
- **PowerShell** é a janela azul/preta onde se digitam comandos no Windows. Para abrir: aperte `Windows + X` e clique em **Terminal** (ou **Windows PowerShell**). Para colar um comando: clique com o botão direito dentro da janela (ou `Ctrl + V`) e aperte `Enter`.
- Onde estiver escrito `$item`, é a pasta do item que você está trabalhando (o passo 8 ensina a preencher).
- **Px** (pixel) é o pontinho da imagem. Uma capa de reel tem 1080 px de largura e 1920 px de altura. Contamos a posição de cima para baixo (y) e da esquerda para a direita (x), começando do 0 no canto de cima à esquerda.
- **Nunca** apague nada da pasta do item. Se precisar refazer, a versão antiga ganha o final `_v1`, `_v2` (o passo 56 ensina).
- Trabalho pesado (renderizar lote de artes, vídeo) **nunca das 18h às 22h30** e sempre **1 por vez**. Uma capa avulsa é trabalho leve (leva segundos) e pode ser feita a qualquer hora; um lote inteiro de artes do dia é pesado.

---

## 1. Objetivo do cargo

### 1.1 Em uma frase

O Designer faz **toda peça visual parada** da Hypado — capa de reel, lâminas de carrossel, stories, pin do Pinterest, imagem do Threads e artes estáticas avulsas — **no tamanho certo de cada rede, com o texto dentro da zona segura, legível no celular, com a cara do canal, com crédito e com "Valores aproximados…" sempre que aparecer valor**.

### 1.2 Por que isso importa para a monetização

- **A capa decide o clique.** Quem chega no perfil vê a grade de capas. Capa com título cortado, ilegível ou genérica = perfil com cara de amador = menos seguidores. Seguidor é o primeiro requisito de monetização em todas as redes.
- **O carrossel é o motor de salvamento e compartilhamento.** Carrossel bem numerado, com uma ideia por lâmina e uma lâmina final pedindo "salva e comenta aí", é o formato que mais gera salvamentos em Receitas, Destinos e Carros. Salvamento empurra o alcance.
- **Texto embaixo do botão da rede = post perdido.** Se o título ficar atrás do nome do perfil, da legenda ou dos botões de curtir, o espectador não lê e passa. Por isso este manual é tão chato com zona segura.
- **Identidade repetida cria marca.** Quando a pessoa reconhece "isso é do HP" pela cor e pela letra antes de ler, a taxa de seguir sobe.

### 1.3 O que o Designer faz

| Peça | Tamanho | Canais | Onde sai |
|---|---|---|---|
| Capa de reel / vídeo curto | 1080 x 1920 | os 6 | Instagram, Facebook, TikTok, YouTube Shorts, Threads |
| Lâminas de carrossel | 1080 x 1350 | os 6 | Instagram, Facebook, Threads (TikTok em modo foto, quando pedido) |
| Story de conteúdo | 1080 x 1920 | os 6 | Instagram, Facebook |
| Story com enquete das 16h do GTA | 1080 x 1920 (com caixa vazia para a figurinha da enquete) | GTA 6 \| HP | Instagram (pelo emulador) |
| Story de contagem regressiva do GTA 6 | 1080 x 1920 | GTA 6 \| HP | Instagram, Facebook |
| Pin | 1000 x 1500 | só Receitas, Carros e Destinos | Pinterest |
| Imagem do Threads | 1080 x 1350 | os 6 | Threads |
| Arte estática de feed (foto única) | 1080 x 1350 | os 6 | Instagram, Facebook |
| Moldes (modelos) de cada canal | — | os 6 | usados pelo app para gerar tudo acima |

### 1.4 O que o Designer NÃO faz (para não pisar no pé de ninguém)

- **Não escolhe o tema** — isso é o Curador (manual 01).
- **Não escreve título nem legenda** — isso é o Redator (manual 08). O Designer recebe o título pronto em `post.json` → `titulo_capa`. Se o título não cabe (mais de 3 linhas no tamanho mínimo), o Designer **pede um título menor** ao Redator (passo 17); não corta palavra por conta própria.
- **Não edita o vídeo** — isso é o Editor (manual 03). Cartões e textos queimados dentro do vídeo são do Editor; o Designer só entrega os moldes visuais que ele usa.
- **Não publica** — isso é o Publicador (manual 10).
- **Não aprova o próprio trabalho** — isso é o Revisor (manual 09).

### 1.5 Como sabemos que o Designer está indo bem (metas com número)

| Meta | Número |
|---|---|
| Peças na medida exata da rede | 100% |
| Texto importante fora da zona segura | 0 peças |
| Contraste do texto principal com o fundo | ≥ 4,5 : 1 em 100% das peças (título grande: nunca abaixo de 3 : 1) |
| Nota do Revisor no critério "Capa" / "Arte" | média ≥ 9 na semana |
| Peças com valor em R$ sem "Valores aproximados…" | 0 |
| Peças com foto/vídeo de terceiro sem crédito | 0 |
| Tempo por capa | Claude ≤ 3 min · app ≤ 20 s |
| Tempo por carrossel de 7 lâminas | Claude ≤ 10 min · app ≤ 60 s |
| Voltas do Revisor por causa do Designer | ≤ 1 a cada 20 itens |

---

## 2. Entradas e saídas

### 2.1 A esteira em 1 minuto

Tudo o que a Hypado produz anda por uma **esteira de pastas** em `H:\HypadoLocal\esteira\`. Cada post é **uma pasta** que vai passando de uma etapa para a outra, como numa linha de montagem:

```
H:\HypadoLocal\esteira\
├── 01_pedidos            ← o Curador larga o pedido (pedido.json). O app baixa sozinho.
├── 02_baixados           ← o vídeo bruto já chegou; corte do trecho e transcrição.
├── 03_legenda_dublagem   ← legenda, tradução, dublagem, narração "Toque HP".
├── 04_edicao             ← Editor monta o final.mp4; DESIGNER faz capa e artes; Redator escreve o post.json.
├── 05_revisao            ← o Revisor olha 3 quadros + o texto e grava aprovado.json ou refazer.json.
├── 06_agendados          ← o app agenda pela API (TikTok: o Claude agenda pelo Chrome e grava tiktok_ok.json).
├── 07_postados           ← já está no ar; daqui sai o aviso "no ar" no WhatsApp.
└── 99_erros              ← algo deu errado ou o item foi descartado.
```

**Onde o Designer entra:**

- **Item de vídeo (reel):** na etapa `04_edicao`, depois que o Editor já gravou `final.mp4` (a capa usa um quadro do vídeo final) e o Redator já gravou `post.json` (a capa usa o título dele). Se o `post.json` ainda não chegou, o Designer espera (passo 10).
- **Item estático (carrossel, story, pin, imagem do Threads, arte de feed):** o pedido entra em `01_pedidos` com o campo `tipo` preenchido; o app vê que não é vídeo e **pula as etapas 02 e 03** (não há o que baixar, legendar nem dublar). O item cai direto em `04_edicao`, onde o Designer faz as artes e o Redator faz o texto.
- **Item de texto puro do Threads** (`tipo: "threads_texto"`): não passa pelo Designer.

### 2.2 O nome da pasta de cada item

Exemplo: `P1_2026-09-30_1830_gta_rockstar-quinta`

| Pedaço | Exemplo | O que quer dizer |
|---|---|---|
| Prioridade | `P1_` | `P0_` = urgente/ao vivo (gol, placar, lançamento, notícia bombástica) — fura a fila de tudo · `P1_` = do dia · `P2_` = programado para outro dia |
| Data de postagem | `2026-09-30` | ano-mês-dia em que vai ao ar |
| Hora de postagem | `1830` | 18h30 (horário de Brasília) |
| Canal | `gta` | `gta`, `futebol`, `filmes`, `receitas`, `carros` ou `destinos` |
| Apelido | `rockstar-quinta` | 2 a 4 palavras sem acento, separadas por hífen |

Como o nome começa com `P0_`, `P1_`, `P2_`, **ordenar a pasta por nome já coloca o mais urgente em cima**. Sempre trabalhe de cima para baixo.

Mais exemplos reais de nome (um por canal):

- `P0_2026-09-30_2147_futebol_gol-flamengo-pedro`
- `P1_2026-09-30_1830_gta_rockstar-quinta`
- `P1_2026-09-30_1900_filmes_estreias-outubro`
- `P2_2026-10-02_1130_receitas_bolo-cenoura-carrossel`
- `P2_2026-10-03_1200_carros_5-mais-baratos-2026`
- `P2_2026-10-04_1000_destinos_gramado-barato`

### 2.3 O que tem dentro da pasta do item

| Arquivo | Quem cria | Etapa | O Designer… |
|---|---|---|---|
| `pedido.json` | Curador | 01 | **lê** (canal, tipo, tema, redes, lâminas, valores) |
| `bruto.mp4` (ou `.mkv`, `.webm`) | app (download) | 01→02 | normalmente não usa |
| `transcricao.json` | app / Legendador | 02 | não usa |
| `legenda.srt` e `legenda.ass` | Legendador | 03 | não usa (mas confere que a capa não repete a legenda) |
| `dublagem.wav` | Tradutor/dublador ou Narrador | 03 | não usa |
| `final.mp4` | Editor | 04 | **lê** (tira o quadro da capa) |
| `post.json` | Redator | 04 | **lê** (`titulo_capa`, `subtitulo_capa`, `credito`, `valores_aproximados`) |
| `fontes\` (subpasta) | Curador / app | 01 | **lê** (fotos oficiais para carrossel, pin, story) |
| `capa.jpg` | **Designer** | 04 | **escreve** |
| `lamina_01.jpg` … `lamina_10.jpg` | **Designer** | 04 | **escreve** (só estáticos) |
| `story.jpg` | **Designer** | 04 | **escreve** |
| `pin.jpg` | **Designer** | 04 | **escreve** (só Receitas, Carros, Destinos) |
| `threads.jpg` | **Designer** | 04 | **escreve** (quando o Threads leva imagem própria) |
| `design.json` | **Designer** | 04 | **escreve** (o "recibo" do que foi feito — modelo no 2.9) |
| `conferencia_*.jpg` | **Designer** | 04 | **escreve** (cópias com a zona segura desenhada, só para conferir; o Publicador ignora) |
| `historico.log` | todos | todas | **acrescenta 1 linha** no fim |
| `aprovado.json` / `refazer.json` | Revisor | 05 | **lê** quando o item volta (passo 55) |

### 2.4 Exemplo completo de `pedido.json` de um reel (entrada)

```json
{
  "esquema": "hp.pedido/1",
  "item": "P1_2026-09-30_1830_gta_rockstar-quinta",
  "prioridade": "P1",
  "canal": "gta",
  "conta": "@hpgta6",
  "tipo": "reel",
  "tema": "Rockstar avisa que tem novidade de GTA 6 na quinta (01/10)",
  "fonte": {
    "url": "https://www.youtube.com/watch?v=XXXXXXXXXXX",
    "plataforma": "youtube",
    "criador": "@criadorexemplo",
    "nome_criador": "Criador Exemplo",
    "trecho": {"inicio": "00:01:12", "fim": "00:01:52"}
  },
  "redes": ["instagram", "facebook", "tiktok", "youtube", "threads"],
  "postar_em": "2026-09-30T18:30:00-03:00",
  "voz": "nenhuma",
  "idioma_origem": "pt-BR",
  "observacoes": "Destacar a quinta-feira no gancho. Nada de vazamento.",
  "criado_por": "curador-claude",
  "criado_em": "2026-09-30T09:12:00-03:00",
  "voltas_revisao": 0
}
```

Campos que o Designer usa: `canal` (escolhe o molde e as cores), `tipo` (decide que peças fazer), `redes` (decide se precisa de `pin.jpg`, `threads.jpg`), `prioridade` (P0 = capa em até 3 minutos, sem firula).

### 2.5 Exemplo completo de `pedido.json` de um carrossel (entrada de estático)

```json
{
  "esquema": "hp.pedido/1",
  "item": "P2_2026-10-02_1130_receitas_bolo-cenoura-carrossel",
  "prioridade": "P2",
  "canal": "receitas",
  "conta": "@hp.receitas",
  "tipo": "carrossel",
  "tema": "Bolo de cenoura de liquidificador em 7 lâminas",
  "redes": ["instagram", "facebook", "threads", "pinterest"],
  "postar_em": "2026-10-02T11:30:00-03:00",
  "laminas": [
    {"n": 1, "papel": "capa",     "titulo": "BOLO DE CENOURA DE LIQUIDIFICADOR", "texto": "Fofinho e com cobertura que endurece", "imagem": "fontes\\bolo_pronto.jpg", "credito": "Foto: @hp.receitas"},
    {"n": 2, "papel": "conteudo", "titulo": "Ingredientes da massa", "texto": "3 cenouras médias · 3 ovos · 1 xícara de óleo · 2 xícaras de açúcar · 2 xícaras de farinha · 1 colher (sopa) de fermento", "imagem": "fontes\\ingredientes.jpg", "credito": "Foto: @hp.receitas"},
    {"n": 3, "papel": "conteudo", "titulo": "Modo de preparo", "texto": "Bata cenoura, ovos e óleo no liquidificador. Misture açúcar e farinha à mão. Fermento por último.", "imagem": null, "credito": null},
    {"n": 4, "papel": "conteudo", "titulo": "Forno", "texto": "180 °C por 40 minutos. Teste do palito: saiu limpo, tá pronto.", "imagem": null, "credito": null},
    {"n": 5, "papel": "conteudo", "titulo": "Cobertura que endurece", "texto": "4 colheres de chocolate em pó · 1 xícara de açúcar · 1 colher de manteiga · 5 colheres de leite. Ferva 3 minutos.", "imagem": "fontes\\cobertura.jpg", "credito": "Foto: @hp.receitas"},
    {"n": 6, "papel": "conteudo", "titulo": "Quanto custa", "texto": "Custo total: cerca de R$ 18 (rende 12 fatias, uns R$ 1,50 cada)", "imagem": null, "credito": null},
    {"n": 7, "papel": "cta",      "titulo": "SALVA PRA FAZER NO FIM DE SEMANA", "texto": "E comenta aí: com ou sem cobertura?", "imagem": null, "credito": null}
  ],
  "valores": {"tem_valor": true, "referencia": "set/2026, média de mercados de SP"},
  "criado_por": "curador-claude",
  "criado_em": "2026-09-30T10:40:00-03:00",
  "voltas_revisao": 0
}
```

Repare: a lâmina 6 cita **R$ 18**, então ela **tem que** levar o rodapé "Valores aproximados…" (regra 4.6), e a legenda do post também (isso é com o Redator).

### 2.6 Campos do `post.json` que o Designer lê (o Redator escreve)

```json
{
  "titulo_capa": "ROCKSTAR SOLTA NOVIDADE NA QUINTA?",
  "subtitulo_capa": "o que dá pra esperar",
  "credito": {
    "rotulo": "Vídeo",
    "nome": "Criador Exemplo",
    "por_rede": {"instagram": "@criadorexemplo", "facebook": "Criador Exemplo", "tiktok": "@criadorexemplo", "youtube": "@CriadorExemplo", "threads": "@criadorexemplo"}
  },
  "valores_aproximados": false,
  "texto_valores": null,
  "status": "pronto"
}
```

(É só um pedaço do `post.json`; o arquivo completo está no manual 08, seção 2.4.)

- `titulo_capa`: o texto grande da capa. Já vem no tamanho certo (até 36 caracteres, até 6 palavras, cabendo em 3 linhas de até 18). Maiúsculas ou não é decisão do molde do canal (tabela 2.9).
- `subtitulo_capa`: opcional, linha menor embaixo do título (até 28 caracteres).
- `credito`: na arte vai sempre o rótulo + o @ **do Instagram** (`credito.rotulo` + `credito.por_rede.instagram`, ex.: "Vídeo: @criadorexemplo"), porque a mesma imagem vai para todas as redes. Vai na capa **só** quando a capa usa imagem de terceiro que não aparece com crédito no próprio vídeo (normalmente o crédito já está queimado no vídeo pelo Editor — então na capa é opcional). Em lâmina de carrossel com foto de terceiro, o crédito é **obrigatório** em cada lâmina.
- `valores_aproximados` e `texto_valores`: `true` quando o post cita valor; `texto_valores` traz a frase exata do aviso ("Valores aproximados, pesquisados em set/2026. Podem mudar."). Se a arte mostra valor, o rodapé é obrigatório e usa essa mesma frase.

### 2.7 Tamanhos, formatos e pesos de cada peça (saídas)

| Peça | Arquivo | Largura x altura | Proporção | Formato | Peso máximo | Cor |
|---|---|---|---|---|---|---|
| Capa de reel | `capa.jpg` | 1080 x 1920 | 9:16 | JPG qualidade 90–92 | 1 MB (meta 300–700 KB) | sRGB |
| Lâmina de carrossel | `lamina_01.jpg` … | 1080 x 1350 | 4:5 | JPG 90–92 | 8 MB (limite da API do Instagram; meta ≤ 1,5 MB) | sRGB |
| Story | `story.jpg` | 1080 x 1920 | 9:16 | JPG 90–92 | 8 MB (meta ≤ 1 MB) | sRGB |
| Story com enquete (GTA 16h) | `story.jpg` | 1080 x 1920 | 9:16 | JPG 90–92 | 8 MB | sRGB |
| Pin | `pin.jpg` | 1000 x 1500 | 2:3 | JPG 90–92 | 20 MB (limite do Pinterest; meta ≤ 1,5 MB) | sRGB |
| Imagem do Threads | `threads.jpg` | 1080 x 1350 | 4:5 | JPG 90–92 | 8 MB (meta ≤ 1,5 MB) | sRGB |
| Arte de feed avulsa | `lamina_01.jpg` | 1080 x 1350 | 4:5 | JPG 90–92 | 8 MB | sRGB |

Por que **JPG e não PNG**: a API de publicação do Instagram só aceita JPG para imagem. Mandar PNG faz o post falhar na hora do agendamento (o erro aparece no Publicador, lá na frente, e o item volta).

### 2.8 Zonas seguras de cada rede (onde o texto PODE ficar)

**Zona segura** é a parte da imagem que nenhuma rede cobre com botão, nome do perfil, legenda ou barra. Todo texto importante (título, número, preço, crédito, numeração da lâmina) tem que ficar **dentro** dela. Foto e fundo podem ir até a borda; texto não.

#### 2.8.1 Vídeo vertical e story — 1080 x 1920

| Faixa | Medida | O que cobre ali |
|---|---|---|
| Topo | y 0 a 250 | barra de progresso do story, nome do perfil, "Reels", botão de câmera, busca do TikTok |
| Base | y 1500 a 1920 (420 px) | legenda do post, nome do perfil, música, botão "Enviar mensagem", título do Shorts, figurinha de link |
| Direita | x 930 a 1080 (150 px) | coluna de botões (curtir, comentar, compartilhar, salvar, disco da música) no Reels, TikTok e Shorts |
| Esquerda | x 0 a 60 | margem de respiro (alguns celulares cortam) |
| **Zona segura de texto** | **x 60 a 930 · y 250 a 1500** | aqui pode tudo |

Para **story** (Instagram e Facebook) a base cobre um pouco menos: use **y 250 a 1580** (caixa de resposta e figurinha de link ficam abaixo de 1580). Na dúvida, use a mesma zona do reel.

#### 2.8.2 Capa de reel na grade do perfil — o corte 3:4

A grade do perfil do Instagram (e a do TikTok e do Facebook, que são parecidas) **não mostra a capa inteira**: ela mostra só o miolo em 3:4, que numa imagem 1080 x 1920 é o retângulo **y 240 a 1680** (1080 x 1440). Tudo que estiver acima de 240 ou abaixo de 1680 some na grade.

Então a capa tem duas regras ao mesmo tempo:

- O título tem que estar **dentro da zona segura** (x 60–930 no vídeo; na capa aceitamos x 90–990 porque a grade não tem botões — mas a capa também aparece no começo do vídeo em algumas telas, por isso preferimos centralizar o título entre x 90 e 990 e nunca encostar na direita).
- O título tem que estar **dentro do corte 3:4** (y 240–1680).
- **Faixa ideal do título na capa: y 420 a 1000** (terço de cima do miolo). Fica visível na grade, não briga com a legenda de baixo e não fica atrás do nome do perfil.

#### 2.8.3 Carrossel, arte de feed e imagem do Threads — 1080 x 1350

| Faixa | Medida | Por quê |
|---|---|---|
| Margem lateral | 80 px de cada lado (x 80 a 1000) | a grade 3:4 do perfil corta ~34 px de cada lado de uma imagem 4:5; 80 px dá folga |
| Margem de cima e de baixo | 80 px (y 80 a 1270) | respiro; o Threads e o Facebook arredondam os cantos |
| Numeração da lâmina ("2/7") | canto de cima à direita, dentro da margem: caixa em x 900–1000, y 80–130 | nunca colada na borda |
| Crédito da foto | canto de baixo à esquerda: y 1210–1270, a partir de x 80 | tamanho 28–32 px |
| @ do canal | canto de baixo à direita: y 1210–1270, terminando em x 1000 | tamanho 28–32 px |
| Rodapé "Valores aproximados…" | faixa y 1150–1200, centralizado | tamanho 28–30 px, sempre legível |

#### 2.8.4 Pin do Pinterest — 1000 x 1500

| Faixa | Medida | Por quê |
|---|---|---|
| Margens | 60 px de cada lado (x 60–940, y 60–1440) | o Pinterest arredonda os cantos |
| Canto de baixo à direita | evitar texto em x 800–1000, y 1340–1500 | o app do celular põe ali o botão de busca por imagem (lente) e o "…" |
| Canto de cima à direita | evitar texto em x 800–1000, y 0–160 | aparece o botão "Salvar" ao passar o mouse |
| Título | terço de cima: y 100 a 600 | é o que o olho lê primeiro no feed em colunas |

#### 2.8.5 Resumo em uma tabela (cole na parede)

| Peça | Tamanho | Zona segura de texto (x) | Zona segura de texto (y) | Extra |
|---|---|---|---|---|
| Reel/vídeo | 1080x1920 | 60–930 | 250–1500 | — |
| Capa de reel | 1080x1920 | 90–990 | 250–1500 | título entre y 420–1000; tudo dentro de y 240–1680 (grade 3:4) |
| Story | 1080x1920 | 60–930 (ou 60–1020 se não tiver botão à direita) | 250–1580 | caixa da enquete: x 140–940, y 1050–1450 |
| Carrossel / feed / Threads | 1080x1350 | 80–1000 | 80–1270 | numeração em cima à direita |
| Pin | 1000x1500 | 60–940 | 60–1440 | fugir dos cantos da direita |

### 2.9 Identidade visual de cada canal (os "moldes")

> **Importante:** as cores e fontes abaixo são a **referência deste manual**. Se o `scripts\estaticos.py` ou o `scripts\posts_canais.py` já tiverem cores/fontes diferentes gravadas no código para aquele canal, **o que está no código manda** (é o que já está no ar). Nesse caso, o Designer abre um ticket com `scripts\tickets.py` na área de design pedindo para alinhar este manual ao código — não troca a identidade por conta própria.
>
> Todos os contrastes da tabela foram medidos com a fórmula do passo 24 (padrão internacional WCAG).

| Canal (@) | Cor de fundo | Cor de destaque | Cor da caixa atrás do texto | Texto sobre a caixa | Contraste medido | Fonte do título (grátis, licença livre) | Fonte do texto | Título em maiúsculas? | Clima |
|---|---|---|---|---|---|---|---|---|---|
| **GTA 6 \| HP** (@hpgta6) | preto-azulado `#0B0B12` | rosa neon `#FF2E88` | roxo `#7B2CBF` | branco `#FFFFFF` | branco/roxo 7,11 · rosa/preto 5,60 | Anton | Inter SemiBold | sim | noite de Vice City, neon, pôr do sol |
| **Futebol \| HP** (@hp.futebol) | verde-escuro `#0B3D2E` | amarelo `#FFD400` | verde-escuro `#0B3D2E` | amarelo `#FFD400` ou branco | amarelo/verde 8,52 · branco/verde 12,2 | Bebas Neue | Inter SemiBold | sim | placar, estádio, energia |
| **Filmes e Séries \| HP** (@hp.filmes) | quase preto `#111111` | dourado `#D4AF37` | vermelho-cinema `#B3122E` | branco | dourado/preto 8,98 · branco/vermelho 6,90 | Bebas Neue | Inter | sim | sala de cinema, pôster |
| **Receitas \| HP** (@hp.receitas) | creme `#FFF4E0` | laranja `#FFB347` | laranja-queimado `#C24E00` | branco | marrom `#3A2416`/creme 13,35 · branco/laranja-queimado 4,79 · marrom/laranja 8,17 | Montserrat ExtraBold | Montserrat Medium | não (só a 1ª letra) | cozinha de casa, quentinho |
| **Carros \| HP** (@hp.carros) | grafite `#1F2A36` | vermelho `#C1121F` | vermelho `#C1121F` | branco | branco/grafite 14,56 · branco/vermelho 6,22 · prata `#C0C7CF`/grafite 8,53 | Anton | Inter SemiBold | sim | garagem, asfalto, painel |
| **Destinos \| HP** (@hp.destinos) | areia `#F2D8A7` | turquesa `#00A6C8` (só enfeite) | azul-petróleo `#005F87` | branco | azul-escuro `#0B2E3A`/areia 10,34 · branco/azul-petróleo 7,03 | Montserrat ExtraBold | Montserrat Medium | não (só a 1ª letra) | praia, céu, mapa |

**Combinações proibidas (contraste baixo demais, medido):**

| Combinação | Contraste | Por que não |
|---|---|---|
| Branco sobre rosa neon `#FF2E88` | 3,50 | só serve para número gigante (≥ 150 px); em título normal, lê mal no sol |
| Branco sobre turquesa `#00A6C8` | 2,88 | ilegível no celular |
| Branco sobre amarelo `#FFD400` | 1,43 | ilegível |
| Branco sobre cinza médio `#9AA0A6` | 2,64 | ilegível |
| Vermelho `#E63946` sobre grafite | 3,49 | vibra e cansa; só em detalhe, nunca texto |
| Branco sobre verde-gramado `#0F9D58` | 3,51 | só número gigante |

**Elementos fixos de todo molde:**

- **Selo do canal**: o nome curto do canal ("GTA 6 | HP", "Futebol | HP"…) em cima à esquerda, dentro da zona segura (na capa: x 90, y 280), altura 44–52 px, na cor de destaque.
- **@ do canal**: embaixo à direita nas lâminas e no pin (28–32 px). Na capa de reel **não** vai @ (o perfil já aparece na tela).
- **Caixa atrás do texto**: retângulo de cantos arredondados (raio 24 px) na cor da caixa com 85–100% de opacidade, **ou** degradê preto de 0% a 70% de opacidade subindo de baixo. Texto solto em cima de foto sem caixa nem degradê é proibido (regra 4.9).
- **Sombra no texto**: sombra preta 60%, deslocamento 0 x 4 px, desfoque 12 px — ajuda quando a foto tem partes claras.

**Tipografia (tamanho mínimo em cada peça):**

| Peça | Título | Subtítulo | Texto corrido | Crédito / rodapé / numeração |
|---|---|---|---|---|
| Capa de reel 1080x1920 | 96–140 px (mínimo absoluto 88) | 48–60 px | não usar texto corrido | 30–34 px |
| Story 1080x1920 | 88–120 px | 48–56 px | 44–52 px, até 25 palavras | 30–34 px |
| Lâmina 1080x1350 | 72–100 px | 44–52 px | 40–48 px, até 40 palavras por lâmina | 28–32 px |
| Pin 1000x1500 | 80–110 px | 44–52 px | 38–44 px, até 20 palavras | 28–32 px |

- Até **3 linhas** de título. Até **18 caracteres por linha** de título na capa (com fonte condensada tipo Anton/Bebas, cabem ~16–20 caracteres por linha em 110 px dentro de 900 px de largura).
- **Entrelinha** do título: 0,95 a 1,05 do tamanho da letra. Do texto corrido: 1,25 a 1,35.
- **Alinhamento**: título centralizado na capa e no story; alinhado à esquerda nas lâminas de conteúdo (fica mais fácil de ler texto longo).
- **Destaque de 1 palavra**: pode pintar **uma** palavra do título na cor de destaque (ex.: "NOVIDADE NA **QUINTA**?"). Nunca duas.
- **Só fontes de licença livre** (Google Fonts, licença OFL): Anton, Bebas Neue, Montserrat, Inter. Fonte "baixada de site qualquer" é proibida (direito autoral).

### 2.10 Saída: exemplo completo de `design.json` (o recibo do Designer)

Todo item que passa pelo Designer ganha um `design.json`. É com ele que o app sabe que a parte visual está pronta e é nele que o Revisor confere as medidas sem precisar abrir a imagem.

```json
{
  "esquema": "hp.design/1",
  "item": "P1_2026-09-30_1830_gta_rockstar-quinta",
  "canal": "gta",
  "tipo": "reel",
  "status": "pronto",
  "versao": 1,
  "pecas": [
    {
      "arquivo": "capa.jpg",
      "papel": "capa_reel",
      "largura": 1080,
      "altura": 1920,
      "kb": 418,
      "quadro_origem": {"arquivo": "final.mp4", "segundo": 3.4},
      "titulo": "ROCKSTAR SOLTA NOVIDADE NA QUINTA?",
      "linhas_titulo": 3,
      "fonte_titulo": "Anton",
      "tamanho_titulo_px": 118,
      "caixa_titulo": {"x": 90, "y": 440, "largura": 900, "altura": 420},
      "cor_texto": "#FFFFFF",
      "cor_caixa": "#7B2CBF",
      "contraste": 7.11,
      "safe_zone_ok": true,
      "dentro_grade_3x4": true,
      "credito": null,
      "valores_aproximados": "nao_se_aplica"
    }
  ],
  "checagens": {
    "dimensoes": true,
    "peso": true,
    "formato_jpg_srgb": true,
    "safe_zone": true,
    "contraste_minimo": 7.11,
    "ortografia_conferida": true,
    "credito": "nao_se_aplica",
    "valores_aproximados": "nao_se_aplica",
    "numeracao_laminas": "nao_se_aplica"
  },
  "ferramenta": "scripts\\posts_canais.py",
  "molde": "gta_capa_v1",
  "feito_por": "designer-claude",
  "modo": "valendo",
  "feito_em": "2026-09-30T16:05:12-03:00",
  "duracao_s": 142,
  "observacoes": ""
}
```

Exemplo do mesmo recibo para o carrossel de Receitas (só a parte que muda):

```json
{
  "esquema": "hp.design/1",
  "item": "P2_2026-10-02_1130_receitas_bolo-cenoura-carrossel",
  "canal": "receitas",
  "tipo": "carrossel",
  "status": "pronto",
  "versao": 1,
  "pecas": [
    {"arquivo": "lamina_01.jpg", "papel": "capa",     "largura": 1080, "altura": 1350, "kb": 612, "numeracao": "1/7", "credito": "Foto: @hp.receitas", "contraste": 13.35, "safe_zone_ok": true, "valores_aproximados": "nao_se_aplica"},
    {"arquivo": "lamina_02.jpg", "papel": "conteudo", "largura": 1080, "altura": 1350, "kb": 540, "numeracao": "2/7", "credito": "Foto: @hp.receitas", "contraste": 13.35, "safe_zone_ok": true, "valores_aproximados": "nao_se_aplica"},
    {"arquivo": "lamina_03.jpg", "papel": "conteudo", "largura": 1080, "altura": 1350, "kb": 201, "numeracao": "3/7", "credito": null, "contraste": 13.35, "safe_zone_ok": true, "valores_aproximados": "nao_se_aplica"},
    {"arquivo": "lamina_04.jpg", "papel": "conteudo", "largura": 1080, "altura": 1350, "kb": 198, "numeracao": "4/7", "credito": null, "contraste": 13.35, "safe_zone_ok": true, "valores_aproximados": "nao_se_aplica"},
    {"arquivo": "lamina_05.jpg", "papel": "conteudo", "largura": 1080, "altura": 1350, "kb": 577, "numeracao": "5/7", "credito": "Foto: @hp.receitas", "contraste": 13.35, "safe_zone_ok": true, "valores_aproximados": "nao_se_aplica"},
    {"arquivo": "lamina_06.jpg", "papel": "conteudo", "largura": 1080, "altura": 1350, "kb": 205, "numeracao": "6/7", "credito": null, "contraste": 13.35, "safe_zone_ok": true, "valores_aproximados": "sim"},
    {"arquivo": "lamina_07.jpg", "papel": "cta",      "largura": 1080, "altura": 1350, "kb": 190, "numeracao": "7/7", "credito": null, "contraste": 4.79,  "safe_zone_ok": true, "valores_aproximados": "nao_se_aplica"},
    {"arquivo": "pin.jpg",       "papel": "pin",      "largura": 1000, "altura": 1500, "kb": 655, "numeracao": null,  "credito": "Foto: @hp.receitas", "contraste": 13.35, "safe_zone_ok": true, "valores_aproximados": "sim"}
  ],
  "checagens": {
    "dimensoes": true,
    "peso": true,
    "formato_jpg_srgb": true,
    "safe_zone": true,
    "contraste_minimo": 4.79,
    "ortografia_conferida": true,
    "credito": "ok",
    "valores_aproximados": "ok",
    "numeracao_laminas": "ok"
  },
  "ferramenta": "scripts\\estaticos.py",
  "molde": "receitas_carrossel_v1",
  "feito_por": "designer-claude",
  "modo": "valendo",
  "feito_em": "2026-09-30T14:22:40-03:00",
  "duracao_s": 510,
  "observacoes": "Lâmina 6 com rodapé de valores."
}
```

Valores aceitos em cada campo:

| Campo | Valores aceitos |
|---|---|
| `status` | `"rascunho"` (ainda fazendo), `"pronto"` (pode ir para revisão), `"travado"` (falta algo — escreva o quê em `observacoes`) |
| `papel` | `capa_reel`, `capa`, `conteudo`, `cta`, `story`, `story_enquete`, `story_contagem`, `pin`, `threads`, `feed` |
| `valores_aproximados` | `"sim"` (tem valor e tem rodapé), `"nao_se_aplica"` (não tem valor), **nunca** `"nao"` com valor na arte |
| `feito_por` | `designer-claude`, `designer-app`, `designer-antonio` |
| `modo` | `"sombra"` (o app fez só para comparar; não vale) ou `"valendo"` |

### 2.11 Linha que o Designer acrescenta no `historico.log`

Formato (uma linha por ação; a data e hora entram sozinhas no começo quando o app grava):

```
2026-09-30T16:05:12-03:00 [designer] capa.jpg v1 pronta (1080x1920, 418 KB, contraste 7,11, safe zone ok) — designer-claude
```

Para carrossel:

```
2026-09-30T14:22:40-03:00 [designer] carrossel 7 lâminas + pin prontos (valores aproximados na lâmina 6 e no pin) — designer-claude
```

---

## 3. Passo a passo numerado para leigo

São **58 passos** divididos em 8 partes. Nem todo item usa todos: um reel usa as partes A, B, C, G (e H se voltar); um carrossel usa A, B, D, G; um story usa A, B, E, G; um pin usa A, B, F, G.

| Parte | Passos | Quando usar |
|---|---|---|
| A — Preparar o computador | 1 a 7 | sempre, uma vez por sessão de trabalho |
| B — Achar o trabalho e entender o pedido | 8 a 14 | sempre |
| C — Capa de reel | 15 a 29 | item `tipo: "reel"` |
| D — Carrossel (e arte de feed avulsa) | 30 a 42 | item `tipo: "carrossel"` ou `"feed"` |
| E — Stories (conteúdo, enquete das 16h, contagem regressiva) | 43 a 48 | item `tipo: "story"`, `"story_enquete"`, `"story_contagem"` |
| F — Pin do Pinterest | 49 a 52 | quando `redes` tem `"pinterest"` (só Receitas, Carros, Destinos) |
| G — Entregar | 53 a 55 | sempre |
| H — Quando o Revisor devolve | 56 a 58 | quando existe `refazer.json` na pasta |

### Parte A — Preparar o computador

#### Passo 1 — Abrir o PowerShell
- **Abra:** aperte `Windows + X` e clique em **Terminal** (em alguns PCs aparece **Windows PowerShell**).
- **Rode:** nada ainda.
- **Confira:** a janela abriu e tem um texto parecido com `PS C:\Users\...>` piscando.
- **Deve aparecer:** o cursor piscando esperando você digitar.

#### Passo 2 — Criar os atalhos desta sessão
Estes 4 atalhos evitam digitar caminho comprido o tempo todo. Eles valem só enquanto a janela estiver aberta; se fechar, rode de novo.
- **Rode:**
```powershell
$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
$E  = "H:\HypadoLocal\esteira"
$S  = "G:\Meu Drive\Hypado\scripts"
Set-Location "G:\Meu Drive\Hypado"
```
- **Confira:** nenhuma mensagem vermelha.
- **Deve aparecer:** a linha de comando muda para `PS G:\Meu Drive\Hypado>`.

#### Passo 3 — Conferir o Python
- **Rode:**
```powershell
& $py --version
```
- **Deve aparecer:** `Python 3.12.` seguido de um número (ex.: `Python 3.12.6`).
- **Se aparecer** "não é reconhecido" ou "não foi possível encontrar": veja a seção 6, erro E01.

#### Passo 4 — Conferir o ffmpeg (programa que tira quadro do vídeo e desenha as caixas de conferência)
- **Rode:**
```powershell
ffmpeg -version | Select-Object -First 1
```
- **Deve aparecer:** uma linha começando com `ffmpeg version`.
- **Se aparecer** "ffmpeg não é reconhecido": seção 6, erro E02.
- **Observação:** o `ffprobe` (irmão do ffmpeg) pode não existir no PC. Este manual **não depende** dele: tudo é feito só com o `ffmpeg`.

#### Passo 5 — Conferir as ferramentas de arte que já existem
- **Rode:**
```powershell
& $py "$S\estaticos.py" --help
& $py "$S\posts_canais.py" --help
```
- **Confira:** leia a ajuda de cada um e anote num papel quais parâmetros existem para: **canal**, **tipo de peça** (capa, lâmina, story, pin), **título**, **texto**, **imagem de fundo** e **pasta de saída**. Os nomes exatos dos parâmetros são os que a ajuda mostrar — este manual **não** inventa parâmetro.
- **Deve aparecer:** o texto de ajuda de cada script (começa com `usage:` ou `uso:`).
- **Se** um dos dois não tiver ajuda ou der erro: use o outro; se os dois falharem, seção 6, erro E03.

#### Passo 6 — Conferir as fontes (tipos de letra) instaladas
- **Rode:**
```powershell
Get-ChildItem "$env:WINDIR\Fonts", "$env:LOCALAPPDATA\Microsoft\Windows\Fonts" -ErrorAction SilentlyContinue |
  Where-Object Name -match 'Anton|Bebas|Montserrat|Inter' | Select-Object Name
```
- **Deve aparecer:** pelo menos um arquivo de cada: `Anton-Regular.ttf`, `BebasNeue-Regular.ttf`, `Montserrat-...ttf`, `Inter-...ttf` (os nomes podem variar um pouco).
- **Se faltar alguma:** seção 6, erro E04. **Nunca** substitua por Arial/Impact "porque é parecida" — a identidade do canal muda e o Revisor devolve.

#### Passo 7 — Conferir a hora e a trava de trabalho pesado
Uma capa avulsa é leve e pode ser feita a qualquer hora. **Lote de artes** (mais de 10 imagens de uma vez, ex.: todos os estáticos do dia) é pesado.
- **Rode:**
```powershell
Get-Date -Format "HH:mm"
Test-Path "H:\HypadoLocal\app\pesado.lock"
```
- **Confira:** se a hora estiver entre **18:00 e 22:29** e você for gerar **lote**, pare e deixe para depois das 22h30 (ou antes das 18h). Se o segundo comando responder `True`, outro trabalho pesado está rodando: espere ele terminar para rodar lote.
- **Deve aparecer:** a hora (ex.: `16:02`) e `False` (sem trava).

### Parte B — Achar o trabalho e entender o pedido

#### Passo 8 — Ver a fila da etapa de edição e escolher o item
- **Rode:**
```powershell
Get-ChildItem "$E\04_edicao" -Directory | Sort-Object Name | Select-Object Name
```
- **Confira:** a lista vem ordenada: primeiro os `P0_` (urgentes), depois `P1_`, depois `P2_`. **Sempre pegue o de cima**, a não ser que ele já tenha `design.json` com `"status": "pronto"` (já foi feito — pule para o próximo).
- **Rode** (troque o nome pelo item escolhido):
```powershell
$item = "$E\04_edicao\P1_2026-09-30_1830_gta_rockstar-quinta"
Test-Path $item
```
- **Deve aparecer:** `True`.
- **Atalho** (pega sozinho o primeiro da lista):
```powershell
$item = (Get-ChildItem "$E\04_edicao" -Directory | Sort-Object Name | Select-Object -First 1).FullName
$item
```

#### Passo 9 — Ver o que tem dentro da pasta
- **Rode:**
```powershell
Get-ChildItem $item | Select-Object Name, Length, LastWriteTime
```
- **Confira:** a lista de arquivos, comparando com a tabela 2.3.
- **Deve aparecer (reel):** pelo menos `pedido.json`, `final.mp4`, `post.json`, `historico.log`.
- **Deve aparecer (carrossel/story/pin):** pelo menos `pedido.json`, `historico.log` e a subpasta `fontes` (se o pedido usa fotos).

#### Passo 10 — Ler o pedido
- **Rode:**
```powershell
$pedido = Get-Content "$item\pedido.json" -Raw -Encoding UTF8 | ConvertFrom-Json
$pedido | Select-Object canal, conta, tipo, prioridade, postar_em, tema
$pedido.redes
```
- **Confira:** `canal` (qual molde usar), `tipo` (qual parte deste manual seguir), `prioridade` (P0 = rapidez máxima), `redes` (tem `pinterest`? então precisa de `pin.jpg` — Parte F).
- **Deve aparecer:** por exemplo `gta  @hpgta6  reel  P1  2026-09-30T18:30:00-03:00  Rockstar avisa...` e a lista `instagram facebook tiktok youtube threads`.
- **Importante:** sempre use `-Encoding UTF8`. Sem ele, o PowerShell 5.1 lê acentos errado ("NOVIDADE NA QUINTA" fica certo, mas "Receitas de fÃ©rias" aparece torto) — seção 6, erro E05.

#### Passo 11 — Decidir quais peças fazer
Use esta tabela:

| `tipo` no pedido | Peças que o Designer faz | Parte do manual |
|---|---|---|
| `reel` | `capa.jpg` (+ `pin.jpg` se `redes` tiver `pinterest`) | C (+ F) |
| `carrossel` | `lamina_01.jpg` … `lamina_NN.jpg` (+ `pin.jpg` se tiver `pinterest`) | D (+ F) |
| `feed` | `lamina_01.jpg` (uma só, 1080x1350) | D |
| `story` | `story.jpg` | E |
| `story_enquete` | `story.jpg` com caixa vazia para a enquete | E (passo 45) |
| `story_contagem` | `story.jpg` com o número de dias | E (passo 46) |
| `pin` | `pin.jpg` | F |
| `threads_imagem` | `threads.jpg` (1080x1350, mesmas regras da lâmina) | D |
| `threads_texto` | nada — não é com o Designer | — |

#### Passo 12 — Ver se é trabalho novo ou uma volta do Revisor
- **Rode:**
```powershell
$ref = Get-ChildItem $item -Filter "refazer*.json" | Sort-Object LastWriteTime | Select-Object -Last 1
$ref | Select-Object Name, LastWriteTime
if (Test-Path "$item\design.json") { (Get-Item "$item\design.json").LastWriteTime } else { "sem design.json" }
```
- **Confira:** se aparece um arquivo de volta (`refazer.json`, ou `refazer_1_feito.json` / `refazer_2_feito.json` quando um cargo anterior — manuais 04 e 05 — já renomeou) **mais novo** que o seu `design.json`, o item **voltou** da revisão e você ainda não refez: vá direto para a Parte H (passo 56). Não refaça tudo do zero. Se o arquivo de volta é **mais velho** que o `design.json`, você já refez nesta volta.
- **Deve aparecer (trabalho novo):** nenhuma linha de arquivo de volta e `sem design.json`.

#### Passo 13 — Ler o título que o Redator escreveu (só reel, story e pin)
- **Rode:**
```powershell
$post = Get-Content "$item\post.json" -Raw -Encoding UTF8 | ConvertFrom-Json
$post.titulo_capa
$post.subtitulo_capa
$post.status
$post.valores_aproximados
```
- **Confira:** `status` tem que ser `pronto`. Se o arquivo não existe ou o status é `rascunho`, o Redator ainda não terminou: **espere** (com o app ligado, ele avisa quando ficar pronto). Em item `P0_`, não espere parado: faça a capa de emergência (passo 22, plano B) e troque depois.
- **Deve aparecer:** por exemplo `ROCKSTAR SOLTA NOVIDADE NA QUINTA?`, `o que dá pra esperar`, `pronto`, `False`.

#### Passo 14 — Conferir o vídeo final (só reel)
- **Rode:**
```powershell
ffmpeg -hide_banner -i "$item\final.mp4" 2>&1 | Select-String "Duration|Video:"
```
- **Confira:** a duração e o tamanho do vídeo.
- **Deve aparecer:** algo como `Duration: 00:00:38.40` e `Video: h264 ... 1080x1920`.
- **Se** o vídeo não for 1080x1920: **não é problema do Designer**, mas anote em `design.json` → `observacoes` ("final.mp4 veio 720x1280") para o Revisor ver. A capa continua sendo 1080x1920.

### Parte C — Capa de reel

#### Passo 15 — Medir o título
- **Rode:**
```powershell
$t = $post.titulo_capa
"$($t.Length) caracteres, $(($t -split '\s+').Count) palavras"
```
- **Confira:** até **36 caracteres** e até **6 palavras** (é o limite que o Redator usa — manual 08, passo 18).
- **Deve aparecer:** por exemplo `34 caracteres, 5 palavras` → dentro do limite. Se passar de 36 caracteres ou de 6 palavras, veja o passo 17.

#### Passo 16 — Quebrar o título em linhas (no papel, antes de gerar)
Regras da quebra:
1. No máximo **3 linhas**, até **18 caracteres por linha** (contando espaço).
2. Quebre na **pausa natural** da frase (onde você respiraria ao ler em voz alta).
3. **Nunca** separe número da palavra que ele mede ("50 / DIAS" errado; "50 DIAS" junto certo).
4. **Nunca** deixe uma palavrinha sozinha na última linha ("DE", "O", "NA").
5. A palavra que você pintar na cor de destaque (só 1) é a que carrega a novidade.

Exemplos prontos dos 6 canais:

| Canal | `titulo_capa` | Quebra certa | Palavra em destaque |
|---|---|---|---|
| GTA 6 \| HP | ROCKSTAR SOLTA NOVIDADE NA QUINTA? | ROCKSTAR SOLTA / NOVIDADE / NA QUINTA? | QUINTA? (rosa neon) |
| Futebol \| HP | PEDRO DE NOVO! FLAMENGO 2x0 | PEDRO DE NOVO! / FLAMENGO 2x0 | 2x0 (amarelo) |
| Filmes e Séries \| HP | 5 ESTREIAS DE OUTUBRO QUE VALEM | 5 ESTREIAS / DE OUTUBRO / QUE VALEM | 5 (dourado) |
| Receitas \| HP | Bolo de cenoura de liquidificador | Bolo de cenoura / de liquidificador | cenoura (laranja) |
| Carros \| HP | OS 5 CARROS MAIS BARATOS DE 2026 | OS 5 CARROS / MAIS BARATOS / DE 2026 | BARATOS (vermelho) |
| Destinos \| HP | Gramado gastando pouco | Gramado / gastando pouco | pouco (turquesa como sublinhado, texto em azul-petróleo) |

Quebras **erradas** (não faça):

| Errado | Por quê |
|---|---|
| ROCKSTAR SOLTA NOVIDADE / NA / QUINTA? | "NA" sozinho; linha 1 com 23 caracteres |
| OS 5 / CARROS MAIS BARATOS DE 2026 | linha 2 com 28 caracteres, fica letra pequena |
| PEDRO DE NOVO! FLAMENGO / 2x0 | placar isolado, perde força |

#### Passo 17 — Se o título não cabe: pedir outro ao Redator (não cortar por conta própria)
- **Quando:** mais de 36 caracteres, mais de 6 palavras, ou a quebra do passo 16 exige 4 linhas.
- **Rode** (grava o pedido no próprio `design.json`, com status travado):
```powershell
$trava = @{
  esquema = "hp.design/1"; item = (Split-Path $item -Leaf); canal = $pedido.canal; tipo = $pedido.tipo
  status = "travado"; versao = 0; pecas = @()
  observacoes = "titulo_capa com $($post.titulo_capa.Length) caracteres; preciso de ate 36 e ate 6 palavras"
  feito_por = "designer-claude"; feito_em = (Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz")
}
$trava | ConvertTo-Json -Depth 6 | Set-Content "$item\design.json" -Encoding UTF8
```
- **Confira:** o arquivo `design.json` foi criado.
- **Deve aparecer:** nada na tela (silêncio = deu certo).
- **O que acontece depois:** com o app ligado, ele devolve o item ao Redator **(a criar — etapa 3)**. Hoje, sem o app, quem faz o papel de Redator (o próprio Claude) reescreve o `titulo_capa` seguindo o manual 08 e você volta ao passo 13.

#### Passo 18 — Fazer a "folha de quadros" do vídeo (8 quadros numa imagem só)
- **Rode:**
```powershell
New-Item -ItemType Directory -Force "$item\candidatos" | Out-Null
ffmpeg -hide_banner -loglevel error -y -i "$item\final.mp4" -vf "fps=1/3,scale=270:480,tile=4x2" -frames:v 1 "$item\candidatos\folha.jpg"
Invoke-Item "$item\candidatos\folha.jpg"
```
- **Confira:** abre uma imagem com 8 quadrinhos, um a cada 3 segundos do vídeo (0 s, 3 s, 6 s, 9 s na linha de cima; 12 s, 15 s, 18 s, 21 s na de baixo).
- **Deve aparecer:** a imagem no visualizador de fotos do Windows.
- **Para vídeo com mais de 24 s**, se quiser ver o vídeo todo, troque `fps=1/3` por `fps=1/6` (um quadro a cada 6 s).

#### Passo 19 — Escolher o melhor quadro
Critérios, nesta ordem (o primeiro que falhar elimina o quadro):
1. **Não pode ser proibido:** nada de imagem de vazamento de GTA 6; nada de imagem de transmissão de TV no Futebol (placar de emissora, logo de canal no canto); nada do Flow Games; nada que seja spoiler grande em Filmes e Séries.
2. **Nítido:** sem borrão de movimento, sem tela preta, sem transição no meio.
3. **Tem um "herói":** rosto com expressão forte, o carro inteiro, o prato pronto, a paisagem mais bonita, o jogador comemorando, o personagem principal.
4. **Sem legenda queimada** no lugar onde vai o título (a legenda do vídeo fica em geral na metade de baixo; o título vai em cima — mas confira).
5. **Deixa espaço** para o título na faixa y 420–1000 sem cobrir o rosto/objeto principal.

Exemplo de escolha por canal:

| Canal | Quadro bom | Quadro ruim |
|---|---|---|
| GTA 6 | Lucia de perfil com o pôr do sol de Vice City (imagem oficial do trailer da Rockstar) | tela de "vazamento" de fórum; quadro escuro de transição |
| Futebol | jogador comemorando no vídeo oficial do clube | quadro com o logo de emissora de TV no canto |
| Filmes e Séries | pôster oficial ou cena de divulgação sem spoiler | a cena da morte do personagem |
| Receitas | fatia do bolo com a cobertura escorrendo | liquidificador vazio |
| Carros | carro inteiro de 3/4 de frente | painel desfocado |
| Destinos | vista mais aberta do lugar, céu limpo | foto de corredor de hotel |

- **Se nenhum dos 8 serve:** abra o vídeo inteiro (`Invoke-Item "$item\final.mp4"`), pause no melhor momento e anote o segundo que aparece no player.

#### Passo 20 — Conferir que naquele segundo não tem legenda na tela
- **Rode:**
```powershell
Get-Content "$item\legenda.srt" -Encoding UTF8 | Select-Object -First 40
```
- **Confira:** a legenda tem blocos com tempo, tipo `00:00:04,200 --> 00:00:06,900`. Escolha um segundo que fique **entre** o fim de um bloco e o começo do próximo. Se não houver buraco, tudo bem: a caixa do título vai ficar em cima, longe da legenda (que fica embaixo) — mas confira na imagem.
- **Deve aparecer:** os primeiros blocos da legenda.
- **Grave o segundo escolhido:**
```powershell
$seg = 5.4
```

#### Passo 21 — Tirar o quadro em qualidade máxima
- **Rode:**
```powershell
ffmpeg -hide_banner -loglevel error -y -ss $seg -i "$item\final.mp4" -frames:v 1 -q:v 1 "$item\candidatos\base.jpg"
Invoke-Item "$item\candidatos\base.jpg"
```
- **Confira:** é o quadro que você queria, nítido, 1080x1920.
- **Deve aparecer:** a imagem aberta.
- **Dica:** se o quadro saiu meio borrado, tente 0,2 s antes ou depois (`$seg = 5.2` ou `5.6`) e rode de novo.

#### Passo 22 — Aplicar o molde do canal e gerar a `capa.jpg`
- **Rode** a ferramenta de arte que o passo 5 mostrou que faz capa, com os parâmetros que a ajuda dela indicar, passando: o canal (`$pedido.canal`), o título já quebrado em linhas (passo 16), o subtítulo (`$post.subtitulo_capa`, se houver), a palavra de destaque, a imagem de fundo (`$item\candidatos\base.jpg`) e a saída `$item\capa.jpg`. Exemplo do **formato** do comando (os nomes dos parâmetros vêm do `--help`, confira antes):
```powershell
& $py "$S\posts_canais.py" --help   # veja os nomes certos dos parâmetros antes de rodar
```
- **Confira:** o arquivo `capa.jpg` apareceu na pasta do item (se a ferramenta salvou em outro lugar, copie: `Copy-Item "<onde ela salvou>\<arquivo>.jpg" "$item\capa.jpg"`).
- **Deve aparecer:** `capa.jpg` na pasta, com o título na caixa da cor do canal (tabela 2.9).
- **Plano B — capa de emergência (só P0, quando a ferramenta falhar e o post não pode esperar):** use o próprio quadro como capa, sem título:
```powershell
Copy-Item "$item\candidatos\base.jpg" "$item\capa.jpg"
```
  e escreva em `design.json` → `observacoes`: `"capa de emergência sem título — refazer depois"`. Abra um ticket pela `scripts\tickets.py` na área de design contando o erro da ferramenta. Nunca use o plano B em P1 ou P2.

#### Passo 23 — Conferir tamanho e peso da capa
- **Rode:**
```powershell
Add-Type -AssemblyName System.Drawing
$img = [System.Drawing.Image]::FromFile("$item\capa.jpg")
"$($img.Width) x $($img.Height)"
$img.Dispose()
"{0:N0} KB" -f ((Get-Item "$item\capa.jpg").Length / 1KB)
```
- **Deve aparecer:** `1080 x 1920` e um peso entre **200 KB e 1.000 KB** (meta 300–700 KB).
- **Se** der outro tamanho: seção 6, erro E07. **Se** passar de 1.000 KB: erro E08.
- **Atenção:** o `$img.Dispose()` é obrigatório; sem ele o Windows "prende" o arquivo e o próximo passo não consegue mexer nele.

#### Passo 24 — Medir o contraste entre a cor do texto e a cor da caixa
Contraste é quanto uma cor se destaca da outra. A régua vai de 1 (igual, invisível) a 21 (preto no branco). **Mínimo 4,5** para qualquer texto; título gigante (≥ 150 px) aceita 3,0.
- **Rode** (troque as duas cores — sem o `#` — pelas que você usou; exemplo: branco sobre roxo do GTA):
```powershell
& $py -c "import sys;f=lambda c:c/12.92 if c<=0.03928 else ((c+0.055)/1.055)**2.4;L=lambda h:0.2126*f(int(h[0:2],16)/255)+0.7152*f(int(h[2:4],16)/255)+0.0722*f(int(h[4:6],16)/255);a,b=sorted([L(sys.argv[1]),L(sys.argv[2])]);print(round((b+0.05)/(a+0.05),2))" FFFFFF 7B2CBF
```
- **Deve aparecer:** `7.11` (passou, é maior que 4,5).
- Outros exemplos já medidos: `FFD400 0B3D2E` → `8.52` (Futebol, passou) · `FFFFFF 00A6C8` → `2.88` (Destinos, **reprovado**) · `3A2416 FFF4E0` → `13.35` (Receitas, passou).
- **Texto sobre foto sem caixa:** não existe contraste confiável (a foto muda de cor). Por isso a regra 4.9 manda sempre caixa ou degradê.

#### Passo 25 — Desenhar a zona segura por cima da capa (conferência visual)
Este comando cria uma **cópia** da capa com as áreas proibidas pintadas de vermelho, o corte da grade (3:4) em amarelo e a faixa ideal do título em verde. A capa original não muda.
- **Rode:**
```powershell
ffmpeg -hide_banner -loglevel error -y -i "$item\capa.jpg" -vf "drawbox=x=0:y=0:w=1080:h=250:color=red@0.4:t=fill,drawbox=x=0:y=1500:w=1080:h=420:color=red@0.4:t=fill,drawbox=x=0:y=250:w=90:h=1250:color=red@0.4:t=fill,drawbox=x=990:y=250:w=90:h=1250:color=red@0.4:t=fill,drawbox=x=0:y=240:w=1080:h=1440:color=yellow@0.9:t=6,drawbox=x=90:y=420:w=900:h=580:color=lime@0.9:t=4" -q:v 3 "$item\conferencia_capa.jpg"
Invoke-Item "$item\conferencia_capa.jpg"
```
- **Confira:**
  1. Nenhuma letra do título, subtítulo ou selo encosta no vermelho.
  2. O título está **dentro** do retângulo verde (faixa ideal) — tolerância: pode passar até 60 px para baixo.
  3. Tudo que é texto está dentro do retângulo amarelo (o que aparece na grade do perfil).
- **Deve aparecer:** a capa com as faixas coloridas e o texto todo na área limpa.

#### Passo 26 — Simular a capa na grade do perfil (tamanho de celular)
- **Rode:**
```powershell
ffmpeg -hide_banner -loglevel error -y -i "$item\capa.jpg" -vf "crop=1080:1440:0:240,scale=360:480" "$item\conferencia_grade.jpg"
Invoke-Item "$item\conferencia_grade.jpg"
```
- **Confira:** esta imagem pequena (360x480) é mais ou menos o tamanho real da capa na grade do perfil no celular. **Teste do braço esticado:** afaste-se da tela até ela parecer um celular na mão. Dá para ler o título inteiro em 1 segundo? Se não, o título está pequeno ou com contraste baixo.
- **Deve aparecer:** o miolo da capa, com o título inteiro visível (nada cortado em cima nem embaixo).

#### Passo 27 — Conferir a ortografia letra por letra
- **Abra:** `capa.jpg` (Invoke-Item) e, ao lado, o texto do título (`$post.titulo_capa`).
- **Confira:** leia **em voz alta**, uma palavra por vez, comparando a imagem com o texto: acentos (É, Ã, Ç), ponto de interrogação, número, placar (2x0, não 2 x 0 nem 2X0), nome próprio (Lucia, Jason, Pedro, Flamengo, Gramado, Corolla).
- **Deve aparecer:** 100% igual. Uma letra errada na capa = nota 0 no critério "Ortografia da arte" (seção 5).

#### Passo 28 — Conferir as proibições na capa
Marque cada item (todos têm que ser "sim"):
- [ ] Não tem nada de vazamento de GTA 6 (nem imagem, nem palavra "vazou", "leak").
- [ ] Não tem nada do Flow Games (nome, logo, imagem, pessoa associada).
- [ ] Futebol: não é imagem de transmissão de TV (sem logo de emissora, sem placar de emissora na tela).
- [ ] Filmes e Séries: não entrega spoiler grande (final, morte, reviravolta).
- [ ] Se aparece valor (R$, preço, FIPE), tem o rodapé "Valores aproximados…" (regra 4.6) — em capa de reel isso é raro; se o título tem preço, peça ao Redator para tirar o preço da capa (o preço fica no vídeo e na legenda, onde o aviso cabe).
- [ ] Nada de marca d'água, @ ou logo de outro canal/perfil.
- [ ] Nenhuma promessa mentirosa no visual (seta apontando para algo que não existe, "ADIADO!" quando não foi).

#### Passo 29 — Apagar os candidatos? Não.
- **Confira:** deixe a subpasta `candidatos\` e os arquivos `conferencia_*.jpg` onde estão. Eles pesam pouco, ajudam o Revisor e o teste de paridade (7 dias de modo sombra), e o Publicador ignora tudo que não está no `post.json`.

### Parte D — Carrossel (e arte de feed avulsa)

#### Passo 30 — Listar as lâminas pedidas
- **Rode:**
```powershell
$pedido.laminas | Format-Table n, papel, titulo, imagem, credito -AutoSize
"Total: $($pedido.laminas.Count) lâminas"
```
- **Deve aparecer:** a tabela das lâminas (ex.: 7 linhas no bolo de cenoura) e `Total: 7 lâminas`.

#### Passo 31 — Conferir a estrutura do carrossel
| Regra | Como conferir | Se falhar |
|---|---|---|
| Entre 5 e 10 lâminas (padrão HP: 7) | `$pedido.laminas.Count` | menos de 5: pedir mais conteúdo ao Curador; mais de 10: pedir corte |
| Lâmina 1 tem `papel: "capa"` com gancho | olhar a tabela do passo 30 | pedir ao Curador/Redator |
| Última lâmina tem `papel: "cta"` ("salva", "comenta aí", "manda pra alguém") | olhar a tabela | pedir ao Redator |
| Uma ideia por lâmina | ler cada texto | pedir para dividir |
| Até 40 palavras por lâmina | comando abaixo | pedir para enxugar |

- **Rode** (conta as palavras de cada lâmina):
```powershell
$pedido.laminas | ForEach-Object { "{0}: {1} palavras" -f $_.n, (($_.texto -split '\s+') | Where-Object { $_ }).Count }
```
- **Deve aparecer:** uma linha por lâmina, todas com **40 ou menos**.

Estruturas-modelo de 7 lâminas por canal:

| Canal | 1 (capa) | 2–6 (conteúdo) | 7 (CTA) |
|---|---|---|---|
| GTA 6 | "O QUE A ROCKSTAR JÁ CONFIRMOU" | 5 fatos oficiais, 1 por lâmina, com imagem oficial e "Imagem: Rockstar Games" | "FALTAM 50 DIAS — comenta aí: vai comprar no dia?" |
| Futebol | "TABELA DO BRASILEIRÃO APÓS A RODADA" | G4, meio, Z4, artilharia, próximos jogos (fotos oficiais de clubes com crédito) | "Comenta aí: quem cai?" |
| Filmes e Séries | "5 ESTREIAS DE OUTUBRO QUE VALEM" | 1 estreia por lâmina: pôster de divulgação + data + onde assistir | "Salva pra não esquecer e comenta aí qual você vai ver" |
| Receitas | "Bolo de cenoura de liquidificador" | ingredientes, preparo, forno, cobertura, quanto custa | "Salva pra fazer no fim de semana" |
| Carros | "OS 5 CARROS MAIS BARATOS DE 2026" | 1 carro por lâmina: foto de divulgação da montadora + preço + "Valores aproximados…" | "Comenta aí: qual você compraria?" |
| Destinos | "Gramado gastando pouco" | hospedagem, comida, passeio grátis, passeio pago, melhor época | "Salva e manda pra quem vai com você" |

#### Passo 32 — Conferir as fotos da subpasta `fontes`
- **Rode:**
```powershell
Add-Type -AssemblyName System.Drawing
Get-ChildItem "$item\fontes" -File | ForEach-Object {
  $i = [System.Drawing.Image]::FromFile($_.FullName)
  "{0}  {1}x{2}  {3:N0} KB" -f $_.Name, $i.Width, $i.Height, ($_.Length/1KB)
  $i.Dispose()
}
```
- **Confira:** toda foto que vai ocupar a lâmina inteira precisa ter **pelo menos 1080 px de largura** (e de preferência 1350 de altura). Foto menor que isso fica borrada quando ampliada.
- **Deve aparecer:** uma linha por foto, ex.: `bolo_pronto.jpg  2400x3000  1.812 KB`.
- **Se** uma foto tiver menos de 1080 px de largura: use-a só pequena (em moldura, metade da lâmina) ou peça outra ao Curador (grave `design.json` com status `travado` como no passo 17, observação: "fontes\\x.jpg com 640 px; preciso ≥ 1080").

#### Passo 33 — Conferir crédito de cada foto
- **Rode:**
```powershell
$pedido.laminas | Where-Object { $_.imagem -and -not $_.credito } | Select-Object n, imagem
```
- **Deve aparecer:** **nada** (lista vazia). Se aparecer alguma lâmina, ela tem foto sem crédito: **não gere** — peça o crédito ao Curador (status `travado`). Foto própria da HP leva "Foto: @hp.receitas" (ou o @ do canal).
- **Formatos de crédito aceitos:** `Foto: @perfil` · `Foto: Nome do fotógrafo/Clube` · `Imagem: Rockstar Games` · `Imagem: divulgação/Netflix` · `Imagem: divulgação/Toyota` · `Vídeo: @criador` (quando é quadro de vídeo).

#### Passo 34 — Achar as lâminas que citam valor
- **Rode:**
```powershell
$pedido.laminas | Where-Object { "$($_.titulo) $($_.texto)" -match 'R\$|US\$|€|reais|d[oó]lar|pre[cç]o|FIPE|custa' } | Select-Object n, titulo
```
- **Deve aparecer:** as lâminas que precisam do rodapé "Valores aproximados…" (no bolo de cenoura: a lâmina 6).
- **Texto do rodapé (padrão HP):** `Valores aproximados, pesquisados em set/2026. Podem mudar.` — troque o mês/ano pela `referencia` do pedido. Se o `estaticos.py` já tiver um texto-padrão de rodapé no código, use o do código (é o que já está no ar) desde que comece com "Valores aproximados".

#### Passo 35 — Gerar as lâminas
- **Rode** o `scripts\estaticos.py` com os parâmetros que o `--help` (passo 5) mostrou, passando o canal, o tipo carrossel, a lista de lâminas (título, texto, imagem, crédito, numeração) e a pasta de saída = pasta do item. Se ele aceitar ler direto do `pedido.json`, melhor ainda (menos digitação, menos erro).
```powershell
& $py "$S\estaticos.py" --help   # confira os nomes certos dos parâmetros antes de rodar
```
- **Se é um lote** (vários itens de uma vez): confira antes o passo 7 (horário e trava).
- **Confira:** onde os arquivos foram salvos (a ferramenta mostra no fim). Se não foi na pasta do item, copie e renomeie para o padrão:
```powershell
# exemplo: a ferramenta salvou como carrossel_1.jpg ... carrossel_7.jpg em outra pasta
$origem = "<pasta onde a ferramenta salvou>"
1..7 | ForEach-Object { Copy-Item "$origem\carrossel_$_.jpg" ("$item\lamina_{0:D2}.jpg" -f $_) }
```
- **Deve aparecer:** `lamina_01.jpg` … `lamina_07.jpg` na pasta do item.

#### Passo 36 — Conferir quantidade e ordem
- **Rode:**
```powershell
$laminas = Get-ChildItem "$item\lamina_*.jpg" | Sort-Object Name
$laminas | Select-Object Name
"Geradas: $($laminas.Count) · Pedidas: $($pedido.laminas.Count)"
```
- **Deve aparecer:** os nomes em ordem (`lamina_01.jpg` até `lamina_07.jpg`) e `Geradas: 7 · Pedidas: 7`. Números diferentes = erro E12.
- **Por que `01` e não `1`:** com dois dígitos, a ordem alfabética é igual à ordem certa (`lamina_10` vem depois de `lamina_09`, e não depois de `lamina_1`). O Publicador manda as lâminas nessa ordem.

#### Passo 37 — Conferir o tamanho de todas as lâminas
- **Rode:**
```powershell
Add-Type -AssemblyName System.Drawing
$laminas | ForEach-Object {
  $i = [System.Drawing.Image]::FromFile($_.FullName)
  "{0}  {1}x{2}  {3:N0} KB" -f $_.Name, $i.Width, $i.Height, ($_.Length/1KB)
  $i.Dispose()
}
```
- **Deve aparecer:** todas `1080x1350`, cada uma com menos de 8.000 KB (meta ≤ 1.500 KB).

#### Passo 38 — Montar a folha do carrossel (todas as lâminas numa imagem só)
- **Rode** (até 8 lâminas; para 9 ou 10 troque `tile=4x2` por `tile=5x2`):
```powershell
ffmpeg -hide_banner -loglevel error -y -framerate 1 -start_number 1 -i "$item\lamina_%02d.jpg" -vf "scale=270:338,tile=4x2:padding=6:color=white" -frames:v 1 "$item\conferencia_carrossel.jpg"
Invoke-Item "$item\conferencia_carrossel.jpg"
```
- **Confira:** a sequência conta uma história: capa com gancho → conteúdo na ordem certa → CTA no fim. As cores e as letras são iguais em todas (mesma identidade). A numeração está em todas, no mesmo lugar.
- **Deve aparecer:** uma imagem com as lâminas lado a lado, na ordem.

#### Passo 39 — Conferir a numeração
- **Confira** na folha (passo 38) e, se precisar, abrindo cada lâmina:
  - Toda lâmina tem "n/N" no canto de cima à direita (ex.: `1/7`, `2/7` … `7/7`).
  - O N (total) é o mesmo em todas e bate com o número de arquivos.
  - A lâmina 1 também tem a seta "arrasta →" (ou "arrasta pro lado →") embaixo, dentro da zona segura.
- **Deve aparecer:** 1/7, 2/7, 3/7, 4/7, 5/7, 6/7, 7/7 — sem pular, sem repetir.

#### Passo 40 — Conferir a zona segura de cada lâmina
- **Rode** (cria uma cópia de conferência de cada lâmina com as margens de 80 px em vermelho):
```powershell
$laminas | ForEach-Object {
  ffmpeg -hide_banner -loglevel error -y -i $_.FullName -vf "drawbox=x=0:y=0:w=80:h=1350:color=red@0.4:t=fill,drawbox=x=1000:y=0:w=80:h=1350:color=red@0.4:t=fill,drawbox=x=80:y=0:w=920:h=80:color=red@0.4:t=fill,drawbox=x=80:y=1270:w=920:h=80:color=red@0.4:t=fill" -q:v 3 ("$item\conferencia_" + $_.Name)
}
ffmpeg -hide_banner -loglevel error -y -framerate 1 -start_number 1 -i "$item\conferencia_lamina_%02d.jpg" -vf "scale=270:338,tile=4x2:padding=6:color=white" -frames:v 1 "$item\conferencia_carrossel_margens.jpg"
Invoke-Item "$item\conferencia_carrossel_margens.jpg"
```
- **Confira:** nenhuma letra (título, texto, crédito, numeração, @, rodapé) encosta no vermelho.
- **Deve aparecer:** a folha com as margens vermelhas e todo o texto por dentro.

#### Passo 41 — Conferir rodapé de valores e crédito lâmina por lâmina
- **Abra** cada lâmina que o passo 34 listou e confira: o rodapé "Valores aproximados…" está lá, legível (28–30 px, contraste ≥ 4,5).
- **Abra** cada lâmina que tem `imagem` no pedido e confira: o crédito está lá, embaixo à esquerda, igual ao `credito` do pedido.
- **Deve aparecer:** 100% das lâminas com valor com rodapé; 100% das lâminas com foto de terceiro com crédito.

#### Passo 42 — Conferir a última lâmina (CTA) e o Threads
- **Confira:** a última lâmina pede uma ação clara e só uma principal: "Salva…", "Comenta aí…" ou "Manda pra alguém…" (pode ter uma secundária pequena), e tem o @ do canal.
- **Threads:** as mesmas lâminas servem para o Threads (4:5 funciona lá). Só faça `threads.jpg` separado se o pedido tiver `tipo: "threads_imagem"`. Nesse caso, siga os passos 35–41 para uma única imagem e salve como `threads.jpg`.
- **Arte de feed avulsa** (`tipo: "feed"`): é um carrossel de 1 lâmina só: `lamina_01.jpg`, sem numeração, com crédito e @.

### Parte E — Stories

#### Passo 43 — Story de conteúdo (todos os canais)
- **Regras do story:** 1080x1920 · texto dentro de **x 60–930 e y 250–1580** · uma ideia só · até 25 palavras · título 88–120 px · caixa ou degradê atrás do texto · crédito se a foto for de terceiro.
- **Rode** o `estaticos.py` (parâmetros do `--help`) com tipo story, saída `$item\story.jpg`.
- **Deve aparecer:** `story.jpg` na pasta.
- Exemplos:

| Canal | Story |
|---|---|
| GTA 6 | "A ROCKSTAR MEXEU NO SITE HOJE" + imagem oficial + "Imagem: Rockstar Games" |
| Futebol | placar grande "FLA 2x0 PAL" + foto oficial do clube + "Foto: @flamengo" |
| Filmes e Séries | "CHEGOU HOJE" + pôster de divulgação + "Imagem: divulgação/Netflix" |
| Receitas | "3 INGREDIENTES, 10 MINUTOS" + foto do prato + "Foto: @hp.receitas" |
| Carros | "R$ 79 MIL" em destaque + foto de divulgação + rodapé "Valores aproximados…" + "Imagem: divulgação/Fiat" |
| Destinos | "PRAIA SEM FILA EM OUTUBRO" + foto + crédito |

- **Não confunda:** o **story de divulgação do post** (aquele que compartilha o reel/carrossel recém-publicado) **não é arte do Designer**: o emulador compartilha o próprio post pelo botão "Enviar → Adicionar ao story" (fila `H:\HypadoLocal\emulador\fila_story\`, `scripts\story_clicavel.py`). Não faça arte para ele.

#### Passo 44 — Conferir a zona segura do story
- **Rode:**
```powershell
ffmpeg -hide_banner -loglevel error -y -i "$item\story.jpg" -vf "drawbox=x=0:y=0:w=1080:h=250:color=red@0.4:t=fill,drawbox=x=0:y=1580:w=1080:h=340:color=red@0.4:t=fill,drawbox=x=0:y=250:w=60:h=1330:color=red@0.4:t=fill,drawbox=x=930:y=250:w=150:h=1330:color=red@0.4:t=fill" -q:v 3 "$item\conferencia_story.jpg"
Invoke-Item "$item\conferencia_story.jpg"
```
- **Deve aparecer:** todo o texto fora do vermelho.

#### Passo 45 — Story com enquete das 16h (só GTA 6 | HP)
Todo dia às 16h o GTA posta um story com **enquete** (figurinha de votação do Instagram). A figurinha é colocada pelo emulador Android **(o robô `story_post.py` é a criar — módulo F)** em cima da arte. O Designer faz a arte com uma **caixa vazia** onde a figurinha vai ser arrastada.
- **Layout obrigatório:**

| Elemento | Posição | Tamanho | Cor |
|---|---|---|---|
| Selo "GTA 6 \| HP" | x 60, y 280 | 48 px | rosa neon `#FF2E88` |
| Pergunta grande (a mesma da enquete, pode ser mais longa) | y 380 a 900, centralizada | 96–120 px, até 3 linhas | branco sobre roxo `#7B2CBF` |
| Imagem oficial de fundo | tela toda, escurecida 40% | — | — |
| **Caixa da enquete** | **x 140–940, y 1050–1450** | 800 x 400, cantos arredondados, borda 6 px | borda rosa neon, dentro preto 35% |
| Crédito | x 60, y 1520 | 30 px | branco 80% |

- **Pergunta da figurinha** (vai digitada pelo robô dentro da figurinha, não na arte): até **~25 caracteres** (ex.: `Vai comprar no dia 19/11?` = 25). A arte pode trazer a versão longa: "VAI COMPRAR O GTA 6 NO DIA DO LANÇAMENTO?".
- **Opções** da enquete: curtas (ex.: "Sim, no dia" / "Vou esperar"); o texto exato vem do Redator.
- **Onde a arte é registrada:** o robô pega a arte do dia em `lotes\<dia>_estaticos.json` (ex.: `lotes\2026-09-30_estaticos.json`), que o `scripts\estaticos.py` já grava. Depois de gerar, **confira** que a arte do dia está listada lá:
```powershell
Select-String -Path "<pasta lotes>\2026-09-30_estaticos.json" -Pattern "story|enquete"
```
  (a pasta `lotes` é a que o `estaticos.py` informa na última linha que imprime).
- **Deve aparecer:** a linha com o caminho da arte do story do dia.

#### Passo 46 — Story de contagem regressiva do GTA 6
- **Calcule** os dias (nunca digite de cabeça):
```powershell
((Get-Date "2026-11-19") - (Get-Date).Date).Days
```
- **Deve aparecer:** em 30/09/2026 → `50`.
- **Layout:** "FALTAM" (96 px, branco) em y 520 · número gigante (320–420 px, rosa neon `#FF2E88` sobre preto `#0B0B12`, contraste 5,60) em y 640–1060 · "DIAS PRO GTA 6" (96 px) em y 1100 · "19/11/2026" (60 px, branco 80%) em y 1230 · imagem oficial de fundo escurecida 60% · crédito "Imagem: Rockstar Games".
- **Quando falta 1 dia:** "FALTA 1 DIA" (singular). **No dia 19/11:** "É HOJE!" — não "FALTAM 0 DIAS".

#### Passo 47 — Story de Futebol (placar, resultado, gol)
- **Regra de ouro:** só foto **oficial** publicada pelo clube, pela CBF ou pela liga, com crédito (`Foto: @clube` ou `Foto: Fulano/Clube`). **Nunca** quadro de transmissão de TV.
- **Layout de placar:** escudos pequenos só para identificar (≤ 160 px, sem deformar) · placar grande 200–260 px em amarelo `#FFD400` sobre verde-escuro `#0B3D2E` · autor do gol e minuto em 48 px · crédito embaixo.
- Em **P0** (gol, fim de jogo), a meta é story pronto em até 5 minutos. Use o molde pronto; não invente layout na hora.

#### Passo 48 — Conferir tamanho, contraste e ortografia do story
- **Rode** o mesmo do passo 23 trocando `capa.jpg` por `story.jpg`:
```powershell
Add-Type -AssemblyName System.Drawing
$img = [System.Drawing.Image]::FromFile("$item\story.jpg"); "$($img.Width) x $($img.Height)"; $img.Dispose()
```
- **Deve aparecer:** `1080 x 1920`.
- **Confira** o contraste (passo 24) e a ortografia (passo 27).

### Parte F — Pin do Pinterest (só Receitas, Carros e Destinos)

#### Passo 49 — Confirmar que o pin é devido
- **Rode:**
```powershell
$pedido.canal
$pedido.redes -contains "pinterest"
```
- **Deve aparecer:** `receitas`, `carros` ou `destinos` e `True`. Se o canal for `gta`, `futebol` ou `filmes`, **não faça pin** (esses canais não estão no Pinterest) — se o pedido pedir, anote em `observacoes` e avise o Curador.

#### Passo 50 — Montar o pin
- **Layout (1000 x 1500):**

| Elemento | Posição | Tamanho |
|---|---|---|
| Título | terço de cima, y 100–600, x 60–940 | 80–110 px, até 3 linhas |
| Subtítulo / promessa ("em 10 minutos", "gastando pouco", "abaixo de R$ 80 mil") | logo abaixo do título | 44–52 px |
| Foto principal | y 600–1340 (ou fundo inteiro com degradê) | — |
| Faixa do canal com @ | y 1360–1440, x 60–780 (fugindo do canto da lente) | 30 px |
| Rodapé "Valores aproximados…" (se tiver valor) | acima da faixa do canal | 28–30 px |
| Crédito da foto | junto da faixa, à esquerda | 28 px |

- Exemplos:
  - **Receitas:** "Bolo de cenoura de liquidificador" / "com cobertura que endurece" / foto da fatia / "Custo aprox. R$ 18 · Valores aproximados, pesquisados em set/2026. Podem mudar."
  - **Carros:** "5 carros mais baratos de 2026" / "a partir de R$ 79 mil" / foto de divulgação / rodapé de valores / "Imagem: divulgação/montadoras".
  - **Destinos:** "Gramado gastando pouco" / "roteiro de 3 dias" / foto / rodapé de valores (se citar diária ou passeio).
- **Rode** o `estaticos.py` (parâmetros do `--help`) com saída `$item\pin.jpg`.

#### Passo 51 — Conferir o pin
- **Rode:**
```powershell
Add-Type -AssemblyName System.Drawing
$img = [System.Drawing.Image]::FromFile("$item\pin.jpg"); "$($img.Width) x $($img.Height)"; $img.Dispose()
ffmpeg -hide_banner -loglevel error -y -i "$item\pin.jpg" -vf "drawbox=x=0:y=0:w=60:h=1500:color=red@0.4:t=fill,drawbox=x=940:y=0:w=60:h=1500:color=red@0.4:t=fill,drawbox=x=60:y=0:w=880:h=60:color=red@0.4:t=fill,drawbox=x=60:y=1440:w=880:h=60:color=red@0.4:t=fill,drawbox=x=800:y=1340:w=200:h=160:color=orange@0.5:t=fill,drawbox=x=800:y=0:w=200:h=160:color=orange@0.5:t=fill" -q:v 3 "$item\conferencia_pin.jpg"
Invoke-Item "$item\conferencia_pin.jpg"
```
- **Deve aparecer:** `1000 x 1500`; nenhum texto no vermelho nem nos cantos laranja.

#### Passo 52 — Conferir o pin "em miniatura"
O Pinterest mostra o pin em colunas estreitas (~236 px de largura no computador).
- **Rode:**
```powershell
ffmpeg -hide_banner -loglevel error -y -i "$item\pin.jpg" -vf "scale=236:354" "$item\conferencia_pin_mini.jpg"
Invoke-Item "$item\conferencia_pin_mini.jpg"
```
- **Confira:** o título ainda dá para ler nesse tamanho? Se não, aumente a letra ou encurte o título (pedindo ao Redator).

### Parte G — Entregar

#### Passo 53 — Gravar o `design.json`
- **Rode** (exemplo para capa de reel; ajuste os números com o que você mediu nos passos 23–26):
```powershell
$d = [ordered]@{
  esquema = "hp.design/1"
  item    = (Split-Path $item -Leaf)
  canal   = $pedido.canal
  tipo    = $pedido.tipo
  status  = "pronto"
  versao  = 1
  pecas   = @(
    [ordered]@{ arquivo="capa.jpg"; papel="capa_reel"; largura=1080; altura=1920
                kb=[int]((Get-Item "$item\capa.jpg").Length/1KB)
                quadro_origem=[ordered]@{ arquivo="final.mp4"; segundo=$seg }
                titulo=$post.titulo_capa; cor_texto="#FFFFFF"; cor_caixa="#7B2CBF"; contraste=7.11
                safe_zone_ok=$true; dentro_grade_3x4=$true; credito=$null; valores_aproximados="nao_se_aplica" }
  )
  checagens = [ordered]@{ dimensoes=$true; peso=$true; formato_jpg_srgb=$true; safe_zone=$true
                          contraste_minimo=7.11; ortografia_conferida=$true; credito="nao_se_aplica"
                          valores_aproximados="nao_se_aplica"; numeracao_laminas="nao_se_aplica" }
  ferramenta = "scripts\posts_canais.py"
  feito_por  = "designer-claude"
  modo       = "valendo"
  feito_em   = (Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz")
  observacoes = ""
}
$d | ConvertTo-Json -Depth 6 | Set-Content "$item\design.json" -Encoding UTF8
Get-Content "$item\design.json" -Encoding UTF8 | Select-Object -First 12
```
- **Confira:** o `-Depth 6` é obrigatório (sem ele o PowerShell 5.1 corta a lista `pecas` e grava lixo — erro E14).
- **Deve aparecer:** o começo do JSON com `"status": "pronto"`. (O PowerShell 5.1 pode trocar alguns sinais, como o apóstrofo `'`, por códigos do tipo `\u0027` dentro do JSON, e grava o arquivo com uma marca invisível no começo (BOM); está certo, o app lê normal.)

#### Passo 54 — Anotar no `historico.log`
- **Rode:**
```powershell
$linha = "{0} [designer] capa.jpg v1 pronta (1080x1920, {1} KB, contraste 7,11, safe zone ok) - designer-claude" -f (Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz"), [int]((Get-Item "$item\capa.jpg").Length/1KB)
Add-Content -Path "$item\historico.log" -Value $linha -Encoding UTF8
Get-Content "$item\historico.log" -Encoding UTF8 -Tail 3
```
- **Deve aparecer:** as 3 últimas linhas do histórico, a última sendo a sua.

#### Passo 55 — Liberar para a revisão
- **Com o app ligado (a criar — etapa 3):** não mova nada. O app move a pasta de `04_edicao` para `05_revisao` sozinho quando encontrar, ao mesmo tempo: `final.mp4` (se for reel), `post.json` com `"status": "pronto"` e `design.json` com `"status": "pronto"`.
- **Sem o app (hoje):** confira os 3 e mova à mão:
```powershell
(Test-Path "$item\post.json") -and (Test-Path "$item\design.json")
Move-Item $item "$E\05_revisao\"
Get-ChildItem "$E\05_revisao" -Directory | Select-Object Name
```
- **Deve aparecer:** `True` no primeiro comando e o item listado em `05_revisao`.
- **Nunca** mova um item em que o Editor ou o Redator ainda estão trabalhando (sem `final.mp4` ou sem `post.json` pronto).

### Parte H — Quando o Revisor devolve

#### Passo 56 — Ler o que o Revisor pediu
- **Rode** (usa o `$ref` do passo 12):
```powershell
$r = Get-Content $ref.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
$r.classe; $r.media; $r.criterio_menor; $r.motivo
$r.o_que_refazer | Where-Object { $_.cargo -eq "designer" } | Format-List
$r.voltas
```
- **Confira:** `o_que_refazer` diz **exatamente** que peça refazer e como (ex.: `peca: "capa.jpg"`, `instrucao: "título encosta na faixa de baixo; subir para y 420–1000"`). Refaça **só** as ações com `cargo: "designer"`. Se não aparecer nenhuma, não há nada para você nesta volta: não mexa nas peças.
- **Deve aparecer:** por exemplo `Médio`, `6.6`, `capa`, o motivo, a lista e `1` (primeira volta).
- **Atenção:** se `voltas` já é `2`, esta é a **última chance** — na próxima reprovação o item é descartado (manual 09). Capriche.

#### Passo 57 — Guardar a versão antiga e refazer só o pedido
- **Rode** (exemplo para a capa):
```powershell
Rename-Item "$item\capa.jpg" "capa_v1.jpg"
```
- **Depois:** refaça a peça seguindo os passos da parte correspondente (C, D, E ou F), **incluindo todas as conferências** (tamanho, contraste, zona segura, ortografia).
- **Deve aparecer:** `capa_v1.jpg` (antiga) e `capa.jpg` (nova) na pasta. O Publicador só usa `capa.jpg`.

#### Passo 58 — Atualizar o recibo e o histórico
- **Rode:**
```powershell
$d = Get-Content "$item\design.json" -Raw -Encoding UTF8 | ConvertFrom-Json
$d.versao = [int]$d.versao + 1
$d.status = "pronto"
$d.feito_em = (Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz")
$d.observacoes = "v$($d.versao): " + $r.motivo
$d | ConvertTo-Json -Depth 6 | Set-Content "$item\design.json" -Encoding UTF8
Add-Content "$item\historico.log" ("{0} [designer] refeito v{1} a pedido do revisor: {2}" -f (Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz"), $d.versao, $r.criterio_menor) -Encoding UTF8
```
- **Deve aparecer:** nenhum erro. Com o app ligado, ele devolve o item para `05_revisao` sozinho; sem o app, faça o passo 55.
- **Não apague** o `refazer.json` e **não renomeie**: o app renomeia para `refazer_volta1.json` (ou `_volta2`) quando o item volta à revisão, para o Revisor saber quantas voltas já houve. (Os manuais 04 e 05 mandam o Legendador e o Tradutor renomear para `refazer_1_feito.json`; os dois nomes valem e o Revisor conta os dois.)

---

## 4. Regras que nunca se quebram

Cada regra tem o **porquê**. Quebrar qualquer uma delas = peça reprovada, mesmo que esteja linda.

**4.1 Nada quebra o que funciona.** As cores, fontes e moldes que já estão gravados no `scripts\estaticos.py` e no `scripts\posts_canais.py` são os que estão no ar. Molde novo ou mudança de identidade só entra depois de **7 dias em modo sombra** com paridade comprovada (a ferramenta `qa_paridade` — a criar, módulo D — compara número e ordem de lâminas, tamanho e diferença visual quadro a quadro). O Designer nunca edita esses scripts por conta própria; pede por ticket (`scripts\tickets.py`, área de design).

**4.2 Medida exata.** Capa e story 1080x1920; lâmina, feed e Threads 1080x1350; pin 1000x1500. Sempre **JPG em sRGB**. Nada de PNG (a API do Instagram recusa), nada de 1079 px, nada de "quase 4:5".

**4.3 Texto dentro da zona segura.** Todo texto importante dentro das faixas da tabela 2.8.5. A capa, além disso, com todo texto dentro do corte 3:4 (y 240–1680).

**4.4 Crédito sempre.** Toda foto, quadro ou imagem que não foi produzida pela HP leva crédito visível ("Foto: @perfil", "Imagem: Rockstar Games", "Imagem: divulgação/Netflix", "Vídeo: @criador"). Foto própria leva "Foto: @<canal>". Sem crédito, não sai.

**4.5 Só imagem permitida.**
- **GTA 6:** só material oficial da Rockstar/Take-Two (trailers, capturas, artes, site oficial) ou captura própria quando o jogo sair. **Nada de vazamento** — nem imagem, nem print de fórum, nem "suposto vazamento", nem desenho baseado em vazamento.
- **Futebol:** só foto/vídeo **oficial** publicado pelo clube, pela CBF ou pela liga. **Nunca imagem de transmissão de TV** (quadro com logo de emissora, placar de emissora, câmera de transmissão).
- **Filmes e Séries:** pôster e imagens de divulgação oficiais do estúdio/plataforma, com crédito. Arte de fã só com autorização do autor e crédito.
- **Receitas, Carros, Destinos:** foto própria, foto de divulgação oficial (montadora, órgão de turismo) ou banco de imagem com licença que permite uso comercial — sempre com crédito.
- **Flow Games:** nada. Nem logo, nem imagem, nem pessoa associada, nem menção.
- Nada de marca d'água, @ ou logo de outro perfil na arte.

**4.6 Valor citado leva "Valores aproximados…".** Toda peça que mostra preço, custo, salário, valor de transferência, tabela FIPE, diária, passagem ou qualquer número em dinheiro leva o rodapé **"Valores aproximados, pesquisados em <mês/ano>. Podem mudar."** (ou o texto-padrão que o `estaticos.py` já usa, desde que comece com "Valores aproximados"), legível (28–30 px, contraste ≥ 4,5), na mesma lâmina/peça do valor.

**4.7 Só fontes de licença livre.** Anton, Bebas Neue, Montserrat e Inter (Google Fonts, licença OFL). Nenhuma fonte baixada de site desconhecido, nenhuma fonte "pirata" de marca.

**4.8 Contraste mínimo 4,5 : 1** entre texto e fundo imediato (caixa). Título gigante (≥ 150 px) aceita 3,0 : 1. Medido pela fórmula do passo 24, não "no olho".

**4.9 Nunca texto solto em cima de foto.** Sempre caixa sólida (85–100% de opacidade) ou degradê escuro (até 70%) atrás do texto, mais a sombra padrão.

**4.10 O Designer não escreve nem corta título.** O texto é do Redator (`post.json`). Se não cabe, o Designer devolve pedindo outro (passo 17). Trocar uma palavra "porque ficou melhor" é proibido — o Revisor compara a capa com o `post.json` letra por letra.

**4.11 Nunca apagar versão anterior.** Refazer = renomear a antiga para `_v1`, `_v2` e gerar a nova com o nome original.

**4.12 Trabalho pesado: 1 por vez e nunca das 18h às 22h30.** Lote de artes (mais de 10 imagens de uma vez) só fora dessa janela e sem `pesado.lock` de outro trabalho. Uma capa ou um story avulso (segundos de processamento) é leve e pode sair a qualquer hora — por isso o Futebol consegue ter story de gol às 21h47.

**4.13 Segredos não são assunto do Designer.** Nunca abrir, ler, copiar ou mostrar nada de `H:\HypadoLocal\segredos\`. Nenhuma ferramenta de arte precisa de token.

**4.14 O Designer não publica e não manda mensagem.** Nada de postar "só para testar", nada de mandar prévia no WhatsApp (o WhatsApp só serve para as 3 mensagens oficiais: resumo do dia anterior, aviso "no ar" e resumo de sábado).

**4.15 Nada de clickbait visual mentiroso.** Seta apontando para algo que não existe, círculo vermelho em "detalhe secreto" que não é segredo, "ADIADO!" quando não foi adiado, rosto de choque colado que não está no vídeo, placar que não aconteceu. A capa promete **só** o que o vídeo/carrossel entrega.

**4.16 Respeito a pessoas e marcas.** Nunca deformar escudo, logo ou rosto; nunca montagem que humilhe jogador, torcida, ator ou qualquer pessoa real; nunca usar logo de marca de um jeito que pareça patrocínio (a HP não tem publi hoje; afiliados é assunto futuro).

**4.17 Imagem gerada por IA não pode parecer foto real** de pessoa, jogo, partida, carro ou lugar (engana o público e derruba a confiança). Se algum dia for usada como ilustração, leva o selo "Ilustração" visível.

**4.18 Lâminas numeradas, na ordem, sem pular.** "1/7" até "7/7", mesmo lugar em todas, e os arquivos `lamina_01.jpg`… com dois dígitos.

**4.19 Uma peça por arquivo, com o nome padrão.** `capa.jpg`, `lamina_NN.jpg`, `story.jpg`, `pin.jpg`, `threads.jpg`. O Publicador procura exatamente esses nomes; qualquer outro nome é ignorado.

**4.20 Não mexer no que está em andamento no PC.** A etapa 4 (Facebook e YouTube pela API), a redução de arquivos do painel público e a auditoria da API do YouTube estão sendo feitas por outra sessão. O Designer não toca em nada disso.

---

## 5. Critérios de qualidade com nota

Cada peça recebe nota de 0 a 10 em cada critério. A nota do Designer no item é a **média** dos critérios que se aplicam. É essa média (junto com a olhada nos quadros) que o Revisor usa no critério **"Capa"** (reel) ou **"Arte"** (estático) do manual 09. Meta: **média ≥ 9** em todos os itens.

| # | Critério | Como medir | Nota 10 | Nota 7 | Nota 5 | Nota 0 |
|---|---|---|---|---|---|---|
| D1 | **Medida e formato** | passo 23/37/48/51 (System.Drawing) + extensão do arquivo | tamanho exato, JPG sRGB, nome padrão | tamanho exato, mas nome fora do padrão corrigido na hora | proporção certa com tamanho diferente (ex.: 720x1280) | proporção errada, PNG, ou arquivo corrompido |
| D2 | **Zona segura** | passo 25/40/44/51 (drawbox) | 100% do texto dentro, com folga ≥ 20 px | texto encosta na borda da zona sem entrar no vermelho | até 1 elemento secundário (crédito, @) dentro do vermelho | título ou número principal dentro do vermelho (coberto pelo app da rede) |
| D3 | **Contraste e legibilidade** | passo 24 (fórmula) + passo 26 (grade 360x480) | contraste ≥ 7 e lido em 1 s na miniatura | contraste 4,5–6,9 e lido na miniatura | contraste 3,0–4,4 em texto não gigante | contraste < 3 ou ilegível na miniatura |
| D4 | **Ortografia da arte** | passo 27 (leitura em voz alta, letra por letra, contra o `post.json`/`pedido.json`) | 0 erro, texto idêntico | 1 vírgula faltando em texto corrido | 1 acento errado em texto corrido | qualquer erro no título, em nome próprio, em número ou em placar |
| D5 | **Identidade do canal** | comparar com a tabela 2.9 (cores, fonte, selo, caixa) | cores, fontes, selo e caixa exatamente do molde | 1 detalhe fora (ex.: selo 10 px maior) | cor ou fonte de outro canal | parece de outro perfil / sem identidade nenhuma |
| D6 | **Hierarquia (o olho lê na ordem certa)** | olhar a miniatura por 1 s e dizer o que leu primeiro | título → herói da imagem → resto | título e imagem disputam atenção | o olho vai primeiro para um detalhe secundário | não dá para saber qual é o assunto |
| D7 | **Escolha da imagem/quadro** | passo 19 (nítido, herói, sem legenda) | nítida, herói claro, expressão forte, sem legenda por baixo | nítida mas sem emoção | levemente borrada ou com legenda aparecendo por baixo do título | borrada, preta, transição, ou imagem proibida |
| D8 | **Crédito** | passo 33/41 | 100% das imagens de terceiro com crédito correto e legível | crédito presente, mas pequeno demais (< 28 px) | crédito com @ errado | falta crédito em qualquer imagem de terceiro (**eliminatório**) |
| D9 | **Valores aproximados** | passo 34/41 | toda peça com valor tem o rodapé legível; peça sem valor não tem rodapé à toa | rodapé presente mas colado na borda | rodapé com texto diferente do padrão | valor sem rodapé (**eliminatório**) |
| D10 | **Numeração e ordem (carrossel)** | passo 36/38/39 | "n/N" em todas, ordem certa, arquivos `_01`… | numeração em lugar diferente em 1 lâmina | numeração faltando em 1 lâmina | ordem errada, lâmina faltando ou repetida |
| D11 | **Regras de conteúdo** | passo 28 | nenhuma violação | — | — | qualquer violação da regra 4.5 ou 4.15 (**eliminatório** — descarta a peça) |
| D12 | **Peso do arquivo** | passo 23/37 | capa 300–700 KB; lâmina ≤ 1,5 MB | capa 700–1.000 KB | capa > 1 MB ou lâmina 1,5–8 MB | acima do limite da rede (8 MB IG/Threads, 20 MB Pinterest) |
| D13 | **Grade 3:4 (só capa)** | passo 25 (retângulo amarelo) e 26 | todo o texto e o herói dentro do 3:4 | texto dentro, herói cortado pela metade | 1 linha do título cortada na grade | título some na grade |
| D14 | **Coerência com o conteúdo** | comparar capa/lâminas com o vídeo, o `post.json` e o pedido | promete exatamente o que entrega | promete um pouco mais do que entrega (exagero leve) | imagem de um assunto e título de outro | promessa falsa (clickbait mentiroso — **eliminatório**) |
| D15 | **Recibo e histórico** | abrir `design.json` e `historico.log` | `design.json` completo e correto + linha no histórico | `design.json` com 1 campo faltando | sem linha no histórico | sem `design.json` (o app não sabe que acabou) |

**Critérios eliminatórios** (D8, D9, D11, D14 com nota 0): a peça não sai, qualquer que seja a média. O Revisor trata como trava (manual 09, seção 5).

**Como calcular a nota do Designer no item:**
1. Dê a nota de cada critério que se aplica (D10 só em carrossel; D13 só em capa).
2. Some e divida pela quantidade de critérios que se aplicaram.
3. Exemplo (capa do GTA): D1 10, D2 10, D3 10, D4 10, D5 10, D6 9, D7 9, D8 não se aplica (sem imagem de terceiro fora do vídeo), D9 não se aplica, D10 não se aplica (só carrossel), D11 10, D12 10, D13 10, D14 10, D15 10 → soma 118 ÷ 12 critérios = **9,83 (Excelente)**.

---

## 6. Erros comuns e o que fazer

| Código | Sintoma (o que você vê) | Causa | Solução |
|---|---|---|---|
| E01 | `& $py --version` diz "não é reconhecido" ou "não foi possível encontrar o caminho" | o atalho `$py` não foi criado (janela nova) ou o Python não está nesse lugar | rode de novo o passo 2; se continuar, rode `Get-ChildItem "$env:LOCALAPPDATA\Programs\Python"` e ajuste o caminho do `$py` para a pasta que aparecer |
| E02 | "ffmpeg não é reconhecido como nome de cmdlet" | ffmpeg fora do PATH | procure: `Get-ChildItem H:\ -Filter ffmpeg.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1 FullName`; use o caminho completo entre aspas com `&` na frente (`& "H:\...\ffmpeg.exe" ...`); abra ticket para pôr no PATH |
| E03 | `estaticos.py`/`posts_canais.py` dá erro vermelho (`Traceback`) | parâmetro errado, arquivo de entrada faltando ou biblioteca faltando | leia a **última** linha do erro: `FileNotFoundError` = caminho errado (confira aspas em caminho com espaço); `ModuleNotFoundError: No module named 'PIL'` = falta biblioteca → `& $py -m pip install pillow`; outros = ticket com o erro copiado (sem dados pessoais) |
| E04 | letra saiu em Arial/Times no lugar da fonte do canal | fonte não instalada para o usuário que roda o script | instale a fonte (clique direito no `.ttf` → **Instalar para todos os usuários**); rode o passo 6 de novo; refaça a peça |
| E05 | acentos aparecem como `Ã©`, `Ã§` | leitura sem `-Encoding UTF8` no PowerShell 5.1 | sempre `Get-Content ... -Raw -Encoding UTF8`; se foi a **arte** que saiu com acento torto, o erro está no texto que foi passado para a ferramenta — gere de novo lendo o JSON com UTF8 |
| E06 | `ConvertFrom-Json : Primitivo JSON inválido` | `pedido.json`/`post.json` com erro (vírgula sobrando, aspas faltando) | não conserte à mão o arquivo de outro cargo: grave `design.json` com status `travado` e observação "pedido.json inválido"; com o app, o item vai para `99_erros` |
| E07 | passo 23 mostra `1080 x 1921` ou `1079 x 1920` | arredondamento de escala na ferramenta | gere de novo; se persistir, corrija com `ffmpeg -y -i capa.jpg -vf "scale=1080:1920" -q:v 2 capa_ok.jpg` e renomeie; abra ticket da ferramenta |
| E08 | capa com mais de 1.000 KB | qualidade JPG 100 ou foto com muito detalhe/ruído | recomprima: `ffmpeg -y -i capa.jpg -q:v 3 capa_leve.jpg` (o `-q:v` vai de 2 = melhor a 31 = pior; 3–4 fica ótimo) e renomeie |
| E09 | Publicador falha com erro de formato de imagem | peça salva como PNG (mesmo com nome `.jpg`) ou em CMYK | converta: `ffmpeg -y -i capa.jpg -pix_fmt yuvj420p -q:v 2 capa_ok.jpg`; renomeie; confira D1 |
| E10 | título cortado na grade do perfil | título fora do corte 3:4 (acima de y 240 ou abaixo de 1680) | refaça com o título na faixa y 420–1000 (passo 25, retângulo verde) |
| E11 | Revisor diz "título atrás dos botões" | texto em x > 930 (reel) ou y > 1500 | refaça dentro da zona; use o drawbox antes de entregar |
| E12 | número de lâminas geradas ≠ pedidas | lâmina com texto vazio pulada pela ferramenta, ou arquivo antigo sobrando | confira o `pedido.json`; apague só as lâminas **desta** geração e gere de novo; nunca "complete" com lâmina repetida |
| E13 | carrossel sai fora de ordem | arquivos `lamina_1.jpg … lamina_10.jpg` (sem zero à esquerda) | renomeie para `lamina_01.jpg …` (passo 35) |
| E14 | `design.json` com `"pecas": "System.Collections..."` | `ConvertTo-Json` sem `-Depth` no PowerShell 5.1 (padrão corta no nível 2) | sempre `ConvertTo-Json -Depth 6` |
| E15 | "o processo não pode acessar o arquivo porque ele está sendo usado" | imagem aberta pelo `System.Drawing` sem `Dispose()`, ou aberta no visualizador | rode `$img.Dispose()`; feche o visualizador de fotos; tente de novo |
| E16 | foto borrada/pixelada na lâmina | foto de origem pequena (< 1080 px de largura) ampliada | use a foto pequena em moldura (metade da lâmina) ou peça outra ao Curador |
| E17 | cores "lavadas" ou diferentes no celular | imagem salva em Adobe RGB/CMYK | reexporte em sRGB (o ffmpeg converte ao regravar em JPG: `ffmpeg -y -i x.jpg -q:v 2 x_srgb.jpg`); confira no celular pela prévia do painel |
| E18 | legenda do vídeo aparece por baixo do título da capa | quadro tirado num momento com legenda na tela | escolha outro segundo entre dois blocos da legenda (passo 20) |
| E19 | `Move-Item` dá "acesso negado" | algum arquivo da pasta aberto (visualizador, player) ou antivírus/sincronização segurando | feche tudo que está aberto da pasta; espere 10 s; tente de novo |
| E20 | caminho com espaço dá erro ("G:\Meu" não encontrado) | caminho sem aspas | sempre coloque caminho entre aspas: `"G:\Meu Drive\Hypado\scripts"` |
| E21 | contagem regressiva com 1 dia a mais ou a menos | conta feita com hora (não só data), ou digitada de cabeça | use o comando do passo 46 (com `.Date`); confira que o relógio do PC está em Brasília |
| E22 | figurinha da enquete não coube na caixa | caixa menor que 800 x 400 ou fora da posição padrão | refaça com a caixa em x 140–940, y 1050–1450 (passo 45) — o robô do emulador arrasta a figurinha para esse lugar |
| E23 | Revisor devolveu por "sem crédito" | lâmina com foto de terceiro sem crédito, ou crédito com o @ de outra rede | confira o `credito` do pedido; na arte, o @ é o do **Instagram** do autor (a arte é a mesma para todas as redes) |
| E24 | Revisor devolveu por "valor sem aviso" | lâmina com R$ sem rodapé | rode o passo 34 de novo — ele pega "R$", "reais", "preço", "FIPE", "custa" |
| E25 | `pesado.lock` existe e você precisa rodar lote | outro trabalho pesado rodando | espere; confira quem é o dono: `Get-Content H:\HypadoLocal\app\pesado.lock`; **nunca apague** a trava de outro trabalho (o app assume sozinho trava abandonada com mais de 3 h) |
| E26 | são 18h40 e tem lote de estáticos para amanhã | janela proibida | deixe para depois das 22h30; se é P0, faça só a peça avulsa (leve) |
| E27 | título tem 4 linhas mesmo no tamanho mínimo | título longo demais | passo 17 (pedir outro ao Redator); não diminua a letra abaixo do mínimo |
| E28 | a ferramenta gerou a arte mas não em `$item` | a ferramenta tem pasta de saída própria | copie com `Copy-Item` para a pasta do item com o nome padrão (passo 35) |
| E29 | `Invoke-Item` abre a imagem num programa pesado | associação de arquivo do Windows | tudo bem, só feche depois; ou use `explorer.exe "$item\capa.jpg"` |
| E30 | `refazer.json` pede algo que não é do Designer (ex.: "legenda fora de sincronia") | o item passou pela sua etapa, mas o problema é de outro cargo | não mexa; com o app, o `cargo_destino` do `refazer.json` já manda para o cargo certo; sem o app, avise quem faz aquele cargo |

---

## 7. O que o app faz sozinho x o que o Claude decide

A meta do Antônio é o app **o mais independente possível da IA**. O Designer é um dos cargos mais "automatizáveis": a maior parte é medida, molde e conferência — coisas que o computador faz melhor que qualquer pessoa. O Claude fica só com o **gosto**: qual quadro tem mais emoção, se a capa está atraente.

| Passo(s) | O que é | App sozinho (depois da etapa 3 e dos 7 dias de sombra) | O Claude decide | % app (meta) |
|---|---|---|---|---|
| 1–7 | preparar o PC, conferir ferramentas, trava e horário | tudo (checagem automática na partida do app; `TravaPesada` e `janela_proibida` do `hpbase`) | nada | 100% |
| 8–12 | achar o item, ler o pedido, decidir as peças | tudo (vigia da esteira, ordena P0 > P1 > P2, lê `tipo`) | nada | 100% |
| 13–14 | esperar o `post.json` e o `final.mp4` | tudo (só começa quando os dois estão prontos) | nada | 100% |
| 15–17 | medir o título, quebrar em linhas, devolver se não cabe | medir e quebrar por regra (≤ 18 caracteres/linha, sem palavra sozinha, número junto da unidade) | a palavra de destaque, quando o Redator não marcou | 90% |
| 18–21 | escolher o quadro da capa | gerar candidatos, descartar tela preta/borrão (nitidez medida), descartar quadro com legenda (pelos tempos do `legenda.srt`), sugerir os 3 melhores | escolher 1 dos 3 (emoção, "herói") | 70% (meta 85% com a regra "rosto maior + mais nítido" validada em sombra) |
| 22 | aplicar o molde e gerar a peça | tudo (`estaticos.py`/`posts_canais.py` chamados pelo trabalho `designer.capa`/`designer.carrossel` — a criar) | nada | 100% |
| 23–26 | medidas, contraste, zona segura, grade 3:4 | tudo, sem olhar a imagem: o app sabe onde desenhou cada texto, então confere as coordenadas contra a tabela 2.8.5; contraste calculado das cores do molde | nada | 100% |
| 27 | ortografia | comparar o texto passado à ferramenta com o `post.json` (igualdade exata) | nada | 100% |
| 28 | proibições | lista de palavras e fontes bloqueadas (Flow Games, "vazou", "leak", emissoras de TV), conferir crédito e rodapé de valor por regra | julgar imagem duvidosa (ex.: é quadro de TV?) | 80% |
| 30–34 | estrutura do carrossel, fotos, crédito, valores | tudo por regra (contagens, tamanho das fotos, crédito vazio, regex de valor) | nada | 100% |
| 35–42 | gerar e conferir lâminas | tudo | olhar a folha do carrossel e dizer se "conta a história" (só nos 7 dias de sombra; depois, só por amostragem de 1 em 10) | 95% |
| 43–48 | stories, enquete, contagem regressiva | tudo (contagem calculada, caixa da enquete em posição fixa) | nada | 100% |
| 49–52 | pin | tudo | nada | 100% |
| 53–55 | recibo, histórico, liberar para revisão | tudo | nada | 100% |
| 56–58 | refazer a pedido do Revisor | refazer o que o `o_que_refazer` pede quando é regra (posição, tamanho, crédito, rodapé) | refazer quando o motivo é gosto ("capa sem emoção") | 75% |
| **Total ponderado** | | | | **≈ 90%** (hoje, sem o app: 0%) |

**Como o app fica igual ao Claude (modo sombra de 7 dias):** durante 7 dias, o app gera a peça em paralelo (com `modo: "sombra"` e nome `capa_sombra.jpg`) e o `qa_paridade` (a criar) compara com a peça do Claude: tamanho, posição da caixa de título (diferença ≤ 20 px), cores (iguais), texto (idêntico) e diferença visual (SSIM ≥ 0,90 quando o quadro escolhido é o mesmo). Só depois de 7 dias seguidos com **nota do Revisor ≥ 9 nas peças do app** e **0 violação**, o app assume.

---

## 8. Ferramentas existentes que já fazem cada passo

| Passo | Ferramenta | Já existe? | Onde | Para quê |
|---|---|---|---|---|
| 3 | Python 3.12 | sim | `%LOCALAPPDATA%\Programs\Python\Python312\python.exe` | roda os scripts |
| 4, 18, 21, 25–26, 38, 40, 44, 51–52 | ffmpeg | sim | no PATH do PC | tirar quadro, fazer folha de quadros, desenhar zona segura, recomprimir |
| 5, 22, 35, 43, 45, 50 | `scripts\estaticos.py` | sim | `G:\Meu Drive\Hypado\scripts\` | artes estáticas (carrossel, story, pin, arte do story das 16h) e o `lotes\<dia>_estaticos.json` |
| 5, 22 | `scripts\posts_canais.py` | sim | `G:\Meu Drive\Hypado\scripts\` | artes dos posts dos canais (moldes por canal) |
| 47 | `scripts\posts_futebol.py` (`legenda_video`) | sim | `G:\Meu Drive\Hypado\scripts\` | caixa de legenda do Futebol usada nos reels (o Designer só mantém o visual consistente com ela) |
| 23, 32, 37, 48, 51 | PowerShell + `System.Drawing` | sim (vem com o Windows) | — | medir largura/altura sem instalar nada |
| 24 | fórmula de contraste (linha de Python do passo 24) | sim (é só um comando) | — | medir contraste |
| 17, 22 | `scripts\tickets.py` | sim | `G:\Meu Drive\Hypado\scripts\` | abrir ticket em `08 Empresa\tickets\<area>\novo` quando uma ferramenta falha |
| 43, 45 | `scripts\story_clicavel.py` + emulador (`H:\HypadoLocal\android\`: `ligar_emulador.ps1`, `ui.py`, `digitar.py`) | sim | — | fila do story de divulgação e base para o robô da enquete |
| 45 | `story_post.py` | **(a criar — módulo F)** | `scripts\` | pegar a arte do dia, subir no emulador, pôr a enquete na caixa |
| — | `scripts\publicador_meta.py` | sim | `G:\Meu Drive\Hypado\scripts\` | usa `capa.jpg`/lâminas na hora de publicar no Instagram e Threads (o Designer só precisa entregar no nome e formato certos) |
| — | `scripts\painel_local.py` | sim | `G:\Meu Drive\Hypado\scripts\` | fila local do painel (onde aparece a prévia) |
| 8–14, 53–55 | esteira de pastas (vigia que move os itens) | **(a criar — etapa 3)** | `app\hp_studio_nuvem\esteira\` | achar item, esperar `post.json`, mover para `05_revisao` |
| 18–28 | trabalho `designer.capa` (quadros candidatos, nitidez, molde, conferência por coordenadas) | **(a criar — etapa 3)** | `app\hp_studio_nuvem\esteira\` | fazer a capa sozinho |
| 30–42 | trabalho `designer.carrossel` | **(a criar — etapa 3)** | `app\hp_studio_nuvem\esteira\` | lâminas + conferências |
| 23–26, 37, 40 | `checar_arte` (medidas, zona segura, contraste, peso, crédito, rodapé) | **(a criar — etapa 3)** | `app\hp_studio_nuvem\esteira\` | todas as conferências do Designer num comando só, gravando o `design.json` |
| paridade | `qa_paridade` | **(a criar — módulo D)** | `app\hp_studio_nuvem\qa_paridade\` | comparar peça do app x peça do Claude nos 7 dias de sombra (número e ordem de lâminas, SSIM) |
| 47 | `reel_futebol.py` (cartão de 2 s, modos gol/notícia/debate…) | **(a criar — módulo G)** | `scripts\` | usa os moldes visuais do Futebol definidos aqui |

---

## 9. Testes de aceitação

O cargo de Designer (feito pelo app) só é aceito quando **todos** os testes abaixo passam. Cada teste diz o número exato que tem que dar.

| # | Teste | Como rodar | Passa se |
|---|---|---|---|
| T01 | Medida das capas | gerar 20 capas (pelo menos 3 de cada canal) e medir (passo 23) | 20 de 20 com `1080 x 1920`, JPG |
| T02 | Medida das lâminas | gerar 6 carrosséis (1 por canal, 7 lâminas = 42 lâminas) | 42 de 42 com `1080 x 1350` |
| T03 | Medida do pin | gerar 3 pins (Receitas, Carros, Destinos) | 3 de 3 com `1000 x 1500` |
| T04 | Pin só onde pode | pedir pin para GTA, Futebol e Filmes | 0 pins gerados nesses 3 canais (e observação registrada) |
| T05 | Zona segura | conferir as 20 capas + 42 lâminas + 6 stories + 3 pins pelas coordenadas | 71 de 71 com 100% do texto dentro da zona |
| T06 | Grade 3:4 | conferir as 20 capas | 20 de 20 com todo o texto entre y 240 e y 1680 |
| T07 | Contraste | calcular o contraste de todas as combinações usadas | 100% ≥ 4,5 (títulos ≥ 150 px: ≥ 3,0) |
| T08 | Proibidas | tentar gerar branco sobre turquesa `#00A6C8` e branco sobre amarelo `#FFD400` | o app recusa as 2 (contraste 2,88 e 1,43) |
| T09 | Ortografia | comparar o texto das 20 capas com o `titulo_capa` | 20 de 20 idênticos, caractere por caractere |
| T10 | Crédito | 10 carrosséis com foto de terceiro | 100% das lâminas com foto têm crédito; 1 pedido sem crédito de propósito → item fica `travado` |
| T11 | Valores aproximados | 5 peças com valor (Receitas, Carros, Destinos, Futebol com valor de contratação, GTA com preço do jogo) | 5 de 5 com rodapé "Valores aproximados…"; 5 peças sem valor → 0 rodapés |
| T12 | Numeração | 6 carrosséis | 100% das lâminas com "n/N" certo; arquivos `lamina_01…` sem pular |
| T13 | Contagem regressiva | gerar o story para 30/09/2026, 18/11/2026 e 19/11/2026 | "FALTAM 50 DIAS", "FALTA 1 DIA", "É HOJE!" |
| T14 | Caixa da enquete | gerar o story das 16h do GTA | caixa exatamente em x 140–940, y 1050–1450; arte listada em `lotes\<dia>_estaticos.json` |
| T15 | Peso | as 20 capas | 20 de 20 entre 200 e 1.000 KB |
| T16 | Título grande demais | pedir capa com título de 41 caracteres | o app não gera; grava `design.json` com `"status": "travado"` e a observação |
| T17 | Tempo | 20 capas e 6 carrosséis pelo app | capa ≤ 20 s cada; carrossel de 7 lâminas ≤ 60 s |
| T18 | Horário e trava | pedir lote de 15 artes às 18h30 e com `pesado.lock` de outro dono | o lote não roda nos 2 casos; capa avulsa às 18h30 roda |
| T19 | Recibo | todos os itens dos testes | 100% com `design.json` válido (o app lê sem erro) e 1 linha no `historico.log` |
| T20 | Paridade (modo sombra) | 7 dias seguidos, todas as peças do dia feitas em paralelo pelo app e pelo Claude | nota do Revisor nas peças do app com média ≥ 9 em cada um dos 7 dias; 0 violação eliminatória; posição do título com diferença ≤ 20 px em ≥ 95% das capas |
| T21 | Volta do Revisor | simular `refazer.json` pedindo "subir título para a faixa 420–1000" | o app gera `capa.jpg` nova, guarda `capa_v1.jpg`, `design.json` com `versao: 2`, e não mexe em nenhuma outra peça |
| T22 | Formato aceito pela API | enviar 5 capas e 1 carrossel pelo `publicador_meta.py` em modo simular | 0 erro de formato de imagem |

---

## 10. Glossário

| Palavra | O que quer dizer |
|---|---|
| **Capa** | a imagem que aparece na grade do perfil e antes do vídeo começar |
| **Lâmina** | cada imagem de um carrossel |
| **Carrossel** | post com várias imagens que a pessoa arrasta para o lado |
| **Story** | publicação vertical que some em 24 h (pode ir para um destaque) |
| **Destaque** | coleção de stories fixada no perfil (ex.: "Enquetes") |
| **Pin** | a "publicação" do Pinterest |
| **Zona segura** | parte da imagem que nenhum botão ou texto da rede cobre |
| **Grade / corte 3:4** | a vitrine de capas do perfil, que mostra só o miolo da capa |
| **Px (pixel)** | cada pontinho da imagem; 1080 x 1920 = 1080 de largura por 1920 de altura |
| **Proporção 9:16, 4:5, 2:3** | formato da imagem: vertical de celular, quase quadrado em pé, vertical do Pinterest |
| **Contraste** | quanto o texto se destaca do fundo (de 1 a 21; mínimo 4,5) |
| **sRGB** | o "idioma de cores" padrão da internet e dos celulares |
| **JPG** | formato de imagem leve, o único aceito pela API do Instagram para foto |
| **Molde** | o modelo de arte de cada canal (cores, fonte, lugar de cada coisa) |
| **Selo do canal** | o nome curto do canal ("GTA 6 \| HP") na arte |
| **Herói** | o elemento principal da imagem (rosto, carro, prato, paisagem) |
| **Gancho** | o que faz a pessoa parar de rolar (na capa: o título + o herói) |
| **CTA** | "chamada para ação": "salva", "comenta aí", "manda pra alguém" |
| **Crédito** | o aviso de quem é a imagem ("Foto: @perfil", "Imagem: Rockstar Games") |
| **Esteira** | as pastas numeradas por onde cada post passa, em ordem |
| **Item** | a pasta de um post na esteira |
| **P0 / P1 / P2** | prioridade: urgente/ao vivo, do dia, programado |
| **`design.json`** | o recibo do Designer, dizendo o que foi feito e medido |
| **`refazer.json`** | o bilhete do Revisor dizendo o que refazer |
| **Modo sombra** | o app faz o trabalho em paralelo, sem valer, só para comparar com o do Claude |
| **Paridade** | quando o trabalho do app fica igual ao do Claude, medido com números |
| **SSIM** | nota de 0 a 1 de quão parecidas duas imagens são (1 = iguais) |
| **Trava pesada (`pesado.lock`)** | arquivo que garante 1 trabalho pesado por vez |
| **Janela proibida** | das 18h às 22h30, quando o PC não faz trabalho pesado |
| **PowerShell** | a janela de comandos do Windows |
| **`$item`** | atalho para a pasta do item que você está trabalhando |
