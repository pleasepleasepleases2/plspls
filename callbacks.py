from pesquisas import *
from user import *
from bd import *
from loja import *
from gnome import *
from cestas import *
from tag import *
from gift import *
from evento import *
from callbacks import *
from operacoes import *
from sub import *
from armazem import *
from wish import *
from cenourar import *
from pescar import *
from trocas import *
from operacoes import *
from gif import *
import html

def diminuir_cenouras(id_usuario, valor):
    try:
        conn, cursor = conectar_banco_dados()
        cursor.execute("SELECT cenouras FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        resultado = cursor.fetchone()

        if resultado:
            cenouras_atuais = int(resultado[0]) 
            if cenouras_atuais >= valor:
                nova_quantidade = cenouras_atuais - valor
                cursor.execute("UPDATE usuarios SET cenouras = %s WHERE id_usuario = %s", (nova_quantidade, id_usuario))
                conn.commit()
            else:
                print("Erro: Não há cenouras suficientes para diminuir.")
        else:
            print("Erro: Usuário não encontrado.")

    except Exception as e:
        print(f"Erro ao diminuir cenouras: {e}")

    finally:
        fechar_conexao(cursor, conn)
def add_to_inventory(id_usuario, id_personagem, max_retries=5):
    attempt = 0
    id_usuario = int(id_usuario)
    id_personagem = int(id_personagem)
    
    while attempt < max_retries:
        try:
            conn, cursor = conectar_banco_dados()

            # Iniciar uma transação
            conn.start_transaction()

            # Ordenar as operações em ordem específica para evitar deadlocks
            if id_usuario < id_personagem:
                cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s FOR UPDATE",
                               (id_usuario, id_personagem))
            else:
                cursor.execute("SELECT quantidade FROM inventario WHERE id_personagem = %s AND id_usuario = %s FOR UPDATE",
                               (id_personagem, id_usuario))

            existing_carta = cursor.fetchone()

            if existing_carta:
                nova_quantidade = existing_carta[0] + 1
                cursor.execute("UPDATE inventario SET quantidade = %s WHERE id_usuario = %s AND id_personagem = %s",
                               (nova_quantidade, id_usuario, id_personagem))
            else:
                cursor.execute("INSERT INTO inventario (id_personagem, id_usuario, quantidade) VALUES (%s, %s, 1)",
                               (id_personagem, id_usuario))

            cursor.execute("UPDATE personagens SET total = IFNULL(total, 0) + 1 WHERE id_personagem = %s", (id_personagem,))

            # Confirmar a transação
            conn.commit()
            break  # Saia do loop se a transação for bem-sucedida

        except mysql.connector.errors.DatabaseError as db_err:
            if db_err.errno == 1205:  # Código de erro para lock wait timeout exceeded
                attempt += 1
                time.sleep(1)  # Esperar um pouco antes de tentar novamente
                if attempt >= max_retries:
                    mensagem = "Erro: Excedido o número máximo de tentativas para resolver o deadlock."
                    bot.send_message(grupodeerro, mensagem, parse_mode="HTML")
            else:
                mensagem = f"Erro ao adicionar carta ao inventário: {db_err}"
                bot.send_message(grupodeerro, mensagem, parse_mode="HTML")
                break
        except Exception as e:
            traceback.print_exc()
            erro = traceback.format_exc()
            mensagem = f"Adição de personagem com erro: {id_personagem} - usuário {id_usuario}. erro: {e}\n{erro}"
            bot.send_message(grupodeerro, mensagem, parse_mode="HTML")
            break
        finally:
            fechar_conexao(cursor, conn)
