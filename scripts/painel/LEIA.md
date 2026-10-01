# Painel público: peças para o `montar_painel_publico.py`

Tickets: `20260929-164354-painel-publico-sem-artifactdata`, `20260930-121636…selo`, `20260930-103550…moldura de iPhone`.

O `montar_painel_publico.py` continua igual (não foi reescrito). Estas peças encaixam nele:

| Arquivo | Para que serve |
|---|---|
| `espelho_banco.py` | Banco do painel em SQLite local, com a mesma API do ArtifactData (`set/update/get/list/query/delete/batch`). Exporta tudo num `painel_dados.json`. |
| `selo_abas.py` + `selo_abas.js` | Correção do selo das abas: mostra a contagem real e some no 0. |
| `selo_casos.json` | Casos de teste do selo. Python e JS rodam os mesmos casos. |
| `previa_celular.js` + `previa_celular.css` | Prévia do post numa moldura de celular, com uma aba para cada rede. |
| `previa_celular.py` | Embute a prévia no HTML do painel e liga o clique da capa. Também regrava a demo. |
| `previa_demo.html` | Demo autocontida. Abra com dois cliques no navegador; funciona sem internet. |

## Instalação

- Nada para instalar: só Python 3.12 (o `sqlite3` já vem com ele) e o `hpbase` do app.
- Os scripts acham o `hpbase` sozinhos, nesta ordem:
  1. a variável `HP_APP`;
  2. `..\app\hp_studio_nuvem`;
  3. `..\06 Projeto\app\hp_studio_nuvem`.
  Se a pasta for outra, defina: `$env:HP_APP = "G:\Meu Drive\Hypado\06 Projeto\app"`.
- Testes: entre na pasta `app` e rode `python -m pytest -q <scripts>\testes\test_painel_*.py`. O `node` é opcional; sem ele, os testes do JS são pulados.
- Logs: `H:\HypadoLocal\app\logs\painel_espelho_AAAA-MM-DD.log`. O log registra só contagens, nunca o conteúdo.

---

## 1. Espelho local do banco (a rotina roda sem ArtifactData)

### O que descobri no painel publicado

O HTML do painel **não usa ArtifactData em tempo de execução**. Ele baixa o arquivo `dados.json`, publicado junto dele, com estas chaves:

- `gerado`, `dias`;
- `canais{gta,…}`, `agenda{AAAA-MM-DD:{itens}}`;
- `sistema{pendencias,producao,saude}`;
- `avatares{…}`, `eventos`.

O ArtifactData só aparece na rotina que monta esse arquivo. O espelho troca essa parte.

- Banco: `H:\HypadoLocal\app\painel_espelho.sqlite`. Tabela `docs(colecao, doc_id, dados JSON, atualizado_em, versao)`.
- Export: `H:\HypadoLocal\app\painel_dados.json`, no **mesmo formato do `dados.json`**: cada coleção vira uma chave de topo, com `{doc_id: dados}`. Traz também `gerado` e `_espelho` (assinatura e contagens). O `dias` quem calcula é o `montar` (hoje já é assim).
- Um documento pode ser objeto, texto ou lista. Exemplo: `avatares/gta` é o texto `data:image/webp…`.
- **Idempotente**:
  - gravar o mesmo conteúdo não muda a versão nem a data;
  - importar o mesmo arquivo duas vezes não muda nada;
  - `exportar()` devolve `mudou: false` quando nada mudou. Nesse caso a rotina **pode pular a publicação**, o que economiza tokens.
- **Transacional**:
  - `batch([...])` e `importar(...)` gravam tudo ou nada: qualquer erro desfaz o lote inteiro;
  - `with banco.transacao(): ...` junta várias chamadas numa gravação só.
- **Sem segredo**: o painel é público. O espelho **recusa** gravar:
  - um campo chamado `token`, `access_token`, `senha`, `password`, `secret`, `api_key`…;
  - um valor com cara de token (`EAA…`, `AIza…`, `ya29.…`, `Bearer …`, `access_token=`).

  A mensagem de erro nunca mostra o valor.

