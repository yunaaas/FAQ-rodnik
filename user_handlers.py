from aiogram import types
from aiogram.types import ParseMode
from keyboards import *  # Импортируем метод для клавиатуры
from users import * 
from faq import *
from states import *
from aiogram.dispatcher import FSMContext

user_db = UserDB()
faq_db = QuestionAnswerDB()


async def process_faq(callback_query: types.CallbackQuery, state: FSMContext):
    # Отправляем сообщение с клавиатурой вопросов (редактируем текущее сообщение)
    await callback_query.answer()

    # Получаем клавиатуру с вопросами
    keyboard = get_questions_keyboard()

    # Редактируем текущее сообщение
    await callback_query.message.edit_text("<b>Приветствуем!</b> \nЗдесь собраны самые популярные вопросы, которые нам часто задают. \n\nЕсли у вас есть вопрос, на который Вы не нашли ответа, не стесняйтесь — <i>задайте его</i>, и мы обязательно поможем! 😊", reply_markup=keyboard, parse_mode=ParseMode.HTML)



async def cmd_start(message: types.Message):
    user = message.from_user

    # Проверяем и добавляем пользователя в базу данных, если его нет
    user_db.add_user_if_not_exists(user.id, user.first_name, user.last_name, user.username)
    # Получаем инлайн клавиатуру
    keyboard = get_start_keyboard()
    id = message.chat.id
    # Отправляем сообщение с меню
    await message.answer(f"Привет! Вот все доступные действия: {id}" , reply_markup=keyboard)





async def process_question(callback_query: types.CallbackQuery):
    question = callback_query.data[len("question_"):]

    # Получаем ответ на этот вопрос из базы данных
    answer = faq_db.get_answer(question)

    # Создаем клавиатуру с кнопкой "Назад"
    back_button = InlineKeyboardButton(text="🔙 Назад", callback_data="faq")
    keyboard = InlineKeyboardMarkup().add(back_button)

    # Отправляем уведомление
    await callback_query.answer("Мы нашли ответ на ваш вопрос!")  # Уведомление

    # Редактируем предыдущее сообщение
    await callback_query.message.edit_text(
        text=f"{answer}",  # Ответ с форматированием
        parse_mode=ParseMode.HTML,  # HTML-разметка
        reply_markup=keyboard  # Добавляем клавиатуру с кнопкой "Назад"
    )




async def ask_own_question(callback_query: types.CallbackQuery, state: FSMContext):
    # Отправляем сообщение пользователю, что он может задать вопрос
    await callback_query.message.edit_text(
        "Опишите ваш вопрос или прикрепите фото/видео. Родник увидит его и ответит как можно скорее! 💙💌"
    )

    # Добавляем кнопку "Я нажал сюда случайно", которая перенесет обратно
    cancel_button = InlineKeyboardButton(text="🙈 Я нажал сюда случайно", callback_data="cancel_question")
    keyboard = InlineKeyboardMarkup().add(cancel_button)

    # Обновляем клавиатуру в сообщении
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)

    # Устанавливаем состояние только при получении вопроса
    await state.set_state(UserStates.asking_question)  # Устанавливаем состояние для обработки вопроса




async def cancel_question(callback_query: types.CallbackQuery, state: FSMContext):
    # Завершаем состояние и возвращаем в меню вопросов
    await callback_query.message.edit_text("<b>Приветствуем!</b> \nЗдесь собраны самые популярные вопросы, которые нам часто задают. \n\nЕсли у вас есть вопрос, на который Вы не нашли ответа, не стесняйтесь — <i>задайте его</i>, и мы обязательно поможем! 😊", reply_markup=get_questions_keyboard(), parse_mode=ParseMode.HTML)
    await state.finish()  # Завершаем состояние



async def handle_question(message: types.Message, state: FSMContext):
    if await state.get_state() == UserStates.asking_question.state:
        user = message.from_user

        # Пересылаем сообщение администратору
        await message.forward(chat_id=1012078689)  # ID администратора
        
        # Отправляем дополнительное сообщение с информацией о пользователе
        await message.bot.send_message(
            chat_id=1012078689,
            text=f"ВОПРОС!!!!\n\nОт: {user.first_name} {user.last_name} @{user.username}, <code>!send !{user.id}!</code>",
            parse_mode=ParseMode.HTML  # Чтобы использовать HTML-теги в сообщении
        )

        # Отправляем ответ пользователю
        await message.answer("Ваш вопрос принят! Мы ответим вам как можно скорее. 💙💌", reply_markup=get_start_keyboard())

        # Завершаем состояние
        await state.finish()



