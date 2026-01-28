from aiogram.types import Message, ReplyKeyboardRemove
from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from database import *
from ..filters import AdminChatFilter
from ..states import NotificationUser, NotifificationAllUsers, AdminStates
from ..services import googlesheet_service, bot_logger

admin_router = Router()
admin_router.message.filter(AdminChatFilter())

@admin_router.message(Command("all_notification"))
async def notify_all_users_message(message: Message, state: FSMContext):
    """Запускает процесс рассылки уведомления всем пользователям"""

    await message.delete()
    await message.answer("Напишите сообщение для рассылки всем пользователям.")
    await state.set_state(NotifificationAllUsers.waiting_for_message)

@admin_router.message(NotifificationAllUsers.waiting_for_message)
async def process_notify_all_users_message(message: Message, state: FSMContext, bot:Bot):
    """Начинает рассылку уведомления всем пользователям"""

    message_for_users = message.text
    await message.delete()
    await message.answer(f"🔄 Запускаю рассылку...\n\n<b>Текст уведомления:</b> {message_for_users}")
    db_status, all_ids, db_message = await db_get_all_user_tg_ids()

    if db_status == False:
        await message.answer(f"{db_message}\n\n❗️ Попробуйте ещё раз. При повторной ошибке обратитесь к разработчику")
        await state.clear()
        return

    success_count = 0

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

        bot_logger.log_admin_msg(tg_id = message.from_user.id,
        username = message.from_user.username,
        message = f"МАССОВОЕ УВЕДОМЛЕНИЕ: Успешно\n"
                    f"Отправлено {success_count}/{len(all_ids)} уведомлений.")

    except Exception as e:
        bot_logger.log_admin_msg(tg_id = message.from_user.id,
            username = message.from_user.username,
            message = f"МАССОВОЕ УВЕДОМЛЕНИЕ: Ошибка БД\n"
                         f"Текст: {message_for_users}\n"
                         f"БД: {db_message}\n"
                         f"Ошибка: {e}")

        await message.answer(f"❌ Ошибка рассылки: {e}\n\nТекст: <b>{message_for_users}</b>\n\n ", show_alert=True)

    await state.clear()

@admin_router.message(Command("user_notification"))
async def notify_user(message: Message, state: FSMContext):
    """Запускает процесс рассылки уведомления конкретному пользователю"""

    await message.delete()

    sent_message =  await message.answer("Введите ID пользователя для отправки уведомления.")
    await state.set_state(NotificationUser.waiting_for_user_id)
    await state.update_data(bot_message_id=sent_message.message_id)

@admin_router.message(NotificationUser.waiting_for_user_id)
async def notify_user_message(message: Message, state: FSMContext):
    """Принимает ID пользователя и запрашивает сообщение для отправки"""
    
    await message.delete()

    data = await state.get_data()
    bot_message_id = data.get('bot_message_id')

    try:
        await message.bot.delete_message(message.chat.id, bot_message_id)
    except:
        pass

    sent_message = await message.answer(f"Введите сообщение для отправки пользователю <b>{message.text}</b>")

    await state.update_data(user_id = message.text)
    await state.update_data(bot_message_id=sent_message.message_id)
    await state.set_state(NotificationUser.waiting_for_message)

