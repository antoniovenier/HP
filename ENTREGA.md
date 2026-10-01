# ENTREGA.md — HP Studio, rodada 2: os formatos reais do PC (01/10/2026)

**Para o Diretor, em 3 linhas.** (1) O repositório da nuvem passou a falar os formatos REAIS do PC (fila da API, tokens, scripts, pedido, lote de estáticos, WhatsApp, paleta) com 20 fixtures copiadas da Seção 4 e um teste de contrato; mais as lacunas do YouTube e do Facebook (`publicar_extra`), as artes de story (3 modelos × 6 canais), o story no celular real por ADB e 86 fontes novas verificadas para o radar. (2) **1540 testes passando, 0 falhas, 74 s** na nuvem (rodada 1: 554; novos: 986) — app 939 · scripts 520 · contrato 43 · radar 38. (3) Falta o que só o PC/Antônio pode fazer: aprovação da auditoria do YouTube, permissões de comentário da Meta, coleta de telas reais do Instagram (E4), decidir os conflitos de paleta e revisar a lista de ofensivos; tudo começa em sombra/simulação.

Tudo foi feito e testado na nuvem (Linux, Python 3.11, ffmpeg 6, Pillow 12). **Nada rodou no PC, no emulador,
no WhatsApp nem nas APIs de verdade** (rede só para ler páginas públicas: tarefa F e a documentação oficial
do Google/Meta nas tarefas B e C). Os relatórios completos de cada agente estão em `docs/rodada2/<tarefa>.md`
(A1, A2a, A2b, A3, D, F0–F4, E1, E2, B, C) e são a fonte das seções 6 a 9 deste arquivo.

## 1. O que foi entregue (tabela módulo · arquivos novos · testes · tempo · começa em)

| Tarefa | Módulo (onde fica no PC) | Arquivos novos | Testes novos (passed/failed/skipped) | Tempo | Começa em |
|---|---|---|---|---|---|
| A1 | `hpbase/fila_api_pc.py` (fila real da API) + `trava.py`/`caminhos.py` (A6) + `reenvio_seguro.py` | `fila_api_pc.py`, `LEIA_fila_api_pc.md`, `testes/test_fila_api_pc.py`, `testes/test_trava_pc.py`, `esteira/testes/test_config_pc.py` | 50 + 4 no reenvio / 0 / 0 | < 1 s | sombra (`esteira_sombra`; `reenviar --simular`) |
| A2 | `metricas/chaves_pc.py` (nomes reais de token; IG em `graph.instagram.com`) | `chaves_pc.py`, `testes/test_chaves_pc.py`, `contas_exemplo.json` | 21 / 0 / 0 | 0,2 s | `python -m metricas coletar --simular` → 0 `sem_token` |
| A3 | `esteira/comandos_pc.py` (argv exato de `ytdlp/cortar/dublar/estaticos/posts_*`) | `comandos_pc.py`, `testes/test_comandos_pc.py` | 23 / 0 / 0 | 0,8 s | `esteira --simular` |
| A4 | `esteira/pedido_pc.py` (pedido real) + `scripts/story_post_lote.py` (chave `interativo`, pergunta ≤ 25) | `pedido_pc.py`, `LEIA_pedido_pc.md`, `testes/test_pedido_pc.py`, `story_post_lote.py`, `LEIA_story_post_lote.md`, `testes/test_story_post_lote.py` | 60 + 26 / 0 / 0 | 0,5 s | `story_post_lote.py <lote>` (só decide) |
| A5 | `hpbase/marca.py` (paleta única da §4.6 + resolvedor de fontes) | `marca.py`, `testes/test_marca.py` | 63 / 0 / 0 | 0,2 s | — (dado) |
| A7 | `whatsapp_local/fila_pc.py` (fila real, 6 `agendados.json`, aviso literal) | `fila_pc.py`, `LEIA_fila_pc.md`, `testes/test_fila_pc.py` | 22 / 0 / 0 | 0,4 s | sombra (`importar --so-mostrar`) |
| A8 | `tests/test_contrato_pc_real.py` + `scripts/ui_dump.py` + `radar_fontes/esquema_radar.py` | `tests/` (conftest, 20 fixtures, teste), `ui_dump.py`, `LEIA_ui_dump.md`, `testes/test_ui_dump.py`, `esquema_radar.py` | 43 + 5 / 0 / 0 | 0,6 s | roda depois de cada integração |
| B | `publicar_extra/youtube_extra.py` (playlists, corrigir vídeo, conferir lote, SRT, cota) | `youtube_extra.py`, `LEIA_youtube.md`, `testes/test_youtube_extra.py`, `contrato_pc.py`, `LEIA.md` | 99 / 0 / 0 | 0,7 s | simulação (`ClienteFalso`); no PC só depois da auditoria |
| C | `publicar_extra/facebook_extra.py`, `comentarios.py`, `lexico_comentarios.json`, `comentarios_ig_threads.py` | + `LEIA_facebook.md`, `testes/test_facebook_extra.py`, `test_comentarios.py`, `test_comentarios_ig_threads.py`, `comentarios_banco.json` | 225 / 0 / 0 | 0,6 s | `enviar=False` (só propõe); listar é só leitura |
| D | `scripts/story_artes.py` (+ `_base`, `_canais`, `_modelos`, `_exemplos`) | 5 módulos, `LEIA_story_artes.md`, `testes/test_story_artes.py` | 136 / 0 / 0 | 10 s | `story_artes.py exemplos <pasta>` (gera arte; não publica) |
| E | `scripts/story_dispositivo.py`, `story_fila_v2.py`, `story_fluxos.py`, `story_coletar_telas.py` | 4 módulos, `LEIA_story_celular.md`, `testes/adb_falso.py`, 4 `test_story_*.py`, 28 XML em `tests/fixtures/android/` | 166 / 0 / 0 | 1,8 s | `--simular` (roteiro sem adb) |
| F | `radar_fontes/` (`verificar_fontes.py`, 4 JSONs de fontes, `RELATORIO_FONTES.md`) | `verificar_fontes.py`, `LEIA.md`, `testes/`, `*_fontes_novas.json`, `*_candidatos.txt`, `RELATORIO_FONTES.md` | 38 / 0 / 0 | 0,9 s | dados verificados (feed do YouTube: repetir no PC) |

**Suíte inteira (rodada 1 + rodada 2), rodada na nuvem depois do último commit:**

| Comando | passed | failed | skipped | tempo |
|---|---|---|---|---|
| `cd app/hp_studio_nuvem && python3 -m pytest -q hpbase esteira metricas qa_paridade whatsapp_local publicar_extra` | **939** | 0 | 0 | 28,3 s |
| `cd scripts && python3 -m pytest -q testes` | **520** | 0 | 0 | 44,1 s |
| `cd . && python3 -m pytest -q tests` (contrato, A8) | **43** | 0 | 0 | 0,6 s |
| `python3 -m pytest -q radar_fontes` | **38** | 0 | 0 | 0,9 s |
| **Total** | **1540** | **0** | **0** | **74 s** |

Rodada 1 continua verde dentro desses números: os 373 do app e os 181 dos scripts passam (alguns testes antigos
foram **ajustados** para o formato real — fila da API, comandos, `recente_max_min` — e cada ajuste está no `PATCHES.md`).

### Tarefa por tarefa: pronto, pela metade, não deu

| Tarefa | Pronto | Pela metade | Não deu / não feito |
|---|---|---|---|
| **A** (A1–A8) | tudo: fila real, tokens, comandos, pedido, lote, marca, trava/pastas, WhatsApp, contrato (320 testes) | — | mensagens do `_validar` que o enunciado cortou ("feed = exatamente 1 imagem…") ficaram como suposição |
| **B** (B1–B6) | B1–B5 + revisão crítica B6 com página oficial e data | — | não confirmado em página oficial: granularidade do `publishAt`, regras de Shorts, lado legal do COPPA, escopos por método |
| **C** (C1–C3) | C1, C2 e **C3 também** (Instagram e Threads) | C1: listar **reels** agendados (a doc da Meta não diz como; tentativa marcada `confirmar: true`) | — |
| **D** | 3 modelos × 6 canais, 18 exemplos + prancha vistos e ajustados em 3 rodadas | — | — |
| **E** (E1–E4) | aparelho (emulador/celular), fluxos, fila v2, coleta de telas, roteiro `--simular` | patch (b) do `story_post.py` (usar o `Dispositivo`) só **descrito** linha a linha, não aplicado | 5 ids da figurinha de contagem/calendário sem tela de coleta; o que só o aparelho real (API 34) confirma |
| **F** | 4 JSONs (futebol 7+13, filmes 8+18, carros 6+21, gta 1+1), ferramenta + 38 testes, relatório | `channel_id` provado pela página do canal, não pelo feed (404 daqui); lista da Série A pelo ge/Wikipedia (CBF não abre daqui) | mesclar nos `07 Canais\radar\*.json` do PC (não estão no repositório); Caoa Chery e 8 montadoras sem prova de canal/feed |
| **Fechamento** | suíte inteira, 3 documentos de controle, compilado único + `desempacotar` de prova | — | — |

## 2. Como rodar os testes no PC (PowerShell 5.1) e o número esperado

```powershell
$PY = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
& $PY --version                                   # Python 3.12.x
& $PY -m pip install pytest numpy pillow          # os únicos pacotes que os testes novos usam (já instalados na rodada 1)

cd "G:\Meu Drive\Hypado\06 Projeto\app\hp_studio_nuvem"
& $PY -m pytest -q hpbase esteira metricas qa_paridade whatsapp_local publicar_extra
#   esperado: 939 passed (na nuvem 28 s; no PC o qa_paridade usa ffmpeg)

cd "G:\Meu Drive\Hypado\06 Projeto\scripts"
& $PY -m pytest -q testes
#   esperado: 520 passed (na nuvem 44 s; test_reel_futebol e test_story_artes usam ffmpeg/Pillow)

cd "G:\Meu Drive\Hypado\06 Projeto"                 # raiz da entrega (onde ficam tests\ e radar_fontes\)
& $PY -m pytest -q tests radar_fontes
#   esperado: 43 + 38 passed — tests\ é o TESTE DE CONTRATO (A8): rode depois de cada integração
```

Os testes criam arquivos só em pastas temporárias (`HP_LOCAL`/`HP_DRIVE` apontam para `tmp_path`); nenhum
toca `H:\HypadoLocal\segredos\`, rede, adb, WhatsApp ou relógio real. Os 53 testes da etapa 1 do PC não
são afetados (não há `conftest.py` em `app\`; cada `testes\` tem o seu).

## 3. Cópia para o PC (leigo, sem sobrescrever o que o PC tem)

O compilado `ENTREGA_NUVEM_HP_STUDIO_2.md` traz só o que é **novo** e os 3 documentos de controle; o
`desempacotar.py` do PC cria os arquivos nos caminhos relativos à raiz do repositório. Depois de
desempacotar numa pasta temporária no H: (nada no C:):

1. **Arquivos novos** (copiar como estão): tudo de `app\hp_studio_nuvem\...` (novos módulos `fila_api_pc.py`,
   `marca.py`, `chaves_pc.py`, `comandos_pc.py`, `pedido_pc.py`, `fila_pc.py`, `publicar_extra\`, testes e `LEIA_*.md`),
   `scripts\story_artes*.py`, `scripts\story_post_lote.py`, `scripts\story_dispositivo.py`, `scripts\story_fluxos.py`,
   `scripts\story_fila_v2.py`, `scripts\story_coletar_telas.py`, `scripts\ui_dump.py`, `scripts\testes\test_*.py` novos,
   `scripts\testes\adb_falso.py`, `tests\` (contrato + fixtures), `radar_fontes\`, `docs\compilar_entrega_2.py`,
   `docs\desempacotar_check.py`.
2. **Arquivos da rodada 1 que mudaram**: aplicar `patches\rodada2_rodada1_alterados.diff` com
   `git apply` na cópia do PC (ou à mão, função por função, pelo `PATCHES.md`). Os 4 que mudaram mais da
   metade vêm inteiros no compilado (copiar por cima): `app/hp_studio_nuvem/hpbase/trava.py`, `app/hp_studio_nuvem/esteira/agendador.py`, `app/hp_studio_nuvem/esteira/testes/test_agendador_aviso.py` e `app/hp_studio_nuvem/metricas/config.py`.
3. **Apagar** `app\hp_studio_nuvem\metricas\contas.json` se existir (virou `contas_exemplo.json`; a cópia do
   Antônio em `H:\HypadoLocal\metricas\contas.json` continua valendo e não está neste repositório).
4. Rodar os 3 blocos de testes da seção 2. Se o número bater, a integração está igual à nuvem.
5. Ligar em **modo sombra** (nada publica): tudo começa em `--simular`/sombra, como a tabela da seção 1 diz.

## 4. O que a sessão principal decidiu sozinha (e como desfazer, 1 linha cada)

| Decisão | Base | Onde desfazer |
|---|---|---|
| Voz sintética passa a valer no GTA (criador gringo sai dublado; futebol continua proibido) | `config.json` real do GTA (§4.5): `dublagem` + 19 criadores `en` "saem dublados" | `esteira/constantes.py::CANAIS_COM_VOZ` (tirar `"gta"`) |
| `redes_api` da esteira = só `instagram` e `threads`; `facebook`, `youtube`, `tiktok`, `pinterest` esperam `<rede>_ok.json` | `_validar` do publicador real recusa Facebook (§4.2); o `publicar\` do PC ainda não é chamado pela esteira da nuvem | `esteira/config.py::Config.redes_api` |
| Tipo `"aviso"` aceito no WhatsApp local (avisar o Antônio) | as 2 mensagens reais de `temp\whatsapp_fila.json` (§4.8) | `whatsapp_local/config.py::TIPOS_PERMITIDOS` |
| Pedido solto em `01_pedidos` só é lido depois de 2 s parado | §4.5 ("nada meio gravado") | `esteira/motor.py::_importar_json` |
| `metricas/contas.json` → `contas_exemplo.json` | regra 3 da Seção 2 (classificador do PC) | `metricas/config.py::caminho_config` |
| `ZONA_LINK = (140,1500)-(940,1640)` mantida como a tarefa D define, mesmo entrando 70 px nos 350 px da base | §5-D é explícita; só o contorno fino entra na faixa | `hpbase/marca.py::ZONA_LINK` (o gerador e o `_zonas.json` seguem) |
| As 3 correções do `verificar_fontes.py` que o F4 deixou prontas foram aplicadas (motor1 exato, data por extenso, marcas sobrevivem ao `--gravar`) e o feed da Netflix pt_br entrou | F4 §8 | `radar_fontes/verificar_fontes.py` (`TOKENS_EXATOS`, `_data_por_extenso`, `MARCAS_HUMANAS`) |
| Pacote renomeado para `app/hp_studio_nuvem` no repositório | §1 regra 4 (pacote irmão) | — |

Conflitos de paleta (§4.6) ficam como **decisão do Antônio/Diretor**, não da nuvem: Carros `#FF2D2D`
(perfil) × `#E61E2D` (post) — arte nova usa `#E61E2D`; GTA `#FF48A0` (post) × `#FF3CAA` (perfil) × `#FF3D8B`
(site) — arte nova usa `#FF48A0`; Futebol: vale o verde `#1ED760` (o reel da rodada 1 foi trocado). Divergências
só relatadas: página de links e painel usam Carros `#FF3B3B` (um 3º vermelho) e GTA `#FF3D8B`.

