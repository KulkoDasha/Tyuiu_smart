from dataclasses import dataclass
from aiogram.fsm.state import State, StatesGroup

@dataclass
class RegistrationFormStates(StatesGroup):
    """
    Состояния при регистрации
    """
    full_name = State()
    institute= State()
    direction = State()
    form_of_education = State()
    course = State()
    group = State()
    start_year = State()
    end_year = State()
    phone_number = State()
    email = State()
    registration_end = State()

@dataclass 
class EditRegistrationForm(StatesGroup):
    """
    Состояния при изменении данных
    """
    start = State()
    edit_full_name = State()
    edit_institute = State()
    edit_direction = State()
    edit_form_of_education = State()
    edit_course = State()
    edit_group = State()
    edit_start_year = State()
    edit_end_year = State()
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
