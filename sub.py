from pesquisas import *
from user import *
from bd import *
from loja import *
from gnome import *
from cestas import *
from tag import *
from gift import *
from evento import *
from callbacks import *
from operacoes import *
from sub import *
from armazem import *
from wish import *
from cenourar import *
from pescar import *

def handle_sub_s(message, sub_name):
    subcategoria = get_subcategoria_by_name(sub_name)
    if not subcategoria:
        bot.reply_to(message, "Subobra não encontrada.")
        return

    id_subcategoria = subcategoria['id_subcategoria']
    user_id = message.from_user.id

    personagens_ids_quantidade = get_personagens_ids_quantidade_por_subcategoria_s(id_subcategoria, user_id)

    if not personagens_ids_quantidade:
        response = f"Você não possui nenhum personagem de {subcategoria['nomesub']}."
        bot.reply_to(message, response)
        return

    total_personagens = len(personagens_ids_quantidade)
    total_subobra = get_total_personagens_subobra(id_subcategoria)

    items_por_pagina = 1
    paginas = criar_lista_paginas(personagens_ids_quantidade, items_por_pagina)

    for i, pagina in enumerate(paginas, start=1):
        response = f"💌 | <b>{subcategoria['nomesub']}</b>\n⏱️ | ({total_personagens}/{total_subobra}) - Página {i}\n\n"
        response += '\n'.join(pagina)
        bot.send_photo(message.chat.id, subcategoria['imagem'], caption=response, parse_mode='HTML')

def handle_sub_f(message, sub_name):
    subcategoria = get_subcategoria_by_name(sub_name)
    if not subcategoria:
        bot.reply_to(message, "Subobra não encontrada.")
        return

    id_subcategoria = subcategoria['id_subcategoria']
    user_id = message.from_user.id

    personagens_ids_quantidade = get_personagens_ids_quantidade_por_subcategoria_f(id_subcategoria, user_id)

    if not personagens_ids_quantidade:
        response = f"Você já possui todos os personagens de {subcategoria['nomesub']}."
        bot.reply_to(message, response)
        return

    total_personagens = len(personagens_ids_quantidade)
    total_subobra = get_total_personagens_subobra(id_subcategoria)

    items_por_pagina = 1
    paginas = criar_lista_paginas(personagens_ids_quantidade, items_por_pagina)

    for i, pagina in enumerate(paginas, start=1):
        response = f"💌 | <b>{subcategoria['nomesub']}</b>\n⏱️ | ({total_personagens}/{total_subobra}) - Página {i}\n\n"
        response += '\n'.join(pagina)
        bot.send_photo(message.chat.id, subcategoria['imagem'], caption=response, parse_mode='HTML')
def get_personagens_ids_quantidade_por_subcategoria_s(id_subcategoria, user_id):
    query = """
    SELECT aps.id_personagem, SUM(inv.quantidade) as quantidade
    FROM associacao_pessoa_subcategoria aps
    LEFT JOIN inventario inv ON aps.id_personagem = inv.id_personagem AND inv.id_usuario = %s
    WHERE aps.id_subcategoria = %s
    AND (inv.id_personagem IS NOT NULL AND inv.quantidade > 0)
    GROUP BY aps.id_personagem
    """
    cursor.execute(query, (user_id, id_subcategoria))
    return {row[0]: row[1] for row in cursor.fetchall()}

def get_personagens_ids_por_subcategoria_f(id_subcategoria, user_id):
    query = """
    SELECT aps.id_personagem
    FROM associacao_pessoa_subcategoria aps
    LEFT JOIN inventario inv ON aps.id_personagem = inv.id_personagem AND inv.id_usuario = %s
    WHERE aps.id_subcategoria = %s
    AND (inv.id_personagem IS NULL OR inv.quantidade = 0)
    """
    cursor.execute(query, (user_id, id_subcategoria))
    return [row[0] for row in cursor.fetchall()]

