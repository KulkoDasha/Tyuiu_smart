from aiogram import Router, Bot, F
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.types import Message, Update, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from datetime import datetime
import pytz

from states.user_states import RegistrationStates, EditRegistration, Application
from keyboards.user_keyboard import AgreementInlineButtons, MenuKeyboard, ChoiceOfInstituteInlineButtons,Confirm_anketa,Change_anketa
from lexicon.user_keyboard_lexicon import LEXICON_USER_KEYBOARD
from keyboards.moderator_keyboard import RegisterNewUserInlineButtons
from config.config import config

user_router = Router()
keyboard_start = AgreementInlineButtons.get_inline_keyboard()
menu_keyboard = MenuKeyboard.get_keyboard_menu()
institute_keyboard = ChoiceOfInstituteInlineButtons.get_inline_keyboard()
change_anketa = Change_anketa.get_inline_keyboard()
confirm_anketa = Confirm_anketa.get_inline_keyboard()


ekaterinburg_tz = pytz.timezone('Asia/Yekaterinburg')

def is_valid_date(text: str) -> bool:
    """Проверяет дату в формате ДД.ММ.ГГГГ"""
    try:
        datetime.strptime(text, '%d.%m.%Y')
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
    await message.answer("Добро пожаловать...Вставить лексикон", reply_markup = keyboard_start)

@user_router.callback_query(F.data.startswith("read_the_agreement"))
async def send_the_agreement(callback: CallbackQuery):
    """
    Хендлер на обработку согласия
    """
    await callback.message.answer("Вставить согласие")
    await callback.answer()

@user_router.callback_query(F.data.startswith("give_"))
async def send_the_agreement(callback:CallbackQuery, state: FSMContext):
    """
    Хендлер на принятие согласия
    """
    await callback.message.edit_text("Вы приняли...Лексикон")
    await callback.message.answer("Начнем заполнение анкеты. Введите ваше фио")
    await state.set_state(RegistrationStates.fio)
    await callback.answer()

@user_router.callback_query(F.data.startswith("refuse_agreement"))
async def send_the_agreement(callback:CallbackQuery, state: FSMContext):
    """
    Хендлер на отказ от согласия
    """
    await callback.message.answer("Вы отказались...Лексикон")
    await callback.answer()
    
@user_router.message(Command(commands='cancel'), StateFilter(default_state))
async def process_cancel_command(message: Message):
    """
    Хендлер на отмену состояний
    """
    await message.answer(text="Отменять нечего, вы в главном меню.Вставить лексикон")
    
@user_router.message(Command(commands = 'cancel'), ~StateFilter(default_state))
async def procces_cancel_command_state(message: Message,state: FSMContext):
    """
    Хендлер на отмену состояний
    """
    await message.answer(text = "Возвращаемся в главное меню. Вставить лексикон")
    await state.clear()

@user_router.message(Command(commands='help'))
async def help_command(message: Message):
    """
    Хендлер на команду хелп
    """
    await message.answer(text = "Команда хелп. Вставить лексикон")

@user_router.message(StateFilter(RegistrationStates.fio), F.text.regexp(r'^[А-ЯЁа-яё\s]+$'))
async def fio_sent(message:Message, state: FSMContext ):
    """
    Хендлер фио ввели, запрашивается институт
    """
    await state.update_data(fio=message.text, user_id=message.from_user.id)
    await message.answer(text = "Выберите институт. Заменить лексикон", reply_markup = institute_keyboard)
    await state.set_state(RegistrationStates.institute)

@user_router.message(StateFilter(RegistrationStates.fio))
async def process_fio_incorrect(message: Message):
    """если фио некоректное"""
    await message.answer("То что вы ввели не похоже на имя. Лексикон")

