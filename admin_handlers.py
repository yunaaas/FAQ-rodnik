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
from greetings import greetings_db
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from aiogram.dispatcher import FSMContext
from datetime import datetime

# ID администраторов
ADMIN_IDS = [1012078689, 1612789346]  # Ваши ID

async def is_admin(user_id):
    return user_id in ADMIN_IDS

async def admin_command(message: types.Message, state: FSMContext):
    """Команда /admin - показывает список всех участников (создавших ссылки)"""
    user_id = message.from_user.id
    
    if not await is_admin(user_id):
        await message.answer("❌ У вас нет прав администратора")
        return
    
    # Сохраняем информацию об админе
    greetings_db.save_or_update_user(
        message.from_user.id,
        message.from_user.first_name,
        message.from_user.last_name,
        message.from_user.username
    )
    
    # Получаем ВСЕХ участников (кто создал ссылку)
    participants = greetings_db.get_all_participants()
    
    if not participants:
        await message.answer(
            "📭 <b>Нет пользователей с активными ссылками</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")
            )
        )
        return
    
    # Сохраняем список в state
    await state.update_data(participants_list=participants, current_page=0)
    await show_participants_page(message, state, edit=False)

async def get_participant_display_name(participant_data):
    """Формирует отображаемое имя участника"""
    user_id, first_name, last_name, username, total, link_created, link_code = participant_data
    
    if username:
        return f"@{username}"
    elif first_name or last_name:
        name_parts = []
        if first_name:
            name_parts.append(first_name)
        if last_name:
            name_parts.append(last_name)
        return " ".join(name_parts)
    else:
        return f"ID: {user_id}"

