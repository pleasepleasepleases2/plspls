import telebot
import mysql.connector
from telebot.types import InputMediaPhoto
import datetime as dt_module  
from datetime import datetime, timedelta
from datetime import date
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from urllib.parse import urlparse
from bd import *
ultima_interacao = {}
def buscar_subcategorias(categoria, user_id=None):
    conn, cursor = conectar_banco_dados()
    try:
        if categoria == 'geral':
            cursor.execute('SELECT DISTINCT subcategoria FROM personagens')
        elif user_id is None:
            cursor.execute('SELECT DISTINCT subcategoria FROM personagens WHERE categoria = %s', (categoria,))
        else:
            cursor.execute('SELECT DISTINCT subcategoria FROM personagens WHERE categoria = %s AND user_id != %s',
                           (categoria, user_id))

        subcategorias = [row[0] for row in cursor.fetchall()]
        return subcategorias

    except mysql.connector.Error as err:
        print(f"Erro ao buscar subcategorias: {err}")
        return []

    finally:
        fechar_conexao(cursor, conn)
        
def buscar_cartas_usuario(id_usuario, id_personagem):
    try:
        conn, cursor = conectar_banco_dados()
        query = "SELECT COUNT(*) FROM inventario WHERE id_usuario = %s AND id_personagem = %s"
        cursor.execute(query, (id_usuario, id_personagem))
        resultado = cursor.fetchone()
        return resultado[0] if resultado else 0

    except mysql.connector.Error as err:
        print(f"Erro ao buscar cartas {id_personagem} do usuário {id_usuario}: {err}")
    finally:
        fechar_conexao(cursor, conn)
        
def obter_link_formatado(link):
    parsed_url = urlparse(link)
    if parsed_url.scheme and parsed_url.netloc:
        return f"<a href='{link}'>🎨 | Créditos da imagem!</a>"
    else:
        return "CR"
    

def procurar_subcategorias_similares(cursor, subcategoria):
    try:
        subnova = subcategoria.split(' ', 1)[1].strip().title()
        sql_consultar_subcategorias = """
            SELECT DISTINCT(subcategoria)
            FROM personagens
            WHERE subcategoria LIKE %s
        """
        cursor.execute(sql_consultar_subcategorias, (f'%{subnova}%',))
        subcategorias_similares = cursor.fetchall()
        return subcategorias_similares[0] if subcategorias_similares else None  # Retorna o primeiro elemento ou None se vazio
    except Exception as e:
        print("Erro ao consultar subcategorias:", e)
        return None
def verificar_cesta_vazia(id_usuario, subcategoria, cursor):
    try:
        sql_verificar_cartas = """
            SELECT COUNT(*)
            FROM inventario i
            JOIN personagens p ON i.id_personagem = p.id_personagem
            WHERE i.id_usuario = %s AND p.subcategoria LIKE %s
        """
        cursor.execute(sql_verificar_cartas, (id_usuario, f'%{subcategoria}%'))
        count_cartas = cursor.fetchone()[0]
        return count_cartas == 0
    except Exception as e:
        print("Erro ao verificar a cesta:", e)
        return True  # Se houver algum erro, considerar cesta vazia
    
def quantidade_cartas_usuario(id_usuario, id_personagem):

    try:
        conn, cursor = conectar_banco_dados()

        query_quantidade_cartas = """
            SELECT quantidade
            FROM inventario
            WHERE id_usuario = %s AND id_personagem = %s
        """
        cursor.execute(query_quantidade_cartas, (id_usuario, id_personagem))
        quantidade = cursor.fetchone()

        if quantidade:
            return quantidade[0]
        else:
            return 0  

    except mysql.connector.Error as e:
        print(f"Erro ao obter quantidade de cartas do usuário: {e}")
        return 0  

    finally:
        fechar_conexao(cursor, conn)


        
