# story_artes.py: a arte do story, pronta para o celular

É o programa que desenha a imagem de story (1080x1920) de cada canal da HP. Ele deixa
dois retângulos vazios, marcados só por um contorno fino: ali o `story_post.py` solta
a figurinha de **link** e a de **enquete** no Instagram. Nada de importante fica nos
250 px do topo nem nos 350 px da base (onde o Instagram põe o perfil e a caixa de resposta).

## Os 3 modelos (cada um sai em qualquer um dos 6 canais)

| Modelo | O que mostra | Para quê |
|---|---|---|
| `chamada` | capa do post num cartão, rótulo ("NOVO REEL"), chamada curta com a palavra `*destacada*`, seta "toque pra ver" apontando para a zona do link | divulgar o post que acabou de sair |
| `maissobre` | miniatura do post, um dado forte grande (ex.: "R$ 80 mi"), 2 a 4 fatos com marcador, botão "Salva o post" | continuar o assunto |
| `interacao` | pergunta grande e a zona vazia da enquete; opcional "você prefere" com duas fotos lado a lado | puxar resposta |

Cada canal tem a cara dele (cores e fontes da tabela da marca, `hpbase/marca.py`): GTA com
céu de noite e título rosa→laranja; Futebol com caixa escura e verde HP (ou a cor do clube);
Filmes com pílula e caixa amarelas; Receitas com faixas amarelas e letra serifada; Carros com
etiqueta vermelha e frase em itálico; Destinos em azul com curvas e ciano.

## Como usar (PowerShell, na pasta `G:\Meu Drive\Hypado`)

1. Peça um spec de exemplo e salve num arquivo:
   `python scripts\story_artes.py spec-exemplo > meu_story.json`
2. Abra o `meu_story.json` no Bloco de Notas e troque os campos:
   - `canal`: gta, futebol, filmes, receitas, carros ou destinos
   - `tipo`: chamada, maissobre ou interacao
   - `capa`: caminho da imagem do post (pode deixar vazio: ele desenha um fundo do canal)
   - `chamada` (até 45 letras), `fatos` (2 a 4, até 70 letras cada), `pergunta` (até 60 letras)
   - `*palavra*` entre asteriscos = palavra na cor do canal
   - `figurinhas`: `["link"]` ou `["link", "enquete"]` (com a enquete o cartão encolhe para sobrar a zona)
   - `cor_destaque`: só no Futebol, a cor do clube do post (ex.: `"#C8102E"`)
   - `credito_foto`: aparece em cima da foto, no canto; `foco`: `[0.5, 0.3]` = que parte da foto manter
   - `saida`: pasta onde gravar; `nome`: começo do nome dos arquivos
3. Gere: `python scripts\story_artes.py render meu_story.json`

Saem três arquivos na pasta `saida`: `<nome>.jpg` (a arte), `<nome>_zonas.json` (onde ficam
as zonas das figurinhas, em pixels e em fração da tela, para o `story_post`) e, se pedir
`--png`, `<nome>.png`. A mesma entrada gera sempre a mesma imagem, byte a byte.

Outros comandos:
- `python scripts\story_artes.py todas futebol C:\saida` — os 3 modelos do canal, com textos de exemplo.
- `python scripts\story_artes.py exemplos C:\saida` — os 18 (3 x 6) e a `_prancha_story.jpg` com
  todos em miniatura, para conferir de olho.

## O que ele recusa (e avisa em português)

- Texto comprido demais: ele diminui a letra até um mínimo; se ainda não couber, para e explica
  qual campo encurtar (nunca deixa texto cortado ou saindo da margem).
- Emoji não entra na arte (é tirado sozinho). Canal ou tipo errado, figurinha que não existe,
  `maissobre` com enquete, menos de 2 ou mais de 4 fatos: erro com explicação.
- `cor_destaque` fora do Futebol é ignorada (sai um aviso).

Código de saída: `0` deu certo, `1` erro.

## Instalação

Precisa de Python 3.12 com `pillow` e `numpy` (`pip install pillow numpy`). Copie
`story_artes.py`, `story_artes_base.py`, `story_artes_canais.py`, `story_artes_modelos.py` e
`story_artes_exemplos.py` para `G:\Meu Drive\Hypado\scripts\` (e o teste para `scripts\testes\`).
Ele acha o `hpbase` sozinho (`06 Projeto\app\hp_studio_nuvem`); se mudar de lugar, defina `HP_APP`.
As fontes são as do PC (`06 Projeto\marca\fontes` e `C:\Windows\Fonts`); onde faltar alguma,
ele usa a substituta mais parecida e não para.

Testes: `cd scripts` e `python -m pytest -q testes\test_story_artes.py`.
