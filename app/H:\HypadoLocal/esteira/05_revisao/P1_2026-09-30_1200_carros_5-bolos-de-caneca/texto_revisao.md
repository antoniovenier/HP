# Revisão — P1_2026-09-30_1200_carros_5-bolos-de-caneca

- Rodada: 1 (voltas até agora: 0 de 2)
- Canal: Carros | HP (@hp.carros) · tipo: threads_texto · prioridade: P1
- Horário alvo: 2026-09-30T12:00-03:00 · redes: threads
- Título: 5 bolos de caneca
- Crédito: (sem fonte externa)

## Conferência automática
- Arquivos: texto_threads.txt

## Legenda do post
```
Qual carro você levaria?
```

## Como responder
Grave UM arquivo nesta pasta (ou use a linha de comando):
- `aprovado.json` — `python -m esteira aprovar <item> --notas gancho=9 legenda=8 ...`
- `refazer.json` — `python -m esteira refazer <item> --motivo "..." --notas ...`

```json
{"notas": {"assunto": 9, "fonte_credito": 10, "gancho": 8, "legenda": 7}, "motivo": "...", "etapa_destino": "(opcional)", "ajustes": {}, "revisor": "Claude"}
```

Faixas: média >= 9 Excelente, 7 a 8,9 Bom (aprovado); 5 a 6,9 Médio (volta para a etapa do critério de menor nota); abaixo de 5 Razoável (volta ao Curador). Máximo 2 voltas; na seguinte vai para 99_erros.

| critério | volta para |
|---|---|
| assunto | 01_pedidos |
| fonte_credito | 01_pedidos |
| gancho | 04_edicao |
| legenda | 03_legenda_dublagem |
| voz | 03_legenda_dublagem |
| audio | 04_edicao |
| enquadramento | 04_edicao |
| ritmo | 04_edicao |
| capa | 04_edicao |
| arte | 04_edicao |
| texto_post | 04_edicao |
