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
$app     = "G:\Meu Drive\Hypado\06 Projeto\app\hp_studio_nuvem"
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
        "max_posts_dia_por_rede": { "instagram": 4, "tiktok": 4, "youtube": 4, "facebook": 3, "threads": 6 },
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
2. Para cada vaga, acha o **assunto** que encaixa em `canal` + `formato` + `pilar` + `publico` e cria o pedido em `01_pedidos` **copiando** para o `pedido.json`:
   - `slot_id` → `slot_id`; `formato` → `formato_estrategia`; `teste_ab` → `teste_ab`;
   - `redes[].rede` → `redes` (a lista de nomes, como o `pedido.json` já usa hoje);
   - `redes[].hora` → `horarios` (`{"instagram": "<data>T18:30:00-03:00", ...}`) e o **menor** horário → `publicar_em`;
   - `story` → `story`; `duracao_alvo_s` → `duracao_alvo_s`;
   - `narracao` → os campos de áudio e Toque HP do pedido (`nenhuma` → sem voz; `toque_hp_texto` → Toque HP em texto; `*_piper` → voz Piper permitida, só nos 4 canais liberados).
   O Publicador (manual 10, seção 2.3) lê `horarios`, `story` e os campos de rastreio (`slot_id`, `formato_estrategia`, `teste_ab`) daí.
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

## 3. Passo a passo (para leigo)

> O ciclo tem 3 ritmos: **semanal** (sábado: plano da semana seguinte), **diário** (7h: ajuste do dia; e na hora, para P0) e **mensal** (1º sábado do mês: revisão de pesos, catálogo, metas e capacidade).
>
> O **app** (módulo `estrategista`, **a criar**) faz as contas, aplica as regras e monta o JSON. O **Claude** revisa em até **20 minutos**, decide o que as regras não cobrem (seção 7) e assina. Os comandos abaixo têm nomes **previstos**; os definitivos ficam no `LEIA.md` do módulo (`& $py -m estrategista --help`).

### Bloco A — Sábado de manhã: receber os números

**Passo 1.** Às **7h** de sábado, confira se o Analista entregou o arquivo da semana seguinte:

```powershell
$semana = "2026-W42"   # a semana do PLANO (a próxima)
Test-Path "H:\HypadoLocal\metricas\relatorios\para_estrategista_$semana.json"
```

Tem que responder `True`. Se `False` às 8h: ticket P1 na área `estrategia` (passo 90) e use o plano da semana anterior como base (passo 9).

**Passo 2.** Leia o relatório semanal (`semanal_<AAAA>-W<nn>.md`, o da semana que acabou) — **só** as seções 1, 2, 8 e 10 (resumo, crescimento, monetização e regras disparadas). ≤ **5 minutos**.

**Passo 3.** Veja o resumo de qualidade dos dados:

```powershell
$pe = Get-Content "H:\HypadoLocal\metricas\relatorios\para_estrategista_$semana.json" -Raw -Encoding UTF8 | ConvertFrom-Json
$pe.qualidade_dados
$pe.regras_disparadas | Format-Table regra, canal, rede, formato, numeros -Wrap
```

**Passo 4.** Abra o plano da semana que está rodando (é a base para "antes → depois"):

```powershell
$anterior = "2026-W41"
Test-Path "$est\planos\plano_semana_$anterior.json"
```

**Passo 5.** Confira a capacidade (`$est\config\capacidade.json`). Se o plantão avisou (por ticket) que a esteira está mais lenta ou mais rápida, o número já deve estar atualizado; se não estiver, **não** invente: use o que está lá e anote em `decisoes`.

**Passo 6.** Confira o calendário de eventos das **próximas 3 semanas** (`$est\calendario_eventos.json`): jogos, estreias, feriados, marcos do GTA 6. Evento sem `fonte` oficial **não** conta.

### Bloco B — Os dados são confiáveis? (antes de qualquer decisão)

**Passo 7.** **Regra R14 — semana anômala.** Se a cobertura foi **< 90%**, ou algum canal teve `queda_geral` (todas as redes −30% no mesmo período), ou alguma conta ficou restrita/sem token: **nesse canal, nesta semana, não se corta nada** (só reforço é permitido). Anote em `decisoes`.

**Passo 8.** **Regra R13 — dado insuficiente.** Todo grupo (formato, faixa, rede) com **menos de 4 posts** na janela fica `dado_insuficiente`: **mantém a quantidade** da semana anterior e, se fizer sentido, entra como candidato a **teste** (bloco F).

**Passo 9.** **Sem arquivo do Analista:** o plano da semana seguinte é **cópia** do plano atual com datas trocadas e **nenhuma** mudança de quantidade. Isso é registrado como `"regra": "SEM_DADOS"`.

**Passo 10.** **P0 fora da conta:** as regras usam os números **sem P0** (o Analista já entrega assim: `base.sem_p0 = true`). Um gol que viralizou não prova que o formato de notícia do Futebol é bom.

### Bloco C — A matriz canal × rede × formato × horário (e a cadência inicial)

**Passo 11.** **O que é a matriz.** É uma grande tabela em que cada **célula** é uma combinação: **canal** (6) × **rede** (até 6) × **formato** (do catálogo) × **faixa de horário** (8 faixas: `06-09`, `09-12`, `12-14`, `14-17`, `17-19`, `19-21`, `21-23`, `23-06`). Cada célula tem números (alcance, TE, retenção, seguidores por mil) e uma **nota de prioridade P** (bloco D). O plano é, no fundo, "escolher as melhores células e dizer quantos posts cada uma recebe".

**Passo 12.** **Estados de cada célula:** `ativo` (recebe posts normalmente), `reforcado` (R02), `cortado` (R01), `pausado` (R03), `aposentado` (R04), `teste` (bloco F), `dado_insuficiente` (R13).

**Passo 13.** **Cadência inicial (semanas 1 e 2 — hipótese).** Enquanto não houver 2 semanas de números medidos na esteira, o plano parte desta tabela (quantidade **por dia**, horário de referência por rede; FB e YT seguem o processo atual até a etapa 4 ser ligada). A partir da 3ª semana, **os números mandam** e esta tabela só serve de ponto de partida para formatos novos.

**GTA 6 | HP** (fase `aquecimento`; ver bloco H para as outras fases)

| Formato | Por dia | Instagram | TikTok | YouTube | Facebook | Threads | Público |
|---|---|---|---|---|---|---|---|
| `reel_contagem` | 1 | 18:30 | 19:00 | 19:30 | 20:00 | 18:35 (vídeo) | gamers 16–30 |
| `reel_noticia` (só notícia **oficial**; a 2ª do dia entra pela reserva P0) | 1 | 12:30 | 13:00 | 13:30 | 14:00 | — | gamers 16–30 |
| `reel_criador` (corte com crédito + Toque HP em texto) | 1 | 21:30 | 21:00 | 22:00 | — | — | gamers 16–30 |
| `reel_curiosidade` ou `carrossel_lista` (alternando) | 1 | 15:30 (reel) / 10:00 (carrossel) | 16:00 (reel) | 16:30 (reel) | 10:30 (carrossel) | — | fãs da série GTA |
| `threads_texto` | 3 | — | — | — | — | 09:00 · 15:00 · 22:30 | comunidade |
| `story_contagem` | 1 | 09:00 (story) | — | — | — | — | seguidores |
| `story_enquete` | 1 | **16:00** (story, destaque Enquetes) | — | — | — | — | seguidores |

**Futebol | HP** (o `07 Canais\Futebol\PLANO_CRESCIMENTO.md` **(existe)** manda enquanto não houver 2 semanas de números da esteira; esta tabela só vale onde ele não disser nada)

| Formato | Dia sem jogo | Dia com jogo | Instagram | TikTok | YouTube | Facebook | Threads |
|---|---|---|---|---|---|---|---|
| `reel_futebol_noticia` (fotos oficiais, **sem voz**) | 1 | 1 | 12:00 | 12:30 | 13:00 | 13:30 | — |
| `reel_debate` | 1 | 0 | 19:30 | 20:00 | 20:30 | 21:00 | — |
| `reel_estatistica` ou `carrossel_rodada` (alternando) | 1 | 0 | 10:00 | 10:30 | 11:00 | 10:30 | — |
| `reel_gol` (vídeo **oficial** do clube/CBF/liga, **áudio original**) | 0 | **reserva P0: até 3** | na hora | +15 min | +30 min | +30 min | — |
| `reel_resultado` / `reel_tabela` | 0 | 1 (logo depois do jogo) + 1 (`reel_tabela`, 8:00 do dia seguinte) | na hora | +15 min | — | +30 min | — |
| `threads_texto` (placar e debate) | 2 | 4 a 6 (durante o jogo) | — | — | — | — | ao vivo |
| `story_enquete` (palpite) | 3 por semana | no dia do jogo, 16:00 | 16:00 | — | — | — | — |

