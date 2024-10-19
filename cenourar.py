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
        print(f"Erro ao processar o comando de cenourar: {e}")
        traceback.print_exc()
        bot.send_message(message.chat.id, "Erro ao processar o comando de cenourar.")
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


