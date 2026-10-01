# story_post.py: story clicável pelo emulador (app oficial do Instagram)

Ticket: `20260930-124527-emulador-android…` (módulo F do HP Studio).

## O que ele faz, em uma frase por comando

| Comando | O que faz |
|---|---|
| `fila` | Pega cada post da `H:\HypadoLocal\emulador\fila_story\` que **já foi publicado** e ainda não tem story. Para cada um: liga o emulador, abre o Instagram, troca para a conta certa, abre o post, Enviar → Adicionar ao story → Seu story, põe no destaque (se o JSON pedir), avisa o `story_clicavel.py feito` e, no fim, desliga o emulador. |
| `fila --uma-vez` | O mesmo, mas faz no máximo 1 story e sai. |
| `post <post_id>` | Faz o story de um post só (o arquivo `fila_story\<post_id>.json`). |
| `enquete --dia 2026-09-30` | Story interativo das 16h do GTA: manda a arte para a galeria do emulador, cria o story com a figurinha de enquete (pergunta + opções), arrasta a figurinha para a caixa da arte, publica e põe no destaque "Enquetes". `--dia hoje` também vale. |
| `contagem` | Story com a figurinha de contagem regressiva do lançamento do GTA 6 (19/11/2026). |
| `status` | Mostra se está PARADO, quando foi o último story, quanto falta para o próximo e o que está na fila. |
| `config` | Cria o arquivo de configuração com os valores padrão. |
| `--simular` (em qualquer comando) | **Não encosta no emulador.** Só imprime o roteiro do que faria. |

## Regras que ele segue sozinho (não dá para desligar)

1. **Parar ao primeiro aviso da Meta.** Se a tela mostrar "Tente novamente mais tarde", "Try Again Later", "Ação bloqueada", "Action Blocked", "We restrict certain activity", "Restringimos", "suspeita", CAPTCHA, "confirme que é você", tela de login, pedido de código ou termos novos, ele para na hora, desliga o emulador e grava
   `H:\HypadoLocal\emulador\PARADO_AVISO_META.json` (com a frase, o passo, a conta e a imagem da tela em `emulador\avisos\`).
   **Enquanto esse arquivo existir, nenhum story sai.** Só o Antônio apaga.
   Para não parar por engano: as palavras soltas ("suspeita", "suspicious", "captcha", "restringimos") só contam no texto visível da tela, fora de legenda, comentário, grade e fotos (a descrição automática de uma foto de notícia pode ter "SUSPEITA"). As frases completas ("Tente novamente mais tarde", "Action Blocked"…) contam em qualquer lugar. A lista está no `story_post_seletores.py`, e dá para acrescentar frases pela chave `"avisos_meta_extra"` do config.
2. **Nunca digita senha nem código, nunca toca em Entrar/Login/Aceitar/Concordo/Permitir/Termos.** Se for tocar num botão desses, ele para (e grava o arquivo de parada).
3. **1 story por post.** O post fica registrado **antes** do toque em "Seu story". Se algo der errado depois do toque, ele nunca repete (marca "a conferir").
4. **Sem rajada.** Mínimo de 3 min entre dois stories (qualquer conta). Ajuste em `intervalo_min_seg`.
5. **No máximo 5 min por story** (inclui ligar o emulador). Estourou: aborta, registra a falha e desliga.
6. **Desliga o emulador sempre**, mesmo em erro.
7. **Pode sair a qualquer hora** (story é leve). Mesmo assim, respeita o `pesado.lock`: se um trabalho pesado estiver rodando, ele não liga o emulador e tenta na próxima rodada.
8. **Conta conferida.** Depois de trocar de conta, ele lê o @ que ficou ativo. Se não for o esperado, aborta. Também confere se o post aberto é da conta certa.
9. **Story de divulgação só depois do post.** Item com `publicado_em` no futuro fica esperando.
10. Depois de 3 falhas no mesmo post, ele tira o post da fila automática (fica em `status`).

## Arquivos

| Arquivo | Onde fica no PC |
|---|---|
| `story_post.py` | `G:\Meu Drive\Hypado\scripts\` |
| `story_post_seletores.py` (nomes dos botões do Instagram) | `G:\Meu Drive\Hypado\scripts\` |
| `testes\test_story_post.py` | `G:\Meu Drive\Hypado\scripts\testes\` |
| Configuração (`story_post_config.json`) | `H:\HypadoLocal\emulador\` |
| Estado (último story, posts feitos, falhas) `story_post_estado.json` | `H:\HypadoLocal\emulador\` |
| Histórico em texto `story_post_historico.log` | `H:\HypadoLocal\emulador\` |
| Parada por aviso `PARADO_AVISO_META.json` + `avisos\` | `H:\HypadoLocal\emulador\` |
| Tela do último erro (XML para conferir com o ui.py) | `H:\HypadoLocal\emulador\story_post_erros\` |
| Log detalhado | `H:\HypadoLocal\app\logs\story_post_<dia>.log` |

Usa a base `hpbase` do app (`G:\Meu Drive\Hypado\06 Projeto\app\hp_studio_nuvem\hpbase`). Ele acha sozinho. Se mudar de lugar, defina a variável `HP_APP` com o caminho da pasta `hp_studio`.
**Não precisa instalar nada com pip** (só Python 3.12 e a biblioteca padrão).

## Instalação, passo a passo (uma vez só)

1. Copie `story_post.py` e `story_post_seletores.py` para `G:\Meu Drive\Hypado\scripts\`.
2. Copie `test_story_post.py` para `G:\Meu Drive\Hypado\scripts\testes\`.
3. Abra o PowerShell e vá até a pasta da Hypado:
   `cd "G:\Meu Drive\Hypado"`
4. Crie a configuração:
   `python scripts\story_post.py config`
   Ele mostra onde criou o arquivo (`H:\HypadoLocal\emulador\story_post_config.json`).
5. Abra esse arquivo no Bloco de Notas e confira a parte `"contas"` (canal → @ de cada um dos 6 perfis):
   `gta → hpgta6`, `futebol → hp.futebol`, `filmes → hp.filmes`, `receitas → hp.receitas`, `carros → hp.carros`, `destinos → hp.destinos`. Salve.
6. Confira o adb. O script procura, nesta ordem: a variável `HP_ADB`, a chave `"adb"` do config, `H:\HypadoLocal\android\sdk\platform-tools\adb.exe` e o PATH. Se nenhum servir, coloque no config:
   `"adb": "H:\\HypadoLocal\\android\\sdk\\platform-tools\\adb.exe"` (no JSON a barra é dupla).
7. **No emulador, à mão, uma vez (o Antônio):**
   1. Ligue com `H:\HypadoLocal\android\ligar_emulador.ps1`.
   2. No Instagram, deixe as 6 contas logadas (a troca de conta só funciona com as 6 na lista). O script **nunca** faz login.
   3. Em cada conta, faça 1 story à mão (qualquer um, pode apagar depois). Isso tira da frente os avisos de "primeira vez" (Facebook, dicas…).
   4. Na primeira vez que abrir a galeria pelo story, o Android pede permissão de fotos: **toque em Permitir à mão**. O script não toca em "Permitir".
   5. Crie os destaques que vão ser usados (ex.: "Enquetes", "GTA 6"). O script só escolhe destaque que já existe; se não existir, o story sai e só o destaque falha (fica no log).
   6. Desligue com `desligar_emulador.ps1`.
8. **Conferir os nomes dos botões** (veja a tabela "Resource-ids a confirmar" mais abaixo). Isso é obrigatório antes de ligar o modo real.
9. Rode os testes (não precisam do emulador):
   `cd "G:\Meu Drive\Hypado\06 Projeto\app"`
   `python -m pytest -q "..\..\scripts\testes\test_story_post.py"`
   Tem que terminar com `passed` e sem `failed`.

## Modo sombra (7 dias, antes de assumir)

1. Todo dia, quando o Claude fizer um story à mão, rode o simulado do mesmo post:
   `python scripts\story_post.py post <post_id> --simular`
2. Compare o roteiro impresso (conta, link, botões, destaque) com o que foi feito à mão.
3. Rode também `python scripts\story_post.py fila --simular` para ver quais posts ele pegaria.
4. Depois de 7 dias iguais, faça **um story real assistido** com o emulador aberto na tela:
   `python scripts\story_post.py post <post_id>`
   e confira no Instagram (conta certa, story clicável, destaque certo).
5. Só então ponha no Agendador de Tarefas (abaixo).

## Uso no dia a dia

```powershell
cd "G:\Meu Drive\Hypado"
python scripts\story_post.py status                       # como está
python scripts\story_post.py fila --simular               # o que faria
python scripts\story_post.py fila                         # faz todos os pendentes (3 min entre eles)
python scripts\story_post.py fila --uma-vez               # faz no máximo 1
python scripts\story_post.py post 2026-09-30_gta_trailer  # um post específico
python scripts\story_post.py enquete --dia hoje           # enquete das 16h do GTA
python scripts\story_post.py contagem --arte "H:\HypadoLocal\canais\gta\contagem.png"
```

Códigos de saída (para rotinas): `0` ok · `1` erro · `2` bloqueado (parado, intervalo, trava, já feito) · `3` parou por aviso da Meta.

### No Agendador de Tarefas (sem janela preta)

Programa: `%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe`
Iniciar em: `G:\Meu Drive\Hypado`

| Tarefa | Argumentos | Quando |
|---|---|---|
| Stories da fila | `"G:\Meu Drive\Hypado\scripts\story_post.py" fila` | a cada 15 min |
| Enquete do GTA | `"G:\Meu Drive\Hypado\scripts\story_post.py" enquete --dia hoje` | todo dia 16:00 |
| Contagem regressiva | `"G:\Meu Drive\Hypado\scripts\story_post.py" contagem` | quando o Antônio decidir (precisa de arte, veja abaixo) |

Duas rodadas ao mesmo tempo não acontecem: a segunda encontra o `pesado.lock` e sai sem fazer nada.

## Formato dos arquivos que ele lê

**Fila** (`H:\HypadoLocal\emulador\fila_story\<post_id>.json`, feito pelo `story_clicavel.py`/`fila_story_com_post.py`):
```json
{"post_id": "2026-09-30_gta_trailer", "conta": "hpgta6", "canal": "gta",
 "link": "https://www.instagram.com/p/XXXX/", "publicado_em": "2026-09-30T18:30:00-03:00",
 "titulo": "Trailer 3", "destaque": "GTA 6"}