def get_subcategoria_by_name(sub_name):
    query = "SELECT * FROM subcategorias WHERE nomesub = %s"
    cursor.execute(query, (sub_name,))
    result = cursor.fetchone()
    if result:
        return {
            'id_subcategoria': result[0],
            'nomesub': result[1],
            'imagem': result[3]
        }
    return None

def get_personagem_by_id(id_personagem, cursor, retries=3):
    query = "SELECT * FROM cartas WHERE id = %s"
    for attempt in range(retries):
        try:
            cursor.execute(query, (id_personagem,))
            result = cursor.fetchone()
            if result:
                return {
                    'id': result[0],
                    'nome': result[1],
                    'subcategoria': result[2],
                    'emoji': result[3],
                    'categoria': result[4],
                    'imagem': result[5]
                }
            return None
        except Error as e:
            if e.errno == 1205:  # Error code for lock wait timeout
                if attempt < retries - 1:
                    print(f"Lock wait timeout exceeded, retrying... (attempt {attempt + 1}/{retries})")
                    time.sleep(2)  # Wait before retrying
                else:
                    print("Lock wait timeout exceeded, no more retries left.")
                    raise
            else:
                raise

def get_inventario_do_usuario_por_personagem(user_id, personagem_id):
    query = "SELECT * FROM inventario WHERE id_usuario = %s AND id_personagem = %s"
    cursor.execute(query, (user_id, personagem_id))
    row = cursor.fetchone()
    if row:
        return {'quantidade': row[3]}
    return None

def get_total_personagens_subobra(id_subcategoria):
    query = "SELECT COUNT(*) FROM associacao_pessoa_subcategoria WHERE id_subcategoria = %s"
    cursor.execute(query, (id_subcategoria,))
    result = cursor.fetchone()
    if result:
        return result[0]
    return 0

def get_personagens_ids_quantidade_por_subcategoria_f(id_subcategoria, user_id):
    query = """
    SELECT aps.id_personagem, SUM(inv.quantidade) as quantidade
    FROM associacao_pessoa_subcategoria aps
    LEFT JOIN inventario inv ON aps.id_personagem = inv.id_personagem AND inv.id_usuario = %s
    WHERE aps.id_subcategoria = %s
    AND (inv.id_personagem IS NULL OR inv.quantidade = 0)
    GROUP BY aps.id_personagem
    """
    cursor.execute(query, (user_id, id_subcategoria))
    return {row[0]: row[1] for row in cursor.fetchall()}
