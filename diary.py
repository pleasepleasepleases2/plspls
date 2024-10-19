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

def receive_note(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    note = message.text
    today = date.today()

    conn, cursor = conectar_banco_dados()

    try:
        # Registrar a anotação no banco de dados
        cursor.execute("INSERT INTO anotacoes (id_usuario, data, nome_usuario, anotacao) VALUES (%s, %s, %s, %s)",
                       (user_id, today, user_name, note))
        conn.commit()
        bot.send_message(message.chat.id, "Sua anotação foi registrada com sucesso!")

    except mysql.connector.Error as err:
        print(f"Erro ao registrar anotação: {err}")
        bot.send_message(message.chat.id, "Ocorreu um erro ao tentar registrar sua anotação. Tente novamente mais tarde.")
    finally:
        fechar_conexao(cursor, conn)
        
def diary_command(message):
    user_id = message.from_user.id
    today = date.today()

    conn, cursor = conectar_banco_dados()

    try:
        # Verifica se o usuário é VIP
        cursor.execute("SELECT COUNT(*) FROM vips WHERE id_usuario = %s", (user_id,))
        is_vip = cursor.fetchone()[0] > 0

        # Recupera o registro do diário do usuário
        cursor.execute("SELECT ultimo_diario, dias_consecutivos FROM diario WHERE id_usuario = %s", (user_id,))
        result = cursor.fetchone()

        if result:
            ultimo_diario, dias_consecutivos = result

            # Verifica se o usuário já fez o diário hoje
            if ultimo_diario == today:
                bot.send_message(message.chat.id, "Você já recebeu suas cenouras hoje. Volte amanhã!")
                return

            # Se fez ontem, aumenta o streak
            if ultimo_diario == today - timedelta(days=1):
                dias_consecutivos += 1
            elif is_vip and ultimo_diario == today - timedelta(days=2):
                # Se VIP, permite recuperar um dia perdido
                dias_consecutivos += 1
            else:
                # Caso contrário, reseta o streak
                dias_consecutivos = 1

            # Calcula as cenouras baseadas no streak
            cenouras = min(dias_consecutivos * 10, 100)

            # Atualiza o diário e o saldo de cenouras do usuário
            cursor.execute("UPDATE diario SET ultimo_diario = %s, dias_consecutivos = %s WHERE id_usuario = %s", 
                           (today, dias_consecutivos, user_id))
            cursor.execute("UPDATE usuarios SET cenouras = cenouras + %s WHERE id_usuario = %s", 
                           (cenouras, user_id))
            conn.commit()

        else:
            # Se for a primeira vez que o usuário registra no diário
            cenouras = 10
            dias_consecutivos = 1
            cursor.execute("INSERT INTO diario (id_usuario, ultimo_diario, dias_consecutivos) VALUES (%s, %s, %s)", 
                           (user_id, today, dias_consecutivos))
            cursor.execute("UPDATE usuarios SET cenouras = cenouras + %s WHERE id_usuario = %s", 
                           (cenouras, user_id))
            conn.commit()

        # Envia a mensagem de confirmação ao usuário
        phrase = random.choice(phrases)
        fortune = random.choice(fortunes)
        bot.send_message(message.chat.id, f"<i>{phrase}</i>\n\n<b>{fortune}</b>\n\nVocê recebeu <i>{cenouras} cenouras</i>!\n\n<b>Dias consecutivos:</b> <i>{dias_consecutivos}</i>\n\n", parse_mode="HTML")

        # Pergunta se o usuário deseja adicionar uma anotação ao diário
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(text="Sim", callback_data="add_note"))
        markup.add(telebot.types.InlineKeyboardButton(text="Não", callback_data="cancel_note"))
        bot.send_message(message.chat.id, "Deseja anotar algo nesse dia especial?", reply_markup=markup)

    except mysql.connector.Error as err:
        print(f"Erro ao processar o comando /diary: {err}")
        bot.send_message(message.chat.id, "Ocorreu um erro ao tentar registrar seu diário. Tente novamente mais tarde.")
    finally:
        fechar_conexao(cursor, conn)

