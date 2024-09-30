import random
from pesquisas import *
from user import *
from bd import *
from loja import *
from gnome import *
from operacoes import *
from inventario import *
from gif import *
from cachetools import cached, TTLCache
from evento import *
from sub import *
from datetime import date

def obter_total_imagens(subcategoria):
    conn, cursor = conectar_banco_dados()
    try:
        query_total = "SELECT COUNT(id_personagem) FROM personagens WHERE subcategoria = %s"
        cursor.execute(query_total, (subcategoria,))
        total_imagens = cursor.fetchone()[0]
        return total_imagens
    finally:
        fechar_conexao(cursor, conn)


def obter_imagem_info(subcategoria, offset):
    conn, cursor = conectar_banco_dados()
    try:
        query = "SELECT imagem, emoji, nome, id_personagem FROM personagens WHERE subcategoria = %s LIMIT 1 OFFSET %s"
        cursor.execute(query, (subcategoria, offset))
        return cursor.fetchone()
    finally:
        fechar_conexao(cursor, conn)


def obter_ids_personagens(subcategoria):
    conn, cursor = conectar_banco_dados()
    try:
        query_ids = "SELECT id_personagem FROM personagens WHERE subcategoria = %s"
        cursor.execute(query_ids, (subcategoria,))
        return [id[0] for id in cursor.fetchall()]
    finally:
        fechar_conexao(cursor, conn)

def criar_botao_pagina_peixes(message, subcategoria, pagina_atual):
    try:
        total_imagens = obter_total_imagens(subcategoria)
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row(
            telebot.types.InlineKeyboardButton(text="⏪️", callback_data=f"img_1_{subcategoria}"),
            telebot.types.InlineKeyboardButton(text="⬅️", callback_data=f"img_{pagina_atual-1}_{subcategoria}"),
            telebot.types.InlineKeyboardButton(text="➡️", callback_data=f"img_{pagina_atual+1}_{subcategoria}"),
            telebot.types.InlineKeyboardButton(text="⏩️", callback_data=f"img_{total_imagens}_{subcategoria}")
        )
        return markup
    except Exception as e:
        print(f"Erro ao criar botões de página: {e}")

def enviar_imagem_peixe(message, subcategoria, pagina_atual=1):
    try:
        subcategoria_encontrada = verificar_apelido(subcategoria)
        offset = pagina_atual - 1
        imagem_info = obter_imagem_info(subcategoria_encontrada, offset)
        
        ids = obter_ids_personagens(subcategoria_encontrada)
        total_ids = len(ids)
        
        if imagem_info:
            imagem, emoji, nome, id_personagem = imagem_info
            caption = f"Peixes da espécie: <b>{subcategoria_encontrada}</b>\n\n{emoji} {id_personagem} - {nome}\n\nPersonagem {pagina_atual} de {total_ids}"
            markup = criar_botao_pagina_peixes(message, subcategoria_encontrada, pagina_atual)
            bot.send_photo(message.chat.id, photo=imagem, caption=caption, reply_markup=markup, parse_mode="HTML")
        else:
            bot.reply_to(message, f"Nenhuma imagem encontrada na subcategoria '{subcategoria_encontrada}'.")

    except Exception as e:
        print(f"Erro ao processar comando /peixes img: {e}")
        bot.reply_to(message, "Ocorreu um erro ao processar sua solicitação.")

def callback_img_peixes(call, pagina_atual, subcategoria):
    try:
        subcategoria_encontrada = verificar_apelido(subcategoria)
        ids = obter_ids_personagens(subcategoria_encontrada)
        total_ids = len(ids)

        if 1 <= pagina_atual <= total_ids:
            id_atual = ids[pagina_atual - 1]
            conn, cursor = conectar_banco_dados()
            query_info = "SELECT imagem, emoji, nome FROM personagens WHERE id_personagem = %s"
            cursor.execute(query_info, (id_atual,))
            info = cursor.fetchone()
            fechar_conexao(cursor, conn)

            if info:
                imagem, emoji, nome = info
                legenda = f"Peixes da espécie: <b>{subcategoria}</b>\n\n{emoji} {id_atual} - {nome}\n\nPersonagem {pagina_atual} de {total_ids}"
                markup = criar_botao_pagina_peixes(call.message, subcategoria, pagina_atual)
                bot.edit_message_media(chat_id=call.message.chat.id, message_id=call.message.message_id, media=telebot.types.InputMediaPhoto(imagem, caption=legenda, parse_mode="HTML"), reply_markup=markup)
            else:
                bot.answer_callback_query(call.id, text="Imagem não encontrada.")
        else:
            bot.answer_callback_query(call.id, text="ID não encontrado.")
    except Exception as e:
        print(f"Erro ao processar callback 'img' de peixes: {e}")

