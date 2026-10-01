# C — Facebook Página: agenda por API (C1), comentários (C2) e Instagram/Threads (C3)

Agente C, rodada 2, 01/10/2026. Trabalho em `/home/user/HP` (branch `claude/relaxed-cray-0fkcdu`), sem commit.
Cobre a tarefa **C** do `docs/PROMPT_NUVEM_2.md` (§3.3, §4.3, §4.5 post.json/publicar.json/agendados.json, §5-C).
Tudo em `app/hp_studio_nuvem/publicar_extra/` com o contrato `cliente.pedir(...)` do `contrato_pc.py`
(Graph API v26.0, token no `access_token` da consulta/form, nunca na URL). Não toquei em `youtube_extra.py`,
`LEIA_youtube.md`, `contrato_pc.py`, `hpbase/`, `tests/conftest.py` nem em nada da rodada 1.

## 1. Feito / pela metade / não deu

### C1 — Agenda da Página (`facebook_extra.py`)

| Critério de pronto | Situação |
|---|---|
| `listar_agendados(cliente, token, pagina_id)` → `GET /{page}/scheduled_posts?fields=id,message,scheduled_publish_time,created_time,permalink_url,is_published,attachments{media_type,url}&limit=100`, paginado por `paging.next` | **Feito** — o `paging.next` da Meta vem com `access_token` dentro: a URL é limpa (`_url_sem_token`) e o token volta pela consulta, então nunca entra em URL nem log |
| Lista normalizada `[{id, tipo (post\|reel), quando (Brasília "AAAA-MM-DD HH:MM"), texto, link, bruto}]` | **Feito** — epoch e ISO `+0000` viram Brasília (`hpbase.FUSO`); link relativo ganha `https://www.facebook.com`; ordenada pela hora; `tipo="reel"` quando o permalink é `/reel/` ou o anexo é `video_reel` |
| Reels agendados: confirmar na doc oficial | **Confirmado que a doc NÃO diz** (ver seção 1.1): implementada a tentativa `GET /{page}/video_reels?fields=id,title,description,scheduled_publish_time,video_status,permalink_url&limit=100`, só os itens com `scheduled_publish_time` e sem status publicado, cada um com **`"confirmar": True`**; se a chamada falhar, vai para `avisos=[...]` e a lista principal vale; `incluir_reels=False` desliga; constante `REELS_AGENDADOS_CONFIRMADO = False` |
| `cancelar_agendado(cliente, token, id)` → `DELETE /{id}` | **Feito** — token na consulta; `entrada("cancelado")` ou `entrada("erro", erro=português, codigo, categoria, permissao, transitorio)` |
| `reagendar(cliente, token, id, nova_hora, agora=None)` → `POST /{id}` com `scheduled_publish_time` (epoch UTC) + `is_published=false`; janela 10 min a 75 dias (reel 10 min a 29 dias), mensagem em português | **Feito** — `tipo="post"\|"reel"`; `agora` injetado (sem relógio escondido nos testes); hora inválida, 9 min, já passou, 76 dias e reel 30 dias não chamam a API (`categoria: "janela"`) |
| `comparar_com_agendados_json(agendados_api, agendados_json, tolerancia_min=5)` → `{"buracos", "duplicados", "hora_errada", "sobras", "ok"}` casando por id (links) ou início do texto normalizado; aceita `{"itens": [...]}` real e lista/`{"posts"}` | **Feito** — mais `"ignorados"` (itens do JSON sem Facebook em `redes` e sem link, ou com status cancelado/erro), `"resumo"` em português; id vem de `links.facebook` (`/posts/N`, `/videos/N`, `/reel/N`, `?v=N`, `story_fbid=N`) ou `ids.facebook`; texto casa por prefixo normalizado (≥ 8 caracteres) escolhendo o de hora mais próxima; aceita também `Path` do arquivo |
| `erro_graph(resposta\|ErroRede)` em português com 1363040/1363127/1363128/1363129, 190, 10/200-299 (diz QUAL permissão), 4/17/32/613, 100, 368 e genérico; resultados no formato `entrada()` | **Feito** — `detalhar_erro_graph()` devolve `{categoria, codigo, subcodigo, tipo, mensagem_meta, fbtrace, permissao, transitorio, mensagem}`; códigos de reel valem como `code` ou `error_subcode`; permissão: primeiro a que a própria mensagem da Meta cita (regex `pages_*`, `instagram_*`, `threads_*`...), senão a da ação (`PERMISSOES[acao]`, "a Meta não disse qual, mas para responder é preciso pages_manage_engagement"); 100/33 = "não existe mais"; 1/2 = passageiro; 80001 também é limite; HTTP sem JSON e `ErroRede` tratados; `fbtrace_id` no fim da frase |

