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
from armazem import *
def verificar_travessura_embaralhamento(user_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Verificar se a travessura está ativa
        cursor.execute("""
            SELECT fim_travessura FROM travessuras
            WHERE id_usuario = %s AND tipo_travessura = 'embaralhamento'
        """, (user_id,))
        resultado = cursor.fetchone()

        if resultado:
            fim_travessura = resultado[0]
            # Se a travessura ainda está ativa (o tempo atual é menor que o fim)
            if datetime.now() < fim_travessura:
                return True
        
        return False  # Travessura não está ativa
    
    except Exception as e:
        print(f"Erro ao verificar a travessura de embaralhamento: {e}")
        return False
    finally:
        fechar_conexao(cursor, conn)

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
        subcategoria = verificar_apelido(subcategoria)  # Função que valida apelidos de subcategorias
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
        # Verificar se a travessura está ativa e embaralhar, se necessário
        if verificar_travessura_embaralhamento(message.from_user.id):
            mensagem = embaralhar_mensagem(mensagem)
        if diferenca:
            for id_personagem in diferenca:
                mensagem += f"<code>{id_personagem}</code> - {personagens_usuario_1.get(id_personagem)}\n"
        else:
            mensagem = "Parece que não temos um match. Tente outra espécie!"
            # Verificar se a travessura está ativa e embaralhar, se necessário
            if verificar_travessura_embaralhamento(message.from_user.id):
                mensagem = embaralhar_mensagem(mensagem)
        bot.send_message(message.chat.id, mensagem, parse_mode="HTML", reply_to_message_id=message.id)

    except Exception as e:
        bot.reply_to(message, f"Ocorreu um erro ao processar o comando: {e}")

    finally:
        fechar_conexao(cursor, conn)

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
        # Verificar se a travessura está ativa e embaralhar, se necessário
        if verificar_travessura_embaralhamento(message.from_user.id):
            mensagem = embaralhar_mensagem(mensagem)
        if diferenca:
            for id_personagem in diferenca:
                mensagem += f"<code>{id_personagem}</code> - {personagens_usuario_2.get(id_personagem)}\n"
        else:
            mensagem = "Parece que não temos um match."
                # Verificar se a travessura está ativa e embaralhar, se necessário
            if verificar_travessura_embaralhamento(message.from_user.id):
                mensagem = embaralhar_mensagem(mensagem)
        bot.send_message(message.chat.id, mensagem, parse_mode="HTML", reply_to_message_id=message.id)

    except Exception as e:
        bot.reply_to(message, f"Ocorreu um erro ao processar o comando: {e}")
    finally:
        fechar_conexao(cursor, conn)
