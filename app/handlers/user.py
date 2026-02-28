from aiogram import Router, Bot, F
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InputMediaPhoto
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from datetime import datetime
import pytz
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import *
from ..states import *
from ..keyboards import *
from ..lexicon import *
from ..config import *
from ..services import *

user_router = Router()
keyboard_start = AgreementInlineButtons.get_inline_keyboard()
menu_keyboard = MenuKeyboard.get_keyboard_menu()
support_keyboard = SupportInlineButtons.get_inline_keyboard()
choice_role = ChoiceOfRoleInlineButtons.get_inline_keyboard()
direction_of_activities_keyboard = DirectionOfActivitiesInlineButtons.get_inline_keyboard()
application_confirm_keyboard = ApplicationConfirmationInlineButtons.get_inline_keyboard()
change_of_application_keyboard = ChangeOfApplicationInlineButtons.get_inline_keyboard()
additional_material_keyboard = AddMaterial.get_inline_keyboard()
confirm_material_keyboard = AddMaterialConfirm.get_inline_keyboard()
about_competition_keyboard = AboutTheCompetition.get_inline_keyboard()
my_tiukoins = MyTiukoins.get_inline_keyboard()
recall_the_agreement_keyboard = RecallTheAgreement.get_inline_keyboard()
catalog_of_rewards = catalog_of_rewards

competition_regulations_id = "BQACAgIAAxkBAAJA3GmgMNrgIt4gbm_X1xjELFgow5BkAAJujQAC6f0AAUk0tsjTgfAoxDoE"
agreement_id = "BQACAgIAAxkDAAJAkGmgItYgKOpgOOhKutIsQs40hQQpAAKhjAAC6f0AAUkfEtpNyrxb-joE"
cards_id = ["AgACAgIAAxkBAAJA5GmgMXA7829aLG590XGoBHIi1wbCAAKmF2sb6f0AAUnHCH8wp-GgHgEAAwIAA3kAAzoE",
            "AgACAgIAAxkBAAJA5mmgMYkCyS12_PyT7rukq2jYbAcNAAKpF2sb6f0AAUll9ZBBz-1rsQEAAwIAA3kAAzoE",
            "AgACAgIAAxkBAAJA6GmgMZvQmSLdk3TQ0zL5CYXiYFKjAAKqF2sb6f0AAUmS9AYsgwABgeoBAAMCAAN5AAM6BA",
            "AgACAgIAAxkBAAJA6mmgMiJuy4PEM1Yjnb-7TDz0-qfBAAKwF2sb6f0AAUkDZddOOOCPEwEAAwIAA3kAAzoE",
            "AgACAgIAAxkBAAJA7GmgMif62FiP9HqPoYPMSgo_5pKKAAKyF2sb6f0AAUmHBNP3WgEkSAEAAwIAA3kAAzoE",
            "AgACAgIAAxkBAAJA7mmgMizXlId2HlNisuaHbsbrGqr8AAKzF2sb6f0AAUm5tQJAOZTKqwEAAwIAA3kAAzoE",
            "AgACAgIAAxkBAAJA8GmgMi9Cbgq0y3i2VHkTt5dOhjweAAK1F2sb6f0AAUm9NDo-s14d0gEAAwIAA3kAAzoE",
            "AgACAgIAAxkBAAJA8mmgMjGn5nOLB1XrGlU98R_gjdw-AAK2F2sb6f0AAUmSHFjMrQLWngEAAwIAA3kAAzoE",
            "AgACAgIAAxkBAAJA9GmgMjMdm5LNFP3VHNqbi3HKh2KuAAK3F2sb6f0AAUkY18MdPcAZYgEAAwIAA3kAAzoE"]

ekaterinburg_tz = pytz.timezone('Asia/Yekaterinburg')

@user_router.message(CommandStart(), StateFilter(default_state))
async def start(message: Message, state: FSMContext):
    """Хендлер на /start с проверкой есть ли пользователь в базе данных"""
    
    user_id = str(message.from_user.id)
    user_exists = await db_user_exists(user_id)
    if user_exists == "approved":
        await message.answer(text=LEXICON_TEXT["start_already_registered"],
            reply_markup=menu_keyboard)
    elif user_exists == "pending":
        await message.answer(text=LEXICON_TEXT["wait_registration"])
    else:
        await message.answer(text=LEXICON_TEXT["start_text"])
        await state.set_state(RegistrationFormStates.full_name)

@user_router.callback_query(F.data == "re_register")
async def re_register_start(callback: CallbackQuery,state:FSMContext):
    """Нажатие на кнопку получить ОПД заново"""

    await callback.message.edit_text(LEXICON_TEXT["re_register_text"])
    await state.set_state(RegistrationFormStates.full_name)
    await callback.answer()

@user_router.message(StateFilter(RegistrationFormStates.full_name), lambda message: is_valid_full_name(message.text) == True )
async def full_name_sent(message:Message, state: FSMContext ):
    """Обрабатывает введенное ФИО"""
    
    await state.update_data(full_name = message.text, user_id=message.from_user.id, username = f"@{message.from_user.username}", message_id = message.message_id)
    await message.answer(text = LEXICON_TEXT['start_agreement_text'], reply_markup = keyboard_start)

@user_router.message(StateFilter(RegistrationFormStates.full_name),lambda message: not message.text.startswith('/'))
async def process_full_name_incorrect(message: Message):
    """ФИО некоректное"""
    
    await message.answer(text = LEXICON_TEXT["registration_incorrect_full_name"])