def processar_submenus_command(message):
    try:
        parts = message.text.split(' ', 1)
        conn, cursor = conectar_banco_dados()

        if len(parts) == 1:
            pagina = 1
            submenus_por_pagina = 15

            query_todos_submenus = """
            SELECT subcategoria, submenu
            FROM personagens
            WHERE submenu IS NOT NULL AND submenu != ''
            GROUP BY subcategoria, submenu
            ORDER BY subcategoria, submenu
            LIMIT %s OFFSET %s
            """
            offset = (pagina - 1) * submenus_por_pagina
            cursor.execute(query_todos_submenus, (submenus_por_pagina, offset))
            submenus = cursor.fetchall()
            cursor.execute("SELECT COUNT(DISTINCT subcategoria, submenu) FROM personagens WHERE submenu IS NOT NULL AND submenu != ''")
            total_submenus = cursor.fetchone()[0]
            total_paginas = (total_submenus // submenus_por_pagina) + (1 if total_submenus % submenus_por_pagina > 0 else 0)

            if submenus:
                mensagem = "<b>📂 Todos os Submenus:</b>\n\n"
                for subcategoria, submenu in submenus:
                    mensagem += f"🍎 {subcategoria} - {submenu}\n"
                mensagem += f"\nPágina {pagina}/{total_paginas}"
                markup = InlineKeyboardMarkup()
                if total_paginas > 1:
                    markup.row(
                        InlineKeyboardButton("⬅️", callback_data=f"navigate_submenus_{pagina - 1 if pagina > 1 else total_paginas}"),
                        InlineKeyboardButton("➡️", callback_data=f"navigate_submenus_{pagina + 1 if pagina < total_paginas else 1}")
                    )

                bot.send_message(message.chat.id, mensagem, parse_mode="HTML", reply_to_message_id=message.message_id, reply_markup=markup)
            else:
                bot.send_message(message.chat.id, "Não foram encontrados submenus.", parse_mode="HTML", reply_to_message_id=message.message_id)

        else:
            subcategoria = parts[1].strip()
            query_submenus = """
            SELECT DISTINCT submenu
            FROM personagens
            WHERE subcategoria = %s AND submenu IS NOT NULL AND submenu != ''
            """
            cursor.execute(query_submenus, (subcategoria,))
            submenus = [row[0] for row in cursor.fetchall()]

            if submenus:
                mensagem = f"<b>🌳 Submenus na subcategoria {subcategoria.title()}:</b>\n\n"
                for submenu in submenus:
                    mensagem += f"🍎 {subcategoria.title()}- {submenu}\n"
            else:
                mensagem = f"Não foram encontrados submenus para a subcategoria '{subcategoria.title()}'."

            bot.send_message(message.chat.id, mensagem, parse_mode="HTML", reply_to_message_id=message.message_id)

    except Exception as e:
        print(f"Erro ao processar comando /submenus: {e}")

    finally:
        fechar_conexao(cursor, conn)


def processar_submenu_command(message):
    try:
        parts = message.text.split(' ', 2)
        if len(parts) < 3:
            bot.reply_to(message, "Por favor, forneça o tipo ('s' ou 'f') e o nome do submenu após o comando, por exemplo: /submenu s bts")
            return

        tipo = parts[1].strip()
        submenu = parts[2].strip()

        submenu_proximo = encontrar_submenu_proximo(submenu)
        if not submenu_proximo:
            bot.reply_to(message, "Submenu não identificado. Verifique se digitou corretamente.")
            return

        id_usuario = message.from_user.id
        nome_usuario = message.from_user.first_name

        conn, cursor = conectar_banco_dados()

        query_todos = """
        SELECT id_personagem, nome, subcategoria
        FROM personagens
        WHERE submenu = %s
        """
        cursor.execute(query_todos, (submenu_proximo,))
        todos_personagens = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}

        if not todos_personagens:
            bot.reply_to(message, f"O submenu '{submenu_proximo}' não existe.")
            return

        query_possui = """
        SELECT per.id_personagem, per.nome, per.subcategoria
        FROM inventario inv
        JOIN personagens per ON inv.id_personagem = per.id_personagem
        WHERE inv.id_usuario = %s AND per.submenu = %s
        """
        cursor.execute(query_possui, (id_usuario, submenu_proximo))
        personagens_possui = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}

        subcategoria = next(iter(todos_personagens.values()), ("", ""))[1]  # Definindo subcategoria para uso na mensagem

        if tipo == 's':
            if personagens_possui:
                mensagem = f"☀️ Peixes do submenu na cesta de {nome_usuario}!\n\n"
                mensagem += f"🌳 | {subcategoria} \n"
                mensagem += f"🍎 | {submenu_proximo}\n"
                mensagem += f"🐟 | {len(personagens_possui)}/{len(todos_personagens)}\n\n"
                for id_personagem, (nome, subcategoria) in personagens_possui.items():
                    mensagem += f"<code>{id_personagem}</code> • {nome}\n"
            else:
                mensagem = f"🌧️ Você não possui nenhum personagem neste submenu."

        elif tipo == 'f':
            personagens_faltantes = {id_personagem: (nome, subcategoria) for id_personagem, (nome, subcategoria) in todos_personagens.items() if id_personagem not in personagens_possui}
            if personagens_faltantes:
                mensagem = f"🌧️ Faltam do submenu na cesta de {nome_usuario}:\n\n"
                mensagem += f"🌳 | {subcategoria} \n"
                mensagem += f"🍎 | {submenu_proximo}\n"
                mensagem += f"🐟 | {len(personagens_faltantes)}/{len(todos_personagens)}\n\n"
                for id_personagem, (nome, subcategoria) in personagens_faltantes.items():
                    mensagem += f"<code>{id_personagem}</code> • {nome}\n"
            else:
                mensagem = f"☀️ Nada como a alegria de ter todos os peixes de {submenu_proximo} na cesta!"

        else:
            bot.reply_to(message, "Tipo inválido. Use 's' para os personagens que você possui e 'f' para os que você não possui.")
            return

        bot.send_message(message.chat.id, mensagem, parse_mode="HTML")

    except Exception as e:
        print(f"Erro ao processar comando /submenu: {e}")

    finally:
        fechar_conexao(cursor, conn)


