# Entrega da nuvem — HP Studio (30/09/2026)

Para a sessão **HP GESTÃO** integrar no PC do Antônio e ligar o **modo sombra**. Tudo aqui foi feito e testado na nuvem (Linux, Python 3.11, ffmpeg 7). **Nada foi rodado no PC, no emulador, no WhatsApp nem nas APIs de verdade.** Por isso tudo começa em sombra ou simulação.

## 1. O que foi entregue

| # | Módulo | Onde fica no PC | Testes | Começa em |
|---|---|---|---|---|
| A | Manuais 04–13 + `README.md` (índice) | `06 Projeto\app\manuais\` | — | (texto; faltam revisão e o 01) |
| 0 | `hpbase`: base comum (caminhos, log sem segredo, `pesado.lock`, 18h–22h30, sem janela preta, segredos) | `06 Projeto\app\hp_studio\hpbase\` | 9 | — |
| B | `esteira`: etapa 3, pastas P0/P1/P2 | `06 Projeto\app\hp_studio\esteira\` | 151 | sombra (`--simular`) |
| C | `metricas`: etapa 6, métricas por API | `06 Projeto\app\hp_studio\metricas\` | 30 | `coletar --simular` |
| D | `qa_paridade`: teste de paridade + 7 dias | `06 Projeto\app\hp_studio\qa_paridade\` | 93 | (é a régua da sombra) |
| E | `whatsapp_local`: enviador local | `06 Projeto\app\hp_studio\whatsapp_local\` | 90 | sombra (padrão) |
| F | `story_post.py`: story pelo emulador | `scripts\` | 43 | `--simular` |
| G | `reel_futebol.py`: reels do Futebol | `scripts\` | 29 | `montar --simular` |
| H | `reenvio_seguro.py`: publicador sem duplicar | `scripts\` | 22 | `reenviar --simular` |
| I | Painel: espelho do banco, selo das abas, prévia no celular | `scripts\painel\` | 73 | `comparar` (sombra) |
| J | Página de links: fundos, botões e passo a passo | `scripts\pagina_links\` | 14 | (manual no Google Sites) |

**Total: 554 testes passando** (373 no `app\hp_studio` + 181 em `scripts\`). Os módulos com ffmpeg rodaram com vídeo e áudio sintéticos de verdade.

Cada módulo tem o seu `LEIA.md` com o passo a passo completo. Este arquivo é só o roteiro de integração.

## 2. Regras que a integração NÃO pode quebrar

1. **Não sobrescrever nada que já existe.** Os arquivos novos não têm nome igual aos do PC que conhecemos: `publicador_meta.py`, `lote.py`, `painel_local.py` e `montar_painel_publico.py` **não foram tocados**. Os módulos novos só se plugam neles.
   - Antes de copiar, confira se já existe `hp_studio\hpbase`, `hp_studio\esteira`, `hp_studio\metricas`, `hp_studio\qa_paridade` ou `hp_studio\whatsapp_local`. Se existir, pare e avise.
   - **Não há `conftest.py` em `app\` nem em `scripts\testes\`.** Cada pasta `testes\` traz o seu, então os 53 testes da etapa 1 continuam intactos.
2. **Não mexer no que está em andamento no PC:** etapa 4 (Facebook e YouTube pela API), redução de arquivos do painel público e auditoria da API do YouTube.
3. **Nenhuma tarefa passa para o app sem 7 dias de sombra aprovados no `qa_paridade`.**
4. Trabalho pesado é 1 por vez (`H:\HypadoLocal\app\pesado.lock`) e nunca das 18h às 22h30, exceto P0 da esteira (decisão de 30/09, ver item 6). Todos os módulos usam `hpbase.TravaPesada`; só o story (leve) e o P0 usam `ignorar_horario=True`.
5. Tokens ficam só em `H:\HypadoLocal\segredos\`. O `hpbase.ler_segredo` lê e nunca mostra, e o log passa tudo por `mascarar()`.

## 3. Instalação no PC, passo a passo

Tudo no **PowerShell 5.1**. `$PY` é o Python 3.12 do Antônio.

1. Abra o PowerShell (não precisa ser administrador).
2. Defina o atalho do Python:
   `$PY = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"`
