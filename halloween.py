import time
import globals
from bd import *
from tag import *
from pescar import send_card_message,subcategoria_handler,verificar_subcategoria_evento
# jogo da velha
import random
from datetime import datetime, timedelta
import traceback
from telebot import types
import globals
from collections import defaultdict
import random
from datetime import timedelta, datetime
url_imagem = "https://pub-6f23ef52e8614212a14d24b0cf55ae4a.r2.dev/BQACAgEAAxkBAAIcfGcVeT6gaLXd0DKA7aihUQJfV62hAAJMBQACSV6xRD2puYHoSyajNgQ.jpg"

aboboras = {
    1: {"nome": "Abóbora Assustadora", "premio": "50 cenouras", "descricao": "🎃👻 Você encontrou uma abóbora assombrada escondida no quintal!"},
    2: {"nome": "Abóbora Macabra", "premio": "100 cenouras", "descricao": "🎃🕸️ Um vizinho misterioso deixou uma abóbora macabra na sua porta."},
    3: {"nome": "Abóbora da Morte", "premio": "Carta Faltante", "descricao": "🎃💀 No silêncio da noite, uma abóbora da morte apareceu em seu caminho."},
    4: {"nome": "Abóbora Doce", "premio": "50% de chance de encontrar cartas de uma subcategoria favorita nas próximas 10 pescas", "descricao": "🍬🎃 Você tropeçou em uma abóbora doce, e ela exala um aroma encantador."},
    5: {"nome": "Abóbora Encantada", "premio": "Pesca extra ao encontrar uma carta de evento", "descricao": "🎃✨ Uma abóbora encantada surge do nada e flutua em sua direção!"},
    6: {"nome": "Abóbora Brilhante", "premio": "Escolha entre 10 opções de séries em cada giro", "descricao": "🌕🎃 No brilho da lua, você vê uma abóbora brilhante esperando por você."},
    7: {"nome": "Abóbora Dourada", "premio": "20 cartas de uma série comum à sua escolha após 50 pescas", "descricao": "💰🎃 Uma abóbora dourada reluzente surge na beira da estrada escura."},
    8: {"nome": "Abóbora Misteriosa", "premio": "Pesca de evento a cada 10 giros", "descricao": "🎩🎃 Você encontrou uma abóbora misteriosa em um baú antigo."},
    9: {"nome": "Abóbora Favorita", "premio": "Aumenta a chance de encontrar um personagem favorito em 35% por um dia", "descricao": "🎃❤️ Uma abóbora favorita foi deixada com uma carta ao seu nome."},
    10: {"nome": "Abóbora Espectral", "premio": "Aumenta a chance de duplicar cartas ao pescar", "descricao": "🌫️👻 Uma abóbora espectral surge entre as sombras, reluzente e tentadora."},
    11: {"nome": "Abóbora da Sorte", "premio": "Chance de multiplicar recompensas em pescas de cartas de evento", "descricao": "🍀🎃 Você encontrou uma abóbora da sorte escondida entre as folhas secas."},
    12: {"nome": "Abóbora Gélida", "premio": "Desconto em compras de cartas durante 24 horas", "descricao": "❄️🎃 Do frio da madrugada, uma abóbora gélida aparece com um leve brilho."},
    13: {"nome": "Abóbora Enfeitiçada", "premio": "Aumenta as chances de cartas duplicadas por 24 horas", "descricao": "✨🎃 Uma abóbora enfeitiçada dança ao seu redor, cercada por luzes mágicas."},
    14: {"nome": "Abóbora Estelar", "premio": "Ganha uma carta estrela após 30 giros", "descricao": "🌌🎃 Você se depara com uma abóbora estelar, caída de uma constelação distante."},
    15: {"nome": "Abóbora Espinhenta", "premio": "Próxima pesca gratuita de evento após 10 cartas comuns", "descricao": "🌵🎃 Entre espinhos e folhas, você encontrou uma abóbora espinhenta."},
    16: {"nome": "Abóbora Serenidade Sombria", "premio": "Reduz a chance de cartas repetidas por 24 horas", "descricao": "🌙🎃 Uma abóbora de serenidade repousa tranquilamente em seu jardim."},
    17: {"nome": "Abóbora Rara", "premio": "Cria pescas especiais com personagens das séries favoritas", "descricao": "🌟🎃 De uma caixa antiga, você retira uma rara e preciosa abóbora."},
    18: {"nome": "Abóbora Fumegante", "premio": "Cada carta tem chance de liberar uma semente por 24 horas", "descricao": "🔥🎃 Uma abóbora fumegante aparece, soltando vapores enigmáticos."},
    19: {"nome": "Abóbora Lunar", "premio": "Aumenta a chance de cartas de evento durante a noite", "descricao": "🌕🎃 No luar, você encontra uma abóbora lunar, brilhando intensamente."},
    20: {"nome": "Abóbora Realçada", "premio": "50% de chance de cartas favoritas em 'Estou com sorte' por 12 horas", "descricao": "💫🎃 Uma abóbora realçada surge, envolta em um leve brilho encantador."},
    21: {"nome": "Abóbora Carismática", "premio": "Selecione um personagem que aparece a cada 50 giros", "descricao": "🎭🎃 Em uma noite calma, uma abóbora carismática é deixada em sua porta."},
    22: {"nome": "Abóbora Fantástica", "premio": "Permite alterar a foto de qualquer personagem após 15 pescas", "descricao": "✨🎃 De repente, uma abóbora fantástica aparece, cheia de surpresas."},
    23: {"nome": "Abóbora Sortuda", "premio": "Chance de ganhar um item raro a cada 20 giros", "descricao": "🍀🎃 Escondida entre as árvores, uma abóbora sortuda chama sua atenção."},
    24: {"nome": "Abóbora Colorida", "premio": "Ganha uma borda colorida em uma carta aleatória a cada 10 giros", "descricao": "🌈🎃 Você vê uma abóbora colorida entre as folhas secas do jardim."},
    25: {"nome": "Abóbora Cristalina", "premio": "Cartas têm chance de serem transformadas em cartas de Halloween", "descricao": "💎🎃 Uma abóbora cristalina surge, cintilando como uma joia rara."},
    26: {"nome": "Abóbora Especial", "premio": "Aumenta em 10% a chance de encontrar cartas raras durante eventos", "descricao": "✨🎃 Entre os arbustos, você encontra uma abóbora especial e reluzente."},
    27: {"nome": "Abóbora Mágica", "premio": "Garante uma carta de alta raridade a cada 10 giros por um dia", "descricao": "🔮🎃 Uma abóbora mágica flutua até você, com um brilho suave."},
    28: {"nome": "Abóbora Assombrosa", "premio": "Cartas de Halloween aparecem com mais frequência por 24 horas", "descricao": "👻🎃 No escuro, uma abóbora assombrosa surge inesperadamente."},
    29: {"nome": "Abóbora Sombria", "premio": "Encontre até 2 cartas de Halloween por pesca durante eventos", "descricao": "🌫️🎃 Do nevoeiro, uma abóbora sombria aparece silenciosamente."},
    30: {"nome": "Abóbora Eterna", "premio": "Chance permanente de 15% para cartas de evento", "descricao": "🌅🎃 No amanhecer, uma abóbora eterna repousa à sua porta."}
}


