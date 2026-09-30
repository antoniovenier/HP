"""Seletores do WhatsApp Web — O ÚNICO lugar que conhece o HTML da página.

O WhatsApp muda a página de tempos em tempos. Quando o enviador parar de
achar alguma coisa (o log diz "elemento não encontrado: <NOME>"), é AQUI que
se mexe, e só aqui.

Estratégia (da mais estável para a menos estável):
  1. `data-testid`  — atributos de teste; mudam pouco, mas o WhatsApp tem
                       tirado vários deles nas versões novas;
  2. `aria-label` / `role` — acessibilidade; estável, mas depende do idioma
                       (o navegador abre em pt-BR; deixamos o inglês de reserva);
  3. `data-icon` / ids (`#main`, `#pane-side`) — estruturais;
  4. classes (`message-in`, `selectable-text`) — último recurso.

Cada constante é uma LISTA de alternativas: o código tenta na ordem e usa a
primeira que existir na página. Para consertar, acrescente a nova
alternativa NO COMEÇO da lista (sem apagar as antigas de cara).

Como descobrir um seletor novo: rode `python -m whatsapp_local login`
(janela visível), clique com o botão direito no elemento > Inspecionar, e
procure `data-testid`, `aria-label`, `role` ou `data-icon` no HTML.
"""

# --- Tela inicial --------------------------------------------------------
# Lista de conversas: se aparece, estamos logados.
LISTA_CONVERSAS = [
    '[data-testid="chat-list"]',
    '#pane-side',
    'div[aria-label="Lista de conversas"]',
    'div[aria-label="Chat list"]',
]

# QR code de login: se aparece, NÃO estamos logados (o Antônio precisa
# rodar `login` e escanear; o código nunca digita nada de login).
QR_CODE = [
    'canvas[aria-label*="QR" i]',
    '[data-testid="qrcode"]',
    'div[data-ref] canvas',
    'canvas[aria-label*="Scan" i]',
    'canvas[aria-label*="Escaneie" i]',
]

# --- Busca de conversa ----------------------------------------------------
# Caixa "Pesquisar ou começar uma nova conversa" (é um div editável).
CAIXA_BUSCA = [
    '[data-testid="chat-list-search"]',
    'div[contenteditable="true"][role="textbox"][aria-label*="Pesquisar" i]',
    'div[contenteditable="true"][role="textbox"][aria-label*="Search" i]',
    'div[contenteditable="true"][data-tab="3"]',
    'input[aria-label*="Pesquisar" i]',
    'input[aria-label*="Search" i]',
]

# Nome de cada conversa nos resultados da busca. O atributo `title` traz o
# nome COMPLETO, com emoji em texto (o texto visível troca o emoji por
# <img>, por isso lemos com JS_TEXTO_COM_EMOJI, que prefere o `title`).
TITULOS_RESULTADO = [
    '#pane-side span[title]',
    '[data-testid="cell-frame-title"] span[title]',
    '[data-testid="cell-frame-title"] span[dir="auto"]',
    'div[aria-label*="Resultados" i] span[title]',
    'div[aria-label*="Search results" i] span[title]',
]

# --- Conversa aberta ------------------------------------------------------
# Cabeçalho (topo) da conversa aberta.
CABECALHO_CONVERSA = [
    '#main header',
    '[data-testid="conversation-header"]',
    'div#main div[role="banner"]',
]

# Título do cabeçalho = NOME do grupo aberto. É o que conferimos, exato,
# antes de enviar. O primeiro que devolver texto vale.
TITULO_CONVERSA = [
    '#main header [data-testid="conversation-info-header-chat-title"]',
    '#main header span[data-testid="conversation-info-header-chat-title"]',
    '#main header div[role="button"] span[dir="auto"][title]',
    '#main header span[title]',
    '#main header div[role="button"] span[dir="auto"]',
    '#main header span[dir="auto"]',
]

# Linha de baixo do cabeçalho (participantes do grupo / "online" / "visto
# por último"). Usada só para confirmar que é GRUPO e não contato.
SUBTITULO_CONVERSA = [
    '#main header [data-testid="conversation-info-header"] span[title]',
    '#main header div[role="button"] > div:nth-child(2) span[title]',
    '#main header div[role="button"] > div:nth-child(2) span',
]

# Ícone de grupo (avatar padrão de grupo no cabeçalho).
MARCADOR_GRUPO = [
    '#main header [data-icon="default-group"]',
    '#main header [data-icon="default-group-refreshed"]',
    '#main header [data-icon="community"]',
]

# Caixa "Digite uma mensagem" (div editável no rodapé da conversa).
CAIXA_MENSAGEM = [
    '[data-testid="conversation-compose-box-input"]',
    '#main footer div[contenteditable="true"][role="textbox"]',
    '#main footer div[contenteditable="true"][data-tab="10"]',
    'div[contenteditable="true"][aria-label*="Digite uma mensagem" i]',
    'div[contenteditable="true"][aria-label*="Type a message" i]',
]

# Botão de enviar (setinha) da mensagem de texto.
BOTAO_ENVIAR = [
    '[data-testid="send"]',
    '#main footer button[aria-label="Enviar"]',
    '#main footer button[aria-label="Send"]',
    '#main footer [data-icon="send"]',
    '#main footer [data-icon="wds-ic-send-filled"]',
]

