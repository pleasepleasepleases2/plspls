import random
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


def doar(message):
    try:
        chat_id = message.chat.id
        eu = message.from_user.id
        args = message.text.split()

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

            bot.send_message(chat_id, texto, reply_markup=keyboard)
        else:
            bot.send_message(chat_id, "Você não pode doar uma carta que não possui.")

    except Exception as e:
        newrelic.agent.record_exception()    
        print(f"Erro durante o comando de doação: {e}")

    finally:
        fechar_conexao(cursor, conn)
