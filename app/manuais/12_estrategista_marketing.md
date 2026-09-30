# Manual 12 — Estrategista de marketing e publicidade

> **Cargo:** Estrategista de marketing e publicidade (decide o que postar, onde, em que formato, a que horas, quantos por dia e para qual público — **pelos números**)
> **Empresa:** Hypado (HP) — 6 perfis: GTA 6 | HP (@hpgta6), Futebol | HP (@hp.futebol), Filmes e Séries | HP (@hp.filmes), Receitas | HP (@hp.receitas), Carros | HP (@hp.carros), Destinos | HP (@hp.destinos)
> **Versão:** 1.0 — 30/09/2026
> **Pasta deste manual no PC:** `G:\Meu Drive\Hypado\06 Projeto\app\manuais\12_estrategista_marketing.md`
> **Quem vem antes:** 11 Analista de resultados (`para_estrategista_<semana>.json`) · **Quem vem depois:** 02 Pauteiro (lê o plano da semana e transforma cada vaga em pauta)
> **Por que este cargo existe (palavras do Antônio):** sem ele, a HP "produz muito conteúdo onde não precisa e não chega na monetização".

---

## Como ler este manual (para quem nunca fez isso)

- Escrito para uma pessoa **totalmente leiga** em marketing. Não precisa "ter feeling": este cargo trabalha com **regras escritas e contas simples**. Quando os números mandam cortar, corta; quando mandam reforçar, reforça. O "feeling" entra só onde o manual diz que o Claude decide (seção 7).
- Comandos vão em blocos cinza para colar no **PowerShell**.
- Marcações: **(existe)** · **(a criar)** · **(em andamento no PC — não mexer)** · **(conferir na página oficial)**.
- Números de exemplo (alcance, seguidores, notas) são **inventados** para ensinar a conta.
- Hora sempre de **Brasília**. Semanas no padrão ISO: `2026-W42` = segunda 12/10 a domingo 18/10/2026.

### Preparação do PowerShell (uma vez por janela)

```powershell
$py      = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
$app     = "G:\Meu Drive\Hypado\06 Projeto\app\hp_studio"
$est     = "H:\HypadoLocal\estrategia"
$met     = "H:\HypadoLocal\metricas"
Set-Location $app
```

---

## 1. Objetivo do cargo

### 1.1 Em uma frase

Transformar os números do Analista num **plano semanal** (e num **ajuste diário**) que diz, para cada um dos 6 canais: **o que** produzir, **em que formato**, **em quais redes** publicar, **a que horas**, **quantos por dia** e **para qual público** — sempre escolhendo o caminho que **chega mais rápido à monetização com o menor trabalho**.

### 1.2 As 3 perguntas que o Estrategista responde toda semana

1. **Onde está o retorno?** Qual canal, rede, formato e horário traz mais **seguidor por visualização** e mais **visualização por item produzido**.
2. **Onde está o desperdício?** O que está sendo produzido e **não volta** (formato fraco, rede que não converte, horário morto). Isso é cortado.
3. **O que falta para monetizar?** Para cada canal e rede: qual requisito falta, em quantos dias bate no ritmo atual, e **o que acelera** (mais vídeos longos no TikTok? mais Shorts no YouTube?).

### 1.3 O que o Estrategista entrega

| Entrega | Quando | Onde |
|---|---|---|
| **Plano da semana** (JSON) — vagas de produção com canal, formato, redes, horários, público, prioridade, testes | **Sábado até 12h**, valendo de segunda 00h a domingo 23h59 | `H:\HypadoLocal\estrategia\planos\plano_semana_<AAAA>-W<nn>.json` **(a criar)** |
| **Registro das decisões** (por que cada mudança, com número) | Junto com o plano | `H:\HypadoLocal\estrategia\decisoes\decisoes_<AAAA>-W<nn>.md` **(a criar)** |
| **Ajuste do dia** (acrescentar, tirar ou mudar vagas por causa de P0, destaque ou alerta) | Todo dia às **7h** (e na hora, para P0) | `H:\HypadoLocal\estrategia\ajustes\ajuste_<AAAA-MM-DD>.json` **(a criar)** |
| **Registro de testes A/B** | Sempre que abre ou fecha um teste | `H:\HypadoLocal\estrategia\testes_ab.json` **(a criar)** |
| **Calendário de eventos** (GTA 6, futebol, estreias, feriados) | Atualizado toda semana; revisado todo mês | `H:\HypadoLocal\estrategia\calendario_eventos.json` **(a criar)** |
| **Matriz atual** (cada combinação canal × rede × formato × faixa com sua nota de prioridade) | Com o plano | `H:\HypadoLocal\estrategia\matriz_<AAAA>-W<nn>.json` **(a criar)** |

### 1.4 Como saber se o Estrategista está indo bem

