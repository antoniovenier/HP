# Página de links (`sites.google.com/view/hpcanais`): fundos e botões

Ticket: `20260929-170836-pagina-de-links-hpcanais`. O pedido: foto de fundo clarinha em cada item e botões na cor de cada canal, conferidos no celular.

O Google Sites **não se edita por código**. Por isso, aqui só se **gera as imagens**, e o Antônio aplica seguindo o [`PASSO_A_PASSO.md`](PASSO_A_PASSO.md). Ninguém faz login por ele.

| Arquivo | O que é |
|---|---|
| `gerar_fundos.py` | Gera os fundos clarinhos, os botões e os cartões de cada canal, mais uma prévia em HTML. |
| `cores_canais.json` | Cor de cada canal e cor do texto do botão, com o contraste anotado. |
| `PASSO_A_PASSO.md` | Manual leigo, com 60 passos e checklist, de como aplicar no Google Sites e conferir no celular. |

## Instalação

- Precisa de Python 3.12 e do **Pillow** (`pip install pillow`). É a única dependência.
- O `hpbase` do app é achado sozinho: variável `HP_APP`, ou `..\app\hp_studio_nuvem`, ou `..\06 Projeto\app\hp_studio_nuvem`.
- A fonte dos botões é achada sozinha. No Windows usa Segoe UI Bold ou Arial Bold; para usar outra, defina `HP_FONTE`.

## Comandos

```powershell
python scripts\pagina_links\gerar_fundos.py                     # gera tudo (6 canais)
python scripts\pagina_links\gerar_fundos.py contraste           # confere as cores (6 × "OK (AA)")
python scripts\pagina_links\gerar_fundos.py gerar --canal receitas --foto receitas=C:\fotos\bolo.jpg
python scripts\pagina_links\gerar_fundos.py gerar --simular     # só mostra o que faria
python scripts\pagina_links\gerar_fundos.py botao receitas "Receitas no TikTok"
python scripts\pagina_links\gerar_fundos.py --help
```

## O que ele grava

A pasta de saída é `H:\HypadoLocal\pagina_links\` (ou `HP_LOCAL\pagina_links`):

- `fundos\<canal>_1600x400.jpg`: faixa, para o fundo da seção.
- `fundos\<canal>_1080x1080.jpg`: quadrado, para item ou cartão.
- `botoes\<canal>_botao.png`: botão de 1000 × 200, fundo transparente, pontas arredondadas, na cor do canal, com o nome.
- `cartoes\<canal>_cartao.jpg`: a faixa com o botão já em cima. É uma imagem só, com link, e é o jeito mais garantido no Google Sites.
- `previa.html`: os 6 canais numa coluna do tamanho de um celular, para conferir antes de subir.

### Fundo com foto

Para usar foto, ponha em `pagina_links\fotos\<canal>.jpg|png|webp`, ou passe `--foto canal=arquivo`. O script:

- corta a foto no tamanho;
- aplica um **leve desfoque**;
- dá um toque de 8% da cor do canal;
- mistura com **branco entre 75% e 85%** (quanto mais escura a foto, mais branco).

### Fundo sem foto

Sem foto, sai um **degradê suave** na cor do canal, com um **padrão discreto** a 10%:

- GTA: listras;
- Futebol: linhas do campo;
- Filmes: furinhos de filme;
- Receitas: bolinhas;
- Carros: quadriculado;
- Destinos: ondas.

Os dois casos terminam com **luminância média acima de 200** (de 255). Na conta real ficou entre 218 e 247.

## Cores propostas (as mesmas do painel HP, para a identidade ser uma só)

| Canal | Botão | Texto do botão | Contraste (WCAG) | Contorno (sobre o branco, ≥ 3:1) |
|---|---|---|---|---|
| GTA 6 \| HP | `#FF3D8B` | `#141413` | 5,52:1 AA | `#FF3D8B` |
| Futebol \| HP | `#1ED760` | `#141413` | 9,61:1 AA | `#18AA4C` |
| Filmes e Séries \| HP | `#F5B301` | `#141413` | 9,95:1 AA | `#BF8C01` |
| Receitas \| HP | `#FF7A1A` | `#141413` | 7,07:1 AA | `#ED7118` |
| Carros \| HP | `#FF3B3B` | `#141413` | 5,21:1 AA | `#FF3B3B` |
| Destinos \| HP | `#00C2D1` | `#141413` | 8,46:1 AA | `#00A3B0` |

Como o contraste é garantido no código:

- A fórmula é a oficial da WCAG 2.x (luminância relativa).
- O `carregar_cores()` **recusa** qualquer canal com menos de 4,5:1 e sugere a cor de texto que passa.
- Ele também recusa se o número anotado em `contraste` não bater com o cálculo.
- O **contorno** do botão é calculado sozinho: escurece a cor até dar 3:1 contra o branco. Assim, até o botão amarelo aparece bem sobre o fundo claro.
- Com texto branco, essas cores ficariam entre 1,9 e 3,5:1 e **não** passariam. Por isso o texto é escuro.

## Modo sombra e integração

Não há o que "sombrear": o script não age no mundo real, só grava imagens numa pasta local. O `--simular` mostra o que seria gerado, sem gravar nada.

Não entra no `hp` nem no motor. É uma tarefa de uma vez só, rodada à mão quando mudar foto ou cor. Se um dia quiser pôr no motor, o gancho é `executar(trabalho) -> dict`, que chama `gerar_tudo(**trabalho)` e devolve o dicionário de arquivos.

Log em `H:\HypadoLocal\app\logs\pagina_links_AAAA-MM-DD.log`.

## Testes

```powershell
cd "G:\Meu Drive\Hypado\06 Projeto\app"
python -m pytest -q "..\..\scripts\testes\test_pagina_links.py"
```

Ajuste o caminho relativo ao seu PC. Os testes conferem:

- o contraste ≥ 4,5 de todas as cores (e a fórmula, com valores conhecidos);
- os tamanhos certos dos fundos (1600 × 400 e 1080 × 1080);
- a luminância média > 200, com e sem foto (inclusive foto escura);
- os botões de 1000 × 200, com a cor e o texto presentes;
- os cartões;
- a prévia;
- o modo simular;
- a linha de comando.
