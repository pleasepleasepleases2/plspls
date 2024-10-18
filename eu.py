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

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())
        
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
            
