#хендлер на другие сообщения
from aiogram import Router
from aiogram.types import Message

from filters.filters import  UserIDFilter

other_router = Router()
moder_filter = UserIDFilter()
    
@other_router.message()
async def send_answer(message: Message):
    await message.answer("Я не знаю такой команды. Лексикон")