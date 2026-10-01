# Rodada 2 — Tarefa B: YouTube, o que falta além do envio (`publicar_extra/youtube_extra.py`)

Agente B, rodada 2, 01/10/2026. Trabalho em `/home/user/HP` (branch `claude/relaxed-cray-0fkcdu`), sem commit meu.
Cobre B1–B6 do `docs/PROMPT_NUVEM_2.md` (§3.3, §4.3, §4.5 e a tarefa B em §5). O envio (`videos.insert`) é do PC e
não foi refeito. Nenhum teste faz rede; a única rede foi a leitura (curl, só leitura) de 10 páginas oficiais do Google
para confirmar custos e riscos — URLs e data em cada ponto abaixo.

## 1. Feito / pela metade / não deu

| Critério de pronto | Situação |
|---|---|
| **B1** `playlist_do_canal(cliente, token, canal, titulo, criar=True, cache=None)` → id: cache `{canal: {titulo: id}}` primeiro, depois `playlists.list part=snippet&mine=true&maxResults=50` com paginação por `nextPageToken`, título comparado sem acento/maiúscula/espaços duplicados; cria com `playlists.insert part=snippet,status` `{"snippet": {"title","description"}, "status": {"privacyStatus": "public"}}` só se não achou; **nunca duplica** (2ª vez: 0 POST e 0 chamadas); cache injetável (`ler()/gravar(dict)`), padrão `CacheArquivo` em `app\publicar\youtube_playlists.json` abaixo de `hpbase.pasta_app()` (= `H:\HypadoLocal\app\...` no PC, pasta temporária nos testes), gravação atômica via `hpbase.escrever_json` | **Feito** |
| **B1** `adicionar_na_playlist(cliente, token, playlist_id, video_id)`: `GET playlistItems?part=snippet&playlistId=&videoId=` antes; `POST playlistItems?part=snippet` com `{"snippet": {"playlistId", "resourceId": {"kind": "youtube#video", "videoId"}}}`; 409/`duplicate`/`videoAlreadyInPlaylist` → `ja_estava`, não é falha | **Feito** |
| **B2** `atualizar_video(..., publicar_em=None, agora=None)`: `GET videos?part=snippet,status&id=`, mescla, `PUT videos?part=snippet,status` com snippet **completo** (title, description, tags, categoryId, defaultLanguage) e status completo (privacyStatus, publishAt, license, embeddable, publicStatsViewable, selfDeclaredMadeForKids, containsSyntheticMedia — porque a API apaga o que faltar na parte enviada, ver B6); `publishAt` em UTC `…Z` a partir de datetime/`"AAAA-MM-DD HH:MM"` de Brasília (`hpbase.FUSO`) e sempre com `privacyStatus=private`; validação em português ANTES da API (título ≤ 100 sem `<` `>`, descrição ≤ 5.000 bytes UTF-8, tags ≤ 500 contadas como o YouTube, categoria numérica, `publicar_em` no futuro, vídeo já público não agenda) → `status: "invalido"` com 0 chamadas | **Feito** |
| **B3** `conferir_lote(cliente, token, esperado, agora=None)`: 1 `GET videos?part=status,snippet,processingDetails&id=a,b,c` a cada 50 ids (120 ids = 3 chamadas); os 3 diagnósticos de "travado como privado (projeto sem auditoria)" (agendado sem publishAt; pediu público e ficou privado; agendado que passou do horário e continua privado); `uploadStatus`, `rejectionReason` (lista oficial + `size`) e `failureReason` em português; `nao_encontrado` para id que não veio; `"resumo"` com contagens e nº de chamadas | **Feito** |
| **B4** `transcricao_para_srt(dados, inicio, fim, max_palavras=4)` pura: formato 4.5, blocos de até N palavras sem cruzar segmento, tempos relativos a `inicio`, recorte na borda, `00:00:01,240` com vírgula, sem bloco vazio, sem sobreposição; golden com `tests/fixtures/pc_real/transcricao_exemplo.json` | **Feito** |
| **B4** `enviar_legenda(..., idioma="pt-BR", nome="Português", ligado=False)`: `captions.insert` em `upload/youtube/v3/captions?part=snippet&uploadType=multipart`, corpo `multipart/related` (JSON `{"snippet": {"videoId","language","name","isDraft": false}}` + SRT); custo confirmado **400 unidades** → **desligada por padrão**: `entrada("desligado", erro="legenda por API desligada: custa 400 unidades (4 % da cota do dia)…")` sem chamar nada | **Feito** |
| **B5** `registro_de_cota(chamadas, limite_dia=10000, aviso_em=0.8)` → `{"total","por_tipo","avisar","mensagem","envios","restante","desconhecidos","confirmar"}`; tabela `CUSTOS` no topo com `custo`, `fonte` (URL oficial), `confirmado_em` = `CUSTOS_CONFIRMADOS_EM = "2026-10-01"` e `confirmar: False` em todos (todos confirmados hoje); `videos.insert` no balde próprio "envios" (100/dia) fora das 10.000; `Contador.registrar(tipo)` injetável, chamado por toda função do módulo antes de cada pedido (chamada inválida também custa ≥ 1) | **Feito** — ficou dentro do `youtube_extra.py` (a tarefa permitia) |
| `erro_youtube(resposta|ErroRede)` → português: `quotaExceeded` ("cota diária da API do YouTube esgotada (10.000 unidades); volta à meia-noite da Califórnia"), `uploadLimitExceeded`, `duplicate`, 401 ("token vencido: o PC renova"), 403 (permissão/auditoria), `forbidden`, 404, 409, 429, 5xx, rede sem status; tudo passa por `mascarar()` | **Feito** |
| Token: só em `Authorization: Bearer …` (nunca URL/consulta/log/erro/arquivo); o módulo não lê refresh token | **Feito** — provado em `test_nenhum_token_em_resultado_excecao_log_nem_arquivo` e `test_token_so_no_cabecalho_nunca_na_url_nem_na_consulta` |
| Testes com `ClienteFalso` conferindo URL, método, consulta e corpo de cada chamada; paginação; idempotência; cache lido/gravado; snippet completo e publishAt UTC; validações; 3 travados + rejeitado + nao_encontrado + 120 ids; SRT golden; legenda desligada; cota 80 %; tradução de erros; ≥ 40 | **Feito** — 67 funções / **99 itens** do pytest |
| `LEIA_youtube.md` (1 página, leigo) | **Feito** |
| **B6** revisão crítica com página oficial em cada ponto | **Feito** — seção 9 abaixo; o que não deu para confirmar está marcado |

