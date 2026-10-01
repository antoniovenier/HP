# qa_paridade — teste de paridade (app x Claude)

Compara o vídeo ou a arte que o **app** fez com o mesmo trabalho feito **100% pelo Claude** (a referência) e dá uma nota de 0 a 10 para cada métrica, uma nota final e um veredito. Também guarda o **modo sombra**: nenhuma tarefa passa para o app sem **7 dias corridos seguidos aprovados**.

## O que é medido

| Métrica | Como mede | Nota 10 | Reprova (< 9) |
|---|---|---|---|
| Duração | diferença absoluta (s), lida do `ffmpeg -i` | até 0,1 s | acima de ~0,25 s |
| Imagem (SSIM) | quadros alinhados no tempo (1 por segundo, mínimo 6), em cinza, reduzidos (1080x1920 vira 270x480); SSIM gaussiano 7x7 feito em numpy; média, pior quadro e os 3 piores com o tempo e a região da tela | média >= 0,985 e pior >= 0,97 | média < 0,97 ou pior < 0,93 |
| Áudio (loudness) | LUFS integrado e true peak (filtro `loudnorm`, plano B `ebur128`) | diferença <= 0,5 LU, app a até 1 LU de -14 e pico <= -1 dBTP | diferença > 1 LU, app a mais de 2 LU de -14 ou pico > -0,5 dBTP |
| Legenda | texto por palavras (difflib, sem acento/caixa/pontuação); desvio de início e fim dos blocos pareados (ms); número de blocos | texto igual, desvio médio <= 40 ms e máximo <= 100 ms, mesmos blocos | texto < 98% igual, desvio médio > 100 ms, máximo > 200 ms ou 1 bloco a mais/menos |
| Lâminas | pastas em ordem natural do nome; SSIM de cada par; casamento ótimo (algoritmo húngaro) para achar ordem trocada, lâmina faltando e sobrando | mesma quantidade, mesma ordem, SSIM como acima | qualquer troca, falta ou sobra |
| Formato | resolução, fps e presença de áudio | tudo igual | resolução diferente, fps diferente ou áudio só de um lado |

Cada métrica tem subnotas; a nota da métrica é a **menor subnota**. Todos os números estão em `limites.json` (com explicação dentro). Para ajustar sem mexer no pacote, crie `H:\HypadoLocal\app\paridade\limites.json` só com o que muda (ele é mesclado por cima), ou passe `--limites arquivo.json`.

**Nota final** = média ponderada das métricas que se aplicam (pesos: duração 1, SSIM 3, loudness 1,5, legenda 1,5, lâminas 3, formato 0,5).

**Veredito**
- `IDENTICO`: média >= 9,5 e todas as métricas >= 9
- `EQUIVALENTE`: média >= 9 e todas >= 9
- `DIFERENTE`: alguma métrica < 9 (ou média < 9)

**Passa no dia (aprovado)**: todas as métricas >= 9 **e** média >= 9,5 (ou seja, só `IDENTICO`). Configurável no bloco `veredito` do `limites.json`.

## Instalação

1. Python 3.12 já instalado. No PowerShell:
   `& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m pip install numpy pillow pytest`
2. ffmpeg no PATH (ou variável `HP_FFMPEG` apontando para o `ffmpeg.exe`; o padrão do PC é `H:\HypadoLocal\ferramentas\ffmpeg\bin`). **Não precisa de ffprobe.**
3. O pacote fica em `G:\Meu Drive\Hypado\06 Projeto\app\hp_studio_nuvem\qa_paridade\` e usa a base `hpbase` (mesma pasta).

## Comandos

Rodar de dentro de `...\06 Projeto\app\hp_studio_nuvem`:

```powershell
cd "G:\Meu Drive\Hypado\06 Projeto\app\hp_studio_nuvem"
python -m qa_paridade --help

# vídeo (com ou sem legenda em arquivo; se os vídeos tiverem faixa de legenda, ela é usada sozinha)
python -m qa_paridade video app.mp4 ref.mp4 --tarefa editor_reel --id post123
python -m qa_paridade video app.mp4 ref.mp4 --legenda-app app.srt --legenda-ref ref.srt --tarefa legendador

# arte única, pasta de lâminas, só legenda
python -m qa_paridade imagem app.png ref.png --tarefa estaticos
python -m qa_paridade laminas "H:\...\carrossel_app" "H:\...\carrossel_ref" --tarefa carrossel
python -m qa_paridade legenda app.srt ref.ass

