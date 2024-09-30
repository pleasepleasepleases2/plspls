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

