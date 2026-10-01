# Facebook: agenda da Página e comentários (publicar_extra)

Três módulos novos em `app\hp_studio_nuvem\publicar_extra\`, para o que o PC ainda não fazia na Página
do Facebook. Postar (foto, carrossel, reel, story, texto) continua sendo do `hp_studio\publicar\facebook.py`.

- `facebook_extra.py` — agenda da Página pela API (listar, cancelar, reagendar, conferir contra o
  `agendados.json` do canal) e a tradução de qualquer erro da Meta para português (`erro_graph`).
- `comentarios.py` — ler, classificar (sem IA), propor e, só quando ligado, curtir/responder comentários.
- `lexico_comentarios.json` — as listas de palavras (ofensivos, spam, pergunta, elogio...). **É dado, não código:
  o Antônio edita no Bloco de Notas.** Entrada na lista `ofensivos` = o comentário fica sem curtida e sem resposta.
- `comentarios_ig_threads.py` — a mesma regra para Instagram e Threads (responder e ocultar; essas APIs não curtem).

## Instalação

Nada a instalar: só Python 3.11/3.12 e o `hpbase`. Nenhum módulo lê token nem faz rede sozinho: o PC passa o
`cliente` (o `hp_studio\publicar\http` do PC) e o `token_de(canal)`. Nos testes entra o `ClienteFalso`.

## Agenda da Página (C1)

```python
from publicar_extra import facebook_extra as fb
itens = fb.listar_agendados(cliente, token, pagina_id)          # [{id, tipo, quando, texto, link, bruto}]
rel = fb.comparar_com_agendados_json(itens, "G:\\Meu Drive\\Hypado\\07 Canais\\Futebol\\agendados.json")
print(rel["resumo"])        # "3 ok, 1 buraco(s), 0 duplicado(s), 1 hora(s) errada(s), 0 sobra(s) na Página."
fb.cancelar_agendado(cliente, token, "123_456")
fb.reagendar(cliente, token, "123_456", "2026-10-05 18:30")      # Brasília; reel: tipo="reel"
```

- `quando` sai sempre em hora de Brasília `AAAA-MM-DD HH:MM`; a Meta recebe epoch UTC.
- Janela da Meta: de 10 minutos a 75 dias a partir de agora (reel: até 29 dias). Fora disso a função nem
  chama a API e explica em português.
- **Reels agendados**: a documentação oficial não diz como listá-los; o módulo tenta `GET /{page}/video_reels`
  e marca cada reel com `"confirmar": True`. Se a Página mostrar reel agendado no Business Suite que não
  aparece aqui, é esse o motivo (ver `docs/rodada2/C.md`).
- O relatório de `comparar_com_agendados_json`: `buracos` (no JSON e não na Página), `duplicados` (mesmo texto
  e hora 2x na Página), `hora_errada` (diferença maior que 5 min), `sobras` (na Página e não no JSON), `ok`,
  `ignorados` (itens do JSON que não são do Facebook).

## Comentários (C2)

Regra do Antônio (30/09): *antes de responder, veja se precisaria de resposta ou se só a curtida serve;
se for ofensivo, não faça nada.* O módulo segue isso em 3 classes: `responder` (pergunta, dúvida, pedido,
crítica que vale conversa), `curtir` (elogio, emoji, marcação de amigo, e tudo que ficou na dúvida) e
`ignorar` (ofensivo, spam/link, sarcasmo).

```python
from publicar_extra import comentarios as co
cfg = co.ConfigComentarios()                 # 25 respostas por passada, 1 por pessoa, 20 s entre elas, enviar=False
lidos = co.ler_comentarios(cliente, token, post_id, desde=ontem)
estado = co.EstadoComentarios(pasta_app() / "publicar" / "comentarios_estado.json")
acoes = co.planejar(lidos, estado.conjunto_tratados(), cfg, posts_nossos={post_id}, redator=minha_funcao)
r = co.executar(cliente, token, acoes, cfg, estado)                     # SIMULADO: nada vai para a rede
r = co.executar(cliente, token, acoes, cfg, estado, enviar=True)        # o PC liga; grava o estado
```

- `planejar` só monta a proposta. Resposta sem texto fica como `"a redigir"` e `executar` pula; o texto vem
  do `redator` que o PC injeta (Claude escreve, o módulo não).
- `executar` nunca curte nem responde duas vezes: o `comentarios_estado.json` guarda o que já foi feito
  (por comentário e por pessoa) e é gravado atômico depois de cada envio.
- Para em token vencido, permissão faltando, bloqueio (368) ou limite de chamadas, e diz o que fazer.
- `ocultar()` existe, mas nenhuma regra usa: ofensivo = não fazer nada.

## Permissões que o token da Página precisa (o que o Antônio autoriza no app "HP Publicador")

| Para | Permissão | Se faltar, a mensagem diz |
|---|---|---|
| ler a agenda e os comentários | `pages_read_engagement` (+ `pages_read_user_content` para ver o texto de quem comentou) | "Falta a permissão pages_read_engagement..." |
| curtir, responder, ocultar | `pages_manage_engagement` (quem gera o token precisa ser moderador da Página) | "Falta a permissão pages_manage_engagement..." |
| cancelar ou reagendar post | `pages_manage_posts` | "Falta a permissão pages_manage_posts..." |
| Instagram (login do Instagram) | `instagram_business_basic` + `instagram_business_manage_comments` | idem |
| Threads | `threads_read_replies` + `threads_manage_replies` (o app já tem) | idem |

Passo a passo se faltar: developers.facebook.com → app "HP Publicador" → Casos de uso → adicionar a permissão
→ gerar de novo o token da Página com `hp publicar facebook-token` (o token velho não ganha permissão nova).

## Testes

```
cd app\hp_studio_nuvem
python -m pytest -q -p no:cacheprovider publicar_extra\testes\test_facebook_extra.py publicar_extra\testes\test_comentarios.py
```

O banco `testes\comentarios_banco.json` tem 114 comentários inventados com a classe esperada; para ajustar o
comportamento, mude o `lexico_comentarios.json` e rode os testes: a falha nomeia o comentário.