def obter_nome(id_personagem):
    try:
        query_fav_usuario_personagens = f"""
            SELECT p.nome AS nome_personagem
            FROM personagens p
            WHERE p.id_personagem = {id_personagem}
        """
        query_fav_usuario_eventos = f"""
            SELECT e.nome AS nome_personagem
            FROM evento e
            WHERE e.id_personagem = {id_personagem}
        """

        conn, cursor = conectar_banco_dados()
        cursor.execute(query_fav_usuario_personagens)
        resultado_fav_personagens = cursor.fetchone()

        if resultado_fav_personagens:
            nome_carta = resultado_fav_personagens[0] 
            return nome_carta

        cursor.execute(query_fav_usuario_eventos)
        resultado_fav_eventos = cursor.fetchone()

        if resultado_fav_eventos:
            nome_carta = resultado_fav_eventos[0]  
            return nome_carta
        
        return None

    except Exception as e:
        print(f"Erro ao obter nome da carta: {e}")
    finally:
        fechar_conexao(cursor, conn)

    try:
        query_fav_usuario_personagens = f"""
            SELECT p.id_personagem, p.emoji, p.nome AS nome_personagem, p.subcategoria, 0 AS quantidade, p.categoria, p.imagem
            FROM personagens p
            WHERE p.id_personagem = {id_personagem}
        """
        query_fav_usuario_eventos = f"""
            SELECT e.id_personagem, e.emoji, e.nome AS nome_personagem, e.subcategoria, 0 AS quantidade, e.categoria, e.imagem
            FROM evento e
            WHERE e.id_personagem = {id_personagem}
"""
        conn, cursor = conectar_banco_dados()
        cursor.execute(query_fav_usuario_personagens)
        resultado_fav_personagens = cursor.fetchone()

        if resultado_fav_personagens:
            nome_carta = resultado_fav_personagens[2]
            return nome_carta
        cursor.execute(query_fav_usuario_eventos)
        resultado_fav_eventos = cursor.fetchone()

        if resultado_fav_eventos:
            nome_carta = resultado_fav_eventos[2] 
            return nome_carta
        return None

    except Exception as e:
        print(f"Erro ao obter nome da carta: {e}")
    finally:
        fechar_conexao(cursor, conn)
        
def verificar_id_na_tabela(id_pessoa, tabela, coluna_iduser):
    try:
        conn, cursor = conectar_banco_dados()
        cursor.execute(f"SELECT COUNT(*) FROM {tabela} WHERE {coluna_iduser} = %s", (id_pessoa,))
        resultado_contagem = cursor.fetchone()[0]

        if resultado_contagem > 0:
            raise ValueError(f"ID {id_pessoa} já está na tabela '{tabela}' na coluna '{coluna_iduser}'")

    except mysql.connector.Error as err:
        print(f"Erro ao verificar ID {id_pessoa} na tabela '{tabela}': {err}")

    finally:
        fechar_conexao(cursor, conn)
        
def buscar_cartas_usuario(id_usuario, id_personagem):
    try:
        conn, cursor = conectar_banco_dados()
        query = "SELECT COUNT(*) FROM inventario WHERE id_usuario = %s AND id_personagem = %s"
        cursor.execute(query, (id_usuario, id_personagem))
        resultado = cursor.fetchone()
        return resultado[0] if resultado else 0

    except mysql.connector.Error as err:
        print(f"Erro ao buscar cartas {id_personagem} do usuário {id_usuario}: {err}")
    finally:
        fechar_conexao(cursor, conn)
        
def obter_username_por_id(user_id):
    try:
        user_info = bot.get_chat(user_id)
        if user_info.username:
            return f"O username do usuário com o ID {user_id} é: @{user_info.username}"
        else:
            return f"O usuário com o ID {user_id} não possui um username público."
    except Exception as e:
        return f"Erro ao obter o username: {e}"
def verificar_bloqueio(eu, voce):
    try:
        conn, cursor = conectar_banco_dados()
        query = "SELECT COUNT(*) FROM bloqueios WHERE (id_usuario = %s AND id_bloqueado = %s) OR (id_usuario = %s AND id_bloqueado = %s)"
        cursor.execute(query, (eu, voce, voce, eu))
        resultado = cursor.fetchone()
        return resultado[0] > 0
        
    except Exception as e:
        print(f"Erro ao verificar bloqueio: {e}")
        return False
    finally:
        fechar_conexao(cursor, conn)    
        
      
def obter_gif_url(id_personagem, id_usuario):
    conn, cursor = conectar_banco_dados()
    try:
        print(id_personagem, id_usuario)
        sql_gif = """
            SELECT link
            FROM gif
            WHERE id_personagem = %s AND id_usuario = %s
        """
        values_gif = (id_personagem, id_usuario)
        cursor.execute(sql_gif, values_gif)
        resultado_gif = cursor.fetchall()
        return resultado_gif[0][0] if resultado_gif else None
    finally:
        fechar_conexao(cursor, conn)
        


