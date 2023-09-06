import os
import requests
import schedule
import time
from telegram import ReplyKeyboardMarkup, Bot
from telegram.ext import CommandHandler, Updater

from dotenv import load_dotenv

import errors

load_dotenv()


PRACTICUM_TOKEN = 'y0_AgAAAAAyJ55PAAYckQAAAADr4_HlSWx5X1b-T3KZweaLtzSJtqzPi30'
TELEGRAM_TOKEN = os.getenv('TOKEN')
TELEGRAM_CHAT_ID = 5766924512

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверяет наличие токенов."""
    if not PRACTICUM_TOKEN:
        raise errors.PracticumTokenError(
            'Ошибка: токен для Яндекс Практикума не найден.'
        )
    if not TELEGRAM_TOKEN:
        raise errors.TelegramTokenError(
            'Ошибка: токен для Telegram не найден.'
        )


def send_message(bot, message):
    """Отправляет в telegram сообщение."""
    bot.sendMessage(TELEGRAM_CHAT_ID, message)


def get_api_answer(timestamp):
    """Получаем ответ от Яндекс Практикума."""
    return requests.get(
        ENDPOINT,
        headers={'Authorization': PRACTICUM_TOKEN},
        params={'from_date': timestamp}
    )


def check_response(response):
    """Проверка на обновление статуса."""
    result = False
    try:
        # Пытаемся открыть файл.
        with open('answer.txt', 'r+', encoding='utf8') as file:
            # Читаем последний статус.
            status = file.readlines()[-1].strip()
            # Если текуший статус не совпадает и он не False.
            if status != response and response:
                # Записываем тикущий статус и возвращаем True.
                file.write(response + '\n')
                result = True
    except FileNotFoundError:
        # Если файл не найден будет создан.
        with open('answer.txt', 'w', encoding='utf8') as file:
            # Записываем тикущий статус.
            file.write(response + '\n')
            # Если текуший статус True возвращаем True.
            if response:
                result = True
    return result


def parse_status(homework):
    """Извлекаем статус из ответа с Практикума."""
    homework_name = homework['homeworks'][0]['homework_name'][9:-4]
    verdict = homework['homeworks'][0]['status']
    # Проверка изменился ли статус.
    if check_response():
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    bot = Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time()) - 600
    answer = get_api_answer(timestamp)
    message = parse_status(answer)
    if message:
        send_message(bot, message)

    while True:
        try:
            # Запуск функции каждые 10 минут
            schedule.every(10).minutes.do(main)
            # Бесконечный цикл для выполнения расписания
            while True:
                schedule.run_pending()
                time.sleep(1)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            ...
        ...


if __name__ == '__main__':
    main()
