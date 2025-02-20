import logging
from aiogram import Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import bot
from user_handlers import *  # Импортируем регистрацию хендлеров

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Создание диспетчера
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

register_user_handlers(dp)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
