# story no celular por ADB — parte 1: o aparelho (`story_dispositivo.py`) e a fila v2 (`story_fila_v2.py`)

Rodada 2, tarefa E (E1 + E3). A parte 2 (fluxos `story_fluxos.py`, coleta de telas `story_coletar_telas.py`)
é do agente E2 e completa este arquivo.

## O que cada módulo faz, em uma frase

| Módulo | Para que serve |
|---|---|
| `scripts\story_dispositivo.py` | Tudo o que encosta no aparelho (emulador `hp_celular` ou celular real): escolher o aparelho, esperar ligar, ler o tamanho da tela, ver se está acesa e destravada, ler a tela (uiautomator), tocar no centro do botão, deslizar, apertar tecla, tirar foto, digitar (acento vira letra sem acento e fica no log), mandar a arte para a galeria e **parar** ao ver aviso da Meta, login, código ou termos. |
| `scripts\story_fila_v2.py` | O JSON da `fila_story` ganha a lista `stories[]` (esquema v2): valida, migra o pedido antigo (o real da §4.7), converte o lote de estáticos do dia em itens de story e lê o `<arte>_zonas.json` do `story_artes` convertendo para a tela do aparelho. |
| `scripts\testes\adb_falso.py` | O adb de mentira dos testes: responde com as telas de `tests\fixtures\android\` e anota todo comando. Também gera essas fixtures. |

Nada aqui instala nada, não faz login, não digita senha ou PIN e não toca em Entrar/Aceitar/Permitir.
**Só Python 3.11+ e a biblioteca padrão** (mais o `hpbase` do app, que os scripts acham sozinhos).

## Instalação (uma vez)

1. Copie `story_dispositivo.py`, `story_fila_v2.py` e `story_post_seletores.py` (já existe) para `G:\Meu Drive\Hypado\scripts\`.
2. Copie `testes\adb_falso.py`, `testes\test_story_dispositivo.py` e `testes\test_story_fila_v2.py` para `G:\Meu Drive\Hypado\scripts\testes\` e a pasta `tests\fixtures\android\` para o mesmo lugar do repositório (`tests\fixtures\android\`).
3. Rode os testes (não precisam de aparelho): `cd "G:\Meu Drive\Hypado\scripts"` e `python -m pytest -q testes\test_story_dispositivo.py testes\test_story_fila_v2.py`. Tem de terminar em `passed`.
4. O adb é achado nesta ordem: variável `HP_ADB`, `H:\HypadoLocal\android\sdk\platform-tools\adb.exe`, PATH.

## Como escolher o aparelho (emulador ou celular)

Com **um** aparelho ligado, o script usa ele. Com **dois** (emulador + celular no cabo) ou **nenhum**, ele recusa e lista o que viu. Para escolher:

- `--serial emulator-5554` (o serial aparece em `adb devices`; o do emulador é sempre `emulator-NNNN`);
- ou `--emulador` / `--celular` (preferência: "o emulador" ou "o que não é emulador");
- ou a variável de ambiente `HP_ANDROID_SERIAL`.

Celular real: ative "Depuração USB" nas opções do desenvolvedor e **aceite** o aviso "Permitir depuração USB?" na tela do celular (isso é um clique do Antônio; o script nunca toca em Permitir). Se `adb devices` mostrar `unauthorized`, é esse aviso que falta.

Diagnóstico rápido (código 0 = ok, 3 = aviso da rede, 4 = bloqueado / precisa do Antônio):

```
python scripts\story_dispositivo.py aparelhos
python scripts\story_dispositivo.py status --emulador
python scripts\story_dispositivo.py dump highlight --serial emulator-5554
python scripts\story_dispositivo.py foto H:\HypadoLocal\android\telas\tela.png
python scripts\story_dispositivo.py status --simular        (não chama o adb; mostra o roteiro)
```

## Regras que o aparelho segue sozinho

1. **Tela diferente = coordenada diferente.** Nunca há coordenada fixa: todo toque é no centro dos `bounds` do elemento lido no dump; frações da tela usam o `wm size` do aparelho (1080x2400 no emulador; outro no celular). Os testes rodam o mesmo fluxo em 1080x2400 e em 1080x2340 e provam que os toques mudam junto.
2. **Celular bloqueado = parar com código 4** e a mensagem `celular bloqueado: o Antônio desbloqueia`. O script acorda a tela e tira a tela de bloqueio **sem PIN**; se tiver PIN/padrão, não digita nada.
3. **Aviso da Meta, tela de login, pedido de código ou termos novos = parar com código 3**, gravando `H:\HypadoLocal\emulador\PARADO_AVISO_META.json` (só o Antônio apaga). Botão Entrar/Log in/Aceitar/Permitir/Concordo/Cadastre-se nunca é tocado (recusa + mesma parada).
4. **Acento e emoji.** O `adb shell input text` só digita ASCII. Modo padrão `sem_acento`: "Você" vira "Voce", "Não" vira "Nao", emoji some, e cada troca fica no log (`acento trocado: 'Você' -> 'Voce'`). Modo `acento_real`: **desligado**; só funciona com o teclado ADBKeyBoard, que o Antônio instala e ativa (veja abaixo). Sem ele, o script explica e não digita.
5. **Arte na galeria.** `adb push` para `/sdcard/Pictures/HP/<nome>` (nome sempre ASCII: "contagem ção.jpg" vira `contagem_cao.jpg`) e aviso ao MediaStore para a foto aparecer na galeria do Instagram: principal `content call … scan_file` (Android 10+), plano B o broadcast antigo `MEDIA_SCANNER_SCAN_FILE`, plano C `scan_volume`. Cada plano é conferido (`content query`); se nenhum funcionar, o script avisa e o Antônio confere no aparelho (anotado em `docs\rodada2\E1.md`).

## Se um dia quiser acento de verdade (modo `acento_real`) — passo a passo para o Antônio

Isso **não** está ligado e o script **não instala nada**. Só se o Antônio decidir:

1. Baixar o `ADBKeyboard.apk` (projeto `senzhk/ADBKeyBoard` no GitHub) e instalar: `adb install ADBKeyboard.apk`.
2. No aparelho: Configurações > Sistema > Idiomas e entrada > Teclado virtual > Gerenciar teclados > ligar **ADB Keyboard** e **aceitar** o aviso de segurança do Android (é um clique seu).
3. Selecionar como teclado padrão: `adb shell ime set com.android.adbkeyboard/.AdbIME` (ou pelo ícone de teclado na barra).
4. Depois de postar, voltar ao Gboard: `adb shell ime set com.google.android.inputmethod.latin/com.android.inputmethod.latin.LatinIME`.
5. Só então chamar `disp.digitar(texto, politica="acento_real")`. Com o teclado faltando, o script responde com esse passo a passo e código 4.

## A fila v2 (módulo story_fila_v2)

O pedido de hoje (`H:\HypadoLocal\emulador\fila_story\<post_id>.json`, gravado pelo `story_clicavel.py fila`) continua valendo. A v2 acrescenta `stories[]`:

```
{"quando": "2026-10-01 09:40", "tipo": "chamada_post", "arte": "H:\\...\\story_chamada.jpg",
 "zonas": "H:\\...\\story_chamada_zonas.json", "texto": "...",
 "figurinha": {"tipo": "link", "url": "https://...", "rotulo": "Ver post", "opcoes": null},
 "pergunta_publico": null, "destaque": null}
