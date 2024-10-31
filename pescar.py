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
def aplicar_recompensa_extra(user_id, subcategoria):
    """
    Função para conceder uma recompensa extra com base no bônus de sorte ativo,
    com 50% de chance de aplicar o bônus e 50% de não ocorrer nada.
    """
    if random.random() >= 0.5:  # 50% de chance de ocorrer bônus
        conn, cursor = conectar_banco_dados()
        # Escolha entre cenouras ou uma carta da mesma subcategoria
        recompensa = random.choice(["cenouras", "carta"])

        if recompensa == "cenouras":
            # Recompensa de cenouras
            cenouras_extras = random.randint(10, 50)
            aumentar_cenouras(user_id, cenouras_extras)
            return f"Você ganhou {cenouras_extras} cenouras extras!"
        else:
            # Recompensa de carta extra
            cartas = obter_cartas_subcateg(subcategoria, conn)
            if cartas:
                carta_escolhida = random.choice(cartas)  # Seleciona uma carta aleatória
                id_personagem, _, nome, _ = carta_escolhida  # Acessa o id_personagem e o nome
                add_to_inventory(user_id, id_personagem)  # Adiciona ao inventário do usuário
                return f"Você ganhou uma carta extra: {id_personagem} - {nome} de {subcategoria}!"
            else:
                return 
    else:
        return 

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

import random
from datetime import datetime

import random

# Função para truncar ou alterar uma mensagem simulando uma "travessura de embaralhamento"
def embaralhar_mensagem(texto):
    palavras = texto.split()
    resultado = []

    for palavra in palavras:
        # Define uma probabilidade de truncar ou alterar cada palavra
        if random.random() < 0.5:
            truncamento = max(1, int(len(palavra) * 0.5))  # Corta a palavra pela metade
            palavra = palavra[:truncamento]
        resultado.append(palavra)

    return " ".join(resultado)

# Função para verificar se a "travessura de embaralhamento" está ativa
def verificar_travessura_ativa(id_usuario, tipo_travessura="embaralhamento"):
    conn, cursor = conectar_banco_dados()
    try:
        query = "SELECT fim_travessura FROM travessuras WHERE id_usuario = %s AND tipo_travessura = %s"
        cursor.execute(query, (id_usuario, tipo_travessura))
        resultado = cursor.fetchone()
        
        # Verificar se a travessura está ativa e ainda dentro do prazo
        if resultado:
            fim_travessura = resultado[0]
            return datetime.now() < fim_travessura
        return False
    finally:
        fechar_conexao(cursor, conn)

# Função para truncar aleatoriamente nomes de subcategorias
def truncar_texto(texto, truncar_percent=0.5):
    # Separar tags HTML do texto visível
    partes = re.split(r'(<[^>]+>)', texto)  # Divide o texto preservando as tags
    texto_embaralhado = ""

    for parte in partes:
        if parte.startswith("<") and parte.endswith(">"):
            # Se é uma tag HTML, preserve sem alterar
            texto_embaralhado += parte
        else:
            # Trunca exatamente a metade da parte do texto visível
            metade = len(parte) // 2
            texto_embaralhado += parte[:metade]  # Pega somente a primeira metade


    return texto_embaralhado


