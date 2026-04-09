from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import settings
import pickle
import logging
from admin import is_admin

# Включение логгирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


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


async def feedback(update, context):
    """Отправка сообщения, когда пользователь нажимает на кнопку 'Обратная связь'."""
    user = update.effective_user
    user_id = user.id
    full_name = user.full_name
    context.user_data["feedback"] = False
    context.user_data["password_edit"] = False
    context.user_data["login"] = False
    context.user_data["picture_edit"] = False
    if is_admin(user_id):
        total_feedbacks = len(settings.FEEDBACK_USER)
        if total_feedbacks > 0:
            text = f"Всего отзывов: {total_feedbacks}\n"
            buttons = []

            # Отобразим максимум 10 отзывов на одной странице
            for i, feedback in enumerate(settings.FEEDBACK_USER[:10]):
                read_status = "✅" if feedback['read'] else "❌"
                text += f"{feedback['id']}. Статус: {read_status}\n"
                buttons.extend([InlineKeyboardButton(text=str(feedback['id']),
                                                     callback_data=f"feedback_event_{feedback['id']}")])
            if total_feedbacks > 10:
                keyboard = build_menu(buttons, n_cols=4,
                                      footer_buttons=[InlineKeyboardButton(text=">",
                                                                           callback_data=f"feedback_menu_next_1")])
            else:
                keyboard = build_menu(buttons, n_cols=4)
            markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

            await context.bot.send_message(chat_id=update.message.chat_id,
                                           text=text,
                                           reply_markup=markup)
        else:
            text = "Отзывов нет"
            await context.bot.send_message(chat_id=update.message.chat_id,
                                           text=text)
        logger.info(
            f"Админ {user.username} /{full_name} вызвал функцию feedback.")
    else:
        text = "Напишите свой отзыв или проблему, с которой столкнулись:"
        await context.bot.send_photo(chat_id=update.message.chat_id, photo=settings.FEEDBACK_WALLPAPERS,
                                     caption=text)
        context.user_data["feedback"] = True
        logger.info(
            f"Пользователь {user.username} /{full_name} вызвал функцию feedback.")