### C2 — Comentários (`comentarios.py` + `lexico_comentarios.json`)

| Critério de pronto | Situação |
|---|---|
| `ler_comentarios(cliente, token, post_id, desde=None, limite=200)` → `GET /{post}/comments?fields=id,message,from,created_time,like_count,comment_count&filter=stream&order=chronological&limit=100` paginado; `desde` = `since` epoch + filtro | **Feito** — `{id, texto, autor_id, autor_nome, criado_em (Brasília), curtidas, respostas, post_id, bruto}`; `from` ausente (privacidade) → `autor_id=None` |
| `curtir` → `POST /{id}/likes`; `responder` → `POST /{id}/comments {"message"}`; `ocultar` → `POST /{id} {"is_hidden": true}` | **Feito** — token no form; resposta vazia não chama; `ocultar` existe mas nenhuma regra usa (ofensivo = não fazer nada) |
| `classificar_comentario(texto, lexico=None) -> responder\|curtir\|ignorar`, pura, conservadora, sem IA, léxico em JSON | **Feito** — `classificar_detalhado()` dá também o `motivo`; ordem: ofensivo → spam/link → emoji puro → marcação de amigo → sarcasmo → pergunta (`?` ou marca forte; "sério?", "jura?! kkkk", "é mesmo??" são espanto → curtir) → pedido → crítica que vale conversa → elogio → **na dúvida curtir**; caixa alta e acento somem na normalização; disfarces de palavrão (`f.d.p`, `m3rda`, `p*rra`, `merdaaaa`) são desmascarados antes da lista |
| Léxico `lexico_comentarios.json` com `ofensivos` (163, **o Antônio revisa**), `ofensivos_regex`, `spam` (165), `spam_regex` (links, "ganhe dinheiro", "chama no pv", "renda extra", "me segue", telefone, bets...), `pergunta_marcas`, `pergunta_inicio_regex`, `pergunta_retorica`, `pedido_marcas`, `critica_que_vale_conversa`, `elogio`, `sarcasmo`, `emoji_puro_regex`, `marcacao_regex`, `nossos_handles_regex`, `risada_regex` | **Feito** — cabeçalho `_leia` explica como editar; regra: entrada em `ofensivos` = sem curtida e sem resposta |
| `ConfigComentarios` (dataclass): `max_respostas_por_passada=25`, `uma_resposta_por_pessoa=True`, `so_posts_nossos=True`, `intervalo_entre_respostas_s=20`, `curtir_elogios=True`, `enviar=False` | **Feito** — mais `intervalo_entre_curtidas_s=3`, `max_curtidas_por_passada=60` (nunca em massa) e `parar_em=("token","permissao","bloqueio","limite")` |
| `planejar(comentarios, ja_tratados, cfg, posts_nossos, redator=None)` → ações `{"acao", "comentario_id", "autor_id", "texto_resposta" (do redator ou "a redigir"), "motivo"}` com 1 por pessoa, máximo por passada, só post nosso | **Feito** — já tratados nem entram; 2ª pergunta da mesma pessoa vira curtida ("1 por pessoa"); além do limite fica "para a próxima passada" (não é marcado); `nossos_ids` pula comentário da própria Página; redator que quebra não derruba a proposta |
| `executar(cliente, token, acoes, cfg, estado, enviar=False, dormir=injetado)` — padrão NÃO envia; com `enviar=True` curte/responde, grava estado (ids por comentário e por autor, JSON atômico injetável) e espera o intervalo; idempotente | **Feito** — `EstadoComentarios(caminho)` grava com `hpbase.escrever_json` depois de CADA envio; segunda passada = 0 POST (teste); "a redigir" é pulado; erro de token/permissão/bloqueio/limite para a passada e nada fica marcado; `funcoes=` troca curtir/responder para outra rede |
| Permissões descritas para leigo | **Feito** — `LEIA_facebook.md` (tabela) e seção 6 abaixo; confirmado na doc: responder comentário exige **`pages_manage_engagement`**, não `pages_manage_posts` |
| Banco ≥ 60 comentários inventados com classe esperada; zero falso "responder" em ofensivo e nenhum em emoji puro; teste parametrizado que nomeia o comentário | **Feito** — **114 comentários** (`testes/comentarios_banco.json`: 43 ignorar, 41 curtir, 30 responder; grupos elogio, elogio_giria, caixa_alta, emoji, só pontuação, pergunta, pergunta_giria, pergunta_retorica, pedido, critica, ofensa_palavrao, ofensa_sem_palavrao, ofensa_pergunta, ofensa+elogio misturado, spam_link/pv/segue/aposta/contato, marcacao, marcação nossa + pergunta, sarcasmo, giria, neutro, opinião, dúvida sem "?", vazio); `test_banco_de_comentarios[grupo:texto]` falha nomeando o comentário; `test_zero_falso_responder_em_ofensivo_e_nenhum_em_emoji_puro` |

