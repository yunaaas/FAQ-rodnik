from aiogram import types
from aiogram.types import ParseMode
from keyboards import *  # Импортируем метод для клавиатуры
from users import * 
from faq import *
from states import *
from aiogram.dispatcher import FSMContext
from api import *
from config import API_TOKEN

api_key = API_TOKEN


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

    # Получаем день рождения пользователя, если он есть
    birthdate = await get_user_birthdate(api_key, user.id)

    # Проверяем и добавляем пользователя в базу данных, если его нет
    user_db.add_user_if_not_exists(user.id, user.first_name, user.last_name, user.username, birthdate)

    # Получаем инлайн клавиатуру
    keyboard = get_start_keyboard()

    # Отправляем сообщение с меню
    await message.answer(f"Привет! Вот все доступные действия:", reply_markup=keyboard)





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
            text=f"ВОПРОС!!!!\n\nОт: {user.first_name} {user.last_name} @{user.username}, <code>|send |{user.id}|</code>",
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
            text=f"ПРЕДЛОЖКА!!! \n\nОт: {user.first_name} {user.last_name} @{user.username}, <code>|send |{user.id}|</code>",
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

    # Отправляем сообщение с клавиатурой
    await callback_query.message.edit_text(
        "Этот раздел будет пополняться по мере приближения дат смены, мы оповестим когда будут обновления. 🙏",
        reply_markup=get_parents_keyboard_with_back()  # Добавляем клавиатуру с кнопками
    )

async def process_program(callback_query: types.CallbackQuery):
    # Отправляем уведомление
    await callback_query.answer("Мы нашли ответ на ваш вопрос!")  # Уведомление

    # Сообщение с информацией о программе лагеря
    message = f"""
<b>⚡️ Областная профильная смена для одаренных старшеклассников</b>  
<i>«Искатель» (возраст 14+)</i>

<b>⚡️ Министерство образования Владимирской области</b> ежегодно проводит профильную смену для одаренных старшеклассников <i>«Искатель»</i> дважды в год – в августе и декабре.  

<b>⚡️ Основной целью смены является</b> личностное развитие подростков и обогащение знаний в выбранной предметной области в условиях временного детского коллектива и воспитательного пространства лагеря. 

<b>⚡️ Каждая профильная смена имеет свое название,</b> отражающее игровую модель смены. На всех сменах в приоритете наполнение и смысловое содержание. Здесь школьники познают науку, размышляют о будущем, учатся дружить, обретают поддержку и доверие взрослых. <i>Девиз лагеря</i> -  «Гореть самим и зажигать других». 

<b>⚡️ Совместно с комиссарами Владимирского областного педагогического отряда «Родник»</b> разрабатывается образовательная и досуговая программа, которая включает в себя теоретические и практические занятия по различным направлениям деятельности, а также сюжетно-ролевые игры, интеллектуальные и конкурсные шоу-программы, театрализованные вечерние творческие дела.   
"""

    # Создаем клавиатуру с кнопкой "Назад"
    back_button = InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_parents")
    keyboard = InlineKeyboardMarkup().add(back_button)

    # Редактируем предыдущее сообщение
    await callback_query.message.edit_text(
        text=message,  # Сообщение о программе лагеря
        parse_mode=ParseMode.HTML,  # HTML-разметка
        reply_markup=keyboard  # Добавляем кнопку "Назад"
    )




async def process_schools(callback_query: types.CallbackQuery):
    # Ответ на нажатие кнопки
    await callback_query.answer("Мы нашли ответ на ваш вопрос!")

    # Сообщение с информацией о профильных школах
    message = f"""
<b>⚡️ На занятиях в профильных школах</b> ребята вместе с педагогами говорят о защите персональных данных в сети Интернет, спорят о современном искусстве, знакомятся с особенностями предпринимательской деятельности, рассуждают об истории вооружения и иностранных языков, касаются вопросов экологии и биологии, делятся опытом реализации добровольческих проектов.

<b>⚡️ Мастер-классы искателей</b> для своих сверстников всегда не менее интересны: подготовка к олимпиадам, инвестирование, математика, живопись, театр, игра на гитаре и др. 🎸🎨📚
"""


    # Создаем клавиатуру с кнопкой "Назад"
    back_button = InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_parents")
    keyboard = InlineKeyboardMarkup().add(back_button)

    # Редактируем предыдущее сообщение
    await callback_query.message.edit_text(
        text=message,  # Сообщение о профильных школах
        parse_mode=ParseMode.HTML,  # HTML-разметка
        reply_markup=keyboard  # Добавляем кнопку "Назад"
    )


async def process_teachers(callback_query: types.CallbackQuery):
    # Ответ на нажатие кнопки
    await callback_query.answer("Мы нашли ответ на ваш вопрос!")

    # Сообщение с информацией о педагогическом составе
    message = f"""
<b>⚡️ Педагогический состав Владимирского областного педагогического отряда «Родник»</b> включает в себя высококвалифицированных специалистов с многолетним опытом работы. Каждый педагог имеет соответствующее образование и обязательный <i>сертификат вожатого</i>. 📜

<b>⚡️ Педагоги</b> проходят регулярные курсы повышения квалификации и участвуют в методических объединениях и семинарах. 🧑‍🏫

Кроме того, педагоги отряда активно участвуют в подготовке и проведении мастер-классов, а также в создании образовательных и досуговых программ для старшеклассников. 🎨🎭

Комиссары «Родника» работают в тесном сотрудничестве с <b>Владимирским институтом развития образования</b> и <b>Министерством образования Владимирской области</b>, что подтверждает высокий уровень их профессионализма и готовности к инновациям в педагогической деятельности. 🏫

Образовательный процесс в лагере «Искатель» строится на основе индивидуального подхода и практического опыта, что позволяет каждому ребенку раскрыть свой потенциал, развивать творческие и интеллектуальные способности. 🌱
"""


    # Создаем клавиатуру с кнопкой "Назад"
    back_button = InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_parents")
    keyboard = InlineKeyboardMarkup().add(back_button)

    # Редактируем предыдущее сообщение
    await callback_query.message.edit_text(
        text=message,  # Сообщение о педагогическом составе
        parse_mode=ParseMode.HTML,  # HTML-разметка
        reply_markup=keyboard  # Добавляем кнопку "Назад"
    )

async def process_back_to_parents(callback_query: types.CallbackQuery):
    # Ответ на нажатие кнопки "Назад"
    await callback_query.answer("Вы вернулись назад!")

    # Возвращаем пользователя в раздел для родителей
    await callback_query.message.edit_text(
        "Этот раздел будет пополняться по мере приближения дат смены, мы оповестим, когда будут обновления. 🙏",
        reply_markup=get_parents_keyboard_with_back()  # Возвращаем клавиатуру для родителей
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
    dp.register_callback_query_handler(process_program, lambda c: c.data == "parents_program")
    dp.register_callback_query_handler(process_schools, lambda c: c.data == "parents_schools")
    dp.register_callback_query_handler(process_teachers, lambda c: c.data == "parents_teachers")
    dp.register_callback_query_handler(process_back_to_parents, lambda c: c.data == "back_to_parents")