```
- A conta sai do `canal` (pelo mapa do config) e/ou do `conta`. Se os dois disserem contas diferentes, ele não faz.
- `destaque` vazio = sem destaque.
- Item com `"feito": true` ou `"status": "feito"` é ignorado (o script também guarda os feitos no estado).
- O link tem que começar com `https://www.instagram.com/` (ou `https://instagram.com/`).

**Enquete** (SUPOSIÇÃO DE FORMATO, confirmar com quem gera o lote): `lotes\<dia>_estaticos.json`, procurado em `G:\Meu Drive\Hypado\lotes\` e depois em `H:\HypadoLocal\lotes\` (outras pastas: chave `"pastas_lotes"` do config). Pode ser uma lista de itens ou `{"itens": [...]}` (também aceita `items`, `estaticos`, `posts`). Ele usa o **primeiro item com `"tipo": "story_enquete"`**:
```json
{"tipo": "story_enquete", "arquivo": "arte_enquete_0930.png",
 "pergunta": "Vai comprar no 1º dia?", "opcoes": ["Sim", "Não"],
 "caixa_enquete": [540, 1500], "canal": "gta", "destaque": "Enquetes"}
```
- `arquivo`: caminho completo, ou relativo à pasta do JSON (ou à raiz do Drive/HypadoLocal).
- `pergunta`: **no máximo 25 caracteres**. Passou: ele **não faz** e explica. Com `--cortar` (ou `"cortar_pergunta": true` no config) ele corta na última palavra que cabe.
- `opcoes`: 2 a 4, cada uma com no máximo 25 caracteres.
- `caixa_enquete`: **onde soltar a figurinha, em pixels da TELA do emulador** (não da arte). Número com ponto entre 0 e 1 vale como fração da tela: `[0.5, 0.7]` = meio da largura, 70% da altura. Se o item não tiver, vale o `"caixa_enquete"` do config. Para medir: abra a arte no story à mão, veja onde fica a caixa e use o `ui.py`/print da tela para ler as coordenadas.
- 1 enquete por dia (a segunda do mesmo dia é bloqueada).

**Contagem**: a arte vem de `--arte`, ou de um item `"tipo": "story_contagem"` no lote do dia (`arquivo`, `titulo`, `data`, `caixa`, `destaque`), ou de `"contagem": {"arte": ...}` no config. Título padrão "Lançamento do GTA 6" (até 30 caracteres, a confirmar), data padrão 2026-11-19, conta do canal `gta`, sem destaque (ajuste em `contagem.destaque`). 1 por dia.

## Resource-ids a confirmar no emulador (ANTES do modo real)

Como conferir cada um:
1. Ligue o emulador e abra o Instagram na tela indicada.
2. Rode `python H:\HypadoLocal\android\ui.py` (lista os elementos da tela com resource-id e texto).
3. Procure o botão. O resource-id é a parte depois de `com.instagram.android:id/`.
4. Se for diferente do padrão, **não mexa no código**: ponha no `story_post_config.json`:
   ```json
   "seletores": {"ids": {"criar": ["o_id_que_apareceu"]},
                 "textos": {"menu_story": ["Story"]}}
   ```
5. Depois de um erro real, o XML da tela fica em `H:\HypadoLocal\emulador\story_post_erros\`. Abra no Bloco de Notas e procure `resource-id`.

**Já vistos no emulador (vieram do ticket), só reconferir:** `action_bar_username_container`, `row_feed_button_share`, `your_story_share_shortcut_button`, `reel_viewer_timestamp`, `toolbar_highlights_button`, `asset_button`, `poll_sticker_v2_question`, `done_button`.

**Palpites que PRECISAM ser confirmados:**

| Chave (config) | Padrão (alternativas) | Tela onde conferir | Se não achar |
|---|---|---|---|
| `aba_perfil` | `profile_tab` | qualquer tela com as abas de baixo | nada anda (é o 1º passo) |
| `conta_titulo` | `action_bar_large_title_auto_size`, `action_bar_title`, `action_bar_textview_title` | perfil (o @ lá em cima) | ele também lê o texto dentro do `action_bar_username_container` |
| `autor_post` | `row_feed_photo_profile_name` | post aberto (nome do autor) | pula a conferência do autor |
| `avatar_perfil` | `row_profile_header_imageview` | perfil (foto redonda) | destaque falha (o story já saiu) |
| `grade_item` | `image_button`, `grid_card_layout_container` | perfil (quadradinhos) | plano B da grade falha |
| `criar` | `creation_tab`, `action_bar_new_post_button`, `action_bar_create_button` (ou descrição "Criar"/"Create") | perfil, botão "+" | enquete/contagem não saem |
| texto `menu_story` | "Story" | menu do "+" | idem |
| `galeria` | `gallery_preview_button`, `camera_gallery_button` (ou descrição "Galeria") | câmera do story | idem |
| `galeria_item` | `gallery_grid_item_thumbnail`, `media_picker_grid_item` | galeria do story | idem (conferir também que a 1ª miniatura é a foto mais nova, e não um atalho de câmera) |
| `busca_figurinha` | `row_search_edit_text`, `search_edit_text` | bandeja de figurinhas | só é usado se a figurinha não estiver à vista |
| textos `figurinha_enquete` / `figurinha_contagem` | contém "enquete"/"poll" e "contagem regressiva"/"countdown" (texto ou descrição) | bandeja de figurinhas | idem |
| `enquete_opcao` | `poll_sticker_v2_option_text` (plano B: os campos de texto abaixo da pergunta) | editor da enquete | confira se o plano B acha 2 campos |
| texto `enquete_add_opcao` | "Adicionar opção" | editor da enquete | só para 3 ou 4 opções |
| `contagem_titulo` | `countdown_sticker_title` | editor da contagem | contagem não sai |
| `contagem_dia_inteiro` | `countdown_sticker_all_day_switch` | editor da contagem | pula (fica com hora) |
| `contagem_data` | `countdown_sticker_end_date` (ou texto "Definir data…") | editor da contagem | contagem não sai |
| `data_proximo_mes` / `data_ok` | `android:id/next` / `android:id/button1` | calendário que abre ao tocar na data | contagem não sai |
| texto do dia no calendário | descrição "19 de novembro de 2026" (ou "19 November 2026") | calendário | contagem não sai |
| texto `add_story` | "Adicionar ao story" / "Add to story" | folha do Enviar | story não sai |
| texto `enviando` | "Publicando", "Posting"… | logo depois de publicar | ele segue depois de 60 s |
| texto `destaque_ok` | "Adicionado"/"Added to" | depois de tocar no destaque | só avisa no log |
| `IDS_CONTEUDO_IGNORAR_AVISO` (no `story_post_seletores.py`) | `row_feed_comment_textview_layout`, `row_feed_textview_comments`, `row_feed_photo_imageview`, `carousel_image`, `image_button` | feed e post aberto (legenda, comentários, foto), perfil (grade) | uma legenda com "suspeita" pararia tudo (falso alarme, lado seguro) |

Conferir também no emulador:
- **Posição do toque para passar o story** (`toque_avancar`, padrão 92% da largura e 30% da altura): tem que cair fora da figurinha do post.
- **Arrasto da figurinha** (`origem_adesivo` = meio da tela, `arrastar_modo` "swipe" 1,2 s): se o arrasto trocar o filtro da foto em vez de mover a figurinha, troque para `"arrastar_modo": "draganddrop"`.
- Se o `uiautomator dump` falhar muito no visualizador de story (vídeo tocando), o destaque falha, mas o story já saiu e é marcado como feito.

## Suposições (confirmar no PC)

1. **`ligar_emulador.ps1`**: pode esperar o boot ou só abrir o emulador e voltar. O script aguenta os dois casos: espera o `.ps1` por até 150 s e depois pergunta `sys.boot_completed` até dar 1 (até 180 s, dentro dos 5 min). Se o emulador **já estiver ligado**, ele usa assim mesmo (e desliga no fim).
2. **`digitar.py`**: supus que é chamado como `python digitar.py "texto"` e digita no campo que está em foco. Texto só com letras sem acento, números e `.,!?:-` vai direto pelo `adb shell input text`; o resto vai pelo `digitar.py`. Se a chamada for outra, ajuste `"digitar_cmd"` no config, ex.: `["{python}", "{script}", "--texto", "{texto}"]`.
3. **`story_clicavel.py feito <post_id> --link <url>`**: roda com o mesmo Python, a partir de `G:\Meu Drive\Hypado`, e o `--link` é o link do post (o mesmo da fila). Se o `feito` falhar, o story não é repetido: na próxima `fila` ele tenta **só o feito** de novo.
4. **Fila**: considero pendente todo `.json` direto na `fila_story\` (subpastas são ignoradas).
5. **Galeria**: a arte vai para `/sdcard/Pictures/hp_<tipo>_<data_hora>.png`. Antes de abrir a galeria ele espera a arte aparecer no MediaStore (`content query`). Em Android muito novo, se o `MEDIA_SCANNER_SCAN_FILE` não funcionar, a espera estoura em 20 s e o story não sai (fica no log).
6. **Animações**: depois do boot ele zera `window_animation_scale` e `transition_animation_scale` (o dump fica mais estável). O `animator_duration_scale` fica como está, para não acelerar o story.

## Quando aparece "PARADO por aviso da Meta"

1. Rode `python scripts\story_post.py status` e veja o motivo.
2. Abra `H:\HypadoLocal\emulador\PARADO_AVISO_META.json` (motivo, conta, passo) e a imagem em `H:\HypadoLocal\emulador\avisos\`.
3. Ligue o emulador à mão, abra o Instagram na conta indicada e leia o aviso. **Nada de digitar código ou senha pelo script.** Resolva à mão, sem pressa (se for bloqueio de ação, espere pelo menos 24 h).
4. Só então **apague** `PARADO_AVISO_META.json`. Na próxima rodada, os stories voltam a sair.

## Erros comuns

| Mensagem | O que fazer |
|---|---|
| `não achei o adb.exe` | Passo 6 da instalação. |
| `não achei ...ligar_emulador.ps1` | Confira `H:\HypadoLocal\android\` ou a chave `"android"` do config. |
| `o emulador não terminou o boot a tempo` | Ligue à mão uma vez e veja se abre. Feche emulador travado no Gerenciador de Tarefas. |
| `@x não aparece na lista de contas` | Faça login nessa conta no emulador (à mão). |
| `conta ativa é @y, esperado @x` | A troca caiu na conta errada. Ele abortou sem postar. Veja `conta_titulo`. |
| `não apareceu: id=...` | Um botão mudou. Veja o XML em `story_post_erros\` e ajuste em `"seletores"`. |
| `orçamento de 300s estourado` | Emulador lento ou botão sumido. Tenta de novo na próxima rodada (máx. 3). |
| `a pergunta tem N caracteres (máximo 25)` | Encurte no lote ou use `--cortar`. |
| `intervalo mínimo entre stories: faltam Ns` | Normal. Sai na próxima rodada. |
| `outro trabalho pesado está rodando` | Normal. Sai na próxima rodada. |
| `a conferir: tocou em 'Seu story' mas não confirmou` | Olhe no Instagram se o story saiu. Ele não repete sozinho. |

## Integração com o HP Studio

Gancho para o motor: `story_post.executar(trabalho: dict) -> dict`, com
`{"modo": "fila", "uma_vez": true}`, `{"modo": "post", "post_id": "..."}`,
`{"modo": "enquete", "dia": "2026-09-30"}` ou `{"modo": "contagem"}` (qualquer um com `"simular": true` para o modo sombra).
Devolve `{"ok": bool, "codigo": 0|1|2|3, "mensagem": str, "resultados": [...]}`.

## Testes (sem emulador)

```powershell
cd "G:\Meu Drive\Hypado\06 Projeto\app"
python -m pytest -q "..\..\scripts\testes\test_story_post.py"
```
(No repositório da nuvem: `cd app && python -m pytest -q ../scripts/testes/test_story_post.py`.)
O arquivo de teste se vira sozinho: põe `scripts` e `hp_studio` no caminho do Python e usa pastas temporárias no lugar do `H:` e do `G:`. O `conftest.py` do `app\` **não é carregado** quando o teste está fora de `app\`.
Os testes usam um "Instagram falso" que responde aos comandos do adb com telas em XML do uiautomator e cobrem: leitura do XML e centro dos botões, troca de conta certa/errada, fluxo completo com a sequência exata de comandos, aviso da Meta criando o arquivo de parada, arquivo de parada bloqueando tudo, intervalo mínimo, 1 story por post, emulador sempre desligado em erro, orçamento de 5 min, pergunta com mais de 25 caracteres, `story_clicavel.py feito` com os argumentos certos, enquete e contagem completas e o `--simular` sem nenhum comando real.
