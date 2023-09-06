import requests
from pprint import pprint

url = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
headers = {'Authorization': 'OAuth y0_AgAAAAAyJ55PAAYckQAAAADr4_HlSWx5X1b-T3KZweaLtzSJtqzPi30'}
payload = {'from_date': 1693569805}

# Делаем GET-запрос к эндпоинту url с заголовком headers и параметрами params
homework_statuses = requests.get(url, headers=headers, params=payload)

# Печатаем ответ API в формате JSON
# print(homework_statuses.text)

# А можно ответ в формате JSON привести к типам данных Python и напечатать и его
homework_statuses = homework_statuses.json()
homework_name = homework_statuses['homeworks'][0]['homework_name'][9:-4]
verdict = homework_statuses['homeworks'][0]['status']
pprint(homework_statuses)
# print(homework_name, verdict)


# def check_response(response):
#     """Проверка на обновление статуса."""
#     resolt = False
#     try:
#         with open('answer.txt', 'r+', encoding='utf8') as file:
#             status = file.readlines()[-1].strip()
#             if status != response and response:
#                 file.write(response + '\n')
#                 resolt = True
#     except:
#         # Если файл не найден будет создан.
#         with open('answer.txt', 'w', encoding='utf8') as file:
#             file.write(response + '\n')
#             if response:
#                 resolt = True
#     return resolt

# print(check_response(""))

#######
# from_date = homework_statuses['current_date']