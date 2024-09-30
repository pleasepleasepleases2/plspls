import mysql.connector
from mysql.connector import Error
import telebot
from telebot import types
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import time
import traceback
import threading
from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests
from io import BytesIO
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import re
import random
from retrying import retry
from datetime import datetime
import os
from telegraph import upload_file, Telegraph
from telebot import types
import traceback
from instaloader import Instaloader, Post
import telebot

# Inicialização do instaloader
L = Instaloader()
# Configuração do bot
bot = telebot.TeleBot("6994807679:AAG-33Rn0p3dADLzi-Op789K5_zRbgGszJk")
# Dicionário para armazenar a última subcategoria adicionada por categoria
ultima_subcategoria_adicionada = {}
# Configuração do banco de dados
def db():
    return {
        'host': '127.0.0.1',
        'database': 'garden',
        'user': 'root',
        'password': '#Folkevermore13'
    }

def conectar_banco_dados():
    while True:
        try:
            conn = mysql.connector.connect(**db())
            cursor = conn.cursor()
            return conn, cursor
        except mysql.connector.Error as e:
            print(f"Erro na conexão com o banco de dados: {e}")
            print("Tentando reconectar em 5 segundos...")
            time.sleep(5)

conn, cursor = conectar_banco_dados()

# Inicialize o Telegraph
telegraph = Telegraph()
telegraph.create_account(short_name="assistantmabi")

# Mensagens
start_msg = "Bem-vindo ao bot de download do Instagram!"
help_msg = "Envie um link de post do Instagram para baixar a mídia."
fail_msg = "Ocorreu um erro ao processar seu pedido. Tente novamente mais tarde."
wrong_pattern_msg = "Formato incorreto. Envie um link de post do Instagram."


def get_post_or_reel_shortcode_from_link(link):
    match = re.search(r'instagram\.com/(p|reel)/([^/?#&]+)', link)
    return match.group(2) if match else None

@bot.message_handler(func=lambda message: re.search(r'instagram\.com/(p|reel)/', message.text))
def post_or_reel_link_handler(message):

    try:
        guide_msg_1 = bot.send_message(message.chat.id, "Ok, aguarde um momento...")
        post_shortcode = get_post_or_reel_shortcode_from_link(message.text)
        
        if not post_shortcode:
            bot.send_message(message.chat.id, wrong_pattern_msg)
            return
        
        post = Post.from_shortcode(L.context, post_shortcode)
        
        # Handle post with single media
        if post.mediacount == 1:
            if post.is_video:
                bot.send_video(message.chat.id, post.video_url, caption=post.caption)
            else:
                bot.send_photo(message.chat.id, post.url, caption=post.caption)
        else:
            media_list = []
            sidecars = post.get_sidecar_nodes()
            for s in sidecars:
                if s.is_video:
                    media = telebot.types.InputMediaVideo(s.video_url)
                else:
                    media = telebot.types.InputMediaPhoto(s.display_url)
                media_list.append(media)
            bot.send_media_group(message.chat.id, media_list)
        
        bot.send_message(message.chat.id, "Download concluído!")
        bot.delete_message(message.chat.id, guide_msg_1.message_id)
    except Exception as e:
       
        bot.send_message(message.chat.id, fail_msg)
        traceback.print_exc()


    
    
def obter_proximo_id_personagem():
    conn, cursor = conectar_banco_dados()
    cursor.execute("SELECT MAX(CAST(id_personagem AS UNSIGNED)) FROM evento")
    max_id = cursor.fetchone()[0]
    fechar_conexao(cursor, conn)
    if max_id is None:
        return "1"
    else:
        return int(max_id) + 1
def generate_photo_link(file_path):
    # Substitua 'YOUR_API_TOKEN' pelo token do seu bot
    return f"https://api.telegram.org/file/bot{bot}/{file_path}"

def get_file_path(file_id):
    file_info = bot.get_file(file_id)
    return file_info.file_path

def get_attached_photo_url(message):
    photos = message.photo or (message.reply_to_message.photo if message.reply_to_message else None)
    photo = photos[-1].file_id if photos else None

    doc = message.document or (message.reply_to_message.document if message.reply_to_message else None)
    if doc:
        photo = doc.file_id

    if not photo:
        return None

    file_path = get_file_path(photo)
    return generate_photo_link(file_path)