async def feedback_callback(update, context):
    query = update.callback_query
    data = query.data.split("_")
    user = update.effective_user
    full_name = user.full_name
    if data[1] == "menu":
        if data[2] == "next":
            page_number = int(data[3])
            feedbacks_per_page = 10
            start_index = page_number * feedbacks_per_page
            end_index = start_index + feedbacks_per_page

            total_feedbacks = len(settings.FEEDBACK_USER)
            max_pages = (total_feedbacks - 1) // feedbacks_per_page

            text = f"Всего отзывов: {total_feedbacks}\n"
            buttons = []

            for i, feedback in enumerate(settings.FEEDBACK_USER[start_index:end_index], start=start_index):
                read_status = "✅" if feedback['read'] else "❌"
                text += f"{feedback['id']}. Статус: {read_status}\n"
                buttons.extend([InlineKeyboardButton(text=str(feedback['id']),
                                                     callback_data=f"feedback_event_{feedback['id']}")])

            prev_page_button = InlineKeyboardButton(text="<", callback_data=f"feedback_menu_next_{page_number - 1}")
            next_page_button = InlineKeyboardButton(text=">", callback_data=f"feedback_menu_next_{page_number + 1}")

            keyboard = build_menu(buttons, n_cols=4, footer_buttons=[prev_page_button, next_page_button])
            if page_number == 0:
                keyboard[-1].remove(prev_page_button)
            if page_number == max_pages:
                keyboard[-1].remove(next_page_button)
            markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

            await query.answer()  # Отправляем ответ о нажатии кнопки
            await context.bot.edit_message_text(chat_id=query.message.chat_id,
                                                message_id=query.message.message_id,
                                                text=text,
                                                reply_markup=markup)
            logger.info(
                f"Админ {user.username} /{full_name} вызвал функцию feedback. Статус feedback_menu_next_{int(data[3])}")
    elif data[1] == "event":
        feedback_index = int(data[2])
        if 0 <= feedback_index <= len(settings.FEEDBACK_USER):
            feedback = settings.FEEDBACK_USER[feedback_index-1]
            read_status = "✅" if feedback['read'] else "❌"
            text = f"Всего отзывов: {len(settings.FEEDBACK_USER)}\n"
            text += f"№ {feedback['id']} Пользователь: {feedback['username']}\n"
            text += f"Статус: {read_status}\n"
            text += f"{feedback['text']}"

            settings.FEEDBACK_USER[feedback_index-1]['read'] = True

            delete_feedback_button = InlineKeyboardButton(text="удалить",
                                                          callback_data=f"feedback_delete_{feedback_index}")
            back_feedback_button = InlineKeyboardButton(text="назад", callback_data=f"feedback_menu_next_0")
            prev_feedback_button = InlineKeyboardButton(text="<", callback_data=f"feedback_event_{feedback_index - 1}")
            next_feedback_button = InlineKeyboardButton(text=">", callback_data=f"feedback_event_{feedback_index + 1}")

            keyboard = [[delete_feedback_button, back_feedback_button], [prev_feedback_button, next_feedback_button]]
            if feedback_index == 1:
                keyboard[1].remove(prev_feedback_button)
            if feedback_index == len(settings.FEEDBACK_USER):
                keyboard[1].remove(next_feedback_button)
            markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

            await query.answer()  # Отправляем ответ о нажатии кнопки
            await context.bot.edit_message_text(chat_id=query.message.chat_id,
                                                message_id=query.message.message_id,
                                                text=text,
                                                reply_markup=markup)
            with open(settings.FEEDBACK_TXT, 'wb') as file:
                pickle.dump(settings.FEEDBACK_USER, file)
            logger.info(
                f"Админ {user.username} /{full_name} вызвал функцию feedback. Статус feedback_event_{feedback_index}")
    elif data[1] == "delete":
        feedback_index = int(data[2]) - 1
        if 0 <= feedback_index < len(settings.FEEDBACK_USER):
            deleted_feedback = settings.FEEDBACK_USER.pop(feedback_index)
            with open(settings.FEEDBACK_TXT, 'wb') as file:
                pickle.dump(settings.FEEDBACK_USER, file)

            # Обновляем ID оставшихся отзывов
            for i, feedback in enumerate(settings.FEEDBACK_USER):
                feedback['id'] = i + 1
            await query.answer("Отзыв удален")

            total_feedbacks = len(settings.FEEDBACK_USER)
            if total_feedbacks > 0:
                text = f"Всего отзывов: {total_feedbacks}\n"
                buttons = []
                # Отобразим максимум 10 отзывов на одной странице
                for i, feedback in enumerate(settings.FEEDBACK_USER[:10]):
                    read_status = "✅" if feedback['read'] else "❌"
                    text += f"{feedback['id']}. Статус: {read_status}\n"
                    buttons.extend([InlineKeyboardButton(text=str(feedback['id']),
                                                         callback_data=f"feedback_event_{feedback['id']}")])
                if total_feedbacks > 10:
                    keyboard = build_menu(buttons, n_cols=4, footer_buttons=[
                        InlineKeyboardButton(text=">", callback_data=f"feedback_menu_next_1")])
                else:
                    keyboard = build_menu(buttons, n_cols=4)
                markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

                await context.bot.edit_message_text(chat_id=query.message.chat_id,
                                                    message_id=query.message.message_id,
                                                    text=text,
                                                    reply_markup=markup)
                logger.info(
                    f"Админ {user.username} /{full_name} вызвал функцию feedback. "
                    f"Статус feedback_delete_{feedback['id']}")
            else:
                text = "Отзывов нет"
                await context.bot.edit_message_text(chat_id=query.message.chat_id,
                                                    message_id=query.message.message_id,
                                                    text=text)
                logger.info(
                    f"Админ {user.username} /{full_name} вызвал функцию feedback. Статус "
                    f"feedback_delete_{feedback['id']}- отзывы закончились")


async def feedback_text(update, context):
    if context.user_data is not None:
        search_query = context.user_data.get("feedback")
        if search_query is not None:
            if context.user_data["feedback"]:
                user = update.effective_user
                # Получение введенного пользователем имени
                text_feedback = update.message.text
                full_name = user.full_name
                # Создание словаря с данными отзыва
                feedback_data = {
                    'id': len(settings.FEEDBACK_USER)+1,
                    'user_id': user.id,
                    'full_name': user.full_name,
                    'username': user.username,
                    'user_html': user.mention_html(),
                    'text': text_feedback,
                    'read': False  # По умолчанию отзыв не прочитан
                }

                # Добавление словаря в список отзывов в settings.FEEDBACK_USER
                settings.FEEDBACK_USER.append(feedback_data)
                print(settings.FEEDBACK_USER)
                # Сохранение списка отзывов в файл
                with open(settings.FEEDBACK_TXT, 'wb') as file:
                    pickle.dump(settings.FEEDBACK_USER, file)

                text = f"Ваше мнение для нас очень важно"  # Исправьте текст сообщения по вашему желанию
                await context.bot.send_message(chat_id=update.message.chat_id, text=text)
                context.user_data["feedback"] = False
                logger.info(
                    f"Пользователь {user.username} /{full_name} вызвал функцию feedback_text. Статус отзыв сохранен")
