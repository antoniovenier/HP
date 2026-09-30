# Manuais do HP Studio — índice

> **Empresa:** Hypado (HP) — 6 perfis de vídeos curtos: **GTA 6 | HP** (@hpgta6, foco no lançamento do GTA 6 em **19/11/2026**), **Futebol | HP** (@hp.futebol), **Filmes e Séries | HP** (@hp.filmes), **Receitas | HP** (@hp.receitas), **Carros | HP** (@hp.carros) e **Destinos | HP** (@hp.destinos), em Instagram, Facebook, TikTok, YouTube e Threads (e Pinterest em Receitas, Carros e Destinos).
> **Objetivo nº 1:** crescer e chegar à monetização o quanto antes.
> **Pasta no PC:** `G:\Meu Drive\Hypado\06 Projeto\app\manuais\` · **Versão do índice:** 1.0 — 30/09/2026

Cada cargo da operação tem **um manual**. O manual é escrito para uma pessoa **totalmente leiga** e é, ao mesmo tempo, a **especificação** do que o app HP Studio vai fazer sozinho. A ideia é o app ser o mais independente possível da IA: ele faz o que é regra; o Claude fica só com o julgamento (escolha, revisão, texto).

---

## 1. Os 13 manuais

| Nº | Arquivo | Cargo | O que faz, em uma linha | Onde trabalha na esteira | Situação |
|---|---|---|---|---|---|
| 01 | `01_curador.md` | Curador | Escolhe o que vale virar post (fonte oficial, crédito, regras de conteúdo) e larga o pedido | `01_pedidos` | Existe no PC (ainda **sem revisão**) |
| 02 | `02_pauteiro.md` | Pauteiro | Transforma cada vaga do plano semanal em pauta e `pedido.json` (canal, formato, redes, horários) | `01_pedidos` | Existe no PC |
| 03 | `03_editor.md` | Editor | Corta, monta e renderiza o vídeo final (`final.mp4`), com legenda queimada e áudio certo | `04_edicao` | Existe no PC |
| 04 | `04_legendador.md` | Legendador | Transcreve, corrige nomes e gera a legenda (`legenda.ass` / `legenda.srt`) | `03_legenda_dublagem` | Novo — rascunho para revisão |
| 05 | `05_tradutor_dublador.md` | Tradutor e dublador | Traduz para pt-BR natural; dubla só onde é permitido (voz Piper, 4 canais, vídeo próprio) | `03_legenda_dublagem` | Novo — rascunho para revisão |
| 06 | `06_narrador_toque_hp.md` | Narrador "Toque HP" | Pergunta nos 2 primeiros segundos, trecho narrado com voz neutra (onde permitido) e fecho com pergunta | `03_legenda_dublagem` / `04_edicao` | Novo — rascunho para revisão |
| 07 | `07_designer.md` | Designer | Capa, lâminas de carrossel, story, pin | `04_edicao` | Novo — rascunho para revisão |
| 08 | `08_redator.md` | Redator | Texto final de cada rede (`post.json`), crédito, hashtags, "Valores aproximados…" | `04_edicao` | Novo — rascunho para revisão |
| 09 | `09_revisor_qualidade.md` | Revisor de qualidade | Nota de 0 a 10 por critério; aprova (`aprovado.json`) ou devolve (`refazer.json`) | `05_revisao` | Novo — rascunho para revisão |
| 10 | `10_publicador.md` | Publicador | Publica/agenda em cada rede, confere na API, reenvio seguro, stories, aviso "no ar" | `06_agendados` → `07_postados` | Novo — rascunho para revisão |
| 11 | `11_analista_resultados.md` | Analista de resultados | Métricas diárias às 6h, indicadores com fórmula única, relatórios, metas de monetização | `H:\HypadoLocal\metricas\` | Novo — rascunho para revisão |
| 12 | `12_estrategista_marketing.md` | Estrategista de marketing e publicidade | Decide o que postar, onde, formato, horário, quantidade e público — pelos números; plano semanal em JSON | `H:\HypadoLocal\estrategia\` | Novo — rascunho para revisão |
| 13 | `13_comercial_afiliados.md` | Comercial de afiliados | **FUTURO — NÃO IMPLEMENTAR** | — | Só o manual |

---

## 2. A ordem da esteira

### 2.1 As pastas (em `H:\HypadoLocal\esteira\`, etapa 3 do app — a criar)

```
01_pedidos → 02_baixados → 03_legenda_dublagem → 04_edicao → 05_revisao → 06_agendados → 07_postados
                                                                   │
                                                                   └──→ 99_erros (erro de máquina ou item descartado)