| Indicador (medido pelo Analista, manual 11) | Meta |
|---|---|
| **Dias estimados até a 1ª monetização** de cada canal (a rede mais perto) | Cair semana a semana |
| **Eficiência**: seguidores ganhos por item produzido (somando as redes) | Subir semana a semana na média da HP |
| **Cumprimento do plano** (vagas publicadas ÷ vagas planejadas) | **≥ 90%** |
| Decisões registradas **com número** | **100%** |
| Plano dentro da **capacidade** da esteira | **100%** das semanas |
| Vagas usadas em **testes A/B** | **≤ 20%** |
| Semanas com **mais de 3 mudanças grandes** por canal | **0** (regra R15) |

### 1.5 O que o Estrategista NÃO faz

- **Não escolhe o assunto específico** de cada post (qual notícia, qual receita). Isso é do **Curador** (manual 01) e do **Pauteiro** (manual 02). O Estrategista diz "terça 18h30, GTA, reel de notícia, público gamer 16–30"; o Pauteiro acha a melhor notícia para essa vaga.
- **Não publica, não edita, não aprova.**
- **Não quebra regra de conteúdo nem de segurança por causa de número** (regra R20): se "trailer puro" viraliza, continua proibido; se voz sintética rende bem, continua proibida no Futebol e no GTA.
- **Não mexe em afiliados nem publicidade paga** (manual 13 é **FUTURO**). "Publicidade" neste cargo quer dizer **divulgação orgânica** dos próprios perfis (stories, destaques, página de links, chamadas entre canais).
- **Não gasta dinheiro** (impulsionamento, anúncio pago): fora do escopo até o Antônio decidir.

### 1.6 Público de cada canal (hipóteses iniciais — confirmar com os dados)

O "para qual público" do plano começa destas **hipóteses** e é corrigido pelos dados de público que as redes mostram (idade, gênero, cidades, horários em que os seguidores estão on-line — Instagram, TikTok Studio e, quando autorizado, YouTube Analytics). O Analista inclui o bloco `publico` no arquivo para o Estrategista **1 vez por mês** **(a criar no módulo `metricas`)**.

| Canal | Público-alvo (hipótese) | O que esse público quer | Quando costuma estar on-line (hipótese) |
|---|---|---|---|
| GTA 6 \| HP | 16–30 anos, maioria masculina, gamers do Brasil | Novidade oficial, contagem regressiva, curiosidade, "o que vai ter no jogo", comunidade | Almoço (12–14h) e noite (19–23h); fim de semana à tarde |
| Futebol \| HP | 18–45 anos, torcedores de clubes brasileiros | Gol, placar, tabela, debate, estatística | Logo depois dos jogos; manhã seguinte (resultado); intervalo de trabalho |
| Filmes e Séries \| HP | 18–40 anos, assinantes de streaming | Onde assistir, estreias, curiosidades, listas | Noite (20–23h), sexta e fim de semana |
| Receitas \| HP | 25–55 anos (hipótese: maioria feminina) | Receita rápida, barata, passo a passo que dá para salvar | Manhã (9–11h) e fim de tarde (16–18h, antes do jantar); domingo |
| Carros \| HP | 20–50 anos, maioria masculina | Lançamentos, comparativos, "quanto custa manter", ficha técnica | Almoço e noite |
| Destinos \| HP | 25–50 anos, viagem econômica | Roteiro, quanto custa, dica de feriado | Noite (planejamento) e 10 dias antes de feriado prolongado |

---

## 2. Entradas e saídas

### 2.1 Mapa de pastas

```
H:\HypadoLocal\
├── metricas\relatorios\
│   ├── para_estrategista_<AAAA>-W<nn>.json    ← ENTRADA principal (manual 11, passo 78)
│   └── semanal_<AAAA>-W<nn>.md                 ← leitura de apoio
├── metricas\<dia>\indicadores_<dia>.json       ← ENTRADA do ajuste diário
├── estrategia\                                 (a criar)
│   ├── config\
│   │   ├── capacidade.json                     ← quanto a esteira aguenta por dia
│   │   ├── catalogo_formatos.json              ← formatos que existem, por canal, com custo
│   │   └── pesos.json                          ← pesos da fórmula de prioridade e limites da casa
│   ├── calendario_eventos.json
│   ├── testes_ab.json
│   ├── planos\plano_semana_<AAAA>-W<nn>.json    ← SAÍDA principal (o Pauteiro lê)
│   ├── ajustes\ajuste_<AAAA-MM-DD>.json         ← SAÍDA diária
│   ├── decisoes\decisoes_<AAAA>-W<nn>.md        ← SAÍDA: o porquê de cada mudança
│   └── matriz_<AAAA>-W<nn>.json                 ← SAÍDA: notas de prioridade
G:\Meu Drive\Hypado\07 Canais\Futebol\PLANO_CRESCIMENTO.md   ← ENTRADA (existe) para o Futebol
```

### 2.2 Entrada 1 — `para_estrategista_<AAAA>-W<nn>.json` (do Analista)

Esquema completo e exemplo no **manual 11, passo 78**. Os campos que o Estrategista usa:

