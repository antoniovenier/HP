# Relatório das fontes do radar — rodada 2 (verificação final em 01/10/2026)

Fechamento da tarefa F (pesquisa de fontes do `radar_hp.py`, Seção 4.10). Os números abaixo vêm dos
quatro JSONs `radar_fontes/<canal>_fontes_novas.json` **depois** da última passada com rede
(`verificar_fontes.py verificar <json> --gravar`, 01/10/2026 entre 01:59 e 02:00, horário de Brasília):
nenhuma entrada caiu nessa passada (saída 0 nos 4 canais), todas as 74 entradas têm `evidencia` e
`verificado_por`, e Flow Games não aparece em nenhum arquivo (nem em `descartadas`).

Como ler: **fonte nova** = passou na verificação e está pronta para o `07 Canais\radar\<canal>.json`;
**descartada** = candidato que não passou ou não pôde ser provado, com o motivo gravado no JSON.
Quatro entradas de YouTube estão marcadas `ja_existe: true` (já estão na tabela de 4.10 com outro
nome; servem para conferir o id, não para duplicar).

## Resumo

| Canal | RSS novos | YouTube novos | dos quais `ja_existe` | Descartadas | Arquivo |
|---|---|---|---|---|---|
| futebol | 7 | 13 | 2 (CBF, CONMEBOL Libertadores BR) | 18 | `futebol_fontes_novas.json` |
| filmes | 8 (6 oficiais + 2 Google News) | 18 (17 oficiais + AdoroCinema) | 1 (Paramount Brasil) | 20 | `filmes_fontes_novas.json` |
| carros | 6 | 21 | 0 | 46 | `carros_fontes_novas.json` |
| gta | 1 | 1 (Rockstar, confirmação) | 1 (Rockstar Games) | 2 | `gta_fontes_novas.json` |
| **total** | **22** | **53** | 4 | **86** | |

Descontando as 4 `ja_existe`, são **49 canais de YouTube novos e 22 feeds novos** (20 oficiais e 2 de
site de notícia via Google Notícias). Todos os 53 canais foram provados pela página do canal
(`verificado_por: "pagina_canal"`, ver a nota no fim); todos os 22 feeds responderam 200 com XML válido
e item dos últimos 30 dias (`verificado_por: "rss"` ou `"atom"`).

## Canal futebol

**Fontes novas — RSS (7):** Atlético-MG, Bahia, Chapecoense, Santos, São Paulo FC, Vitória (feeds
WordPress dos sites oficiais, `oficial: true`, `filtrar: false`, peso 1.5) e CONMEBOL
(`conmebol.com/feed/`, espanhol, todas as competições: `filtrar: true`, peso 1.2).

**Fontes novas — YouTube (13):** os 7 clubes da Série A 2026 que faltavam na tabela de 4.10 —
Athletico Paranaense (@AthleticoParanaense), Red Bull Bragantino (@MassaBrutaTV), Chapecoense (@ChapeTv),
Coritiba (@coritibaoficial), Mirassol (@CanalMirassolFC), Remo (@RemoTV), Vitória (@tvvitoria1899) —
mais CONMEBOL (@conmebol), CONMEBOL Sudamericana (@Sudamericana, espanhol), CONMEBOL Sudamericana BR
(@SudamericanaBR), FIFA (@FIFA) e, marcados `ja_existe`, CBF (@brasil, canal hoje chamado
"Confederação Brasileira de Futebol" — provavelmente o "CBF TV" da tabela) e CONMEBOL Libertadores BR
(@LibertadoresBR — a tabela já tem "CONMEBOL Libertadores"). Todos `oficial: true` e
`video_reutilizavel: true` com `nota_uso` (crédito, áudio original, nunca imagem de TV).
Não existe canal separado da Seleção: a busca só devolve o canal da CBF.

**Descartadas (18), por motivo:**

