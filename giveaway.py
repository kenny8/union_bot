from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import random
import settings
import pickle
import logging
import datetime
import calendar
from admin import is_admin
import asyncio
# Включение логгирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# Словарь месяцев с английскими названиями (с большой буквы)
months_dict = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
}


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


async def auto_results(update, context):
    if settings.START_GIVEAWAY['active']:
        settings.START_GIVEAWAY['active'] = False
        winners = int(settings.START_GIVEAWAY['winners'])
        participants = settings.START_GIVEAWAY['participants']
        if not participants:
            result_text = "Участников не было"
        elif len(participants) >= winners:
            winners_list = random.sample(participants, winners)  # Случайный выбор победителей
            result_text = f"Победители ({winners} из {len(participants)}):\n\n"
            for i, winner_id in enumerate(winners_list):
                result_text += rf"{i + 1}. {winner_id['user_html']}"
                result_text += "\n"
        elif len(participants) < winners:
            winners_list = participants  # Случайный выбор победителей
            result_text = f"Победители ({winners} из {len(participants)}):\n\n"
            for i, winner_id in enumerate(winners_list):
                result_text += rf"{i + 1}. {winner_id['user_html']}"
                result_text += "\n"
        else:
            result_text = "Недостаточно участников для определения победителей"

        # Отправка результатов автору и тому, кто завершил конкурс
        author_id = settings.START_GIVEAWAY['author']['user_id']

        await context.bot.send_message(chat_id=author_id, text=f"Результаты розыгрыша:\n\n{result_text}",
                                       parse_mode='HTML')
        # Отправка сообщений участникам о результатах
        text_winner = f"Поздравляем👏👏👏, вы выиграли билет! Чтобы его получить, напишите "
        text_winner += rf"{settings.START_GIVEAWAY['author']['user_html']}"
        text_loser = "Увы, сегодня удача не на вашей стороне🥺, но это только сегодня! Я уверен:" \
                     " в следующий раз вам обязательно повезёт👍"
        for participant_id in participants:
            is_winner = text_winner if participant_id in winners_list else text_loser
            if settings.START_GIVEAWAY['prize'] != "":
                if participant_id in winners_list:
                    await context.bot.send_photo(chat_id=winner_id['user_id'], photo=settings.START_GIVEAWAY['prize'],
                                                 caption=is_winner,
                                                 parse_mode='HTML')
                else:
                    await context.bot.send_message(chat_id=participant_id['user_id'], text=is_winner,
                                                   parse_mode='HTML')
            else:
                await context.bot.send_message(chat_id=participant_id['user_id'], text=is_winner,
                                               parse_mode='HTML')
        with open(settings.GIVEAWAY_TXT, 'wb') as file:
            pickle.dump(settings.START_GIVEAWAY, file)
        logger.info(
            f" Dызвалась функция auto_results. Статус : {result_text}"
        )


