import asyncio
from telegram import Bot

TOKEN = '5352353471:AAEeZ4W69c2n-25pN7BDeai-mVV16N0k8Pk'

bot = Bot(token=TOKEN)

chat_id = 770629236  #  user_id == chat_id???????????????????

async def get_info():
    chat_info = await bot.get_chat(chat_id)
    print(f"Информация о чате: {chat_info}")

    if hasattr(chat_info, 'birthdate') and chat_info.birthdate:
        print(f"Дата рождения пользователя: {chat_info.birthdate}")
    else:
        print("Дата рождения пользователя не указана.")

if __name__ == '__main__':
    asyncio.run(get_info())