# situação do modo sombra (todas as tarefas ou uma)
python -m qa_paridade status
python -m qa_paridade status --tarefa editor_reel --json
```

Opções comuns: `--tarefa` (registra no modo sombra), `--id` (nome da comparação, ex. id do post; padrão = hora), `--saida PASTA` (sem tarefa), `--limites arquivo.json`, `--json` (relatório inteiro na tela).

Códigos de saída: `0` passou no dia, `1` não passou, `2` erro de entrada (arquivo/pasta não existe, mídia ilegível), `3` PC ocupado com outro trabalho pesado ou horário proibido (18h–22h30) — tentar depois.

O trabalho de vídeo roda dentro da trava `TravaPesada("qa_paridade")` (`H:\HypadoLocal\app\pesado.lock`): 1 trabalho pesado por vez e nunca das 18h às 22h30. Imagem, lâminas e legenda são leves e não pegam a trava.

## Onde ficam os resultados

- Com `--tarefa`: `H:\HypadoLocal\app\paridade\<tarefa>\AAAA-MM-DD_<id>.json` + `.md` (mesmo nome) e `resumo.json` da tarefa (refeito a cada comparação).
- Sem tarefa: `H:\HypadoLocal\app\paridade\_avulsos\` (ou `--saida`).
- Log: `H:\HypadoLocal\app\logs\qa_paridade_<dia>.log`.

O `.md` é para ler: veredito, tabela de notas, piores quadros (tempo e região da tela), diferenças de texto da legenda, lâminas fora de ordem/faltando/sobrando.

## Modo sombra — regra dos 7 dias

Uma tarefa só é **liberada para o app** quando tem **7 dias corridos seguidos** de sombra, **cada dia com pelo menos 1 comparação** e **todas aprovadas**.
- Duas ou mais comparações no mesmo dia contam como 1 dia (e todas precisam passar).
- Um dia com qualquer reprovação **zera** a contagem; se a tarefa já estava liberada, ela volta para a sombra.
- Dia sem comparação quebra a sequência (recomeça do 1) enquanto ela não chegou a 7. Hoje ainda sem comparação não quebra nada.
- Depois de liberada, conferências esporádicas aprovadas mantêm a liberação.

`status` mostra a tabela: tarefa, dias aprovados seguidos, quantos faltam, liberada sim/não, último dia, última nota e uma observação (ex.: "reprovado em 2026-10-03 zerou a contagem"). Em Python: `from qa_paridade import status_tarefa; status_tarefa("editor_reel")`.

### Como ligar o modo sombra (passo a passo)

1. Escolha o nome da tarefa (ex.: `editor_reel`, `legendador`, `carrossel`, `estaticos`) e use sempre o mesmo.
2. Todo dia, a rotina de sempre (Claude) gera a peça normalmente — ela continua sendo a que vai ao ar.
3. O app gera a mesma peça, com as mesmas entradas, **sem publicar**.
4. Rode `python -m qa_paridade video <app> <claude> --tarefa <nome> --id <post>` (ou `imagem`/`laminas`/`legenda`).
5. Se sair `1` (não passou), abra o `.md` do dia para ver onde diferiu, corrija o motor e continue no dia seguinte (a contagem recomeça).
6. Quando `status` mostrar `liberada = sim`, a tarefa pode passar para o app.

## Integração com o motor do HP Studio

O motor chama `qa_paridade.executar(trabalho) -> dict`:

```python
from qa_paridade import executar
r = executar({"tipo": "video", "app": r"H:\...\app.mp4", "ref": r"H:\...\ref.mp4",
              "tarefa": "editor_reel", "id": "post123",
              "legenda_app": None, "legenda_ref": None})
# r = {"ok": True, "aprovado": True, "veredito": "IDENTICO", "nota_final": 9.87,
#      "json": "...", "md": "...", "status": {"dias_seguidos": 3, "falta": 4, "liberada": False, ...}}
# PC ocupado/horário proibido: {"ok": False, "adiar": True, "erro": "..."} -> o motor tenta depois
# erro de entrada:              {"ok": False, "adiar": False, "erro": "..."}
```

`tipo`: `video`, `imagem`, `laminas` ou `legenda`. Nunca levanta exceção; nada pede aprovação manual.

## Testes

```powershell
cd "G:\Meu Drive\Hypado\06 Projeto\app"
python -m pytest -q hp_studio/qa_paridade
```

Os testes geram mídia sintética pequena com o ffmpeg (testsrc2 180x320 + seno, 3 s) e cobrem: vídeo idêntico (nota 10), caixa sobreposta, ruído e vídeo adiantado 0,5 s (DIFERENTE), duração diferente, áudio 6 dB mais baixo, sem áudio, legenda deslocada 500 ms / texto trocado / bloco faltando / SRT x ASS, legenda embutida no vídeo, lâminas trocadas/faltando/sobrando, a regra dos 7 dias, o SSIM próprio (igual = 1,0; ruído < 0,9; confere com a conta direta janela por janela) e o algoritmo húngaro (confere com força bruta). Rodam em ~10 s. Nada acessa rede nem o H:/G: de verdade.

## Limites conhecidos

- O SSIM é calculado em tamanho reduzido e em cinza: diferença só de cor (mesmo brilho) quase não aparece; texto muito miúdo pesa menos que em tamanho cheio.
- Quadros são comparados no mesmo instante; se o app tiver fps diferente da referência, sai aviso em Formato e o SSIM cai um pouco em cenas com muito movimento.
- Legenda queimada na imagem entra no SSIM, não na métrica de legenda (essa precisa de .srt/.ass ou faixa de legenda).
- Os limites iniciais foram calibrados com mídia sintética (reencode crf 18 x crf 23 do mesmo vídeo dá SSIM ~0,988 e passa); ajuste no `limites.json` depois dos primeiros dias de sombra, se precisar.