| Campo | Usado em |
|---|---|
| `qualidade_dados.cobertura_pct` | Regra R14 (semana anômala) |
| `canais.<c>.resumo.eficiencia_seg_por_item` | Regra R17 (eficiência) |
| `canais.<c>.redes.<r>.seguidores_por_mil_views` | Regra R05 (rede de baixo retorno) e fórmula (S) |
| `canais.<c>.redes.<r>.formatos.<f>.razao_vs_canal`, `n`, `semanas_abaixo_50`, `semanas_acima_150` | Regras R01 a R04 e fórmula (A) |
| `...formatos.<f>.te_pct`, `retencao_pct`, `seg_por_mil` | Fórmula (E, R, S) e regras R08 a R10 |
| `canais.<c>.redes.<r>.faixas.<faixa>.razao_vs_melhor`, `n` | Regras R06 e R07 |
| `canais.<c>.monetizacao[]` | Regra R11 e fator M |
| `canais.<c>.testes_ab[]` | Bloco F (fechar testes, aplicar vencedor) |
| `regras_disparadas[]` | Conferência: o app do Estrategista recalcula e tem que chegar nas **mesmas** regras |

### 2.3 Entrada 2 — `capacidade.json` **(a criar)**

Quanto a esteira (app + Claude) consegue produzir **por dia** sem atrasar nada. Os números do exemplo são **ponto de partida**; o plantão ajusta ao real depois de 2 semanas medindo.

```json
{
  "versao_esquema": 1,
  "atualizado_em": "2026-09-30T18:00:00-03:00",
  "por_dia": {
    "itens_video": 26,
    "itens_video_com_voz": 6,
    "itens_reel_futebol": 6,
    "itens_estatico": 14,
    "pins_estaticos": 12,
    "textos_threads": 24,
    "stories_clicaveis": 18,
    "stories_programados": 8,
    "revisoes_claude": 45
  },
  "reserva_p0_padrao": {
    "gta": 1,
    "futebol_dia_sem_jogo": 1,
    "futebol_dia_com_jogo": 4,
    "filmes": 0,
    "receitas": 0,
    "carros": 0,
    "destinos": 0
  },
  "piso_itens_dia_por_canal": 2,
  "observacao": "trabalho pesado 1 por vez e nunca das 18h às 22h30; publicar e story não são pesados"
}
```

- `itens_*` contam **itens** (pastas da esteira). **Um vídeo que sai em 5 redes é 1 item.**
- `itens_video_com_voz`: vídeos com voz sintética (Piper, `scripts\dublar.py`) — só em Destinos, Receitas, Carros e Filmes, e só em vídeos próprios.
- `itens_estatico` conta carrosséis e fotos; `pins_estaticos` e `textos_threads` têm capacidade própria porque são baratos (quase sempre reaproveitam arte ou texto de outro item).
- `revisoes_claude`: quantas revisões o Revisor (manual 09) consegue fazer por dia; o plano **nunca** pede mais itens do que isso.

### 2.4 Entrada 3 — `catalogo_formatos.json` **(a criar)**

A lista fechada de formatos por canal. **O plano só usa formatos que estão no catálogo.** Formato novo entra primeiro no catálogo (com custo e regras) e depois como **teste** (bloco F).

