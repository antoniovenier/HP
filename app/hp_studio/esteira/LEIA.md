# esteira — Etapa 3 do HP Studio (esteira de pastas P0/P1/P2)

O Claude só larga o pedido; o app baixa, confere, legenda, dubla/narra (quando
pode), edita, prepara a revisão, agenda e avisa "no ar" sozinho. O Claude entra
só no julgamento: escolher o pedido, revisar (notas) e agendar o TikTok pelo Chrome.

## 1. Como funciona

Tudo mora em `H:\HypadoLocal\esteira\` (`raiz_local()\esteira`). **Cada item é
uma pasta** com tudo dentro (`pedido.json`, bruto, transcrição, legenda,
dublagem, final, capa, `post.json`, `historico.log`, `estado.json`).

Nome da pasta: `P1_2026-09-30_1830_gta_rockstar-quinta`
= prioridade + data + hora alvo (Brasília) + canal + resumo do título.

| Prioridade | Quando usar | Efeito |
|---|---|---|
| `P0_` | urgente / ao vivo: gol, placar, lançamento, bombástica | **faixa expressa**: é processado antes de qualquer P1/P2 em **qualquer** etapa e, no mesmo ciclo, anda até onde der |
| `P1_` | do dia | depois dos P0, pelo horário alvo |
| `P2_` | programado | por último |

| Pasta | O que o app faz com o item | Vai para | Pesado? |
|---|---|---|---|
| `01_pedidos` | lê e valida o `pedido.json`; vídeo: **Baixador** (`scripts\ytdlp.py` ou `yt-dlp`) ou copia `arquivos` locais | `02` (vídeo) / `04` (estático) | sim (vídeo) |
| `02_baixados` | confere o bruto (tem vídeo? duração? corte cabe?) e extrai `audio.wav` | `03` | sim |
| `03_legenda_dublagem` | **Legendador** (faster-whisper) → `legenda.srt`; **Dublador** (`dublar.py`) se `dublar`; **Narrador Toque HP** se `narrar_toque_hp` | `04` | sim |
| `04_edicao` | **Editor** (ffmpeg): `final.mp4` 1080x1920, legenda e crédito queimados, −14 LUFS, `capa.jpg`. Estático: **Designer** (`estaticos.py`) → `arte\` | `05` | sim (vídeo) |
| `05_revisao` | gera 3 quadros (`revisao\quadro_1_inicio.jpg`, `_2_meio`, `_3_fim`, 540 px de largura para gastar menos token) + `texto_revisao.md`; espera `aprovado.json` ou `refazer.json` | `06` / volta / `99` | não |
| `06_agendados` | **Agendador**: grava na fila da API (Instagram, Threads, Facebook, YouTube); TikTok (e Pinterest) esperam `tiktok_ok.json` (`pinterest_ok.json`) do Claude | `07` quando todas as redes confirmarem | não |
| `07_postados` | aviso "no ar" na fila do WhatsApp (só se ligado; padrão = sombra). Depois de 7 dias vai para `07_postados\_arquivo\AAAA-MM\` | fim | não |
| `99_erros` | item com `erro.json` (etapa, mensagem, traceback resumido, tentativas) | `reprocessar` | — |

**Estáticos** (`carrossel`, `story`, `threads_texto`, `estatico`) pulam as etapas
de vídeo: `01 → 04 (arte) → 05 → 06 → 07`. `threads_texto` não tem arte: o texto
vai em `texto_threads.txt`. Se o pedido já trouxer imagens prontas em `arquivos`,
o Designer só as organiza em `arte\`.

## 2. Instalação (PC do Antônio)

1. Copie a pasta `esteira` para `G:\Meu Drive\Hypado\06 Projeto\app\hp_studio\esteira\`
   (ao lado de `hpbase`).
2. Legendador (opcional, mas sem ele os vídeos sem `legenda_manual.srt` vão para
   `99_erros` com a mensagem clara):
   `python -m pip install faster-whisper`
3. ffmpeg: já achado pelo `hpbase` (`H:\HypadoLocal\ferramentas\ffmpeg\bin`). O
   ffprobe é opcional (sem ele o app lê a saída do `ffmpeg -i`).
4. Criar pastas e `config.json` padrão (modo sombra):
   ```powershell
   cd "G:\Meu Drive\Hypado\06 Projeto\app\hp_studio"
   python -m esteira iniciar
   ```
5. Testes (na nuvem: 149 passando): `cd app ; python -m pytest -q hp_studio/esteira`

## 3. Comandos (`python -m esteira --help`)

| Comando | Para quê |
|---|---|
| `iniciar` | cria as pastas e o `config.json` |
| `pedido --json pedido.json` | cria o item em `01_pedidos` (valida tudo; erro diz o que falta) |
| `status` (`--json`) | tabela por etapa, com a situação de cada item |
| `aprovar <item> --notas gancho=9 legenda=8,5 audio=9 [--motivo ...]` | grava `aprovado.json` e já aplica |
| `refazer <item> --motivo "..." [--etapa 03] [--notas ...] [--ajustes '{"capa_tempo": 3}']` | grava `refazer.json` e já aplica |
| `tiktok-ok <item> [--link URL] [--agendado-para ...]` | o Claude agendou no TikTok pelo Chrome |
| `confirmar <item> <rede> [--link]` | confirma à mão (Pinterest, ou API em caso de dúvida) |
| `liberar <item>` | o Curador ajustou o pedido depois de uma nota < 5 |
| `reprocessar <item> [--etapa 04]` | tira de `99_erros` e devolve para a etapa |
| `prioridade <item> P0` | promove/rebaixa (renomeia a pasta) |
| `ciclo [--max N]` | uma passada agora |
| `vigiar --uma-vez` / `vigiar --intervalo 30` | vigia (loop) |
| `--simular` (em qualquer comando) | **não chama nada externo** (nem ffmpeg, nem scripts, nem filas de verdade): só move e registra |

`<item>` aceita o nome inteiro, o nome sem `P1_` ou um pedaço único ("rockstar").
O Claude também pode só largar um `.json` solto em `01_pedidos\`: o vigia
transforma em item (e guarda o original como `pedido_original.json`).

## 4. pedido.json

```json
{
  "canal": "gta",                        "tipo": "reel",
  "prioridade": "P1",                    "titulo": "Rockstar solta novidade na quinta",
  "fonte_url": "https://www.youtube.com/watch?v=...",   "arquivos": [],
  "credito": "@rockstargames",           "redes": ["instagram", "threads", "tiktok"],
  "horario_alvo": "2026-09-30T18:30:00-03:00",
  "dublar": false,                       "narrar_toque_hp": false,
  "observacoes": ""
}
```
Opcionais: `id` (gerado), `slug`, `legenda_post`, `hashtags` (≤ 30), `texto`
(obrigatório em `threads_texto`, ≤ 500), `roteiro_narracao` `{abertura, trecho,
fecho}`, `corte` `{inicio, fim}` (s), `capa_tempo` (s), `fonte_oficial`
(futebol), `fonte_propria`, `legendar` (padrão true), `laminas` (Designer).

Regras que o app **recusa** (erro na hora, nada é criado):
- `canal` ∈ gta, futebol, filmes, receitas, carros, destinos; `tipo` ∈ reel,
  carrossel, story, threads_texto, estatico; redes ∈ instagram, facebook, tiktok,
  youtube, threads, pinterest.
- **Futebol nunca com `dublar`/`narrar_toque_hp` = true** (voz sintética proibida);
  futebol com fonte externa exige `fonte_oficial: true` (clube/CBF/liga, nunca TV).
- Dublagem/voz só em destinos, receitas, carros e filmes; estático não tem voz.
- Crédito obrigatório quando há fonte externa (`fonte_url` ou `arquivos` de
  terceiros; material próprio: `fonte_propria: true`).
- Narração pede `roteiro_narracao` com abertura e fecho em forma de **pergunta**.
- Nada do Flow Games; GTA sem vazamento/leak; reel precisa de fonte.
- `threads_texto` só no Threads; story só Instagram/Facebook; YouTube só reel;
  Pinterest só receitas/carros/destinos; valor citado leva "Valores aproximados…"
  (no Threads o texto é conferido; na legenda do post o app acrescenta sozinho).
- O que **não** dá para checar automaticamente: trailer puro, imagem de TV,
  música com direitos — continua com o Curador.

## 5. Revisão (manual 09)

`aprovado.json` ou `refazer.json` na pasta do item em `05_revisao`:
```json
{"notas": {"assunto": 9, "fonte_credito": 10, "gancho": 8, "legenda": 7},
 "motivo": "texto curto", "etapa_destino": "(opcional)", "ajustes": {}, "revisor": "Claude"}
