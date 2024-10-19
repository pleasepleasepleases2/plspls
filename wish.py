from pesquisas import *
from user import *
from bd import *
from loja import *
from gnome import *
from operacoes import *

grupodeerro = -4279935414
@bot.message_handler(commands=['wishlist'])
def verificar_cartas(message):
    try:
        conn, cursor = conectar_banco_dados()
        id_usuario = message.from_user.id

        sql_wishlist = f"""
            SELECT w.id_personagem, p.id_personagem, p.nome AS nome_personagem, p.subcategoria, p.emoji
            FROM wishlist w
            JOIN personagens p ON w.id_personagem = p.id_personagem
            WHERE w.id_usuario = {id_usuario}
        """

        cursor.execute(sql_wishlist)
        cartas_wishlist = cursor.fetchall()

        if cartas_wishlist:
            cartas_removidas = []

            for carta_wishlist in cartas_wishlist:
                id_personagem_wishlist = carta_wishlist[0]
                id_carta_wishlist = carta_wishlist[1]
                nome_carta_wishlist = carta_wishlist[2]
                subcategoria_carta_wishlist = carta_wishlist[3]
                emoji_carta_wishlist = carta_wishlist[4]
                cursor.execute("SELECT COUNT(*) FROM inventario WHERE id_usuario = %s AND id_personagem = %s",
                               (id_usuario, id_personagem_wishlist))
                existing_inventory_count = cursor.fetchone()[0]
                inventory_exists = existing_inventory_count > 0

                if inventory_exists:
                    cursor.execute("DELETE FROM wishlist WHERE id_usuario = %s AND id_personagem = %s",
                                   (id_usuario, id_personagem_wishlist))
                    cartas_removidas.append(
                        f"{emoji_carta_wishlist} {id_carta_wishlist} - {nome_carta_wishlist} de {subcategoria_carta_wishlist}")

            sql_atualizada = f"""
                SELECT p.emoji, p.id_personagem, p.nome AS nome_personagem, p.subcategoria
                FROM personagens p
                JOIN wishlist w ON p.id_personagem = w.id_personagem
                WHERE w.id_usuario = {id_usuario}
            """

            cursor.execute(sql_atualizada)
            cartas_atualizadas = cursor.fetchall()

            if cartas_atualizadas:
                lista_wishlist_atualizada = f"⭐️ | Cartas no armazem de {message.from_user.first_name}:\n\n"
                for carta_atualizada in cartas_atualizadas:
                    emoji_carta = carta_atualizada[0]
                    id_carta = carta_atualizada[1]
                    nome_carta = carta_atualizada[2]
                    subcategoria_carta = carta_atualizada[3]
                    lista_wishlist_atualizada += f"{emoji_carta} {id_carta} - {nome_carta} de {subcategoria_carta}\n"

                bot.send_message(message.chat.id, lista_wishlist_atualizada, reply_to_message_id=message.message_id)
            else:
                bot.send_message(message.chat.id, "Sua Wishlist está vazia :)", reply_to_message_id=message.message_id)

            if cartas_removidas:
                resposta = f"Algumas cartas foram removidas da wishlist porque já estão no inventário:\n{', '.join(map(str, cartas_removidas))}"
                bot.send_message(message.chat.id, resposta, reply_to_message_id=message.message_id)

        else:
            bot.send_message(message.chat.id, "Sua Wishlist está vazia :)", reply_to_message_id=message.message_id)
    except Exception  as err:
        print(f"Erro de SQL: {err}")
        traceback.print_exc()
        erro = traceback.format_exc()
        mensagem = f"carta com erro: {id_personagem}. erro: {e}\n{erro}"
        bot.send_message(grupodeerro, mensagem, parse_mode="HTML")

        bot.send_message(message.chat.id, mensagem, reply_to_message_id=message.message_id)
    finally:
        conn.commit() 
        fechar_conexao(cursor, conn)