**Filmes e Séries | HP**

| Formato | Por dia | Instagram | TikTok | YouTube | Facebook | Threads |
|---|---|---|---|---|---|---|
| `reel_onde_assistir` | 1 (sexta: 2) | 19:00 | 19:30 | 20:00 | 20:30 | — |
| `reel_trailer_comentado` (**nunca trailer puro**) | 1 | 21:00 | 21:30 | 22:00 | — | — |
| `reel_curiosidade` | 1 | 12:30 | 13:00 | 13:30 | 14:00 | — |
| `carrossel_lista` (nunca na sexta, para não passar do teto) | 3 por semana | 10:00 | — | — | 10:30 | — |
| `threads_texto` | 2 | — | — | — | — | 11:00 · 22:30 |
| `story_enquete` | 3 por semana | 16:00 | — | — | — | — |

**Receitas | HP**

| Formato | Por dia | Instagram | TikTok | YouTube | Facebook | Pinterest | Threads |
|---|---|---|---|---|---|---|---|
| `reel_receita` | 2 | 10:00 · 17:00 | 10:30 · 17:30 | 11:00 · 18:00 | 11:30 · 18:00 | 1 pin por reel (12:00 · 19:00) | — |
| `carrossel_receita` | 1 | 12:30 | — | — | 13:00 | 13:00 | — |
| `pin_estatico` | 2 | — | — | — | — | 08:00 · 21:00 | — |
| `reel_quanto_custa` ("Valores aproximados…") | 2 por semana | 19:30 | 20:00 | 20:30 | 20:30 | — | — |
| `threads_texto` | 2 | — | — | — | — | — | 09:00 · 16:00 |
| `story_enquete` | 3 por semana | 16:00 | — | — | — | — | — |

**Carros | HP**

| Formato | Por dia | Instagram | TikTok | YouTube | Facebook | Pinterest | Threads |
|---|---|---|---|---|---|---|---|
| `reel_lancamento` | 1 | 12:30 | 13:00 | 13:30 | 14:00 | — | — |
| `reel_comparativo` ("Valores aproximados…") | 1 | 19:30 | 20:00 | 20:30 | 21:00 | — | — |
| `carrossel_lista` (ficha, lista) | 3 por semana | 10:00 | — | — | 10:30 | 11:00 | — |
| `pin_estatico` | 2 | — | — | — | — | 08:00 · 21:00 | — |
| `threads_texto` | 2 | — | — | — | — | — | 09:00 · 22:00 |

**Destinos | HP**

| Formato | Por dia | Instagram | TikTok | YouTube | Facebook | Pinterest | Threads |
|---|---|---|---|---|---|---|---|
| `reel_roteiro` | 1 | 20:30 | 21:00 | 21:30 | 21:30 | 1 pin (22:00) | — |
| `reel_quanto_custa` ("Valores aproximados…") | 1 | 12:30 | 13:00 | 13:30 | 14:00 | — | — |
| `reel_dica` | 1 a cada 2 dias | 17:30 | 18:00 | 18:30 | — | — | — |
| `carrossel_lista` (roteiro em lâminas) | 3 por semana | 10:00 | — | — | 10:30 | 11:00 | — |
| `pin_estatico` | 3 | — | — | — | — | 08:00 · 15:00 · 23:00 | — |
| `threads_texto` | 2 | — | — | — | — | — | 09:00 · 19:00 |

> Por que os horários de uma mesma vaga ficam "escadinha" (IG 18:30, TikTok 19:00, YouTube 19:30)? (1) O Publicador não publica tudo no mesmo minuto; (2) o story clicável do Instagram sai antes de o vídeo "concorrer" consigo mesmo nas outras redes; (3) o Analista consegue ver qual rede responde primeiro. O intervalo é padrão, e a regra R06 muda o horário de cada rede separadamente quando os números mandarem.

**Passo 14.** **Tetos e pisos da casa** (regra R12; podem ser mudados na revisão mensal, nunca no meio da semana):

| Rede | Teto por conta por dia (sem contar P0) | Piso (se a rede tem meta de monetização viva) |
|---|---|---|
| Instagram (feed: reels + carrossel + foto) | 4 | 1 |
| Instagram stories clicáveis | 4 | — |
| TikTok | 4 | 1 |
| YouTube Shorts | 4 | 1 |
| Facebook | 3 | 1 (quando ativo) |
| Threads | 6 | 1 |
| Pinterest | 5 | 1 |

Intervalo mínimo entre dois posts do **feed** da mesma conta na mesma rede: **60 minutos** (P0 não respeita). Limites oficiais das redes (publicação pela API, spam): **conferir na página oficial**; o teto da casa é sempre menor.

**Passo 15.** **Capacidade por canal.** Todo canal tem **piso de 2 itens por dia** (`piso_itens_dia_por_canal`). O resto da capacidade (limitada a **90%** do total, para sobrar folga para P0 e refações do Revisor) é dividido pela **prioridade do canal**:

```
Prioridade do canal (PC) = (eficiência do canal ÷ eficiência média da HP) × M do canal × F do canal
```

- **Eficiência** = seguidores ganhos por item produzido (manual 11, passo 50).
- **M do canal** = o maior fator M entre as redes do canal (regra R11).
- **F do canal** = fator de fase/evento (GTA `aquecimento` 1,2; `reta_final` 1,5; `lancamento` 2,0; Futebol em semana de rodada decisiva 1,2; os outros 1,0).

**Capacidade é teto, não meta:** se o canal recebe 7 vagas mas as regras só justificam 5, ele usa 5 e a sobra fica como folga. **Não se produz para "encher" a capacidade** — é exatamente isso que faz a HP "produzir muito onde não precisa".

**Passo 16.** **Exemplo resolvido (números inventados).** Capacidade de vídeo: 26/dia → 90% = **23**. Pisos: 6 canais × 2 = **12**. Sobram **11**.

| Canal | Eficiência | ÷ média (36,88) | M | F | PC | Parte das 11 | Teto do dia |
|---|---|---|---|---|---|---|---|
| GTA | 73,8 | 2,00 | 1,5 | 1,2 | 3,60 | 3,60 ÷ 7,60 × 11 = 5,2 → **5** | 2 + 5 = **7** |
| Futebol | 45,0 | 1,22 | 1,0 | 1,0 | 1,22 | 1,8 → **2** | **4** |
| Filmes | 25,0 | 0,68 | 1,0 | 1,0 | 0,68 | 1,0 → **1** | **3** |
| Receitas | 19,5 | 0,53 | 1,0 | 1,0 | 0,53 | 0,8 → **1** | **3** |
| Carros | 30,0 | 0,81 | 1,0 | 1,0 | 0,81 | 1,2 → **1** | **3** |
| Destinos | 28,0 | 0,76 | 1,0 | 1,0 | 0,76 | 1,1 → **1** | **3** |
| **Soma** | | | | | **7,60** | **11** | **23** |

(Média da eficiência = (73,8 + 45 + 25 + 19,5 + 30 + 28) ÷ 6 = 221,3 ÷ 6 = 36,88. Arredondamento: pelo maior resto, até fechar 11.) Nenhum canal pode ficar com mais de **40%** da capacidade total.

### Bloco D — A fórmula de prioridade (a nota P de cada célula)

**Passo 17.** **A fórmula:**

```
P = (0,35 × A  +  0,30 × S  +  0,20 × E  +  0,15 × R)  ×  M  ×  F  ÷  C
```

