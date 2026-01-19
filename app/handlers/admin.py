from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram import Router, Bot, F
from aiogram.filters import Command, StateFilter, Filter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
import time

from database import *

from ..config import config
from ..filters import AdminChatFilter
from ..keyboards import AdminPanelInlineButtons
from ..states import *
from ..services import googlesheet_service

admin_router = Router()
admin_router.message.filter(AdminChatFilter())

@admin_router.message(Command("checkadmin"))
async def check_in_admin_chat(message: Message):
    """
    Проверяет, написано сообщение в чате админ-панели или нет
    """

    await message.answer("Да, это чат админ-панели")

@admin_router.message(Command("all_notification"))
async def notify_all_users_message(message: Message, state: FSMContext):
    """
    Запускает процесс рассылки уведомления всем пользователям
    """

    await message.delete()
    await message.answer("Напишите сообщение для рассылки всем пользователям.")
    await state.set_state(NotifificationAllUsers.waiting_for_message)

@admin_router.message(NotifificationAllUsers.waiting_for_message)
async def process_notify_all_users_message(message: Message, state: FSMContext, bot:Bot):
    """
    Начинает рассылку уведомления всем пользователям
    """

    message_for_users = message.text
    await message.delete()
    await message.answer(f"Рассылка уведомления всем пользователям начата.\n\n<b>Уведомление:</b> {message_for_users}")
    db_status, all_ids = await db_get_all_user_tg_ids()
    success_count=0

    try:

        for chat_id in all_ids:
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text = f"✉️ Новое уведомление от бота\n\n<b>{message_for_users}</b>"
                    )
                success_count += 1
            except Exception as e:
                await message.answer(f"Ошибка отправки {chat_id}: Чат не найден")

        await message.answer(
            f"✅ Рассылка завершена! Отправлено {success_count}/{len(all_ids)} уведомлений.\n\nТекст: <b>{message_for_users}</b>",
            show_alert=True
            )
    except Exception as e:
        await message.answer(f"❌ Ошибка рассылки: {e}\n\nТекст: <b>{message_for_users}</b>", show_alert=True)

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

    message_for_user = message.text
    await message.delete()

    data = await state.get_data()
    bot_message_id = data.get('bot_message_id')
    try:
        await message.bot.delete_message(message.chat.id, bot_message_id)
    except:
        pass
    
    user_id = data.get("user_id")

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

@admin_router.message(Command("delete_user"))
async def delete_user_command(message: Message, state: FSMContext):
    """
    Начинает удаление конкретного пользователя
    """

    await message.answer(
        "👤 Введите Telegram ID для удаления пользователя:\n"
        "💡 Пример: `1293014025`",
        parse_mode="Markdown"
    )
    await state.set_state(ModeratorStates.waiting_delete_user_tg_id)

@admin_router.message(ModeratorStates.waiting_delete_user_tg_id)
async def get_user_id_for_delete(message: Message, state: FSMContext):
    """
    Просит причину удаления пользователя
    """
    await state.update_data(user_id = message.text)

    await message.answer(
        "❔ Введите причину удаления пользователя из системы:\n",
        parse_mode="Markdown"
    )
    await state.set_state(ModeratorStates.waiting_delete_user_reason)

