# youtube_extra — o que falta no YouTube além do envio

O envio de vídeo (`videos.insert`) **já existe no PC** (`hp_studio\publicar\youtube.py`). Este módulo
só cobre as lacunas, para ligar quando o Google aprovar a auditoria da API:

| Função | O que faz | Custo (unidades) |
|---|---|---|
| `playlist_do_canal(cliente, token, canal, titulo)` | acha a playlist pelo título (cache → API, todas as páginas) e só cria se não existir — **nunca duplica** | 1 por página + 50 se criar |
| `adicionar_na_playlist(cliente, token, playlist_id, video_id)` | confere antes; "já está na playlist" não é falha | 1 + 50 |
| `atualizar_video(cliente, token, video_id, titulo=, descricao=, tags=, categoria=, publicar_em=)` | corrige um vídeo já enviado; `publicar_em` é hora de **Brasília** (vai em UTC para a API) | 1 + 50 |
| `conferir_lote(cliente, token, esperado)` | confere até 50 vídeos por chamada e diz quem está **travado como privado (projeto sem auditoria)**, rejeitado, falhou, processando | 1 a cada 50 |
| `transcricao_para_srt(dados, inicio, fim)` | transcrição do PC → legenda SRT (não usa rede) | 0 |
| `enviar_legenda(cliente, token, video_id, srt, ligado=True)` | manda a legenda; **vem desligada** porque custa 400 unidades (4 % do dia) | 400 |
| `registro_de_cota(chamadas)` / `Contador` | soma o que gastou no dia e avisa a 80 % das 10.000 unidades | — |

## Instalação

Nada a instalar: só Python 3.11/3.12 e o pacote `hpbase` da nuvem (já no `app\hp_studio_nuvem`).
No PC, o `contrato_pc.py` troca `Resposta`/`ErroRede` pelas de `hp_studio.publicar.http`.

## Uso (no PC, com o cliente e o token que o PC já tem)

```python
from publicar_extra.youtube_extra import playlist_do_canal, adicionar_na_playlist, conferir_lote, Contador
cont = Contador()                                   # conta a cota do dia
tok = token_de("gta")                               # o PC faz o OAuth; este módulo nunca vê refresh token
pid = playlist_do_canal(cliente, tok, "gta", "GTA 6 — Notícias", registrar=cont.registrar)
print(adicionar_na_playlist(cliente, tok, pid, "ID_DO_VIDEO", registrar=cont.registrar))
# {"status": "adicionado" | "ja_estava" | "erro", "link": ..., "id": ..., "erro": ...}
r = conferir_lote(cliente, tok, {"ID_DO_VIDEO": {"status_pedido": "agendado", "publicar_em": "2026-10-02 09:00"}})
print(r["ID_DO_VIDEO"]["diagnostico"], r["resumo"])
print(cont.resumo()["mensagem"])                    # "cota do YouTube: 103 de 10000 unidades usadas (1 %)"
```

## Regras que o módulo garante

- Token só no cabeçalho `Authorization: Bearer …`; nunca na URL, no log, no erro nem no cache.
- Validação **antes** de chamar a API: título ≤ 100 sem `<` `>`, descrição ≤ 5.000 **bytes** (acento conta 2),
  tags ≤ 500 caracteres contando vírgulas e aspas (regra do YouTube), categoria numérica. Erro sai com
  `status: "invalido"` e **zero** chamadas.
- `publishAt` só com vídeo privado nunca publicado, no futuro; horário passado é recusado (o YouTube
  publicaria na hora).
- Erros da API viram frase em português: cota esgotada (volta à meia-noite da Califórnia), limite de
  100 envios/dia, token vencido (o PC renova), sem permissão/auditoria, duplicado, não encontrado.
- Cache das playlists: `H:\HypadoLocal\app\publicar\youtube_playlists.json` = `{canal: {titulo: id}}`,
  gravado de forma atômica; nos testes vai para uma pasta temporária (`HP_LOCAL`).

## Testes

```
cd app\hp_studio_nuvem
python -m pytest -q -p no:cacheprovider publicar_extra\testes\test_youtube_extra.py
```

Nenhum teste faz rede: tudo passa pelo `ClienteFalso` do `contrato_pc.py`.
