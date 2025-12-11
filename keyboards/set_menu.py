from aiogram.types import BotCommand

class SetMainMenu:
    """
    Установка главного меню бота
    """
    @staticmethod
    async def set_main_menu():
        main_menu_commands = [
            BotCommand(command="/start", description="Запустить бота"),
            BotCommand(command="/menu", description="Открыть главное меню"),
            BotCommand(command="/help", description="Информация о проекте"),
            BotCommand(command="/support", description="Поддержка"),
        ]

        return main_menu_commands
