from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from ..lexicon import LEXICON_MODERATOR_KEYBOARD

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
    def get_inline_keyboard(application_id: int, user_id: int, event_role: str, db_application_id: int):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                                [InlineKeyboardButton(text=LEXICON_MODERATOR_KEYBOARD["approve_application"],callback_data=f"approve_application_{application_id}_{user_id}_{event_role}_{db_application_id}")],
                                [InlineKeyboardButton(text=LEXICON_MODERATOR_KEYBOARD["decline_application"], callback_data=f"decline_application_{application_id}_{user_id}_{event_role}_{db_application_id}")]
                                ])
        
        return keyboard

class ModeratorSupportInlineButtons:
    """
    Инлайн-кнопки поддержки
    """
    
    @staticmethod
    def get_inline_keyboard(user_id: int, message:str):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                                [InlineKeyboardButton(text=LEXICON_MODERATOR_KEYBOARD["answer_user"],callback_data=f"answer_user_{user_id}_{message}")],
                                [InlineKeyboardButton(text=LEXICON_MODERATOR_KEYBOARD["close_the_request"], callback_data=f"close_the_request_{user_id}_{message}")]
                                ])
        
        return keyboard

class ModeratorCloseRewards:
    """
    Инлайн-кнопки обработку заявки на получение поощрения
    """
    @staticmethod
    def get_inline_keyboard(request_id: int, user_id: int, item_id: str, item_price:int):
        req_str = str(request_id)
        user_str = str(user_id)
        item_str = item_id[:4] 
        item_price_str = str(item_price)
        
        full_issue = f"i_r_{req_str}_{user_str}_{item_price_str}_{item_str}"
        print (full_issue)
        
        # Автоматическое сжатие если >60 байт
        if len(full_issue) > 60:
            # Сжимаем request_id → 3 цифры
            short_req = req_str[-3:]
            full_issue = f"i_r_{req_str}_{user_str}_{item_price_str}_{item_str}"
            
            if len(full_issue) > 60:
                # Экстремально: user_id → 7 цифр
                short_user = user_str[-7:]
                full_issue = f"i_r_{req_str}_{user_str}_{item_price_str}_{item_str}"
        
        issue_data = full_issue
        reject_data = full_issue.replace("i_r_", "r_r_")
        
        print(f"🔧 '{issue_data}' ({len(issue_data)} символов)")
        
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Выдать", callback_data=issue_data),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=reject_data)
            ]
        ])
