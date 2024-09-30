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
from sub import *

# Cache com validade de 10 minutos (600 segundos)
banco_cache = TTLCache(maxsize=100, ttl=600)

@cached(banco_cache)
def obter_cartas_banco_cache():
    conn, cursor = conectar_banco_dados()
    cursor.execute("SELECT id_personagem, quantidade FROM banco_inventario ORDER BY id_personagem ASC")
    cartas_banco = cursor.fetchall()
    fechar_conexao(cursor, conn)
    return cartas_banco

def incrementar_quantidades_banco():
    try:
        conn, cursor = conectar_banco_dados()
        
        # Seleciona todos os cards existentes no banco
        cursor.execute("SELECT id_personagem, quantidade FROM banco_inventario")
        cartas_existentes = cursor.fetchall()
        
        if not cartas_existentes:
            return "Não há cartas no banco para incrementar."
        
        # Define o número máximo de cartas a incrementar
        max_cartas_a_incrementar = len(cartas_existentes) // 2
        
        # Seleciona aleatoriamente o número de cartas a incrementar
        num_cartas_a_incrementar = random.randint(1, max_cartas_a_incrementar)
        
        # Seleciona aleatoriamente as cartas a incrementar
        cartas_a_incrementar = random.sample(cartas_existentes, num_cartas_a_incrementar)
        
        mensagens = []
        mensagem_atual = "📈 Cartas incrementadas:\n\n"
        
        for carta in cartas_a_incrementar:
            id_personagem, quantidade_atual = carta
            quantidade_a_adicionar = random.randint(1, 10)  # Quantidade aleatória entre 1 e 10
            nova_quantidade = quantidade_atual + quantidade_a_adicionar
            cursor.execute(
                "UPDATE banco_inventario SET quantidade = %s WHERE id_personagem = %s",
                (nova_quantidade, id_personagem)
            )
            mensagem_carta = f"💳 ID: {id_personagem} | +{quantidade_a_adicionar} (Total: {nova_quantidade})\n"
            
            if len(mensagem_atual) + len(mensagem_carta) > 4096:  # Verifica se a mensagem atual excederá o limite de caracteres
                mensagens.append(mensagem_atual)
                mensagem_atual = "📈 Cartas incrementadas (continuação):\n\n"
            
            mensagem_atual += mensagem_carta
        
        if mensagem_atual:
            mensagens.append(mensagem_atual)
        
        conn.commit()
        
        # Invalidar o cache
        banco_cache.clear()

        return mensagens
    
    except Exception as e:
        print(f"Erro ao incrementar quantidades no banco: {e}")
        return [f"Erro ao incrementar quantidades no banco: {e}"]
    
    finally:
        fechar_conexao(cursor, conn)

def obter_total_cenouras():
    conn, cursor = conectar_banco_dados()
    try:
        cursor.execute("SELECT SUM(quantidade_cenouras) FROM banco_cidade")
        total_cenouras = cursor.fetchone()
        if total_cenouras and total_cenouras[0]:
            return total_cenouras[0]
        return 0
    except Exception as e:
        print(f"Erro ao obter total de cenouras: {e}")
        return 0
    finally:
        fechar_conexao(cursor, conn)

        
def mostrar_cartas_banco(chat_id, pagina_atual, total_paginas, cartas_banco, total_cartas, message_id):
    offset = (pagina_atual - 1) * 30
    cartas_pagina = cartas_banco[offset:offset + 30]

    total_cenouras = obter_total_cenouras()

    mensagem_banco = "🍎 <b>Peixes no Banco do Vilarejo:</b>\n\n"
    mensagem_banco += f"💰 Total de peixes: {total_cartas}\n\n"
    for carta in cartas_pagina:
        id_personagem, quantidade = carta
        mensagem_banco += f"💸 <i>{id_personagem}</i> - {quantidade}\n"

    mensagem_banco += f"\nPágina {pagina_atual}/{total_paginas}"

    markup = botoes_paginacao(pagina_atual, total_paginas, total_cartas, 'banco')

    if message_id:
        try:
            bot.edit_message_text(mensagem_banco, chat_id=chat_id, message_id=message_id, reply_markup=markup, parse_mode="HTML")
        except Exception as e:
            bot.send_message(chat_id, mensagem_banco, reply_markup=markup, parse_mode="HTML")
    else:
        bot.send_message(chat_id, mensagem_banco, reply_markup=markup, parse_mode="HTML")

