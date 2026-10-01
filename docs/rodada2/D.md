# Rodada 2 — Tarefa D: artes de story profissionais por canal (`scripts/story_artes.py`)

Agente D · 01/10/2026 · branch `claude/relaxed-cray-0fkcdu` (sem commit)

## 1. Feito / pela metade / não deu

| Critério de pronto (tarefa D) | Situação |
|---|---|
| CLI `render <spec.json>` · `todas <canal> <pasta>` · `exemplos <pasta>` (18 + `_prancha_story.jpg`) | **Feito** (+ `spec-exemplo` imprime um spec para copiar; `--png` grava o PNG; `--saida` sobrepõe a pasta) |
| Spec com `canal, tipo, capa, rotulo, chamada, fatos, dado_forte, pergunta, credito_foto, figurinhas, cor_destaque, saida, nome, foco, fotos_prefere` | **Feito** (+ `cta` opcional: "Salva o post" padrão no maissobre, "Responde aí" no interacao) |
| Modelo `chamada`: cartão ~860 px com cantos arredondados enquadrado por `foco`, rótulo em pílula, chamada ≤ 45 car. em até 2 linhas com `*destaque*`, seta VETORIAL para a zona do link (140,1500)-(940,1640) só com contorno fino translúcido, selo HP e @ | **Feito** (seta = bezier + ponta triangular desenhada; "toque pra ver" ao lado) |
| `chamada` com `["link","enquete"]`: cartão encolhe (520 px, y 350–900) e sobra a zona da enquete (110,930)-(970,1480) acima da zona do link | **Feito** (chamada vai para a coluna da direita, até 4 linhas; seta vertical desce pela margem direita até a zona do link) |
| Modelo `maissobre`: 2–4 fatos ≤ 70 car. com marcador, dado forte grande opcional, miniatura do post, CTA | **Feito** (marcador muda por canal: losango GTA, bolinha Futebol/Destinos, quadrado Filmes, traço Receitas/Carros) |
| Modelo `interacao`: pergunta ≤ 60 car. + zona livre da enquete; "você prefere" com 2 fotos | **Feito** |
| Personalidade por canal (§4.6 + lista da tarefa) | **Feito** — ver §9 abaixo, modelo por modelo |
| Nada importante nos 250 px do topo nem nos 350 px da base | **Feito** (todo texto E todo elemento — cartão, pílulas, seta, CTA — ficam em y 250–1570; só o contorno da zona do link desce até 1640, porque `marca.ZONA_LINK` é assim — ver §8) |
| Texto sempre cabe: reduz até um mínimo e recusa em português | **Feito** (`ajustar()`: desce de 2 em 2 px até o mínimo; `ErroStory` "O texto … não cabe em N linha(s) … Encurte o 'campo'"; limite de caracteres checado antes) |
| Sem emoji (`marca.sem_emoji`) | **Feito** (em todo campo de texto, na normalização do spec) |
| Crédito da foto quando houver `credito_foto` | **Feito** (pílula escura dentro do cartão, canto inferior esquerdo) |
| `<nome>_zonas.json` com zonas em pixels e em fração (`link_fracao`, `enquete_fracao`) | **Feito** (só das figurinhas pedidas; + `largura`, `altura`, `figurinhas`) |
| Determinístico (mesmo SHA-256 do PNG) | **Feito** (sem hora, random só com semente fixa, JPG qualidade 92 fixa, PNG sem metadado; teste compara SHA do PNG e do JPG) |
| Capa ausente → fundo gerado no degradê do canal | **Feito** (`capa_gerada`, sem texto) |
| Foto tratada como `marca.TRATAMENTO_FOTO` (contraste ×1.12, cor ×1.10, brilho ×0.96, vinheta 0.55), cor natural | **Feito** (teste numérico: cinza continua cinza, canto < 60 % do centro) |
| Fontes via `marca.fonte()`; fallback no Linux | **Feito** (testes rodam com DejaVu; exemplos gerados com Anton/Barlow/DM Serif do cache; Bauhaus 93, Segoe e Bahnschrift só existem no Windows → substitutas da `marca.SUBSTITUTAS`) |
| Testes ≥ 45, sem rede, sem olhar imagem, capas sintéticas em `tmp_path` | **Feito**: 136 testes (18 combos parametrizados × 5 invariantes + regras + spec + CLI) |
| 18 exemplos em < 60 s (tempo medido) | **Feito**: 2,5–3,9 s os 18 + prancha (teste mede e exige < 60 s) |
| `LEIA_story_artes.md` de 1 página para leigo | **Feito** |
| Prancha e JPGs gerados com as fontes reais, vistos a olho, 2+ rodadas de ajuste | **Feito**: 3 rodadas (v1 → v2 → final), descritas em §9 |

