import telebot
import mysql.connector
from mysql.connector import pooling
import concurrent.futures
from datetime import datetime

from pesquisas import *
from user import *
from bd import *
from loja import *
from gnome import *
from operacoes import *


def enviar_pergunta_cenoura(message, id_usuario, id_personagem, quantidade):
    try:
        texto_pergunta = f"Você deseja mesmo cenourar a carta {id_personagem}?"
        keyboard = telebot.types.InlineKeyboardMarkup()
        sim_button = telebot.types.InlineKeyboardButton(text="Sim", callback_data=f"cenourar_sim_{id_usuario}_{id_personagem}")
        nao_button = telebot.types.InlineKeyboardButton(text="Não", callback_data=f"cenourar_nao_{id_usuario}_{id_personagem}")
        keyboard.row(sim_button, nao_button)
        bot.send_message(message.chat.id, texto_pergunta, reply_markup=keyboard)
    except Exception as e:
        print(f"Erro ao enviar pergunta de cenourar: {e}")

def processar_verificar_e_cenourar(message):
    try:
        conn = conectar_banco_dados()
        cursor = conn.cursor()
        id_usuario = message.from_user.id
        id_personagem = message.text.replace('/cenourar', '').strip()

        cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (id_usuario, id_personagem))
        quantidade_atual = cursor.fetchone()

        if quantidade_atual and quantidade_atual[0] >= 1:
            enviar_pergunta_cenoura(message, id_usuario, id_personagem, quantidade_atual[0])
        else:
            bot.send_message(message.chat.id, "Você não possui essa carta no inventário ou não tem quantidade suficiente.")
    except Exception as e:
        print(f"Erro ao processar o comando de cenourar: {e}")
        bot.send_message(message.chat.id, "Erro ao processar o comando de cenourar.")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def cenourar_carta(call, id_usuario, id_personagem):
    try:
        conn, cursor = conectar_banco_dados()
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        
        id_personagens_list = id_personagem.split(",")
        id_personagens_list = [id.strip() for id in id_personagens_list]

        if len(id_personagens_list) > 10:
            mensagem_progresso = "Você pode cenourar no máximo 10 cartas por vez."
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=mensagem_progresso)
            return
        
        # Verificar se possui todas as cartas
        cartas_a_cenourar = []
        for id_personagem in id_personagens_list:
            cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (id_usuario, id_personagem))
            quantidade_atual = cursor.fetchone()
            if quantidade_atual and quantidade_atual[0] > 0:
                cartas_a_cenourar.append(id_personagem)
            else:
                bot.send_message(chat_id, f"A carta {id_personagem} não foi encontrada no inventário ou a quantidade é insuficiente e será ignorada.")
        
        if not cartas_a_cenourar:
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Nenhuma carta válida para cenourar foi encontrada.")
            return
        
        cartas_cenouradas = []
        for id_personagem in cartas_a_cenourar:
            cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (id_usuario, id_personagem))
            quantidade_atual = cursor.fetchone()[0]
            
            nova_quantidade = quantidade_atual - 1
            cursor.execute("UPDATE inventario SET quantidade = %s WHERE id_usuario = %s AND id_personagem = %s", (nova_quantidade, id_usuario, id_personagem))
            
            cursor.execute("SELECT cenouras FROM usuarios WHERE id_usuario = %s", (id_usuario,))
            cenouras = int(cursor.fetchone()[0])
            novas_cenouras = cenouras + 1
            cursor.execute("UPDATE usuarios SET cenouras = %s WHERE id_usuario = %s", (novas_cenouras, id_usuario))

            # Verificar se a carta já está na tabela banco_inventario
            cursor.execute("SELECT quantidade FROM banco_inventario WHERE id_personagem = %s", (id_personagem,))
            quantidade_banco = cursor.fetchone()
            if quantidade_banco:
                nova_quantidade_banco = quantidade_banco[0] + 1
                cursor.execute("UPDATE banco_inventario SET quantidade = %s WHERE id_personagem = %s", (nova_quantidade_banco, id_personagem))
            else:
                cursor.execute("INSERT INTO banco_inventario (id_personagem, quantidade) VALUES (%s, %s)", (id_personagem, 1))
            
            conn.commit()
            cartas_cenouradas.append(id_personagem)
            mensagem_progresso = f"🔄 Cenourando carta:\n{id_personagem}\n\n✅ Cartas cenouradas:\n" + "\n🥕".join(cartas_cenouradas)
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=mensagem_progresso)

        mensagem_final = "🥕 Cartas cenouradas com sucesso:\n\n" + "\n".join(cartas_cenouradas)
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=mensagem_final)
    
    except Exception as e:
        print(f"Erro ao processar cenoura: {e}")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Erro ao processar a cenoura.")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def verificar_id_na_tabelabeta(user_id):
    try:
        conn = conectar_banco_dados()
        cursor = conn.cursor()
        query = f"SELECT id FROM beta WHERE id = {user_id}"
        cursor.execute(query)
        resultado = cursor.fetchone()
        return resultado is not None
    except Exception as e:
        print(f"Erro ao verificar ID na tabela beta: {e}")
        raise ValueError("Erro ao verificar ID na tabela beta")
    finally:
        cursor.close()
        conn.close()


