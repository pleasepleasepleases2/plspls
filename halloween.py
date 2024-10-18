import time
import globals
from bd import *
from tag import *
from pescar import send_card_message,subcategoria_handler,verificar_subcategoria_evento
# jogo da velha
# Inicializar o tabuleiro do jogo da velha
def inicializar_tabuleiro():
    return [['⬜', '⬜', '⬜'], ['⬜', '⬜', '⬜'], ['⬜', '⬜', '⬜']]

# Função para mostrar o tabuleiro
def mostrar_tabuleiro(tabuleiro):
    return '\n'.join([' '.join(linha) for linha in tabuleiro])

# Função para verificar se alguém ganhou
def verificar_vitoria(tabuleiro, jogador):
    # Verificar linhas, colunas e diagonais
    for linha in tabuleiro:
        if all(celula == jogador for celula in linha):
            return True
    for coluna in range(3):
        if all(tabuleiro[linha][coluna] == jogador for linha in range(3)):
            return True
    if tabuleiro[0][0] == tabuleiro[1][1] == tabuleiro[2][2] == jogador:
        return True
    if tabuleiro[0][2] == tabuleiro[1][1] == tabuleiro[2][0] == jogador:
        return True
    return False

# Função para verificar se há empate
def verificar_empate(tabuleiro):
    return all(celula != '⬜' for linha in tabuleiro for celula in linha)

# Função Minimax para determinar a melhor jogada para o bot
def minimax(tabuleiro, profundidade, is_bot, simbolo_bot, simbolo_jogador):
    if verificar_vitoria(tabuleiro, simbolo_bot):
        return 10 - profundidade  # Quanto mais rápido vencer, melhor o resultado
    elif verificar_vitoria(tabuleiro, simbolo_jogador):
        return profundidade - 10  # Quanto mais rápido perder, pior o resultado
    elif verificar_empate(tabuleiro):
        return 0  # Empate

    if is_bot:
        melhor_valor = -float('inf')
        for i in range(3):
            for j in range(3):
                if tabuleiro[i][j] == '⬜':
                    tabuleiro[i][j] = simbolo_bot
                    valor = minimax(tabuleiro, profundidade + 1, False, simbolo_bot, simbolo_jogador)
                    tabuleiro[i][j] = '⬜'
                    melhor_valor = max(melhor_valor, valor)
        return melhor_valor
    else:
        melhor_valor = float('inf')
        for i in range(3):
            for j in range(3):
                if tabuleiro[i][j] == '⬜':
                    tabuleiro[i][j] = simbolo_jogador
                    valor = minimax(tabuleiro, profundidade + 1, True, simbolo_bot, simbolo_jogador)
                    tabuleiro[i][j] = '⬜'
                    melhor_valor = min(melhor_valor, valor)
        return melhor_valor

# Função para o bot fazer uma jogada usando Minimax com 60% de chance
def bot_fazer_jogada(tabuleiro, simbolo_bot, simbolo_jogador):
    if random.random() < 0.6:  # 60% de chance de usar Minimax
        melhor_valor = -float('inf')
        melhor_jogada = None
        for i in range(3):
            for j in range(3):
                if tabuleiro[i][j] == '⬜':
                    tabuleiro[i][j] = simbolo_bot
                    valor = minimax(tabuleiro, 0, False, simbolo_bot, simbolo_jogador)
                    tabuleiro[i][j] = '⬜'
                    if valor > melhor_valor:
                        melhor_valor = valor
                        melhor_jogada = (i, j)
        if melhor_jogada:
            tabuleiro[melhor_jogada[0]][melhor_jogada[1]] = simbolo_bot
            return tabuleiro
    # 40% de chance de fazer uma jogada aleatória
    while True:
        i, j = random.randint(0, 2), random.randint(0, 2)
        if tabuleiro[i][j] == '⬜':
            tabuleiro[i][j] = simbolo_bot
            return tabuleiro

