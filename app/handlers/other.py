from aiogram import Router, F
from aiogram.types import Message

from ..filters import  UserIDFilter
from ..config import GENERAL_CHAT

from ..lexicon import LEXICON_TEXT

other_router = Router()
moder_filter = UserIDFilter()
    
@other_router.message(F.message_thread_id.not_in([GENERAL_CHAT]))
async def send_answer(message: Message):
    await message.answer(text=LEXICON_TEXT["other_answer"])