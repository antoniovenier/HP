# Manual 10 — Publicador

> **Cargo:** Publicador (agendamento e publicação nas redes)
> **Empresa:** Hypado (HP) — 6 perfis: GTA 6 | HP (@hpgta6), Futebol | HP (@hp.futebol), Filmes e Séries | HP (@hp.filmes), Receitas | HP (@hp.receitas), Carros | HP (@hp.carros), Destinos | HP (@hp.destinos)
> **Versão:** 1.0 — 30/09/2026
> **Pasta deste manual no PC:** `G:\Meu Drive\Hypado\06 Projeto\app\manuais\10_publicador.md`
> **Quem vem antes:** 09 Revisor de qualidade (grava `aprovado.json`) · **Quem vem depois:** 11 Analista de resultados (lê o que foi ao ar)
> **Objetivo nº 1 da empresa:** crescer e chegar à monetização o quanto antes. O Publicador contribui com isso garantindo que **cada post certo saia na conta certa, no horário certo, uma vez só**.

---

## Como ler este manual (para quem nunca fez isso)

- Este manual foi escrito para uma pessoa **totalmente leiga**. Se você nunca publicou nada por API, tudo bem: siga os passos na ordem, sem pular.
- Cada comando para digitar aparece em um bloco cinza. Você copia **exatamente** como está e cola no **PowerShell** (a janela azul do Windows). Onde aparecer `<id>` ou `<post_id>`, troque pelo valor real, **sem** os sinais `<` e `>`.
- Marcações usadas no texto:
  - **(existe)** — a ferramenta já existe no PC e funciona. Não reescrever, só usar.
  - **(a criar)** — a ferramenta ainda não existe; o manual já descreve como ela deve se comportar. Até ela existir, o passo é feito pelo Claude do jeito descrito como "hoje".
  - **(em andamento no PC — não mexer)** — outra frente já está construindo isso. Não tocar, não "adiantar", não consertar.
  - **(conferir na página oficial)** — regra de rede social que muda com frequência (limites, tamanhos, prazos). Antes de confiar no número, olhe a página oficial da rede.
- Palavras difíceis estão explicadas no **Glossário**, no fim do manual.
- Hora sempre de **Brasília** (fuso `America/Sao_Paulo`).

### Preparação do PowerShell (faça uma vez por janela aberta)

Toda vez que abrir uma janela nova do PowerShell para trabalhar como Publicador, cole estas 5 linhas primeiro. Elas só criam "apelidos" para caminhos longos; não mudam nada no PC.

```powershell
$py      = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
$scripts = "G:\Meu Drive\Hypado\scripts"
$esteira = "H:\HypadoLocal\esteira"
$logs    = "H:\HypadoLocal\app\logs"
Set-Location $scripts
```

Para conferir se deu certo:

```powershell
& $py --version
```

Tem que aparecer `Python 3.12.x`. Se aparecer erro, o Python não está no lugar esperado: pare e abra um ticket (passo 91).

---

## 1. Objetivo do cargo

### 1.1 Em uma frase

Pegar cada item **aprovado** pelo Revisor, publicá-lo (ou agendá-lo) **em cada rede prevista no plano**, **no horário do plano**, **na conta certa**, **uma única vez**, confirmar que ele realmente está no ar, registrar o link, soltar os stories de divulgação **só depois** do post e avisar o grupo no WhatsApp que ele está "no ar".

### 1.2 O que o Publicador entrega, na prática

1. **Post no ar** em cada rede combinada: Instagram, Threads, Facebook, YouTube, TikTok e, nos canais Receitas, Carros e Destinos, também Pinterest.
2. **Prova de que está no ar:** o identificador do post na rede (`media_id`) e o link público (`permalink`) gravados no `publicado.json` da pasta do item.
3. **Zero duplicado:** se a rede demorou a responder, o Publicador **confere antes** de tentar de novo (seção 3, bloco K).
4. **Story de divulgação** (Instagram) **depois** que o post existe, e **story clicável** (o post compartilhado no story pelo app oficial, no emulador) quando o plano pedir.
5. **Pasta do item movida** de `06_agendados` para `07_postados`.
6. **Aviso "no ar"** no WhatsApp, com os links, no formato do `AVISO.md`.
7. **Registro limpo** no `historico.log` do item e no log do dia, para o Analista (manual 11) medir depois.

### 1.3 Como saber se o Publicador está indo bem (metas numéricas)

| Indicador | Meta | Como medir |
|---|---|---|
| Posts no ar no horário do plano (tolerância de ±5 min) | ≥ 95% | `publicado.json` → campo `publicado_em` comparado com `horario_plano` (o horário que veio do `pedido.json`) |
| Posts duplicados | **0** (zero absoluto) | Conferência diária na API: 2 posts com a mesma legenda na mesma conta no mesmo dia = duplicado |
| Posts na conta errada | **0** | Conferência do `conta` do `post.json` com a conta devolvida pela API |
| Itens aprovados que não foram ao ar em até 24 h sem motivo registrado | 0 | Pastas paradas em `06_agendados` há mais de 24 h sem `erro.json` |
| Story de divulgação antes do post | **0** | Horário do story > horário do post, sempre |
| Aviso "no ar" enviado com todos os links do lote | ≥ 98% | Comparar links do aviso com `07_postados` do dia |
| Tokens, senhas ou códigos aparecendo em log ou tela | **0** | Busca automática nos logs (teste T-15 da seção 9) |

### 1.4 O que o Publicador NÃO faz

- **Não escolhe** o que postar, nem em que rede, nem a hora: isso vem do **Estrategista** (manual 12) pelo plano da semana e do **Pauteiro** (manual 02) pela pauta.
- **Não edita** vídeo, capa ou legenda. Se achar erro, devolve (seção 6), não conserta "no braço".
- **Não aprova** conteúdo. Só publica o que tem `aprovado.json` do Revisor (manual 09).
- **Não mexe** em conta: não faz login, não digita senha nem código, não aceita termos, não cria conta, não troca foto de perfil, não mexe em configurações.
- **Não lê token.** O script lê o token de `H:\HypadoLocal\segredos\` sozinho, sem mostrar. Ninguém abre essa pasta para "ver se o token está lá".

### 1.5 Mapa das redes: como cada uma é publicada hoje

| Rede | Formatos que a HP usa | Como publica | Quem aperta o botão | Ferramenta | Situação |
|---|---|---|---|---|---|
| Instagram | Reels, carrossel, foto, story de divulgação | API oficial da Meta (Graph API, publicação de conteúdo) | App | `scripts\publicador_meta.py` + fila `H:\HypadoLocal\fila_api\` | **(existe)** |
| Threads | Texto, texto + imagem, texto + vídeo | API oficial do Threads | App | `scripts\publicador_meta.py` + fila `H:\HypadoLocal\fila_api\` | **(existe)** |
| Facebook (Página) | Reels, vídeo, foto | API oficial de Páginas da Meta | App | Etapa 4 do app | **(em andamento no PC — não mexer)** |
| YouTube | Shorts (e vídeo longo quando houver) | YouTube Data API (upload com agendamento) | App | Etapa 4 do app + auditoria da API do YouTube | **(em andamento no PC — não mexer)** |
| TikTok | Vídeo curto | Página oficial do TikTok (TikTok Studio) no Chrome | **Claude**, que grava `tiktok_ok.json` | Chrome + pasta do item | Hoje: Claude pelo Chrome |
| Pinterest (só Receitas, Carros, Destinos) | Pin de imagem, pin de vídeo | Hoje: página oficial do Pinterest no Chrome. Futuro: API oficial do Pinterest | **Claude** (hoje) | Chrome; `pinterest_ok.json` **(a criar)** | Hoje: Claude pelo Chrome |
| Story clicável (Instagram) | Post compartilhado no story + destaque | App oficial do Instagram dentro do emulador Android | App (robô do emulador) | fila `H:\HypadoLocal\emulador\fila_story\` + `scripts\story_clicavel.py` **(existe)** + `story_post.py` **(a criar — ticket F)** | Parcial |
| WhatsApp (aviso "no ar") | Mensagem de texto com links | WhatsApp Web em janela própria | App | fila `H:\HypadoLocal\whatsapp_fila\` + enviador local **(a criar — ticket E)** | Hoje: plantão do Claude |

> **Por que TikTok e Pinterest são pelo Chrome?** Porque a HP não tem acesso liberado à API oficial deles para publicar. A regra da empresa é: **só API oficial, o app oficial no emulador ou a página oficial**. Biblioteca "pirata" que imita o aplicativo (tipo as que simulam o protocolo do Instagram ou do WhatsApp) é **proibida**.

---

## 2. Entradas e saídas

### 2.1 Pastas que o Publicador usa

```
H:\HypadoLocal\
├── esteira\                         (a criar — etapa 3 do app)
│   ├── 05_revisao\                  ← o Revisor trabalha aqui
│   ├── 06_agendados\                ← ENTRADA do Publicador
│   │   └── P1_2026-10-06_1830_gta_rockstar-quinta\
│   │       ├── pedido.json          ← em quais redes e quando (Pauteiro, manual 02)
│   │       ├── post.json            ← texto exato de cada rede (Redator, manual 08)
│   │       ├── aprovado.json        ← sem isto, NADA sai
│   │       ├── final.mp4            ← vídeo final (Editor, manual 03)
│   │       ├── capa.jpg             ← capa (Designer, manual 07)
│   │       ├── lamina_01.jpg …      ← só em estático (carrossel, arte de feed)
│   │       ├── story.jpg · pin.jpg  ← quando houver story com arte / Pinterest
│   │       ├── legenda.srt
│   │       ├── publicado.json       ← o Publicador cria e vai completando
│   │       ├── tiktok_ok.json       ← o Claude grava depois de agendar no TikTok
│   │       ├── pinterest_ok.json    ← o Claude grava depois de agendar no Pinterest
│   │       └── historico.log        ← uma linha por acontecimento
│   ├── 07_postados\                 ← SAÍDA: pasta movida para cá quando tudo saiu
│   └── 99_erros\                    ← pasta movida para cá se não deu para publicar
├── fila_api\                        (existe) ← fila do publicador_meta.py (Instagram e Threads)
├── emulador\fila_story\             (existe) ← 1 JSON por story clicável a fazer
├── whatsapp_fila\                   (a criar — ticket E) ← 1 JSON por mensagem
├── segredos\                        (existe) ← tokens. NUNCA abrir, NUNCA imprimir
└── app\
    ├── logs\                        ← publicador_AAAA-MM-DD.log etc.
    └── pesado.lock                  ← trava do trabalho pesado (1 por vez)
