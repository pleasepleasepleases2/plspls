
import telebot

bot = telebot.TeleBot("7088149058:AAFdanx1YlD-AgfinrFXEC6eJEE2FFzWDNI")

# Função principal para iniciar o polling
def start_polling():
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception as e:
            print(f"Erro no bot: {e}")


if __name__ == "__main__":
    start_polling()