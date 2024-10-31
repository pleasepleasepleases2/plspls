import telebot
import traceback
from credentials import *
from bd import *
bot = telebot.TeleBot(API_TOKEN)
# Função para verificar se a "travessura de embaralhamento" está ativa
def verificar_travessura_ativa(id_usuario, tipo_travessura="embaralhamento"):
    conn, cursor = conectar_banco_dados()
    try:
        query = "SELECT fim_travessura FROM travessuras WHERE id_usuario = %s AND tipo_travessura = %s"
        cursor.execute(query, (id_usuario, tipo_travessura))
        resultado = cursor.fetchone()
        
        # Verificar se a travessura está ativa e ainda dentro do prazo
        if resultado:
            fim_travessura = resultado[0]
            return datetime.now() < fim_travessura
        return False
    finally:
        fechar_conexao(cursor, conn)
def enviar_pergunta_cenoura(message, id_usuario, ids_personagens, bot):
    try:
        conn, cursor = conectar_banco_dados()
        # Verificar se a travessura de embaralhamento está ativa
        embaralhamento_ativo = verificar_travessura_ativa(id_usuario)
        # Recupera os nomes das cartas e formata a pergunta
        cartas_formatadas = []
        for id_personagem in ids_personagens:
            cursor.execute("SELECT nome FROM personagens WHERE id_personagem = %s", (id_personagem,))
            nome_carta = cursor.fetchone()
            if nome_carta:
                cartas_formatadas.append(f"{id_personagem} - {nome_carta[0]}")

        respostatexto = f"Você deseja mesmo cenourar as cartas:\n\n" + "\n".join(cartas_formatadas)
        respostatexto = truncar_texto(respostatexto) if embaralhamento_ativo else respostatexto
        # Passando os IDs como uma string separada por vírgula
        keyboard = telebot.types.InlineKeyboardMarkup()
        sim_button = telebot.types.InlineKeyboardButton(text="Sim", callback_data=f"cenourar_sim_{id_usuario}_{','.join(ids_personagens)}")
        nao_button = telebot.types.InlineKeyboardButton(text="Não", callback_data=f"cenourar_nao_{id_usuario}")
        keyboard.row(sim_button, nao_button)

        bot.send_message(message.chat.id, respostatexto, reply_markup=keyboard)

    except Exception as e:
        print(f"Erro ao enviar pergunta de cenourar: {e}")
        traceback.print_exc()  # Mostra mais detalhes da exceção
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def processar_verificar_e_cenourar(message, bot):
    try:
        conn, cursor = conectar_banco_dados()
        id_usuario = message.from_user.id

        if len(message.text.split()) < 2:
            bot.send_message(message.chat.id, "Por favor, forneça os IDs dos personagens que deseja cenourar, separados por vírgulas. Exemplo: /cenourar 12345,67890")
            return
        
        ids_personagens_bruto = ' '.join(message.text.split()[1:]).strip()
        ids_personagens = [id_personagem.strip() for id_personagem in ids_personagens_bruto.split(',') if id_personagem.strip()]

        cartas_a_cenourar = []
        cartas_nao_encontradas = []

        for id_personagem in ids_personagens:
            cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (id_usuario, id_personagem))
            quantidade_atual = cursor.fetchone()

            if quantidade_atual and quantidade_atual[0] >= 1:
                cartas_a_cenourar.append(id_personagem)
            else:
                cartas_nao_encontradas.append(id_personagem)

        if cartas_a_cenourar:
            enviar_pergunta_cenoura(message, id_usuario, cartas_a_cenourar, bot)
        if cartas_nao_encontradas:
            bot.send_message(message.chat.id, f"As seguintes cartas não foram encontradas no inventário ou você não tem quantidade suficiente: {', '.join(cartas_nao_encontradas)}")
        if not cartas_a_cenourar and not cartas_nao_encontradas:
            bot.send_message(message.chat.id, "Nenhuma carta válida foi encontrada para cenourar.")
    except Exception as e:
        print(f"DEBUG: Erro ao processar o comando de cenourar: {e}")
        traceback.print_exc()  # Mostra mais detalhes da exceção
        bot.send_message(message.chat.id, "Erro ao processar o comando de cenourar.")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

from datetime import datetime, timedelta

