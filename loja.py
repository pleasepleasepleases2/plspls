import random
from pesquisas import *
from user import *
from bd import *
from loja import *
from pescar import *
from operacoes import *
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from cachetools import cached, TTLCache


# Cache com validade de 24 horas (86400 segundos)
loja_cache = TTLCache(maxsize=100, ttl=43200)

@cached(loja_cache)
def obter_ids_loja_do_dia(data_atual):
    try:
        conn, cursor = conectar_banco_dados()
        ordem_categorias = {'Música': 1, 'animangá': 2, 'Filmes': 3, 'Séries': 4, 'Jogos': 5, 'Miscelânea': 6}
        cursor.execute(
            "SELECT l.id_personagem FROM loja AS l "
            "JOIN personagens AS p ON l.id_personagem = p.id_personagem "
            "WHERE l.data = %s "
            "ORDER BY FIELD(p.categoria, %s)",
            (data_atual, ','.join(f"'{cat}'" for cat in ordem_categorias.keys()))
        )
        ids_do_dia = [id_tuple[0] for id_tuple in cursor.fetchall()]
        return ids_do_dia
    except mysql.connector.Error as err:
        print(f"Erro ao obter IDs da loja para o dia de hoje: {err}")
        return []
    finally:
        fechar_conexao(cursor, conn)


def obter_cartas_aleatorias(quantidade=6):
    try:
        conn, cursor = conectar_banco_dados()
        categorias = ['Música', 'Séries', 'Filmes', 'Miscelanêa', 'Jogos', 'Animangá']
        cartas_aleatorias = []

        for categoria in categorias:
            while True:
                cursor.execute(
                    "SELECT id_personagem, nome, subcategoria, imagem, emoji FROM personagens WHERE categoria = %s AND imagem IS NOT NULL ORDER BY RAND() LIMIT 1",
                    (categoria,))
                carta_aleatoria = cursor.fetchone()

                if carta_aleatoria and carta_aleatoria[0]:
                    id_personagem = carta_aleatoria[0]
                    if not id_ja_registrado_na_loja(cursor, id_personagem):
                        cartas_dict = {
                            "id": id_personagem,
                            "nome": carta_aleatoria[1],
                            "subcategoria": carta_aleatoria[2],
                            "imagem": carta_aleatoria[3],
                            "emoji": carta_aleatoria[4],
                            "categoria": categoria 
                        }
                        cartas_aleatorias.append(cartas_dict)
                        print(f"Carta adicionada: {cartas_dict} - Categoria: {categoria}")
                        break
                    else:
                        print(f"ID {id_personagem} já registrado na loja. Tentando outra carta.")
                else:
                    print("Carta não encontrada para a categoria:", categoria)
                    break
        return cartas_aleatorias

    except Exception as e:
        print(f"Erro ao obter cartas aleatórias: {e}")
        return []
    finally:
        fechar_conexao(cursor, conn)

def obter_cartas_por_ids(ids):
    try:
        conn, cursor = conectar_banco_dados()
        ids_formatados = ','.join(['%s'] * len(ids))
        query = f"SELECT id_personagem, emoji, nome, imagem, categoria, subcategoria FROM personagens WHERE id_personagem IN ({ids_formatados})"
        cursor.execute(query, ids)
        resultados = cursor.fetchall()
        cartas = [{'id': r[0], 'emoji': r[1], 'nome': r[2], 'imagem': r[3], 'categoria': r[4], 'subcategoria': r[5]} for r in resultados]
        return cartas
    except Exception as e:
        print(f"Erro ao obter cartas: {e}")
        return []
    finally:
        fechar_conexao(cursor, conn)


def registrar_cartas_loja(cartas_aleatorias, data_atual):
    try:
        conn, cursor = conectar_banco_dados()

        for carta in cartas_aleatorias:
            id_personagem = carta['id']
            categoria = carta['categoria']
            cursor.execute(
                "SELECT COUNT(*) FROM loja WHERE id_personagem = %s AND data = %s",
                (id_personagem, data_atual)
            )
            count = cursor.fetchone()[0]

            if count == 0:
                cursor.execute(
                    "INSERT INTO loja (id_personagem, data, categoria) VALUES (%s, %s, %s)",
                    (id_personagem, data_atual, categoria) 
                )
        conn.commit()

    except Exception as e:
        print(f"Erro ao registrar cartas na loja: {e}")
    finally:
        fechar_conexao(cursor, conn)

