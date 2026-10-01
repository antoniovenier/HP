# fila_api_pc — a fila real da API do Instagram e do Threads

`hpbase\fila_api_pc.py` fala o formato REAL da fila que o `scripts\publicador_meta.py`
(em produção) lê em `H:\HypadoLocal\fila_api\`. Nada aqui publica: o módulo monta,
valida, grava e lê os itens, e dá um adaptador para chamar o `publicar_item` real
com segurança. Instalação: nenhuma (só Python 3.11+; está dentro do `hpbase`).

## O que cada função faz

| Função | Para quê |
|---|---|
| `handle(item)` | handle da conta (`hp.futebol`) a partir de `conta` ou, se faltar, de `canal` (`futebol` → `hp.futebol`, `gta` → `hpgta6`) |
| `chave_token(item)` | `IG_<handle>` (instagram) ou `TH_<handle>` (threads) — o nome da linha em `meta_tokens.txt` |
| `token_do_item(item, ler_token)` | devolve o token só a quem chamou, pela função injetada; nunca imprime; sem token → `SegredoAusente` só com o nome da chave |
| `leitor_de_tokens()` | a função `ler(chave)` de produção: lê `meta_tokens.txt` como o publicador (aceita `@`, aspas, `#`) |
| `id_da_conta(chave, meta_json)` / `ler_meta()` | id da conta em `meta_tokens_meta.json` (só leitura; o `carregar_meta` do publicador regrava o arquivo, por isso não é usado) |
| `inicio(item)` | `datetime` de `quando` (`"AAAA-MM-DD HH:MM"`, aceita `T`, hora de Brasília, sem fuso) |
| `montar_item(conta, rede, tipo, arquivos, legenda, quando, canal=, titulo=, capa=, depende_de=, id_=, grupo_whatsapp=, slug_=, lote=, n=, pasta_fila=, existe=)` | o dict de 4.1 validado com as regras e mensagens do `_validar` do publicador; id padrão pela convenção (`gta_<data>_<ig/th>_<tipo>_<HHMM>`, `<canal>_<data>_<HHMM>_<slug>_<ig/th>_<tipo>`) |
| `gravar_item(item, pasta_fila, subpasta=None)` | grava `<id>.json` de forma atômica |
| `ler_confirmacao(id_, pasta_fila)` | `{"estado": "no_ar" / "erro" / "pendente" / "desconhecido", "link", "erro", "publicado_em", "media_id", "pasta"}` olhando raiz, `feitos\`, `erros\`, `story_clicavel\`, `reserva_largada\`, `removidos\<motivo>\` |
| `post_que_falta(item, pasta_fila)` | regra do story irmão (`<base>_ig_story` espera `<base>_ig_carrossel/reel/feed` em `feitos\`) e de `depende_de` |
| `chegou_a_hora / esta_vencido / mensagem_vencido` | as regras de hora do `rodar()` (tolerância 2 min; vencido há mais de 12 h vai para `erros\`) |
| `ler_limite_24h / publicacoes_24h / no_limite` | `limite_24h.json` (100 posts por conta no IG, 250 no Threads, por 24 h) |
| `ler_log(pasta ou arquivo)` | `publicador.log` → eventos `no_ar`, `publicando`, `invalido`, `hospedado` |
| `publicador_adaptado(publicar_item_real, ler_tokens=, meta=, simular=False)` | `publicar(item) -> {media_id, permalink, publicado_em}`; `"limite"` → `LimiteDaConta`; `ErroAPI` → `ErroPublicador` (sem token); em `simular` devolve um resultado falso **sem chamar** o publicador (no PC o `simular` dele ainda sobe o arquivo para a hospedagem) |

## Regras que ele aplica (as mesmas do publicador)

- `rede` só `instagram` ou `threads` → senão "rede tem que ser instagram ou threads (Facebook continua pelo Business Suite)".
- `quando` obrigatório; `conta` tem que ser uma das 6 marcas ("conta desconhecida: X").
- arquivo relativo resolve contra a pasta da fila e tem que existir ("arquivo não existe: <caminho>"); a `capa` também.
- feed = 1 imagem; reel = 1 vídeo; story = 1 arquivo; carrossel 2 a 10 (IG) ou 2 a 20 (Threads); texto só no Threads, sem arquivo e com legenda.
- legenda ≤ 2200 no Instagram; texto ≤ 500 no Threads.

## O que ainda é suposição (confirmar no `publicador_meta.py` do PC)

- Texto exato depois de "feed = exatamente 1 imagem" (o enunciado cortou com "…"): aqui é
  "(vídeo vai como reel)". Trocar em `_validar_tipo`.
- "post de texto só no Threads", "post de texto não leva arquivo (veio N)" e "tipo tem que ser feed, carrossel, reel, story ou texto (veio X)"
  são mensagens da nuvem (o argparse do PC impede esses casos antes). Trocar em `_validar_tipo`.
- Item em `removidos\<motivo>\` volta como `estado: "erro"` ("tirado da fila à mão"); se o PC preferir "pendente", trocar em `ler_confirmacao`.
- O `slug` do id dos canais vem do `titulo` quando não é informado (no PC quem escolhe o slug é o script que enfileira).

## Como usar nos testes

```python
from hpbase import fila_api_pc as fa
item = fa.montar_item("hp.futebol", "instagram", "feed", ["H:\\x\\frase_feed.jpg"], "legenda",
                      "2026-09-30 23:20", canal="futebol", existe=lambda p: True)
fa.gravar_item(item, tmp_path)                 # a fila temporária
fa.ler_confirmacao(item["id"], tmp_path)       # {"estado": "pendente", ...}
```

Os testes ficam em `hpbase\testes\test_fila_api_pc.py` e usam as fixtures reais de
`tests\fixtures\pc_real\fila_api_*.json`.
