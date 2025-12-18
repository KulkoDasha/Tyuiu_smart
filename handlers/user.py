from aiogram import Router, Bot, F
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.types import Message, Update, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from datetime import datetime
import pytz

from states.user_states import RegistrationFormStates, EditRegistrationForm, Application
from keyboards.user_keyboard import (AgreementInlineButtons, 
                                     MenuKeyboard, 
                                     ChoiceOfInstituteInlineButtons,
                                     ChangeRegistrationFormInlineButtons,
                                     ConfirmRegistrationFormInlineButtons)
from lexicon import (LEXICON_TEXT, 
                    LEXICON_USER_KEYBOARD,
                    INSTITUTE_MAPPING)
from keyboards.moderator_keyboard import RegisterNewUserInlineButtons
from config.config import config

user_router = Router()
keyboard_start = AgreementInlineButtons.get_inline_keyboard()
menu_keyboard = MenuKeyboard.get_keyboard_menu()
institute_keyboard = ChoiceOfInstituteInlineButtons.get_inline_keyboard()
change_registration_form = ChangeRegistrationFormInlineButtons.get_inline_keyboard()
confirm_registration_form = ConfirmRegistrationFormInlineButtons.get_inline_keyboard()


ekaterinburg_tz = pytz.timezone('Asia/Yekaterinburg')

def is_valid_date(text: str) -> int:
    """Проверяет дату в формате ГГГГ"""
    try:
        datetime.strptime(text, '%Y')
        return True
    except ValueError:
        return False

def is_valid_email(email: str) -> bool:
    """Проверяет корректность email адреса"""
    email = email.strip().lower()
    if '@' not in email:
        return False
    else:
        return True

@user_router.message(CommandStart(),StateFilter(default_state))
async def start(message: Message):
    """
    Хендлер на команду страрт
    """
    await message.answer(text=LEXICON_TEXT["start_text"], reply_markup = keyboard_start)

@user_router.callback_query(F.data.startswith("read_the_agreement"))
async def send_the_agreement(callback: CallbackQuery):
    """
    Хендлер на обработку согласия
    """
    await callback.message.answer("Вставить согласие")
    await callback.answer()

@user_router.callback_query(F.data.startswith("give_agreement"))
async def give_agreement(callback:CallbackQuery, state: FSMContext):
    """
    Хендлер на принятие согласия
    """
    await callback.message.edit_text(text=LEXICON_TEXT["give_agreement"])
    await callback.message.answer(text=LEXICON_TEXT["registration_fill_full_name"])
    await state.set_state(RegistrationFormStates.full_name)
    await callback.answer()

@user_router.callback_query(F.data.startswith("refuse_agreement"))
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

@user_router.message(StateFilter(RegistrationFormStates.full_name), F.text.regexp(r'^[А-ЯЁа-яё\s]+$'))
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
    institute_name = INSTITUTE_MAPPING.get(institute_key, 'Неизвестный институт')
    await callback.message.edit_text(f"✅ Вы выбрали: {institute_name}")
    
    await state.update_data(institute=institute_name)
    await callback.message.answer(text = LEXICON_TEXT["registration_fill_direction"])  
    await state.set_state(RegistrationFormStates.direction)

@user_router.message(StateFilter(RegistrationFormStates.direction), F.text.regexp(r'^[А-ЯЁа-яё\s]+$'))
async def form_of_education_sent(message:Message, state:FSMContext):
    """
    Ввели направление, запрашиваем форму обучения
    """
    await state.update_data(direction = message.text)
    await message.answer(text = LEXICON_TEXT["registration_fill_form_of_education"])  
    await state.set_state(RegistrationFormStates.form_of_education)

@user_router.message(StateFilter(RegistrationFormStates.direction))
async def process_from_of_education_incorrect(message:Message):
    """если направление неккоректно"""
    await message.answer(text=LEXICON_TEXT["registration_incorrect_direction"])
    