async def show_participants_page(message_or_callback, state: FSMContext, edit=True):
    """Отображает страницу со списком участников"""
    
    data = await state.get_data()
    participants_list = data.get('participants_list', [])
    current_page = data.get('current_page', 0)
    
    # Настройки пагинации
    items_per_page = 10  # Можно изменить на любое число
    total_pages = (len(participants_list) + items_per_page - 1) // items_per_page
    start_idx = current_page * items_per_page
    end_idx = min(start_idx + items_per_page, len(participants_list))
    
    current_participants = participants_list[start_idx:end_idx]
    
    # Создаем клавиатуру
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for participant in current_participants:
        user_id, first_name, last_name, username, total, link_created, link_code = participant
        
        # Получаем отображаемое имя
        display_name = await get_participant_display_name(participant)
        
        # Форматируем дату создания ссылки
        if link_created:
            try:
                date_obj = datetime.fromisoformat(str(link_created)) if link_created else datetime.now()
                date_str = date_obj.strftime("%d.%m.%Y")
            except:
                date_str = "неизвестно"
        else:
            date_str = "неизвестно"
        
        btn_text = f"{display_name} | {total} 📨 | с {date_str}"
        
        keyboard.add(
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"admin_view_user_{user_id}"
            )
        )
    
    # Кнопки навигации
    nav_buttons = []
    
    if current_page > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data="admin_prev_page"))
    
    nav_buttons.append(InlineKeyboardButton(text=f"📄 {current_page + 1}/{total_pages}", callback_data="admin_page_info"))
    
    if current_page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="Вперед ▶️", callback_data="admin_next_page"))
    
    if len(nav_buttons) > 1:
        keyboard.row(*nav_buttons)
    
    keyboard.add(InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_main"))
    
    # Подсчитываем общую статистику
    total_greetings_all = sum(p[4] for p in participants_list)
    
    text = (
        f"👑 <b>Админ-панель</b>\n\n"
        f"📋 Всего участников (создавших ссылки): <b>{len(participants_list)}</b>\n"
        f"📨 Всего получено поздравлений: <b>{total_greetings_all}</b>\n\n"
        f"<i>Нажмите на участника, чтобы увидеть все его поздравления\n"
        f"(даже анонимные будут показаны с реальными отправителями)</i>"
    )
    
    if edit:
        await message_or_callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    else:
        await message_or_callback.answer(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)

async def admin_prev_page(callback_query: types.CallbackQuery, state: FSMContext):
    """Переключение на предыдущую страницу списка участников"""
    if not await is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Нет прав")
        return
    
    data = await state.get_data()
    current_page = data.get('current_page', 0)
    
    if current_page > 0:
        await state.update_data(current_page=current_page - 1)
        await show_participants_page(callback_query, state, edit=True)
    
    await callback_query.answer()

async def admin_next_page(callback_query: types.CallbackQuery, state: FSMContext):
    """Переключение на следующую страницу списка участников"""
    if not await is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Нет прав")
        return
    
    data = await state.get_data()
    participants_list = data.get('participants_list', [])
    current_page = data.get('current_page', 0)
    
    items_per_page = 10
    total_pages = (len(participants_list) + items_per_page - 1) // items_per_page
    
    if current_page < total_pages - 1:
        await state.update_data(current_page=current_page + 1)
        await show_participants_page(callback_query, state, edit=True)
    
    await callback_query.answer()

async def admin_view_user_greetings(callback_query: types.CallbackQuery, state: FSMContext):
    """Просмотр всех поздравлений конкретного пользователя"""
    user_id = callback_query.from_user.id
    
    if not await is_admin(user_id):
        await callback_query.answer("❌ У вас нет прав администратора")
        return
    
    target_user_id = int(callback_query.data.replace("admin_view_user_", ""))
    
    # Получаем информацию о целевом пользователе
    user_info = greetings_db.get_user_info(target_user_id)
    
    if user_info:
        _, first_name, last_name, username, _, _ = user_info
        if username:
            target_user_name = f"@{username}"
        elif first_name or last_name:
            target_user_name = f"{first_name or ''} {last_name or ''}".strip()
        else:
            target_user_name = f"ID: {target_user_id}"
    else:
        target_user_name = f"ID: {target_user_id}"
    
    # Получаем все поздравления пользователя
    greetings = greetings_db.get_user_greetings(target_user_id, limit=1000)
    
    if not greetings:
        await callback_query.message.edit_text(
            f"📭 <b>У пользователя {target_user_name} нет поздравлений</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton(text="🔙 К списку участников", callback_data="admin_back_to_list")
            )
        )
        await callback_query.answer()
        return
    
    # Сохраняем поздравления в state для пагинации
    await state.update_data(
        user_greetings=greetings, 
        greeting_page=0, 
        target_user=target_user_id,
        target_user_name=target_user_name
    )
    
    # Показываем первую страницу поздравлений
    await show_greetings_page(callback_query, state)

