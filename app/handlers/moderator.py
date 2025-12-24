from aiogram.types import Message, CallbackQuery
from aiogram import Router, Bot, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from datetime import datetime
import pytz

from ..services import *

from ..lexicon import LEXICON_TEXT
from ..config import config
from ..filters import ModeratorChatFilter
from ..states import ModeratorStates
from ..keyboards import MenuKeyboard

moderator_router = Router()
moderator_router.message.filter(ModeratorChatFilter())
ekaterinburg_tz = pytz.timezone('Asia/Yekaterinburg')
menu_keyboard = MenuKeyboard.get_keyboard_menu()

@moderator_router.message(Command("check"))
async def check_in_moderator_chat(message:Message):
    """
    Проверяет, написано сообщение в чате модераторов или нет
    """
    await message.answer("Да, это чат модераторов")

@moderator_router.callback_query(F.data.startswith("accept_user"))
async def approve_application(callback: CallbackQuery, bot: Bot):
    """
    Обрабатывает нажатие на кнопку принять анкету пользователя
    """
    user_id = int(callback.data.split("_")[-1])
    utc_time = callback.message.date
    ekaterinburg_time = utc_time.astimezone(ekaterinburg_tz)

    moderator_username = f'@{callback.from_user.username}' or callback.from_user.full_name or "Unknown"
    approval_date = ekaterinburg_time.strftime('%d.%m.%Y %H:%M')

    # Парсим анкету из сообщения
    form_data = parse_registration_form_from_message(callback.message.text or "", user_id, moderator_username, approval_date)

    if not form_data:
        await callback.answer("❌ Не удалось извлечь данные анкеты", show_alert=True)
        return
    
    # Отправляем в Google Sheets
    sheets_result = googlesheet_service.add_participant(form_data)
    
    # Статус для модератора
    sheets_status = "✅ Добавлен в базу" if sheets_result["success"] else f"❌ {sheets_result.get('error', 'Ошибка')}"

    await callback.answer(f"✅ Анкета пользователя {user_id} одобрена!", show_alert=True)
    await callback.message.edit_text(
        f"✅ Анкета одобрена\n"
        f"👤 ID пользователя: {user_id}\n"
        f"📊 Google Sheets: {sheets_status}\n"
        f"👮 Модератор: @{callback.from_user.username or callback.from_user.full_name}\n"
        f"🕐 Время: {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}",
        reply_markup=None)
    try:
        await bot.send_message(
            chat_id=user_id,
            text=LEXICON_TEXT["registration_completed"],reply_markup = menu_keyboard
        )
    except Exception as e:
        await callback.message.answer(f"❗️ Не удалось уведомить пользователя {user_id}")

