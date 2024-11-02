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
from pescar import *
from gif import *
import random
import traceback
from math import ceil
import diskcache as dc
from cachetools import cached, TTLCache

# Configuração do cache persistente em disco para eventos
cache_eventos = dc.Cache('/tmp/eventos_cache')

# Configuração do cache com TTL de 30 minutos para reduzir consultas repetitivas ao banco de dados
ttl_cache = TTLCache(maxsize=100, ttl=1800)  # 30 minutos

# Função de cache para carregar dados de evento, com TTL usando `cachetools`
@cached(ttl_cache)
def carregar_dados_evento_cache(evento):
    """Carrega dados do evento no cache com TTL, consultando o banco de dados apenas quando necessário."""
    conn, cursor = conectar_banco_dados()
    try:
        # Total de personagens no evento
        cursor.execute("SELECT COUNT(*) FROM evento WHERE evento = %s", (evento,))
        total_personagens = cursor.fetchone()[0]

        # IDs de personagens no evento
        cursor.execute("SELECT id_personagem FROM evento WHERE evento = %s", (evento,))
        ids_personagens_evento = [row[0] for row in cursor.fetchall()]

        # Salva no cache de disco
        cache_eventos[evento] = {
            "total_personagens": total_personagens,
            "ids_personagens_evento": ids_personagens_evento
        }
    finally:
        fechar_conexao(cursor, conn)

# Função de cache para carregar dados de evento, com TTL usando `cachetools`
@cached(ttl_cache)
def carregar_dados_evento_cache(evento):
    """Carrega dados do evento no cache com TTL, consultando o banco de dados apenas quando necessário."""
    conn, cursor = conectar_banco_dados()
    try:
        # Total de personagens no evento
        cursor.execute("SELECT COUNT(*) FROM evento WHERE evento = %s", (evento,))
        total_personagens = cursor.fetchone()[0]

        # IDs de personagens no evento
        cursor.execute("SELECT id_personagem FROM evento WHERE evento = %s", (evento,))
        ids_personagens_evento = [row[0] for row in cursor.fetchall()]

        # Salva no cache de disco
        cache_eventos[evento] = {
            "total_personagens": total_personagens,
            "ids_personagens_evento": ids_personagens_evento
        }
    finally:
        fechar_conexao(cursor, conn)

def obter_total_personagens_evento(evento):
    """Obtém o total de personagens para um evento, usando o cache se disponível."""
    if evento not in cache_eventos:
        carregar_dados_evento_cache(evento)
    return cache_eventos[evento]["total_personagens"]

def obter_ids_personagens_evento_inventario(id_usuario, evento):
    """Obtém IDs de personagens no inventário do usuário para um evento."""
    if evento not in cache_eventos:
        carregar_dados_evento_cache(evento)

    conn, cursor = conectar_banco_dados()
    try:
        # Consulta para IDs no inventário
        query = """
            SELECT e.id_personagem 
            FROM evento e
            JOIN inventario i ON e.id_personagem = i.id_personagem
            WHERE i.id_usuario = %s AND e.evento = %s 
        """
        cursor.execute(query, (id_usuario, evento))
        ids_inventario = [row[0] for row in cursor.fetchall()]
        return ids_inventario
    finally:
        fechar_conexao(cursor, conn)
# Função para obter a quantidade de cartas de um usuário para um personagem específico
def obter_quantidade_cartas_usuario(id_usuario, id_personagem):
    """
    Consulta a quantidade de cartas de um personagem específico que o usuário possui.
    """
    conn, cursor = conectar_banco_dados()
    try:
        cursor.execute(
            "SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s",
            (id_usuario, id_personagem)
        )
        resultado = cursor.fetchone()
        return resultado[0] if resultado else 0
    except Exception as e:
        print(f"Erro ao obter quantidade de cartas do usuário: {e}")
        return 0
    finally:
        fechar_conexao(cursor, conn)
def obter_ids_personagens_evento_faltantes(id_usuario, evento):
    """Obtém IDs de personagens do evento que estão faltando no inventário do usuário."""
    if evento not in cache_eventos:
        carregar_dados_evento_cache(evento)

    conn, cursor = conectar_banco_dados()
    try:
        # Consulta para IDs faltantes no inventário
        query = """
            SELECT e.id_personagem
            FROM evento e
            WHERE e.evento = %s 
            AND e.id_personagem NOT IN (
                SELECT id_personagem FROM inventario WHERE id_usuario = %s
            )
        """
        cursor.execute(query, (evento, id_usuario))
        ids_faltantes = [row[0] for row in cursor.fetchall()]
        return ids_faltantes
    finally:
        fechar_conexao(cursor, conn)