async def giveaway(update, context):
    """Отправка сообщения, когда пользователь нажимает на кнопку 'Розыгрыш билетов'."""
    user = update.effective_user
    user_id = user.id
    full_name = user.full_name
    context.user_data["feedback"] = False
    context.user_data["password_edit"] = False
    context.user_data["login"] = False
    context.user_data["picture_edit"] = False
    if is_admin(user_id):
        if settings.START_GIVEAWAY['active'] is False:
            start_button2 = InlineKeyboardButton(text="Начать с 2 фото", callback_data="giveaway_admin_start_0_2")
            start_button1 = InlineKeyboardButton(text="Начать с 1 фото", callback_data="giveaway_admin_start_0_1")
            start_button0 = InlineKeyboardButton(text="Начать без фото", callback_data="giveaway_admin_start_0_0")
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[start_button0], [start_button1], [start_button2]])
            await context.bot.send_message(chat_id=update.message.chat_id,
                                           text="Вы вошли в розыгрыши\n 2 фото это картинка приветвие "
                                                "розыгрыша и картинка что увидит победитель\n "
                                                "1 фото это картинка что увидит победитель\n "
                                                "без фото -пользователи увидят только текст",
                                                reply_markup=keyboard)
            logger.info(
                f"Админ {user.username} /{full_name} вызвал функцию giveaway."
                f" Статус розыгрыша False"
            )
        else:
            if settings.START_GIVEAWAY["auto"]:
                text = f"Вы вошли в розыгрыши\n победители будут объявлены {settings.START_GIVEAWAY['end_date']}" \
                       f" {settings.START_GIVEAWAY['end_time']}" \
                       f" количество победителей: {settings.START_GIVEAWAY['winners']}"
            else:
                text = f"Вы вошли в розыгрыши\n розыгрыш ждет окончания." \
                       f" количество победителей: {settings.START_GIVEAWAY['winners']}"
            stop_button = InlineKeyboardButton(text="Завершить без победителя", callback_data="giveaway_admin_stop_0")
            stop_win_button = InlineKeyboardButton(text="Завершить с победителем",
                                                   callback_data="giveaway_admin_stop_1")
            check_button = InlineKeyboardButton(text="Количество участников", callback_data="giveaway_admin_stop_2")
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[stop_button, stop_win_button], [check_button]])
            await context.bot.send_message(chat_id=update.message.chat_id,
                                           text=text,
                                           reply_markup=keyboard)
            logger.info(
                f"Админ {user.username} /{full_name} вызвал функцию giveaway."
                f"Статус розыгрыша True"
            )
    else:
        if settings.START_GIVEAWAY['active']:
            context.user_data["sub"] = True
            context.user_data["memb1"] = True
            context.user_data["memb2"] = True
            text = settings.START_GIVEAWAY['contest_text']
            start_giveaway_button = InlineKeyboardButton(text="Участвовать", callback_data="giveaway_user_0_0")
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[start_giveaway_button]])
            if settings.START_GIVEAWAY['picture'] != "":
                photo_file_id = settings.START_GIVEAWAY['picture']
                context.user_data["photo_message"] = await context.bot.send_photo(chat_id=update.message.chat_id,
                                                                                  photo=photo_file_id,
                                                                                  caption=text,
                                                                                  reply_markup=keyboard)
            else:

                context.user_data["photo_message"] = await context.bot.send_message(chat_id=update.message.chat_id,
                                                                                    text=text,
                                                                                    reply_markup=keyboard)
            logger.info(
                f"Пользователь {user.username} /{full_name} вызвал функцию giveaway. "
                f"Статус розыгрыша True"
            )
        else:
            await context.bot.send_message(chat_id=update.message.chat_id,
                                           text="Пока нет розыгрышей")
            logger.info(
                f"Пользователь {user.username} /{full_name} вызвал функцию giveaway. "
                f"Статус розыгрыша False"
            )