## 5. Limites deste ambiente (o PC resolve)

- **Feed do YouTube responde 404 daqui** (`youtube.com/feeds/videos.xml?channel_id=…`, para qualquer canal — bloqueio
  de datacenter). Os 53 `channel_id` da tarefa F foram provados pela **página oficial do canal** (ela declara o
  próprio id em `externalId`/`canonical` e o título): `verificado_por: "pagina_canal"`. No PC, os 4 comandos
  `verificar … --gravar` promovem para `"feed"`.
- `cbf.com.br` e `kianewscenter.com` não abrem daqui (certificado no proxy); `press.paramountplus.com`,
  `press.amazonstudios.com` e `hondanews.com.br` devolvem 502 pelo proxy. A lista da Série A 2026 veio do ge +
  Wikipedia (idênticas), não da CBF — conferir no PC.
- Fontes do PC (Bauhaus 93, Segoe UI, Bahnschrift) não existem no Linux: os testes de render rodam com o
  fallback (DejaVu) e os 18 exemplos de story foram gerados com as OFL reais (Anton, Barlow, Barlow Condensed,
  DM Serif Display) baixadas do repositório google/fonts para um cache fora do repositório. No PC
  `marca.fonte()` acha as fontes de verdade sozinho.
- Rede foi usada só na tarefa F (páginas públicas) e, nas tarefas B e C, para LER a documentação oficial do
  Google/Meta (custos de cota, permissões): está dito no relatório de cada uma e nenhum teste faz rede.

## 6. Suposições que sobraram (suposição · arquivo · função exata onde trocar)

Consolidado das seções 5 dos relatórios, por agente. É a lista que a rodada 1 não tinha num lugar só.
O teste de contrato (`tests/test_contrato_pc_real.py`) falha com mensagem clara se uma fixture mudar de formato.

#### A1

| Suposição | Arquivo | Onde trocar |
|---|---|---|
| Texto completo da mensagem "feed = exatamente 1 imagem…" (o enunciado cortou com "…"); usei "feed = exatamente 1 imagem (vídeo vai como reel)". Os testes casam só o prefixo. | `app/hp_studio_nuvem/hpbase/fila_api_pc.py` | `_validar_tipo` |
| Mensagens que o PC não tem (o argparse dele impede antes): "post de texto só no Threads", "post de texto não leva arquivo (veio N)", "tipo tem que ser feed, carrossel, reel, story ou texto (veio X)" | `hpbase/fila_api_pc.py` | `_validar_tipo` |
| Item em `removidos\<motivo>\` volta como `estado: "erro"` ("tirado da fila à mão (removidos\<motivo>)") — para a esteira mandar o item a `99_erros` em vez de esperar para sempre | `hpbase/fila_api_pc.py` | `ler_confirmacao` (laço de `removidos`) |
| Slug do id dos canais: vem do nome do item da esteira (`P1_<data>_<hora>_<canal>_<slug>`) ou do título; no PC quem escolhe é o script que enfileira. Texto do Threads dos canais sem `lote` usa a convenção genérica `<canal>_<data>_<HHMM>_<slug>_th_texto` | `esteira/agendador.py`; `hpbase/fila_api_pc.py` | `slug_do_post`; `id_padrao` |
| `CANAIS_DIR` do publicador real não veio no enunciado; `PASTA_CANAL` guarda só o nome da pasta em `07 Canais` (GTA = `None` = `06 Projeto`) | `hpbase/fila_api_pc.py` | constante `PASTA_CANAL` |
| O `meta` passado ao `publicar_item` real é só leitura (`fila_api_pc.ler_meta`). Se o `publicar_item` do PC gravar ids novos nesse dict e esperar que alguém salve, nada é salvo (o publicador `rodar` real salva pelo `carregar_meta`) | `scripts/reenvio_seguro.py` | `achar_publicador` (argumento `meta=`) |
| `desde` ISO do lock do PC é hora local do PC, sem fuso (comparado com `datetime.now()`/`agora` naive) | `hpbase/trava.py` | `_desde` |
| `capa` só vai para a fila no tipo `reel` (4.1: "capa opcional (reel)") | `esteira/agendador.py` | `montar_registro_fila` |


#### A2a

| Suposição | Arquivo | Onde trocar |
|---|---|---|
| Host/versão do YouTube no inventário: `https://www.googleapis.com` / `v3` (a §4.3 não diz) | `metricas/chaves_pc.py` | `HOSTS["youtube"]` (e `CHAVE_HOST`) |
| Nomes dos grupos novos em `arquivos_segredo` (`meta_meta`, `facebook`, `facebook_paginas`, `youtube_oauth`, `youtube_canais`) — escolhidos para não colidir com `meta`/`youtube` da rodada 1 que uma cópia antiga do `contas.json` do Antônio possa sobrepor | `metricas/chaves_pc.py` | `ARQUIVOS_PADRAO`, `GRUPOS` |
| Falta de **id** também sai como `sem_token` (com `"falta": ["id"]`), como o coletor já reportava | `metricas/chaves_pc.py` | `_entrada_meta` / `_entrada_youtube` |
| Facebook coleta em `v26.0` (`versao_graph`); o `metricas_api.py` do PC pode usar outra | `metricas/config.py` | `PADRAO["versao_graph"]` e `contas.json` |
| `transcrever.py`: positional `arquivo` antes de `--id-streamer` (argparse aceita as duas ordens; a §4.4 só dá o `usage`) | `esteira/comandos_pc.py` | `MODELOS["transcrever"]` |
| `estaticos.py story --selo`: valor quando vem texto, bandeira solta quando `True` | `esteira/comandos_pc.py` | `argv_estaticos_story` |
| `argv_baixar` sem `inicio`/`fim` baixa o vídeo inteiro (sem `--download-sections`), como `baixar.py` sem `--so-trecho`; `inicio − 4 < 0` vira `00:00:00.000` | `esteira/comandos_pc.py` | `argv_baixar`, `hms` |
| Sem `corte` no pedido, a janela do `cortar.py` é `[4, 4 + (fim − inicio)]` (o `lote.py` encosta em frases pela transcrição — não é puro) | `esteira/comandos_pc.py` | `argvs_do_pedido` |
| Emenda (`trechos/zoom/cobrir/bipes/tarjas/selos`): `cortar.py` recebe `<bruto>_ed<n>.mkv` + `--transcricao <bruto>_ed<n>.json`, com `n` = número do item no plano (`"n"`/`lote_n`) | `esteira/comandos_pc.py` | `argvs_do_pedido` (`CAMPOS_EMENDA`) |
| `arquivo_corte`: caracteres proibidos no Windows no gancho viram espaço; mês por extenso em `MESES` | `esteira/comandos_pc.py` | `arquivo_corte` |
| `pedido_de_plano`: item com `render_status`/`agendado`/`upload` é "concluído" e o `arquivo` dele é o corte pronto (descartado); sem isso, `arquivo` = trecho já baixado → `arquivos: [arquivo]`; crédito = `Crédito: @x` da legenda, senão o do `config.json`, senão `@<streamer>` | `esteira/comandos_pc.py` | `pedido_de_plano`, `CAMPOS_RESULTADO`, `_RX_CREDITO` |
| Designer GTA: story usa `modelo` (padrão `noticia`) e `opcoes` do pedido; `estatico` não tem comando no `estaticos.py` (erro); canais exigem `pedido["spec"]` (JSON do `posts_<canal>.py`) — não inventei o spec por modelo | `esteira/plugins.py` | `DesignerScript.comando`, `spec_carrossel_gta` |
| `DubladorScript.dublar` na etapa 03 só com `final.mp4` + `transcricao_pt.json`/`transcricao.json` | `esteira/plugins.py` | `DubladorScript.dublar` |


#### A2b

| Suposição | Arquivo | Onde trocar |
|---|---|---|
| Pedido sem `canal` é do GTA (`"gta"`), porque o `config.json` e o `estaticos.py` do PC são do GTA | `esteira/pedido_pc.py` | `CANAL_PADRAO`, `validar_pc` |
| Corte exige `streamer` (id do criador); estático só confere criador se trouxer `streamer` | `esteira/pedido_pc.py` | `validar_pc`, `criador_autorizado` |
| **Sem `config.json`** (ou `HP_CONFIG_PC` apontando para nada) nenhum criador é autorizado → corte recusado com a mensagem dizendo o caminho procurado (regra 6: "só criador com autorizado: true") | `esteira/pedido_pc.py` | `criador_autorizado` |
| Corte com `video`/`link` exige `inicio` e `fim` (o `ytdlp.py` baixa só o trecho); com `arquivo` (trecho pronto) são opcionais | `esteira/pedido_pc.py` | `validar_pc` |
| `story` exige `arte` ∈ `ARTES_STORY`; `carrossel` exige `spec` (caminho ou dict); `texto` exige `texto` | `esteira/pedido_pc.py` | `validar_pc` |
| Apelidos `ig/fb/th/yt/shorts/tt/pin` valem também no pedido (não só no post.json); `pinterest` é recusado no pedido do PC (não está em `REDES`); `redes` pode vir como texto "instagram, tiktok" | `esteira/pedido_pc.py` | `redes_do_pedido` |
| `prioridade` aceita `"1"` e `"P1"` além do inteiro; `data` aceita espaço no lugar do `T` e segundos | `esteira/pedido_pc.py` | `prioridade_pc`, `ler_data` (`_RX_DATA`) |
| Vazamento: `vazad|vazament|leak` em gancho/titulo/legenda/texto/link/obs, só no canal gta (mesma regra do `validar_pedido` da rodada 1) | `esteira/pedido_pc.py` | `conferir_vazamento`, `PALAVRAS_VAZAMENTO` |
| `toque_hp` (dict) no pedido do PC vira `narrar_toque_hp` + `roteiro_narracao`, como o `pedido_de_plano` do A2a | `esteira/pedido_pc.py` | `para_esteira` |
| `titulo` interno = titulo → gancho → `opcoes.titulo` (story) → 1ª linha da legenda/texto → `spec.titulo/tema` → `"<tipo> <data>"`; apelido = `apelido` → gancho → esse título | `esteira/pedido_pc.py` | `titulo_do_pedido`, `apelido_do_pedido` |
| post.json do corte: `arquivos = ["final.mp4"]` e `capa = "capa.jpg"` (docstring do `post.py`; o PC também gera `upload.mp4` ≤ 10 MB — não sei qual o `publicar` prefere); estáticos sem `arquivo` ficam com lista vazia (a etapa 06 completa com a arte); `tags` = `hashtags` do pedido, senão as `#` da legenda; `titulo` não é cortado em 100 (quem corta é o `publicar`) | `esteira/pedido_pc.py` | `ARQUIVOS_POST_PADRAO`, `CAPA_POST_PADRAO`, `para_post_json` |
| `textos {rede: texto}` para rede que não está em `redes` é descartado em silêncio | `esteira/pedido_pc.py` | `para_post_json` (laço `por_rede`) |
| A figurinha recebe texto puro: **emoji sai** da pergunta e das opções (o adb não digita emoji); o vocativo/introdução sai **mesmo quando a pergunta cabe** ("Galera, o que você faz?" → "O que você faz?") | `scripts/story_post_lote.py` | `limpar`/`sem_emoji`, `candidatos` (ordem `sem_vocativo` antes de `texto`) |
| Lista de vocativos/introduções (galera, gente, pessoal, me conta, e aí, pergunta do dia, hein…) — só segmentos feitos SÓ dessas palavras antes de `,`/`:` e o que sobra tem que terminar em `?` | `scripts/story_post_lote.py` | `PALAVRAS_DE_ABERTURA`, `VOCATIVOS_DE_FECHO`, `sem_vocativo` |
| Se a ÚLTIMA oração com "?" não cabe, tenta as anteriores com "?" (da última para a primeira) antes de recusar | `scripts/story_post_lote.py` | `candidatos` |
| Opção repetida (ignorando acento/maiúscula) é recusada | `scripts/story_post_lote.py` | `opcoes_da_figurinha` |
| No lote real a conta é o `@` dentro do texto `rede` (`"Instagram @hpgta6 (compartilhar no Facebook)"` → `hpgta6`), `compartilhar_facebook` = "facebook" nesse texto, canal = `gta` | `scripts/story_post_lote.py` | `ler_interativo`, `conta_do_texto`, `CANAL_PADRAO` |
| `figurinha` diferente de `enquete` é recusada (o story_post só sabe enquete) | `scripts/story_post_lote.py`, `scripts/story_post.py` | `decidir`, `carregar_enquete` |
| O lote real não tem `caixa_enquete`: vale `caixa_enquete` do `story_post_config.json` (ou a chave extra dentro de `interativo`, se alguém gravar) | `scripts/story_post.py` | `carregar_enquete` |
| `len()` da pergunta da fixture dá **44** (o enunciado diz 46 — provavelmente o texto real era um pouco maior); a decisão é a mesma | `tests/fixtures/pc_real/lote_estaticos_2026-10-01.json` | — |


