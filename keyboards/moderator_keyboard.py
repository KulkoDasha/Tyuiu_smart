from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from lexicon import LEXICON_MODERATOR_KEYBOARD

class AdminPanelInlineButtons:
    """
    Инлайн-кнопки админа вызываются при ("/menu" в админ-панели)
    """
    @staticmethod
    def get_inline_admin_panel():
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                                [InlineKeyboardButton(text=LEXICON_MODERATOR_KEYBOARD["notification_all"],callback_data="notification_for_all")],
                                [InlineKeyboardButton(text=LEXICON_MODERATOR_KEYBOARD["notification_user"], callback_data="notification_user")]
                                ])
        
        return keyboard
    
class RegisterNewUserInlineButtons:
    """
    Инлайн-кнопки регистрации нового пользователя
    """
    @staticmethod
    def get_inline_register_new_user():
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                                [InlineKeyboardButton(text=LEXICON_MODERATOR_KEYBOARD["accept_user"],callback_data="accept_user")],
                                [InlineKeyboardButton(text=LEXICON_MODERATOR_KEYBOARD["reject_user"], callback_data="reject_user")]
                                ])
        
        return keyboard
    
class ProcessingUserApplicationInlineButtons:
    """
    Инлайн-кнопки обработки заявки пользователя
    """
    @staticmethod
    def get_inline_processing_user_application():
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                                [InlineKeyboardButton(text=LEXICON_MODERATOR_KEYBOARD["approve_application"],callback_data="approve_application")],
                                [InlineKeyboardButton(text=LEXICON_MODERATOR_KEYBOARD["decline_application"], callback_data="decline_application")]
                                ])
        
        return keyboard