from dataclasses import dataclass
from aiogram.fsm.state import State, StatesGroup

@dataclass
class RegistrationFormStates(StatesGroup):
    """Состояния при регистрации пользователя"""

    full_name = State()
    institute= State()
    direction = State()
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
    Состояния при изменении данных в регистрационной анкете
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
class EventApplicationStates(StatesGroup):
    """
    Состояния при заполнения заявки на получение ТИУкоинов
    """

    event_direction = State()
    name_event = State()
    date_event = State()
    event_location = State()
    role_at_the_event = State()
    supporting_manerial = State()
    application_process_end = State()

@dataclass
class ChangeEventApplicationStates(StatesGroup):
    """Состояния при изменении заявки на получение ТИУкоинов"""

    start = State()
    change_event_direction = State()
    change_name_event = State()
    change_date_event = State()
    change_event_location = State()
    change_role_at_the_event = State()
    change_materials_of_the_event = State()
    

@dataclass
class SupportStates(StatesGroup):
    """Состояния при нажатии на кнопку поддержки"""

    support_start = State()
    support_write_moderator = State()
    support_choice_direction = State()
    support_feedback = State()
    support_error = State()
    
@dataclass
class CatalogOfRewardsStates(StatesGroup):
    """Состояния при просмотре Каталога поощрений"""

    catalog_of_rewards_start = State()
    show_item_details_state = State()
    show_purchase_confirmation_state = State()
    
@dataclass
class AboutCompetition(StatesGroup):
    """Состояния при нажатии на кнопку О конкурсе и Мои ТИУкоины"""

    about_competition_start = State()
    my_tiukoins_start = State()
    
@dataclass
class RecallAgreement(StatesGroup):
    """Состояния при отзыве согласия"""
    
    wait_answer = State()