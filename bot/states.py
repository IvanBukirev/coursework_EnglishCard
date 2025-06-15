from telebot.handler_backends import State, StatesGroup

class AddWordStates(StatesGroup):
    english = State()
    russian = State()