@admin_router.message(NotificationUser.waiting_for_message)
async def process_notify_user(message: Message, state: FSMContext, bot: Bot):
    """Завершает отправку уведомления конкретному пользователю"""

    message_for_user = message.text
    await message.delete()

    data = await state.get_data()
    bot_message_id = data.get('bot_message_id')
    user_id = data.get("user_id")

    try:
        await message.bot.delete_message(message.chat.id, bot_message_id)
    except:
        pass

    try:
        await bot.send_message(
            chat_id=user_id,
            text = f"✉️ Новое уведомление от бота\n\n<b>{message_for_user}</b>"
        )

        await message.answer(f"✅ Уведомление пользователю {user_id} отправлено!\n\nТекст уведомления: <b>{message_for_user}</b>",
                             show_alert=True)
        
        bot_logger.log_admin_msg(tg_id = message.from_user.id,
                                username = message.from_user.username,
                                message = f"ОДИНОЧНОЕ УВЕДОМЛЕНИЕ: Успешно\n"
                                            f"Пользователь: {user_id}\n"
                                            f"Текст: {message_for_user}")
    except Exception as e:
        bot_logger.log_admin_msg(tg_id = message.from_user.id,
            username = message.from_user.username,
            message = f"ОДИНОЧНОЕ УВЕДОМЛЕНИЕ: Ошибка\n"
                         f"Пользователь: {user_id}\n"
                         f"Текст: {message_for_user}\n"
                         f"Ошибка: {e}")

        await message.answer(f"❌ Не удалось отправить уведомление пользователю {user_id}!\n\nТекст уведомления: <b>{message_for_user}</b>")

    await state.clear()

@admin_router.message(Command("delete_user"))
async def delete_user(message: Message, state: FSMContext):
    """Начинает удаление конкретного пользователя"""

    await message.answer(
        "👤 Введите Telegram ID для удаления пользователя:\n"
        "💡 Пример: `1293014025`",
        parse_mode="Markdown"
    )
    await state.set_state(AdminStates.waiting_delete_user_tg_id)

@admin_router.message(AdminStates.waiting_delete_user_tg_id)
async def get_user_id_for_delete(message: Message, state: FSMContext):
    """Запрашивает причину удаления пользователя"""

    await state.update_data(user_id = message.text)
    
    await message.answer(
        "❔ Введите причину удаления пользователя из системы:\n",
        parse_mode="Markdown"
    )
    await state.set_state(AdminStates.waiting_delete_user_reason)

@admin_router.message(AdminStates.waiting_delete_user_reason)
async def process_delete_user(message: Message, state: FSMContext, bot:Bot):
    """Удаляет конкретного пользователя"""

    reason_for_delete = message.text
    data = await state.get_data()
    user_id = data.get("user_id")

    try:
        user_full_name = await db_get_user_full_name(user_id)
    except Exception as e:
        await message.answer("❌ Неверный ID пользователя\n\n❗️ Попробуйте ещё раз, обратитесь к разработчику.")
        await state.clear()
        return

    await message.answer("🔄 Проверяю и удаляю...")

    # Инициализация статусов БД и Google Sheets
    db_success = db_result = db_user_id = None
    google_sheets_status = google_sheets_row = "⏳"
    
    try:

        # БД (приоритетная)
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
            google_sheets_row = f"Ошибка Google Sheets: {str(gs_error)}"
        
        # Финальный отчет
        if db_success:
            bot_logger.log_admin_msg(tg_id = message.from_user.id,
            username = message.from_user.username,
            message = f"УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЯ: Успешно\n"
                    f"Пользователь: {user_full_name} (ID: {user_id})\n"
                    f"Причина: {reason_for_delete}\n"
                    f"База данных: {db_status} (ID: {db_user_id}) \n"
                    f"Google Sheets: {google_sheets_status} (строка {google_sheets_row})")

            await message.answer(
                f"✅ <b>Пользователь {user_full_name} (ID: {user_id}) удалён из системы</b>\n\n"
                f"❔ <b>Причина:</b> {reason_for_delete}\n"
                f"💾 <b>База данных:</b> {db_status} (ID: {db_user_id})\n"
                f"📊 <b>Google Sheets:</b> {google_sheets_status}\n"
                f"  └─ Строка: {google_sheets_row}\n\n"
                f"❗️ Если пользователь не удалён из Google Sheets - сделайте это вручную",
                parse_mode="HTML"
            )

            # Уведомление пользователю
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=f"❌ Ваш аккаунт был удалён из системы\n\n"
                         f"❔ <b>Причина: {reason_for_delete}</b>\n"
                         f"При наличии вопросов обратитесь в поддержку /support",
                    reply_markup=ReplyKeyboardRemove(),
                    parse_mode="HTML"
                )
            except Exception:
                await message.answer("⚠️ Уведомление пользователю не доставлено")

        else:
            bot_logger.log_admin_msg(tg_id = message.from_user.id,
            username = message.from_user.username,
            message = f"УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЯ: Ошибка БД\n"
                    f"Пользователь: {user_full_name} (ID: {user_id})\n"
                    f"Причина: {reason_for_delete}\n"
                    f"База данных: {db_status}\n"
                    f"  └─ {db_result}\n"
                    f"Google Sheets: {google_sheets_status} ({google_sheets_row})")

            await message.answer(
                f"❌ <b>Ошибка удаления из базы данных</b>\n\n"
                f"💾 <b>База данных:</b> {db_status}\n"
                f"  └─ {db_result}\n"
                f"📊 <b>Google Sheets:</b> {google_sheets_status}\n"
                f"  └─ {google_sheets_row}\n\n"
                f"⚠️ Пользователь {user_id} НЕ удалён\n\n"
                f"❗️ Попробуйте ещё раз. При повторной ошибке обратитесь к разработчику",
                parse_mode="HTML"
            )
            
    except Exception as e:
        bot_logger.log_admin_msg(tg_id = message.from_user.id,
            username = message.from_user.username,
            message = f"УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЯ: Критическая ошибка\n"
                        f"База данных: {db_status if db_status else 'Неизвестно'}\n"
                        f"  └─ {db_result}\n"
                        f"Google Sheets: {google_sheets_status} ({google_sheets_row})\n"
                        f"{str(e)}")

        await message.answer(
            f"💥 <b>Критическая ошибка:</b>\n"
            f"<code>{str(e)}</code>\n\n"
            f"💾 <b>База данных:</b> {db_status}\n"
            f"  └─ {db_result}\n"
            f"📊 <b>Google Sheets:</b> {google_sheets_status}\n"
            f"  └─ {google_sheets_row}\n\n"
            f"❗️ Обратитесь к разработчику",
            parse_mode="HTML"
        )
    
    await state.clear()

