import os
import requests
import time

import telegram
from dotenv import load_dotenv


def make_message_sender(bot, chat_id):
    def send_message(text):
        bot.send_message(chat_id=chat_id, text=text)
    
    return send_message


def monitor_review_status(dvmn_token, send_message_func, params):
    url = 'https://dvmn.org/api/long_polling/'
    headers = {
        'Authorization': f'Token {dvmn_token}',
    }

    response = requests.get(url, headers=headers, params=params, timeout=90)
    response.raise_for_status()
    review_response = response.json()

    if review_response['status'] == 'found':
        for attempt in review_response['new_attempts']:
            lesson_title = attempt['lesson_title']
            is_negative = attempt['is_negative']
            lesson_url = attempt['lesson_url']

            if is_negative:
                text = f'❌ Работа "{lesson_title}" не принята. [Посмотреть задание]({lesson_url})'
            else:
                text = f'✅ Работа "{lesson_title}" успешно принята! [Посмотреть задание]({lesson_url})'
            
            send_message_func(text)

        params['timestamp'] = review_response['last_attempt_timestamp']

    elif review_response['status'] == 'timeout':
        params['timestamp'] = review_response['last_attempt_timestamp']

    return params


def handle_connection_error():
    print('Ошибка соединения. Подожду 10 секунд...')
    time.sleep(10)


def main():
    load_dotenv()
    dvmn_token = os.getenv('TOKEN_API')
    telegram_token = os.getenv('TG_TOKEN')
    chat_id = int(os.getenv('CHAT_ID'))

    bot = telegram.Bot(token=telegram_token)
    send_message_func = make_message_sender(bot, chat_id)

    params = {}

    while True:
        try:
            params = monitor_review_status(dvmn_token, send_message_func, params)
        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.ConnectionError:
            print('Ошибка соединения. Жду 10 секунд...')
            time.sleep(10)
            continue


if __name__ == '__main__':
    main()