**Pela metade / não deu:** nada da tarefa. Não criei `publicar_extra/testes/conftest.py` (a tarefa C, em paralelo, pode
criar o dela; o meu teste põe `app/hp_studio_nuvem` no `sys.path` e importa a fixture autouse `raizes_temporarias` sozinho).

## 2. Arquivos

**Novos**
- `app/hp_studio_nuvem/publicar_extra/youtube_extra.py` (B1–B5 + cota + erros; 823 linhas)
- `app/hp_studio_nuvem/publicar_extra/testes/test_youtube_extra.py` (67 funções / 99 itens)
- `app/hp_studio_nuvem/publicar_extra/LEIA_youtube.md`
- `docs/rodada2/B.md` (este)

**Da rodada 1 alterados:** nenhum. Não toquei em `contrato_pc.py`, `hpbase/*`, `tests/conftest.py`, `.claude` nem em arquivo de outra tarefa.

Observação: o commit `ef9252e` (05:46 UTC, sessão principal, "metricas: contas.json vira contas_exemplo.json…") já levou
o `youtube_extra.py` junto; o teste e o LEIA ainda estão sem commit (`??`). Eu não fiz commit.

## 3. Patches

Nenhum arquivo da rodada 1 mudou.

## 4. Testes (números reais)

```
cd app/hp_studio_nuvem && python3 -m pytest -q -p no:cacheprovider publicar_extra/testes/test_youtube_extra.py
99 passed in 0.71s
```
passed 99 · failed 0 · skipped 0 · 0,71 s.

Módulos da rodada 1 que eu importo (`hpbase`) + a pasta inteira de `publicar_extra`:
```
cd app/hp_studio_nuvem && python3 -m pytest -q -p no:cacheprovider publicar_extra hpbase
219 passed in 0.46s
```
Sintaxe conferida com `ast.parse(..., feature_version=(3, 11))` nos dois arquivos; `from __future__ import annotations`;
nenhuma linha começa com `## nome.ext`; nenhum arquivo com nome de segredo; nenhum binário.

