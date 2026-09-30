# FUTURO — NÃO IMPLEMENTAR

> **Este manual descreve um cargo que ainda NÃO existe na HP.** Afiliados é **assunto futuro** por decisão do Antônio. **Não desenvolver nada agora**: nenhum código, nenhuma pasta, nenhum módulo, nenhuma conta, nenhum link, nenhuma vaga no plano do Estrategista, nenhuma menção em post. O manual existe só para que, **quando** o Antônio liberar, o trabalho comece do jeito certo.
>
> Se você (pessoa ou Claude) chegou aqui por causa de uma tarefa do dia a dia: **pare**. Nada daqui se aplica hoje.

---

# Manual 13 — Comercial de afiliados

> **Cargo:** Comercial de afiliados (receita com links de afiliado de programas oficiais) — **FUTURO**
> **Empresa:** Hypado (HP) — 6 perfis: GTA 6 | HP, Futebol | HP, Filmes e Séries | HP, Receitas | HP, Carros | HP, Destinos | HP
> **Versão:** 1.0 — 30/09/2026 (rascunho para o futuro)
> **Pasta deste manual no PC:** `G:\Meu Drive\Hypado\06 Projeto\app\manuais\13_comercial_afiliados.md`
> **Quem vem antes (quando existir):** 12 Estrategista (diz onde e quanto) · **Quem vem depois:** 08 Redator, 07 Designer, 10 Publicador, 11 Analista
> **Situação:** **FUTURO — NÃO IMPLEMENTAR.** Marcações neste manual: tudo o que é ferramenta nova é **(a criar — futuro)**.

---

## 0. Quando este cargo pode começar (gatilho)

O cargo **só começa** quando **todas** as condições abaixo forem verdadeiras:

1. O **Antônio** disse, com todas as letras, que é hora de começar afiliados (por ticket ou na conversa com a sessão HP GESTÃO). Nenhuma outra pessoa, sessão ou "sinal dos números" libera.
2. O Antônio **escolheu os programas** e **ele mesmo** criou as contas, aceitou os termos e fez o cadastro fiscal/bancário. **O Claude nunca cria conta, nunca aceita termos, nunca digita senha ou código.**
3. As regras legais de divulgação (publicidade identificada) foram **conferidas na fonte oficial** na semana de início (ver 4.2).
4. Sugestão para não atrapalhar o objetivo nº 1 (crescer e monetizar): pelo menos **1 canal** já monetizando em alguma rede **ou** com **≥ 10 mil seguidores** numa rede, e taxa de engajamento estável há 4 semanas (o Analista mostra). Afiliado cedo demais em conta pequena rende pouco e pode passar imagem de "conta que só quer vender".

Até lá: **nada**.

---

## 1. Objetivo do cargo

### 1.1 Em uma frase

**Quando liberado**, gerar receita com **links de afiliado de programas oficiais** ligados ao assunto de cada canal, **sem** derrubar alcance, **sem** enganar ninguém e **sempre** com a publicidade identificada.

### 1.2 O que entregaria

1. Uma **lista curta de programas** aprovados pelo Antônio, por canal.
2. **Links** gerados pela ferramenta **oficial** de cada programa, organizados por canal e produto.
3. **Sugestões de vagas** com afiliado para o Estrategista (que decide se entram no plano), respeitando o limite de frequência (4.3).
4. **Textos de divulgação** (com a identificação de publicidade) para o Redator encaixar.
5. **Relatório mensal**: cliques, vendas, comissão e efeito no alcance (o post com link perdeu alcance?).

### 1.3 Metas (quando existir)

| Indicador | Meta inicial |
|---|---|
| Posts com afiliado **sem** identificação de publicidade | **0** |
| Links quebrados ou levando a página errada | **0** |
| Queda de alcance dos posts com afiliado contra a média do mesmo formato | **≤ 15%** (se passar, reduzir frequência) |
| Posts com afiliado sobre o total do canal | **≤ 20%** |
| Receita por mil views dos posts com afiliado | Medir 8 semanas antes de definir meta |