### C3 — Instagram e Threads (`comentarios_ig_threads.py`) — **feito**

| Critério | Situação |
|---|---|
| Instagram: `GET /{media-id}/comments`, `POST /{comment-id}/replies`, ocultar `POST /{comment-id}?hide=true` (graph.instagram.com v21.0, token IG) | **Feito** — `ig_ler_comentarios` (paginado, pula `hidden`), `ig_responder`, `ig_ocultar`, `ig_executar` (reusa `comentarios.executar`; a API do IG **não curte comentário**: toda ação "curtir" é pulada e aparece no resultado) |
| Threads: `GET /{media-id}/replies` (graph.threads.net v1.0), responder via `POST /me/threads` com `reply_to_id` + `POST /me/threads_publish` | **Feito** — `th_ler_respostas` (`reverse=false`, pula `hide_status=HIDDEN`), `th_responder` (2 passos, `creation_id`, `espera_s`/`dormir` opcionais), `th_ocultar` (`POST /{reply-id}/manage_reply {"hide": true}`, só 1º nível), `th_executar` |
| Permissão do Instagram confirmada na doc | **Confirmado** (seção 1.1): login do Instagram = `instagram_business_basic` + `instagram_business_manage_comments`; login do Facebook = `instagram_basic` + `instagram_manage_comments` + `pages_read_engagement` |
| Testes | 8 em `testes/test_comentarios_ig_threads.py` (além dos ≥ 40 exigidos) |

**Pela metade / não deu:** nada da tarefa. Ficam marcados "confirmar" (seção 8): reels agendados na listagem; host/versão do IG e do Threads que o PC usa.

### 1.1 Documentação oficial lida (curl, só leitura, 9 páginas em 01/10/2026 05:53 UTC)

