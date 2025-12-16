from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


from lexicon import LEXICON_MODERATOR_KEYBOARD

class AdminPanelInlineButtons:
    """
    Инлайн-кнопки админа вызываются при ("/menu" в админ-панели)
    """
    
    @staticmethod
    def get_inline_keyboard():
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
    def get_inline_keyboard(user_id: int):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                                [InlineKeyboardButton(text=LEXICON_MODERATOR_KEYBOARD["accept_user"],callback_data=f"accept_user_{user_id}")],
                                [InlineKeyboardButton(text=LEXICON_MODERATOR_KEYBOARD["reject_user"], callback_data=f"reject_user_{user_id}")]
                                ])
        
        return keyboard
    
class ProcessingUserApplicationInlineButtons:
    """
    Инлайн-кнопки обработки заявки пользователя
    """

    @staticmethod
    def get_inline_keyboard():
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                                [InlineKeyboardButton(text=LEXICON_MODERATOR_KEYBOARD["approve_application"],callback_data="approve_application")],
                                [InlineKeyboardButton(text=LEXICON_MODERATOR_KEYBOARD["decline_application"], callback_data="decline_application")]
                                ])
        
        return keyboard