### 1.4 Ideias de encaixe por canal (hipóteses para o futuro)

| Canal | O que faz sentido indicar | O que **nunca** indicar |
|---|---|---|
| Receitas | Utensílios, eletroportáteis, ingredientes difíceis de achar (lojas e marketplaces com programa oficial) | Suplemento com promessa de saúde; produto sem nota fiscal |
| Carros | Acessórios, itens de manutenção, cursos oficiais de direção defensiva | Peça "paralela" sem procedência; qualquer coisa ilegal (ex.: equipamento que burla fiscalização) |
| Destinos | Hospedagem, passagens, seguro-viagem, passeios (programas oficiais de agências e plataformas) | Pacote de agência sem cadastro; "promoção" sem data |
| GTA 6 | O jogo e consoles em lojas oficiais/marketplaces com programa oficial | Chave de jogo de revenda duvidosa, "conta pronta", mod pirata, qualquer coisa do Flow Games |
| Filmes e Séries | Assinaturas de streaming **se** houver programa oficial; livros/boxes relacionados | Site pirata, "IPTV", qualquer link de conteúdo não licenciado |
| Futebol | Produtos **oficiais** (loja oficial do clube/liga, se tiver programa) | Aposta esportiva (**fora**, mesmo que pague bem), produto falsificado |

> **Aposta esportiva e cassino ficam fora da HP**, com ou sem programa de afiliado. É decisão de marca e de risco; só o Antônio poderia rever, e por escrito.

---

## 2. Entradas e saídas (desenho para o futuro — nada disso existe)

### 2.1 Pastas **(a criar — futuro)**

```
H:\HypadoLocal\afiliados\                 (NÃO criar agora)
├── programas.json          ← programas aprovados pelo Antônio
├── links.json              ← links gerados na ferramenta oficial
├── sugestoes_<AAAA>-W<nn>.json   ← sugestões de vagas para o Estrategista
└── relatorios\afiliados_<AAAA-MM>.json
```