#### A3

| Suposição | Arquivo | Onde trocar |
|---|---|---|
| Aviso "no ar" dos canais: mesmo modelo do GTA trocando o cabeçalho por `🎬 *Novo post no ar — <Canal> \| HP!*` (o `AVISO.md` só descreve o GTA; "trocando o título" lido como o título do canal no cabeçalho). O GTA usa o literal `🎬 *Novo vídeo no ar!*` mesmo para story/carrossel | `whatsapp_local/fila_pc.py` | `CABECALHO_CANAL`, `CABECALHO_GTA` (função `montar_aviso_no_ar`) |
| Link de perfil quando a rede está em `redes[]` sem link: Instagram `instagram.com/<handle>/`, TikTok `tiktok.com/@<handle>`, YouTube `youtube.com/@<handle>`, Threads `threads.com/@<handle>` (o domínio do log real), **Facebook `facebook.com/<handle>` é palpite** | `whatsapp_local/fila_pc.py` | `PERFIL` (função `link_da_rede`) |
| `links[youtube]`/`links[tiktok]` podem vir como URL pronta ou só o id (ou em `ids{}`/`<rede>_id`); id vira a URL de §4.8 | `whatsapp_local/fila_pc.py` | `link_da_rede` |
| Tipo das mensagens da fila real que não são resumo nem "no ar" (ex.: "Pinterest pronto"): `"aviso"` (heurística `TIPOS_POR_TEXTO`); a validação dura do enviador (`TIPOS_PERMITIDOS`, rodada 1) ainda só aceita 3 tipos — ver seção 8 | `whatsapp_local/fila_pc.py` | `TIPO_PADRAO`, `tipo_da_mensagem` |
| Na volta (pasta → lista) mensagem sem `enviar_apos` sai com `"enviar_apos": null` (não sei se o plantão tolera; hoje o arquivo real está `[]`) | `whatsapp_local/fila_pc.py` | `para_lista` |
| `avisos_enviados.json` guarda o NOME DO ARQUIVO do item (`arquivo`); sem `arquivo`, o id | `whatsapp_local/fila_pc.py` | `chave_do_aviso` |
| `pronta_para_enviar` também segura a madrugada (não só `enviar_apos`), porque "de madrugada nada vai para o WhatsApp" | `whatsapp_local/fila_pc.py`, `enviador.py` | `pronta_para_enviar(..., bloquear_madrugada=)` |
| `fundo2` do reel = fundo misturado 25 % com o verde escuro (`#0C361D`), não o `#12A850` puro ("ou equivalente" da tarefa; contraste do branco) | `scripts/reel_futebol_arte.py` | `ESTILO_PADRAO["cores"]["fundo2"]` |
| Config do radar: `rockstar_newswire` opcional (só o GTA tem); `video_reutilizavel: true` exige `nota_uso` (regra da tarefa F); chaves fora da §4.10 não são erro (saem em `chaves_desconhecidas`) | `radar_fontes/esquema_radar.py` | `OPCIONAIS`, laço do `youtube` em `validar_config_radar` |
| Linha do `ui.py` com ` \| ` dentro do texto (nome de grupo) é recomposta como texto (marcada `ambiguo`) | `scripts/ui_dump.py` | `ler_linha_ui` |
| `ZONA_LINK = (140, 1500, 940, 1640)` é o retângulo da §5-D e entra 70 px nos 350 px da base; o teste confere os valores da tabela e que ele fica abaixo da `ZONA_ENQUETE`, não `dentro_da_zona_segura` | `hpbase/testes/test_marca.py` | `test_zonas_seguras_do_story` (ver seção 8) |


#### D

| Suposição | Arquivo | Onde trocar |
|---|---|---|
| `ZONA_LINK` (140,1500)-(940,1640) desce 70 px além da zona segura (1570). Mantive o valor de `marca.py` como está (é a verdade da §4.6); o contorno é o único elemento que entra nos 350 px da base. | `scripts/story_artes_base.py` | `ZONA_LINK = tuple(marca.ZONA_LINK)` (só muda se mudar em `hpbase/marca.py`) |
| No GTA, o `*destaque*` sai em ciano `#46E1EB` (extra do canal), porque o título inteiro já é o degradê rosa→laranja e rosa-sobre-rosa não destacaria nada. | `scripts/story_artes_canais.py` | `ESTILOS["gta"]["destaque"]` |
| Filmes: com `*destaque*` na chamada/pergunta uso a **variação escura** (caixa preta, contorno amarelo, texto branco, destaque amarelo); sem destaque, a caixa amarela com contorno preto e texto preto (amarelo sobre amarelo não lê). | `scripts/story_artes_modelos.py` | `titulo()`: `if caixa.get("escuro") and tem_destaque` |
| Receitas: a chamada e a pergunta vão na **faixa amarela** (DM Serif, texto escuro) e o `*destaque*` vira um sublinhado laranja (laranja sobre amarelo dá 2,0:1 e reprovaria o WCAG). Regra geral: se a cor de destaque não lê sobre a superfície, vira sublinhado. | `scripts/story_artes_modelos.py` | `titulo()`: `if superficie is not None and marca.contraste(cor_dest, superficie) < 4.5` |
| Carros: rótulo, CTA e selo "HP" em etiqueta (paralelogramo) vermelha `#E61E2D` com texto branco — contraste 4,58:1, passa por pouco. | `scripts/story_artes_canais.py` | `ESTILOS["carros"]["pilula"]`, `["cta"]`, `selo_hp()` (ramo `carros`) |
| Cor de clube escura (ex.: marinho) no Futebol é clareada (mistura com branco) só nos textos destacados até dar 4,5; a pílula/CTA ficam na cor pura com texto branco ou preto (o que ler melhor). | `scripts/story_artes_canais.py` | `estilo()`: `clarear_ate_ler` / `legivel_sobre` |
| Destinos: a pílula "IDA E VOLTA" aparece no `maissobre` quando `dado_forte.valor` contém "R$" (`"ida_volta": false` no spec esconde). | `scripts/story_artes_modelos.py` | `modelo_maissobre()`: `if est["canal"] == "destinos" and "R$" in df["valor"]` |
| Tamanho dos cartões: chamada normal 860×820 (y 352–1172); compacta 520×550 (y 350–900); miniatura do maissobre 320×348; fotos do "você prefere" 410×308. O enunciado só fixa a largura (~860 / ~520) e o y da compacta. | `scripts/story_artes_modelos.py` | constantes dentro de `modelo_chamada`, `modelo_maissobre`, `modelo_interacao` |
| Limites que o enunciado não dá: rótulo ≤ 22, CTA ≤ 24, `dado_forte.valor` ≤ 14, legenda ≤ 48, crédito ≤ 60 caracteres. | `scripts/story_artes_base.py` | `LIMITES` |
| `figurinhas` padrão: chamada e maissobre `["link"]`; interacao `["enquete"]` (e a enquete é sempre incluída no interacao). `maissobre` com enquete é recusado (não há lugar). | `scripts/story_artes_base.py` | `FIGURINHAS_PADRAO`, `normalizar_spec()` |
| `foco`: fração 0–1 da capa; valores > 1 são lidos como pixels da capa original. | `scripts/story_artes_base.py` | `enquadrar()` |


#### F0

| Suposição | Arquivo | Onde trocar |
|---|---|---|
| `video_reutilizavel` só existe para `futebol`, `filmes` e `gta` (regra F ao pé da letra); vídeo de montadora (`carros`) vira `false` com aviso. Se o Antônio quiser reutilizar vídeo oficial de montadora, basta acrescentar `"carros": "<nota de uso>"` | `radar_fontes/verificar_fontes.py` | constante `NOTA_USO_PADRAO` (e `video_reutilizavel()` lê dela) |
| `peso` padrão quando a entrada não traz: 1.5 oficial, 1.0 não oficial (o Rockstar de `radar_gta.json` tem 1.5) | `verificar_fontes.py` | função `_peso` |
| `filtrar` padrão para RSS quando a entrada não traz: `not oficial` (sala de imprensa não filtra; site de notícia filtra, como IGN/GameSpot da fixture) | `verificar_fontes.py` | função `verificar_entrada_rss` |
| A lista de sites de notícia é um pente-fino heurístico (nome, @handle, rótulos do domínio; token com até 5 letras só casa exato) — não substitui o julgamento de F1–F3, só impede `oficial: true` óbvio errado | `verificar_fontes.py` | constante `SITES_NOTICIA` e função `e_site_noticia` |
| `verificado_em` é ISO 8601 com fuso do `hoje` injetado (na CLI, Brasília: `2026-10-01T01:15:56-03:00`) | `verificar_fontes.py` | função `_carimbo` |
| O feed do YouTube não precisa ter vídeo recente (canal oficial pode postar pouco): só o título, o XML e o `yt:channelId` (com ou sem prefixo UC) contam | `verificar_fontes.py` | função `_verificar_feed_youtube` |
| Sem `nome`/`--nome` (CLI `canal` só com @handle) não há conferência de título: a prova é o id que a própria página declara. Com `nome` (caso de `verificar` e `candidatos`), título que não bate descarta | `verificar_fontes.py` | função `verificar_canal_youtube` (bloco `nome and not nomes_batem`) |
| Entradas já em `descartadas` não são re-tentadas por `verificar_arquivo` (ficam como estão, sem duplicar) | `verificar_fontes.py` | função `verificar_lista` (laço `descartadas`) |
| Código de saída de `verificar`: 1 quando alguma entrada caiu nesta rodada (além de erro de leitura); `candidatos`: 1 quando alguém caiu ou linha inválida | `verificar_fontes.py` | funções `_cmd_verificar` e `_cmd_candidatos` |
| `evidencia` quando a entrada não traz: a URL do feed (RSS) ou a página `@handle` (YouTube) — F1–F3 devem preencher com a página oficial onde acharam o id/feed | `verificar_fontes.py` | funções `verificar_entrada_rss` / `verificar_entrada_youtube` |


#### F1

| Suposição | Arquivo | Onde trocar |
|---|---|---|
| `peso`: clubes 1.5 (como o Rockstar da fixture), CONMEBOL 1.2, Sudamericana 1.3, FIFA 1.0 (canal global, pouco Brasileirão) | `radar_fontes/futebol_fontes_novas.json` | campo `peso` de cada entrada |
| `filtrar: true` só no feed da CONMEBOL (espanhol, todas as competições) e no da Take-Two (cobre 2K/Zynga); feeds de clube `filtrar: false` | `futebol_fontes_novas.json`, `gta_fontes_novas.json` | campo `filtrar` |
| `nome` das entradas foi escolhido para bater com o título do canal na reverificação (`nomes_batem`: um contém o outro): "Chapecoense (ChapeTV)", "CBF (Confederação Brasileira de Futebol)", "CONMEBOL Sudamericana BR". Se trocar o nome, mantenha um pedaço do título | `futebol_fontes_novas.json` | campo `nome` |
| CBF @brasil (UCdQuDaRww5NkKpQQ1BJBWww) é o mesmo canal que a tabela chama "CBF TV"; @LibertadoresBR pode ser o "CONMEBOL Libertadores" da tabela (ou a tabela tem o canal em espanhol). Marquei `ja_existe: true` + `nota_conferir` em vez de repetir | `futebol_fontes_novas.json` | entradas com `ja_existe` |
| FIFA, Sudamericana BR e CBF: a evidência é a própria página do canal (selo verificado na busca do YouTube + links do canal para o site da entidade), porque fifa.com não expõe o link sem JS e cbf.com.br não abre daqui | `futebol_fontes_novas.json` | campo `evidencia` |
| Coritiba: evidência são os links da página do canal (coritiba.com.br, sociocoxa.com.br); o site oficial é só JS | `futebol_fontes_novas.json` | entrada "Coritiba" |
| `video_reutilizavel: true` também para CONMEBOL/FIFA (liga/federação), pela regra da tarefa F; se o Antônio quiser só clubes/CBF, trocar para `false` | `futebol_fontes_novas.json` | campo `video_reutilizavel` |
| Take-Two: o feed foi achado pelo caminho padrão dos sites de RI hospedados em `ir.take2games.com` (a página take2games.com/ir/press-releases não declara `<link rss>`) | `gta_fontes_novas.json` | entrada "Take-Two Interactive (press releases)" |

