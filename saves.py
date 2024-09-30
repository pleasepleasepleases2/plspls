from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bd import *
import time
import globals
def save_user_state(chat_id, data):
    globals.state_data[chat_id] = data
    
def update_message_media(media_url, mensagem, chat_id, message_id, markup):
    if media_url.lower().endswith(".gif"):
        bot.edit_message_media(media=types.InputMediaAnimation(media_url, caption=mensagem,parse_mode="HTML"), chat_id=chat_id, message_id=message_id, reply_markup=markup)
    elif media_url.lower().endswith(".mp4"):
        bot.edit_message_media(media=types.InputMediaVideo(media_url, caption=mensagem,parse_mode="HTML"), chat_id=chat_id, message_id=message_id, reply_markup=markup)
    elif media_url.lower().endswith((".jpeg", ".jpg", ".png")):
        bot.edit_message_media(media=types.InputMediaPhoto(media_url, caption=mensagem,parse_mode="HTML"), chat_id=chat_id, message_id=message_id, reply_markup=markup)
    else:
        bot.edit_message_text(text=mensagem, chat_id=chat_id, message_id=message_id, reply_markup=markup,parse_mode="HTML")
    
def mostrar_repetidas_evento(chat_id, nome_usuario, evento, cartas_repetidas, pagina_atual, total_paginas, message_id, original_message_id):
    offset = (pagina_atual - 1) * 20
    cartas_pagina = cartas_repetidas[offset:offset + 20]

    resposta = f"Cartas repetidas do evento {evento.capitalize()} no inventário de {nome_usuario}:\n\n"
    for carta in cartas_pagina:
        id_personagem, nome, subcategoria, quantidade = carta
        resposta += f"• {id_personagem} — {nome} de {subcategoria} — {quantidade}x\n"

    resposta += f"\nPágina {pagina_atual} de {total_paginas}"

    markup = InlineKeyboardMarkup()
    if pagina_atual > 1:
        markup.add(InlineKeyboardButton("⬅️", callback_data=f"rep_prev_{original_message_id}_{pagina_atual}"))
    if pagina_atual < total_paginas:
        markup.add(InlineKeyboardButton("➡️", callback_data=f"rep_next_{original_message_id}_{pagina_atual}"))

    bot.edit_message_text(resposta, chat_id=chat_id, message_id=message_id, reply_markup=markup)    