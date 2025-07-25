# DVMN Telegram Bot

Этот бот отслеживает статус проверки ваших работ на [dvmn.org](https://dvmn.org/) и присылает уведомления в Telegram.

## Как работает

- Бот подключается к API Девмана через Long Polling.
- Как только преподаватель проверяет работу, бот отправляет вам сообщение в Telegram.
- В сообщении указывается название урока, результат проверки (успех или доработка) и ссылка на сам урок.

## Настройка

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/your_username/dvmn-notifier.git
cd dvmn-notifier
```
### 2. Создайте виртуальное окружение
```
python3 -m venv venv
source venv/bin/activate
```
### 3. Установите зависимости
```
pip install -r requirements.txt
```
### 4. Настройте переменные окружения

Создайте файл .env в корне проекта со следующим содержимым:
```
TOKEN_API=ваш_токен_девмана
TG_TOKEN=токен_вашего_телеграм_бота
CHAT_ID=ваш_чат_id
```
TOKEN_API — токен доступа к API Девмана.

TG_TOKEN — токен вашего Telegram-бота, полученный через BotFather.

CHAT_ID — ваш Telegram chat_id. Узнать его можно через @userinfobot.

### 5. Запустите бота
```
python telegram_bot.py
```
Бот начнет слушать проверки ваших работ и присылать уведомления.

## Требования

- Python 3.8+
- Аккаунт на dvmn.org
- Telegram-бот

## Как остановить бота

Просто нажмите Ctrl+C в терминале. Бот корректно завершит работу.
