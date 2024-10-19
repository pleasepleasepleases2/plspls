import random
from telebot import types
import globals

# Função para inicializar o tabuleiro vazio
def inicializar_tabuleiro():
    return ['⬜' for _ in range(9)]

# Função para mostrar o tabuleiro formatado com '✔️' e '❌'
def mostrar_tabuleiro(tabuleiro):
    return f"{tabuleiro[0]} {tabuleiro[1]} {tabuleiro[2]}\n" \
           f"{tabuleiro[3]} {tabuleiro[4]} {tabuleiro[5]}\n" \
           f"{tabuleiro[6]} {tabuleiro[7]} {tabuleiro[8]}"

# Função para criar botões interativos para o tabuleiro
def criar_botoes_tabuleiro(tabuleiro):
    markup = types.InlineKeyboardMarkup()
    botoes = []
    for i in range(9):
        texto = tabuleiro[i] if tabuleiro[i] != '⬜' else str(i + 1)
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
    return all(celula != '⬜' for celula in tabuleiro)

# Função Minimax para determinar a melhor jogada para o bot
def minimax(tabuleiro, profundidade, is_bot, simbolo_bot, simbolo_jogador):
    if verificar_vitoria(tabuleiro, simbolo_bot):
        return 10 - profundidade  # Quanto mais rápido vencer, melhor
    elif verificar_vitoria(tabuleiro, simbolo_jogador):
        return profundidade - 10  # Quanto mais rápido perder, pior
    elif verificar_empate(tabuleiro):
        return 0  # Empate

    if is_bot:
        melhor_valor = -float('inf')
        for i in range(9):
            if tabuleiro[i] == '⬜':
                tabuleiro[i] = simbolo_bot
                valor = minimax(tabuleiro, profundidade + 1, False, simbolo_bot, simbolo_jogador)
                tabuleiro[i] = '⬜'
                melhor_valor = max(melhor_valor, valor)
        return melhor_valor
    else:
        melhor_valor = float('inf')
        for i in range(9):
            if tabuleiro[i] == '⬜':
                tabuleiro[i] = simbolo_jogador
                valor = minimax(tabuleiro, profundidade + 1, True, simbolo_bot, simbolo_jogador)
                tabuleiro[i] = '⬜'
                melhor_valor = min(melhor_valor, valor)
        return melhor_valor

# Função para o bot fazer uma jogada com 70% de chance de ser inteligente
def bot_fazer_jogada(tabuleiro, simbolo_bot, simbolo_jogador):
    if random.random() < 0.7:  # 70% de chance de usar Minimax
        melhor_valor = -float('inf')
        melhor_jogada = None
        for i in range(9):
            if tabuleiro[i] == '⬜':
                tabuleiro[i] = simbolo_bot
                valor = minimax(tabuleiro, 0, False, simbolo_bot, simbolo_jogador)
                tabuleiro[i] = '⬜'
                if valor > melhor_valor:
                    melhor_valor = valor
                    melhor_jogada = i
        if melhor_jogada is not None:
            tabuleiro[melhor_jogada] = simbolo_bot
            return tabuleiro
    # 30% de chance de fazer uma jogada aleatória
    while True:
        jogada_aleatoria = random.randint(0, 8)
        if tabuleiro[jogada_aleatoria] == '⬜':
            tabuleiro[jogada_aleatoria] = simbolo_bot
            return tabuleiro

# Função para iniciar o jogo da velha
def iniciar_jogo(bot, message):
    id_usuario = message.from_user.id
    tabuleiro = inicializar_tabuleiro()
    globals.jogos_da_velha[id_usuario] = tabuleiro
    
    bot.send_message(message.chat.id, f"Vamos jogar Jogo da Velha! Você é o '✔️' e eu sou o '❌'.\n\n{mostrar_tabuleiro(tabuleiro)}",
                     reply_markup=criar_botoes_tabuleiro(tabuleiro))

# Função para processar as jogadas do jogador
def jogador_fazer_jogada(bot, call):
    try:
        id_usuario = call.from_user.id
        if id_usuario not in globals.jogos_da_velha:
            bot.send_message(call.message.chat.id, "Você não iniciou um jogo da velha. Use /jogodavelha para começar.")
            return

        tabuleiro = globals.jogos_da_velha[id_usuario]
        jogada = int(call.data)

        if tabuleiro[jogada] != '⬜':
            bot.answer_callback_query(call.id, "Essa posição já está ocupada!")
            return

        # Jogada do jogador
        tabuleiro[jogada] = '✔️'

        # Verifica se o jogador venceu
        if verificar_vitoria(tabuleiro, '✔️'):
            bot.edit_message_text(f"🎉 Parabéns! Você venceu!\n\n{mostrar_tabuleiro(tabuleiro)}", call.message.chat.id, call.message.message_id)
            del globals.jogos_da_velha[id_usuario]
            return

        # Verifica se houve empate
        if verificar_empate(tabuleiro):
            bot.edit_message_text(f"😐 Empate!\n\n{mostrar_tabuleiro(tabuleiro)}", call.message.chat.id, call.message.message_id)
            del globals.jogos_da_velha[id_usuario]
            return

        # Jogada do bot
        tabuleiro = bot_fazer_jogada(tabuleiro, '❌', '✔️')

        # Verifica se o bot venceu
        if verificar_vitoria(tabuleiro, '❌'):
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

