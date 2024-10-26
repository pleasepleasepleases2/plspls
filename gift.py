from pesquisas import *
from user import *
from bd import *
from loja import *
from gnome import *
from cenourar import *


@bot.callback_query_handler(func=lambda call: call.data.startswith('total_'))
def callback_total_personagem(call):
    conn, cursor = conectar_banco_dados()
    chat_id = call.message.chat.id

    id_pesquisa = call.data.split('_')[1]

    sql_total = "SELECT total FROM personagens WHERE id_personagem = %s"
    cursor.execute(sql_total, (id_pesquisa,))
    total_pescados = cursor.fetchone()

    if total_pescados is not None and total_pescados[0] is not None:
        if total_pescados[0] > 1:
            bot.answer_callback_query(call.id, text=f"O personagem foi pescado {total_pescados[0]} vezes!", show_alert=True)
        elif total_pescados[0] == 1:
            bot.answer_callback_query(call.id, text=f"O personagem foi pescado {total_pescados[0]} vez!", show_alert=True)
        else:
            bot.answer_callback_query(call.id, text="Esse personagem ainda não foi pescado :(", show_alert=True)
    else:
        bot.answer_callback_query(call.id, text="Esse personagem ainda não foi pescado :(", show_alert=True)
        
@bot.message_handler(commands=['rev'])
def handle_rev_cards(message):
    if message.from_user.id != 1112853187:
        bot.reply_to(message, "Você não é a Maria para usar esse comando.")
        return
    try:
        _, quantity, card_id, user_id = message.text.split()
        quantity = int(quantity)
        card_id = int(card_id)
        user_id = int(user_id)
    except (ValueError, IndexError):
        bot.reply_to(message, "Por favor, use o formato correto: /rev quantidade card_id user_id")
        return
    success = rev_cards(message, quantity, card_id, user_id)
    if success:
        bot.reply_to(message, f"{quantity} cartas removidas com sucesso!")

def rev_cards(message, quantity, card_id, user_id):
    for _ in range(quantity):
        query = "SELECT * FROM inventario WHERE id_personagem = %s AND id_usuario = %s"
        cursor.execute(query, (card_id, user_id))
        existing_card = cursor.fetchone()

        if existing_card and int(existing_card[3]) > 0:
            new_quantity = int(existing_card[3]) - 1
            update_query = "UPDATE inventario SET quantidade = %s WHERE id_personagem = %s AND id_usuario = %s"
            cursor.execute(update_query, (new_quantity, card_id, user_id))
        else:
            bot.reply_to(message, f"O usuário {user_id} não tem cartas suficientes do ID {card_id} para remover.")
            return False

        update_total_query = "UPDATE cartas SET total = total - 1 WHERE id = %s"
        cursor.execute(update_total_query, (card_id,))

    conn.commit()
    return True


def gift_cards(quantity, card_id, user_id):
    for _ in range(quantity):
        conn, cursor = conectar_banco_dados()
        query = "SELECT * FROM inventario WHERE id_personagem = %s AND id_usuario = %s"
        cursor.execute(query, (card_id, user_id))
        existing_card = cursor.fetchone()

        if existing_card:
            new_quantity = int(existing_card[3]) + int(quantity)
            update_query = "UPDATE inventario SET quantidade = %s WHERE id_personagem = %s AND id_usuario = %s"
            cursor.execute(update_query, (new_quantity, card_id, user_id))
        else:
            insert_query = "INSERT INTO inventario (id_personagem, id_usuario, quantidade) VALUES (%s, %s, %s)"
            cursor.execute(insert_query, (card_id, user_id))

        update_total_query = "UPDATE personagens SET total = total + 1 WHERE id_personagem = %s"
        cursor.execute(update_total_query, (card_id,))
    conn.commit()
def update_total_personagem(id_personagem, quantidade):
    try:
        conn, cursor = conectar_banco_dados()
        cursor.execute("UPDATE personagens SET total = total - %s WHERE id_personagem = %s", (quantidade, id_personagem))
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Erro ao atualizar o total na tabela personagens: {err}")
    finally:
        fechar_conexao(cursor, conn)

def cenourar_carta(message, id_usuario, id_personagens, sim=True):
    try:
        conn, cursor = conectar_banco_dados()
        mensagem_cenoura = f"Cenourando carta:\n"
        cartas_cenouradas = []

        for id_personagem in id_personagens.split(","):
            id_personagem = id_personagem.strip()
            cursor.execute(
                "SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s",
                (id_usuario, id_personagem))
            quantidade_atual = cursor.fetchone()

            if quantidade_atual is not None and quantidade_atual[0] > 0:
                quantidade_atual = int(quantidade_atual[0])
                cursor.execute(
                    "SELECT cenouras FROM usuarios WHERE id_usuario = %s",
                    (id_usuario,))
                cenouras = int(cursor.fetchone()[0])

                if quantidade_atual >= 1:
                    nova_quantidade = quantidade_atual - 1
                    novas_cenouras = cenouras + 1
                    cursor.execute(
                        "UPDATE inventario SET quantidade = %s WHERE id_usuario = %s AND id_personagem = %s",
                        (nova_quantidade, id_usuario, id_personagem))
                    cursor.execute(
                        "UPDATE usuarios SET cenouras = %s WHERE id_usuario = %s",
                        (novas_cenouras, id_usuario))

                    cartas_cenouradas.append((id_personagem, nova_quantidade))
                    update_cartas_counters(id_personagem)
                    mensagem_cenoura += f"{id_personagem}\n"
                    update_total_personagem(id_personagem, 1) 
                    conn.commit()

            else:
                mensagem_erro = f"Erro ao processar a cenoura. A carta {id_personagem} não foi encontrada no inventário."
                bot.send_message(message.chat.id, mensagem_erro)

        bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=mensagem_cenoura)
        mensagem_consolidada = "Cartas cenouradas com sucesso:\n"
        for carta, nova_quantidade in cartas_cenouradas:
            mensagem_consolidada += f"{carta} - Nova quantidade: {nova_quantidade}\n"
        bot.send_message(message.chat.id, mensagem_consolidada)
    except Exception as e:
        print(f"Erro ao processar cenoura: {e}")
    finally:
        fechar_conexao(cursor, conn)
