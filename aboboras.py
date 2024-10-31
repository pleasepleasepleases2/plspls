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





# Função para buscar o nome técnico da travessura com base no estilizado
def obter_nome_tecnico(nome_estilizado):
    for nome_tecnico, nome_formatado in NOMES_TRAVESSURAS_ESTILIZADOS.items():
        if nome_estilizado.lower() == nome_formatado.lower():
            return nome_tecnico
    return None
