import logging
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
import settings
import pickle
# Включение логгирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def admin(update, context):
    """Отправка сообщения, когда пользователь нажимает на кнопку для входа в админку."""

    if context.user_data is not None:
        search_query = context.user_data.get("login")
        if search_query is not None:
            if context.user_data["login"]:
                user = update.effective_user
                # Получение введенного пользователем имени
                if settings.PASSWORD == update.message.text:
                    context.user_data["password_edit"] = False
                    context.user_data["feedback"] = False
                    context.user_data["picture_edit"] = False
                    reply_keyboard = ReplyKeyboardMarkup(
                        [["Афиша", "Розыгрыш билетов"], ["Обратная связь", "Настройки", "Выход"]],
                        resize_keyboard=True,
                    )
                    user_id = user.id
                    admin_username = "@" + str(user.username)
                    full_name = user.full_name

                    user_dict = next(
                        (user_dict for user_dict in settings.ADMIN_STATUS if user_dict.get("user_id") == user_id), None)

                    if user_dict is None:
                        settings.ADMIN_STATUS.append({
                            "user_id": user_id,
                            "username": admin_username,
                            "is_admin": True,
                            "full_name": full_name,
                            'user_html': user.mention_html(),
                        })
                    else:
                        user_dict["is_admin"] = True
                        user_dict["username"] = admin_username
                        user_dict["full_name"] = full_name
                        user_dict["user_html"]: user.mention_html()

                    with open(settings.ADMIN_TXT, 'wb') as file:
                        pickle.dump(settings.ADMIN_STATUS, file)

                    await context.bot.send_message(
                        chat_id=update.message.chat_id,
                        text=f"вы вошли в админку\nинтересный факт, столько пользователей "
                             f"пользуются ботом: {len(settings.USERS)}",
                        reply_markup=reply_keyboard
                    )

                    logger.info(
                        f"Пользователь {user.username} /{full_name} вызвал функцию admin. Статус админа: True"
                    )
                    context.user_data["login"] = False
                else:
                    await context.bot.send_message(
                        chat_id=update.message.chat_id,
                        text=f"пароль не верен"
                    )
                    context.user_data["login"] = False
                    user = update.effective_user
                    full_name = user.full_name
                    logger.info(
                        f"Пользователь {user.username} /{full_name} вызвал функцию admin. Статус админа:"
                        f" False. Статус ошибся паролем"
                    )


async def admin_out(update, context):
    context.user_data["password_edit"] = False
    context.user_data["picture_edit"] = False
    user = update.effective_user
    user_id = user.id
    if any(user_dict.get("user_id") == user_id for user_dict in settings.ADMIN_STATUS):
        reply_keyboard = ReplyKeyboardMarkup(
            [["Афиша", "Розыгрыш билетов"], ["Обратная связь"]],
            resize_keyboard=True,
        )
        for user_dict in settings.ADMIN_STATUS:
            if user_dict["user_id"] == user_id:
                user_dict["is_admin"] = False
                break

        with open(settings.ADMIN_TXT, 'wb') as file:
            pickle.dump(settings.ADMIN_STATUS, file)

        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text="вы вышли из админки",
            reply_markup=reply_keyboard
        )
        full_name = user.full_name
        logger.info(
            f"Пользователь {user.username} /{full_name} вызвал функцию admin_out. Статус админа: False"
        )


def is_admin(user_id):
    for user_dict in settings.ADMIN_STATUS:
        if user_dict["user_id"] == user_id and user_dict["is_admin"]:
            return True
    return False


async def settings_edit(update, context):
    context.user_data["picture_edit"] = False
    user = update.effective_user
    user_id = user.id
    if is_admin(user_id):
        edit_password_button = InlineKeyboardButton(text="Изменить пароль", callback_data="settings_password")
        edit_pick_button = InlineKeyboardButton(text="Изменить картинки", callback_data="settings_picture_0")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[edit_password_button], [edit_pick_button]])
        await context.bot.send_message(chat_id=update.message.chat_id,
                                       text="Вы вошли в настройки",
                                       reply_markup=keyboard)
        user = update.effective_user
        full_name = user.full_name
        logger.info(
            f"Пользователь {update.effective_user.username} /{full_name} вызвал функцию settings_edit")


