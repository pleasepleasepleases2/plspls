from pesquisas import *
from user import *
from bd import *
from loja import *
from gnome import *

user_data = {}

import diskcache as dc
from cachetools import cached, TTLCache

# Cache com validade de 24 horas (86400 segundos)
cache = dc.Cache('./cache')

# Exemplo de cache com TTL (Time-To-Live)
ttl_cache = TTLCache(maxsize=100, ttl=30)
cache_longo = TTLCache(maxsize=100, ttl=3600)
cache_medio = TTLCache(maxsize=100, ttl=300)
@cached(cache_longo)
def verificar_apelido(subcategoria):
    try:
        conn, cursor = conectar_banco_dados()
        query = "SELECT nome_certo FROM apelidos WHERE apelido = %s AND tipo = 'subcategoria'"
        cursor.execute(query, (subcategoria,))
        resultado = cursor.fetchone()
        if resultado:
            return resultado[0]
        return subcategoria
    except Exception as e:
        print(f"Erro ao verificar apelido: {e}")
        return subcategoria
    finally:
        fechar_conexao(cursor, conn)
@cached(cache_longo)
def verificar_e_adicionar_card_especial(id_usuario, subcategoria):
    conn, cursor = conectar_banco_dados()
    try:
        # Verificar se a subcategoria está completa
        ids_faltantes = obter_ids_personagens_faltantes(id_usuario, subcategoria)
        print(f"IDs faltantes para {subcategoria}: {ids_faltantes}")  # Debug

        if not ids_faltantes:
            # Subcategoria completa, verificar se existe um card especial para ela
            query = "SELECT id_card, nome FROM cards_especiais WHERE subcategoria = %s"
            cursor.execute(query, (subcategoria,))
            card_especial = cursor.fetchone()

            if card_especial:
                id_card, nome_card = card_especial
                print(f"Card especial encontrado: {nome_card} para {subcategoria}")  # Debug

                # Verificar se o usuário já possui o card especial
                query_possui_card = """
                SELECT COUNT(*) FROM inventario_especial 
                WHERE id_usuario = %s AND id_card = %s
                """
                cursor.execute(query_possui_card, (id_usuario, id_card))
                possui_card = cursor.fetchone()[0]

                if not possui_card:
                    # Adicionar o card especial ao inventário do usuário
                    query_adicionar_card = "INSERT INTO inventario_especial (id_usuario, id_card) VALUES (%s, %s)"
                    cursor.execute(query_adicionar_card, (id_usuario, id_card))
                    conn.commit()
                    print(f"Card especial {nome_card} adicionado para o usuário {id_usuario}")  # Debug
                    return f"{nome_card}"
                else:
                    print(f"Usuário {id_usuario} já possui o card especial {nome_card}")  # Debug
                    return f"{nome_card}"  # Adicionar o nome do card mesmo que o usuário já o possua

        return None
    finally:
        fechar_conexao(cursor, conn)

@cached(cache_longo)
def encontrar_subcategoria_proxima(subcategoria):
    try:
        subcategoria = verificar_apelido(subcategoria)
        conn, cursor = conectar_banco_dados()
        query = "SELECT subcategoria FROM personagens WHERE subcategoria LIKE %s LIMIT 1"
        cursor.execute(query, (f"%{subcategoria}%",))
        resultado = cursor.fetchone()
        if resultado:
            return resultado[0]
        else:
            return None
    except Exception as e:
        print(f"Erro ao encontrar subcategoria mais próxima: {e}")
        return None
    finally:
        fechar_conexao(cursor, conn)
@cached(cache_longo)
def encontrar_categoria_proxima(categoria):
    try:
        categoria = verificar_apelido(categoria)
        conn, cursor = conectar_banco_dados()
        query = "SELECT categoria FROM personagens WHERE categoria LIKE %s LIMIT 1"
        cursor.execute(query, (f"%{categoria}%",))
        resultado = cursor.fetchone()
        if resultado:
            return resultado[0]
        else:
            return None
    except Exception as e:
        print(f"Erro ao encontrar categoria mais próxima: {e}")
        return None
    finally:
        fechar_conexao(cursor, conn)
