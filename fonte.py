from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bd import *
from botoes import *
import time
import random
import globals

def process_wish(message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        command_parts = message.text.split()
        id_cartas = list(map(int, command_parts[:-1]))[:5]  
        quantidade_cenouras = int(command_parts[-1])

        if quantidade_cenouras < 10 or quantidade_cenouras > 20:
            bot.send_message(chat_id, "A quantidade de cenouras deve ser entre 10 e 20.")
            return
        if user_id != 1011473517:
            can_make_wish, time_remaining = check_wish_time(user_id)
            if not can_make_wish:
                hours, remainder = divmod(time_remaining.total_seconds(), 3600)
                minutes, _ = divmod(remainder, 60)
                image_url = "https://telegra.ph/file/94c9c66af4ca4d6f0a3e5.jpg"
                caption = (f"<b>Você já fez um pedido recentemente.</b> Por favor, aguarde {int(hours)} horas e {int(minutes)} minutos "
                           "para fazer um novo pedido.")
                media = InputMediaPhoto(image_url, caption=caption, parse_mode="HTML")
                bot.send_message(chat_id=message.chat.id, text=caption, parse_mode="HTML")
                return

            results = []
            debug_info = []
            diminuir_cenouras(user_id, quantidade_cenouras)
            adicionar_cenouras_banco(quantidade_cenouras)  # Adiciona as cenouras ao banco da cidade
    
            for id_carta in id_cartas:
                chance = random.randint(1, 100)
                if chance <= 15:  # 10% de chance
                    results.append(id_carta)
                    update_inventory(user_id, id_carta)
                debug_info.append(f"ID da carta: {id_carta}, Chance: {chance}, Resultado: {'Ganhou' if chance <= 10 else 'Não ganhou'}")
    
            if results:
                bot.send_message(chat_id, f"<i>As águas da fonte começam a circular em uma velocidade assutadora, mas antes que você possa reagir, aparece na sua cesta os seguintes peixes:<b> {', '.join(map(str, results))}.</b>\n\nA fonte então desaparece. Quem sabe onde ele estará daqui 6 horas?</i>", parse_mode="HTML")
            else:
                bot.send_message(chat_id, "<i>A fonte nem se move ao receber suas cenouras, elas apenas desaparecem no meio da água calma. Talvez você deva tentar novamente mais tarde... </i>", parse_mode="HTML")
    
            log_wish_attempt(user_id, id_cartas, quantidade_cenouras, results)
        else:
            results = []
            debug_info = []
            diminuir_cenouras(user_id, quantidade_cenouras)
            adicionar_cenouras_banco(quantidade_cenouras)  # Adiciona as cenouras ao banco da cidade
    
            for id_carta in id_cartas:
                chance = random.randint(1, 100)
                if chance <= 50:  # 10% de chance
                    results.append(id_carta)
                    update_inventory(user_id, id_carta)
                debug_info.append(f"ID da carta: {id_carta}, Chance: {chance}, Resultado: {'Ganhou' if chance <= 10 else 'Não ganhou'}")
    
            if results:
                bot.send_message(chat_id, f"<i>As águas da fonte começam a circular em uma velocidade assutadora, mas antes que você possa reagir, aparece na sua cesta os seguintes peixes:<b> {', '.join(map(str, results))}.</b>\n\nA fonte então desaparece. Quem sabe onde ele estará daqui 6 horas?</i>", parse_mode="HTML")
            else:
                bot.send_message(chat_id, "<i>A fonte nem se move ao receber suas cenouras, elas apenas desaparecem no meio da água calma. Talvez você deva tentar novamente mais tarde... </i>", parse_mode="HTML")
    
    except Exception as e:
        bot.send_message(message.chat.id, f"Ocorreu um erro. Você escreveu da maneira correta?")

def adicionar_cenouras_banco(quantidade_cenouras):
    conn, cursor = conectar_banco_dados()
    try:
        cursor.execute("UPDATE banco_cidade SET quantidade_cenouras = quantidade_cenouras + %s", (quantidade_cenouras,))
        conn.commit()
    except Exception as e:
        print(f"Erro ao adicionar cenouras ao banco: {e}")
    finally:
        fechar_conexao(cursor, conn)

def check_wish_time(user_id):
    conn, cursor = conectar_banco_dados()
    try:
        cursor.execute("SELECT MAX(timestamp) FROM wish_log WHERE id_usuario = %s", (user_id,))
        last_wish = cursor.fetchone()[0]

        # Verificar se o usuário é VIP
        cursor.execute("SELECT COUNT(*) FROM vips WHERE id_usuario = %s", (user_id,))
        is_vip = cursor.fetchone()[0] > 0

        # Tempo de espera: 3 horas para VIPs, 6 horas para não VIPs
        tempo_espera = timedelta(hours=3) if is_vip else timedelta(hours=6)

        if last_wish:
            time_since_last_wish = datetime.now() - last_wish
            if time_since_last_wish.total_seconds() < tempo_espera.total_seconds():
                return False, tempo_espera - time_since_last_wish
            return True, None
        return True, None
    except Exception as e:
        print(f"Erro ao verificar o tempo do último desejo: {e}")
        return False, None
    finally:
        fechar_conexao(cursor, conn)


def update_inventory(user_id, id_carta):
    conn, cursor = conectar_banco_dados()
    query = "SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s"
    cursor.execute(query, (user_id, id_carta))
    result = cursor.fetchone()
    if result:
        query = "UPDATE inventario SET quantidade = quantidade + 1 WHERE id_usuario = %s AND id_personagem = %s"
    else:
        query = "INSERT INTO inventario (id_usuario, id_personagem, quantidade) VALUES (%s, %s, 1)"
    cursor.execute(query, (user_id, id_carta))
    conn.commit()
    fechar_conexao(cursor, conn)

def log_wish_attempt(user_id, id_cartas, quantidade_cenouras, results):
    conn, cursor = conectar_banco_dados()
    for id_carta in id_cartas:
        success = id_carta in results
        query = "INSERT INTO wish_log (id_usuario, id_personagem, quantidade_cenouras, sucesso, timestamp) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (user_id, id_carta, quantidade_cenouras, success, datetime.now()))
    conn.commit()
    fechar_conexao(cursor, conn)

def comando_sorte(message):
    try:
        user_id = message.from_user.id
        conn, cursor = conectar_banco_dados()

        cursor.execute("SELECT MAX(timestamp) FROM sorte_log WHERE id_usuario = %s", (user_id,))
        last_use = cursor.fetchone()[0]

        if last_use:
            time_since_last_use = datetime.now() - last_use
            if time_since_last_use.total_seconds() < 43200:
                hours, remainder = divmod(43200 - time_since_last_use.total_seconds(), 3600)
                minutes, _ = divmod(remainder, 60)
                bot.send_message(message.chat.id, f"Você já usou o comando /raspadinha recentemente. Tente novamente em {int(hours)} horas e {int(minutes)} minutos.")
                return

        cursor.execute("SELECT SUM(quantidade_cenouras) FROM banco_cidade")
        total_cenouras = cursor.fetchone()[0] or 0

        if total_cenouras <= 0:
            bot.send_message(message.chat.id, "O banco da cidade está vazio. Tente novamente mais tarde.")
            return

        # Sorteio usando distribuição uniforme para garantir valores não negativos
        sorteio = random.randint(0, min(100, total_cenouras))

        cursor.execute("UPDATE banco_cidade SET quantidade_cenouras = quantidade_cenouras - %s WHERE quantidade_cenouras >= %s", (sorteio, sorteio))
        if cursor.rowcount == 0:
            bot.send_message(message.chat.id, "Não foi possível completar a transação. Tente novamente mais tarde.")
            return
        conn.commit()

        cursor.execute("UPDATE usuarios SET cenouras = cenouras + %s WHERE id_usuario = %s", (sorteio, user_id))
        conn.commit()

        cursor.execute("INSERT INTO sorte_log (id_usuario, quantidade_ganha, timestamp) VALUES (%s, %s, %s)", (user_id, sorteio, datetime.now()))
        conn.commit()

        bot.send_message(message.chat.id, f"<i>A sorte está ao seu favor!</i> \nVocê comprou uma raspadinha e ganhou <b>{sorteio}</b> cenouras!", parse_mode="HTML")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ocorreu um erro ao processar o comando /raspadinha: {e}")
    finally:
        fechar_conexao(cursor, conn)

def handle_poco_dos_desejos(call):
    usuario = call.from_user.first_name
    image_url = "https://telegra.ph/file/94c9c66af4ca4d6f0a3e5.jpg"
    caption = (f"<i>Enquanto os demais camponeses estavam distraídos com suas pescas, {usuario} caminhava para um lugar mais distante, até que encontrou uma floresta mágica.\n\n</i>"
               "<i>Já havia escutado seus colegas falando da mesma mas sempre duvidou que era real.</i>\n\n"
               "⛲: <i><b>Oh! Olá camponês, imagino que a dona do jardim tenha te mandado pra cá, certo?</b></i>\n\n"
               "<i>Apesar da confusão com a voz repentina, perguntou a fonte o que aquilo significava.\n\n</i>"
               "⛲: <i><b>Sou uma fonte dos desejos! você tem direito a fazer um pedido, em troca eu peço apenas algumas cenouras. Se os peixes que você deseja estiverem disponíveis e a sorte ao seu favor eles irão aparecer no seu armazém. Se não, volte mais tarde com outras cenouras.</b></i>")
    media = InputMediaPhoto(image_url, caption=caption, parse_mode="HTML")
    bot.edit_message_media(media, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_wish_buttons())

def handle_fazer_pedido(call):
    user_id = call.from_user.id  # Adicionando a identificação do usuário

    can_make_wish, time_remaining = check_wish_time(user_id)
    if not can_make_wish:
        hours, remainder = divmod(time_remaining.total_seconds(), 3600)
        minutes, _ = divmod(remainder, 60)
        image_url = "https://telegra.ph/file/94c9c66af4ca4d6f0a3e5.jpg"
        caption = (f"<b>Você já fez um pedido recentemente.</b> Por favor, aguarde {int(hours)} horas e {int(minutes)} minutos "
                   "para fazer um novo pedido.")
        media = InputMediaPhoto(image_url, caption=caption, parse_mode="HTML")
        bot.send_photo(chat_id=call.message.chat.id, photo=image_url, caption=caption, parse_mode="HTML")
        return
    else:
        image_url = "https://telegra.ph/file/94c9c66af4ca4d6f0a3e5.jpg"
        caption = ("<b>⛲: Para pedir os seus peixes é simples!</b> \n\nMe envie até <b>5 IDs</b> dos peixes e a quantidade de cenouras que você quer doar "
                   "\n(eu aceito qualquer quantidade entre 10 e 20 cenouras...) \n\n<i>exemplo: ID1 ID2 ID3 ID4 ID5 cenouras</i>")
        media = InputMediaPhoto(image_url, caption=caption, parse_mode="HTML")
        bot.edit_message_media(media, chat_id=call.message.chat.id, message_id=call.message.message_id)
        
        bot.register_next_step_handler(call.message, process_wish)
def processar_pedido_peixes(call):
    try:
        image_url = "https://telegra.ph/file/94c9c66af4ca4d6f0a3e5.jpg"
        caption = ("<b>⛲: Para pedir os seus peixes é simples!</b> \n\nMe envie até <b>5 IDs</b> dos peixes e a quantidade de cenouras que você quer doar "
                   "\n(eu aceito qualquer quantidade entre 10 e 20 cenouras...) \n\n<i>exemplo: ID1 ID2 ID3 ID4 ID5 cenouras</i>")
        media = InputMediaPhoto(image_url, caption=caption, parse_mode="HTML")
        bot.edit_message_media(media, chat_id=call.message.chat.id, message_id=call.message.message_id)

        # Registrar o próximo passo para processar o pedido
        bot.register_next_step_handler(call.message, process_wish)

    except Exception as e:
        print(f"Erro ao processar o pedido de peixes: {e}")

