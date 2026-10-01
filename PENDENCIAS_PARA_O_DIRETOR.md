# PENDENCIAS_PARA_O_DIRETOR.md — rodada 2 (01/10/2026)

Tudo que mexe em `.claude\` (CLAUDE.md da empresa, rotinas, SKILLs). A nuvem **não edita** essa pasta:
cada item traz o arquivo onde o Diretor cola e o trecho pronto. Ordem: do que destrava mais para o que é
só ajuste de texto. (Os itens das tarefas B, C e E vêm depois dos de A, D e F.)

## 1. `CLAUDE.md` da empresa — 3 linhas de regra que o código da rodada 2 já aplica

Colar na seção de regras de conteúdo/operacão (perto de "trabalho pesado 1 por vez"):

```
- P0 da esteira (gol, placar, resultado, bombástica, lançamento) roda também das 18h às 22h30,
  1 pesado por vez (pesado.lock). P1/P2 continuam esperando 22h30. (Decisão do Antônio, 30/09.)
- Voz sintética (Piper, "dublado por HP"): permitida no GTA (criador gringo "idioma": "en" do
  config.json sai dublado) e em Filmes, Receitas, Carros e Destinos; NUNCA no Futebol.
- WhatsApp: resumo do dia, aviso "no ar", resumo de sábado E avisos ao Antônio (tipo "aviso":
  algo precisa dele — senha, login, decisão, falha). Toda mensagem começa com *Claude - *;
  de madrugada (0h–7h30) nada sai: fica na fila com enviar_apos.
```

Por quê: o item 1 é a decisão de 30/09 que a rodada 1 já pedia; o item 2 é o que `esteira/constantes.py::CANAIS_COM_VOZ`
passou a aceitar (o `config.json` real do GTA tem `dublagem` e 19 criadores `en`); o item 3 é o que
`whatsapp_local/config.py::TIPOS_PERMITIDOS` aceita (a fila real `temp\whatsapp_fila.json` tem avisos).

## 2. SKILL `hypado-estaticos` — gravar `interativo.pergunta_curta` (tarefa A4)

Arquivo: `.claude\skills\hypado-estaticos\SKILL.md`, na parte que escreve o story interativo do lote
`lotes\AAAA-MM-DD_estaticos.json`. Colar:

```
### Story interativo (chave "interativo" do lote): grave DUAS perguntas

Além de "pergunta" (a pergunta completa, com contexto, como hoje), grave SEMPRE
"pergunta_curta": a pergunta que vai na figurinha de enquete do Instagram.

Regras da "pergunta_curta":
- Até 25 caracteres, contando espaço, acento e pontuação (conte antes de gravar).
- Uma frase só, terminada em "?", que fecha sozinha: dá para entender sem ler a arte nem a
  pergunta completa. Ex.: "O que você faz?" (15), "Vai jogar no dia 1?" (19), "Vice City ou Leonida?" (21).
- Sem emoji, sem "#", sem vocativo ("galera,", "gente,") nem introdução ("me conta:", "e aí,").
- Não terminar em vírgula, dois-pontos ou reticências; nunca cortar palavra no meio.
- "opcoes": 2 a 4, cada uma com até 25 caracteres, sem emoji e sem repetir.

Exemplo:
  "interativo": {
    "pergunta": "Furacão chegando em Leonida. O que você faz?",
    "pergunta_curta": "O que você faz?",
    "opcoes": ["Vou ver de perto", "Fujo pro outro lado"],
    ...
  }

Antes de fechar o lote, rode: python scripts\story_post_lote.py lotes\AAAA-MM-DD_estaticos.json
Tem que terminar com código 0 e mostrar a pergunta escolhida. Se aparecer "NÃO DÁ", arrume
"pergunta_curta"/"opcoes" e rode de novo. Sem "pergunta_curta" o story_post tenta encurtar a
pergunta completa pela última oração com "?"; se nada couber em 25, o story NÃO sai.
```

## 3. SKILL (ou rotina) do story de divulgação — arte pelo `story_artes.py` (tarefa D)

Arquivo: a SKILL que hoje manda o `story_post` subir story de post (ou o `LEIA_story_post.md`, se a
regra viver lá). Colar:

```
Story de divulgação: antes de o story_post subir um story, gere a arte com
`python scripts\story_artes.py render <spec.json>` (spec na LEIA_story_artes.md; 3 modelos:
chamada, maissobre, interacao; 6 canais). Use o `<nome>_zonas.json` que sai ao lado do JPG para
posicionar a figurinha de link (chave "link"/"link_fracao") e a de enquete ("enquete"/"enquete_fracao").
Se o comando devolver código 1, leia a mensagem (em português) e encurte o texto indicado; nunca
ignore o erro para não sair texto cortado. Sem emoji na arte (o gerador tira sozinho).
```

## 4. Rotina nova `hp-radar-fontes` (mensal) e ajuste no SKILL `hp-carros-lancamentos` (tarefa F)

Arquivo: `.claude\` (rotina nova, mensal, dia 1, 7h). Colar:

```
Rotina hp-radar-fontes (mensal, dia 1, 7h), na pasta G:\Meu Drive\Hypado\06 Projeto:
  python radar_fontes\verificar_fontes.py verificar radar_fontes\futebol_fontes_novas.json --gravar
  python radar_fontes\verificar_fontes.py verificar radar_fontes\filmes_fontes_novas.json --gravar
  python radar_fontes\verificar_fontes.py verificar radar_fontes\carros_fontes_novas.json --gravar
  python radar_fontes\verificar_fontes.py verificar radar_fontes\gta_fontes_novas.json --gravar
  (se der erro de certificado: --curl antes de "verificar")
Saída 1 = alguma fonte caiu: abra o JSON, veja "descartadas" e o motivo, e tire a fonte do
07 Canais\radar\<canal>.json ou ache o @handle/feed novo no site oficial.
A cada trimestre, releia radar_fontes\<canal>_candidatos.txt e radar_fontes\RELATORIO_FONTES.md
(seção "O que o PC deve tentar de novo"): salas de imprensa e sites de clube trocam de plataforma.
Nunca inclua Flow Games nem invente id: sem prova, não entra.
```

Arquivo: `.claude\skills\hp-carros-lancamentos\SKILL.md` (endereços conferidos em 01/10/2026). Colar no fim da lista de salas de imprensa:

```
Salas de imprensa conferidas em 01/10/2026:
- Ferrari: https://www.ferrari.com/en-US/media-centre (o /en-EN/media responde 404)
- Hyundai Brasil: https://www.hyundai.com.br/imprensa -> https://hyundai-csa-news.com/ (feed: /feed/)
- Toyota Brasil: https://www.toyotacomunica.com.br/ (feed: /feed/)
- BMW Brasil: https://www.press.bmwgroup.com/brazil (feed: /pressclub/p/br/rss.html?locale=pt&outputChannelId=43)
- McLaren: cars.mclaren.press responde 404 (procurar o endereço novo)
- Nissan: feed global https://global.nissannews.com/en/rss (nissannews.com/pt-BR cai na página global)
Feeds e canais novos prontos: radar_fontes\carros_fontes_novas.json (6 rss + 21 youtube) e os outros 3 canais
(futebol 7 + 13, filmes 8 + 18, gta 1 + 1). Antes de mesclar no 07 Canais\radar\<canal>.json, conferir as
4 entradas marcadas "ja_existe" (CBF @brasil, CONMEBOL Libertadores BR, Paramount Brasil, Rockstar Games).
```
