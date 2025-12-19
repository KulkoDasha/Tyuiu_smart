from aiogram.types import Message, CallbackQuery
from aiogram import Router, Bot, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from datetime import datetime
import pytz
import logging


from services.googlesheets_service import googlesheet_service
from services.parser_registration_form_service import parse_registration_form_from_message

from lexicon import LEXICON_TEXT
from config.config import config
from filters import ModeratorChatFilter
from states.admin_states import ModeratorStates
from keyboards.user_keyboard import MenuKeyboard


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

    await callback.answer(f"✅ Анкета пользователя {user_id} одобрена!", show_alert=True, reply_murkup = menu_keyboard)
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
            text=LEXICON_TEXT["registration_completed"]
        )
    except Exception as e:
        await callback.message.answer(f"❗️ Не удалось уведомить пользователя {user_id}")

@moderator_router.callback_query(F.data.startswith("reject_user"))
async def decline_application(callback: CallbackQuery, bot: Bot, state: FSMContext):
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
