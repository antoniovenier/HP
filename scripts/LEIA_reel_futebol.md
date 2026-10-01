# reel_futebol.py — montador de reels do Futebol | HP (@hp.futebol)

Ticket `20260930-152310-futebol-montador-reel-futebol-py…` (P0). Monta o reel
inteiro a partir de **um arquivo JSON (o "roteiro")**, sem Claude no meio:
arte, legenda queimada, crédito, áudio e loudness saem prontos.

- Saída: **1080x1920**, H.264 yuv420p, **30 fps**, AAC **48 kHz**, loudness
  **−14 LUFS** (loudnorm em 2 passadas), com um relatório `.relatorio.json` ao lado.
- 6 formatos: `gol`, `noticia`, `debate`, `estatistica`, `resultado`, `tabela`.
- Render medido aqui (4 núcleos): 3 a 36 s por reel (tabela no fim). Limite
  duro: **10 min** (passou disso, ele para e avisa).
- Trabalho pesado: pega o `H:\HypadoLocal\app\pesado.lock` (1 por vez) e
  **não roda das 18h às 22h30**.

## Regras que o montador garante sozinho (recusa o roteiro se quebrar)

| Regra | Como ele confere |
|---|---|
| Futebol sem imagem de transmissão de TV | qualquer `fonte_tipo` = `transmissao_tv` (ou `tv`, `print_tv`) → **recusa** |
| Vídeo só oficial (clube, CBF, liga) | `fonte_tipo` do vídeo precisa ser `oficial_clube`, `oficial_cbf` ou `oficial_liga` |
| Crédito sempre | vídeo sem `credito` → recusa; foto sem `credito` → recusa. No vídeo aparece fixo "Vídeo: @clube" |
| Áudio original, nunca mudo | vídeo sem trilha de áudio ou com áudio mudo (pico < −60 dB) → recusa. O gol não aceita música por cima |
| **Nunca narração/voz sintética no futebol** | qualquer campo `voz`, `narracao`, `tts`, `locucao`, `dublagem`, `piper`… ou `"tipo": "tts"` em qualquer lugar do roteiro → recusa |
| Música só livre de direitos | a música precisa estar numa pasta chamada `musicas_livres` e ter licença registrada (veja abaixo); sem licença → recusa |
| Gol nunca é o vídeo puro | o modo `gol` sempre monta: cartão de 2 s + vídeo + caixa de legenda + crédito |
| Safe zones do Reels | nada escrito nos **250 px do topo** nem nos **350 px da base**; se algum texto invadir, o render para com erro |

## Instalação (uma vez, no PC)