def loja_geral_callback(call):
    try:
        id_usuario = call.from_user.id
        cursor.execute("SELECT cenouras FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        result = cursor.fetchone()
        if result:
            qnt_cenouras = int(result[0])
        else:
            qnt_cenouras = 0
        if qnt_cenouras >= 3:
            mensagem = f"Você tem {qnt_cenouras} cenouras. Deseja usar 3 para ganhar um peixe aleatório?"
            keyboard = telebot.types.InlineKeyboardMarkup()
            keyboard.row(
                telebot.types.InlineKeyboardButton(text="Sim", callback_data=f'geral_compra_{id_usuario}'),
                telebot.types.InlineKeyboardButton(text="Não", callback_data='cancelar_compra')
            )
            imagem_url = "https://telegra.ph/file/d4d5d0af60ec66f35e29c.jpg"
            bot.edit_message_media(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=keyboard,
                media=telebot.types.InputMediaPhoto(media=imagem_url, caption=mensagem)
            )
    except Exception as e:
        print(f"Erro ao processar loja_geral_callback: {e}")

def geral_compra_callback(call):
    try:
        conn, cursor = conectar_banco_dados()
        
        query_personagens = "SELECT * FROM personagens ORDER BY RAND() LIMIT 1"
        cursor.execute(query_personagens)
        carta_personagem = cursor.fetchone()
        
        query_evento = "SELECT * FROM evento ORDER BY RAND() LIMIT 1"
        cursor.execute(query_evento)
        carta_evento = cursor.fetchone()

        if carta_personagem and carta_evento:
            if random.choice([True, False]):
                carta_aleatoria = carta_personagem
            else:
                carta_aleatoria = carta_evento

            id_personagem, nome, subcategoria, categoria, evento, imagem, emoji, cr = carta_aleatoria[:8]
            id_usuario = call.from_user.id
            valor = 3
            add_to_inventory(id_usuario, id_personagem)
            diminuir_cenouras(id_usuario, valor)

            resposta = f"🎴 Os mares trazem para sua rede:\n\n" \
                       f"{emoji} • {id_personagem} - {nome} \n{subcategoria} - {evento}\n\nVolte sempre!"

            if imagem:
                bot.send_photo(
                    chat_id=call.message.chat.id,
                    photo=imagem,
                    caption=resposta
                )
            else:
                resposta1 = f"🎴 Os mares trazem para sua rede:\n\n {emoji} • {id_personagem} - {nome} \n{subcategoria} - {evento}\n\n (A carta não possui foto ainda :())"
                bot.send_message(
                    chat_id=call.message.chat.id,
                    text=resposta1
                )
        else:
            bot.send_message(call.message.chat.id, "Não foi possível encontrar uma carta aleatória.")
    except mysql.connector.Error as err:
        bot.send_message(call.message.chat.id, f"Erro ao sortear carta: {err}")
    finally:
        fechar_conexao(cursor, conn)


def geral_compra_callback(call):
    try:
        conn, cursor = conectar_banco_dados()

        query_personagens = "SELECT id_personagem, nome, subcategoria,  emoji, categoria,  imagem, cr FROM personagens ORDER BY RAND() LIMIT 1"
        cursor.execute(query_personagens)
        carta_personagem = cursor.fetchone()
        chance = random.choices([True, False], weights=[3, 97])[0]
        # Se não houver carta de personagem, selecionar aleatoriamente uma carta da tabela 'evento' com 5% de chance
        if chance:
            query_evento = "SELECT id_personagem, nome, subcategoria, categoria, evento, emoji, cr, imagem FROM evento ORDER BY RAND() LIMIT 1"
            cursor.execute(query_evento)
            carta_evento = cursor.fetchone()
        else:
            carta_evento = None
        if carta_personagem or carta_evento:
            if carta_evento:
                id_personagem, nome, subcategoria, categoria, evento, emoji, cr, imagem = carta_evento
                categoria = "Evento"
            else:
                id_personagem, nome, subcategoria,  emoji, categoria,  imagem, cr = carta_personagem
                evento = ""
                categoria = categoria.capitalize()  
            id_usuario = call.from_user.id
            valor = 3
            add_to_inventory(id_usuario, id_personagem)
            diminuir_cenouras(id_usuario, valor)

            resposta = f"🎴 Os mares trazem para sua rede:\n\n" \
           f"{emoji} • {id_personagem} - {nome} \n{subcategoria}{' - ' + evento if not carta_personagem else ''}\n\nVolte sempre!"

            if imagem:
                bot.edit_message_media(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    media=telebot.types.InputMediaPhoto(media=imagem, caption=resposta)
                )
            else:
                resposta1 = f"🎴 Os mares trazem para sua rede:\n\n {emoji} • {id_personagem} - {nome} \n{subcategoria} - {categoria if carta_personagem else evento}\n\n (A carta não possui foto ainda :())"
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=resposta1,
                    reply_markup=None
                )
        else:
            bot.send_message(call.message.chat.id, "Não foi possível encontrar uma carta aleatória.")
    except mysql.connector.Error as err:
        mensagem = f"Erro ao sortear carta: {err}"
        bot.send_message(grupodeerro, mensagem, parse_mode="HTML")
    finally:
        fechar_conexao(cursor, conn)