def categoria_handler(message, categoria, id_usuario):
    try:
        conn, cursor = conectar_banco_dados()
        chat_id = message.chat.id
        
        # Verificar se a travessura de embaralhamento está ativa
        embaralhamento_ativo = verificar_travessura_ativa(id_usuario)

        if categoria.lower() == 'geral': 
            subcategorias = buscar_subcategorias(categoria)
            subcategorias = [subcategoria for subcategoria in subcategorias if subcategoria]

            if not subcategorias:
                bot.send_message(chat_id, f"Nenhuma subcategoria encontrada para a categoria '{categoria}'.")
                return None

            respostatexto = "Sua isca atraiu 6 espécies, qual peixe você vai levar?\n\n"
            resposta_texto = truncar_texto(respostatexto) if embaralhamento_ativo else respostatexto
            subcategorias_aleatorias = random.sample(subcategorias, min(6, len(subcategorias)))

            for i, subcategoria in enumerate(subcategorias_aleatorias, start=1):
                subcategoria_final = truncar_texto(subcategoria) if embaralhamento_ativo else subcategoria
                resposta_texto += f"{i}\uFE0F\u20E3 - {subcategoria_final}\n"

            markup = telebot.types.InlineKeyboardMarkup(row_width=6)
            row_buttons = []
            for i, subcategoria in enumerate(subcategorias_aleatorias, start=1):
                subcategoria_final = truncar_texto(subcategoria) if embaralhamento_ativo else subcategoria
                button_text = f"{i}\uFE0F\u20E3"
                callback_data = f"choose_subcategoria_{subcategoria}"
                row_buttons.append(telebot.types.InlineKeyboardButton(button_text, callback_data=callback_data))

            markup.row(*row_buttons)
            imagem_url = "https://telegra.ph/file/8a50bf408515b52a36734.jpg"
            bot.edit_message_media(
                chat_id=chat_id,
                message_id=message.message_id,
                reply_markup=markup,
                media=telebot.types.InputMediaPhoto(media=imagem_url, caption=resposta_texto)
            )
            return None  

        # Tratamento para categorias diferentes de "geral"
        subcategorias = buscar_subcategorias(categoria)
        subcategorias = [subcategoria for subcategoria in subcategorias if subcategoria]

        if not subcategorias:
            bot.send_message(chat_id, f"Nenhuma subcategoria encontrada para a categoria '{categoria}'.")
            return None

        resposta_texto = "Sua isca atraiu 6 espécies, qual peixe você vai levar?\n\n"
        subcategorias_aleatorias = random.sample(subcategorias, min(6, len(subcategorias)))

        for i, subcategoria in enumerate(subcategorias_aleatorias, start=1):
            subcategoria_final = truncar_texto(subcategoria) if embaralhamento_ativo else subcategoria
            resposta_texto += f"{i}\uFE0F\u20E3 - {subcategoria_final}\n"

        markup = telebot.types.InlineKeyboardMarkup(row_width=6)
        row_buttons = []
        for i, subcategoria in enumerate(subcategorias_aleatorias, start=1):
            subcategoria_final = truncar_texto(subcategoria) if embaralhamento_ativo else subcategoria
            button_text = f"{i}\uFE0F\u20E3"
            callback_data = f"choose_subcategoria_{subcategoria}"
            row_buttons.append(telebot.types.InlineKeyboardButton(button_text, callback_data=callback_data))

        markup.row(*row_buttons)
        imagem_url = "https://telegra.ph/file/8a50bf408515b52a36734.jpg"
        bot.edit_message_media(
            chat_id=chat_id,
            message_id=message.message_id,
            reply_markup=markup,
            media=telebot.types.InputMediaPhoto(media=imagem_url, caption=resposta_texto)
        )

    except mysql.connector.Error as err:
        bot.send_message(chat_id, f"Erro ao buscar subcategorias: {err}")
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

import traceback

def adicionar_boost_peixes(user_id, multiplicador, duracao_horas, chat_id):
    try:
        conn, cursor = conectar_banco_dados()
        fim_boost = datetime.now() + timedelta(hours=duracao_horas)

        # Inserir ou atualizar o boost de peixes na tabela 'boosts'
        cursor.execute("""
            INSERT INTO boosts (id_usuario, tipo_boost, multiplicador, fim_boost)
            VALUES (%s, 'peixes', %s, %s)
            ON DUPLICATE KEY UPDATE multiplicador = %s, fim_boost = %s
        """, (user_id, multiplicador, fim_boost, multiplicador, fim_boost))
        
        conn.commit()

        bot.send_message(
            chat_id, 
            f"🎣✨ Você ativou o Boost de Peixes! Todos os peixes capturados serão multiplicados por {multiplicador} nas próximas {duracao_horas} horas.",
            parse_mode="Markdown"
        )
    
    except Exception as e:
        print(f"Erro ao adicionar Boost de Peixes: {e}")
    
    finally:
        fechar_conexao(cursor, conn)

