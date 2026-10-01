# PENDENCIAS_PARA_O_DIRETOR.md — rodada 2 (01/10/2026)

Tudo que mexe em `.claude\` (CLAUDE.md da empresa, rotinas, SKILLs). A nuvem **não edita** essa pasta:
cada item traz o arquivo onde o Diretor cola e o trecho pronto. Ordem: do que destrava mais para o que é
só ajuste de texto. (Os itens das tarefas B, C e E vêm depois dos de A, D e F.)

## 1. `CLAUDE.md` da empresa — 3 linhas de regra que o código da rodada 2 já aplica

Colar na seção de regras de conteúdo/operacão (perto de "trabalho pesado 1 por vez"):

```
- P0 da esteira (gol, placar, resultado, bombástica, lançamento) roda também das 18h às 22h30,
  1 pesado por vez (pesado.lock). P1/P2 continuam esperando 22h30. (Decisão do Antônio, 30/09.)
- Voz sintética (Piper, "dublado por HP"): permitida no GTA (criador gringo "idioma": "en" do
  config.json sai dublado) e em Filmes, Receitas, Carros e Destinos; NUNCA no Futebol.
- WhatsApp: resumo do dia, aviso "no ar", resumo de sábado E avisos ao Antônio (tipo "aviso":
  algo precisa dele — senha, login, decisão, falha). Toda mensagem começa com *Claude - *;
  de madrugada (0h–7h30) nada sai: fica na fila com enviar_apos.
```

Por quê: o item 1 é a decisão de 30/09 que a rodada 1 já pedia; o item 2 é o que `esteira/constantes.py::CANAIS_COM_VOZ`
passou a aceitar (o `config.json` real do GTA tem `dublagem` e 19 criadores `en`); o item 3 é o que
`whatsapp_local/config.py::TIPOS_PERMITIDOS` aceita (a fila real `temp\whatsapp_fila.json` tem avisos).

## 2. SKILL `hypado-estaticos` — gravar `interativo.pergunta_curta` (tarefa A4)

Arquivo: `.claude\skills\hypado-estaticos\SKILL.md`, na parte que escreve o story interativo do lote
`lotes\AAAA-MM-DD_estaticos.json`. Colar:

```
### Story interativo (chave "interativo" do lote): grave DUAS perguntas

Além de "pergunta" (a pergunta completa, com contexto, como hoje), grave SEMPRE
"pergunta_curta": a pergunta que vai na figurinha de enquete do Instagram.

Regras da "pergunta_curta":
- Até 25 caracteres, contando espaço, acento e pontuação (conte antes de gravar).
- Uma frase só, terminada em "?", que fecha sozinha: dá para entender sem ler a arte nem a
  pergunta completa. Ex.: "O que você faz?" (15), "Vai jogar no dia 1?" (19), "Vice City ou Leonida?" (21).
- Sem emoji, sem "#", sem vocativo ("galera,", "gente,") nem introdução ("me conta:", "e aí,").
- Não terminar em vírgula, dois-pontos ou reticências; nunca cortar palavra no meio.
- "opcoes": 2 a 4, cada uma com até 25 caracteres, sem emoji e sem repetir.

Exemplo:
  "interativo": {
    "pergunta": "Furacão chegando em Leonida. O que você faz?",
    "pergunta_curta": "O que você faz?",
    "opcoes": ["Vou ver de perto", "Fujo pro outro lado"],
    ...
  }

