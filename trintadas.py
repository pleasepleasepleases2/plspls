from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bd import *
import globals
from botoes import *
import random
def buscar_cartas_trintadas(user_id, offset):
    conn, cursor = conectar_banco_dados()
    query = """
        SELECT p.emoji, p.nome, i.quantidade, p.subcategoria, p.id_personagem, p.categoria 
        FROM inventario i
        JOIN personagens p ON i.id_personagem = p.id_personagem
        WHERE i.id_usuario = %s AND i.quantidade >= 30
        ORDER BY p.categoria, i.quantidade DESC
        LIMIT 15 OFFSET %s
    """
    cursor.execute(query, (user_id, offset))
    cartas = cursor.fetchall()
    cursor.close()
    conn.close()
    return cartas

def buscar_todas_cartas_trintadas(user_id):
    conn, cursor = conectar_banco_dados()
    query = """
        SELECT p.imagem 
        FROM inventario i
        JOIN personagens p ON i.id_personagem = p.id_personagem
        WHERE i.id_usuario = %s AND i.quantidade >= 30
    """
    cursor.execute(query, (user_id,))
    imagens = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return imagens

def contar_cartas_trintadas(user_id):
    conn, cursor = conectar_banco_dados()
    query = """
        SELECT COUNT(*)
        FROM inventario
        WHERE id_usuario = %s AND quantidade >= 30
    """
    cursor.execute(query, (user_id,))
    total_cartas = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return total_cartas


def criar_mensagem_trintadas(cartas, pagina_atual, total_paginas, total_cartas, nome_usuario):
    resposta = f"🐝 Cartas trintadas pelo camponês {nome_usuario}:\n\n"
    for carta in cartas:
        emoji, nome, quantidade, subcategoria, id_personagem, categoria = carta
        resposta += f"{emoji} {id_personagem} • {nome}\nde {subcategoria} - {quantidade}⤫\n"
    resposta += f"\n📄 {pagina_atual}/{total_paginas}"
    return resposta

# Função para enviar a mensagem inicial de trintadas
def enviar_mensagem_trintadas(message, pagina_atual):
    user_id = message.from_user.id
    nome_usuario = message.from_user.first_name
    imagens = buscar_todas_cartas_trintadas(user_id)
    if not imagens:
        bot.send_message(message.chat.id, "Você não possui cartas com 30 ou mais unidades.")
        return

    imagem_aleatoria = random.choice(imagens)
    offset = (pagina_atual - 1) * 15
    cartas = buscar_cartas_trintadas(user_id, offset)
    total_cartas = contar_cartas_trintadas(user_id)
    total_paginas = (total_cartas + 14) // 15

    resposta = criar_mensagem_trintadas(cartas, pagina_atual, total_paginas, total_cartas, nome_usuario)
    markup = criar_markup_trintadas(pagina_atual, total_paginas, user_id, nome_usuario)

    bot.send_photo(message.chat.id, photo=imagem_aleatoria, caption=resposta, reply_markup=markup, parse_mode="HTML")

# Função para editar a mensagem de trintadas ao navegar pelas páginas
def editar_mensagem_trintadas(call, user_id_inicial, pagina_atual, nome_usuario_inicial):
    imagens = buscar_todas_cartas_trintadas(user_id_inicial)
    if not imagens:
        bot.send_message(call.message.chat.id, "Você não possui cartas com 30 ou mais unidades.")
        return

    imagem_aleatoria = random.choice(imagens)
    offset = (pagina_atual - 1) * 15
    cartas = buscar_cartas_trintadas(user_id_inicial, offset)
    total_cartas = contar_cartas_trintadas(user_id_inicial)
    total_paginas = (total_cartas + 14) // 15

    resposta = criar_mensagem_trintadas(cartas, pagina_atual, total_paginas, total_cartas, nome_usuario_inicial)
    markup = criar_markup_trintadas(pagina_atual, total_paginas, user_id_inicial, nome_usuario_inicial)

    media = InputMediaPhoto(media=imagem_aleatoria, caption=resposta, parse_mode="HTML")
    bot.edit_message_media(media=media, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