| Letra | Nome | Conta | Limites |
|---|---|---|---|
| **A** | Alcance relativo | alcance médio da célula ÷ alcance médio do canal na mesma rede (é a "razão do formato" do manual 11, passo 49) | entre 0 e 3 |
| **S** | Seguidores relativos | seguidores por mil views da célula ÷ o mesmo número do canal na rede | entre 0 e 3 |
| **E** | Engajamento relativo | TE da célula ÷ TE do canal na rede (TE_v nas redes sem alcance) | entre 0 e 3 |
| **R** | Retenção relativa | retenção da célula ÷ retenção do canal na rede; **estático = 1** | entre 0 e 3 |
| **M** | Fator monetização (R11) | 1,5 se a rede bate a meta em ≤ 30 dias; 1,25 se em 31–90 dias **ou** se falta ≤ +50% de ritmo; 1,0 nos outros casos | 1,0 a 1,5 |
| **F** | Fator de fase/evento | 1,0 normal; GTA contagem: 1,2 (`aquecimento`), 1,5 (`reta_final`), 2,0 (`lancamento`); Futebol em dia de jogo para formatos de jogo: 1,3; data do calendário ligada ao formato: 1,2 | 1,0 a 2,0 |
| **C** | Custo de produção | `custo` do catálogo (0,5 a 3,0); **publicar o mesmo item em mais uma rede custa 0** | 0,5 a 3,0 |

Por que esses pesos: **A (35%)** é o que o algoritmo mais recompensa; **S (30%)** é o que leva à monetização (seguidor é requisito em quase todo programa); **E (20%)** e **R (15%)** são sinais de qualidade que puxam alcance no futuro. Os pesos ficam em `$est\config\pesos.json` **(a criar)** e só mudam na revisão mensal (bloco K), com teste.

**Passo 18.** **Por que limitar entre 0 e 3:** um post viral faz a razão ir a 10 e "sequestrar" o plano inteiro. Com o limite, o viral conta como "muito bom" (3), não como "infinitamente bom".

**Passo 19.** **Exemplo resolvido — GTA no Instagram (números inventados):**

| Célula (formato) | A | S | E | R | Soma ponderada | M | F | C | **P** |
|---|---|---|---|---|---|---|---|---|---|
| `reel_contagem` | 1,30 | 1,20 | 1,18 | 1,16 | 0,455 + 0,360 + 0,236 + 0,174 = **1,225** | 1,0 | 1,2 | 1,5 | 1,225 × 1,0 × 1,2 ÷ 1,5 = **0,98** |
| `reel_noticia` | 1,12 | 1,05 | 1,05 | 1,04 | 0,392 + 0,315 + 0,210 + 0,156 = **1,073** | 1,0 | 1,0 | 2,0 | 1,073 ÷ 2,0 = **0,54** |
| `carrossel_lista` | 0,39 | 0,45 | 0,82 | 1 (estático) | 0,137 + 0,135 + 0,164 + 0,150 = **0,586** | 1,0 | 1,0 | 2,0 | 0,586 ÷ 2,0 = **0,29** |

Leitura: a contagem regressiva é a célula mais "rentável" do GTA no Instagram; a notícia vem depois; o carrossel de lista está rendendo pouco **e** custa caro.

**Passo 20.** **Para que serve o P** (ele **não** manda sozinho; as regras da seção 4.2 vêm antes):
1. **Dividir o que sobrou** da capacidade do canal depois das regras e dos formatos fixos: proporcional ao P.
2. **Desempate e corte:** se o plano passar da capacidade, corta primeiro a célula de **menor P** (nunca abaixo do piso, nunca formato protegido pela R18).
3. **Escolher as redes** de cada item quando o teto da rede aperta: a rede em que a célula tem maior P fica com o post.
4. **Ordenar os horários** (a faixa de maior P da rede recebe o post mais importante do dia).

**Passo 21.** **Célula sem dado** (formato novo ou `dado_insuficiente`): usa **A = S = E = R = 1** (neutro) até ter 4 posts.

**Passo 22.** O app grava todas as células com suas letras e o P em `matriz_<AAAA>-W<nn>.json` (seção 2.10).

**Passo 23.** Comando previsto (**a criar**):

```powershell
& $py -m estrategista matriz --semana 2026-W42
```

**Passo 24.** O Claude confere 3 células por canal (as de maior e menor P e uma do meio) refazendo a conta à mão com a tabela do passo 19. Diferença > 0,01 → ticket (fórmula errada no app).

### Bloco E — Aplicar as regras de decisão

**Passo 25.** As regras estão na **seção 4.2** (R01 a R20). O app aplica **nesta ordem** (a primeira que "segura" uma célula impede as seguintes de mexer nela):

```
R20 (regras invioláveis) → R14 (semana anômala) → R13 (dado insuficiente)
→ R18 (fase do GTA) → R19 (reservas P0) → R11 (monetização)
→ R03/R04 (pausa e aposentadoria) → R01 (corte) → R02 (reforço)
→ R05 (rede de baixo retorno) → R08/R09/R10 (retenção, útil, espalha)
→ R06 (horário) → R07 (exploração de horário)
→ R16 (reaproveitar) → R17 (eficiência do canal) → R12 (tetos e pisos)
→ R15 (no máximo 3 mudanças grandes por canal)
```

**Passo 26.** **Ponto de partida** de cada célula: a quantidade **da semana anterior** (na 1ª semana, a cadência inicial do passo 13).

**Passo 27.** Cada regra que dispara vira uma linha em `decisoes` com: regra, canal, rede, formato, **antes**, **depois**, **números** que dispararam.

**Passo 28.** **Quantidade de itens de um formato** = o **maior** número pedido entre as redes em que ele sai. Ex.: `reel_noticia` do GTA: Instagram pede 10 na semana, TikTok pede 14 (R02) → produzir **14** itens; o Instagram recebe 10 deles (os de melhor assunto, escolhidos pelo Pauteiro), o TikTok recebe os 14.

**Passo 29.** **Regra dos 3 (R15):** se mais de 3 mudanças **grandes** (R01, R02, R03, R04, R05 ou R06) dispararem no mesmo canal, ficam as **3 de maior impacto** — impacto = |razão − 1| × n. As outras esperam a semana seguinte (e aparecem em `decisoes` como "adiada por R15"). Motivo: se tudo mudar de uma vez, ninguém sabe o que causou a melhora ou a piora.

**Passo 30.** Compare as regras que o app disparou com as `regras_disparadas` do Analista (passo 3). **Têm que ser as mesmas** (o Estrategista pode adiar por R15 ou segurar por R14/R13, mas nunca "não ver" uma regra). Diferença sem explicação → ticket.

**Passo 31.** Comando previsto (**a criar**):

```powershell
& $py -m estrategista regras --semana 2026-W42 --mostrar
```

Mostra, por canal, cada regra que disparou, antes → depois e os números.

**Passo 32.** O Claude lê a lista (≤ **10 minutos**) e só interfere nos casos da seção 7 (ex.: um evento do calendário que os números ainda não conhecem). Toda interferência vai para `decisoes` com o motivo, marcada `"por": "claude"`.

### Bloco F — Testes A/B (aprender sem arriscar o canal)

**Passo 33.** **Quando abrir um teste:** (a) quando dois caminhos estão em **empate técnico** (diferença < 15%); (b) quando um grupo está em `dado_insuficiente` e vale a pena descobrir; (c) quando o Claude tem uma ideia nova (capa, gancho, duração); (d) para dar uma última chance a um formato pausado (R03). **Limites:** no máximo **20%** das vagas de cada canal na semana; no máximo **2 testes ao mesmo tempo por canal**; no máximo **1 teste por rede e formato**.

**Passo 34.** **Uma variável só.** Muda **uma** coisa entre A e B; o resto fica igual. Variáveis aceitas: `capa`, `gancho` (os 2 primeiros segundos), `duracao`, `horario`, `legenda` (curta × longa), `hashtags` (3 × 6), `laminas` (carrossel 5 × 8), `musica` (sempre livre de direitos), `toque_hp` (onde o manual 06 permitir variar).

**Passo 35.** **Escreva a hipótese e a métrica antes de começar** (depois que o resultado sai, é tentador escolher a métrica que "deu certo"):

| Pergunta | Métrica principal |
|---|---|
| "Isso faz mais gente ver?" (capa, gancho, horário, hashtags) | `alcance_d3` (ou `views_d3` nas redes sem alcance) |
| "Isso faz mais gente seguir?" | `seg_por_mil` |
| "Isso segura mais a pessoa?" (duração, gancho) | `retencao_pct` |
| "Isso é mais útil?" (lâminas, legenda longa) | `salvamentos_por_mil` |

**Passo 36.** **Desenho:** A e B em **pares** — mesmo dia (ou dias vizinhos), **mesma faixa de horário** (alternando quem sai primeiro), assuntos de peso parecido. **Mínimo de 5 posts por lado**; **no máximo 2 semanas**. Se em 2 semanas não juntar 5 de cada lado, o teste é **cancelado** (e anotado).