def mostrar_lista_peixes(message, subcategoria):
    try:
        conn, cursor = conectar_banco_dados()
        subcategoria_like = f"%{subcategoria}%"
        query_subcategoria = "SELECT subcategoria FROM personagens WHERE subcategoria LIKE %s LIMIT 1"
        cursor.execute(query_subcategoria, (subcategoria_like,))
        subcategoria_encontrada = cursor.fetchone()

        if subcategoria_encontrada:
            subcategoria = subcategoria_encontrada[0]
            query_personagens = "SELECT id_personagem, nome, emoji FROM personagens WHERE subcategoria = %s"
            cursor.execute(query_personagens, (subcategoria,))
            peixes_personagens = cursor.fetchall()
            fechar_conexao(cursor, conn)

            conn, cursor = conectar_banco_dados()
            query_evento = "SELECT id_personagem, nome, emoji FROM evento WHERE subcategoria = %s"
            cursor.execute(query_evento, (subcategoria,))
            peixes_evento = cursor.fetchall()
            fechar_conexao(cursor, conn)

            peixes = peixes_personagens + peixes_evento

            if peixes:
                resposta = f"<i>Peixes da espécie</i> <b>{subcategoria}</b>:\n\n"
                paginas = dividir_em_paginas(peixes, 15)
                pagina_atual = 1

                if pagina_atual in paginas:
                    resposta_pagina = ""
                    for index, peixe in enumerate(paginas[pagina_atual], start=1):
                        id_personagem, nome, emoji = peixe
                        resposta_pagina += f"{emoji} <code>{id_personagem}</code> - {nome}\n"

                    resposta += resposta_pagina

                    if len(paginas) > 1:
                        resposta += f"\nPágina <b>{pagina_atual}</b>/{len(paginas)}"
                        markup = criar_markup_peixes(pagina_atual, len(paginas), subcategoria)
                        bot.send_message(message.chat.id, resposta, reply_markup=markup, parse_mode="HTML")
                    else:
                        bot.send_message(message.chat.id, resposta, parse_mode="HTML")
                else:
                    bot.reply_to(message, "Página não encontrada.")
            else:
                bot.reply_to(message, f"Nenhum peixe encontrado na subcategoria '{subcategoria}'.")
        else:
            bot.reply_to(message, f"Nenhuma subcategoria correspondente encontrada para '{subcategoria}'.")

    except Exception as e:
        print(f"Erro ao processar comando /peixes: {e}")
        bot.reply_to(message, "Ocorreu um erro ao processar sua solicitação.")

def criar_markup_peixes(pagina_atual, total_paginas, subcategoria):
    markup = telebot.types.InlineKeyboardMarkup()

    markup.row(
        telebot.types.InlineKeyboardButton(text="⏪️", callback_data=f"peixes_1_{subcategoria}"),
        telebot.types.InlineKeyboardButton(text="⬅️", callback_data=f"peixes_{pagina_atual-1}_{subcategoria}"),
        telebot.types.InlineKeyboardButton(text="➡️", callback_data=f"peixes_{pagina_atual+1}_{subcategoria}"),
        telebot.types.InlineKeyboardButton(text="⏪️", callback_data=f"peixes_{total_paginas}_{subcategoria}")
    )

    return markup

def pagina_peixes_callback(call, pagina, subcategoria):
    try:
        conn, cursor = conectar_banco_dados()
        query_personagens = "SELECT id_personagem, nome, emoji FROM personagens WHERE subcategoria = %s"
        cursor.execute(query_personagens, (subcategoria,))
        peixes_personagens = cursor.fetchall()
        fechar_conexao(cursor, conn)

        conn, cursor = conectar_banco_dados()
        query_evento = "SELECT id_personagem, nome, emoji FROM evento WHERE subcategoria = %s"
        cursor.execute(query_evento, (subcategoria,))
        peixes_evento = cursor.fetchall()
        fechar_conexao(cursor, conn)

        peixes = peixes_personagens + peixes_evento
        paginas = dividir_em_paginas(peixes, 15)

        if pagina in paginas:
            resposta = f"<i>Peixes da espécie</i> <b>{subcategoria}</b>:\n\n"
            for peixe in paginas[pagina]:
                id_personagem, nome, emoji = peixe
                resposta += f"{emoji} <code>{id_personagem}</code> - {nome}\n"

            resposta += f"\nPágina <b>{pagina}</b>/{len(paginas)}"
            markup = criar_markup_peixes(pagina, len(paginas), subcategoria)

            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=resposta, reply_markup=markup, parse_mode="HTML")
        else:
            bot.answer_callback_query(call.id, text="Página não encontrada.")
    except Exception as e:
        print(f"Erro ao processar callback de página de peixes: {e}")

def dividir_em_paginas(lista, tamanho_pagina):
    paginas = {}
    for i in range(0, len(lista), tamanho_pagina):
        paginas[(i // tamanho_pagina) + 1] = lista[i:i + tamanho_pagina]
    return paginas