| Página | O que confirma |
|---|---|
| https://developers.facebook.com/docs/graph-api/reference/page/scheduled_posts/ (v26.0) | `GET /{page-id}/scheduled_posts` devolve "A list of PagePost nodes", Page Access Token; **"This endpoint doesn't have any parameters"** (fields/limit são a expansão padrão da Graph); erros 80001, 100, 200, 283 ("requires pages_read_engagement and/or pages_read_user_content and/or..."), 190. **Nada sobre reels.** |
| https://developers.facebook.com/docs/graph-api/reference/v26.0/page/video_reels | **"Reading: You can't perform this operation on this endpoint"**; Creating com `video_state` enum {DRAFT, PUBLISHED, SCHEDULED} e `scheduled_publish_time`. Ou seja: a referência diz que não se lê; o guia abaixo diz que se lê os publicados. Listar os AGENDADOS não está documentado → tentativa com `"confirmar": True`. |
| https://developers.facebook.com/docs/video-api/guides/reels-publishing/ (Updated Jul 30, 2026) | "Get a List of Reels: To get a list of all reels **published** on your Facebook Page, send a GET request to /page-id/video_reels"; permissões `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`; limite 30 reels/24 h; tabela de erros **1363040** (proporção 16:9 a 9:16), **1363127** (mínimo 540x960, recomendado 1080x1920), **1363128** (3 a 90 s), **1363129** (24 a 60 fps) — as frases do `erro_graph` vêm daí. |
| https://developers.facebook.com/docs/graph-api/reference/v26.0/page/feed | `scheduled_publish_time`: "Must be date between **10 minutes and 75 days** from the time of the API request"; `is_published` é campo do post agendado; publicar exige `pages_manage_posts` + `pages_read_engagement` + `pages_show_list`; ler exige `pages_read_engagement` + `pages_read_user_content`. |
| https://developers.facebook.com/docs/pages-api/posts/ | Diz "**between 10 minutes and 30 days**" (conflita com os 75 da referência; o PC já usa 75 — mantive 75, seção 8); `DELETE /{page_post_id}` apaga o post; `POST /{page_post_id}` atualiza. |
| https://developers.facebook.com/docs/graph-api/reference/v26.0/object/comments | Ler: "The same permissions required to view the parent object"; `filter=stream` ("All-level comments in chronological order... useful for comment moderation tools"), `order=chronological`; **Publicar: "A Page access token requested by a person who can perform the MODERATE task on the Page" + "The pages_manage_engagement permission"** — responder NÃO pede `pages_manage_posts`. |
| https://developers.facebook.com/docs/graph-api/reference/v26.0/comment | Updating: `POST /{comment_id}` com `is_hidden` ("Only applicable to Page comments"); edge `likes`; erros 100, 80001, 200, 368, 190, 283, 613, 210. |
| https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/comment-moderation | Host `graph.instagram.com` (login IG) ou `graph.facebook.com` (login FB); permissões acima; endpoints `GET /<IG_MEDIA_ID>/comments`, `POST /<IG_COMMENT_ID>/replies` (`message`), `POST /<IG_COMMENT_ID>` (hide/unhide); exemplos em **v26.0**. |
| https://developers.facebook.com/docs/threads/reply-management (Updated Feb 13, 2026) | `POST /<THREADS_REPLY_ID>/manage_reply` com `hide=true\|false` (só 1º nível); `POST /me/threads` + `POST /{threads-user-id}/threads_publish?creation_id=...`; host nos exemplos: **graph.threads.com** (o prompt e o PC usam graph.threads.net). |

## 2. Arquivos

**Novos** (todos em `app/hp_studio_nuvem/publicar_extra/`):
- `facebook_extra.py` (605 linhas) — C1 + `erro_graph`/`detalhar_erro_graph`/`ErroGraph` + `_pedir`/`_paginar` (reaproveitados por C2/C3) + `ler_hora`/`hora_brasilia`/`epoch_utc`
- `comentarios.py` (509) — C2
- `lexico_comentarios.json` (1112) — léxico editável
- `comentarios_ig_threads.py` (181) — C3
- `LEIA_facebook.md` (84) — 1 página, leigo
- `testes/test_facebook_extra.py` (381; 64 testes), `testes/test_comentarios.py` (411; 153 testes), `testes/test_comentarios_ig_threads.py` (167; 8 testes), `testes/comentarios_banco.json` (114 comentários)