# Função para criar os botões do tabuleiro
def criar_botoes_tabuleiro(tabuleiro):
    markup = types.InlineKeyboardMarkup(row_width=3)
    botoes = []
    for i in range(3):
        for j in range(3):
            if tabuleiro[i][j] == '⬜':
                botao = types.InlineKeyboardButton(f"{i*3+j+1}", callback_data=f"jogada_{i}_{j}")
            else:
                botao = types.InlineKeyboardButton(tabuleiro[i][j], callback_data=f"jogada_disabled")
            botoes.append(botao)
    markup.add(*botoes)
    return markup
#labirinto
# Função para garantir que o jogador tenha sempre um caminho livre até a saída
def gerar_labirinto_com_caminho_e_validacao(tamanho=10):
    labirinto = [['🪨' for _ in range(tamanho)] for _ in range(tamanho)]
    
    # Definir o ponto inicial e final
    x, y = 1, 1  # Ponto inicial
    saida_x, saida_y = tamanho - 2, random.randint(1, tamanho - 2)  # Saída em posição aleatória na borda inferior
    
    # Definir um caminho garantido até a saída usando backtracking
    caminho = [(x, y)]
    labirinto[x][y] = '⬜'
    
    while (x, y) != (saida_x, saida_y):
        direcoes = []
        if x > 1 and labirinto[x-1][y] == '🪨':  # Norte
            direcoes.append((-1, 0))
        if x < tamanho - 2 and labirinto[x+1][y] == '🪨':  # Sul
            direcoes.append((1, 0))
        if y > 1 and labirinto[x][y-1] == '🪨':  # Oeste
            direcoes.append((0, -1))
        if y < tamanho - 2 and labirinto[x][y+1] == '🪨':  # Leste
            direcoes.append((0, 1))

        if not direcoes:
            # Retroceder se não houver direções disponíveis
            x, y = caminho.pop()
        else:
            dx, dy = random.choice(direcoes)
            x += dx
            y += dy
            labirinto[x][y] = '⬜'
            caminho.append((x, y))

    # Colocar a saída
    labirinto[saida_x][saida_y] = '🚪'
    
    # Adicionar monstros e recompensas fora do caminho garantido
    for _ in range(5):
        while True:
            mx, my = random.randint(1, tamanho-2), random.randint(1, tamanho-2)
            if labirinto[mx][my] == '🪨' and (mx, my) not in caminho:  # Não bloquear o caminho principal
                labirinto[mx][my] = '👻'
                break
    
    for _ in range(3):
        while True:
            rx, ry = random.randint(1, tamanho-2), random.randint(1, tamanho-2)
            if labirinto[rx][ry] == '🪨' and (rx, ry) not in caminho:  # Não bloquear o caminho principal
                labirinto[rx][ry] = '🎃'
                break

    return labirinto

# Função para revelar todo o labirinto ao final do jogo
def revelar_labirinto(labirinto):
    return '\n'.join([''.join(linha) for linha in labirinto])

# Função para mostrar o labirinto com visibilidade limitada
def mostrar_labirinto(labirinto, posicao):
    mapa = ""
    x, y = posicao
    for i in range(len(labirinto)):
        for j in range(len(labirinto[i])):
            # Mostrar a posição atual do jogador
            if (i, j) == posicao:
                mapa += "🔦"
            # Revelar as células ao redor do jogador (cima, baixo, esquerda, direita)
            elif abs(x - i) <= 1 and abs(y - j) <= 1:
                mapa += labirinto[i][j]
            else:
                mapa += "⬛"  # Células ainda não reveladas
        mapa += "\n"
    return mapa
# Função para calcular a nova posição com base na direção, sem permitir passar por pedras
def mover_posicao(posicao_atual, direcao, tamanho_labirinto, labirinto):
    x, y = posicao_atual
    if direcao == 'norte' and x > 0 and labirinto[x-1][y] != '🪨':
        return (x - 1, y)
    elif direcao == 'sul' and x < tamanho_labirinto - 1 and labirinto[x+1][y] != '🪨':
        return (x + 1, y)
    elif direcao == 'leste' and y < tamanho_labirinto - 1 and labirinto[x][y+1] != '🪨':
        return (x, y + 1)
    elif direcao == 'oeste' and y > 0 and labirinto[x][y-1] != '🪨':
        return (x, y - 1)
    return posicao_atual  # Se a direção for inválida ou for uma pedra, retorna a posição atual