def obter_imagem_carta(id_usuario):
    try:
        query_fav_usuario_personagens = f"""
            SELECT p.id_personagem, p.emoji, p.nome AS nome_personagem, p.subcategoria, 0 AS quantidade, p.categoria, p.imagem
            FROM personagens p
            WHERE p.id_personagem = (
                SELECT fav
                FROM usuarios
                WHERE id_usuario = {id_usuario}
            )
        """
        query_fav_usuario_eventos = f"""
            SELECT e.id_personagem, e.emoji, e.nome AS nome_personagem, e.subcategoria, 0 AS quantidade, e.categoria, e.imagem
            FROM evento e
            WHERE e.id_personagem = (
                SELECT fav
                FROM usuarios
                WHERE id_usuario = {id_usuario}
            )
        """

        conn, cursor = conectar_banco_dados()
        cursor.execute(query_fav_usuario_personagens)
        resultado_fav_personagens = cursor.fetchone()

        if resultado_fav_personagens:
            id_carta_personagens = resultado_fav_personagens[0]
            query_obter_imagem_personagens = "SELECT imagem FROM personagens WHERE id_personagem = %s"
            cursor.execute(query_obter_imagem_personagens, (id_carta_personagens,))
            imagem_carta_personagens = cursor.fetchone()
            
            if imagem_carta_personagens:
                return imagem_carta_personagens[0]

        cursor.execute(query_fav_usuario_eventos)
        resultado_fav_eventos = cursor.fetchone()

        if resultado_fav_eventos:
            id_carta_eventos = resultado_fav_eventos[0]
            query_obter_imagem_eventos = "SELECT imagem FROM evento WHERE id_personagem = %s"
            cursor.execute(query_obter_imagem_eventos, (id_carta_eventos,))
            imagem_carta_eventos = cursor.fetchone()

            if imagem_carta_eventos:
                return imagem_carta_eventos[0]
        return None

    except Exception as e:
        print(f"Erro ao obter imagem da carta: {e}")
    finally:
        fechar_conexao(cursor, conn)
        
def obter_nome_carta(id_usuario):
    try:
        query_fav_usuario = f"""
            SELECT p.id_personagem, p.emoji, p.nome AS nome_personagem, p.subcategoria, 0 AS quantidade, p.categoria, p.imagem
            FROM personagens p
            WHERE p.id_personagem = (
                SELECT fav
                FROM usuarios
                WHERE id_usuario = {id_usuario}
            )
            UNION
            SELECT e.id_personagem, e.emoji, e.nome AS nome_personagem, e.subcategoria, 0 AS quantidade, e.categoria, e.imagem
            FROM evento e
            WHERE e.id_personagem = (
                SELECT fav
                FROM usuarios
                WHERE id_usuario = {id_usuario}
            )
        """
        conn, cursor = conectar_banco_dados()
        cursor.execute(query_fav_usuario)
        resultado_fav = cursor.fetchone()

        if resultado_fav:
            nome_carta = resultado_fav[2]
            return nome_carta
        else:
            return None
    except Exception as e:
        print(f"Erro ao obter nome da carta: {e}")
    finally:
        fechar_conexao(cursor, conn)

def obter_quantidade_total_cartas(id_usuario):
    try:
        conn, cursor = conectar_banco_dados()
        cursor.execute("SELECT COUNT(DISTINCT id_personagem) FROM inventario WHERE id_usuario = %s", (id_usuario,))
        resultado = cursor.fetchone()

        if resultado:
            return resultado[0]
        else:
            return 0
    finally:
        fechar_conexao(cursor, conn)
        
def obter_cartas_subcateg(subcategoria, conn):
    try:
        subcategoria = subcategoria.split('_')[-1].lower()
        cursor = conn.cursor()
        cursor.execute("SELECT id_personagem, emoji, nome, imagem FROM personagens WHERE subcategoria = %s", (subcategoria,))
        cartas = cursor.fetchall()
        return cartas

    except mysql.connector.Error as err:
        print(f"Erro ao obter cartas da subcategoria: {err}")
        return None
    finally:
        fechar_conexao(cursor, conn)     
                   
def obter_total_pescagens(id_personagem, cursor):
    cursor.execute("SELECT total FROM personagens WHERE id_personagem = %s", (id_personagem,))
    total_pescagens = cursor.fetchone()
    return total_pescagens[0] if total_pescagens else 0
        
def obter_informacoes_carta(card_id):
    conn, cursor = conectar_banco_dados()
    cursor.execute("SELECT id_personagem, emoji, nome, subcategoria FROM personagens WHERE id_personagem = %s", (card_id,))
    result_personagens = cursor.fetchone()

    if result_personagens:
        return result_personagens
    cursor.execute("SELECT id_personagem, emoji, nome, subcategoria FROM evento WHERE id_personagem = %s", (card_id,))
    result_evento = cursor.fetchone()
    return result_evento