@admin_router.message(Command("clear_system"))
async def delete_all_users(message: Message, state: FSMContext):
    """Начинает полную очистку БД и Google Sheets"""

    await message.delete()
    await message.answer("🗑️ Вы уверены что хотите <b>ПОЛНОСТЬЮ</b> очистить систему?(Y/n)\n\n"
                        "⚠️ <b>Это удалит ВСЕХ пользователей и заявки!</b>",
                        parse_mode="HTML")
    await state.set_state(AdminStates.waiting_accept_to_delete_all_users)

@admin_router.message(AdminStates.waiting_accept_to_delete_all_users)
async def process_delete_all_users(message: Message, state: FSMContext, bot:Bot):
    """Полностью очищает БД и Google Sheets"""

    if message.text == "Y":
        await message.delete()
        await message.answer("🔄 Выполняю полную очистку...")
    
        # Инициализация статусов БД и Google Sheets
        db_success = db_result = None
        google_sheets_status = google_sheets_total_deleted = "⏳"
        db_status_ids, all_ids, db_message = await db_get_all_user_tg_ids()
        
        try:

            # БД (приоритетная)
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
                google_sheets_total_deleted = f"Ошибка Google Sheets: {str(gs_error)}"
            
            # Финальный отчет
            if db_success:

                bot_logger.log_admin_msg(tg_id = message.from_user.id,
                                        username = message.from_user.username,
                                        message = f"ОЧИСТКА СИСТЕМЫ: Успешно\n"
                                                    f"База данных: {db_status if db_status else 'Неизвестно'}\n"
                                                    f"Google Sheets: {google_sheets_status} (удалено строк: {google_sheets_total_deleted})")

                await message.answer(
                    f"🎉 <b>Система очищена!</b>\n\n"
                    f"💾 <b>База данных:</b> {db_status}\n"
                    f"📊 <b>Google Sheets:</b> {google_sheets_status}\n"
                    f"  └─ Удалено строк: {google_sheets_total_deleted}\n\n"
                    f"❗️ Если данные не удалёны из Google Sheets - сделайте это вручную, обратитесь к разработчику",
                    parse_mode="HTML"
                )
                    
                for chat_id in all_ids:

                    try:
                        await bot.send_message(
                            chat_id=chat_id,
                            text = "🔄 <b>Система «ТИУмничка» была полностью очищена.</b>\n\n😊 Благодарим вас за использование нашего сервиса!",
                            reply_markup=ReplyKeyboardRemove())
                    except Exception as e:
                        await message.answer(f"Ошибка отправки {chat_id}: Чат не найден\n\n Ошибка: {e}")

            else:
                bot_logger.log_admin_msg(tg_id = message.from_user.id,
                        username = message.from_user.username,
                        message = f"ОЧИСТКА СИСТЕМЫ: Ошибка БД\n"
                                    f"База данных: {db_status if db_status else 'Неизвестно'}\n"
                                    f"  └─ {db_result}\n"
                                    f"Google Sheets: {google_sheets_status} (удалено строк: {google_sheets_total_deleted})")

                await message.answer(
                    f"❌ <b>Ошибка очистки базы данных</b>\n\n"
                    f"💾 <b>База данных:</b> {db_status}\n"
                    f"  └─ {db_result}\n"
                    f"📊 <b>Google Sheets:</b> {google_sheets_status}\n"
                    f"  └─ Удалено строк: {google_sheets_total_deleted}\n\n"
                    f"⚠️ Очистка НЕ выполнена\n\n"
                    f"❗️ Попробуйте ещё раз. При повторной ошибке обратитесь к разработчику",
                    parse_mode="HTML"
                )
                
        except Exception as e:
            bot_logger.log_admin_msg(tg_id = message.from_user.id,
            username = message.from_user.username,
            message = f"ОЧИСТКА СИСТЕМЫ: Критическая ошибка\n"
                        f"База данных: {db_status if db_status else 'Неизвестно'}\n"
                        f"  └─ {db_result}\n"
                        f"Google Sheets: {google_sheets_status} (удалено строк: {google_sheets_total_deleted})\n"
                        f"{str(e)}")

            await message.answer(
                f"💥 <b>Критическая ошибка:</b>\n"
                f"<code>{str(e)}</code>\n\n"
                f"💾 <b>База данных:</b> {db_status}\n"
                f"  └─ {db_result}\n"
                f"📊 <b>Google Sheets:</b> {google_sheets_status}\n"
                f"  └─ Удалено строк: {google_sheets_total_deleted}\n\n"
                f"❗️ Обратитесь к разработчику",
                parse_mode="HTML"
            )
        
        await state.clear()

    else:
        await message.answer(f"❌ Очистка системы отменена!\nБольше так не балуйся 😏", 
                            parse_mode="HTML")
        await state.clear()