```
- O app **sempre recalcula** média e veredito pelas notas (0 a 10): ≥ 9 Excelente,
  7–8,9 Bom → **aprovado** (06); 5–6,9 Médio → volta para a etapa do **critério de
  menor nota** (empate: a etapa mais para trás) ou para `etapa_destino` se o revisor
  mandar; < 5 Razoável → volta para `01_pedidos` e **espera o Curador**
  (`aguardando_curador.json`; depois de ajustar: `liberar`).
- Máximo **2 voltas**; na 3ª reprovação o item vai para `99_erros` com o motivo.
- `aprovado.json` com média < 7 vale como refazer; os dois arquivos juntos: vale o
  refazer. Arquivo inválido é renomeado para `*.invalido.json` e o item espera.
- `ajustes` é mesclado no `pedido.json` antes de refazer (ex.: `capa_tempo`, `corte`,
  `legenda_post`). Para corrigir a legenda, grave `legenda_manual.srt` na pasta
  (tem preferência sobre a automática).
- Mapa critério → etapa (muda em `config.json` → `criterio_etapa`): assunto e
  fonte_credito → 01; legenda e voz → 03; gancho, audio, enquadramento, ritmo, capa,
  arte, texto_post → 04. Estático nunca volta para 02/03 (vai para 04).
- Decisões ficam em `revisao\decisao_rodada_N.json` e `revisao\decisoes\`.

## 6. Modo sombra (padrão) e modo real

`config.json` (em `H:\HypadoLocal\esteira\`):

| Chave | Padrão | Efeito |
|---|---|---|
| `modo` | `"sombra"` | sombra: o Agendador grava em `esteira\sombra\fila_api\` (o publicador nunca lê) e confirma na hora como "sombra"; **nada vai ao ar**. `"real"`: grava em `H:\HypadoLocal\fila_api\` |
| `aviso_no_ar_habilitado` | `false` | só com `modo: "real"` **e** `true` o aviso vai para `H:\HypadoLocal\whatsapp_fila\`; senão vai para `esteira\sombra\whatsapp_fila\` (para comparar com o que o plantão mandou) |
| `max_voltas` / `max_tentativas` | 2 / 3 | revisão / erros passageiros |
| `comandos` | ver abaixo | linha de comando dos scripts (ajuste sem mexer no código) |
| `editor` | 1080x1920, 30 fps, crf 20, −14 LUFS, TP −1,5, fundo desfocado | |
| `redes_api` / `redes_manuais` | IG, Threads, FB, YT / TikTok, Pinterest | |
| `arquivar_postados_dias` | 7 | limpa `07_postados` |

No modo sombra o vídeo é editado de verdade (é isso que o `qa_paridade` compara
com o do Claude: duração, SSIM, loudness, legenda — `edicao.json` traz os números).
Pela regra da empresa, só depois de **7 dias de sombra com paridade** trocar para
`"modo": "real"`.

## 7. Integração com o HP Studio

- **Gancho do motor (etapa 1)**: `esteira.gancho.executar(trabalho: dict) -> dict`,
  nunca levanta exceção (`{"ok": true/false, ...}`). Ex.: `{"tipo": "esteira",
  "acao": "ciclo"}` a cada 30 s; também `pedido`, `status`, `aprovar`, `refazer`,
  `tiktok_ok`, `confirmar`, `liberar`, `reprocessar`, `prioridade` (ver docstring).
- **Ou** vigia próprio sem janela (Agendador de Tarefas, ao entrar):
  `pythonw -m esteira vigiar --intervalo 30` com a pasta `hp_studio` como diretório.
  Só roda um vigia por vez (`esteira\.vigia.lock`).
- Logs: `H:\HypadoLocal\app\logs\esteira_AAAA-MM-DD.log` (sem segredos).
- Subprocessos sempre por `hpbase.rodar` (sem janela preta) e com timeout; todo
  ffmpeg tem saída de duração limitada (`-t`).

## 8. Segurança contra queda

- `.em_andamento` na pasta durante o trabalho: se o app cair, o próximo ciclo anota
  "retomada após queda" no `historico.log` e refaz a etapa (tudo é gravado com nome
  temporário + troca atômica). Queda 3 vezes na mesma etapa → `99_erros`.
- `estado.json` → `pendente`: diário do movimento. Caiu entre terminar e mover? O
  próximo ciclo só completa o movimento (não refaz a edição).
- Movimento = `os.replace` da pasta inteira (mesma unidade, atômico, idempotente).
  Arquivo aberto em outro programa: o movimento é adiado, não perde nada.
- Pedido novo nasce em `.criando_<nome>` e só aparece completo.

## 9. Pesado e horário — **P0 liberado (decisão do Antônio, 30/09/2026)**

Baixar, conferir, legendar/dublar e editar vídeo usam `TravaPesada` (1 por vez,
`pesado.lock`) e **não rodam das 18h às 22h30 — exceto P0** (gol, placar,
lançamento, bombástica). Um gol às 20h é baixado e editado na hora; um P1/P2
espera 22h30. O P0 continua respeitando o `pesado.lock` (1 pesado por vez).
Estáticos, revisão, agendamento e aviso são leves e rodam a qualquer hora.
Chave `p0_na_janela` no `config.json` (padrão `true`; `false` volta à regra antiga).
**O CLAUDE.md da empresa precisa ganhar essa exceção** (a sessão HP GESTÃO atualiza).

Aviso "no ar": `aviso_no_ar_habilitado` fica **false** — decisão de 30/09: quem
monta o aviso é o `whatsapp_local` (a partir do `agendados.json` + `AVISO.md`).

## 10. Suposições da nuvem (conferir no PC antes de ligar)

1. **Formato da fila da API** (`agendador.py`, suposto — `publicador_meta.py` não
   estava disponível e **não foi reescrito**): 1 JSON por post e por rede,
   `fila_api\<item>__<rede>.json` com `id, origem, rede, conta, canal, tipo,
   midia[], capa, legenda, titulo, agendar_para, status:"pendente", criado_em`;
   mídia copiada para `fila_api\midia\<item>\`. Confirmação suposta: o publicador
   muda `status` para `publicado`/`agendado`/`ok` com `permalink`/`link`, ou move
   o arquivo para `fila_api\feitos\` (`publicados\`, `enviados\`, `ok\`);
   `status: "erro"` → item vai para `99_erros`. Para casar com o real, mude **só**
   `montar_registro_fila()` e `ler_confirmacao()` em `agendador.py`.
2. Facebook e YouTube estão em `redes_api` (etapa 4 em andamento no PC). Se a fila
   ainda não publica neles, passe-os para `redes_manuais` no `config.json` (aí
   esperam `facebook_ok.json`/`youtube_ok.json`, gravados por `confirmar`).
3. **Parâmetros dos scripts** (`config.json` → `comandos`, marcadores `{python}
   {scripts} {url} {entrada} {saida} {item}`):
   - `ytdlp.py {url} --saida <pasta>` (o app pega o maior vídeo da pasta);
   - `dublar.py --srt legenda.srt --saida dublagem.wav` (dublagem) e
     `dublar.py --texto-arquivo frase.txt --saida frase.wav` (narração, frase a frase);
   - `estaticos.py --pedido pedido.json --saida arte\` (o app pega as imagens da pasta).
4. Aviso "no ar": texto simples montado aqui (`aviso.py`); o modelo oficial está em
   `06 Projeto\AVISO.md` — ajustar `montar_aviso()` quando o enviador (módulo E) ficar pronto.
5. Critérios da revisão e o mapa critério → etapa são uma proposta até o manual 09 fechar.

## 11. O que falta ligar no PC (em ordem)

1. Copiar o pacote e rodar `python -m esteira iniciar` e os testes.
2. `pip install faster-whisper` (primeira execução baixa o modelo `small`).
3. Conferir os parâmetros reais de `ytdlp.py`, `dublar.py`, `estaticos.py` e ajustar
   `comandos` no `config.json`.
4. Ler `publicador_meta.py` e ajustar as 2 funções do `agendador.py` (item 10.1).
5. Registrar o gancho no motor (ou a tarefa do vigia) em modo sombra.
6. 7 dias de sombra comparando com o `qa_paridade`; então `"modo": "real"`.
7. Quando o enviador de WhatsApp estiver em sombra aprovada: `aviso_no_ar_habilitado: true`.
8. Decidir o ponto da seção 9 (P0 na janela 18h–22h30).
