import settings
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import InputMediaPhoto
from datetime import datetime
from json_parser import json_afisha_
import textwrap
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
        full_name = user.full_name
        user = update.effective_user
        logger.info(f"Пользователь {user.username}/{full_name} вызвал функцию {func.__name__}")
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
async def afisha(update, context):
    # Отправка сообщения, когда пользователь нажимает на кнопку 'Афиша'.
    # Получаем текущее время
    context.user_data["feedback"] = False
    context.user_data["password_edit"] = False
    context.user_data["login"] = False
    context.user_data["picture_edit"] = False
    now = datetime.now()
    time_diff = now - settings.AFISHA_CARD_TIME
    hours_diff = time_diff.seconds // 3600
    if hours_diff >= 12:
        print("обновились афиши")
        settings.AFISHA_CARD = json_afisha_()
        settings.AFISHA_CARD_TIME = now
    afisha_card = settings.AFISHA_CARD  # загрузка json
    if len(afisha_card["ticket"]) == 0:
        # Отправка сообщения пользователю с клавиатурой выбора даты концерта
        await context.bot.send_photo(chat_id=update.message.chat_id, photo=settings.END_WALLPAPERS,
                                     caption="пока концертов нету, но они обязательно появятся")
    elif len(afisha_card["subscription"]) == 0:
        # Получение списка событий только с билетами
        ticket_events = [event for event in afisha_card["ticket"]]
        # Создание кнопок выбора билетов по времени, но обработка по ID
        buttons = [InlineKeyboardButton(text=event['time_start'][0][0],
                                        callback_data=f"afisha_event_{event['id']}")
                   for event in ticket_events]
        keyboard = InlineKeyboardMarkup(inline_keyboard=build_menu(buttons, n_cols=2))
        # Отправка сообщения пользователю с клавиатурой выбора билетов по времени
        await context.bot.send_photo(chat_id=update.message.chat_id, photo=settings.MAIN_WALLPAPERS,
                                     caption="Выберите билет", reply_markup=keyboard)

        # Сохранение данных афиши в пользовательскую базу данных бота
        context.user_data["afisha_card_ticket"] = ticket_events
    else:
        ticket_button = InlineKeyboardButton(text="билеты", callback_data=f"afisha_ticket")
        subscription_button = InlineKeyboardButton(text="абонемент", callback_data=f"afisha_subscription")

        keyboard = [[ticket_button, subscription_button]]
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        await context.bot.send_photo(chat_id=update.message.chat_id, photo=settings.MAIN_WALLPAPERS,
                                     caption="Выберите", reply_markup=markup)
        # Сохранение данных афиши в пользовательскую базу данных бота
        context.user_data["afisha_card"] = afisha_card