def verificar_boost_peixes(user_id):
    """Verifica se o boost de peixes está ativo e retorna o multiplicador se ativo."""
    conn, cursor = conectar_banco_dados()
    try:
        cursor.execute("SELECT multiplicador, fim_boost FROM boosts WHERE id_usuario = %s AND tipo_boost = 'peixes'", (user_id,))
        resultado = cursor.fetchone()
        if resultado:
            multiplicador, fim_boost = resultado
            if datetime.now() < fim_boost:
                return multiplicador  # Boost ativo
        return 1  # Sem boost
    except Exception as e:
        print(f"Erro ao verificar o boost de peixes: {e}")
        return 1
    finally:
        fechar_conexao(cursor, conn)

def send_card_message(message, *args, cursor=None, conn=None):
    try:
        id_usuario = message.chat.id
        id_user = message.from_user.id
        embaralhamento_ativo = verificar_travessura_ativa(id_user)

        # Verificar se o boost de peixes e o bônus de sorte estão ativos
        multiplicador_peixes = verificar_boost_peixes(id_usuario)
        multiplicador_sorte = verificar_bonus_sorte(id_usuario)

        # Debug: Exibindo os argumentos e estado de bônus e boosts
        print(f"[DEBUG] id_usuario: {id_usuario}, id_user: {id_user}, multiplicador_peixes: {multiplicador_peixes}, multiplicador_sorte: {multiplicador_sorte}, embaralhamento_ativo: {embaralhamento_ativo}, args: {args}")

        # Verifica se é um evento fixo (dicionário passado)
        if len(args) == 1 and isinstance(args[0], dict):
            evento_aleatorio = args[0]
            subcategoria_display = evento_aleatorio['subcategoria'].split('_')[-1]
            id_personagem = evento_aleatorio['id_personagem']
            nome = evento_aleatorio['nome']
            subcategoria = evento_aleatorio['subcategoria']

            # Adicionar carta ao inventário e aplicar multiplicador de peixes
            add_to_inventory(id_usuario, id_personagem)
            quantidade = verifica_inventario_troca(id_usuario, id_personagem) * multiplicador_peixes

            imagem = evento_aleatorio.get('imagem', "https://telegra.ph/file/8a50bf408515b52a36734.jpg")
            texto = f"🎣 Parabéns! Sua isca era boa e você recebeu:\n\n🎃 {id_personagem} - {nome}\nde {subcategoria_display}\nQuantidade de cartas: {quantidade}"


            text = truncar_texto(texto) if embaralhamento_ativo else texto

            # Enviar mensagem com o resultado
            enviar_mensagem_com_imagem(message, imagem, text)
            register_card_history(message, id_usuario, id_personagem)

        # Verifica se é uma carta aleatória (5 argumentos)
        elif len(args) == 5:
            emoji_categoria, id_personagem, nome, subcategoria, imagem = args
            subcategoria_display = subcategoria.split('_')[-1]

            # Adicionar carta ao inventário e aplicar multiplicador de peixes
            add_to_inventory(id_usuario, id_personagem)
            quantidade = verifica_inventario_troca(id_usuario, id_personagem) * multiplicador_peixes

            imagem_url = imagem if imagem else "https://telegra.ph/file/8a50bf408515b52a36734.jpg"
            texto = f"🎣 Parabéns! Sua isca era boa e você recebeu:\n\n{emoji_categoria}<code> {id_personagem}</code> - {nome}\nde {subcategoria_display}\nQuantidade de cartas: {quantidade}"

            if multiplicador_sorte > 1:
            # Chance de recompensa extra
                recompensa_extra = aplicar_recompensa_extra(id_usuario, subcategoria)
                if recompensa_extra is not None:
                    texto += f"\n\n🍀 Bônus de Sorte ativado: {recompensa_extra}"


            text = truncar_texto(texto) if embaralhamento_ativo else texto

            # Enviar mensagem com o resultado
            enviar_mensagem_com_imagem(message, imagem_url, text)
            register_card_history(message.from_user, id_usuario, id_personagem)

        else:
            print("[DEBUG] Número incorreto de argumentos.")

    except Exception as e:
        erro = traceback.format_exc()
        mensagem = f"Erro ao enviar carta: {e}\n{erro}"
        bot.send_message(grupodeerro, mensagem, parse_mode="HTML")