**Passo 37.** Registre o teste em `testes_ab.json` (seção 2.8) com `status: "rodando"` e marque as vagas no plano com `teste_ab: {"id": ..., "variante": "A" | "B", "o_que_muda": ...}`. O Pauteiro e o Redator/Designer/Editor leem `o_que_muda` e produzem a variante certa; o Publicador copia o campo para o `publicado.json`; o Analista mede.

**Passo 38.** **Leitura do resultado** (o Analista calcula, manual 11, passo 73): vence o lado com **≥ 20% a mais** na métrica principal **e** que ganhou **≥ 70% dos pares**. Qualquer outra coisa é **empate** — e no empate fica a opção **mais barata** de produzir.

**Passo 39.** **Aplicar:** o vencedor vira **padrão** daquele canal e formato (anotado em `observacoes` das vagas e no `catalogo_formatos.json`, campo `padroes`); a decisão entra em `decisoes` com os números. **Reteste** do mesmo assunto só depois de **8 semanas** (as redes mudam o algoritmo).

**Passo 40.** **Fila de testes sugerida para as primeiras 8 semanas** (o Claude pode trocar a ordem conforme o que os números mostrarem):

| # | Canal | Teste | Métrica |
|---|---|---|---|
| 1 | GTA | Capa com número grande × capa com rosto de personagem | alcance_d3 |
| 2 | Todos (1 canal por semana) | Gancho com pergunta × gancho com afirmação forte | retencao_pct |
| 3 | Receitas | Reel de 20–30 s × 40–60 s | seg_por_mil |
| 4 | Filmes | 12h30 × 13h30 | alcance_d3 |
| 5 | Carros | Carrossel de 5 × 8 lâminas | salvamentos_por_mil |
| 6 | Receitas | Legenda curta × legenda com a receita inteira | salvamentos_por_mil |
| 7 | Destinos | TikTok de 30 s × acima de 60 s (preparando a monetização do TikTok, se disponível no Brasil) | seg_por_mil |
| 8 | Futebol | `reel_debate` com 3 recortes × com 2 recortes | retencao_pct |

> Algumas redes oferecem ferramentas próprias de teste (por exemplo, publicar um reel primeiro só para não seguidores). Se existirem e forem acessíveis pela API oficial ou pelo app oficial, podem ser usadas — **conferir na página oficial** antes; nunca por ferramenta não oficial.

### Bloco G — Montar as vagas da semana

**Passo 41.** **Quantidades por canal, rede e formato:** resultado do bloco E (regras) a partir da semana anterior.

**Passo 42.** **Fixos primeiro:** formatos com `fixo_por_dia` (GTA: `reel_contagem` e `story_contagem`) e os `stories_programados` (enquete das 16h do GTA todos os dias; enquetes dos outros canais 3 vezes por semana).

**Passo 43.** **Reservas P0** (regra R19): guardam capacidade **sem** criar vaga. Padrão: GTA 1 item por dia (2 na `reta_final`, 4 no `lancamento`); Futebol 1 por dia sem jogo e 4 em dia de jogo (o `calendario_eventos.json` diz quando tem jogo); outros canais 0. Reserva não usada até **22h30** é liberada (não vira produção atrasada; simplesmente não é usada).

**Passo 44.** **Itens por formato** = maior quantidade entre as redes (passo 28).

**Passo 45.** **Some os itens de cada canal** e compare com o teto do canal (passo 15):
- **Passou do teto:** corte a célula de **menor P** (uma de cada vez) até caber. Nunca corte abaixo do **piso** (2 itens/dia) e nunca corte formato protegido (R18).
- **Ficou abaixo:** **não** complete. A sobra fica como folga (capacidade é teto, não meta). Exceção: se houver célula com **P ≥ 0,8** e `semanas_acima_150 ≥ 1`, pode receber +1 por dia (conta como mudança grande para a R15).

**Passo 46.** **Distribuir pelos dias:** espalhe cada formato de forma **uniforme** na semana (ex.: 3 carrosséis → seg, qua, sex; se a sexta estourar o teto, qui). Eventos do calendário puxam formatos para o dia certo (Filmes: `reel_onde_assistir` extra na **sexta**; Destinos: roteiro de feriado **10 dias antes** do feriado; Futebol: formatos de jogo no **dia do jogo** e no seguinte).

**Passo 47.** **Horários de cada rede:**
1. Ordene as faixas da rede pela razão contra a melhor faixa (dados do Analista; na falta, a cadência inicial do passo 13).
2. O item de **maior P** do dia vai para a **melhor faixa**; o 2º, para a 2ª melhor, e assim por diante.
3. Respeite **60 minutos** entre posts do feed da mesma conta na mesma rede.
4. **Nunca** duas vagas do mesmo canal na mesma rede no **mesmo minuto**; e evite as horas "cheias" exatas quando há muitos posts no mesmo horário (use :30, :15 etc., como na tabela do passo 13).
5. **R07:** **10%** das vagas de cada rede vão para uma faixa **pouco testada** (n < 4 nos 14 dias), para descobrir horário bom novo.

**Passo 48.** **Público de cada vaga:** o do canal (1.6), a menos que o formato peça outro (ex.: Futebol, jogo de um clube → torcedores daquele clube; Receitas, `reel_quanto_custa` → quem cozinha com orçamento curto). O campo `publico` é curto: "quem" + "idade", no máximo 40 caracteres.

**Passo 49.** **Narração** de cada vaga (conferência obrigatória):
- `futebol`: **sempre** `nenhuma` (o gol vai com **áudio original**; notícia com música livre baixa, **sem voz**).
- `gta`: `nenhuma` ou `toque_hp_texto` (**sem voz sintética**).
- `filmes`, `receitas`, `carros`, `destinos`: pode ser `toque_hp_voz_piper` ou `dublagem_piper` **só em vídeo próprio**, com a voz Piper pt-BR já instalada (`scripts\dublar.py`). **Nunca clonar voz.**

**Passo 50.** **Stories de cada vaga:** `divulgacao: true` em todo reel e carrossel do Instagram; `clicavel: true` nos **4 itens de maior P** do dia em cada conta (teto de 4 stories clicáveis por dia por conta; 1 story por post, sem rajada); `destaque` conforme o pilar (Notícias, Contagem, Receitas, Roteiros, Enquetes...).

**Passo 51.** **Marcar testes** (bloco F) e preencher `regra_origem` e `nota_prioridade` de cada vaga.

**Passo 52.** Comando previsto (**a criar**) que faz os passos 41 a 51 sozinho:

```powershell
& $py -m estrategista plano --semana 2026-W42 --rascunho
```

Gera `plano_semana_2026-W42.json` com `"rascunho": true` e o `decisoes_2026-W42.md`.

### Bloco H — Calendário, fases do GTA 6 e datas especiais

**Passo 53.** **O foco nº 1 até 19/11/2026 é o lançamento do GTA 6.** Em 30/09/2026 **faltam 50 dias**. O canal passa por 4 fases:

| Fase | Datas | Faltam | Itens de vídeo/dia (fora P0) | Reserva P0/dia | Contagem regressiva | F da contagem | Regras especiais |
|---|---|---|---|---|---|---|---|
| `aquecimento` | 30/09 a 01/11 | 50 a 18 dias | 4 | 1 | Story diário 9h + reel diário 18h30 | 1,2 | R01 **pode** cortar o reel de contagem se ele ficar < 50% por 2 semanas (o story de contagem nunca é cortado) |
| `reta_final` | 02/11 a 18/11 | 17 a 1 dia | 5 | 2 | Reel diário **protegido** (R18) + marcos especiais | 1,5 | Contagem **não** é cortada; enquete e quiz alternam às 16h |
| `lancamento` | 19/11 a 25/11 | "É hoje" e dias 1 a 6 | 6 a 8 | 4 | "É HOJE" no dia 19/11 (horário oficial de liberação: **conferir na página oficial da Rockstar**) | 2,0 | P0 fura tudo; aviso de spoiler na capa quando mostrar história |
| `pos_lancamento` | a partir de 26/11 | — | 4 | 1 | Encerrada | — | Revisão completa da matriz do GTA com 2 semanas de números |

**Passo 54.** **Marcos da contagem** (dias com arte especial do Designer, carrossel "X coisas confirmadas" e story com a figurinha de contagem regressiva do próprio Instagram, se o robô do emulador suportar — **a criar** no `story_post.py`):

