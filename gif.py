from pesquisas import *
from user import *
from bd import *
from loja import *
from gnome import *
from operacoes import *
from inventario import *
import re
import globals
def verifica_tempo_ultimo_gif(id_usuario):
    try:
        query_ultimo_gif = f"""
            SELECT MAX(data) AS ultima_data, MAX(horario) AS ultima_hora 
            FROM logs 
            WHERE id_usuario = {id_usuario} AND ação = 'gif'
        """
        conn, cursor = conectar_banco_dados()
        cursor.execute(query_ultimo_gif)
        ultimo_gif = cursor.fetchone()

        if ultimo_gif and ultimo_gif[0]:
            ultima_data_hora_str = f"{ultimo_gif[0]} {ultimo_gif[1]}"
            ultimo_gif_datetime = datetime.strptime(ultima_data_hora_str, "%Y-%m-%d %H:%M:%S")
            
            if ultimo_gif_datetime.date() == datetime.now().date():
                ultimo_gif_datetime = ultimo_gif_datetime.replace(year=datetime.now().year, month=datetime.now().month, day=datetime.now().day)
            
            diferenca_tempo = datetime.now() - ultimo_gif_datetime
            if diferenca_tempo.total_seconds() < 3600:
                tempo_restante = timedelta(seconds=(3600 - diferenca_tempo.total_seconds()))
                return tempo_restante
            else:
                return None
        else:
            return None

    except Exception as e:
        print(f"Erro ao verificar tempo do último gif: {e}")
    finally:
        fechar_conexao(cursor, conn)

def verifica_inventario(id_usuario, id_personagem):
    conn, cursor = conectar_banco_dados()
    query = f"SELECT quantidade FROM inventario WHERE id_usuario = {id_usuario} AND id_personagem = {id_personagem}"
    cursor.execute(query)
    quantidade_total = cursor.fetchone()[0]
    return quantidade_total > 29

def verifica_inventario_troca(id_usuario, id_personagem):
    conn, cursor = conectar_banco_dados()
    query = f"SELECT quantidade FROM inventario WHERE id_usuario = {id_usuario} AND id_personagem = {id_personagem}"
    cursor.execute(query)
    quantidade_total = cursor.fetchone()
    if quantidade_total is None:
        return 0  # Retorna 0 se a quantidade total for nula
    else:
        return quantidade_total[0]

def adicionar_atualizar_gif(id_personagem, id_usuario, link):
    try:
        conn, cursor = conectar_banco_dados()

        query_select = "SELECT idgif FROM gif WHERE id_personagem = %s AND id_usuario = %s"
        cursor.execute(query_select, (id_personagem, id_usuario))
        gif_existente = cursor.fetchone()

        if gif_existente:
            query_update = "UPDATE gif SET link = %s WHERE id_personagem = %s AND id_usuario = %s"
            cursor.execute(query_update, (link, id_personagem, id_usuario))
            conn.commit()
            return "GIF atualizado com sucesso!"
        else:
            query_insert = "INSERT INTO gif (id_personagem, id_usuario, link) VALUES (%s, %s, %s)"
            cursor.execute(query_insert, (id_personagem, id_usuario, link))
            conn.commit()
            return "GIF adicionado com sucesso!"

    except mysql.connector.Error as error:
        return f"Erro ao adicionar/atualizar GIF: {error}"

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def obter_dados_gif(message):
    try:
        parametros = message.text.split()
        if len(parametros) != 3:
            bot.reply_to(message, "Por favor, forneça exatamente três parâmetros: ID da pessoa, ID do personagem e link do GIF.")
            return

        id_personagem = int(parametros[0])
        id_usuario = int(parametros[1])
        link = parametros[2]

        resposta = adicionar_atualizar_gif(id_personagem, id_usuario, link)
        bot.reply_to(message, resposta)

    except ValueError:
        bot.reply_to(message, "Os IDs devem ser números inteiros.")


def processar_comando_gif(message):
    try:
        bot.reply_to(message, "Por favor, forneça  o ID do personagem, o ID da pessoa, e o link do GIF.")
        bot.register_next_step_handler(message, obter_dados_gif)

    except Exception as e:
        bot.reply_to(message, f"Erro ao processar comando /gif: {e}")