```json
{
  "versao_esquema": 1,
  "formatos": {
    "reel_contagem":        { "canais": ["gta"], "tipo": "reel", "custo": 1.5, "voz": "proibida", "redes": ["instagram","tiktok","youtube","facebook","threads"], "fixo_por_dia": 1, "descricao": "Arte 'faltam X dias' + 1 curiosidade oficial; até 19/11/2026" },
    "reel_noticia":         { "canais": ["gta","filmes","carros"], "tipo": "reel", "custo": 2.0, "voz": "conforme_canal", "redes": ["instagram","tiktok","youtube","facebook","threads"] },
    "reel_curiosidade":     { "canais": ["gta","filmes","carros","destinos"], "tipo": "reel", "custo": 2.0, "voz": "conforme_canal", "redes": ["instagram","tiktok","youtube","facebook"] },
    "reel_criador":         { "canais": ["gta","filmes"], "tipo": "reel", "custo": 1.5, "voz": "proibida", "redes": ["instagram","tiktok","youtube","facebook"], "descricao": "Corte de criador com crédito + Toque HP" },
    "reel_gol":             { "canais": ["futebol"], "tipo": "reel", "custo": 1.5, "voz": "proibida", "redes": ["instagram","tiktok","youtube","facebook"], "descricao": "reel_futebol.py modo gol: vídeo oficial com áudio original" },
    "reel_futebol_noticia": { "canais": ["futebol"], "tipo": "reel", "custo": 2.0, "voz": "proibida", "redes": ["instagram","tiktok","youtube","facebook"] },
    "reel_debate":          { "canais": ["futebol"], "tipo": "reel", "custo": 2.0, "voz": "proibida", "redes": ["instagram","tiktok","youtube","facebook"] },
    "reel_estatistica":     { "canais": ["futebol"], "tipo": "reel", "custo": 2.0, "voz": "proibida", "redes": ["instagram","tiktok","youtube"] },
    "reel_resultado":       { "canais": ["futebol"], "tipo": "reel", "custo": 1.0, "voz": "proibida", "redes": ["instagram","tiktok","facebook"] },
    "reel_tabela":          { "canais": ["futebol"], "tipo": "reel", "custo": 1.0, "voz": "proibida", "redes": ["instagram","tiktok"] },
    "reel_trailer_comentado": { "canais": ["filmes"], "tipo": "reel", "custo": 2.5, "voz": "permitida_piper", "redes": ["instagram","tiktok","youtube","facebook"], "descricao": "Nunca trailer puro: sempre com comentário/Toque HP" },
    "reel_onde_assistir":   { "canais": ["filmes"], "tipo": "reel", "custo": 2.0, "voz": "permitida_piper", "redes": ["instagram","tiktok","youtube","facebook"] },
    "reel_receita":         { "canais": ["receitas"], "tipo": "reel", "custo": 2.5, "voz": "permitida_piper", "redes": ["instagram","tiktok","youtube","facebook","pinterest"] },
    "reel_dica":            { "canais": ["receitas","carros","destinos"], "tipo": "reel", "custo": 2.0, "voz": "permitida_piper", "redes": ["instagram","tiktok","youtube","facebook"] },
    "reel_lancamento":      { "canais": ["carros"], "tipo": "reel", "custo": 2.0, "voz": "permitida_piper", "redes": ["instagram","tiktok","youtube","facebook"] },
    "reel_comparativo":     { "canais": ["carros"], "tipo": "reel", "custo": 2.5, "voz": "permitida_piper", "redes": ["instagram","tiktok","youtube","facebook"], "exige": "Valores aproximados…" },
    "reel_roteiro":         { "canais": ["destinos"], "tipo": "reel", "custo": 2.5, "voz": "permitida_piper", "redes": ["instagram","tiktok","youtube","facebook","pinterest"] },
    "reel_quanto_custa":    { "canais": ["destinos","receitas","carros"], "tipo": "reel", "custo": 2.5, "voz": "permitida_piper", "redes": ["instagram","tiktok","youtube","facebook"], "exige": "Valores aproximados…" },
    "reel_longo_60":        { "canais": ["receitas","destinos","carros","filmes"], "tipo": "reel", "custo": 3.0, "voz": "permitida_piper", "redes": ["tiktok","youtube","instagram","facebook"], "descricao": "Vídeo próprio > 60 s (monetização do TikTok, se disponível)" },
    "carrossel_lista":      { "canais": ["gta","filmes","carros","destinos"], "tipo": "carrossel", "custo": 2.0, "voz": "nao_se_aplica", "redes": ["instagram","facebook","threads"] },
    "carrossel_receita":    { "canais": ["receitas"], "tipo": "carrossel", "custo": 2.0, "voz": "nao_se_aplica", "redes": ["instagram","facebook","pinterest"] },
    "carrossel_rodada":     { "canais": ["futebol"], "tipo": "carrossel", "custo": 1.5, "voz": "nao_se_aplica", "redes": ["instagram","facebook","threads"] },
    "pin_estatico":         { "canais": ["receitas","carros","destinos"], "tipo": "foto", "custo": 1.0, "voz": "nao_se_aplica", "redes": ["pinterest"] },
    "threads_texto":        { "canais": ["gta","futebol","filmes","receitas","carros","destinos"], "tipo": "texto", "custo": 0.5, "voz": "nao_se_aplica", "redes": ["threads"] },
    "story_enquete":        { "canais": ["gta","futebol","filmes","receitas","carros","destinos"], "tipo": "story", "custo": 0.5, "voz": "nao_se_aplica", "redes": ["instagram"], "descricao": "Pelo emulador (story_post.py); pergunta ≤ ~25 caracteres" },
    "story_contagem":       { "canais": ["gta"], "tipo": "story", "custo": 0.5, "voz": "nao_se_aplica", "redes": ["instagram"], "fixo_por_dia": 1 }
  }
}
```

- `custo` (1 a 3; 0,5 para texto e story) é o **C** da fórmula de prioridade (bloco D).
- `voz`: `proibida` (GTA e Futebol: **nunca** voz sintética; no Futebol, **nunca narração sintética** e o vídeo de gol vai **com o áudio original**), `permitida_piper` (só Destinos, Receitas, Carros e Filmes, só vídeos próprios, só a voz Piper pt-BR já instalada, **nunca clonar voz**), `conforme_canal` (proibida em GTA; permitida_piper nos 4 canais liberados), `nao_se_aplica`.
- `fixo_por_dia`: formato de cadência fixa (não é distribuído pela fórmula).

### 2.5 Entrada 4 — `calendario_eventos.json` **(a criar)**

