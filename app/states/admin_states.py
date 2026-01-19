from dataclasses import dataclass
from aiogram.fsm.state import State, StatesGroup

@dataclass
class NotifificationAllUsers(StatesGroup):
    waiting_for_message = State()
    bot_message_id = State()

@dataclass
class NotificationUser(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_message = State()
    bot_message_id = State()

@dataclass
class ModeratorStates(StatesGroup):
    waiting_reject_reason = State()
    waiting_edit_comment = State()
    application_id = State()
    waiting_reject_application_reason = State()
    waiting_repeatability_factor = State()
    waiting_delete_user_tg_id = State()
    waiting_delete_user_reason = State()
    waiting_accept_to_delete_all_users = State()
    deduct_tiukoins = State()
    add_tiukoins = State()