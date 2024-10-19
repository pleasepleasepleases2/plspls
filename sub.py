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
