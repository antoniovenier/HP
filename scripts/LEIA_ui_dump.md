# ui_dump — ler a tela do celular a partir do texto do ui.py

`scripts\ui_dump.py` lê a saída do `H:\HypadoLocal\android\ui.py` (uma linha por
elemento: `x,y | classe | texto | desc | id | clic`) e devolve a lista de nós
`{x, y, classe, texto, desc, id, clicavel}` — o mesmo que o `ui.ler()` devolve,
só que sem adb, sem emulador e sem rede. Serve para testar decisões de toque
sobre um dump salvo e para o `story_post` conferir ids (ex.: o carimbo real do
story recém-publicado é `3m`, o botão de destaque é `toolbar_highlights_button`
com descrição `Highlight`).

## Uso

```
python scripts\ui_dump.py H:\HypadoLocal\android\telas\ui_salvo.txt [filtro]
```

Imprime os nós em JSON (com `filtro`, só os que têm esse trecho no id, texto ou
descrição). De outro script:

```python
from ui_dump import ler_arquivo, achar, centro
nos = ler_arquivo("ui_salvo.txt")
x, y = centro(achar(nos, id="toolbar_highlights_button"))   # (530, 2190) no dump real
```

Regras: nunca use coordenada fixa — sempre a do dump da tela atual; a busca por
texto/descrição ignora maiúscula e acento e, com `contem=True`, aceita trecho.
Linha fora do formato é ignorada. Instalação: copiar `ui_dump.py` para
`G:\Meu Drive\Hypado\scripts\`; só Python 3.11+, sem biblioteca extra.
