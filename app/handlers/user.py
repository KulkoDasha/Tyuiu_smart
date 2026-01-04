from aiogram import Router, Bot, F
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.types import Message, CallbackQuery,FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from datetime import datetime
import pytz
import logging

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
catalog_of_rewards = ItemKeyboard()
additional_material_keyboard = AddMaterial.get_inline_keyboard()
confirm_material_keyboard = AddMaterialConfirm.get_inline_keyboard()
logger = logging.getLogger(__name__)

competition_regulations_path = "app\\files\\Polozhenie_o_Konkurse_nematerialnoy_motivatsii_obuchayuschikhsya_TIUmnichka.pdf"
agreement_path = "app\\files\\Soglasie_na_obrabotku_personalnx_dannx.pdf"

ekaterinburg_tz = pytz.timezone('Asia/Yekaterinburg')

@user_router.message(CommandStart(), StateFilter(default_state))
async def start(message: Message):
    """
    Хендлер на /start
    """

    # Логгер
    bot_logger.log_user_msg(
        tg_id=str(message.from_user.id),
        username=message.from_user.username,
        message="РЕГИСТРАЦИЯ: Пользователь написал /start"
    )

    await message.answer(text=LEXICON_TEXT["start_text"], reply_markup=keyboard_start)

@user_router.callback_query(F.data == "read_the_agreement")
async def send_the_agreement(callback: CallbackQuery):
    """
    Высылает согласие
    """
    await callback.answer()
    document = FSInputFile(
            path = agreement_path,
            filename = "Согласие на обработку персональных данных.pdf"
        )
    await callback.message.answer_document(document=document)
    await callback.answer()

@user_router.callback_query(F.data == "give_agreement")
async def give_agreement(callback:CallbackQuery, state: FSMContext):
    """
    Хендлер на принятие согласия
    """
    
    # Логгер
    bot_logger.log_user_msg(
        tg_id=str(callback.from_user.id),
        username=callback.from_user.username,
        message="РЕГИСТРАЦИЯ: Пользователь принял согласие и начал регистрацию"
    )

    await callback.message.edit_text(text=LEXICON_TEXT["give_agreement"])
    await callback.message.answer(text=LEXICON_TEXT["registration_fill_full_name"])
    await state.set_state(RegistrationFormStates.full_name)
    await callback.answer()