| Faltam | Data | Dia |
|---|---|---|
| 45 | 05/10/2026 | segunda |
| 40 | 10/10/2026 | sábado |
| 35 | 15/10/2026 | quinta |
| 30 | 20/10/2026 | terça |
| 25 | 25/10/2026 | domingo |
| 20 | 30/10/2026 | sexta |
| 15 | 04/11/2026 | quarta |
| 10 | 09/11/2026 | segunda |
| 7 | 12/11/2026 | quinta |
| 5 | 14/11/2026 | sábado |
| 3 | 16/11/2026 | segunda |
| 2 | 17/11/2026 | terça |
| 1 | 18/11/2026 | quarta |
| **0 — É HOJE** | **19/11/2026** | **quinta** |

Conta para conferir: "faltam X dias" = 19/11/2026 − data do post (em 30/09, 50; em 12/10, 38; em 01/11, 18).

**Passo 55.** **Story interativo das 16h do GTA** (todo dia, pelo emulador, `story_post.py` **a criar — ticket F**): arte do dia de `lotes\<dia>_estaticos.json` (Designer, `scripts\estaticos.py` **existe**) + figurinha de **enquete** com pergunta de **no máximo ~25 caracteres** e 2 opções curtas; vai para o destaque **Enquetes**. O plano traz `pergunta_sugerida` e `opcoes` em `stories_programados` (o Redator pode trocar por uma melhor do mesmo tamanho). Exemplos que cabem: "Vai jogar no dia 1?" (19), "Jason ou Lucia?" (15), "Jogo físico ou digital?" (23), "Comprar na pré-venda?" (21), "Qual plataforma?" (16). Só assunto **oficial**; nada de vazamento.

**Passo 56.** **Público do GTA por fase:** `aquecimento` → gamers que já acompanham (reter e trazer amigos: enquete, debate); `reta_final` → também quem **ainda não decidiu comprar** (o que já foi confirmado oficialmente, plataformas, data); `lancamento` → quem **está jogando** (dicas iniciais de criadores com crédito, primeiras impressões); `pos_lancamento` → dicas, guias, curiosidades.

**Passo 57.** **Outras datas até o fim de 2026** (todas no `calendario_eventos.json`; conferir na fonte oficial):

| Data | O quê | Canais | O que muda no plano |
|---|---|---|---|
| 12/10 (seg) | Feriado nacional + Dia das Crianças | Destinos, Receitas | Destinos: roteiro de feriado a partir de 02/10; Receitas: receita para crianças |
| 31/10 (sáb) | Halloween | Receitas, Filmes | Receitas temáticas; Filmes: lista de terror |
| 02/11 (seg) | Feriado nacional (Finados) | Destinos | Roteiro de feriado prolongado a partir de 23/10 |
| 15/11 (dom) | Feriado nacional | Destinos | Idem, a partir de 05/11 |
| 19/11 (qui) | **Lançamento do GTA 6** | GTA (e chamadas nos outros canais) | Fase `lancamento`; chamadas cruzadas nos outros perfis (story, sem exagero) |
| 20/11 (sex) | Feriado nacional | Destinos | Roteiro a partir de 10/11 |
| 27/11 (sex) | Black Friday | Carros, Receitas, Destinos | Conteúdo "quanto custa" com "Valores aproximados…"; **sem** publi e **sem** afiliado (manual 13 é FUTURO) |
| Dezembro | Férias, Natal (25/12, sex), Réveillon | Destinos, Receitas, Filmes | Destinos: verão; Receitas: ceia a partir de 05/12; Filmes: listas de fim de ano |
| Rodadas e finais | Brasileirão, Copa do Brasil, Libertadores, Seleção | Futebol | Datas **só** das tabelas oficiais (CBF, Conmebol, ligas) — **conferir**; dia de jogo = reserva P0 de 4 |

**Passo 58.** **Chamadas cruzadas** (divulgação entre os próprios perfis): no máximo **1 story por semana** de um canal chamando outro (ex.: @hp.filmes mostra o post do GTA na semana do lançamento), só quando os públicos combinam. Isso é "publicidade" orgânica da HP; não é publi paga.

**Passo 59.** **Página de links** (`https://sites.google.com/view/hpcanais`): é o destino dos links de bio e dos pins. O Estrategista não mexe na página; só usa nos planos.

**Passo 60.** **Futebol e o `PLANO_CRESCIMENTO.md`**: enquanto o canal não tiver 2 semanas de números da esteira, as quantidades do Futebol vêm do `07 Canais\Futebol\PLANO_CRESCIMENTO.md` **(existe)**. A partir daí, as regras da seção 4.2 valem também para o Futebol, e qualquer conflito com o `PLANO_CRESCIMENTO.md` vira ticket para o Antônio decidir (não se muda o plano de crescimento sozinho).

**Passo 61.** **Montadores do Futebol:** os formatos `reel_gol`, `reel_futebol_noticia`, `reel_debate`, `reel_estatistica`, `reel_resultado` e `reel_tabela` correspondem aos modos do `reel_futebol.py` **(a criar — ticket G)**. Até ele existir, esses formatos são feitos do jeito atual, e a capacidade `itens_reel_futebol` é a do processo atual.

**Passo 62.** Atualize o `calendario_eventos.json` toda semana (sábado) com as datas **oficiais** das 3 semanas seguintes. Comando previsto (**a criar**) para conferir o que vem aí:

```powershell
& $py -m estrategista calendario --proximas 3
```

### Bloco I — Gerar, validar e entregar o plano

**Passo 63.** Gere o rascunho (passo 52) e rode a validação (esquema + as 9 regras de negócio da seção 2.6.6):

```powershell
& $py -m estrategista validar "$est\planos\plano_semana_2026-W42.json"
```

**(a criar)**. Tem que responder `ok`. Qualquer erro: corrigir a causa (quase sempre capacidade, teto ou narração em canal proibido) e gerar de novo. **Nunca** editar o JSON à mão para "passar" na validação.

**Passo 64.** O Claude revisa (≤ **20 minutos** no total de sábado):
1. Lê o `decisoes_2026-W42.md` inteiro.
2. Confere 3 células por canal (passo 24).
3. Confere as datas especiais (bloco H) e as reservas P0.
4. Confere o **objetivo da semana** de cada canal (1 linha, ligada à monetização quando houver meta próxima).
5. Decide os casos da seção 7 e anota em `decisoes` com `"por": "claude"`.

**Passo 65.** Para ver um resumo do rascunho (quantos itens por canal e dia):

```powershell
$pl = Get-Content "$est\planos\plano_semana_2026-W42.json" -Raw -Encoding UTF8 | ConvertFrom-Json
$pl.canais.PSObject.Properties | ForEach-Object {
  $c = $_.Name; $_.Value.slots | Group-Object dia | ForEach-Object { "{0}  {1}  itens={2}" -f $c, $_.Name, $_.Count }
}
```

**Passo 66.** Feche o plano (tira o `rascunho`):

```powershell
& $py -m estrategista plano --semana 2026-W42 --fechar
```

**(a criar)**. O comando valida de novo, grava a versão final e registra no log.

**Passo 67.** **Prazo:** sábado até **12h**. O Pauteiro (manual 02) começa a preparar a segunda-feira no sábado à tarde e no domingo.

**Passo 68.** **Mudança depois de fechado:** só pelo **ajuste diário** (bloco J). O plano fechado **não se reescreve** (senão o Analista não consegue comparar planejado × realizado).

**Passo 69.** O app avisa o painel (`scripts\painel_local.py` **existe**) de que há plano novo, e o painel mostra a semana em forma de grade (canal × dia).

**Passo 70.** **Não** se manda o plano pelo WhatsApp (não é uma das 3 coisas). O Antônio vê pelo painel; mudança grande de estratégia (ex.: parar uma rede inteira) vira **ticket** para ele decidir.

### Bloco J — Ajuste diário (7h) e P0 (na hora)

**Passo 71.** Às **7h**, depois do relatório diário do Analista (6h45), o app lê o `indicadores_<dia>.json` e o plano do dia.

**Passo 72.** **Destaque de ontem** (post com IDR ≥ 2 na marca D+1): cria **1 vaga de continuação** para hoje (mesmo assunto, ângulo novo; regra R16), no melhor horário livre. Se não houver folga, tira a vaga **P2 de menor P** do mesmo canal no dia.

**Passo 73.** **Alerta `queda_geral`** num canal: marca `congelar_cortes: true` (R14) e abre ticket (pode ser problema na conta).

