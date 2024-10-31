def conceder_cenouras(user_id, quantidade):
    """
    Concede uma quantidade específica de cenouras ao jogador.
    """
    conn, cursor = conectar_banco_dados()
    try:
        cursor.execute("UPDATE usuarios SET cenouras = cenouras + %s WHERE id_usuario = %s", (quantidade, user_id))
        conn.commit()
        bot.send_message(user_id, f"🎃 Você ganhou {quantidade} cenouras!")
    except Exception as e:
        print(f"Erro ao conceder cenouras: {e}")
    finally:
        fechar_conexao(cursor, conn)


def adicionar_carta_faltante_halloween(user_id, chat_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Obter todas as cartas do evento Halloween que o usuário ainda não possui
        query_faltantes_halloween = """
            SELECT e.id_personagem, e.nome 
            FROM evento e
            LEFT JOIN inventario i ON e.id_personagem = i.id_personagem AND i.id_usuario = %s
            WHERE e.evento = 'Festival das Abóboras' AND i.id_personagem IS NULL
        """
        cursor.execute(query_faltantes_halloween, (user_id,))
        cartas_faltantes = cursor.fetchall()
        total_faltantes = len(cartas_faltantes)

        if not cartas_faltantes:
            bot.send_message(user_id, "Parabéns! Mas você já tem todas as cartas do evento de Halloween.")
            return

        # Selecionar uma carta de Halloween aleatória
        carta_faltante = random.choice(cartas_faltantes)
        id_carta_faltante, nome_carta_faltante = carta_faltante

        # Adicionar a carta ao inventário
        cursor.execute("INSERT INTO inventario (id_usuario, id_personagem, quantidade) VALUES (%s, %s, 1)", (user_id, id_carta_faltante))
        conn.commit()

        # Enviar a mensagem informando a carta recebida e o total de cartas que ainda faltam
        bot.send_message(chat_id, 
                         f"🎃 Parabéns! Você encontrou uma carta do evento Halloween: "
                         f"{nome_carta_faltante} (ID: {id_carta_faltante}) foi adicionada ao seu inventário. "
                         f"Ainda faltam {total_faltantes - 1} cartas para completar o evento!")

    except Exception as e:
        print(f"Erro ao adicionar carta de Halloween faltante: {e}")
    finally:
        fechar_conexao(cursor, conn)


# Função para buscar o nome técnico da travessura com base no estilizado
def obter_nome_tecnico(nome_estilizado):
    for nome_tecnico, nome_formatado in NOMES_TRAVESSURAS_ESTILIZADOS.items():
        if nome_estilizado.lower() == nome_formatado.lower():
            return nome_tecnico
    return None
