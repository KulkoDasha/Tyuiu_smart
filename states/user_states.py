from dataclasses import dataclass
from aiogram.fsm.state import State, StatesGroup



@dataclass
class RegistrationStates(StatesGroup):
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
    a = State()

@dataclass 
class EditRegistration(StatesGroup):
    start = State()
    edit_fio = State()
    edit_institut = State()
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
    event = State()
    date_event = State()
    place = State()
