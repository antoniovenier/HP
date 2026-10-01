# Modelo do aviso "no ar" (WhatsApp)

Este arquivo é lido pelo enviador local de WhatsApp (`whatsapp_local`) para
montar o aviso "no ar" **sem o Claude**. O lugar dele no PC é
`G:\Meu Drive\Hypado\06 Projeto\AVISO.md` (este aqui, dentro do pacote, é só o
exemplo usado quando aquele não existe).

**Só o que está entre as duas marcas abaixo vira mensagem.** O resto do
arquivo é explicação e pode ser mudado à vontade.

Marcadores (trocados sozinhos pelo app):

| Marcador | Vira | Exemplo |
|---|---|---|
| `{canal}` | nome do canal | GTA 6 \| HP |
| `{titulo}` | título do post | Rockstar confirma novo trailer |
| `{horario}` | hora que entrou no ar | 18:30 |
| `{data}` | dia que entrou no ar | 30/09 |
| `{links}` | uma linha por rede, na ordem Instagram, TikTok, YouTube, Facebook, Threads, Pinterest | Instagram: https://… |
| `{redes}` | lista das redes | Instagram, TikTok e YouTube |
| `{link}` | só o primeiro link | https://… |
| `{link_instagram}`, `{link_tiktok}`… | o link de uma rede só | https://… |

Regras:
- a mensagem **tem** que começar com `*Claude - *` (se esquecer, o app coloca);
- marcador escrito errado fica do jeito que está (aparece no relatório da sombra);
- linhas em branco repetidas viram uma só.

<!-- MODELO_WHATSAPP -->
*Claude - * 🚀 No ar agora — {canal}

🎬 {titulo}
🕒 {horario}

{links}
<!-- FIM_MODELO -->