def comando_evento_s(id_usuario, evento, cursor, usuario_inicial, page=1):
    items_per_page = 20
    offset = (page - 1) * items_per_page
    
    # Consulta SQL para cartas que o usuário possui do evento
    sql_usuario = f"""
        SELECT e.emoji, e.id_personagem, e.nome AS nome_personagem, e.subcategoria
        FROM evento e
        JOIN inventario i ON e.id_personagem = i.id_personagem
        WHERE i.id_usuario = %s AND e.evento = %s
        ORDER BY CAST(e.id_personagem AS UNSIGNED) ASC
        LIMIT %s OFFSET %s;
    """
    cursor.execute(sql_usuario, (id_usuario, evento, items_per_page, offset))
    resultados_usuario = cursor.fetchall()

    # Contagem total de cartas do evento que o usuário possui
    sql_total = """
        SELECT COUNT(*)
        FROM evento e
        JOIN inventario i ON e.id_personagem = i.id_personagem
        WHERE i.id_usuario = %s AND e.evento = %s;
    """
    cursor.execute(sql_total, (id_usuario, evento))
    total_items = cursor.fetchone()[0]
    total_pages = ceil(total_items / items_per_page)

    if resultados_usuario:
        lista_cartas = "\n".join(
            f"{carta[0]} {str(carta[1]).zfill(4)} — {carta[2]}"
            for carta in resultados_usuario
        )
        resposta = f"🌾 | Cartas do evento {evento} no inventário de {usuario_inicial}:\n\n{lista_cartas}"
        return evento, resposta, total_pages
    else:
        return f"🌧 Sem cartas do evento {evento} no inventário. A jornada continua..."

def comando_evento_f(id_usuario, evento, cursor, usuario_inicial, page=1):
    items_per_page = 20
    offset = (page - 1) * items_per_page
    
    # Consulta SQL para cartas faltantes do evento
    sql_faltantes = f"""
        SELECT e.emoji, e.id_personagem, e.nome AS nome_personagem, e.subcategoria
        FROM evento e
        WHERE e.evento = %s 
            AND NOT EXISTS (
                SELECT 1
                FROM inventario i
                WHERE i.id_usuario = %s AND i.id_personagem = e.id_personagem
            )
        ORDER BY CAST(e.id_personagem AS UNSIGNED) ASC
        LIMIT %s OFFSET %s;
    """
    cursor.execute(sql_faltantes, (evento, id_usuario, items_per_page, offset))
    resultados_faltantes = cursor.fetchall()

    # Contagem total de cartas faltantes do evento
    sql_total_faltantes = """
        SELECT COUNT(*)
        FROM evento e
        WHERE e.evento = %s 
            AND NOT EXISTS (
                SELECT 1
                FROM inventario i
                WHERE i.id_usuario = %s AND i.id_personagem = e.id_personagem
            );
    """
    cursor.execute(sql_total_faltantes, (evento, id_usuario))
    total_items_faltantes = cursor.fetchone()[0]
    total_pages = ceil(total_items_faltantes / items_per_page)

    if resultados_faltantes:
        lista_cartas = "\n".join(
            f"{carta[0]} {str(carta[1]).zfill(4)} — {carta[2]}"
            for carta in resultados_faltantes
        )
        resposta = f"☀️ | Cartas do evento {evento} que não estão no inventário de {usuario_inicial}:\n\n{lista_cartas}"
        return evento, resposta, total_pages
    else:
        return f"☀️ Nada como a alegria de ter todas as cartas do evento {evento} na cesta!"
        
