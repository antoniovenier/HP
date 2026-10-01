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
