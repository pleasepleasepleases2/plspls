import telebot
import mysql.connector
import random
import requests
import time
import datetime
import re
import datetime as dt_module  
import io
import functools
import json
import threading
import os
import Levenshtein
import diskcache as dc
import spotipy
import math
import logging

from queue import Queue
from telebot.types import InputMediaPhoto
from datetime import datetime, timedelta
from datetime import date
from PIL import Image, ImageDraw, ImageFont, ImageOps
from io import BytesIO
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from urllib.parse import urlparse
from mysql.connector import Error
from cestas import *
from album import *
from pescar import *
from evento import *
from spotipy.oauth2 import SpotifyClientCredentials
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import utc
from phrases import *
from bs4 import BeautifulSoup
from callbacks2 import choose_subcategoria_callback
import globals
from trocas import *
from bd import *
from saves import *
from calculos import *
from fonte import *
from trintadas import *
from eu import *
from submenu import *
from especies import *
from config import *
from historico import *
from tag import *
from banco import *
from diary import *
from admin import obter_id_beta,remover_beta,verificar_ban,obter_id_cenouras,obter_id_iscas,remover_id_cenouras,remover_id_iscas,verificar_autorizacao
from peixes import *
import logging
import flask
import http.server
import socketserver

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)
processing_lock = threading.Lock()
ids_proibidos = {164, 165, 163, 174, 192, 214, 215, 216}
scheduler = BackgroundScheduler(timezone=utc)
scheduler.start()
API_TOKEN="7088149058:AAECPYzJ_f32mJk01D8zT70__UxqUT62EDM"
SPOTIFY_CLIENT_ID="804047efa98c4d1d81da250b0770c05d"
SPOTIFY_CLIENT_SECRET="6deb00cb4cea42f79abe41cc4da05f13"
DB_HOST="127.0.0.1"
DB_USER="teste"
DB_PASS="#Folkevermore13"
DB_NAME="garden"
WEBHOOK_URL_BASE = os.getenv("mabigarden-production.up.railway.app")
API_TOKEN = os.getenv(API_TOKEN)
APP_URL = os.getenv(WEBHOOK_URL_BASE) + os.getenv('WEBHOOK_URL_PATH')
WEBHOOK_URL_PATH = '/' + API_TOKEN + '/'
APP_URL = WEBHOOK_URL_BASE + WEBHOOK_URL_PATH

logger = telebot.logger
telebot.logger.setLevel(logging.INFO)

bot = telebot.TeleBot(API_TOKEN)

app = flask.Flask(__name__)






@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET))
cache = dc.Cache('./cache')  
conn, cursor = conectar_banco_dados()
task_queue = Queue()
grupodeerro = -4279935414
def process_tasks():
    while True:
        task = task_queue.get()
        if task is None:
            break
        task()
        task_queue.task_done()
task_thread = threading.Thread(target=process_tasks)
task_thread.start()
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
def callback_pescar(call):
    try:
        data = call.data.split('_')
        subcategoria = data[2]
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        choose_subcategoria_callback(call, subcategoria, cursor, conn,chat_id,message_id)    
    except Exception as e:
        print(f"Erro ao processar callback de pescar: {e}")    
@bot.message_handler(commands=['ervadaninha'])
def listar_bloqueios(message):
    try:
        if message.chat.type != 'private':
            bot.send_message(message.chat.id, "Este comando só pode ser usado em uma conversa privada.")
            return

        id_bloqueador = message.from_user.id

        conn, cursor = conectar_banco_dados()

        cursor.execute("""
            SELECT u.user 
            FROM bloqueios b
            JOIN usuarios u ON b.id_bloqueado = u.id_usuario
            WHERE b.id_usuario = %s
        """, (id_bloqueador,))

        bloqueados = cursor.fetchall()

        if not bloqueados:
            bot.send_message(message.chat.id, "Você não bloqueou nenhum jardineiro.")
            return

        resposta = "Lista de jardineiros bloqueados:\n\n"
        for bloqueado in bloqueados:
            resposta += f"𓇣 {bloqueado[0]}\n"

        bot.send_message(message.chat.id, resposta)
    except mysql.connector.Error as err:
        bot.send_message(message.chat.id, f"Erro ao listar bloqueios: {err}")
    finally:
        fechar_conexao(cursor, conn)

# Adicionando o handler para o comando /delgif
@bot.message_handler(commands=['delgif'])
def handle_delgif(message):
    processar_comando_delgif(message)

@bot.message_handler(commands=['blockjardineiro'])
def bloquear_jardineiro(message):
    try:
        args = message.text.split()
        if len(args) != 2:
            bot.send_message(message.chat.id, "Uso correto: /blockjardineiro <username>")
            return

        username = args[1].replace("@", "")  # Remover o símbolo "@" se estiver presente
        id_bloqueador = message.from_user.id

        conn, cursor = conectar_banco_dados()

        cursor.execute("SELECT id_usuario FROM usuarios WHERE user = %s", (username,))
        resultado = cursor.fetchone()

        if not resultado:
            bot.send_message(message.chat.id, f"Usuário {username} não encontrado.")
            return

        id_bloqueado = resultado[0]

        cursor.execute("SELECT * FROM bloqueios WHERE id_usuario = %s AND id_bloqueado = %s", (id_bloqueador, id_bloqueado))
        if cursor.fetchone():
            bot.send_message(message.chat.id, "Usuário já está bloqueado.")
            return

        cursor.execute("INSERT INTO bloqueios (id_usuario, id_bloqueado) VALUES (%s, %s)", (id_bloqueador, id_bloqueado))
        conn.commit()

        bot.send_message(message.chat.id, f"Usuário {username} bloqueado com sucesso.")

    except mysql.connector.Error as err:
        bot.send_message(message.chat.id, f"Erro ao bloquear jardineiro: {err}")
        
            
@bot.message_handler(commands=['raspadinha'])
def handle_sorte(message):
    comando_sorte(message)
    
@bot.message_handler(commands=['addjardineiro'])
def adicionar_jardineiro(message):
    try:
        args = message.text.split()
        if len(args) != 2:
            bot.send_message(message.chat.id, "Uso correto: /addjardineiro <username>")
            return

        username = args[1].replace("@", "")  # Remover o símbolo "@" se estiver presente
        id_solicitante = message.from_user.id

        conn, cursor = conectar_banco_dados()

        cursor.execute("SELECT id_usuario FROM usuarios WHERE user = %s", (username,))
        resultado = cursor.fetchone()

        if not resultado:
            bot.send_message(message.chat.id, f"Usuário {username} não encontrado.")
            return

        id_amigo = resultado[0]

        cursor.execute("SELECT * FROM amizades WHERE id_solicitante = %s AND id_amigo = %s", (id_solicitante, id_amigo))
        if cursor.fetchone():
            bot.send_message(message.chat.id, "Solicitação de amizade já enviada.")
            return

        cursor.execute("INSERT INTO amizades (id_solicitante, id_amigo, status) VALUES (%s, %s, 'pendente')", (id_solicitante, id_amigo))
        conn.commit()

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Aceitar", callback_data=f"aceitar_amizade_{id_solicitante}"),
                   InlineKeyboardButton("Recusar", callback_data=f"recusar_amizade_{id_solicitante}"))

        bot.send_message(id_amigo, f"Você recebeu uma solicitação de amizade de {message.from_user.first_name}.", reply_markup=markup)

    except mysql.connector.Error as err:
        bot.send_message(message.chat.id, f"Erro ao adicionar jardineiro: {err}")

    
@bot.callback_query_handler(func=lambda call: call.data.startswith('aceitar_amizade_') or call.data.startswith('recusar_amizade_'))
def resposta_solicitacao_amizade(call):
    try:
        conn, cursor = conectar_banco_dados()
        data_parts = call.data.split('_')
        acao = data_parts[0] + '_' + data_parts[1]
        id_solicitante = int(data_parts[2])
        id_amigo = call.from_user.id

        if acao == 'aceitar_amizade':
            cursor.execute("UPDATE amizades SET status = 'aceito' WHERE id_solicitante = %s AND id_amigo = %s", (id_solicitante, id_amigo))
            conn.commit()
            bot.send_message(id_solicitante, f"{call.from_user.first_name} aceitou sua solicitação de amizade.")
            bot.send_message(call.message.chat.id, "Você aceitou a solicitação de amizade.")
        elif acao == 'recusar_amizade':
            cursor.execute("DELETE FROM amizades WHERE id_solicitante = %s AND id_amigo = %s", (id_solicitante, id_amigo))
            conn.commit()
            bot.send_message(id_solicitante, f"{call.from_user.first_name} recusou sua solicitação de amizade.")
            bot.send_message(call.message.chat.id, "Você recusou a solicitação de amizade.")
    except mysql.connector.Error as err:
        bot.send_message(call.message.chat.id, f"Erro ao processar solicitação de amizade: {err}")
    finally:
        fechar_conexao(cursor, conn)

@bot.message_handler(commands=['jardim'])
def ver_jardim(message):
    try:
        id_usuario = message.from_user.id
        conn, cursor = conectar_banco_dados()
        
        cursor.execute("""
            SELECT u.user 
            FROM amizades a
            JOIN usuarios u ON a.id_amigo = u.id_usuario
            WHERE a.id_solicitante = %s AND a.status = 'aceito'
        """, (id_usuario,))
        
        amigos = cursor.fetchall()

        if not amigos:
            bot.send_message(message.chat.id, "Você ainda não tem jardineiros amigos.")
            return

        resposta = "Lista de jardineiros amigos:\n\n"
        for amigo in amigos:
            resposta += f"❀ {amigo[0]}\n"

        bot.send_message(message.chat.id, resposta)
    except mysql.connector.Error as err:
        bot.send_message(message.chat.id, f"Erro ao buscar lista de amigos: {err}")
    finally:
        fechar_conexao(cursor, conn)
       
@bot.callback_query_handler(func=lambda call: call.data.startswith('cdoacao_'))
def confirmar_doacao(call):
    try:
        data = call.data.split('_')
        if len(data) != 5:
            bot.send_message(call.message.chat.id, "Dados de doação inválidos.")
            return

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
            bot.edit_message_text(texto_confirmacao, chat_id=call.message.chat.id, message_id=call.message.message_id)
        else:
            if quantidade_doador_anterior < quantidade:
                bot.edit_message_text("Você não possui cartas suficientes para fazer a doação.", chat_id=call.message.chat.id, message_id=call.message.message_id)
            elif cenouras_doador < quantidade:
                bot.edit_message_text("Você não possui cenouras suficientes para fazer a doação.", chat_id=call.message.chat.id, message_id=call.message.message_id)
    except Exception as e:
        print(f"Erro ao confirmar a doação: {e}")
        bot.send_message(call.message.chat.id, "Erro ao confirmar a doação.")
    finally:
        fechar_conexao(cursor, conn)



@bot.callback_query_handler(func=lambda call: call.data.startswith('ccancelar_'))
def cancelar_doacao(call):
    try:
        bot.edit_message_text("Doação cancelada.", chat_id=call.message.chat.id, message_id=call.message.message_id)
    except Exception as e:
        print(f"Erro ao cancelar a doação: {e}")
        bot.send_message(call.message.chat.id, "Erro ao cancelar a doação.")
        
@bot.callback_query_handler(func=lambda call: call.data == 'acoes_vendinha')
def exibir_acoes_vendinha(call):
    try:
        mensagem = "📦 Pacotes de Ações disponíveis:\n\n"
        mensagem += "🥕 Pacote Básico: 50 cenouras - 10 cartas\n"
        mensagem += "💸 Pacote Médio: 100 cenouras - 25 cartas\n"
        mensagem += "💳 Pacote Premium: 200 cenouras - 80 cartas\n\n"
        
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            telebot.types.InlineKeyboardButton(text="🥕", callback_data='comprar_acao_vendinha_basico'),
            telebot.types.InlineKeyboardButton(text="💸", callback_data='comprar_acao_vendinha_prata'),
            telebot.types.InlineKeyboardButton(text="💳", callback_data='comprar_acao_vendinha_ouro')
        )
        
        bot.edit_message_caption(caption=mensagem, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=keyboard)
    except Exception as e:
        print(f"Erro ao exibir pacotes de ações: {e}")
        bot.send_message(call.message.chat.id, "Erro ao exibir pacotes de ações.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('comprar_acao_vendinha_'))
def confirmar_compra_vendinha(call):
    pacote = call.data.split('_')[3]
    pacotes = {
        'basico': ('Pacote Básico', 50),
        'prata': ('Pacote Médio', 100),
        'ouro': ('Pacote Premium', 200)
    }
    
    if pacote in pacotes:
        nome_pacote, preco = pacotes[pacote]
        mensagem = f"Deseja gastar {preco} cenouras com o {nome_pacote}?"
        
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            telebot.types.InlineKeyboardButton(text="Sim", callback_data=f'confirmar_compra_vendinha_{pacote}'),
            telebot.types.InlineKeyboardButton(text="Não", callback_data='cancelar_compra_vendinha')
        )
        
        bot.edit_message_caption(caption=mensagem, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == 'cancelar_compra_vendinha')
def cancelar_compra_vendinha(call):
    bot.edit_message_caption(caption="Até logo!", chat_id=call.message.chat.id, message_id=call.message.message_id)
    
    