@user_router.message(StateFilter(RegistrationFormStates.form_of_education), lambda message: message.text.lower() in ["очная", "заочная"])
async def form_of_education_sent(message:Message, state:FSMContext):
    """
    Ввели направление, запрашиваем курс
    """
    await state.update_data(form_of_education = message.text)
    await message.answer(text = LEXICON_TEXT["registration_fill_course"])  
    await state.set_state(RegistrationFormStates.course)

@user_router.message(StateFilter(RegistrationFormStates.form_of_education))
async def process_from_of_education_incorrect(message:Message):
    """если форма обучения неккоректна"""
    await message.answer(text = LEXICON_TEXT["registration_incorrect_form_of_education"])

@user_router.message(StateFilter(RegistrationFormStates.course),lambda message: message.text in ["1","2","3","4","5"])
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

@user_router.message(StateFilter(RegistrationFormStates.group))
async def groupe_sent(message: Message, state: FSMContext):
    """
    Ввели курс, запрашиваем год поступления
    """
    await state.update_data(group = message.text)
    await message.answer(text = LEXICON_TEXT["registration_fill_start_year"])  
    await state.set_state(RegistrationFormStates.start_year)

@user_router.message(StateFilter(RegistrationFormStates.start_year),lambda message: is_valid_date(message.text))
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

@user_router.message(StateFilter(RegistrationFormStates.end_year),lambda message: is_valid_date(message.text))
async def end_year_sent(message: Message, state: FSMContext):
    """
    Ввели дату конца, запрашиваем номер телефона
    """
    await state.update_data(end_year = message.text)
    await message.answer(text = LEXICON_TEXT["registration_fill_phone_number"]) 
    await state.set_state(RegistrationFormStates.phone_number)

@user_router.message(StateFilter(RegistrationFormStates.end_year))
async def process_end_year_incorrect(message:Message): 
    """если дата конца неккоректна"""
    await message.answer(LEXICON_TEXT["registration_incorrect_end_year"])

@user_router.message(StateFilter(RegistrationFormStates.phone_number))
async def phone_sent(message: Message, state: FSMContext):  
    """
    Ввели телефон, запрашиваем почту
    """
    await state.update_data(phone = message.text)
    await message.answer(text = LEXICON_TEXT["registration_fill_email"])  
    await state.set_state(RegistrationFormStates.email)

@user_router.message(StateFilter(RegistrationFormStates.phone_number))
async def process_phone_incorrect(message:Message): 
    """если номер телефона неккоректен""" 
    await message.answer(text = LEXICON_TEXT["registration_incorrect_phone_number"])

@user_router.message(StateFilter(RegistrationFormStates.email))
async def email_sent(message: Message, state: FSMContext):  
    """
    Если почта корректна, выводим итоговое сообщение
    """
    await state.update_data(email = message.text)
    data = await state.get_data()
    await message.answer("✅ Анкета успешно заполнена!Подтвердите данные или выберите что изменить\n\n"
                         f"ФИО: {data.get('full_name', 'Не указано')}\n"
                         f"Структурное подразделение обучения: {data.get('institute', 'Не указано')}\n"
                         f"Направление: {data.get('direction', 'Не указано')}\n"
                         f"Форма обучения: {data.get('form_of_education', 'Не указано')}\n"
                         f"Курс: {data.get('course', 'Не указано')}\n"
                         f"Группа: {data.get('group', 'Не указано')}\n"
                         f"Год начала обучения: {data.get('start_year', 'Не указано')}\n"
                         f"Год окончания программы обучения: {data.get('end_year', 'Не указано')}\n"
                         f"Телефон: {data.get('phone', 'Не указано')}\n"
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
    if callback.data.startswith("save_registration_form"):
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
            f"• Форма обучения: {data.get('form_of_education', 'Не указано')}\n"
            f"• Курс: {data.get('course', 'Не указано')}\n"
            f"• Группа: {data.get('group', 'Не указано')}\n"
            f"• Год начала обучения: {data.get('start_year', 'Не указано')}\n"
            f"• Год окончания программы обучения: {data.get('end_year', 'Не указано')}\n"
            f"• Телефон: {data.get('phone', 'Не указано')}\n"
            f"• Email: {data.get('email', 'Не указано')}\n"
        )
        moderator_confirm_form = RegisterNewUserInlineButtons.get_inline_keyboard(
            user_id=callback.from_user.id 
        )
        send_params = {
                "chat_id": config.moderator_chat_id,
                "text": moderator_message,
                "reply_markup": moderator_confirm_form,
                "message_thread_id": 45
            }
        await bot.send_message(**send_params)
        await callback.message.edit_text(text = LEXICON_TEXT["registration_end"])
        await state.clear()
    elif callback.data.startswith("change_registration_form"):
        await callback.message.edit_text(text = LEXICON_TEXT["registration_edit"], reply_markup = change_registration_form)
        await state.set_state(EditRegistrationForm.start)
    else:
        await callback.message.answer(
            text = LEXICON_TEXT["registration_edit"]
        )