**Passo 74.** **Cumprimento do plano ontem < 90%** (itens presos na esteira): tira **20% das vagas P2** de hoje daquele canal, para a esteira alcançar. Anota em `remover` com o motivo.

**Passo 75.** **P0 durante o dia** (gol, anúncio oficial da Rockstar, notícia bombástica): o Curador (manual 01) marca o pedido como `P0_`; ele **não precisa** de vaga no plano: usa a **reserva P0** do canal. Se a reserva do dia acabou, o app tira a vaga **P2 de menor P** do canal **que ainda não começou a ser produzida** (pasta ainda em `01_pedidos`) e registra no ajuste. Vaga que já está em produção **não** é tirada.

**Passo 76.** **Evento oficial novo** (ex.: a Rockstar marca uma data de anúncio): entra no `calendario_eventos.json` com `fonte`, e o ajuste do dia reforça a reserva P0 daquele dia.

**Passo 77.** **Limite:** no máximo **3 mudanças por canal por dia** no ajuste (P0 não conta).

**Passo 78.** Grave e valide o ajuste:

```powershell
& $py -m estrategista ajuste --dia (Get-Date -Format yyyy-MM-dd)
& $py -m estrategista validar "$est\ajustes\ajuste_$(Get-Date -Format yyyy-MM-dd).json"
```

**(a criar)**. O Pauteiro aplica o ajuste às **7h15**.

**Passo 79.** O Claude lê o ajuste (≤ **3 minutos**). Só interfere se um evento do dia exigir (ex.: jogo adiado — a reserva P0 vai para o dia novo).

**Passo 80.** Nada do ajuste vai para o WhatsApp.

### Bloco K — Revisão mensal (1º sábado do mês)

**Passo 81.** **Pesos da fórmula** (0,35 / 0,30 / 0,20 / 0,15): o app mostra, para o mês, se as células de maior P foram de fato as que mais trouxeram seguidores (correlação simples). Se a ordem errou em mais de **30%** dos canais, o Claude propõe novos pesos **como teste** (2 semanas, metade dos canais) — nunca troca direto.

**Passo 82.** **Catálogo de formatos:** aposentar os que estão `aposentado` há 8 semanas; incluir formatos novos (sempre com `custo`, `voz`, `redes`) como `teste`.

**Passo 83.** **Capacidade real:** comparar a capacidade do `capacidade.json` com o que a esteira realmente entregou nas 4 semanas (itens em `07_postados` por dia + itens em `99_erros`). Diferença > 15% → atualizar (com ticket para o plantão confirmar).

**Passo 84.** **Metas de monetização:** conferir com o Analista que o `metas_monetizacao.json` foi conferido na página oficial no mês (manual 11, passo 60).

**Passo 85.** **Público:** comparar as hipóteses de 1.6 com os dados de público das redes (idade, gênero, cidades, horários on-line). Mudou? Atualizar a tabela 1.6 e os horários de referência.

**Passo 86.** **Tetos e pisos** (passo 14): revisar com base em 4 semanas; mudança de teto só com teste de 2 semanas.

### Bloco L — Quando algo dá errado

**Passo 87.** **Plano não valida** e o prazo de sábado 12h está chegando: entregue o plano da semana anterior com datas trocadas (passo 9) e abra ticket.

**Passo 88.** **Pauteiro devolveu muitas vagas `vazia`** (> 20% num canal): o formato/pilar pode estar sem assunto (ex.: poucas notícias oficiais do GTA naquela semana). Reduza as vagas daquele pilar no ajuste e registre.

**Passo 89.** **Regra disparou "errado"** (o Claude acha que o número não reflete a realidade): **não** desligue a regra. Use R14 (se for problema de dado) ou registre a exceção em `decisoes` com o motivo e abra ticket para revisar a regra na revisão mensal.

**Passo 90.** **Abrir ticket:** `scripts\tickets.py` **(existe)**, área `estrategia` (sintaxe com `& $py "G:\Meu Drive\Hypado\scripts\tickets.py" --help`). Pedido de ajuda **nunca** pelo WhatsApp.

**Passo 91.** **Decisão que muda a empresa** (parar uma rede num canal, abrir um canal, mudar o foco): o Estrategista **propõe** com números num ticket para o **Antônio** decidir. Nunca faz sozinho.

**Passo 92.** Tudo o que for proposta de publicidade paga, publi ou afiliado: **não** entra no plano (manual 13 é **FUTURO**).

---

## 4. Regras que nunca se quebram

### 4.1 Regras invioláveis (valem acima de qualquer número — é a regra R20)

1. **Conteúdo:** nada do Flow Games; nada de vazamento de GTA 6; **sem trailer puro**; futebol **sem imagem de transmissão de TV** (vídeo oficial do clube/CBF/liga pode, com crédito e com o áudio original) e **nunca com narração sintética**; **crédito do criador sempre**; música **só livre de direitos**; valor citado leva **"Valores aproximados…"**.
2. **Voz:** **nunca clonar voz**; voz sintética **só** a Piper pt-BR já instalada (`scripts\dublar.py`) e **só** nos vídeos próprios de Destinos, Receitas, Carros e Filmes.
3. **Segurança:** nunca digitar senha ou código, criar conta, aceitar termos, ler ou imprimir token, contornar CAPTCHA. Só API oficial, app oficial no emulador ou página oficial.
4. **PC:** trabalho pesado 1 por vez e **nunca das 18h às 22h30**. O plano **não** pode exigir renderização nesse horário: vaga com publicação entre 18h e 22h30 tem que estar produzida **antes das 18h** (o Pauteiro e o Editor recebem isso como prazo). Publicar e story não são pesados.
5. **WhatsApp:** só as 3 coisas (resumo do dia anterior, aviso "no ar", resumo de sábado). O plano **não** é mandado pelo WhatsApp.
6. **Afiliados, publi e anúncio pago:** **FUTURO** (manual 13). Não entram no plano.
7. **Nada quebra o que funciona:** o plano do app só substitui o plano feito pelo Claude depois de **7 dias de modo sombra** com paridade comprovada (README e seção 9).
8. **Não mexer** na etapa 4 (Facebook e YouTube), na auditoria da API do YouTube e na redução de arquivos do painel público.

### 4.2 Regras de decisão (sempre aplicadas, na ordem do passo 25)

Termos usados: **razão** = alcance médio do formato ÷ alcance médio do canal na mesma rede, na janela de 7 dias, **sem P0**, medido em D+3 (manual 11, passos 41 e 49). **n** = número de posts do grupo na janela.

