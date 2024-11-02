from pesquisas import *
from user import *
from bd import *
import functools
from pescar import *
import traceback
grupodeerro = -1002209493474
        
MAX_RETRIES = 5
RETRY_DELAY = 1  # seconds

def realizar_troca(message, eu, voce, minhacarta, suacarta, chat_id, qntminha_antes, qntsua_antes):
    retries = 0
    while retries < MAX_RETRIES:
        try:
            conn, cursor = conectar_banco_dados()

            cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (eu, minhacarta))
            qntminha = cursor.fetchone()
            
            cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (voce, suacarta))
            qntsua = cursor.fetchone()

            qntminha = qntminha[0] if qntminha else 0
            qntsua = qntsua[0] if qntsua else 0


            if qntminha > 0 and qntsua > 0:
                print(f"DEBUG: Quantidades válidas. Realizando atualização das quantidades...")

                cursor.execute("UPDATE inventario SET quantidade = quantidade - 1 WHERE id_usuario = %s AND id_personagem = %s", (eu, minhacarta))
                cursor.execute("UPDATE inventario SET quantidade = quantidade - 1 WHERE id_usuario = %s AND id_personagem = %s", (voce, suacarta))

                cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (voce, minhacarta))
                qnt_voce_minhacarta = cursor.fetchone()

                if qnt_voce_minhacarta:
                    cursor.execute("UPDATE inventario SET quantidade = quantidade + 1 WHERE id_usuario = %s AND id_personagem = %s", (voce, minhacarta))
                else:
                    cursor.execute("INSERT INTO inventario (id_usuario, id_personagem, quantidade) VALUES (%s, %s, 1)", (voce, minhacarta,))

                    cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (eu, suacarta))
                qnt_eu_suacarta = cursor.fetchone()

                if qnt_eu_suacarta:
                    cursor.execute("UPDATE inventario SET quantidade = quantidade + 1 WHERE id_usuario = %s AND id_personagem = %s", (eu, suacarta))
                else:
                    cursor.execute("INSERT INTO inventario (id_usuario, id_personagem, quantidade) VALUES (%s, %s, 1)", (eu, suacarta,))

                conn.commit()

                qntminha_depois = verifica_inventario_troca(eu, minhacarta)
                qntsua_depois = verifica_inventario_troca(voce, suacarta)

                sql_insert = """
                    INSERT INTO historico_trocas 
                    (id_usuario1, id_usuario2, quantidade_cartas_antes_usuario1, quantidade_cartas_depois_usuario1, 
                    quantidade_cartas_antes_usuario2, quantidade_cartas_depois_usuario2, id_carta_usuario1, id_carta_usuario2, aceita) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                val = (eu, voce, qntminha_antes, qntminha_depois, qntsua_antes, qntsua_depois, minhacarta, suacarta, True)
                cursor.execute(sql_insert, val)

                conn.commit()


                image_url = "https://pub-6f23ef52e8614212a14d24b0cf55ae4a.r2.dev/BQACAgEAAxkBAAIe3WcllmUOQwUnpp5VMHZWngABFsU6bAACyQQAAu1oMUXnYh3PF56CezYE.jpg"
                bot.edit_message_media(
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    media=telebot.types.InputMediaPhoto(media=image_url, caption="Troca realizada com sucesso. Até a próxima!")
                )
                break  # Sai do loop se a troca for realizada com sucesso
            else:
                print(f"DEBUG: Troca inválida: qntminha={qntminha}, qntsua={qntsua}")
                bot.edit_message_caption(chat_id=message.chat.id, message_id=message.message_id, caption="Troca inválida devido a quantidades insuficientes.")
                break
        except mysql.connector.errors.InternalError as err:
            if err.errno == 1213:  # Deadlock
                print(f"DEBUG: Deadlock detectado, tentando novamente... (tentativa {retries + 1})")
                retries += 1
                time.sleep(RETRY_DELAY)
                continue  # Tenta novamente
            else:
                traceback.print_exc()
                erro = traceback.format_exc()
                mensagem = f"Erro na troca: {eu}, {voce}, {minhacarta}, {suacarta}. Erro:\n{erro}"
                bot.send_message(grupodeerro, mensagem, parse_mode="HTML")
                bot.edit_message_caption(chat_id=message.chat.id, caption="Houve um problema com a troca, tente novamente!")
                break
        except Exception as e:
            traceback.print_exc()
            erro = traceback.format_exc()
            mensagem = f"Erro na troca: {eu}, {voce}, {minhacarta}, {suacarta}. Erro:\n{erro}"
            bot.send_message(grupodeerro, mensagem, parse_mode="HTML")
            bot.edit_message_caption(chat_id=message.chat.id, caption="Houve um problema com a troca, tente novamente!")
            break
        finally:
            print("DEBUG: Fechando conexão com o banco de dados.")
            fechar_conexao(cursor, conn)
    else:
        print("DEBUG: Falha ao realizar a troca após várias tentativas.")
        bot.edit_message_caption(chat_id=message.chat.id, caption="Falha ao realizar a troca após várias tentativas. Tente novamente mais tarde.")
def verifica_inventario_troca(id_usuario, id_personagem):
    try:
        conn, cursor = conectar_banco_dados()
        cursor.execute("SELECT quantidade FROM inventario WHERE id_usuario = %s AND id_personagem = %s", (id_usuario, id_personagem))
        quantidade = cursor.fetchone()
        return quantidade[0] if quantidade else 0
    except Exception as e:
        print(f"Erro ao verificar inventário: {e}")
    finally:
        fechar_conexao(cursor, conn)

def troca_callback(call):
    try:
        message_data = call.data.replace('troca_sim_', '').replace('troca_nao_', '')
        parts = message_data.split('_')
        conn, cursor = conectar_banco_dados()
        if len(parts) >= 5:
            eu, voce, minhacarta, suacarta, message = parts
            qntminha_antes = verifica_inventario_troca(eu, minhacarta)
            qntsua_antes = verifica_inventario_troca(voce, suacarta)
            chat_id = call.message.chat.id if call.message else None
            user_id = call.from_user.id if call.from_user else None

            eu = int(eu)
            voce = int(voce)

            print(f"Callback troca: eu={eu}, voce={voce}, minhacarta={minhacarta}, suacarta={suacarta}, user_id={user_id}")

            if user_id in [eu, voce]:
                if call.data.startswith('troca_sim_'):
                    if eu != user_id:
                        if int(voce) == 6723799817:
                            bot.edit_message_caption(chat_id=chat_id, caption="Você não pode fazer trocas com a Mabi :(")
                        elif voce == eu:
                            bot.edit_message_caption(chat_id=chat_id, caption="Você não pode fazer trocas consigo mesmo!")
                        else:
                            realizar_troca(call.message, eu, voce, minhacarta, suacarta, chat_id, qntminha_antes, qntsua_antes)
                    else:
                        bot.answer_callback_query(callback_query_id=call.id, text="Você não pode aceitar seu próprio lanche.")
                elif call.data.startswith('troca_nao_'):
                    if chat_id and call.message:
                        sql_insert = "INSERT INTO historico_trocas (id_usuario1, id_usuario2, quantidade_cartas_antes_usuario1, quantidade_cartas_depois_usuario1, quantidade_cartas_antes_usuario2, quantidade_cartas_depois_usuario2, id_carta_usuario1, id_carta_usuario2, aceita) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                        val = (eu, voce, qntminha_antes, 0, qntsua_antes, 0, minhacarta, suacarta, False)
                        cursor.execute(sql_insert, val)
                        conn.commit()
                        bot.edit_message_caption(chat_id=chat_id, message_id=call.message.message_id, caption="Poxa, um de vocês esqueceu a comida. 🕊\nQuem sabe na próxima?")
                    else:
                        print("Erro: Não há informações suficientes no callback_data.")
                        bot.answer_callback_query(callback_query_id=call.id, text="Você não pode aceitar esta troca.")
            else:
                bot.answer_callback_query(callback_query_id=call.id, text="Você não pode realizar esta ação nesta troca.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        erro = html.escape(traceback.format_exc())
        mensagem = f"Troca com erro: {call}. Erro: {e}\n{erro}"
        bot.send_message(grupodeerro, text=mensagem, parse_mode="HTML")

        chat_id = call.message.chat.id if call.message else None
        bot.edit_message_caption(chat_id=chat_id, message_id=call.message.message_id, caption="Alguém não tem o lanche enviado.\nQue tal olhar sua cesta novamente?")
    finally:
        fechar_conexao(cursor, conn)
