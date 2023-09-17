import sys
from http import HTTPStatus
import logging
import os
import requests
import time
from telegram import Bot, error
from dotenv import load_dotenv
from errors import HTTPRequestError, SendMessageError, RequestException
from timestamp import read_time, write_time


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

# Создаем потоковый обработчик
stream_handler = logging.StreamHandler()

# Добавляем обработчик к логгеру модуля
logger.addHandler(stream_handler)

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
            logger.critical(f'Ошибка: {value} не найдена.')
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
        raise RequestException('Ошибка при запроса к API: %s', str(exception))
    if response.status_code != HTTPStatus.OK:
        raise HTTPRequestError(
            'Статус ответа от Практикума не 200.',
            request_url=response.url,
            response_code=response.status_code,
            response_body=response.text
        )
    return response.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    try:
        homework = response.get('homeworks')
    except Exception:
        raise TypeError('Ответ API не содержит ключа "homeworks"')
    if not isinstance(homework, list):
        raise TypeError('Неверный формат списка домашних заданий')
    return homework


def wrapper_parse_status(func):
    """Обработка функции для pytest."""
    def wrapper(homework_list):
        """Извлекаем статусы из ответа с Практикума."""
        # Костыль для pytest.
        if isinstance(homework_list, dict):
            return func(homework_list)
        # Основная работа по проверке статуса.
        if len(homework_list) < 2:
            homevork = homework_list[0]
            return func(homevork)
        # Обработка если в ответе больше одной домашки.
        message = ''
        for homework_dict in homework_list:
            try:
                homework_name = homework_dict['homework_name']
                status = homework_dict['status']
                verdict = HOMEWORK_VERDICTS[status]
            except KeyError as exception:
                raise KeyError(f'Отсутствует ключ {exception} в ответе API.')
            message += (
                f'Изменился статус проверки работы "{homework_name}". '
                f'{verdict}\n'
            )
        return message
    return wrapper


@wrapper_parse_status
def parse_status(homework):
    """Извлекаем статус из ответа с Практикума."""
    if not isinstance(homework, dict):
        raise TypeError('Неверный формат домашнего задания')
    try:
        homework_name = homework['homework_name']
        status = homework['status']
        verdict = HOMEWORK_VERDICTS[status]
    except KeyError as exception:
        raise KeyError(f'Отсутствует ключ {exception} в ответе API.')
    message = f'Изменился статус проверки работы "{homework_name}". {verdict}'
    return message


def send_message(bot, message):
    """Отправляет в telegram сообщение."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except error.TelegramError as exception:
        raise SendMessageError(f'Ошибка отправки сообщения: {exception}')
    else:
        logger.debug('Сообщение о смене статуса отправлено.')


def main():
    """Основная логика работы бота."""
    # Проверяет доступность переменных окружения.
    check_tokens()
    bot = Bot(token=TELEGRAM_TOKEN)
    message = None
    while True:
        try:
            # Получаем время предыдущего запроса.
            timestamp = read_time()
            # Записываем время текущего запроса.
            write_time()
            # Сохраняем ответ от эндпоинта.
            api_data = get_api_answer(timestamp)
            # Проверяем ответ на соответствие документации.
            homework_list = check_response(api_data)
            # Формируем сообщение.
            message = parse_status(homework_list)
        except IndexError:
            # Отлавливаю ошибку пустого словаря переменной message.
            logger.debug('Ответ АPI пуст. Бот работает в штатном режиме.')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            # Отправляем сообщение.
            logger.error(message)
        finally:
            if message:
                try:
                    # Отправляем сообщение.
                    send_message(bot, message)
                except Exception as error:
                    logger.error(f'Сбой в работе программы: {error}')
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
