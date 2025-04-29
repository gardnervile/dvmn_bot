import os
import requests
import time

import telegram
from dotenv import load_dotenv


def make_message_sender(bot, chat_id):
    def send_message(text):
        bot.send_message(chat_id=chat_id, text=text)
    
    return send_message


def monitor_review_status(dvmn_token, send_message_func):
    url = 'https://dvmn.org/api/long_polling/'
    headers = {
        'Authorization': f'Token {dvmn_token}',
    }
    params = {}
    
    while True:
        try:
            response = requests.get(url, headers=headers, params=params, timeout=90)
            response.raise_for_status()
            data = response.json()

            if data['status'] == 'found':
                for attempt in data['new_attempts']:
                    lesson_title = attempt['lesson_title']
                    is_negative = attempt['is_negative']
                    lesson_url = attempt['lesson_url']

                    if is_negative:
                        text = f'❌ Работа "{lesson_title}" не принята, нужно доработать. Посмотреть урок - {lesson_url}'
                    else:
                        text = f'✅ Работа "{lesson_title}" успешно принята! Поздравляем! Посмотреть урок - {lesson_url}'
                    
                    send_message_func(text)

                params['timestamp'] = data['last_attempt_timestamp']

            elif data['status'] == 'timeout':
                params['timestamp'] = data['last_attempt_timestamp']

        except requests.exceptions.ReadTimeout:
            print('Таймаут ожидания. Жду новую проверку...')
            continue

        except requests.exceptions.ConnectionError:
            print('Ошибка соединения. Подожду 10 секунд...')
            time.sleep(10)
            continue


def main():
    load_dotenv()
    dvmn_token = os.getenv('TOKEN_API')
    telegram_token = os.getenv('TG_TOKEN')
    chat_id = int(os.getenv('CHAT_ID'))

    bot = telegram.Bot(token=telegram_token)
    
    send_message_func = create_messenger(bot, chat_id)

    review_user(dvmn_token, send_message_func)


if __name__ == '__main__':
    main()