```

**Nome da pasta do item** (padrão da esteira): `P<prioridade>_<AAAA-MM-DD>_<HHMM>_<canal>_<assunto-curto>`

- `P0_` = urgente / ao vivo (gol, placar, lançamento, notícia bombástica). Fura a fila: sai antes de todo mundo.
- `P1_` = do dia.
- `P2_` = programado (pode esperar o horário do plano sem pressa).
- `<AAAA-MM-DD>_<HHMM>` = data e hora **previstas** de publicação (a do plano).
- `<canal>` = `gta`, `futebol`, `filmes`, `receitas`, `carros`, `destinos`.

Exemplo: `P0_2026-10-04_1712_futebol_gol-flamengo-pedro` → urgente, 04/10/2026 às 17h12, canal Futebol.

### 2.2 Entrada 1 — `aprovado.json` (vem do Revisor, manual 09)

O Publicador **só** mexe num item se este arquivo existir **e** tiver `"veredito": "aprovado"`.

```json
{
  "item": "P1_2026-10-06_1830_gta_rockstar-quinta",
  "veredito": "aprovado",
  "media_nota": 9.2,
  "classe": "Excelente",
  "notas": {
    "gancho": 9,
    "legenda_queimada": 10,
    "audio": 9,
    "credito": 10,
    "texto_post": 9,
    "capa": 9,
    "regras_conteudo": 10
  },
  "voltas": 0,
  "revisor": "claude",
  "revisado_em": "2026-10-06T14:02:11-03:00",
  "observacoes": "Ok. Crédito do criador aparece aos 0,5 s e na legenda."
}
```

Regras de leitura:
- `veredito` diferente de `"aprovado"` → **não publica**. Se existir `refazer.json` na pasta, o item nem deveria estar em `06_agendados`: mova para `99_erros` com motivo "item sem aprovação em 06_agendados" (passo 17).
- `media_nota` abaixo de 7 com veredito "aprovado" → incoerente. **Não publica**, abre ticket (passo 91).

### 2.3 Entrada 2 — `pedido.json` (onde e quando) e `post.json` (com que texto)

O Publicador lê **dois** arquivos da pasta do item:
- o **`pedido.json`**, criado pelo Pauteiro (manual 02) a partir da vaga do plano do Estrategista (manual 12): diz **em quais redes** e **quando**;
- o **`post.json`**, escrito pelo Redator (manual 08, esquema `hp.post/1`): diz **o texto exato** de cada rede.

> **Nome curto usado neste manual:** `post_id` = **o nome da pasta do item** (igual ao campo `item` do `post.json` e ao `id` do `pedido.json`). Ex.: `P1_2026-10-06_1830_gta_rockstar-quinta`. É esse nome que vai nas filas (`fila_api`, `fila_story`, `whatsapp_fila`) e no `publicado.json`.

#### 2.3.1 O que o Publicador usa do `pedido.json`

```json
{
  "id": "P1_2026-10-06_1830_gta_rockstar-quinta",
  "canal": "gta",
  "tipo": "reel",
  "prioridade": "P1",
  "publicar_em": "2026-10-06T18:30:00-03:00",
  "redes": ["instagram", "threads", "facebook", "youtube", "tiktok"],
  "slot_id": "2026-W41-gta-ter-02",
  "formato_estrategia": "reel_noticia",
  "teste_ab": null,
  "horarios": {
    "instagram": "2026-10-06T18:30:00-03:00",
    "threads":   "2026-10-06T18:35:00-03:00",
    "facebook":  "2026-10-06T18:40:00-03:00",
    "youtube":   "2026-10-06T19:00:00-03:00",
    "tiktok":    "2026-10-06T19:10:00-03:00"
  },
  "story": { "divulgacao": true, "clicavel": true, "destaque": "Notícias" },
  "aviso_lote": "noite"
}
```

(O `pedido.json` real tem mais campos — fonte, áudio, legenda, Toque HP —, que são das etapas anteriores. Acima estão só os que o Publicador usa.)

| Campo | Para que serve | O que conferir / o que fazer se faltar |
|---|---|---|
| `id` | Nome do item | Igual ao nome da pasta e ao `item` do `post.json` |
| `canal` | Qual dos 6 canais | Igual ao `<canal>` do nome da pasta e ao `canal` do `post.json` |
| `tipo` | `reel`, `video`, `carrossel`, `story`, `threads` | Define quais arquivos de mídia têm que existir (2.3.3) |
| `prioridade` | `P0`, `P1`, `P2` | Igual ao começo do nome da pasta |
| `publicar_em` | Hora principal | Usada para **todas** as redes quando `horarios` não existe |
| `redes` | Lista de redes em que o item sai | Pinterest **só** em `receitas`, `carros`, `destinos` |
| `slot_id`, `formato_estrategia`, `teste_ab` | De qual vaga do plano o item veio, qual formato da matriz e se é teste A/B | **Só copiar** para o `publicado.json` (é assim que o Analista, manual 11, sabe o que medir). Se faltar, grava `null` e segue |
| `horarios` | Hora de cada rede (vem do plano) | **Opcional.** Sem ele, todas as redes usam `publicar_em` |
| `story` | Story de divulgação e story clicável | **Opcional.** Sem ele: `divulgacao: true` em reel e carrossel do Instagram, `clicavel: false` |
| `aviso_lote` | Em qual aviso "no ar" o item entra | **Opcional.** Sem ele: `manha` (antes das 12h), `tarde` (12h–18h), `noite` (depois das 18h); P0 → `p0` |

#### 2.3.2 O que o Publicador usa do `post.json` (esquema `hp.post/1`; exemplo completo no manual 08, seção 2.4)

Trecho de exemplo, só com os campos que o Publicador lê:

```json
{
  "esquema": "hp.post/1",
  "item": "P1_2026-10-06_1830_gta_rockstar-quinta",
  "canal": "gta",
  "conta": "@hpgta6",
  "tipo": "reel",
  "status": "pronto",
  "versao": 1,
  "credito": {
    "rotulo": "Vídeo",
    "nome": "Criador Exemplo",
    "por_rede": { "instagram": "@criadorexemplo", "facebook": "Criador Exemplo", "tiktok": "@criadorexemplo", "youtube": "@CriadorExemplo", "threads": "@criadorexemplo" }
  },
  "valores_aproximados": false,
  "texto_valores": null,
  "redes": {
    "instagram": { "texto_final": "A Rockstar mexeu no site de novo… o que você acha que vem aí na quinta? 👀\n\nVídeo: @criadorexemplo\n\n#gta6 #gtavi #rockstargames" },
    "facebook":  { "texto_final": "A Rockstar mexeu no site de novo… o que vem aí na quinta?\n\nVídeo: Criador Exemplo\n\n#gta6" },
    "tiktok":    { "texto_final": "Rockstar mexeu no site de novo 👀 o que vem na quinta? Vídeo: @criadorexemplo #gta6 #gtavi" },
    "youtube":   { "titulo": "A Rockstar mexeu no site de novo… o que vem na quinta? #gta6", "descricao": "Vídeo: @CriadorExemplo. Tudo sobre o lançamento em 19/11/2026.", "tags": ["gta 6", "gta vi", "rockstar"] },
    "threads":   { "texto_final": "A Rockstar mexeu no site de novo. O que sai na quinta? Comenta aí 👇\n\nVídeo: @criadorexemplo", "topico": "GTA 6" },
    "pinterest": null
  },
  "enquete": null,
  "aviso": { "titulo_curto": "Rockstar mexeu no site de novo" },
  "modo": "valendo"
}
```

| Campo | Para que serve | O que conferir |
|---|---|---|
| `esquema` | Versão do formato | Tem que ser `hp.post/1`. Outro valor → não publica (passo 17) |
| `item` | Nome da pasta | Igual ao nome da pasta. Diferente = `post.json` de outro item: parar |
| `canal`, `conta` | Canal e @ do Instagram/Threads/TikTok | `conta` tem que ser a do canal (tabela do passo 15) |
| `status` | Situação do texto | Tem que ser `pronto` |
| `credito.por_rede.<rede>` | Crédito do criador em cada rede | Tem que aparecer **dentro** do texto da rede (passo 18). Em conteúdo próprio pode ser a própria conta HP |
| `valores_aproximados` / `texto_valores` | Se cita valor em dinheiro | `true` → o `texto_valores` tem que estar no texto de cada rede (passo 19) |
| `redes.<rede>.texto_final` | Texto de Instagram, Facebook, TikTok e Threads | O Publicador publica **exatamente** este texto, letra por letra |
| `redes.youtube.titulo` / `descricao` / `tags` | Texto do YouTube | Limites da seção 4.4 |
| `redes.pinterest.titulo` / `descricao` / `texto_alternativo` / `link` | Texto do Pinterest | Só nos 3 canais com Pinterest |
| `redes.<rede>` = `null` | A rede não tem texto | Se a rede está no `pedido.json` e o texto é `null` → passo 17 |
| `enquete` | Pergunta e opções do story com enquete (GTA 16h) | Usado pelo `story_post.py` (bloco L) |
| `aviso.titulo_curto` | Título do item no aviso "no ar" | Usado no bloco M |

#### 2.3.3 Arquivos de mídia (nomes fixos da esteira)

| Arquivo | Quem faz | Quando é obrigatório |
|---|---|---|
| `final.mp4` | Editor (manual 03) | `tipo` = `reel` ou `video` |
| `capa.jpg` | Designer (manual 07) | Reel e vídeo |
| `lamina_01.jpg` … `lamina_10.jpg` | Designer | `tipo` = `carrossel` (ou arte de feed avulsa: só `lamina_01.jpg`) |
| `story.jpg` | Designer | Story de divulgação com arte, story com enquete |
| `pin.jpg` | Designer | Quando `pinterest` está em `redes` |
| `legenda.srt` | Legendador (manual 04) | Vídeo com fala (vai como legenda no YouTube quando a etapa 4 permitir) |

### 2.4 Entrada 3 — plano da semana (vem do Estrategista, manual 12)

O Publicador **não decide horário**, mas usa o plano para conferir. O arquivo é `H:\HypadoLocal\estrategia\planos\plano_semana_<AAAA>-W<nn>.json` **(a criar — ver manual 12, seção 2)**. O Publicador só lê de lá:

- `canais.<canal>.slots[].slot_id` → tem que existir o `slot_id` do `pedido.json` (item sem `slot_id` é P0 ou está fora do plano: segue normalmente e fica registrado no `historico.log`);
- `canais.<canal>.slots[].redes[].hora` → confirma os `horarios` do `pedido.json`;
- `canais.<canal>.limites.max_posts_dia_por_rede` e `intervalo_minimo_min` → nunca publicar acima disso no mesmo dia (passos 22 e 23);
- o ajuste do dia, `H:\HypadoLocal\estrategia\ajustes\ajuste_<AAAA-MM-DD>.json` → horários mudados de última hora (campo `mover`).

### 2.5 Entrada 4 — tokens e IDs das contas (NUNCA ler à mão)

- Tokens da Meta: `H:\HypadoLocal\segredos\meta_tokens.txt` **(existe)**. O `publicador_meta.py` lê sozinho. **Ninguém abre, copia, imprime ou cola esse arquivo em lugar nenhum.**
- Credenciais do YouTube e do Facebook da etapa 4: em `H:\HypadoLocal\segredos\` **(em andamento no PC — não mexer)**.
- IDs das contas (`ig_id`, `threads_user_id`, `page_id`, `channel_id`): ficam na configuração que o próprio `publicador_meta.py` já usa. Não copiar ID à mão para nenhum JSON.

### 2.6 Saída 1 — trabalho na fila da API (`H:\HypadoLocal\fila_api\`)

Para Instagram e Threads, o Publicador (app) coloca **um arquivo por publicação** na fila do `publicador_meta.py`. O formato exato é o que o script **já usa no PC**; o exemplo abaixo mostra os campos que este manual espera encontrar. **Se algum nome de campo for diferente no PC, vale o do script** — não mude o script para bater com o manual.

```json
{
  "id": "P1_2026-10-06_1830_gta_rockstar-quinta-ig",
  "post_id": "P1_2026-10-06_1830_gta_rockstar-quinta",
  "rede": "instagram",
  "conta": "@hpgta6",
  "tipo": "reels",
  "arquivo": "H:\\HypadoLocal\\esteira\\06_agendados\\P1_2026-10-06_1830_gta_rockstar-quinta\\final.mp4",
  "capa": "H:\\HypadoLocal\\esteira\\06_agendados\\P1_2026-10-06_1830_gta_rockstar-quinta\\capa.jpg",
  "legenda": "A Rockstar mexeu no site de novo… o que você acha que vem aí na quinta? 👀\n\nVídeo: @criadorexemplo\n\n#gta6 #gtavi #rockstargames",
  "publicar_em": "2026-10-06T18:30:00-03:00",
  "story_depois": true,
  "tentativas": 0,
  "status": "na_fila"
}
```

O campo `legenda` é **exatamente** o `redes.instagram.texto_final` do `post.json` (no Threads, o `redes.threads.texto_final`), sem mudar nenhuma letra. O `publicar_em` é o horário daquela rede (`horarios.<rede>` do `pedido.json`, ou `publicar_em` quando não houver `horarios`).

Estados possíveis do campo `status` (ciclo de vida):

```
na_fila → enviando → processando (a rede está preparando o vídeo)
        → publicado            (tem media_id e permalink)
        → tempo_esgotado       (a rede não respondeu a tempo: vai para o reenvio seguro)
        → erro                 (a rede recusou com motivo: vai para 99_erros)
