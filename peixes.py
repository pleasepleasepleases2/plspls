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
from datetime import date

def obter_total_imagens(subcategoria):
    conn, cursor = conectar_banco_dados()
    try:
        query_total = "SELECT COUNT(id_personagem) FROM personagens WHERE subcategoria = %s"
        cursor.execute(query_total, (subcategoria,))
        total_imagens = cursor.fetchone()[0]
        return total_imagens
    finally:
        fechar_conexao(cursor, conn)


def obter_imagem_info(subcategoria, offset):
    conn, cursor = conectar_banco_dados()
    try:
        query = "SELECT imagem, emoji, nome, id_personagem FROM personagens WHERE subcategoria = %s LIMIT 1 OFFSET %s"
        cursor.execute(query, (subcategoria, offset))
        return cursor.fetchone()
    finally:
        fechar_conexao(cursor, conn)


def obter_ids_personagens(subcategoria):
    conn, cursor = conectar_banco_dados()
    try:
        query_ids = "SELECT id_personagem FROM personagens WHERE subcategoria = %s"
        cursor.execute(query_ids, (subcategoria,))
        return [id[0] for id in cursor.fetchall()]
    finally:
        fechar_conexao(cursor, conn)

def criar_botao_pagina_peixes(message, subcategoria, pagina_atual):
    try:
        total_imagens = obter_total_imagens(subcategoria)
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row(
            telebot.types.InlineKeyboardButton(text="⏪️", callback_data=f"img_1_{subcategoria}"),
            telebot.types.InlineKeyboardButton(text="⬅️", callback_data=f"img_{pagina_atual-1}_{subcategoria}"),
            telebot.types.InlineKeyboardButton(text="➡️", callback_data=f"img_{pagina_atual+1}_{subcategoria}"),
            telebot.types.InlineKeyboardButton(text="⏩️", callback_data=f"img_{total_imagens}_{subcategoria}")
        )
        return markup
    except Exception as e:
        print(f"Erro ao criar botões de página: {e}")

def enviar_imagem_peixe(message, subcategoria, pagina_atual=1):
    try:
        subcategoria_encontrada = verificar_apelido(subcategoria)
        offset = pagina_atual - 1
        imagem_info = obter_imagem_info(subcategoria_encontrada, offset)
        
        ids = obter_ids_personagens(subcategoria_encontrada)
        total_ids = len(ids)
        
        if imagem_info:
            imagem, emoji, nome, id_personagem = imagem_info
            caption = f"Peixes da espécie: <b>{subcategoria_encontrada}</b>\n\n{emoji} {id_personagem} - {nome}\n\nPersonagem {pagina_atual} de {total_ids}"
            markup = criar_botao_pagina_peixes(message, subcategoria_encontrada, pagina_atual)
            bot.send_photo(message.chat.id, photo=imagem, caption=caption, reply_markup=markup, parse_mode="HTML")
        else:
            bot.reply_to(message, f"Nenhuma imagem encontrada na subcategoria '{subcategoria_encontrada}'.")

    except Exception as e:
        print(f"Erro ao processar comando /peixes img: {e}")
        bot.reply_to(message, "Ocorreu um erro ao processar sua solicitação.")

def callback_img_peixes(call, pagina_atual, subcategoria):
    try:
        subcategoria_encontrada = verificar_apelido(subcategoria)
        ids = obter_ids_personagens(subcategoria_encontrada)
        total_ids = len(ids)

        if 1 <= pagina_atual <= total_ids:
            id_atual = ids[pagina_atual - 1]
            conn, cursor = conectar_banco_dados()
            query_info = "SELECT imagem, emoji, nome FROM personagens WHERE id_personagem = %s"
            cursor.execute(query_info, (id_atual,))
            info = cursor.fetchone()
            fechar_conexao(cursor, conn)

            if info:
                imagem, emoji, nome = info
                legenda = f"Peixes da espécie: <b>{subcategoria}</b>\n\n{emoji} {id_atual} - {nome}\n\nPersonagem {pagina_atual} de {total_ids}"
                markup = criar_botao_pagina_peixes(call.message, subcategoria, pagina_atual)
                bot.edit_message_media(chat_id=call.message.chat.id, message_id=call.message.message_id, media=telebot.types.InputMediaPhoto(imagem, caption=legenda, parse_mode="HTML"), reply_markup=markup)
            else:
                bot.answer_callback_query(call.id, text="Imagem não encontrada.")
        else:
            bot.answer_callback_query(call.id, text="ID não encontrado.")
    except Exception as e:
        print(f"Erro ao processar callback 'img' de peixes: {e}")