async def process_back_to_main(callback_query: types.CallbackQuery):
    # Получаем основную клавиатуру
    keyboard = get_start_keyboard()

    # Редактируем текущее сообщение
    await callback_query.answer()
    await callback_query.message.edit_text("Привет! Вот все доступные вопросы:", reply_markup=keyboard)


async def process_offer(callback_query: types.CallbackQuery, state: FSMContext):
    # Отправляем сообщение пользователю, что он может сделать предложение
    await callback_query.message.edit_text(
        "Опишите ваше предложение или прикрепите файл. Мы учтем все ваши идеи! 💡"
    )

    # Добавляем кнопку "Я нажал сюда случайно", которая перенесет обратно
    back_button = InlineKeyboardButton(text="🙈 Я нажал сюда случайно", callback_data="offer_error")
    keyboard = InlineKeyboardMarkup().add(back_button)

    # Обновляем клавиатуру
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)

    # Ожидаем, что пользователь напишет свое предложение
    await state.set_state(UserStates.offer_post)  # Используем это же состояние для обработки предложений

async def handle_offer(message: types.Message, state: FSMContext):
    if await state.get_state() == UserStates.offer_post.state:
        user = message.from_user

        # Пересылаем сообщение администратору
        await message.forward(chat_id=1012078689)  # ID администратора
        
        # Отправляем дополнительное сообщение с информацией о пользователе
        await message.bot.send_message(
            chat_id=1012078689,
            text=f"ПРЕДЛОЖКА!!! \n\nОт: {user.first_name} {user.last_name} @{user.username}, <code>!send !{user.id}!</code>",
            parse_mode=ParseMode.HTML  # Чтобы использовать HTML-теги в сообщении
        )

        # Отправляем ответ пользователю
        await message.answer("Ваша идея получена! Ожидайте, может быть она скоро появится в нашей группе!💙", reply_markup=get_start_keyboard())

        # Завершаем состояние
        await state.finish()

async def process_cancel_offer(callback_query: types.CallbackQuery, state: FSMContext):
    # Завершаем состояние и возвращаем пользователя в главное меню
    await callback_query.message.edit_text("Вы вернулись в главное меню.", reply_markup=get_start_keyboard())
    await state.finish()  # Завершаем состояние


async def process_social(callback_query: types.CallbackQuery):
    # Ответ на нажатие кнопки
    await callback_query.answer()  # Откликаемся на нажатие

    # Отправляем сообщение с клавиатурой социальных сетей
    await callback_query.message.edit_text(
        "Вот наши социальные сети и сайт. \nВы можете перейти по ссылкам, нажав на кнопки!",
        reply_markup=get_social_networks_keyboard()  # Возвращаем клавиатуру с соц. сетями
    )

async def process_parents(callback_query: types.CallbackQuery):
    # Ответ на нажатие кнопки
    await callback_query.answer()

    # Отправляем сообщение с заглушкой
    await callback_query.message.edit_text(
        "Этот раздел ещё не готов. Мы скоро добавим полезную информацию для родителей! 🙏",
        reply_markup=get_parents_placeholder_keyboard()  # Добавляем кнопку "Назад"
    )


def register_user_handlers(dp):
    dp.register_message_handler(cmd_start, commands=['start'])
    dp.register_callback_query_handler(process_question, lambda c: c.data and c.data.startswith('question_'))
    dp.register_callback_query_handler(process_faq, lambda c: c.data == "faq")
    dp.register_callback_query_handler(process_back_to_main, lambda c: c.data == "back_to_main")
    dp.register_callback_query_handler(cancel_question, lambda c: c.data == "cancel_question", state=UserStates.asking_question)
    dp.register_message_handler(handle_question, content_types=["any"], state=UserStates.asking_question)
    dp.register_callback_query_handler(ask_own_question, lambda c: c.data == "ask_own_question")
    dp.register_message_handler(handle_offer, content_types=["any"], state=UserStates.offer_post)
    dp.register_callback_query_handler(process_cancel_offer, lambda c: c.data == "offer_error", state=UserStates.offer_post)
    dp.register_callback_query_handler(process_offer, lambda c: c.data == "offer")
    dp.register_callback_query_handler(process_social, lambda c: c.data == "social")
    dp.register_callback_query_handler(process_parents, lambda c: c.data == "parrents")