```

### 2.7 Saída 2 — `publicado.json` (dentro da pasta do item) **(a criar — etapa 3)**

Um registro por rede. É o que o Analista (manual 11) usa para saber **qual post medir**. Exemplo completo, depois de tudo publicado:

```json
{
  "item": "P1_2026-10-06_1830_gta_rockstar-quinta",
  "post_id": "P1_2026-10-06_1830_gta_rockstar-quinta",
  "canal": "gta",
  "tipo": "reel",
  "formato_estrategia": "reel_noticia",
  "slot_id": "2026-W41-gta-ter-02",
  "teste_ab": null,
  "duracao_video_s": 31.4,
  "redes": {
    "instagram": {
      "status": "publicado",
      "conta": "@hpgta6",
      "media_id": "17900000000000001",
      "permalink": "https://www.instagram.com/reel/EXEMPLO1/",
      "horario_plano": "2026-10-06T18:30:00-03:00",
      "publicado_em": "2026-10-06T18:31:12-03:00",
      "atraso_min": 1.2,
      "tentativas": 1,
      "conferido_na_api": true,
      "story_divulgacao": { "status": "publicado", "media_id": "17900000000000002", "publicado_em": "2026-10-06T18:34:40-03:00" },
      "story_clicavel": { "status": "feito", "destaque": "Notícias", "feito_em": "2026-10-06T18:52:03-03:00" }
    },
    "threads": {
      "status": "publicado",
      "conta": "@hpgta6",
      "media_id": "18000000000000003",
      "permalink": "https://www.threads.net/@hpgta6/post/EXEMPLO2",
      "horario_plano": "2026-10-06T18:35:00-03:00",
      "publicado_em": "2026-10-06T18:35:20-03:00",
      "atraso_min": 0.3,
      "tentativas": 1,
      "conferido_na_api": true
    },
    "facebook": {
      "status": "publicado",
      "conta": "GTA 6 | HP",
      "media_id": "1000000000000004",
      "permalink": "https://www.facebook.com/reel/1000000000000004",
      "horario_plano": "2026-10-06T18:40:00-03:00",
      "publicado_em": "2026-10-06T18:40:55-03:00",
      "atraso_min": 0.9,
      "tentativas": 1,
      "conferido_na_api": true
    },
    "youtube": {
      "status": "agendado",
      "conta": "GTA 6 | HP",
      "media_id": "EXEMPLOyt01",
      "permalink": "https://youtube.com/shorts/EXEMPLOyt01",
      "horario_plano": "2026-10-06T19:00:00-03:00",
      "agendado_para": "2026-10-06T19:00:00-03:00",
      "publicado_em": null,
      "tentativas": 1,
      "conferido_na_api": true
    },
    "tiktok": {
      "status": "agendado_pelo_claude",
      "conta": "@hpgta6",
      "horario_plano": "2026-10-06T19:10:00-03:00",
      "agendado_para": "2026-10-06T19:10:00-03:00",
      "permalink": null,
      "fonte": "tiktok_ok.json"
    },
    "pinterest": { "status": "nao_se_aplica" }
  },
  "aviso_no_ar": { "status": "na_fila", "arquivo": "H:\\HypadoLocal\\whatsapp_fila\\2026-10-06_noite_gta.json" },
  "atualizado_em": "2026-10-06T19:12:40-03:00"
}
```

`formato_estrategia`, `slot_id` e `teste_ab` são copiados do `pedido.json`. `duracao_video_s` é medida no `final.mp4` (com `achar_ffprobe()` da `hpbase`; se não houver ffprobe, pelo plano B com ffmpeg) — o Analista usa para calcular a retenção.

Valores aceitos para `status` de cada rede:

| Valor | Significado |
|---|---|
| `pendente` | Ainda não chegou a hora ou ainda não foi para a fila |
| `na_fila` | Arquivo colocado na fila da rede |
| `agendado` | A rede aceitou e vai soltar sozinha no horário (YouTube com `publishAt`, por exemplo) |
| `agendado_pelo_claude` | TikTok ou Pinterest agendados pelo Claude no Chrome (tem `tiktok_ok.json` / `pinterest_ok.json`) |
| `publicado` | Está no ar, com `media_id` e `permalink` conferidos na API |
| `tempo_esgotado` | A rede não respondeu; em reenvio seguro |
| `erro` | Recusado; ver `erro.json` |
| `nao_se_aplica` | A rede não está na lista `redes` do `pedido.json` |
| `rede_inativa` | A rede ainda não foi ligada no app (ex.: Facebook e YouTube enquanto a etapa 4 não termina); não segura as outras redes (passos 37 e 42) |

### 2.8 Saída 3 — `tiktok_ok.json` (o Claude grava depois de agendar no Chrome)

Enquanto este arquivo não existir, o app **não** considera o TikTok feito e **não** move a pasta para `07_postados`.

```json
{
  "post_id": "P1_2026-10-06_1830_gta_rockstar-quinta",
  "conta": "@hpgta6",
  "acao": "agendado",
  "agendado_para": "2026-10-06T19:10:00-03:00",
  "legenda_usada": "Rockstar mexeu no site de novo 👀 o que vem na quinta? Vídeo: @criadorexemplo #gta6 #gtavi",
  "arquivo_enviado": "final.mp4",
  "capa_escolhida": "quadro 0,8 s",
  "conferido_lista_agendados": true,
  "link": null,
  "feito_por": "claude",
  "feito_em": "2026-10-06T15:20:31-03:00",
  "observacoes": ""
}
```

- `acao`: `agendado` (vai sair sozinho no horário) ou `publicado` (saiu na hora; aí `link` é obrigatório).
- `conferido_lista_agendados`: `true` só depois de o Claude ver o post na lista de agendados do TikTok Studio com a hora certa.
- Depois que o horário passar, o Claude (ou o Analista, na coleta do Chrome) completa o `link` com o endereço público do vídeo.

### 2.9 Saída 4 — `pinterest_ok.json` **(a criar)** (Receitas, Carros, Destinos)

Mesmo modelo do TikTok, com os campos do Pinterest:

```json
{
  "post_id": "P2_2026-10-07_1200_receitas_bolo-cenoura",
  "conta": "Receitas | HP",
  "acao": "agendado",
  "pasta_pinterest": "Bolos fáceis",
  "titulo": "Bolo de cenoura fofinho com calda de chocolate",
  "descricao": "Receita completa no vídeo. Valores aproximados, pesquisados em out/2026. Podem mudar.",
  "texto_alternativo": "Fatia de bolo de cenoura com cobertura de chocolate",
  "link": "https://sites.google.com/view/hpcanais",
  "agendado_para": "2026-10-07T12:00:00-03:00",
  "conferido_lista_agendados": true,
  "link": null,
  "feito_por": "claude",
  "feito_em": "2026-10-07T09:10:02-03:00"
}
```

### 2.10 Saída 5 — pedido de story clicável (`H:\HypadoLocal\emulador\fila_story\<post_id>.json`)

Criado **só depois** do Instagram confirmar o post (tem que existir o `permalink`). Campos definidos no ticket F:

```json
{
  "post_id": "P1_2026-10-06_1830_gta_rockstar-quinta",
  "conta": "@hpgta6",
  "canal": "gta",
  "link": "https://www.instagram.com/reel/EXEMPLO1/",
  "publicado_em": "2026-10-06T18:31:12-03:00",
  "titulo": "Rockstar mexeu no site de novo",
  "destaque": "Notícias"
}
```

Quem consome: `story_post.py` **(a criar — ticket F)**, que liga o emulador, abre o app oficial do Instagram, troca para a conta, compartilha o post no story, coloca no destaque e no fim roda `story_clicavel.py feito <post_id> --link <url>` **(existe)**.

### 2.11 Saída 6 — aviso "no ar" (`H:\HypadoLocal\whatsapp_fila\<arquivo>.json`) **(a criar — ticket E)**

Um arquivo por mensagem. O texto segue o modelo de `G:\Meu Drive\Hypado\06 Projeto\AVISO.md` **(existe)** e **sempre começa com `*Claude - *`**.

```json
{
  "grupo": "HP | Comissão 🚀",
  "texto": "*Claude - * No ar agora (noite de 06/10):\n\n🎮 GTA 6 | HP — Rockstar mexeu no site de novo\nIG: https://www.instagram.com/reel/EXEMPLO1/\nThreads: https://www.threads.net/@hpgta6/post/EXEMPLO2\nFB: https://www.facebook.com/reel/1000000000000004\nYT (19h): https://youtube.com/shorts/EXEMPLOyt01\nTikTok: agendado 19h10",
  "anexos": [],
  "origem": "publicador",
  "lote": "noite",
  "criado_em": "2026-10-06T19:12:40-03:00"
}
```

- `grupo`: só `HP | Comissão 🚀` ou um grupo da lista `HP | Grupos`. Qualquer outro nome = o enviador recusa.
- `texto`: tem que começar exatamente com `*Claude - *` (asterisco, a palavra Claude, espaço, hífen, espaço, asterisco).

### 2.12 Saída 7 — `historico.log` do item e log do dia

Cada acontecimento vira **uma linha** no `historico.log` da pasta (a função `anexar_linha` da base `hpbase` já põe a data e hora na frente). Exemplo:

```
2026-10-06T18:30:02-03:00 publicador: instagram na_fila (fila_api\P1_2026-10-06_1830_gta_rockstar-quinta-ig.json)
2026-10-06T18:31:12-03:00 publicador: instagram publicado media_id=17900000000000001
2026-10-06T18:31:15-03:00 publicador: instagram conferido na API (legenda e horário batem)
2026-10-06T18:34:40-03:00 publicador: instagram story_divulgacao publicado
2026-10-06T18:34:41-03:00 publicador: fila_story criado (P1_2026-10-06_1830_gta_rockstar-quinta.json)
2026-10-06T18:35:20-03:00 publicador: threads publicado media_id=18000000000000003
2026-10-06T19:12:40-03:00 publicador: todas as redes ok; pasta movida para 07_postados
```

O log geral fica em `H:\HypadoLocal\app\logs\publicador_AAAA-MM-DD.log`. Esse log **passa por um filtro que apaga qualquer coisa com cara de token** (função `mascarar` da `hpbase`), mas mesmo assim: **nunca** mande o script imprimir token.

### 2.13 Saída 8 — `erro.json` (quando o item vai para `99_erros`)

```json
{
  "item": "P1_2026-10-06_1830_gta_rockstar-quinta",
  "rede": "instagram",
  "etapa": "publicacao",
  "codigo": "tempo_esgotado_4x",
  "mensagem": "4 tentativas sem resposta; conferido na API: post NÃO existe",
  "tentativas": [
    { "n": 1, "em": "2026-10-06T18:30:02-03:00", "resultado": "tempo_esgotado", "conferencia_api": "não achou" },
    { "n": 2, "em": "2026-10-06T18:31:05-03:00", "resultado": "tempo_esgotado", "conferencia_api": "não achou" },
    { "n": 3, "em": "2026-10-06T18:36:10-03:00", "resultado": "tempo_esgotado", "conferencia_api": "não achou" },
    { "n": 4, "em": "2026-10-06T18:51:20-03:00", "resultado": "tempo_esgotado", "conferencia_api": "não achou" }
  ],
  "redes_ja_publicadas": ["threads", "facebook"],
  "o_que_fazer": "Abrir ticket P0 em publicacao; tentar de novo manualmente com 'publicador_meta.py reenviar <id>' depois de 30 min",
  "criado_em": "2026-10-06T18:52:00-03:00"
}
```

> Importante: se **uma** rede deu erro e as outras saíram, a pasta vai para `99_erros` **com** o `publicado.json` mostrando o que já saiu. Assim, ao tentar de novo, só a rede que falhou é refeita (nunca republicar as que já estão no ar).

---

## 3. Passo a passo (para leigo)

> O **app** faz a maior parte destes passos sozinho (ver seção 7). O passo a passo está escrito para que **qualquer pessoa** consiga (a) entender o que o app está fazendo, (b) conferir se ele fez certo e (c) fazer à mão numa emergência. Onde o passo é só do Claude (TikTok e Pinterest pelo Chrome), isso está dito no título do bloco.

### Bloco A — Começo do dia (uma vez por dia, de manhã)

**Passo 1.** Abra o PowerShell (tecla Windows, digite `PowerShell`, Enter) e cole o bloco de preparação do início deste manual (as 5 linhas com `$py`, `$scripts`, `$esteira`, `$logs`).

**Passo 2.** Confira se o app está rodando: abra o navegador em `http://127.0.0.1:8770`. Tem que aparecer a tela do HP Studio. Se não abrir, o app está parado: abra ticket na área `publicacao` (passo 91) e **não** publique nada à mão até alguém do plantão olhar, a não ser P0 (passo 21).

**Passo 3.** Confira se a esteira existe:

```powershell
Test-Path "$esteira\06_agendados"
Test-Path "$esteira\07_postados"
Test-Path "$esteira\99_erros"
```

As três linhas têm que responder `True`. Se alguma responder `False`, a etapa 3 do app ainda não foi instalada nesse PC: siga o processo atual do plantão (fila `fila_api` direto) e anote isso no ticket do dia.