@admin_router.message(Command("deduct_coins"))
async def deduct_tiukoins_from_user(message: Message, state: FSMContext):
    """Запрашивает ТГ_айди пользователя для списания ТИУкоинов"""

    await message.delete()
    await message.answer(text="Напишите ID пользователя и количество ТИУкоинов, которые хотите списать через пробел\n\n<i>Например: 1059294358 150</i>")
    
    await state.set_state (AdminStates.deduct_tiukoins)

@admin_router.message(AdminStates.deduct_tiukoins)
async def process_deduct_tiukoins_from_user(message: Message, state: FSMContext, bot: Bot):
    """Списывает определённое количество ТИУкоинов по ТГ_айди пользователя"""

    parts = message.text.split(" ")
    user_id = parts[0]
    coins = float(parts[1])
    user_full_name = await db_get_user_full_name(user_id)
    
    await message.answer(f"🔄 Списываю ТИУкоины...\n\nПользователь: {user_full_name} (ID: {user_id})")

    # Инициализация статусов
    db_success = db_result = None
    google_sheets_status = google_sheets_row ="⏳"

    # БД (приоритетная)
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
    
    # Google Sheets (опционально)
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
        google_sheets_row = f"Ошибка Google Sheets: {str(gs_error)}"
        
    # Финальный отчет
    try:
        if db_success:
            bot_logger.log_admin_msg(tg_id = message.from_user.id,
            username = message.from_user.username,
            message = f"СПИСАНИЕ: Успешно\n"
                    f"Пользователь: {user_full_name} (ID: {user_id})\n"
                    f"Списано: {coins}\n"
                    f"База данных: {db_status}\n"
                    f"Google Sheets: {google_sheets_status} (строка: {google_sheets_row})")

            await message.answer(
                f"✅ <b>ТИУкоины списаны!</b>\n\n"
                f"<b>Пользователь:</b> {user_full_name} (ID: {user_id})\n"
                f"💎 <b>Списано:</b> {coins}\n"
                f"💾 <b>База данных:</b> {db_status}\n"
                f"📊 <b>Google Sheets:</b> {google_sheets_status}\n"
                f"  └─ Строка: {google_sheets_row}\n\n"
                f"❗️ Если ТИУкоины не списались из Google Sheets - сделайте это вручную. Сообщите об ошибке разработчику.",
                parse_mode="HTML"
            )

            # Уведомление пользователю
            await bot.send_message(
                chat_id=user_id,
                text=f"💎 У вас было списано {coins} ТИУкоинов.\n\n❗️Если это произошло по ошибке - обратитесь в /support.")

        else:
            bot_logger.log_admin_msg(tg_id = message.from_user.id,
            username = message.from_user.username,
            message = f"СПИСАНИЕ: Ошибка БД\n"
                    f"Пользователь: {user_full_name} (ID: {user_id})\n"
                    f"База данных: {db_status}\n"
                    f"  └─ {db_result}\n"
                    f"Google Sheets: {google_sheets_status} ({google_sheets_row})")

            await message.answer(
                f"❌ <b>Ошибка базы данных</b>\n\n"
                f"<b>Пользователь:</b> {user_full_name} (ID: {user_id})\n"
                f"💾 <b>База данных:</b> {db_status}\n"
                f"  └─ {db_result}\n"
                f"📊 <b>Google Sheets:</b> {google_sheets_status}\n"
                f"  └─ {google_sheets_row}\n\n"
                f"❗️ Попробуйте ещё раз, если ошибка повторится - сообщите разработчику.",
                parse_mode="HTML"
            )
    except Exception as e:
        bot_logger.log_admin_msg(tg_id = message.from_user.id,
            username = message.from_user.username,
            message = f"СПИСАНИЕ: Критическая ошибка\n"
                    f"Пользователь: {user_full_name} (ID: {user_id})\n"
                    f"База данных: {db_status}\n"
                    f"  └─ {db_result}\n"
                    f"Google Sheets: {google_sheets_status} ({google_sheets_row})"
                    f"{str(e)}")

        await message.answer(
            f"💥 <b>Критическая ошибка:</b>\n"
            f"<code>{str(e)}</code>\n\n"
            f"<b>Пользователь:</b> {user_full_name} (ID: {user_id})\n"
            f"💾 <b>База данных:</b> {db_status}\n"
            f"  └─ {db_result}\n"
            f"📊 <b>Google Sheets:</b> {google_sheets_status}\n"
            f"  └─ {google_sheets_row}\n\n"
            f"❗️ Попробуйте ещё раз, если ошибка повторится - сообщите разработчику.",
            parse_mode="HTML"
        )
    
    await state.clear()