Nada ficou pela metade. Não deu / não fiz de propósito: nenhum item.

## 2. Arquivos

**Novos** (todos em `scripts/`):
- `scripts/story_artes.py` — API `render(spec, saida=, png=, devolver_camadas=)`, `render_todas`, `render_exemplos`, CLI (192 linhas)
- `scripts/story_artes_base.py` — acha o hpbase (mesmo truque do `reel_futebol_base.py`), constantes das zonas, `normalizar_spec`, `ajustar`/`quebrar`/`tokens_destaque`, `bloco_texto` (degradê, contorno, itálico falso, sublinhado), `Tela` (fundo + camadas de texto com bbox), formas (pílula/etiqueta/caixa, cartão arredondado, seta vetorial), `tratar_foto`, `enquadrar`, `capa_gerada`, `zonas_de`, `gravar_imagem` (680 linhas)
- `scripts/story_artes_canais.py` — `ESTILOS` por canal (só com cores/fontes de `marca.CANAIS`), `estilo(canal, cor_destaque)`, `pintar_fundo`, `selo_hp`, `marcador` (275 linhas)
- `scripts/story_artes_modelos.py` — cabeçalho, cartão, título por estilo, zonas, CTA e os 3 modelos (290 linhas)
- `scripts/story_artes_exemplos.py` — os 18 specs de exemplo, `capa_sintetica` (determinística), `prancha` (192 linhas)
- `scripts/testes/test_story_artes.py` — 136 testes (607 linhas)
- `scripts/LEIA_story_artes.md`
- `docs/rodada2/D.md` (este)

**Arquivos da rodada 1 alterados:** nenhum. (Não toquei em `hpbase/marca.py`, `story_post.py` nem em `tests/conftest.py`.)

## 3. Patches

Nenhum arquivo da rodada 1 foi alterado.

## 4. Testes

Comando exato (sem `HP_FONTES_CACHE`, fallback DejaVu — a fixture autouse apaga `HP_FONTES`, `HP_FONTES_CACHE` e `HP_APP` e aponta `HP_LOCAL`/`HP_DRIVE` para `tmp_path`):

```
cd scripts && python3 -m pytest -q -p no:cacheprovider testes/test_story_artes.py
136 passed in 10.12s
```

Suíte inteira dos scripts (rodada 1 + a nova), para provar que nada quebrou:

```
cd scripts && python3 -m pytest -q -p no:cacheprovider testes
320 passed in 45.76s
```
(181 da rodada 1 continuam passando; os módulos de `app/hp_studio_nuvem` não foram tocados.)

Conferência extra, fora do pytest, com as fontes REAIS (`HP_FONTES_CACHE=<scratchpad>/fontes`): os mesmos invariantes (zona segura, contraste WCAG ≥ 4,5 de cada texto contra o fundo amostrado, variância ≤ 10 dentro das zonas) passam nos 18 exemplos; pior contraste = **4,58** (texto branco do rótulo/selo sobre a etiqueta vermelha `#E61E2D` do Carros).

