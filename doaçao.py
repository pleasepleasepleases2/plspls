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
import mysql.connector.pooling


dbconfig_cenoura = {
    'host': '127.0.0.1',
    'database': 'garden',
    'user': 'teste',
    'password': '#Folkevermore13',
    'ssl_disabled': True
}

pool_cenoura = mysql.connector.pooling.MySQLConnectionPool(pool_name="pool_doar",
                                                           pool_size=32,  # Tamanho maior para lidar com mais conexões simultâneas
                                                           pool_reset_session=True,
                                                           **dbconfig_cenoura)

def conectar_banco_dados_cenoura():
    conn = pool_cenoura.get_connection()
    cursor = conn.cursor()
    return conn, cursor

def confirmar_doacao(eu, minhacarta, destinatario_id, chat_id,message_id,qnt):
    try:
        conn, cursor = conectar_banco_dados_cenoura()

        qnt_carta = verifica_inventario_troca(eu, minhacarta)
        valor = qnt
        diminuir_cenouras(eu, valor)
        if qnt_carta > 0:
            cursor.execute("UPDATE inventario SET quantidade = quantidade - %s WHERE id_usuario = %s AND id_personagem = %s",
                           (qnt, eu, minhacarta))

            cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s",
                           (destinatario_id, minhacarta))
            qnt_destinatario = cursor.fetchone()

            if qnt_destinatario:
                cursor.execute("UPDATE inventario SET quantidade = quantidade + %s WHERE id_usuario = %s AND id_personagem = %s",
                               (qnt, destinatario_id, minhacarta))
            else:
                cursor.execute("INSERT INTO inventario (id_usuario, id_personagem, quantidade) VALUES (%s, %s, %s)",
                               (destinatario_id, minhacarta,qnt))

            conn.commit()
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Doação realizada com sucesso!")
        else:
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Você não pode doar uma carta que não possui.")
       
    except Exception as e:
        bot.send_message(chat_id, "Houve um erro ao processar a doação. Tente novamente.")
        traceback.print_exc()
        erro = traceback.format_exc()
        mensagem = f"Doação com erro: {eu}, {minhacarta}, {destinatario_id},{qnt}. erro: {e}\n{erro}"
        bot.send_message(grupodeerro, mensagem, parse_mode="HTML")