async def giveaway_callback(update, context):
    query = update.callback_query
    data = query.data.split("_")
    user = update.effective_user
    full_name = user.full_name
    print(query.data)
    if data[1] == "admin":
        if data[2] == "start":
            if data[3] == "back":
                start_button2 = InlineKeyboardButton(text="Начать с 2 фото",
                                                     callback_data="giveaway_admin_start_0_2")
                start_button1 = InlineKeyboardButton(text="Начать с 1 фото",
                                                     callback_data="giveaway_admin_start_0_1")
                start_button0 = InlineKeyboardButton(text="Начать без фото",
                                                     callback_data="giveaway_admin_start_0_0")
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[start_button0], [start_button1], [start_button2]])
                await context.bot.edit_message_text(chat_id=query.message.chat_id,
                                                    message_id=query.message.message_id,
                                                    text="Вы вошли в розыгрыши\n 2 фото это картинка приветвие "
                                                         "розыгрыша и картинка что увидит победитель\n "
                                                         "1 фото это картинка что увидит победитель\n "
                                                         "без фото -пользователи увидят только текст",
                                                    reply_markup=keyboard)
                logger.info(
                    f"Админ {user.username} /{full_name} вызвал функцию giveaway_callback. "
                    f"Статус giveaway_admin_start_back"
                )
            elif data[3] == "0":
                context.user_data["giveaway_photo_start"] = []
                context.user_data["giveaway_photo_numb"] = int(data[4])
                text = f"Введите текст розыгрыша и вместе отправте с {int(data[4])} фото"
                if int(data[4]) == 2:
                    text += "\n 1 фото это приветствие, 2 фото - приз"
                start_giveaway_button = InlineKeyboardButton(text="Назад", callback_data="giveaway_admin_start_back")
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[start_giveaway_button]])
                await context.bot.edit_message_text(chat_id=query.message.chat_id,
                                                    message_id=query.message.message_id,
                                                    text=text,
                                                    reply_markup=keyboard)
                context.user_data["giveaway_Text_start"] = True
                logger.info(
                    f"Админ {user.username} /{full_name} вызвал функцию giveaway_callback. "
                    f"Статус giveaway_admin_start_0_{int(data[4])}"
                )
            elif data[3] == "1":
                text = "Выберите месяц"
                back_giveaway_button = InlineKeyboardButton(text="Назад", callback_data="giveaway_admin_start_0")
                months = [
                    "Январь", "Февраль", "Март", "Апрель",
                    "Май", "Июнь", "Июль", "Август",
                    "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
                ]
                buttons = [InlineKeyboardButton(month, callback_data=f"giveaway_admin_start_month_{index + 1}")
                           for index, month in
                           enumerate(months)]
                keyboard = build_menu(buttons, n_cols=3, footer_buttons=[back_giveaway_button])
                markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
                await context.bot.edit_message_text(chat_id=query.message.chat_id,
                                                    message_id=query.message.message_id,
                                                    text=text,
                                                    reply_markup=markup)
                logger.info(
                    f"Админ {user.username} /{full_name} вызвал функцию giveaway_callback. "
                    f"Статус giveaway_admin_start_1"
                )
            elif data[3] == "month":
                back_month_button = InlineKeyboardButton(text="Назад", callback_data="giveaway_admin_start_1")
                year = datetime.datetime.now().year
                month = int(data[4])
                today = datetime.datetime.now()

                # Если месяц уже прошел в этом году, берем следующий год
                if month < today.month:
                    year += 1

                days_in_month = calendar.monthrange(year, month)[1]
                text = f"Выберите день месяца '{months_dict[month]}'"
                days_buttons = []
                print(year)
                # Добавляем кнопки для дней месяца и их дней недели
                for day in range(1, days_in_month + 1):
                    day_date = datetime.date(year, month, day)
                    day_name = day_date.strftime("%d")
                    days_buttons.append(
                        InlineKeyboardButton(day_name, callback_data=f"giveaway_admin_start_day_{year}_{month}_{day}")
                    )

                keyboard = build_menu(days_buttons, n_cols=7, footer_buttons=[back_month_button])
                markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
                await context.bot.edit_message_text(chat_id=query.message.chat_id,
                                                    message_id=query.message.message_id,
                                                    text=text,
                                                    reply_markup=markup)
                logger.info(
                    f"Админ {user.username} /{full_name} вызвал функцию giveaway_callback. "
                    f"Статус giveaway_admin_start_month_{month}"
                )
            elif data[3] == "day":

                year = int(data[4])
                month = int(data[5])
                day = int(data[6])
                back_day_button = InlineKeyboardButton(text="Назад",
                                                       callback_data=f"giveaway_admin_start_month_{month}")
                hours_buttons = [
                    InlineKeyboardButton(str(hour), callback_data=f"giveaway_admin_start_hour_"
                                                                  f"{year}_{month}_{day}_{hour}")
                    for hour in range(24)
                ]
                text = f"Выберите час для {day}.{month}.{year}"
                keyboard = build_menu(hours_buttons, n_cols=6, footer_buttons=[back_day_button])
                markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
                await context.bot.edit_message_text(chat_id=query.message.chat_id,
                                                    message_id=query.message.message_id,
                                                    text=text,
                                                    reply_markup=markup)
                logger.info(
                    f"Админ {user.username} /{full_name} вызвал функцию giveaway_callback. "
                    f"Статус giveaway_admin_start_day_{year}_{month}_{day}"
                )
            elif data[3] == "hour":
                year = int(data[4])
                month = int(data[5])
                day = int(data[6])
                hour = int(data[7])
                back_hour_button = InlineKeyboardButton(text="Назад",
                                                        callback_data=f"giveaway_admin_start_day_{year}_{month}_{day}")
                winners_buttons = [
                    InlineKeyboardButton(str(i),
                                         callback_data=f"giveaway_admin_start_winners_{i}")
                    for i in range(1, 11)  # От 1 до 10 победителей
                ]
                text = f"Выберите количество победителей для {day}.{month}.{year} {hour}:00"

                # Сохраняем дату и время в START_GIVEAWAY
                end_date = datetime.date(year, month, day)
                end_time = f"{hour}:00"
                settings.START_GIVEAWAY['end_date'] = end_date.strftime("%Y-%m-%d")
                settings.START_GIVEAWAY['end_time'] = end_time
                settings.START_GIVEAWAY['auto'] = True

                keyboard = build_menu(winners_buttons, n_cols=5, footer_buttons=[back_hour_button])
                markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
                await context.bot.edit_message_text(chat_id=query.message.chat_id,
                                                    message_id=query.message.message_id,
                                                    text=text,
                                                    reply_markup=markup)
                logger.info(
                    f"Админ {user.username} /{full_name} вызвал функцию giveaway_callback. "
                    f"Статус giveaway_admin_start_hour_{year}_{month}_{day}_{hour}"
                )
            elif data[3] == "win":
                back_hour_button = InlineKeyboardButton(text="Назад",
                                                        callback_data=f"giveaway_admin_start_0")
                winners_buttons = [
                    InlineKeyboardButton(str(i),
                                         callback_data=f"giveaway_admin_start_winners_{i}")
                    for i in range(1, 11)  # От 1 до 10 победителей
                ]
                text = f"Выберите количество победителей"
                settings.START_GIVEAWAY['auto'] = False

                keyboard = build_menu(winners_buttons, n_cols=5, footer_buttons=[back_hour_button])
                markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
                await context.bot.edit_message_text(chat_id=query.message.chat_id,
                                                    message_id=query.message.message_id,
                                                    text=text,
                                                    reply_markup=markup)
                logger.info(
                    f"Админ {user.username} /{full_name} вызвал функцию giveaway_callback. "
                    f"Статус giveaway_admin_start_win"
                )
            elif data[3] == "winners":
                winners = int(data[4])
                settings.START_GIVEAWAY['winners'] = winners
                text1 = f"Появился новый розыгрыш"
                text = "Розыгрыш начат\n"
                text += f"Выбрано количество победителей: {winners}\n"
                await context.bot.edit_message_text(chat_id=query.message.chat_id,
                                                    message_id=query.message.message_id,
                                                    text=text)
                settings.START_GIVEAWAY['active'] = True
                for participant in settings.USERS:
                    if participant[1] != update.effective_chat.id:
                        await context.bot.send_message(chat_id=participant[1], text=text1)

                end_date = settings.START_GIVEAWAY.get('end_date')
                end_time = settings.START_GIVEAWAY.get('end_time')

                if end_date and end_time:
                    end_datetime = datetime.datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")

                    async def schedule_text_rea():
                        await asyncio.sleep((end_datetime - datetime.datetime.now()).total_seconds())
                        await auto_results(update, context)

                    loop = asyncio.get_event_loop()  # Получаем цикл событий
                    loop.create_task(schedule_text_rea())  # Создаем задачу и запускаем параллельно

                with open(settings.GIVEAWAY_TXT, 'wb') as file:
                    pickle.dump(settings.START_GIVEAWAY, file)
                logger.info(
                    f"Админ {user.username} /{full_name} вызвал функцию giveaway_callback. "
                    f"Статус giveaway_admin_start_winners_{winners}"
                )
        elif data[2] == "stop":
            if data[3] == "0":
                settings.START_GIVEAWAY['active'] = False
                text = "Розыгрыш закончен по техническим причинам"
                await context.bot.edit_message_text(chat_id=query.message.chat_id,
                                                    message_id=query.message.message_id,
                                                    text=text)
                text_stop = "Розыгрыш закончен по техническим причинам"
                for participant in settings.START_GIVEAWAY['participants']:
                    text = text_stop
                    await context.bot.send_message(chat_id=participant['user_id'], text=text)
                with open(settings.GIVEAWAY_TXT, 'wb') as file:
                    pickle.dump(settings.START_GIVEAWAY, file)
                logger.info(
                    f"Админ {user.username} /{full_name} вызвал функцию giveaway_callback. "
                    f"Статус giveaway_admin_stop_0"
                )
            elif data[3] == "1":
                settings.START_GIVEAWAY['active'] = False
                winners = int(settings.START_GIVEAWAY['winners'])
                participants = settings.START_GIVEAWAY['participants']

                if not participants:
                    result_text = "Участников не было"
                elif len(participants) >= winners:
                    winners_list = random.sample(participants, winners)  # Случайный выбор победителей
                    result_text = f"Победители ({winners} из {len(participants)}):\n\n"
                    for i, winner_id in enumerate(winners_list):
                        result_text += rf"{i + 1}. {winner_id['user_html']}"
                        result_text += "\n"
                elif len(participants) < winners:
                    winners_list = participants  # Случайный выбор победителей
                    result_text = f"Победители ({winners} из {len(participants)}):\n\n"
                    for i, winner_id in enumerate(winners_list):
                        result_text += rf"{i + 1}. {winner_id['user_html']}"
                        result_text += "\n"
                else:
                    result_text = "Недостаточно участников для определения победителей"

                # Отправка результатов автору и тому, кто завершил конкурс
                author_id = settings.START_GIVEAWAY['author']['user_id']

                await context.bot.send_message(chat_id=author_id, text=f"Результаты розыгрыша:\n\n{result_text}",
                                               parse_mode='HTML')
                await context.bot.edit_message_text(chat_id=query.message.chat_id,
                                                    message_id=query.message.message_id,
                                                    text=f"Результаты розыгрыша:\n\n{result_text}",
                                                    parse_mode='HTML')
                # Отправка сообщений участникам о результатах
                text_winner = f"Поздравляем👏👏👏, вы выиграли билет! Чтобы его получить, напишите "
                text_winner += rf"{settings.START_GIVEAWAY['author']['user_html']}"
                text_loser = "Увы, сегодня удача не на вашей стороне🥺, но это только сегодня!" \
                             " Я уверен: в следующий раз вам обязательно повезёт👍"
                for participant_id in participants:
                    is_winner = text_winner if participant_id in winners_list else text_loser
                    if settings.START_GIVEAWAY['prize'] != "":
                        if participant_id in winners_list:
                            await context.bot.send_photo(chat_id=winner_id['user_id'],
                                                         photo=settings.START_GIVEAWAY['prize'],
                                                         caption=is_winner,
                                                         parse_mode='HTML')
                        else:
                            await context.bot.send_message(chat_id=participant_id['user_id'],
                                                           text=is_winner,
                                                           parse_mode='HTML')
                    else:
                        await context.bot.send_message(chat_id=participant_id['user_id'],
                                                       text=is_winner,
                                                       parse_mode='HTML')
                with open(settings.GIVEAWAY_TXT, 'wb') as file:
                    pickle.dump(settings.START_GIVEAWAY, file)
                logger.info(
                    f"Админ {user.username} /{full_name} вызвал функцию giveaway_callback. "
                    f"Статус giveaway_admin_stop_1"
                )

            elif data[3] == "2":
                text = f"Количество участников: {len(settings.START_GIVEAWAY['participants'])}"
                start_giveaway_button = InlineKeyboardButton(text="Назад", callback_data="giveaway_back_")
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[start_giveaway_button]])
                await context.bot.edit_message_text(chat_id=query.message.chat_id,
                                                    message_id=query.message.message_id,
                                                    text=text,
                                                    reply_markup=keyboard)
            logger.info(
                f"Админ {user.username} /{full_name} вызвал функцию giveaway_callback. "
                f"Статус giveaway_admin_stop_2"
            )

    elif data[1] == "user":
        if context.user_data["photo_message"] is not None:
            await context.bot.delete_message(chat_id=query.message.chat_id,
                                             message_id=context.user_data["photo_message"].message_id)
            context.user_data["photo_message"] = None
        if data[2] == "0":
            user = update.effective_user
            user_id = user.id
            chat_id = update.effective_chat.id

            user_status = await context.bot.get_chat_member(chat_id='@' + settings.CHAT, user_id=user_id)
            if user_status.status in ['member', 'creator', 'administrator']:
                full_name = user.full_name
                username = user.username

                if user_id not in [user_['user_id'] for user_ in settings.START_GIVEAWAY['participants']]:
                    if context.user_data["memb1"] is None or context.user_data["sub"] is None:
                        await context.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=query.message.message_id,
                            text='Вы присоединились к розыгрышу.')
                    else:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text='Вы присоединились к розыгрышу.')
                        context.user_data["memb1"] = None
                    participant = {
                        'username': username,
                        'chat_id': chat_id,
                        'full_name': full_name,
                        'user_id': user_id,
                        'user_html': user.mention_html(),
                    }
                    settings.START_GIVEAWAY['participants'].append(participant)
                    with open(settings.GIVEAWAY_TXT, 'wb') as file:
                        pickle.dump(settings.START_GIVEAWAY, file)
                    logger.info(
                        f"Пользователь {user.username} /{full_name} вызвал функцию giveaway_callback. "
                        f"Статус giveaway_user_0 - присоединились к розыгрышу"
                    )
                else:
                    if context.user_data["memb2"] is None or context.user_data["memb1"] is None or \
                            context.user_data["sub"] is None:
                        await context.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=query.message.message_id,
                            text='Вы уже участвуете.')
                    else:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text='Вы уже участвуете.')
                        context.user_data["memb2"] = None
                    logger.info(
                        f"Пользователь {user.username} /{full_name} вызвал функцию giveaway_callback. "
                        f"Статус giveaway_user_0 - уже участвует"
                    )
            else:
                if data[3] == "1":
                    text = f"Извините, но вы не подписались. Подпишитесь на канал t.me/{settings.CHAT}, " \
                           f"чтобы принять участие в розыгрыше."
                    check_button = InlineKeyboardButton(text="Проверить", callback_data=f"giveaway_user_0_2")
                else:
                    text = f"Пожалуйста, подпишитесь на канал t.me/{settings.CHAT}, чтобы принять участие в розыгрыше."
                    check_button = InlineKeyboardButton(text="Проверить", callback_data=f"giveaway_user_0_1")
                community_button = InlineKeyboardButton(text="Подписаться", url=f"t.me/{settings.CHAT}")
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[community_button, check_button]])
                if data[3] != "2":
                    if context.user_data["sub"] is None:
                        await context.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=query.message.message_id,
                            text=text,
                            reply_markup=keyboard)
                    else:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=text,
                            reply_markup=keyboard)
                        context.user_data["sub"] = None
                logger.info(
                    f"Пользователь {user.username} /{full_name} вызвал функцию giveaway_callback. "
                    f"Статус giveaway_user_0 - подписывается на канал"
                )
    if data[1] == "back":
        user = update.effective_user
        user_id = user.id
        if is_admin(user_id):
            stop_button = InlineKeyboardButton(text="завершить без победителя",
                                               callback_data=f"giveaway_admin_stop_0")
            stop_win_button = InlineKeyboardButton(text="завершить с победителим",
                                                   callback_data=f"giveaway_admin_stop_1")
            check_button = InlineKeyboardButton(text="кол-во участников",
                                                callback_data=f"giveaway_admin_stop_2")
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[stop_button, stop_win_button], [check_button]])
            await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text="вы вошли в розыгрыши",
                reply_markup=keyboard)
            logger.info(
                f"Админ {user.username} /{full_name} вызвал функцию giveaway_callback. "
                f"Статус giveaway_back"
            )