@cached(cache_longo)
def consultar_informacoes_personagem_com_subcategoria(id_personagem):
    conn, cursor = conectar_banco_dados()
    try:
        query = "SELECT emoji, nome, subcategoria FROM personagens WHERE id_personagem = %s"
        cursor.execute(query, (id_personagem,))
        resultado = cursor.fetchone()
        if not resultado:
            query_evento = "SELECT emoji, nome, subcategoria FROM evento WHERE id_personagem = %s"
            cursor.execute(query_evento, (id_personagem,))
            resultado = cursor.fetchone()
        if not resultado:
            return "❓", "Desconhecido", "Desconhecida"
        return resultado[0], resultado[1], resultado[2]
    except Exception as e:
        print(f"Erro ao consultar informações do personagem: {e}")
        return "❓", "Desconhecido", "Desconhecida"
    finally:
        fechar_conexao(cursor, conn)

def obter_ids_personagens_inventario(id_usuario, subcategoria):
    subcategoria = verificar_apelido(subcategoria)
    conn, cursor = conectar_banco_dados()
    try:
        # Consulta para obter os personagens que o usuário possui na subcategoria especificada
        query = """
        SELECT inv.id_personagem
        FROM inventario inv
        JOIN personagens per ON inv.id_personagem = per.id_personagem
        WHERE inv.id_usuario = %s AND per.subcategoria = %s
        """
        cursor.execute(query, (id_usuario, subcategoria))
        ids_personagens = [row[0] for row in cursor.fetchall()]
        return ids_personagens
    finally:
        fechar_conexao(cursor, conn)


def obter_ids_personagens_faltantes(id_usuario, subcategoria):
    subcategoria = verificar_apelido(subcategoria)
    conn, cursor = conectar_banco_dados()
    try:
        # Consulta para obter os personagens que faltam para o usuário na subcategoria especificada
        query = """
        SELECT id_personagem
        FROM personagens 
        WHERE subcategoria = %s 
        AND id_personagem NOT IN (
            SELECT id_personagem
            FROM inventario 
            WHERE id_usuario = %s
        )
        """
        cursor.execute(query, (subcategoria, id_usuario))
        ids_personagens_faltantes = [row[0] for row in cursor.fetchall()]
        return ids_personagens_faltantes
    finally:
        fechar_conexao(cursor, conn)

@cached(cache_medio)
def obter_ids_personagens_faltantes_categoria(id_usuario, categoria):
    categoria = verificar_apelido(categoria)
    try:
        conn, cursor = conectar_banco_dados()
        query = """
        SELECT id_personagem 
        FROM personagens 
        WHERE categoria = %s AND id_personagem NOT IN (
            SELECT id_personagem 
            FROM inventario 
            WHERE id_usuario = %s
        )
        """
        cursor.execute(query, (categoria, id_usuario))
        ids_personagens = [row[0] for row in cursor.fetchall()]
        fechar_conexao(cursor, conn)
        return ids_personagens
    finally:
        fechar_conexao(cursor, conn)
@cached(cache_medio)
def obter_total_personagens_categoria(categoria):
    categoria = verificar_apelido(categoria)
    try:
        conn, cursor = conectar_banco_dados()
        query = "SELECT COUNT(*) FROM personagens WHERE categoria = %s"
        cursor.execute(query, (categoria,))
        total_personagens = cursor.fetchone()[0]
        return total_personagens
    finally:
        fechar_conexao(cursor, conn)
@cached(cache_medio)
def obter_total_personagens_subcategoria(subcategoria):
    subcategoria = verificar_apelido(subcategoria)
    conn, cursor = conectar_banco_dados()
    try:
        query = """
        SELECT COUNT(*)
        FROM personagens
        WHERE subcategoria = %s
        """
        cursor.execute(query, (subcategoria,))
        total_personagens = cursor.fetchone()[0]
        return total_personagens
    finally:
        fechar_conexao(cursor, conn)
        
@cached(ttl_cache)
def obter_ids_personagens_evento(id_usuario, subcategoria, incluir=True):
    subcategoria = verificar_apelido(subcategoria)
    conn, cursor = conectar_banco_dados()
    try:
        if incluir:
            query = """
            SELECT ev.id_personagem 
            FROM evento ev
            WHERE ev.subcategoria = %s 
            AND ev.id_personagem NOT IN (
                SELECT inv.id_personagem 
                FROM inventario inv
                WHERE inv.id_usuario = %s
            ) 
            """
        else:
            query = """
            SELECT ev.id_personagem 
            FROM evento ev
            WHERE ev.subcategoria = %s 
            AND ev.id_personagem IN (
                SELECT inv.id_personagem 
                FROM inventario inv
                WHERE inv.id_usuario = %s
            )
            """
        cursor.execute(query, (subcategoria, id_usuario))
        ids_personagens = [row[0] for row in cursor.fetchall()]
        return ids_personagens
        print(ids_personagens)
    finally:
        fechar_conexao(cursor, conn)