| Motivo | Quantas | Quem |
|---|---|---|
| Feed existe mas está vazio ou abandonado | 4 | Palmeiras (último item de 2009), Athletico-PR (vazio), Corinthians (declarado no HTML, vem vazio), CONMEBOL Sudamericana (`/sudamericana/feed/` só tem comentários; vale o feed geral, que entrou) |
| Sem feed: HTTP 404 e o site não declara RSS/Atom | 5 | Internacional, Botafogo, Vasco (home 403), Remo, Mirassol |
| Veio página HTML no lugar de feed (site só JavaScript) | 4 | Fluminense, Cruzeiro, Coritiba, Red Bull Bragantino |
| Não abre desta nuvem (bloqueio de robô, certificado, corpo vazio) | 3 | Flamengo (conexão reiniciada / 403), Grêmio (200 com corpo vazio), **CBF** (erro de certificado no proxy) |
| @handle errado (página 404; o certo entrou) | 1 | @CONMEBOLSudamericana → @Sudamericana |
| Não verificado por tempo | 1 | FIFA RSS (fifa.com não expõe feed no HTML) |

**Os 20 clubes da Série A 2026** (fonte: `https://ge.globo.com/futebol/brasileirao-serie-a/`, tabela de
classificação, campo `nome_popular`; conferida com `https://pt.wikipedia.org/wiki/Campeonato_Brasileiro_de_Futebol_de_2026_-_Série_A`,
seção "Participantes" — as duas listas batem, 20 a 20. **A página oficial da CBF não foi usada**:
`cbf.com.br` não abre desta nuvem por erro de certificado no proxy; o PC confirma lá):

Athletico-PR*, Atlético-MG, Bahia, Botafogo, Red Bull Bragantino*, Chapecoense*, Corinthians, Coritiba*,
Cruzeiro, Flamengo, Fluminense, Grêmio, Internacional, Mirassol*, Palmeiras, Remo*, Santos, São Paulo,
Vasco, Vitória*. (* = canal de YouTube novo nesta rodada; os outros 13 já estavam na tabela de 4.10.)

## Canal filmes

**Fontes novas — RSS (7):** salas de imprensa oficiais Marvel (`marvel.com/rss/feed`, `filtrar: true`:
cobre quadrinhos e games), Apple TV Press (`apple.com/tv-pr/news-feed.xml`, Atom, `filtrar: false`),
Apple Newsroom Brasil (`apple.com/br/newsroom/rss-feed.rss`, Atom, em português, `filtrar: true`),
The Walt Disney Company (`thewaltdisneycompany.com/feed/`, `filtrar: true`) e Amazon News
(`aboutamazon.com/rss/feed.rss`, `filtrar: true`); mais 2 de site de notícia (`oficial: false`,
`filtrar: true`): Omelete e AdoroCinema **via RSS do Google Notícias** restrito ao domínio
(`news.google.com/rss/search?q=site:omelete.com.br…` / `site:adorocinema.com`), porque nenhum dos dois
sites tem RSS próprio.

**Fontes novas — YouTube (18):** streamings Paramount+ Brasil (@ParamountPlusBR), Netflix (@Netflix),
Prime Video (@PrimeVideo), HBO Max (@hbomax), Disney Plus (@DisneyPlus), Paramount Plus (@paramountplus),
Apple TV (@AppleTV — não há canal BR separado); estúdios Walt Disney Studios BR (@WaltDisneyStudiosBR),
Universal Pictures (@UniversalPictures), Sony Pictures Entertainment (@SonyPictures), Paramount Pictures
(@ParamountPictures), Pixar (@Pixar), Star Wars (@StarWars), Lucasfilm (@Lucasfilm), Lionsgate Movies
(@LionsgateMovies), A24 (@A24); AdoroCinema (@AdoroCinemaOficial, site de notícia: `oficial: false`,
`video_reutilizavel: false`); e, marcado `ja_existe`, Paramount Brasil (@ParamountBrasil — provavelmente
o "Paramount Pictures Brasil" da tabela, renomeado). Os 17 oficiais têm `video_reutilizavel: true` com
`nota_uso` "trailer/clipe só com comentário nosso; nunca trailer puro". Netflix Brasil, Prime Video
Brasil, HBO Max Brasil, Disney+ Brasil, Warner (global e BR) e Marvel (global e BR) já estão na tabela
e não foram repetidos.

**Descartadas (21), por motivo:**

