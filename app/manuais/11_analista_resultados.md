# Manual 11 — Analista de resultados

> **Cargo:** Analista de resultados (métricas, indicadores, relatórios e metas de monetização)
> **Empresa:** Hypado (HP) — 6 perfis: GTA 6 | HP (@hpgta6), Futebol | HP (@hp.futebol), Filmes e Séries | HP (@hp.filmes), Receitas | HP (@hp.receitas), Carros | HP (@hp.carros), Destinos | HP (@hp.destinos)
> **Versão:** 1.0 — 30/09/2026
> **Pasta deste manual no PC:** `G:\Meu Drive\Hypado\06 Projeto\app\manuais\11_analista_resultados.md`
> **Quem vem antes:** 10 Publicador (o `publicado.json` diz o que foi ao ar) · **Quem vem depois:** 12 Estrategista de marketing (decide o que fazer com os números)
> **Objetivo nº 1 da empresa:** crescer e chegar à monetização o quanto antes. O Analista mostra, **com números iguais para todas as redes**, o que está trazendo seguidor e visualização, o que não está, e **quantos dias faltam** para cada canal monetizar em cada rede.

---

## Como ler este manual (para quem nunca fez isso)

- Escrito para uma pessoa **totalmente leiga**: não precisa saber estatística. Toda conta está explicada com um exemplo resolvido.
- Os comandos vão em blocos cinza, para colar no **PowerShell**. Onde houver `<dia>`, troque pela data no formato `AAAA-MM-DD` (ex.: `2026-10-06`).
- Marcações: **(existe)** já funciona no PC · **(a criar)** ainda não existe (o manual já diz como deve ser) · **(em andamento no PC — não mexer)** outra frente está fazendo · **(conferir na página oficial)** regra de rede social que muda; olhe a página oficial antes de confiar no número.
- Hora sempre de **Brasília**.
- **Números de exemplo** (seguidores, views etc.) neste manual são **inventados** para ensinar a conta. Nunca use como dado real.

### Preparação do PowerShell (uma vez por janela)

```powershell
$py      = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
$scripts = "G:\Meu Drive\Hypado\scripts"
$app     = "G:\Meu Drive\Hypado\06 Projeto\app\hp_studio_nuvem"
$met     = "H:\HypadoLocal\metricas"
$logs    = "H:\HypadoLocal\app\logs"
Set-Location $app
```

Confira: `& $py --version` tem que mostrar `Python 3.12.x`.

---

## 1. Objetivo do cargo

### 1.1 Em uma frase

**Todo dia às 6h**, fotografar os números de todas as contas e de todos os posts em todas as redes, transformar esses números em **indicadores com a mesma fórmula para todo mundo**, comparar (canal, rede, formato, horário), mostrar a **distância até a monetização** e entregar tudo mastigado ao **Estrategista** (manual 12), ao **painel** e ao **resumo do WhatsApp**.

### 1.2 O que o Analista entrega