```

- **Cada item é uma pasta** com tudo dentro (`pedido.json`, bruto, transcrição, legenda, dublagem, `final.mp4`, capa, `post.json`, `historico.log`...). Nome: `P<0|1|2>_<AAAA-MM-DD>_<HHMM>_<canal>_<assunto-curto>` (ex.: `P1_2026-09-30_1830_gta_rockstar-quinta`).
- **Prioridade no nome:** `P0_` urgente/ao vivo (gol, placar, lançamento, bombástica) — faixa expressa que fura tudo · `P1_` do dia · `P2_` programado.
- **Estáticos** (carrossel, story, texto do Threads, pin) entram em `01_pedidos` com o campo `tipo` e **pulam** as etapas de vídeo (02 e 03).
- O Claude só **larga o pedido** em `01_pedidos`; o app baixa sozinho.

### 2.2 Quem passa o quê para quem

```
                    ┌──────────────────────────────────────────────────────────────┐
                    │   12 ESTRATEGISTA  (sábado: plano da semana; 7h: ajuste)     │
                    │   plano_semana_<AAAA>-W<nn>.json · ajuste_<dia>.json         │
                    └───────────────┬──────────────────────────────────────────────┘
                                    │ vagas (canal, formato, redes, horários, público)
                                    ▼
  01 CURADOR ──── assunto/fonte ───► 02 PAUTEIRO ──── pedido.json ───► [01_pedidos]
  (fonte oficial, crédito,           (1 vaga = 1 item)                     │ app baixa sozinho
   regras de conteúdo; P0)                                                 ▼
                                                                     [02_baixados] bruto
                                                                           │
                               04 LEGENDADOR ◄──────────────────────────────┤
                               transcricao.json, legenda.ass/.srt          │
                               05 TRADUTOR E DUBLADOR (se não for pt)       │
                               traducao.json, dublagem.wav, mix_dublado.wav │
                               06 NARRADOR "TOQUE HP"                       │
                               pergunta de abertura, trecho, fecho          ▼
                                                               [03_legenda_dublagem]
                                                                           │
                               03 EDITOR ──── final.mp4                     │
                               07 DESIGNER ── capa.jpg, lamina_NN.jpg,      │
                                              story.jpg, pin.jpg            │
                               08 REDATOR ─── post.json (texto de cada rede)▼
                                                                    [04_edicao]
                                                                           │
                               09 REVISOR ─── 3 quadros + textos + medidas  ▼
                               aprovado.json  ─────────────────────► [06_agendados]
                               refazer.json   ── volta à etapa do critério de menor nota
                                              ── média < 5: volta ao Curador (01_pedidos)
                               descartado.json ── [99_erros]                │
                                                                           ▼
                               10 PUBLICADOR ─ API (IG, Threads; FB e YT na etapa 4)
                                               TikTok e Pinterest: Claude pelo Chrome (tiktok_ok.json)
                                               story clicável: emulador (fila_story)
                                               publicado.json ──────► [07_postados] ─► aviso "no ar" (WhatsApp)
                                                                           │
                               11 ANALISTA ◄── publicado.json + APIs às 6h ┘
                               metricas\<dia>\*.json, indicadores, relatórios,
                               para_estrategista_<semana>.json ─────────────► 12 ESTRATEGISTA (fecha o ciclo)

  13 COMERCIAL DE AFILIADOS — FUTURO, NÃO IMPLEMENTAR (fora da esteira)