| Motivo | Quantas | Quem |
|---|---|---|
| Sala de imprensa / site sem RSS (o HTML não declara feed; `/rss`, `/feed` 404) | 9 | Warner Bros. Discovery, Disney+ (vale o feed corporativo da Disney, que entrou), Sony Pictures (só lista HTML), A24, Pixar, Lucasfilm/Star Wars, Universal/NBCUniversal, Omelete (só `sitemap-news.xml`), AdoroCinema |
| Bloqueio de robô (HTTP 403 / desafio Cloudflare) | 3 | Amazon RI, Paramount Global (Press Express exige login: não tentado), Lionsgate RI |
| Não abre desta nuvem (proxy responde 502) | 2 | press.paramountplus.com, press.amazonstudios.com |
| ~~Feed válido, mas data em formato fora do padrão~~ **ENTROU em 01/10 (02h38)** | 0 | **Netflix Brasil** `about.netflix.com/pt_br/feed.xml` (`<pubDate>30 de setembro de 2026</pubDate>`): a sessão principal corrigiu `analisar_data()` (data por extenso em português e inglês) e o feed passou a verificar (15 itens, mais novo 30/09/2026) — está em `rss` com `oficial: true`, `filtrar: false`, `peso: 1.5` |
| @handle errado (página 404; o certo entrou) | 2 | @ParamountPlusBrasil → @ParamountPlusBR; @AdoroCinema → @AdoroCinemaOficial |
| Fora do assunto / fora do escopo / não existe | 3 | Apple Brasil (canal geral da Apple), Walt Disney Studios PT (Portugal), Apple TV Brasil (não existe canal próprio) |
| Não verificado por tempo | 1 | canais BR separados de Lionsgate, A24, Pixar e Lucasfilm (os globais entraram) |

## Canal carros

**Fontes novas — RSS (6):** Volkswagen Newsroom (`volkswagen-newsroom.com/en/feeds/press-releases`),
Audi Media Center, Nissan Global Newsroom (`global.nissannews.com/en/rss`) — globais —, BMW Group
PressClub Brazil (`filtrar: true`: mistura BMW, MINI e Motorrad), Hyundai CSA News (sala BR, em
`hyundai-csa-news.com/feed/`) e Toyota Comunica (`toyotacomunica.com.br/feed/`) — Brasil. Todos
`oficial: true`, peso 1.5.

**Fontes novas — YouTube (21), todos `oficial: true` e `video_reutilizavel: false`** (vídeo de montadora
não é reutilizável pela regra da tarefa F): globais Ram Trucks, Nissan, Peugeot, Citroën
(@theofficialcitroen), Honda, Chevrolet, Jeep, BYD Global, GWM Global (@greatwallmotor1853), Renault Group
(@renaultgroup), Mitsubishi Motors (@MitsubishiMotorsTV); Brasil Ram do Brasil, Nissan Brasil, Peugeot
Brasil, Citroën do Brasil (@citroen), Mitsubishi Motors BR (@MitsubishiMotors), Ford Brasil, Audi Brasil,
Hyundai Motor Brasil (@hyundaibr), Kia Brasil (@KiaBrasilOficial), Land Rover Brasil (@landroverbr).
Dos 6 que o enunciado apontou como faltando, **5 entraram** (Ram, Nissan, Peugeot, Citroën, Mitsubishi —
global e BR); **Caoa Chery não entrou** (canal @CAOAChery existe, id UCo3iqVlz3pzmXlSoipcAWEw, mas sem
selo e sem link no site oficial: fica para o Antônio confirmar).

**Descartadas (46), por motivo:**

| Motivo | Quantas | Quem |
|---|---|---|
| Sala de imprensa bloqueia robô (HTTP 403 / desafio) | 13 | Stellantis global e BR (vale para Fiat, Jeep, Ram, Peugeot, Citroën), Ford global e BR, GM Newsroom (`/rss` 403) e GM Brasil, Mercedes-Benz Group Media, Toyota global (`/rss`, `/feed` 403), Renault Group media (feed 403), Volvo Cars (global e BR), Lamborghini (202 com desafio), Tesla, Audi Brasil |
| Sala abre mas não declara feed (sem RSS) | 11 | Porsche Newsroom, Honda global, Kia Brasil (só kits .zip), Nissan en-US (404; o `/en/rss` entrou), BYD global, GWM Brasil, Caoa Chery notícias, Mitsubishi global e BR, Ferrari media centre, Hyundai Motor Brasil (URL do enunciado redireciona; a sala certa, `hyundai.com.br/imprensa` → hyundai-csa-news.com, entrou) |
| Não abre desta nuvem (certificado, 502 do proxy, conexão reiniciada, laço de redirecionamento) | 5 | Mercedes-Benz Brasil imprensa, Kia Newscenter (certificado), Honda News Brasil (502), Nissan Brasil newsroom (laço 303), GWM global `/news/` (reset) |
| Aplicação JavaScript (veio HTML no lugar de feed) | 3 | Renault Brasil imprensa, BYD Brasil, Volkswagen News Brasil |
| Feed existe mas vazio (XML válido com 0 itens) | 2 | JLR Corporate, JLR Land Rover |
| Endereço do SKILL desativado / não verificado por tempo | 1 | McLaren `cars.mclaren.press` (404) |
| Canal de YouTube sem prova (sem selo e sem link no site oficial) ou em dúvida | 9 | Fiat global (dois canais verificados "Fiat"), @Renault (o site leva ao Renault Group), MITSUBISHI MOTORS Global, CAOA Chery, BMW Brasil, Mercedes-Benz Brasil, Porsche Brasil, Volvo Car Brasil, canal BR da BMW (a sala BR só linka o global) |
| @handle errado (página 404; o certo entrou) | 1 | @MitsubishiMotorsBR (citado no site) → @MitsubishiMotors |
| Não verificado por tempo | 1 | Chery global (só canais regionais na busca) |