def callback_navegacao_submenus(call):
    try:
        data = call.data.split('_')
        pagina_str = data[-1]
        pagina = int(pagina_str)
        submenus_por_pagina = 15

        conn, cursor = conectar_banco_dados()

        query_todos_submenus = """
        SELECT subcategoria, submenu
        FROM personagens
        WHERE submenu IS NOT NULL AND submenu != ''
        GROUP BY subcategoria, submenu
        ORDER BY subcategoria, submenu
        LIMIT %s OFFSET %s
        """
        offset = (pagina - 1) * submenus_por_pagina
        cursor.execute(query_todos_submenus, (submenus_por_pagina, offset))
        submenus = cursor.fetchall()

        cursor.execute("SELECT COUNT(DISTINCT subcategoria, submenu) FROM personagens WHERE submenu IS NOT NULL AND submenu != ''")
        total_submenus = cursor.fetchone()[0]
        total_paginas = (total_submenus // submenus_por_pagina) + (1 if total_submenus % submenus_por_pagina > 0 else 0)

        if submenus:
            mensagem = "<b>🌳 Todos os Submenus: </b>\n\n"
            for subcategoria, submenu in submenus:
                mensagem += f"🍎 {subcategoria} - {submenu}\n"
            mensagem += f"\nPágina {pagina}/{total_paginas}"

            markup = InlineKeyboardMarkup()
            if total_paginas > 1:
                markup.row(
                    InlineKeyboardButton("⬅️", callback_data=f"navigate_submenus_{pagina - 1 if pagina > 1 else total_paginas}"),
                    InlineKeyboardButton("➡️", callback_data=f"navigate_submenus_{pagina + 1 if pagina < total_paginas else 1}")
                )

            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=mensagem, parse_mode="HTML", reply_markup=markup)

    except Exception as e:
        print(f"Erro ao processar callback de navegação: {e}")

    finally:
        fechar_conexao(cursor, conn)


def encontrar_submenu_proximo(submenu):
    try:
        conn, cursor = conectar_banco_dados()
        query = "SELECT DISTINCT submenu FROM personagens WHERE submenu LIKE %s LIMIT 1"
        cursor.execute(query, (f"%{submenu}%",))
        resultado = cursor.fetchone()
        return resultado[0] if resultado else None
    except Exception as e:
        print(f"Erro ao encontrar submenu mais próximo: {e}")
        return None
    finally:
        fechar_conexao(cursor, conn)


