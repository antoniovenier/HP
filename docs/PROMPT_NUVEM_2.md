# Prompt para a sessão do Claude na nuvem — HP Studio, rodada 2: os formatos reais do PC (01/10/2026)

> **Como usar (Antônio ou Diretor):** cole tudo abaixo da linha numa sessão nova do Claude na nuvem. Quando ela terminar, peça: "compile tudo num único .md no formato da seção 2 (`## caminho/arquivo` + bloco de código), com o ENTREGA.md, o PATCHES.md e o PENDENCIAS_PARA_O_DIRETOR.md no começo", publique como artifact e mande o .md para a sessão HP GESTÃO integrar (`H:\HypadoLocal\temp\nuvem\desempacotar.py`).
> Este prompt **não contém token, senha nem id de conta**, de propósito. Números que parecem id (media_id de post, id de story) foram trocados por números falsos. Os links públicos de post são reais.

---

Você é o time de Tecnologia da **Hypado (HP)**, uma operação de 6 perfis de vídeos curtos no Brasil: **GTA 6 | HP** (@hpgta6, foco no lançamento do GTA 6 em 19/11/2026) e 5 canais — **Futebol | HP** (@hp.futebol), **Filmes e Séries | HP** (@hp.filmes), **Receitas | HP** (@hp.receitas), **Carros | HP** (@hp.carros) e **Destinos | HP** (@hp.destinos) — em Instagram, Facebook, TikTok, YouTube, Threads (e Pinterest). O dono é o **Antônio**, sócio único; fala português BR informal e quer execução, não explicação. **Objetivo nº 1: crescer e chegar à monetização o quanto antes, gastando menos token do Claude.** O **HP Studio** é o app local (Python, fila SQLite, CLI `hp`, tela em `http://127.0.0.1:8770`) que faz o trabalho mecânico; o Claude só julga (escolha, texto, revisão).

## 0. Onde você está, onde o código vai rodar e por que esta rodada existe

- **Você** roda em **Linux** (Python 3.11 + ffmpeg 7), **com internet** (use só na tarefa F). **Não tem acesso** ao PC do Antônio, ao Google Drive, ao Chrome, ao emulador Android, ao WhatsApp nem a nenhum token.
- **O código roda no PC**: Windows 11 Home, **PowerShell 5.1**, **Python 3.12.10**, Drive em `G:\Meu Drive\Hypado\` (a letra pode mudar), pesado e temporário em `H:\HypadoLocal\`, **nada no C:**.
- **Rodada 1 (30/09):** você entregou 176 arquivos (`hpbase`, `esteira`, `metricas`, `qa_paridade`, `whatsapp_local`, manuais 04–13, `story_post`, `reel_futebol`, `reenvio_seguro`, painel, página de links) e 554 testes. Foi integrado no PC como **pacote irmão** `06 Projeto\app\hp_studio_nuvem\` (+ `scripts\`), sem sobrescrever nada. Resultado no PC: 373 passed no pacote e 181 nos scripts, tudo verde. **Mas 5 das suas "suposições a confirmar" estavam erradas**, porque você não conhecia os formatos reais: o formato da `fila_api`, os parâmetros dos scripts (`ytdlp.py`, `dublar.py`, `estaticos.py`), os nomes das chaves de token, a chave `interativo` do lote de estáticos (e a pergunta real de 46 caracteres contra o limite de 25) e a paleta. O PC consertou à mão só o que bloqueava (fila e tokens). **Falta o resto, e falta refazer tudo no seu repositório**, para a próxima integração entrar sem remendo.
- **Esta rodada:** a **Seção 4 traz os formatos reais**, copiados do PC em 30/09–01/10 (sem nenhum segredo). **Trate a Seção 4 como verdade absoluta e como fixtures de teste**: copie cada JSON/trecho para `tests/fixtures/pc_real/<nome indicado>` no seu repositório e escreva os testes em cima deles. Se o repositório da sessão já tiver o código da rodada 1, trabalhe em cima dele; se não tiver, avise no `ENTREGA.md` e entregue só o que é novo, escrito contra os nomes de módulo da rodada 1 (`hpbase`, `esteira`, `metricas`, `whatsapp_local`, `qa_paridade`).

## 1. Regras que não podem ser quebradas

1. **Nada roda de verdade.** Nenhum teste, script ou módulo seu faz chamada de rede real (exceto a tarefa F: só leitura de páginas públicas, só durante a pesquisa), publica, liga emulador/celular, manda WhatsApp ou lê arquivo de segredo. Tudo que fala com rede, celular ou disco de produção recebe o **transporte injetado** (função ou objeto) e os testes usam um **falso**.
2. **Segurança.** Nunca digitar senha ou código, criar conta, aceitar termos, ler/imprimir/logar token, contornar CAPTCHA, nem tocar em "Entrar", "Permitir", "Aceitar", "Concordo", "Allow" no celular (quem faz é o Antônio). Tokens só em `H:\HypadoLocal\segredos\`: seu código só conhece o **nome** do arquivo e da chave; valores nos testes são `FAKE_NAO_E_TOKEN_<n>`. **Sem biblioteca que imita protocolo de rede social** (instagrapi, Baileys etc.): só API oficial, o app oficial num emulador/celular ou a página oficial.
3. **Compatível com Windows** (o código nasce no Linux e roda no Windows):
   - Python **3.11 e 3.12** com o mesmo código (nada de sintaxe só do 3.12);
   - `pathlib`; caminhos **com espaço** (`G:\Meu Drive\Hypado\06 Projeto\...`); nada de `/tmp` fixo (use `tempfile` ou a variável `HP_TMP`);
   - `encoding="utf-8"` explícito em todo `open`, `read_text`, `write_text` (o PowerShell 5.1 usa ANSI por padrão);
   - gravação atômica (`.tmp` + `os.replace`);
   - todo `subprocess` leva `creationflags=0x08000000` (CREATE_NO_WINDOW) quando `os.name == "nt"` (o motor roda por `pythonw`, sem console, e cada subprocesso sem a flag abre uma janela preta na tela do Antônio);
   - **HTTPS no PC é sempre pelo `curl.exe`** (o Avast quebra o HTTPS do Python). Por isso a rede entra por **transporte injetado**; `requests`/`urllib` direto não vão em código de produção;
   - Pillow **não desenha emoji colorido**: tire emoji de texto de arte (emoji só em legenda de post).
4. **Pacote irmão.** Seu código vive em `hp_studio_nuvem/` (ao lado do `hp_studio/` do PC). **Nunca** importe, sobrescreva ou dependa de `hp_studio.esteira` nem `hp_studio.metricas`: existem no PC com outro conteúdo. Os nomes curtos (`import esteira`, `import metricas`, `import hpbase`) continuam como na rodada 1, com `hp_studio_nuvem` no `sys.path`.
5. **Não reenvie o que já entregou.** Só arquivo novo, ou arquivo que muda. Arquivo da rodada 1 que muda vai descrito em `PATCHES.md` (por função); só reenvie o arquivo inteiro se mais da metade dele mudou.
6. **Regras de conteúdo que o código precisa respeitar:** Flow Games e vazamento de GTA 6 nunca passam; só criador com `autorizado: true` no `config.json`; futebol sem imagem de transmissão de TV e **nunca** narração sintética no futebol; música só livre de direitos; crédito do criador sempre; valor citado leva "Valores aproximados…"; nunca clonar voz. Trabalho pesado é **1 por vez** (`pesado.lock`) e nunca das 18h às 22h30 (exceção do Antônio: P0 da esteira). Story é leve e pode sair a qualquer hora.
7. **Lotes de no máximo 3 agentes ao mesmo tempo, e nunca 2 workflows juntos** (o plano do Claude do Antônio já estourou 3 vezes com agentes demais).
8. **Relatório com números reais:** o que rodou, quantos testes passaram, falharam e pularam, e quanto tempo levou. Nada de "deve funcionar".
9. **Afiliados é assunto futuro:** não desenvolva nada disso.
10. **Em dúvida sobre um formato, não invente.** Escreva no `ENTREGA.md`, seção "Suposições que sobraram", a suposição, o arquivo e a função exata onde trocar. Foi o que faltou na rodada 1: ela dizia "suposições a confirmar", mas elas estavam espalhadas.

## 2. Como entregar (o formato que funcionou na rodada 1 + o que quebrou)

Entregue **um único `.md`**. O PC usa o `desempacotar.py`, que corta o arquivo pelos cabeçalhos:

1. Cada arquivo = uma linha `## caminho/relativo/arquivo.ext` (só letras, números, `_`, `.`, `/`, `-`; **sem espaço e sem acento**; caminho relativo à raiz do repositório) seguida de **um bloco de código** com a linguagem. O 1º bloco depois do cabeçalho abre e o último fecha o arquivo. Se o arquivo contém cercas de três crases dentro dele (um `LEIA.md`, por exemplo), use **cerca externa de cinco crases**.
2. **Nenhuma linha dentro do conteúdo de um arquivo pode começar com `## ` seguido de algo que pareça nome de arquivo com extensão** (ex.: `## contas.json`). Na rodada 1 isso partiu o `LEIA.md` do `metricas` ao meio e criou um "arquivo" falso `contas.json`. Num documento escreva `## O arquivo de contas` ou indente a linha.
3. **Não crie arquivo com nome de segredo** (`contas.json`, `tokens*`, `segredos*`, `*.env`): o classificador de segurança do PC bloqueia a cópia. Use `contas_exemplo.json`.
4. No começo do `.md`, antes dos outros arquivos, venham os 3 documentos de controle (também no formato acima):
   - `## ENTREGA.md`:
     - (a) tabela módulo | arquivos novos | testes (passed/failed/skipped) | tempo | começa em (simulação ou sombra);
     - (b) como rodar os testes no PC (PowerShell 5.1, `$PY = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"`) e o número esperado;
     - (c) "Suposições que sobraram";
     - (d) o que depende do Antônio (token, permissão, clique), com passo a passo para leigo;
     - (e) o que você **não** conseguiu e por quê;
   - `## PATCHES.md`: para cada arquivo da rodada 1 que muda: arquivo, função, o que muda, por quê, teste que cobre;
   - `## PENDENCIAS_PARA_O_DIRETOR.md`: texto pronto para tudo que mexe em `.claude\` (rotinas, SKILLs). **Você não edita pasta `.claude`**: escreva o trecho exato e o arquivo onde o Diretor cola.
5. Cada módulo novo traz um `LEIA.md` curto (instalação e uso, 1 página, para leigo).
6. Sem binários. Imagens de teste são geradas pelos testes; fixtures são texto.
7. Os testes (pytest) ficam em `testes/` ao lado do módulo e **não dependem de rede, de relógio real (injete a hora), de Windows, de ffmpeg (a não ser onde a tarefa pede) nem da ordem de execução**.

## 3. O que já existe no PC (não refaça)

### 3.1 Mapa

```
G:\Meu Drive\Hypado\06 Projeto\
  scripts\                  scripts de sempre (4.4) + os seus da rodada 1 (story_post*.py, reel_futebol*.py, reenvio_seguro.py, painel\, pagina_links\)
  app\hp_studio\            app do PC: núcleo (etapa 1), cardápio/pauta (etapa 2), esteira\ (etapa 3, PC), metricas\ (PC),
                            paridade\ (PC), publicar\ (etapa 4: Facebook, YouTube, fila_facebook), trabalhos\, tela\
  app\hp_studio_nuvem\      a SUA entrega da rodada 1 (hpbase, esteira, metricas, qa_paridade, whatsapp_local)
  app\manuais\              manuais dos profissionais
  lotes\                    planos do GTA (AAAA-MM-DD_diario.json, AAAA-MM-DD_estaticos.json)
G:\Meu Drive\Hypado\07 Canais\<Pasta>\   Futebol | Filmes e Series | Gastronomia (= Receitas) | Carros | Viagens (= Destinos)
H:\HypadoLocal\             fila_api\, canais\, upload\, brutos\, transcricoes\, segredos\ (NUNCA abrir), android\, emulador\, app\, radar\, temp\
```

### 3.2 O que o PC ajustou nos SEUS arquivos (30/09 23h30; reproduza no seu repositório, com testes — é a tarefa A)

- `hpbase\trava.py`: o `pesado.lock` do PC é `{"quem": "...", "desde": "AAAA-MM-DDTHH:MM"}` (sem pid; trava abandonada vale 30 min). A sua era `{"dono", "pid", "desde": <epoch>}` e quebrava com `ValueError`. Agora lê os dois, e grava `quem` + `desde` ISO + `dono` + `pid` + `desde_epoch`.
- `esteira\config.py`: `pasta_scripts` aponta para `06 Projeto\scripts` quando a pasta existe (a sua apontava para `G:\Meu Drive\Hypado\scripts`, que não existe).
- `hpbase\caminhos.py`: a esteira da nuvem usa `H:\HypadoLocal\esteira_sombra` (variável `HP_ESTEIRA_NOME`) e a paridade `H:\HypadoLocal\app\paridade_nuvem` (`HP_PARIDADE_NOME`), porque o PC já usa `H:\HypadoLocal\esteira` e `...\app\paridade` com outro conteúdo.
- `hpbase\fila_api_pc.py` (novo, escrito no PC): `handle()`, `chave_token()`, `token_do_item()`, `id_da_conta()`, `inicio()`, `ler_confirmacao()`, `montar_item()`, `publicador_adaptado()`. Detalhes na tarefa A1.
- `metricas\config.py`: `chaves()` também procura os nomes reais de token (4.3); o Instagram fala com `graph.instagram.com`; resultado: `python -m metricas coletar --simular` → 0 `sem_token`.
- `esteira\agendador.py`: `montar_registro_fila` grava `conta` (handle), `arquivos[]` e `quando`; `ler_confirmacao` lê `feitos\`/`erros\`; em modo real recusa rede diferente de instagram/threads.
- `scripts\reenvio_seguro.py`: `quando` vale como início; `cliente_e_id` usa `IG_<handle>` + id do `meta_tokens_meta.json` + host `graph.instagram.com`; `achar_publicador` usa o adaptador.
- Testes no PC depois disso: pacote 387 passed (68 s); `scripts\testes\test_reenvio_seguro.py` 22 passed; `scripts\testes` 181 passed.

### 3.3 O que o PC já tem pronto e testado (você NÃO refaz; as tarefas B e C são só as **lacunas**)

- **Instagram e Threads pela API** em produção: `scripts\publicador_meta.py` (loop de 60 s). Formato em 4.1 e 4.2.
- **Facebook Página pela Graph API v26.0** (`hp_studio\publicar\facebook.py`, `fila_facebook.py`, 13 + token 12 testes): foto, carrossel (várias fotos), **reel** com agendamento nativo (`video_state=SCHEDULED`, 10 min a 29 dias, 30 reels/24 h por Página), **story** de foto/vídeo (a API não agenda: o app segura e solta na hora), texto; conferência (`is_published`, `permalink_url`); gêmeo automático de cada post do Instagram atrás da chave `facebook_api.json` (**desligada**).
- **YouTube pela Data API v3** (`hp_studio\publicar\youtube.py`, `youtube_token.py`, `youtube_envio.py`; 59 testes): OAuth loopback + PKCE, envio resumable com retomada, `private` + `publishAt` em UTC, categoria por canal, `containsSyntheticMedia` para dublado, **miniatura opcional** (`thumbnails.set`), limite de 100 envios/24 h, e a **detecção de "travado como privado"** (projeto sem auditoria: o `videos.insert` responde 200, mas o vídeo fica privado e o `publishAt` não vale). O Google ainda não aprovou a auditoria.
- **Radar** (`scripts\radar_hp.py` + `07 Canais\radar\{gta,futebol,filmes,carros}.json`): ver 4.10.
- **Esteira local** (`hp_studio\esteira\`: `pedido.py`, `pastas.py`, `etapas.py`, `ferramentas.py`, `textos.py`): é a que vale no PC. A sua (`hp_studio_nuvem\esteira`) é a segunda opinião; a fusão só depois do modo sombra. O formato real do pedido está em 4.5.
- **Métricas** locais (`hp_studio\metricas\`): IG, Threads, Facebook, YouTube; grava `metricas\AAAA-MM-DD_api.json`.

---

## 4. OS FORMATOS REAIS (copie para `tests/fixtures/pc_real/`)

Tudo desta seção veio de arquivos e código reais do PC. Onde diz "fixture:", salve o bloco com aquele nome.

### 4.1 A fila da API do Instagram e do Threads (`H:\HypadoLocal\fila_api\`)

Layout real (contagens de 30/09 23h40):

```
H:\HypadoLocal\fila_api\
  <id>.json                itens esperando a hora. A volta do publicador (a cada 60 s) olha só os *.json desta pasta;
                           ignora nome que começa com "_" e o limite_24h.json
  feitos\<id>.json         saiu: ganha "status": "no_ar" e "resultado" {media_id, permalink, publicado_em}   (62 arquivos)
  erros\<id>.json          falhou 2 vezes, inválido ou atrasado mais de 12 h: ganha "erro" (inválido/atrasado)
                           ou "ultimo_erro" + "tentativas"                                                     (4 arquivos)
  removidos\<motivo>\      itens tirados à mão (api_bloqueada_2026-09-29, reels_repetidos_2026-09-29)
  reserva_largada\         posts guardados pela "largada devagar" dos canais novos (9)
  story_clicavel\          stories de "post novo" tirados da fila: passam a ser feitos pelo emulador (story_clicavel.py)
  facebook\                (ainda não existe) gêmeos "_fb_" quando a chave facebook_api.json for ligada
  limite_24h.json          {"IG_<conta>": ["AAAA-MM-DD HH:MM", ...]}  hora de cada publicação das últimas 24 h
  publicador.log           linhas "AAAA-MM-DD HH:MM:SS texto"
  .trava                   "<pid> <data hora>"; vale 20 min
