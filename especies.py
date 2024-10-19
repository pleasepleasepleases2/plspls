from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bd import *
from gif import *
import globals
from botoes import *
import random      
def mostrar_primeira_pagina_especies(message, categoria):
    try:
        conn, cursor = conectar_banco_dados()

        query_total = "SELECT COUNT(DISTINCT subcategoria) FROM personagens WHERE categoria = %s"
        cursor.execute(query_total, (categoria,))
        total_registros = cursor.fetchone()[0]

        total_paginas = (total_registros // 20) + (1 if total_registros % 20 > 0 else 0)

        if total_registros == 0:
            bot.reply_to(message, f"Nenhuma subcategoria encontrada para a categoria '{categoria}'.")
            return

        query = "SELECT DISTINCT subcategoria FROM personagens WHERE categoria = %s LIMIT 20"
        cursor.execute(query, (categoria,))
        resultados = cursor.fetchall()

        if resultados:
            resposta = f"🔖| Subcategorias na categoria {categoria}:\n\n"
            for resultado in resultados:
                subcategoria = resultado[0]
                resposta += f"• {subcategoria}\n"

            markup = None
            if total_paginas > 1:
                markup = criar_markup_especies(1, total_paginas, categoria)
            bot.send_message(message.chat.id, resposta, reply_markup=markup, parse_mode="HTML")
        else:
            bot.reply_to(message, f"Nenhuma subcategoria encontrada para a categoria '{categoria}'.")

    except Exception as e:
        print(f"Erro ao processar comando /especies: {e}")
        bot.reply_to(message, "Ocorreu um erro ao processar sua solicitação.")

def editar_mensagem_especies(call, categoria, pagina_atual, total_paginas):
    try:
        conn, cursor = conectar_banco_dados()

        offset = (pagina_atual - 1) * 20
        query = "SELECT DISTINCT subcategoria FROM personagens WHERE categoria = %s LIMIT 20 OFFSET %s"
        cursor.execute(query, (categoria, offset))
        resultados = cursor.fetchall()

        if resultados:
            resposta = f"🔖| Subcategorias na categoria {categoria}, página {pagina_atual}/{total_paginas}:\n\n"
            for resultado in resultados:
                subcategoria = resultado[0]
                resposta += f"• {subcategoria}\n"

            markup = criar_markup_especies(pagina_atual, total_paginas, categoria)

            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=resposta, reply_markup=markup, parse_mode="HTML")
        else:
            bot.reply_to(call.message, f"Nenhuma subcategoria encontrada para a categoria '{categoria}'.")

    except Exception as e:
        print(f"Erro ao editar mensagem de espécies: {e}")
        bot.reply_to(call.message, "Ocorreu um erro ao processar sua solicitação.")

def criar_markup_especies(pagina_atual, total_paginas, categoria):
    markup = telebot.types.InlineKeyboardMarkup()

    if pagina_atual > 1:
        btn_anterior = telebot.types.InlineKeyboardButton("⬅️", callback_data=f"especies_{pagina_atual-1}_{categoria}")
        markup.add(btn_anterior)
    
    if pagina_atual < total_paginas:
        btn_proxima = telebot.types.InlineKeyboardButton("➡️", callback_data=f"especies_{pagina_atual+1}_{categoria}")
        markup.add(btn_proxima)

    return markup