Observações sobre a ferramenta da F0 (não é bug; não alterei `verificar_fontes.py`):
1. A 6ª coluna de `candidatos <arquivo.txt>` é `channel_id`; a tarefa F1 pediu a 6ª coluna como `resultado`. Por isso `futebol_candidatos.txt` é documentação da pesquisa (cabeçalho avisa) e **não** entrada da CLI; o JSON foi montado chamando `verificar_lista` direto (com `evidencia` por entrada) e provado com `verificar`.
2. `verificar --gravar` reconstrói cada entrada só com as chaves de 4.10 + `verificado_em/evidencia/verificado_por`: as marcas `ja_existe`/`nota_conferir` **somem** ao regravar. Quem for mesclar no `07 Canais\radar\` deve olhar essas marcas **antes** de rodar `--gravar`.
3. A CLI não confere o selo "verificado" do YouTube; eu anotei o selo (quando aparece na busca) no campo `evidencia`.
4. Como a F0 avisou, o feed `feeds/videos.xml` responde 404 nesta nuvem: tudo saiu `pagina_canal`; no PC, `verificar --gravar` promove para `feed`.


#### F2

| Suposição | Arquivo | Onde trocar |
|---|---|---|
| `peso`: canais BR oficiais 1.5 (como o Rockstar da fixture); streamings/estúdios globais 1.2; Paramount Plus global, Lucasfilm, Lionsgate, A24 e AdoroCinema 1.0 | `radar_fontes/filmes_fontes_novas.json` | campo `peso` de cada entrada |
| `filtrar: true` nos feeds que misturam assunto (Marvel = quadrinhos/games; Apple Newsroom BR = toda a Apple; Disney corporativa; Amazon; Google News); `filtrar: false` só no Apple TV Press | `filmes_fontes_novas.json` | campo `filtrar` |
| Os dois "via Google News" entraram em `rss` porque é um RSS 2.0 comum que a ferramenta prova. Se o Antônio preferir o coletor próprio do radar, o equivalente é `google_news: [{"q": "site:omelete.com.br", "lingua": "pt"}, {"q": "site:adorocinema.com", "lingua": "pt"}]` (mesma busca; não coloquei porque o JSON de entrega só tem `rss`/`youtube`) | `filmes_fontes_novas.json` | entradas "Omelete (via Google News)" e "AdoroCinema (via Google News)" |
| Canais globais em inglês (Netflix, Prime Video, HBO Max, Disney Plus, Paramount Plus, Apple TV) entraram além dos BR da tabela: trailer global costuma sair horas antes do BR. Se virar ruído, tirar ou baixar o peso | `filmes_fontes_novas.json` | entradas com evidência "canal global" |
| `nome` das entradas foi escolhido para bater com o título do canal (`nomes_batem`): "Disney Plus" (não "Disney+"), "Sony Pictures Entertainment", "Lionsgate Movies", "Walt Disney Studios BR". Se trocar o nome, mantenha um pedaço do título | `filmes_fontes_novas.json` | campo `nome` |
| Paramount Brasil (@ParamountBrasil, UCgqD3GdUEfupsdY1kmFLIrw) é o mesmo canal que a tabela chama "Paramount Pictures Brasil" (renomeado). Marquei `ja_existe: true` + `nota_conferir` em vez de repetir | `filmes_fontes_novas.json` | entrada "Paramount Brasil" |
| Star Wars (@StarWars) conta como canal da Lucasfilm (é o canal principal do estúdio; @Lucasfilm é o institucional, pequeno) | `filmes_fontes_novas.json` | entradas "Star Wars" e "Lucasfilm" |
| Evidência "busca do YouTube + selo verificado" vale quando o site oficial não expõe o link no HTML (sites em JavaScript) — a prova dura é sempre o `externalId` que a própria página do canal declara | `filmes_fontes_novas.json` | campo `evidencia` |

Observações sobre a ferramenta da F0 (não alterei `verificar_fontes.py`):
1. **Limitação (não é bug de código, é formato fora do padrão):** `analisar_data()` lê RFC 2822 e ISO 8601; o feed da Netflix usa `<pubDate>30 de setembro de 2026</pubDate>` (pt_br) e `<pubDate>01 October 2026</pubDate>` (en), e cai como "nenhum item com data". Contornei registrando em `descartadas` com o motivo exato. **Patch sugerido para a F0/sessão principal** (não aplicado; 1 teste novo com o feed gravado): em `analisar_data`, antes de devolver `None`, tentar `re.match(r"(\d{1,2})(?: de)? ([a-zç]+)(?: de)? (\d{4})", t.lower())` com um dicionário `{"janeiro"/"january": 1, …, "dezembro"/"december": 12}` e devolver `datetime(ano, mes, dia, tzinfo=timezone.utc)`. Com isso o feed da Netflix (pt_br) entra como `oficial: true, filtrar: false, peso: 1.5` — é a melhor fonte em português do canal.
2. A 6ª coluna de `candidatos <arquivo.txt>` é `channel_id`; a tarefa F2 pediu a 6ª coluna como `resultado`. Por isso `filmes_candidatos.txt` é documentação da pesquisa (o cabeçalho avisa) e **não** entrada da CLI; o JSON foi montado chamando `verificar_lista` direto (com `evidencia` por entrada) e provado com `verificar`.
3. `verificar --gravar` reconstrói cada entrada só com as chaves de 4.10 + `verificado_em/evidencia/verificado_por`: as marcas `ja_existe`/`nota_conferir` **somem** ao regravar. Olhar a entrada "Paramount Brasil" **antes** de rodar `--gravar`.
4. O feed `feeds/videos.xml` responde 404 nesta nuvem: tudo saiu `pagina_canal`; no PC, `verificar --gravar` promove para `feed`.


#### F3

| Suposição | Arquivo | Onde trocar |
|---|---|---|
| Vídeo de montadora não é reutilizável (`video_reutilizavel: false` em todos os 21 canais), seguindo a regra da tarefa F e a `NOTA_USO_PADRAO` da F0 (sem chave `carros`). Se o Antônio quiser reutilizar vídeo oficial de montadora (com crédito), acrescentar `"carros": "<nota>"` na ferramenta e mudar o campo nas entradas | `radar_fontes/carros_fontes_novas.json` (campo `video_reutilizavel` de cada canal) e `radar_fontes/verificar_fontes.py` (`NOTA_USO_PADRAO`) | entradas `youtube[*]` |
| `filtrar: false` em 5 dos 6 feeds (sala de imprensa só fala da própria marca) e `true` só no BMW Group PressClub Brazil (mistura BMW, MINI e Motorrad). Hyundai CSA News cobre a Hyundai na América Central/Sul (só Hyundai, por isso `false`) | `carros_fontes_novas.json` | `rss[*].filtrar` |
| Selo de canal verificado do YouTube vale como prova de "canal da própria marca" quando o site oficial bloqueia robô (Peugeot BR, Audi BR, Ford BR, Nissan, Honda, Chevrolet, Jeep, BYD Global, Ram Trucks, Nissan Brasil, MitsubishiMotorsTV). Sem selo E sem link no site oficial = descartado | `carros_fontes_novas.json` | `youtube[*].evidencia` diz qual prova foi usada |
| "Renault Group" (canal corporativo: Renault, Dacia, Alpine) entrou como canal global da Renault porque renault.com redireciona para renaultgroup.com, que linka só ele; o @Renault (verificado, 3,69 mil) ficou em dúvida | `carros_fontes_novas.json` | entrada "Renault Group" / descartada "Renault (global, @Renault)" |
| Para GWM Global a URL é o @handle que a própria página do canal declara (@greatwallmotor1853), não um nome bonito | `carros_fontes_novas.json` | entrada "GWM Global" |
| Peso padrão 1.5 (oficial), como na fixture `radar_gta.json` (Rockstar 1.5) | `carros_fontes_novas.json` | `peso` de cada entrada |


#### F4

| Suposição | Arquivo | Onde trocar |
|---|---|---|
| As marcas `ja_existe`/`nota_conferir` valem a pena mesmo não sendo de 4.10, por isso foram repostas depois do `--gravar`. Se o Antônio quiser o JSON "puro", é só apagar essas duas chaves das 4 entradas (nada lê essas marcas por código) | `futebol_fontes_novas.json` (2), `filmes_fontes_novas.json` (1), `gta_fontes_novas.json` (1) | entradas `youtube[*]` com `ja_existe` |
| "GWM Global" é oficial (`oficial: true`), apesar de a ferramenta dizer o contrário a cada `--gravar` (falso positivo `motor1`) | `carros_fontes_novas.json` | entrada "GWM Global"; correção da ferramenta em 8 |
| O agrupamento das 87 descartadas por motivo é leitura minha do texto livre de cada `motivo` (ex.: Vasco entrou em "sem feed", não em "bloqueio", porque o feed deu 404 e só a home deu 403); os grupos somam exatamente 18/21/46/2 | `radar_fontes/RELATORIO_FONTES.md` | tabelas "Descartadas … por motivo" |
| A lista da Série A 2026 vem do ge + Wikipedia (idênticas), não da CBF | `RELATORIO_FONTES.md`, seção "Canal futebol" | trocar a fonte citada quando o PC confirmar em cbf.com.br |
| Pasta do projeto no PC para os comandos = `G:\Meu Drive\Hypado\06 Projeto` (como no `radar_fontes/LEIA.md`) | `RELATORIO_FONTES.md`, seção da nota do feed | bloco de comandos |
| Nenhuma validação por `esquema_radar.py` (não existe); a validação é o script desta tarefa (critérios em 1.1) | — | se o A3 entregar o esquema depois, rodar nos 4 JSONs |

Herdadas de F1–F3 e ainda válidas (não repetidas aqui): pesos (clubes 1.5, CONMEBOL 1.2, Sudamericana 1.3,
FIFA 1.0; BR 1.5, globais 1.2, Paramount Plus/Lucasfilm/Lionsgate/A24/AdoroCinema 1.0; montadoras 1.5),
`filtrar` por feed, nomes escolhidos para bater com o título do canal, Google Notícias como `rss` para
Omelete/AdoroCinema, "Renault Group" como canal global da Renault, `video_reutilizavel: false` em carros.


#### E1

| Suposição | Arquivo | Onde trocar |
|---|---|---|
| `DispositivoAmbiguo` (0 ou 2+ aparelhos, serial pedido ausente/`unauthorized`) sai com **código 4** ("precisa do Antônio": ligar/escolher/aceitar a depuração); o enunciado só fixa o 4 para "bloqueado" | `scripts/story_dispositivo.py` | `DispositivoAmbiguo.codigo` |
| Tela travada = `dumpsys window` com `mShowingLockscreen=true`, `mDreamingLockscreen=true`, `isKeyguardShowing=true`, `mKeyguardShowing=true` ou linha `showing=true` (KeyguardServiceDelegate); tela acesa = `dumpsys power` `mWakefulness=Awake` (sem o campo: `Display Power: state=ON`; sem nada: considera acesa). Nomes mudam por versão do Android | `scripts/story_dispositivo.py` | `_RX_TRAVADA`, `_RX_ACORDADO`, `Dispositivo._travada`, `_acesa` |
| `wm dismiss-keyguard` tira só a tela de bloqueio por deslizar (sem PIN); com PIN continua travada e o script para | `scripts/story_dispositivo.py` | `Dispositivo.tela_acesa_e_destravada` |
| `am start … -p com.instagram.android` (`-p` = `Intent.setPackage`, como o enunciado escreve); a rodada 1 passava o pacote como argumento posicional | `scripts/story_dispositivo.py` | `Dispositivo.abrir_link` |
| O `adb shell` junta os argumentos com espaço SEM escapar (código do adb: "We don't escape here, just like ssh(1)"), e o shell do aparelho lê de novo: por isso `input text` recebe `faz\?` e chega `faz?`; `& $ \| ; < > ( ) * [ ] { } ~ # ! ^` ganham barra; aspas são removidas (como o `digitar.py`) | `scripts/story_dispositivo.py` | `texto_para_input`, `_PERIGOSOS_SHELL` |
| ids de tela de login que também param (`login_username`, `login_password`, `password`, `login_button`, `confirmation_code`, `security_code`, `verification_code`) são palpite; o campo com `password="true"` é o critério seguro | `scripts/story_dispositivo.py` | `IDS_TELA_LOGIN`, `detectar_aviso` |
| Teclado de acento = ADBKeyBoard, IME `com.android.adbkeyboard/.AdbIME`, detectado por `ime list -s` + `settings get secure default_input_method`, texto por `am broadcast -a ADB_INPUT_B64 --es msg <base64>` | `scripts/story_dispositivo.py` | `TECLADO_ADB`, `Dispositivo.teclado_acento`, `_digitar_acento_real` |
| Pasta da arte no aparelho `/sdcard/Pictures/HP`; dump em `/sdcard/ui.xml` (o mesmo do `ui.py` do PC); foto em `/sdcard/hp_tela.png` | `scripts/story_dispositivo.py` | `PASTA_FOTOS`, `ARQUIVO_DUMP`, `ARQUIVO_FOTO` |
| URI da chamada ao MediaStore = `content://media/external/file` (qualquer `content://media/...` resolve a authority `media`); plano C `scan_volume` com `external_primary`; conferência pelo `content query` em `images/media` por `_display_name` | `scripts/story_dispositivo.py` | `Dispositivo.planos_mediastore`, `midia_indexada` |
| Bounds do dump real DERIVADOS do centro (texto: 24 px/letra × 56; clicável: 140×140; contêiner centrado: largura toda; ícone: 48×48; encolhidos na borda para o centro não mudar) | `scripts/testes/adb_falso.py` | `bounds_estimados` |
| Ids e textos das telas sintéticas que NÃO existem no `story_post_seletores.py` são inventados (`row_user_container`/`row_user_textview` da lista de contas, `direct_share_sheet_add_to_story` da folha Send, `asset_item` da bandeja com textos `POLL`/`LINK`/`COUNTDOWN`, `link_sticker_url_edit_text`, `highlight_title`, `igds_headline_*` do aviso, `login_*`) | `scripts/testes/adb_falso.py` | `telas_sinteticas` (o E4 troca pelos dumps reais) |
| `ler_zonas` trata a arte (1080x1920) como ocupando a tela inteira; se o editor do Instagram mostrar a arte 9:16 enquadrada numa tela 20:9 (barras), passe `area=` com os bounds do nó da mídia lido no dump | `scripts/story_fila_v2.py` | `ler_zonas(arte, tela, area=None)` |
| Rótulo da figurinha de link e título da contagem até 30 caracteres (`LIMITE_ROTULO`); rótulo padrão "Ver post" | `scripts/story_fila_v2.py` | `LIMITE_ROTULO`, `ROTULO_LINK_PADRAO` |
| Figurinha `contagem` leva `data` (AAAA-MM-DD) e `rotulo` (título), chaves que o esquema do enunciado não lista; `de_lote_estaticos` calcula `data` = dia do lote + N dias e guarda `dias` | `scripts/story_fila_v2.py` | `_validar_figurinha` (ramo `contagem`), `de_lote_estaticos` |
| Item `vídeo novo:` do lote vira `compartilhar_post` com `link: null` + `pendencias` (o lote não tem o link do post do vídeo); `validar_v2` recusa o pedido até o link entrar (`links={"12:10": url}` ou campo `link` no item). A arte estática do item fica guardada em `arte` para o E2 decidir se usa | `scripts/story_fila_v2.py` | `de_lote_estaticos` (ramo `compartilhar_post`), `_validar_story` |
| Tema que não é `vídeo novo:`, `comenta aí` nem `contagem N dias` e sem `tipo` explícito é RECUSADO (não adivinho o tipo) | `scripts/story_fila_v2.py` | `_tipo_do_tema`, `de_lote_estaticos` |
| Pedido vindo do lote: `post_id` = `<canal>_<data>_estaticos`, `titulo` = `Estáticos de <data>`, `link`/`publicado_em` nulos (aceitos pelo `validar_v2`); conta = `@` do `interativo.rede` ou o handle de `marca.CANAIS[canal]` | `scripts/story_fila_v2.py` | `pedido_de_lote`, `_handle_do_canal` |
| `quando` sem fuso é Brasília (`hpbase.FUSO`); ISO com fuso é convertido para Brasília na normalização, mas `publicado_em` original não é reescrito | `scripts/story_fila_v2.py` | `normalizar_quando`, `migrar_v1` |


