@bot.message_handler(commands=['trade'])
def trade_stickers(message):
    user_id = message.from_user.id
    reply_to_message = message.reply_to_message

    if not reply_to_message:
        bot.send_message(message.chat.id, "Você deve responder a uma mensagem da pessoa com quem deseja trocar figurinhas.")
        return

    other_user_id = reply_to_message.from_user.id
    trade_info = message.text.split()[1:]

    if len(trade_info) != 2:
        bot.send_message(message.chat.id, "Formato inválido. Use /trade luv{seu_numero} luv{numero_outro_usuario}")
        return

    try:
        user_sticker_id = int(''.join(filter(str.isdigit, trade_info[0])))
        other_sticker_id = int(''.join(filter(str.isdigit, trade_info[1])))
    except ValueError:
        bot.send_message(message.chat.id, "Os IDs das figurinhas devem conter números. Use /trade luv{seu_numero} luv{numero_outro_usuario}")
        return

    # Verifique se ambos os usuários têm as figurinhas repetidas
    if not has_repeated_sticker(user_id, user_sticker_id):
        bot.send_message(message.chat.id, "Essa figurinha já foi colada e não pode ser trocada.")
        return

    if not has_repeated_sticker(other_user_id, other_sticker_id):
        bot.send_message(message.chat.id, "Essa figurinha do outro usuário já foi colada e não pode ser trocada.")
        return

    # Criar botões para a outra pessoa aceitar ou recusar a troca
    markup = types.InlineKeyboardMarkup()
    accept_button = types.InlineKeyboardButton("Aceitar Troca", callback_data=f"accept_trade_{user_sticker_id}_{other_sticker_id}_{user_id}_{other_user_id}")
    decline_button = types.InlineKeyboardButton("Recusar Troca", callback_data=f"decline_trade_{user_sticker_id}_{other_sticker_id}_{user_id}_{other_user_id}")
    markup.add(accept_button, decline_button)

    bot.send_message(reply_to_message.chat.id, f"{reply_to_message.from_user.first_name}, {message.from_user.first_name} quer trocar a figurinha {user_sticker_id} pela sua figurinha {other_sticker_id}.", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('accept_trade_'))