@cached(cache_longo)
def obter_ids_personagens_categoria(id_usuario, categoria):
    categoria = verificar_apelido(categoria)
    try:
        conn, cursor = conectar_banco_dados()
        cursor.execute("SELECT id_personagem FROM inventario WHERE id_usuario = %s AND id_personagem IN (SELECT id_personagem FROM personagens WHERE categoria = %s)", (id_usuario, categoria))
        ids_personagens = [row[0] for row in cursor.fetchall()]
        return ids_personagens
    finally:
        fechar_conexao(cursor, conn)

@cached(cache_longo)
def consultar_informacoes_personagem(id_personagem):
    conn, cursor = conectar_banco_dados()
    try:
        query = "SELECT emoji, nome FROM personagens WHERE id_personagem = %s"
        cursor.execute(query, (id_personagem,))
        resultado = cursor.fetchone()
        if not resultado:
            query_evento = "SELECT emoji, nome FROM evento WHERE id_personagem = %s"
            cursor.execute(query_evento, (id_personagem,))
            resultado = cursor.fetchone()
        if not resultado:
            return "❓", "Desconhecido"
        return resultado[0], resultado[1]
    except Exception as e:
        print(f"Erro ao consultar informações do personagem: {e}")
        return "❓", "Desconhecido"
    finally:
        fechar_conexao(cursor, conn)
        
 
def mostrar_pagina_cesta_s(message, subcategoria, id_usuario, pagina_atual, total_paginas, ids_personagens, total_personagens_subcategoria, nome_usuario, call=None):
    try:
        subcategoria = verificar_apelido(subcategoria)
        conn, cursor = conectar_banco_dados()

        # Verificar se há um card especial (diamante)
        card_especial = verificar_e_adicionar_card_especial(id_usuario, subcategoria)
        print(f"Resultado do card especial para {subcategoria}: {card_especial}")  # Debug

        if card_especial:
            # Se houver um card especial, usar a imagem e emojis personalizados
            cursor.execute("SELECT imagem FROM cards_especiais WHERE subcategoria = %s", (subcategoria,))
            resultado_imagem = cursor.fetchone()
            imagem_subcategoria = resultado_imagem[0] if resultado_imagem else None
            
            resposta = f"💎 | {card_especial}\n"
            resposta += f"📄 | {pagina_atual}/{total_paginas}\n"
            resposta += f"💵 | {len(ids_personagens)}/{total_personagens_subcategoria}\n\n"
        else:
            # Caso contrário, usar a imagem e emojis padrão
            cursor.execute("SELECT Imagem FROM subcategorias WHERE subcategoria = %s", (subcategoria,))
            resultado_imagem = cursor.fetchone()
            imagem_subcategoria = resultado_imagem[0] if resultado_imagem else None

            resposta = f"☀️ Peixes na cesta de {nome_usuario}! A recompensa de uma jornada dedicada à pesca.\n\n"
            resposta += f"🧺 | {subcategoria}\n"
            resposta += f"📄 | {pagina_atual}/{total_paginas}\n"
            resposta += f"🐟 | {len(ids_personagens)}/{total_personagens_subcategoria}\n\n"

        # Adicionar as informações dos personagens
        offset = (pagina_atual - 1) * 15
        ids_pagina = sorted(ids_personagens, key=lambda id: consultar_informacoes_personagem(id)[1])[offset:offset + 15]
        for id_personagem in ids_pagina:
            emoji, nome = consultar_informacoes_personagem(id_personagem)
            quantidade_cartas = obter_quantidade_cartas_usuario(id_usuario, id_personagem)
            resposta += f"{emoji} <code>{id_personagem}</code> • {nome} {adicionar_quantidade_cartas(quantidade_cartas)} \n"

        # Criar a navegação de páginas se necessário
        markup = None
        if total_paginas > 1:
            markup = criar_markup_cesta(pagina_atual, total_paginas, subcategoria, 's', id_usuario)

        # Enviar ou editar a mensagem com a imagem e a resposta
        if call:
            if imagem_subcategoria:
                bot.edit_message_media(media=telebot.types.InputMediaPhoto(imagem_subcategoria, caption=resposta, parse_mode="HTML"), chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
            else:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=resposta, reply_markup=markup, parse_mode="HTML")
        else:
            if imagem_subcategoria:
                bot.send_photo(message.chat.id, imagem_subcategoria, caption=resposta, reply_markup=markup, parse_mode="HTML")
            else:
                bot.send_message(message.chat.id, resposta, reply_markup=markup, parse_mode="HTML")

    except Exception as e:
        print(f"Erro ao mostrar página da cesta: {e}")
    finally:
        fechar_conexao(cursor, conn)

          
          
