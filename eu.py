from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bd import *
from gif import *
import globals
from botoes import *
import random
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from credentials import *

        
def enviar_perfil(chat_id, legenda, imagem_fav, fav, id_usuario,message):
    gif_url = obter_gif_url(fav, id_usuario)
    if gif_url:

        if gif_url.lower().endswith(('.mp4', '.gif')):
            bot.send_animation(chat_id, gif_url, caption=legenda, parse_mode="HTML",reply_to_message_id=message.message_id)
        else:
            bot.send_photo(chat_id, gif_url, caption=legenda, parse_mode="HTML",reply_to_message_id=message.message_id)
    elif legenda:

        if imagem_fav.lower().endswith(('.jpg', '.jpeg', '.png')):
            bot.send_photo(chat_id, imagem_fav, caption=legenda, parse_mode="HTML",reply_to_message_id=message.message_id)
        elif imagem_fav.lower().endswith(('.mp4', '.gif')):
            bot.send_animation(chat_id, imagem_fav, caption=legenda, parse_mode="HTML",reply_to_message_id=message.message_id)
    else: 
        bot.send_message(chat_id, legenda, parse_mode="HTML")


def handle_set_musica(message):
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
            
def handle_set_fav(message):
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

def handle_obter_username(message):
    if len(message.text.split()) == 2 and message.text.split()[1].isdigit():
        user_id = int(message.text.split()[1])
        username = obter_username_por_id(user_id)
        bot.reply_to(message, username)
    else:
        bot.reply_to(message, "Formato incorreto. Use /usuario seguido do ID desejado, por exemplo: /usuario 123")

def handle_me_command(message):
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