def accept_trade(call):
    data = call.data.split('_')
    user_sticker_id = int(data[2])
    other_sticker_id = int(data[3])
    requester_id = int(data[4])
    accepter_id = int(data[5])

    if call.from_user.id != accepter_id:
        bot.answer_callback_query(call.id, "Você não tem permissão para aceitar essa troca.")
        return

    # Realizar a troca
    try:
        if execute_trade(requester_id, accepter_id, user_sticker_id, other_sticker_id):
            bot.send_message(call.message.chat.id, "Troca realizada com sucesso!")
        else:
            bot.send_message(call.message.chat.id, "Erro ao realizar a troca. Tente novamente mais tarde.")
    except Exception as e:
        bot.send_message(call.message.chat.id, f"Erro ao realizar a troca: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('decline_trade_'))
def decline_trade(call):
    data = call.data.split('_')
    user_sticker_id = int(data[2])
    other_sticker_id = int(data[3])
    requester_id = int(data[4])
    accepter_id = int(data[5])

    if call.from_user.id != accepter_id:
        bot.answer_callback_query(call.id, "Você não tem permissão para recusar essa troca.")
        return

    bot.send_message(call.message.chat.id, "Troca recusada.")
@bot.callback_query_handler(func=lambda call: call.data == "lembretes")
def lembrete_command(call):
    id_usuario = call.from_user.id
    
    conn, cursor = conectar_banco_dados()
    
    # Verificar se o usuário já tem registros na tabela de lembretes
    cursor.execute("SELECT fonte, gif, diary FROM lembretes WHERE id_usuario = %s", (id_usuario,))
    lembretes = cursor.fetchone()
    
    if not lembretes:
        # Se não existir, criar um novo registro com valores padrão desativados
        cursor.execute("INSERT INTO lembretes (id_usuario, fonte, gif, diary) VALUES (%s, %s, %s, %s)", (id_usuario, False, False, False))
        conn.commit()
        lembretes = (False, False, False)
    
    fonte, gif, diary = lembretes

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(f"Fonte {'✅' if fonte else '❌'}", callback_data=f"lembrete_fonte_{id_usuario}_{not fonte}"))
    markup.add(InlineKeyboardButton(f"GIF {'✅' if gif else '❌'}", callback_data=f"lembrete_gif_{id_usuario}_{not gif}"))
    markup.add(InlineKeyboardButton(f"Diary {'✅' if diary else '❌'}", callback_data=f"lembrete_diary_{id_usuario}_{not diary}"))
    
    bot.edit_message_text("Escolha suas preferências de lembrete:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    
    fechar_conexao(cursor, conn)


def has_repeated_sticker(user_id, sticker_id):
    conn, cursor = conectar_banco_dados()
    cursor.execute('''
        SELECT quantity 
        FROM inventariofig 
        WHERE user_id = %s AND sticker_id = %s
    ''', (user_id, sticker_id))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result and result[0] > 1

def execute_trade(requester_id, accepter_id, requester_sticker_id, accepter_sticker_id):
    conn, cursor = conectar_banco_dados()

    try:
        # Verificar novamente se ambos têm mais de uma unidade das figurinhas
        cursor.execute('''
            SELECT quantity 
            FROM inventariofig 
            WHERE user_id = %s AND sticker_id = %s
        ''', (requester_id, requester_sticker_id))
        requester_quantity = cursor.fetchone()[0]

        cursor.execute('''
            SELECT quantity 
            FROM inventariofig 
            WHERE user_id = %s AND sticker_id = %s
        ''', (accepter_id, accepter_sticker_id))
        accepter_quantity = cursor.fetchone()[0]

        if requester_quantity < 2 or accepter_quantity < 2:
            raise Exception("Uma das figurinhas não é repetida e não pode ser trocada.")

        # Remover uma figurinha do solicitante
        cursor.execute('''
            UPDATE inventariofig 
            SET quantity = quantity - 1 
            WHERE user_id = %s AND sticker_id = %s
        ''', (requester_id, requester_sticker_id))

        # Adicionar a figurinha ao solicitante
        cursor.execute('''
            INSERT INTO inventariofig (user_id, sticker_id, quantity)
            VALUES (%s, %s, 1)
            ON DUPLICATE KEY UPDATE
            quantity = quantity + 1
        ''', (requester_id, accepter_sticker_id))

        # Remover uma figurinha do aceito
        cursor.execute('''
            UPDATE inventariofig 
            SET quantity = quantity - 1 
            WHERE user_id = %s AND sticker_id = %s
        ''', (accepter_id, accepter_sticker_id))

        # Adicionar a figurinha ao aceito
        cursor.execute('''
            INSERT INTO inventariofig (user_id, sticker_id, quantity)
            VALUES (%s, %s, 1)
            ON DUPLICATE KEY UPDATE
            quantity = quantity + 1
        ''', (accepter_id, requester_sticker_id))

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Erro ao realizar a troca: {e}")
        return False
    finally:
        cursor.close()
        conn.close()
        
@bot.message_handler(commands=['album'])
def send_album(message):
    user_id = message.from_user.id
    page = 1  # Página inicial

    
    album_path = create_album(user_id, page)
    if album_path:
        with open(album_path, 'rb') as photo:
            bot.send_photo(message.chat.id, photo, reply_markup=get_navigation_markup(page))
    else:
        bot.send_message(message.chat.id, "Houve um erro ao gerar o álbum. Tente novamente mais tarde.")


@bot.callback_query_handler(func=lambda call: call.data.startswith('page_'))
def callback_page(call):
    user_id = call.from_user.id
    page = int(call.data.split('_')[1])
    album_path = create_album(user_id, page)
    
    if album_path:
        with open(album_path, 'rb') as photo:
            bot.edit_message_media(media=telebot.types.InputMediaPhoto(photo), chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=get_navigation_markup(page))
    else:
        bot.send_message(call.message.chat.id, "Houve um erro ao atualizar o álbum. Tente novamente mais tarde.")

@bot.message_handler(commands=['figurinhas'])
def send_random_stickers(message):
    try:
        user_id = message.from_user.id
        conn, cursor = conectar_banco_dados()

        # Selecionar 5 figurinhas aleatórias, permitindo repetidas
        cursor.execute('SELECT id, image_path FROM stickers')
        all_stickers = cursor.fetchall()
        random_stickers = [random.choice(all_stickers) for _ in range(5)]

        # Verificar quais figurinhas o usuário já possui
        cursor.execute('SELECT sticker_id FROM inventariofig WHERE user_id = %s', (user_id,))
        user_stickers = {row[0] for row in cursor.fetchall()}

        # Adicionar as figurinhas ao inventário do usuário e determinar bordas
        sticker_borders = []
        for sticker_id, sticker_url in random_stickers:
            if sticker_id in user_stickers:
                # Figurinha repetida
                border_color = 'black'
                border_width = 2
                cursor.execute('UPDATE inventariofig SET quantity = quantity + 1 WHERE user_id = %s AND sticker_id = %s', (user_id, sticker_id))
            else:
                # Figurinha nova
                border_color = 'gold'
                border_width = 5
                cursor.execute('INSERT INTO inventariofig (user_id, sticker_id, quantity) VALUES (%s, %s, 1)', (user_id, sticker_id))
                user_stickers.add(sticker_id)
            sticker_borders.append((sticker_url, border_color, border_width))
        
        conn.commit()
        cursor.close()
        conn.close()

        # Baixar a imagem de fundo
        background_url = 'https://telegra.ph/file/33879a99c60ca9d11e60c.png'
        response = requests.get(background_url)
        background = Image.open(BytesIO(response.content))

        # Definir tamanho e layout da imagem final (quadrada)
        width, height = background.size
        sticker_width, sticker_height = 140, 210  # Tamanho das figurinhas
        padding = 20  # Espaço entre figurinhas

        # Redimensionar fundo para um quadrado se necessário
        background = background.resize((width, width))

        # Criar uma nova imagem com o fundo
        img = Image.new('RGB', (width, width))
        img.paste(background, (0, 0))

        draw = ImageDraw.Draw(img)

        # Coordenadas das 5 figurinhas (3-2 centralizado)
        start_x = (width - 3 * sticker_width - 2 * padding) // 2
        start_y = (width - 2 * sticker_height - padding) // 2

        coordinates = [
            (start_x, start_y),
            (start_x + sticker_width + padding, start_y),
            (start_x + 2 * (sticker_width + padding), start_y),
            (start_x + (sticker_width // 2) + (padding // 2), start_y + sticker_height + padding),
            (start_x + sticker_width + (padding // 2) + (sticker_width // 2) + padding, start_y + sticker_height + padding)
        ]

        # Adicionar as figurinhas à imagem
        for (sticker_url, border_color, border_width), coord in zip(sticker_borders, coordinates):
            response = requests.get(sticker_url)
            sticker_image = Image.open(BytesIO(response.content))
            sticker_image = sticker_image.resize((sticker_width, sticker_height))
            
            # Adicionar borda à figurinha
            bordered_sticker = ImageOps.expand(sticker_image, border=border_width, fill=border_color)
            
            # Colar a figurinha na posição correta
            img.paste(bordered_sticker, coord)

        # Salvar a imagem final
        result_image_path = 'random_stickers.png'
        img.save(result_image_path)

        # Enviar a imagem das figurinhas sorteadas
        with open(result_image_path, 'rb') as photo:
            bot.send_photo(message.chat.id, photo)

        bot.reply_to(message, "5 figurinhas aleatórias foram adicionadas ao seu inventário!")
    except Exception as e:
        bot.reply_to(message, f"Houve um erro ao adicionar as figurinhas: {e}")
@bot.message_handler(commands=['albf'])
def send_missing_album_list(message):
    user_id = message.from_user.id
    page = 1
    stickers_per_page = 9
    missing_stickers, total_missing = get_missing_stickers(user_id, page, stickers_per_page)
    total_pages = (total_missing + stickers_per_page - 1) // stickers_per_page

    if not missing_stickers:
        bot.reply_to(message, "Você já possui todas as figurinhas.")
        return

    user_name = message.from_user.first_name
    album_text = '\n'.join([f"luv{sticker[0]} - {sticker[1]}" for sticker in missing_stickers])
    markup = get_missing_album_markup(page, total_pages)
    bot.send_message(message.chat.id, f"Álbum de figurinhas faltantes de {user_name}:\n\n{total_missing}/40\n\n{album_text}", reply_markup=markup)
@bot.message_handler(commands=['fig'])
def send_sticker(message):
    try:
        args = message.text.split()
        if len(args) != 2:
            bot.reply_to(message, "Uso: /fig <id>")
            return
        
        sticker_id = int(args[1].replace('luv', ''))
        sticker = get_sticker_by_id(sticker_id)

        if not sticker:
            bot.reply_to(message, "Figurinha não encontrada.")
            return

        sticker_id, name, image_path = sticker

        caption = f"ID: luv{sticker_id}\nNome: {name}"

        # Enviar a imagem da figurinha diretamente pelo caminho fornecido
        bot.send_photo(message.chat.id, image_path, caption=caption)

    except Exception as e:
        bot.reply_to(message, f"Houve um erro ao buscar a figurinha: {e}")

@bot.message_handler(commands=['alb'])
def send_album_list(message):
    user_id = message.from_user.id
    page = 1
    stickers = get_user_stickers(user_id, page)
    total_pages = get_total_pages(user_id)
    total_stickers = get_total_stickers(user_id)

    if not stickers:
        bot.reply_to(message, "Você não possui figurinhas.")
        return

    user_name = message.from_user.first_name
    album_text = '\n'.join([f"luv{sticker[0]} - {sticker[1]}" + (f" (x{sticker[3]})" if sticker[3] > 1 else "") for sticker in stickers])
    markup = get_album_markup(page, total_pages)
    bot.send_message(message.chat.id, f"Álbum de figurinhas de {user_name}:\n\n{total_stickers}/40\n\n{album_text}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('prev_') or call.data.startswith('next_'))
def callback_page(call):
    user_id = call.from_user.id
    page = int(call.data.split('_')[1])
    stickers = get_user_stickers(user_id, page)
    total_pages = get_total_pages(user_id)
    total_stickers = get_total_stickers(user_id)

    if not stickers:
        bot.answer_callback_query(call.id, "Nenhuma figurinha nesta página.")
        return

    user_name = call.from_user.first_name
    album_text = '\n'.join([f"luv{sticker[0]} - {sticker[1]}" + (f" (x{sticker[3]})" if sticker[3] > 1 else "") for sticker in stickers])
    markup = get_album_markup(page, total_pages)
    bot.edit_message_text(f"Álbum de figurinhas de {user_name}:\n\n{total_stickers}/40\n\n{album_text}", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)
@bot.callback_query_handler(func=lambda call: call.data.startswith('missing_prev_') or call.data.startswith('missing_next_'))
def callback_page_missing(call):
    user_id = call.from_user.id
    page = int(call.data.split('_')[2])
    stickers_per_page = 9
    missing_stickers, total_missing = get_missing_stickers(user_id, page, stickers_per_page)
    total_pages = (total_missing + stickers_per_page - 1) // stickers_per_page

    if not missing_stickers:
        bot.answer_callback_query(call.id, "Nenhuma figurinha faltante nesta página.")
        return

    user_name = call.from_user.first_name
    album_text = '\n'.join([f"luv{sticker[0]} - {sticker[1]}" for sticker in missing_stickers])
    markup = get_missing_album_markup(page, total_pages)
    bot.edit_message_text(f"Álbum de figurinhas faltantes de {user_name}:\n\n{total_missing}/40\n\n{album_text}", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)