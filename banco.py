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

import random
import mysql.connector
from bd import conectar_banco_dados, fechar_conexao

# Função para processar a compra de pacotes de cartas por categoria
def processar_compra_vendinha_categoria(call):
    try:
        partes = call.data.split('_')
        pacote = partes[2]
        categoria = partes[3]

        pacotes = {
            'basico': (10, 50),  # 10 cartas, 50 cenouras
            'prata': (25, 100),  # 25 cartas, 100 cenouras
            'ouro': (80, 200)    # 80 cartas, 200 cenouras
        }

        if pacote in pacotes:
            quantidade, preco = pacotes[pacote]
            id_usuario = call.from_user.id

            # Ajuste de preço para categorias específicas
            if categoria != 'geral':
                preco *= 2

            conn, cursor = conectar_banco_dados()
            cursor.execute("SELECT cenouras FROM usuarios WHERE id_usuario = %s", (id_usuario,))
            cenouras = cursor.fetchone()[0]

            if cenouras >= preco:
                # Obter cartas com base na categoria
                if categoria == 'geral':
                    cartas = obter_cartas_do_inventario(quantidade)
                else:
                    cartas = obter_cartas_categoria_do_inventario(quantidade, categoria)

                if isinstance(cartas, list):
                    atualizar_inventario(id_usuario, cartas)
                    cursor.execute("UPDATE usuarios SET cenouras = cenouras - %s WHERE id_usuario = %s", (preco, id_usuario))
                    conn.commit()

                    globals.cartas_compradas_dict[id_usuario] = cartas

                    bot.edit_message_caption(caption=f"Compra realizada com sucesso! Você comprou {quantidade} cartas de {categoria.capitalize()}.", chat_id=call.message.chat.id, message_id=call.message.message_id)
                    mostrar_cartas_compradas(call.message.chat.id, cartas, id_usuario, 1, call.message.message_id)
                else:
                    bot.edit_message_caption(caption="Erro ao buscar cartas. Tente novamente mais tarde.", chat_id=call.message.chat.id, message_id=call.message.message_id)
            else:
                bot.edit_message_caption(caption="Cenouras insuficientes para realizar a compra.", chat_id=call.message.chat.id, message_id=call.message.message_id)
        else:
            bot.edit_message_caption(caption="Pacote inválido.", chat_id=call.message.chat.id, message_id=call.message.message_id)

    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        fechar_conexao(cursor, conn)

