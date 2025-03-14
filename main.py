import logging
import asyncio

from aiogram import Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import bot
from user_handlers import *  # Импортируем регистрацию хендлеров
from admin_handlers import *
from apscheduler.schedulers.asyncio import AsyncIOScheduler
# Настройка логирования
logging.basicConfig(level=logging.INFO)
from aiogram import Bot
from config import API_TOKEN
# Создание диспетчера
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
bot = Bot(token=API_TOKEN)


async def schedule_birthday_task(bot: Bot, user_db: UserDB):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_birthday_messages, 'cron', hour=10, minute=0, args=[bot, user_db])
    scheduler.start()

async def on_start():
    await schedule_birthday_task(bot, user_db)

register_user_handlers(dp)
register_admin_handlers(dp)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(on_start())
    executor.start_polling(dp, skip_updates=True)