def deletar_gif(id_personagem, id_usuario):
    try:
        conn, cursor = conectar_banco_dados()
        query_select = "SELECT idgif FROM gif WHERE id_personagem = %s AND id_usuario = %s"
        cursor.execute(query_select, (id_personagem, id_usuario))
        gif_existente = cursor.fetchone()

        if gif_existente:
            query_delete = "DELETE FROM gif WHERE id_personagem = %s AND id_usuario = %s"
            cursor.execute(query_delete, (id_personagem, id_usuario))
            conn.commit()
            return "GIF deletado com sucesso!"
        else:
            return "Nenhum GIF encontrado para esse usuário e ID de personagem."

    except mysql.connector.Error as error:
        return f"Erro ao deletar GIF: {error}"

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
            
def processar_comando_delgif(message):
    try:
        bot.reply_to(message, "Por favor, forneça o ID do personagem e o ID do usuário.")
        bot.register_next_step_handler(message, obter_ids)

    except Exception as e:
        bot.reply_to(message, f"Erro ao processar comando /delgif: {e}")


def obter_ids(message):
    try:
        parametros = message.text.split()
        if len(parametros) != 2:
            bot.reply_to(message, "Por favor, forneça exatamente dois IDs.")
            return

        id_personagem = int(parametros[0])
        id_usuario = int(parametros[1])

        resposta = deletar_gif(id_personagem, id_usuario)
        bot.reply_to(message, resposta)

    except ValueError:
        bot.reply_to(message, "Os IDs devem ser números inteiros.")    
def aprovar_callback(call):
    try:
        data = call.data.replace('aprovar_', '').strip().split('_')

        conn, cursor = conectar_banco_dados()
        if len(data) == 3:
            id_usuario, id_personagem, message_id = data

            sql_temp_select = "SELECT valor FROM temp_data WHERE id_usuario = %s AND id_personagem = %s"
            values_temp_select = (id_usuario, id_personagem)
            cursor.execute(sql_temp_select, values_temp_select)
            link_gif = cursor.fetchone()
            cursor.fetchall()  

            if link_gif:
                sql_check_gif = "SELECT idgif FROM gif WHERE id_usuario = %s AND id_personagem = %s"
                cursor.execute(sql_check_gif, (id_usuario, id_personagem))
                existing_gif = cursor.fetchone()

                if existing_gif:
                    sql_update_gif = "UPDATE gif SET link = %s, timestamp = NOW() WHERE idgif = %s"
                    cursor.execute(sql_update_gif, (link_gif[0], existing_gif[0]))
                else:
                    sql_insert_gif = "INSERT INTO gif (id_personagem, id_usuario, link, timestamp) VALUES (%s, %s, %s, NOW())"
                    cursor.execute(sql_insert_gif, (id_personagem, id_usuario, link_gif[0]))

                conn.commit()
                mensagem = f"Seu GIF para o personagem {id_personagem} foi atualizado!"
                bot.send_message(id_usuario, mensagem)

                grupo_id = -1002144134360 
                nome_usuario = obter_nome_usuario_por_id(id_usuario)
                mensagem_grupo = f"🎉 O GIF para o personagem {id_personagem} de {nome_usuario} foi aprovado! 🎉"

                try:
                    bot.edit_message_text(mensagem_grupo, chat_id=grupo_id, message_id=int(message_id))
                except telebot.apihelper.ApiTelegramException as e:
                    if "message to edit not found" in str(e):
                        bot.send_message(grupo_id, mensagem_grupo)
                    else:
                        raise e
            else:
                print("Link do GIF não encontrado.")
                bot.send_message(call.message.chat.id, "Erro ao aprovar o GIF. Link não encontrado.")
        else:
            print("Formato de callback incorreto. Esperado: 'aprovar_id_usuario_id_personagem_message_id'.")
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        fechar_conexao(cursor, conn)

def reprovar_callback(call):
    try:
        data = call.data.replace('reprovar_', '').strip().split('_')
        if len(data) == 3:
            id_usuario, id_personagem, message_id = data
            mensagem = f"Seu gif para o personagem {id_personagem} foi recusado"
            bot.send_message(id_usuario, mensagem)

            grupo_id = -1002144134360
            nome_usuario = obter_nome_usuario_por_id(id_usuario)
            mensagem_grupo = f"O GIF para o personagem {id_personagem} de {nome_usuario} foi reprovado... 😐"
            bot.edit_message_text(mensagem_grupo, chat_id=grupo_id, message_id=int(message_id))
        else:
            print("Formato de callback incorreto. Esperado: 'reprovar_id_usuario_id_personagem_message_id'")
    except Exception as e:
        print(f"Erro ao processar reprovar_callback: {e}")