@admin_router.message(ModeratorStates.waiting_delete_user_reason)
async def process_delete_user(message: Message, state: FSMContext, bot:Bot):
    """
    Удаляет конкретного пользователя
    """
    reason_for_delete = message.text
    data = await state.get_data()
    user_id = data.get("user_id")
    user_full_name = await db_get_user_full_name(user_id)
    await message.answer("🔄 Проверяю и удаляю...")

    # Инициализация статусов
    db_success = db_result = db_user_id = None
    google_sheets_status = google_sheets_row = "⏳"
    
    try:
        # БД ВСЕГДА работает (приоритетная)
        try:
            db_success, db_result, db_user_id= await db_delete_user_by_tg_id(user_id)
            db_status = "✅" if db_success else "❌"
        except Exception as db_error:
            db_success = False
            db_result = f"Ошибка: {str(db_error)}"
            db_status = "❌"
        
        # Google Sheets (опционально)
        try:
            google_sheets_success = await googlesheet_service.delete_user_by_tg_id_async(int(user_id))
            if google_sheets_success.get("success"):
                google_sheets_status = "✅"
                google_sheets_row = google_sheets_success.get('deleted_row', 'N/A')
            else:
                google_sheets_status = "⚠️"
                google_sheets_row = google_sheets_success.get('message', 'Не найден')
        except Exception as gs_error:
            google_sheets_status = "⚠️"
            google_sheets_row = f"Ошибка GoogleSheets: {str(gs_error)}"
        
        # Финальный отчет
        if db_success:
            await message.answer(
                f"✅ <b>Пользователь {user_full_name} (ID: {user_id}) удалён из системы</b>\n\n"
                f"❔ <b>Причина: {reason_for_delete}</b>\n"
                f"💾 <b>База данных:</b> {db_status} (ID: {db_user_id}) \n"
                f"📊 <b>Google Sheets:</b>  (строка {google_sheets_row})\n\n"
                f"❗️ Если пользователь не удалён из GoogleSheets - сделайте это вручную",
                parse_mode="HTML"
            )
            # Уведомление ПОЛЬЗОВАТЕЛЮ
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=f"❌ Ваш аккаунт был удалён из системы\n\n"
                         f"❔ <b>Причина: {reason_for_delete}</b>\n"
                         f"При наличии вопросов обратитесь в поддержку /help",
                    reply_markup=ReplyKeyboardRemove(),
                    parse_mode="HTML"
                )
            except Exception:
                await message.answer("⚠️ Уведомление пользователю не доставлено")
        else:
            await message.answer(
                f"❌ <b>Ошибка БД</b>\n\n"
                f"💾 <b>База данных:</b> {db_status}\n"
                f"  └─ {db_result}\n"
                f"📊 <b>Google Sheets:</b> {google_sheets_status} (строка {google_sheets_row})\n\n"
                f"⚠️ Пользователь НЕ удалён",
                parse_mode="HTML"
            )
            
    except Exception as e:
        await message.answer(
            f"💥 <b>Критическая ошибка:</b>\n"
            f"<code>{str(e)}</code>\n\n"
            f"БД: {db_status if db_status else 'Неизвестно'}\n"
            f"Google Sheets: {google_sheets_status}",
            parse_mode="HTML"
        )
    
    await state.clear()

@admin_router.message(Command("supermegasecretcommandfordeleteallusers"))
async def delete_all_users(message: Message, state: FSMContext):
    """
    Начинает полную очистку системы от данных пользователей
    """
    await message.delete()
    await message.answer("🗑️ Вы уверены что хотите <b>ПОЛНОСТЬЮ</b> очистить систему?\n\n"
                        "⚠️ <b>Это удалит ВСЕХ пользователей и заявки!</b>",
                        parse_mode="HTML")
    await state.set_state(ModeratorStates.waiting_accept_to_delete_all_users)

@admin_router.message(ModeratorStates.waiting_accept_to_delete_all_users)
async def process_delete_all_users(message: Message, state: FSMContext, bot:Bot):
    """
    Полностью очищает систему от данных пользователей
    """
    if message.text == "Ye$, I w@nt to de1ete":
        await message.delete()
        await message.answer("🔄 Выполняю полную очистку...")
    
        # Инициализация статусов
        db_success = db_result = None
        google_sheets_status = google_sheets_total_deleted = "⏳"
        db_status_ids, all_ids = await db_get_all_user_tg_ids()
        
        try:
            # БД ВСЕГДА работает (приоритетная)
            try:
                db_success, db_result = await db_delete_all_users()
                db_status = "✅" if db_success else "❌"
            except Exception as db_error:
                db_success = False
                db_result = f"Ошибка: {str(db_error)}"
                db_status = "❌"
            
            # Google Sheets (опционально)
            try:
                google_sheets_success = await googlesheet_service.clear_all_user_data_async()
                if google_sheets_success.get("success"):
                    google_sheets_status = "✅"
                    google_sheets_total_deleted = google_sheets_success.get('total_deleted', 'N/A')
                else:
                    google_sheets_status = "⚠️"
                    google_sheets_total_deleted = google_sheets_success.get('error', 'Не удалось')
            except Exception as gs_error:
                google_sheets_status = "⚠️"
                google_sheets_total_deleted = f"Ошибка GS: {str(gs_error)}"
            
            # Финальный отчет
            if db_success:
                await message.answer(
                    f"🎉 <b>Система очищена!</b>\n\n"
                    f"💾 <b>База данных:</b> {db_status}\n"
                    f"📊 <b>Google Sheets:</b> {google_sheets_status}\n"
                    f"  └─ Удалено: {google_sheets_total_deleted}\n\n"
                    f"❗️ Если данные не удалёны из GoogleSheets - сделайте это вручную",
                    parse_mode="HTML"
                )
            else:
                await message.answer(
                    f"❌ <b>Ошибка очистки БД</b>\n\n"
                    f"💾 <b>База данных:</b> {db_status}\n"
                    f"  └─ {db_result}\n"
                    f"📊 <b>Google Sheets:</b> {google_sheets_status}\n"
                    f"  └─ {google_sheets_total_deleted}\n\n"
                    f"⚠️ Очистка не выполнена",
                    parse_mode="HTML"
                )
                
        except Exception as e:
            await message.answer(
                f"💥 <b>Критическая ошибка:</b>\n"
                f"<code>{str(e)}</code>\n\n"
                f"БД: {db_status if db_status else 'Неизвестно'}\n"
                f"Google Sheets: {google_sheets_status}",
                parse_mode="HTML"
            )
        
        for chat_id in all_ids:
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text = "🔄 Система «ТИУмничка» была полностью очищена.\n\nБлагодарим вас за использование нашего сервиса!",
                    reply_markup=ReplyKeyboardRemove())
                
            except Exception as e:
                await message.answer(f"Ошибка отправки {chat_id}: Чат не найден")
        
        await state.clear()

    else:
        await message.answer(f"❌Команда для очистки системы указана неверно!\n\n",
                             f"Очистка отменена! Больше так не балуйся:)", parse_mode="HTML")
        
        await state.clear()

