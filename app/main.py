import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import shutil
from pathlib import Path

from .config import config
from .handlers import *

logging.basicConfig(
    level=logging.getLevelName(config.log.level),
    format=config.log.format,
    style='{'
)
logger = logging.getLogger(__name__)

async def main():
    session_path = Path("session")
    if session_path.exists():
        shutil.rmtree(session_path)
        print("Старые сессии удалены")
        logger.info("Старые сессии удалены")
    logger.info(f"Загружен полный токен: {config.bot.token}")
    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    dp.include_router(user_router)
    dp.include_router(moderator_router)
    dp.include_router(admin_router)
    dp.include_router(other_router)
    await bot.delete_webhook(drop_pending_updates=True) 
    await dp.start_polling(bot)
    
if __name__ == "__main__":
    asyncio.run(main())
