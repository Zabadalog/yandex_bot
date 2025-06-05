# keyboard.py
from aiogram import types

def role_keyboard() -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Преподаватель")],
            [types.KeyboardButton(text="Слушатель")],
        ],
        resize_keyboard=True
    )