```json
{
  "versao_esquema": 1,
  "atualizado_em": "2026-10-10T08:00:00-03:00",
  "eventos": [
    { "id": "gta6-lancamento", "canal": "gta", "data": "2026-11-19", "tipo": "lancamento", "peso": "maximo", "fonte": "anúncio oficial da Rockstar (conferir horário de liberação na página oficial)" },
    { "id": "feriado-2026-10-12", "canal": "todos", "data": "2026-10-12", "tipo": "feriado_nacional", "nota": "segunda; feriado prolongado — Destinos prepara roteiro 10 dias antes" },
    { "id": "halloween-2026", "canal": "receitas", "data": "2026-10-31", "tipo": "data_tematica" },
    { "id": "feriado-2026-11-02", "canal": "todos", "data": "2026-11-02", "tipo": "feriado_nacional", "nota": "segunda; feriado prolongado" },
    { "id": "feriado-2026-11-15", "canal": "todos", "data": "2026-11-15", "tipo": "feriado_nacional", "nota": "domingo" },
    { "id": "feriado-2026-11-20", "canal": "todos", "data": "2026-11-20", "tipo": "feriado_nacional", "nota": "sexta; um dia depois do lançamento do GTA 6" },
    { "id": "black-friday-2026", "canal": "todos", "data": "2026-11-27", "tipo": "data_comercial", "nota": "sem publi e sem afiliado (manual 13 é FUTURO)" },
    { "id": "natal-2026", "canal": "receitas", "data": "2026-12-25", "tipo": "data_tematica", "nota": "ceia: começar 20 dias antes" },
    { "id": "rodada-brasileirao-exemplo", "canal": "futebol", "data": "2026-10-18", "tipo": "jogos", "fonte": "tabela oficial da CBF (conferir)", "reserva_p0": 4 }
  ]
}
```

Regra: **toda data de jogo, estreia ou lançamento vem de fonte oficial** (site da Rockstar, tabela da CBF/liga, anúncio oficial do estúdio/streaming) e fica anotada em `fonte`. Data de boato **não entra**. Nada de vazamento de GTA 6.

### 2.6 Saída principal — o plano da semana (`plano_semana_<AAAA>-W<nn>.json`) — o esquema que o Pauteiro consome

#### 2.6.1 Ideia central: 1 vaga = 1 item a produzir

O plano é uma lista de **vagas** (`slots`). **Cada vaga é 1 item** que a esteira vai produzir (uma pasta em `01_pedidos`). Dentro da vaga vai a lista de **redes** em que o item sai, cada uma com seu **horário**. Assim, um vídeo que sai em 5 redes é **uma** vaga (e conta **1** na capacidade), e o Pauteiro faz **uma** pauta para ele.

#### 2.6.2 Campos do nível de cima

| Campo | Tipo | Obrigatório | O que é |
|---|---|---|---|
| `versao_esquema` | número | sim | Hoje `1`. Muda quando o formato do arquivo mudar |
| `semana` | texto `AAAA-Wnn` | sim | Semana ISO do plano (ex.: `2026-W42`) |
| `valido_de` / `valido_ate` | data e hora com fuso | sim | Segunda 00:00 e domingo 23:59 |
| `gerado_em` | data e hora | sim | Quando o plano foi gerado |
| `gerado_por` | `app` ou `claude` | sim | Quem gerou (no modo sombra existem os dois) |
| `base` | objeto | sim | Arquivo do Analista usado e a janela de dados |
| `capacidade` | objeto | sim | Capacidade usada × disponível por dia |
| `canais` | objeto | sim | Um bloco por canal (2.6.3) |
| `testes_ab` | lista | sim (pode ser vazia) | Testes rodando nesta semana |
| `decisoes` | lista | sim | Cada mudança em relação à semana anterior, com a regra e os números |

#### 2.6.3 Campos de cada canal (`canais.<canal>`)

| Campo | Tipo | O que é |
|---|---|---|
| `objetivo_semana` | texto curto | Ex.: "acelerar views de Shorts (monetização YouTube)" |
| `publico` | texto curto | Público principal da semana (1.6) |
| `fase` | texto | Só GTA: `aquecimento`, `reta_final`, `lancamento`, `pos_lancamento` |
| `limites` | objeto | `max_posts_dia_por_rede`, `intervalo_minimo_min`, `max_stories_clicaveis_dia` |
| `reservas_p0` | lista | Capacidade guardada para urgente (gol, anúncio oficial) |
| `stories_programados` | lista | Stories que não dependem de post (enquete das 16h, contagem) |
| `slots` | lista | As vagas (2.6.4) |

#### 2.6.4 Campos de cada vaga (`slots[]`)

