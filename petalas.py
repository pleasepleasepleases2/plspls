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
import random
from datetime import datetime
import requests
from PIL import Image, UnidentifiedImageError
from io import BytesIO
import tempfile
import os
from telebot import types
from bd import conectar_banco_dados, fechar_conexao

# Função para atualizar as pétalas do usuário
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
        print(f"DEBUG: Pétalas atuais: {petalas_atual}. Última regeneração: {ultima_regeneracao}")
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
        print(f"DEBUG: Pétalas regeneradas: {petalas_regeneradas}. Novas pétalas: {novas_petalas}")

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
            cartas_aleatorias = random.sample(resultado, 3)

            # Tentar pegar as imagens correspondentes às cartas
            imagens_cartas = []
            for carta in cartas_aleatorias:
                try:
                    # Verificar se a imagem com borda já está no cache
                    if carta[0] in cache_imagens_com_bordas:
                        imagens_cartas.append(cache_imagens_com_bordas[carta[0]])
                    else:
                        # Tentar fazer o download e abrir a imagem da carta
                        response = requests.get(carta[2])
                        img = Image.open(BytesIO(response.content))

                        # Baixar e aplicar uma borda aleatória
                        borda_response = requests.get(random.choice(bordas_urls))
                        borda_aleatoria = Image.open(BytesIO(borda_response.content))
                        img_com_borda = aplicar_borda(img, borda_aleatoria)

                        # Adicionar ao cache
                        cache_imagens_com_bordas[carta[0]] = img_com_borda
                        imagens_cartas.append(img_com_borda)

                except (UnidentifiedImageError, IOError):
                    continue

            # Definir o tamanho das imagens e o espaço entre elas
            largura_individual = 300
            altura_individual = 400
            espaco_entre = 10

            largura_total = 3 * largura_individual + 2 * espaco_entre
            altura_total = altura_individual

            imagem_final = Image.new("RGBA", (largura_total, altura_total), (255, 255, 255, 0))

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
        if os.path.exists(caminho_imagem):
            os.remove(caminho_imagem)

def callback_escolher_carta(call):
    try:
        if hasattr(call.message, 'escolha_feita') and call.message.escolha_feita:
            return

        id_personagem_escolhido = int(call.data.split("_")[1])

        call.message.escolha_feita = True

        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

        conn, cursor = conectar_banco_dados()
        cursor.execute("SELECT nome FROM personagens WHERE id_personagem = %s", (id_personagem_escolhido,))
        nome_personagem = cursor.fetchone()[0]
        fechar_conexao(cursor, conn)

        add_to_inventory(call.from_user.id, id_personagem_escolhido)

        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=f"💐 Você escolheu a pétala perfeita! {id_personagem_escolhido} - {nome_personagem} adicionada ao seu inventário. ✨"
        )

    except Exception as e:
        print(f"Erro ao processar a escolha de carta: {e}")
        bot.reply_to(call.message, "Ocorreu um erro ao processar sua escolha.")
