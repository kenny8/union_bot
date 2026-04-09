import sys  # импортируем модуль sys для использования функции exit()
import requests  # модуль для выполнения HTTP-запросов
import json  # модуль для работы с JSON-данными
import re  # модуль для работы с регулярными выражениями
from bs4 import BeautifulSoup  # библиотека для парсинга HTML-страниц
from datetime import datetime  # для работы с временим
import settings


def json_afisha_():
    try:
        response = requests.get(settings.JSON_AFISHA_URL)
        response.raise_for_status()
    except requests.exceptions.RequestException as error:
        print(error)
        sys.exit(1)

    data = json.loads(response.text)
    afisha_card = []
    events_by_type = {"ticket": [], "subscription": []}  # Словарь для хранения событий по типам

    for idx, item in enumerate(data):
        afisha = {}
        title = item['title'][0]['value']
        soup = BeautifulSoup(item['body'][0]['value'], 'html.parser')
        txt = re.sub(r'\s+', ' ', soup.get_text()).strip()

        dt_start_list = [datetime.fromisoformat(date['value']) for date in item['field_data_koncerta']]
        dt_end_list = [datetime.fromisoformat(date['value']) for date in item['field_data_koncerta_end']]

        if any(dt.date() < datetime.today().date() for dt in dt_start_list):
            continue

        time_start_list = [[dt.strftime('%d.%m.%y'), dt.strftime('%H:%M')] for dt in dt_start_list]
        time_end_list = [[dt.strftime('%d.%m.%y'), dt.strftime('%H:%M')] for dt in dt_end_list]

        banner = item['field_banner_dlya_glavnoy'][0]['url']
        ticket = "https://www.afisha.ru/wl/691/api#/about/" + item['field_qt_id'][0]['value']

        if len(dt_start_list) > 1:
            season_ticket = True
            event_type = "subscription"
        else:
            season_ticket = False
            event_type = "ticket"

        afisha['id'] = len(afisha_card) + 1
        afisha['title'] = title
        afisha['txt'] = txt
        afisha['time_start'] = time_start_list
        afisha['time_end'] = time_end_list
        afisha['banner'] = banner
        afisha['ticket'] = ticket
        afisha['season_ticket'] = season_ticket

        afisha_card.append(afisha)
        events_by_type[event_type].append(afisha)

    events_by_type["ticket"] = sorted(events_by_type["ticket"],
                                      key=lambda x: datetime.strptime(x['time_start'][0][0], '%d.%m.%y'))
    events_by_type["subscription"] = sorted(events_by_type["subscription"],
                                            key=lambda x: datetime.strptime(x['time_start'][0][0], '%d.%m.%y'))
    for idx, event in enumerate(events_by_type["ticket"]):
        event['id'] = idx + 1
    for idx, event in enumerate(events_by_type["subscription"]):
        event['id'] = idx + 1

    return {**events_by_type}


def json_persons():
    # выполнение HTTP-запроса и проверка на ошибки
    try:
        response = requests.get(settings.JSON_PERSONS_URL)
        response.raise_for_status()
    except requests.exceptions.RequestException as error:
        print(error)
        sys.exit(1)  # выходим из программы в случае ошибки
    data = json.loads(response.text)  # преобразуем полученные данные в формат JSON
    persons_card = []  # список для хранения полученной информации
    # обработка данных из формата JSON и сохранение в списке persons_card
    for item in data:
        persons = []
        persons_name = item['title'][0]['value']  # получаем имя персоны, если оно есть
        # получаем описание персоны, если оно есть
        soup = BeautifulSoup(item['body'][0]['summary'], 'html.parser')  # получаем HTML-код описания мероприятия
        persons_description = re.sub(r'\s+', ' ',
                                     soup.get_text()).strip()  # получаем текст из HTML-кода и
        # Очищаем текст от управляющих символов
        persons_url = "https://unionzal.ru/node/" + str(
            item['nid'][0]['value'])  # получаем ссылка на сайт
        persons_tags = settings.TIPE[item['field_tags'][0]['target_id']]  # получаем список тегов персоны, если они есть
        persons_image = item['field_image'][0]['url']  # получаем изображение персоны, если оно есть
        persons.extend([persons_name, persons_description, persons_tags, persons_url, persons_image])
        persons_card.append(persons)  # добавляем полученную информацию в список persons_card
    return persons_card
