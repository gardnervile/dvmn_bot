import os
import time
import logging
import traceback
import requests

from dotenv import load_dotenv
from requests.exceptions import ReadTimeout
from telegram import Bot


logger = logging.getLogger('bot_logger')


def send_message(bot, chat_id, text):
    bot.send_message(chat_id=chat_id, text=text, parse_mode='Markdown', disable_web_page_preview=True)


def check_review_status(dvmn_token, send_message_func, params):
    url = 'https://dvmn.org/api/long_polling/'
    headers = {'Authorization': f'Token {dvmn_token}'}

    response = requests.get(url, headers=headers, params=params, timeout=90)
    response.raise_for_status()
    review_response = response.json()

    new_params = {**params}

    if review_response['status'] == 'found':
        for attempt in review_response['new_attempts']:
            lesson_title = attempt['lesson_title']
            is_negative = attempt['is_negative']
            lesson_url = attempt['lesson_url']
            text = (
                f'❌ Работа "{lesson_title}" не принята. [Посмотреть задание]({lesson_url})'
                if is_negative else
                f'✅ Работа "{lesson_title}" успешно принята! [Посмотреть задание]({lesson_url})'
            )
            send_message_func(text)

        new_params['timestamp'] = review_response['last_attempt_timestamp']
    elif review_response['status'] == 'timeout':
        new_params['timestamp'] = review_response['last_attempt_timestamp']

    return new_params


class TelegramLogsHandler(logging.Handler):
    def __init__(self, tg_bot, chat_id):
        super().__init__()
        self.tg_bot = tg_bot
        self.chat_id = chat_id

    def emit(self, record):
        log_entry = self.format(record)
        max_length = 4000

        for i in range(0, len(log_entry), max_length):
            try:
                self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry[i:i+max_length])
            except Exception as e:
                print(f"Failed to send log chunk to Telegram: {e}")


def main():
    load_dotenv()
    dvmn_token = os.environ['TOKEN_API']
    telegram_token = os.environ['TG_TOKEN']
    chat_id = os.environ['CHAT_ID']

    bot = Bot(token=telegram_token)

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    telegram_handler = TelegramLogsHandler(bot, chat_id)
    telegram_handler.setFormatter(formatter)
    logger.addHandler(telegram_handler)

    logger.info("Бот запущен")

    params = {}

    while True:
        try:
            params = check_review_status(dvmn_token, lambda text: send_message(bot, chat_id, text), params)
        except ReadTimeout:
            continue
        except Exception:
            tb = traceback.format_exc()
            short_tb = '\n'.join(tb.splitlines()[-5:])
            logger.error(f'❌ Бот упал с ошибкой:\n```{short_tb}```')
            time.sleep(10)


if __name__ == '__main__':
    main()
