# whatsapp_local — enviador local de WhatsApp (ticket P0)

Uma janela própria do **WhatsApp Web** (a página oficial `web.whatsapp.com`),
aberta pelo Playwright com um **perfil separado** (`H:\HypadoLocal\whatsapp_perfil`),
que lê a fila `H:\HypadoLocal\whatsapp_fila\` e envia sozinha, sem gastar token.
Também monta o aviso **"no ar"** e os **resumos** sem o Claude, e salva em arquivo
as mensagens novas do Antônio nos grupos HP (não responde nada).

**Começa em modo sombra**: só monta o texto e compara com o que o plantão mandou.
Nesse modo o navegador nem abre.

## Regras que o código garante (não dá para desligar)

| Regra | Como |
|---|---|
| WhatsApp só para 3 coisas | `tipo` tem que ser `resumo_dia`, `no_ar` ou `resumo_sabado`; outro → `rejeitadas\` |
| Toda mensagem começa com `*Claude - *` | exatamente (nem espaço antes); senão → `rejeitadas\` |
| Só grupos "HP \| Comissão 🚀" e lista "HP \| Grupos" | `grupos_permitidos.json`; nome com cara de telefone é barrado mesmo se estiver na lista |
| Conferir o cabeçalho antes de enviar | abre a conversa pela busca, lê o título do topo e compara exato (Unicode NFC) com o grupo; também confere que não é contato individual; na dúvida **não envia**. Confere de novo logo antes de clicar em Enviar |
| Nunca em primeiro plano | janela em `-32000,-32000` + minimizada, som mudo, nunca é trazida para frente (só o `login` abre visível, para o QR) |
| Volume baixo | mínimo 20 s entre mensagens (nem a config baixa disso) e teto por hora (`max_por_hora`, padrão 10) |
| Não duplicar | id repetido é rejeitado; na retentativa, olha a conversa antes de reenviar |
| Segurança | o código **nunca digita login**, senha ou código; só o Antônio escaneia o QR. Nada de Baileys, whatsapp-web.js ou parecidos: só o navegador na página oficial |
| Privacidade | o log (`H:\HypadoLocal\app\logs\whatsapp_<dia>.log`) nunca tem texto de mensagem: só id, tamanho e hash |

## Pastas

```
H:\HypadoLocal\
  whatsapp_perfil\            login do WhatsApp Web (não mexa, não copie)
  whatsapp_fila\              1 JSON por mensagem a enviar
    rejeitadas\  enviadas\  erros\
  whatsapp_local\
    config.json               modo sombra/real, ritmo, navegador...
    grupos_permitidos.json    a lista "HP | Grupos" (o Antônio mantém)
    estado.json  ritmo.json   controle interno
    recebidas\AAAA-MM-DD.jsonl   mensagens novas do Antônio
  whatsapp_sombra\
    app\  plantao\  relatorios\