async def show_greetings_page(callback_query: types.CallbackQuery, state: FSMContext):
    """Отображает страницу со списком поздравлений"""
    data = await state.get_data()
    greetings = data.get('user_greetings', [])
    current_page = data.get('greeting_page', 0)
    target_user = data.get('target_user')
    target_user_name = data.get('target_user_name', f"ID: {target_user}")
    
    items_per_page = 5
    total_pages = (len(greetings) + items_per_page - 1) // items_per_page
    start_idx = current_page * items_per_page
    end_idx = min(start_idx + items_per_page, len(greetings))
    
    current_greetings = greetings[start_idx:end_idx]
    
    # Создаем клавиатуру
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for g in current_greetings:
        # Распаковываем данные
        (greeting_id, link_code, owner_id, sender_id, sender_first, sender_last, 
         sender_username, is_anonymous, message_text, media_type, 
         media_file_id, created_at, is_read) = g
        
        # Определяем реального отправителя
        if sender_username:
            real_sender = f"@{sender_username}"
        elif sender_first or sender_last:
            real_sender = f"{sender_first or ''} {sender_last or ''}".strip()
        else:
            real_sender = f"ID: {sender_id}"
        
        # Добавляем пометку об анонимности
        anonymous_mark = "🔸 " if is_anonymous else ""
        
        # Дата
        try:
            date_obj = datetime.fromisoformat(str(created_at)) if created_at else datetime.now()
            date_str = date_obj.strftime("%d.%m %H:%M")
        except:
            date_str = "неизвестно"
        
        # Иконка типа медиа
        media_icons = {
            "photo": "📸", "video": "🎥", "gif": "🎭", "sticker": "🎨",
            "voice": "🎤", "video_note": "📹", "audio": "🎵", 
            "document": "📄", "text": "💬"
        }
        icon = media_icons.get(media_type, "📦")
        
        # Статус прочтения
        read_status = "✅" if is_read else "⏳"
        
        # Текст сообщения (обрезаем)
        message_preview = message_text[:20] + "..." if len(message_text) > 20 else message_text
        
        btn_text = f"{read_status} {icon} {date_str} - {anonymous_mark}{real_sender[:15]}: {message_preview}"
        
        keyboard.add(
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"admin_show_greeting_{greeting_id}"
            )
        )
    
    # Навигация по страницам
    nav_buttons = []
    
    if current_page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="◀️ Назад", callback_data="admin_greetings_prev")
        )
    
    page_info = f"{current_page + 1}/{total_pages}"
    nav_buttons.append(
        InlineKeyboardButton(text=page_info, callback_data="admin_greetings_info")
    )
    
    if current_page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton(text="Вперед ▶️", callback_data="admin_greetings_next")
        )
    
    if len(nav_buttons) > 1:
        keyboard.row(*nav_buttons)
    
    # Кнопки управления
    keyboard.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data=f"admin_user_stats_{target_user}"),
        InlineKeyboardButton(text="🔙 К списку", callback_data="admin_back_to_list")
    )
    
    # Подсчитываем статистику
    anonymous_count = sum(1 for g in greetings if g[7])
    read_count = sum(1 for g in greetings if g[12])
    
    text = (
        f"👑 <b>Поздравления пользователя {target_user_name}</b>\n"
        f"📨 Всего: {len(greetings)} сообщений\n"
        f"🔸 Анонимных: {anonymous_count}\n"
        f"✅ Прочитано: {read_count}\n\n"
        f"<i>✅ - прочитано | ⏳ - не прочитано\n"
        f"🔸 - было отправлено анонимно</i>\n\n"
        f"<i>Нажмите на сообщение, чтобы увидеть его полностью</i>"
    )
    
    await callback_query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )
    await callback_query.answer()

