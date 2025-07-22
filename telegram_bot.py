import logging
import os
import time

import requests
import telegram
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from telegram import Bot
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater


def monitor_review_status(dvmn_token, send_message_func, params):
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

            if is_negative:
                text = f'❌ Работа "{lesson_title}" не принята. [Посмотреть задание]({lesson_url})'
            else:
                text = f'✅ Работа "{lesson_title}" успешно принята! [Посмотреть задание]({lesson_url})'
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
        try:
            self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)
        except Exception as e:
            print(f"Failed to send log to Telegram: {e}")


def start(update, context):
    update.message.reply_text('Бот запущен и работает!')


def echo(update, context):
    update.message.reply_text(update.message.text)


def main():
    load_dotenv()

    dvmn_token = os.environ['TOKEN_API']
    telegram_token = os.environ['TG_TOKEN']
    chat_id = os.environ['CHAT_ID']

    bot = Bot(token=telegram_token)

    logger = logging.getLogger('bot_logger')
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

    def send_message(text):
        bot.send_message(chat_id=chat_id, text=text, parse_mode='Markdown')

    while True:
        try:
            params = monitor_review_status(dvmn_token, send_message, params)
        except Exception:
            logger.exception('❌ Бот упал с ошибкой:')
            time.sleep(30)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        import traceback
        load_dotenv()
        telegram_token = os.environ['TG_TOKEN']
        chat_id = os.environ['CHAT_ID']

        bot = telegram.Bot(token=telegram_token)
        bot.send_message(chat_id=chat_id, text='❌ Бот упал с ошибкой:')
        bot.send_message(chat_id=chat_id, text=traceback.format_exc())
        raise
