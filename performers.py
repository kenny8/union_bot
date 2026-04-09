
from telegram import  InlineKeyboardButton, InlineKeyboardMarkup
from telegram import InputMediaPhoto
from json_parser import json_persons
import settings
from datetime import datetime
from admin import update_admin_status
import logging

# Включение логгирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

def log_user_action(func):
    def wrapper(update, context, *args, **kwargs):
        user = update.effective_user
        logger.info(f"Пользователь {user.username} вызвал функцию {func.__name__}")
        return func(update, context, *args, **kwargs)
    return wrapper


def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    """
    Создает меню с кнопками.
    :param buttons: список кнопок
    :param n_cols: количество столбцов
    :param header_buttons: список кнопок для шапки
    :param footer_buttons: список кнопок для подвала
    :return: InlineKeyboardMarkup
    """
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu

@log_user_action
async def performers(update, context):
    """Отправка сообщения, когда пользователь нажимает на кнопку 'Исполнители'."""
    now = datetime.now()
    context.user_data["feedback"] = False
    time_diff = now - settings.PERSONS_CARD_TIME
    hours_diff = time_diff.seconds // 3600
    if hours_diff >= 12:
        print("обновились персоналии")
        settings.PERSONS_CARD = json_persons()
        settings.PERSONS_CARD_TIME = now
    persons_card = settings.PERSONS_CARD # загрузка json
    # Создание кнопок выбора выбора вида исполнителя
    #print(persons_card)
    persons = list(set(event[2] for event in persons_card))
    # Создание кнопок выбора выбора вида исполнителя
    # Создание клавиатуры с кнопками выбора вида исполнителя
    buttons = [InlineKeyboardButton(text=per, callback_data=f"performers_event_{per}") for per in persons]
    search_button = InlineKeyboardButton(text="Поиск", callback_data=f"performers_search_")
    buttons.append(search_button)
    keyboard = InlineKeyboardMarkup(inline_keyboard=build_menu(buttons, n_cols=2))
    # Отправка сообщения пользователю с клавиатурой выбора вида исполнителя
    await context.bot.send_photo(chat_id=update.message.chat_id, photo=settings.MAIN_WALLPAPERS, caption="Выберите:", reply_markup=keyboard)
    # Сохранение данных персоналий в пользовательскую базу данных бота
    context.user_data["persons_card"] = persons_card

@log_user_action
async def performers_callback(update, context):
    query = update.callback_query
    data = query.data.split("_")
    if data[1] == "event":
        # Получение карточек исполнителей из пользовательских данных
        persons_card = context.user_data.get("persons_card")
        # Фильтрация карточек исполнителей по выбранному типу
        persons = [card for card in persons_card if card[2] == data[2]]
        buttons = [InlineKeyboardButton(text=str(i + 1), callback_data=f"performers_card_{data[2]}_{i}") for i, _ in
                   enumerate(persons)]
        back_button = InlineKeyboardButton(text="назад", callback_data=f"performers_back_")
        buttons.append(back_button)
        keyboard = InlineKeyboardMarkup(inline_keyboard=build_menu(buttons, n_cols=3))
        # Отправка сообщения с номерами исполнителей и кнопкой назад
        text = f"Выберите номер {data[2]}:\n"
        text += "\n".join([f"{i + 1}. {p[0]}" for i, p in enumerate(persons)])
        await context.bot.edit_message_media(chat_id=query.message.chat_id, message_id=query.message.message_id,
                                             media=InputMediaPhoto(settings.MAIN_WALLPAPERS, caption=text),
                                             reply_markup=keyboard)
    elif data[1] == "card":
        # Изменение клавиатуры для карточки исполнителя
        persons_card = context.user_data.get("persons_card")
        persons = [card for card in persons_card if card[2] == data[2]]
        # Вывод картинки, текста и кнопки ссылки на исполнителя
        button = InlineKeyboardButton(text="Ссылка", url=persons[int(data[3])][3])
        back_button = InlineKeyboardButton(text="назад", callback_data=f"performers_event_{data[2]}")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[button, back_button]])

        text = f"{persons[int(data[3])][0]}\n {persons[int(data[3])][1]}\n"
        await context.bot.edit_message_media(chat_id=query.message.chat_id, message_id=query.message.message_id,
                                             media=InputMediaPhoto(persons[int(data[3])][4], caption=text),
                                             reply_markup=keyboard)
    elif data[1] == "search":
        # Создание кнопки назад
        back_button = InlineKeyboardButton(text="назад", callback_data=f"performers_back_")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[back_button]])
        text = "Введите имя исполнителя:"
        await context.bot.edit_message_media(chat_id=query.message.chat_id, message_id=query.message.message_id,
                                             media=InputMediaPhoto(settings.MAIN_WALLPAPERS, caption=text),
                                             reply_markup=keyboard)

        # Добавление функционала для поиска исполнителя по имени
        query = update.callback_query
        context.user_data["search_query"] = True
        context.user_data["search_type"] = "performers"
        context.user_data["search_data"] = {}
        context.user_data["performers_search_state"] = "performers_name"  # устанавливаем состояние поиска

    elif data[1] == "back":
        # Создание кнопок выбора выбора вида исполнителя
        persons_card = context.user_data.get("persons_card")
        persons = list(set(event[2] for event in persons_card))
        # persons.insert(0, "Поиск")
        # Создание кнопок выбора выбора вида исполнителя
        buttons = [InlineKeyboardButton(text=per, callback_data=f"performers_event_{per}") for per in persons]
        search_button = InlineKeyboardButton(text="Поиск", callback_data=f"performers_search_")
        buttons.append(search_button)
        keyboard = InlineKeyboardMarkup(inline_keyboard=build_menu(buttons, n_cols=2))
        # Отправка сообщения пользователю с клавиатурой выбора вида исполнителя
        await context.bot.edit_message_media(chat_id=query.message.chat_id, message_id=query.message.message_id,
                                             media=InputMediaPhoto(settings.MAIN_WALLPAPERS, caption="Выберите:"),
                                             reply_markup=keyboard)
        context.user_data["search_query"] = False

@log_user_action
async def performers_search_name(update, context):
    if context.user_data is not None:
        search_query = context.user_data.get("search_query")
        if search_query is not None:
            if context.user_data["search_query"]:
                # Получение введенного пользователем имени
                search_name = update.message.text

                # Получение карточек исполнителей из пользовательских данных
                persons_card = context.user_data.get("persons_card")

                # Фильтрация карточек исполнителей по имени
                persons = [card for card in persons_card if search_name.lower() in card[0].lower()]

                if not persons:
                    text = "К сожалению, ничего не найдено. Попробуйте ввести другое имя."
                    await update.message.reply_text(text)
                else:
                    for person in persons:
                        # Вывод картинки, текста и кнопки ссылки на исполнителя
                        button = InlineKeyboardButton(text="Ссылка", url=person[3])
                        back_button = InlineKeyboardButton(text="назад", callback_data=f"performers_back_")
                        keyboard = InlineKeyboardMarkup(inline_keyboard=[[button, back_button]])
                        await context.bot.send_photo(chat_id=update.message.chat_id, photo=person[4], caption=person[0],
                                                     reply_markup=keyboard)
                    context.user_data["search_query"] = False