**Tabela montadora → sala de imprensa → RSS → canal de YouTube.** *tabela* = já estava em 4.10 (não
repetido); **novo** = entrou nesta rodada; ✗ = não entrou (motivo curto); — = não existe / não pesquisado.

| Montadora | Sala de imprensa global | RSS | Sala de imprensa BR | RSS | YouTube global | YouTube BR |
|---|---|---|---|---|---|---|
| BMW | press.bmwgroup.com | sim (*tabela*) | press.bmwgroup.com/brazil | **sim, novo** | *tabela* | ✗ @BMWTVBrasil sem prova |
| Mercedes-Benz | group-media.mercedes-benz.com (403) | não | mercedes-benz.com.br (não abre daqui) | ✗ | *tabela* | ✗ @MercedesBenzBrasil sem prova |
| Audi | audi-mediacenter.com | **sim, novo** | audi.com.br (403) | ✗ | *tabela* | **novo** (@AudiBRAudiBrasil) |
| Porsche | newsroom.porsche.com | não (não declara) | não há edição BR | — | *tabela* | ✗ @PorscheBrasilOficial sem prova |
| Volkswagen | volkswagen-newsroom.com | **sim, novo** | vwnews.com.br (só JavaScript) | não | *tabela* | *tabela* |
| Toyota | global.toyota/en/newsroom | não (403; *Toyota Pressroom* já na tabela) | toyotacomunica.com.br | **sim, novo** | *tabela* | *tabela* |
| Honda | global.honda/en/newsroom | não (não declara) | hondanews.com.br (não abre daqui) | ✗ | **novo** (@Honda) | *tabela* |
| Hyundai | hyundainews.com | sim (*tabela*) | hyundai.com.br/imprensa → hyundai-csa-news.com | **sim, novo** | *tabela* | **novo** (@hyundaibr) |
| Kia | kianewscenter.com (certificado) | ✗ | kia.com.br/areaimprensa (só kits) | não | *tabela* | **novo** (@KiaBrasilOficial) |
| Chevrolet | news.gm.com | não (`/rss` 403) | media.gm.com/br (403) | ✗ | **novo** (@Chevrolet) | *tabela* |
| Fiat | media.stellantis.com (403) | ✗ | media.stellantis.com/br-pt (403) | ✗ | ✗ dois canais "Fiat", em dúvida | *tabela* |
| Jeep | media.stellantis.com (403) | ✗ | idem (403) | ✗ | **novo** (@Jeep) | *tabela* |
| Ram | media.stellantis.com (403) | ✗ | idem (403) | ✗ | **novo** (@RamTrucks) | **novo** (@RamdoBrasil) |
| Ford | media.ford.com (403) | ✗ | media.ford.com/…/br (403) | ✗ | *tabela* | **novo** (@fordbrasil) |
| Renault | media.renaultgroup.com | não (feed 403) | imprensa.renault.com.br (só JavaScript) | não | **novo** (@renaultgroup) | *tabela* |
| Nissan | global.nissannews.com | **sim, novo** | brasil.nissannews.com (laço de redirecionamento) | ✗ | **novo** (@Nissan) | **novo** (@nissanbrasil) |
| Peugeot | media.stellantis.com (403) | ✗ | idem (403) | ✗ | **novo** (@Peugeot) | **novo** (@peugeotbrasil) |
| Citroën | media.stellantis.com (403) | ✗ | idem (403) | ✗ | **novo** (@theofficialcitroen) | **novo** (@citroen) |
| BYD | byd.com (sem sala com feed) | não | byd.com.br (só JavaScript) | não | **novo** (@BYDGlobal) | *tabela* |
| GWM | gwm-global.com (`/news` reinicia a conexão) | não | gwmmotors.com.br (sem imprensa) | não | **novo** (@greatwallmotor1853) | *tabela* |
| Caoa Chery | Chery global não verificado | — | caoachery.com.br/noticias | não (sem feed) | — | ✗ @CAOAChery sem prova |
| Mitsubishi | mitsubishi-motors.com/en/newsroom | não (não declara) | mitsubishimotors.com.br/imprensa | não (sem feed) | **novo** (@MitsubishiMotorsTV) | **novo** (@MitsubishiMotors) |
| Volvo | volvocars.com/intl/media (403) | ✗ | volvocars.com/br (403) | ✗ | *tabela* | ✗ @VolvoCarBrasil sem prova |
| Land Rover | media.jlr.com | não (feed vazio) | landrover.com.br (sem feed) | não | *tabela* | **novo** (@landroverbr) |
| Ferrari | ferrari.com/en-US/media-centre | não (não declara) | — | — | *tabela* | — |
| Lamborghini | media.lamborghini.com (desafio anti-robô) | ✗ | — | — | *tabela* | — |
| McLaren | cars.mclaren.press (404, desativado) | ✗ | — | — | *tabela* | — |
| Tesla | tesla.com/blog (403) | ✗ | — | — | *tabela* | — |