#### E2

| Suposição | Arquivo | Onde trocar |
|---|---|---|
| Ids do link, da lista de contas, da folha Send, do seletor de destaque, da prévia da arte e da bandeja (`IDS_PALPITE`) e os textos extras (`TEXTOS_EXTRA`: "Customize sticker text", "New", "Add", "Story preview") são palpite; o fluxo tem plano B por classe/texto (`EditText` focado, texto "URL", etc.) | `scripts/story_fluxos.py` | `IDS_PALPITE`, `TEXTOS_EXTRA` |
| Depois do `done_button` a figurinha aparece como um nó NOVO dentro da área da arte (entre 0,2 % e 80 % da área); se o Instagram não expuser a figurinha no dump, o fluxo não arrasta e avisa (o story sai com a figurinha onde o app a pôs) | `scripts/story_fluxos.py` | `figurinha_nova`, `posicionar_figurinha` |
| A arte aparece no editor dentro de um nó de prévia (`camera_preview`/"Story preview") com ≥ 40 % da tela; sem ele, a conversão das zonas usa a tela inteira (arte 9:16 numa tela 20:9 pode errar o y) | `scripts/story_fluxos.py` | `area_da_arte` |
| Avançar story = tocar a 92 % da largura e 30 % da altura dos bounds da mídia (`reel_viewer_media_container`); no máximo 40 avanços | `scripts/story_fluxos.py` | `_ponto_avancar`, `MAX_STORIES_AVANCAR` |
| Confirmação do destaque = aparece "Added to"/"Adicionado" OU a lista de destaques sumiu (como na rodada 1); criar destaque novo = "New" → campo → nome → "Add"/"Done" | `scripts/story_fluxos.py` | `adicionar_ao_destaque`, `TEXTOS_EXTRA["destaque_*"]` |
| Calendário da contagem: `android:id/next` até o mês/ano certo e dia por texto/desc ("19 November 2026"); o DatePicker padrão pode não expor os dias no dump — aí o fluxo para com a mensagem de coletar a tela | `scripts/story_fluxos.py` | `escolher_data`, `_achar_dia`, `_mes_ano_na_tela` |
| Chave do estado: `compartilhar_post` = `post_id` (igual à rodada 1); os outros = `post_id#tipo@AAAAMMDDHHMM` | `scripts/story_fluxos.py` | `chave_do_story` |
| Timestamp da API (`2026-10-01T13:05:10+0000`) comparado com `desde` = hora em que o item começou (antes da troca de conta) | `scripts/story_fluxos.py` | `_dt`, `rodar_item_v2` (variável `inicio`) |
| Desligar o emulador = `adb emu kill` (o PC pode injetar `desligar_emulador=` com o `desligar_emulador.ps1`) | `scripts/story_fluxos.py` | `desligar_emulador_padrao`, `rodar_pedido_v2(desligar_emulador=)` |
| Erro de aparelho/fluxo conta como tentativa só enquanto o story não foi registrado; parada por aviso e "já feito" não contam | `scripts/story_fluxos.py` | `Estado.registrar_falha`, `rodar_item_v2` |
| A coleta grava a parada (`PARADO_AVISO_META.json`) ao ver login/aviso, como o story_post faria (conservador) | `scripts/story_coletar_telas.py` | `main` (passe `gravar_parada=None` para só parar sem gravar) |
| Tela "menu +" e "busca link" não têm sintética no E1: o índice não aponta substituta para elas | `scripts/story_coletar_telas.py` | `TELAS[*]["sintetica"]` |


#### B

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


#### C

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

## 7. Depende do Antônio (token, permissão, clique, instalação) — passo a passo

Consolidado das seções 6 dos relatórios. O que não está aqui não precisa dele.

#### A1

Nenhum token, permissão, clique ou instalação novos. Para a próxima integração no PC: (1) conferir no `publicador_meta.py` as duas mensagens da seção 5 e colar o texto exato em `_validar_tipo`; (2) se já existir `H:\HypadoLocal\esteira_sombra\config.json` da rodada 1 com `pasta_scripts` fixo, apagar a chave para o padrão novo (`06 Projeto\scripts`) valer.


#### A2a

Nenhum token, permissão, clique ou instalação novos para esta tarefa. Na próxima integração no PC (para leigo):

1. Abrir o PowerShell em `G:\Meu Drive\Hypado\06 Projeto\app\hp_studio_nuvem` e rodar `python -m metricas chaves`. Ele lista, por conta e rede, o **nome** da chave e em que arquivo está (nunca mostra o valor). Tudo `ok` = pode coletar. `sem_token` com `falta: id` = o `publicador_meta.py` ainda não gravou o id daquela conta no `meta_tokens_meta.json` (rode o `publicador_meta.py` uma vez) ou falta o `facebook_paginas.json` (`hp publicar facebook-token`).
2. YouTube continua `nao_autorizado` até o Google aprovar a auditoria; quando aprovar, trocar `"autorizado": true` no `contas.json` de cada canal e rodar `hp publicar youtube-autorizar --canal <canal>` (hoje só o GTA tem refresh token).
3. Se existir `H:\HypadoLocal\metricas\contas.json` copiado na rodada 1, apagar ou recopiar o novo exemplo (o antigo tem `versao_graph: v21.0` e só 2 arquivos em `arquivos_segredo`; os grupos novos continuam valendo, mas o Facebook ficaria em v21.0).
4. Esteira: `python -m esteira iniciar` grava os 12 modelos reais no `config.json` (se o `config.json` da rodada 1 existir com `comandos` antigos — `--saida`, `--srt`, `--pedido` — apagar a chave `comandos` dele).


#### A2b

Nenhum token, permissão ou clique. Na próxima cópia para o PC (leigo):

1. Copiar `scripts\story_post_lote.py` para `G:\Meu Drive\Hypado\scripts\` (ao lado do `story_post.py`) — sem ele o `story_post.py` novo não abre (`import story_post_lote`).
2. Copiar `app\hp_studio_nuvem\esteira\pedido_pc.py` junto com o `esteira\pedido.py` novo para `06 Projeto\app\hp_studio_nuvem\esteira\`.
3. Conferir que `G:\Meu Drive\Hypado\06 Projeto\config.json` existe (é o de sempre); em outra máquina, `set HP_CONFIG_PC=<caminho do config.json>`.
4. Conferir a enquete do dia antes das 16h: `python scripts\story_post_lote.py lotes\2026-10-01_estaticos.json` — tem que terminar sem "NÃO DÁ".


#### A3

Nenhum token, permissão, clique ou instalação. Na próxima cópia para o PC (leigo):

1. Copiar `app\hp_studio_nuvem\whatsapp_local\fila_pc.py`, `config.py`, `montagem.py`, `tarefas.py`, `enviador.py` para `06 Projeto\app\hp_studio_nuvem\whatsapp_local\` (os 5 juntos).
2. Conferir, no WhatsApp, que os 5 grupos da lista "HP | Grupos" têm EXATAMENTE os nomes `HP | Futebol ⚽`, `HP | Filmes 🎬`, `HP | Receitas 🍔`, `HP | Carros 🏎️`, `HP | Destinos ✈️` (com o emoji) e colocar esses nomes em `H:\HypadoLocal\whatsapp_local\grupos_permitidos.json` (`"grupos": [...]`), senão o enviador rejeita.
3. Responder as 3 perguntas da seção 8 (cabeçalho dos canais, tipo "aviso", link do Facebook) — todas são 1 linha para trocar.
4. Teste sem mandar nada: `cd "G:\Meu Drive\Hypado\06 Projeto\app\hp_studio_nuvem"` e `python -m whatsapp_local.fila_pc importar --agora "2026-10-02 08:00" --so-mostrar` (mostra o que entraria na pasta) e `python -m whatsapp_local.fila_pc avisos --agora "2026-10-02 08:00"` (mostra os avisos "no ar" que ainda não saíram).
5. Copiar `scripts\ui_dump.py` para `G:\Meu Drive\Hypado\scripts\` e `radar_fontes\esquema_radar.py` para onde o radar mora (serve para conferir uma config nova: `python esquema_radar.py "G:\Meu Drive\Hypado\07 Canais\radar\gta.json"`).
6. Depois de cada integração rodar `python -m pytest -q tests` na raiz do repositório (é o teste de contrato).


#### D

- **Nada para rodar.** No PC só precisa de `pillow` e `numpy` (já usados pelos `posts_*.py`).
- Para as fontes saírem exatas no PC: nada a fazer — `marca.fonte()` acha `06 Projeto\marca\fontes` e `C:\Windows\Fonts` (Bauhaus 93, Segoe UI Black/Bold/Black Italic, Bahnschrift). Na nuvem elas são substituídas (Bauhaus → Anton, Segoe → Barlow, Bahnschrift → Barlow Condensed).
- **Conferir de olho** (passo a passo): `python scripts\story_artes.py exemplos C:\temp\stories` → abrir `C:\temp\stories\_prancha_story.jpg` e os 18 JPG. O que olhar está em §9.


#### F0

- Nada obrigatório. Opcional no PC: se `python radar_fontes\verificar_fontes.py rss <url>` falhar com erro de
  certificado/HTTPS (antivírus), ou rodar com `--curl` (usa o `curl.exe` do Windows, sem janela), ou
  `pip install truststore` uma vez (a ferramenta passa a usar o cofre de certificados do Windows sozinha).


#### F1

1. **Conferir os dois `ja_existe`** antes de mesclar: abrir `07 Canais\radar\futebol.json` e comparar o `channel_id` de "CBF TV" com `UCdQuDaRww5NkKpQQ1BJBWww` e o de "CONMEBOL Libertadores" com `UCyuLjFPzlkMSYJpIpY8M6qA`. Igual → ignorar a entrada nova (ou só atualizar `url`/`nome`); diferente → decidir se troca ou se mantém os dois.
2. **Mesclar** os `rss` e `youtube` de `radar_fontes\futebol_fontes_novas.json` e o `rss` de `gta_fontes_novas.json` no `07 Canais\radar\<canal>.json` (não fiz: os arquivos do PC não estão no repositório). Antes, no PC: `python radar_fontes\verificar_fontes.py verificar radar_fontes\futebol_fontes_novas.json --gravar` (promove para `feed`; se der erro de certificado, `--curl`).
3. **Testar do PC o que não abriu daqui** (passo a passo): abrir no navegador `https://www.cbf.com.br/noticias`, apertar Ctrl+U e procurar `rss` ou `feed`; se achar um endereço, rodar `python radar_fontes\verificar_fontes.py rss <endereço>`. Se não achar, tentar `https://www.cbf.com.br/rss` e `https://www.cbf.com.br/feed`. Mesma coisa para Flamengo (`https://www.flamengo.com.br/feed/`), Vasco (`https://vasco.com.br/feed/`) e Grêmio (`https://gremio.net/feed/`), que bloquearam ou não responderam ao robô da nuvem.


#### F2

1. **Conferir o `ja_existe`** antes de mesclar: abrir `07 Canais\radar\filmes.json` e comparar o `channel_id` de "Paramount Pictures Brasil" com `UCgqD3GdUEfupsdY1kmFLIrw`. Igual → ignorar a entrada nova (ou só atualizar `nome`/`url` para "Paramount Brasil" / @ParamountBrasil); diferente → decidir se troca ou mantém os dois.
2. **Mesclar** os `rss` e `youtube` de `radar_fontes\filmes_fontes_novas.json` no `07 Canais\radar\filmes.json` (não fiz: os arquivos do PC não estão no repositório). Antes, no PC: `python radar_fontes\verificar_fontes.py verificar radar_fontes\filmes_fontes_novas.json --gravar` (promove para `feed`; se der erro de certificado, `--curl`).
3. **Testar do PC o que não abriu daqui** (passo a passo): abrir no navegador `https://press.paramountplus.com/` e `https://press.amazonstudios.com/`, apertar Ctrl+U e procurar `rss` ou `feed`; se achar um endereço, rodar `python radar_fontes\verificar_fontes.py rss <endereço>`. Se não achar, tentar `<site>/rss`, `<site>/feed` e `<site>/rss.xml`.
4. **Netflix em português:** decidir se aplica o patch do item 5.1 (quem aplica é a sessão principal/F0, não eu). Enquanto isso, o feed fica em `descartadas` com o motivo.