#tinder



def registrar_interacao(id_usuario, id_carta, gostou):
    """Registra a interação no banco de dados, garantindo que o usuário não interaja mais de uma vez na mesma carta."""
    conn, cursor = conectar_banco_dados()

    # Verificar se o usuário já interagiu com a carta
    cursor.execute("SELECT * FROM interacoes_cartas WHERE id_usuario = %s AND id_carta = %s", (id_usuario, id_carta))
    interacao_existente = cursor.fetchone()

    if interacao_existente:
        fechar_conexao(cursor, conn)
        return False  # Usuário já interagiu com essa carta

    # Inserir a interação
    interacao = 'gostou' if gostou else 'rejeitou'
    cursor.execute("INSERT INTO interacoes_cartas (id_usuario, id_carta, interacao) VALUES (%s, %s, %s)",
                   (id_usuario, id_carta, interacao))

    # Atualizar contador de interações
    cursor.execute("UPDATE usuarios SET interacoes_cartas = interacoes_cartas + 1 WHERE id_usuario = %s", (id_usuario,))

    # Verificar se o usuário já respondeu 10 cartas
    cursor.execute("SELECT interacoes_cartas FROM usuarios WHERE id_usuario = %s", (id_usuario,))
    interacoes = cursor.fetchone()[0]

    if interacoes >= 10:
        # Dar 5 cenouras e resetar o contador
        cursor.execute("UPDATE usuarios SET cenouras = cenouras + 5, interacoes_cartas = 0 WHERE id_usuario = %s", (id_usuario,))
        bot.send_message(id_usuario, "🎉 Parabéns! Você ganhou 5 cenouras por responder 10 cartas!")

    # Atualizar popularidade da carta
    cursor.execute("SELECT gostos, rejeicoes FROM popularidade_cartas WHERE id_carta = %s", (id_carta,))
    resultado = cursor.fetchone()

    if resultado:
        gostos, rejeicoes = resultado
        if gostou:
            gostos += 1
        else:
            rejeicoes += 1
        cursor.execute("UPDATE popularidade_cartas SET gostos = %s, rejeicoes = %s WHERE id_carta = %s",
                       (gostos, rejeicoes, id_carta))
    else:
        if gostou:
            cursor.execute("INSERT INTO popularidade_cartas (id_carta, gostos, rejeicoes) VALUES (%s, %s, %s)",
                           (id_carta, 1, 0))
        else:
            cursor.execute("INSERT INTO popularidade_cartas (id_carta, gostos, rejeicoes) VALUES (%s, %s, %s)",
                           (id_carta, 0, 1))

    conn.commit()
    fechar_conexao(cursor, conn)
    return True  # Interação registrada com sucesso

import traceback
import globals
from telebot import types

# Inicializa o tabuleiro vazio
def inicializar_tabuleiro():
    return [' ' for _ in range(9)]

# Mostra o tabuleiro formatado
def mostrar_tabuleiro(tabuleiro):
    return f"{tabuleiro[0]} | {tabuleiro[1]} | {tabuleiro[2]}\n" \
           f"--+---+--\n" \
           f"{tabuleiro[3]} | {tabuleiro[4]} | {tabuleiro[5]}\n" \
           f"--+---+--\n" \
           f"{tabuleiro[6]} | {tabuleiro[7]} | {tabuleiro[8]}"

# Cria os botões de interação para o jogo
def criar_botoes_tabuleiro(tabuleiro):
    markup = types.InlineKeyboardMarkup()
    botoes = []
    for i in range(9):
        botoes.append(types.InlineKeyboardButton(text=tabuleiro[i], callback_data=str(i)))
        if (i + 1) % 3 == 0:
            markup.row(*botoes)
            botoes = []
    return markup