1. Copie os arquivos para `G:\Meu Drive\Hypado\scripts\`:
   `reel_futebol.py`, `reel_futebol_base.py`, `reel_futebol_arte.py`,
   `reel_futebol_midia.py`, `reel_futebol_roteiro.py`, `reel_futebol_modos.py`,
   `reel_futebol_exemplos.py` e `testes\test_reel_futebol.py`.
2. Abra o PowerShell (tecla Windows, digite `powershell`, Enter).
3. Instale as bibliotecas (só na primeira vez):
   `& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m pip install pillow numpy pytest`
4. Confira o ffmpeg: `ffmpeg -version`. Se der "não reconhecido", ele pega sozinho
   `H:\HypadoLocal\ferramentas\ffmpeg\bin\ffmpeg.exe`; se estiver em outro lugar,
   rode `setx HP_FFMPEG "caminho\do\ffmpeg.exe"` e abra um PowerShell novo.
   **Não precisa de ffprobe** (duração e tamanho saem do próprio ffmpeg).
5. O script acha o `hpbase` sozinho em `..\06 Projeto\app\hp_studio_nuvem`. Se o app
   estiver em outro lugar: `setx HP_APP "G:\Meu Drive\Hypado\06 Projeto\app"`.
6. Fonte: ele procura **Arial Bold** (`arialbd.ttf`) e depois **Segoe UI Bold**
   em `C:\Windows\Fonts` (no Linux, DejaVuSans-Bold). Para usar outra fonte, ponha
   o caminho no estilo (campo `fonte`) ou em `setx HP_FONTE "caminho.ttf"`.

## Primeiro uso: gerar os 4 modelos (passo a passo)

1. Abra o PowerShell **fora do horário 18h–22h30**.
2. `cd "G:\Meu Drive\Hypado"`
3. `python scripts\reel_futebol.py exemplos`
4. Espere ~40 s. Ele escreve uma linha `OK:` por modelo.
5. Abra a pasta `H:\HypadoLocal\canais\futebol\modelos_reel\`. Tem:
   - `MODELO_gol.mp4`, `MODELO_noticia.mp4`, `MODELO_debate.mp4`, `MODELO_estatistica.mp4`;
   - `MODELO_<formato>.json` (o roteiro usado — é o ponto de partida para os reais);
   - `MODELO_<formato>.relatorio.json` (duração, LUFS, tempo de render…);
   - `LEIA_MODELOS.txt` e a pasta `midia_sintetica\`.
6. Assista no celular. Todos têm a marca d'água **"MODELO · MÍDIA SINTÉTICA"**
   e times fictícios (Azul FC, Verde EC…): **não publicar**.
7. Pressa? `python scripts\reel_futebol.py exemplos --curto` faz versões de 2–5 s.

## Fazer um reel de verdade (passo a passo)

1. Crie a pasta do item (na esteira, ex.: `H:\HypadoLocal\esteira\04_edicao\P0_2026-09-30_2140_futebol_gol-silva\`).
2. Ponha dentro a mídia **oficial** baixada (vídeo do perfil do clube/CBF/liga, fotos oficiais).
3. Copie o modelo do formato: `python scripts\reel_futebol.py esquema gol > roteiro.json`
   (troque `gol` pelo formato). Ou copie o `MODELO_gol.json` e apague `_aviso` e `marca_dagua`.
4. Abra o `roteiro.json` no Bloco de Notas e troque: times, placar, autor, minuto,
   `video.arquivo` (nome do arquivo na mesma pasta), `video.credito` (o @ do clube),
   `video.fonte_tipo` e a `legenda`. Salve como UTF-8.
5. Confira: `python scripts\reel_futebol.py validar roteiro.json`
   - `OK: roteiro válido` → siga;
   - `RECUSADO:` → cada linha diz o campo e o motivo; corrija e repita.
6. (Opcional) Veja o que ele vai rodar, sem gastar tempo: `python scripts\reel_futebol.py montar roteiro.json --simular`
7. Monte: `python scripts\reel_futebol.py montar roteiro.json`
   (saída: `roteiro.mp4` ao lado do JSON; outra saída com `--saida final.mp4`).
8. Leia a linha `OK:` (tamanho 1080x1920, LUFS perto de −14 no gol) e abra o vídeo.
9. O `roteiro.relatorio.json` guarda créditos, fonte do vídeo, legenda e
   números — use os créditos no texto do post.
10. Se aparecer `ESPERAR:` é trava ocupada ou horário proibido: tente de novo depois.

Códigos de saída (para rotinas): `0` ok · `1` roteiro recusado · `2` erro de render · `3` trava/horário.

## O roteiro (JSON) — esquema completo

Campos que valem para todos os formatos:

| Campo | Obrigatório | O que é |
|---|---|---|
| `modo` | sim | `gol`, `noticia`, `debate`, `estatistica`, `resultado` ou `tabela` |
| `canal` | não | se vier, tem que ser `"futebol"` |
| `versao`, `id` | não | controle; `id` vira o nome do arquivo quando o roteiro vem como dict |
| `saida` | não | caminho do .mp4 (relativo ao roteiro) |
| `musica` | não (proibida no gol) | `{"arquivo": "nome.mp3", "inicio": 0}` — veja "Música livre" |
| `estilo` | não | caminho de um estilo JSON ou um objeto com ajustes (ex.: `{"cores": {"destaque": "#FFCC00"}}`) |
| `marca_dagua` | não | texto diagonal translúcido (usado nos modelos) |
| `legenda_auto` | não | `true` = mesmo que `--legenda-auto` |

Caminhos relativos (`arquivo`, `escudo`) são relativos à pasta do roteiro.
Mídia (`video`, `clipe`, `foto`): `arquivo`, `credito`, `fonte_tipo`; vídeo e
clipe aceitam `inicio`/`fim` em segundos (`fim: null` = até o fim); foto aceita
`foco: [x, y]` (0 a 1, onde centralizar o recorte). Para foto, `fonte_tipo` pode
ser `oficial_clube`, `oficial_cbf`, `oficial_liga` ou `propria` (arte da HP).

`python scripts\reel_futebol.py esquema <modo>` imprime cada exemplo abaixo.

### `gol` — cartão de 2 s + vídeo oficial com o áudio original

Obrigatórios: `mandante`/`visitante` (`nome`, `gols`; opcionais `sigla`, `cor`,
`escudo`, `artigo` "do"/"da"), `time_do_gol`, `minuto`, `autor`, `video`
(`arquivo`, `fonte_tipo`, `credito`) e `legenda` (texto, lista de textos ou
lista `{texto, inicio, fim}` em segundos do vídeo) — ou `--legenda-auto`.
Opcionais: `campeonato`, `duracao_cartao` (1,5–3 s; padrão 2).

```json
{
  "versao": 1, "canal": "futebol", "modo": "gol",
  "id": "2026-09-30_gol_azul_silva",
  "mandante": {"nome": "Azul FC", "sigla": "AZU", "gols": 2, "cor": "#1D4ED8"},
  "visitante": {"nome": "Verde EC", "sigla": "VER", "gols": 1, "cor": "#15803D"},
  "time_do_gol": "mandante",
  "minuto": 67,
  "autor": "Silva",
  "campeonato": "Campeonato Exemplo 2026 · 28ª rodada",
  "duracao_cartao": 2.0,
  "video": {"arquivo": "clipe_oficial_do_clube.mp4", "fonte_tipo": "oficial_clube",
            "credito": "@azulfc", "link_origem": "https://www.instagram.com/p/EXEMPLO/",
            "inicio": 0, "fim": null},
  "legenda": "Silva sobe mais que a zaga e testa no canto: o Azul vira o jogo no fim e segue na briga pelo título!"
}
```

Como sai: cartão (GOL!, "do Azul FC", escudos e placar, "SILVA · 67'") por 2 s
em silêncio → vídeo com o som original normalizado a −14 LUFS. Vídeo deitado
fica numa janela no meio (fundo do canal em volta); vídeo em pé cobre a tela
com degradês escuros atrás dos textos. Sempre: faixa do placar no topo,
"Vídeo: @clube" fixo e a caixa de legenda.

### `noticia` — 2 a 4 fotos com zoom lento, título grande, legenda queimada, música baixa, SEM voz

Obrigatórios: `titulo`, `fotos` (2 a 4, cada uma com `credito`), `legendas`.
Opcionais: `fonte`, `duracao_por_foto` (1–10 s; padrão 4), `musica`, `etiqueta`.

```json
{
  "versao": 1, "canal": "futebol", "modo": "noticia",
  "id": "2026-09-30_noticia_renovacao_silva",
  "titulo": "Azul FC renova com o artilheiro Silva até 2029",
  "fonte": "Fonte: site oficial do Azul FC",
  "fotos": [
    {"arquivo": "foto_oficial_1.jpg", "credito": "Foto: Fotógrafo Exemplo / Azul FC", "fonte_tipo": "oficial_clube"},
    {"arquivo": "foto_oficial_2.jpg", "credito": "Foto: Fotógrafo Exemplo / Azul FC", "fonte_tipo": "oficial_clube"},
    {"arquivo": "foto_oficial_3.jpg", "credito": "Foto: Assessoria / Azul FC", "fonte_tipo": "oficial_clube"}
  ],
  "legendas": ["O camisa 9 assinou nesta terça-feira",
               "São 21 gols no campeonato, líder da artilharia",
               "Novo contrato vai até dezembro de 2029"],
  "duracao_por_foto": 4.0,
  "musica": {"arquivo": "trilha_livre.mp3", "inicio": 0}
}
```

Foto deitada: aparece inteira numa faixa, com a própria foto desfocada de
fundo. Foto em pé: cobre a tela. Troca de foto com fusão de 0,4 s. Lista de
legendas sem tempo = divididas igualmente pela duração.

### `debate` — 3 recortes (foto ou clipe) com nome e 1 número + "comenta aí"

Obrigatórios: `titulo` e exatamente 3 `recortes`, cada um com `nome`, `numero`
e **`foto` OU `clipe`**. Opcionais: `time`, `rotulo`, `duracao_recorte`
(padrão 3 s), `duracao_final` (padrão 2,5 s), `pergunta_final`, `musica`.
Clipe segue as regras do vídeo do gol (oficial, crédito, áudio original).

```json
{
  "versao": 1, "canal": "futebol", "modo": "debate",
  "titulo": "Quem é o melhor camisa 9 do campeonato?",
  "recortes": [
    {"nome": "Silva", "time": "Azul FC", "numero": "21", "rotulo": "gols no campeonato",
     "foto": {"arquivo": "foto_oficial_2.jpg", "credito": "Foto: Azul FC", "fonte_tipo": "oficial_clube"}},
    {"nome": "Costa", "time": "Verde EC", "numero": "17", "rotulo": "gols no campeonato",
     "clipe": {"arquivo": "clipe_oficial_do_clube.mp4", "fonte_tipo": "oficial_clube", "credito": "@verdeec", "inicio": 0}},
    {"nome": "Souza", "time": "Rubro AC", "numero": "0,71", "rotulo": "gols por jogo",
     "foto": {"arquivo": "foto_oficial_4.jpg", "credito": "Foto: Rubro AC", "fonte_tipo": "oficial_clube"}}
  ],
  "duracao_recorte": 3.0,
  "duracao_final": 2.5,
  "pergunta_final": "Qual deles é o melhor? Comenta aí!",
  "musica": {"arquivo": "trilha_livre.mp3", "inicio": 0}
}
```

### `estatistica` — contador animado de 0 até o valor

Obrigatórios: `titulo`, `valor` (número), `rotulo`. Opcionais: `casas_decimais`
(0–3), `prefixo`, `sufixo` (ex.: `"%"`), `fonte`, `duracao` (padrão 5 s),
`duracao_contagem` (padrão 2,5 s), `foto` (fundo escurecido, com crédito), `musica`.

```json
{
  "versao": 1, "canal": "futebol", "modo": "estatistica",
  "titulo": "Artilheiro do campeonato",
  "valor": 21, "casas_decimais": 0, "prefixo": "", "sufixo": "",
  "rotulo": "gols de Silva em 27 jogos pelo Azul FC",
  "fonte": "Fonte: tabela oficial da liga",
  "duracao": 5.0, "duracao_contagem": 2.5,
  "musica": {"arquivo": "trilha_livre.mp3", "inicio": 0}
}
```

### `resultado` — placar final com escudos e gols (autor e minuto)

Obrigatórios: `mandante`, `visitante` (como no gol; `escudo` = imagem opcional,
sem ela vira círculo com a sigla na `cor`). `gols`: lista `{time, autor, minuto,
tipo}` (`tipo` opcional: `penalti`, `contra`). A contagem por lado **tem que
bater** com o placar (gol contra conta para o time que ganhou o gol).
Opcionais: `campeonato`, `estadio`, `data`, `etiqueta_placar` (padrão "FIM DE JOGO"), `duracao`, `musica`.

```json
{
  "versao": 1, "canal": "futebol", "modo": "resultado",
  "campeonato": "Campeonato Exemplo 2026 · 28ª rodada",
  "mandante": {"nome": "Azul FC", "sigla": "AZU", "gols": 2, "cor": "#1D4ED8", "escudo": "escudos/azul.png"},
  "visitante": {"nome": "Verde EC", "sigla": "VER", "gols": 1, "cor": "#15803D"},
  "gols": [{"time": "mandante", "autor": "Silva", "minuto": 12},
           {"time": "visitante", "autor": "Costa", "minuto": "45+2", "tipo": "penalti"},
           {"time": "mandante", "autor": "Souza", "minuto": 81}],
  "estadio": "Estádio Exemplo", "data": "30/09/2026",
  "duracao": 5.0
}
```

### `tabela` — classificação (top N) entrando linha a linha

Obrigatórios: `titulo`, `linhas` (cada uma com `pos`, `time`, `pts`; `j`, `v`,
`sg` aparecem se todas as linhas tiverem). Opcionais: `subtitulo`, `top` (2–20;
padrão 10), `zonas` (`libertadores`, `pre_libertadores`, `sulamericana`,
`rebaixamento`, `acesso` como `[de, até]`, ou `{"de":1,"ate":4,"cor":"#…","rotulo":"…"}`),
`destaque` (times com borda amarela), `fonte`, `duracao` (padrão 6 s), `musica`.

```json
{
  "versao": 1, "canal": "futebol", "modo": "tabela",
  "titulo": "Classificação do Campeonato Exemplo",
  "subtitulo": "após a 28ª rodada",
  "top": 10,
  "linhas": [{"pos": 1, "time": "Azul FC", "pts": 60, "j": 28, "v": 18, "sg": 30},
             {"pos": 2, "time": "Verde EC", "pts": 57, "j": 28, "v": 17, "sg": 26}],
  "zonas": {"libertadores": [1, 4], "pre_libertadores": [5, 6], "sulamericana": [7, 12], "rebaixamento": [17, 20]},
  "destaque": ["Azul FC"],
  "fonte": "Fonte: tabela oficial da liga",
  "duracao": 6.0
}
```

## Música livre (obrigatório para usar música)

1. As músicas ficam em `H:\HypadoLocal\musicas_livres\` (ou em qualquer pasta
   chamada `musicas_livres`; outra pasta padrão: variável `HP_MUSICAS_LIVRES`
   ou campo `pasta_musicas` do estilo).
2. Nome solto no roteiro (`"arquivo": "trilha.mp3"`) = procura nessa pasta.
3. Registre a licença em `musicas_livres\licencas.json`:
   ```json
   {"trilha.mp3": {"licenca": "CC0", "fonte": "https://…", "autor": "Fulano"}}
   ```
   (ou um arquivo `trilha.mp3.licenca.json` ao lado). `licenca` vazia ou
   "desconhecida" e `fonte` vazia são recusadas.
4. Volume, com entrada e saída suaves:
   - quando há áudio principal (debate com clipes), a música fica **20 dB abaixo**
     dele (≈ −34 LUFS, `musica_db_relativo`);
   - quando a música é o único som (notícia, estatística…), ela sai a **−20 LUFS**
     (6 dB abaixo do alvo, `musica_sozinha_db_relativo`): baixa, mas audível —
     a −34 LUFS o reel pareceria mudo no celular.

## Legenda automática do gol (`--legenda-auto`)

Chama `python -X utf8 scripts\posts_futebol.py legenda_video <roteiro.json>` e
usa o que ele imprimir (texto puro, ou JSON com a chave `legenda`). Se o
`posts_futebol.py` tiver outra assinatura, troque no estilo, sem mexer no código:
`"legenda_auto_cmd": ["{python}", "-X", "utf8", "{script}", "legenda_video", "{roteiro}"]`.
Outro caminho do script: variável `HP_POSTS_FUTEBOL`. No `--simular` ele não
chama o script (só mostra que chamaria).

## Estilo do canal (cores, fonte, áudio)

Padrão embutido (verde escuro + amarelo HP, marca "FUTEBOL | HP"). Para mudar
sem código, crie `H:\HypadoLocal\canais\futebol\estilo_reel.json` só com o que
quiser trocar, por exemplo:

```json
{"cores": {"fundo": "#06170F", "fundo2": "#0F3B26", "destaque": "#FFD23F", "texto": "#FFFFFF"},
 "caixa_opacidade": 0.62, "fonte": "C:\\Windows\\Fonts\\arialbd.ttf",
 "alvo_lufs": -14.0, "true_peak": -1.5, "musica_db_relativo": -20.0,
 "video": {"preset": "veryfast", "crf": 20}, "duracao_max_s": 90, "limite_render_s": 600}