O que os testes cobrem (por bloco): B1 18 funções (URL/método/consulta/corpo do `playlists.list` e `playlists.insert`,
2 páginas, título normalizado, `criar=False`, 2ª vez 0 POST/0 chamadas, cache antes da API, cache gravado, arquivo padrão
em `app\publicar\youtube_playlists.json` sem `.tmp` e sem token, cota, erro 403 em português, `playlistItems` GET+POST,
`ja_estava`, 409 ×3, idempotência, erro de cota); B2 14 (snippet+status completos, `publishAt` `2026-10-02T12:00:00Z`
×3 formatos de entrada, título 101 e 100, `<`/`>`, 2.600 `é` = 5.200 bytes, regra das tags com 509/559/vazia/texto,
categoria, passado, já público, `privacidade="public"` tira publishAt, não encontrado, 401, cota); B3 14 (120 ids = 3
chamadas com `part` e ids exatos, os 3 travados, futuro ok, publicado/privado como pedido, rejeitado duplicate, falhou
codec, processando 25 %, nao_encontrado + resumo, 11 rejeições + 6 falhas parametrizadas, lista oficial coberta, erro de
cota no lote); B4 11 (golden ×2, borda, vazio, sem sobreposição/sem vazio, segmento sem palavras, vírgula/numeração,
desligada, ligada com multipart/related e cota 400, 409 `captionExists`, vazia/403); B5 6; erros 15 (14 parametrizados);
token 2.

## 5. Suposições que sobraram (suposição · arquivo · função exata onde trocar)

| Suposição | Arquivo | Onde trocar |
|---|---|---|
| Corpo do `captions.insert` montado à mão como `multipart/related` (parte 1 JSON, parte 2 SRT) e enviado em `corpo=` + cabeçalho `Content-Type: multipart/related; boundary=…`. O `multipart=` do contrato parece ser form-data (curl `-F`), que o Google não aceita no `uploadType=multipart` | `publicar_extra/youtube_extra.py` | `enviar_legenda`, `corpo_multipart_related` |
| `publishAt` sai como `AAAA-MM-DDTHH:MM:SSZ` (sem fração); a API aceita ISO 8601 | idem | `para_utc_z` |
| Link nas entradas é `https://www.youtube.com/watch?v=<id>` (o `conferir_lote` não lê `contentDetails.duration`, então não sei se é Short); o §4.8 usa `youtube.com/shorts/<id>` só no aviso do WhatsApp | idem | `link_video` |
| Status das entradas: playlist `adicionado | ja_estava | erro`; vídeo `atualizado | agendado | invalido | erro`; legenda `enviado | ja_existe | desligado | invalido | erro`. O PC só conta como feito `agendado/publicado/pendente_chrome` (`STATUS_FEITO`); se o PC quiser outros nomes, é só trocar os literais | idem | `adicionar_na_playlist`, `atualizar_video`, `enviar_legenda` |
| Vídeo `unlisted`, ou `public` quando pediu privado, sai como `"ok"` com diagnóstico "— confira" (a tarefa fixa 6 status; não inventei um 7º) | idem | `diagnosticar_video` |
| Descrição também não pode ter `<` `>` (a página `docs/videos` diz isso para `snippet.description`; o PC só cita o título) | idem | `validar_metadados` |
| Regra das tags = a oficial: soma dos tamanhos + 1 vírgula entre cada par + 2 aspas por tag com espaço (`Foo-Baz` 7, `Foo Baz` 9) — fonte na docstring | idem | `contar_tags` |
| Cache guarda o título como veio (chave) e compara normalizado; `mine` vai como string `"true"`, `maxResults` como int 50 (igual ao `metricas/youtube.py`) | idem | `playlist_do_canal`, `_cache_busca` |
| Playlist nova nasce `public` (parâmetro `privacidade=`) | idem | `playlist_do_canal` |
| Ao agendar, exijo que o vídeo esteja `private` AGORA (a API só agenda privado nunca publicado); se o PC quiser forçar `private` em vídeo `unlisted`, trocar a checagem | idem | `atualizar_video` (bloco `if quando is not None`) |
| Segmento sem `palavras` vira 1 bloco com o texto do segmento (a §4.5 diz que todo segmento tem `palavras`; é só rede de segurança) | idem | `transcricao_para_srt` |
| Cota: tipo desconhecido conta 1 unidade e sai em `desconhecidos`; `search.list` não está na tabela (o módulo não usa) | idem | `CUSTOS`, `registro_de_cota` |

## 6. Depende do Antônio