Endereços do SKILL `hp-carros-lancamentos` que mudaram (conferido em 01/10/2026): Ferrari é
`ferrari.com/en-US/media-centre` (o `/en-EN/media` dá 404); Hyundai Brasil é `hyundai.com.br/imprensa` →
`hyundai-csa-news.com`; `cars.mclaren.press` responde 404; Nissan Brasil `nissannews.com/pt-BR` cai na
página global (o feed global é `global.nissannews.com/en/rss`).

## Canal gta

**Fonte nova — RSS (1):** Take-Two Interactive, press releases do RI
(`https://ir.take2games.com/rss/news-releases.xml`, `oficial: true`, `filtrar: true` porque cobre 2K e
Zynga, peso 1.5). **YouTube:** Rockstar Games (@RockstarGames, UC6VcWc1rAoWdBCM0JxrRQ3A) **confirmado**
pela própria página do canal (`externalId` + título) e marcado `ja_existe` (já é a entrada da fixture
`radar_gta.json`). Nada mais oficial apareceu; o Newswire da Rockstar já tem coletor próprio no radar.

**Descartadas (2):** Take-Two por caminho alternativo (`take2games.com/ir/rss/news-releases.xml` 404; o
feed válido entrou) e Rockstar Newswire RSS (não testado de propósito: `rockstar_newswire: true` no
config). Nenhuma fonte de vazamento, fã ou Flow Games foi considerada.

## O que o PC deve tentar de novo (não abriu desta nuvem)

Abrir no navegador, apertar Ctrl+U e procurar `rss` ou `feed`; achando um endereço, rodar
`python radar_fontes\verificar_fontes.py rss <endereço>`:

- Futebol: `cbf.com.br` (notícias e a página da Série A — confirmar também a lista dos 20 clubes),
  `flamengo.com.br/feed/`, `vasco.com.br/feed/`, `gremio.net/feed/`.
- Filmes: `press.paramountplus.com`, `press.amazonstudios.com`.
- Carros: `media.stellantis.com/br-pt`, `media.ford.com`, `news.gm.com`, `volvocars.com/intl/media`,
  `tesla.com/blog`, `group-media.mercedes-benz.com`, `kianewscenter.com`, `hondanews.com.br`,
  `mercedes-benz.com.br/imprensa`, `brasil.nissannews.com`.
- Canais de YouTube sem prova (1 clique: rodapé do site oficial → o YouTube linkado é este?):
  Caoa Chery @CAOAChery, BMW Brasil @BMWTVBrasil, Mercedes-Benz Brasil @MercedesBenzBrasil, Porsche
  Brasil @PorscheBrasilOficial, Volvo Car Brasil @VolvoCarBrasil, Fiat global (@fiat1253 ou @Fiat). Os ids
  estão nas `descartadas` de `carros_fontes_novas.json`; se bater, colar a linha
  `youtube|Nome|url|true|false|UC...` num .txt e rodar
  `python radar_fontes\verificar_fontes.py candidatos esse.txt --canal carros`.