def compras_iscas_callback(call):
    try:
        chat_id = call.message.chat.id
        message_data = call.data
        parts = message_data.split('_')
        categoria = parts[1]
        id_usuario = parts[2]
        original_message_id = parts[3]
        conn, cursor = conectar_banco_dados()
        id_usuario = call.from_user.id
        cursor.execute("SELECT cenouras FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        result = cursor.fetchone()

        if result:
            qnt_cenouras = int(result[0])
        else:
            qnt_cenouras = 0
        if qnt_cenouras >= 5:
            mensagem = f"Você tem {qnt_cenouras} cenouras. Deseja usar 5 para comprar iscas?"
            keyboard = telebot.types.InlineKeyboardMarkup()
            keyboard.row(
                telebot.types.InlineKeyboardButton(text="Sim", callback_data=f'confirmar_compra_iscas_{id_usuario}_{original_message_id}'),
                telebot.types.InlineKeyboardButton(text="Não", callback_data='cancelar_compra')
            )
            imagem_url = "URL_DA_SUA_IMAGEM"
            bot.edit_message_media(
                chat_id=call.message.chat.id,
                message_id=original_message_id,
                reply_markup=keyboard,
                media=telebot.types.InputMediaPhoto(media=imagem_url, caption=mensagem)
            )
        else:
            bot.send_message(call.message.chat.id, "Você não tem cenouras suficientes para comprar iscas.")
    
    except Exception as e:
        traceback.print_exc()
        erro = traceback.format_exc()
        mensagem = f"Erro ao processar compras_iscas_callback: {e}\n{erro}"
        bot.send_message(grupodeerro, mensagem, parse_mode="HTML")
        
def isca_callback(call):
    try:
        chat_id = call.message.chat.id
        message_data = call.data
        parts = message_data.split('_')
        id_usuario = parts[1]
        original_message_id = parts[2]

        conn, cursor = conectar_banco_dados()
        id_usuario = call.from_user.id
        cursor.execute("SELECT cenouras FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        result = cursor.fetchone()

        if result:
            qnt_cenouras = int(result[0])
        else:
            qnt_cenouras = 0
        if qnt_cenouras >= 5:
            mensagem = f"Você tem {qnt_cenouras} cenouras. Deseja usar 5 para comprar uma isca?"
            keyboard = telebot.types.InlineKeyboardMarkup()
            keyboard.row(
                telebot.types.InlineKeyboardButton(text="Sim", callback_data=f'confirmar_compra_isca_{id_usuario}_{original_message_id}'),
                telebot.types.InlineKeyboardButton(text="Não", callback_data='cancelar_compra')
            )
            imagem_url = "URL_DA_SUA_IMAGEM"
            bot.edit_message_media(
                chat_id=call.message.chat.id,
                message_id=original_message_id,
                reply_markup=keyboard,
                media=telebot.types.InputMediaPhoto(media=imagem_url, caption=mensagem)
            )
        else:
            bot.send_message(call.message.chat.id, "Você não tem cenouras suficientes para comprar uma isca.")
    
    except Exception as e:
        print(f"Erro ao processar isca_callback: {e}")
        
def aprovar_callback(call):
    try:
        data = call.data.replace('aprovar_', '').strip().split('_')
        data_atual = datetime.now().strftime("%Y-%m-%d")
        hora_atual = datetime.now().strftime("%H:%M:%S")
        
        if len(data) == 2:
            conn, cursor = conectar_banco_dados()
            id_usuario, id_personagem = data
            
            sql_temp_select = "SELECT valor FROM temp_data WHERE id_usuario = %s AND id_personagem = %s"
            values_temp_select = (id_usuario, id_personagem)
            cursor.execute(sql_temp_select, values_temp_select)
            link_gif = cursor.fetchone()
            cursor.fetchall()  # Limpa os resultados do cursor antes de executar a próxima consulta

            if link_gif:
                sql_check_gif = "SELECT id_personagem FROM gif WHERE id_usuario = %s AND id_personagem = %s"
                cursor.execute(sql_check_gif, (id_usuario, id_personagem))
                cursor.fetchall()  # Limpa os resultados do cursor antes de executar a próxima consulta
                existing_gif_id = cursor.fetchone()

                if existing_gif_id:
                    sql_update_gif = "UPDATE gif SET link = %s WHERE id_personagem = %s"
                    cursor.execute(sql_update_gif, (link_gif[0], existing_gif_id[0]))
                else:
                    sql_insert_gif = "INSERT INTO gif (id_personagem, id_usuario, link) VALUES (%s, %s, %s)"
                    cursor.execute(sql_insert_gif, (id_personagem, id_usuario, link_gif[0]))

                sql_logs = "INSERT INTO logs (id_usuario, nome_usuario, ação, horario, data, aprovado, adm) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                values_logs = (id_usuario, obter_nome_usuario_por_id(id_usuario), 'gif', hora_atual, data_atual, 'sim', call.from_user.username if call.from_user.username else call.from_user.first_name)
                cursor.execute(sql_logs, values_logs)

                conn.commit()
                mensagem = f"Seu GIF para o personagem {id_personagem} foi atualizado!"
                bot.send_message(id_usuario, mensagem)

                grupo_id = -1002144134360 
                nome_usuario = obter_nome_usuario_por_id(id_usuario)
                mensagem_grupo = f"🎉 O GIF para o personagem {id_personagem} de {nome_usuario} foi aprovado! 🎉"
                bot.send_message(grupo_id, mensagem_grupo)
            else:
                print("Formato de callback incorreto. Esperado: 'aprovar_id_usuario_id_personagem'.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        erro = traceback.format_exc()
        mensagem = f"Erro ao aprovar gif - erro: {e}\n{erro} - {call}"
        bot.send_message(grupodeerro, mensagem, parse_mode="HTML")
        
def reprovar_callback(call):
    try:
        data = call.data.replace('reprovar_', '').strip().split('_')
        if len(data) == 2:
            id_usuario, id_personagem = data
            mensagem = f"Seu gif para o personagem {id_personagem} foi recusado."
            bot.send_message(id_usuario, mensagem)

            grupo_id = -1002144134360
            nome_usuario = obter_nome_usuario_por_id(id_usuario)
            mensagem_grupo = f"O GIF para o personagem {id_personagem} de {nome_usuario} foi reprovado... 😐"
            bot.send_message(grupo_id, mensagem_grupo)
        else:
            print("Formato de callback incorreto. Esperado: 'reprovar_id_usuario_id_personagem'")
    except Exception as e:
        import traceback
        traceback.print_exc()
        erro = traceback.format_exc()
        mensagem = f"Erro ao reprovar gif - erro: {e}\n{erro} - {call}"
        bot.send_message(grupodeerro, mensagem, parse_mode="HTML")


def compra_callback(call):
    try:
        chat_id = call.message.chat.id
        message_data = call.data
        parts = message_data.split('_')
        categoria = parts[1]
        id_usuario = parts[2]
        original_message_id = parts[3]
        conn, cursor = conectar_banco_dados()
        cursor.execute("SELECT cenouras FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        result = cursor.fetchone()

        if result:
            qnt_cenouras = int(result[0])
        else:
            qnt_cenouras = 0

        if qnt_cenouras >= 3:
            mensagem = f"Você tem {qnt_cenouras} cenouras. Deseja usar 3 para ganhar um peixe aleatório?"
            keyboard = telebot.types.InlineKeyboardMarkup()
            keyboard.row(
                telebot.types.InlineKeyboardButton(text="Sim", callback_data=f'confirmar_compra_{categoria}_{id_usuario}_{original_message_id}'),
                telebot.types.InlineKeyboardButton(text="Não", callback_data='cancelar_compra')
            )
            bot.edit_message_text(chat_id=chat_id, message_id=original_message_id, text=" ", reply_markup=keyboard)
        else:
            mensagem = "Desculpe, você não tem cenouras suficientes para comprar um peixe. Volte quando tiver pelo menos 3 cenouras!"
            bot.edit_message_text(chat_id=chat_id, message_id=original_message_id, text=mensagem)
    except Exception as e:
        import traceback
        traceback.print_exc()
        erro = traceback.format_exc()
        mensagem = f"Erro ao processar compra - erro: {e}\n{erro} - {call}"
        bot.send_message(grupodeerro, mensagem, parse_mode="HTML")


def confirmar_compra_callback(call):
    try:
        chat_id = call.message.chat.id
        message_data = call.data
        parts = message_data.split('_')
        categoria = parts[1]
        id_usuario = parts[2]
        original_message_id = parts[3]
        conn, cursor = conectar_banco_dados()
        cursor.execute("SELECT cenouras FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        result = cursor.fetchone()

        if result:
            qnt_cenouras = int(result[0])
        else:
            qnt_cenouras = 0

        if qnt_cenouras >= 3:
            cursor.execute("UPDATE usuarios SET cenouras = cenouras - 3 WHERE id_usuario = %s", (id_usuario,))
            cursor.execute("SELECT id_personagem FROM personagens WHERE subcategoria = %s ORDER BY RAND() LIMIT 1", (categoria,))
            result = cursor.fetchone()

            if result:
                id_personagem = result[0]
                cursor.execute("INSERT INTO colecao_usuario (id_usuario, id_personagem) VALUES (%s, %s)", (id_usuario, id_personagem))
                conn.commit()

                mensagem = f"Parabéns! Você comprou um peixe aleatório da categoria {categoria} por 3 cenouras."
                bot.edit_message_text(chat_id=chat_id, message_id=original_message_id, text=mensagem)
            else:
                mensagem = "Desculpe, ocorreu um erro ao processar sua compra. Tente novamente mais tarde."
                bot.edit_message_text(chat_id=chat_id, message_id=original_message_id, text=mensagem)
        else:
            mensagem = "Desculpe, você não tem cenouras suficientes para comprar um peixe. Volte quando tiver pelo menos 3 cenouras!"
            bot.edit_message_text(chat_id=chat_id, message_id=original_message_id, text=mensagem)
    except Exception as e:
        import traceback
        traceback.print_exc()
        erro = traceback.format_exc()
        mensagem = f"Erro ao confirmar compra - erro: {e}\n{erro} - {call}"
        bot.send_message(grupodeerro, mensagem, parse_mode="HTML")
        
def troca_callback(call):
    try:
        conn, cursor = conectar_banco_dados()
        message_data = call.data.replace('troca_sim_', '').replace('troca_nao_', '')
        parts = message_data.split('_')

        if len(parts) >= 5:
            eu, voce, minhacarta, suacarta, message = parts
            qntminha_antes = verifica_inventario_troca(eu, minhacarta)
            qntsua_antes = verifica_inventario_troca(voce, suacarta)
            chat_id = call.message.chat.id 
            user_id = call.from_user.id 
            eu = int(eu)
            voce = int(voce)

            if user_id in [eu, voce]:
                if call.data.startswith('troca_sim_'):
                    if eu != user_id:
                        if int(voce) == 6127981599:
                            bot.edit_message_caption(chat_id=chat_id,
                                                     caption="Você não pode fazer trocas com a Mabi :(")
                        elif voce == eu:
                            bot.edit_message_caption(chat_id=chat_id,
                                                     caption="Você não pode fazer trocas consigo mesmo!")
                        else:
                            realizar_troca(call.message, eu, voce, minhacarta, suacarta, chat_id, qntminha_antes, qntsua_antes)
                    else:
                        bot.answer_callback_query(callback_query_id=call.id,
                                                  text="Você não pode aceitar seu próprio lanche.")

                elif call.data.startswith('troca_nao_'):
                    if chat_id and call.message:
                        conn, cursor = conectar_banco_dados()
                        sql_insert = "INSERT INTO historico_trocas (id_usuario1, id_usuario2, quantidade_cartas_antes_usuario1, quantidade_cartas_depois_usuario1, quantidade_cartas_antes_usuario2, quantidade_cartas_depois_usuario2, id_carta_usuario1, id_carta_usuario2, aceita) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                        val = (eu, voce, qntminha_antes, 0, qntsua_antes, 0, minhacarta, suacarta, False)
                        cursor.execute(sql_insert, val)
                        conn.commit()
                        bot.edit_message_caption(chat_id=chat_id,
                                                 message_id=call.message.message_id,
                                                 caption="Poxa, um de vocês esqueceu a comida. 🕊"
                                                         "\nQuem sabe na próxima?")
                    else:
                        print("Erro: Não há informações suficientes no callback_data.")
                        bot.answer_callback_query(callback_query_id=call.id,
                                                  text="Você não pode aceitar esta troca.")
            else:
                bot.answer_callback_query(callback_query_id=call.id,
                                          text="Você não pode realizar esta ação nesta troca.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        erro = html.escape(traceback.format_exc())
        mensagem = f"Troca com erro: {call}. Erro: {e}\n{erro}"
        bot.send_message(grupodeerro, text=mensagem, parse_mode="HTML")

        chat_id = call.message.chat.id if call.message else None
        bot.edit_message_caption(chat_id=chat_id,
                                 message_id=call.message.message_id,
                                 caption="Alguém não tem o lanche enviado.\nQue tal olhar sua cesta novamente?")
    finally:
        fechar_conexao(cursor, conn)
def process_callback(call):
    try:
        message = call.message
        conn, cursor = conectar_banco_dados()
        chat_id = call.message.chat.id

        if call.message:
            chat_id = call.message.chat.id
            if not verificar_tempo_passado(chat_id):
                return
            else:
                ultima_interacao[chat_id] = datetime.now()

            # Condicionais para verificar o callback data
            if call.data.startswith("geral_compra_"):
                geral_compra_callback(call)

            elif call.data.startswith('confirmar_iscas'):
                message_id = call.message.message_id
                confirmar_iscas(call, message_id)

            elif call.data.startswith("liberar_beta"):
                process_beta_liberacao(call, message)
                
            elif call.data.startswith("remover_beta"):
                process_beta_remocao(call, message)

            elif call.data.startswith("beta_"):
                mostrar_opcoes_beta(call)

            elif call.data.startswith("verificarban_"):
                verificar_ban(call)

            elif call.data.startswith("ban_"):
                mostrar_opcoes_ban(call)

            elif call.data.startswith("novogif"):
                processar_comando_gif(message)

            elif call.data.startswith("delgif"):
                processar_comando_delgif(message)

            elif call.data.startswith("gif_"):
                mostrar_opcoes_gif(call)

            elif call.data.startswith("tag"):
                processar_pagina_tag(call)

            elif call.data.startswith("admdar_"):
                mostrar_opcoes_adm(call)

            elif call.data.startswith("dar_cenoura"):
                obter_dados_cenouras(call, message)

            elif call.data.startswith("dar_iscas"):
                obter_dados_iscas(call, message)

            elif call.data.startswith("tirar_cenoura"):
                remover_dados_cenouras(call, message)

            elif call.data.startswith("tirar_isca"):
                remover_dados_iscas(call, message)

            elif call.data.startswith("privacy"):
                processar_privacidade(call)

            elif call.data == 'open_profile':
                alterar_privacidade_perfil(call, False)

            elif call.data == 'lock_profile':
                alterar_privacidade_perfil(call, True)

            elif call.data == 'pcancelar':
                cancelar_processo(call)

            elif call.data.startswith("pronomes_"):
                atualizar_pronomes(call)

            elif call.data.startswith("bpronomes_"):
                mostrar_opcoes_pronome(call)

            elif call.data.startswith('troca_'):
                troca_callback(call)

    except Exception as e:
        import traceback
        traceback.print_exc()


# Funções extras para cada bloco de callback
def process_beta_liberacao(call, message):
    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Por favor, envie o ID da pessoa a ser liberada no beta:")                    
        bot.register_next_step_handler(message, obter_id_beta)
    except Exception as e:
        bot.reply_to(message, f"Ocorreu um erro: {e}")

def process_beta_remocao(call, message):
    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Por favor, envie o ID da pessoa a ser removida do beta:")                    
        bot.register_next_step_handler(message, remover_beta)
    except Exception as e:
        bot.reply_to(message, f"Ocorreu um erro: {e}")

def mostrar_opcoes_beta(call):
    try:
        markup = types.InlineKeyboardMarkup()
        btn_cenoura = types.InlineKeyboardButton("🥕 Liberar Usuario", callback_data=f"liberar_beta")
        btn_iscas = types.InlineKeyboardButton("🐟 Remover Usuario", callback_data=f"remover_beta")
        btn_5 = types.InlineKeyboardButton("❌ Cancelar", callback_data=f"pcancelar")
        markup.row(btn_cenoura, btn_iscas)
        markup.row(btn_5)

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Escolha o que deseja fazer:", reply_markup=markup)
    except Exception as e:
        import traceback
        traceback.print_exc()

def mostrar_opcoes_ban(call):
    try:
        markup = types.InlineKeyboardMarkup()
        btn_cenoura = types.InlineKeyboardButton("🚫 Banir", callback_data=f"banir_{call.message.chat.id}")
        btn_iscas = types.InlineKeyboardButton("🔍 Verificar Banimento", callback_data=f"verificarban_{call.message.chat.id}")
        btn_5 = types.InlineKeyboardButton("❌ Cancelar", callback_data=f"pcancelar")
        markup.row(btn_cenoura, btn_iscas)
        markup.row(btn_5)

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Escolha o que deseja fazer:", reply_markup=markup)
    except Exception as e:
        import traceback
        traceback.print_exc()

def mostrar_opcoes_gif(call):
    try:
        markup = types.InlineKeyboardMarkup()
        btn_cenoura = types.InlineKeyboardButton("Alterar gif", callback_data=f"novogif")
        btn_iscas = types.InlineKeyboardButton("Deletar Gif", callback_data=f"delgif")
        btn_5 = types.InlineKeyboardButton("❌ Cancelar", callback_data=f"pcancelar")
        markup.row(btn_cenoura, btn_iscas)
        markup.row(btn_5)

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Escolha o que deseja fazer:", reply_markup=markup)
    except Exception as e:
        import traceback
        traceback.print_exc()

def mostrar_opcoes_adm(call):
    try:
        markup = types.InlineKeyboardMarkup()
        btn_cenoura = types.InlineKeyboardButton("🥕 Dar Cenouras", callback_data=f"dar_cenoura_{call.message.chat.id}")
        btn_iscas = types.InlineKeyboardButton("🐟 Dar Iscas", callback_data=f"dar_iscas_{call.message.chat.id}")
        btn_1 = types.InlineKeyboardButton("🥕 Tirar Cenouras", callback_data=f"tirar_cenoura_{call.message.chat.id}")
        btn_2 = types.InlineKeyboardButton("🐟 Tirar Iscas", callback_data=f"tirar_isca_{call.message.chat.id}")
        btn_5 = types.InlineKeyboardButton("❌ Cancelar", callback_data=f"pcancelar")
        markup.row(btn_cenoura, btn_iscas)
        markup.row(btn_1, btn_2)
        markup.row(btn_5)

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Escolha o que deseja fazer:", reply_markup=markup)
    except Exception as e:
        import traceback
        traceback.print_exc()

def processar_pagina_tag(call):
    try:
        parts = call.data.split('_')
        pagina = int(parts[1])
        nometag = parts[2]
        id_usuario = call.from_user.id 
        editar_mensagem_tag(call.message, nometag, pagina, id_usuario)
    except Exception as e:
        print(f"Erro ao processar callback de página para a tag: {e}")

