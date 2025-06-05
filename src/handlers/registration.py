# src/handlers/registration.py
import uuid
import secrets

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy.future import select
from .yandex import CLIENT_ID, SCOPES

from models import User, async_session
from .keyboard import role_keyboard

router = Router()

class RegStates(StatesGroup):
    choosing_role = State()
    entering_tutor_code = State()
    entering_yadisk_token = State()
    entering_code = State()

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer(
        "Вы преподаватель или слушатель?",
        reply_markup=role_keyboard()
    )
    await state.set_state(RegStates.choosing_role)

@router.message(RegStates.choosing_role)
async def role_chosen(message: types.Message, state: FSMContext):
    role = message.text.lower()
    uid = message.from_user.id
    uname = message.from_user.username or "unknown"

    async with async_session() as session:
        res = await session.execute(select(User).where(User.user_id == uid))
        user_obj = res.scalar_one_or_none()

        # если уже есть активная роль — отказываемся
        if user_obj and (user_obj.tutor_code or user_obj.subscribe_to):
            await message.answer(
                "Вы уже зарегистрированы.",
                reply_markup=ReplyKeyboardRemove()
            )
            await state.clear()
            return

        if role == "преподаватель":
            code = uuid.uuid4().hex[:8]
            if user_obj:
                user_obj.role = "tutor"
                user_obj.tutor_code = code
                user_obj.subscribe = None
            else:
                session.add(User(
                    user_id=uid,
                    username=uname,
                    role="tutor",
                    tutor_code=code
                ))
            await session.commit()
            await message.answer(
                f"Вы преподаватель. Ваш код: `{code}`",
                parse_mode="Markdown",
                reply_markup=ReplyKeyboardRemove()
            )
            await state.clear()

        elif role == "слушатель":
            await message.answer(
                "Введите код преподавателя:",
                reply_markup=ReplyKeyboardRemove()
            )
            await state.set_state(RegStates.entering_code)

        else:
            await message.answer("Пожалуйста, нажмите одну из кнопок.")

@router.message(Command("token"))
async def save_yandex_token(message: types.Message):
    uid = message.from_user.id
    parts = message.text.strip().split(maxsplit=1)

    if len(parts) < 2:
        await message.answer("Пожалуйста, отправьте команду в формате:\n/token <ваш_токен>")
        return

    token = parts[1]

    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == uid))
        user_obj = result.scalar_one_or_none()

        if not user_obj:
            await message.answer("Сначала зарегистрируйтесь через /start.")
            return

        user_obj.yadisk_token = token
        await session.commit()

    await message.answer("Токен Яндекс.Диска сохранён успешно")

@router.message(RegStates.entering_code)
async def process_tutor_code(message: types.Message, state: FSMContext):
    code = message.text.strip()
    uid = message.from_user.id
    uname = message.from_user.username or "unknown"

    async with async_session() as session:
        # ищем преподавателя по коду
        res = await session.execute(select(User).where(User.tutor_code == code))
        tutor = res.scalar_one_or_none()

        if not tutor:
            await message.answer(
                "Неверный код. Попробуйте снова:",
                reply_markup=ReplyKeyboardRemove()
            )
            return

        # создаём или обновляем слушателя
        res2 = await session.execute(select(User).where(User.user_id == uid))
        user_obj = res2.scalar_one_or_none()

        if user_obj:
            user_obj.role = "student"
            user_obj.subscribe_to = tutor.user_id
            user_obj.tutor_code = None
        else:
            session.add(User(
                user_id=uid,
                username=uname,
                role="student",
                subscribe_to=tutor.user_id
            ))

        await session.commit()

    await message.answer(
        f"Вы слушатель @{tutor.username}",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.clear()

@router.message(Command("change_role"))
async def cmd_change_role(message: types.Message, state: FSMContext):
    uid = message.from_user.id

    # Сбросим только tutor_code и subscribe
    async with async_session() as session:
        res = await session.execute(select(User).where(User.user_id == uid))
        user_obj = res.scalar_one_or_none()
        if user_obj:
            user_obj.tutor_code = None
            user_obj.subscribe_to  = None
            # НЕ трогаем user_obj.role!
            await session.commit()

    # Предлагаем выбрать новую роль
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Преподаватель")],
            [KeyboardButton(text="Слушатель")],
        ],
        resize_keyboard=True
    )
    await message.answer("Выберите новую роль:", reply_markup=kb)
    await state.set_state(RegStates.choosing_role)
@router.message(Command("register"))
async def cmd_register(message: types.Message):
    # Собираем строку scope-ов через пробел
    scope_str = " ".join(SCOPES)

    # Формируем URL авторизации
    auth_url = (
        "https://oauth.yandex.ru/authorize"
        f"?response_type=token"
        f"&client_id={CLIENT_ID}"
        f"&scope={scope_str}"
    )

    text = (
        "Чтобы выдать боту доступ к вашему Яндекс.Диску:\n\n"
        f"1. Перейдите по ссылке:\n{auth_url}\n\n"
        "2. Разрешите приложению указанные права.\n"
        "3. После редиректа на https://oauth.yandex.ru/verification_code "
        "скопируйте `access_token` из URL (он идёт после `#access_token=`).\n"
        "4. Отправьте боту команду:\n"
        "/token <скопированный_токен>"
    )
    # отключаем парсинг Markdown/HTML — просто текст
    await message.answer(text, parse_mode=None)
