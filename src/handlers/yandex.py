# src/handlers/yandex.py
from dotenv import load_dotenv
load_dotenv()

import os

import yadisk
from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy.future import select

from models import User, async_session

router = Router()

# Ваш client_id Яндекс.Диска из .env
CLIENT_ID = os.getenv("YD_CLIENT_ID")

# Права (scope), которые запрашиваем
SCOPES = [
    "botplatform:read",
    "cloud_api:disk.app_folder",
    "cloud_api:disk.read",
    "cloud_api:disk.write",
    "cloud_api:disk.info",
]

@router.message(Command("register"))
async def cmd_register(message: types.Message):
    # Собираем строку scope-ов через пробел
    scope_str = " ".join(SCOPES)
    # Формируем URL авторизации
    auth_url = (
        f"https://oauth.yandex.ru/authorize"
        f"?response_type=token"
        f"&client_id={CLIENT_ID}"
        f"&scope={scope_str}"
    )
    text = (
        "Чтобы получить токен для доступа к вашему Яндекс.Диску:\n\n"
        "1. Перейдите по ссылке и авторизуйтесь:\n"
        f"{auth_url}\n\n"
        "2. После успешной авторизации вас перенаправит на:\n"
        "   https://oauth.yandex.ru/verification_code#access_token=<ТОКЕН>&...\n\n"
        "3. Скопируйте значение <ТОКЕН> и отправьте боту команду:\n"
        "`/token <ТОКЕН>`"
    )
    # Разметка Markdown для моноширинного отображения токена
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("token"))
async def cmd_token(message: types.Message):
    parts = message.text.strip().split(maxsplit=1)
    if len(parts) != 2:
        return await message.answer(
            "Неверный формат. Использование:\n"
            "`/token <ТОКЕН>`",
            parse_mode="Markdown"
        )
    token = parts[1]
    # Проверяем токен через yadisk
    yd = yadisk.YaDisk(token=token)
    try:
        yd.get_meta("/")  # проверка доступа к корню Диска
    except Exception:
        return await message.answer("Токен недействителен или нет доступа.")

    # Сохраняем токен в базе (только для зарегистрированных преподавателей)
    async with async_session() as session:
        res = await session.execute(select(User).where(User.user_id == message.from_user.id))
        user = res.scalar_one_or_none()

        if user and user.role == "tutor":
            user.token = token
            await session.commit()
            await message.answer("Токен успешно сохранён.")
        else:
            await message.answer("Только преподаватель может сохранять токен.")