@user_router.callback_query(F.data == "read_the_agreement")
async def send_the_agreement(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """Высылает согласие на обработку персональных данных"""
    
    data = await state.get_data()
    user_id = data.get('user_id', 'Не указано')
    full_name = data.get('full_name')
    username = data.get('username', 'Не указано')
    message_id = data.get('message_id', 'Не указано')
    utc_time = callback.message.date
    ekaterinburg_time = utc_time.astimezone(ekaterinburg_tz)
    await callback.message.edit_reply_markup(reply_markup = None)
    
    db_success, db_user_message, user_id_in_db, db_log_message = await db_set_user(tg_id_str=str(user_id), full_name=full_name, username=username)

    if db_success:
        db_message = f"✅ Успешно (ID: {user_id_in_db})"
    else:
        db_message = db_user_message
        bot_logger.log_user_msg(
            tg_id=callback.from_user.id,
            message=f"❌ РЕГИСТРАЦИЯ: Ошибка БД\n"
                    f"Ошибка: {db_log_message}"
        )
        
    moderator_message = (
        "📋<b> Пользователь скачал согласие на обработку персональных данных</b>\n\n"
        f"👤 <b>Пользователь:</b> {username} (ID: {user_id})\n"
        f"💾 <b>База данных:</b> {db_message}\n"
        f"📅 <b>Время скачивания:</b> {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}"
    )

    await bot.delete_message(message_id=message_id, chat_id=user_id)

    # Отправка модератору
    moderator_confirm_form = RegisterNewUserInlineButtons.get_inline_keyboard(
        user_id = callback.from_user.id 
    )
    
    send_params = {
        "chat_id": config.moderator_chat_id,
        "text": moderator_message,
        "reply_markup": moderator_confirm_form,
        "message_thread_id": TOPIC_REGISTRATION_NEW_USER
    }
    
    try:
        await bot.send_message(**send_params)
        await callback.message.edit_text(text = LEXICON_TEXT["registration_completed"])

        bot_logger.log_user_msg(
            tg_id=callback.from_user.id,
            message=f"РЕГИСТРАЦИЯ: ✅ Согласие на ОПД отправлено модератору"
        )

    except Exception as send_error:
        bot_logger.log_user_msg(
            tg_id=callback.from_user.id,
            message=f"❌ РЕГИСТРАЦИЯ: Ошибка отправки сообщения модератору\n"
                    f"Ошибка: {str(send_error)}"
        )
    
    doc = await callback.message.answer("⏳ Загружаем согласие на обработку персональных данных...")
    await callback.answer()
    
    bot_logger.log_user_msg(
        tg_id=callback.from_user.id,
        message="РЕГИСТРАЦИЯ: ✅ Согласие на ОПД загружено"
        )
    
    await state.clear()
    await callback.message.answer_document(document = agreement_id)
    await doc.delete()
    

@user_router.message(Command(commands='cancel'), StateFilter(default_state))
async def process_cancel_command(message: Message):
    """Хендлер на отмену состояний"""
    
    await message.answer(text = LEXICON_TEXT["cancel_no_fsm"])
    
@user_router.message(Command(commands = 'cancel'), ~StateFilter(default_state))
async def procces_cancel_command_state(message: Message,state: FSMContext):
    """Хендлер на отмену состояний и возврат в главное меню"""
    
    await message.answer(text = LEXICON_TEXT["cancel_fsm"])
    await state.clear()

@user_router.message(Command(commands='help'))
async def help_command(message: Message):
    """Хендлер на команду хелп"""
    
    await message.answer(text = LEXICON_TEXT["help_text"])

@user_router.message(F.text == LEXICON_USER_KEYBOARD['submit_application'],StateFilter(default_state))
async def application_start(message: Message, state: FSMContext):
    """Обработка кнопки подать заявку"""

    user_id = str(message.from_user.id)
    user_exists = await db_user_exists(user_id)
    if user_exists:
        await message.answer(LEXICON_TEXT["application_select_event_topic"], reply_markup = direction_of_activities_keyboard )
        await state.set_state(EventApplicationStates.event_direction)
    else:
        await message.answer(text=LEXICON_TEXT["not_registred"], reply_markup=ReplyKeyboardRemove())

@user_router.callback_query(StateFilter(EventApplicationStates.event_direction))
async def event_direction(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора направления"""
    
    event_direction, thread_id = TOPIC_MAPPING[callback.data]
    await state.update_data(
        thread_id = thread_id,
        event_direction = event_direction
    )
    await callback.message.edit_text(f"✅ Вы выбрали: {event_direction}")
    await callback.message.answer(text = LEXICON_TEXT["application_fill_event_name"])
    await state.set_state(EventApplicationStates.name_event)
    await callback.answer()

@user_router.message(StateFilter(EventApplicationStates.name_event))
async def name_of_event_sent(message: Message, state: FSMContext):
    """Получили название мероприятия, запросили дату мероприятия"""
    
    await state.update_data(name_of_event = message.text)
    await message.answer(LEXICON_TEXT["application_fill_event_date"])
    await state.set_state(EventApplicationStates.date_event)

@user_router.message(StateFilter(EventApplicationStates.date_event))
async def date_of_event_sent(message: Message, state: FSMContext):
    """Получили дату мероприятия, запросили название площадки мероприятия"""
    
    if is_valid_event_date(message.text) == True:
        await state.update_data(date_of_event = message.text)
        await message.answer(LEXICON_TEXT["application_fill_event_location"])
        await state.set_state(EventApplicationStates.event_location)
    else:
        await message.answer(LEXICON_TEXT["application_incorrect_event_date"])

@user_router.message(StateFilter(EventApplicationStates.event_location))
async def event_location_sent(message: Message, state: FSMContext):
    """Получили название площадки мероприятия, запросили роль"""
    
    await state.update_data(event_location = message.text)
    await message.answer(LEXICON_TEXT["application_event_select_role"], reply_markup = choice_role)
    await state.set_state(EventApplicationStates.role_at_the_event)

@user_router.callback_query(StateFilter(EventApplicationStates.role_at_the_event))
async def role_at_the_event_sent(callback: CallbackQuery, state: FSMContext):
    """Получили роль, запросили материал, подтверждающий участие"""
    
    event_role = LEXICON_USER_KEYBOARD.get(callback.data, 'Неизвестная роль')
    await state.update_data(event_role = event_role, supporting_materials=[])
    await callback.message.edit_text(f"✅ Вы выбрали: {event_role}")
    await callback.message.answer(text = LEXICON_TEXT["application_event_material"])
    await state.set_state(EventApplicationStates.supporting_manerial)
    await callback.answer()
    
@user_router.message(StateFilter(EventApplicationStates.supporting_manerial))
async def supporting_material_sent(message:Message,state:FSMContext):
    """Сохраняем отправленный материал"""
    
    data = await state.get_data()
    materials_list = data.get('supporting_materials', [])
    material_info = None
    
    if len(materials_list) >= 3:
        await message.answer(LEXICON_TEXT["application_event_material_incorrect"], reply_markup = confirm_material_keyboard)
        await state.set_state(EventApplicationStates.application_process_end)
        return
    
    if message.text and (message.text.startswith("http://") or message.text.startswith("https://")):
        material_info = {
            "type": "ссылка",
            "content": message.text,
            "timestamp": message.date.isoformat(),
            "description": None
        }
        await message.answer(f"✅ Ссылка сохранена ({len(materials_list) + 1}/3)")
        
    elif message.document:   
        material_info = {
            "type": "документ",
            "file_id": message.document.file_id,
            "file_name": message.document.file_name,
            "file_size": message.document.file_size,
            "mime_type": message.document.mime_type,
            "timestamp": message.date.isoformat(),
            "description": None
        }
        await message.answer(f"✅ Документ сохранен ({len(materials_list) + 1}/3)")
        
    elif message.photo:
        photo = message.photo[-1]
        material_info = {
            "type": "фото",
            "file_id": photo.file_id,
            "width": photo.width,
            "height": photo.height,
            "timestamp": message.date.isoformat(),
            "description": message.caption
        }
        await message.answer(f"✅ Фото сохранено ({len(materials_list) + 1}/3)")
        
    elif message.video:
        material_info = {
            "type": "видео",
            "file_id": message.video.file_id,
            "file_name": message.video.file_name,
            "duration": message.video.duration,
            "file_size": message.video.file_size,
            "timestamp": message.date.isoformat(),
            "description": message.caption
        }
        await message.answer(f"✅ Видео сохранено ({len(materials_list) + 1}/3)")
        
    else:
        await message.answer(
            f"❌ Неподдерживаемый формат. Вы добавили {len(materials_list)} из 3 материалов.\n\n"
            "✅ <b>Поддерживаемые форматы:</b>\n"
            "• Ссылки (http:// или https://)\n"
            "• Документы (Word, PDF)\n"
            "• Фото (JPG, PNG)\n"
            "• Видео (MP4, MOV)\n\n"
        )
        return
    
    if material_info:
        materials_list.append(material_info)
        await state.update_data(supporting_materials = materials_list)
        await show_current_materials(message, materials_list)
    await state.set_state(EventApplicationStates.application_process_end)

@user_router.callback_query(F.data == "finish_application", StateFilter(EventApplicationStates.application_process_end))
async def finish_application_handler(callback: CallbackQuery, state: FSMContext):
    """Завершение заявки и показ итоговой информации"""
    
    data = await state.get_data()
    materials_list = data.get('supporting_materials', [])
    await callback.message.edit_text(text= f"✅ <b>Заявка успешно заполнена!</b>\n\n"
                                     f"🎯 <b>Направление внеучебной деятельности:</b> {data.get('event_direction', 'Не указано')}\n"
                                     f"📌 <b>Название мероприятия:</b> {data.get('name_of_event', 'Не указано')}\n"
                                     f"📅 <b>Дата проведения:</b> {data.get('date_of_event', 'Не указано')}\n"
                                     f"📍 <b>Место проведения:</b> {data.get('event_location', 'Не указано')}\n"
                                     f"👤 <b>Роль в мероприятии:</b> {data.get('event_role', 'Не указано')}\n"
                                     f"\n📎 <b>Подтверждающие материалы:</b> ({len(materials_list)} шт.)\n", reply_markup = application_confirm_keyboard)
    await callback.answer()

@user_router.callback_query(F.data == "add_more_material",StateFilter(EventApplicationStates.application_process_end))
async def add_more_material(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Добавить еще материал'"""
    
    await callback.message.edit_text(
        "📤 Отправьте следующий материал\n\n"
    )
    await state.set_state(EventApplicationStates.supporting_manerial)
    await callback.answer()
    
async def show_current_materials(message: Message, materials_list: list):
    """Показывает текущий список материалов"""
    
    if not materials_list:
        await message.answer("📎 Материалы еще не добавлены")
        return
    
    text = "📎 <b>Текущие материалы:</b>\n\n"
    for i, material in enumerate(materials_list, 1):
        text += f"{i}. <b>{material['type'].upper()}</b>\n"
        if material['type'] == 'ссылка':
            text += f"   🔗 {material['content'][:50]}...\n"
        elif material['type'] == 'документ':
            text += f"   📄 {material['file_name']}\n"
        elif material['type'] == 'фото':
            text += f"   🖼️ Фото ({material['width']}x{material['height']})\n"
        elif material['type'] == 'видео':
            text += f"   🎥 Видео ({material['duration']} сек.)\n"
        text += "\n"
    
    text += f"<i>Всего материалов: {len(materials_list)} из 3</i>"
    await message.answer(text, reply_markup = additional_material_keyboard, parse_mode="HTML")
    
async def show_updated_application(message:Message, state: FSMContext):
    """Показывает обновленную заявку на получение ТИУкоинов"""
    
    data = await state.get_data()
    await message.answer("✅ <b>Заявка успешно обновлена!</b>\nПодтвердите данные или выберите что изменить\n\n"
                         f"🎯 <b>Направление внеучебной деятельности:</b> {data.get('event_direction', 'Не указано')}\n"
                         f"📌 <b>Название мероприятия:</b> {data.get('name_of_event', 'Не указано')}\n"
                         f"📅 <b>Дата проведения:</b> {data.get('date_of_event', 'Не указано')}\n"
                         f"📍 <b>Место проведения:</b> {data.get('event_location', 'Не указано')}\n"
                         f"👤 <b>Роль в мероприятии:</b> {data.get('event_role', 'Не указано')}\n"
                         f"📎 <b>Подтверждающие материалы:</b> Прикреплены ниже 👇\n", reply_markup = application_confirm_keyboard) #!!!!!!!!!!!!!
    await state.set_state(EventApplicationStates.application_process_end)

@user_router.callback_query(StateFilter(EventApplicationStates.application_process_end ))
async def registration_end(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Обрабатывает нажатие на кнопки отправить заявку/изменить заявку"""
    
    try:
        if callback.data == "confirm_application":
            await process_application_confirmation(callback, state, bot)
        elif callback.data == "edit_application":
            await process_application_edit(callback, state)
        else:
            await handle_unknown_callback(callback)
            
    except Exception as e:
        await callback.answer("❌ Произошла ошибка. Попробуйте позже. Если ошибка повторяется - обратитесь в поддержку /support", show_alert = True)

        bot_logger.log_user_msg(
            tg_id=callback.from_user.id,
            message=f"ЗАЯВКА: ❌ Ошибка отправки\n"
                    f"Ошибка: {str(e)}"
        )
        
        await callback.message.edit_text("❌ Произошла ошибка. Попробуйте позже. Если ошибка повторяется - обратитесь в поддержку /support")
        await state.clear()

async def process_application_confirmation(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Обрабатывает отправление заявки"""
    
    data = await state.get_data()
    user_id = callback.from_user.id
    thread_id = data.get("thread_id")
    ekaterinburg_time = callback.message.date.astimezone(ekaterinburg_tz)
    user_full_name = await db_get_user_full_name(str(user_id))
    clean_role = data.get('event_role', 'Не указано')[2:8].replace("/", "_")
    tiukoins = ROLE_LEXICON[clean_role]
    await state.update_data(tiukoins = tiukoins)
    await state.update_data(username = f"@{callback.from_user.username}")
    data["tiukoins"] = tiukoins
    
    await callback.message.edit_reply_markup(reply_markup=None)
    
    try:
        database_result = await save_application_to_database(state, callback)
        
        if not database_result.get("success"):

            bot_logger.log_user_msg(
            tg_id=callback.from_user.id,
            message=f"ЗАЯВКА: ❌ Ошибка БД\n"
                    f"БД: {database_result['log_message']}\n"
                    f"ФИО: {pii_masker.mask_full_name(user_full_name)}\n"
                    f"Направление: {data.get('event_direction', '') or 'Не указано'}\n"
                    f"Мероприятие: {data.get('name_of_event', 'Не указано')}\n"
                    f"Роль: {data.get('event_role', 'Не указано')}\n"
                    f"Материалы: {len(data.get('supporting_materials', []))} шт."
        )
            
            await callback.message.answer("❌ Ошибка отправки заявки. Попробуйте позже. Если ошибка повторяется - обратитесь в поддержку /support")
            await callback.answer()
            await state.clear()
            return 

        event_direction = "ЗАГЛУШКА" #TODO: надо ли сделать лист и строку заявки
        
        send_moderator = await send_to_moderator(
                callback, user_id, database_result, ekaterinburg_time,
                data, clean_role, bot, thread_id,
            )
        
        bot_logger.log_user_msg(
            tg_id=callback.from_user.id,
            message=f"ЗАЯВКА: ✅ Заявка отправлена\n"
                    f"БД: {database_result['message']}\n"
                    f"ФИО: {pii_masker.mask_full_name(user_full_name)}\n"
                    f"Направление: {data.get('event_direction', '') or 'Не указано'}\n"
                    f"Мероприятие: {data.get('name_of_event', 'Не указано')}\n"
                    f"Роль: {data.get('event_role', 'Не указано')}\n"
                    f"Материалы: {len(data.get('supporting_materials', []))} шт."
        )

        if not send_moderator:
            await callback.message.answer("❌ Ваша заявка не отправлена модератору. Попробуйте позже. Если ошибка повторяется - обратитесь в поддержку /support")

            bot_logger.log_user_msg(
            tg_id=callback.from_user.id,
            message=f"ЗАЯВКА: ❌ Ошибка отправки модератору\n"
                    f"БД: {database_result['message']}\n"
                    f"ФИО: {pii_masker.mask_full_name(user_full_name)}\n"
                    f"Направление: {data.get('event_direction', '') or 'Не указано'}\n"
                    f"Мероприятие: {data.get('name_of_event', 'Не указано')}\n"
                    f"Роль: {data.get('event_role', 'Не указано')}\n"
                    f"Материалы: {len(data.get('supporting_materials', []))} шт."
                    f"Ошибка: {str(e)}"
        )
        
    except Exception as e:
        
        await callback.message.answer("❌ Произошла непредвиденная ошибка. Пожалуйста, попробуйте позже. Если ошибка повторяется - обратитесь в поддержку /support")

        bot_logger.log_user_msg(
            tg_id=callback.from_user.id,
            message=f"ЗАЯВКА: ❌ Неожиданная ошибка\n"
                    f"БД: {database_result['message']}\n"
                    f"Ошибка: {str(e)}"
        )
    
    await callback.answer()
    await state.clear()

async def process_application_edit(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает редактирование заявки"""
    
    await callback.message.delete()
    await callback.message.answer(
        LEXICON_TEXT["application_edit"],
        reply_markup = change_of_application_keyboard,
        parse_mode = "HTML"
    )
    await state.set_state(ChangeEventApplicationStates.start)
    await callback.answer()

async def handle_unknown_callback(callback: CallbackQuery):
    """Обрабатывает неизвестный callback"""
    
    await callback.message.answer(
        text = LEXICON_TEXT["application_other_answer"],
        parse_mode = "HTML"
    )
    await callback.answer("❌ Неизвестная команда")

async def save_application_to_database(state: FSMContext,callback:CallbackQuery):
    """
    Сохраняет заявку в БД
    Возвращает словарь с True/False, айди заявки в БД, статус заявки в БД
    """
    
    data = await state.get_data()
    user_id = callback.from_user.id
    db_application_id, db_user_message, db_log_message = await db_submit_event_application(
            tg_id_str = str(user_id),
            event_direction = data.get("event_direction", ""),
            event_name = data.get("name_of_event", ""),
            date_of_event = data.get("date_of_event", ""),
            event_place = data.get("event_location", ""),
            event_role = data.get("event_role", ""),
            username = data.get("username","")
        )
        
    db_status = ""
    if db_application_id: 
        db_status = f"✅ Заявка сохранена (ID: {db_application_id})"
        return {"success": True, "application_id": db_application_id, "message": db_status, "log_message": db_log_message}
    else:
        db_status = f"❌ {db_user_message}"
        return {"success": False, "application_id": db_application_id, "message": db_status, "log_message": db_log_message}

    
async def send_to_moderator(callback: CallbackQuery, user_id: int,
                            database_result, ekaterinburg_time,
                            data: dict,
                            clean_role, bot, thread_id: int):
    """
    Отправляет сообщение с данными в чат модераторов
    Возвращает True/False
    """
    
    moderator_message = (
            "📋 <b>Новая заявка на проверку</b>\n\n"
            f"👤 <b>Пользователь:</b> @{callback.from_user.username or 'без username'} "
            f"(ID: {user_id})\n"
            f"💾 <b>База данных:</b> {database_result['message']}\n"
            f"📅 <b>Время подачи:</b> {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"📝 <b>Данные заявки:</b>\n"
            f"• <b>Направление внеучебной деятельности:</b> {data.get('event_direction', 'Не указано')}\n"
            f"• <b>Название мероприятия:</b> {data.get('name_of_event', 'Не указано')}\n"
            f"• <b>Дата проведения:</b> {data.get('date_of_event', 'Не указано')}\n"
            f"• <b>Место проведения:</b> {data.get('event_location', 'Не указано')}\n"
            f"• <b>Роль в мероприятии:</b> {data.get('event_role', 'Не указано')}\n"
            f"• <b>Подтверждающие материалы:</b> {len(data.get('supporting_materials', []))} шт. 👇"
        )
       
    moderator_proceesing_application_keyboard = ProcessingUserApplicationInlineButtons.get_inline_keyboard(
            application_id = int(3)-1, #TODO: че делать с этим
            user_id = user_id,
            event_role = clean_role,
            db_application_id = database_result["application_id"]
        )

    send_params = {
                "chat_id": config.moderator_chat_id,
                "text": moderator_message,
                "reply_markup": moderator_proceesing_application_keyboard,
                "message_thread_id": thread_id 
            }
    try:
        await bot.send_message(**send_params)
        await callback.message.edit_text(text = LEXICON_TEXT["application_event_end"])
            
        materials_list = data.get('supporting_materials', [])
        if materials_list:
            await bot.send_message(
                    chat_id=config.moderator_chat_id,
                    text=f"📎 <b>Подтверждающие материалы ({len(materials_list)} шт.):</b>",
                    message_thread_id=thread_id,
                    parse_mode="HTML"
                )
                    
            for i, material in enumerate(materials_list, 1):
                try:
                    caption = (
                            f"📎 <b>Материал {i} из {len(materials_list)}</b>\n"
                            f"👤 <b>От:</b> @{callback.from_user.username or user_id}\n"
                        )
                        
                    if material['type'] == 'ссылка':
                        await bot.send_message(
                                chat_id = config.moderator_chat_id,
                                text = f"🔗 <b>Ссылка {i}:</b>\n{material['content']}",
                                message_thread_id = thread_id,
                                parse_mode = "HTML"
                            )
                    elif material['type'] == 'документ':
                        await bot.send_document(
                                chat_id = config.moderator_chat_id,
                                document = material['file_id'],
                                caption = caption,
                                message_thread_id = thread_id,
                                parse_mode = "HTML"
                            )
                    elif material['type'] == 'фото':
                        await bot.send_photo(
                                chat_id = config.moderator_chat_id,
                                photo = material['file_id'],
                                caption = caption,
                                message_thread_id = thread_id,
                                parse_mode = "HTML"
                            )
                    elif material['type'] == 'видео':
                        await bot.send_video(
                                chat_id = config.moderator_chat_id,
                                video = material['file_id'],
                                caption = caption,
                                message_thread_id = thread_id,
                                parse_mode = "HTML"
                            )
                except Exception as e:
                    await bot.send_message(
                            chat_id = config.moderator_chat_id,
                            text = f"❌ Ошибка отправки материала {i}",
                            message_thread_id = thread_id
                            )
        else:
            await bot.send_message(
                    chat_id = config.moderator_chat_id,
                    text = "⚠️ <b>Подтверждающие материалы не приложены</b>",
                    message_thread_id = thread_id,
                    parse_mode = "HTML"
                )
        return True
    
    except Exception:
        return False
    
@user_router.callback_query(StateFilter(ChangeEventApplicationStates.start))
async def start_change_of_application(callback: CallbackQuery, state:FSMContext):
    """Начало изменения заявки на получение ТИУкоинов"""
    
    if callback.data == "edit_direction_of_activities":
        await callback.message.delete()
        await callback.message.answer(LEXICON_TEXT["application_edit_topic"],reply_markup = direction_of_activities_keyboard)
        await state.set_state(ChangeEventApplicationStates.change_event_direction)
        await callback.answer()
        
    elif callback.data == "edit_event_name":
        await callback.message.delete()
        await callback.message.answer(LEXICON_TEXT["application_edit_name"])
        await state.set_state(ChangeEventApplicationStates.change_name_event)
        await callback.answer()
        
    elif callback.data == "edit_event_date":
        await callback.message.delete()
        await callback.message.answer(LEXICON_TEXT["application_edit_date"])
        await state.set_state(ChangeEventApplicationStates.change_date_event)
        await callback.answer()
        
    elif callback.data == "edit_event_location":
        await callback.message.delete()
        await callback.message.answer(LEXICON_TEXT["application_edit_location"])
        await state.set_state(ChangeEventApplicationStates.change_event_location)
        await callback.answer()
        
    elif callback.data == "edit_role":
        await callback.message.delete()
        await callback.message.answer(LEXICON_TEXT["application_edit_role"], reply_markup = choice_role)
        await state.set_state(ChangeEventApplicationStates.change_role_at_the_event)
        await callback.answer()
        
    elif callback.data == "edit_confirmation_material":
        await callback.message.delete()
        await state.update_data(supporting_materials=[])
        await callback.message.answer(LEXICON_TEXT["application_edit_material"])
        await state.set_state(EventApplicationStates.supporting_manerial)
        await callback.answer()
        
    else:
        await callback.message.answer(
            text = LEXICON_TEXT["application_other_answer"]
        )
        await callback.answer()

@user_router.callback_query(StateFilter(ChangeEventApplicationStates.change_event_direction))
async def change_event_direction(callback:CallbackQuery, state:FSMContext):  
    
    event_direction, thread_id = TOPIC_MAPPING[callback.data]
    await state.update_data(
        thread_id = thread_id,
        event_direction = event_direction
    )
    await callback.message.edit_text(f"✅ Вы выбрали: {event_direction}")   
    await callback.answer()  
    await show_updated_application(callback.message, state)

@user_router.message(StateFilter(ChangeEventApplicationStates.change_name_event))
async def change_name_event(message:Message, state:FSMContext): 
    
    await state.update_data(name_of_event = message.text)   
    await show_updated_application(message, state)

@user_router.message(StateFilter(ChangeEventApplicationStates.change_date_event))
async def change_date_event(message:Message, state:FSMContext): 
    
    if is_valid_event_date(message.text) == True:
        await state.update_data(date_of_event = message.text)
        await show_updated_application(message, state)
    else:
        await message.answer(LEXICON_TEXT["application_incorrect_event_date"])

@user_router.message(StateFilter(ChangeEventApplicationStates.change_event_location))
async def change_event_location(message:Message, state:FSMContext):   
    
    await state.update_data(event_location=message.text) 
    await show_updated_application(message, state)

@user_router.callback_query(StateFilter(ChangeEventApplicationStates.change_role_at_the_event))
async def application_edit_role(callback:CallbackQuery, state:FSMContext):
    
    event_role = LEXICON_USER_KEYBOARD.get(callback.data, 'Неизвестная роль')
    await state.update_data(event_role=event_role)
    await callback.message.edit_text(f"✅ Вы выбрали: {event_role}")   
    await callback.answer()
    await show_updated_application(callback.message, state)

@user_router.message(F.text == LEXICON_USER_KEYBOARD['my_tyuiu_coins'],StateFilter(default_state))
async def tyuiu_coins_start(message: Message, state: FSMContext):
    """Обрабатывает нажатие на кнопку Мои ТИУкоины"""
    
    await message.answer(LEXICON_TEXT["my_coins_menu"],reply_markup = my_tiukoins)
    await state.set_state(AboutCompetition.my_tiukoins_start)

@connection
@user_router.callback_query(StateFilter(AboutCompetition.my_tiukoins_start))
async def balance_or_history(callback:CallbackQuery,state:FSMContext):
    """Высылает баланс или историю заявок"""
    
    if callback.data == "my_tyuiu_coins":
        balance, db_user_message ,db_log_message  = await db_get_user_balance(tg_id_str= str(callback.from_user.id))
        await callback.message.edit_text(f"💎 <b>Ваш баланс:</b> {balance} ТИУкоинов")
        await callback.answer()
        await state.clear()
        
    elif callback.data == "application_history":
        await callback.message.delete()
        db_success, db_applications, db_user_message, db_log_message = await db_get_application_history(str(callback.from_user.id))

        if not db_success:
            
            bot_logger.log_user_msg(
            tg_id=callback.from_user.id,
            message=f"ИСТОРИЯ ЗАЯВОК: ❌ Ошибка БД\n"
                    f"Ошибка: {db_log_message}"
                )

            await callback.message.answer(
                "❌ Не удалось загрузить историю заявок. Попробуйте позже. Если ошибка повторяется - обратитесь в поддержку /support",
                reply_markup=menu_keyboard
            )
            await callback.answer()
            await state.clear()
            return
            
        if not db_applications:
            await callback.message.answer(
                "📭 У вас нет заявок за последние 3 месяца.",
                parse_mode="HTML",
                reply_markup=menu_keyboard
            )
            await callback.answer()
            await state.clear()
            return
        
        application_text = "📝 <b>История заявок</b> (за последние 3 месяца):\n"
        
        for i, app in enumerate(db_applications, 1):
            status_emoji = " "
            if "Принята" in app[5]:
                status_emoji = "✅"
            elif "На рассмотрении" in app[5]:
                status_emoji = "⏳"
            elif "Отклонена" in app[5]:
                status_emoji = "❌"
        
            app_text = (
                f"\n📋 <b>Заявка #{i}</b>\n"
                f"🎯 <b>Направление:</b> {app[0]}\n"
                f"📌 <b>Мероприятие:</b> «{app[1]}»\n"
                f"📅 <b>Дата:</b> {app[2]}\n"
                f"👤 <b>Роль:</b> {app[3]}\n"
                f"💎 <b>ТИУкоины:</b> {app[4]}\n"
                f"<b>Статус:</b> {status_emoji} {app[5]}\n"
            )
            application_text += app_text
        parts = split_message(application_text, max_length = 4096)
        
        for i, part in enumerate(parts, 1):
            if i == len(parts): 
                await callback.message.answer(part, parse_mode = "HTML", reply_markup = menu_keyboard)
            else:
                await callback.message.answer(part, parse_mode = "HTML")
        await callback.answer()
        await state.clear()
        
    else:
        await callback.message.answer(text=LEXICON_TEXT["in_state"])
        await callback.answer()

def split_message(text: str, max_length: int = 4096) -> list:
    """
    Разбивает текст на части по max_length символов, не разрывая слова и абзацы
    (для истории заявок).
    """
    
    if len(text) <= max_length:
        return [text]
    parts = []
    
    # Разбиваем по абзацам сначала
    paragraphs = text.split('\n')
    current_part = ""
    for paragraph in paragraphs:
        if len(paragraph) > max_length:
            # Если абзац сам по себе слишком длинный разбиваем его на слова
            words = paragraph.split(' ')
            for word in words:
                if len(current_part) + len(word) + 1 > max_length:
                    parts.append(current_part.strip())
                    current_part = word + " "
                else:
                    current_part += word + " "
        else:
            if len(current_part) + len(paragraph) + 1 > max_length:
                parts.append(current_part.strip())
                current_part = paragraph + "\n"
            else:
                current_part += paragraph + "\n"
    if current_part.strip():
        parts.append(current_part.strip())
    
    return parts

@user_router.message(F.text == LEXICON_USER_KEYBOARD['catalog_of_rewards'],StateFilter(default_state))
async def catalog_start(message: Message, state: FSMContext):
    """Обрабатывает нажатие на кнопку 'Каталог Поощрений'"""

    user_id = str(message.from_user.id)
    user_exists = await db_user_exists(user_id)
    if user_exists:
        catalog = await message.answer("⏳ Загружаем каталог поощрений...")
        async with async_session() as session:
             keyboard_markup = await catalog_of_rewards.create_table_keyboard(session)
            
        await catalog.delete()
        await message.answer(text="🛒 <b>Каталог поощрений </b>\n\nВыберите поощрение:", reply_markup = keyboard_markup)
        await state.set_state(CatalogOfRewardsStates.catalog_of_rewards_start)
    else:
        await message.answer(text=LEXICON_TEXT["not_registred"], reply_markup=ReplyKeyboardRemove())

@user_router.callback_query(F.data == "cancel_catalog", StateFilter(CatalogOfRewardsStates.catalog_of_rewards_start))
async def cancel_catalog(callback: CallbackQuery, state: FSMContext):
    """Кнопка 'Закрыть каталог'"""
    
    await callback.message.edit_text(LEXICON_TEXT["cancel_fsm"])
    await state.clear()
    await callback.answer()

@user_router.callback_query(F.data.startswith("view_item_"), StateFilter(CatalogOfRewardsStates.catalog_of_rewards_start))
async def show_item_details_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Просмотр выбранного поощрения из Каталога поощрений"""
    
    try:
        await callback.answer("⏳ Обрабатываем...", show_alert = False)
    except Exception:
        pass
    
    item_id = int(callback.data.replace("view_item_", ""))
    
    async with async_session() as session:
        # Получаем данные из БД
        catalog = select(Catalog_of_reward).where(Catalog_of_reward.id == item_id)
        result = await session.execute(catalog)
        item = result.scalar_one_or_none()
        
        if item:
            keyboard = SelectingRewardInlineButtons.get_inline_keyboard(item_id)
            
            link_on_photo = item.link_on_photo
            print(link_on_photo)
            
            if "https://disk.yandex.ru"in link_on_photo or "https://drive.google.com" in link_on_photo:
                caption = (f"🎁 <b>{item.name_of_reward}</b>\n\n"
                f"💎 <b>Стоимость:</b> {item.price} ТИУкоинов\n"
                f"📝 <b>Примечание:</b> {item.note}\n\n"
                f"<i>Хотите выбрать это поощрение?</i>")
                await callback.message.delete()
                await bot.send_photo(
                    chat_id=callback.message.chat.id,
                    photo=link_on_photo,
                    caption=caption,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            else:
                await callback.message.edit_text(
                f"🎁 <b>{item.name_of_reward}</b>\n\n"
                f"💎 <b>Стоимость:</b> {item.price} ТИУкоинов\n"
                f"📝 <b>Примечание:</b> {item.note}\n"
                f"<i>Хотите выбрать это поощрение?</i>",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            await state.set_state(CatalogOfRewardsStates.show_item_details_state)
        else:
            await callback.answer("❌ Товар не найден", show_alert=True)
    
    await callback.answer()

@user_router.callback_query(F.data == "close_all",StateFilter(CatalogOfRewardsStates.show_item_details_state))
async def close_all(callback:CallbackQuery, state: FSMContext):
    
    await callback.message.delete()
    await callback.message.answer(LEXICON_TEXT["cancel_fsm"])
    await state.clear()
    await callback.answer()
    
@user_router.callback_query(F.data == "show_catalog", StateFilter(CatalogOfRewardsStates.show_item_details_state))
async def show_catalog(callback: CallbackQuery, state: FSMContext):
    """Возврат к каталогу"""
    
    await callback.message.delete()
    async with async_session() as session:
        keyboard_markup = await catalog_of_rewards.create_table_keyboard(session)
    await callback.message.answer(
        "🛒 <b>Каталог поощрений</b>\n\nВыберите товар:",
        reply_markup = keyboard_markup,
        parse_mode = "HTML"
    )
    await state.set_state(CatalogOfRewardsStates.catalog_of_rewards_start)
    await callback.answer()

@user_router.callback_query(F.data.startswith("select_item_"), StateFilter(CatalogOfRewardsStates.show_item_details_state))
async def select_item(callback: CallbackQuery, state: FSMContext):
    """Подтверждение покупки"""
    
    await callback.message.delete()
    item_id = int(callback.data.replace("select_item_", ""))
    catalog = select(Catalog_of_reward).where(Catalog_of_reward.id == item_id)
    async with async_session() as session:
        result = await session.execute(catalog)
        item = result.scalar_one_or_none()
    
    if item:
        keyboard = ConfirmationRewardInlineButtons.get_inline_keyboard(item_id)
        
        await callback.message.answer(
            f"✅ <b>Подтверждение покупки</b>\n\n"
            f"🎁 <b>Поощрение:</b> {item.name_of_reward}\n"
            f"💎 <b>Стоимость:</b> {item.price} ТИУкоинов\n\n"
            f"<i>Подтверждаете списание {item.price} ТИУкоинов?</i>",
            reply_markup = keyboard,
            parse_mode = "HTML"
        )
        await state.set_state(CatalogOfRewardsStates.show_purchase_confirmation_state)
    await callback.answer()


@user_router.callback_query(F.data.startswith("confirm_purchase_"), StateFilter(CatalogOfRewardsStates.show_purchase_confirmation_state))
async def confirm_purchase(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Обработка подтверждения покупки"""
    
    try:
        await callback.answer("⏳ Обрабатываем...", show_alert=False)
    except Exception:
        pass
    
    await callback.message.edit_reply_markup(reply_markup=None)
    
    user_id = callback.from_user.id
    item_id = int(callback.data.replace("confirm_purchase_", ""))
    purchase_date = datetime.now().strftime("%d.%m.%Y")
    catalog = select(Catalog_of_reward).where(Catalog_of_reward.id == item_id)

    
    async with async_session() as session:
        result = await session.execute(catalog)
        item = result.scalar_one_or_none()
        
    status = "Ожидает выдачи"
    
    if not item:
        await callback.message.answer("❌ Товар не найден")
        await state.clear()
        return
    
    try:
        user_full_name = await db_get_user_full_name(str(user_id))
        issuance_id, db_user_message, i_count, db_log_message = await db_purchase_reward(
            tg_id_str = str(user_id),
            reward_id_str = str(item_id),
            username = str(callback.from_user.username)
        )
        
        if issuance_id == -1:
            bot_logger.log_user_msg(
                tg_id=callback.from_user.id,
                message=f"ПООЩРЕНИЕ: ❌ Ошибка списания ТИУкоинов\n"
                        f"Пользователь: {pii_masker.mask_full_name(user_full_name)} (ID: {user_id})\n"
                        f"Товар: {item.name_of_reward}\n"
                        f"Цена: {item.price} ТИУкоинов\n"
                        f"База данных: {db_log_message}"
            )
            await callback.message.answer(f"❌ <b>Ошибка списания ТИУкоинов</b>\n\n{db_user_message}")
            await state.clear()
            return
        
        confirm_text = (
            f"✅ <b>Заявка на получение поощрения оформлена!</b>\n\n"
            f"<b>Заявка №{issuance_id}</b>\n"
            f"🎁 <b>Поощрение:</b> {item.name_of_reward}\n"
            f"💎 <b>Стоимость:</b> {item.price} ТИУкоинов\n"
            f"📅 <b>Дата оформления:</b> {purchase_date}\n"
            f"📍 <b>Место выдачи:</b> г. Тюмень, ул. Мельникайте, 72, корпус 1, кабинет 103\n"
            f"🕓 <b>Режим работы:</b> Пн–Чт с 9:00 до 18:00, Пт с 9:00 до 16:45\n"
            f"📞<b>Обязательная запись по телефону:</b> 8 (3452) 28-39-76 или электронной почте torlopovaaa@tyuiu.ru\n\n"
            f"<b>❗️ Обратите внимание</b>\nКак только вы получите поощрение - вернуть или обменять его будет невозможно. Если вы хотите отменить выдачу поощрения - обратитесь в поддержку /support или по телефону, указанному выше. ТИУкоины при отмене будут возвращены.")

        moderator_message = (
            "🔔 <b>Новая заявка на получение поощрения</b>\n\n"
            f"<b>Заявка №{issuance_id}</b>\n"
            f"<b>Пользователь:</b> @{callback.from_user.username or 'без username'} (ID: {user_id}) \n"
            f"🎁 <b>Поощрение:</b> {item.name_of_reward}\n"
            f"💾 <b>База данных:</b> {db_log_message}\n"
            f"💎 <b>Стоимость:</b> {item.price} ТИУкоинов\n"
            f"📦 <b>Осталось:</b> {i_count} шт.\n"
            f"📅 <b>Дата оформления:</b> {purchase_date}\n"
            f"📍 <b>Место выдачи:</b> г. Тюмень, ул. Мельникайте, 72, корпус 1, кабинет 103\n"
            f"📋 <b>Статус:</b> {status}\n"
        )
        
        moderator_keyboard = ModeratorCloseRewards.get_inline_keyboard(issuance_id, user_id, item_id, item.price)
        send_params = {
                    "chat_id": config.moderator_chat_id,
                    "text": moderator_message,
                    "reply_markup": moderator_keyboard,
                    "message_thread_id": ISSUANCE_OF_INCENTIVES,
                    "parse_mode":"HTML"
                }
        
            
        asyncio.create_task(bot.send_message(**send_params))

        bot_logger.log_user_msg(
            tg_id=callback.from_user.id,
            message=f"ПООЩРЕНИЕ: ✅ Заявка отправлена\n"
                    f"Заявка №{issuance_id}\n"
                    f"Пользователь: {pii_masker.mask_full_name(user_full_name)} (ID: {user_id})\n"
                    f"Товар: {item.name_of_reward}\n"
                    f"Цена: {item.price} ТИУкоинов\n"
                    f"База данных: {db_log_message}"
        )

        await callback.message.edit_text(text = confirm_text, parse_mode = "HTML")
        await state.clear()
        await callback.answer("✅ Покупка совершена!", show_alert = True)
            
    except Exception as e:
        
        await callback.message.answer(f"❌ Произошла ошибка. Попробуйте позже. Если ошибка повторяется - обратитесь в поддержку /support")

        bot_logger.log_user_msg(
            tg_id=callback.from_user.id,
            message=f"ПООЩРЕНИЕ: ❌ Неожиданная ошибка\n"
                    f"Заявка №{issuance_id}\n"
                    f"Пользователь: {pii_masker.mask_full_name(user_full_name)} (ID: {user_id})\n"
                    f"База данных: {db_log_message}\n"
                    f"Ошибка: {str(e)}"
        )          

@user_router.callback_query(F.data == "error_catalog", StateFilter(CatalogOfRewardsStates.catalog_of_rewards_start))
async def error_catalog(callback: CallbackQuery):
    """Ошибка загрузки каталога"""
    
    await callback.answer("❌ Ошибка загрузки каталога. Попробуйте позже. Если ошибка повторяется - обратитесь в поддержку /support", show_alert=True)

@user_router.callback_query(F.data.startswith("cancel_purchase_"),StateFilter(CatalogOfRewardsStates.show_purchase_confirmation_state))
async def cancel_purchase(callback: CallbackQuery, state: FSMContext):
    """Отмена покупки"""
    
    await callback.answer("❌ Покупка отменена", show_alert = True)
    await show_catalog(callback, state)

@user_router.message(F.text == LEXICON_USER_KEYBOARD['agreement_of_contest'],StateFilter(default_state))
async def competition_regulations_start(message: Message, state: FSMContext):
    """Высылает клавиатуру с выбором 'О конкурсе' или 'Карточки'"""
    
    await message.answer(text = LEXICON_TEXT["about_contest_choice"], reply_markup = about_competition_keyboard)
    await state.set_state(AboutCompetition.about_competition_start)

@user_router.callback_query(StateFilter(AboutCompetition.about_competition_start))
async def about_competition_start(callback: CallbackQuery,state: FSMContext, bot: Bot):
    """Обрабатывает коллбеки с кнопок 'О конкурсе' или 'Карточки'"""
    
    if callback.data == "about_competition":
        try:
            mes = await callback.message.edit_text(text = LEXICON_TEXT["loading_document"], reply_markup = None)
            await callback.message.answer_document(document = competition_regulations_id, reply_markup = menu_keyboard)
            await mes.delete()
            await callback.answer()
            await state.clear()
        except Exception:
            pass
        
    elif callback.data == "see_cards":
        try:
            mes = await callback.message.edit_text(text = LEXICON_TEXT["loading_cards"], reply_markup = None)
            media_group = [
                InputMediaPhoto(media=file_id) 
                for file_id in cards_id]

            await callback.message.answer_media_group(media=media_group)
            await mes.delete()
            await callback.answer()
            await state.clear()
        except Exception:
            pass
        
    else:
        await callback.message.answer(text = LEXICON_TEXT["in_state"])


@user_router.message(Command(commands='support'),StateFilter(default_state))
@user_router.message(F.text == LEXICON_USER_KEYBOARD['support'],StateFilter(default_state))
async def support_start(message:Message, state: FSMContext):
    """Обработчик кнопки поддержки"""
    
    await message.answer(LEXICON_TEXT["support_head"], reply_markup = support_keyboard)
    await state.set_state(SupportStates.support_start)

@user_router.callback_query(StateFilter(SupportStates.support_start))
async def support_process(callback:CallbackQuery,state:FSMContext):
    """Обработчик инлайн-кнопок поддержки"""
    
    if callback.data == "write_moderator_of_the_direct":
        await callback.message.edit_text(
            text = LEXICON_TEXT["support_select_event_topic"], reply_markup = direction_of_activities_keyboard
        )
        await state.set_state(SupportStates.support_choice_direction)
        await callback.answer()
        
    elif callback.data == "feedback":
        await callback.message.delete()
        await callback.message.answer(
            text = LEXICON_TEXT["feedback_text"])
        await state.set_state(SupportStates.support_feedback)
        await callback.answer()
        
    else:
        await callback.message.delete()
        await callback.message.answer(
            text = LEXICON_TEXT["support_text"])
        await state.set_state(SupportStates.support_error)
        await callback.answer()

@user_router.callback_query(StateFilter(SupportStates.support_choice_direction))
async def support_choice_direction(callback:CallbackQuery, state:FSMContext):
    """Выбор направления для поддержки"""
    
    event_direction, thread_id = TOPIC_MAPPING[callback.data]
    await state.update_data(
        thread_id = thread_id
    )
    await callback.message.edit_text(f"✅ Вы выбрали: {event_direction}")
    await callback.answer()
    await callback.message.answer(text = LEXICON_TEXT["support_text"])
    await state.set_state(SupportStates.support_write_moderator)

@user_router.message(StateFilter(SupportStates.support_write_moderator))
async def support_write_moderator(message:Message,state:FSMContext, bot: Bot):
    """Обработчик инлайн-кнопки написать модератору направления"""
    
    user_full_name = await db_get_user_full_name(message.from_user.id)
    data = await state.get_data()
    thread_id = data.get("thread_id")
    utc_time = message.date
    ekaterinburg_time = utc_time.astimezone(ekaterinburg_tz)
    moderator_message = (
        "❗️ <b>Новое сообщение от пользователя:</b> \n\n"
        f"👤 <b>Пользователь:</b> @{message.from_user.username or 'без username'} (ID: {message.from_user.id})\n"   
        f"📅 <b>Время подачи:</b> {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"<b>Сообщение:</b> {message.text}"
    )
    moderator_support_keyboard = ModeratorSupportInlineButtons.get_inline_keyboard(message.from_user.id)
    send_params = {
                "chat_id": config.moderator_chat_id,
                "text": moderator_message,
                "reply_markup": moderator_support_keyboard,
                "message_thread_id": thread_id
            }
    
    await bot.send_message(**send_params)
    await message.answer(text = LEXICON_TEXT["support_end"], reply_markup = menu_keyboard)
    await state.clear()
    
@user_router.message(StateFilter(SupportStates.support_feedback))
async def support_feedback_and_error(message:Message,state:FSMContext, bot: Bot):
    """Обработчки инлайн-кнопок обратная связь"""
    
    utc_time = message.date
    ekaterinburg_time = utc_time.astimezone(ekaterinburg_tz)
    moderator_message = (
        "❗️ <b>Новое сообщение от пользователя:</b> \n\n"
        f"👤 <b>Пользователь:</b> @{message.from_user.username or 'без username'} (ID: {message.from_user.id})\n"
        f"📅 <b>Время подачи:</b> {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"<b>Сообщение:</b> {message.text}"
    )
    moderator_support_keyboard = ModeratorSupportInlineButtons.get_inline_keyboard(message.from_user.id)
    send_params = {
                "chat_id": config.moderator_chat_id,
                "text": moderator_message,
                "reply_markup": moderator_support_keyboard,
                "message_thread_id": USER_FEEDBACK
            }
    await bot.send_message(**send_params)
    await message.answer(text = LEXICON_TEXT["support_end"], reply_markup = menu_keyboard)
    await state.clear()

@user_router.message(StateFilter(SupportStates.support_error))
async def support_feedback_and_error(message:Message,state:FSMContext, bot: Bot):
    """Обработчки инлайн-кнопок сообщить об ошибке"""
    
    user_full_name = await db_get_user_full_name(message.from_user.id)
    utc_time = message.date
    ekaterinburg_time = utc_time.astimezone(ekaterinburg_tz)
    moderator_message = (
        "❗️ <b>Новое сообщение от пользователя:</b> \n\n"
        f"👤 <b>Пользователь:</b> @{message.from_user.username or 'без username'} (ID: {message.from_user.id})\n"   
        f"📅 <b>Время подачи:</b> {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"<b>Сообщение:</b> {message.text}"
    )
    moderator_support_keyboard = ModeratorSupportInlineButtons.get_inline_keyboard(message.from_user.id)
    send_params = {
                "chat_id": config.moderator_chat_id,
                "text": moderator_message,
                "reply_markup": moderator_support_keyboard,
                "message_thread_id": TOPIC_SUPPORT
            }

    await bot.send_message(**send_params)
    await message.answer(text = LEXICON_TEXT["support_end"], reply_markup = menu_keyboard)
    await state.clear()

@user_router.message(Command(commands = "getmytgid"),StateFilter(default_state))
async def getmytgid(message: Message):
    
    await message.answer(f"🆔 Ваш телеграмм айди: <b>{message.from_user.id}</b>")

@user_router.message(Command(commands = "superpupermegalegasecretpupacommandforsuperpupermegalegasecretpupausers"))
async def sticker(message:Message, bot: Bot):
    
    await message.delete()
    await bot.send_sticker(chat_id = message.from_user.id,sticker='CAACAgIAAxkBAAECCW9pcf5whyOfSwac8j-BoA-FJC9ibAACCFwAAivjEUgq_1ezGy98fzgE')

@user_router.message(Command(commands = "recall_the_agreement"), StateFilter(default_state))
async def recall_the_agreement(message: Message, state: FSMContext):
    """Обрабатывает нажатие на команду отозвать согласие"""
    
    await message.answer(LEXICON_TEXT["recall_the_agreement"], reply_markup = recall_the_agreement_keyboard)
    await state.set_state(RecallAgreement.wait_answer)

@user_router.callback_query(StateFilter(RecallAgreement.wait_answer))
async def wait_answer(callback:CallbackQuery, state: FSMContext, bot:Bot):
    
    if callback.data == "not_recall_agreement":
        await callback.message.edit_text(LEXICON_TEXT["cancel_fsm"])
        await state.clear()
        await callback.answer()
    elif callback.data == "recall_agreement":
        await callback.message.edit_text(LEXICON_TEXT["recall"])
        result = await process_recall_user(callback,bot)
        if result:
            await state.clear()
        else:
            await state.clear()
        await callback.answer()
    else:
        await callback.message.answer(LEXICON_TEXT["in_state"])
        await callback.answer()

async def process_recall_user(callback:CallbackQuery, bot: Bot):
    """Удаляет пользователя из БД"""
    
    user_id = callback.from_user.id
    user_full_name = await db_get_user_full_name(user_id)
    # Инициализация статусов БД
    db_success = db_result = db_user_id = None
    
    try:
        # БД (приоритетная)
        try:
            db_success, db_result, db_user_id, db_log_message= await db_delete_user_by_tg_id(user_id)
            db_status = "✅" if db_success else "❌"
        except Exception as db_error:
            db_success = False
            db_status = "❌"
        
        # Финальный отчет
        if db_success:
            bot_logger.log_user_msg(
            tg_id=callback.message.from_user.id,
            message=f"ОТЗЫВ СОГЛАСИЯ И УДАЛЕНИЕ: ✅ Удалён\n"
                    f"Пользователь: {pii_masker.mask_full_name(user_full_name)} (ID: {user_id})\n"
                    f"База данных: {db_status} (ID: {db_user_id})\n"
        )
            
            moderator_message = (f"✅ <b>Пользователь {user_id} отозвал согласие и был удалён из системы</b>\n\n"
                                f"💾 <b>База данных:</b> {db_status} (ID: {db_user_id})")
            send_params = {
                "chat_id": config.moderator_chat_id,
                "text": moderator_message,
                "message_thread_id": TOPIC_REGISTRATION_NEW_USER
            }
            
            await bot.send_message(**send_params)
    
            await callback.message.delete()
            await callback.message.answer(
                text = f"❌ <b>Ваш аккаунт был удалён из системы! Согласие отозвано</b>\n\nДля повторной регистрации воспользуйтесь командой /start.",
                reply_markup=ReplyKeyboardRemove(),
                parse_mode="HTML")

        else:
            bot_logger.log_user_msg(
                tg_id=callback.message.from_user.id,
                message=f"ОТЗЫВ СОГЛАСИЯ И УДАЛЕНИЕ: ❌ Ошибка БД\n"
                        f"Пользователь: {pii_masker.mask_full_name(user_full_name)} (ID: {user_id})\n"
                        f"База данных: {db_status}\n"
                        f"  └─ {db_log_message}\n"
            )

            await callback.message.answer(
                f"💥 <b>Произошла ошибка!</b>\n"
                f"❗️ Попробуйте ещё раз, если ошибка повторяется - обратитесь в поддержку /support.",
                parse_mode="HTML"
            )
            
    except Exception as e:
        bot_logger.log_user_msg(
            tg_id=callback.message.from_user.id,
            message=f"ОТЗЫВ СОГЛАСИЯ И УДАЛЕНИЕ: 🚨 КРИТИЧЕСКАЯ ОШИБКА\n"
                    f"Пользователь: {pii_masker.mask_full_name(user_full_name)} (ID: {user_id})\n"            
                    f"База данных: {db_status or 'Неизвестно'}\n"
                    f"  └─ {db_log_message}\n"
                    f"Ошибка: {str(e)}"
        )

        await callback.message.answer(
            f"💥 <b>Произошла ошибка!</b>\n"
            f"❗️ Попробуйте ещё раз, если ошибка повторяется - обратитесь в поддержку /support.",
            parse_mode="HTML"
        )

