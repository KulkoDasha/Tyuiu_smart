import asyncio
import logging
import traceback
from pathlib import Path
import shutil
from .services import bot_logger

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from .config import config
from .handlers import *
from .keyboards import *

logging.basicConfig(
    level=logging.getLevelName(config.log.level),
    format=config.log.format,
    style='{'
)

async def main():
    session_path = Path("session")
    if session_path.exists():
        shutil.rmtree(session_path)
        print("Старые сессии удалены")
    
    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    dp.include_router(user_router)
    dp.include_router(moderator_router)
    dp.include_router(admin_router)
    dp.startup.register(set_main_menu)
    dp.include_router(other_router)

    try:
        print("🚀 Бот запущен!")
        await dp.start_polling(bot)
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("🛑 Остановка по Ctrl+C")
    except Exception as e:
        bot_logger.log_user_msg(
            error_msg=f"Критическая ошибка бота: {str(e)}",
            error_type="CRITICAL",
            traceback=traceback.format_exc()
        )
    finally:
        await bot.session.close()
        print("✅ Бот остановлен")

    
if __name__ == "__main__":
    asyncio.run(main())
