#Bibliotecas para interagir com o Telegram e HTTP
import telebot
import requests
import flask
import http.server
import socketserver
from telebot.types import InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
#Conexão com o Banco de Dados
import mysql.connector
from mysql.connector import Error
#Manipulação de Data e Tempo
import time
import datetime
from datetime import datetime, timedelta, date
import datetime as dt_module
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import utc
#Manipulação de Imagens e Áudio
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter, UnidentifiedImageError
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
from io import BytesIO
import tempfile
#Análise e Manipulação de Strings e Web
import re
import Levenshtein
from bs4 import BeautifulSoup
from urllib.parse import urlparse
#Gerenciamento de Tarefas e Threads
import threading
from queue import Queue
#Manipulação de Arquivos e Sistema Operacional
import os
import json
import io
#Operações Matemáticas e Funções Utilitárias
import math
import random
import functools
#Cache e Armazenamento Temporário
import diskcache as dc
from cachetools import TTLCache
#Integração com APIs Externas (Spotify)
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
#Logs e Monitoramento
import logging
import newrelic.agent
#Módulos Personalizados do Projeto
from halloween import *
from doaçao import *
from wish import *
from songs import *
from credentials import *
from cestas import *
from album import *
from pescar import *
from evento import *
from phrases import *
from callbacks2 import choose_subcategoria_callback
from trocas import *
from bd import *
from saves import *
from calculos import *
from fonte import *
from trintadas import *
from eu import *
from sub import *
from submenu import *
from especies import *
from config import *
from historico import *
from tag import *
from banco import *
from diary import *
from admin import *
from peixes import *
from halloween import *
from vips import *
from petalas import *
from compat import *
from armazem import *
from diamantes import *
from game import *
# Configuração de Webhook
WEBHOOK_URL_PATH = '/' + API_TOKEN + '/'
WEBHOOK_LISTEN = "0.0.0.0"
WEBHOOK_PORT = int(os.getenv('PORT', 5000))
#Inicialização do Bot e Aplicações
bot = telebot.TeleBot(API_TOKEN)
app = flask.Flask(__name__)
newrelic.agent.initialize('newrelic.ini')
#Cache e Filas de Tarefas
cache_musicas_editadas = dc.Cache('./cache_musicas_editadas')
song_cooldown_cache = TTLCache(maxsize=1000, ttl=15)
cache = dc.Cache('./cache')
task_queue = Queue()
conn, cursor = conectar_banco_dados()

@app.route("/")
def set_webhook():

    bot.remove_webhook()
    success = bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH)
    
    if success:
        return "Webhook configurado com sucesso!", 200
    else:
        return "Falha ao configurar o webhook.", 500

@app.route('/', methods=['GET', 'HEAD'])
def index():
    return 'Server is running.'


@bot.message_handler(commands=['jogodavelha'])
def handle_jogo_da_velha(message):
    iniciar_jogo(bot, message)

@bot.callback_query_handler(func=lambda call: call.data.isdigit())
def handle_jogada(call):
    jogador_fazer_jogada(bot, call)

@bot.message_handler(commands=['picnic', 'trocar', 'troca'])
def trade(message):
    try:
        chat_id = message.chat.id
        eu = message.from_user.id
        voce = message.reply_to_message.from_user.id
        seunome = message.reply_to_message.from_user.first_name
        meunome = message.from_user.first_name
        bot_id = 7088149058
        categoria = message.text.replace('/troca', '')
        minhacarta = message.text.split()[1]
        suacarta = message.text.split()[2]
        
        # Verificação de bloqueios entre os usuários
        if verificar_bloqueio(eu, voce):
            bot.send_message(chat_id, "A troca não pode ser realizada porque um dos usuários bloqueou o outro.")
            return

        # Verificação se o destinatário é o bot
        if voce == bot_id:
            bot.send_message(chat_id, "Você não pode fazer trocas com a Mabi :(", reply_to_message_id=message.message_id)
            return

        # Verificação de inventário para o usuário que iniciou a troca
        if verifica_inventario_troca(eu, minhacarta) == 0:
            bot.send_message(chat_id, f"🌦️ ་  {meunome}, você não possui o peixe {minhacarta} para trocar.", reply_to_message_id=message.message_id)
            return

        # Verificação de inventário para o destinatário da troca
        if verifica_inventario_troca(voce, suacarta) == 0:
            bot.send_message(chat_id, f"🌦️ ་  Parece que {seunome} não possui o peixe {suacarta} para trocar.", reply_to_message_id=message.message_id)
            return

        # Obter informações das cartas
        info_minhacarta = obter_informacoes_carta(minhacarta)
        info_suacarta = obter_informacoes_carta(suacarta)
        emojiminhacarta, idminhacarta, nomeminhacarta, subcategoriaminhacarta = info_minhacarta
        emojisuacarta, idsuacarta, nomesuacarta, subcategoriasuacarta = info_suacarta

        meu_username = bot.get_chat_member(chat_id, eu).user.username
        seu_username = bot.get_chat_member(chat_id, voce).user.username

        seu_nome_formatado = f"@{seu_username}" if seu_username else seunome

        # Texto de descrição da troca
        texto = (
            f"🥪 | Hora do picnic!\n\n"
            f"{meunome} oferece de lanche:\n"
            f" {idminhacarta} {emojiminhacarta}  —  {nomeminhacarta} de {subcategoriaminhacarta}\n\n"
            f"E {seunome} oferece de lanche:\n"
            f" {idsuacarta} {emojisuacarta}  —  {nomesuacarta} de {subcategoriasuacarta}\n\n"
            f"Podemos começar a comer, {seu_nome_formatado}?"
        )

        # Criação dos botões de confirmação e rejeição
        keyboard = types.InlineKeyboardMarkup()
        primeiro = [
            types.InlineKeyboardButton(text="✅", callback_data=f'troca_sim_{eu}_{voce}_{minhacarta}_{suacarta}_{chat_id}'),
            types.InlineKeyboardButton(text="❌", callback_data=f'troca_nao_{eu}_{voce}_{minhacarta}_{suacarta}_{chat_id}'),
        ]
        keyboard.add(*primeiro)

        # Envio da imagem do picnic com a descrição da troca
        image_url = "https://telegra.ph/file/8672c8f91c8e77bcdad45.jpg"
        bot.send_photo(chat_id, image_url, caption=texto, reply_markup=keyboard, reply_to_message_id=message.reply_to_message.message_id)

    except Exception as e:
        traceback.print_exc()
        erro = traceback.format_exc()
        mensagem = f"Erro durante a troca. dados: {voce},{eu},{minhacarta},{suacarta}\n{erro}"
        bot.send_message(grupodeerro, mensagem, parse_mode="HTML")

@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)

# Registra o comando para iniciar o jogo Termo
@bot.message_handler(commands=['termo'])
def handle_termo(message):
    iniciar_termo(message)  # Chama a função iniciar_termo do arquivo halloween.py

@bot.message_handler(commands=['verificar'])
def verificar_ids(message):
    try:
        print("Comando verificar acionado")    
        if not message.reply_to_message:
            bot.reply_to(message, "Por favor, responda a uma mensagem que contenha os IDs que você deseja verificar.")
            return
        texto_original = message.reply_to_message.text
        soup = BeautifulSoup(texto_original, 'html.parser')
        ids_code = [tag.text for tag in soup.find_all('code')]

        ids_text = re.findall(r'\b\d{1,5}\b', texto_original)

        ids = list(set(ids_code + ids_text))

        if not ids:
            bot.reply_to(message, "Nenhum ID válido encontrado na mensagem.")
            return

        ids = list(map(int, ids))
        id_usuario = message.from_user.id

        conn, cursor = conectar_banco_dados()
        
        inventario = []

        for id_personagem in ids:
            cursor.execute("SELECT nome FROM personagens WHERE id_personagem = %s", (id_personagem,))
            resultado = cursor.fetchone()
            if resultado:
                nome_personagem = resultado[0]
                cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (id_usuario, id_personagem))
                quantidade = cursor.fetchone()
                if quantidade and quantidade[0] > 0:
                    inventario.append((id_personagem, nome_personagem, quantidade[0]))
            else:
                cursor.execute("SELECT nome FROM evento WHERE id_personagem = %s", (id_personagem,))
                resultado = cursor.fetchone()
                if resultado:
                    nome_personagem = resultado[0]
                    cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (id_usuario, id_personagem))
                    quantidade = cursor.fetchone()
                    if quantidade and quantidade[0] > 0:
                        inventario.append((id_personagem, nome_personagem, quantidade[0]))

        if not inventario:
            bot.send_message(message.chat.id, "Você não possui nenhuma das cartas mencionadas.", reply_to_message_id=message.message_id)
            return

        inventario.sort(key=lambda x: x[0])

        resposta = "🧺 Seu armazém:\n\n"
        for id_personagem, nome, quantidade in inventario:
            resposta += f"<code>{id_personagem}</code> — {nome}: {quantidade}x\n"

        max_chars = 4096  
        partes = [resposta[i:i + max_chars] for i in range(0, len(resposta), max_chars)]
        for parte in partes:
            bot.send_message(message.chat.id, parte, reply_to_message_id=message.message_id,parse_mode="HTML")

    except Exception as e:
        print(f"Erro ao verificar IDs: {e}")
        bot.reply_to(message, "Não foi possivel verificar essa mensagem, tente copiar e colar para verificar novamente.")
        