G:\Meu Drive\Hypado\06 Projeto\AVISO.md   texto-modelo do aviso "no ar"
```

## Instalação passo a passo (PC do Antônio, Windows 11)

1. Abra o **PowerShell** (menu Iniciar → digite `PowerShell` → Enter).
2. Instale o Playwright (a biblioteca que controla o navegador):
   ```powershell
   & "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m pip install playwright
   ```
3. Escolha o navegador (**um** dos dois):
   - **A (recomendado) — usar o Google Chrome que já está instalado.** Não baixa
     nada. No passo 6 você coloca `"canal_navegador": "chrome"` no `config.json`.
   - **B — baixar o Chromium do Playwright no H:** (nada no C:):
     ```powershell
     setx PLAYWRIGHT_BROWSERS_PATH "H:\HypadoLocal\ferramentas\ms-playwright"
     ```
     Feche e abra o PowerShell de novo e rode:
     ```powershell
     & "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m playwright install chromium
     ```
4. Entre na pasta do app:
   ```powershell
   cd "G:\Meu Drive\Hypado\06 Projeto\app\hp_studio"
   ```
5. Rode o status (cria as pastas e os arquivos de exemplo):
   ```powershell
   & "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m whatsapp_local status
   ```
   Deve aparecer `Modo: sombra` e `Playwright: instalado`.
6. Abra `H:\HypadoLocal\whatsapp_local\config.json` no Bloco de Notas. Se escolheu a
   opção A, troque `"canal_navegador": null` por `"canal_navegador": "chrome"`. Salve.
7. Abra `H:\HypadoLocal\whatsapp_local\grupos_permitidos.json` e escreva os nomes
   **exatos** dos grupos da lista "HP | Grupos" (copie do topo da conversa, com
   emoji), por exemplo:
   ```json
   {"grupos": ["HP | GTA 6", "HP | Futebol ⚽"]}
   ```
   "HP | Comissão 🚀" já é permitido sempre. **Nunca** ponha contato individual.
8. Texto-modelo do aviso: se ainda não existe `G:\Meu Drive\Hypado\06 Projeto\AVISO.md`,
   copie o `AVISO.md` desta pasta para lá. Se já existe um, acrescente no fim dele
   o bloco entre `<!-- MODELO_WHATSAPP -->` e `<!-- FIM_MODELO -->` (veja o exemplo).
   Os marcadores (`{canal}`, `{titulo}`, `{horario}`, `{data}`, `{links}`, `{redes}`,
   `{link}`, `{link_instagram}`…) estão explicados no próprio `AVISO.md`.

## Login por QR (1 vez só)

1. No PowerShell, na pasta do passo 4:
   ```powershell
   & "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m whatsapp_local login
   ```
2. Abre uma janela **visível** do WhatsApp Web com o QR.
3. No celular: **WhatsApp → Configurações** (no Android, os 3 pontinhos) →
   **Aparelhos conectados → Conectar um aparelho** → aponte a câmera para o QR.
4. Espere a lista de conversas aparecer; o comando espera mais uns segundos (para
   o WhatsApp gravar a sessão) e fecha a janela sozinho. Aparece `Login OK`.
5. Pronto: o login fica guardado em `H:\HypadoLocal\whatsapp_perfil`. Se um dia o
   WhatsApp desconectar, o `status` mostra `PRECISA LOGIN` (e o `enviar` sai com
   código 2): é só repetir estes passos. O programa nunca digita nada de login.

## Modo sombra (os 7 dias obrigatórios)

- É o padrão (`"modo": "sombra"` no `config.json`). O enviador valida a fila e,
  em vez de enviar, move cada mensagem válida para `whatsapp_sombra\app\`.
- **O plantão (Claude) continua mandando como hoje** e, a cada mensagem enviada,
  grava uma cópia em `H:\HypadoLocal\whatsapp_sombra\plantao\`, 1 arquivo por
  mensagem, por exemplo `20260930-1832_no_ar.json`:
  ```json
  {"grupo": "HP | Comissão 🚀", "tipo": "no_ar",
   "texto": "*Claude - * 🚀 No ar agora — GTA 6 | HP ...",
   "enviado_em": "2026-09-30T18:32:00-03:00"}
  ```
  (também vale `.jsonl`, ou `.txt`/`.md` só com o texto).
- A cada ciclo o app refaz `whatsapp_sombra\relatorios\AAAA-MM-DD.md` (legível:
  tabela com % de similaridade, veredito e o diff de cada par) e `.json` (números).
  Na mão: `python -m whatsapp_local relatorio-sombra --dia 2026-09-30`.
- Sugestão de critério para ligar o real: **7 dias seguidos** com todos os pares
  "idêntico" ou "quase igual" (≥ 90 %, média ≥ 95 %) e nenhum item em "o plantão
  mandou e o app não montou". Quem decide é o Antônio.

## Passar para o modo real

1. Rode um teste com 1 mensagem para a Comissão (crie o arquivo na fila, veja o
   formato abaixo) e mande na mão, olhando o resultado:
   ```powershell
   python -m whatsapp_local enviar --uma-vez --real
   python -m whatsapp_local status
   ```
2. Deu certo → no `config.json` troque `"modo": "sombra"` por `"modo": "real"`. O vigia
   lê a config a cada ciclo (não precisa reiniciar).
3. Voltar para sombra a qualquer momento: `"modo": "sombra"`.

## Formato da fila (para quem produz mensagens)

Um arquivo `.json` por mensagem em `H:\HypadoLocal\whatsapp_fila\`, gravado de forma
atômica (arquivo temporário e troca de nome, como o `hpbase.escrever_json` faz):

```json
{"id": "no_ar_gta-0930-1830_1a2b3c",
 "grupo": "HP | Comissão 🚀",
 "texto": "*Claude - * 🚀 No ar agora — GTA 6 | HP\n\n🎬 Título\n\nInstagram: https://...",
 "anexos": [],
 "tipo": "no_ar",
 "criado_em": "2026-09-30T18:31:00-03:00"}
