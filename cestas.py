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

def criar_markup_cesta(pagina_atual, total_paginas, subcategoria, tipo, id_usuario_original):
    markup = telebot.types.InlineKeyboardMarkup()

    # Navegação circular
    pagina_anterior = total_paginas if pagina_atual == 1 else pagina_atual - 1
    pagina_proxima = 1 if pagina_atual == total_paginas else pagina_atual + 1

    # Botões de navegação na mesma linha
    markup.row(
        telebot.types.InlineKeyboardButton(text="⏪️", callback_data=f"cesta_{tipo}_1_{subcategoria}_{id_usuario_original}"),
        telebot.types.InlineKeyboardButton(text="⬅️", callback_data=f"cesta_{tipo}_{pagina_anterior}_{subcategoria}_{id_usuario_original}"),
        telebot.types.InlineKeyboardButton(text="➡️", callback_data=f"cesta_{tipo}_{pagina_proxima}_{subcategoria}_{id_usuario_original}"),
        telebot.types.InlineKeyboardButton(text="⏩️", callback_data=f"cesta_{tipo}_{total_paginas}_{subcategoria}_{id_usuario_original}")
    )

    return markup

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
