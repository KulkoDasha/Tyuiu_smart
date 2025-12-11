from aiogram.types import Message, CallbackQuery
from aiogram import Router, Bot, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
import time

from config.config import config
from filters import AdminChatFilter
from keyboards import AdminPanelInlineButtons
from states import NotifificationAllUsers, NotificationUser

admin_router = Router()
admin_router.message.filter(AdminChatFilter())

@admin_router.message(Command("checkadmin"))
async def check_in_admin_chat(message:Message):

    """
    Проверяет, написано сообщение в чате админ-панели или нет
    """
    await message.answer("Да, это чат админ-панели")

@admin_router.message(Command("menu"))
async def admin_menu(message:Message):
    """
    Отправляет меню админ панели
    """
    keyboard = AdminPanelInlineButtons.get_inline_keyboard()
    await message.answer("<b>Меню админ-панели</b>\nВыберите действие:", reply_markup=keyboard)



@admin_router.callback_query(F.data == "notification_for_all")
async def notify_all_users_message(callback:CallbackQuery,state:FSMContext):
    """
    Запускает процесс рассылки уведомления всем пользователям
    """
    await state.set_state(NotifificationAllUsers.waiting_for_message)
    await callback.message.answer("Напишите сообщение для рассылки всем пользователям.",callback_data="notification_for_all_message")


@admin_router.message(NotifificationAllUsers.waiting_for_message)
async def process_notify_all_users_message(callback:CallbackQuery, state:FSMContext, bot:Bot):
    """
    Начинает рассылку уведомления всем пользователям
    """

    await callback.message.answer("Рассылка уведомления всем пользователям начата.")
    # Логика рассылки уведомления всем пользователям здесь
    await callback.message.answer("Уведомление всем пользователям отправлено.")
    await state.clear()



@admin_router.callback_query(F.data == "notification_user")
async def notify_user_message(callback:CallbackQuery,state:FSMContext):
    """
    Запускает процесс рассылки уведомления конкретному пользователю
    """
    await callback.message.answer("Пожалуйста, введите ID пользователя для отправки уведомления.", callback_data="notification_user_id")
    await state.set_state(NotificationUser.waiting_for_user_id)

@admin_router.message(NotificationUser.waiting_for_user_id)
async def process_notify_user_message(callback:CallbackQuery, state:FSMContext, bot:Bot):
    """
    Принимает ID пользователя и запрашивает сообщение для отправки
    """
    await state.set_state(NotificationUser.waiting_for_message)
    await callback.message.answer("Пожалуйста, введите сообщение для отправки уведомления пользователю.", callback_data="notification_user_message")
    # Логика отправки уведомления конкретному пользователю здесь

@admin_router.message(NotificationUser.waiting_for_message)
async def process_notify_user_message_final(callback:CallbackQuery, state:FSMContext, bot:Bot):
    """
    Завершает отправку уведомления конкретному пользователю
    """
    # Логика рассылки уведомления конкретному пользователю здесь
    await callback.message.answer("Уведомление пользователю отправлено.")
    await state.clear()
