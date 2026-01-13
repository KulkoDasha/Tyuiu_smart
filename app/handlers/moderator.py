from typing import Dict, Any
from aiogram.types import Message, CallbackQuery
from aiogram import Router, Bot, F, Dispatcher
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from datetime import datetime
import pytz
from asyncio import sleep
from typing import Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError


from ..services import *
from database import *


from ..lexicon import LEXICON_TEXT, LEXICON_USER_KEYBOARD
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

@connection
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

    db_status = ""
    try:
        # Вызываем функцию set_user для добавления в БД
        success, message, user_id_in_db = await db_set_user( 
            tg_id_str=str(user_id),
            full_name=form_data.get('full_name', ''),
            institute=form_data.get('institute', ''),
            direction=form_data.get('direction', ''),
            group=form_data.get('group', ''),
            course_str=str(form_data.get('course', '')),
            start_year_str=str(form_data.get('start_year', '')),
            end_year_str=str(form_data.get('end_year', '')),
            phone_number=form_data.get('phone_number', ''),
            email=form_data.get('email', ''),
            moderator_username=moderator_username
        )
        
        if success and user_id_in_db:
            db_status = f"✅ Добавлен (ID: {user_id_in_db})"
        elif not success:
            db_status = f"❌ {message}"
        else:
            db_status = "❌ Ошибка: пользователь не добавлен"
                
    except Exception as e:
        db_status = f"❌ Ошибка PostgreSQL: {str(e)}"

    await callback.answer(f"✅ Анкета пользователя {user_id} одобрена!", show_alert=True)
    await callback.message.edit_text(
        f"✅ Анкета одобрена\n"
        f"👤 <b>ID пользователя:</b> {user_id}\n"
        f"📊 <b>Google Sheets:</b> {sheets_status}\n"
        f"💾 <b>База данных:</b> {db_status}\n"
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

@connection
@moderator_router.callback_query(F.data.startswith("approve_application_"))
async def approve_applications(callback: CallbackQuery, bot: Bot,state: FSMContext):
    """
    Обработка нажатия на кнопку Одобрить заявку
    """
    parts = callback.data.split("_")
    application_id = int(parts[2])
    user_id = int(parts[3])
    event_role = "_".join(parts[4:])
    utc_time = callback.message.date
    ekaterinburg_time = utc_time.astimezone(ekaterinburg_tz)
    moderator_username = callback.from_user.username or callback.from_user.full_name

    await state.update_data(
        application_id=application_id,
        user_id=user_id,
        moderator_username=moderator_username,
        event_role=event_role,
        callback_message_id=callback.message.message_id,
        chat_id=callback.message.chat.id
    )

    # Логгер
    bot_logger.log_moderator_msg(
    tg_id=str(callback.from_user.id),
    username= moderator_username,
    message=f"ЗАЯВКА: Начал принимать заявку {user_id} на получение 'ТИУКоинов'"
    )
    
    if event_role == LEXICON_USER_KEYBOARD["role_leader"][2:14]:
        await callback.message.answer(f"🔢 Введите коэффициент повторяемости для пользователя {user_id}:")
        await state.set_state(ModeratorStates.waiting_repeatability_factor)
        await callback.answer()
        return
    
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

    db_status = ""
    try:
        success, db_message, db_awarded_amount = await db_approve_application(
            application_id=application_id,
            moderator_username=moderator_username,
            tiukoins_amount=8.0  
        )
        db_status = f"✅ Обновлено (ID заявки: {application_id})" if success else f"❌ {db_message}"
    except Exception as e:
        db_status = f"❌ Ошибка: {str(e)}"

    await callback.answer(f"✅ Заявка пользователя {user_id} одобрена!", show_alert=True)
    await callback.message.edit_text(
        f"✅ Заявка одобрена\n"
        f"👤 <b>Пользователь:</b> {app_data.get('full_name', '')} (ID: {user_id})\n"
        f"💰 <b>Начислено:</b> {db_awarded_amount:.1f} ТИУкоинов\n"
        f"📊 Строка в Google Sheets <b>{row_id}</b>: {sheets_status}\n"
        f"📁 <b>Лист:</b> {app_data.get('event_direction', 'Неизвестно')}\n"
        f"💾 <b>База данных:</b> {db_status}\n"
        f"👮 <b>Модератор:</b> @{moderator_username}\n"
        f"🕐 <b>Время одобрения:</b> {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}",
        reply_markup=None,
        parse_mode="HTML"
    )

    # Логгер
    bot_logger.log_moderator_msg(
    tg_id=str(callback.from_user.id),
    username= moderator_username,
    message=f"ЗАЯВКА: Принял заявку {user_id} на получение 'ТИУКоинов': {app_data.get('name_of_event')}, GoogleSheets: {app_data.get('event_direction', 'Неизвестно')}, {row_id}, {sheets_status}"
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


@moderator_router.message(StateFilter(ModeratorStates.waiting_repeatability_factor))
async def waiting_repeatability_factor(message: Message, bot: Bot,state:FSMContext):
    """
    Обработка введенного коэффициента повторяемости
    """
    data = await state.get_data()
    user_id = data.get("user_id")
    application_id = data.get("application_id")
    print (application_id)
    moderator_username = data.get("moderator_username")
    row_id = data.get("row_id")
    app_data = data.get("app_data", {})
    
    utc_time = message.date
    ekaterinburg_time = utc_time.astimezone(ekaterinburg_tz)
    
    try:
        coefficient_float = float(message.text.strip())
        coins = 8  
        awarded_amount = coins * coefficient_float
        
        await message.answer(f"✅ Коэффициент {coefficient_float} сохранен для пользователя {user_id}")

        
        result = googlesheet_service.update_application_status(
            app_data.get("event_direction", ""), 
            row_id, 
            "Принята", 
            f"@{moderator_username}"
        )

        db_status = ""
        try:
            success, db_message, db_awarded_amount = await db_approve_application(
                application_id=application_id,
                moderator_username=moderator_username,
                tiukoins_amount= awarded_amount  
            )
            db_status = f"✅ Обновлено (ID заявки: {application_id})" if success else f"❌ {db_message}"
        except Exception as e:
            db_status = f"❌ Ошибка: {str(e)}"

        sheets_status = "✅ Обновлено" if result.get("success") else f"❌ {result.get('error', 'Ошибка')}"

        try:
            callback_message_id = data.get("callback_message_id")
            chat_id = data.get("chat_id")
            
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=callback_message_id,
                text=(
                    f"✅ Заявка одобрена\n"
                    f"👤 <b>Пользователь:</b> {app_data.get('full_name', '')} (ID: {user_id})\n"
                    f"📈 <b>Коэффициент:</b> {coefficient_float}\n"
                    f"💰 <b>Начислено:</b> {awarded_amount:.1f} ТИУкоинов\n"
                    f"📊 <b>Строка в Google Sheets</b> <b>{row_id}</b>: {sheets_status}\n"
                    f"💾 <b>База данных:</b> {db_status}\n"
                    f"📁 <b>Лист:</b> {app_data.get('event_direction', 'Неизвестно')}\n"
                    f"👮 <b>Модератор:</b> @{moderator_username}\n"
                    f"🕐 <b>Время одобрения:</b> {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}"
                ),
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Не удалось отредактировать сообщение: {e}")
        
        # Логгер
        bot_logger.log_moderator_msg(
            tg_id=str(message.from_user.id),
            username=moderator_username,
            message=f"ЗАЯВКА: Принял заявку {user_id} на получение 'ТИУКоинов': {app_data.get('name_of_event', '')}, Коэффициент: {coefficient_float}, Начислено: {awarded_amount}"
        )
        
        # Уведомляем пользователя
        try:
            await bot.send_message(
                chat_id=user_id,
                text=LEXICON_TEXT["application_event_completed"].format(awarded_amount=awarded_amount),
                reply_markup=menu_keyboard
            )
        except Exception as e:
            await message.answer(f"❗️ Не удалось уведомить пользователя {user_id}")
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число (например: 1.5 или 2). Попробуйте снова:")
    
@moderator_router.callback_query(F.data.startswith("decline_application_"))
async def decline_application(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает нажатие на кнопку отклонить заявку пользователя
    """
    parts = callback.data.split("_")
    application_id = int(parts[2])  
    user_id = int(parts[3])

    await callback.answer("❔ Укажите причину отклонения заявки пользователя", show_alert=False)
    await state.update_data(
        application_id=application_id,
        reject_user_id=user_id,
        moder_message_id=callback.message.message_id,
        moder_chat_id=callback.message.chat.id,
        moder_thread_id=callback.message.message_thread_id,
        message_text=callback.message.text or "" 
        )
    await callback.message.answer(f"❔ Введите причину отклонения заявки пользователя {user_id}:" )

    await state.set_state(ModeratorStates.waiting_reject_application_reason)

@connection
@moderator_router.message(F.text, StateFilter(ModeratorStates.waiting_reject_application_reason))
async def process_reject_reason(message: Message, state: FSMContext, bot: Bot):
    utc_time = message.date
    ekaterinburg_time = utc_time.astimezone(ekaterinburg_tz)
    data = await state.get_data()
    application_id = data.get("application_id")
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
        db_status = ""
        try:
            success, db_message = await db_reject_application(
                application_id,  
                moderator_username
            )
                
            if success:
                db_status = f"✅ Обновлен статус (ID заявки: {application_id})"
            else:
                db_status = f"❌ {db_message}"
        except Exception as e:
            db_status = f"❌ Ошибка PostgreSQL: {str(e)}"


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
            text=(f"😔 Ваша заявка на получение ТИУКионов отклонена.\n<b>Мероприятие:</b> «{app_data.get('name_of_event')}»\n<b>Направление внеучебной деятельности:</b> «{app_data.get('event_direction')}»\n"
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
        message=f"ЗАЯВКА: Отклонил заявку {user_id} на получение 'ТИУКоинов': {app_data.get('name_of_event')}, Причина: {reason} GoogleSheets: {app_data.get('event_direction', 'Неизвестно')}, {row_id}, {sheets_status}"
        )

        await bot.edit_message_text(
            chat_id=moder_chat_id,
            message_id=moder_message_id,
            text=f"❌ Заявка <b>отклонена</b>\n\n"
                 f"👤 <b>Пользователь</b> {app_data.get('full_name', '')}(ID: {user_id})\n"
                 f"📊 Строка в Google Sheets <b>{row_id}</b>: {sheets_status}\n"
                 f"📁 <b>Лист:</b> {app_data.get('event_direction', 'Неизвестно')}\n"
                 f"💾 <b>База данных:</b> {db_status}\n"
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

def parse_short_callback_data(callback_data: str) -> Dict[str, Any]:
    """
    Парсит данные из callback_data
    """
    print(f"🔍 '{callback_data}'")
    
    if callback_data.startswith("i_r_"):
        action = "issue"
        rest = callback_data[4:]
    elif callback_data.startswith("r_r_"):
        action = "reject"
        rest = callback_data[4:]
    else:
        return {}
    
    parts = rest.split("_", 3) 
    print(parts)
    if len(parts) == 4:
        short_req = parts[0]
        user_str = parts[1] 
        item_price = parts[2]
        item_id = parts[3]

        print(short_req,user_str, item_id, item_price)
        
        request_id = int(short_req)
        user_id = int(user_str) 

        return {
            "request_id": request_id,
            "user_id": user_id,
            "item_id": item_id,
            "item_price": item_price,
            "action": action
        }
    return {}

@connection
@moderator_router.callback_query(F.data.startswith(("i_r_", "r_r_")))
async def reward_action(callback: CallbackQuery, bot: Bot):
    """Объединённый "Выдать+Отклонить" в один хендлер"""
    
    try:
        await callback.answer("⏳ Обработка...", show_alert=False)
    except Exception:
        pass

    # Парсим callback_data
    data = parse_short_callback_data(callback.data)
    if not data:
        await callback.message.edit_text("❌ Ошибка данных кнопки!")
        return
    
    request_id = data["request_id"]
    user_id = data["user_id"]
    item_id = data["item_id"]
    item_price = data["item_price"]
    action = data["action"]
    
    # Быстрое название поощрения по айди
    item_name = get_item_name(item_id) if item_id else "Не указано"
    
    utc_time = callback.message.date
    ekaterinburg_time = datetime.now()
    moderator_username = callback.from_user.username or callback.from_user.full_name
    user_full_name = db_get_user_full_name( user_id)

    # Логика действия
    if action == "issue":
        # Выдача: update_status
        sheets_result = googlesheet_service.update_reward_status(request_id, "Выдано", moderator_username)
        sheets_status = f"✅ Строка {sheets_result.get('row', 'N/A')}" if sheets_result.get("success") else f"❌ {sheets_result.get('error', 'Ошибка')}"

        # Ответ модератору
        await callback.message.edit_text(
            f"✅ <b>Поощрение выдано!</b>\n\n"
            f"<b>Заявка №{request_id}</b>\n"
            f"<b>ФИО студента:</b> {user_full_name}\n"
            f"👤 <b>ID студента:</b> {user_id}\n"
            f"🎁 <b>Поощрение:</b> {item_name}\n"
            f"💎 <b>Стоимость:</b> {item_price} ТИУКоинов\n"
            f"📊 <b>Google Sheets:</b> {sheets_status}\n"
            f"👮 <b>Модератор:</b> @{moderator_username}\n"
            f"🕐 <b>Дата и время:</b> {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}",
            reply_markup=None, parse_mode="HTML"
        )
        
    else:  # reject
        # Отмена: update_status + cancel_reward_purchase (+1)
        sheets_result = googlesheet_service.update_reward_status(request_id, "Отменено", moderator_username)
        sheets_status = f"✅ Строка {sheets_result.get('row', 'N/A')}" if sheets_result.get("success") else f"❌ {sheets_result.get('error', 'Ошибка')}"

        success, message = await db_return_tiukoins( user_id, item_price)

        if success:
            tiukoins_status = f"💰 <b>ТИУКоины возвращены:</b> {item_price:.1f}"
        else:
            tiukoins_status = f"⚠️ <b>Ошибка возврата:</b> {message}"
        
        catalog_status = ""
        if item_id:
            catalog_result = googlesheet_service.cancel_reward_purchase(item_id) 
            catalog_status = f"📦 <b>Осталось:</b> {catalog_result.get('new_quantity', 0)} шт."

            # Ответ модератору
        await callback.message.edit_text(
            f"❌ <b>Выдача отменена!</b>\n\n"
            f"<b>Заявка №{request_id}</b>\n"
            f"<b>ФИО студента:</b> {user_full_name}\n"
            f"👤 <b>ID студента:</b> {user_id}\n"
            f"🎁 <b>Поощрение:</b> {item_name}\n"
            f"💎 <b>Стоимость:</b> {item_price} ТИУКоинов\n"
            f"📊 <b>Google Sheets:</b> {sheets_status}\n"
            f"{tiukoins_status}\n"
            f"{catalog_status}\n"
            f"👮 <b>Модератор:</b> @{moderator_username}\n"
            f"🕐 <b>Дата и время:</b> {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}",
            reply_markup=None, parse_mode="HTML"
        )
        
    # Логгер
    bot_logger.log_moderator_msg(
    tg_id=str(callback.from_user.id),
    username=callback.from_user.username,
    message=f"ПООЩРЕНИЕ: Модератор {'выдал поощрение' if action=='issue' else 'ОТМЕНИЛ выдачу поощрения'}\n"
        f"Заявка №{request_id}\n"
        f"ФИО пользователя: {user_full_name}\n"
        f"ID пользователя: {user_id}\n"
        f"Google Sheets:{sheets_status}\n"
        f"Поощрение: {item_name}\n"
        f"Стоимость: {item_price}"
    )

    # Уведомляем студента
    try:
        status_emoji = "✅" if action == "issue" else "❌"
        student_text = (
            f"{status_emoji} <b>{'Поощрение выдано!' if action=='issue' else 'Выдача отменена!'}</b>\n\n"
            f"<b>Заявка №{request_id}</b>\n"
            f"🎁 <b>Поощрение:</b> {item_name}\n"
            f"💎 <b>Стоимость:</b> {item_price} ТИУКоинов\n"
            f"🕐 <b>Дата и время:</b> {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}"
       )
        if action == "reject":
            student_text += f"\n\n<i>ТИУКоины возвращены!</i> ({item_price})\nПри необходимости обратитесь в поддержку."
        
        await bot.send_message(
            chat_id=user_id,
            text=student_text,
            parse_mode="HTML", 
            reply_markup=menu_keyboard
        )
        await callback.answer(f"✅ Студент {user_id} уведомлён!", show_alert=True)

    except Exception:
        await callback.answer(f"❌ Студент не {user_id} уведомлён!", show_alert=True)



@moderator_router.message(F.text == "ТЕСТ УДАЛЕНИЯ")
async def cmd_delete_user(message: Message, state: FSMContext):
    await message.answer(
        "👤 Введите Telegram ID для удаления:\n"
        "💡 Пример: `1293014025`",
        parse_mode="Markdown"
    )
    await state.set_state(ModeratorStates.waiting_delete_user_tg_id)

@moderator_router.message(ModeratorStates.waiting_delete_user_tg_id)
async def process_delete_user(message: Message, state: FSMContext):
    tg_id = message.text.strip()
    await message.answer("🔄 Проверяю и удаляю...")
    
    success, result_msg = await db_delete_user_by_tg_id(tg_id)
    
    await message.answer(result_msg)
    await state.clear()