def id_ja_registrado_na_loja(cursor, id_personagem):
    cursor.execute("SELECT COUNT(*) FROM loja WHERE id_personagem = %s", (id_personagem,))
    count = cursor.fetchone()[0]
    return count > 0

def loja_geral_callback(call):
    try:
        conn, cursor = conectar_banco_dados()
        id_usuario = call.from_user.id
        cursor.execute("SELECT cenouras FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        result = cursor.fetchone()
        if result:
            qnt_cenouras = int(result[0])
        else:
            qnt_cenouras = 0
        if qnt_cenouras >= 3:
            mensagem = f"Você tem {qnt_cenouras} cenouras. Deseja usar 3 para ganhar um peixe aleatório?"
            keyboard = telebot.types.InlineKeyboardMarkup()
            keyboard.row(
                telebot.types.InlineKeyboardButton(text="Sim", callback_data=f'geral_compra_{id_usuario}'),
                telebot.types.InlineKeyboardButton(text="Não", callback_data='cancelar_compra')
            )
            imagem_url = "https://pub-6f23ef52e8614212a14d24b0cf55ae4a.r2.dev/BQACAgEAAxkBAAIe1Wclk2eiQkwGjTXrZqQvdjaeLtrbAALHBAAC7WgxRfD2-mIpIl3TNgQ.jpg"
            bot.edit_message_media(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=keyboard,
                media=telebot.types.InputMediaPhoto(media=imagem_url, caption=mensagem)
            )
    except Exception as e:
        print(f"Erro ao processar loja_geral_callback: {e}")

def geral_compra_callback(call):
    try:
        conn, cursor = conectar_banco_dados()

        query_personagens = "SELECT id_personagem, nome, subcategoria,  emoji, categoria,  imagem, cr FROM personagens ORDER BY RAND() LIMIT 1"
        cursor.execute(query_personagens)
        carta_personagem = cursor.fetchone()
        chance = random.choices([True, False], weights=[5, 95])[0]
        if chance:
            query_evento = "SELECT id_personagem, nome, subcategoria, categoria, evento, emoji, cr, imagem FROM evento ORDER BY RAND() LIMIT 1"
            cursor.execute(query_evento)
            carta_evento = cursor.fetchone()
        else:
            carta_evento = None
        if carta_personagem or carta_evento:
            if carta_evento:
                id_personagem, nome, subcategoria, categoria, evento, emoji, cr, imagem = carta_evento
                categoria = "Evento"
            else:
                id_personagem, nome, subcategoria,  emoji, categoria,  imagem, cr = carta_personagem
                evento = ""
                categoria = categoria.capitalize() 

            id_usuario = call.from_user.id
            valor = 3
            add_to_inventory(id_usuario, id_personagem)
            diminuir_cenouras(id_usuario, valor)

            resposta = f"🎴 Os mares trazem para sua rede:\n\n" \
           f"{emoji} • <code>{id_personagem}</code> - {nome} \n{subcategoria}{' - ' + evento if not carta_personagem else ''}\n\nVolte sempre!"

            if imagem:
                bot.edit_message_media(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    media=telebot.types.InputMediaPhoto(media=imagem, caption=resposta,parse_mode="HTML")
                )
            else:
                resposta1 = f"🎴 Os mares trazem para sua rede:\n\n {emoji} • <code>{id_personagem}</code> - {nome} \n{subcategoria} - {categoria if carta_personagem else evento}\n\n (A carta não possui foto ainda :())"
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=resposta1,
                    reply_markup=None,
                    parse_mode="HTML"
                )
        else:
            bot.send_message(call.message.chat.id, "Não foi possível encontrar uma carta aleatória.")
    except mysql.connector.Error as err:
        bot.send_message(call.message.chat.id, f"Erro ao sortear carta: {err}")
    finally:
        fechar_conexao(cursor, conn)
        