@user_router.callback_query(F.data == "refuse_agreement")
async def refuse_agreement(callback:CallbackQuery, state: FSMContext):
    """
    Хендлер на отказ от согласия
    """

    # Логгер
    bot_logger.log_user_msg(
        tg_id=str(callback.from_user.id),
        username=callback.from_user.username,
        message="РЕГИСТРАЦИЯ: Пользователь НЕ принял согласие"
    )

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

    # Логгер
    bot_logger.log_user_msg(
        tg_id=str(callback.from_user.id),
        username=callback.from_user.username,
        message="РЕГИСТРАЦИЯ: Пользователь начал регистрацию заново"
    )

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
    await state.update_data(phone_number = message.text)
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
                         f"<b>ФИО:</b> {data.get('full_name', 'Не указано')}\n"
                         f"<b>Структурное подразделение обучения:</b> {data.get('institute', 'Не указано')}\n"
                         f"<b>Направление:</b> {data.get('direction', 'Не указано')}\n"
                         f"<b>Курс:</b> {data.get('course', 'Не указано')}\n"
                         f"<b>Группа:</b> {data.get('group', 'Не указано')}\n"
                         f"<b>Год начала обучения:</b> {data.get('start_year', 'Не указано')}\n"
                         f"<b>Год окончания программы обучения:</b> {data.get('end_year', 'Не указано')}\n"
                         f"<b>Номер телефона:</b> {data.get('phone_number', 'Не указано')}\n"
                         f"<b>Email:</b> {message.text}\n",reply_markup= confirm_registration_form)
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
            f"👤 <b>Пользователь:</b> @{callback.from_user.username or 'без username'} "
            f"(<b>ID:</b> {callback.from_user.id})\n"
            f"📅 <b>Время подачи:</b> {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"📝 Данные анкеты:\n"
            f"• <b>ФИО:</b> {data.get('full_name', 'Не указано')}\n"
            f"• <b>Структурное подразделение обучения:</b> {data.get('institute', 'Не указано')}\n"
            f"• <b>Направление:</b> {data.get('direction', 'Не указано')}\n"
            f"• <b>Курс:</b> {data.get('course', 'Не указано')}\n"
            f"• <b>Группа:</b> {data.get('group', 'Не указано')}\n"
            f"• <b>Год начала обучения:</b> {data.get('start_year', 'Не указано')}\n"
            f"• <b>Год окончания программы обучения:</b> {data.get('end_year', 'Не указано')}\n"
            f"• <b>Номер телефона:</b> {data.get('phone_number', 'Не указано')}\n"
            f"• <b>Email:</b> {data.get('email', 'Не указано')}\n"
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
        
        # Логгер
        bot_logger.log_user_msg(
        tg_id=str(callback.from_user.id),
        username=callback.from_user.username,
        message=f"РЕГИСТРАЦИЯ: Пользователь отправил анкету на регистрацию\n"
            f"ФИО: {data.get('full_name', 'Не указано')}\n"
            f"Структурное подразделение обучения: {data.get('institute', 'Не указано')}\n"
            f"Направление: {data.get('direction', 'Не указано')}\n"
            f"Номер телефона: {data.get('phone_number', 'Не указано')}"
        )

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
                         f"<b>ФИО:</b> {data.get('full_name', 'Не указано')}\n"
                         f"<b>Структурное подразделение обучения:</b> {data.get('institute', 'Не указано')}\n"
                         f"<b>Направление:</b> {data.get('direction', 'Не указано')}\n"
                         f"<b>Курс:</b> {data.get('course', 'Не указано')}\n"
                         f"<b>Группа:</b> {data.get('group', 'Не указано')}\n"
                         f"<b>Год начала обучения:</b> {data.get('start_year', 'Не указано')}\n"
                         f"<b>Год окончания программы обучения:</b> {data.get('end_year', 'Не указано')}\n"
                         f"<b>Номер телефона:</b> {data.get('phone_number', 'Не указано')}\n"
                         f"<b>Email:</b> {data.get('email', 'Не указано')}\n", reply_markup=confirm_registration_form)
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
        await show_updated_form(message, state)
    else:
        await message.answer(LEXICON_TEXT["registration_incorrect_end_year"])
    

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
    await state.set_state(EventApplicationStates.event_direction)

@user_router.callback_query(StateFilter(EventApplicationStates.event_direction))
async def event_direction(callback: CallbackQuery, state: FSMContext):
    """
    Обработка выбора направления
    """
    event_direction, thread_id = TOPIC_MAPPING[callback.data]
    await state.update_data(
        thread_id=thread_id,
        event_direction = event_direction
    )
    await callback.message.edit_text(f"✅ Вы выбрали: {event_direction}")
    await callback.message.answer(text=LEXICON_TEXT["application_fill_event_name"])
    await state.set_state(EventApplicationStates.name_event)
    await callback.answer()

@user_router.message(StateFilter(EventApplicationStates.name_event))
async def name_of_event_sent(message: Message, state: FSMContext):
    await state.update_data(name_of_event=message.text)
    await message.answer(LEXICON_TEXT["application_fill_event_date"])
    await state.set_state(EventApplicationStates.date_event)

@user_router.message(StateFilter(EventApplicationStates.date_event))
async def date_of_event_sent(message: Message, state: FSMContext):
    if is_valid_event_date(message.text) == True:
        await state.update_data(date_of_event=message.text)
        await message.answer(LEXICON_TEXT["application_fill_event_location"])
        await state.set_state(EventApplicationStates.event_location)
    else:
        await message.answer(LEXICON_TEXT["application_incorrect_event_date"])

@user_router.message(StateFilter(EventApplicationStates.event_location))
async def date_of_event_sent(message: Message, state: FSMContext):
    await state.update_data(event_location=message.text)
    await message.answer(LEXICON_TEXT["application_event_select_role"],reply_markup=choice_role)
    await state.set_state(EventApplicationStates.role_at_the_event)

@user_router.callback_query(StateFilter(EventApplicationStates.role_at_the_event))
async def role_at_the_event_sent(callback: CallbackQuery, state: FSMContext):
    role_key = callback.data
    event_role = LEXICON_USER_KEYBOARD.get(role_key, 'Неизвестая роль')
    await state.update_data(event_role=event_role)
    await state.update_data(supporting_materials=[])
    await callback.message.edit_text(f"✅ Вы выбрали: {event_role}")
    await callback.message.answer(text=LEXICON_TEXT["application_event_material"])
    await state.set_state(EventApplicationStates.supporting_manerial)
    await callback.answer()
    
