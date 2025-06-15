import random
import logging

from database.db import Database
from database.models import Word
from bot.keyboards import main_keyboard
from telebot import TeleBot, types

logger = logging.getLogger(__name__)


def show_next_card(bot: TeleBot, message: types.Message, db: Database):
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        # Гарантируем существование пользователя и стандартных слов
        db.ensure_user_exists(user_id)

        # Получаем слова пользователя
        words = db.get_user_words(user_id)

        if not words:
            # Предлагаем добавить первое слово с клавиатурой
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton("Добавить слово ➕"))
            bot.send_message(
                    chat_id,
                    "У вас пока нет слов для изучения. Добавьте первое слово!",
                    reply_markup=markup
            )
            return None

        # Выбираем случайное целевое слово
        target = random.choice(words)

        # Выбираем 3 других случайных слова
        other_words = [word for word in words if word.id != target.id]
        others = random.sample(other_words, min(3, len(other_words)))

        # Создаем клавиатуру
        markup = main_keyboard([target] + others)

        # Обновляем состояние пользователя
        if not db.update_user_state(user_id, target.id):
            logger.warning(f"Не удалось обновить состояние для user_id={user_id}")

        # Отправляем сообщение с указанием типа слова
        word_type = "🆕 Ваше слово" if target.is_custom else "📚 Стандартное слово"
        message_text = (
                f"Выбери перевод слова:\n"
                f"☐ {target.russian}\n"
                f"<i>{word_type}</i>"
        )

        bot.send_message(
                chat_id,
                message_text,
                reply_markup=markup,
                parse_mode="HTML"
        )

        logger.info(f"Показана карточка: {target.english} -> {target.russian} для user_id={user_id}")
        return target

    except Exception as e:
        logger.error(f"Ошибка при показе карточки: {str(e)}")

        # При ошибке показываем клавиатуру для продолжения
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("Дальше ⏭"))

        bot.send_message(
                chat_id,
                "Произошла ошибка. Нажмите 'Дальше ⏭' для продолжения",
                reply_markup=markup
        )
        return None