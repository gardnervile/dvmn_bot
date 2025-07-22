import os
import requests
import time

import telegram
from dotenv import load_dotenv
import logging


logging.basicConfig(
    level=logging.INFO,  # или DEBUG если хочешь подробнее
    format="%(asctime)s %(levelname)s:%(name)s:%(message)s"
)

logger = logging.getLogger(__name__)


def monitor_review_status(dvmn_token, send_message_func, params):
    url = 'https://dvmn.org/api/long_polling/'
    headers = {
        'Authorization': f'Token {dvmn_token}',
    }

    response = requests.get(url, headers=headers, params=params, timeout=90)
    response.raise_for_status()
    review_response = response.json()

    new_params = {**params}

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

        new_params['timestamp'] = review_response['last_attempt_timestamp']

    elif review_response['status'] == 'timeout':
        new_params['timestamp'] = review_response['last_attempt_timestamp']

    return new_params


def main():
    load_dotenv()
    dvmn_token = os.environ['TOKEN_API']
    telegram_token = os.environ['TG_TOKEN']
    chat_id = int(os.environ['CHAT_ID'])

    bot = telegram.Bot(token=telegram_token)
    send_message_func = lambda text: bot.send_message(chat_id=chat_id, text=text)

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
