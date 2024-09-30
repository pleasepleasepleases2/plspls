import json
from bd import *
from pesquisas import *

def create_next_button_markup(current_index, total_count):
    markup = types.InlineKeyboardMarkup()
    button_text = f"Próximo ({current_index}/{total_count})"
    button_callback = f"next_button_{current_index}_{total_count}"
    markup.add(types.InlineKeyboardButton(text=button_text, callback_data=button_callback))
    return markup

def create_next_button_markup(current_index, total_count):
    markup = types.InlineKeyboardMarkup()

    if current_index > 0:
        prev_button_text = f"Anterior ({current_index}/{total_count})"
        prev_button_callback = f"prev_button_{current_index}_{total_count}"
        markup.add(types.InlineKeyboardButton(text=prev_button_text, callback_data=prev_button_callback))
        markup.add(types.InlineKeyboardButton(text=next_button_text, callback_data=next_button_callback))

    if current_index < total_count - 1:
        next_button_text = f"Próximo ({current_index + 2}/{total_count})"
        next_button_callback = f"next_button_{current_index + 2}_{total_count}"
        markup.add(types.InlineKeyboardButton(text=prev_button_text, callback_data=prev_button_callback))
        markup.add(types.InlineKeyboardButton(text=next_button_text, callback_data=next_button_callback))
    return markup

        
def load_user_state(chat_id, command):
    conn, cursor = conectar_banco_dados()
    try:
        cursor.execute("SELECT data FROM user_state WHERE chat_id = %s AND command = %s", (chat_id, command))
        result = cursor.fetchone()
        if result:
            return json.loads(result[0]), chat_id
        return None, None
    finally:
        fechar_conexao(cursor, conn)

def clear_user_state(user_id, command):
    conn, cursor = conectar_banco_dados()
    try:
        cursor.execute("DELETE FROM user_state WHERE user_id = %s AND command = %s", (user_id, command))
        conn.commit()
    finally:
        fechar_conexao(cursor, conn)

def create_navigation_markup(current_index, total_count):
    markup = types.InlineKeyboardMarkup()
    buttons = []

    if current_index > 0:
        prev_button = types.InlineKeyboardButton(text="⬅", callback_data=f"change_page_{current_index-1}")
        buttons.append(prev_button)
    
    if current_index < total_count - 1:
        next_button = types.InlineKeyboardButton(text="➡", callback_data=f"change_page_{current_index+1}")
        buttons.append(next_button)
    
    markup.add(*buttons)
    return markup

def send_message_with_buttons(chat_id, idmens, mensagens, current_index=0, reply_to_message_id=None):
    total_count = len(mensagens)

    if current_index < total_count:
        media_url, mensagem = mensagens[current_index]
        markup = create_navigation_markup(current_index, total_count)

        if media_url.lower().endswith(".gif"):
            bot.send_animation(chat_id, media_url, caption=mensagem, reply_markup=markup, parse_mode="HTML", reply_to_message_id=reply_to_message_id)
        elif media_url.lower().endswith(".mp4"):
            bot.send_video(chat_id, media_url, caption=mensagem, reply_markup=markup, parse_mode="HTML", reply_to_message_id=reply_to_message_id)
        elif media_url.lower().endswith((".jpeg", ".jpg", ".png")):
            bot.send_photo(chat_id, media_url, caption=mensagem, reply_markup=markup, parse_mode="HTML", reply_to_message_id=reply_to_message_id)
        else:
            bot.send_message(chat_id, mensagem, reply_markup=markup, reply_to_message_id=reply_to_message_id)
    else:
        bot.send_message(chat_id, "Não há mais personagens disponíveis.")
        clear_user_state(chat_id, 'gnomes')
        

def save_state(user_id, command, data, chat_id, message_id):
    conn, cursor = conectar_banco_dados()

    try:
        cursor.execute("REPLACE INTO user_state (user_id, command, data, chat_id, message_id) VALUES (%s, %s, %s, %s, %s)",
                       (user_id, command, json.dumps(data), chat_id, message_id))
        conn.commit()
    finally:
        fechar_conexao(cursor, conn)

def create_navegacao_markup(pagina_atual, total_paginas):
    markup = types.InlineKeyboardMarkup()
    if pagina_atual > 1:
        prev_button_text = f"< Anterior"
        prev_button_callback = f"prev_button_{pagina_atual - 1}_{total_paginas}"
        markup.add(types.InlineKeyboardButton(text=prev_button_text, callback_data=prev_button_callback))

    if pagina_atual < total_paginas:
        next_button_text = f"Próximo >"
        next_button_callback = f"next_button_{pagina_atual + 1}_{total_paginas}"
        markup.add(types.InlineKeyboardButton(text=next_button_text, callback_data=next_button_callback))
    return markup
        