# --- Anexos ---------------------------------------------------------------
# Botão do clipe / "+" que abre o menu de anexos.
BOTAO_ANEXAR = [
    '[data-testid="clip"]',
    '#main footer button[aria-label="Anexar"]',
    '#main footer button[title="Anexar"]',
    '#main footer button[aria-label="Attach"]',
    '#main footer [data-icon="plus-rounded"]',
    '#main footer [data-icon="plus"]',
    '#main footer [data-icon="clip"]',
]

# Campo de arquivo escondido de "Fotos e vídeos" (recebe set_input_files).
INPUT_ARQUIVO_MIDIA = [
    'input[type="file"][accept*="image"]',
    'input[type="file"][accept*="video"]',
]

# Campo de arquivo escondido de "Documento".
INPUT_ARQUIVO_DOCUMENTO = [
    'input[type="file"][accept="*"]',
    'input[type="file"]:not([accept*="image"])',
    'input[type="file"]',
]

# Caixa de legenda na tela de prévia do anexo.
LEGENDA_ANEXO = [
    '[data-testid="media-caption-input-container"] div[contenteditable="true"]',
    'div[contenteditable="true"][aria-label*="legenda" i]',
    'div[contenteditable="true"][aria-label*="caption" i]',
    'div[contenteditable="true"][aria-label*="Adicione" i]',
]

# Botão de enviar na tela de prévia do anexo.
BOTAO_ENVIAR_ANEXO = [
    '[data-testid="send"]',
    'div[role="button"][aria-label="Enviar"]',
    'div[role="button"][aria-label="Send"]',
    'button[aria-label="Enviar"]',
    'button[aria-label="Send"]',
    '[data-icon="send"]',
    '[data-icon="wds-ic-send-filled"]',
]

# --- Mensagens da conversa ------------------------------------------------
# JS: identifica a ÚLTIMA mensagem que saiu desta conta e se ela ainda está
# com o relógio de "enviando..." (msg-time). Serve para confirmar o envio:
# depois de clicar em Enviar, esperamos aparecer uma saída NOVA sem relógio.
#   saídas:  div.message-out  |  [data-id^="true_"] (id das mensagens próprias)
#   relógio: [data-icon="msg-time"] | [data-testid="msg-time"]
JS_ULTIMA_SAIDA = """
() => {
  const els = document.querySelectorAll('#main div.message-out, #main [data-id^="true_"]');
  if (!els.length) return {id: null, pendente: false, total: 0};
  const el = els[els.length - 1];
  const c = el.closest('[data-id]') || el.querySelector('[data-id]') || el;
  const pend = !!el.querySelector('[data-icon="msg-time"], [data-testid="msg-time"]');
  return {id: c.getAttribute('data-id') || ('n' + els.length), pendente: pend, total: els.length};
}
"""

# Prefixo "[10:32, 30/09/2026] Antônio: " que o WhatsApp guarda em cada
# mensagem de texto (atributo data-pre-plain-text).
REGEX_PRE_TEXTO = r"^\s*\[(?P<hora>[^\]]+)\]\s*(?P<autor>.*?):\s*$"

# JS: texto de um elemento trocando <img alt="🚀"> (emoji) pelo próprio
# emoji. Se o elemento tiver `title`, ele já traz o nome completo.
JS_TEXTO_COM_EMOJI = """
(el) => {
  const t = el.getAttribute && el.getAttribute('title');
  if (t) return t;
  let s = '';
  const andar = (n) => {
    if (n.nodeType === 3) { s += n.nodeValue; return; }
    if (n.nodeType !== 1) return;
    if (n.tagName === 'IMG') { s += (n.getAttribute('alt') || ''); return; }
    if (n.tagName === 'BR') { s += '\\n'; return; }
    n.childNodes.forEach(andar);
  };
  andar(el);
  return s;
}
"""

# JS: lê as últimas N mensagens de texto da conversa aberta.
# Devolve [{pre, texto, saida}] — `pre` é o data-pre-plain-text.
JS_LER_MENSAGENS = """
(limite) => {
  const txt = (el) => {
    let s = '';
    const andar = (n) => {
      if (n.nodeType === 3) { s += n.nodeValue; return; }
      if (n.nodeType !== 1) return;
      if (n.tagName === 'IMG') { s += (n.getAttribute('alt') || ''); return; }
      if (n.tagName === 'BR') { s += '\\n'; return; }
      n.childNodes.forEach(andar);
    };
    andar(el);
    return s;
  };
  const out = [];
  document.querySelectorAll('#main [data-pre-plain-text]').forEach((el) => {
    const corpo = el.querySelector(
      'span.selectable-text, [data-testid="selectable-text"], span[dir="ltr"], span[dir="auto"]');
    out.push({
      pre: el.getAttribute('data-pre-plain-text') || '',
      texto: corpo ? txt(corpo) : txt(el),
      saida: !!el.closest('.message-out, [data-id^="true_"]'),
    });
  });
  return out.slice(-limite);
}
"""