async def giveaway_text(update, context):
    if context.user_data is not None:
        search_query = context.user_data.get("giveaway_Text_start")
        if search_query is not None:
            if context.user_data["giveaway_Text_start"]:
                user = update.effective_user
                text_admin = update.message.text
                full_name = user.full_name
                if text_admin is None:
                    text_admin = update.message.caption

                message = update.effective_message
                if message.photo:  # Если сообщение содержит фото
                    photos = message.photo
                    context.user_data["giveaway_photo_start"].append(photos[-1].file_id)

                if len(context.user_data["giveaway_photo_start"]) == 1:
                    context.user_data["giveaway_text_context"] = text_admin
                    print(context.user_data["giveaway_text_context"])
                elif len(context.user_data["giveaway_photo_start"]) == 2:
                    text_admin = context.user_data["giveaway_text_context"]

                if len(context.user_data["giveaway_photo_start"]) == context.user_data["giveaway_photo_numb"] or \
                        context.user_data["giveaway_photo_numb"] == 0 and \
                        len(context.user_data["giveaway_photo_start"]) >= 1:
                    settings.START_GIVEAWAY['picture'] = ""
                    settings.START_GIVEAWAY['prize'] = ""
                    photo = context.user_data["giveaway_photo_start"]
                    if context.user_data["giveaway_photo_numb"] == 0 and \
                            len(context.user_data["giveaway_photo_start"]) >= 1:
                        pass
                    else:
                        if len(photo) == 2:
                            # Записываем первую фотографию в ключ 'picture'
                            settings.START_GIVEAWAY['picture'] = photo[0]
                            # Записываем вторую фотографию в ключ 'prize'
                            settings.START_GIVEAWAY['prize'] = photo[1]
                        elif len(photo) == 1:
                            # Записываем первую фотографию в ключ 'prize'
                            settings.START_GIVEAWAY['prize'] = photo[0]

                    if text_admin:
                        text = f"Розыгрыш начат\nТекст: {text_admin}"
                    else:
                        text = "Розыгрыш начат"

                    date_giveaway_button = InlineKeyboardButton(text="выбрать дату",
                                                                callback_data="giveaway_admin_start_1")
                    not_date_giveaway_button = InlineKeyboardButton(text="без даты",
                                                                    callback_data="giveaway_admin_start_win")
                    self_giveaway_button = InlineKeyboardButton(text="исправить",
                                                                callback_data="giveaway_admin_start_back")
                    keyboard = InlineKeyboardMarkup(
                        inline_keyboard=[[date_giveaway_button, not_date_giveaway_button], [self_giveaway_button]])
                    if settings.START_GIVEAWAY['picture'] != "":
                        photo_file_id = settings.START_GIVEAWAY['picture']
                        await context.bot.send_photo(chat_id=update.message.chat_id,
                                                     photo=photo_file_id,
                                                     caption="заставка")
                    if settings.START_GIVEAWAY['prize'] != "":
                        photo_file_id = settings.START_GIVEAWAY['prize']
                        await context.bot.send_photo(chat_id=update.message.chat_id,
                                                     photo=photo_file_id,
                                                     caption="приз")
                    await context.bot.send_message(chat_id=update.message.chat_id,
                                                   text=text,
                                                   reply_markup=keyboard)
                    context.user_data["giveaway_Text_start"] = False

                    settings.START_GIVEAWAY['active'] = False
                    settings.START_GIVEAWAY['contest_text'] = text_admin
                    settings.START_GIVEAWAY['author'] = {
                        'user_id': user.id,
                        'full_name': user.full_name,
                        'username': user.username,
                        'user_html': user.mention_html(),
                        'chat_id': update.effective_chat.id
                    }

                    settings.START_GIVEAWAY['participants'] = []
                    settings.START_GIVEAWAY['auto'] = False
                    logger.info(
                        f"Админ {user.username} /{full_name} вызвал функцию giveaway_text. "
                        f"Статус загрузил текст/фото розыгрыша"
                    )