def processar_sub_command(message):
    try:
        parts = message.text.split(' ', 2)
        if len(parts) < 2:
            bot.reply_to(message, "Por favor, forneça o tipo ('s' ou 'f') e o nome do sub após o comando, por exemplo: /sub s loona")
            return

        tipo = parts[1].strip().lower()
        sub_nome = parts[2].strip().lower() if len(parts) > 2 else None

        id_usuario = message.from_user.id
        nome_usuario = message.from_user.first_name

        conn, cursor = conectar_banco_dados()

        # Corrigir a consulta para incluir o emoji
        query_todos = """
        SELECT s.id_personagem, p.nome, p.subcategoria, p.emoji
        FROM sub s
        JOIN personagens p ON s.id_personagem = p.id_personagem
        WHERE s.sub_nome = %s
        """
        cursor.execute(query_todos, (sub_nome,))
        todos_personagens = {row[0]: (row[1], row[2], row[3]) for row in cursor.fetchall()}

        if not todos_personagens:
            bot.reply_to(message, f"O sub '{sub_nome}' não existe.")
            return

        # Adicionar o emoji também no inventário
        query_possui = """
        SELECT s.id_personagem, p.nome, p.subcategoria, p.emoji
        FROM inventario inv
        JOIN sub s ON inv.id_personagem = s.id_personagem
        JOIN personagens p ON s.id_personagem = p.id_personagem
        WHERE inv.id_usuario = %s AND s.sub_nome = %s
        """
        cursor.execute(query_possui, (id_usuario, sub_nome))
        personagens_possui = {row[0]: (row[1], row[2], row[3]) for row in cursor.fetchall()}

        query_imagem = """
        SELECT Imagem FROM subcategorias WHERE nomesub = %s
        """
        cursor.execute(query_imagem, (sub_nome,))
        resultado_imagem = cursor.fetchone()
        imagem_subgrupo = resultado_imagem[0] if resultado_imagem else None

        subcategoria = next(iter(todos_personagens.values()), ("", ""))[1]

        if tipo == 's':
            if personagens_possui:
                enviar_pagina(message.chat.id, message.message_id, 1, 's', personagens_possui, len(todos_personagens), sub_nome, nome_usuario, imagem_subgrupo, id_usuario, is_first_page=True)
            else:
                bot.reply_to(message, f"🌧️ Você não possui nenhum personagem neste subgrupo.")

        elif tipo == 'f':
            personagens_faltantes = {id_personagem: (nome, subcategoria, emoji) for id_personagem, (nome, subcategoria, emoji) in todos_personagens.items() if id_personagem not in personagens_possui}
            if personagens_faltantes:
                enviar_pagina(message.chat.id, message.message_id, 1, 'f', personagens_faltantes, len(todos_personagens), sub_nome, nome_usuario, imagem_subgrupo, id_usuario, is_first_page=True)
            else:
                bot.reply_to(message, f"☀️ Nada como a alegria de ter todos os personagens de {sub_nome.capitalize()} na cesta!")

        elif tipo == 'all':
            enviar_pagina(message.chat.id, message.message_id, 1, 'all', todos_personagens, len(todos_personagens), sub_nome, "", imagem_subgrupo, id_usuario, is_first_page=True)

        else:
            bot.reply_to(message, "Tipo inválido. Use 's' para os personagens que você possui, 'f' para os que você não possui, ou 'all' para ver todos.")

    except Exception as e:
        print(f"Erro ao processar comando /sub: {e}")

    finally:
        fechar_conexao(cursor, conn)


