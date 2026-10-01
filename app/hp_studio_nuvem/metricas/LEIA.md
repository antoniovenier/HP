# metricas — etapa 6: métricas por API (HP Studio)

Coleta **todo dia às 6h** (e quando você pedir) os números dos 6 perfis
(gta, futebol, filmes, receitas, carros, destinos) no **Instagram, Threads,
Facebook (Páginas) e YouTube**, só pela API oficial. O **TikTok** continua pelo
Chrome: aqui ele só é **importado** de um CSV/JSON (fonte: `manual`).

Grava uma "foto" por dia e um resumo para o painel. Alimenta o manual 11
(Analista de resultados).

## Instalação

1. Copie a pasta `metricas\` para `G:\Meu Drive\Hypado\06 Projeto\app\hp_studio_nuvem\metricas\`
   (do lado da `hpbase\`).
2. `pip install requests` (se já não estiver instalado).
3. Crie/complete os arquivos de segredo (abaixo). **Nunca** cole token em outro lugar.
4. Teste sem chamar nada: `cd "G:\Meu Drive\Hypado\06 Projeto\app\hp_studio_nuvem"` e
   `python -m metricas coletar --simular`. Ele mostra, por conta e rede, se o token e o
   id existem (sem mostrar o valor).

## Segredos (formato REAL do PC — §4.3 da rodada 2; só os nomes, nunca o valor)

Tudo em `H:\HypadoLocal\segredos\`. O app conhece só o **nome** do arquivo e da chave; o valor é
lido na hora da chamada e apagado (`***`) de toda mensagem, log e JSON. Conferir o que existe,
sem mostrar nada: `python -m metricas chaves` (ou `coletar --simular`).

| Rede | Token (arquivo: chave) | Id da conta (não é segredo) | Host / versão |
|---|---|---|---|
| Instagram | `meta_tokens.txt`: `IG_<handle>=` (handle sem `@`, minúsculo, pode ter ponto: `IG_hpgta6`, `IG_hp.futebol`) | `meta_tokens_meta.json` → `contas/IG_<handle>/id` | `graph.instagram.com` / `v21.0` |
| Threads | `meta_tokens.txt`: `TH_<handle>=` | `meta_tokens_meta.json` → `contas/TH_<handle>/id` | `graph.threads.net` / `v1.0` |
| Facebook | `facebook_tokens.txt`: `FB_<canal>=` (`canal` = gta, futebol, filmes, receitas, carros, destinos — **não** é handle) | `facebook_paginas.json` → `<canal>/id` | `graph.facebook.com` / `v26.0` |
| YouTube | `youtube.json` → `oauth/refresh_tokens/<canal>` + `oauth/client_id` + `oauth/client_secret` (ou `api_key`) | `youtube.json` → `canais/<canal>` ou `youtube_canais.json` → `<canal>/id` | `googleapis.com` / `v3` |

- O `handle` vem do `contas.json` (`"usuario"`) ou da tabela `hpbase/fila_api_pc.CANAIS`.
- `meta_tokens.txt` aceita `@` no nome, aspas no valor e linhas `#` (como o `publicador_meta.py`).
- YouTube só coleta com `"autorizado": true` no `contas.json`; senão a rede sai `nao_autorizado`
  sem ler nada (só o GTA tem refresh token no PC).
- **Nomes antigos da rodada 1 continuam valendo, depois dos reais**: `IG_<CONTA>_TOKEN`, `IG_<CONTA>_ID`,
  `TH_...`, `FB_...` no `meta_tokens.txt`; `IG_TOKEN`/`META_TOKEN` (um token para todas); e
  `youtube_tokens.txt` com `YT_API_KEY`, `YT_<CONTA>_CANAL`, `YT_CLIENT_ID`, `YT_CLIENT_SECRET`,
  `YT_<CONTA>_REFRESH_TOKEN`. Nomes diferentes: `"chave_token"` / `"chave_id"` / `"chave_api"` na conta;
  o id também pode ficar no `contas.json` (`"id": "..."`).
- Quem decide a ordem e em que arquivo procurar é `metricas/chaves_pc.py` (`nomes_token`, `nomes_id`,
  `GRUPOS`); `config.Credenciais` só lê o valor. Status quando falta algo: `sem_token` (o nome da chave
  que falta vem em `detalhe`, nunca o valor).

## O arquivo contas.json

O `contas.json` deste pacote é um **exemplo sem segredo** (6 perfis × 5 redes). Para mudar,
copie para `H:\HypadoLocal\metricas\contas.json` e edite lá (ele passa a valer).
Campos úteis: `versao_graph` (padrão `v21.0`), `dias_posts` (7), `limite_posts` (50),
`"ativo": false` para desligar uma rede, `youtube.autorizado` (**false** até a auditoria
da API do YouTube terminar — aí a rede sai `nao_autorizado` sem chamar nada),
`facebook.metricas_post` / `metricas_reel` (nomes das métricas de insights do Facebook,
que a Meta troca com frequência: `{"nome_na_api": "alcance" | "views"}`).

## Comandos (dentro de `...\app\hp_studio_nuvem`)