@user_router.callback_query(StateFilter(RegistrationStates.institute))
async def institut_select(callback: CallbackQuery,state: FSMContext):
    """
    Выбрали институт, запрашиваем направление
    """
    if callback.data.startswith('institute_of_architecture_and_design'):
        await callback.message.edit_text(f"Вы выбрали:{LEXICON_USER_KEYBOARD['institute_of_architecture_and_design']}")
    elif callback.data.startswith('civil_engineering_institute'):
        await callback.message.edit_text(f"Вы выбрали:{LEXICON_USER_KEYBOARD['civil_engineering_institute']}")
    elif callback.data.startswith('higher_school_of_engineering'):
        await callback.message.edit_text(f"Вы выбрали:{LEXICON_USER_KEYBOARD['higher_school_of_engineering']}")
    elif callback.data.startswith('higher_school_of_digital_technologies'):
        await callback.message.edit_text(f"Вы выбрали:{LEXICON_USER_KEYBOARD['higher_school_of_digital_technologies']}")
    elif callback.data.startswith('oil_and_gas_institute'):
        await callback.message.edit_text(f"Вы выбрали:{LEXICON_USER_KEYBOARD['oil_and_gas_institute']}")
    elif callback.data.startswith('institute_of_service_and_industry_management'):
        await callback.message.edit_text(f"Вы выбрали:{LEXICON_USER_KEYBOARD['institute_of_service_and_industry_management']}")
    elif callback.data.startswith('institute_of_technology'):
        await callback.message.edit_text(f"Вы выбрали:{LEXICON_USER_KEYBOARD['institute_of_technology']}")
    else:
        await callback.message.edit_text(f"Вы выбрали:{LEXICON_USER_KEYBOARD['institute_of_correspondence_and_distance_education']}")
    await state.update_data(institute = callback.data)  
    await callback.message.answer(text = "Введите направление без цифр.Лексикон")  
    await state.set_state(RegistrationStates.direction)

@user_router.message(StateFilter(RegistrationStates.direction), F.text.regexp(r'^[А-ЯЁа-яё\s]+$'))
async def form_of_education_sent(message:Message, state:FSMContext):
    """
    Ввели направление, запрашиваем форму обучения
    """
    await state.update_data(direction = message.text)
    await message.answer(text = "Введите форму обучения (очная\заочная). Лексикон")  
    await state.set_state(RegistrationStates.form_of_education)

@user_router.message(StateFilter(RegistrationStates.direction))
async def process_from_of_education_incorrect(message:Message):
    """если направление неккоректно"""
    await message.answer("Направление некоректно. Лексикон")
    
@user_router.message(StateFilter(RegistrationStates.form_of_education), lambda message: message.text.lower() in ["очная", "заочная"])
async def form_of_education_sent(message:Message, state:FSMContext):
    """
    Ввели направление, запрашиваем курс
    """
    await state.update_data(form_of_education = message.text)
    await message.answer(text = "Введите курс. Лексикон")  
    await state.set_state(RegistrationStates.course)

@user_router.message(StateFilter(RegistrationStates.form_of_education))
async def process_from_of_education_incorrect(message:Message):
    """если форма обучения неккоректна"""
    await message.answer("форма обучения неверная. Лексикон")

@user_router.message(StateFilter(RegistrationStates.course),lambda message: message.text in ["1","2","3","4","5"])
async def course_sent(message: Message, state: FSMContext):
    """
    Ввели курс, запрашиваем группу
    """
    await state.update_data(course = message.text)
    await message.answer(text = "Введите свою группу.Лексикон") 
    await state.set_state(RegistrationStates.group) 

@user_router.message(StateFilter(RegistrationStates.course))
async def process_course_incorrect(message:Message):
    """если курс некорректен"""
    await message.answer("Курс некоректный. Лексикон")

@user_router.message(StateFilter(RegistrationStates.group))
async def groupe_sent(message: Message, state: FSMContext):
    """
    Ввели курс, запрашиваем дату начала
    """
    await state.update_data(group = message.text)
    await message.answer(text = "Введи дату начала обучения в формате ДД.ММ.ГГГГ .Лексикон")  
    await state.set_state(RegistrationStates.date_start)

