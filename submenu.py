from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bd import *
from gif import *
import globals
from botoes import *
import random
def mostrar_primeira_pagina_submenus(message, subcategoria):
    try:
        conn, cursor = conectar_banco_dados()
        query_total = "SELECT COUNT(DISTINCT submenu) FROM personagens WHERE subcategoria = %s"
        cursor.execute(query_total, (subcategoria,))
        total_registros = cursor.fetchone()[0]
        total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)

        if total_registros == 0:
            bot.reply_to(message, f"Nenhum submenu encontrado para a subcategoria '{subcategoria}'.")
            return

        query = "SELECT DISTINCT submenu FROM personagens WHERE subcategoria = %s LIMIT 15"
        cursor.execute(query, (subcategoria,))
        resultados = cursor.fetchall()

        if resultados:
            resposta = f"🔖| Submenus na subcategoria {subcategoria}:\n\n"
            for resultado in resultados:
                submenu = resultado[0]
                resposta += f"• {submenu}\n"

            markup = None
            if total_paginas > 1:
                markup = criar_markup_submenus(1, total_paginas, subcategoria)
            bot.send_message(message.chat.id, resposta, reply_markup=markup, parse_mode="HTML")
        else:
            bot.reply_to(message, f"Nenhum submenu encontrado para a subcategoria '{subcategoria}'.")

    except Exception as e:
        print(f"Erro ao processar comando /submenus: {e}")
        bot.reply_to(message, "Ocorreu um erro ao processar sua solicitação.")

def editar_mensagem_submenus(call, subcategoria, pagina_atual, total_paginas):
    try:
        conn, cursor = conectar_banco_dados()

        offset = (pagina_atual - 1) * 15
        query = "SELECT DISTINCT submenu FROM personagens WHERE subcategoria = %s LIMIT 15 OFFSET %s"
        cursor.execute(query, (subcategoria, offset))
        resultados = cursor.fetchall()

        if resultados:
            resposta = f"🔖| Submenus na subcategoria {subcategoria}, página {pagina_atual}/{total_paginas}:\n\n"
            for resultado in resultados:
                submenu = resultado[0]
                resposta += f"• {submenu}\n"

            markup = criar_markup_submenus(pagina_atual, total_paginas, subcategoria)

            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=resposta, reply_markup=markup, parse_mode="HTML")
        else:
            bot.reply_to(call.message, f"Nenhum submenu encontrado para a subcategoria '{subcategoria}'.")

    except Exception as e:
        print(f"Erro ao editar mensagem de submenus: {e}")
        bot.reply_to(call.message, "Ocorreu um erro ao processar sua solicitação.")

def criar_markup_submenus(pagina_atual, total_paginas, subcategoria):
    markup = telebot.types.InlineKeyboardMarkup()

    if pagina_atual > 1:
        btn_anterior = telebot.types.InlineKeyboardButton("⬅️", callback_data=f"submenus_{pagina_atual-1}_{subcategoria}")
        markup.add(btn_anterior)
    
    if pagina_atual < total_paginas:
        btn_proxima = telebot.types.InlineKeyboardButton("➡️", callback_data=f"submenus_{pagina_atual+1}_{subcategoria}")
        markup.add(btn_proxima)

    return markup