```

Ou passe `--estilo outro.json` no comando.

## Como funciona por dentro (para quem for mexer)

- Cada formato vira uma lista de **segmentos**: desenhados no Pillow (cartão,
  fotos com zoom, contador, tabela) e mandados ao ffmpeg por pipe, ou **clipe**
  (vídeo oficial + moldura PNG + legendas PNG com hora de entrar/sair).
- Todo texto é imagem PNG feita no Pillow (caixa semitransparente, quebra
  automática de linha) — não depende de libass/fontconfig.
- Zoom lento (Ken Burns) no Pillow com recorte fracionário: mais liso e mais
  rápido que o `zoompan` do ffmpeg (medido: 7,5 s contra 13 s para 5 s de vídeo).
- Os segmentos são emendados **sem recodificar o vídeo** (`-c:v copy`); só o
  áudio é tratado no fim: passada 1 mede (loudnorm JSON), passada 2 aplica
  `linear=true`. Se a medição falhar, cai para 1 passada dinâmica (anotado em
  `loudnorm_passadas` no relatório).
- Temporários em `H:\HypadoLocal\app\tmp\` (nada no C:), apagados no fim
  (`--manter-temp` guarda para investigar).
- Log: `H:\HypadoLocal\app\logs\reel_futebol_<dia>.log`.
- Subprocessos sem janela preta (CREATE_NO_WINDOW), pronto para pythonw.

## Tempos de render medidos (Linux, 4 núcleos, ffmpeg 7.0)

| Reel | Duração | Render |
|---|---|---|
| gol (cartão 2 s + clipe 720p 8 s) | 10 s | 3,9 s |
| gol (clipe 1080p60 de 30 s, 2 legendas) | 32 s | 20,4 s |
| notícia (3 fotos × 4 s) | 12 s | 12,6 s |
| notícia (4 fotos × 8 s) | 32 s | 36,3 s |
| debate (2 fotos + 1 clipe + final) | 11,5 s | 7,2 s |
| estatística | 5 s | 2,2 s |
| resultado | 5 s | 1,4 s |
| tabela (top 10) | 6 s | 1,8 s |

Pior caso previsto (90 s de notícia com fotos em pé): ~2 min — bem abaixo dos 10 min.

## Cadência (onde encaixa no plano)

Quantidade por dia, horários e formatos prioritários seguem os números do
plano **`07 Canais\Futebol\PLANO_CRESCIMENTO.md`** (o plano não veio para esta
entrega; nenhum número foi inventado aqui). Encaixe na esteira:
- `gol` e `resultado` são **P0** (faixa expressa: vai do pedido ao ar na hora);
- `noticia` e `tabela` costumam ser **P1** (do dia);
- `debate` e `estatistica` servem bem como **P2** (programados) para engajamento.

## Integração com o HP Studio (motor)

Gancho: `reel_futebol.executar(trabalho: dict) -> dict` (nunca levanta exceção).

```python
executar({"acao": "montar", "roteiro": "caminho\\roteiro.json", "saida": "final.mp4",
          "simular": False, "legenda_auto": True})