@user_router.message(StateFilter(RegistrationStates.date_start),lambda message: is_valid_date(message.text))
async def date_start_sent(message: Message, state: FSMContext):
    """
    Ввели дату начала, запрашиваем дату конца
    """
    await state.update_data(date_start = message.text)
    await message.answer(text = "Введи дату конца обучения в формате ДД.ММ.ГГГГ.Лексикон")  
    await state.set_state(RegistrationStates.date_end)

@user_router.message(StateFilter(RegistrationStates.date_start))
async def process_date_start_incorrect(message:Message):
    """если дата начала неккоректна"""
    await message.answer("Дата начала неккоректна. Лексикон")

@user_router.message(StateFilter(RegistrationStates.date_end),lambda message: is_valid_date(message.text))
async def date_end_sent(message: Message, state: FSMContext):
    """
    Ввели дату конца, запрашиваем номер телефона
    """
    await state.update_data(date_end = message.text)
    await message.answer(text = "Введите номер телефона. Лексикон") 
    await state.set_state(RegistrationStates.phone_number)

@user_router.message(StateFilter(RegistrationStates.date_end))
async def process_date_end_incorrect(message:Message): 
    """если дата конца неккоректна"""
    await message.answer("Дата конца неккоректна. Лексикон")

@user_router.message(StateFilter(RegistrationStates.phone_number))
async def phone_sent(message: Message, state: FSMContext):  
    """
    Ввели телефон, запрашиваем почту
    """
    await state.update_data(phone = message.text)
    await message.answer(text = "Введите email. Лексикон")  
    await state.set_state(RegistrationStates.email)

@user_router.message(StateFilter(RegistrationStates.phone_number))
async def process_phone_incorrect(message:Message): 
    """если номер телефона неккоректен""" 
    await message.answer("Номер телефона неккоректен. Лексикон")

@user_router.message(StateFilter(RegistrationStates.email))
async def email_sent(message: Message, state: FSMContext):  
    """
    Если почта корректна, выводим итоговое сообщение
    """
    await state.update_data(email = message.text)
    data = await state.get_data()
    await message.answer("✅ Анкета успешно заполнена!Подтвердите данные или выберите что изменить\n\n"
                         f"ФИО: {data.get('fio', 'Не указано')}\n"
                         f"Институт: {data.get('institute', 'Не указано')}\n"
                         f"Направление: {data.get('direction', 'Не указано')}\n"
                         f"Форма обучения: {data.get('form_of_education', 'Не указано')}\n"
                         f"Курс: {data.get('course', 'Не указано')}\n"
                         f"Группа: {data.get('group', 'Не указано')}\n"
                         f"Дата начала: {data.get('date_start', 'Не указано')}\n"
                         f"Дата окончания: {data.get('date_end', 'Не указано')}\n"
                         f"Телефон: {data.get('phone', 'Не указано')}\n"
                         f"Email: {message.text}\n",reply_markup= confirm_anketa)
    await state.set_state(RegistrationStates.registration_end)

@user_router.message(StateFilter(RegistrationStates.email))
async def process_phone_incorrect(message:Message):  
    """если почта неккоректна"""
    await message.answer("Почта неккоректна. Лексикон")

