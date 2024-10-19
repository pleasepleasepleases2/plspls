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