Antes de fechar o lote, rode: python scripts\story_post_lote.py lotes\AAAA-MM-DD_estaticos.json
Tem que terminar com código 0 e mostrar a pergunta escolhida. Se aparecer "NÃO DÁ", arrume
"pergunta_curta"/"opcoes" e rode de novo. Sem "pergunta_curta" o story_post tenta encurtar a
pergunta completa pela última oração com "?"; se nada couber em 25, o story NÃO sai.
```

## 3. SKILL (ou rotina) do story de divulgação — arte pelo `story_artes.py` (tarefa D)

Arquivo: a SKILL que hoje manda o `story_post` subir story de post (ou o `LEIA_story_post.md`, se a
regra viver lá). Colar:

```
Story de divulgação: antes de o story_post subir um story, gere a arte com
`python scripts\story_artes.py render <spec.json>` (spec na LEIA_story_artes.md; 3 modelos:
chamada, maissobre, interacao; 6 canais). Use o `<nome>_zonas.json` que sai ao lado do JPG para
posicionar a figurinha de link (chave "link"/"link_fracao") e a de enquete ("enquete"/"enquete_fracao").
Se o comando devolver código 1, leia a mensagem (em português) e encurte o texto indicado; nunca
ignore o erro para não sair texto cortado. Sem emoji na arte (o gerador tira sozinho).
```

## 4. Rotina nova `hp-radar-fontes` (mensal) e ajuste no SKILL `hp-carros-lancamentos` (tarefa F)

Arquivo: `.claude\` (rotina nova, mensal, dia 1, 7h). Colar:

```
Rotina hp-radar-fontes (mensal, dia 1, 7h), na pasta G:\Meu Drive\Hypado\06 Projeto:
  python radar_fontes\verificar_fontes.py verificar radar_fontes\futebol_fontes_novas.json --gravar
  python radar_fontes\verificar_fontes.py verificar radar_fontes\filmes_fontes_novas.json --gravar
  python radar_fontes\verificar_fontes.py verificar radar_fontes\carros_fontes_novas.json --gravar
  python radar_fontes\verificar_fontes.py verificar radar_fontes\gta_fontes_novas.json --gravar
  (se der erro de certificado: --curl antes de "verificar")
Saída 1 = alguma fonte caiu: abra o JSON, veja "descartadas" e o motivo, e tire a fonte do
07 Canais\radar\<canal>.json ou ache o @handle/feed novo no site oficial.
A cada trimestre, releia radar_fontes\<canal>_candidatos.txt e radar_fontes\RELATORIO_FONTES.md
(seção "O que o PC deve tentar de novo"): salas de imprensa e sites de clube trocam de plataforma.
Nunca inclua Flow Games nem invente id: sem prova, não entra.
```

Arquivo: `.claude\skills\hp-carros-lancamentos\SKILL.md` (endereços conferidos em 01/10/2026). Colar no fim da lista de salas de imprensa:

```
Salas de imprensa conferidas em 01/10/2026:
- Ferrari: https://www.ferrari.com/en-US/media-centre (o /en-EN/media responde 404)
- Hyundai Brasil: https://www.hyundai.com.br/imprensa -> https://hyundai-csa-news.com/ (feed: /feed/)
- Toyota Brasil: https://www.toyotacomunica.com.br/ (feed: /feed/)
- BMW Brasil: https://www.press.bmwgroup.com/brazil (feed: /pressclub/p/br/rss.html?locale=pt&outputChannelId=43)
- McLaren: cars.mclaren.press responde 404 (procurar o endereço novo)
- Nissan: feed global https://global.nissannews.com/en/rss (nissannews.com/pt-BR cai na página global)
Feeds e canais novos prontos: radar_fontes\carros_fontes_novas.json (6 rss + 21 youtube) e os outros 3 canais
(futebol 7 + 13, filmes 8 + 18, gta 1 + 1). Antes de mesclar no 07 Canais\radar\<canal>.json, conferir as
4 entradas marcadas "ja_existe" (CBF @brasil, CONMEBOL Libertadores BR, Paramount Brasil, Rockstar Games).
```

## 5. Rotina `youtube_conferir_agenda` (tarefa B) — substitui o "conferir no YouTube Studio pelo Chrome"

Arquivo: `.claude\` (rotina, todo dia 08:40 e 20:40 Brasília). Só vale quando o Google aprovar a auditoria da API;
até lá o `conferir_lote` é justamente o alarme do "travado como privado". Colar:

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
Lembrete: o balde de 100 envios/dia do YouTube zera à MEIA-NOITE DA CALIFÓRNIA (04h/05h de Brasília), não é
janela móvel de 24 h; e todo videos.update sem o snippet completo APAGA tags, categoria, descrição,
selfDeclaredMadeForKids e containsSyntheticMedia (o youtube_extra.atualizar_video manda tudo).
```

## 6. Rotina `conferente-de-agenda` por API e rotina `comentarios-pagina` (tarefa C)

