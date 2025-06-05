# src/handlers/tracking.py
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy.future import select

from models import TrackedFolder, User, async_session
from src.handlers.registration import RegStates  # если вы хотите переиспользовать RegStates

router = Router()

# Своя группа состояний для отслеживания папок
class TrackStates(StatesGroup):
    entering_path = State()

@router.message(Command("add"))
async def cmd_add(message: types.Message, state: FSMContext):
    # Проверяем, что это преподаватель
    uid = message.from_user.id
    async with async_session() as session:
        res = await session.execute(select(User).where(User.user_id == uid))
        tutor = res.scalar_one_or_none()

    if not tutor or tutor.role != "tutor":
        return await message.answer("Только преподаватель может добавлять папки.")

    # Просим путь и переводим FSM в новое состояние
    await message.answer("Введите путь к папке на вашем Яндекс.Диске:")
    await state.set_state(TrackStates.entering_path)

@router.message(TrackStates.entering_path)
async def process_folder_path(message: types.Message, state: FSMContext):
    path = message.text.strip()
    uid  = message.from_user.id

    async with async_session() as session:
        # сохраняем новую отслеживаемую папку
        session.add(TrackedFolder(tutor_id=uid, path=path))
        await session.commit()

        # находим всех подписанных студентов
        subs = (await session.execute(
            select(User).where(User.subscribe_to == uid)
        )).scalars().all()

    # Рассылаем уведомления
    for sub in subs:
        await message.bot.send_message(
            sub.user_id,
            f"Добавлена новая папка для отслеживания: {path}"
        )

    await message.answer("Путь сохранён, все ваши слушатели получили уведомление.")
    await state.clear()
