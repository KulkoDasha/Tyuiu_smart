from aiogram import Router, Bot, F
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.types import Message, Update, CallbackQuery,FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from datetime import datetime
import pytz

from ..states import *
from ..keyboards import *
from ..lexicon import *
from ..config import *
from ..services import *

user_router = Router()
keyboard_start = AgreementInlineButtons.get_inline_keyboard()
menu_keyboard = MenuKeyboard.get_keyboard_menu()
institute_keyboard = ChoiceOfInstituteInlineButtons.get_inline_keyboard()
change_registration_form = ChangeRegistrationFormInlineButtons.get_inline_keyboard()
confirm_registration_form = ConfirmRegistrationFormInlineButtons.get_inline_keyboard()
support_keyboard = SupportInlineButtons.get_inline_keyboard()
choice_role = ChoiceOfRoleInlineButtons.get_inline_keyboard()
direction_of_activities_keyboard = DirectionOfActivitiesInlineButtons.get_inline_keyboard()
application_confirm_keyboard = ApplicationConfirmationInlineButtons.get_inline_keyboard()
change_of_application_keyboard = ChangeOfApplicationInlineButtons.get_inline_keyboard()


competition_regulations_path = "app/files/Polozhenie_o_Konkurse_nematerialnoy_motivatsii_obuchayuschikhsya_TIUmnichka.docx"

ekaterinburg_tz = pytz.timezone('Asia/Yekaterinburg')

@user_router.message(CommandStart(),StateFilter(default_state))
async def start(message: Message):
    """
    Хендлер на команду старт
    """
    await message.answer(text=LEXICON_TEXT["start_text"], reply_markup = keyboard_start)

@user_router.callback_query(F.data == "read_the_agreement")
async def send_the_agreement(callback: CallbackQuery):
    """
    Хендлер на обработку согласия
    """
    await callback.message.answer("Вставить согласие")
    await callback.answer()

@user_router.callback_query(F.data == "give_agreement")
async def give_agreement(callback:CallbackQuery, state: FSMContext):
    """
    Хендлер на принятие согласия
    """
    await callback.message.edit_text(text=LEXICON_TEXT["give_agreement"])
    await callback.message.answer(text=LEXICON_TEXT["registration_fill_full_name"])
    await state.set_state(RegistrationFormStates.full_name)
    await callback.answer()

@user_router.callback_query(F.data == "refuse_agreement")
async def refuse_agreement(callback:CallbackQuery, state: FSMContext):
    """
    Хендлер на отказ от согласия
    """
    await callback.message.answer(text=LEXICON_TEXT["refuse_agreement"])
    await callback.answer()
    
@user_router.message(Command(commands='cancel'), StateFilter(default_state))
async def process_cancel_command(message: Message):
    """
    Хендлер на отмену состояний
    """
    await message.answer(text=LEXICON_TEXT["cancel_no_fsm"])
    
@user_router.message(Command(commands = 'cancel'), ~StateFilter(default_state))
async def procces_cancel_command_state(message: Message,state: FSMContext):
    """
    Хендлер на отмену состояний и возврат в главное меню
    """
    await message.answer(text = LEXICON_TEXT["cancel_fsm"])
    await state.clear()

@user_router.message(Command(commands='help'))
async def help_command(message: Message):
    """
    Хендлер на команду хелп
    """
    await message.answer(text = LEXICON_TEXT["help_text"])

@user_router.callback_query(F.data == "re_register")
async def re_register_start(callback: CallbackQuery,state:FSMContext):
    """
    Нажатие на кнопку пройти регистрацию заново
    """
    await callback.message.edit_text(LEXICON_TEXT["re_register_text"])
    await state.set_state(RegistrationFormStates.full_name)

@user_router.message(StateFilter(RegistrationFormStates.full_name), lambda message: is_valid_full_name(message.text) == True )
async def full_name_sent(message:Message, state: FSMContext ):
    """
    Хендлер фио ввели, запрашивается институт
    """
    await state.update_data(full_name=message.text, user_id=message.from_user.id)
    await message.answer(text = LEXICON_TEXT["registration_select_institute"], reply_markup = institute_keyboard)
    await state.set_state(RegistrationFormStates.institute)

@user_router.message(StateFilter(RegistrationFormStates.full_name))
async def process_full_name_incorrect(message: Message):
    """если фио некоректное"""
    await message.answer(text=LEXICON_TEXT["registration_incorrect_full_name"])

@user_router.callback_query(StateFilter(RegistrationFormStates.institute))
async def institute_select(callback: CallbackQuery,state: FSMContext):
    """
    Выбрали институт, запрашиваем направление
    """
    institute_key = callback.data
    institute_name = LEXICON_USER_KEYBOARD.get(institute_key, 'Неизвестный институт')
    await callback.message.edit_text(f"✅ Вы выбрали: {institute_name}")
    
    await state.update_data(institute=institute_name)
    await callback.message.answer(text = LEXICON_TEXT["registration_fill_direction"])  
    await state.set_state(RegistrationFormStates.direction)

