from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy.future import select

from models import User, async_session

router = Router()

@router.message(Command("status"))
async def cmd_status(message: types.Message):
    uid = message.from_user.id
    async with async_session() as session:
        res = await session.execute(
            select(User).where(User.user_id == uid)
        )
        user = res.scalar_one_or_none()

    if not user:
        return await message.answer("Не зарегистрированы. /start")

    # Если преподаватель
    if user.tutor_code:
        return await message.answer(
            f"Вы — преподаватель\n"
            f"ID: {uid}\n"
            f"Username: @{user.username or 'не задан'}\n"
            f"Код: `{user.tutor_code}`",
            parse_mode="Markdown"
        )

    # Если слушатель
    if user.subscribe_to:
        # найдём username преподавателя
        async with async_session() as session:
            r2 = await session.execute(
                select(User).where(User.user_id == user.subscribe_to)
            )
            tutor = r2.scalar_one_or_none()

        name = tutor.username if tutor else f"ID {user.subscribe_to}"
        return await message.answer(
            f"Вы — слушатель.\n"
            f"ID: {uid}\n"
            f"Username: @{user.username or 'не задан'}\n"
            f"Подписан на: @{name}"
        )

    # Если нет ни tutor_code, ни подписки
    await message.answer("Невозможно определить ваш статус.")
