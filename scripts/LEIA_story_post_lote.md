# story_post_lote.py — a enquete do lote REAL de estáticos (figurinha de 25 caracteres)

O story interativo das 16h do GTA está na chave **`interativo`** de
`lotes\AAAA-MM-DD_estaticos.json` (não num item `story_enquete`, como a rodada 1 supôs).
A pergunta completa tem ~46 caracteres e a figurinha de enquete do Instagram aceita ~25.
Este módulo decide o que vai na figurinha **sem cortar no escuro**.

## Como ele escolhe a pergunta (nesta ordem)

1. `interativo.pergunta_curta`, se existir e couber em 25.
2. Encurta a pergunta completa de forma previsível: tira emoji, vocativo e introdução
   ("Galera,", "Me conta:", "E aí,", ", hein?"), e prefere a **última oração terminada em "?"**
   (`Furacão chegando em Leonida. O que você faz?` → `O que você faz?`). Nunca corta no meio
   de palavra.
3. Se nada couber: **recusa** e explica (`PerguntaImpossivel`). A solução é gravar
   `pergunta_curta` no lote (o SKILL `hypado-estaticos` deve fazer isso).

Opções: 2 a 4, cada uma com até 25 caracteres, sem emoji e sem repetição; opção comprida não é
cortada, é recusada com o motivo.

## Uso

```
python scripts\story_post_lote.py lotes\2026-10-01_estaticos.json            (imprime a decisão)
python scripts\story_post_lote.py lotes\2026-10-01_estaticos.json --json     (a mesma coisa em JSON)
python scripts\story_post_lote.py lotes\2026-10-01_estaticos.json --limite 25 --limite-opcao 25
```

Código de saída: `0` = dá para postar; `1` = não dá (pergunta impossível, opção fora do limite,
lote sem `interativo`, arquivo ilegível). O `story_post.py enquete --dia 2026-10-01` já usa este
módulo; o formato antigo (`story_enquete`) continua valendo como plano B, e `--cortar` continua
sendo o corte por palavra de antes.

Também lista o lote inteiro (`itens_do_lote`): stories (hora, arquivo, tema — "vídeo novo:" vira
`novo_video`), carrossel (tema, arquivos, spec, legenda), threads e comunidade do YouTube. As
chaves `instagram`/`facebook`/`tiktok` desses itens são **texto livre de status**, e saem assim.

## Instalação

1. Copie `story_post_lote.py` para `G:\Meu Drive\Hypado\scripts\` (ao lado do `story_post.py`).
2. Nada de pip: só a biblioteca padrão do Python.
3. Testes: `cd "G:\Meu Drive\Hypado\scripts" ; python -m pytest -q testes\test_story_post_lote.py`
