'''
Тут инфа о боте и админах надо переделать на os.getenv
'''
import os
from dotenv import load_dotenv
from aiogram import Bot


load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=API_TOKEN)


if not API_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения!")

YOUR_ADMIN_ID = 1012078689 