def pages_command(message):
    user_id = message.from_user.id
    conn, cursor = conectar_banco_dados()

    try:
        cursor.execute("SELECT data, anotacao FROM anotacoes WHERE id_usuario = %s ORDER BY data DESC", (user_id,))
        anotacoes = cursor.fetchall()

        if not anotacoes:
            bot.send_message(message.chat.id, "Você ainda não tem anotações no diário.")
            return

        response = ""
        total_anotacoes = len(anotacoes)
        for i, (data, anotacao) in enumerate(anotacoes, 1):
            page_number = total_anotacoes - i + 1
            response += f"Dia {page_number} - {data.strftime('%d/%m/%Y')}\n"
        
        bot.send_message(message.chat.id, response)

    except mysql.connector.Error as err:
        print(f"Erro ao obter anotações: {err}")
        bot.send_message(message.chat.id, "Ocorreu um erro ao tentar obter suas anotações. Tente novamente mais tarde.")
    finally:
        fechar_conexao(cursor, conn)

def page_command(message):
    user_id = message.from_user.id
    params = message.text.split(' ', 1)[1:]
    if len(params) < 1:
        bot.send_message(message.chat.id, "Uso: /page <número_da_página>")
        return
    page_number = int(params[0])

    conn, cursor = conectar_banco_dados()

    try:
        cursor.execute("SELECT data, anotacao FROM anotacoes WHERE id_usuario = %s ORDER BY data DESC", (user_id,))
        anotacoes = cursor.fetchall()

        if not anotacoes:
            bot.send_message(message.chat.id, "Você ainda não tem anotações no diário.")
            return

        if page_number < 1 or page_number > len(anotacoes):
            bot.send_message(message.chat.id, "Número de página inválido.")
            return

        data, anotacao = anotacoes[page_number - 1]
        response = f"Mabigarden, dia {data.strftime('%d/%m/%Y')}\n\nQuerido diário... {anotacao}"
        
        bot.send_message(message.chat.id, response)

    except mysql.connector.Error as err:
        print(f"Erro ao obter anotação: {err}")
        bot.send_message(message.chat.id, "Ocorreu um erro ao tentar obter sua anotação. Tente novamente mais tarde.")
    finally:
        fechar_conexao(cursor, conn)

def edit_diary(message, bot):
    user_id = message.from_user.id
    today = date.today()

    conn, cursor = conectar_banco_dados()

    try:
        cursor.execute("SELECT anotacao FROM anotacoes WHERE id_usuario = %s AND data = %s", (user_id, today))
        result = cursor.fetchone()

        if result:
            anotacao = result[0]
            bot.send_message(message.chat.id, f"Sua anotação para hoje é:\n\n<i>\"{anotacao}\"</i>\n\nEscolha uma ação:")
        else:
            bot.send_message(message.chat.id, "Você ainda não tem uma anotação para hoje. Deseja fazer uma anotação?")
        
        # Botões para editar ou apagar a mensagem
        markup = types.InlineKeyboardMarkup()
        edit_button = types.InlineKeyboardButton("✍️ Editar", callback_data="edit_note")
        cancel_button = types.InlineKeyboardButton("❌ Cancelar", callback_data="cancel_edit")
        markup.add(edit_button, cancel_button)

        bot.send_message(message.chat.id, "Escolha uma opção:", reply_markup=markup)

    except Exception as e:
        bot.send_message(message.chat.id, "Erro ao processar o comando de edição do diário.")
        print(f"Erro ao editar anotação: {e}")
    finally:
        fechar_conexao(cursor, conn)

def salvar_ou_editar_anotacao(message, user_id, today, bot):
    anotacao = message.text

    conn, cursor = conectar_banco_dados()

    try:
        cursor.execute("SELECT COUNT(*) FROM anotacoes WHERE id_usuario = %s AND data = %s", (user_id, today))
        existe_anotacao = cursor.fetchone()[0]

        if existe_anotacao:
            cursor.execute("UPDATE anotacoes SET anotacao = %s WHERE id_usuario = %s AND data = %s", (anotacao, user_id, today))
            bot.send_message(message.chat.id, "Sua anotação foi editada com sucesso!")
        else:
            cursor.execute("INSERT INTO anotacoes (id_usuario, data, nome_usuario, anotacao) VALUES (%s, %s, %s, %s)", 
                           (user_id, today, message.from_user.first_name, anotacao))
            bot.send_message(message.chat.id, "Sua anotação foi registrada com sucesso!")
        
        conn.commit()

    except Exception as e:
        bot.send_message(message.chat.id, "Erro ao salvar ou editar sua anotação.")
        print(f"Erro ao salvar ou editar anotação: {e}")
    finally:
        fechar_conexao(cursor, conn)

def cancelar_edicao(call, bot):
    bot.delete_message(call.message.chat.id, call.message.message_id)