def mostrar_pagina_cesta_f(message, subcategoria, id_usuario, pagina_atual, total_paginas, ids_personagens_faltantes, total_personagens_subcategoria, nome_usuario, call=None):
    try:
        subcategoria = verificar_apelido(subcategoria)
        conn, cursor = conectar_banco_dados()

        cursor.execute("SELECT Imagem FROM subcategorias WHERE subcategoria = %s", (subcategoria,))
        resultado_imagem = cursor.fetchone()
        imagem_subcategoria = resultado_imagem[0] if resultado_imagem else None

        offset = (pagina_atual - 1) * 15
        ids_pagina = sorted(ids_personagens_faltantes, key=lambda id: consultar_informacoes_personagem(id)[1])[offset:offset + 15]

        resposta = f"🌧️ A cesta de {nome_usuario} não está completa, mas o rio ainda tem muitos segredos!\n\n"
        resposta += f"🧺 | {subcategoria}\n"
        resposta += f"📄 | {pagina_atual}/{total_paginas}\n"
        resposta += f"🐟 | {total_personagens_subcategoria - len(ids_personagens_faltantes)}/{total_personagens_subcategoria}\n\n"

        for id_personagem in ids_pagina:
            emoji, nome = consultar_informacoes_personagem(id_personagem)
            resposta += f"{emoji} <code>{id_personagem}</code> • {nome}\n"

        markup = None
        if total_paginas > 1:
            markup = criar_markup_cesta(pagina_atual, total_paginas, subcategoria, 'f', id_usuario)

        if call:
            if imagem_subcategoria:
                bot.edit_message_media(media=telebot.types.InputMediaPhoto(imagem_subcategoria, caption=resposta, parse_mode="HTML"), chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
            else:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=resposta, reply_markup=markup, parse_mode="HTML")
        else:
            if imagem_subcategoria:
                bot.send_photo(message.chat.id, imagem_subcategoria, caption=resposta, reply_markup=markup, parse_mode="HTML")
            else:
                bot.send_message(message.chat.id, resposta, reply_markup=markup, parse_mode="HTML")

    except Exception as e:
        print(f"Erro ao mostrar página da cesta: {e}")
    finally:
        fechar_conexao(cursor, conn)


def mostrar_pagina_cesta_c(message, categoria, id_usuario, pagina_atual, total_paginas, ids_personagens, total_personagens_categoria, nome_usuario, call=None):
    try:
        categoria = verificar_apelido(categoria)
        conn, cursor = conectar_banco_dados()

        # Ordenar os IDs dos personagens por subcategoria e nome do personagem
        ids_personagens.sort(key=lambda id: (consultar_informacoes_personagem_com_subcategoria(id)[2], consultar_informacoes_personagem_com_subcategoria(id)[1]))

        offset = (pagina_atual - 1) * 15
        ids_pagina = ids_personagens[offset:offset + 15]

        resposta = f"🌧️ A cesta de {nome_usuario} não está completa, mas o rio ainda tem muitos segredos!\n\n"
        resposta += f"🧺 | {categoria}\n"
        resposta += f"📄 | {pagina_atual}/{total_paginas}\n"
        resposta += f"🐟 | {len(ids_personagens)}/{total_personagens_categoria}\n\n"

        for id_personagem in ids_pagina:
            emoji, nome, subcategoria = consultar_informacoes_personagem_com_subcategoria(id_personagem)
            if int(id_personagem) < 9999:
                resposta += f"{emoji}<code>{id_personagem}</code> • {nome} - {subcategoria}\n"
            else:
                resposta += f"{emoji} <code>{id_personagem}</code> • {nome} - {subcategoria}\n"

        markup = None
        if total_paginas > 1:
            markup = criar_markup_cesta(pagina_atual, total_paginas, categoria, 'c', id_usuario)

        if call:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=resposta, reply_markup=markup, parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, resposta, reply_markup=markup, parse_mode="HTML")

    except Exception as e:
        print(f"Erro ao mostrar página da cesta: {e}")
    finally:
        fechar_conexao(cursor, conn)