| Código | Nome | Quando dispara (tudo com n ≥ 4, sem P0) | O que faz |
|---|---|---|---|
| **R01** | Corte | Razão **< 0,50** na janela de 7 dias | Quantidade do formato **naquela rede** na semana seguinte **× 0,5** (arredonda para baixo; mínimo 1 se o formato for continuar em teste) |
| **R02** | Reforço | Razão **≥ 1,50** na janela de 7 dias | Quantidade **+50%** (arredonda para cima), limitada pelo teto da rede (R12) e pela capacidade do canal |
| **R03** | Pausa | Razão < 0,50 por **2 semanas seguidas** (`semanas_abaixo_50 ≥ 2`) | Formato **pausado 2 semanas** naquela rede; fica **1 post de teste por semana** com uma variação (capa, gancho ou duração) |
| **R04** | Volta ou aposentadoria | Fim da pausa da R03 | Se os testes da pausa tiveram razão **≥ 0,80** → volta com **50%** da quantidade de antes do corte; senão → **aposentado** por 8 semanas |
| **R05** | Rede de baixo retorno | Numa rede, seguidores por mil views do canal **< 30%** da média das outras redes do mesmo canal, por **14 dias**, **e** essa rede **não** tem meta de monetização a ≤ 90 dias | A rede entra em **modo reaproveitamento**: só recebe itens já produzidos para outras redes (custo 0); nenhuma produção exclusiva para ela |
| **R06** | Horário fraco | Faixa com alcance médio **< 70%** da melhor faixa da rede, em 14 dias (n ≥ 4 nas duas) | **Metade** dos posts daquela faixa vai para a melhor faixa (ou a 2ª melhor, se a melhor já estiver cheia pelo intervalo de 60 min) |
| **R07** | Exploração de horário | Sempre | **10%** das vagas de cada rede em faixa pouco testada (n < 4 em 14 dias) |
| **R08** | Retenção | Vídeo com retenção ponderada **< 30%** | Duração-alvo **−20%** e observação "gancho novo nos 2 primeiros segundos" para o Editor e o Narrador (manual 06). Se retenção **≥ 60%** com duração < 30 s → abrir teste de versão **+50%** mais longa |
| **R09** | Conteúdo útil | Salvamentos por mil **≥ 1,5 ×** a média do canal na rede | Manter ou aumentar a versão em **carrossel** e, nos 3 canais com Pinterest, **1 pin** por item desse formato |
| **R10** | Conteúdo que espalha | Compartilhamentos por mil **≥ 1,5 ×** a média do canal na rede | O formato ganha prioridade nas **2 melhores faixas** do dia e story clicável garantido |
| **R11** | Monetização perto | Rede do canal com prazo estimado **≤ 30 dias** → M = 1,5; **31 a 90 dias** ou falta **≤ +50%** de ritmo → M = 1,25; senão M = 1,0 | M entra na fórmula; com M = 1,5, **nenhum corte** de quantidade nessa rede na semana, e ela fica com as melhores faixas. Se o requisito for "vídeo ≥ 60 s" (TikTok, se disponível no Brasil), o plano inclui `reel_longo_60` |
| **R12** | Tetos e pisos | Sempre | Tetos e pisos do passo 14; intervalo de 60 min no feed; piso de 2 itens/dia por canal; nenhum canal > 40% da capacidade |
| **R13** | Dado insuficiente | n < 4 | Não aplica R01 a R10 naquele grupo; mantém a quantidade; candidato a teste |
| **R14** | Semana anômala | Cobertura < 90%, `queda_geral`, conta restrita ou sem token | Naquele canal, **só reforço**; nenhum corte na semana; ticket |
| **R15** | Regra dos 3 | Mais de 3 mudanças grandes (R01–R06) no mesmo canal | Ficam as 3 de maior impacto (|razão − 1| × n); as outras são adiadas 1 semana |
| **R16** | Reaproveitar antes de produzir | Sempre | Todo item sai em **todas** as redes em que o formato tem razão ≥ 0,80 (ou sem dado) antes de se criar item exclusivo; post com **IDR ≥ 2** gera **continuação** (ajuste diário) e pode ter **nova versão** (capa/gancho novos) em outra rede ou depois de 14 dias |
| **R17** | Eficiência do canal | Canal com eficiência **< 40%** da média da HP por **2 semanas** | Itens do canal **−25%** (nunca abaixo do piso); a capacidade liberada fica como folga ou vai para canal com **M ≥ 1,25** |
| **R18** | Fase do GTA 6 | Sempre no canal `gta` | Cadência e fatores do passo 53; na `reta_final` e no `lancamento`, a contagem regressiva é **protegida** (R01/R03 não se aplicam a ela) |
| **R19** | Reservas P0 | Sempre | Reservas do passo 43 e do calendário; reserva não usada é liberada às 22h30 |
| **R20** | Invioláveis | Sempre, antes de tudo | Seção 4.1: nenhum número justifica quebrar regra de conteúdo, voz, segurança, PC ou WhatsApp |

**Exemplos (números inventados):**
- R01: `carrossel_lista` do GTA no Instagram com razão 0,39 e n = 5 (1ª semana) → de 4 para **2** na semana seguinte.
- R02: `reel_noticia` do GTA no TikTok com razão 1,62 e n = 10 → de 10 para **15**, mas o teto de 4 por dia do TikTok (com contagem e criador já ocupando 2 por dia) deixa **14** → **14**.
- R03: `carrossel_lista` do Filmes no Instagram com razão 0,38 pela 2ª semana → **pausa** de 2 semanas com **1** carrossel de teste por semana.
- R06: faixa 12–14 do Filmes no Instagram com 7.300 contra 11.900 da melhor (0,61 < 0,70) → 2 dos 4 posts dessa faixa vão para 19–21 (ou 21–23, se 19–21 estiver cheia).
- R11: TikTok do GTA com prazo de 27 dias → M = 1,5 → nenhum corte no TikTok do GTA na semana.

---

## 5. Critérios de qualidade com nota

Nota de 0 a 10 por critério, **por plano semanal**; a nota do plano é a média. Qualquer **0** impede o plano de ser entregue.

| Critério | Nota 10 | Nota 7 | Nota 5 | Nota 0 |
|---|---|---|---|---|
| **Baseado em números** | 100% das mudanças com regra e número em `decisoes` | 1 mudança sem número, explicada pelo Claude | 2 ou mais sem número | Plano mudado "no achismo" |
| **Validação** | Esquema e as 9 regras de negócio ok de primeira | Ok depois de 1 correção de causa | Ok depois de 2 ou mais | Plano entregue sem validar ou editado à mão |
| **Capacidade** | ≤ 90% da capacidade em todos os dias | Até 95% em 1 dia | Até 100% em algum dia | Acima da capacidade |
| **Invioláveis** | Nenhuma vaga com narração proibida, Pinterest fora dos 3 canais ou formato fora do catálogo | — | — | Qualquer violação |
| **Monetização** | Todo canal com meta ≤ 90 dias tem `objetivo_semana` ligado a ela e M aplicado | 1 canal sem objetivo ligado | 2 canais | Meta próxima ignorada |
| **Testes** | ≤ 20% das vagas, 1 variável, hipótese e métrica escritas antes | Teste sem hipótese escrita | Teste com 2 variáveis | > 20% das vagas ou teste que quebra regra |
| **Prazo** | Plano fechado sábado até 12h; ajuste diário até 7h10 | Plano até 18h de sábado | Plano no domingo | Segunda sem plano (e sem cópia da semana anterior) |
| **Resultado (4 semanas)** | Eficiência da HP e prazo de monetização melhorando nas 4 | Melhorando em 3 | Em 2 | Piorando nas 4 sem ajuste de regra |
| **Cumprimento** | ≥ 95% das vagas publicadas | 90% a 94,9% | 80% a 89,9% | < 80% |

Classificação: **≥ 9 Excelente**; **7 a 8,9 Bom**; **5 a 6,9 Médio** (revisar o processo no sábado seguinte); **< 5 Razoável** (volta a ser feito pelo Claude, com o app em sombra, até 2 semanas seguidas ≥ 7).

---

## 6. Erros comuns e o que fazer

| # | Erro | Por que acontece | O que fazer |
|---|---|---|---|
| 1 | "Encher" a capacidade com posts fracos | Achar que mais post = mais crescimento | Capacidade é teto, não meta (passo 15); vaga vazia é melhor que post ruim |
| 2 | Cortar formato por causa de uma semana ruim geral | Queda da conta toda (problema técnico, restrição) | R14: sem cortes na semana anômala |
| 3 | Decidir com 2 ou 3 posts | Pressa | R13: mínimo 4 |
| 4 | Viral "sequestra" o plano | Média sensível a extremo | Limite 0–3 nas letras (passo 18); regras sem P0 |
| 5 | Mudar tudo de uma vez | Muitas regras disparando | R15: no máximo 3 mudanças grandes por canal |
| 6 | Horário igual para todas as redes | Copiar e colar | Passo 47: cada rede tem as suas faixas |
| 7 | Narração sintética no Futebol ou no GTA | Copiar vaga de outro canal | Validação (2.6.6, regra 1) bloqueia; corrigir a causa |
| 8 | Vaga de publicação às 19h exigindo render às 18h30 | Esquecer a janela proibida | Regra 4.1.4: produzir antes das 18h |
| 9 | Plano sem reserva P0 no dia de jogo | Calendário desatualizado | Passo 62 toda semana; dia de jogo = reserva 4 |
| 10 | Teste A/B nunca termina | Poucas vagas por lado | Passo 36: cancelar com 2 semanas e anotar |
| 11 | Plano editado à mão depois de fechado | "Só uma mudancinha" | Passo 68: mudança só pelo ajuste diário |
| 12 | Contagem regressiva com número errado | Conta de datas | Passo 54: 19/11/2026 − data; a tabela de marcos é a referência |
| 13 | Rede fraca recebendo produção exclusiva | Não aplicar R05 | Modo reaproveitamento |
| 14 | Analista e Estrategista com regras diferentes disparadas | Versões diferentes das fórmulas | Passo 30: ticket; alinhar `versao_esquema` |
| 15 | Canal "esquecido" (sem vaga num dia) | Corte abaixo do piso | R12: piso de 2 itens por dia |

---

## 7. O que o app faz sozinho x o que o Claude decide

