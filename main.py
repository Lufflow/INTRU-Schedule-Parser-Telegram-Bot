# main.py

import logging
import os
import asyncio
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from database import Database
from aiogram import Bot, Dispatcher
from handlers import basic_handlers, group_handlers
from parser_modules.async_request import requester
from parser_modules.auto_update import auto_update_task
from logging_config import setup_logging

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("Токен не найден. Проверь .env файл")


db = Database("users.db")
storage = MemoryStorage()
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=storage)
logger = setup_logging()


async def on_shutdown(bot: Bot, dp: Dispatcher):
    logger.info("⏹️  Остановка бота...")

    try:
        await requester.close()
    except Exception as e:
        logger.warning(f"Ошибка при закрытии requester: {e}")

    try:
        await storage.close()
    except Exception as e:
        logger.warning(f"Ошибка при закрытии storage: {e}")

    try:
        await bot.session.close()
    except Exception as e:
        logger.warning(f"Ошибка при закрытии session: {e}")

    logger.info("✅ Ресурсы закрыты")


async def main():
    logger.info("🚀 Запуск бота...")

    dp.shutdown.register(on_shutdown)
    dp.include_router(group_handlers.router)
    dp.include_router(basic_handlers.router)
    bot.db = db

    asyncio.create_task(auto_update_task(interval_hours=24))
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("⚠️  Бот остановлен пользователем (Ctrl+C)")
