from aiogram.types import BotCommand
from aiogram import Bot

async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(command="/getmytgid", description="Узнать свой телеграмм айди"),
        BotCommand(command="/help", description="Информация о проекте"),
        BotCommand(command="/support", description="Поддержка"),
        BotCommand(command="/cancel", description="Отмена")
    ]
    await bot.set_my_commands(main_menu_commands)