async def afisha_callback(update, context):
    query = update.callback_query
    #await query.answer()
    context.user_data["feedback"] = False
    data = query.data.split("_")
    user = update.effective_user
    full_name = user.full_name
    try:
        if data[1] == "backSUB":
            ticket_button = InlineKeyboardButton(text="билеты", callback_data=f"afisha_ticket")
            subscription_button = InlineKeyboardButton(text="абонемент", callback_data=f"afisha_subscription")

            keyboard = [[ticket_button, subscription_button]]
            markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
            await context.bot.edit_message_caption(chat_id=query.message.chat_id,
                                                   message_id=query.message.message_id,
                                                   caption="Выберите",
                                                   reply_markup=markup)
            logger.info(
                f"Пользователь {user.username} /{full_name} вызвал функцию afisha_callback. "
                f"Статус afisha_backSUB"
            )
        elif data[1] == "ticket":
            # Получение списка событий только с билетами
            ticket_events = [event for event in context.user_data["afisha_card"]["ticket"]]

            if len(ticket_events) == 0:
                # Отправка сообщения пользователю с клавиатурой выбора даты концерта
                await context.bot.send_photo(chat_id=update.message.chat_id, photo=settings.END_WALLPAPERS,
                                             caption="пока концертов нету, но они обязательно появятся")
            else:
                # Создание кнопок выбора билетов по времени, но обработка по ID
                buttons = [InlineKeyboardButton(text=event['time_start'][0][0],
                                                callback_data=f"afisha_event_{event['id']}")
                           for event in ticket_events]
                back_button = InlineKeyboardButton(text="назад", callback_data="afisha_backSUB")
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=build_menu(buttons, n_cols=2, footer_buttons=[back_button]))
                # Отправка сообщения пользователю с клавиатурой выбора билетов по времени
                await context.bot.edit_message_caption(chat_id=query.message.chat_id,
                                                       message_id=query.message.message_id,
                                                       caption=f"Выберите билет",
                                                       reply_markup=keyboard)
            # Сохранение данных афиши в пользовательскую базу данных бота
            context.user_data["afisha_card_ticket"] = ticket_events
            logger.info(
                f"Пользователь {user.username} /{full_name} вызвал функцию afisha_callback. "
                f"Статус afisha_ticket"
            )
        elif data[1] == "subscription":
            # Получение списка событий только с билетами
            subscription_events = [event for event in context.user_data["afisha_card"]["subscription"]]
            # Создание кнопок выбора билетов по времени, но обработка по ID
            buttons = [InlineKeyboardButton(text=event['title'],
                                            callback_data=f"afisha_event_{event['id']}")
                       for event in subscription_events]
            back_button = InlineKeyboardButton(text="назад", callback_data="afisha_backSUB")
            keyboard = InlineKeyboardMarkup(inline_keyboard=build_menu(buttons, n_cols=2, footer_buttons=[back_button]))
            # Отправка сообщения пользователю с клавиатурой выбора билетов по времени
            await context.bot.edit_message_caption(chat_id=query.message.chat_id,
                                                   message_id=query.message.message_id,
                                                   caption=f"Выберите абонемент",
                                                   reply_markup=keyboard)
            # Сохранение данных афиши в пользовательскую базу данных бота
            context.user_data["afisha_card_ticket"] = subscription_events
            logger.info(
                f"Пользователь {user.username} /{full_name} вызвал функцию afisha_callback. "
                f"Статус afisha_subscription"
            )
        elif data[1] == "event":
            event_id = int(data[2])  # Получаем id события из callback_data
            selected_event = next((event for event in context.user_data["afisha_card_ticket"]
                                   if event['id'] == event_id), None)

            buy_button = InlineKeyboardButton(text="Купить билет", url=selected_event['ticket'])
            more_info_button = InlineKeyboardButton(text="Подробнее",
                                                    callback_data=f"afisha_more_0_{selected_event['id']}")
            prev_button = InlineKeyboardButton(text="<", callback_data=f"afisha_prev_{selected_event['id']}")
            next_button = InlineKeyboardButton(text=">", callback_data=f"afisha_next_{selected_event['id']}")

            keyboard = [[buy_button, more_info_button], [prev_button, next_button]]
            if len(context.user_data["afisha_card_ticket"]) == 1:
                keyboard[1].remove(prev_button)
                keyboard[1].remove(next_button)
            elif event_id == 1:
                keyboard[1].remove(prev_button)
            elif event_id == len(context.user_data["afisha_card_ticket"]):
                keyboard[1].remove(next_button)
            markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
            text = f""
            await context.bot.edit_message_media(chat_id=query.message.chat_id, message_id=query.message.message_id,
                                                 media=InputMediaPhoto(selected_event['banner'], caption=text),
                                                 reply_markup=markup)
            logger.info(
                f"Пользователь {user.username} /{full_name} вызвал функцию afisha_callback. "
                f"Статус afisha_event_{selected_event['id']}"
            )
        elif data[1] == "prev":
            event_id = int(data[2]) - 1  # Получаем id события из callback_data
            selected_event = next(
                (event for event in context.user_data["afisha_card_ticket"] if event['id'] == event_id),
                None)

            buy_button = InlineKeyboardButton(text="Купить билет", url=selected_event['ticket'])
            more_info_button = InlineKeyboardButton(text="Подробнее",
                                                    callback_data=f"afisha_more_0_{selected_event['id']}")
            prev_button = InlineKeyboardButton(text="<", callback_data=f"afisha_prev_{selected_event['id']}")
            next_button = InlineKeyboardButton(text=">", callback_data=f"afisha_next_{selected_event['id']}")

            keyboard = [[buy_button, more_info_button], [prev_button, next_button]]
            if event_id == 1:
                keyboard[1].remove(prev_button)
            elif event_id == len(context.user_data["afisha_card_ticket"]):
                keyboard[1].remove(next_button)
            markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
            text = f""
            await context.bot.edit_message_media(chat_id=query.message.chat_id, message_id=query.message.message_id,
                                                 media=InputMediaPhoto(selected_event['banner'], caption=text),
                                                 reply_markup=markup)
            logger.info(
                f"Пользователь {user.username} /{full_name} вызвал функцию afisha_callback. "
                f"Статус afisha_prev_{selected_event['id'] - 1}"
            )
        elif data[1] == "next":
            event_id = int(data[2]) + 1  # Получаем id события из callback_data
            selected_event = next(
                (event for event in context.user_data["afisha_card_ticket"] if event['id'] == event_id),
                None)

            buy_button = InlineKeyboardButton(text="Купить билет", url=selected_event['ticket'])
            more_info_button = InlineKeyboardButton(text="Подробнее",
                                                    callback_data=f"afisha_more_0_{selected_event['id']}")
            prev_button = InlineKeyboardButton(text="<", callback_data=f"afisha_prev_{selected_event['id']}")
            next_button = InlineKeyboardButton(text=">", callback_data=f"afisha_next_{selected_event['id']}")

            keyboard = [[buy_button, more_info_button], [prev_button, next_button]]
            if event_id == 1:
                keyboard[1].remove(prev_button)
            elif event_id == len(context.user_data["afisha_card_ticket"]):
                keyboard[1].remove(next_button)
            markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
            text = f""
            await context.bot.edit_message_media(chat_id=query.message.chat_id, message_id=query.message.message_id,
                                                 media=InputMediaPhoto(selected_event['banner'], caption=text),
                                                 reply_markup=markup)
            logger.info(
                f"Пользователь {user.username} /{full_name} вызвал функцию afisha_callback. "
                f"Статус afisha_next_{selected_event['id'] - 1}"
            )
        elif data[1] == "more":
            event_id = int(data[3])
            part_number = int(data[2])
            selected_event = next(
                (event for event in context.user_data["afisha_card_ticket"] if event['id'] == event_id),
                None)

            buy_button = InlineKeyboardButton(text="Купить билет", url=selected_event['ticket'])
            prev_button = InlineKeyboardButton(text="<", callback_data=f"afisha_prev_{selected_event['id']}")
            next_button = InlineKeyboardButton(text=">", callback_data=f"afisha_next_{selected_event['id']}")
            more_info_button = InlineKeyboardButton(text="Дальше",
                                                    callback_data=f"afisha_more_{part_number + 1}_{selected_event['id']}")
            keyboard = [[buy_button, more_info_button], [prev_button, next_button]]

            # Split the event text into parts based on MAX_MESSAGE_LENGTH using textwrap.wrap()
            txt_parts = textwrap.wrap(selected_event['txt'], width=settings.MAX_MESSAGE_LENGTH)

            if 0 <= part_number < len(txt_parts):
                text = txt_parts[part_number]

            if part_number == len(txt_parts) - 1:
                keyboard[0].remove(more_info_button)
                await query.answer("Конец")

            # Update keyboard based on part_number and event_id
            if len(context.user_data["afisha_card_ticket"]) == 1:
                keyboard[1].remove(prev_button)
                keyboard[1].remove(next_button)
            elif event_id == 1:
                keyboard[1].remove(prev_button)
            elif event_id == len(context.user_data["afisha_card_ticket"]):
                keyboard[1].remove(next_button)

            markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

            await context.bot.edit_message_media(chat_id=query.message.chat_id, message_id=query.message.message_id,
                                                 media=InputMediaPhoto(selected_event['banner'], caption=text),
                                                 reply_markup=markup)
            logger.info(
                f"Пользователь {user.username} /{full_name} вызвал функцию afisha_callback. "
                f"Статус afisha_more_{part_number}_{selected_event['id']}"
            )
    except KeyError as e:
        await query.answer("Сообщение устарело")
        logger.info(
            f"Пользователь {user.username} /{full_name} вызвал функцию afisha_callback. "
            f"Статус Сообщение устарело"
        )
    except ValueError as e:
        await query.answer("Сообщение устарело")
        logger.info(
            f"Пользователь {user.username} /{full_name} вызвал функцию afisha_callback. "
            f"Статус Сообщение устарело"
        )
