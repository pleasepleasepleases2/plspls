from bd import *
def processar_nome_usuario(message):
    nome_usuario = message.text.strip()

    if verificar_valor_existente("nome_usuario", nome_usuario):
        bot.send_message(message.chat.id, "O nome de usuário já está em uso.", reply_to_message_id=message.message_id)
        bot.send_message(message.chat.id, "Por favor, escolha um nome de usuário diferente:", reply_to_message_id=message.message_id)
        bot.register_next_step_handler(message, processar_nome_usuario)
    else:
        try:
            conn = mysql.connector.connect(**db_config())
            cursor = conn.cursor()
            query = "UPDATE usuarios SET nome_usuario = %s WHERE id_usuario = %s"
            cursor.execute(query, (nome_usuario, message.from_user.id))
            conn.commit()

            bot.send_message(message.chat.id, f"O nome de usuário '{nome_usuario}' foi registrado com sucesso.", reply_to_message_id=message.message_id)

        except mysql.connector.Error as err:
            bot.send_message(message.chat.id, f"Erro ao registrar nome de usuário: {err}", reply_to_message_id=message.message_id)
        finally:
            fechar_conexao(cursor, conn)

def registrar_usuario(id_usuario, nome_usuario, username):
    try:
        conn, cursor = conectar_banco_dados()
        
        if verificar_valor_existente("id_usuario", id_usuario):
            print(f"O usuário com ID {id_usuario} já existe na tabela. Nenhum novo registro é necessário.")
            return

        query = "INSERT INTO usuarios (id_usuario, nome_usuario, nome, qntcartas, fav, cenouras, iscas) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (id_usuario,username, nome_usuario,0,0,10,10))
        conn.commit()

        print(f"Registro para o usuário com ID {id_usuario} e nome {nome_usuario} inserido com sucesso.")

    except mysql.connector.Error as err:
        print(f"Erro ao registrar usuário: {err}")

    finally:
        fechar_conexao(cursor, conn)

def registrar_valor(coluna, valor, id_usuario):
    try:
        conn, cursor = conectar_banco_dados()
        if not verificar_valor_existente("id_usuario", id_usuario):
            query = f"INSERT INTO usuarios (id_usuario, {coluna}, qntcartas, cenouras, iscas, pp) VALUES (%s, %s, 0, 0, 0, 0)"
            cursor.execute(query, (id_usuario, valor))
            conn.commit()
            print(f"Novo registro adicionado para o ID do usuário {id_usuario}")

        else:
            query = f"UPDATE usuarios SET {coluna} = %s WHERE id_usuario = %s"
            cursor.execute(query, (valor, id_usuario))
            conn.commit()
            print(f"Valor {valor} registrado na coluna {coluna} para o ID do usuário {id_usuario}")

    except mysql.connector.Error as err:
        print(f"Erro ao registrar {coluna}: {err}")

    finally:
        fechar_conexao(cursor, conn)
        
def verificar_valor_existente(coluna, valor):
    try:
        conn, cursor = conectar_banco_dados()
        query = f"SELECT * FROM usuarios WHERE {coluna} = %s"
        cursor.execute(query, (valor,))
        resultado = cursor.fetchone()

        return resultado is not None

    except mysql.connector.Error as err:
        print(f"Erro ao verificar {coluna}: {err}")

    finally:
        fechar_conexao(cursor, conn)        
        
def qnt_carta(id_usuario):
    retry_attempts = 3

    for attempt in range(retry_attempts):
        try:
            conn, cursor = conectar_banco_dados()
            query_atualizar_qnt_cartas = """
                UPDATE usuarios u
                SET u.qntcartas = (
                    SELECT COALESCE(SUM(i.quantidade), 0)
                    FROM inventario i
                    WHERE i.id_usuario = %s
                )
                WHERE u.id_usuario = %s
            """
            cursor.execute(query_atualizar_qnt_cartas, (id_usuario, id_usuario))
            conn.commit()
            break
        except mysql.connector.Error as err:
            if err.errno == 1213:  # Deadlock detected
                print(f"Deadlock detected. Retrying... (Attempt {attempt + 1}/{retry_attempts})")
                conn.rollback()
            else:
                print(f"Erro ao atualizar quantidade total de cartas do usuário: {err}")
                break
        finally:
            fechar_conexao(cursor, conn)
def atualizar_coluna_usuario(id_usuario, coluna, novo_valor):
    try:
        conn, cursor = conectar_banco_dados()
        query = f"UPDATE usuarios SET {coluna} = %s WHERE id_usuario = %s"
        cursor.execute(query, (novo_valor, id_usuario))
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Erro ao atualizar {coluna}: {err}")
    finally:
        fechar_conexao(cursor, conn)    