#### F3

- **Confirmar 5 canais BR sem prova** (1 clique cada: abrir o site oficial no navegador, ir ao rodapé, ver se o YouTube linkado é este): Caoa Chery → youtube.com/@CAOAChery (UCo3iqVlz3pzmXlSoipcAWEw); BMW Brasil → @BMWTVBrasil (UCNdmMv0UNG470K6YHYznwKA); Mercedes-Benz Brasil → @MercedesBenzBrasil (UC1yLUcwlC_f2vaSBoaOLcgg); Porsche Brasil → @PorscheBrasilOficial (UCBfvceulEkHn9XaFTJ1-ckA); Volvo Car Brasil → @VolvoCarBrasil (UCeoxJyBwpgNhAB8ZQEhyb9w). Se bater, copiar a linha do `carros_candidatos.txt` para um .txt no formato da CLI (`youtube|Nome|url|true|false|UC...`) e rodar `python radar_fontes\verificar_fontes.py candidatos esse.txt --canal carros`.
- **Fiat global:** abrir fiat.com no navegador e ver qual dos dois canais verificados "Fiat" o site linka (@fiat1253 = UCpQS0xnrCfJfdLHwTSQxOGA ou @Fiat = UC_nBvBIV0K6P5C3tA27Hwrg).
- **Salas de imprensa bloqueadas para robô** (Stellantis, Ford, GM, Volvo, Tesla, Mercedes Group, Kia Newscenter, Honda News BR, Mercedes BR, Nissan BR): no PC, abrir no navegador e procurar "RSS" no rodapé; se achar, testar com `python radar_fontes\verificar_fontes.py rss <url>` (ou `--curl`). Nenhuma delas abriu desta nuvem.
- Nada de token, permissão, instalação ou clique em Entrar/Aceitar.


#### F4

1. **Conferir as 4 `ja_existe` antes de mesclar** (abrir o `07 Canais\radar\<canal>.json` e comparar o `channel_id`):
   futebol — "CBF TV" × `UCdQuDaRww5NkKpQQ1BJBWww` (@brasil) e "CONMEBOL Libertadores" × `UCyuLjFPzlkMSYJpIpY8M6qA` (@LibertadoresBR);
   filmes — "Paramount Pictures Brasil" × `UCgqD3GdUEfupsdY1kmFLIrw` (@ParamountBrasil); gta — Rockstar é o mesmo
   da fixture (só confirmação). Igual → ignorar a entrada nova (ou atualizar nome/url); diferente → decidir se troca ou soma.
2. **Mesclar** os `rss` e `youtube` dos 4 JSONs de `radar_fontes\` nos `07 Canais\radar\<canal>.json` (não fiz: os
   arquivos do PC não estão no repositório). As entradas já estão no formato de 4.10; os campos extras
   (`verificado_em`, `evidencia`, `verificado_por`, `ja_existe`, `nota_conferir`) podem ir junto ou ser apagados
   — o `radar_hp.py` ignora chaves que não conhece? **Não sei**: se não ignorar, apagar os extras ao mesclar.
3. **Rodar no PC a verificação pelo feed** (promove os 53 canais de `pagina_canal` para `feed`): os 4 comandos
   `python radar_fontes\verificar_fontes.py verificar radar_fontes\<canal>_fontes_novas.json --gravar` (com
   `--curl` antes de `verificar` se der erro de certificado). Antes: olhar o item 1 (as marcas somem) e, depois,
   repor `oficial: true` no "GWM Global" (ou aplicar a correção de 8 primeiro).
4. **Tentar do PC o que não abriu daqui** (lista completa e passo a passo em `RELATORIO_FONTES.md`, seção "O que o PC
   deve tentar de novo"): cbf.com.br (lista da Série A + RSS), Flamengo/Vasco/Grêmio, press.paramountplus.com,
   press.amazonstudios.com, Stellantis/Ford/GM/Volvo/Tesla/Mercedes/Kia/Honda BR/Mercedes BR/Nissan BR.
5. **Confirmar com 1 clique os canais sem prova** (rodapé do site oficial → é este o YouTube?): Caoa Chery
   @CAOAChery, BMW Brasil @BMWTVBrasil, Mercedes-Benz Brasil @MercedesBenzBrasil, Porsche Brasil
   @PorscheBrasilOficial, Volvo Car Brasil @VolvoCarBrasil, Fiat global (@fiat1253 ou @Fiat). Ids nas
   `descartadas` de `carros_fontes_novas.json`; se bater, `youtube|Nome|url|true|false|UC...` num .txt e
   `python radar_fontes\verificar_fontes.py candidatos esse.txt --canal carros`.
6. Nada de token, permissão, instalação (opcional: `pip install truststore` no PC se o antivírus quebrar o HTTPS do Python).


#### E1

- **Celular real pelo cabo:** ativar "Opções do desenvolvedor" → "Depuração USB" e, ao plugar, tocar em **Permitir** no aviso "Permitir depuração USB deste computador?" (marcar "sempre"). Sem isso o `adb devices` mostra `unauthorized` e o script para com código 4 explicando. O script nunca toca em Permitir.
- **Celular travado:** o script para com `celular bloqueado: o Antônio desbloqueia` (código 4). Desbloquear à mão e rodar de novo; o script não digita PIN. Para o celular real, uma opção é deixar "Permanecer ativo" ligado nas opções do desenvolvedor enquanto estiver no cabo.
- **Parada por aviso:** `H:\HypadoLocal\emulador\PARADO_AVISO_META.json` só o Antônio apaga, depois de olhar o aparelho.
- **Acento real (opcional, desligado):** instalar e ativar o ADBKeyBoard — passo a passo na `LEIA_story_celular.md` (baixar APK, `adb install`, Configurações > Idiomas e entrada > ativar e aceitar o aviso, `ime set`). Sem isso, o padrão `sem_acento` funciona.
- **Conferir no aparelho (API 34), uma vez, porque aqui não há aparelho** — passo a passo com o emulador ligado e o Instagram aberto:
  1. `python scripts\story_dispositivo.py status --emulador` → tem de mostrar `tela: 1080x2400`, `tela acesa e destravada: sim`, `na frente: com.instagram.android`. Se der "bloqueado" com a tela visivelmente destravada, os marcadores do `dumpsys window` mudaram: mande a saída de `adb shell dumpsys window | findstr /i "lockscreen keyguard showing"` e `adb shell dumpsys power | findstr Wakefulness`.
  2. `python scripts\story_dispositivo.py dump highlight` com o próprio story aberto → tem de listar `toolbar_highlights_button`.
  3. Arte na galeria: `adb push H:\HypadoLocal\upload\story_interativo_2026-10-01.jpg /sdcard/Pictures/HP/teste.jpg` e `adb shell content call --uri content://media/external/file --method scan_file --arg /sdcard/Pictures/HP/teste.jpg` → a resposta deve trazer `Result: Bundle[{android.intent.extra.STREAM=content://media/external/images/media/N}]` e a foto deve aparecer na galeria do Instagram (abrir "+" > Story). Se não aparecer, testar o plano B (`adb shell am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file:///sdcard/Pictures/HP/teste.jpg`) e dizer qual funcionou.
  4. Digitação com `?`: num campo de busca do Instagram, `adb shell input text faz\?` tem de escrever `faz?` (se escrever `faz\?`, o adb está escapando sozinho: trocar `texto_para_input` para não pôr a barra — seção 5).
  5. Deep link: `adb shell am start -a android.intent.action.VIEW -d https://www.instagram.com/p/Dd7J4uso3bI/ -p com.instagram.android` tem de abrir o post no app (não no navegador).
- Primeira vez na galeria pelo story: a permissão de fotos ("Permitir") é tocada à mão (já estava na `LEIA_story_post.md`).


#### E2

#### Coleta de telas (E4) — passo a passo para leigo (também na `LEIA_story_celular.md`, parte 2)

1. Ligue o emulador (`H:\HypadoLocal\android\ligar_emulador.ps1`) ou plugue o celular com a depuração USB aceita. Deixe o
   Instagram aberto na @hp.futebol (a conta que sabemos estar logada).
2. Veja o roteiro antes, sem encostar no aparelho: `python scripts\story_coletar_telas.py --simular`.
3. Rode: `python scripts\story_coletar_telas.py --emulador` (ou `--celular`, ou `--serial emulator-5554`). A pasta padrão é
   `H:\HypadoLocal\android\telas\coleta` (`--pasta` muda).
4. Leia a instrução da tela 1 ("Abra o perfil…"), faça isso no celular e aperte **ENTER**. O script lê a tela, tira a foto,
   grava `01_perfil_proprio.xml` + `.png` e diz quais botões reconheceu (ex.: "Confirmados: aba_perfil, conta_container…").
5. Repita nas 12 telas. Regras: **não** toque em "Seu story", **não** escolha destaque, **não** toque em "Adicionar conta",
   **nunca** escreva senha (o script não pede e não ecoa o que for escrito). `pular` pula uma tela; `sair` encerra; `--so 07`
   repete só a tela 7.
6. Se aparecer "PAREI …" é porque a tela mostrava login/código/termos/aviso: o script gravou
   `H:\HypadoLocal\emulador\PARADO_AVISO_META.json` e não tocou em nada. Resolva no aparelho, apague o arquivo e rode de novo.
7. Mande a pasta `coleta\` inteira (12 XML + 12 PNG + `coleta.json`) para a próxima rodada: eles substituem os
   `*_sintetico_*.xml` de `tests\fixtures\android\` e confirmam/corrigem os ids da seção 9.
8. **Duas telas extras, fora da lista da tarefa (opcional, decisão 2 da seção 8):** figurinha de contagem aberta e o
   calendário dela. Dá para gravar à mão: com a tela aberta, `python scripts\story_dispositivo.py dump > H:\...\coleta\13_contagem.txt`.

#### Modo de acento real (DESLIGADO; o padrão `sem_acento` já funciona) — passo a passo

O `adb shell input text` não digita acento nem emoji. O padrão troca ("Você" → "Voce") e avisa no log. Se quiser acento de
verdade, é uma decisão sua (instalar APK) e são estes os passos — o script não faz nenhum deles:

1. Baixar `ADBKeyboard.apk` (projeto `senzhk/ADBKeyBoard` no GitHub) e instalar: `adb install ADBKeyboard.apk`.
2. No aparelho: Configurações > Sistema > Idiomas e entrada > Teclado virtual > Gerenciar teclados > ligar **ADB Keyboard** e
   **aceitar** o aviso de segurança do Android (clique seu).
3. Selecionar como padrão: `adb shell ime set com.android.adbkeyboard/.AdbIME`.
4. Rodar o story com a política `acento_real` (no `story_post_config.json`: `"politica_texto": "acento_real"` quando o patch (b)
   for aplicado; hoje: `disp.digitar(texto, politica="acento_real")`). Sem o teclado, o script explica e sai com código 4.
5. Depois: `adb shell ime set com.google.android.inputmethod.latin/com.android.inputmethod.latin.LatinIME` (volta ao Gboard).

#### Outros

- Primeira vez na galeria pelo story: a permissão de fotos ("Permitir") é tocada à mão (o script nunca toca em Permitir).
- Conferência pela API: o PC precisa passar `get_json` (`publicador_meta.api`) e o `ig_user_id` da conta
  (`meta_tokens_meta.json → contas["IG_<handle>"].id`) ao `Contexto`; sem isso o story fica em "tocado" (sem prova).
- Celular real: depuração USB + "Permanecer ativo" ligado enquanto no cabo; travado → código 4 (`celular bloqueado: o Antônio desbloqueia`).


#### B

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


#### C

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

## 8. O que NÃO foi possível e por quê

- **Rodar no PC, no emulador, no WhatsApp ou nas APIs**: a nuvem não tem acesso (Seção 0). Tudo está em sombra/simulação com transportes injetados; a prova real começa na integração.
- **Feed do YouTube** (`feeds/videos.xml`): responde 404 deste ambiente para qualquer canal; a prova foi a página oficial do canal (53/53). No PC: os 4 comandos `verificar … --gravar`.
- **`cbf.com.br`, `kianewscenter.com`** (certificado no proxy) e **`press.paramountplus.com`, `press.amazonstudios.com`, `hondanews.com.br`** (502 do proxy): não abriram; lista no `RELATORIO_FONTES.md`, seção "O que o PC deve tentar de novo".
- **Mesclar as fontes novas nos `07 Canais\radar\<canal>.json`**: os arquivos do PC não estão no repositório (só a config do GTA veio como fixture); os JSONs estão no formato de 4.10 prontos para colar.
- **Listar reels agendados no Facebook**: a documentação da Meta (lida em 01/10/2026) não descreve o endpoint; a tentativa `GET /{page}/video_reels` está marcada `confirmar: true`.
- **Contagem/calendário no story do celular**: os 5 ids (`contagem_titulo`, `contagem_data`, `contagem_dia_inteiro`, `data_proximo_mes`, `data_ok`) continuam palpite porque a lista de 12 telas da E4 não inclui essa figurinha (sugestão: telas 13 e 14 na próxima rodada).
- **Migração completa do `story_post.py` para o aparelho real**: o enunciado manda descrever, não reenviar; o patch (b) está linha a linha em `docs/rodada2/E2.md` §3.
- **Confirmações que só o aparelho dá (API 34)**: marcadores do `dumpsys window/power` (tela travada), `wm dismiss-keyguard`, `scan_file` do MediaStore fazendo a foto aparecer na galeria do Instagram, `input text faz\?` chegando como `faz?`, `am start -p` abrindo no app — passo a passo em `docs/rodada2/E1.md` §6.
- **B6**: granularidade/atraso do `publishAt`, regras de Shorts (3 min, `#Shorts`, miniatura), lado legal do COPPA e a lista de escopos por método não foram confirmados em página oficial (limite de 10 leituras); estão marcados.