# Função principal para iniciar o jogo da velha
def iniciar_jogo(bot, message):
    try:
        id_usuario = message.from_user.id
        tabuleiro = inicializar_tabuleiro()
        globals.jogos_da_velha[id_usuario] = tabuleiro
        
        bot.send_message(message.chat.id, f"Vamos jogar Jogo da Velha! Você é o '✔️' e eu sou o '❌'.\n\n{mostrar_tabuleiro(tabuleiro)}")
        
        markup = criar_botoes_tabuleiro(tabuleiro)
        bot.send_message(message.chat.id, "Escolha sua jogada (1-9):", reply_markup=markup)
    except Exception as e:
        print(f"Erro ao processar o jogo da velha: {e}")
        traceback.print_exc()

def gerar_proxima_carta():
    """Seleciona uma carta aleatória do banco de dados."""
    conn, cursor = conectar_banco_dados()
    cursor.execute("SELECT id_personagem, nome, subcategoria, emoji, categoria FROM personagens ORDER BY RAND() LIMIT 1")
    carta = cursor.fetchone()
    fechar_conexao(cursor, conn)
    return carta

def consultar_popularidade():
    """Consulta as cartas mais amadas e mais rejeitadas."""
    conn, cursor = conectar_banco_dados()
    
    cursor.execute("SELECT id_carta, gostos, rejeicoes FROM popularidade_cartas ORDER BY gostos DESC LIMIT 10")
    mais_amadas = cursor.fetchall()
    
    cursor.execute("SELECT id_carta, gostos, rejeicoes FROM popularidade_cartas ORDER BY rejeicoes DESC LIMIT 10")
    mais_rejeitadas = cursor.fetchall()
    
    fechar_conexao(cursor, conn)
    return mais_amadas, mais_rejeitadas

import traceback
from telebot import types
import globals

# Função para manipular as jogadas do jogador
@bot.callback_query_handler(func=lambda call: call.data.startswith('jogada_'))
def jogador_fazer_jogada(call):
    try:
        id_usuario = call.from_user.id
        # Verifica se o jogo foi iniciado
        if id_usuario not in globals.jogos_da_velha:
            bot.send_message(call.message.chat.id, "Você não iniciou um jogo da velha. Use /jogodavelha para começar.")
            return

        # Verifica se a jogada é inválida
        if call.data == "jogada_disabled":
            bot.answer_callback_query(call.id, "Essa posição já está ocupada!")
            return

        # Processa a jogada
        tabuleiro = globals.jogos_da_velha[id_usuario]
        _, i, j = call.data.split('_')
        i, j = int(i), int(j)

        if tabuleiro[i][j] != '⬜':
            bot.answer_callback_query(call.id, "Essa posição já está ocupada!")
            return

        # Atualiza o tabuleiro com a jogada do jogador
        tabuleiro[i][j] = '✔️'

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
# Função para escolher uma palavra aleatória com base no tamanho
def escolher_palavra():
    todas_palavras = palavras_4_letras + palavras_5_letras + palavras_6_letras + palavras_7_letras + palavras_8_letras
    return random.choice(todas_palavras)

# Função para fornecer o feedback ao jogador usando emojis coloridos
def verificar_palpite(palavra_secreta, palpite):
    resultado = ''
    palavra_secreta_lista = list(palavra_secreta)
    palpite_lista = list(palpite)
    marcados = [False] * len(palavra_secreta)

    # Primeiro, marcar as letras corretas na posição correta
    for i in range(len(palavra_secreta)):
        if palpite_lista[i] == palavra_secreta_lista[i]:
            resultado += '🟩'  # Letra correta na posição correta
            marcados[i] = True
            palpite_lista[i] = None  # Remover a letra do palpite para não ser considerada novamente
        else:
            resultado += ' '  # Espaço reservado para ajustar depois

    # Segundo, marcar as letras corretas na posição errada
    for i in range(len(palavra_secreta)):
        if resultado[i] == ' ':
            if palpite_lista[i] and palpite_lista[i] in palavra_secreta_lista:
                idx = palavra_secreta_lista.index(palpite_lista[i])
                if not marcados[idx]:
                    resultado = resultado[:i] + '🟨' + resultado[i+1:]  # Letra correta na posição errada
                    marcados[idx] = True
                    palpite_lista[i] = None  # Remover a letra do palpite
                else:
                    resultado = resultado[:i] + '⬛' + resultado[i+1:]  # Letra incorreta
            else:
                resultado = resultado[:i] + '⬛' + resultado[i+1:]  # Letra incorreta
    return resultado