O que cada grupo de teste prova (sem olhar a imagem):
- `test_tamanho_1080x1920` (×18); `test_todo_texto_na_zona_segura` (×18: bbox de cada camada de texto E de cada elemento, exceto `zona_*`, dentro de y 250–1570);
- `test_contraste_wcag_de_cada_texto` (×18: para cada camada de texto, média do fundo SEM os textos dentro do bbox × cada cor usada no texto ≥ 4,5);
- `test_zonas_das_figurinhas_sem_texto` (×18: desvio-padrão por canal ≤ 10 dentro da zona recuada 10 px, nenhum bbox cruza a zona, e o contorno fino existe);
- `test_cor_dominante_e_destaque_casam_com_o_canal` (×6: cor dominante ≈ uma das cores de fundo do canal, tolerância 48; ≥ 1500 px a ≤ 40 da `cor_post`);
- `test_zonas_json_ao_lado_do_jpg` (×18); emoji; SHA-256 igual em 2 renders (PNG e JPG); PNG só com `--png`; texto longo demais (limite e "não cabe") em português; fato/pergunta longos; 18 exemplos + prancha < 60 s; cartão encolhe com enquete; seta termina logo acima da zona do link; `cor_destaque` só no Futebol (magenta aparece no Futebol e não no Carros, com aviso) e cor de clube escura clareada; capa ausente; `foco`; crédito só quando houver; tratamento da foto; `enquadrar`; API de camadas; "você prefere"; personalidade por canal (degradê GTA, caixa Futebol, variação escura Filmes, faixa Receitas, traço Carros, barra Destinos); pílula "IDA E VOLTA" só em preço; padrões de rótulo/CTA; spec inválido (6 casos) e campos obrigatórios; `zonas_de`; `tokens_destaque` cola pontuação; `ajustar`; `bloco_texto`; resolvedor de fontes; CLI 0/1 (render, arquivo inexistente, spec inválido, JSON quebrado, sem comando, `todas` com canal errado, `spec-exemplo`, aviso de `cor_destaque`).

## 5. Suposições que sobraram

| Suposição | Arquivo | Onde trocar |
|---|---|---|
| `ZONA_LINK` (140,1500)-(940,1640) desce 70 px além da zona segura (1570). Mantive o valor de `marca.py` como está (é a verdade da §4.6); o contorno é o único elemento que entra nos 350 px da base. | `scripts/story_artes_base.py` | `ZONA_LINK = tuple(marca.ZONA_LINK)` (só muda se mudar em `hpbase/marca.py`) |
| No GTA, o `*destaque*` sai em ciano `#46E1EB` (extra do canal), porque o título inteiro já é o degradê rosa→laranja e rosa-sobre-rosa não destacaria nada. | `scripts/story_artes_canais.py` | `ESTILOS["gta"]["destaque"]` |
| Filmes: com `*destaque*` na chamada/pergunta uso a **variação escura** (caixa preta, contorno amarelo, texto branco, destaque amarelo); sem destaque, a caixa amarela com contorno preto e texto preto (amarelo sobre amarelo não lê). | `scripts/story_artes_modelos.py` | `titulo()`: `if caixa.get("escuro") and tem_destaque` |
| Receitas: a chamada e a pergunta vão na **faixa amarela** (DM Serif, texto escuro) e o `*destaque*` vira um sublinhado laranja (laranja sobre amarelo dá 2,0:1 e reprovaria o WCAG). Regra geral: se a cor de destaque não lê sobre a superfície, vira sublinhado. | `scripts/story_artes_modelos.py` | `titulo()`: `if superficie is not None and marca.contraste(cor_dest, superficie) < 4.5` |
| Carros: rótulo, CTA e selo "HP" em etiqueta (paralelogramo) vermelha `#E61E2D` com texto branco — contraste 4,58:1, passa por pouco. | `scripts/story_artes_canais.py` | `ESTILOS["carros"]["pilula"]`, `["cta"]`, `selo_hp()` (ramo `carros`) |
| Cor de clube escura (ex.: marinho) no Futebol é clareada (mistura com branco) só nos textos destacados até dar 4,5; a pílula/CTA ficam na cor pura com texto branco ou preto (o que ler melhor). | `scripts/story_artes_canais.py` | `estilo()`: `clarear_ate_ler` / `legivel_sobre` |
| Destinos: a pílula "IDA E VOLTA" aparece no `maissobre` quando `dado_forte.valor` contém "R$" (`"ida_volta": false` no spec esconde). | `scripts/story_artes_modelos.py` | `modelo_maissobre()`: `if est["canal"] == "destinos" and "R$" in df["valor"]` |
| Tamanho dos cartões: chamada normal 860×820 (y 352–1172); compacta 520×550 (y 350–900); miniatura do maissobre 320×348; fotos do "você prefere" 410×308. O enunciado só fixa a largura (~860 / ~520) e o y da compacta. | `scripts/story_artes_modelos.py` | constantes dentro de `modelo_chamada`, `modelo_maissobre`, `modelo_interacao` |
| Limites que o enunciado não dá: rótulo ≤ 22, CTA ≤ 24, `dado_forte.valor` ≤ 14, legenda ≤ 48, crédito ≤ 60 caracteres. | `scripts/story_artes_base.py` | `LIMITES` |
| `figurinhas` padrão: chamada e maissobre `["link"]`; interacao `["enquete"]` (e a enquete é sempre incluída no interacao). `maissobre` com enquete é recusado (não há lugar). | `scripts/story_artes_base.py` | `FIGURINHAS_PADRAO`, `normalizar_spec()` |
| `foco`: fração 0–1 da capa; valores > 1 são lidos como pixels da capa original. | `scripts/story_artes_base.py` | `enquadrar()` |

