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


def processar_id_vip(message):
    try:
        id_usuario = int(message.text)
        msg = bot.reply_to(message, "Por favor, envie o nome do usuário.")
        bot.register_next_step_handler(msg, lambda msg: processar_nome_vip(msg, id_usuario))
    except ValueError:
        bot.reply_to(message, "ID inválido. Por favor, tente novamente.")


def processar_nome_vip(message, id_usuario):
    nome = message.text
    msg = bot.reply_to(message, "Informe a data de pagamento (formato: AAAA-MM-DD):")
    bot.register_next_step_handler(msg, lambda msg: processar_pagamento_vip(msg, id_usuario, nome))


def processar_pagamento_vip(message, id_usuario, nome):
    try:
        data_pagamento = message.text
        conn, cursor = conectar_banco_dados()
        
        # Inserir o novo VIP na tabela
        cursor.execute(
            "INSERT INTO vips (id_usuario, nome, data_pagamento, mes_atual) VALUES (%s, %s, %s, DATE_FORMAT(NOW(), '%Y-%m'))",
            (id_usuario, nome, data_pagamento)
        )
        conn.commit()

        bot.reply_to(message, f"{nome} foi adicionado(a) como VIP com sucesso!")
    except Exception as e:
        bot.reply_to(message, f"Erro ao adicionar VIP: {e}")
    finally:
        fechar_conexao(cursor, conn)

  # Função para verificar quanto tempo falta para a próxima pétala
def calcular_tempo_restante(id_usuario):
    conn, cursor = conectar_banco_dados()
    cursor.execute("SELECT ultima_regeneracao_petalas FROM usuarios WHERE id_usuario = %s", (id_usuario,))
    resultado = cursor.fetchone()
    
    if resultado:
        ultima_regeneracao = resultado[0]
        agora = datetime.now()

        # Verificar se o usuário é VIP e ajustar o tempo de regeneração
        vip = is_vip(id_usuario)
        if vip:
            TEMPO_REGENERACAO = timedelta(hours=2)
        else:
            TEMPO_REGENERACAO = timedelta(hours=3)

        # Calcular o tempo até a próxima regeneração de pétalas
        tempo_restante = TEMPO_REGENERACAO - (agora - ultima_regeneracao)
        if tempo_restante.total_seconds() > 0:
            horas, resto = divmod(tempo_restante.total_seconds(), 3600)
            minutos, _ = divmod(resto, 60)
            return f"{int(horas)}h {int(minutos)}min"
        else:
            return "menos de 1 minuto"

    fechar_conexao(cursor, conn)
    return "um pouco mais"

def processar_remocao_vip(message):
    try:
        id_usuario = int(message.text)
        conn, cursor = conectar_banco_dados()
        
        # Remover o VIP da tabela
        cursor.execute("DELETE FROM vips WHERE id_usuario = %s", (id_usuario,))
        conn.commit()

        bot.reply_to(message, "VIP removido com sucesso!")
    except Exception as e:
        bot.reply_to(message, f"Erro ao remover VIP: {e}")
    finally:
        fechar_conexao(cursor, conn)
def verificar_pedidos_vip(id_usuario):
    conn, cursor = conectar_banco_dados()
    
    cursor.execute(
        "SELECT pedidos_restantes, mes_atual FROM vips WHERE id_usuario = %s",
        (id_usuario,)
    )
    vip_data = cursor.fetchone()
    fechar_conexao(cursor, conn)
    
    if vip_data:
        pedidos_restantes, mes_atual = vip_data
        mes_atual_sistema = datetime.now().strftime('%Y-%m')
        
        if mes_atual != mes_atual_sistema:
            # Reiniciar pedidos para o novo mês
            pedidos_restantes = 4
            atualizar_pedidos_vip(id_usuario, pedidos_restantes, mes_atual_sistema)
        
        return pedidos_restantes
    else:
        return None


def atualizar_pedidos_vip(id_usuario, novos_pedidos, novo_mes):
    conn, cursor = conectar_banco_dados()
    
    cursor.execute(
        "UPDATE vips SET pedidos_restantes = %s, mes_atual = %s WHERE id_usuario = %s",
        (novos_pedidos, novo_mes, id_usuario)
    )
    conn.commit()
    fechar_conexao(cursor, conn)

def is_vip(id_usuario):
    """Verifica se o usuário é VIP consultando a tabela vips."""
    conn, cursor = conectar_banco_dados()
    
    # Verifica se o usuário está na tabela de VIPs
    cursor.execute("SELECT id_usuario FROM vips WHERE id_usuario = %s", (id_usuario,))
    resultado = cursor.fetchone()  # Usa fetchone para obter um único resultado

    # Fechar o cursor e a conexão
    cursor.fetchall()  # Garante que todos os resultados foram processados, se houver
    fechar_conexao(cursor, conn)

    # Retorna True se o usuário for VIP, False caso contrário
    return resultado is not None

