# verificar_fontes — prova que cada fonte do radar vale

Ferramenta do `radar_hp.py` (Seção 4.10): antes de uma fonte entrar no `07 Canais\radar\<canal>.json`,
ela passa por aqui. Nada é inventado: o que não passa vai para `descartadas` com o motivo.

## Instalação

Nada a instalar: só Python 3.11 ou 3.12 (biblioteca padrão). No PC, se o antivírus quebrar o HTTPS do
Python, instale `pip install truststore` (a ferramenta usa o cofre de certificados do Windows sozinha,
se o pacote existir). Na nuvem o proxy é respeitado via `HTTPS_PROXY` e `SSL_CERT_FILE`.

## Uso (na pasta do projeto, `G:\Meu Drive\Hypado\06 Projeto`)

```
python radar_fontes\verificar_fontes.py verificar radar_fontes\futebol_fontes_novas.json [--gravar] [--json]
python radar_fontes\verificar_fontes.py canal @Flamengo [--id UCxxxx] [--nome "Flamengo"] [--json]
python radar_fontes\verificar_fontes.py rss https://www.ign.com/rss/articles/feed [--json]
python radar_fontes\verificar_fontes.py candidatos radar_fontes\futebol_candidatos.txt [--canal futebol] [--json]
```

- `verificar`: relê o JSON do canal, refaz a verificação de tudo e mostra quem caiu. Com `--gravar`
  regrava o arquivo (quem caiu vai para `descartadas`, as antigas ficam). Saída 0 = ninguém caiu; 1 = alguém caiu ou o arquivo não abre.
- `canal`: imprime `id`, `título`, `url` e `verificado_por` (`feed` ou `pagina_canal`). Saída 1 = não verificado (motivo na tela).
- `rss`: imprime título, nº de itens e a data do item mais novo. Saída 1 = não passou (motivo na tela).
- `candidatos`: arquivo de texto com uma linha por fonte, `tipo|nome|url|oficial|reutilizavel`
  (opcionais: `|channel_id|peso`; `#` começa comentário). Verifica todas e imprime o JSON pronto para
  colar em `<canal>_fontes_novas.json`. O canal vem de `--canal` ou do prefixo do nome do arquivo
  (`futebol_...txt`). Saída 0 = tudo passou; 1 = alguém caiu.
- `--json` em qualquer comando: só o JSON na saída (para máquina).

## O que conta como verificado

- **Canal de YouTube:** 1) o feed `feeds/videos.xml?channel_id=` responde 200, é XML e o `<title>` bate com
  o nome (sem acento/maiúscula; um pode conter o outro) → `verificado_por: "feed"`; 2) se o feed falhar
  (na nuvem o YouTube responde 404 para qualquer feed), abre `https://www.youtube.com/@handle` e confere que
  o id que a própria página declara é o esperado (ou descobre o id, se não foi dado) → `"pagina_canal"`;
  3) senão, descarta com o motivo. Página 404 = o @handle está errado: procure o @ certo no site oficial.
- **RSS/Atom:** 200 + XML válido (RSS 2.0, RSS 1.0 ou Atom) + pelo menos 1 item com data nos últimos 30 dias.
- **Regras:** `oficial: true` só para canal/sala da própria marca, clube, liga ou federação; site/canal de
  notícia (ge, Omelete, Autoesporte, IGN...) vira `oficial: false` e `video_reutilizavel: false` com aviso;
  `video_reutilizavel: true` só em canal oficial de clube/CBF/liga (futebol) ou de estúdio (filmes, gta), sempre
  com `nota_uso`; Flow Games nunca entra.

## Formato do JSON de saída

`{"canal", "verificado_em", "rss": [{nome, url, oficial, filtrar, peso, verificado_em, evidencia, verificado_por}],
"youtube": [{nome, url (@handle), channel_id, peso, oficial, video_reutilizavel, nota_uso?, verificado_em, evidencia,
verificado_por}], "descartadas": [{nome, url|channel_id, motivo}]}`. `evidencia` é a URL da página oficial onde o
id/feed foi achado (se a entrada já tinha, é mantida).

## Testes

`cd <projeto>` e `python -m pytest -q radar_fontes` — sem rede e sem relógio real (respostas gravadas, `hoje` injetado).