@admin_router.message(Command("deduct_coins"))
async def deduct_tiukoins_from_user(message: Message, state: FSMContext):
    """
    Начало: Списывает определённое количество ТИУкоинов по ТГ_айди пользователя
    """

    await message.delete()
    await message.answer(text="Напишите ID пользователя и количество ТИУкоинов, которые хотите списать через пробел\n\n <i>Пример:1059294358 150</i>")
    
    await state.set_state (ModeratorStates.deduct_tiukoins)

@admin_router.message(ModeratorStates.deduct_tiukoins)
async def process_deduct_tiukoins_from_user(message: Message, state: FSMContext, bot: Bot):
    """
    Конец: Списывает определённое количество ТИУкоинов по ТГ_айди пользователя
    """

    parts = message.text.split(" ")
    user_id = parts[0]
    coins = float(parts[1])
    user_full_name = await db_get_user_full_name(user_id)
    await message.delete
    await message.answer(f"🔄 Списываю ТИУкоины...\n\nПользователь: {user_full_name} (ID: {user_id})")

    db_success = db_result = None
    google_sheets_status = google_sheets_row ="⏳"
    try:
        db_success, db_result = await db_deduct_tiukoins(
            tg_id_str=str(user_id),
            spend_amount=coins,
            name_of_item="Списание ТИУкоинов"
        )
        db_status = "✅" if db_success else "❌"

    except Exception as db_error:
        db_success = False
        db_result = f"Ошибка: {str(db_error)}"
        db_status = "❌"
    
    try:
        google_sheets_success = await googlesheet_service.deduct_tiukoins_async(
            tg_id=user_id,
            amount=coins, 
        )
        if google_sheets_success.get("success"):
            google_sheets_status = "✅"
            google_sheets_row = google_sheets_success.get('user_row', 'N/A')
        else:
            google_sheets_status = "⚠️"
            google_sheets_row = google_sheets_success.get('error', 'Не удалось')
    except Exception as gs_error:
        google_sheets_status = "⚠️"
        google_sheets_row = f"Ошибка GS: {str(gs_error)}"
        
        # Финальный отчет
        if db_success:
            await message.answer(
                f"✅ <b>ТИУкоины списаны!</b>\n\n"
                f"<b>Пользователь:</b> {user_full_name} (ID: {user_id})\n"
                f"💎 <b>Списано:</b> {coins}\n"
                f"💾 <b>База данных:</b> {db_status}\n"
                f"📊 <b>Google Sheets:</b> {google_sheets_status} ({google_sheets_row} строка)\n\n"
                f"❗️ Если ТИУкоины не списались из GoogleSheets - сделайте это вручную. Сообщите об ошибке разработчику.",
                parse_mode="HTML"
            )

            await bot.send_message(
                chat_id=user_id,
                text=f"💎У вас было списано {coins} ТИУкоинов.\n\n❗️Если это произошло по ошибке - обратитесь в /support.")

        else:
            await message.answer(
                f"❌ <b>Ошибка БД</b>\n\n"
                f"<b>Пользователь:</b> {user_full_name} (ID: {user_id})\n"
                f"💾 <b>База данных:</b> {db_status}\n"
                f"  └─ {db_result}\n"
                f"📊 <b>Google Sheets:</b> {google_sheets_status} ({google_sheets_row} строка)\n\n"
                f"❗️ Попробуйте ещё раз, если ошибка повторится - сообщите разработчику.",
                parse_mode="HTML"
            )
            
    except Exception as e:
        await message.answer(
            f"💥 <b>Критическая ошибка:</b>\n"
            f"<code>{str(e)}</code>\n\n"
            f"БД: {db_status if db_status else 'Неизвестно'}\n"
            f"Google Sheets: {google_sheets_status}"
            f"❗️ Попробуйте ещё раз, если ошибка повторится - сообщите разработчику.",
            parse_mode="HTML"
        )
    
    await state.clear()