@bot.message_handler(commands=['labirinto'])
def handle_labirinto(message):
    iniciar_labirinto(message)

@bot.callback_query_handler(func=lambda call: call.data in ['norte', 'sul', 'leste', 'oeste'])
def handle_mover_labirinto(call):
    mover_labirinto(call)

@bot.callback_query_handler(func=lambda call: call.data in ['encerrar', 'continuar'])
def handle_encerrar_ou_continuar(call):
    encerrar_ou_continuar(call)

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
        print(f"DEBUG: Entrando no 'processar_pedido_peixes' com call data: {call.data}")
        image_url = "https://telegra.ph/file/94c9c66af4ca4d6f0a3e5.jpg"
        caption = ("<b>⛲: Para pedir os seus peixes é simples!</b> \n\nMe envie até <b>5 IDs</b> dos peixes e a quantidade de cenouras que você quer doar "
                   "\n(eu aceito qualquer quantidade entre 10 e 20 cenouras...) \n\n<i>exemplo: ID1 ID2 ID3 ID4 ID5 cenouras</i>")
        media = InputMediaPhoto(image_url, caption=caption, parse_mode="HTML")
        bot.edit_message_media(media, chat_id=call.message.chat.id, message_id=call.message.message_id)

        print("DEBUG: Registrando 'next_step_handler' para process_wish")
        bot.register_next_step_handler(call.message, process_wish)

    except Exception as e:
        print(f"Erro ao processar o pedido de peixes: {e}")
@bot.message_handler(commands=['sugestao'])
def sugestao_command(message):
    try:
        argumentos = message.text.split(maxsplit=1)
        if len(argumentos) < 2:
            bot.reply_to(message, "Por favor, envie sua sugestão no formato:\n"
                                  "/sugestao nome, subcategoria, categoria, imagem")
            return
        
        dados = argumentos[1].split(",")
        if len(dados) < 4:
            bot.reply_to(message, "Erro no formato. Envie como:\n"
                                  "/sugestao nome, subcategoria, categoria, imagem")
            return

        nome = dados[0].strip()
        subcategoria = dados[1].strip()
        categoria = dados[2].strip()
        imagem = dados[3].strip()

        nome_usuario = message.from_user.first_name
        user_usuario = message.from_user.username

        sugestao_texto = (f"Sugestão recebida:\n"
                          f"Nome: {nome}\nSubcategoria: {subcategoria}\nCategoria: {categoria}\n"
                          f"Imagem: {imagem}\n"
                          f"Usuário: {nome_usuario} (@{user_usuario})")

        bot.send_message(GRUPO_SUGESTOES, sugestao_texto)

    except Exception as e:
        print(f"Erro ao processar o comando /sugestao: {e}")
        bot.reply_to(message, "Ocorreu um erro ao processar sua sugestão. Tente novamente.")

@bot.message_handler(commands=['adicionar_vip'])
def handle_adicionar_vip(message):
    adicionar_vip_logic(message)

@bot.message_handler(commands=['remover_vip'])
def handle_remover_vip(message):
    remover_vip_logic(message)

@bot.message_handler(commands=['vips'])
def handle_listar_vips(message):
    listar_vips_logic(message)

@bot.message_handler(commands=['pedidos'])
def handle_listar_pedidos_vips(message):
    listar_pedidos_vips_logic(message)

@bot.message_handler(commands=['ficha'])
def handle_ver_ficha_vip(message):
    ver_ficha_vip_logic(message)

@bot.message_handler(commands=['doar'])
def handle_doar(message):
    doar(message)

@bot.message_handler(commands=['roseira'])
def handle_roseira_command(message):
    roseira_command(message)

@bot.message_handler(commands=['pedidosubmenu'])
def handle_pedido_submenu_command(message):
    pedido_submenu_command(message)

@bot.message_handler(commands=['pedidovip'])
def handle_pedidovip_command(message):
    pedidovip_command(message)
