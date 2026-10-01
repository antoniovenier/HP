# Convenções da entrega da nuvem (valem para TODOS os módulos)

Estrutura do repositório (espelha o PC do Antônio):
- `app/` = `G:\Meu Drive\Hypado\06 Projeto\app\`
  - `app/manuais/` = manuais 04–13 + README.md
  - `app/hp_studio_nuvem/hpbase/` = base comum (JÁ PRONTA, não reescrever)
  - `app/hp_studio_nuvem/<modulo>/` = cada módulo novo (pacote Python) com `LEIA.md` e `testes/`
  - sem `conftest.py` em `app/` (o PC pode já ter um): cada `testes/` tem o seu, que importa a fixture autouse de `hpbase/pytest_raizes.py` (HP_LOCAL e HP_DRIVE → pastas temporárias)
- `scripts/` = `G:\Meu Drive\Hypado\scripts\` (scripts avulsos novos, cada um com testes em `scripts/testes/`)

Base `hpbase` (importar com `from hpbase import ...`, pois `app/hp_studio_nuvem` está no sys.path; nos scripts, adicionar o caminho do app ao sys.path):
- `raiz_local()` (H:\HypadoLocal ou env HP_LOCAL), `raiz_drive()` (G:\Meu Drive\Hypado ou HP_DRIVE), `pasta_app()`, `pasta_logs()`, `pasta_segredos()`, `garantir(p)`
- `obter_logger(nome)` → log em `H:\HypadoLocal\app\logs\<nome>_<dia>.log`, mascarando segredos; `mascarar(txt)`
- `TravaPesada(dono, ignorar_horario=False, agora=None)` (context manager, pesado.lock, 1 por vez, horário 18h–22h30 proibido), `TravaOcupada`, `janela_proibida(agora)`
- `rodar(cmd, timeout)` → subprocess com CREATE_NO_WINDOW no Windows; `achar_ffmpeg()`, `achar_ffprobe()` (pode ser None → usar plano B com ffmpeg)
- `ler_segredo(arquivo, chave)` (nunca imprimir o valor), `SegredoAusente`
- `ler_json`, `escrever_json` (atômico), `agora()`, `agora_iso()` (fuso de Brasília), `anexar_linha(p, txt)`, `FUSO`

Regras de código:
- Python 3.12 no Windows 11 (testar aqui em 3.11 Linux; usar pathlib, nunca caminho fixo com barra).
- Português BR em comentários, mensagens e nomes quando natural.
- Nada de tokens/senhas em código ou log. Nada de bibliotecas que imitam protocolo de rede social.
- Toda chamada de rede isolada numa função/classe injetável para os testes usarem um falso (nenhum teste acessa a internet).
- Todo módulo que age no mundo real tem `--simular` / modo sombra.
- Cada módulo tem CLI (`python -m <pacote> ...` ou `python scripts\x.py ...`) com `--help` em português.
- Testes com pytest: `cd app\hp_studio_nuvem && python -m pytest -q <modulo>` e `cd scripts && python -m pytest -q testes` (cada teste de script tem a própria fixture de raízes temporárias). Nenhum teste pode depender de rede, emulador ou WhatsApp reais.
- ffmpeg está no PATH do ambiente de teste (ffprobe NÃO está: use `achar_ffprobe()` e tenha plano B).
- LEIA.md curto por módulo: o que faz, instalação (pip), comandos, como ligar o modo sombra, como integrar ao `hp`/motor já existente (que não temos aqui — descrever o gancho: função `executar(trabalho: dict) -> dict`).

## Rodada 2 (01/10/2026): o que mudou nas convenções

- O pacote da nuvem chama-se `app/hp_studio_nuvem/` (no PC: `06 Projeto\app\hp_studio_nuvem\`, pacote irmão do `hp_studio` do PC). Os nomes curtos de import (`hpbase`, `esteira`, `metricas`, `whatsapp_local`, `qa_paridade`, `publicar_extra`) continuam. Nunca importar `hp_studio.esteira` nem `hp_studio.metricas`.
- `tests/fixtures/pc_real/` guarda os formatos REAIS copiados do PC (Seção 4 do `docs/PROMPT_NUVEM_2.md`); `tests/test_contrato_pc_real.py` passa cada fixture pelo adaptador responsável e é o que o PC roda depois de cada integração. `tests/conftest.py` põe `app/hp_studio_nuvem`, `scripts` e `radar_fontes` no sys.path.
- Paleta, fontes, tamanhos e zonas seguras vêm SÓ de `hpbase/marca.py` (nenhum módulo duplica cor). Resolvedor `marca.fonte(nome, tamanho)`: `HP_FONTES`/`06 Projeto\marca\fontes` → `C:\Windows\Fonts` → cache `HP_FONTES_CACHE`/`H:\HypadoLocal\fontes` → DejaVu; nunca usa rede (`python -m hpbase.marca baixar-fontes` é o comando explícito).
- Rede com o PC: `publicar_extra/contrato_pc.py` (cópias de `Resposta`, `ErroRede`, `entrada()` e o `ClienteFalso` dos testes). No PC, importar de `hp_studio.publicar.http`.
- Formato de entrega: `python docs/compilar_entrega_2.py` gera `ENTREGA_NUVEM_HP_STUDIO_2.md` (só arquivos novos desde a rodada 1 + os 3 documentos de controle + o diff dos alterados) e `python docs/desempacotar_check.py <md> --comparar-com .` prova que desempacota sem arquivo sem bloco nem arquivo falso. Regra: nenhuma linha dentro de um arquivo pode começar com `## nome.ext`; nenhum arquivo com nome de segredo.
- Relatórios dos agentes da rodada 2 em `docs/rodada2/<TAREFA>.md` (fonte do `ENTREGA.md`, `PATCHES.md` e `PENDENCIAS_PARA_O_DIRETOR.md`).
