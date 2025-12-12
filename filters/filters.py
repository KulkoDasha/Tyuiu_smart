from aiogram.filters import Filter
from aiogram.types import Message
from config.config import config

class UserIDFilter(Filter):
    async def  __call__ (self, message: Message) -> bool:
        """
        Проверяет в какой чат написал пользователь.
        """
        user_id = message.from_user.id
        is_not_moderator = user_id != config.moderator_chat_id
        return is_not_moderator
    
class ModeratorChatFilter(Filter):
    async def __call__ (self, message: Message) -> bool:
        """
        Проверяет, что сообщение написано в чате модераторов.
        """
        return message.chat.id == config.moderator_chat_id

class AdminChatFilter(Filter):    
    async def __call__(self, message: Message) -> bool:
        """
        Поверяет, что сообщение отправлено в теме "Админ-панель"
        в чате модераторов.
        """

        if message.chat.id != config.moderator_chat_id:
            return False
        
        if message.message_thread_id != config.admin_panel_id:
            return False
    
        return True