##########################################################################################################3
def troca_invertida(user_id, chat_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Definir o tempo de duração da praga aleatoriamente entre 5 e 60 minutos
        duracao_minutos = random.randint(5, 60)
        fim_travessura = datetime.now() + timedelta(minutes=duracao_minutos)

        # Inserir a praga na tabela 'travessuras' para o usuário
        cursor.execute("""
            INSERT INTO travessuras (id_usuario, tipo_travessura, fim_travessura)
            VALUES (%s, 'troca_invertida', %s)
            ON DUPLICATE KEY UPDATE fim_travessura = %s
        """, (user_id, fim_travessura, fim_travessura))

        conn.commit()
        bot.send_photo(user_id, url_imagem, caption=f"🎭 Travessura! A ordem dos comandos das suas próximas trocas foi invertida por {duracao_minutos} minutos. Tome cuidado!")

    except Exception as e:
        print(f"Erro ao aplicar praga: {e}")
    finally:
        fechar_conexao(cursor, conn)


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
import traceback
from telebot import types
import globals

# Função para escolher a palavra secreta (você deve implementar ou importar essa função)
def escolher_palavra():
    return "exemplo"

# Função para verificar o palpite do jogador (comparar com a palavra secreta)
def verificar_palpite(palavra_secreta, palpite):
    resultado = []
    for i in range(len(palavra_secreta)):
        if palpite[i] == palavra_secreta[i]:
            resultado.append(f"{palpite[i]}✔️")
        elif palpite[i] in palavra_secreta:
            resultado.append(f"{palpite[i]}~")
        else:
            resultado.append(f"{palpite[i]}❌")
    return ' '.join(resultado)

# Função que inicia o jogo do termo
def iniciar_termo(message):
    id_usuario = message.from_user.id
    palavra_secreta = escolher_palavra()

    # Armazenar o jogo do usuário
    globals.jogos_termo[id_usuario] = {
        "palavra_secreta": palavra_secreta,
        "tentativas_restantes": 6,
        "tamanho_palavra": len(palavra_secreta)
    }

    bot.send_message(message.chat.id, f"🎮 Bem-vindo ao Termo!\nA palavra tem {len(palavra_secreta)} letras.\nVocê tem 6 tentativas.\n\nEnvie sua primeira tentativa:")

# Lidar com as tentativas do jogador
@bot.message_handler(func=lambda message: message.from_user.id in globals.jogos_termo)
def tentar_termo(message):
    id_usuario = message.from_user.id
    jogo = globals.jogos_termo[id_usuario]
    palavra_secreta = jogo['palavra_secreta']
    tentativas_restantes = jogo['tentativas_restantes']

    palpite = message.text.lower().strip()

    # Verificar se o palpite tem o mesmo número de letras
    if len(palpite) != len(palavra_secreta):
        bot.send_message(message.chat.id, f"O palpite deve ter {len(palavra_secreta)} letras!")
        return

    # Verificar se o jogador acertou a palavra
    if palpite == palavra_secreta:
        bot.send_message(message.chat.id, f"🎉 Parabéns! Você acertou a palavra '{palavra_secreta}'!")
        del globals.jogos_termo[id_usuario]  # Remover o jogo após vencer
        return

    # Fornecer feedback ao jogador
    resultado = verificar_palpite(palavra_secreta, palpite)
    tentativas_restantes -= 1
    globals.jogos_termo[id_usuario]['tentativas_restantes'] = tentativas_restantes

    # Histórico de tentativas
    if 'historico' not in globals.jogos_termo[id_usuario]:
        globals.jogos_termo[id_usuario]['historico'] = []
    globals.jogos_termo[id_usuario]['historico'].append(f"{resultado} - {palpite}")

    historico_texto = '\n'.join(globals.jogos_termo[id_usuario]['historico'])

    # Verificar se o jogador ainda tem tentativas
    if tentativas_restantes > 0:
        bot.send_message(message.chat.id, f"{historico_texto}\n\nTentativas restantes: {tentativas_restantes}")
    else:
        bot.send_message(message.chat.id, f"{historico_texto}\n\n💀 Suas tentativas acabaram! A palavra era '{palavra_secreta}'.")
        del globals.jogos_termo[id_usuario]  # Remover o jogo após terminar as tentativas

def registrar_voto(id_usuario_avaliado, id_usuario_avaliador, voto):
    try:
        conn, cursor = conectar_banco_dados()

        # Verificar se já existe um voto do avaliador
        cursor.execute("SELECT voto FROM votos WHERE id_usuario_avaliado = %s AND id_usuario_avaliador = %s", 
                       (id_usuario_avaliado, id_usuario_avaliador))
        voto_existente = cursor.fetchone()

        if voto_existente:
            # Atualizar o voto existente
            cursor.execute("UPDATE votos SET voto = %s WHERE id_usuario_avaliado = %s AND id_usuario_avaliador = %s", 
                           (voto, id_usuario_avaliado, id_usuario_avaliador))
        else:
            # Inserir um novo voto
            cursor.execute("INSERT INTO votos (id_usuario_avaliado, id_usuario_avaliador, voto) VALUES (%s, %s, %s)", 
                           (id_usuario_avaliado, id_usuario_avaliador, voto))

        conn.commit()

    except Exception as e:
        print(f"Erro ao registrar voto: {e}")
    finally:
        fechar_conexao(cursor, conn)

def contar_votos(id_usuario_avaliado):
    try:
        conn, cursor = conectar_banco_dados()

        # Contar os votos doces
        cursor.execute("SELECT COUNT(*) FROM votos WHERE id_usuario_avaliado = %s AND voto = 1", (id_usuario_avaliado,))
        doces = cursor.fetchone()[0]

        # Contar os votos fantasmas
        cursor.execute("SELECT COUNT(*) FROM votos WHERE id_usuario_avaliado = %s AND voto = 0", (id_usuario_avaliado,))
        fantasmas = cursor.fetchone()[0]

        return doces, fantasmas

    except Exception as e:
        print(f"Erro ao contar votos: {e}")
        return 0, 0
    finally:
        fechar_conexao(cursor, conn)

#################################################################################################################################
def realizar_halloween_gostosura(user_id):
    chance = random.randint(1, 100)

    if chance <= 50:
        # Cenouras como gostosura
        cenouras_ganhas = random.randint(50, 100)
        aumentar_cenouras(user_id, cenouras_ganhas)
        emoji = random.choice(["🍬", "🍪", "🍭", "🍩", "🧁", "🧇", "🍫", "🎂", "🍡", "🍨", "🍰", "🍯", "🥞", "🍦", "🍮", "🍧"])
        bot.send_message(user_id, f"{emoji} Você encontrou um saco de doces! Parabéns, recebeu {cenouras_ganhas} cenouras!")
    else:
        # Adicionar carta faltante do evento como gostosura
        adicionar_carta_faltante_evento(user_id)

def adicionar_vip_temporario(user_id, grupo_sugestao):
    try:
        conn, cursor = conectar_banco_dados()

        # Verificar se o usuário já é VIP
        cursor.execute("SELECT COUNT(*) FROM vips WHERE id_usuario = %s", (user_id,))
        ja_vip = cursor.fetchone()[0] > 0

        if ja_vip:
            # Se já for VIP, realiza outra gostosura
            realizar_halloween_gostosura(user_id)
        else:
            # Se não for VIP, dar VIP por um período aleatório de 1 a 7 dias
            dias_vip = random.randint(1, 7)
            data_fim_vip = datetime.now() + timedelta(days=dias_vip)

            # Inserir na tabela de VIPs
            cursor.execute("""
                INSERT INTO vips (id_usuario, nome, data_pagamento, renovou, pedidos_restantes, mes_atual, Dia_renovar)
                VALUES (%s, (SELECT nome FROM usuarios WHERE id_usuario = %s), NOW(), 1, 4, MONTH(NOW()), DAY(NOW() + INTERVAL %s DAY))
            """, (user_id, user_id, dias_vip))
            conn.commit()

            # Enviar mensagem para o grupo de sugestões
            bot.send_message(grupo_sugestao, f"🎉 O usuário {user_id} ganhou VIP por {dias_vip} dias!")

            # Informar o usuário que ganhou VIP
            bot.send_message(user_id, f"🎁 Parabéns! Você ganhou VIP por {dias_vip} dias. Aproveite!")

    except Exception as e:
        print(f"Erro ao adicionar VIP temporário: {e}")
    finally:
        fechar_conexao(cursor, conn)

def adicionar_protecao_temporaria(user_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Definir o período de proteção entre 3 e 12 horas
        horas_protecao = random.randint(3, 12)
        fim_protecao = datetime.now() + timedelta(hours=horas_protecao)

        # Atualizar ou inserir a proteção na tabela de usuários
        cursor.execute("""
            INSERT INTO protecoes (id_usuario, fim_protecao)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE fim_protecao = %s
        """, (user_id, fim_protecao, fim_protecao))
        conn.commit()

        # Informar o usuário sobre a proteção
        bot.send_message(user_id, f"🛡️ Você ganhou uma proteção mágica por {horas_protecao} horas! Durante esse tempo, você está imune a travessuras.")
    
    except Exception as e:
        print(f"Erro ao adicionar proteção temporária: {e}")
    finally:
        fechar_conexao(cursor, conn)

def realizar_combo_gostosura(user_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Parte 1: Ganhar até 100 cenouras
        cenouras_ganhas = random.randint(50, 100)
        aumentar_cenouras(user_id, cenouras_ganhas)
        bot.send_message(user_id, f"🍬 Parabéns, você recebeu {cenouras_ganhas} cenouras no Combo!")

        # Parte 2: Receber de 1 a 3 cartas faltantes do evento Halloween
        num_cartas = random.randint(1, 3)
        for _ in range(num_cartas):
            adicionar_carta_faltante_halloween(user_id)
        bot.send_message(user_id, f"🎃 Você também ganhou {num_cartas} carta(s) faltante(s) do evento Halloween!")

        # Parte 3: Escolher um efeito bônus
        efeitos_bonus = [
            "dobro de cenouras ao cenourar",
            "peixes em dobro na pesca",
            "proteção contra travessuras",
            "VIP de 1 dia"
        ]
        efeito_escolhido = random.choice(efeitos_bonus)

        if efeito_escolhido == "dobro de cenouras ao cenourar":
            ativar_dobro_cenouras(user_id)
            bot.send_message(user_id, "🥕 Bônus ativado: Você receberá o dobro de cenouras quando cenourar!")
        
        elif efeito_escolhido == "peixes em dobro na pesca":
            ativar_peixes_em_dobro(user_id)
            bot.send_message(user_id, "🐟 Bônus ativado: Você receberá peixes em dobro ao pescar!")

        elif efeito_escolhido == "proteção contra travessuras":
            adicionar_protecao_temporaria(user_id)
        
        elif efeito_escolhido == "VIP de 1 dia":
            adicionar_vip_temporario(user_id, GRUPO_SUGESTAO, dias=1)
            bot.send_message(user_id, "⚡ Bônus ativado: Você recebeu VIP por 1 dia!")

    except Exception as e:
        print(f"Erro ao realizar combo de gostosuras: {e}")
    finally:
        fechar_conexao(cursor, conn)


def ativar_dobro_cenouras(user_id):
    try:
        conn, cursor = conectar_banco_dados()
        fim_bonus = datetime.now() + timedelta(hours=24)

        # Armazena o bônus de cenouras dobradas no banco de dados
        cursor.execute("""
            INSERT INTO bonus_cenouras (id_usuario, fim_bonus)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE fim_bonus = %s
        """, (user_id, fim_bonus, fim_bonus))
        conn.commit()

    except Exception as e:
        print(f"Erro ao ativar bônus de cenouras: {e}")
    finally:
        fechar_conexao(cursor, conn)

def ativar_peixes_em_dobro(user_id):
    try:
        conn, cursor = conectar_banco_dados()
        fim_bonus = datetime.now() + timedelta(hours=24)

        # Armazena o bônus de peixes em dobro no banco de dados
        cursor.execute("""
            INSERT INTO bonus_peixes (id_usuario, fim_bonus)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE fim_bonus = %s
        """, (user_id, fim_bonus, fim_bonus))
        conn.commit()

    except Exception as e:
        print(f"Erro ao ativar bônus de peixes em dobro: {e}")
    finally:
        fechar_conexao(cursor, conn)
import random
from datetime import datetime, timedelta

def iniciar_compartilhamento(user_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Verificar se o usuário já tem um compartilhamento ativo
        cursor.execute("SELECT ativo FROM compartilhamentos WHERE id_usuario = %s", (user_id,))
        resultado = cursor.fetchone()

        if resultado and resultado[0]:  # Se já tiver um compartilhamento ativo
            bot.send_message(user_id, "👻 Você já tem um compartilhamento ativo! Compartilhe antes de ganhar mais.")
            return

        # Gerar uma quantidade de cenouras entre 50 e 100
        cenouras_ganhas = random.randint(50, 100)
        
        # Registrar o compartilhamento no banco de dados
        cursor.execute("""
            INSERT INTO compartilhamentos (id_usuario, quantidade_cenouras)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE quantidade_cenouras = %s, ativo = TRUE, data_inicio = NOW()
        """, (user_id, cenouras_ganhas, cenouras_ganhas))
        conn.commit()

        # Enviar a mensagem informando sobre o compartilhamento
        bot.send_message(user_id, f"🎃 Você ganhou {cenouras_ganhas} cenouras! Agora escolha alguém para compartilhar usando o comando +compartilhar <id do jogador>.")
    
    except Exception as e:
        print(f"Erro ao iniciar o compartilhamento: {e}")
    
    finally:
        fechar_conexao(cursor, conn)
def compartilhar_cenouras(user_id, target_user_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Verificar se o usuário tem um compartilhamento ativo
        cursor.execute("SELECT quantidade_cenouras FROM compartilhamentos WHERE id_usuario = %s AND ativo = TRUE", (user_id,))
        resultado = cursor.fetchone()

        if not resultado:
            bot.send_message(user_id, "👻 Você não tem nenhum compartilhamento ativo. Ative um compartilhamento primeiro com o comando /halloween.")
            return

        quantidade_cenouras = resultado[0]

        # Transferir cenouras para o alvo do compartilhamento
        cursor.execute("UPDATE usuarios SET cenouras = cenouras + %s WHERE id_usuario = %s", (quantidade_cenouras, target_user_id))
        cursor.execute("UPDATE usuarios SET cenouras = cenouras + %s WHERE id_usuario = %s", (quantidade_cenouras, user_id))
        
        # Desativar o compartilhamento
        cursor.execute("UPDATE compartilhamentos SET ativo = FALSE WHERE id_usuario = %s", (user_id,))
        conn.commit()

        # Informar ambos os usuários
        bot.send_message(user_id, f"🎃 Você compartilhou {quantidade_cenouras} cenouras com {target_user_id}! Cenouras adicionadas.")
        bot.send_message(target_user_id, f"🎃 {user_id} compartilhou {quantidade_cenouras} cenouras com você! Aproveite!")
    
    except Exception as e:
        print(f"Erro ao compartilhar cenouras: {e}")
    
    finally:
        fechar_conexao(cursor, conn)


def encontrar_abobora(user_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Verificar quais abóboras o usuário já ganhou
        cursor.execute("SELECT id_abobora FROM aboboras_ganhas WHERE id_usuario = %s", (user_id,))
        aboboras_ganhas = cursor.fetchall()

        aboboras_ganhas_ids = [row[0] for row in aboboras_ganhas]

        # Filtrar as abóboras que ainda não foram ganhas
        aboboras_disponiveis = {id_abobora: aboboras[id_abobora] for id_abobora in aboboras if id_abobora not in aboboras_ganhas_ids}

        if not aboboras_disponiveis:
            bot.send_message(user_id, "🎃 Você já encontrou todas as abóboras disponíveis!")
            return

        # Escolher uma abóbora aleatória entre as disponíveis
        id_abobora = random.choice(list(aboboras_disponiveis.keys()))
        abobora = aboboras_disponiveis[id_abobora]

        # Registrar que o jogador ganhou essa abóbora
        cursor.execute("INSERT INTO aboboras_ganhas (id_usuario, id_abobora) VALUES (%s, %s)", (user_id, id_abobora))
        conn.commit()

        # Entregar o prêmio
        if "cenouras" in abobora["premio"]:
            quantidade = int(abobora["premio"].split()[0])
            aumentar_cenouras(user_id, quantidade)
            bot.send_message(user_id, f"🎃 {abobora['nome']} encontrada! Parabéns, você recebeu {quantidade} cenouras!")
        elif abobora["premio"] == "Carta Faltante":
            adicionar_carta_faltante_halloween(user_id)
            bot.send_message(user_id, f"🎃 {abobora['nome']} encontrada! Parabéns, você recebeu uma carta faltante do evento!")
        
        # Adicione outras possíveis premiações aqui

    except Exception as e:
        print(f"Erro ao encontrar abóbora: {e}")
    
    finally:
        fechar_conexao(cursor, conn)

def ganhar_caixa_misteriosa(user_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Verificar quantas caixas o usuário já tem
        cursor.execute("SELECT COUNT(*) FROM caixas_misteriosas WHERE id_usuario = %s", (user_id,))
        quantidade_caixas = cursor.fetchone()[0]

        if quantidade_caixas >= 3:
            bot.send_message(user_id, "🎁 Você já tem 3 Caixas Misteriosas no estoque. Deseja jogar uma fora para ganhar uma nova?")
            # Implementar a lógica de escolha para jogar fora uma caixa ou recusar
            return

        # Atribuir um número de caixa misteriosa aleatório (único para esse jogador)
        numero_caixa = random.randint(1, 10000)  # Número de exemplo, ajustável conforme necessidade

        # Registrar a nova caixa no estoque do jogador
        cursor.execute("INSERT INTO caixas_misteriosas (id_usuario, numero_caixa) VALUES (%s, %s)", (user_id, numero_caixa))
        conn.commit()

        bot.send_message(user_id, f"🎁 Você ganhou uma Caixa Misteriosa! Ela será revelada no último dia do evento. Número da caixa: {numero_caixa}")

    except Exception as e:
        print(f"Erro ao ganhar Caixa Misteriosa: {e}")
    
    finally:
        fechar_conexao(cursor, conn)
def descartar_caixa_misteriosa(user_id, numero_caixa):
    try:
        conn, cursor = conectar_banco_dados()

        # Remover a caixa específica do estoque do jogador
        cursor.execute("DELETE FROM caixas_misteriosas WHERE id_usuario = %s AND numero_caixa = %s", (user_id, numero_caixa))
        conn.commit()

        bot.send_message(user_id, f"❌ Você jogou fora a Caixa Misteriosa número {numero_caixa}.")

    except Exception as e:
        print(f"Erro ao descartar Caixa Misteriosa: {e}")
    
    finally:
        fechar_conexao(cursor, conn)
def revelar_caixas_misteriosas(user_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Obter todas as caixas do jogador
        cursor.execute("SELECT numero_caixa FROM caixas_misteriosas WHERE id_usuario = %s", (user_id,))
        caixas = cursor.fetchall()

        if not caixas:
            bot.send_message(user_id, "🎁 Você não tem nenhuma Caixa Misteriosa para revelar.")
            return

        for caixa in caixas:
            numero_caixa = caixa[0]

            # Determinar o prêmio da caixa misteriosa (exemplo: 50 a 100 cenouras, uma carta especial etc.)
            premio = random.choice([
                f"{random.randint(50, 100)} cenouras",
                "Uma carta especial do evento",
                "VIP de 1 a 7 dias"
            ])

            # Enviar a mensagem de revelação para o jogador
            bot.send_message(user_id, f"🎁 Caixa Misteriosa número {numero_caixa} revelada! Você ganhou: {premio}")

            # Se o prêmio for cenouras, adicionar ao saldo
            if "cenouras" in premio:
                quantidade_cenouras = int(premio.split()[0])
                aumentar_cenouras(user_id, quantidade_cenouras)

            # Implementar a lógica para adicionar outros prêmios (VIP, carta especial, etc.)

        # Limpar as caixas do jogador após a revelação
        cursor.execute("DELETE FROM caixas_misteriosas WHERE id_usuario = %s", (user_id,))
        conn.commit()

    except Exception as e:
        print(f"Erro ao revelar Caixas Misteriosas: {e}")
    
    finally:
        fechar_conexao(cursor, conn)
def opcoes_descartar_caixa(user_id, caixas):
    markup = InlineKeyboardMarkup()
    for caixa in caixas:
        numero_caixa = caixa[0]
        botao = InlineKeyboardButton(text=f"Caixa {numero_caixa}", callback_data=f"descartar_caixa_{numero_caixa}")
        markup.add(botao)

    bot.send_message(user_id, "Escolha uma Caixa Misteriosa para jogar fora:", reply_markup=markup)
def mostrar_portas_escolha(user_id):
    # Definir três prêmios aleatórios
    premios = [
        f"{random.randint(50, 100)} cenouras",
        "VIP por 1 dia",
        "Uma carta faltante do evento Halloween"
    ]
    
    # Embaralhar os prêmios para cada jogador ter uma experiência diferente
    random.shuffle(premios)

    # Salvar os prêmios para o usuário (exemplo de cache ou banco de dados)
    salvar_premios_escolha(user_id, premios)

    # Criar os botões das portas
    markup = InlineKeyboardMarkup()
    porta_1 = InlineKeyboardButton("🚪 Porta 1", callback_data=f"escolha_porta_1_{user_id}")
    porta_2 = InlineKeyboardButton("🚪 Porta 2", callback_data=f"escolha_porta_2_{user_id}")
    porta_3 = InlineKeyboardButton("🚪 Porta 3", callback_data=f"escolha_porta_3_{user_id}")
    
    markup.add(porta_1, porta_2, porta_3)
    
    # Enviar a mensagem com as três portas
    bot.send_message(user_id, "Escolha uma porta! Todas as portas escondem algo bom:", reply_markup=markup)
def salvar_premios_escolha(user_id, premios):
    # Aqui você pode salvar os prêmios no banco de dados ou em cache
    # Exemplo básico:
    conn, cursor = conectar_banco_dados()
    cursor.execute("REPLACE INTO escolhas (id_usuario, premio1, premio2, premio3) VALUES (%s, %s, %s, %s)",
                   (user_id, premios[0], premios[1], premios[2]))
    conn.commit()
    fechar_conexao(cursor, conn)

def recuperar_premios_escolha(user_id):
    # Recupera os prêmios do banco de dados ou cache
    conn, cursor = conectar_banco_dados()
    cursor.execute("SELECT premio1, premio2, premio3 FROM escolhas WHERE id_usuario = %s", (user_id,))
    premios = cursor.fetchone()
    fechar_conexao(cursor, conn)
    return premios if premios else ["", "", ""]
def processar_premio(user_id, premio):
    if "cenouras" in premio:
        # Extrair a quantidade de cenouras
        quantidade_cenouras = int(premio.split()[0])
        aumentar_cenouras(user_id, quantidade_cenouras)

    elif "VIP" in premio:
        # Conceder VIP de 1 dia
        conceder_vip(user_id, 1)

    elif "carta faltante" in premio:
        # Dar uma carta faltante do evento
        dar_carta_faltante(user_id, "Halloween")
def adicionar_inverter_travessura(user_id):
    try:
        conn, cursor = conectar_banco_dados()
        # Atualiza o banco de dados para adicionar a habilidade ao jogador
        cursor.execute("UPDATE usuarios SET pode_inverter_travessura = %s WHERE id_usuario = %s", (True, user_id))
        conn.commit()
        bot.send_message(user_id, "🎃 Você ganhou a habilidade de inverter uma travessura! Quando for alvo, poderá reverter o efeito.")
    except Exception as e:
        print(f"Erro ao adicionar a chance de inverter a travessura: {e}")
    finally:
        fechar_conexao(cursor, conn)

# Função que será chamada quando o jogador for alvo de uma travessura
def verificar_inverter_travessura(user_id, atacante_id):
    try:
        conn, cursor = conectar_banco_dados()
        cursor.execute("SELECT pode_inverter_travessura FROM usuarios WHERE id_usuario = %s", (user_id,))
        resultado = cursor.fetchone()
        if resultado and resultado[0]:  # Se o jogador tiver a habilidade de inverter
            # Inverte a travessura
            cursor.execute("UPDATE usuarios SET pode_inverter_travessura = %s WHERE id_usuario = %s", (False, user_id))
            conn.commit()
            bot.send_message(atacante_id, "👻 A travessura foi invertida e agora o efeito recai sobre você!")
            bot.send_message(user_id, "🎃 Você usou sua habilidade e inverteu a travessura!")
        else:
            bot.send_message(user_id, "Você não possui a habilidade de inverter a travessura no momento.")
    except Exception as e:
        print(f"Erro ao verificar e inverter a travessura: {e}")
    finally:
        fechar_conexao(cursor, conn)
def adicionar_super_boost_cenouras(user_id, multiplicador, duracao_horas):
    try:
        conn, cursor = conectar_banco_dados()
        # Adiciona o multiplicador e a duração ao banco de dados
        cursor.execute("UPDATE usuarios SET boost_cenouras = %s, duracao_boost = %s, inicio_boost = NOW() WHERE id_usuario = %s", (multiplicador, duracao_horas, user_id))
        conn.commit()
        bot.send_message(user_id, f"🌟 Você recebeu um Super Boost de Cenouras! Todas as cenouras que você ganhar serão multiplicadas por {multiplicador} nas próximas {duracao_horas} horas.")
    except Exception as e:
        print(f"Erro ao adicionar Super Boost de Cenouras: {e}")
    finally:
        fechar_conexao(cursor, conn)

# Função para aplicar o boost ao jogador quando ele ganha cenouras
def aplicar_boost_cenouras(user_id, cenouras_ganhas):
    try:
        conn, cursor = conectar_banco_dados()
        cursor.execute("SELECT boost_cenouras, duracao_boost, TIMESTAMPDIFF(HOUR, inicio_boost, NOW()) as horas_passadas FROM usuarios WHERE id_usuario = %s", (user_id,))
        resultado = cursor.fetchone()

        if resultado and resultado[0] and resultado[2] < resultado[1]:  # Se o jogador tem boost ativo e dentro da duração
            multiplicador = resultado[0]
            cenouras_com_boost = cenouras_ganhas * multiplicador
            cursor.execute("UPDATE usuarios SET cenouras = cenouras + %s WHERE id_usuario = %s", (cenouras_com_boost, user_id))
            conn.commit()
            bot.send_message(user_id, f"🌟 Suas cenouras foram multiplicadas! Você recebeu {cenouras_com_boost} cenouras.")
        else:
            # Sem boost ativo ou fora da duração, dá as cenouras normalmente
            cursor.execute("UPDATE usuarios SET cenouras = cenouras + %s WHERE id_usuario = %s", (cenouras_ganhas, user_id))
            conn.commit()
            bot.send_message(user_id, f"Você recebeu {cenouras_ganhas} cenouras.")
    except Exception as e:
        print(f"Erro ao aplicar boost de cenouras: {e}")
    finally:
        fechar_conexao(cursor, conn)
def ativar_travessura_embaralhamento(user_id, duracao_minutos):
    try:
        conn, cursor = conectar_banco_dados()

        fim_travessura = datetime.now() + timedelta(minutes=duracao_minutos)

        # Inserir ou atualizar a travessura no banco
        cursor.execute("""
            INSERT INTO travessuras (id_usuario, tipo_travessura, fim_travessura)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE tipo_travessura = VALUES(tipo_travessura), fim_travessura = VALUES(fim_travessura)
        """, (user_id, 'embaralhamento', fim_travessura))
        conn.commit()

        bot.send_message(user_id, f"🎃 Você foi atingido por uma travessura! Suas mensagens serão embaralhadas pelos próximos {duracao_minutos} minutos.")
    
    except Exception as e:
        print(f"Erro ao ativar a travessura de embaralhamento: {e}")
    finally:
        fechar_conexao(cursor, conn)
def verificar_travessura_embaralhamento(user_id):
    try:
        conn, cursor = conectar_banco_dados()

        # Verificar se a travessura está ativa
        cursor.execute("""
            SELECT fim_travessura FROM travessuras
            WHERE id_usuario = %s AND tipo_travessura = 'embaralhamento'
        """, (user_id,))
        resultado = cursor.fetchone()

        if resultado:
            fim_travessura = resultado[0]
            # Se a travessura ainda está ativa (o tempo atual é menor que o fim)
            if datetime.now() < fim_travessura:
                return True
        
        return False  # Travessura não está ativa
    
    except Exception as e:
        print(f"Erro ao verificar a travessura de embaralhamento: {e}")
        return False
    finally:
        fechar_conexao(cursor, conn)
# Inicializa a tabela de inversões, caso ainda não exista
def inicializar_tabela_inversoes():
    conn, cursor = conectar_banco_dados()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inversoes (
                id_usuario BIGINT PRIMARY KEY,
                quantidade INT DEFAULT 0
            )
        """)
        conn.commit()
    except Exception as e:
        print(f"Erro ao inicializar a tabela de inversões: {e}")
    finally:
        fechar_conexao(cursor, conn)




# Função para adicionar uma inversão ao usuário
def adicionar_inversao(user_id, quantidade=1):
    conn, cursor = conectar_banco_dados()
    try:
        cursor.execute("""
            INSERT INTO inversoes (id_usuario, quantidade)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE quantidade = quantidade + %s
        """, (user_id, quantidade, quantidade))
        conn.commit()
        print(f"DEBUG: {quantidade} inversão(ões) adicionada(s) para o usuário {user_id}")
    except Exception as e:
        print(f"Erro ao adicionar inversão: {e}")
    finally:
        fechar_conexao(cursor, conn)