@user_router.callback_query(StateFilter(RegistrationStates.registration_end))
async def registration_end(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Обрабатываем нажатие на кнопки отправить анкету/изменить анкету
    """
    if callback.data.startswith("save_anketa"):
        data = await state.get_data()
        utc_time = callback.message.date
        ekaterinburg_time = utc_time.astimezone(ekaterinburg_tz)
        moder_message = (
            "📋 Новая анкета на проверку\n\n"
            f"👤 Пользователь: @{callback.from_user.username or 'без username'} "
            f"(ID: {callback.from_user.id})\n"
            f"📅 Время подачи: {ekaterinburg_time.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"📝 Данные анкеты:\n"
            f"• ФИО: {data.get('fio', 'Не указано')}\n"
            f"• Институт: {data.get('institute', 'Не указано')}\n"
            f"• Направление: {data.get('direction', 'Не указано')}\n"
            f"• Форма обучения: {data.get('form_of_education', 'Не указано')}\n"
            f"• Курс: {data.get('course', 'Не указано')}\n"
            f"• Группа: {data.get('group', 'Не указано')}\n"
            f"• Дата начала: {data.get('date_start', 'Не указано')}\n"
            f"• Дата окончания: {data.get('date_end', 'Не указано')}\n"
            f"• Телефон: {data.get('phone', 'Не указано')}\n"
            f"• Email: {data.get('email', 'Не указано')}\n"
        )
        moderator_confirm_anketa = RegisterNewUserInlineButtons.get_inline_keyboard(
            user_id=callback.from_user.id 
        )
        send_params = {
                "chat_id": config.moderator_chat_id,
                "text": moder_message,
                "reply_markup": moderator_confirm_anketa,
                "message_thread_id": 45
            }
        await bot.send_message(**send_params)
        await callback.message.edit_text("Данные отправленны модераторам на проверку. Лексикон")
        await state.clear()
    elif callback.data.startswith("change_anketa"):
        await callback.message.edit_text("Выберите что изменить", reply_markup = change_anketa)
        await state.set_state(EditRegistration.start)
    else:
        await callback.message.answer(
            "Пожалуйста, ответьте:\n"
            "• «Да» - чтобы сохранить анкету\n"
            "• «Нет» - чтобы редактировать"
        )

@user_router.callback_query(StateFilter(EditRegistration.start))
async def choice_edit(callback:CallbackQuery, state: FSMContext):
    """
    Обрабатываем нажатие на кнопки изменить данные
    """
    if callback.data.startswith("fio"):
        await callback.message.answer("Введите изменнённые данные")
        await state.set_state(EditRegistration.edit_fio)
    elif callback.data.startswith("institute"):
        await callback.message.answer("Введите изменнённые данные")
        await state.set_state(EditRegistration.edit_institute)
    elif callback.data.startswith("direction"):
        await callback.message.answer("Введите изменнённые данные")
        await state.set_state(EditRegistration.edit_direction)
    elif callback.data.startswith("form_of_education"):
        await callback.message.answer("Введите изменнённые данные")
        await state.set_state(EditRegistration.edit_form_of_education)
    elif callback.data.startswith("course"):
        await callback.message.answer("Введите изменнённые данные")
        await state.set_state(EditRegistration.edit_course)
    elif callback.data.startswith("group"):
        await callback.message.answer("Введите изменнённые данные")
        await state.set_state(EditRegistration.edit_group)
    elif callback.data.startswith("date_start"):
        await callback.message.answer("Введите изменнённые данные")
        await state.set_state(EditRegistration.edit_date_start)
    elif callback.data.startswith("date_end"):
        await callback.message.answer("Введите изменнённые данные")
        await state.set_state(EditRegistration.edit_date_end)
    elif callback.data.startswith("phone_number"):
        await callback.message.answer("Введите изменнённые данные")
        await state.set_state(EditRegistration.edit_phone_number)
    else:
        await callback.message.answer("Введите изменнённые данные")
        await state.set_state(EditRegistration.edit_email)

async def show_updated_anketa(message: Message, state: FSMContext):
    """Показываем обновленную анкету"""
    data = await state.get_data()
    response = "✅ Данные обновлены! Подтвердите данные или выберите что изменить\n\n"
    response += f"ФИО: {data.get('fio', 'Не указано')}\n"
    response += f"Институт: {data.get('institute', 'Не указано')}\n"
    response += f"Направление: {data.get('direction', 'Не указано')}\n"
    response += f"Форма обучения: {data.get('form_of_education', 'Не указано')}\n"
    response += f"Курс: {data.get('course', 'Не указано')}\n"
    response += f"Группа: {data.get('group', 'Не указано')}\n"
    response += f"Дата начала: {data.get('date_start', 'Не указано')}\n"
    response += f"Дата окончания: {data.get('date_end', 'Не указано')}\n"
    response += f"Телефон: {data.get('phone', 'Не указано')}\n"
    response += f"Email: {data.get('email', 'Не указано')}\n"
    
    await message.answer(response, reply_markup=confirm_anketa)
    await state.set_state(RegistrationStates.registration_end)

@user_router.message(StateFilter(EditRegistration.edit_fio))
async def edit_fio(message:Message, state: FSMContext):
    await state.update_data(fio=message.text)
    await message.answer("Данные изменены")
    await show_updated_anketa(message, state)

@user_router.message(StateFilter(EditRegistration.edit_institute))
async def edit_institute(message:Message, state: FSMContext):
    await state.update_data(institute=message.text)
    await message.answer("Данные изменены")
    await show_updated_anketa(message, state)

@user_router.message(StateFilter(EditRegistration.edit_direction))
async def edit_direction(message:Message, state: FSMContext):
    await state.update_data(direction=message.text)
    await message.answer("Данные изменены")
    await show_updated_anketa(message, state)

@user_router.message(StateFilter(EditRegistration.edit_form_of_education))
async def edit_form_of_education(message:Message, state: FSMContext):
    await state.update_data(form_of_education=message.text)
    await message.answer("Данные изменены")
    await show_updated_anketa(message, state)

@user_router.message(StateFilter(EditRegistration.edit_course))
async def edit_course(message:Message, state: FSMContext):
    await state.update_data(course=message.text)
    await message.answer("Данные изменены")
    await show_updated_anketa(message, state)

@user_router.message(StateFilter(EditRegistration.edit_group))
async def edit_groupe(message:Message, state: FSMContext):
    await state.update_data(groupe=message.text)
    await message.answer("Данные изменены")
    await show_updated_anketa(message, state)

@user_router.message(StateFilter(EditRegistration.edit_date_start))
async def edit_date_start(message:Message, state: FSMContext):
    await state.update_data(date_start=message.text)
    await message.answer("Данные изменены")
    await show_updated_anketa(message, state)

@user_router.message(StateFilter(EditRegistration.edit_date_end))
async def edit_date_end(message:Message, state: FSMContext):
    await state.update_data(date_end=message.text)
    await message.answer("Данные изменены")
    await show_updated_anketa(message, state)

@user_router.message(StateFilter(EditRegistration.edit_phone_number))
async def edit_phone_number(message:Message, state: FSMContext):
    await state.update_data(phone_number=message.text)
    await message.answer("Данные изменены")
    await show_updated_anketa(message, state)

@user_router.message(StateFilter(EditRegistration.edit_email ))
async def edit_email(message:Message, state: FSMContext):
    await state.update_data(email=message.text)
    await message.answer("Данные изменены")
    await show_updated_anketa(message, state)

@user_router.message(F.text == LEXICON_USER_KEYBOARD['submit_application'],StateFilter(default_state))
async def aplication_start(message: Message, state: FSMContext):
    await message.answer("Давайте заполним заявку. Введите название мероприятия. Лексикон")
    await state.set_state(Application.event)

@user_router.callback_query(StateFilter(Application.event))
async def name_of_event_sent(callback: CallbackQuery, state: FSMContext):
    await callback.data

@user_router.message(F.text == LEXICON_USER_KEYBOARD['my_tyuiu_coins'],StateFilter(default_state))
async def tyuiu_coins_start(message: Message, state: FSMContext):
    await message.answer("Здесь будет функция просмотра тиукоинов. Лексикон")

@user_router.message(F.text == LEXICON_USER_KEYBOARD['catalog_of_rewards'],StateFilter(default_state))
async def catalog_start(message: Message, state: FSMContext):
    await message.answer("Здась будет каталог. Лексикон")

@user_router.message(F.text == LEXICON_USER_KEYBOARD['agreement_of_contest'],StateFilter(default_state))
async def aplication_start(message: Message, state: FSMContext):
    await message.answer("ДЗдесь будет положение конкурса. Лексикон")

@user_router.message(F.text == LEXICON_USER_KEYBOARD['support'],StateFilter(default_state))
async def aplication_start(message: Message, state: FSMContext):
    await message.answer("Это поддержка. Лексикон")

    

