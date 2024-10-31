from pesquisas import *
from user import *
from bd import *
from loja import *
from gnome import *
from operacoes import *
from inventario import *
from math import ceil
from pesquisas import *
from user import *
from bd import *
from loja import *
from gnome import *
from operacoes import *
from inventario import *
from gif import *
import random
import traceback

def comando_evento_s(id_usuario, evento, subcategoria, cursor, usuario_inicial, page=1):
    subcategoria = subcategoria.strip().title()
    def formatar_id(id_personagem):
        return str(id_personagem).zfill(4)
    
    items_per_page = 20
    offset = (page - 1) * items_per_page
    
    sql_usuario = f"""
        SELECT e.emoji, e.id_personagem, e.nome AS nome_personagem, e.subcategoria
        FROM evento e
        JOIN inventario i ON e.id_personagem = i.id_personagem
        WHERE i.id_usuario = {id_usuario} AND e.evento = '{evento}'
        ORDER BY CAST(e.id_personagem AS UNSIGNED) ASC
        LIMIT {items_per_page} OFFSET {offset};
    """
    cursor.execute(sql_usuario)
    resultados_usuario = cursor.fetchall()

    sql_total = f"""
        SELECT COUNT(*)
        FROM evento e
        JOIN inventario i ON e.id_personagem = i.id_personagem
        WHERE i.id_usuario = {id_usuario} AND e.evento = '{evento}';
    """
    cursor.execute(sql_total)
    total_items = cursor.fetchone()[0]
    total_pages = ceil(total_items / items_per_page)
    
    if resultados_usuario:
        lista_cartas = ""

        for carta in resultados_usuario:
            id_carta = carta[1]
            emoji_carta = carta[0]
            nome_carta = carta[2]
            subcategoria_carta = carta[3].title()
            lista_cartas += f"{emoji_carta} {id_carta} — {nome_carta}\n"
        if lista_cartas:
            resposta = f"🌾 | Cartas do evento {evento} no inventario de {usuario_inicial}:\n\n{lista_cartas}"
            return subcategoria_carta, resposta, total_pages
    return f"🌧 Sem cartas de {subcategoria} no evento {evento}! A jornada continua..."

def comando_evento_f(id_usuario, evento, subcategoria, cursor, usuario_inicial, page=1):
    subcategoria = subcategoria.strip().title()
    def formatar_id(id_personagem):
        return str(id_personagem).zfill(4)
    
    items_per_page = 20
    offset = (page - 1) * items_per_page
    
    sql_faltantes = f"""
        SELECT e.emoji, e.id_personagem, e.nome AS nome_personagem, e.subcategoria
        FROM evento e
        WHERE e.evento = '{evento}' 
            AND NOT EXISTS (
                SELECT 1
                FROM inventario i
                WHERE i.id_usuario = {id_usuario} AND i.id_personagem = e.id_personagem
            )
        ORDER BY CAST(e.id_personagem AS UNSIGNED) ASC
        LIMIT {items_per_page} OFFSET {offset};
    """
    cursor.execute(sql_faltantes)
    resultados_faltantes = cursor.fetchall()

    sql_total = f"""
        SELECT COUNT(*)
        FROM evento e
        WHERE e.evento = '{evento}' 
            AND NOT EXISTS (
                SELECT 1
                FROM inventario i
                WHERE i.id_usuario = {id_usuario} AND i.id_personagem = e.id_personagem
            );
    """
    cursor.execute(sql_total)
    total_items = cursor.fetchone()[0]
    total_pages = ceil(total_items / items_per_page)

    if resultados_faltantes:
        lista_cartas = ""

        for carta in resultados_faltantes:
            id_carta = carta[1]
            emoji_carta = carta[0]
            nome_carta = carta[2]
            subcategoria_carta = carta[3].title()
            lista_cartas += f"{emoji_carta} {id_carta}— {nome_carta}\n"
        if lista_cartas:
            resposta = f"☀️ | Cartas do evento {evento} que não estão no inventário de {usuario_inicial}:\n\n{lista_cartas}"
            return subcategoria_carta, resposta, total_pages
    return f"☀️ Nada como a alegria de ter todas as cartas de {subcategoria} no evento {evento} na cesta!"

        
def get_random_card_valentine(subcategoria):
    try:
        conn, cursor = conectar_banco_dados()
        cursor.execute(
            "SELECT id_personagem, nome, subcategoria, imagem FROM evento WHERE subcategoria = %s AND evento = 'Inverno' ORDER BY RAND() LIMIT 1",
            (subcategoria,))
        evento_aleatorio = cursor.fetchone()
        if evento_aleatorio:

            id_personagem, nome, subcategoria, imagem = evento_aleatorio
            evento_formatado = {
                    'id_personagem': id_personagem,
                    'nome': nome,
                    'subcategoria': subcategoria,
                    'imagem': imagem  
                }

            return evento_formatado
        else:
            return None


    except Exception as e:
        print(f"Erro ao verificar subcategoria na tabela de eventos: {e}")
        return None

def alternar_evento():
    global evento_ativo
    evento_ativo = not evento_ativo