def mostrar_lista_peixes(message, subcategoria):
    try:
        conn, cursor = conectar_banco_dados()
        subcategoria_like = f"%{subcategoria}%"
        query_subcategoria = "SELECT subcategoria FROM personagens WHERE subcategoria LIKE %s LIMIT 1"
        cursor.execute(query_subcategoria, (subcategoria_like,))
        subcategoria_encontrada = cursor.fetchone()

        if subcategoria_encontrada:
            subcategoria = subcategoria_encontrada[0]
            query_personagens = "SELECT id_personagem, nome, emoji FROM personagens WHERE subcategoria = %s"
            cursor.execute(query_personagens, (subcategoria,))
            peixes_personagens = cursor.fetchall()
            fechar_conexao(cursor, conn)

            conn, cursor = conectar_banco_dados()
            query_evento = "SELECT id_personagem, nome, emoji FROM evento WHERE subcategoria = %s"
            cursor.execute(query_evento, (subcategoria,))
            peixes_evento = cursor.fetchall()
            fechar_conexao(cursor, conn)

            peixes = peixes_personagens + peixes_evento

            if peixes:
                resposta = f"<i>Peixes da espécie</i> <b>{subcategoria}</b>:\n\n"
                paginas = dividir_em_paginas(peixes, 15)
                pagina_atual = 1

                if pagina_atual in paginas:
                    resposta_pagina = ""
                    for index, peixe in enumerate(paginas[pagina_atual], start=1):
                        id_personagem, nome, emoji = peixe
                        resposta_pagina += f"{emoji} <code>{id_personagem}</code> - {nome}\n"

                    resposta += resposta_pagina

                    if len(paginas) > 1:
                        resposta += f"\nPágina <b>{pagina_atual}</b>/{len(paginas)}"
                        markup = criar_markup_peixes(pagina_atual, len(paginas), subcategoria)
                        bot.send_message(message.chat.id, resposta, reply_markup=markup, parse_mode="HTML")
                    else:
                        bot.send_message(message.chat.id, resposta, parse_mode="HTML")
                else:
                    bot.reply_to(message, "Página não encontrada.")
            else:
                bot.reply_to(message, f"Nenhum peixe encontrado na subcategoria '{subcategoria}'.")
        else:
            bot.reply_to(message, f"Nenhuma subcategoria correspondente encontrada para '{subcategoria}'.")

    except Exception as e:
        print(f"Erro ao processar comando /peixes: {e}")
        bot.reply_to(message, "Ocorreu um erro ao processar sua solicitação.")

def criar_markup_peixes(pagina_atual, total_paginas, subcategoria):
    markup = telebot.types.InlineKeyboardMarkup()

    markup.row(
        telebot.types.InlineKeyboardButton(text="⏪️", callback_data=f"peixes_1_{subcategoria}"),
        telebot.types.InlineKeyboardButton(text="⬅️", callback_data=f"peixes_{pagina_atual-1}_{subcategoria}"),
        telebot.types.InlineKeyboardButton(text="➡️", callback_data=f"peixes_{pagina_atual+1}_{subcategoria}"),
        telebot.types.InlineKeyboardButton(text="⏪️", callback_data=f"peixes_{total_paginas}_{subcategoria}")
    )

    return markup