1. **Foto diária** (JSON) de cada conta em cada rede, em `H:\HypadoLocal\metricas\<dia>\`.
2. **Indicadores do dia** (`indicadores_<dia>.json`): seguidores, ganho, views, alcance, retenção, salvamentos, compartilhamentos, taxa de engajamento, conversão em seguidores, índice de desempenho de cada post.
3. **Relatório diário** (até 6h45) e **texto do resumo do dia anterior** para o WhatsApp.
4. **Relatório semanal** (sábado até 7h) e **texto do resumo de sábado** para o WhatsApp.
5. **Arquivo para o Estrategista** (`para_estrategista_<semana>.json`), com os comparativos prontos para as regras de decisão.
6. **Painel de metas de monetização**: por canal e rede, quanto falta e em quantos dias bate no ritmo atual.
7. **Alertas**: queda forte, post sumido, coleta faltando, número estranho.

### 1.3 Metas do próprio Analista

| Indicador | Meta |
|---|---|
| Coleta das 6h concluída | até **6h20** em ≥ 95% dos dias |
| Posts de `07_postados` dos últimos 7 dias medidos | **≥ 98%** |
| Diferença entre o número do JSON e o número da tela oficial (amostra semanal de 3 posts por rede) | **≤ 2%** |
| Relatório diário pronto | até **6h45** |
| Relatório semanal pronto | sábado até **7h00** |
| Segredos (token) em arquivo de métrica, relatório ou log | **0** |

### 1.4 O que o Analista NÃO faz

- **Não decide** o que postar, quanto, onde ou quando. Ele **recomenda com números**; quem decide é o **Estrategista** (manual 12).
- **Não publica** nada, **não responde** comentário, **não mexe** em configuração de conta.
- **Não faz login**, não digita senha nem código, não aceita termos, não contorna CAPTCHA, **não lê token**.
- **Não "arruma" número.** Se o número parece errado, marca como suspeito e explica; nunca edita o dado bruto.

### 1.5 De onde vem cada número

| Rede | Como coleta | Ferramenta | Situação |
|---|---|---|---|
| Instagram | API oficial da Meta (Graph API — insights da conta e de cada post) | Módulo `metricas` (etapa 6) | **(a criar — etapa 6)** |
| Threads | API oficial do Threads (insights da conta e de cada post) | Módulo `metricas` (etapa 6) | **(a criar — etapa 6)** |
| Facebook (Página) | API oficial de Páginas (insights) | Módulo `metricas`, usando o acesso da etapa 4 | **(a criar)**; acesso da etapa 4 **(em andamento no PC — não mexer)** |
| YouTube | YouTube Data API (números públicos) + YouTube Analytics API (retenção, tempo assistido), **quando autorizado** | Módulo `metricas` | **(a criar)**; autorização **(em andamento no PC — não mexer)** |
| TikTok | **Claude** lê a área de análises do TikTok Studio no **Chrome** já logado e grava o JSON | Chrome + JSON no mesmo formato | Hoje: Claude pelo Chrome (sem API) |
| Pinterest (Receitas, Carros, Destinos) | Hoje: Claude pela página oficial (análises); futuro: API oficial do Pinterest | Chrome; API **(a criar)** | Hoje: Claude pelo Chrome, **1 vez por semana** |

Tokens: `H:\HypadoLocal\segredos\meta_tokens.txt` **(existe)** e os do Google/YouTube na mesma pasta. O módulo lê com `ler_segredo` da `hpbase`, que **nunca mostra o valor**. Ninguém abre essa pasta.

---

## 2. Entradas e saídas

### 2.1 Mapa de pastas

```
H:\HypadoLocal\
├── esteira\07_postados\<item>\publicado.json   ← ENTRADA: o que foi ao ar (media_id, formato, horário)
├── estrategia\planos\plano_semana_<AAAA>-W<nn>.json   ← ENTRADA: o que estava planejado (manual 12)
├── metricas\                                     ← SAÍDA principal
│   ├── 2026-10-06\                               ← uma pasta por dia (foto das 6h)
│   │   ├── instagram_hpgta6.json
│   │   ├── threads_hpgta6.json
│   │   ├── facebook_hpgta6.json
│   │   ├── youtube_hpgta6.json
│   │   ├── tiktok_hpgta6.json                    ← gravado pelo Claude (Chrome)
│   │   ├── ... (as mesmas 5 redes × 6 contas; pinterest_* só em 3 canais, semanal)
│   │   ├── coleta.json                           ← o que deu certo e o que faltou
│   │   └── indicadores_2026-10-06.json
│   ├── config\
│   │   ├── metas_monetizacao.json                ← requisitos de cada rede (a criar)
│   │   └── contas.json                           ← contas e redes ativas por canal (a criar)
│   ├── relatorios\
│   │   ├── diario_2026-10-06.md
│   │   ├── semanal_2026-W41.md
│   │   └── para_estrategista_2026-W41.json
│   └── sob_demanda\                              ← coletas fora das 6h (P0, testes)
├── whatsapp_fila\                                ← SAÍDA: resumo do dia anterior e de sábado (a criar — ticket E)
└── app\logs\metricas_AAAA-MM-DD.log
```

> Os nomes de arquivo acima são o padrão deste manual. Se o módulo `metricas` (etapa 6) for entregue com outro nome de arquivo, **vale o do módulo** (está no `LEIA.md` dele) e este manual continua valendo para o **conteúdo**.

### 2.2 Entrada 1 — `publicado.json` (do Publicador, manual 10)

O Analista lê de cada pasta de `07_postados` (últimos **30 dias**) estes campos: `post_id` (é o nome da pasta do item), `canal`, `tipo`, `formato_estrategia`, `slot_id`, `teste_ab`, `duracao_video_s`, e em `redes.<rede>`: `conta`, `media_id`, `permalink`, `publicado_em`, `status`. Só mede redes com `status` `publicado` (ou `agendado` cuja hora já passou). Modelo completo no manual 10, seção 2.7.

A **duração do vídeo** vem do campo `duracao_video_s` do `publicado.json` (o Publicador mede no `final.mp4`). Ela é necessária para calcular a retenção. **Atenção:** o campo `duracao_s` do `post.json` é outra coisa (quanto tempo o Redator levou para escrever) e **não** serve para retenção. Nos arquivos de métrica, o campo `duracao_s` de cada post é sempre a duração do **vídeo**.

### 2.3 Entrada 2 — `contas.json` **(a criar)**

Diz quais redes estão ativas em cada canal e desde quando (para não reclamar de "coleta faltando" numa rede que ainda não foi ligada):

```json
{
  "versao_esquema": 1,
  "canais": {
    "gta":      { "nome": "GTA 6 | HP",          "redes": { "instagram": "@hpgta6",      "threads": "@hpgta6",      "facebook": "GTA 6 | HP",          "youtube": "GTA 6 | HP",          "tiktok": "@hpgta6" } },
    "futebol":  { "nome": "Futebol | HP",        "redes": { "instagram": "@hp.futebol",  "threads": "@hp.futebol",  "facebook": "Futebol | HP",        "youtube": "Futebol | HP",        "tiktok": "@hp.futebol" } },
    "filmes":   { "nome": "Filmes e Séries | HP","redes": { "instagram": "@hp.filmes",   "threads": "@hp.filmes",   "facebook": "Filmes e Séries | HP","youtube": "Filmes e Séries | HP","tiktok": "@hp.filmes" } },
    "receitas": { "nome": "Receitas | HP",       "redes": { "instagram": "@hp.receitas", "threads": "@hp.receitas", "facebook": "Receitas | HP",       "youtube": "Receitas | HP",       "tiktok": "@hp.receitas", "pinterest": "Receitas | HP" } },
    "carros":   { "nome": "Carros | HP",         "redes": { "instagram": "@hp.carros",   "threads": "@hp.carros",   "facebook": "Carros | HP",         "youtube": "Carros | HP",         "tiktok": "@hp.carros",   "pinterest": "Carros | HP" } },
    "destinos": { "nome": "Destinos | HP",       "redes": { "instagram": "@hp.destinos", "threads": "@hp.destinos", "facebook": "Destinos | HP",       "youtube": "Destinos | HP",       "tiktok": "@hp.destinos", "pinterest": "Destinos | HP" } }
  },
  "redes_ativas_na_coleta": {
    "instagram": true, "threads": true, "facebook": false, "youtube": false, "tiktok": true, "pinterest": true
  },
  "atualizado_em": "2026-09-30T18:00:00-03:00"
}
```

`facebook` e `youtube` ficam `false` até a etapa 4 e a autorização do YouTube serem ligadas no PC.

### 2.4 Saída 1 — foto diária por conta e rede (`metricas\<dia>\<rede>_<conta>.json`)

**Uma foto = o número como estava às 6h daquele dia.** Nunca se reescreve uma foto antiga: se precisar coletar de novo, grava em `sob_demanda\`.

Nome do arquivo: `<rede>_<conta sem @ e sem ponto>.json`. Ex.: `@hp.futebol` no Instagram → `instagram_hpfutebol.json`.

Exemplo completo (Instagram, @hpgta6):

```json
{
  "versao_esquema": 1,
  "dia": "2026-10-06",
  "coletado_em": "2026-10-06T06:04:12-03:00",
  "rede": "instagram",
  "canal": "gta",
  "conta": "@hpgta6",
  "fonte": "api",
  "conta_metricas": {
    "seguidores": 18342,
    "seguindo": 12,
    "total_posts": 412,
    "views_dia_anterior": 96410,
    "alcance_dia_anterior": 51220,
    "visitas_perfil_dia_anterior": 1830,
    "cliques_link_dia_anterior": 74,
    "interacoes_dia_anterior": 6120
  },
  "posts": [
    {
      "post_id": "P1_2026-10-02_1830_gta_contagem-48",
      "media_id": "17900000000000011",
      "permalink": "https://www.instagram.com/reel/EXEMPLO11/",
      "tipo": "reel",
      "formato_estrategia": "reel_contagem",
      "teste_ab": null,
      "publicado_em": "2026-10-02T18:31:02-03:00",
      "idade_h": 83.6,
      "duracao_s": 24.0,
      "metricas": {
        "views": 41230,
        "alcance": 29870,
        "curtidas": 2210,
        "comentarios": 188,
        "salvamentos": 402,
        "compartilhamentos": 655,
        "tempo_medio_s": 11.3,
        "seguidores_ganhos": 96
      },
      "bruto": {
        "views": 41230, "reach": 29870, "likes": 2210, "comments": 188,
        "saved": 402, "shares": 655, "ig_reels_avg_watch_time": 11300, "follows": 96
      }
    }
  ],
  "avisos": []
}
```

Regras da foto:
- `metricas` usa **os nomes da HP** (iguais em todas as redes, tabela 2.5). `bruto` guarda **o nome e o valor originais** da API, para conferência e para quando a rede mudar o nome de alguma métrica.
- Métrica que a rede **não fornece** vai como `null` (nunca `0`). Zero quer dizer "a rede disse zero"; `null` quer dizer "a rede não informa".
- `idade_h` = horas entre `publicado_em` e `coletado_em`.
- `posts` inclui **todo post publicado nos últimos 30 dias** daquela conta (os da esteira e, se houver, posts feitos fora da esteira, marcados com `"post_id": null` e `"fora_da_esteira": true`).

### 2.5 Dicionário de métricas (nome HP × nome em cada rede)

Os nomes das métricas nas APIs **mudam com frequência** (a Meta, por exemplo, trocou várias métricas antigas por `views` em 2025). A tabela é a referência atual; **conferir na página oficial** de cada API. O módulo guarda sempre o original em `bruto`.

| Nome HP | Instagram (API) | Threads (API) | Facebook (API) | YouTube (API) | TikTok (tela do Studio) |
|---|---|---|---|---|---|
| `seguidores` | `followers_count` | `followers_count` (insights da conta) | seguidores da Página | `subscriberCount` | Seguidores |
| `views` | `views` | `views` | visualizações do vídeo/reel | `views` | Visualizações |
| `alcance` | `reach` | não fornece (`null`) | alcance do post (contas únicas) | não fornece (`null`) | Espectadores únicos, se mostrar; senão `null` |
| `curtidas` | `likes` | `likes` | reações | `likes` | Curtidas |
| `comentarios` | `comments` | `replies` | comentários | `comments` | Comentários |
| `salvamentos` | `saved` | não fornece | não fornece | não fornece | Favoritos |
| `compartilhamentos` | `shares` | `reposts` + `quotes` + `shares` | compartilhamentos | `shares` (Analytics API) | Compartilhamentos |
| `tempo_medio_s` | `ig_reels_avg_watch_time` ÷ 1000 | não fornece | tempo médio assistido | `averageViewDuration` (Analytics API) | Tempo médio assistido |
| `retencao_pct` | calculada (2.6) | — | calculada | `averageViewPercentage` (Analytics API) | calculada; e "Assistiu ao vídeo completo" à parte |
| `seguidores_ganhos` | `follows` (por post, quando houver) | não fornece | não fornece | `subscribersGained` (Analytics API) | Novos seguidores |

### 2.6 Saída 2 — `indicadores_<dia>.json`

Calculado a partir das fotos. Um bloco por canal e rede, mais a lista de posts com seus índices. Exemplo (cortado a 1 canal e 1 rede para caber; o arquivo real tem todos):

```json
{
  "versao_esquema": 1,
  "dia": "2026-10-06",
  "gerado_em": "2026-10-06T06:18:40-03:00",
  "idade_referencia_h": 72,
  "canais": {
    "gta": {
      "instagram": {
        "seguidores": 18342,
        "ganho_dia": 214,
        "ganho_7d": 1480,
        "crescimento_7d_pct": 8.78,
        "views_dia": 96410,
        "views_media_7d": 88150,
        "posts_7d": 21,
        "alcance_por_post_7d": 21450,
        "te_7d_pct": 6.1,
        "retencao_media_7d_pct": 44.2,
        "salvamentos_por_mil_7d": 13.1,
        "compartilhamentos_por_mil_7d": 19.8,
        "seguidores_por_mil_views_7d": 2.4,
        "por_formato_7d": {
          "reel_noticia":   { "n": 9, "alcance_medio": 24100, "te_pct": 6.4, "retencao_pct": 46.0 },
          "reel_contagem":  { "n": 7, "alcance_medio": 27900, "te_pct": 7.2, "retencao_pct": 51.3 },
          "carrossel_lista":{ "n": 5, "alcance_medio":  8400, "te_pct": 5.0, "retencao_pct": null }
        },
        "por_faixa_7d": {
          "12-14": { "n": 5, "alcance_medio": 17800 },
          "17-19": { "n": 8, "alcance_medio": 22900 },
          "19-21": { "n": 8, "alcance_medio": 24300 }
        }
      }
    }
  },
  "posts": [
    {
      "post_id": "P1_2026-10-02_1830_gta_contagem-48",
      "rede": "instagram",
      "canal": "gta",
      "formato_estrategia": "reel_contagem",
      "faixa": "17-19",
      "idade_h": 83.6,
      "te_pct": 11.57,
      "retencao_pct": 47.1,
      "salvamentos_por_mil": 13.46,
      "compartilhamentos_por_mil": 21.93,
      "seguidores_por_mil_views": 2.33,
      "idr_alcance": 1.39,
      "classe": "acima"
    }
  ],
  "alertas": [
    { "tipo": "queda", "canal": "filmes", "rede": "tiktok", "texto": "views do dia 41% abaixo da média de 7 dias" }
  ]
}
```

(Os números do exemplo são inventados, mas as contas batem: veja 3.E.)

### 2.7 Saída 3 — `coleta.json` (o que deu certo e o que faltou no dia)

```json
{
  "dia": "2026-10-06",
  "inicio": "2026-10-06T06:00:02-03:00",
  "fim": "2026-10-06T06:11:47-03:00",
  "resultado": "parcial",
  "itens": [
    { "rede": "instagram", "conta": "@hpgta6",     "status": "ok",       "posts": 58 },
    { "rede": "threads",   "conta": "@hpgta6",     "status": "ok",       "posts": 61 },
    { "rede": "tiktok",    "conta": "@hpgta6",     "status": "pendente_claude" },
    { "rede": "facebook",  "conta": "GTA 6 | HP",  "status": "rede_inativa" },
    { "rede": "instagram", "conta": "@hp.carros",  "status": "erro", "erro": "autorizacao (codigo 190) — ticket aberto" }
  ],
  "posts_esperados_7d": 214,
  "posts_medidos_7d": 211,
  "cobertura_pct": 98.6
}
```

`resultado`: `completo` (tudo `ok` ou `rede_inativa`), `parcial` (algo `pendente_claude` ou `erro`), `falhou` (nada coletado).

### 2.8 Saída 4 — relatórios

- `metricas\relatorios\diario_<dia>.md` — modelo na seção 3, passo 64.
- `metricas\relatorios\semanal_<AAAA>-W<nn>.md` — modelo no passo 75.
- Texto do **resumo do dia anterior** e do **resumo de sábado** no WhatsApp (2 das 3 únicas coisas permitidas no WhatsApp), gravado em `H:\HypadoLocal\whatsapp_fila\` **(a criar — ticket E)**, sempre começando com `*Claude - *`. Modelos nos passos 67 e 77.

### 2.9 Saída 5 — `para_estrategista_<AAAA>-W<nn>.json`

É **a entrada principal** do Estrategista (manual 12). Tem, para cada canal e rede, os números da semana já prontos para as regras de decisão. Esquema completo com exemplo no passo 78.

---

## 3. Passo a passo (para leigo)

> O **app** faz quase tudo sozinho (coleta por API, contas, relatórios). O Claude faz o **TikTok** e o **Pinterest** pelo Chrome e **lê** os alertas. Os passos abaixo servem para entender, conferir e, numa emergência, fazer à mão.
>
> Os comandos do módulo `metricas` são **(a criar — etapa 6)**. Os nomes previstos aqui (`coletar`, `indicadores`, `relatorio`) podem mudar; o nome certo estará no `LEIA.md` do módulo. Para ver a ajuda: `& $py -m metricas --help`.

### Bloco A — Preparação (uma vez, e conferência rápida todo dia)

**Passo 1.** Abra o PowerShell e cole o bloco de preparação do início do manual.

**Passo 2.** Confira se a pasta de métricas existe e se a foto de hoje já foi feita:

```powershell
Test-Path $met
Get-ChildItem "$met\$(Get-Date -Format yyyy-MM-dd)" -ErrorAction SilentlyContinue | Select-Object Name, Length
```

Depois das 6h20, a pasta de hoje tem que existir e ter um arquivo por conta e rede ativa, mais o `coleta.json`.

**Passo 3.** Confira o arquivo de contas (`$met\config\contas.json`, seção 2.3). Ele diz quais redes estão ativas. **Só o plantão** muda esse arquivo, e só quando uma rede é ligada ou desligada no PC (ex.: quando a etapa 4 do Facebook terminar os 7 dias de sombra).

**Passo 4.** Confira o arquivo de metas (`$met\config\metas_monetizacao.json`, bloco G). A data `conferido_em` de cada rede **não pode ter mais de 30 dias**. Se tiver, o Claude abre a página oficial da rede (passo 60) e atualiza.

**Passo 5.** Confira no log de ontem se teve erro:

```powershell
$ontem = (Get-Date).AddDays(-1).ToString("yyyy-MM-dd")
Select-String -Path "$logs\metricas_$ontem.log" -Pattern "ERROR|WARNING" | Select-Object -Last 20
```

### Bloco B — Coleta automática das 6h (o app faz sozinho)

**Passo 6.** Às **6h00** o **vigia** do app (etapa 1, **existe**) dispara a coleta. Se o PC estava desligado às 6h, a coleta roda **uma vez** assim que o app ligar, e o `coleta.json` registra o horário real (`inicio`). Por que 6h: os números do dia anterior já fecharam, o PC está livre e dá tempo de o relatório estar pronto antes do dia de trabalho. A coleta é **trabalho leve** (só pergunta números pela internet), então não precisa da trava do trabalho pesado.

**Passo 7.** Comando equivalente, para rodar à mão (ou para testar):

```powershell
& $py -m metricas coletar --dia (Get-Date -Format yyyy-MM-dd)
```

E no **modo simular** (usa respostas falsas, não acessa a internet; serve para conferir que o módulo está inteiro):

```powershell
& $py -m metricas coletar --dia (Get-Date -Format yyyy-MM-dd) --simular
```

**(a criar — etapa 6)**.

**Passo 8.** O que a coleta faz, rede por rede, **Instagram** (explicado para leigo):
1. Lê o token da conta com `ler_segredo` (sem mostrar).
2. Pede os números da **conta**: seguidores, total de posts, e os totais do dia anterior (views, alcance, visitas ao perfil, cliques no link, interações).
3. Monta a lista de posts dos **últimos 30 dias** a partir dos `publicado.json` de `07_postados` **e** da lista de posts da própria conta na API (para pegar post feito fora da esteira).
4. Para cada post, pede os **insights** (views, alcance, curtidas, comentários, salvamentos, compartilhamentos, tempo médio assistido, seguidores ganhos quando houver).
5. Grava a foto `instagram_<conta>.json` com os nomes HP em `metricas` e os originais em `bruto`.

**Passo 9.** **Threads:** igual ao Instagram, com as métricas que o Threads fornece (views, curtidas, respostas, reposts, citações, compartilhamentos e seguidores da conta). `alcance`, `salvamentos` e `tempo_medio_s` vão como `null`.

**Passo 10.** **Facebook (Página):** só quando `redes_ativas_na_coleta.facebook = true`. Usa o acesso da etapa 4 **(em andamento no PC — não mexer)**. Enquanto for `false`, o `coleta.json` registra `rede_inativa`.

**Passo 11.** **YouTube:** só quando autorizado. A **Data API** dá números públicos (inscritos, views, curtidas, comentários). A **Analytics API** dá retenção (`averageViewPercentage`), tempo médio (`averageViewDuration`), minutos assistidos e inscritos ganhos — ela precisa de uma autorização separada, feita pelo Antônio na página oficial do Google (**o Claude nunca faz login nem aceita termos**). Sem a Analytics API, `retencao_pct` e `tempo_medio_s` do YouTube ficam `null`.

**Passo 12.** **Limites de consulta:** as APIs limitam quantas perguntas o app pode fazer por hora (Meta) ou por dia (cota do YouTube; ler dados custa pouco, mas soma). O módulo:
- faz as perguntas **em lote** quando a API permite;
- espera e tenta de novo se a API disser "muitas requisições" (3 tentativas, com espera de 1, 5 e 15 min);
- **nunca** usa a cota do YouTube de modo que falte cota para a **publicação** (manual 10): se a cota do dia estiver acima de **70%** usada, a coleta do YouTube pula os posts com mais de 7 dias.

**Passo 13.** **Idade dos posts:** a coleta das 6h mede todos os posts dos últimos 30 dias, mas, para comparar, o app usa a foto em que cada post tem **a mesma idade**: a **idade de referência é 72 horas** (3 dias). Por quê: um post de ontem ainda está crescendo e um post de 10 dias já parou; comparar os dois é injusto. Para isso, o app guarda, para cada post, a foto mais próxima de **24 h**, **72 h** e **7 dias** de idade (as "marcas" D+1, D+3 e D+7).

**Passo 14.** Exemplo de marcas: um post publicado na **sexta 03/10 às 18h31**:
- foto das 6h de **sábado 04/10** → 11,5 h de idade (cedo demais, só acompanhamento);
- foto das 6h de **domingo 05/10** → 35,5 h (é a mais perto de 24 h → marca **D+1**);
- foto das 6h de **segunda 06/10** → 59,5 h;
- foto das 6h de **terça 07/10** → 83,5 h (a mais perto de 72 h → marca **D+3**, usada nas comparações);
- foto das 6h de **sexta 10/10** → 155,5 h;
- foto das 6h de **sábado 11/10** → 179,5 h (fica a 11,5 h de 168 h, e a de sexta fica a 12,5 h → a de sábado é a marca **D+7**).

Regra: vale sempre a foto **mais perto** da idade-alvo; empate → a mais nova.

**Passo 15.** **Posts P0** (gol, lançamento): além das 6h, o app faz uma **coleta sob demanda** do post **1 hora** e **6 horas** depois de publicado (bloco J), gravada em `sob_demanda\`. Serve para o Estrategista saber rápido se vale repetir o assunto no mesmo dia.

**Passo 16.** Ao fim, o app grava o `coleta.json` (seção 2.7) com o que deu certo, o que faltou e a **cobertura** (posts medidos ÷ posts esperados × 100).

**Passo 17.** Se alguma conta deu **erro de autorização** (token vencido, código 190 na Meta): o app **não** tenta mexer no token; marca `erro` no `coleta.json` e abre ticket **P0** na área `metricas` (passo 85). As outras contas seguem normalmente.

**Passo 18.** Para ver o resumo da coleta de hoje:

```powershell
Get-Content "$met\$(Get-Date -Format yyyy-MM-dd)\coleta.json" -Raw -Encoding UTF8 | ConvertFrom-Json | Select-Object resultado, cobertura_pct, inicio, fim
(Get-Content "$met\$(Get-Date -Format yyyy-MM-dd)\coleta.json" -Raw -Encoding UTF8 | ConvertFrom-Json).itens | Format-Table rede, conta, status, posts
```

### Bloco C — TikTok e Pinterest (quem faz é o **Claude**, pelo Chrome)

**Passo 19.** O TikTok não tem API liberada para a HP. Então, **uma vez por dia**, logo depois das 6h (junto com o resto do trabalho da manhã, para economizar token), o Claude abre as **análises** do TikTok Studio no Chrome **já logado** (login feito pelo Antônio). Endereço atual: área "Análises" do TikTok Studio (**conferir na página oficial** se mudou).

**Passo 20.** **Se aparecer pedido de login, senha, código, CAPTCHA, "confirme que é você" ou termos novos → PARAR.** Não digitar nada. Abrir ticket (passo 85) e marcar `pendente_claude` → `erro` no `coleta.json`. **Não** avisar por WhatsApp.

**Passo 21.** Confira a conta ativa (@ no canto). Troque de conta só pelo menu do próprio TikTok e **só** se a conta já estiver conectada sem pedir senha.

**Passo 22.** Na **visão geral** da conta, anote (período "últimos 7 dias" e o total): seguidores, visualizações de vídeo, visualizações do perfil, curtidas, comentários, compartilhamentos.

**Passo 23.** Na lista de **conteúdos/posts**, para **cada vídeo dos últimos 30 dias**, abra os detalhes e anote: visualizações, curtidas, comentários, compartilhamentos, favoritos, tempo médio assistido, % que assistiu ao vídeo completo, novos seguidores (se aparecer) e, se a tela mostrar, espectadores únicos. Para ganhar tempo, os vídeos com **mais de 7 dias** só precisam ser lidos nas marcas D+7 e D+30 (o Claude olha a data de publicação e pula os outros).

**Passo 24.** Relacione cada vídeo do TikTok com o `post_id` da HP: procure a pasta em `07_postados` que tem `tiktok_ok.json` com o mesmo horário (`agendado_para`) e a mesma legenda. Se o `tiktok_ok.json` ainda não tiver `link`, **complete o link** agora (o link do vídeo público).

**Passo 25.** Grave a foto `tiktok_<conta>.json` na pasta do dia, **no mesmo formato** do Instagram (seção 2.4), com `"fonte": "chrome"` e as métricas que o TikTok não mostra como `null`. Exemplo de um post:

```json
{
  "post_id": "P1_2026-10-02_1830_gta_contagem-48",
  "media_id": null,
  "permalink": "https://www.tiktok.com/@hpgta6/video/EXEMPLO",
  "tipo": "reel",
  "formato_estrategia": "reel_contagem",
  "publicado_em": "2026-10-02T19:10:00-03:00",
  "idade_h": 83.3,
  "duracao_s": 24.0,
  "metricas": {
    "views": 15820,
    "alcance": null,
    "curtidas": 1190,
    "comentarios": 64,
    "salvamentos": 141,
    "compartilhamentos": 88,
    "tempo_medio_s": 9.8,
    "seguidores_ganhos": 57,
    "assistiu_completo_pct": 21.4
  },
  "bruto": { "fonte_tela": "TikTok Studio > Análises > Conteúdo", "lido_em": "2026-10-06T06:25:10-03:00" }
}
```

**Passo 26.** Depois de gravar, rode o **validador** do módulo (confere se o JSON está no formato certo, sem campos faltando):

```powershell
& $py -m metricas validar "$met\$(Get-Date -Format yyyy-MM-dd)\tiktok_hpgta6.json"
```

**(a criar — etapa 6)**. Tem que responder `ok`.

**Passo 27.** Repita os passos 21 a 26 para as **6 contas** do TikTok.

**Passo 28.** Depois que todas as 6 estiverem gravadas, rode o recálculo para o TikTok entrar nos indicadores:

```powershell
& $py -m metricas indicadores --dia (Get-Date -Format yyyy-MM-dd)
```

**Passo 29.** **Pinterest** (Receitas, Carros, Destinos): **1 vez por semana**, na sexta de manhã (para entrar no relatório de sábado), o Claude abre as **análises** do Pinterest no Chrome (mesmas regras do passo 20) e grava `pinterest_<conta>.json` com: impressões (vão em `views`), salvamentos, cliques no Pin, cliques no link de saída e seguidores. O Pinterest mede diferente das outras redes; ele **não entra** nas comparações de formato com as outras redes, só na comparação dele com ele mesmo (semana contra semana).

**Passo 30.** Tempo-alvo do Claude neste bloco: **≤ 15 minutos por dia** (TikTok) e **≤ 10 minutos por semana** (Pinterest). Se passar muito disso, anotar no ticket semanal do Analista: é sinal de que precisa simplificar.

### Bloco D — Validação da coleta (o app faz; o Claude lê os alertas)

**Passo 31.** **Cobertura:** `cobertura_pct` do `coleta.json` tem que ser **≥ 98%**. Menos que isso → o relatório diário sai com o aviso "dados incompletos" no topo e a lista do que faltou.

**Passo 32.** **Teste de sanidade 1 — seguidores:** se os seguidores de uma conta caírem **mais de 5%** de um dia para o outro, ou subirem **mais de 50%**, o número é marcado `suspeito` (pode ser erro da API ou limpeza de contas falsas pela rede). Ele aparece no relatório, mas **não** entra no ganho de 7 dias até ser confirmado no dia seguinte.

**Passo 33.** **Teste de sanidade 2 — números que só crescem:** views, curtidas e comentários de um post **não diminuem** de uma foto para a outra (no máximo, uma pequena queda quando a rede remove interações falsas). Queda de mais de **3%** → `suspeito`.

**Passo 34.** **Teste de sanidade 3 — alcance maior que views:** alcance (contas únicas) **não pode** ser maior que views. Se for, a foto do post é marcada `suspeito` e o Analista usa só views para esse post.

**Passo 35.** **Teste de sanidade 4 — post sumido:** um post que estava na foto de ontem e não aparece hoje na lista da API → alerta "post sumido" (pode ter sido removido pela rede). Vai para o relatório e vira ticket P1 na área `publicacao`.

**Passo 36.** **Teste de sanidade 5 — rede fora do ar:** se **todas** as contas de uma rede derem erro, provavelmente a API está fora do ar. O app tenta de novo às **7h** e às **9h** e marca no relatório.

**Passo 37.** **Conferência semanal com a tela** (Claude, **sábado**, 10 minutos): escolha **3 posts por rede** (sorteio que o app faz) e compare o número do JSON com o que aparece na tela oficial (app no emulador **não** é necessário; basta a área de insights/análises no Chrome já logado, ou o próprio Instagram/Threads na web). A diferença tem que ser **≤ 2%** (lembrando que o número da tela é de agora e o do JSON é das 6h — compare com a foto de sob demanda se precisar). Diferença maior → ticket P1 na área `metricas`.

**Passo 38.** Para ver os alertas de hoje:

```powershell
(Get-Content "$met\$(Get-Date -Format yyyy-MM-dd)\indicadores_$(Get-Date -Format yyyy-MM-dd).json" -Raw -Encoding UTF8 | ConvertFrom-Json).alertas | Format-Table tipo, canal, rede, texto -Wrap
```

**Passo 39.** Nunca edite uma foto do dia "para corrigir". Se um número estiver errado, o jeito certo é: coleta sob demanda (bloco J) e anotação no campo `avisos` da foto (o app faz com `metricas anotar`, **a criar**).

**Passo 40.** Segurança: rode a busca de segredos nos arquivos do dia (o app roda sozinho; à mão):

```powershell
Select-String -Path "$met\$(Get-Date -Format yyyy-MM-dd)\*.json","$logs\metricas_$(Get-Date -Format yyyy-MM-dd).log" -Pattern "EAA[A-Za-z0-9]{20,}|access_token=[^*]|Bearer [A-Za-z0-9]|ya29\.|AIza[0-9A-Za-z_-]{30,}"
```

Tem que sair **vazio**. Qualquer linha = ticket **P0** de segurança (sem copiar a linha).

### Bloco E — Calcular os indicadores (o app faz; aqui está cada conta explicada)

> Todas as contas abaixo usam o **mesmo post de exemplo** (números inventados): reel do GTA publicado em 02/10 às 18h31, 24 segundos, medido na marca D+3 com **41.230 views**, **29.870 de alcance**, **2.210 curtidas**, **188 comentários**, **402 salvamentos**, **655 compartilhamentos**, **tempo médio assistido de 11,3 s** e **96 seguidores ganhos**.

**Passo 41.** **Janela de 7 dias (a regra de "que posts entram na conta").** Para a foto do dia **d**, a janela de 7 dias são os posts publicados **de 10 dias atrás até 4 dias atrás** (7 dias de calendário). Todos esses posts já passaram de 72 horas, então todos têm a marca D+3. Exemplo: na foto de **06/10**, a janela vai de **26/09 a 02/10**. A **janela de 14 dias** é a mesma ideia, de 17 a 4 dias atrás.

> Por que não usar os posts de ontem? Porque eles ainda estão crescendo. Misturar post de 1 dia com post de 5 dias faz o formato mais novo parecer pior do que é.

**Passo 42.** **Seguidores e ganho.**
- Seguidores hoje = número da conta na foto de hoje. Ex.: **18.342**.
- Ganho do dia = hoje − ontem. Ex.: 18.342 − 18.128 = **214**.
- Crescimento do dia (%) = ganho ÷ seguidores de ontem × 100. Ex.: 214 ÷ 18.128 × 100 = **1,18%**.
- Ganho de 7 dias = hoje − 7 dias atrás. Ex.: 18.342 − 16.862 = **1.480**.
- Crescimento de 7 dias (%) = 1.480 ÷ 16.862 × 100 = **8,78%**.
- Seguidor marcado `suspeito` (passo 32) **não entra** nessas contas até ser confirmado.

**Passo 43.** **Views e alcance.**
- **Views** = quantas vezes o conteúdo foi exibido (a mesma pessoa pode contar mais de uma vez).
- **Alcance** = quantas **contas diferentes** viram. Sempre menor ou igual a views.
- **Views por dia da conta** (média de 7 dias) = soma das views dos últimos 7 dias ÷ 7.
- **Alcance por post (7 dias)** = soma do alcance D+3 dos posts da janela ÷ número de posts da janela. Ex.: 21 posts somando 450.450 de alcance → 450.450 ÷ 21 = **21.450**.
- Nas redes que **não informam alcance** (Threads, YouTube e, em geral, TikTok), o app usa **views** no lugar e escreve o indicador com o final `_v` (ex.: `views_por_post_7d`). **Nunca** comparar alcance de uma rede com views de outra.

**Passo 44.** **Taxa de engajamento (TE) — a fórmula oficial da HP.**

```
TE (%) = (curtidas + comentários + salvamentos + compartilhamentos) ÷ alcance × 100
```

Exemplo: (2.210 + 188 + 402 + 655) ÷ 29.870 × 100 = 3.455 ÷ 29.870 × 100 = **11,57%**.

Regras:
- Onde a rede **não informa alcance**, usa-se **views** no lugar e o indicador se chama **TE_v**: `TE_v (%) = (curtidas + comentários + salvamentos + compartilhamentos) ÷ views × 100`. Métrica que a rede não fornece (`null`) conta como **zero só no numerador** e o relatório avisa. **TE e TE_v nunca se comparam entre si.**
- **TE de um grupo de posts** (7 dias, um formato, uma faixa de horário) = **soma** das interações de todos os posts ÷ **soma** dos alcances × 100. **Não** é a média das porcentagens (a média das porcentagens dá peso demais a post pequeno).
- Existe também a "TE por seguidores" (interações ÷ seguidores × 100). A HP **não** usa essa para decidir, porque conta pequena com um post viral dá número absurdo. Ela só aparece no relatório semanal, por curiosidade.

**Passo 45.** **Retenção.**

```
Retenção (%) = tempo médio assistido (s) ÷ duração do vídeo (s) × 100
```

Exemplo: 11,3 ÷ 24 × 100 = **47,1%**.

- No YouTube (com a Analytics API), usa-se direto o `averageViewPercentage`.
- No TikTok, além da retenção calculada, guarda-se o "% que assistiu ao vídeo completo" à parte (`assistiu_completo_pct`).
- Vídeo que "dá a volta" (a pessoa assiste 2 vezes) pode passar de 100%. O número é mantido; no relatório aparece "100%+".
- **Retenção de um grupo** = média **ponderada pelas views**: soma de (retenção × views) ÷ soma das views.
- Estático (carrossel, foto) **não tem** retenção (`null`).

**Passo 46.** **Salvamentos e compartilhamentos por mil.**

```
Salvamentos por mil = salvamentos ÷ alcance × 1.000      → 402 ÷ 29.870 × 1.000 = 13,46
Compartilhamentos por mil = compartilhamentos ÷ alcance × 1.000 → 655 ÷ 29.870 × 1.000 = 21,93
```

Salvamento mostra conteúdo **útil** (a pessoa quer ver de novo: receita, dica, lista). Compartilhamento mostra conteúdo que **espalha** (a pessoa manda para alguém). Os dois são os sinais que mais ajudam o alcance para não seguidores. Sem alcance → usa views e chama de `_v`.

**Passo 47.** **Conversão em seguidores (o indicador mais importante para monetizar).**

```
Seguidores por mil views = seguidores ganhos com o post ÷ views × 1.000 → 96 ÷ 41.230 × 1.000 = 2,33
```

Quando a rede **não diz** quantos seguidores cada post trouxe, usa-se o número da **conta**: ganho de seguidores do dia ÷ views do dia × 1.000 (e o relatório avisa que é da conta, não do post).

**Passo 48.** **Índice de desempenho relativo (IDR)** — "esse post foi melhor ou pior que o normal do canal?"

```
IDR = alcance D+3 do post ÷ mediana do alcance D+3 dos posts do mesmo canal e rede na janela de 14 dias
```

**Mediana** é o número do meio quando você coloca todos em ordem (se forem 5 posts com 8, 12, **20**, 25 e 90 mil, a mediana é 20 mil). Ela é usada porque **um viral não distorce** a mediana como distorce a média.

Exemplo: mediana de 14 dias = 21.490 → IDR = 29.870 ÷ 21.490 = **1,39**.

| IDR | Classe | Significado |
|---|---|---|
| ≥ 2,0 | `destaque` | Pelo menos o dobro do normal: estudar e repetir o que funcionou |
| 1,2 a 1,99 | `acima` | Melhor que o normal |
| 0,8 a 1,19 | `na_media` | Normal |
| 0,5 a 0,79 | `abaixo` | Pior que o normal |
| < 0,5 | `fraco` | Menos da metade do normal |

O app calcula também o IDR de **views** (`idr_views`) para as redes sem alcance.

**Passo 49.** **Razão do formato** (é o número que a regra R01 do Estrategista usa):

```
Razão do formato = alcance por post do formato (7 dias) ÷ alcance por post do canal na mesma rede (7 dias)
```

Exemplo: carrossel de lista do GTA no Instagram: 8.400 ÷ 21.450 = **0,39** → está com **39%** da média do canal (abaixo de 50%). O app marca `abaixo_50: true` e conta há quantas semanas seguidas isso acontece (`semanas_abaixo_50`). Mínimo de **4 posts** do formato na janela; com menos, o resultado é `dado_insuficiente`.

**Passo 50.** **Eficiência de produção** (onde a HP gasta trabalho sem retorno):

```
Eficiência = seguidores ganhos na semana (somando todas as redes do canal) ÷ itens produzidos na semana
```

"Item" é **uma pasta** em `07_postados` (um vídeo que saiu em 5 redes conta **1** item, não 5). Exemplo: GTA ganhou 3.100 seguidores com 42 itens → **73,8 seguidores por item**; Receitas ganhou 410 com 21 itens → **19,5**. É com esse número que o Estrategista vê onde "produz muito conteúdo onde não precisa".

**Passo 51.** **Números para a monetização** (bloco G): o app guarda, por canal e rede, as somas móveis que os programas usam: views dos últimos 30 dias (TikTok), views de Shorts dos últimos 90 dias e horas de exibição dos últimos 12 meses (YouTube), minutos assistidos dos últimos 60 dias (Facebook), seguidores/inscritos.

**Passo 52.** **Planejado x realizado:** para cada canal, o app compara as vagas (`slots`) do plano da semana (manual 12) com os posts em `07_postados`:

```
Cumprimento do plano (%) = posts publicados que vieram de um slot ÷ slots planejados até ontem × 100
```

Abaixo de **90%** → alerta no relatório (a causa costuma ser item preso em `99_erros` ou falta de pauta).

### Bloco F — Comparativos (o app monta; o Claude lê)

**Passo 53.** **Por canal** — tabela com, para cada canal: seguidores somando as redes, ganho de 7 dias, crescimento %, views por dia, TE e eficiência de produção. Serve para ver **qual canal cresce mais rápido** e **qual rende mais por item produzido**.

**Passo 54.** **Por rede, dentro de cada canal** — para cada canal: seguidores por mil views, views por post, TE, retenção, em cada rede. Responde "**onde** esse canal ganha seguidor": às vezes o mesmo vídeo traz 3 seguidores por mil views no TikTok e 0,4 no Facebook.

**Passo 55.** **Por formato** (usa o `formato_estrategia` de cada post) — para cada canal e rede: número de posts, alcance médio, razão do formato (passo 49), TE, retenção, salvamentos e compartilhamentos por mil, seguidores por mil. Os nomes dos formatos são os da matriz do Estrategista (manual 12, seção 3, bloco C), por exemplo `reel_noticia`, `reel_contagem`, `reel_gol`, `reel_receita`, `carrossel_lista`, `story_enquete`, `threads_texto`.

**Passo 56.** **Por horário** — faixas fixas (hora de Brasília): `06-09`, `09-12`, `12-14`, `14-17`, `17-19`, `19-21`, `21-23`, `23-06`. Para cada faixa: número de posts, alcance médio e a **razão contra a melhor faixa** (alcance da faixa ÷ alcance da melhor faixa). **Por dia da semana** só aparece no relatório semanal e **só depois de 4 semanas** de dados (antes disso é sorte, não padrão).

**Passo 57.** **Por duração** (só vídeo) — faixas `0-15 s`, `15-30 s`, `30-45 s`, `45-60 s`, `60-90 s`, `90 s+`, com retenção e alcance. No TikTok, a faixa `60 s+` importa para a monetização (bloco G).

**Passo 58.** **Regras de bom senso estatístico** (o app aplica; o Claude respeita ao escrever):
1. **Mínimo de 4 posts** num grupo para dizer qualquer coisa. Menos que isso: `dado_insuficiente`.
2. **P0 à parte:** posts P0 (gol, lançamento) inflam a média. Eles entram nos totais, mas os comparativos de formato e horário são mostrados **com e sem P0**; as regras do Estrategista usam **sem P0**.
3. **Mesma idade:** comparar sempre na marca D+3 (ou D+1 para P0).
4. **Diferença menor que 15%** entre dois grupos = **empate técnico**. Não chamar de "melhor".
5. **Uma semana não é tendência.** Mudança só vira recomendação quando se repete em **2 janelas seguidas** (exceto quedas graves, que viram alerta na hora).
6. **Nunca** tirar conclusão de post com dado `suspeito`.

### Bloco G — Metas de monetização (quanto falta e em quantos dias)

**Passo 59.** **Requisitos conhecidos de cada rede.** Atenção: **todos os números abaixo mudam com frequência e variam por país — conferir na página oficial** antes de usar em qualquer decisão. Eles estão aqui só para explicar **que tipo** de meta cada rede tem.

| Rede | Programa (nome genérico) | O que costuma ser exigido (referência — **conferir na página oficial**) | O que o Analista acompanha | Cuidado especial para a HP |
|---|---|---|---|---|
| **YouTube** | Programa de Parcerias do YouTube — **nível de entrada** (recursos de fãs: assinaturas do canal, Super Chat, Super Thanks etc.) | Na faixa de **500 inscritos** + **3 vídeos públicos nos últimos 90 dias** + (**3.000 horas** de exibição pública nos últimos 12 meses **ou** **3 milhões** de views válidas de Shorts nos últimos 90 dias) | Inscritos; uploads públicos 90 d; horas 12 m; views de Shorts 90 d | "Conteúdo reutilizado" (corte de terceiros sem acréscimo real) pode ser recusado na análise do canal. Edição própria, "Toque HP" (manual 06) e narração/contexto contam a favor. |
| **YouTube** | Programa de Parcerias — **nível completo** (divisão de receita de anúncios, inclusive dos Shorts) | Na faixa de **1.000 inscritos** + (**4.000 horas** de exibição pública nos últimos 12 meses **ou** **10 milhões** de views válidas de Shorts nos últimos 90 dias). Também: país elegível, conta AdSense, sem aviso ativo de diretrizes, verificação em 2 etapas (feita pelo **Antônio**) | Os mesmos do nível de entrada, com as metas maiores | Idem. Só o Antônio aceita termos e vincula AdSense. |
| **TikTok** | Programa de recompensas para criadores (paga por views qualificadas) | Na faixa de **18+ anos**, **10.000 seguidores**, **100.000 views nos últimos 30 dias**, conta em boa situação; só vídeos **originais com mais de 1 minuto** geram recompensa. **Disponível só em alguns países — conferir se o Brasil está incluído e se aceita conta de empresa** | Seguidores; views 30 d; nº de vídeos originais ≥ 60 s | Vídeo < 1 min não conta; corte de terceiros não é "original". Se o programa estiver disponível, o Estrategista precisa planejar vídeos próprios ≥ 60 s. |
| **TikTok** | Presentes em LIVE, assinaturas | Requisitos próprios de idade e seguidores (**conferir**) | Seguidores | LIVE não faz parte do plano atual. |
| **Facebook** | Monetização de conteúdo da Meta (anúncios em vídeos e reels, bônus por desempenho) e Estrelas | A Meta vem juntando os programas; a entrada costuma aparecer como **elegibilidade no painel profissional da Página** (às vezes por convite). Referência antiga de anúncios em vídeo: na faixa de **5.000 seguidores** + **60.000 minutos assistidos em 60 dias** (**conferir, pode estar desatualizado**). Estrelas têm mínimo próprio de seguidores (**conferir**) | Seguidores da Página; minutos assistidos 60 d; o aviso de elegibilidade no painel | Precisa da etapa 4 ligada para medir bem. |
| **Instagram** | Presentes em reels, assinaturas, conteúdo de marca/parcerias | **Não há** pagamento geral por view aberto a todos no Brasil (**conferir**). Presentes e assinaturas têm mínimos de idade e seguidores (**conferir**). Parcerias dependem do tamanho e do engajamento | Seguidores; alcance mensal; TE | Parceria paga e afiliados são **FUTURO** (manual 13). Por enquanto, o Instagram é o motor de **crescimento** e de alimentar as outras redes. |
| **Threads** | — | **Sem** programa de pagamento direto aberto no Brasil (**conferir**) | Seguidores; views | Papel de funil: leva gente para o Instagram (mesma conta). |
| **Pinterest** (3 canais) | — | **Sem** programa de pagamento a criadores no Brasil (**conferir**) | Impressões; cliques de saída | Papel: tráfego para a página de links; no futuro, afiliados (manual 13, FUTURO). |

**Passo 60.** **Atualizar o arquivo de metas** — **1 vez por mês** (ou quando uma rede anunciar mudança), o Claude abre a **página oficial** de cada programa (só leitura; **sem** login, **sem** aceitar nada) e atualiza `H:\HypadoLocal\metricas\config\metas_monetizacao.json` **(a criar)**:

```json
{
  "versao_esquema": 1,
  "atualizado_em": "2026-09-30T18:00:00-03:00",
  "redes": {
    "youtube": {
      "programas": [
        {
          "id": "ypp_entrada",
          "nome": "YouTube — nível de entrada",
          "conferido_em": "2026-09-30",
          "fonte": "página oficial de ajuda do YouTube sobre o Programa de Parcerias",
          "requisitos_todos": [
            { "metrica": "inscritos", "meta": 500 },
            { "metrica": "uploads_publicos_90d", "meta": 3 }
          ],
          "requisitos_um_dos": [
            { "metrica": "horas_exibicao_12m", "meta": 3000, "janela_dias": 365 },
            { "metrica": "views_shorts_90d", "meta": 3000000, "janela_dias": 90 }
          ]
        },
        {
          "id": "ypp_completo",
          "nome": "YouTube — nível completo (anúncios)",
          "conferido_em": "2026-09-30",
          "fonte": "página oficial de ajuda do YouTube sobre o Programa de Parcerias",
          "requisitos_todos": [ { "metrica": "inscritos", "meta": 1000 } ],
          "requisitos_um_dos": [
            { "metrica": "horas_exibicao_12m", "meta": 4000, "janela_dias": 365 },
            { "metrica": "views_shorts_90d", "meta": 10000000, "janela_dias": 90 }
          ]
        }
      ]
    },
    "tiktok": {
      "programas": [
        {
          "id": "tiktok_recompensas",
          "nome": "TikTok — recompensas para criadores",
          "conferido_em": "2026-09-30",
          "disponivel_no_brasil": "conferir",
          "fonte": "página oficial do TikTok sobre o programa",
          "requisitos_todos": [
            { "metrica": "seguidores", "meta": 10000 },
            { "metrica": "views_30d", "meta": 100000, "janela_dias": 30 }
          ],
          "requisitos_um_dos": [],
          "observacao": "só vídeos originais com mais de 1 minuto geram recompensa"
        }
      ]
    }
  }
}
```

- `requisitos_todos`: tem que bater **todos**. `requisitos_um_dos`: basta bater **um**.
- `conferido_em` com mais de **30 dias** → o relatório mostra "meta desatualizada — conferir".
- Os valores do exemplo são **referência** e **precisam ser conferidos** na página oficial no dia de preencher.

**Passo 61.** **Como calcular "em quantos dias bate" (ETA).** Existem dois tipos de meta:

**Tipo 1 — meta que só acumula** (seguidores, inscritos):

```
Dias estimados = (meta − valor atual) ÷ ganho médio por dia nos últimos 14 dias
```

Exemplo (inventado): YouTube do GTA com **640** inscritos, meta **1.000**, ganho médio de **18** por dia → (1.000 − 640) ÷ 18 = 360 ÷ 18 = **20 dias** → data prevista **26/10**. Se o ganho médio for zero ou negativo → "não bate no ritmo atual".

**Tipo 2 — meta em janela móvel** (views dos últimos 30 dias, views de Shorts dos últimos 90 dias). Aqui os dias antigos "saem" da conta enquanto os novos entram. Faça em 2 passos:

1. **Dá para bater no ritmo atual?** Ritmo atual **r** = média de views por dia nos últimos 14 dias. Se **r × tamanho da janela < meta** → **não bate**. O relatório mostra o ritmo necessário: `meta ÷ janela`.
2. **Se dá**, os dias estimados são:

```
a = soma atual da janela ÷ tamanho da janela       (média dos dias que vão sair)
Dias estimados = (meta − soma atual) ÷ (r − a)
```

Exemplo A (inventado) — TikTok do GTA, meta **100.000 views em 30 dias**: soma atual = 62.000; a = 62.000 ÷ 30 = 2.067 por dia; r = 3.400 por dia. Teste 1: 3.400 × 30 = 102.000 ≥ 100.000 → **dá**. Dias = (100.000 − 62.000) ÷ (3.400 − 2.067) = 38.000 ÷ 1.333 = **28,5 → 29 dias**.

Exemplo B (inventado) — YouTube do GTA, meta **3.000.000 de views de Shorts em 90 dias**: r = 21.000 por dia → 21.000 × 90 = 1.890.000 < 3.000.000 → **não bate no ritmo atual**. Ritmo necessário = 3.000.000 ÷ 90 = **33.334 views por dia** (hoje 21.000: precisa de **+59%**).

**Programa com várias exigências:** o prazo do programa é o da exigência **mais demorada**. Ex.: TikTok do GTA precisa de 10.000 seguidores (hoje 6.800, ganho de 95/dia → 3.200 ÷ 95 = 33,7 → **34 dias**) **e** 100.000 views em 30 dias (**29 dias**) → prazo do programa = **34 dias** → data prevista **09/11/2026** (10 dias antes do lançamento do GTA 6).

**Passo 62.** O app grava o resultado no `indicadores_<dia>.json`, bloco `monetizacao`, e no `para_estrategista` (passo 78):

```json
"monetizacao": [
  {
    "canal": "gta", "rede": "tiktok", "programa": "tiktok_recompensas",
    "requisitos": [
      { "metrica": "seguidores", "atual": 6800,  "meta": 10000,  "ritmo_dia": 95,   "dias_estimados": 34, "bate_no_ritmo": true },
      { "metrica": "views_30d",  "atual": 62000, "meta": 100000, "ritmo_dia": 3400, "dias_estimados": 29, "bate_no_ritmo": true }
    ],
    "dias_estimados_programa": 34,
    "data_prevista": "2026-11-09",
    "meta_conferida_em": "2026-09-30",
    "disponivel_no_brasil": "conferir"
  },
  {
    "canal": "gta", "rede": "youtube", "programa": "ypp_entrada",
    "requisitos": [
      { "metrica": "inscritos", "atual": 640, "meta": 500, "ritmo_dia": 18, "dias_estimados": 0, "bate_no_ritmo": true },
      { "metrica": "uploads_publicos_90d", "atual": 85, "meta": 3, "dias_estimados": 0, "bate_no_ritmo": true },
      { "metrica": "views_shorts_90d", "atual": 1450000, "meta": 3000000, "ritmo_dia": 21000, "ritmo_necessario_dia": 33334, "dias_estimados": null, "bate_no_ritmo": false }
    ],
    "dias_estimados_programa": null,
    "data_prevista": null,
    "falta_para_bater": "views de Shorts: +59% de ritmo (33.334/dia)"
  }
]
```

### Bloco H — Relatório diário e resumo do dia anterior (o app monta; o Claude escreve só as 3 linhas)

**Passo 63.** Às **6h30** (ou assim que a coleta terminar), o app gera `metricas\relatorios\diario_<dia>.md`:

```powershell
& $py -m metricas relatorio --diario --dia (Get-Date -Format yyyy-MM-dd)
```

**(a criar — etapa 6)**.

**Passo 64.** **Modelo do relatório diário** (sempre nesta ordem):

```
# Relatório diário — 06/10/2026 (números até 05/10; foto das 6h04)
Cobertura: 98,6% — faltou: Instagram @hp.carros (autorização; ticket aberto)