# -> {"ok": True, "saida": ..., "duracao_planejada": 10.0, "lufs_saida": -14.0,
#     "tempo_render_s": 3.9, "creditos": ["@azulfc"], ...}
# -> {"ok": False, "tipo": "roteiro_invalido" | "trava_ocupada" | "erro", "erro": "...", "erros": [...]}
```

`acao` também aceita `"validar"` e `"exemplos"`. `roteiro` pode ser um dict
(passe `"base"` = pasta dos arquivos). Na esteira, a etapa `04_edicao` chama
`executar` com o `roteiro.json` da pasta do item e grava o `final.mp4`;
`trava_ocupada` = recolocar na fila depois.

**Modo sombra (7 dias antes de assumir):** rode com `--simular` ao lado do
fluxo atual para conferir se os roteiros passam; depois renderize de verdade
numa pasta à parte (`--saida H:\HypadoLocal\sombra\...`) e compare com o vídeo
feito pelo Claude usando o `qa_paridade` (duração, SSIM, loudness, legenda). Só
depois de 7 dias iguais o app assume.

## Erros comuns e o que fazer

| Mensagem | O que fazer |
|---|---|
| `fonte_tipo = 'transmissao_tv'…` | não use: pegue o vídeo do perfil oficial do clube/CBF/liga |
| `falta o crédito do vídeo` | preencha `video.credito` com o @ do perfil oficial |
| `o vídeo não tem áudio` / `áudio original está mudo` | baixe de novo com o som (o futebol sempre leva o som original) |
| `futebol NUNCA leva narração/voz sintética` | tire o campo de voz; futebol não usa `dublar.py` |
| `sem licença registrada` | registre em `musicas_livres\licencas.json` ou troque a música |
| `placar não bate` | confira `gols` do mandante/visitante e a lista de gols |
| `título vazio` | preencha `titulo` |
| `trecho inválido` | `inicio`/`fim` fora da duração do vídeo |
| `reel com XXs passa do máximo de 90s` | corte com `inicio`/`fim` ou use menos fotos |
| `ESPERAR: horário proibido` / `pesado.lock com '…'` | outro trabalho pesado rodando ou 18h–22h30: tentar depois |
| `ERRO: … ffmpeg falhou` | rode de novo com `--manter-temp` e mande o log do dia |

## Testes

```
cd "G:\Meu Drive\Hypado\06 Projeto\app"
python -m pytest -q ..\..\scripts\testes\test_reel_futebol.py
```
(no repositório: `cd app && python -m pytest -q ../scripts/testes/test_reel_futebol.py`).
29 testes, ~36 s, sem rede e sem mídia real: recusas (voz sintética, TV,
música sem licença, gol sem crédito, título vazio, vídeo mudo…), render de
cada formato conferindo 1080x1920, duração ±0,2 s, cartão de 2 s, áudio
original (seno de 440 Hz preservado), −14 LUFS no gol e ≈ −20 LUFS da música
sozinha, trava e horário proibido.