# Função para obter cartas aleatórias do inventário
def obter_cartas_do_inventario(quantidade):
    conn, cursor = conectar_banco_dados()
    
    # Obter cartas do banco de inventário
    query_inventario = """
    SELECT bi.id_personagem, p.nome, p.subcategoria, p.imagem, p.emoji
    FROM banco_inventario bi
    JOIN personagens p ON bi.id_personagem = p.id_personagem
    WHERE bi.quantidade > 0
    ORDER BY RAND() LIMIT %s
    """
    cursor.execute(query_inventario, (quantidade,))
    cartas_inventario = cursor.fetchall()

    # Obter cartas de eventos
    query_evento = """
    SELECT e.id_personagem, e.nome, e.subcategoria, e.imagem, e.emoji
    FROM evento e
    ORDER BY RAND() LIMIT %s
    """
    # Selecionar uma fração de cartas do evento
    quantidade_evento = max(1, quantidade // 10)  # Por exemplo, 25% das cartas podem ser de eventos
    cursor.execute(query_evento, (quantidade_evento,))
    cartas_evento = cursor.fetchall()

    # Combinar cartas do inventário e do evento
    todas_cartas = cartas_inventario + cartas_evento
    random.shuffle(todas_cartas)  # Embaralha a lista de cartas

    fechar_conexao(cursor, conn)
    return todas_cartas

# Função para obter cartas de uma categoria específica
def obter_cartas_categoria_do_inventario(quantidade, categoria):
    conn, cursor = conectar_banco_dados()
    
    # Obter cartas da categoria especificada no banco de inventário
    query_inventario = """
    SELECT bi.id_personagem, p.nome, p.subcategoria, p.imagem, p.emoji
    FROM banco_inventario bi
    JOIN personagens p ON bi.id_personagem = p.id_personagem
    WHERE bi.quantidade > 0 AND p.categoria = %s
    ORDER BY RAND() LIMIT %s
    """
    cursor.execute(query_inventario, (categoria, quantidade))
    cartas_inventario = cursor.fetchall()

    # Obter cartas de eventos
    query_evento = """
    SELECT e.id_personagem, e.nome, e.subcategoria, e.imagem, e.emoji
    FROM evento e
    ORDER BY RAND() LIMIT %s
    """
    # Selecionar uma fração de cartas do evento
    quantidade_evento = max(1, quantidade // 10)  # Por exemplo, 25% das cartas podem ser de eventos
    cursor.execute(query_evento, (quantidade_evento,))
    cartas_evento = cursor.fetchall()

    # Combinar cartas do inventário e do evento
    todas_cartas = cartas_inventario + cartas_evento
    random.shuffle(todas_cartas)  # Embaralha a lista de cartas

    fechar_conexao(cursor, conn)
    return todas_cartas

def processar_saldo_usuario(message):
    try:
        id_usuario = message.from_user.id
        
        conn, cursor = conectar_banco_dados()

        # Obter saldo total de cenouras do banco
        cursor.execute("SELECT SUM(quantidade_cenouras) FROM banco_cidade")
        total_cenouras_banco = cursor.fetchone()[0] or 0

        # Obter saldo total de cartas no banco de inventário
        cursor.execute("SELECT SUM(quantidade) FROM banco_inventario")
        total_cartas_banco = cursor.fetchone()[0] or 0

        # Obter saldo de cenouras do usuário
        cursor.execute("SELECT cenouras, iscas FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        resultado = cursor.fetchone()
        if resultado:
            saldo_cenouras_usuario, saldo_iscas_usuario = resultado
        else:
            saldo_cenouras_usuario, saldo_iscas_usuario = 0, 0

        # Montar a mensagem de saldo
        resposta = f"💰 <b>Saldo da Cidade:</b>\n"
        resposta += f"🥕 Total de cenouras: {total_cenouras_banco}\n"
        resposta += f"📦 Total de cartas: {total_cartas_banco}\n\n"
        resposta += f"💼 <b>Saldo do Camponês:</b>\n"
        resposta += f"🥕 Suas cenouras: {saldo_cenouras_usuario}\n"
        resposta += f"🪝 Suas iscas: {saldo_iscas_usuario}\n"

        # Enviar a mensagem
        bot.send_message(message.chat.id, resposta, parse_mode="HTML")
        
    except Exception as e:
        print(f"Erro ao processar comando /saldo: {e}")
        bot.reply_to(message, "Ocorreu um erro ao verificar seu saldo.")
    finally:
        fechar_conexao(cursor, conn)


def processar_banco_command(message):
    try:
        parts = message.text.split(' ', 2)
        categoria = parts[1].strip() if len(parts) > 1 else None
        subcategoria = parts[2].strip() if len(parts) > 2 else None

        conn, cursor = conectar_banco_dados()

        # Construir a consulta SQL com base na categoria e subcategoria
        query = "SELECT p.id_personagem, bi.quantidade, p.nome, p.subcategoria, p.emoji FROM banco_inventario bi JOIN personagens p ON bi.id_personagem = p.id_personagem"
        query_params = []

        if categoria:
            query += " WHERE p.categoria = %s"
            query_params.append(categoria)
        if subcategoria:
            query += " AND p.subcategoria = %s"
            query_params.append(subcategoria)

        query += " ORDER BY p.id_personagem ASC"
        
        cursor.execute(query, tuple(query_params))
        cartas_banco = cursor.fetchall()

        if not cartas_banco:
            bot.send_message(message.chat.id, "Não há cartas no banco para os critérios especificados.")
            return

        total_paginas = (len(cartas_banco) // 30) + (1 if len(cartas_banco) % 30 > 0 else 0)
        total_cartas = sum([quantidade for _, quantidade, _, _, _ in cartas_banco])
        
        mostrar_cartas_banco(message.chat.id, 1, total_paginas, cartas_banco, total_cartas, message.message_id, categoria, subcategoria)

    except Exception as e:
        print(f"Erro ao processar o comando /banco: {e}")
        bot.send_message(message.chat.id, "Erro ao processar o comando.")
    finally:
        fechar_conexao(cursor, conn)


def processar_callback_banco_pagina(call):
    data = call.data.split('_')
    pagina = int(data[2])
    categoria = data[3] if len(data) > 3 and data[3] else None
    subcategoria = data[4] if len(data) > 4 and data[4] else None

    conn, cursor = conectar_banco_dados()

    query = "SELECT p.id_personagem, bi.quantidade, p.nome, p.subcategoria, p.emoji FROM banco_inventario bi JOIN personagens p ON bi.id_personagem = p.id_personagem"
    query_params = []

    if categoria:
        query += " WHERE p.categoria = %s"
        query_params.append(categoria)
    if subcategoria:
        query += " AND p.subcategoria = %s"
        query_params.append(subcategoria)

    query += " ORDER BY p.id_personagem ASC"
    
    cursor.execute(query, tuple(query_params))
    cartas_banco = cursor.fetchall()

    total_paginas = (len(cartas_banco) // 30) + (1 if len(cartas_banco) % 30 > 0 else 0)
    total_cartas = sum([quantidade for _, quantidade, _, _, _ in cartas_banco])

    mostrar_cartas_banco(call.message.chat.id, pagina, total_paginas, cartas_banco, total_cartas, call.message.message_id, categoria, subcategoria)

    fechar_conexao(cursor, conn)


def processar_callback_cartas_compradas(call):
    pagina_atual = int(call.data.split('_')[-1])
    id_usuario = call.from_user.id

    if id_usuario in globals.cartas_compradas_dict:
        cartas = globals.cartas_compradas_dict[id_usuario]
        mostrar_cartas_compradas(call.message.chat.id, cartas, id_usuario, pagina_atual, call.message.message_id)
    else:
        bot.send_message(call.message.chat.id, "Erro ao exibir cartas compradas. Tente novamente.")

    fechar_conexao(cursor, conn)
