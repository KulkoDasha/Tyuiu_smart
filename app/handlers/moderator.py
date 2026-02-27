from typing import Dict, Any
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram import Router, Bot, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from datetime import datetime
import pytz
from asyncio import sleep

from database import *
from ..services import *
from ..lexicon import LEXICON_TEXT, ROLE_LEXICON 
from ..filters import ModeratorChatFilter
from ..states import ModeratorStates
from ..keyboards import MenuKeyboard, ReRegister

moderator_router = Router()
moderator_router.message.filter(ModeratorChatFilter())
ekaterinburg_tz = pytz.timezone('Asia/Yekaterinburg')
menu_keyboard = MenuKeyboard.get_keyboard_menu()
re_register_keyboard = ReRegister.get_inline_keyboard()


@moderator_router.callback_query(F.data.startswith("accept_user"))
async def approve_application(callback: CallbackQuery, bot: Bot, ):
    """Обрабатывает нажатие на кнопку принять анкету пользователя"""
    
    try:
        await callback.answer("⏳ Обрабатываем...", show_alert = False)
    except Exception:
        pass
    
    await callback.message.edit_reply_markup(reply_markup = None)
    
    user_id = int(callback.data.split("_")[-1])
    
    ekaterinburg_time = callback.message.date.astimezone(ekaterinburg_tz)

    moderator_username = f'@{callback.from_user.username}' or callback.from_user.full_name or "Unknown"
    approval_date = ekaterinburg_time.strftime('%d.%m.%Y %H:%M')
    user_full_name = await db_get_user_full_name(tg_id_str=str(user_id))

    db_status = ""
    try:
        # Вызываем функцию db_update_user для обновления записи в БД
        db_success, db_user_message, user_id_in_db, db_log_message = await db_update_user( 
            tg_id_str=str(user_id),
            moderator_username=moderator_username
        )
        
        if db_success and user_id_in_db:
            db_status = f"✅ Обновлено (ID: {user_id_in_db})"
        elif not db_success:
            db_status = f"❌ {db_user_message}"

            bot_logger.log_moderator_msg(
            tg_id=callback.from_user.id,
            message=f"РЕГИСТРАЦИЯ: ❌ Ошибка БД\n"
                    f"Пользователь: {pii_masker.mask_full_name(user_full_name)} (ID: {user_id})\n"
                    f"База данных: {db_log_message}"
        )
        else:
            db_status = "❌ Ошибка: Информация не обновлена"
             
    except Exception as e:
        db_status = f"❌ Ошибка: {db_user_message}"

        bot_logger.log_moderator_msg(
            tg_id=callback.from_user.id,
            message=f"РЕГИСТРАЦИЯ: ❌ Критическая ошибка\n"
                    f"Пользователь: {pii_masker.mask_full_name(user_full_name)} (ID: {user_id})\n"
                    f"База данных: {db_log_message}"
                    f"Ошибка: {str(e)}"
        )

    bot_logger.log_moderator_msg(
            tg_id=callback.from_user.id,
            message=f"РЕГИСТРАЦИЯ: ✅ Анкета одобрена\n"
                    f"Пользователь: {pii_masker.mask_full_name(user_full_name)} (ID: {user_id})\n"
                    f"База данных: {db_status}"
        )

    await callback.answer(f"✅ Пользователь {user_id} успешно добавлен!", show_alert = True)
    await callback.message.edit_text(
        f"✅ <b>Пользователь зарегистрирован</b>\n\n"
        f"👤 <b>Пользователь:</b> {user_id}\n"
        f"💾 <b>База данных:</b> {db_status}\n"
        f"👮 <b>Модератор:</b> {moderator_username}\n"
        f"🕐 <b>Время:</b> {approval_date}",
        reply_markup = None)
    
    try:
        await bot.send_message(
            chat_id = user_id,
            text = LEXICON_TEXT["approve_registration"], reply_markup = menu_keyboard
        )
        
    except Exception as e:
        await callback.message.answer(f"❗️ Не удалось уведомить пользователя {user_id}")

