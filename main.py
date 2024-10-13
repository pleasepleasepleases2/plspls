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
from songs import *
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
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
from PIL import Image, ImageFilter
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
from halloween import *
from vips import *
from petalas import *
import logging
import flask
import http.server
import newrelic.agent
from datetime import datetime, timedelta
import socketserver
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from PIL import Image, UnidentifiedImageError, ImageOps
import random
import os
import tempfile
import requests
from io import BytesIO
processing_lock = threading.Lock()
ids_proibidos = {164, 165, 163, 174, 192, 214, 215, 216}
scheduler = BackgroundScheduler(timezone=utc)
scheduler.start()
API_TOKEN="7088149058:AAEoZ7PsVgaOAFDcW9q1t28k5Pj11o-6LCU"
SPOTIFY_CLIENT_ID="804047efa98c4d1d81da250b0770c05d"
SPOTIFY_CLIENT_SECRET="6deb00cb4cea42f79abe41cc4da05f13"
DB_HOST="mysql.railway.internal"
DB_USER="root"
DB_PASS="ZGDCREJXfzPkyqxisMhnwAcJhtbYkfge"
DB_NAME="garden"
WEBHOOK_URL_BASE = "https://plspls-production.up.railway.app/"

WEBHOOK_URL_PATH = '/' + API_TOKEN + '/'
WEBHOOK_LISTEN = "0.0.0.0"
WEBHOOK_PORT = int(os.getenv('PORT', 5000))  #

bot = telebot.TeleBot(API_TOKEN)
app = flask.Flask(__name__)
newrelic.agent.initialize('newrelic.ini')

grupodeerro = -1002209493474
GRUPO_SUGESTOES = -4546359573
cache_musicas_editadas = dc.Cache('./cache_musicas_editadas')
song_cooldown_cache = TTLCache(maxsize=1000, ttl=15)  # 3 horas de cooldown
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET))
cache = dc.Cache('./cache')  
conn, cursor = conectar_banco_dados()
task_queue = Queue()


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
def iniciar_jogo(message):
    try:
        id_usuario = message.from_user.id
        tabuleiro = inicializar_tabuleiro()
        jogos_da_velha[id_usuario] = tabuleiro
        
        bot.send_message(message.chat.id, f"Vamos jogar Jogo da Velha! Você é o '✔️' e eu sou o '❌'.\n\n{mostrar_tabuleiro(tabuleiro)}")
        
        markup = criar_botoes_tabuleiro(tabuleiro)
        bot.send_message(message.chat.id, "Escolha sua jogada (1-9):", reply_markup=markup)
    except Exception as e:
        print(f"Erro ao processar o jogo da velha): {e}")
        traceback.print_exc()

@bot.message_handler(commands=['picnic'])
@bot.message_handler(commands=['trocar'])
@bot.message_handler(commands=['troca'])
def trade(message):
    try:
        print("Comando troca acionado")
        chat_id = message.chat.id
        eu = message.from_user.id
        voce = message.reply_to_message.from_user.id
        seunome = message.reply_to_message.from_user.first_name
        meunome = message.from_user.first_name
        bot_id = 7088149058
        categoria = message.text.replace('/troca', '')
        minhacarta = message.text.split()[1]
        suacarta = message.text.split()[2]

        print(f"Dados da troca: eu={eu}, voce={voce}, minhacarta={minhacarta}, suacarta={suacarta}")

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
        mensagem = f"Erro durante a troca. dados: {voce},{eu},{minhacarta},{suacarta}\n{erro}"
        bot.send_message(grupodeerro, mensagem, parse_mode="HTML")
        newrelic.agent.record_exception()



@bot.callback_query_handler(func=lambda call: call.data.startswith('jogada_'))
def jogador_fazer_jogada(call):
    try: 
        id_usuario = call.from_user.id
        if id_usuario not in jogos_da_velha:
            bot.send_message(call.message.chat.id, "Você não iniciou um jogo da velha. Use /jogodavelha para começar.")
            return
    
        if call.data == "jogada_disabled":
            bot.answer_callback_query(call.id, "Essa posição já está ocupada!")
            return
    
        tabuleiro = jogos_da_velha[id_usuario]
        _, i, j = call.data.split('_')
        i, j = int(i), int(j)
        
        if tabuleiro[i][j] != '⬜':
            bot.answer_callback_query(call.id, "Essa posição já está ocupada!")
            return
        
        tabuleiro[i][j] = '✔️'
        
        if verificar_vitoria(tabuleiro, '✔️'):
            bot.edit_message_text(f"🎉 Parabéns! Você venceu!\n\n{mostrar_tabuleiro(tabuleiro)}", call.message.chat.id, call.message.message_id)
            del jogos_da_velha[id_usuario]
            return
        
        if verificar_empate(tabuleiro):
            bot.edit_message_text(f"😐 Empate!\n\n{mostrar_tabuleiro(tabuleiro)}", call.message.chat.id, call.message.message_id)
            del jogos_da_velha[id_usuario]
            return
        
        tabuleiro = bot_fazer_jogada(tabuleiro, '❌', '✔️')
    
        if verificar_vitoria(tabuleiro, '❌'):
            bot.edit_message_text(f"😎 Eu venci! Melhor sorte da próxima vez.\n\n{mostrar_tabuleiro(tabuleiro)}", call.message.chat.id, call.message.message_id)
            del jogos_da_velha[id_usuario]
            return
        
        if verificar_empate(tabuleiro):
            bot.edit_message_text(f"😐 Empate!\n\n{mostrar_tabuleiro(tabuleiro)}", call.message.chat.id, call.message.message_id)
            del jogos_da_velha[id_usuario]
            return
        
        markup = criar_botoes_tabuleiro(tabuleiro)
        bot.edit_message_text(f"Seu turno!\n\n{mostrar_tabuleiro(tabuleiro)}", call.message.chat.id, call.message.message_id, reply_markup=markup)
    except Exception as e:
        print(f"Erro ao processar o jogo da velha): {e}")
        traceback.print_exc()
@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)
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
def iniciar_labirinto(message):
    try:
        id_usuario = message.from_user.id
        tamanho = 10  # Tamanho do labirinto (10x10 para mais complexidade)
        
        labirinto = gerar_labirinto_com_caminho_e_validacao(tamanho)
        posicao_inicial = (1, 1)  # O jogador começa em uma posição inicial fixa ou aleatória
        movimentos_restantes = 35  # Limite de movimentos para encontrar a saída
        
        globals.jogadores_labirinto[id_usuario] = {
            "labirinto": labirinto,
            "posicao": posicao_inicial,
            "movimentos": movimentos_restantes
        }
        
        mapa = mostrar_labirinto(labirinto, posicao_inicial)
        
        # Criar os botões de navegação
        markup = types.InlineKeyboardMarkup(row_width=4)
        botao_cima = types.InlineKeyboardButton("⬆️", callback_data="norte")
        botao_esquerda = types.InlineKeyboardButton("⬅️", callback_data="oeste")
        botao_direita = types.InlineKeyboardButton("➡️", callback_data="leste")
        botao_baixo = types.InlineKeyboardButton("⬇️", callback_data="sul")
        markup.add(botao_cima, botao_esquerda, botao_direita, botao_baixo)
        
        bot.send_message(message.chat.id, f"🏰 Bem-vindo ao Labirinto! Você tem {movimentos_restantes} movimentos para escapar.\n\n{mapa}", reply_markup=markup)
    except Exception as e:
        print(f"Erro ao processar o jogo da velha): {e}")
        traceback.print_exc()
@bot.callback_query_handler(func=lambda call: call.data in ['norte', 'sul', 'leste', 'oeste'])
def mover_labirinto(call):
    try:
        id_usuario = call.from_user.id
        if id_usuario not in jogadores_labirinto:
            bot.send_message(call.message.chat.id, "👻 Você precisa iniciar o labirinto primeiro com o comando /labirinto.")
            return
        
        direcao = call.data  # Pega a direção do botão clicado
        jogador = globals.jogadores_labirinto[id_usuario]
        labirinto = jogador["labirinto"]
        posicao_atual = jogador["posicao"]
        movimentos_restantes = jogador["movimentos"]
        
        nova_posicao = mover_posicao(posicao_atual, direcao, len(labirinto), labirinto)
        
        if nova_posicao != posicao_atual:  # Se a nova posição for válida
            jogadores_labirinto[id_usuario]["posicao"] = nova_posicao
            jogadores_labirinto[id_usuario]["movimentos"] -= 1
            movimentos_restantes -= 1
            conteudo = labirinto[nova_posicao[0]][nova_posicao[1]]
            
            # Verificar se o jogador chegou na saída
            if conteudo == '🚪':
                bot.edit_message_text(f"🏆 Parabéns! Você encontrou a saída e escapou do labirinto!\n\n{revelar_labirinto(labirinto)}",
                                      call.message.chat.id, call.message.message_id)
                del jogadores_labirinto[id_usuario]  # Remover o jogador do labirinto
            elif movimentos_restantes == 0:
                bot.edit_message_text(f"😢 Seus movimentos acabaram! Você não conseguiu escapar da maldição...\n\n{revelar_labirinto(labirinto)}",
                                      call.message.chat.id, call.message.message_id)
                del jogadores_labirinto[id_usuario]  # Fim do jogo, remover jogador
            else:
                mapa = mostrar_labirinto(labirinto, nova_posicao)
                # Revelar o conteúdo do bloco ao chegar nele
                if conteudo == '👻' or conteudo == '🎃':
                    # Remover o monstro ou abóbora do labirinto
                    labirinto[nova_posicao[0]][nova_posicao[1]] = '⬜'
                    
                    markup_opcoes = types.InlineKeyboardMarkup(row_width=2)
                    botao_encerrar = types.InlineKeyboardButton("Encerrar", callback_data="encerrar")
                    botao_continuar = types.InlineKeyboardButton("Continuar", callback_data="continuar")
                    markup_opcoes.add(botao_encerrar, botao_continuar)
                    
                    if conteudo == '👻':
                        bot.edit_message_text(f"👻 Você encontrou um monstro e perdeu 20 cenouras! Você quer encerrar ou continuar?\n\n{mapa}",
                                              call.message.chat.id, call.message.message_id, reply_markup=markup_opcoes)
                        conn, cursor = conectar_banco_dados()
                        cursor.execute("UPDATE usuarios SET cenouras = cenouras - 20 WHERE id_usuario = %s", (id_usuario,))
                        conn.commit()
                    elif conteudo == '🎃':
                        bot.edit_message_text(f"🎃 Você encontrou uma recompensa de 50 cenouras! Você quer encerrar ou continuar?\n\n{mapa}",
                                              call.message.chat.id, call.message.message_id, reply_markup=markup_opcoes)
                        conn, cursor = conectar_banco_dados()
                        cursor.execute("UPDATE usuarios SET cenouras = cenouras + 50 WHERE id_usuario = %s", (id_usuario,))
                        conn.commit()
                else:
                    # Atualizar os botões de navegação
                    markup = types.InlineKeyboardMarkup(row_width=4)
                    botao_cima = types.InlineKeyboardButton("⬆️", callback_data="norte")
                    botao_esquerda = types.InlineKeyboardButton("⬅️", callback_data="oeste")
                    botao_direita = types.InlineKeyboardButton("➡️", callback_data="leste")
                    botao_baixo = types.InlineKeyboardButton("⬇️", callback_data="sul")
                    markup.add(botao_cima, botao_esquerda, botao_direita, botao_baixo)
    
                    bot.edit_message_text(f"🌕 Você avançou pelo labirinto. Movimentos restantes: {movimentos_restantes}\n\n{mapa}",
                                          call.message.chat.id, call.message.message_id, reply_markup=markup)
        else:
            bot.answer_callback_query(call.id, "👻 Você não pode ir nessa direção!")
    except Exception as e:
        print(f"Erro ao processar o jogo da velha): {e}")
        traceback.print_exc()
@bot.callback_query_handler(func=lambda call: call.data in ['encerrar', 'continuar'])
def encerrar_ou_continuar(call):
    try:
        id_usuario = call.from_user.id
        if call.data == 'encerrar':
            bot.edit_message_text("💀 Você decidiu encerrar sua jornada no labirinto. Fim de jogo!", call.message.chat.id, call.message.message_id)
            del jogadores_labirinto[id_usuario]  # Remover jogador
        elif call.data == 'continuar':
            jogador = jogadores_labirinto[id_usuario]
            labirinto = jogador["labirinto"]
            posicao = jogador["posicao"]
            movimentos_restantes = jogador["movimentos"]
    
            # Atualizar a mensagem com o labirinto e botões de navegação
            mapa = mostrar_labirinto(labirinto, posicao)
            markup = types.InlineKeyboardMarkup(row_width=4)
            botao_cima = types.InlineKeyboardButton("⬆️", callback_data="norte")
            botao_esquerda = types.InlineKeyboardButton("⬅️", callback_data="oeste")
            botao_direita = types.InlineKeyboardButton("➡️", callback_data="leste")
            botao_baixo = types.InlineKeyboardButton("⬇️", callback_data="sul")
            markup.add(botao_cima, botao_esquerda, botao_direita, botao_baixo)
    
            bot.edit_message_text(f"🏃 Você decidiu continuar sua jornada! Movimentos restantes: {movimentos_restantes}\n\n{mapa}",
                                  call.message.chat.id, call.message.message_id, reply_markup=markup)

    except Exception as e:
        print(f"Erro ao processar o jogo da velha): {e}")
        traceback.print_exc()

def process_tasks():
    while True:
        task = task_queue.get()
        if task is None:
            break
        task()
        task_queue.task_done()
        
task_thread = threading.Thread(target=process_tasks)
task_thread.start()

@bot.message_handler(commands=['tinder'])
def tinder_cartas_command(message):
    try:
        carta = gerar_proxima_carta()
    
        id_carta, nome, subcategoria, emoji, categoria = carta
    
        # Montar a mensagem com as informações da carta
        mensagem_carta = (f"ID:<code>{id_carta}</code>\n"
                          f"Nome: {nome}\n"
                          f"Subcategoria: {subcategoria}\n"
                          f"Categoria:{emoji} - {categoria}")
    
        # Criar os botões de coração (gostar) e X (rejeitar)
        markup = types.InlineKeyboardMarkup()
        botao_coracao = types.InlineKeyboardButton("❤️", callback_data=f"gostar_{id_carta}")
        botao_x = types.InlineKeyboardButton("❌", callback_data=f"rejeitar_{id_carta}")
        markup.add(botao_coracao, botao_x)
    
        bot.send_message(message.chat.id, mensagem_carta, reply_markup=markup, parse_mode="HTML")
    except Exception as e:
        print(f"Erro ao processar o comando /tinder: {e}")
        traceback.print_exc()

