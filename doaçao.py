import random
from credentials import *
from pesquisas import *
from user import *
from bd import *
from loja import *
from gnome import *
from operacoes import *
from inventario import *
from gif import *
from cachetools import cached, TTLCache
from evento import *
from sub import *
import mysql.connector.pooling
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


def doar(message):
    try:
        chat_id = message.chat.id
        eu = message.from_user.id
        args = message.text.split()
        # Verificar se a travessura de embaralhamento está ativa
        embaralhamento_ativo = verificar_travessura_ativa(eu)
        if len(args) < 2:
            bot.send_message(chat_id, "Formato incorreto. Use /doar <quantidade> <ID_da_carta> ou /doar all <ID_da_carta>")
            return

        doar_todas = False
        doar_uma = False

        if args[1].lower() == 'all':
            doar_todas = True
            minhacarta = int(args[2])
        elif len(args) == 2:
            doar_uma = True
            minhacarta = int(args[1])
        else:
            quantidade = int(args[1])
            minhacarta = int(args[2])

        conn, cursor = conectar_banco_dados()
        qnt_carta = verifica_inventario_troca(eu, minhacarta)
        if qnt_carta > 0:
            if doar_todas:
                quantidade = qnt_carta
            elif doar_uma:
                quantidade = 1
            elif quantidade > qnt_carta:
                bot.send_message(chat_id, f"Você não possui {quantidade} unidades dessa carta.")
                return

            destinatario_id = None
            nome_destinatario = None

            if message.reply_to_message and message.reply_to_message.from_user:
                destinatario_id = message.reply_to_message.from_user.id
                nome_destinatario = message.reply_to_message.from_user.first_name

            # Verificar se o destinatário é o bot
            if destinatario_id == int(API_TOKEN.split(':')[0]):
                bot.send_message(chat_id, "Pr-Pra mim? 😳 Muito obrigada, mas não acho que seja de bom tom um bot aceitar doação tão generosa... 😢 Talvez você deva procurar um camponês de verdade...")
                return

            if not destinatario_id:
                bot.send_message(chat_id, "Você precisa responder a uma mensagem para doar a carta.")
                return

            nome_carta = obter_nome(minhacarta)
            qnt_str = f"uma unidade da carta" if quantidade == 1 else f"{quantidade} unidades da carta"
            texto = f"Olá, {message.from_user.first_name}!\n\nVocê tem {qnt_carta} unidades da carta: {minhacarta} — {nome_carta}.\n\n"
            texto += f"Deseja doar {qnt_str} para {nome_destinatario}?"

            keyboard = types.InlineKeyboardMarkup()
            keyboard.row(
                types.InlineKeyboardButton(text="Sim", callback_data=f'cdoacao_{eu}_{minhacarta}_{destinatario_id}_{quantidade}'),
                types.InlineKeyboardButton(text="Não", callback_data=f'ccancelar_{eu}')
            )
            # Embaralha a mensagem se a travessura estiver ativa
            texto = truncar_texto(texto) if embaralhamento_ativo else texto
            bot.send_message(chat_id, texto, reply_markup=keyboard)
        else:
            bot.send_message(chat_id, "Você não pode doar uma carta que não possui.")

    except Exception as e:
        newrelic.agent.record_exception()    
        print(f"Erro durante o comando de doação: {e}")

    finally:
        fechar_conexao(cursor, conn)
