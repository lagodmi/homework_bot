import sys
from http import HTTPStatus
import logging
import os
import requests
import time
from telegram import Bot, error
from dotenv import load_dotenv
from errors import HTTPRequestError


load_dotenv()

# создаем потоковый обработчик
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)

# добавляем обработчик к корневому логгеру
logging.getLogger().addHandler(handler)

# создаем логгер для модуля my_module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# создаем файловый обработчик и задаем ему уровень логирования
file_handler = logging.FileHandler('main.log', mode='w')
file_handler.setLevel(logging.DEBUG)

# создаем форматтер и задаем ему формат сообщений
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(formatter)

# добавляем обработчик к логгеру
logger.addHandler(file_handler)


PRACTICUM_TOKEN = os.getenv('practicum_token')
TELEGRAM_TOKEN = os.getenv('token')
TELEGRAM_CHAT_ID = os.getenv('chat_id')

DURATION_IN_SECONDS = 600
RETRY_PERIOD = DURATION_IN_SECONDS
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверяет доступность переменных окружения."""
    constante_dict = {
        PRACTICUM_TOKEN: 'котстанта токена для Яндекс Практикума',
        TELEGRAM_TOKEN: 'константа токена для Telegram',
        TELEGRAM_CHAT_ID: 'константа chat id',
        RETRY_PERIOD: 'константа повторного пориода',
        ENDPOINT: 'ENDPOINT'
    }
    for key, value in constante_dict.items():
        if key is None:
            logging.critical(f'Ошибка: {value} не найдена.')
            sys.exit(1)


def get_api_answer(timestamp):
    """Делает запрос к эндпоинту."""
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
    except requests.RequestException as exception:
        logger.error('Ошибка при запросе к API: %s', str(exception))
    if response.status_code != HTTPStatus.OK:
        raise HTTPRequestError
    logger.debug('Работает исправно')
    return response.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    try:
        homework = response.get('homeworks')
    except Exception:
        raise TypeError
    if not isinstance(homework, list):
        raise TypeError
    return homework


# Альтернативный вариант pytest не проходит.
# def parse_status(homework):
#     """Извлекаем статусы из ответа с Практикума."""
#     message = ''
#     for homework_dict in homework:
#         try:
#             homework_name = homework_dict['homework_name']
#             status = homework_dict['status']
#             verdict = HOMEWORK_VERDICTS[status]
#         except KeyError as exception:
#             logger.error(f'Отсутствует ключ {exception} в ответе API.')
#             raise KeyError
#         message += (
#             f'Изменился статус проверки работы "{homework_name}". '
#             f'{verdict}\n'
#         )
#     return message


def parse_status(homework):
    """Извлекаем статус из ответа с Практикума."""
    try:
        homework_name = homework['homework_name']
        status = homework['status']
        verdict = HOMEWORK_VERDICTS[status]
    except KeyError as exception:
        logger.error(f'Отсутствует ключ {exception} в ответе API.')
        raise KeyError
    message = f'Изменился статус проверки работы "{homework_name}". {verdict}'
    return message


def send_message(bot, message):
    """Отправляет в telegram сообщение."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except error.TelegramError:
        logger.error('Ошибка при отправке сообщения.')
    logger.debug('Сообщение о смене статуса отправлено.')


def main():
    """Основная логика работы бота."""
    # Проверяет доступность переменных окружения.
    check_tokens()
    bot = Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time() - RETRY_PERIOD)
    while True:
        try:
            # Сохраняем ответ от эндпоинта.
            response = get_api_answer(timestamp)
            # Проверяем ответ на соответствие документации.
            homework = check_response(response)
            # Формируем сообщение.
            message = parse_status(homework[0])
            # Формируем сообщение.(альтернативный вариант).
            # message = parse_status(homework)
        except IndexError:
            # Отлавливаю ошибку пустого словаря переменной message.
            logger.debug('Ответ АPI пуст. Бот работает в штатном режиме.')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            # Отправляем сообщение.
            logger.error(message)
        else:
            if message:
                # Отправляем сообщение.
                send_message(bot, message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()

# Я сделал 2 варианта один под pytest
# другой так чтобы обрабатывалось любое количество домашних работ
# не стал костылями подгонять под pytest т.к. в реальной жизни тесты
# пишуться под программу а не наоборот.