@bot.message_handler(commands=['dupinv'])
def listar_duplicatas_inventario(message):
    conn, cursor = conectar_banco_dados()
    if conn is None or cursor is None:
        bot.send_message(message.chat.id, "Falha na conexão com o banco de dados.")
        return

    try:
        # Encontrar todas as duplicatas no inventário
        cursor.execute("""
            SELECT
                id_usuario,
                id_personagem,
                COUNT(*) as total_entradas,
                SUM(quantidade) as total_quantidade
            FROM inventario
            GROUP BY id_usuario, id_personagem
            HAVING COUNT(*) > 1;
        """)
        
        duplicatas = cursor.fetchall()
        
        if duplicatas:
            resposta = "Duplicatas encontradas:\n"
            for dup in duplicatas:
                id_usuario, id_personagem, total_entradas, total_quantidade = dup
                resposta += f"Usuário {id_usuario}, Personagem {id_personagem}: {total_entradas} entradas, Total Quantidade: {total_quantidade}\n"

            # Adicionar botão para confirmar a consolidação das quantidades
            markup = telebot.types.InlineKeyboardMarkup()
            confirm_button = telebot.types.InlineKeyboardButton("Consolidar Quantidades", callback_data="consolidar_quantidades")
            markup.add(confirm_button)
            
            bot.send_message(message.chat.id, resposta, reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Nenhuma duplicata encontrada no inventário.")
    except Exception as e:
        print(f"Erro ao listar duplicatas no inventário: {e}")
        bot.send_message(message.chat.id, f"Erro ao listar duplicatas no inventário: {e}")
    finally:
        cursor.close()
        conn.close()

@bot.callback_query_handler(func=lambda call: call.data == 'consolidar_quantidades')
def consolidar_quantidades_duplicadas(call):
    conn, cursor = conectar_banco_dados()

    try:
        # Consolidar as quantidades de cartas duplicadas
        cursor.execute("""
            UPDATE inventario i
            INNER JOIN (
                SELECT
                    id_usuario,
                    id_personagem,
                    SUM(quantidade) AS total_quantidade,
                    MIN(id) AS min_id
                FROM inventario
                GROUP BY id_usuario, id_personagem
                HAVING COUNT(*) > 1
            ) AS dups ON i.id_usuario = dups.id_usuario AND i.id_personagem = dups.id_personagem
            SET i.quantidade = dups.total_quantidade
            WHERE i.id = dups.min_id;
        """)

        # Deletar as entradas duplicadas, mantendo apenas a entrada com o menor ID
        cursor.execute("""
            DELETE i FROM inventario i
            INNER JOIN (
                SELECT
                    id_usuario,
                    id_personagem,
                    MIN(id) AS min_id
                FROM inventario
                GROUP BY id_usuario, id_personagem
                HAVING COUNT(*) > 1
            ) AS dups ON i.id_usuario = dups.id_usuario AND i.id_personagem = dups.id_personagem
            WHERE i.id > dups.min_id;
        """)
        
        conn.commit()
        bot.edit_message_text("Duplicatas no inventário foram consolidadas e limpas com sucesso.", call.message.chat.id, call.message.message_id)
    except Exception as e:
        bot.edit_message_text(f"Erro ao consolidar duplicatas no inventário: {e}", call.message.chat.id, call.message.message_id)
    finally:
        cursor.close()
        conn.close()

            
@bot.message_handler(commands=['delev'])
def solicitar_id_personagem(message):
    msg = bot.reply_to(message, "Por favor, forneça o ID do personagem que deseja deletar:")
    bot.register_next_step_handler(msg, processar_comando_delev)

def processar_comando_delev(message):
    try:
        id_personagem = message.text.strip()
        
        if not id_personagem.isdigit():
            bot.reply_to(message, "ID do personagem inválido. Certifique-se de que seja um número.")
            return

        resultado = deletar_evento(id_personagem)
        bot.reply_to(message, resultado)

    except Exception as e:
        bot.reply_to(message, f"Erro ao processar o comando /delev: {e}")

def deletar_evento(id_personagem):
    try:
        conn, cursor = conectar_banco_dados()

        # Verifica se existe um evento com o ID do personagem fornecido
        query_select = "SELECT id_personagem FROM evento WHERE id_personagem = %s"
        cursor.execute(query_select, (id_personagem,))
        evento_existente = cursor.fetchone()

        if evento_existente:
            # Se existir, deleta o registro da tabela
            query_delete = "DELETE FROM evento WHERE id_personagem = %s"
            cursor.execute(query_delete, (id_personagem,))
            conn.commit()
            return "Evento deletado com sucesso!"
        else:
            return "Nenhum evento encontrado com esse ID de personagem."

    except mysql.connector.Error as error:
        return f"Erro ao deletar evento: {error}"

    finally:
        fechar_conexao(cursor, conn)
def notify_group(action, details):
    group_chat_id = -1002216029435
    bot.send_message(group_chat_id, f"Ação: {action}\nDetalhes: {details}")

@bot.message_handler(commands=['diary'])
def atualizar_streak_diario(call):
    try:
        conn, cursor = conectar_banco_dados()

        # Obter a data atual
        data_atual = datetime.now().date()

        # Atualizar a data de todos os usuários para hoje
        cursor.execute("UPDATE diario SET ultimo_diario = %s", (data_atual,))

        # Commit das alterações
        conn.commit()
        print("Streak diário atualizado para todos os usuários.")

    except mysql.connector.Error as err:
        print(f"Erro ao atualizar o streak diário: {err}")

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@bot.message_handler(commands=['addev'])
def processar_comando_addev(message):
    user_id = message.from_user.id
    
    try:
        match = re.match(r'/addev ([^,]+), ([^,]+), (.+)', message.text)
        if not match:
            bot.reply_to(message, "Por favor, use o formato correto: '/addev nome, subcategoria, linkdaimagem'.")
            return

        nome, subcategoria, linkdaimagem = match.groups()
        id_personagem = obter_proximo_id_personagem()  # Esta função deve ser definida em outro lugar no seu código
        categoria = "evento"
        evento = "Inverno"
        emoji = "☃️"

        # Assumindo que conectar_banco_dados() retorna uma conexão e um cursor
        conn, cursor = conectar_banco_dados()
        cursor.execute("INSERT INTO evento (id_personagem, nome, subcategoria, categoria, evento, imagem, emoji) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                       (id_personagem, nome, subcategoria, categoria, evento, linkdaimagem, emoji))
        conn.commit()

        notify_group(f"Evento Adicionado por {message.from_user.first_name}\n", f"\nID: {id_personagem}, \nNome: {nome}, \nSubcategoria: {subcategoria}\nImagem: {linkdaimagem}")
        bot.reply_to(message, f"Evento adicionado com sucesso!\nID: {id_personagem}\nNome: {nome}\nSubcategoria: {subcategoria}\nImagem: {linkdaimagem}")

    except Exception as e:
        bot.reply_to(message, f"Erro ao adicionar evento: {e}")

    finally:
        cursor.close()
        conn.close()

borda_map = {
    1: "https://i.postimg.cc/RZ8Fbs4b/mail-google.png", 
    2: "https://i.postimg.cc/x87hSz8Y/mail-google.png", 
    3: "https://i.postimg.cc/66LhJR7h/mail-google.png",
    4: "https://i.postimg.cc/m2FpVpjk/image.png"
}
@bot.message_handler(commands=['url'])
def handle_url_command(message):
    if not message.reply_to_message:
        bot.send_message(message.chat.id, "Por favor, responda a uma mensagem contendo uma foto ou arquivo.")
        return

    msg = message.reply_to_message

    file_info = None
    file_name = None
    if msg.photo:
        file_info = bot.get_file(msg.photo[-1].file_id)
        file_name = "photo.jpg"
    elif msg.document:
        file_info = bot.get_file(msg.document.file_id)
        file_name = msg.document.file_name
    else:
        bot.send_message(message.chat.id, "Por favor, responda a uma foto ou arquivo.")
        return

    download_url = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"
    
    try:
        # Baixar o arquivo
        file_content = bot.download_file(file_info.file_path)
        with open(file_name, 'wb') as new_file:
            new_file.write(file_content)

        # Fazer upload do arquivo para o Telegraph
        link = upload_file(file_name)
        generated_link = "https://telegra.ph" + "".join(link)

        response_text = f"🖇️ <b>Link</b> - {generated_link}"

        bot.send_message(message.chat.id, text=response_text, parse_mode="HTML")
    except Exception as e:
        bot.send_message(message.chat.id, f"Erro ao processar o arquivo: {e}")
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)
def obter_subcategorias_sem_banner(categoria):
    try:
        conn, cursor = conectar_banco_dados()
        
        query = """
            SELECT DISTINCT p.subcategoria 
            FROM personagens p
            LEFT JOIN subcategorias s ON p.subcategoria = s.subcategoria
            WHERE s.subcategoria IS NULL AND p.categoria = %s
        """
        
        cursor.execute(query, (categoria,))
        subcategorias_sem_banner = cursor.fetchall()

        return [subcategoria[0] for subcategoria in subcategorias_sem_banner]
    
    except Exception as e:
        print(f"Erro ao obter subcategorias sem banner: {e}")
        return []
    finally:
        fechar_conexao(cursor, conn)

@bot.message_handler(commands=['sembanner'])
def listar_subcategorias_sem_banner(message):
    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.send_message(message.chat.id, "Formato incorreto. Use /sembanner {categoria}.")
            return

        categoria = parts[1].strip()
        subcategorias = obter_subcategorias_sem_banner(categoria)

        if not subcategorias:
            bot.send_message(message.chat.id, f"Todas as subcategorias da categoria '{categoria}' possuem banners.")
            return

        resposta = f"Subcategorias da categoria '{categoria}' sem banners:\n\n"
        limite_caracteres = 4096

        for subcategoria in subcategorias:
            if len(resposta) + len(subcategoria) + 2 < limite_caracteres:  # +2 para o "\n\n"
                resposta += f"𓇣 {subcategoria}\n"
            else:
                bot.send_message(message.chat.id, resposta)
                resposta = f"𓇣 {subcategoria}\n"

        if resposta:
            bot.send_message(message.chat.id, resposta)

    except Exception as e:
        print(f"Erro ao listar subcategorias sem banner: {e}")
        traceback.print_exc()
        bot.send_message(message.chat.id, "Ocorreu um erro ao processar a solicitação.")
# Inicialização do instaloader
L = Instaloader()
@bot.message_handler(commands=['reabastecer'])
def reabastecer_banco(message):
    try:
        args = message.text.split()
        if len(args) != 2 or not args[1].isdigit():
            bot.reply_to(message, "Uso: /reabastecer <número_de_cartas>")
            return

        num_cartas = int(args[1])
        if num_cartas <= 0:
            bot.reply_to(message, "O número de cartas deve ser maior que zero.")
            return

        conn, cursor = conectar_banco_dados()

        cursor.execute("SELECT id_personagem FROM personagens")
        personagens_ids = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT id_personagem FROM evento")
        eventos_ids = [row[0] for row in cursor.fetchall()]

        all_ids = personagens_ids + eventos_ids

        if not all_ids:
            bot.reply_to(message, "Nenhum personagem ou evento encontrado para reabastecer.")
            return

        reabastecidos = {}
        for _ in range(num_cartas):
            id_escolhido = random.choice(all_ids)
            quantidade = random.randint(1, 10)

            if id_escolhido in reabastecidos:
                reabastecidos[id_escolhido] += quantidade
            else:
                reabastecidos[id_escolhido] = quantidade

            cursor.execute("SELECT quantidade FROM banco_inventario WHERE id_personagem = %s", (id_escolhido,))
            quantidade_banco = cursor.fetchone()

            if quantidade_banco:
                nova_quantidade_banco = quantidade_banco[0] + quantidade
                cursor.execute("UPDATE banco_inventario SET quantidade = %s WHERE id_personagem = %s", (nova_quantidade_banco, id_escolhido))
            else:
                cursor.execute("INSERT INTO banco_inventario (id_personagem, quantidade) VALUES (%s, %s)", (id_escolhido, quantidade))

        conn.commit()

        resposta = "📦 Reabastecimento do banco:\n\n"
        for id_personagem, quantidade in reabastecidos.items():
            resposta += f"ID: {id_personagem} — Quantidade: {quantidade}\n"


        max_chars = 4096  
        partes = [resposta[i:i + max_chars] for i in range(0, len(resposta), max_chars)]
        for parte in partes:
            bot.send_message(message.chat.id, parte)

    except Exception as e:
        print(f"Erro ao reabastecer o banco: {e}")
        bot.reply_to(message, "Ocorreu um erro ao reabastecer o banco.")
    finally:
        fechar_conexao(cursor, conn)
@bot.message_handler(commands=['link'])
def processar_comando_link(message):
    try:
        command_parts = message.text.split()
        if len(command_parts) != 2:
            bot.reply_to(message, "Por favor, forneça o ID do personagem no formato '/link id_personagem'.")
            return

        id_personagem = command_parts[1]

        conn, cursor = conectar_banco_dados()
        query = "SELECT imagem FROM evento WHERE id_personagem = %s"
        cursor.execute(query, (id_personagem,))
        resultado = cursor.fetchone()

        if resultado:
            imagem_url = resultado[0]
            bot.reply_to(message, f"O link da imagem para o ID {id_personagem} é: {imagem_url}")
        else:
            bot.reply_to(message, f"Nenhuma imagem encontrada para o ID '{id_personagem}'.")

        fechar_conexao(cursor, conn)

    except Exception as e:
        bot.reply_to(message, f"Erro ao processar o comando /link: {e}")
        
def adicionar_borda(imagem_url, borda_url):
    try:

        response = requests.get(imagem_url)
        imagem = Image.open(BytesIO(response.content))

        response = requests.get(borda_url)
        borda = Image.open(BytesIO(response.content)).resize(imagem.size)

        imagem_com_borda = ImageOps.expand(imagem, border=(0, 0, 0, 0), fill='white')
        imagem_com_borda.paste(borda, (0, 0), borda)


        if imagem_com_borda.mode == 'RGBA':
            imagem_com_borda = imagem_com_borda.convert('RGB')

        resultado = BytesIO()
        imagem_com_borda.save(resultado, format='JPEG')
        resultado.seek(0)
        
        return resultado

    except Exception as e:
        raise ValueError(f"Erro ao adicionar borda: {e}")
# Emojis por categoria
emojis_categoria = {
    'Música': '☁️',
    'Séries': '🍄',
    'Animangá': '🌷',
    'Jogos': '🧶',
    'Filmes': '🍰',
    'Miscelânea': '🍂'
}   

@bot.message_handler(commands=['mudaridperfil'])
def mudar_id_perfil(message):
    try:
        partes = message.text.split()
        if len(partes) < 3:
            bot.send_message(message.chat.id, "Uso: /mudaridperfil idnovo idatual")
            return

        idnovo, idatual = partes[1], partes[2]

        confirmacao = f"Você deseja mudar o ID de {idatual} para {idnovo} em todas as tabelas relacionadas?"
        markup = telebot.types.InlineKeyboardMarkup()
        sim_button = telebot.types.InlineKeyboardButton("Sim", callback_data=f"confirmarmudancaid_{idnovo}_{idatual}_{message.from_user.id}")
        nao_button = telebot.types.InlineKeyboardButton("Não", callback_data="cancelar_mudanca_id")
        markup.add(sim_button, nao_button)
        bot.send_message(message.chat.id, confirmacao, reply_markup=markup)
    except Exception as e:
        bot.send_message(message.chat.id, f"Erro: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirmarmudancaid'))
def confirmar_mudanca_id(call):
    parts = call.data.split('_')
    if len(parts) != 4:
        bot.answer_callback_query(call.id, "Formato de dados inválido.", show_alert=True)
        return

    _, idnovo, idatual, user_id = parts[0], parts[1], parts[2], parts[3]

    bot.answer_callback_query(call.id, "Processando a mudança de ID...")

    conn, cursor = conectar_banco_dados()
    try:

        tabelas = ['anotacoes', 'diario', 'gif', 'historico_cartas_giradas', 'inventario', 'tags', 'usuarios', 'wishlist']
        for tabela in tabelas:
            cursor.execute(f"UPDATE {tabela} SET id_usuario = %s WHERE id_usuario = %s", (idnovo, idatual))
        conn.commit()

        # Registra no grupo especificado
        msg_log = f"Usuário {user_id} mudou ID de {idatual} para {idnovo} em {', '.join(tabelas)}."
        bot.send_message(-1002216029435, msg_log)
        bot.edit_message_text("ID atualizado com sucesso em todas as tabelas.", call.message.chat.id, call.message.message_id)
    except Exception as e:
        bot.send_message(call.message.chat.id, f"Erro ao atualizar o ID: {e}")


@bot.callback_query_handler(func=lambda call: call.data == 'cancelar_mudanca_id')
def cancelar_mudanca_id(call):
    bot.answer_callback_query(call.id, "Mudança de ID cancelada.")
    bot.edit_message_text("Mudança de ID cancelada.", call.message.chat.id, call.message.message_id)




@bot.message_handler(commands=['altsub'])
def alterar_subcategoria(message):
    try:
        params = message.text.split(' ', 1)[1:]
        if len(params) < 1 or '|' not in params[0]:
            bot.send_message(message.chat.id, "Uso: /altsub <subcategoria_atual> | <nova_subcategoria>")
            return
        
        subcategoria_atual, nova_subcategoria = params[0].split('|', 1)
        subcategoria_atual = subcategoria_atual.strip()
        nova_subcategoria = nova_subcategoria.strip()

        conn, cursor = conectar_banco_dados()
        sql = "UPDATE personagens SET subcategoria = %s WHERE subcategoria = %s"
        cursor.execute(sql, (nova_subcategoria, subcategoria_atual))
        conn.commit()

        if cursor.rowcount > 0:
            bot.send_message(message.chat.id, f"Subcategoria '{subcategoria_atual}' alterada para '{nova_subcategoria}' em {cursor.rowcount} personagens com sucesso!")
        else:
            bot.send_message(message.chat.id, f"Nenhum personagem encontrado com a subcategoria '{subcategoria_atual}'.")

    except Exception as e:
        bot.send_message(message.chat.id, f"Erro ao alterar a subcategoria dos personagens: {e}")

    finally:
        fechar_conexao(cursor, conn)
        
@bot.message_handler(commands=['altsubid'])
def alterar_subcategoria_por_id(message):
    try:
        params = message.text.split(' ', 2)[1:]
        if len(params) < 2:
            bot.send_message(message.chat.id, "Uso: /altsubid <id_personagem> <nova_subcategoria>")
            return
        id_personagem, nova_subcategoria = params

        conn, cursor = conectar_banco_dados()
        sql = "UPDATE personagens SET subcategoria = %s WHERE id_personagem = %s"
        cursor.execute(sql, (nova_subcategoria, id_personagem))
        conn.commit()

        if cursor.rowcount > 0:
            bot.send_message(message.chat.id, f"Subcategoria do personagem com ID {id_personagem} alterada para '{nova_subcategoria}' com sucesso!")
        else:
            bot.send_message(message.chat.id, f"Nenhum personagem encontrado com o ID {id_personagem}.")

    except Exception as e:
        bot.send_message(message.chat.id, f"Erro ao alterar a subcategoria do personagem: {e}")

    finally:
        fechar_conexao(cursor, conn)

@bot.message_handler(commands=['delcard'])
def deletar_personagem(message):
    try:
        params = message.text.split(' ', 1)[1:]
        if len(params) < 1:
            bot.send_message(message.chat.id, "Uso: /delcard <id_personagem>")
            return
        id_personagem = params[0]

        conn, cursor = conectar_banco_dados()
        sql = "DELETE FROM personagens WHERE id_personagem = %s"
        cursor.execute(sql, (id_personagem,))
        conn.commit()

        if cursor.rowcount > 0:
            bot.send_message(message.chat.id, f"Personagem com ID {id_personagem} deletado com sucesso!")
        else:
            bot.send_message(message.chat.id, f"Nenhum personagem encontrado com o ID {id_personagem}.")

    except Exception as e:
        bot.send_message(message.chat.id, f"Erro ao deletar o personagem: {e}")

    finally:
        fechar_conexao(cursor, conn)
@bot.message_handler(commands=['addbanner'])
def adicionar_banner(message):
    try:
        params = message.text.split(' ', 1)[1:]
        
        if len(params) < 1:
            bot.send_message(message.chat.id, "Uso: /addbanner <nome_subcategoria> | <link_da_imagem>")
            return

        if '|' not in params[0]:
            bot.send_message(message.chat.id, "Formato incorreto. Uso: /addbanner <nome_subcategoria> | <link_da_imagem>")
            return
        
        nome_subcategoria, link_imagem = params[0].split('|', 1)
        nome_subcategoria = nome_subcategoria.strip()
        link_imagem = link_imagem.strip()
        
        conn, cursor = conectar_banco_dados()

        cursor.execute("SELECT * FROM subcategorias WHERE nomesub = %s", (nome_subcategoria,))
        subcategoria_existente = cursor.fetchone()
        
        if subcategoria_existente:
            bot.send_message(message.chat.id, f"A subcategoria '{nome_subcategoria}' já possui imagem.")
        else:
            sql = "INSERT INTO subcategorias (nomesub, subcategoria, Imagem) VALUES (%s, %s, %s)"
            cursor.execute(sql, (nome_subcategoria, nome_subcategoria, link_imagem))
            conn.commit()
            
            bot.send_message(message.chat.id, f"Banner da subcategoria '{nome_subcategoria}' adicionado com sucesso!")
            mensagem_log = f"Usuário {message.from_user.first_name} (ID {message.from_user.id}) atualizou a imagem do Banner da categoria {nome_subcategoria} para: {link_imagem}"

            bot.send_message(-1002216029435, mensagem_log)
        fechar_conexao(cursor, conn)

    except Exception as e:
        print(f"Erro ao adicionar o banner da subcategoria: {e}")
        bot.send_message(message.chat.id, f"Erro ao adicionar o banner da subcategoria: {e}")


        
@bot.message_handler(commands=['delbanner'])
def deletar_banner(message):
    try:
        params = message.text.split(' ', 1)[1:]
        if len(params) < 1:
            bot.send_message(message.chat.id, "Uso: /delbanner <nome_subcategoria>")
            return
        nome_subcategoria = params[0]

        conn, cursor = conectar_banco_dados()
        
        sql = "DELETE FROM subcategorias WHERE nomesub = %s"
        cursor.execute(sql, (nome_subcategoria,))
        conn.commit()

        if cursor.rowcount > 0:
            bot.send_message(message.chat.id, f"Banner da subcategoria '{nome_subcategoria}' deletado com sucesso!")
        else:
            bot.send_message(message.chat.id, f"Nenhuma subcategoria encontrada com o nome '{nome_subcategoria}'.")

    except Exception as e:
        bot.send_message(message.chat.id, f"Erro ao deletar o banner da subcategoria: {e}")

    finally:
        fechar_conexao(cursor, conn)
                    
@bot.message_handler(commands=['altnome'])
def alterar_nome(message):
    try:
        params = message.text.split(' ', 2)[1:]
        if len(params) < 2:
            bot.send_message(message.chat.id, "Uso: /altnome <id_personagem> <novo_nome>")
            return
        id_personagem, novo_nome = params

        conn, cursor = conectar_banco_dados()
        sql = "UPDATE personagens SET nome = %s WHERE id_personagem = %s"
        cursor.execute(sql, (novo_nome, id_personagem))
        conn.commit()

        if cursor.rowcount > 0:
            bot.send_message(message.chat.id, f"Nome do personagem com ID {id_personagem} alterado para {novo_nome} com sucesso!")
        else:
            bot.send_message(message.chat.id, f"Nenhum personagem encontrado com o ID {id_personagem}.")

    except Exception as e:
        bot.send_message(message.chat.id, f"Erro ao alterar o nome do personagem: {e}")

    finally:
        fechar_conexao(cursor, conn)
def add_personagem(chat_id, categoria, nome, subcategoria, link_imagem):
    try:
        conn, cursor = conectar_banco_dados()
    
        cursor.execute(f"SELECT MAX(CAST(id_personagem AS UNSIGNED)) FROM personagens WHERE categoria = %s", (categoria,))
        max_id = cursor.fetchone()[0]
        if max_id is None:
            max_id = 0
        novo_id = max_id + 1

        emoji = emojis_categoria[categoria]


        sql = """
            INSERT INTO personagens (id_personagem, nome, subcategoria, emoji, categoria, imagem)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (novo_id, nome, subcategoria, emoji, categoria, link_imagem))
        conn.commit()
        user_message = f"Personagem adicionado com sucesso!\n\nID: {novo_id}\nNome: {nome}\nCategoria: {categoria}\nSubcategoria: {subcategoria}\nLink da Imagem: {link_imagem}"
        bot.send_message(chat_id, user_message)
        
        group_message = f"Novo Personagem Adicionado:\n\nID: {novo_id}\nNome: {nome}\nCategoria: {categoria}\nSubcategoria: {subcategoria}\nLink da Imagem: {link_imagem}"
        bot.send_message(-1002216029435, group_message)
        
        return novo_id 

    except Exception as e:
        bot.send_message(chat_id, f"Erro ao adicionar personagem: {e}")
        return None 

    finally:
        fechar_conexao(cursor, conn)


def obter_ultima_subcategoria(categoria):
    conn, cursor = conectar_banco_dados()
    try:
        cursor.execute("""
            SELECT id_personagem, nome, subcategoria
            FROM personagens
            WHERE categoria = %s
            ORDER BY id_personagem DESC
            LIMIT 1
        """, (categoria,))
        result = cursor.fetchone()
        return result
    except Exception as e:
        print(f"Erro ao buscar a última subcategoria: {e}")
        return None
    finally:
        fechar_conexao(cursor, conn)
        
def buscar_personagens_por_subcategoria(subcategoria, id_inicial=None):
    conn, cursor = conectar_banco_dados()
    try:
        if id_inicial:
            query = """
                SELECT id_personagem, nome
                FROM personagens
                WHERE subcategoria = %s AND id_personagem >= %s
                ORDER BY id_personagem
            """
            params = (subcategoria, id_inicial)
        else:
            query = """
                SELECT id_personagem, nome
                FROM personagens
                WHERE subcategoria = %s
                ORDER BY id_personagem
            """
            params = (subcategoria,)
        
        cursor.execute(query, params)
        resultados = cursor.fetchall()
        return resultados
    except Exception as e:
        print(f"Erro ao buscar personagens da subcategoria {subcategoria}: {e}")
        return []
    finally:
        fechar_conexao(cursor, conn)

       
@bot.message_handler(commands=['ultimasub'])
def enviar_personagens_ultima_subcategoria(message):
    partes = message.text.split()
    categoria = partes[1] if len(partes) > 1 else 'séries'
    id_inicial = int(partes[2]) if len(partes) > 2 and partes[2].isdigit() else None

    ultima_subcategoria = obter_ultima_subcategoria(categoria)
    
    if ultima_subcategoria:
        _, _, subcategoria = ultima_subcategoria
        personagens = buscar_personagens_por_subcategoria(subcategoria, id_inicial)
        if personagens:
            resposta = f"Adição de Personagens:\n\n{subcategoria}:\n\n"
            for id_personagem, nome in personagens:
                resposta += f"{id_personagem}, {nome}\n"
        else:
            resposta = f"Nenhum personagem encontrado na subcategoria '{subcategoria}' a partir do ID {id_inicial}."
    else:
        resposta = f"Nenhuma subcategoria foi adicionada recentemente para a categoria '{categoria}'."
    
    bot.send_message(message.chat.id, resposta)


def process_addition(message, categoria):
    try:

        entries = message.text.split(' ', 1)[1].split('|')
        if not entries:
            bot.send_message(message.chat.id, f"Uso: /add{categoria.lower()} <nome>, <subcategoria>, <link_da_imagem> | <nome>, <subcategoria>, <link da imagem> ...")
            return

        user_name = message.from_user.first_name  
        added_items = []
        group_message = f"Adição de Personagens em {categoria} por {message.from_user.first_name} (ID {message.from_user.id}) :\n\n"
        for entry in entries:

            params = entry.split(',')
            if len(params) != 3:
                continue 

            nome = params[0].strip()
            subcategoria = params[1].strip()
            link_imagem = params[2].strip()

            if not link_imagem.startswith('http'):
                continue  
            id_personagem = add_personagem(message.chat.id, categoria, nome, subcategoria, link_imagem)
            if id_personagem:
                added_items.append(f"{id_personagem}, {nome}")
                group_message += f"{id_personagem}, {nome}\n"

        if added_items:
            bot.send_message(message.chat.id, f"Adicionados com sucesso:\n" + "\n".join(added_items))
            bot.send_message(-1002216029435, group_message)
        else:
            bot.send_message(message.chat.id, "Nenhuma entrada válida foi adicionada.")

    except Exception as e:
        bot.send_message(message.chat.id, f"Erro ao processar comando /add{categoria.lower()}: {e}")


@bot.message_handler(commands=['addserie'])
def add_serie(message):
    process_addition(message, 'Séries')

@bot.message_handler(commands=['addmusica'])
def add_musica(message):
    process_addition(message, 'Música')

@bot.message_handler(commands=['addfilme'])
def add_filme(message):
    process_addition(message, 'Filmes')

@bot.message_handler(commands=['addanime'])
def add_anime(message):
    process_addition(message, 'Animangá')

@bot.message_handler(commands=['addmisc'])
def add_misc(message):
    process_addition(message, 'Miscelânea')

@bot.message_handler(commands=['addjogo'])
def add_jogo(message):
    process_addition(message, 'Jogos')


            
@bot.message_handler(commands=['emojip'])
def atualizar_emojis_personagens(message):
    try:
        conn, cursor = conectar_banco_dados()

        # Atualizar emojis para cada categoria
        emojis_categoria = {
            'musica': '☁️',
            'séries': '🍄',
            'animangá': '🌷',
            'jogos': '🧶',
            'filmes': '🍰',
            'miscelanea': '🍂'
        }

        for categoria, emoji in emojis_categoria.items():
            query = "UPDATE personagens SET emoji = %s WHERE categoria = %s AND emoji is null"
            cursor.execute(query, (emoji, categoria))

        conn.commit()
        fechar_conexao(cursor, conn)

        bot.reply_to(message, "Emojis atualizados com sucesso!")

    except Exception as e:
        bot.reply_to(message, f"Erro ao atualizar emojis: {e}")
        
@bot.message_handler(commands=['imagemev'])
def processar_comando_imagemev(message):
    try:
        command_parts = message.text.split()
        if len(command_parts) != 3:
            bot.reply_to(message, "Por favor, forneça o ID do personagem e o novo link da imagem no formato '/imagemev id link'.")
            return

        id_personagem = command_parts[1]
        novo_link = command_parts[2]

        conn, cursor = conectar_banco_dados()
        query = "UPDATE evento SET imagem = %s WHERE id_personagem = %s"
        cursor.execute(query, (novo_link, id_personagem))
        conn.commit()
        fechar_conexao(cursor, conn)

        bot.reply_to(message, f"Imagem do evento com ID {id_personagem} atualizada com sucesso!")

    except Exception as e:
        bot.reply_to(message, f"Erro ao atualizar a imagem do evento: {e}")   
@bot.message_handler(commands=['addsubmenu'])
def addsubmenu(message):
    try:
        comando = message.text.split('/addsubmenu', 1)[1].strip()
        partes_comando = comando.split(' ')
        if len(partes_comando) < 2:
            bot.send_message(message.chat.id, "Por favor, forneça os IDs dos personagens e o nome do submenu. Exemplo: /addsubmenu id1 id2 id3 - submenu")
            return

        indice_hifen = partes_comando.index('-')
        ids_personagens = partes_comando[:indice_hifen]
        nome_submenu = ' '.join(partes_comando[indice_hifen + 1:]).strip()

        conn, cursor = conectar_banco_dados()

        for id_personagem in ids_personagens:
            cursor.execute(
                "UPDATE personagens SET submenu = %s WHERE id_personagem = %s",
                (nome_submenu, id_personagem)
            )

        conn.commit()

        bot.send_message(message.chat.id, f"Submenu '{nome_submenu}' adicionado com sucesso aos personagens: {', '.join(ids_personagens)}")
    
    except ValueError:
        bot.send_message(message.chat.id, "Formato de comando inválido. Certifique-se de usar o formato correto: /addsubmenu id1 id2 id3 - submenu")
    
    except Exception as e:
        print(f"Erro ao adicionar submenu: {e}")
        bot.send_message(message.chat.id, f"Erro ao adicionar submenu: {e}")
    
    finally:
        fechar_conexao(cursor, conn)


@bot.message_handler(commands=['tabelasubmenu'])
def tabela_submenu(message):
    try:
        partes = message.text.split(' ', 1)
        if len(partes) < 2:
            bot.send_message(message.chat.id, "Por favor, forneça a subcategoria e o submenu no formato: /tabelasubmenu subcategoria - submenu")
            return
        subcategoria_e_submenu = partes[1].split(' - ')
        if len(subcategoria_e_submenu) != 2:
            bot.send_message(message.chat.id, "Formato incorreto. Use: /tabelasubmenu subcategoria - submenu")
            return

        subcategoria = subcategoria_e_submenu[0].strip()
        submenu = subcategoria_e_submenu[1].strip()

        if not subcategoria or not submenu:
            bot.send_message(message.chat.id, "Formato incorreto. Use: /tabelasubmenu subcategoria - submenu")
            return
        conn, cursor = conectar_banco_dados()
        cursor.execute(
            "INSERT INTO subcategoria_submenu (subcategoria, submenu) VALUES (%s, %s)",
            (subcategoria, submenu)
        )
        conn.commit()

        bot.send_message(message.chat.id, f"Subcategoria '{subcategoria}' e submenu '{submenu}' adicionados na tabela com sucesso.")

    except Exception as e:
        print(f"Erro ao adicionar na tabela subcategoria_submenu: {e}")
        bot.send_message(message.chat.id, "Erro ao adicionar na tabela subcategoria_submenu.")

    finally:
        fechar_conexao(cursor, conn)
             
@bot.message_handler(commands=['emoji'])
def atualizar_emojis(message):
    try:
        conn, cursor = conectar_banco_dados()


        query_amor = "UPDATE evento SET emoji = '💐' WHERE evento = 'amor'"
        cursor.execute(query_amor)
        query_inv = "UPDATE evento SET emoji = '🪴' WHERE evento = 'fixo'"
        cursor.execute(query_inv)
        query_fixo = "UPDATE evento SET emoji = '☃️' WHERE evento = 'Inverno'"
        cursor.execute(query_fixo)
        query_aniversario = "UPDATE evento SET emoji = '🎁' WHERE evento = 'aniversario'"
        cursor.execute(query_aniversario)

        conn.commit()
        fechar_conexao(cursor, conn)

        bot.reply_to(message, "Emojis atualizados com sucesso!")

    except Exception as e:
        bot.reply_to(message, f"Erro ao atualizar emojis: {e}")        
@bot.message_handler(commands=['borda'])
def processar_comando_borda(message):
    try:
        comando_parts = message.text.split(' ')
        if len(comando_parts) != 3:
            bot.reply_to(message, "Por favor, forneça a opção de borda e o link da foto no formato '/borda <opcao_borda> <link_foto>'.")
            return

        opcao_borda = int(comando_parts[1])
        link_foto = comando_parts[2]

        # Verificar se a opção de borda é válida
        if opcao_borda not in borda_map:
            bot.reply_to(message, "Opção de borda inválida. Use /borda 1, /borda 2, /borda 3 ou /borda 4.")
            return

        msg_processamento = bot.reply_to(message, "Processando a imagem, por favor aguarde...")
        
        borda_url = borda_map[opcao_borda]
        imagem_com_borda = adicionar_borda(link_foto, borda_url)

        bot.send_photo(message.chat.id, imagem_com_borda, caption="Aqui está sua foto com a borda selecionada.", parse_mode="HTML")
        bot.delete_message(chat_id=msg_processamento.chat.id, message_id=msg_processamento.message_id)

    except Exception as e:
        bot.reply_to(message, f"Erro ao processar o comando /borda: {e}")

cancelando = {}
db_lock = threading.Lock()
respostas = {}

def fechar_conexao(cursor, conn):
    if cursor is not None:
        cursor.close()
    if conn is not None:
        conn.close()   
# Definição da lista de comandos
comandos = [
    "/start - Iniciar o bot",
    "/ajuda - Exibir a lista de comandos",
    "/adc - Adicionar um novo personagem",
    "/adcmassa - Adicionar personagens em massa",
    "/pesquisar_nome - Pesquisar personagens por nome",
    "/pesquisar_id - Pesquisar personagens por ID",
    "/pesquisar_categoria - Pesquisar personagens por categoria",
    "/pesquisar_subcategoria - Pesquisar personagens por subcategoria",
    "/allcateg - Listar todas as categorias",
    "/allsubcateg - Listar todas as subcategorias",
    "/allsubmenu - Listar todos os submenus",
    "/listar_todos - Listar todos os personagens",
    "/last_id - Encontrar o último ID ocupado por uma categoria"
]

def voltar(message):
    markup = InlineKeyboardMarkup()
    markup.row_width =  4 # Ajuste o número de botões por linha, se necessário


    botoes = [
        InlineKeyboardButton("Adição", callback_data="adição"),
        InlineKeyboardButton("Pesquisa", callback_data="pesquisa"),
        InlineKeyboardButton("All", callback_data="all"),
        InlineKeyboardButton("Outros", callback_data="outros"),
    ]     


    markup.add(*botoes)

    bot.edit_message_text(chat_id=message.chat.id,text="Bem-vindo! Escolha um comando:",message_id=message.id,reply_markup=markup)
@bot.callback_query_handler(func=lambda call: call.data.startswith("status_"))
def atualizar_status(call):
    novo_status = call.data.split('_')[1]
    user_id = call.from_user.id
    try:
        conn, cursor = conectar_banco_dados()
        cursor.execute("UPDATE adms SET status = %s WHERE idadm = %s", (novo_status, user_id))
        conn.commit()
        bot.edit_message_text(f"Status atualizado para {novo_status}.", chat_id=call.message.chat.id, message_id=call.message.message_id)
    except Exception as e:
        bot.send_message(call.message.chat.id, f"Erro ao atualizar status: {e}")
    finally:
        fechar_conexao(cursor, conn)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    markup.row_width =  4 # Ajuste o número de botões por linha, se necessário


    botoes = [
        InlineKeyboardButton("Adição", callback_data="adição"),
        InlineKeyboardButton("Pesquisa", callback_data="pesquisa"),
        InlineKeyboardButton("All", callback_data="all"),
        InlineKeyboardButton("Outros", callback_data="outros"),
    ]     


    markup.add(*botoes)


    bot.send_message(message.chat.id, "Bem-vindo! Escolha um comando:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == "ajuda":
        mostrar_comandos(call.message)
    elif call.data == "adição":
        markup = InlineKeyboardMarkup()
        
        markup.row(telebot.types.InlineKeyboardButton(text="Adição", callback_data="adc"))
        markup.row(telebot.types.InlineKeyboardButton(text="Adição em Massa", callback_data="adcmassa"))
        markup.row(telebot.types.InlineKeyboardButton(text="Ajuda", callback_data="ajuda"))
        markup.row(telebot.types.InlineKeyboardButton(text="Voltar", callback_data="voltar"))
        
        bot.edit_message_text(chat_id=call.message.chat.id,text="Escolha um comando de adição:",message_id=call.message.id,reply_markup=markup)
    elif call.data == "pesquisa":
        markup = InlineKeyboardMarkup()
        
        markup.row(telebot.types.InlineKeyboardButton("pesquisar nome", callback_data="pesquisar_nome"))
        markup.row(telebot.types.InlineKeyboardButton("pesquisar id", callback_data="pesquisar_id"))
        markup.row(telebot.types.InlineKeyboardButton("pesquisar categoria", callback_data="pesquisar_categoria"))
        markup.row(telebot.types.InlineKeyboardButton(text="Ajuda", callback_data="ajuda"))
        markup.row(telebot.types.InlineKeyboardButton(text="Voltar", callback_data="voltar"))
        bot.edit_message_text(chat_id=call.message.chat.id,text="Escolha um comando de pesquisa:",message_id=call.message.id,reply_markup=markup)
    elif call.data == "all":
        markup = InlineKeyboardMarkup()
        
        markup.row(telebot.types.InlineKeyboardButton("all categorias", callback_data="allcateg"))
        markup.row(telebot.types.InlineKeyboardButton("all subcategorias", callback_data="allsubcateg"))
        markup.row(telebot.types.InlineKeyboardButton("all submenu", callback_data="allsubmenu"))
        markup.row(telebot.types.InlineKeyboardButton(text="Ajuda", callback_data="ajuda"))
        markup.row(telebot.types.InlineKeyboardButton(text="Voltar", callback_data="voltar"))
        bot.edit_message_text(chat_id=call.message.chat.id,text="Escolha um comando para ver tudo:",message_id=call.message.id,reply_markup=markup)
 
    elif call.data == "outros":
        markup = InlineKeyboardMarkup()

        markup.row(telebot.types.InlineKeyboardButton("listar todos", callback_data="listar_todos"))
        markup.row(telebot.types.InlineKeyboardButton("last id", callback_data="last_id"))
        markup.row(telebot.types.InlineKeyboardButton("all submenu", callback_data="allsubmenu"))
        markup.row(telebot.types.InlineKeyboardButton(text="Ajuda", callback_data="ajuda"))
        markup.row(telebot.types.InlineKeyboardButton(text="Voltar", callback_data="voltar"))
        bot.edit_message_text(chat_id=call.message.chat.id,text="Escolha um comando para ver tudo:",message_id=call.message.id,reply_markup=markup)
    elif call.data == "voltar":
        voltar(call.message)
    # elif call.data == "adc":
    #     adc(call.message)
    # elif call.data == "adcmassa":
    #     adcmassa(call.message)
    # elif call.data == "pesquisar_nome":
    #     pesquisar_nome(call.message)
    # elif call.data == "pesquisar_id":
    #     pesquisar_id(call.message)
    # elif call.data == "pesquisar_categoria":
    #     pesquisar_categoria(call.message)
    # elif call.data == "pesquisar_subcategoria":
    #     pesquisar_subcategoria(call.message)
    # elif call.data == "allcateg":
    #     allcateg(call.message)
    # elif call.data == "allsubcateg":
    #     allsubcateg(call.message)
    # elif call.data == "allsubmenu":
    #     allsubmenu(call.message)
    # elif call.data == "listar_todos":
    #     listar_todos(call.message)
    # elif call.data == "last_id":
    #     digiteid(call.message)

# Comando para exibir a lista de administradores
@bot.message_handler(commands=['adms'])
def listar_adms(message):
    try:
        conn, cursor = conectar_banco_dados()
        cursor.execute("SELECT nome, status FROM adms")
        adms = cursor.fetchall()
        
        if not adms:
            bot.send_message(message.chat.id, "Nenhum administrador encontrado.")
            return
        
        resposta = "Lista de Administradores:\n\n"
        for nome, status in adms:
            if status.lower() == "online":
                emoji = "🍏"
            elif status.lower() == "offline":
                emoji = "🍎"
            elif status.lower() == "ocupado":
                emoji = "🍊"
            else:
                emoji = "❓"
            
            resposta += f"{nome} - {status.capitalize()} {emoji}\n"
        
        bot.send_message(message.chat.id, resposta)
    
    except Exception as e:
        bot.send_message(message.chat.id, f"Erro ao listar administradores: {e}")
    finally:
        fechar_conexao(cursor, conn)
# Comando para atualizar o status
@bot.message_handler(commands=['statz'])
def escolher_status(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Online", callback_data="status_online"))
    markup.add(types.InlineKeyboardButton("Offline", callback_data="status_offline"))
    markup.add(types.InlineKeyboardButton("Ocupado", callback_data="status_ocupado"))
    bot.send_message(message.chat.id, "Escolha seu status:", reply_markup=markup)


# Comando para atualizar a foto
@bot.message_handler(commands=['foto'])
def atualizar_foto(message):
    bot.reply_to(message, "Por favor, envie o link da nova foto:")
    bot.register_next_step_handler(message, processar_foto)

def processar_foto(message):
    nova_foto = message.text.strip()
    user_id = message.from_user.id
    try:
        conn, cursor = conectar_banco_dados()
        cursor.execute("UPDATE adms SET foto = %s WHERE idadm = %s", (nova_foto, user_id))
        conn.commit()
        bot.send_message(message.chat.id, "Foto atualizada com sucesso!")
    except Exception as e:
        bot.send_message(message.chat.id, f"Erro ao atualizar foto: {e}")
    finally:
        fechar_conexao(cursor, conn)


# Comando para atualizar a bio
@bot.message_handler(commands=['bio'])
def atualizar_bio(message):
    bot.reply_to(message, "Por favor, escreva a nova bio:")
    bot.register_next_step_handler(message, processar_bio)

def processar_bio(message):
    nova_bio = message.text.strip()
    user_id = message.from_user.id
    try:
        conn, cursor = conectar_banco_dados()
        cursor.execute("UPDATE adms SET bio = %s WHERE idadm = %s", (nova_bio, user_id))
        conn.commit()
        bot.send_message(message.chat.id, "Bio atualizada com sucesso!")
    except Exception as e:
        bot.send_message(message.chat.id, f"Erro ao atualizar bio: {e}")
    finally:
        fechar_conexao(cursor, conn)
# Comando para exibir o perfil da pessoa

def criar_marcacao_metricas(user_id, metric, new_value):
    markup = types.InlineKeyboardMarkup()
    botao_coracao = types.InlineKeyboardButton(f"❤️ {new_value if metric == 'sexy' else '❤️'}", callback_data=f"sexy_{user_id}")
    botao_legal = types.InlineKeyboardButton(f"👍 {new_value if metric == 'legal' else '👍'}", callback_data=f"legal_{user_id}")
    botao_confiavel = types.InlineKeyboardButton(f"🤝 {new_value if metric == 'confiavel' else '🤝'}", callback_data=f"confiavel_{user_id}")
    botao_fas = types.InlineKeyboardButton(f"🌟 {new_value if metric == 'fas' else '🌟'}", callback_data=f"fas_{user_id}")
    markup.add(botao_coracao, botao_legal, botao_confiavel, botao_fas)
    return markup
# Comando para atualizar o nome
@bot.message_handler(commands=['nome'])
def atualizar_nome(message):
    bot.reply_to(message, "Por favor, escreva o novo nome:")
    bot.register_next_step_handler(message, processar_nome)

def processar_nome(message):
    novo_nome = message.text.strip()
    user_id = message.from_user.id
    try:
        conn, cursor = conectar_banco_dados()
        cursor.execute("UPDATE adms SET nome = %s WHERE idadm = %s", (novo_nome, user_id))
        conn.commit()
        bot.send_message(message.chat.id, "Nome atualizado com sucesso!")
    except Exception as e:
        bot.send_message(message.chat.id, f"Erro ao atualizar nome: {e}")
    finally:
        fechar_conexao(cursor, conn)

        
# Função para exibir a lista de comandos
@bot.message_handler(commands=['ajuda'])
def mostrar_comandos(message):
    chat_id = message.chat.id
    lista_comandos = "\n\n".join(comandos)
    bot.edit_message_text(chat_id=message.chat.id,text= f"Lista de comandos disponíveis:\n\n{lista_comandos}",message_id=message.id)

# Função para cancelar a ação em andamento
def cancelar_comando(chat_id):
    if chat_id in cancelando:
        del cancelando[chat_id]

def digiteid(message):
    bot.send_message(message.chat.id, "Por favor, digite a categoria:")
    bot.register_next_step_handler(message, encontrar_ultimo_id_por_categoria)
# Comando para adicionar personagens
def fechar_conexao(cursor, conn):
    cursor.close()
    conn.close()

# Mapear emojis de acordo com a categoria
emoji_por_categoria = {
    'Música': '☁️',
    'Séries': '🍄',
    'Animangá': '🌷',
    'Filmes': '🍰',
    'Jogos': '🧶',
    'Miscelânea': '🍂'
}

# Comando para adicionar personagens
@bot.message_handler(commands=['addpersonagem'])
def iniciar_add_personagem(message):
    bot.reply_to(message, "Por favor, forneça os detalhes do personagem no formato:\n\nnome, subcategoria, categoria, imagem, submenu, cr")

def processar_add_personagem(message):
    try:
        user_input = message.text.split(',')
        if len(user_input) != 6:
            bot.reply_to(message, "Formato incorreto. Por favor, forneça os detalhes no formato:\n\nnome, subcategoria, categoria, imagem, submenu, cr")
            return

        nome = user_input[0].strip()
        subcategoria = user_input[1].strip()
        categoria = user_input[2].strip()
        imagem = user_input[3].strip()
        submenu = user_input[4].strip()
        cr = user_input[5].strip()
        emoji = emoji_por_categoria.get(categoria, '❓')  # Emoji padrão caso a categoria não seja encontrada

        nome = None if nome.lower() == 'null' else nome
        subcategoria = None if subcategoria.lower() == 'null' else subcategoria
        categoria = None if categoria.lower() == 'null' else categoria
        imagem = None if imagem.lower() == 'null' else imagem
        submenu = None if submenu.lower() == 'null' else submenu
        cr = None if cr.lower() == 'null' else cr
        total = None

        adicionar_personagem(nome, subcategoria, emoji, categoria, imagem, submenu, cr, total)
        bot.reply_to(message, f"Personagem '{nome}' adicionado com sucesso!")

    except ValueError:
        bot.reply_to(message, "Erro no formato do total. Por favor, forneça um número válido para o total.")
        bot.register_next_step_handler(message, processar_add_personagem)
    except Exception as e:
        bot.reply_to(message, f"Erro ao adicionar personagem: {e}")

def adicionar_personagem(nome, subcategoria, emoji, categoria, imagem, submenu, cr, total):
    try:
        conn, cursor = conectar_banco_dados()
        cursor.execute("INSERT INTO personagens (nome, subcategoria, emoji, categoria, imagem, submenu, cr, total) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                       (nome, subcategoria, emoji, categoria, imagem, submenu, cr, total))
        conn.commit()
    except Exception as e:
        print(f"Erro ao adicionar personagem: {e}")
    finally:
        fechar_conexao(cursor, conn)
# Função para encontrar o último ID ocupado por uma categoria
@bot.message_handler(commands=['lastid'])
def encontrar_ultimo_id_por_categoria(message):
    chat_id = message.chat.id
    command_parts = message.text.split()

    if len(command_parts) == 2:
        texto = command_parts[1]
        categoria = texto
        sql = "SELECT MAX(id_personagem), nome, subcategoria FROM personagens WHERE categoria = %s GROUP BY nome, subcategoria ORDER BY MAX(id_personagem) DESC LIMIT 1"
        values = (categoria,)

        try:
            # Executa o comando SQL
            cursor.execute(sql, values)
            resultado = cursor.fetchone()

            if resultado and resultado[0] is not None:
                ultimo_id = resultado[0]
                nome = resultado[1]
                subcategoria = resultado[2]
                mensagem = f"O último ID ocupado pela categoria '{categoria}' é: {ultimo_id} - {nome} - {subcategoria}"
                bot.send_message(chat_id, mensagem)
            else:
                bot.send_message(chat_id, f"Nenhum ID encontrado para a categoria '{categoria}'.")
        except mysql.connector.Error as err:
            print(f"Erro MySQL: {err}")
        finally:
            # Certifique-se de commitar as alterações e fechar o cursor e a conexão
            if 'cursor' in locals() and cursor is not None:
                cursor.close()
            if 'connection' in locals() and conn is not None:
                conn.commit()
                conn.close()

# Função para listar todas as categorias
@bot.message_handler(commands=['allcateg'])
def listar_categorias(message):
    chat_id = message.chat.id
    cursor.execute("SELECT DISTINCT categoria FROM personagens")
    categorias = cursor.fetchall()

    if categorias:
        # Criar a lista de categorias (extrair primeiro elemento da tupla)
        lista_categorias = [categoria[0] for categoria in categorias]

        # Dividir a lista em partes para enviar em mensagens separadas
        chunk_size = 10  # Quantidade de categorias por mensagem
        for i in range(0, len(lista_categorias), chunk_size):
            chunk = lista_categorias[i:i + chunk_size]
            mensagem = f"Lista de Categorias:\n" + "\n".join(chunk)
            bot.send_message(chat_id, mensagem)
    else:
        bot.send_message(chat_id, "Nenhuma categoria encontrada no banco de dados.")


# Função para listar todas as subcategorias
@bot.message_handler(commands=['allsubcateg'])
def listar_subcategorias(message):
    chat_id = message.chat.id

    # Dicionário que mapeia categorias aos emojis correspondentes
    categorias_emoji = {
        "Música": "☁️",
        "Filmes": "🍰",
        "Jogos": "🧶",
        "Miscelânea": "🍂",
        "Séries": "🍄",
        "Animangá": "🌷"
    }

    cursor.execute("SELECT DISTINCT subcategoria, categoria FROM personagens")
    subcategorias = cursor.fetchall()

    if subcategorias:
        # Criar a lista de subcategorias com emojis
        lista_subcategorias = [f"{categorias_emoji[categoria]} {emoji} - {categoria}" for emoji, categoria in subcategorias]

        # Dividir a lista em partes para enviar em mensagens separadas
        chunk_size = 100  # Quantidade de subcategorias por mensagem
        for i in range(0, len(lista_subcategorias), chunk_size):
            chunk = lista_subcategorias[i:i + chunk_size]
            mensagem = f"Lista de Subcategorias:\n" + "\n".join(chunk)
            bot.send_message(chat_id, mensagem)
    else:
        bot.send_message(chat_id, "Nenhuma subcategoria encontrada no banco de dados.")


# Função para listar todos os submenus
@bot.message_handler(commands=['allsubmenu'])
def listar_submenus(message):
    chat_id = message.chat.id
    cursor.execute("SELECT DISTINCT submenu FROM personagens")
    submenus = cursor.fetchall()

    if submenus:
        lista_submenus = "\n".join([submenu[0] for submenu in submenus])

        # Dividir a lista em partes para enviar em mensagens separadas
        chunk_size = 10  # Quantidade de submenus por mensagem
        for i in range(0, len(lista_submenus), chunk_size):
            chunk = lista_submenus[i:i + chunk_size]
            mensagem = f"Lista de Submenus:\n" + "\n".join(chunk)
            bot.send_message(chat_id, mensagem)
    else:
        bot.send_message(chat_id, "Nenhum submenu encontrado no banco de dados.")


# Função para pesquisar cartas por categoria de forma paginada
def pesquisar_categoria_paginada(categoria, page, chat_id):
    page_size = 10  # Quantidade de resultados por página

    # Calcular o índice de início e fim da página
    start_index = (page - 1) * page_size
    end_index = start_index + page_size

    sql = "SELECT id_personagem, nome, subcategoria, categoria, submenu FROM personagens WHERE categoria = %s LIMIT %s, %s"
    values = (categoria, start_index, page_size)

    cursor.execute(sql, values)
    resultados = cursor.fetchall()

    if resultados:
        mensagem = f"Resultados da pesquisa (Página {page}):\n"
        for resultado in resultados:
            id, nome, subcategoria, categoria, submenu = resultado
            mensagem += f"ID: {id}, Nome: {nome}, Subcategoria: {subcategoria}, Categoria: {categoria}, Submenu: {submenu}\n"

        # Cria o teclado para a paginação
        markup = types.InlineKeyboardMarkup()
        if page > 1:
            previous_button = types.InlineKeyboardButton("Anterior", callback_data=f"prev_{categoria}_{page}")
            markup.add(previous_button)
        if len(resultados) == page_size:
            next_button = types.InlineKeyboardButton("Próxima", callback_data=f"next_{categoria}_{page}")
            markup.add(next_button)

        bot.send_message(chat_id, mensagem, reply_markup=markup)
    else:
        bot.send_message(chat_id, f"Nenhum resultado encontrado para a categoria '{categoria}'.")


# Função para tratar os callbacks de paginação
def callback_paginacao_categoria(call):
    chat_id = call.message.chat.id
    data = call.data.split('_')
    acao = data[0]
    categoria = data[1]

    if len(data) == 3:
        page = int(data[2])
    else:
        page = None

    # Verifique se a categoria é válida
    total_pages = obter_total_de_paginas(categoria)
    if total_pages is not None:
        if acao == "prev":
            page = page - 1 if page > 1 else 1
        elif acao == "next":
            # Verifique se a página não é maior do que o total de páginas
            page = page + 1 if page < total_pages else total_pages

        if page is not None:
            pesquisar_categoria_paginada(categoria, page, chat_id)
    else:
        bot.send_message(chat_id, f"A categoria '{categoria}' não contém cartas ou não é válida.")

def obter_total_de_paginas(categoria):
    # Consulte o banco de dados para contar quantas cartas existem na categoria especificada.
    sql = "SELECT COUNT(*) FROM personagens WHERE categoria = %s"
    values = (categoria,)

    cursor.execute(sql, values)
    total_cartas = cursor.fetchone()

    if total_cartas:
        total_cartas = total_cartas[0]
        # Defina o tamanho da página (quantidade de resultados por página).
        resultados_por_pagina = 15

        # Calcule o número total de páginas.
        total_pages = (total_cartas + resultados_por_pagina - 1) // resultados_por_pagina

        return total_pages

    return 1  # Se não houver cartas, o número total de páginas é 1


import threading

# Dicionário para armazenar respostas
respostas = {}

# Lock para garantir exclusão mútua ao acessar recursos compartilhados
lock = threading.Lock()


respostas = {}
cancelando = {}


def adicionar_personagens_em_massa(message):
    chat_id = message.chat.id
    cancelar_comando(chat_id)  # Cancela a ação anterior, se houver

    respostas.clear()  # Limpa as respostas anteriores
    cancelando[chat_id] = "adcmassa"  # Define a ação atual

    respostas["chat_id"] = chat_id  # Adiciona o chat_id às respostas

    bot.send_message(chat_id, "Vamos adicionar personagens em massa. Responda às seguintes perguntas:")
    bot.send_message(chat_id, "Qual é o ID inicial?")
    bot.register_next_step_handler(message, verificar_e_obter_id_inicial)  # Update this line to use the correct function

def verificar_e_obter_id_inicial(message):
    chat_id = message.chat.id
    id_inicial = message.text.strip()

    # Consultar o banco de dados para verificar a existência do ID inicial
    sql = "SELECT * FROM personagens WHERE id_personagem = %s"
    values = (id_inicial,)

    cursor.execute(sql, values)
    resultado = cursor.fetchone()

    print("Resultado:", resultado)  # Add this line for debugging

    if resultado:
        # ID inicial já existe, exiba as informações da carta existente
        id, nome, subcategoria, categoria = resultado[:4]
        mensagem = f"Já existe uma carta com o ID {id}.\nNome: {nome}\nSubcategoria: {subcategoria}\nCategoria: {categoria}"
        bot.send_message(chat_id, mensagem)
    else:
        # ID inicial não existe, continue com a adição dos personagens em massa
        respostas["id_inicial"] = id_inicial
        respostas["id_atual"] = id_inicial
        bot.send_message(chat_id, "Agora, digite os nomes dos personagens separados por vírgula (,).")
        bot.register_next_step_handler(message, obter_nomes_personagens)

def obter_nomes_personagens(message):
    chat_id = message.chat.id
    nomes = message.text.split(',')  # Divida os nomes separados por vírgula em uma lista
    id_atual = int(respostas["id_atual"])  # Obtém o ID atual

    # Criar personagens com IDs incrementais
    personagens = []

    for nome in nomes:
        personagem = {
            "id_personagem": id_atual,
            "nome": nome.strip(),
            "subcategoria": "",
            "categoria": ""
        }
        personagens.append(personagem)
        id_atual += 1  # Incrementa o ID atual

    respostas["personagens"] = personagens
    respostas["id_atual"] = id_atual  # Atualiza o ID atual

    # Solicitar a subcategoria
    bot.send_message(chat_id, "Agora, digite a subcategoria para todos os personagens.")
    bot.register_next_step_handler(message, obter_subcategoria_em_massa)

def obter_subcategoria_em_massa(message):
    chat_id = message.chat.id
    subcategoria = message.text.strip()
    personagens = respostas["personagens"]

    # Definir a subcategoria para todos os personagens
    for personagem in personagens:
        personagem["subcategoria"] = subcategoria

    # Solicitar a categoria
    bot.send_message(chat_id, "Agora, digite a categoria para todos os personagens.")
    bot.register_next_step_handler(message, obter_categoria_em_massa)

def obter_categoria_em_massa(message):
    chat_id = message.chat.id
    categoria = message.text.strip()
    personagens = respostas["personagens"]

    # Definir a categoria para todos os personagens
    for personagem in personagens:
        personagem["categoria"] = categoria

    # Confirmar as informações
    mensagem_confirmacao = "Confira as informações dos personagens:\n"
    for personagem in personagens:
        mensagem_confirmacao += f"ID: {personagem['id_personagem']}, Nome: {personagem['nome']}, " \
                                f"Subcategoria: {personagem['subcategoria']}, " \
                                f"Categoria: {personagem['categoria']}\n"
    mensagem_confirmacao += "As informações estão corretas? (Sim/Não)"
    bot.send_message(chat_id, mensagem_confirmacao)
    bot.register_next_step_handler(message, confirmar_informacoes_em_massa)

def confirmar_informacoes_em_massa(message):
    chat_id = message.chat.id
    resposta = message.text.strip().lower()

    if resposta == "sim":
        adicionar_personagens_em_massa_ao_banco()
        bot.send_message(chat_id, "Personagens adicionados ao banco de dados com sucesso!")
    elif resposta == "não" or resposta == "nao":
        bot.send_message(chat_id, "Operação cancelada.")
    else:
        bot.send_message(chat_id, "Resposta inválida. Por favor, responda com 'Sim' ou 'Não'.")

def adicionar_personagens_em_massa_ao_banco():
    chat_id = respostas["chat_id"]
    personagens = respostas["personagens"]

    try:
        conn, cursor = conectar_banco_dados()

        for personagem in personagens:
            # Inserir o personagem no banco de dados
            sql = "INSERT INTO personagens (id_personagem, nome, subcategoria, categoria) " \
                  "VALUES (%s, %s, %s, %s)"
            values = (
                personagem.get("id_personagem", None),
                personagem.get("nome", None),
                personagem.get("subcategoria", None),
                personagem.get("categoria", None)
            )

            cursor.execute(sql, values)

        conn.commit()
        bot.send_message(chat_id, "Personagens adicionados ao banco de dados com sucesso!")

    except mysql.connector.Error as err:
        bot.send_message(chat_id, f"Erro ao adicionar personagens ao banco de dados: {err}")

    finally:
        # Feche a conexão com o banco de dados
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

# Manipulador para o comando /adcmassa
@bot.message_handler(commands=['adcmassa'])
def iniciar_adicao_em_massa(message):
    adicionar_personagens_em_massa(message)

@bot.message_handler(commands=['eaddimagem'])
def adicionar_link_imagem(message):
    chat_id = message.chat.id

    try:
        # Extrair ID e link da mensagem
        command_parts = message.text.split()
        id_personagem = int(command_parts[1])
        link_imagem = command_parts[2]

        # Consultar o banco de dados para obter informações sobre o personagem
        sql_info = "SELECT nome, imagem FROM evento WHERE id_personagem = %s"
        cursor.execute(sql_info, (id_personagem,))
        info_personagem = cursor.fetchone()

        if info_personagem:
            nome_personagem, imagem_personagem = info_personagem

            # Atualizar o link da imagem no banco de dados
            sql_update = "UPDATE evento SET imagem = %s WHERE id_personagem = %s"
            cursor.execute(sql_update, (link_imagem, id_personagem))
            conn.commit()

            # Consultar novamente o banco de dados para obter as informações atualizadas
            cursor.execute(sql_info, (id_personagem,))
            info_personagem_atualizado = cursor.fetchone()

            if info_personagem_atualizado:
                nome_personagem, imagem_personagem = info_personagem_atualizado

                # Enviar a foto do personagem
                if imagem_personagem:
                    bot.send_photo(chat_id, imagem_personagem,
                                   caption=f"Link da imagem adicionado com sucesso para {nome_personagem} (ID {id_personagem}).")
                else:
                    bot.send_message(chat_id,
                                     f"Link da imagem adicionado com sucesso para {nome_personagem} (ID {id_personagem}).")
            else:
                bot.send_message(chat_id, f"Não foi possível recuperar as informações atualizadas do personagem.")
        else:
            bot.send_message(chat_id, f"Personagem com ID {id_personagem} não encontrado.")

    except (ValueError, IndexError) as e:
        traceback.print_exc()
        bot.send_message(chat_id, f"Formato inválido. Use /addimagem ID link_imagem. Tente novamente.")
    except Exception as e:
        traceback.print_exc()
        bot.send_message(chat_id, f"Ocorreu um erro ao processar a solicitação. Tente novamente.")

# Função para adicionar o link da imagem para um ID específico
@bot.message_handler(commands=['addimagem'])
def adicionar_link_imagem(message):
    chat_id = message.chat.id

    try:
        # Extrair ID e link da mensagem
        command_parts = message.text.split()
        id_personagem = int(command_parts[1])
        link_imagem = command_parts[2]
        print("ID do personagem:", id_personagem)
        print("Link da imagem:", link_imagem)
        
        # Consultar o banco de dados para obter informações sobre o personagem
        sql_info = "SELECT nome, imagem FROM personagens WHERE id_personagem = %s"
        cursor.execute(sql_info, (id_personagem,))
        info_personagem = cursor.fetchone()

        if info_personagem:
            nome_personagem, imagem_personagem = info_personagem

            # Atualize o link da imagem no banco de dados
            sql_update = "UPDATE personagens SET imagem = %s WHERE id_personagem = %s"
            cursor.execute(sql_update, (link_imagem, id_personagem))
            conn.commit()

            # Consultar novamente o banco de dados para obter as informações atualizadas
            cursor.execute(sql_info, (id_personagem,))
            info_personagem_atualizado = cursor.fetchone()

            if info_personagem_atualizado:
                nome_personagem, imagem_personagem = info_personagem_atualizado

                # Enviar a foto do personagem
                if imagem_personagem:
                    bot.send_photo(chat_id, imagem_personagem,
                                   caption=f"Link da imagem adicionado com sucesso para {nome_personagem} (ID {id_personagem}).")
                        # Enviar notificação ao grupo de log
                    mensagem_log = f"Usuário {message.from_user.first_name} (ID {message.from_user.id}) atualizou a imagem do personagem ID {id_personagem} para: {link_imagem}"
                    bot.send_message(-1002216029435, mensagem_log)  # Substitua -1002216029435 pelo ID real do seu grupo de log

                else:
                    bot.send_message(chat_id,
                                     f"Link da imagem adicionado com sucesso para {nome_personagem} (ID {id_personagem}).")
                    # Enviar notificação ao grupo de log
                    mensagem_log = f"Usuário {message.from_user.first_name} (ID {message.from_user.id}) atualizou a imagem do personagem ID {id_personagem} para: {link_imagem}"
                    bot.send_message(-1002216029435, mensagem_log)  # Substitua -1002216029435 pelo ID real do seu grupo de log

            else:
                bot.send_message(chat_id, f"Não foi possível recuperar as informações atualizadas do personagem.")
        else:
            bot.send_message(chat_id, f"Personagem com ID {id_personagem} não encontrado.")

    except (ValueError, IndexError) as e:
        traceback.print_exc()
        bot.send_message(chat_id, f"Formato inválido. Use /addimagem ID link_imagem. Tente novamente.")
    except Exception as e:
        traceback.print_exc()
        bot.send_message(chat_id, f"Ocorreu um erro ao processar a solicitação. Tente novamente.")

def confirmar_informacoes_em_massa(message):
    chat_id = message.chat.id
    resposta = message.text.strip().lower()

    if resposta == "sim":
        # Inserir informações no banco de dados
        inserir_informacoes_em_massa()
        bot.send_message(chat_id, "As informações foram adicionadas no banco de dados.")
    else:
        bot.send_message(chat_id, "As informações não foram adicionadas no banco de dados.")


def inserir_informacoes_em_massa():
    personagens = respostas.get("personagens", [])  # Use get method with a default empty list if 'personagens' is not present

    sql = "INSERT INTO personagens (id_personagem, nome, subcategoria, categoria, submenu) VALUES (%s, %s, %s, %s, %s)"

    # Crie uma lista de tuplas contendo os valores para inserção em massa
    values = [
        (
            personagem.get("id_personagem", None),
            personagem.get("nome", None),
            personagem.get("subcategoria", None),
            personagem.get("categoria", None),
            personagem.get("submenu", None)
        )
        for personagem in personagens
    ]

    cursor.executemany(sql, values)
    conn.commit()


# Função para cancelar a ação em andamento
def cancelar_comando(chat_id):
    if chat_id in cancelando:
        del cancelando[chat_id]

@bot.message_handler(commands=['extrair_ids'])
def extrair_ids(message):
    try:
        # Verificar se a mensagem é uma resposta
        if not message.reply_to_message:
            bot.reply_to(message, "Por favor, responda a uma mensagem que contenha os IDs que você deseja extrair.")
            return

        # Extrair IDs da mensagem original, incluindo IDs dentro de <code> </code>
        texto_original = message.reply_to_message.text

        # Usar BeautifulSoup para extrair IDs dentro de tags <code>
        soup = BeautifulSoup(texto_original, 'html.parser')
        ids_code = [tag.text for tag in soup.find_all('code')]

        # Usar regex para extrair IDs fora de tags <code>
        ids_text = re.findall(r'\b\d{1,5}\b', texto_original)

        # Combinar IDs, removendo duplicatas
        ids = list(set(ids_code + ids_text))

        if not ids:
            bot.reply_to(message, "Nenhum ID válido encontrado na mensagem.")
            return

        # Ordenar os IDs e convertê-los em string
        ids = sorted(map(int, ids))
        ids_str = ', '.join(map(str, ids))

        # Enviar a lista de IDs como resposta
        bot.send_message(message.chat.id, f"IDs extraídos: {ids_str}", reply_to_message_id=message.message_id)

    except Exception as e:
        print(f"Erro ao extrair IDs: {e}")
        bot.reply_to(message, "Ocorreu um erro ao extrair os IDs.")
# Função para iniciar a adição de um personagem
@bot.message_handler(commands=['adc'])
def adicionar_personagem(message):
    chat_id = message.chat.id
    cancelar_comando(chat_id)  # Cancela a ação anterior, se houver

    respostas.clear()  # Limpa as respostas anteriores
    cancelando[chat_id] = "adc"  # Define a ação atual

    # Inicia o processo de coleta de informações
    bot.send_message(chat_id, "Vamos adicionar um novo personagem. Responda às seguintes perguntas:")
    bot.send_message(chat_id, "Qual é o ID?")
    bot.register_next_step_handler(message, verificar_e_obter_id)

# Função para verificar e obter o ID inicial
def verificar_e_obter_id(message):
    chat_id = message.chat.id
    id_inicial = message.text

    try:
        id_inicial = int(id_inicial)
        respostas["id_inicial"] = id_inicial

        # Verificar se o ID inicial já existe no banco de dados
        sql = "SELECT * FROM personagens WHERE id_personagem = %s"
        values = (id_inicial,)

        cursor.execute(sql, values)
        resultado = cursor.fetchone()

        if resultado:
            # ID já existe, exiba as informações da carta existente
            id, nome, subcategoria, categoria, submenu = resultado[:5]
            mensagem = f"Já existe uma carta com o ID {id}.\nNome: {nome}\nSubcategoria: {subcategoria}\nCategoria: {categoria}\nSubmenu: {submenu}"
            bot.send_message(chat_id, mensagem)
        else:
            # ID inicial não existe, continue com a adição dos personagens em massa
            respostas["id_atual"] = id_inicial
            bot.send_message(chat_id, "Agora, digite os nomes dos personagens separados por vírgula (,).")
            bot.register_next_step_handler(message, obter_nomes_personagens)
    except ValueError:
        bot.send_message(chat_id, "ID inicial inválido. Tente novamente.")


def obter_nome(message):
    chat_id = message.chat.id
    respostas["nome"] = message.text

    bot.send_message(chat_id, "Qual é a subcategoria?")
    bot.register_next_step_handler(message, obter_subcategoria)


def obter_subcategoria(message):
    chat_id = message.chat.id
    respostas["subcategoria"] = message.text

    bot.send_message(chat_id, "Qual é a categoria?")
    bot.register_next_step_handler(message, obter_categoria)


def obter_categoria(message):
    chat_id = message.chat.id
    respostas["categoria"] = message.text

    bot.send_message(chat_id, "Qual é a categoria?")
    bot.register_next_step_handler(message, obter_submenu)


def obter_submenu(message):
    chat_id = message.chat.id
    # Confirmação das informações
    mensagem_confirmacao = "Confira as informações:\n"
    for chave, valor in respostas.items():
        mensagem_confirmacao += f"{chave}: {valor}\n"
    mensagem_confirmacao += "As informações estão corretas? (Sim/Não)"
    bot.send_message(chat_id, mensagem_confirmacao)
    bot.register_next_step_handler(message, confirmar_informacoes)


def confirmar_informacoes(message):
    chat_id = message.chat.id
    resposta = message.text.strip().lower()

    if resposta == "sim":
        # Inserir informações no banco de dados
        inserir_informacoes_no_banco()
        bot.send_message(chat_id, "As informações foram adicionadas no banco de dados.")
    else:
        bot.send_message(chat_id, "As informações não foram adicionadas no banco de dados.")


def inserir_informacoes_no_banco():
    sql = "INSERT INTO personagens (id_personagem, nome, subcategoria, categoria, submenu) VALUES (%s, %s, %s, %s, %s)"
    values = (
    respostas["id_personagem"], respostas["nome"], respostas["subcategoria"], respostas["categoria"], respostas["submenu"])
    cursor.execute(sql, values)
    conn.commit()


# Função genérica para pesquisar cartas no banco de dados
def pesquisar_cartas_por_campo(campo, valor, mensagem_resultado, chat_id):
    sql = f"SELECT id_personagem, nome, subcategoria, categoria, submenu FROM personagens WHERE {campo} = %s"
    value = (valor,)

    cursor.execute(sql, value)
    resultados = cursor.fetchall()

    if resultados:
        mensagem = mensagem_resultado
        for resultado in resultados:
            id, nome, subcategoria, categoria, submenu = resultado
            mensagem += f"ID: {id}, Nome: {nome}, Subcategoria: {subcategoria}, Categoria: {categoria}, Submenu: {submenu}\n"
        bot.send_message(chat_id, mensagem)
    else:
        bot.send_message(chat_id, f"Nenhum resultado encontrado para o {campo} '{valor}'.")# Atualize a função para listar todas as cartas paginadas
# Atualize a função para listar todas as cartas paginadas
# Inicialmente, armazene a mensagem da primeira página em uma variável global
primeira_mensagem = None

# Função para listar todas as cartas paginadas
def listar_todas_cartas_paginado(message, page=None):
    global primeira_mensagem

    chat_id = message.chat.id
    page_size = 15  # Quantidade de resultados por página
    if page is None:
        page = 1
    start_index = (page - 1) * page_size

    sql = "SELECT id_personagem, nome, subcategoria, categoria, submenu FROM personagens LIMIT %s, %s"
    values = (start_index, page_size)

    cursor.execute(sql, values)
    resultados = cursor.fetchall()

    mensagem = f"Listagem de cartas (Página {page}):\n"
    for resultado in resultados:
        id, nome, subcategoria, categoria, submenu = resultado
        mensagem += f"ID: {id}, Nome: {nome}, Subcategoria: {subcategoria}, Categoria: {categoria}, Submenu: {submenu}\n"

    markup = types.InlineKeyboardMarkup()
    if page > 1:
        previous_button = types.InlineKeyboardButton("⬅️", callback_data=f"prev_listar_todas_{page}")
        markup.add(previous_button)
    if len(resultados) == page_size:
        next_button = types.InlineKeyboardButton("➡️", callback_data=f"next_listar_todas_{page}")
        markup.add(next_button)

    if primeira_mensagem is None:
        # Se é a primeira página, envie a mensagem e armazene-a
        primeira_mensagem = bot.send_message(chat_id, mensagem, reply_markup=markup)
    else:
        # Caso contrário, edite a mensagem original
        bot.edit_message_text(chat_id=chat_id, message_id=primeira_mensagem.message_id, text=mensagem, reply_markup=markup)




@bot.callback_query_handler(
    func=lambda call: call.data.startswith('prev_listar_todas_') or call.data.startswith('next_listar_todas_'))
def callback_paginacao_lista(call):
    chat_id = call.message.chat.id
    page = int(call.data.split('_')[-1])

    if call.data.startswith('prev_listar_todas_'):
        page -= 1
    elif call.data.startswith('next_listar_todas_'):
        page += 1

    listar_todas_cartas_paginado(call.message, page)



# Função para tratar os callbacks de paginação
@bot.callback_query_handler(func=lambda call: call.data.startswith(("prev_listar_todas_", "next_listar_todas_")))
def callback_paginacao_listar_todas_cartas(call):
    chat_id = call.message.chat.id
    data = call.data.split('_')
    acao = data[0]

    if len(data) == 3:
        page = data[2]
    else:
        page = 1  # Define um valor padrão se o número da página não estiver presente.

    try:
        page = int(page)  # Tenta converter a página em um número inteiro.
    except ValueError:
        page = 1  # Em caso de erro, define o valor padrão como 1.

    if acao == "prev":
        page = page - 1 if page > 1 else 1
    elif acao == "next":
        # Verifica se a página não é maior do que o total de páginas
        total_pages = obter_total_de_paginas("todas")  # Use "todas" como categoria para listar todas as cartas.
        page = page + 1 if page < total_pages else total_pages

    listar_todas_cartas_paginado(call.message, str(page))



# Função para listar todas as cartas
@bot.message_handler(commands=['all'])
def listar_todas_cartas(message):
    listar_todas_cartas_paginado(message)


# Define the command handler with a parameter
@bot.message_handler(commands=['id'])
def obter_id_e_enviar_info_com_imagem(message):
    chat_id = message.chat.id

    # Extract the ID from the command
    command_parts = message.text.split()
    if len(command_parts) == 2 and command_parts[1].isdigit():
        id_pesquisa = command_parts[1]

        # Consultar o banco de dados para obter as informações e o link da imagem
        sql = "SELECT id_personagem, nome, subcategoria, categoria, submenu, imagem FROM personagens WHERE id_personagem = %s"
        values = (id_pesquisa,)

        cursor.execute(sql, values)
        resultado = cursor.fetchone()

        if resultado:
            id, nome, subcategoria, categoria, submenu, imagem_url = resultado

            # Enviar informações textuais
            mensagem = f"Resultado da pesquisa:\nID: {id}\nNome: {nome}\nSubcategoria: {subcategoria}\nCategoria: {categoria}\nSubmenu: {submenu}"

            # Enviar imagem
            try:
                # Certifique-se de que a URL da imagem é válida
                bot.send_photo(chat_id, imagem_url, caption=mensagem)
            except Exception as e:
                # Em caso de erro no envio da imagem, envie apenas as informações textuais
                bot.send_message(chat_id, mensagem)
        else:
            bot.send_message(chat_id, f"Nenhum resultado encontrado para o ID '{id_pesquisa}'.")
    else:
        bot.send_message(chat_id, "Formato incorreto. Use /id seguido do ID desejado, por exemplo: /id 123")
@bot.message_handler(commands=['idevento'])
def obter_id_e_enviar_info_com_imagem(message):
    chat_id = message.chat.id

    # Extrair o ID do comando
    command_parts = message.text.split()
    if len(command_parts) == 2 and command_parts[1].isdigit():
        id_pesquisa = command_parts[1]

        # Conectar ao banco de dados
        conn, cursor = conectar_banco_dados()
        try:
            # Consultar o banco de dados para obter as informações e o link da imagem
            sql = "SELECT id_personagem, nome, subcategoria, categoria, evento, imagem FROM evento WHERE id_personagem = %s"
            values = (id_pesquisa,)

            cursor.execute(sql, values)
            resultado = cursor.fetchone()

            if resultado:
                id, nome, subcategoria, categoria, evento, imagem_url = resultado

                # Enviar informações textuais
                mensagem = f"Resultado da pesquisa:\nID: {id}\nNome: {nome}\nSubcategoria: {subcategoria}\nCategoria: {categoria}\nEvento: {evento}"

                # Enviar imagem
                try:
                    # Certificar-se de que a URL da imagem é válida
                    bot.send_photo(chat_id, imagem_url, caption=mensagem)
                except Exception as e:
                    # Em caso de erro no envio da imagem, envie apenas as informações textuais
                    bot.send_message(chat_id, mensagem)
            else:
                bot.send_message(chat_id, f"Nenhum resultado encontrado para o ID '{id_pesquisa}'.")
        except Exception as e:
            bot.send_message(chat_id, f"Erro ao buscar informações: {e}")
        finally:
            fechar_conexao(cursor, conn)
    else:
        bot.send_message(chat_id, "Formato incorreto. Use /id seguido do ID desejado, por exemplo: /id 123")

@bot.message_handler(commands=['allid'])
def listar_personagens_por_subcategoria(message):
    chat_id = message.chat.id

    # Obter a subcategoria da mensagem
    command_parts = message.text.split(maxsplit=1)
    print(command_parts)
    if len(command_parts) >= 2:
        print(command_parts)
        subcategoria = command_parts[1].strip()
        print(subcategoria)

        # Consultar o banco de dados para obter os personagens da subcategoria (usando LIKE)
        sql = "SELECT id_personagem, nome, subcategoria FROM personagens WHERE subcategoria LIKE %s"
        cursor.execute(sql, (f"%{subcategoria}%",))
        personagens = cursor.fetchall()

        if personagens:
            # Criar a lista de personagens (id - nome - subcategoria)
            lista_personagens = [f"{id_personagem} - {nome} - {subcategoria}" for id_personagem, nome, subcategoria in
                                 personagens]

            # Dividir a lista em partes para enviar em mensagens separadas
            chunk_size = 40  # Quantidade de personagens por mensagem
            for i in range(0, len(lista_personagens), chunk_size):
                chunk = lista_personagens[i:i + chunk_size]
                mensagem = f"Lista de personagens correspondendo à subcategoria '{subcategoria}':\n\n" + "\n".join(chunk)
                bot.send_message(chat_id, mensagem)

        else:
            bot.send_message(chat_id, f"Nenhum personagem encontrado na subcategoria '{subcategoria}'.")
    else:
        bot.send_message(chat_id, "Formato incorreto. Use /allid seguido da subcategoria desejada.")

# Função para pesquisar cartas pelo submenu
@bot.message_handler(commands=['submenu'])
def pesquisar_submenu(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Digite o submenu que deseja pesquisar:")
    bot.register_next_step_handler(message, lambda msg: pesquisar_cartas_por_campo("submenu", msg.text,
                                                                                   "Resultados da pesquisa:\n",
                                                                                   chat_id))

# Função para pesquisar cartas pelo ID
@bot.message_handler(commands=['id'])
def pesquisar_id(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Digite o ID que deseja pesquisar:")
    bot.register_next_step_handler(message, lambda msg: pesquisar_cartas_por_campo("id_personagem", msg.text,
                                                                                   "Resultado da pesquisa:\n",
                                                                                   chat_id))

# Função genérica para pesquisar cartas no banco de dados
def pesquisar_cartas_por_campo(campo, valor, mensagem_resultado, chat_id):
    sql = f"SELECT id_personagem, nome, subcategoria, categoria, submenu FROM personagens WHERE {campo} = %s"
    value = (valor,)

    cursor.execute(sql, value)
    resultados = cursor.fetchall()

    if resultados:
        mensagem = mensagem_resultado
        for resultado in resultados:
            id, nome, subcategoria, categoria, submenu = resultado
            mensagem += f"ID: {id}, Nome: {nome}, Subcategoria: {subcategoria}, Categoria: {categoria}, Submenu: {submenu}\n"
        bot.send_message(chat_id, mensagem)
    else:
        bot.send_message(chat_id, f"Nenhum resultado encontrado para o {campo} '{valor}'.")

@bot.message_handler(commands=['categ'])
def pesquisar_cartas_por_categoria(message):
    chat_id = message.chat.id
    conn = mysql.connector.connect(**db())
    cursor = conn.cursor()

    # Extrair a categoria do comando
    command_parts = message.text.split()
    if len(command_parts) == 2:
        categoria_pesquisa = command_parts[1]

        # Usar a função de pesquisa_cartas_por_campo para realizar a consulta
        pesquisar_cartas_por_campo("categoria", categoria_pesquisa, "Resultados da pesquisa por Categoria:\n", chat_id)

    else:
        bot.send_message(chat_id, "Formato incorreto. Use /gcateg seguido da categoria desejada, por exemplo: /gcateg Acao")
# Função para pesquisar cartas por subcategoria
def pesquisar_cartas_por_subcategoria(subcategoria_pesquisa, chat_id):
    try:
        # Estabelecer conexão com o banco de dados
        conn = mysql.connector.connect(**db())
        cursor = conn.cursor()

        # Consulta SQL para pesquisar cartas por subcategoria
        sql_query = "SELECT id_personagem, emoji, nome, subcategoria FROM personagens WHERE subcategoria LIKE %s"
        cursor.execute(sql_query, (f"%{subcategoria_pesquisa}%",))

        # Obter os resultados da consulta
        results = cursor.fetchall()

        if results:
            response = f"Resultados da pesquisa por Subcategoria '{subcategoria_pesquisa}':\n"
            for result in results:
                id_personagem, emoji, nome, subcategoria = result
                response += f"{emoji} {id_personagem}: {nome} - {subcategoria}\n"
        else:
            response = f"Nenhuma carta encontrada na subcategoria '{subcategoria_pesquisa}'."

        # Enviar a resposta para o chat
        bot.send_message(chat_id, response)

    except Error as e:
        bot.send_message(chat_id, f"Erro ao pesquisar cartas por subcategoria: {e}")

    finally:
        # Fechar a conexão com o banco de dados
        if conn.is_connected():
            cursor.close()
            conn.close()

# Comando /subcateg para pesquisar cartas por subcategoria
@bot.message_handler(commands=['subcateg'])
def handle_subcategoria_command(message):
    chat_id = message.chat.id

    # Extrair a subcategoria do comando
    command_parts = message.text.split()
    if len(command_parts) > 1:
        subcategoria_pesquisa = ' '.join(command_parts[1:])  # Reunir todos os elementos após /subcateg em uma única string

        # Usar a função para pesquisar cartas por subcategoria
        pesquisar_cartas_por_subcategoria(subcategoria_pesquisa, chat_id)

    else:
        bot.send_message(chat_id, "Formato incorreto. Use /subcateg seguido da subcategoria desejada, por exemplo: /subcateg Animais Selvagens")
@bot.message_handler(commands=['nome'])
def obter_nome_e_enviar_info_com_imagem(message):
    chat_id = message.chat.id
    conn = mysql.connector.connect(**db())
    cursor = conn.cursor()

    # Extract the ID from the command
    command_parts = message.text.split()
    if len(command_parts) >= 2:
        nome = command_parts[1]

        sql = "SELECT id_personagem, nome, subcategoria, categoria, submenu, imagem FROM personagens WHERE nome LIKE %s"
        values = (nome + '%',)  # Adiciona '%' ao final para encontrar resultados que começam com o nome fornecido

        cursor.execute(sql, values)
        resultado = cursor.fetchone()
        print(resultado)
        if resultado:
            id, nome, subcategoria, categoria, submenu, imagem_url = resultado
            print(resultado)
            # Enviar informações textuais
            mensagem = f"Resultado da pesquisa:\nID: {id}\nNome: {nome}\nSubcategoria: {subcategoria}\nCategoria: {categoria}\nSubmenu: {submenu}"

            # Enviar imagem
            try:
                # Certifique-se de que a URL da imagem é válida
                bot.send_photo(chat_id, imagem_url, caption=mensagem)
            except Exception as e:
                # Em caso de erro no envio da imagem, envie apenas as informações textuais
                bot.send_message(chat_id, mensagem)
        else:
            bot.send_message(chat_id, f"Nenhum resultado encontrado para o nome '{nome}'.")
    else:
        bot.send_message(chat_id, "Formato incorreto. Use /nome seguido do ID desejado, por exemplo: /id 123")


@bot.message_handler(commands=['menu'])
def menu(message):    
    try:
        keyboard = telebot.types.InlineKeyboardMarkup()

        primeira_coluna = [
                    telebot.types.InlineKeyboardButton(text="Adição", callback_data='adicao'),
                    telebot.types.InlineKeyboardButton(text="Alteração", callback_data='pescar_animanga'),
                    telebot.types.InlineKeyboardButton(text="Correção", callback_data='pescar_jogos')
                ]
   
        keyboard.add(*primeira_coluna)
                
        photo = "https://telegra.ph/file/b3e6d2a41b68c2ceec8e5.jpg"
        bot.send_photo(message.chat.id, photo=photo, caption=f'Bem vindo ao menu do Mabi assistant. O que você deseja?0', reply_markup=keyboard, reply_to_message_id=message.message_id,parse_mode="HTML")
    except:
        print("erro")
@bot.callback_query_handler(func=lambda call: call.data.startswith('adicao'))       


@bot.message_handler(commands=['allnomes'])        
def obter_nome_e_enviar_info_com_imagem(message):
    chat_id = message.chat.id
    conn = mysql.connector.connect(**db())
    cursor = conn.cursor()

    # Extract the nome from the command
    command_parts = message.text.split()
    if len(command_parts) == 2:
        nome = command_parts[1]

        # Paginação
        pagina = 1  # Página inicial
        resultados_por_pagina = 10  # Número de resultados por página

        # Consultar o banco de dados para obter os resultados da página atual
        sql = "SELECT id_personagem, nome, subcategoria, categoria FROM personagens WHERE nome LIKE %s LIMIT %s OFFSET %s"
        values = (nome + '%', resultados_por_pagina, (pagina - 1) * resultados_por_pagina)

        cursor.execute(sql, values)
        resultados = cursor.fetchall()

        if resultados:
            # Criar a lista de personagens
            lista_personagens = [f"{id} - {nome} - {subcategoria} de {categoria}" for id, nome, subcategoria, categoria in resultados]

            # Enviar a lista como uma única mensagem
            mensagem = f"Lista de personagens com o nome '{nome}', Página {pagina}:\n\n"
            mensagem += "\n".join(lista_personagens)

            # Adicionar botões de paginação na mesma linha
            markup = telebot.types.InlineKeyboardMarkup()
            buttons_row = [
                telebot.types.InlineKeyboardButton("◀️", callback_data=f"anterior_{nome}_{pagina-1}"),
                telebot.types.InlineKeyboardButton("▶️", callback_data=f"proxima_{nome}_{pagina+1}")
            ]
            markup.row(*buttons_row)

            # Enviar mensagem completa com resultados, botões de paginação e remover teclado anterior
            bot.send_message(chat_id, mensagem, reply_markup=markup)

        else:
            bot.send_message(chat_id, f"Nenhum resultado encontrado para o nome '{nome}'.")
    else:
        bot.send_message(chat_id, "Formato incorreto. Use /allnomes seguido do nome desejado, por exemplo: /allnomes taylor")


@bot.callback_query_handler(func=lambda call: call.data.startswith(('anterior_', 'proxima_')))
def callback_paginacao_nome(call):
    chat_id = call.message.chat.id
    nome, pagina_str = call.data.split('_')[1:3]
    pagina = int(pagina_str)

    # Paginação
    resultados_por_pagina = 10

    # Consultar o banco de dados para obter os resultados da página atual
    sql = "SELECT id_personagem, nome, subcategoria, categoria FROM personagens WHERE nome LIKE %s LIMIT %s OFFSET %s"
    values = (nome + '%', resultados_por_pagina, (pagina - 1) * resultados_por_pagina)

    cursor.execute(sql, values)
    resultados = cursor.fetchall()

    if resultados:
        # Criar a lista de personagens
        lista_personagens = [f"{id} - {nome} - {subcategoria} de {categoria}" for id, nome, subcategoria, categoria in resultados]
        # Adicionar botões de paginação na mesma linha
        markup = telebot.types.InlineKeyboardMarkup()
        # Adicionar botões de paginação na mesma linha
        # Adicionar botões de paginação
        buttons_row = []
        if pagina > 1:
            buttons_row.append(
                telebot.types.InlineKeyboardButton("◀️", callback_data=f"anterior_{nome}_{pagina - 1}"))
        if len(resultados) == resultados_por_pagina:
            buttons_row.append(
                telebot.types.InlineKeyboardButton("▶️", callback_data=f"proxima_{nome}_{pagina + 1}"))
        else:
            buttons_row.append(telebot.types.InlineKeyboardButton("▶️", callback_data=f"proxima_{nome}_1"))

        markup.row(*buttons_row)
        # Criar a lista como uma única mensagem
        mensagem = f"Lista de personagens com o nome '{nome}', Página {pagina}:\n\n"
        mensagem += "\n".join(lista_personagens)

        # Editar a mensagem original com os novos resultados e botões de paginação
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=mensagem, reply_markup=markup)

    else:
        # Em caso de nenhum resultado encontrado, enviar mensagem informativa
        bot.answer_callback_query(callback_query_id=call.id, text=f"Nenhum resultado encontrado para o nome '{nome}'.")

@bot.message_handler(commands=['allsub'])
def obter_subcategorias_e_enviar_info_com_imagem(message):
    chat_id = message.chat.id
    conn = mysql.connector.connect(**db())
    cursor = conn.cursor()

    # Extract the categoria from the command
    command_parts = message.text.split()
    if len(command_parts) == 2:
        categoria = command_parts[1]

        # Paginação
        pagina = 1  # Página inicial
        resultados_por_pagina = 10  # Número de resultados por página

        # Consultar o banco de dados para obter os resultados da página atual
        sql = "SELECT DISTINCT subcategoria FROM personagens WHERE categoria = %s ORDER BY subcategoria ASC LIMIT %s OFFSET %s"
        values = (categoria, resultados_por_pagina, (pagina - 1) * resultados_por_pagina)

        cursor.execute(sql, values)
        resultados = cursor.fetchall()

        if resultados:
            # Criar a lista de subcategorias
            lista_subcategorias = [f"{subcategoria}" for subcategoria, in resultados]

            markup = telebot.types.InlineKeyboardMarkup()
            buttons_row = [
                telebot.types.InlineKeyboardButton("◀️ Anterior",
                                                   callback_data=f"categoria_{categoria}_anterior_{pagina - 1}"),
                telebot.types.InlineKeyboardButton("Próxima ▶️",
                                                   callback_data=f"categoria_{categoria}_proxima_{pagina + 1}")
            ]
            markup.row(*buttons_row)

            # Enviar a lista como uma única mensagem com botões de paginação
            mensagem = f"Lista de subcategorias para a categoria '{categoria}', Página {pagina}:\n\n"
            mensagem += "\n".join(lista_subcategorias)
            bot.send_message(chat_id, mensagem, reply_markup=markup)

        else:
            bot.send_message(chat_id, f"Nenhuma subcategoria encontrada para a categoria '{categoria}'.")
    else:
        bot.send_message(chat_id, "Formato incorreto. Use /allsub seguido do nome da categoria, por exemplo: /allsub comida")

@bot.callback_query_handler(func=lambda call: call.data.startswith(('categoria_', 'categoria_anterior_', 'categoria_proxima_')))
def callback_paginacao_sub(call):
    chat_id = call.message.chat.id
    _, categoria, _, pagina_str = call.data.split('_')
    pagina = int(pagina_str)

    # Paginação
    resultados_por_pagina = 10
    offset = (pagina - 1) * resultados_por_pagina

    # Consultar o banco de dados para obter os resultados da página atual
    sql = "SELECT DISTINCT subcategoria FROM personagens WHERE categoria = %s ORDER BY subcategoria ASC LIMIT %s OFFSET %s"
    values = (categoria, resultados_por_pagina, offset)

    cursor.execute(sql, values)
    resultados = cursor.fetchall()

    if resultados:
        # Criar a lista de subcategorias
        lista_subcategorias = [f"{subcategoria}" for subcategoria, in resultados]

        # Adicionar botões de paginação na mesma linha
        markup = telebot.types.InlineKeyboardMarkup()

        # Adicionar botões de paginação
        buttons_row = [
            telebot.types.InlineKeyboardButton("◀️ Anterior", callback_data=f"categoria_{categoria}_anterior_{pagina-1}"),
            telebot.types.InlineKeyboardButton("Próxima ▶️", callback_data=f"categoria_{categoria}_proxima_{pagina+1}")
        ]

        markup.row(*buttons_row)

        # Criar a lista como uma única mensagem
        mensagem = f"Lista de subcategorias para a categoria '{categoria}', Página {pagina}:\n\n"
        mensagem += "\n".join(lista_subcategorias)

        # Editar a mensagem original com os novos resultados e botões de paginação
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=mensagem, reply_markup=markup)

    else:
        # Em caso de nenhum resultado encontrado, enviar mensagem informativa
        bot.answer_callback_query(callback_query_id=call.id, text=f"Nenhuma subcategoria encontrada para a categoria '{categoria}'.")
def pesquisar_cartas_por_campo(campo, valor, mensagem_resultado, chat_id, limite=5, pagina=1):
    conn = None
    cursor = None

    try:
        conn = mysql.connector.connect(**db())
        cursor = conn.cursor()

        # Modificação 1: Usar LIKE para pesquisa aproximada
        sql = f"SELECT id_personagem, nome, subcategoria, categoria, submenu FROM personagens WHERE {campo} LIKE %s LIMIT %s OFFSET %s"
        value = (f"%{valor}%", limite, (pagina - 1) * limite)

        cursor.execute(sql, value)
        resultados = cursor.fetchall()

        if resultados:
            mensagem = mensagem_resultado
            for resultado in resultados:
                id_personagem, nome, subcategoria, categoria, submenu = resultado
                mensagem += f"ID: {id_personagem}, Nome: {nome}, Subcategoria: {subcategoria}, Categoria: {categoria}, Submenu: {submenu}\n"
            bot.send_message(chat_id, mensagem)
        else:
            bot.send_message(chat_id, f"Nenhum resultado encontrado para o {campo} '{valor}' na página {pagina}.")
    except mysql.connector.Error as err:
        bot.send_message(chat_id, f"Erro ao executar a consulta: {err}")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

# Comando /tabelas para listar todas as tabelas do banco de dados
@bot.message_handler(commands=['tabelas'])
def handle_tabelas_command(message):
    try:
        # Conectar ao banco de dados
        conn = conectar_banco_dados()
        if not conn:
            bot.reply_to(message, 'Erro ao conectar ao banco de dados.')
            return

        # Obter o cursor
        cursor = conn.cursor()

        # Consulta para listar todas as tabelas do banco de dados
        cursor.execute("SHOW TABLES")

        # Obter os resultados
        tables = cursor.fetchall()

        # Construir a resposta com os nomes das tabelas
        if tables:
            response = 'Tabelas disponíveis no banco de dados:\n'
            response += ', '.join(table[0] for table in tables)
        else:
            response = 'Nenhuma tabela encontrada no banco de dados.'

        # Enviar resposta ao usuário
        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f'Erro ao obter lista de tabelas: {e}')

    finally:
        # Fechar conexão com o banco de dados
        if conn and conn.is_connected():
            conn.close()
            print('Conexão com o banco de dados fechada.')

# Comando /colunas para listar as colunas de uma tabela específica
@bot.message_handler(commands=['colunas'])
def handle_colunas_command(message):
    try:
        # Extrair o nome da tabela da mensagem após o comando /colunas
        table_name = message.text.split('/colunas', 1)[1].strip()

        # Conectar ao banco de dados
        conn = conectar_banco_dados()
        if not conn:
            bot.reply_to(message, 'Erro ao conectar ao banco de dados.')
            return

        # Obter o cursor
        cursor = conn.cursor()

        # Consulta para obter as colunas da tabela especificada
        cursor.execute(f"SHOW COLUMNS FROM {table_name}")

        # Obter os resultados
        columns = cursor.fetchall()

        # Construir a resposta com os nomes das colunas
        if columns:
            response = f'Colunas da tabela {table_name}:\n'
            response += ', '.join(column[0] for column in columns)
        else:
            response = f'Nenhuma coluna encontrada para a tabela {table_name}.'

        # Enviar resposta ao usuário
        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f'Erro ao obter lista de colunas: {e}')

    finally:
        # Fechar conexão com o banco de dados
        if conn and conn.is_connected():
            conn.close()
            print('Conexão com o banco de dados fechada.')

                        
# Comando /sql para executar comandos SQL
@bot.message_handler(commands=['sql'])
def handle_sql_command(message):
    # Verificar se o usuário é autorizado a executar comandos SQL (implementar suas próprias regras de autorização)
    if message.chat.type == 'private':  # Permitir apenas em chats privados para segurança
        if message.from_user.id == 1112853187:
            try:
                # Extrair o comando SQL da mensagem (após o comando /sql)
                sql_command = message.text.split('/sql', 1)[1].strip()

                # Conectar ao banco de dados
                conn = conectar_banco_dados()
                if not conn:
                    bot.reply_to(message, 'Erro ao conectar ao banco de dados.')
                    return

                # Executar o comando SQL
                cursor = conn.cursor()
                cursor.execute(sql_command)

                # Obter resultados (se aplicável)
                if cursor.with_rows:
                    results = cursor.fetchall()
                    if results:
                        response = '\n'.join(str(row) for row in results)
                    else:
                        response = 'Nenhum resultado encontrado.'
                else:
                    response = 'Comando SQL executado com sucesso.'

                # Enviar resposta ao usuário
                bot.reply_to(message, response)

            except Exception as e:
                bot.reply_to(message, f'Erro ao executar comando SQL: {e}')

            finally:
                # Fechar conexão com o banco de dados
                if conn:
                    conn.close()
                    print('Conexão com o banco de dados fechada.')

        else:
            bot.reply_to(message, 'Você não tem permissão para executar comandos SQL.')
            
while True:          
    try:
        if __name__ == "__main__":
            bot.polling(none_stop=True, interval=1, timeout=20)
        else:
            bot.polling()
    except Exception as e:
        import traceback
        traceback.print_exc()
        time.sleep(5)      