@user_router.message(StateFilter(EventApplicationStates.supporting_manerial))
async def supporting_material_sent(message:Message,state:FSMContext):
    """
    Сохраняем отправленный материал
    """
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
    
    if material_info:
        materials_list.append(material_info)
        await state.update_data(supporting_materials=materials_list)
        await show_current_materials(message, materials_list)
    await state.set_state(EventApplicationStates.application_process_end)

@user_router.callback_query(F.data == "finish_application", StateFilter(EventApplicationStates.application_process_end))
async def finish_application_handler(callback: CallbackQuery, state: FSMContext):
    """
    Завершение заявки и показ итоговой информации
    """
    data = await state.get_data()
    materials_list = data.get('supporting_materials', [])
    await callback.message.edit_text(text= f"✅ <b>Заявка успешно заполнена!</b>\n\n"
                                     f"🎯 <b>Направление внеучебной деятельности:</b> {data.get('event_direction', 'Не указано')}\n"
                                     f"📌 <b>Название мероприятия:</b> {data.get('name_of_event', 'Не указано')}\n"
                                     f"📅 <b>Дата проведения:</b> {data.get('date_of_event', 'Не указано')}\n"
                                     f"📍 <b>Место проведения:</b> {data.get('event_location', 'Не указано')}\n"
                                     f"👤 <b>Роль в мероприятии:</b> {data.get('event_role', 'Не указано')}\n"
                                     f"\n📎 <b>Подтверждающие материалы:</b> ({len(materials_list)} шт.)\n", reply_markup=application_confirm_keyboard)
    await callback.answer()