def deletar_gif_usuario(id_usuario, id_personagem):
    try:
        conn, cursor = conectar_banco_dados()
        query_select = "SELECT idgif FROM gif WHERE id_usuario = %s AND id_personagem = %s"
        cursor.execute(query_select, (id_usuario, id_personagem))
        gif_existente = cursor.fetchone()

        if gif_existente:
            query_delete = "DELETE FROM gif WHERE id_personagem = %s AND id_usuario = %s"
            cursor.execute(query_delete, (id_personagem, id_usuario))
            conn.commit()
            return "GIF deletado com sucesso!"
        else:
            return "Nenhum GIF encontrado para esse personagem no seu inventário."

    except mysql.connector.Error as error:
        return f"Erro ao deletar GIF: {error}"

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def processar_comando_delgif(message):
    try:
        parametros = message.text.split()
        if len(parametros) != 2:
            bot.reply_to(message, "Por favor, forneça o comando no formato: /delgif <ID_do_personagem>")
            return

        id_usuario = message.from_user.id
        id_personagem = int(parametros[1])

        resposta = deletar_gif_usuario(id_usuario, id_personagem)
        bot.reply_to(message, resposta)

    except ValueError:
        bot.reply_to(message, "O ID do personagem deve ser um número inteiro.")
    except Exception as e:
        bot.reply_to(message, f"Erro ao processar comando /delgif: {e}")

def receber_link_gif(message, id_personagem):
    id_usuario = message.from_user.id

    if id_usuario:
        link_gif = message.text

        if not re.match(r'^https?://\S+$', link_gif):
            bot.send_message(message.chat.id, "Por favor, envie <b>apenas</b> o <b>link</b> do GIF.", parse_mode="HTML")
            return

        if id_usuario in globals.links_gif:
            id_personagem = globals.links_gif[id_usuario]

            if id_personagem:
                numero_personagem = id_personagem.split('_')[0]
                conn, cursor = conectar_banco_dados()

                sql_usuario = "SELECT nome_usuario, nome FROM usuarios WHERE id_usuario = %s"
                cursor.execute(sql_usuario, (id_usuario,))
                resultado_usuario = cursor.fetchone()

                sql_personagem = "SELECT nome, subcategoria FROM personagens WHERE id_personagem = %s"
                cursor.execute(sql_personagem, (numero_personagem,))
                resultado_personagem = cursor.fetchone()

                if resultado_usuario and resultado_personagem:
                    nome_usuario = resultado_usuario[0]
                    nome_personagem = resultado_personagem[0]
                    subcategoria_personagem = resultado_personagem[1]

                    sql_temp_insert = """
                        INSERT INTO temp_data (id_usuario, id_personagem, chave, valor)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE valor = VALUES(valor), chave = VALUES(chave)
                    """
                    chave = f"{id_usuario}_{numero_personagem}"
                    cursor.execute(sql_temp_insert, (id_usuario, numero_personagem, chave, link_gif))
                    conn.commit()
                    fechar_conexao(cursor, conn)

                    keyboard = telebot.types.InlineKeyboardMarkup()
                    btn_aprovar = telebot.types.InlineKeyboardButton(text="✔️ Aprovar", callback_data=f"aprovar_{id_usuario}_{numero_personagem}_{message.message_id}")
                    btn_reprovar = telebot.types.InlineKeyboardButton(text="❌ Reprovar", callback_data=f"reprovar_{id_usuario}_{numero_personagem}_{message.message_id}")

                    keyboard.row(btn_aprovar, btn_reprovar)
                    bot.forward_message(chat_id=-1002144134360, from_chat_id=message.chat.id, message_id=message.message_id)
                    chat_id = -1002144134360
                    mensagem = f"Pedido de aprovação de GIF:\n\n"
                    mensagem += f"ID Personagem: {numero_personagem}\n"
                    mensagem += f"{nome_personagem} de {subcategoria_personagem}\n\n"
                    mensagem += f"Usuário: @{message.from_user.username}\n"
                    mensagem += f"Nome: {nome_usuario}\n"

                    sent_message = bot.send_message(chat_id, mensagem, reply_markup=keyboard)
                    bot.send_message(message.chat.id, "Link do GIF registrado com sucesso. Aguardando aprovação.")
                    return sent_message.message_id
                else:
                    fechar_conexao(cursor, conn)
                    bot.send_message(message.chat.id, "Erro ao obter informações do usuário ou do personagem.")
            else:
                bot.send_message(message.chat.id, "Erro ao processar o link do GIF. Por favor, use o comando /setgif novamente.")
        else:
            bot.send_message(message.chat.id, "Erro ao processar o link do GIF. ID de usuário inválido.")
    else:
        bot.send_message(message.chat.id, "Erro ao processar o link do GIF. ID de usuário inválido.")
