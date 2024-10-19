from telebot import types
import globals

# Função para inicializar o tabuleiro vazio
def inicializar_tabuleiro():
    return [' ' for _ in range(9)]

# Função para mostrar o tabuleiro formatado
def mostrar_tabuleiro(tabuleiro):
    return f"{tabuleiro[0]} | {tabuleiro[1]} | {tabuleiro[2]}\n" \
           f"--+---+--\n" \
           f"{tabuleiro[3]} | {tabuleiro[4]} | {tabuleiro[5]}\n" \
           f"--+---+--\n" \
           f"{tabuleiro[6]} | {tabuleiro[7]} | {tabuleiro[8]}"

# Função para criar botões interativos para o tabuleiro
def criar_botoes_tabuleiro(tabuleiro):
    markup = types.InlineKeyboardMarkup()
    botoes = []
    for i in range(9):
        texto = tabuleiro[i] if tabuleiro[i] != ' ' else str(i + 1)
        botoes.append(types.InlineKeyboardButton(text=texto, callback_data=str(i)))
        if (i + 1) % 3 == 0:
            markup.row(*botoes)
            botoes = []
    return markup

# Função para verificar se há um vencedor
def verificar_vitoria(tabuleiro, jogador):
    vitorias = [(0, 1, 2), (3, 4, 5), (6, 7, 8),  # Linhas
                (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Colunas
                (0, 4, 8), (2, 4, 6)]             # Diagonais
    return any(tabuleiro[a] == tabuleiro[b] == tabuleiro[c] == jogador for a, b, c in vitorias)

# Função para verificar se houve empate
def verificar_empate(tabuleiro):
    return all(celula != ' ' for celula in tabuleiro)

# Função para iniciar o jogo da velha
def iniciar_jogo(bot, message):
    id_usuario = message.from_user.id
    tabuleiro = inicializar_tabuleiro()
    globals.jogos_da_velha[id_usuario] = tabuleiro
    
    bot.send_message(message.chat.id, f"Vamos jogar Jogo da Velha! Você é 'X' e eu sou 'O'.\n\n{mostrar_tabuleiro(tabuleiro)}",
                     reply_markup=criar_botoes_tabuleiro(tabuleiro))

# Função para o bot fazer uma jogada aleatória
def bot_fazer_jogada(tabuleiro):
    for i in range(9):
        if tabuleiro[i] == ' ':
            tabuleiro[i] = 'O'
            break
    return tabuleiro

# Função para processar as jogadas do jogador
def jogador_fazer_jogada(bot, call):
    try:
        id_usuario = call.from_user.id
        if id_usuario not in globals.jogos_da_velha:
            bot.send_message(call.message.chat.id, "Você não iniciou um jogo da velha. Use /jogodavelha para começar.")
            return

        tabuleiro = globals.jogos_da_velha[id_usuario]
        jogada = int(call.data)

        if tabuleiro[jogada] != ' ':
            bot.answer_callback_query(call.id, "Essa posição já está ocupada!")
            return

        # Jogada do jogador
        tabuleiro[jogada] = 'X'

        # Verifica se o jogador venceu
        if verificar_vitoria(tabuleiro, 'X'):
            bot.edit_message_text(f"🎉 Parabéns! Você venceu!\n\n{mostrar_tabuleiro(tabuleiro)}", call.message.chat.id, call.message.message_id)
            del globals.jogos_da_velha[id_usuario]
            return

        # Verifica se houve empate
        if verificar_empate(tabuleiro):
            bot.edit_message_text(f"😐 Empate!\n\n{mostrar_tabuleiro(tabuleiro)}", call.message.chat.id, call.message.message_id)
            del globals.jogos_da_velha[id_usuario]
            return

        # Jogada do bot
        tabuleiro = bot_fazer_jogada(tabuleiro)

        # Verifica se o bot venceu
        if verificar_vitoria(tabuleiro, 'O'):
            bot.edit_message_text(f"😎 Eu venci! Melhor sorte da próxima vez.\n\n{mostrar_tabuleiro(tabuleiro)}", call.message.chat.id, call.message.message_id)
            del globals.jogos_da_velha[id_usuario]
            return

        # Verifica novamente se houve empate após a jogada do bot
        if verificar_empate(tabuleiro):
            bot.edit_message_text(f"😐 Empate!\n\n{mostrar_tabuleiro(tabuleiro)}", call.message.chat.id, call.message.message_id)
            del globals.jogos_da_velha[id_usuario]
            return

        # Atualiza o tabuleiro com os novos botões
        markup = criar_botoes_tabuleiro(tabuleiro)
        bot.edit_message_text(f"Seu turno!\n\n{mostrar_tabuleiro(tabuleiro)}", call.message.chat.id, call.message.message_id, reply_markup=markup)

    except Exception as e:
        print(f"Erro ao processar o jogo da velha: {e}")
        traceback.print_exc()

