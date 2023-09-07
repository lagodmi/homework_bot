import logging
import os
import requests
import schedule
import time
from telegram import Bot
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    filemode='w',
    format='%(asctime)s, %(levelname)s, %(message)s'
)


PRACTICUM_TOKEN = 'y0_AgAAAAAyJ55PAAYckQAAAADr4_HlSWx5X1b-T3KZweaLtzSJtqzPi30'
TELEGRAM_TOKEN = os.getenv('Token')
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
    """Проверяет доступность переменных окружения."""
    if not PRACTICUM_TOKEN:
        logging.critical(
            'Ошибка: токен для Яндекс Практикума не найден.'
        )
    if not TELEGRAM_TOKEN:
        logging.critical(
            'Ошибка: токен для Telegram не найден.'
        )


def get_api_answer(timestamp):
    """Делает запрос к эндпоинту."""
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
    except Exception:
        logging.error('Ошибка при запросе к API.')
    return response.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if not response['homeworks']:
        logging.debug('API не соответствует.')


def parse_status(homework):
    """Извлекаем статус из ответа с Практикума."""
    try:
        homework_name = homework['homeworks'][0]['homework_name'][9:-4]
        status = homework['homeworks'][0]['status']
    except Exception:
        logging.error('Отсутствие ожидаемых ключей в ответе API.')
    verdict = HOMEWORK_VERDICTS[status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot, message):
    """Отправляет в telegram сообщение."""
    try:
        bot.sendMessage(TELEGRAM_CHAT_ID, message)
        logging.debug('Сообщение о смене статуса отправлено.')
    except Exception:
        logging.error('Ошибка в отправке сообщения.')


def main():
    """Основная логика работы бота."""
    bot = Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time()) - 600000
    try:
        # Проверяет доступность переменных окружения.
        check_tokens()
        # Сохраняем ответ от эндпоинта.
        answer = get_api_answer(timestamp)
        # Проверяем ответ на соответствие документации.
        check_response(answer)
        # Формируем сообщение.
        message = parse_status(answer)
        # Отправляем сообщение.
        send_message(bot, message)
    except Exception as error:
        message = f'Сбой в работе программы: {error}'
        # Отправляем сообщение.
        send_message(bot, message)


if __name__ == '__main__':
    # Запуск функции каждые 10 минут
    schedule.every(1).minutes.do(main)
    # Бесконечный цикл для выполнения расписания
    while True:
        schedule.run_pending()
        time.sleep(1)
