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


def criar_lista_paginas(personagens_ids_quantidade, items_por_pagina):
    paginas = []
    pagina_atual = []
    for i, (personagem_id, quantidade) in enumerate(personagens_ids_quantidade.items(), start=1):
        personagem = get_personagem_by_id(personagem_id)
        if personagem:
            emoji = personagem['emoji']
            card_id = personagem['id']
            name = personagem['nome']
            if quantidade > 1:
                item = f"{emoji} <code>{card_id}</code>. <b>{name}</b> ({int(quantidade)}x)"
            else:
                item = f"{emoji} <code>{card_id}</code>. <b>{name}</b>"
            pagina_atual.append(item)

            if len(pagina_atual) == items_por_pagina or i == len(personagens_ids_quantidade):
                paginas.append(pagina_atual)
                pagina_atual = []

    return paginas

def editar_mensagem_tag(message, nometag, pagina_atual, id_usuario, total_paginas):
    try:
        conn, cursor = conectar_banco_dados()
        offset = (pagina_atual - 1) * 15
        query = "SELECT id_personagem FROM tags WHERE nometag = %s LIMIT 15 OFFSET %s"
        cursor.execute(query, (nometag, offset))
        resultados = cursor.fetchall()

        if resultados:
            resposta = f"🔖| Cartas na tag {nometag}:\n\n"
            for resultado in resultados:
                id_personagem = resultado[0]
                
                cursor.execute("SELECT emoji, nome,subcategoria FROM personagens WHERE id_personagem = %s", (id_personagem,))
                carta_info_personagens = cursor.fetchone()

                cursor.execute("SELECT emoji, nome,subcategoria FROM evento WHERE id_personagem = %s", (id_personagem,))
                carta_info_evento = cursor.fetchone()

                if carta_info_personagens:
                    emoji, nome,subcategoria = carta_info_personagens
                elif carta_info_evento:
                    emoji, nome,subcategoria = carta_info_evento
                else:
                    resposta += f"ℹ️ | Carta não encontrada para ID: {id_personagem}\n"
                    continue

                emoji_status = '☀️' if inventario_existe(id_usuario, id_personagem) else '🌧️'
                resposta += f"{emoji_status} | {emoji} ⭑<code> {id_personagem}</code> - {nome} de {subcategoria}\n"

            markup = None
            if int(total_paginas) > 1:
                markup = criar_markup_tag(pagina_atual, total_paginas, nometag)
            resposta += f"\nPágina {pagina_atual}/{total_paginas}"
            bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=resposta, reply_markup=markup, parse_mode="HTML")
        else:
            bot.reply_to(message, f"Nenhum registro encontrado para a tag '{nometag}'.")

    except Exception as e:
        print(f"Erro ao editar mensagem de tag: {e}")
        bot.reply_to(message, "Ocorreu um erro ao processar sua solicitação.")

def criar_markup_tag(pagina_atual, total_paginas, nometag):
    markup = telebot.types.InlineKeyboardMarkup()
    btn_anterior = telebot.types.InlineKeyboardButton("⬅️", callback_data=f"tag_{pagina_atual-1}_{nometag}_{total_paginas}")
    btn_proxima = telebot.types.InlineKeyboardButton("➡️", callback_data=f"tag_{pagina_atual+1}_{nometag}_{total_paginas}")
    markup.row(btn_anterior, btn_proxima)

    return markup