def mostrar_pagina_cesta_cf(message, categoria, id_usuario, pagina_atual, total_paginas, ids_personagens, total_personagens_categoria, nome_usuario, call=None):
    try:
        categoria = verificar_apelido(categoria)
        conn, cursor = conectar_banco_dados()

        # Ordenar os IDs dos personagens por subcategoria e nome do personagem
        ids_personagens.sort(key=lambda id: (consultar_informacoes_personagem_com_subcategoria(id)[2], consultar_informacoes_personagem_com_subcategoria(id)[1]))

        offset = (pagina_atual - 1) * 15
        ids_pagina = ids_personagens[offset:offset + 15]

        resposta = f"🌧️ Peixes da espécie {categoria} que faltam na cesta de {nome_usuario}:\n\n"
        resposta += f"🧺 | {categoria}\n"
        resposta += f"📄 | {pagina_atual}/{total_paginas}\n"
        resposta += f"🐟 | {total_personagens_categoria - len(ids_personagens)}/{total_personagens_categoria}\n\n"

        for id_personagem in ids_pagina:
            emoji, nome, subcategoria = consultar_informacoes_personagem_com_subcategoria(id_personagem)
            if int(id_personagem) < 9999:
                resposta += f"{emoji}<code>{id_personagem}</code> • {nome} - {subcategoria}\n"
            else:
                resposta += f"{emoji}<code> {id_personagem}</code> • {nome} - {subcategoria}\n"

        markup = None
        if total_paginas > 1:
            markup = criar_markup_cesta(pagina_atual, total_paginas, categoria, 'cf', id_usuario)

        if call:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=resposta, reply_markup=markup, parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, resposta, reply_markup=markup, parse_mode="HTML")

    except Exception as e:
        print(f"Erro ao mostrar página da cesta: {e}")
    finally:
        fechar_conexao(cursor, conn)

def adicionar_quantidade_cartas(quantidade_carta):
    if isinstance(quantidade_carta, str):
        quantidade_carta = int(quantidade_carta)
    if quantidade_carta == 1:
        letra_quantidade = ""
    elif 2 <= quantidade_carta <= 4:
        letra_quantidade = "🌾"
    elif 5 <= quantidade_carta <= 9:
        letra_quantidade = "🌼"
    elif 10 <= quantidade_carta <= 19:
        letra_quantidade = "☀️"
    elif 20 <= quantidade_carta <= 29:
        letra_quantidade = "🍯️"
    elif 30 <= quantidade_carta <= 39:
        letra_quantidade = "🐝"
    elif 40 <= quantidade_carta <= 49:
        letra_quantidade = "🌻"
    elif 50 <= quantidade_carta <= 99:
        letra_quantidade = "👑"
    elif 100 <= quantidade_carta:
        letra_quantidade = "⭐️"
    else:
        letra_quantidade = ""
    return letra_quantidade

def obter_quantidade_cartas_usuario(id_usuario, id_personagem):
    try:
        conn, cursor = conectar_banco_dados()
        query = """
        SELECT quantidade 
        FROM inventario 
        WHERE id_usuario = %s AND id_personagem = %s
        """
        cursor.execute(query, (id_usuario, id_personagem))
        resultado = cursor.fetchone()
        if resultado:
            quantidade = resultado[0]
        else:
            quantidade = 0
    except Exception as e:
        print(f"Erro ao obter quantidade de cartas: {e}")
        quantidade = 0
    finally:
        fechar_conexao(cursor, conn)
    return quantidade
