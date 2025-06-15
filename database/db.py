# database/db.py
import psycopg2
import logging
from config import DB_CONFIG, DEFAULT_WORDS
from database.models import Word, UserState

logger = logging.getLogger(__name__)


class Database:

    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.conn.autocommit = False
        logger.info("Соединение с базой данных установлено")

    def initialize(self):
        """Создает таблицы и добавляет стандартные слова"""
        try:
            with self.conn.cursor() as cur:
                # Создание таблиц
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS words (
                        id SERIAL PRIMARY KEY,
                        english VARCHAR(50) NOT NULL UNIQUE,
                        russian VARCHAR(50) NOT NULL,
                        is_custom BOOLEAN DEFAULT FALSE
                    );

                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        first_seen TIMESTAMP DEFAULT NOW()
                    );

                    CREATE TABLE IF NOT EXISTS user_words (
                        user_id BIGINT REFERENCES users(user_id),
                        word_id INTEGER REFERENCES words(id),
                        is_deleted BOOLEAN DEFAULT FALSE,
                        PRIMARY KEY (user_id, word_id)
                    );

                    CREATE TABLE IF NOT EXISTS user_states (
                        user_id BIGINT PRIMARY KEY REFERENCES users(user_id),
                        current_word_id INTEGER REFERENCES words(id),
                        last_interaction TIMESTAMP DEFAULT NOW()
                    );
                """)

                # Добавление стандартных слов
                for en, ru in DEFAULT_WORDS:
                    cur.execute("""
                                        INSERT INTO words (english, russian, is_custom)
                                        VALUES (%s, %s, FALSE)
                                        ON CONFLICT (english) DO UPDATE 
                                        SET russian = EXCLUDED.russian
                                    """, (en, ru))

                self.conn.commit()
                logger.info(f"Добавлено {len(DEFAULT_WORDS)} стандартных слов")
        except Exception as e:
            logger.error(f"Ошибка при инициализации БД: {str(e)}")
            self.conn.rollback()
            raise

    def delete_word(self, user_id: int, word_id: int):
        """Удаляет слово для пользователя"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    UPDATE user_words 
                    SET is_deleted = TRUE 
                    WHERE user_id = %s AND word_id = %s
                """, (user_id, word_id))
                self.conn.commit()
                logger.info(f"Удалено слово word_id={word_id} для user_id={user_id}")
                return True
        except Exception as e:
            logger.error(f"Ошибка при удалении слова: {str(e)}")
            self.conn.rollback()
            return False

    def get_user_state(self, user_id: int) -> UserState:
        """Получает состояние пользователя"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT user_id, current_word_id, last_interaction
                    FROM user_states
                    WHERE user_id = %s
                """, (user_id,))
                row = cur.fetchone()
                if row:
                    state = UserState(*row)
                    logger.debug(f"Получено состояние для user_id={user_id}: {state}")
                    return state
                return None
        except Exception as e:
            logger.error(f"Ошибка при получении состояния пользователя: {str(e)}")
            return None



    def clear_user_state(self, user_id: int):
        """Очищает состояние пользователя"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM user_states
                    WHERE user_id = %s
                """, (user_id,))
                self.conn.commit()
                logger.info(f"Очищено состояние для user_id={user_id}")
                return True
        except Exception as e:
            logger.error(f"Ошибка при очистке состояния пользователя: {str(e)}")
            self.conn.rollback()
            return False

    def get_word_by_id(self, word_id: int) -> Word:
        """Получает слово по ID"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT id, english, russian, is_custom
                    FROM words
                    WHERE id = %s
                """, (word_id,))
                row = cur.fetchone()
                if row:
                    word = Word(*row)
                    logger.debug(f"Найдено слово по ID {word_id}: {word.english}")
                    return word
                return None
        except Exception as e:
            logger.error(f"Ошибка при получении слова по ID: {str(e)}")
            return None

    def ensure_user_exists(self, user_id: int):
        """Гарантирует, что пользователь существует в базе и добавлены стандартные слова"""
        try:
            with self.conn.cursor() as cur:
                # Проверяем, существует ли пользователь
                cur.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
                user_exists = cur.fetchone()

                if not user_exists:
                    # Создаем пользователя
                    cur.execute("""
                        INSERT INTO users (user_id) 
                        VALUES (%s)
                        ON CONFLICT (user_id) DO NOTHING
                    """, (user_id,))

                    # Добавляем стандартные слова пользователю
                    cur.execute("""
                        INSERT INTO user_words (user_id, word_id)
                        SELECT %s, id 
                        FROM words 
                        WHERE is_custom = FALSE
                        ON CONFLICT (user_id, word_id) DO NOTHING
                    """, (user_id,))

                    self.conn.commit()
                    logger.info(f"Добавлен новый пользователь {user_id} со стандартными словами")
                return True
        except Exception as e:
            logger.error(f"Ошибка при создании пользователя: {str(e)}")
            self.conn.rollback()
            return False

    def get_user_words(self, user_id: int) -> list[Word]:
        """Возвращает слова для пользователя"""
        self.ensure_user_exists(user_id)
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT w.id, w.english, w.russian, w.is_custom 
                    FROM words w
                    JOIN user_words uw ON w.id = uw.word_id
                    WHERE uw.user_id = %s AND uw.is_deleted = FALSE
                """, (user_id,))
                words = [Word(*row) for row in cur.fetchall()]
                logger.debug(f"Найдено {len(words)} слов для user_id={user_id}")
                return words
        except Exception as e:
            logger.error(f"Ошибка при получении слов пользователя: {str(e)}")
            return []

    def add_word(self, user_id: int, english: str, russian: str, is_custom=True):
        """Добавляет слово для пользователя"""
        self.ensure_user_exists(user_id)  # Гарантируем существование пользователя
        try:
            with self.conn.cursor() as cur:
                # Добавляем слово
                cur.execute("""
                    INSERT INTO words (english, russian, is_custom)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (english) DO UPDATE 
                    SET russian = EXCLUDED.russian
                    RETURNING id
                """, (english, russian, is_custom))

                result = cur.fetchone()
                if not result:
                    # Если слово не было добавлено (уже существует), получаем его ID
                    cur.execute("SELECT id FROM words WHERE english = %s", (english,))
                    result = cur.fetchone()

                word_id = result[0] if result else None
                if not word_id:
                    raise ValueError("Не удалось получить ID слова")

                # Связываем слово с пользователем
                cur.execute("""
                    INSERT INTO user_words (user_id, word_id)
                    VALUES (%s, %s)
                    ON CONFLICT (user_id, word_id) 
                    DO UPDATE SET is_deleted = FALSE
                """, (user_id, word_id))

                self.conn.commit()
                logger.info(f"Добавлено слово: {english} -> {russian} для user_id={user_id}")
                return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении слова: {str(e)}")
            self.conn.rollback()
            return False

    def update_user_state(self, user_id: int, word_id: int):
        """Обновляет состояние пользователя"""
        self.ensure_user_exists(user_id)  # Гарантируем существование пользователя
        try:
            with self.conn.cursor() as cur:
                # Проверяем существование слова
                cur.execute("SELECT 1 FROM words WHERE id = %s", (word_id,))
                if not cur.fetchone():
                    logger.warning(f"Слово с ID {word_id} не найдено")
                    return False

                cur.execute("""
                    INSERT INTO user_states (user_id, current_word_id)
                    VALUES (%s, %s)
                    ON CONFLICT (user_id) DO UPDATE
                    SET current_word_id = EXCLUDED.current_word_id,
                        last_interaction = NOW()
                """, (user_id, word_id))
                self.conn.commit()
                logger.debug(f"Обновлено состояние для user_id={user_id}: word_id={word_id}")
                return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении состояния пользователя: {str(e)}")
            self.conn.rollback()
            return False

    def close(self):
        """Закрывает соединение с БД"""
        try:
            if self.conn and not self.conn.closed:
                self.conn.close()
                logger.info("Соединение с БД закрыто")
        except Exception as e:
            logger.error(f"Ошибка при закрытии соединения с БД: {str(e)}")