async def admin_show_greeting(callback_query: types.CallbackQuery):
    """Показывает конкретное поздравление"""
    user_id = callback_query.from_user.id
    
    if not await is_admin(user_id):
        await callback_query.answer("❌ Нет прав")
        return
    
    greeting_id = int(callback_query.data.replace("admin_show_greeting_", ""))
    greeting = greetings_db.get_greeting_by_id(greeting_id)
    
    if not greeting:
        await callback_query.answer("❌ Поздравление не найдено")
        return
    
    # Распаковываем данные
    (id, link_code, owner_id, sender_id, sender_first, sender_last, 
     sender_username, is_anonymous, message_text, media_type, 
     media_file_id, created_at, is_read) = greeting
    
    # Получаем информацию о получателе
    owner_info = greetings_db.get_user_info(owner_id)
    if owner_info:
        _, o_first, o_last, o_username, _, _ = owner_info
        if o_username:
            owner_name = f"@{o_username}"
        elif o_first or o_last:
            owner_name = f"{o_first or ''} {o_last or ''}".strip()
        else:
            owner_name = f"ID: {owner_id}"
    else:
        owner_name = f"ID: {owner_id}"
    
    # Информация об отправителе
    sender_info_parts = []
    if sender_first or sender_last:
        sender_info_parts.append(f"<b>{sender_first or ''} {sender_last or ''}</b>".strip())
    if sender_username:
        sender_info_parts.append(f"📱 @{sender_username}")
    sender_info_parts.append(f"🆔 <code>{sender_id}</code>")
    sender_info = "\n".join(sender_info_parts)
    
    anonymity_info = "\n🔹 <i>Для получателя было анонимным</i>" if is_anonymous else ""
    
    # Форматируем дату
    try:
        date_obj = datetime.fromisoformat(str(created_at)) if created_at else datetime.now()
        date_formatted = date_obj.strftime("%d.%m.%Y %H:%M:%S")
    except:
        date_formatted = str(created_at)
    
    info_text = (
        f"📬 <b>Поздравление #{id}</b>\n\n"
        f"<b>Получатель:</b> {owner_name}\n"
        f"🆔 <code>{owner_id}</code>\n"
        f"🔗 Код ссылки: <code>{link_code}</code>\n\n"
        f"<b>Отправитель (реальные данные):</b>\n{sender_info}{anonymity_info}\n\n"
        f"<b>Дата:</b> {date_formatted}\n"
        f"<b>Статус:</b> {'✅ Прочитано' if is_read else '⏳ Не прочитано'}\n\n"
        f"<b>Сообщение:</b>\n{message_text}"
    )
    
    await callback_query.message.answer(info_text, parse_mode=ParseMode.HTML)
    
    # Отправляем медиа если есть
    if media_file_id and media_type and media_type != "text":
        try:
            if media_type == "photo":
                await callback_query.message.answer_photo(photo=media_file_id)
            elif media_type == "video":
                await callback_query.message.answer_video(video=media_file_id)
            elif media_type in ["gif", "animation"]:
                await callback_query.message.answer_animation(animation=media_file_id)
            elif media_type == "sticker":
                await callback_query.message.answer_sticker(sticker=media_file_id)
            elif media_type == "voice":
                await callback_query.message.answer_voice(voice=media_file_id)
            elif media_type == "video_note":
                await callback_query.message.answer_video_note(video_note=media_file_id)
            elif media_type == "audio":
                await callback_query.message.answer_audio(audio=media_file_id)
            elif media_type == "document":
                await callback_query.message.answer_document(document=media_file_id)
        except Exception as e:
            await callback_query.message.answer(f"❌ Ошибка при отправке медиа: {e}")
    
    await callback_query.answer()

