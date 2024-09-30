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
        cursor.execute("INSERT INTO anotacoes (id_usuario, data, nome_usuario, anotacao) VALUES (%s, %s, %s, %s)",
                       (user_id, today, user_name, note))
        conn.commit()
        bot.send_message(message.chat.id, "Sua anotação foi registrada com sucesso!")

    except mysql.connector.Error as err:
        print(f"Erro ao registrar anotação: {err}")
        bot.send_message(message.chat.id, "Ocorreu um erro ao tentar registrar sua anotação. Tente novamente mais tarde.")
    finally:
        fechar_conexao(cursor, conn)