## 1. Em 3 linhas  (o Claude escreve; máximo 3 linhas, só fatos com número)
- GTA segue puxando: +514 seguidores ontem, 51% do crescimento da HP.
- Contagem regressiva no IG do GTA teve IDR 2,1 (o dobro do normal) pelo 3º dia seguido.
- Carrossel de lista do Filmes está a 38% da média do canal no IG há 7 dias.

## 2. Seguidores (total | ontem | 7 dias | % 7 dias)
| Canal    | Instagram            | Threads | Facebook | YouTube | TikTok | Pinterest |
| GTA      | 18.342 | +214 | +1.480 | 8,8% | ... | inativa | ... | ... | — |
| ...      |

## 3. Destaques (IDR ≥ 2,0)
| Canal | Rede | Post | Formato | Faixa | IDR | TE | Retenção | Seg./mil |

## 4. Fracos (IDR < 0,5)
(mesmas colunas)

## 5. Alertas
- queda > 30% nas views do dia contra a média de 7 dias
- post sumido / número suspeito / coleta faltando / meta desatualizada

## 6. Monetização (dias estimados no ritmo atual)
| Canal | Rede | Programa | Falta | Dias | Data prevista |

## 7. Planejado x realizado (ontem)
| Canal | Slots | Publicados | % | Motivo das faltas |
```

**Passo 65.** **Alertas automáticos** (entram na seção 5 do relatório):

| Alerta | Quando dispara |
|---|---|
| `queda` | Views do dia de uma conta **30% ou mais abaixo** da média de 7 dias |
| `queda_geral` | Todas as redes de um canal caíram 30% ou mais no mesmo dia (pode ser problema na conta; o Estrategista **não** corta formato com base nesse dia) |
| `pico` | Views do dia **2 vezes ou mais** a média de 7 dias (descobrir o post que puxou) |
| `seguidores_negativo` | Ganho negativo por 2 dias seguidos |
| `post_sumido` | Passo 35 |
| `suspeito` | Passos 32 a 34 |
| `coleta_faltando` | Conta ativa sem foto no dia |
| `meta_desatualizada` | `conferido_em` com mais de 30 dias |
| `plano_abaixo_90` | Cumprimento do plano < 90% |

**Passo 66.** O Claude lê o relatório (≤ **5 minutos**) e escreve **só** as **3 linhas** da seção 1. Regra: **cada linha tem pelo menos um número** e **nenhuma opinião sem número**. Se o dia foi normal, pode escrever "Dia normal: nenhum alerta; crescimento dentro da média de 7 dias".

**Passo 67.** **Resumo do dia anterior no WhatsApp** (uma das **3 únicas coisas** permitidas no WhatsApp). O app monta o texto a partir do relatório, **no máximo 10 linhas**, sempre começando com `*Claude - *`:

```
*Claude - * Resumo de ontem (05/10)
👥 Seguidores: +1.012 no total (GTA +514 · Futebol +260 · Filmes +88 · Receitas +61 · Carros +49 · Destinos +40)
👀 Views: 412 mil (+9% sobre a média da semana)
🏆 Melhor: GTA — "Faltam 45 dias" (IG, 2,1x o normal)
📉 Mais fraco: Filmes — carrossel de lista (IG, 0,4x)
💰 Mais perto de monetizar: TikTok do GTA — ~34 dias (09/11)
⚠️ Instagram @hp.carros sem números hoje (já tem ticket)
```

**Passo 68.** O texto vai para `H:\HypadoLocal\whatsapp_fila\<dia>_resumo.json` **(a criar — ticket E)** com `"grupo": "HP | Comissão 🚀"` (ou o grupo que o plantão já usa para o resumo; só grupos da lista permitida). **Hoje**, enquanto o enviador local está em **modo sombra**, o plantão do Claude envia o resumo e o app **só monta** o texto, para comparar os dois.

**Passo 69.** O app atualiza a fila local do painel (`scripts\painel_local.py` **(existe)**) com os números do dia, para o painel mostrar seguidores, destaques e metas.

### Bloco I — Relatório semanal, resumo de sábado e arquivo para o Estrategista

**Passo 70.** **Quando:** todo **sábado**, logo depois da coleta das 6h. Pronto até **7h00**. Motivo: o resumo de sábado (WhatsApp) sai de manhã e o Estrategista (manual 12) monta o plano da semana seguinte no sábado, com o fim de semana para o Pauteiro preparar a segunda-feira.

**Passo 71.** **Que dados entram:**
- **Contas** (seguidores, views por dia): os 7 dias fechados antes da foto de sábado (sábado anterior a sexta).
- **Posts** (formato, horário, duração, testes): a **janela de 7 dias** da foto de sábado (passo 41) **e** a janela de 14 dias, lado a lado.

**Passo 72.** O app calcula, para cada canal e rede: todos os indicadores do bloco E, todos os comparativos do bloco F, a **semana contra a semana anterior** (diferença em %) e as **metas** do bloco G.

**Passo 73.** **Resultado dos testes A/B** (os testes são desenhados pelo Estrategista, manual 12, seção 3, bloco F): para cada teste com `status: "rodando"`, o app junta os posts da variante A e da B (pelo campo `teste_ab` do `publicado.json`) e calcula a métrica principal do teste em cada lado.

```
Diferença (%) = (métrica B − métrica A) ÷ métrica A × 100
```

O teste está **concluído** quando cada lado tem o **mínimo de posts** pedido pelo teste (padrão **5**). O vencedor é declarado se a diferença for **≥ 20%** e se o lado vencedor ganhou em **pelo menos 70% dos pares** (post A × post B do mesmo dia/assunto). Se não, é **empate** — e empate também é resultado (fica o mais barato de produzir).

**Passo 74.** **Recomendações do Analista** — o app aplica as **regras de decisão do Estrategista** (manual 12, seção 4.2: R01, R02...) aos números e lista **quais regras "dispararam"**, com os números que fizeram disparar. O Analista **recomenda**; quem **decide** é o Estrategista.

**Passo 75.** **Modelo do relatório semanal** (`metricas\relatorios\semanal_<AAAA>-W<nn>.md`):

```
# Relatório semanal — 2026-W41 (sáb 03/10 a sex 09/10) — gerado sáb 10/10 6h41 — base do plano 2026-W42
Cobertura da semana: 98,9%

