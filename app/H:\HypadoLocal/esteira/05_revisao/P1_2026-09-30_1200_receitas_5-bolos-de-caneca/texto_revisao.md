# Revisão — P1_2026-09-30_1200_receitas_5-bolos-de-caneca

- Rodada: 1 (voltas até agora: 0 de 2)
- Canal: Receitas | HP (@hp.receitas) · tipo: carrossel · prioridade: P1
- Horário alvo: 2026-09-30T12:00-03:00 · redes: instagram, pinterest
- Título: 5 bolos de caneca
- Crédito: (sem fonte externa)

## Conferência automática
- Arquivos: arte/arte_01.png, arte/arte_02.png, arte/arte_03.png

## Quadros (olhe os 3)
- revisao/quadro_1_inicio.jpg (arte/arte_01.png)
- revisao/quadro_2_meio.jpg (arte/arte_02.png)
- revisao/quadro_3_fim.jpg (arte/arte_03.png)

## Legenda do post
```
5 bolos de caneca
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
