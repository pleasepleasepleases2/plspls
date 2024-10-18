from pesquisas import *
from user import *
from bd import *
from loja import *
from gnome import *
from operacoes import *
import globals
import mysql.connector
import traceback
import telebot
import newrelic.agent

def handle_callback_paginacao_armazem(call):
    try:
        conn, cursor = conectar_banco_dados()
        chat_id = call.message.chat.id
        _, direcao, pagina_str, id_usuario = call.data.split('_')
        pagina = int(pagina_str)
        info_armazem = globals.armazem_info.get(int(id_usuario), {})
        id_usuario = info_armazem.get('id_usuario', '')
        usuario = info_armazem.get('usuario', '')
        resultados_por_pagina = 15
        offset = (pagina - 1) * resultados_por_pagina

        quantidade_total_cartas = obter_quantidade_total_cartas(id_usuario)
        total_paginas = (quantidade_total_cartas + resultados_por_pagina - 1) // resultados_por_pagina

        if pagina == 1 and call.data.startswith("armazem_anterior_"):
            pagina = total_paginas
            offset = (pagina - 1) * resultados_por_pagina

        elif pagina == total_paginas and call.data.startswith("armazem_proxima_"):
            pagina = 1
            offset = 0

        else:
            if call.data.startswith("armazem_anterior_"):
                pagina -= 1
            elif call.data.startswith("armazem_ultima_"):
                pagina += 5 
            elif call.data.startswith("armazem_primeira_"):
                pagina -= 5
            elif call.data.startswith("armazem_proxima_"):
                pagina += 1
            offset = (pagina - 1) * resultados_por_pagina

        sql = f"""
            SELECT id_personagem, 
                   emoji COLLATE utf8mb4_general_ci AS emoji, 
                   nome_personagem COLLATE utf8mb4_general_ci AS nome_personagem, 
                   subcategoria COLLATE utf8mb4_general_ci AS subcategoria, 
                   quantidade, 
                   categoria COLLATE utf8mb4_general_ci AS categoria, 
                   evento COLLATE utf8mb4_general_ci AS evento
            FROM (
                SELECT i.id_personagem, p.emoji COLLATE utf8mb4_general_ci AS emoji, p.nome COLLATE utf8mb4_general_ci AS nome_personagem, p.subcategoria COLLATE utf8mb4_general_ci AS subcategoria, i.quantidade, p.categoria COLLATE utf8mb4_general_ci AS categoria, '' COLLATE utf8mb4_general_ci AS evento
                FROM inventario i
                JOIN personagens p ON i.id_personagem = p.id_personagem
                WHERE i.id_usuario = {id_usuario} AND i.quantidade > 0

                UNION ALL

                SELECT e.id_personagem, e.emoji COLLATE utf8mb4_general_ci AS emoji, e.nome COLLATE utf8mb4_general_ci AS nome_personagem, e.subcategoria COLLATE utf8mb4_general_ci AS subcategoria, 0 AS quantidade, e.categoria COLLATE utf8mb4_general_ci AS categoria, e.evento COLLATE utf8mb4_general_ci AS evento
                FROM evento e
                WHERE e.id_personagem IN (
                    SELECT id_personagem
                    FROM inventario
                    WHERE id_usuario = {id_usuario} AND quantidade > 0
                )
            ) AS combined
            ORDER BY 
                CASE WHEN categoria = 'evento' THEN 0 ELSE 1 END, 
                categoria, 
                CAST(id_personagem AS UNSIGNED) ASC
            LIMIT {resultados_por_pagina} OFFSET {offset}
        """
        cursor.execute(sql)
        resultados = cursor.fetchall()
        if resultados:
            markup = telebot.types.InlineKeyboardMarkup()
            if quantidade_total_cartas > 10:
                buttons_row = [
                    telebot.types.InlineKeyboardButton("⏪️", callback_data=f"armazem_primeira_{pagina}_{id_usuario}"),
                    telebot.types.InlineKeyboardButton("◀️", callback_data=f"armazem_anterior_{pagina}_{id_usuario}"),
                    telebot.types.InlineKeyboardButton("▶️", callback_data=f"armazem_proxima_{pagina}_{id_usuario}"),
                    telebot.types.InlineKeyboardButton("⏩️", callback_data=f"armazem_ultima_{pagina}_{id_usuario}")
                ]
                markup.row(*buttons_row)

            id_fav_usuario, emoji_fav, nome_fav, subcategoria_fav, imagem_fav = obter_favorito(id_usuario)

            resposta = f"💌 | Cartas no armazém de {usuario}:\n\n🩷 ∙ {id_fav_usuario} — {nome_fav} de {subcategoria_fav}\n\n" if id_fav_usuario is not None else f"💌 | Cartas no armazém de {usuario}:\n\n"

            for carta in resultados:
                id_carta, emoji_carta, nome_carta, subcategoria_carta, quantidade_carta, categoria_carta, evento_carta = carta

                quantidade_carta = int(quantidade_carta) if quantidade_carta is not None else 0

                if categoria_carta == 'evento' and (int(id_carta) < 10000 and int(id_carta) != 102):
                    emoji_carta = obter_emoji_evento(evento_carta)
                    repetida = "" if quantidade_carta > 1 else ""
                    letra_quantidade = ""
                else:
                    letra_quantidade = (
                        "🌾" if 2 <= quantidade_carta <= 4 else
                        "🌼" if 5 <= quantidade_carta <= 9 else
                        "☀️" if 10 <= quantidade_carta <= 19 else
                        "🍯️" if 20 <= quantidade_carta <= 29 else
                        "🐝" if 30 <= quantidade_carta <= 39 else
                        "🌻" if 40 <= quantidade_carta <= 49 else
                        "👑" if 50 <= quantidade_carta <= 101 else
                        "" 
                    )
                    repetida = "" if quantidade_carta > 1 else ""

                resposta += f" {emoji_carta} <code>{id_carta}</code> • {nome_carta} - {subcategoria_carta} {letra_quantidade}{repetida}\n"

            resposta += f"\n{pagina}/{total_paginas}"
            bot.edit_message_caption(chat_id=chat_id, message_id=call.message.message_id, caption=resposta, reply_markup=markup, parse_mode="HTML")

        else:
            bot.answer_callback_query(callback_query_id=call.id, text="Nenhuma carta encontrada.")
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        fechar_conexao(cursor, conn)
