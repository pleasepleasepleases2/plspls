import time
from queue import Queue
resultados_gnome = {}

jogos_termo = {}
ultimo_clique = {}
cartas_compradas_dict = {}
dict_peixes_por_pagina = {}
user_pages = {}
state_data = {}
callbacks_temp = {}
estados = {}
links_gif = {}
motivos_reprovacao = {}
ultima_interacao = {}
armazem_info = {}
cartas_legenda = {}
ultimo_clique = {}
categoria_escolhida = {}
message_ids = {}
mensagens_editaveis = []
cesta_info = []
botao_clicado = False
load_state = {}
user_event_data = {}
active_song_challenges = {}
usuarios_em_sugestao = {}
jogos_da_velha = {}
jogadores_labirinto = {}
# Lista de URLs das bordas PNG
bordas_urls = [
    "https://pub-2c8b03f2268f415896ccfb5456f45c9c.r2.dev/foto_20240921014910.jpg",
    "https://pub-2c8b03f2268f415896ccfb5456f45c9c.r2.dev/foto_20240921014846.jpg",
    "https://pub-2c8b03f2268f415896ccfb5456f45c9c.r2.dev/foto_20240921014841.jpg",
    "https://pub-2c8b03f2268f415896ccfb5456f45c9c.r2.dev/foto_20240921014836.jpg",
    "https://pub-2c8b03f2268f415896ccfb5456f45c9c.r2.dev/foto_20240921014831.jpg",
    "https://pub-2c8b03f2268f415896ccfb5456f45c9c.r2.dev/foto_20240921014817.jpg"
]

# Criar um cache para as imagens com bordas aplicadas
cache_imagens_com_bordas = {}

# Listas de palavras separadas por quantidade de letras
palavras_4_letras = ['doce', 'osso', 'fada', 'medo', 'gato', 'mago', 'lobo', 'teia', 'bala']
palavras_5_letras = ['doces', 'morte', 'ossos', 'fadas', 'bruxa', 'magia', 'poção', 'zumbi', 'lobos', 'mumia', 'uivar', 'susto', 'tumba']
palavras_6_letras = ['mortes', 'morder', 'sangue', 'caixão', 'aranha', 'presas', 'crânio', 'lápide', 'pocoes', 'bombom']
palavras_7_letras = ['abobora', 'vampiro', 'malvado', 'demonio', 'maldade', 'sangrar', 'varinha', 'caveira', 'monstro', 'morcego']
palavras_8_letras = ['fantasia', 'fantasma', 'vassoura']