```

### 2.3 Arquivos que passam de um cargo para outro

| Arquivo | Quem escreve | Quem lê | Onde |
|---|---|---|---|
| `plano_semana_<AAAA>-W<nn>.json`, `ajuste_<dia>.json` | 12 Estrategista | 02 Pauteiro, 10 Publicador (conferência) | `H:\HypadoLocal\estrategia\` |
| `pedido.json` | 01 Curador / 02 Pauteiro | todos os cargos da esteira | pasta do item |
| `bruto.mp4` | app (baixa sozinho) | 04, 05, 03 | pasta do item |
| `transcricao.json`, `legenda.ass`, `legenda.srt` | 04 Legendador | 03 Editor, 08 Redator, 09 Revisor | pasta do item |
| `traducao.json`, `dublagem.wav`, `mix_dublado.wav` | 05 Tradutor e dublador | 04, 03, 09 | pasta do item |
| `final.mp4` | 03 Editor | 09 Revisor, 10 Publicador | pasta do item |
| `capa.jpg`, `lamina_NN.jpg`, `story.jpg`, `pin.jpg` | 07 Designer | 09, 10 | pasta do item |
| `post.json` (esquema `hp.post/1`) | 08 Redator | 07 (título da capa), 09, 10 | pasta do item |
| `aprovado.json` / `refazer.json` / `descartado.json` | 09 Revisor | app (move a pasta), cargo de destino | pasta do item |
| `publicado.json`, `tiktok_ok.json`, `pinterest_ok.json` | 10 Publicador (e o Claude no Chrome) | 11 Analista | pasta do item |
| `metricas\<dia>\*.json`, `para_estrategista_<semana>.json` | 11 Analista | 12 Estrategista, painel | `H:\HypadoLocal\metricas\` |
| `historico.log` | todos (uma linha por acontecimento) | todos | pasta do item |

---

## 3. Modelo obrigatório de todo manual

Todo manual (01 a 13) tem, **nesta ordem**, estas seções numeradas:

1. **Objetivo do cargo** — o que o cargo entrega, em uma frase e em lista; metas com número; o que o cargo **não** faz.
2. **Entradas e saídas** — arquivos, campos JSON com **exemplos completos**, pastas; quem escreve e quem lê cada arquivo.
3. **Passo a passo numerado para leigo** — quantos passos precisar (se precisar 50, são 50), com os **comandos exatos do PowerShell** quando houver e o que tem que aparecer na tela.
4. **Regras que nunca se quebram.**
5. **Critérios de qualidade com nota** — tabela com o que é nota **10 / 7 / 5 / 0** em cada critério.
6. **Erros comuns e o que fazer.**
7. **O que o app faz sozinho x o que o Claude decide** — com a **% estimada**.
8. **Ferramentas existentes que já fazem cada passo** — o que **existe** e o que é **(a criar)**.
9. **Testes de aceitação** — com números.

E, no fim, um **glossário** curto. Regras de escrita: português do Brasil, sem jargão sem explicar; toda ferramenta que ainda não existe é marcada **(a criar)**; tudo o que está sendo feito no PC por outra frente é marcado **(em andamento no PC — não mexer)**; toda regra de rede social que muda com frequência é marcada **(conferir na página oficial)**.

---

## 4. Regra do modo sombra de 7 dias (teste de paridade)

**Nada quebra o que funciona.** O app só assume uma tarefa depois de **7 dias seguidos em modo sombra** com qualidade **idêntica comprovada com números**.

### 4.1 Como funciona o modo sombra

1. Durante 7 dias, o trabalho continua sendo feito **do jeito de hoje** (pelo Claude/plantão) e é **isso** que vai ao ar.
2. Em paralelo, o app faz a **mesma** tarefa com os **mesmos** insumos, com `modo: "sombra"`, gravando os arquivos com sufixo (ex.: `final_sombra.mp4`, `capa_sombra.jpg`). **Nada do app é publicado.**
3. A ferramenta `qa_paridade` **(a criar — módulo D)** compara o resultado do app com o do Claude e grava um relatório por item e por dia em `H:\HypadoLocal\app\paridade\<tarefa>\<AAAA-MM-DD>.json`, com nota e veredito.
4. **Um dia reprovado zera a contagem.** Só 7 dias **seguidos** aprovados liberam a tarefa.
5. Mínimo de itens: **3 por dia** por tarefa (ou todos do dia, se houver menos) e **20 no total** nos 7 dias.
6. Terminados os 7 dias, a sessão HP GESTÃO abre **ticket** com o resumo dos números para a tarefa passar de `sombra` para `valendo`. Enquanto isso não acontece, o app continua em sombra.

### 4.2 O que o `qa_paridade` mede (valores-padrão; se o `LEIA.md` do módulo D definir outros, vale o do módulo)

| Medida | Como compara | Passa se |
|---|---|---|
| **Duração** | Duração do vídeo do app × do Claude | Diferença **≤ 0,10 s** |
| **SSIM** (parecença visual, de 0 a 1) | Quadro a quadro, nos mesmos tempos | Média **≥ 0,95** e nenhum trecho de 1 s com média **< 0,90**. Imagens (capa, lâminas): **≥ 0,90** quando o quadro de origem é o mesmo |
| **Loudness** (volume percebido, em LUFS) | Volume integrado e pico | Os dois em **−14 LUFS ± 1**, diferença entre eles **≤ 1 LU**, pico **≤ −1,5 dBTP** |
| **Legenda** | Texto e tempos de cada bloco | Texto **idêntico** depois de normalizar espaços; início e fim de cada bloco **± 0,10 s**; mesmo número de blocos |
| **Lâminas** (carrossel) | Número e ordem | **Mesmo número** e **mesma ordem** (100%); cada lâmina com SSIM **≥ 0,90** |
| **Nota do Revisor** | Revisor (09) avalia as duas versões às cegas | Média do app **≥ média do Claude − 0,2** e **nenhum** critério que bloqueia com nota 0 |

Exemplo do registro de um dia:

```json
{
  "tarefa": "editor_reel",
  "dia": "2026-10-06",
  "itens": [
    { "item": "P1_2026-10-06_1830_gta_rockstar-quinta", "duracao_dif_s": 0.03, "ssim_medio": 0.972, "ssim_pior_1s": 0.931,
      "lufs_app": -14.2, "lufs_claude": -14.0, "legenda_texto_igual": true, "legenda_tempo_max_dif_s": 0.06,
      "laminas": "nao_se_aplica", "nota_revisor_app": 9.1, "nota_revisor_claude": 9.2, "veredito": "igual" }
  ],
  "itens_no_dia": 4,
  "veredito_do_dia": "aprovado",
  "dias_seguidos_aprovados": 3
}
```

### 4.3 Cargos que não produzem vídeo

Publicador, Analista e Estrategista têm paridade **própria**, descrita na seção 9 de cada manual: o Publicador compara conta, texto e horário (±5 min) com o que o plantão publicou, com **0** duplicados; o Analista compara os números com a coleta do plantão (diferença **≤ 2%**); o Estrategista compara o plano do app com o do Claude (mesmo número de itens por canal e dia em **≥ 90%** dos casos, mesmo formato em **≥ 80%** das vagas, **100%** das diferenças explicadas).

---

## 5. Regra de revisão (manual 09)

O Revisor dá **nota de 0 a 10 em cada critério** e calcula a **média**:

| Média | Classe | O que acontece |
|---|---|---|
| **≥ 9,00** | **Excelente** | **Aprovado** → `aprovado.json` → `06_agendados` |
| **7,00 a 8,99** | **Bom** | **Aprovado** → `aprovado.json` → `06_agendados` |
| **5,00 a 6,99** | **Médio** | **Refazer** → `refazer.json` → volta para a **etapa do critério de menor nota** (empate entre etapas: vai para a mais cedo da esteira) |
| **< 5,00** | **Razoável** | **Refazer** → volta ao **Curador** (`01_pedidos`) |

- **Máximo de 2 voltas.** Na 3ª reprovação o item é **descartado** (`descartado.json`, vai para `99_erros`) e o descarte é **registrado**.
- Conteúdo irreparável (vazamento de GTA 6, Flow Games, imagem de transmissão de TV no Futebol) é descartado na hora, sem contar volta.
- Detalhes, critérios e travas: manual 09.

---

## 6. Regras que valem para todos os cargos

- **Segurança:** nunca digitar senha ou código, criar conta, aceitar termos, ler ou imprimir token (tokens ficam em `H:\HypadoLocal\segredos\`; o script lê e nunca mostra), contornar CAPTCHA. Só **API oficial**, **app oficial num emulador Android** ou **página oficial**. Nada de biblioteca que imita protocolo de rede social.
- **Conteúdo:** nada do Flow Games; nada de vazamento de GTA 6; sem trailer puro; futebol sem imagem de transmissão de TV (vídeo oficial do clube/CBF/liga pode, com crédito e áudio original — **nunca narração sintética no futebol**); crédito do criador sempre; música só livre de direitos; valor citado leva "Valores aproximados…"; **nunca clonar voz**; voz sintética só a Piper pt-BR já instalada (`scripts\dublar.py`), e só nos vídeos próprios de Destinos, Receitas, Carros e Filmes.
- **PC:** trabalho pesado 1 por vez (`H:\HypadoLocal\app\pesado.lock`) e **nunca das 18h às 22h30**; processos sem console sempre com `CREATE_NO_WINDOW`.
- **WhatsApp** só para 3 coisas: resumo do dia anterior, aviso "no ar" com links, resumo de sábado. Toda mensagem começa com `*Claude - *`; só os grupos "HP | Comissão 🚀" e os da lista "HP | Grupos"; nunca em primeiro plano. Erro e pedido de ajuda vão por **ticket** (`scripts\tickets.py`).
- **Afiliados é assunto futuro** (manual 13): não desenvolver nada agora.
- **Não mexer** no que está em andamento no PC: etapa 4 (Facebook e YouTube pela API), redução de arquivos do painel público, auditoria da API do YouTube.

---

## 7. Glossário comum

- **API** — porta de serviço oficial de uma rede social para programas publicarem e lerem dados.
- **Esteira** — sequência de pastas por onde cada item passa, de `01_pedidos` a `07_postados`.
- **Item** — uma pasta da esteira; um post (que pode sair em várias redes).
- **LUFS** — unidade do volume percebido; a HP usa −14 LUFS.
- **Modo sombra** — o app faz em paralelo, sem publicar, para provar que faz igual.
- **P0 / P1 / P2** — urgente / do dia / programado.
- **Paridade** — prova com números de que o app faz igual ao Claude (`qa_paridade`, a criar).
- **SSIM** — nota de 0 a 1 de quão parecidas duas imagens são (1 = iguais).
- **Ticket** — pedido registrado em `08 Empresa\tickets\<area>\{novo,fazendo,travado,feito}` pelo `scripts\tickets.py`.
- **Vaga (slot)** — um item planejado pelo Estrategista (canal, formato, redes, horários, público).
