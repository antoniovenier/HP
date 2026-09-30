# Revisão — P1_2026-09-30_1830_gta_rockstar-quinta

- Rodada: 1 (voltas até agora: 0 de 2)
- Canal: GTA 6 | HP (@hpgta6) · tipo: reel · prioridade: P1
- Horário alvo: 2026-09-30T18:30-03:00 · redes: instagram
- Título: Rockstar quinta
- Crédito: @rockstargames
- Fonte: https://www.youtube.com/watch?v=x

## Conferência automática
- Resolução: 1080x1920 (ok)
- Duração: 15.0 s
- Loudness: -14.0 LUFS (alvo -14.0; ok)
- Legenda queimada: sim (1 falas) · dublagem: não · narração Toque HP: não

## Quadros (olhe os 3)
- revisao/quadro_1_inicio.jpg (1.0 s)
- revisao/quadro_2_meio.jpg (7.5 s)
- revisao/quadro_3_fim.jpg (14.0 s)

## Legenda queimada (legenda.srt)
```
1
00:00:00,000 --> 00:00:02,000
(legenda simulada)
```

## Legenda do post
```
Rockstar quinta

Crédito: @rockstargames
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
