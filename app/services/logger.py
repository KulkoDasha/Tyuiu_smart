import logging
from typing import Optional
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
from ..config.bot_config import config 

class BotLogger:
    def __init__(self, log_config):
        self.logs_dir = Path(log_config.logs_dir)
        self.logs_dir.mkdir(exist_ok=True)
        print(f"📁 Логи: {self.logs_dir.absolute()}")

        self.user_logger = logging.getLogger("UserLog")
        self.moderator_logger = logging.getLogger("ModeratorLog")
        self.error_logger = logging.getLogger("ErrorLog")

        self.user_logger.propagate = False
        self.moderator_logger.propagate = False
        self.error_logger.propagate = False

        self.user_logger.setLevel(logging.DEBUG)
        self.moderator_logger.setLevel(logging.DEBUG)
        self.error_logger.setLevel(logging.ERROR)
        
        self.user_logger.handlers.clear()
        self.moderator_logger.handlers.clear()
        self.error_logger.handlers.clear()

        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s | %(name)s | %(message)s', 
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Для дальнейшего продакшена
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

        self.error_handler = TimedRotatingFileHandler(
        self.logs_dir / "ErrorLog.log",
        when='midnight', interval=1, backupCount=30, encoding='utf-8'
        )
        self.error_handler.setFormatter(formatter)
        self.error_logger.addHandler(self.error_handler)

    def log_user_msg(self, tg_id: str, username: str, message: str, level: str = "INFO"):
        full_msg = f"tg_id={tg_id} | username=@{username or 'no_username'} | {message}"
        self.user_logger.info(full_msg)

    def log_moderator_msg(self, tg_id: str, username: str, message: str, level: str = "INFO"):
        full_msg = f"tg_id={tg_id} | username={username or 'no_username'} | {message}"
        self.moderator_logger.info(full_msg)

    def log_error(self, error_msg: str, error_type: str = "", traceback: str = ""):
        """Логирует ошибку с типом и traceback"""
        full_msg = f"{error_type} | {error_msg}"
        if traceback:
            full_msg += f"\nTraceback: {traceback}"
        self.error_logger.error(full_msg)

# ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР
bot_logger = BotLogger(config.log)