### Primeira carga (uma vez só, fora de rotina)

O jeito mais simples é importar o próprio `dados.json` publicado, porque ele já é o estado completo do painel:

```powershell
python scripts\painel\espelho_banco.py importar "<pasta do painel>\dados.json"
```

As chaves `gerado` e `dias` são ignoradas de propósito.

Se houver dados que **só** existem no banco do ArtifactData, peça à sessão HP GESTÃO, uma vez e fora de rotina: *"liste cada coleção do banco do painel com ArtifactData e grave em `H:\HypadoLocal\app\painel_export.json`"*. Depois rode `importar painel_export.json`.

O importador aceita todos estes formatos:

- `{"colecao": {"id": {...}}}`;
- `{"colecoes": {...}}`;
- `{"colecao": [{"id": "x", ...}]}`;
- `{"colecao": {"documents": [...]}}`;
- `[{"collection": "c", "doc_id": "x", "data": {...}}]`.

### Na rotina (no lugar do ArtifactData)

| ArtifactData | Espelho (Python) | Espelho (linha de comando) |
|---|---|---|
| set | `b.set("canais", "gta", {...})` | `espelho_banco.py set canais gta --arquivo gta.json` |
| update | `b.update("canais", "gta", {...}, profundo=True)` | `espelho_banco.py update canais gta --arquivo x.json --profundo` |
| get | `b.get("canais", "gta")` | `espelho_banco.py get canais gta` |
| list | `b.list("agenda")` | `espelho_banco.py listar agenda` |
| query | `b.query("agenda", {"status": "postado"}, ordenar="hora")` | `espelho_banco.py consultar agenda "{...}"` |
| delete | `b.delete("canais", "gta")` | `espelho_banco.py apagar canais gta` |
| batch | `b.batch([{"op": "set", "colecao": ..., "doc_id": ..., "dados": {...}}])` | `espelho_banco.py batch lote.json` |

Operadores do `query`: `$eq $ne $gt $gte $lt $lte $in $nin $existe $contem`. Um ponto entra no campo de dentro, como em `"redes.instagram.seguidores"`.

Exemplo de gancho dentro do `montar_painel_publico.py`:

```python
import json, sys
sys.path.insert(0, r"G:\Meu Drive\Hypado\scripts\painel")
from espelho_banco import EspelhoBanco
from selo_abas import limpar_pendencias, corrigir_html_painel
from previa_celular import ligar_no_painel

with EspelhoBanco() as banco:
    banco.update("canais", "gta", {"status": "ok", "prontos": 3})   # o que antes ia para o ArtifactData
    r = banco.exportar()                  # {"caminho", "assinatura", "mudou", "documentos"}

dados = json.loads(open(r["caminho"], encoding="utf-8").read())
dados["dias"] = dias_calculados           # o que o montar já calcula hoje
limpar_pendencias(dados)                  # selo: tira pendência vazia na origem
# ... grava dados como dados.json na pasta do painel (como hoje) ...

html = modelo_html                        # o HTML que o montar já gera
html, rel_selo = corrigir_html_painel(html)
html, rel_previa = ligar_no_painel(html)
```

**Opcional: embutir os dados no HTML** (build sem nenhuma chamada em tempo de execução). Rode `embutir_no_html(html, dados)` ou `espelho_banco.py embutir painel.html`. Isso põe um `<script type="application/json" id="painel-dados">` antes do código do painel. No `carregar()` do painel, troque o `fetch("dados.json…")` por:

```js
const emb = document.getElementById("painel-dados");
if (emb) E.dados = JSON.parse(emb.textContent);
else { const r = await fetch("dados.json?t=" + Date.now(), {cache:"no-store"}); if(!r.ok) throw new Error(r.status); E.dados = await r.json(); }
```

Com os dados embutidos, cada atualização precisa republicar o HTML. Quem já está com a página aberta recebe a versão nova sozinho. Continuar publicando o `dados.json` separado também funciona, e sai mais leve.

### Modo sombra (7 dias antes de desligar o ArtifactData)