| Tarefa | App sozinho | Claude | Observação |
|---|---|---|---|
| Ler números, checar qualidade dos dados (R13, R14) | 100% | 0% | — |
| Montar a matriz e calcular P | 100% | 0% (confere 3 células por canal) | — |
| Aplicar R01 a R19 | 100% | 0% | O Claude só adia/segura com motivo escrito |
| Dividir capacidade, distribuir dias e horários, stories | 95% | 5% | Claude ajusta quando o calendário tem algo que os números não conhecem |
| Calendário de eventos | 30% (lembra datas fixas) | 70% (busca datas oficiais de jogos, estreias, anúncios) | Só fonte oficial |
| Fases do GTA 6 e contagem | 100% | 0% | Datas fixas |
| Perguntas das enquetes (sugestão) | 60% (banco de perguntas) | 40% | O Redator pode trocar |
| Testes A/B: escolher o que testar e escrever a hipótese | 20% (fila sugerida) | 80% | É onde entra a criatividade |
| Testes A/B: medir e declarar vencedor | 100% | 0% | Critério fixo |
| Objetivo da semana de cada canal (1 linha) | 70% (a partir das metas) | 30% | — |
| Revisão mensal (pesos, catálogo, público, tetos) | 40% (mostra os números) | 60% | Mudança sempre como teste |
| Propostas que mudam a empresa (parar rede, abrir canal) | 0% | 100% da proposta; decisão do **Antônio** | Por ticket |

**Estimativa geral:** **≈ 80% app / 20% Claude** (≈ 20 min no sábado, ≈ 3 min por dia, ≈ 30 min no mês). Meta depois de 2 meses: **≈ 85% / 15%**, com o banco de perguntas e a fila de testes mais completos.

---

## 8. Ferramentas existentes que já fazem cada passo

| Passo(s) | Ferramenta | Situação |
|---|---|---|
| 1–3 | Arquivo `para_estrategista_<semana>.json` do Analista (manual 11) | **(a criar — etapa 6)** |
| 11–32, 41–52, 63–66, 71–78, 81 | Módulo `estrategista` (`app\hp_studio_nuvem\estrategista\`): `matriz`, `regras`, `plano`, `validar`, `ajuste`, `calendario` | **(a criar)** |
| 5, 15 | `estrategia\config\capacidade.json`, `pesos.json`, `catalogo_formatos.json` | **(a criar)** |
| 6, 57, 62 | `estrategia\calendario_eventos.json` | **(a criar)** |
| 13, 60 | `G:\Meu Drive\Hypado\07 Canais\Futebol\PLANO_CRESCIMENTO.md` | existe |
| 55 | `lotes\<dia>_estaticos.json` + `scripts\estaticos.py` e `scripts\posts_canais.py` (artes) | existe |
| 55 | `story_post.py` (enquete das 16h, contagem pelo emulador) + emulador em `H:\HypadoLocal\android\` | `story_post.py` **(a criar — ticket F)**; emulador existe |
| 61 | `reel_futebol.py` (modos gol, noticia, debate, estatistica, resultado, tabela) | **(a criar — ticket G)** |
| 49 | `scripts\dublar.py` (Piper pt-BR) | existe |
| 67, 2.6.7 | Etapa 2 do app (cardápio e pauta) — o Pauteiro que lê o plano | existe (falta revisão) |
| 69 | `scripts\painel_local.py` | existe |
| 87–91 | `scripts\tickets.py` | existe |
| todos | `hpbase` (`ler_json`, `escrever_json`, `obter_logger`, `agora_iso`) | existe |

---

## 9. Testes de aceitação

Nenhum teste acessa rede ou internet: os números de entrada são arquivos de exemplo. O plano do app só substitui o plano feito pelo Claude depois de passar em **todos** e de **7 dias** (1 plano semanal + 7 ajustes diários) de **modo sombra**.

| Nº | Teste | Entrada | Passa se |
|---|---|---|---|
| T-01 | R01 corte | Formato com razão 0,39, n = 5, quantidade 4 | Nova quantidade **2**; linha em `decisoes` com R01 e "0,39" |
| T-02 | R02 reforço | Razão 1,62, n = 10, quantidade 10, teto sobrando 4/semana | Nova quantidade **14** (e não 15) |
| T-03 | R03 pausa | Razão 0,38, `semanas_abaixo_50 = 2`, quantidade 4 | Pausado; **1** vaga de teste na semana |
| T-04 | R04 | Testes da pausa com razão 0,85 / 0,60 | Volta com 50% / aposentado 8 semanas |
| T-05 | R13 | Formato com n = 3 e razão 0,20 | **Sem** corte; `dado_insuficiente` |
| T-06 | R14 | Cobertura 85% e um formato com razão 0,30 | **Sem** corte naquele canal; reforços permitidos |
| T-07 | R15 | 5 mudanças grandes no mesmo canal | Ficam **3** (as de maior |razão − 1| × n); 2 "adiadas por R15" |
| T-08 | R11 | TikTok do GTA com prazo 27 dias e razão 0,45 | M = 1,5; **nenhum** corte no TikTok do GTA |
| T-09 | R18 | Reel de contagem na `reta_final` com razão 0,40 por 2 semanas | **Não** é cortado nem pausado |
| T-10 | Fórmula P | Células do passo 19 | P = **0,98**, **0,54**, **0,29** (±0,01) |
| T-11 | Capacidade por canal | Exemplo do passo 16 | Tetos 7/4/3/3/3/3; soma **23**; nenhum canal > 40% |
| T-12 | Capacidade é teto | Canal com teto 7 e demanda 5 | Plano com **5** itens, não 7 |
| T-13 | Invioláveis | Vaga de Futebol com `dublagem_piper`; Pinterest no GTA | Validação **recusa** as duas |
| T-14 | Tetos e intervalo | 5 reels de IG no mesmo dia para uma conta; 2 com 30 min de distância | Validação recusa; o gerador nunca produz isso (100 semanas sorteadas: **0** violações) |
| T-15 | Testes ≤ 20% | Pedido de 12 vagas de teste num canal de 40 vagas | No máximo **8** marcadas |
| T-16 | Janela proibida | Vaga publicada às 19h | Prazo de produção < 18h no pedido ao Pauteiro |
| T-17 | Contagem | Datas 30/09, 12/10, 01/11, 19/11 | "Faltam" 50, 38, 18, "É hoje" |
| T-18 | Esquema | Plano gerado para 6 canais × 7 dias | Valida no JSON Schema da seção 2.6.6; `slot_id` todos únicos |
| T-19 | Determinismo | Mesma entrada 2 vezes | Mesmo plano (mesmo hash, exceto `gerado_em`) |
| T-20 | Ajuste diário | Destaque IDR 2,4 ontem; reserva P0 esgotada; 1 P0 novo | 1 vaga de continuação; 1 P2 de menor P removida; vagas em produção intactas |
| T-21 | Tempo | Plano completo | Gerado e validado em **≤ 60 s** |
| T-22 | Modo sombra (7 dias) | Plano do app × plano do Claude na mesma semana | Mesmo número de itens por canal e dia (±1) em **≥ 90%** dos canal-dias; mesmo formato em **≥ 80%** das vagas; **100%** das diferenças explicadas por uma regra ou por uma decisão do Claude registrada |

---

## Glossário

- **Célula** — uma combinação canal × rede × formato × faixa de horário.
- **Capacidade** — quantos itens a esteira aguenta por dia sem atrasar. É **teto**, não meta.
- **Eficiência** — seguidores ganhos por item produzido.
- **Fator M / F / C** — monetização / fase ou evento / custo de produção, na fórmula de prioridade.
- **Faixa** — intervalo de horário (ex.: `19-21`).
- **Formato** — o "tipo de post" do catálogo (ex.: `reel_contagem`, `carrossel_lista`).
- **Item** — uma pasta da esteira; um vídeo que sai em 5 redes é 1 item.
- **P (nota de prioridade)** — nota da célula pela fórmula do bloco D.
- **P0 / P1 / P2** — urgente / do dia / programado. P0 não é planejado; usa a reserva.
- **Pilar** — linha editorial (contagem regressiva, notícia oficial, debate...).
- **Razão** — alcance médio do formato ÷ alcance médio do canal na mesma rede.
- **Reserva P0** — capacidade guardada para o que é urgente.
- **Teste A/B** — comparar duas versões mudando uma coisa só.
- **Vaga (slot)** — um item planejado, com canal, formato, redes, horários e público.
