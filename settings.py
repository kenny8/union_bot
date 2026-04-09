from json_parser import json_afisha_
from datetime import datetime
import pickle

MAX_MESSAGE_LENGTH = 950
# MAIN_WALLPAPERS = "https://unionzal.ru/sites/default/files/2020-11/presentation-wrapper.jpg"

TOKEN_BOT = ""
# TOKEN_BOT = ""
JSON_AFISHA_URL = "https://unionzal.ru/rest/export/json/afisha"
JSON_PERSONS_URL = "https://unionzal.ru/rest/export/json/persons"
TIPE = {2: "Солисты", 20: "Коллективы", 4: "Ведущие концертов", 51: "Концертмейстеры"}
# PASSWORD = ""

PASSWORD_TXT = 'txt/password_fl.txt'
FEEDBACK_TXT = 'txt/feedback_fl.txt'
USERS_TXT = 'txt/users_chat_fl.txt'
GIVEAWAY_TXT = 'txt/giveway_fl.txt'
ADMIN_TXT = "txt/admin_fl.txt"
WALLPAPERS_TXT = "txt/wallpapers_fl.txt"

wallpapers_dict = {
    "main_wallpapers": "https://unionzal.ru/sites/default/files/2020-11/presentation-wrapper.jpg",
    "main_for_meet_wallpapers": "https://unionzal.ru/sites/default/files/2020-11/presentation-wrapper.jpg",
    "end_wallpapers": "https://unionzal.ru/sites/default/files/2020-11/presentation-wrapper.jpg",
    "feedback_wallpapers": "https://unionzal.ru/sites/default/files/2020-11/presentation-wrapper.jpg"
}

with open(WALLPAPERS_TXT, 'rb') as file:
    wallpapers_dict = pickle.load(file)

MAIN_WALLPAPERS = wallpapers_dict["main_wallpapers"]
MAIN_FOR_MEET_WALLPAPERS = wallpapers_dict["main_for_meet_wallpapers"]
END_WALLPAPERS = wallpapers_dict["end_wallpapers"]
FEEDBACK_WALLPAPERS = wallpapers_dict["feedback_wallpapers"]

PASSWORD = ""
with open(PASSWORD_TXT, 'rb') as file:
    PASSWORD = pickle.load(file)

ADMIN_STATUS = []
with open(ADMIN_TXT, 'rb') as file:
    ADMIN_STATUS = pickle.load(file)

START_GIVEAWAY = {}
with open(GIVEAWAY_TXT, 'rb') as file:
    START_GIVEAWAY = pickle.load(file)

FEEDBACK_USER = []
with open(FEEDBACK_TXT, 'rb') as file:
    FEEDBACK_USER = pickle.load(file)

USERS = []
with open(USERS_TXT, 'rb') as file:
    USERS = pickle.load(file)

print(f"пароль :{PASSWORD}")
print(f"администраторы :{ADMIN_STATUS}")
print(f"отзывы :{FEEDBACK_USER}")
print(f"пользователи :{USERS}")
print(f"розыгрыш :{START_GIVEAWAY}")

CHAT = ""  # ""
# CHAT = ""

now = datetime.now()
AFISHA_CARD = json_afisha_()
AFISHA_CARD_TIME = now
print(f"афиша :{AFISHA_CARD}")
