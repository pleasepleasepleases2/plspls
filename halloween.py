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