1. **Auditoria da API** (é o que destrava tudo): Google Cloud → formulário "YouTube API Services – Audit and Quota Extension Form"
   (link na página https://developers.google.com/youtube/v3/guides/quota_and_compliance_audits). Até aprovar, o `videos.insert`
   responde 200 e o vídeo fica privado (`conferir_lote` mostra `travado_privado`).
2. **Escopo do OAuth**: `youtube_canais.json → escopos` precisa incluir `https://www.googleapis.com/auth/youtube.force-ssl`
   para `captions.insert` e para escrever playlists (se o PC autorizou só `youtube.upload`, re-autorizar com
   `hp publicar youtube-autorizar --canal X` depois de ampliar os escopos no código do PC). **A confirmar** na lista de
   escopos de cada página de referência (não copiei a lista).
3. **Verificação por telefone** da conta de cada canal (YouTube → Configurações → Status e recursos): sem isso vídeo > 15 min
   é rejeitado (`length`). Passo a passo oficial: https://support.google.com/youtube/answer/71673 (lido 01/10/2026):
   app do YouTube → Criar → Enviar vídeo → escolher um vídeo > 15 min → seguir "verificar conta" (SMS ou ligação).
   Depois de verificar, o vídeo rejeitado tem que ser **enviado de novo**.
4. **Audiência do canal** no YouTube Studio (Configurações → Canal → Configurações avançadas): marcar "Não, este canal não é
   para crianças" em todos os 6 canais (GTA 6 é +18). Ver B6.
5. Decidir se liga a legenda por API (`ligado=True`): 400 unidades por vídeo = 25 vídeos/dia esgotam a cota sozinhos.

## 7. Pendências para o Diretor

Texto pronto para uma rotina (ou SKILL) em `.claude\` — "conferir agenda do YouTube" (substitui o Chrome no Studio):

```
Rotina: youtube_conferir_agenda  (todo dia 08:40 e 20:40, Brasília)
1. Ler os publicar.json dos itens com youtube.status em ("agendado","publicado") dos últimos 3 dias.
2. Montar esperado = {id: {"status_pedido": "agendado"|"publico", "publicar_em": post.json.data}} e chamar
   publicar_extra.youtube_extra.conferir_lote(cliente, token_de(canal), esperado, registrar=contador.registrar)
   (1 unidade a cada 50 vídeos).
3. Se resumo["travado_privado"] > 0 ou "rejeitado"/"falhou": mandar no WhatsApp do grupo o diagnóstico de cada um
   (texto já em português) e marcar youtube.status = "pendente_chrome" no publicar.json (o PC solta pelo Studio).
4. Gravar contador.resumo() em app\logs\youtube_cota_AAAA-MM-DD.json; se "avisar" for true, avisar no WhatsApp.
Nunca: imprimir token, rodar entre 18h e 22h30 sem ser P0, chamar enviar_legenda sem ligado=True aprovado.
```

## 8. Decisões em aberto / conflitos

- `youtube_extra.py` já foi parar no commit `ef9252e` da sessão principal (junto com a troca de `contas.json`); o teste e o
  LEIA não. Se a sessão principal preferir um commit só da tarefa B, é só mover.
- **`conftest.py` de `publicar_extra/testes`**: não criei (a tarefa C roda em paralelo na mesma pasta). Sugestão para a
  sessão principal: criar um igual ao de `metricas/testes` (sys.path + `raizes_temporarias`) e tirar as 4 linhas de
  `sys.path` do topo do meu teste — funciona dos dois jeitos.
- `rejectionReason: "size"` não está na lista oficial de 01/10/2026 (claim, copyright, duplicate, inappropriate, legal,
  length, termsOfUse, trademark, uploaderAccountClosed, uploaderAccountSuspended); deixei na tabela porque a tarefa pede.
- O PC fala em "limite de 100 envios/24 h"; o balde oficial **zera à meia-noite da Califórnia** (04h/05h de Brasília),
  não é janela móvel de 24 h — ver B6 (cota). Decidir se o contador do PC muda.
- `uploadLimitExceeded` é **400 badRequest** ("The user has exceeded the number of videos they may upload" — limite do
  canal/usuário), diferente do 403 `quotaExceeded` do balde da API. Os dois viram mensagens distintas aqui; vale o PC
  separar também (hoje não sei como ele trata).
- Vídeo `unlisted` sai como `ok` com aviso (ver suposições). Se o Antônio quiser que conte como problema, vira 1 linha.

## 9. B6 — Revisão crítica do que o PC já faz (texto, sem código)

Páginas lidas em **01/10/2026** (curl, só leitura; "Last updated" da própria página entre parênteses):
Q = https://developers.google.com/youtube/v3/determine_quota_cost (2026-09-15) ·
VI = https://developers.google.com/youtube/v3/docs/videos/insert (2026-09-14) ·
VU = https://developers.google.com/youtube/v3/docs/videos/update (2026-09-14) ·
VR = https://developers.google.com/youtube/v3/docs/videos (2026-09-16) ·
PI = https://developers.google.com/youtube/v3/docs/playlists/insert · PII = …/playlistItems/insert · PL = …/playlists/list ·
CI = https://developers.google.com/youtube/v3/docs/captions/insert (todas 2026-09-14) ·
AU = https://developers.google.com/youtube/v3/guides/quota_and_compliance_audits (2026-09-14) ·
H15 = https://support.google.com/youtube/answer/71673 (Central de Ajuda, sem data na página).

1. **Projeto sem auditoria → vídeo preso como privado (a causa do "travado").** VI e VR dizem, literalmente: *"All videos
   uploaded via the videos.insert endpoint from unverified API projects created after 28 July 2020 will be restricted to
   private viewing mode. To lift this restriction, each API project must undergo an audit"*. Ou seja: não é bug do PC, é
   regra; `publishAt` não vale enquanto isso. Risco: o PC "agenda" 20 vídeos, todos ficam privados e ninguém vê até
   alguém abrir o Studio. O `conferir_lote` (B3) é o alarme; recomendo rodar 2× ao dia (seção 7). AU só descreve o
   formulário ("Audit and Quota Extension Form") — a mesma auditoria serve para destravar e para pedir mais cota.

2. **Cota.** Q: *"default quota allocation of 100 search.list calls, 100 videos.insert calls, and 10,000 units per day
   combined for all other endpoints"*; *"Daily quotas reset at midnight Pacific Time (PT)"*; *"All API requests, including
   invalid requests, incur a quota cost of at least one point"*; páginas extras de um `list` custam de novo. VI: *"100 calls
   per day. A call to this method has a quota cost of 1 unit in the Video Uploads quota bucket"*. Confirmado hoje (B5):
   videos.list 1, channels.list 1, playlists.list 1 (PL), playlistItems.list 1, thumbnails.set 50, videos.update 50 (VU),
   playlists.insert 50 (PI), playlistItems.insert 50 (PII), captions.insert 400 (CI; captions.list 50, captions.update 450).
   Riscos para o PC: (a) o "limite de 100 envios/24 h" do PC é janela móvel, o Google zera **à meia-noite da Califórnia**
   (04h ou 05h de Brasília) — o PC pode recusar envio que já seria permitido, ou tentar 100 de manhã e 100 de noite e
   tomar 403; (b) `uploadLimitExceeded` (VI: 400, "The user has exceeded the number of videos they may upload") é limite
   do canal, não da API — mensagem diferente de `quotaExceeded`; (c) miniatura (50) + playlist (51) + legenda (400) +
   correção (51) por vídeo = ~550 unidades: 18 vídeos/dia esgotam as 10.000 se tudo estiver ligado; (d) erro inválido
   também custa 1 — laço de retry sem pausa queima cota.

3. **`publishAt` e privacidade.** VR (`status.publishAt`): *"It can be set only if the privacy status of the video is
   private"*; *"If you set this property's value when calling the videos.update method, you must also set the
   status.privacyStatus property value to private even if the video is already private"*; *"can only be set if the
   video's privacy status is private and the video has never been published"*; *"If your request schedules a video to be
   published at some time in the past, the video will be published right away"*. Riscos: (a) relógio do PC adiantado/UTC
   errado → agenda no passado → **publica na hora** (B2 recusa horário passado antes de chamar); (b) vídeo que já foi
   público uma vez nunca mais agenda; (c) **granularidade/atraso**: a página só diz ISO 8601 — **não confirmei** em página
   oficial se o YouTube arredonda para o minuto nem o atraso de alguns minutos que o Antônio vê no Studio; tratar como
   "aproximado". VU: *"this method will override the existing values for all of the mutable properties that are contained
   in any parts that the parameter value specifies"* e *"if your request does not specify a value for a property that
   already has a value, the property's existing value will be deleted"* → qualquer `videos.update` do PC que mande só
   `title` **apaga tags, categoria, descrição, selfDeclaredMadeForKids e containsSyntheticMedia**. O B2 manda tudo.

4. **`selfDeclaredMadeForKids` (COPPA).** VR: *"In a videos.insert or videos.update request, this property allows the
   channel owner to designate the video as being child-directed"*; `status.madeForKids` *"contains the current 'made for
   kids' status of the video. For example, the status might be determined based on the value of the
   selfDeclaredMadeForKids property"*. Risco: se o PC **não manda** o campo, quem decide é a configuração do canal ou a
   classificação automática do YouTube (vídeo "para crianças" perde comentários, notificações, tela final e anúncios
   personalizados). §3.3 não diz que o PC declara. Recomendo mandar `selfDeclaredMadeForKids: false` em todo
   `videos.insert` e marcar o canal como "não é para crianças" no Studio. A parte legal (COPPA/FTC) não está em página da
   API — **não confirmada** aqui, só o campo.

5. **`containsSyntheticMedia`.** VR confirma que a API aceita: *"In a videos.insert or videos.update request, this property
   allows the channel owner to disclose that a video contains realistic Altered or Synthetic (A/S) content"*; exemplos:
   *"Make a real person appear to say or do something they didn't actually say or do"*, *"Alter footage of a real event or
   place"*, *"Generate a realistic-looking scene that did not actually occur"*. O PC marca `true` para dublado — certo
   (voz sintética falando pelo streamer cai no 1º exemplo). Riscos: (a) corte normal com narração HP não precisa; marcar
   `true` à toa põe o rótulo "conteúdo alterado" no vídeo; (b) `videos.update` sem o campo **apaga** a declaração (item 3);
   (c) a regra de não clonar voz (contexto, regra 6) continua valendo — declarar não autoriza clonar.

6. **Vídeo > 15 min sem verificação por telefone.** H15: *"By default, you can upload videos that are up to 15 minutes
   long. Verified accounts can upload videos longer than 15 minutes"*; verificação por SMS ou ligação; *"After you verify
   your account, you'll need to upload your video again"*; máximo 256 GB ou 12 h. Na API isso aparece como
   `uploadStatus: rejected` + `rejectionReason: length` (VR). Risco: o `videos.insert` responde 200, o PC marca "enviado",
   e só o `conferir_lote` pega a rejeição. Os cortes HP têm ≤ 60 s, então só pega compilado/vídeo longo.

7. **Shorts.** Nenhuma das páginas da API fala de Shorts; **não confirmei** em página oficial a regra "vertical ≤ 3 min vira
   Short automaticamente" nem se `#Shorts` no título ainda é necessário (a Central de Ajuda não coube nos 10 fetches). O
   que o repositório assume: `metricas/youtube.py` usa `LIMITE_SHORTS_SEG = 180`. Riscos: (a) a API **não tem campo** para
   dizer "é Short" — é o YouTube que decide pela proporção e duração; um corte de 3:05 vertical vira vídeo comum feio;
   (b) link: Short abre em `youtube.com/shorts/<id>` e vídeo comum em `watch?v=`; o PC grava qual no `publicar.json`?
   (c) miniatura por `thumbnails.set` em Short: o Studio não deixa escolher miniatura de Short no computador — **não
   confirmado** se a API aplica.

8. **Outros riscos que vi.** (a) `videos.insert` com `tags` vazia como string → 400 (comentário no exemplo em Go de VI:
   *"The API returns a 400 Bad Request response if tags is an empty string"*); (b) VR: título ≤ 100 e descrição ≤ 5.000
   **bytes** (acento/emoji contam 2–4), ambos sem `<` `>`; tags ≤ 500 **contando vírgulas e aspas** — a legenda com emoji
   do §4.5 (`🏁`, `🎥`) pesa 4 bytes cada; (c) VR: *"For URLs in the description to be rendered as clickable links … the
   channel must meet platform-level requirements, such as channel verification or having Advanced Features enabled"* —
   o link do crédito pode sair sem clique; (d) CI: `captionExists` (409) se repetir idioma+nome; `name` ≤ 150; o parâmetro
   `sync` está *deprecated*; (e) `playlistItems.insert`: `playlistContainsMaximumNumberOfVideos` (403) — playlist "GTA 6"
   cresce sem limite se for uma só; (f) VR não diz que `publishAt` aceita fração de segundo — mandei sem fração.

**Marcado como não confirmado nesta tarefa:** granularidade/atraso do `publishAt`; regras de Shorts (3 min, `#Shorts`,
miniatura); lado legal do COPPA; escopos exigidos por método (lista não copiada); verificação por telefone para miniatura
personalizada.