def pagina_peixes_callback(call, pagina, subcategoria):
    try:
        conn, cursor = conectar_banco_dados()
        query_personagens = "SELECT id_personagem, nome, emoji FROM personagens WHERE subcategoria = %s"
        cursor.execute(query_personagens, (subcategoria,))
        peixes_personagens = cursor.fetchall()
        fechar_conexao(cursor, conn)

        conn, cursor = conectar_banco_dados()
        query_evento = "SELECT id_personagem, nome, emoji FROM evento WHERE subcategoria = %s"
        cursor.execute(query_evento, (subcategoria,))
        peixes_evento = cursor.fetchall()
        fechar_conexao(cursor, conn)

        peixes = peixes_personagens + peixes_evento
        paginas = dividir_em_paginas(peixes, 15)

        if pagina in paginas:
            resposta = f"<i>Peixes da espécie</i> <b>{subcategoria}</b>:\n\n"
            for peixe in paginas[pagina]:
                id_personagem, nome, emoji = peixe
                resposta += f"{emoji} <code>{id_personagem}</code> - {nome}\n"

            resposta += f"\nPágina <b>{pagina}</b>/{len(paginas)}"
            markup = criar_markup_peixes(pagina, len(paginas), subcategoria)

            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=resposta, reply_markup=markup, parse_mode="HTML")
        else:
            bot.answer_callback_query(call.id, text="Página não encontrada.")
    except Exception as e:
        print(f"Erro ao processar callback de página de peixes: {e}")

def dividir_em_paginas(lista, tamanho_pagina):
    paginas = {}
    for i in range(0, len(lista), tamanho_pagina):
        paginas[(i // tamanho_pagina) + 1] = lista[i:i + tamanho_pagina]
    return paginas

def processar_notificacao_personagem(call):
    try:
        id_personagem = int(call.data.split('_')[1])
        conn, cursor = conectar_banco_dados()

        # Verificar quantas vezes a carta foi rodada
        cursor.execute("SELECT rodados FROM cartas WHERE id_personagem = %s", (id_personagem,))
        quantidade_personagem = cursor.fetchone()

        if quantidade_personagem is not None and quantidade_personagem[0] >= 0:
            bot.answer_callback_query(call.id, f"Esta carta foi rodada {quantidade_personagem[0]} vezes!")
        else:
            bot.answer_callback_query(call.id, f"Esta carta não foi rodada ainda :(!")
    except Exception as e:
        print(f"Erro ao lidar com o callback: {e}")
    finally:
        fechar_conexao(cursor, conn)
def handle_navigate_messages(call):
    try:
        chat_id = call.message.chat.id
        data_parts = call.data.split('_')

        if len(data_parts) == 4 and data_parts[0] in ('next', 'prev'):
            direction, current_index, total_count = data_parts[0], int(data_parts[2]), int(data_parts[3])
        else:
            raise ValueError("Callback_data com número incorreto de partes ou formato inválido.")

        user_id = call.from_user.id
        mensagens, _ = load_user_state(user_id, 'gnomes')
        if direction == 'next':
            current_index += 1
        elif direction == 'prev':
            current_index -= 1
        media_url, mensagem = mensagens[current_index]
        markup = create_navigation_markup(current_index, len(mensagens))

        if media_url:
            if media_url.lower().endswith(".gif"):
                bot.edit_message_media(chat_id=chat_id, message_id=call.message.message_id, media=telebot.types.InputMediaAnimation(media=media_url, caption=mensagem, parse_mode="HTML"), reply_markup=markup)
            elif media_url.lower().endswith(".mp4"):
                bot.edit_message_media(chat_id=chat_id, message_id=call.message.message_id, media=telebot.types.InputMediaVideo(media=media_url, caption=mensagem, parse_mode="HTML"), reply_markup=markup)
            elif media_url.lower().endswith((".jpeg", ".jpg", ".png")):
                bot.edit_message_media(chat_id=chat_id, message_id=call.message.message_id, media=telebot.types.InputMediaPhoto(media=media_url, caption=mensagem, parse_mode="HTML"), reply_markup=markup)
            else:
                bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=mensagem, reply_markup=markup, parse_mode="HTML")
        else:
            bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=mensagem, reply_markup=markup, parse_mode="HTML")

    except Exception as e:
        print("Erro ao processar callback dos botões de navegação:", str(e))


