from aiogram.types import Message, CallbackQuery
from aiogram import Router, Bot, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from datetime import datetime
import pytz
from asyncio import sleep

from ..services import *

from ..lexicon import LEXICON_TEXT
from ..config import config
from ..filters import ModeratorChatFilter
from ..states import ModeratorStates
from ..keyboards import MenuKeyboard, ReRegister

moderator_router = Router()
moderator_router.message.filter(ModeratorChatFilter())
ekaterinburg_tz = pytz.timezone('Asia/Yekaterinburg')
menu_keyboard = MenuKeyboard.get_keyboard_menu()
re_register_keyboard = ReRegister.get_inline_keyboard()

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

    # Логгер
    bot_logger.log_moderator_msg(
    tg_id=str(callback.message.from_user.id),
    username= moderator_username,
    message=f"РЕГИСТРАЦИЯ: Начал принимать анкету пользователя {user_id}"
    )

    # Парсим анкету из сообщения
    form_data = parse_registration_form_from_message(callback.message.text or "", user_id, moderator_username, approval_date)

    if not form_data:
        await callback.answer("❌ Не удалось извлечь данные анкеты", show_alert=True)

        # Логгер
        bot_logger.log_moderator_msg(
        tg_id=str(callback.message.from_user.id),
        username= moderator_username,
        message=f"РЕГИСТРАЦИЯ: Ошибка извлечения данных из анкеты пользователя {user_id}"
        )

        return
    
    # Отправляем в Google Sheets
    sheets_result = googlesheet_service.add_participant(form_data)
    
    # Статус для модератора
    sheets_status = "✅ Добавлен в базу" if sheets_result["success"] else f"❌ {sheets_result.get('error', 'Ошибка')}"

    await callback.answer(f"✅ Анкета пользователя {user_id} одобрена!", show_alert=True)
    await callback.message.edit_text(
        f"✅ Анкета одобрена\n"
        f"👤 <b>ID пользователя:</b> {user_id}\n"
        f"📊 <b>Google Sheets:</b> {sheets_status}\n"
        f"👮 <b>Модератор:</b> @{callback.from_user.username or callback.from_user.full_name}\n"
        f"🕐 <b>Время:</b> {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}",
        reply_markup=None)
    
    # Логгер
    bot_logger.log_moderator_msg(
    tg_id=str(callback.message.from_user.id),
    username= moderator_username,
    message=f"РЕГИСТРАЦИЯ: заявка {user_id} одобрена, GoogleSheets: {sheets_status}"
    )

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
    
    # Логгер
    bot_logger.log_moderator_msg(
    tg_id=str(callback.from_user.id),
    username= callback.from_user.username,
    message=f"РЕГИСТРАЦИЯ: Начал отклонять анкету пользователя {user_id}"
    )

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
            text=f"😔 Ваша анкета отклонена.\n<b>Причина:</b> {reason}\n\nПожалуйста, заполните анкету заново.",
            reply_markup=re_register_keyboard
        )
        moder_chat_id = data.get("moder_chat_id")
        moder_message_id = data.get("moder_message_id")
        await bot.edit_message_text(
        chat_id=moder_chat_id,
        message_id=moder_message_id,
        text=f"❌ Анкета отклонена\n"
            f"👤 <b>Пользователь ID:</b> {user_id}\n"
            f"👮 <b>Модератор:</b> @{message.from_user.username or message.from_user.full_name}\n"
            f"📝 <b>Причина:</b> {reason}\n"
            f"🕐 <b>Время:</b> {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}",
            reply_markup=None
        )

        # Логгер
        bot_logger.log_moderator_msg(
        tg_id=str(message.from_user.id),
        username= message.from_user.username,
        message=f"РЕГИСТРАЦИЯ: Отклонил анкету {user_id} по причине: {reason}"
        )

        reason_msg = await message.answer(f"✅ Анкета пользователя {user_id} отклонена. Причина отправлена.")
        await sleep(10)
        await reason_msg.delete()
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
        
    parts = callback.data.split("_")
    user_id = int(parts[3]) 
    utc_time = callback.message.date
    ekaterinburg_time = utc_time.astimezone(ekaterinburg_tz)

    await callback.answer(f"✅ Обращение пользователя {user_id} закрыто!", show_alert=True)
    await callback.message.edit_text(
        f"✅ Вопрос закрыт\n"
        f"👤 <b>ID пользователя:</b> {user_id}\n"
        f"📝 {message_line}\n"
        f"👮 <b>Модератор:</b> @{callback.from_user.username or callback.from_user.full_name}\n"
        f"🕐 <b>Время:</b> {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}",
        reply_markup=None)

