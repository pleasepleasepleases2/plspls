import telebot
import traceback
from credentials import *
from bd import *
bot = telebot.TeleBot(API_TOKEN)


def enviar_pergunta_cenoura(message, id_usuario, ids_personagens, bot):
    try:
        conn, cursor = conectar_banco_dados()

        # Recupera os nomes das cartas e formata a pergunta
        cartas_formatadas = []
        for id_personagem in ids_personagens:
            cursor.execute("SELECT nome FROM personagens WHERE id_personagem = %s", (id_personagem,))
            nome_carta = cursor.fetchone()
            if nome_carta:
                cartas_formatadas.append(f"{id_personagem} - {nome_carta[0]}")

        texto_pergunta = f"Você deseja mesmo cenourar as cartas:\n\n" + "\n".join(cartas_formatadas)

        keyboard = telebot.types.InlineKeyboardMarkup()
        sim_button = telebot.types.InlineKeyboardButton(text="Sim", callback_data=f"cenourar_sim_{id_usuario}_{'_'.join(ids_personagens)}")
        nao_button = telebot.types.InlineKeyboardButton(text="Não", callback_data=f"cenourar_nao_{id_usuario}")
        keyboard.row(sim_button, nao_button)
        
        bot.send_message(message.chat.id, texto_pergunta, reply_markup=keyboard)
    
    except Exception as e:
        print(f"Erro ao enviar pergunta de cenourar: {e}")
        traceback.print_exc()  # Mostra mais detalhes da exceção
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def processar_verificar_e_cenourar(message, bot):
    try:
        conn, cursor = conectar_banco_dados()
        id_usuario = message.from_user.id

        if len(message.text.split()) < 2:
            bot.send_message(message.chat.id, "Por favor, forneça os IDs dos personagens que deseja cenourar, separados por vírgulas. Exemplo: /cenourar 12345,67890")
            return
        
        ids_personagens_bruto = ' '.join(message.text.split()[1:]).strip()
        ids_personagens = [id_personagem.strip() for id_personagem in ids_personagens_bruto.split(',') if id_personagem.strip()]

        cartas_a_cenourar = []
        cartas_nao_encontradas = []

        for id_personagem in ids_personagens:
            cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (id_usuario, id_personagem))
            quantidade_atual = cursor.fetchone()

            if quantidade_atual and quantidade_atual[0] >= 1:
                cartas_a_cenourar.append(id_personagem)
            else:
                cartas_nao_encontradas.append(id_personagem)

        if cartas_a_cenourar:
            enviar_pergunta_cenoura(message, id_usuario, cartas_a_cenourar, bot)
        if cartas_nao_encontradas:
            bot.send_message(message.chat.id, f"As seguintes cartas não foram encontradas no inventário ou você não tem quantidade suficiente: {', '.join(cartas_nao_encontradas)}")
        if not cartas_a_cenourar and not cartas_nao_encontradas:
            bot.send_message(message.chat.id, "Nenhuma carta válida foi encontrada para cenourar.")
    except Exception as e:
        print(f"DEBUG: Erro ao processar o comando de cenourar: {e}")
        traceback.print_exc()  # Mostra mais detalhes da exceção
        bot.send_message(message.chat.id, "Erro ao processar o comando de cenourar.")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Certifique-se de definir corretamente o 'user_id' ou 'id_usuario'

def cenourar_carta(call, id_usuario, ids_personagens):
    try:
        conn, cursor = conectar_banco_dados()
        chat_id = call.message.chat.id
        message_id = call.message.message_id

        cartas_cenouradas = []
        cartas_nao_encontradas = []

        for id_personagem in ids_personagens:
            cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (id_usuario, id_personagem))
            quantidade_atual = cursor.fetchone()

            if quantidade_atual and quantidade_atual[0] > 0:
                nova_quantidade = quantidade_atual[0] - 1
                cursor.execute("UPDATE inventario SET quantidade = %s WHERE id_usuario = %s AND id_personagem = %s", 
                               (nova_quantidade, id_usuario, id_personagem))
                conn.commit()

                cursor.execute("SELECT cenouras FROM usuarios WHERE id_usuario = %s", (id_usuario,))
                cenouras = cursor.fetchone()[0]  # Pegando a quantidade de cenouras

                novas_cenouras = cenouras + 1
                cursor.execute("UPDATE usuarios SET cenouras = %s WHERE id_usuario = %s", (novas_cenouras, id_usuario))
                conn.commit()

                cartas_cenouradas.append(id_personagem)
            else:
                cartas_nao_encontradas.append(id_personagem)

        # Mensagens de confirmação
        if cartas_cenouradas:
            mensagem_final = f"🥕<b> Agora você está mais rico em cenouras!</b>\nCartas cenouradas com sucesso:\n\n{', '.join(cartas_cenouradas)}"

            bot.send_message(chat_id, mensagem_final, parse_mode="HTML")
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=mensagem_final,parse_mode="HTML")
     
        if cartas_nao_encontradas:
            bot.send_message(chat_id, f"As seguintes cartas não foram encontradas no inventário ou a quantidade é insuficiente: {', '.join(cartas_nao_encontradas)}")
    
    except mysql.connector.Error as e:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Erro ao processar a cenoura.")
    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except Exception as e:
            print(f"DEBUG: Erro ao fechar conexão ou cursor: {e}")


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