**Arquivos da rodada 1 alterados:** nenhum. (`publicar_extra/__init__.py`, `contrato_pc.py`, `hpbase/*`, `tests/conftest.py` intactos.)

## 3. Patches

Nenhum (nenhum arquivo da rodada 1 foi alterado).

## 4. Testes (números reais, saída do pytest)

| Comando | passed | failed | skipped | tempo |
|---|---|---|---|---|
| `cd app/hp_studio_nuvem && python3 -m pytest -q -p no:cacheprovider publicar_extra/testes/test_facebook_extra.py publicar_extra/testes/test_comentarios.py` (o comando da tarefa) | **217** | 0 | 0 | **0,46 s** |
| só `test_facebook_extra.py` | 64 | 0 | 0 | 0,20 s |
| só `test_comentarios.py` | 153 | 0 | 0 | 0,44 s |
| `python3 -m pytest -q -p no:cacheprovider publicar_extra/testes/test_comentarios_ig_threads.py` (C3) | 8 | 0 | 0 | 0,12 s |
| `python3 -m pytest -q -p no:cacheprovider publicar_extra` (pacote inteiro: os meus 225 + os 99 do agente B) | **324** | 0 | 0 | 0,61 s |

Módulos da rodada 1 tocados: nenhum (não rodei a suíte da rodada 1 porque nada dela mudou; o pacote
`publicar_extra` inteiro, que compartilha o `contrato_pc.py`, está verde acima).

O que os testes cobrem: URL, método, parâmetros e corpo de cada chamada (token no `access_token` da consulta
ou do form, nunca na URL); paginação com o token tirado do `paging.next`; reels como tentativa `confirmar`;
`comparar_com_agendados_json` com a fixture real `agendados_exemplo.json` (sem Facebook → 2 ignorados; com
Facebook → ok por id do link, ok por texto, hora errada 12 min, buraco, duplicado, 2 sobras, tolerância 15,
status cancelado, formatos lista/`posts`/`agendados`/`itens`/Path); janelas de reagendar (9 min, 10 min, já
passou, 75 d, 76 d, reel 29 d, reel 30 d, reel 9 min); 22 casos de `erro_graph` (4 códigos de reel como code e
como subcode, 190/102, 10/200/283 com o nome da permissão, 4/17/32/613/80001, 100 e 100/33, 368, 2, genérico,
HTTP 500 sem JSON, ErroRede); banco de 114 comentários parametrizado; caixa alta e gíria; léxico injetado;
desmascarar; `ler_comentarios` (parâmetros, paginação, limite, `desde`, sem `from`); curtir/responder/ocultar;
dataclass; planejar (classes, redator, redator quebrado, 1 por pessoa, estado anterior, máximo 25 e 3, só post
nosso, já tratados, própria Página, curtidas desligadas, limite de curtidas); executar sem enviar = 0 POST;
enviar=True idempotente com arquivo em pasta com espaço, gravação atômica sem `.tmp` sobrando, segunda passada
= 0 POST; intervalo só entre respostas (`[20]`) e entre curtidas; para em token vencido sem marcar; funções
injetadas; estado ausente/quebrado; IG e Threads (listagem, resposta em 2 passos, ocultar, executar, idempotência);
e em cada módulo um teste de que `FAKE_NAO_E_TOKEN_1` não aparece em URL, log do cliente, resultado, exceção
nem arquivo.

## 5. Suposições que sobraram