def callback_pagina_sub(call):
    try:
        partes = call.data.split('_')
        tipo = partes[0]
        pagina = int(partes[2])
        sub_nome = partes[3]
        id_usuario = int(partes[4])  # O ID do usuário original que iniciou a interação

        conn, cursor = conectar_banco_dados()

        # Consulta para todos os personagens, incluindo o emoji
        query_todos = """
        SELECT s.id_personagem, p.nome, p.subcategoria, p.emoji
        FROM sub s
        JOIN personagens p ON s.id_personagem = p.id_personagem
        WHERE s.sub_nome = %s
        """
        cursor.execute(query_todos, (sub_nome,))
        todos_personagens = {row[0]: (row[1], row[2], row[3]) for row in cursor.fetchall()}

        # Consulta para os personagens que o usuário possui, incluindo o emoji
        query_possui = """
        SELECT s.id_personagem, p.nome, p.subcategoria, p.emoji
        FROM inventario inv
        JOIN sub s ON inv.id_personagem = s.id_personagem
        JOIN personagens p ON s.id_personagem = p.id_personagem
        WHERE inv.id_usuario = %s AND s.sub_nome = %s
        """
        cursor.execute(query_possui, (id_usuario, sub_nome))
        personagens_possui = {row[0]: (row[1], row[2], row[3]) for row in cursor.fetchall()}

        query_imagem = """
        SELECT Imagem FROM subcategorias WHERE nomesub = %s
        """
        cursor.execute(query_imagem, (sub_nome,))
        resultado_imagem = cursor.fetchone()
        imagem_subgrupo = resultado_imagem[0] if resultado_imagem else None

        nome_usuario = call.from_user.first_name

        if tipo == 's':
            enviar_pagina(call.message.chat.id, call.message.message_id, pagina, 's', personagens_possui, len(todos_personagens), sub_nome, nome_usuario, imagem_subgrupo, id_usuario)
        elif tipo == 'f':
            personagens_faltantes = {id_personagem: (nome, subcategoria, emoji) for id_personagem, (nome, subcategoria, emoji) in todos_personagens.items() if id_personagem not in personagens_possui}
            enviar_pagina(call.message.chat.id, call.message.message_id, pagina, 'f', personagens_faltantes, len(todos_personagens), sub_nome, nome_usuario, imagem_subgrupo, id_usuario)
        elif tipo == 'all':
            enviar_pagina(call.message.chat.id, call.message.message_id, pagina, 'all', todos_personagens, len(todos_personagens), sub_nome, nome_usuario, imagem_subgrupo, id_usuario)

        bot.answer_callback_query(call.id)

    except Exception as e:
        print(f"Erro ao processar callback de navegação: {e}")
        bot.send_message(call.message.chat.id, "Ocorreu um erro ao processar a navegação.")
    finally:
        fechar_conexao(cursor, conn)


def enviar_pagina(chat_id, message_id, pagina, tipo, personagens, total_personagens, sub_nome, nome_usuario, imagem_subgrupo, id_usuario, is_first_page=False):
    itens_por_pagina = 15
    inicio = (pagina - 1) * itens_por_pagina
    fim = inicio + itens_por_pagina
    personagens_pagina = list(personagens.items())[inicio:fim]
    
    if tipo == 's':
        titulo = f"☀️ Peixes do subgrupo {sub_nome.title()} na cesta de {nome_usuario} 👩🏻‍🌾!\n\n🐟 | {len(personagens)}/{total_personagens}"
    elif tipo == 'f':
        titulo = f"☀️ Peixes do subgrupo {sub_nome.title()} faltantes na cesta de {nome_usuario} 👩🏻‍🌾!\n\n🐟 | {len(personagens)}/{total_personagens}"
    elif tipo == 'all':
        titulo = f"🌳 Todos os Peixes do subgrupo {sub_nome.title()}"

    # Preparar a mensagem com os personagens da página atual
    mensagem = f"{titulo}\n\n"
    for id_personagem, (nome, subcategoria, emoji) in personagens_pagina:
        mensagem += f"{emoji} <code>{id_personagem}</code> • {nome}\n"

    # Preparar os botões de navegação
    markup = InlineKeyboardMarkup()
    if pagina > 1:
        markup.add(InlineKeyboardButton("⬅️ Anterior", callback_data=f"{tipo}_pagina_{pagina-1}_{sub_nome}_{id_usuario}"))
    if fim < len(personagens):
        markup.add(InlineKeyboardButton("Próxima ➡️", callback_data=f"{tipo}_pagina_{pagina+1}_{sub_nome}_{id_usuario}"))

    # Se for a primeira página, enviar a foto, caso contrário, editar a mensagem anterior
    if is_first_page and imagem_subgrupo:
        bot.send_photo(chat_id, imagem_subgrupo, caption=mensagem, reply_markup=markup, parse_mode="HTML")
    else:
        bot.edit_message_text(mensagem, chat_id=chat_id, message_id=message_id, reply_markup=markup, parse_mode="HTML")

