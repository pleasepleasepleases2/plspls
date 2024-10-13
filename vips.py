

def processar_id_vip(message):
    try:
        id_usuario = int(message.text)
        msg = bot.reply_to(message, "Por favor, envie o nome do usuário.")
        bot.register_next_step_handler(msg, lambda msg: processar_nome_vip(msg, id_usuario))
    except ValueError:
        bot.reply_to(message, "ID inválido. Por favor, tente novamente.")


def processar_nome_vip(message, id_usuario):
    nome = message.text
    msg = bot.reply_to(message, "Informe a data de pagamento (formato: AAAA-MM-DD):")
    bot.register_next_step_handler(msg, lambda msg: processar_pagamento_vip(msg, id_usuario, nome))


def processar_pagamento_vip(message, id_usuario, nome):
    try:
        data_pagamento = message.text
        conn, cursor = conectar_banco_dados()
        
        # Inserir o novo VIP na tabela
        cursor.execute(
            "INSERT INTO vips (id_usuario, nome, data_pagamento, mes_atual) VALUES (%s, %s, %s, DATE_FORMAT(NOW(), '%Y-%m'))",
            (id_usuario, nome, data_pagamento)
        )
        conn.commit()

        bot.reply_to(message, f"{nome} foi adicionado(a) como VIP com sucesso!")
    except Exception as e:
        bot.reply_to(message, f"Erro ao adicionar VIP: {e}")
    finally:
        fechar_conexao(cursor, conn)

  # Função para verificar quanto tempo falta para a próxima pétala
def calcular_tempo_restante(id_usuario):
    conn, cursor = conectar_banco_dados()
    cursor.execute("SELECT ultima_regeneracao_petalas FROM usuarios WHERE id_usuario = %s", (id_usuario,))
    resultado = cursor.fetchone()
    
    if resultado:
        ultima_regeneracao = resultado[0]
        agora = datetime.now()

        # Verificar se o usuário é VIP e ajustar o tempo de regeneração
        vip = is_vip(id_usuario)
        if vip:
            TEMPO_REGENERACAO = timedelta(hours=2)
        else:
            TEMPO_REGENERACAO = timedelta(hours=3)

        # Calcular o tempo até a próxima regeneração de pétalas
        tempo_restante = TEMPO_REGENERACAO - (agora - ultima_regeneracao)
        if tempo_restante.total_seconds() > 0:
            horas, resto = divmod(tempo_restante.total_seconds(), 3600)
            minutos, _ = divmod(resto, 60)
            return f"{int(horas)}h {int(minutos)}min"
        else:
            return "menos de 1 minuto"

    fechar_conexao(cursor, conn)
    return "um pouco mais"

def processar_remocao_vip(message):
    try:
        id_usuario = int(message.text)
        conn, cursor = conectar_banco_dados()
        
        # Remover o VIP da tabela
        cursor.execute("DELETE FROM vips WHERE id_usuario = %s", (id_usuario,))
        conn.commit()

        bot.reply_to(message, "VIP removido com sucesso!")
    except Exception as e:
        bot.reply_to(message, f"Erro ao remover VIP: {e}")
    finally:
        fechar_conexao(cursor, conn)
def verificar_pedidos_vip(id_usuario):
    conn, cursor = conectar_banco_dados()
    
    cursor.execute(
        "SELECT pedidos_restantes, mes_atual FROM vips WHERE id_usuario = %s",
        (id_usuario,)
    )
    vip_data = cursor.fetchone()
    fechar_conexao(cursor, conn)
    
    if vip_data:
        pedidos_restantes, mes_atual = vip_data
        mes_atual_sistema = datetime.now().strftime('%Y-%m')
        
        if mes_atual != mes_atual_sistema:
            # Reiniciar pedidos para o novo mês
            pedidos_restantes = 4
            atualizar_pedidos_vip(id_usuario, pedidos_restantes, mes_atual_sistema)
        
        return pedidos_restantes
    else:
        return None


def atualizar_pedidos_vip(id_usuario, novos_pedidos, novo_mes):
    conn, cursor = conectar_banco_dados()
    
    cursor.execute(
        "UPDATE vips SET pedidos_restantes = %s, mes_atual = %s WHERE id_usuario = %s",
        (novos_pedidos, novo_mes, id_usuario)
    )
    conn.commit()
    fechar_conexao(cursor, conn)

def is_vip(id_usuario):
    """Verifica se o usuário é VIP consultando a tabela vips."""
    conn, cursor = conectar_banco_dados()
    
    # Verifica se o usuário está na tabela de VIPs
    cursor.execute("SELECT id_usuario FROM vips WHERE id_usuario = %s", (id_usuario,))
    resultado = cursor.fetchone()  # Usa fetchone para obter um único resultado

    # Fechar o cursor e a conexão
    cursor.fetchall()  # Garante que todos os resultados foram processados, se houver
    fechar_conexao(cursor, conn)

    # Retorna True se o usuário for VIP, False caso contrário
    return resultado is not None

def processar_pedido_submenu(message, pedidos_restantes, user_name):
    chat_id = message.chat.id
    texto_submenu = message.text

    # Verificar se o texto está no formato esperado
    try:
        if not validar_formato_submenu(texto_submenu):
            bot.send_message(chat_id, "Formato incorreto. Certifique-se de seguir o exemplo:\n- subcategoria:\n- submenu:\npersonagem1nome, link da foto\npersonagem2nome, link da foto")
            return

        # Reduzir o número de pedidos restantes no banco de dados
        conn, cursor = conectar_banco_dados()
        cursor.execute("UPDATE vips SET pedidos_restantes = pedidos_restantes - 1 WHERE id_usuario = %s", (message.from_user.id,))
        conn.commit()

        # Enviar o pedido para o grupo
        grupo_id = -1002024419694  # ID do grupo para encaminhar os pedidos
        mensagem_grupo = (
            f"📩 Novo pedido de submenu de {user_name}!\n\n"
            f"Pedidos restantes: {pedidos_restantes - 1}\n\n"
            f"Submenu enviado:\n\n{texto_submenu}"
        )
        bot.send_message(grupo_id, mensagem_grupo)

        bot.send_message(chat_id, "Seu pedido foi encaminhado com sucesso!")
    except Exception as e:
        bot.send_message(chat_id, "Ocorreu um erro ao processar seu pedido. Tente novamente.")
        print(f"Erro ao processar pedido de submenu: {e}")
    finally:
        fechar_conexao(cursor, conn)


def validar_formato_submenu(texto):
    # Verifica se o texto contém os itens básicos do submenu
    linhas = texto.splitlines()
    if len(linhas) < 4:
        return False

    # Verifica a presença das chaves "subcategoria" e "submenu"
    if not linhas[0].lower().startswith("- subcategoria:") or not linhas[1].lower().startswith("- submenu:"):
        return False

    # Verifica se há ao menos uma linha de personagem no formato esperado (nome, link)
    for linha in linhas[2:]:
        if "," not in linha or len(linha.split(",")) != 2:
            return False

    return True