async def admin_user_stats(callback_query: types.CallbackQuery, state: FSMContext):
    """Показывает подробную статистику по пользователю"""
    if not await is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Нет прав")
        return
    
    target_user_id = int(callback_query.data.replace("admin_user_stats_", ""))
    
    # Получаем информацию о пользователе
    user_info = greetings_db.get_user_info(target_user_id)
    if user_info:
        _, first_name, last_name, username, first_seen, last_active = user_info
        if username:
            user_name = f"@{username}"
        elif first_name or last_name:
            user_name = f"{first_name or ''} {last_name or ''}".strip()
        else:
            user_name = f"ID: {target_user_id}"
        
        first_seen_str = first_seen[:16] if first_seen else "неизвестно"
        last_active_str = last_active[:16] if last_active else "неизвестно"
    else:
        user_name = f"ID: {target_user_id}"
        first_seen_str = "неизвестно"
        last_active_str = "неизвестно"
    
    # Получаем статистику
    stats = greetings_db.get_stats(target_user_id)
    
    # Получаем все поздравления для детальной статистики
    greetings = greetings_db.get_user_greetings(target_user_id, limit=1000)
    
    if greetings:
        # Статистика по отправителям
        senders = {}
        media_types = {}
        anonymous_count = 0
        read_count = 0
        
        for g in greetings:
            sender_id = g[3]
            if sender_id in senders:
                senders[sender_id] += 1
            else:
                senders[sender_id] = 1
            
            media_type = g[9] or "text"
            media_types[media_type] = media_types.get(media_type, 0) + 1
            
            if g[7]:  # is_anonymous
                anonymous_count += 1
            
            if g[12]:  # is_read
                read_count += 1
        
        # Находим топ-отправителей
        top_senders = sorted(senders.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Формируем текст статистики
        stat_text = (
            f"📊 <b>Статистика пользователя {user_name}</b>\n"
            f"🆔 <code>{target_user_id}</code>\n\n"
            f"👤 Информация:\n"
            f"  • Первое появление: {first_seen_str}\n"
            f"  • Последняя активность: {last_active_str}\n\n"
            f"📨 Поздравления:\n"
            f"  • Всего получено: <b>{stats[0] if stats else len(greetings)}</b>\n"
            f"  • Анонимных: <b>{anonymous_count}</b> ({anonymous_count/len(greetings)*100:.1f}%)\n"
            f"  • Прочитано: <b>{read_count}</b> ({read_count/len(greetings)*100:.1f}%)\n"
            f"  • Последнее: {stats[1][:16] if stats and stats[1] else 'никогда'}\n\n"
            f"📎 Типы медиа:\n"
        )
        
        media_names = {
            "photo": "📸 Фото", "video": "🎥 Видео", "gif": "🎭 GIF",
            "sticker": "🎨 Стикер", "voice": "🎤 Голосовое", 
            "video_note": "📹 Кружок", "audio": "🎵 Аудио",
            "document": "📄 Документ", "text": "💬 Текст"
        }
        
        for m_type, count in sorted(media_types.items(), key=lambda x: x[1], reverse=True):
            name = media_names.get(m_type, f"📦 {m_type}")
            stat_text += f"  {name}: {count}\n"
        
        if top_senders:
            stat_text += f"\n👥 Топ отправителей:\n"
            for s_id, count in top_senders:
                sender_info = greetings_db.get_user_info(s_id)
                if sender_info:
                    _, s_first, s_last, s_username, _, _ = sender_info
                    if s_username:
                        s_name = f"@{s_username}"
                    elif s_first or s_last:
                        s_name = f"{s_first or ''} {s_last or ''}".strip()
                    else:
                        s_name = f"ID: {s_id}"
                else:
                    s_name = f"ID: {s_id}"
                stat_text += f"  {s_name}: {count} сообщений\n"
        
    else:
        stat_text = (
            f"📊 <b>Статистика пользователя {user_name}</b>\n"
            f"🆔 <code>{target_user_id}</code>\n\n"
            f"👤 Информация:\n"
            f"  • Первое появление: {first_seen_str}\n"
            f"  • Последняя активность: {last_active_str}\n\n"
            f"📨 Получено поздравлений: <b>0</b>\n"
            f"Ссылка создана, но поздравлений пока нет."
        )
    
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton(text="🔙 К поздравлениям", callback_data=f"admin_back_to_user_{target_user_id}"),
        InlineKeyboardButton(text="🔙 К списку", callback_data="admin_back_to_list")
    )
    
    await callback_query.message.edit_text(
        stat_text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )
    await callback_query.answer()

async def admin_greetings_prev(callback_query: types.CallbackQuery, state: FSMContext):
    """Предыдущая страница поздравлений"""
    if not await is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Нет прав")
        return
    
    data = await state.get_data()
    current_page = data.get('greeting_page', 0)
    
    if current_page > 0:
        await state.update_data(greeting_page=current_page - 1)
        await show_greetings_page(callback_query, state)
    else:
        await callback_query.answer("Это первая страница")
    
    await callback_query.answer()

async def admin_greetings_next(callback_query: types.CallbackQuery, state: FSMContext):
    """Следующая страница поздравлений"""
    if not await is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Нет прав")
        return
    
    data = await state.get_data()
    greetings = data.get('user_greetings', [])
    current_page = data.get('greeting_page', 0)
    
    items_per_page = 5
    total_pages = (len(greetings) + items_per_page - 1) // items_per_page
    
    if current_page < total_pages - 1:
        await state.update_data(greeting_page=current_page + 1)
        await show_greetings_page(callback_query, state)
    else:
        await callback_query.answer("Это последняя страница")
    
    await callback_query.answer()