Os dados de acesso aos programas (se algum dia houver API oficial) ficariam em `H:\HypadoLocal\segredos\`, lidos só pelo script, **nunca** impressos.

### 2.2 `programas.json` (exemplo do formato)

```json
{
  "versao_esquema": 1,
  "aprovado_por": "Antônio",
  "aprovado_em": "AAAA-MM-DD",
  "programas": [
    {
      "id": "marketplace_exemplo",
      "nome": "Programa de afiliados oficial do Marketplace Exemplo",
      "canais": ["receitas", "carros", "gta"],
      "como_gerar_link": "ferramenta oficial do programa, com a sessão aberta pelo Antônio",
      "comissao_referencia": "conferir na página oficial",
      "regras_do_programa_conferidas_em": "AAAA-MM-DD",
      "proibicoes_do_programa": ["não usar em anúncio pago", "não encurtar link com serviço de terceiros"]
    }
  ]
}
```

### 2.3 `links.json` (exemplo)

```json
{
  "versao_esquema": 1,
  "links": [
    {
      "id": "rec-air-fryer-001",
      "programa": "marketplace_exemplo",
      "canal": "receitas",
      "produto": "Air fryer 4 L (modelo de exemplo)",
      "url": "https://exemplo.com/produto?tag=EXEMPLO",
      "preco_visto": "R$ 399 (valor aproximado, visto em AAAA-MM-DD)",
      "conferido_em": "AAAA-MM-DD",
      "status": "ativo"
    }
  ]
}
```

### 2.4 Acréscimo no `post.json` (manual 10) — **só no futuro**

```json
"afiliado": {
  "tem": true,
  "link_id": "rec-air-fryer-001",
  "onde_aparece": ["pagina_de_links", "story_link", "pinterest"],
  "identificacao": "Publicidade — link de afiliado: a HP pode ganhar comissão, sem custo extra para você.",
  "preco_citado": "Valores aproximados, conferidos em AAAA-MM-DD; podem mudar."
}
```

### 2.5 Relatório mensal (exemplo)

```json
{
  "mes": "AAAA-MM",
  "por_canal": {
    "receitas": { "posts_com_afiliado": 12, "cliques": 1840, "vendas": 37, "comissao_estimada": "conferir no painel oficial", "alcance_rel_vs_formato": 0.91 }
  },
  "fonte": "painel oficial de cada programa (lido pelo Antônio ou por API oficial)"
}
```

---

## 3. Passo a passo (para leigo) — **só quando o Antônio liberar**

**Passo 1.** Confirme o gatilho (seção 0): mensagem ou ticket do Antônio liberando, com os programas escolhidos. Sem isso, **pare aqui**.

**Passo 2.** Confirme que as contas nos programas foram criadas **pelo Antônio** e que **ele** aceitou os termos. O Claude não abre página de cadastro, não preenche formulário, não aceita nada.

**Passo 3.** Leia a **página oficial de regras** de cada programa (só leitura) e anote em `programas.json`: o que é proibido (ex.: usar em anúncio pago, encurtar link, usar a marca no nome do perfil), prazo do cookie, forma de identificação exigida. Data em `regras_do_programa_conferidas_em`.

**Passo 4.** Confira as regras brasileiras de publicidade identificada (Guia de publicidade por influenciadores digitais do CONAR e o Código de Defesa do Consumidor — **conferir na fonte oficial** a versão em vigor) e anote o texto de identificação que a HP vai usar.

**Passo 5.** Monte, com o Antônio, a lista de **categorias** por canal (tabela 1.4). Nada fora da lista.

**Passo 6.** Para cada produto: gere o link **na ferramenta oficial** do programa (com a sessão aberta pelo Antônio; se pedir login, senha ou código → **parar** e avisar por ticket) ou pela API oficial do programa, se existir e estiver autorizada.

**Passo 7.** Abra o link numa aba anônima e confira: leva ao produto certo? Está disponível? O preço visto bate com o que vai ser citado? Anote em `links.json` com `conferido_em`.

**Passo 8.** Escreva a **sugestão de vaga** para o Estrategista (`sugestoes_<semana>.json`): canal, formato em que o produto aparece naturalmente (ex.: `reel_receita` que usa a air fryer), rede, link, motivo.

**Passo 9.** O **Estrategista** decide se entra, respeitando o limite de **20%** dos posts do canal e **nunca** em formato de urgência (P0), notícia de Futebol ou contagem do GTA.

**Passo 10.** O **Redator** (manual 08) coloca no texto: a **identificação de publicidade** logo no começo, o preço com **"Valores aproximados…"** e data, e a chamada ("link na bio", "link no story").

**Passo 11.** O **Designer** (manual 07), quando for o caso, coloca a identificação também na **imagem** (ex.: "Publicidade" no canto), de forma legível.

**Passo 12.** O **Revisor** (manual 09) confere o critério extra "afiliado": identificação presente, preço com aviso, link conferido há ≤ 7 dias, produto dentro da lista. Falhou → volta.

**Passo 13.** Onde o link vai (só por meios oficiais): **página de links** `https://sites.google.com/view/hpcanais` (seção própria "Indicações", marcada como publicidade), **figurinha de link no story** pelo app oficial no emulador, **pin com link** no Pinterest pela página oficial. Nunca em comentário automático, nunca em mensagem direta em massa.

**Passo 14.** O **Publicador** (manual 10) publica normalmente; o `post.json` leva o bloco `afiliado`.

**Passo 15.** **Toda semana**, reconfira os links ativos (passo 7). Produto indisponível ou preço muito diferente → link `inativo` e remoção da página de links.

**Passo 16.** O **Analista** (manual 11) compara o **alcance** dos posts com afiliado com a média do mesmo formato (sem afiliado). Queda > 15% por 2 semanas → reduzir a frequência pela metade.

**Passo 17.** **Todo mês**, o Antônio (ou uma API oficial autorizada) lê o painel de cada programa: cliques, vendas, comissão. O Claude **não** abre painel financeiro que peça login.