@admin_router.message(Command("add_coins"))
async def add_tiukoins_to_user(message: Message, state: FSMContext):
    """
    Начало: Добавляет определённое количество ТИУкоинов по ТГ_айди пользователя
    """

    await message.delete()
    await message.answer(text="Напишите ID пользователя и количество ТИУкоинов, которые хотите добавить через пробел.\n\n <i>Пример:1059294358 150</i>")
    
    await state.set_state (ModeratorStates.add_tiukoins)

@admin_router.message(ModeratorStates.add_tiukoins)
async def process_add_tiukoins_to_user(message: Message, state: FSMContext, bot: Bot):
    """
    Конец: Добавляет определённое количество ТИУкоинов по ТГ_айди пользователя
    """

    parts = message.text.split(" ")
    user_id = parts[0]
    coins = float(parts[1])
    user_full_name = await db_get_user_full_name(user_id)
    await message.delete
    await message.answer(f"🔄 Добавляю ТИУкоины...\n\nПользователь: {user_full_name} (ID: {user_id})")

    db_success = db_result = None
    google_sheets_status = google_sheets_row ="⏳"
    try:
        db_success, db_result = await db_add_tiukoins(
            tg_id_str=str(user_id),
            spend_amount=coins,
        )
        db_status = "✅" if db_success else "❌"

    except Exception as db_error:
        db_success = False
        db_result = f"Ошибка: {str(db_error)}"
        db_status = "❌"
    
    try:
        google_sheets_success = await googlesheet_service.add_tiukoins_async(
            tg_id=user_id,
            amount=coins, 
        )
        if google_sheets_success.get("success"):
            google_sheets_status = "✅"
            google_sheets_row = google_sheets_success.get('user_row', 'N/A')
        else:
            google_sheets_status = "⚠️"
            google_sheets_row = google_sheets_success.get('error', 'Не удалось')
    except Exception as gs_error:
        google_sheets_status = "⚠️"
        google_sheets_row = f"Ошибка GS: {str(gs_error)}"
        
        # Финальный отчет
        if db_success:
            await message.answer(
                f"✅ <b>ТИУкоины добавлены!</b>\n\n"
                f"<b>Пользователь:</b> {user_full_name} (ID: {user_id})\n"
                f"💎 <b>Добавлено:</b> {coins}\n"
                f"💾 <b>База данных:</b> {db_status}\n"
                f"📊 <b>Google Sheets:</b> {google_sheets_status} ({google_sheets_row} строка)\n\n"
                f"❗️ Если ТИУкоины не добавлены в GoogleSheets - сделайте это вручную. Сообщите об ошибке разработчику.",
                parse_mode="HTML"
            )

            await bot.send_message(
                chat_id=user_id,
                text=f"💎Вам было добавлено {coins} ТИУкоинов.\n\n❗️Если это произошло по ошибке - обратитесь в /support.")

        else:
            await message.answer(
                f"❌ <b>Ошибка  БД</b>\n\n"
                f"<b>Пользователь:</b> {user_full_name} (ID: {user_id})\n"
                f"💾 <b>База данных:</b> {db_status}\n"
                f"  └─ {db_result}\n"
                f"📊 <b>Google Sheets:</b> {google_sheets_status} ({google_sheets_row} строка)\n\n"
                f"❗️ Попробуйте ещё раз, если ошибка повторится - сообщите разработчику.",
                parse_mode="HTML"
            )
            
    except Exception as e:
        await message.answer(
            f"💥 <b>Критическая ошибка:</b>\n"
            f"<code>{str(e)}</code>\n\n"
            f"БД: {db_status if db_status else 'Неизвестно'}\n"
            f"Google Sheets: {google_sheets_status}"
            f"❗️ Попробуйте ещё раз, если ошибка повторится - сообщите разработчику.",
            parse_mode="HTML"
        )
    
    await state.clear()