```

**Convenção dos ids** (o id é o nome do arquivo sem `.json`):

- canais: `<canal>_<AAAA-MM-DD>_<HHMM>_<slug>_<ig|th>_<tipo>` (ex.: `carros_2026-09-30_2315_novo-bmw-serie-3_ig_carrossel`);
- textos do Threads dos canais: `<canal>_th_<AAAA-MM-DD>_<HHMM>_<lote>_<n>`;
- GTA: `gta_<AAAA-MM-DD>_<ig|th>_<tipo>_<HHMM>` (ex.: `gta_2026-10-01_th_texto_1200`).
- O **story irmão** de um post, `<base>_ig_story`, só sai depois que `<base>_ig_carrossel|reel|feed` está em `feitos\` (regra `post_que_falta`, 4.2). O campo `depende_de` faz o mesmo para qualquer item.

**Regras do formato** (vêm do código real, 4.2): `rede` ∈ `instagram`|`threads` (Facebook **não** entra por esta fila); `tipo` ∈ `feed|carrossel|reel|story|texto`; `quando` = `"AAAA-MM-DD HH:MM"` em **hora de Brasília, sem fuso** (aceita `T`); `arquivos[]` com caminho absoluto que **existe**; `legenda` ≤ 2.200 (IG) e ≤ 500 (Threads); feed = 1 imagem; reel = 1 vídeo; carrossel = 2–10 arquivos no IG e 2–20 no Threads; story = 1 arquivo; texto do Threads = `arquivos: []`; `capa` opcional (reel); `titulo` e `grupo_whatsapp` são usados pelo plantão do WhatsApp; item vencido há mais de 12 h vai para `erros\` ("venceu há mais de 12:00:00 e não saiu"), a menos que traga `"publicar_mesmo_atrasado": true`.

**fixture: `fila_api_reel_pendente_gta.json`** (um reel que ainda NÃO saiu; depois de sair ele ganha `resultado` e `status`, como nos feitos abaixo):

```json
{
 "id": "gta_2026-10-02_ig_reel_1200",
 "conta": "hpgta6",
 "rede": "instagram",
 "tipo": "reel",
 "arquivos": ["H:\\HypadoLocal\\upload\\02_10_2026_12h00_a_rockstar_mandou_um_presente.mp4"],
 "legenda": "Chegou uma caixa da Rockstar na porta dele, sem aviso 📦 Dentro: boné rosa e azul, camiseta de Vice City, adesivos [...] Qual item você queria? 🎥 Corte: TmarTn2 (canal TmarTn2 no YouTube), dublado por HP 🔔 Segue a @hpgta6 pra mais cortes de GTA 6 #gta6 #gtavi #gta #rockstargames #tmartn2 #cortes #games",
 "quando": "2026-10-02 12:00",
 "canal": "gta",
 "grupo_whatsapp": "HP | Comissão 🚀"
}
```

**fixture: `fila_api_feitos_ig_feed_futebol.json`**:

```json
{
 "id": "futebol_2026-09-30_2320_jj-quem-decide_ig_feed",
 "conta": "hp.futebol",
 "rede": "instagram",
 "tipo": "feed",
 "arquivos": ["H:\\HypadoLocal\\canais\\futebol\\noticias\\2026-09-30_1700\\jj\\frase\\frase_feed.jpg"],
 "legenda": "\"Quem decide sou eu\" 🗣️ O recado do Mister na coletiva de Portugal em Copenhague, antes de Cristiano Ronaldo deixar a concentração.\n\n📌 Jorge Jesus disse que, em princípio, Gonçalo Ramos jogaria contra a Dinamarca [...]\n🔜 Portugal pega a Dinamarca amanhã (1/10), 15h45 de Brasília, pela Nations League, sem o camisa 7.\n\nO Mister tá certo ou passou do ponto? Comenta aí 👇\n\nFonte: coletiva de Jorge Jesus (via RTP e A Bola) e comunicado da Federação Portuguesa de Futebol\nFoto: Sportreport / Wikimedia Commons (CC BY 3.0)\n\nSiga @hp.futebol\n#futebol #jorgejesus #cristianoronaldo #cr7 #portugal",
 "quando": "2026-09-30 23:20",
 "canal": "futebol",
 "grupo_whatsapp": "HP | Futebol ⚽",
 "titulo": "Jorge Jesus: \"Quem decide sou eu\" (treta com CR7)",
 "resultado": {
  "media_id": "18100000000000001",
  "permalink": "https://www.instagram.com/p/Dd70ZtCFSND/",
  "publicado_em": "2026-09-30 23:18"
 },
 "status": "no_ar"
}
```

**fixture: `fila_api_feitos_ig_carrossel_carros.json`** (carrossel de 7 lâminas; legenda encurtada aqui):

```json
{
 "id": "carros_2026-09-30_2315_novo-bmw-serie-3_ig_carrossel",
 "conta": "hp.carros",
 "rede": "instagram",
 "tipo": "carrossel",
 "arquivos": [
  "H:\\HypadoLocal\\canais\\carros\\lancamentos\\2026-09-30_2315_novo-bmw-serie-3\\01.jpg",
  "H:\\HypadoLocal\\canais\\carros\\lancamentos\\2026-09-30_2315_novo-bmw-serie-3\\02.jpg",
  "H:\\HypadoLocal\\canais\\carros\\lancamentos\\2026-09-30_2315_novo-bmw-serie-3\\03.jpg",
  "H:\\HypadoLocal\\canais\\carros\\lancamentos\\2026-09-30_2315_novo-bmw-serie-3\\04.jpg",
  "H:\\HypadoLocal\\canais\\carros\\lancamentos\\2026-09-30_2315_novo-bmw-serie-3\\05.jpg",
  "H:\\HypadoLocal\\canais\\carros\\lancamentos\\2026-09-30_2315_novo-bmw-serie-3\\06.jpg",
  "H:\\HypadoLocal\\canais\\carros\\lancamentos\\2026-09-30_2315_novo-bmw-serie-3\\07.jpg"
 ],
 "legenda": "LANÇAMENTO! 🔥 A BMW revelou o novo Série 3\n\nA 8ª geração do BMW mais vendido da história [...]\n\nElétrico ou a combustão: qual Série 3 você levaria? 👇\n\nFonte: BMW (PressClub, 30/09/2026). Dados provisórios do mercado europeu.\nFotos: divulgação/BMW\n\nSiga @hp.carros\n\n#bmw #bmwserie3 #serie3 #bmwi3 #m350 #lancamento #carros #hpcarros",
 "quando": "2026-09-30 23:01",
 "canal": "carros",
 "grupo_whatsapp": "HP | Carros 🏎️",
 "titulo": "O novo BMW Série 3 chegou: 469 cv e 912 km de autonomia no i3 elétrico",
 "resultado": {
  "media_id": "18100000000000002",
  "permalink": "https://www.instagram.com/p/Dd7ytwrlQye/",
  "publicado_em": "2026-09-30 23:03"
 },
 "status": "no_ar"
}
```

**fixture: `fila_api_feitos_th_feed_futebol.json`** (o mesmo post no Threads: texto curto, a mesma imagem):

```json
{
 "id": "futebol_2026-09-30_2320_jj-quem-decide_th_feed",
 "conta": "hp.futebol",
 "rede": "threads",
 "tipo": "feed",
 "arquivos": ["H:\\HypadoLocal\\canais\\futebol\\noticias\\2026-09-30_1700\\jj\\frase\\frase_feed.jpg"],
 "legenda": "\"Quem decide sou eu\" 🗣️ Jorge Jesus na coletiva de Portugal, antes de CR7 deixar a concentração em Copenhague. O Mister tá certo ou passou do ponto com o camisa 7? 👇\n\nFonte: coletiva de Jorge Jesus (via RTP e A Bola)",
 "quando": "2026-09-30 23:20",
 "canal": "futebol",
 "grupo_whatsapp": "HP | Futebol ⚽",
 "titulo": "Jorge Jesus: \"Quem decide sou eu\" (treta com CR7)",
 "resultado": {
  "media_id": "18100000000000003",
  "permalink": "https://www.threads.com/@hp.futebol/post/Dd70cgAlbPX",
  "publicado_em": "2026-09-30 23:18"
 },
 "status": "no_ar"
}
```

**fixture: `fila_api_feitos_ig_story_futebol.json`** (story de imagem avulsa, saiu pela API):

```json
{
 "id": "futebol_2026-09-30_1707_cr7-deixa-portugal_ig_story",
 "conta": "hp.futebol",
 "rede": "instagram",
 "tipo": "story",
 "arquivos": ["H:\\HypadoLocal\\canais\\futebol\\noticias\\2026-09-30_1700\\cr7\\post\\urgente_story.jpg"],
 "legenda": "",
 "quando": "2026-09-30 17:08",
 "canal": "futebol",
 "grupo_whatsapp": "HP | Futebol ⚽",
 "titulo": "CR7 deixa a concentração de Portugal após a coletiva de Jorge Jesus",
 "resultado": {
  "media_id": "18100000000000004",
  "permalink": "https://www.instagram.com/stories/hp.futebol/3990000000000000001",
  "publicado_em": "2026-09-30 17:07"
 },
 "status": "no_ar"
}
```

**fixture: `fila_api_erros_th_carrossel_carros.json`** (erro de validação: a mídia ainda não tinha sido gerada; vai para `erros\`):

```json
{
 "id": "carros_2026-10-01_0930_bmw-serie-3-o-que-mudou_th_carrossel",
 "conta": "hp.carros",
 "rede": "threads",
 "tipo": "carrossel",
 "arquivos": [
  "H:\\HypadoLocal\\canais\\carros\\lancamentos\\2026-10-01_0930_bmw-serie-3-o-que-mudou\\01.jpg",
  "H:\\HypadoLocal\\canais\\carros\\lancamentos\\2026-10-01_0930_bmw-serie-3-o-que-mudou\\02.jpg"
 ],
 "legenda": "O QUE MUDOU? 👀 Novo BMW Série 3 x o antigo, lado a lado\n\nPor fora, o novo cresceu: 4.765 mm de comprimento [...]\n\nSiga @hp.carros",
 "quando": "2026-10-01 09:30",
 "canal": "carros",
 "grupo_whatsapp": "HP | Carros 🏎️",
 "titulo": "Novo x antigo: o que mudou no BMW Série 3",
 "erro": "arquivo não existe: H:\\HypadoLocal\\canais\\carros\\lancamentos\\2026-10-01_0930_bmw-serie-3-o-que-mudou\\01.jpg"
}
```

(O original tem 7 lâminas; encurtei para 2 aqui. Erro por falha de rede/API em vez de validação teria `"ultimo_erro": "<texto>"` e `"tentativas": 2`, sem `"erro"`.)

**fixture: `fila_api_texto_th_gta.json`** (post de texto do Threads: `arquivos` vazio):

```json
{
 "id": "gta_2026-10-01_th_texto_1200",
 "conta": "hpgta6",
 "rede": "threads",
 "tipo": "texto",
 "arquivos": [],
 "legenda": "📰 A Game Informer revelou que o GTA 6 tem mais de 170 espécies de animais em terra, no ar e no mar.\n\nTem flamingo, peixe-boi, pelicano e jacaré [...]\n\nQual você quer encontrar primeiro? 🐊\n\nFonte: Game Informer, edição 382",
 "quando": "2026-10-01 12:00",
 "canal": "gta",
 "grupo_whatsapp": "HP | Comissão 🚀",
 "titulo": "📰 A Game Informer revelou que o GTA 6 tem mais de 170 espécies de animais em terra, no ar e no mar."
}
```

**fixture: `fila_api_story_clicavel_parqueado.json`** (story de "post novo" tirado da fila e guardado em `story_clicavel\`; ganha `parqueado_em` e `origem_pasta`):

```json
{
 "id": "carros_2026-10-01_1230_hb20-x-onix_ig_story",
 "rede": "instagram",
 "tipo": "story",
 "arquivos": ["H:\\HypadoLocal\\canais\\carros\\lote-01\\2026-10-01_1230_hb20-x-onix\\story.jpg"],
 "legenda": "",
 "quando": "2026-10-01 12:40",
 "titulo": "Story: HB20 x Onix",
 "conta": "hp.carros",
 "canal": "carros",
 "grupo_whatsapp": "HP | Carros 🏎️",
 "parqueado_em": "2026-09-30 17:35",
 "origem_pasta": "raiz"
}
```

**fixture: `fila_api_limite_24h.json`**:

```json
{
 "IG_hp.futebol": ["2026-09-30 11:00", "2026-09-30 11:08", "2026-09-30 23:18"],
 "TH_hp.carros": ["2026-09-30 09:58", "2026-09-30 23:06"],
 "IG_hpgta6": []
}
```

**fixture: `fila_api_publicador.log`** (linhas reais; a ordem do fluxo de um carrossel no Threads e de um feed no Instagram):

```
2026-09-30 23:04:38 hospedado (uguu, 226 KB): 04.jpg -> https://d.uguu.se/<nome>.jpg
2026-09-30 23:06:06 NO AR carros_2026-09-30_2315_novo-bmw-serie-3_th_carrossel: https://www.threads.com/@hp.carros/post/Dd7y-0jlRrY
2026-09-30 23:18:08 publicando futebol_2026-09-30_2320_jj-quem-decide_ig_feed (instagram feed @hp.futebol, marcado 2026-09-30 23:20)
2026-09-30 23:18:30 NO AR futebol_2026-09-30_2320_jj-quem-decide_ig_feed: https://www.instagram.com/p/Dd70ZtCFSND/
2026-09-30 23:21:02 fila: carros_2026-10-01_0930_bmw-serie-3-o-que-mudou_ig_carrossel.json inválido: arquivo não existe: H:\HypadoLocal\canais\carros\lancamentos\2026-10-01_0930_bmw-serie-3-o-que-mudou\01.jpg
```

### 4.2 `scripts\publicador_meta.py` — a docstring, o argparse e as funções que a fila usa

Em **produção** (loop desde 30/09 14h10). **Você não mexe nele**: só chama por fora, com o transporte injetado. A docstring real:

```python
"""Publicador pela API da Meta (app "HP Publicador", 28/09/2026): Instagram (login do Instagram) e Threads,
sem Chrome, para as 6 marcas (@hpgta6, @hp.futebol, @hp.filmes, @hp.receitas, @hp.carros, @hp.destinos).

Tokens: H:/HypadoLocal/segredos/meta_tokens.txt, uma linha por conta: IG_<conta>=<token> e TH_<conta>=<token>.
NUNCA imprimir, logar ou copiar token: ele só existe dentro deste script e vai para o curl.exe pelo stdin
(nunca na linha de comando). Toda saída passa por _limpar(), que troca qualquer token por ***.
Datas de renovação e ids (sem tokens) ficam em meta_tokens_meta.json na mesma pasta.

HTTPS sempre pelo curl.exe do Windows (o Python quebra no HTTPS por causa do Avast).

Mídia: a API exige link público (image_url/video_url). Hospedagem temporária sem conta:
litterbox.catbox.moe (24 h) e, se falhar, uguu.se (3 h). Em 28/09/2026 o litterbox não conecta
deste PC e o 0x0.st desligou os uploads; o uguu.se funciona.

Uso:
  publicador_meta.py tokens                 situação de cada conta (sem mostrar token)
  publicador_meta.py ids                    busca e guarda o id/username de cada conta
  publicador_meta.py renovar [--forcar]     renova o que faltar < 15 dias (regrava o .txt)
  publicador_meta.py testar [--simular]     cria 1 container de imagem (IG) e 1 de texto (Threads) por conta, SEM publicar
  publicador_meta.py hospedar <arquivo>     sobe um arquivo e mostra o link direto
  publicador_meta.py enfileirar --conta hp.futebol --rede instagram --tipo feed --arquivos a.jpg
                                 --legenda "..." --quando "2026-09-30 12:00" [--canal futebol] [--id x]
  publicador_meta.py rodar [--simular]      publica o que venceu na fila (H:/HypadoLocal/fila_api)
  publicador_meta.py loop                   roda a fila a cada 60 s, das 06h00 às 00h40

Facebook (30/09/2026): com "ativo": true em H:/HypadoLocal/publicador/facebook_api.json, cada post do Instagram
ganha o gêmeo na Página do canal, depois do IG e do Threads de cada volta (app/hp_studio/publicar/fila_facebook.py).
Desligado (padrão, ou sem o arquivo), nada muda aqui e o módulo do Facebook nem é importado.
"""
```

O argparse real (`main()`):

```python
ap = argparse.ArgumentParser(description="Publicador pela API da Meta (Instagram + Threads)")
sub = ap.add_subparsers(dest="cmd", required=True)
sub.add_parser("tokens")
s = sub.add_parser("ids");        s.add_argument("--simular", action="store_true")
s = sub.add_parser("renovar");    s.add_argument("--forcar", action="store_true"); s.add_argument("--simular", action="store_true")
s = sub.add_parser("testar");     s.add_argument("--simular", action="store_true")
s = sub.add_parser("hospedar");   s.add_argument("arquivo")
s = sub.add_parser("rodar");      s.add_argument("--simular", action="store_true")
sub.add_parser("loop")
s = sub.add_parser("enfileirar")
s.add_argument("--conta"); s.add_argument("--canal")
s.add_argument("--rede", required=True, choices=["instagram", "threads"])
s.add_argument("--tipo", required=True, choices=["feed", "carrossel", "reel", "story", "texto"])
s.add_argument("--arquivos", nargs="*"); s.add_argument("--legenda"); s.add_argument("--titulo"); s.add_argument("--capa")
s.add_argument("--quando", help='"AAAA-MM-DD HH:MM" (vazio = agora)'); s.add_argument("--id")
```

Constantes e funções reais. `normalizar_conta`, `ler_tokens`, `api`, `_quando`, `_validar` e `post_que_falta` são **literais**; `http`, `publicar_item` e `rodar` estão **resumidos** (`[...]` marca o que cortei), mas na ordem real dos passos e com as mesmas mensagens:

```python
RAIZ = Path(__file__).resolve().parent.parent          # 06 Projeto
SEGREDOS = Path("H:/HypadoLocal/segredos")
TOKENS_TXT = SEGREDOS / "meta_tokens.txt"
TOKENS_META = SEGREDOS / "meta_tokens_meta.json"
FILA = Path("H:/HypadoLocal/fila_api"); FEITOS = FILA / "feitos"; ERROS = FILA / "erros"
IG_VER = os.environ.get("HP_IG_VER", "v21.0"); TH_VER = "v1.0"
IG_BASE = "https://graph.instagram.com"; TH_BASE = "https://graph.threads.net"
LIMITE_IG_24H = 100     # 100 posts publicados via API por conta a cada 24 h (carrossel conta 1)
LIMITE_TH_24H = 250
TOLERANCIA = timedelta(minutes=2)
ATRASO_MAX = timedelta(hours=12)
FACEBOOK_CHAVE = Path("H:/HypadoLocal/publicador/facebook_api.json")

# canal -> (conta, pasta do agendados.json, grupo do WhatsApp)
CANAIS = {
    "gta": ("hpgta6", RAIZ, "HP | Comissão 🚀"),
    "futebol": ("hp.futebol", CANAIS_DIR / "Futebol", "HP | Futebol ⚽"),
    "filmes": ("hp.filmes", CANAIS_DIR / "Filmes e Series", "HP | Filmes 🎬"),
    "receitas": ("hp.receitas", CANAIS_DIR / "Gastronomia", "HP | Receitas 🍔"),
    "carros": ("hp.carros", CANAIS_DIR / "Carros", "HP | Carros 🏎️"),
    "destinos": ("hp.destinos", CANAIS_DIR / "Viagens", "HP | Destinos ✈️"),
}
EXT_VIDEO = {".mp4", ".mov"}; EXT_IMAGEM = {".jpg", ".jpeg", ".png", ".webp"}


class ErroAPI(Exception):
    pass


def normalizar_conta(conta):
    conta = (conta or "").strip().lstrip("@").lower()
    if conta in CANAIS:  # aceita o nome do canal ("futebol") no lugar da conta
        conta = CANAIS[conta][0]
    return conta


def ler_tokens():
    """{"IG_hpgta6": token, ...} só com as linhas preenchidas."""
    toks = {}
    if not TOKENS_TXT.exists():
        return toks
    for linha in TOKENS_TXT.read_text(encoding="utf-8-sig").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        chave, valor = chave.strip(), valor.strip().strip('"').strip("'")
        m = re.match(r"^(IG|TH)_@?(.+)$", chave, re.I)
        if not m or not valor:
            continue
        chave = f"{m.group(1).upper()}_{normalizar_conta(m.group(2))}"
        toks[chave] = valor
        _SEGREDOS_CARREGADOS.add(valor)
    return toks


def http(metodo, url, params=None, form_arquivo=None, timeout=120, simular=False):
    """Chama o curl.exe com a configuração pelo stdin (o token nunca aparece na linha de comando).
    params vão como data-urlencode (POST) ou query (GET). Devolve (status, corpo em dict ou texto)."""
    # [...] monta a config do curl: url, silent, show-error, max-time, connect-timeout, write-out "\n%{http_code}",
    #       "get" se GET, data-urlencode por param, form por arquivo
    if simular:
        # imprime o pedido com access_token="***" e devolve:
        return 200, {"id": "SIMULADO", "status_code": "FINISHED", "status": "FINISHED", "permalink": "https://simulado"}
    r = subprocess.run(["curl.exe", "-K", "-"], input="\n".join(cfg).encode("utf-8"), capture_output=True,
                       timeout=timeout + 30, creationflags=0x08000000 if os.name == "nt" else 0)
    # [...] corpo, _, codigo = saida.rpartition("\n"); json.loads(corpo) ou texto; returncode != 0 -> ErroAPI


def api(metodo, url, params, simular=False, timeout=120):
    codigo, dados = http(metodo, url, params, timeout=timeout, simular=simular)
    if codigo >= 400 or (isinstance(dados, dict) and "error" in dados):
        erro = dados.get("error", dados) if isinstance(dados, dict) else dados
        raise ErroAPI(_limpar(f"HTTP {codigo}: {json.dumps(erro, ensure_ascii=False)[:600]}"))
    if not isinstance(dados, dict):
        raise ErroAPI(_limpar(f"HTTP {codigo}: resposta inesperada {str(dados)[:300]}"))
    return dados


def _quando(item):
    return datetime.strptime(item["quando"].replace("T", " ")[:16], "%Y-%m-%d %H:%M")


def _validar(item):
    for campo in ("id", "rede", "tipo", "quando"):
        if not item.get(campo):
            raise ErroAPI(f"campo '{campo}' faltando")
    if item["rede"] not in ("instagram", "threads"):
        raise ErroAPI("rede tem que ser instagram ou threads (Facebook continua pelo Business Suite)")
    _quando(item)
    item["conta"] = normalizar_conta(item.get("conta") or item.get("canal"))
    if item["conta"] not in PERFIS:
        raise ErroAPI(f"conta desconhecida: {item['conta']}")
    item.setdefault("canal", CONTA_CANAL[item["conta"]])
    item["arquivos"] = [str(Path(a) if Path(a).is_absolute() else FILA / a) for a in item.get("arquivos") or []]
    for a in item["arquivos"] + ([item["capa"]] if item.get("capa") else []):
        if not Path(a).exists():
            raise ErroAPI(f"arquivo não existe: {a}")


RX_STORY_DE_POST = re.compile(r"^(?P<base>.+)_(?P<rede>ig|th)_story$")


def post_que_falta(item):
    """Id do post de que este item depende e que ainda NÃO está no ar; None se pode sair."""
    ids = [item["depende_de"]] if item.get("depende_de") else []
    if not ids and item.get("tipo") == "story":
        m = RX_STORY_DE_POST.match(str(item.get("id") or ""))
        if m:
            ids = [f"{m['base']}_{m['rede']}_{t}" for t in ("carrossel", "reel", "feed")]
    falta = None
    for i in ids:
        if (FEITOS / f"{i}.json").exists():
            return None
        if any((p / f"{i}.json").exists() for p in (FILA, ERROS, FILA / "reserva_largada", FILA / "removidos")):
            falta = falta or i
    return falta  # None também quando o post irmão não existe em lugar nenhum (story avulso)