def obter_nome_usuario_por_id(id_usuario):
    try:
        conn, cursor = conectar_banco_dados()
        query = "SELECT nome_usuario FROM usuarios WHERE id_usuario = %s"
        cursor.execute(query, (id_usuario,))
        resultado = cursor.fetchone()
        if resultado:
            return resultado[0] 
        else:
            return "Nome de Usuário Desconhecido"
    except Exception as e:
        print(f"Erro ao obter nome do usuário: {e}")
        return "Nome de Usuário Desconhecido"      

def obter_url_imagem_por_id(id_carta):
    try:
        conn, cursor = conectar_banco_dados()
        sql = f"""
            SELECT id_personagem, imagem
            FROM (
                SELECT id_personagem, imagem
                FROM personagens
                WHERE id_personagem = %s
                UNION ALL
                SELECT id_personagem, imagem
                FROM evento
                WHERE id_personagem = %s
            ) AS cartas_usuario
        """
        cursor.execute(sql, (id_carta, id_carta))
        resultado = cursor.fetchone()
        if resultado:
            return resultado[1]
        else:
            return None
    except Exception as e:
        print(f"Erro ao obter URL da imagem por ID: {e}")
        return None
    finally:
        fechar_conexao(cursor, conn)

def obter_info_carta_por_id(id_carta):
    try:
        conn, cursor = conectar_banco_dados()
        sql = """
            SELECT emoji, id_personagem, nome, subcategoria
            FROM personagens
            WHERE id_personagem = %s
        """
        values = (id_carta,)
        cursor.execute(sql, values)
        resultado = cursor.fetchone()

        if resultado:
            emoji, id_personagem, nome, subcategoria = resultado
            info_carta = {
                'emoji': emoji,
                'id': id_personagem,
                'nome': nome,
                'subcategoria': subcategoria
            }
            return info_carta
        return None
    except mysql.connector.Error as e:
        print(f"Erro ao obter informações da carta por ID: {e}")
    finally:
        fechar_conexao(cursor, conn)
        
def obter_nome_do_usuario(id_usuario):
    try:
        conn = mysql.connector.connect(**db_config())  
        cursor = conn.cursor()

        query = "SELECT nome FROM usuarios WHERE id_usuario = %s"
        cursor.execute(query, (id_usuario,))
        resultado = cursor.fetchone()

        if resultado:
            return resultado[0]  
        else:
            return None  

    except mysql.connector.Error as err:
        print(f"Erro ao obter nome do usuário: {err}")
        return None

    finally:
        cursor.close()
        conn.close()        

def verificar_evento(cursor, id_personagem):
    try:
        cursor.execute("SELECT id_personagem FROM evento WHERE id_personagem = %s", (id_personagem,))
        result = cursor.fetchone()
        cursor.fetchall()
        return result is not None
    
    except Exception as e:
        print(f"Erro ao verificar evento: {e}")
        return False
    
def obter_link_formatado(link):
    parsed_url = urlparse(link)
    if parsed_url.scheme and parsed_url.netloc:
        return f"<a href='{link}'>🎨 | Créditos da imagem!</a>"
    else:
        return 
    
def obter_resultados_faltante(subcategoria, numero_pagina, id_usuario):
    subcategoria_com_prefixo = "f " + subcategoria
    conn, cursor = conectar_banco_dados()
    try:
        cursor.execute("SELECT cartas_json FROM temp_cartas WHERE subcategoria = %s AND pagina = %s AND id_usuario = %s", (subcategoria_com_prefixo, numero_pagina, id_usuario))
        resultados = cursor.fetchall()
        
        return resultados
    finally:
        fechar_conexao(cursor, conn)
 
