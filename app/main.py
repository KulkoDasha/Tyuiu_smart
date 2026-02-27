import asyncio
import logging
import traceback
from pathlib import Path
import shutil
from .services import bot_logger

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import ClientTimeout

from .config import config
from .handlers import *
from .keyboards import *

logging.basicConfig(
    level=logging.getLevelName(config.log.level),
    format=config.log.format,
    style='{'
)

timeout = ClientTimeout(
    total=600,        # 10 минут на всю операцию
    connect=30,       # 30 секунд на подключение
    sock_read=600,    # 10 минут на чтение данных
    sock_connect=30
)

async def main():
    session_path = Path("session")
    if session_path.exists():
        shutil.rmtree(session_path)
        print("Старые сессии удалены")
    
    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        timeout=timeout
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
        bot_logger.log_admin_msg(
            tg_id=0,
            message=f"🚨 КРИТИЧЕСКАЯ ОШИБКА БОТА: {str(e)}\n"
                   f"Traceback:\n{traceback.format_exc()}"
        )
    finally:
        await bot.session.close()
        print("✅ Бот остановлен")

if __name__ == "__main__":
    asyncio.run(main())