| Suposição | Arquivo | Onde trocar |
|---|---|---|
| Reels agendados aparecem em `GET /{page}/video_reels` com `scheduled_publish_time` (a doc não diz; pode ser que apareçam em `scheduled_posts` com permalink `/reel/`, que também é tratado) | `publicar_extra/facebook_extra.py` | `listar_agendados` (bloco `if incluir_reels`), constantes `CAMPOS_REELS_AGENDADOS`, `REELS_AGENDADOS_CONFIRMADO` |
| Para reagendar, o parâmetro é `is_published=false` (como o prompt pede); a doc do feed mostra `published=false` na criação | `facebook_extra.py` | `reagendar` (dict `form`) |
| Janela do post = 75 dias (referência do feed e o PC), não 30 (guia Pages API) | `facebook_extra.py` | `JANELA_DIAS_POST` |
| `scheduled_publish_time` na listagem pode vir como epoch ou ISO `+0000` (os dois são lidos) | `facebook_extra.py` | `ler_hora` |
| Id do post no `links.facebook` do agendados.json está em `/posts/N`, `/videos/N`, `/reel/N`, `?v=N` ou `story_fbid=N`; o id da API é `PAGE_N` | `facebook_extra.py` | `_RX_ID_LINK`, `_id_do_link`, `comparar_com_agendados_json` (casamento por `sufixo`) |
| Item do agendados.json sem `redes` conta como do Facebook; com `redes` sem "facebook" e sem link é ignorado | `facebook_extra.py` | `_item_json_normalizado` (`relevante`) |
| Nossos handles começam com `hp`/`hypado` (marcação nossa não é "marcação de amigo") | `lexico_comentarios.json` | chave `nossos_handles_regex` |
| Sarcasmo explícito ("só que não", "parabéns pela mentira", "fonte: confia") → `ignorar` (nem curtida nem resposta) | `lexico_comentarios.json` / `comentarios.py` | chaves `sarcasmo`, `sarcasmo_regex` / `classificar_detalhado` |
| Só pontuação/número ("???", "...", "2026") → `ignorar`; emoji puro → `curtir` | `comentarios.py` | `classificar_detalhado` (bloco `emoji_puro`) |
| Palavrão positivo ("caralho que vídeo bom", "tô puto com o adiamento") → `ignorar` (conservador: ofensivo vence) | `lexico_comentarios.json` | lista `ofensivos` (tirar "caralho"/"puto" se o Antônio preferir) |
| Instagram em `graph.instagram.com/v21.0` e Threads em `graph.threads.net/v1.0` (como o prompt diz; a doc mostra v26.0 e graph.threads.com) | `comentarios_ig_threads.py` | `API_IG`, `API_TH` |
| Threads: resposta de texto publica logo em seguida (`espera_s=0`); a doc fala em ~30 s para mídia | `comentarios_ig_threads.py` | `th_responder` (`espera_s`, `dormir`) |
| `since` é aceito em `/{post}/comments` (o prompt pede; a referência não lista o parâmetro) — por isso há também o filtro local por `created_time` | `comentarios.py` | `ler_comentarios` |

## 6. Depende do Antônio

1. **Permissões do token da Página** (app "HP Publicador" em developers.facebook.com → Casos de uso → Gerenciar
   Páginas → adicionar; depois gerar o token de novo com `hp publicar facebook-token`, porque token velho não
   ganha permissão nova):
   - `pages_read_engagement` — ler a agenda e os comentários (+ `pages_read_user_content` para ver o texto de quem comentou);
   - `pages_manage_engagement` — curtir, responder e ocultar comentários como a Página (quem gera o token precisa ter a tarefa "Moderar" na Página);
   - `pages_manage_posts` — cancelar/reagendar posts (já deve existir: é a mesma de publicar).
   Se faltar, a mensagem de erro diz exatamente qual ("Falta a permissão pages_manage_engagement no token da Página...").
2. **Revisar `lexico_comentarios.json`** (Bloco de Notas): a lista `ofensivos` decide o que fica sem curtida e
   sem resposta; `spam` e `sarcasmo` idem. Depois de mexer, rodar os testes (o banco de 114 acusa o que mudou).
3. **Ligar o envio**: por padrão nada vai para a rede (`enviar=False`); o PC liga com `enviar=True` quando o
   Antônio aprovar a proposta (`planejar`) — sugestão: 1 semana só em modo simulado, lendo o resumo.
4. Instagram: confirmar que o token `IG_<conta>` do `meta_tokens.txt` tem `instagram_business_manage_comments`
   (o publicador_meta só precisava de publicar). Threads já tem `threads_read_replies` + `threads_manage_replies`.