def verificar_bonus_sorte(user_id):
    """
    Função para verificar se o bônus de sorte está ativo e retornar o multiplicador.
    """
    conn, cursor = conectar_banco_dados()
    cursor.execute("""
        SELECT multiplicador FROM boosts 
        WHERE id_usuario = %s AND tipo_boost = 'sorte' AND fim_boost > NOW()
    """, (user_id,))
    resultado = cursor.fetchone()
    fechar_conexao(cursor, conn)
    return resultado[0] if resultado else 1

def enviar_mensagem_com_imagem(message, imagem_url, text):
    """
    Função para enviar mensagem com imagem, tratando o tipo de mídia.
    """
    try:
        if imagem_url.lower().endswith(('.jpg', '.jpeg', '.png')):
            bot.edit_message_media(
                chat_id=message.chat.id,
                message_id=message.message_id,
                media=telebot.types.InputMediaPhoto(media=imagem_url, caption=text, parse_mode="HTML")
            )
        elif imagem_url.lower().endswith(('.mp4', '.gif')):
            bot.edit_message_media(
                chat_id=message.chat.id,
                message_id=message.message_id,
                media=telebot.types.InputMediaVideo(media=imagem_url, caption=text, parse_mode="HTML")
            )
    except Exception as ex:
        print(f"[DEBUG] edit_message_media falhou: {ex}")
        if imagem_url.lower().endswith(('.jpg', '.jpeg', '.png')):
            bot.send_photo(chat_id=message.chat.id, photo=imagem_url, caption=text, parse_mode="HTML")
        elif imagem_url.lower().endswith(('.mp4', '.gif')):
            bot.send_video(chat_id=message.chat.id, video=imagem_url, caption=text, parse_mode="HTML")

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

ultima_interacao = {}
def embaralhar_texto_visivel(texto):
    # Separar tags HTML do texto visível
    partes = re.split(r'(<[^>]+>)', texto)  # Quebra o texto preservando as tags
    texto_embaralhado = ""

    for parte in partes:
        if parte.startswith("<") and parte.endswith(">"):
            # Se é uma tag HTML, preserve sem alterar
            texto_embaralhado += parte
        else:
            # Embaralha o texto visível
            palavras = parte.split()
            palavras_embaralhadas = ["".join(random.sample(palavra, len(palavra))) if len(palavra) > 3 else palavra for palavra in palavras]
            texto_embaralhado += " ".join(palavras_embaralhadas)

    return texto_embaralhado
# Função para o comando de pesca
def pescar(message):
    try:
        print("Comando pescar acionado")
        nome = message.from_user.first_name
        user_id = message.from_user.id

        bloqueado, minutos_restantes = verificar_bloqueio_comandos(user_id)
        if bloqueado:
            bot.send_message(message.chat.id, f"👻 Você está invisível e seus comandos serão ignorados por mais {minutos_restantes} minutos.")
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
                photo = "https://pub-6f23ef52e8614212a14d24b0cf55ae4a.r2.dev/BQACAgEAAxkBAAIeq2ckA3TkUqJpUN8HGwSScRjS3dY6AAIZBQACy-MhRXObx3AerywHNgQ.jpg"
                texto = f'<i>Olá! {nome}, \nVocê tem disponível: {qtd_iscas} iscas. \nBoa pesca!\n\nSelecione uma categoria:</i>'
                # Verificar se a travessura está ativa e embaralhar, se necessário
                if verificar_travessura_embaralhamento(message.from_user.id):
                    texto = truncar_texto(texto)
                bot.send_photo(message.chat.id, photo=photo, caption=texto, reply_markup=keyboard, reply_to_message_id=message.message_id, parse_mode="HTML")
            else:
                bot.send_message(message.chat.id, "Ei visitante, você não foi convidado! 😡", reply_to_message_id=message.message_id)

    except ValueError as e:
        print(f"Erro: {e}")
        newrelic.agent.record_exception()    
        bot.send_message(message.chat.id, "Você foi banido permanentemente do garden. Entre em contato com o suporte caso haja dúvidas.", reply_to_message_id=message.message_id)
    except Exception as e:
        error_details = traceback.format_exc()  # Captura toda a stack trace
        print(f"Erro inesperado: {error_details}")  # Log mais detalhado
        
        bot.send_message(message.chat.id, "Ocorreu um erro inesperado ao tentar pescar.", reply_to_message_id=message.message_id)

