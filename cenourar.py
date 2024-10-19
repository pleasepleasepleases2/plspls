import telebot
import traceback
from bd import conectar_banco_dados, fechar_conexao


def enviar_pergunta_cenoura(message, id_usuario, ids_personagens, bot):
    try:
        texto_pergunta = f"Você deseja cenourar as cartas: {', '.join(ids_personagens)}?"
        keyboard = telebot.types.InlineKeyboardMarkup()
        sim_button = telebot.types.InlineKeyboardButton(text="Sim", callback_data=f"cenourar_sim_{id_usuario}_{','.join(ids_personagens)}")
        nao_button = telebot.types.InlineKeyboardButton(text="Não", callback_data=f"cenourar_nao_{id_usuario}_{','.join(ids_personagens)}")
        keyboard.row(sim_button, nao_button)
        bot.send_message(message.chat.id, texto_pergunta, reply_markup=keyboard)
    except Exception as e:
        print(f"Erro ao enviar pergunta de cenourar: {e}")
        traceback.print_exc()

def processar_verificar_e_cenourar(message, bot):
    try:
        print("Processando comando de cenourar...")
        conn, cursor = conectar_banco_dados()
        id_usuario = message.from_user.id
        print(f"ID do usuário: {id_usuario}")

        if len(message.text.split()) < 2:
            bot.send_message(message.chat.id, "Por favor, forneça os IDs dos personagens que deseja cenourar, separados por vírgulas. Exemplo: /cenourar 12345,67890")
            return
        
        ids_personagens = message.text.split()[1].strip().split(',')
        ids_personagens = [id_personagem.strip() for id_personagem in ids_personagens]
        print(f"IDs dos personagens: {ids_personagens}")

        # Verifica se as cartas estão no inventário
        cartas_a_cenourar = []
        for id_personagem in ids_personagens:
            cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (id_usuario, id_personagem))
            quantidade_atual = cursor.fetchone()
            if quantidade_atual and quantidade_atual[0] >= 1:
                cartas_a_cenourar.append(id_personagem)
            else:
                bot.send_message(message.chat.id, f"A carta {id_personagem} não foi encontrada no inventário ou você não tem quantidade suficiente.")

        if cartas_a_cenourar:
            enviar_pergunta_cenoura(message, id_usuario, cartas_a_cenourar, bot)
        else:
            bot.send_message(message.chat.id, "Nenhuma carta válida foi encontrada para cenourar.")
    except Exception as e:
        print(f"Erro ao processar o comando de cenourar: {e}")
        traceback.print_exc()
        bot.send_message(message.chat.id, "Erro ao processar o comando de cenourar.")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def cenourar_carta(call, id_usuario, ids_personagens, bot):
    try:
        print(f"ID do usuário: {id_usuario}, IDs dos personagens: {ids_personagens}")
        conn, cursor = conectar_banco_dados()
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        
        ids_personagens_list = ids_personagens.split(",")
        ids_personagens_list = [id.strip() for id in ids_personagens_list]

        # Verificar se possui todas as cartas
        cartas_cenouradas = []
        for id_personagem in ids_personagens_list:
            cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (id_usuario, id_personagem))
            quantidade_atual = cursor.fetchone()
            if quantidade_atual and quantidade_atual[0] > 0:
                nova_quantidade = quantidade_atual[0] - 1
                cursor.execute("UPDATE inventario SET quantidade = %s WHERE id_usuario = %s AND id_personagem = %s", (nova_quantidade, id_usuario, id_personagem))
                
                # Adicionar cenouras
                cursor.execute("SELECT cenouras FROM usuarios WHERE id_usuario = %s", (id_usuario,))
                cenouras = cursor.fetchone()[0] + 1
                cursor.execute("UPDATE usuarios SET cenouras = %s WHERE id_usuario = %s", (cenouras, id_usuario))
                
                # Atualizar banco de inventário
                cursor.execute("SELECT quantidade FROM banco_inventario WHERE id_personagem = %s", (id_personagem,))
                quantidade_banco = cursor.fetchone()
                if quantidade_banco:
                    nova_quantidade_banco = quantidade_banco[0] + 1
                    cursor.execute("UPDATE banco_inventario SET quantidade = %s WHERE id_personagem = %s", (nova_quantidade_banco, id_personagem))
                else:
                    cursor.execute("INSERT INTO banco_inventario (id_personagem, quantidade) VALUES (%s, %s)", (id_personagem, 1))

                conn.commit()
                cartas_cenouradas.append(id_personagem)
                bot.edit_message_text(f"🥕 Cenourando carta: {id_personagem}", chat_id, message_id)

        mensagem_final = "🥕 Cartas cenouradas com sucesso:\n\n" + "\n".join(cartas_cenouradas)
        bot.edit_message_text(mensagem_final, chat_id, message_id)
    
    except Exception as e:
        print(f"Erro ao processar cenoura: {e}")
        traceback.print_exc()
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Erro ao processar a cenoura.")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def callback_cenourar(call, bot):
    try:
        data_parts = call.data.split("_")
        acao = data_parts[1]
        id_usuario = int(data_parts[2])
        ids_personagens = data_parts[3] if len(data_parts) >= 4 else ""
        print(f"Callback recebido: Ação: {acao}, ID usuário: {id_usuario}, IDs personagens: {ids_personagens}")
        
        if acao == "sim":
            cenourar_carta(call, id_usuario, ids_personagens, bot)
        elif acao == "nao":
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Operação de cenoura cancelada.")
    except Exception as e:
        print(f"Erro ao processar callback de cenoura: {e}")
        traceback.print_exc()
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Erro ao processar a cenoura.")

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