def botoes_paginacao(pagina_atual, total_paginas,total_cartas, comando_base):
    markup = InlineKeyboardMarkup()
    if total_paginas > 1:
        botoes = []
        if pagina_atual > 1:
            botoes.append(InlineKeyboardButton("⬅️", callback_data=f"{comando_base}_pagina_{pagina_atual-1}"))
        if pagina_atual < total_paginas:
            botoes.append(InlineKeyboardButton("➡️", callback_data=f"{comando_base}_pagina_{pagina_atual+1}"))
        markup.row(*botoes)
    return markup

def mostrar_cartas_pagina(chat_id, pagina_atual, total_paginas, cartas, message_id=None):
    offset = (pagina_atual - 1) * 20
    cartas_pagina = cartas[offset:offset + 20]

    mensagem = "📦 Cartas recebidas:\n\n"
    for carta in cartas_pagina:
        id_personagem, quantidade = carta
        mensagem += f"💸 {id_personagem} - {quantidade}\n"
    
    mensagem += f"\nPágina {pagina_atual}/{total_paginas}"

    markup = botoes_paginacao(pagina_atual, total_paginas, 'cartas_compradas')

    if message_id:
        bot.edit_message_text(mensagem, chat_id=chat_id, message_id=message_id, reply_markup=markup)
    else:
        bot.send_message(chat_id, mensagem, reply_markup=markup)

def obter_cartas_do_banco(quantidade):
    conn, cursor = conectar_banco_dados()
    cursor.execute("SELECT id_personagem, quantidade FROM banco_inventario WHERE quantidade > 0")
    cartas_disponiveis = cursor.fetchall()

    if not cartas_disponiveis:
        return []

    cartas_selecionadas = []
    for _ in range(quantidade):
        carta = random.choice(cartas_disponiveis)
        id_personagem, quantidade_disponivel = carta

        # Adicionar a carta selecionada à lista de cartas selecionadas
        cartas_selecionadas.append((id_personagem, 1))

        # Atualizar a quantidade no banco
        nova_quantidade = quantidade_disponivel - 1
        if nova_quantidade > 0:
            cursor.execute("UPDATE banco_inventario SET quantidade = %s WHERE id_personagem = %s", (nova_quantidade, id_personagem))
        else:
            cursor.execute("DELETE FROM banco_inventario WHERE id_personagem = %s", (id_personagem,))

        # Atualizar a lista de cartas disponíveis
        if nova_quantidade > 0:
            cartas_disponiveis = [(id, qtde) if id != id_personagem else (id, nova_quantidade) for id, qtde in cartas_disponiveis]
        else:
            cartas_disponiveis = [(id, qtde) for id, qtde in cartas_disponiveis if id != id_personagem]

    conn.commit()
    
    # Invalidar o cache
    banco_cache.clear()

    fechar_conexao(cursor, conn)
    return cartas_selecionadas

def atualizar_inventario(id_usuario, cartas):
    conn, cursor = conectar_banco_dados()
    for carta in cartas:
        cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (id_usuario, carta[0]))
        resultado = cursor.fetchone()
        if resultado:
            nova_quantidade = resultado[0] + 1
            cursor.execute("UPDATE inventario SET quantidade = %s WHERE id_usuario = %s AND id_personagem = %s", (nova_quantidade, id_usuario, carta[0]))
        else:
            cursor.execute("INSERT INTO inventario (id_usuario, id_personagem, quantidade) VALUES (%s, %s, 1)", (id_usuario, carta[0]))

    conn.commit()
    fechar_conexao(cursor, conn)

def obter_detalhes_personagem(id_personagem):
    conn, cursor = conectar_banco_dados()
    cursor.execute("SELECT emoji, nome, subcategoria FROM personagens WHERE id_personagem = %s", (id_personagem,))
    detalhes = cursor.fetchone()
    
    if not detalhes:
        cursor.execute("SELECT emoji, nome, subcategoria FROM evento WHERE id_personagem = %s", (id_personagem,))
        detalhes = cursor.fetchone()
    
    fechar_conexao(cursor, conn)
    return detalhes

def obter_quantidade_atual(id_usuario, id_personagem):
    conn, cursor = conectar_banco_dados()
    cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (id_usuario, id_personagem))
    quantidade = cursor.fetchone()[0]
    fechar_conexao(cursor, conn)
    return quantidade

def botoes_paginacao_cartas_compradas(pagina_atual, total_paginas):
    markup = InlineKeyboardMarkup()
    if total_paginas > 1:
        botoes = []
        if pagina_atual > 1:
            botoes.append(InlineKeyboardButton("⬅️", callback_data=f"cartas_compradas_pagina_{pagina_atual-1}"))
        if pagina_atual < total_paginas:
            botoes.append(InlineKeyboardButton("➡️", callback_data=f"cartas_compradas_pagina_{pagina_atual+1}"))
        markup.row(*botoes)
    return markup

