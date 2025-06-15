import time
import logging
from telebot import TeleBot, types

from bot.states import AddWordStates
from database.db import Database
from bot.utils import show_next_card
from bot.keyboards import welcome_keyboard

logger = logging.getLogger(__name__)


def register_handlers(bot: TeleBot, db: Database):
    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message: types.Message):
        chat_id = message.chat.id
        user_id = message.from_user.id

        # Очищаем состояние пользователя
        db.clear_user_state(user_id)

        welcome_text = (
                "Привет 👋 Давай попрактикуемся в английском языке. "
                "Тренировки можешь проходить в удобном для себя темпе.\n\n"
                "У тебя есть возможность использовать тренажёр как конструктор:\n"
                "- Добавить слово ➕\n"
                "- Удалить слово 🔙\n\n"
                "Ну что, начнём ⬇️"
        )

        # Создаем клавиатуру с кнопкой "Начать обучение"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("Начать обучение ▶️"))

        bot.send_message(chat_id, welcome_text, reply_markup=markup)

    @bot.message_handler(func=lambda m: m.text == "Начать обучение ▶️")
    def start_learning(message: types.Message):
        db.clear_user_state(message.from_user.id)
        show_next_card(bot, message, db)

    @bot.message_handler(func=lambda m: m.text == "Дальше ⏭")
    def next_card_handler(message: types.Message):
        # Создаем временную клавиатуру
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("Дальше ⏭"))

        # Отправляем сообщение с клавиатурой
        bot.send_message(
                message.chat.id,
                "Загружаю следующую карточку...",
                reply_markup=markup
        )

        # Показываем следующую карточку
        show_next_card(bot, message, db)

    @bot.message_handler(func=lambda m: m.text == "Добавить слово ➕")
    def add_word_start(message: types.Message):
        # Очищаем состояние перед добавлением слова
        db.clear_user_state(message.from_user.id)
        bot.send_message(message.chat.id, "Введите английское слово:")
        bot.set_state(message.from_user.id, AddWordStates.english, message.chat.id)

    @bot.message_handler(state=AddWordStates.english)
    def add_word_english(message: types.Message):
        # Сохраняем английское слово во временных данных
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['english'] = message.text

        bot.send_message(message.chat.id, "Теперь введите перевод:")
        bot.set_state(message.from_user.id, AddWordStates.russian, message.chat.id)

    @bot.message_handler(state=AddWordStates.russian)
    def add_word_russian(message: types.Message):
        user_id = message.from_user.id
        chat_id = message.chat.id

        with bot.retrieve_data(user_id, chat_id) as data:
            english = data.get('english', '').strip()
            russian = message.text.strip()

            if not english or not russian:
                bot.send_message(chat_id, "Ошибка: не указано слово или перевод")
                return

            if db.add_word(user_id, english, russian):
                bot.send_message(chat_id, f"Слово '{english}' добавлено!")
            else:
                bot.send_message(chat_id, "Не удалось добавить слово. Попробуйте позже.")

        # Очищаем состояние
        bot.delete_state(user_id, chat_id)

        # Показываем следующую карточку
        show_next_card(bot, message, db)

    @bot.message_handler(func=lambda m: m.text == "Удалить слово 🔙")
    def delete_word_handler(message: types.Message):
        chat_id = message.chat.id
        user_id = message.from_user.id

        state = db.get_user_state(user_id)
        if not state or state.current_word_id <= 0:
            bot.send_message(chat_id, "Нет активного слова для удаления")
            show_next_card(bot, message, db)
            return

        word = db.get_word_by_id(state.current_word_id)
        if not word:
            bot.send_message(chat_id, "Ошибка: слово не найдено")
            show_next_card(bot, message, db)
            return

        if not word.is_custom:
            bot.send_message(
                    chat_id,
                    "⛔ Стандартные слова нельзя удалить!\n"
                    "Вы можете удалять только слова, которые добавили сами."
            )
            show_next_card(bot, message, db)
            return

        if db.delete_word(user_id, state.current_word_id):
            bot.send_message(chat_id, "✅ Слово успешно удалено!")
        else:
            bot.send_message(chat_id, "❌ Не удалось удалить слово. Попробуйте позже.")

        show_next_card(bot, message, db)

    @bot.message_handler(func=lambda message: True, content_types=['text'])
    def handle_answer(message: types.Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        user_answer = message.text

        # Пропускаем команды
        if user_answer in ["Дальше ⏭", "Добавить слово ➕", "Удалить слово 🔙", "Начать обучение ▶️"]:
            return

        # Создаем временную клавиатуру
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("Дальше ⏭"))

        # Получаем текущее состояние
        state = db.get_user_state(user_id)
        if not state or state.current_word_id <= 0:
            bot.send_message(
                    chat_id,
                    "Нажмите 'Дальше ⏭' для новой карточки",
                    reply_markup=markup
            )
            return

        # Получаем слово из базы данных
        word = db.get_word_by_id(state.current_word_id)
        if not word:
            bot.send_message(
                    chat_id,
                    "Ошибка: слово не найдено. Нажмите 'Дальше ⏭'",
                    reply_markup=markup
            )
            return

        # Проверяем ответ
        if user_answer == word.english:
            response = f"{user_answer} ✅"
        else:
            response = f"{user_answer} ❌\nПравильно: {word.english}"

        bot.send_message(chat_id, response, reply_markup=markup)

        # Показываем следующую карточку через 1 секунду
        time.sleep(1)
        show_next_card(bot, message, db)