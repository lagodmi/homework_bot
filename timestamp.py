from time import time


def read_time():
    """Получаем время предидущего запроса."""
    with open('time_control', 'r', encoding='utf-8') as file:
        return int(file.read())


def write_time():
    """Записываем время последнего запроса."""
    with open('time_control', 'w', encoding='utf-8') as file:
        file.write(str(int(time())))
