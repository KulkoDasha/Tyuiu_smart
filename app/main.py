import asyncio
import logging
import traceback
from pathlib import Path
import shutil
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import ClientTimeout

from .config import config
from .handlers import *
from .keyboards import *
from .services import bot_logger, send_log_file

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

async def scheduled_log_sender():
    """Асинхронный планировщик внутри main.py"""
    send_time = config.logs_send_time  # формат "HH:MM"
    bot_logger.log_admin_msg(
        tg_id="Отправка логов", 
        message=f"⏰ Планировщик запущен. Отправка в {send_time}"
    )
    
    last_send_date = None
    
    while True:
        try:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            current_date = now.strftime("%Y-%m-%d")
            
            # Проверяем время и чтобы не отправить дважды за день
            if current_time == send_time and current_date != last_send_date:
                bot_logger.log_admin_msg(
                    tg_id="Отправка логов", 
                    message=f"🕐 Время отправки: {current_time}"
                )
                
                # ← Запускаем send_log_file() в отдельном потоке (smtplib синхронный)
                await asyncio.get_event_loop().run_in_executor(
                    None, 
                    send_log_file
                )
                
                last_send_date = current_date
                bot_logger.log_admin_msg(
                    tg_id="Отправка логов", 
                    message=f"✅ Отправка завершена. Следующая: завтра в {send_time}"
                )
                
                await asyncio.sleep(60)  # Не отправлять повторно в ту же минуту
            else:
                await asyncio.sleep(30)  # Проверка каждые 30 секунд
                
        except Exception as e:
            bot_logger.log_admin_msg(
                tg_id="Отправка логов", 
                message=f"❌ Ошибка планировщика: {e}"
            )
            await asyncio.sleep(60)

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
        send_log_file()
        await asyncio.gather(
            dp.start_polling(bot),
            scheduled_log_sender()
        )
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