## 6. Depende do Antônio

- **Nada para rodar.** No PC só precisa de `pillow` e `numpy` (já usados pelos `posts_*.py`).
- Para as fontes saírem exatas no PC: nada a fazer — `marca.fonte()` acha `06 Projeto\marca\fontes` e `C:\Windows\Fonts` (Bauhaus 93, Segoe UI Black/Bold/Black Italic, Bahnschrift). Na nuvem elas são substituídas (Bauhaus → Anton, Segoe → Barlow, Bahnschrift → Barlow Condensed).
- **Conferir de olho** (passo a passo): `python scripts\story_artes.py exemplos C:\temp\stories` → abrir `C:\temp\stories\_prancha_story.jpg` e os 18 JPG. O que olhar está em §9.

## 7. Pendências para o Diretor

Sem rotina nova. Sugestão de SKILL curta para `.claude\` (texto pronto):

```
Story de divulgação (tarefa D): antes de o story_post subir um story, gere a arte com
`python scripts\story_artes.py render <spec.json>` (spec na LEIA_story_artes.md). Use o
`<nome>_zonas.json` para posicionar a figurinha de link (chave "link"/"link_fracao") e a de
enquete ("enquete"/"enquete_fracao"). Se o comando devolver código 1, leia a mensagem (em
português) e encurte o texto indicado; nunca ignore o erro para não sair texto cortado.
```

## 8. Decisões em aberto / conflitos

1. **Zona do link × zona segura.** `marca.ZONA_LINK = (140,1500,940,1640)` vai até y 1640, mas a regra da §4.6 é "nada nos 350 px da base" (y > 1570). Mantive a zona como a §4.6/`marca.py` dizem e deixei só o contorno fino entrar nessa faixa; todo texto e a ponta da seta terminam antes de 1500. Decisão do Antônio/Diretor: manter (a figurinha de link do Instagram fica mesmo perto do campo de resposta) ou subir a zona para (140,1430)-(940,1570) em `hpbase/marca.py` (o gerador e o `_zonas.json` seguem automaticamente).
2. **Rosa do GTA**: usei `GTA_ROSA_POST #FF48A0` (pílula, degradê do título, marcadores), como a §4.6 manda para arte de post/story; o selo "HP" do GTA é branco em itálico (como `arte_perfil.selo_hp`).
3. **Vermelho do Carros**: `#E61E2D` (post) em tudo, nunca `#FF2D2D`.
4. **Futebol**: verde `#1ED760` (nunca o amarelo da rodada 1); `cor_destaque` troca por cor de clube quando o spec traz.
5. Texto branco sobre a etiqueta vermelha do Carros fica em 4,58:1 (limite 4,5). Se quiserem folga, a alternativa é texto preto `#0F0F12` (4,56:1 — igual) ou escurecer levemente a etiqueta, o que muda a cor da marca: decisão do Diretor.

## 9. O que vi na prancha e nos JPGs (fontes reais) e o que o Antônio deve conferir

Gerado com `HP_FONTES_CACHE=<scratchpad>/fontes` em `<scratchpad>/story_artes_exemplos/` (18 JPG + 18 PNG + 18 `_zonas.json` + `_prancha_story.jpg` de 1620×1518; fora do repositório). Três rodadas:

