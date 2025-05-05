import os
import telebot
import requests
import psycopg2
import random

from telebot import types, TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup
from dotenv import load_dotenv

load_dotenv('../../.env')



database_name = os.getenv('DB_NAME_CRUD')
user_name = os.getenv('USER_NAME')
password_db = os.getenv('USER_PASSWORD')



if __name__ == '__main__':
    print('PyCharm')

