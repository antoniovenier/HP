# Página de links HP Canais: passo a passo no Google Sites

**Página:** https://sites.google.com/view/hpcanais
**Objetivo:** cada canal com um fundo clarinho e um botão na cor do canal, conferido no celular.
**Tempo:** uns 40 minutos na primeira vez.

> **Importante:** o Google Sites não se edita por código. O script só **gera as imagens**; quem aplica é você, seguindo os passos abaixo. **Login é sempre você que faz.** O Claude nunca entra na sua conta, nunca digita senha nem código.

Se algum botão ou menu estiver com um nome um pouco diferente, é porque o Google muda os nomes de vez em quando. Procure pelo **ícone** descrito entre parênteses.

---

## Parte A: gerar as imagens no PC (passos 1 a 9)

1. **(Opcional) Escolha uma foto para cada canal.** Não é obrigatório: sem foto, o script faz um degradê clarinho na cor do canal, com um desenho bem leve:
   - GTA: listras;
   - Futebol: linhas do campo;
   - Filmes: furinhos de filme;
   - Receitas: bolinhas;
   - Carros: quadriculado;
   - Destinos: ondas.
2. Se for usar foto:
   - Use foto **sua** ou **livre de direitos**.
   - No Futebol, **nunca** use imagem de transmissão de TV.
   - No GTA, **nada de vazamento**.
   - Salve em `H:\HypadoLocal\pagina_links\fotos\` com o nome do canal: `gta.jpg`, `futebol.jpg`, `filmes.jpg`, `receitas.jpg`, `carros.jpg`, `destinos.jpg`.
   - Também aceita `.png` e `.webp`. A foto vai ser clareada sozinha: fica bem clarinha e um pouco desfocada, de propósito, para o botão aparecer.
3. Abra o **PowerShell**: aperte a tecla Windows, digite `PowerShell` e aperte Enter.
4. Digite a linha abaixo e aperte Enter:
   `cd "G:\Meu Drive\Hypado"`
5. Confira as cores. Digite a linha abaixo e aperte Enter:
   `python scripts\pagina_links\gerar_fundos.py contraste`
   Devem aparecer **6 linhas terminando em "OK (AA)"**. Isso quer dizer que o texto do botão fica legível: contraste de pelo menos 4,5 para 1, o mínimo de acessibilidade. Se aparecer **FALHOU**, pare aqui e mostre a mensagem para o Claude.
6. Gere as imagens. Digite a linha abaixo e aperte Enter:
   `python scripts\pagina_links\gerar_fundos.py`
   Leva uns 5 segundos. No fim aparece uma lista com os arquivos.
7. Abra a pasta `H:\HypadoLocal\pagina_links\` no Explorador de Arquivos. Lá dentro você vai ver:
   - `fundos\`: 2 imagens por canal. A `…_1600x400.jpg` é a faixa, para o fundo da seção. A `…_1080x1080.jpg` é o quadrado, para item ou cartão.
   - `botoes\`: 1 botão por canal (`…_botao.png`, 1000 × 200), na cor do canal e com o nome escrito.
   - `cartoes\`: 1 imagem pronta por canal (`…_cartao.jpg`), com a faixa clarinha e o botão já em cima. É o jeito mais fácil (Parte E).
   - `previa.html`: mostra como vai ficar no celular.
8. Dê dois cliques em `previa.html`. Abre no navegador uma coluna estreita, do tamanho de um celular, com os 6 canais. Se não gostou de algum fundo, troque a foto do passo 2 e repita o passo 6.
9. **(Opcional) Botão com outro texto.** Por exemplo, "Receitas no TikTok":
   `python scripts\pagina_links\gerar_fundos.py botao receitas "Receitas no TikTok"`
   O arquivo novo vai para a pasta `botoes\`.

---

## Parte B: abrir o site para editar (passos 10 a 17)

10. No PC, abra o **Chrome**.
11. Entre em **sites.google.com**.
12. Se pedir login, **você** entra com a conta Google dona do site (a da Hypado). Se pedir código de verificação, é você quem digita.
13. Em **"Sites recentes"**, clique no site da página de links. O nome aparece como "hpcanais" ou o título que você deu.
14. Abre o **editor**: a página fica no meio e, à direita, um painel com 3 abas: **Inserir**, **Páginas** e **Temas**.
15. **Não achou o site na lista?** Abra https://sites.google.com/view/hpcanais logado. Procure o **lápis** ("Editar este site"), que costuma ficar num canto da tela, e clique nele.
16. **Antes de mexer, guarde os links atuais.** Clique em cada botão que já existe. Na barrinha que aparece, clique no **lápis** (Editar) e copie o link. Cole num Bloco de Notas com o nome do canal ao lado. Assim nenhum link se perde.
17. **Rede de segurança.** Se algo der errado, dá para voltar atrás:
    1. no topo, clique nos **três pontinhos (⋮)**;
    2. escolha **"Histórico de versões"**;
    3. clique numa versão de antes;
    4. clique em **"Restaurar esta versão"**.

---

## Parte C: tema (cor geral do site) (passos 18 a 23)

18. No painel da direita, clique na aba **Temas**.
19. O tema que está em uso fica marcado. Embaixo dele aparecem **bolinhas de cor**.
20. Clique na bolinha de **cor personalizada**: fica no fim da fila, com um "+" ou um arco-íris. Digite `#141413` (um quase-preto) e confirme. Se o seu tema não tiver cor personalizada, escolha a bolinha **mais escura**.
21. **Por que escura?**
    - Os fundos novos são clarinhos, então títulos e botões comuns ficam fáceis de ler em cor escura.
    - O Google Sites **não deixa escolher uma cor diferente para cada botão**: todo botão comum usa a mesma cor do tema. Mesmo o **tema personalizado** só dá uma cor geral para o site.
    - Por isso, a cor de cada canal vai numa **imagem de botão** com link (Parte E). Com imagem, cada canal fica com a sua cor.
