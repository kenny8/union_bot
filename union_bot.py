
import logging
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
import settings
from afisha_ import afisha, afisha_callback
from giveaway import giveaway, giveaway_callback, giveaway_text
from feedback import feedback, feedback_text, feedback_callback
from admin import admin_out, admin, is_admin, settings_edit, settings_callback, password_edit, picture_edit
import pickle
import asyncio


# Включение логгирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# Декоратор для логирования вызова функции
def log_user_action(func):
    def wrapper(update, context, *args, **kwargs):
        user = update.effective_user
        full_name = user.full_name
        user = update.effective_user
        logger.info(f"Пользователь {user.username}/{full_name} вызвал функцию {func.__name__}")
        return func(update, context, *args, **kwargs)
    return wrapper

# Создание разметки клавиатуры для меню
# reply_keyboard_main = ReplyKeyboardMarkup(
#    [["Афиша", "Розыгрыш билетов"], ["Исполнители", "Обратная связь"]],
#    resize_keyboard=True, # изменить размер клавиатуры
# )


reply_keyboard_main = ReplyKeyboardMarkup(
    [["Афиша", "Розыгрыш билетов"], ["Обратная связь"]],
    resize_keyboard=True,  # изменить размер клавиатуры
)


reply_keyboard_admin = ReplyKeyboardMarkup(
        [["Афиша", "Розыгрыш билетов"], ["Обратная связь", "Настройки", "Выход"]],
        resize_keyboard=True,  # изменить размер клавиатуры
    )

# Определение обработчиков команд. Обычно они принимают два аргумента: update и context.
# Функция обработки команды /start с декоратором логирования


@log_user_action
async def start(update, context):
    user = update.effective_user
    user_id = user.id
    context.user_data["password_edit"] = False
    context.user_data["feedback"] = False
    context.user_data["picture_edit"] = False
    context.user_data["login"] = False
    # Отправка сообщения пользователю
    reply_keyboard = reply_keyboard_main
    if is_admin(user_id):
        reply_keyboard = reply_keyboard_admin
    await context.bot.send_photo(chat_id=update.message.chat_id, photo=settings.MAIN_FOR_MEET_WALLPAPERS)
    await update.message.reply_html(
        rf"Привет, {user.mention_html()}! Это бот Липецкой филармонии! :) 123456891011121314",
        reply_markup=reply_keyboard,
    )
    full_name = user.full_name
    print(full_name)
    print(user_id)
    print(user.mention_html())
    if update.effective_chat.id not in [chat[1] for chat in settings.USERS]:
        settings.USERS.append([user.username, update.effective_chat.id, full_name, user_id, user.mention_html()])
    else:
        index = [chat[1] for chat in settings.USERS].index(update.effective_chat.id)
        settings.USERS[index] = [user.username, update.effective_chat.id, full_name, user_id, user.mention_html()]

    # if full_name == "Kenny":
    #    print("gjikj")
    #    for user_n in settings.USERS:
    #        if user_n[0] is None and user_n[1] not in [user_n[1] for user_n in settings.START_GIVEAWAY[4]]:
    #            await context.bot.send_message(
    #                chat_id=user_n[1],
    #                text='Возможно раньше вы не смогли присоединиться к розыгрышу(если у вас не
    #                было имени пользователя t.me/username), если хотите попробуйте снова',
    #                reply_markup=reply_keyboard
    #            )

    with open(settings.USERS_TXT, 'wb') as file:
        pickle.dump(settings.USERS, file)
    vk = InlineKeyboardButton(text="vk", url="https://vk.com/unionzal")
    dzen = InlineKeyboardButton(text="dzen", url="https://dzen.ru/id/623981f3b6c1bf4924ba9525")
    tg = InlineKeyboardButton(text="tg", url="https://t.me/filarmonia48")
    ok = InlineKeyboardButton(text="ok", url="https://ok.ru/group54024261795965")
    union = InlineKeyboardButton(text="union", url="https://unionzal.ru")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[tg, vk, ok], [dzen, union]])
    await context.bot.send_message(chat_id=update.message.chat_id,
                                   text="вот наши социалки",
                                   reply_markup=keyboard)
# Функция обработки команды /help с декоратором логирования


@log_user_action
async def help_command(update, context):
    # Отправка сообщения, когда пользователь вводит команду /help.
    # Отправка сообщения пользователю с инструкцией, что нужно делать
    context.user_data["password_edit"] = False
    context.user_data["feedback"] = False
    context.user_data["picture_edit"] = False
    context.user_data["login"] = False
    user = update.effective_user
    user_id = user.id
    if is_admin(user_id):
        text = "сейчас вы под админкой\n в розыгрышах можно настроить сам конкурс и обьявить об его окончании" \
               "\n в настройках можно сменить пароль или картинки \n в отзывах можно посмотреть что написали люди"
    else:
        text = "в афиши можно посмотреть ближайшие концерты\n в розыгрышах можно выйграть билет на концерт" \
               "\n в обратной связи можно написать ваш отзыв"
    await update.message.reply_text(text)


@log_user_action
async def login(update, context):
    context.user_data["password_edit"] = False
    context.user_data["feedback"] = False
    context.user_data["picture_edit"] = False
    context.user_data["login"] = True
    await context.bot.send_message(chat_id=update.message.chat_id,
                                   text="если вы хотите войти в админку то введите пароль")


async def text_reader(update, context):
    await feedback_text(update, context)
    await giveaway_text(update, context)
    await password_edit(update, context)
    await admin(update, context)


async def photo_reader(update, context):
    await giveaway_text(update, context)
    await picture_edit(update, context)


def main():
    # Запуск бота.
    # Создание приложения и передача ему токена вашего бота.
    application = Application.builder().token(settings.TOKEN_BOT).build()
    # Назначение обработчиков на различные команды в Telegram.
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Добавление обработчиков для каждой кнопки
    application.add_handler(
        MessageHandler(filters.Regex("^Афиша$"), callback=afisha)
    )
    # Регистрация обработчиков афиши
    application.add_handler(CallbackQueryHandler(callback=afisha_callback, pattern=r"afisha_\d*"))

    application.add_handler(
        MessageHandler(filters.Regex("^Розыгрыш билетов$"), callback=giveaway)
    )
    application.add_handler(CallbackQueryHandler(callback=giveaway_callback, pattern=r"giveaway_\d*"))

    application.add_handler(CommandHandler("login", login))
    application.add_handler(
        MessageHandler(filters.Regex(f"^Выход$"), callback=admin_out)
    )
    application.add_handler(
        MessageHandler(filters.Regex(f"^Настройки$"), callback=settings_edit)
    )
    application.add_handler(CallbackQueryHandler(callback=settings_callback, pattern=r"settings_\d*"))

    application.add_handler(
        MessageHandler(filters.Regex("^Обратная связь$"), callback=feedback)
    )
    application.add_handler(CallbackQueryHandler(callback=feedback_callback, pattern=r"feedback_\d*"))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_reader))
    application.add_handler(MessageHandler(filters.PHOTO, photo_reader))

    # Запуск бота и ожидание его завершения пользователем (нажатие Ctrl-C).

    application.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