@user_router.message(StateFilter(RegistrationFormStates.direction), lambda message: is_valid_direction(message.text) == True)
async def direction_sent(message:Message, state:FSMContext):
    """
    Ввели направление, запрашиваем курс
    """
    await state.update_data(direction = message.text)
    await message.answer(text = LEXICON_TEXT["registration_fill_course"])  
    await state.set_state(RegistrationFormStates.course)

@user_router.message(StateFilter(RegistrationFormStates.direction))
async def process_from_of_education_incorrect(message:Message):
    """если направление неккоректно"""
    await message.answer(text=LEXICON_TEXT["registration_incorrect_direction"])

@user_router.message(StateFilter(RegistrationFormStates.course),lambda message: is_valid_course(message.text) == True)
async def course_sent(message: Message, state: FSMContext):
    """
    Ввели курс, запрашиваем группу
    """
    await state.update_data(course = message.text)
    await message.answer(text = LEXICON_TEXT["registration_fill_group"]) 
    await state.set_state(RegistrationFormStates.group) 

@user_router.message(StateFilter(RegistrationFormStates.course))
async def process_course_incorrect(message:Message):
    """если курс некорректен"""
    await message.answer(text = LEXICON_TEXT["registration_incorrect_course"])

@user_router.message(StateFilter(RegistrationFormStates.group),lambda message: is_valid_group(message.text) == True)
async def groupe_sent(message: Message, state: FSMContext):
    """
    Ввели группу, запрашиваем год поступления
    """
    await state.update_data(group = message.text)
    await message.answer(text = LEXICON_TEXT["registration_fill_start_year"])  
    await state.set_state(RegistrationFormStates.start_year)

@user_router.message(StateFilter(RegistrationFormStates.group))
async def process_course_incorrect(message:Message):
    """если группа некорректна"""
    await message.answer(text = LEXICON_TEXT["registration_incorrect_group"])

@user_router.message(StateFilter(RegistrationFormStates.start_year), lambda message: message.text.isdigit() 
                     and len(message.text) == 4
                     and 1900 <= int(message.text) <= 2200) 
async def start_year_sent(message: Message, state: FSMContext):
    """
    Ввели год поступления, запрашиваем год окончания
    """
    await state.update_data(start_year = message.text)
    await message.answer(text = LEXICON_TEXT["registration_fill_end_year"])  
    await state.set_state(RegistrationFormStates.end_year)

@user_router.message(StateFilter(RegistrationFormStates.start_year))
async def process_start_year_incorrect(message:Message):
    """если дата начала неккоректна"""
    await message.answer(text = LEXICON_TEXT["registration_incorrect_start_year"])

@user_router.message(StateFilter(RegistrationFormStates.end_year))
async def end_year_sent(message: Message, state: FSMContext):
    """
    Ввели дату конца, запрашиваем номер телефона
    """
    data = await state.get_data()
    start_year = data.get("start_year")
    if is_valid_study_years(start_year, message.text):
        await state.update_data(end_year = message.text)
        await message.answer(text = LEXICON_TEXT["registration_fill_phone_number"]) 
        await state.set_state(RegistrationFormStates.phone_number)
    else:
        await message.answer(LEXICON_TEXT["registration_incorrect_end_year"])

@user_router.message(StateFilter(RegistrationFormStates.phone_number),lambda message: is_valid_phone_number(message.text) == True)
async def phone_sent(message: Message, state: FSMContext):  
    """
    Ввели номер телефон, запрашиваем почту
    """
    await state.update_data(phone = message.text)
    await message.answer(text = LEXICON_TEXT["registration_fill_email"])  
    await state.set_state(RegistrationFormStates.email)

@user_router.message(StateFilter(RegistrationFormStates.phone_number))
async def process_phone_incorrect(message:Message): 
    """если номер телефона неккоректен""" 
    await message.answer(text = LEXICON_TEXT["registration_incorrect_phone_number"])

@user_router.message(StateFilter(RegistrationFormStates.email),lambda message: is_valid_email(message.text) == True)
async def email_sent(message: Message, state: FSMContext):  
    """
    Если почта корректна, выводим итоговое сообщение
    """
    await state.update_data(email = message.text)
    data = await state.get_data()
    await message.answer("✅ Анкета успешно заполнена!\nПодтвердите данные или выберите что изменить\n\n"
                         f"ФИО: {data.get('full_name', 'Не указано')}\n"
                         f"Структурное подразделение обучения: {data.get('institute', 'Не указано')}\n"
                         f"Направление: {data.get('direction', 'Не указано')}\n"
                         f"Курс: {data.get('course', 'Не указано')}\n"
                         f"Группа: {data.get('group', 'Не указано')}\n"
                         f"Год начала обучения: {data.get('start_year', 'Не указано')}\n"
                         f"Год окончания программы обучения: {data.get('end_year', 'Не указано')}\n"
                         f"Номер телефона: {data.get('phone', 'Не указано')}\n"
                         f"Email: {message.text}\n",reply_markup= confirm_registration_form)
    await state.set_state(RegistrationFormStates.registration_end)