## 9. Decisões em aberto e conflitos (para o Antônio/Diretor)

Consolidado das seções 8 dos relatórios. As decisões que a sessão principal já tomou estão na seção 4
(com a linha para desfazer).

#### A1

1. **`redes_api` ainda tem `facebook` e `youtube`** (padrão da rodada 1, `esteira/config.py`). Em modo real, um pedido com `redes: ["instagram", "facebook"]` grava o item do Instagram e, na rede seguinte, cai em `99_erros` com "facebook: rede tem que ser instagram ou threads…" (é o que o PC pediu: recusar). Sugestão: trocar o padrão para `redes_api: ["instagram", "threads"]` e passar `facebook`/`youtube` para `redes_manuais` (esperam `facebook_ok.json`/`youtube_ok.json`) até o `publicar\` do PC entrar — mudança de 1 linha, não fiz por ser decisão de produto.
2. **Sombra também valida.** Em modo sombra o item IG/Threads passa pela mesma validação do publicador (arquivo existe, contagens, limites); um pedido ruim vai para `99_erros` já na sombra. Acho desejável (a sombra existe para achar isso), mas pode ser trocado por `validar=False` em `AgendadorFilaApi.agendar`.
3. **`LimiteDaConta` no `reenviar`:** o limite de 24 h não é "tempo esgotado", então o `reenvio_seguro` para na hora e marca `status: "erro"` no item (não republica). O PC pode preferir deixar o item na fila (voltar sem marcar).
4. **Trava compartilhada:** o lock que gravamos agora tem `pid`; os scripts do PC (sem pid) vão aplicar a regra deles (30 min) ao nosso lock se eles só olharem `desde`. Se um trabalho pesado nosso passar de 30 min, um script do PC pode assumir a trava. Alternativa: o PC passar a ler `pid` como fizemos.


#### A2a

1. **Voz no GTA.** O plano real (`plano_corte_exemplo.json`) tem `toque_hp` (narração) e criadores gringos dublados no canal GTA, mas a regra da rodada 1 (`esteira/constantes.py → CANAIS_COM_VOZ = destinos, receitas, carros, filmes`) faz `validar_pedido` recusar `narrar_toque_hp`/`dublar` no GTA ("dublagem/voz sintética só em destinos, receitas, carros e filmes"). O teste da esteira registra o conflito (`assert any("voz sintética" in e …)`) e roda com `narrar_toque_hp = False`. Resolver é 1 linha (incluir `"gta"` em `CANAIS_COM_VOZ`); não fiz por ser regra de conteúdo — o CLAUDE.md só proíbe voz sintética no **futebol**.
2. **Quem renderiza na esteira da nuvem.** O Editor continua o ffmpeg próprio (`editor.py`); não há plugin que chame o `cortar.py` do PC. `argv_cortar` está pronto e um `EditorCortar` (1 classe: `argv_cortar(... dublar=dublar_por_padrao(...))` + `rodar`) daria paridade total com o PC, mas mudaria a "segunda opinião" em cópia — decisão do Diretor.
3. **Narrador Toque HP** não tem sintetizador no PC pelo `dublar.py` (sem `--texto-arquivo`). Para rodar de verdade falta o comando do Piper (`H:\HypadoLocal\modelos\piper`, `pylib`) em `comandos.falar` do `config.json` (`{entrada}` texto, `{saida}` wav) — ninguém sabe o argv real; o plugin dá erro claro até lá.
4. **Status do inventário** mistura `sem_token` (token) e `sem_token` com `falta: ["id"]`; se o painel quiser distinguir, basta ler `falta` — ou trocar para `sem_id` em `chaves_pc._entrada_meta` (o `coletar` seguiria igual).


#### A2b

1. **Gringo no GTA × `CANAIS_COM_VOZ`** (mesmo conflito da decisão 1 do A2a): o pedido real de criador `en` (ex.: `tmartn2`) sai `dublar: true` pelo `pedido_pc`, mas `esteira/pedido.validar_pedido` recusa ("dublagem/voz sintética só em destinos, receitas, carros e filmes") porque `CANAIS_COM_VOZ` (rodada 1) não tem `gta`. O teste `test_gringo_no_gta_esbarra_na_regra_de_voz_da_rodada_1` registra isso. Resolver = incluir `"gta"` em `esteira/constantes.py::CANAIS_COM_VOZ` (1 linha; não fiz por ser regra de conteúdo — o CLAUDE.md só proíbe voz sintética no futebol, e o `config.json` do GTA tem `dublagem` com `"credito": "dublado por HP"`).
2. **`ler_pedido_pc` não está ligado ao motor.** `motor.importar_pedidos_soltos` lê o `.json` solto na hora (pode pegar arquivo meio gravado). Ligar são ~3 linhas em `_importar_json` (`if pedido_pc.ler_pedido_pc(arq, agora=time.time()) is None: return []`), usando `time.time()` como a limpeza de `.criando_` já faz (o `agora` injetado dos testes está no passado em relação ao mtime real). Não mexi em `motor.py` (arquivo da rodada 1 fora do patch pedido).
3. **Sem `config.json` o corte é recusado.** Alternativa mais leniente: pular a checagem do criador quando o config não existe. Mantive o recusar (regra 6) — se o Diretor preferir, é `conferir_criador=False` em `validar_pc` quando `config is None`.
4. **Emoji e vocativo saem sempre** da pergunta da figurinha (mesmo quando cabe). Se o Antônio quiser a pergunta exatamente como foi escrita quando couber, inverter a ordem em `story_post_lote.candidatos` (texto antes de `sem_vocativo`) e tirar o `sem_emoji` de `limpar`.
5. **post.json do corte publica `final.mp4`** (docstring do `post.py`). Se o `publicar` do PC preferir o `upload.mp4` (≤ 10 MB), trocar `ARQUIVOS_POST_PADRAO["corte"]`.
6. **`tags` do post.json** saem das `#` da legenda quando o pedido não traz `hashtags` — pode duplicar o que o `publicar` já faz; é só trocar `hashtags_do_pedido(v) or _RX_HASHTAG.findall(legenda)` por `hashtags_do_pedido(v)`.


#### A3

1. **Cores da página de links e do painel divergem da marca (só relatado, nada alterado):**
   - `scripts/pagina_links/cores_canais.json`: GTA `#FF3D8B` (= `marca.GTA_ROSA_SITE`, o 3º rosa do conflito 2 da §4.6 — esperado, "só o site"); **Carros `#FF3B3B`**, que não é nem o `#FF2D2D` do perfil nem o `#E61E2D` do post — um 3º vermelho que a tabela da §4.6 não tem. Futebol, Filmes, Receitas e Destinos batem com `cor_canal`.
   - `scripts/painel/previa_celular.py` (dados de demonstração): GTA `#ff3d8b` e Carros `#ff3b3b` — as mesmas divergências; os outros 4 batem.
   - Decisão do Antônio: manter o `#FF3D8B` do site e escolher o vermelho do Carros na página de links (`#FF2D2D` do perfil é o candidato natural; o `gerar_fundos.py contraste` precisa rodar depois, porque o contraste do texto do botão muda).
2. **`ZONA_LINK` entra na base proibida:** `(140, 1500, 940, 1640)` é o que a tarefa D define e o `marca.py` tem, mas 1640 > 1570 (1920 − 350). O relatório D (§8) também marca isso. Ou a zona do link sobe para ≤ 1570, ou se aceita que a figurinha de link (que o Instagram põe ali) viva na faixa da resposta. O teste de marca confere o valor atual; mudando a constante, muda-se 1 linha no teste.
3. **Tipo `"aviso"` × "WhatsApp só para 3 coisas":** as 2 mensagens reais da fixture (Pinterest pronto; conteúdo de amanhã) não são resumo nem "no ar". O adaptador as enfileira com `tipo: "aviso"`, mas `validacao.TIPOS_PERMITIDOS` (rodada 1) rejeita qualquer tipo fora dos 3 — na prática iriam para `rejeitadas\`. Resolver é 1 linha (`TIPOS_PERMITIDOS = (..., "aviso")` em `whatsapp_local/config.py`); não fiz porque é regra de produto (§4.8 diz "mais: avisar quando algo precisa dele", o que sugere permitir).
4. **Duas filas ao mesmo tempo:** enquanto o plantão antigo continuar lendo `temp\whatsapp_fila.json`, importar para a pasta faria a mesma mensagem sair duas vezes. `importar --limpar` esvazia o arquivo do PC depois de importar; só use quando o plantão antigo estiver desligado (ou vice-versa: `exportar` alimenta o antigo e o enviador novo fica em sombra).
5. **Aviso de madrugada:** o vigia novo monta o aviso de um post que saiu de madrugada com `enviar_apos 07:30` (fica na fila). Se o Antônio preferir que post de madrugada NÃO gere aviso nenhum, é trocar `enviar_apos_padrao` por um `continue` em `tarefas.enfileirar_no_ar`.
6. **`esquema_radar` sobre os arquivos da tarefa F:** o F4 pede "se o A3 entregar o esquema, rodar nos 4 JSONs"; os `*_fontes_novas.json` da F são listas de fontes candidatas, não a config do radar — o esquema valida só `07 Canais\radar\<canal>.json` (a fixture `radar_gta.json`). Fica para quem fechar a F juntar as fontes novas na config e aí rodar `python radar_fontes\esquema_radar.py <config>`.


#### D

1. **Zona do link × zona segura.** `marca.ZONA_LINK = (140,1500,940,1640)` vai até y 1640, mas a regra da §4.6 é "nada nos 350 px da base" (y > 1570). Mantive a zona como a §4.6/`marca.py` dizem e deixei só o contorno fino entrar nessa faixa; todo texto e a ponta da seta terminam antes de 1500. Decisão do Antônio/Diretor: manter (a figurinha de link do Instagram fica mesmo perto do campo de resposta) ou subir a zona para (140,1430)-(940,1570) em `hpbase/marca.py` (o gerador e o `_zonas.json` seguem automaticamente).
2. **Rosa do GTA**: usei `GTA_ROSA_POST #FF48A0` (pílula, degradê do título, marcadores), como a §4.6 manda para arte de post/story; o selo "HP" do GTA é branco em itálico (como `arte_perfil.selo_hp`).
3. **Vermelho do Carros**: `#E61E2D` (post) em tudo, nunca `#FF2D2D`.
4. **Futebol**: verde `#1ED760` (nunca o amarelo da rodada 1); `cor_destaque` troca por cor de clube quando o spec traz.
5. Texto branco sobre a etiqueta vermelha do Carros fica em 4,58:1 (limite 4,5). Se quiserem folga, a alternativa é texto preto `#0F0F12` (4,56:1 — igual) ou escurecer levemente a etiqueta, o que muda a cor da marca: decisão do Diretor.


#### F0

- Regra 3 do enunciado diz que HTTPS no PC é pelo `curl.exe`; a tarefa F0 pediu urllib + truststore no
  transporte real. Entreguei os dois: urllib é o padrão (como pedido) e `--curl` troca para o `curl.exe`.
  O Antônio decide qual vira padrão no PC (trocar é uma linha em `main()`: `transporte_curl if args.curl else transporte_real`).
- `video_reutilizavel` em `carros` (ver Suposições): hoje fica `false` por regra; decidir se vídeo oficial de montadora pode ser reutilizado (com crédito).
- Neste ambiente o feed do YouTube responde 404 para todo canal, então tudo que F1–F3 verificarem sai como
  `pagina_canal`; o PC, ao rodar `verificar --gravar`, deve promover as entradas para `feed` (a ferramenta tenta o feed primeiro).


#### F1

- **CBF TV × @brasil** e **CONMEBOL Libertadores × @LibertadoresBR**: entradas marcadas `ja_existe: true`; o Antônio decide se trocam, somam ou são ignoradas (ver 6.1).
- **Duas Sul-Americanas** (espanhol @Sudamericana e português @SudamericanaBR): entrei com as duas; se for ruído, manter só a BR.
- **FIFA** no radar do futebol: entrou com peso 1.0; pode gerar alerta de assunto fora do Brasileirão — se incomodar, tirar ou deixar `peso` menor.
- **Feed da CONMEBOL em espanhol** com `filtrar: true`: fica dependendo das `palavras`/`entidades` do config para não virar alerta de qualquer rodada de outra liga.
- **Formato de `futebol_candidatos.txt`** (6ª coluna = resultado, como a tarefa pediu) não é o da CLI `candidatos` (6ª = channel_id). Se o PC preferir o formato da CLI, basta cortar a 6ª coluna.
- **cbf.com.br** não é acessível desta nuvem (certificado): a lista da Série A 2026 veio do ge + Wikipedia, não da CBF.


#### F2

- **Paramount Pictures Brasil × @ParamountBrasil**: entrada marcada `ja_existe: true`; o Antônio decide se troca, soma ou ignora (ver 6.1).
- **Netflix sala de imprensa (pt_br)**: a melhor fonte em português caiu só por formato de data fora do padrão. Decidir se a F0/sessão principal aplica o patch de `analisar_data` (item 5.1) — aí o feed entra com `oficial: true`.
- **Canais globais em inglês** (Netflix, Prime Video, HBO Max, Disney Plus, Paramount Plus, Apple TV, estúdios): entraram com peso 1.2; podem gerar alerta de título que não estreia no Brasil — se incomodar, baixar o peso ou tirar.
- **Google News como RSS** para Omelete/AdoroCinema: ficou em `rss` (provado pela ferramenta). Se o Antônio preferir o coletor `google_news` do radar, a query equivalente está em 5.
- **Feeds corporativos** (Disney, Amazon, Apple Newsroom BR, Marvel) com `filtrar: true`: dependem das `palavras`/`entidades` do config de filmes para não virar alerta de parque temático, iPhone ou quadrinho.
- **press.paramountplus.com / press.amazonstudios.com** não são acessíveis desta nuvem (502 do proxy): o PC testa.