1. Deixe a rotina de hoje como está. Em paralelo, grave também no espelho.
2. Uma vez por dia, confira:

   ```powershell
   python scripts\painel\espelho_banco.py comparar "<dados.json publicado hoje>"
   ```

   O comando termina com código 0 quando está igual e 1 quando há diferença. Ele lista `diferentes`, `so_no_arquivo` e `so_no_espelho`.
3. Com 7 dias seguidos de `"iguais": true`, troque as chamadas do ArtifactData pelo espelho.

**PowerShell 5.1** come as aspas do JSON passado na linha de comando. Use `--arquivo dados.json`, ou escreva `'{\"campo\": 1}'`.

---

## 2. Selo das abas ("Não urgentes" vazia mostrando "1")

**Regra:** o selo mostra a contagem **real** de itens da aba e **some quando é 0**.

### Causa, confirmada com o painel publicado

Rodei o HTML publicado com um `dados.json` de teste. Resultado: com uma pendência vazia (`""`) em `sistema.pendencias.voce`, a aba aparece como **"Não urgentes 1"** e a lista mostra um item vazio com o numerador amarelo "1". Os três motivos:

1. O selo é `<b class="num">${g[k].length}</b>`. Ele conta tudo o que está no array, inclusive item vazio, e mostra até o "0".
2. O item vazio nasce na origem. Em Python, `"".split("\n")` dá `[""]`, de tamanho 1. Um `{"texto": ""}`, `"Nenhum item"` ou `"—"` também vira 1. Sem data, esse item cai no grupo `nao` (Não urgentes).
3. Outra armadilha comum: `el.hidden = true` não esconde se o CSS tiver `.num{display:inline-flex}`. O `renderSelo` usa `hidden` **e** `display:none`.

### Como aplicar (as três juntas são o ideal)

1. **Na origem.** Antes de gravar o `dados.json`, rode `selo_abas.limpar_pendencias(dados)`. Ou, pela linha de comando: `python scripts\painel\selo_abas.py limpar dados.json`.
2. **No HTML gerado.** Rode `html, rel = selo_abas.corrigir_html_painel(html)`. Ele:
   - embute o `selo_abas.js` antes do código do painel;
   - troca o selo por `${SeloAbas.htmlSelo(SeloAbas.contarSelo(g, k))}`;
   - põe `if(!SeloAbas.ehItemReal(o.texto)) continue;` em `tarefasPorDia`.

   É idempotente. Se o modelo mudar, só avisa (`"nao_encontrado"`) e não quebra nada. Pela linha de comando: `selo_abas.py corrigir painel.html`.
3. **Em HTML montado em Python.** `html_selo(n)` devolve `""` quando `n == 0`. `html_aba(rotulo, itens, chave)` já monta a aba inteira.

No JS, para outras abas: `SeloAbas.contarSelo(itens, aba)` e `SeloAbas.renderSelo(el, n)`. O `contarSelo` aceita:

- uma lista;
- um objeto `{aba: lista}`;
- um texto com um item por linha;
- uma NodeList.

Não contam: `null`, texto vazio, "Nenhum item", "Nada aqui.", "carregando…", "—", `{placeholder: true}`. Frases de verdade, como "Nada de trailer puro…", **contam**.

---

## 3. Prévia do post em moldura de celular

Clicar na capa abre um modal com um celular genérico: formato de smartphone com notch, **sem marca**. Em cima fica uma barra com as redes do post. As redes possíveis são:

- Instagram Reels, Instagram Feed e Instagram Story;
- TikTok;
- YouTube Shorts;
- Facebook, Facebook Reels e Facebook Story;
- Threads;
- Pinterest.

Cada rede mostra como o post fica:

- **Proporção:** 9:16 (Reels, Story, TikTok, Shorts), 4:5 (Feed e Facebook), 1:1 (Threads) e 2:3 (Pinterest).
- **Interface por cima da capa:** botões à direita, conta, "Seguir" e legenda embaixo. Um botão **"Mostrar zonas cobertas"** pinta de vermelho o que a interface esconde.
- **Legenda cortada** no "... mais" (ou "... Ver mais"), no limite aproximado de cada rede. Tocar em "mais" abre a legenda inteira. Shorts e Pinterest usam o **título**. Story não mostra legenda.
- **Ficha ao lado** (no celular, embaixo):
  - formato;
  - quantos caracteres aparecem;
  - tamanho da sua legenda, com aviso se passar do máximo da rede;
  - **quanto da capa é cortado** nessa rede (ex.: "perde ~20% dos lados").