| Campo | Tipo | Obrigatório | O que é | Exemplo |
|---|---|---|---|---|
| `slot_id` | texto | sim | Identificador único: `<semana>-<canal>-<dia da semana>-<nº>` | `2026-W42-gta-seg-01` |
| `dia` | data | sim | Dia da publicação principal | `2026-10-12` |
| `canal` | texto | sim | Um dos 6 | `gta` |
| `formato` | texto | sim | Do `catalogo_formatos.json` | `reel_contagem` |
| `tipo` | texto | sim | `reel`, `carrossel`, `foto`, `story`, `texto` | `reel` |
| `pilar` | texto | sim | Linha editorial (para o Pauteiro achar o assunto) | `contagem_regressiva` |
| `publico` | texto | sim | Para quem é | `gamers 16-30` |
| `prioridade` | `P1` ou `P2` | sim | P0 **não** é planejado (vem da reserva) | `P1` |
| `redes` | lista | sim | Cada rede com `rede`, `hora` (`HH:MM`) e `formato_rede` | ver exemplo |
| `duracao_alvo_s` | [mín, máx] | vídeo | Faixa de duração pedida ao Editor | `[18, 30]` |
| `narracao` | texto | sim | `nenhuma`, `toque_hp_texto`, `toque_hp_voz_piper`, `dublagem_piper` | `toque_hp_texto` |
| `story` | objeto | não | `divulgacao` (true/false), `clicavel` (true/false), `destaque` | `{"divulgacao": true, "clicavel": true, "destaque": "Contagem"}` |
| `teste_ab` | objeto ou null | sim | `{ "id": ..., "variante": "A" ou "B", "o_que_muda": ... }` | `null` |
| `regra_origem` | lista | sim | Regras que criaram ou mudaram esta vaga | `["R18"]` |
| `nota_prioridade` | número | sim | O **P** da fórmula (bloco D) da célula de origem | `0.98` |
| `observacoes` | texto | não | Instrução para o Pauteiro/Editor | `"marco: faltam 35 dias"` |

#### 2.6.5 Exemplo completo (cortado a 1 canal e 1 dia para caber; o arquivo real tem os 6 canais × 7 dias)

```json
{
  "versao_esquema": 1,
  "semana": "2026-W42",
  "valido_de": "2026-10-12T00:00:00-03:00",
  "valido_ate": "2026-10-18T23:59:59-03:00",
  "gerado_em": "2026-10-10T10:42:18-03:00",
  "gerado_por": "app",
  "base": {
    "arquivo_analista": "H:\\HypadoLocal\\metricas\\relatorios\\para_estrategista_2026-W42.json",
    "janela_posts_7d": { "de": "2026-09-30", "ate": "2026-10-06" },
    "cobertura_pct": 98.9
  },
  "capacidade": {
    "por_dia_disponivel": { "itens_video": 26, "itens_video_com_voz": 6, "itens_reel_futebol": 6, "itens_estatico": 14 },
    "por_dia_planejado_max": { "itens_video": 23, "itens_video_com_voz": 5, "itens_reel_futebol": 4, "itens_estatico": 11 },
    "folga_pct": 11.5
  },
  "canais": {
    "gta": {
      "objetivo_semana": "crescer TikTok (10 mil seguidores) e acelerar views de Shorts",
      "publico": "gamers 16-30, Brasil",
      "fase": "aquecimento",
      "limites": {
        "max_posts_dia_por_rede": { "instagram": 4, "tiktok": 4, "youtube": 3, "facebook": 3, "threads": 6 },
        "intervalo_minimo_min": 60,
        "max_stories_clicaveis_dia": 4
      },
      "reservas_p0": [
        { "dia": "todos", "itens": 1, "motivo": "anúncio oficial da Rockstar", "liberar_as": "22:30" }
      ],
      "stories_programados": [
        { "dia": "2026-10-12", "hora": "09:00", "formato": "story_contagem", "texto": "Faltam 38 dias", "destaque": "Contagem" },
        { "dia": "2026-10-12", "hora": "16:00", "formato": "story_enquete", "pergunta_sugerida": "Vai jogar no dia 1?", "opcoes": ["Sim!", "Depois"], "destaque": "Enquetes" }
      ],
      "slots": [
        {
          "slot_id": "2026-W42-gta-seg-01",
          "dia": "2026-10-12",
          "canal": "gta",
          "formato": "reel_contagem",
          "tipo": "reel",
          "pilar": "contagem_regressiva",
          "publico": "gamers 16-30",
          "prioridade": "P1",
          "redes": [
            { "rede": "instagram", "hora": "18:30", "formato_rede": "reels" },
            { "rede": "tiktok",    "hora": "19:00", "formato_rede": "video" },
            { "rede": "youtube",   "hora": "19:30", "formato_rede": "shorts" },
            { "rede": "threads",   "hora": "18:35", "formato_rede": "texto_video" }
          ],
          "duracao_alvo_s": [18, 30],
          "narracao": "toque_hp_texto",
          "story": { "divulgacao": true, "clicavel": true, "destaque": "Contagem" },
          "teste_ab": null,
          "regra_origem": ["R18"],
          "nota_prioridade": 0.98,
          "observacoes": "faltam 38 dias; 1 curiosidade oficial confirmada; sem vazamento"
        },
        {
          "slot_id": "2026-W42-gta-seg-02",
          "dia": "2026-10-12",
          "canal": "gta",
          "formato": "reel_noticia",
          "tipo": "reel",
          "pilar": "noticia_oficial",
          "publico": "gamers 16-30",
          "prioridade": "P1",
          "redes": [
            { "rede": "instagram", "hora": "12:30", "formato_rede": "reels" },
            { "rede": "tiktok",    "hora": "13:00", "formato_rede": "video" },
            { "rede": "youtube",   "hora": "13:30", "formato_rede": "shorts" }
          ],
          "duracao_alvo_s": [20, 35],
          "narracao": "toque_hp_texto",
          "story": { "divulgacao": true, "clicavel": true, "destaque": "Notícias" },
          "teste_ab": { "id": "AB-2026-W42-gta-capa", "variante": "A", "o_que_muda": "capa com número grande" },
          "regra_origem": ["R02"],
          "nota_prioridade": 0.54,
          "observacoes": ""
        },
        {
          "slot_id": "2026-W42-gta-seg-03",
          "dia": "2026-10-12",
          "canal": "gta",
          "formato": "threads_texto",
          "tipo": "texto",
          "pilar": "debate",
          "publico": "gamers 16-30",
          "prioridade": "P2",
          "redes": [ { "rede": "threads", "hora": "21:00", "formato_rede": "texto" } ],
          "duracao_alvo_s": null,
          "narracao": "nenhuma",
          "story": null,
          "teste_ab": null,
          "regra_origem": [],
          "nota_prioridade": 0.61,
          "observacoes": "pergunta aberta para gerar respostas"
        }
      ]
    }
  },
  "testes_ab": [
    { "id": "AB-2026-W42-gta-capa", "canal": "gta", "rede": "instagram", "variavel": "capa", "a": "capa com número grande", "b": "capa com rosto de personagem", "metrica": "alcance_d3", "min_posts_por_lado": 5, "inicio": "2026-10-12", "fim_max": "2026-10-25", "status": "rodando" }
  ],
  "decisoes": [
    { "regra": "R03", "canal": "filmes", "rede": "instagram", "formato": "carrossel_lista", "antes": 4, "depois": 1, "numeros": "razão 0,38 (< 0,50) pela 2ª semana; n=4", "texto": "pausa de 2 semanas; 1 post de teste por semana com capa nova" },
    { "regra": "R02", "canal": "gta", "rede": "tiktok", "formato": "reel_noticia", "antes": 10, "depois": 14, "numeros": "razão 1,62 (≥ 1,50); n=10", "texto": "+50% limitado ao teto de 4 por dia no TikTok" }
  ]
}
```

