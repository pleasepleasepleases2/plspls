#Bibliotecas para interagir com o Telegram e HTTP
import telebot
import requests
import flask
import http.server
import socketserver
from telebot.types import InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import numpy as np
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
from gif import *
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
GRUPO_SUGESTAO = -4546359573
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

def bloquear_acao(user_id, acao, minutos):
    # Bloquear a ação por x minutos
    conn, cursor = conectar_banco_dados()
    fim_bloqueio = datetime.now() + timedelta(minutes=minutos)
    cursor.execute("INSERT INTO bloqueios (id_usuario, acao, fim_bloqueio) VALUES (%s, %s, %s)", (user_id, acao, fim_bloqueio))
    conn.commit()
    fechar_conexao(cursor, conn)

@bot.callback_query_handler(func=lambda call: call.data.startswith('votar_'))
def votar_usuario(call):
    id_usuario_avaliador = call.from_user.id
    data_parts = call.data.split('_')
    tipo_voto = data_parts[1]  # 'doce' ou 'fantasma'
    id_usuario_avaliado = int(data_parts[2])

    voto = 1 if tipo_voto == 'doce' else 0

    # Registrar o voto
    registrar_voto(id_usuario_avaliado, id_usuario_avaliador, voto)

    # Atualizar a contagem de votos
    doces, fantasmas = contar_votos(id_usuario_avaliado)

    # Atualizar os botões com a nova contagem
    markup = InlineKeyboardMarkup()
    botao_doce = InlineKeyboardButton(text=f"🍬  {doces}", callback_data=f"votar_doce_{id_usuario_avaliado}")
    botao_fantasma = InlineKeyboardButton(text=f"👻  {fantasmas}", callback_data=f"votar_fantasma_{id_usuario_avaliado}")
    markup.row(botao_doce, botao_fantasma)

    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)

# URL da imagem a ser enviada
url_imagem = "https://pub-6f23ef52e8614212a14d24b0cf55ae4a.r2.dev/BQACAgEAAxkBAAIcfGcVeT6gaLXd0DKA7aihUQJfV62hAAJMBQACSV6xRD2puYHoSyajNgQ.jpg"
def mudar_bio_usuario(user_id, bio_nova,chat_id):
    alterar_usuario(user_id, "bio", bio_nova,chat_id)
    bot.send_message(chat_id, f"😂 Travessura! Sua bio agora é: {bio_nova}.")
def mudar_musica_usuario(user_id, musica_nova,chat_id):
    alterar_usuario(user_id, "musica", musica_nova,chat_id)
    bot.send_message(chat_id, f"🎶 Travessura! Sua música agora é: {musica_nova}.")
def mudar_nome_usuario(user_id, nome_novo,chat_id):
    alterar_usuario(user_id, "nome", nome_novo,chat_id)
    bot.send_message(chat_id, f"😂 Travessura! Seu nome agora é {nome_novo}!")
def verificar_travessura(id_usuario):
    """
    Verifica quais travessuras estão ativas para o usuário.
    Retorna uma lista com os tipos de travessuras ativas.
    """
    conn, cursor = conectar_banco_dados()
    try:
        cursor.execute("""
            SELECT tipo_travessura
            FROM travessuras
            WHERE id_usuario = %s AND fim_travessura > NOW()
        """, (id_usuario,))
        travessuras_ativas = cursor.fetchall()
        return [row[0] for row in travessuras_ativas]  # Retorna uma lista com os tipos de travessuras ativas

    except Exception as e:
        print(f"Erro ao verificar travessuras: {e}")
        return []
    finally:
        fechar_conexao(cursor, conn)

def iniciar_demonio_roubo_carta(user_id, chat_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Selecionar uma carta aleatória do inventário do usuário
        cursor.execute("SELECT id_personagem, nome FROM inventario WHERE id_usuario = %s ORDER BY RAND() LIMIT 1", (user_id,))
        carta = cursor.fetchone()

        if carta:
            id_carta, nome_carta = carta
            palavra_desafio = gerar_palavra_desafio()

            # Enviar mensagem para o usuário com a palavra desafio
            bot.send_message(chat_id, f"👹 Um demônio está tentando roubar sua carta '{nome_carta}'! Responda rapidamente com a palavra: <b>{palavra_desafio}</b>", parse_mode="HTML")

            # Iniciar um temporizador de 10 segundos para o usuário responder
            threading.Timer(10.0, verificar_resposta, args=(user_id, id_carta, palavra_desafio, chat_id)).start()
        else:
            bot.send_message(chat_id, "Parece que você não tem nenhuma carta para o demônio roubar.")
    
    except Exception as e:
        print(f"Erro ao iniciar o roubo de carta pelo demônio: {e}")
    finally:
        fechar_conexao(cursor, conn)
def embaralhar_mensagem(mensagem):
    palavras = mensagem.split()
    random.shuffle(palavras)  # Embaralha as palavras da mensagem
    return ' '.join(palavras)  # Retorna a mensagem embaralhada

def ativar_protecao_travessura(user_id, horas_duracao):
    try:
        conn, cursor = conectar_banco_dados()
        
        # Definir o fim da proteção como o tempo atual mais a duração
        fim_protecao = datetime.now() + timedelta(hours=horas_duracao)
        
        # Verificar se já existe uma proteção para esse usuário
        cursor.execute("""
            SELECT id_usuario FROM protecoes_travessura WHERE id_usuario = %s
        """, (user_id,))
        resultado = cursor.fetchone()

        if resultado:
            # Atualizar o tempo de fim da proteção
            cursor.execute("""
                UPDATE protecoes_travessura SET fim_protecao = %s WHERE id_usuario = %s
            """, (fim_protecao, user_id))
        else:
            # Inserir uma nova proteção
            cursor.execute("""
                INSERT INTO protecoes_travessura (id_usuario, fim_protecao) VALUES (%s, %s)
            """, (user_id, fim_protecao))
        
        conn.commit()
        bot.send_message(user_id, f"🛡️ Você está protegido contra travessuras por {horas_duracao} horas!")
    
    except Exception as e:
        print(f"Erro ao ativar proteção: {e}")
        bot.send_message(user_id, "Ocorreu um erro ao tentar ativar sua proteção.")
    finally:
        fechar_conexao(cursor, conn)

def verificar_protecao_travessura(user_id):
    try:
        conn, cursor = conectar_banco_dados()
        
        # Verificar se o usuário tem proteção ativa
        cursor.execute("""
            SELECT fim_protecao FROM protecoes_travessura
            WHERE id_usuario = %s
        """, (user_id,))
        resultado = cursor.fetchone()

        if resultado:
            fim_protecao = resultado[0]
            # Se a proteção ainda está ativa (o tempo atual é menor que o fim)
            if datetime.now() < fim_protecao:
                return True
        
        return False  # Sem proteção ativa ou proteção expirada
    
    except Exception as e:
        print(f"Erro ao verificar a proteção contra travessuras: {e}")
        return False
    finally:
        fechar_conexao(cursor, conn)

def adicionar_carta_faltante_halloween(user_id, chat_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Obter todas as cartas do evento Halloween que o usuário ainda não possui
        query_faltantes_halloween = """
            SELECT e.id_personagem, e.nome 
            FROM evento e
            LEFT JOIN inventario i ON e.id_personagem = i.id_personagem AND i.id_usuario = %s
            WHERE e.evento = 'Festival das Abóboras' AND i.id_personagem IS NULL
        """
        cursor.execute(query_faltantes_halloween, (user_id,))
        cartas_faltantes = cursor.fetchall()

        if not cartas_faltantes:
            bot.send_message(user_id, "Parabéns! Mas você já tem todas as cartas do evento de Halloween.")
            return

        # Selecionar uma carta de Halloween aleatória
        carta_faltante = random.choice(cartas_faltantes)
        id_carta_faltante, nome_carta_faltante = carta_faltante

        # Adicionar a carta ao inventário
        cursor.execute("INSERT INTO inventario (id_usuario, id_personagem, quantidade) VALUES (%s, %s, 1)", (user_id, id_carta_faltante))
        conn.commit()

        # Enviar a mensagem informando a carta recebida
        bot.send_message(chat_id, f"🎃 Parabéns! Você encontrou uma carta do evento Halloween: {nome_carta_faltante} foi adicionada ao seu inventário.")

    except Exception as e:
        print(f"Erro ao adicionar carta de Halloween faltante: {e}")
    finally:
        fechar_conexao(cursor, conn)



def travessura_grupal(chat_id, user_id):
    try:
        chat_info = bot.get_chat(chat_id)

        # Verificar se o chat é um grupo (não precisa verificar se é privado, porque é acionado em grupo)
        if chat_info.type not in ["group", "supergroup"]:
            bot.send_message(chat_id, "👻 Travessuras grupais só podem ser realizadas em grupos ou supergrupos!")
            return

        # Obter a lista de participantes do grupo
        membros = bot.get_chat_members_count(chat_id)
        todos_participantes = [user.user.id for user in bot.get_chat_members(chat_id, 0, membros)]

        # Garantir que o usuário que acionou o comando esteja na lista
        if user_id not in todos_participantes:
            todos_participantes.append(user_id)

        # Sortear de 1 a 10 pessoas (incluindo quem acionou)
        num_pessoas = random.randint(1, 10)
        sorteados = random.sample(todos_participantes, min(num_pessoas, len(todos_participantes)))

        # Aplicar a travessura a cada usuário sorteado
        for usuario_sorteado in sorteados:
            aplicar_travessura(usuario_sorteado, chat_id)

        # Enviar mensagem informando quem foi sorteado
        nomes_sorteados = []
        for usuario_id in sorteados:
            user_info = bot.get_chat_member(chat_id, usuario_id).user
            nomes_sorteados.append(user_info.first_name)

        mensagem = f"👻 As seguintes pessoas foram amaldiçoadas pela travessura grupal: {', '.join(nomes_sorteados)}!"
        bot.send_message(chat_id, mensagem)

    except Exception as e:
        print(f"Erro ao realizar travessura grupal: {e}")

# Variáveis de jogo
tabuleiro = np.full((3, 3), ' ')
jogador = 'X'
bot_jogador = 'O'

def criar_tabuleiro_markup():
    """Cria um markup inline para o tabuleiro de jogo da velha"""
    markup = InlineKeyboardMarkup(row_width=3)
    for i in range(3):
        for j in range(3):
            simbolo = tabuleiro[i][j]
            button = InlineKeyboardButton(
                text=simbolo if simbolo != ' ' else ' ',
                callback_data=f"jogada_{i}_{j}"
            )
            markup.add(button)
    return markup

def checar_vitoria(simbolo):
    for i in range(3):
        if all(tabuleiro[i, :] == simbolo) or all(tabuleiro[:, i] == simbolo):
            return True
    if all([tabuleiro[i, i] == simbolo for i in range(3)]) or all([tabuleiro[i, 2 - i] == simbolo for i in range(3)]):
        return True
    return False

def checar_empate():
    return ' ' not in tabuleiro

def minimax(tabuleiro, depth, is_maximizing):
    if checar_vitoria(bot_jogador):
        return 1
    elif checar_vitoria(jogador):
        return -1
    elif checar_empate():
        return 0

    if is_maximizing:
        best_score = -np.inf
        for i in range(3):
            for j in range(3):
                if tabuleiro[i, j] == ' ':
                    tabuleiro[i, j] = bot_jogador
                    score = minimax(tabuleiro, depth + 1, False)
                    tabuleiro[i, j] = ' '
                    best_score = max(score, best_score)
        return best_score
    else:
        best_score = np.inf
        for i in range(3):
            for j in range(3):
                if tabuleiro[i, j] == ' ':
                    tabuleiro[i, j] = jogador
                    score = minimax(tabuleiro, depth + 1, True)
                    tabuleiro[i, j] = ' '
                    best_score = min(score, best_score)
        return best_score

def bot_jogada():
    best_score = -np.inf
    best_move = None
    for i in range(3):
        for j in range(3):
            if tabuleiro[i, j] == ' ':
                tabuleiro[i, j] = bot_jogador
                score = minimax(tabuleiro, 0, False)
                tabuleiro[i, j] = ' '
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    if best_move:
        tabuleiro[best_move] = bot_jogador

def iniciar_jogo_da_velha(chat_id):
    """Inicia um jogo da velha quando o usuário é desafiado pelo fantasma."""
    global tabuleiro
    tabuleiro = np.full((3, 3), ' ')
    bot.send_message(chat_id, "👻 Um fantasma te desafiou para um jogo da velha! Se você ganhar, a travessura será evitada.")
    bot.send_message(chat_id, "Faça sua jogada clicando em uma posição.", reply_markup=criar_tabuleiro_markup())

@bot.callback_query_handler(func=lambda call: call.data.startswith("jogada_"))
def processar_jogada(call):
    _, linha, coluna = call.data.split("_")
    linha, coluna = int(linha), int(coluna)

    if tabuleiro[linha, coluna] != ' ':
        bot.answer_callback_query(call.id, "Posição já ocupada! Escolha outra.")
        return

    # Jogada do usuário
    tabuleiro[linha, coluna] = jogador
    if checar_vitoria(jogador):
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Parabéns! Você venceu o fantasma e evitou a travessura!\n\n" + mostrar_tabuleiro(), reply_markup=None)
        return

    if checar_empate():
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Empate! A travessura foi evitada por pouco!\n\n" + mostrar_tabuleiro(), reply_markup=None)
        return

    # Jogada do bot
    bot_jogada()
    if checar_vitoria(bot_jogador):
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="O fantasma venceu! Prepare-se para a travessura!\n\n" + mostrar_tabuleiro(), reply_markup=None)
        return

    if checar_empate():
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Empate! A travessura foi evitada por pouco!\n\n" + mostrar_tabuleiro(), reply_markup=None)
        return

    # Atualiza o tabuleiro com as novas jogadas
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  reply_markup=criar_tabuleiro_markup())

def mostrar_tabuleiro():
    """Função para retornar o tabuleiro como string"""
    return "\n".join([" | ".join(row) for row in tabuleiro])
# Função para aplicar a travessura ao usuário
def aplicar_travessura(user_id, chat_id):
    try:
        # Aqui você coloca a lógica para aplicar a travessura ao usuário
        bot.send_message(chat_id, f"👻 O usuário {user_id} foi amaldiçoado!")
    
    except Exception as e:
        print(f"Erro ao aplicar travessura: {e}")

processing_lock = threading.Lock()
# Função de callback para processar navegação
@bot.callback_query_handler(func=lambda call: call.data.startswith('vendinha_'))
def processar_callback_cartas_compradas(call):
    # Extraímos a página e ID do callback data
    _, pagina_str, id_usuario_str = call.data.split('_')
    pagina_atual = int(pagina_str)
    id_usuario = int(id_usuario_str)

    # Verificar se o usuário tem cartas salvas no cache para navegação
    if id_usuario in globals.cartas_compradas_dict:
        cartas = globals.cartas_compradas_dict[id_usuario]
        mostrar_cartas_compradas(call.message.chat.id, cartas, id_usuario, pagina_atual, call.message.message_id)
    else:
        bot.send_message(call.message.chat.id, "Erro ao exibir cartas compradas. Tente novamente.")