## 1. Resumo em 5 linhas (Claude, só fatos com número)
## 2. Crescimento por canal (seguidores somando as redes, % na semana, eficiência por item)
## 3. Onde cada canal ganha seguidor (seguidores por mil views, por rede)
## 4. Formatos (por canal e rede: n, alcance médio, razão vs canal, TE, retenção, salv./mil, compart./mil, seg./mil)
## 5. Horários (faixas; razão vs melhor faixa) — dia da semana só a partir de 4 semanas
## 6. Durações (retenção por faixa)
## 7. Testes A/B (rodando / concluídos / vencedor / diferença)
## 8. Monetização (tabela de prazos; o que mais acelera cada meta)
## 9. Planejado x realizado da semana
## 10. Regras do Estrategista que dispararam (R01…) com os números
## 11. Qualidade dos dados (cobertura, suspeitos, redes inativas, metas desatualizadas)
```

**Passo 76.** O Claude escreve as **5 linhas** da seção 1 (mesma regra do passo 66: só fatos com número) e confere se as regras da seção 10 fazem sentido (≤ **15 minutos**).

**Passo 77.** **Resumo de sábado no WhatsApp** (a terceira das 3 coisas permitidas). No máximo **12 linhas**, começando com `*Claude - *`:

```
*Claude - * Resumo da semana (03/10 a 09/10)
👥 Seguidores: +6.940 (+7,2%) — GTA +3.100 · Futebol +1.820 · Filmes +700 · Receitas +410 · Carros +520 · Destinos +390
🏭 Rende mais por vídeo: GTA (73,8 seguidores/vídeo) · menos: Receitas (19,5)
🏆 Formato da semana: contagem regressiva do GTA (IG 1,3x a média; TikTok 1,6x)
✂️ Vai diminuir: carrossel de lista do Filmes (38% da média, 2ª semana)
🧪 Teste concluído: capa com número > capa com rosto (+27% de alcance)
💰 Prazos: TikTok GTA ~27 dias · YouTube GTA precisa +59% de views de Shorts
```

(Mesmo caminho do passo 68: `whatsapp_fila`, grupo permitido, modo sombra até o enviador local ser ligado.)

**Passo 78.** **Arquivo para o Estrategista** — `metricas\relatorios\para_estrategista_<AAAA>-W<nn>.json`, onde `W<nn>` é a **semana do plano que vai ser feito** (a semana seguinte). Esquema com exemplo (cortado a 1 canal; o real tem os 6):

```json
{
  "versao_esquema": 1,
  "semana_alvo": "2026-W42",
  "gerado_em": "2026-10-10T06:44:02-03:00",
  "base": {
    "foto_dia": "2026-10-10",
    "janela_posts_7d": { "de": "2026-09-30", "ate": "2026-10-06" },
    "janela_posts_14d": { "de": "2026-09-23", "ate": "2026-10-06" },
    "idade_referencia_h": 72,
    "sem_p0": true
  },
  "qualidade_dados": { "cobertura_pct": 98.9, "redes_inativas": ["facebook", "youtube"], "suspeitos": 2 },
  "canais": {
    "filmes": {
      "resumo": { "seguidores_total": 9120, "ganho_7d": 700, "crescimento_7d_pct": 8.3, "itens_produzidos_7d": 28, "eficiencia_seg_por_item": 25.0 },
      "redes": {
        "instagram": {
          "seguidores": 4210, "ganho_7d": 260, "seguidores_por_mil_views": 1.9,
          "views_dia_media_7d": 19400, "posts_7d": 14, "alcance_por_post_7d": 9800,
          "te_7d_pct": 5.2, "retencao_7d_pct": 41.0,
          "formatos": {
            "reel_trailer_comentado": { "n": 6, "alcance_medio": 13100, "razao_vs_canal": 1.34, "te_pct": 5.9, "retencao_pct": 44.0, "seg_por_mil": 2.2, "semanas_abaixo_50": 0, "semanas_acima_150": 0 },
            "reel_curiosidade":       { "n": 4, "alcance_medio": 11050, "razao_vs_canal": 1.13, "te_pct": 5.1, "retencao_pct": 39.5, "seg_por_mil": 1.8, "semanas_abaixo_50": 0, "semanas_acima_150": 0 },
            "carrossel_lista":        { "n": 4, "alcance_medio":  3720, "razao_vs_canal": 0.38, "te_pct": 4.1, "retencao_pct": null, "seg_por_mil": 0.9, "semanas_abaixo_50": 2, "semanas_acima_150": 0 }
          },
          "faixas": {
            "12-14": { "n": 4, "alcance_medio": 7300,  "razao_vs_melhor": 0.61 },
            "19-21": { "n": 6, "alcance_medio": 11900, "razao_vs_melhor": 1.00 },
            "21-23": { "n": 4, "alcance_medio": 9100,  "razao_vs_melhor": 0.76 }
          },
          "duracoes": {
            "15-30": { "n": 5, "retencao_pct": 46.0 },
            "30-45": { "n": 5, "retencao_pct": 38.2 }
          },
          "semana_vs_anterior_pct": { "alcance_por_post": 6.5, "seguidores_ganhos": 12.0 }
        }
      },
      "monetizacao": [],
      "testes_ab": [
        { "id": "AB-2026-W41-filmes-capa", "status": "concluido", "metrica": "alcance_d3", "n_a": 5, "n_b": 5, "valor_a": 8200, "valor_b": 10400, "diferenca_pct": 26.8, "pares_vencidos_b_pct": 80, "vencedor": "B" }
      ],
      "alertas": []
    }
  },
  "regras_disparadas": [
    { "regra": "R03", "canal": "filmes", "rede": "instagram", "formato": "carrossel_lista", "numeros": "razão 0,38 (< 0,50) pela 2ª semana seguida; n=4", "sugestao": "pausar 2 semanas e manter 1 post de teste por semana" }
  ]
}
```

(Números inventados; a conta de `razao_vs_canal` do carrossel: 3.720 ÷ 9.800 = 0,38.)

**Passo 79.** O app **valida** o arquivo antes de entregar (campos obrigatórios, números não negativos, `razao_vs_canal` coerente com os alcances, `n ≥ 4` em todo formato que tem regra disparada):

```powershell
& $py -m metricas validar "$met\relatorios\para_estrategista_2026-W42.json"
```

**(a criar — etapa 6)**. Tem que responder `ok`.

**Passo 80.** Entrega: o arquivo fica em `metricas\relatorios\`, onde o Estrategista (manual 12, passo 1) lê. O app registra no log `para_estrategista entregue`.

### Bloco J — Coleta sob demanda

**Passo 81.** Serve para: posts **P0** (1 h e 6 h depois de publicados), **testes A/B** que precisam de marca D+1, e quando o Antônio ou o Estrategista pedem o número de agora.

```powershell
& $py -m metricas coletar --post P1_2026-10-02_1830_gta_contagem-48
```

**(a criar — etapa 6)**. Grava em `metricas\sob_demanda\<dia>_<hora>_<post_id>.json`, **nunca** por cima da foto das 6h.

**Passo 82.** Coleta sob demanda é leve, mas respeita os limites de consulta das APIs: **no máximo 1 por post por hora**.

**Passo 83.** TikTok sob demanda: só se o Estrategista pedir para uma decisão P0 (ex.: repetir um assunto de gol). O Claude lê a tela e grava no mesmo formato do passo 25.

**Passo 84.** O resultado de uma coleta sob demanda **não** entra nos indicadores do dia (que são das 6h); ele só aparece no painel e no arquivo próprio.

### Bloco K — Quando algo dá errado

**Passo 85.** **Abrir ticket** com `scripts\tickets.py` **(existe)**, área `metricas` (veja a sintaxe com `& $py "$scripts\tickets.py" --help`). Escrever: o que faltou (rede, conta, dia), a mensagem de erro **sem token**, o que já foi tentado. **Nunca** pedir ajuda pelo WhatsApp (ele é só para as 3 coisas).

**Passo 86.** **Token vencido ou autorização retirada** (erro de autorização; na Meta, código 190): **não** abrir `segredos\`. Ticket **P0** para o Antônio renovar a autorização na página oficial. A conta fica sem números até lá; o relatório avisa.

**Passo 87.** **A rede mudou o nome de uma métrica** (a API responde "métrica inválida" ou a métrica some): o módulo grava `null`, registra `WARNING` e abre ticket P1. O Claude confere a **documentação oficial** da API e atualiza o mapa de métricas (arquivo de configuração do módulo, **a criar**: `metricas\config\mapa_metricas.json`), **sem** mudar código. A tabela 2.5 deste manual também é atualizada.

**Passo 88.** **Cota do YouTube acabando:** passo 12 (a publicação tem prioridade sobre a coleta).

**Passo 89.** **Número muito estranho** que passou nos testes de sanidade (ex.: um post com 50 vezes o normal): não "corrigir". Conferir na tela (passo 37) e, se o número for real, é um **destaque** — ótima notícia para o Estrategista estudar.

**Passo 90.** **Coleta do TikTok não feita** até as 9h: o relatório sai sem TikTok (com aviso) e é **refeito** quando o Claude gravar os arquivos (rodar o passo 28 e o passo 63 de novo).

### Bloco L — Fim do dia

**Passo 91.** Conferir no painel que os números do dia aparecem (seguidores, destaques, metas).

**Passo 92.** Conferir que o `coleta.json` do dia está `completo` (ou `parcial` com ticket para cada falta) e que a busca de segredos do passo 40 deu **vazio**.

---

## 4. Regras que nunca se quebram

### 4.1 Segurança
1. **Nunca** fazer login, digitar senha ou código, criar conta, aceitar termos ou contornar CAPTCHA — nem no TikTok, nem no Pinterest, nem no Google. Apareceu → **parar** e abrir ticket.
2. **Nunca** abrir, ler, copiar, imprimir ou colar token. O módulo lê com `ler_segredo` e o log passa pelo `mascarar` da `hpbase`. Arquivos de métrica e relatórios **nunca** têm token (busca do passo 40 sempre vazia).
3. **Só** API oficial ou a página oficial no Chrome já logado. **Proibido** raspar dados com biblioteca que imita aplicativo de rede social.
4. Nada de dado pessoal de seguidor (nome, @ de quem comentou) em relatório: só números agregados.

### 4.2 Dados
5. **Foto do dia não se reescreve.** Correção vai em `sob_demanda\` e em `avisos`.
6. **`null` não é zero.** Métrica que a rede não informa é `null`.
7. **Mesma fórmula para todos** (seção 3, bloco E). Mudou a fórmula → muda a versão do esquema (`versao_esquema`) e recalcula as 4 semanas anteriores, para a comparação continuar justa.
8. **Mesma idade** para comparar (marca D+3; D+1 para P0).
9. **Mínimo de 4 posts** por grupo para qualquer conclusão; **P0 à parte**.
10. **Alcance nunca se compara com views**; **TE nunca se compara com TE_v**.
11. Requisito de monetização **sempre com data de conferência** e a marca "conferir na página oficial"; mais de 30 dias → "meta desatualizada".

### 4.3 Papel
12. **O Analista recomenda; o Estrategista decide.** Nenhum relatório diz "vamos fazer X"; diz "a regra R0X disparou com estes números".
13. **Nenhuma opinião sem número** nas linhas escritas pelo Claude.
14. **Não mexer** na etapa 4 (Facebook e YouTube), na auditoria da API do YouTube e na redução de arquivos do painel público (em andamento no PC).

### 4.4 WhatsApp
15. O Analista só alimenta **2 das 3 coisas** permitidas: **resumo do dia anterior** e **resumo de sábado**. Erro, alerta técnico e dúvida vão por **ticket**.
16. Toda mensagem começa com `*Claude - *`; só grupos `HP | Comissão 🚀` e os da lista `HP | Grupos`; nunca em primeiro plano.

---

## 5. Critérios de qualidade com nota

Nota de 0 a 10 por critério, **todo dia**; a nota do dia é a média. Qualquer **0** vira ticket P0.

| Critério | Nota 10 | Nota 7 | Nota 5 | Nota 0 |
|---|---|---|---|---|
| **Pontualidade** | Coleta até 6h20 e relatório até 6h45 | Relatório até 8h | Relatório até 10h | Sem relatório no dia |
| **Cobertura** | ≥ 98% dos posts da janela medidos; toda conta ativa com foto | 95% a 97,9% | 90% a 94,9% | < 90% sem ticket |
| **Exatidão** | Amostra semanal com diferença ≤ 2% da tela | 2,1% a 5% | 5,1% a 10% | > 10% ou número inventado |
| **Fórmulas** | Todas as contas do bloco E batem com o recálculo do teste (T-04 a T-09) | 1 indicador secundário com arredondamento diferente | 1 indicador principal errado, corrigido no dia | TE, retenção ou razão do formato com fórmula errada em decisão |
| **Comparações justas** | Mesma idade, n ≥ 4, P0 à parte, sem mistura alcance/views | 1 comparativo sem "com e sem P0" | Comparativo com n < 4 sem aviso | Conclusão tirada de dado suspeito ou de mistura alcance/views |
| **Monetização** | Todas as metas com `conferido_em` ≤ 30 dias e ETA calculado pelas 2 fórmulas | 1 meta entre 31 e 45 dias | Meta > 45 dias | Requisito sem "conferir" ou inventado |
| **Texto do Claude** | 3 linhas (diário) / 5 linhas (semanal), todas com número | 1 linha sem número | Opinião sem número | Informação falsa |
| **WhatsApp** | Resumo ≤ 10/12 linhas, começa com `*Claude - *`, grupo permitido | 1 linha a mais | Enviado fora do horário da manhã | Sem `*Claude - *`, grupo errado ou WhatsApp usado para alerta |
| **Segurança** | Busca de segredos vazia; nenhum login/código | — | — | Qualquer token em arquivo/log/tela |

Classificação: **≥ 9 Excelente**; **7 a 8,9 Bom**; **5 a 6,9 Médio** (ticket de melhoria); **< 5 Razoável** (o relatório do dia **não** alimenta o Estrategista até ser refeito).

---

## 6. Erros comuns e o que fazer

| # | Erro | Por que acontece | O que fazer |
|---|---|---|---|
| 1 | Coleta não rodou às 6h | PC desligado ou app parado | O vigia roda ao ligar (passo 6); se não rodar, `metricas coletar` à mão (passo 7) e ticket |
| 2 | Erro de autorização (código 190 na Meta) | Token vencido | Passo 86: ticket P0, não abrir `segredos\` |
| 3 | "Muitas requisições" | Limite de consulta da API | Espera e tenta (1, 5, 15 min — passo 12) |
| 4 | Métrica inválida / sumiu | A rede mudou o nome | Passo 87: `null`, ticket, atualizar o mapa pela documentação oficial |
| 5 | Seguidores caíram muito num dia | Limpeza de contas falsas pela rede ou erro da API | Passo 32: `suspeito`, confirmar no dia seguinte |
| 6 | Alcance maior que views | Erro da API | Passo 34: usar só views nesse post |
| 7 | Post sumido | Removido pela rede ou atraso na listagem | Passo 35: alerta e ticket P1 em `publicacao` |
| 8 | TikTok pede login/código | Sessão venceu | Passo 20: parar, ticket, relatório sem TikTok |
| 9 | Post do TikTok sem `post_id` | Não achou o `tiktok_ok.json` correspondente | Relacionar pela hora e legenda (passo 24); se não achar, `fora_da_esteira: true` |
| 10 | Formato aparece como `null` | `publicado.json` sem `formato_estrategia` | O post entra nos totais, mas não nos comparativos de formato; ticket para o Publicador/Pauteiro preencherem |
| 11 | Comparação "estranha" (formato novo parece péssimo) | Posts novos medidos antes de 72 h | Conferir a janela (passo 41) |
| 12 | Um viral distorce a média | Média é sensível a valor extremo | Olhar a mediana e o IDR (passo 48); regras usam sem P0 |
| 13 | Meta de monetização desatualizada | Mais de 30 dias sem conferir | Passo 60 |
| 14 | Relatório semanal sem testes A/B | `teste_ab` não gravado nos posts | Ticket para o Pauteiro/Publicador: o campo vem da vaga do plano, passa pelo `pedido.json` e é copiado para o `publicado.json` |
| 15 | Cota do YouTube acabou na coleta | Coleta pesada demais | Passo 12: pular posts antigos; publicação tem prioridade |
| 16 | Número diferente da tela > 2% | Hora diferente (6h × agora) ou métrica com outro significado | Comparar com coleta sob demanda; se persistir, ticket P1 |

---

## 7. O que o app faz sozinho x o que o Claude decide

| Tarefa | App sozinho | Claude | Observação |
|---|---|---|---|
| Coleta por API (Instagram, Threads, Facebook, YouTube) | 100% | 0% | Etapa 6 (a criar); Facebook/YouTube quando ligados |
| Coleta do TikTok | 0% | 100% | Chrome, ≤ 15 min/dia |
| Coleta do Pinterest | 0% (100% quando houver API) | 100% hoje | 1 vez por semana |
| Validação e alertas | 100% | 0% | Testes de sanidade fixos |
| Conferência semanal com a tela | 0% | 100% | 10 min no sábado |
| Cálculo de todos os indicadores e comparativos | 100% | 0% | Fórmulas fixas |
| Metas: cálculo de prazo | 100% | 0% | — |
| Metas: conferir requisitos na página oficial | 0% | 100% | 1 vez por mês |
| Relatório diário e semanal (tabelas) | 100% | 0% | — |
| 3 linhas do diário e 5 do semanal | 0% | 100% | ≤ 5 e ≤ 15 min |
| Texto do resumo no WhatsApp | 100% (modelo) | 0% | O Claude só escreve se o modelo não cobrir algo |
| Arquivo para o Estrategista, com regras disparadas | 100% | 0% | — |

**Estimativa geral:** **≈ 85% app / 15% Claude** hoje (o TikTok pesa); **≈ 90% / 10%** quando Facebook, YouTube e Pinterest estiverem ligados por API.

---

## 8. Ferramentas existentes que já fazem cada passo

| Passo(s) | Ferramenta | Situação |
|---|---|---|
| 1–5, 18, 38, 40 | PowerShell (`Get-Content`, `ConvertFrom-Json`, `Select-String`) | existe |
| 6 | Vigia do app (etapa 1: motor + vigia + fila + `hp` + tela `http://127.0.0.1:8770`) | existe |
| 7–17, 26, 28, 31–36, 41–58, 61–63, 72–74, 78–82 | Módulo `metricas` (`app\hp_studio_nuvem\metricas\`): `coletar`, `validar`, `indicadores`, `relatorio`, `anotar` | **(a criar — etapa 6)** |
| 8–11, 17, 86 | Tokens em `H:\HypadoLocal\segredos\meta_tokens.txt`; `ler_segredo` da `hpbase` | existe |
| todos | `hpbase`: `obter_logger`, `mascarar`, `ler_json`, `escrever_json`, `agora_iso`, `raiz_local` | existe |
| 10, 11 | Acesso da etapa 4 (Facebook, YouTube) e autorização do YouTube | em andamento no PC — não mexer |
| 19–30, 37, 83 | Chrome já logado (TikTok Studio, Pinterest, insights) | existe (processo atual do Claude) |
| 24 | `tiktok_ok.json` gravado pelo Publicador/Claude (manual 10) | processo atual |
| 60 | `metricas\config\metas_monetizacao.json` | **(a criar)** |
| 3 | `metricas\config\contas.json` | **(a criar)** |
| 87 | `metricas\config\mapa_metricas.json` | **(a criar)** |
| 67–68, 77 | Fila `H:\HypadoLocal\whatsapp_fila\` + enviador local | **(a criar — ticket E)** |
| 69 | `scripts\painel_local.py` (fila local do painel) | existe |
| 85 | `scripts\tickets.py` | existe |

---

## 9. Testes de aceitação

Nenhum teste acessa internet, WhatsApp ou Chrome de verdade: as APIs são trocadas por um **falso** com respostas gravadas. O Analista do app só substitui o trabalho manual depois de passar em **todos** e de **7 dias de modo sombra** (ver README), em que os números do app são comparados com os levantados pelo plantão.

| Nº | Teste | Como | Passa se |
|---|---|---|---|
| T-01 | Coleta completa | API falsa com 6 contas × 2 redes, 60 posts cada | 12 fotos gravadas; `coleta.json` `completo`; cobertura 100% |
| T-02 | Rede inativa | `facebook: false` em `contas.json` | `rede_inativa` no `coleta.json`; nenhum alerta de "coleta faltando" |
| T-03 | `null` ≠ zero | Threads sem `reach` e `saved` | Campos `null` na foto; nenhum `0` inventado |
| T-04 | TE | Post do exemplo (3.455 interações ÷ 29.870) | TE = **11,57%** (±0,01) |
| T-05 | TE de grupo | 3 posts: (100/1.000), (50/2.000), (900/10.000) | TE do grupo = 1.050 ÷ 13.000 × 100 = **8,08%** (e **não** a média das %, 7,17%) |
| T-06 | Retenção | 11,3 s em vídeo de 24 s | **47,1%** |
| T-07 | IDR e classe | Alcance 29.870, mediana 21.490 | IDR **1,39**, classe `acima` |
| T-08 | Razão do formato e R01 | Formato 8.400 × canal 21.450, n = 5 | Razão **0,39**; `abaixo_50: true`; com n = 3 → `dado_insuficiente` |
| T-09 | ETA tipo 1 e tipo 2 | Exemplos do passo 61 | **20** dias; **29** dias; "não bate" com ritmo necessário **33.334**/dia; programa TikTok = **34** dias |
| T-10 | Janela de 7 dias | Foto de 06/10 com posts de 20/09 a 05/10 | Entram só os de **26/09 a 02/10** |
| T-11 | Marcas D+1/D+3/D+7 | Post de 03/10 18h31 | D+1 = foto de 05/10; D+3 = 07/10; D+7 = 11/10 |
| T-12 | Sanidade | Seguidores −8% num dia; alcance > views num post | Os dois marcados `suspeito`; fora do ganho de 7 dias |
| T-13 | Foto não se reescreve | Rodar `coletar` 2 vezes no mesmo dia | A 2ª vai para `sob_demanda\`; foto das 6h intacta (mesmo hash) |
| T-14 | Relatório diário | Dados do T-01 | Arquivo com as 7 seções na ordem; gerado em **≤ 60 s** |
| T-15 | Resumo WhatsApp | Dados do T-01 | Começa com `*Claude - *`; ≤ 10 linhas; grupo permitido |
| T-16 | Teste A/B | A: 5 posts; B: 5 posts com +27%; B vence 4 de 5 pares | `concluido`, vencedor **B**; com +12% → `empate` |
| T-17 | `para_estrategista` | Dados de 14 dias | Valida no `metricas validar`; `regras_disparadas` contém R03 para o formato com 2 semanas < 0,5 |
| T-18 | Segredos | Rodar T-01 a T-17 com token falso `EAA` + 30 letras | Busca do passo 40 = **0** linhas em JSON, relatórios e log |
| T-19 | Desempenho | 6 contas × 5 redes × 60 posts (falso) | Coleta + indicadores em **≤ 10 min** |
| T-20 | Modo sombra (7 dias) | App em paralelo com o plantão | Seguidores idênticos; métricas de post com diferença ≤ **2%** em ≥ **95%** dos posts; relatórios nos 7 dias até 6h45 |

---

## Glossário

- **Alcance** — número de contas **diferentes** que viram o conteúdo.
- **API** — porta de serviço oficial da rede para programas pedirem dados.
- **Cobertura** — quantos dos posts esperados foram medidos, em %.
- **D+1 / D+3 / D+7** — a foto do post quando ele tem cerca de 1, 3 e 7 dias de idade.
- **ETA** — estimativa de quantos dias faltam para bater uma meta no ritmo atual.
- **Foto diária** — os números como estavam às 6h; nunca se reescreve.
- **IDR** — índice de desempenho relativo: o post ÷ o normal do canal (mediana).
- **Janela móvel** — soma dos últimos N dias que "anda" um dia por vez (ex.: views dos últimos 30 dias).
- **Mediana** — o valor do meio numa lista em ordem; não é distorcida por um viral.
- **Modo sombra** — o app faz em paralelo, sem substituir, para comparar com o plantão.
- **Razão do formato** — alcance médio do formato ÷ alcance médio do canal na mesma rede.
- **Retenção** — quanto do vídeo, em média, as pessoas assistem (%).
- **TE / TE_v** — taxa de engajamento sobre alcance / sobre views.
- **Views** — número de exibições (a mesma pessoa pode contar mais de uma vez).