#### 2.6.6 Esquema formal (para o app validar)

O módulo do Estrategista **(a criar)** valida o plano com este esquema (JSON Schema, resumido nos campos obrigatórios):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "plano_semana HP v1",
  "type": "object",
  "required": ["versao_esquema", "semana", "valido_de", "valido_ate", "gerado_em", "gerado_por", "base", "capacidade", "canais", "testes_ab", "decisoes"],
  "properties": {
    "versao_esquema": { "const": 1 },
    "semana": { "type": "string", "pattern": "^\\d{4}-W\\d{2}$" },
    "gerado_por": { "enum": ["app", "claude"] },
    "canais": {
      "type": "object",
      "propertyNames": { "enum": ["gta", "futebol", "filmes", "receitas", "carros", "destinos"] },
      "additionalProperties": {
        "type": "object",
        "required": ["objetivo_semana", "publico", "limites", "reservas_p0", "stories_programados", "slots"],
        "properties": {
          "slots": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["slot_id", "dia", "canal", "formato", "tipo", "pilar", "publico", "prioridade", "redes", "narracao", "teste_ab", "regra_origem", "nota_prioridade"],
              "properties": {
                "slot_id": { "type": "string", "pattern": "^\\d{4}-W\\d{2}-[a-z]+-(seg|ter|qua|qui|sex|sab|dom)-\\d{2}$" },
                "tipo": { "enum": ["reel", "carrossel", "foto", "story", "texto"] },
                "prioridade": { "enum": ["P1", "P2"] },
                "narracao": { "enum": ["nenhuma", "toque_hp_texto", "toque_hp_voz_piper", "dublagem_piper"] },
                "redes": {
                  "type": "array", "minItems": 1,
                  "items": {
                    "type": "object", "required": ["rede", "hora"],
                    "properties": {
                      "rede": { "enum": ["instagram", "threads", "facebook", "youtube", "tiktok", "pinterest"] },
                      "hora": { "type": "string", "pattern": "^([01]\\d|2[0-3]):[0-5]\\d$" }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

Além do esquema, o validador confere **regras de negócio** (se qualquer uma falhar, o plano **não** é entregue):
1. `narracao` com `piper` **só** em `filmes`, `receitas`, `carros`, `destinos`. Em `futebol` e `gta`: só `nenhuma` ou `toque_hp_texto`.
2. `pinterest` **só** em `receitas`, `carros`, `destinos`.
3. Cada `formato` existe no catálogo **para aquele canal**.
4. Soma de itens por dia ≤ capacidade de cada tipo (2.3).
5. Nenhuma rede passa de `max_posts_dia_por_rede` no dia.
6. Posts do feed da mesma conta e rede com pelo menos `intervalo_minimo_min` de distância.
7. Vagas com `teste_ab` ≤ **20%** das vagas do canal na semana.
8. `slot_id` único na semana.
9. Todo canal com **pelo menos** `piso_itens_dia_por_canal` itens por dia (2.3).

#### 2.6.7 Como o Pauteiro (manual 02) usa o plano

1. Lê as vagas do dia (plano da semana **mais** o ajuste do dia, 2.7).
2. Para cada vaga, acha o **assunto** que encaixa em `canal` + `formato` + `pilar` + `publico` e cria o pedido em `01_pedidos` **copiando** `slot_id`, `formato` (vira `formato_estrategia`), `teste_ab`, `redes` e `duracao_alvo_s`.
3. Se **não houver assunto bom** para a vaga, o Pauteiro marca a vaga como `vazia` com o motivo. **Não se enche linguiça**: vaga vazia é melhor que post ruim (post ruim derruba a média do canal e ensina errado o algoritmo).
4. Campo que o Pauteiro não conhecer ele **ignora** e registra um aviso no log (assim o plano pode ganhar campos novos sem quebrar a etapa 2).

### 2.7 Saída diária — `ajuste_<AAAA-MM-DD>.json`

Pequeno "remendo" no plano do dia. O Pauteiro aplica **por cima** do plano da semana.

```json
{
  "versao_esquema": 1,
  "dia": "2026-10-13",
  "gerado_em": "2026-10-13T07:04:51-03:00",
  "adicionar": [
    {
      "slot_id": "2026-W42-gta-ter-90",
      "dia": "2026-10-13", "canal": "gta", "formato": "reel_noticia", "tipo": "reel",
      "pilar": "continuacao_destaque", "publico": "gamers 16-30", "prioridade": "P1",
      "redes": [ { "rede": "instagram", "hora": "20:30", "formato_rede": "reels" }, { "rede": "tiktok", "hora": "21:00", "formato_rede": "video" } ],
      "duracao_alvo_s": [20, 35], "narracao": "toque_hp_texto", "teste_ab": null,
      "regra_origem": ["R16"], "nota_prioridade": 0.9,
      "observacoes": "continuação do post de ontem com IDR 2,4 (mesmo assunto, ângulo novo)"
    }
  ],
  "remover": [ { "slot_id": "2026-W42-gta-ter-04", "motivo": "capacidade usada pelo destaque (R16)" } ],
  "mover": [ { "slot_id": "2026-W42-filmes-ter-02", "rede": "instagram", "hora_nova": "20:00", "motivo": "R06: faixa 12-14 a 0,61 da melhor" } ],
  "congelar_cortes": false,
  "observacoes": ""
}
```

Numeração: vagas criadas pelo ajuste usam números **de 90 para cima** (`-90`, `-91`...), para nunca colidir com as do plano.

### 2.8 Saída — `testes_ab.json`

Registro de **todos** os testes (rodando, concluídos, cancelados). Um teste por entrada:

```json
{
  "versao_esquema": 1,
  "testes": [
    {
      "id": "AB-2026-W42-gta-capa",
      "canal": "gta",
      "rede": "instagram",
      "formato": "reel_noticia",
      "hipotese": "Capa com número grande traz mais alcance que capa com rosto",
      "variavel": "capa",
      "a": "capa com número grande",
      "b": "capa com rosto de personagem",
      "metrica": "alcance_d3",
      "min_posts_por_lado": 5,
      "criterio": "vence quem tiver ≥ 20% a mais e ganhar ≥ 70% dos pares",
      "inicio": "2026-10-12",
      "fim_max": "2026-10-25",
      "status": "rodando",
      "resultado": null,
      "decisao": null
    }
  ]
}
```

### 2.9 Saída — `decisoes_<AAAA>-W<nn>.md`

Texto simples, uma linha por decisão, **sempre com a regra e o número**. Exemplo:

```
# Decisões — plano 2026-W42 (gerado 10/10 10h42 pelo app; revisado pelo Claude 11h05)
- R03 · Filmes · Instagram · carrossel_lista: 4 → 1/semana (razão 0,38 pela 2ª semana; n=4). Volta testada em 2 semanas.
- R02 · GTA · TikTok · reel_noticia: 10 → 14/semana (razão 1,62; n=10). Limitado pelo teto de 4/dia.
- R06 · Filmes · Instagram: faixa 12-14 → 19-21 em 2 de 4 posts (0,61 da melhor faixa; n=4 e 6).
- R11 · GTA · TikTok: fator M = 1,5 (monetização estimada em 27 dias).
- Sem mudança: Receitas (dado insuficiente em 3 formatos — R13).
- Claude: incluída a vaga extra do feriado de 12/10 em Destinos (evento do calendário).
```

### 2.10 Saída — `matriz_<AAAA>-W<nn>.json`

A "fotografia" da matriz canal × rede × formato × faixa com a nota de prioridade (bloco D) de cada célula. Serve para o painel e para explicar o plano. Exemplo de 1 célula:

```json
{ "canal": "gta", "rede": "instagram", "formato": "reel_contagem", "faixa": "17-19",
  "A": 1.30, "S": 1.20, "E": 1.18, "R": 1.16, "M": 1.0, "F": 1.2, "C": 1.5,
  "P": 0.98, "n": 7, "status": "ativo" }
```

`status`: `ativo`, `reforcado`, `cortado`, `pausado`, `aposentado`, `teste`, `dado_insuficiente`.

---