22. Em **"Estilo da fonte"**, deixe como está.
23. Não precisa salvar: o Google Sites salva sozinho (aparece "Todas as alterações foram salvas" no topo).

---

## Parte D: fundo clarinho em cada seção (passos 24 a 34)

Aqui cada canal é uma **seção** da página: a faixa com o título e os botões dele. Se hoje tudo está numa seção só, faça os passos 24 a 26 para separar.

24. Passe o mouse sobre a seção atual. À **esquerda** dela aparece uma barrinha vertical com ícones:
    - **paleta** = plano de fundo;
    - **dois quadradinhos** = duplicar;
    - **lixeira** = excluir.
25. Clique nos **dois quadradinhos (Duplicar seção)** até ter **6 seções**, uma por canal.
26. Em cada seção, deixe só o que é daquele canal. Apague o resto: clique no item e depois na **lixeira** da barrinha do item.
27. Agora os fundos. Passe o mouse sobre a seção do **GTA 6** e clique na **paleta (Plano de fundo da seção)**.
28. Aparecem as opções **Estilo 1**, **Estilo 2**, **Estilo 3** e **Imagem**. Clique em **Imagem**.
29. Clique em **"Alterar imagem"** (ou "Selecionar imagem") e depois em **"Enviar"**. Se aparecer "Fazer upload", é a mesma coisa.
30. Na janela que abrir, vá até `H:\HypadoLocal\pagina_links\fundos\`, escolha **`gta_1600x400.jpg`** e clique em **Abrir**.
31. Espere carregar. A seção fica com o fundo rosa clarinho.
32. **Confira se o texto da seção continua fácil de ler.** Às vezes o Google escurece a imagem de fundo ou deixa as letras brancas, e o fundo clarinho some ou o texto fica apagado. Se isso acontecer:
    - **a)** abra a paleta de novo e procure uma opção de **"Legibilidade"** ou **"Ajustar"**, para tirar o escurecimento, se existir; **ou**
    - **b)** apague o título em letra branca dessa seção: o nome do canal já vai escrito no botão (Parte E); **ou**
    - **c)** volte a seção para **Estilo 1** e use o **cartão pronto** (passos 45 a 48). É o mais garantido.
33. Repita os passos 27 a 32 para os outros canais. Use a faixa de cada um:

    | Canal | Fundo (faixa) |
    |---|---|
    | GTA 6 \| HP | `fundos\gta_1600x400.jpg` |
    | Futebol \| HP | `fundos\futebol_1600x400.jpg` |
    | Filmes e Séries \| HP | `fundos\filmes_1600x400.jpg` |
    | Receitas \| HP | `fundos\receitas_1600x400.jpg` |
    | Carros \| HP | `fundos\carros_1600x400.jpg` |
    | Destinos \| HP | `fundos\destinos_1600x400.jpg` |

34. **Se o seu site usa "itens" (cartões com foto) em vez de seções:** use o **quadrado** `…_1080x1080.jpg` do canal como imagem do item:
    1. selecione a imagem antiga do item;
    2. clique nos **três pontinhos (⋮)** dela;
    3. escolha **"Substituir imagem"**;
    4. clique em **"Enviar"** e escolha o quadrado do canal.

    Se não existir "Substituir", apague a antiga e insira a nova pelo passo 37.

---

## Parte E: botões na cor de cada canal (passos 35 a 48)

**Jeito 1: imagem de botão com link.** Fica em cima do fundo da seção.

35. Tenha à mão o Bloco de Notas com os links do passo 16.
36. No painel da direita, clique em **Inserir**.
37. Clique em **Imagens** e depois em **Enviar**.
38. Escolha `H:\HypadoLocal\pagina_links\botoes\gta_botao.png` e clique em **Abrir**.
39. A imagem entra na página. **Arraste** para dentro da seção do GTA, no lugar do botão antigo.
40. Puxe os cantinhos da imagem para ela ficar **larga**: de preferência a largura toda da coluna. No celular ela se ajusta sozinha. **Não use "Cortar"**, senão o botão perde as pontas arredondadas.
41. Com a imagem selecionada, aparece uma barrinha em cima dela. Clique na **corrente (🔗 Inserir link)**, cole o link do GTA que você guardou e clique em **Aplicar**.
42. Coloque o **texto alternativo** (ajuda quem usa leitor de tela):
    1. com a imagem selecionada, clique nos **três pontinhos (⋮)**;
    2. escolha **"Texto alternativo"** ou "Adicionar texto alternativo";
    3. escreva, por exemplo, `GTA 6 | HP: abrir o perfil`;
    4. clique em **Aplicar**.

    Se não achar essa opção, pode pular.
43. Apague o botão antigo: clique nele e depois na **lixeira**.
44. Repita os passos 36 a 43 para cada canal, com o botão e o link certos:

    | Canal | Botão |
    |---|---|
    | GTA 6 \| HP | `botoes\gta_botao.png` |
    | Futebol \| HP | `botoes\futebol_botao.png` |
    | Filmes e Séries \| HP | `botoes\filmes_botao.png` |
    | Receitas \| HP | `botoes\receitas_botao.png` |
    | Carros \| HP | `botoes\carros_botao.png` |
    | Destinos \| HP | `botoes\destinos_botao.png` |

**Jeito 2: cartão pronto (o mais garantido).** O fundo clarinho e o botão já vêm juntos numa imagem só.

45. Deixe a seção em **Estilo 1** (fundo liso). Faça pela paleta, como no passo 28.
46. Clique em **Inserir**, depois em **Imagens** e em **Enviar**, e escolha `cartoes\gta_cartao.jpg`.
47. Estique a imagem na largura toda e coloque o link, como no passo 41. Coloque também o texto alternativo, como no passo 42.
48. Repita para cada canal com o `cartoes\<canal>_cartao.jpg` dele.

---

## Parte F: conferir no celular e publicar (passos 49 a 60)

49. No topo do editor, clique no **olho (Visualizar)**.
50. Embaixo, à direita, aparecem 3 ícones: **celular**, **tablet** e **tela grande**. Clique no **celular**.
51. Role a página toda e confira:
    - cada canal tem o fundo **clarinho** aparecendo;
    - o botão aparece **inteiro**: não cortado e sem sair da tela;
    - dá para ler tudo **sem aproximar**.
52. Toque em cada botão. Tem de abrir o **perfil certo**, normalmente numa aba nova. Feche a aba e volte.
53. Saia da visualização pelo **X** ou por **"Sair da visualização"**.
54. Se algo estiver errado, arrume agora: volte à Parte D ou E.
55. Clique no botão azul **"Publicar"**, no canto de cima à direita. Na janela, clique em **"Publicar"** de novo. O endereço continua o mesmo.
56. Espere **1 a 2 minutos**.
57. **No seu celular de verdade**, abra o Chrome (ou o Safari, no iPhone) e digite `sites.google.com/view/hpcanais`.
58. Faça o mesmo teste do passo 51: role a página toda e toque em **cada botão**.
59. Teste também **pelo link da bio do Instagram**. É assim que o público chega: abre dentro do próprio Instagram. Toque no link da bio de um dos perfis e confira que a página abre bonita.
60. Teste com o **Wi-Fi desligado**, só no 4G/5G. A página deve abrir em poucos segundos.

---

## Checklist final (marque tudo antes de dar por encerrado)

| Canal | Fundo clarinho | Botão na cor certa | Texto legível | Link certo | Conferido no celular |
|---|---|---|---|---|---|
| GTA 6 \| HP | ☐ | ☐ | ☐ | ☐ | ☐ |
| Futebol \| HP | ☐ | ☐ | ☐ | ☐ | ☐ |
| Filmes e Séries \| HP | ☐ | ☐ | ☐ | ☐ | ☐ |
| Receitas \| HP | ☐ | ☐ | ☐ | ☐ | ☐ |
| Carros \| HP | ☐ | ☐ | ☐ | ☐ | ☐ |
| Destinos \| HP | ☐ | ☐ | ☐ | ☐ | ☐ |

- ☐ `gerar_fundos.py contraste` deu 6 × "OK (AA)".
- ☐ Nenhum link antigo se perdeu (compare com o Bloco de Notas do passo 16).
- ☐ Todos os botões têm texto alternativo (passo 42), ou você decidiu pular.
- ☐ Nomes com acento certo: "Filmes e **Séries**".
- ☐ A página não "anda para os lados" no celular (nada passa da largura da tela).
- ☐ Publicado (passo 55) e conferido no celular real (passos 57 a 60).
- ☐ Testado pelo link da bio do Instagram (passo 59).
- ☐ Se tiver outro celular em casa (Android ou iPhone), conferido nele também.

## Problemas comuns

| O que aconteceu | O que fazer |
|---|---|
| O texto da seção ficou branco e apagado em cima do fundo clarinho | Passo 32: tire o escurecimento, apague o título (o nome já está no botão) ou use o cartão pronto (passos 45 a 48). |
| O botão ficou pequeno no celular | No editor, puxe os cantinhos da imagem até a largura toda (passo 40). |
| O fundo aparece cortado nas laterais no celular | É normal: o Google corta o fundo para encher a seção. Os fundos são padrões suaves, feitos para aguentar esse corte. |
| O botão abre o perfil errado | Clique no botão, depois na **corrente (🔗)**, e troque o link. Depois clique em **Publicar**. |
| O botão "Publicar" está apagado | Não há nada novo para publicar: já está no ar. |
| O Google pediu login ou código | É **você** quem digita. O Claude nunca faz login por ninguém. |
| Quero outra cor para um canal | Troque a `cor` em `scripts\pagina_links\cores_canais.json`. Rode o passo 5 (se der FALHOU, use a cor de texto sugerida) e depois o passo 6. Reenvie as imagens (Partes D e E). |
