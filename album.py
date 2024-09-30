from pesquisas import *
from user import *
from bd import *
from loja import *
from gnome import *
import PIL
from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests
import diskcache as dc
ALBUM_PATH = 'album.png'
BACKGROUND_URL = 'https://i.pinimg.com/564x/19/a5/b0/19a5b0b149cd1a26f3fa7766061e902c.jpg'
BORDER_COLOR = '#DE3163'
CACHE_DIR = 'sticker_cache'
cache = dc.Cache('./cache')


def get_all_stickers():
    conn, cursor = conectar_banco_dados()
    cursor.execute('SELECT id, name FROM stickers')
    all_stickers = cursor.fetchall()
    cursor.close()
    conn.close()
    return all_stickers

def get_user_stickers(user_id):
    conn, cursor = conectar_banco_dados()
    cursor.execute('SELECT sticker_id FROM inventariofig WHERE user_id = %s', (user_id,))
    user_stickers = {row[0] for row in cursor.fetchall()}
    cursor.close()
    conn.close()
    return user_stickers

def get_missing_stickers(user_id, page, stickers_per_page=9):
    all_stickers = get_all_stickers()
    user_stickers = get_user_stickers(user_id)
    missing_stickers = [sticker for sticker in all_stickers if sticker[0] not in user_stickers]
    
    start = (page - 1) * stickers_per_page
    end = start + stickers_per_page
    return missing_stickers[start:end], len(missing_stickers)

def get_missing_album_markup(page, total_pages):
    markup = InlineKeyboardMarkup()
    if page > 1:
        markup.add(InlineKeyboardButton('Anterior', callback_data=f'missing_prev_{page - 1}'))
    if page < total_pages:
        markup.add(InlineKeyboardButton('Próximo', callback_data=f'missing_next_{page + 1}'))
    return markup

def get_user_stickers(user_id, page, stickers_per_page=9):
    conn, cursor = conectar_banco_dados()
    offset = (page - 1) * stickers_per_page
    cursor.execute('''
        SELECT stickers.id, stickers.name, stickers.image_path, SUM(inventariofig.quantity)
        FROM inventariofig
        JOIN stickers ON inventariofig.sticker_id = stickers.id
        WHERE inventariofig.user_id = %s
        GROUP BY stickers.id
        LIMIT %s OFFSET %s
    ''', (user_id, stickers_per_page, offset))
    stickers = cursor.fetchall()
    cursor.close()
    conn.close()
    return stickers

def get_total_pages(user_id, stickers_per_page=9):
    conn, cursor = conectar_banco_dados()
    cursor.execute('''
        SELECT COUNT(DISTINCT sticker_id)
        FROM inventariofig
        WHERE user_id = %s
    ''', (user_id,))
    total_stickers = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return (total_stickers + stickers_per_page - 1) // stickers_per_page

def get_total_stickers(user_id):
    conn, cursor = conectar_banco_dados()
    cursor.execute('''
        SELECT COUNT(DISTINCT sticker_id)
        FROM inventariofig
        WHERE user_id = %s
    ''', (user_id,))
    total_stickers = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return total_stickers

def get_album_markup(page, total_pages):
    markup = InlineKeyboardMarkup()
    if page > 1:
        markup.add(InlineKeyboardButton('Anterior', callback_data=f'prev_{page - 1}'))
    if page < total_pages:
        markup.add(InlineKeyboardButton('Próximo', callback_data=f'next_{page + 1}'))
    return markup


def get_sticker_by_id(sticker_id):
    conn, cursor = conectar_banco_dados()
    cursor.execute('''
        SELECT id, name, image_path 
        FROM stickers 
        WHERE id = %s
    ''', (sticker_id,))
    sticker = cursor.fetchone()
    cursor.close()
    conn.close()
    return sticker

def get_cached_sticker(sticker_url, hole_width, hole_height):
    """Retorna a imagem da figurinha redimensionada do cache ou faz o download e redimensiona se não estiver no cache."""
    response = requests.get(sticker_url)
    sticker_image = Image.open(BytesIO(response.content))
    sticker_image = sticker_image.resize((hole_width, hole_height))
    bordered_sticker = ImageOps.expand(sticker_image, border=2, fill='black')  # Borda padrão preta
    return bordered_sticker