@bot.message_handler(commands=['addw'])
def add_to_wish(message):
    try:
        chat_id = message.chat.id
        id_usuario = message.from_user.id
        command_parts = message.text.split()
        if len(command_parts) == 2:
            id_personagem = command_parts[1]

            conn, cursor = conectar_banco_dados()
            cursor.execute("SELECT COUNT(*) FROM wishlist WHERE id_usuario = %s AND id_personagem = %s",
                           (id_usuario, id_personagem))
            existing_wishlist_count = cursor.fetchone()[0]
            wishlist_exists = existing_wishlist_count > 0

            if wishlist_exists:
                bot.send_message(chat_id, "Você já possui essa carta na wishlist!", reply_to_message_id=message.message_id)
            else:
                cursor.execute("SELECT COUNT(*) FROM inventario WHERE id_usuario = %s AND id_personagem = %s",
                               (id_usuario, id_personagem))
                existing_inventory_count = cursor.fetchone()[0]
                inventory_exists = existing_inventory_count > 0

                if inventory_exists:
                    bot.send_message(chat_id, "Você já possui essa carta no inventário!", reply_to_message_id=message.message_id)
                else:
                    cursor.execute("INSERT INTO wishlist (id_personagem, id_usuario) VALUES (%s, %s)",
                                   (id_personagem, id_usuario))
                    bot.send_message(chat_id, "Carta adicionada à sua wishlist!\nBoa sorte!", reply_to_message_id=message.message_id)
            conn.commit()
    except mysql.connector.Error as err:
        traceback.print_exc()
        erro = traceback.format_exc()
        mensagem = f"wishlist com erro: {id_personagem}. erro: {e}\n{erro}"
        bot.send_message(grupodeerro, mensagem, parse_mode="HTML")
    finally:
        fechar_conexao(cursor, conn)

@bot.message_handler(commands=['removew'])
def remover_da_wishlist(message):
    try:
        chat_id = message.chat.id
        id_usuario = message.from_user.id
        command_parts = message.text.split()
        if len(command_parts) == 2:
            id_personagem = command_parts[1]
            
        print(f"ID do usuário: {id_usuario}")
        print(f"ID da carta: {id_personagem}")

        conn, cursor = conectar_banco_dados()
        cursor.execute("SELECT COUNT(*) FROM wishlist WHERE id_usuario = %s AND id_personagem = %s",
                       (id_usuario, id_personagem))
        existing_carta_count = cursor.fetchone()[0]

        if existing_carta_count > 0:
            cursor.execute("DELETE FROM wishlist WHERE id_usuario = %s AND id_personagem = %s",
                           (id_usuario, id_personagem))
            bot.send_message(chat_id=chat_id, text="Carta removida da sua wishlist!", reply_to_message_id=message.message_id)
        else:
            bot.send_message(chat_id=chat_id, text="Você não possui essa carta na wishlist.", reply_to_message_id=message.message_id)
        conn.commit()

    except mysql.connector.Error as err:
        print(f"Erro ao remover carta da wishlist: {err}")
    finally:
        fechar_conexao(cursor, conn)

def verificar_cartas(message):
    try:
        conn, cursor = conectar_banco_dados()
        id_usuario = message.from_user.id

        sql_wishlist = f"""
            SELECT p.id_personagem, 
                   p.nome COLLATE utf8mb4_general_ci AS nome_personagem, 
                   p.subcategoria COLLATE utf8mb4_general_ci AS subcategoria, 
                   p.emoji COLLATE utf8mb4_general_ci AS emoji
            FROM wishlist w
            JOIN personagens p ON w.id_personagem = p.id_personagem
            WHERE w.id_usuario = {id_usuario}
            
            UNION
            
            SELECT e.id_personagem, 
                   e.nome COLLATE utf8mb4_general_ci AS nome_personagem, 
                   e.subcategoria COLLATE utf8mb4_general_ci AS subcategoria, 
                   e.emoji COLLATE utf8mb4_general_ci AS emoji
            FROM wishlist w
            JOIN evento e ON w.id_personagem = e.id_personagem
            WHERE w.id_usuario = {id_usuario}
        """

        cursor.execute(sql_wishlist)
        cartas_wishlist = cursor.fetchall()

        if cartas_wishlist:
            cartas_removidas = []

            for carta_wishlist in cartas_wishlist:
                id_personagem_wishlist = carta_wishlist[0]
                nome_carta_wishlist = carta_wishlist[1]
                subcategoria_carta_wishlist = carta_wishlist[2]
                emoji_carta_wishlist = carta_wishlist[3]

                cursor.execute("SELECT COUNT(*) FROM inventario WHERE id_usuario = %s AND id_personagem = %s",
                               (id_usuario, id_personagem_wishlist))
                existing_inventory_count = cursor.fetchone()[0]
                inventory_exists = existing_inventory_count > 0

                if inventory_exists:
                    cursor.execute("DELETE FROM wishlist WHERE id_usuario = %s AND id_personagem = %s",
                                   (id_usuario, id_personagem_wishlist))
                    cartas_removidas.append(f"{emoji_carta_wishlist} - {nome_carta_wishlist} de {subcategoria_carta_wishlist}")

            if cartas_removidas:
                resposta = f"Algumas cartas foram removidas da wishlist porque já estão no seu inventário:\n{', '.join(map(str, cartas_removidas))}"
                bot.send_message(message.chat.id, resposta, reply_to_message_id=message.message_id)

            lista_wishlist_atualizada = f"🤞 | Cartas na wishlist de {message.from_user.first_name}:\n\n"
            for carta_atualizada in cartas_wishlist:
                id_carta = carta_atualizada[0]
                emoji_carta = carta_atualizada[3]
                nome_carta = carta_atualizada[1]
                subcategoria_carta = carta_atualizada[2]
                lista_wishlist_atualizada += f"{emoji_carta} ∙ <code>{id_carta}</code> - {nome_carta} de {subcategoria_carta}\n"

            bot.send_message(message.chat.id, lista_wishlist_atualizada, reply_to_message_id=message.message_id, parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, "Sua wishlist está vazia! Devo te desejar parabéns?", reply_to_message_id=message.message_id)

    except mysql.connector.Error as err:
        print(f"Erro de SQL: {err}")
        traceback.print_exc()
        erro = traceback.format_exc()
        mensagem = f"wish com erro: {id_personagem}. erro: {err}\n{erro}"
        bot.send_message(grupodeerro, mensagem, parse_mode="HTML")
        bot.send_message(message.chat.id, "Ocorreu um erro ao processar a consulta no banco de dados.", reply_to_message_id=message.message_id)
    except ValueError as e:
        print(f"Erro: {e}")
        mensagem_banido = "Um erro ocorreu ao abrir seu armazém... Tente trocar seu fav usando o </code>comando /setfav</code>. Caso não resolva, entre em contato com o suporte."
        bot.send_message(message.chat.id, mensagem_banido)
    except telebot.apihelper.ApiHTTPException as e:
        print(f"Erro na API do Telegram: {e}")
    finally:
        conn.commit() 
        fechar_conexao(cursor, conn)