**Passo 4.** Confira a hora. Publicar pela API **é trabalho leve** (só manda o arquivo pela internet), então pode acontecer **a qualquer hora**, inclusive das 18h às 22h30, que é o horário nobre das redes. O que é **proibido** das 18h às 22h30 é **trabalho pesado** (renderizar, cortar, dublar). O story pelo emulador é a exceção combinada: pode sair a qualquer hora desde que leve **no máximo 5 minutos** (o robô usa a trava com `ignorar_horario=True`, ver passo 78).

**Passo 5.** Veja se há trabalho pesado rodando (só para saber, publicar não depende disso):

```powershell
Test-Path "H:\HypadoLocal\app\pesado.lock"
```

`True` = tem alguém usando o PC pesado agora. Para ver quem: `Get-Content "H:\HypadoLocal\app\pesado.lock"` (esse arquivo **não** tem segredo, só o nome do dono e a hora).

**Passo 6.** Olhe se ontem teve erro de publicação no log:

```powershell
$ontem = (Get-Date).AddDays(-1).ToString("yyyy-MM-dd")
Select-String -Path "$logs\publicador_$ontem.log" -Pattern "ERROR|WARNING" | Select-Object -Last 30
```

Se aparecer linha, confira se cada erro já tem ticket (passo 91). Se não tiver, abra.

**Passo 7.** Veja se tem item parado em `99_erros`:

```powershell
Get-ChildItem "$esteira\99_erros" -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 10 Name, LastWriteTime
```

Cada pasta ali precisa ter `erro.json` e um ticket aberto. Pasta sem ticket = abrir ticket agora.

**Passo 8.** Veja o que está esperando para sair hoje, **em ordem de prioridade** (como o nome começa com `P0_`, `P1_`, `P2_`, a ordem alfabética já põe o urgente primeiro):

```powershell
Get-ChildItem "$esteira\06_agendados" -Directory | Sort-Object Name | Select-Object Name
```

### Bloco B — Pegar um item aprovado e conferir (para cada item)

**Passo 9.** Escolha o próximo item: **primeiro todos os `P0_`**; depois, entre os `P1_` e `P2_`, o de **horário mais cedo** (o `HHMM` do nome).

**Passo 10.** Guarde o caminho do item numa variável (troque pelo nome real da pasta):

```powershell
$item = "$esteira\06_agendados\P1_2026-10-06_1830_gta_rockstar-quinta"
```

**Passo 11.** Liste o que tem dentro:

```powershell
Get-ChildItem $item | Select-Object Name, Length
```

Tem que ter, no mínimo: `pedido.json`, `post.json`, `aprovado.json`, `historico.log` e a mídia (`final.mp4` + `capa.jpg` para vídeo; `lamina_01.jpg`… para carrossel; `pin.jpg` quando tem Pinterest). Nenhum com `Length` igual a 0.

**Passo 12.** Confira a aprovação:

```powershell
$apr = Get-Content "$item\aprovado.json" -Raw -Encoding UTF8 | ConvertFrom-Json
$apr.veredito; $apr.media_nota; $apr.classe
```

Tem que sair `aprovado`, uma nota **≥ 7** e a classe `Excelente` (≥ 9) ou `Bom` (7 a 8,9). Qualquer outra coisa: **não publica**, vá para o passo 17.

**Passo 13.** Confira que **não** existe pedido de refazer:

```powershell
Test-Path "$item\refazer.json"
```

Tem que responder `False`. Se responder `True`, o item foi mandado de volta e não deveria estar aqui: passo 17.

**Passo 14.** Leia o `pedido.json` e o `post.json` e confira se são deste item mesmo:

```powershell
$ped  = Get-Content "$item\pedido.json" -Raw -Encoding UTF8 | ConvertFrom-Json
$post = Get-Content "$item\post.json"   -Raw -Encoding UTF8 | ConvertFrom-Json
Split-Path $item -Leaf
$ped.id
$post.item
$post.esquema; $post.status
```

As três primeiras linhas têm que mostrar **exatamente o mesmo nome**. Depois tem que aparecer `hp.post/1` e `pronto`. Qualquer diferença = passo 17 (motivo: "post.json de outro item", "esquema desconhecido" ou "post.json não está pronto").

**Passo 15.** Confira o canal e as contas. Tabela oficial:

| `canal` | Instagram / Threads / TikTok | Facebook / YouTube / Pinterest |
|---|---|---|
| `gta` | @hpgta6 | GTA 6 \| HP |
| `futebol` | @hp.futebol | Futebol \| HP |
| `filmes` | @hp.filmes | Filmes e Séries \| HP |
| `receitas` | @hp.receitas | Receitas \| HP |
| `carros` | @hp.carros | Carros \| HP |
| `destinos` | @hp.destinos | Destinos \| HP |

```powershell
$ped.canal; $post.canal; $post.conta
$ped.redes -join ", "
```

`$ped.canal` e `$post.canal` têm que ser iguais, e `$post.conta` tem que ser o @ do canal na tabela acima (as contas de Facebook, YouTube e Pinterest saem da mesma tabela, pelo canal). **Conta de outro canal = parar** (passo 17). Pinterest só existe para `receitas`, `carros` e `destinos`; se `pinterest` aparecer nas redes de outro canal, é erro: passo 17. Toda rede da lista tem que ter texto no `post.json` (`$post.redes.<rede>` diferente de vazio); rede sem texto = passo 17.

**Passo 16.** Confira que os arquivos de mídia existem e não estão vazios (nomes fixos, seção 2.3.3):

```powershell
$precisa = switch ($ped.tipo) { "reel" { @("final.mp4","capa.jpg") } "video" { @("final.mp4","capa.jpg") } "carrossel" { @("lamina_01.jpg") } "story" { @("story.jpg") } default { @() } }
if ($ped.redes -contains "pinterest") { $precisa += "pin.jpg" }
foreach ($a in $precisa) { $p = Join-Path $item $a; "{0}  existe={1}  tamanho={2}" -f $a, (Test-Path $p), ((Get-Item $p -ErrorAction SilentlyContinue).Length) }
```

Todo arquivo tem que mostrar `existe=True` e tamanho maior que zero.

**Passo 17.** (Só se algo falhou nos passos 12 a 16, 18 ou 19.) Tire o item da fila e registre o motivo. Normalmente **o app faz isso sozinho**; à mão é assim:

```powershell
$motivo = "post.json de outro item"   # escreva o motivo real, curto
$erro = @{ item = (Split-Path $item -Leaf); etapa = "conferencia_publicador"; codigo = "entrada_invalida"; mensagem = $motivo; criado_em = (Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz") } | ConvertTo-Json
Set-Content -Path "$item\erro.json" -Value $erro -Encoding UTF8
Add-Content -Path "$item\historico.log" -Value ("{0} publicador: movido para 99_erros ({1})" -f (Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz"), $motivo) -Encoding UTF8
Move-Item -LiteralPath $item -Destination "$esteira\99_erros\"
```

Depois abra ticket (passo 91). **Nunca** conserte o `post.json` você mesmo "para dar tempo": quem escreve texto é o Redator (manual 08), quem aprova é o Revisor (manual 09).

**Passo 18.** Confira o **crédito** em todas as redes que vão publicar (conteúdo de terceiros **sempre** tem crédito):

```powershell
$post.credito.nome
foreach ($r in $ped.redes) {
  $t = $post.redes.$r
  $texto = "$($t.texto_final) $($t.descricao)"
  $cred = $post.credito.por_rede.$r
  "{0}: credito='{1}' tem_credito={2}" -f $r, $cred, ([bool]$cred -and $texto.Contains([string]$cred))
}
```

Em conteúdo de **terceiros**, toda rede tem que mostrar `tem_credito=True`. Se alguma mostrar `False`: passo 17 com motivo "crédito faltando no texto de <rede>". Conteúdo **próprio** da HP (o `credito.nome` é da própria HP, como "HP Receitas") dispensa o crédito no texto, como define o Redator (manual 08).

**Passo 19.** Se a legenda cita **valor em dinheiro** (R$, preço, custo), ela **tem** que ter a frase "Valores aproximados…":

```powershell
"valores_aproximados = {0}" -f $post.valores_aproximados
foreach ($r in $ped.redes) {
  $t = $post.redes.$r
  $texto = "$($t.texto_final) $($t.descricao)"
  if ($post.valores_aproximados -or $texto -match 'R\$|reais|preço|custa') { "{0}: cita valor; tem_aviso={1}" -f $r, ($texto -match 'Valores aproximados') }
}
```

Se aparecer `tem_aviso=False`: passo 17 com motivo "valor sem 'Valores aproximados…'".

### Bloco C — Conferir o horário

**Passo 20.** Compare o horário de cada rede (`horarios.<rede>` do `pedido.json`; sem ele, `publicar_em`) com a hora de agora:

```powershell
$agora = Get-Date
foreach ($r in $ped.redes) {
  $hs = if ($ped.horarios -and $ped.horarios.$r) { $ped.horarios.$r } else { $ped.publicar_em }
  $h = [datetime]::Parse($hs)
  "{0}: plano={1:dd/MM HH:mm}  diferenca_min={2:N0}" -f $r, $h, ($h - $agora).TotalMinutes
}
```

- `diferenca_min` positivo = ainda vai chegar a hora: tudo certo, o app espera.
- Entre 0 e −120 (atrasou até 2 h): o app publica **assim que puder** e registra o atraso.
- Menor que −120 (atrasou mais de 2 h) num `P1`/`P2`: **não publica sozinho.** O horário ruim pode derrubar o alcance e bagunçar a medição. O app marca o item como "precisa de novo horário" e o **Estrategista** (manual 12) escolhe o próximo horário livre no plano (pelo ajuste diário das 7h ou na hora, se for urgente). Registre no `historico.log`.

**Passo 21.** `P0` (urgente, ao vivo) **fura a fila**: sai **na hora**, sem esperar horário do plano, em todas as redes da lista `redes` do `pedido.json`. Continua valendo: aprovação, conta certa, crédito, conferência antes de reenviar, story só depois do post. Meta de tempo: do `aprovado.json` ao post no Instagram em **≤ 10 minutos**.

**Passo 22.** Confira o **limite do dia**. O plano da semana diz o máximo de posts por rede por dia em cada canal (`limites.max_posts_dia_por_rede`). Para contar quantos já saíram hoje num canal:

```powershell
$hoje = Get-Date -Format "yyyy-MM-dd"
(Get-ChildItem "$esteira\07_postados" -Directory | Where-Object { $_.Name -match "_${hoje}_\d{4}_gta_" }).Count
```

(Troque `gta` pelo canal.) Se já bateu o máximo, um `P2` vai para o próximo dia (o app remarca e registra); um `P1` pede decisão do Estrategista; um `P0` sai mesmo assim (P0 não conta no limite, mas conta no relatório).

**Passo 23.** Confira o **intervalo mínimo** entre dois posts do **feed** da **mesma conta** na **mesma rede**: padrão **60 minutos** (ou o `limites.intervalo_minimo_min` do plano, se for diferente). Stories não contam. P0 não respeita intervalo. Se dois itens caírem colados, o app empurra o segundo para respeitar o intervalo e registra `"empurrado +N min por intervalo"` no `historico.log`.

### Bloco D — Instagram (o app faz sozinho pelo `publicador_meta.py`)

**Passo 24.** Na hora certa (ou alguns minutos antes, conforme o script já faz), o app cria o arquivo do trabalho na fila da API: `H:\HypadoLocal\fila_api\<post_id>-ig.json` (modelo na seção 2.6). Para ver a fila:

```powershell
Get-ChildItem "H:\HypadoLocal\fila_api" -File | Sort-Object LastWriteTime -Descending | Select-Object -First 15 Name, LastWriteTime
```

