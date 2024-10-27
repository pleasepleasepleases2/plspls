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
        
        # Calcular o offset com base na página atual
        offset = (pagina_atual - 1) * 15
        
        # Ajuste da consulta SQL para paginação usando LIMIT e OFFSET corretamente
        query = "SELECT id_personagem FROM tags WHERE nometag = %s AND id_usuario = %s LIMIT 15 OFFSET %s"
        cursor.execute(query, (nometag, id_usuario, offset))
        resultados = cursor.fetchall()

        if resultados:
            resposta = f"🔖| Cartas na tag <b>{nometag}</b>:\n\n"
            for resultado in resultados:
                id_personagem = resultado[0]
                
                # Consultar informações da carta em `personagens` ou `evento`
                cursor.execute("SELECT emoji, nome, subcategoria FROM personagens WHERE id_personagem = %s", (id_personagem,))
                carta_info = cursor.fetchone() or cursor.execute("SELECT emoji, nome, subcategoria FROM evento WHERE id_personagem = %s", (id_personagem,)) or cursor.fetchone()
                
                # Processar informações e verificar se está no inventário
                if carta_info:
                    emoji, nome, subcategoria = carta_info
                    emoji_status = '☀️' if inventario_existe(id_usuario, id_personagem) else '🌧️'
                    resposta += f"{emoji_status} | {emoji} ⭑<code>{id_personagem}</code> - {nome} de {subcategoria}\n"
                else:
                    resposta += f"ℹ️ | Carta não encontrada para ID: {id_personagem}\n"

            # Criar a navegação se houver mais de uma página
            markup = criar_markup_tag(pagina_atual, total_paginas, nometag) if total_paginas > 1 else None
            resposta += f"\nPágina {pagina_atual}/{total_paginas}"

            # Editar a mensagem existente com o conteúdo atualizado da página
            bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=resposta, reply_markup=markup, parse_mode="HTML")
        else:
            bot.reply_to(message, f"Nenhum registro encontrado para a tag '{nometag}'.")

    except Exception as e:
        print(f"Erro ao editar mensagem de tag: {e}")
        bot.reply_to(message, "Ocorreu um erro ao processar sua solicitação.")
    finally:
        fechar_conexao(cursor, conn)

def mostrar_primeira_pagina_tag(message, nometag, id_usuario):
    try:
        conn, cursor = conectar_banco_dados()
        
        # Obter o número total de registros para a tag do usuário
        query_total = "SELECT COUNT(id_personagem) FROM tags WHERE nometag = %s AND id_usuario = %s"
        cursor.execute(query_total, (nometag, id_usuario))
        total_registros = cursor.fetchone()[0]
        
        # Definir o número de páginas
        total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)
        pagina_atual = 1  # Inicializar a primeira página

        # Verificar se não há registros
        if total_registros == 0:
            bot.reply_to(message, f"<i>Você não possui uma tag com o nome '{nometag}'.</i> \nDeseja criar? Use o comando <code>/addtag id | {nometag}</code>.", parse_mode="HTML")
            return

        # Obter os personagens da tag na primeira página
        query = "SELECT id_personagem FROM tags WHERE nometag = %s AND id_usuario = %s LIMIT 15"
        cursor.execute(query, (nometag, id_usuario))
        resultados = cursor.fetchall()

        # Construir a resposta com os resultados
        if resultados:
            resposta = f"🔖| Cartas na tag <b>{nometag}</b>:\n\n"
            for resultado in resultados:
                id_personagem = resultado[0]
                
                # Consultar informações da carta em `personagens` ou `evento`
                cursor.execute("SELECT emoji, nome, subcategoria FROM personagens WHERE id_personagem = %s", (id_personagem,))
                carta_info = cursor.fetchone() or cursor.execute("SELECT emoji, nome, subcategoria FROM evento WHERE id_personagem = %s", (id_personagem,)) or cursor.fetchone()
                
                # Processar informações e verificar se está no inventário
                if carta_info:
                    emoji, nome, subcategoria = carta_info
                    emoji_status = '☀️' if inventario_existe(id_usuario, id_personagem) else '🌧️'
                    resposta += f"{emoji_status} | {emoji} ⭑<code>{id_personagem}</code> - {nome} de {subcategoria}\n"
                else:
                    resposta += f"ℹ️ | Carta não encontrada para ID: {id_personagem}\n"

            # Criar a navegação se houver mais de uma página
            markup = criar_markup_tag(pagina_atual, total_paginas, nometag) if total_paginas > 1 else None
            resposta += f"\nPágina {pagina_atual}/{total_paginas}"

            # Enviar a primeira página da tag (não tenta editar)
            bot.send_message(chat_id=message.chat.id, text=resposta, reply_markup=markup, parse_mode="HTML")

    except Exception as e:
        print(f"Erro ao processar comando /tag: {e}")
        bot.reply_to(message, "Ocorreu um erro ao processar sua solicitação.")
    finally:
        fechar_conexao(cursor, conn)


