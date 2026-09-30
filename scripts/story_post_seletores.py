# -*- coding: utf-8 -*-
"""story_post_seletores.py — onde o story_post.py procura cada botão do Instagram.

Se o Instagram mudar um botão de lugar ou de nome, é AQUI que se ajusta (ou,
sem mexer em código, no H:\\HypadoLocal\\emulador\\story_post_config.json, chave
"seletores": {"ids": {...}, "textos": {...}}). O resto do código não muda.

Como descobrir o nome certo de um botão: com o emulador ligado e o Instagram
na tela que interessa, rode
    python H:\\HypadoLocal\\android\\ui.py
e procure na lista o resource-id (a parte depois de ":id/") ou o texto.

Cada entrada é uma LISTA de alternativas: vale a primeira que aparecer na tela.
As chaves em A_CONFIRMAR são palpites (versões conhecidas do app) e precisam
ser conferidas com o ui.py no emulador antes de ligar o modo real; as demais
vieram do ticket (já vistas no emulador).
"""

PACOTE = "com.instagram.android"

# ---------------------------------------------------------------------------
# resource-ids (só a parte depois de "com.instagram.android:id/")
# ---------------------------------------------------------------------------
IDS = {
    # abas de baixo do app
    "aba_perfil": ["profile_tab"],
    # perfil: o nome da conta lá em cima (tocar abre a lista de contas)
    "conta_container": ["action_bar_username_container"],
    "conta_titulo": ["action_bar_large_title_auto_size", "action_bar_title",
                     "action_bar_textview_title", "action_bar_large_title"],
    # post aberto
    "compartilhar": ["row_feed_button_share"],
    "autor_post": ["row_feed_photo_profile_name"],
    # editor de story: botão "Seu story" (publica)
    "publicar_seu_story": ["your_story_share_shortcut_button"],
    # perfil: foto (abre o próprio story) e grade de posts (plano B)
    "avatar_perfil": ["row_profile_header_imageview"],
    "grade_item": ["image_button", "grid_card_layout_container"],
    # visualizador de story
    "story_timestamp": ["reel_viewer_timestamp"],
    "story_destaque": ["toolbar_highlights_button"],
    # criar story a partir do perfil ("+") e galeria
    "criar": ["creation_tab", "action_bar_new_post_button",
              "action_bar_create_button"],
    "galeria": ["gallery_preview_button", "camera_gallery_button",
                "gallery_button"],
    "galeria_item": ["gallery_grid_item_thumbnail", "media_picker_grid_item",
                     "gallery_grid_item"],
    # editor: figurinhas
    "figurinhas": ["asset_button"],
    "busca_figurinha": ["row_search_edit_text", "search_edit_text",
                        "asset_search_edit_text"],
    # figurinha de enquete
    "enquete_pergunta": ["poll_sticker_v2_question"],
    "enquete_opcao": ["poll_sticker_v2_option_text", "poll_sticker_v2_option"],
    # botão "Concluir" das figurinhas
    "concluir": ["done_button"],
    # figurinha de contagem regressiva
    "contagem_titulo": ["countdown_sticker_title", "countdown_sticker_title_text"],
    "contagem_data": ["countdown_sticker_end_date", "countdown_sticker_date_text"],
    "contagem_dia_inteiro": ["countdown_sticker_all_day_switch"],
    # calendário padrão do Android (DatePicker)
    "data_proximo_mes": ["android:id/next"],
    "data_ok": ["android:id/button1"],
}

# Chaves que ainda são palpite (conferir com ui.py no emulador).
A_CONFIRMAR = {
    "aba_perfil", "conta_titulo", "autor_post", "avatar_perfil", "grade_item",
    "criar", "galeria", "galeria_item", "busca_figurinha", "enquete_opcao",
    "contagem_titulo", "contagem_data", "contagem_dia_inteiro",
    "data_proximo_mes", "data_ok",
}

