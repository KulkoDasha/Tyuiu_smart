from dataclasses import dataclass
from aiogram.fsm.state import State, StatesGroup

@dataclass
class NotifificationAllUsers(StatesGroup):
    waiting_for_message = State()

@dataclass
class NotificationUser(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_message = State()