from telebot import types
import random
import logging
logger = logging.getLogger(__name__)
def main_keyboard(words):
    """Создает клавиатуру с вариантами ответов"""
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)

    try:
        # Создаем кнопки только для английских слов
        english_words = [word.english for word in words]

        # Перемешиваем кнопки
        random.shuffle(english_words)

        # Добавляем кнопки вариантов ответов (максимум 4)
        buttons = [types.KeyboardButton(word) for word in english_words[:4]]
        for i in range(0, len(buttons), 2):
            row = buttons[i:i + 2]
            markup.add(*row)

        # Добавляем управляющие кнопки
        markup.row(
                types.KeyboardButton("Дальше ⏭"),
                types.KeyboardButton("Добавить слово ➕"),
                types.KeyboardButton("Удалить слово 🔙")
        )

        return markup

    except Exception as e:
        logger.error(f"Ошибка создания клавиатуры: {str(e)}")
        # Возвращаем простую клавиатуру в случае ошибки
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("Дальше ⏭"))
        return markup


def welcome_keyboard():
    """Клавиатура для приветственного сообщения"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Начать обучение ▶️"))
    return markup