def mostrar_primeira_pagina_tag(message, nometag, id_usuario):
    try:
        conn, cursor = conectar_banco_dados()
        query_total = "SELECT COUNT(id_personagem) FROM tags WHERE nometag = %s AND id_usuario = %s"
        cursor.execute(query_total, (nometag, id_usuario))
        total_registros = cursor.fetchone()[0]

        total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)

        if total_registros == 0:
            bot.reply_to(message, f"Nenhum registro encontrado para a tag '{nometag}'.")
            return

        query = "SELECT id_personagem FROM tags WHERE nometag = %s AND id_usuario = %s LIMIT 15"
        cursor.execute(query, (nometag, id_usuario))
        resultados = cursor.fetchall()

        if resultados:
            resposta = f"🔖| Cartas na tag {nometag}:\n\n"
            for resultado in resultados:
                id_personagem = resultado[0]
                
                cursor.execute("SELECT emoji, nome,subcategoria FROM personagens WHERE id_personagem = %s", (id_personagem,))
                carta_info_personagens = cursor.fetchone()

                cursor.execute("SELECT emoji, nome,subcategoria FROM evento WHERE id_personagem = %s", (id_personagem,))
                carta_info_evento = cursor.fetchone()

                if carta_info_personagens:
                    emoji, nome,subcategoria = carta_info_personagens
                elif carta_info_evento:
                    emoji, nome,subcategoria = carta_info_evento
                else:
                    resposta += f"ℹ️ | Carta não encontrada para ID: {id_personagem}\n"
                    continue

                emoji_status = '☀️' if inventario_existe(id_usuario, id_personagem) else '🌧️'

                resposta += f"{emoji_status} | {emoji} ⭑<code> {id_personagem}</code> - {nome} de {subcategoria}\n"

            markup = None
            if total_paginas > 1:
                markup = criar_markup_tag(1, total_paginas, nometag)
            resposta += f"\nPágina 1/{total_paginas}"
            bot.send_message(message.chat.id, resposta, reply_markup=markup, parse_mode="HTML")
        else:
            bot.reply_to(message, f"Nenhum registro encontrado para a tag '{nometag}'.")

    except Exception as e:
        print(f"Erro ao processar comando /tag: {e}")
        bot.reply_to(message, "Ocorreu um erro ao processar sua solicitação.")

# Função para lidar com o comando /tag
def verificar_comando_tag(message):
    try:
        parametros = message.text.split(' ', 1)[1:] 

        if not parametros:
            conn, cursor = conectar_banco_dados()
            id_usuario = message.from_user.id
            cursor.execute("SELECT DISTINCT nometag FROM tags WHERE id_usuario = %s", (id_usuario,))
            tags = cursor.fetchall()
            if tags:
                resposta = "🔖| Suas tags:\n\n"
                for tag in tags:
                    resposta += f"• {tag[0]}\n"
                bot.reply_to(message, resposta)
            else:
                bot.reply_to(message, "Você não possui nenhuma tag.")
            fechar_conexao(cursor, conn)
            return

        # Se uma tag foi fornecida, mostrar a primeira página da tag
        nometag = parametros[0] 
        id_usuario = message.from_user.id
        mostrar_primeira_pagina_tag(message, nometag, id_usuario)

    except Exception as e:
        print(f"Erro ao processar comando /tag: {e}")

# Função para adicionar tags com o comando /addtag
def adicionar_tag(message):
    try:
        conn, cursor = conectar_banco_dados()
        id_usuario = message.from_user.id
        args = message.text.split(maxsplit=1)
        
        if len(args) == 2:
            tag_info = args[1]
            tag_parts = tag_info.split('|')
            
            if len(tag_parts) == 2:
                ids_personagens_str = tag_parts[0].strip()
                nometag = tag_parts[1].strip()
                
                if ids_personagens_str and nometag:
                    ids_personagens = [id_personagem.strip() for id_personagem in ids_personagens_str.split(',')]
                    
                    for id_personagem in ids_personagens:
                        cursor.execute(
                            "INSERT INTO tags (id_usuario, id_personagem, nometag) VALUES (%s, %s, %s)", 
                            (id_usuario, id_personagem, nometag)
                        )
                    
                    conn.commit()
                    bot.reply_to(message, f"Tag '{nometag}' adicionada com sucesso.")
                else:
                    bot.reply_to(message, "Formato incorreto. Use /addtag id1,id2,... | nometag")
            else:
                bot.reply_to(message, "Formato incorreto. Use /addtag id1,id2,... | nometag")
        else:
            bot.reply_to(message, "Formato incorreto. Use /addtag id1,id2,... | nometag")
    
    except mysql.connector.Error as err:
        print(f"Erro de MySQL: {err}")
        bot.reply_to(message, "Ocorreu um erro ao processar a operação no banco de dados.")
    
    except Exception as e:
        print(f"Erro ao adicionar tag: {e}")
        bot.reply_to(message, "Ocorreu um erro ao processar a operação.")
    
    finally:
        fechar_conexao(cursor, conn)