@moderator_router.callback_query(F.data.startswith("reject_user"))
async def decline_application(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает нажатие на кнопку отклонить анкету пользователя"""
    
    user_id = int(callback.data.split("_")[-1])
    await callback.message.edit_reply_markup(reply_markup = None)

    await callback.answer()
    await state.update_data(
        reject_user_id = user_id,
        moder_message_id = callback.message.message_id,
        moder_chat_id = callback.message.chat.id,
        moder_thread_id = callback.message.message_thread_id
    )
    await callback.message.answer(f"❔ Введите причину отклонения анкеты пользователя {user_id}:" )
    await state.set_state(ModeratorStates.waiting_reject_reason)

@moderator_router.message(F.text, StateFilter(ModeratorStates.waiting_reject_reason))
async def process_reject_reason(message: Message, state: FSMContext, bot: Bot):
    """Процесс отклонения анкеты пользователя"""
    
    ekaterinburg_time = message.date.astimezone(ekaterinburg_tz)
    data = await state.get_data()
    user_id = data.get("reject_user_id")
    reason = message.text
    user_full_name = await db_get_user_full_name(tg_id_str=str(user_id))

    try:

        try:
            # Вызываем функцию для удаления записи из БД
            db_success, db_user_message, user_id_in_db, db_log_message = await db_delete_user_by_tg_id( 
                tg_id_str=str(user_id),
            )
            
            if db_success:
                db_status = f"✅ Успешно"
            else:
                db_status = f"❌ {db_user_message}"
                    
        except Exception as e:
            db_status = f"❌ Ошибка: {db_user_message}"

            bot_logger.log_moderator_msg(
                tg_id=message.from_user.id,
                message=f"РЕГИСТРАЦИЯ: ❌ Ошибка БД при отклонении\n"
                        f"Пользователь: {pii_masker.mask_full_name(user_full_name)} (ID: {user_id})\n"
                        f"База данных: {db_log_message}"
            )

        moder_chat_id = data.get("moder_chat_id")
        moder_message_id = data.get("moder_message_id")

        bot_logger.log_moderator_msg(
            tg_id=message.from_user.id,
            message=f"РЕГИСТРАЦИЯ: ❌ Анкета отклонена\n"
                    f"Пользователь ID: {user_id}\n"
                    f"Причина: {reason}"
        )

        await bot.edit_message_text(
        chat_id = moder_chat_id,
        message_id = moder_message_id,
        text = f"❌ <b>Отклонено</b>\n\n"
            f"👤 <b>ID пользователя:</b> {user_id}\n"
            f"📝 <b>Причина:</b> {reason}\n"
            f"👮 <b>Модератор:</b> @{message.from_user.username or message.from_user.full_name}\n"
            f"🕐 <b>Время:</b> {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}",
            reply_markup = None
        )

        await bot.send_message(
            chat_id = user_id,
            text = f"😔 К сожалению вы не прошли регистрацию.\n\n<b>Причина:</b> {reason}\n\nПожалуйста, пройдите процедуру регистрации заново. Если у вас есть вопросы - обращайтесь в поддержку в /support.",
            reply_markup = re_register_keyboard
        )

        reason_msg = await message.answer(f"✅ Анкета пользователя {user_id} отклонена. Причина отправлена.")
        await sleep(7)
        await reason_msg.delete()
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❗️ Не удалось уведомить пользователя")
        await state.clear()

@moderator_router.callback_query(F.data.startswith("close_the_request"))
async def close_the_request(callback: CallbackQuery):
    """Обрабатывает нажатие на кнопку закрыть обращение"""
    
    await callback.message.edit_reply_markup(reply_markup = None)
    current_text = callback.message.text
    lines = current_text.split('\n')
   
    message_line = None
    for line in lines:
        if line.strip().startswith("Сообщение:"):
            message_line = line.strip()
            return
    
    if message_line:
        message_line = message_line.replace("Сообщение:", "<b>Сообщение:</b>")
    
    parts = callback.data.split("_")
    user_id = int(parts[3]) 
    ekaterinburg_time = callback.message.date.astimezone(ekaterinburg_tz)

    await callback.answer(f"✅ Обращение пользователя {user_id} закрыто!", show_alert = True)
    await callback.message.edit_text(
        f"✅ <b>Обращение пользователя закрыто</b>\n\n"
        f"👤 <b>ID пользователя:</b> {user_id}\n"
        f"📝 {message_line}\n"
        f"👮 <b>Модератор:</b> @{callback.from_user.username or callback.from_user.full_name}\n"
        f"🕐 <b>Время:</b> {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}",
        reply_markup = None)

@moderator_router.callback_query(F.data.startswith("answer_user_"))
async def the_request_answer(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает нажатие на кнопку ответить в поддержке"""
    
    parts = callback.data.split("_")
    user_id = int(parts[2])  
    current_text = callback.message.text
    lines = current_text.split('\n')
   
    message_line = None
    for line in lines:
        if line.strip().startswith("Сообщение:"):
            message_line = line.strip()
            break
    
    if message_line:
        message_line = message_line.replace("Сообщение:", "")
        
    await state.update_data(
        support_user_id = user_id,
        moder_message_id = callback.message.message_id,
        original_message = message_line
    )
    await callback.message.answer(f"Введите ответ на обращение пользователя {user_id}:" )
    await state.set_state(ModeratorStates.waiting_appeal_answer)

@moderator_router.message(F.text, StateFilter(ModeratorStates.waiting_appeal_answer))
async def process_the_request_answer(message: Message, state: FSMContext, bot: Bot):
    """Процесс ответа на вопрос в поддержке"""
    
    data = await state.get_data()
    user_id = data.get("support_user_id")
    original_message = data.get("original_message")
    answer = message.text

    try:
        await bot.send_message(
            chat_id = user_id,
            text = f"📨 <b>Ответ от службы поддержки\n\nВаш вопрос:</b>{original_message}\n<b>Ответ:</b> {answer}\n\n💬 Если у вас остались вопросы, напишите нам снова!",
            reply_markup = ReplyKeyboardRemove()
        )
        await message.answer(f"✅ Ответ пользователю {user_id} отправлен!")
        await state.clear()
    except Exception as e:
        await message.answer(f"❗️ Не удалось отправить ответ пользователю")
        await state.clear()

@connection
@moderator_router.callback_query(F.data.startswith("approve_application_"))
async def approve_application(callback: CallbackQuery, bot: Bot,state: FSMContext):
    """Обработка нажатия на кнопку Одобрить заявку"""
    
    await callback.message.edit_reply_markup(reply_markup=None)

    try:
        await callback.answer("⏳ Обработка...", show_alert=False)
    except Exception:
        pass
    
    parts = callback.data.split("_")
    application_id = int(parts[2])

    user_id = int(parts[3])
    event_role = parts[4]
    db_application_id = int(parts[5])
    ekaterinburg_time = callback.message.date.astimezone(ekaterinburg_tz)
    moderator_username = callback.from_user.username or callback.from_user.full_name
    
    # Парсим заявку извлекаем row_id из сообщения
    message_text = callback.message.text or ""
    app_data = parse_event_application_from_message(message_text, user_id)
    
    # Извлекаем номер строки из сообщения из текста сообщения
    import re
    row_match = re.search(r'строка\s*(\d+)', message_text)
    row_id = int(row_match.group(1)) if row_match else int(application_id+1)

    await state.update_data(
        application_id = application_id,
        db_application_id = db_application_id,
        event_direction = app_data.get('event_direction'),
        user_id = user_id,
        name_of_event = app_data.get('name_of_event'),
        moderator_username = moderator_username,
        event_role = event_role,
        callback_message_id = callback.message.message_id,
        chat_id = callback.message.chat.id,
        row_id = row_id
    )
    
    await process_regular_application(callback, bot, state, user_id, moderator_username,
                                      app_data, row_id, event_role, db_application_id,
                                      ekaterinburg_time)
    await callback.answer()

async def process_regular_application(callback: CallbackQuery,bot: Bot, state:FSMContext,
                                      user_id: int, moderator_username: str,
                                      app_data: dict, row_id: int, event_role: str,
                                      db_application_id: int, ekaterinburg_time):
    """Обработка заявки"""
    coins = ROLE_LEXICON[event_role]
    db_status, db_log_message = await approve_db(db_application_id, moderator_username, coins)
    if db_status.startswith("❌"):
        await callback.message.edit_text("❗️ Произошла ошибка при сохранении в базу данных. Обратитесь к разработчику с данной проблемой.")

        bot_logger.log_moderator_msg(
            tg_id=callback.from_user.id,
            message=f"ЗАЯВКА: ❌ Ошибка БД при принятии\n"
                    f"Пользователь: {pii_masker.mask_full_name(app_data.get('full_name', ''))} (ID: {user_id})\n"
                    f"База данных: {db_log_message}"
        )

        await state.clear()
        return
    
    try:
        await send_message(callback, user_id, app_data, coins,
                           db_status, moderator_username, ekaterinburg_time, bot, row_id)
        
        bot_logger.log_moderator_msg(
            tg_id=callback.from_user.id,
            message=f"ЗАЯВКА: ✅ Одобрена\n"
                    f"Пользователь: {pii_masker.mask_full_name(app_data.get('full_name', ''))} (ID: {user_id})\n"
                    f"Направление: {app_data.get('event_direction', 'Неизвестно')}\n"
                    f"Мероприятие: {app_data.get('name_of_event')}\n"
                    f"Начислено: {coins} ТИУкоинов\n"
                    f"База данных: {db_status}\n"
        )

    except Exception:
        await callback.message.answer('Не удалось отправить ответ пользователю')
    
async def approve_db(db_application_id: int, moderator_username: str, coins:float):
    """Отправляет заявку в БД"""
    
    db_status = ""

    try:
        db_success, db_user_message, db_awarded_amount, db_log_message = await db_approve_application(
            application_id = db_application_id,
            moderator_username = moderator_username,
            tiukoins_amount = coins
        )
        db_status = f"✅ Обновлено (ID: {db_application_id})" if db_success else f"❌ {db_user_message}"
    except Exception as e:
        db_status = f"❌ Ошибка: {db_user_message}"
        
    return db_status, db_log_message

async def send_message(callback: CallbackQuery, user_id: int,
                       app_data: dict, coins: float,
                       db_status, moderator_username: str,
                       ekaterinburg_time, bot: Bot, row_id):
    """Отправляет сообщение пользователю и модератору"""
    
    await callback.answer(f"✅ Заявка пользователя {user_id} одобрена!", show_alert  = True)
    await callback.message.edit_text(
            f"✅ <b>Заявка одобрена</b>\n\n"
            f"👤 <b>Пользователь:</b> {user_id}\n"
            f"💎 <b>Начислено:</b> {coins} ТИУкоинов\n"
            f"💾 <b>База данных:</b> {db_status}\n"
            f"👮 <b>Модератор:</b> @{moderator_username}\n"
            f"🕐 <b>Время одобрения:</b> {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}",
            reply_markup = None, parse_mode = "HTML"
        )
    
    await bot.send_message(
                chat_id = user_id,
                text = (f"😊 Ваша заявка на получение ТИУкионов подтверждена.\n\n<b>📌 Мероприятие:</b> «{app_data.get('name_of_event')}»\n<b>🎯 Направление внеучебной деятельности:</b> {app_data.get('event_direction')}\n"
                 f"<b>💎 Вам начислено:</b> {coins} ТИУкоинов"),
                reply_markup = menu_keyboard
            )
    
@moderator_router.callback_query(F.data.startswith("decline_application_"))
async def decline_application(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает нажатие на кнопку отклонить заявку пользователя"""
    
    try:
        await callback.answer("⏳ Обработка...", show_alert = False)
    except Exception:
        pass
    
    await callback.message.edit_reply_markup(reply_markup = None)
    
    parts = callback.data.split("_")
    application_id = int(parts[2])
    user_id = int(parts[3])
    db_application_id = int(parts[5])

    await state.update_data(
        application_id = application_id,
        db_application_id = db_application_id,
        reject_user_id = user_id,
        moder_message_id = callback.message.message_id,
        moder_chat_id = callback.message.chat.id,
        moder_thread_id = callback.message.message_thread_id,
        message_text = callback.message.text or "" 
        )
    await callback.message.answer(f"❔ Введите причину отклонения заявки пользователя {user_id}:" )

    await state.set_state(ModeratorStates.waiting_reject_application_reason)

@connection
@moderator_router.message(F.text, StateFilter(ModeratorStates.waiting_reject_application_reason))
async def process_reject_reason(message: Message, state: FSMContext, bot: Bot):
    """Процесс отмены заявки пользователя"""
    
    ekaterinburg_time = message.date.astimezone(ekaterinburg_tz)
    data = await state.get_data()
    application_id = data.get("application_id")
    db_application_id = data.get("db_application_id")
    user_id = data.get("reject_user_id")
    reason = message.text
    message_text = data.get("message_text", "")
    
    # Парсим заявку извлекаем row_id из сообщения
    app_data = parse_event_application_from_message(message_text, user_id)

    # Извлекаем номер строки из сообщения из текста сообщения
    import re
    row_match = re.search(r'строка\s*(\d+)', message_text)
    row_id = int(row_match.group(1)) if row_match else int(application_id+1)
    
    moderator_username = message.from_user.username or message.from_user.full_name
    
    try:
        db_status = ""
        try:
            db_success, db_user_message, db_log_message = await db_reject_application(
                db_application_id,  
                moderator_username
            )
                
            if db_success:
                db_status = f"✅ Обновлено (ID: {db_application_id})"
            else:
                db_status = f"❌ {db_user_message}"
        except Exception as e:
            db_status = f"❌ Ошибка Базы данных: {db_user_message}"
        
        bot_logger.log_moderator_msg(
            tg_id=message.from_user.id,
            message=f"ЗАЯВКА: ❌ Отклонена\n"
                    f"Пользователь: {pii_masker.mask_full_name(app_data.get('full_name', ''))} (ID: {user_id})\n"
                    f"Направление: {data.get('event_direction', 'Неизвестно')}\n"
                    f"Мероприятие: {data.get('name_of_event')}\n"
                    f"База данных: {db_log_message}"
        )

        # Обновляем сообщение модератора
        moder_chat_id = data.get("moder_chat_id")
        moder_message_id = data.get("moder_message_id")

        await bot.edit_message_text(
            chat_id = moder_chat_id,
            message_id = moder_message_id,
            text = f"❌ <b>Заявка отклонена</b>\n\n"
                 f"👤 <b>Пользователь:</b> {user_id}\n"
                 f"📝 <b>Причина:</b> {reason}\n"
                 f"💾 <b>База данных:</b> {db_status}\n"
                 f"👮 <b>Модератор:</b> @{moderator_username}\n"
                 f"🕐 <b>Время отклонения:</b> {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}",
            reply_markup = None,
            parse_mode = "HTML"
        )

        # Уведомляем пользователя
        await bot.send_message(
            chat_id = user_id,
            text = (f"😔 Ваша заявка на получение ТИУкоинов отклонена.\n\n<b>📌 Мероприятие:</b> «{app_data.get('name_of_event')}»\n<b>🎯 Направление внеучебной деятельности:</b> {app_data.get('event_direction')}\n"
                 f"📝 <b>Причина:</b> {reason}\n\n"
                 f"Пожалуйста, заполните заявку заново."),
            parse_mode = "HTML"
        )
        
        reason_msg = await message.answer(f"✅ Заявка пользователя {user_id} отклонена. Причина отправлена.")
        await sleep(5)
        await reason_msg.delete()
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❗️ Не удалось отклонить заявку. Обратитесь с проблемой к разработчику.")

        bot_logger.log_moderator_msg(
            tg_id=message.from_user.id,
            message=f"ЗАЯВКА: ❌ Ошибка отклонения\n"
                    f"Пользователь: {pii_masker.mask_full_name(app_data.get('full_name', ''))} (ID: {user_id})\n"
                    f"Направление: {data.get('event_direction', 'Неизвестно')}\n"
                    f"Мероприятие: {data.get('name_of_event')}\n"
                    f"База данных: {db_log_message}\n"
                    f"Ошибка: {str(e)}"
        )

        await state.clear()

def parse_short_callback_data(callback_data: str) -> Dict[str, Any]:
    """Парсит данные из callback_data"""
    
    if callback_data.startswith("i_r_"):
        action = "issue"
        rest = callback_data[4:]
    elif callback_data.startswith("r_r_"):
        action = "reject"
        rest = callback_data[4:]
    else:
        return {}
    
    parts = rest.split("_", 3) 
    if len(parts) == 4:
        short_req = parts[0]
        user_str = parts[1] 
        item_price = parts[2]
        item_id = parts[3]
        
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
        await callback.answer("⏳ Обрабатываем...", show_alert = False)
    except Exception:
        pass
    
    await callback.message.edit_reply_markup(reply_markup=None)
    
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
    
    # TODO: сделать связь с яндекс таблицами
    item_name = "pass"
    catalog_status = "pass"
    ekaterinburg_time = datetime.now()
    moderator_username = callback.from_user.username or callback.from_user.full_name
    user_full_name = await db_get_user_full_name( str(user_id))

    # Логика действия
    if action == "issue":

        bot_logger.log_moderator_msg(
            tg_id=callback.from_user.id,
            message=f"ПООЩРЕНИЕ: ✅ Выдано\n"
                    f"Заявка №{request_id}\n"
                    f"Пользователь: {pii_masker.mask_full_name(user_full_name)} (ID: {user_id})\n"
                    f"Товар: {item_name}\n"
                    f"Цена: {item_price} ТИУкоинов\n"
        )


        # Ответ модератору
        await callback.message.edit_text(
            f"✅ <b>Поощрение выдано!</b>\n\n"
            f"<b>Заявка №{request_id}</b>\n"
            f"<b>Пользователь:</b> {user_full_name} (ID: {user_id})\n\n"
            f"🎁 <b>Поощрение:</b> {item_name}\n"
            f"💎 <b>Стоимость:</b> {item_price} ТИУкоинов\n"
            f"👮 <b>Модератор:</b> @{moderator_username}\n"
            f"🕐 <b>Дата и время:</b> {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}",
            reply_markup = None, parse_mode = "HTML"
        )
        
    else:  # reject

        db_success, db_user_message, db_log_message = await db_reject_issuance( tg_id_str = str(user_id), issuance_id = item_price)

        if db_success:
            tiukoins_status = f"💎 <b>ТИУкоины возвращены:</b> {item_price}"
        else:
            tiukoins_status = f"⚠️ <b>Ошибка возврата:</b> {db_user_message}"

            bot_logger.log_moderator_msg(
            tg_id=callback.from_user.id,
            message=f"ПООЩРЕНИЕ: ❌ Ошибка возврата ТИУКоинов\n"
                    f"Заявка №{request_id}\n"
                    f"Пользователь: {pii_masker.mask_full_name(user_full_name)} (ID: {user_id})\n"
                    f"Поощрение: {item_name}\n"
                    f"Цена: {item_price} ТИУкоинов\n"
                    f"База данных: {db_log_message}\n"
                    f"ТИУкоины возвращены: {item_price}"
        )
        
        bot_logger.log_moderator_msg(
            tg_id=callback.from_user.id,
            message=f"ПООЩРЕНИЕ: ❌ Отменено\n"
                    f"Заявка №{request_id}\n"
                    f"Пользователь: {pii_masker.mask_full_name(user_full_name)} (ID: {user_id})\n"
                    f"Товар: {item_name}\n"
                    f"Цена: {item_price} ТИУкоинов\n"
                    f"ТИУкоины возвращены: {item_price}"
        )

            # Ответ модератору
        await callback.message.edit_text(
            f"❌ <b>Выдача отменена!</b>\n\n"
            f"<b>Заявка №{request_id}</b>\n"
            f"<b>Пользователь:</b> {user_full_name} (ID: {user_id})\n\n"
            f"🎁 <b>Поощрение:</b> {item_name}\n"
            f"💎 <b>Стоимость:</b> {item_price} ТИУкоинов\n"
            f"{tiukoins_status}\n"
            f"{catalog_status}\n"
            f"👮 <b>Модератор:</b> @{moderator_username}\n"
            f"🕐 <b>Дата и время:</b> {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}",
            reply_markup=None, parse_mode="HTML"
        )

    # Уведомляем студента
    try:
        status_emoji = "✅" if action == "issue" else "❌"
        student_text = (
            f"{status_emoji} <b>{'Поощрение выдано!' if action == 'issue' else 'Выдача отменена!'}</b>\n\n"
            f"<b>Заявка №{request_id}</b>\n"
            f"🎁 <b>Поощрение:</b> {item_name}\n"
            f"💎 <b>Стоимость:</b> {item_price} ТИУкоинов\n"
            f"🕐 <b>Дата и время:</b> {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}"
       )
        if action == "reject":
            student_text += f"\n\n<i>ТИУкоины возвращены!</i> ({item_price})\nПри необходимости обратитесь в поддержку /support"
        
        await bot.send_message(
            chat_id = user_id,
            text = student_text,
            parse_mode = "HTML", 
            reply_markup = menu_keyboard
        )
        await callback.answer(f"✅ Студент {user_id} уведомлён!", show_alert = True)

    except Exception:
        await callback.answer(f"❌ Студент {user_id} не уведомлён!", show_alert = True)