async def admin_back_to_user(callback_query: types.CallbackQuery, state: FSMContext):
    """Возврат к поздравлениям пользователя"""
    if not await is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Нет прав")
        return
    
    target_user_id = int(callback_query.data.replace("admin_back_to_user_", ""))
    
    greetings = greetings_db.get_user_greetings(target_user_id, limit=1000)
    
    if greetings:
        # Получаем имя пользователя
        user_info = greetings_db.get_user_info(target_user_id)
        if user_info:
            _, first_name, last_name, username, _, _ = user_info
            if username:
                target_user_name = f"@{username}"
            elif first_name or last_name:
                target_user_name = f"{first_name or ''} {last_name or ''}".strip()
            else:
                target_user_name = f"ID: {target_user_id}"
        else:
            target_user_name = f"ID: {target_user_id}"
        
        await state.update_data(
            user_greetings=greetings, 
            greeting_page=0, 
            target_user=target_user_id,
            target_user_name=target_user_name
        )
        await show_greetings_page(callback_query, state)
    else:
        await admin_back_to_list(callback_query, state)
    
    await callback_query.answer()

async def admin_back_to_list(callback_query: types.CallbackQuery, state: FSMContext):
    """Возврат к списку участников"""
    if not await is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Нет прав")
        return
    
    # Очищаем данные о поздравлениях
    await state.update_data(user_greetings=None, greeting_page=0, target_user=None, target_user_name=None)
    
    # Получаем свежий список участников
    participants = greetings_db.get_all_participants()
    await state.update_data(participants_list=participants, current_page=0)
    
    await show_participants_page(callback_query, state, edit=True)
    
    await callback_query.answer()

async def admin_page_info(callback_query: types.CallbackQuery):
    """Информация о странице"""
    await callback_query.answer("Используйте кнопки навигации для переключения", show_alert=False)

async def admin_greetings_info(callback_query: types.CallbackQuery):
    """Информация о странице поздравлений"""
    await callback_query.answer("Нажмите на сообщение для просмотра", show_alert=False)


async def cmd_send_message(message: types.Message):
    if message.from_user.id == 1012078689 or message.from_user.id == 975101969:  # Проверка, что это администратор
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
            await bd(message)
        except Exception as e:
                print(f"я хуй знает что легло, ладно наебал - вот {e}")
        



def register_admin_handlers(dp: Dispatcher):
    """Регистрация всех админских хэндлеров"""
    dp.register_message_handler(admin_command, commands=['admin'])
    dp.register_callback_query_handler(admin_prev_page, Text(startswith="admin_prev_page"), state='*')
    dp.register_callback_query_handler(admin_next_page, Text(startswith="admin_next_page"), state='*')
    dp.register_callback_query_handler(admin_view_user_greetings, Text(startswith="admin_view_user_"), state='*')
    dp.register_callback_query_handler(admin_show_greeting, Text(startswith="admin_show_greeting_"), state='*')
    dp.register_callback_query_handler(admin_greetings_prev, Text(startswith="admin_greetings_prev"), state='*')
    dp.register_callback_query_handler(admin_greetings_next, Text(startswith="admin_greetings_next"), state='*')
    dp.register_callback_query_handler(admin_user_stats, Text(startswith="admin_user_stats_"), state='*')
    dp.register_callback_query_handler(admin_back_to_user, Text(startswith="admin_back_to_user_"), state='*')
    dp.register_callback_query_handler(admin_back_to_list, Text(startswith="admin_back_to_list"), state='*')
    dp.register_callback_query_handler(admin_page_info, Text(startswith="admin_page_info"), state='*')
    dp.register_callback_query_handler(admin_greetings_info, Text(startswith="admin_greetings_info"), state='*')
    
    # Заглушка для информационных кнопок
    dp.register_callback_query_handler(lambda c: c.answer(), lambda c: c.data in ["admin_page_info", "admin_greetings_info"], state='*')
    dp.register_message_handler(cmd_send_message, commands=['send'], commands_prefix='|')
    dp.register_message_handler(cmd_view_questions, commands=['view_questions'])
    dp.register_message_handler(cmd_delete_question, commands=['delete_question'])
    dp.register_message_handler(cmd_update_question, commands=['update_question'], commands_prefix='|')
    dp.register_message_handler(cmd_add_question, commands=['add_question'], commands_prefix='|')
    dp.register_message_handler(bd, commands=['киньБД'], commands_prefix='/')
    dp.register_message_handler(norm_dr, commands=['date'], commands_prefix='|')

