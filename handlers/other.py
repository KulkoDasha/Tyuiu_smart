#хендлер на другие сообщения
from aiogram import Router, F
from aiogram.types import Message

from filters.filters import  UserIDFilter

other_router = Router()
moder_filter = UserIDFilter()
    
@other_router.message(F.message_thread_id.not_in([243]))
async def send_answer(message: Message):
    await message.answer("Я не знаю такой команды. Лексикон")