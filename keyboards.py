from faq import *
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

faq_db = QuestionAnswerDB() 


def get_start_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.row(
        InlineKeyboardButton(text="📩 Предложка", callback_data="offer"),
        InlineKeyboardButton(text="🧸 Для родителей", callback_data="parrents")
    )
    
    # Добавляем кнопку для FAQ
    keyboard.add(InlineKeyboardButton(text="💬 Часто задаваемые вопросы", callback_data="faq"))
    
    # Добавляем кнопку для социальных сетей
    keyboard.add(InlineKeyboardButton(text="🌐 Наши социальные сети", callback_data="social"))
    
    return keyboard



def get_questions_keyboard():
    # Получаем все вопросы с их id из базы данных
    questions = faq_db.get_all_questions()

    # Два URL для добавления кнопок с внешними ссылками
    url_buttons = [
        {"text": "🧑‍🏫 Про Родник!", "url": "https://родник1978.рф/"},
        {"text": "☀️ Наши Летние смены.", "url": "https://родник1978.рф/summer"},
        {"text": "❄️ Наши Зимние смены.", "url": "https://родник1978.рф/winter"}
    ]
    
    # Создаем инлайн клавиатуру
    keyboard = InlineKeyboardMarkup(row_width=2)  # Устанавливаем 2 кнопки в строку для коротких вопросов

    current_row = []  # Список для текущей строки кнопок

    # Проходим по всем вопросам и добавляем их в клавиатуру
    for question_id, question in questions:
        # Если вопрос длинный, добавляем его по одному в строку
        if len(question) > 15:  # Для длинных вопросов, например, более 30 символов
            if current_row:  # Если текущая строка не пуста, добавляем её в клавиатуру
                keyboard.add(*current_row)
            # Создаем кнопку для длинного вопроса и добавляем её на новую строку
            button = InlineKeyboardButton(text=question, callback_data=f"question_{question_id}")
            keyboard.add(button)
            current_row = []  # Очищаем текущую строку для следующего набора кнопок
        else:
            # Добавляем кнопку в текущую строку (для коротких вопросов)
            button = InlineKeyboardButton(text=question, callback_data=f"question_{question_id}")
            current_row.append(button)

            # Если в строке уже 2 кнопки (для коротких вопросов), добавляем её в клавиатуру
            if len(current_row) == 2:
                keyboard.add(*current_row)
                current_row = []  # Очищаем текущую строку для следующего набора кнопок

    # Добавляем оставшиеся кнопки в случае, если их меньше 2 на последней строке
    if current_row:
        keyboard.add(*current_row)

    # Добавляем кнопки с URL в конец
    for url_button in url_buttons:
        keyboard.add(InlineKeyboardButton(text=url_button["text"], url=url_button["url"]))

    # Добавляем кнопку "Задать свой вопрос!"
    keyboard.add(InlineKeyboardButton(text="❓Задать свой вопрос!", callback_data="ask_own_question"))

    # Добавляем кнопку "Назад", которая вернет пользователя в главное меню
    keyboard.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main"))

    return keyboard



# Клавиатура для сообщения об ошибке
def get_bug_report_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main"))
    return keyboard

def get_social_networks_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)

    # Кнопки для социальных сетей и сайтов
    keyboard.add(
        InlineKeyboardButton(text="🔴 Искатель ВКонтакте", url="https://vk.com/pro.iskatel"),
        InlineKeyboardButton(text="🔵 Родник ВКонтакте", url="https://vk.com/vporodnik"),
        InlineKeyboardButton(text="🌐 Сайт Родника", url="https://родник1978.рф/"),
        InlineKeyboardButton(text="📱 Искатель в Телеграмм", url="https://t.me/proiskatel")
    )
    keyboard.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main"))
    return keyboard

def get_parents_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)

    # Кнопки с нужной информацией
    keyboard.add(
        InlineKeyboardButton(text="📜 Правила лагеря", callback_data="rules"),
        InlineKeyboardButton(text="👨‍👩‍👧‍👦 Ответственные за детей", callback_data="responsible"),
        InlineKeyboardButton(text="🛡️ Безопасность в лагере", callback_data="safety"),
        InlineKeyboardButton(text="📅 Расписание мероприятий", callback_data="schedule"),
        InlineKeyboardButton(text="📞 Контакты для родителей", callback_data="contacts")
    )

    return keyboard



def get_parents_placeholder_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Кнопка "Назад", которая возвращает в главное меню
    back_button = InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")
    keyboard.add(back_button)
    
    return keyboard