@cached(ttl_cache)
def obter_ids_personagens_inventario_sem_evento(id_usuario, subcategoria):
    subcategoria = verificar_apelido(subcategoria)
    conn, cursor = conectar_banco_dados()
    try:
        query = """
        SELECT inv.id_personagem
        FROM inventario inv
        JOIN personagens per ON inv.id_personagem = per.id_personagem
        WHERE inv.id_usuario = %s AND per.subcategoria = %s
        """
        cursor.execute(query, (id_usuario, subcategoria))
        ids_personagens = [row[0] for row in cursor.fetchall()]
        return ids_personagens
    finally:
        fechar_conexao(cursor, conn)

@cached(ttl_cache)
def obter_ids_personagens_inventario_com_evento(id_usuario, subcategoria):
    subcategoria = verificar_apelido(subcategoria)
    conn, cursor = conectar_banco_dados()
    try:
        query = """
        SELECT inv.id_personagem
        FROM inventario inv
        JOIN evento ev ON inv.id_personagem = ev.id_personagem
        WHERE inv.id_usuario = %s AND ev.subcategoria = %s
        """
        cursor.execute(query, (id_usuario, subcategoria))
        ids_personagens = [row[0] for row in cursor.fetchall()]
        return ids_personagens
    finally:
        fechar_conexao(cursor, conn)

@cached(ttl_cache)
def obter_ids_personagens_faltantes_sem_evento(id_usuario, subcategoria):
    subcategoria = verificar_apelido(subcategoria)
    conn, cursor = conectar_banco_dados()
    try:
        query = """
        SELECT per.id_personagem
        FROM personagens per
        WHERE per.subcategoria = %s AND per.id_personagem NOT IN (
            SELECT inv.id_personagem
            FROM inventario inv
            WHERE inv.id_usuario = %s
        )
        """
        cursor.execute(query, (subcategoria, id_usuario))
        ids_personagens_faltantes = [row[0] for row in cursor.fetchall()]
        return ids_personagens_faltantes
    finally:
        fechar_conexao(cursor, conn)

@cached(ttl_cache)
def obter_ids_personagens_faltantes_com_evento(id_usuario, subcategoria):
    subcategoria = verificar_apelido(subcategoria)
    conn, cursor = conectar_banco_dados()
    try:
        query = """
        SELECT ev.id_personagem
        FROM evento ev
        WHERE ev.subcategoria = %s AND ev.id_personagem NOT IN (
            SELECT inv.id_personagem
            FROM inventario inv
            WHERE inv.id_usuario = %s
        )
        """
        cursor.execute(query, (subcategoria, id_usuario))
        ids_personagens_faltantes = [row[0] for row in cursor.fetchall()]
        return ids_personagens_faltantes
    finally:
        fechar_conexao(cursor, conn)

global processing_lock

