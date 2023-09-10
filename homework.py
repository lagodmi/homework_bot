from http import HTTPStatus
import logging
import os
import requests
import time
from telegram import Bot
from dotenv import load_dotenv


class HTTPRequestError(Exception):
    """Ошибка статуса запроса."""

    pass


class SendMessageError(Exception):
    """Ошибка отправки сообщения."""

    pass


class CheckTokenError(Exception):
    """ошибка переменной."""

    pass


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
    constante_dict = {PRACTICUM_TOKEN: 'котстанта токена для Яндекс Практикума',
                      TELEGRAM_TOKEN: 'константа токена для Telegram',
                      TELEGRAM_CHAT_ID: 'константа chat id',
                      RETRY_PERIOD: 'константа повторного пориода',
                      ENDPOINT: 'ENDPOINT'}
    for key, value in constante_dict.items():
        if not key:
            logging.critical(f'Ошибка: {value} не найдена.')
            raise CheckTokenError


def get_api_answer(timestamp):
    """Делает запрос к эндпоинту."""
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
        if response.status_code != HTTPStatus.OK:
            logging.error('Ошибка код статуса не 200')
            raise HTTPRequestError
    except requests.RequestException as e:
        logging.error('Ошибка при запросе к API: %s', str(e))
    return response.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    try:
        homework = response.get('homeworks')
        if not isinstance(homework, list):
            logging.error('Тип данных ответа API не соответствует ожиданию.')
            raise TypeError
    except Exception:
        logging.error('API не соответствует.')
        raise TypeError
    return homework


def parse_status(homework):
    """Извлекаем статус из ответа с Практикума."""
    try:
        isinstance(homework, dict)
        homework_name = homework['homework_name']
        status = homework['status']
        verdict = HOMEWORK_VERDICTS[status]
    except KeyError as e:
        logging.error(f'Отсутствует ключ {e} в ответе API.')
        raise KeyError
    except TypeError:
        logging.error('Некорректный формат ответа API.')
        raise TypeError
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot, message):
    """Отправляет в telegram сообщение."""
    try:
        bot.sendMessage(TELEGRAM_CHAT_ID, message)
        logging.debug('Сообщение о смене статуса отправлено.')
    except SendMessageError as e:
        logging.error(f'Ошибка {e} в отправке сообщения.')
        raise SendMessageError


def main():
    """Основная логика работы бота."""
    bot = Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time() - RETRY_PERIOD)
    while True:
        try:
            # Проверяет доступность переменных окружения.
            check_tokens()
            # Сохраняем ответ от эндпоинта.
            api_answer = get_api_answer(timestamp)
            # Проверяем ответ на соответствие документации.
            answer = check_response(api_answer)
            # Формируем сообщение.
            message = parse_status(answer[0])
            # Отправляем сообщение.
            send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            # Отправляем сообщение.
            logging.error(message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