@bot.callback_query_handler(func=lambda call: call.data.startswith("cesta_"))
def callback_query_cesta(call):
    global processing_lock

    # Log para confirmar que o callback foi chamado
    print(f"Callback acionado com dados: {call.data}")

    if not processing_lock.acquire(blocking=False):
        print("Processando outra requisição, bloqueio ativo.")
        return

    try:
        # Dividir o callback data em partes
        parts = call.data.split('_')
        print(f"Dados divididos em partes: {parts}")

        # Verificar se todas as partes necessárias estão presentes
        if len(parts) < 5:
            print("Erro: Dados insuficientes em parts.")
            bot.answer_callback_query(call.id, "Erro ao processar a navegação.")
            return

        # Extrair informações da mensagem
        tipo = parts[1]
        pagina = int(parts[2])
        categoria = parts[3]
        id_usuario_original = int(parts[4])
        nome_usuario = bot.get_chat(id_usuario_original).first_name
        print(f"Tipo: {tipo}, Página: {pagina}, Categoria: {categoria}, ID Usuário: {id_usuario_original}")

        # Lógica de navegação baseada no tipo de consulta
        if tipo == 's':
            ids_personagens = obter_ids_personagens_inventario_sem_evento(id_usuario_original, categoria)
            total_personagens_subcategoria = obter_total_personagens_subcategoria(categoria)
            total_registros = len(ids_personagens)

            if total_registros > 0:
                total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)
                mostrar_pagina_cesta_s(call.message, categoria, id_usuario_original, pagina, total_paginas, ids_personagens, total_personagens_subcategoria, nome_usuario, call=call)
            else:
                bot.answer_callback_query(call.id, f"Nenhum personagem encontrado na cesta '{categoria}'.")

        elif tipo == 'f':
            ids_personagens_faltantes = obter_ids_personagens_faltantes_sem_evento(id_usuario_original, categoria)
            total_personagens_subcategoria = obter_total_personagens_subcategoria(categoria)
            total_registros = len(ids_personagens_faltantes)

            if total_registros > 0:
                total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)
                mostrar_pagina_cesta_f(call.message, categoria, id_usuario_original, pagina, total_paginas, ids_personagens_faltantes, total_personagens_subcategoria, nome_usuario, call=call)
            else:
                bot.answer_callback_query(call.id, f"Todos os personagens na subcategoria '{categoria}' estão no seu inventário.")

        # Outros tipos de tratamento de navegação
        elif tipo == 'se':
            ids_personagens = obter_ids_personagens_inventario_com_evento(id_usuario_original, categoria)
            total_personagens_com_evento = obter_total_personagens_subcategoria(categoria)
            total_registros = len(ids_personagens)

            if total_registros > 0:
                total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)
                mostrar_pagina_cesta_s(call.message, categoria, id_usuario_original, pagina, total_paginas, ids_personagens, total_personagens_com_evento, nome_usuario, call=call)
            else:
                bot.answer_callback_query(call.id, f"Nenhum personagem encontrado na cesta '{categoria}'.")

        elif tipo == 'fe':
            ids_personagens_faltantes = obter_ids_personagens_faltantes_com_evento(id_usuario_original, categoria)
            total_personagens_subcategoria = obter_total_personagens_subcategoria(categoria)
            total_registros = len(ids_personagens_faltantes)

            if total_registros > 0:
                total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)
                mostrar_pagina_cesta_f(call.message, categoria, id_usuario_original, pagina, total_paginas, ids_personagens_faltantes, total_personagens_subcategoria, nome_usuario, call=call)
            else:
                bot.answer_callback_query(call.id, f"Todos os personagens na subcategoria '{categoria}' estão no seu inventário.")

        elif tipo == 'c':
            ids_personagens = obter_ids_personagens_categoria(id_usuario_original, categoria)
            total_personagens_categoria = obter_total_personagens_categoria(categoria)
            total_registros = len(ids_personagens)

            if total_registros > 0:
                total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)
                mostrar_pagina_cesta_c(call.message, categoria, id_usuario_original, pagina, total_paginas, ids_personagens, total_personagens_categoria, nome_usuario, call=call)
            else:
                bot.answer_callback_query(call.id, f"Nenhum personagem encontrado na categoria '{categoria}'.")

        elif tipo == 'cf':
            ids_personagens_faltantes = obter_ids_personagens_faltantes_categoria(id_usuario_original, categoria)
            total_personagens_categoria = obter_total_personagens_categoria(categoria)
            total_registros = len(ids_personagens_faltantes)

            if total_registros > 0:
                total_paginas = (total_registros // 15) + (1 if total_registros % 15 > 0 else 0)
                mostrar_pagina_cesta_cf(call.message, categoria, id_usuario_original, pagina, total_paginas, ids_personagens_faltantes, total_personagens_categoria, nome_usuario, call=call)
            else:
                bot.answer_callback_query(call.id, f"Você possui todos os personagens na categoria '{categoria}'.")

    except Exception as e:
        print(f"Erro ao processar callback da cesta: {e}")
        bot.answer_callback_query(call.id, "Erro ao processar o callback.")
    finally:
        processing_lock.release()
        
def aplicar_praga(user_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Definir o tempo de duração da praga (exemplo: 10 minutos)
        fim_travessura = datetime.now() + timedelta(minutes=10)

        # Inserir a praga na tabela 'travessuras' para o usuário
        cursor.execute("""
            INSERT INTO travessuras (id_usuario, tipo_travessura, fim_travessura)
            VALUES (%s, 'praga', %s)
            ON DUPLICATE KEY UPDATE fim_travessura = %s
        """, (user_id, fim_travessura, fim_travessura))

        conn.commit()

        # Informar o usuário que ele foi amaldiçoado
        bot.send_message(user_id, "👹 Travessura! Você foi amaldiçoado, use +praga para passar a praga para outra pessoa.")

    except Exception as e:
        print(f"Erro ao aplicar praga: {e}")
    finally:
        fechar_conexao(cursor, conn)

def verificar_praga(user_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Verificar se o usuário tem a praga ativa
        cursor.execute("""
            SELECT fim_travessura FROM travessuras
            WHERE id_usuario = %s AND tipo_travessura = 'praga'
        """, (user_id,))
        resultado = cursor.fetchone()

        if resultado:
            fim_travessura = resultado[0]
            # Se a praga ainda está ativa (tempo atual é menor que o fim da travessura)
            if datetime.now() < fim_travessura:
                return True

        return False  # Não tem praga ativa
    
    except Exception as e:
        print(f"Erro ao verificar praga: {e}")
        return False
    finally:
        fechar_conexao(cursor, conn)

def iniciar_praga(user_id):
    """
    Inicia a praga para um usuário.
    """
    jogo_praga['user_id'] = user_id
    jogo_praga['start_time'] = time.time()
    bot.send_message(user_id, "👻 Você foi amaldiçoado com a praga! Passe a praga para outro usuário rapidamente, ou sofrerá uma travessura!")

def roubar_cenouras_periodicamente(user_id, fim_travessura):
    try:
        conn, cursor = conectar_banco_dados()

        while datetime.now() < fim_travessura:
            # Verificar se a travessura ainda está ativa
            cursor.execute("""
                SELECT fim_travessura FROM travessuras
                WHERE id_usuario = %s AND tipo_travessura = 'sombra_rouba_cenouras'
            """, (user_id,))
            resultado = cursor.fetchone()

            if resultado and datetime.now() < resultado[0]:
                # Roubar uma cenoura
                cursor.execute("UPDATE usuarios SET cenouras = cenouras - 1 WHERE id_usuario = %s", (user_id,))
                conn.commit()

                # Notificar o usuário que uma cenoura foi roubada
                bot.send_message(user_id, "👻 Uma sombra roubou uma de suas cenouras!")
                
                # Esperar 10 segundos antes de roubar novamente
                time.sleep(10)
            else:
                break

    except Exception as e:
        print(f"Erro ao roubar cenouras: {e}")
    finally:
        fechar_conexao(cursor, conn)

def aplicar_travessura(id_usuario, tipo_travessura):
    """
    Aplica a travessura ao usuário com base no tipo de travessura.
    """
    try:
        if tipo_travessura == 'alucinacao':
            # Exemplo de aplicação da travessura de alucinação (embaralhar texto)
            print(f"Aplicando travessura de alucinação para o usuário {id_usuario}")
            if texto:
                return embaralhar_mensagem(texto)  # Função para embaralhar texto
            else:
                return "Mensagem embaralhada!"

        elif tipo_travessura == 'bloqueio_pesca':
            # Exemplo de bloqueio para impedir o comando de pesca
            print(f"Aplicando bloqueio de pesca para o usuário {id_usuario}")
            bot.send_message(id_usuario, "Você está bloqueado de pescar por algum tempo!")

        elif tipo_travessura == 'mudar_nome':
            # Exemplo de mudança de nome
            print(f"Aplicando mudança de nome para o usuário {id_usuario}")
            novo_nome = "Zé Praga"  # Nome de exemplo
            alterar_nome_usuario(id_usuario, novo_nome)
            bot.send_message(id_usuario, f"Seu nome foi alterado para {novo_nome}!")

        # Adicione outras travessuras aqui conforme necessário

    except Exception as e:
        print(f"Erro ao aplicar a travessura: {e}")

def verificar_travessuras(id_usuario):
    """
    Verifica todas as travessuras ativas para o usuário, incluindo a travessura de embaralhamento.
    Retorna uma lista com os tipos de travessuras ativas e um indicador se a travessura de embaralhamento está ativa.
    """
    conn, cursor = conectar_banco_dados()
    try:
        # Verificar todas as travessuras ativas
        cursor.execute("""
            SELECT tipo_travessura, fim_travessura
            FROM travessuras
            WHERE id_usuario = %s AND fim_travessura > NOW()
        """, (id_usuario,))
        travessuras_ativas = cursor.fetchall()

        # Verificar se a travessura de embaralhamento está ativa
        embaralhamento_ativo = False
        for travessura, fim_travessura in travessuras_ativas:
            if travessura == 'embaralhamento' and datetime.now() < fim_travessura:
                embaralhamento_ativo = True
        
        # Retornar todas as travessuras ativas e o status do embaralhamento
        return {
            "travessuras": [row[0] for row in travessuras_ativas],
            "embaralhamento_ativo": embaralhamento_ativo
        }

    except Exception as e:
        print(f"Erro ao verificar travessuras: {e}")
        return {"travessuras": [], "embaralhamento_ativo": False}
    
    finally:
        fechar_conexao(cursor, conn)

# Dicionário para rastrear as threads e o status do roubo para cada usuário
roubo_ativo = {}

# Função para iniciar a sombra roubando cenouras periodicamente
def iniciar_sombra_roubo_cenouras(user_id, duracao_minutos=10):
    try:
        conn, cursor = conectar_banco_dados()

        # Verificar se o usuário já tem a travessura ativa
        cursor.execute("""
            SELECT fim_travessura FROM travessuras
            WHERE id_usuario = %s AND tipo_travessura = 'sombra_rouba_cenouras'
        """, (user_id,))
        resultado = cursor.fetchone()

        if resultado:
            fim_travessura = resultado[0]
            if datetime.now() < fim_travessura:
                bot.send_message(user_id, "👻 A sombra já está roubando suas cenouras! Use /exorcizar para se livrar dela!")
                return

        fim_roubo = datetime.now() + timedelta(minutes=duracao_minutos)

        # Registrar a travessura na tabela
        cursor.execute("""
            INSERT INTO travessuras (id_usuario, tipo_travessura, fim_travessura)
            VALUES (%s, 'sombra_rouba_cenouras', %s)
            ON DUPLICATE KEY UPDATE fim_travessura = %s
        """, (user_id, fim_roubo, fim_roubo))
        conn.commit()

        # Sinalizar que o roubo está ativo para o usuário
        roubo_ativo[user_id] = True

        # Função interna para o roubo de cenouras
        def roubar_cenouras_periodicamente():
            while datetime.now() < fim_roubo and roubo_ativo.get(user_id, False):
                sucesso = diminuir_cenouras(user_id, 1)
                if sucesso:
                    bot.send_message(user_id, "👻 A sombra roubou 1 cenoura! Use /exorcizar para deter a sombra!")
                else:
                    break  # Se não há mais cenouras para roubar
                time.sleep(10)

            # Remover a travessura após o tempo acabar
            if roubo_ativo.get(user_id, False):  # Se o exorcismo não foi usado
                cursor.execute("DELETE FROM travessuras WHERE id_usuario = %s AND tipo_travessura = 'sombra_rouba_cenouras'", (user_id,))
                conn.commit()
                bot.send_message(user_id, "🕯️ A sombra desapareceu, suas cenouras estão seguras por enquanto.")

        # Iniciar o roubo em uma thread separada
        threading.Thread(target=roubar_cenouras_periodicamente).start()

    except Exception as e:
        print(f"Erro ao iniciar sombra para roubar cenouras: {e}")
    finally:
        fechar_conexao(cursor, conn)


@bot.message_handler(commands=['exorcizar'])
def exorcizar_sombra(message):
    user_id = message.from_user.id
    try:
        conn, cursor = conectar_banco_dados()

        # Verificar se o usuário está com a travessura ativa
        cursor.execute("""
            SELECT fim_travessura FROM travessuras
            WHERE id_usuario = %s AND tipo_travessura = 'sombra_rouba_cenouras'
        """, (user_id,))
        resultado = cursor.fetchone()

        if resultado:
            chance_sucesso = random.randint(1, 100)

            if chance_sucesso <= 30:  # Sucesso em 30% das tentativas
                # Exorcismo bem-sucedido: parar o roubo e remover a travessura
                roubo_ativo[user_id] = False  # Parar o roubo
                cursor.execute("DELETE FROM travessuras WHERE id_usuario = %s AND tipo_travessura = 'sombra_rouba_cenouras'", (user_id,))
                conn.commit()
                bot.send_message(message.chat.id, "🕯️ Você exorcizou a sombra! Suas cenouras estão seguras.")
            else:
                bot.send_message(message.chat.id, "👻 O exorcismo falhou! A sombra continua a roubar suas cenouras.")
        else:
            bot.send_message(message.chat.id, "👻 Não há nenhuma sombra para exorcizar.")

    except Exception as e:
        bot.send_message(message.chat.id, f"Erro ao exorcizar a sombra: {e}")
    finally:
        fechar_conexao(cursor, conn)


def adicionar_vip_temporario(user_id, grupo_sugestao,chat_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Verificar se o usuário já é VIP
        cursor.execute("SELECT COUNT(*) FROM vips WHERE id_usuario = %s", (user_id,))
        ja_vip = cursor.fetchone()[0] > 0

        if ja_vip:
            # Se já for VIP, realiza outra gostosura
            realizar_halloween_gostosura(user_id, chat_id)
        else:
            # Se não for VIP, dar VIP por um período aleatório de 1 a 7 dias
            dias_vip = random.randint(1, 3)
            data_fim_vip = datetime.now() + timedelta(days=dias_vip)

            # Inserir na tabela de VIPs
            cursor.execute("""
                INSERT INTO vips (id_usuario, nome, data_pagamento, renovou, pedidos_restantes, mes_atual, Dia_renovar)
                VALUES (%s, (SELECT nome FROM usuarios WHERE id_usuario = %s), NOW(), 1, 4, MONTH(NOW()), DAY(NOW() + INTERVAL %s DAY))
            """, (user_id, user_id, dias_vip))
            conn.commit()

            # Enviar mensagem para o grupo de sugestões
            bot.send_message(grupo_sugestao, f"🎉 O usuário {user_id} ganhou VIP por {dias_vip} dias!")

            # Informar o usuário que ganhou VIP
            bot.send_message(chat_id, f"🎁 Parabéns! Você ganhou VIP por {dias_vip} dias. Aproveite!")

    except Exception as e:
        print(f"Erro ao adicionar VIP temporário: {e}")
    finally:
        fechar_conexao(cursor, conn)

# Função para aumentar as cenouras de um usuário
def aumentar_cenouras(user_id, quantidade):
    try:
        conn = conectar_banco_dados()
        cursor = conn.cursor()
        # Atualiza o campo `cenouras` na tabela `usuarios` adicionando a quantidade
        cursor.execute("UPDATE usuarios SET cenouras = cenouras + %s WHERE id_usuario = %s", (quantidade, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"DEBUG: Cenouras aumentadas em {quantidade} para o usuário {user_id}.")
    except Exception as e:
        print(f"Erro ao aumentar cenouras para o usuário {user_id}: {e}")

def alterar_usuario(user_id, coluna, valor_novo,chat_id):
    """
    Função genérica para alterar um campo específico na tabela `usuarios`.
    """
    try:
        conn, cursor = conectar_banco_dados()

        # Atualizar a coluna especificada com o novo valor
        query = f"UPDATE usuarios SET {coluna} = %s WHERE id_usuario = %s"
        cursor.execute(query, (valor_novo, user_id))
        conn.commit()

        print(f"DEBUG: {coluna} do usuário {user_id} alterada para {valor_novo}")
    except Exception as e:
        print(f"Erro ao alterar {coluna} para o usuário {user_id}: {e}")
    finally:
        fechar_conexao(cursor, conn)

def adicionar_protecao_temporaria(user_id,chat_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Definir o período de proteção entre 3 e 12 horas
        horas_protecao = random.randint(1, 6)
        fim_protecao = datetime.now() + timedelta(hours=horas_protecao)

        # Atualizar ou inserir a proteção na tabela de usuários
        cursor.execute("""
            INSERT INTO protecoes (id_usuario, fim_protecao)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE fim_protecao = %s
        """, (user_id, fim_protecao, fim_protecao))
        conn.commit()

        # Informar o usuário sobre a proteção
        bot.send_message(chat_id, f"🛡️ Você ganhou uma proteção mágica por {horas_protecao} horas! Durante esse tempo, você está imune a travessuras.")
    
    except Exception as e:
        print(f"Erro ao adicionar proteção temporária: {e}")
    finally:
        fechar_conexao(cursor, conn)

def realizar_combo_gostosura(user_id, chat_id):
    try:
        conn, cursor = conectar_banco_dados()
        mensagem_combo = "Uma senhora te deu um combo como gostosura:\n\n"

        # Parte 1: Ganhar até 100 cenouras
        cenouras_ganhas = random.randint(50, 100)
        aumentar_cenouras(user_id, cenouras_ganhas)
        mensagem_combo += f"🍬 {cenouras_ganhas} cenouras no Combo!\n\n"

        cartas_ganhas = adicionar_carta_faltante_halloween(user_id, chat_id)
        if cartas_ganhas:
            mensagem_combo += f"🎃 1 carta faltante do evento Halloween!\n\n"
        else:
            mensagem_combo += f"🎃 Parabéns! Mas você já tem todas as cartas do evento Halloween.\n\n"

        # Parte 3: Escolher um efeito bônus
        efeitos_bonus = [
            "dobro de cenouras ao cenourar",
            "peixes em dobro na pesca",
            "proteção contra travessuras",
            "VIP de 1 dia"
        ]
        efeito_escolhido = random.choice(efeitos_bonus)

        if efeito_escolhido == "dobro de cenouras ao cenourar":
            ativar_dobro_cenouras(user_id)
            mensagem_combo += "🥕 Bônus ativado: Você receberá o dobro de cenouras quando cenourar!\n"
        
        elif efeito_escolhido == "peixes em dobro na pesca":
            ativar_peixes_em_dobro(user_id)
            mensagem_combo += "🐟 Bônus ativado: Você receberá peixes em dobro ao pescar!\n"

        elif efeito_escolhido == "proteção contra travessuras":
            adicionar_protecao_temporaria(user_id,chat_id)
            mensagem_combo += "🛡️ Bônus ativado: Você está protegido contra travessuras!\n"

        elif efeito_escolhido == "VIP de 1 dia":
            adicionar_vip_temporario(user_id, chat_id, GRUPO_SUGESTAO, dias=1)
            mensagem_combo += "⚡ Bônus ativado: Você recebeu VIP por 1 dia!\n"

        # Enviar a mensagem final com todas as informações
        bot.send_message(chat_id, mensagem_combo)

    except Exception as e:
        print(f"Erro ao realizar combo de gostosuras: {e}")
    finally:
        fechar_conexao(cursor, conn)
# Dicionário para armazenar quem está com a praga e o tempo restante
praga_ativa = {}
@bot.message_handler(commands=['setgif'])
def handle_setgif(message):
    enviar_gif(message)

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

        bot.send_message(message.chat.id, "Eba! Você pode escolher um gif!\nEnvie o link do gif gerado pelo @LinksdamabiBot:")

        # Armazena o estado global para o próximo handler
        globals.links_gif[id_usuario] = id_personagem

        # Registra o próximo step para capturar o link do GIF
        bot.register_next_step_handler(message, receber_link_gif, id_personagem)

        fechar_conexao(cursor, conn)

    except IndexError:
        bot.send_message(message.chat.id, "Por favor, forneça o ID do personagem.")
    except Exception as e:
        print(f"Erro ao processar o comando /setgif: {e}")
        fechar_conexao(cursor, conn)
def receber_link_gif(message, id_personagem):
    id_usuario = message.from_user.id

    if id_usuario:
        link_gif = message.text

        if not re.match(r'^https?://\S+$', link_gif):
            bot.send_message(message.chat.id, "Por favor, envie <b>apenas</b> o <b>link</b> do GIF.", parse_mode="HTML")
            return

        if id_usuario in globals.links_gif:
            id_personagem = globals.links_gif[id_usuario]

            if id_personagem:
                numero_personagem = id_personagem.split('_')[0]
                conn, cursor = conectar_banco_dados()

                sql_usuario = "SELECT nome_usuario, nome FROM usuarios WHERE id_usuario = %s"
                cursor.execute(sql_usuario, (id_usuario,))
                resultado_usuario = cursor.fetchone()

                sql_personagem = "SELECT nome, subcategoria FROM personagens WHERE id_personagem = %s"
                cursor.execute(sql_personagem, (numero_personagem,))
                resultado_personagem = cursor.fetchone()

                if resultado_usuario and resultado_personagem:
                    nome_usuario = resultado_usuario[0]
                    nome_personagem = resultado_personagem[0]
                    subcategoria_personagem = resultado_personagem[1]

                    sql_temp_insert = """
                        INSERT INTO temp_data (id_usuario, id_personagem, chave, valor)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE valor = VALUES(valor), chave = VALUES(chave)
                    """
                    chave = f"{id_usuario}_{numero_personagem}"
                    cursor.execute(sql_temp_insert, (id_usuario, numero_personagem, chave, link_gif))
                    conn.commit()
                    fechar_conexao(cursor, conn)

                    keyboard = telebot.types.InlineKeyboardMarkup()
                    btn_aprovar = telebot.types.InlineKeyboardButton(text="✔️ Aprovar", callback_data=f"aprovar_{id_usuario}_{numero_personagem}_{message.message_id}")
                    btn_reprovar = telebot.types.InlineKeyboardButton(text="❌ Reprovar", callback_data=f"reprovar_{id_usuario}_{numero_personagem}_{message.message_id}")

                    keyboard.row(btn_aprovar, btn_reprovar)
                    bot.forward_message(chat_id=-1002144134360, from_chat_id=message.chat.id, message_id=message.message_id)
                    chat_id = -1002144134360
                    mensagem = f"Pedido de aprovação de GIF:\n\n"
                    mensagem += f"ID Personagem: {numero_personagem}\n"
                    mensagem += f"{nome_personagem} de {subcategoria_personagem}\n\n"
                    mensagem += f"Usuário: @{message.from_user.username}\n"
                    mensagem += f"Nome: {nome_usuario}\n"

                    sent_message = bot.send_message(chat_id, mensagem, reply_markup=keyboard)
                    bot.send_message(message.chat.id, "Link do GIF registrado com sucesso. Aguardando aprovação.")
                    return sent_message.message_id
                else:
                    fechar_conexao(cursor, conn)
                    bot.send_message(message.chat.id, "Erro ao obter informações do usuário ou do personagem.")
            else:
                bot.send_message(message.chat.id, "Erro ao processar o link do GIF. Por favor, use o comando /setgif novamente.")
        else:
            bot.send_message(message.chat.id, "Erro ao processar o link do GIF. ID de usuário inválido.")
    else:
        bot.send_message(message.chat.id, "Erro ao processar o link do GIF. ID de usuário inválido.")
def iniciar_pega_pega(user_id, chat_id):
    try:
        # Definir a pessoa inicial com a praga
        praga_ativa[chat_id] = {
            "usuario_atual": user_id,
            "tempo_inicial": time.time(),
            "tempo_final": time.time() + 600  # 10 minutos de duração
        }

        # Anunciar o início do pega-pega com praga
        bot.send_message(chat_id, f"👻 {user_id} está com a praga! Use +praga para passar a praga para outra pessoa!")

        # Iniciar uma thread para monitorar o tempo e aplicar a travessura
        threading.Thread(target=monitorar_praga, args=(chat_id,)).start()

    except Exception as e:
        print(f"Erro ao iniciar o Pega-Pega com praga: {e}")
        bot.send_message(chat_id, "Ocorreu um erro ao iniciar o Pega-Pega com praga.")

def monitorar_praga(chat_id):
    try:
        while True:
            # Verificar se o tempo da praga acabou
            if praga_ativa[chat_id]["tempo_final"] <= time.time():
                # O tempo acabou, a pessoa que está com a praga sofre a travessura
                usuario_com_praga = praga_ativa[chat_id]["usuario_atual"]
                bot.send_message(chat_id, f"⏰ O tempo acabou! {usuario_com_praga} ainda está com a praga e vai sofrer uma travessura!")
                
                # Aplique a travessura aqui, como uma penalidade
                realizar_travessura_final(usuario_com_praga, chat_id)
                
                # Remover a praga do chat
                del praga_ativa[chat_id]
                break

            time.sleep(10)  # Verificar a cada 10 segundos

    except Exception as e:
        print(f"Erro ao monitorar a praga: {e}")

def verificar_praga(user_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Verificar se o usuário tem a praga ativa
        cursor.execute("SELECT fim_praga FROM pragas WHERE id_usuario = %s", (user_id,))
        resultado = cursor.fetchone()

        if resultado:
            fim_praga = resultado[0]
            # Verificar se a praga ainda está ativa
            if datetime.now() < fim_praga:
                return True

        return False  # Não tem praga ativa ou já expirou

    except Exception as e:
        print(f"Erro ao verificar praga: {e}")
        return False

    finally:
        fechar_conexao(cursor, conn)

# Função para dar a praga a um usuário
def dar_praga(user_id, duracao_minutos=10):
    try:
        conn, cursor = conectar_banco_dados()

        fim_praga = datetime.now() + timedelta(minutes=duracao_minutos)

        # Inserir ou atualizar o status da praga no banco de dados
        cursor.execute("""
            INSERT INTO pragas (id_usuario, fim_praga)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE fim_praga = VALUES(fim_praga)
        """, (user_id, fim_praga))
        conn.commit()

        bot.send_message(user_id, f"👻 Você foi amaldiçoado com a praga! Passe-a para alguém nos próximos {duracao_minutos} minutos.")
    
    except Exception as e:
        print(f"Erro ao dar praga: {e}")
    
    finally:
        fechar_conexao(cursor, conn)

# Função para passar a praga para outro usuário
def passar_praga(user_id, target_user_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Verificar se o usuário realmente tem a praga
        if not verificar_praga(user_id):
            bot.send_message(user_id, "👻 Você não tem uma praga para passar.")
            return

        # Dar a praga ao usuário alvo
        dar_praga(target_user_id)

        # Remover a praga do usuário atual
        cursor.execute("DELETE FROM pragas WHERE id_usuario = %s", (user_id,))
        conn.commit()

        bot.send_message(user_id, f"🎃 Você passou a praga para {bot.get_chat_member(user_id, target_user_id).user.first_name}!")
        bot.send_message(target_user_id, "👻 Você recebeu uma praga! Passe-a para alguém nos próximos 10 minutos.")

    except Exception as e:
        print(f"Erro ao passar praga: {e}")

    finally:
        fechar_conexao(cursor, conn)

def realizar_travessura_final(usuario_com_praga, chat_id):
    # Implemente aqui a travessura final que será aplicada ao usuário com a praga
    # Por exemplo, roubar cenouras ou remover cartas
    bot.send_message(chat_id, f"👻 {usuario_com_praga} sofreu uma travessura! Uma carta foi removida do seu inventário.")
   
def ativar_dobro_cenouras(user_id):
    try:
        conn, cursor = conectar_banco_dados()
        fim_bonus = datetime.now() + timedelta(hours=24)

        # Armazena o bônus de cenouras dobradas no banco de dados
        cursor.execute("""
            INSERT INTO bonus_cenouras (id_usuario, fim_bonus)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE fim_bonus = %s
        """, (user_id, fim_bonus, fim_bonus))
        conn.commit()

    except Exception as e:
        print(f"Erro ao ativar bônus de cenouras: {e}")
    finally:
        fechar_conexao(cursor, conn)

def ativar_peixes_em_dobro(user_id):
    try:
        conn, cursor = conectar_banco_dados()
        fim_bonus = datetime.now() + timedelta(hours=24)

        # Armazena o bônus de peixes em dobro no banco de dados
        cursor.execute("""
            INSERT INTO bonus_peixes (id_usuario, fim_bonus)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE fim_bonus = %s
        """, (user_id, fim_bonus, fim_bonus))
        conn.commit()

    except Exception as e:
        print(f"Erro ao ativar bônus de peixes em dobro: {e}")
    finally:
        fechar_conexao(cursor, conn)

def iniciar_compartilhamento(user_id,chat_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Verificar se o usuário já tem um compartilhamento ativo
        cursor.execute("SELECT ativo FROM compartilhamentos WHERE id_usuario = %s", (user_id,))
        resultado = cursor.fetchone()

        if resultado and resultado[0]:  # Se já tiver um compartilhamento ativo
            bot.send_message(user_id, "👻 Você já tem um compartilhamento ativo! Compartilhe antes de ganhar mais.")
            return

        # Gerar uma quantidade de cenouras entre 50 e 100
        cenouras_ganhas = random.randint(50, 100)
        
        # Registrar o compartilhamento no banco de dados
        cursor.execute("""
            INSERT INTO compartilhamentos (id_usuario, quantidade_cenouras)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE quantidade_cenouras = %s, ativo = TRUE, data_inicio = NOW()
        """, (user_id, cenouras_ganhas, cenouras_ganhas))
        conn.commit()

        # Enviar a mensagem informando sobre o compartilhamento
        bot.send_message(chat_id, f"🎃 Você ganhou {cenouras_ganhas} cenouras! Agora escolha alguém para compartilhar usando o comando +compartilhar <id do jogador>.")
    
    except Exception as e:
        print(f"Erro ao iniciar o compartilhamento: {e}")
    
    finally:
        fechar_conexao(cursor, conn)

@bot.message_handler(func=lambda message: message.text and message.text.startswith('+compartilhar'))
def handle_compartilhar(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Verificar se a mensagem é uma resposta
    if not message.reply_to_message:
        bot.send_message(chat_id, "👻 Você deve responder a uma mensagem da pessoa com quem deseja compartilhar as cenouras.")
        return
    
    # Obter o ID da pessoa alvo (a pessoa que recebeu a mensagem)
    target_user_id = message.reply_to_message.from_user.id

    # Não pode compartilhar com você mesmo
    if target_user_id == user_id:
        bot.send_message(chat_id, "👻 Você não pode compartilhar cenouras com você mesmo.")
        return

    # Chamar a função para compartilhar as cenouras
    compartilhar_cenouras(user_id, target_user_id, chat_id, message.reply_to_message.from_user.first_name)

def compartilhar_cenouras(user_id, target_user_id, chat_id, user_name, target_user_name):
    try:
        conn, cursor = conectar_banco_dados()

        # Verificar se o usuário tem um compartilhamento ativo
        cursor.execute("SELECT quantidade_cenouras FROM compartilhamentos WHERE id_usuario = %s AND ativo = TRUE", (user_id,))
        resultado = cursor.fetchone()

        if not resultado:
            bot.send_message(chat_id, "👻 Você não tem nenhum compartilhamento ativo. Ative um compartilhamento primeiro com o comando +halloween.")
            return

        quantidade_cenouras = resultado[0]

        # Transferir cenouras para o alvo do compartilhamento
        cursor.execute("UPDATE usuarios SET cenouras = cenouras + %s WHERE id_usuario = %s", (quantidade_cenouras, target_user_id))
        cursor.execute("UPDATE usuarios SET cenouras = cenouras - %s WHERE id_usuario = %s", (quantidade_cenouras, user_id))
        
        # Desativar o compartilhamento
        cursor.execute("UPDATE compartilhamentos SET ativo = FALSE WHERE id_usuario = %s", (user_id,))
        conn.commit()

        # Informar ambos os usuários
        bot.send_message(user_id, f"🎃 Você compartilhou {quantidade_cenouras} cenouras com {target_user_name}! Cenouras removidas.")
        bot.send_message(target_user_id, f"🎃 {user_name} compartilhou {quantidade_cenouras} cenouras com você! Aproveite!")
    
    except Exception as e:
        print(f"Erro ao compartilhar cenouras: {e}")
    
    finally:
        fechar_conexao(cursor, conn)



@bot.callback_query_handler(func=lambda call: call.data.startswith("descartar_caixa") or call.data == "recusar_caixa")
def callback_descartar_ou_recusar_caixa(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    if call.data == "recusar_caixa":
        # O usuário decidiu não descartar nenhuma caixa e recusar a nova
        bot.send_message(chat_id, "Você decidiu recusar a nova Caixa Misteriosa.")
        return

    # Caso contrário, o usuário decidiu descartar uma caixa
    numero_caixa = int(call.data.split("_")[-1])

    try:
        conn, cursor = conectar_banco_dados()

        # Remover a caixa escolhida do inventário
        cursor.execute("DELETE FROM caixas_misteriosas WHERE id_usuario = %s AND numero_caixa = %s", (user_id, numero_caixa))
        conn.commit()

        bot.send_message(chat_id, f"🎁 Você jogou fora a Caixa Misteriosa número {numero_caixa}.")

        # Atribuir uma nova caixa misteriosa
        novo_numero_caixa = random.randint(1, 10000)
        cursor.execute("INSERT INTO caixas_misteriosas (id_usuario, numero_caixa) VALUES (%s, %s)", (user_id, novo_numero_caixa))
        conn.commit()

        bot.send_message(chat_id, f"🎁 Você ganhou uma nova Caixa Misteriosa! Número da nova caixa: {novo_numero_caixa}.")

    except Exception as e:
        print(f"Erro ao descartar a Caixa Misteriosa: {e}")

    finally:
        fechar_conexao(cursor, conn)

def encontrar_abobora(user_id,chat_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Verificar quais abóboras o usuário já ganhou
        cursor.execute("SELECT id_abobora FROM aboboras_ganhas WHERE id_usuario = %s", (user_id,))
        aboboras_ganhas = cursor.fetchall()

        aboboras_ganhas_ids = [row[0] for row in aboboras_ganhas]

        # Filtrar as abóboras que ainda não foram ganhas
        aboboras_disponiveis = {id_abobora: aboboras[id_abobora] for id_abobora in aboboras if id_abobora not in aboboras_ganhas_ids}

        if not aboboras_disponiveis:
            bot.send_message(chat_id, "🎃 Você já encontrou todas as abóboras disponíveis! Mas vai levar como recompensa 100 cenouras.")
            return

        # Escolher uma abóbora aleatória entre as disponíveis
        id_abobora = random.choice(list(aboboras_disponiveis.keys()))
        abobora = aboboras_disponiveis[id_abobora]

        # Registrar que o jogador ganhou essa abóbora
        cursor.execute("INSERT INTO aboboras_ganhas (id_usuario, id_abobora) VALUES (%s, %s)", (user_id, id_abobora))
        conn.commit()

        # Entregar o prêmio
        if "cenouras" in abobora["premio"]:
            quantidade = int(abobora["premio"].split()[0])
            aumentar_cenouras(user_id, quantidade)
            bot.send_message(chat_id, f"🎃 {abobora['nome']} encontrada! Parabéns, você recebeu {quantidade} cenouras!")
        elif abobora["premio"] == "Carta Faltante":
            adicionar_carta_faltante_halloween(user_id, chat_id)
            bot.send_message(chat_id, f"🎃 {abobora['nome']} encontrada! Parabéns, você recebeu uma carta faltante do evento!")
        
        # Adicione outras possíveis premiações aqui

    except Exception as e:
        print(f"Erro ao encontrar abóbora: {e}")
    
    finally:
        fechar_conexao(cursor, conn)

def ganhar_caixa_misteriosa(user_id, chat_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Verificar quantas caixas o usuário já tem
        cursor.execute("SELECT numero_caixa FROM caixas_misteriosas WHERE id_usuario = %s", (user_id,))
        caixas = cursor.fetchall()

        if len(caixas) >= 3:
            # O usuário tem 3 caixas, perguntar se quer descartar uma
            markup = InlineKeyboardMarkup()
            for caixa in caixas:
                numero_caixa = caixa[0]
                markup.add(InlineKeyboardButton(text=f"Jogar fora Caixa {numero_caixa}", callback_data=f"descartar_caixa_{numero_caixa}"))
            markup.add(InlineKeyboardButton(text="Recusar nova caixa", callback_data="recusar_caixa"))
            bot.send_message(chat_id, "🎁 Você já tem 3 Caixas Misteriosas. Deseja jogar fora uma delas para ganhar uma nova?", reply_markup=markup)
            return

        # Se o usuário tiver menos de 3 caixas, atribuir uma nova
        numero_caixa = random.randint(1, 10000)

        # Registrar a nova caixa no estoque do jogador
        cursor.execute("INSERT INTO caixas_misteriosas (id_usuario, numero_caixa) VALUES (%s, %s)", (user_id, numero_caixa))
        conn.commit()

        bot.send_message(chat_id, f"🎁 Você ganhou uma Caixa Misteriosa! Ela será revelada no último dia do evento. Número da caixa: {numero_caixa}")

    except Exception as e:
        print(f"Erro ao ganhar Caixa Misteriosa: {e}")
    
    finally:
        fechar_conexao(cursor, conn)

def descartar_caixa_misteriosa(user_id, numero_caixa):
    try:
        conn, cursor = conectar_banco_dados()

        # Remover a caixa específica do estoque do jogador
        cursor.execute("DELETE FROM caixas_misteriosas WHERE id_usuario = %s AND numero_caixa = %s", (user_id, numero_caixa))
        conn.commit()

        bot.send_message(user_id, f"❌ Você jogou fora a Caixa Misteriosa número {numero_caixa}.")

    except Exception as e:
        print(f"Erro ao descartar Caixa Misteriosa: {e}")
    
    finally:
        fechar_conexao(cursor, conn)
def revelar_caixas_misteriosas(user_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Obter todas as caixas do jogador
        cursor.execute("SELECT numero_caixa FROM caixas_misteriosas WHERE id_usuario = %s", (user_id,))
        caixas = cursor.fetchall()

        if not caixas:
            bot.send_message(user_id, "🎁 Você não tem nenhuma Caixa Misteriosa para revelar.")
            return

        for caixa in caixas:
            numero_caixa = caixa[0]

            # Determinar o prêmio da caixa misteriosa (exemplo: 50 a 100 cenouras, uma carta especial etc.)
            premio = random.choice([
                f"{random.randint(50, 100)} cenouras",
                "Uma carta especial do evento",
                "VIP de 1 a 7 dias"
            ])

            # Enviar a mensagem de revelação para o jogador
            bot.send_message(user_id, f"🎁 Caixa Misteriosa número {numero_caixa} revelada! Você ganhou: {premio}")

            # Se o prêmio for cenouras, adicionar ao saldo
            if "cenouras" in premio:
                quantidade_cenouras = int(premio.split()[0])
                aumentar_cenouras(user_id, quantidade_cenouras)

            # Implementar a lógica para adicionar outros prêmios (VIP, carta especial, etc.)

        # Limpar as caixas do jogador após a revelação
        cursor.execute("DELETE FROM caixas_misteriosas WHERE id_usuario = %s", (user_id,))
        conn.commit()

    except Exception as e:
        print(f"Erro ao revelar Caixas Misteriosas: {e}")
    
    finally:
        fechar_conexao(cursor, conn)
def opcoes_descartar_caixa(user_id, caixas):
    markup = InlineKeyboardMarkup()
    for caixa in caixas:
        numero_caixa = caixa[0]
        botao = InlineKeyboardButton(text=f"Caixa {numero_caixa}", callback_data=f"descartar_caixa_{numero_caixa}")
        markup.add(botao)

    bot.send_message(user_id, "Escolha uma Caixa Misteriosa para jogar fora:", reply_markup=markup)
def mostrar_portas_escolha(user_id):
    # Definir três prêmios aleatórios
    premios = [
        f"{random.randint(50, 100)} cenouras",
        "VIP por 1 dia",
        "Uma carta faltante do evento Halloween"
    ]
    
    # Embaralhar os prêmios para cada jogador ter uma experiência diferente
    random.shuffle(premios)

    # Salvar os prêmios para o usuário (exemplo de cache ou banco de dados)
    salvar_premios_escolha(user_id, premios)

    # Criar os botões das portas
    markup = InlineKeyboardMarkup()
    porta_1 = InlineKeyboardButton("🚪", callback_data=f"escolha_porta_1_{user_id}")
    porta_2 = InlineKeyboardButton("🚪", callback_data=f"escolha_porta_2_{user_id}")
    porta_3 = InlineKeyboardButton("🚪 ", callback_data=f"escolha_porta_3_{user_id}")
    
    markup.add(porta_1, porta_2, porta_3)
    
    # Enviar a mensagem com as três portas
    bot.send_message(user_id, "Escolha uma porta! Todas as portas escondem algo bom:", reply_markup=markup)
def salvar_premios_escolha(user_id, premios):
    # Aqui você pode salvar os prêmios no banco de dados ou em cache
    # Exemplo básico:
    conn, cursor = conectar_banco_dados()
    cursor.execute("REPLACE INTO escolhas (id_usuario, premio1, premio2, premio3) VALUES (%s, %s, %s, %s)",
                   (user_id, premios[0], premios[1], premios[2]))
    conn.commit()
    fechar_conexao(cursor, conn)

def recuperar_premios_escolha(user_id):
    # Recupera os prêmios do banco de dados ou cache
    conn, cursor = conectar_banco_dados()
    cursor.execute("SELECT premio1, premio2, premio3 FROM escolhas WHERE id_usuario = %s", (user_id,))
    premios = cursor.fetchone()
    fechar_conexao(cursor, conn)
    return premios if premios else ["", "", ""]
def processar_premio(user_id, premio):
    if "cenouras" in premio:
        # Extrair a quantidade de cenouras
        quantidade_cenouras = int(premio.split()[0])
        aumentar_cenouras(user_id, quantidade_cenouras)

    elif "VIP" in premio:
        # Conceder VIP de 1 dia
        conceder_vip(user_id, 1)

    elif "carta faltante" in premio:
        # Dar uma carta faltante do evento
        dar_carta_faltante(user_id, "Halloween")

def adicionar_inverter_travessura(user_id,chat_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Inserir ou atualizar a habilidade de inverter travessura
        cursor.execute("""
            INSERT INTO inverter_travessuras (id_usuario, pode_inverter)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE pode_inverter = VALUES(pode_inverter)
        """, (user_id, True))
        conn.commit()

        bot.send_message(chat_id, "🪄 Você ganhou a habilidade de inverter uma travessura! Quando for alvo, poderá reverter o efeito.")
    except Exception as e:
        print(f"Erro ao adicionar a chance de inverter a travessura: {e}")
    finally:
        fechar_conexao(cursor, conn)


def verificar_inverter_travessura(user_id, atacante_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Verificar se o usuário tem a habilidade de inverter travessura
        cursor.execute("SELECT pode_inverter FROM inverter_travessuras WHERE id_usuario = %s", (user_id,))
        resultado = cursor.fetchone()

        if resultado and resultado[0]:  # Se o usuário tem a habilidade
            # Remove a habilidade após usá-la
            cursor.execute("UPDATE inverter_travessuras SET pode_inverter = %s WHERE id_usuario = %s", (False, user_id))
            conn.commit()

            # Notifica o atacante e o alvo
            bot.send_message(atacante_id, "👻 A travessura foi invertida e agora o efeito recai sobre você!")
            bot.send_message(user_id, "🎃 Você usou sua habilidade e inverteu a travessura!")
        else:
            bot.send_message(user_id, "Você não possui a habilidade de inverter travessuras no momento.")
    except Exception as e:
        print(f"Erro ao verificar e inverter a travessura: {e}")
    finally:
        fechar_conexao(cursor, conn)

def adicionar_super_boost_cenouras(user_id, multiplicador, duracao_horas,chat_id):
    try:
        conn, cursor = conectar_banco_dados()
        fim_boost = datetime.now() + timedelta(hours=duracao_horas)

        # Inserir o boost de cenouras na tabela 'boosts'
        cursor.execute("""
            INSERT INTO boosts (id_usuario, tipo_boost, multiplicador, fim_boost)
            VALUES (%s, 'cenouras', %s, %s)
            ON DUPLICATE KEY UPDATE multiplicador = %s, fim_boost = %s
        """, (user_id, multiplicador, fim_boost, multiplicador, fim_boost))
        
        conn.commit()

        bot.send_message(chat_id, f"🌟 Você recebeu um Super Boost de Cenouras! Todas as cenouras que você ganhar serão multiplicadas por {multiplicador} nas próximas {duracao_horas} horas.")
    
    except Exception as e:
        print(f"Erro ao adicionar Super Boost de Cenouras: {e}")
    
    finally:
        fechar_conexao(cursor, conn)


def aplicar_boost_cenouras(user_id, cenouras_ganhas):
    try:
        conn, cursor = conectar_banco_dados()

        # Verificar se o usuário tem um boost ativo de cenouras
        cursor.execute("""
            SELECT multiplicador, fim_boost 
            FROM boosts 
            WHERE id_usuario = %s AND tipo_boost = 'cenouras' AND fim_boost > NOW()
        """, (user_id,))
        
        resultado = cursor.fetchone()

        if resultado:
            multiplicador, fim_boost = resultado
            cenouras_com_boost = cenouras_ganhas * multiplicador
            cursor.execute("UPDATE usuarios SET cenouras = cenouras + %s WHERE id_usuario = %s", (cenouras_com_boost, user_id))
            bot.send_message(user_id, f"🌟 Suas cenouras foram multiplicadas! Você recebeu {cenouras_com_boost} cenouras.")
        else:
            # Sem boost ativo, dá as cenouras normalmente
            cursor.execute("UPDATE usuarios SET cenouras = cenouras + %s WHERE id_usuario = %s", (cenouras_ganhas, user_id))
            bot.send_message(user_id, f"Você recebeu {cenouras_ganhas} cenouras.")

        conn.commit()
    
    except Exception as e:
        print(f"Erro ao aplicar boost de cenouras: {e}")
    
    finally:
        fechar_conexao(cursor, conn)

# Lista de emojis de gostosuras
emojis_gostosura = [
    "🍬", "🍪", "🍭", "🍩", "🧁", "🧇", "🍫", "🎂", "🍡", "🍨",
    "🍰", "🍯", "🥞", "🍦", "🍮", "🍧"
]
# Lista de emojis de travessuras
emojis_travessura = [
    "🎃", "👻", "🕸️", "🕷️", "🧟‍♀️", "🐈‍⬛", "🦇", "⚰️", "💀", 
    "🕯️", "☠️", "🌕", "👿", "😈"
]
@bot.message_handler(func=lambda message: message.text and message.text.startswith('+100vip'))
def handle_100vip(message):
    try:
        user_id = message.from_user.id
        conn, cursor = conectar_banco_dados()

        # Verificar se o usuário é VIP
        query_verificar_vip = "SELECT COUNT(*) FROM vips WHERE id_usuario = %s"
        cursor.execute(query_verificar_vip, (user_id,))
        is_vip = cursor.fetchone()[0] > 0

        if is_vip:
            # Verificar se o usuário já usou o comando +100vip
            query_verificar_uso = "SELECT COUNT(*) FROM usuarios_100vip WHERE id_usuario = %s"
            cursor.execute(query_verificar_uso, (user_id,))
            ja_usou = cursor.fetchone()[0] > 0

            if ja_usou:
                bot.send_message(message.chat.id, "Você já usou o código +100vip e não pode utilizá-lo novamente.")
            else:
                # Adicionar 100 pétalas ao usuário
                query_adicionar_petalas = "UPDATE usuarios SET petalas = petalas + 100 WHERE id_usuario = %s"
                cursor.execute(query_adicionar_petalas, (user_id,))

                # Registrar que o usuário usou o comando +100vip
                query_registrar_uso = "INSERT INTO usuarios_100vip (id_usuario) VALUES (%s)"
                cursor.execute(query_registrar_uso, (user_id,))
                
                conn.commit()

                bot.send_message(message.chat.id, "🎉 Parabéns! Você recebeu 100 pétalas por ser VIP! 🌸")

        else:
            bot.send_message(message.chat.id, "Você não é VIP e não pode receber esse bônus.")

    except Exception as e:
        print(f"Erro ao processar o comando +100vip: {e}")
        bot.send_message(message.chat.id, "Ocorreu um erro ao processar sua solicitação.")

    finally:
        fechar_conexao(cursor, conn)
# Função para iniciar a Fonte Extra
def ativar_fonte_extra(user_id,chat_id):
    # Envia a mensagem pedindo os IDs dos peixes
    bot.send_message(user_id, "Você ativou uma Fonte Extra! Por favor, me envie até 5 IDs dos peixes que você quer usar separados por espaço.")
    
    # Registra o próximo passo para aguardar os IDs
    bot.register_next_step_handler_by_chat_id(user_id, processar_fonte_extra)

# Função para processar a resposta com os IDs
def processar_fonte_extra(message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        command_parts = message.text.split()  # Separar os IDs recebidos na resposta
        id_cartas = list(map(int, command_parts))[:5]  # Pega até 5 IDs

        # Verificar se foram fornecidos IDs válidos
        if not id_cartas or len(id_cartas) == 0:
            bot.send_message(chat_id, "Você não forneceu IDs válidos. Por favor, tente novamente.")
            return
        
        # Realizar a lógica da fonte
        quantidade_cenouras = random.randint(10, 20)  # Você pode modificar isso conforme necessário
        diminuir_cenouras(user_id, quantidade_cenouras)

        # Simula o processo da fonte com base nos IDs fornecidos
        results = []
        for id_carta in id_cartas:
            chance = random.randint(1, 100)
            if chance <= 15:  # 15% de chance de sucesso, você pode ajustar
                results.append(id_carta)
                update_inventory(user_id, id_carta)

        # Enviar a resposta baseada nos resultados
        if results:
            bot.send_message(chat_id, f"🎉 As águas da fonte revelaram os seguintes peixes: {', '.join(map(str, results))}")
        else:
            bot.send_message(chat_id, "A fonte se manteve tranquila e nada foi revelado desta vez. Tente novamente mais tarde!")

    except Exception as e:
        print(f"Erro ao processar a Fonte Extra: {e}")
        bot.send_message(message.chat.id, "Ocorreu um erro ao processar a sua Fonte Extra. Tente novamente.")


        
url_imagem = "https://pub-6f23ef52e8614212a14d24b0cf55ae4a.r2.dev/BQACAgEAAxkBAAIcfGcVeT6gaLXd0DKA7aihUQJfV62hAAJMBQACSV6xRD2puYHoSyajNgQ.jpg"

def realizar_halloween_gostosura(user_id, chat_id):
    try:
        print(f"DEBUG: Iniciando gostosura para o usuário {user_id}")
        chance = random.randint(1, 12)  # 12 tipos de gostosuras diferentes
        print(f"DEBUG: Chance sorteada: {chance}")

        if chance == 1:
            cenouras_ganhas = random.randint(50, 100)
            aumentar_cenouras(user_id, cenouras_ganhas)
            emoji = random.choice(emojis_gostosura)
            bot.send_message(chat_id, f"{emoji} Você encontrou um saco de doces! Parabéns, recebeu {cenouras_ganhas} cenouras!")
            print(f"DEBUG: {cenouras_ganhas} cenouras enviadas ao usuário {user_id}")

        elif chance == 2:
            print(f"DEBUG: Adicionando carta faltante de Halloween para o usuário {user_id}")
            adicionar_carta_faltante_halloween(user_id, chat_id)

        elif chance == 3:
            print(f"DEBUG: Adicionando VIP temporário para o usuário {user_id}")
            adicionar_vip_temporario(user_id, GRUPO_SUGESTAO,chat_id)

        elif chance == 4:
            print(f"DEBUG: Adicionando proteção temporária para o usuário {user_id}")
            adicionar_protecao_temporaria(user_id,chat_id)

        elif chance == 5:
            print(f"DEBUG: Realizando combo de gostosura para o usuário {user_id}")
            realizar_combo_gostosura(user_id, chat_id)

        elif chance == 6:
            print(f"DEBUG: Encontrando abóbora para o usuário {user_id}")
            encontrar_abobora(user_id,chat_id)

        elif chance == 7:
            print(f"DEBUG: Ganhando caixa misteriosa para o usuário {user_id}")
            bot.send_message(chat_id, f"🎃 Uma caixa miseriosa foi enviada para seu endereço!")
            ganhar_caixa_misteriosa(user_id,chat_id)

        elif chance == 8:
            print(f"DEBUG: Mostrando portas de escolha para o usuário {user_id}")
            bot.send_message(chat_id, f"🎃 Parabéns! 3 portas foram enviadas para o seu privado, escolha com sabedoria!")
            mostrar_portas_escolha(user_id)

        elif chance == 9:
            print(f"DEBUG: Ativando fonte extra para o usuário {user_id}")
            bot.send_message(chat_id, f"🎃 Parabéns! A fonte fez uma breve aparição no seu privado, corra antes que ela suma!")
            ativar_fonte_extra(user_id, chat_id)

        elif chance == 10:
            print(f"DEBUG: Adicionando inversão de travessura para o usuário {user_id}")
            adicionar_inverter_travessura(user_id,chat_id)

        elif chance == 11:
            print(f"DEBUG: Adicionando super boost de cenouras para o usuário {user_id}")
            duracao_horas = random.randint(1, 6)
            multiplicador= random.randint(2, 4)
            adicionar_super_boost_cenouras(user_id, multiplicador, duracao_horas,chat_id)

        elif chance == 12:
            print(f"DEBUG: Iniciando compartilhamento de gostosura para o usuário {user_id}")
            iniciar_compartilhamento(user_id,chat_id)

    except Exception as e:
        print(f"DEBUG: Erro ao realizar gostosura para o usuário {user_id}: {e}")
        traceback.print_exc()
        bot.send_message(user_id, "Ocorreu um erro ao realizar a gostosura.")

def mudar_favorito_usuario(user_id,chat_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Selecionar uma carta aleatória do inventário do usuário
        query = """
            SELECT id_personagem FROM inventario
            WHERE id_usuario = %s
            ORDER BY RAND() LIMIT 1
        """
        cursor.execute(query, (user_id,))
        resultado = cursor.fetchone()

        if resultado:
            novo_favorito = resultado[0]
            # Atualizar o favorito na tabela `usuarios`
            alterar_usuario(user_id, "fav", novo_favorito,chat_id)
            bot.send_message(chat_id, f"👻 Travessura! Seu favorito agora é a carta ID {novo_favorito}!")
        else:
            bot.send_message(chat_id, "Parece que você não tem cartas no inventário para fazer essa travessura.")

    except Exception as e:
        print(f"Erro ao mudar favorito para o usuário {user_id}: {e}")
        traceback.print_exc()
    finally:
        fechar_conexao(cursor, conn)

def bloquear_comandos_usuario(user_id, duracao_minutos,chat_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Calcular o tempo de término do bloqueio
        fim_bloqueio = datetime.now() + timedelta(minutes=duracao_minutos)

        # Inserir ou atualizar o tempo de bloqueio na tabela `bloqueios_comandos`
        query = """
            INSERT INTO bloqueios_comandos (id_usuario, fim_bloqueio)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE fim_bloqueio = %s
        """
        cursor.execute(query, (user_id, fim_bloqueio, fim_bloqueio))
        conn.commit()

        # Enviar mensagem informando sobre o bloqueio
        bot.send_message(chat_id, f"👻 Travessura! Você está invisível por {duracao_minutos} minutos. Nenhum comando será processado!")

    except Exception as e:
        print(f"Erro ao bloquear comandos para o usuário {user_id}: {e}")
        traceback.print_exc()
    finally:
        fechar_conexao(cursor, conn)
def verificar_bloqueio_comandos(user_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Verificar se o usuário está bloqueado
        query = "SELECT fim_bloqueio FROM bloqueios_comandos WHERE id_usuario = %s"
        cursor.execute(query, (user_id,))
        resultado = cursor.fetchone()

        if resultado:
            fim_bloqueio = resultado[0]
            if datetime.now() < fim_bloqueio:
                # Se ainda estiver dentro do período de bloqueio, retorna True
                return True, (fim_bloqueio - datetime.now()).seconds // 60
        return False, 0

    except Exception as e:
        print(f"Erro ao verificar bloqueio de comandos para o usuário {user_id}: {e}")
        traceback.print_exc()
        return False, 0
    finally:
        fechar_conexao(cursor, conn)
def apagar_carta_aleatoria(user_id, chat_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Verificar se o jogador tem cartas no inventário
        cursor.execute("""
            SELECT i.id_personagem, i.quantidade, p.nome, p.subcategoria
            FROM inventario i
            JOIN personagens p ON i.id_personagem = p.id_personagem
            WHERE i.id_usuario = %s
        """, (user_id,))
        cartas = cursor.fetchall()

        if not cartas:
            bot.send_message(chat_id, "👻 O demônio tentou, mas você não tem cartas no inventário para serem apagadas.")
            return

        # Selecionar uma carta aleatória para apagar
        carta_apagada = random.choice(cartas)
        id_carta, quantidade_carta, nome_carta, subcategoria = carta_apagada

        if quantidade_carta > 1:
            # Reduzir apenas uma unidade da carta
            cursor.execute("UPDATE inventario SET quantidade = quantidade - 1 WHERE id_usuario = %s AND id_personagem = %s", (user_id, id_carta))
            bot.send_message(chat_id, f"👻 O demônio removeu uma unidade da carta ID {id_carta} - {nome_carta} de {subcategoria}. Você ainda tem {quantidade_carta - 1} restantes.")
        else:
            # Apagar a carta completamente do inventário
            cursor.execute("DELETE FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (user_id, id_carta))
            bot.send_message(chat_id, f"👻 O demônio apagou a carta ID {id_carta} - {nome_carta} de {subcategoria} do seu inventário!")

        conn.commit()

    except Exception as e:
        print(f"Erro ao apagar carta: {e}")
        bot.send_message(chat_id, "Ocorreu um erro ao tentar apagar sua carta.")
    finally:
        fechar_conexao(cursor, conn)

        fechar_conexao(cursor, conn)

def aplicar_travessura(user_id, chat_id):
    try:
        print(f"DEBUG: Aplicando travessura para o usuário {user_id}")
        # Lista de travessuras exceto a praga
        travessuras = [
            "perder_cenouras",            # 1. Perde uma quantidade de cenouras
            "mudar_nome_engracado",       # 2. Nome do jogador é alterado para algo engraçado
            "mudar_musica_ze_felipe",     # 3. Música do perfil é alterada para uma das músicas do Zé Felipe
            "mudar_bio_engracada",        # 4. Bio do jogador é alterada para algo engraçado
            "mudar_fav_aleatorio",        # 5. O favorito do jogador é alterado para uma carta aleatória
            "bloqueio_pesca",             # 6. Bloqueio de pescar por alguns minutos
            "bloqueio_comandos",          # 7. Bloqueio de enviar comandos (invisível)
            "mensagens_embaralhadas",     # 8. Mensagens do bot são embaralhadas
            "apagar_carta_aleatoria"      # 22. Apaga uma carta aleatória do inventário
        ]
        
        # Escolher uma travessura aleatória (exceto a praga)
        travessura_escolhida = random.choice(travessuras)
        print(f"DEBUG: Travessura escolhida: {travessura_escolhida}")

        # Aplicar a travessura escolhida
        if travessura_escolhida == "perder_cenouras":
            perder_cenouras(user_id, chat_id)
        elif travessura_escolhida == "mudar_nome_engracado":
            mudar_nome_engracado(user_id, chat_id)
        elif travessura_escolhida == "mudar_musica_ze_felipe":
            mudar_musica_ze_felipe(user_id, chat_id)
        elif travessura_escolhida == "mudar_bio_engracada":
            mudar_bio_engracada(user_id, chat_id)
        elif travessura_escolhida == "mudar_fav_aleatorio":
            mudar_fav_aleatorio(user_id, chat_id)
        elif travessura_escolhida == "bloqueio_pesca":
            bloquear_pesca(user_id, chat_id)
        elif travessura_escolhida == "bloqueio_comandos":
            bloquear_comandos(user_id, chat_id)
        elif travessura_escolhida == "mensagens_embaralhadas":
            embaralhar_mensagens(user_id, chat_id)
        elif travessura_escolhida == "apagar_carta_aleatoria":
            apagar_carta_aleatoria(user_id, chat_id)
        elif tipo_travessura == 'apagar_carta':
            apagar_carta_aleatoria(user_id, chat_id)
    except Exception as e:
        print(f"Erro ao aplicar a travessura: {e}")
        bot.send_message(chat_id, f"Ocorreu um erro ao aplicar a travessura.")

# Função de contagem regressiva para a praga
def contagem_regressiva_praga(user_id, chat_id):
    try:
        # Espera por 10 minutos
        time.sleep(600)  # 600 segundos = 10 minutos

        # Se o usuário ainda estiver com a praga, aplica uma travessura aleatória
        if jogo_praga.get('user_id') == user_id:
            aplicar_travessura(user_id, chat_id)  # Aplica uma travessura aleatória
            bot.send_message(chat_id, "💀 Você não passou a praga a tempo. A travessura foi aplicada!")
            jogo_praga.clear()  # Limpar a praga

    except Exception as e:
        bot.send_message(chat_id, f"Erro ao executar a contagem regressiva da praga: {e}")
# Dicionário para armazenar quem tem a praga e o horário
jogo_praga = {}

# Função para iniciar a travessura de pega-pega
def iniciar_travessura_praga(user_id, chat_id):
    try:
        # Inicia a praga para o usuário
        bot.send_message(chat_id, f"👻 Você foi amaldiçoado com uma praga! Passe a praga para outra pessoa usando +praga em até 10 minutos, ou será afetado pela travessura!")
        
        # Salvar a praga e o horário inicial
        jogo_praga['user_id'] = user_id
        jogo_praga['start_time'] = time.time()

        # Iniciar contagem regressiva de 10 minutos
        threading.Thread(target=contagem_regressiva_praga, args=(user_id, chat_id,)).start()

    except Exception as e:
        bot.send_message(chat_id, f"Erro ao iniciar a travessura de praga: {e}")

# Função para o comando +praga (responder a uma mensagem de outro usuário)
@bot.message_handler(func=lambda message: message.text.startswith('+praga'))
def passar_praga(message):
    try:
        # O usuário deve responder à mensagem de outro usuário
        if not message.reply_to_message:
            bot.send_message(message.chat.id, "👻 Você precisa responder a uma mensagem de outro usuário para passar a praga!")
            return

        user_id = message.from_user.id
        target_user_id = message.reply_to_message.from_user.id
        chat_id = message.chat.id

        # Verificar se o usuário tem a praga
        if jogo_praga.get('user_id') != user_id:
            bot.send_message(chat_id, "👻 Você não tem a praga para passar!")
            return

        # Transferir a praga para o outro usuário
        jogo_praga['user_id'] = target_user_id
        jogo_praga['start_time'] = time.time()

        # Informar o alvo que ele recebeu a praga
        bot.send_message(chat_id, f"👻 {message.reply_to_message.from_user.first_name}, você recebeu a praga! Passe para outra pessoa ou sofrerá a travessura!")
        bot.send_message(user_id, "🎃 Você passou a praga para outro usuário com sucesso!")

    except Exception as e:
        bot.send_message(message.chat.id, f"Erro ao passar a praga: {e}")

def ativar_travessura_embaralhamento(chat_id, id_usuario):
    # Definir duração aleatória entre 30 minutos e 2 horas
    duracao = random.randint(30, 120)  # Em minutos
    fim_travessura = datetime.now() + timedelta(minutes=duracao)

    # Enviar mensagem informando sobre a travessura
    bot.send_message(chat_id, "💀 Travessura! Suas mensagens estarão incompletas por um tempo!")

    # Registrar a travessura na tabela
    conn, cursor = conectar_banco_dados()
    try:
        query = """
            INSERT INTO travessuras (id_usuario, tipo_travessura, fim_travessura)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE fim_travessura = VALUES(fim_travessura)
        """
        cursor.execute(query, (id_usuario, 'embaralhamento', fim_travessura))
        conn.commit()
        print(f"[DEBUG] Travessura de embaralhamento ativada para {id_usuario}, termina às {fim_travessura}")
    except Exception as e:
        print(f"Erro ao registrar travessura: {e}")
    finally:
        fechar_conexao(cursor, conn)
import random
from datetime import datetime, timedelta
from telebot import types

# Armazenamento de jogadores no labirinto
jogadores_labirinto = {}

# Função para criar o labirinto com um caminho garantido até a saída
def gerar_labirinto_com_caminho_e_validacao(tamanho=10):
    labirinto = [['🪨' for _ in range(tamanho)] for _ in range(tamanho)]
    
    # Ponto inicial e final
    x, y = 1, 1  # Início
    saida_x, saida_y = tamanho - 2, random.randint(1, tamanho - 2)  # Saída aleatória
    
    # Backtracking para garantir caminho à saída
    caminho = [(x, y)]
    labirinto[x][y] = '⬜'
    
    while (x, y) != (saida_x, saida_y):
        direcoes = []
        if x > 1 and labirinto[x-1][y] == '🪨':
            direcoes.append((-1, 0))
        if x < tamanho - 2 and labirinto[x+1][y] == '🪨':
            direcoes.append((1, 0))
        if y > 1 and labirinto[x][y-1] == '🪨':
            direcoes.append((0, -1))
        if y < tamanho - 2 and labirinto[x][y+1] == '🪨':
            direcoes.append((0, 1))

        if not direcoes:
            x, y = caminho.pop()
        else:
            dx, dy = random.choice(direcoes)
            x += dx
            y += dy
            labirinto[x][y] = '⬜'
            caminho.append((x, y))

    # Define a saída
    labirinto[saida_x][saida_y] = '🚪'
    
    # Adiciona monstros e recompensas
    for _ in range(5):
        while True:
            mx, my = random.randint(1, tamanho - 2), random.randint(1, tamanho - 2)
            if labirinto[mx][my] == '🪨' and (mx, my) not in caminho:
                labirinto[mx][my] = '👻'
                break
    
    for _ in range(3):
        while True:
            rx, ry = random.randint(1, tamanho - 2), random.randint(1, tamanho - 2)
            if labirinto[rx][ry] == '🪨' and (rx, ry) not in caminho:
                labirinto[rx][ry] = '🎃'
                break

    return labirinto

# Função para mostrar o labirinto parcialmente, baseado na posição do jogador
def mostrar_labirinto(labirinto, posicao):
    mapa = ""
    x, y = posicao
    for i in range(len(labirinto)):
        for j in range(len(labirinto[i])):
            if (i, j) == posicao:
                mapa += "🔦"
            elif abs(x - i) <= 1 and abs(y - j) <= 1:
                mapa += labirinto[i][j]
            else:
                mapa += "⬛"
        mapa += "\n"
    return mapa

# Função para mover o jogador no labirinto
def mover_posicao(posicao_atual, direcao, labirinto):
    x, y = posicao_atual
    if direcao == 'norte' and x > 0 and labirinto[x - 1][y] != '🪨':
        return (x - 1, y)
    elif direcao == 'sul' and x < len(labirinto) - 1 and labirinto[x + 1][y] != '🪨':
        return (x + 1, y)
    elif direcao == 'leste' and y < len(labirinto[0]) - 1 and labirinto[x][y + 1] != '🪨':
        return (x, y + 1)
    elif direcao == 'oeste' and y > 0 and labirinto[x][y - 1] != '🪨':
        return (x, y - 1)
    return posicao_atual  # Movimento inválido, retorna posição atual

def iniciar_labirinto(user_id, chat_id):
    try:
        tamanho = 10  # Tamanho do labirinto
        labirinto = gerar_labirinto_com_caminho_e_validacao(tamanho)
        posicao_inicial = (1, 1)  # Início fixo
        movimentos_restantes = 35  # Limite de movimentos para escapar

        # Armazena o estado do jogador
        jogadores_labirinto[user_id] = {
            "labirinto": labirinto,
            "posicao": posicao_inicial,
            "movimentos": movimentos_restantes
        }

        mapa = mostrar_labirinto(labirinto, posicao_inicial)
        markup = criar_botoes_navegacao()
        
        bot.send_message(chat_id, f"🏰 Bem-vindo ao Labirinto! Você tem {movimentos_restantes} movimentos para escapar.\n\n{mapa}", reply_markup=markup)
    except Exception as e:
        print(f"Erro ao iniciar o labirinto: {e}")

# Função para criar botões de navegação
def criar_botoes_navegacao():
    markup = types.InlineKeyboardMarkup(row_width=4)
    markup.add(
        types.InlineKeyboardButton("⬆️", callback_data="norte"),
        types.InlineKeyboardButton("⬅️", callback_data="oeste"),
        types.InlineKeyboardButton("➡️", callback_data="leste"),
        types.InlineKeyboardButton("⬇️", callback_data="sul")
    )
    return markup

# Função para mover dentro do labirinto
@bot.callback_query_handler(func=lambda call: call.data in ['norte', 'sul', 'leste', 'oeste'])
def mover_labirinto(call):
    id_usuario = call.from_user.id
    if id_usuario not in jogadores_labirinto:
        bot.send_message(call.message.chat.id, "👻 Inicie o labirinto com /labirinto.")
        return
    
    direcao = call.data
    jogador = jogadores_labirinto[id_usuario]
    labirinto = jogador["labirinto"]
    posicao_atual = jogador["posicao"]
    movimentos_restantes = jogador["movimentos"]
    
    nova_posicao = mover_posicao(posicao_atual, direcao, labirinto)
    
    if nova_posicao != posicao_atual:  # Movimento válido
        jogadores_labirinto[id_usuario]["posicao"] = nova_posicao
        jogadores_labirinto[id_usuario]["movimentos"] -= 1
        movimentos_restantes -= 1
        conteudo = labirinto[nova_posicao[0]][nova_posicao[1]]
        
        # Verifica vitória, derrota ou continuidade
        if conteudo == '🚪':
            bot.edit_message_text(f"🏆 Parabéns! Você encontrou a saída!\n\n{revelar_labirinto(labirinto)}", call.message.chat.id, call.message.message_id)
            del jogadores_labirinto[id_usuario]  # Remove jogador
        elif movimentos_restantes == 0:
            bot.edit_message_text(f"😢 Seus movimentos acabaram. Fim de jogo!\n\n{revelar_labirinto(labirinto)}", call.message.chat.id, call.message.message_id)
            del jogadores_labirinto[id_usuario]
        else:
            atualizar_labirinto(call, labirinto, nova_posicao, movimentos_restantes, conteudo)
    else:
        bot.answer_callback_query(call.id, "👻 Direção bloqueada por uma parede!")

# Função para atualizar o labirinto e aplicar consequências (monstro ou recompensa)
def atualizar_labirinto(call, labirinto, posicao, movimentos_restantes, conteudo):
    mapa = mostrar_labirinto(labirinto, posicao)
    markup = criar_botoes_navegacao()

    if conteudo == '👻':
        labirinto[posicao[0]][posicao[1]] = '⬜'
        bot.edit_message_text(f"👻 Você encontrou um monstro! Perdeu 20 cenouras. Quer encerrar ou continuar?\n\n{mapa}", 
                              call.message.chat.id, call.message.message_id, reply_markup=criar_botoes_opcoes())
        aplicar_penalidade_cenouras(call.from_user.id, -20)
    elif conteudo == '🎃':
        labirinto[posicao[0]][posicao[1]] = '⬜'
        bot.edit_message_text(f"🎃 Você encontrou uma abóbora! Ganhou 50 cenouras. Quer encerrar ou continuar?\n\n{mapa}", 
                              call.message.chat.id, call.message.message_id, reply_markup=criar_botoes_opcoes())
        aplicar_recompensa_cenouras(call.from_user.id, 50)
    else:
        bot.edit_message_text(f"Movimentos restantes: {movimentos_restantes}\n\n{mapa}", 
                              call.message.chat.id, call.message.message_id, reply_markup=markup)

# Função para criar botões de opções (encerrar ou continuar)
def criar_botoes_opcoes():
    markup_opcoes = types.InlineKeyboardMarkup()
    markup_opcoes.add(
        types.InlineKeyboardButton("Encerrar", callback_data="encerrar"),
        types.InlineKeyboardButton("Continuar", callback_data="continuar")
    )
    return markup_opcoes

# Handlers para encerrar ou continuar no labirinto
@bot.callback_query_handler(func=lambda call: call.data in ['encerrar', 'continuar'])
def encerrar_ou_continuar(call):
    id_usuario = call.from_user.id
    if call.data == 'encerrar':
        bot.edit_message_text("💀 Você encerrou o jogo. Fim de jornada!", call.message.chat.id, call.message.message_id)
        del jogadores_labirinto[id_usuario]
    elif call.data == 'continuar':
        jogador = jogadores_labirinto[id_usuario]
        mapa = mostrar_labirinto(jogador["labirinto"], jogador["posicao"])
        markup = criar_botoes_navegacao()
        bot.edit_message_text(f"Movimentos restantes: {jogador['movimentos']}\n\n{mapa}", call.message.chat.id, call.message.message_id, reply_markup=markup)

def realizar_halloween_travessura(user_id, chat_id):
    try:
        print(f"DEBUG: Iniciando travessura para o usuário {user_id}")
                # Verificar se o usuário tem proteção ativa
        if verificar_protecao_travessura(user_id):
            bot.send_message(chat_id, "🛡️ Você está protegido contra travessuras! Nada aconteceu desta vez.")
            return

        chance = random.randint(1, 20)  # 22 tipos de travessuras diferentes
        print(f"DEBUG: Chance sorteada: {chance}")

        if chance == 1:
            # Perder cenouras
            cenouras_perdidas = random.randint(20, 50)
            diminuir_cenouras(user_id, cenouras_perdidas)
            bot.send_message(chat_id, f"👻 Travessura! Você perdeu {cenouras_perdidas} cenouras!")

        elif chance == 2:
            # Mudar o nome para algo engraçado
            nome_novo = random.choice([
                "Zé Bobo", 
                "Palhaço Triste", 
                "Mestre das Travessuras", 
                "Tio da Pamonha", 
                "Príncipe da Zona Leste", 
                "Ninja da Calçada", 
                "Sábio do Pastel", 
                "Lord do Desespero", 
                "Chiclete Grudento", 
                "Salsicha Triste", 
                "Bobo da Corte", 
                "Rei do Nada", 
                "Menino de Ouro", 
                "Fantasma do Zap", 
                "Sheik da Quebrada",  
                "Ícone dos Perdidos", 
                "Mestre dos Memes", 
                "Guru das Piadas Ruins", 
                "Pé de Pano", 
                "Zé das Couves", 
                "Vendedor de Ilusões",
                "Tá Tranquilo, Tá Favorável", 
                "Cara do Tá Louco Bicho", 
                "Famoso Quem?", 
                "Cadê o My Precious?", 
                "Bicho Solto do Zap", 
                "Boneco de Olinda", 
                "Neymar Caído", 
                "Menino Neymar", 
                "Mr. Catra", 
                "Senhor Barriga", 
                "Mainha da Internet", 
                "Dono da Kombi", 
                "A Tia do Pavê", 
                "Agostinho Carrara", 
                "Seu Madruga", 
                "Judite do Telefone", 
                "Lineu Silva", 
                "Kiko", 
                "Bebel Carrara", 
                "Seu Peru", 
                "Rolando Lero",  
                "Cabeção", 
                "Paulão da Regulagem", 
                "Eterno Beiçola", 
                "Didi Mocó", 
                "Richarlissom José Tite Junior Paquetá piuzinho Lucas burrao da Silva 🇧🇷🇧🇷🇧🇷", 
                "Jaiminho Carteiro", 
                "Dona Florinda", 
                "Boça",
                "Lindah💍", 
                "Gattinha😋", 
                "Maravilhosa🌸", 
                "TãÖö_LïNdÄa 😍😍👏❤️💘💍💑👑💞🍃 ", 
                "RöStÏnHöÖ_Dë_PrÏnCëSäÄ🙆👑✊😍😍😘💍💞", 
                "seloko fidelidade e pra cachorro🔥nois e patife", 
                "sai fora pvt", 
                "Boça",
                "Rei dos Áudios de 7 Minutos"
            ])
            mudar_nome_usuario(user_id, nome_novo, chat_id)

        elif chance == 3:
            # Mudar a música para Zé Felipe
            nova_musica = random.choice([
                "Dança do Créu - MC Créu",
                "Rap do Zé Felipe", 
                "Bandido - Zé Felipe", 
                "Malvada - Zé Felipe",
                "Cachorrinho - Kelly Key", 
                "Eguinha Pocotó - MC Serginho e Lacraia",
                "Morango do Nordeste - Karametade",
                "Adoleta - Kelly Key",
                "Vou Passar Cerol na Mão - Bonde do Tigrão",
                "Dança do Quadrado",
                "Piririm Pom Pom - As Chiquititas",
                "Vem Ni Mim Que Eu Tô Carente - DJ Sandrinho",
                "Ragatanga - Rouge",
                "Na Boquinha da Garrafa - Cia. do Pagode",
                "Tô Nem Aí - Larissa Manoela",
                "Só Love - Claudinho & Buchecha",
                "Éguinha Mijona - Deize Tigrona",
                "Eu Quero Tchu, Eu Quero Tcha - João Lucas & Marcelo",
                "A Barata da Vizinha - MC Batata",
                "É o Tchan no Havaí - É o Tchan",
                "Festa no Apê - Latino",
                "Me Leva - Latino",
                "Amigo Fura Olho - Latino",
                "Renata Ingrata - Latino",
                "Cátia Catchaça - Latino",
                "Caneta Azul - Manoel Gomes",
                "Malandramente - Dennis e MCs Nandinho & Nego Bam",
                "Ai Se Eu Te Pego - Michel Teló",
                "Saudade de Ex - Gaab e MC Davi",
                "Tô Comendo Água - Barões da Pisadinha",
                "Chupa Que é de Uva - MC Jair da Rocha",
                "Despedida de Solteiro - Latino",
                "Dança do Vampiro - Asa de Águia"
            ])
            mudar_musica_usuario(user_id, nova_musica,chat_id)

        elif chance == 4:
            # Mudar a bio para uma bio engraçada baseada em memes
            bio_nova = random.choice([
                "RECEITA DO LÓLÓ ORIGINAL:\nO intuito desse texto é viralizar e, por sorte, melhorar a qualidade do lóló encontrado no carnaval do Brasil. Com os anos, os lolozeiros têm depreciado a veracidade do no nosso amado lóló e nos fornecido um produto de qualidade inferior.\nEntão vamos lá:",
                "Oi gente sou tenente da PMDF e achei o celular desse patriota no Congresso, infelizmente ele veio a óbito lutando pelo nosso país. Sejam sinceros (mulheres apenas) o que vocês achavam dele? Tinham crush nele? Gostavam dele? deem uma nota de 1 a 10.o",
                "👧🏽: *bora toma uma*\n👩🏿: *bora* ...\n👧🏽: *bora pra festa* .?\n👩🏿: *bora*...\n👧🏽: *Bora pra igreja*?\n👩🏿: *Se der eu vou*\n👧🏽: *Blz quando Deus* *volta se der ele ti leva*.\n*Ti juro só repasse se você não tiver vergonha de Deus*\n*Mais é só se vc tever coragem!!😉*",
                'Defesa Pessoal 😅\nSe alguém 👤👤 te disser: 🗨️\n"és um narigudo!"👃\ntu respondes: 🗣️\nJá olhaste 👀👀 bem pra ti?!\nCom esse focinho de Javali? 🐗\no mais raro 💎 que eu já vi. 👁️\nTentaste uma ofensa 🤬🤬 menino 🧒\nmas eu nem senti. 😁😁\nhe hee 😉😉\ntoma lá 😎',
                "relíquia da ZN 🚩🇸🇲 dinda do gael👩‍👦filha da dona ivone👵 mãe do juninho 👩‍🍼 namorada do do marcinho do BRX 👩‍❤️‍👨",
                "Eu:perco no frefaire\nParede: não não por favor 😭😭😭😭😭😭\nEu: 👊👊👊😈😈😈😈😈😡😡😡👊👊👊",
                "Mais perdida que cebola em salada de frutas",
                "Minha kara quando digo que ADORO lasanha\ne a minha miiiiiiiiga crente diz: \nadora nãããoo Markim tu gosta\npq a gente ADORA só o senhor...\nahhhhh me poupe jessica",
                "CORRENTE DE ORAÇÃO PELO BRASIL📿\nQue todas as entidades🙏🏼 existentes ajudem o Brasil🇧🇷  a passar dessa fase🙌🏼\nRepasse para os seus contatos 🙌🏼🙌🏼🙌🏼",
                "BORA BIL",
                "amor, tô terminando com você. não é você, você foi ate que bem normie. sou eu que sou assim meio cringe, meio noggers. me desculpe se isso é random mas eu tive que fazer, eu tenho me sentido edgy e nosso relacionamento tem sido bluepill por meses, é hora de acabar fella, sem bait",
                "Bolsonaro querido Presidente, teu povo está pronto ✅ pra o que for necessário! Que o “SENHOR DOS EXÉRCITOS” dê diretrizes para o “Comandante Supremo das Forças Armadas!”\nTMJ 🫡🫡🫡🫡\nEu cozinho e lavo panelas de boas! Depois retomo a minha empresa.",
                "eu sou:\n○ lésbica\n○ hétero\n○ bi\n● extremamente brasileiro. verde, azul, amarelo e branco 😝😝🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷",
                "Ah 🅰️que felicidade. 😀É que  🤔eu brigo🤬, choro😢, rio🤣, e brigo 😡e deleto ❌e bloqueio🚫 e ‼️fico feliz 😆e triste 😫e dou 🍑castigo😣, depois ⏩me arrependo 😞e choro 😭e rio  🤣e isto ⬅️gera ➡️um mau 😒estar nas 💢pessoas👯‍♂️ e gera ➡️desconfiança 🥸também. 😢Mas ⚠️tem uma coisa ⏺que eu 👾não faço☝️ é manipular😨 ninguém.🔇 Deixo ♾livre 🦋para pensar🤔🧠.",
                "eu não sou bonito sério eu sou tipo muito feio pessoalmente tipo por video caralho e eu não arrumei meu cabelo eu juro que não arrumei meu cabelo porque tu pediu pra mim não arrumar e a minha voz não é bonita eu acho minha voz tipo é sério eu acho ela muito ridícula sei lá argh",
                "LISTA DE PROCURADOS DA INTERPOL DIVULGADA ESSA SEXTA!!🚨\n🇩🇪 Prënsa Ducht🚨\n🇳🇱 Veer Deen🚨\n🇯🇵 Tabaku Ma Luko🚨\n🇨🇲 Dedudi Guri Lah🚨\n🇸🇦 Kahnah Bih Satyvah🚨\n🇹🇷 Çigar Duhčapeta🚨\n🇵🇹 Maria Joana🚨\n🇰🇷 Kadeo-Bong🚨",
                "Sou hetero, mas a atração sexual que o bolsonaro exala é de outro patamar slcccc🥵",
                "ei, voce gosta de anime é? entao me diz todos os jutsus e sharingas de naruto, pra ver se voce e realmente otaku. não sabe né?? ainda diz que gosta de anime kkkkkkkkkkk",
                "Se eu 👤👈 ganhasse 🎁um ☝️ real 💸 por cada minuto ⏱️ que penso 🤔🧠 nela 😍eu não 🙅‍♂️teria um ☝️único🤏 centavo 🪙 em meu bolso👖👖, pois teria gasto🛍️💱 o dinheiro 💰 comprando 🎁 uma Lamborghini 🏎️ cheia de Tortuguitas 🐢🐢🐢 e patinhos🦆🦆🦆 para minha ✊✊ garota 👧🏽🥰",
                "oi ;-; eu tava vendo seu perfil.e te achei muito fofa rsrs 📷 queria perguntar se você quer ser minhq amiga '-' (talvez futura esposa) ksksks mas se nao quiser responder nao precisa. já estou acustumado;-;",
                "Parece meu rosto né?\nMas é uma máscara\nParece que to feliz né?\nSo to fingindo",
                "Tomando coragem para amar a pessoa q não amar oq amar aí eu pedir em namora aí nois mata a polícia sonhoooh ❤😘\nPostah no status do zap e me menciona quem gostou 😉😜",
                "⚠️ UM AVISO AVISAMOS QUE POR FALTA DE AVISO NÃO AVISAREMOS O AVISO QUE ERA PRA AVISAR, PORTANTO FIQUEM AVISADOS DESTE AVISO QUE AVISAMOS, AVISEM PARA OUTRAS PESSOAS SOBRE O AVISO PARA QUE TODOS FIQUEM AVISADOS,  TÁ  AVISADO QLQ DÚVIDA ME AVISEM⚠️",
                "POWPAPAPUPUPAPUL🎉🎉🎉🎊🎊FIIILLLPUUUUUPOWPOWPOWPOW🎉🎉🎉🎆🎆🎆🎆🎆PAPAPAPATRATRATRATRATRA🎉🎉🎉🎉🎉🎊🎊🎊🎊🎆🎆🎆🎆🎆TATATATATAFIIIIILLLFIIIIILLLLFIIIIIIILLLPOOOWWWWWW🎆🎆🎉🎉🎉🎉🎊🎊🎊🎊PAPAPARARARARATA🎆🎆🎆🎉🎉🎉🎊🎊🎊FIIIIIIIIILLLLPOOOOOWTATATATATATARRARA🎆🎆🎆🎊🎊🎊🎉🎉🎉",
                "Oi\n😎\nVocê tem whemts apple😎",
                "blz mais eu já disse para vc :que:ekhfjdhsksfgdhjsvisghulvlgscgseygvisuyvgusdhfyhsi 8  ywgfyefyets8fyeyfguetw 803y f89 e78ftw78et f7t w87 trfwe87t r t3fyewfhuisgvu ergf re,ause zrge7s tfea7rt fer8 tf7at efkerygfuwrtgfiakrwygvi6wrgfa86etf we ftgwekftiewyagrekygfi 6rf t6ew tf6 ewt+",
                "ARCANE É UMA PROPAGANDA MANIPULADORA DE NOSSOS JOVENS PARA VICIA-LOS EM JOGOS HEREGES COMO LEAGUE OF LEGENDS, PIOR QUE O VICIO DA SODOMIA, POR FAVOR NAO DEIXEM SEUS FILHOS ASSISTIREM ESSE TIPO DE CONTEUDO E NAO OS DEIXEM JOGAR LEAGUE OF LEGENDS (LOL)",
                "Halloween chegando, quem quiser me assustar, eu tenho medo de whisky",
                "Me desbloqueia vida, eu mudei",
                "Como confiar no amor, se o amor dos outros fica me mandando msg 🤡",
                "😲 imagina 👈🏻💭 nessa 🥳 idade 👄 o 🌹 que 🤸🏻‍♀️ aconteceu 💥 comigo 😱 resolvi 😌 me 🙋🏻‍♀️ apaixonar 💖 por 😳 alguém 🗣️ que 👀 não ❌ consigo 😩 ironia 🤷🏻‍♀️ do 🥱 destino 🏃🏻‍♀️ que 🌬️ só 🤲🏻 quer 🧐 brincar 🤹🏻‍♀️ com a 💢 gente 🚫 não 😠 sei 🤓 lidar 👾 com 👥 isso ⚔️ tá ✋🏻 tudo 🤔 diferente",
                "Minha cara : 😡\nMinha personalidade: 🤪",
                "Vc viu 😧 a briga 🙈 que teve 😱 na frente 😮 da sua casa 🏠 ontem? Não😦 viu? 5 anjos 👼🏽👼🏾👼🏻👼🏽👼🏾 lutando para te dar o garden de volta 😱 se você crê 🙏🏼 👍🏻 🙏🏼 🙏🏼 🙏🏼 🙏🏻 🙏🏼 repasse e veja algo incrível acontecer 🙌🏼🙏🏻.",
                "GENTE NAO É COPYPASTA, hoje à meia-noite irá ter um teste nuclear aqui no Brasil esse negócio do garden cair é apenas uma distração para que nós não soubéssemos dessa O garden volto mas nao do jeito que achamos. prestemos atenção no que realmente vai acontecer  QUE DEUS TENHA PIEDADE😟!",
                "Vc atrevessaria essa ponte agui com esse. Jaquere raivoso. Gordinho. Um bufu. faminto louco pra te papar. vc teria coragem de atravessar essa ponte de madeira podre mofada fodida um lixo cheia de cupim vc teria coragem?",
                "NUBANK: Compra APROVADA. Ingresso do Rock in Rio para o dia da Juliette no palco Nordeste no valor de R$ 272,50 às 23:49. O ingresso acompanha um saco de farinha, leve o seu preconceito para engolir.",
                "O LOBISOMEM PIDÃO\ntoda noite ele passa na praça pedindo farinha na cumbuca. Pede pede pede que so a porra enche o saco esse bicho pidão... eis o relato:\n- Me dê!\n- Sai pra lá pidão!",
                "rapaz 🤔 nem se eu 🗂️ juntasse todas as copypastas 📂📁 de elogio que existe 🌍✨🪐🌌 eu ia conseguir descrever 📝🥰🙏o quao LINDA🌟✨😍 você é 🥳😘 abençoou meu dia 🌄⛅ nmrl prfta 🥴💗💖💘 linda demais 💭💕",
                "Voltou para o lobby, foi de base, não tankou, foi de dormes, foi de berço, foi de ralo, cinzou, lobbyou, deu b, tomou ban da vida, deu respawn em um lugar melhor, foi para o Gulag, F.",
                "Pai = Cansado\nMãe = Careca\nLento = Rápido\nTonto = Trouxa\nPato = Chato\nIdiota = Otário\nQuem = Alguém\nO que = É você\nFala o seu desejo = Levanta o rabo do gato e dá um beijo",
                "E vc tá endauldie agrummt?E vc tá endauldilie agrummt og😜as Riobousssmigt tra",
                "Odeio Gente Falsa Que na Frente da fente é uma coisa com a gente Por de Traz Fica Falando Da Gente De falar Por a Frente fala por de traz",
                "Sextou com s de saudades do ex",
                "Esquerdista 🍁 Evangelica 🙏 Feminista 🚺  Homofobica 🏳‍🌈 Independente 💪 Bolsonaro2k18 🇧🇷",
                "se viro profesora sua mocreia lacraia malasafraia desalmada ordinaria fedida catingueira",
                "Ei machão😡😡😡😡🤬🤬, acha bonito enganar mulher 👩👩👩né…🤬 se pagar de gostosão😋😋🤬 né? Jogadorzinho de lol 🤮🤮🤮🤮🥶 sem caráter, aprende a respeitar as mulheres 🤬🤬😡👩👩 viu, acho bom 😁😁, chamar uma mulher 👩👩👩 pra sair 🏃🏃🏃 e ficar com outra 👱‍♀️👱‍♀️👱‍♀️👱‍♀️, tu tem vergonha 🙈🙈 na cara 😳😳 não 😡😡😡😡? Tem caráter não 😡🤯🤬? Tu é um molequezinho 👶👶👶👶 sem caráter👺👺💢! Tu fez uma coisa mais ridícula 😒😒😒😒, tu quer ser homem👨‍🦰👨‍🦰👨‍🦰👨‍🎓👨‍🎓👨‍🎤👨‍🏫? Começa a agir como um🤸‍♂️🤸‍♂️🤸‍♂️🤸‍♂️, seu moleque👼👼👼…",
                "POR FAVOR NAO COMPRE O LANCHE DO BTS DO MCDONALDS SE VOCE NAO FOR ARMY. VOCE VAI ESTAR IMPEDINDO OS VERDADEIROS FÃS DO BTS QUE ESPERARAM MESES PARA PODER COMER. COMER OS MOLHOS SEM ENTENDER O SIGNIFICADO É LITERALMENTE APROPRIAÇÃO CULTURAL E NÃO ESTA TUDO BEM  : )",
                "se viro profesora sua mocreia lacraia malasafraia desalmada ordinaria fedida catingueira",
                "olha o pronome neutro 👻👻 olha a lacração 👻👻 olha os gay andando na rua 👻👻👻 olha o personagem preto 👻👻👻 buuuu olha a agenda woke 👻👻",
                "Bom🥺dia🥺gente🥺eu🥺estou🥺querendo🥺uma🥺coisa🥺mas🥺to🥺com🥺vergonha🥺de🥺pedir🥺",
                "gente, acabei de receber um email com uma intimação judicial e eu fiquei ??? Aparentemente to sendo processado e preciso comparecer amanhã as 16h no fórum com um advogado pq me denunciaram por ser o sonho de toda sogra",
                "BARK 🤬🐗WOOF 🐒BARK 🐕‍🦺RUFF 😡🐺BARK 🐻BARK 🤬🦊BARK 🐕BARK 🐻WOOF 🐕WOOF 🦊RUFF 🐂RUFF🦮 GRRRRR🐕‍🦺 BARK🐶 BARK 🤬🦁WOOF😡🙊 WOOF 🦁GRRRR🐶 RUFF 🐴RUFF🐗 BARK🐺 😡WOOF🦮 RUFF🐕 GRRRR🐶 BARK 🐕‍🦺BARK BARK 🤬🐗WOOF 🐒BARK 🐕‍🦺RUFF 😡🐺BARK 🐻BARK 🤬🦊BARK 🐕BARK",
                "nem hetero\nnem homossexual\neu pertenço ao mundo animal\nmeus pronomes?\njagua/tirica",
                "👑*-AtenÇão 😱😱To Vendo Uma Lindeza😍Uma Perfeição😍😘Na Minha Frente😁😍😘 Vc Chego Ao LiiMitte ⚠️⚠️🚧 De Liindezha 🎥📹📷📷💝😍😘❤️💘 Ir PerfeiÇãoO 😍😘😊❤️💚-Miin-Descullpa 👆👆 Maiis Me Enprestta Un Ocullos 😎😎 Porque Sua Belleza Incomodaa Muita Gente❤️💚💞💕😌😌🍃IluMinar Maiis Que O Sol..😍😍❤️💞💓🍃😘😍😍Chega Meu Celular Travo📱📱📱De Tanta Beleza...😍😍😍😍....🚧🚦 Parou o Face.. Kaundo Vi Essa Foto,, Sllk Essa Ft Ta a Sensação,, Do Meu Face 👇👇👇👇👇👇👇👇😍💘😎...😱😱😱 A Melhor Ft Q Ja Vi Ate Agora Sem Mentira...😍.....Toca Fogo Na Inveja Que Essa Foto Ta a Mais Lindah Das Perffeiccoes...😍😍😍",
                "se viro profesora sua mocreia lacraia malasafraia desalmada ordinaria fedida catingueira",
                "😍- Princesa 😍👊♡ 👏😱❤️ tão Lindaa ❤️😱👏CHUPA DISNEY ESSA PRINCESA VOCÊS NÃO TEM 👊 ",
                "Para tudu😱😱🖐🖐 olha essa princesa 👑✔️a disney vai a falensia🔝✔️a mais gata😻✔️a mais top🔝😍✔️plincesaah✔️divaah💜💚💙👑✔️ seducao 👑✔️taum perfeitah💕👏✔️taum rainha👑😍✔️taum lindah😻✔️meu face parou so pra te ver😍 Ta isperanu oq pra mebja 😍😘❤️🔝👌 sorriahh, alguein pode se apaixonahh pelo seu sorrisuhh😍🔝💘To digitando com os pé pq ca mão to aplaudindo",
                "Vamos falar de coisa boa,chegou a filmadora mais vendida do Brasil , é a Tekpix Ela grava,filma,é mp3,tem saída de áudio e de tv . É a filmadora que faltava na sua casa. E ta vendo esta parcelinha aqui em baixo de R$110,00 mensais,acabou de cair para 99,00 é isso mesmo 99,00.",
                "quem é Neymar?\nem geografia, meu mundo.\nem história, meu rei.\nem matemática, minha solução.\nem biologia, meu medicamento.\nem mitologia, meu deus.\nem astronomia, meu universo.\nPara o cego, é a luz.\nPara o faminto, é o pão.\nPara o sedento, é a fonte de água viva.",
                "alô📞☎️ alô alô📞 alô alô📞 alô alouuu alouu📞❓ alouuu alouu📞❓ alouu aloUuUu alouUUUuuUuU📞⁉️ aal o U😂😂  ALOOOOOO📞☎️ ALOOUuUuUUuUULUULULULU LULULULULU",
                "se tem uma menina👩🏻‍🦰 olhando essa mensagem💌🥺 por favor namora comigo 😭😭 eu nunca namorei desde quando eu nasci 👶🏾 eu tenho 1️⃣9️⃣ anos e nunca namorei 😭😭😭 meus amigos👨‍👨‍👦 ficam me zoando na escola 🏬 porque eu nunca namorei pufavo namora comigo pufavoo 🥺😭😭",
                "EU ARREPENDIDO POR TER VOTADO 17??\nMEUAMIGO EU APERTO 17 TODO DIA NO ELEVADOR NO IMPULSO, MORO NO TERCEIRO ANDAR\nCOMO COMIDA FRIA PQ APERTO 17 NO MICROONDAS\nCOMPREI UMA REPLICA DA URNA SÓ PRA FICAR APERTANDO 17",
                "Estou offline\nNao estou usandi whats app\nEstou sem sinao\nNao estou usano nada de redes sociais \nNao me encham o saco",
                "Minha vacina é a BOLSOVAC\n💉 1ª dose foi em 2018\n💉 2ª dose será em 2022\nJAIRMECTINA\nAZITROMESSIAS\nHIDROXICLOROMITO\n👉🏻 eficaz contra o abuso das autoridades, contra a corrupção e contra o comunismo e o terrorismo psicológico !!!\n#Bolsonaro2022 😎💪🏻🇧🇷",
                "Vocês acham que a Peppa Pig é só um desenho infantil? Acordem! Peppa Pig na verdade é uma trama secreta dos Illuminati para manipular nossas crianças. O triângulo que aparece nos episódios não é coincidência, é o símbolo da Nova Ordem Mundial",
                "eu sei que alguns de vocês podem amar o jungkook e tudo mais, mas vocês têm que entender que eu sou a pessoa que mais ama ele na terra, sabem? sinto muito e espero que cheguem onde cheguei, mas sou eu. eu sou a maior fã dele que existe. ninguém ama mais o jungkook do que eu",
                "Eu lembro da época em que eu queria ter uma bicicleta, eu tentei pedir pra deus me dar uma, mas eu sei que deus não trabalha dessa forma então eu roubei uma bicicleta e pedi perdão em seguida.",
                "E na chamada da escola, a professora:\nSapo?\n- Presente!\nCachorro?\n- Presente! \nGato?\n- Presente!\nJumento?\n(Ñ respondeu pq tava lendo)\n Galinha?\n- Presente!\n Macaco?\n- Presente!\n e o jumento lendo...\nPinguim?\n- Presente!\nPorco?\n- Presente!\n e o jumento ainda lendo",
                "⚠️ATENÇÃO⚠️\neu sou baixinha\nisso mesmo que vc leu 😤 eu 👉sou baixinha👈\ndiria que minúscula 😜 quase nao alcanço a maçaneta 😂",
                "*aponta arma*\n- quem são elas\n- twice\n- que que elas são\n- o maior grupo da nação\n- quem é a membro mais fofa\n- a momo\n- errado, são todas agora dança\n*dançando* 🕺🕺🕺",
                "OLA limda bjss sabe vc ELINDA GOSTARIA SE jair bolsonaro 👍"
            ])
            mudar_bio_usuario(user_id, bio_nova, chat_id)

        elif chance == 5:
            # Mudar o favorito para outra carta aleatória
            mudar_favorito_usuario(user_id,chat_id)

        elif chance == 6:
            # Bloquear pesca por um tempo aleatório entre 5 e 30 minutos
            duracao_bloqueio = random.randint(2, 30)
            bloquear_pesca_usuario(user_id, duracao_bloqueio)

        elif chance == 7:
            # Bloquear o envio de comandos por um tempo aleatório entre 5 e 30 minutos
            duracao_bloqueio_comandos = random.randint(2, 30)
            bloquear_comandos_usuario(user_id, duracao_bloqueio_comandos,chat_id)
            
        elif chance == 8:
            # Embaralhar as mensagens
            bot.send_message(chat_id, embaralhar_mensagem("🐯 Olá! Você tem disponível: X iscas. Boa pesca!"))

        elif chance == 9:
            # Pega-pega (passar uma praga para outros usuários)
            bot.send_message(chat_id, f"👹 Travessura! Você foi amaldiçoado, use +praga para passar a praga para outra pessoa.")
            iniciar_pega_pega(user_id)

        elif chance == 10:
            # Nada acontece
            bot.send_message(chat_id, "🎁 Gostosura! Ah, não, era uma travessura! Não há recompensa para você dessa vez.")

        elif chance == 11:
            # Jogo da velha com um fantasma
            bot.send_message(chat_id, "👻 Um fantasma te desafiou para um jogo da velha! Se você ganhar, a travessura será evitada.")
            iniciar_jogo_da_velha(chat_id)

        elif chance == 12:
            # Labirinto com um fantasma
            bot.send_message(chat_id, "👻 Um fantasma te desafiou para escapar de um labirinto!")
            iniciar_labirinto(user_id,chat_id)

        elif chance == 13:
            # Travessura acontece com todos os que mandaram mensagem no grupo nos últimos 10 minutos
            travessura_grupal(user_id,chat_id)

        elif chance == 14:
            # Troca de ordem nos comandos de troca
            troca_invertida(user_id,chat_id)

        elif chance == 15:
            # Bloquear raspadinha por 1 dia
            bloquear_acao(user_id, "raspadinha", 1440)
            bot.send_message(chat_id, "🎰 Travessura! Você está bloqueado de jogar raspadinha por 1 dia.")

        elif chance == 16:
                        # Registrar a travessura na tabela
            try:
                conn, cursor = conectar_banco_dados()
        
                # Definir o tempo de duração da travessura (por exemplo, 1 hora)
                fim_travessura = datetime.now() + timedelta(minutes=10)
        
                # Inserir ou atualizar a travessura no banco de dados
                cursor.execute("""
                    INSERT INTO travessuras (id_usuario, tipo_travessura, fim_travessura)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE tipo_travessura = VALUES(tipo_travessura), fim_travessura = VALUES(fim_travessura)
                """, (user_id, 'sombra_rouba_cenouras', fim_travessura))
                conn.commit()
        
            except Exception as e:
                print(f"Erro ao registrar travessura de categoria errada: {e}")
        
            finally:
                fechar_conexao(cursor, conn)
            # Sombra rouba cenouras a cada 10 segundos
            iniciar_sombra_roubo_cenouras(user_id)
            bot.send_message(chat_id, "🕯️ Travessura! Uma sombra está roubando suas cenouras a cada 10 segundos. Use +exorcizar para parar!")

        elif chance == 17:
            # Alucinação: mensagens incompletas
            ativar_travessura_embaralhamento(chat_id, user_id)
            
        elif chance == 18:
            # Registrar a travessura na tabela
            try:
                conn, cursor = conectar_banco_dados()
        
                # Definir o tempo de duração da travessura (por exemplo, 1 hora)
                fim_travessura = datetime.now() + timedelta(hours=1)
        
                # Inserir ou atualizar a travessura no banco de dados
                cursor.execute("""
                    INSERT INTO travessuras (id_usuario, tipo_travessura, fim_travessura)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE tipo_travessura = VALUES(tipo_travessura), fim_travessura = VALUES(fim_travessura)
                """, (user_id, 'categoria_errada', fim_travessura))
                conn.commit()
        
                bot.send_message(chat_id, "🎃 Travessura! Suas cartas estão com as categorias erradas temporariamente.")
        
            except Exception as e:
                print(f"Erro ao registrar travessura de categoria errada: {e}")
        
            finally:
                fechar_conexao(cursor, conn)

        elif chance == 19:
            # Carta aleatória do inventário será apagada
            apagar_carta_aleatoria(user_id, chat_id)
            bot.send_message(chat_id, "💀 Travessura! Uma carta aleatória foi apagada do seu inventário.")

    except Exception as e:
        print(f"DEBUG: Erro ao realizar travessura para o usuário {user_id}: {e}")
        traceback.print_exc()
        bot.send_message(user_id, "Ocorreu um erro ao realizar a travessura.")


@bot.message_handler(commands=['halloween'])
def handle_halloween(message):
    user_id = message.from_user.id  # Obtém o ID do usuário
    chat_id = message.chat.id

    # Verificar se o usuário já tem um jogo da velha ativo
    if user_id in jogos_da_velha:
        bot.send_message(chat_id, "👻 Você já tem um jogo da velha em andamento! Complete o jogo atual antes de iniciar outra ação.")
        print(f"DEBUG: Comando /halloween bloqueado para o usuário {user_id} porque há um jogo da velha ativo.")
        return

    print(f"DEBUG: Comando /halloween acionado pelo usuário {user_id}")
    chance = random.random()  # Gera um número entre 0 e 1
    print(f"DEBUG: Chance sorteada para gostosura ou travessura: {chance}")

    if chance < 0.5:
        print(f"DEBUG: Executando gostosura para o usuário {user_id}")
        realizar_halloween_gostosura(user_id, chat_id)  # Executa uma das funções de gostosura
    else:
        print(f"DEBUG: Executando travessura para o usuário {user_id}")
        realizar_halloween_travessura(user_id, chat_id)  # Executa uma das funções de travessura



@bot.callback_query_handler(func=lambda call: call.data.startswith("pronomes_"))
def pronomes(call):
    atualizar_pronomes(call)
    
@bot.callback_query_handler(func=lambda call: call.data.startswith("bpronomes_"))
def bpronomes(call):
    mostrar_opcoes_pronome(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("escolha_porta_"))
def callback_escolha_porta(call):
    user_id = int(call.data.split("_")[-1])
    porta_escolhida = call.data.split("_")[2]

    # Recuperar os prêmios salvos para esse jogador
    premios = recuperar_premios_escolha(user_id)

    # Identificar qual prêmio foi escolhido
    if porta_escolhida == "1":
        premio = premios[0]
    elif porta_escolhida == "2":
        premio = premios[1]
    elif porta_escolhida == "3":
        premio = premios[2]

    # Enviar a recompensa para o jogador
    bot.send_message(user_id, f"🎉 Parabéns! Você escolheu a {porta_escolhida} e ganhou: {premio}")

    # Processar o prêmio (cenouras, VIP, cartas etc.)
    processar_premio(user_id, premio)

@bot.message_handler(commands=['jogodavelha'])
def handle_jogo_da_velha(message):
    iniciar_jogo(bot, message)

@bot.callback_query_handler(func=lambda call: call.data.isdigit())
def handle_jogada(call):
    jogador_fazer_jogada(bot, call)

# Função principal de troca
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

        # Verificação se a travessura "troca invertida" está ativa
        if verificar_travessura_ativa(eu, 'troca_invertida'):
            minhacarta, suacarta = suacarta, minhacarta  # Inverte as cartas na troca
            bot.send_message(chat_id, "🔮 A bruxa lançou sua maldição! 🕸️ Seus instintos se confundem e agora a ordem das cartas na troca foi invertida... boa sorte quebrando o feitiço! 🕯️")

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

# Função para verificar se a travessura está ativa
def verificar_travessura_ativa(id_usuario, tipo_travessura):
    conn, cursor = conectar_banco_dados()
    try:
        query = """
            SELECT fim_travessura FROM travessuras
            WHERE id_usuario = %s AND tipo_travessura = %s AND fim_travessura > NOW()
        """
        cursor.execute(query, (id_usuario, tipo_travessura))
        resultado = cursor.fetchone()
        return resultado is not None  # Retorna True se a travessura está ativa
    except Exception as e:
        print(f"Erro ao verificar travessura: {e}")
        return False
    finally:
        fechar_conexao(cursor, conn)

# Função que aplica a travessura e bloqueia o comando de raspadinha por 1 dia
def bloquear_raspadinha(user_id):
    try:
        # Conectar ao banco de dados
        conn, cursor = conectar_banco_dados()

        # Calcular o tempo de bloqueio (1 dia)
        fim_bloqueio = datetime.now() + timedelta(hours=24)

        # Inserir o bloqueio na tabela `travessuras`
        cursor.execute("""
            INSERT INTO travessuras (id_usuario, tipo_travessura, fim_travessura)
            VALUES (%s, 'bloqueio_raspadinha', %s)
            ON DUPLICATE KEY UPDATE fim_travessura = VALUES(fim_travessura)
        """, (user_id, fim_bloqueio))
        conn.commit()

        # Enviar mensagem informando o bloqueio
        bot.send_message(user_id, "👻 Você foi amaldiçoado! O comando de raspadinha está bloqueado por 24 horas.")

    except mysql.connector.Error as err:
        print(f"Erro ao aplicar o bloqueio de raspadinha: {err}")
    finally:
        fechar_conexao(cursor, conn)

# Função que verifica se o usuário está bloqueado ao tentar usar o comando raspadinha
def verificar_bloqueio_raspadinha(user_id):
    try:
        # Conectar ao banco de dados
        conn, cursor = conectar_banco_dados()

        # Consultar a tabela `travessuras` para ver se o bloqueio ainda está ativo
        cursor.execute("""
            SELECT fim_travessura FROM travessuras
            WHERE id_usuario = %s AND tipo_travessura = 'bloqueio_raspadinha'
        """, (user_id,))
        resultado = cursor.fetchone()

        if resultado:
            fim_bloqueio = resultado[0]
            tempo_restante = (fim_bloqueio - datetime.now()).total_seconds()
            if tempo_restante > 0:
                horas_restantes = int(tempo_restante // 3600)
                minutos_restantes = int((tempo_restante % 3600) // 60)
                return True, horas_restantes, minutos_restantes

            # Se o tempo expirou, remover a travessura
            cursor.execute("""
                DELETE FROM travessuras WHERE id_usuario = %s AND tipo_travessura = 'bloqueio_raspadinha'
            """, (user_id,))
            conn.commit()

        return False, None, None

    except mysql.connector.Error as err:
        print(f"Erro ao verificar bloqueio de raspadinha: {err}")
        return False, None, None
    finally:
        fechar_conexao(cursor, conn)
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

@bot.message_handler(commands=['tag','tags'])
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
    handle_set_fav(message)

@bot.message_handler(commands=['usuario'])
def obter_username_por_comando(message):
    from eu import handle_obter_username
    handle_obter_username(message)

@bot.message_handler(commands=['eu'])
def me_command(message):
    handle_me_command(message)
    
@bot.message_handler(commands=['gperfil'])
def gperfil_command(message):
    handle_gperfil_command(message)

@bot.message_handler(commands=['config'])
def config_command(message):
    handle_config(message)
    
@bot.message_handler(commands=['delpage'])
def del_page(message):
    try:
        user_id = message.from_user.id
        params = message.text.split(' ', 1)[1:]
        if len(params) < 1:
            bot.send_message(message.chat.id, "Uso: /delpage <número_da_página>")
            return

        page_number = int(params[0])

        conn, cursor = conectar_banco_dados()

        cursor.execute("SELECT data, anotacao FROM anotacoes WHERE id_usuario = %s ORDER BY data DESC", (user_id,))
        anotacoes = cursor.fetchall()

        if not anotacoes or page_number < 1 or page_number > len(anotacoes):
            bot.send_message(message.chat.id, "Número de página inválido.")
            return

        data, anotacao = anotacoes[page_number - 1]

        response = f"Mabigarden, dia {data.strftime('%d/%m/%Y')}\n\n<i>\"{anotacao}\"</i>\n\nDeseja deletar esta página?"

        markup = types.InlineKeyboardMarkup()
        confirm_button = types.InlineKeyboardButton("✔️ Confirmar", callback_data=f"confirmar_delete_{page_number}")
        cancel_button = types.InlineKeyboardButton("❌ Cancelar", callback_data=f"cancelar_delete_{page_number}")
        markup.add(confirm_button, cancel_button)

        bot.send_message(message.chat.id, response, reply_markup=markup)

    except Exception as e:
        bot.send_message(message.chat.id, "Erro ao processar o comando de deletar página.")
        print(f"Erro ao deletar página: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirmar_delete_'))
def confirmar_delete(call):
    try:
        user_id = call.from_user.id
        page_number = int(call.data.split('_')[-1])

        conn, cursor = conectar_banco_dados()

        cursor.execute("SELECT id FROM anotacoes WHERE id_usuario = %s ORDER BY data DESC LIMIT 1 OFFSET %s", (user_id, page_number - 1))
        anotacao_id = cursor.fetchone()

        if anotacao_id:
            cursor.execute("DELETE FROM anotacoes WHERE id = %s", (anotacao_id[0],))
            conn.commit()
            bot.edit_message_text("Página deletada com sucesso.", call.message.chat.id, call.message.message_id)
        else:
            bot.edit_message_text("Erro ao deletar a página. Página não encontrada.", call.message.chat.id, call.message.message_id)

    except Exception as e:
        bot.send_message(call.message.chat.id, "Erro ao deletar a página.")
        print(f"Erro ao deletar página: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('cancelar_delete_'))
def cancelar_delete(call):
    bot.edit_message_text("Ação cancelada.", call.message.chat.id, call.message.message_id)

@bot.message_handler(commands=['editdiary'])
def handle_edit_diary(message):
    edit_diary(message, bot)

@bot.callback_query_handler(func=lambda call: call.data == 'edit_note')
def handle_edit_note_callback(call):
    bot.send_message(call.message.chat.id, "Envie a nova anotação para editar.")
    bot.register_next_step_handler(call.message, salvar_ou_editar_anotacao, call.from_user.id, date.today(), bot)

@bot.callback_query_handler(func=lambda call: call.data == 'cancel_edit')
def handle_cancel_edit_callback(call):
    cancelar_edicao(call, bot)
def roubar_carta(user_id, chat_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Verificar se o jogador tem cartas no inventário
        cursor.execute("SELECT id_personagem, nome FROM inventario WHERE id_usuario = %s", (user_id,))
        cartas = cursor.fetchall()

        if not cartas:
            bot.send_message(chat_id, "👻 Você não tem cartas no inventário para serem roubadas.")
            return

        # Selecionar uma carta aleatória para roubar
        carta_roubada = random.choice(cartas)
        id_carta, nome_carta = carta_roubada

        # Gerar a palavra que o jogador deve digitar
        palavra_gerada = gerar_palavra_aleatoria()

        # Avisar o jogador e dar a chance de impedir o roubo
        bot.send_message(chat_id, f"⚠️ Um demônio está tentando roubar a carta '{nome_carta}'! Escreva a palavra '{palavra_gerada}' em 10 segundos para impedir o roubo!")

        # Configurar o temporizador de 10 segundos
        bot.register_next_step_handler_by_chat_id(chat_id, processar_resposta_palavra, user_id, id_carta, palavra_gerada, nome_carta)
        bot.send_message(chat_id, "Você tem 10 segundos para responder...")

    except Exception as e:
        print(f"Erro ao tentar roubar carta: {e}")
    finally:
        fechar_conexao(cursor, conn)
import time
import random
import string

def gerar_palavra_aleatoria(tamanho=8):
    letras = string.ascii_lowercase  # Gera uma palavra usando letras minúsculas
    return ''.join(random.choice(letras) for i in range(tamanho))

def processar_resposta_palavra(message, user_id, id_carta, palavra_gerada, nome_carta):
    resposta = message.text.lower().strip()
    chat_id = message.chat.id

    # Verificar se a palavra digitada é a correta
    if resposta == palavra_gerada:
        bot.send_message(chat_id, f"🎉 Parabéns! Você impediu o demônio de roubar a carta '{nome_carta}'!")
    else:
        # Caso a resposta esteja errada ou o tempo limite seja excedido, remover a carta
        try:
            conn, cursor = conectar_banco_dados()
            cursor.execute("DELETE FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (user_id, id_carta))
            conn.commit()
            bot.send_message(chat_id, f"👻 O demônio roubou a carta '{nome_carta}' do seu inventário!")
        except Exception as e:
            print(f"Erro ao remover a carta roubada: {e}")
        finally:
            fechar_conexao(cursor, conn)


# Função para truncar aleatoriamente nomes de subcategorias
def truncar_texto(texto, truncar_percent=0.5):
    # Separar tags HTML do texto visível
    partes = re.split(r'(<[^>]+>)', texto)  # Divide o texto preservando as tags
    texto_embaralhado = ""

    for parte in partes:
        if parte.startswith("<") and parte.endswith(">"):
            # Se é uma tag HTML, preserve sem alterar
            texto_embaralhado += parte
        else:
            # Trunca exatamente a metade da parte do texto visível
            metade = len(parte) // 2
            texto_embaralhado += parte[:metade]  # Pega somente a primeira metade


    return texto_embaralhado

@bot.message_handler(commands=['gnome'])
def handle_gnome(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    # Verificar se a travessura de embaralhamento está ativa
    embaralhamento_ativo = verificar_travessura_ativa(user_id)
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

        # Verificar se a travessura de categoria errada está ativa
        if verificar_categoria_errada(user_id):
            conn, cursor = conectar_banco_dados()
            cursor.execute("SELECT subcategoria FROM personagens ORDER BY RAND() LIMIT 1")
            categoria_errada = cursor.fetchone()[0]
            fechar_conexao(cursor, conn)
            categoria = categoria_errada

        # Salvar os resultados no dicionário global para navegação posterior
        globals.resultados_gnome[user_id] = truncar_texto(resultados_personagens) if embaralhamento_ativo else resultados_personagens

        # Exibir a primeira carta
        enviar_primeira_carta(chat_id, user_id, resultados_personagens, 0)

    except Exception as e:
        print(f"Erro: {e}")
    finally:
        fechar_conexao(cursor, conn)

def verificar_categoria_errada(user_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Verificar se a travessura está ativa para o usuário
        cursor.execute("""
            SELECT fim_travessura FROM travessuras
            WHERE id_usuario = %s AND tipo_travessura = 'categoria_errada'
        """, (user_id,))
        resultado = cursor.fetchone()

        if resultado:
            fim_travessura = resultado[0]
            if datetime.now() < fim_travessura:  # Travessura ainda ativa
                return True
        
        return False
    
    except Exception as e:
        print(f"Erro ao verificar categoria errada: {e}")
        return False
    finally:
        fechar_conexao(cursor, conn)

def enviar_primeira_carta(chat_id, user_id, resultados_personagens, index):
    id_personagem, nome, subcategoria, categoria, quantidade_usuario, imagem_url = resultados_personagens[index]

    # Verificar se a travessura de categoria errada está ativa
    if verificar_categoria_errada(user_id):
        # Selecionar uma categoria incorreta aleatoriamente
        conn, cursor = conectar_banco_dados()
        cursor.execute("SELECT subcategoria FROM personagens ORDER BY RAND() LIMIT 1")
        categoria_errada = cursor.fetchone()[0]
        fechar_conexao(cursor, conn)
        subcategoria = categoria_errada  # Substituir a categoria correta pela errada

    # Criação da mensagem para a carta
    mensagem = f"💌 | Personagem:\n\n<code>{id_personagem}</code> • {nome}\nde {subcategoria}\n\n"
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

    # Enviar a mensagem com a carta
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


# Função para editar a carta com navegação
def editar_carta(chat_id, user_id, resultados_personagens, index, message_id):
    id_personagem, nome, subcategoria, categoria, quantidade_usuario, imagem_url = resultados_personagens[index]

    # Verificar se a travessura de categoria errada está ativa
    if verificar_categoria_errada(user_id):
        conn, cursor = conectar_banco_dados()
        cursor.execute("SELECT subcategoria FROM personagens ORDER BY RAND() LIMIT 1")
        categoria_errada = cursor.fetchone()[0]
        fechar_conexao(cursor, conn)
        subcategoria = categoria_errada  # Substituir a categoria correta pela errada

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
            bot.edit_message_media(
                media=types.InputMediaAnimation(media=imagem_url, caption=mensagem, parse_mode="HTML"),
                chat_id=chat_id, message_id=message_id, reply_markup=keyboard
            )
        elif imagem_url.lower().endswith(".mp4"):
            bot.edit_message_media(
                media=types.InputMediaVideo(media=imagem_url, caption=mensagem, parse_mode="HTML"),
                chat_id=chat_id, message_id=message_id, reply_markup=keyboard
            )
        elif imagem_url.lower().endswith((".jpeg", ".jpg", ".png")):
            bot.edit_message_media(
                media=types.InputMediaPhoto(media=imagem_url, caption=mensagem, parse_mode="HTML"),
                chat_id=chat_id, message_id=message_id, reply_markup=keyboard
            )
        else:
            bot.edit_message_text(mensagem, chat_id=chat_id, message_id=message_id, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        print(f"Erro ao editar a mídia: {e}")
        bot.edit_message_text(mensagem, chat_id=chat_id, message_id=message_id, reply_markup=keyboard, parse_mode="HTML")

# Função de callback para a navegação
@bot.callback_query_handler(func=lambda call: call.data.startswith('gnome_'))
def callback_gnome_navigation(call):
    try:
        data = call.data.split('_')
        action = data[1]  # 'prev' ou 'next'
        index = int(data[2])
        user_id = int(data[3])

        # Recuperar os resultados da pesquisa original
        resultados_personagens = globals.resultados_gnome.get(user_id, [])

        if resultados_personagens:
            # Editar a mensagem existente com a nova carta
            editar_carta(call.message.chat.id, user_id, resultados_personagens, index, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "Não foi possível encontrar os resultados. Tente novamente.")
    except Exception as e:
        bot.answer_callback_query(call.id, "Erro ao processar a navegação.")
        print(f"Erro ao processar callback de navegação: {e}")
        
# Função para criar a navegação com botões de "Anterior" e "Próxima"
def create_navigation_markup(pagina_atual, total_paginas):
    markup = types.InlineKeyboardMarkup(row_width=2)  # Garantir que os botões fiquem na mesma linha
    
    if pagina_atual == 1:  # Se estiver na primeira página
        prev_button = types.InlineKeyboardButton("⬅️", callback_data=f"gnomes_prev_{total_paginas}")  # Volta para a última página
        next_button = types.InlineKeyboardButton("➡️", callback_data=f"gnomes_next_{pagina_atual+1}")  # Vai para a próxima página
    elif pagina_atual == total_paginas:  # Se estiver na última página
        prev_button = types.InlineKeyboardButton("⬅️", callback_data=f"gnomes_prev_{pagina_atual-1}")  # Volta para a página anterior
        next_button = types.InlineKeyboardButton("➡️", callback_data=f"gnomes_next_1")  # Vai para a primeira página
    else:  # Qualquer outra página no meio
        prev_button = types.InlineKeyboardButton("⬅️", callback_data=f"gnomes_prev_{pagina_atual-1}")  # Volta para a página anterior
        next_button = types.InlineKeyboardButton("➡️", callback_data=f"gnomes_next_{pagina_atual+1}")  # Vai para a próxima página

    # Adiciona os botões na mesma linha
    markup.add(prev_button, next_button)
    
    return markup


# Função para salvar o estado dos resultados de pesquisa do usuário
def save_state(user_id, pesquisa, resultados_personagens, chat_id, message_id):
    if not hasattr(globals, 'resultados_gnome'):
        globals.resultados_gnome = {}
    globals.resultados_gnome[user_id] = {
        'resultados': resultados_personagens,
        'pesquisa': pesquisa,
        'chat_id': chat_id,
        'message_id': message_id
    }

# Função para manusear o comando /gnomes
def gnomes(message):
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
        cursor.execute(sql_personagens, values_personagens)
        resultados_personagens = cursor.fetchall()

        if resultados_personagens:
            total_resultados = len(resultados_personagens)
            resultados_por_pagina = 15
            total_paginas = -(-total_resultados // resultados_por_pagina)
            pagina_solicitada = 1

            if total_resultados > resultados_por_pagina:
                resultados_pagina_atual = resultados_personagens[(pagina_solicitada - 1) * resultados_por_pagina:pagina_solicitada * resultados_por_pagina]
                lista_resultados = [f"{emoji} <code>{id_personagem}</code> • {nome}\nde {subcategoria}" for emoji, id_personagem, nome, subcategoria in resultados_pagina_atual]

                mensagem_final = f"🐠 Peixes de nome <b>{nome}</b>:\n\n" + "\n".join(lista_resultados) + f"\n\nPágina {pagina_solicitada}/{total_paginas}:"
                markup = create_navigation_markup(pagina_solicitada, total_paginas)
                msg = bot.send_message(chat_id, mensagem_final, reply_markup=markup, reply_to_message_id=message.message_id, parse_mode="HTML")

                save_state(user_id, nome, resultados_personagens, chat_id, msg.message_id)
            else:
                lista_resultados = [f"{emoji} <code>{id_personagem}</code> • {nome}\nde {subcategoria}" for emoji, id_personagem, nome, subcategoria in resultados_personagens]
                mensagem_final = f"🐠 Peixes de nome <b>{nome}</b>:\n\n" + "\n".join(lista_resultados)
                bot.send_message(chat_id, mensagem_final, reply_to_message_id=message.message_id, parse_mode='HTML')

        else:
            bot.send_message(chat_id, f"Nenhum resultado encontrado para o nome '{nome}'.", reply_to_message_id=message.message_id)
    finally:
        fechar_conexao(cursor, conn)

# Função de callback para manusear os botões de navegação da lista de /gnomes
@bot.callback_query_handler(func=lambda call: call.data.startswith('gnomes_'))
def callback_gnomes_navigation(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    # Recuperar o estado do usuário
    if user_id in globals.resultados_gnome:
        dados = globals.resultados_gnome[user_id]
        resultados_personagens = dados['resultados']
        pesquisa = dados['pesquisa']
        total_resultados = len(resultados_personagens)
        resultados_por_pagina = 10  # Mesmo número que foi usado na função /gnomes
        total_paginas = -(-total_resultados // resultados_por_pagina)

        # Determinar qual página foi solicitada
        data = call.data.split('_')
        acao = data[1]  # 'prev' ou 'next'
        pagina_solicitada = int(data[2])

        # Calcular os resultados da página solicitada
        resultados_pagina_atual = resultados_personagens[(pagina_solicitada - 1) * resultados_por_pagina:pagina_solicitada * resultados_por_pagina]
        lista_resultados = [f"{emoji} <code>{id_personagem}</code> • {nome}\nde {subcategoria}" for emoji, id_personagem, nome, subcategoria in resultados_pagina_atual]

        # Criar a mensagem com os resultados
        mensagem_final = f"🐠 Peixes de nome <b>{pesquisa}</b>:\n\n" + "\n".join(lista_resultados) + f"\n\nPágina {pagina_solicitada}/{total_paginas}:"
        markup = create_navigation_markup(pagina_solicitada, total_paginas)

        # Editar a mensagem existente para exibir os resultados da nova página
        bot.edit_message_text(mensagem_final, chat_id=chat_id, message_id=message_id, reply_markup=markup, parse_mode="HTML")

    else:
        bot.answer_callback_query(call.id, "Erro ao recuperar os resultados. Tente novamente.")

@bot.message_handler(commands=['gnomes'])
def gnomes_command(message):
    gnomes(message)

# Função de callback para manusear os botões de navegação
@bot.callback_query_handler(func=lambda call: call.data.startswith('gnome_'))
def callback_gnome_navigation(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    # Recuperar o estado do usuário
    if user_id in globals.resultados_gnome:
        dados = globals.resultados_gnome[user_id]
        resultados_personagens = dados['resultados']
        pesquisa = dados['pesquisa']
        total_resultados = len(resultados_personagens)
        resultados_por_pagina = 15
        total_paginas = -(-total_resultados // resultados_por_pagina)

        # Determinar qual página foi solicitada
        data = call.data.split('_')
        acao = data[1]  # 'prev' ou 'next'
        pagina_solicitada = int(data[2])

        # Calcular os resultados da página solicitada
        resultados_pagina_atual = resultados_personagens[(pagina_solicitada - 1) * resultados_por_pagina:pagina_solicitada * resultados_por_pagina]
        lista_resultados = [f"{emoji} <code>{id_personagem}</code> • {nome}\nde {subcategoria}" for emoji, id_personagem, nome, subcategoria in resultados_pagina_atual]

        # Criar a mensagem com os resultados
        mensagem_final = f"🐠 Peixes de nome <b>{pesquisa}</b>:\n\n" + "\n".join(lista_resultados) + f"\n\nPágina {pagina_solicitada}/{total_paginas}:"
        markup = create_navigation_markup(pagina_solicitada, total_paginas)

        # Editar a mensagem existente
        bot.edit_message_text(mensagem_final, chat_id=chat_id, message_id=message_id, reply_markup=markup, parse_mode="HTML")

    else:
        bot.answer_callback_query(call.id, "Erro ao recuperar os resultados. Tente novamente.")


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
                    enviar_mensagem_personagem(chat_id, resultado_evento, message.message_id, user_id)
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
                    enviar_mensagem_personagem(chat_id, resultado_normal, message.message_id, user_id)
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

def enviar_mensagem_personagem(chat_id, resultado_personagem, message_id, user_id):
    id_personagem, nome, subcategoria, quantidade_usuario, imagem_url = resultado_personagem[:5]
    cr = resultado_personagem[5] if len(resultado_personagem) > 5 else None

    # Verificar se a travessura de categoria errada está ativa
    if verificar_categoria_errada(user_id):
        conn, cursor = conectar_banco_dados()
        cursor.execute("SELECT subcategoria FROM personagens ORDER BY RAND() LIMIT 1")
        categoria_errada = cursor.fetchone()[0]
        fechar_conexao(cursor, conn)
        categoria = categoria_errada
    else:
        categoria = subcategoria  # Usar a categoria correta se a travessura não estiver ativa

    # Montar a mensagem
    mensagem = f"💌 | Personagem:\n\n<code>{id_personagem}</code> • {nome}\nde {categoria}"
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

    gif_url = obter_gif_url(id_personagem, user_id)
    print(gif_url)
    if gif_url:
        imagem_url = gif_url

    # Enviar mídia
    try:
        if imagem_url.lower().endswith(".gif"):
            # Tenta enviar como animação
            bot.send_animation(chat_id, imagem_url, caption=mensagem, reply_markup=markup, reply_to_message_id=message_id, parse_mode="HTML")
        elif imagem_url.lower().endswith(".mp4"):
            # Tenta enviar como vídeo
            bot.send_video(chat_id, imagem_url, caption=mensagem, reply_markup=markup, reply_to_message_id=message_id, parse_mode="HTML")
        elif imagem_url.lower().endswith((".jpeg", ".jpg", ".png")):
            # Envia como foto
            bot.send_photo(chat_id, imagem_url, caption=mensagem, reply_markup=markup, reply_to_message_id=message_id, parse_mode="HTML")
        else:
            # Se o arquivo não for suportado, envia a mensagem sem mídia
            bot.send_message(chat_id, mensagem, reply_markup=markup, parse_mode="HTML")
    except Exception as e:
        print(f"Erro ao enviar a mídia: {e}")
        try:
            # Se houver erro, tenta enviar como documento
            bot.send_document(chat_id, imagem_url, caption=mensagem, reply_markup=markup, reply_to_message_id=message_id, parse_mode="HTML")
        except Exception as e2:
            print(f"Erro ao enviar como documento: {e2}")
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
        id_usuario = call.from_user.id  # Captura o ID do usuário que acionou o callback

        if chat_id and message_id:
            # Passamos o ID do usuário para verificar travessura ou embaralhamento
            ultimo_clique[chat_id] = {'categoria': categoria}
            categoria_handler(call.message, categoria, id_usuario)
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
        
@bot.callback_query_handler(func=lambda call: call.data.startswith('total_'))
def callback_total_personagem(call):
    handle_callback_total_personagem(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith(('armazem_anterior_', 'armazem_proxima_','armazem_ultima_','armazem_primeira_')))
def callback_paginacao_armazem(call):
    handle_callback_paginacao_armazem(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('subcategory_'))
def handle_callback_subcategory(call):
    callback_subcategory(call)

@bot.message_handler(commands=['cenourar'])
def handle_cenourar(message):
    processar_verificar_e_cenourar(message, bot)
    
@bot.callback_query_handler(func=lambda call: call.data.startswith('cenourar_'))
def callback_cenourar(call):
    try:
        # Dividindo os dados do callback para extrair ação, usuário e cartas
        data_parts = call.data.split("_")
        acao = data_parts[1]  # Ação (sim ou nao)
        if acao == "sim":
            id_usuario = int(data_parts[2])  # ID do usuário
            ids_personagens = data_parts[3].split(",")  # IDs das cartas
            cenourar_carta(call, id_usuario, ids_personagens)
        elif acao == "nao":
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="🍂 Ufa! As cartas escaparam de serem cenouradas por pouco!")
    except Exception as e:
        print(f"Erro ao processar callback de cenoura: {e}")
        traceback.print_exc()
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
                # Apaga a mensagem original após o botão ser pressionado
        bot.delete_message(call.message.chat.id, call.message.message_id)
        aprovar_callback(call)
    except Exception as e:
        print(f"Erro ao processar callback de aprovação: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('reprovar_'))
def callback_reprovar(call):
    try:
                # Apaga a mensagem original após o botão ser pressionado
        bot.delete_message(call.message.chat.id, call.message.message_id)
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
@bot.message_handler(commands=['editartag'])
def handle_edit_tag_command(message):
    handle_edit_tag(message)

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

@bot.message_handler(commands=['setbio'])
def handle_setbio(message):
    set_bio_command(message)

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