```

- `tipo`: `chamada_post`, `mais_sobre`, `interacao`, `enquete`, `contagem` ou `compartilhar_post` (este não precisa de arte; precisa do `link`).
- `figurinha.tipo`: `link` (precisa de `url`; rótulo padrão "Ver post"), `enquete`/`quiz` (2 a 4 `opcoes` de até 25 letras e `pergunta_publico` de até 25), `pergunta`, `contagem` (precisa de `data` AAAA-MM-DD) ou `null`.
- `quando`: hora de Brasília `AAAA-MM-DD HH:MM` (ISO com fuso também vale).

Comandos (código 0 = ok, 1 = recusado, com os motivos em português, um por linha):

```
python scripts\story_fila_v2.py validar H:\HypadoLocal\emulador\fila_story\<post_id>.json
python scripts\story_fila_v2.py migrar  <pedido_antigo.json> --saida <pedido_v2.json>
python scripts\story_fila_v2.py de-lote G:\Meu Drive\Hypado\lotes\2026-10-01_estaticos.json --limite 25
python scripts\story_fila_v2.py zonas   H:\HypadoLocal\stories\story_chamada.jpg --tela 1080x2400
```

`migrar` transforma o pedido real em v2 com **um** story `compartilhar_post` na hora de `publicado_em`.
`de-lote` lê o lote real do dia: tema `vídeo novo: X` vira `compartilhar_post` (o link do post do vídeo não está no lote: o item sai com `link: null` e a pendência anotada; o pedido só valida quando o link entrar), `comenta aí` vira `interacao`, `contagem N dias` vira `contagem` (data = dia do lote + N; 01/10 + 49 = 19/11/2026), e o `interativo` vira `enquete` com a pergunta encurtada pelo `story_post_lote.py` (`O que você faz?`). Item incompleto é **recusado com o motivo** — nada é inventado.
`zonas` converte o `<arte>_zonas.json` do `story_artes` para a tela do aparelho (fração × `wm size`): na tela 1080x2400 a zona do link (140,1500)-(940,1640) da arte vira (140,1875)-(940,2050).

## Arquivos

| Arquivo | Onde fica |
|---|---|
| `story_dispositivo.py`, `story_fila_v2.py` | `G:\Meu Drive\Hypado\scripts\` |
| `testes\adb_falso.py`, `testes\test_story_dispositivo.py`, `testes\test_story_fila_v2.py` | `G:\Meu Drive\Hypado\scripts\testes\` |
| `tests\fixtures\android\*.xml` (1 derivado do dump real + 13 telas sintéticas × 2 tamanhos) | repositório; "sintetico" no nome = inventada, o PC troca pelos dumps da coleta (E4) |
| Parada por aviso `PARADO_AVISO_META.json` | `H:\HypadoLocal\emulador\` |
| Arte no aparelho | `/sdcard/Pictures/HP/` |

---

# parte 2: os fluxos (`story_fluxos.py`) e a coleta de telas (`story_coletar_telas.py`)

Rodada 2, tarefa E (E2 + E4). Continua a parte 1 (aparelho e fila v2). Tudo aqui usa o `story_dispositivo.py`:
**nenhuma coordenada fixa** (todo toque é o centro do elemento lido no dump), **nenhuma senha**, **nenhum toque em
Entrar/Aceitar/Permitir**, e qualquer aviso da Meta / tela de login para tudo com código 3.

## O que cada módulo faz, em uma frase

| Módulo | Para que serve |
|---|---|
| `scripts\story_fluxos.py` | Os passos dentro do Instagram: trocar de conta (e conferir), story a partir de uma arte com figurinha de link / enquete / contagem posicionada na zona da arte, compartilhar um post no story, pôr o story de agora num destaque, conferir pela API que o story saiu, e rodar um pedido inteiro da fila v2 com as regras (3 min entre stories, 5 min por story, 1 story por post, 3 falhas tiram da fila, pesado.lock, desliga só o emulador). |
| `scripts\story_coletar_telas.py` | Roteiro assistido que SÓ lê a tela (dump + foto) para coletar as 12 telas reais do Instagram: quem navega é você, o script nunca toca em nada. Serve para trocar as telas sintéticas dos testes pelas reais e confirmar os ids que ainda são palpite. |

## Instalação (uma vez, além da parte 1)

1. Copie `story_fluxos.py` e `story_coletar_telas.py` para `G:\Meu Drive\Hypado\scripts\` (ao lado de `story_post.py`,
   `story_post_seletores.py`, `story_post_lote.py`, `story_dispositivo.py`, `story_fila_v2.py`).
2. Copie `testes\test_story_fluxos.py` e `testes\test_story_coletar_telas.py` para `scripts\testes\`.
3. Teste sem aparelho: `cd "G:\Meu Drive\Hypado\scripts"` e
   `python -m pytest -q testes\test_story_dispositivo.py testes\test_story_fila_v2.py testes\test_story_fluxos.py testes\test_story_coletar_telas.py testes\test_story_post.py`
   (tem de terminar em `passed`; nada aí liga emulador nem faz rede).

## Primeiro: veja o roteiro sem encostar no aparelho (`--simular`)

Cada comando aceita `--simular`: imprime passo a passo o que faria (cada linha `[simular] adb ...` é um comando que NÃO foi executado).

```
python scripts\story_fluxos.py trocar-conta hp.futebol --simular
python scripts\story_fluxos.py arte H:\HypadoLocal\stories\story_chamada.jpg --conta hp.carros --link https://www.instagram.com/p/XXXX/ --rotulo "Ver post" --simular
python scripts\story_fluxos.py arte H:\HypadoLocal\stories\story_enquete.jpg --conta hpgta6 --enquete "O que você faz?" --opcao Jogo --opcao Durmo --destaque Enquetes --simular
python scripts\story_fluxos.py compartilhar https://www.instagram.com/p/XXXX/ --conta hp.futebol --simular
python scripts\story_fluxos.py destaque Enquetes --conta hp.futebol --simular
python scripts\story_fluxos.py pedido H:\HypadoLocal\emulador\fila_story\<post_id>.json --simular
```

## Depois: de verdade (com o emulador ligado ou o celular no cabo)

Tire o `--simular`. Escolha o aparelho como na parte 1 (`--serial`, `--emulador`, `--celular` ou `HP_ANDROID_SERIAL`).
O comando `pedido` lê o JSON da `fila_story` (o antigo, de um campo `link`, é migrado sozinho para a v2) e roda todos
os `stories[]` dele, um a um, respeitando:

| Regra | O que acontece |
|---|---|
| `pesado.lock` ocupado | Não liga nada; sai com código 2 ("tento na próxima rodada"). O story é leve: ignora a janela 18h–22h30. |
| 3 min entre dois stories (qualquer conta) | Sai com código 2 dizendo quantos segundos faltam; com `--esperar-intervalo` ele espera. |
| 5 min por story | Passou disso, aborta o story (conta como falha) e vai para o próximo. |
| 1 story por post | O post é anotado em `H:\HypadoLocal\emulador\story_post_estado.json` ANTES do toque em "Seu story"; rodar de novo não repete (código 2). |
| Falhou depois do toque | Fica "a conferir": confira no Instagram; o script nunca toca de novo. |
| 3 falhas no mesmo post | Sai da fila automática (código 2) até alguém zerar `tentativas` no JSON de estado. |
| Conta | Troca pelo nome lá em cima do perfil, toca no @ na lista e LÊ de volta o @ ativo; diferente = aborta. |
| Aviso da Meta / login / código / termos | Para na hora (código 3) e grava `H:\HypadoLocal\emulador\PARADO_AVISO_META.json` (só o Antônio apaga). |
| Celular bloqueado, 2 aparelhos sem escolha | Código 4: o Antônio resolve (nunca digita PIN, nunca toca em Permitir). |
| Fim | Emulador é desligado SEMPRE (mesmo com erro). Celular real NUNCA é desligado. |

Códigos de saída: 0 ok · 1 erro · 2 bloqueado · 3 aviso da rede · 4 precisa do Antônio.

**Figurinhas e zonas.** O story a partir de arte usa o `<arte>_zonas.json` que o `story_artes.py` grava ao lado do JPG:
a figurinha (link ou enquete) é arrastada do lugar onde o Instagram a põe (lido no dump) até o centro da zona da arte,
convertida para a tela do aparelho. Pergunta de enquete com mais de 25 letras é encurtada pelo `story_post_lote.py`
sem cortar palavra; se não couber, o story é recusado antes de publicar (ninguém corta no escuro).

**Acento.** `adb shell input text` só digita ASCII: "Você" vira "Voce", "Não" vira "Nao", e cada troca fica no log
(`acento trocado: 'Você' -> 'Voce'`). O modo de acento real continua DESLIGADO (passo a passo na parte 1).

**Conferência pela API.** Quando o PC passa `get_json` (o `publicador_meta.api`) e o `ig_user_id` da conta
(`meta_tokens_meta.json -> contas["IG_<handle>"].id`), o script consulta
`GET https://graph.instagram.com/v21.0/<id>/stories?fields=id,media_type,permalink,timestamp` até 3 vezes (20 s entre
elas) e marca "publicado" se achar um story com `timestamp` depois do toque; se não achar, marca "a conferir" e NÃO
repete o toque. Este módulo nunca faz rede sozinho e não conhece token nenhum.