def publicar_item(item, toks, meta, simular=False):
    """-> dict {"media_id", "permalink", "publicado_em": "AAAA-MM-DD HH:MM"}  ou a string "limite"
    (100 posts do IG / 250 do Threads nas últimas 24 h). Levanta ErroAPI."""
    rede, conta = item["rede"], item["conta"]
    chave = ("IG_" if rede == "instagram" else "TH_") + conta
    tok = toks.get(chave)
    if not tok and not simular:
        raise ErroAPI(f"sem token {chave} em meta_tokens.txt")
    # [...] id da conta = meta["contas"][chave]["id"] (se faltar, busca por GET /me); "aviso" no meta = erro
    # [...] limite 24 h; depois ig_publicar(...) ou th_publicar(...)
    res["publicado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    return res


def rodar(simular=False):
    toks = ler_tokens(); meta = carregar_meta(toks)
    agora = datetime.now()
    for arq in sorted(FILA.glob("*.json")):
        if arq.name.startswith("_") or arq.name == LIMITE_JSON.name:
            continue
        item = _json(arq)
        try:
            _validar(item); quando = _quando(item)
        except (ErroAPI, ValueError, KeyError) as e:           # inválido -> erros/ com "erro"
            item["erro"] = str(e); _gravar_json(ERROS / arq.name, item); arq.unlink(); continue
        if quando - TOLERANCIA > agora:                       # ainda não é a hora
            continue
        if agora - quando > ATRASO_MAX and not item.get("publicar_mesmo_atrasado"):
            item["erro"] = f"venceu há mais de {ATRASO_MAX} e não saiu (decidir se ainda vale)"   # -> erros/
            continue
        if post_que_falta(item):                              # story espera o post dele
            continue
        try:
            res = publicar_item(item, toks, meta, simular)
            if res == "limite":                               # fica na fila
                continue
            item["resultado"] = res; item["status"] = "no_ar"; item.pop("_links_midia", None)
            registrar_no_ar(item)                             # grava em <canal>\agendados.json (4.5) para o plantão avisar
            _gravar_json(FEITOS / arq.name, item); arq.unlink()
        except (ErroAPI, subprocess.TimeoutExpired, OSError) as e:
            item["tentativas"] = int(item.get("tentativas", 0)) + 1
            item["ultimo_erro"] = _limpar(e)
            if item["tentativas"] >= 2:
                _gravar_json(ERROS / arq.name, item); arq.unlink()   # 2 falhas -> erros/
            else:
                _gravar_json(arq, item)                              # 1 nova tentativa na próxima volta
    if facebook_ativo():
        _rodar_facebook(resumo, simular)                      # gêmeo do Facebook (chave desligada hoje)
    return resumo   # {"publicados": [...], "erros": [...], "adiados_limite": [...], "pendentes": N}
```

Atenção ao `simular` real do PC: `publicar_item(..., simular=True)` **ainda hospeda o arquivo** (o `hospedar()` não olha o `simular`). Por isso o seu adaptador **nunca** chama o publicador real em simulação.

### 4.3 Tokens e segredos: só os NOMES (lidos do código, não dos arquivos)

Tudo em `H:\HypadoLocal\segredos\`. **Não abra nem peça nenhum desses arquivos.** O que existe:

| Arquivo | Formato (linha ou chave) | Quem grava |
|---|---|---|
| `meta_tokens.txt` | `IG_<conta>=<token>` e `TH_<conta>=<token>`, uma por linha; `<conta>` = handle sem `@`, minúsculo, **pode ter ponto** (`IG_hpgta6`, `TH_hp.futebol`); aceita `@`, aspas, linhas `#` | Antônio cola; `publicador_meta.py renovar` regrava o valor |
| `meta_tokens_meta.json` | `{"contas": {"IG_hpgta6": {"id", "username", "app_scoped_id", "impressao", "visto_em", "expira_em", "expira_estimada", "renovado_em", "ids_em", "erro", "aviso"}}, "ultima_checagem_renovacao", "ultimo_teste"}` — **sem token**; o `id` não é segredo | `publicador_meta.py` |
| `facebook_tokens.txt` | `FB_<canal>=<token da Página>`; `<canal>` = `gta|futebol|filmes|receitas|carros|destinos` (**não** é handle) | `hp publicar facebook-token` |
| `facebook_paginas.json` | `{canal: {"id", "nome", "expira"}}` — sem token | idem |
| `facebook_token_usuario.txt` | 1 linha: o token que o Antônio cola (temporário) | Antônio |
| `meta_app.txt` | `APP_ID=...` e `APP_SECRET=...` (opcional) | Antônio |
| `youtube_client.json` | o JSON baixado do Google Cloud ("App para computador": `{"installed": {...}}`) | Antônio |
| `youtube.json` | `{"api_key"?, "canais": {canal: "UC..."}, "oauth": {"client_id", "client_secret", "refresh_tokens": {canal: "1//..."}}}` | `hp publicar youtube-autorizar --canal X` |
| `youtube_canais.json` | `{canal: {"id", "titulo", "escopos", "autorizado_em", "vence_em", "projeto"}}` — sem token | idem |
| `pinterest_tokens.txt` | `PIN_<canal>=<token de acesso>` | Antônio |

Regras: ler só na hora do uso; tudo que sai (tela, log, erro, arquivo, teste) passa por um `limpar()` que troca qualquer segredo já lido por `***` (o `publicar\segredos.py` do PC também mascara os padrões `access_token=…`, `refresh_token=…`, `client_secret=…` e `Authorization: Bearer …`); id de conta **não** é segredo (aparece no `meta_tokens_meta.json`), token é. Nos seus testes, crie esses arquivos numa pasta temporária com valores `FAKE_NAO_E_TOKEN_<n>` e **prove que o valor falso nunca aparece** na saída, no log nem em exceção.

### 4.4 Os scripts reais (`G:\Meu Drive\Hypado\06 Projeto\scripts\`): a linha de comando de cada um

Rodei `python x.py --help` em cada um (só leitura). **Atenção:** `lote.py` e `versao_upload.py` **não têm argparse** (`--help` não existe: o primeiro quebra com `IndexError`, o segundo tenta abrir um arquivo chamado `--help`). Nenhum teste seu pode chamá-los com `--help`. `emenda.py` é só módulo (sem CLI). Python do PC: `%LOCALAPPDATA%\Programs\Python\Python312\python.exe`.

**`ytdlp.py`** — é só passagem para o yt-dlp com os certificados do Windows (**`--saida` NÃO existe**; use as opções do próprio yt-dlp: `-o`, `-f`, `--download-sections`…). Código inteiro:

```python
"""yt-dlp usando os certificados do Windows. Uso: python ytdlp.py <os mesmos argumentos do yt-dlp>"""
import sys
import truststore
truststore.inject_into_ssl()
from yt_dlp import main  # noqa: E402
sys.exit(main())
```

**`baixar.py`** — baixa um trecho e grava a ficha do crédito. Usa o `ytdlp.py` por baixo:

```
usage: baixar.py [-h] [--id-streamer ID_STREAMER] [--so-trecho INICIO FIM] url
```

Efeito real: grava `H:\HypadoLocal\brutos\<streamer_id|avulso>_<id do vídeo>.mp4` e `...\brutos\<mesmo nome>.json` (ficha: `id, titulo, canal, canal_url, duracao_seg, url, credito, streamer_id, autorizado, arquivo, trecho_baixado`). O comando do yt-dlp que a função `baixar(url, destino, inicio, fim)` monta (o trecho é baixado com `--download-sections "*INI-FIM" --force-keyframes-at-cuts`; INI/FIM em `HH:MM:SS.mmm`):

```python
["<python.exe>", "<...>\\ytdlp.py", "-f", "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080]/b",
 "--merge-output-format", "mp4", "-o", "<destino.mp4>", "--no-playlist", "--no-warnings",
 "--download-sections", "*00:03:22.000-00:04:08.000", "--force-keyframes-at-cuts", "<url>"]
```

**`transcrever.py`** — Whisper local (faster-whisper, modelo `small`, CPU, int8, `vad_filter`):

```
usage: transcrever.py [-h] [--id-streamer ID_STREAMER] arquivo
```

Grava `H:\HypadoLocal\transcricoes\<nome do arquivo sem extensão>.json` no formato de 4.5 (`segmentos` com `palavras` cronometradas). `idioma` vem do criador no `config.json` (`"en"` = gringo). Há `corrigir(texto, correcoes)` (troca palavra inteira, mantém maiúscula/minúscula) e `montar_vocabulario(cfg, streamer)`.

**`cortar.py`** — o render final 9:16 (janela com cantos arredondados, legenda queimada palavra a palavra, gancho, crédito, marca, cartão "segue a gente"), áudio a **-14 LUFS** (`loudnorm=I=-14:TP=-1.5:LRA=11`), 1080x1920, 30 fps:

```
usage: cortar.py [-h] --inicio INICIO --fim FIM [--gancho GANCHO] [--credito CREDITO]
                 [--id-streamer ID_STREAMER] [--saida SAIDA] [--transcricao TRANSCRICAO]
                 [--fade-saida FADE_SAIDA] [--dublar] arquivo
```

**`lote.py`** — o orquestrador de hoje (sem `--help`): `python lote.py <plano.json> preparar|renderizar [--so 402,405]`. O `renderizar` chama o `cortar.py` com **exatamente** este argv (é o que a sua esteira tem que reproduzir; `extra` = `["--transcricao", <json>]` se houve emenda, `["--fade-saida", x]` se pedido, `["--dublar"]` se o criador é `"idioma": "en"` e o corte não traz `"dublar": false`):

```python
[PYTHON, ".../scripts/cortar.py", str(arq), "--inicio", str(ini), "--fim", str(fim), "--gancho", item["gancho"],
 "--id-streamer", item["streamer"], "--saida", str(saida), *extra]
```

O bruto do lote é `H:\HypadoLocal\brutos\<streamer>_<id do vídeo>_<início em segundos inteiros>.mp4` (ex.: `tgg_c0Com9SMv1s_883.mp4`) e a transcrição `H:\HypadoLocal\transcricoes\<mesmo nome>.json`; `lote.py renderizar` também grava `<plano>_resultado.json` ao lado do plano. Constantes: `FOLGA = 4.0` s baixados antes e depois do trecho pedido; `encostar_em_frases(segmentos, alvo_ini, alvo_fim, video_cfg)` acha o começo de frase mais perto do início e o fim de frase mais perto do fim (`ini - 0.15`, `fim + 0.4`; respeita `duracao_min_seg`=15 e `duracao_max_seg`=59); o arquivo vai para a fila do Drive em `01 Fila para postar\AAAA\MM Mês\dd.mm.aaaa HHhMM <gancho>.mp4` (sem data: `Reserva\<gancho>.mp4`). Docstring real do plano:

```
Cada item do plano:
  {"n": 1, "video": "<id do YouTube>", "streamer": "davyjones", "inicio": "03:26", "fim": "04:04",
   "gancho": "...", "titulo": "...", "legenda": "..."}
  Opcional: "corte": [ini, fim] em segundos dentro do trecho baixado, para acertar na mao.
  Opcional: "trechos": [[ini, fim], ...] (emendas: tirar pausa/tropeco) e "zoom": [...] - ver emenda.py.
  Opcional: "fade_saida": 0.1 (fade do audio no fim, quando a fala emenda na palavra seguinte).
  Criador com "idioma": "en" no config sai dublado em PT (dublar.py); "dublar": false desliga.
```

**`emenda.py`** — pré-edição do bruto (módulo; `emenda.preparar_fonte(cfg, item, arq, dados)`). Campos opcionais de cada corte, em segundos do bruto: `trechos` (partes que ficam), `zoom` (`{de, ate, centro:[x,y], escala}`), `cobrir` (`{imagem, de, ate, centro, zoom:[1.0,1.12]}` troca o vídeo por arte parada; o áudio fica), `bipes`, `tarjas` (`{de, ate, x, y, w, h, modo: desfoque|cor, cor}`), `selos` (`{imagem, x, y, de, ate}`). Gera `<bruto>_ed<n>.mkv` + `<bruto>_ed<n>.json` (transcrição remapeada).

**`dublar.py`** — dubla um corte **já renderizado** (voz Piper pt-BR `pt_BR-faber-medium`, local; nunca clona voz; original abaixado a ~15%, nas pausas 30%; `acelerar_max` 1.25). **Não aceita `--srt` nem `--texto-arquivo`**:

```
usage: dublar.py [-h] --transcricao TRANSCRICAO --inicio INICIO --fim FIM [--saida SAIDA] corte
  corte           corte ja renderizado (legenda PT queimada)
  --transcricao   JSON no formato de 4.5, com os segmentos JÁ traduzidos para PT
  --inicio/--fim  onde o corte começa/termina dentro do trecho da transcrição
```

Normalmente roda por dentro do `cortar.py --dublar`. Crédito no vídeo e no post: `dublado por HP`.

**`versao_upload.py`** — cópia ≤ 9,5 MB para subir pelo Chrome (a extensão aceita 10 MB). Sem argparse: `python versao_upload.py <corte.mp4>`. Já cabe: só copia (`shutil.copy2`); passa: 2 passadas de ffmpeg (bitrate calculado; abaixo de 1,6 Mbps de vídeo cai para 720x1280). Saída: `<pastas.midia>\upload\<slug ASCII do nome>.mp4` (no PC: `H:\HypadoLocal\upload\`), onde `slug = ascii(nome).lower()` com tudo que não é `[a-z0-9]` virando `_`. Imprime `"<caminho>  (<MB> MB, ...)"`.

**`estaticos.py`** — arte do GTA 6 | HP (usa a paleta GTA6, 4.6). **Sem `--pedido`**:

```
usage: estaticos.py {carrossel,story,destaques} ...
  estaticos.py carrossel <spec.json> <pasta_saida> [--tiktok]
      spec: {"capa": {"titulo", "subtitulo", "imagem", "imagem_vertical"?, "selo"},
             "laminas": [{"titulo", "texto", "imagem"?}], "fonte": "...", "final": "..."}
      saída: 01.jpg, 02.jpg... em 1080x1350 (capa + laminas + lâmina final com "SEGUE @hpgta6"); --tiktok = tiktok_01.jpg... em 1080x1920
  estaticos.py story <tipo> <saida.jpg> [--titulo --texto --imagem --video --fonte --data --hoje --selo]
      tipos: novo_video (--titulo + --video|--imagem) | contagem (--data 2026-11-19 --hoje AAAA-MM-DD) |
             noticia (--titulo --texto [--imagem --fonte --selo]) | interativo (--titulo = a pergunta; fundo com o retângulo livre y 930–1480 para a figurinha)
  estaticos.py destaques <pasta_saida>      -> destaque_noticias|trailers|data_e_preco|enquetes|curiosidades .jpg (1080x1920)
```

**`posts_canais.py`, `posts_futebol.py`, `posts_filmes.py`, `posts_receitas.py`, `posts_carros.py`, `posts_destinos.py`** — as artes dos 5 canais. Todos têm `render <post.json>` (gera `<nome>_feed.jpg` 1080x1350 e `<nome>_story.jpg` 1080x1920; carrossel `<nome>_01.jpg…`) e `exemplos [pasta]`. `posts_canais.py` (o molde genérico, usa Bahnschrift) tem também `destaques <canal> <pasta>`, `placar <post.json>` e `gol <gol.json>`. O JSON do `posts_canais.py render`:

```json
{
  "canal": "receitas", "id": "2026-10-01_1000_frango-assado", "saida": "<pasta>",
  "slides": [
    {"tipo": "capa",  "foto": "<jpg>", "etiqueta": "ALMOÇO · 40 MIN", "titulo": "Frango assado suculento", "sub": "que impressiona sem esforço", "foco": [0.5, 0.5]},
    {"tipo": "lista", "titulo": "Ingredientes", "itens": ["1 frango inteiro", "..."], "foto": "<jpg opcional>"},
    {"tipo": "passo", "n": 1, "de": 4, "titulo": "Tempere", "texto": "...", "foto": "<jpg opcional>"},
    {"tipo": "foto",  "foto": "<jpg>", "titulo": "Praia do Sancho", "texto": "...", "foco": [0.5, 0.6]},
    {"tipo": "dica",  "titulo": "O segredo", "texto": "..."},
    {"tipo": "cta",   "texto": "Salva pra fazer no fim de semana"}
  ],
  "story": {"foto": "<jpg>", "titulo": "Receita nova no feed", "chamada": "Toque para ver"},
  "reel": true,
  "creditos": "Fotos: Unsplash"
}
```

Os `posts_<canal>.py` usam `tipo` por modelo (`noticia`, `urgente`, `frase`, `resultado`, `gol`, `legenda_video`, `prejogo`, `tabela`, `mercado`, `comparativo`, `ranking`, `carrossel`… no Futebol; `chamada`, `manchete`, `detalhe`, `dupla`, `ficha`, `comparativo`, `ranking` no Carros; etc.). Campos comuns: `"foto"`, `"foco": [x, y]`, `"credito_foto"`, `"titulo"`, `"nome"`, `"saida"`; `*palavra*` = destaque colorido. Regras de arte: foto com cor natural (nunca tingida); crédito sempre; sem emoji dentro da arte; selo "HP" + @ do canal num canto; fotos só de banco livre (Unsplash, Pexels, Openverse comercial, Wikimedia com autor e licença) ou imprensa oficial com crédito.

**`corte_filmes.py`** (novo, 30/09) — reel do Filmes e Séries a partir de vídeo OFICIAL: `montar|validar|quadros`. Roteiro JSON com `video, fonte_tipo:"oficial", credito, link_origem, trechos[[ini,fim]] (total 12–60 s), rotulo, gancho, comentario, pergunta, dur_pergunta, recorte, zoom, legenda: "nao"|"auto"|[...], transcricao`. Garante: só fonte oficial com crédito, gancho e pergunta presentes, 12–60 s, vídeo com áudio, **nada escrito nos 250 px do topo nem nos 350 px da base** (safe zones do Reels). Códigos de saída: 0 ok · 1 roteiro recusado · 2 erro de render · 3 esperar (trava/horário).

**`fila_canais.py`** — monta a fila da API com os posts dos canais aprovados pelo revisor:

```
usage: fila_canais.py [-h] [--de DE] [--ate ATE] [--canais CANAIS] [--simular]
```

Por post (`H:\HypadoLocal\canais\<canal>\<lote>\<AAAA-MM-DD_HHMM_slug>\`): carrossel `01..NN.jpg` (máx. 10; 1 lâmina só → feed) no horário do post; story `story.jpg` 10 min depois; reel só se existir `reel_proprio.mp4`; Threads carrossel das lâminas (texto = 1º parágrafo da legenda + "Siga"); mais os textos `threads_*.json` do lote.

**`largada_canais.py`** — deixa no máximo N posts de FEED do Instagram por canal por dia (`--max`, padrão 2) e move o resto para `fila_api\reserva_largada\`: `usage: largada_canais.py [-h] [--de DE] [--ate ATE] [--max MAX] [--simular]` (`--devolver AAAA-MM-DD` devolve da reserva).

**`story_clicavel.py`** — o story de "post novo" é o compartilhamento do post pelo app do Instagram (post embutido, clicável), não imagem solta:

```
story_clicavel.py parquear [--simular]   tira da fila da API os stories que divulgam um post e guarda em fila_api\story_clicavel\
story_clicavel.py fila [--desde AAAA-MM-DD]   para cada post do IG que foi ao ar (feitos: carrossel, feed, reel) sem story
                                              clicável, grava um pedido em H:\HypadoLocal\emulador\fila_story\<id>.json
story_clicavel.py feito <id do post> [--link <url do story>]   o story_post.py chama ao terminar
```

**`painel_local.py`** — fila local do Painel HP (as rotinas não usam o `ArtifactData`):

```
python painel_local.py gravar --colecao agenda|canais|eventos|sistema --doc <doc> [--op update|set] --json "<caminho.json ou JSON inline>" [--quem <rotina>]
python painel_local.py listar            -> o que está esperando
python painel_local.py aplicado <nome>   -> move para aplicados/
```

Grava `H:\HypadoLocal\painel_local\fila\<AAAAMMDD_HHMMSS>_<colecao>_<doc>.json` = `{"colecao","doc","op","quem","quando","data":{...}}`.

**`tickets.py`** — tickets da empresa (um ticket = um `.md` em `08 Empresa\tickets\<area>\<status>\P<prioridade>_<id>.md`):

```
tickets.py criar --area gta --titulo "..." --pedido "..." [--prioridade 0|1|2] [--de antonio] [--canal gta] [--prazo "2026-09-29 18:00"] [--pronto "critério de pronto"]
tickets.py listar [--area gta] [--status novo,fazendo,travado] [--json]
tickets.py pegar <id> --por <quem>   |   nota <id> "texto"   |   feito <id> --resultado "..."
tickets.py travar <id> --motivo "..." [--espera antonio|<área>]   |   voltar <id>   |   resumo [--json]   |   painel [--atual producao.json]
```

**`radar_hp.py`** — ver 4.10. **`metricas_api.py`** — `python metricas_api.py [--mostrar]` grava `H:\HypadoLocal\canais\painel_publico\metricas_api.json` (por conta e rede: seguidores, curtidas, comentários, views).

### 4.5 Os formatos de dados reais

**`config.json`** (`06 Projeto\config.json`; o `{HYPADO}` em `pastas` vira a pasta Hypado do Drive). **fixture: `config_trecho.json`** (vocabulário e correções encurtados; 33 criadores no real):

```json
{
 "marca": {"nome": "GTA 6 | HP", "handle": "@hpgta6", "slogan": "Tudo sobre GTA 6, todo dia", "cor_principal": "#FF48A0",
           "cor_clara": "#FFB054", "cor_escura": "#101234", "cor_texto": "#FFE9F3", "fonte_cartao": "C:/Windows/Fonts/BAUHS93.TTF"},
 "pastas": {"midia": "H:/HypadoLocal", "brutos": "H:/HypadoLocal/brutos", "cortes": "{HYPADO}/01 Fila para postar",
            "postados": "{HYPADO}/02 Postados", "transcricoes": "H:/HypadoLocal/transcricoes", "temp": "H:/HypadoLocal/temp"},
 "video": {"largura": 1080, "altura": 1920, "fps": 30, "duracao_min_seg": 15, "duracao_max_seg": 59,
           "desfoque_fundo": 34, "escurecer_fundo": -0.26, "saturacao_fundo": 0.7},
 "legenda": {"fonte": "Segoe UI Black", "tamanho": 76, "cor_base": "#FFFFFF", "cor_destaque": "#FFB054", "contorno": 4,
             "sombra": 0, "margem_inferior": 560, "distancia_do_video": 36, "max_palavras_por_linha": 4},
 "dublagem": {"voz": "pt_BR-faber-medium", "modelos": "H:/HypadoLocal/modelos/piper", "pylib": "H:/HypadoLocal/pylib",
              "volume_original": 0.15, "volume_original_pausa": 0.3, "ritmo_voz": 0.95, "acelerar_max": 1.25,
              "credito": "dublado por HP", "pronuncia": {"Trevor": "Trévor", "Martin": "Mártin"}},
 "transcricao": {"modelo": "small", "dispositivo": "cpu", "precisao": "int8", "idioma": "pt",
                 "vocabulario_base": ["hypado", "GTA 6", "Rockstar", "Leonida"],
                 "correcoes": {"Selnick": "Zelnick", "Game Former": "Game Informer", "hipado": "hypado"}},
 "estilo": {"raio_video": 32, "deslocamento_video": -10, "gancho_tamanho": 58, "gancho_cor_texto": "#FFFFFF",
            "gancho_cor_fundo": "#101234", "gancho_opacidade": 205, "gancho_y": 236, "credito_tamanho": 34,
            "credito_margem_inferior": 400, "credito_acima_do_video": 18, "marca_tamanho": 34, "marca_opacidade": 195,
            "marca_y": 96, "cta_segundos": 3.0, "cta_chamada": "GOSTOU? SEGUE A GENTE"},
 "agendamento": {"timezone": "America/Sao_Paulo", "horarios": ["11:30", "17:30", "21:00"], "fila_minima_dias": 3,
                 "redes": ["instagram", "tiktok", "youtube", "facebook", "threads"], "rascunho_ate_aprovacao": true},
 "streamers": [
  {"id": "davyjones", "nome": "Davy Jones", "credito": "@DavyJonesGTA6", "canal": "https://www.youtube.com/@DavyJonesGTA6",
   "youtube": "https://www.youtube.com/@Gameplayrj", "autorizado": true, "data_autorizacao": "", "observacao": "texto livre",
   "vocabulario": ["Davy Jones", "Gameplayrj"]},
  {"id": "tmartn2", "nome": "TmarTn2", "credito": "@TmarTn2", "idioma": "en", "autorizado": true, "vocabulario": ["TmarTn2"]}
 ]
}
```

Os 33 `id` reais de criadores (todos `autorizado: true`; os marcados `en` são gringos e saem dublados): davyjones, brksedu, alanzoka, casimiro, funkyblackcat, paulinholoko, loudcoringa, piuzinho, central, saninplay, digplay, carocanal, estsee, bladerkorotte + **en**: darkviperau, gtaseriesvideos, mrbossftw, typicalgamer, tgg, lessonsininternetculture, inktv, hazard, wesnemo, tyronemagnus, joblessgarrett, bombastic, jericho, moreimmortal, ivansbetter, drawnout, theprofessional, projectvice, tmartn2.

**`transcricao.json`** (também o formato do `legenda.json`/`traducao.json` da esteira). **fixture: `transcricao_exemplo.json`**:

```json
{
 "duracao_seg": 60.0,
 "segmentos": [
  {"inicio": 4.74, "fim": 7.2, "texto": "Aproveitando Red Dead Redemption,",
   "palavras": [{"inicio": 4.74, "fim": 5.68, "texto": "Aproveitando"}, {"inicio": 5.68, "fim": 5.97, "texto": "Red"},
                {"inicio": 5.97, "fim": 6.33, "texto": "Dead"}, {"inicio": 6.33, "fim": 7.2, "texto": "Redemption,"}]},
  {"inicio": 7.38, "fim": 13.86, "texto": "animais com iridescência, bioluminescência, translucidez,",
   "palavras": [{"inicio": 7.38, "fim": 7.98, "texto": "animais"}, {"inicio": 7.98, "fim": 8.28, "texto": "com"}]}
 ],
 "revisao": "Legendador 30/09: traduzido para PT-BR só dentro dos trechos do plano. Inglês original: tgg_c0Com9SMv1s_883_en_backup.json."
}
```

Regra de formato: todo segmento tem `inicio`, `fim`, `texto` e `palavras` (lista, cada uma com `inicio`, `fim`, `texto`); tempos em segundos do **bruto**; `revisao` é opcional.

**Plano do lote** (`lotes\AAAA-MM-DD_diario.json`, chave `cortes[]`; o `lote.py` só lê `cortes`). **fixture: `plano_corte_exemplo.json`** (1 de 4 cortes reais; textos livres encurtados):

```json
{
 "n": 801, "video": "c0Com9SMv1s", "streamer": "tgg", "inicio": "07:02", "fim": "07:48",
 "gancho": "GTA 6 tem corrida de DEMOLIÇÃO",
 "titulo": "GTA 6 vai ter corrida de demolição, festa na lama e dunas de motocross #gta6 #shorts",
 "legenda": "O norte do mapa do GTA 6 é um parque de diversões 🏁 Segundo a Rockstar na Game Informer: [...] O que você faz primeiro? 🎥 Crédito: @TGG_ (dublado por HP) #gta6 #gtavi #rockstargames #vicecity #games",
 "redes": ["youtube", "facebook"],
 "data": "2026-10-02T09:00",
 "toque_hp": {"pergunta_abertura": "O que dá pra fazer no norte do mapa do GTA 6?", "narracao": "Quem descreve é Paul MacPherson, [...]",
              "fecho": "E você, vai de corrida de demolição ou de pescaria?", "inserir_em": 20.57},
 "video_url": "https://www.youtube.com/watch?v=c0Com9SMv1s",
 "corte": [6.08, 46.04],
 "cobrir": [{"imagem": "H:\\HypadoLocal\\radar\\artes_oficiais\\trailer1_festa_na_lama.jpg", "de": 0.0, "ate": 27.5, "centro": [0.5, 0.55], "zoom": [1.0, 1.12]}],
 "obs": "texto livre da pauta", "obs_editor": "texto livre", "legenda_status": "texto livre",
 "arquivo": "2026\\10 Outubro\\02.10.2026 09h00 GTA 6 tem corrida de DEMOLIÇÃO.mp4",
 "upload": "H:\\HypadoLocal\\upload\\02_10_2026_09h00_gta_6_tem_corrida_de_demolicao.mp4", "upload_mb": 8.9,
 "duracao_seg": 49.8, "render_status": "ok: 49,8 s (trecho 40,0 + cartela 9,8)...",
 "agendado": true, "agendado_em": {"youtube": "agendado 2026-10-02 09:00 (https://youtube.com/shorts/<id>)"}, "status": "agendado"
}
```

O `_resultado.json` do mesmo lote (gravado pelo `lote.py renderizar`) é uma **lista** com o mesmo item mais `duracao_seg`, `primeira_fala`, `ultima_fala` e `toque_hp_aplicado: {duracao_final_seg, narracao_seg, cartela_em}`.

**Lote de estáticos do GTA** (`lotes\AAAA-MM-DD_estaticos.json`) — **é aqui que a sua suposição 6 estava errada**: o story da enquete NÃO é um item `tipo: "story_enquete"`; é a chave **`interativo`**, e a pergunta tem **46 caracteres** (o limite da figurinha de enquete é ~25). **fixture: `lote_estaticos_2026-10-01.json`** (textos encurtados):

```json
{
 "data": "2026-10-01",
 "criado": "2026-09-30 madrugada (hypado-estaticos, 03h36)",
 "revisor": "aprovado 30/09",
 "pauta": "lotes\\2026-10-01_estaticos_pauta.json",
 "carrossel": {
  "tema": "Linha do tempo do GTA 6 — A linha do tempo do GTA 6",
  "arquivos": "H:\\HypadoLocal\\upload\\carrossel_2026-10-01\\01-09.jpg",
  "spec": "H:\\HypadoLocal\\upload\\carrossel_spec_2026-10-01.json",
  "legenda": "1.749 dias. É o tempo entre o anúncio e o lançamento do GTA 6. ⏳\n\n[...]\n\n🔔 Segue o @hpgta6 pra não perder nada do GTA 6\n💾 Salva pra consultar depois e 📤 compartilha com quem está esperando desde 2022\n\n#gta6 #gtavi #rockstargames",
  "horario": "15:00",
  "instagram": "na fila da API para 01/10 15:00 — id gta_2026-10-01_ig_carrossel",
  "facebook": "programado 01/10 15:00 (Planner do Business Suite conferido, so Pagina, 9 imagens)",
  "tiktok": "pausado (modo recuperação até 02/10)"
 },
 "stories": [
  {"hora": "09:00", "arquivo": "H:\\HypadoLocal\\upload\\stories_2026-10-01\\0900_contagem.jpg", "tema": "contagem 49 dias",
   "instagram": "na fila da API (publicador_meta) para 01/10 09:00 — id gta_2026-10-01_ig_story_0900",
   "facebook": "programado 01/10 09:00 (Planner do Business Suite conferido, so Pagina)"},
  {"hora": "12:10", "arquivo": "H:\\HypadoLocal\\upload\\stories_2026-10-01\\1210_novo_video.jpg", "tema": "vídeo novo: Dá pra ficar GORDO no GTA 6",
   "instagram": "na fila da API (publicador_meta) para 01/10 12:10 — id gta_2026-10-01_ig_story_1210", "facebook": "programado 01/10 12:10"}
 ],
 "interativo": {
  "arquivo": "H:\\HypadoLocal\\upload\\story_interativo_2026-10-01.jpg",
  "rede": "Instagram @hpgta6 (compartilhar no Facebook)",
  "horario": "16:00",
  "figurinha": "enquete",
  "pergunta": "Furacão chegando em Leonida. O que você faz?",
  "opcoes": ["Vou ver de perto", "Fujo pro outro lado"],
  "destaque": "Enquetes",
  "quem_manda": "hypado-resumo-7h (item 4) em 01/10"
 },
 "threads": [
  {"hora": "09:00", "texto": "Faltam 49 dias pro GTA 6. 🗓️\n\n[...]\n\nJá decidiu se vai jogar no lançamento ou vai esperar o fim de semana?",
   "status": "na fila da API para 01/10 09:00 — id gta_2026-10-01_th_texto_0900"}
 ],
 "comunidade_youtube": {"horario": "10:00", "tipo": "curiosidade com imagem (capa do carrossel)",
                        "imagem": "H:\\HypadoLocal\\upload\\carrossel_2026-10-01\\01.jpg", "texto": "A linha do tempo do GTA 6 em 4 datas: [...]",
                        "status": "programado 01/10 10:00 (aba Posts > Programado do canal conferido, imagem 01.jpg)"},
 "obs": "IG (carrossel + 9 stories) e Threads (5 textos) pela API da Meta; Facebook e Comunidade do YouTube pelo Chrome.",
 "fechado": "2026-09-30 04h10"
}
```

Note: as chaves `instagram`/`facebook` dentro de `stories[]` e `carrossel` são **texto livre de status**, não objeto. O `tema` de um story de "post novo" tem o prefixo `vídeo novo:`. O `spec` do carrossel é o JSON do `estaticos.py carrossel` (4.4).

**O pedido da esteira (o que o Claude larga em `01_pedidos`)** — formato real do `hp_studio\esteira\pedido.py` do PC (a **sua** esteira tem que aceitar este formato; o `normalizar()` do PC devolve `ErroParametro` com motivo em português para pedido mal feito). Docstring literal:

```
Corte (vídeo) — os mesmos campos de um corte do plano do lote (lote.py), para o vídeo sair igual:
  {"tipo": "corte", "canal": "gta", "prioridade": 2, "data": "2026-09-30T18:30",
   "video": "<id do YouTube>"  (ou "link": "https://...", ou "arquivo": "H:\\...\\trecho.mp4"),
   "streamer": "davyjones", "inicio": "03:26", "fim": "04:04",
   "gancho": "...", "titulo": "...", "legenda": "...", "redes": ["instagram", "tiktok", ...]}
  Opcionais iguais aos do plano: corte [ini, fim], trechos, zoom, cobrir, bipes, tarjas, fade_saida, dublar.
  Outros opcionais: idioma ("en" = gringo: espera traducao.json), hashtags, textos {rede: texto}, correcoes
  {"errado": "certo"}, apelido (nome curto da pasta).
Estáticos pulam as etapas de vídeo: "tipo": "carrossel" (spec, tiktok), "story" (arte, opcoes), "texto" (texto).
Prioridade: 0 = urgente/ao vivo (faixa expressa), 1 = do dia, 2 = programado (padrão).
```

Constantes reais: `TIPOS = ("corte","carrossel","story","texto")`; `REDES = ("instagram","facebook","threads","youtube","tiktok")`; `REDES_PADRAO = {"corte": todas, "carrossel": ["instagram","facebook"], "story": ["instagram","facebook"], "texto": ["threads"]}`; `ARTES_STORY = ("novo_video","contagem","noticia","interativo")`; campos copiados do plano: `corte, trechos, zoom, cobrir, bipes, tarjas, fade_saida, dublar, n`; recusa `flow games|flowgames|flow podcast|flowpodcast|flow_games` em `streamer, credito, link, gancho, titulo`; `data` = `AAAA-MM-DDTHH:MM`; pedido solto só é lido depois de **2 s parado** (nada meio gravado).

**`post.json`** — o contrato entre a esteira (quem grava) e o `publicar` do PC (quem lê). Docstring literal do `hp_studio\publicar\post.py`:

```
{
  "canal": "gta",                     gta | futebol | filmes | receitas | carros | destinos
  "tipo": "reel",                     reel | carrossel | feed | story | texto | video | comunidade
  "quando": "2026-09-30 18:30",       hora de Brasília (a do PC); "agora" = publica já (também aceita "data" + "hora")
  "titulo": "…",                      YouTube (até 100) e Pinterest; se faltar, 1ª linha da legenda
  "legenda": "…",                     texto do post (crédito + hashtags)
  "arquivos": ["final.mp4"],          relativos à pasta do item (ou caminho completo)
  "capa": "capa.jpg",                 opcional: capa do reel no Instagram, miniatura no YouTube
  "tags": ["gta6", "gtavi"],          YouTube
  "dublado": false,                   true = YouTube marca "conteúdo alterado/sintético" (voz sintética)
  "redes": ["instagram", "facebook", "threads", "youtube", "tiktok"]
}
"redes" também pode ser um objeto: o que vier dentro vale só para aquela rede e passa por cima do geral.
    "redes": {"instagram": {}, "threads": {"legenda": "pergunta…"}, "youtube": {"titulo": "…"}, "pinterest": {"pasta": "Carros clássicos", "link": "https://…"}}
Campos só de uma rede: youtube -> categoria (20 = Games), notificar, sintetico, miniatura; pinterest -> pasta, link, alt.
```

`REDES` aceitas: `instagram, facebook, threads, youtube, tiktok, pinterest, youtube_comunidade`; apelidos (`ig`, `fb`, `th`, `yt`, `shorts`, `tt`, `pin`, `comunidade`) e `short→reel`, `foto→feed`, `longo→video`. O resultado por rede é gravado no item em `publicar.json` (simulação: `publicar_simulado.json`): `{"item", "simulado", "redes": {<rede>: {"status", "link", "id", "erro", ...}}}`; cada rede devolve o contrato `{status, link, id, erro}` (+ campos extras da rede); os 3 status que contam como **feito** são `agendado`, `publicado` e `pendente_chrome` (TikTok: espera o Claude agendar pelo Chrome); falha e vídeo travado em privado gravam `erro`; rede que já está `agendado|publicado|pendente_chrome` **não é mandada de novo**; upload que caiu no meio guarda `detalhe` (video_id, upload_url) e continua dali; trava `.publicando` (velha após 45 min).

**`agendados.json`** — um por canal (`07 Canais\<Pasta>\agendados.json`) e um do GTA (`06 Projeto\agendados.json`); o `publicador_meta.registrar_no_ar` grava e o plantão do WhatsApp lê para o aviso "no ar". Os dois têm o mesmo formato `{"itens": [...]}`. **fixture: `agendados_exemplo.json`**:

```json
{"itens": [
 {"id": "futebol_2026-09-30_2320_jj-quem-decide_ig_feed", "titulo": "Jorge Jesus: \"Quem decide sou eu\" (treta com CR7)",
  "data_post": "2026-09-30T23:18", "redes": ["instagram"], "links": {"instagram": "https://www.instagram.com/p/Dd70ZtCFSND/"},
  "status": "no_ar", "origem": "api", "grupo_whatsapp": "HP | Futebol ⚽", "tipo": "feed", "arquivo": "frase_feed.jpg"},
 {"id": "gta_2026-09-29_ig_story_1700", "titulo": "gta_2026-09-29_ig_story_1700", "data_post": "2026-09-29T16:58",
  "redes": ["instagram"], "links": {"instagram": "https://www.instagram.com/stories/hpgta6/3990000000000000002"},
  "status": "no_ar", "origem": "api", "grupo_whatsapp": "HP | Comissão 🚀", "tipo": "story", "arquivo": "1700_contagem.jpg"}
]}
```

`avisos_enviados.json` (`06 Projeto\`): **lista** de nomes de arquivo já avisados; o PowerShell às vezes embrulha a lista como `[{"value": [...], "Count": N}]` — o `plantao.py` tolera os dois, o seu leitor também tem que tolerar.

**Foto diária de métricas** (`06 Projeto\metricas\AAAA-MM-DD.json`, feita pelo resumo das 7h; o módulo de métricas do PC grava `AAAA-MM-DD_api.json` ao lado): `{"coletado_em": "AAAA-MM-DDTHH:MM", "obs": "...", "seguidores": {"tiktok": 7, "youtube": 3, "instagram": 11, "facebook": 3, "threads": 1}, "ontem": {"views": 829, "tiktok": 0, "youtube": 139, "instagram": 74, "facebook": 592, "threads": 24, "curtidas": 7, "comentarios": 0, "seguidores": 1}, "posts": {"youtube": [{"titulo", "data": "29/09 21h00", "views"}], "instagram": [{"titulo", "data", "views", "alcance", "curtidas"}], "tiktok": [...], "facebook": [...], "threads": [...]}}`.

### 4.6 Marca: paleta, fontes e tamanhos (a verdade está no código dos `posts_*.py`, `estaticos.py`, `arte_perfil.py`, `arte_canais.py`)

| Canal | @ | Cor do canal (perfil/capa) | Cor nos posts e stories | Fundo | Extras do código | Fontes |
|---|---|---|---|---|---|---|
| **GTA 6 \| HP** | @hpgta6 | rosa `(255,60,170)` `#FF3CAA` (arte de perfil "vice") | rosa `(255,72,160)` `#FF48A0`, laranja `(255,176,84)` `#FFB054`, ciano `(70,225,235)` `#46E1EB` | noite `(16,18,52)` `#101234`; céu em degradê `(52,40,110)→(28,24,72)→noite` com brilho rosa no topo | título com **degradê vertical rosa→laranja** + contorno noite; texto `#FFE9F3`; `(245,242,255)` no corpo | **Bauhaus 93** `C:/Windows/Fonts/BAUHS93.TTF` (títulos), Segoe UI Black `seguibl.ttf` (tema, pílulas), Segoe UI Bold `segoeuib.ttf` (texto), Segoe UI Black Itálico `seguibli.ttf` (o "HP") |
| **Futebol \| HP** | @hp.futebol | verde `(30,215,96)` `#1ED760` | verde HP `#1ED760` (destaque e detalhes); verde escuro `(18,168,80)` `#12A850` (moldura do urgente, aspas, faixas). **Cor por clube:** o post segue o clube do post (nunca a cor de um rival); clube preto e branco = prata; jogo entre dois clubes = neutra; sem clube = verde HP | `(10,16,12)`; preto `(8,9,11)`; estúdio `(24,27,33)→(6,7,9)` | foto com **cor natural** (nunca tingida); caixa escura translúcida com contorno fino | **Anton** (manchete), Barlow Medium/SemiBold/ExtraBold, Barlow Condensed Bold/ExtraBold |
| **Filmes e Séries \| HP** | @hp.filmes | amarelo `(245,179,1)` `#F5B301` | o mesmo; painel claro `(239,239,239)` `#EFEFEF` nas lâminas de texto; variação `"cor": "escuro"` (caixa preta, texto branco) | `(14,12,10)` | caixa amarela com contorno preto; foto de cima ~58–60% | Barlow ExtraBold/Medium, Anton nos pôsteres |
| **Receitas \| HP** | @hp.receitas | laranja `(255,122,26)` `#FF7A1A` | laranja nas etiquetas/botões; faixa amarela `(255,226,18)` `#FFE212`; creme `(255,246,214)` `#FFF6D6`; roxo `(124,58,237)`; azul `(37,72,255)` | `(18,12,9)` | close de prato com cor natural | Barlow ExtraBold, **DM Serif Display** (Regular e Italic) nas capas |
| **Carros \| HP** | @hp.carros | vermelho `(255,45,45)` `#FF2D2D` (perfil/capa) | vermelho `(230,30,45)` `#E61E2D` (o da referência) e amarelo `(255,214,0)` `#FFD600` nas palavras-chave | `(14,14,16)` | trapézio/etiqueta vermelha com "HP"; traço vermelho na frase da capa | Anton, Barlow Condensed ExtraBold, Barlow |
| **Destinos \| HP** | @hp.destinos | ciano `(0,194,209)` `#00C2D1` | ciano `#00C2D1`, ciano claro `(120,225,255)` `#78E1FF`, marinho `(10,38,110)` `#0A266E`, azul `(21,84,200)` `#1554C8`, claro `(236,243,251)` `#ECF3FB` | `(8,16,20)`; fundo azul-royal→marinho com curvas | pílula ciano "IDA E VOLTA"; amarelo só no selo "BAIXOU!" | Barlow ExtraBold/SemiBold, Barlow Condensed ExtraBold |

- **Selo "HP" dos 5 canais** (`arte_canais.selo_hp`): pílula branca `(255,255,255)` com "HP" em `(15,15,18)`, Bahnschrift Bold; ao lado, o `@` do canal em Bahnschrift SemiBold. O **GTA** tem o seu (`arte_perfil.selo_hp`, "HP" em Segoe UI Black Itálico, discreto, mais o `@hpgta6`). Bahnschrift é variável: `ImageFont.truetype("C:/Windows/Fonts/bahnschrift.ttf", tam)` + `.set_variation_by_name("Bold Condensed"|"Bold"|"SemiBold"|"Regular")`.
- **Onde estão as fontes no PC:** `06 Projeto\marca\fontes\` (Anton-Regular, Barlow-{Regular,Medium,SemiBold,Bold,ExtraBold}, BarlowCondensed-{SemiBold,Bold,ExtraBold}, DMSerifDisplay-{Regular,Italic}; todas OFL) e `C:\Windows\Fonts\` (`bahnschrift.ttf`, `seguibl.ttf`, `seguibli.ttf`, `segoeuib.ttf`, `BAUHS93.TTF`, `seguiemj.ttf` para emoji em lugares específicos). **Na nuvem essas fontes não existem**: faça um resolvedor `fonte(nome, tamanho)` que procura nessa ordem (1) `HP_FONTES` ou `06 Projeto\marca\fontes\`, (2) `C:\Windows\Fonts\`, (3) as OFL baixadas do Google Fonts (Anton, Barlow, Barlow Condensed, DM Serif Display) numa pasta de cache, (4) DejaVu como último recurso (só para teste). Os testes de render rodam com o fallback; no PC sai com as fontes reais.
- **Tamanhos:** feed e carrossel **1080x1350** (4:5); story, reel, capa de reel, destaque e carrossel do TikTok **1080x1920** (9:16); perfil 1080x1080; capa do YouTube 2560x1440 (área segura 1546x423 no centro); capa do Facebook 1640x624. **Zonas seguras do story/reel:** nada importante nos **250 px do topo** (perfil e barra de progresso) nem nos **350 px da base** (campo de resposta); o `estaticos.py interativo` deixa livre o retângulo `(110, 930)–(970, 1480)` para a figurinha.
- **Tratamento de foto** (`arte_canais.tratar`): contraste ×1.12, cor ×1.10, brilho ×0.96; vinheta de força 0.55 nos cantos.
- **Regras de arte:** foto de cor natural; crédito da foto sempre; **sem emoji na arte** (o `estaticos.sem_emoji()` tira); `*palavra*` = destaque colorido; `@` do canal e selo HP num canto.
- **Os conflitos que existem hoje no código** (por isso não escolha por conta própria; exponha os dois valores e deixe a decisão marcada no `ENTREGA.md` como "decisão do Antônio/Diretor"):
  1. **Carros:** `#FF2D2D` em `posts_canais.py`/`arte_canais.py` (perfil e capa) x `#E61E2D` em `posts_carros.py` (posts). Para arte nova de post e story do Carros use **`#E61E2D`**; perfil e capa ficam `#FF2D2D`.
  2. **GTA:** três rosas — `#FF48A0` (config.json e `estaticos.py`, usado nos carrosséis e stories), `#FF3CAA` (`arte_perfil.py`, só perfil e capa) e `#FF3D8B` (página de links, só o site). Para arte nova de **post e story** use **`#FF48A0`**.
  3. **Reel do Futebol da rodada 1** (fundo `#06170F`, destaque amarelo `#FFD23F`) x `posts_futebol.py` (verde `#1ED760`, que o Antônio pediu em 28/09 no lugar do amarelo/vermelho do SportsCenter: "quem sabe a gente tenta aderir outras cores para não parecer tanto cópia"). **Vale o verde do `posts_futebol.py`.**

### 4.7 O Instagram no celular: o que existe, o que foi visto de verdade e o que é palpite

**Ambiente real.** Emulador oficial do Android (AVD `hp_celular`: Pixel 6, **1080x2400**, 420 dpi, **Android 14 / API 34**, imagem `google_apis_playstore` x86_64) em `H:\HypadoLocal\android\`; `adb` em `H:\HypadoLocal\android\sdk\platform-tools\adb.exe`; app `com.instagram.android`; **o app no emulador está em inglês** (o dump mostra "Highlight", "Send story", "Say something…"); as contas ficam logadas no emulador (quem loga é o Antônio; o script **nunca** faz login, nunca digita senha ou código; no PC **só se tem certeza de que o @hp.futebol está logado**, o do dump abaixo; as outras contas são presumidas e o `story_post` precisa conferir a lista de contas antes de trocar). O Antônio pode usar também um **celular real por ADB**: o serial aparece em `adb devices` (o do emulador é `emulator-NNNN`); com 2 aparelhos ligados é obrigatório escolher por serial. **Tela diferente = coordenada diferente**: nunca use coordenada fixa; sempre os `bounds` do dump do uiautomator.

Scripts reais (cole-os nos testes como referência do comportamento):

```powershell
# H:\HypadoLocal\android\env.ps1
$global:HP_ANDROID = "H:\HypadoLocal\android"
$env:JAVA_HOME = (Get-Content "$HP_ANDROID\java_home.txt" -Raw).Trim()
$env:ANDROID_SDK_ROOT = "$HP_ANDROID\sdk"; $env:ANDROID_HOME = "$HP_ANDROID\sdk"
$env:ANDROID_USER_HOME = "$HP_ANDROID\.android"; $env:ANDROID_AVD_HOME = "$HP_ANDROID\avd"; $env:ANDROID_EMULATOR_HOME = "$HP_ANDROID\.android"
$global:ADB = "$HP_ANDROID\sdk\platform-tools\adb.exe"; $global:EMU = "$HP_ANDROID\sdk\emulator\emulator.exe"; $global:HP_AVD = "hp_celular"

# H:\HypadoLocal\android\ligar_emulador.ps1 [-Esperar 240]   (boot frio; nunca das 18h às 22h30; só abre para postar e fecha)
. H:\HypadoLocal\android\env.ps1
$rodando = (& $ADB devices 2>$null) -match "emulator-\d+\s+device"
if (-not $rodando) {
  Start-Process -FilePath $EMU -ArgumentList "-avd", $HP_AVD, "-no-boot-anim", "-no-metrics", "-no-snapshot-load", "-netdelay", "none", "-netspeed", "full" `
    -WindowStyle Hidden -RedirectStandardOutput "$HP_ANDROID\emulador.log" -RedirectStandardError "$HP_ANDROID\emulador_erros.log"
}
# espera `adb shell getprop sys.boot_completed` = 1 (de 5 em 5 s, até -Esperar s); imprime "PRONTO: Android iniciado (14)" ou sai com 1

# H:\HypadoLocal\android\desligar_emulador.ps1 : `adb emu kill`, espera 8 s, `adb kill-server`
# H:\HypadoLocal\android\tela.ps1 [-Esperar n] : screencap -> H:\HypadoLocal\android\telas\tela.png e diz o app na frente
#   ("na frente: " + `dumpsys activity activities | grep topResumedActivity`)
```

`H:\HypadoLocal\android\ui.py` (inteiro; lê a tela pelo `uiautomator dump` e toca por texto/descrição/id):

```python
"""Lê a tela do celular virtual (uiautomator) e lista os elementos com texto/descrição e o centro de cada um.
Uso: python ui.py [filtro]  -> linhas "centro_x,centro_y | classe | texto | desc | id | clicavel"
     python ui.py --tocar "texto ou desc"  -> toca no primeiro elemento cujo texto/desc contém isso"""
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ADB = r"H:\HypadoLocal\android\sdk\platform-tools\adb.exe"
XML = Path(r"H:\HypadoLocal\android\telas\ui.xml")


def adb(*a):
    return subprocess.run([ADB, *a], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60).stdout


def ler():
    adb("shell", "uiautomator", "dump", "/sdcard/ui.xml")
    adb("pull", "/sdcard/ui.xml", str(XML))
    raiz = ET.parse(XML).getroot()
    out = []
    for n in raiz.iter("node"):
        m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", n.get("bounds", ""))
        if not m:
            continue
        x1, y1, x2, y2 = map(int, m.groups())
        out.append({"x": (x1 + x2) // 2, "y": (y1 + y2) // 2, "classe": n.get("class", "").split(".")[-1],
                    "texto": n.get("text", ""), "desc": n.get("content-desc", ""), "id": n.get("resource-id", "").split("/")[-1],
                    "clicavel": n.get("clickable") == "true", "w": x2 - x1, "h": y2 - y1})
    return out


def main():
    a = sys.argv[1:]
    itens = ler()
    if a and a[0] == "--tocar":
        alvo = a[1].lower()
        for it in itens:
            if alvo in it["texto"].lower() or alvo in it["desc"].lower() or alvo == it["id"].lower():
                adb("shell", "input", "tap", str(it["x"]), str(it["y"]))
                print("toquei:", it["x"], it["y"], "|", it["texto"] or it["desc"] or it["id"])
                return 0
        print("nao achei:", a[1])
        return 1
    filtro = a[0].lower() if a else ""
    for it in itens:
        if not (it["texto"] or it["desc"] or it["id"]):
            continue
        linha = f'{it["x"]},{it["y"]} | {it["classe"]} | {it["texto"][:60]} | {it["desc"][:60]} | {it["id"]} | {"clic" if it["clicavel"] else ""}'
        if filtro in linha.lower():
            print(linha)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

`H:\HypadoLocal\android\digitar.py` (inteiro; **só ASCII**: espaço vira `%s`, aspas são removidas):

```python
"""Digita num campo do celular virtual: toca no campo (x,y), apaga o que tem e escreve o texto (ASCII; espaço vira %s).
Uso: python digitar.py <x> <y> "<texto>"  ou  python digitar.py --id <resource-id|texto do campo> "<texto>" """
import subprocess
import sys
import time

sys.path.insert(0, r"H:\HypadoLocal\android")
import ui  # noqa: E402

ADB = ui.ADB


def adb(*a):
    return subprocess.run([ADB, *a], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60).stdout


def digitar(x, y, texto):
    adb("shell", "input", "tap", str(x), str(y))
    time.sleep(0.8)
    adb("shell", "input", "keycombination", "113", "29")  # CTRL+A
    time.sleep(0.3)
    adb("shell", "input", "keyevent", "67")  # DEL
    time.sleep(0.3)
    seguro = texto.replace(" ", "%s").replace("'", "").replace('"', "")
    adb("shell", "input", "text", seguro)
    time.sleep(0.6)


def main():
    a = sys.argv[1:]
    if a[0] == "--id":
        alvo = a[1].lower()
        for it in ui.ler():
            if alvo == it["id"].lower() or alvo == it["texto"].lower():
                digitar(it["x"], it["y"], a[2])
                print("digitei em", it["id"] or it["texto"], "->", a[2])
                return 0
        print("campo nao achado:", a[1])
        return 1
    digitar(int(a[0]), int(a[1]), a[2])
    print("digitei em", a[0], a[1], "->", a[2])
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Limitação real que você tem que resolver (tarefa E):** o `adb shell input text` **não digita acento nem emoji**. Pergunta de enquete, rótulo de link e legenda de story com acento ("Você", "Não") não saem. Não sugira instalar o ADBKeyBoard (instalar APK é decisão do Antônio): entregue (1) um modo padrão que **troca acento por letra sem acento e avisa no log** (`Voce`, `Nao`), e (2) um segundo modo, **desligado por padrão**, que descreve o que o Antônio teria de instalar/aceitar para digitar acento de verdade, com o passo a passo para leigo no `ENTREGA.md`.

**Os resource-ids que o PC já viu de verdade** (`com.instagram.android:id/…`; confirmados no emulador, do ticket): `row_feed_button_share` (botão Enviar do post aberto), `your_story_share_shortcut_button` ("Seu story" na folha de envio e no editor), `action_bar_username_container` (nome da conta no alto do perfil: tocar abre a lista de contas), `asset_button` (figurinhas), `poll_sticker_v2_question` (campo da pergunta da enquete), `done_button` (Concluir), `toolbar_highlights_button` (Destaque, no visualizador do próprio story), `reel_viewer_timestamp` (carimbo de tempo do story).

**Dump real de 30/09 23:41** — o **único** dump do Instagram que existe no PC: a tela do **visualizador do próprio story** do @hp.futebol (1080x2400; só esta tela; as outras telas — perfil, galeria, editor, figurinhas — **não existem em dump**). **fixture: `ui_story_visualizador_hp_futebol.txt`** (saída do `ui.py` sobre o `ui.xml` real; as linhas sem texto, descrição e id foram omitidas, como o `ui.py` faz):

```
540,1168 | LinearLayout |  |  | action_bar_root | 
540,1168 | FrameLayout |  |  | content | 
540,1168 | ViewGroup |  |  | layout_container_parent | 
540,1232 | FrameLayout |  |  | layout_container_main | 
540,1232 | FrameLayout |  |  | reel_viewer_root | 
540,1232 | FrameLayout |  |  | view_pager | 
540,1232 | LinearLayout |  |  | reel_viewer_content_layout | 
540,1262 | FrameLayout |  |  | reel_view_group | 
540,1232 | ViewGroup |  |  | reel_item_toolbar_container | 
540,2082 | FrameLayout |  |  | story_caption_legibility_background | 
540,2193 | LinearLayout |  |  | reel_item_toolbar_footer_container | 
540,2193 | LinearLayout |  |  | viewer_reel_item_toolbar_container | 
1006,2193 | LinearLayout |  |  | toolbar_buttons_container | 
1006,2192 | ViewGroup |  |  | toolbar_like_container | 
540,2190 | LinearLayout |  |  | self_reel_item_toolbar_container | 
100,2190 | LinearLayout |  |  | viewers_facepile_button | clic
100,2172 | ImageView |  |  | viewers_facepile | 
100,2253 | TextView | Activity |  | viewers_facepile_label | 
688,2190 | LinearLayout |  |  | self_toolbar_button_container | 
382,2190 | LinearLayout |  | Create a promote for current media | toolbar_promote_button | clic
381,2253 | TextView | Boost |  | promote_label | 
530,2190 | LinearLayout |  | Highlight | toolbar_highlights_button | clic
530,2172 | ImageView |  |  | highlights_status | 
529,2253 | TextView | Highlight |  | highlights_label | 
678,2190 | LinearLayout |  | Send story | self_toolbar_reshare_button_container | clic
677,2253 | TextView | Send |  | self_toolbar_reshare_button_label | 
826,2190 | LinearLayout |  |  | self_toolbar_mention_button_container | clic
826,2253 | TextView | Mention |  | self_toolbar_mention_button_label | 
984,2190 | LinearLayout |  | More options | self_toolbar_menu_button | clic
974,2172 | ImageView |  |  | self_toolbar_menu_button_icon | 
974,2253 | TextView | More |  | self_toolbar_menu_button_label | 
540,1148 | FrameLayout |  |  | reel_viewer_media_layout | 
540,1148 | FrameLayout |  |  | reel_sticker_overlay_container | 
540,1148 | FrameLayout |  |  | reel_sticker_accessibility_container | 
540,1148 | FrameLayout |  |  | reel_viewer_media_container | 
540,1148 | FrameLayout |  |  | reel_viewer_image_view | 
540,319 | View |  |  | reel_viewer_top_shadow | 
540,280 | LinearLayout |  |  | reel_viewer_header_container | 
540,211 | View |  |  | reel_viewer_progress_bar | 
540,293 | ViewGroup |  |  | reel_viewer_header | 
74,305 | FrameLayout |  |  | profile_picture_container | clic
74,279 | FrameLayout |  |  | reel_viewer_profile_picture | clic
74,279 | FrameLayout |  | Profile picture |  | 
74,279 | ImageView |  |  | reel_viewer_front_avatar | 
598,305 | Button |  | hp.futebol's story, 3 minutes ago | reel_viewer_text_container | clic
265,279 | LinearLayout |  |  | reel_viewer_title_row | 
230,279 | TextView | hp.futebol |  | reel_viewer_title | 
379,279 | TextView | 3m |  | reel_viewer_timestamp | 
540,1976 | View |  |  | reel_viewer_bottom_shadow | 
166,2045 | TextView | Say something… |  | add_comment_textview | 
540,64 | View |  |  | statusBarBackground | 
540,2368 | View |  |  | navigationBarBackground | 
```

O que esse dump ensina (e a rodada 1 não sabia): (a) o carimbo real do story recém-publicado é **`3m`** (abreviado, em inglês: `3m`, `1h`), e o `content-desc` do cabeçalho é `hp.futebol's story, 3 minutes ago`; a lista `TIMESTAMP_AGORA = ["agora", "agora mesmo", "now", "just now"]` da rodada 1 **não casa** com isso; (b) o botão de destaque tem `content-desc="Highlight"` e id `toolbar_highlights_button`; (c) o botão "Send story" é `self_toolbar_reshare_button_container`; (d) o nome da conta de quem é o story aparece em `reel_viewer_title` (`hp.futebol`) e é a forma de **conferir de quem é o story**.

**Seletores da rodada 1 (`story_post_seletores.py`)**: os ids acima são os confirmados; os **palpites a confirmar** (`A_CONFIRMAR`) são: `aba_perfil` (`profile_tab`), `conta_titulo`, `autor_post`, `avatar_perfil`, `grade_item`, `criar`, `galeria`, `galeria_item`, `busca_figurinha`, `enquete_opcao`, `contagem_titulo`, `contagem_data`, `contagem_dia_inteiro`, `data_proximo_mes`, `data_ok`. Textos (en/pt, sem acento e sem maiúscula na comparação): "Add to story"/"Adicionar ao story", "Create"/"Criar", "Gallery"/"Galeria", "poll"/"enquete", "countdown"/"contagem regressiva", "Search"/"Pesquisar", "Add option", "Highlight". **Nunca tocar** em: Entrar, Log in, Concordo, I agree, Aceitar, Accept, Permitir, Allow, Cadastre-se, Sign up, e qualquer botão com "senha", "password", "termos", "terms of", "código de segurança", "captcha", "continuar como". **Parar tudo** (arquivo `H:\HypadoLocal\emulador\PARADO_AVISO_META.json`; só o Antônio apaga) ao ver: "Tente novamente mais tarde", "Try again later", "Ação bloqueada", "Action Blocked", "We restrict certain activity", "Restringimos", "atividade suspeita", "suspicious", "captcha", "confirme que é você", "confirm it's you", "sua conta foi suspensa", "your account has been suspended", pedido de código, termos novos.

**Pedido real da `fila_story`** (`H:\HypadoLocal\emulador\fila_story\<post_id>.json`, gravado pelo `story_clicavel.py fila`; é o que o `story_post.py` consome — **fixture: `fila_story_pedido_real.json`**):

```json
{
 "post_id": "futebol_2026-09-30_1707_cr7-deixa-portugal_ig_feed",
 "conta": "hp.futebol",
 "canal": "futebol",
 "link": "https://www.instagram.com/p/Dd7J4uso3bI/",
 "publicado_em": "2026-09-30 17:07",
 "titulo": "CR7 deixa a concentração de Portugal após a coletiva de Jorge Jesus",
 "destaque": null,
 "criado_em": "2026-09-30 17:35"
}
```

**fixture: `fila_story_pedido_real_carrossel.json`**:

```json
{
 "post_id": "carros_2026-09-30_2315_novo-bmw-serie-3_ig_carrossel",
 "conta": "hp.carros",
 "canal": "carros",
 "link": "https://www.instagram.com/p/Dd7ytwrlQye/",
 "publicado_em": "2026-09-30 23:03",
 "titulo": "O novo BMW Série 3 chegou: 469 cv e 912 km de autonomia no i3 elétrico",
 "destaque": null,
 "criado_em": "2026-09-30 23:11"
}
```

(`publicado_em` é hora de Brasília sem fuso; a rodada 1 aceitava ISO com fuso — mantenha os dois. `destaque: null` = sem destaque. Pasta `fila_story\feitos\` guarda o que já foi.)

**A API para conferir se o story saiu** (Instagram com login do Instagram, o mesmo token do `publicador_meta`): `GET https://graph.instagram.com/v21.0/<ig-user-id>/stories?fields=id,media_type,permalink,timestamp` (só stories ainda vivos, 24 h); o story publicado pela API já tem `permalink` do formato `https://www.instagram.com/stories/<conta>/<id numérico>`. O `<ig-user-id>` vem de `meta_tokens_meta.json → contas["IG_<handle>"].id`. **Você não faz a chamada**: recebe uma função `get_json(url, params) -> dict` injetada (no PC é o `publicador_meta.api` por `curl.exe`).

### 4.8 WhatsApp

- **Grupos:** só **"HP | Comissão 🚀"** (o Antônio é o único membro; é onde vai o resumo, o aviso "no ar" do GTA e tudo que precisa dele) e os grupos da lista **"HP | Grupos"**, um por canal: **"HP | Futebol ⚽"**, **"HP | Filmes 🎬"**, **"HP | Receitas 🍔"**, **"HP | Carros 🏎️"**, **"HP | Destinos ✈️"**. Nenhuma outra conversa: o antigo "Hypado | Comissão 🟣" **não recebe mais nada**. Antes de digitar, conferir o cabeçalho (`#main header`) do grupo certo; nunca clicar na lista por coordenada (já abriu conversa errada).
- **WhatsApp só para 3 coisas:** (1) resumo do dia anterior, de manhã, no grupo de cada canal; (2) aviso **"no ar"** com os links, na hora em que o post sai; (3) sábado: resumo da semana com as melhorias. Mais: responder o Antônio e avisar quando algo precisa dele (senha, login, decisão, falha). **Toda mensagem começa com `*Claude - *`** (aparece **Claude -** em negrito; vale para texto, legenda de anexo e pergunta de enquete). O que **não** começa com isso no grupo é do Antônio. De madrugada (0h–7h30) **nada vai para o WhatsApp**: fica na fila com `enviar_apos`. **Nunca em primeiro plano:** terminou de mandar → a guia do WhatsApp volta para segundo plano.
- **A fila de hoje** é `H:\HypadoLocal\temp\whatsapp_fila.json`: **uma lista** de `{"grupo", "texto", "enviar_apos"}` (hoje está vazia: `[]`). **fixture: `whatsapp_fila_real.json`**:

```json
[
 {"grupo": "HP | Comissão 🚀",
  "enviar_apos": "2026-09-29 07:30",
  "texto": "*Claude - *📌 Pinterest pronto: Receitas, Destinos e Carros com foto, bio, pastas e pins agendados até 06/10 (2 por dia em cada) — Receitas: https://br.pinterest.com/hpreceitas/ · Destinos: https://br.pinterest.com/hpdestinos/ · Carros: https://br.pinterest.com/hpcarros/"},
 {"grupo": "HP | Comissão 🚀",
  "enviar_apos": "2026-09-29 07:30",
  "texto": "*Claude - *🧩 *Conteúdo de amanhã (qua 30/09) agendado*\n• Carrossel \"De 1997 a Vice City de novo\" — 15h, IG + FB\n• 9 stories no IG + FB\n• 5 textos no Threads (9h, 12h, 15h, 18h30, 21h30)"}
]
```

  O seu `whatsapp_local` lê **uma pasta com 1 JSON por mensagem** (`H:\HypadoLocal\whatsapp_fila\`): faça o adaptador dos dois sentidos (lista do PC → pasta; pasta → lista) sem perder `enviar_apos`, e **valide** que o texto começa com `*Claude - *` e que o `grupo` é um dos 6 acima.
- **Aviso "no ar" do GTA** (`06 Projeto\AVISO.md`, tom profissional; shift+Enter quebra linha, Enter envia; só as redes em que o post saiu, **nesta ordem**: Instagram, Facebook, TikTok, YouTube, Threads). Modelo literal:

```
*Claude - *🎬 *Novo vídeo no ar!*
*<título do vídeo>*

Acabou de ser publicado nas nossas redes. Já está no ar nas redes abaixo 🚀

📸 *Instagram:* <link>
📘 *Facebook:* <link>
🎵 *TikTok:* <link>
▶️ *YouTube:* <link>
🧵 *Threads:* <link>
```

  Links: YouTube `https://youtube.com/shorts/<id>`; TikTok `https://www.tiktok.com/@hpgta6/video/<id>`; Instagram e Threads vêm do `links` do `agendados.json` (4.5). Se o link de uma rede não aparecer, usa o link do perfil dela — **não atrasa o aviso**. O estado do que já foi avisado é o `avisos_enviados.json` (4.5). Para os canais o modelo é o mesmo, trocando o título do canal e mostrando só as redes que têm link (**suposição a confirmar com o Antônio**: o `AVISO.md` só descreve o GTA).
- **Como o plantão de hoje manda** (pelo Chrome do Antônio; o seu módulo é o substituto): busca "Pesquisar ou começar uma nova conversa" → digita o nome do grupo → clica no resultado → confere `#main header` → digita (shift+Enter quebra linha) → Enter; anexo: botão "Anexar" do `#main footer` → "Fotos e vídeos" → caixa "Digite uma mensagem" na prévia. Arquivo ≤ 10 MB em `H:\HypadoLocal\upload\`. Depois de reiniciar o PC o WhatsApp Web pode pedir o QR code: **só o Antônio lê** (o seu código para e avisa; nunca tenta logar).

### 4.9 A esteira de pastas (ROADMAP, etapa 3, literal) e o que o PC já tem

```
H:\HypadoLocal\esteira\   (a do PC;  a sua usa H:\HypadoLocal\esteira_sombra)
  01_pedidos → 02_baixados → 03_legenda_dublagem → 04_edicao → 05_revisao → 06_agendados → 07_postados   ·   99_erros
```

- `01_pedidos`: o **Claude** só larga aqui um `pedido.json` (canal, link do vídeo, trecho aproximado, idioma, título/gancho, data e horário, redes). **O app baixa sozinho** a partir do link (`scripts\ytdlp.py`).
- `02_baixados`: trecho bruto + transcrição com tempo por palavra; corte fino automático (começa na 1ª palavra da ideia, termina no fim da frase).
- `03_legenda_dublagem`: correções automáticas de legenda (vocabulário do `config.json`); gringo: tradução + dublagem pt-BR (`dublar.py`). Quando a tradução precisar do Claude, o item espera um `traducao.json` e segue sozinho quando ele aparece.
- `04_edicao`: render 9:16 (`cortar.py`), versão de upload ≤ 10 MB, capa, texto do post (modelo por canal, créditos, hashtags).
- `05_revisao`: o **Claude/revisor** só olha 3 quadros + o texto e grava `aprovado.json` (ou `refazer.json` com o motivo, que devolve à etapa certa).
- `06_agendados`: o app agenda/publica pela API no horário (IG, Threads; FB e YouTube na etapa 4). TikTok: o item espera o Claude agendar pelo Chrome e gravar `tiktok_ok.json`.
- `07_postados`: saiu no ar: grava os links. **É daqui que o plantão manda o aviso "no ar".**
- `99_erros`: o que falhou 3 vezes, com o motivo.
- Cada item é **uma pasta** (`P0_2026-09-30_1847_futebol_gol-arrascaeta`) com tudo dentro; mudar de etapa = **renomear a pasta inteira de uma vez** (mesmo disco: instantâneo; arquivo aberto prende a pasta: tentar de novo com esperas de 0,3/0,7/1/2/3 s); **o app só pega pasta que tem o arquivo `pronto`**.
- **Prioridade no nome:** `P0_` urgente/ao vivo (gol, placar, resultado, bombástica, lançamento) com **faixa expressa** (o motor deixa sempre 1 vaga livre para P0, que passa na frente de tudo e nunca espera um render longo terminar); `P1_` do dia; `P2_` programado (padrão; pasta sem prefixo = P2). Renomear `P2_`→`P0_` muda a prioridade. Nome do item: `P<n>_<AAAA-MM-DD>_<HHMM>_<canal(até 20)>_<apelido(até 40)>`, tudo ASCII sem espaço.
- Estáticos (carrossel, story, texto do Threads) entram em `01_pedidos` com `tipo` e **pulam as etapas de vídeo**.
- Arquivos dentro do item (PC): `pedido.json`, `bruto.mp4`, `fonte.json`, `transcricao.json`, `corte.json` (`{inicio, fim, origem: "automatico"|"pedido", alvo}`), `traducao.json`, `legenda.json`, `final.mp4`, `render.json`, `upload.mp4`, `capa.jpg`, `quadro_1..3.jpg` (nos tempos 15%, 50%, 85%), `post.json`, `publicar.json`, `historico.log`, `pronto`, `aprovado.json`/`refazer.json`, `tiktok_ok.json`, `_tmp\`.
- **O que o PC faz hoje (sua esteira tem que dar o mesmo resultado):** o `hp_studio\esteira\ferramentas.py` chama **no mesmo processo** o código de sempre (`baixar`, `transcrever`, `emenda`, `cortar`, `dublar`, `versao_upload`, `lote`), com os mesmos parâmetros que o `lote.py` usa, mudando só a pasta temporária (cada item usa a sua, `<item>\_tmp`, porque o `cortar.py` grava `gancho.png`, `credito.png`, `mascara.png` com nome fixo no temporário e um P0 rodando junto trocaria a arte de um corte pela do outro). Quatro comandos: `baixar` (→ `bruto.mp4` + `fonte.json`; a folga é `lote.FOLGA` = 4 s), `transcrever` (→ `transcricao.json` + `corte.json` pelo `lote.encostar_em_frases`), `legenda` (→ `legenda.json`; gringo exige `traducao.json`; aplica `correcoes` do pedido; recusa se o trecho ainda está em inglês), `editar` (→ `final.mp4`, `upload.mp4`, `capa.jpg`, `quadro_1..3.jpg`).
- Configuração do PC (`hp_studio\config.py`): `ESTEIRA = H:/HypadoLocal/esteira`; `ESTEIRA_ATIVA = False`; `ESTEIRA_SIMULAR = True`; `ESTEIRA_VOLTA_SEG = 3`; `PRIORIDADE_ESTEIRA = {0: -1, 1: 4, 2: 6}` (P0 = faixa expressa, prioridade < 0); `PUBLICAR_ATIVO = False` (tudo em simulação); `METRICAS_ATIVO = False`; `PESADO_LOCK = H:/HypadoLocal/app/pesado.lock`; `LIMITE_C_GB = 3` (abaixo disso a faixa pesada espera o C: liberar); `PRIORIDADES = {"urgente": 0, "normal": 5, "baixa": 9}` na fila SQLite. **Flags só o Diretor liga.**

### 4.10 O radar de fontes (`scripts\radar_hp.py` + `07 Canais\radar\<canal>.json`) — já existe

Docstring real do `radar_hp.py`: vigia local, **sem Claude**, do que está bombando agora em `gta`, `futebol`, `filmes` e `carros`; roda a cada 20 min das 6h às 23h e só acorda o Claude (rotina `hp-radar-furo`) quando há alerta **P0/P1**; depois do post continua medindo e gera alerta de **COMPLEMENTO** (≥ 1 h depois da parte anterior, máx. 4 partes/dia) e **FATO_NOVO**. Fontes (grátis, sem token): Google News RSS, RSS de sites e salas de imprensa, YouTube (RSS do canal; se falhar, a página `/videos`), busca do YouTube (hoje), Google Trends BR, Newswire da Rockstar. Comandos reais:

```
radar_hp.py varrer [--canal gta,carros] [--simular]   -> candidatos.json + alertas.json por canal (--simular: lê a web, grava em _simulacao)
radar_hp.py alertas [--json] [--canal x]               -> só os alertas "novo"
radar_hp.py feito <gta|futebol|filmes|carros> <id> [--link URL] [--encerrar]
radar_hp.py pular <canal> <id> [--motivo "..."]
radar_hp.py candidatos <canal> [--n 10]
radar_hp.py resolver [--canal x] [--gravar]            -> acha channel_id faltando (cache no H:)
radar_hp.py loop [--simular]                           -> 20 em 20 min, 6h-23h, instância única
```

Variáveis de ambiente: `HP_RADAR_CONFIG` (padrão `07 Canais\radar`), `HP_RADAR_DADOS` (padrão `H:\HypadoLocal\radar`), `HP_RADAR_FILA_API`.

**fixture: `radar_gta.json`** (a config **inteira** do GTA; as dos outros 3 canais têm as mesmas chaves e, no Carros e no Futebol, listas de `google_news`, `rss` e `youtube` bem maiores):

```json
{
 "canal": "gta",
 "nome": "GTA 6 | HP",
 "ativo": true,
 "google_news_janela": "12h",
 "google_news": [
  {"q": "\"GTA 6\" OR \"GTA VI\"", "lingua": "pt"},
  {"q": "\"GTA 6\" OR \"GTA VI\" OR \"Grand Theft Auto VI\"", "lingua": "en"},
  {"q": "\"Rockstar Games\" OR \"Take-Two\"", "lingua": "en", "filtrar": true}
 ],
 "rss": [
  {"nome": "IGN", "url": "https://www.ign.com/rss/articles/feed", "oficial": false, "filtrar": true, "peso": 1.0},
  {"nome": "GameSpot", "url": "https://www.gamespot.com/feeds/news/", "oficial": false, "filtrar": true, "peso": 1.0}
 ],
 "rockstar_newswire": true,
 "youtube": [
  {"nome": "Rockstar Games", "url": "https://www.youtube.com/@RockstarGames", "channel_id": "UC6VcWc1rAoWdBCM0JxrRQ3A", "peso": 1.5, "oficial": true, "video_reutilizavel": true, "nota_uso": "trailer só com comentário nosso; nunca trailer puro"}
 ],
 "criadores_do_config": true,
 "youtube_busca": ["GTA 6", "GTA VI"],
 "trends": true,
 "palavras": {"trailer": 6, "trailer 3|terceiro trailer|third trailer": 10, "gameplay oficial|official gameplay": 8, "adiado|adiamento|delayed|delay|postponed": 10, "pre venda|pre order|preorder|pré-venda": 8, "preco|price|valor": 6, "19 de novembro|november 19": 5},
 "entidades": {"gta 6|gta vi|grand theft auto vi|gta6": 6, "rockstar games|rockstar": 4, "take two|take-two": 3, "jason": 3, "lucia": 3, "leonida": 3, "vice city": 3},
 "bombasticas": ["trailer 3", "terceiro trailer", "third trailer", "novo trailer", "new trailer", "adiado", "adiamento", "delayed", "pre venda", "pre order", "preco oficial", "data de lancamento", "release date", "gameplay oficial", "official gameplay", "capa oficial", "box art"],
 "fato_novo": ["confirma", "confirmed", "responde", "anuncia", "announced", "preco", "price", "data", "trailer", "adiado", "delay"],
 "negativas": ["fan made", "fanmade", "fan trailer", "concept", "conceitual", "feito por ia", "ai generated", "mod", "mods", "remake", "unreal engine", "gta online", "fortnite", "minecraft", "roblox", "roleplay"],
 "genericas": ["gta", "6", "vi", "grand", "theft", "auto", "rockstar", "games", "game", "jogo", "video", "novo", "nova", "gta6", "oficial", "official"],
 "dominios_oficiais": ["rockstargames.com", "take2games.com", "x.com/rockstargames"],
 "limiares": {"P0": 85, "P1": 65, "vph_min": 500, "vph_cheio": 50000, "relevancia_min": 6},
 "max_alertas_dia": 6, "max_p0_dia": 3,
 "validade_h": {"P0": 3, "P1": 4},
 "complemento": {"min_veiculos_novos_2h": 3, "vph_min": 20000, "intervalo_h": 1, "max_partes_dia": 4, "encerrar_sem_calor_h": 6},
 "yt_html_intervalo_min": 60, "yt_html_intervalo_oficial_min": 20, "yt_refinar_max": 6, "yt_refinar_horas": 6,
 "dedup": {"prefixos_fila": ["gta_"]},
 "perguntas": [{"se": ["trailer"], "pergunta": "Ficou top?", "opcoes": ["🔥 Sim", "👎 Não"]}, {"se": ["adiado", "delayed", "delay"], "pergunta": "Vale esperar?", "opcoes": ["Vale", "Não vale"]}],
 "pergunta_padrao": "Vai bombar?",
 "interacoes": [{"se": ["adiado", "delayed"], "texto": "O que achou do adiamento?"}],
 "interacao_padrao": "O que você espera do GTA 6?",
 "chamadas": {"furo": "NOVIDADE DO GTA 6! Toque 👆", "complemento": "TEM MAIS DO GTA 6! Toque 👆", "fato_novo": "ATUALIZAÇÃO! Toque pra ver 👆"}
}
```

(Aqui encurtei `palavras`, `bombasticas`, `negativas`, `perguntas` e `interacoes`; as chaves e os tipos são os reais.) As entradas de `rss` são `{nome, url, oficial, filtrar, peso}`; as de `youtube` são `{nome, url (o @handle), channel_id (UC…), peso, oficial, video_reutilizavel, nota_uso?}`.

**O que cada config tem hoje** (todos os `channel_id` já resolvidos; 0 sem id):

| Canal | `youtube` (nomes) | `rss` (nomes) |
|---|---|---|
| gta | Rockstar Games | IGN, GameSpot (+ Newswire da Rockstar, que tem coletor próprio) |
| futebol | CBF TV, CONMEBOL Libertadores, ge, Flamengo, Corinthians, Palmeiras, São Paulo FC, Vasco, Santos, Botafogo, Fluminense, Grêmio, Internacional, Cruzeiro, Atlético-MG, Bahia (16) | ge |
| filmes | Netflix Brasil, Prime Video Brasil, HBO Max Brasil, Disney+ Brasil, Paramount Pictures Brasil, Warner Bros. Pictures, Warner Bros. Pictures Brasil, Marvel Entertainment, Marvel Brasil, Sony Pictures Brasil, Universal Pictures Brasil, Omelete (12) | Deadline, Variety, Cinepop, Legião dos Heróis |
| carros | BMW, Mercedes-Benz, Audi, Porsche, Volkswagen, Toyota, Ferrari, Lamborghini, McLaren, Tesla, BYD Brasil, Hyundai Worldwide, Kia, Ford, Chevrolet Brasil, Fiat Brasil, Jeep Brasil, Volkswagen do Brasil, Toyota do Brasil, Honda Automóveis, Renault Brasil, GWM Brasil, Volvo Cars, Land Rover, Autoesporte, Quatro Rodas, Acelerados, carwow, Top Gear (29) | BMW Group PressClub, Hyundai News, Toyota Pressroom, Autoesporte, Quatro Rodas, Notícias Automotivas, Motor1, Carscoops, The Drive (9) |

`radar_hp.py` **ainda não conhece** Receitas e Destinos (o `choices` do argparse é `gta|futebol|filmes|carros`). Isso fica para outra rodada; não faça.

---

## 5. As tarefas

Cada tarefa tem **critério de pronto**. Marque no `ENTREGA.md`, tarefa por tarefa, o que ficou pronto, o que ficou pela metade e o que não deu. Convenções que valem para todas:

- Transporte injetado (rede, `adb`, relógio, disco de produção): nenhum teste toca no mundo real; relógio sempre injetado (`agora=`).
- Texto de interface e mensagem de erro em **português BR**, para leigo ("não achei o botão X na tela; o Instagram mudou?").
- Saídas de CLI: código `0` ok · `1` erro · `2` bloqueado (trava, horário, já feito) · `3` parou por aviso da rede · `4` aparelho bloqueado/precisa do Antônio.
- Cada módulo novo: `LEIA.md` de 1 página + docstring no topo no estilo dos scripts do PC (o que faz, uso, regras).
- Tamanho dos testes: rápidos (a suíte nova inteira em menos de 3 minutos no seu Linux).

### A. Adaptadores reais: o seu repositório passa a falar os formatos do PC (prioridade máxima)

**Objetivo:** acabar com as suposições da rodada 1. Cada formato da Seção 4 vira fixture e adaptador testado. O PC já consertou **à mão** parte disto (Seção 3.2); você reproduz no repositório, com testes, para a próxima integração entrar sem remendo. Entregue arquivos novos em `app/hp_studio_nuvem/…` e o que mudar nos antigos em `PATCHES.md`.

**A1. Fila da API** — `hpbase/fila_api_pc.py` (mesmos nomes do PC), testes em `hpbase/testes/test_fila_api_pc.py` sobre as fixtures de 4.1:

- `handle(item)`: handle da conta (`hp.futebol`) a partir de `conta` ou, se faltar, de `canal` (`futebol` → `hp.futebol`; `gta` → `hpgta6`; mapa de 4.2).
- `chave_token(item)`: `IG_<handle>` (rede `instagram`) ou `TH_<handle>` (rede `threads`). `token_do_item(...)` só devolve o token a quem o pediu por função injetada; **nunca** imprime.
- `id_da_conta(chave, meta_json)`: lê `contas[chave].id` de um dict do `meta_tokens_meta.json` (id não é segredo). Não usa o `carregar_meta` do publicador (ele **regrava** o arquivo).
- `inicio(item)`: `datetime` de `quando` (`"AAAA-MM-DD HH:MM"`, aceita `T`, hora de Brasília, sem fuso).
- `montar_item(conta, rede, tipo, arquivos, legenda, quando, canal=None, titulo=None, capa=None, depende_de=None, id_=None)`: devolve o dict de 4.1 e **valida com as mesmas regras e as mesmas mensagens** do `_validar` (4.2): `campo 'quando' faltando`, `rede tem que ser instagram ou threads…`, `arquivo não existe: <caminho>`, `carrossel precisa de 2 a 10 arquivos (veio N)`, `legenda com N caracteres (máx. 2200 no Instagram)`, `texto com N caracteres (máx. 500 no Threads)`, `feed = exatamente 1 imagem…`, `reel = exatamente 1 vídeo`, `story = exatamente 1 arquivo`, `post de texto sem legenda`. Id padrão por convenção de 4.1.
- `ler_confirmacao(id_, pasta_fila)`: olha `feitos\<id>.json` (`status == "no_ar"` + `resultado.permalink`) e `erros\<id>.json` (`erro` ou `ultimo_erro`) e devolve `{"estado": "no_ar"|"erro"|"pendente", "link": …, "erro": …, "publicado_em": …}`; `pendente` se o arquivo ainda está na raiz.
- `publicador_adaptado(publicar_item_real)`: devolve uma função `(item) -> {"media_id", "permalink", "publicado_em"}` que chama o `publicar_item(item, toks, meta, simular=False)` **injetado**, converte `"limite"` na exceção `LimiteDaConta` e `ErroAPI` na sua exceção própria. **Nunca é chamada com `simular=True`** (no PC o `simular` ainda sobe o arquivo para a hospedagem temporária): em simulação o adaptador devolve um resultado falso **sem chamar** o publicador real.
- Não nasce item de Facebook por esta fila (rede `facebook` → erro com a mensagem de `_validar`).
- **Pronto quando:** todo item de 4.1 (reel, carrossel, feed, Threads, story, texto, feitos IG/Threads, erro, story_clicavel parqueado) passa por `montar_item` → `ler_confirmacao`; os casos de erro listados acima dão a mensagem idêntica; a esteira (`esteira/agendador.py`) usa só estas funções (descreva a troca no `PATCHES.md`); ≥ 25 testes.

**A2. Tokens** — `metricas/chaves_pc.py` + `PATCHES.md` para `metricas/config.py`: dado o diretório de segredos (injetado), diga **quais chaves existem sem ler o valor** e monte, por conta e rede, `{"chave_token", "id", "host", "versao"}`:

- IG: `IG_<handle>` + `contas/IG_<handle>/id` do `meta_tokens_meta.json`; host `graph.instagram.com`, versão `v21.0`. Threads: `TH_<handle>` + id idem; host `graph.threads.net`, versão `v1.0`.
- Facebook: `FB_<canal>` em `facebook_tokens.txt` + `<canal>/id` em `facebook_paginas.json`; host `graph.facebook.com`, versão `v26.0`.
- YouTube: `oauth/refresh_tokens/<canal>` + `oauth/client_id` + `oauth/client_secret` em `youtube.json`; id do canal em `canais/<canal>` (ou `youtube_canais.json:<canal>/id`). YouTube só coleta com `"autorizado": true` na config de contas; senão o status é `nao_autorizado`.
- Nomes antigos da rodada 1 (`IG_<CONTA>_TOKEN`…) continuam valendo **depois** dos reais.
- **Pronto quando:** `python -m metricas coletar --simular` sobre fixtures temporárias (6 contas × IG/Threads/Facebook com valores `FAKE_NAO_E_TOKEN_n`) dá **0 `sem_token`**; YouTube dá `nao_autorizado` com a flag falsa e "coletaria" com a verdadeira (só o GTA tem refresh token no PC); teste que captura stdout, stderr e log e **prova que nenhum valor falso aparece**; ≥ 12 testes.

**A3. Comandos reais dos scripts** — `esteira/comandos_pc.py` (funções puras `argv_*`) + `esteira/config.json → comandos` (PATCHES). Cada função recebe o pedido normalizado e devolve a **lista de argumentos** exata, e o teste compara com o argv que o PC usa (Seção 4.4):

- `argv_baixar(pedido, destino)`: `[PYTHON, ytdlp.py, "-f", "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080]/b", "--merge-output-format", "mp4", "-o", destino, "--no-playlist", "--no-warnings", "--download-sections", "*INI-FIM", "--force-keyframes-at-cuts", url]` com `INI = hms(inicio − 4)` e `FIM = hms(fim + 4)` (`hms` = `HH:MM:SS.mmm`, `lote.hms`). Pedido com `arquivo` (trecho já baixado) não baixa: copia.
- `argv_transcrever(bruto, id_streamer)` e `argv_cortar(...)` (o argv de `lote.renderizar` em 4.4, com `extra` na ordem `--transcricao`, `--fade-saida`, `--dublar`), `argv_versao_upload(final)`, `argv_dublar_avulso(corte, transcricao, inicio, fim, saida=None)`, `argv_estaticos_carrossel(spec, saida, tiktok=False)`, `argv_estaticos_story(tipo, saida, **opcoes)`, `argv_estaticos_destaques(saida)`, `argv_posts_render(canal, spec_json)` (o script certo por canal: `posts_futebol.py|posts_filmes.py|posts_receitas.py|posts_carros.py|posts_destinos.py render <spec>`; `posts_canais.py` só para os modelos genéricos), `argv_story_clicavel_fila()`.
- **Erros da rodada 1 que não podem voltar:** `ytdlp.py --saida`, `dublar.py --srt` ou `--texto-arquivo`, `estaticos.py --pedido` **não existem**. Teste que prova que nenhuma função gera essas opções.
- Os comandos usam o `PYTHON` do PC (`%LOCALAPPDATA%\Programs\Python\Python312\python.exe`) e a pasta de scripts `06 Projeto\scripts` (4.4), nunca caminhos do Linux; caminho com espaço sai **sem** aspas dentro da lista (aspas só ao imprimir para o humano).
- **Pronto quando:** teste "golden" por função (≥ 20 casos, incluindo pedido `arquivo`, gringo com `--dublar`, `fade_saida`, `trechos`/emenda) e um teste que roda `esteira --simular` com um pedido real de 4.5 e confere o argv de cada etapa.

**A4. Pedido real e lote de estáticos** — `esteira/pedido_pc.py` e `scripts/story_post_lote.py`:

- `esteira/pedido_pc.py`: aceita o **pedido real** de 4.5 (`tipo: corte|carrossel|story|texto`, `prioridade`, `data`, `video|link|arquivo`, `streamer`, `inicio`, `fim`, `gancho`, `titulo`, `legenda`, `redes`, opcionais `corte, trechos, zoom, cobrir, bipes, tarjas, fade_saida, dublar, idioma, hashtags, textos, correcoes, apelido`) e converte para o modelo interno da sua esteira **e para o `post.json`** de 4.5. Recusa Flow Games e criador sem `autorizado: true` com a mensagem em português; nome da pasta `P<n>_AAAA-MM-DD_HHMM_<canal>_<apelido>`.
- `scripts/story_post_lote.py`: `ler_interativo(lote_json)` lê a chave **`interativo`** do lote de estáticos real (4.5) e também o formato antigo `story_enquete` da rodada 1. `pergunta_da_figurinha(interativo, limite=25)` decide, **nesta ordem**: (1) `interativo.pergunta_curta` se existir (campo novo e opcional); (2) `encurtar_pergunta()` determinístico: **nunca corta no meio de palavra**, tira vocativo e introdução, e prefere a **última oração terminada em `?`** — `"Furacão chegando em Leonida. O que você faz?"` (46) vira `"O que você faz?"` (15); (3) se nada couber em 25, **recusa com explicação** (não corta no escuro). As opções (2 a 4) também ≤ 25 cada. `PATCHES.md` diz onde `story_post._item_do_lote` chama isto (a função fica perto da linha ~1989 do `story_post.py` do PC).
- `PENDENCIAS_PARA_O_DIRETOR.md`: texto pronto para o SKILL do `hypado-estaticos` passar a gravar `interativo.pergunta_curta` (≤ 25 caracteres, uma pergunta que fecha sozinha) além da `pergunta` completa que vai na arte.
- **Pronto quando:** o lote real de 4.5 dá `pergunta_da_figurinha == "O que você faz?"`; com `pergunta_curta` ela vence; pergunta impossível → recusa; ≥ 20 testes (acentos, emoji, pontuação, opções longas, 1 e 5 opções).

**A5. Marca única** — `hpbase/marca.py`: a tabela de 4.6 como dado (`CANAIS[canal] = {nome, handle, cor_canal, cor_post, fundo, destaque, extras, fontes}`, `GTA6 = {rosa, laranja, noite, ciano}`), os tamanhos e o resolvedor `fonte(nome, tamanho)` com a ordem de 4.6. Exponha os **conflitos** como constantes nomeadas (`CARROS_COR_PERFIL`, `CARROS_COR_POST`, `GTA_ROSA_POST`, `GTA_ROSA_PERFIL`) e **pare de duplicar cor** nos módulos da rodada 1 (`reel_futebol_arte.py` passa a usar `marca.CANAIS["futebol"]`: verde `#1ED760`, não o amarelo `#FFD23F`; descreva no `PATCHES.md`). **Pronto quando:** teste que compara cada valor com a tabela de 4.6, contraste WCAG ≥ 4.5 de texto branco sobre cada `fundo`, o resolvedor cai no DejaVu no Linux sem quebrar, e ≥ 12 testes.

**A6. Trava e pastas** — reproduza com testes o que 3.2 descreve: `hpbase/trava.py` lê/grava os dois formatos de `pesado.lock` (ilegível usa a data do arquivo e **nunca** vira "velha" de graça; sem pid vale a regra de 30 min; com pid vale "processo morto ou 3 h"); `esteira/config.py` acha `06 Projeto\scripts`; `hpbase/caminhos.py` com `HP_ESTEIRA_NOME` e `HP_PARIDADE_NOME`. ≥ 7 testes.

**A7. WhatsApp** — `whatsapp_local/fila_pc.py`: adaptador da fila **real** (lista `[{grupo, texto, enviar_apos}]` em `temp\whatsapp_fila.json`, 4.8) para a sua pasta de 1 JSON por mensagem, e de volta; validação (`*Claude - *` no começo; `grupo` ∈ os 6 nomes; `enviar_apos` respeitado; mensagem criada entre 0h e 7h30 sem `enviar_apos` ganha `AAAA-MM-DD 07:30` do mesmo dia, porque de madrugada nada vai para o WhatsApp); leitor do `agendados.json` real de **todos os 6** lugares (GTA em `06 Projeto\agendados.json` e os 5 canais em `07 Canais\<Pasta>\agendados.json`; ambos `{"itens": [...]}`); `avisos_enviados.json` tolerando a lista embrulhada `[{"value": [...], "Count": N}]`; `montar_aviso_no_ar(item)` que gera o texto literal de 4.8 (ordem Instagram, Facebook, TikTok, YouTube, Threads; só as redes com link). **Pronto quando:** o `agendados_exemplo.json` de 4.5 vira exatamente o texto esperado (golden), e ≥ 15 testes.

**A8. Teste de contrato** — `tests/test_contrato_pc_real.py`: carrega **todas** as fixtures de `tests/fixtures/pc_real/` e passa cada uma pelo adaptador responsável; falha com mensagem clara se uma fixture mudar de formato. É o que o PC roda depois de cada integração.

**Pronto da tarefa A:** a suíte da rodada 1 continua verde (reporte o número real) + os testes novos (≥ 100 no total entre A1–A8); `PATCHES.md` completo.

### B. YouTube: o que ainda falta além do envio (`publicar_extra/youtube_extra.py`)

O **envio** já existe no PC e foi testado (3.3). **Não refaça.** Entregue só as **lacunas**, para ligar quando o Google aprovar a auditoria da API:

- **B1. Playlists:** `playlist_do_canal(cliente, token, canal, titulo, criar=True) -> id` (`playlists.list mine=true` com paginação de 50; cria com `playlists.insert` se não existir, **nunca duplica**; cache em `H:\HypadoLocal\app\publicar\youtube_playlists.json` = `{canal: {titulo: id}}`, injetado) e `adicionar_na_playlist(cliente, token, playlist_id, video_id)` (`playlistItems.insert`; erro "já está na playlist" não é falha).
- **B2. Corrigir vídeo já enviado:** `atualizar_video(cliente, token, video_id, titulo=None, descricao=None, tags=None, categoria=None, publicar_em=None)`: lê o vídeo (`videos.list part=snippet,status`), mescla e manda `videos.update` com o `snippet` **completo** (a API exige `title` e `categoryId`) e o `status` (o `publishAt` em UTC só vale com `privacyStatus=private`). Valida os limites do PC: título ≤ 100 sem `<` e `>`, descrição ≤ 5.000 bytes, tags ≤ 500 caracteres somados.
- **B3. Conferência em lote:** `conferir_lote(cliente, token, esperado: dict) -> dict`: um `videos.list part=status,snippet id=a,b,c` por 50 ids (1 unidade) e, por vídeo, o **diagnóstico** igual ao do PC: pediu agendado e ficou privado sem `publishAt` → `travado como privado (projeto sem auditoria)`; pediu público e ficou privado → o mesmo; agendado que passou do horário e continua privado → o mesmo; `uploadStatus` e `rejectionReason` (`length`, `duplicate`, `copyright`…) traduzidos em português. É o que substitui o "conferir a agenda no YouTube Studio pelo Chrome".
- **B4. Legenda em arquivo (baixa prioridade):** `transcricao_para_srt(dados, inicio, fim, max_palavras=4)` (função pura, testável sem rede; o formato é o da 4.5) e `enviar_legenda(cliente, token, video_id, srt, idioma="pt-BR", nome="Português")` com `captions.insert`. Confirme o **custo em unidades** na documentação oficial e deixe a função desligada por padrão se for alto.
- **B5. Cota:** `registro_de_cota(chamadas)` soma as unidades por tipo de chamada e avisa a 80% do dia (10.000 unidades). **O que o PC conferiu na documentação oficial em 15/09/2026:** `videos.insert` tem balde próprio de 100 envios/dia por projeto (não gasta as 10.000); `thumbnails.set` custa 50; `videos.list` e `channels.list` custam 1. **O que você precisa conferir e citar com a data** (valores de memória, não confirmados): `videos.update` 50, `playlistItems.insert` 50, `playlists.insert` 50, `captions.insert` 400, `playlists.list` 1. Valor que você não conseguir confirmar fica marcado `"confirmar": true`.
- **B6. Revisão crítica (texto, sem código):** leia a Seção 3.3 e liste no `ENTREGA.md` os **riscos** que você vê no que o PC já faz (Shorts, `selfDeclaredMadeForKids`, `containsSyntheticMedia`, `publishAt` com granularidade, vídeo > 15 min sem verificação por telefone, cota). Sem inventar: cite a página oficial.
- **Contrato com o PC** (para encaixar sem retrabalho): o seu código recebe `cliente` com `pedir(metodo, url, *, consulta=None, form=None, multipart=None, json_=None, corpo=None, cabecalhos=None, tempo=120) -> Resposta` (`Resposta.status`, `.dados` dict ou texto, `.cabecalhos` em minúsculas, `.json()`) e levanta `ErroRede(mensagem, transitorio=False, status=None)`; o `token` de acesso chega por uma função injetada `token_de(canal)` (o PC faz o OAuth; **você não toca em refresh token**). Entregue um `contrato_pc.py` com **cópias mínimas** de `Resposta`, `ErroRede` e de um `ClienteFalso` para os testes, e um comentário dizendo "no PC, importar de `hp_studio.publicar.http`". Resultados no formato `{"status", "link", "id", "erro"}` (`entrada()` do PC).
- **Pronto quando:** testes com `ClienteFalso` conferem **URL, método, parâmetros e corpo** de cada chamada; paginação; idempotência (rodar de novo não duplica playlist nem item de playlist); tradução de erros (`quotaExceeded`, `uploadLimitExceeded`, `duplicate`, 401/403); nenhum token em log; ≥ 40 testes.

### C. Facebook Página (e comentários): o que ainda falta além de postar (`publicar_extra/facebook_extra.py`)

Foto, carrossel, reel (com agendamento nativo), story e texto **já existem no PC** (3.3). **Não refaça.** Entregue as lacunas, com o mesmo contrato `cliente` da tarefa B:

- **C1. Agenda da Página por API:** `listar_agendados(cliente, token, pagina_id)` (`GET /{page}/scheduled_posts`; confirme na documentação oficial como listar também **reels agendados** e cite a página), `cancelar_agendado(cliente, token, id)`, `reagendar(cliente, token, id, nova_hora)` (a Meta aceita de 10 minutos a 75 dias; reel de 10 min a 29 dias) e `comparar_com_agendados_json(agendados_api, agendados_json_do_canal)` → relatório de **buraco, duplicado e hora errada**. É o que o `conferente-de-agenda` hoje faz abrindo o Planner do Business Suite pelo Chrome.
- **C2. Comentários da Página (Antônio, 30/09/2026 11:52, vale para todas as contas HP):** *"antes de responder, veja se precisaria de resposta, ou somente a curtida sirva; se for algo ofensivo, não faça nada de curtida nem nada"*.
  - `ler_comentarios(cliente, token, post_id, desde=None)` (`GET /{post}/comments` com `fields=id,message,from,created_time,like_count,comment_count`, paginado), `curtir(cliente, token, comentario_id)`, `responder(cliente, token, comentario_id, texto)`, `ocultar(cliente, token, comentario_id)`.
  - `classificar_comentario(texto) -> "responder" | "curtir" | "ignorar"`, **função pura, conservadora, sem IA**: `responder` = pergunta, dúvida, pedido ou crítica que vale conversa; `curtir` = elogio, emoji, marcação de amigo; `ignorar` = ofensivo (**sem curtida e sem resposta**) e spam (link, "ganhe dinheiro", "chama no pv"…). Na dúvida: `curtir`. Pesquisa de léxico em português BR fica numa tabela de dados (`lexico_comentarios.json`) fácil de ajustar, e **o Antônio revisa a lista de ofensivos**.
  - Regras de execução (campos de configuração, não constantes soltas): **1 resposta por pessoa**, máximo **25 respostas por passada**, só em post **nosso**, nunca em massa, intervalo entre respostas, e o módulo **só monta a proposta** (`planejar(...)` devolve a lista de ações) — `executar(..., enviar=False)` por padrão e **o PC liga o envio**. Permissões de token necessárias (`pages_read_engagement`, `pages_manage_engagement`): descreva no `ENTREGA.md`, para leigo, o que o Antônio teria de autorizar se faltar.
  - Banco de testes: ≥ 60 comentários em português BR **inventados por você** (elogio, emoji, pergunta, crítica, ofensa, spam, gíria, caixa alta) com a classe esperada; o critério é **zero falso "responder" em ofensivo** e nenhum "responder" em emoji puro.
- **C3. (Só se sobrar tempo; marque no `ENTREGA.md` se não fez)** o mesmo para **Instagram** (`GET /{media-id}/comments`, `POST /{comment-id}/replies`, ocultar) e **Threads** (`GET /{media-id}/replies`, responder pelo `reply_to_id`), reaproveitando `classificar_comentario`. O app do Threads já tem `read_replies` e `manage_replies`; para o Instagram **confirme na documentação qual permissão exige** e escreva no `ENTREGA.md`.
- **Pronto quando:** ≥ 40 testes com `ClienteFalso`; idempotência (não curte nem responde duas vezes); o texto de qualquer erro da Graph API chega em português (`erro_graph` do PC tem os códigos de reel: 1363040 proporção, 1363127 resolução, 1363128 duração, 1363129 fps).

### D. Artes de story profissionais por canal (`scripts/story_artes.py`)

**Objetivo:** hoje o story de divulgação é uma imagem simples. Entregue um gerador (Pillow, 1080x1920) com **3 modelos × 6 canais**, na paleta e nas fontes reais (4.6). É a arte que o `story_post` (tarefa E) coloca no celular com as figurinhas por cima.

- **CLI:** `python story_artes.py render <spec.json>` · `python story_artes.py todas <canal> <pasta>` · `python story_artes.py exemplos <pasta>` (gera os 18 e uma `_prancha_story.jpg`). Spec: `{"canal": "futebol", "tipo": "chamada|maissobre|interacao", "capa": "<imagem do post, opcional>", "rotulo": "NOVO REEL", "chamada": "…", "fatos": ["…"], "pergunta": "…", "credito_foto": "…", "figurinhas": ["link"], "cor_destaque": null, "saida": "<pasta>", "nome": "<prefixo>"}`; `cor_destaque` só vale no Futebol (cor do clube do post, regra de 4.6).
- **Modelo 1 — `chamada` ("chamada do post"):** a **capa do post** como cartão com cantos arredondados (aprox. 860 px de largura, enquadrada por `foco`), um **rótulo** em pílula (`NOVO REEL`, `NOVO CARROSSEL`, `NOVA NOTÍCIA`…), a **chamada** (≤ 45 caracteres, até 2 linhas, `*destaque*` na cor do canal), uma **seta vetorial** "toque pra ver" (desenhada, **não emoji**) apontando para a **zona reservada da figurinha de link** (retângulo `(140, 1500)–(940, 1640)`, só um contorno fino e translúcido), selo HP e `@` do canal. O spec traz `"figurinhas": ["link"]` (padrão) ou `["link", "enquete"]`: com a enquete, o cartão da capa **encolhe** (cerca de 520 px de largura, no alto, y 290–900) para sobrar a **zona da enquete** `(110, 930)–(970, 1480)` acima da zona do link; sem enquete o cartão ocupa a parte grande do quadro.
- **Modelo 2 — `maissobre` ("mais sobre"):** o story que continua o assunto: 2 a 4 **fatos** curtos (≤ 70 caracteres cada) em linhas com marcador, um **dado forte** opcional em tamanho grande (número ou nome), miniatura do post e CTA "Salva o post" / "Leia a legenda".
- **Modelo 3 — `interacao` ("interação"):** uma **pergunta grande** (≤ 60 caracteres) e a **zona livre da enquete** `(110, 930)–(970, 1480)` (a mesma do `estaticos.py interativo`); opcional "você prefere" com duas fotos lado a lado acima da zona.
- **Personalidade por canal (siga as referências de 4.6):** GTA (Bauhaus 93, título com degradê rosa→laranja, fundo noite com brilho); Futebol (Anton, caixa escura translúcida com contorno fino, verde HP, **foto de cor natural**); Filmes (pílula amarela, caixa amarela com contorno preto ou a variação escura); Receitas (faixas amarelas e serifa DM Serif nas chamadas, laranja nas etiquetas); Carros (etiqueta/faixa vermelha `#E61E2D`, frase curta em itálico com traço vermelho, "HP" no canto); Destinos (azul com curvas, ciano, pílula "IDA E VOLTA" só em preço).
- **Regras:** nenhuma linha de texto ou elemento importante nos 250 px do topo nem nos 350 px da base (as zonas das figurinhas ficam **dentro** das zonas seguras); texto sempre cabe (reduz a fonte até um mínimo e, se não couber, **recusa com explicação** em vez de estourar a margem); sem emoji na arte (`sem_emoji`); crédito da foto na arte quando houver `credito_foto`; ao lado de cada JPG sai um `<nome>_zonas.json` com as zonas das figurinhas **em pixels e em fração da tela**, para o `story_post` saber onde soltar (`{"link": [x0,y0,x1,y1], "enquete": [...]}`).
- **Fontes:** o resolvedor de `hpbase/marca.py` (A5). No Linux de teste cai no fallback; no PC sai com as fontes reais.
- **Pronto quando** (testes de render, sem olhar para a imagem): tamanho 1080x1920; **caixa de todo texto dentro da zona segura** (renderize cada texto numa camada própria e confira o `bbox`); contraste WCAG ≥ 4.5 entre cada texto e o fundo amostrado; as zonas das figurinhas ficam sem texto (variância baixa fora do contorno); a cor dominante do fundo/destaque casa com a do canal dentro de uma tolerância; entrada com emoji sai sem emoji; **determinístico** (mesma entrada → mesmo SHA-256 do PNG); texto longo demais → erro em português; os 18 exemplos em menos de 60 s; ≥ 45 testes. Gere também a prancha e **descreva no `ENTREGA.md`** o que viu nela (você consegue ver imagens) e o que o Antônio deve conferir.

### E. `story_post` para celular real por ADB (e emulador)

**Contexto:** o `story_post.py` da rodada 1 já existe no PC e roda em `--simular` (6 stories prontos na `fila_story`). Hoje ele só fala com o **emulador**, com 15 seletores que são **palpite** (4.7), só faz story de **post compartilhado** e **enquete** do GTA, e a pergunta da enquete real tem 46 caracteres. **Não reenvie o `story_post.py`:** entregue módulos **novos** que ele importa e `PATCHES.md` com as linhas a trocar.

- **E1. `scripts/story_dispositivo.py` — o aparelho (emulador ou celular real):**
  - `Dispositivo(runner, serial=None, relogio=time)`: `runner(argv) -> (codigo, saida)` injetado (no PC é `subprocess.run` com `creationflags=0x08000000` e `timeout`); **seleção de aparelho**: `--serial`, variável `HP_ANDROID_SERIAL` ou, se houver exatamente **um** `device` em `adb devices`, ele; com 2 ou mais ou nenhum, recusa listando os seriais (preferência `--emulador`/`--celular`).
  - `esperar_boot()`, `tamanho_tela()` (`wm size`; use **sempre** a tela do aparelho, nunca 1080x2400 fixo), `tela_acesa_e_destravada()` (sem digitar PIN: se estiver bloqueado, **código de saída 4** e a mensagem "celular bloqueado: o Antônio desbloqueia"), `app_na_frente()` (`dumpsys activity activities`, pacote `com.instagram.android`).
  - `dump()` com **repetição** (o `uiautomator dump` falha de vez em quando) devolvendo nós com `bounds`, `id`, `texto`, `desc`, `clicavel`; buscas `achar(id=…, texto=…, desc=…, contem=True)` ignorando maiúscula e acento; `tocar(no)` no **centro dos bounds**; `deslizar(de, para, ms)`; `tecla(codigo)`; `screencap(destino)`.
  - **`digitar(texto)`**: ASCII pelo `adb shell input text` (espaço vira `%s`, aspas removidas, como o `digitar.py`); acento e emoji pela política da Seção 4.7 (padrão: troca por letra sem acento **e registra no log**; o modo de acento real fica desligado e documentado).
  - `empurrar_arte(arquivo_local, nome_ascii)`: `adb push` para `/sdcard/Pictures/HP/<nome>` + aviso ao MediaStore para a foto aparecer na galeria do Instagram. **Confirme na documentação do Android (API 34) o caminho que funciona** (o `MEDIA_SCANNER_SCAN_FILE` é antigo) e entregue o principal e um plano B; o que só dá para confirmar no aparelho vai para o `ENTREGA.md`. Nome do arquivo sempre ASCII.
  - **Parar sempre** ao ver um aviso da Meta (lista em 4.7) ou tela de login/código/termos: grava o arquivo de parada por função injetada e sai com código 3. **Nunca** toca nos botões proibidos de 4.7.
- **E2. `scripts/story_fluxos.py` — os fluxos (use `story_post_seletores.py` da rodada 1; os ids confirmados são os de 4.7):**
  - `trocar_conta(disp, handle)`: perfil → `action_bar_username_container` → toca o `@handle` na lista → **lê de volta** o `@` ativo; diferente do esperado → aborta. Nunca digita senha; tela de login → para (código 3).
  - `story_da_arte(disp, arte, figurinhas, destaque=None)`: arte na galeria (a mais recente) → editor → figurinhas (`asset_button`) → **link** (campo da URL; rótulo curto tipo "Ver post") e/ou **enquete** (`poll_sticker_v2_question` ≤ 25, opções, `done_button`) → **posiciona** a figurinha dentro da zona do `<arte>_zonas.json` (D) arrastando pelos `bounds` reais da figurinha → "Seu story" (`your_story_share_shortcut_button`) → espera o indicador de envio sumir. O post fica registrado **antes** do toque final ("1 story por post; nunca repete"; se algo falhar depois do toque, marca "a conferir").
  - `compartilhar_post_no_story(disp, link)`: abre o post (deep link `am start -a android.intent.action.VIEW -d <link> -p com.instagram.android`, ou a grade do perfil como plano B) → Enviar (`row_feed_button_share`) → "Add to story" → "Seu story" (é o fluxo que a rodada 1 já tem; adapte para o aparelho escolhido).
  - `adicionar_ao_destaque(disp, nome)`: abre o próprio story, confere que é o **de agora** pelo carimbo (**`reel_viewer_timestamp` real é `3m`/`1h`, não "agora"**: aceite `^\d+m$` com ≤ 5, `Now`, `Just now`, `agora`; e o `content-desc` `"<conta>'s story, N minutes ago"`) → `toolbar_highlights_button` ("Highlight") → escolhe o destaque pelo nome ou cria → confirma ("Added to"/"Adicionado").
  - `conferir_pela_api(get_json, ig_user_id, desde, tentativas=3, espera_s=20)`: `GET /{ig-user-id}/stories?fields=id,media_type,permalink,timestamp` (4.7) e devolve o story mais novo com `timestamp ≥ desde`; é a **prova** de que saiu. Falhou na conferência → "a conferir", nunca repete o toque.
  - Regras que continuam (do `LEIA_story_post.md` da rodada 1): 3 min entre dois stories (qualquer conta); ≤ 5 min por story; conta conferida depois da troca; `pesado.lock` respeitado (se pesado, não liga o aparelho e tenta na rodada seguinte); desliga o **emulador** sempre, mesmo em erro (celular real **não** é desligado); 3 falhas no mesmo post tiram o post da fila automática.
- **E3. `scripts/story_fila_v2.py` — a fila ganha `stories[]`** (compatível com a real de 4.7: os campos de hoje continuam valendo). Esquema v2 (validador + migrador da v1 + conversor do **lote de estáticos real**):

```json
{
 "post_id": "…", "conta": "hp.carros", "canal": "carros", "link": "https://www.instagram.com/p/…/",
 "publicado_em": "2026-09-30 23:03", "titulo": "…", "destaque": null, "criado_em": "2026-09-30 23:11",
 "stories": [
  {"quando": "2026-10-01 09:40", "tipo": "chamada_post|mais_sobre|interacao|enquete|contagem|compartilhar_post",
   "arte": "H:\\…\\story_chamada.jpg", "zonas": "H:\\…\\story_chamada_zonas.json", "texto": "…",
   "figurinha": {"tipo": "link|enquete|quiz|contagem|pergunta|null", "url": "https://…", "rotulo": "Ver post", "opcoes": ["…", "…"]},
   "pergunta_publico": "O que você faz?", "destaque": "Enquetes"}
 ]
}
```

  `pergunta_publico` é o texto que vai na figurinha de enquete/pergunta (limite configurável, padrão 25 para a enquete, vindo de A4). Conversor `de_lote_estaticos(lote)` transforma `stories[]` (`hora`, `arquivo`, `tema`) e `interativo` do lote real (4.5) em itens v2 (o tema `vídeo novo:` vira `compartilhar_post`; `comenta aí` vira `interacao`; `contagem N dias` vira `contagem`). Recusa item incompleto com o motivo.
- **E4. `scripts/story_coletar_telas.py` — a coleta assistida de telas reais** (para a **próxima** rodada ter dumps de verdade): roteiro passo a passo para leigo, que **só** roda `uiautomator dump` e `screencap` (**nenhum toque, nenhuma digitação**: o Antônio ou o Diretor navega no aparelho e dá ENTER a cada tela) e grava `H:\HypadoLocal\android\telas\coleta\<NN>_<nome>.xml` e `.png` com um índice `coleta.json`. Telas a coletar: perfil próprio, menu "+", galeria, editor de story, bandeja de figurinhas, busca "link", figurinha de link aberta, figurinha de enquete aberta, botão "Seu story", folha de envio do post (Send), seletor de destaque, lista de contas. **O roteiro nunca pede senha** e para ao ver tela de login.
- **Testes (sem aparelho):** `AdbFalso` que **reproduz dumps de fixture** (o real de 4.7 + XMLs sintéticos para as outras telas, **marcados `"sintetico": true` no nome do arquivo** para o PC trocar pelos de E4) e confere a **sequência de comandos `adb`**: nenhum toque em coordenada fixa (rode o mesmo fluxo em **duas telas** diferentes — 1080x2400 e 1080x2340 — com fixtures proporcionais e prove que os toques seguem os `bounds`); aborta com aviso da Meta (arquivo de parada gravado, código 3); celular bloqueado → código 4; conta errada → aborta; acento → troca e loga; carimbo `3m`; idempotência (post registrado antes do toque); intervalo e limite de 5 min com relógio injetado; seleção de aparelho (0, 1 e 2 dispositivos); ≥ 60 testes.
- **Pronto quando:** tudo acima, `--simular` imprime o roteiro completo de cada fluxo **sem chamar `adb`**, e o `ENTREGA.md` lista **cada seletor que ainda é palpite** e a tela de E4 que o confirma.

### F. Pesquisa de fontes do radar (você tem web)

**Objetivo:** ampliar e **verificar** as fontes do `radar_hp.py` (4.10) para GTA, Futebol, Filmes e Séries e Carros. As configs já têm o que a tabela de 4.10 mostra; falta **cobertura** (principalmente RSS de salas de imprensa e os canais de YouTube que ainda não estão) e **prova de que cada fonte vale**.

- **Futebol:** os **20 clubes da Série A de 2026** (confirme a lista na página oficial da CBF e cite) — canal oficial de YouTube de cada um que ainda não está na tabela de 4.10 —, a CBF, a CONMEBOL (Libertadores e Sul-Americana), o ge e os canais oficiais das seleções que a CBF/FIFA mantêm; feeds RSS/Atom das páginas de notícias oficiais dos clubes e da CBF quando existirem.
- **Filmes e Séries:** Netflix, Prime Video, HBO Max, Disney+, Paramount+ e Apple TV (Brasil), Warner, Marvel, Sony, Universal, Paramount Pictures, Lionsgate, A24, Pixar, Lucasfilm; Omelete e AdoroCinema (RSS ou, se não houver, o que a página oferece); salas de imprensa dos estúdios.
- **Carros:** as **28 montadoras** da rotina `hp-carros-lancamentos` — **BMW, Mercedes-Benz, Audi, Porsche, Volkswagen, Toyota, Honda, Hyundai, Kia, Chevrolet, Fiat, Jeep, Ram, Ford, Renault, Nissan, Peugeot, Citroën, BYD, GWM, Caoa Chery, Mitsubishi, Volvo, Land Rover, Ferrari, Lamborghini, McLaren, Tesla**: para cada uma, a **sala de imprensa** (global e a do Brasil quando houver) com **RSS/Atom** se existir; o canal de YouTube (global e Brasil) com `channel_id`. Faltam hoje no YouTube do radar, pelo menos: **Ram, Nissan, Peugeot, Citroën, Caoa Chery e Mitsubishi**. As salas de imprensa que o SKILL da rotina cita: `press.bmwgroup.com`, `group-media.mercedes-benz.com`, `audi-mediacenter.com`, `newsroom.porsche.com`, `volkswagen-newsroom.com`, `global.toyota/en/newsroom`, `media.stellantis.com` (Fiat, Jeep, Ram, Peugeot, Citroën), `media.ford.com`, `news.gm.com`, `hyundainews.com`, `kianewscenter.com`, `global.honda/en/newsroom`, `global.nissannews.com`, `media.renaultgroup.com`, `byd.com`, `gwm-global.com`, `volvocars.com/intl/media`, `media.jaguarlandrover.com`, `ferrari.com/en-EN/media`, `media.lamborghini.com`, `cars.mclaren.press`, `tesla.com`. Esses sites só servem para **achar o assunto**; os números sempre vêm da montadora.
- **GTA:** confirme o canal oficial da Rockstar e acrescente fontes novas **só se oficiais** (Newswire da Rockstar já tem coletor próprio; Take-Two em `take2games.com/ir`).
- **Formato da entrega:** para cada canal, um JSON `radar_fontes/<canal>_fontes_novas.json` **no formato de 4.10** (`rss`: `{nome, url, oficial, filtrar, peso}`; `youtube`: `{nome, url (@handle), channel_id, peso, oficial, video_reutilizavel, nota_uso?}`), **mais** um campo `"verificado_em"` e `"evidencia"` (URL da página oficial onde você achou o id/feed) em cada entrada. Regras: `oficial: true` só para canal/sala **da própria marca, clube, liga ou federação**; `video_reutilizavel: true` só para vídeo oficial que o clube, a CBF ou a liga publica (futebol: **com crédito e áudio original**) ou trailer/clipe oficial de estúdio (**sempre com comentário nosso, nunca trailer puro**); sites de notícia (`ge`, Omelete, Autoesporte…) são `oficial: false` e `video_reutilizavel: false`. **Nunca** inclua perfil de Flow Games.
- **Verificação (obrigatória):** `channel_id` só entra se `https://www.youtube.com/feeds/videos.xml?channel_id=<id>` responder 200 com um `<title>` que **bate com o nome do canal**; RSS/Atom só entra se responder 200, for XML válido e tiver pelo menos 1 item com data dos últimos 30 dias. O que **não** passou vai para uma lista `"descartadas"` com o motivo. **Não invente id nem URL:** sem prova, não entra.
- **Entregue também** `radar_fontes/verificar_fontes.py`: lê os JSONs e refaz a verificação (rede por `transporte` injetado; testes com respostas gravadas), para o PC repetir quando quiser. Testes ≥ 20 (parser de RSS e Atom, `<title>` do canal, data recente, descarte com motivo, regra `oficial`/`video_reutilizavel`).
- **`RELATORIO_FONTES.md`:** por canal, quantas fontes novas, quantas descartadas e por quê, e uma tabela montadora → sala de imprensa → RSS (sim/não) → canal YouTube.
- **Pronto quando:** os 3 JSONs novos (futebol, filmes, carros) + GTA se houver algo oficial novo; todas as entradas com evidência; o `verificar_fontes.py` e os testes; relatório com os números reais.

---

## 6. Ordem de trabalho, lotes e o que entregar no fim

**Ordem (no máximo 3 agentes ao mesmo tempo, nunca 2 workflows juntos):**

1. **Lote 1 (3 agentes):** **A** (adaptadores; é a que mais pesa e a que destrava a integração), **D** (artes de story) e **F** (pesquisa de fontes; é a que usa a web).
2. **Lote 2 (3 agentes):** **E** (story no celular; usa a paleta e as zonas de A5 e D), **B** (YouTube) e **C** (Facebook e comentários).
3. **Fechamento (1 agente, sozinho):** rodar a **suíte inteira** (a da rodada 1 + a nova) no mesmo ambiente, montar `ENTREGA.md`, `PATCHES.md` e `PENDENCIAS_PARA_O_DIRETOR.md`, conferir o formato da Seção 2 com um `desempacotar` seu (a mesma regra: cabeçalho `## caminho` + bloco) e **provar que desempacota sem arquivo "sem bloco" nem arquivo falso**.

Se faltar tempo ou limite de uso, **entregue na ordem A → E → D → F → B → C**, e diga no `ENTREGA.md` o que ficou de fora. Se aparecer "session limit", pare e escreva o que fez.

**Antes de entregar, confira (e marque no `ENTREGA.md`):**

- [ ] Nenhum arquivo importa `hp_studio.esteira` nem `hp_studio.metricas`.
- [ ] Nenhum teste faz rede, abre `adb`, lê `H:\HypadoLocal\segredos\` ou depende de relógio real.
- [ ] Nenhum valor `FAKE_NAO_E_TOKEN_*` aparece em saída, log, exceção ou arquivo gerado (há teste para isso).
- [ ] Todo `subprocess` do código de produção leva `creationflags=0x08000000` no Windows e o comando é uma **lista** (não string).
- [ ] Todo `open`/`read_text`/`write_text` tem `encoding="utf-8"`; gravação com `.tmp` + `os.replace`.
- [ ] Caminho do PC só em constante no topo do módulo (ou variável de ambiente), nunca espalhado; funciona com espaço no caminho.
- [ ] Nenhuma arte tem emoji; nenhuma mensagem do WhatsApp começa sem `*Claude - *`.
- [ ] Nenhum `## <arquivo>.<ext>` dentro do conteúdo de um arquivo; nenhum arquivo com nome de segredo.
- [ ] A suíte da rodada 1 continua verde e o número está no relatório (passed, failed, skipped, segundos).
- [ ] Cada suposição que sobrou está em "Suposições que sobraram" com arquivo e função.

**O que o `ENTREGA.md` precisa responder ao Diretor, sem enrolação** (3 linhas no topo): o que mudou, quantos testes (N passed, X segundos) e o que falta ou espera o Antônio.

**O que depende do Antônio e você deve deixar com passo a passo para leigo (≈ 50 passos se precisar):** (1) permissões de comentário da Meta, se faltarem; (2) a aprovação da auditoria da API do YouTube (já em andamento no PC); (3) rodar a coleta de telas reais do Instagram (tarefa E4) com o emulador ou o celular ligado; (4) decidir os conflitos de paleta (4.6) e a lista de palavras ofensivas (C2); (5) qualquer instalação de APK no celular (**não faça nada que dependa disso por padrão**).

Boa sorte. O Antônio quer o app o mais independente possível da IA, cada peça "com 100% de excelência, exatamente como o Claude faz". Tudo que você entregar entra em **modo sombra** e só vira produção depois de **7 dias de qualidade idêntica comprovada**.
