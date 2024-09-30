import requests
def get_command_user_id(message):
    return message.from_user.id

def get_replied_user_id(message):
    if message.reply_to_message:
        return message.reply_to_message.from_user.id
    return None  # Retorna None se a mensagem não for uma resposta

def get_command_user_name(message):
    return message.from_user.first_name

def get_replied_user_name(message):
    if message.reply_to_message:
        return message.reply_to_message.from_user.first_name
    return None  # Retorna None se a mensagem não for uma resposta

def get_username_from_id(user_id):
    token = 'YOUR_TELEGRAM_BOT_TOKEN'
    url = f"https://api.telegram.org/bot{token}/getChat?chat_id={user_id}"
    
    response = requests.get(url)
    data = response.json()
    
    if data['ok']:
        username = data['result'].get('username')
        if username:
            return username
        else:
            return "O usuário não tem um username."
    else:
        return "Erro ao buscar o username."