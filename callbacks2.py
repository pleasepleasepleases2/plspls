import time
import globals
from bd import *
from tag import *
from pescar import send_card_message,subcategoria_handler,verificar_subcategoria_evento
#subcategoria
def choose_subcategoria_callback(call, subcategoria, cursor, conn,chat_id,message_id):
    try:
        categoria_info = globals.ultimo_clique.get(call.message.chat.id, {})
        categoria = categoria_info.get('categoria', '')
        if categoria.lower() == 'geral':
            evento_aleatorio = verificar_subcategoria_evento(subcategoria, cursor)
            if evento_aleatorio:
                send_card_message(call.message, evento_aleatorio)
            else:
                subcategoria_handler(call.message, subcategoria, cursor, conn, None,chat_id,message_id)
        else:
            subcategoria_handler(call.message, subcategoria, cursor, conn, None,chat_id,message_id)
    except Exception as e:
        print(f"Erro durante o processamento choose_subcategoria_callback: {e}")
#tag       
def callback_pagina_tag(call):
    try:
        parts = call.data.split('_')
        pagina_atual = int(parts[1])
        nometag = parts[2]
        total_paginas = parts[3]
        id_usuario = call.from_user.id 
        if pagina_atual < 1:
            bot.answer_callback_query(call.id, text="Página inválida.")
            return

        editar_mensagem_tag(call.message, nometag, pagina_atual,id_usuario,total_paginas)

    except Exception as e:
        print(f"Erro ao processar callback de tag: {e}")
        bot.answer_callback_query(call.id, text="Ocorreu um erro ao processar a consulta.")
        
#categoria        
def categoria_callback(call):
    try:
        categoria = call.data.replace('pescar_', '')
        
        if call.message and call.message.chat and call.message.chat.id:
            chat_id = call.message.chat.id
            message_id = call.message.message_id
            globals.ultimo_clique[chat_id] = {'categoria': categoria}
            categoria_handler(call.message, categoria)
        else:
            print("Invalid message or chat data in the callback query.")
    except Exception as e:
        print(f"Erro ao processar categoria_callback: {e}")                
