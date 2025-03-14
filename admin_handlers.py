import asyncio
import datetime

from aiogram import types
from aiogram.types import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from users import *
from faq import *
from config import *
from aiogram import Dispatcher
from aiogram import Bot

user_db = UserDB()
faq_db = QuestionAnswerDB()

bot = Bot(token=API_TOKEN)


async def cmd_send_message(message: types.Message):
    if message.from_user.id == 1012078689:  # Проверка, что это администратор
        # Разделяем сообщение по символу '|'
        msg_parts = message.text.split("|")
        print(msg_parts)
        if len(msg_parts) < 3:  # Проверяем, что есть достаточно параметров
            await message.reply("Неверный формат команды. Используйте: |send |id| сообщение")
            return

        target = msg_parts[2].strip()  # ID пользователя или 'all'
        text_message = msg_parts[3].strip()  # Сообщение

        if target == "all":  # Если рассылка всем
            data = user_db.get_id()  # Получаем всех пользователей
            for user_id in data:
                try:
                    await bot.send_message(chat_id=user_id[0], text=f"<b>Важное сообщение!</b>\n\n{text_message}\n\nС уважением, <b>ВОПО Родник</b>🫂💙", parse_mode=ParseMode.HTML)
                    await asyncio.sleep(1)
                except Exception as e:
                    continue
            await bot.send_message(message.from_user.id, text=f"Сообщение отправлено всем пользователям.")
        else:
            if user_db.get_user(target):  # Проверяем, есть ли пользователь с таким ID
                await bot.send_message(message.from_user.id, text=f"Сообщение отправлено пользователю {target}.")
                await bot.send_message(chat_id=target, text=f"<b>Важное сообщение!</b>\n\n{text_message}\n\nС уважением, <b>ВОПО</b> <b>Родник</b>🫂💙", parse_mode=ParseMode.HTML)
            else:
                await bot.send_message(message.from_user.id, text="Пользователь не найден.")
    else:
        await bot.send_message(message.from_user.id, text="У вас нет прав для отправки сообщений.")


from aiogram import types
from aiogram.types import ParseMode

async def cmd_view_questions(message: types.Message):
    if message.from_user.id == 1012078689:  # Проверка на админа
        questions = faq_db.get_all_questions()
        if questions:
            questions_text = "\n".join([f"ID: {q[0]} - Вопрос: {q[1]}" for q in questions])
            await message.answer(f"Список вопросов:\n\n{questions_text}", parse_mode=ParseMode.HTML)
        else:
            await message.answer("Нет доступных вопросов в базе.")

async def cmd_delete_question(message: types.Message):
    if message.from_user.id == 1012078689:  # Проверка на админа
        try:
            question_id = int(message.text.split(" ")[1])
            faq_db.delete_question(question_id)
            await message.answer(f"Вопрос с ID {question_id} удален.")
        except ValueError:
            await message.answer("Пожалуйста, укажите ID вопроса для удаления.")

async def cmd_update_question(message: types.Message):
    if message.from_user.id == 1012078689:  # Проверка на админа
        try:
            parts = message.text.split("|")
            print(parts)
            question_id = int(parts[2])
            new_question = parts[4]
            new_answer = parts[5].lstrip()
            faq_db.update_question_answer(question_id, new_question, new_answer)
            await message.answer(f"Вопрос с ID {question_id} был обновлен.")
        except ValueError:
            await message.answer("Неверный формат. Используйте: |update_question |ID| |Новый вопрос| Новый ответ")


async def cmd_add_question(message: types.Message):
    if message.from_user.id == 1012078689:  # Проверка на админа
        try:
            parts = message.text.split("|")  # Разделяем по '|'
            if len(parts) < 4:  # Проверка на наличие всех параметров
                await message.answer("Неверный формат. Используйте: |add_question |Вопрос| Ответ")
                return

            new_question = parts[2].strip()  # Вопрос
            new_answer = parts[3].strip()  # Ответ

            # Добавляем вопрос и ответ в базу данных
            faq_db.add_question_answer(new_question, new_answer)
            await message.answer(f"Вопрос '{new_question}' с ответом '{new_answer}' был успешно добавлен.")
        except Exception as e:
            await message.answer(f"Произошла ошибка при добавлении вопроса: {e}")
    else:
        await message.answer("У вас нет прав для добавления вопросов.")


async def send_birthday_messages(bot: Bot, user_db: UserDB):
    today = datetime.date.today().strftime('%d.%m')  # Получаем текущую дату в формате DD.MM
    users = user_db.get_all_users()  # Получаем всех пользователей с их данными

    for user in users:
        try:
            user_id, first_name, last_name, username, birthdate, _ = user  # Извлекаем все данные из кортежа
            if birthdate and birthdate != "NULL":  # Проверяем, что дата рождения существует и не NULL
                # Сравниваем день и месяц
                if birthdate == today:
                    message = f"""
Привет! Если меня не обманул Telegram, то у кое-кого сегодня день рождения! 🎉\n
В Африке слоники живут, они до неба достают и поднимают хвостики! 🐘
\nС Днем Рождения, <b>{first_name}!</b> 🎂
Желаем тебе море счастья, здоровья, удачи и ярких эмоций! Пусть сбудутся все мечты, а впереди будет только самое лучшее! 🎁
С любовью и наилучшими пожеланиями, <b>Родник</b>! 🫂💙
                        """
                    # Отправляем поздравление с Днем Рождения
                    await bot.send_message(user_id, message, parse_mode=ParseMode.HTML)
        except Exception as e:
            print(f"Ошибка при обработке пользователя {user}: {e}")

async def bd(message: types.Message):
    if message.from_user.id == 1012078689:
        f = open("users.db", "rb")
        await message.reply_document(f)
        ss = open("questions_answers.db", "rb")
        await message.reply_document(ss)



async def norm_dr(message: types.Message):
    print("МЫ ВНУТРИ!")
    if message.from_user.id == 1012078689:
        try:
            parts = message.text.split("|")  # Разделяем по '|'
            print(parts)
            if len(parts) < 4:  # Проверка на наличие всех параметров
                await message.answer("Неверный формат. Используйте: |др |id| data")
                return
            user_id = parts[2]
            data = parts[3].strip()
            user_db.set_dr(user_id, data)
        except Exception as e:
                print(f"я хуй знает что легло, ладно наебал - вот {e}")



def register_admin_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_send_message, commands=['send'], commands_prefix='|')
    dp.register_message_handler(cmd_view_questions, commands=['view_questions'])
    dp.register_message_handler(cmd_delete_question, commands=['delete_question'])
    dp.register_message_handler(cmd_update_question, commands=['update_question'], commands_prefix='|')
    dp.register_message_handler(cmd_add_question, commands=['add_question'], commands_prefix='|')
    dp.register_message_handler(bd, commands=['киньБД'], commands_prefix='/')
    dp.register_message_handler(norm_dr, commands=['date'], commands_prefix='|')

