from aiogram import types
from aiogram.types import ParseMode, InputFile  
from keyboards import *  # Импортируем метод для клавиатуры
from users import * 
from faq import *
from states import *
from aiogram.dispatcher import FSMContext
from api import *
from config import API_TOKEN
import os, random
from datetime import datetime
api_key = API_TOKEN


user_db = UserDB()
faq_db = QuestionAnswerDB()



from greetings import greetings_db
from urllib.parse import quote
from aiogram.types import InputFile

# Константы
BOT_USERNAME = "@proiskatel_bot"  # Замените на username вашего бота

async def process_start_greetings(callback_query: types.CallbackQuery):
    """Обработчик кнопки 'Начать принимать поздравления'"""
    user = callback_query.from_user
    
    # Сохраняем информацию о пользователе
    greetings_db.save_or_update_user(
        user.id,
        user.first_name,
        user.last_name,
        user.username
    )
    
    # Создаем или получаем ссылку пользователя
    link_code = greetings_db.create_or_get_link(
        user.id,
        user.first_name,
        user.last_name,
        user.username
    )
    
    # Формируем ссылку
    bot_link = f"https://t.me/{BOT_USERNAME}?start=greet_{link_code}"
    
    # Создаем клавиатуру
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(
            text="🔙 Назад в меню",
            callback_data="back_to_main"
        )
    )
    
    # Удаляем старое сообщение с кнопками
    await callback_query.message.delete()
    
    # Отправляем ТОЛЬКО ОДНО новое сообщение
    await callback_query.message.answer(
        f"🎉 <b>Ваша персональная ссылка для поздравлений готова!</b>\n\n"
        f"📎 <b>Ссылка:</b>\n"
        f"<code>{bot_link}</code>\n\n"
        f"💡 <i>Разместите эту ссылку в соцсетях, канале или отправьте друзьям.\n"
        f"Когда кто-то перейдет по ней и отправит сообщение, вы получите уведомление!</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
        disable_web_page_preview=True
    )
    
    await callback_query.answer()

    
    # # Отправляем новое сообщение вместо редактирования старого
    # await callback_query.message.answer(
    #     f"🎉 <b>Ваша персональная ссылка для поздравлений готова!</b>\n\n"
    #     f"📎 <b>Ссылка:</b>\n"
    #     f"<code>{bot_link}</code>\n\n"
    #     f"💡 <i>Разместите эту ссылку в соцсетях, канале или отправьте друзьям.\n"
    #     f"Когда кто-то перейдет по ней и отправит сообщение, вы получите уведомление!</i>",
    #     parse_mode=ParseMode.HTML,
    #     reply_markup=keyboard,
    #     disable_web_page_preview=True
    # )
    
    # # Удаляем старое сообщение с кнопками (опционально)
    # await callback_query.message.delete()
    # await callback_query.answer()

async def process_copy_link(callback_query: types.CallbackQuery):
    """Обработчик копирования ссылки"""
    link_code = callback_query.data.replace("copy_link_", "")
    bot_link = f"https://t.me/{BOT_USERNAME}?start=greet_{link_code}"
    
    # Отправляем ссылку в чат для легкого копирования
    await callback_query.message.answer(
        f"📋 <b>Скопируйте ссылку:</b>\n\n"
        f"<code>{bot_link}</code>\n\n"
        f"👇 Просто нажмите на текст выше, чтобы скопировать!",
        parse_mode=ParseMode.HTML
    )
    
    await callback_query.answer("✅ Ссылка отправлена!")