@user_router.message(StateFilter(RegistrationFormStates.email))
async def process_phone_incorrect(message:Message):  
    """если почта неккоректна"""
    await message.answer(text = LEXICON_TEXT["registration_incorrect_email"])

@user_router.callback_query(StateFilter(RegistrationFormStates.registration_end))
async def registration_end(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Обрабатываем нажатие на кнопки отправить анкету/изменить анкету
    """
    if callback.data == ("save_registration_form"):
        data = await state.get_data()
        utc_time = callback.message.date
        ekaterinburg_time = utc_time.astimezone(ekaterinburg_tz)
        moderator_message = (
            "📋 Новая анкета на проверку\n\n"
            f"👤 Пользователь: @{callback.from_user.username or 'без username'} "
            f"(ID: {callback.from_user.id})\n"
            f"📅 Время подачи: {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"📝 Данные анкеты:\n"
            f"• ФИО: {data.get('full_name', 'Не указано')}\n"
            f"• Структурное подразделение обучения: {data.get('institute', 'Не указано')}\n"
            f"• Направление: {data.get('direction', 'Не указано')}\n"
            f"• Курс: {data.get('course', 'Не указано')}\n"
            f"• Группа: {data.get('group', 'Не указано')}\n"
            f"• Год начала обучения: {data.get('start_year', 'Не указано')}\n"
            f"• Год окончания программы обучения: {data.get('end_year', 'Не указано')}\n"
            f"• Номер телефона: {data.get('phone_number', 'Не указано')}\n"
            f"• Email: {data.get('email', 'Не указано')}\n"
        )
        moderator_confirm_form = RegisterNewUserInlineButtons.get_inline_keyboard(
            user_id=callback.from_user.id 
        )
        send_params = {
                "chat_id": config.moderator_chat_id,
                "text": moderator_message,
                "reply_markup": moderator_confirm_form,
                "message_thread_id": TOPIC_REGISTRATION_NEW_USER
            }
        await bot.send_message(**send_params)
        await callback.message.edit_text(text = LEXICON_TEXT["registration_end"])
        await state.clear()
    elif callback.data == "change_registration_form":
        await callback.message.edit_text(text = LEXICON_TEXT["registration_edit"], reply_markup = change_registration_form)
        await state.set_state(EditRegistrationForm.start)
    else:
        await callback.message.answer(
            text = "ДОБАВИТЬ ТЕКСТ"
        )

@user_router.callback_query(StateFilter(EditRegistrationForm.start))
async def choice_edit(callback:CallbackQuery, state: FSMContext):
    """
    Обрабатываем нажатие на кнопки изменить данные
    """
    if callback.data == "full_name":
        await callback.message.edit_text(text=LEXICON_TEXT["registration_edit_full_name"])
        await state.set_state(EditRegistrationForm.edit_full_name)
    elif callback.data == "institute":
        await callback.message.edit_text(text=LEXICON_TEXT["registration_edit_institute"],reply_markup = institute_keyboard)
        await state.set_state(EditRegistrationForm.edit_institute)
    elif callback.data == "direction":
        await callback.message.edit_text(text=LEXICON_TEXT["registration_edit_direction"])
        await state.set_state(EditRegistrationForm.edit_direction)
    elif callback.data == "course":
        await callback.message.edit_text(text=LEXICON_TEXT["registration_edit_course"])
        await state.set_state(EditRegistrationForm.edit_course)
    elif callback.data == "group":
        await callback.message.edit_text(text=LEXICON_TEXT["registration_edit_group"])
        await state.set_state(EditRegistrationForm.edit_group)
    elif callback.data == "start_year":
        await callback.message.edit_text(text=LEXICON_TEXT["registration_edit_start_year"])
        await state.set_state(EditRegistrationForm.edit_start_year)
    elif callback.data == "end_year":
        await callback.message.edit_text(text=LEXICON_TEXT["registration_edit_end_year"])
        await state.set_state(EditRegistrationForm.edit_end_year)
    elif callback.data == "phone_number":
        await callback.message.edit_text(text=LEXICON_TEXT["registration_edit_phone_number"])
        await state.set_state(EditRegistrationForm.edit_phone_number)
    else:
        await callback.message.edit_text(text=LEXICON_TEXT["registration_edit_email"])
        await state.set_state(EditRegistrationForm.edit_email)

async def show_updated_form(message: Message, state: FSMContext):
    """Показываем обновленную анкету"""
    data = await state.get_data()
    await message.answer("✅ Анкета успешно обновлена!\nПодтвердите данные или выберите что вы хотите изменить\n\n"
                         f"ФИО: {data.get('full_name', 'Не указано')}\n"
                         f"Структурное подразделение обучения: {data.get('institute', 'Не указано')}\n"
                         f"Направление: {data.get('direction', 'Не указано')}\n"
                         f"Курс: {data.get('course', 'Не указано')}\n"
                         f"Группа: {data.get('group', 'Не указано')}\n"
                         f"Год начала обучения: {data.get('start_year', 'Не указано')}\n"
                         f"Год окончания программы обучения: {data.get('end_year', 'Не указано')}\n"
                         f"Номер телефона: {data.get('phone', 'Не указано')}\n"
                         f"Email: {data.get('email', 'Не указано')}\n", reply_markup=confirm_registration_form)
    await state.set_state(RegistrationFormStates.registration_end)

@user_router.message(StateFilter(EditRegistrationForm.edit_full_name), lambda message: is_valid_full_name(message.text) == True)
async def edit_full_name(message:Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await show_updated_form(message, state)

@user_router.message(StateFilter(EditRegistrationForm.edit_full_name))
async def edit_full_name_incorrect(message:Message):
    await message.answer(text=LEXICON_TEXT["registration_incorrect_full_name"])

@user_router.callback_query(StateFilter(EditRegistrationForm.edit_institute))
async def edit_institute(callback: CallbackQuery, state: FSMContext):
    institute_key = callback.data
    institute_name = LEXICON_USER_KEYBOARD.get(institute_key, 'Неизвестый институт')
    await callback.message.edit_text(f"✅ Вы выбрали: {institute_name}")   
    await state.update_data(institute=institute_name)
    await show_updated_form(callback.message, state)

@user_router.message(StateFilter(EditRegistrationForm.edit_direction), lambda message: is_valid_direction(message.text) == True)
async def edit_direction(message:Message, state: FSMContext):
    await state.update_data(direction=message.text)
    await show_updated_form(message, state)

@user_router.message(StateFilter(EditRegistrationForm.edit_direction))
async def edit_direction_incorrect(message:Message):
    await message.answer(text=LEXICON_TEXT["registration_incorrect_direction"])

@user_router.message(StateFilter(EditRegistrationForm.edit_course),lambda message: is_valid_course(message.text) == True)
async def edit_course(message:Message, state: FSMContext):
    await state.update_data(course=message.text)
    await show_updated_form(message, state)

@user_router.message(StateFilter(EditRegistrationForm.edit_course))
async def edit_course_incorrect(message:Message):
    await message.answer(text = LEXICON_TEXT["registration_incorrect_course"])
    
@user_router.message(StateFilter(EditRegistrationForm.edit_group),lambda message: is_valid_group(message.text) == True)
async def edit_groupe(message:Message, state: FSMContext):
    await state.update_data(groupe=message.text)
    await show_updated_form(message, state)

@user_router.message(StateFilter(EditRegistrationForm.edit_group))
async def edit_groupe_incorrect(message:Message):
    await message.answer(text = LEXICON_TEXT["registration_incorrect_group"])

@user_router.message(StateFilter(EditRegistrationForm.edit_start_year), lambda message: message.text.isdigit() 
                     and len(message.text) == 4
                     and 1900 <= int(message.text) <= 2200)
async def edit_start_year(message:Message, state: FSMContext):
    await state.update_data(start_year=message.text)
    await show_updated_form(message, state)

@user_router.message(StateFilter(EditRegistrationForm.edit_start_year))
async def edit_start_year_incorrext(message:Message):
    await message.answer(text = LEXICON_TEXT["registration_incorrect_start_year"])

@user_router.message(StateFilter(EditRegistrationForm.edit_end_year))
async def edit_end_year(message:Message, state: FSMContext):
    data = await state.get_data()
    start_year = data.get("start_year")
    if is_valid_study_years(start_year, message.text):
        await state.update_data(end_year = message.text)
        await message.answer(text = LEXICON_TEXT["registration_fill_phone_number"]) 
        await state.set_state(RegistrationFormStates.phone_number)
    else:
        await message.answer(LEXICON_TEXT["registration_incorrect_end_year"])
    await state.update_data(end_year=message.text)
    await show_updated_form(message, state)

@user_router.message(StateFilter(EditRegistrationForm.edit_phone_number),lambda message: is_valid_phone_number(message.text) == True)
async def edit_phone_number(message:Message, state: FSMContext):
    await state.update_data(phone_number=message.text)
    await show_updated_form(message, state)

@user_router.message(StateFilter(EditRegistrationForm.edit_phone_number))
async def edit_phone_number_number_incorrect(message:Message):
    await message.answer(text = LEXICON_TEXT["registration_incorrect_phone_number"])

@user_router.message(StateFilter(EditRegistrationForm.edit_email),lambda message: is_valid_email(message.text) == True)
async def edit_email(message:Message, state: FSMContext):
    await state.update_data(email=message.text)
    await show_updated_form(message, state)

@user_router.message(StateFilter(EditRegistrationForm.edit_email))
async def edit_email_incorrect(message:Message):
    await message.answer(text = LEXICON_TEXT["registration_incorrect_email"])

@user_router.message(F.text == LEXICON_USER_KEYBOARD['submit_application'],StateFilter(default_state))
async def aplication_start(message: Message, state: FSMContext):
    """
    Обработка кнопки подать заявку
    """
    await message.answer(LEXICON_TEXT["application_select_event_topic"],reply_markup=direction_of_activities_keyboard )
    await state.set_state(ApplicationStates.direction_name)

@user_router.callback_query(StateFilter(ApplicationStates.direction_name))
async def direction_name(callback: CallbackQuery, state: FSMContext):
    """
    Обработка выбора направления
    """
    direction_name, thread_id = TOPIC_MAPPING[callback.data]
    await state.update_data(
        thread_id=thread_id,
        direction_name = direction_name
    )
    await callback.message.edit_text(f"✅ Вы выбрали: {direction_name}")
    await callback.message.answer(text=LEXICON_TEXT["application_fill_event_name"])
    await state.set_state(ApplicationStates.name_event)

@user_router.message(StateFilter(ApplicationStates.name_event))
async def name_of_event_sent(message: Message, state: FSMContext):
    await state.update_data(name_of_event=message.text)
    await message.answer(LEXICON_TEXT["application_fill_event_date"])
    await state.set_state(ApplicationStates.date_event)

@user_router.message(StateFilter(ApplicationStates.date_event))
async def date_of_event_sent(message: Message, state: FSMContext):
    if is_valid_event_date(message.text) == True:
        await state.update_data(date_of_event=message.text)
        await message.answer(LEXICON_TEXT["application_fill_event_location"])
        await state.set_state(ApplicationStates.event_location)
    else:
        await message.answer(LEXICON_TEXT["application_incorrect_event_date"])

@user_router.message(StateFilter(ApplicationStates.event_location))
async def date_of_event_sent(message: Message, state: FSMContext):
    await state.update_data(event_location=message.text)
    await message.answer(LEXICON_TEXT["application_event_select_role"],reply_markup=choice_role)
    await state.set_state(ApplicationStates.role_at_the_event)

@user_router.callback_query(StateFilter(ApplicationStates.role_at_the_event))
async def role_at_the_event_sent(callback: CallbackQuery, state: FSMContext):
    role_key = callback.data
    role_name = LEXICON_USER_KEYBOARD.get(role_key, 'Неизвестая роль')
    await state.update_data(role_name=role_name)
    await callback.message.edit_text(f"✅ Вы выбрали: {role_name}")
    await callback.message.answer(text=LEXICON_TEXT["application_event_material"])
    await state.set_state(ApplicationStates.supporting_manerial)
    
@user_router.message(StateFilter(ApplicationStates.supporting_manerial))
async def supporting_material_sent(message:Message,state:FSMContext):
    """
    Сохраняем отправленный материал
    """
    data = await state.get_data()
    user_id = message.from_user.id
    material_info = None
    
    material_text = ""
    
    if message.text:
        material_text = message.text
    elif message.document:
        material_text = message.document.file_name or ""
    elif message.caption:  
        material_text = message.caption
    
    if not is_valid_confirmation_material(material_text):
        await message.answer(
            "❌ Некорректный формат материала!\n\n"
            "✅ Допустимые форматы:\n"
            "• Ссылка: http:// или https://\n"
            "• Документы: .doc, .docx, .txt, .pdf\n"
            "• Изображения: .jpg, .jpeg, .png\n"
            "• Видео: .mov, .mkv, .avi, .mp4\n\n"
            "Отправьте материал заново:"
        )
        return
    
    if message.text and (message.text.startswith("http://") or message.text.startswith("https://")):
        material_info = {
            "type": "ссылка",
            "content": message.text,
            "timestamp": message.date.isoformat()
        }
        await message.answer("✅ Ссылка сохранена")
    elif message.document:
        material_info = {
            "type": "документ",
            "file_id": message.document.file_id,
            "file_name": message.document.file_name,
            "file_size": message.document.file_size,
            "mime_type": message.document.mime_type,
            "timestamp": message.date.isoformat()
        }
        await message.answer("✅ Документ сохранен")
    elif message.photo:
        material_info = {
            "type": "фото",
            "file_id": message.photo[-1].file_id,
            "width": message.photo[-1].width,
            "height": message.photo[-1].height,
            "timestamp": message.date.isoformat()
        }
        await message.answer("✅ Фото сохранено")
    elif message.video:
        material_info = {
            "type": "видео",
            "file_id": message.video.file_id,
            "file_name": message.video.file_name,
            "duration": message.video.duration,
            "file_size": message.video.file_size,
            "timestamp": message.date.isoformat()
        }
        await message.answer("✅ Видео сохранено")
    else:
        await message.answer(
            "❌ Пожалуйста, отправьте:\n"
            "• Ссылку (начинается с http:// или https://)\n"
            "• Документ (Word, PDF, Excel)\n"
            "• Фото или видео\n\n"
            "Вы можете прислать только один файл или ссылку."
        )
        return
    if material_info:
        await state.update_data(supporting_material=material_info)
    updated_data = await state.get_data()
    await message.answer("✅ Заявка успешно заполнена!\nПодтвердите данные или выберите что изменить\n\n"
                         f"🎯 <b>Направление внеучебной деятельности:</b> {data.get('direction_name', 'Не указано')}\n"
                         f"📌 <b>Название мероприятия:</b> {data.get('name_of_event', 'Не указано')}\n"
                         f"📅 <b>Дата проведения:</b> {data.get('date_of_event', 'Не указано')}\n"
                         f"📍 <b>Место проведения:</b> {data.get('event_location', 'Не указано')}\n"
                         f"👤 <b>Роль в мероприятии:</b> {data.get('role_name', 'Не указано')}\n"
                         f"📎 <b>Подтверждающий материал:</b> Прикреплен ниже 👇\n", reply_markup = application_confirm_keyboard)
    material = updated_data.get('supporting_material')
    if material and isinstance(material, dict):
        file_id = material.get('file_id')
        material_type = material.get('type')
        
        if material_type == 'фото' and file_id:
            await message.answer_photo(
                photo=file_id,
                caption="🖼️ Ваше подтверждающее фото"
            )
        elif material_type == 'документ' and file_id:
            file_name = material.get('file_name', 'Документ')
            await message.answer_document(
                document=file_id,
                caption=f"📄 {file_name}"
            )
        elif material_type == 'ссылка':
            await message.answer(f"🔗 Ссылка: {material.get('content')}")
        await state.set_state(ApplicationStates.application_process_end )

async def show_updated_application(message:Message, state: FSMContext):
    """
    Показывает обновленную заявку
    """
    data = await state.get_data()
    await message.answer("✅ Заявка успешно обновлена!\nПодтвердите данные или выберите что изменить\n\n"
                         f"🎯 <b>Направление внеучебной деятельности:</b> {data.get('direction_name', 'Не указано')}\n"
                         f"📌 <b>Название мероприятия:</b> {data.get('name_of_event', 'Не указано')}\n"
                         f"📅 <b>Дата проведения:</b> {data.get('date_of_event', 'Не указано')}\n"
                         f"📍 <b>Место проведения:</b> {data.get('event_location', 'Не указано')}\n"
                         f"👤 <b>Роль в мероприятии:</b> {data.get('role_name', 'Не указано')}\n"
                         f"📎 <b>Подтверждающий материал:</b> Прикреплен ниже 👇\n", reply_markup = application_confirm_keyboard)
    await state.set_state(ApplicationStates.application_process_end)

@user_router.callback_query(StateFilter(ApplicationStates.application_process_end ))
async def registration_end(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Обрабатываем нажатие на кнопки отправить отправить заявку/изменить заявку
    """
    if callback.data == ("confirm_application"):
        data = await state.get_data()
        user_id = callback.from_user.id
        updated_data = await state.get_data()
        thread_id = data.get("thread_id")
        utc_time = callback.message.date
        ekaterinburg_time = utc_time.astimezone(ekaterinburg_tz)

        user_full_name = "Не указано"  # TODO: из БД участников

        app_data = {
        "tg_id": user_id,
        "user_id": user_id,
        "full_name": user_full_name,
        "direction_name": data.get("direction_name", ""),
        "event_name": data.get("name_of_event", ""),
        "event_date": data.get("date_of_event", ""),
        "event_location": data.get("event_location", ""),
        "role_name": data.get("role_name", ""),
        "application_time": ekaterinburg_time.strftime('%d.%m.%Y %H:%M'),
        "status": "На рассмотрении",
        "moderator": "",
        "sheet_name": data.get("direction_name", ""),
        "thread_id": thread_id
        }

        direction_name = app_data["direction_name"]
        sheets_result = googlesheet_service.add_event_application(app_data, direction_name)

        moderator_message = (
            "📋 Новая заявка на проверку\n\n"
            f"👤 Пользователь: @{callback.from_user.username or 'без username'} "
            f"(ID: {user_id})\n"
            f"📊 Google Sheets: {'✅' if sheets_result.get('success') else '❌'}\n"
            f"📁 Лист: {direction_name}\n"
            f"📄 Строка: {sheets_result.get('row', 'N/A')}\n"
            f"📅 Время подачи: {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"📝 Данные заявки:\n"
            f"• ФИО: {user_full_name}\n"
            f"• Направление внеучебной деятельности: {data.get('direction_name', 'Не указано')}\n"
            f"• Название мероприятия: {data.get('name_of_event', 'Не указано')}\n"
            f"• Дата проведения: {data.get('date_of_event', 'Не указано')}\n"
            f"• Место проведения: {data.get('event_location', 'Не указано')}\n"
            f"• Роль в мероприятии: {data.get('role_name', 'Не указано')}\n"
            f"• Подтверждающий материал: Прикреплен ниже 👇\n"
        )
        moderator_proceesing_application_keyboard = ProcessingUserApplicationInlineButtons.get_inline_keyboard(user_id)
        send_params = {
                "chat_id": config.moderator_chat_id,
                "text": moderator_message,
                "reply_markup": moderator_proceesing_application_keyboard,
                "message_thread_id": thread_id 
            }
        await bot.send_message(**send_params)
        material = updated_data.get('supporting_material')
        if material:
            try:
                if isinstance(material, dict):
                    file_id = material.get('file_id')
                    material_type = material.get('type')
                    
                    if material_type == 'фото' and file_id:
                        await bot.send_photo(
                            chat_id=config.moderator_chat_id,
                            photo=file_id,
                            caption="🖼️ Подтверждающее фото от пользователя",
                            message_thread_id=thread_id
                        )
                    elif material_type == 'документ' and file_id:
                        file_name = material.get('file_name', 'Документ')
                        await bot.send_document(
                            chat_id=config.moderator_chat_id,
                            document=file_id,
                            caption=f"📄 {file_name}",
                            message_thread_id=thread_id
                        )
                    elif material_type == 'видео' and file_id:
                        await bot.send_video(
                            chat_id=config.moderator_chat_id,
                            video=file_id,
                            caption="🎥 Видео от пользователя",
                            message_thread_id=thread_id
                        )
                    elif material_type == 'ссылка' and material.get('content'):
                        await bot.send_message(
                            chat_id=config.moderator_chat_id,
                            text=f"🔗 Ссылка от пользователя: {material['content']}",
                            message_thread_id=thread_id
                        )
                else:
                    await bot.send_document(
                        chat_id=config.moderator_chat_id,
                        document=material,
                        caption="📎 Подтверждающий материал",
                        message_thread_id=thread_id
                    )
            except Exception as e:
                await bot.send_message(
                    chat_id=config.moderator_chat_id,
                    text=f"⚠️ Не удалось отправить материал.",
                    message_thread_id=thread_id
                )
        await callback.message.edit_text(text = LEXICON_TEXT["application_event_end"])
        await state.clear()
    elif callback.data == "edit_application":
        await callback.message.delete()
        await callback.message.answer(LEXICON_TEXT["application_edit"],reply_markup = change_of_application_keyboard)
        await state.set_state(ChangeApplicationStates.start)
    else:
        await callback.message.answer(
            text = LEXICON_TEXT["application_other_answer"]
        )

@user_router.callback_query(StateFilter(ChangeApplicationStates.start))
async def start_change_of_application(callback: CallbackQuery, state:FSMContext):
    """
    Начало изменения заявки
    """
    if callback.data == "edit_direction_of_activities":
        await callback.message.delete()
        await callback.message.answer(LEXICON_TEXT["application_edit_topic"],reply_markup = direction_of_activities_keyboard)
        await state.set_state(ChangeApplicationStates.change_direction_name)
    elif callback.data == "edit_event_name":
        await callback.message.delete()
        await callback.message.answer(LEXICON_TEXT["application_edit_name"])
        await state.set_state(ChangeApplicationStates.change_name_event)
    elif callback.data == "edit_event_date":
        await callback.message.delete()
        await callback.message.answer(LEXICON_TEXT["application_edit_date"])
        await state.set_state(ChangeApplicationStates.change_date_event)
    elif callback.data == "edit_event_location":
        await callback.message.delete()
        await callback.message.answer(LEXICON_TEXT["application_edit_location"])
        await state.set_state(ChangeApplicationStates.change_event_location)
    elif callback.data == "edit_role":
        await callback.message.delete()
        await callback.message.answer(LEXICON_TEXT["application_edit_role"], reply_markup = choice_role)
        await state.set_state(ChangeApplicationStates.change_role_at_the_event)
    elif callback.data == "edit_confirmation_material":
        await callback.message.delete()
        await callback.message.answer(LEXICON_TEXT["application_edit_material"])
        await state.set_state(ApplicationStates.supporting_manerial)
    else:
        await callback.message.answer(
            text = LEXICON_TEXT["application_other_answer"]
        )

@user_router.callback_query(StateFilter(ChangeApplicationStates.change_direction_name))
async def change_direction_name(callback:CallbackQuery, state:FSMContext):  
    direction_name, thread_id = TOPIC_MAPPING[callback.data]
    await state.update_data(
        thread_id=thread_id,
        direction_name = direction_name
    )
    await callback.message.edit_text(f"✅ Вы выбрали: {direction_name}")     
    await show_updated_application(callback.message, state)

@user_router.message(StateFilter(ChangeApplicationStates.change_name_event))
async def change_date_event(message:Message, state:FSMContext): 
    await state.update_data(name_of_event=message.text)   
    await show_updated_application(message, state)

@user_router.message(StateFilter(ChangeApplicationStates.change_date_event))
async def change_date_event(message:Message, state:FSMContext): 
    if is_valid_event_date(message.text) == True:
        await state.update_data(date_of_event=message.text)
        await show_updated_application(message, state)
    else:
        await message.answer(LEXICON_TEXT["application_incorrect_event_date"])


@user_router.message(StateFilter(ChangeApplicationStates.change_event_location))
async def change_event_location (message:Message, state:FSMContext):   
    await state.update_data(event_location=message.text) 
    await show_updated_application(message, state)

@user_router.callback_query(StateFilter(ChangeApplicationStates.change_role_at_the_event))
async def application_edit_role(callback:CallbackQuery, state:FSMContext):
    role_key = callback.data
    role_name = LEXICON_USER_KEYBOARD.get(role_key, 'Неизвестая роль')
    await state.update_data(role_name=role_name)
    await callback.message.edit_text(f"✅ Вы выбрали: {role_name}")   
    await show_updated_application(callback.message, state)

    
@user_router.message(F.text == LEXICON_USER_KEYBOARD['my_tyuiu_coins'],StateFilter(default_state))
async def tyuiu_coins_start(message: Message, state: FSMContext):
    await message.answer(text = LEXICON_TEXT["balance"])

@user_router.message(F.text == LEXICON_USER_KEYBOARD['catalog_of_rewards'],StateFilter(default_state))
async def catalog_start(message: Message, state: FSMContext):
    await message.answer("Здась будет каталог. Лексикон")

@user_router.message(F.text == LEXICON_USER_KEYBOARD['agreement_of_contest'],StateFilter(default_state))
async def competition_regulations_start(message: Message, state: FSMContext):
    """
    Высылает положение о конкурсе
    """
    document = FSInputFile(
            path =competition_regulations_path,
            filename="Положение_о_конкурсе_ТИУмничка.docx"  
        )
    await message.answer_document(document=document)

@user_router.message(F.text == LEXICON_USER_KEYBOARD['support'],StateFilter(default_state))
async def support_start(message:Message, state: FSMContext):
    """
    Обработчки кнопки поддержки
    """
    await message.answer(LEXICON_TEXT["support_head"],reply_markup=support_keyboard)
    await state.set_state(SupportStates.support_start)

@user_router.callback_query(StateFilter(SupportStates.support_start))
async def support_process(callback:CallbackQuery,state:FSMContext):
    """
    Обработчки инлайн-кнопок поддержки
    """
    if callback.data == "write_moderator_of_the_direct":
        await callback.message.edit_text(
            text = LEXICON_TEXT["support_select_event_topic"],reply_markup=direction_of_activities_keyboard
        )
        await state.set_state(SupportStates.support_choice_direction)
    elif callback.data == "feedback":
        await callback.message.edit_text(
            text = LEXICON_TEXT["feedback_text"]
        )
        await state.set_state(SupportStates.support_feedback_and_error)
    else:
        await callback.message.edit_text(
            text = LEXICON_TEXT["support_text"]
        )
        await state.set_state(SupportStates.support_feedback_and_error)

@user_router.callback_query(StateFilter(SupportStates.support_choice_direction))
async def support_choice_direction(callback:CallbackQuery, state:FSMContext):
    """
    Обработчки инлайн-кнопки написать модератору направления
    """
    direction_name, thread_id = TOPIC_MAPPING[callback.data]
    await state.update_data(
        thread_id=thread_id
    )
    await callback.message.edit_text(f"✅ Вы выбрали: {direction_name}")
    await callback.message.answer(text=LEXICON_TEXT["support_text"])
    await state.set_state(SupportStates.support_write_moderator)

@user_router.message(StateFilter(SupportStates.support_write_moderator))
async def support_write_moderator(message:Message,state:FSMContext, bot: Bot):
    """
    Обработчки инлайн-кнопки написать модератору направления
    """
    data = await state.get_data()
    thread_id = data.get("thread_id")
    utc_time = message.date
    ekaterinburg_time = utc_time.astimezone(ekaterinburg_tz)
    moderator_message = (
        "❗️ Новое сообщение от пользователя: \n\n"
        f"👤 Пользователь: @{message.from_user.username or 'без username'} "
        f"(ID: {message.from_user.id})\n"
        f"📅 Время подачи: {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"Сообщение: {message.text}"
    )
    moderator_support_keyboard = ModeratorSupportInlineButtons.get_inline_keyboard(message.from_user.id)
    send_params = {
                "chat_id": config.moderator_chat_id,
                "text": moderator_message,
                "reply_markup": moderator_support_keyboard,
                "message_thread_id": thread_id
            }
    await bot.send_message(**send_params)
    await message.answer(text = LEXICON_TEXT["support_end"])
    await state.clear()
    
@user_router.message(StateFilter(SupportStates.support_feedback_and_error))
async def support_feedback_and_error(message:Message,state:FSMContext, bot: Bot):
    """
    Обработчки инлайн-кнопок обратная связь и сообщить об ошибке
    """
    utc_time = message.date
    ekaterinburg_time = utc_time.astimezone(ekaterinburg_tz)
    moderator_message = (
        "❗️ Новое сообщение от пользователя: \n\n"
        f"👤 Пользователь: @{message.from_user.username or 'без username'} "
        f"(ID: {message.from_user.id})\n"
        f"📅 Время подачи: {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"Сообщение: {message.text}"
    )
    moderator_support_keyboard = ModeratorSupportInlineButtons.get_inline_keyboard(message.from_user.id)
    send_params = {
                "chat_id": config.moderator_chat_id,
                "text": moderator_message,
                "reply_markup": moderator_support_keyboard,
                "message_thread_id": 3
            }
    await bot.send_message(**send_params)
    await message.answer(text = LEXICON_TEXT["support_end"])
    await state.clear()
    