def handle_callback_query_cesta(call):
    if not processing_lock.acquire(blocking=False):
        return
    try:
        parts = call.data.split('_')
        tipo = parts[1]
        pagina = int(parts[2])
        categoria = parts[3]
        id_usuario_original = int(parts[4])
        nome_usuario = bot.get_chat(id_usuario_original).first_name

        if tipo == 's':
            ids_personagens = obter_ids_personagens_inventario_sem_evento(id_usuario_original, categoria)
            total_personagens_subcategoria = obter_total_personagens_subcategoria(categoria)
            total_registros = len(ids_personagens)

            if total_registros > 0:
                total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)
                mostrar_pagina_cesta_s(call.message, categoria, id_usuario_original, pagina, total_paginas, ids_personagens, total_personagens_subcategoria, nome_usuario, call=call)
            else:
                bot.reply_to(call.message, f"Nenhum personagem encontrado na cesta '{categoria}'.")

        elif tipo == 'f':
            ids_personagens_faltantes = obter_ids_personagens_faltantes_sem_evento(id_usuario_original, categoria)
            total_personagens_subcategoria = obter_total_personagens_subcategoria(categoria)
            total_registros = len(ids_personagens_faltantes)

            if total_registros > 0:
                total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)
                mostrar_pagina_cesta_f(call.message, categoria, id_usuario_original, pagina, total_paginas, ids_personagens_faltantes, total_personagens_subcategoria, nome_usuario, call=call)
            else:
                bot.reply_to(call.message, f"Todos os personagens na subcategoria '{categoria}' estão no seu inventário.")

        elif tipo == 'se':
            ids_personagens = obter_ids_personagens_inventario_com_evento(id_usuario_original, categoria)
            total_personagens_com_evento = obter_total_personagens_subcategoria(categoria)
            total_registros = len(ids_personagens)

            if total_registros > 0:
                total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)
                mostrar_pagina_cesta_s(call.message, categoria, id_usuario_original, pagina, total_paginas, ids_personagens, total_personagens_com_evento, nome_usuario, call=call)
            else:
                bot.reply_to(call.message, f"Nenhum personagem encontrado na cesta '{categoria}'.")

        elif tipo == 'fe':
            ids_personagens_faltantes = obter_ids_personagens_faltantes_com_evento(id_usuario_original, categoria)
            total_personagens_subcategoria = obter_total_personagens_subcategoria(categoria)
            total_registros = len(ids_personagens_faltantes)

            if total_registros > 0:
                total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)
                mostrar_pagina_cesta_f(call.message, categoria, id_usuario_original, pagina, total_paginas, ids_personagens_faltantes, total_personagens_subcategoria, nome_usuario, call=call)
            else:
                bot.reply_to(call.message, f"Todos os personagens na subcategoria '{categoria}' estão no seu inventário.")

        elif tipo == 'c':
            ids_personagens = obter_ids_personagens_categoria(id_usuario_original, categoria)
            total_personagens_categoria = obter_total_personagens_categoria(categoria)
            total_registros = len(ids_personagens)

            if total_registros > 0:
                total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)
                mostrar_pagina_cesta_c(call.message, categoria, id_usuario_original, pagina, total_paginas, ids_personagens, total_personagens_categoria, nome_usuario, call=call)
            else:
                bot.reply_to(call.message, f"Nenhum personagem encontrado na categoria '{categoria}'.")

        elif tipo == 'cf':
            ids_personagens_faltantes = obter_ids_personagens_faltantes_categoria(id_usuario_original, categoria)
            total_personagens_categoria = obter_total_personagens_categoria(categoria)
            total_registros = len(ids_personagens_faltantes)

            if total_registros > 0:
                total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)
                mostrar_pagina_cesta_cf(call.message, categoria, id_usuario_original, pagina, total_paginas, ids_personagens_faltantes, total_personagens_categoria, nome_usuario, call=call)
            else:
                bot.reply_to(call.message, f"Você possui todos os personagens na categoria '{categoria}'.")

    except Exception as e:
        print(f"Erro ao processar callback da cesta: {e}")
    finally:
        processing_lock.release()