async def settings_callback(update, context):
    query = update.callback_query
    await query.answer()
    context.user_data["feedback"] = False
    context.user_data["password_edit"] = False
    data = query.data.split("_")
    user = update.effective_user
    full_name = user.full_name
    if data[1] == "back":
        edit_password_button = InlineKeyboardButton(text="Изменить пароль", callback_data="settings_password")
        edit_pick_button = InlineKeyboardButton(text="Изменить картинки", callback_data="settings_picture_0")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[edit_password_button], [edit_pick_button]])
        await context.bot.edit_message_text(chat_id=query.message.chat_id,
                                            message_id=query.message.message_id,
                                            text="Вы вошли в настройки",
                                            reply_markup=keyboard)
        logger.info(
            f"Пользователь {update.effective_user.username} /{full_name} вызвал функцию settings_edit. "
            f"Статус: вернуля в настройки")
    elif data[1] == "password":
        text = "Введите новый пароль"
        back_password_button = InlineKeyboardButton(text="назад", callback_data="settings_back")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[back_password_button]])
        await context.bot.edit_message_text(chat_id=query.message.chat_id,
                                            message_id=query.message.message_id,
                                            text=text,
                                            reply_markup=keyboard)
        context.user_data["password_edit"] = True
        logger.info(
            f"Пользователь {update.effective_user.username} /{full_name} вызвал функцию settings_edit."
            f" Статус: смена пароля")
    elif data[1] == "picture":
        if data[2] == "0":
            context.user_data["picture_edit"] = False
            text = "выберите какую картинку заменить хотите\n Афиша 1 - при открытии афиши \n" \
                   " Афиша 2 - когда концертов нету\n Приветствие - при вызове команды /start\n" \
                   " Отзывы - когда пользователь нажимает Обратная связь"
            back_password_button = InlineKeyboardButton(text="назад", callback_data="settings_back")

            main_wallpapers = InlineKeyboardButton(text="Афиша 1", callback_data="settings_picture_1")
            main_for_meet_wallpapers = InlineKeyboardButton(text="Приветствие",
                                                            callback_data="settings_picture_3")
            end_wallpapers = InlineKeyboardButton(text="Афиша 2", callback_data="settings_picture_2")
            feedback_wallpapers = InlineKeyboardButton(text="Отзывы", callback_data="settings_picture_4")
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[main_wallpapers], [end_wallpapers],
                                                             [main_for_meet_wallpapers], [feedback_wallpapers],
                                                             [back_password_button]])
            await context.bot.edit_message_text(chat_id=query.message.chat_id,
                                                message_id=query.message.message_id,
                                                text=text,
                                                reply_markup=keyboard)
            logger.info(
                f"Пользователь {update.effective_user.username} /{full_name} вызвал функцию settings_edit. "
                f"Статус: смена картинки")
        elif data[2] == "1":
            context.user_data["picture_edit"] = True
            context.user_data["picture_edit_num"] = "1"
            text = "загрузите картинку для Афиша 1"
            back_password_button = InlineKeyboardButton(text="назад", callback_data="settings_picture_0")
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[back_password_button]])
            await context.bot.edit_message_text(chat_id=query.message.chat_id,
                                                message_id=query.message.message_id,
                                                text=text,
                                                reply_markup=keyboard)
            logger.info(
                f"Пользователь {update.effective_user.username} /{full_name} вызвал функцию settings_edit."
                f" Статус: начало загрузки Афиша 1")
        elif data[2] == "2":
            context.user_data["picture_edit"] = True
            context.user_data["picture_edit_num"] = "2"
            text = "загрузите картинку для Афиша 2"
            back_password_button = InlineKeyboardButton(text="назад", callback_data="settings_picture_0")
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[back_password_button]])
            await context.bot.edit_message_text(chat_id=query.message.chat_id,
                                                message_id=query.message.message_id,
                                                text=text,
                                                reply_markup=keyboard)
            logger.info(
                f"Пользователь {update.effective_user.username} /{full_name} вызвал функцию settings_edit. "
                f"Статус: начало загрузки Афиша 2")
        elif data[2] == "3":
            context.user_data["picture_edit"] = True
            context.user_data["picture_edit_num"] = "3"
            text = "загрузите картинку для Приветствие"
            back_password_button = InlineKeyboardButton(text="назад", callback_data="settings_picture_0")
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[back_password_button]])
            await context.bot.edit_message_text(chat_id=query.message.chat_id,
                                                message_id=query.message.message_id,
                                                text=text,
                                                reply_markup=keyboard)
            logger.info(
                f"Пользователь {update.effective_user.username} /{full_name} вызвал функцию settings_edit."
                f" Статус: начало загрузки Приветствие")
        elif data[2] == "4":
            context.user_data["picture_edit"] = True
            context.user_data["picture_edit_num"] = "4"
            text = "загрузите картинку для Отзывы"
            back_password_button = InlineKeyboardButton(text="назад", callback_data="settings_picture_0")
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[back_password_button]])
            await context.bot.edit_message_text(chat_id=query.message.chat_id,
                                                message_id=query.message.message_id,
                                                text=text,
                                                reply_markup=keyboard)
            logger.info(
                f"Пользователь {update.effective_user.username} /{full_name} вызвал функцию settings_edit. "
                f"Статус: начало загрузки Отзывы ")