## Nota: o feed do YouTube responde 404 neste ambiente

A regra da tarefa F manda provar o `channel_id` pelo feed `https://www.youtube.com/feeds/videos.xml?channel_id=<id>`
(200 + `<title>` batendo com o nome). **Nesta nuvem o YouTube responde HTTP 404 para esse feed em
qualquer canal** (inclusive o Rockstar Games da fixture), então a ferramenta caiu para a segunda prova
prevista: abrir `https://www.youtube.com/@handle` e conferir que o id que a **própria página** declara
(`externalId` / `canonical`) é o esperado e que o título bate. Por isso **todos os 53 canais estão com
`verificado_por: "pagina_canal"`**, nenhum com `"feed"`. Nenhum id foi inventado: todos saíram da página
do canal, e a URL da página oficial (site do clube/marca/estúdio, ou a página do canal com selo
verificado) está em `evidencia`.

Para repetir a verificação **pelo feed** (o PC enxerga o feed normalmente), na pasta do projeto
(`G:\Meu Drive\Hypado\06 Projeto`):

```
python radar_fontes\verificar_fontes.py verificar radar_fontes\futebol_fontes_novas.json --gravar
python radar_fontes\verificar_fontes.py verificar radar_fontes\filmes_fontes_novas.json --gravar
python radar_fontes\verificar_fontes.py verificar radar_fontes\carros_fontes_novas.json --gravar
python radar_fontes\verificar_fontes.py verificar radar_fontes\gta_fontes_novas.json --gravar
```

A ferramenta tenta o feed primeiro: no PC as entradas passam para `verificado_por: "feed"` e o
`verificado_em` é recarimbado. Saída 0 = ninguém caiu; 1 = alguma fonte caiu (ela vai para
`descartadas` com o motivo; as antigas ficam). Se der erro de certificado/HTTPS (antivírus), a opção
`--curl` vai **antes** do comando: `python radar_fontes\verificar_fontes.py --curl verificar radar_fontes\carros_fontes_novas.json --gravar`.
Para conferir um canal só: `python radar_fontes\verificar_fontes.py canal @RockstarGames --id UC6VcWc1rAoWdBCM0JxrRQ3A --nome "Rockstar Games"`
(no PC deve imprimir `verificado_por: feed`).

As duas atenções que o F4 deixou para o `--gravar` no PC **já foram resolvidas pela sessão principal
(01/10, 02h38)** em `verificar_fontes.py`, com 3 testes novos (38 no total):

1. As marcas `ja_existe`/`nota_conferir` das entradas agora **sobrevivem** ao `--gravar` (`MARCAS_HUMANAS`).
2. "GWM Global" (@greatwallmotor1853) continua `oficial: true`: `motor1` virou token exato (`TOKENS_EXATOS`),
   então o @handle não casa mais com o Motor1.com.
3. `analisar_data()` lê data por extenso ("30 de setembro de 2026", "September 30, 2026") — foi o que fez o
   feed da Netflix Brasil entrar. Os 4 JSONs foram regravados com a ferramenta corrigida: `gta 1 rss · 1 yt`,
   `futebol 7 · 13`, `filmes 8 · 18`, `carros 6 · 21`; carimbos `2026-10-01T02:37:56` a `02:38:31-03:00`.
   No PC basta rodar os 4 comandos da seção "nota do feed" sem nenhuma correção à mão depois.

## Como foi verificado (resumo)

- Ferramenta: `radar_fontes/verificar_fontes.py` (F0), rede só por `transporte_real` (urllib via proxy da
  nuvem; `--curl` disponível para o PC). Testes: 38 (35 da F0 + 3 das correções), sem rede e sem relógio real.
- Pesquisa (F1 futebol + gta, F2 filmes, F3 carros): só leitura de páginas públicas; nenhum login, nenhum
  clique em Aceitar/Permitir, nenhum id ou URL inventado. Candidatos e resultado linha a linha em
  `radar_fontes/<canal>_candidatos.txt` (futebol 48, filmes 51, carros 87).
- Verificação final (F4, 01/10/2026): `verificar <json>` seco e depois `verificar <json> --gravar`, nos 4
  canais, com rede; 0 quedas novas; saída 0 em todos.