@user_router.callback_query(StateFilter(EditRegistrationForm.start))
async def choice_edit(callback:CallbackQuery, state: FSMContext):
    """
    Обрабатываем нажатие на кнопки изменить данные
    """
    if callback.data.startswith("full_name"):
        await callback.message.edit_text(text=LEXICON_TEXT["registration_edit_full_name"])
        await state.set_state(EditRegistrationForm.edit_full_name)
    elif callback.data.startswith("institute"):
        await callback.message.edit_text(text=LEXICON_TEXT["registration_edit_institute"])
        await state.set_state(EditRegistrationForm.edit_institute)
    elif callback.data.startswith("direction"):
        await callback.message.edit_text(text=LEXICON_TEXT["registration_edit_direction"])
        await state.set_state(EditRegistrationForm.edit_direction)
    elif callback.data.startswith("form_of_education"):
        await callback.message.edit_text(text=LEXICON_TEXT["registration_edit_form_of_education"])
        await state.set_state(EditRegistrationForm.edit_form_of_education)
    elif callback.data.startswith("course"):
        await callback.message.edit_text(text=LEXICON_TEXT["registration_edit_course"])
        await state.set_state(EditRegistrationForm.edit_course)
    elif callback.data.startswith("group"):
        await callback.message.edit_text(text=LEXICON_TEXT["registration_edit_group"])
        await state.set_state(EditRegistrationForm.edit_group)
    elif callback.data.startswith("start_year"):
        await callback.message.edit_text(text=LEXICON_TEXT["registration_edit_start_year"])
        await state.set_state(EditRegistrationForm.edit_start_year)
    elif callback.data.startswith("end_year"):
        await callback.message.edit_text(text=LEXICON_TEXT["registration_edit_end_year"])
        await state.set_state(EditRegistrationForm.edit_end_year)
    elif callback.data.startswith("phone_number"):
        await callback.message.edit_text(text=LEXICON_TEXT["registration_edit_phone_number"])
        await state.set_state(EditRegistrationForm.edit_phone_number)
    else:
        await callback.message.edit_text(text=LEXICON_TEXT["registration_edit_email"])
        await state.set_state(EditRegistrationForm.edit_email)

async def show_updated_form(message: Message, state: FSMContext):
    """Показываем обновленную анкету"""
    data = await state.get_data()
    await message.answer("✅ Анкета успешно заполнена!\nПодтвердите данные или выберите что вы хотите изменить\n\n"
                         f"ФИО: {data.get('full_name', 'Не указано')}\n"
                         f"Структурное подразделение обучения: {data.get('institute', 'Не указано')}\n"
                         f"Направление: {data.get('direction', 'Не указано')}\n"
                         f"Форма обучения: {data.get('form_of_education', 'Не указано')}\n"
                         f"Курс: {data.get('course', 'Не указано')}\n"
                         f"Группа: {data.get('group', 'Не указано')}\n"
                         f"Год начала обучения: {data.get('start_year', 'Не указано')}\n"
                         f"Год окончания программы обучения: {data.get('end_year', 'Не указано')}\n"
                         f"Телефон: {data.get('phone', 'Не указано')}\n"
                         f"Email: {message.text}\n", reply_markup=confirm_registration_form)
    await state.set_state(RegistrationFormStates.registration_end)