- **v1 → v2:** a pontuação colada ao destaque ganhava espaço ("milhões ?", "2029 ,") — corrigido (pedaços de palavra sem espaço). A variação escura do Filmes perdia o amarelo do destaque (condição errada) — corrigido. O laranja do Receitas sobre a faixa amarela dava 2:1 — virou sublinhado laranja com texto escuro. Chamada de 1 linha ficava pequena por causa de um teto de tamanho por altura — agora o ajuste mede a altura real e usa até 96 px. Pergunta do interacao ficava colada no topo — centrada na faixa. Marcadores dos fatos um pouco baixos — subidos.
- **v2 → final:** chamada normal centrada entre o cartão e a linha "toque pra ver"; fatos com letra até 54 px quando sobra espaço; curvas de baixo do Destinos afastadas para não encostar na zona do link.

Modelo por modelo (o que está na prancha final):

**chamada** — cartão grande com cantos arredondados e o crédito numa pílula preta no canto inferior esquerdo da foto; rótulo em pílula à esquerda e selo HP + @ à direita, alinhados na mesma linha (y ≈ 290); chamada abaixo do cartão; "toque pra ver" com a seta curva desenhada descendo até o contorno da zona do link. GTA (com enquete) é o compacto: cartão 520 px à esquerda, título rosa→laranja em 3 linhas à direita com "GTA 6" em ciano, seta rosa vertical descendo pela margem direita até a zona do link, zona da enquete vazia no meio. Futebol: caixa preta translúcida com contorno branco fino atrás da chamada em Anton, rótulo e "reforço" na cor do clube (`#C8102E` do spec de exemplo). Filmes: caixa preta com contorno amarelo (variação escura, porque tem destaque "Duna 3"). Receitas: faixa amarela com DM Serif escuro e "cenoura" sublinhado em laranja. Carros: Anton em itálico com o traço vermelho embaixo e "Civic" em amarelo, etiqueta vermelha "NOVIDADE" e selo "HP" vermelho. Destinos: fundo azul-royal→marinho com curvas, barra ciano à esquerda da chamada e "R$ 2.990" em ciano.
*Conferir:* se a seta "toque pra ver" agrada (é um bezier com ponta triangular; dá para mudar curva/largura em `modelo_chamada`); se o crédito dentro da foto pode ficar ali; se no compacto a chamada em 3–4 linhas à direita do cartão serve.

**maissobre** — miniatura 320 px à esquerda, dado forte grande à direita ("R$ 80 mi" em Anton no Futebol, "19/11" em degradê no GTA, "40 min" em DM Serif no Receitas, "184 cv" itálico com traço no Carros, "R$ 2.990" com a pílula "IDA E VOLTA" no Destinos), legenda pequena embaixo; fatos com marcador do canal; CTA "Salva o post" em pílula (etiqueta no Carros, caixa amarela no Receitas) logo acima da zona do link.
*Conferir:* sobra espaço entre o último fato e o CTA quando há 3 fatos curtos (é proposital: o CTA fica sempre no mesmo lugar); se preferir, dá para puxar o CTA para logo abaixo dos fatos.

**interacao** — pergunta grande centrada (Bauhaus-fallback em degradê no GTA; caixa preta translúcida no Futebol; caixa amarela/escura no Filmes; faixa amarela em DM Serif no Receitas; itálico com traço no Carros; barra ciano no Destinos); zona da enquete vazia com contorno fino; "Responde aí" em texto pequeno abaixo. GTA, Filmes e Carros mostram o "você prefere": duas fotos lado a lado entre a pergunta e a zona.
*Conferir:* nas fotos do "você prefere" não há letra A/B dentro (de propósito: a enquete do Instagram traz as opções); se quiser rótulos, é texto novo e passa pelos mesmos testes.

Fundos: GTA céu com brilho rosa e estrelas só no topo (y < 230); Futebol estúdio escuro com brilho verde no canto inferior esquerdo e fio verde no topo; Filmes cantos amarelos e perfuração de filme na base; Receitas faixas amarelas inclinadas no topo e na base com fio laranja; Carros trapézio vermelho no topo, fio vermelho e faixa cinza na base; Destinos curvas ciano-claro nos cantos. Nenhum desses enfeites entra nas zonas das figurinhas nem atrás de texto (os testes provam).

As "fotos" dos exemplos são sintéticas (degradê + círculos + um retângulo claro no centro): servem para ver o enquadramento e o tratamento, não para julgar a foto. No PC, basta apontar `capa` para a imagem real do post.
