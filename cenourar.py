import telebot
import traceback
from bd import conectar_banco_dados, fechar_conexao

def enviar_pergunta_cenoura(message, id_usuario, id_personagem):
    try:
        texto_pergunta = f"Você deseja mesmo cenourar a carta {id_personagem}?"
        keyboard = telebot.types.InlineKeyboardMarkup()
        sim_button = telebot.types.InlineKeyboardButton(text="Sim", callback_data=f"cenourar_sim_{id_usuario}_{id_personagem}")
        nao_button = telebot.types.InlineKeyboardButton(text="Não", callback_data=f"cenourar_nao_{id_usuario}_{id_personagem}")
        keyboard.row(sim_button, nao_button)
        bot.send_message(message.chat.id, texto_pergunta, reply_markup=keyboard)
    except Exception as e:
        print(f"Erro ao enviar pergunta de cenourar: {e}")

def processar_verificar_e_cenourar(message, bot):
    try:
        conn, cursor = conectar_banco_dados()
        id_usuario = message.from_user.id
        id_personagem = message.text.replace('/cenourar', '').strip()

        # Verifica se a carta está no inventário
        cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (id_usuario, id_personagem))
        quantidade_atual = cursor.fetchone()

        if quantidade_atual and quantidade_atual[0] >= 1:
            enviar_pergunta_cenoura(message, id_usuario, id_personagem)
        else:
            bot.send_message(message.chat.id, "Você não possui essa carta no inventário ou não tem quantidade suficiente.")
    except Exception as e:
        print(f"Erro ao processar o comando de cenourar: {e}")
        bot.send_message(message.chat.id, "Erro ao processar o comando de cenourar.")
    finally:
        fechar_conexao(cursor, conn)

def cenourar_carta(call, id_usuario, id_personagem, bot):
    try:
        conn, cursor = conectar_banco_dados()
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        
        cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (id_usuario, id_personagem))
        quantidade_atual = cursor.fetchone()[0]
        
        if quantidade_atual > 0:
            # Atualiza o inventário
            nova_quantidade = quantidade_atual - 1
            cursor.execute("UPDATE inventario SET quantidade = %s WHERE id_usuario = %s AND id_personagem = %s", 
                           (nova_quantidade, id_usuario, id_personagem))
            
            # Adiciona cenouras ao usuário
            cursor.execute("SELECT cenouras FROM usuarios WHERE id_usuario = %s", (id_usuario,))
            cenouras = cursor.fetchone()[0] + 1
            cursor.execute("UPDATE usuarios SET cenouras = %s WHERE id_usuario = %s", (cenouras, id_usuario))
            
            # Adiciona a carta ao banco de inventário
            cursor.execute("SELECT quantidade FROM banco_inventario WHERE id_personagem = %s", (id_personagem,))
            quantidade_banco = cursor.fetchone()
            
            if quantidade_banco:
                nova_quantidade_banco = quantidade_banco[0] + 1
                cursor.execute("UPDATE banco_inventario SET quantidade = %s WHERE id_personagem = %s", 
                               (nova_quantidade_banco, id_personagem))
            else:
                cursor.execute("INSERT INTO banco_inventario (id_personagem, quantidade) VALUES (%s, %s)", 
                               (id_personagem, 1))
            
            conn.commit()
            bot.edit_message_text(f"🥕 A carta {id_personagem} foi cenourada com sucesso!", chat_id, message_id)
        else:
            bot.edit_message_text(f"A carta {id_personagem} não está mais disponível para cenourar.", chat_id, message_id)
    
    except Exception as e:
        print(f"Erro ao processar cenourar: {e}")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Erro ao processar a cenoura.")
    finally:
        fechar_conexao(cursor, conn)

def callback_cenourar(call, bot):
    try:
        data_parts = call.data.split("_")
        acao = data_parts[1]
        id_usuario = int(data_parts[2])
        id_personagem = data_parts[3]
        
        if acao == "sim":
            cenourar_carta(call, id_usuario, id_personagem, bot)
        elif acao == "nao":
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Operação de cenoura cancelada.")
    except Exception as e:
        print(f"Erro ao processar callback de cenoura: {e}")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Erro ao processar a cenoura.")
        traceback.print_exc()

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