def confirmar_iscas(call,message_id):
    try:
        print(message_id)
        chat_id = call.message.chat.id
        id_usuario = call.message.chat.id
        conn, cursor = conectar_banco_dados()
        
        cursor.execute("SELECT cenouras FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        result = cursor.fetchone()

        if result and len(result) > 0: 
            qnt_cenouras = int(result[0])
            if qnt_cenouras >= 5:
                cursor.execute("UPDATE usuarios SET cenouras = cenouras - 5 WHERE id_usuario = %s", (id_usuario,))
                cursor.execute("UPDATE usuarios SET iscas = iscas + 1 WHERE id_usuario = %s", (id_usuario,))
                conn.commit()

                mensagem = "Parabéns! Você comprou uma isca.\n\nBoas pescas."
                bot.edit_message_caption(
                    chat_id=chat_id,
                    message_id=message_id,
                    caption=mensagem
                )
            else:
                mensagem = "Desculpe, você não tem cenouras suficientes para comprar uma isca."
                bot.edit_message_caption(
                    chat_id=chat_id,
                    message_id=message_id,
                    caption=mensagem
                )
        else:
            mensagem = "Desculpe, não foi possível encontrar suas cenouras."
            bot.edit_message_caption(
                    chat_id=chat_id,
                    message_id=message_id,
                    caption=mensagem
                )
    except Exception as e:
        print(f"Erro ao processar confirmar_compra_iscas: {e}")


def compras_iscas_callback(call):
    try:
        message_id = call.message.message_id
        chat_id = call.message.chat.id
        id_usuario = call.message.chat.id
        conn, cursor = conectar_banco_dados()

        cursor.execute("SELECT cenouras FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        result = cursor.fetchone()

        print(f"DEBUG - Resultado da consulta: {result}")
        print(f"message id: {message_id}")
        if result and len(result) > 0:
            qnt_cenouras = int(result[0])
            if qnt_cenouras >= 5:
                mensagem = f"Você tem {qnt_cenouras} cenouras. Deseja usar 5 para comprar iscas?"
                keyboard = telebot.types.InlineKeyboardMarkup()
                keyboard.row(
                    telebot.types.InlineKeyboardButton(text="Sim", callback_data='confirmar_iscas'),
                    telebot.types.InlineKeyboardButton(text="Não", callback_data='cancelar_compra')
                )
                bot.edit_message_caption(
                    chat_id=chat_id,
                    message_id=message_id,
                    reply_markup=keyboard,
                    caption=mensagem
                )
            else:
                bot.send_message(chat_id, "Você não tem cenouras suficientes para comprar iscas.")
        else:
            bot.send_message(chat_id, "Desculpe, ocorreu um erro ao verificar suas cenouras.")
    except Exception as e:
        print(f"Erro ao processar compras_iscas_callback: {e}")

def doar_cenoura(call):
    try:
        conn, cursor = conectar_banco_dados()
        message_id = call.message.message_id
        chat_id = call.message.chat.id
        id_usuario = call.from_user.id

        cursor.execute("SELECT cenouras FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        result = cursor.fetchone()

        print(f"DEBUG - Resultado da consulta: {result}")

        if result and len(result) > 0:  
            qnt_cenouras = int(result[0])
            if qnt_cenouras >= 1:
                mensagem = f"Você tem {qnt_cenouras} cenouras. \n\nPara doar, digite o usuário do Garden e a quantidade. \n\nExemplo: user1 100"
                bot.edit_message_caption(
                    chat_id=chat_id,
                    message_id=message_id,
                    caption=mensagem
                )


                @bot.message_handler(func=lambda message: message.chat.id == chat_id and message.from_user.id == id_usuario)
                def processar_resposta(message):
                    try:
                        conn, cursor = conectar_banco_dados()
                        resposta = message.text
                        
                        usuario_destino, quantidade = resposta.split()

                        cursor.execute("SELECT id_usuario FROM usuarios WHERE username = %s", (usuario_destino,))
                        usuario_existe = cursor.fetchone()
                        
                        if usuario_existe:
                            if int(quantidade) <= qnt_cenouras:
                                diminuir_cenouras(id_usuario, quantidade)
                                aumentar_cenouras(usuario_existe[0], quantidade)
                                caption = f"Você doou {quantidade} cenouras para {usuario_destino}."
                            else:
                                caption = "Você não tem essa quantidade de cenouras."
 
                        else:
                            caption = "O usuário digitado não existe, verifique e tente novamente."
                        
                        bot.send_message(chat_id, caption)
                    except Exception as e:
                        print(f"Erro ao processar resposta do usuário: {e}")
            else:
                bot.send_message(chat_id, "Você não tem cenouras suficientes para doar.")
        else:
            bot.send_message(chat_id, "Desculpe, ocorreu um erro ao verificar suas cenouras.")
    except Exception as e:
        print(f"Erro ao processar doar_cenoura: {e}")
        
        
def compra_callback(call):
    try:
        chat_id = call.message.chat.id
        message_data = call.data
        parts = message_data.split('_')
        categoria = parts[1]
        id_usuario = parts[2]
        original_message_id = parts[3]
        conn, cursor = conectar_banco_dados()
        cursor.execute("SELECT cenouras FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        result = cursor.fetchone()

        if result:
            qnt_cenouras = int(result[0])
        else:
            qnt_cenouras = 0

        if qnt_cenouras >= 3:
            mensagem = f"Você tem {qnt_cenouras} cenouras. Deseja usar 3 para ganhar um peixe aleatório?"
            keyboard = telebot.types.InlineKeyboardMarkup()
            keyboard.row(
                telebot.types.InlineKeyboardButton(text="Sim", callback_data=f'confirmar_compra_{categoria}_{id_usuario}_{original_message_id}'),
                telebot.types.InlineKeyboardButton(text="Não", callback_data='cancelar_compra')
            )
            bot.edit_message_text(chat_id=chat_id, message_id=original_message_id, text=" ", reply_markup=keyboard)
        else:
            mensagem = "Desculpe, você não tem cenouras suficientes para comprar um peixe. Volte quando tiver pelo menos 3 cenouras!"
            bot.edit_message_text(chat_id=chat_id, message_id=original_message_id, text=mensagem)
    except Exception as e:
        print(f"Erro ao processar compra_callback: {e}")

def confirmar_compra_callback(call):
    try:
        chat_id = call.message.chat.id
        message_data = call.data
        parts = message_data.split('_')
        categoria = parts[1]
        id_usuario = parts[2]
        original_message_id = parts[3]
        conn, cursor = conectar_banco_dados()
        cursor.execute("SELECT cenouras FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        result = cursor.fetchone()

        if result:
            qnt_cenouras = int(result[0])
        else:
            qnt_cenouras = 0

        if qnt_cenouras >= 3:
            cursor.execute("UPDATE usuarios SET cenouras = cenouras - 3 WHERE id_usuario = %s", (id_usuario,))
            cursor.execute("SELECT id_personagem FROM personagens WHERE subcategoria = %s ORDER BY RAND() LIMIT 1", (categoria,))
            result = cursor.fetchone()

            if result:
                id_personagem = result[0]
                cursor.execute("INSERT INTO colecao_usuario (id_usuario, id_personagem) VALUES (%s, %s)", (id_usuario, id_personagem))
                conn.commit()

                mensagem = f"Parabéns! Você comprou um peixe aleatório da categoria {categoria} por 3 cenouras."
                bot.edit_message_text(chat_id=chat_id, message_id=original_message_id, text=mensagem)
            else:
                mensagem = "Desculpe, ocorreu um erro ao processar sua compra. Tente novamente mais tarde."
                bot.edit_message_text(chat_id=chat_id, message_id=original_message_id, text=mensagem)
        else:
            mensagem = "Desculpe, você não tem cenouras suficientes para comprar um peixe. Volte quando tiver pelo menos 3 cenouras!"
            bot.edit_message_text(chat_id=chat_id, message_id=original_message_id, text=mensagem)
    except Exception as e:
        print(f"Erro ao processar confirmar_compra_callback: {e}")
        
        
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


# Função para exibir a vendinha
def loja(message):
    try:
        # Verifica se o usuário está banido
        verificar_id_na_tabela(message.from_user.id, "ban", "iduser")
        
        # Cria o teclado interativo
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(telebot.types.InlineKeyboardButton(text="🎣 Peixes do dia", callback_data='loja_loja'))
        keyboard.row(telebot.types.InlineKeyboardButton(text="🎴 Estou com sorte", callback_data='loja_geral'))
        keyboard.row(telebot.types.InlineKeyboardButton(text="⛲ Fonte dos Desejos", callback_data='fazer_pedido'))
        keyboard.row(telebot.types.InlineKeyboardButton(text="💼 Pacotes de Ações", callback_data='acoes_vendinha'))

        # URL da imagem da vendinha
        image_url = "https://pub-6f23ef52e8614212a14d24b0cf55ae4a.r2.dev/AgACAgEAAxkBAAIevWckR24NZLiulyoyM6p4gICs3xU5AAItrjEby-MpRZ9k194KIDqPAQADAgADeQADNgQ.jpg"
        
        # Envia a imagem e o teclado interativo
        bot.send_photo(message.chat.id, image_url,
                       caption='Olá! Seja muito bem-vindo à vendinha da Mabi. Como posso te ajudar?',
                       reply_markup=keyboard, reply_to_message_id=message.message_id)

    except ValueError as e:
        # Se o usuário estiver banido, envia uma mensagem de erro
        print(f"Erro: {e}")
        mensagem_banido = "Você foi banido permanentemente do garden. Entre em contato com o suporte caso haja dúvidas."
        bot.send_message(message.chat.id, mensagem_banido, reply_to_message_id=message.message_id)

def handle_callback_loja_loja(call):
    try:
        message_data = call.data.replace('loja_', '')
        if message_data == "loja":
            data_atual = datetime.today().strftime("%Y-%m-%d")
            id_usuario = call.from_user.id
            ids_do_dia = obter_ids_loja_do_dia(data_atual)
            imagem_url = 'https://pub-6f23ef52e8614212a14d24b0cf55ae4a.r2.dev/BQACAgEAAxkBAAIe1Wclk2eiQkwGjTXrZqQvdjaeLtrbAALHBAAC7WgxRfD2-mIpIl3TNgQ.jpg'
            original_message_id = call.message.message_id
            keyboard = telebot.types.InlineKeyboardMarkup()
            primeira_coluna = [
                telebot.types.InlineKeyboardButton(text="☁️", callback_data=f'compra_musica_{id_usuario}_{original_message_id}'),
                telebot.types.InlineKeyboardButton(text="🍄", callback_data=f'compra_series_{id_usuario}_{original_message_id}'),
                telebot.types.InlineKeyboardButton(text="🍰", callback_data=f'compra_filmes_{id_usuario}_{original_message_id}')
            ]
            segunda_coluna = [
                telebot.types.InlineKeyboardButton(text="🍂", callback_data=f'compra_miscelanea_{id_usuario}_{original_message_id}'),
                telebot.types.InlineKeyboardButton(text="🧶", callback_data=f'compra_jogos_{id_usuario}_{original_message_id}'),
                telebot.types.InlineKeyboardButton(text="🌷", callback_data=f'compra_animanga_{id_usuario}_{original_message_id}')
            ]
            keyboard.row(*primeira_coluna)
            keyboard.row(*segunda_coluna)

            mensagem = "𝐀𝐡, 𝐨𝐥𝐚́! 𝐕𝐨𝐜𝐞̂ 𝐜𝐡𝐞𝐠𝐨𝐮 𝐧𝐚 𝐡𝐨𝐫𝐚 𝐜𝐞𝐫𝐭𝐚! \n\nNosso pescador acabou de chegar com os peixes fresquinhos de hoje:\n\n"

            for carta_id in ids_do_dia:
                id_personagem, emoji, nome, subcategoria = obter_informacoes_carta(carta_id)
                mensagem += f"{emoji} - {nome} de {subcategoria}\n"

            bot.edit_message_media(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=keyboard,
                media=telebot.types.InputMediaPhoto(media=imagem_url, caption=mensagem)
            )
    except Exception as e:
        newrelic.agent.record_exception()    
        print(f"Erro ao processar loja_loja_callback: {e}")

def verificar_desconto_loja(user_id):
    """
    Verifica se o usuário tem um desconto ativo na loja.
    """
    conn, cursor = conectar_banco_dados()
    try:
        cursor.execute("""
            SELECT fim_desconto FROM descontos_loja 
            WHERE id_usuario = %s AND fim_desconto > NOW()
        """, (user_id,))
        resultado = cursor.fetchone()
        return resultado is not None
    except Exception as e:
        print(f"Erro ao verificar desconto na loja: {e}")
        return False
    finally:
        fechar_conexao(cursor, conn)

def handle_callback_compra(call):
    try:
        chat_id = call.message.chat.id
        parts = call.data.split('_')
        categoria = parts[1]
        id_usuario = parts[2]
        original_message_id = parts[3]
        conn, cursor = conectar_banco_dados()
        
        # Verifica se o usuário possui desconto ativo
        desconto_ativo = verificar_desconto_loja(id_usuario)
        preco = 3 if desconto_ativo else 5  # Aplica desconto se ativo

        cursor.execute("SELECT cenouras FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        result = cursor.fetchone()
        qnt_cenouras = int(result[0]) if result else 0

        if qnt_cenouras >= preco:
            # Seleciona uma carta aleatória da categoria do dia
            cursor.execute(
                "SELECT loja.id_personagem, personagens.nome, personagens.subcategoria, personagens.emoji "
                "FROM loja "
                "JOIN personagens ON loja.id_personagem = personagens.id_personagem "
                "WHERE loja.categoria = %s AND loja.data = %s ORDER BY RAND() LIMIT 1",
                (categoria, datetime.today().strftime("%Y-%m-%d"))
            )
            carta_comprada = cursor.fetchone()

            if carta_comprada:
                id_personagem, nome, subcategoria, emoji = carta_comprada
                mensagem = f"Você tem {qnt_cenouras} cenouras.\nDeseja usar {preco} para comprar o peixe:\n\n{emoji} {id_personagem} - {nome} de {subcategoria}?"
                keyboard = telebot.types.InlineKeyboardMarkup()
                keyboard.row(
                    telebot.types.InlineKeyboardButton(text="Sim", callback_data=f'confirmar_compra_{categoria}_{id_usuario}'),
                    telebot.types.InlineKeyboardButton(text="Não", callback_data='cancelar_compra')
                )
                imagem_url = "https://telegra.ph/file/d4d5d0af60ec66f35e29c.jpg"
                bot.edit_message_media(
                    chat_id=chat_id,
                    message_id=original_message_id,
                    reply_markup=keyboard,
                    media=telebot.types.InputMediaPhoto(media=imagem_url, caption=mensagem)
                )
            else:
                print(f"Nenhuma carta disponível para compra na categoria {categoria} hoje.")
        else:
            bot.send_message(chat_id, "Desculpe, você não tem cenouras suficientes para realizar esta compra.")
    except Exception as e:
        print(f"Erro ao processar a compra: {e}")
    finally:
        fechar_conexao(cursor, conn)

def handle_callback_confirmar_compra(call):
    try:
        parts = call.data.split('_')
        categoria = parts[2]
        id_usuario = parts[3]
        data_atual = datetime.today().strftime("%Y-%m-%d")
        conn, cursor = conectar_banco_dados()
        cursor.execute(
            "SELECT p.id_personagem, p.nome, p.subcategoria, p.imagem, p.emoji "
            "FROM loja AS l "
            "JOIN personagens AS p ON l.id_personagem = p.id_personagem "
            "WHERE l.categoria = %s AND l.data = %s ORDER BY RAND() LIMIT 1",
            (categoria, data_atual)
        )
        carta_comprada = cursor.fetchone()

        if carta_comprada:
            id_personagem, nome, subcategoria, imagem, emoji = carta_comprada
            mensagem = f"𝐂𝐨𝐦𝐩𝐫𝐚 𝐟𝐞𝐢𝐭𝐚 𝐜𝐨𝐦 𝐬𝐮𝐜𝐞𝐬𝐬𝐨! \n\nO seguinte peixe foi adicionado à sua cesta: \n\n{emoji} {id_personagem} • {nome}\nde {subcategoria}\n\n𝐕𝐨𝐥𝐭𝐞 𝐬𝐞𝐦𝐩𝐫𝐞!"
            add_to_inventory(id_usuario, id_personagem)
            diminuir_cenouras(id_usuario, 5)

            bot.edit_message_media(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                media=telebot.types.InputMediaPhoto(media=imagem, caption=mensagem)
            )
        else:
            print(f"Nenhuma carta disponível para compra na categoria {categoria} hoje.")
    except Exception as e:
        print(f"Erro ao processar a compra para o usuário {id_usuario}: {e}")
        newrelic.agent.record_exception()
    finally:
        fechar_conexao(cursor, conn)

def obter_informacoes_loja(ids_do_dia):
    try:
        conn, cursor = conectar_banco_dados()
        placeholders = ', '.join(['%s' for _ in ids_do_dia])
        cursor.execute(
            f"SELECT id_personagem, emoji, nome, subcategoria FROM personagens WHERE id_personagem IN ({placeholders})",
            tuple(ids_do_dia))
        cartas_loja = cursor.fetchall()
        return cartas_loja

    except mysql.connector.Error as err:
        print(f"Erro ao obter informações da loja: {err}")
    finally:
        cursor.close()
        conn.close()
import telebot
import newrelic.agent

# Função para exibir pacotes de ações disponíveis
def exibir_acoes_vendinha(call):
    try:
        mensagem = "📦 Pacotes de Ações disponíveis:\n\n"
        mensagem += "🥕 Pacote Básico: 10 cartas\n"
        mensagem += "💸 Pacote Médio: 25 cartas\n"
        mensagem += "💳 Pacote Premium: 80 cartas\n\n"
        
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            telebot.types.InlineKeyboardButton(text="🥕", callback_data='comprar_acao_vendinha_basico'),
            telebot.types.InlineKeyboardButton(text="💸", callback_data='comprar_acao_vendinha_prata'),
            telebot.types.InlineKeyboardButton(text="💳", callback_data='comprar_acao_vendinha_ouro')
        )
        
        bot.edit_message_caption(caption=mensagem, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=keyboard)
    except Exception as e:
        print(f"Erro ao exibir pacotes de ações: {e}")
        newrelic.agent.record_exception()    
        bot.send_message(call.message.chat.id, "Erro ao exibir pacotes de ações.")

# Função para confirmar a compra de um pacote de ações
def confirmar_compra_vendinha(call):
    pacote = call.data.split('_')[3]
    pacotes = {
        'basico': ('Pacote Básico', 50),
        'prata': ('Pacote Médio', 100),
        'ouro': ('Pacote Premium', 200)
    }

    if pacote in pacotes:
        nome_pacote, preco = pacotes[pacote]
        mensagem = f"Selecione a categoria para o {nome_pacote}:\n\n"
        mensagem += f"★ Geral - {preco} cenouras\n"
        mensagem += f"★ Por categoria - {preco * 2} cenouras\n"

        # Criação do teclado com categorias
        keyboard = telebot.types.InlineKeyboardMarkup()
        primeira_coluna = [
            telebot.types.InlineKeyboardButton(text="☁ Música", callback_data=f'confirmar_categoria_{pacote}_musica'),
            telebot.types.InlineKeyboardButton(text="🌷 Anime", callback_data=f'confirmar_categoria_{pacote}_animanga'),
            telebot.types.InlineKeyboardButton(text="🧶 Jogos", callback_data=f'confirmar_categoria_{pacote}_jogos')
        ]
        segunda_coluna = [
            telebot.types.InlineKeyboardButton(text="🍰 Filmes", callback_data=f'confirmar_categoria_{pacote}_filmes'),
            telebot.types.InlineKeyboardButton(text="🍄 Séries", callback_data=f'confirmar_categoria_{pacote}_series'),
            telebot.types.InlineKeyboardButton(text="🍂 Misc", callback_data=f'confirmar_categoria_{pacote}_miscelanea')
        ]
        geral = telebot.types.InlineKeyboardButton(text="🫧 Geral", callback_data=f'confirmar_categoria_{pacote}_geral')
        cancel = telebot.types.InlineKeyboardButton(text="Cancelar Compra", callback_data=f'cancelar_compra_vendinha')
        
        keyboard.add(*primeira_coluna)
        keyboard.add(*segunda_coluna)
        keyboard.row(geral)
        keyboard.row(cancel)
        
        bot.edit_message_caption(caption=mensagem, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=keyboard)