def handle_navigate_gnome_results(call):
    try:
        chat_id = call.message.chat.id
        data_parts = call.data.split('_')

        if len(data_parts) == 4 and data_parts[0] in ('prox', 'ant'):
            direction, current_page, total_pages = data_parts[0], int(data_parts[2]), int(data_parts[3])
        else:
            raise ValueError("Callback_data com número incorreto de partes ou formato inválido.")

        user_id = call.from_user.id
        resultados, _, message_id = globals.load_state(user_id, 'gnomes')
        if direction == 'prox':
            current_page = min(current_page + 1, total_pages)
        elif direction == 'ant':
            current_page = max(current_page - 1, 1)
            
        resultados_pagina_atual = resultados[(current_page - 1) * 15 : current_page * 15]
        lista_resultados = [f"{emoji} - {id_personagem} - {nome} de {subcategoria}" for emoji, id_personagem, nome, subcategoria in resultados_pagina_atual]
        mensagem_final = f"🐠 Peixes de nome', página {current_page}/{total_pages}:\n\n" + "\n".join(lista_resultados)
        markup = create_navegacao_markup(current_page, total_pages)

        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=mensagem_final, reply_markup=markup)

    except Exception as e:
        print("Erro ao processar callback dos botões de navegação:", str(e))
import traceback


def handle_callback_total_personagem(call):
    try:
        conn, cursor = conectar_banco_dados()
        chat_id = call.message.chat.id
        id_pesquisa = call.data.split('_')[1]

        sql_total = "SELECT total FROM personagens WHERE id_personagem = %s"
        cursor.execute(sql_total, (id_pesquisa,))
        total_pescados = cursor.fetchone()

        if total_pescados is not None and total_pescados[0] is not None:
            if total_pescados[0] > 1:
                response_text = f"O personagem foi pescado {total_pescados[0]} vezes!"
            elif total_pescados[0] == 1:
                response_text = f"O personagem foi pescado {total_pescados[0]} vez!"
            else:
                response_text = "Esse personagem ainda não foi pescado :("
        else:
            response_text = "Esse personagem ainda não foi pescado :("

        try:
            bot.answer_callback_query(call.id, text=response_text, show_alert=True)
        except Exception as e:
            traceback.print_exc()
            erro = traceback.format_exc()
            mensagem = f"Alerta de erro carta pescadas. Erro: {e}\n{erro}"
            bot.send_message(grupodeerro, mensagem, parse_mode="HTML")

    except Exception as e:
        traceback.print_exc()
        erro = traceback.format_exc()
        mensagem = f"Alerta de erro carta pescadas. Erro: {e}\n{erro}"
        bot.send_message(grupodeerro, mensagem, parse_mode="HTML")

    finally:
        cursor.close()
        conn.close()