def inventario_existe(id_usuario, id_personagem):
    try:
        conn, cursor = conectar_banco_dados()
        cursor.execute("SELECT 1 FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (id_usuario, id_personagem))
        return cursor.fetchone() is not None
    except Exception as e:
        print(f"Erro ao verificar inventário: {e}")
        return False
    finally:
        fechar_conexao(cursor, conn)

def procurar_subcategorias_similares(cursor, subcategoria):
    try:
        subnova = subcategoria.split(' ', 1)[1].strip().title()
        sql_consultar_subcategorias = """
            SELECT DISTINCT(subcategoria)
            FROM personagens
            WHERE subcategoria LIKE %s
        """
        cursor.execute(sql_consultar_subcategorias, (f'%{subnova}%',))
        subcategorias_similares = cursor.fetchall()
        return subcategorias_similares[0] if subcategorias_similares else None 
    except Exception as e:
        print("Erro ao consultar subcategorias:", e)
        return None
def verificar_cesta_vazia(id_usuario, subcategoria, cursor):
    try:
        sql_verificar_cartas = """
            SELECT COUNT(*)
            FROM inventario i
            JOIN personagens p ON i.id_personagem = p.id_personagem
            WHERE i.id_usuario = %s AND p.subcategoria LIKE %s
        """
        cursor.execute(sql_verificar_cartas, (id_usuario, f'%{subcategoria}%'))
        count_cartas = cursor.fetchone()[0]
        return count_cartas == 0
    except Exception as e:
        print("Erro ao verificar a cesta:", e)
        return True  
    
def excluir_registros_antigos(cursor, conn, usuario, subcategoria_like):
    try:
        sql_excluir_cartas = """
            DELETE FROM temp_cartas
            WHERE id_usuario = %s AND subcategoria LIKE %s
        """
        cursor.execute(sql_excluir_cartas, (usuario, f'%{subcategoria_like}%'))
        conn.commit()
        print("Registros antigos excluídos com sucesso.")
    except Exception as e:
        print("Erro ao excluir registros antigos:", e)
        conn.rollback()


def quantidade_cartas_usuario(id_usuario, id_personagem):

    try:
        conn, cursor = conectar_banco_dados()

        query_quantidade_cartas = """
            SELECT quantidade
            FROM inventario
            WHERE id_usuario = %s AND id_personagem = %s
        """
        cursor.execute(query_quantidade_cartas, (id_usuario, id_personagem))
        quantidade = cursor.fetchone()

        if quantidade:
            return quantidade[0]
        else:
            return 0 

    except mysql.connector.Error as e:
        print(f"Erro ao obter quantidade de cartas do usuário: {e}")
        return 0 

    finally:
        fechar_conexao(cursor, conn)
def verificar_tempo_passado(chat_id):
    if chat_id in ultima_interacao:
        tempo_passado = datetime.now() - ultima_interacao[chat_id]
        return tempo_passado.total_seconds() >=1
    else:
        return True        
    
def verificar_id_na_tabelabeta(user_id):
    try:
        conn, cursor = conectar_banco_dados() 
        query = f"SELECT id FROM beta WHERE id = {user_id}"
        cursor.execute(query)
        resultado = cursor.fetchone()
        cursor.close()
        conn.close()
        return resultado is not None
    except Exception as e:
        print(f"Erro ao verificar ID na tabela beta: {e}")
        raise ValueError("Erro ao verificar ID na tabela beta")    
    
def obter_favorito(id_usuario):
    try:
        query_fav_usuario = f"""
            SELECT p.id_personagem, 
                   p.emoji COLLATE utf8mb4_general_ci AS emoji, 
                   p.nome COLLATE utf8mb4_general_ci AS nome_personagem, 
                   p.subcategoria COLLATE utf8mb4_general_ci AS subcategoria, 
                   p.categoria COLLATE utf8mb4_general_ci AS categoria, 
                   p.imagem COLLATE utf8mb4_general_ci AS imagem, 
                   'personagens' COLLATE utf8mb4_general_ci AS origem
            FROM personagens p
            WHERE p.id_personagem = (
                SELECT fav
                FROM usuarios
                WHERE id_usuario = {id_usuario}
            )
            UNION
            SELECT e.id_personagem, 
                   e.emoji COLLATE utf8mb4_general_ci AS emoji, 
                   e.nome COLLATE utf8mb4_general_ci AS nome_personagem, 
                   e.subcategoria COLLATE utf8mb4_general_ci AS subcategoria, 
                   e.categoria COLLATE utf8mb4_general_ci AS categoria, 
                   e.imagem COLLATE utf8mb4_general_ci AS imagem, 
                   'evento' COLLATE utf8mb4_general_ci AS origem
            FROM evento e
            WHERE e.id_personagem = (
                SELECT fav
                FROM usuarios
                WHERE id_usuario = {id_usuario}
            )
        """
        conn, cursor = conectar_banco_dados()
        cursor.execute(query_fav_usuario)
        resultado_fav = cursor.fetchone()

        if resultado_fav:
            id_personagem = resultado_fav[0]
            emoji = resultado_fav[1]
            nome_carta = resultado_fav[2]
            subcategoria = resultado_fav[3]
            imagem = resultado_fav[5]
            return id_personagem, emoji, nome_carta, subcategoria, imagem
        else:
            return None, None, None, None, None
    except Exception as e:
        print(f"Erro ao obter nome da carta: {e}")
        return None, None, None, None, None
    finally:
        fechar_conexao(cursor, conn)


        
def obter_emoji_evento(evento):
    if evento == 'fixo':
        return '🪴'
    elif evento == 'amor':
        return '💐'
    elif evento == 'aniversario':
        return '🎁'
    elif evento == 'inverno':
        return '☃️'    
    return '🪴'                 