def get_random_subcategories_all_valentine(connection):
    cursor = connection.cursor()
    query = "SELECT subcategoria FROM evento WHERE evento = 'Inverno' ORDER BY RAND() LIMIT 2"
    cursor.execute(query)
    subcategories_valentine = [row[0] for row in cursor.fetchall()]

    cursor.close()
    return subcategories_valentine      

import newrelic.agent
import traceback

def callback_subcategory(call):
    try:
        subcategory_data = call.data.split("_")
        subcategory = subcategory_data[1]
        card = get_random_card_valentine(subcategory)
        if card:
            evento_aleatorio = card
            send_card_message(call.message, evento_aleatorio)
        else:
            bot.answer_callback_query(call.id, "Ocorreu um erro ao processar sua solicitação. Tente novamente mais tarde.")
    except Exception as e:
        newrelic.agent.record_exception()    
        print(f"Erro ao processar callback de subcategoria: {e}")
        traceback.print_exc()


def handle_evento_command(message):
    try:
        verificar_id_na_tabela(message.from_user.id, "ban", "iduser")
        conn, cursor = conectar_banco_dados()
        qnt_carta(message.from_user.id)
        id_usuario = message.from_user.id
        user = message.from_user
        usuario = user.first_name
        
        comando_parts = message.text.split(maxsplit=2)
        
        # Verificação para garantir que o comando tenha pelo menos dois argumentos
        if len(comando_parts) < 3:
            resposta = "Comando inválido. Use /evento <evento> <subcategoria>."
            bot.send_message(message.chat.id, resposta)
            return
        
        # Extrair evento e subcategoria corretamente
        evento = comando_parts[1].strip().lower()
        subcategoria = comando_parts[2].strip().lower()

        # Usar SQL com parâmetros para garantir segurança e precisão na consulta
        sql_evento_existente = "SELECT DISTINCT evento FROM evento WHERE evento = %s"
        cursor.execute(sql_evento_existente, (evento,))
        evento_existente = cursor.fetchone()
        
        if not evento_existente:
            resposta = f"Evento '{evento}' não encontrado na tabela de eventos."
            bot.send_message(message.chat.id, resposta)
            return

        # Verificar se é um comando de subcategoria "s" ou "f"
        if message.text.startswith('/evento s'):
            resposta_completa = comando_evento_s(id_usuario, evento, subcategoria, cursor, usuario)
        elif message.text.startswith('/evento f'):
            resposta_completa = comando_evento_f(id_usuario, evento, subcategoria, cursor, usuario)
        else:
            resposta = "Comando inválido. Use /evento s <evento> ou /evento f <evento>."
            bot.send_message(message.chat.id, resposta)
            return

        # Exibir resposta e botões de navegação, se houver mais páginas
        if isinstance(resposta_completa, tuple):
            subcategoria_pesquisada, lista, total_pages = resposta_completa
            resposta = f"{lista}\n\nPágina 1 de {total_pages}"

            markup = InlineKeyboardMarkup()
            if total_pages > 1:
                markup.add(InlineKeyboardButton("Próxima", callback_data=f"evt_next_{id_usuario}_{evento[:20]}_{subcategoria_pesquisada[:20]}_2"))

            bot.send_message(message.chat.id, resposta, reply_markup=markup)
        else:
            bot.send_message(message.chat.id, resposta_completa)

    except Exception as e:
        traceback.print_exc()
    finally:
        fechar_conexao(cursor, conn)


def handle_callback_query_evento(call):
    data_parts = call.data.split('_')
    action = data_parts[1]
    id_usuario_inicial = int(data_parts[2])
    evento = data_parts[3]
    subcategoria = data_parts[4]
    page = int(data_parts[5])
    
    try:
        conn, cursor = conectar_banco_dados()

        if action == "prev":
            page -= 1
        elif action == "next":
            page += 1

        if call.message.text.startswith('🌾'):
            resposta_completa = comando_evento_s(id_usuario_inicial, evento, subcategoria, cursor, call.from_user.first_name, page)
        else:
            resposta_completa = comando_evento_f(id_usuario_inicial, evento, subcategoria, cursor, call.from_user.first_name, page)

        if isinstance(resposta_completa, tuple):
            subcategoria_pesquisada, lista, total_pages = resposta_completa
            resposta = f"{lista}\n\nPágina {page} de {total_pages}"

            markup = InlineKeyboardMarkup()
            if page > 1:
                markup.add(InlineKeyboardButton("Anterior", callback_data=f"evt_prev_{id_usuario_inicial}_{evento}_{subcategoria}_{page}"))
            if page < total_pages:
                markup.add(InlineKeyboardButton("Próxima", callback_data=f"evt_next_{id_usuario_inicial}_{evento}_{subcategoria}_{page}"))

            bot.edit_message_text(resposta, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
        else:
            bot.edit_message_text(resposta_completa, chat_id=call.message.chat.id, message_id=call.message.message_id)
    except Exception as e:
        traceback.print_exc()
    finally:
        fechar_conexao(cursor, conn)