# Função para lidar com o comando /tag
def verificar_comando_tag(message):
    try:
        parametros = message.text.split(' ', 1)[1:]
        conn, cursor = conectar_banco_dados()
        id_usuario = message.from_user.id
        nome_usuario = message.from_user.first_name
        # Obter todas as tags do usuário, em ordem alfabética
        cursor.execute("SELECT DISTINCT nometag FROM tags WHERE id_usuario = %s ORDER BY nometag ASC", (id_usuario,))
        tags = cursor.fetchall()
        
        if not parametros:  # Exibir todas as tags com numeração
            if tags:
                resposta = f"<b>🔖 | Tags de {nome_usuario}:\n\n</b>"
                for i, tag in enumerate(tags, start=1):
                    resposta += f"<i>{i} — {tag[0]}\n</i>"
                bot.reply_to(message, resposta,parse_mode="HTML")
            else:
                bot.reply_to(message, "Você não possui nenhuma tag.")
            fechar_conexao(cursor, conn)
            return

        # Determinar se o parâmetro fornecido é um número (índice da tag) ou o nome da tag
        nometag = parametros[0].strip()
        
        # Verificar se o parâmetro é um número para obter a tag correspondente
        if nometag.isdigit():
            index = int(nometag) - 1
            if 0 <= index < len(tags):
                nometag = tags[index][0]  # Nome da tag correspondente ao índice
            else:
                bot.reply_to(message, "Número de tag inválido. Verifique a lista de tags e tente novamente.")
                fechar_conexao(cursor, conn)
                return
        
        # Mostrar a primeira página da tag com o nome identificado (por índice ou nome direto)
        mostrar_primeira_pagina_tag(message, nometag, id_usuario)

    except Exception as e:
        print(f"Erro ao processar comando /tag: {e}")
        bot.reply_to(message, "Ocorreu um erro ao processar sua solicitação.")
    finally:
        fechar_conexao(cursor, conn)


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
        
def criar_markup_tag(pagina_atual, total_paginas, nometag):
    markup = telebot.types.InlineKeyboardMarkup()
    btn_primeiro = telebot.types.InlineKeyboardButton("⏪", callback_data=f"tag_1_{nometag}_{total_paginas}")
    btn_anterior = telebot.types.InlineKeyboardButton("⬅️", callback_data=f"tag_{pagina_atual-1}_{nometag}_{total_paginas}")
    btn_proxima = telebot.types.InlineKeyboardButton("➡️", callback_data=f"tag_{pagina_atual+1}_{nometag}_{total_paginas}")
    btn_ultimo = telebot.types.InlineKeyboardButton("⏩", callback_data=f"tag_{total_paginas}_{nometag}_{total_paginas}")
    markup.row(btn_primeiro,btn_anterior, btn_proxima,btn_ultimo)

    return markup

def processar_deletar_tag(message):
    try:
        conn, cursor = conectar_banco_dados()
        id_usuario = message.from_user.id
        args = message.text.split(maxsplit=1)
        
        if len(args) == 2:
            tag_info = args[1].strip()

            if '|' in tag_info:
                id_list, nometag = [part.strip() for part in tag_info.split('|')]
                ids_personagens = [id.strip() for id in id_list.split(',')]

                for id_personagem in ids_personagens:
                    cursor.execute("SELECT idtags FROM tags WHERE id_usuario = %s AND id_personagem = %s AND nometag = %s",
                                   (id_usuario, id_personagem, nometag))
                    tag_existente = cursor.fetchone()
                    
                    if tag_existente:
                        idtag = tag_existente[0]
                        cursor.execute("DELETE FROM tags WHERE idtags = %s", (idtag,))
                        conn.commit()
                        bot.reply_to(message, f"ID {id_personagem} removido da tag '{nometag}' com sucesso.")
                    else:
                        bot.reply_to(message, f"O ID {id_personagem} não está associado à tag '{nometag}'.")
            
            else:
                nometag = tag_info.strip()
                cursor.execute("DELETE FROM tags WHERE id_usuario = %s AND nometag = %s", (id_usuario, nometag))
                conn.commit()
                bot.reply_to(message, f"A tag '{nometag}' foi removida completamente.")
        
        else:
            bot.reply_to(message, "Formato incorreto. Use /deltag id1, id2, id3 | nometag para remover IDs específicos da tag ou /deltag nometag para remover a tag inteira.")

    except Exception as e:
        print(f"Erro ao deletar tag: {e}")
    finally:
        fechar_conexao(cursor, conn)