Arquivo: a rotina `conferente-de-agenda` em `.claude\` (hoje abre o Planner do Business Suite pelo Chrome). Colar no lugar:

```
# conferente-de-agenda (API)
Para cada canal com Página no Facebook (facebook_paginas.json): token = token_de(canal);
itens = facebook_extra.listar_agendados(cliente, token, pagina_id, avisos=avisos);
rel = facebook_extra.comparar_com_agendados_json(itens, <07 Canais\<Pasta>\agendados.json ou 06 Projeto\agendados.json>).
Relate rel["resumo"] e liste buracos, duplicados e hora_errada com id, hora do JSON e hora da Página.
Reagendar/cancelar só com aprovação do Antônio (facebook_extra.reagendar / cancelar_agendado).
Reels com "confirmar": True precisam de conferência manual no Planner até o Antônio confirmar o endpoint
(a documentação da Meta não diz como listar reel agendado; ver docs/rodada2/C.md, seção 1.1).
```

Arquivo: rotina NOVA `comentarios-pagina` em `.claude\` (proposta, nunca envio sem aprovação). Colar:

```
# comentarios-pagina (proposta, nunca envio)
Regra do Antônio (30/09, 11:52, vale para todas as contas HP): "antes de responder, veja se precisaria de
resposta, ou somente a curtida sirva; se for algo ofensivo, não faça nada de curtida nem nada".
Para cada post nosso das últimas 48 h: lidos = comentarios.ler_comentarios(cliente, token, post_id, desde=48h);
estado = comentarios.EstadoComentarios(H:\HypadoLocal\app\publicar\comentarios_estado_<canal>.json);
acoes = comentarios.planejar(lidos, estado.conjunto_tratados(), ConfigComentarios(), posts_nossos, redator=<Claude redige>).
Mostre a proposta (acao, texto, motivo) e só rode executar(..., enviar=True) com aprovação. Ofensivo: nada.
Limites (ConfigComentarios): 1 resposta por pessoa, 25 respostas e 60 curtidas por passada, 20 s entre respostas,
só em post nosso. O que é ofensivo/spam/sarcasmo está em publicar_extra\lexico_comentarios.json: o Antônio revisa.
Instagram e Threads: comentarios_ig_threads (o Instagram NÃO curte comentário por API; só responde/oculta).
```

## 7. SKILL curta "story no celular" (tarefa E)

Arquivo: a SKILL/rotina que manda o `story_post` subir stories (ou nova, `.claude\skills\hp-story-celular\SKILL.md`). Colar:

```
Story no celular (tarefa E, rodada 2): nunca use coordenada fixa; nunca digite senha/PIN; nunca toque em
Entrar/Aceitar/Permitir. Antes de rodar de verdade, SEMPRE veja o roteiro:
  python scripts\story_fluxos.py pedido H:\HypadoLocal\emulador\fila_story\<post_id>.json --simular
Depois: o mesmo comando sem --simular (--emulador ou --celular). Códigos: 2 = bloqueado (trava, intervalo
de 3 min, já feito, 3 falhas) → tente na próxima rodada; 3 = aviso da Meta/login → PARADO_AVISO_META.json,
só o Antônio apaga; 4 = o Antônio precisa agir no aparelho. Story "a conferir" = olhe no Instagram, não
repita. Para confirmar os botões que ainda são palpite: python scripts\story_coletar_telas.py --emulador
(só lê a tela; quem navega é a pessoa). Acento no celular: o padrão troca ("Você" → "Voce") e avisa no log;
o modo de acento real fica DESLIGADO (instalar teclado é decisão do Antônio).
```

## 8. Ordem sugerida para o Diretor

1. Item 1 (CLAUDE.md): 3 linhas, sem risco.
2. Item 2 (hypado-estaticos): é o que faz a enquete das 16h sair com a pergunta certa sem cortar no escuro.
3. Item 4 (radar): rodar os 4 comandos uma vez no PC (promove `pagina_canal` → `feed`) e mesclar nos `07 Canais\radar\*.json`.
4. Itens 6 e 7 (agenda por API, comentários, story no celular): só depois das permissões/coleta de telas que o Antônio faz (lista no `ENTREGA.md`, seção "Depende do Antônio").
5. Item 5 (YouTube): só depois da auditoria do Google.