def create_album(user_id, page):
    try:
        cache_key = f"album_{user_id}_page_{page}"
        
        if cache_key in cache:
            return cache[cache_key]

        # Conecte-se ao banco de dados
        conn, cursor = conectar_banco_dados()

        # Baixar a imagem de fundo
        response = requests.get(BACKGROUND_URL)
        background = Image.open(BytesIO(response.content))

        # Dimensões da imagem 9:16 (por exemplo, 540x960 pixels)
        width, height = 540, 960
        background = background.resize((width, height))

        # Crie uma nova imagem com o fundo
        img = Image.new('RGB', (width, height))
        img.paste(background, (0, 0))

        draw = ImageDraw.Draw(img)

        # Dimensões dos buracos pretos
        hole_width, hole_height = 140, 210
        horizontal_padding = 20
        vertical_padding = 40  # Aumentando o espaçamento vertical

        # Calcula a posição inicial para centralizar a grade
        total_width = 3 * hole_width + 2 * horizontal_padding
        total_height = 3 * hole_height + 2 * vertical_padding
        start_x = (width - total_width) // 2
        start_y = (height - total_height) // 2

        # Coordenadas dos buracos (3x3)
        coordinates = []
        for row in range(3):
            for col in range(3):
                x0 = start_x + col * (hole_width + horizontal_padding)
                y0 = start_y + row * (hole_height + vertical_padding)
                x1 = x0 + hole_width
                y1 = y0 + hole_height
                coordinates.append((x0, y0, x1, y1))

        # Verifique quais figurinhas o usuário possui na página atual
        cursor.execute('''
            SELECT stickers.id, stickers.image_path 
            FROM inventariofig 
            JOIN stickers ON inventariofig.sticker_id = stickers.id 
            WHERE inventariofig.user_id = %s
        ''', (user_id,))
        stickers = cursor.fetchall()

        # Dicionário de figurinhas do usuário
        user_stickers = {sticker[0]: sticker[1] for sticker in stickers}

        # Preencha os buracos com as figurinhas
        for idx, coord in enumerate(coordinates):
            sticker_id = (page - 1) * 9 + idx + 1
            if sticker_id in user_stickers:
                # Carregar a figurinha correspondente do cache ou baixar se não estiver no cache
                bordered_sticker = get_cached_sticker(user_stickers[sticker_id], hole_width, hole_height)
                
                # Colar a figurinha com borda na posição correta
                img.paste(bordered_sticker, (coord[0], coord[1]))
            else:
                # Preencher com buraco preto se a figurinha não existir
                draw.rectangle(coord, fill='black')

        # Adicionar texto "Página x/5" no rodapé
        font = ImageFont.load_default()
        text = f"Página {page}/5"
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = (width - text_width) // 2
        text_y = height - 30  # 30 pixels acima do rodapé
        draw.text((text_x, text_y), text, fill="black", font=font)

        # Salve a imagem
        album_path = f"album_{user_id}_page_{page}.png"
        img.save(album_path)

        # Salvar a imagem no cache
        cache[cache_key] = album_path
        
        cursor.close()
        conn.close()
        return album_path
    
    except Exception as e:
        print(f"Erro ao criar o álbum: {e}")
        return None
def cache_sticker(sticker_url, border_color, border_width):
    cache_key = f"{sticker_url}_{border_color}_{border_width}"
    if cache_key in cache:
        return cache[cache_key]

    response = requests.get(sticker_url)
    sticker_image = Image.open(BytesIO(response.content))
    sticker_image = sticker_image.resize((140, 210))  # Tamanho das figurinhas
    bordered_sticker = ImageOps.expand(sticker_image, border=border_width, fill=border_color)
    
    # Converter para RGB se a imagem tiver um canal alfa
    if bordered_sticker.mode == 'RGBA':
        bordered_sticker = bordered_sticker.convert('RGB')
    
    img_bytes = BytesIO()
    bordered_sticker.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    cache[cache_key] = img_bytes

    return img_bytes

def process_sticker(sticker_info):
    sticker_url, border_color, border_width = sticker_info
    return cache_sticker(sticker_url, border_color, border_width)

def get_navigation_markup(current_page):
    markup = types.InlineKeyboardMarkup(row_width=5)
    buttons = []
    for i in range(1, 6):
        if i == current_page:
            buttons.append(types.InlineKeyboardButton(f"📄 {i}", callback_data=f'page_{i}'))
        else:
            buttons.append(types.InlineKeyboardButton(str(i), callback_data=f'page_{i}'))
    markup.add(*buttons)
    return markup

def adicionar_figurinha_ao_cache(user_id, sticker_id):
    page = (sticker_id - 1) // 9 + 1
    cache_key = f"album_{user_id}_page_{page}"
    
    if cache_key in cache:
        # Remover o álbum do cache para forçar a atualização
        del cache[cache_key]