def add_to_wish(message):
    try:
        chat_id = message.chat.id
        id_usuario = message.from_user.id
        command_parts = message.text.split()
        if len(command_parts) == 2:
            id_personagem = command_parts[1]

            conn, cursor = conectar_banco_dados()
            cursor.execute("SELECT COUNT(*) FROM wishlist WHERE id_usuario = %s AND id_personagem = %s",
                           (id_usuario, id_personagem))
            existing_wishlist_count = cursor.fetchone()[0]
            wishlist_exists = existing_wishlist_count > 0

            if wishlist_exists:
                bot.send_message(chat_id, "Você já possui essa carta na wishlist!", reply_to_message_id=message.message_id)
            else:
                cursor.execute("SELECT COUNT(*) FROM inventario WHERE id_usuario = %s AND id_personagem = %s",
                               (id_usuario, id_personagem))
                existing_inventory_count = cursor.fetchone()[0]
                inventory_exists = existing_inventory_count > 0

                if inventory_exists:
                    bot.send_message(chat_id, "Você já possui essa carta no inventário!", reply_to_message_id=message.message_id)
                else:
                    cursor.execute("INSERT INTO wishlist (id_personagem, id_usuario) VALUES (%s, %s)",
                                   (id_personagem, id_usuario))
                    bot.send_message(chat_id, "Carta adicionada à sua wishlist!\nBoa sorte!", reply_to_message_id=message.message_id)
            conn.commit()
    except mysql.connector.Error as err:
        print(f"Erro ao adicionar carta à wishlist: {err}")
    finally:
        fechar_conexao(cursor, conn)

def remover_da_wishlist(message):
    try:
        chat_id = message.chat.id
        id_usuario = message.from_user.id
        command_parts = message.text.split()
        if len(command_parts) == 2:
            id_personagem = command_parts[1]
            
        conn, cursor = conectar_banco_dados()
        cursor.execute("SELECT COUNT(*) FROM wishlist WHERE id_usuario = %s AND id_personagem = %s",
                       (id_usuario, id_personagem))
        existing_carta_count = cursor.fetchone()[0]

        if existing_carta_count > 0:
            cursor.execute("DELETE FROM wishlist WHERE id_usuario = %s AND id_personagem = %s",
                           (id_usuario, id_personagem))
            bot.send_message(chat_id=chat_id, text="Carta removida da sua wishlist!", reply_to_message_id=message.message_id)
        else:
            bot.send_message(chat_id=chat_id, text="Você não possui essa carta na wishlist.", reply_to_message_id=message.message_id)
        conn.commit()

    except mysql.connector.Error as err:
        print(f"Erro ao remover carta da wishlist: {err}")
    finally:
        fechar_conexao(cursor, conn)