def get_random_card_valentine(subcategoria):
    try:
        conn, cursor = conectar_banco_dados()
        cursor.execute(
            "SELECT id_personagem, nome, subcategoria, imagem FROM evento WHERE subcategoria = %s AND evento = 'Festival das Abóboras' ORDER BY RAND() LIMIT 1",
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
    conn, cursor = conectar_banco_dados()
    query = "SELECT subcategoria FROM evento WHERE evento = 'Festival das Abóboras' ORDER BY RAND() LIMIT 2"
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
        id_usuario = message.from_user.id
        user = message.from_user
        usuario = user.first_name

        # Dividir o comando para verificar corretamente "s" ou "f" e o evento
        comando_parts = message.text.split(maxsplit=2)
        if len(comando_parts) < 3:
            resposta = "Comando inválido. Use /evento s <evento> ou /evento f <evento>."
            bot.send_message(message.chat.id, resposta)
            return

        # Identificar o tipo de consulta ("s" ou "f") e o evento
        tipo_consulta = comando_parts[1].strip().lower()
        evento = comando_parts[2].strip().lower()

        # Verificar se o evento existe na tabela usando o nome correto
        sql_evento_existente = "SELECT DISTINCT evento FROM evento WHERE evento = %s"
        cursor.execute(sql_evento_existente, (evento,))
        evento_existente = cursor.fetchone()

        if not evento_existente:
            resposta = f"Evento '{evento}' não encontrado na tabela de eventos."
            bot.send_message(message.chat.id, resposta)
            return

        # Verificar tipo de consulta ("s" ou "f") e chamar a função correta
        if tipo_consulta == 's':
            resposta_completa = comando_evento_s(id_usuario, evento, cursor, usuario)
        elif tipo_consulta == 'f':
            resposta_completa = comando_evento_f(id_usuario, evento, cursor, usuario)
        else:
            resposta = "Comando inválido. Use /evento s <evento> ou /evento f <evento>."
            bot.send_message(message.chat.id, resposta)
            return

        # Exibir resposta e botões de navegação, se houver mais páginas
        if isinstance(resposta_completa, tuple):
            evento, lista, total_pages, total_personagens_subcategoria = resposta_completa
            resposta = (
                f"{lista}\n\n"
                f"📄 | Página 1/{total_pages}\n"
                f"🐟 | Personagens mostrados: {len(lista.splitlines())}/{total_personagens_subcategoria}\n\n"
            )

            markup = InlineKeyboardMarkup()
            if total_pages > 1:
                markup.add(InlineKeyboardButton("Próxima", callback_data=f"evt_next_{id_usuario}_{evento}_{2}"))

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
    page = int(data_parts[4])
    
    try:
        conn, cursor = conectar_banco_dados()

        if action == "prev":
            page -= 1
        elif action == "next":
            page += 1

        # Chamar a função correta com base no tipo de evento e página
        if call.message.text.startswith('🌾'):
            resposta_completa = comando_evento_s(id_usuario_inicial, evento, cursor, call.from_user.first_name, page)
        else:
            resposta_completa = comando_evento_f(id_usuario_inicial, evento, cursor, call.from_user.first_name, page)

        if isinstance(resposta_completa, tuple):
            evento, lista, total_pages, total_personagens_subcategoria = resposta_completa
            resposta = (
                f"{lista}\n\n"
                f"📄 | Página {page}/{total_pages}\n"
                f"🐟 | Personagens mostrados: {len(lista.splitlines())}/{total_personagens_subcategoria}\n\n"
            )

            markup = InlineKeyboardMarkup()
            if page > 1:
                markup.add(InlineKeyboardButton("Anterior", callback_data=f"evt_prev_{id_usuario_inicial}_{evento}_{page - 1}"))
            if page < total_pages:
                markup.add(InlineKeyboardButton("Próxima", callback_data=f"evt_next_{id_usuario_inicial}_{evento}_{page + 1}"))

            bot.edit_message_text(resposta, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
        else:
            bot.edit_message_text(resposta_completa, chat_id=call.message.chat.id, message_id=call.message.message_id)

    except Exception as e:
        traceback.print_exc()
    finally:
        fechar_conexao(cursor, conn)

def criar_markup_evento(pagina_atual, total_paginas, evento, tipo, id_usuario):
    """
    Cria um teclado inline para navegação entre páginas no contexto de eventos.
    """
    markup = types.InlineKeyboardMarkup(row_width=4)

    # Botões de navegação de páginas
    btn_inicio = types.InlineKeyboardButton("⏪️", callback_data=f"evento_{tipo}_1_{evento}_{id_usuario}")
    btn_anterior = types.InlineKeyboardButton("⬅️", callback_data=f"evento_{tipo}_{max(1, pagina_atual - 1)}_{evento}_{id_usuario}")
    btn_proxima = types.InlineKeyboardButton("➡️", callback_data=f"evento_{tipo}_{min(total_paginas, pagina_atual + 1)}_{evento}_{id_usuario}")
    btn_final = types.InlineKeyboardButton("⏩️", callback_data=f"evento_{tipo}_{total_paginas}_{evento}_{id_usuario}")

    # Adiciona os botões de navegação ao teclado
    markup.add(btn_inicio, btn_anterior, btn_proxima, btn_final)

    return markup
def adicionar_quantidade_cartas(quantidade):
    """
    Retorna uma string formatada com a quantidade de cartas.
    Se a quantidade for 1, retorna uma string vazia, caso contrário, mostra o número.
    """
    if quantidade > 1:
        return f"𖡩"
    return ""

def mostrar_pagina_evento_s(message, evento, id_usuario, pagina_atual, total_paginas, ids_personagens, total_personagens_evento, nome_usuario, call=None):
    try:
        # Conteúdo da mensagem
        resposta = f"🎉 Cartas do evento <i>{evento}</i> no inventário de <b>{nome_usuario}</b>:\n\n"
        resposta += f"📄 | Página {pagina_atual}/{total_paginas}\n"
        resposta += f"🎴 | {len(ids_personagens)}/{total_personagens_evento}\n\n"

        # Seleciona a página atual
        offset = (pagina_atual - 1) * 20
        ids_pagina = sorted(ids_personagens)[offset:offset + 20]

        for id_personagem in ids_pagina:
            info_personagem = consultar_informacoes_personagem(id_personagem)
            if info_personagem:
                emoji, nome, _ = info_personagem
                quantidade_cartas = obter_quantidade_cartas_usuario(id_usuario, id_personagem)
                resposta += f"{emoji} <code>{id_personagem}</code> • {nome} {adicionar_quantidade_cartas(quantidade_cartas)} \n"

        markup = criar_markup_evento(pagina_atual, total_paginas, evento, 's', id_usuario)

        if call:
            bot.edit_message_text(resposta, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, resposta, reply_markup=markup, parse_mode="HTML")

    except Exception as e:
        print(f"Erro ao mostrar página do evento: {e}")

def mostrar_pagina_evento_f(message, evento, id_usuario, pagina_atual, total_paginas, ids_personagens_faltantes, total_personagens_evento, nome_usuario, call=None):
    try:
        resposta = f"🌧️ A cesta de <b>{nome_usuario}</b> ainda não está completa para o evento<i> {evento}</i>:\n\n"
        resposta += f"📄 | Página {pagina_atual}/{total_paginas}\n"
        resposta += f"🎴 | {total_personagens_evento - len(ids_personagens_faltantes)}/{total_personagens_evento}\n\n"

        # Seleciona a página atual
        offset = (pagina_atual - 1) * 20
        ids_pagina = sorted(ids_personagens_faltantes)[offset:offset + 20]

        for id_personagem in ids_pagina:
            info_personagem = consultar_informacoes_personagem(id_personagem)
            if info_personagem:
                emoji, nome, _ = info_personagem
                resposta += f"{emoji} <code>{id_personagem}</code> • {nome}\n"

        markup = criar_markup_evento(pagina_atual, total_paginas, evento, 'f', id_usuario)

        if call:
            bot.edit_message_text(resposta, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, resposta, reply_markup=markup, parse_mode="HTML")

    except Exception as e:
        print(f"Erro ao mostrar página do evento: {e}")


def consultar_informacoes_personagem_evento(id_personagem):
    conn, cursor = conectar_banco_dados()
    try:
        cursor.execute("""
            SELECT emoji, nome, imagem FROM evento WHERE id_personagem = %s
        """, (id_personagem,))
        
        resultado = cursor.fetchone()
        if resultado:
            emoji, nome, imagem = resultado
            return emoji, nome, imagem
        else:
            return None
    except Exception as e:
        print(f"Erro ao consultar informações do personagem no evento: {e}")
        return None
    finally:
        fechar_conexao(cursor, conn)

def consultar_informacoes_personagem(id_personagem):
    """
    Consulta as informações de um personagem específico na tabela 'evento'.
    """
    conn, cursor = conectar_banco_dados()
    try:
        query = """
            SELECT emoji, nome, imagem
            FROM evento
            WHERE id_personagem = %s
        """
        cursor.execute(query, (id_personagem,))
        resultado = cursor.fetchone()

        if resultado:
            emoji, nome, imagem = resultado
            return emoji, nome, imagem
        else:
            print(f"Personagem com ID {id_personagem} não encontrado na tabela de eventos.")
            return None, None, None

    except mysql.connector.Error as err:
        print(f"Erro ao consultar informações do personagem: {err}")
        return None, None, None

    finally:
        fechar_conexao(cursor, conn)