| Comando | O que faz |
|---|---|
| `python -m metricas coletar` | coleta tudo agora e grava |
| `python -m metricas coletar --conta gta --rede instagram` | só uma conta/rede (mescla na foto do dia) |
| `python -m metricas coletar --simular` | não chama API nem grava; mostra o plano e se os tokens existem |
| `python -m metricas chaves [--json]` | quais chaves existem em `segredos\` por conta e rede (nome, arquivo, id, host, versão; nunca o valor) |
| `python -m metricas resumo [--data 2026-09-30] [--json]` | resumo do dia (seguidores, deltas, status, top 5) |
| `python -m metricas importar-tiktok arquivo.csv [--conta gta] [--data ...]` | importa o TikTok manual |
| `python -m metricas agendar-6h` | **imprime** o comando `schtasks` (pythonw, sem console) para colar; não executa |

## O que sai (em `H:\HypadoLocal\metricas\`)

- `AAAA-MM-DD.json` — foto do dia:
  `{data, coletado_em, versao, contas: {gta: {instagram: {status, seguidores, usuario, posts_total,
  posts: [{id, legenda_inicio, tipo, publicado_em, link, curtidas, comentarios, views, salvamentos,
  compartilhamentos, alcance, taxa_engajamento}], totais: {...}, avisos: [...], coletado_em, fonte}},
  threads: {...}, facebook: {...}, youtube: {...}, tiktok: {fonte: "manual", ...}}}, analise: {...}}`
  - `tipo`: reels, carrossel, imagem, video, story, texto, shorts.
  - `publicado_em` sempre na hora de Brasília.
  - Threads não tem salvamentos/alcance (fica `null`); compartilhamentos = reposts + citações.
  - YouTube: `shorts` = até 3 min (suposição); compartilhamentos só com Analytics autorizado.
- `ultimo.json` — cópia da foto mais recente.
- `metricas_painel.json` — resumo para o painel (abaixo).
- Log em `H:\HypadoLocal\app\logs\metricas_AAAA-MM-DD.log`.

**Status por rede** (uma rede nunca derruba as outras): `ok` · `erro:<mensagem sem token>` ·
`nao_autorizado` (token vencido/sem permissão ou YouTube não autorizado; detalhe em `detalhe`) ·
`sem_token` (falta a chave no arquivo; o nome da chave vem em `detalhe`) ·
`aguardando_importacao` (TikTok antes do CSV). Se uma coleta sob demanda falhar no mesmo
dia, os números bons da manhã ficam e aparece `dados_de` com a hora deles.
Métrica que a API recusa para um tipo de mídia (ex.: `views` num carrossel antigo) é pulada:
o app pede todas, e se vier recusa pede uma a uma e lembra quais não valem para aquele tipo.
Erro 429/5xx/queda de rede: repete 3 vezes (2 s, 10 s, 30 s; respeita `Retry-After`).

## Contas para o Analista (manual 11) — bloco `analise` da foto

Por conta e rede: `seguidores`, `delta_dia` (vs foto de ontem), `delta_7d` (vs foto de 7 dias
atrás), `taxa_engajamento` = (curtidas + comentários + salvamentos + compartilhamentos) ÷ alcance
(só posts com alcance), `views_por_formato` e `views_por_hora` (média de views e nº de posts,
juntando as fotos dos últimos 30 dias; o mesmo post conta uma vez, com o número mais novo).
Delta fica `null` quando falta a foto do dia de comparação.

## Como o `painel_local.py` deve ler (não temos o painel aqui — só o gancho)

```python
from pathlib import Path
import json
ARQ = Path(r"H:\HypadoLocal\metricas\metricas_painel.json")
m = json.loads(ARQ.read_text(encoding="utf-8")) if ARQ.exists() else None
if m:
    # m["gerado_em"] mais velho que 26 h → mostrar "métricas atrasadas"
    for conta, c in m["contas"].items():          # "gta", "futebol", ...
        print(c["nome"], c["seguidores_total"], c["delta_dia_total"])
        for rede, r in c["redes"].items():         # instagram, threads, facebook, youtube, tiktok
            # campos: status, fonte, seguidores, delta_dia, delta_7d, views_24h, posts_24h,
            #         taxa_engajamento (0.052 = 5,2 %), coletado_em
            print(rede, r["status"], r["seguidores"], r["delta_dia"], r["delta_7d"])
        top_conta = c["top_24h"], c["top_7d"]      # até 5 posts da conta
    top_geral = m["top_posts"]["24h"], m["top_posts"]["7d"]   # até 5 posts no geral
    # cada post: id, conta, rede, tipo, legenda_inicio, publicado_em, link, views, curtidas, comentarios
    total = m["totais"]["seguidores"], m["totais"]["delta_dia"]
```

Mostrar `—` para `null`; `status` diferente de `ok` em vermelho com o texto do status.

## Agendar às 6h

Rode `python -m metricas agendar-6h` e cole a linha `schtasks --% ...` no PowerShell. Ela
agenda `pythonw.exe ...\metricas\agendado.py coletar` (sem janela). Coleta é leve (só rede),
não usa o `pesado.lock`.

## Modo sombra (7 dias)

Durante 7 dias deixe a tarefa das 6h rodando em paralelo com a rotina atual do Claude e
compare os números de seguidores e views do `resumo` com o que a rotina reporta. Para não
misturar, dá para gravar em outra pasta: `coletar --saida H:\HypadoLocal\metricas_sombra`.

## Gancho no motor do app

`from metricas import executar` →
`executar({"acao": "coletar"})`, `executar({"acao": "coletar", "conta": "gta", "rede": "instagram"})`,
`executar({"acao": "coletar", "simular": True})`,
`executar({"acao": "importar_tiktok", "arquivo": "...csv", "conta": "gta"})`.
Devolve `{"ok": bool, ...}` (status por conta/rede), nunca levanta exceção.

## Testes

`cd app && python -m pytest -q hp_studio/metricas` — tudo com cliente falso, sem internet.