**Passo 25.** Para ver o conteúdo de um trabalho da fila (esses arquivos **não** têm token; o token fica só em `segredos\`):

```powershell
Get-Content "H:\HypadoLocal\fila_api\P1_2026-10-06_1830_gta_rockstar-quinta-ig.json" -Raw -Encoding UTF8 | ConvertFrom-Json | Format-List
```

Confira: `conta`, `publicar_em`, `legenda` (com crédito) e caminho do `arquivo`.

**Passo 26.** O que o `publicador_meta.py` **(existe)** faz por dentro, explicado para leigo (não precisa fazer nada, só entender):

1. Pede à Meta para criar um **"contêiner"** (uma caixa temporária) com o vídeo, a capa e a legenda, na conta certa.
2. A Meta baixa e **processa** o vídeo. Enquanto processa, o status do contêiner é `IN_PROGRESS`. Quando termina, vira `FINISHED`. Se o vídeo tem problema, vira `ERROR`. Se ninguém publica a caixa a tempo, vira `EXPIRED` (a caixa vence; conferir o prazo na página oficial).
3. Com o contêiner `FINISHED`, o script manda **publicar** a caixa. A Meta devolve o `media_id` (número do post).
4. O script grava o resultado na fila e o app copia para o `publicado.json`.

**Passo 27.** Acompanhe o andamento pelo log do app (a janela fica mostrando as linhas novas; para sair, aperte `Ctrl + C`):

```powershell
Get-Content "$logs\publicador_$(Get-Date -Format yyyy-MM-dd).log" -Tail 30 -Wait
```

O `publicador_meta.py` também tem o log próprio dele, no lugar onde ele já grava hoje. Para ver os comandos que o script aceita no PC:

```powershell
& $py .\publicador_meta.py --help
```

**Passo 28.** Resultado esperado no log: uma linha `instagram publicado media_id=...`. Logo depois, a **conferência na API** (bloco J) roda sozinha. Só depois dela o post conta como publicado de verdade.

**Passo 29.** **Carrossel** (várias imagens num post): o script cria um contêiner para cada imagem e um contêiner "pai" que junta todas, na ordem dos nomes (`lamina_01.jpg`, `lamina_02.jpg`…). Limite de imagens por carrossel e tamanhos aceitos: **(conferir na página oficial)** — hoje a HP usa de 2 a 10 lâminas, verticais 1080×1350. A ordem das lâminas é a da numeração feita pelo Designer; **nunca** reordenar na publicação.

**Passo 30.** **Limite de publicações pela API.** A Meta limita quantos posts uma conta pode publicar pela API em 24 horas (o número muda; **conferir na página oficial**, e o próprio script pode consultar o uso atual da conta). Se uma conta estiver a **5 posts ou menos** do limite, o app segura os `P2` para o dia seguinte e reserva o restante para `P0`/`P1`. Esse limite quase nunca é atingido no ritmo da HP; se for, é sinal de que tem algo publicando em dobro — abrir ticket P0.

**Passo 31.** Story de divulgação e story clicável: ver bloco L. **Nunca** antes do post estar confirmado.

### Bloco E — Threads (o app faz sozinho pelo `publicador_meta.py`)

**Passo 32.** O app cria `H:\HypadoLocal\fila_api\<post_id>-th.json` com `rede: "threads"`. O Threads é publicado pela **API oficial do Threads**, na mesma fila e pelo mesmo script do Instagram **(existe)**.

**Passo 33.** Limites do Threads (**conferir na página oficial**, mudam): texto de até 500 caracteres; vídeo curto; imagem. O Redator (manual 08) já entrega o texto no tamanho certo. Se passar do limite, o script recusa: passo 17 com motivo "texto do Threads acima do limite".

**Passo 34.** Como no Instagram: cria contêiner → (para vídeo, espera processar) → publica → recebe `media_id` → conferência na API (bloco J).

**Passo 35.** O Threads **não** tem story. O `post.json` do Threads nunca pede story.

### Bloco F — Facebook (Página) — (em andamento no PC — não mexer)

**Passo 36.** A publicação no Facebook pela API de Páginas é a **etapa 4** do app, que está sendo feita no PC agora. **Não mexer, não adiantar, não consertar.**

**Passo 37.** Enquanto a etapa 4 não for ligada, a rede Facebook fica marcada como **inativa** na configuração do app. Nesse caso o app grava `"status": "rede_inativa"` no `publicado.json` e **não segura** as outras redes por causa do Facebook. O Facebook continua sendo feito do jeito que o plantão faz hoje.

**Passo 38.** Quando a etapa 4 for ligada (depois dos 7 dias de modo sombra), o fluxo é igual ao Instagram: fila → publica na **Página certa** → recebe o identificador → conferência na API (listar as últimas publicações/vídeos da Página e achar pela legenda e horário).

**Passo 39.** O Publicador confere no Facebook as mesmas coisas de sempre: Página do canal certo, legenda com crédito, horário.

### Bloco G — YouTube (Shorts) — (em andamento no PC — não mexer)

**Passo 40.** A publicação no YouTube pela **YouTube Data API** também é da **etapa 4**, junto com a **auditoria da API do YouTube**, ambas em andamento no PC. **Não mexer.**

**Passo 41.** Como vai funcionar (para entender): o app envia o vídeo como **privado** com uma **data de publicação agendada** (`publishAt`); na hora marcada, o próprio YouTube torna o vídeo público. Por isso o status do YouTube no `publicado.json` fica `agendado` até a hora, e o `media_id` já existe desde o envio.

**Passo 42.** Por que a auditoria importa: pela regra do YouTube, vídeos enviados por um **projeto de API ainda não auditado** ficam **presos como privados** (**conferir na página oficial**). Até a auditoria ser aprovada, o YouTube pela API fica `rede_inativa` como o Facebook, e segue o processo atual.

**Passo 43.** **Cota diária** da API do YouTube: cada projeto tem uma cota por dia, e **enviar vídeo custa muito mais do que ler dados** (**conferir os números atuais na página oficial de cotas**). A cota zera todo dia à meia-noite do horário do Pacífico (4h ou 5h da manhã em Brasília, dependendo da época do ano). Se a cota acabar, o app **não** tenta de novo o dia todo: marca o vídeo para o primeiro horário do plano depois que a cota zerar e registra no `historico.log`.

**Passo 44.** Conferência do YouTube: depois do envio, o app pergunta à API os dados do vídeo pelo `media_id` e confere: canal certo, título igual ao `post.json`, `publishAt` igual ao horário do YouTube no `pedido.json` (`horarios.youtube` ou `publicar_em`). Vídeo vertical e curto (limite de duração de Shorts: **conferir na página oficial**).

### Bloco H — TikTok (quem faz é o **Claude**, pela página oficial no Chrome)

> O TikTok **não** é publicado pelo app: a HP não tem API do TikTok para publicar. O Claude agenda na **página oficial** (TikTok Studio) no Chrome que **já está logado** na conta (o login foi feito pelo Antônio). O app **espera** o arquivo `tiktok_ok.json` para considerar o TikTok feito.

**Passo 45.** Descubra quais itens estão esperando o TikTok (têm `tiktok` nas `redes` do `pedido.json` e ainda não têm `tiktok_ok.json`):

```powershell
Get-ChildItem "$esteira\06_agendados" -Directory | Sort-Object Name | ForEach-Object {
  $pd = Get-Content (Join-Path $_.FullName "pedido.json") -Raw -Encoding UTF8 | ConvertFrom-Json
  if (($pd.redes -contains "tiktok") -and -not (Test-Path (Join-Path $_.FullName "tiktok_ok.json"))) {
    $hora = if ($pd.horarios -and $pd.horarios.tiktok) { $pd.horarios.tiktok } else { $pd.publicar_em }
    "{0}  canal={1}  hora={2}" -f $_.Name, $pd.canal, $hora
  }
}
```

Faça **em lote** (vários itens de uma vez, de manhã e à tarde), para gastar menos token. Prioridade: `P0` primeiro, depois pelo horário.

**Passo 46.** Abra o Chrome no perfil onde as contas da HP já estão conectadas e vá para a página de envio do TikTok Studio (endereço atual: `https://www.tiktok.com/tiktokstudio/upload` — **conferir na página oficial** se mudou).

**Passo 47.** **Se aparecer QUALQUER uma destas telas, PARE na hora:** pedido de login, pedido de senha, pedido de código (SMS, e-mail, app autenticador), "confirme que é você", quebra-cabeça/CAPTCHA, "aceite os novos termos", "crie uma conta". **Não digite nada, não clique em aceitar, não tente contornar.** Feche a aba, abra ticket (passo 91) dizendo o que apareceu e em qual conta, e siga com as outras redes. Se houver `P0` esperando TikTok, o ticket é `P0`. **Não** avise por WhatsApp: WhatsApp é só para as 3 coisas combinadas.

**Passo 48.** Confira a conta ativa (foto e @ no canto da página). Tem que ser a do canal do item (tabela do passo 15). Se for outra, use o menu de **trocar de conta** do próprio TikTok, **somente** se a conta certa já aparecer na lista de contas conectadas. Se a troca pedir senha ou código → passo 47 (parar).

**Passo 49.** Clique em **Selecionar vídeo** (ou arraste o arquivo) e escolha o `final.mp4` **da pasta do item** (`H:\HypadoLocal\esteira\06_agendados\<item>\final.mp4`). Espere a barra de envio chegar a 100%.

**Passo 50.** No campo de **descrição**, apague o que o TikTok sugerir e cole **exatamente** o texto de `redes.tiktok.texto_final` do `post.json`. Para copiar o texto certinho para a área de transferência:

```powershell
$p   = Get-Content "$item\post.json"   -Raw -Encoding UTF8 | ConvertFrom-Json
$ped = Get-Content "$item\pedido.json" -Raw -Encoding UTF8 | ConvertFrom-Json
$hTik = if ($ped.horarios -and $ped.horarios.tiktok) { $ped.horarios.tiktok } else { $ped.publicar_em }
Set-Clipboard -Value $p.redes.tiktok.texto_final
```

Depois é só colar (`Ctrl + V`). Confira se o **crédito** está no texto.

**Passo 51.** **Capa:** clique em editar capa e escolha o quadro mais parecido com o `capa.jpg` do item (o quadro com o título grande). Anote no `tiktok_ok.json` qual quadro escolheu (ex.: `"quadro 0,8 s"`).

**Passo 52.** **Configurações do post:**
- Quem pode ver: **Todos**.
- Comentários: **ligados**.
- Divulgação de conteúdo comercial / conteúdo de marca: **desligado** (a HP ainda não faz publicidade paga nem afiliado — ver manual 13, FUTURO).
- **Rótulo de conteúdo gerado por IA:** ligar quando o vídeo tiver **voz sintética** (Piper, nos canais Destinos, Receitas, Carros e Filmes). A regra de quando o rótulo é obrigatório muda: **conferir na página oficial**. Futebol **nunca** tem voz sintética.

**Passo 53.** **Agendar:** ligue a opção **Agendar** e escolha a **data** e a **hora** exatas do TikTok (`$hTik` do passo 50: `horarios.tiktok` do `pedido.json` ou, sem ele, `publicar_em`). Confira que o fuso mostrado é o de Brasília. O TikTok tem prazo mínimo e máximo para agendar (**conferir na página oficial**; costuma ser de alguns minutos até alguns dias à frente). Se o horário já passou ou está perto demais para agendar, use **Publicar agora** só se o horário do plano já chegou; senão, escolha o horário possível mais próximo e anote em `observacoes`.

**Passo 54.** Clique em **Agendar** (ou **Publicar**). Depois abra a **lista de posts** do TikTok Studio e confira que o vídeo aparece como agendado, **na conta certa, na hora certa**. Só então grave o `tiktok_ok.json` na pasta do item. Modelo em PowerShell (troque os valores):

```powershell
$ok = [ordered]@{
  post_id = $p.item
  conta = $p.conta
  acao = "agendado"
  agendado_para = $hTik
  legenda_usada = $p.redes.tiktok.texto_final
  arquivo_enviado = "final.mp4"
  capa_escolhida = "quadro 0,8 s"
  conferido_lista_agendados = $true
  link = $null
  feito_por = "claude"
  feito_em = (Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz")
  observacoes = ""
} | ConvertTo-Json
Set-Content -Path "$item\tiktok_ok.json" -Value $ok -Encoding UTF8
```

(O PowerShell 5.1 grava UTF-8 com uma marca invisível no começo, o "BOM"; o app lê normalmente, porque a `hpbase` abre os JSON com `utf-8-sig`.)

**Passo 55.** Anote no histórico do item:

```powershell
Add-Content -Path "$item\historico.log" -Value ("{0} claude: tiktok agendado para {1}" -f (Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz"), $hTik) -Encoding UTF8
```

### Bloco I — Pinterest (só Receitas, Carros e Destinos; hoje o **Claude**, pela página oficial)

**Passo 56.** O Pinterest só é usado nos canais `receitas`, `carros` e `destinos`. Liste os itens esperando Pinterest (mesmo comando do passo 45, trocando `tiktok` por `pinterest` e `tiktok_ok.json` por `pinterest_ok.json`).

**Passo 57.** Abra o Chrome no perfil já logado e vá para a página de criar Pin do Pinterest (endereço atual: `https://www.pinterest.com/pin-creation-tool/` — **conferir na página oficial**). As mesmas regras do passo 47 valem aqui: login, senha, código, CAPTCHA ou termos novos → **parar** e abrir ticket.

**Passo 58.** Confira a conta ativa (tem que ser a do canal) e preencha:
- **Imagem:** o `pin.jpg` da pasta do item (arte vertical 2:3 feita pelo Designer, manual 07; tamanhos recomendados: **conferir na página oficial**).
- **Título:** `redes.pinterest.titulo` do `post.json`.
- **Descrição:** `redes.pinterest.descricao` (com "Valores aproximados…" se citar preço).
- **Texto alternativo:** `redes.pinterest.texto_alternativo`.
- **Link de destino:** `redes.pinterest.link`; se vier `null`, a página de links `https://sites.google.com/view/hpcanais`. **Nunca** link de afiliado (manual 13 é FUTURO).
- **Pasta (board):** uma pasta **já existente** do canal que combine com o assunto (ex.: "Bolos fáceis"). Não achou pasta adequada: use a pasta geral do canal e anote em `observacoes` do `pinterest_ok.json` a sugestão de pasta nova (quem cria pasta nova é o plantão, com calma, não no meio da publicação).

**Passo 59.** Escolha **Publicar mais tarde** com a data e a hora do Pinterest (`horarios.pinterest` do `pedido.json` ou `publicar_em`) e confirme. Abra a lista de Pins agendados e confira.

**Passo 60.** Grave o `pinterest_ok.json` (modelo da seção 2.9, igual ao passo 54 trocando os campos) e anote no `historico.log`. Quando a HP tiver acesso liberado à **API oficial do Pinterest**, este bloco passa para o app **(a criar)** e o Claude deixa de fazer.

### Bloco J — Conferência depois do post (o app faz sozinho)

**Passo 61.** Até **2 minutos** depois de receber `publicado`, o app pede à API a lista dos **5 posts mais recentes** da conta:
- Instagram: `GET /<ig_id>/media?fields=id,caption,timestamp,permalink,media_product_type&limit=5`
- Threads: `GET /<threads_user_id>/threads?fields=id,text,timestamp,permalink&limit=5`
- Facebook e YouTube: a consulta equivalente da etapa 4 **(em andamento no PC — não mexer)**.

(O `<ig_id>` e o token saem da configuração do script. Nada disso aparece na tela nem no log.)

**Passo 62.** O app confirma que o `media_id` recebido **está** na lista, que a **legenda** bate com a do `post.json` (comparação do passo 68) e que o `timestamp` é de agora. Grava o `permalink` e `conferido_na_api: true` no `publicado.json`.

**Passo 63.** Se o `media_id` **não** aparece na lista em até **10 minutos**, o app marca `"conferido_na_api": false`, registra `WARNING` no log e tenta a conferência de novo aos 20 e aos 30 minutos. Se continuar sumido aos 30 minutos: ticket P1 (pode ser post removido pela rede ou conta com restrição). **Não** republica sozinho nesse caso: um post "sumido" pode estar só atrasado na listagem, e republicar criaria duplicado.

**Passo 64.** Conferência extra de duplicado, uma vez por dia (fim do dia, passo 96): o app olha os 25 últimos posts de cada conta e procura **duas legendas iguais no mesmo dia**. Achou → ticket **P0** (ver passo 94). Não apagar sozinho.

### Bloco K — Reenvio seguro quando dá "tempo esgotado" (o app faz sozinho) — ticket H

**Passo 65.** O que é **tempo esgotado**: o app mandou publicar e a rede **não respondeu** a tempo (internet lenta, servidor da Meta ocupado). O problema é que, às vezes, **a rede publicou mesmo sem responder**. Se o app simplesmente tentar de novo, sai **duplicado** — e post duplicado derruba alcance e passa imagem de conta amadora.

**Passo 66.** **Regra de ouro: nunca tentar de novo sem antes conferir na API se o post já saiu.**

**Passo 67.** A conferência é a mesma do passo 61: pedir os **5 posts mais recentes** da conta (`GET /<ig_id>/media` com `caption` e `timestamp`, `limit=5`; no Threads, `/<threads_user_id>/threads` com `text` e `timestamp`).

**Passo 68.** Como o app decide se "é o mesmo post" (os dois testes têm que passar):
1. **Legenda:** pega a legenda do `post.json` e a de cada um dos 5 posts; tira espaços repetidos, quebras de linha e diferença de maiúscula/minúscula; compara os **primeiros 100 caracteres**. Iguais = passa.
2. **Horário:** o `timestamp` do post na rede é **igual ou depois** da hora da 1ª tentativa **menos 2 minutos**, e **antes** de agora.

Se **achou** um post que passa nos dois testes → o post **já saiu**: o app grava `status: "publicado"`, o `media_id` e o `permalink` desse post, escreve no histórico `"tempo esgotado, mas já estava no ar — NÃO reenviado"` e **não** tenta de novo.

**Passo 69.** Se **não achou**, o app espera e tenta de novo, **conferindo antes de cada tentativa**. São **4 tentativas no total**, com espera crescente:

| Tentativa | Quando | Antes de tentar |
|---|---|---|
| 1ª | Na hora do plano (H) | — |
| 2ª | H + tempo da 1ª + **1 minuto** de espera | Confere os 5 últimos posts |
| 3ª | + **5 minutos** de espera | Confere os 5 últimos posts |
| 4ª | + **15 minutos** de espera | Confere os 5 últimos posts |

No pior caso, o item fica uns **22 a 25 minutos** tentando. Cada tentativa vira uma linha no `historico.log` e uma entrada no campo `tentativas` do `publicado.json`.

**Passo 70.** Se o tempo esgotou **depois** de o contêiner ficar pronto (`FINISHED`), a nova tentativa **reaproveita o mesmo contêiner** (enquanto ele não vencer), em vez de subir o vídeo de novo. Isso economiza tempo e diminui o risco de dois posts.

**Passo 71.** Depois da **4ª** tentativa sem sucesso (e sem achar o post na conferência): o app grava o `erro.json` (modelo na seção 2.13), move a pasta para `99_erros` **mantendo o `publicado.json`** com as redes que já saíram, e abre ticket (P0 se o item for P0; P1 nos outros casos).

**Passo 72.** **Reenvio manual** (depois de o problema ser resolvido, por exemplo a internet voltar). O comando faz **a mesma conferência antes** de tentar:

```powershell
& $py .\publicador_meta.py reenviar P1_2026-10-06_1830_gta_rockstar-quinta-ig
```

(`reenviar <id>` é **(a criar — ticket H)**; o `<id>` é o nome do arquivo da fila sem o `.json`.) Ele só mexe na rede daquele `id`; nunca republica as redes que já estão `publicado`.

**Passo 73.** **Modo simular** — obrigatório antes de ligar o reenvio de verdade no PC (e sempre que mexerem no script):

```powershell
& $py .\publicador_meta.py reenviar P1_2026-10-06_1830_gta_rockstar-quinta-ig --simular
```

**(a criar — ticket H)**. No modo simular, o script faz a conferência (só leitura) e **mostra o que faria** ("já está no ar, não reenviaria" ou "não achei, reenviaria"), **sem publicar nada**.

**Passo 74.** **Nunca** rode o `reenviar` do mesmo `id` em duas janelas ao mesmo tempo. O script deve travar por `id` (arquivo `fila_api\<id>.lock`, **a criar**); se a trava existir, ele recusa e diz quem está com ela.

### Bloco L — Stories: de divulgação e clicável (sempre DEPOIS do post)

**Passo 75.** Regra fixa: **story só depois do post**. "Depois" quer dizer: o post está `publicado` **e** `conferido_na_api: true` **e** tem `permalink`. Story de algo que ainda não está no ar leva o seguidor a um post que não existe — isso não acontece nunca.

**Passo 76.** **Story de divulgação (pela API):** quando `story.divulgacao` do `pedido.json` é `true` (ou não existe e o item é reel/carrossel do Instagram), o `publicador_meta.py` **(existe)** já solta o story **depois** do post dele — esse comportamento já funciona e **não deve ser mudado**. O Publicador só confere no `publicado.json` que o horário do story é **maior** que o horário do post.

**Passo 77.** **Story clicável (pelo emulador):** quando `story.clicavel` do `pedido.json` é `true`, depois da conferência do Instagram o app cria o pedido `H:\HypadoLocal\emulador\fila_story\<post_id>.json` (modelo na seção 2.10). Quem cria esse pedido automaticamente, no fluxo da largada, é o `fila_story_com_post.py`, chamado pelo `largada_canais.py` (ticket H; se o `fila_story_com_post.py` não existir no PC, ele é **(a criar)**).

**Passo 78.** O robô do emulador, `story_post.py` **(a criar — ticket F)**, pega os pedidos da fila, um de cada vez:
1. Pega a trava do trabalho pesado com `ignorar_horario=True` (o story pode sair a qualquer hora, inclusive das 18h às 22h30, desde que leve **no máximo 5 minutos**).
2. Liga o emulador: `H:\HypadoLocal\android\ligar_emulador.ps1` **(existe)** (boot frio).
3. Abre o **app oficial** do Instagram, troca para a conta do pedido (toca no nome da conta no alto do perfil e escolhe o @; **se pedir senha ou código → para**).
4. Abre o post pelo link.
5. Toca em **Enviar** → **Adicionar ao story** → publica no seu story.
6. Se o pedido tem `destaque`, abre o próprio story, vai até o de agora e adiciona ao destaque indicado.
7. Marca como feito: `python scripts\story_clicavel.py feito <post_id> --link <url>` **(existe)**.
8. Desliga o emulador: `H:\HypadoLocal\android\desligar_emulador.ps1` **(existe)**.

Para ver a tela do emulador numa conferência: `H:\HypadoLocal\android\tela.ps1` **(existe)**; para ver os botões da tela: `ui.py` **(existe)**.

**Passo 79.** **Sem rajada:** **1 story clicável por post**, nunca vários seguidos. Entre dois stories clicáveis da **mesma conta**, o robô espera no mínimo **15 minutos** (padrão da casa; o Estrategista pode aumentar). Se houver fila acumulada, ela anda devagar — é de propósito.

**Passo 80.** **Parar ao primeiro aviso da Meta.** Se aparecer no app oficial qualquer aviso do tipo "Tente novamente mais tarde", "Ação bloqueada", "Restringimos certas atividades", "Confirme que é você": o robô **para tudo** do emulador, desliga, **não** tenta de novo por **24 horas** e abre ticket **P0**. Nenhuma pessoa nem o Claude "força" o story nesse período.

**Passo 81.** Para mandar à mão um pedido de story clicável (emergência; normalmente o app faz):

```powershell
$pedido = [ordered]@{
  post_id = "P1_2026-10-06_1830_gta_rockstar-quinta"
  conta = "@hpgta6"
  canal = "gta"
  link = "https://www.instagram.com/reel/EXEMPLO1/"
  publicado_em = "2026-10-06T18:31:12-03:00"
  titulo = "Rockstar mexeu no site de novo"
  destaque = "Notícias"
} | ConvertTo-Json
Set-Content -Path "H:\HypadoLocal\emulador\fila_story\P1_2026-10-06_1830_gta_rockstar-quinta.json" -Value $pedido -Encoding UTF8
```

Só faça isso com o `link` de um post **confirmado** no ar (passo 75).

**Passo 82.** **Story interativo das 16h do GTA e contagem regressiva:** são pedidos do **plano** (manual 12), não de um post. A arte vem de `lotes\<dia>_estaticos.json` (Designer, manual 07); o `story_post.py` **(a criar — ticket F)** publica pelo emulador com a figurinha de **enquete** (pergunta com **no máximo ~25 caracteres** e as opções: campo `enquete` do `post.json`, escrito pelo Redator, manual 08) e salva no destaque **Enquetes**. O Publicador confere depois: saiu às 16h (±10 min), na @hpgta6, com a enquete e no destaque certo.

### Bloco M — Fechar o item: mover para `07_postados` e aviso "no ar"

**Passo 83.** O app olha o `publicado.json`. O item está **pronto para fechar** quando **toda** rede da lista `redes` do `pedido.json` está em um destes estados: `publicado` (com `conferido_na_api: true`), `agendado` (YouTube, com `publishAt` conferido), `agendado_pelo_claude` (com `tiktok_ok.json` / `pinterest_ok.json`) ou `rede_inativa`.

**Passo 84.** O app move a pasta de `06_agendados` para `07_postados`. À mão (emergência):

```powershell
Add-Content -Path "$item\historico.log" -Value ("{0} publicador: todas as redes ok; pasta movida para 07_postados" -f (Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz")) -Encoding UTF8
Move-Item -LiteralPath $item -Destination "$esteira\07_postados\"
```

**Passo 85.** O app atualiza o `agendados.json` que o plantão já usa **(existe)** com os links do item, e a fila local do painel (`scripts\painel_local.py` **(existe)**), para o painel mostrar o post no ar.

**Passo 86.** **Aviso "no ar" no WhatsApp** (uma das 3 únicas coisas permitidas no WhatsApp). O app junta os itens do **mesmo lote** (`aviso_lote` do `pedido.json`: `manha`, `tarde`, `noite` ou `p0`; o título de cada item é o `aviso.titulo_curto` do `post.json`) e monta **uma** mensagem com os links, seguindo o texto-modelo de `G:\Meu Drive\Hypado\06 Projeto\AVISO.md` **(existe)**. A mensagem **sempre começa com `*Claude - *`**.

**Passo 87.** **Quando** o aviso sai: depois que o **último** item do lote foi ao ar (ou foi para `99_erros`). No máximo **1 aviso por lote por grupo**. Item `P0` pode ter aviso próprio, na hora. Se o `AVISO.md` disser outra frequência, vale o `AVISO.md`.

**Passo 88.** **Para onde** vai: só o grupo `HP | Comissão 🚀` e os grupos da lista `HP | Grupos`. O app grava o JSON em `H:\HypadoLocal\whatsapp_fila\` (modelo na seção 2.11) e o **enviador local** **(a criar — ticket E)** manda, sem deixar a janela na frente e com volume baixo. **Hoje**, enquanto o enviador está em modo sombra, o plantão do Claude manda o aviso e o app **só monta o texto** para comparar.

**Passo 89.** Conferência do aviso (o app faz; à mão numa emergência): o texto começa com `*Claude - *`? Tem **todos** os links dos itens do lote que estão em `07_postados`? Nenhum link de item que foi para `99_erros`? Grupo está na lista permitida? Qualquer "não" → o aviso não sai e abre ticket.

**Passo 90.** Anote no `historico.log` do item: `aviso_no_ar na_fila` e, depois, `aviso_no_ar enviado`.

### Bloco N — Quando algo dá errado

**Passo 91.** **Abrir ticket** (é assim que se pede ajuda; **não** pelo WhatsApp). Use o `tickets.py` **(existe)**, área `publicacao`:

```powershell
& $py .\tickets.py --help
```

Siga a sintaxe que o `--help` mostrar no PC. O ticket fica em `G:\Meu Drive\Hypado\08 Empresa\tickets\publicacao\novo\`. Escreva: **título curto** ("TikTok pediu código na @hp.carros"), **item**, **rede**, **o que apareceu** (texto da mensagem de erro, **sem** token), **o que já foi tentado**, **prioridade** (P0 se tem post urgente parado). **Nunca** cole print ou texto que mostre token, senha ou código.

**Passo 92.** **P0 parado:** se um `P0` não saiu no Instagram em **10 minutos** depois do `aprovado.json`, abrir ticket **P0** na hora e continuar tentando as outras redes.

**Passo 93.** **Token vencido ou inválido** (a API responde com erro de autorização, por exemplo código 190 na Meta): **não** abrir a pasta `segredos\`, **não** tentar gerar token novo. O app para aquela conta, move os itens dela para esperar e abre ticket **P0** para o Antônio renovar a autorização pela página oficial da Meta.

**Passo 94.** **Post duplicado ou na conta errada:** **não apague sozinho** (apagar é irreversível e a API do Instagram nem oferece isso para todo tipo de post). Abra ticket **P0** com os dois links. Quem decide o que apagar é o Antônio.

**Passo 95.** **Arquivo com defeito** descoberto na publicação (vídeo recusado pela rede por formato, capa errada): **não** conserte. Passo 17 com o motivo e o erro exato da rede; o item volta para o Editor (manual 03) ou Designer (manual 07) pela regra do Revisor.

### Bloco O — Fim do dia (o app faz; o Claude confere em 2 minutos)

**Passo 96.** Nada vencido parado:

```powershell
Get-ChildItem "$esteira\06_agendados" -Directory | Where-Object { $_.Name -match "_(\d{4}-\d{2}-\d{2})_" -and ([datetime]$Matches[1]) -lt (Get-Date).Date } | Select-Object Name
```

Tem que sair **vazio**. Item de dia passado ainda em `06_agendados` = ticket.

**Passo 97.** Todo item de `99_erros` do dia tem `erro.json` e ticket.

**Passo 98.** Contagem do dia por canal e rede comparada com o plano (o app mostra no painel; ver também o relatório do Analista, manual 11). Diferença maior que **10%** para menos → anotar o motivo no ticket do dia.

**Passo 99.** Nenhum segredo no log (o app roda sozinho; à mão):

```powershell
Select-String -Path "$logs\publicador_$(Get-Date -Format yyyy-MM-dd).log" -Pattern "EAA[A-Za-z0-9]{20,}|access_token=[^*]|Bearer [A-Za-z0-9]|ya29\.|AIza[0-9A-Za-z_-]{30,}"
```

Tem que sair **vazio**. Se aparecer qualquer linha: ticket **P0** de segurança, **sem** copiar a linha para o ticket (só o nome do arquivo e o número da linha).

**Passo 100.** Emulador desligado no fim do dia (se não houver story na fila): `H:\HypadoLocal\android\desligar_emulador.ps1`.

---

## 4. Regras que nunca se quebram

### 4.1 Segurança
1. **Nunca** digitar senha, código (SMS, e-mail, autenticador), criar conta, aceitar termos ou contornar CAPTCHA. Apareceu? **Para** e abre ticket (passo 47).
2. **Nunca** abrir, ler, copiar, imprimir ou colar token. Tokens ficam em `H:\HypadoLocal\segredos\` e só o script lê (função `ler_segredo` da `hpbase`, que nunca mostra o valor).
3. **Só** API oficial, app oficial no emulador ou página oficial no Chrome. **Proibido** biblioteca que imita protocolo de rede social (instagrapi, Baileys e parecidas).
4. **Parar ao primeiro aviso da Meta** no emulador (passo 80): 24 h sem story clicável naquela conta.

### 4.2 Publicação
5. **Sem `aprovado.json` com `veredito: "aprovado"`, nada sai.** Nem P0.
6. **Nunca republicar sem conferir na API** se o post já saiu (bloco K). Zero duplicado é regra, não meta.
7. **Conta errada = parar.** Conferir `canal` × `conta` antes de toda publicação (passo 15).
8. **Story só depois do post** confirmado com `permalink` (passo 75). **1 story clicável por post**, sem rajada (passo 79).
9. **O Publicador não edita** vídeo, capa, legenda nem horário do plano. Achou erro → devolve (passo 17).
10. **Nunca republicar** as redes que já estão `publicado` quando uma rede do mesmo item falhar.
11. **Nunca apagar post** sozinho (passo 94).
12. **Não mexer** na etapa 4 (Facebook e YouTube pela API), na redução de arquivos do painel público e na auditoria da API do YouTube — estão em andamento no PC.
13. **Não mudar** o que já funciona no `publicador_meta.py` (fila, story depois do post). Coisa nova entra como opção nova (`reenviar`, `--simular`), sem mudar o comportamento atual.

### 4.3 Conteúdo (conferência final, mesmo já revisado)
14. **Crédito do criador sempre**, em todas as redes publicadas (passo 18).
15. **Valor em dinheiro leva "Valores aproximados…"** (passo 19).
16. Nada do **Flow Games**; nada de **vazamento** de GTA 6; **sem trailer puro**; futebol **sem imagem de transmissão de TV** e **nunca com narração sintética**. Se o Publicador notar qualquer uma dessas coisas, **não publica**, mesmo com `aprovado.json`, e abre ticket P0 para o Revisor.
17. Nada de link de afiliado, "publi" ou conteúdo de marca (manual 13 é **FUTURO**).

### 4.4 Limites de texto (valores de referência — **conferir na página oficial**, mudam)

| Rede | Campo | Referência usada pela HP | O que fazer se passar |
|---|---|---|---|
| Instagram | legenda | até 2.200 caracteres; até 30 hashtags (a HP usa 3 a 6) | Devolver ao Redator |
| Threads | texto | até 500 caracteres | Devolver ao Redator |
| TikTok | descrição | limite atual da página (a HP usa até ~300) | Devolver ao Redator |
| YouTube | título | até 100 caracteres | Devolver ao Redator |
| YouTube | descrição | até 5.000 caracteres | Devolver ao Redator |
| Pinterest | título / descrição | até 100 / até 500 caracteres | Devolver ao Redator |

### 4.5 WhatsApp
18. WhatsApp **só** para 3 coisas: resumo do dia anterior, **aviso "no ar" com links** e resumo de sábado. Erro, dúvida e pedido de ajuda vão por **ticket**.
19. Toda mensagem começa com `*Claude - *`.
20. Só os grupos `HP | Comissão 🚀` e os da lista `HP | Grupos`. Janela **nunca** em primeiro plano.

---

## 5. Critérios de qualidade com nota

Cada item publicado recebe uma nota de 0 a 10 **por critério**. A nota do item é a **média**. Meta: média do dia **≥ 9**. Qualquer critério com nota **0** vira ticket P0, mesmo que a média fique alta.

| Critério | Nota 10 | Nota 7 | Nota 5 | Nota 0 |
|---|---|---|---|---|
| **Pontualidade** | Todas as redes no ar a até ±5 min do plano (P0: ≤ 10 min do `aprovado.json`) | Atraso de 6 a 30 min em alguma rede | Atraso de 31 a 120 min | Mais de 2 h de atraso sem decisão do Estrategista, ou não saiu sem motivo registrado |
| **Conta certa** | 100% das redes na conta do canal | — | — | Qualquer post em conta de outro canal |
| **Sem duplicado** | Nenhuma duplicação; conferência na API antes de todo reenvio | — | Reenvio feito sem registro da conferência, mas sem duplicar | Post duplicado |
| **Texto certo por rede** | Legenda/título idênticos ao `post.json`, com crédito e aviso de valor quando precisa | 1 diferença pequena de formatação (quebra de linha) | Hashtag ou emoji faltando | Sem crédito, texto de outro post ou valor sem "Valores aproximados…" |
| **Registro** | `publicado.json` completo (media_id, permalink, horários, tentativas, `conferido_na_api: true`) e `historico.log` com todas as linhas | 1 campo não essencial faltando | Sem `permalink` em alguma rede | Sem `publicado.json` |
| **Stories** | Story de divulgação e clicável depois do post, 1 por post, destaque certo | Story clicável atrasou mais de 1 h | Destaque errado | Story antes do post, rajada, ou insistência depois de aviso da Meta |
| **Aviso "no ar"** | Mensagem única do lote, começa com `*Claude - *`, todos os links, grupo permitido | 1 link faltando | Aviso fora do lote (mensagens soltas demais) | Mensagem sem `*Claude - *`, grupo errado ou WhatsApp usado para outra coisa |
| **TikTok / Pinterest (Claude)** | Agendado na hora certa, conferido na lista, `*_ok.json` completo | `*_ok.json` sem `capa_escolhida` ou `observacoes` | Agendado com até 30 min de diferença sem anotar motivo | Agendado sem conferir ou `*_ok.json` gravado sem ter agendado |
| **Segurança** | Nenhum token, senha ou código tocado ou mostrado | — | — | Qualquer token em log/tela, qualquer login/código digitado |

Classificação (igual ao Revisor, manual 09): **≥ 9 Excelente**; **7 a 8,9 Bom**; **5 a 6,9 Médio** (abrir ticket de melhoria do processo); **< 5 Razoável** (parar de publicar sozinho e revisar o processo com o plantão).

---

## 6. Erros comuns e o que fazer

| # | O que aparece | Por que acontece | O que fazer |
|---|---|---|---|
| 1 | Tempo esgotado (timeout) | Internet lenta ou rede ocupada | Bloco K: conferir nos 5 últimos posts; se não saiu, tentar com espera de 1, 5 e 15 min; depois `99_erros` + ticket |
| 2 | Contêiner com status `ERROR` | Vídeo fora do padrão (codec, tamanho, proporção, duração) | Não reenviar igual. Passo 17 com o erro exato; volta ao Editor (manual 03) |
| 3 | Contêiner `EXPIRED` | Contêiner criado e não publicado a tempo | Criar contêiner novo (só depois de conferir que não saiu) |
| 4 | Erro de autorização (ex.: código 190) | Token vencido ou autorização retirada | Passo 93: parar a conta, ticket P0 para o Antônio. Não abrir `segredos\` |
| 5 | Limite de publicação da API atingido | Muitas publicações em 24 h (ou algo publicando em dobro) | Passo 30: segurar P2, ticket P0 para investigar |
| 6 | Threads recusa texto | Acima do limite de caracteres | Devolver ao Redator (passo 17) |
| 7 | YouTube: cota esgotada | Cota diária do projeto acabou | Passo 43: remarcar para depois que a cota zerar |
| 8 | YouTube: vídeo fica privado | Projeto de API ainda não auditado | Passo 42: rede inativa até a auditoria; seguir processo atual |
| 9 | TikTok/Pinterest pede login, código ou CAPTCHA | Sessão do navegador venceu ou verificação de segurança | Passo 47: **parar**, ticket; nunca digitar nada |
| 10 | TikTok não deixa agendar na hora pedida | Fora do prazo mínimo/máximo de agendamento | Passo 53: horário possível mais próximo, anotar em `observacoes` |
| 11 | Emulador não liga ou trava | Boot lento, falta de memória | Desligar (`desligar_emulador.ps1`), esperar 2 min, ligar de novo 1 vez; falhou de novo → ticket; o post continua no ar, só o story atrasa |
| 12 | "Ação bloqueada" / "Tente mais tarde" no emulador | Limite de ações da Meta | Passo 80: parar 24 h, ticket P0 |
| 13 | Emulador na conta errada | Troca de conta não concluída | Robô confere o @ antes de compartilhar; se errado, volta, troca de novo; 2 falhas → para e abre ticket |
| 14 | `post.json` de outro item / conta de outro canal | Erro de cópia em etapa anterior | Passo 17 |
| 15 | Item sem `aprovado.json` em `06_agendados` | Alguém moveu a pasta à mão | Passo 17; nunca publicar |
| 16 | Post "sumido" (não aparece na lista da API) | Atraso na listagem ou remoção pela rede | Passo 63: conferir aos 10, 20 e 30 min; não republicar; ticket P1 |
| 17 | Post duplicado descoberto | Reenvio sem conferência, ou duas janelas | Passo 94: ticket P0 com os dois links; não apagar sozinho; investigar a trava por `id` (passo 74) |
| 18 | Aviso "no ar" com link faltando | Item do lote ainda não fechou | Esperar o último item do lote (passo 87) |
| 19 | Horário do plano já passou há mais de 2 h (P1/P2) | Fila atrasou | Passo 20: Estrategista escolhe novo horário |
| 20 | Pasta presa em `06_agendados` há mais de 24 h | Falta `tiktok_ok.json`/`pinterest_ok.json` ou rede em erro | Ver `publicado.json`; fazer o que falta ou mover para `99_erros` com ticket |

---

## 7. O que o app faz sozinho x o que o Claude decide

| Tarefa | App sozinho | Claude | Observação |
|---|---|---|---|
| Conferir entrada (aprovado, post.json, contas, arquivos, crédito, valor) — passos 11 a 19 | 100% | 0% | Regras fixas, sem julgamento |
| Respeitar horário, limite do dia e intervalo — passos 20 a 23 | 90% | 10% | Claude/Estrategista só decide novo horário quando atrasou mais de 2 h |
| Publicar Instagram e Threads — blocos D e E | 100% | 0% | `publicador_meta.py` (existe) |
| Publicar Facebook e YouTube — blocos F e G | 100% (quando a etapa 4 for ligada) | 0% | Em andamento no PC |
| Conferência na API e reenvio seguro — blocos J e K | 100% | 0% | Ticket H |
| TikTok — bloco H | 0% | 100% | Sem API; Claude pelo Chrome, em lote |
| Pinterest — bloco I | 0% hoje (100% quando houver API) | 100% hoje | Só 3 canais |
| Story de divulgação (API) | 100% | 0% | Já existe |
| Story clicável e story interativo (emulador) | 95% | 5% | Claude só olha a tela quando o robô para com dúvida |
| Mover pastas, atualizar `agendados.json` e painel | 100% | 0% | — |
| Montar e enviar aviso "no ar" | 100% (quando o enviador local sair do modo sombra) | 0% | Hoje o plantão envia |
| Exceções (duplicado, conta errada, aviso da Meta) | 0% (só detecta e para) | 100% da decisão (com o Antônio) | Sempre por ticket |

**Estimativa geral do cargo:** hoje **≈ 75% app / 25% Claude** (o TikTok, o Pinterest e o Facebook/YouTube pesam). Com a etapa 4 ligada: **≈ 85% / 15%**. Com API do Pinterest e o enviador de WhatsApp ligado: **≈ 90% / 10%** (o que sobra é o TikTok pelo Chrome e as exceções).

---

## 8. Ferramentas existentes que já fazem cada passo

| Passo(s) | Ferramenta | Situação |
|---|---|---|
| 1–8 | PowerShell; tela do app `http://127.0.0.1:8770`; CLI `hp` (`hp --help`) | existe (etapa 1) |
| 3, 9–19, 83–84 | Módulo `esteira` (pastas `01_pedidos` → `07_postados`, `99_erros`) | **(a criar — etapa 3)** |
| 17, 90, histórico | `hpbase` (`ler_json`, `escrever_json`, `anexar_linha`, `obter_logger`, `mascarar`) | existe (base da nuvem) |
| 24–35, 61–62, 76 | `scripts\publicador_meta.py` + fila `H:\HypadoLocal\fila_api\` | existe |
| 36–44 | Etapa 4 do app (Facebook e YouTube pela API) | em andamento no PC — não mexer |
| 45–55 | Chrome (TikTok Studio) + `tiktok_ok.json` | processo atual do Claude |
| 56–60 | Chrome (Pinterest) + `pinterest_ok.json`; API oficial do Pinterest | Chrome hoje; API **(a criar)** |
| 65–71 | Reenvio seguro dentro do `publicador_meta.py` | **(a criar — ticket H)** |
| 72–73 | `publicador_meta.py reenviar <id>` e `--simular` | **(a criar — ticket H)** |
| 74 | Trava por `id` (`fila_api\<id>.lock`) | **(a criar)** |
| 77 | `largada_canais.py` → `fila_story_com_post.py` | ticket H (conferir no PC; se faltar, **a criar**) |
| 78–82 | `story_post.py` | **(a criar — ticket F)** |
| 78 | `story_clicavel.py feito <post_id> --link <url>`; fila `H:\HypadoLocal\emulador\fila_story\` | existe |
| 78 | `H:\HypadoLocal\android\` — `env.ps1`, `ligar_emulador.ps1`, `desligar_emulador.ps1`, `tela.ps1`, `ui.py`, `digitar.py` | existe |
| 78 | `TravaPesada(..., ignorar_horario=True)` da `hpbase` | existe |
| 82 | `lotes\<dia>_estaticos.json` (artes do dia) + `scripts\estaticos.py` | existe |
| 85 | `agendados.json`; `scripts\painel_local.py` | existe |
| 86–89 | `06 Projeto\AVISO.md` (texto-modelo) | existe |
| 86–89 | Enviador local de WhatsApp + fila `H:\HypadoLocal\whatsapp_fila\` | **(a criar — ticket E)** |
| 91 | `scripts\tickets.py` (tickets em `08 Empresa\tickets\<area>\{novo,fazendo,travado,feito}`) | existe |

---

## 9. Testes de aceitação

O Publicador do app só assume uma rede depois de passar **todos** os testes abaixo **e** de **7 dias de modo sombra** (ver README). No modo sombra, o app faz tudo **menos** apertar "publicar": monta a fila, calcula horários, simula conferência e reenvio, monta o aviso, e o resultado é comparado com o que o plantão do Claude realmente fez. Nenhum teste acessa internet, emulador ou WhatsApp reais (usam um "falso" da API).

| Nº | Teste | Como | Passa se |
|---|---|---|---|
| T-01 | Item sem `aprovado.json` | 20 pastas em `06_agendados`, 5 sem aprovação | As 5 vão para `99_erros`; **0** publicadas |
| T-02 | Conta de outro canal | 10 `post.json` com 1 conta trocada | 10 de 10 barrados no passo 15 |
| T-03 | Crédito faltando | 10 itens, 3 sem crédito em alguma rede | 3 de 3 barrados; 7 seguem |
| T-04 | Valor sem aviso | 8 legendas com "R$", 4 sem "Valores aproximados" | 4 de 4 barradas |
| T-05 | Ordem de prioridade | Fila com 3 P0, 10 P1, 10 P2 misturados | Os 3 P0 saem primeiro; P1/P2 por horário |
| T-06 | Pontualidade (simulada) | 100 itens com relógio falso | ≥ 95 saem a ±5 min; P0 em ≤ 10 min |
| T-07 | Intervalo mínimo | 2 itens da mesma conta a 20 min um do outro | O 2º é empurrado para +60 min; P0 não é empurrado |
| T-08 | Tempo esgotado com post já no ar | API falsa: timeout na 1ª, mas o post aparece nos 5 últimos | **0** reenvios; status `publicado` com o `media_id` achado |
| T-09 | Tempo esgotado sem post no ar | API falsa: 3 timeouts e sucesso na 4ª | 4 tentativas, esperas de 1, 5 e 15 min (relógio falso), 1 post só |
| T-10 | 4 falhas seguidas | API falsa: 4 timeouts, nada nos 5 últimos | Pasta em `99_erros` com `erro.json` de 4 tentativas; redes já publicadas preservadas |
| T-11 | Duplicado (estresse) | 50 cenários aleatórios de timeout/sucesso | **0** duplicados em 50 |
| T-12 | Story antes do post | Post sem `permalink` e pedido de story | Story **não** é criado; 0 pedidos em `fila_story` |
| T-13 | Fechamento do item | Item com IG/Threads publicados, TikTok sem `tiktok_ok.json` | Pasta **não** vai para `07_postados`; com o arquivo, vai |
| T-14 | Aviso "no ar" | Lote com 4 itens (1 em `99_erros`) | 1 mensagem, começa com `*Claude - *`, 3 links, grupo permitido |
| T-15 | Nenhum segredo no log | Rodar T-01 a T-14 com token falso `EAA` + 30 letras no ambiente | Busca do passo 99 nos logs = **0** linhas |
| T-16 | `reenviar --simular` | 10 ids (5 já no ar, 5 não) | Mostra "não reenviaria" em 5 e "reenviaria" em 5; **0** publicações |
| T-17 | Trava por id | Dois `reenviar` do mesmo id ao mesmo tempo | O 2º recusa com mensagem clara |
| T-18 | Modo sombra de 7 dias | App em paralelo com o plantão | Nos 7 dias: mesma conta, mesmo texto e horário a ±5 min em **100%** dos itens comparados (mínimo 30 itens); 0 duplicados; 0 segredos em log |

---

## Glossário

- **API** — "porta de serviço" oficial que a rede social oferece para programas publicarem e lerem dados sem usar a tela.
- **Aprovado.json** — arquivo que o Revisor grava dizendo que o item pode sair.
- **Contêiner** — caixa temporária na Meta com vídeo + legenda, que depois é "publicada".
- **Emulador** — um celular Android "de mentira" rodando dentro do PC, com o app oficial do Instagram.
- **Esteira** — sequência de pastas por onde cada item passa (`01_pedidos` → `07_postados`).
- **Fila** — pasta onde cada arquivo é um trabalho esperando a vez.
- **media_id** — número que a rede dá a cada post.
- **Modo sombra** — o app faz tudo em paralelo sem publicar, para comparar com o que o Claude fez.
- **P0 / P1 / P2** — urgente / do dia / programado.
- **Permalink** — endereço público e fixo do post.
- **publishAt** — data e hora em que o YouTube torna público um vídeo agendado.
- **Reenvio seguro** — tentar de novo só depois de conferir que o post não saiu.
- **Story clicável** — o próprio post compartilhado no story: quem toca vai direto para o post.
- **Timestamp** — data e hora registradas pela rede.
- **Token** — "chave" que autoriza o script a publicar. Segredo: ninguém vê.