5. Conferir no Planner do Business Suite, uma vez, se um reel agendado pelo PC aparece na `listar_agendados`
   (marcado `confirmar: True`) — é a única parte que a documentação não garante.

## 7. Pendências para o Diretor

Texto pronto para `.claude\` (rotina do conferente-de-agenda, substituindo o Chrome):

```
# conferente-de-agenda (API)
Para cada canal com Página no Facebook (facebook_paginas.json): token = token_de(canal);
itens = facebook_extra.listar_agendados(cliente, token, pagina_id, avisos=avisos);
rel = facebook_extra.comparar_com_agendados_json(itens, <07 Canais\<Pasta>\agendados.json ou 06 Projeto\agendados.json>).
Relate rel["resumo"] e liste buracos, duplicados e hora_errada com id, hora do JSON e hora da Página.
Reagendar/cancelar só com aprovação do Antônio (facebook_extra.reagendar / cancelar_agendado).
Reels com "confirmar": True precisam de conferência manual no Planner até o Antônio confirmar o endpoint.
```

```
# comentarios-pagina (proposta, nunca envio)
Para cada post nosso das últimas 48 h: lidos = comentarios.ler_comentarios(cliente, token, post_id, desde=48h);
estado = comentarios.EstadoComentarios(H:\HypadoLocal\app\publicar\comentarios_estado_<canal>.json);
acoes = comentarios.planejar(lidos, estado.conjunto_tratados(), ConfigComentarios(), posts_nossos, redator=<Claude redige>).
Mostre a proposta (acao, texto, motivo) e só rode executar(..., enviar=True) com aprovação. Ofensivo: nada.
```

## 8. Decisões em aberto / conflitos

1. **Reels agendados na listagem** — a referência de `video_reels` diz "Reading: You can't perform this operation";
   o guia de Reels diz que `GET /page-id/video_reels` lista os **publicados**. Nenhuma página diz como listar os
   agendados. Implementei a tentativa marcada `"confirmar": True`; se o Antônio vir que o reel agendado aparece em
   `scheduled_posts` (com permalink `/reel/`) ou não aparece em lugar nenhum, basta mudar `REELS_AGENDADOS_CONFIRMADO`
   / `incluir_reels`.
2. **75 dias x 30 dias** — a referência do feed (`page/feed`) diz 75; o guia `pages-api/posts` diz 30. Mantive 75
   (o prompt e o PC). Se a API recusar acima de 30, trocar `JANELA_DIAS_POST`.
3. **Sarcasmo = ignorar** — o prompt só define ignorar para ofensivo e spam ("na dúvida, curtir"). Curtir "parabéns
   pela mentira" ficaria ruim, então marquei sarcasmo explícito como ignorar. Antônio decide; é só esvaziar a lista
   `sarcasmo` para voltar ao "na dúvida, curtir".
4. **Palavrão em elogio** ("caralho que vídeo bom") vira ignorar — conservador de propósito (zero falso responder/curtir
   em ofensa). Se o Antônio quiser curtir esses, tirar "caralho"/"porra"/"puto" de `ofensivos`.
5. **Hosts/versões do IG e do Threads** — a doc atual mostra `v26.0` para o Instagram e `graph.threads.com` para o
   Threads; o prompt pede `v21.0` e `graph.threads.net`. Deixei o que o prompt pede em `API_IG`/`API_TH`; conferir
   com o `publicador_meta.py` do PC e alinhar.
6. **`is_published=false` no reagendar** — segui o prompt; se a Meta responder 100 "Invalid parameter", trocar
   por `published=false` no dict `form` de `reagendar`.
7. **`ocultar` não é usado** por nenhuma regra (regra do Antônio: ofensivo = não fazer nada). Fica disponível para o
   caso de ele querer esconder spam com link; ligar seria 1 linha no `planejar` (acao "ocultar") + `executar`.
