import telebot
import traceback
from credentials import *
from bd import *
bot = telebot.TeleBot(API_TOKEN)
def enviar_pergunta_cenoura(message, id_usuario, cartas_a_cenourar, bot):
    try:
        # Preparando os dados para o callback
        ids_personagens = ','.join(cartas_a_cenourar)  # Concatenar IDs em uma string separada por vírgula
        texto_pergunta = f"Você deseja cenourar as cartas: {ids_personagens}?"
        
        # Criando botões de confirmação
        keyboard = telebot.types.InlineKeyboardMarkup()
        sim_button = telebot.types.InlineKeyboardButton(text="Sim", callback_data=f"cenourar_sim_{id_usuario}_{ids_personagens}")
        nao_button = telebot.types.InlineKeyboardButton(text="Não", callback_data=f"cenourar_nao_{id_usuario}_{ids_personagens}")
        keyboard.row(sim_button, nao_button)

        # Enviando a pergunta com os botões
        bot.send_message(message.chat.id, texto_pergunta, reply_markup=keyboard)
    except Exception as e:
        print(f"Erro ao enviar pergunta de cenourar: {e}")

def processar_verificar_e_cenourar(message, bot):
    try:
        print("DEBUG: Iniciando o processamento de comando de cenourar...")
        conn, cursor = conectar_banco_dados()
        id_usuario = message.from_user.id
        print(f"DEBUG: ID do usuário: {id_usuario}")
        print(message.text)

        # Verifica se o comando tem pelo menos dois argumentos (comando e IDs)
        if len(message.text.split()) < 2:
            bot.send_message(message.chat.id, "Por favor, forneça os IDs dos personagens que deseja cenourar, separados por vírgulas. Exemplo: /cenourar 12345,67890")
            return

        # Remove espaços extras e divide os IDs por vírgula, filtrando entradas vazias
        ids_personagens_bruto = ' '.join(message.text.split()[1:]).strip()  # Pega o texto após o comando, unido por espaço
        print(f"DEBUG: IDs dos personagens brutos: {ids_personagens_bruto}")

        # Divide os IDs por vírgula, remove espaços em branco e filtra IDs vazios
        ids_personagens = [id_personagem.strip() for id_personagem in ids_personagens_bruto.split(',') if id_personagem.strip()]
        print(f"DEBUG: IDs dos personagens recebidos (após limpeza): {ids_personagens}")

        # Verifica se as cartas estão no inventário
        cartas_a_cenourar = []
        cartas_nao_encontradas = []

        for id_personagem in ids_personagens:
            print(f"DEBUG: Verificando carta com ID {id_personagem} no inventário...")
            cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (id_usuario, id_personagem))
            quantidade_atual = cursor.fetchone()
            print(f"DEBUG: Quantidade atual da carta {id_personagem}: {quantidade_atual}")
            if quantidade_atual and quantidade_atual[0] >= 1:
                cartas_a_cenourar.append(id_personagem)
            else:
                cartas_nao_encontradas.append(id_personagem)

        print(f"DEBUG: Cartas a cenourar: {cartas_a_cenourar}")
        print(f"DEBUG: Cartas não encontradas ou insuficientes: {cartas_nao_encontradas}")

        # Envia a pergunta de confirmação para as cartas que podem ser cenouradas
        if cartas_a_cenourar:
            enviar_pergunta_cenoura(message, id_usuario, cartas_a_cenourar, bot)
        # Mensagem de erro para cartas que não foram encontradas ou quantidade insuficiente
        if cartas_nao_encontradas:
            bot.send_message(message.chat.id, f"As seguintes cartas não foram encontradas no inventário ou você não tem quantidade suficiente: {', '.join(cartas_nao_encontradas)}")
        if not cartas_a_cenourar and not cartas_nao_encontradas:
            bot.send_message(message.chat.id, "Nenhuma carta válida foi encontrada para cenourar.")
    except Exception as e:
        print(f"DEBUG: Erro ao processar o comando de cenourar: {e}")
        traceback.print_exc()
        bot.send_message(message.chat.id, "Erro ao processar o comando de cenourar.")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def cenourar_carta(call, id_usuario, ids_personagens):
    try:
        print(f"DEBUG: Iniciando processamento do callback de cenourar para o usuário {id_usuario}")
        conn, cursor = conectar_banco_dados()
        chat_id = call.message.chat.id
        message_id = call.message.message_id

        cartas_cenouradas = []
        cartas_nao_encontradas = []

        # Itera sobre cada ID de personagem
        for id_personagem in ids_personagens:
            print(f"DEBUG: Verificando quantidade no inventário da carta {id_personagem} para o usuário {id_usuario}")

            # Verifica se o personagem está no inventário do usuário
            cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (id_usuario, id_personagem))
            quantidade_atual = cursor.fetchone()
            print(f"DEBUG: Quantidade atual da carta {id_personagem}: {quantidade_atual}")

            # Se a quantidade for válida e maior que 0, podemos cenourar
            if quantidade_atual and quantidade_atual[0] > 0:
                nova_quantidade = quantidade_atual[0] - 1
                print(f"DEBUG: Nova quantidade da carta {id_personagem} será {nova_quantidade}")

                # Atualiza a quantidade da carta no inventário do usuário
                cursor.execute("UPDATE inventario SET quantidade = %s WHERE id_usuario = %s AND id_personagem = %s", 
                               (nova_quantidade, id_usuario, id_personagem))
                conn.commit()
                print(f"DEBUG: Atualizada quantidade no inventário para a carta {id_personagem}")

                # Atualiza o número de cenouras do usuário
                cursor.execute("SELECT cenouras FROM usuarios WHERE id_usuario = %s", (id_usuario,))
                cenouras = cursor.fetchone()[0]  # Pegando a quantidade de cenouras
                print(f"DEBUG: Quantidade atual de cenouras do usuário {id_usuario}: {cenouras}")
                
                novas_cenouras = cenouras + 1
                cursor.execute("UPDATE usuarios SET cenouras = %s WHERE id_usuario = %s", (novas_cenouras, id_usuario))
                conn.commit()
                print(f"DEBUG: Cenouras atualizadas para o usuário {id_usuario}: {novas_cenouras}")

                cartas_cenouradas.append(id_personagem)
            else:
                cartas_nao_encontradas.append(id_personagem)
                print(f"DEBUG: Carta {id_personagem} não encontrada ou quantidade insuficiente no inventário")

        # Mensagens de confirmação
        if cartas_cenouradas:
            mensagem_final = f"🥕 Cartas cenouradas com sucesso:\n\n{', '.join(cartas_cenouradas)}"
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=mensagem_final)
            print(f"DEBUG: Cartas cenouradas: {cartas_cenouradas}")
        
        if cartas_nao_encontradas:
            bot.send_message(chat_id, f"As seguintes cartas não foram encontradas no inventário ou a quantidade é insuficiente: {', '.join(cartas_nao_encontradas)}")
            print(f"DEBUG: Cartas não encontradas: {cartas_nao_encontradas}")
    
    except mysql.connector.Error as e:
        print(f"DEBUG: Erro ao processar cenoura: {e}")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Erro ao processar a cenoura.")
    finally:
        # Fechando o cursor e conexão adequadamente
        try:
            if cursor:
                cursor.close()
                print(f"DEBUG: Cursor fechado com sucesso")
            if conn:
                conn.close()
                print(f"DEBUG: Conexão fechada com sucesso")
        except Exception as e:
            print(f"DEBUG: Erro ao fechar conexão ou cursor: {e}")


def verificar_id_na_tabelabeta(user_id):
    try:
        conn = conectar_banco_dados()
        cursor = conn.cursor()
        query = f"SELECT id FROM beta WHERE id = {user_id}"
        cursor.execute(query)
        resultado = cursor.fetchone()
        return resultado is not None
    except Exception as e:
        print(f"Erro ao verificar ID na tabela beta: {e}")
        raise ValueError("Erro ao verificar ID na tabela beta")
    finally:
        cursor.close()
        conn.close()