def iniciar_labirinto(message):
    try:
        id_usuario = message.from_user.id
        tamanho = 10  # Tamanho do labirinto (10x10 para mais complexidade)
        
        labirinto = gerar_labirinto_com_caminho_e_validacao(tamanho)
        posicao_inicial = (1, 1)  # O jogador começa em uma posição inicial fixa ou aleatória
        movimentos_restantes = 35  # Limite de movimentos para encontrar a saída
        
        globals.jogadores_labirinto[id_usuario] = {
            "labirinto": labirinto,
            "posicao": posicao_inicial,
            "movimentos": movimentos_restantes
        }
        
        mapa = mostrar_labirinto(labirinto, posicao_inicial)
        
        # Criar os botões de navegação
        markup = types.InlineKeyboardMarkup(row_width=4)
        botao_cima = types.InlineKeyboardButton("⬆️", callback_data="norte")
        botao_esquerda = types.InlineKeyboardButton("⬅️", callback_data="oeste")
        botao_direita = types.InlineKeyboardButton("➡️", callback_data="leste")
        botao_baixo = types.InlineKeyboardButton("⬇️", callback_data="sul")
        markup.add(botao_cima, botao_esquerda, botao_direita, botao_baixo)
        
        bot.send_message(message.chat.id, f"🏰 Bem-vindo ao Labirinto! Você tem {movimentos_restantes} movimentos para escapar.\n\n{mapa}", reply_markup=markup)
    except Exception as e:
        print(f"Erro ao processar o jogo da velha): {e}")
        traceback.print_exc()