# Callback para confirmar a doação
def confirmar_doacao(call):
    try:
        data = call.data.split('_')
        if len(data) != 5:
            bot.send_message(call.message.chat.id, "Dados de doação inválidos.")
            return
        # Verificar se a travessura de embaralhamento está ativa
        embaralhamento_ativo = verificar_travessura_ativa(id_usuario)
        eu = int(data[1])
        minhacarta = int(data[2])
        destinatario_id = int(data[3])
        quantidade = int(data[4])
        message = call.message

        conn, cursor = conectar_banco_dados()

        # Verificar quantidade de cartas no inventário do doador
        cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (eu, minhacarta))
        quantidade_doador_anterior = cursor.fetchone()
        if not quantidade_doador_anterior:
            bot.send_message(call.message.chat.id, "Você não possui essa carta no inventário.")
            return
        quantidade_doador_anterior = quantidade_doador_anterior[0]

        # Verificar quantidade de cenouras do doador
        cursor.execute("SELECT cenouras FROM usuarios WHERE id_usuario = %s", (eu,))
        cenouras_doador = cursor.fetchone()[0]

        if quantidade_doador_anterior >= quantidade and cenouras_doador >= quantidade:
            cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (destinatario_id, minhacarta))
            quantidade_destinatario_anterior = cursor.fetchone()
            if quantidade_destinatario_anterior:
                quantidade_destinatario_anterior = quantidade_destinatario_anterior[0]
            else:
                quantidade_destinatario_anterior = 0

            # Atualizar inventário do doador
            cursor.execute("UPDATE inventario SET quantidade = quantidade - %s WHERE id_usuario = %s AND id_personagem = %s", (quantidade, eu, minhacarta))

            # Atualizar inventário do destinatário
            cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (destinatario_id, minhacarta))
            quantidade_destinatario = cursor.fetchone()

            if quantidade_destinatario:
                cursor.execute("UPDATE inventario SET quantidade = quantidade + %s WHERE id_usuario = %s AND id_personagem = %s", (quantidade, destinatario_id, minhacarta))
            else:
                cursor.execute("INSERT INTO inventario (id_usuario, id_personagem, quantidade) VALUES (%s, %s, %s)", (destinatario_id, minhacarta, quantidade))

            # Atualizar cenouras do doador
            cursor.execute("UPDATE usuarios SET cenouras = cenouras - %s WHERE id_usuario = %s", (quantidade, eu))

            # Obter quantidades atualizadas para confirmação
            cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (eu, minhacarta))
            quantidade_doador_atual = cursor.fetchone()[0]

            cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (destinatario_id, minhacarta))
            quantidade_destinatario_atual = cursor.fetchone()[0]

            conn.commit()

            # Registrar no histórico de doações
            cursor.execute("""
                INSERT INTO historico_doacoes (id_usuario_doacao, id_usuario_recebedor, id_personagem_carta, data_hora, quantidade, 
                                               quantidade_anterior_doacao, quantidade_atual_doacao, 
                                               quantidade_anterior_recebedor, quantidade_atual_recebedor)
                VALUES (%s, %s, %s, NOW(), %s, %s, %s, %s, %s)
            """, (eu, destinatario_id, minhacarta, quantidade, 
                  quantidade_doador_anterior, quantidade_doador_atual, 
                  quantidade_destinatario_anterior, quantidade_destinatario_atual))
            conn.commit()

            # Obter informações dos usuários para a mensagem de confirmação
            user_info = bot.get_chat(destinatario_id)
            seunome = user_info.first_name
            user_info1 = bot.get_chat(eu)
            meunome = user_info1.first_name
            doacao_str = f"uma unidade da carta {minhacarta}" if quantidade == 1 else f"{quantidade} unidades da carta {minhacarta}"
            texto_confirmacao = f"Doação de {doacao_str} realizada com sucesso!\n\n"
            texto_confirmacao += f"🧺 De {meunome}: {quantidade_doador_anterior}↝{quantidade_doador_atual}\n\n"
            texto_confirmacao += f"🧺 Para {seunome}: {quantidade_destinatario_anterior}↝{quantidade_destinatario_atual}\n"
            # Embaralha a mensagem se a travessura estiver ativa
            texto = truncar_texto(texto_confirmacao) if embaralhamento_ativo else texto_confirmacao
            bot.edit_message_text(texto_confirmacao, chat_id=call.message.chat.id, message_id=call.message.message_id)
        else:
            if quantidade_doador_anterior < quantidade:
                bot.edit_message_text("Você não possui cartas suficientes para fazer a doação.", chat_id=call.message.chat.id, message_id=call.message.message_id)
            elif cenouras_doador < quantidade:
                bot.edit_message_text("Você não possui cenouras suficientes para fazer a doação.", chat_id=call.message.chat.id, message_id=call.message.message_id)
    except Exception as e:
        print(f"Erro ao confirmar a doação: {e}")
        bot.send_message(call.message.chat.id, "Erro ao confirmar a doação. Tente novamente!")
    finally:
        fechar_conexao(cursor, conn)

# Callback para cancelar a doação
def cancelar_doacao(call):
    try:
        bot.edit_message_text("Doação cancelada.", chat_id=call.message.chat.id, message_id=call.message.message_id)
    except Exception as e:
        print(f"Erro ao cancelar a doação: {e}")
        bot.send_message(call.message.chat.id, "Erro ao cancelar a doação.")