@bot.callback_query_handler(func=lambda call: call.data.startswith('gostar_') or call.data.startswith('rejeitar_'))
def callback_tinder_cartas(call):
    try:
        id_carta = call.data.split("_")[1]
        id_usuario = call.from_user.id

        if call.data.startswith("gostar_"):
            if registrar_interacao(id_usuario, id_carta, gostou=True):
                bot.answer_callback_query(call.id, "Você gostou dessa carta!")
            else:
                bot.answer_callback_query(call.id, "Você já interagiu com essa carta antes.")
        elif call.data.startswith("rejeitar_"):
            if registrar_interacao(id_usuario, id_carta, gostou=False):
                bot.answer_callback_query(call.id, "Você rejeitou essa carta!")
            else:
                bot.answer_callback_query(call.id, "Você já interagiu com essa carta antes.")

        # Substituir os botões por um botão de "próxima carta"
        markup_nova_carta = types.InlineKeyboardMarkup()
        botao_proxima = types.InlineKeyboardButton("➡️", callback_data="proxima_carta")
        markup_nova_carta.add(botao_proxima)

        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup_nova_carta)
    except Exception as e:
        print(f"Erro ao processar o callback (gostar/rejeitar): {e}")
        traceback.print_exc()

@bot.callback_query_handler(func=lambda call: call.data == "proxima_carta")
def callback_proxima_carta(call):
    try:
        # Gerar a próxima carta
        carta = gerar_proxima_carta()
        id_carta, nome, subcategoria, emoji, categoria = carta

        # Montar a nova mensagem com as informações da nova carta
        mensagem_carta = (f"ID: <code>{id_carta}</code>\n"
                          f"Nome: {nome}\n"
                          f"Subcategoria: {subcategoria}\n"
                          f"Emoji: {emoji}\n"
                          f"Categoria: {categoria}")

        # Criar os botões de coração (gostar) e X (rejeitar)
        markup = types.InlineKeyboardMarkup()
        botao_coracao = types.InlineKeyboardButton("❤️", callback_data=f"gostar_{id_carta}")
        botao_x = types.InlineKeyboardButton("❌", callback_data=f"rejeitar_{id_carta}")
        markup.add(botao_coracao, botao_x)

        # Editar a mensagem existente com as novas informações e botões
        bot.edit_message_text(mensagem_carta, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
    except Exception as e:
        print(f"Erro ao processar o callback de próxima carta: {e}")
        traceback.print_exc()

@bot.message_handler(commands=['popularidade'])
def consultar_popularidade_command(message):
    mais_amadas, mais_rejeitadas = consultar_popularidade()
    
    # Construir a resposta
    resposta = "Cartas mais amadas:\n"
    for carta in mais_amadas:
        resposta += f"ID: <code>{carta[0]}</code> - ♡: {carta[1]} -  x: {carta[2]}\n"
    
    resposta += "\nCartas mais rejeitadas:\n"
    for carta in mais_rejeitadas: 
        resposta += f"ID: <code>{carta[0]}</code> - ♡: {carta[1]} - x: {carta[2]}\n"
    
    bot.send_message(message.chat.id, resposta, parse_mode="HTML")

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

        # Obter o nome e user da pessoa que sugeriu
        nome_usuario = message.from_user.first_name
        user_usuario = message.from_user.username

        # Montar a mensagem da sugestão
        sugestao_texto = (f"Sugestão recebida:\n"
                          f"Nome: {nome}\nSubcategoria: {subcategoria}\nCategoria: {categoria}\n"
                          f"Imagem: {imagem}\n"
                          f"Usuário: {nome_usuario} (@{user_usuario})")

        # Encaminhar para o grupo de sugestões
        bot.send_message(GRUPO_SUGESTOES, sugestao_texto)

    except Exception as e:
        print(f"Erro ao processar o comando /sugestao: {e}")
        bot.reply_to(message, "Ocorreu um erro ao processar sua sugestão. Tente novamente.")

@bot.message_handler(commands=['ranking_semanal'])
def ranking_semanal(message):
    try:
        conn, cursor = conectar_banco_dados()


        hoje = datetime.now()
        inicio_semana = hoje - timedelta(days=hoje.weekday() + 7)
        fim_semana = inicio_semana + timedelta(days=6, hours=23, minutes=59, seconds=59)

        # Buscar o top 10 de doadores
        cursor.execute("""
            SELECT id_usuario, SUM(quantidade_cartas) AS total_doado
            FROM historico_doacoes
            WHERE data_hora BETWEEN %s AND %s
            GROUP BY id_usuario
            ORDER BY total_doado DESC
            LIMIT 10
        """, (inicio_semana, fim_semana))

        top_doadores = cursor.fetchall()

        # Buscar o top 10 de pescadores
        cursor.execute("""
            SELECT id_usuario, COUNT(id_carta) AS total_pescado
            FROM historico_cartas_giradas
            WHERE data_hora BETWEEN %s AND %s
            GROUP BY id_usuario
            ORDER BY total_pescado DESC
            LIMIT 10
        """, (inicio_semana, fim_semana))

        top_pescadores = cursor.fetchall()

        # Montar a resposta do ranking
        resposta = "🏆 <b>Ranking Semanal de Doadores:</b>\n"
        for i, doador in enumerate(top_doadores, 1):
            resposta += f"{i}º lugar: ID {doador[0]} - {doador[1]} cartas doadas\n"

        resposta += "\n🎣 <b>Ranking Semanal de Pescadores:</b>\n"
        for i, pescador in enumerate(top_pescadores, 1):
            resposta += f"{i}º lugar: ID {pescador[0]} - {pescador[1]} cartas pescadas\n"

        bot.send_message(message.chat.id, resposta, parse_mode="HTML")

    except Exception as e:
        print(f"Erro ao processar comando /ranking_semanal: {e}")
        bot.reply_to(message, "Ocorreu um erro ao gerar o ranking.")
    finally:
        fechar_conexao(cursor, conn)

@bot.message_handler(commands=['adicionar_vip'])
def adicionar_vip(message):
    # Verificar se o usuário é autorizado
    if message.from_user.id not in [5532809878, 1805086442, 5799169750]:
        bot.reply_to(message, "Você não tem permissão para usar este comando.")
        return

    msg = bot.reply_to(message, "Por favor, envie o ID do usuário.")
    bot.register_next_step_handler(msg, processar_id_vip)

@bot.message_handler(commands=['remover_vip'])
def remover_vip(message):
    if message.from_user.id not in [5532809878, 1805086442, 5799169750]:
        bot.reply_to(message, "Você não tem permissão para usar este comando.")
        return

    msg = bot.reply_to(message, "Por favor, envie o ID do usuário VIP a ser removido.")
    bot.register_next_step_handler(msg, processar_remocao_vip)

@bot.message_handler(commands=['vips'])
def listar_vips(message):
    try:
        if message.from_user.id not in [5532809878, 1805086442, 5799169750]:
            return
        conn, cursor = conectar_banco_dados()
        query = """
            SELECT id, nome, Dia_renovar
            FROM vips;
        """
        cursor.execute(query)
        vips = cursor.fetchall()

        if not vips:
            bot.send_message(message.chat.id, "Nenhum VIP encontrado.")
            return

        mensagem = "🎩 Lista de VIPs, IDs e dias restantes para renovação:\n\n"

        for vip in vips:
            id_vip, nome, dia_renovar = vip

            # Calcular a próxima data de renovação
            hoje = datetime.now()
            dia_atual = hoje.day
            mes_atual = hoje.month
            ano_atual = hoje.year

            # Se o dia de renovação já passou neste mês, calcular para o próximo mês
            if dia_renovar < dia_atual:
                proxima_renovacao = datetime(ano_atual, mes_atual + 1, dia_renovar)
            else:
                proxima_renovacao = datetime(ano_atual, mes_atual, dia_renovar)

            dias_restantes = (proxima_renovacao - hoje).days

            mensagem += f"ID: {id_vip} | {nome}: {dias_restantes} dias restantes\n"

        bot.send_message(message.chat.id, mensagem)

    except Exception as e:
        print(f"Erro ao listar VIPs: {e}")
        bot.send_message(message.chat.id, "Erro ao listar VIPs.")
    finally:
        fechar_conexao(cursor, conn)

@bot.message_handler(commands=['pedidos'])
def listar_pedidos_vips(message):
    try:
        if message.from_user.id not in [5532809878, 1805086442]:
            return
        conn, cursor = conectar_banco_dados()
        query = """
            SELECT nome, pedidos_restantes 
            FROM vips;
        """
        cursor.execute(query)
        pedidos_vips = cursor.fetchall()
        
        if not pedidos_vips:
            bot.send_message(message.chat.id, "Nenhum VIP encontrado.")
            return
        
        mensagem = "📦 Pedidos restantes dos VIPs:\n\n"
        for vip in pedidos_vips:
            nome, pedidos_restantes = vip
            mensagem += f"{nome}: {pedidos_restantes} pedidos restantes\n"

        bot.send_message(message.chat.id, mensagem)
        
    except Exception as e:
        print(f"Erro ao listar pedidos VIPs: {e}")
        bot.send_message(message.chat.id, "Erro ao listar pedidos VIPs.")
    finally:
        fechar_conexao(cursor, conn)
        
@bot.message_handler(commands=['ficha'])
def ver_ficha_vip(message):
    try:
        # Verificar se o usuário tem permissão para usar o comando
        if message.from_user.id not in [5532809878, 1805086442]:
            return

        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            bot.reply_to(message, "Uso correto: /ficha <id_vip>")
            return

        id_vip = args[1].strip()

        conn, cursor = conectar_banco_dados()
        query = """
            SELECT nome, data_pagamento, renovou, pedidos_restantes, Dia_renovar, imagem
            FROM vips
            WHERE id = %s;
        """
        cursor.execute(query, (id_vip,))
        ficha_vip = cursor.fetchone()

        if not ficha_vip:
            bot.send_message(message.chat.id, f"Nenhum VIP encontrado com o ID '{id_vip}'.")
            return

        nome, data_pagamento, renovou, pedidos_restantes, dia_renovar, imagem_url = ficha_vip
        status_renovou = "Sim" if renovou else "Não"

        # Calcular dias restantes para a próxima renovação
        hoje = datetime.now()
        dia_atual = hoje.day
        mes_atual = hoje.month
        ano_atual = hoje.year

        if dia_renovar < dia_atual:
            proxima_renovacao = datetime(ano_atual, mes_atual + 1, dia_renovar)
        else:
            proxima_renovacao = datetime(ano_atual, mes_atual, dia_renovar)

        dias_restantes = (proxima_renovacao - hoje).days

        mensagem = f"🎟️ Ficha de {nome} (ID: {id_vip}):\n\n"
        mensagem += f"📅 Data de pagamento: {data_pagamento}\n"
        mensagem += f"🔄 Renovou: {status_renovou}\n"
        mensagem += f"📦 Pedidos restantes: {pedidos_restantes}\n"
        mensagem += f"📆 Próxima renovação: Daqui a {dias_restantes} dias, no dia {dia_renovar}\n"

        if imagem_url:
            bot.send_photo(message.chat.id, imagem_url, caption=mensagem)
        else:
            bot.send_message(message.chat.id, mensagem)

    except Exception as e:
        print(f"Erro ao exibir ficha do VIP: {e}")
        bot.send_message(message.chat.id, "Erro ao exibir ficha do VIP.")
    finally:
        fechar_conexao(cursor, conn)

@bot.callback_query_handler(func=lambda call: call.data.startswith('toggle_'))
def toggle_config(call):
    parte = call.data.split('_')[1]
    conn, cursor = conectar_banco_dados()

    try:
        # Alterna o valor da parte no banco de dados
        cursor.execute(f"SELECT {parte} FROM usuarios WHERE id_usuario = %s", (call.from_user.id,))
        valor_atual = cursor.fetchone()[0]
        novo_valor = 0 if valor_atual else 1  # Troca entre 0 e 1
        
        cursor.execute(f"UPDATE usuarios SET {parte} = %s WHERE id_usuario = %s", (novo_valor, call.from_user.id))
        conn.commit()

        # Atualiza o menu de perfil
        perfil_config(call)
    finally:
        fechar_conexao(cursor, conn)
        
@bot.callback_query_handler(func=lambda call: call.data == 'toggle_casamento')
def toggle_casamento(call):
    user_id = call.from_user.id

    conn, cursor = conectar_banco_dados()

    # Buscar status atual do casamento
    query_status_casamento = "SELECT casamento_ativo FROM usuarios WHERE id_usuario = %s"
    cursor.execute(query_status_casamento, (user_id,))
    casamento_ativo = cursor.fetchone()[0]

    # Alternar o status do casamento
    novo_status = not casamento_ativo
    update_query = "UPDATE usuarios SET casamento_ativo = %s WHERE id_usuario = %s"
    cursor.execute(update_query, (novo_status, user_id))
    conn.commit()

    # Atualizar a mensagem com o novo status
    casamento_btn_text = "Casamento: ✔️" if novo_status else "Casamento: ❌"
    casamento_btn = types.InlineKeyboardButton(casamento_btn_text, callback_data='toggle_casamento')

    # Criar um novo menu com o botão atualizado
    markup = call.message.reply_markup
    for i, button in enumerate(markup.keyboard):
        if "Casamento" in button[0].text:
            markup.keyboard[i] = [casamento_btn]

    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

    fechar_conexao(cursor, conn)
        
@bot.callback_query_handler(func=lambda call: call.data == 'perfil_config')
def perfil_config(call):
    try:
        conn, cursor = conectar_banco_dados()
        cursor.execute("SELECT bio, musica, pronome FROM usuarios WHERE id_usuario = %s", (call.from_user.id,))
        config = cursor.fetchone()

        bio_ativo = "✅" if config[0] else "❌"
        musica_ativa = "✅" if config[1] else "❌"
        pronome_ativo = "✅" if config[2] else "❌"

        markup = types.InlineKeyboardMarkup()
        btn_bio = types.InlineKeyboardButton(f'Bio: {bio_ativo}', callback_data='toggle_bio')
        btn_musica = types.InlineKeyboardButton(f'Música: {musica_ativa}', callback_data='toggle_musica')
        btn_pronome = types.InlineKeyboardButton(f'Pronome: {pronome_ativo}', callback_data='toggle_pronome')
        btn_voltar = types.InlineKeyboardButton('🔙 Voltar', callback_data='voltar_config')

        markup.add(btn_bio, btn_musica, btn_pronome)
        markup.add(btn_voltar)
        
        bot.edit_message_text("Escolha o que deseja ativar/desativar no perfil:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    finally:
        fechar_conexao(cursor, conn)
@bot.message_handler(commands=['doar'])
def doar(message):
    try:
        print("Comando doar acionado")
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

            keyboard = telebot.types.InlineKeyboardMarkup()
            keyboard.row(
                telebot.types.InlineKeyboardButton(text="Sim", callback_data=f'cdoacao_{eu}_{minhacarta}_{destinatario_id}_{quantidade}'),
                telebot.types.InlineKeyboardButton(text="Não", callback_data=f'ccancelar_{eu}')
            )

            bot.send_message(chat_id, texto, reply_markup=keyboard)
        else:
            bot.send_message(chat_id, "Você não pode doar uma carta que não possui.")

    except Exception as e:
        newrelic.agent.record_exception()    
        print(f"Erro durante o comando de doação: {e}")
def atualizar_petalas(id_usuario):
    """Atualiza o número de pétalas do usuário de acordo com o tempo decorrido e se é VIP."""
    print(f"DEBUG: Iniciando atualização de pétalas para o usuário {id_usuario}.")
    conn, cursor = conectar_banco_dados()

    # Verificar se o usuário é VIP
    vip = is_vip(id_usuario)

    # Definir o tempo de regeneração e o máximo de pétalas com base no status VIP
    if vip:
        TEMPO_REGENERACAO = 2  # 2 horas para VIP
        MAX_PETALAS = 36  # VIP pode acumular até 3 dias de pétalas (36 pétalas)
    else:
        TEMPO_REGENERACAO = 3  # 3 horas para não VIP
        MAX_PETALAS = 8   # Não VIP pode acumular até 1 dia de pétalas (8 pétalas)
    
    print(f"DEBUG: Regeneração definida para {TEMPO_REGENERACAO} horas. Máximo de pétalas: {MAX_PETALAS}")

    # Buscar o número atual de pétalas e a última regeneração
    cursor.execute("SELECT petalas, ultima_regeneracao_petalas FROM usuarios WHERE id_usuario = %s", (id_usuario,))
    resultado = cursor.fetchone()

    if resultado:
        petalas_atual, ultima_regeneracao = resultado
        petalas_atual = petalas_atual if petalas_atual is not None else 0  # Inicializar com 0 se estiver NULL
        print(f"DEBUG: Petalas atuais: {petalas_atual}. Última regeneração: {ultima_regeneracao}")
        agora = datetime.now()

        # Verificar se a última regeneração é válida
        if ultima_regeneracao is None:
            ultima_regeneracao = agora
            print(f"DEBUG: Última regeneração estava nula. Atualizando com o valor atual.")
            cursor.execute("""
                UPDATE usuarios SET ultima_regeneracao_petalas = %s WHERE id_usuario = %s
            """, (ultima_regeneracao, id_usuario))
            conn.commit()

        # Calcular o tempo desde a última regeneração
        horas_passadas = (agora - ultima_regeneracao).total_seconds() / 3600
        print(f"DEBUG: Horas passadas desde a última regeneração: {horas_passadas}")

        # Calcular quantas pétalas regenerar
        petalas_regeneradas = int(horas_passadas // TEMPO_REGENERACAO)  # Divide as horas passadas pelo tempo de regeneração
        novas_petalas = min(MAX_PETALAS, petalas_atual + petalas_regeneradas)
        print(f"DEBUG: Petalas regeneradas: {petalas_regeneradas}. Novas pétalas: {novas_petalas}")

        # Se houver novas pétalas a serem adicionadas, atualizar no banco
        if novas_petalas > petalas_atual:
            print(f"DEBUG: Atualizando pétalas no banco para {novas_petalas}.")
            cursor.execute("""
                UPDATE usuarios
                SET petalas = %s, ultima_regeneracao_petalas = %s
                WHERE id_usuario = %s
            """, (novas_petalas, agora, id_usuario))
            conn.commit()
        else:
            print(f"DEBUG: Nenhuma nova pétala para atualizar.")
    else:
        print(f"DEBUG: Nenhuma informação encontrada para o usuário {id_usuario}.")

    fechar_conexao(cursor, conn)



@bot.message_handler(commands=['roseira'])
def roseira_command(message):
    try:
        id_usuario = message.from_user.id
        print(f"DEBUG: Comando /roseira acionado pelo usuário {id_usuario}")
        # Verificar se o usuário é VIP
        if not is_vip(id_usuario):
            bot.reply_to(message, "Este comando está em teste e só pode ser usado por usuários VIP.")
            return
        # Atualizar as pétalas antes de usar o comando
        atualizar_petalas(id_usuario)

        # Verificar o número de pétalas atual
        conn, cursor = conectar_banco_dados()
        cursor.execute("SELECT petalas FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        petalas_disponiveis = cursor.fetchone()[0]
        print(f"DEBUG: Pétalas disponíveis para o usuário {id_usuario}: {petalas_disponiveis}")


        if petalas_disponiveis > 0:
            # Reduzir o número de pétalas em 1
            cursor.execute("UPDATE usuarios SET petalas = petalas - 1 WHERE id_usuario = %s", (id_usuario,))
            conn.commit()

            # Executar o comando roseira normalmente
            # Extrair a subcategoria
            args = message.text.split(maxsplit=1)
            if len(args) < 2:
                bot.reply_to(message, "Por favor, forneça uma subcategoria válida.")
                return

            subcategoria = args[1].strip()

            # Validar se a subcategoria existe no banco de dados
            cursor.execute("SELECT id_personagem, nome, imagem FROM personagens WHERE subcategoria = %s", (subcategoria,))
            resultado = cursor.fetchall()

            if not resultado or len(resultado) < 3:
                bot.reply_to(message, "Subcategoria não encontrada ou não há cartas suficientes.")
                return

            # Garantir que não haja cartas repetidas
            cartas_aleatorias = random.sample(resultado, 3)  # Pega 3 cartas aleatórias sem repetição

            # Tentar pegar as imagens correspondentes às cartas
            imagens_cartas = []
            for carta in cartas_aleatorias:
                try:
                    # Verificar se a imagem com borda já está no cache
                    if carta[0] in cache_imagens_com_bordas:
                        imagens_cartas.append(cache_imagens_com_bordas[carta[0]])
                    else:
                        # Tentar fazer o download e abrir a imagem da carta
                        response = requests.get(carta[2])  # carta[2] contém a URL da imagem
                        img = Image.open(BytesIO(response.content))  # Abrir a imagem em memória

                        # Baixar e aplicar uma borda aleatória
                        borda_response = requests.get(random.choice(bordas_urls))  # Pega uma borda aleatória
                        borda_aleatoria = Image.open(BytesIO(borda_response.content))  # Abrir a borda
                        img_com_borda = aplicar_borda(img, borda_aleatoria)

                        # Adicionar ao cache
                        cache_imagens_com_bordas[carta[0]] = img_com_borda
                        imagens_cartas.append(img_com_borda)

                except (UnidentifiedImageError, IOError):
                    # Se a imagem for inválida, tentar outra carta
                    continue


            # Definir o tamanho das imagens e o espaço entre elas (3x4 com espaço)
            largura_individual = 300  # largura padrão 3x4
            altura_individual = 400   # altura padrão 3x4
            espaco_entre = 10         # Espaço entre as imagens

            # Calcular o tamanho total da imagem com 3 cartas lado a lado
            largura_total = 3 * largura_individual + 2 * espaco_entre
            altura_total = altura_individual

            # Criar a imagem final com fundo transparente
            imagem_final = Image.new("RGBA", (largura_total, altura_total), (255, 255, 255, 0))

            # Colar as imagens lado a lado com espaço entre elas
            x_offset = 0
            for img in imagens_cartas:
                img_resized = img.resize((largura_individual, altura_individual))
                imagem_final.paste(img_resized, (x_offset, 0))
                x_offset += largura_individual + espaco_entre

            # Salvar a imagem gerada temporariamente
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_img_file:
                imagem_final.save(temp_img_file.name)
                caminho_imagem = temp_img_file.name

            # Construir a mensagem personalizada
            nomes_cartas = [f"1️⃣ {cartas_aleatorias[0][1]}", f"2⃣ {cartas_aleatorias[1][1]}", f"3⃣ {cartas_aleatorias[2][1]}"]
            mensagem = (f"🌹 Você balança a roseira, fazendo ela derrubar algumas pétalas.\n"
            f"Qual dessas você vai levar?\n\n" + "\n".join(nomes_cartas) +
            f"\n\n🌺 Pétalas disponíveis: {petalas_disponiveis}")

            # Enviar a imagem com os botões 1, 2, 3 e a mensagem personalizada
            markup = types.InlineKeyboardMarkup()
            botao1 = types.InlineKeyboardButton("1️⃣", callback_data=f"escolher_{cartas_aleatorias[0][0]}")
            botao2 = types.InlineKeyboardButton("2⃣", callback_data=f"escolher_{cartas_aleatorias[1][0]}")
            botao3 = types.InlineKeyboardButton("3⃣", callback_data=f"escolher_{cartas_aleatorias[2][0]}")
            markup.add(botao1, botao2, botao3)

            bot.send_photo(message.chat.id, open(caminho_imagem, 'rb'), caption=mensagem, reply_markup=markup, reply_to_message_id=message.message_id)

        else:
            tempo_restante = calcular_tempo_restante(id_usuario)
            bot.reply_to(message, f"🥀 Ainda não tem pétalas disponíveis na sua roseira... Volte em: {tempo_restante}")


    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        fechar_conexao(cursor, conn)
        # Remover a imagem temporária
        if os.path.exists(caminho_imagem):
            os.remove(caminho_imagem)


@bot.callback_query_handler(func=lambda call: call.data.startswith("escolher_"))
def callback_escolher_carta(call):
    try:
        # Impedir múltiplos cliques (trava)
        if hasattr(call.message, 'escolha_feita') and call.message.escolha_feita:
            return

        # Identificar a escolha do usuário
        id_personagem_escolhido = int(call.data.split("_")[1])

        # Trava: impedir múltiplas escolhas
        call.message.escolha_feita = True

        # Remover os botões após a escolha
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

        # Buscar o nome do personagem no banco de dados
        conn, cursor = conectar_banco_dados()
        cursor.execute("SELECT nome FROM personagens WHERE id_personagem = %s", (id_personagem_escolhido,))
        nome_personagem = cursor.fetchone()[0]
        fechar_conexao(cursor, conn)

        # Adicionar a carta ao inventário
        add_to_inventory(call.from_user.id, id_personagem_escolhido)

        # Editar a legenda da imagem com a mensagem personalizada
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=f"💐 Você escolheu a pétala perfeita! {id_personagem_escolhido} - {nome_personagem} adicionada ao seu inventário. ✨"
        )

    except Exception as e:
        print(f"Erro ao processar a escolha de carta: {e}")
        bot.reply_to(call.message, "Ocorreu um erro ao processar sua escolha.")

@bot.message_handler(commands=['pedidosubmenu'])
def pedido_submenu_command(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    try:
        conn, cursor = conectar_banco_dados()

        # Verificar se o usuário é VIP
        query_vip = """
            SELECT pedidos_restantes 
            FROM vips 
            WHERE id_usuario = %s
        """
        cursor.execute(query_vip, (user_id,))
        vip_info = cursor.fetchone()

        if not vip_info:
            bot.send_message(message.chat.id, "Desculpe, você não é um VIP ou não possui pedidos restantes.")
            return

        pedidos_restantes = vip_info[0]

        # Verificar se o VIP ainda tem pedidos restantes
        if pedidos_restantes <= 0:
            bot.send_message(message.chat.id, "Você já usou todos os seus pedidos de submenu deste mês.")
            return

        # Instruções para enviar o submenu
        mensagem_inicial = (
            "Você pode fazer seu pedido de submenu!\n\n"
            "Envie o submenu dessa forma:\n\n"
            "- subcategoria: <b>Nome da Subcategoria</b>\n"
            "- submenu: <b>Nome do Submenu</b>\n"
            "personagem1nome, link da foto\n"
            "personagem2nome, link da foto\n"
            "..."
        )
        bot.send_message(message.chat.id, mensagem_inicial, parse_mode="HTML")

        # Registrar o próximo passo para processar o submenu enviado
        bot.register_next_step_handler(message, processar_pedido_submenu, pedidos_restantes, user_name)

    except Exception as e:
        bot.send_message(message.chat.id, "Ocorreu um erro ao verificar suas permissões de VIP.")
        print(f"Erro ao verificar VIP: {e}")
    finally:
        fechar_conexao(cursor, conn)


@bot.message_handler(commands=['pedidovip'])
def pedidovip_command(message):
    # Verifica se o usuário é autorizado a usar o comando
    if message.from_user.id not in [5532809878, 1805086442]:
        bot.send_message(message.chat.id, "Você não tem permissão para usar este comando.")
        return

    try:
        # Divide o comando em partes
        args = message.text.split()
        if len(args) != 3:
            bot.send_message(message.chat.id, "Uso incorreto. Formato correto: /pedidovip <iddovip> <número (+ ou -)>")
            return

        # Extrai os argumentos
        id_vip = int(args[1])
        ajuste = int(args[2])

        # Conecta ao banco de dados
        conn, cursor = conectar_banco_dados()

        # Verifica se o VIP existe
        cursor.execute("SELECT pedidos_restantes FROM vips WHERE id = %s", (id_vip,))
        vip_info = cursor.fetchone()

        if not vip_info:
            bot.send_message(message.chat.id, f"Nenhum VIP encontrado com o ID '{id_vip}'.")
            return

        pedidos_atual = vip_info[0]
        pedidos_novo = pedidos_atual + ajuste

        # Atualiza o número de pedidos restantes
        cursor.execute("UPDATE vips SET pedidos_restantes = %s WHERE id = %s", (pedidos_novo, id_vip))
        conn.commit()

        # Mensagem de confirmação
        bot.send_message(message.chat.id, f"Pedidos do VIP com ID {id_vip} foram atualizados. Novo total de pedidos: {pedidos_novo}")

    except Exception as e:
        bot.send_message(message.chat.id, f"Erro ao atualizar os pedidos: {e}")
        print(f"Erro ao processar o comando /pedidovip: {e}")
    finally:
        fechar_conexao(cursor, conn)

@bot.message_handler(commands=['song'])
def jogar_song(message):
    id_usuario = message.from_user.id
    chat_id = message.chat.id

    # Verificar se o usuário está no período de cooldown
    if id_usuario in song_cooldown_cache:
        bot.reply_to(message, "Você já jogou recentemente! Tente novamente em 3 horas.")
        return

    conn, cursor = conectar_banco_dados()

    try:
        # Escolher uma música aleatória da tabela
        cursor.execute("SELECT id, url, nome, artista FROM musicas ORDER BY RAND() LIMIT 1")
        musica = cursor.fetchone()

        if not musica:
            bot.reply_to(message, "Nenhuma música disponível no momento.")
            return

        id_musica, url, nome_musica, artista_musica = musica

        # Verificar se a música já foi editada e está no cache
        if id_musica in cache_musicas_editadas:
            audio_file = cache_musicas_editadas[id_musica]
            audio_file.seek(0)  # Reposiciona o cursor no início do arquivo novamente
        else:
            # Fazer download do arquivo de áudio a partir da URL
            response = requests.get(url)
            if response.status_code != 200:
                bot.reply_to(message, "Erro ao baixar a música. Tente novamente mais tarde.")
                return

            audio_file = io.BytesIO(response.content)
            audio_file.name = "adivinhe_a_musica.mp3"  # Definir o nome do arquivo no objeto BytesIO

            # Armazenar a música no cache
            cache_musicas_editadas[id_musica] = audio_file

        # Enviar a música como arquivo de áudio
        pergunta = random.choice(["Qual o nome da música?", "Qual o nome do artista?"])
        bot_message = bot.send_audio(chat_id, audio=audio_file, caption=pergunta, title="Adivinhe a música")

        # Armazenar a mensagem do bot para referência posterior
        active_song_challenges[chat_id] = {
            'message_id': bot_message.message_id,
            'id_musica': id_musica,
            'nome_musica': nome_musica.lower(),
            'artista_musica': artista_musica.lower(),
            'respondido': False,
            'usuario_ativador': id_usuario
        }

        # Adicionar o usuário ao cooldown
        song_cooldown_cache[id_usuario] = datetime.now()

        # Timer para apagar a mensagem e avisar se o tempo esgotou
        timer = threading.Timer(30.0, tempo_esgotado, [chat_id])
        timer.start()

    except Exception as e:
        bot.reply_to(message, "Ocorreu um erro ao tentar iniciar o jogo.")
        print(f"Erro ao iniciar o jogo: {e}")
    finally:
        fechar_conexao(cursor, conn)
        

@bot.message_handler(func=lambda message: message.reply_to_message and message.reply_to_message.message_id in [challenge['message_id'] for challenge in active_song_challenges.values()])
def verificar_resposta(message):
    chat_id = message.chat.id
    id_usuario = message.from_user.id
    resposta = message.text.strip().lower()

    challenge = active_song_challenges.get(chat_id)

    if challenge and not challenge['respondido'] and message.reply_to_message.message_id == challenge['message_id']:
        if resposta == challenge['nome_musica'] or resposta == challenge['artista_musica']:
            # Marca como respondido e remove o desafio ativo
            challenge['respondido'] = True
            del active_song_challenges[chat_id]

            # Apaga a mensagem de pergunta original do bot
            bot.delete_message(chat_id, challenge['message_id'])

            # Adicionar cenouras ao usuário
            cenouras = random.randint(50, 100)
            conn, cursor = conectar_banco_dados()
            cursor.execute("UPDATE usuarios SET cenouras = cenouras + %s WHERE id_usuario = %s", (cenouras, id_usuario))
            conn.commit()

            # Enviar mensagem de parabéns no privado
            bot.send_message(id_usuario, f"🎉 Parabéns, você acertou! Como recompensa, vai ganhar:\n🥕 {cenouras} cenouras!")

            # Enviar mensagem no grupo informando o acerto
            nome_usuario = message.from_user.first_name
            bot.send_message(chat_id, f"🎶 Parabéns! Música ou Artista adivinhados por {nome_usuario}.\n\n A música era: <b>{challenge['nome_musica'].capitalize()} de {challenge['artista_musica'].capitalize()}</b>.",parse_mode="HTML")

            # Registrar a tentativa na tabela
            cursor.execute("INSERT INTO song_tentativas (id_usuario, id_musica, data_hora, acertou) VALUES (%s, %s, %s, %s)", 
                           (id_usuario, challenge['id_musica'], datetime.now(), True))
            conn.commit()
            fechar_conexao(cursor, conn)

        else:
            # Resposta incorreta - apagar mensagem original e enviar alerta no grupo
            bot.delete_message(chat_id, challenge['message_id'])
            bot.send_message(chat_id, f"❌ Poxa, parece que a resposta está incorreta. A música era: {challenge['nome_musica'].capitalize()} de {challenge['artista_musica'].capitalize()}.")
@bot.message_handler(commands=['biblioteca'])
def listar_biblioteca(message):
    chat_id = message.chat.id

    conn, cursor = conectar_banco_dados()

    try:
        # Buscar todas as músicas na tabela
        cursor.execute("SELECT nome, artista FROM musicas ORDER BY nome ASC")
        musicas = cursor.fetchall()

        if not musicas:
            bot.send_message(chat_id, "Nenhuma música disponível na biblioteca.")
            return

        # Construir a lista de músicas no formato "nome - artista"
        biblioteca = "\n".join([f"{musica[0]} - {musica[1]}" for musica in musicas])

        # Enviar a lista para o usuário
        bot.send_message(chat_id, f"🎵 <b>Biblioteca de Músicas:</b>\n\n{biblioteca}", parse_mode="HTML")

    except Exception as e:
        bot.reply_to(message, "Ocorreu um erro ao tentar acessar a biblioteca de músicas.")
        print(f"Erro ao listar a biblioteca: {e}")
    finally:
        fechar_conexao(cursor, conn)           
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
        newrelic.agent.record_exception()
        print(f"Erro em categoria_callback: {e}")
        
@bot.callback_query_handler(func=lambda call: call.data.startswith('peixes_'))
def callback_peixes(call):
    try:
        parts = call.data.split('_')
        pagina = int(parts[1])
        subcategoria = parts[2]
        
        pagina_peixes_callback(call, pagina, subcategoria)
    except Exception as e:
        newrelic.agent.record_exception()    
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

        
        # Se existe evento fixo e a chance de 30% se aplica, envia o evento fixo
        if evento_fixo and chance <= 5:
            # Acessa os valores de 'evento_fixo' como tupla
            emoji, id_personagem_carta, nome, subcategoria, imagem = evento_fixo
            send_card_message(call.message, emoji, id_personagem_carta, nome, subcategoria, imagem)
        else:
            # Caso contrário, envia uma carta aleatória normal da subcategoria
             subcategoria_handler(call.message, subcategoria, cursor, conn, None,chat_id,message_id)
    
    except Exception as e:
        traceback.print_exc()
        erro = traceback.format_exc()
        bot.send_message(grupodeerro, f"Erro em categoria_callback: {e}\n{erro}")
    finally:
        fechar_conexao(cursor, conn)


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
# Comando /casar
@bot.message_handler(commands=['casar'])
def casar_command(message):
    try:
        user_id = message.from_user.id
        command_parts = message.text.split()
        if len(command_parts) == 2:
            id_personagem = command_parts[1]
        else:
            bot.send_message(message.chat.id, "Uso: /casar <id_personagem>")
            print("Debug: Uso incorreto do comando /casar")
            return

        conn, cursor = conectar_banco_dados()

        # Verifica se o usuário já está casado
        cursor.execute("SELECT COUNT(*) FROM controle_de_casamento WHERE usuario = %s AND casado = 'sim'", (user_id,))
        ja_casado = cursor.fetchone()[0] > 0

        if ja_casado:
            bot.send_message(message.chat.id, "Não desrespeite seu parceiro! Você já está casado! 😡", parse_mode="HTML")
            print("Debug: Usuário já está casado")
            return

        # Verifica se a carta existe na tabela evento e é do tipo "amor"
        cursor.execute("SELECT COUNT(*), MAX(nome), MAX(evento) FROM evento WHERE id_personagem = %s AND evento = 'amor'", (id_personagem,))
        result = cursor.fetchone()
        carta_existe = result[0] > 0
        nome_personagem = result[1]
        evento_amor = result[2] == 'amor'

        if not carta_existe or not evento_amor:
            bot.send_message(message.chat.id, "Essa carta não existe ou não pertence ao evento amor.")
            print(f"Debug: Carta não existe ou não é do evento amor - id_personagem: {id_personagem}")
            return

        # Verifica se o usuário possui a carta no inventário
        cursor.execute("SELECT COUNT(*) FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (user_id, id_personagem))
        possui_carta = cursor.fetchone()[0] > 0

        if not possui_carta:
            bot.send_message(message.chat.id, "Parece que o cupido não colocou essa carta na sua cesta.")
            print(f"Debug: Usuário não possui a carta - id_usuario: {user_id}, id_personagem: {id_personagem}")
            return

        # Pergunta se o usuário deseja mesmo casar com a carta
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="Sim", callback_data=f"confirmar_casamento_{id_personagem}"))
        markup.add(types.InlineKeyboardButton(text="Não", callback_data="cancelar_casamento"))
        mensagem = f"<i>Você deseja ficar com o personagem <b>{nome_personagem}</b> na saúde e na pobreza até que a morte os separe? 💍🌹</i>"
        bot.send_message(message.chat.id, mensagem, reply_markup=markup, parse_mode="HTML")

        print(f"Debug: Pergunta de casamento enviada - id_usuario: {user_id}, id_personagem: {id_personagem}")

        conn.commit()
    except mysql.connector.Error as err:
        print(f"Erro ao processar o comando /casar: {err}")
    finally:
        fechar_conexao(cursor, conn)

# Callback para confirmar o casamento
@bot.callback_query_handler(func=lambda call: call.data.startswith("confirmar_casamento_"))
def confirmar_casamento(call):
    user_id = call.from_user.id
    id_personagem = call.data.split("_")[2]

    conn, cursor = conectar_banco_dados()
    try:
        # Verifica se o casamento já foi negado
        cursor.execute("SELECT COUNT(*) FROM negacoes_de_pedido WHERE id_usuario = %s AND id_personagem = %s", (user_id, id_personagem))
        casamento_negado = cursor.fetchone()[0] > 0

        if casamento_negado:
            bot.send_message(call.message.chat.id, "<b>Você já tentou casar com essa pessoa e foi negado.</b> Não pode se humilhar por ex! 😑", parse_mode="HTML")
            print(f"Debug: Pedido de casamento já foi negado anteriormente - id_usuario: {user_id}, id_personagem: {id_personagem}")
            return

        # Verifica se o usuário já está casado
        cursor.execute("SELECT COUNT(*) FROM controle_de_casamento WHERE usuario = %s AND casado = 'sim'", (user_id,))
        ja_casado = cursor.fetchone()[0] > 0

        if ja_casado:
            bot.send_message(call.message.chat.id, "<b>Não desrespeite seu parceiro!</b> Você já está casado! 😡", parse_mode="HTML")
            print(f"Debug: Usuário já está casado - id_usuario: {user_id}")
            return

        # Realiza o sorteio de 70% de sucesso e 30% de falha
        sucesso = random.random() < 0.7

        if sucesso:
            # Verifica se já existe um registro para o usuário e atualiza
            cursor.execute("SELECT COUNT(*) FROM controle_de_casamento WHERE usuario = %s", (user_id,))
            existe_registro = cursor.fetchone()[0] > 0

            if existe_registro:
                cursor.execute("UPDATE controle_de_casamento SET casado = 'sim', conjuge = %s, divorciado = 'nao' WHERE usuario = %s", (id_personagem, user_id))
                print(f"Debug: Registro de casamento atualizado - id_usuario: {user_id}, id_personagem: {id_personagem}")
            else:
                cursor.execute("INSERT INTO controle_de_casamento (usuario, casado, conjuge, divorciado) VALUES (%s, 'sim', %s, 'nao')", (user_id, id_personagem))
                print(f"Debug: Registro de casamento inserido - id_usuario: {user_id}, id_personagem: {id_personagem}")

            bot.send_message(call.message.chat.id, f"<i>Parabéns! <b>Você se casou com o personagem {id_personagem}!</b></i> Que sejam felizes para sempre! 🥰💍", parse_mode="HTML")
        else:
            cursor.execute("INSERT INTO negacoes_de_pedido (id_usuario, id_personagem) VALUES (%s, %s)", (user_id, id_personagem))
            bot.send_message(call.message.chat.id, f"<i>O personagem {id_personagem} gentilmente negou o seu pedido de casamento.</i> Parece que o amor não estava no ar dessa vez. 🥹", parse_mode="HTML")
            print(f"Debug: Pedido de casamento negado - id_usuario: {user_id}, id_personagem: {id_personagem}")
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Erro ao confirmar casamento: {err}")
    finally:
        fechar_conexao(cursor, conn)

# Comando /divorciar
@bot.message_handler(commands=['divorciar'])
def divorciar_command(message):
    try:
        user_id = message.from_user.id
        conn, cursor = conectar_banco_dados()

        # Verifica se o usuário já se divorciou
        cursor.execute("SELECT COUNT(*) FROM controle_de_casamento WHERE usuario = %s AND divorciado = 'sim'", (user_id,))
        ja_divorciado = cursor.fetchone()[0] > 0

        if ja_divorciado:
            bot.send_message(message.chat.id, "<i>Você já se divorciou anteriormente e não pode se divorciar novamente. 😔</i>", parse_mode="HTML")
            print(f"Debug: Usuário já se divorciou anteriormente - id_usuario: {user_id}")
            return

        # Permite o divórcio
        cursor.execute("UPDATE controle_de_casamento SET divorciado = 'sim', conjuge = NULL WHERE usuario = %s", (user_id,))
        bot.send_message(message.chat.id, "<i>Infelizmente o amor não foi suficiente e vocês se divorciaram com sucesso.</i> Escolha melhor da próxima vez. 😥", parse_mode="HTML")
        print(f"Debug: Divórcio realizado com sucesso - id_usuario: {user_id}")
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Erro ao processar o comando /divorciar: {err}")
    finally:
        fechar_conexao(cursor, conn)


@bot.message_handler(commands=['completos'])
def handle_completos(message):
    try:
        parts = message.text.split(' ', 1)
        if len(parts) < 2:
            bot.reply_to(message, "Por favor, forneça a categoria após o comando, por exemplo: /completos música")
            return

        categoria = parts[1].strip()
        id_usuario = message.from_user.id
        nome_usuario = message.from_user.first_name

        conn, cursor = conectar_banco_dados()

        # Corrigir a mistura de collations com COLLATE utf8mb4_unicode_ci nas colunas envolvidas na comparação
        query = """
        SELECT s.subcategoria COLLATE utf8mb4_unicode_ci AS subcategoria, 
               SUM(CASE WHEN inv.id_personagem IS NOT NULL THEN 1 ELSE 0 END) AS total_possui, 
               COUNT(p.id_personagem) AS total_necessario,
               MAX(s.Imagem) AS Imagem
        FROM subcategorias s
        JOIN personagens p ON s.subcategoria COLLATE utf8mb4_unicode_ci = p.subcategoria COLLATE utf8mb4_unicode_ci
        LEFT JOIN inventario inv ON p.id_personagem = inv.id_personagem AND inv.id_usuario = %s
        WHERE p.categoria = %s COLLATE utf8mb4_unicode_ci
        GROUP BY s.subcategoria
        HAVING total_possui = total_necessario
        ORDER BY s.subcategoria ASC
        """
        cursor.execute(query, (id_usuario, categoria))
        completos = cursor.fetchall()

        if not completos:
            bot.reply_to(message, f"Você ainda não completou nenhuma subcategoria em '{categoria}'.")
            return

        total_paginas = (len(completos) + 14) // 15  # Calcula total de páginas
        mostrar_pagina_completos(message, 1, total_paginas, completos, categoria, nome_usuario, id_usuario)

    except Exception as e:
        print(f"Erro ao processar comando /completos: {e}")
        bot.reply_to(message, "Ocorreu um erro ao processar sua solicitação.")
    finally:
        fechar_conexao(cursor, conn)


def mostrar_pagina_completos(message, pagina_atual, total_paginas, completos, categoria, nome_usuario, id_usuario, call=None):
    try:
        offset = (pagina_atual - 1) * 15
        subcategorias_pagina = completos[offset:offset + 15]

        resposta = f"🌟 Subcategorias completas de {categoria} por {nome_usuario}:\n\n"
        for subcategoria, total_possui, total_necessario, _ in subcategorias_pagina:
            resposta += f"✮ {subcategoria} — {total_possui}/{total_necessario}\n"
        resposta += f"\nPágina {pagina_atual} de {total_paginas}"

        markup = None
        if total_paginas > 1:
            markup = criar_markup_completos(pagina_atual, total_paginas, categoria, id_usuario, nome_usuario)

        # Seleciona uma imagem aleatória da lista de subcategorias completas
        imagens_validas = [img for _, _, _, img in subcategorias_pagina if img]
        banner_imagem = random.choice(imagens_validas) if imagens_validas else None

        if call:
            if banner_imagem:
                bot.edit_message_media(media=telebot.types.InputMediaPhoto(banner_imagem, caption=resposta, parse_mode="HTML"), chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
            else:
                bot.edit_message_text(resposta, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="HTML")
        else:
            if banner_imagem:
                bot.send_photo(message.chat.id, banner_imagem, caption=resposta, reply_markup=markup, parse_mode="HTML")
            else:
                bot.send_message(message.chat.id, resposta, reply_markup=markup, parse_mode="HTML")

    except Exception as e:
        print(f"Erro ao mostrar página de subcategorias completas: {e}")
    finally:
        fechar_conexao(cursor, conn)


def criar_markup_completos(pagina_atual, total_paginas, categoria, id_usuario, nome_usuario):
    markup = telebot.types.InlineKeyboardMarkup()

    if pagina_atual > 1:
        markup.add(telebot.types.InlineKeyboardButton("⬅️", callback_data=f"completos_{pagina_atual - 1}_{categoria}_{id_usuario}_{nome_usuario}"))

    if pagina_atual < total_paginas:
        markup.add(telebot.types.InlineKeyboardButton("➡️", callback_data=f"completos_{pagina_atual + 1}_{categoria}_{id_usuario}_{nome_usuario}"))

    return markup


@bot.callback_query_handler(func=lambda call: call.data.startswith('completos_'))
def callback_navegacao_completos(call):
    try:
        parts = call.data.split('_')
        pagina_atual = int(parts[1])
        categoria = parts[2]
        id_usuario = int(parts[3])
        nome_usuario = parts[4]  # Nome original do usuário

        conn, cursor = conectar_banco_dados()

        # Reexecuta a consulta para obter subcategorias completas
        query = """
        SELECT s.subcategoria COLLATE utf8mb4_unicode_ci AS subcategoria, 
               SUM(CASE WHEN inv.id_personagem IS NOT NULL THEN 1 ELSE 0 END) AS total_possui, 
               COUNT(p.id_personagem) AS total_necessario,
               MAX(s.Imagem) AS Imagem
        FROM subcategorias s
        JOIN personagens p ON s.subcategoria COLLATE utf8mb4_unicode_ci = p.subcategoria COLLATE utf8mb4_unicode_ci
        LEFT JOIN inventario inv ON p.id_personagem = inv.id_personagem AND inv.id_usuario = %s
        WHERE p.categoria = %s COLLATE utf8mb4_unicode_ci
        GROUP BY s.subcategoria
        HAVING total_possui = total_necessario
        ORDER BY s.subcategoria ASC
        """
        cursor.execute(query, (id_usuario, categoria))
        completos = cursor.fetchall()

        total_paginas = (len(completos) + 14) // 15  # Calcula total de páginas
        mostrar_pagina_completos(call.message, pagina_atual, total_paginas, completos, categoria, nome_usuario, id_usuario, call=call)

    except Exception as e:
        print(f"Erro ao processar callback de navegação: {e}")
        bot.answer_callback_query(call.id, "Erro ao processar a navegação.")
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
        newrelic.agent.record_exception()    
        bot.send_message(call.message.chat.id, "Erro ao confirmar a doação. Tente novamente!")
    finally:
        fechar_conexao(cursor, conn)



@bot.callback_query_handler(func=lambda call: call.data.startswith('ccancelar_'))
def cancelar_doacao(call):
    try:
        bot.edit_message_text("Doação cancelada.", chat_id=call.message.chat.id, message_id=call.message.message_id)
    except Exception as e:
        print(f"Erro ao cancelar a doação: {e}")
        newrelic.agent.record_exception()    
        bot.send_message(call.message.chat.id, "Erro ao cancelar a doação.")
        
@bot.callback_query_handler(func=lambda call: call.data == 'acoes_vendinha')
def exibir_acoes_vendinha(call):
    try:
        mensagem = "📦 Pacotes de Ações disponíveis:\n\n"
        mensagem += "🥕 Pacote Básico: 10 cartas\n"
        mensagem += "💸 Pacote Médio: 25 cartas\n"
        mensagem += "💳 Pacote Premium: 80 cartas\n\n"
        
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            telebot.types.InlineKeyboardButton(text="🥕", callback_data='comprar_acao_vendinha_basico'),
            telebot.types.InlineKeyboardButton(text="💸", callback_data='comprar_acao_vendinha_prata'),
            telebot.types.InlineKeyboardButton(text="💳", callback_data='comprar_acao_vendinha_ouro')
        )
        
        bot.edit_message_caption(caption=mensagem, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=keyboard)
    except Exception as e:
        print(f"Erro ao exibir pacotes de ações: {e}")
        newrelic.agent.record_exception()    
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
        mensagem = f"Selecione a categoria para o {nome_pacote}:\n\n"
        mensagem += f"★ Geral -{preco} cenouras\n"
        mensagem += f"★ Por categoria - {preco * 2} cenouras\n"

        # Criação do teclado com categorias
        keyboard = telebot.types.InlineKeyboardMarkup()
        primeira_coluna = [
            telebot.types.InlineKeyboardButton(text="☁ Música", callback_data=f'confirmar_categoria_{pacote}_musica'),
            telebot.types.InlineKeyboardButton(text="🌷 Anime", callback_data=f'confirmar_categoria_{pacote}_animanga'),
            telebot.types.InlineKeyboardButton(text="🧶 Jogos", callback_data=f'confirmar_categoria_{pacote}_jogos')
        ]
        segunda_coluna = [
            telebot.types.InlineKeyboardButton(text="🍰 Filmes", callback_data=f'confirmar_categoria_{pacote}_filmes'),
            telebot.types.InlineKeyboardButton(text="🍄 Séries", callback_data=f'confirmar_categoria_{pacote}_series'),
            telebot.types.InlineKeyboardButton(text="🍂 Misc", callback_data=f'confirmar_categoria_{pacote}_miscelanea')
        ]
        geral = telebot.types.InlineKeyboardButton(text="🫧 Geral", callback_data=f'confirmar_categoria_{pacote}_geral')
        cancel =  telebot.types.InlineKeyboardButton(text="Cancelar Compra", callback_data=f'cancelar_compra_vendinha')
        keyboard.add(*primeira_coluna)
        keyboard.add(*segunda_coluna)
        keyboard.row(geral)
        keyboard.row(cancel)
        bot.edit_message_caption(caption=mensagem, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith('confirmar_categoria_'))
def processar_compra_vendinha_categoria(call):
    try:
        partes = call.data.split('_')
        pacote = partes[2]
        categoria = partes[3]

        print(f"DEBUG: Pacote: {pacote}, Categoria: {categoria}")

        pacotes = {
            'basico': (10, 50),  # 10 cartas, 50 cenouras
            'prata': (25, 100),  # 25 cartas, 100 cenouras
            'ouro': (80, 200)    # 80 cartas, 200 cenouras
        }

        if pacote in pacotes:
            quantidade, preco = pacotes[pacote]
            id_usuario = call.from_user.id
            print(f"DEBUG: Quantidade: {quantidade}, Preço: {preco}, ID Usuário: {id_usuario}")

            # Ajuste de preço para categorias específicas
            if categoria != 'geral':
                preco *= 2
            print(f"DEBUG: Preço atualizado (se aplicável): {preco}")

            conn, cursor = conectar_banco_dados()
            cursor.execute("SELECT cenouras FROM usuarios WHERE id_usuario = %s", (id_usuario,))
            cenouras = cursor.fetchone()[0]
            print(f"DEBUG: Cenouras do usuário: {cenouras}")

            if cenouras >= preco:
                # Obter cartas com base na categoria
                if categoria == 'geral':
                    cartas = obter_cartas_do_inventario(quantidade)
                else:
                    cartas = obter_cartas_categoria_do_inventario(quantidade, categoria)

                print(f"DEBUG: Cartas retornadas: {cartas}")

                if isinstance(cartas, list):
                    atualizar_inventario(id_usuario, cartas)
                    cursor.execute("UPDATE usuarios SET cenouras = cenouras - %s WHERE id_usuario = %s", (preco, id_usuario))
                    conn.commit()

                    globals.cartas_compradas_dict[id_usuario] = cartas

                    bot.edit_message_caption(caption=f"Compra realizada com sucesso! Você comprou {quantidade} cartas de {categoria.capitalize()}.", chat_id=call.message.chat.id, message_id=call.message.message_id)
                    mostrar_cartas_compradas(call.message.chat.id, cartas, id_usuario, 1, call.message.message_id)
                else:
                    bot.edit_message_caption(caption="Erro ao buscar cartas. Tente novamente mais tarde.", chat_id=call.message.chat.id, message_id=call.message.message_id)
            else:
                bot.edit_message_caption(caption="Cenouras insuficientes para realizar a compra.", chat_id=call.message.chat.id, message_id=call.message.message_id)
        else:
            bot.edit_message_caption(caption="Pacote inválido.", chat_id=call.message.chat.id, message_id=call.message.message_id)

    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        fechar_conexao(cursor, conn)

def obter_cartas_do_inventario(quantidade):
    conn, cursor = conectar_banco_dados()
    
    # Obter cartas do banco de inventário
    query_inventario = """
    SELECT bi.id_personagem, p.nome, p.subcategoria, p.imagem, p.emoji
    FROM banco_inventario bi
    JOIN personagens p ON bi.id_personagem = p.id_personagem
    WHERE bi.quantidade > 0
    ORDER BY RAND() LIMIT %s
    """
    cursor.execute(query_inventario, (quantidade,))
    cartas_inventario = cursor.fetchall()

    # Obter cartas de eventos
    query_evento = """
    SELECT e.id_personagem, e.nome, e.subcategoria, e.imagem, e.emoji
    FROM evento e
    ORDER BY RAND() LIMIT %s
    """
    # Selecionar uma fração de cartas do evento
    quantidade_evento = max(1, quantidade // 10)  # Por exemplo, 25% das cartas podem ser de eventos
    cursor.execute(query_evento, (quantidade_evento,))
    cartas_evento = cursor.fetchall()

    # Combinar cartas do inventário e do evento
    todas_cartas = cartas_inventario + cartas_evento
    random.shuffle(todas_cartas)  # Embaralha a lista de cartas

    fechar_conexao(cursor, conn)
    return todas_cartas


def obter_cartas_categoria_do_inventario(quantidade, categoria):
    conn, cursor = conectar_banco_dados()
    
    # Obter cartas da categoria especificada no banco de inventário
    query_inventario = """
    SELECT bi.id_personagem, p.nome, p.subcategoria, p.imagem, p.emoji
    FROM banco_inventario bi
    JOIN personagens p ON bi.id_personagem = p.id_personagem
    WHERE bi.quantidade > 0 AND p.categoria = %s
    ORDER BY RAND() LIMIT %s
    """
    cursor.execute(query_inventario, (categoria, quantidade))
    cartas_inventario = cursor.fetchall()

    # Obter cartas de eventos
    query_evento = """
    SELECT e.id_personagem, e.nome, e.subcategoria, e.imagem, e.emoji
    FROM evento e
    ORDER BY RAND() LIMIT %s
    """
    # Selecionar uma fração de cartas do evento
    quantidade_evento = max(1, quantidade // 10)  # Por exemplo, 25% das cartas podem ser de eventos
    cursor.execute(query_evento, (quantidade_evento,))
    cartas_evento = cursor.fetchall()

    # Combinar cartas do inventário e do evento
    todas_cartas = cartas_inventario + cartas_evento
    random.shuffle(todas_cartas)  # Embaralha a lista de cartas

    fechar_conexao(cursor, conn)
    return todas_cartas


@bot.callback_query_handler(func=lambda call: call.data == 'cancelar_compra_vendinha')
def cancelar_compra_vendinha(call):
    bot.edit_message_caption(caption="Poxa, Até logo!", chat_id=call.message.chat.id, message_id=call.message.message_id)
    
    
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

def mostrar_cartas_compradas(chat_id, cartas, id_usuario, pagina_atual=1, message_id=None):
    try:
        # Debug: Verificar a lista de cartas recebidas
        print(f"DEBUG: Lista de cartas recebidas: {cartas}")

        # Verificar se todas as cartas têm uma estrutura correta
        cartas_ordenadas = sorted(cartas, key=lambda x: int(x[0]) if isinstance(x[0], str) and x[0].isdigit() else x[0])
        
        total_cartas = len(cartas_ordenadas)
        total_paginas = (total_cartas // 20) + (1 if total_cartas % 20 > 0 else 0)

        print(f"DEBUG: Total de cartas compradas: {total_cartas}, Total de páginas: {total_paginas}, Página atual: {pagina_atual}")

        offset = (pagina_atual - 1) * 20
        cartas_pagina = cartas_ordenadas[offset:offset + 20]

        mensagem = "📦 Cartas recebidas:\n\n"
        for carta in cartas_pagina:
            print(f"DEBUG: Carta processada: {carta}")  # Verificar a estrutura da carta
            id_personagem, nome, subcategoria, url_imagem, emoji = carta

            # Obter quantidade atual no inventário
            quantidade_atual = obter_quantidade_atual(id_usuario, id_personagem)
            if quantidade_atual is not None:
                mensagem += f"{emoji}| {id_personagem} — {nome} de {subcategoria} - seu inventário: {quantidade_atual} (+1)\n"
            else:
                mensagem += f"{emoji}| {id_personagem} — {nome} de {subcategoria} - seu inventário: 1 (+1)\n"

        mensagem += f"\nPágina {pagina_atual}/{total_paginas}"

        markup = botoes_paginacao_cartas_compradas(pagina_atual, total_paginas)

        if message_id:
            try:
                bot.edit_message_text(mensagem, chat_id=chat_id, message_id=message_id, reply_markup=markup)
            except Exception as e:
                print(f"DEBUG: Erro ao editar a mensagem: {e}")
                bot.send_message(chat_id, mensagem, reply_markup=markup)
        else:
            bot.send_message(chat_id, mensagem, reply_markup=markup)

    except Exception as e:
        print(f"DEBUG: Erro em mostrar_cartas_compradas: {e}")



@bot.message_handler(commands=['pesca', 'pescar'])
def pescar(message):
    try:
        print("Comando pescar acionado")
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
        newrelic.agent.record_exception()    
        bot.send_message(message.chat.id, "Você foi banido permanentemente do garden. Entre em contato com o suporte caso haja dúvidas.", reply_to_message_id=message.message_id)

@bot.message_handler(commands=['spicnic'])
def spicnic_command(message):
    try:
        chat_id = message.chat.id
        eu = message.from_user.id
        meunome = message.from_user.first_name
        bot_id = 7088149058
        
        # Verificar se o comando está sendo usado em resposta a uma mensagem
        if not message.reply_to_message:
            bot.send_message(chat_id, "Responda a uma mensagem contendo /gid para iniciar a troca simplificada.")
            return
        
        voce = message.reply_to_message.from_user.id
        seunome = message.reply_to_message.from_user.first_name
        
        # Extrair o GID da mensagem de resposta
        mensagem_resposta = message.reply_to_message.text
        if not mensagem_resposta.startswith("/gid"):
            bot.send_message(chat_id, "Responda a uma mensagem com o comando /gid para realizar a troca.")
            return

        suacarta = mensagem_resposta.split()[1]
        
        # Verificar se o usuário incluiu a carta que deseja oferecer
        if len(message.text.split()) < 2:
            bot.send_message(chat_id, "Use o comando /spicnic seguido do ID da sua carta. Exemplo: /spicnic 19200.")
            return

        minhacarta = message.text.split()[1]

        # Verificar se os usuários possuem as cartas indicadas
        if verifica_inventario_troca(eu, minhacarta) == 0:
            bot.send_message(chat_id, f"🌦️ ་  {meunome}, você não possui o peixe {minhacarta} para trocar.", reply_to_message_id=message.message_id)
            return

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
        texto = (
            f"🥪 | Hora do picnic!\n\n"
            f"{meunome} oferece de lanche:\n"
            f" {idminhacarta} {emojiminhacarta}  —  {nomeminhacarta} de {subcategoriaminhacarta}\n\n"
            f"E {seunome} oferece de lanche:\n"
            f" {idsuacarta} {emojisuacarta}  —  {nomesuacarta} de {subcategoriasuacarta}\n\n"
            f"Podemos começar a comer, {seu_nome_formatado}?"
        )

        # Criar os botões de aceitar ou recusar a troca
        keyboard = types.InlineKeyboardMarkup()
        primeiro = [
            types.InlineKeyboardButton(text="✅", callback_data=f'troca_sim_{eu}_{voce}_{minhacarta}_{suacarta}_{chat_id}'),
            types.InlineKeyboardButton(text="❌", callback_data=f'troca_nao_{eu}_{voce}_{minhacarta}_{suacarta}_{chat_id}'),
        ]
        keyboard.add(*primeiro)

        # Enviar a mensagem de troca com imagem
        image_url = "https://telegra.ph/file/8672c8f91c8e77bcdad45.jpg"
        bot.send_photo(chat_id, image_url, caption=texto, reply_markup=keyboard, reply_to_message_id=message.reply_to_message.message_id)

    except Exception as e:
        traceback.print_exc()
        erro = traceback.format_exc()
        mensagem = f"Erro durante a troca. dados: {voce},{eu},{minhacarta},{suacarta}\n{erro}"
        bot.send_message(grupodeerro, mensagem, parse_mode="HTML")




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

@bot.message_handler(commands=['versubs'])
def versubs_command(message):
    try:
        conn, cursor = conectar_banco_dados()

        # Consulta para obter todos os nomes únicos de subs
        query = "SELECT DISTINCT sub_nome FROM sub ORDER BY sub_nome ASC"
        cursor.execute(query)
        subs = [row[0] for row in cursor.fetchall()]

        if not subs:
            bot.send_message(message.chat.id, "Não há subs registrados no momento.")
            return

        # Paginação
        total_subs = len(subs)
        itens_por_pagina = 15
        total_paginas = (total_subs // itens_por_pagina) + (1 if total_subs % itens_por_pagina > 0 else 0)

        # Exibe a primeira página
        enviar_pagina_subs(message.chat.id, 1, subs, total_paginas)

    except Exception as e:
        print(f"Erro ao processar comando /versubs: {e}")
        bot.send_message(message.chat.id, "Ocorreu um erro ao processar sua solicitação.")

    finally:
        fechar_conexao(cursor, conn)


def enviar_pagina_subs(chat_id, pagina_atual, subs, total_paginas, call=None):
    itens_por_pagina = 15
    offset = (pagina_atual - 1) * itens_por_pagina
    subs_pagina = subs[offset:offset + itens_por_pagina]

    resposta = "<b>🌻| Lista de Subgrupos Disponíveis:</b>\n\n"
    for sub in subs_pagina:
        resposta += f"• <i>{sub}</i>\n"

    resposta += f"\n📄 Página {pagina_atual}/{total_paginas}"

    # Criar a navegação
    markup = telebot.types.InlineKeyboardMarkup()
    if pagina_atual > 1:
        markup.add(telebot.types.InlineKeyboardButton("⬅️", callback_data=f"versubs_{pagina_atual-1}"))
    if pagina_atual < total_paginas:
        markup.add(telebot.types.InlineKeyboardButton("➡️", callback_data=f"versubs_{pagina_atual+1}"))

    if call:
        bot.edit_message_text(resposta, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="HTML")
    else:
        bot.send_message(chat_id, resposta, reply_markup=markup, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data.startswith('versubs_'))
def callback_pagina_versubs(call):
    try:
        pagina = int(call.data.split('_')[1])

        # Recarregar a lista de subs para paginar corretamente
        conn, cursor = conectar_banco_dados()
        query = "SELECT DISTINCT sub_nome FROM sub ORDER BY sub_nome ASC"
        cursor.execute(query)
        subs = [row[0] for row in cursor.fetchall()]
        total_subs = len(subs)
        itens_por_pagina = 15
        total_paginas = (total_subs // itens_por_pagina) + (1 if total_subs % itens_por_pagina > 0 else 0)

        # Enviar a página solicitada
        enviar_pagina_subs(call.message.chat.id, pagina, subs, total_paginas, call=call)

    except Exception as e:
        print(f"Erro ao processar callback de paginação: {e}")
        bot.send_message(call.message.chat.id, "Ocorreu um erro ao processar a navegação.")
    finally:
        fechar_conexao(cursor, conn)

@bot.message_handler(commands=['rep'])
def ver_repetidos_evento(message):
    try:
        print("Comando rep acionado")    
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
        newrelic.agent.record_exception()    
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
        newrelic.agent.record_exception()
    finally:
        fechar_conexao(cursor, conn)

@bot.message_handler(commands=['progresso'])
def progresso_evento(message):
    try:
        print("Comando progresso acionado")    
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
        newrelic.agent.record_exception()
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
        newrelic.agent.record_exception()
        
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
        newrelic.agent.record_exception()    

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
@bot.message_handler(commands=['saldo'])
def saldo_command(message):
    try:
        id_usuario = message.from_user.id
        
        conn, cursor = conectar_banco_dados()

        # Obter saldo total de cenouras do banco
        cursor.execute("SELECT SUM(quantidade_cenouras) FROM banco_cidade")
        total_cenouras_banco = cursor.fetchone()[0] or 0

        # Obter saldo total de cartas no banco de inventário
        cursor.execute("SELECT SUM(quantidade) FROM banco_inventario")
        total_cartas_banco = cursor.fetchone()[0] or 0

        # Obter saldo de cenouras do usuário
        cursor.execute("SELECT cenouras, iscas FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        resultado = cursor.fetchone()
        if resultado:
            saldo_cenouras_usuario, saldo_iscas_usuario = resultado
        else:
            saldo_cenouras_usuario, saldo_iscas_usuario = 0, 0

        # Montar a mensagem de saldo
        resposta = f"💰 <b>Saldo da Cidade:</b>\n"
        resposta += f"🥕 Total de cenouras: {total_cenouras_banco}\n"
        resposta += f"📦 Total de cartas: {total_cartas_banco}\n\n"
        resposta += f"💼 <b>Saldo do Camponês:</b>\n"
        resposta += f"🥕 Suas cenouras: {saldo_cenouras_usuario}\n"
        resposta += f"🪝 Suas iscas: {saldo_iscas_usuario}\n"

        # Enviar a mensagem
        bot.send_message(message.chat.id, resposta, parse_mode="HTML")
        
    except Exception as e:
        print(f"Erro ao processar comando /saldo: {e}")
        bot.reply_to(message, "Ocorreu um erro ao verificar seu saldo.")
    finally:
        fechar_conexao(cursor, conn)


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
        newrelic.agent.record_exception()    
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
        newrelic.agent.record_exception()    
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
        newrelic.agent.record_exception()
# Callback para tratar cestas
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
            ids_personagens = obter_ids_personagens_inventario_sem_evento(id_usuario_original, categoria)
            total_personagens_subcategoria = obter_total_personagens_subcategoria(categoria)
            total_registros = len(ids_personagens)
  
            if total_registros > 0:
                total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)
                mostrar_pagina_cesta_s(call.message, categoria, id_usuario_original, pagina, total_paginas, ids_personagens, total_personagens_subcategoria, nome_usuario, call=call)
            else:
                bot.reply_to(call.message, f"Nenhum personagem encontrado na cesta '{categoria}'.")

        elif tipo == 'f':
            ids_personagens_faltantes = obter_ids_personagens_faltantes_sem_evento(id_usuario_original, categoria)
            total_personagens_subcategoria = obter_total_personagens_subcategoria(categoria)
            total_registros = len(ids_personagens_faltantes)
  
            if total_registros > 0:
                total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)
                mostrar_pagina_cesta_f(call.message, categoria, id_usuario_original, pagina, total_paginas, ids_personagens_faltantes, total_personagens_subcategoria, nome_usuario, call=call)
            else:
                bot.reply_to(call.message, f"Todos os personagens na subcategoria '{categoria}' estão no seu inventário.")

        elif tipo == 'se':
            ids_personagens = obter_ids_personagens_inventario_com_evento(id_usuario_original, categoria)
            total_personagens_com_evento = obter_total_personagens_subcategoria(categoria)
            total_registros = len(ids_personagens)

            if total_registros > 0:
                total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)
                mostrar_pagina_cesta_s(call.message, categoria, id_usuario_original, pagina, total_paginas, ids_personagens, total_personagens_com_evento, nome_usuario, call=call)
            else:
                bot.reply_to(call.message, f"Nenhum personagem encontrado na cesta '{categoria}'.")

        elif tipo == 'fe':
            ids_personagens_faltantes = obter_ids_personagens_faltantes_com_evento(id_usuario_original, categoria)
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
            newrelic.agent.record_exception()
    except Exception as e:
        traceback.print_exc()
        erro = traceback.format_exc()
        mensagem = f"Alerta de erro carta pescadas. Erro: {e}\n{erro}"
        bot.send_message(grupodeerro, mensagem, parse_mode="HTML")

        newrelic.agent.record_exception()
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
        total_paginas = (quantidade_total_cartas + resultados_por_pagina - 1) // resultados_por_pagina

        if pagina == 1 and call.data.startswith("armazem_anterior_"):
            pagina = total_paginas
            offset = (pagina - 1) * resultados_por_pagina

        elif pagina == total_paginas and call.data.startswith("armazem_proxima_"):
            pagina = 1
            offset = 0

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
            SELECT id_personagem, 
                   emoji COLLATE utf8mb4_general_ci AS emoji, 
                   nome_personagem COLLATE utf8mb4_general_ci AS nome_personagem, 
                   subcategoria COLLATE utf8mb4_general_ci AS subcategoria, 
                   quantidade, 
                   categoria COLLATE utf8mb4_general_ci AS categoria, 
                   evento COLLATE utf8mb4_general_ci AS evento
            FROM (
                SELECT i.id_personagem, p.emoji COLLATE utf8mb4_general_ci AS emoji, p.nome COLLATE utf8mb4_general_ci AS nome_personagem, p.subcategoria COLLATE utf8mb4_general_ci AS subcategoria, i.quantidade, p.categoria COLLATE utf8mb4_general_ci AS categoria, '' COLLATE utf8mb4_general_ci AS evento
                FROM inventario i
                JOIN personagens p ON i.id_personagem = p.id_personagem
                WHERE i.id_usuario = {id_usuario} AND i.quantidade > 0

                UNION ALL

                SELECT e.id_personagem, e.emoji COLLATE utf8mb4_general_ci AS emoji, e.nome COLLATE utf8mb4_general_ci AS nome_personagem, e.subcategoria COLLATE utf8mb4_general_ci AS subcategoria, 0 AS quantidade, e.categoria COLLATE utf8mb4_general_ci AS categoria, e.evento COLLATE utf8mb4_general_ci AS evento
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
            LIMIT {resultados_por_pagina} OFFSET {offset}
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

            id_fav_usuario, emoji_fav, nome_fav, subcategoria_fav, imagem_fav = obter_favorito(id_usuario)

            resposta = f"💌 | Cartas no armazém de {usuario}:\n\n🩷 ∙ {id_fav_usuario} — {nome_fav} de {subcategoria_fav}\n\n" if id_fav_usuario is not None else f"💌 | Cartas no armazém de {usuario}:\n\n"

            for carta in resultados:
                id_carta, emoji_carta, nome_carta, subcategoria_carta, quantidade_carta, categoria_carta, evento_carta = carta

                quantidade_carta = int(quantidade_carta) if quantidade_carta is not None else 0

                if categoria_carta == 'evento' and (int(id_carta) < 10000 and int(id_carta) != 102):
                    emoji_carta = obter_emoji_evento(evento_carta)
                    repetida = "" if quantidade_carta > 1 else ""
                    letra_quantidade = ""
                else:
                    letra_quantidade = (
                        "🌾" if 2 <= quantidade_carta <= 4 else
                        "🌼" if 5 <= quantidade_carta <= 9 else
                        "☀️" if 10 <= quantidade_carta <= 19 else
                        "🍯️" if 20 <= quantidade_carta <= 29 else
                        "🐝" if 30 <= quantidade_carta <= 39 else
                        "🌻" if 40 <= quantidade_carta <= 49 else
                        "👑" if 50 <= quantidade_carta <= 101 else
                        "" 
                    )
                    repetida = "" if quantidade_carta > 1 else ""

                resposta += f" {emoji_carta} <code>{id_carta}</code> • {nome_carta} - {subcategoria_carta} {letra_quantidade}{repetida}\n"

            resposta += f"\n{pagina}/{total_paginas}"
            bot.edit_message_caption(chat_id=chat_id, message_id=call.message.message_id, caption=resposta, reply_markup=markup, parse_mode="HTML")

        else:
            bot.answer_callback_query(callback_query_id=call.id, text="Nenhuma carta encontrada.")
    except mysql.connector.Error as err:
        print(f"Erro de SQL: {err}")
        newrelic.agent.record_exception()    
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
        newrelic.agent.record_exception()    
        print(f"Erro ao processar callback de subcategoria: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('cenourar_sim_'))
def callback_cenourar(call):
    try:
        data_parts = call.data.split("_")
        acao = data_parts[1]
        id_usuario = int(data_parts[2])
        id_personagem = data_parts[3] if len(data_parts) >= 3 else ""
        print(data_parts)
        if acao == "sim":
            cenourar_carta(call, id_usuario, id_personagem)
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
        newrelic.agent.record_exception()    
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
        newrelic.agent.record_exception()
    finally:
        cursor.close()
        conn.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith('compras_iscas_'))
def callback_compras_iscas(call):
    try:
        compras_iscas_callback(call)
    except Exception as e:
        print(f"Erro ao processar callback de compras iscas: {e}")
        newrelic.agent.record_exception()
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
        newrelic.agent.record_exception()    
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
        newrelic.agent.record_exception()    
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
        print(f"Erro ao processar a compra para o usuário {id_usuario}: {e}")

        
@bot.message_handler(commands=['setmusica','setmusic'])
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
        newrelic.agent.record_exception()    
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
        newrelic.agent.record_exception()     
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

        # Verificar se o usuário existe
        cursor.execute(query_verificar_usuario, (id_usuario,))
        usuario_existe = cursor.fetchone()[0]

        if usuario_existe > 0:
            # Obter perfil do usuário
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

            # Verificar se o usuário é VIP
            query_verificar_vip = "SELECT COUNT(*) FROM vips WHERE id_usuario = %s"
            cursor.execute(query_verificar_vip, (id_usuario,))
            is_vip = cursor.fetchone()[0] > 0

            # Obter estado de casamento
            query_obter_casamento = """
                SELECT c.id_personagem, COALESCE(p.nome, e.nome) AS nome_parceiro
                FROM casamentos c
                LEFT JOIN personagens p ON c.id_personagem = p.id_personagem
                LEFT JOIN evento e ON c.id_personagem = e.id_personagem
                WHERE c.user_id = %s AND c.estado = 'casado'
            """
            cursor.execute(query_obter_casamento, (id_usuario,))
            casamento = cursor.fetchone()

            # Construir a resposta
            if perfil:
                nome, nome_usuario, fav, adm, qntcartas, cenouras, iscas, bio, musica, pronome, privado, user, beta, nome_fav, imagem_fav = perfil
                resposta = f"<b>Perfil de {nome}</b>\n\n" \
                           f"✨ Fav: {fav} — {nome_fav}\n\n"

                if is_vip:
                    resposta += "<i>🍃 Agricultor do Garden</i>\n\n"

                # Mostrar estado de casamento
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

                # Enviar a resposta do perfil
                enviar_perfil(message.chat.id, resposta, imagem_fav, fav, id_usuario, message)

        else:
            bot.send_message(message.chat.id, "Você ainda não iniciou o bot. Use /start para começar.", reply_to_message_id=message.message_id)

    except Exception as e:
        print(f"Erro ao verificar perfil: {e}")
        bot.send_message(message.chat.id, f"Erro ao verificar perfil: {e}", reply_to_message_id=message.message_id)

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
        newrelic.agent.record_exception()
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
        apagar_cartas_quantidade_zero_ou_negativa()
        if tipo in ['s', 'se']:
            subcategoria_proxima = encontrar_subcategoria_proxima(subcategoria)
            if not subcategoria_proxima:
                bot.reply_to(message, "Espécie não identificada. Você digitou certo? 🤭")
                return

            ids_personagens = obter_ids_personagens_inventario(id_usuario, subcategoria_proxima)
            print(ids_personagens)
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
            print(ids_personagens_faltantes)
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
                mensagem = f"<b>🌳 Submenus na subcategoria {subcategoria.title()}:</b>\n\n"
                for submenu in submenus:
                    mensagem += f"🍎 {subcategoria.title()}- {submenu}\n"
            else:
                mensagem = f"Não foram encontrados submenus para a subcategoria '{subcategoria.title()}'."

            bot.send_message(message.chat.id, mensagem, parse_mode="HTML", reply_to_message_id=message.message_id)

    except Exception as e:
        print(f"Erro ao processar comando /submenus: {e}")

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
            mensagem = "<b>🌳 Todos os Submenus: </b>\n\n"
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

    finally:
        fechar_conexao(cursor, conn)
        
def encontrar_submenu_proximo(submenu):
    try:
        conn, cursor = conectar_banco_dados()
        query = "SELECT DISTINCT submenu FROM personagens WHERE submenu LIKE %s LIMIT 1"
        cursor.execute(query, (f"%{submenu}%",))
        resultado = cursor.fetchone()
        return resultado[0] if resultado else None
    except Exception as e:
        print(f"Erro ao encontrar submenu mais próximo: {e}")
        return None
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

        submenu_proximo = encontrar_submenu_proximo(submenu)
        if not submenu_proximo:
            bot.reply_to(message, "Submenu não identificado. Verifique se digitou corretamente.")
            return

        id_usuario = message.from_user.id
        nome_usuario = message.from_user.first_name

        conn, cursor = conectar_banco_dados()

        # Consulta para obter todos os personagens do submenu
        query_todos = """
        SELECT id_personagem, nome, subcategoria
        FROM personagens
        WHERE submenu = %s
        """
        cursor.execute(query_todos, (submenu_proximo,))
        todos_personagens = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}

        if not todos_personagens:
            bot.reply_to(message, f"O submenu '{submenu_proximo}' não existe.")
            return

        # Consulta para obter os personagens que o usuário possui no submenu
        query_possui = """
        SELECT per.id_personagem, per.nome, per.subcategoria
        FROM inventario inv
        JOIN personagens per ON inv.id_personagem = per.id_personagem
        WHERE inv.id_usuario = %s AND per.submenu = %s
        """
        cursor.execute(query_possui, (id_usuario, submenu_proximo))
        personagens_possui = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}

        subcategoria = next(iter(todos_personagens.values()), ("", ""))[1]  # Definindo subcategoria para uso na mensagem

        if tipo == 's':
            if personagens_possui:
                mensagem = f"☀️ Peixes do submenu na cesta de {nome_usuario}!\n\n"
                mensagem += f"🌳 | {subcategoria} \n"
                mensagem += f"🍎 | {submenu_proximo}\n"
                mensagem += f"🐟 | {len(personagens_possui)}/{len(todos_personagens)}\n\n"
                for id_personagem, (nome, subcategoria) in personagens_possui.items():
                    mensagem += f"<code>{id_personagem}</code> • {nome}\n"
            else:
                mensagem = f"🌧️ Você não possui nenhum personagem neste submenu."

        elif tipo == 'f':
            personagens_faltantes = {id_personagem: (nome, subcategoria) for id_personagem, (nome, subcategoria) in todos_personagens.items() if id_personagem not in personagens_possui}
            if personagens_faltantes:
                mensagem = f"🌧️ Faltam do submenu na cesta de {nome_usuario}:\n\n"
                mensagem += f"🌳 | {subcategoria} \n"
                mensagem += f"🍎 | {submenu_proximo}\n"
                mensagem += f"🐟 | {len(personagens_faltantes)}/{len(todos_personagens)}\n\n"
                for id_personagem, (nome, subcategoria) in personagens_faltantes.items():
                    mensagem += f"<code>{id_personagem}</code> • {nome}\n"
            else:
                mensagem = f"☀️ Nada como a alegria de ter todos os peixes de {submenu_proximo} na cesta!"

        else:
            bot.reply_to(message, "Tipo inválido. Use 's' para os personagens que você possui e 'f' para os que você não possui.")
            return

        bot.send_message(message.chat.id, mensagem, parse_mode="HTML")

    except Exception as e:
        print(f"Erro ao processar comando /submenu: {e}")

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
def enviar_pagina(chat_id, message_id, pagina, tipo, personagens, total_personagens, sub_nome, nome_usuario, imagem_subgrupo, id_usuario, is_first_page=False):
    itens_por_pagina = 15  # Sempre paginar em 15 itens, independente do tipo
    offset = (pagina - 1) * itens_por_pagina
    ids_pagina = list(personagens.items())[offset:offset + itens_por_pagina]

    if tipo == 'all':
        mensagem = f"Peixes do subgrupo {sub_nome.capitalize()}:\n\n"
    else:
        mensagem = f"☀️ Peixes do subgrupo {sub_nome.capitalize()} na cesta de {nome_usuario}!\n\n"

    # Adicionar a linha de páginas e quantidade para todos os tipos
    if len(personagens) > itens_por_pagina:
        mensagem += f"📑 | {pagina}/{(total_personagens // itens_por_pagina) + (1 if total_personagens % itens_por_pagina > 0 else 0)}\n"
    
    mensagem += f"🐟 | {len(personagens)}/{total_personagens}\n\n"

    for id_personagem, (nome, subcategoria, emoji) in ids_pagina:  # Inclui o emoji na tupla
        mensagem += f"{emoji} <code>{id_personagem}</code> • {nome} de {subcategoria}\n"  # Exibe o emoji

    markup = types.InlineKeyboardMarkup()

    # Adiciona botões de navegação apenas se houver mais de 15 itens
    if len(personagens) > itens_por_pagina:
        if pagina > 1:
            markup.add(types.InlineKeyboardButton("⬅️", callback_data=f"{tipo}_pagina_{pagina-1}_{sub_nome}_{id_usuario}"))
        if offset + itens_por_pagina < total_personagens:
            markup.add(types.InlineKeyboardButton("➡️", callback_data=f"{tipo}_pagina_{pagina+1}_{sub_nome}_{id_usuario}"))

    has_buttons = len(markup.to_dict().get('inline_keyboard', [])) > 0

    if is_first_page:
        if imagem_subgrupo:
            bot.send_photo(chat_id, imagem_subgrupo, caption=mensagem, parse_mode="HTML", reply_markup=markup if has_buttons else None)
        else:
            bot.send_message(chat_id, mensagem, parse_mode="HTML", reply_markup=markup if has_buttons else None)
    else:
        if imagem_subgrupo:
            bot.edit_message_media(media=types.InputMediaPhoto(imagem_subgrupo, caption=mensagem, parse_mode="HTML"), chat_id=chat_id, message_id=message_id, reply_markup=markup if has_buttons else None)
        else:
            bot.edit_message_text(mensagem, chat_id=chat_id, message_id=message_id, parse_mode="HTML", reply_markup=markup if has_buttons else None)


@bot.message_handler(commands=['sub'])
def sub_command(message):
    try:
        parts = message.text.split(' ', 2)
        if len(parts) < 2:
            bot.reply_to(message, "Por favor, forneça o tipo ('s' ou 'f') e o nome do sub após o comando, por exemplo: /sub s loona")
            return

        tipo = parts[1].strip().lower()
        sub_nome = parts[2].strip().lower() if len(parts) > 2 else None

        id_usuario = message.from_user.id
        nome_usuario = message.from_user.first_name

        conn, cursor = conectar_banco_dados()

        # Corrigir a consulta para incluir o emoji
        query_todos = """
        SELECT s.id_personagem, p.nome, p.subcategoria, p.emoji
        FROM sub s
        JOIN personagens p ON s.id_personagem = p.id_personagem
        WHERE s.sub_nome = %s
        """
        cursor.execute(query_todos, (sub_nome,))
        # Agora, incluir o emoji corretamente
        todos_personagens = {row[0]: (row[1], row[2], row[3]) for row in cursor.fetchall()}

        if not todos_personagens:
            bot.reply_to(message, f"O sub '{sub_nome}' não existe.")
            return

        # Adicionar o emoji também no inventário
        query_possui = """
        SELECT s.id_personagem, p.nome, p.subcategoria, p.emoji
        FROM inventario inv
        JOIN sub s ON inv.id_personagem = s.id_personagem
        JOIN personagens p ON s.id_personagem = p.id_personagem
        WHERE inv.id_usuario = %s AND s.sub_nome = %s
        """
        cursor.execute(query_possui, (id_usuario, sub_nome))
        personagens_possui = {row[0]: (row[1], row[2], row[3]) for row in cursor.fetchall()}

        query_imagem = """
        SELECT Imagem FROM subcategorias WHERE nomesub = %s
        """
        cursor.execute(query_imagem, (sub_nome,))
        resultado_imagem = cursor.fetchone()
        imagem_subgrupo = resultado_imagem[0] if resultado_imagem else None

        subcategoria = next(iter(todos_personagens.values()), ("", ""))[1]

        if tipo == 's':
            if personagens_possui:
                enviar_pagina(message.chat.id, message.message_id, 1, 's', personagens_possui, len(todos_personagens), sub_nome, nome_usuario, imagem_subgrupo, id_usuario, is_first_page=True)
            else:
                bot.reply_to(message, f"🌧️ Você não possui nenhum personagem neste subgrupo.")

        elif tipo == 'f':
            personagens_faltantes = {id_personagem: (nome, subcategoria, emoji) for id_personagem, (nome, subcategoria, emoji) in todos_personagens.items() if id_personagem not in personagens_possui}
            if personagens_faltantes:
                enviar_pagina(message.chat.id, message.message_id, 1, 'f', personagens_faltantes, len(todos_personagens), sub_nome, nome_usuario, imagem_subgrupo, id_usuario, is_first_page=True)
            else:
                bot.reply_to(message, f"☀️ Nada como a alegria de ter todos os personagens de {sub_nome.capitalize()} na cesta!")

        elif tipo == 'all':
            enviar_pagina(message.chat.id, message.message_id, 1, 'all', todos_personagens, len(todos_personagens), sub_nome, "", imagem_subgrupo, id_usuario, is_first_page=True)

        else:
            bot.reply_to(message, "Tipo inválido. Use 's' para os personagens que você possui, 'f' para os que você não possui, ou 'all' para ver todos.")

    except Exception as e:
        print(f"Erro ao processar comando /sub: {e}")

    finally:
        fechar_conexao(cursor, conn)


@bot.callback_query_handler(func=lambda call: call.data.startswith(('s_pagina_', 'f_pagina_', 'all_pagina_')))
def callback_pagina(call):
    try:
        partes = call.data.split('_')
        tipo = partes[0]
        pagina = int(partes[2])
        sub_nome = partes[3]
        id_usuario = int(partes[4])  # O ID do usuário original que iniciou a interação

        conn, cursor = conectar_banco_dados()

        # Consulta para todos os personagens, incluindo o emoji
        query_todos = """
        SELECT s.id_personagem, p.nome, p.subcategoria, p.emoji
        FROM sub s
        JOIN personagens p ON s.id_personagem = p.id_personagem
        WHERE s.sub_nome = %s
        """
        cursor.execute(query_todos, (sub_nome,))
        todos_personagens = {row[0]: (row[1], row[2], row[3]) for row in cursor.fetchall()}

        # Consulta para os personagens que o usuário possui, incluindo o emoji
        query_possui = """
        SELECT s.id_personagem, p.nome, p.subcategoria, p.emoji
        FROM inventario inv
        JOIN sub s ON inv.id_personagem = s.id_personagem
        JOIN personagens p ON s.id_personagem = p.id_personagem
        WHERE inv.id_usuario = %s AND s.sub_nome = %s
        """
        cursor.execute(query_possui, (id_usuario, sub_nome))
        personagens_possui = {row[0]: (row[1], row[2], row[3]) for row in cursor.fetchall()}

        # Consulta para obter a imagem do subgrupo
        query_imagem = """
        SELECT Imagem FROM subcategorias WHERE nomesub = %s
        """
        cursor.execute(query_imagem, (sub_nome,))
        resultado_imagem = cursor.fetchone()
        imagem_subgrupo = resultado_imagem[0] if resultado_imagem else None

        nome_usuario = call.from_user.first_name

        if tipo == 's':
            enviar_pagina(call.message.chat.id, call.message.message_id, pagina, 's', personagens_possui, len(todos_personagens), sub_nome, nome_usuario, imagem_subgrupo, id_usuario)
        elif tipo == 'f':
            personagens_faltantes = {id_personagem: (nome, subcategoria, emoji) for id_personagem, (nome, subcategoria, emoji) in todos_personagens.items() if id_personagem not in personagens_possui}
            enviar_pagina(call.message.chat.id, call.message.message_id, pagina, 'f', personagens_faltantes, len(todos_personagens), sub_nome, nome_usuario, imagem_subgrupo, id_usuario)
        elif tipo == 'all':
            enviar_pagina(call.message.chat.id, call.message.message_id, pagina, 'all', todos_personagens, len(todos_personagens), sub_nome, nome_usuario, imagem_subgrupo, id_usuario)

        bot.answer_callback_query(call.id)

    except Exception as e:
        print(f"Erro ao processar callback de navegação: {e}")
        bot.send_message(call.message.chat.id, "Ocorreu um erro ao processar a navegação.")
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
def verificar_trocas_suspeitas():
    try:
        conn, cursor = conectar_banco_dados()

        query = """
        SELECT 
            hd1.id_usuario_doacao AS usuario1,
            hd1.id_usuario_recebedor AS usuario2,
            hd1.id_personagem_carta,
            hd1.data_hora AS data_doacao1,
            hd2.data_hora AS data_doacao2
        FROM 
            historico_doacoes hd1
        JOIN 
            historico_doacoes hd2 
        ON 
            hd1.id_usuario_recebedor = hd2.id_usuario_doacao
            AND hd1.id_usuario_doacao = hd2.id_usuario_recebedor
            AND hd1.id_personagem_carta = hd2.id_personagem_carta
        WHERE 
            hd2.data_hora <= hd1.data_hora + INTERVAL 24 HOUR
            AND hd2.data_hora > hd1.data_hora
        """

        cursor.execute(query)
        trocas_suspeitas = cursor.fetchall()

        if trocas_suspeitas:
            for usuario1, usuario2, id_personagem_carta, data_doacao1, data_doacao2 in trocas_suspeitas:
                nome_usuario1 = obter_nome_usuario(usuario1, cursor)
                nome_usuario2 = obter_nome_usuario(usuario2, cursor)
                alerta = (f"⚠️ Alerta de troca suspeita! ⚠️\n"
                          f"A carta {id_personagem_carta} foi doada de {nome_usuario1} para {nome_usuario2} "
                          f"em {data_doacao1}, e devolvida em {data_doacao2}.\n"
                          f"Essa troca ocorreu dentro de 24 horas.")
                enviar_alerta_para_grupo(alerta)
        else:
            print("Nenhuma troca suspeita detectada.")

    except Exception as e:
        print(f"Erro ao verificar trocas suspeitas: {e}")
    finally:
        fechar_conexao(cursor, conn)

def enviar_alerta_para_grupo(alerta):
    grupo_id = -4209628464
    bot.send_message(grupo_id, alerta)

def obter_nome_usuario(id_usuario, cursor):
    query = "SELECT nome FROM usuarios WHERE id_usuario = %s"
    cursor.execute(query, (id_usuario,))
    resultado = cursor.fetchone()
    return resultado[0] if resultado else "Usuário Desconhecido"
       
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
        
@bot.message_handler(commands=['banco'])
def banco_command(message):
    try:
        parts = message.text.split(' ', 2)
        categoria = parts[1].strip() if len(parts) > 1 else None
        subcategoria = parts[2].strip() if len(parts) > 2 else None

        conn, cursor = conectar_banco_dados()

        # Construir a consulta SQL com base na categoria e subcategoria
        query = "SELECT p.id_personagem, bi.quantidade, p.nome, p.subcategoria, p.emoji FROM banco_inventario bi JOIN personagens p ON bi.id_personagem = p.id_personagem"
        query_params = []

        if categoria:
            query += " WHERE p.categoria = %s"
            query_params.append(categoria)
        if subcategoria:
            query += " AND p.subcategoria = %s"
            query_params.append(subcategoria)

        query += " ORDER BY p.id_personagem ASC"
        
        cursor.execute(query, tuple(query_params))
        cartas_banco = cursor.fetchall()

        if not cartas_banco:
            bot.send_message(message.chat.id, "Não há cartas no banco para os critérios especificados.")
            return

        total_paginas = (len(cartas_banco) // 30) + (1 if len(cartas_banco) % 30 > 0 else 0)
        total_cartas = sum([quantidade for _, quantidade, _, _, _ in cartas_banco])
        
        mostrar_cartas_banco(message.chat.id, 1, total_paginas, cartas_banco, total_cartas, message.message_id, categoria, subcategoria)

    except Exception as e:
        print(f"Erro ao processar o comando /banco: {e}")
        bot.send_message(message.chat.id, "Erro ao processar o comando.")
    finally:
        fechar_conexao(cursor, conn)


@bot.callback_query_handler(func=lambda call: call.data.startswith('banco_pagina_'))
def callback_banco_pagina(call):
    data = call.data.split('_')
    pagina = int(data[2])
    categoria = data[3] if len(data) > 3 and data[3] else None
    subcategoria = data[4] if len(data) > 4 and data[4] else None

    conn, cursor = conectar_banco_dados()

    query = "SELECT p.id_personagem, bi.quantidade, p.nome, p.subcategoria, p.emoji FROM banco_inventario bi JOIN personagens p ON bi.id_personagem = p.id_personagem"
    query_params = []

    if categoria:
        query += " WHERE p.categoria = %s"
        query_params.append(categoria)
    if subcategoria:
        query += " AND p.subcategoria = %s"
        query_params.append(subcategoria)

    query += " ORDER BY p.id_personagem ASC"
    
    cursor.execute(query, tuple(query_params))
    cartas_banco = cursor.fetchall()

    total_paginas = (len(cartas_banco) // 30) + (1 if len(cartas_banco) % 30 > 0 else 0)
    total_cartas = sum([quantidade for _, quantidade, _, _, _ in cartas_banco])

    mostrar_cartas_banco(call.message.chat.id, pagina, total_paginas, cartas_banco, total_cartas, call.message.message_id, categoria, subcategoria)

    fechar_conexao(cursor, conn)

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
            elif call.data.startswith("bpronomes_"):
                try:
                    mostrar_opcoes_pronome(call.message.chat.id, call.message.message_id)
                except Exception as e:
                    import traceback
                    traceback.print_exc()
            elif call.data.startswith('troca_'):
                troca_callback(call)
    except Exception as e:
        import traceback
        traceback.print_exc()
# Função para mostrar opções de pronome ✅
def mostrar_opcoes_pronome(chat_id, message_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    itembtn1 = types.InlineKeyboardButton('Ele/dele', callback_data='pronomes_Ele/Dele')
    itembtn2 = types.InlineKeyboardButton('Ela/dela', callback_data='pronomes_Ela/Dela')
    itembtn3 = types.InlineKeyboardButton('Elu/delu', callback_data='pronomes_Elu/Delu')
    itembtn4 = types.InlineKeyboardButton('Outros', callback_data='pronomes_Outros')
    itembtn5 = types.InlineKeyboardButton('Todos', callback_data='pronomes_Todos')
    itembtn6 = types.InlineKeyboardButton('Remover Pronome', callback_data='pronomes_remove')
    itembtn7 = types.InlineKeyboardButton('❌ Cancelar', callback_data='pcancelar')
    markup.add(itembtn1, itembtn2, itembtn3, itembtn4, itembtn5, itembtn6)
    markup.add(itembtn7)

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
def verificar_e_adicionar_card_especial(id_usuario, subcategoria):
    conn, cursor = conectar_banco_dados()
    try:
        # Verificar se a subcategoria está completa
        ids_faltantes = obter_ids_personagens_faltantes(id_usuario, subcategoria)
        if not ids_faltantes:
            # Subcategoria completa, verificar se existe um card especial para ela
            query = "SELECT id_card, nome FROM cards_especiais WHERE subcategoria = %s"
            cursor.execute(query, (subcategoria,))
            card_especial = cursor.fetchone()

            if card_especial:
                id_card, nome_card = card_especial

                # Verificar se o usuário já possui o card especial
                query_possui_card = """
                SELECT COUNT(*) FROM inventario_especial 
                WHERE id_usuario = %s AND id_card = %s
                """
                cursor.execute(query_possui_card, (id_usuario, id_card))
                possui_card = cursor.fetchone()[0]

                if not possui_card:
                    # Adicionar o card especial ao inventário do usuário
                    query_adicionar_card = "INSERT INTO inventario_especial (id_usuario, id_card) VALUES (%s, %s)"
                    cursor.execute(query_adicionar_card, (id_usuario, id_card))
                    conn.commit()
                    return f"💎 {nome_card}"
        return None
    finally:
        fechar_conexao(cursor, conn)
@bot.message_handler(commands=['diamante'])
def mostrar_diamante_por_nome(message):
    try:
        args = message.text.split(' ', 1)
        if len(args) < 2:
            bot.reply_to(message, "Por favor, forneça o nome do card especial. Exemplo: /diamante Red Velvet")
            return

        nome_procurado = args[1].strip().lower()
        id_usuario = message.from_user.id

        conn, cursor = conectar_banco_dados()

        # Verificar se o usuário possui um card especial com o nome especificado
        query = """
        SELECT ce.nome, ce.imagem 
        FROM inventario_especial ie
        JOIN cards_especiais ce ON ie.id_card = ce.id_card
        WHERE ie.id_usuario = %s AND LOWER(ce.nome) = %s
        """
        cursor.execute(query, (id_usuario, nome_procurado))
        card = cursor.fetchone()

        if card:
            nome_card, imagem_card = card
            resposta = f"💎 {nome_card}"
            if imagem_card:
                bot.send_photo(message.chat.id, imagem_card, caption=resposta, parse_mode="HTML")
            else:
                bot.send_message(message.chat.id, resposta, parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, f"Você não possui um card especial com o nome '{nome_procurado}'.", parse_mode="HTML")

    except Exception as e:
        bot.send_message(message.chat.id, "Erro ao procurar o card especial.")
        print(f"Erro ao procurar o card especial: {e}")
    finally:
        fechar_conexao(cursor, conn)

@bot.message_handler(commands=['diamantes'])
def mostrar_diamantes(message):
    id_usuario = message.from_user.id
    conn, cursor = conectar_banco_dados()
    try:
        query = """
        SELECT ce.nome 
        FROM inventario_especial ie
        JOIN cards_especiais ce ON ie.id_card = ce.id_card
        WHERE ie.id_usuario = %s
        """
        cursor.execute(query, (id_usuario,))
        cards = cursor.fetchall()

        if cards:
            resposta = "💎 Seus cards especiais:\n\n"
            for card in cards:
                resposta += f"💎 {card[0]}\n"
        else:
            resposta = "Você não possui nenhum card especial no momento."

        bot.send_message(message.chat.id, resposta)

    except Exception as e:
        bot.send_message(message.chat.id, "Erro ao buscar seus cards especiais.")
        print(f"Erro ao buscar cards especiais: {e}")
    finally:
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
        # Verifica se o usuário é VIP
        cursor.execute("SELECT COUNT(*) FROM vips WHERE id_usuario = %s", (user_id,))
        is_vip = cursor.fetchone()[0] > 0

        # Recuperar os dados do diário do usuário
        cursor.execute("SELECT ultimo_diario, dias_consecutivos FROM diario WHERE id_usuario = %s", (user_id,))
        result = cursor.fetchone()

        if result:
            ultimo_diario, dias_consecutivos = result

            # Caso o usuário já tenha feito o diário hoje
            if ultimo_diario == today:
                bot.send_message(message.chat.id, "Você já recebeu suas cenouras hoje. Volte amanhã!")
                return

            # Caso ele tenha feito o diário ontem ou seja VIP e possa recuperar um dia
            if ultimo_diario == today - timedelta(days=1):
                dias_consecutivos += 1
            elif is_vip and ultimo_diario == today - timedelta(days=2):
                # Se o usuário é VIP, ele pode "recuperar" o dia perdido
                dias_consecutivos += 1
            else:
                # Resetar streak se perdeu mais de um dia
                dias_consecutivos = 1

            # Cenouras com base no streak
            cenouras = min(dias_consecutivos * 10, 100)

            # Atualizar o diário e as cenouras do usuário
            cursor.execute("UPDATE diario SET ultimo_diario = %s, dias_consecutivos = %s WHERE id_usuario = %s", (today, dias_consecutivos, user_id))
            cursor.execute("UPDATE usuarios SET cenouras = cenouras + %s WHERE id_usuario = %s", (cenouras, user_id))
            conn.commit()

        else:
            # Caso o usuário esteja registrando o diário pela primeira vez
            cenouras = 10
            dias_consecutivos = 1
            cursor.execute("INSERT INTO diario (id_usuario, ultimo_diario, dias_consecutivos) VALUES (%s, %s, %s)", (user_id, today, dias_consecutivos))
            cursor.execute("UPDATE usuarios SET cenouras = cenouras + %s WHERE id_usuario = %s", (cenouras, user_id))
            conn.commit()

        # Enviar mensagem de confirmação
        phrase = random.choice(phrases)
        fortune = random.choice(fortunes)
        bot.send_message(message.chat.id, f"<i>{phrase}</i>\n\n<b>{fortune}</b>\n\nVocê recebeu <i>{cenouras} cenouras</i>!\n\n<b>Dias consecutivos:</b> <i>{dias_consecutivos}</i>\n\n", parse_mode="HTML")

        # Pergunta se o usuário deseja adicionar uma anotação ao diário
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(text="Sim", callback_data="add_note"))
        markup.add(telebot.types.InlineKeyboardButton(text="Não", callback_data="cancel_note"))
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
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@bot.message_handler(commands=['setbio'])
def set_bio_command(message):

    id_usuario = message.from_user.id
    nome_usuario = message.from_user.first_name  # Obtém o nome do usuário
    command_parts = message.text.split(maxsplit=1)
    
    if len(command_parts) == 2:
        nova_bio = command_parts[1].strip()
        atualizar_coluna_usuario(id_usuario, 'bio', nova_bio)
        bot.send_message(message.chat.id, f"Bio do {nome_usuario} atualizada para: {nova_bio}")
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
@bot.message_handler(commands=['removefav'])
def remove_fav_command(message):
    id_usuario = message.from_user.id

    conn, cursor = conectar_banco_dados()
    cursor.execute("UPDATE usuarios SET fav = NULL WHERE id_usuario = %s", (id_usuario,))
    conn.commit()

    bot.send_message(message.chat.id, "Favorito removido com sucesso.", reply_to_message_id=message.message_id)

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


if __name__ == "__main__":
    app.run(host=WEBHOOK_LISTEN, port=int(WEBHOOK_PORT), debug=False)