**Passo 18.** Monte o relatório mensal (2.5) e a recomendação: manter, aumentar, reduzir ou tirar cada programa, **com números**.

**Passo 19.** Decisões de dinheiro (trocar programa, aceitar proposta de marca, negociar comissão) são **do Antônio**. O cargo só prepara os números.

**Passo 20.** Qualquer problema (link quebrado em post já publicado, reclamação de seguidor, aviso do programa): ticket na área `comercial` com `scripts\tickets.py` **(existe)**. **Nunca** pelo WhatsApp (ele é só para as 3 coisas).

---

## 4. Regras que nunca se quebram

### 4.1 Segurança e contas
1. **Nunca** criar conta, aceitar termos, digitar senha ou código, contornar CAPTCHA, preencher dado fiscal ou bancário. Tudo isso é do **Antônio**.
2. **Nunca** ler ou imprimir token ou chave de programa. Segredos em `H:\HypadoLocal\segredos\`.
3. **Só** programas oficiais e ferramentas oficiais de gerar link. Nada de encurtador de terceiros se o programa proibir; nada de "robô" que imita aplicativo.

### 4.2 Transparência e lei
4. **Todo** post com link de afiliado tem a **identificação de publicidade** visível no texto (e na imagem, quando o link estiver na arte). Regras do CONAR e do CDC: **conferir na fonte oficial**.
5. Preço sempre com **"Valores aproximados…"** e a data em que foi visto.
6. **Nunca** prometer resultado ("emagrece", "economiza X garantido"), nunca inventar avaliação, nunca dizer que usou o produto se não usou.
7. **Nunca** esconder que é afiliado (ex.: link "limpo" disfarçado).

### 4.3 Marca e crescimento
8. **No máximo 20%** dos posts de um canal com afiliado; **zero** em P0, notícia de Futebol, gol, contagem do GTA.
9. **Fora sempre:** aposta esportiva, cassino, pirataria (IPTV, sites de filme sem licença), chave de jogo de origem duvidosa, produto falsificado, Flow Games, qualquer coisa ilegal.
10. O conteúdo tem que ser **bom mesmo sem o link**. Se o post só existe para vender, ele não sai.
11. As regras de conteúdo da HP continuam valendo (crédito, sem vazamento, sem trailer puro, voz sintética só onde é permitida).

### 4.4 Processo
12. Nada deste manual é implementado antes do gatilho da seção 0.
13. Quando for implementar: **7 dias de modo sombra** (o app sugere e o Claude/Antônio compara), como todo o resto (README).

---

## 5. Critérios de qualidade com nota (para quando existir)

| Critério | Nota 10 | Nota 7 | Nota 5 | Nota 0 |
|---|---|---|---|---|
| Identificação de publicidade | No texto **e** na imagem, clara, no começo | Só no texto, no começo | No fim do texto | Ausente |
| Link | Conferido há ≤ 7 dias, leva ao produto certo | Conferido há 8–14 dias | Conferido há 15–30 dias | Quebrado ou errado |
| Preço | Com "Valores aproximados…" e data | Sem data | Sem aviso, mas correto | Preço errado ou prometido |
| Encaixe | Produto aparece naturalmente no conteúdo | Encaixe fraco | Produto "forçado" | Post só para vender |
| Frequência | ≤ 20% dos posts, nenhum em formato proibido | 21–25% | 26–30% | Em P0/gol/contagem, ou > 30% |
| Lista de proibidos | Nada fora da lista 1.4 | — | — | Qualquer item proibido (aposta, pirataria...) |
| Segurança | Nenhum login/termo/código pelo Claude | — | — | Qualquer um |

Classificação igual aos outros cargos: ≥ 9 Excelente; 7–8,9 Bom; 5–6,9 Médio (volta ao Redator/Designer); < 5 Razoável (sai do plano).

---

## 6. Erros comuns e o que fazer (previstos)

| Erro | O que fazer |
|---|---|
| Esquecer a identificação de publicidade | Revisor barra; se já publicou, ticket P0 para o Antônio decidir (editar legenda pelo meio oficial ou apagar) |
| Link quebrado depois de publicado | Tirar da página de links na hora; ticket |
| Preço mudou muito | Link `inativo`; não citar preço de novo sem conferir |
| Programa pede login/código | Parar; ticket para o Antônio |
| Alcance caiu nos posts com link | Reduzir a frequência pela metade (passo 16) |
| Seguidor reclama de "propaganda demais" | Registrar; o Analista mede; o Estrategista reduz |
| Proposta de marca chega por mensagem | Não responder negociando; ticket para o Antônio |

---

## 7. O que o app faria sozinho x o que o Claude decidiria (estimativa para o futuro)

| Tarefa | App | Claude | Antônio |
|---|---|---|---|
| Criar contas, aceitar termos, dados fiscais | 0% | 0% | **100%** |
| Escolher programas e categorias | 0% | 30% (proposta com números) | **70%** (decide) |
| Gerar link (API oficial, se houver) | 80% | 20% | — |
| Conferir links toda semana | 90% | 10% | — |
| Sugerir vagas com afiliado | 60% | 40% | — |
| Texto com identificação | 50% (modelo) | 50% | — |
| Relatório mensal | 90% | 10% | lê e decide |

Estimativa geral (quando existir): **≈ 55% app / 30% Claude / 15% Antônio**.

---

## 8. Ferramentas existentes que já fariam cada passo

| Passo | Ferramenta | Situação |
|---|---|---|
| 8–9 | Plano do Estrategista (manual 12) | **(a criar)** — sem afiliado até o gatilho |
| 10–12 | Redator, Designer, Revisor (manuais 08, 07, 09) | manuais existem; critério "afiliado" **(a criar — futuro)** |
| 13 | Página de links `https://sites.google.com/view/hpcanais` | existe (sem seção de afiliados) |
| 13 | Story com link pelo emulador (`story_post.py`) | **(a criar — ticket F)**; figurinha de link **(a criar — futuro)** |
| 14 | `scripts\publicador_meta.py` e fila `fila_api` | existe (sem bloco `afiliado`) |
| 16 | Módulo `metricas` (manual 11) | **(a criar — etapa 6)** |
| 20 | `scripts\tickets.py` | existe |
| todos | Módulo `afiliados` | **(a criar — futuro; NÃO criar agora)** |