allowed_user_ids = [5532809878, 1805086442]
@bot.message_handler(commands=['criarvendinha'])
def criar_colagem(message):
    if message.from_user.id not in allowed_user_ids:
        bot.send_message(message.chat.id, "Você não tem permissão para usar este comando.")
        return

    try:
        cartas_aleatorias = obter_cartas_aleatorias()
        data_atual_str = dt_module.date.today().strftime("%Y-%m-%d") 
        if not cartas_aleatorias:
            bot.send_message(message.chat.id, "Não foi possível obter cartas aleatórias.")
            return

        registrar_cartas_loja(cartas_aleatorias, data_atual_str)
        imagens = []
        for carta in cartas_aleatorias:
            img_url = carta.get('imagem', '')
            try:
                if img_url:
                    response = requests.get(img_url)
                    if response.status_code == 200:
                        img = Image.open(io.BytesIO(response.content))
                        img = img.resize((300, 400), Image.LANCZOS)
                    else:
                        img = Image.new('RGB', (300, 400), color='black')
                else:
                    img = Image.new('RGB', (300, 400), color='black')
            except Exception as e:
                print(f"Erro ao abrir a imagem da carta {carta['id']}: {e}")
                img = Image.new('RGB', (300, 400), color='black')
            imagens.append(img)

        altura_total = (len(imagens) // 3) * 400

        colagem = Image.new('RGB', (900, altura_total))  
        coluna_atual = 0
        linha_atual = 0

        for img in imagens:
            colagem.paste(img, (coluna_atual, linha_atual))
            coluna_atual += 300

            if coluna_atual >= 900:
                coluna_atual = 0
                linha_atual += 400

        colagem.save('colagem_cartas.png')
        
        mensagem_loja = "🐟 Peixes na vendinha hoje:\n\n"
        for carta in cartas_aleatorias:
            mensagem_loja += f"{carta['emoji']}| {carta['id']} • {carta['nome']} - {carta['subcategoria']}\n"
        mensagem_loja += "\n🥕 Acesse usando o comando /vendinha"

        with open('colagem_cartas.png', 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=mensagem_loja, reply_to_message_id=message.message_id)
    except Exception as e:
        print(f"Erro ao criar colagem: {e}")
        bot.send_message(message.chat.id, "Erro ao criar colagem.")


@bot.message_handler(commands=['vendinha'])
def handle_vendinha_command(message):
    loja(message)

@bot.message_handler(commands=['peixes'])
def handle_peixes_command(message):
    verificar_comando_peixes(message)

@bot.message_handler(commands=['delgif'])
def handle_delgif(message):
    processar_comando_delgif(message)
            
@bot.message_handler(commands=['raspadinha'])
def handle_sorte(message):
    comando_sorte(message)

@bot.message_handler(commands=['casar'])
def handle_casar_command(message):
    casar_command(message)

@bot.message_handler(commands=['divorciar'])
def handle_divorciar_command(message):
    divorciar_command(message)

@bot.message_handler(commands=['tag'])
def handle_tag_command(message):
    verificar_comando_tag(message)

@bot.message_handler(commands=['addtag'])
def handle_addtag_command(message):
    adicionar_tag(message)

@bot.message_handler(commands=['completos'])
def handle_completos_command(message):
    handle_completos(message)

@bot.message_handler(commands=['pesca', 'pescar'])
def handle_pescar(message):
    pescar(message)
    
@bot.message_handler(commands=['spicnic'])
def handle_spicnic(message):
    spicnic_command(message)
@bot.message_handler(commands=['delcards'])
def delcards_handler(message):
    delcards_command(message)
    
@bot.message_handler(commands=['versubs'])
def versubs_handler(message):
    versubs_command(message)

@bot.message_handler(commands=['rep'])
def ver_repetidos_evento_handler(message):
    ver_repetidos_evento(message)

@bot.message_handler(commands=['progresso'])
def progresso_evento_handler(message):
    progresso_evento(message)
    
@bot.message_handler(commands=['saldo'])
def saldo_command(message):
    processar_saldo_usuario(message)

@bot.message_handler(commands=['trintadas', 'abelhadas', 'abelhas'])
def handle_trintadas(message):
    enviar_mensagem_trintadas(message, pagina_atual=1)
    
@bot.message_handler(commands=['setmusica', 'setmusic'])
def set_musica_command(message):
    handle_set_musica(message)

@bot.message_handler(commands=['evento'])
def evento_command(message):
    handle_evento_command(message)

@bot.message_handler(commands=['setfav'])
def set_fav_command(message):
    from eu import handle_set_fav
    handle_set_fav(message)

@bot.message_handler(commands=['usuario'])
def obter_username_por_comando(message):
    from eu import handle_obter_username
    handle_obter_username(message)

@bot.message_handler(commands=['eu'])
def me_command(message):
    from eu import handle_me_command
    handle_me_command(message)
    
@bot.message_handler(commands=['gperfil'])
def gperfil_command(message):
    from eu import handle_gperfil_command
    handle_gperfil_command(message)

@bot.message_handler(commands=['config'])
def config_command(message):
    from eu import handle_config
    handle_config(message)
@bot.message_handler(commands=['gnome'])
def handle_gnome(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        partes = message.text.split()
        if 'e' in partes:
            nome = ' '.join(partes[2:])
            sql_personagens = """
                SELECT
                    e.id_personagem,
                    e.nome,
                    e.subcategoria,
                    e.categoria,
                    COALESCE(i.quantidade, 0) AS quantidade_usuario,
                    e.imagem
                FROM evento e
                LEFT JOIN inventario i ON e.id_personagem = i.id_personagem AND i.id_usuario = %s
                WHERE e.nome LIKE %s
            """
        else:
            nome = ' '.join(partes[1:])
            sql_personagens = """
                SELECT
                    p.id_personagem,
                    p.nome,
                    p.subcategoria,
                    p.categoria,
                    COALESCE(i.quantidade, 0) AS quantidade_usuario,
                    p.imagem
                FROM personagens p
                LEFT JOIN inventario i ON p.id_personagem = i.id_personagem AND i.id_usuario = %s
                WHERE p.nome LIKE %s
            """

        values_personagens = (user_id, f"%{nome}%")
        conn, cursor = conectar_banco_dados()
        cursor.execute(sql_personagens, values_personagens)
        resultados_personagens = cursor.fetchall()

        if not resultados_personagens:
            bot.send_message(chat_id, f"Nenhum personagem encontrado com o nome '{nome}'.")
            return

        # Salvar os resultados no dicionário global para navegação posterior
        globals.resultados_gnome[user_id] = resultados_personagens

        # Exibir a primeira carta - ENVIA ao invés de editar
        enviar_primeira_carta(chat_id, user_id, resultados_personagens, 0)

    except Exception as e:
        print(f"Erro: {e}")
    finally:
        fechar_conexao(cursor, conn)


def enviar_primeira_carta(chat_id, user_id, resultados_personagens, index):
    id_personagem, nome, subcategoria, categoria, quantidade_usuario, imagem_url = resultados_personagens[index]

    # Criação da mensagem para a carta
    mensagem = f"💌 | Personagem:\n\n<code>{id_personagem}</code> • {nome}\nde {subcategoria}\n"
    if quantidade_usuario > 0:
        mensagem += f"☀ | {quantidade_usuario}⤫"
    else:
        mensagem += f"🌧 | Tempo fechado..."

    # Botões de navegação
    keyboard = types.InlineKeyboardMarkup()
    if index > 0:
        keyboard.add(types.InlineKeyboardButton("⬅️ Anterior", callback_data=f"gnome_prev_{index-1}_{user_id}"))
    if index < len(resultados_personagens) - 1:
        keyboard.add(types.InlineKeyboardButton("Próxima ➡️", callback_data=f"gnome_next_{index+1}_{user_id}"))

    # Verificar se existe uma imagem GIF ou URL para a carta
    gif_url = obter_gif_url(id_personagem, user_id)
    if gif_url:
        imagem_url = gif_url

    # Enviar a primeira mensagem
    try:
        if imagem_url.lower().endswith(".gif"):
            bot.send_animation(chat_id, imagem_url, caption=mensagem, parse_mode="HTML", reply_markup=keyboard)
        elif imagem_url.lower().endswith(".mp4"):
            bot.send_video(chat_id, imagem_url, caption=mensagem, parse_mode="HTML", reply_markup=keyboard)
        elif imagem_url.lower().endswith((".jpeg", ".jpg", ".png")):
            bot.send_photo(chat_id, imagem_url, caption=mensagem, parse_mode="HTML", reply_markup=keyboard)
        else:
            bot.send_message(chat_id, mensagem, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        print(f"Erro ao enviar a mídia: {e}")
        bot.send_message(chat_id, mensagem, reply_markup=keyboard, parse_mode="HTML")


def editar_carta(chat_id, user_id, resultados_personagens, index, message_id):
    id_personagem, nome, subcategoria, categoria, quantidade_usuario, imagem_url = resultados_personagens[index]

    # Criação da mensagem para a carta
    mensagem = f"💌 | Personagem:\n\n<code>{id_personagem}</code> • {nome}\nde {subcategoria}\n"
    if quantidade_usuario > 0:
        mensagem += f"☀ | {quantidade_usuario}⤫"
    else:
        mensagem += f"🌧 | Tempo fechado..."

    # Botões de navegação
    keyboard = types.InlineKeyboardMarkup()
    if index > 0:
        keyboard.add(types.InlineKeyboardButton("⬅️ Anterior", callback_data=f"gnome_prev_{index-1}_{user_id}"))
    if index < len(resultados_personagens) - 1:
        keyboard.add(types.InlineKeyboardButton("Próxima ➡️", callback_data=f"gnome_next_{index+1}_{user_id}"))

    # Verificar se existe uma imagem GIF ou URL para a carta
    gif_url = obter_gif_url(id_personagem, user_id)
    if gif_url:
        imagem_url = gif_url

    # Editar a mensagem existente com a nova carta
    try:
        if imagem_url.lower().endswith(".gif"):
            bot.edit_message_media(media=types.InputMediaAnimation(media=imagem_url, caption=mensagem, parse_mode="HTML"),
                                   chat_id=chat_id, message_id=message_id, reply_markup=keyboard)
        elif imagem_url.lower().endswith(".mp4"):
            bot.edit_message_media(media=types.InputMediaVideo(media=imagem_url, caption=mensagem, parse_mode="HTML"),
                                   chat_id=chat_id, message_id=message_id, reply_markup=keyboard)
        elif imagem_url.lower().endswith((".jpeg", ".jpg", ".png")):
            bot.edit_message_media(media=types.InputMediaPhoto(media=imagem_url, caption=mensagem, parse_mode="HTML"),
                                   chat_id=chat_id, message_id=message_id, reply_markup=keyboard)
        else:
            bot.edit_message_text(mensagem, chat_id=chat_id, message_id=message_id, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        print(f"Erro ao editar a mídia: {e}")
        bot.edit_message_text(mensagem, chat_id=chat_id, message_id=message_id, reply_markup=keyboard, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data.startswith('gnome_'))
def callback_gnome_navigation(call):
    data = call.data.split('_')
    action = data[1]  # 'prev' ou 'next'
    index = int(data[2])
    user_id = int(data[3])

    # Recuperar os resultados da pesquisa original
    resultados_personagens = globals.resultados_gnome.get(user_id, [])

    if resultados_personagens:
        # Editar a mensagem existente com a nova carta
        try:
            editar_carta(call.message.chat.id, user_id, resultados_personagens, index, call.message.message_id)
        except Exception as e:
            bot.answer_callback_query(call.id, "Erro ao processar a navegação.")
            print(f"Erro ao processar callback de navegação: {e}")
    else:
        bot.answer_callback_query(call.id, "Não foi possível encontrar os resultados. Tente novamente.")

def gnomes_command(message):
    gnomes(message)
@bot.message_handler(commands=['gid'])
def obter_id_e_enviar_info_com_imagem(message):
    try:
        conn, cursor = conectar_banco_dados()
        user_id = message.from_user.id
        chat_id = message.chat.id

        command_parts = message.text.split()
        if len(command_parts) == 2 and command_parts[1].isdigit():
            id_pesquisa = command_parts[1]

            # Verificar se o ID pertence a um evento
            is_evento = verificar_evento(cursor, id_pesquisa)

            # Se for evento, usa a query de evento
            if is_evento:
                sql_evento = """
                    SELECT
                        e.id_personagem,
                        e.nome,
                        e.subcategoria,
                        COALESCE(i.quantidade, 0) AS quantidade_usuario,
                        e.imagem
                    FROM evento e
                    LEFT JOIN inventario i ON e.id_personagem = i.id_personagem AND i.id_usuario = %s
                    WHERE e.id_personagem = %s
                """
                values_evento = (user_id, id_pesquisa)

                cursor.execute(sql_evento, values_evento)
                resultado_evento = cursor.fetchone()

                if resultado_evento:
                    enviar_mensagem_personagem(chat_id, resultado_evento, message.message_id)
                else:
                    bot.send_message(chat_id, f"Nenhum resultado encontrado para o ID '{id_pesquisa}'.", reply_to_message_id=message.message_id)

            # Se não for evento, trata como personagem regular
            else:
                sql_normal = """
                    SELECT
                        p.id_personagem,
                        p.nome,
                        p.subcategoria,
                        COALESCE(i.quantidade, 0) AS quantidade_usuario,
                        p.imagem,
                        p.cr
                    FROM personagens p
                    LEFT JOIN inventario i ON p.id_personagem = i.id_personagem AND i.id_usuario = %s
                    WHERE p.id_personagem = %s
                """
                values_normal = (user_id, id_pesquisa)

                cursor.execute(sql_normal, values_normal)
                resultado_normal = cursor.fetchone()

                if resultado_normal:
                    enviar_mensagem_personagem(chat_id, resultado_normal, message.message_id)
                else:
                    bot.send_message(chat_id, f"Nenhum resultado encontrado para o ID '{id_pesquisa}'.", reply_to_message_id=message.message_id)
        else:
            bot.send_message(chat_id, "Formato incorreto. Use /gid seguido do ID desejado, por exemplo: /gid 123", reply_to_message_id=message.message_id)
    except Exception as e:
        import traceback
        traceback.print_exc()
        erro = traceback.print_exc()
        mensagem = f"Erro ao processar o ID: {id_pesquisa}. Erro: {e}"
        bot.send_message(grupodeerro, mensagem, parse_mode="HTML")
    finally:
        fechar_conexao(cursor, conn)


def enviar_mensagem_personagem(chat_id, resultado_personagem, message_id):
    id_personagem, nome, subcategoria, quantidade_usuario, imagem_url = resultado_personagem[:5]
    cr = resultado_personagem[5] if len(resultado_personagem) > 5 else None

    # Montar a mensagem
    mensagem = f"💌 | Personagem:\n\n<code>{id_personagem}</code> • {nome}\nde {subcategoria}"
    if quantidade_usuario > 0:
        mensagem += f"\n\n☀ | {quantidade_usuario}⤫"
    else:
        mensagem += f"\n\n🌧 | Tempo fechado..."

    if cr:
        link_cr = obter_link_formatado(cr)
        mensagem += f"\n\n{link_cr}"

    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton("💟", callback_data=f"total_{id_personagem}"))

    gif_url = obter_gif_url(id_personagem, chat_id)

    if gif_url:
        imagem_url = gif_url

    # Enviar mídia
    try:
        if imagem_url.lower().endswith(".gif"):
            bot.send_animation(chat_id, imagem_url, caption=mensagem, reply_markup=markup, reply_to_message_id=message_id, parse_mode="HTML")
        elif imagem_url.lower().endswith(".mp4"):
            bot.send_video(chat_id, imagem_url, caption=mensagem, reply_markup=markup, reply_to_message_id=message_id, parse_mode="HTML")
        elif imagem_url.lower().endswith((".jpeg", ".jpg", ".png")):
            bot.send_photo(chat_id, imagem_url, caption=mensagem, reply_markup=markup, reply_to_message_id=message_id, parse_mode="HTML")
        else:
            bot.send_message(chat_id, mensagem, reply_markup=markup, parse_mode="HTML")
    except Exception as e:
        print(f"Erro ao enviar a mídia: {e}")
        bot.send_message(chat_id, mensagem, reply_markup=markup, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data.startswith('toggle_'))
def handle_toggle_config(call):
    toggle_config(call)

@bot.callback_query_handler(func=lambda call: call.data == 'toggle_casamento')
def handle_toggle_casamento(call):
    toggle_casamento(call)
    
@bot.callback_query_handler(func=lambda call: call.data.startswith("escolher_"))
def handle_callback_escolher_carta(call):
    callback_escolher_carta(call)
    
@bot.callback_query_handler(func=lambda call: call.data.startswith('pescar_'))
def categoria_callback(call):
    try:
        categoria = call.data.replace('pescar_', '')
        chat_id = call.message.chat.id
        message_id = call.message.message_id

        if chat_id and message_id:
            ultimo_clique[chat_id] = {'categoria': categoria}
            categoria_handler(call.message, categoria)
        else:
            print("Invalid message or chat data in the callback query.")
    except Exception as e:
        print(f"Erro em categoria_callback: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('peixes_'))
def callback_peixes(call):
    try:
        parts = call.data.split('_')
        pagina = int(parts[1])
        subcategoria = parts[2]
        
        pagina_peixes_callback(call, pagina, subcategoria)
    except Exception as e:
        print(f"Erro ao processar callback de peixes: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('choose_subcategoria_'))
def callback_subcategoria_handler(call):
    try:
        data = call.data.split('_')
        subcategoria = data[2]
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        conn, cursor = conectar_banco_dados()

        # Verifica se existe um evento fixo para a subcategoria
        evento_fixo = obter_carta_evento_fixo(subcategoria=subcategoria)
        chance = random.randint(1, 100)

        # Se existe evento fixo e a chance de 5% se aplica, envia o evento fixo
        if evento_fixo and chance <= 5:
            emoji, id_personagem_carta, nome, subcategoria, imagem = evento_fixo
            send_card_message(call.message, emoji, id_personagem_carta, nome, subcategoria, imagem)
        else:
            # Caso contrário, envia uma carta aleatória normal da subcategoria
            subcategoria_handler(call.message, subcategoria, cursor, conn, None, chat_id, message_id)
    
    except Exception as e:
        traceback.print_exc()
        erro = traceback.format_exc()
        bot.send_message(grupodeerro, f"Erro em categoria_callback: {e}\n{erro}")
    finally:
        fechar_conexao(cursor, conn)

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirmar_casamento_"))
def handle_confirmar_casamento(call):
    confirmar_casamento(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('cdoacao_'))
def handle_confirmar_doacao(call):
    confirmar_doacao(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('ccancelar_'))
def handle_cancelar_doacao(call):
    cancelar_doacao(call)

@bot.callback_query_handler(func=lambda call: call.data == 'acoes_vendinha')
def handle_acoes_vendinha(call):
    exibir_acoes_vendinha(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('comprar_acao_vendinha_'))
def handle_confirmar_compra_vendinha(call):
    confirmar_compra_vendinha(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirmar_categoria_'))
def handle_processar_compra_vendinha_categoria(call):
    processar_compra_vendinha_categoria(call)

@bot.callback_query_handler(func=lambda call: call.data == 'cancelar_compra_vendinha')
def cancelar_compra_vendinha(call):
    bot.edit_message_caption(caption="Poxa, Até logo!", chat_id=call.message.chat.id, message_id=call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirmar_compra_vendinha_'))
def handle_processar_compra_vendinha(call):
    processar_compra_vendinha(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("change_page_"))
def handle_page_change(call):
    page_index = int(call.data.split("_")[2])
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    data = globals.state_data.get(chat_id)
    if not data:
        return

    if isinstance(data, list):
        mensagens = data
    else:
        return

    total_count = len(mensagens)
    if 0 <= page_index < total_count:
        media_url, mensagem = mensagens[page_index]
        markup = create_navigation_markup(page_index, total_count)

        try:
            update_message_media(media_url, mensagem, chat_id, message_id, markup)
            bot.answer_callback_query(call.id)
        except Exception as e:
            bot.answer_callback_query(call.id, "Falha ao atualizar a mensagem.")
            newrelic.agent.record_exception()    
    else:
        bot.answer_callback_query(call.id, "Índice de página inválido.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('submenu_'))
def handle_submenu(call):
    callback_submenu(call)

@bot.callback_query_handler(func=lambda call: call.data == "add_note")
def handle_add_note_callback(call):
    bot.send_message(call.message.chat.id, "Digite sua anotação para o diário:")
    bot.register_next_step_handler(call.message, receive_note)

@bot.callback_query_handler(func=lambda call: call.data == "cancel_note")
def handle_cancel_note_callback(call):
    bot.send_message(call.message.chat.id, "Anotação cancelada.")
  
@bot.callback_query_handler(func=lambda call: call.data.startswith('versubs_'))
def handle_versubs_callback(call):
    callback_pagina_versubs(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('rep_'))
def callback_repetidas_evento_handler(call):
    callback_repetidas_evento(call)
    
@bot.callback_query_handler(func=lambda call: call.data.startswith('cdoacao_'))
def handle_confirmar_doacao(call):
    confirmar_doacao(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('ccancelar_'))
def handle_cancelar_doacao(call):
    cancelar_doacao(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("submenus_"))
def callback_submenus_handler(call):
    callback_submenus(call)
        
@bot.callback_query_handler(func=lambda call: call.data.startswith('especies_'))
def callback_especies(call):
    try:
        # Extrair a página e a categoria do callback_data
        _, pagina_str, categoria = call.data.split('_')
        pagina_atual = int(pagina_str)

        # Obter o número total de páginas
        conn, cursor = conectar_banco_dados()
        query_total = "SELECT COUNT(DISTINCT subcategoria) FROM personagens WHERE categoria = %s"
        cursor.execute(query_total, (categoria,))
        total_registros = cursor.fetchone()[0]
        total_paginas = (total_registros // 20) + (1 if total_registros % 15 > 0 else 0)

        # Editar a mensagem com os novos dados da página
        editar_mensagem_especies(call, categoria, pagina_atual, total_paginas)

    except Exception as e:
        print(f"Erro ao processar o callback de espécies: {e}")
        bot.reply_to(call.message, "Ocorreu um erro ao processar sua solicitação.")


@bot.callback_query_handler(func=lambda call: call.data.startswith('poço_dos_desejos'))
def handle_poco_dos_desejos_handler(call):
    handle_poco_dos_desejos(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('fazer_pedido'))
def handle_fazer_pedido_handler(call):
    handle_fazer_pedido(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('trintadas_'))
def callback_trintadas(call):
    data = call.data.split('_')
    user_id_inicial = int(data[1])
    pagina_atual = int(data[2])
    nome_usuario_inicial = data[3]
    editar_mensagem_trintadas(call, user_id_inicial, pagina_atual, nome_usuario_inicial)

@bot.callback_query_handler(func=lambda call: call.data.startswith('fazer_pedido'))
def handle_fazer_pedido(call):
    processar_pedido_peixes(call)
    
@bot.callback_query_handler(func=lambda call: call.data.startswith('notificar_'))
def callback_handler(call):
    processar_notificacao_personagem(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith(('next_button', 'prev_button')))
def navigate_messages(call):
    handle_navigate_messages(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith(('prox_button', 'ant_button')))
def navigate_gnome_results(call):
    handle_navigate_gnome_results(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("cesta_"))
def callback_query_cesta(call):
    handle_callback_query_cesta(call)
        
@bot.callback_query_handler(func=lambda call: call.data.startswith('total_'))
def callback_total_personagem(call):
    handle_callback_total_personagem(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith(('armazem_anterior_', 'armazem_proxima_','armazem_ultima_','armazem_primeira_')))
def callback_paginacao_armazem(call):
    handle_callback_paginacao_armazem(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('subcategory_'))
def handle_callback_subcategory(call):
    callback_subcategory(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('cenourar_sim_'))
def handle_callback_cenourar(call):
    callback_cenourar(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('loja_geral'))
def callback_loja_geral(call):
    try:
        loja_geral_callback(call)
    except Exception as e:
        print(f"Erro ao processar callback de loja geral: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('img_'))
def callback_img_peixes_handler(call):
    try:
        dados = call.data.split('_')
        pagina = int(dados[-2])
        subcategoria = dados[-1]
        callback_img_peixes(call, pagina, subcategoria)
    except Exception as e:
        newrelic.agent.record_exception()    
        print(f"Erro ao processar callback 'img' de peixes: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('peixes_'))
def callback_peixes(call):
    try:
        dados = call.data.split('_')
        pagina = int(dados[-2])
        subcategoria = dados[-1]
        pagina_peixes_callback(call, pagina, subcategoria)
    except Exception as e:
        print(f"Erro ao processar callback de peixes: {e}")
        newrelic.agent.record_exception()
@bot.callback_query_handler(func=lambda call: call.data.startswith("tag_"))
def callback_tag(call):
    try:
        parts = call.data.split('_')
        pagina = int(parts[1])
        nometag = parts[2]
        total_paginas = int(parts[3])
        id_usuario = call.from_user.id
        editar_mensagem_tag(call.message, nometag, pagina, id_usuario,total_paginas)
    except Exception as e:
        print(f"Erro ao processar callback de página para a tag: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('aprovar_'))
def callback_aprovar(call):
    try:
        aprovar_callback(call)
    except Exception as e:
        print(f"Erro ao processar callback de aprovação: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('reprovar_'))
def callback_reprovar(call):
    try:
        reprovar_callback(call)
    except Exception as e:
        print(f"Erro ao processar callback de reprovação: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('repor_'))
def callback_repor(call):
    try:
        quantidade = 1
        message_data = call.data
        parts = message_data.split('_')
        id_usuario = parts[1]
        adicionar_iscas(id_usuario, quantidade, call.message)
    except Exception as e:
        print(f"Erro ao processar callback de reposição: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('loja_loja'))
def callback_loja_loja(call):
    from loja import handle_callback_loja_loja
    handle_callback_loja_loja(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('compra_'))
def callback_compra(call):
    from loja import handle_callback_compra
    handle_callback_compra(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirmar_compra_'))
def callback_confirmar_compra(call):
    from loja import handle_callback_confirmar_compra
    handle_callback_confirmar_compra(call)
        
@bot.callback_query_handler(func=lambda call: call.data.startswith("evt_"))
def callback_query_evento(call):
    handle_callback_query_evento(call)

@bot.message_handler(commands=['start'])
def start_comando(message):
    user_id = message.from_user.id
    nome_usuario = message.from_user.first_name  
    username = message.chat.username
    grupo_id = -4209628464  # ID do grupo para enviar a notificação do /start
    print(f"Comando /start recebido. ID do usuário: {user_id} - {nome_usuario}")
    # Enviar notificação do start para o grupo
    bot.send_message(grupo_id, f"Novo usuário iniciou o bot: {nome_usuario} (@{username}) - ID: {user_id}")
    try:
        verificar_id_na_tabela(user_id, "ban", "iduser")
        print("Novo /start ", {user_id}, "-", {nome_usuario}, "-", {username})

        if verificar_id_na_tabelabeta(user_id):
            registrar_usuario(user_id, nome_usuario, username)
            registrar_valor("nome_usuario", nome_usuario, user_id)
            
            keyboard = telebot.types.InlineKeyboardMarkup()
            image_url = "https://pub-6f23ef52e8614212a14d24b0cf55ae4a.r2.dev/AgACAgEAAxkBAAIZf2cSyI4kuw-GHGMBuPUdp-Gefo_ZAAKprTEbhPYRRedTrmeod49GAQADAgADeAADNgQ.jpg"
            bot.send_photo(message.chat.id, image_url,
                           caption='Seja muito bem-vindo ao MabiGarden! Entre, busque uma sombra e aproveite a estadia.',
                           reply_markup=keyboard, reply_to_message_id=message.message_id)
        else:
            video_url = "https://pub-6f23ef52e8614212a14d24b0cf55ae4a.r2.dev/BAACAgEAAxkBAAIZfGcSx9DRGzg211Ym_G47xld4U-sdAAJHBQACuXZhRGUFAAGmQXGCtTYE.mp4"
            caption = "🧐 QUEM É VO-CÊ? Estranho detectado! Lembrando que você precisa se identificar antes de usar. Chame a gente no suporte se houver dúvidas!"
            bot.send_video(message.chat.id, video=video_url, caption=caption, reply_to_message_id=message.message_id)

    except ValueError as e:
        print(f"Erro: {e}")
        mensagem_banido = "Você foi banido permanentemente do garden. Entre em contato com o suporte caso haja dúvidas."
        bot.send_message(message.chat.id, mensagem_banido, reply_to_message_id=message.message_id)

@bot.message_handler(commands=['especies'])
def verificar_comando_especies(message):
    try:
        parametros = message.text.split(' ', 1)[1:]  
        if not parametros:
            bot.reply_to(message, "Por favor, forneça a categoria.")
            return

        categoria = parametros[0]
        mostrar_primeira_pagina_especies(message, categoria)

    except Exception as e:
        print(f"Erro ao processar comando /especies: {e}")

@bot.message_handler(commands=['cesta'])
def verificar_cesta(message):
    processar_cesta(message)
    
@bot.message_handler(commands=['submenus'])
def submenus_command(message):
    processar_submenus_command(message)

@bot.message_handler(commands=['submenu'])
def submenu_command(message):
    processar_submenu_command(message)

@bot.callback_query_handler(func=lambda call: call.data.startswith('navigate_submenus_'))
def callback_navegacao_submenus(call):
    callback_navegacao_submenus(call)

def command_historico(message):
    processar_historico_command(message)
    
@bot.message_handler(commands=['sub'])
def sub_command(message):
    processar_sub_command(message)

@bot.callback_query_handler(func=lambda call: call.data.startswith(('s_pagina_', 'f_pagina_', 'all_pagina_')))
def callback_pagina(call):
    callback_pagina_sub(call)
    
@bot.message_handler(commands=['deltag'])
def deletar_tag(message):
    processar_deletar_tag(message)
    
@bot.message_handler(commands=['apoiar'])
def doacao(message):
    markup = telebot.types.InlineKeyboardMarkup()
    chave_pix = "80388add-294e-4075-8cd5-8765cc9f9be0"
    mensagem = f"👨🏻‍🌾 Oi, jardineiro! Se está vendo esta mensagem, significa que está interessado em nos ajudar, certo? A equipe MabiGarden fica muito feliz em saber que nosso trabalho o agradou e o motivou a nos ajudar! \n\nCaso deseje contribuir com PIX, a chave é: <code>{chave_pix}</code> (clique na chave para copiar automaticamente) \n\n"
    bot.send_message(message.chat.id, mensagem, parse_mode="HTML", reply_to_message_id=message.message_id)

@bot.message_handler(commands=['banco'])
def banco_command(message):
    processar_banco_command(message)

@bot.callback_query_handler(func=lambda call: call.data.startswith('banco_pagina_'))
def callback_banco_pagina(call):
    processar_callback_banco_pagina(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('cartas_compradas_pagina_'))
def callback_cartas_compradas(call):
    processar_callback_cartas_compradas(call)

@bot.message_handler(commands=['armazém', 'armazem', 'amz'])
def armazem_command(message):
    try:
        id_usuario = message.from_user.id
        usuario = message.from_user.first_name
        verificar_id_na_tabela(id_usuario, "ban", "iduser")

        conn, cursor = conectar_banco_dados()
        qnt_carta(id_usuario)
        globals.armazem_info[id_usuario] = {'id_usuario': id_usuario, 'usuario': usuario}
        pagina = 1
        resultados_por_pagina = 15
        
        id_fav_usuario, emoji_fav, nome_fav, subcategoria_fav, imagem_fav = obter_favorito(id_usuario)

            

        if id_fav_usuario is not None:
            resposta = f"💌 | Cartas no armazém de {usuario}:\n\n🩷 ∙ {id_fav_usuario} — {nome_fav} de {subcategoria_fav}\n\n"

            sql = f"""
                SELECT id_personagem, emoji, nome_personagem, subcategoria, quantidade, categoria, evento
                FROM (
                    SELECT i.id_personagem, 
                           p.emoji COLLATE utf8mb4_general_ci AS emoji, 
                           p.nome COLLATE utf8mb4_general_ci AS nome_personagem, 
                           p.subcategoria COLLATE utf8mb4_general_ci AS subcategoria, 
                           i.quantidade, 
                           p.categoria COLLATE utf8mb4_general_ci AS categoria, 
                           '' COLLATE utf8mb4_general_ci AS evento
                    FROM inventario i
                    JOIN personagens p ON i.id_personagem = p.id_personagem
                    WHERE i.id_usuario = {id_usuario} AND i.quantidade > 0

                    UNION

                    SELECT e.id_personagem, 
                           e.emoji COLLATE utf8mb4_general_ci AS emoji, 
                           e.nome COLLATE utf8mb4_general_ci AS nome_personagem, 
                           e.subcategoria COLLATE utf8mb4_general_ci AS subcategoria, 
                           0 AS quantidade, 
                           e.categoria COLLATE utf8mb4_general_ci AS categoria, 
                           e.evento COLLATE utf8mb4_general_ci AS evento
                    FROM evento e
                    WHERE e.id_personagem IN (
                        SELECT id_personagem
                        FROM inventario
                        WHERE id_usuario = {id_usuario} AND quantidade > 0
                    )
                ) AS combined
                ORDER BY 
                    CASE WHEN categoria = 'evento' THEN 0 ELSE 1 END, 
                    categoria, 
                    CAST(id_personagem AS UNSIGNED) ASC
                LIMIT {15}
            """
            cursor.execute(sql)
            resultados = cursor.fetchall()

            if resultados:
                markup = telebot.types.InlineKeyboardMarkup()
                buttons_row = [
                    telebot.types.InlineKeyboardButton("⏪️", callback_data=f"armazem_primeira_{pagina}_{id_usuario}"),
                    telebot.types.InlineKeyboardButton("◀️", callback_data=f"armazem_anterior_{pagina}_{id_usuario}"),
                    telebot.types.InlineKeyboardButton("▶️", callback_data=f"armazem_proxima_{pagina}_{id_usuario}"),
                    telebot.types.InlineKeyboardButton("⏩️", callback_data=f"armazem_ultima_{pagina}_{id_usuario}")
                ]
                markup.row(*buttons_row)

                for carta in resultados:
                    id_carta, emoji_carta, nome_carta, subcategoria_carta, quantidade_carta, categoria_carta, evento_carta = carta
                    quantidade_carta = int(quantidade_carta) if quantidade_carta is not None else 0

                    if categoria_carta == 'evento':
                        emoji_carta = obter_emoji_evento(evento_carta)

                    if quantidade_carta == 1:
                        letra_quantidade = ""
                    elif 2 <= quantidade_carta <= 4:
                        letra_quantidade = "🌾"
                    elif 5 <= quantidade_carta <= 9:
                        letra_quantidade = "🌼"
                    elif 10 <= quantidade_carta <= 19:
                        letra_quantidade = "☀️"
                    elif 20 <= quantidade_carta <= 29:
                        letra_quantidade = "🍯️"
                    elif 30 <= quantidade_carta <= 39:
                        letra_quantidade = "🐝"
                    elif 40 <= quantidade_carta <= 49:
                        letra_quantidade = "🌻"
                    elif 50 <= quantidade_carta <= 99:
                        letra_quantidade = "👑"
                    elif 100 <= quantidade_carta:
                        letra_quantidade = "⭐️"    
                    else:
                        letra_quantidade = ""

                    repetida = " [+]" if quantidade_carta > 1 and categoria_carta != 'evento' else ""

                    resposta += f" {emoji_carta} <code>{id_carta}</code> • {nome_carta} - {subcategoria_carta} {letra_quantidade}{repetida}\n"

                quantidade_total_cartas = obter_quantidade_total_cartas(id_usuario)
                total_paginas = (quantidade_total_cartas + resultados_por_pagina - 1) // resultados_por_pagina
                resposta += f"\n{pagina}/{total_paginas}"
                gif_url = obter_gif_url(id_fav_usuario, id_usuario)
                if (gif_url):
                    bot.send_animation(
                        chat_id=message.chat.id,
                        animation=gif_url,
                        caption=resposta,
                        reply_to_message_id=message.message_id,
                        reply_markup=markup,
                        parse_mode="HTML"
                    )
                else:
                    bot.send_photo(
                        chat_id=message.chat.id,
                        photo=imagem_fav,
                        caption=resposta,
                        reply_to_message_id=message.message_id,
                        reply_markup=markup,
                        parse_mode="HTML"
                    )
            return

        resposta = f"💌 | Cartas no armazém de {usuario}:\n\n"

        sql = f"""
            SELECT id_personagem, emoji, nome_personagem, subcategoria, quantidade, categoria, evento
            FROM (
                -- Consulta para cartas no inventário do usuário
                SELECT i.id_personagem, 
                       p.emoji COLLATE utf8mb4_general_ci AS emoji, 
                       p.nome COLLATE utf8mb4_general_ci AS nome_personagem, 
                       p.subcategoria COLLATE utf8mb4_general_ci AS subcategoria, 
                       i.quantidade, 
                       p.categoria COLLATE utf8mb4_general_ci AS categoria, 
                       '' COLLATE utf8mb4_general_ci AS evento
                FROM inventario i
                JOIN personagens p ON i.id_personagem = p.id_personagem
                WHERE i.id_usuario = {id_usuario} AND i.quantidade > 0

                UNION ALL

                -- Consulta para cartas de evento que o usuário possui
                SELECT e.id_personagem, 
                       e.emoji COLLATE utf8mb4_general_ci AS emoji, 
                       e.nome COLLATE utf8mb4_general_ci AS nome_personagem, 
                       e.subcategoria COLLATE utf8mb4_general_ci AS subcategoria, 
                       0 AS quantidade, 
                       e.categoria COLLATE utf8mb4_general_ci AS categoria, 
                       e.evento COLLATE utf8mb4_general_ci AS evento
                FROM evento e
                WHERE e.id_personagem IN (
                    SELECT id_personagem
                    FROM inventario
                    WHERE id_usuario = {id_usuario} AND quantidade > 0
                )
            ) AS combined
            ORDER BY 
                CASE WHEN categoria = 'evento' THEN 0 ELSE 1 END, 
                categoria, 
                CAST(id_personagem AS UNSIGNED) ASC
            LIMIT {resultados_por_pagina} OFFSET {(pagina - 1) * resultados_por_pagina}
        """
        cursor.execute(sql)
        resultados = cursor.fetchall()

        if resultados:
            markup = telebot.types.InlineKeyboardMarkup()
            buttons_row = [
                telebot.types.InlineKeyboardButton("⏪️", callback_data=f"armazem_primeira_{pagina}_{id_usuario}"),
                telebot.types.InlineKeyboardButton("◀️", callback_data=f"armazem_anterior_{pagina}_{id_usuario}"),
                telebot.types.InlineKeyboardButton("▶️", callback_data=f"armazem_proxima_{pagina}_{id_usuario}"),
                telebot.types.InlineKeyboardButton("⏩️", callback_data=f"armazem_ultima_{pagina}_{id_usuario}")
            ]
            markup.row(*buttons_row)

            for carta in resultados:
                id_carta, emoji_carta, nome_carta, subcategoria_carta, quantidade_carta, categoria_carta, evento_carta = carta
                quantidade_carta = int(quantidade_carta) if quantidade_carta is not None else 0

                if categoria_carta == 'evento':
                    emoji_carta = obter_emoji_evento(evento_carta)

                if quantidade_carta == 1:
                    letra_quantidade = ""
                elif 2 <= quantidade_carta <= 4:
                    letra_quantidade = "🌾"
                elif 5 <= quantidade_carta <= 9:
                    letra_quantidade = "🌼"
                elif 10 <= quantidade_carta <= 19:
                    letra_quantidade = "☀️"
                elif 20 <= quantidade_carta <= 29:
                    letra_quantidade = "🍯️"
                elif 30 <= quantidade_carta <= 39:
                    letra_quantidade = "🐝"
                elif 40 <= quantidade_carta <= 49:
                    letra_quantidade = "🌻"
                elif 50 <= quantidade_carta <= 99:
                    letra_quantidade = "👑"
                elif 100 <= quantidade_carta:
                    letra_quantidade = "⭐️"    
                else:
                    letra_quantidade = ""

                repetida = " [+]" if quantidade_carta > 1 and evento_carta else ""

                resposta += f" {emoji_carta} <code>{id_carta}</code> • {nome_carta} - {subcategoria_carta} {letra_quantidade}{repetida}\n"

            quantidade_total_cartas = obter_quantidade_total_cartas(id_usuario)
            total_paginas = (quantidade_total_cartas + resultados_por_pagina - 1) // resultados_por_pagina
            resposta += f"\n{pagina}/{total_paginas}"
            
            carta_aleatoria = random.choice(resultados)
            id_carta_aleatoria, emoji_carta_aleatoria, _, _, _, _ = carta_aleatoria
            foto_carta_aleatoria = obter_url_imagem_por_id(id_carta_aleatoria)
            if foto_carta_aleatoria:
                bot.send_photo(chat_id=message.chat.id, photo=foto_carta_aleatoria, caption=resposta, reply_to_message_id=message.message_id, reply_markup=markup, parse_mode="HTML")
            else:       
                bot.send_message(
                    chat_id=message.chat.id,
                    text=resposta,
                    reply_to_message_id=message.message_id,
                    reply_markup=markup,
                    parse_mode="HTML"
                )
        else:
            bot.send_message(
                chat_id=message.chat.id,
                text="Você não possui cartas no armazém.",
                reply_to_message_id=message.message_id
            )

    except mysql.connector.Error as err:
        print(f"Erro de SQL: {err}")
        newrelic.agent.record_exception()
        bot.send_message(message.chat.id, "Ocorreu um erro ao processar a consulta no banco de dados.")
    except ValueError as e:
        print(f"Erro: {e}")
        mensagem_banido = "Um erro ocorreu ao abrir seu armazém... Tente trocar seu fav usando o coamndo <code>/setfav</code>. Caso não resolva, entre em contato com o suporte."
        bot.send_message(message.chat.id, mensagem_banido,parse_mode="HTML")
    except telebot.apihelper.ApiHTTPException as e:
        print(f"Erro na API do Telegram: {e}")
    finally:
        fechar_conexao(cursor, conn)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    process_callback(call)
    
@bot.message_handler(commands=['youcompat'])
def youcompat_command_handler(message):
    youcompat_command(message)
    
@bot.message_handler(commands=['diamante'])
def mostrar_diamante_handler(message):
    mostrar_diamante_por_nome(message)

@bot.message_handler(commands=['diamantes'])
def mostrar_diamantes_handler(message):
    mostrar_diamantes(message)
    
@bot.message_handler(commands=['incrementar_banco'])
def incrementar_banco_command(message):
    try:
        mensagens = incrementar_quantidades_banco()
        if isinstance(mensagens, list):
            for msg in mensagens:
                bot.send_message(message.chat.id, msg)
        else:
            bot.send_message(message.chat.id, mensagens)
    except Exception as e:
        print(f"Erro ao incrementar quantidades no banco: {e}")
        bot.send_message(message.chat.id, "Erro ao incrementar quantidades no banco.")

@bot.message_handler(commands=['mecompat'])
def mecompat_handler(message):
    mecompat_command(message)

@bot.message_handler(commands=['diary'])
def handle_diary(message):
    diary_command(message)

@bot.message_handler(commands=['pages'])
def handle_pages(message):
    pages_command(message)

@bot.message_handler(commands=['page'])
def handle_page(message):
    page_command(message)                      

@bot.message_handler(commands=['wishlist'])
def verificar_cartas(message):
    try:
        conn, cursor = conectar_banco_dados()
        id_usuario = message.from_user.id

        # Forçar a mesma collation em todas as colunas envolvidas na operação UNION
        sql_wishlist = f"""
            SELECT p.id_personagem, 
                   p.nome COLLATE utf8mb4_general_ci AS nome_personagem, 
                   p.subcategoria COLLATE utf8mb4_general_ci AS subcategoria, 
                   p.emoji COLLATE utf8mb4_general_ci AS emoji
            FROM wishlist w
            JOIN personagens p ON w.id_personagem = p.id_personagem
            WHERE w.id_usuario = {id_usuario}
            
            UNION
            
            SELECT e.id_personagem, 
                   e.nome COLLATE utf8mb4_general_ci AS nome_personagem, 
                   e.subcategoria COLLATE utf8mb4_general_ci AS subcategoria, 
                   e.emoji COLLATE utf8mb4_general_ci AS emoji
            FROM wishlist w
            JOIN evento e ON w.id_personagem = e.id_personagem
            WHERE w.id_usuario = {id_usuario}
        """

        cursor.execute(sql_wishlist)
        cartas_wishlist = cursor.fetchall()

        if cartas_wishlist:
            cartas_removidas = []

            for carta_wishlist in cartas_wishlist:
                id_personagem_wishlist = carta_wishlist[0]
                nome_carta_wishlist = carta_wishlist[1]
                subcategoria_carta_wishlist = carta_wishlist[2]
                emoji_carta_wishlist = carta_wishlist[3]

                cursor.execute("SELECT COUNT(*) FROM inventario WHERE id_usuario = %s AND id_personagem = %s",
                               (id_usuario, id_personagem_wishlist))
                existing_inventory_count = cursor.fetchone()[0]
                inventory_exists = existing_inventory_count > 0

                if inventory_exists:
                    cursor.execute("DELETE FROM wishlist WHERE id_usuario = %s AND id_personagem = %s",
                                   (id_usuario, id_personagem_wishlist))
                    cartas_removidas.append(f"{emoji_carta_wishlist} - {nome_carta_wishlist} de {subcategoria_carta_wishlist}")

            if cartas_removidas:
                resposta = f"Algumas cartas foram removidas da wishlist porque já estão no seu inventário:\n{', '.join(map(str, cartas_removidas))}"
                bot.send_message(message.chat.id, resposta, reply_to_message_id=message.message_id)

            lista_wishlist_atualizada = f"🤞 | Cartas na wishlist de {message.from_user.first_name}:\n\n"
            for carta_atualizada in cartas_wishlist:
                id_carta = carta_atualizada[0]
                emoji_carta = carta_atualizada[3]
                nome_carta = carta_atualizada[1]
                subcategoria_carta = carta_atualizada[2]
                lista_wishlist_atualizada += f"{emoji_carta} ∙ <code>{id_carta}</code> - {nome_carta} de {subcategoria_carta}\n"

            bot.send_message(message.chat.id, lista_wishlist_atualizada, reply_to_message_id=message.message_id, parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, "Sua wishlist está vazia! Devo te desejar parabéns?", reply_to_message_id=message.message_id)

    except mysql.connector.Error as err:
        print(f"Erro de SQL: {err}")
        traceback.print_exc()
        erro = traceback.format_exc()
        mensagem = f"wish com erro: {id_personagem}. erro: {err}\n{erro}"
        bot.send_message(grupodeerro, mensagem, parse_mode="HTML")
        bot.send_message(message.chat.id, "Ocorreu um erro ao processar a consulta no banco de dados.", reply_to_message_id=message.message_id)
    except ValueError as e:
        print(f"Erro: {e}")
        mensagem_banido = "Um erro ocorreu ao abrir seu armazém... Tente trocar seu fav usando o </code>comando /setfav</code>. Caso não resolva, entre em contato com o suporte."
        bot.send_message(message.chat.id, mensagem_banido)
    except telebot.apihelper.ApiHTTPException as e:
        print(f"Erro na API do Telegram: {e}")
    finally:
        conn.commit() 
        fechar_conexao(cursor, conn)



@bot.message_handler(commands=['addw'])
def add_to_wish(message):
    try:
        chat_id = message.chat.id
        id_usuario = message.from_user.id
        command_parts = message.text.split()
        if len(command_parts) == 2:
            id_personagem = command_parts[1]

            conn, cursor = conectar_banco_dados()
            cursor.execute("SELECT COUNT(*) FROM wishlist WHERE id_usuario = %s AND id_personagem = %s",
                           (id_usuario, id_personagem))
            existing_wishlist_count = cursor.fetchone()[0]
            wishlist_exists = existing_wishlist_count > 0

            if wishlist_exists:
                bot.send_message(chat_id, "Você já possui essa carta na wishlist!", reply_to_message_id=message.message_id)
            else:
                cursor.execute("SELECT COUNT(*) FROM inventario WHERE id_usuario = %s AND id_personagem = %s",
                               (id_usuario, id_personagem))
                existing_inventory_count = cursor.fetchone()[0]
                inventory_exists = existing_inventory_count > 0

                if inventory_exists:
                    bot.send_message(chat_id, "Você já possui essa carta no inventário!", reply_to_message_id=message.message_id)
                else:
                    cursor.execute("INSERT INTO wishlist (id_personagem, id_usuario) VALUES (%s, %s)",
                                   (id_personagem, id_usuario))
                    bot.send_message(chat_id, "Carta adicionada à sua wishlist!\nBoa sorte!", reply_to_message_id=message.message_id)
            conn.commit()
    except mysql.connector.Error as err:
        print(f"Erro ao adicionar carta à wishlist: {err}")
    finally:
        fechar_conexao(cursor, conn)

@bot.message_handler(commands=['iduser'])
def handle_iduser_command(message):
    if message.reply_to_message:
        idusuario = message.reply_to_message.from_user.id
        bot.send_message(chat_id=message.chat.id, text=f"O ID do usuário é <code>{idusuario}</code>", reply_to_message_id=message.message_id,parse_mode="HTML")

@bot.message_handler(commands=['ping'])
def ping_command(message):
    start_time = time.time()
    chat_id = message.chat.id

    # Enviar uma mensagem de ping para calcular o tempo de resposta
    sent_message = bot.send_message(chat_id, "Calculando o ping...")

    ping = time.time() - start_time
    queue_size = task_queue.qsize()

    bot.edit_message_text(
        chat_id=chat_id,
        message_id=sent_message.message_id,
        text=f"🏓 Pong!\nPing: {ping:.2f} segundos\nTarefas na fila: {queue_size}"
    )
@bot.message_handler(commands=['wishlist'])
def handle_wishlist(message):
    verificar_cartas(message)

@bot.message_handler(commands=['addw'])
def handle_add_to_wishlist(message):
    add_to_wish(message)

@bot.message_handler(commands=['removew', 'delw'])
def handle_removew(message):
    remover_da_wishlist(message)
    
@bot.message_handler(commands=['cenourar'])
def handle_cenourar(message):
    processar_verificar_e_cenourar(message)

@bot.message_handler(commands=['setbio'])
def handle_setbio(message):
    set_bio_command(message)

@bot.message_handler(commands=['setgif'])
def handle_setgif(message):
    enviar_gif(message)

@bot.message_handler(commands=['admin'])
def handle_admin(message):
    admin(message)

@bot.message_handler(commands=['enviar_mensagem'])
def handle_enviar_mensagem_privada(message):
    enviar_mensagem_privada(message)

@bot.message_handler(commands=['enviar_grupo'])
def handle_enviar_mensagem_grupo(message):
    enviar_mensagem_grupo(message)


@bot.message_handler(commands=['supergroupid'])
def supergroup_id_command(message):
    chat_id = message.chat.id
    chat_type = message.chat.type

    if chat_type == 'supergroup':
        chat_info = bot.get_chat(chat_id)
        bot.send_message(chat_id, f"O ID deste supergrupo é: <code>{chat_info.id}</code>", reply_to_message_id=message.message_id,parse_mode="HTML")
    else:
        bot.send_message(chat_id, "Este chat não é um supergrupo.")

@bot.message_handler(commands=['idchat'])
def handle_idchat_command(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, f"O ID deste chat é<code>{chat_id}</code>", reply_to_message_id=message.message_id,parse_mode="HTML")

@bot.message_handler(commands=['setnome'])
def handle_set_nome(message):
    set_nome_command(message)

@bot.message_handler(commands=['setuser'])
def handle_setuser(message):
    setuser_comando(message)

@bot.message_handler(commands=['removefav'])
def handle_remove_fav(message):
    remove_fav_command(message)
    
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    if message.chat.type == 'private':
        registrar_mensagens_privadas(message)
        
def apagar_cartas_quantidade_zero_ou_negativa():
    conn, cursor = conectar_banco_dados()
    try:
        query = "DELETE FROM inventario WHERE quantidade <= 0"
        cursor.execute(query)
        conn.commit()
        print(f"{cursor.rowcount} cartas deletadas.")
    except mysql.connector.Error as err:
        print(f"Erro: {err}")
    finally:
        cursor.close()
        conn.close()

def registrar_mensagens_privadas(message):
    try:
        conn, cursor = conectar_banco_dados()
        user_id = message.from_user.id
        message_text = message.text
        cursor.execute("INSERT INTO mensagens_privadas (user_id, message_text) VALUES (%s, %s)", (user_id, message_text))
        conn.commit()
    except Exception as e:
        print(f"Erro ao registrar mensagem privada: {e}")
    finally:
        fechar_conexao(cursor, conn)   

def manter_proporcoes(imagem, largura_maxima, altura_maxima):
    largura_original, altura_original = imagem.size
    proporcao_original = largura_original / altura_original

    if proporcao_original > 1:
        nova_largura = largura_maxima
        nova_altura = int(largura_maxima / proporcao_original)
    else:
        nova_altura = altura_maxima
        nova_largura = int(altura_maxima * proporcao_original)

    return imagem.resize((nova_largura, nova_altura))        

# Função para criar a colagem
def criar_colagem(message):
    if message.from_user.id not in allowed_user_ids:
        bot.send_message(message.chat.id, "Você não tem permissão para usar este comando.")
        return

    try:
        cartas_aleatorias = obter_cartas_aleatorias()
        data_atual_str = dt_module.date.today().strftime("%Y-%m-%d") 
        if not cartas_aleatorias:
            bot.send_message(message.chat.id, "Não foi possível obter cartas aleatórias.")
            return

        registrar_cartas_loja(cartas_aleatorias, data_atual_str)

        imagens = []
        for carta in cartas_aleatorias:
            img_url = carta.get('imagem', '')
            try:
                if img_url:
                    response = requests.get(img_url)
                    if response.status_code == 200:
                        img = Image.open(io.BytesIO(response.content))
                        img = img.resize((300, 400), Image.LANCZOS)
                    else:
                        img = Image.new('RGB', (300, 400), color='black')
                else:
                    img = Image.new('RGB', (300, 400), color='black')
            except Exception as e:
                print(f"Erro ao abrir a imagem da carta {carta['id']}: {e}")
                img = Image.new('RGB', (300, 400), color='black')
            imagens.append(img)

        altura_total = (len(imagens) // 3) * 400

        colagem = Image.new('RGB', (900, altura_total))  
        coluna_atual = 0
        linha_atual = 0

        for img in imagens:
            colagem.paste(img, (coluna_atual, linha_atual))
            coluna_atual += 300

            if coluna_atual >= 900:
                coluna_atual = 0
                linha_atual += 400

        colagem.save('colagem_cartas.png')
        
        mensagem_loja = "🐟 Peixes na vendinha hoje:\n\n"
        for carta in cartas_aleatorias:
            mensagem_loja += f"{carta['emoji']}| {carta['id']} • {carta['nome']} - {carta['subcategoria']}\n"
        mensagem_loja += "\n🥕 Acesse usando o comando /vendinha"

        with open('colagem_cartas.png', 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=mensagem_loja, reply_to_message_id=message.message_id)

    except Exception as e:
        print(f"Erro ao criar colagem: {e}")
        bot.send_message(message.chat.id, "Erro ao criar colagem.")

if __name__ == "__main__":
    app.run(host=WEBHOOK_LISTEN, port=int(WEBHOOK_PORT), debug=False)