# ---------------------------------------------------------------------------
# Textos (português e inglês; a comparação ignora maiúsculas e acentos)
# ---------------------------------------------------------------------------
TEXTOS = {
    # folha do "Enviar": botão de adicionar ao story
    "add_story": ["Adicionar ao story", "Adicionar ao seu story",
                  "Adicionar publicação ao seu story", "Add to story",
                  "Add post to your story", "Add to your story"],
    # menu do "+" do perfil
    "menu_story": ["Story", "Adicionar ao story", "Add to story"],
    "criar_desc": ["Criar", "Create", "Nova publicação", "New post"],
    "galeria_desc": ["Galeria", "Gallery", "Abrir galeria", "Open gallery"],
    # figurinhas (procura por "contém", no texto ou na descrição)
    "figurinha_enquete": ["enquete", "poll"],
    "figurinha_contagem": ["contagem regressiva", "countdown"],
    # o que digitar na busca de figurinhas (tenta na ordem)
    "busca_enquete": ["enquete", "poll"],
    "busca_contagem": ["contagem", "countdown"],
    "busca_rotulo": ["Pesquisar", "Search", "Buscar"],
    "enquete_add_opcao": ["Adicionar opção", "Add option", "Adicionar outra opção"],
    # indicador de envio em andamento (espera sumir antes de seguir)
    "enviando": ["Publicando", "Posting", "Enviando", "Uploading",
                 "Compartilhando", "Sharing"],
    # confirmação de destaque
    "destaque_ok": ["Adicionado", "Adicionada", "Added to"],
    # contagem regressiva
    "dia_inteiro": ["Dia inteiro", "All day"],
    "definir_data": ["Definir data", "Set end date", "Data de término",
                     "End date", "Definir data e hora"],
}

# Timestamps que contam como "agora" no visualizador de story.
TIMESTAMP_AGORA = ["agora", "agora mesmo", "now", "just now"]

# ---------------------------------------------------------------------------
# Avisos da Meta: se QUALQUER um aparecer na tela, o story_post para tudo,
# grava H:\HypadoLocal\emulador\PARADO_AVISO_META.json e nenhum story sai
# enquanto esse arquivo existir (só o Antônio apaga). Comparação por "contém",
# sem acento e sem maiúscula.
# ---------------------------------------------------------------------------
AVISOS_META = [
    "tente novamente mais tarde", "try again later",
    "ação bloqueada", "action blocked",
    "we restrict certain activity", "restringimos",
    "suspeita", "suspicious",
    "captcha",
    "confirme que é você", "confirme que você", "confirm it's you",
    "confirm it is you", "confirm that it's you", "confirm you're human",
    "help us confirm", "ajude-nos a confirmar", "nos ajude a confirmar",
    "sua conta foi suspensa", "suspendemos sua conta",
    "we suspended your account", "your account has been suspended",
    "conta desativada", "desativamos sua conta",
    "your account has been disabled", "we disabled your account",
    "limitamos a frequência", "we limit how often",
    "digite o código", "insira o código", "enter the code",
    "enter confirmation code", "código de segurança", "security code",
    "atualizamos nossos termos", "we've updated our terms",
    "we have updated our terms", "revise e concorde", "review and agree",
    "esqueceu a senha", "forgot password",
    "sessão expirou", "session expired", "faça login novamente",
    "please log in again",
]

# Nós cujo texto é conteúdo nosso (legenda/comentários) não contam como aviso
# (evita parar por causa de uma legenda com a palavra "suspeita").
# Campos de digitação (EditText) também são ignorados.
IDS_CONTEUDO_IGNORAR_AVISO = [
    "row_feed_comment_textview_layout", "row_feed_textview_comments",
    "row_feed_headline_text",
]

# ---------------------------------------------------------------------------
# Nunca tocar (login, senha, código, termos, permissões). Se o story_post for
# tocar num botão assim, ele para e grava o arquivo de parada.
# ---------------------------------------------------------------------------
PROIBIDO_TOCAR_EXATO = [
    "entrar", "log in", "login", "fazer login", "concordo", "i agree", "agree",
    "aceitar", "accept", "aceito", "aceitar tudo", "accept all", "permitir",
    "allow", "cadastre-se", "sign up", "criar nova conta", "create new account",
    "enviar código", "send code",
]
PROIBIDO_TOCAR_CONTEM = [
    "senha", "password", "termos", "terms of", "código de segurança",
    "security code", "captcha", "continuar como", "continue as",
]

# Pop-ups inofensivos que podem ser fechados ("Agora não" etc.). Só texto exato.
POPUPS_DISPENSAVEIS = [
    "agora não", "not now", "entendi", "got it", "dispensar", "dismiss",
]
