from pesquisas import *
from user import *
from bd import *
from loja import *
from gnome import *

# Função para verificar se um ID de usuário está na tabela ban
def verificar_ban(id_usuario):
    try:
        conn, cursor = conectar_banco_dados()
        
        # Consultar a tabela ban para verificar se o ID está presente
        cursor.execute("SELECT * FROM ban WHERE iduser = %s", (str(id_usuario),))
        ban_info = cursor.fetchone()

        if ban_info:
            # Se o ID estiver na tabela ban, informar motivo e nome
            motivo = ban_info[3]
            nome = ban_info[2]
            return True, motivo, nome
        else:
            # Se o ID não estiver na tabela ban
            return False, None, None

    except Exception as e:
        print(f"Erro ao verificar na tabela ban: {e}")
        return False, None, None                    
    finally:
        fechar_conexao(cursor, conn)
        
def verificar_autorizacao(id_usuario):
    try:
        conn, cursor = conectar_banco_dados()
        cursor.execute("SELECT adm FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        result = cursor.fetchone()

        if result and result[0] is not None:
            return True  
        else:
            return False  
    except Exception as e:
        print(f"Erro ao verificar autorização: {e}")
        return False  

    finally:
   
        if conn.is_connected():
            cursor.close()
            conn.close()

def inserir_na_tabela_beta(id_usuario, nome):
    try:
        conn, cursor = conectar_banco_dados()
        cursor.execute("INSERT INTO beta (id, nome) VALUES (%s, %s)", (id_usuario, nome))
        conn.commit()  

        return True  

    except Exception as e:
        print(f"Erro ao inserir na tabela beta: {e}")
        return False  

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
            

def excluir_da_tabela_beta(id_usuario):
    try:
        conn, cursor = conectar_banco_dados()
        cursor.execute("DELETE FROM beta WHERE id = %s", (id_usuario,))
        conn.commit()  

        return True  

    except Exception as e:
        print(f"Erro ao excluir da tabela beta: {e}")
        return False  #
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def remover_id_cenouras(message):
    try:
        parts = message.text.split()
        if len(parts) == 2:
            id_pessoa = int(parts[0])
            quantidade_cenouras = int(parts[1])
            conn, cursor = conectar_banco_dados()

            cursor.execute("SELECT cenouras FROM usuarios WHERE id_usuario = %s", (id_pessoa,))
            result = cursor.fetchone()
            if result:
                quantidade_atual = result[0]
                nova_quantidade = quantidade_atual - quantidade_cenouras

                cursor.execute("UPDATE usuarios SET cenouras = %s WHERE id_usuario = %s", (nova_quantidade, id_pessoa))
                conn.commit()
                fechar_conexao(cursor, conn)

                bot.send_message(message.chat.id, f"A quantidade de cenouras foi atualizada para {nova_quantidade} para o usuário com ID {id_pessoa}.")
            else:
                bot.send_message(message.chat.id, f"ID de usuário inválido.")

        else:
            bot.send_message(message.chat.id, "Formato incorreto. Envie o ID da pessoa e a quantidade de cenouras a ser adicionada, separados por espaço.")

    except Exception as e:
        print(f"Erro ao obter ID e quantidade de cenouras: {e}")
        bot.send_message(message.chat.id, "Ocorreu um erro ao processar a solicitação.")
                
def remover_id_iscas(message):
    try:
        parts = message.text.split()
        if len(parts) == 2:
            id_pessoa = int(parts[0])
            quantidade_iscas = int(parts[1])

            conn, cursor = conectar_banco_dados()

            cursor.execute("SELECT iscas FROM usuarios WHERE id_usuario = %s", (id_pessoa,))
            result = cursor.fetchone()

            if result:
                quantidade_atual = result[0]
                nova_quantidade = quantidade_atual - quantidade_iscas

                cursor.execute("UPDATE usuarios SET iscas = %s WHERE id_usuario = %s", (nova_quantidade, id_pessoa))
                conn.commit()

                fechar_conexao(cursor, conn)

                bot.send_message(message.chat.id, f"A quantidade de iscas foi atualizada para {nova_quantidade} para o usuário com ID {id_pessoa}.")
            else:
                bot.send_message(message.chat.id, f"ID de usuário inválido.")

        else:
            bot.send_message(message.chat.id, "Formato incorreto. Envie o ID da pessoa e a quantidade de cenouras a ser adicionada, separados por espaço.")

    except Exception as e:
        print(f"Erro ao obter ID e quantidade de cenouras: {e}")
        bot.send_message(message.chat.id, "Ocorreu um erro ao processar a solicitação.")
                    
def obter_id_cenouras(message):
    try:
        parts = message.text.split()
        if len(parts) == 2:
            id_pessoa = int(parts[0])
            quantidade_cenouras = int(parts[1])
            conn, cursor = conectar_banco_dados()

            cursor.execute("SELECT cenouras FROM usuarios WHERE id_usuario = %s", (id_pessoa,))
            result = cursor.fetchone()

            if result:
                quantidade_atual = result[0]
                nova_quantidade = quantidade_atual + quantidade_cenouras

                cursor.execute("UPDATE usuarios SET cenouras = %s WHERE id_usuario = %s", (nova_quantidade, id_pessoa))
                conn.commit()

                fechar_conexao(cursor, conn)

                bot.send_message(message.chat.id, f"A quantidade de cenouras foi atualizada para {nova_quantidade} para o usuário com ID {id_pessoa}.")
            else:
                bot.send_message(message.chat.id, f"ID de usuário inválido.")

        else:
            bot.send_message(message.chat.id, "Formato incorreto. Envie o ID da pessoa e a quantidade de cenouras a ser adicionada, separados por espaço.")

    except Exception as e:
        print(f"Erro ao obter ID e quantidade de cenouras: {e}")
        bot.send_message(message.chat.id, "Ocorreu um erro ao processar a solicitação.")
                
def obter_id_iscas(message):
    try:
        parts = message.text.split()
        if len(parts) == 2:
            id_pessoa = int(parts[0])
            quantidade_iscas = int(parts[1])

            conn, cursor = conectar_banco_dados()

            cursor.execute("SELECT iscas FROM usuarios WHERE id_usuario = %s", (id_pessoa,))
            result = cursor.fetchone()

            if result:
                quantidade_atual = result[0]
                nova_quantidade = quantidade_atual + quantidade_iscas

                cursor.execute("UPDATE usuarios SET iscas = %s WHERE id_usuario = %s", (nova_quantidade, id_pessoa))
                conn.commit()

                fechar_conexao(cursor, conn)

                bot.send_message(message.chat.id, f"A quantidade de iscas foi atualizada para {nova_quantidade} para o usuário com ID {id_pessoa}.")
            else:
                bot.send_message(message.chat.id, f"ID de usuário inválido.")

        else:
            bot.send_message(message.chat.id, "Formato incorreto. Envie o ID da pessoa e a quantidade de iscas a ser adicionada, separados por espaço.")

    except Exception as e:
        print(f"Erro ao obter ID e quantidade de cenouras: {e}")
        bot.send_message(message.chat.id, "Ocorreu um erro ao processar a solicitação.")

def obter_id_beta(message):
    id_usuario = message.text.strip()
    bot.send_message(message.chat.id, "Por favor, envie o nome da pessoa:")
    bot.register_next_step_handler(message, lambda msg: obter_nome_beta(msg, id_usuario))

def obter_nome_beta(message, id_usuario):
    nome = message.text.strip()
    if inserir_na_tabela_beta(id_usuario, nome):
        bot.reply_to(message, "Usuário adicionado à lista beta com sucesso!")
    else:
        bot.reply_to(message, "Erro ao adicionar usuário à lista beta.")
        
def remover_beta(message):
    id_usuario = message.text

    if excluir_da_tabela_beta(id_usuario):
        bot.reply_to(message, "Usuário excluido com sucesso!")
    else:
        bot.reply_to(message, "Erro ao excluir usuário à lista beta.")
def processar_gift_cards(message):
    conn, cursor = conectar_banco_dados()
    try:
        # Verifica se o usuário é autorizado
        if message.from_user.id not in [5532809878, 1805086442]:
            bot.reply_to(message, "Você não tem permissão para usar esse comando.")
            return

        # Tenta dividir a mensagem e converter os valores
        _, quantity, card_id, user_id = message.text.split()
        quantity = int(quantity)
        card_id = int(card_id)
        user_id = int(user_id)

        # Chama a função para adicionar as cartas
        gift_cards(quantity, card_id, user_id)
        bot.reply_to(message, f"{quantity} cartas adicionadas com sucesso!")

    except (ValueError, IndexError):
        bot.reply_to(message, "Formato incorreto. Use o formato: /gift <quantidade> <card_id> <user_id>")
    finally:
        fechar_conexao(cursor, conn)


def processar_addbanco(message):
    try:
        conn, cursor = conectar_banco_dados()
        partes_comando = message.text.split()

        if len(partes_comando) != 2:
            bot.send_message(message.chat.id, "Uso correto: /addbanco <id_usuario>")
            return

        id_usuario = int(partes_comando[1])

        # Obter as cartas do inventário do usuário
        cursor.execute("SELECT id_personagem, quantidade FROM inventario WHERE id_usuario = %s", (id_usuario,))
        cartas_usuario = cursor.fetchall()

        if not cartas_usuario:
            bot.send_message(message.chat.id, "Usuário não possui cartas.")
            return

        # Transferir as cartas para o banco
        for id_personagem, quantidade in cartas_usuario:
            cursor.execute("SELECT COUNT(*) FROM banco_inventario WHERE id_personagem = %s", (id_personagem,))
            existe = cursor.fetchone()[0]

            if existe:
                cursor.execute("UPDATE banco_inventario SET quantidade = quantidade + %s WHERE id_personagem = %s", (quantidade, id_personagem))
            else:
                cursor.execute("INSERT INTO banco_inventario (id_personagem, quantidade) VALUES (%s, %s)", (id_personagem, quantidade))

        # Remover cartas do usuário
        cursor.execute("DELETE FROM inventario WHERE id_usuario = %s", (id_usuario,))
        conn.commit()

        bot.send_message(message.chat.id, f"Cartas do usuário {id_usuario} transferidas para o banco com sucesso.")

    except Exception as e:
        print(f"Erro ao transferir cartas para o banco: {e}")
        bot.send_message(message.chat.id, "Erro ao transferir cartas para o banco.")
    finally:
        fechar_conexao(cursor, conn)


def obter_nome_usuario(id_usuario, cursor):
    query = "SELECT nome FROM usuarios WHERE id_usuario = %s"
    cursor.execute(query, (id_usuario,))
    resultado = cursor.fetchone()
    return resultado[0] if resultado else "Usuário Desconhecido"