@admin_router.message(Command("add_coins"))
async def add_tiukoins_to_user(message: Message, state: FSMContext):
    """Запрашивает ТГ_айди пользователя для начисления ТИУкоинов"""

    await message.delete()
    await message.answer(text="Напишите ID пользователя и количество ТИУкоинов, которые хотите добавить через пробел.\n\n <i>Например: 1059294358 150</i>")
    
    await state.set_state (AdminStates.add_tiukoins)

@admin_router.message(AdminStates.add_tiukoins)
async def process_add_tiukoins_to_user(message: Message, state: FSMContext, bot: Bot):
    """Начисляет определённое количество ТИУкоинов по ТГ_айди пользователя"""

    parts = message.text.split(" ")
    user_id = parts[0]
    coins = float(parts[1])
    user_full_name = await db_get_user_full_name(user_id)
    await message.delete()
    await message.answer(f"🔄 Начисляю ТИУкоины...\n\nПользователь: {user_full_name} (ID: {user_id})")

    # Инициализация статусов
    db_success = db_result = None
    google_sheets_status = google_sheets_row ="⏳"

    # БД (приоритетная)
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
    
    # Google Sheets (опционально)
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
        google_sheets_row = f"Ошибка Google Sheets: {str(gs_error)}"
        
    try:
        # Финальный отчет
        if db_success:
            bot_logger.log_admin_msg(tg_id = message.from_user.id,
            username = message.from_user.username,
            message = f"НАЧИСЛЕНИЕ: Успешно\n"
                    f"Пользователь: {user_full_name} (ID: {user_id})\n"
                    f"Добавлено: {coins}\n"
                    f"База данных: {db_status}\n"
                    f"Google Sheets: {google_sheets_status} (строка: {google_sheets_row})")

            await message.answer(
                f"✅ <b>ТИУкоины начислены!</b>\n\n"
                f"<b>Пользователь:</b> {user_full_name} (ID: {user_id})\n"
                f"💎 <b>Добавлено:</b> {coins}\n"
                f"💾 <b>База данных:</b> {db_status}\n"
                f"📊 <b>Google Sheets:</b> {google_sheets_status}\n"
                f"  └─ Строка: {google_sheets_row}\n\n"
                f"❗️ Если ТИУкоины не начислились в Google Sheets - сделайте это вручную. Сообщите об ошибке разработчику.",
                parse_mode="HTML"
            )

            # Уведомление пользователю
            await bot.send_message(
                chat_id=user_id,
                text=f"💎 Вам было начислено {coins} ТИУкоинов.\n\n❗️Если это произошло по ошибке - обратитесь в /support.")

        else:

            bot_logger.log_admin_msg(tg_id = message.from_user.id,
            username = message.from_user.username,
            message = f"НАЧИСЛЕНИЕ: Ошибка БД\n"
                    f"Пользователь: {user_full_name} (ID: {user_id})\n"
                    f"База данных: {db_status}\n"
                    f"  └─ {db_result}\n"
                    f"Google Sheets: {google_sheets_status} ({google_sheets_row})")

            await message.answer(
                f"❌ <b>Ошибка базы данных</b>\n\n"
                f"<b>Пользователь:</b> {user_full_name} (ID: {user_id})\n"
                f"💾 <b>База данных:</b> {db_status}\n"
                f"  └─ {db_result}\n"
                f"📊 <b>Google Sheets:</b> {google_sheets_status}\n"
                f"  └─ {google_sheets_row}\n\n"
                f"❗️ Попробуйте ещё раз, если ошибка повторится - сообщите разработчику.",
                parse_mode="HTML"
            )
            
    except Exception as e:
        bot_logger.log_admin_msg(tg_id = message.from_user.id,
            username = message.from_user.username,
            message = f"НАЧИСЛЕНИЕ: Ошибка БД\n"
                    f"Пользователь: {user_full_name} (ID: {user_id})\n"
                    f"База данных: {db_status}\n"
                    f"  └─ {db_result}\n"
                    f"Google Sheets: {google_sheets_status} ({google_sheets_row})"
                    f"{str(e)}") 

        await message.answer(
            f"💥 <b>Критическая ошибка:</b>\n"
            f"<code>{str(e)}</code>\n\n"
            f"💾 <b>База данных:</b> {db_status}\n"
            f"  └─ {db_result}\n"
            f"📊 <b>Google Sheets:</b> {google_sheets_status}\n"
            f"  └─ {google_sheets_row}\n\n"
            f"❗️ Попробуйте ещё раз, если ошибка повторится - сообщите разработчику.",
            parse_mode="HTML"
        )
    
    await state.clear()
