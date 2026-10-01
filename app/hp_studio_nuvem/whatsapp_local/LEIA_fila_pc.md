# fila_pc — a fila real do WhatsApp do PC e o aviso "no ar" literal

Módulo `whatsapp_local/fila_pc.py` (rodada 2, tarefa A7). Faz o `whatsapp_local`
falar o formato que o plantão de hoje usa, sem o Claude e sem rede.

## O que ele faz

1. **Fila real → pasta.** O plantão guarda uma LISTA em
   `H:\HypadoLocal\temp\whatsapp_fila.json`: `[{"grupo", "texto", "enviar_apos"}]`.
   O enviador local lê `H:\HypadoLocal\whatsapp_fila\` (1 JSON por mensagem).
   `importar` converte a lista para a pasta, sem duplicar (o id é um hash de
   grupo + texto + enviar_apos) e guardando o `enviar_apos`.
2. **Pasta → fila real.** `exportar` devolve as mensagens pendentes no formato
   da lista, com o `enviar_apos` intacto.
3. **Validação:** o texto começa exatamente com `*Claude - *`; o grupo é um dos
   6 nomes exatos (`HP | Comissão 🚀`, `HP | Futebol ⚽`, `HP | Filmes 🎬`,
   `HP | Receitas 🍔`, `HP | Carros 🏎️`, `HP | Destinos ✈️`); `enviar_apos` no
   formato `AAAA-MM-DD HH:MM`. O que não passa vai para `rejeitadas\` com o motivo.
4. **Madrugada (0h–7h30):** nada sai. Mensagem criada nessa janela sem
   `enviar_apos` ganha `07:30` do mesmo dia; o enviador adia o que ainda não
   chegou na hora (fica na fila, não é rejeitado).
5. **agendados.json real** dos 6 lugares (`06 Projeto\agendados.json` do GTA e
   `07 Canais\<Futebol|Filmes e Series|Gastronomia|Carros|Viagens>\agendados.json`),
   e `avisos_enviados.json` mesmo quando o PowerShell embrulha a lista
   (`[{"value": [...], "Count": N}]`).
6. **Aviso "no ar"** no texto literal do `AVISO.md` (só as redes em que o post
   saiu, na ordem Instagram, Facebook, TikTok, YouTube, Threads; rede sem link
   usa o link do perfil e não atrasa). O vigia (`tarefas_automaticas`) já monta
   assim para todo item que vier de um `agendados.json` real.

## Como usar (na pasta `app\hp_studio_nuvem`)

```
python -m whatsapp_local.fila_pc importar --agora "2026-09-30 10:00" [--so-mostrar] [--limpar]
python -m whatsapp_local.fila_pc exportar [--arquivo H:\HypadoLocal\temp\whatsapp_fila.json]
python -m whatsapp_local.fila_pc agendados
python -m whatsapp_local.fila_pc avisos --agora "2026-09-30 10:00"
```

`--agora` é obrigatório: o módulo nunca lê o relógio sozinho. `--limpar` esvazia
o arquivo do PC depois de importar — use só quando o plantão antigo estiver
desligado (senão as duas filas mandam a mesma mensagem).

## Suposições a confirmar com o Antônio

- Para os canais o aviso usa o mesmo modelo do GTA trocando o cabeçalho por
  `🎬 *Novo post no ar — <Canal> | HP!*` (constante `CABECALHO_CANAL`).
- Links de perfil quando falta o link da rede (`PERFIL`): o do Facebook é palpite.
- Mensagem que não é resumo nem "no ar" (ex.: "Pinterest pronto") entra com
  `tipo: "aviso"`; a validação dura do enviador (`TIPOS_PERMITIDOS`) ainda só
  aceita os 3 tipos — decisão em aberto no relatório.
- No `exportar`, mensagem sem `enviar_apos` sai com `"enviar_apos": null`.
