# src/handlers/help.py
from aiogram import Router, types
from aiogram.filters import Command

router = Router()

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "/start — регистрация преподавателя/студента\n"
        "/status — узнать ваш статус\n"
        "/register — инструкция по получению токена Яндекс.Диска\n"
        "<code>/token &lt;ваш_токен&gt;</code> — сохранить токен\n"
        "/add — (для преподавателя) добавить папку для отслеживания\n"
        "/change_role — сменить роль\n"
        "/help — показать это сообщение",
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardRemove(),
    )