def processar_pedido_submenu(message, pedidos_restantes, user_name):
    chat_id = message.chat.id
    texto_submenu = message.text

    # Verificar se o texto está no formato esperado
    try:
        if not validar_formato_submenu(texto_submenu):
            bot.send_message(chat_id, "Formato incorreto. Certifique-se de seguir o exemplo:\n- subcategoria:\n- submenu:\npersonagem1nome, link da foto\npersonagem2nome, link da foto")
            return

        # Reduzir o número de pedidos restantes no banco de dados
        conn, cursor = conectar_banco_dados()
        cursor.execute("UPDATE vips SET pedidos_restantes = pedidos_restantes - 1 WHERE id_usuario = %s", (message.from_user.id,))
        conn.commit()

        # Enviar o pedido para o grupo
        grupo_id = -1002024419694  # ID do grupo para encaminhar os pedidos
        mensagem_grupo = (
            f"📩 Novo pedido de submenu de {user_name}!\n\n"
            f"Pedidos restantes: {pedidos_restantes - 1}\n\n"
            f"Submenu enviado:\n\n{texto_submenu}"
        )
        bot.send_message(grupo_id, mensagem_grupo)

        bot.send_message(chat_id, "Seu pedido foi encaminhado com sucesso!")
    except Exception as e:
        bot.send_message(chat_id, "Ocorreu um erro ao processar seu pedido. Tente novamente.")
        print(f"Erro ao processar pedido de submenu: {e}")
    finally:
        fechar_conexao(cursor, conn)


def validar_formato_submenu(texto):
    # Verifica se o texto contém os itens básicos do submenu
    linhas = texto.splitlines()
    if len(linhas) < 4:
        return False

    # Verifica a presença das chaves "subcategoria" e "submenu"
    if not linhas[0].lower().startswith("- subcategoria:") or not linhas[1].lower().startswith("- submenu:"):
        return False

    # Verifica se há ao menos uma linha de personagem no formato esperado (nome, link)
    for linha in linhas[2:]:
        if "," not in linha or len(linha.split(",")) != 2:
            return False

    return True


def adicionar_vip_logic(message):
    if message.from_user.id not in [5532809878, 1805086442, 5799169750]:
        bot.reply_to(message, "Você não tem permissão para usar este comando.")
        return

    msg = bot.reply_to(message, "Por favor, envie o ID do usuário para adicionar como VIP.")
    bot.register_next_step_handler(msg, processar_id_vip)

def processar_id_vip(message):
    try:
        id_usuario = int(message.text)
        # Lógica para adicionar o VIP ao banco de dados
        bot.send_message(message.chat.id, f"Usuário {id_usuario} foi adicionado como VIP.")
    except ValueError:
        bot.reply_to(message, "ID inválido. Por favor, envie um ID numérico válido.")

def remover_vip_logic(message):
    if message.from_user.id not in [5532809878, 1805086442, 5799169750]:
        bot.reply_to(message, "Você não tem permissão para usar este comando.")
        return

    msg = bot.reply_to(message, "Por favor, envie o ID do usuário VIP a ser removido.")
    bot.register_next_step_handler(msg, processar_remocao_vip)

def processar_remocao_vip(message):
    try:
        id_usuario = int(message.text)
        # Lógica para remover o VIP do banco de dados
        bot.send_message(message.chat.id, f"Usuário {id_usuario} foi removido dos VIPs.")
    except ValueError:
        bot.reply_to(message, "ID inválido. Por favor, envie um ID numérico válido.")


# Lógica para listar os VIPs
def listar_vips_logic(message):
    try:
        # Verificar se o usuário é autorizado
        if message.from_user.id not in [5532809878, 1805086442, 5799169750]:
            return
        
        # Conectar ao banco de dados
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
        # Fechar a conexão com o banco de dados
        fechar_conexao(cursor, conn)

# Lógica para listar os pedidos dos VIPs
def listar_pedidos_vips_logic(message):
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

# Lógica para ver a ficha de um VIP
def ver_ficha_vip_logic(message):
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
from bd import conectar_banco_dados, fechar_conexao

# Função para processar o comando /pedidosubmenu
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

# Função para processar o comando /pedidovip
def pedidovip_command(message):
    if message.from_user.id not in [5532809878, 1805086442]:
        bot.send_message(message.chat.id, "Você não tem permissão para usar este comando.")
        return

    try:
        args = message.text.split()
        if len(args) != 3:
            bot.send_message(message.chat.id, "Uso incorreto. Formato correto: /pedidovip <iddovip> <número (+ ou -)>")
            return

        id_vip = int(args[1])
        ajuste = int(args[2])

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