@moderator_router.callback_query(F.data.startswith("answer_user_"))
async def the_request_answer(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """
    Обрабатывает нажатие на кнопку ответить
    """
    parts = callback.data.split("_")
    user_id = int(parts[2])  
    message = parts[3]
    await state.update_data(
        support_user_id=user_id,
        moder_message_id=callback.message.message_id,
        original_message=message
    )
    await callback.message.answer(f"Введите ответ на обращение пользователя {user_id}:" )
    await state.set_state(ModeratorStates.waiting_edit_comment)

@moderator_router.message(F.text, StateFilter(ModeratorStates.waiting_edit_comment))
async def process_the_request_answer(message: Message, state: FSMContext, bot: Bot):
    utc_time = message.date
    ekaterinburg_time = utc_time.astimezone(ekaterinburg_tz)
    data = await state.get_data()
    user_id = data.get("support_user_id")
    original_message = data.get("original_message")
    answer = message.text
    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"📨 <b>Ответ от службы поддержки\nВаш вопрос:</b> {original_message}\n<b>Ответ:</b> {answer}\n\n💬 Если у вас остались вопросы, напишите нам снова!"
        )
        await message.answer(f"✅ Ответ пользователю {user_id} отправлен!")
        await state.clear()

        # Логгер
        bot_logger.log_moderator_msg(
        tg_id=str(message.from_user.id),
        username= message.from_user.username,
        message=f"ПОДДЕРЖКА: Ответил пользователю {user_id} по вопросу: {original_message}, Ответ: {answer}"
        )

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

    # Логгер
    bot_logger.log_moderator_msg(
    tg_id=str(callback.from_user.id),
    username= moderator_username,
    message=f"ЗАЯВКА: Начал принимать заявку {user_id} на получение 'ТИУКоинов'"
    )
    
    # Парсим заявку извлекаем row_id из сообщения
    message_text = callback.message.text or ""
    app_data = parse_event_application_from_message(message_text, user_id)
    
    # Извлекаем номер строки из сообщения из текста сообщения
    import re
    row_match = re.search(r"Строка:\s*(\d+)", message_text)
    row_id = int(row_match.group(1)) if row_match else 2
    
    # Обновляем статус в Google Sheets
    result = googlesheet_service.update_application_status(
        app_data.get("event_direction", ""), 
        row_id, 
        "Принята", 
        f"@{moderator_username}"
    )

    # Статус для модератора
    sheets_status = "✅ Обновлено" if result.get("success") else f"❌ {result.get('error', 'Ошибка')}"

    await callback.answer(f"✅ Заявка пользователя {user_id} одобрена!", show_alert=True)
    await callback.message.edit_text(
        f"✅ Заявка одобрена\n"
        f"👤 <b>Пользователь:</b> {app_data.get('full_name', '')} (ID: {user_id})\n"
        f"📊 Строка в Google Sheets <b>{row_id}</b>: {sheets_status}\n"
        f"📁 <b>Лист:</b> {app_data.get('event_direction', 'Неизвестно')}\n"
        f"👮 <b>Модератор:</b> @{moderator_username}\n"
        f"🕐 <b>Время одобрения:</b> {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}",
        reply_markup=None,
        parse_mode="HTML"
    )

    # Логгер
    bot_logger.log_moderator_msg(
    tg_id=str(callback.from_user.id),
    username= moderator_username,
    message=f"ЗАЯВКА: Принял заявку {user_id} на получение 'ТИУКоинов': {app_data.get("name_of_event")}, GoogleSheets: {app_data.get('event_direction', 'Неизвестно')}, {row_id}, {sheets_status}"
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
    
    # Парсим заявку извлекаем row_id из сообщения
    app_data = parse_event_application_from_message(message_text, user_id)

    # Извлекаем номер строки из сообщения из текста сообщения
    import re
    row_match = re.search(r"Строка:\s*(\d+)", message_text)
    row_id = int(row_match.group(1)) if row_match else 2
    
    moderator_username = message.from_user.username or message.from_user.full_name
    
    try:
        # Обновляем статус в Google Sheets
        sheets_result = googlesheet_service.update_application_status(
            app_data.get("event_direction", ""), 
            row_id, 
            "Отклонена", 
            f"@{moderator_username}"
        )
        sheets_status = "✅ Обновлено" if sheets_result.get("success") else f"❌ {sheets_result.get('error', 'Ошибка')}"
        
        # Уведомляем пользователя
        await bot.send_message(
            chat_id=user_id,
            text=(f"😔 Ваша заявка на получение ТИУКионов отклонена.\n<b>Мероприятие:</b> «{app_data.get("name_of_event")}»\n<b>Направление внеучебной деятельности:</b> «{app_data.get("event_direction")}»\n"
                 f"📝 <b>Причина:</b> {reason}\n\n"
                 f"Пожалуйста, заполните заявку заново."),
            parse_mode="HTML"
        )
        
        # Обновляем сообщение модератора
        moder_chat_id = data.get("moder_chat_id")
        moder_message_id = data.get("moder_message_id")

        # Логгер
        bot_logger.log_moderator_msg(
        tg_id=str(message.from_user.id),
        username= moderator_username,
        message=f"ЗАЯВКА: Отклонил заявку {user_id} на получение 'ТИУКоинов': {app_data.get("name_of_event")}, Причина: {reason} GoogleSheets: {app_data.get('event_direction', 'Неизвестно')}, {row_id}, {sheets_status}"
        )

        await bot.edit_message_text(
            chat_id=moder_chat_id,
            message_id=moder_message_id,
            text=f"❌ Заявка <b>отклонена</b>\n\n"
                 f"👤 <b>Пользователь</b> {app_data.get('full_name', '')}(ID: {user_id})\n"
                 f"📊 Строка в Google Sheets <b>{row_id}</b>: {sheets_status}\n"
                 f"📁 <b>Лист:</b> {app_data.get('event_direction', 'Неизвестно')}\n"
                 f"👮 <b>Модератор:</b> @{moderator_username}\n"
                 f"📝 <b>Причина:</b> {reason}\n"
                 f"🕐 <b>Время отклонения:</b> {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}",
            reply_markup=None,
            parse_mode="HTML"
        )
        reason_msg = await message.answer(f"✅ Заявка пользователя {user_id} отклонена. Причина отправлена.")
        await sleep(10)
        await reason_msg.delete()
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❗️ Не удалось отклонить заявку: {e}")
        await state.clear()