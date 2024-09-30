from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bd import *
from gif import *
import globals
from botoes import *
import random      
        
def obter_historico_trocas(id_usuario):
    try:
        conn, cursor = conectar_banco_dados()
        query_obter_historico = """
            SELECT id_usuario1, id_usuario2, id_carta_usuario1, id_carta_usuario2, aceita
            FROM historico_trocas
            WHERE id_usuario1 = %s
            ORDER BY id DESC
            LIMIT 10
        """
        cursor.execute(query_obter_historico, (id_usuario,))
        historico = cursor.fetchall()

        if historico:
            return historico
        else:
            return []

    except mysql.connector.Error as e:
        print(f"Erro ao obter histórico de trocas: {e}")
        return []

    finally:
        fechar_conexao(cursor, conn)

def obter_historico_pescas(id_usuario):
    try:
        conn, cursor = conectar_banco_dados()

        query_obter_historico = """
            SELECT id_carta, data_hora
            FROM historico_cartas_giradas
            WHERE id_usuario = %s
            ORDER BY data_hora DESC
            LIMIT 10
        """
        cursor.execute(query_obter_historico, (id_usuario,))
        historico = cursor.fetchall()

        if historico:
            return historico
        else:
            return []

    except mysql.connector.Error as e:
        print(f"Erro ao obter histórico de pescas: {e}")
        return []

    finally:
        fechar_conexao(cursor, conn)