Não há nenhum logo oficial: as redes aparecem só como rótulos de texto, e os ícones (coração, balão, avião…) são desenhados no próprio arquivo.

**Acessível:**

- Esc fecha;
- o foco fica preso no modal;
- as setas trocam de rede;
- ao fechar, o foco volta para a capa;
- respeita "reduzir movimento";
- botões de pelo menos 40 px.

**Tema:** segue o painel sozinho (o painel é escuro). Dá para forçar com `tema: "claro" | "escuro"`. Nas redes de feed há ainda o botão "Tela clara/escura".

**Celular:** no celular o modal ocupa a tela toda, e a moldura se ajusta à altura. O painel roda como Artifact: **zero scripts externos**, tudo embutido.

- **Testar:** abra `previa_demo.html` no navegador do PC ou do celular. São 6 posts de exemplo: Reels, carrossel, story, pin, texto do Threads e um post sem redes, que mostra as 8.
- **Entrada:**

  ```js
  PreviaCelular.abrir({capa, video?, legenda, titulo?, conta, canal, redes: [...], laminas?, tipo?, avatar?, cor?},
                      {origem: elementoDaCapa, tema: "auto"})
  ```

  - `redes` aceita "instagram", "reels", "Instagram Feed", "youtube", "shorts"… Com "instagram" e "facebook", o `tipo` decide a tela: `story` vira Story, `reels`/`video`/`short` vira Reels, e o resto vira Feed.
  - `laminas` vira carrossel, com setas e "1/N".
  - `capa_rapida` mostra a miniatura na hora e troca pela nítida quando ela chegar.
- **Ligar pelo HTML:**
  - `PreviaCelular.ligar(document)` faz qualquer `[data-previa='{json}']` abrir a prévia com clique ou Enter;
  - `previa_celular.atributo_previa(post)` gera esse atributo em Python, sem repetir a imagem em base64.

### Onde colar no HTML do `montar_painel_publico.py`

**Automático** (recomendado):

```python
html, rel = ligar_no_painel(html)
```

Ou, pela linha de comando: `python scripts\painel\previa_celular.py embutir painel.html --painel`.

**À mão:**

1. Rode `python scripts\painel\previa_celular.py bloco` e cole o `<style>` e o `<script>` que saírem **antes** do `<script>` principal do painel (logo depois do `</style>` do painel).
2. Cole também a função `abrirPrevia` (o texto `PONTE` em `previa_celular.py`).
3. Em `renderAgenda()`, troque a linha

   ```js
   const abrir = () => ampliar(E.dados.agenda[dia].itens[+t.dataset.zoom]);
   ```

   por

   ```js
   const abrir = () => abrirPrevia(E.dados.agenda[dia].itens[+t.dataset.zoom], t);
   ```

   Opcional: troque `title="Ampliar a capa"` por `title="Ver prévia no celular"`. A capa grande continua disponível pelo botão **"Ampliar capa"** dentro da prévia.
4. Para a prévia mostrar a **legenda de verdade**, inclua o campo `legenda` em cada item de `agenda` no `dados.json`. Hoje só vai o `titulo`, e a prévia avisa: "usando o título no lugar".

Testei com o HTML publicado e o `dados.json` real, num Chromium sem interface, com tela de celular de 390 × 844. O resultado:

- a prévia abre ao tocar na capa e usa o avatar do canal;
- o tema escuro é detectado sozinho;
- o botão "Ampliar capa" abre o zoom antigo;
- nenhum erro de JS.

Os limites de legenda e as zonas são **aproximados** (celular de ~390 pt, redes em 2025/2026). Para ajustar, edite a tabela `REDES` no começo do `previa_celular.js` e depois rode `previa_celular.py demo`.