#### F3

- **Falso positivo da heurística `e_site_noticia` (ferramenta da F0, não alterei):** o @handle do GWM Global é `@greatwallmotor1853` e `SITES_NOTICIA` tem o token `"motor1"` (Motor1.com), que é procurado como substring (`len(token) > 5`). Resultado: na **primeira** passada (URL `/channel/UC…`) a entrada sai `oficial: true`; quando o PC rodar `verificar --gravar`, a ferramenta relê a URL já com o @handle, imprime `aviso: GWM Global: site/canal de notícia não é oficial (oficial passou a false)` e **troca `oficial` para false**. Contorno adotado: a entrada ficou `oficial: true` no JSON entregue, com o aviso escrito na `evidencia`. Correção sugerida para a sessão principal (dona da F0), 1 linha em `radar_fontes/verificar_fontes.py`, função `e_site_noticia`: tratar `motor1` como token exato (ex.: `if len(token) <= 6:` em vez de `<= 5`, o que também protege `record` e `kotaku`), com um teste `test_handle_com_motor1_nao_e_site_noticia`.
- **Fiat global:** dois canais verificados com o mesmo título; decidir qual entra (ver seção 6).
- **Renault global:** entrou o canal corporativo "Renault Group"; se o Antônio preferir só o canal da marca, confirmar o @Renault no site da marca (renault.com hoje redireciona para o grupo).
- **Mitsubishi global:** entrou o @MitsubishiMotorsTV (verificado); o @MitsubishiMotorsGlobal (sem selo) ficou descartado — decidir se vale ter os dois.
- Como na F1: o feed do YouTube responde 404 nesta nuvem, então todos os canais saíram `pagina_canal`; o PC promove para `feed` ao rodar `verificar --gravar` (atenção ao caso GWM acima).
- Passei do limite de ~40 fetches em becos sem saída (~60): a lista de 28 marcas × global/BR × sala/YouTube é grande e a maioria das salas de imprensa bloqueia robô. Parei de sondar quando passei; o que não foi testado está marcado "não verificado (tempo)".


#### F4

**Três correções pequenas em `radar_fontes/verificar_fontes.py` (F0), não aplicadas por mim** — o arquivo é da
F0/sessão principal; ficam prontas para quem decidir (cada uma com 1 teste gravado em `radar_fontes/testes/test_verificar_fontes.py`):

1. **Falso positivo `motor1` (GWM Global)** — função `e_site_noticia`. Antes:
   `if len(token) <= 5:` / `if any(c == token for c in chaves): return True` / `elif any(token in c for c in chaves): return True`.
   Depois: acrescentar a constante `TOKENS_EXATOS = ("motor1",)` ao lado de `SITES_NOTICIA` e trocar a condição
   por `if len(token) <= 5 or token in TOKENS_EXATOS:`. Teste: `test_handle_com_motor1_nao_e_site_noticia`
   (`e_site_noticia("GWM Global", "https://www.youtube.com/@greatwallmotor1853") is False` e
   `e_site_noticia("Motor1", "https://www.motor1.com/rss") is True`). Até lá, o `--gravar` vira o GWM para `oficial: false` todo mês.
2. **Data por extenso (Netflix pt_br)** — função `analisar_data`, antes de `return None` no `except ValueError`:
   casar `r"(\d{1,2})(?: de)? ([a-zç]+)(?: de)? (\d{4})"` em `t.lower()` com um dicionário de meses em
   português e inglês e devolver `datetime(ano, mes, dia, tzinfo=timezone.utc)`. Teste com o feed gravado
   `<pubDate>30 de setembro de 2026</pubDate>`. Com isso o feed da Netflix (melhor fonte em português do canal
   filmes) entra como `oficial: true, filtrar: false, peso: 1.5`.
3. **Marcas por entrada somem no `--gravar`** — funções `verificar_entrada_rss` e `verificar_entrada_youtube`, depois
   de montar `saida`: `for k in ("ja_existe", "nota_conferir"): if k in entrada: saida[k] = entrada[k]`. Teste:
   `verificar_arquivo(..., gravar=True)` com uma entrada marcada mantém a marca. Alternativa sem patch: apagar as
   marcas assim que o Antônio conferir as 4 entradas.

**Decisões de conteúdo herdadas de F1–F3, ainda em aberto** (detalhe nos respectivos relatórios):
- CBF TV × @brasil, CONMEBOL Libertadores × @LibertadoresBR, Paramount Pictures Brasil × @ParamountBrasil (ver 6.1).
- Duas Sul-Americanas (ES e BR) e FIFA com peso 1.0 no radar do futebol: manter ou tirar se virar ruído.
- Canais globais em inglês no canal filmes (Netflix, Prime Video, HBO Max, Disney Plus, Paramount Plus, Apple TV, estúdios) com peso 1.2.
- Google Notícias por domínio como `rss` para Omelete/AdoroCinema × coletor `google_news` do radar (query equivalente no F2.md).
- Fiat global (dois canais verificados), Renault global (Renault Group × @Renault), Mitsubishi global (dois canais).
- `video_reutilizavel` em carros (hoje `false` por regra; se o Antônio quiser reutilizar vídeo oficial de montadora, acrescentar `"carros"` em `NOTA_USO_PADRAO`).
- `--curl` × urllib como transporte padrão no PC (hoje urllib; trocar é 1 linha em `main()`).

**Limites do ambiente que o PC resolve:** feed do YouTube 404 (todos `pagina_canal`); `cbf.com.br` e
`kianewscenter.com` por certificado no proxy; `press.paramountplus.com`, `press.amazonstudios.com` e
`hondanews.com.br` por 502 do proxy; salas que bloqueiam robô (403) podem abrir no navegador do PC.


#### E1

1. **Código de saída da ambiguidade de aparelho:** usei 4 (precisa do Antônio). Se o Diretor preferir 1 (erro), é só `DispositivoAmbiguo.codigo = ERRO`.
2. **"vídeo novo" = `compartilhar_post` sem link.** Segui o enunciado; o lote não traz o link do reel, então o item nasce com `link: null` e pendência e o pedido não valida até o link entrar. Alternativa: tratar como `chamada_post` com a arte estática do lote + figurinha de link (a arte já está no item). Quem decide: Antônio/Diretor; onde: `de_lote_estaticos` (ramo `compartilhar_post`).
3. **Zona das figurinhas × proporção da tela.** Arte 9:16 numa tela 20:9: se o editor enquadra com barras, a conversão fração × tela inteira erra; `ler_zonas(..., area=bounds do nó da mídia)` resolve, mas o E2 precisa ler esse nó no dump real do editor (coleta E4).
4. **Ordem dos planos do MediaStore.** Conferido no AOSP (`MediaStore.SCAN_FILE_CALL = "scan_file"`, `MediaProvider.getResultForScanFile` sem checagem de permissão — só um TODO; `ACTION_MEDIA_SCANNER_SCAN_FILE` marcado `@Deprecated` no `Intent.java`, mas ainda com intent-filter exportado no manifesto do MediaProvider e tratado por `MediaService.onScanFile`). O que NÃO dá para confirmar sem aparelho: se a galeria do Instagram recarrega sozinha depois do scan (pode ser preciso abrir a galeria de novo). Por isso o `empurrar_arte` confere pelo `content query` e o passo 3 da seção 6 existe.
5. **Botão proibido também grava a parada** (`TelaProibida` é `AvisoMetaDetectado`, como na rodada 1). Se preferirem só recusar o toque sem parar tudo, mudar `Dispositivo.tocar` para levantar sem `_parar`.
6. **`scanFile` não é API pública de app** (no AOSP atual é `@SystemApi`/`@hide`), mas a chamada `scan_file` ao provedor existe desde o Android 10 e é o que o `content call` usa; o `MediaScannerConnection.scanFile` (API pública) não tem equivalente por shell.


#### E2

1. **"Falha depois do toque" não derruba o item.** `ElementoNaoApareceu`/`DumpFalhou`/orçamento depois do `input tap` em
   "Seu story" viram `"a_conferir"` e o item segue (destaque é pulado). Aviso da Meta depois do toque também marca
   `"a_conferir"`, mas sobe (código 3). Alternativa: tratar tudo como erro. Onde: `publicar_seu_story`.
2. **Contagem e calendário sem tela de coleta.** A lista da tarefa E4 tem 12 telas e nenhuma é a figurinha de contagem; os 5 ids
   (`contagem_titulo`, `contagem_data`, `contagem_dia_inteiro`, `data_proximo_mes`, `data_ok`) continuam palpite. Sugiro
   acrescentar `13_figurinha_contagem_aberta` e `14_calendario_contagem` em `TELAS` na próxima rodada (é só mais 2 entradas).
3. **Zona × prévia do editor.** Converto as zonas pela área do nó de prévia (`area_da_arte`) — se o editor real não expõe esse
   nó, cai na tela inteira. A coleta `04_editor_story` resolve.
4. **Chave dos stories com arte** (`post_id#tipo@quando`): se o Diretor preferir 1 story por `post_id` mesmo com vários
   `stories[]`, trocar `chave_do_story` para devolver sempre `post_id`.
5. **Coleta grava a parada.** Conservador (igual ao story_post). Se preferirem que a coleta só pare sem bloquear os stories,
   criar o `Dispositivo` sem `gravar_parada` em `story_coletar_telas.main`.
6. **`recente_max_min` 2 → 5** (patch 2) muda o comportamento da rodada 1: um story de até 5 min atrás conta como "de agora".
   É o que o carimbo real pede (`3m`); se o Antônio postar dois stories em menos de 5 min, o destaque pode pegar o anterior —
   o fluxo novo confere também o dono (`reel_viewer_title`), não o conteúdo.


#### B

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


#### C

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

## 10. Checklist da Seção 6 do enunciado (conferido antes de entregar)

- [x] Nenhum arquivo importa `hp_studio.esteira` nem `hp_studio.metricas` (grep em `app`, `scripts`, `tests`, `radar_fontes`: só a instrução dentro da docstring de `contrato_pc.py`).
- [x] Nenhum teste faz rede, abre `adb`, lê `H:\HypadoLocal\segredos\` ou depende de relógio real (grep por `urlopen`/`requests`/`adb` nos `test_*.py`: nada; relógio sempre `agora=` injetado; a fixture autouse troca `HP_LOCAL`/`HP_DRIVE` por `tmp_path`).
- [x] Nenhum valor `FAKE_NAO_E_TOKEN_*` aparece em saída, log, exceção ou arquivo gerado — testes em `metricas/testes/test_chaves_pc.py`, `scripts/testes/test_reenvio_seguro.py`, `publicar_extra/testes/test_youtube_extra.py`, `test_facebook_extra.py`, `test_comentarios.py`, `test_comentarios_ig_threads.py`.
- [x] Todo `subprocess` do código de produção é lista e leva `creationflags=0x08000000` no Windows (`hpbase.rodar`, `reel_futebol_midia._popen_ffmpeg`, `verificar_fontes.transporte_curl`, `story_dispositivo.runner_real`).
- [x] Todo `open`/`read_text`/`write_text` tem `encoding="utf-8"` (grep nos arquivos novos/alterados: só `Image.open`, que é binário); gravação com `.tmp` + `os.replace` (`hpbase.escrever_json`, `gravar_json` do radar, `gravar_imagem` do story_artes).
- [x] Caminho do PC só em constante no topo do módulo ou variável de ambiente (`PYTHON_PC`, `SCRIPTS_PC`, `PASTA_FOTOS`, `arquivo_fila_pc()`, `HP_FONTES`…); funciona com espaço no caminho (`G:\Meu Drive\…`, testado com `tmp_path` com espaço no `comentarios`).
- [x] Nenhuma arte tem emoji (`marca.sem_emoji` em todo texto do `story_artes`; teste); nenhuma mensagem do WhatsApp começa sem `*Claude - *` (`validacao` + `fila_pc.validar_mensagem_pc`).
- [x] Nenhum `## <arquivo>.<ext>` dentro do conteúdo de um arquivo; nenhum arquivo com nome de segredo (`docs/compilar_entrega_2.py --so-checar` recusa os dois; `contas.json` virou `contas_exemplo.json`); `docs/desempacotar_check.py` prova que o compilado desempacota sem arquivo "sem bloco" nem arquivo falso e idêntico ao repositório.
- [x] A suíte da rodada 1 continua verde e o número está acima (1540 passed, 0 failed, 0 skipped, 74 s).
- [x] Cada suposição que sobrou está na seção 6 com arquivo e função.
- [x] Lotes de no máximo 3 agentes ao mesmo tempo e nunca 2 workflows juntos (Lote 1: A→D→F; Lote 2: E→B→C; a máquina da nuvem limitou a 2 simultâneos).

## 11. Onde está cada coisa

- Enunciado desta rodada: `docs/PROMPT_NUVEM_2.md`. Convenções: `docs/CONVENCOES.md` (seção "Rodada 2").
- Relatórios dos agentes: `docs/rodada2/`. Patches por função: `PATCHES.md` (+ `patches/rodada2_rodada1_alterados.diff`). Pendências `.claude`: `PENDENCIAS_PARA_O_DIRETOR.md`.
- Compilado único: `ENTREGA_NUVEM_HP_STUDIO_2.md` (gerado por `python docs/compilar_entrega_2.py`; conferido por `python docs/desempacotar_check.py ENTREGA_NUVEM_HP_STUDIO_2.md --comparar-com .`).
- Rodada 1 (histórico): `docs/ENTREGA_rodada1.md` e `ENTREGA_NUVEM_HP_STUDIO.md`.