def gnome(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    idmens = message.message_id

    try:
        partes = message.text.split()
        if 'e' in partes:
            nome = ' '.join(partes[2:])  
            sql_personagens = """
                SELECT
                    e.id_personagem,
                    e.nome,
                    e.subcategoria,
                    e.categoria,
                    COALESCE(i.quantidade, 0) AS quantidade_usuario,
                    e.imagem
                FROM evento e
                LEFT JOIN inventario i ON e.id_personagem = i.id_personagem AND i.id_usuario = %s
                WHERE e.nome LIKE %s
            """
        else:
            nome = ' '.join(partes[1:]) 
            sql_personagens = """
                SELECT
                    p.id_personagem,
                    p.nome,
                    p.subcategoria,
                    p.categoria,
                    COALESCE(i.quantidade, 0) AS quantidade_usuario,
                    p.imagem
                FROM personagens p
                LEFT JOIN inventario i ON p.id_personagem = i.id_personagem AND i.id_usuario = %s
                WHERE p.nome LIKE %s
            """

        values_personagens = (user_id, f"%{nome}%")
        conn, cursor = conectar_banco_dados()
        cursor.execute(sql_personagens, values_personagens)
        resultados_personagens = cursor.fetchall()

        if not resultados_personagens:
            bot.send_message(chat_id, f"Nenhum personagem encontrado com o nome '{nome}'.")
            return

        total_personagens = len(resultados_personagens)

        # Função para exibir uma carta por vez
        def enviar_carta_individual(index):
            id_personagem, nome, subcategoria, categoria, quantidade_usuario, imagem_url = resultados_personagens[index]
            
            # Criação da mensagem para a carta
            mensagem = f"💌 | Personagem:\n\n<code>{id_personagem}</code> • {nome}\nde {subcategoria}\n"
            if quantidade_usuario > 0:
                mensagem += f"☀ | {quantidade_usuario}⤫"
            else:
                mensagem += f"🌧 | Tempo fechado..."

            # Verificar se existe uma imagem GIF ou URL para a carta
            gif_url = obter_gif_url(id_personagem, user_id)
            if gif_url:
                imagem_url = gif_url

            # Botões de navegação
            keyboard = types.InlineKeyboardMarkup()
            if index > 0:
                keyboard.add(types.InlineKeyboardButton("⬅️ Anterior", callback_data=f"gnome_prev_{index-1}"))
            if index < total_personagens - 1:
                keyboard.add(types.InlineKeyboardButton("Próxima ➡️", callback_data=f"gnome_next_{index+1}"))

            # Envio da imagem e mensagem
            if imagem_url.lower().endswith(".gif"):
                bot.send_animation(chat_id, imagem_url, caption=mensagem, reply_markup=keyboard, parse_mode="HTML")
            elif imagem_url.lower().endswith(".mp4"):
                bot.send_video(chat_id, imagem_url, caption=mensagem, reply_markup=keyboard, parse_mode="HTML")
            elif imagem_url.lower().endswith((".jpeg", ".jpg", ".png")):
                bot.send_photo(chat_id, imagem_url, caption=mensagem, reply_markup=keyboard, parse_mode="HTML")
            else:
                bot.send_message(chat_id, mensagem, reply_markup=keyboard, parse_mode="HTML")

        # Enviar a primeira carta
        enviar_carta_individual(0)

        # Função de callback para navegar entre as cartas
        @bot.callback_query_handler(func=lambda call: call.data.startswith('gnome_'))
        def handle_navigation(call):
            action, index_str = call.data.split('_')[1:3]
            index = int(index_str)

            if action == 'prev':
                enviar_carta_individual(index)
            elif action == 'next':
                enviar_carta_individual(index)

    except Exception as e:
        import traceback
        traceback.print_exc()
        newrelic.agent.record_exception()
    finally:
        fechar_conexao(cursor, conn)



def gnomes(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    conn, cursor = conectar_banco_dados()

    try:
        nome = message.text.split('/gnomes', 1)[1].strip()
        if len(nome) <= 2:
            bot.send_message(chat_id, "Por favor, forneça um nome com mais de 3 letras.", reply_to_message_id=message.message_id)
            return

        sql_personagens = """
            SELECT
                p.emoji,
                p.id_personagem,
                p.nome,
                p.subcategoria
            FROM personagens p
            WHERE p.nome LIKE %s
        """
        values_personagens = (f"%{nome}%",)
        pesquisa = nome
        cursor.execute(sql_personagens, values_personagens)
        resultados_personagens = cursor.fetchall()

        if resultados_personagens:
            total_resultados = len(resultados_personagens)
            resultados_por_pagina = 15
            total_paginas = -(-total_resultados // resultados_por_pagina)
            pagina_solicitada = 1

            if total_resultados > resultados_por_pagina:
                if len(message.text.split()) == 3 and message.text.split()[2].isdigit():
                    pagina_solicitada = min(int(message.text.split()[2]), total_paginas)

                resultados_pagina_atual = resultados_personagens[(pagina_solicitada - 1) * resultados_por_pagina:pagina_solicitada * resultados_por_pagina]
                lista_resultados = [f"{emoji} <code>{id_personagem}</code> • {nome}\nde {subcategoria}" for emoji, id_personagem, nome, subcategoria in resultados_pagina_atual]

                mensagem_final = f"🐠 Peixes de nome <b>{pesquisa}</b>:\n\n" + "\n".join(lista_resultados) + f"\n\nPágina {pagina_solicitada}/{total_paginas}:"
                markup = create_navigation_markup(pagina_solicitada, total_paginas)
                message = bot.send_message(chat_id, mensagem_final, reply_markup=markup, reply_to_message_id=message.message_id, parse_mode="HTML")

                save_state(user_id, 'gnomes', resultados_personagens, chat_id, message.message_id)
            else:
                lista_resultados = [f"{emoji} <code>{id_personagem}</code> • {nome}\nde {subcategoria}" for emoji, id_personagem, nome, subcategoria in resultados_personagens]

                mensagem_final = f"🐠 Peixes de nome <b>{pesquisa}</b>:\n\n" + "\n".join(lista_resultados)
                bot.send_message(chat_id, mensagem_final, reply_to_message_id=message.message_id, parse_mode='HTML')

        else:
            bot.send_message(chat_id, f"Nenhum resultado encontrado para o nome '{nome}'.", reply_to_message_id=message.message_id)
    finally:
        fechar_conexao(cursor, conn)


def obter_id_e_enviar_info_com_imagem(message):
    try:
        conn, cursor = conectar_banco_dados()
        user_id = message.from_user.id
        chat_id = message.chat.id

        command_parts = message.text.split()
        if len(command_parts) == 2 and command_parts[1].isdigit():
            id_pesquisa = command_parts[1]

            is_evento = verificar_evento(cursor, id_pesquisa)

            if is_evento:
                sql_evento = """
                    SELECT
                        e.id_personagem,
                        e.nome,
                        e.subcategoria,
                        e.categoria,
                        i.quantidade AS quantidade_usuario,
                        e.imagem
                    FROM evento e
                    LEFT JOIN inventario i ON e.id_personagem = i.id_personagem AND i.id_usuario = %s
                    WHERE e.id_personagem = %s
                """
                values_evento = (message.from_user.id, id_pesquisa)

                cursor.execute(sql_evento, values_evento)
                resultado_evento = cursor.fetchone()

                if resultado_evento:
                    id_personagem, nome, subcategoria, quantidade_usuario, imagem_url = resultado_evento

                    mensagem = f"💌 | Personagem: \n\n<code>{id_personagem}</code> • {nome}\nde {subcategoria}"

                    if quantidade_usuario is None:
                        mensagem += f"\n\n🌧 | Tempo fechado..."
                    elif quantidade_usuario == 1:
                        mensagem += f"\n\n{'☀  '}"
                    else:
                        mensagem += f"\n\n{'☀ 𖡩'}"

                    try:
                        if imagem_url.lower().endswith(('.jpg', '.jpeg', '.png')):
                            bot.send_photo(chat_id=message.chat.id, photo=imagem_url, caption=mensagem, reply_to_message_id=message.message_id, parse_mode="HTML")
                        elif imagem_url.lower().endswith(('.mp4', '.gif')):
                            bot.send_video(chat_id=message.chat.id, video=imagem_url, caption=mensagem, reply_to_message_id=message.message_id, parse_mode="HTML")
                    except Exception as e:
                        bot.send_message(chat_id, mensagem, reply_to_message_id=message.message_id, parse_mode="HTML")
                else:
                    bot.send_message(chat_id, f"Nenhum resultado encontrado para o ID '{id_pesquisa}'.", reply_to_message_id=message.message_id)

            else:
                sql_normal = """
                    SELECT
                        p.id_personagem,
                        p.nome,
                        p.subcategoria,
                        p.categoria,
                        i.quantidade AS quantidade_usuario,
                        p.imagem,
                        p.cr
                    FROM personagens p
                    LEFT JOIN inventario i ON p.id_personagem = i.id_personagem AND i.id_usuario = %s
                    WHERE p.id_personagem = %s
                """
                values_normal = (message.from_user.id, id_pesquisa)

                cursor.execute(sql_normal, values_normal)
                resultado_normal = cursor.fetchone()

                if resultado_normal:
                    id_personagem, nome, subcategoria, quantidade_usuario, imagem_url, cr = resultado_normal

                    mensagem = f"💌 | Personagem: \n\n{id_personagem} • {nome}\nde {subcategoria}"

                    if quantidade_usuario is not None and quantidade_usuario > 0:
                        mensagem += f"\n\n☀ | {quantidade_usuario}⤫"
                    else:
                        mensagem += f"\n\n🌧 | Tempo fechado..."

                    if cr:
                        link_cr = obter_link_formatado(cr)
                        mensagem += f"\n\n{link_cr}"

                    markup = InlineKeyboardMarkup()
                    markup.row_width = 1
                    markup.add(InlineKeyboardButton("💟", callback_data=f"total_{id_pesquisa}"))

                    gif_url = obter_gif_url(id_personagem, user_id)
                    if gif_url:
                        imagem_url = gif_url
                        if imagem_url.lower().endswith(".gif"):
                            bot.send_video(chat_id=message.chat.id, video=imagem_url, caption=mensagem, reply_markup=markup, reply_to_message_id=message.message_id, parse_mode="HTML")
                        elif imagem_url.lower().endswith(".mp4"):
                            bot.send_video(chat_id=message.chat.id, video=imagem_url, caption=mensagem, reply_markup=markup, reply_to_message_id=message.message_id, parse_mode="HTML")
                        elif imagem_url.lower().endswith((".jpeg", ".jpg", ".png")):
                            bot.send_photo(chat_id=message.chat.id, photo=imagem_url, caption=mensagem, reply_markup=markup, reply_to_message_id=message.message_id, parse_mode="HTML")
                        else:
                            bot.send_message(chat_id, mensagem)
                    else:
                        if imagem_url.lower().endswith(".gif"):
                            bot.send_video(chat_id=message.chat.id, video=imagem_url, caption=mensagem, reply_markup=markup, reply_to_message_id=message.message_id, parse_mode="HTML")
                        elif imagem_url.lower().endswith(".mp4"):
                            bot.send_video(chat_id=message.chat.id, video=imagem_url, caption=mensagem, reply_markup=markup, reply_to_message_id=message.message_id, parse_mode="HTML")
                        elif imagem_url.lower().endswith((".jpeg", ".jpg", ".png")):
                            bot.send_photo(chat_id=message.chat.id, photo=imagem_url, caption=mensagem, reply_markup=markup, reply_to_message_id=message.message_id, parse_mode="HTML")
                        else:
                            bot.send_message(chat_id, mensagem)
                else:
                    bot.send_message(chat_id, f"Nenhum resultado encontrado para o ID '{id_pesquisa}'.", reply_to_message_id=message.message_id)
        else:
            bot.send_message(chat_id, "Formato incorreto. Use /gid seguido do ID desejado, por exemplo: /gid 123", reply_to_message_id=message.message_id)
    except Exception as e:
        import traceback
        traceback.print_exc()
        erro = traceback.print_exc()
        mensagem = f"carta com erro: {id_personagem}. erro: {e}"
        bot.send_message(grupodeerro, mensagem, parse_mode="HTML")
