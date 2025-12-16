from dataclasses import dataclass
from aiogram.fsm.state import State, StatesGroup

@dataclass
class RegistrationStates(StatesGroup):
    """
    Состояния при регистрации
    """
    fio = State()
    institute= State()
    direction = State()
    form_of_education = State()
    course = State()
    group = State()
    date_start = State()
    date_end = State()
    phone_number = State()
    email = State()
    registration_end = State()

@dataclass 
class EditRegistration(StatesGroup):
    """
    Состояния при изменении данных
    """
    start = State()
    edit_fio = State()
    edit_institute = State()
    edit_direction = State()
    edit_form_of_education = State()
    edit_course = State()
    edit_group = State()
    edit_date_start = State()
    edit_date_end = State()
    edit_phone_number = State()
    edit_email = State()

@dataclass
class Application(StatesGroup):
    """
    Состояния при заполнения заявки
    """
    event = State()
    date_event = State()
    place = State()
