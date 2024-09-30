from pesquisas import *
from user import *
from bd import *
from loja import *
from gnome import *
from operacoes import *
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

#botoes wish
def create_wish_buttons():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="Fazer pedido", callback_data="fazer_pedido"))
    markup.add(InlineKeyboardButton(text="Cancelar", callback_data="pedido_cancelar"))
    return markup

#botoes trintadas
def criar_markup_trintadas(pagina_atual, total_paginas, user_id_inicial, nome_usuario_inicial):
    markup = InlineKeyboardMarkup()
    if pagina_atual > 1:
        markup.add(InlineKeyboardButton("⬅️", callback_data=f"trintadas_{user_id_inicial}_{pagina_atual - 1}_{nome_usuario_inicial}"))
    if pagina_atual < total_paginas:
        markup.add(InlineKeyboardButton("➡️", callback_data=f"trintadas_{user_id_inicial}_{pagina_atual + 1}_{nome_usuario_inicial}"))
    return markup