---

## 9. Testes de aceitação (para quando for implementado)

| Nº | Teste | Passa se |
|---|---|---|
| T-01 | Post com `afiliado.tem = true` sem identificação | Revisor/validador **recusa** (10 de 10 casos) |
| T-02 | Afiliado em `reel_gol`, P0 ou `reel_contagem` | Validador do plano **recusa** |
| T-03 | Canal com 25% de posts com afiliado na semana | Plano **recusa** (limite 20%) |
| T-04 | Link de categoria proibida (aposta, IPTV) | **Recusado** em 100% dos casos |
| T-05 | Link sem `conferido_em` nos últimos 7 dias | Post **não** sai |
| T-06 | Preço sem "Valores aproximados…" | Revisor **recusa** |
| T-07 | Busca de segredos nos arquivos de afiliados e logs | **0** ocorrências |
| T-08 | Modo sombra de 7 dias | Sugestões do app × escolhas do Claude/Antônio: ≥ 80% iguais, 100% das diferenças explicadas |

---

## Glossário

- **Afiliado** — quem indica um produto com um link especial e ganha comissão se alguém comprar por ele.
- **Comissão** — a parte do valor da venda que o programa paga ao afiliado.
- **CONAR** — Conselho Nacional de Autorregulamentação Publicitária; publica regras sobre publicidade (inclusive de influenciadores).
- **CDC** — Código de Defesa do Consumidor.
- **Identificação de publicidade** — aviso claro de que aquilo é propaganda ou tem link de afiliado.
- **Programa oficial** — o programa de afiliados mantido pela própria loja/plataforma, com regras públicas.

---

> **Lembrete final: FUTURO — NÃO IMPLEMENTAR.** Nada deste manual vale antes da liberação expressa do Antônio.