def mover_labirinto(call):
    try:
        id_usuario = call.from_user.id
        if id_usuario not in jogadores_labirinto:
            bot.send_message(call.message.chat.id, "👻 Você precisa iniciar o labirinto primeiro com o comando /labirinto.")
            return
        
        direcao = call.data  # Pega a direção do botão clicado
        jogador = globals.jogadores_labirinto[id_usuario]
        labirinto = jogador["labirinto"]
        posicao_atual = jogador["posicao"]
        movimentos_restantes = jogador["movimentos"]
        
        nova_posicao = mover_posicao(posicao_atual, direcao, len(labirinto), labirinto)
        
        if nova_posicao != posicao_atual:  # Se a nova posição for válida
            jogadores_labirinto[id_usuario]["posicao"] = nova_posicao
            jogadores_labirinto[id_usuario]["movimentos"] -= 1
            movimentos_restantes -= 1
            conteudo = labirinto[nova_posicao[0]][nova_posicao[1]]
            
            # Verificar se o jogador chegou na saída
            if conteudo == '🚪':
                bot.edit_message_text(f"🏆 Parabéns! Você encontrou a saída e escapou do labirinto!\n\n{revelar_labirinto(labirinto)}",
                                      call.message.chat.id, call.message.message_id)
                del jogadores_labirinto[id_usuario]  # Remover o jogador do labirinto
            elif movimentos_restantes == 0:
                bot.edit_message_text(f"😢 Seus movimentos acabaram! Você não conseguiu escapar da maldição...\n\n{revelar_labirinto(labirinto)}",
                                      call.message.chat.id, call.message.message_id)
                del jogadores_labirinto[id_usuario]  # Fim do jogo, remover jogador
            else:
                mapa = mostrar_labirinto(labirinto, nova_posicao)
                # Revelar o conteúdo do bloco ao chegar nele
                if conteudo == '👻' or conteudo == '🎃':
                    # Remover o monstro ou abóbora do labirinto
                    labirinto[nova_posicao[0]][nova_posicao[1]] = '⬜'
                    
                    markup_opcoes = types.InlineKeyboardMarkup(row_width=2)
                    botao_encerrar = types.InlineKeyboardButton("Encerrar", callback_data="encerrar")
                    botao_continuar = types.InlineKeyboardButton("Continuar", callback_data="continuar")
                    markup_opcoes.add(botao_encerrar, botao_continuar)
                    
                    if conteudo == '👻':
                        bot.edit_message_text(f"👻 Você encontrou um monstro e perdeu 20 cenouras! Você quer encerrar ou continuar?\n\n{mapa}",
                                              call.message.chat.id, call.message.message_id, reply_markup=markup_opcoes)
                        conn, cursor = conectar_banco_dados()
                        cursor.execute("UPDATE usuarios SET cenouras = cenouras - 20 WHERE id_usuario = %s", (id_usuario,))
                        conn.commit()
                    elif conteudo == '🎃':
                        bot.edit_message_text(f"🎃 Você encontrou uma recompensa de 50 cenouras! Você quer encerrar ou continuar?\n\n{mapa}",
                                              call.message.chat.id, call.message.message_id, reply_markup=markup_opcoes)
                        conn, cursor = conectar_banco_dados()
                        cursor.execute("UPDATE usuarios SET cenouras = cenouras + 50 WHERE id_usuario = %s", (id_usuario,))
                        conn.commit()
                else:
                    # Atualizar os botões de navegação
                    markup = types.InlineKeyboardMarkup(row_width=4)
                    botao_cima = types.InlineKeyboardButton("⬆️", callback_data="norte")
                    botao_esquerda = types.InlineKeyboardButton("⬅️", callback_data="oeste")
                    botao_direita = types.InlineKeyboardButton("➡️", callback_data="leste")
                    botao_baixo = types.InlineKeyboardButton("⬇️", callback_data="sul")
                    markup.add(botao_cima, botao_esquerda, botao_direita, botao_baixo)
    
                    bot.edit_message_text(f"🌕 Você avançou pelo labirinto. Movimentos restantes: {movimentos_restantes}\n\n{mapa}",
                                          call.message.chat.id, call.message.message_id, reply_markup=markup)
        else:
            bot.answer_callback_query(call.id, "👻 Você não pode ir nessa direção!")
    except Exception as e:
        print(f"Erro ao processar o jogo da velha): {e}")
        traceback.print_exc()
@bot.callback_query_handler(func=lambda call: call.data in ['encerrar', 'continuar'])
def encerrar_ou_continuar(call):
    try:
        id_usuario = call.from_user.id
        if call.data == 'encerrar':
            bot.edit_message_text("💀 Você decidiu encerrar sua jornada no labirinto. Fim de jogo!", call.message.chat.id, call.message.message_id)
            del jogadores_labirinto[id_usuario]  # Remover jogador
        elif call.data == 'continuar':
            jogador = jogadores_labirinto[id_usuario]
            labirinto = jogador["labirinto"]
            posicao = jogador["posicao"]
            movimentos_restantes = jogador["movimentos"]
    
            # Atualizar a mensagem com o labirinto e botões de navegação
            mapa = mostrar_labirinto(labirinto, posicao)
            markup = types.InlineKeyboardMarkup(row_width=4)
            botao_cima = types.InlineKeyboardButton("⬆️", callback_data="norte")
            botao_esquerda = types.InlineKeyboardButton("⬅️", callback_data="oeste")
            botao_direita = types.InlineKeyboardButton("➡️", callback_data="leste")
            botao_baixo = types.InlineKeyboardButton("⬇️", callback_data="sul")
            markup.add(botao_cima, botao_esquerda, botao_direita, botao_baixo)
    
            bot.edit_message_text(f"🏃 Você decidiu continuar sua jornada! Movimentos restantes: {movimentos_restantes}\n\n{mapa}",
                                  call.message.chat.id, call.message.message_id, reply_markup=markup)

    except Exception as e:
        print(f"Erro ao processar o jogo da velha): {e}")
        traceback.print_exc()