@moderator_router.callback_query(F.data.startswith("reject_user"))
async def decline_application(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает нажатие на кнопку отклонить анкету пользователя
    """
    user_id = int(callback.data.split("_")[-1])

    await callback.answer("❔ Укажите причину отклонения анкеты пользователя", show_alert=False)
    await state.update_data(
        reject_user_id=user_id,
        moder_message_id=callback.message.message_id,
        moder_chat_id=callback.message.chat.id,
        moder_thread_id=callback.message.message_thread_id
    )
    await callback.message.answer(f"❔ Введите причину отклонения анкеты пользователя {user_id}:" )

    await state.set_state(ModeratorStates.waiting_reject_reason)

@moderator_router.message(F.text, StateFilter(ModeratorStates.waiting_reject_reason))
async def process_reject_reason(message: Message, state: FSMContext, bot: Bot):
    utc_time = message.date
    ekaterinburg_time = utc_time.astimezone(ekaterinburg_tz)
    data = await state.get_data()
    user_id = data.get("reject_user_id")
    reason = message.text
    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"😔 Ваша анкета отклонена.\nПричина: {reason}\n\nПожалуйста, заполните анкету заново."
        )
        moder_chat_id = data.get("moder_chat_id")
        moder_message_id = data.get("moder_message_id")
        await bot.edit_message_text(
        chat_id=moder_chat_id,
        message_id=moder_message_id,
        text=f"❌ Анкета отклонена\n"
            f"👤 Пользователь ID: {user_id}\n"
            f"👮 Модератор: @{message.from_user.username or message.from_user.full_name}\n"
            f"📝 Причина: {reason}\n"
            f"🕐 Время: {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}",
            reply_markup=None
        )
        await message.answer(f"✅ Анкета пользователя {user_id} отклонена. Причина отправлена.")
        await state.clear()
    except Exception as e:
        await message.answer(f"❗️ Не удалось уведомить пользователя")
        await state.clear()

@moderator_router.callback_query(F.data.startswith("close_the_request"))
async def close_the_request(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """
    Обрабатывает нажатие на кнопку закрыть обращение
    """
    current_text = callback.message.text
    lines = current_text.split('\n')
   
    message_line = None
    for line in lines:
        if line.strip().startswith("Сообщение:"):
            message_line = line.strip()
            break
        
    user_id = int(callback.data.split("_")[-1])
    utc_time = callback.message.date
    ekaterinburg_time = utc_time.astimezone(ekaterinburg_tz)

    moderator_username = f'@{callback.from_user.username}' or callback.from_user.full_name or "Unknown"
    approval_date = ekaterinburg_time.strftime('%d.%m.%Y %H:%M')
    await callback.answer(f"✅ Обращение пользователя {user_id} закрыто!", show_alert=True)
    await callback.message.edit_text(
        f"✅ Вопрос закрыт\n"
        f"👤 ID пользователя: {user_id}\n"
        f"📝 {message_line}\n"
        f"👮 Модератор: @{callback.from_user.username or callback.from_user.full_name}\n"
        f"🕐 Время: {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}",
        reply_markup=None)

@moderator_router.callback_query(F.data.startswith("answer_user_"))
async def the_request_answer(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """
    Обрабатывает нажатие на кнопку ответить
    """
    user_id = int(callback.data.split("_")[-1])

    await state.update_data(
        support_user_id=user_id,
        moder_message_id=callback.message.message_id,
    )
    await callback.message.answer(f"Введите ответ на обращение пользователя {user_id}:" )
    await state.set_state(ModeratorStates.waiting_edit_comment)

@moderator_router.message(F.text, StateFilter(ModeratorStates.waiting_edit_comment))
async def process_the_request_answer(message: Message, state: FSMContext, bot: Bot):
    utc_time = message.date
    ekaterinburg_time = utc_time.astimezone(ekaterinburg_tz)
    data = await state.get_data()
    user_id = data.get("support_user_id")
    answer = message.text
    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"📨 <b>Ответ от службы поддержки</b>\n\n{answer}\n\n💬 Если у вас остались вопросы, напишите нам снова!"
        )
        await message.answer(f"✅ Ответ пользователю {user_id} отправлен!")
        await state.clear()
    except Exception as e:
        await message.answer(f"❗️ Не удалось отправить ответ пользователю")
        await state.clear()

@moderator_router.callback_query(F.data.startswith("approve_application_"))
async def approve_application(callback: CallbackQuery, bot: Bot):
    """
    Обработка нажатия на кнопку Одобрить заявку
    """
    user_id = int(callback.data.split("_")[-1])
    utc_time = callback.message.date
    ekaterinburg_time = utc_time.astimezone(ekaterinburg_tz)
    moderator_username = callback.from_user.username or callback.from_user.full_name
    
    # Парсим заявку извлекаем row_id из сообщения
    message_text = callback.message.text or ""
    app_data = parse_event_application_from_message(message_text, user_id)
    
    # Извлекаем номер строки из сообщения из текста сообщения
    import re
    row_match = re.search(r"Строка:\s*(\d+)", message_text)
    row_id = int(row_match.group(1)) if row_match else 2
    
    # Обновляем статус в Google Sheets
    result = googlesheet_service.update_application_status(
        app_data.get("direction_name", ""), 
        row_id, 
        "Принята", 
        f"@{moderator_username}"
    )

    # Статус для модератора
    sheets_status = "✅ Обновлено" if result.get("success") else f"❌ {result.get('error', 'Ошибка')}"

    await callback.answer(f"✅ Заявка пользователя {user_id} одобрена!", show_alert=True)
    await callback.message.edit_text(
        f"✅ Заявка одобрена\n"
        f"👤 ID пользователя: {user_id}\n"
        f"📊 Строка в Google Sheets <b>{row_id}</b>: {sheets_status}\n"
        f"📁 Лист: {app_data.get('direction_name', 'Неизвестно')}\n"
        f"👮 Модератор: @{moderator_username}\n"
        f"🕐 Время: {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}",
        reply_markup=None,
        parse_mode="HTML"
    )
    
    # Уведомляем пользователя
    try:
        await bot.send_message(
            chat_id=user_id,
            text=LEXICON_TEXT["application_event_completed"], 
            reply_markup=menu_keyboard
        )
    except Exception as e:
        await callback.message.answer(f"❗️ Не удалось уведомить пользователя {user_id}")


@moderator_router.callback_query(F.data.startswith("decline_application_"))
async def decline_application(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает нажатие на кнопку отклонить заявку пользователя
    """
    user_id = int(callback.data.split("_")[-1])
    await callback.answer("❔ Укажите причину отклонения заявки пользователя", show_alert=False)
    await state.update_data(
        reject_user_id=user_id,
        moder_message_id=callback.message.message_id,
        moder_chat_id=callback.message.chat.id,
        moder_thread_id=callback.message.message_thread_id,
        message_text=callback.message.text or "" 
        )
    await callback.message.answer(f"❔ Введите причину отклонения заявки пользователя {user_id}:" )

    await state.set_state(ModeratorStates.waiting_reject_application_reason)

@moderator_router.message(F.text, StateFilter(ModeratorStates.waiting_reject_application_reason))
async def process_reject_reason(message: Message, state: FSMContext, bot: Bot):
    utc_time = message.date
    ekaterinburg_time = utc_time.astimezone(ekaterinburg_tz)
    data = await state.get_data()
    user_id = data.get("reject_user_id")
    reason = message.text
    message_text = data.get("message_text", "")
    
    app_data = parse_event_application_from_message(message_text, user_id)
    import re
    row_match = re.search(r"Строка:\s*(\d+)", message_text)
    row_id = int(row_match.group(1)) if row_match else 2
    
    moderator_username = message.from_user.username or message.from_user.full_name
    
    try:
        # 1. Обновляем статус в Google Sheets
        sheets_result = googlesheet_service.update_application_status(
            app_data.get("direction_name", ""), 
            row_id, 
            "Отклонена", 
            f"@{moderator_username}"
        )
        sheets_status = "✅ Обновлено" if sheets_result.get("success") else f"❌ {sheets_result.get('error', 'Ошибка')}"
        
        # 2. Уведомляем пользователя
        await bot.send_message(
            chat_id=user_id,
            text=f"😔 Ваша заявка <b>ОТКЛОНЕНА</b>.\n"
                 f"📊 Строка <b>{row_id}</b>: {sheets_status}\n"
                 f"📝 Причина: {reason}\n\n"
                 f"Пожалуйста, заполните заявку заново.",
            parse_mode="HTML"
        )
        
        # 3. Обновляем сообщение модератора
        moder_chat_id = data.get("moder_chat_id")
        moder_message_id = data.get("moder_message_id")
        await bot.edit_message_text(
            chat_id=moder_chat_id,
            message_id=moder_message_id,
            text=f"❌ Заявка <b>отклонена</b>\n\n"
                 f"👤 Пользователь ID: {user_id}\n"
                 f"📊 Строка <b>{row_id}</b>: {sheets_status}\n"
                 f"📁 Лист: {app_data.get('direction_name', 'Неизвестно')}\n"
                 f"👮 Модератор: @{moderator_username}\n"
                 f"📝 Причина: {reason}\n"
                 f"🕐 Время: {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}",
            reply_markup=None,
            parse_mode="HTML"
        )
        
        await message.answer(
            f"✅ Заявка пользователя <b>{user_id}</b> отклонена!\n"
            f"📊 Строка <b>{row_id}</b>: {sheets_status}\n"
            f"👤 Модератор: @{moderator_username}",
            parse_mode="HTML"
        )
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❗️ Не удалось отклонить заявку: {e}")
        await state.clear()