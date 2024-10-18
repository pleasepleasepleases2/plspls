import random
from pesquisas import *
from user import *
from bd import *
from loja import *
from gnome import *
from operacoes import *
from inventario import *
from gif import *
from cachetools import cached, TTLCache
from evento import *
from gif import *
import traceback
import time
ultimo_clique = {}

grupodeerro = -4279935414
GRUPO_PESCAS_ID = -4209628464  

cache = TTLCache(maxsize=1000, ttl=600)  
cache_cartas = TTLCache(maxsize=1000, ttl=3600)
cache_submenus = TTLCache(maxsize=1000, ttl=3600)
cache_eventos = TTLCache(maxsize=1000, ttl=3600)

@cached(cache_cartas)
def obter_cartas_subcateg(subcategoria, conn):
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id_personagem, emoji, nome, imagem FROM personagens WHERE subcategoria = %s", (subcategoria,))
        return cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Erro ao obter cartas da subcategoria: {err}")
        return []
    finally:
        cursor.close()
        
@cached(cache_cartas)
def buscar_subcategorias(categoria):
    try:
        if categoria=="geral":
            conn, cursor = conectar_banco_dados()
            cursor.execute("SELECT DISTINCT subcategoria FROM personagens")
            subcategorias = cursor.fetchall()
            # Utilizando um conjunto para garantir unicidade
            subcategorias_unicas = {subcategoria[0] for subcategoria in subcategorias}
            return list(subcategorias_unicas)
        else:
            conn, cursor = conectar_banco_dados()
            cursor.execute("SELECT DISTINCT subcategoria FROM personagens WHERE categoria = %s", (categoria,))
            subcategorias = cursor.fetchall()
            # Utilizando um conjunto para garantir unicidade
            subcategorias_unicas = {subcategoria[0] for subcategoria in subcategorias}
            return list(subcategorias_unicas)
    except mysql.connector.Error as err:
        print(f"Erro ao buscar subcategorias: {err}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close() 

def categoria_handler(message, categoria):
    try:
        conn, cursor = conectar_banco_dados()
        chat_id = message.chat.id
        evento_ativo = True
        if categoria.lower() == 'geral': 
            subcategorias = buscar_subcategorias(categoria)
            subcategorias = [subcategoria for subcategoria in subcategorias if subcategoria]

            if subcategorias:
                resposta_texto = "Sua isca atraiu 6 espécies, qual peixe você vai levar?\n\n"
                subcategorias_aleatorias = random.sample(subcategorias, min(6, len(subcategorias)))

                for i, subcategoria in enumerate(subcategorias_aleatorias, start=1):
                    resposta_texto += f"{i}\uFE0F\u20E3 - {subcategoria}\n"

                markup = telebot.types.InlineKeyboardMarkup(row_width=6)
                row_buttons = []
                for i, subcategoria in enumerate(subcategorias_aleatorias, start=1):
                    button_text = f"{i}\uFE0F\u20E3"
                    row_buttons.append(telebot.types.InlineKeyboardButton(button_text, callback_data=f"choose_subcategoria_{subcategoria}"))

                markup.row(*row_buttons)
                imagem_url="https://telegra.ph/file/8a50bf408515b52a36734.jpg"
                bot.edit_message_media(
                        chat_id=message.chat.id,
                        message_id=message.message_id,
                        reply_markup=markup,
                        media=telebot.types.InputMediaPhoto(media=imagem_url, caption=resposta_texto)
                    )
                return None  
            else:
                bot.send_message(message.chat.id, f"Nenhuma subcategoria encontrada para a categoria '{categoria}'.")
                return None
        else:
            subcategorias = buscar_subcategorias(categoria)
            subcategorias = [subcategoria for subcategoria in subcategorias if subcategoria]
            if subcategorias:
                resposta_texto = "Sua isca atraiu 6 espécies, qual peixe você vai levar?\n\n"
                subcategorias_aleatorias = random.sample(subcategorias, min(6, len(subcategorias)))

                for i, subcategoria in enumerate(subcategorias_aleatorias, start=1):
                    resposta_texto += f"{i}\uFE0F\u20E3 - {subcategoria}\n"

                markup = telebot.types.InlineKeyboardMarkup(row_width=6)
                row_buttons = []
                for i, subcategoria in enumerate(subcategorias_aleatorias, start=1):
                    button_text = f"{i}\uFE0F\u20E3"
                    callback_data = f"choose_subcategoria_{subcategoria}"
                    row_buttons.append(telebot.types.InlineKeyboardButton(button_text, callback_data=callback_data))

                markup.row(*row_buttons)

                imagem_url = "https://telegra.ph/file/8a50bf408515b52a36734.jpg"
                bot.edit_message_media(
                        chat_id=message.chat.id,
                        message_id=message.message_id,
                        reply_markup=markup,
                        media=telebot.types.InputMediaPhoto(media=imagem_url, caption=resposta_texto)
                    )
                return None 
    except mysql.connector.Error as err:
        bot.send_message(message.chat.id, f"Erro ao buscar subcategorias: {err}")
        return None
    finally:
        fechar_conexao(cursor, conn)

def criar_markup(subcategorias, tipo):
    markup = telebot.types.InlineKeyboardMarkup()
    row_buttons = []
    emoji_numbers = ['☃️', '❄️'] if tipo == "valentine" else [f"{i}\uFE0F\u20E3" for i in range(1, 7)]
    for i, subcategoria in enumerate(subcategorias):
        button_text = emoji_numbers[i] if tipo == "valentine" else f"{i+1}\uFE0F\u20E3"
        callback_data = f"subcategory_{subcategoria}_{tipo}"
        row_buttons.append(telebot.types.InlineKeyboardButton(button_text, callback_data=callback_data))
    markup.add(*row_buttons)
    return markup
def subcategoria_handler(message, subcategoria, cursor, conn, categoria, chat_id, message_id):
    id_usuario = message.chat.id
    try:
        conn, cursor = conectar_banco_dados()
        if subcategoria.lower() == 'geral':
            print("Verificando chance de evento fixo.")
            if random.randint(1, 100) <= 10:
                evento_aleatorio = obter_carta_evento_fixo(conn, subcategoria)
                if evento_aleatorio:
                    print("Evento fixo encontrado. Enviando carta aleatória.")
                    send_card_message(message, evento_aleatorio, cursor=cursor, conn=conn)
                    return
            # Adicione este print para verificar se está entrando nesta condição
            print("Nenhum evento fixo. Procedendo com a lógica normal.")
        else:
            if verificar_se_subcategoria_tem_submenu(cursor, subcategoria):
                submenus = obter_submenus_para_subcategoria(cursor, subcategoria)
                if submenus:
                    submenu_opcoes = random.sample(submenus, min(3, len(submenus)))
                    enviar_opcoes_submenu(message, submenu_opcoes, subcategoria, chat_id, message_id)
                    return
    
            cartas_disponiveis = obter_cartas_subcateg(subcategoria, conn)
            
            if cartas_disponiveis:
                carta_aleatoria = random.choice(cartas_disponiveis)
                if carta_aleatoria:
                    id_personagem_carta, emoji, nome, imagem = carta_aleatoria
                    send_card_message(message, emoji, id_personagem_carta, nome, subcategoria, imagem)
                    qnt_carta(id_usuario)
                else:
                    print(f"Nenhuma carta disponível para esta subcategoria: {subcategoria}.")
            else:
                print(f"Nenhuma carta disponível para esta subcategoria: {subcategoria}.")
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        fechar_conexao(cursor, conn)

def verificar_se_subcategoria_tem_submenu(cursor, subcategoria):
    try:
        cursor.execute("SELECT COUNT(*) FROM subcategoria_submenu WHERE subcategoria = %s", (subcategoria,))
        return cursor.fetchone()[0] > 0
    except mysql.connector.Error as err:
        print(f"Erro ao verificar submenu da subcategoria: {err}")
        return False

def obter_submenus_para_subcategoria(cursor, subcategoria):
    try:
        cursor.execute("SELECT submenu FROM subcategoria_submenu WHERE subcategoria = %s", (subcategoria,))
        resultados = cursor.fetchall()
        return [submenu[0] for submenu in resultados]
    except mysql.connector.Error as err:
        print(f"Erro ao obter submenus da subcategoria: {err}")
        return []

def enviar_opcoes_submenu(message, submenu_opcoes, subcategoria, chat_id, message_id):
    try:
        # Definir a quantidade de botões com base na quantidade de opções
        row_width = 3 if len(submenu_opcoes) >= 3 else 2
        opcoes = [telebot.types.InlineKeyboardButton(text=opcao, callback_data=f"submenu_{subcategoria}_{opcao}") for opcao in submenu_opcoes]
        markup = telebot.types.InlineKeyboardMarkup(row_width=row_width)
        markup.add(*opcoes)
        
        # Editar a mensagem original para apresentar as opções de submenu
        bot.edit_message_caption(
            chat_id=chat_id,
            message_id=message_id,
            caption=f"A espécie <b>{subcategoria}</b> possuí variedades, qual dessas você deseja levar?", 
            parse_mode="HTML",
            reply_markup=markup
        )
    except Exception as e:
        print(f"Erro ao enviar opções de submenu: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('submenu_'))
def callback_submenu_handler(call):
    try:
        data = call.data.split('_')
        subcategoria = data[1]
        submenu = data[2]

        conn = conectar_banco_dados()
        cursor = conn.cursor()
        carta = obter_carta_por_submenu(cursor, subcategoria, submenu)

        if carta:
            id_personagem, emoji, nome, imagem = carta
            send_card_message(call.message, emoji, id_personagem, nome, f"{subcategoria}_{submenu}", imagem)
        else:
            bot.send_message(call.message.chat.id, "Nenhuma carta encontrada para a combinação de subcategoria e submenu.")

    except Exception as e:
        print(f"Erro ao processar callback do submenu: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def obter_carta_por_submenu(cursor, subcategoria, submenu):
    try:
        cursor.execute("SELECT id_personagem, emoji, nome, imagem FROM personagens WHERE subcategoria = %s AND submenu = %s ORDER BY RAND() LIMIT 1", (subcategoria, submenu))
        return cursor.fetchone()
    except mysql.connector.Error as err:
        print(f"Erro ao obter carta por submenu: {err}")
        return None

def send_card_message(message, *args, cursor=None, conn=None):
    try:
        # Verifica se é um evento fixo (dicionário passado)
        if len(args) == 1 and isinstance(args[0], dict):
            evento_aleatorio = args[0]
            subcategoria_display = evento_aleatorio['subcategoria'].split('_')[-1]
            id_usuario = message.chat.id
            id_personagem = evento_aleatorio['id_personagem']
            nome = evento_aleatorio['nome']
            subcategoria = evento_aleatorio['subcategoria']
            add_to_inventory(id_usuario, id_personagem)
            quantidade = verifica_inventario_troca(id_usuario, id_personagem)
            quantidade_display = "☀" if quantidade == 1 else "☀ 𖡩"

            # Se não houver imagem, use uma imagem padrão
            if not evento_aleatorio['imagem']:
                imagem = "https://telegra.ph/file/8a50bf408515b52a36734.jpg"
            else:
                imagem = evento_aleatorio['imagem']

            text = f"🎣 Parabéns! Sua isca era boa e você recebeu:\n\n☃️ {evento_aleatorio['id_personagem']} - {evento_aleatorio['nome']}\nde {subcategoria_display}\n\n{quantidade_display}"
            try:
                bot.edit_message_media(
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    media=telebot.types.InputMediaPhoto(media=imagem, caption=text)
                )
            except Exception:
                bot.send_photo(chat_id=message.chat.id, photo=imagem, caption=text)
            
            # Registrar no histórico
            register_card_history(message, id_usuario, id_personagem)
        
        # Verifica se é uma carta aleatória (5 argumentos)
        elif len(args) == 5:
            emoji_categoria, id_personagem, nome, subcategoria, imagem = args
            subcategoria_display = subcategoria.split('_')[-1]
            id_usuario = message.chat.id
            add_to_inventory(id_usuario, id_personagem)
            quantidade = verifica_inventario_troca(id_usuario, id_personagem)
            
            if not imagem:
                imagem_url = "https://telegra.ph/file/8a50bf408515b52a36734.jpg"
                text = f"🎣 Parabéns! Sua isca era boa e você recebeu:\n\n{emoji_categoria}<code> {id_personagem}</code> - {nome}\nde {subcategoria_display}\nQuantidade de cartas: {quantidade}"
                try:
                    bot.edit_message_media(
                        chat_id=message.chat.id,
                        message_id=message.message_id,
                        media=telebot.types.InputMediaPhoto(media=imagem_url, caption=text, parse_mode="HTML")
                    )
                except Exception:
                    bot.send_photo(chat_id=message.chat.id, photo=imagem_url, caption=text, parse_mode="HTML")
            else:
                text = f"🎣 Parabéns! Sua isca era boa e você recebeu:\n\n{emoji_categoria} <code>{id_personagem}</code> - {nome}\nde {subcategoria_display}\n\n☀ | {quantidade}⤫"
                try:
                    if imagem.lower().endswith(('.jpg', '.jpeg', '.png')):
                        bot.edit_message_media(
                            chat_id=message.chat.id,
                            message_id=message.message_id,
                            media=telebot.types.InputMediaPhoto(media=imagem, caption=text, parse_mode="HTML")
                        )
                    elif imagem.lower().endswith(('.mp4', '.gif')):
                        bot.edit_message_media(
                            chat_id=message.chat.id,
                            message_id=message.message_id,
                            media=telebot.types.InputMediaVideo(media=imagem, caption=text, parse_mode="HTML")
                        )
                except Exception:
                    if imagem.lower().endswith(('.jpg', '.jpeg', '.png')):
                        bot.send_photo(chat_id=message.chat.id, photo=imagem, caption=text, parse_mode="HTML")
                    elif imagem.lower().endswith(('.mp4', '.gif')):
                        bot.send_video(chat_id=message.chat.id, video=imagem, caption=text, parse_mode="HTML")
            
            register_card_history(message.from_user, id_usuario, id_personagem)
            if quantidade == 30:
                bot.send_message(id_usuario, "🎉 Parabéns! Você alcançou 30 cartas do personagem, pode pedir um gif usando o comando /setgif!")
        
        else:
            print("Número incorreto de argumentos.")
    
    except Exception as e:
        traceback.print_exc()
        erro = traceback.format_exc()
        mensagem = f"Erro ao enviar carta: {e}\n{erro}"
        bot.send_message(grupodeerro, mensagem, parse_mode="HTML")



def verificar_se_subcategoria_tem_submenu(cursor, subcategoria):
    try:
        cursor.execute("SELECT COUNT(*) FROM subcategoria_submenu WHERE subcategoria = %s", (subcategoria,))
        return cursor.fetchone()[0] > 0
    except mysql.connector.Error as err:
        print(f"Erro ao verificar submenu da subcategoria: {err}")
        return False

@cached(cache_submenus)
def obter_submenus_para_subcategoria(cursor, subcategoria):
    try:
        cursor.execute("SELECT submenu FROM subcategoria_submenu WHERE subcategoria = %s", (subcategoria,))
        resultados = cursor.fetchall()
        return [submenu[0] for submenu in resultados]
    except mysql.connector.Error as err:
        print(f"Erro ao obter submenus da subcategoria: {err}")
        return []

def add_to_inventory(id_usuario, id_personagem, max_retries=5):
    attempt = 0
    id_usuario = int(id_usuario)
    id_personagem = int(id_personagem)
    
    while attempt < max_retries:
        try:
            conn, cursor = conectar_banco_dados()

            # Iniciar uma transação
            conn.start_transaction()

            # Ordenar as operações em ordem específica para evitar deadlocks
            if id_usuario < id_personagem:
                cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s FOR UPDATE",
                               (id_usuario, id_personagem))
            else:
                cursor.execute("SELECT quantidade FROM inventario WHERE id_personagem = %s AND id_usuario = %s FOR UPDATE",
                               (id_personagem, id_usuario))

            existing_carta = cursor.fetchone()

            if existing_carta:
                nova_quantidade = existing_carta[0] + 1
                cursor.execute("UPDATE inventario SET quantidade = %s WHERE id_usuario = %s AND id_personagem = %s",
                               (nova_quantidade, id_usuario, id_personagem))
            else:
                cursor.execute("INSERT INTO inventario (id_personagem, id_usuario, quantidade) VALUES (%s, %s, 1)",
                               (id_personagem, id_usuario))

            cursor.execute("UPDATE personagens SET total = IFNULL(total, 0) + 1 WHERE id_personagem = %s", (id_personagem,))

            # Confirmar a transação
            conn.commit()
            break  # Saia do loop se a transação for bem-sucedida

        except mysql.connector.errors.DatabaseError as db_err:
            if db_err.errno == 1205:  # Código de erro para lock wait timeout exceeded
                attempt += 1
                time.sleep(1)  # Esperar um pouco antes de tentar novamente
                if attempt >= max_retries:
                    mensagem = "Erro: Excedido o número máximo de tentativas para resolver o deadlock."
                    bot.send_message(grupodeerro, mensagem, parse_mode="HTML")
            else:
                mensagem = f"Erro ao adicionar carta ao inventário: {db_err}"
                bot.send_message(grupodeerro, mensagem, parse_mode="HTML")
                break
        except Exception as e:
            traceback.print_exc()
            erro = traceback.format_exc()
            mensagem = f"Adição de personagem com erro: {id_personagem} - usuário {id_usuario}. erro: {e}\n{erro}"
            bot.send_message(grupodeerro, mensagem, parse_mode="HTML")
            break
        finally:
            fechar_conexao(cursor, conn)
def obter_cartas_por_subcategoria_e_submenu(subcategoria, submenu, cursor):
    try:
        cursor.execute("SELECT id_personagem, emoji, nome, imagem FROM personagens WHERE subcategoria = %s AND submenu = %s", (subcategoria, submenu))
        return cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Erro ao obter cartas por subcategoria e submenu: {err}")
        return []


def verificar_subcategoria_evento(subcategoria, cursor):
    try:
        cursor.execute(
            "SELECT id_personagem, nome, subcategoria, imagem FROM evento WHERE subcategoria = %s AND evento = 'fixo' ORDER BY RAND() LIMIT 1",
            (subcategoria,))
        evento_aleatorio = cursor.fetchone()
        if evento_aleatorio:
            chance = random.randint(1, 100)

            if chance <= 20:
                id_personagem, nome, subcategoria, imagem = evento_aleatorio
                evento_formatado = {
                    'id_personagem': id_personagem,
                    'nome': nome,
                    'subcategoria': subcategoria,
                    'imagem': imagem
                }
                return evento_formatado
            else:
                return None
        else:
            return None
    except Exception as e:
        print(f"Erro ao verificar subcategoria na tabela de eventos: {e}")
        return None

def obter_carta_evento_fixo(subcategoria=None):
    try:
        conn, cursor = conectar_banco_dados()
        if subcategoria:
            cursor.execute("SELECT emoji, id_personagem, nome, subcategoria, imagem FROM evento WHERE subcategoria = %s AND evento = 'fixo' ORDER BY RAND() LIMIT 1", (subcategoria,))
        else:
            cursor.execute("SELECT emoji, id_personagem, nome, subcategoria, imagem FROM evento WHERE evento = 'fixo' ORDER BY RAND() LIMIT 1")
        evento_aleatorio = cursor.fetchone()
        return evento_aleatorio
    except mysql.connector.Error as err:
        print(f"Erro ao obter carta de evento fixo: {err}")
        return None
    finally:
        fechar_conexao(cursor, conn)

def register_card_history(message,id_usuario, id_carta):
    try:
        conn, cursor = conectar_banco_dados()
        data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO historico_cartas_giradas (id_usuario, id_carta, data_hora) VALUES (%s, %s, %s)",
                       (id_usuario, id_carta, data_hora))
        conn.commit()
        user_info = bot.get_chat(id_usuario)
        # Obter detalhes da carta
        cursor.execute("SELECT nome, subcategoria FROM evento WHERE id_personagem = %s", (id_carta,))
        detalhes_carta = cursor.fetchone()
        if not detalhes_carta:
            return
        
        if detalhes_carta:
            nome_carta, subcategoria_carta = detalhes_carta  
            
            mensagem = f"🎣 Pesca realizada por: <code>{id_usuario}</code>-@{user_info.username}\n"
            mensagem += f"📅 Data e Hora: {data_hora}\n"
            mensagem += f"🃏 Carta: {id_carta} {nome_carta}\n"
            mensagem += f"🗂 Subcategoria: {subcategoria_carta}\n\n\n\n"
            mensagem += f"<code>/enviar_mensagem {id_usuario}</code>\n"
            # Enviar mensagem para o grupo
            bot.send_message(GRUPO_PESCAS_ID, mensagem,parse_mode="HTML")
        else:
            print(f"Detalhes da carta com id {id_carta} não encontrados.")
            
    except mysql.connector.Error as err:
        print(f"Erro ao registrar o histórico da carta: {err}")
    finally:
        fechar_conexao(cursor, conn)
import telebot
from datetime import datetime
from bd import verificar_id_na_tabela, verificar_tempo_passado, diminuir_giros, verificar_giros, verificar_id_na_tabelabeta

ultima_interacao = {}

# Função para o comando de pesca
def pescar(message):
    try:
        print("Comando pescar acionado")
        nome = message.from_user.first_name
        user_id = message.from_user.id

        # Verificar se o usuário está banido
        verificar_id_na_tabela(user_id, "ban", "iduser")
        if message.chat.type != 'private':
            bot.send_message(message.chat.id, "Este comando só pode ser usado em uma conversa privada.")
            return

        # Verificar a quantidade de iscas disponíveis
        qtd_iscas = verificar_giros(user_id)
        if qtd_iscas == 0:
            bot.send_message(message.chat.id, "Você está sem iscas.", reply_to_message_id=message.message_id)
        else:
            # Verificar se o tempo desde a última interação é suficiente
            if not verificar_tempo_passado(message.chat.id):
                return
            else:
                ultima_interacao[message.chat.id] = datetime.now()

            # Verificar se o usuário é beta tester
            if verificar_id_na_tabelabeta(user_id):
                # Diminuir o número de iscas
                diminuir_giros(user_id, 1)

                # Criar o teclado de categorias para escolha
                keyboard = telebot.types.InlineKeyboardMarkup()

                primeira_coluna = [
                    telebot.types.InlineKeyboardButton(text="☁  Música", callback_data='pescar_musica'),
                    telebot.types.InlineKeyboardButton(text="🌷 Anime", callback_data='pescar_animanga'),
                    telebot.types.InlineKeyboardButton(text="🧶  Jogos", callback_data='pescar_jogos')
                ]
                segunda_coluna = [
                    telebot.types.InlineKeyboardButton(text="🍰  Filmes", callback_data='pescar_filmes'),
                    telebot.types.InlineKeyboardButton(text="🍄  Séries", callback_data='pescar_series'),
                    telebot.types.InlineKeyboardButton(text="🍂  Misc", callback_data='pescar_miscelanea')
                ]

                keyboard.add(*primeira_coluna)
                keyboard.add(*segunda_coluna)
                keyboard.row(telebot.types.InlineKeyboardButton(text="🫧  Geral", callback_data='pescar_geral'))

                # Enviar a imagem e o teclado de categorias
                photo = "https://telegra.ph/file/b3e6d2a41b68c2ceec8e5.jpg"
                bot.send_photo(message.chat.id, photo=photo, caption=f'<i>Olá! {nome}, \nVocê tem disponível: {qtd_iscas} iscas. \nBoa pesca!\n\nSelecione uma categoria:</i>', reply_markup=keyboard, reply_to_message_id=message.message_id, parse_mode="HTML")
            else:
                bot.send_message(message.chat.id, "Ei visitante, você não foi convidado! 😡", reply_to_message_id=message.message_id)

    except ValueError as e:
        print(f"Erro: {e}")
        newrelic.agent.record_exception()    
        bot.send_message(message.chat.id, "Você foi banido permanentemente do garden. Entre em contato com o suporte caso haja dúvidas.", reply_to_message_id=message.message_id)