def processar_cesta(message):
    try:
        parts = message.text.split(' ', 2)
        if len(parts) < 3:
            bot.reply_to(message, "Por favor, forneça o tipo ('s', 'f', 'c', 'se', 'fe' ou 'cf') e a subcategoria após o comando, por exemplo: /cesta s bts")
            return

        tipo = parts[1].strip()
        subcategoria = parts[2].strip()

        id_usuario = message.from_user.id
        nome_usuario = message.from_user.first_name
        apagar_cartas_quantidade_zero_ou_negativa()

        if tipo in ['s', 'se']:
            subcategoria_proxima = encontrar_subcategoria_proxima(subcategoria)
            if not subcategoria_proxima:
                bot.reply_to(message, "Espécie não identificada. Você digitou certo? 🤭")
                return

            ids_personagens = obter_ids_personagens_inventario(id_usuario, subcategoria_proxima)
            if 'e' in tipo:
                ids_personagens += obter_ids_personagens_evento(id_usuario, subcategoria_proxima, incluir=False)
            total_personagens_subcategoria = obter_total_personagens_subcategoria(subcategoria_proxima)
            total_registros = len(ids_personagens)

            if total_registros > 0:
                total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)
                mostrar_pagina_cesta_s(message, subcategoria_proxima, id_usuario, 1, total_paginas, ids_personagens, total_personagens_subcategoria, nome_usuario)
            else:
                bot.reply_to(message, f"🌧️ Sem peixes de {subcategoria_proxima} na cesta... a jornada continua.")

        elif tipo in ['f', 'fe']:
            subcategoria_proxima = encontrar_subcategoria_proxima(subcategoria)
            if not subcategoria_proxima:
                bot.reply_to(message, "Espécie não identificada. Você digitou certo? 🤭")
                return

            ids_personagens_faltantes = obter_ids_personagens_faltantes(id_usuario, subcategoria_proxima)
            if 'e' in tipo:
                ids_personagens_faltantes += obter_ids_personagens_evento(id_usuario, subcategoria_proxima, incluir=True)
            total_personagens_subcategoria = obter_total_personagens_subcategoria(subcategoria_proxima)
            total_registros = len(ids_personagens_faltantes)

            if total_registros > 0:
                total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)
                mostrar_pagina_cesta_f(message, subcategoria_proxima, id_usuario, 1, total_paginas, ids_personagens_faltantes, total_personagens_subcategoria, nome_usuario)
            else:
                bot.reply_to(message, f"☀️ Nada como a alegria de ter todos os peixes de {subcategoria_proxima} na cesta!")

        elif tipo == 'c':
            subcategoria_proxima = encontrar_categoria_proxima(subcategoria)
            if not subcategoria_proxima:
                bot.reply_to(message, "Espécie não identificada. Você digitou certo? 🤭")
                return

            ids_personagens = obter_ids_personagens_categoria(id_usuario, subcategoria_proxima)
            total_personagens_categoria = obter_total_personagens_categoria(subcategoria_proxima)
            total_registros = len(ids_personagens)

            if total_registros > 0:
                total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)
                mostrar_pagina_cesta_c(message, subcategoria_proxima, id_usuario, 1, total_paginas, ids_personagens, total_personagens_categoria, nome_usuario)
            else:
                bot.reply_to(message, f"🌧️ Sem peixes de {subcategoria_proxima} na cesta... a jornada continua.")

        elif tipo == 'cf':
            subcategoria_proxima = encontrar_categoria_proxima(subcategoria)
            if not subcategoria_proxima:
                bot.reply_to(message, "Espécie não identificada. Você digitou certo? 🤭")
                return

            ids_personagens_faltantes = obter_ids_personagens_faltantes_categoria(id_usuario, subcategoria_proxima)
            total_personagens_categoria = obter_total_personagens_categoria(subcategoria_proxima)
            total_registros = len(ids_personagens_faltantes)

            if total_registros > 0:
                total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)
                mostrar_pagina_cesta_cf(message, subcategoria_proxima, id_usuario, 1, total_paginas, ids_personagens_faltantes, total_personagens_categoria, nome_usuario)
            else:
                bot.reply_to(message, f"☀️ Nada como a alegria de ter todos os peixes de {subcategoria_proxima} na cesta!")

        else:
            bot.reply_to(message, "Tipo inválido. Use 's' para os personagens que você possui, 'f' para os que você não possui, 'c' para uma categoria completa ou 'cf' para faltantes na categoria.")

    except IndexError:
        bot.reply_to(message, "Por favor, forneça o tipo ('s', 'f', 'c', 'se', 'fe' ou 'cf') e a subcategoria desejada após o comando, por exemplo: /cesta s bts")

    except Exception as e:
        print(f"Erro ao processar comando /cesta: {e}")
def criar_markup_cesta(pagina_atual, total_paginas, categoria, tipo, id_usuario):
    markup = types.InlineKeyboardMarkup(row_width=4)

    # Criar botões de navegação com callback_data
    btn_inicio = types.InlineKeyboardButton("⏪️", callback_data=f"cesta_{tipo}_1_{categoria}_{id_usuario}")
    btn_anterior = types.InlineKeyboardButton("⬅️", callback_data=f"cesta_{tipo}_{max(1, pagina_atual - 1)}_{categoria}_{id_usuario}")
    btn_proxima = types.InlineKeyboardButton("➡️", callback_data=f"cesta_{tipo}_{min(total_paginas, pagina_atual + 1)}_{categoria}_{id_usuario}")
    btn_final = types.InlineKeyboardButton("⏩️", callback_data=f"cesta_{tipo}_{total_paginas}_{categoria}_{id_usuario}")

    # Adicionar todos os botões em uma linha, sempre visíveis
    markup.add(btn_inicio, btn_anterior, btn_proxima, btn_final)

    return markup



def apagar_cartas_quantidade_zero_ou_negativa():
    conn, cursor = conectar_banco_dados()

    try:
        query = "DELETE FROM inventario WHERE quantidade <= 0"
        cursor.execute(query)
        conn.commit()
        print(f"{cursor.rowcount} cartas deletadas.")
    except mysql.connector.Error as err:
        print(f"Erro: {err}")
    finally:
        cursor.close()
        conn.close()