3. Confira se funciona: `& $PY --version`. Deve aparecer `Python 3.12.x`.
4. Baixe o branch `claude/new-session-7kpo1f` do repositório `antoniovenier/HP` numa pasta temporária no **H:**, por exemplo `H:\HypadoLocal\temp\entrega_nuvem\`. Nada no C:.
5. Confira que ainda não existem as pastas novas:
   `Test-Path "G:\Meu Drive\Hypado\06 Projeto\app\hp_studio\hpbase"`
   Deve responder `False`. Repita para `esteira`, `metricas`, `qa_paridade` e `whatsapp_local`. Se algum der `True`, pare.
6. Copie as 5 pastas de `app\hp_studio\` da entrega para `G:\Meu Drive\Hypado\06 Projeto\app\hp_studio\`.
7. Copie `app\manuais\04_...md` até `13_...md` para `06 Projeto\app\manuais\`.
   - O `README.md` da entrega é o índice novo. Se já existir um `README.md` em `manuais\`, compare antes de trocar.
8. Copie para `G:\Meu Drive\Hypado\scripts\`:
   - os arquivos `story_post*.py`, `reel_futebol*.py` e `reenvio_seguro.py`;
   - os arquivos `LEIA_*.md`;
   - as pastas `painel\` e `pagina_links\`;
   - os 6 arquivos `testes\test_*.py` para `scripts\testes\` (crie a pasta se não existir).
9. Instale as dependências:
   `& $PY -m pip install pytest numpy pillow requests`
10. Só para o WhatsApp:
    `& $PY -m pip install playwright`
    O `LEIA.md` do `whatsapp_local` recomenda usar o Chrome já instalado (`canal_navegador: "chrome"`), sem baixar outro navegador.
11. Só para a legenda automática da esteira:
    `& $PY -m pip install faster-whisper`
    Na primeira vez ele baixa o modelo; aponte o cache para o H:, como explica o `LEIA.md` da esteira.
12. Confira que o ffmpeg está no PATH: `ffmpeg -version`. Se não estiver, defina `HP_FFMPEG` com o caminho do `ffmpeg.exe`.
13. Rode os testes do app:
    `cd "G:\Meu Drive\Hypado\06 Projeto\app\hp_studio"; & $PY -m pytest -q hpbase esteira metricas qa_paridade whatsapp_local`
    Esperado: **373 passed**.
14. Rode os testes dos scripts:
    `cd "G:\Meu Drive\Hypado\scripts"; & $PY -m pytest -q testes\test_story_post.py testes\test_reel_futebol.py testes\test_reenvio_seguro.py testes\test_painel_espelho.py testes\test_painel_selo.py testes\test_painel_previa.py testes\test_pagina_links.py`
    Esperado: **181 passed** (os testes de JS são pulados se não houver `node`).
15. Os testes criam arquivos só em pastas temporárias. Confira que nada apareceu em `H:\HypadoLocal\esteira` nem em `whatsapp_fila`.
16. Rode também os testes antigos da etapa 1 e confira que continuam **53 passed**.

## 4. Ligar o modo sombra (ordem sugerida)

| Ordem | O quê | Como fica em sombra | Critério para sair |
|---|---|---|---|
| 1 | **qa_paridade** | é a régua | — |
| 2 | **metricas** | `python -m metricas coletar --simular`, depois `coletar` de verdade (só leitura da API; não publica nada). Agendar às 6h com o comando que `agendar-6h` imprime | 7 dias com `status: ok` nas redes com token |
| 3 | **reenvio_seguro** | `publicador_meta.py` chama em modo simular, conforme `LEIA_reenvio_seguro.md` | 7 dias sem duplicar e sem erro |
| 4 | **esteira** | `python -m esteira iniciar` (cria `H:\HypadoLocal\esteira\` em sombra), depois `python -m esteira --simular vigiar --uma-vez`. O editor real roda e cada `final.mp4` é comparado com o do Claude: `python -m qa_paridade video final.mp4 ref.mp4 --tarefa editor_reel` | `python -m qa_paridade status` mostrar "liberada" |
| 5 | **whatsapp_local** | modo sombra padrão: monta o texto e compara com o que o plantão mandou (`whatsapp_sombra\plantao\`) | 7 dias com pares ≥ 90% e média ≥ 95% (sugestão; o Antônio decide) |
| 6 | **reel_futebol** | `montar --simular`, depois render de verdade comparado com o reel do Claude no `qa_paridade` | 7 dias liberados |
| 7 | **story_post** | `--simular` (só imprime o roteiro). Antes do primeiro real, confira os resource-ids com `android\ui.py` (lista no `LEIA_story_post.md`) | 7 dias sem aviso da Meta e com todos os stories certos |
| 8 | **painel** | `espelho_banco.py importar` do `dados.json` publicado, depois `comparar` todo dia | 7 dias idênticos; aí a rotina deixa de usar ArtifactData |

## 5. Suposições a confirmar no PC

Os pontos abaixo dependem de código que não existia na nuvem. Todos estão isolados num único lugar para ajustar.

1. **Formato da `fila_api\`** (esteira e reenvio): um JSON por post e por rede.
   - Campos: `{id, rede, conta, canal, tipo, midia[], capa, legenda, agendar_para, status}`.
   - Para casar com o `publicador_meta.py` real, ajuste `montar_registro_fila()` e `ler_confirmacao()` em `esteira\agendador.py`.
   - O `reenviar` chama a primeira função que existir entre `publicar_item`, `publicar_da_fila` e `publicar(item)`.
2. **Parâmetros dos scripts do PC:** `ytdlp.py`, `dublar.py`, `estaticos.py` e `posts_futebol.py legenda_video`.
   - Estão em `esteira\config.json → comandos` e no estilo do `reel_futebol` (`legenda_auto_cmd`).
   - Rode cada um com `--help` e ajuste só a configuração. Os manuais 05 e 06 usam `OPCAO_TEXTO`/`OPCAO_SAIDA` como marcador para o mesmo motivo.
3. **`meta_tokens.txt`:** chaves `IG_<CONTA>_TOKEN`/`_ID`, `TH_<CONTA>_...` e `FB_<CONTA>_...`. YouTube em `youtube_tokens.txt`, desligado (`"autorizado": false`) até a auditoria terminar.
   - Se o arquivo real usar outros nomes, ajuste `metricas\config.py`.
   - **Não abra o arquivo para conferir:** rode `python -m metricas coletar --simular`, que diz só quais chaves faltam.
4. **Resource-ids do Instagram no emulador:** os 8 do ticket foram usados como estão; os outros são palpites.
   - Todos estão em `scripts\story_post_seletores.py` e podem ser trocados pela configuração.
5. **Seletores do WhatsApp Web:** estão todos em `whatsapp_local\seletores.py`.
6. **`lotes\<dia>_estaticos.json`** (enquete das 16h): item `tipo: "story_enquete"` com `arquivo`, `pergunta` (≤ 25 caracteres), `opcoes` e `caixa_enquete`.
7. **Paleta dos canais:**
   - Os manuais e o `reel_futebol` usam uma proposta nova, que vale até ser trocada pela paleta de `posts_canais.py`/`estaticos.py`.
   - A página de links usa as mesmas cores do painel, com contraste WCAG conferido.

## 6. Decisões do Antônio (30/09/2026) — já aplicadas

1. **P0 roda também das 18h às 22h30.** Gol, placar, lançamento e bombástica são baixados e editados na hora; P1/P2 continuam esperando 22h30. O P0 ainda respeita o `pesado.lock` (1 pesado por vez). Chave `p0_na_janela` no `esteira\config.json` (padrão `true`). **A sessão HP GESTÃO precisa acrescentar essa exceção no CLAUDE.md da empresa.**
2. **O aviso "no ar" é montado só pelo `whatsapp_local`** (a partir do `agendados.json` + `AVISO.md`): `arquivo_agendados` vem como `"auto"` e acha o `agendados.json` do plantão sozinho. O da esteira fica desligado (`aviso_no_ar_habilitado: false`). Tudo começa em modo sombra: monta e compara, não envia.

Outras escolhas que valem até alguém mudar:
- **Volume da música no Futebol:** notícia e estatística, que só têm música, saem a −20 LUFS (baixa, mas audível); com áudio original a música fica 20 dB abaixo dele; o gol não tem música.
- **Critério de paridade:** para o dia passar, toda métrica precisa ter nota ≥ 9 e a média ≥ 9,5. Os limites de SSIM vêm de testes sintéticos e devem ser recalibrados depois dos primeiros dias reais, em `qa_paridade\limites.json`.
- **Manual 13 (afiliados):** marcado "FUTURO — NÃO IMPLEMENTAR"; nenhum código.

## 7. Onde está cada coisa

- Convenções e base comum: `docs\CONVENCOES.md`, `app\hp_studio\hpbase\`.
- Enunciado original: `docs\PROMPT_NUVEM.md`.
- Este compilado foi gerado por `python docs\compilar_entrega.py`, que cria `ENTREGA_NUVEM_HP_STUDIO.md` com o código completo de todos os arquivos.
