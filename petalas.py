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

def aplicar_borda(imagem, borda):
    """Aplica uma borda PNG sobre uma imagem e usa a imagem original desfocada como fundo, com borda menor."""
    # Garantir que a imagem tenha o modo RGBA (suporte a transparência)
    imagem = imagem.convert("RGBA")

    # Reduzir a imagem para caber dentro da borda
    largura_original, altura_original = imagem.size
    nova_largura = int(largura_original * 1)  # Reduzir a imagem para 85% da largura original
    nova_altura = int(altura_original * 1)  # Reduzir a imagem para 85% da altura original
    imagem_redimensionada = imagem.resize((nova_largura, nova_altura))

    # Aplicar desfoque à imagem original para usar como fundo
    imagem_fundo = imagem.filter(ImageFilter.GaussianBlur(radius=15))  # Ajuste o raio do desfoque conforme necessário

    # Redimensionar a borda para ser menor que a imagem original (diminuir a borda)
    largura_borda = int(largura_original * 1)  # Reduzir a borda para 95% da largura original
    altura_borda = int(altura_original * 1.25)  # Reduzir a borda para 95% da altura original
    borda = borda.convert("RGBA").resize((largura_borda, altura_borda))

    # Criar uma nova imagem com o fundo desfocado
    imagem_com_fundo = Image.new("RGBA", (largura_original, altura_original), (255, 255, 255, 0))

    # Colar o fundo desfocado na nova imagem
    imagem_com_fundo.paste(imagem_fundo, (0, 0))

    # Ajustar a posição vertical para mover a imagem um pouco mais para baixo
    deslocamento_vertical = int(altura_original * 0.1)  # Deslocar 10% para baixo

    # Calcular as posições para centralizar a imagem redimensionada
    posicao_x = (largura_original - nova_largura) // 2
    posicao_y = (altura_original - nova_altura) // 2 + deslocamento_vertical  # Mover a imagem um pouco para baixo

    # Colar a imagem redimensionada no centro da imagem desfocada
    imagem_com_fundo.paste(imagem_redimensionada, (posicao_x, posicao_y), imagem_redimensionada)

    # Calcular as posições para centralizar a borda menor
    posicao_borda_x = (largura_original - largura_borda) // 2
    posicao_borda_y = (altura_original - altura_borda) // 2

    # Aplicar a borda menor sobre a imagem com o fundo
    imagem_com_fundo.paste(borda, (posicao_borda_x, posicao_borda_y), borda)

    return imagem_com_fundo