@user_router.callback_query(F.data == "add_more_material",StateFilter(EventApplicationStates.application_process_end))
async def add_more_material(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик кнопки "Добавить еще материал"
    """
    await callback.message.edit_text(
        "📤 Отправьте следующий материал\n\n"
    )
    await state.set_state(EventApplicationStates.supporting_manerial)
    await callback.answer()
    
async def show_current_materials(message: Message, materials_list: list):
    """
    Показывает текущий список материалов
    """
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
    """
    Показывает обновленную заявку
    """
    data = await state.get_data()
    await message.answer("✅ Заявка успешно обновлена!\nПодтвердите данные или выберите что изменить\n\n"
                         f"🎯 <b>Направление внеучебной деятельности:</b> {data.get('event_direction', 'Не указано')}\n"
                         f"📌 <b>Название мероприятия:</b> {data.get('name_of_event', 'Не указано')}\n"
                         f"📅 <b>Дата проведения:</b> {data.get('date_of_event', 'Не указано')}\n"
                         f"📍 <b>Место проведения:</b> {data.get('event_location', 'Не указано')}\n"
                         f"👤 <b>Роль в мероприятии:</b> {data.get('event_role', 'Не указано')}\n"
                         f"📎 <b>Подтверждающий материал:</b> Прикреплен ниже 👇\n", reply_markup = application_confirm_keyboard)
    await state.set_state(EventApplicationStates.application_process_end)

@user_router.callback_query(StateFilter(EventApplicationStates.application_process_end ))
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
        "event_direction": data.get("event_direction", ""),
        "name_of_event": data.get("name_of_event", ""),
        "date_of_event": data.get("date_of_event", ""),
        "event_location": data.get("event_location", ""),
        "event_role": data.get("event_role", ""),
        "application_time": ekaterinburg_time.strftime('%d.%m.%Y %H:%M'),
        "status": "На рассмотрении",
        "moderator": "",
        "sheet_name": data.get("event_direction", ""),
        "thread_id": thread_id
        }

        event_direction = app_data["event_direction"]
        sheets_result = googlesheet_service.add_event_application(app_data, event_direction)

        moderator_message = (
            "📋 Новая заявка на проверку\n\n"
            f"👤 <b>Пользователь:</b> @{callback.from_user.username or 'без username'} "
            f"(<b>ID:</b> {user_id})\n"
            f"📊 <b>Google Sheets:</b> {'✅' if sheets_result.get('success') else '❌'}\n"
            f"📁 <b>Лист:</b> {event_direction}\n"
            f"📄 <b>Строка:</b> {sheets_result.get('row', 'N/A')}\n"
            f"📅 <b>Время подачи:</b> {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"📝 <b>Данные заявки:</b>\n"
            f"• <b>ФИО</b>: {user_full_name}\n"
            f"• <b>Направление внеучебной деятельности:</b> {data.get('event_direction', 'Не указано')}\n"
            f"• <b>Название мероприятия:</b> {data.get('name_of_event', 'Не указано')}\n"
            f"• <b>Дата проведения:</b> {data.get('date_of_event', 'Не указано')}\n"
            f"• <b>Место проведения:</b> {data.get('event_location', 'Не указано')}\n"
            f"• <b>Роль в мероприятии:</b> {data.get('event_role', 'Не указано')}\n"
            f"• <b>Подтверждающий материал:</b> {len(data.get('supporting_materials', []))} шт. 👇\n"
        )
        clean_role = data.get('event_role', 'Не указано')[2:14].replace("/", "_")
        moderator_proceesing_application_keyboard = ProcessingUserApplicationInlineButtons.get_inline_keyboard(user_id, clean_role)
        send_params = {
                "chat_id": config.moderator_chat_id,
                "text": moderator_message,
                "reply_markup": moderator_proceesing_application_keyboard,
                "message_thread_id": thread_id 
            }
        
        # Логгер
        bot_logger.log_user_msg(
        tg_id=str(callback.from_user.id),
        username=callback.from_user.username,
        message=f"ЗАЯВКА: Пользователь отправил заявку на получение 'ТИУКоинов'\n"
            f"Google Sheets: {'✅' if sheets_result.get('success') else '❌'}\n"
            f"Лист: {event_direction}, {sheets_result.get('row', 'N/A')} строка\n"
            f"ФИО: {user_full_name}\n"
            f"Направление внеучебной деятельности: {data.get('event_direction', 'Не указано')}\n"
            f"Название мероприятия: {data.get('name_of_event', 'Не указано')}\n"
            f"Роль в мероприятии: {data.get('event_role', 'Не указано')}\n"
        )
        await bot.send_message(**send_params)
        
        materials_list = data.get('supporting_materials', [])
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
                            chat_id=config.moderator_chat_id,
                            text=f"🔗 <b>Ссылка {i}:</b>\n{material['content']}",
                            message_thread_id=thread_id,
                            parse_mode="HTML"
                        )
                    elif material['type'] == 'документ':
                        await bot.send_document(
                            chat_id=config.moderator_chat_id,
                            document=material['file_id'],
                            caption=caption,
                            message_thread_id=thread_id,
                            parse_mode="HTML"
                        )
                    elif material['type'] == 'фото':
                        await bot.send_photo(
                            chat_id=config.moderator_chat_id,
                            photo=material['file_id'],
                            caption=caption,
                            message_thread_id=thread_id,
                            parse_mode="HTML"
                        )
                    elif material['type'] == 'видео':
                        await bot.send_video(
                            chat_id=config.moderator_chat_id,
                            video=material['file_id'],
                            caption=caption,
                            message_thread_id=thread_id,
                            parse_mode="HTML"
                        )
                except Exception as e:
                    await bot.send_message(
                        chat_id=config.moderator_chat_id,
                        text=f"❌ Ошибка отправки материала {i}",
                        message_thread_id=thread_id
                        )
        else:
            await bot.send_message(
                chat_id=config.moderator_chat_id,
                text="⚠️ <b>Подтверждающие материалы не приложены</b>",
                message_thread_id=thread_id,
                parse_mode="HTML"
            )
        await callback.message.edit_text(text = LEXICON_TEXT["application_event_end"])
        await state.clear()
    elif callback.data == "edit_application":
        await callback.message.delete()
        await callback.message.answer(LEXICON_TEXT["application_edit"],reply_markup = change_of_application_keyboard)
        await state.set_state(ChangeEventApplicationStates.start)
    else:
        await callback.message.answer(
            text = LEXICON_TEXT["application_other_answer"]
        )
    await callback.answer()

@user_router.callback_query(StateFilter(ChangeEventApplicationStates.start))
async def start_change_of_application(callback: CallbackQuery, state:FSMContext):
    """
    Начало изменения заявки
    """
    if callback.data == "edit_direction_of_activities":
        await callback.message.delete()
        await callback.message.answer(LEXICON_TEXT["application_edit_topic"],reply_markup = direction_of_activities_keyboard)
        await state.set_state(ChangeEventApplicationStates.change_event_direction)
    elif callback.data == "edit_event_name":
        await callback.message.delete()
        await callback.message.answer(LEXICON_TEXT["application_edit_name"])
        await state.set_state(ChangeEventApplicationStates.change_name_event)
    elif callback.data == "edit_event_date":
        await callback.message.delete()
        await callback.message.answer(LEXICON_TEXT["application_edit_date"])
        await state.set_state(ChangeEventApplicationStates.change_date_event)
    elif callback.data == "edit_event_location":
        await callback.message.delete()
        await callback.message.answer(LEXICON_TEXT["application_edit_location"])
        await state.set_state(ChangeEventApplicationStates.change_event_location)
    elif callback.data == "edit_role":
        await callback.message.delete()
        await callback.message.answer(LEXICON_TEXT["application_edit_role"], reply_markup = choice_role)
        await state.set_state(ChangeEventApplicationStates.change_role_at_the_event)
    elif callback.data == "edit_confirmation_material":
        await callback.message.delete()
        await state.update_data(supporting_materials=[])
        await callback.message.answer(LEXICON_TEXT["application_edit_material"])
        await state.set_state(EventApplicationStates.supporting_manerial)
    else:
        await callback.message.answer(
            text = LEXICON_TEXT["application_other_answer"]
        )

@user_router.callback_query(StateFilter(ChangeEventApplicationStates.change_event_direction))
async def change_event_direction(callback:CallbackQuery, state:FSMContext):  
    event_direction, thread_id = TOPIC_MAPPING[callback.data]
    await state.update_data(
        thread_id=thread_id,
        event_direction = event_direction
    )
    await callback.message.edit_text(f"✅ Вы выбрали: {event_direction}")     
    await show_updated_application(callback.message, state)

@user_router.message(StateFilter(ChangeEventApplicationStates.change_name_event))
async def change_date_event(message:Message, state:FSMContext): 
    await state.update_data(name_of_event=message.text)   
    await show_updated_application(message, state)

@user_router.message(StateFilter(ChangeEventApplicationStates.change_date_event))
async def change_date_event(message:Message, state:FSMContext): 
    if is_valid_event_date(message.text) == True:
        await state.update_data(date_of_event=message.text)
        await show_updated_application(message, state)
    else:
        await message.answer(LEXICON_TEXT["application_incorrect_event_date"])


@user_router.message(StateFilter(ChangeEventApplicationStates.change_event_location))
async def change_event_location (message:Message, state:FSMContext):   
    await state.update_data(event_location=message.text) 
    await show_updated_application(message, state)

@user_router.callback_query(StateFilter(ChangeEventApplicationStates.change_role_at_the_event))
async def application_edit_role(callback:CallbackQuery, state:FSMContext):
    role_key = callback.data
    event_role = LEXICON_USER_KEYBOARD.get(role_key, 'Неизвестая роль')
    await state.update_data(event_role=event_role)
    await callback.message.edit_text(f"✅ Вы выбрали: {event_role}")   
    await show_updated_application(callback.message, state)

    
@user_router.message(F.text == LEXICON_USER_KEYBOARD['my_tyuiu_coins'],StateFilter(default_state))
async def tyuiu_coins_start(message: Message, state: FSMContext):
    await message.answer(text = LEXICON_TEXT["balance"])

@user_router.message(F.text == LEXICON_USER_KEYBOARD['catalog_of_rewards'],StateFilter(default_state))
async def catalog_start(message: Message, state: FSMContext):
    """
    Обрабатывает нажатие на кнопку 'Каталог Поощрений'
    """
    keyboard_markup = await catalog_of_rewards.create_table_keyboard()
    await message.answer(LEXICON_TEXT["select_item"],reply_markup = keyboard_markup)
    await state.set_state(CatalogOfRewardsStates.catalog_of_revards_start)

@user_router.callback_query(F.data == "cancel_item" ,StateFilter(CatalogOfRewardsStates.catalog_of_revards_start))
async def cancel_item(callback:CallbackQuery,state: FSMContext):
    await callback.message.edit_text(LEXICON_TEXT["cancel_fsm"])
    await state.clear()
    await callback.answer()

@user_router.callback_query(F.data.startswith("view_item_"),StateFilter(CatalogOfRewardsStates.catalog_of_revards_start))
async def show_item_details_hendler(callback: CallbackQuery,state: FSMContext):
    """
    Просмотр выбранного поощрения
    """
    await show_item_details(callback)
    await state.set_state(CatalogOfRewardsStates.show_item_details_state)
    await callback.answer()

@user_router.callback_query(F.data == "close_all",StateFilter(CatalogOfRewardsStates.show_item_details_state))
async def close_all(callback:CallbackQuery,state: FSMContext):
    await callback.message.edit_text(LEXICON_TEXT["cancel_fsm"])
    await state.clear()
    await callback.answer()
    
@user_router.callback_query(F.data == "show_table",StateFilter(CatalogOfRewardsStates.show_item_details_state))   
async def show_table(callback:CallbackQuery,state: FSMContext):
    keyboard_markup = await catalog_of_rewards.create_table_keyboard()
    await callback.message.edit_text(LEXICON_TEXT["select_item"],reply_markup = keyboard_markup)
    await state.set_state(CatalogOfRewardsStates.catalog_of_revards_start)

@user_router.callback_query(F.data.startswith("select_item_"),StateFilter(CatalogOfRewardsStates.show_item_details_state))
async def select_item(callback:CallbackQuery,state: FSMContext):
    """
    Обрабатывает нажатие на кнопку "Выбрать этот товар"
    """
    await show_purchase_confirmation(callback)
    await state.set_state(CatalogOfRewardsStates.show_purchase_confirmation_state)
    await callback.answer()

@user_router.callback_query(F.data.startswith("confirm_purchase_"),StateFilter(CatalogOfRewardsStates.show_purchase_confirmation_state))
async def confirm_purchase(callback:CallbackQuery,state: FSMContext, bot: Bot):
    """
    Подтверждение списания ТИУкоинов
    """
    # TODO:Сделать проверку есть ли данное количество коинов на балансе студента
    item_key = callback.data.replace("confirm_purchase_", "")
    details = ITEM_DETAILS[item_key]
    name_of_item = details["title"]
    spend_amount = details["price"]
    purchase_date = datetime.now().strftime("%d.%m.%Y")
    confirm_text = LEXICON_TEXT["confirm_purchase"].format(
        name_of_item=name_of_item,
        spend_amount=spend_amount,
        purchase_date=purchase_date
    )
    await callback.message.edit_text(text=confirm_text, parse_mode="HTML")
    await state.clear()
    await callback.answer("✅ Покупка успешно завершена!",show_alert=True)
    user_full_name = "Не указано"  # TODO: из БД участников
    status = "Ожидает выдачи"
    application_id = 1 # TODO: из Гугл таблиц
    user_id = callback.from_user.id
    moderator_message = (
        "🔔 <b>Новая заявка на получение поощрения</b>\n\n"
        f"🆔 <b>ID заявки:</b> {application_id}\n"
        f"👤 <b>Студент:</b> {user_full_name}\n"
        f"👤 <b>ID Студента:</b> {user_id}\n"
        f"📞 <b>Username:</b> @{callback.from_user.username or 'без username'}\n"
        f"🎁 <b>Товар:</b> {name_of_item}\n"
        f"💰 <b>Стоимость:</b> {spend_amount} ТИУкоинов\n"
        f"📅 <b>Дата:</b> {purchase_date}\n"
        f"📍 <b>Место выдачи:</b> Володарского, 38, кабинет ....Уточнить\n"
        f"📋 <b>Статус:</b> {status}\n"
    )
    moderator_keyboards = ModeratorCloseRewards.get_inline_keyboard(user_id,application_id)
    send_params = {
                "chat_id": config.moderator_chat_id,
                "text": moderator_message,
                "reply_markup": moderator_keyboards,
                "message_thread_id": 496
            }
    await bot.send_message(**send_params)

@user_router.callback_query(F.data.startswith("cancel_purchase_"),StateFilter(CatalogOfRewardsStates.show_purchase_confirmation_state))
async def cancel_purchase(callback:CallbackQuery,state: FSMContext):
    """
    Отмена списания ТИУкоинов
    """
    keyboard_markup = await catalog_of_rewards.create_table_keyboard()
    await callback.message.edit_text(LEXICON_TEXT["select_item"],reply_markup = keyboard_markup)
    await state.set_state(CatalogOfRewardsStates.catalog_of_revards_start)
    await callback.answer("❌ Покупка отменена", show_alert=True)

@user_router.message(F.text == LEXICON_USER_KEYBOARD['agreement_of_contest'],StateFilter(default_state))
async def competition_regulations_start(message: Message, state: FSMContext):
    """
    Высылает положение о конкурсе
    """
    document = FSInputFile(
            path = competition_regulations_path,
            filename = "Положение_о_конкурсе_ТИУмничка.pdf"
        )
    await message.answer_document(document=document)

@user_router.message(Command(commands='support'),StateFilter(default_state))
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
        await state.set_state(SupportStates.support_feedback)
    else:
        await callback.message.edit_text(
            text = LEXICON_TEXT["support_text"]
        )
        await state.set_state(SupportStates.support_error)

@user_router.callback_query(StateFilter(SupportStates.support_choice_direction))
async def support_choice_direction(callback:CallbackQuery, state:FSMContext):
    """
    Обработчик инлайн-кнопки написать модератору направления
    """
    event_direction, thread_id = TOPIC_MAPPING[callback.data]
    await state.update_data(
        thread_id=thread_id
    )
    await callback.message.edit_text(f"✅ Вы выбрали: {event_direction}")
    await callback.message.answer(text=LEXICON_TEXT["support_text"])
    await state.set_state(SupportStates.support_write_moderator)

@user_router.message(StateFilter(SupportStates.support_write_moderator))
async def support_write_moderator(message:Message,state:FSMContext, bot: Bot):
    """
    Обработчик инлайн-кнопки написать модератору направления
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
    moderator_support_keyboard = ModeratorSupportInlineButtons.get_inline_keyboard(message.from_user.id, message.text)
    send_params = {
                "chat_id": config.moderator_chat_id,
                "text": moderator_message,
                "reply_markup": moderator_support_keyboard,
                "message_thread_id": thread_id
            }
    
    # Логгер
    bot_logger.log_user_msg(
    tg_id=str(message.from_user.id),
    username= message.from_user.username,
    message=f"ПОДДЕРЖКА: Пользователь написал модератору направления '{thread_id}': {message.text}"
    )

    await bot.send_message(**send_params)
    await message.answer(text = LEXICON_TEXT["support_end"])
    await state.clear()
    
@user_router.message(StateFilter(SupportStates.support_feedback))
async def support_feedback_and_error(message:Message,state:FSMContext, bot: Bot):
    """
    Обработчки инлайн-кнопок обратная связь 
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
    moderator_support_keyboard = ModeratorSupportInlineButtons.get_inline_keyboard(message.from_user.id,message.text)
    send_params = {
                "chat_id": config.moderator_chat_id,
                "text": moderator_message,
                "reply_markup": moderator_support_keyboard,
                "message_thread_id": USER_FEEDBACK
            }
    await bot.send_message(**send_params)
    await message.answer(text = LEXICON_TEXT["support_end"])
    await state.clear()

@user_router.message(StateFilter(SupportStates.support_error))
async def support_feedback_and_error(message:Message,state:FSMContext, bot: Bot):
    """
    Обработчки инлайн-кнопок сообщить об ошибке
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
    moderator_support_keyboard = ModeratorSupportInlineButtons.get_inline_keyboard(message.from_user.id,message.text)
    send_params = {
                "chat_id": config.moderator_chat_id,
                "text": moderator_message,
                "reply_markup": moderator_support_keyboard,
                "message_thread_id": TOPIC_SUPPORT
            }
    
    # Логгер
    bot_logger.log_user_msg(
    tg_id=str(message.from_user.id),
    username= message.from_user.username,
    message=f"ПОДДЕРЖКА: Пользователь написал в поддержку: {message.text}"
    )

    await bot.send_message(**send_params)
    await message.answer(text = LEXICON_TEXT["support_end"])
    await state.clear()

@user_router.message(Command(commands="getmytgid"),StateFilter(default_state))
async def getmytgid(message: Message):
    await message.answer(f"🆔 Ваш телеграмм айди: <b>{message.from_user.id}</b>")
    