def adicionar_super_boost_cenouras(user_id, multiplicador, duracao_horas, chat_id):
    try:
        conn, cursor = conectar_banco_dados()
        fim_boost = datetime.now() + timedelta(hours=duracao_horas)

        # Inserir ou atualizar o boost de cenouras na tabela 'boosts'
        cursor.execute("""
            INSERT INTO boosts (id_usuario, tipo_boost, multiplicador, fim_boost)
            VALUES (%s, 'cenouras', %s, %s)
            ON DUPLICATE KEY UPDATE multiplicador = %s, fim_boost = %s
        """, (user_id, multiplicador, fim_boost, multiplicador, fim_boost))
        
        conn.commit()

        bot.send_message(
            chat_id, 
            f"🎃✨ *Um feitiço raro foi lançado!* 🌿 Todas as cenouras que você colher serão multiplicadas por {multiplicador} nas próximas {duracao_horas} horas. Aproveite essa magia enquanto dura! 🍂🥕",
            parse_mode="Markdown"
        )
    
    except Exception as e:
        print(f"Erro ao adicionar Super Boost de Cenouras: {e}")
    
    finally:
        fechar_conexao(cursor, conn)

def verificar_boost_cenouras(user_id):
    """Verifica se o boost de cenouras está ativo e retorna o multiplicador e tempo restante."""
    conn, cursor = conectar_banco_dados()
    try:
        cursor.execute("SELECT multiplicador, fim_boost FROM boosts WHERE id_usuario = %s AND tipo_boost = 'cenouras'", (user_id,))
        resultado = cursor.fetchone()
        if resultado:
            multiplicador, fim_boost = resultado
            if datetime.now() < fim_boost:
                # Boost ainda está ativo
                return multiplicador, (fim_boost - datetime.now()).total_seconds()
        return 1, 0  # Sem boost
    except Exception as e:
        print(f"Erro ao verificar o boost de cenouras: {e}")
        return 1, 0
    finally:
        fechar_conexao(cursor, conn)

def cenourar_carta(call, id_usuario, ids_personagens_str):
    try:
        conn, cursor = conectar_banco_dados()
        chat_id = call.message.chat.id
        message_id = call.message.message_id

        # Recupera os IDs das cartas
        ids_personagens = ids_personagens_str if isinstance(ids_personagens_str, list) else ids_personagens_str.split(',')
        embaralhamento_ativo = verificar_travessura_ativa(id_usuario)
        cartas_cenouradas = []
        cartas_nao_encontradas = []

        # Verifica boost ativo e aplica o multiplicador
        multiplicador, _ = verificar_boost_cenouras(id_usuario)

        for id_personagem in ids_personagens:
            cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (id_usuario, id_personagem))
            quantidade_atual = cursor.fetchone()

            if quantidade_atual and quantidade_atual[0] > 0:
                nova_quantidade = quantidade_atual[0] - 1
                cursor.execute("UPDATE inventario SET quantidade = %s WHERE id_usuario = %s AND id_personagem = %s", 
                               (nova_quantidade, id_usuario, id_personagem))
                conn.commit()

                # Multiplica as cenouras caso o boost esteja ativo
                cenouras_ganhas = 1 * multiplicador

                cursor.execute("UPDATE usuarios SET cenouras = cenouras + %s WHERE id_usuario = %s", (cenouras_ganhas, id_usuario))
                conn.commit()

                cartas_cenouradas.append(id_personagem)
            else:
                cartas_nao_encontradas.append(id_personagem)

        # Mensagens de confirmação
        if cartas_cenouradas:
            mensagem_final = f"🥕<b> Cenouras colhidas com sucesso!</b> Multiplicador aplicado: x{multiplicador}\nCartas cenouradas: {', '.join(cartas_cenouradas)}"
            mensagem_final = truncar_texto(mensagem_final) if embaralhamento_ativo else mensagem_final
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=mensagem_final, parse_mode="HTML")

        if cartas_nao_encontradas:
            bot.send_message(chat_id, f"As seguintes cartas não foram encontradas no inventário ou a quantidade é insuficiente: {', '.join(cartas_nao_encontradas)}")

    except mysql.connector.Error as e:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Erro ao processar a cenoura.")
    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except Exception as e:
            print(f"DEBUG: Erro ao fechar conexão ou cursor: {e}")