@user_router.message(StateFilter(EditRegistrationForm.edit_full_name))
async def edit_full_name(message:Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer("Данные изменены")
    await show_updated_form(message, state)

@user_router.message(StateFilter(EditRegistrationForm.edit_institute))
async def edit_institute(message:Message, state: FSMContext):
    await state.update_data(institute=message.text)
    await message.answer("Данные изменены")
    await show_updated_form(message, state)

@user_router.message(StateFilter(EditRegistrationForm.edit_direction))
async def edit_direction(message:Message, state: FSMContext):
    await state.update_data(direction=message.text)
    await message.answer("Данные изменены")
    await show_updated_form(message, state)

@user_router.message(StateFilter(EditRegistrationForm.edit_form_of_education))
async def edit_form_of_education(message:Message, state: FSMContext):
    await state.update_data(form_of_education=message.text)
    await message.answer("Данные изменены")
    await show_updated_form(message, state)

@user_router.message(StateFilter(EditRegistrationForm.edit_course))
async def edit_course(message:Message, state: FSMContext):
    await state.update_data(course=message.text)
    await message.answer("Данные изменены")
    await show_updated_form(message, state)

@user_router.message(StateFilter(EditRegistrationForm.edit_group))
async def edit_groupe(message:Message, state: FSMContext):
    await state.update_data(groupe=message.text)
    await message.answer("Данные изменены")
    await show_updated_form(message, state)

@user_router.message(StateFilter(EditRegistrationForm.edit_start_year))
async def edit_start_year(message:Message, state: FSMContext):
    await state.update_data(start_year=message.text)
    await message.answer("Данные изменены")
    await show_updated_form(message, state)

@user_router.message(StateFilter(EditRegistrationForm.edit_end_year))
async def edit_end_year(message:Message, state: FSMContext):
    await state.update_data(end_year=message.text)
    await message.answer("Данные изменены")
    await show_updated_form(message, state)

@user_router.message(StateFilter(EditRegistrationForm.edit_phone_number))
async def edit_phone_number(message:Message, state: FSMContext):
    await state.update_data(phone_number=message.text)
    await message.answer("Данные изменены")
    await show_updated_form(message, state)

@user_router.message(StateFilter(EditRegistrationForm.edit_email))
async def edit_email(message:Message, state: FSMContext):
    await state.update_data(email=message.text)
    await message.answer("Данные изменены")
    await show_updated_form(message, state)

@user_router.message(F.text == LEXICON_USER_KEYBOARD['submit_application'],StateFilter(default_state))
async def aplication_start(message: Message, state: FSMContext):
    await message.answer("Давайте заполним заявку. Введите название мероприятия. Лексикон")
    await state.set_state(Application.event)

@user_router.callback_query(StateFilter(Application.event))
async def name_of_event_sent(callback: CallbackQuery, state: FSMContext):
    await callback.data

@user_router.message(F.text == LEXICON_USER_KEYBOARD['my_tyuiu_coins'],StateFilter(default_state))
async def tyuiu_coins_start(message: Message, state: FSMContext):
    await message.answer(text = LEXICON_TEXT["balance"])

@user_router.message(F.text == LEXICON_USER_KEYBOARD['catalog_of_rewards'],StateFilter(default_state))
async def catalog_start(message: Message, state: FSMContext):
    await message.answer("Здась будет каталог. Лексикон")

@user_router.message(F.text == LEXICON_USER_KEYBOARD['agreement_of_contest'],StateFilter(default_state))
async def aplication_start(message: Message, state: FSMContext):
    await message.answer("ДЗдесь будет положение конкурса. Лексикон")

@user_router.message(F.text == LEXICON_USER_KEYBOARD['support'],StateFilter(default_state))
async def aplication_start(message: Message, state: FSMContext):
    await message.answer("Это поддержка. Лексикон")

    