```

- `anexos`: caminhos absolutos (ou relativos a `H:\HypadoLocal`), no máximo 10. Com
  anexo e texto de até 1000 caracteres, o texto vai como legenda; texto maior vai
  separado e o anexo sai 20 s depois com a legenda `*Claude - * 📎 anexo`.
- Resultado: `enviadas\` (com `enviado_em`), `rejeitadas\` (com `motivo_rejeicao`),
  `erros\` (depois de 3 tentativas, com `historico`).

## Comandos

Sempre a partir de `G:\Meu Drive\Hypado\06 Projeto\app\hp_studio`
(`python` = `& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"`):

| Comando | O que faz |
|---|---|
| `python -m whatsapp_local login` | abre visível e espera o QR (1 vez) |
| `python -m whatsapp_local enviar --uma-vez [--sombra \| --real]` | uma passada na fila e sai |
| `python -m whatsapp_local enviar` | repete até a fila esvaziar |
| `python -m whatsapp_local vigiar --intervalo 60` | fica rodando, 1 ciclo por minuto |
| `python -m whatsapp_local montar-no-ar agendados.json [--so-mostrar] [--grupo "..."]` | aviso "no ar" dos posts que já entraram no ar |
| `python -m whatsapp_local montar-resumo [--dia AAAA-MM-DD]` | resumo do dia (padrão: ontem) |
| `python -m whatsapp_local montar-sabado [--sabado AAAA-MM-DD]` | resumo da semana |
| `python -m whatsapp_local status` | modo, fila, ritmo, login, último erro |
| `python -m whatsapp_local ler-recebidas --real` | passa nos grupos e salva as mensagens novas |
| `python -m whatsapp_local relatorio-sombra [--dia ...]` | refaz o relatório da sombra |

Sem `--sombra`/`--real` vale o `modo` do `config.json`. Códigos de saída:
0 ok · 1 erro · 2 precisa login. Todo comando tem `--help` em português.

## Agendamento (sem janela preta, com pythonw)

`pythonw.exe` roda sem console. O processo auxiliar do Playwright não deve abrir
janela preta (o `sitecustomize.py` do PC força `CREATE_NO_WINDOW` nos subprocessos);
confira na primeira vez rodando a tarefa com o PC em uso.

**Opção 1 (recomendada) — vigia que liga junto com o Windows.** No PowerShell:

```powershell
$py  = "$env:LOCALAPPDATA\Programs\Python\Python312\pythonw.exe"
$dir = "G:\Meu Drive\Hypado\06 Projeto\app\hp_studio"
$acao = New-ScheduledTaskAction -Execute $py -Argument "-m whatsapp_local vigiar --intervalo 60" -WorkingDirectory $dir
$gatilho = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$gatilho.Delay = "PT2M"   # espera 2 min o Google Drive (G:) montar
$ajustes = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 5) -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "HP WhatsApp vigia" -Action $acao -Trigger $gatilho -Settings $ajustes -Description "Enviador local de WhatsApp da HP"
```

**Opção 2 — uma passada a cada 5 minutos** (em vez da opção 1, nunca as duas;
usa as variáveis `$py`, `$dir` e `$ajustes` do bloco acima):

```powershell
$acao = New-ScheduledTaskAction -Execute $py -Argument "-m whatsapp_local enviar --uma-vez" -WorkingDirectory $dir
$gatilho = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5)
Register-ScheduledTask -TaskName "HP WhatsApp envio" -Action $acao -Trigger $gatilho -Settings $ajustes
```

Importante:
- deixe "Executar somente quando o usuário estiver conectado" (o padrão): a janela
  precisa da sessão do Windows, mesmo ficando fora da tela;
