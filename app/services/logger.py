import logging
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
from ..config.bot_config import config 

class BotLogger:
    """
    Логгер для ведения пользовательских и модераторских логов
    """

    def __init__(self, log_config):
        self.logs_dir = Path(log_config.logs_dir)
        self.logs_dir.mkdir(exist_ok=True)
        print(f"📁 Логи: {self.logs_dir.absolute()}")

        self.user_logger = logging.getLogger("UserLog")
        self.moderator_logger = logging.getLogger("ModeratorLog")

        self.user_logger.propagate = False
        self.moderator_logger.propagate = False

        self.user_logger.setLevel(logging.DEBUG)
        self.moderator_logger.setLevel(logging.DEBUG)
        
        self.user_logger.handlers.clear()
        self.moderator_logger.handlers.clear()

        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s | %(name)s | %(message)s', 
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Правила ротации логов
        self.user_handler = TimedRotatingFileHandler(
            self.logs_dir / "UserLog.log",
            when='midnight', interval=1, backupCount=30, encoding='utf-8'
        )
        self.user_handler.setFormatter(formatter)
        self.user_logger.addHandler(self.user_handler)

        self.moderator_handler = TimedRotatingFileHandler(
            self.logs_dir / "ModeratorLog.log",
            when='midnight', interval=1, backupCount=30, encoding='utf-8'
        )
        self.moderator_handler.setFormatter(formatter)
        self.moderator_logger.addHandler(self.moderator_handler)

    def log_user_msg(self, tg_id: str, username: str, message: str, level: str = "INFO"):
        """Пользовательские логи"""
        
        full_msg = f"tg_id={tg_id} | username=@{username or 'no_username'} | {message}"
        self.user_logger.info(full_msg)

    def log_moderator_msg(self, tg_id: str, username: str, message: str, level: str = "INFO"):
        """Модераторские логи"""

        full_msg = f"tg_id={tg_id} | username=@{username or 'no_username'} | {message}"
        self.moderator_logger.info(full_msg)

# Глобальный экземпляр
bot_logger = BotLogger(config.log)
