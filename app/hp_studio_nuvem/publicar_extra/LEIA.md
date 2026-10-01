# publicar_extra — o que falta no YouTube e no Facebook além de postar (rodada 2)

O **envio** (YouTube `videos.insert`; Facebook foto, carrossel, reel, story, texto) já existe no PC em
`hp_studio\publicar\` e **não é refeito aqui**. Este pacote entrega só as lacunas, pronto para o PC
plugar quando quiser (tudo começa em simulação: nada envia sem o PC passar `enviar=True`/`ligado=True`).

| Arquivo | O que faz | Leia |
|---|---|---|
| `contrato_pc.py` | cópia mínima do contrato com o PC: `Resposta`, `ErroRede`, `entrada()`, `mascarar()` e o `ClienteFalso` dos testes. **No PC, importar de `hp_studio.publicar.http`** (trocar só neste arquivo). | — |
| `youtube_extra.py` | playlists sem duplicar, corrigir vídeo já enviado (snippet completo, `publishAt` em UTC), conferência em lote ("travado como privado"), legenda SRT (desligada: 400 unidades), registro de cota (avisa a 80 %), erros em português | `LEIA_youtube.md` |
| `facebook_extra.py` | agenda da Página por API (listar, cancelar, reagendar com a janela da Meta, comparar com o `agendados.json`), `erro_graph` com os códigos de reel | `LEIA_facebook.md` |
| `comentarios.py` + `lexico_comentarios.json` | comentários da Página: ler, classificar (`responder` / `curtir` / `ignorar`, sem IA, léxico que o Antônio revisa), planejar e executar (padrão: só propõe) | `LEIA_facebook.md` |
| `comentarios_ig_threads.py` | o mesmo para Instagram (`/comments`, `/replies`, ocultar) e Threads (`/replies`, `reply_to_id`) | `LEIA_facebook.md` |

Instalação: nada além de `pillow`/`numpy`/`pytest` (já no PC). Testes:
`cd "G:\Meu Drive\Hypado\06 Projeto\app\hp_studio_nuvem"; & $PY -m pytest -q publicar_extra` → 324 passed.

Regras que valem para todo o pacote: o token chega por `token_de(canal)` do PC e vai no cabeçalho
`Authorization: Bearer …` (YouTube) ou no `access_token` da consulta/form (Graph) — nunca na URL, no log,
na exceção nem em arquivo (há teste para isso em cada módulo); `cliente.pedir(...)` é injetado; nenhum teste faz rede.
