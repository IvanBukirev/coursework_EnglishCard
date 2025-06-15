from dotenv import load_dotenv

load_dotenv()
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

DB_CONFIG = {
        "host":     os.getenv("DB_HOST"),
        "database": os.getenv("DB_NAME"),
        "user":     os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
}
DEFAULT_WORDS = [
        ("Peace", "Мир"),
        ("Green", "Зеленый"),
        ("White", "Белый"),
        ("Hello", "Привет"),
        ("Car", "Машина"),
        ("We", "Мы"),
        ("She", "Она"),
        ("It", "Оно"),
        ("Red", "Красный"),
        ("Blue", "Синий")
]