- se usou a opção B da instalação, o `setx PLAYWRIGHT_BROWSERS_PATH` já vale para a tarefa;
- não é trabalho pesado (não usa o `pesado.lock`) e pode enviar a qualquer hora,
  inclusive das 18h às 22h30; mas só 1 processo do WhatsApp por vez
  (`whatsapp_local\enviador.lock`);
- para parar: Agendador de Tarefas → "HP WhatsApp vigia" → Desabilitar.

## Montagem automática (sem Claude)

No `config.json`:
- `"arquivo_agendados": "H:\\...\\agendados.json"` → a cada ciclo, os posts que já
  entraram no ar (horário passou, pelo menos 1 link, até 24 h atrás) viram aviso;
- `"hora_resumo_dia": "08:00"` → depois das 8h, resumo de ontem;
- `"hora_resumo_sabado": "10:00"` → sábado depois das 10h, resumo da semana;
- `"grupo_por_canal": {"GTA 6 | HP": "HP | GTA 6"}` → destino por canal (padrão: Comissão).

Nada duplica: o id é fixo por post/dia e grupo.

`agendados.json`: lista (ou `{"posts": [...]}`) de
`{"id", "canal", "titulo", "horario", "links": {"instagram": "...", "tiktok": "..."}}`
(canal pode ser o nome ou o id: `gta`, `futebol`, `filmes`, `receitas`, `carros`, `destinos`;
`status` "cancelado"/"erro" é ignorado).

`metricas_painel.json` (procurado em `H:\HypadoLocal\metricas\`, `H:\HypadoLocal\app\`,
`06 Projeto\` e `06 Projeto\app\`, ou `"arquivo_metricas"` na config):
`{"dias": {"2026-09-29": {"GTA 6 | HP": {"instagram": {"seguidores": 10100, "views": 30000, "curtidas": 900, "comentarios": 40, "posts": 2}}}}}`
ou `{"registros": [{"dia", "canal", "rede", "seguidores", "views", ...}]}`.
Views/curtidas/posts são do dia; seguidores é o total no fim do dia.

## Mensagens do Antônio (recebidas)

Depois de cada envio (no grupo que já está aberto e conferido) e, no vigia, a cada
30 min em todos os grupos permitidos, o app lê as últimas 20 mensagens e grava as
novas em `whatsapp_local\recebidas\AAAA-MM-DD.jsonl`
(`hash, grupo, autor, hora, direcao, texto, lido_em`). Pula as `*Claude - *`, não
duplica (hash de grupo+autor+hora+texto) e não responde nada. Se o WhatsApp Web
estiver no número do próprio Antônio, as mensagens dele aparecem como
`direcao: "saida"`; as dos outros membros, como `"entrada"`.

## Integração com o `hp` / motor

```python
from whatsapp_local import executar
executar({"acao": "enviar"})                 # 1 ciclo; devolve {"ok": ..., "enviadas": ...}
executar({"acao": "montar_no_ar", "agendados": r"H:\...\agendados.json"})
executar({"acao": "montar_resumo"}) ; executar({"acao": "montar_sabado"})
executar({"acao": "ler_recebidas", "modo": "real"}) ; executar({"acao": "status"})
```

## Quando o WhatsApp mudar a página

O log diz `elemento não encontrado: <NOME> (ver seletores.py)`. Todos os seletores
estão em `seletores.py`, com comentários; acrescente a alternativa nova no começo da
lista certa. Enquanto não achar o cabeçalho, **nada é enviado** (falha segura).

| Sintoma | O que fazer |
|---|---|
| `status` diz PRECISA LOGIN | rodar `login` e escanear o QR |
| `Playwright NÃO instalado` | passo 2 da instalação |
| rejeitada "fora da lista" | conferir o nome exato em `grupos_permitidos.json` |
| falha `CabecalhoDivergente` | o nome do grupo mudou ou o seletor do título mudou |
| a página não carrega com a janela minimizada | `"minimizar_janela": false` no `config.json` (continua fora da tela) |
| "outro processo do WhatsApp está rodando" | já tem vigia rodando; não agende as duas opções |

## Testes

```powershell
cd "G:\Meu Drive\Hypado\06 Projeto\app"
python -m pytest -q hp_studio/whatsapp_local
```
Nenhum teste usa internet, navegador ou WhatsApp de verdade (usam o `NavegadorFalso`
e um relógio falso).
