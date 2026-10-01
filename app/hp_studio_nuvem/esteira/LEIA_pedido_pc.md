# pedido_pc — a esteira da nuvem aceita o pedido REAL do PC

O Claude larga em `01_pedidos` o mesmo `pedido.json` que o `hp_studio\esteira\pedido.py` do PC
entende (§4.5 do prompt da rodada 2). A esteira da nuvem reconhece esse formato sozinha: nada muda
no comando (`python -m esteira ...`).

## O que o módulo faz

| Função | Para quê |
|---|---|
| `para_esteira(pedido, config=None)` | Converte o pedido do PC para o modelo interno (`tipo` corte→reel, texto→threads_texto; `prioridade` 0/1/2→P0/P1/P2; `data` AAAA-MM-DDTHH:MM→`horario_alvo` com fuso de Brasília; `video`/`link`→`fonte_url`, `arquivo`→`arquivos`; crédito e dublagem pelo `config.json`). `esteira.pedido.normalizar_pedido` chama isto quando vê `"tipo": "corte"/"texto"`, `"data"` ou prioridade inteira. |
| `para_post_json(pedido, arquivos=None, capa=None)` | Monta o `post.json` do contrato com o `publicar` do PC (`canal`, `tipo`, `quando "AAAA-MM-DD HH:MM"`, `titulo`, `legenda`, `arquivos`, `capa`, `tags`, `dublado`, `redes`). Entende os apelidos `ig fb th yt shorts tt pin` e `short→reel`, `foto→feed`, `longo→video`; `textos {rede: texto}` vira `redes` como objeto. |
| `nome_da_pasta(pedido)` | `P<n>_AAAA-MM-DD_HHMM_<canal(até 20)>_<apelido(até 40)>`, tudo ASCII sem espaço (apelido = `apelido` do pedido, senão o gancho, senão o título). É o mesmo nome que `criar_pedido` dá à pasta. |
| `ler_pedido_pc(caminho, agora=None, mtime=None)` | Lê um `.json` solto SÓ depois de 2 s parado (nada meio gravado); antes disso devolve `None`. Relógio e data do arquivo são injetáveis. |
| `ler_config_pc()` | Lê `G:\Meu Drive\Hypado\06 Projeto\config.json` (a variável `HP_CONFIG_PC` troca o caminho). |

Constantes reais do PC: `TIPOS`, `REDES`, `REDES_PADRAO`, `ARTES_STORY`, `CAMPOS_DO_PLANO`.

## O que ele recusa (`ErroParametro`, mensagem em português; o item vai para `99_erros`)

- Flow Games (`flow games|flowgames|flow podcast|flowpodcast|flow_games`) em `streamer`, `credito`, `link`, `gancho` ou `titulo`.
- Corte de criador que não está no `config.json` ou está sem `"autorizado": true`. **Sem `config.json` nenhum criador é autorizado** (estáticos passam, porque não têm criador).
- Vazamento de GTA (`vazad`, `vazament`, `leak`) no GTA.
- `data` fora de `AAAA-MM-DDTHH:MM`, tipo/rede/prioridade desconhecidos, corte sem `video`/`link`/`arquivo`, story sem `arte` válida, texto sem `texto`, carrossel sem `spec`.

## Como usar no PC

1. Nada para instalar: o arquivo fica em `06 Projeto\app\hp_studio_nuvem\esteira\pedido_pc.py`.
2. Para a esteira conferir os criadores, o `config.json` do GTA precisa estar em
   `G:\Meu Drive\Hypado\06 Projeto\config.json` (já está). Em outra máquina: `set HP_CONFIG_PC=<caminho>`.
3. Conferir um pedido antes de largar na esteira (PowerShell em `06 Projeto\app\hp_studio_nuvem`):
   ```powershell
   python -c "import json,sys; from esteira import pedido_pc as p; d=json.load(open(sys.argv[1], encoding='utf-8')); print(p.nome_da_pasta(d)); print(json.dumps(p.para_post_json(d), ensure_ascii=False, indent=1))" H:\HypadoLocal\esteira_sombra\01_pedidos\meu_pedido.json
   ```
   Se der `ErroParametro`, a mensagem diz o que arrumar.
4. Testes: `cd "G:\Meu Drive\Hypado\06 Projeto\app\hp_studio_nuvem" ; python -m pytest -q esteira\testes\test_pedido_pc.py`

Decisão em aberto (o Diretor): criador gringo (`"idioma": "en"`) no GTA sai **dublado** no PC, mas a
regra da rodada 1 (`CANAIS_COM_VOZ` em `esteira/constantes.py`) ainda não tem `gta` — a validação
recusa o reel dublado no GTA até essa linha mudar.