## Coleta de telas (E4) — passo a passo para leigo

Serve para a próxima rodada ter os dumps REAIS do Instagram (hoje só existe o do visualizador de story).
O script só lê a tela e tira foto: **você** navega no celular. Ele nunca pede senha e para sozinho se vir tela de login ou aviso.

1. Ligue o emulador (`H:\HypadoLocal\android\ligar_emulador.ps1`) ou plugue o celular (depuração USB aceita) e deixe
   o Instagram aberto na conta @hp.futebol (a que sabemos estar logada).
2. Para ver o roteiro antes: `python scripts\story_coletar_telas.py --simular`.
3. Rode de verdade: `python scripts\story_coletar_telas.py --emulador` (ou `--celular` / `--serial X`).
   Para gravar em outra pasta: `--pasta H:\HypadoLocal\android\telas\coleta`. Para repetir só uma tela: `--so 07`.
4. O script mostra a instrução da tela 1 ("Abra o perfil…"). Faça isso no celular e aperte **ENTER**. Ele grava
   `01_perfil_proprio.xml` e `01_perfil_proprio.png` e diz quais botões reconheceu.
5. Repita para as 12 telas: perfil próprio, menu "+", galeria, editor de story, bandeja de figurinhas, busca "link",
   figurinha de link aberta, figurinha de enquete aberta, botão "Seu story", folha de envio do post (Send), seletor de
   destaque, lista de contas. Não toque em "Seu story", não escolha destaque, não toque em "Adicionar conta".
   Escreva `pular` para pular uma tela e `sair` para terminar antes.
6. No fim, `coleta.json` lista cada arquivo e, por tela, quais ids/textos da lista de palpites apareceram
   (`confirmadas`) e quais não (`faltam`). Mande a pasta inteira para a próxima rodada: os arquivos
   `*_sintetico_*.xml` de `tests\fixtures\android\` são trocados por esses.

Se aparecer "PAREI …": a tela mostrava login, pedido de código, termos ou aviso da Meta. O script gravou
`PARADO_AVISO_META.json` (só o Antônio apaga, depois de olhar o aparelho) e não tocou em nada.

## Arquivos

| Arquivo | Onde fica |
|---|---|
| `story_fluxos.py`, `story_coletar_telas.py` | `G:\Meu Drive\Hypado\scripts\` |
| `testes\test_story_fluxos.py`, `testes\test_story_coletar_telas.py` | `G:\Meu Drive\Hypado\scripts\testes\` |
| Estado (1 story por post, intervalo, tentativas) | `H:\HypadoLocal\emulador\story_post_estado.json` (o mesmo da rodada 1) |
| Telas coletadas | `H:\HypadoLocal\android\telas\coleta\NN_nome.xml/.png` + `coleta.json` |
