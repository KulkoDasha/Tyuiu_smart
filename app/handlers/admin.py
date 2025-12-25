from aiogram.types import Message, CallbackQuery
from aiogram import Router, Bot, F
from aiogram.filters import Command, StateFilter, Filter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
import time

from ..config import config
from ..filters import AdminChatFilter
from ..keyboards import AdminPanelInlineButtons
from ..states import *

admin_router = Router()
admin_router.message.filter(AdminChatFilter())

@admin_router.message(Command("checkadmin"))
async def check_in_admin_chat(message: Message):
    """
    Проверяет, написано сообщение в чате админ-панели или нет
    """

    await message.answer("Да, это чат админ-панели")

# @admin_router.message(Command("menu"))
# async def admin_menu(message: Message):
#     """
#     Отправляет меню админ панели
#     """

#     keyboard = AdminPanelInlineButtons.get_inline_keyboard()
#     await message.answer("<b>Меню админ-панели</b>\nВыберите действие:", reply_markup=keyboard)

@admin_router.message(Command("all_notification"))
async def notify_all_users_message(message: Message, state: FSMContext):
    """
    Запускает процесс рассылки уведомления всем пользователям
    """

    await message.delete()
    await state.set_state(NotifificationAllUsers.waiting_for_message)
    await message.answer("Напишите сообщение для рассылки всем пользователям.",callback_data="notification_for_all_message")

@admin_router.message(NotifificationAllUsers.waiting_for_message)
async def process_notify_all_users_message(callback: CallbackQuery, state: FSMContext):
    """
    Начинает рассылку уведомления всем пользователям
    """

    await callback.message.answer("Рассылка уведомления всем пользователям начата.")
    # ТУТ БУДЕМ ПАРСИТЬ ВСЕ ID ИЗ БАЗЫ ДАННЫХ И ОТПРАВЛЯТЬ СООБЩЕНИЯ ВСЕМ
    await callback.message.answer("Уведомление всем пользователям отправлено.")
    await state.clear()

@admin_router.message(Command("user_notification"))
async def notify_user_message(message: Message, state: FSMContext):
    """
    Запускает процесс рассылки уведомления конкретному пользователю
    """

    await message.delete()

    sent_message =  await message.answer("Введите ID пользователя для отправки уведомления.")
    await state.set_state(NotificationUser.waiting_for_user_id)
    await state.update_data(bot_message_id=sent_message.message_id)

@admin_router.message(NotificationUser.waiting_for_user_id)
async def process_notify_user_message(message: Message, state: FSMContext):
    """
    Принимает ID пользователя и запрашивает сообщение для отправки
    """
    
    await message.delete()

    data = await state.get_data()

    bot_message_id = data.get('bot_message_id')
    try:
        await message.bot.delete_message(message.chat.id, bot_message_id)
    except:
        pass

    await state.update_data(user_id = message.text)
    sent_message = await message.answer(f"Введите сообщение для отправки пользователю <b>{message.text}</b>")
    await state.update_data(bot_message_id=sent_message.message_id)
    await state.set_state(NotificationUser.waiting_for_message)

@admin_router.message(NotificationUser.waiting_for_message)
async def process_notify_user_message_final(message: Message, state: FSMContext, bot: Bot):
    """
    Завершает отправку уведомления конкретному пользователю
    """

    await message.delete()
    await state.update_data(message_for_user = message.text)

    data = await state.get_data()
    bot_message_id = data.get('bot_message_id')
    try:
        await message.bot.delete_message(message.chat.id, bot_message_id)
    except:
        pass
    
    user_id = data.get("user_id")
    message_for_user = data.get("message_for_user")

    try:
        await bot.send_message(
            chat_id=user_id,
            text = f"✉️ Новое уведомление от бота\n\n<b>{message_for_user}</b>"
        )
        await message.answer(f"✅ Уведомление пользователю {user_id} отправлено!\n\nТекст уведомления: <b>{message_for_user}</b>",
                             show_alert=True)
    except:
        await message.answer(f"❌ Не удалось отправить уведомление пользователю {user_id}!\n\nТекст уведомления: <b>{message_for_user}</b>", show_alert=True)

    await state.clear()