async def cmd_start_with_greeting(message: types.Message, state: FSMContext):
    """Обработчик команды /start с параметром для поздравлений"""
    args = message.get_args()
    
    if args and args.startswith("greet_"):
        link_code = args.replace("greet_", "")
        
        # Получаем владельца ссылки
        owner_id = greetings_db.get_user_by_link(link_code)
        
        if not owner_id:
            await message.answer(
                "❌ <b>Ссылка недействительна или отключена</b>\n\n"
                "Возможно, владелец ссылки деактивировал прием поздравлений.",
                parse_mode=ParseMode.HTML,
                reply_markup=get_start_keyboard()
            )
            return
        
        # Сохраняем данные
        await state.update_data(
            greeting_owner=owner_id,
            greeting_link=link_code,
            sender_id=message.from_user.id,
            sender_first=message.from_user.first_name,
            sender_last=message.from_user.last_name,
            sender_username=message.from_user.username
        )
        
        # Спрашиваем про анонимность с обновленным текстом
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton(text="👤 Анонимно", callback_data="anon_yes"),
            InlineKeyboardButton(text="📢 Публично", callback_data="anon_no"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_greeting")
        )
        
        await message.answer(
            "🎉 <b>Вы хотите отправить поздравление!?</b>\n\n"
            "❓ <b>Выберите тип отправки:</b>\n",
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
        
        await state.set_state(UserStates.choosing_anonymity)
        
    else:
        # Обычный запуск бота
        await cmd_start(message)

async def process_anonymity_choice(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработка выбора анонимности"""
    is_anonymous = (callback_query.data == "anon_yes")
    
    await state.update_data(is_anonymous=is_anonymous)
    
    if is_anonymous:
        anon_text = "✅ Вы выбрали <b>анонимную</b> отправку"
    else:
        anon_text = "❌ Вы выбрали <b>неанонимную</b> отправку"
    
    await callback_query.message.edit_text(
        f"{anon_text}\n\n"
        f"💌 <b>Теперь отправьте ваше поздравление!</b>\n"
        f"Это может быть:\n"
        f"• Текстовое сообщение\n"
        f"• Фото 📸\n"
        f"• Видео 🎥\n"
        f"• Стикер или GIF\n"
        f"• Голосовое сообщение 🎤\n\n"
        f"<i>Отправьте сообщение, и оно будет доставлено получателю!</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton(text="🔙 Отмена", callback_data="cancel_greeting")
        )
    )
    
    await state.set_state(UserStates.sending_greeting)
    await callback_query.answer()

async def handle_greeting_message(message: types.Message, state: FSMContext):
    """Обработчик сообщений-поздравлений"""
    if await state.get_state() != UserStates.sending_greeting.state:
        return
    
    data = await state.get_data()
    owner_id = data.get('greeting_owner')
    link_code = data.get('greeting_link')
    is_anonymous = data.get('is_anonymous', False)
    
    if not owner_id or not link_code:
        await message.answer(
            "❌ Произошла ошибка. Попробуйте снова.",
            reply_markup=get_start_keyboard()
        )
        await state.finish()
        return
    
    # Создаем объект отправителя для БД
    class Sender:
        def __init__(self, msg):
            self.id = msg.from_user.id
            self.first_name = msg.from_user.first_name
            self.last_name = msg.from_user.last_name
            self.username = msg.from_user.username
    
    sender = Sender(message)
    
    # Определяем тип и содержимое
    message_text = message.text or message.caption or ""
    media_type = None
    media_file_id = None
    
    if message.photo:
        media_type = "photo"
        media_file_id = message.photo[-1].file_id
        if not message.caption:
            message_text = "📸 Фото без подписи"
    elif message.video:
        media_type = "video"
        media_file_id = message.video.file_id
        if not message.caption:
            message_text = "🎥 Видео без описания"
    elif message.animation:
        media_type = "gif"
        media_file_id = message.animation.file_id
        message_text = message.caption or "🎭 GIF-анимация"
    elif message.sticker:
        media_type = "sticker"
        media_file_id = message.sticker.file_id
        message_text = f"🎨 Стикер: {message.sticker.emoji if message.sticker.emoji else 'без emoji'}"
    elif message.voice:
        media_type = "voice"
        media_file_id = message.voice.file_id
        message_text = "🎤 Голосовое сообщение"
    elif message.video_note:
        media_type = "video_note"
        media_file_id = message.video_note.file_id
        message_text = "📹 Кружочек (видеосообщение)"
    elif message.audio:
        media_type = "audio"
        media_file_id = message.audio.file_id
        performer = message.audio.performer or "Неизвестный исполнитель"
        title = message.audio.title or "Неизвестный трек"
        message_text = f"🎵 Аудио: {performer} - {title}"
    elif message.document:
        media_type = "document"
        media_file_id = message.document.file_id
        file_name = message.document.file_name or "Документ"
        message_text = f"📄 Документ: {file_name}"
    elif message.text:
        media_type = "text"
        message_text = message.text
    
    # Сохраняем в БД (всегда сохраняем полные данные отправителя)
    greeting_id = greetings_db.save_greeting(
        link_code=link_code,
        owner_user_id=owner_id,
        sender=sender,
        is_anonymous=is_anonymous,
        message_text=message_text,
        media_type=media_type,
        media_file_id=media_file_id
    )
    
    # Формируем имя отправителя для получателя
    if is_anonymous:
        sender_display = "👤 <b>Анонимный отправитель</b>"
    else:
        sender_display = f"👤 <b>{message.from_user.first_name}"
        if message.from_user.last_name:
            sender_display += f" {message.from_user.last_name}"
        sender_display += "</b>"
        if message.from_user.username:
            sender_display += f"\n📱 @{message.from_user.username}"
    
    # Формируем уведомление для владельца
    notification = (
        f"🎉 <b>Новое поздравление!</b>\n\n"
        f"{sender_display}\n\n"
        f"💬 <b>Сообщение:</b>\n{message_text}\n\n"
        f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    
    # Отправляем уведомление владельцу
    try:
        # Отправляем в зависимости от типа медиа
        if media_type == "photo" and media_file_id:
            await message.bot.send_photo(
                chat_id=owner_id,
                photo=media_file_id,
                caption=notification[:1024],  # Ограничение на длину caption
                parse_mode=ParseMode.HTML
            )
        elif media_type == "video" and media_file_id:
            await message.bot.send_video(
                chat_id=owner_id,
                video=media_file_id,
                caption=notification[:1024],
                parse_mode=ParseMode.HTML
            )
        elif media_type == "gif" and media_file_id:
            await message.bot.send_animation(
                chat_id=owner_id,
                animation=media_file_id,
                caption=notification[:1024],
                parse_mode=ParseMode.HTML
            )
        elif media_type == "sticker" and media_file_id:
            # Сначала отправляем стикер
            await message.bot.send_sticker(
                chat_id=owner_id,
                sticker=media_file_id
            )
            # Потом отдельно уведомление
            await message.bot.send_message(
                chat_id=owner_id,
                text=notification,
                parse_mode=ParseMode.HTML
            )
        elif media_type in ["voice", "video_note", "audio"] and media_file_id:
            # Для голосовых и аудио
            await message.bot.send_voice(
                chat_id=owner_id,
                voice=media_file_id,
                caption=notification[:1024],
                parse_mode=ParseMode.HTML
            )
        elif media_type == "document" and media_file_id:
        # Документ
            await message.bot.send_document(
                chat_id=owner_id,
                document=media_file_id,
                caption=notification[:1024],
                parse_mode=ParseMode.HTML
            )    
        else:
            # Просто текст
            await message.bot.send_message(
                chat_id=owner_id,
                text=notification,
                parse_mode=ParseMode.HTML
            )
        
        # Добавляем кнопку для ответа
        reply_keyboard = InlineKeyboardMarkup().add(
            InlineKeyboardButton(
                text="💬 Ответить отправителю",
                callback_data=f"reply_to_sender_{message.from_user.id}"
            )
        )
        await message.bot.send_message(
            chat_id=owner_id,
            text="👇 Вы можете ответить отправителю, нажав кнопку ниже:",
            reply_markup=reply_keyboard
        )
        
    except Exception as e:
        print(f"Ошибка при отправке уведомления владельцу: {e}")
        # Пробуем отправить хотя бы текстовое уведомление
        try:
            await message.bot.send_message(
                chat_id=owner_id,
                text=f"🎉 Новое поздравление! (не удалось загрузить медиа)\n\n{notification}",
                parse_mode=ParseMode.HTML
            )
        except:
            pass
    
    # Благодарим отправителя и предлагаем его ссылку
    await message.answer(
        "✅ <b>Спасибо за ваше поздравление!</b>\n\n"
        "Ваше сообщение успешно доставлено получателю. 🎁\n\n"
        "👇 <b>Хотите тоже получать поздравления?</b>\n"
        "Нажмите кнопку ниже, чтобы получить свою персональную ссылку!",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton(
                text="🎉 Начать получать поздравления",
                callback_data="start_greetings_from_message"
            )
        )
    )
    
    await state.finish()

async def process_start_greetings_from_message(callback_query: types.CallbackQuery):
    """Быстрый старт получения поздравлений после отправки"""
    await process_start_greetings(callback_query)

async def process_cancel_greeting(callback_query: types.CallbackQuery, state: FSMContext):
    """Отмена отправки поздравления"""
    await callback_query.message.edit_text(
        "❌ Отправка поздравления отменена.",
        reply_markup=get_start_keyboard()
    )
    await state.finish()
    await callback_query.answer()

async def process_my_greetings_stats(callback_query: types.CallbackQuery):
    """Показывает статистику поздравлений пользователя"""
    user = callback_query.from_user
    stats = greetings_db.get_stats(user.id)
    link_code = greetings_db.create_or_get_link(user.id)
    bot_link = f"https://t.me/{BOT_USERNAME}?start=greet_{link_code}"
    
    if not stats:
        total = 0
        last_date = "никогда"
    else:
        total = stats[0]
        last_date = stats[1] if stats[1] else "никогда"
    
    text = (
        f"📊 <b>Ваша статистика поздравлений:</b>\n\n"
        f"📨 Всего получено: <b>{total}</b>\n"
        f"📅 Последнее: <b>{last_date}</b>\n\n"
        f"📎 <b>Ваша ссылка:</b>\n"
        f"<code>{bot_link}</code>"
    )
    
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_greetings")
    )
    
    await callback_query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
        disable_web_page_preview=True
    )
    await callback_query.answer()

async def process_all_my_greetings(callback_query: types.CallbackQuery):
    """Показывает все полученные поздравления"""
    user = callback_query.from_user
    greetings = greetings_db.get_user_greetings(user.id, limit=20)
    
    if not greetings:
        await callback_query.message.edit_text(
            "📭 <b>У вас пока нет поздравлений</b>\n\n"
            "Разместите свою ссылку в соцсетях и ждите!",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_greetings")
            )
        )
        await callback_query.answer()
        return
    
    text = "📬 <b>Ваши последние поздравления:</b>\n\n"
    
    for i, g in enumerate(greetings[:10], 1):
        # Определяем отправителя
        if g[7]:  # is_anonymous
            sender = "Аноним"
        else:
            sender = g[4] or g[3] or "Неизвестно"  # first_name или last_name
            if g[6]:  # username
                sender += f" (@{g[6]})"
        
        date = g[11][:16] if g[11] else "неизвестно"
        msg = g[8][:30] + "..." if len(g[8]) > 30 else g[8]
        media_icon = "📸" if g[9] else "💬"
        
        text += f"{i}. {media_icon} <b>От {sender}</b>\n"
        text += f"   {msg}\n"
        text += f"   <i>{date}</i>\n\n"
    
    if len(greetings) > 10:
        text += f"<i>...и еще {len(greetings) - 10} поздравлений</i>"
    
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton(text="📊 Статистика", callback_data="my_greetings_stats"),
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_greetings")
    )
    
    await callback_query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )
    await callback_query.answer()

async def process_back_to_greetings(callback_query: types.CallbackQuery):
    """Возврат в меню поздравлений"""
    await process_start_greetings(callback_query)

async def process_reply_to_sender(callback_query: types.CallbackQuery, state: FSMContext):
    """Ответ отправителю поздравления"""
    sender_id = int(callback_query.data.replace("reply_to_sender_", ""))
    
    # Получаем информацию об отправителе из БД для контекста
    # Это опционально - можно передавать доп. информацию
    
    await state.update_data(
        reply_to_user=sender_id,
        reply_mode=True  # Флаг, что мы в режиме ответа
    )
    
    await callback_query.message.answer(
        "✏️ <b>Напишите ответ отправителю:</b>\n\n"
        "Вы можете отправить:\n"
        "• Текстовое сообщение 📝\n"
        "• Фото 📸\n"
        "• Видео 🎥\n"
        "• Стикер или GIF 🎭\n"
        "• Голосовое сообщение 🎤\n"
        "• Любой другой файл 📎\n\n"
        "<i>Ваш ответ будет доставлен получателю в том же виде!</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_reply")
        )
    )
    
    await state.set_state(UserStates.replying_to_greeter)
    await callback_query.answer()

async def handle_reply_to_sender(message: types.Message, state: FSMContext):
    """Обработка ответа на поздравление с поддержкой всех типов контента"""
    if await state.get_state() != UserStates.replying_to_greeter.state:
        return
    
    data = await state.get_data()
    recipient_id = data.get('reply_to_user')
    
    if not recipient_id:
        await message.answer(
            "❌ Ошибка. Попробуйте снова.",
            reply_markup=get_start_keyboard()
        )
        await state.finish()
        return
    
    try:
        # Определяем тип контента и отправляем соответствующим методом
        if message.text:
            # Текстовое сообщение
            await message.bot.send_message(
                chat_id=recipient_id,
                text=f"💬 <b>Ответ на ваше поздравление:</b>\n\n{message.text}",
                parse_mode=ParseMode.HTML
            )
            
        elif message.photo:
            # Фото с подписью или без
            caption = f"💬 <b>Ответ на ваше поздравление</b>"
            if message.caption:
                caption += f"\n\n{message.caption}"
            
            await message.bot.send_photo(
                chat_id=recipient_id,
                photo=message.photo[-1].file_id,
                caption=caption,
                parse_mode=ParseMode.HTML
            )
            
        elif message.video:
            # Видео с подписью или без
            caption = f"💬 <b>Ответ на ваше поздравление</b>"
            if message.caption:
                caption += f"\n\n{message.caption}"
            
            await message.bot.send_video(
                chat_id=recipient_id,
                video=message.video.file_id,
                caption=caption,
                parse_mode=ParseMode.HTML
            )
            
        elif message.animation:
            # GIF/анимация
            caption = f"💬 <b>Ответ на ваше поздравление</b>"
            if message.caption:
                caption += f"\n\n{message.caption}"
            
            await message.bot.send_animation(
                chat_id=recipient_id,
                animation=message.animation.file_id,
                caption=caption,
                parse_mode=ParseMode.HTML
            )
            
        elif message.sticker:
            # Стикер (отправляем как есть, без текста)
            await message.bot.send_sticker(
                chat_id=recipient_id,
                sticker=message.sticker.file_id
            )
            # Добавляем текстовое уведомление отдельно
            await message.bot.send_message(
                chat_id=recipient_id,
                text="💬 <b>Ответ на ваше поздравление</b> (стикер)",
                parse_mode=ParseMode.HTML
            )
            
        elif message.voice:
            # Голосовое сообщение
            caption = f"💬 <b>Ответ на ваше поздравление</b>"
            if message.caption:
                caption += f"\n\n{message.caption}"
            
            await message.bot.send_voice(
                chat_id=recipient_id,
                voice=message.voice.file_id,
                caption=caption,
                parse_mode=ParseMode.HTML
            )
            
        elif message.video_note:
            # Кружочек (видеосообщение)
            await message.bot.send_video_note(
                chat_id=recipient_id,
                video_note=message.video_note.file_id
            )
            # Добавляем текстовое уведомление отдельно
            await message.bot.send_message(
                chat_id=recipient_id,
                text="💬 <b>Ответ на ваше поздравление</b> (видеосообщение)",
                parse_mode=ParseMode.HTML
            )
            
        elif message.audio:
            # Аудиофайл
            caption = f"💬 <b>Ответ на ваше поздравление</b>"
            if message.caption:
                caption += f"\n\n{message.caption}"
            
            await message.bot.send_audio(
                chat_id=recipient_id,
                audio=message.audio.file_id,
                caption=caption,
                parse_mode=ParseMode.HTML,
                performer=message.audio.performer,
                title=message.audio.title
            )
            
        elif message.document:
            # Документ/файл
            caption = f"💬 <b>Ответ на ваше поздравление</b>"
            if message.caption:
                caption += f"\n\n{message.caption}"
            
            await message.bot.send_document(
                chat_id=recipient_id,
                document=message.document.file_id,
                caption=caption,
                parse_mode=ParseMode.HTML
            )
            
        elif message.contact:
            # Контакт
            await message.bot.send_contact(
                chat_id=recipient_id,
                phone_number=message.contact.phone_number,
                first_name=message.contact.first_name,
                last_name=message.contact.last_name
            )
            
        elif message.location:
            # Геолокация
            await message.bot.send_location(
                chat_id=recipient_id,
                latitude=message.location.latitude,
                longitude=message.location.longitude
            )
            
        elif message.venue:
            # Место
            await message.bot.send_venue(
                chat_id=recipient_id,
                latitude=message.venue.location.latitude,
                longitude=message.venue.location.longitude,
                title=message.venue.title,
                address=message.venue.address
            )
            
        elif message.poll:
            # Опрос (нельзя переслать, только создать новый)
            await message.bot.send_message(
                chat_id=recipient_id,
                text="❌ Опросы нельзя пересылать. Отправьте другой тип сообщения."
            )
            return
            
        else:
            # Если тип не определен, пробуем просто переслать
            await message.forward(chat_id=recipient_id)
        
        # Подтверждение отправителю
        await message.answer(
            "✅ <b>Ответ успешно отправлен!</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=get_start_keyboard()
        )
        
    except Exception as e:
        print(f"Ошибка при отправке ответа: {e}")
        await message.answer(
            "❌ <b>Ошибка при отправке ответа</b>\n\n"
            f"Попробуйте еще раз или отправьте другое сообщение.",
            parse_mode=ParseMode.HTML
        )
    
    await state.finish()

async def process_cancel_reply(callback_query: types.CallbackQuery, state: FSMContext):
    """Отмена ответа"""
    await callback_query.message.edit_text(
        "❌ Ответ отменен.\n\n"
        "Вы вернулись в главное меню.",
        reply_markup=get_start_keyboard()
    )
    await state.finish()
    await callback_query.answer()

def format_reply_caption(base_text="💬 Ответ на ваше поздравление", user_message=None):
    """Форматирует подпись для ответа"""
    if user_message and user_message.caption:
        return f"{base_text}\n\n{user_message.caption}"
    return base_text

async def process_cancel_reply(callback_query: types.CallbackQuery, state: FSMContext):
    """Отмена ответа"""
    await callback_query.message.edit_text("❌ Ответ отменен.")
    await state.finish()
    await callback_query.answer()



async def process_get_card(callback_query: types.CallbackQuery):
    # Отвечаем на callback, чтобы убрать "часики" на кнопке
    await callback_query.answer("🎴 Ищем для вас открытку...")
    
    # Задаем количество открыток (замените на актуальное число)
    total_cards = 10  # Укажите реальное количество ваших открыток
    
    # Генерируем случайный номер открытки
    card_number = random.randint(1, total_cards)
    
    # Формируем путь к файлу (предполагаем, что открытки лежат в папке cards)
    # Названия файлов: card_1.jpg, card_2.jpg, ... card_20.jpg
    photo_path = f"card_{card_number}.jpg"
    
    # Проверяем, существует ли файл с другим расширением, если .jpg не найден
    if not os.path.exists(photo_path):
        # Пробуем .png
        photo_path = f"card_{card_number}.png"
        
        if not os.path.exists(photo_path):
            # Пробуем .jpeg
            photo_path = f"card_{card_number}.jpeg"
    
    try:
        # Пытаемся открыть и отправить файл
        with open(photo_path, 'rb') as photo:
            # Отправляем фото с подписью
            await callback_query.message.answer_photo(
                photo=InputFile(photo),
                caption=f"✨ <b>Ваша персональная открытка!</b>\n\n",
                parse_mode=ParseMode.HTML
            )
    except FileNotFoundError:
        # Если файл не найден, отправляем сообщение об ошибке
        await callback_query.message.answer(
            "❌ <b>Открытки временно недоступны</b>\n\n"
            "Попробуйте позже или напишите администратору: @yuunaass",
            parse_mode=ParseMode.HTML,
            reply_markup=get_start_keyboard()  # Возвращаем клавиатуру
        )
    except Exception as e:
        # Ловим другие возможные ошибки
        print(f"Ошибка при отправке открытки: {e}")
        await callback_query.message.answer(
            "❌ <b>Произошла ошибка</b>\n\n"
            "Пожалуйста, попробуйте еще раз позже.",
            parse_mode=ParseMode.HTML,
            reply_markup=get_start_keyboard()
        )


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
        await message.forward(chat_id=1012078689)
        await message.forward(chat_id=975101969)  # ID администратора
        
        # Отправляем дополнительное сообщение с информацией о пользователе
        await message.bot.send_message(
            chat_id=1012078689,
            text=f"ВОПРОС!!!!\n\nОт: {user.first_name} {user.last_name} @{user.username}, <code>|send |{user.id}|</code>",
            parse_mode=ParseMode.HTML  # Чтобы использовать HTML-теги в сообщении
        )
        await message.bot.send_message(
            chat_id=975101969,
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
        await message.forward(chat_id=975101969)
        # Отправляем дополнительное сообщение с информацией о пользователе
        await message.bot.send_message(
            chat_id=1012078689,
            text=f"ПРЕДЛОЖКА!!! \n\nОт: {user.first_name} {user.last_name} @{user.username}, <code>|send |{user.id}|</code>",
            parse_mode=ParseMode.HTML  # Чтобы использовать HTML-теги в сообщении
        )
        await message.bot.send_message(
            chat_id=975101969,
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
    dp.register_message_handler(cmd_start_with_greeting, commands=['start'])
    
    # Заменяем существующий start на новый
    dp.register_message_handler(cmd_start_with_greeting, commands=['start'])
    
    # Обработчики поздравлений (для обычных пользователей)
    dp.register_callback_query_handler(process_start_greetings, lambda c: c.data == "start_greetings")
    dp.register_callback_query_handler(process_start_greetings_from_message, lambda c: c.data == "start_greetings_from_message")
    dp.register_callback_query_handler(process_copy_link, lambda c: c.data and c.data.startswith("copy_link_"))
    dp.register_callback_query_handler(process_anonymity_choice, lambda c: c.data in ["anon_yes", "anon_no"], state=UserStates.choosing_anonymity)
    dp.register_callback_query_handler(process_cancel_greeting, lambda c: c.data == "cancel_greeting", state="*")
    dp.register_message_handler(handle_greeting_message, content_types=["any"], state=UserStates.sending_greeting)
    
    # Убираем старые хэндлеры статистики для обычных пользователей
    # dp.register_callback_query_handler(process_my_greetings_stats, lambda c: c.data == "my_greetings_stats")
    # dp.register_callback_query_handler(process_all_my_greetings, lambda c: c.data == "all_my_greetings")
    dp.register_callback_query_handler(process_back_to_greetings, lambda c: c.data == "back_to_greetings")
    
    # Обработчики ответов
    dp.register_callback_query_handler(process_reply_to_sender, lambda c: c.data and c.data.startswith("reply_to_sender_"), state="*")
    dp.register_callback_query_handler(process_cancel_reply, lambda c: c.data == "cancel_reply", state=UserStates.replying_to_greeter)
    dp.register_message_handler(handle_reply_to_sender, content_types=["any"], state=UserStates.replying_to_greeter)
    

    
    # Остальные существующие хэндлеры...
    dp.register_callback_query_handler(process_get_card, lambda c: c.data == "get_card")
    dp.register_callback_query_handler(process_faq, lambda c: c.data == "faq")
    # ... и так далее
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
    dp.register_callback_query_handler(process_get_card, lambda c: c.data == "get_card")