@bot.callback_query_handler(func=lambda call: call.data.startswith('confirmar_compra_vendinha_'))
def processar_compra_vendinha(call):
    pacote = call.data.split('_')[3]
    pacotes = {
        'basico': (10, 50),
        'prata': (25, 100),
        'ouro': (80, 200)
    }

    if pacote in pacotes:
        quantidade, preco = pacotes[pacote]
        id_usuario = call.from_user.id

        conn, cursor = conectar_banco_dados()
        cursor.execute("SELECT cenouras FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        cenouras = cursor.fetchone()[0]

        if cenouras >= preco:
            cartas = obter_cartas_do_banco(quantidade)
            atualizar_inventario(id_usuario, cartas)
            cursor.execute("UPDATE usuarios SET cenouras = cenouras - %s WHERE id_usuario = %s", (preco, id_usuario))
            conn.commit()

            globals.cartas_compradas_dict[id_usuario] = cartas

            bot.edit_message_caption(caption="Compra realizada com sucesso! Verifique seu inventário.", chat_id=call.message.chat.id, message_id=call.message.message_id)
            mostrar_cartas_compradas(call.message.chat.id, cartas, id_usuario, 1, call.message.message_id)
        else:
            bot.edit_message_caption(caption="Cenouras insuficientes para realizar a compra.", chat_id=call.message.chat.id, message_id=call.message.message_id)
    else:
        bot.edit_message_caption(caption="Pacote inválido.", chat_id=call.message.chat.id, message_id=call.message.message_id)


def registrar_grupo(chat_id, chat_title):
    conn, cursor = conectar_banco_dados()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
    INSERT OR IGNORE INTO grupos_registrados (chat_id, title, timestamp)
    VALUES (?, ?, ?)
    ''', (chat_id, chat_title, timestamp))
    conn.commit()
    conn.close()
@bot.message_handler(commands=['pesca', 'pescar'])
def pescar(message):
    try:
        nome = message.from_user.first_name
        user_id = message.from_user.id

        verificar_id_na_tabela(user_id, "ban", "iduser")
        if message.chat.type != 'private':
            bot.send_message(message.chat.id, "Este comando só pode ser usado em uma conversa privada.")
            return

        qtd_iscas = verificar_giros(user_id)
        if qtd_iscas == 0:
            bot.send_message(message.chat.id, "Você está sem iscas.", reply_to_message_id=message.message_id)
        else:
            if not verificar_tempo_passado(message.chat.id):
                return
            else:
                ultima_interacao[message.chat.id] = datetime.now()

            if verificar_id_na_tabelabeta(user_id):
                diminuir_giros(user_id, 1)
                keyboard = telebot.types.InlineKeyboardMarkup()

                primeira_coluna = [
                    telebot.types.InlineKeyboardButton(text="☁  Música", callback_data='pescar_musica'),
                    telebot.types.InlineKeyboardButton(text="🌷 Anime", callback_data='pescar_animanga'),
                    telebot.types.InlineKeyboardButton(text="🧶  Jogos", callback_data='pescar_jogos')
                ]
                segunda_coluna = [
                    telebot.types.InlineKeyboardButton(text="🍰  Filmes", callback_data='pescar_filmes'),
                    telebot.types.InlineKeyboardButton(text="🍄  Séries", callback_data='pescar_series'),
                    telebot.types.InlineKeyboardButton(text="🍂  Misc", callback_data='pescar_miscelanea')
                ]

                keyboard.add(*primeira_coluna)
                keyboard.add(*segunda_coluna)
                keyboard.row(telebot.types.InlineKeyboardButton(text="🫧  Geral", callback_data='pescar_geral'))

                photo = "https://telegra.ph/file/b3e6d2a41b68c2ceec8e5.jpg"
                bot.send_photo(message.chat.id, photo=photo, caption=f'<i>Olá! {nome}, \nVocê tem disponível: {qtd_iscas} iscas. \nBoa pesca!\n\nSelecione uma categoria:</i>', reply_markup=keyboard, reply_to_message_id=message.message_id, parse_mode="HTML")
            else:
                bot.send_message(message.chat.id, "Ei visitante, você não foi convidado! 😡", reply_to_message_id=message.message_id)

    except ValueError as e:
        print(f"Erro: {e}")
        bot.send_message(message.chat.id, "Você foi banido permanentemente do garden. Entre em contato com o suporte caso haja dúvidas.", reply_to_message_id=message.message_id)


@bot.message_handler(commands=['picnic'])
@bot.message_handler(commands=['trocar'])
@bot.message_handler(commands=['troca'])
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
        if verificar_bloqueio(eu, voce):
            bot.send_message(chat_id, "A troca não pode ser realizada porque um dos usuários bloqueou o outro.")
            return
        if voce == bot_id:
            bot.send_message(chat_id, "Você não pode fazer trocas com a Mabi :(", reply_to_message_id=message.message_id)
            return

        if verifica_inventario_troca(eu, minhacarta) == 0:
            bot.send_message(chat_id, f"🌦️ ་  {meunome}, você não possui o peixe {minhacarta} para trocar.", reply_to_message_id=message.message_id)
            return
        
        if verifica_inventario_troca(voce, suacarta) == 0:
            bot.send_message(chat_id, f"🌦️ ་  Parece que {seunome} não possui o peixe {suacarta} para trocar.", reply_to_message_id=message.message_id)
            return

        info_minhacarta = obter_informacoes_carta(minhacarta)
        info_suacarta = obter_informacoes_carta(suacarta)
        emojiminhacarta, idminhacarta, nomeminhacarta, subcategoriaminhacarta = info_minhacarta
        emojisuacarta, idsuacarta, nomesuacarta, subcategoriasuacarta = info_suacarta
        meu_username = bot.get_chat_member(chat_id, eu).user.username
        seu_username = bot.get_chat_member(chat_id, voce).user.username

        seu_nome_formatado = f"@{seu_username}" if seu_username else seunome
        texto = (
            f"🥪 | Hora do picnic!\n\n"
            f"{meunome} oferece de lanche:\n"
            f" {idminhacarta} {emojiminhacarta}  —  {nomeminhacarta} de {subcategoriaminhacarta}\n\n"
            f"E {seunome} oferece de lanche:\n"
            f" {idsuacarta} {emojisuacarta}  —  {nomesuacarta} de {subcategoriasuacarta}\n\n"
            f"Podemos começar a comer, {seu_nome_formatado}?"
        )

        keyboard = types.InlineKeyboardMarkup()

        primeiro = [
            types.InlineKeyboardButton(text="✅",
                                       callback_data=f'troca_sim_{eu}_{voce}_{minhacarta}_{suacarta}_{chat_id}'),
            types.InlineKeyboardButton(text="❌", callback_data=f'troca_nao_{eu}_{voce}_{minhacarta}_{suacarta}_{chat_id}'),
        ]
        keyboard.add(*primeiro)

        image_url = "https://telegra.ph/file/8672c8f91c8e77bcdad45.jpg"
        bot.send_photo(chat_id, image_url, caption=texto, reply_markup=keyboard, reply_to_message_id=message.reply_to_message.message_id)

    except Exception as e:
        traceback.print_exc()
        erro = traceback.format_exc()
        eu = message.from_user.id
        voce = message.reply_to_message.from_user.id
        seunome = message.reply_to_message.from_user.first_name
        meunome = message.from_user.first_name
        bot_id = 7088149058
        categoria = message.text.replace('/troca', '')
        minhacarta = message.text.split()[1]
        suacarta = message.text.split()[2]
        mensagem = f"Erro durante a troca. dados: {voce},{eu},{minhacarta},{suacarta}\n{erro}"
        bot.send_message(grupodeerro, mensagem, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data.startswith('banco_pagina_'))
def callback_banco_pagina(call):
    pagina = int(call.data.split('_')[-1])

    conn, cursor = conectar_banco_dados()
    cursor.execute("SELECT id_personagem, quantidade FROM banco_inventario ORDER BY id_personagem ASC")
    cartas_banco = cursor.fetchall()
    total_paginas = (len(cartas_banco) // 30) + (1 if len(cartas_banco) % 30 > 0 else 0)
    total_cartas = sum([quantidade for _, quantidade in cartas_banco])
    mostrar_cartas_banco(call.message.chat.id, pagina, total_paginas, cartas_banco,total_cartas, call.message.message_id)
    fechar_conexao(cursor, conn)

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
    else:
        bot.answer_callback_query(call.id, "Índice de página inválido.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('submenu_'))
def callback_submenu(call):
    _, subcategoria, submenu_selecionado = call.data.split('_')
    conn, cursor = conectar_banco_dados()
    try:
        cartas_disponiveis = obter_cartas_por_subcategoria_e_submenu(subcategoria, submenu_selecionado, cursor)
        if cartas_disponiveis:
            carta_aleatoria = random.choice(cartas_disponiveis)
            if carta_aleatoria:
                id_personagem_carta, emoji, nome, imagem = carta_aleatoria
                send_card_message(call.message, emoji, id_personagem_carta, nome, subcategoria, imagem)
                qnt_carta(call.message.chat.id)
            else:
                bot.send_message(call.message.chat.id, "Nenhuma carta disponível para esta combinação de subcategoria e submenu.")
        else:
            bot.send_message(call.message.chat.id, "Nenhuma carta disponível para esta combinação de subcategoria e submenu.")
    finally:
        cursor.close()
        conn.close()       

@bot.callback_query_handler(func=lambda call: call.data == "add_note")
def handle_add_note_callback(call):
    markup = telebot.types.InlineKeyboardMarkup()
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Por favor, envie sua anotação para o diário.", reply_markup=markup)
    bot.register_next_step_handler(call.message, receive_note)

@bot.callback_query_handler(func=lambda call: call.data == "cancel_note")
def handle_cancel_note_callback(call):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Tudo bem, até amanhã!")
@bot.callback_query_handler(func=lambda call: call.data.startswith('help_'))
def callback_help(call):
    if call.data == 'help_cartas':
        help_text = (
            "<b>Aqui estão os comandos relacionados a Cartas:</b>\n\n"
            "<b>/armazem, /armazém, /amz </b> - Olhe os peixes (cartas) que você possui.\n"
            "<b>" 
        )
    elif call.data == 'help_trocas':
        help_text = "Aqui estão os comandos relacionados a Trocas:\n\n"

        help_text += "/troca - Comando de troca (detalhes do comando de troca).\n"
    elif call.data == 'help_eventos':
        help_text = "Aqui estão os comandos relacionados a Eventos:\n\n"

        help_text += "<b>/evento (f ou s para faltantes ou possuidos) </b>- Comando ver os peixes de eventos. ex: /evento s amor. \n"

    elif call.data == 'help_bugs':
        help_text = "Aqui estão os comandos relacionados a Usuários:\n\n"

        help_text += ("/setuser - Comando para definir seu usuário. ex: /setuser maria\n"
                      "/setfav - Comando para definir seu peixe favorito, que aparece no seu armazem e perfil. ex: /setfav 10150"
                      "/removefav - Comando para remover seu peixe favorito. ex: /removefav 10150"
                      )
    elif call.data == 'help_tudo':
        help_text = (
            "Aqui estão todos os comandos disponíveis:\n\n"
            "/armazem, /armazém, /amz - Olhe os peixes (cartas) que você possui.\n"
            "/evento evento <subcategoria> - Comando para interagir com eventos. Use /evento s para subcategoria e /evento f para favoritos.\n"
            "/troca - Comando de troca (detalhes do comando de troca).\n"
            "/reportar_bug - Comando para reportar bugs.\n"
        )
    
    bot.edit_message_text(help_text, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="HTML")

@bot.message_handler(commands=['delcards'])
def delcards_command(message):
    try:
        if message.from_user.id != 5532809878 and message.from_user.id != 1805086442:
            bot.reply_to(message, "Você não é a Hashi ou a Skar para usar esse comando.")
            return
        args = message.text.split()
        if len(args) != 4:
            bot.reply_to(message, "Uso correto: /delcards {id} {quantidade} {id_usuario}")
            return

        id_carta = int(args[1])
        quantidade = int(args[2])
        id_usuario = int(args[3])

        conn, cursor = conectar_banco_dados()
        cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (id_usuario, id_carta))
        resultado = cursor.fetchone()

        if resultado:
            quantidade_atual = resultado[0]
            if quantidade_atual >= quantidade:
                nova_quantidade = quantidade_atual - quantidade

                if nova_quantidade == 0:
                    cursor.execute("DELETE FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (id_usuario, id_carta))
                else:
                    cursor.execute("UPDATE inventario SET quantidade = %s WHERE id_usuario = %s AND id_personagem = %s", (nova_quantidade, id_usuario, id_carta))

                conn.commit()
                bot.reply_to(message, f"{quantidade} unidades da carta {id_carta} foram removidas do inventário do usuário {id_usuario}.")
            else:
                bot.reply_to(message, f"O usuário {id_usuario} não possui {quantidade} unidades da carta {id_carta}.")
        else:
            bot.reply_to(message, f"A carta {id_carta} não foi encontrada no inventário do usuário {id_usuario}.")

    except Exception as e:
        print(f"Erro ao deletar cartas do inventário: {e}")
        bot.reply_to(message, "Ocorreu um erro ao deletar as cartas do inventário.")

@bot.message_handler(commands=['verificar'])
def verificar_ids(message):
    try:
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
            resposta += f"{id_personagem} — {nome}: {quantidade}x\n"

        max_chars = 4096  
        partes = [resposta[i:i + max_chars] for i in range(0, len(resposta), max_chars)]
        for parte in partes:
            bot.send_message(message.chat.id, parte, reply_to_message_id=message.message_id)

    except Exception as e:
        print(f"Erro ao verificar IDs: {e}")
        bot.reply_to(message, "Ocorreu um erro ao verificar os IDs.")
        
@bot.message_handler(commands=['doar'])
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

            if not destinatario_id:
                bot.send_message(chat_id, "Você precisa responder a uma mensagem para doar a carta.")
                return

            nome_carta = obter_nome(minhacarta)
            qnt_str = f"uma unidade da carta" if quantidade == 1 else f"{quantidade} unidades da carta"
            texto = f"Olá, {message.from_user.first_name}!\n\nVocê tem {qnt_carta} unidades da carta: {minhacarta} — {nome_carta}.\n\n"
            texto += f"Deseja doar {qnt_str} para {nome_destinatario}?"

            keyboard = telebot.types.InlineKeyboardMarkup()
            keyboard.row(
                telebot.types.InlineKeyboardButton(text="Sim", callback_data=f'cdoacao_{eu}_{minhacarta}_{destinatario_id}_{quantidade}'),
                telebot.types.InlineKeyboardButton(text="Não", callback_data=f'ccancelar_{eu}')
            )

            bot.send_message(chat_id, texto, reply_markup=keyboard)
        else:
            bot.send_message(chat_id, "Você não pode doar uma carta que não possui.")

    except Exception as e:
        print(f"Erro durante o comando de doação: {e}")
        
@bot.message_handler(commands=['rep'])
def ver_repetidos_evento(message):
    try:
        id_usuario = message.from_user.id
        user = message.from_user
        nome_usuario = user.first_name
        comando_parts = message.text.split()
        if len(comando_parts) != 2:
            bot.send_message(message.chat.id, "Por favor, use o formato: /rep <nomedoevento>")
            return
        evento = comando_parts[1].lower()
        
        eventos_validos = ['inverno', 'amor', 'aniversario', 'fixo']
        if evento not in eventos_validos:
            bot.send_message(message.chat.id, f"O evento '{evento}' não existe. Por favor, use um dos seguintes: {', '.join(eventos_validos)}")
            return
        
        conn, cursor = conectar_banco_dados()
        cursor.execute("""
            SELECT inv.id_personagem, ev.nome, ev.subcategoria, inv.quantidade 
            FROM inventario inv
            JOIN evento ev ON inv.id_personagem = ev.id_personagem
            WHERE inv.id_usuario = %s AND ev.evento = %s AND inv.quantidade > 1
        """, (id_usuario, evento))
        
        cartas_repetidas = cursor.fetchall()

        if not cartas_repetidas:
            bot.send_message(message.chat.id, f"Você não possui cartas repetidas do evento '{evento}'.")
            return

        globals.user_event_data[message.message_id] = {
            'id_usuario': id_usuario,
            'nome_usuario': nome_usuario,
            'evento': evento,
            'cartas_repetidas': cartas_repetidas
        }

        total_paginas = (len(cartas_repetidas) // 20) + (1 if len(cartas_repetidas) % 20 > 0 else 0)
        resposta_inicial = "Gerando relatório de cartas repetidas, por favor aguarde..."
        mensagem = bot.send_message(message.chat.id, resposta_inicial)
        mostrar_repetidas_evento(mensagem.chat.id, nome_usuario, evento, cartas_repetidas, 1, total_paginas, mensagem.message_id, message.message_id)

    except mysql.connector.Error as err:
        bot.send_message(message.chat.id, f"Erro ao buscar cartas repetidas do evento: {err}")
    finally:
        fechar_conexao(cursor, conn)

@bot.callback_query_handler(func=lambda call: call.data.startswith('rep_'))
def callback_repetidas_evento(call):
    try:
        data_parts = call.data.split('_')
        action = data_parts[1]
        original_message_id = int(data_parts[2])
        pagina_atual = int(data_parts[3])

        if original_message_id not in globals.user_event_data:
            bot.send_message(call.message.chat.id, "Dados do evento não encontrados.")
            return

        dados_evento = globals.user_event_data[original_message_id]
        id_usuario = dados_evento['id_usuario']
        nome_usuario = dados_evento['nome_usuario']
        evento = dados_evento['evento']
        cartas_repetidas = dados_evento['cartas_repetidas']

        total_paginas = (len(cartas_repetidas) // 20) + (1 if len(cartas_repetidas) % 20 > 0 else 0)
        
        if action == "prev":
            pagina_atual -= 1
        elif action == "next":
            pagina_atual += 1

        mostrar_repetidas_evento(call.message.chat.id, nome_usuario, evento, cartas_repetidas, pagina_atual, total_paginas, call.message.message_id, original_message_id)
    
    except mysql.connector.Error as err:
        bot.send_message(call.message.chat.id, f"Erro ao buscar cartas repetidas do evento: {err}")
    finally:
        fechar_conexao(cursor, conn)

@bot.message_handler(commands=['progresso'])
def progresso_evento(message):
    try:
        id_usuario = message.from_user.id
        user = message.from_user
        nome_usuario = user.first_name

        comando_parts = message.text.split()
        if len(comando_parts) != 2:
            bot.send_message(message.chat.id, "Por favor, use o formato: /progresso <nomedoevento>")
            return

        evento = comando_parts[1].lower()
        
        eventos_validos = ['inverno', 'amor', 'aniversario', 'fixo']
        if evento not in eventos_validos:
            bot.send_message(message.chat.id, f"O evento '{evento}' não existe. Por favor, use um dos seguintes: {', '.join(eventos_validos)}")
            return
        
        conn, cursor = conectar_banco_dados()

        progresso_mensagem = calcular_progresso_evento(cursor, id_usuario, evento)
        
        resposta = f"Progresso de {nome_usuario} no evento {evento.capitalize()}:\n\n" + progresso_mensagem
        bot.send_message(message.chat.id, resposta)

    except mysql.connector.Error as err:
        bot.send_message(message.chat.id, f"Erro ao buscar progresso do evento: {err}")
    finally:
        fechar_conexao(cursor, conn)


@bot.callback_query_handler(func=lambda call: call.data.startswith("submenus_"))
def callback_submenus(call):
    try:
        parts = call.data.split('_')
        pagina = int(parts[1])
        subcategoria = parts[2]

        conn, cursor = conectar_banco_dados()
        query_total = "SELECT COUNT(DISTINCT submenu) FROM personagens WHERE subcategoria = %s"
        cursor.execute(query_total, (subcategoria,))
        total_registros = cursor.fetchone()[0]
        total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)

        editar_mensagem_submenus(call, subcategoria, pagina, total_paginas)

    except Exception as e:
        print(f"Erro ao processar callback de página para submenus: {e}")
        
@bot.callback_query_handler(func=lambda call: call.data.startswith("especies_"))
def callback_especies(call):
    try:
        parts = call.data.split('_')
        pagina = int(parts[1])
        categoria = parts[2]

        conn, cursor = conectar_banco_dados()
        query_total = "SELECT COUNT(DISTINCT subcategoria) FROM personagens WHERE categoria = %s"
        cursor.execute(query_total, (categoria,))
        total_registros = cursor.fetchone()[0]
        total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)

        editar_mensagem_especies(call, categoria, pagina, total_paginas)

    except Exception as e:
        print(f"Erro ao processar callback de página para espécies: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('poço_dos_desejos'))
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

@bot.callback_query_handler(func=lambda call: call.data.startswith('fazer_pedido'))
def handle_fazer_pedido(call):
    image_url = "https://telegra.ph/file/94c9c66af4ca4d6f0a3e5.jpg"
    caption = "<b>⛲: Para pedir os seus peixes é simples!</b> \n\nMe envie até <b>5 IDs</b> dos peixes e a quantidade de cenouras que você quer doar \n(eu aceito qualquer quantidade entre 10 e 20 cenouras...) \n\n<i>exemplo: ID1 ID2 ID3 ID4 ID5 cenouras</i>"
    media = InputMediaPhoto(image_url, caption=caption, parse_mode="HTML")
    bot.edit_message_media(media, chat_id=call.message.chat.id, message_id=call.message.message_id)
    bot.register_next_step_handler(call.message, process_wish)



@bot.message_handler(commands=['trintadas', 'abelhadas', 'abelhas'])
def handle_trintadas(message):
    enviar_mensagem_trintadas(message, pagina_atual=1)

@bot.callback_query_handler(func=lambda call: call.data.startswith('trintadas_'))
def callback_trintadas(call):
    data = call.data.split('_')
    user_id_inicial = int(data[1])
    pagina_atual = int(data[2])
    nome_usuario_inicial = data[3]
    editar_mensagem_trintadas(call, user_id_inicial, pagina_atual, nome_usuario_inicial)

@bot.callback_query_handler(func=lambda call: call.data.startswith('fazer_pedido'))
def handle_fazer_pedido(call):
    image_url = "https://telegra.ph/file/94c9c66af4ca4d6f0a3e5.jpg"
    caption = "<b>⛲: Para pedir os seus peixes é simples!</b> \n\nMe envie até <b>5 IDs</b> dos peixes e a quantidade de cenouras que você quer doar \n(eu aceito qualquer quantidade entre 10 e 20 cenouras...) \n\n<i>exemplo: ID1 ID2 ID3 ID4 ID5 cenouras</i>"
    media = InputMediaPhoto(image_url, caption=caption, parse_mode="HTML")
    bot.edit_message_media(media, chat_id=call.message.chat.id, message_id=call.message.message_id)
    bot.register_next_step_handler(call.message, process_wish)
@bot.callback_query_handler(func=lambda call: call.data.startswith('notificar_'))
def callback_handler(call):
    try:
        id_personagem = int(call.data.split('_')[1])
        conn, cursor = conectar_banco_dados()
        cursor.execute("SELECT rodados FROM cartas WHERE id_personagem = %s", (id_personagem,))
        quantidade_personagem = cursor.fetchone()

        if quantidade_personagem is not None and quantidade_personagem[0] >= 0:
            bot.answer_callback_query(call.id, f"Esta carta foi rodada {quantidade_personagem[0]} vezes!")
        else:
            bot.answer_callback_query(call.id, f"Esta carta não foi rodada ainda :(!")
            bot.answer_callback_query(call.id, "Erro ao obter a quantidade da carta.")
    except Exception as e:
        print(f"Erro ao lidar com o callback: {e}")
    finally:
        fechar_conexao(cursor, conn)
@bot.callback_query_handler(func=lambda call: call.data.startswith(('next_button', 'prev_button')))
def navigate_messages(call):
    try:
        chat_id = call.message.chat.id
        data_parts = call.data.split('_')

        if len(data_parts) == 4 and data_parts[0] in ('next', 'prev'):
            direction, current_index, total_count = data_parts[0], int(data_parts[2]), int(data_parts[3])
        else:
            raise ValueError("Callback_data com número incorreto de partes ou formato inválido.")

        user_id = call.from_user.id
        mensagens, _ = load_user_state(user_id, 'gnomes')
        if direction == 'next':
            current_index += 1
        elif direction == 'prev':
            current_index -= 1
        media_url, mensagem = mensagens[current_index]
        markup = create_navigation_markup(current_index, len(mensagens))

        if media_url:
            if media_url.lower().endswith(".gif"):
                bot.edit_message_media(chat_id=chat_id, message_id=call.message.message_id, media=telebot.types.InputMediaAnimation(media=media_url, caption=mensagem, parse_mode="HTML"), reply_markup=markup)
            elif media_url.lower().endswith(".mp4"):
                bot.edit_message_media(chat_id=chat_id, message_id=call.message.message_id, media=telebot.types.InputMediaVideo(media=media_url, caption=mensagem, parse_mode="HTML"), reply_markup=markup)
            elif media_url.lower().endswith((".jpeg", ".jpg", ".png")):
                bot.edit_message_media(chat_id=chat_id, message_id=call.message.message_id, media=telebot.types.InputMediaPhoto(media=media_url, caption=mensagem, parse_mode="HTML"), reply_markup=markup)
            else:
                bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=mensagem, reply_markup=markup, parse_mode="HTML")
        else:
            bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=mensagem, reply_markup=markup, parse_mode="HTML")

    except Exception as e:
        print("Erro ao processar callback dos botões de navegação:", str(e))

@bot.callback_query_handler(func=lambda call: call.data.startswith(('prox_button', 'ant_button')))
def navigate_gnome_results(call):
    try:
        chat_id = call.message.chat.id
        data_parts = call.data.split('_')

        if len(data_parts) == 4 and data_parts[0] in ('prox', 'ant'):
            direction, current_page, total_pages = data_parts[0], int(data_parts[2]), int(data_parts[3])
        else:
            raise ValueError("Callback_data com número incorreto de partes ou formato inválido.")

        user_id = call.from_user.id
        resultados, _, message_id = globals.load_state(user_id, 'gnomes')
        if direction == 'prox':
            current_page = min(current_page + 1, total_pages)
        elif direction == 'ant':
            current_page = max(current_page - 1, 1)
            
        resultados_pagina_atual = resultados[(current_page - 1) * 15 : current_page * 15]
        lista_resultados = [f"{emoji} - {id_personagem} - {nome} de {subcategoria}" for emoji, id_personagem, nome, subcategoria in resultados_pagina_atual]
        mensagem_final = f"🐠 Peixes de nome', página {current_page}/{total_pages}:\n\n" + "\n".join(lista_resultados)
        markup = create_navegacao_markup(current_page, total_pages)

        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=mensagem_final, reply_markup=markup)

    except Exception as e:
        print("Erro ao processar callback dos botões de navegação:", str(e))

@bot.callback_query_handler(func=lambda call: call.data.startswith("cesta_"))
def callback_query_cesta(call):
    global processing_lock

    if not processing_lock.acquire(blocking=False):
        return

    try:
        parts = call.data.split('_')
        tipo = parts[1]
        pagina = int(parts[2])
        categoria = parts[3]
        id_usuario_original = int(parts[4])
        nome_usuario = bot.get_chat(id_usuario_original).first_name

        if tipo == 's':
            ids_personagens = obter_ids_personagens_inventario(id_usuario_original, categoria)
            ids_personagens_evento = obter_ids_personagens_evento(id_usuario_original, categoria, incluir=False)
            ids_personagens.extend(ids_personagens_evento)
            total_personagens_subcategoria = obter_total_personagens_subcategoria(categoria)
            total_registros = len(ids_personagens)

            if total_registros > 0:
                total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)
                mostrar_pagina_cesta_s(call.message, categoria, id_usuario_original, pagina, total_paginas, ids_personagens, total_personagens_subcategoria, nome_usuario, call=call)
            else:
                bot.reply_to(call.message, f"Nenhum personagem encontrado na cesta '{categoria}'.")

        elif tipo == 'f':
            ids_personagens_faltantes = obter_ids_personagens_faltantes(id_usuario_original, categoria)
            ids_personagens_evento = obter_ids_personagens_evento(id_usuario_original, categoria, incluir=True)
            ids_personagens_faltantes.extend(ids_personagens_evento)
            total_personagens_subcategoria = obter_total_personagens_subcategoria(categoria)
            total_registros = len(ids_personagens_faltantes)

            if total_registros > 0:
                total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)
                mostrar_pagina_cesta_f(call.message, categoria, id_usuario_original, pagina, total_paginas, ids_personagens_faltantes, total_personagens_subcategoria, nome_usuario, call=call)
            else:
                bot.reply_to(call.message, f"Todos os personagens na subcategoria '{categoria}' estão no seu inventário.")

        elif tipo == 'c':
            ids_personagens = obter_ids_personagens_categoria(id_usuario_original, categoria)
            total_personagens_categoria = obter_total_personagens_categoria(categoria)
            total_registros = len(ids_personagens)

            if total_registros > 0:
                total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)
                mostrar_pagina_cesta_c(call.message, categoria, id_usuario_original, pagina, total_paginas, ids_personagens, total_personagens_categoria, nome_usuario, call=call)
            else:
                bot.reply_to(call.message, f"Nenhum personagem encontrado na categoria '{categoria}'.")

        elif tipo == 'cf':
            ids_personagens_faltantes = obter_ids_personagens_faltantes_categoria(id_usuario_original, categoria)
            total_personagens_categoria = obter_total_personagens_categoria(categoria)
            total_registros = len(ids_personagens_faltantes)

            if total_registros > 0:
                total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)
                mostrar_pagina_cesta_cf(call.message, categoria, id_usuario_original, pagina, total_paginas, ids_personagens_faltantes, total_personagens_categoria, nome_usuario, call=call)
            else:
                bot.reply_to(call.message, f"Você possui todos os personagens na categoria '{categoria}'.")

        elif tipo == 'se':
            ids_personagens = obter_ids_personagens_inventario(id_usuario_original, categoria)
            ids_personagens_evento = obter_ids_personagens_evento(id_usuario_original, categoria, incluir=True)
            ids_personagens.extend(ids_personagens_evento)
            total_personagens_evento = len(ids_personagens_evento)
            total_personagens_com_evento = obter_total_personagens_subcategoria(categoria) + total_personagens_evento
            total_registros = len(ids_personagens)

            if total_registros > 0:
                total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)
                mostrar_pagina_cesta_s(call.message, categoria, id_usuario_original, pagina, total_paginas, ids_personagens, total_personagens_com_evento, nome_usuario, call=call)
            else:
                bot.reply_to(call.message, f"Nenhum personagem encontrado na cesta '{categoria}'.")

        elif tipo == 'fe':
            ids_personagens_faltantes = obter_ids_personagens_faltantes(id_usuario_original, categoria)
            ids_personagens_evento = obter_ids_personagens_evento(id_usuario_original, categoria, incluir=True)
            ids_personagens_faltantes.extend(ids_personagens_evento)
            total_personagens_subcategoria = obter_total_personagens_subcategoria(categoria)
            total_registros = len(ids_personagens_faltantes)

            if total_registros > 0:
                total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)
                mostrar_pagina_cesta_f(call.message, categoria, id_usuario_original, pagina, total_paginas, ids_personagens_faltantes, total_personagens_subcategoria, nome_usuario, call=call)
            else:
                bot.reply_to(call.message, f"Todos os personagens na subcategoria '{categoria}' estão no seu inventário.")

    except Exception as e:
        print(f"Erro ao processar callback da cesta: {e}")
    finally:
        processing_lock.release()
        
@bot.callback_query_handler(func=lambda call: call.data.startswith('total_'))
def callback_total_personagem(call):
    try:
        conn, cursor = conectar_banco_dados()
        chat_id = call.message.chat.id
        id_pesquisa = call.data.split('_')[1]

        sql_total = "SELECT total FROM personagens WHERE id_personagem = %s"
        cursor.execute(sql_total, (id_pesquisa,))
        total_pescados = cursor.fetchone()

        if total_pescados is not None and total_pescados[0] is not None:
            if total_pescados[0] > 1:
                response_text = f"O personagem foi pescado {total_pescados[0]} vezes!"
            elif total_pescados[0] == 1:
                response_text = f"O personagem foi pescado {total_pescados[0]} vez!"
            else:
                response_text = "Esse personagem ainda não foi pescado :("
        else:
            response_text = "Esse personagem ainda não foi pescado :("

        try:
            bot.answer_callback_query(call.id, text=response_text, show_alert=True)
        except Exception as e:
            traceback.print_exc()
            erro = traceback.format_exc()
            mensagem = f"Alerta de erro carta pescadas. Erro: {e}\n{erro}"
            bot.send_message(grupodeerro, mensagem, parse_mode="HTML")

    except Exception as e:
        traceback.print_exc()
        erro = traceback.format_exc()
        mensagem = f"Alerta de erro carta pescadas. Erro: {e}\n{erro}"
        bot.send_message(grupodeerro, mensagem, parse_mode="HTML")


    finally:
        cursor.close()
        conn.close()


@bot.callback_query_handler(func=lambda call: call.data.startswith(('armazem_anterior_', 'armazem_proxima_','armazem_ultima_','armazem_primeira_')))
def callback_paginacao_armazem(call):
    try:
        conn, cursor = conectar_banco_dados()
        chat_id = call.message.chat.id
        _, direcao, pagina_str, id_usuario = call.data.split('_')
        pagina = int(pagina_str)
        info_armazem = globals.armazem_info.get(int(id_usuario), {})
        id_usuario = info_armazem.get('id_usuario', '')
        usuario = info_armazem.get('usuario', '')
        resultados_por_pagina = 15
        offset = (pagina - 1) * resultados_por_pagina

        quantidade_total_cartas = obter_quantidade_total_cartas(id_usuario)
        total_paginas = quantidade_total_cartas // resultados_por_pagina + 1
        limite = resultados_por_pagina

        if pagina == 1 and call.data.startswith("armazem_anterior_"):
            pagina = total_paginas
            offset = (pagina - 1) * resultados_por_pagina
            limite = quantidade_total_cartas % resultados_por_pagina or resultados_por_pagina

        elif pagina == total_paginas and call.data.startswith("armazem_proxima_"):
            pagina = 1
            offset = 0
            limite = min(quantidade_total_cartas, resultados_por_pagina)

        else:
            if call.data.startswith("armazem_anterior_"):

                pagina -= 1
            elif call.data.startswith("armazem_ultima_"):

                pagina += 5 
            elif call.data.startswith("armazem_primeira_"):

                pagina -= 5
            elif call.data.startswith("armazem_proxima_"):

                pagina += 1
            offset = (pagina - 1) * resultados_por_pagina

            
        sql = f"""
            SELECT id_personagem, emoji, nome_personagem, subcategoria, quantidade, categoria, evento
            FROM (
                SELECT i.id_personagem, p.emoji, p.nome AS nome_personagem, p.subcategoria, i.quantidade, p.categoria, '' AS evento
                FROM inventario i
                JOIN personagens p ON i.id_personagem = p.id_personagem
                WHERE i.id_usuario = {id_usuario} AND i.quantidade > 0

                UNION

                SELECT e.id_personagem, e.emoji, e.nome AS nome_personagem, e.subcategoria, 0 AS quantidade, e.categoria, e.evento
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
            LIMIT {limite} OFFSET {offset}
        """
        cursor.execute(sql)
        resultados = cursor.fetchall()
        if resultados:
            markup = telebot.types.InlineKeyboardMarkup()
            if quantidade_total_cartas > 10:
                buttons_row = [
                    telebot.types.InlineKeyboardButton("⏪️", callback_data=f"armazem_primeira_{pagina}_{id_usuario}"),
                    telebot.types.InlineKeyboardButton("◀️", callback_data=f"armazem_anterior_{pagina}_{id_usuario}"),
                    telebot.types.InlineKeyboardButton("▶️", callback_data=f"armazem_proxima_{pagina}_{id_usuario}"),
                    telebot.types.InlineKeyboardButton("⏩️", callback_data=f"armazem_ultima_{pagina}_{id_usuario}")
                ]
                markup.row(*buttons_row)

            id_fav_usuario, emoji_fav, nome_fav, imagem_fav = obter_favorito(id_usuario)

            if id_fav_usuario is not None:
                resposta = f"💌 | Cartas no armazém de {usuario}:\n\nFav: {emoji_fav} {id_fav_usuario} — {nome_fav}\n\n"

            for carta in resultados:
                id_carta = carta[0]
                emoji_carta = carta[1]
                nome_carta = carta[2]
                subcategoria_carta = carta[3]
                quantidade_carta = carta[4]
                categoria_carta = carta[5]
                evento_carta = carta[6]

                if quantidade_carta is None:
                    quantidade_carta = 0
                else:
                    quantidade_carta = int(quantidade_carta)

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
                elif 50 <= quantidade_carta <= 100:
                    letra_quantidade = "👑"
                elif 101 <= quantidade_carta:
                    letra_quantidade = "👑"    
                else:
                    letra_quantidade = ""

                repetida = " [+]" if quantidade_carta > 1 and categoria_carta == 'evento' else ""

                resposta += f" {emoji_carta} <code>{id_carta}</code> • {nome_carta} - {subcategoria_carta} {letra_quantidade}{repetida}\n"

            resposta += f"\n{pagina}/{total_paginas}"
            bot.edit_message_caption(chat_id=chat_id, message_id=call.message.message_id, caption=resposta, reply_markup=markup, parse_mode="HTML")

        else:
            bot.answer_callback_query(callback_query_id=call.id, text="Nenhuma carta encontrada.")
    except mysql.connector.Error as err:
        print(f"Erro de SQL: {err}")
    finally:
        fechar_conexao(cursor, conn)

@bot.callback_query_handler(func=lambda call: call.data.startswith('subcategory_'))
def callback_subcategory(call):
    try:
        subcategory_data = call.data.split("_")
        subcategory = subcategory_data[1]
        card = get_random_card_valentine(subcategory)
        if card:
            evento_aleatorio = card
            send_card_message(call.message, evento_aleatorio)
        else:
            bot.answer_callback_query(call.id, "Ocorreu um erro ao processar sua solicitação. Tente novamente mais tarde.")
    except Exception as e:
        print(f"Erro ao processar callback de subcategoria: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('cenourar_sim_'))
def callback_cenourar(call):
    try:
        data_parts = call.data.split("_")
        acao = data_parts[1]
        id_usuario = int(data_parts[2])
        id_personagem = data_parts[3] if len(data_parts) > 3 else ""

        if acao == "sim":
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(processar_cenourar_carta, call, id_usuario, id_personagem)
                future.result()
        elif acao == "nao":
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Operação de cenoura cancelada.")
    except Exception as e:
        print(f"Erro ao processar callback de cenoura: {e}")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Erro ao processar a cenoura.")

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

@bot.callback_query_handler(func=lambda call: call.data.startswith('loja_compras'))
def callback_loja_compras(call):
    try:
        message_data = call.data.replace('loja_', '')
        if message_data:
            conn, cursor = conectar_banco_dados()
            id_usuario = call.from_user.id
            cursor.execute("SELECT cenouras FROM usuarios WHERE id_usuario = %s", (id_usuario,))
            result = cursor.fetchone()

            imagem_url = 'https://telegra.ph/file/a4c194082eab84886cbd4.jpg'
            original_message_id = call.message.message_id

            keyboard = telebot.types.InlineKeyboardMarkup()
            primeira_coluna = [
                telebot.types.InlineKeyboardButton(text="🐟 Comprar Iscas", callback_data='compras_iscas_callback')
            ]
            segunda_coluna = [
                telebot.types.InlineKeyboardButton(text="🥕 Doar Cenouras", callback_data=f'doar_cenoura_{id_usuario}_{original_message_id}')
            ]
            keyboard.row(*primeira_coluna)
            keyboard.row(*segunda_coluna)

            if result:
                qnt_cenouras = int(result[0])
            else:
                qnt_cenouras = 0

            mensagem = f"🐇 Bem vindo a nossa lojinha. O que você quer levar?\n\n🥕 Saldo Atual: {qnt_cenouras}"
            bot.edit_message_caption(chat_id=call.message.chat.id, message_id=original_message_id, caption=mensagem, reply_markup=keyboard)
        else:
            bot.reply_to(call.message, "Erro ao processar comando.")
    except Exception as e:
        print(f"Erro ao processar comando: {e}")
    finally:
        cursor.close()
        conn.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith('compras_iscas_'))
def callback_compras_iscas(call):
    try:
        compras_iscas_callback(call)
    except Exception as e:
        print(f"Erro ao processar callback de compras iscas: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('tcancelar'))
def callback_tcancelar(call):
    try:
        data = call.data.split('_')
        destinatario_id = int(data[1])
        if destinatario_id == call.from_user.id:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(callback_query_id=call.id, text="Você não pode aceitar esta doação.")
    except Exception as e:
        print(f"Erro ao processar callback de cancelar: {e}")

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
    try:
        message_data = call.data.replace('loja_', '')
        if message_data == "loja":
            data_atual = datetime.today().strftime("%Y-%m-%d")
            id_usuario = call.from_user.id
            ids_do_dia = obter_ids_loja_do_dia(data_atual)
            imagem_url = 'https://telegra.ph/file/a60b21f603ad26eb8608a.jpg'
            original_message_id = call.message.message_id
            keyboard = telebot.types.InlineKeyboardMarkup()
            primeira_coluna = [
                telebot.types.InlineKeyboardButton(text="☁️", callback_data=f'compra_musica_{id_usuario}_{original_message_id}'),
                telebot.types.InlineKeyboardButton(text="🍄", callback_data=f'compra_series_{id_usuario}_{original_message_id}'),
                telebot.types.InlineKeyboardButton(text="🍰", callback_data=f'compra_filmes_{id_usuario}_{original_message_id}')
            ]
            segunda_coluna = [
                telebot.types.InlineKeyboardButton(text="🍂", callback_data=f'compra_miscelanea_{id_usuario}_{original_message_id}'),
                telebot.types.InlineKeyboardButton(text="🧶", callback_data=f'compra_jogos_{id_usuario}_{original_message_id}'),
                telebot.types.InlineKeyboardButton(text="🌷", callback_data=f'compra_animanga_{id_usuario}_{original_message_id}')
            ]
            keyboard.row(*primeira_coluna)
            keyboard.row(*segunda_coluna)

            mensagem = "𝐀𝐡, 𝐨𝐥𝐚́! 𝐕𝐨𝐜𝐞̂ 𝐜𝐡𝐞𝐠𝐨𝐮 𝐧𝐚 𝐡𝐨𝐫𝐚 𝐜𝐞𝐫𝐭𝐚! \n\nNosso pescador acabou de chegar com os peixes fresquinhos de hoje:\n\n"

            for carta_id in ids_do_dia:
                id_personagem, emoji, nome, subcategoria = obter_informacoes_carta(carta_id)
                mensagem += f"{emoji} - {nome} de {subcategoria}\n"

            bot.edit_message_media(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=keyboard,
                media=telebot.types.InputMediaPhoto(media=imagem_url, caption=mensagem)
            )
    except Exception as e:
        print(f"Erro ao processar loja_loja_callback: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('compra_'))
def callback_compra(call):
    try:
        chat_id = call.message.chat.id
        parts = call.data.split('_')
        categoria = parts[1]
        id_usuario = parts[2]
        original_message_id = parts[3]
        conn, cursor = conectar_banco_dados()
        cursor.execute("SELECT cenouras FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        result = cursor.fetchone()

        if result:
            qnt_cenouras = int(result[0])
        else:
            qnt_cenouras = 0

        if qnt_cenouras >= 5:
            cursor.execute(
                "SELECT loja.id_personagem, personagens.nome, personagens.subcategoria, personagens.emoji "
                "FROM loja "
                "JOIN personagens ON loja.id_personagem = personagens.id_personagem "
                "WHERE loja.categoria = %s AND loja.data = %s ORDER BY RAND() LIMIT 1",
                (categoria, datetime.today().strftime("%Y-%m-%d"))
            )
            carta_comprada = cursor.fetchone()

            if carta_comprada:
                id_personagem, nome, subcategoria, emoji = carta_comprada
                mensagem = f"Você tem {qnt_cenouras} cenouras. \nDeseja usar 5 para comprar o seguinte peixe: \n\n{emoji} {id_personagem} - {nome} \nde {subcategoria}?"
                keyboard = telebot.types.InlineKeyboardMarkup()
                keyboard.row(
                    telebot.types.InlineKeyboardButton(text="Sim", callback_data=f'confirmar_compra_{categoria}_{id_usuario}'),
                    telebot.types.InlineKeyboardButton(text="Não", callback_data='cancelar_compra')
                )
                imagem_url = "https://telegra.ph/file/d4d5d0af60ec66f35e29c.jpg"
                bot.edit_message_media(
                    chat_id=chat_id,
                    message_id=original_message_id,
                    reply_markup=keyboard,
                    media=telebot.types.InputMediaPhoto(media=imagem_url, caption=mensagem)
                )
            else:
                print(f"Nenhuma carta disponível para compra na categoria {categoria} hoje.")
        else:
            print("Usuário não tem cenouras suficientes para comprar.")
    except Exception as e:
        print(f"Erro ao processar a compra: {e}")
    finally:
        fechar_conexao(cursor, conn)

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirmar_compra_'))
def callback_confirmar_compra(call):
    try:
        parts = call.data.split('_')
        categoria = parts[2]
        id_usuario = parts[3]
        data_atual = datetime.today().strftime("%Y-%m-%d")
        conn, cursor = conectar_banco_dados()
        cursor.execute(
            "SELECT p.id_personagem, p.nome, p.subcategoria, p.imagem, p.emoji "
            "FROM loja AS l "
            "JOIN personagens AS p ON l.id_personagem = p.id_personagem "
            "WHERE l.categoria = %s AND l.data = %s ORDER BY RAND() LIMIT 1",
            (categoria, data_atual)
        )
        carta_comprada = cursor.fetchone()

        if carta_comprada:
            id_personagem, nome, subcategoria, imagem, emoji = carta_comprada
            mensagem = f"𝐂𝐨𝐦𝐩𝐫𝐚 𝐟𝐞𝐢𝐭𝐚 𝐜𝐨𝐦 𝐬𝐮𝐜𝐞𝐬𝐬𝐨! \n\nO seguinte peixe foi adicionado à sua cesta: \n\n{emoji} {id_personagem} • {nome}\nde {subcategoria}\n\n𝐕𝐨𝐥𝐭𝐞 𝐬𝐞𝐦𝐩𝐫𝐞!"
            add_to_inventory(id_usuario, id_personagem)
            diminuir_cenouras(id_usuario, 5)

            bot.edit_message_media(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                media=telebot.types.InputMediaPhoto(media=imagem, caption=mensagem)
            )
        else:
            print(f"Nenhuma carta disponível para compra na categoria {categoria} hoje.")
    except Exception as e:
        print(f"Erro ao processar a compra: {e}")
    finally:
        fechar_conexao(cursor, conn)
        
@bot.message_handler(commands=['setmusica'])
def set_musica_command(message):
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) == 2:
        link_spotify = command_parts[1].strip()
        id_usuario = message.from_user.id

        try:
            track_id = link_spotify.split("/")[-1].split("?")[0]
            track_info = sp.track(track_id)
            nome_musica = track_info['name']
            artista = track_info['artists'][0]['name']
            nova_musica = f"{nome_musica} - {artista}"

            atualizar_coluna_usuario(id_usuario, 'musica', nova_musica)
            bot.send_message(message.chat.id, f"Música atualizada para: {nova_musica}")
        except Exception as e:
            bot.send_message(message.chat.id, f"Erro ao processar o link do Spotify: {e}")
    else:
        bot.send_message(message.chat.id, "Formato incorreto. Use /setmusica seguido do link do Spotify, por exemplo: /setmusica https://open.spotify.com/track/xxxx.")

@bot.message_handler(commands=['evento'])
def evento_command(message):
    try:
        verificar_id_na_tabela(message.from_user.id, "ban", "iduser")
        conn, cursor = conectar_banco_dados()
        qnt_carta(message.from_user.id)
        id_usuario = message.from_user.id
        user = message.from_user
        usuario = user.first_name
        
        comando_parts = message.text.split('/evento ', 1)[1].strip().lower().split(' ')
        if len(comando_parts) >= 2:
            evento = comando_parts[1]
            subcategoria = ' '.join(comando_parts[1:])
        else:
            resposta = "Comando inválido. Use /evento <evento> <subcategoria>."
            bot.send_message(message.chat.id, resposta)
            return

        sql_evento_existente = f"SELECT DISTINCT evento FROM evento WHERE evento = '{evento}'"
        cursor.execute(sql_evento_existente)
        evento_existente = cursor.fetchone()
        if not evento_existente:
            resposta = f"Evento '{evento}' não encontrado na tabela de eventos."
            bot.send_message(message.chat.id, resposta)
            return

        if message.text.startswith('/evento s'):
            resposta_completa = comando_evento_s(id_usuario, evento, subcategoria, cursor, usuario)
        elif message.text.startswith('/evento f'):
            resposta_completa = comando_evento_f(id_usuario, evento, subcategoria, cursor, usuario)
        else:
            resposta = "Comando inválido. Use /evento s <evento> <subcategoria> ou /evento f <evento> <subcategoria>."
            bot.send_message(message.chat.id, resposta)
            return

        if isinstance(resposta_completa, tuple):
            subcategoria_pesquisada, lista, total_pages = resposta_completa
            resposta = f"{lista}\n\nPágina 1 de {total_pages}"

            markup = InlineKeyboardMarkup()
            if total_pages > 1:
                markup.add(InlineKeyboardButton("Próxima", callback_data=f"evt_next_{id_usuario}_{evento[:10]}_{subcategoria_pesquisada[:10]}_2"))

            bot.send_message(message.chat.id, resposta, reply_markup=markup)
        else:
            bot.send_message(message.chat.id, resposta_completa)
    except ValueError as e:
        print(f"Erro: {e}")
        mensagem_banido = "Você foi banido permanentemente do garden. Entre em contato com o suporte caso haja dúvidas."
        bot.send_message(message.chat.id, mensagem_banido)
    finally:
        fechar_conexao(cursor, conn)

@bot.callback_query_handler(func=lambda call: call.data.startswith("evt_"))
def callback_query_evento(call):
    data_parts = call.data.split('_')
    action = data_parts[1]
    id_usuario_inicial = int(data_parts[2])
    evento = data_parts[3]
    subcategoria = data_parts[4]
    page = int(data_parts[5])
    
    try:
        conn, cursor = conectar_banco_dados()

        if action == "prev":
            page -= 1
        elif action == "next":
            page += 1

        if call.message.text.startswith('🌾'):
            resposta_completa = comando_evento_s(id_usuario_inicial, evento, subcategoria, cursor, call.from_user.first_name, page)
        else:
            resposta_completa = comando_evento_f(id_usuario_inicial, evento, subcategoria, cursor, call.from_user.first_name, page)

        if isinstance(resposta_completa, tuple):
            subcategoria_pesquisada, lista, total_pages = resposta_completa
            resposta = f"{lista}\n\nPágina {page} de {total_pages}"

            markup = InlineKeyboardMarkup()
            if page > 1:
                markup.add(InlineKeyboardButton("Anterior", callback_data=f"evt_prev_{id_usuario_inicial}_{evento}_{subcategoria}_{page}"))
            if page < total_pages:
                markup.add(InlineKeyboardButton("Próxima", callback_data=f"evt_next_{id_usuario_inicial}_{evento}_{subcategoria}_{page}"))

            bot.edit_message_text(resposta, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
        else:
            bot.edit_message_text(resposta_completa, chat_id=call.message.chat.id, message_id=call.message.message_id)
    except mysql.connector.Error as err:
        bot.send_message(call.message.chat.id, f"Erro ao buscar perfil: {err}")
    finally:
        fechar_conexao(cursor, conn)

def obter_informacoes_loja(ids_do_dia):
    try:
        conn, cursor = conectar_banco_dados()
        placeholders = ', '.join(['%s' for _ in ids_do_dia])
        cursor.execute(
            f"SELECT id_personagem, emoji, nome, subcategoria FROM personagens WHERE id_personagem IN ({placeholders})",
            tuple(ids_do_dia))
        cartas_loja = cursor.fetchall()
        return cartas_loja

    except mysql.connector.Error as err:
        print(f"Erro ao obter informações da loja: {err}")
    finally:
        cursor.close()
        conn.close()

@bot.message_handler(commands=['help'])
def help_command(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("Cartas", callback_data="help_cartas"),
        telebot.types.InlineKeyboardButton("Trocas", callback_data="help_trocas")
    )
    markup.row(
        telebot.types.InlineKeyboardButton("Eventos", callback_data="help_eventos"),
        telebot.types.InlineKeyboardButton("Usuário", callback_data="help_bugs")
    )
    markup.row(
        telebot.types.InlineKeyboardButton("Outros", callback_data="help_tudo"),
        telebot.types.InlineKeyboardButton("Sobre o Beta", callback_data="help_beta")
    )
    
    markup.row(
        telebot.types.InlineKeyboardButton("⚠️ IMPORTANTE! ⚠️", callback_data="help_imp")
    )
    
    
    bot.send_message(message.chat.id, "Selecione uma categoria para obter ajuda:", reply_markup=markup)

@bot.message_handler(commands=['iduser'])
def handle_iduser_command(message):
    if message.reply_to_message:
        idusuario = message.reply_to_message.from_user.id
        bot.send_message(chat_id=message.chat.id, text=f"O ID do usuário é <code>{idusuario}</code>", reply_to_message_id=message.message_id,parse_mode="HTML")

@bot.message_handler(commands=['sair'])
def sair_grupo(message):
    try:
        id_grupo = message.text.split(' ', 1)[1]
        bot.leave_chat(id_grupo)
        bot.reply_to(message, f"O bot saiu do grupo com ID {id_grupo}.")

    except IndexError:
        bot.reply_to(message, "Por favor, forneça o ID do grupo após o comando, por exemplo: /sair 123456789.")

    except Exception as e:
        print(f"Erro ao processar comando /sair: {e}")
        bot.reply_to(message, "Ocorreu um erro ao processar sua solicitação.")

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

@bot.message_handler(commands=['setuser'])
def setuser_comando(message):
    command_parts = message.text.split()
    if len(command_parts) != 2:
        bot.send_message(message.chat.id, "Formato incorreto. Use /setuser seguido do user desejado, por exemplo: /setuser novouser.", reply_to_message_id=message.message_id)
        return

    nome_usuario = command_parts[1].strip()

    if not re.match("^[a-zA-Z0-9_]{1,20}$", nome_usuario):
        bot.send_message(message.chat.id, "Nome de usuário inválido. Use apenas letras, números e '_' e não ultrapasse 20 caracteres.", reply_to_message_id=message.message_id)
        return

    try:
        conn, cursor = conectar_banco_dados()
        cursor.execute("SELECT 1 FROM usuarios WHERE user = %s", (nome_usuario,))
        if cursor.fetchone():
            bot.send_message(message.chat.id, "O nome de usuário já está em uso. Escolha outro nome de usuário.", reply_to_message_id=message.message_id)
            return

        cursor.execute("SELECT 1 FROM usuarios_banidos WHERE id_usuario = %s", (nome_usuario,))
        if cursor.fetchone():
            bot.send_message(message.chat.id, "O nome de usuário já está em uso. Escolha outro nome de usuário.", reply_to_message_id=message.message_id)
            return

        cursor.execute("UPDATE usuarios SET user = %s WHERE id_usuario = %s", (nome_usuario, message.from_user.id))
        conn.commit()

        bot.send_message(message.chat.id, f"O nome de usuário foi alterado para '{nome_usuario}'.", reply_to_message_id=message.message_id)

    except mysql.connector.Error as err:
        bot.send_message(message.chat.id, f"Erro ao processar comando /setuser: {err}", reply_to_message_id=message.message_id)

    finally:
        fechar_conexao(cursor, conn)
     
@bot.message_handler(commands=['start'])
def start_comando(message):
    user_id = message.from_user.id
    nome_usuario = message.from_user.first_name  
    username = message.chat.username
    print(f"Comando /start recebido. ID do usuário: {user_id} - {nome_usuario}")

    try:
        verificar_id_na_tabela(user_id, "ban", "iduser")
        print("novo /start ",{user_id},"-",{nome_usuario},"-",{username})

        if verificar_id_na_tabelabeta(message.from_user.id):
            registrar_usuario(user_id, nome_usuario, username)
            registrar_valor("nome_usuario", nome_usuario, user_id)
            keyboard = telebot.types.InlineKeyboardMarkup()
            image_path = "jungk.jpg"
            with open(image_path, 'rb') as photo:
                bot.send_photo(message.chat.id, photo,
                               caption='Seja muito bem-vindo ao MabiGarden! Entre, busque uma sombra e aproveite a estadia.',
                               reply_markup=keyboard, reply_to_message_id=message.message_id)
        else:
            bot.send_message(message.chat.id, "Ei visitante, você não foi convidado! 😡", reply_to_message_id=message.message_id)

    except ValueError as e:
        print(f"Erro: {e}")
        mensagem_banido = "Você foi banido permanentemente do garden. Entre em contato com o suporte caso haja dúvidas."
        bot.send_message(message.chat.id, mensagem_banido, reply_to_message_id=message.message_id)
        
@bot.message_handler(commands=['removefav'])
def remove_fav_command(message):
    id_usuario = message.from_user.id

    conn, cursor = conectar_banco_dados()
    cursor.execute("UPDATE usuarios SET fav = NULL WHERE id_usuario = %s", (id_usuario,))
    conn.commit()

    bot.send_message(message.chat.id, "Favorito removido com sucesso.", reply_to_message_id=message.message_id)

           
@bot.message_handler(commands=['setfav'])
def set_fav_command(message):

    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) == 2 and command_parts[1].isdigit():
        id_personagem = int(command_parts[1])
        id_usuario = message.from_user.id
        nome_personagem = obter_nome(id_personagem)
        qtd_cartas = buscar_cartas_usuario(id_usuario, id_personagem)

        if qtd_cartas > 0:
            atualizar_coluna_usuario(id_usuario, 'fav', id_personagem)
            bot.send_message(message.chat.id, f"❤ {id_personagem} — {nome_personagem} definido como favorito.", reply_to_message_id=message.message_id)
        else:
            bot.send_message(message.chat.id, f"Você não possui {id_personagem} no seu inventário, que tal ir pescar?", reply_to_message_id=message.message_id)


@bot.message_handler(commands=['setnome'])
def set_nome_command(message):

    command_parts = message.text.split(maxsplit=1)

    if len(command_parts) == 2:
        novo_nome = command_parts[1]
        id_usuario = message.from_user.id
        atualizar_coluna_usuario(id_usuario, 'nome', novo_nome)
        bot.send_message(message.chat.id, f"Nome atualizado para: {novo_nome}", reply_to_message_id=message.message_id)
    else:
        bot.send_message(message.chat.id,
                         "Formato incorreto. Use /setnome seguido do novo nome, por exemplo: /setnome Manoela Gavassi", reply_to_message_id=message.message_id)

@bot.message_handler(commands=['usuario'])
def obter_username_por_comando(message):
    if len(message.text.split()) == 2 and message.text.split()[1].isdigit():
        user_id = int(message.text.split()[1])
        username = obter_username_por_id(user_id)
        bot.reply_to(message, username)
    else:
        bot.reply_to(message, "Formato incorreto. Use /usuario seguido do ID desejado, por exemplo: /usuario 123")

@bot.message_handler(commands=['eu'])
def me_command(message):
    id_usuario = message.from_user.id   
    query_verificar_usuario = "SELECT COUNT(*) FROM usuarios WHERE id_usuario = %s"

    try:
        conn, cursor = conectar_banco_dados()
        cursor.execute(query_verificar_usuario, (id_usuario,))
        usuario_existe = cursor.fetchone()[0]  

        if usuario_existe > 0: 
            qnt_carta(id_usuario)
            query_obter_perfil = """
                SELECT 
                    u.nome, u.nome_usuario, u.fav, u.adm, u.qntcartas, u.cenouras, u.iscas, u.bio, u.musica, u.pronome, u.privado, u.user, u.beta,
                    COALESCE(p.nome, e.nome) AS nome_fav, 
                    COALESCE(p.imagem, e.imagem) AS imagem_fav
                FROM usuarios u
                LEFT JOIN personagens p ON u.fav = p.id_personagem
                LEFT JOIN evento e ON u.fav = e.id_personagem
                WHERE u.id_usuario = %s
            """
            cursor.execute(query_obter_perfil, (id_usuario,))
            
            perfil = cursor.fetchone()

            
            query_obter_casamento = """
                SELECT c.id_personagem, COALESCE(p.nome, e.nome) AS nome_parceiro
                FROM casamentos c
                LEFT JOIN personagens p ON c.id_personagem = p.id_personagem
                LEFT JOIN evento e ON c.id_personagem = e.id_personagem
                WHERE c.user_id = %s AND c.estado = 'casado'
            """
            cursor.execute(query_obter_casamento, (id_usuario,))
            casamento = cursor.fetchone()

            if perfil:
                nome, nome_usuario, fav, adm, qntcartas, cenouras, iscas, bio, musica, pronome, privado, user, beta, nome_fav, imagem_fav = perfil

                resposta = f"<b>Perfil de {nome}</b>\n\n" \
                        f"✨ Fav: {fav} — {nome_fav}\n\n"
                
                if casamento:
                    parceiro_id, parceiro_nome = casamento
                    resposta += f"💍 Casado(a) com {parceiro_nome}\n\n"

                if adm:
                    resposta += f"🌈 Adm: {adm.capitalize()}\n\n"
                if beta:
                    resposta += f"🍀 Usuario Beta\n\n"
                resposta += f"‍🧑‍🌾 Camponês: {user}\n" \
                            f"🐟 Peixes: {qntcartas}\n" \
                            f"🥕 Cenouras: {cenouras}\n" \
                            f"🪝 Iscas: {iscas}\n"

                if pronome:
                    resposta += f"🌺 Pronomes: {pronome}\n\n"

                resposta += f"✍ {bio}\n\n" \
                            f"🎧: {musica}"

                enviar_perfil(message.chat.id, resposta, imagem_fav, fav, id_usuario, message)
            else:
                bot.send_message(message.chat.id, "Perfil não encontrado.", reply_to_message_id=message.message_id)
        else:
            bot.send_message(message.chat.id, "Você ainda não iniciou o bot. Use /start para começar.", reply_to_message_id=message.message_id)

    except mysql.connector.Error as err:
        bot.send_message(message.chat.id, f"Erro ao verificar perfil: {err}", reply_to_message_id=message.message_id)
    finally:
        fechar_conexao(cursor, conn)


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
        bot.reply_to(message, "Ocorreu um erro ao processar sua solicitação.")
        
@bot.message_handler(commands=['gperfil'])
def gperfil_command(message):

    if len(message.text.split()) != 2:
        bot.send_message(message.chat.id, "Formato incorreto. Use /gperfil seguido do nome de usuário desejado.")
        return

    username = message.text.split()[1].strip()

    try:
        conn, cursor = conectar_banco_dados()

        query_verificar_usuario = "SELECT 1 FROM usuarios WHERE user = %s"
        cursor.execute(query_verificar_usuario, (username,))
        usuario_existe = cursor.fetchone()

        if usuario_existe:

            query_obter_perfil = """
                SELECT 
                    u.nome, u.nome_usuario, u.fav, u.adm, u.qntcartas, u.cenouras, u.iscas, u.bio, u.musica, u.pronome, u.privado, u.beta,
                    COALESCE(p.nome, e.nome) AS nome_fav, 
                    COALESCE(p.imagem, e.imagem) AS imagem_fav
                FROM usuarios u
                LEFT JOIN personagens p ON u.fav = p.id_personagem
                LEFT JOIN evento e ON u.fav = e.id_personagem
                WHERE u.user = %s
            """
            cursor.execute(query_obter_perfil, (username,))
            perfil = cursor.fetchone()

            if perfil:
                nome, nome_usuario, fav, adm, qntcartas, cenouras, iscas, bio, musica, pronome, privado, beta, nome_fav, imagem_fav = perfil


                if beta == 1:
                    usuario_beta = True
                else:
                    usuario_beta = False
                if privado == 1:
                    resposta = f"<b>Perfil de {username}</b>\n\n" \
                               f"✨ Fav: {fav} — {nome_fav}\n\n"
                    if usuario_beta:
                        resposta += f"🍀 Usuario Beta\n\n"         
                    if adm:
                        resposta += f"🌈 Adm: {adm.capitalize()}\n\n"
                    if pronome:
                        resposta += f"🌺 Pronomes: {pronome.capitalize()}\n\n" 
                          
                    resposta += f"🔒 Perfil Privado"
                else:
                    resposta = f"<b>Perfil de {nome_usuario}</b>\n\n" \
                               f"✨ Fav: {fav} — {nome_fav}\n\n" \
                      
                    if usuario_beta:
                        resposta += f"🍀 <b>Usuario Beta</b>\n\n" 
                    if adm:
                        resposta += f"🌈 Adm: {adm.capitalize()}\n\n"
                    if pronome:
                        resposta += f"🌺 Pronomes: {pronome.capitalize()}\n\n" \
 
                    
                    resposta += f"‍🧑‍🌾 Camponês: {nome}\n" \
                                f"🐟 Peixes: {qntcartas}\n" \
                                f"🥕 Cenouras: {cenouras}\n" \
                                f"🪝 Iscas: {iscas}\n" \
                                f"✍ {bio}\n\n" \
                                f"🎧: {musica}"

                enviar_perfil(message.chat.id, resposta, imagem_fav, fav, message.from_user.id,message)
            else:
                bot.send_message(message.chat.id, "Perfil não encontrado.")
        else:
            bot.send_message(message.chat.id, "O nome de usuário especificado não está registrado.")

    except mysql.connector.Error as err:
        bot.send_message(message.chat.id, f"Erro ao verificar o perfil: {err}")
    finally:
        fechar_conexao(cursor, conn)
       
@bot.message_handler(commands=['config'])
def handle_config(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Pronomes', callback_data='bpronomes_')
    btn2 = types.InlineKeyboardButton('Privacidade', callback_data='privacy')
    btn3 = types.InlineKeyboardButton('Lembretes', callback_data='lembretes')
    btn_cancelar = types.InlineKeyboardButton('❌ Cancelar', callback_data='pcancelar')
    markup.add(btn1, btn2)
    markup.add(btn3, btn_cancelar)
    bot.send_message(message.chat.id, "Escolha uma opção:", reply_markup=markup)


@bot.message_handler(commands=['gnome'])
def gnome(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    idmens = message.message_id
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
                    i.quantidade AS quantidade_usuario,
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
                    i.quantidade AS quantidade_usuario,
                    p.imagem
                FROM personagens p
                LEFT JOIN inventario i ON p.id_personagem = i.id_personagem AND i.id_usuario = %s
                WHERE p.nome LIKE %s
            """

        values_personagens = (user_id, f"%{nome}%")
        conn, cursor = conectar_banco_dados()
        cursor.execute(sql_personagens, values_personagens)
        resultados_personagens = cursor.fetchall()

        if len(resultados_personagens) == 1:

            mensagem = resultados_personagens[0]
            id_personagem, nome, subcategoria, categoria, quantidade_usuario, imagem_url = mensagem

            mensagem = f"💌 | Personagem: \n\n<code>{id_personagem}</code> • {nome}\nde {subcategoria}"
            if quantidade_usuario is None:
                mensagem += f"\n\n🌧 | Tempo fechado..."
            elif quantidade_usuario > 0:
                mensagem += f"\n\n☀ | {quantidade_usuario}⤫"
            else:
                mensagem += f"\n\n🌧 | Tempo fechado..."

            gif_url = obter_gif_url(id_personagem, user_id)

            if gif_url:
                imagem_url = gif_url
                if imagem_url.lower().endswith(".gif"):
                    bot.send_animation(chat_id, imagem_url, caption=mensagem,parse_mode="HTML")                  
                elif imagem_url.lower().endswith(".mp4"):
                    bot.send_video(chat_id, imagem_url, caption=mensagem,parse_mode="HTML") 
                elif imagem_url.lower().endswith((".jpeg", ".jpg", ".png")):
                    bot.send_photo(chat_id, imagem_url, caption=mensagem,parse_mode="HTML")                
                else:
                    send_message_with_buttons(chat_id, idmens, [(None, mensagem)], reply_to_message_id=message.message_id)
            else:
                if  imagem_url.lower().endswith(".gif"):
                    bot.send_animation(chat_id, imagem_url, caption=mensagem,parse_mode="HTML")                  
                elif imagem_url.lower().endswith(".mp4"):
                    bot.send_video(chat_id, imagem_url, caption=mensagem,parse_mode="HTML") 
                elif imagem_url.lower().endswith((".jpeg", ".jpg", ".png")):
                    bot.send_photo(chat_id, imagem_url, caption=mensagem,parse_mode="HTML")                
                else:
                    send_message_with_buttons(chat_id, idmens, [(None, mensagem)], reply_to_message_id=message.message_id)
                
            user_id = chat_id
            save_user_state(chat_id, [mensagem])  

        else:
            mensagens = []
            for resultado_personagem in resultados_personagens:
                id_personagem, nome, subcategoria, categoria, quantidade_usuario, imagem_url = resultado_personagem
                mensagem = f"💌 | Personagem: \n\n<code>{id_personagem}</code> • {nome}\nde {subcategoria}"
                if quantidade_usuario is None:
                    mensagem += f"\n\n🌧 | Tempo fechado..."
                elif quantidade_usuario > 0:
                    mensagem += f"\n\n☀ | {quantidade_usuario}⤫"
                else:
                    mensagem += f"\n\n🌧 | Tempo fechado..."

                gif_url = obter_gif_url(id_personagem, user_id)
                if gif_url:
                    mensagens.append((gif_url, mensagem))
                elif imagem_url:
                    mensagens.append((imagem_url, mensagem))
                else:
                    mensagens.append((None, mensagem))

            save_user_state(chat_id, mensagens)
            send_message_with_buttons(chat_id, idmens, mensagens, reply_to_message_id=message.message_id)

    except Exception as e:
        import traceback
        traceback.print_exc()

    finally:
        fechar_conexao(cursor, conn)



@bot.message_handler(commands=['gnomes'])
def gnome(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    conn, cursor = conectar_banco_dados()

    try:
        nome = message.text.split('/gnomes', 1)[1].strip()
        if len(nome) <= 2:
            bot.send_message(chat_id, "Por favor, forneça um nome com mais de 3 letras.", reply_to_message_id=message.message_id)
            return
        sql_personagens = """
            SELECT
                p.emoji,
                p.id_personagem,
                p.nome,
                p.subcategoria
            FROM personagens p
            WHERE p.nome LIKE %s
        """
        values_personagens = (f"%{nome}%",)
        pesquisa = nome
        cursor.execute(sql_personagens, values_personagens)
        resultados_personagens = cursor.fetchall()

        if resultados_personagens:
            total_resultados = len(resultados_personagens)
            resultados_por_pagina = 15
            total_paginas = -(-total_resultados // resultados_por_pagina)  
            pagina_solicitada = 1

            if total_resultados > resultados_por_pagina:
                if len(message.text.split()) == 3 and message.text.split()[2].isdigit():
                    pagina_solicitada = min(int(message.text.split()[2]), total_paginas)
                resultados_pagina_atual = resultados_personagens[(pagina_solicitada - 1) * resultados_por_pagina : pagina_solicitada * resultados_por_pagina]
                lista_resultados = [F"{emoji} <code>{id_personagem}</code> • {nome}\nde {subcategoria}"  for emoji, id_personagem, nome, subcategoria in resultados_pagina_atual]

                mensagem_final = f"🐠 Peixes de nome <b>{pesquisa}</b>:\n\n" + "\n".join(lista_resultados)+ f"\n\nPágina {pagina_solicitada}/{total_paginas}:"
                markup = create_navigation_markup(pagina_solicitada, total_paginas)
                message = bot.send_message(chat_id, mensagem_final, reply_markup=markup, reply_to_message_id=message.message_id,parse_mode="HTML")
                
                save_state(user_id, 'gnomes', resultados_personagens, chat_id, message.message_id)
            else:
                lista_resultados = [f"{emoji} <code>{id_personagem}</code> • {nome}\nde {subcategoria}" for emoji, id_personagem, nome, subcategoria in resultados_personagens]

                mensagem_final = f"🐠 Peixes de nome <b>{pesquisa}</b>:\n\n" + "\n".join(lista_resultados)
                bot.send_message(chat_id, mensagem_final, reply_to_message_id=message.message_id,parse_mode='HTML')

        else:
            bot.send_message(chat_id, f"Nenhum resultado encontrado para o nome '{nome}'.", reply_to_message_id=message.message_id)
    finally:
        fechar_conexao(cursor, conn)

@bot.message_handler(commands=['gid'])
def obter_id_e_enviar_info_com_imagem(message):
    try:
        conn, cursor = conectar_banco_dados()
        user_id = message.from_user.id
        chat_id = message.chat.id

        command_parts = message.text.split()
        if len(command_parts) == 2 and command_parts[1].isdigit():
            id_pesquisa = command_parts[1]

            is_evento = verificar_evento(cursor, id_pesquisa)

            if is_evento:
                sql_evento = """
                    SELECT
                        e.id_personagem,
                        e.nome,
                        e.subcategoria,
                        e.categoria,
                        i.quantidade AS quantidade_usuario,
                        e.imagem
                    FROM evento e
                    LEFT JOIN inventario i ON e.id_personagem = i.id_personagem AND i.id_usuario = %s
                    WHERE e.id_personagem = %s
                """
                values_evento = (message.from_user.id, id_pesquisa)

                cursor.execute(sql_evento, values_evento)
                resultado_evento = cursor.fetchone()

                if resultado_evento:
                    id_personagem, nome, subcategoria, categoria, quantidade_usuario, imagem_url = resultado_evento

                    mensagem = f"💌 | Personagem: \n\n<code>{id_personagem}</code> • {nome}\nde {subcategoria}"

                    if quantidade_usuario == None:
                        mensagem += f"\n\n🌧 | Tempo fechado..."
                    elif quantidade_usuario == 1:
                        mensagem += f"\n\n{'☀  '}"
                    else:
                        mensagem += f"\n\n{'☀ 𖡩'}"

                    try:
                        if imagem_url.lower().endswith(('.jpg', '.jpeg', '.png')):
                            bot.send_photo(chat_id=message.chat.id, photo=imagem_url, caption=mensagem, reply_to_message_id=message.message_id,parse_mode="HTML")
                        elif imagem_url.lower().endswith(('.mp4', '.gif')):
                            bot.send_video(chat_id=message.chat.id, video=imagem_url, caption=mensagem, reply_to_message_id=message.message_id,parse_mode="HTML")
                    except Exception as e:
                        bot.send_message(chat_id, mensagem, reply_to_message_id=message.message_id,parse_mode="HTML")
                else:
                    bot.send_message(chat_id, f"Nenhum resultado encontrado para o ID '{id_pesquisa}'.", reply_to_message_id=message.message_id)

            else:
                sql_normal = """
                    SELECT
                        p.id_personagem,
                        p.nome,
                        p.subcategoria,
                        p.categoria,
                        i.quantidade AS quantidade_usuario,
                        p.imagem,
                        p.cr
                    FROM personagens p
                    LEFT JOIN inventario i ON p.id_personagem = i.id_personagem AND i.id_usuario = %s
                    WHERE p.id_personagem = %s
                """
                values_normal = (message.from_user.id, id_pesquisa)

                cursor.execute(sql_normal, values_normal)
                resultado_normal = cursor.fetchone()

                if resultado_normal:
                    id_personagem, nome, subcategoria, categoria, quantidade_usuario, imagem_url, cr = resultado_normal

                    mensagem = f"💌 | Personagem: \n\n{id_personagem} • {nome}\nde {subcategoria}"

                    if quantidade_usuario is not None and quantidade_usuario > 0:
                        mensagem += f"\n\n☀ | {quantidade_usuario}⤫"
                    else:
                        mensagem += f"\n\n🌧 | Tempo fechado..."


                    if cr:
                        link_cr = obter_link_formatado(cr)
                        mensagem += f"\n\n{link_cr}"

                    markup = InlineKeyboardMarkup()
                    markup.row_width = 1
                    markup.add(InlineKeyboardButton("💟", callback_data=f"total_{id_pesquisa}"))

                    gif_url = obter_gif_url(id_personagem, user_id)
                    if gif_url:
                        imagem_url = gif_url
                        if  imagem_url.lower().endswith(".gif"):
                            bot.send_video(chat_id=message.chat.id, video=imagem_url, caption=mensagem, reply_markup=markup, reply_to_message_id=message.message_id,parse_mode="HTML")
                        elif imagem_url.lower().endswith(".mp4"):
                            bot.send_video(chat_id=message.chat.id, video=imagem_url, caption=mensagem, reply_markup=markup, reply_to_message_id=message.message_id,parse_mode="HTML")
                        elif imagem_url.lower().endswith((".jpeg", ".jpg", ".png")):
                            bot.send_photo(chat_id=message.chat.id, photo=imagem_url, caption=mensagem, reply_markup=markup, reply_to_message_id=message.message_id,parse_mode="HTML")
                        else:
                            bot.send_message(chat_id, mensagem)
                    else:
                        if  imagem_url.lower().endswith(".gif"):
                            bot.send_video(chat_id=message.chat.id, video=imagem_url, caption=mensagem, reply_markup=markup, reply_to_message_id=message.message_id,parse_mode="HTML")
                        elif imagem_url.lower().endswith(".mp4"):
                            bot.send_video(chat_id=message.chat.id, video=imagem_url, caption=mensagem, reply_markup=markup, reply_to_message_id=message.message_id,parse_mode="HTML")
                        elif imagem_url.lower().endswith((".jpeg", ".jpg", ".png")):
                            bot.send_photo(chat_id=message.chat.id, photo=imagem_url, caption=mensagem, reply_markup=markup, reply_to_message_id=message.message_id,parse_mode="HTML")
                        else:
                            bot.send_message(chat_id, mensagem) 
                else:
                    bot.send_message(chat_id, f"Nenhum resultado encontrado para o ID '{id_pesquisa}'.", reply_to_message_id=message.message_id)
        else:
            bot.send_message(chat_id, "Formato incorreto. Use /gid seguido do ID desejado, por exemplo: /gid 123", reply_to_message_id=message.message_id)
    except Exception as e:
        import traceback
        traceback.print_exc()
        erro = traceback.print_exc()
        mensagem=(f"carta com erro: {id_personagem}. erro:",e)
        bot.send_message(grupodeerro, mensagem,parse_mode="HTML")
@bot.message_handler(commands=['cesta'])
def verificar_cesta(message):
    try:
        parts = message.text.split(' ', 2)
        if len(parts) < 3:
            bot.reply_to(message, "Por favor, forneça o tipo ('s', 'f', 'c', 'se', 'fe' ou 'cf') e a subcategoria após o comando, por exemplo: /cesta s bts")
            return

        tipo = parts[1].strip()
        subcategoria = parts[2].strip()

        id_usuario = message.from_user.id
        nome_usuario = message.from_user.first_name

        if tipo in ['s', 'se']:
            subcategoria_proxima = encontrar_subcategoria_proxima(subcategoria)
            if not subcategoria_proxima:
                bot.reply_to(message, "Espécie não identificada. Você digitou certo? 🤭")
                return

            ids_personagens = obter_ids_personagens_inventario(id_usuario, subcategoria_proxima)
            if 'e' in tipo:
                ids_personagens += obter_ids_personagens_evento(id_usuario, subcategoria_proxima, incluir=False)
            total_personagens_subcategoria = obter_total_personagens_subcategoria(subcategoria_proxima)
            total_registros = len(ids_personagens)

            if total_registros > 0:
                total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)
                mostrar_pagina_cesta_s(message, subcategoria_proxima, id_usuario, 1, total_paginas, ids_personagens, total_personagens_subcategoria, nome_usuario)
            else:
                bot.reply_to(message, f"🌧️ Sem peixes de {subcategoria_proxima} na cesta... a jornada continua.")

        elif tipo in ['f', 'fe']:
            subcategoria_proxima = encontrar_subcategoria_proxima(subcategoria)
            if not subcategoria_proxima:
                bot.reply_to(message, "Espécie não identificada. Você digitou certo? 🤭")
                return

            ids_personagens_faltantes = obter_ids_personagens_faltantes(id_usuario, subcategoria_proxima)
            if 'e' in tipo:
                ids_personagens_faltantes += obter_ids_personagens_evento(id_usuario, subcategoria_proxima, incluir=True)
            total_personagens_subcategoria = obter_total_personagens_subcategoria(subcategoria_proxima)
            total_registros = len(ids_personagens_faltantes)

            if total_registros > 0:
                total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)
                mostrar_pagina_cesta_f(message, subcategoria_proxima, id_usuario, 1, total_paginas, ids_personagens_faltantes, total_personagens_subcategoria, nome_usuario)
            else:
                bot.reply_to(message, f"☀️ Nada como a alegria de ter todos os peixes de {subcategoria_proxima} na cesta!")

        elif tipo == 'c':
            subcategoria_proxima = encontrar_categoria_proxima(subcategoria)
            if not subcategoria_proxima:
                bot.reply_to(message, "Espécie não identificada. Você digitou certo? 🤭")
                return

            ids_personagens = obter_ids_personagens_categoria(id_usuario, subcategoria_proxima)
            total_personagens_categoria = obter_total_personagens_categoria(subcategoria_proxima)
            total_registros = len(ids_personagens)

            if total_registros > 0:
                total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)
                mostrar_pagina_cesta_c(message, subcategoria_proxima, id_usuario, 1, total_paginas, ids_personagens, total_personagens_categoria, nome_usuario)
            else:
                bot.reply_to(message, f"🌧️ Sem peixes de {subcategoria_proxima} na cesta... a jornada continua.")

        elif tipo == 'cf':
            subcategoria_proxima = encontrar_categoria_proxima(subcategoria)
            if not subcategoria_proxima:
                bot.reply_to(message, "Espécie não identificada. Você digitou certo? 🤭")
                return

            ids_personagens_faltantes = obter_ids_personagens_faltantes_categoria(id_usuario, subcategoria_proxima)
            total_personagens_categoria = obter_total_personagens_categoria(subcategoria_proxima)
            total_registros = len(ids_personagens_faltantes)

            if total_registros > 0:
                total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)
                mostrar_pagina_cesta_cf(message, subcategoria_proxima, id_usuario, 1, total_paginas, ids_personagens_faltantes, total_personagens_categoria, nome_usuario)
            else:
                bot.reply_to(message, f"☀️ Nada como a alegria de ter todos os peixes de {subcategoria_proxima} na cesta!")

        else:
            bot.reply_to(message, "Tipo inválido. Use 's' para os personagens que você possui, 'f' para os que você não possui, 'c' para uma categoria completa ou 'cf' para faltantes na categoria.")

    except IndexError:
        bot.reply_to(message, "Por favor, forneça o tipo ('s', 'f', 'c', 'se', 'fe' ou 'cf') e a subcategoria desejada após o comando, por exemplo: /cesta s bts")

    except Exception as e:
        print(f"Erro ao processar comando /cesta: {e}")
        bot.reply_to(message, "Ocorreu um erro ao processar sua solicitação.")
        
@bot.message_handler(commands=['submenus'])
def submenus_command(message):
    try:
        parts = message.text.split(' ', 1)
        conn, cursor = conectar_banco_dados()

        if len(parts) == 1:
            pagina = 1
            submenus_por_pagina = 15

            query_todos_submenus = """
            SELECT subcategoria, submenu
            FROM personagens
            WHERE submenu IS NOT NULL AND submenu != ''
            GROUP BY subcategoria, submenu
            ORDER BY subcategoria, submenu
            LIMIT %s OFFSET %s
            """
            offset = (pagina - 1) * submenus_por_pagina
            cursor.execute(query_todos_submenus, (submenus_por_pagina, offset))
            submenus = cursor.fetchall()
            cursor.execute("SELECT COUNT(DISTINCT subcategoria, submenu) FROM personagens WHERE submenu IS NOT NULL AND submenu != ''")
            total_submenus = cursor.fetchone()[0]
            total_paginas = (total_submenus // submenus_por_pagina) + (1 if total_submenus % submenus_por_pagina > 0 else 0)

            if submenus:
                mensagem = "<b>📂 Todos os Submenus:</b>\n\n"
                for subcategoria, submenu in submenus:
                    mensagem += f"🍎 {subcategoria} - {submenu}\n"
                mensagem += f"\nPágina {pagina}/{total_paginas}"
                markup = InlineKeyboardMarkup()
                if total_paginas > 1:
                    markup.row(
                        InlineKeyboardButton("⬅️", callback_data=f"navigate_submenus_{pagina - 1 if pagina > 1 else total_paginas}"),
                        InlineKeyboardButton("➡️", callback_data=f"navigate_submenus_{pagina + 1 if pagina < total_paginas else 1}")
                    )

                bot.send_message(message.chat.id, mensagem, parse_mode="HTML", reply_to_message_id=message.message_id, reply_markup=markup)
            else:
                bot.send_message(message.chat.id, "Não foram encontrados submenus.", parse_mode="HTML", reply_to_message_id=message.message_id)

        else:
            subcategoria = parts[1].strip()
            query_submenus = """
            SELECT DISTINCT submenu
            FROM personagens
            WHERE subcategoria = %s AND submenu IS NOT NULL AND submenu != ''
            """
            cursor.execute(query_submenus, (subcategoria,))
            submenus = [row[0] for row in cursor.fetchall()]

            if submenus:
                mensagem = f"<b>📂 Submenus na subcategoria '{subcategoria.title()}':</b>\n\n"
                for submenu in submenus:
                    mensagem += f"🍎 {subcategoria.title()}- {submenu}\n"
            else:
                mensagem = f"Não foram encontrados submenus para a subcategoria '{subcategoria.title()}'."

            bot.send_message(message.chat.id, mensagem, parse_mode="HTML", reply_to_message_id=message.message_id)

    except Exception as e:
        print(f"Erro ao processar comando /submenus: {e}")
        bot.reply_to(message, "Ocorreu um erro ao processar sua solicitação.")
    finally:
        fechar_conexao(cursor, conn)

@bot.callback_query_handler(func=lambda call: call.data.startswith('navigate_submenus_'))
def callback_navegacao_submenus(call):
    try:
        data = call.data.split('_')
        pagina_str = data[-1]
        pagina = int(pagina_str)
        submenus_por_pagina = 15

        conn, cursor = conectar_banco_dados()

        query_todos_submenus = """
        SELECT subcategoria, submenu
        FROM personagens
        WHERE submenu IS NOT NULL AND submenu != ''
        GROUP BY subcategoria, submenu
        ORDER BY subcategoria, submenu
        LIMIT %s OFFSET %s
        """
        offset = (pagina - 1) * submenus_por_pagina
        cursor.execute(query_todos_submenus, (submenus_por_pagina, offset))
        submenus = cursor.fetchall()

        cursor.execute("SELECT COUNT(DISTINCT subcategoria, submenu) FROM personagens WHERE submenu IS NOT NULL AND submenu != ''")
        total_submenus = cursor.fetchone()[0]
        total_paginas = (total_submenus // submenus_por_pagina) + (1 if total_submenus % submenus_por_pagina > 0 else 0)

        if submenus:
            mensagem = "<b>📂 Todos os Submenus: </b>\n\n"
            for subcategoria, submenu in submenus:
                mensagem += f"🍎 {subcategoria} - {submenu}\n"
            mensagem += f"\nPágina {pagina}/{total_paginas}"

            markup = InlineKeyboardMarkup()
            if total_paginas > 1:
                markup.row(
                    InlineKeyboardButton("⬅️", callback_data=f"navigate_submenus_{pagina - 1 if pagina > 1 else total_paginas}"),
                    InlineKeyboardButton("➡️", callback_data=f"navigate_submenus_{pagina + 1 if pagina < total_paginas else 1}")
                )

            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=mensagem, parse_mode="HTML", reply_markup=markup)

    except Exception as e:
        print(f"Erro ao processar callback de navegação: {e}")
        bot.answer_callback_query(call.id, "Ocorreu um erro ao processar sua solicitação.")
    finally:
        fechar_conexao(cursor, conn)

@bot.message_handler(commands=['submenu'])
def submenu_command(message):
    try:
        parts = message.text.split(' ', 2)
        if len(parts) < 3:
            bot.reply_to(message, "Por favor, forneça o tipo ('s' ou 'f') e o nome do submenu após o comando, por exemplo: /submenu s bts")
            return

        tipo = parts[1].strip()
        submenu = parts[2].strip()

        id_usuario = message.from_user.id
        nome_usuario = message.from_user.first_name

        conn, cursor = conectar_banco_dados()

        query_todos = """
        SELECT id_personagem, nome, subcategoria
        FROM personagens
        WHERE submenu = %s
        """
        cursor.execute(query_todos, (submenu,))
        todos_personagens = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}

        if not todos_personagens:
            bot.reply_to(message, f"O submenu '{submenu}' não existe.")
            return

        query_possui = """
        SELECT per.id_personagem, per.nome, per.subcategoria
        FROM inventario inv
        JOIN personagens per ON inv.id_personagem = per.id_personagem
        WHERE inv.id_usuario = %s AND per.submenu = %s
        """
        cursor.execute(query_possui, (id_usuario, submenu))
        personagens_possui = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}

        if tipo == 's':
            if personagens_possui:
                mensagem = f"🌧️ A cesta de {nome_usuario} contém:\n\n"
                for id_personagem, (nome, subcategoria) in personagens_possui.items():
                    mensagem += f"<code>{id_personagem}</code> - {nome}\n"
            else:
                mensagem = f"🌧️ Você não possui nenhum personagem neste submenu."

        elif tipo == 'f':
            personagens_faltantes = {id_personagem: (nome, subcategoria) for id_personagem, (nome, subcategoria) in todos_personagens.items() if id_personagem not in personagens_possui}
            if personagens_faltantes:
                mensagem = f"🌧️ Faltam na cesta de {nome_usuario}:\n\n"
                for id_personagem, (nome, subcategoria) in personagens_faltantes.items():
                    mensagem += f"<code>{id_personagem}</code> - {nome}\n"
            else:
                mensagem = f"☀️ Nada como a alegria de ter todas as cartas de {submenu} - {todos_personagens[next(iter(personagens_possui))][1]} na cesta!"

        else:
            bot.reply_to(message, "Tipo inválido. Use 's' para os personagens que você possui e 'f' para os que você não possui.")
            return

        bot.send_message(message.chat.id, mensagem, parse_mode="HTML")

    except Exception as e:
        print(f"Erro ao processar comando /submenu: {e}")
        bot.reply_to(message, "Ocorreu um erro ao processar sua solicitação.")
    finally:
        fechar_conexao(cursor, conn)

@bot.message_handler(commands=['hist'])
def command_historico(message):
    id_usuario = message.chat.id  
    tipo_historico = message.text.split()[-1].lower()  

    if tipo_historico == 'troca':
        historico = obter_historico_trocas(id_usuario)
        if historico:
            historico_mensagem = "🤝 | Seu histórico de trocas:\n\n"
            for troca in historico:
                id_usuario1, id_usuario2, carta1, carta2, aceita = troca
                carta1 = obter_nome(carta1)
                carta2 = obter_nome(carta2)
                nome1 = obter_nome_usuario_por_id(id_usuario1)
                nome2 = obter_nome_usuario_por_id(id_usuario2)
                status = "✅" if aceita else "⛔️"
                mensagem = f"ꕤ Troca entre {nome1} e {nome2}:\n{carta1} e {carta2} - {status}\n\n"
                historico_mensagem += mensagem

            bot.send_message(id_usuario, historico_mensagem)
        else:
            bot.send_message(id_usuario, "Nenhuma troca encontrada para este usuário.")

    elif tipo_historico == 'pesca':
        historico = obter_historico_pescas(id_usuario)
        if historico:
            historico_mensagem = "🎣 | Seu histórico de pescas:\n\n"
            for pesca in historico:
                id_carta, data_hora = pesca
                carta1 = obter_nome(id_carta)
                data_formatada = datetime.strftime(data_hora, "%d/%m/%Y - %H:%M")
                mensagem = f"✦ Carta: {id_carta} → {carta1}\nPescada em: {data_formatada}\n\n"
                historico_mensagem += mensagem

            bot.send_message(id_usuario, historico_mensagem)
        else:
            bot.send_message(id_usuario, "Nenhuma pesca encontrada para este usuário.")


@bot.message_handler(commands=['tag'])
def verificar_comando_tag(message):
    try:
        parametros = message.text.split(' ', 1)[1:] 

        if not parametros:
            conn, cursor = conectar_banco_dados()
            id_usuario = message.from_user.id
            cursor.execute("SELECT DISTINCT nometag FROM tags WHERE id_usuario = %s", (id_usuario,))
            tags = cursor.fetchall()
            if tags:
                resposta = "🔖| Suas tags:\n\n"
                for tag in tags:
                    resposta += f"• {tag[0]}\n"
                bot.reply_to(message, resposta)
            else:
                bot.reply_to(message, "Você não possui nenhuma tag.")
            fechar_conexao(cursor, conn)
            return

        nometag = parametros[0] 
        id_usuario = message.from_user.id
        mostrar_primeira_pagina_tag(message, nometag, id_usuario)

    except Exception as e:
        print(f"Erro ao processar comando /tag: {e}")
        bot.reply_to(message, "Ocorreu um erro ao processar sua solicitação.")


@bot.message_handler(commands=['addtag'])
def adicionar_tag(message):
    try:
        conn, cursor = conectar_banco_dados()
        id_usuario = message.from_user.id
        args = message.text.split(maxsplit=1)
        
        if len(args) == 2:
            tag_info = args[1]
            tag_parts = tag_info.split('|')
            
            if len(tag_parts) == 2:
                ids_personagens_str = tag_parts[0].strip()
                nometag = tag_parts[1].strip()
                
                if ids_personagens_str and nometag:
                    ids_personagens = [id_personagem.strip() for id_personagem in ids_personagens_str.split(',')]
                    
                    for id_personagem in ids_personagens:
                        cursor.execute(
                            "INSERT INTO tags (id_usuario, id_personagem, nometag) VALUES (%s, %s, %s)", 
                            (id_usuario, id_personagem, nometag)
                        )
                    
                    conn.commit()
                    bot.reply_to(message, f"Tag '{nometag}' adicionada com sucesso.")
                else:
                    bot.reply_to(message, "Formato incorreto. Use /addtag id1,id2,... | nometag")
            else:
                bot.reply_to(message, "Formato incorreto. Use /addtag id1,id2,... | nometag")
        else:
            bot.reply_to(message, "Formato incorreto. Use /addtag id1,id2,... | nometag")
    
    except mysql.connector.Error as err:
        print(f"Erro de MySQL: {err}")
        bot.reply_to(message, "Ocorreu um erro ao processar a operação no banco de dados.")
    
    except Exception as e:
        print(f"Erro ao adicionar tag: {e}")
        bot.reply_to(message, "Ocorreu um erro ao processar a operação.")
    
    finally:
        fechar_conexao(cursor, conn)


@bot.message_handler(commands=['deltag'])
def deletar_tag(message):
    try:
        conn, cursor = conectar_banco_dados()
        id_usuario = message.from_user.id
        args = message.text.split(maxsplit=1)
        
        if len(args) == 2:
            tag_info = args[1].strip()

            if '|' in tag_info:
                id_list, nometag = [part.strip() for part in tag_info.split('|')]
                ids_personagens = [id.strip() for id in id_list.split(',')]

                for id_personagem in ids_personagens:
                    cursor.execute("SELECT idtags FROM tags WHERE id_usuario = %s AND id_personagem = %s AND nometag = %s",
                                   (id_usuario, id_personagem, nometag))
                    tag_existente = cursor.fetchone()
                    
                    if tag_existente:
                        idtag = tag_existente[0]
                        cursor.execute("DELETE FROM tags WHERE idtags = %s", (idtag,))
                        conn.commit()
                        bot.reply_to(message, f"ID {id_personagem} removido da tag '{nometag}' com sucesso.")
                    else:
                        bot.reply_to(message, f"O ID {id_personagem} não está associado à tag '{nometag}'.")
            
            else:
                nometag = tag_info.strip()
                cursor.execute("DELETE FROM tags WHERE id_usuario = %s AND nometag = %s", (id_usuario, nometag))
                conn.commit()
                bot.reply_to(message, f"A tag '{nometag}' foi removida completamente.")
        
        else:
            bot.reply_to(message, "Formato incorreto. Use /deltag id1, id2, id3 | nometag para remover IDs específicos da tag ou /deltag nometag para remover a tag inteira.")

    except Exception as e:
        print(f"Erro ao deletar tag: {e}")
    finally:
        fechar_conexao(cursor, conn)

@bot.message_handler(commands=['apoiar'])
def doacao(message):
    markup = telebot.types.InlineKeyboardMarkup()
    chave_pix = "80388add-294e-4075-8cd5-8765cc9f9be0"
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(text="Link do apoia.se 🌟", url="https://apoia.se/garden"))
    mensagem = f"👨🏻‍🌾 Oi, jardineiro! Se está vendo esta mensagem, significa que está interessado em nos ajudar, certo? A equipe MabiGarden fica muito feliz em saber que nosso trabalho o agradou e o motivou a nos ajudar! \n\nCaso deseje contribuir com PIX, a chave é: <code>{chave_pix}</code> (clique na chave para copiar automaticamente) \n\nSe preferir, pode usar a plataforma apoia-se no botão abaixo!"
    bot.send_message(message.chat.id, mensagem, reply_markup=markup, parse_mode="HTML", reply_to_message_id=message.message_id)

@bot.message_handler(commands=['gift'])
def handle_gift_cards(message):
    conn, cursor = conectar_banco_dados()
    if message.from_user.id != 5532809878 and message.from_user.id != 1805086442:
        bot.reply_to(message, "Você não é a Hashi ou a Skar para usar esse comando.")
        return
    try:
        _, quantity, card_id, user_id = message.text.split()
        quantity = int(quantity)
        card_id = int(card_id)
        user_id = int(user_id)
    except (ValueError, IndexError):
        bot.reply_to(message, "Por favor, use o formato correto: /gift quantidade card_id user_id")
        return
    gift_cards(quantity, card_id, user_id)
    bot.reply_to(message, f"{quantity} cartas adicionadas com sucesso!")

@bot.message_handler(commands=['addbanco'])
def addbanco_command(message):
    try:
        conn, cursor = conectar_banco_dados()
        partes_comando = message.text.split()
        if len(partes_comando) != 2:
            bot.send_message(message.chat.id, "Uso: /addbanco <id_usuario>")
            return

        id_usuario = int(partes_comando[1])

        conn, cursor = conectar_banco_dados()
        cursor.execute("SELECT id_personagem, quantidade FROM inventario WHERE id_usuario = %s", (id_usuario,))
        cartas_usuario = cursor.fetchall()

        if not cartas_usuario:
            bot.send_message(message.chat.id, "Usuário não possui cartas.")
            return
        for carta in cartas_usuario:
            id_personagem, quantidade = carta
            
            cursor.execute("SELECT COUNT(*) FROM banco_inventario WHERE id_personagem = %s", (id_personagem,))
            existe = cursor.fetchone()[0]
            
            if existe:
                cursor.execute("UPDATE banco_inventario SET quantidade = quantidade + %s WHERE id_personagem = %s", (quantidade, id_personagem))
            else:
                cursor.execute("INSERT INTO banco_inventario (id_personagem, quantidade) VALUES (%s, %s)", (id_personagem, quantidade))
        cursor.execute("DELETE FROM inventario WHERE id_usuario = %s", (id_usuario,))

        conn.commit()
        bot.send_message(message.chat.id, f"Cartas do usuário {id_usuario} transferidas para o banco com sucesso.")

    except Exception as e:
        print(f"Erro ao transferir cartas para o banco: {e}")
        bot.send_message(message.chat.id, "Erro ao transferir cartas para o banco.")
    finally:
        fechar_conexao(cursor, conn)
        
@bot.callback_query_handler(func=lambda call: call.data.startswith('cartas_compradas_pagina_'))
def callback_cartas_compradas(call):
    pagina_atual = int(call.data.split('_')[-1])
    id_usuario = call.from_user.id

    if id_usuario in globals.cartas_compradas_dict:
        cartas = globals.cartas_compradas_dict[id_usuario]
        mostrar_cartas_compradas(call.message.chat.id, cartas, id_usuario, pagina_atual,call.message.message_id)
    else:
        bot.send_message(call.message.chat.id, "Erro ao exibir cartas compradas. Tente novamente.")

        fechar_conexao(cursor, conn)

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

@bot.message_handler(commands=['banco'])
def banco_command(message):
    try:
        cartas_banco = obter_cartas_banco_cache()

        if not cartas_banco:
            bot.send_message(message.chat.id, "Não há cartas no banco.")
            return

        total_paginas = (len(cartas_banco) // 30) + (1 if len(cartas_banco) % 30 > 0 else 0)
        total_cartas = sum([quantidade for _, quantidade in cartas_banco])
        mostrar_cartas_banco(message.chat.id, 1, total_paginas, cartas_banco, total_cartas, message.message_id)
    except Exception as e:
        import traceback
        traceback.print_exc()


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
        
        id_fav_usuario, emoji_fav, nome_fav, imagem_fav = obter_favorito(id_usuario)

        if id_fav_usuario is not None:
            print(id_fav_usuario)
            resposta = f"💌 | Cartas no armazém de {usuario}:\n\nFav: {emoji_fav} {id_fav_usuario} — {nome_fav}\n\n"

            sql = f"""
                SELECT id_personagem, emoji, nome_personagem, subcategoria, quantidade, categoria, evento
                FROM (
                    SELECT i.id_personagem, p.emoji, p.nome AS nome_personagem, p.subcategoria, i.quantidade, p.categoria, '' AS evento
                    FROM inventario i
                    JOIN personagens p ON i.id_personagem = p.id_personagem
                    WHERE i.id_usuario = {id_usuario} AND i.quantidade > 0

                    UNION

                    SELECT e.id_personagem, e.emoji, e.nome AS nome_personagem, e.subcategoria, 0 AS quantidade, e.categoria, e.evento
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
                if gif_url:
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
                SELECT i.id_personagem, p.emoji, p.nome AS nome_personagem, p.subcategoria, i.quantidade, p.categoria, '' AS evento
                FROM inventario i
                JOIN personagens p ON i.id_personagem = p.id_personagem
                WHERE i.id_usuario = {id_usuario} AND i.quantidade > 0

                UNION ALL

                -- Consulta para cartas de evento que o usuário possui
                SELECT e.id_personagem, e.emoji, e.nome AS nome_personagem, e.subcategoria, 0 AS quantidade, e.categoria, e.evento
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
        bot.send_message(message.chat.id, "Ocorreu um erro ao processar a consulta no banco de dados.")
    except ValueError as e:
        print(f"Erro: {e}")
        mensagem_banido = "Um erro ocorreu ao abrir seu armazém... Tente trocar seu fav usando o </code>comando /setfav</code>. Caso não resolva, entre em contato com o suporte."
        bot.send_message(message.chat.id, mensagem_banido)
    except telebot.apihelper.ApiHTTPException as e:
        print(f"Erro na API do Telegram: {e}")
    finally:
        fechar_conexao(cursor, conn)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    try:

        message = call.message
        conn, cursor = conectar_banco_dados()
        chat_id = call.message.chat.id

        if call.message:
            chat_id = call.message.chat.id
            if not verificar_tempo_passado(chat_id):
                return
            else:
                ultima_interacao[chat_id] = datetime.now()

            if call.data.startswith("geral_compra_"):
                geral_compra_callback(call)
            elif call.data.startswith('confirmar_iscas'):
                message_id = call.message.message_id
                confirmar_iscas(call,message_id)
            elif call.data.startswith('doar_cenoura'):
                message_id = call.message.message_id
                doar_cenoura(call,message_id)    
            elif call.data.startswith("bpronomes_"):
                try:
                    mostrar_opcoes_pronome(call.message.chat.id, call.message.message_id)
                except Exception as e:
                    import traceback
                    traceback.print_exc()
            elif call.data.startswith("liberar_beta"):
                try:

                    message_id = call.message.message_id
                    usuario = call.message.chat.first_name
                    id_usuario = call.message.chat.id
                    
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                    text="Por favor, envie o ID da pessoa a ser liberada no beta:")                    
                    bot.register_next_step_handler(message, obter_id_beta)

                except Exception as e:
                    bot.reply_to(message, f"Ocorreu um erro: {e}")

            elif call.data.startswith("remover_beta"):
                try:

                    message_id = call.message.message_id
                    usuario = call.message.chat.first_name
                    id_usuario = call.message.chat.id
                    
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                    text="Por favor, envie o ID da pessoa a ser removida do beta:")                    
                    bot.register_next_step_handler(message, remover_beta)

                except Exception as e:
                    bot.reply_to(message, f"Ocorreu um erro: {e}")
                            
            elif call.data.startswith("beta_"):
                
                try:
                    message_id = call.message.message_id
                    usuario = call.message.chat.first_name
                    id_usuario = call.message.chat.id

                    markup = types.InlineKeyboardMarkup()
                    btn_cenoura = types.InlineKeyboardButton("🥕 Liberar Usuario", callback_data=f"liberar_beta")
                    btn_iscas = types.InlineKeyboardButton("🐟 Remover Usuario", callback_data=f"remover_beta")
                    btn_5 = types.InlineKeyboardButton("❌ Cancelar", callback_data=f"pcancelar")
                    markup.row(btn_cenoura, btn_iscas)
                    markup.row(btn_5)

                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                    text="Escolha o que deseja fazer:",reply_markup=markup)                    
                   
                except Exception as e:
                    import traceback
                    traceback.print_exc()

                    
            elif call.data.startswith("verificarban_"):
                verificar_ban(call)
                  
            elif call.data.startswith("ban_"):
                
                try:
                    message_id = call.message.message_id
                    usuario = call.message.chat.first_name
                    id_usuario = call.message.chat.id
                    
                    markup = types.InlineKeyboardMarkup()
                    btn_cenoura = types.InlineKeyboardButton("🚫 Banir", callback_data=f"banir_{id_usuario}")
                    btn_iscas = types.InlineKeyboardButton("🔍 Verificar Banimento", callback_data=f"verificarban_{id_usuario}")
                    btn_5 = types.InlineKeyboardButton("❌ Cancelar", callback_data=f"pcancelar")
                    markup.row(btn_cenoura, btn_iscas)
                    markup.row(btn_5)

                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                    text="Escolha o que deseja fazer:",reply_markup=markup)                    
                   
                except Exception as e:
                    import traceback
                    traceback.print_exc()
            elif call.data.startswith("novogif"):
                processar_comando_gif(message)
            elif call.data.startswith("delgif"):
                processar_comando_delgif(message)             
            elif call.data.startswith("gif_"):
                try:
                    message_id = call.message.message_id
                    usuario = call.message.chat.first_name
                    id_usuario = call.message.chat.id

                    markup = types.InlineKeyboardMarkup()
                    btn_cenoura = types.InlineKeyboardButton("Alterar gif", callback_data=f"novogif")
                    btn_iscas = types.InlineKeyboardButton("Deletar Gif", callback_data=f"delgif")
                    btn_5 = types.InlineKeyboardButton("❌ Cancelar", callback_data=f"pcancelar")
                    markup.row(btn_cenoura, btn_iscas)
                    markup.row(btn_5)

                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                    text="Escolha o que deseja fazer:",reply_markup=markup)                    
                   
                except Exception as e:
                    import traceback
                    traceback.print_exc()    
            elif call.data.startswith("tag"):
                    try:
                        parts = call.data.split('_')
                        pagina = int(parts[1])
                        nometag = parts[2]
                        id_usuario = call.from_user.id 
                        editar_mensagem_tag(message, nometag, pagina,id_usuario)
                    except Exception as e:
                        print(f"Erro ao processar callback de página para a tag: {e}")
            
            elif call.data.startswith("admdar_"):
                
                try:
                    message_id = call.message.message_id
                    usuario = call.message.chat.first_name
                    id_usuario = call.message.chat.id

                    markup = types.InlineKeyboardMarkup()
                    btn_cenoura = types.InlineKeyboardButton("🥕 Dar Cenouras", callback_data=f"dar_cenoura_{id_usuario}")
                    btn_iscas = types.InlineKeyboardButton("🐟 Dar Iscas", callback_data=f"dar_iscas_{id_usuario}")
                    btn_1 = types.InlineKeyboardButton("🥕 Tirar Cenouras", callback_data=f"tirar_cenoura_{id_usuario}")
                    btn_2 = types.InlineKeyboardButton("🐟 Tirar Iscas", callback_data=f"tirar_isca_{id_usuario}")
                    btn_5 = types.InlineKeyboardButton("❌ Cancelar", callback_data=f"pcancelar")
                    markup.row(btn_cenoura, btn_iscas)
                    markup.row(btn_1, btn_2)
                    markup.row(btn_5)

                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                    text="Escolha o que deseja fazer:",reply_markup=markup)                    
                   
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    
            elif call.data.startswith("dar_cenoura"):
                try:
                    message_id = call.message.message_id
                    usuario = call.message.chat.first_name
                    id_usuario = call.message.chat.id

                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                    text="Por favor, envie o ID da pessoa junto da quantidade de cenouras a adicionar:")                    
                    bot.register_next_step_handler(message, obter_id_cenouras)

                except Exception as e:
                    bot.reply_to(message, f"Ocorreu um erro: {e}")
                    
            elif call.data.startswith("dar_iscas"):
                try:

                    message_id = call.message.message_id
                    usuario = call.message.chat.first_name
                    id_usuario = call.message.chat.id

                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                    text="Por favor, envie o ID da pessoa junto da quantidade de iscas a adicionar:")                    
                    bot.register_next_step_handler(message, obter_id_iscas)
                except Exception as e:
                    bot.reply_to(message, f"Ocorreu um erro: {e}")
                    
            elif call.data.startswith("tirar_cenoura"):
                try:
                    message_id = call.message.message_id
                    usuario = call.message.chat.first_name
                    id_usuario = call.message.chat.id

                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                    text="Por favor, envie o ID da pessoa junto da quantidade de cenouras a retirar:")                    
                    bot.register_next_step_handler(message, adicionar_iscas)
                except Exception as e:
                    bot.reply_to(message, f"Ocorreu um erro: {e}")
                    
            elif call.data.startswith("tirar_isca"):
                try:
                    message_id = call.message.message_id
                    usuario = call.message.chat.first_name
                    id_usuario = call.message.chat.id

                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                    text="Por favor, envie o ID da pessoa junto da quantidade de iscas a retirar:")
                    bot.register_next_step_handler(message, remover_id_iscas)

                except Exception as e:
                    bot.reply_to(message, f"Ocorreu um erro: {e}")    
                        
            elif call.data.startswith("privacy"):
                message_id = call.message.message_id
                usuario = call.message.chat.first_name
                id_usuario = call.message.chat.id

                status_perfil = obter_privacidade_perfil(id_usuario)

                editar_mensagem_privacidade(call.message.chat.id, message_id, usuario, id_usuario, status_perfil)

            elif call.data == 'open_profile':
                atualizar_privacidade_perfil(call.message.chat.id, privacidade=False)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                    text="Perfil alterado para aberto.")

            elif call.data == 'lock_profile':
                atualizar_privacidade_perfil(call.message.chat.id, privacidade=True)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                    text="Perfil alterado para trancado.")
            elif call.data == 'pcancelar':
                bot.delete_message(call.message.chat.id, call.message.message_id)     
         
            elif call.data.startswith("pronomes_"):
                pronome = call.data.replace('pronomes_', '')  
                print(pronome)
                if pronome == 'remove':
                    pronome = None 
                    atualizar_pronome(call.message.chat.id, pronome)
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                        text="Pronome removido com sucesso.")
                else:
                    atualizar_pronome(call.message.chat.id, pronome)
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                        text=f"Pronome atualizado para: {pronome.capitalize()}")

            elif call.data.startswith("confirmar_compra_"):
                try:
                    data_atual = dt_module.date.today().strftime("%Y-%m-%d")  
                    parts = call.data.split('_')
                    categoria = parts[2]
                    id_usuario = parts[3]

                    cursor.execute(
                        "SELECT p.id_personagem, p.nome, p.subcategoria, p.imagem, p.emoji "
                        "FROM loja AS l "
                        "JOIN personagens AS p ON l.id_personagem = p.id_personagem "
                        "WHERE l.categoria = %s AND l.data = %s ORDER BY RAND() LIMIT 1",
                        (categoria, data_atual)
                    )
                    carta_comprada = cursor.fetchone()

                    if carta_comprada:
                        id_personagem, nome, subcategoria, imagem, emoji = carta_comprada
                        mensagem = f"𝐂𝐨𝐦𝐩𝐫𝐚 𝐟𝐞𝐢𝐭𝐚 𝐜𝐨𝐦 𝐬𝐮𝐜𝐞𝐬𝐬𝐨! \n\nO seguinte peixe foi adicionado à sua cesta: \n\n{emoji} <code>{id_personagem}</code> • {nome}\nde {subcategoria}\n\n𝐕𝐨𝐥𝐭𝐞 𝐬𝐞𝐦𝐩𝐫𝐞!"
                        add_to_inventory(id_usuario, id_personagem)
                        cursor.execute("SELECT cenouras FROM usuarios WHERE id_usuario = %s", (id_usuario,))
                        quantidade = cursor.fetchone()
                        res = functools.reduce(lambda sub, ele: sub * 10 + ele, quantidade)
                        valor = 5
                        diminuir_cenouras(id_usuario, valor)

                        bot.edit_message_media(
                            chat_id=message.chat.id,
                            message_id=message.message_id,
                            media=telebot.types.InputMediaPhoto(media=imagem,
                                                                caption=mensagem,parse_mode="HTML")
                            
                        )
                    else:
                        print(f"Nenhuma carta disponível para compra na categoria {categoria} hoje.")
                except Exception as e:
                    print(f"Erro ao processar a compra: {e}")
                finally:
                    fechar_conexao(cursor, conn)
            elif call.data.startswith('troca_'):
                troca_callback(call)
    except Exception as e:
        import traceback
        traceback.print_exc()

@bot.message_handler(commands=['youcompat'])
def youcompat_command(message):
    try:
        if not message.reply_to_message:
            bot.reply_to(message, "Você precisa usar este comando em resposta a uma mensagem de outro usuário.")
            return

        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "Uso: /youcompat <subcategoria>")
            return
        
        subcategoria = ' '.join(args[1:])
        subcategoria = verificar_apelido(subcategoria)
        subcategoria_titulo = subcategoria.title()
        
        id_usuario_1 = message.from_user.id
        nome_usuario_1 = message.from_user.first_name
        id_usuario_2 = message.reply_to_message.from_user.id
        nome_usuario_2 = message.reply_to_message.from_user.first_name

        conn, cursor = conectar_banco_dados()

        query = """
        SELECT inv.id_personagem, per.nome
        FROM inventario inv
        JOIN personagens per ON inv.id_personagem = per.id_personagem
        WHERE inv.id_usuario = %s AND per.subcategoria = %s
        """
        cursor.execute(query, (id_usuario_1, subcategoria))
        personagens_usuario_1 = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute(query, (id_usuario_2, subcategoria))
        personagens_usuario_2 = {row[0]: row[1] for row in cursor.fetchall()}

        diferenca = set(personagens_usuario_1.keys()) - set(personagens_usuario_2.keys())
        mensagem = f"<b>🎀 COMPATIBILIDADE 🎀 \n\n</b>🍎 | <b><i>{subcategoria_titulo}</i></b>\n🧺 |<b> Cesta de:</b> {nome_usuario_1} \n⛈️ | <b>Faltantes de:</b> {nome_usuario_2} \n\n"

        if diferenca:
            for id_personagem in diferenca:
                mensagem += f"<code>{id_personagem}</code> - {personagens_usuario_1.get(id_personagem)}\n"
        else:
            mensagem = "Parece que não temos um match. Tente outra espécie!"

        bot.send_message(message.chat.id, mensagem, parse_mode="HTML", reply_to_message_id=message.id)

    except Exception as e:
        bot.reply_to(message, f"Ocorreu um erro ao processar o comando: {e}")

    finally:
        fechar_conexao(cursor, conn)

@bot.message_handler(commands=['mecompat'])
def mecompat_command(message):
    conn, cursor = conectar_banco_dados()
    try:
        if not message.reply_to_message:
            bot.reply_to(message, "Você precisa usar este comando em resposta a uma mensagem de outro usuário.")
            return

        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "Uso: /mecompat <subcategoria>")
            return
        
        subcategoria = ' '.join(args[1:])
        subcategoria = verificar_apelido(subcategoria)
        subcategoria_titulo = subcategoria.title()
        
        id_usuario_1 = message.from_user.id
        nome_usuario_1 = message.from_user.first_name
        id_usuario_2 = message.reply_to_message.from_user.id
        nome_usuario_2 = message.reply_to_message.from_user.first_name

        query = """
        SELECT inv.id_personagem, per.nome
        FROM inventario inv
        JOIN personagens per ON inv.id_personagem = per.id_personagem
        WHERE inv.id_usuario = %s AND per.subcategoria = %s
        """
        cursor.execute(query, (id_usuario_1, subcategoria))
        personagens_usuario_1 = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute(query, (id_usuario_2, subcategoria))
        personagens_usuario_2 = {row[0]: row[1] for row in cursor.fetchall()}

        diferenca = set(personagens_usuario_2.keys()) - set(personagens_usuario_1.keys())
        mensagem = f"<b>🎀 COMPATIBILIDADE 🎀 \n\n</b>🍎 | <b><i>{subcategoria_titulo}</i></b>\n🧺 |<b> Cesta de:</b> {nome_usuario_2} \n⛈️ | <b>Faltantes de:</b> {nome_usuario_1} \n\n"

        if diferenca:
            for id_personagem in diferenca:
                mensagem += f"<code>{id_personagem}</code> - {personagens_usuario_2.get(id_personagem)}\n"
        else:
            mensagem = "Parece que não temos um match."

        bot.send_message(message.chat.id, mensagem, parse_mode="HTML", reply_to_message_id=message.id)

    except Exception as e:
        bot.reply_to(message, f"Ocorreu um erro ao processar o comando: {e}")
    finally:
        fechar_conexao(cursor, conn)

@bot.message_handler(commands=['diary'])
def diary_command(message):
    user_id = message.from_user.id
    today = date.today()
    
    conn, cursor = conectar_banco_dados()
    
    try:
        cursor.execute("SELECT ultimo_diario, dias_consecutivos FROM diario WHERE id_usuario = %s", (user_id,))
        result = cursor.fetchone()

        if result:
            ultimo_diario, dias_consecutivos = result

            if ultimo_diario == today:
                bot.send_message(message.chat.id, "Você já recebeu suas cenouras hoje. Volte amanhã!")
                return

            if ultimo_diario == today - timedelta(days=1):
                dias_consecutivos += 1
            else:
                dias_consecutivos = 1

            if dias_consecutivos <= 10:
                cenouras = dias_consecutivos * 10
            else:
                cenouras = 100

            cursor.execute("UPDATE diario SET ultimo_diario = %s, dias_consecutivos = %s WHERE id_usuario = %s", (today, dias_consecutivos, user_id))
            cursor.execute("UPDATE usuarios SET cenouras = cenouras + %s WHERE id_usuario = %s", (cenouras, user_id))
            conn.commit()
        else:

            cenouras = 10
            dias_consecutivos = 1
            cursor.execute("INSERT INTO diario (id_usuario, ultimo_diario, dias_consecutivos) VALUES (%s, %s, %s)", (user_id, today, dias_consecutivos))
            cursor.execute("UPDATE usuarios SET cenouras = cenouras + %s WHERE id_usuario = %s", (cenouras, user_id))
            conn.commit()

        phrase = random.choice(phrases)
        fortune = random.choice(fortunes)
        bot.send_message(message.chat.id, f"<i>{phrase}</i>\n\n<b>{fortune}</b>\n\nVocê recebeu <i>{cenouras} cenouras</i>!\n\n <b>Dias consecutivos:</b> <i>{dias_consecutivos}</i>\n\n",parse_mode="HTML")

        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(text="Sim", callback_data="add_note"))
        markup.add(telebot.types.InlineKeyboardButton(text="Não", callback_data="cancael_note"))
        bot.send_message(message.chat.id, "Deseja anotar algo nesse dia especial?", reply_markup=markup)

    except mysql.connector.Error as err:
        print(f"Erro ao processar o comando /diary: {err}")
        bot.send_message(message.chat.id, "Ocorreu um erro ao tentar registrar seu diário. Tente novamente mais tarde.")
    finally:
        fechar_conexao(cursor, conn)

@bot.message_handler(commands=['pages'])
def pages_command(message):
    user_id = message.from_user.id

    conn, cursor = conectar_banco_dados()

    try:
        cursor.execute("SELECT data, anotacao FROM anotacoes WHERE id_usuario = %s ORDER BY data DESC", (user_id,))
        anotacoes = cursor.fetchall()

        if not anotacoes:
            bot.send_message(message.chat.id, "Você ainda não tem anotações no diário.")
            return

        response = ""
        total_anotacoes = len(anotacoes)
        # Mantém a ordem das datas, mas inverte o número da página
        for i, (data, anotacao) in enumerate(anotacoes, 1):
            page_number = total_anotacoes - i + 1  # Calcula o número da página em ordem inversa
            response += f"Dia {page_number} - {data.strftime('%d/%m/%Y')}\n"
        
        bot.send_message(message.chat.id, response)

    except mysql.connector.Error as err:
        print(f"Erro ao obter anotações: {err}")
        bot.send_message(message.chat.id, "Ocorreu um erro ao tentar obter suas anotações. Tente novamente mais tarde.")
    finally:
        fechar_conexao(cursor, conn)

@bot.message_handler(commands=['page'])
def page_command(message):
    user_id = message.from_user.id
    params = message.text.split(' ', 1)[1:]
    if len(params) < 1:
        bot.send_message(message.chat.id, "Uso: /page <número_da_página>")
        return
    page_number = int(params[0])

    conn, cursor = conectar_banco_dados()

    try:
        cursor.execute("SELECT data, anotacao FROM anotacoes WHERE id_usuario = %s ORDER BY data DESC", (user_id,))
        anotacoes = cursor.fetchall()

        if not anotacoes:
            bot.send_message(message.chat.id, "Você ainda não tem anotações no diário.")
            return

        if page_number < 1 or page_number > len(anotacoes):
            bot.send_message(message.chat.id, "Número de página inválido.")
            return

        data, anotacao = anotacoes[page_number - 1]
        response = f"Mabigarden, dia {data.strftime('%d/%m/%Y')}\n\nQuerido diário... {anotacao}"
        
        bot.send_message(message.chat.id, response)

    except mysql.connector.Error as err:
        print(f"Erro ao obter anotação: {err}")
        bot.send_message(message.chat.id, "Ocorreu um erro ao tentar obter sua anotação. Tente novamente mais tarde.")
    finally:
        fechar_conexao(cursor, conn)                      

@bot.message_handler(commands=['wishlist'])
def verificar_cartas(message):
    try:
        conn, cursor = conectar_banco_dados()
        id_usuario = message.from_user.id

        sql_wishlist = f"""
            SELECT p.id_personagem, p.nome AS nome_personagem, p.subcategoria, p.emoji
            FROM wishlist w
            JOIN personagens p ON w.id_personagem = p.id_personagem
            WHERE w.id_usuario = {id_usuario}
            
            UNION
            
            SELECT e.id_personagem, e.nome AS nome_personagem, e.subcategoria, e.emoji
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

            bot.send_message(message.chat.id, lista_wishlist_atualizada, reply_to_message_id=message.message_id,parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, "Sua wishlist está vazia! Devo te desejar parabéns?", reply_to_message_id=message.message_id)

    except mysql.connector.Error as err:
        print(f"Erro de SQL: {err}")
        bot.send_message(message.chat.id, "Ocorreu um erro ao processar a consulta no banco de dados.", reply_to_message_id=message.message_id)
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


@bot.message_handler(commands=['ping'])
def ping_command(message):
    start_time = time.time()
    chat_id = message.chat.id

    # Enviar uma mensagem de ping para calcular o tempo de resposta
    sent_message = bot.send_message(chat_id, "Calculando o ping...")

    # Calcular o ping
    ping = time.time() - start_time

    # Obter o número de tarefas na fila
    queue_size = task_queue.qsize()

    # Editar a mensagem com o ping e o número de tarefas na fila
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=sent_message.message_id,
        text=f"🏓 Pong!\nPing: {ping:.2f} segundos\nTarefas na fila: {queue_size}"
    )
@bot.message_handler(commands=['removew'])
@bot.message_handler(commands=['delw'])
def remover_da_wishlist(message):
    try:
        chat_id = message.chat.id
        id_usuario = message.from_user.id
        command_parts = message.text.split()
        if len(command_parts) == 2:
            id_personagem = command_parts[1]
            
        conn, cursor = conectar_banco_dados()
        cursor.execute("SELECT COUNT(*) FROM wishlist WHERE id_usuario = %s AND id_personagem = %s",
                       (id_usuario, id_personagem))
        existing_carta_count = cursor.fetchone()[0]

        if existing_carta_count > 0:
            cursor.execute("DELETE FROM wishlist WHERE id_usuario = %s AND id_personagem = %s",
                           (id_usuario, id_personagem))
            bot.send_message(chat_id=chat_id, text="Carta removida da sua wishlist!", reply_to_message_id=message.message_id)
        else:
            bot.send_message(chat_id=chat_id, text="Você não possui essa carta na wishlist.", reply_to_message_id=message.message_id)
        conn.commit()

    except mysql.connector.Error as err:
        print(f"Erro ao remover carta da wishlist: {err}")
    finally:
        fechar_conexao(cursor, conn)

@bot.message_handler(commands=['cenourar'])
def processar_verificar_e_cenourar(message):
    try:
        conn, cursor = conectar_banco_dados()
        id_usuario = message.from_user.id
        id_personagem = message.text.replace('/cenourar', '').strip()

        cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (id_usuario, id_personagem))
        quantidade_atual = cursor.fetchone()

        if quantidade_atual and quantidade_atual[0] >= 1:
            enviar_pergunta_cenoura(message, id_usuario, id_personagem, quantidade_atual[0])
        else:
            bot.send_message(message.chat.id, "Você não possui essa carta no inventário ou não tem quantidade suficiente.")
    except Exception as e:
        print(f"Erro ao processar o comando de cenourar: {e}")
        bot.send_message(message.chat.id, "Erro ao processar o comando de cenourar.")
    finally:
        cursor.close()
        conn.close()

@bot.message_handler(commands=['setbio'])
def set_bio_command(message):

    id_usuario = message.from_user.id
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) == 2:
        nova_bio = command_parts[1].strip()
        atualizar_coluna_usuario(id_usuario, 'bio', nova_bio)
        bot.send_message(message.chat.id, f"Bio do {id_usuario} atualizada para: {nova_bio}")
    else:
        bot.send_message(message.chat.id, "Formato incorreto. Use /setbio seguido da nova bio desejada, por exemplo: /setbio Hhmm, bolo de morango.")
        
@bot.message_handler(commands=['setgif'])
def enviar_gif(message):
    try:
        comando = message.text.split('/setgif', 1)[1].strip().lower()
        partes_comando = comando.split(' ')
        id_personagem = partes_comando[0]
        id_usuario = message.from_user.id

        conn, cursor = conectar_banco_dados()

        # Verificar se o usuário possui 30 unidades da carta
        cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (id_usuario, id_personagem))
        resultado = cursor.fetchone()
        if not resultado or resultado[0] < 30:
            bot.send_message(message.chat.id, "Você precisa ter pelo menos 30 unidades dessa carta para enviar um gif.")
            fechar_conexao(cursor, conn)
            return

        if 'eusoqueriasernormal' not in partes_comando:
            tempo_restante = verifica_tempo_ultimo_gif(id_usuario)
            if tempo_restante:
                bot.send_message(message.chat.id, f"Você já enviou um gif recentemente. Aguarde {tempo_restante} antes de enviar outro.")
                fechar_conexao(cursor, conn)
                return

        bot.send_message(message.chat.id, "Eba! Você pode escolher um gif!\nEnvie o link do gif gerado pelo @UploadTelegraphBot:")
        globals.links_gif[message.from_user.id] = id_personagem
        bot.register_next_step_handler(message, receber_link_gif, id_personagem)

        fechar_conexao(cursor, conn)

    except IndexError:
        bot.send_message(message.chat.id, "Por favor, forneça o ID do personagem.")
    except Exception as e:
        print(f"Erro ao processar o comando /setgif: {e}")
        fechar_conexao(cursor, conn)

@bot.message_handler(commands=['admin'])
def doar(message):
    try:
        id_usuario = message.from_user.id
        if verificar_autorizacao(id_usuario):
            markup = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton('👨‍🌾 Beta', callback_data='beta_')
            btn2 = types.InlineKeyboardButton('🐟 Adicionar ou Remover', callback_data='admdar_')
            btn3 = types.InlineKeyboardButton('🚫 Banir', callback_data='banir_')
            btn4 = types.InlineKeyboardButton('GIFS', callback_data='gif_')
            btn_cancelar = types.InlineKeyboardButton('❌ Cancelar', callback_data='pcancelar')
            markup.add(btn1, btn2, btn3)
            markup.add(btn4, btn_cancelar)
            bot.send_message(message.chat.id, "Escolha uma opção:", reply_markup=markup)
        else:
            bot.reply_to(message, "Você não está autorizado.")

    except Exception as e:
        import traceback
        traceback.print_exc()

# Lista de IDs permitidos
allowed_user_ids = [5121550670, 5532809878, 531165369, 1805086442]
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
def loja(message):
    try:
        verificar_id_na_tabela(message.from_user.id, "ban", "iduser")
        keyboard = telebot.types.InlineKeyboardMarkup()

        keyboard.row(telebot.types.InlineKeyboardButton(text="🎣 Peixes do dia", callback_data='loja_loja'))
        keyboard.row(telebot.types.InlineKeyboardButton(text="🎴 Estou com sorte", callback_data='loja_geral'))
        keyboard.row(telebot.types.InlineKeyboardButton(text="⛲ Fonte dos Desejos", callback_data='fazer_pedido'))
        keyboard.row(telebot.types.InlineKeyboardButton(text="💼 Pacotes de Ações", callback_data='acoes_vendinha'))

        image_url = "https://telegra.ph/file/ea116d98a5bd8d6179612.jpg"
        bot.send_photo(message.chat.id, image_url,
                       caption='Olá! Seja muito bem-vindo à vendinha da Mabi. Como posso te ajudar?',
                       reply_markup=keyboard, reply_to_message_id=message.message_id)

    except ValueError as e:
        print(f"Erro: {e}")
        mensagem_banido = "Você foi banido permanentemente do garden. Entre em contato com o suporte caso haja dúvidas."
        bot.send_message(message.chat.id, mensagem_banido, reply_to_message_id=message.message_id)
      
@bot.message_handler(commands=['peixes'])
def verificar_comando_peixes(message):
    try:
        parametros = message.text.split(' ', 2)[1:]  

        if not parametros:
            bot.reply_to(message, "Por favor, forneça a subcategoria.")
            return
        
        subcategoria = " ".join(parametros)  
        
        if len(parametros) > 1 and parametros[0] == 'img':
            subcategoria = " ".join(parametros[1:])
            enviar_imagem_peixe(message, subcategoria)
        else:
            mostrar_lista_peixes(message, subcategoria)
        
    except Exception as e:
        print(f"Erro ao processar comando /peixes: {e}")
        bot.reply_to(message, "Ocorreu um erro ao processar sua solicitação.")
        
@bot.message_handler(commands=['colagem'])
def criar_colagem(message):
    try:

        if len(message.text.split()) != 7:
            bot.reply_to(message, "Por favor, forneça exatamente 6 IDs de cartas separados por espaços.")
            return
        ids_cartas = message.text.split()[1:]
        imagens = []
        
        for id_carta in ids_cartas:
            img_url = obter_url_imagem_por_id(id_carta)
            if img_url:
                print(id_carta)
                response = requests.get(img_url)
                if response.status_code == 200:
                    img = Image.open(io.BytesIO(response.content))
                    img = manter_proporcoes(img, 300, 400)  
                else:
                    img = Image.new('RGB', (300, 400), color='black')
            else:
                img = Image.new('RGB', (300, 400), color='black')
            imagens.append(img)
        
        altura_total = ((len(imagens) - 1) // 3 + 1) * 400
        colagem = Image.new('RGB', (900, altura_total))  
        coluna_atual = 0
        linha_atual = 0

        for img in imagens:
            colagem.paste(img, (coluna_atual, linha_atual))
            coluna_atual += 300

            if coluna_atual >= 900:
                coluna_atual = 0
                linha_atual += 400

        colagem_path = 'colagem_cartas.png'
        colagem.save(colagem_path)

        with open(colagem_path, 'rb') as photo:
            bot.send_photo(message.chat.id, photo)

    except Exception as e:
        print(f"Erro ao criar colagem: {e}")
        bot.reply_to(message, "Erro ao criar colagem.")

@bot.message_handler(commands=['enviar_mensagem'])
def enviar_mensagem_privada(message):
    try:

        if len(message.text.split()) < 3:
            bot.reply_to(message, "Formato incorreto. Use /enviar_mensagem <id_usuario> <sua_mensagem>")
            return

        _, user_id, *mensagem = message.text.split(maxsplit=2)
        user_id = int(user_id)
        mensagem = mensagem[0]

        bot.send_message(user_id, mensagem)
        
        bot.reply_to(message, f"Mensagem enviada para o usuário {user_id} com sucesso!")
        
    except ValueError:
        bot.reply_to(message, "ID de usuário inválido. Certifique-se de fornecer um número inteiro válido.")
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")
        bot.reply_to(message, "Ocorreu um erro ao enviar a mensagem.")

@bot.message_handler(commands=['enviar_grupo'])
def enviar_mensagem_grupo(message):
    try:

        if len(message.text.split()) < 3:
            bot.reply_to(message, "Formato incorreto. Use /enviar_grupo <id_grupo> <sua_mensagem>")
            return
        
        _, group_id, *mensagem = message.text.split(maxsplit=2)
        group_id = int(group_id)
        mensagem = mensagem[0]

        bot.send_message(group_id, mensagem)

        bot.reply_to(message, f"Mensagem enviada para o grupo {group_id} com sucesso!")
        
    except ValueError:
        bot.reply_to(message, "ID de grupo inválido. Certifique-se de fornecer um número inteiro válido.")
    except Exception as e:
        print(f"Erro ao enviar mensagem para o grupo: {e}")
        bot.reply_to(message, "Ocorreu um erro ao enviar a mensagem para o grupo.")


@bot.message_handler(commands=['legenda'])
def gerar_legenda(message):
    try:
        ids_cartas = message.text.split('/legenda')[1].strip().split()
        if len(ids_cartas) < 1:
            bot.send_message(message.chat.id, "Informe pelo menos um ID de carta.")
            return
        mensagem_legenda = "Legenda:\n\n"
        for id_carta in ids_cartas:
            info_carta = obter_info_carta_por_id(id_carta)
            if info_carta:
                mensagem_legenda += f"{info_carta['emoji']} | {info_carta['id']} • {info_carta['nome']} - {info_carta['subcategoria']}\n"
            else:
                mensagem_legenda += f"ID {id_carta} não encontrado.\n"

        bot.send_message(message.chat.id, mensagem_legenda, reply_to_message_id=message.message_id)
    except Exception as e:
        print(f"Erro ao processar comando /legenda: {e}")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    if message.chat.type == 'private':
        registrar_mensagens_privadas(message)

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
           
time.sleep(0.1)

bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,drop_pending_updates=True )

app.run(host=WEBHOOK_LISTEN, port=WEBHOOK_PORT, debug=True)

