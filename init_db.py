# init_db.py
from database.db import Database

if __name__ == '__main__':
    import logging

    logging.basicConfig(level=logging.INFO)

    db = Database()
    db.initialize()
    print("База данных успешно инициализирована")