def verificar_bloqueio_pesca(user_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Verificar se o usuário está bloqueado
        query = "SELECT fim_bloqueio FROM bloqueios_pesca WHERE id_usuario = %s"
        cursor.execute(query, (user_id,))
        resultado = cursor.fetchone()

        if resultado:
            fim_bloqueio = resultado[0]
            if datetime.now() < fim_bloqueio:
                # Se ainda estiver dentro do período de bloqueio, retorna True
                return True, (fim_bloqueio - datetime.now()).seconds // 60
        return False, 0

    except Exception as e:
        print(f"Erro ao verificar bloqueio de pesca para o usuário {user_id}: {e}")
        traceback.print_exc()
        return False, 0
    finally:
        fechar_conexao(cursor, conn)

def bloquear_pesca_usuario(user_id, duracao_minutos):
    try:
        conn, cursor = conectar_banco_dados()

        # Calcular o tempo de término do bloqueio
        fim_bloqueio = datetime.now() + timedelta(minutes=duracao_minutos)

        # Inserir ou atualizar o tempo de bloqueio na tabela `bloqueios_pesca`
        query = """
            INSERT INTO bloqueios_pesca (id_usuario, fim_bloqueio)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE fim_bloqueio = %s
        """
        cursor.execute(query, (user_id, fim_bloqueio, fim_bloqueio))
        conn.commit()

        # Enviar mensagem informando sobre o bloqueio
        bot.send_message(user_id, f"👻 Travessura! Você está bloqueado de pescar pelos próximos {duracao_minutos} minutos!")

    except Exception as e:
        print(f"Erro ao bloquear pesca para o usuário {user_id}: {e}")
        traceback.print_exc()
    finally:
        fechar_conexao(cursor, conn)
def verificar_bloqueio_comandos(user_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Verificar se o usuário está bloqueado
        query = "SELECT fim_bloqueio FROM bloqueios_comandos WHERE id_usuario = %s"
        cursor.execute(query, (user_id,))
        resultado = cursor.fetchone()

        if resultado:
            fim_bloqueio = resultado[0]
            if datetime.now() < fim_bloqueio:
                # Se ainda estiver dentro do período de bloqueio, retorna True
                return True, (fim_bloqueio - datetime.now()).seconds // 60
        return False, 0

    except Exception as e:
        print(f"Erro ao verificar bloqueio de comandos para o usuário {user_id}: {e}")
        traceback.print_exc()
        return False, 0
    finally:
        fechar_conexao(cursor, conn)
def verificar_travessura_embaralhamento(user_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Verificar se a travessura está ativa
        cursor.execute("""
            SELECT fim_travessura FROM travessuras
            WHERE id_usuario = %s AND tipo_travessura = 'embaralhamento'
        """, (user_id,))
        resultado = cursor.fetchone()

        if resultado:
            fim_travessura = resultado[0]
            # Se a travessura ainda está ativa (o tempo atual é menor que o fim)
            if datetime.now() < fim_travessura:
                return True
        
        return False  # Travessura não está ativa
    
    except Exception as e:
        print(f"Erro ao verificar a travessura de embaralhamento: {e}")
        return False
    finally:
        fechar_conexao(cursor, conn)
