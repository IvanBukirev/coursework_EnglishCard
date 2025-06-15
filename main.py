# main.py
import logging
from telebot import TeleBot, custom_filters
from config import BOT_TOKEN
from database.db import Database
from bot.handlers import register_handlers

# Настройка логирования
logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
                logging.FileHandler("bot_debug.log"),
                logging.StreamHandler()
        ]
)

logger = logging.getLogger(__name__)


def main():
    logger.info("Запуск бота...")

    try:
        # Инициализация базы данных
        logger.info("Создание подключения к базе данных...")
        db = Database()

        logger.info("Инициализация базы данных...")
        db.initialize()
        logger.info("База данных успешно инициализирована")

        # Проверка наличия стандартных слов
        logger.info("Проверка наличия слов в базе данных...")
        test_words = db.get_user_words(1)  # Тестовый запрос
        logger.info(f"Найдено {len(test_words)} слов в базе данных")

        # Создание бота
        logger.info(f"Создание бота с токеном: {BOT_TOKEN[:10]}...")
        bot = TeleBot(BOT_TOKEN)

        # Регистрация обработчиков
        logger.info("Регистрация обработчиков сообщений...")
        register_handlers(bot, db)

        # Регистрация кастомных фильтров
        logger.info("Добавление кастомных фильтров...")
        bot.add_custom_filter(custom_filters.StateFilter(bot))

        # Запуск бота
        logger.info("Бот запущен и готов к работе...")
        bot.infinity_polling()

    except Exception as e:
        logger.exception(f"Критическая ошибка в работе бота: {str(e)}")
    finally:
        try:
            if 'db' in locals():
                logger.info("Закрытие соединения с базой данных...")
                db.close()
        except Exception as e:
            logger.error(f"Ошибка при закрытии соединения с БД: {str(e)}")
        finally:
            logger.info("Работа бота завершена")


if __name__ == '__main__':
    main()