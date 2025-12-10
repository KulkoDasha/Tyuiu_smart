from aiogram.filters import Filter
from aiogram.types import Message
from config.config import config

class userIDFilter(Filter):
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
        Возвращает id чата модерации
        """
        return message.chat.id == config.moderator_chat_id