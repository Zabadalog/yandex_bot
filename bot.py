# bot.py
import asyncio, logging, os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

from models import init_db
from src.handlers import registration_router, status_router, yandex_router, tracking_router, help_router

logging.basicConfig(level=logging.INFO)
load_dotenv()

async def main():
    await init_db()
    bot = Bot(token=os.getenv("BOT_TOKEN"), default=DefaultBotProperties(parse_mode="HTML"))
    dp  = Dispatcher(storage=MemoryStorage())

    # подключаем все подроутеры
    dp.include_router(registration_router)
    dp.include_router(status_router)
    dp.include_router(yandex_router)
    dp.include_router(tracking_router)
    dp.include_router(help_router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