async def password_edit(update, context):
    if context.user_data is not None:
        search_query = context.user_data.get("password_edit")
        if search_query is not None:
            if context.user_data["password_edit"]:
                user = update.effective_user
                full_name = user.full_name
                # Получение введенного пользователем имени
                settings.PASSWORD = update.message.text
                text = f"новый пароль :\n{settings.PASSWORD}"
                print(text)
                # Сохранение списка отзывов в файл
                with open(settings.PASSWORD_TXT, 'wb') as file:
                    pickle.dump(settings.PASSWORD, file)
                await context.bot.send_message(chat_id=update.message.chat_id, text=text)
                context.user_data["password_edit"] = False
                logger.info(
                    f"Пользователь {update.effective_user.username} /{full_name} вызвал функцию password_edit. "
                    f"Статус: пароль изменен на {settings.PASSWORD}")


async def picture_edit(update, context):
    if context.user_data is not None:
        search_query = context.user_data.get("picture_edit")
        if search_query is not None:
            if context.user_data["picture_edit"]:
                user = update.effective_user
                text = "картинка загруженна для "
                message = update.effective_message
                full_name = user.full_name
                if message.photo:  # Если сообщение содержит фото
                    photos = message.photo
                    if context.user_data["picture_edit_num"] == "1":
                        settings.MAIN_WALLPAPERS = photos[-1].file_id
                        settings.wallpapers_dict["main_wallpapers"] = photos[-1].file_id
                        text += "афиши 1"
                        logger.info(
                            f"Пользователь {update.effective_user.username} /{full_name} вызвал функцию picture_edit."
                            f" Статус: загружена афиша 1")
                    elif context.user_data["picture_edit_num"] == "2":
                        settings.END_WALLPAPERS = photos[-1].file_id
                        settings.wallpapers_dict["end_wallpapers"] = photos[-1].file_id
                        text += "афиши 2"
                        logger.info(
                            f"Пользователь {update.effective_user.username} /{full_name} вызвал функцию picture_edit."
                            f" Статус: загружена афиша 2")
                    elif context.user_data["picture_edit_num"] == "3":
                        settings.MAIN_FOR_MEET_WALLPAPERS = photos[-1].file_id
                        settings.wallpapers_dict["main_for_meet_wallpapers"] = photos[-1].file_id
                        text += "приветствие"
                        logger.info(
                            f"Пользователь {update.effective_user.username} /{full_name} вызвал функцию picture_edit."
                            f" Статус: загружена Приветствие")
                    elif context.user_data["picture_edit_num"] == "4":
                        settings.FEEDBACK_WALLPAPERS = photos[-1].file_id
                        settings.wallpapers_dict["feedback_wallpapers"] = photos[-1].file_id
                        text += "отзывы"
                        logger.info(
                            f"Пользователь {update.effective_user.username} /{full_name} вызвал функцию picture_edit."
                            f" Статус: загружена Отзывы")
                    with open(settings.WALLPAPERS_TXT, 'wb') as file:
                        pickle.dump(settings.wallpapers_dict, file)
                await context.bot.send_message(chat_id=update.message.chat_id, text=text)
