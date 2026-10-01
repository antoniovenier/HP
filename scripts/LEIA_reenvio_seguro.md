# reenvio_seguro.py — publicador da API sem post duplicado (ticket H)

**Problema:** quando a API do Instagram/Threads dá "tempo esgotado", o post às vezes
**saiu mesmo assim**. Se o publicador tenta de novo às cegas, o post sai duplicado.

**Solução:** antes de cada nova tentativa, conferir na API se o post já está lá.
O `publicador_meta.py` continua o mesmo (não é reescrito); ele só **importa** este módulo.

## O que tem aqui

| Função | O que faz |
|---|---|
| `ja_publicado(cliente, ig_id, legenda, desde_ts)` | GET `/<ig_id>/media?fields=id,caption,timestamp,permalink&limit=5` e procura um post com a mesma legenda (primeiros 80 caracteres, sem espaços, sem as variações invisíveis de emoji, maiúscula = minúscula) publicado a partir de **início da tentativa − 2 min**. Devolve `{"id", "permalink", "timestamp"}` ou `None`. Para Threads: `rede="threads"` (usa `/<id>/threads` e o campo `text`). |
| `publicar_com_reenvio(publicar_fn, conferir_fn, esperas=(60, 300, 900), simular=False, dormir=time.sleep)` | 4 tentativas no total: publica; se der **tempo esgotado** espera 1 min, confere, e só republica se não saiu; depois 5 min; depois 15 min. Se a conferida acha o post, devolve o id dele **sem publicar de novo**. Depois da 4ª falha ainda espera 1 min e confere uma última vez; se não achou, levanta `ReenvioEsgotado`. Qualquer erro que **não** seja tempo esgotado (legenda recusada, token vencido, HTTP 4xx...) sobe na hora. Se a conferida falhar (API fora), **não republica às cegas**: espera a próxima rodada. `simular=True`: não publica nem espera, só descreve. Parâmetro extra `relatorio={}` recebe tentativas, `ja_tinha_saido` e os eventos. |
| `eh_tempo_esgotado(erro)` | `True` para timeout (`TimeoutError`, `requests` `Timeout`/`ReadTimeout`, `TempoEsgotado`) e HTTP 5xx (atributo `status`/`status_code`/`response.status_code`, ou texto "HTTP 5xx" / "timed out" / "tempo esgotado"). |
| `ClienteGraph(token, versao="v21.0")` | cliente simples da Graph API para a conferida; o token nunca aparece em erro nem log. |
| `fila_story_apos_post(post_id, conta, canal, link, publicado_em, titulo, destaque)` | grava `H:\HypadoLocal\emulador\fila_story\<post_id>.json` (formato do `story_post.py`/`story_clicavel.py`). Nunca sobrescreve: se o arquivo já existe (ou está em `fila_story\feitos\`), não faz nada — nunca 2 stories do mesmo post. Sem id ou link do post → erro (story só **depois** do post). |

## Instalação

1. Copie `reenvio_seguro.py` para `G:\Meu Drive\Hypado\scripts\` (ao lado do `publicador_meta.py`).
2. `pip install requests` (se já não tiver).
3. Ele acha a base `hpbase` sozinho em `G:\Meu Drive\Hypado\06 Projeto\app\hp_studio_nuvem\`
   (ou na pasta da variável `HP_APP`).
4. Tokens: lidos de `H:\HypadoLocal\segredos\meta_tokens.txt` com `IG_<CONTA>_TOKEN` e
   `IG_<CONTA>_ID` (Threads: `TH_<CONTA>_TOKEN`/`TH_<CONTA>_ID`; se faltar, tenta `IG_TOKEN`
   e `META_TOKEN`) — **mesmo formato do LEIA do pacote `metricas`**. Nunca impressos.

## Comandos

```
python scripts\reenvio_seguro.py reenviar <id> --simular
python scripts\reenvio_seguro.py reenviar <id> [--fila H:\HypadoLocal\fila_api]
python scripts\reenvio_seguro.py story <post_id> --conta hpgta6 --canal gta --link <url> --publicado-em 2026-09-30T18:30:00-03:00 --titulo "..." [--destaque "GTA 6"]
```

`reenviar`: acha o item na fila (em `fila_api\<id>.json` ou em qualquer subpasta), confere
na API se já saiu e **só republica se não saiu** (com as 4 tentativas acima). Com `--simular`
só confere e diz "já saiu: <link>" ou "não saiu. Republicaria ..." — não publica nem grava.
Sem `--simular`, grava no próprio item: `status: "publicado"`, `media_id`, `permalink` e um
bloco `reenvio` (tentativas, se já tinha saído, quando); se falhar, `reenvio.status: "erro"`.
Log em `H:\HypadoLocal\app\logs\reenvio_seguro_AAAA-MM-DD.log`.

### Formato do item da fila (SUPOSIÇÃO — conferir com o publicador_meta.py)

```json
{
  "id": "20260930-1830-gta-reel",
  "rede": "instagram",
  "conta": "gta",
  "tipo": "reel",
  "legenda": "texto completo da legenda",
  "tentativa_inicio": "2026-09-30T18:30:05-03:00",
  "status": "tempo_esgotado",
  "ig_id": "opcional (senão vem de IG_GTA_ID)"
}
```

Nomes aceitos também: legenda = `caption`/`texto`/`text`; início = `inicio_tentativa`,
`tentado_em`, `iniciado_em` ou `agendado_para`. Sem nenhum horário, a conferida olha as
últimas 24 h (a legenda decide). Se os nomes forem outros, basta ajustar `CAMPOS_LEGENDA` /
`CAMPOS_INICIO` no topo da seção "fila da API".

## Integração no `publicador_meta.py` (acréscimos, sem reescrever)

**Fase 1 — modo simular (7 dias, antes de ligar).** Só o comando novo. No começo do bloco
`if __name__ == "__main__":` do `publicador_meta.py`, acrescente:

```python
    if len(sys.argv) > 1 and sys.argv[1] == "reenviar":
        import reenvio_seguro
        raise SystemExit(reenvio_seguro.main(sys.argv[1:]))
```

Assim `python scripts\publicador_meta.py reenviar <id> --simular` funciona (é o comando do
ticket). A cada "tempo esgotado" do publicador, rode-o com `--simular` e anote se o que ele
diz ("já saiu" / "republicaria") bate com o que aconteceu de verdade no perfil.

**Fase 2 — ligado.** Onde o publicador hoje chama a publicação de um item (nome suposto
`publicar_item(item)`; troque pelo nome real), troque a linha por:

```python
from reenvio_seguro import ClienteGraph, ja_publicado, publicar_com_reenvio  # no topo
import time                                                                     # no topo

inicio = time.time()
conferir = ClienteGraph(token)  # o mesmo token do IG que o publicador já leu
media_id = publicar_com_reenvio(
    lambda: publicar_item(item),                                  # a chamada de hoje
    lambda: ja_publicado(conferir, ig_id, item["legenda"], inicio))
```

Atenção: no pior caso esse item segura o publicador por ~22 min (1 + 5 + 15 + 1 de
conferida final) — é de propósito, para não duplicar. Os outros itens esperam na fila.

Para o Threads: `ClienteGraph(token_threads, versao="v1.0", host="https://graph.threads.net")`
e `ja_publicado(..., rede="threads")`. Se o publicador levanta um erro próprio no tempo
esgotado, ele é reconhecido se tiver `status_code` 5xx ou "timed out"/"tempo esgotado" no
texto; se não tiver, faça-o levantar `reenvio_seguro.TempoEsgotado`.

**Para o `reenviar` republicar de verdade** ele chama, do `publicador_meta.py`, a primeira
função que existir entre `publicar_item(item)`, `publicar_da_fila(item)` e `publicar(item)`,
que deve publicar UM item da fila e devolver o id (texto ou dict com `id`). Se não existir
nenhuma com esse formato, acrescente uma pequena `publicar_item(item)` que chama o que já existe.

## Story depois do post (`largada_canais.py` → `fila_story_com_post.py`)

A linha exata para o `largada_canais.py`, logo depois que o post saiu (com o `media_id`
e o `permalink` em mãos — o que o `publicar_com_reenvio` devolve):

```python
from reenvio_seguro import fila_story_apos_post  # no topo do largada_canais.py
fila_story_apos_post(media_id, conta, canal, permalink, publicado_em, titulo, destaque)
```

Se preferir manter o `fila_story_com_post.py` como passo separado, ele vira só isto:

```python
# scripts\fila_story_com_post.py
import sys
from reenvio_seguro import main
raise SystemExit(main(["story", *sys.argv[1:]]))
```

e a linha no `largada_canais.py` (sem janela preta) é:

```python
subprocess.run([sys.executable, str(Path(__file__).with_name("fila_story_com_post.py")), media_id, "--conta", conta, "--canal", canal, "--link", permalink, "--publicado-em", publicado_em, "--titulo", titulo, "--destaque", destaque or ""], creationflags=0x08000000 if os.name == "nt" else 0, check=False)
```

Só para posts do Instagram (o story é do Instagram). O `story_post.py` consome a fila.

## Testes

`cd app && python -m pytest -q ../scripts/testes/test_reenvio_seguro.py` — `dormir` falso,
cliente falso, nada de rede: sai de primeira; tempo esgotado e já tinha saído (não duplica);
3 tempos esgotados e a 4ª sai; 4 falhas → erro final; erro que não é tempo esgotado sobe na
hora; modo simular não publica; conferida com erro não republica às cegas; legenda com emoji
diferente; janela de 2 min; token nunca aparece no erro; fila do story sem duplicar.
