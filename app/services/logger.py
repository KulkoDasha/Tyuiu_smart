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
        self.admin_logger = logging.getLogger("AdminLog")

        self.user_logger.propagate = False
        self.moderator_logger.propagate = False
        self.admin_logger.propagate = False

        self.user_logger.setLevel(logging.DEBUG)
        self.moderator_logger.setLevel(logging.DEBUG)
        self.admin_logger.setLevel(logging.DEBUG)
        
        self.user_logger.handlers.clear()
        self.moderator_logger.handlers.clear()
        self.admin_logger.handlers.clear()

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

        self.admin_handler = TimedRotatingFileHandler(
            self.logs_dir / "AdminLog.log",
            when='midnight', interval=1, backupCount=30, encoding='utf-8'
        )
        self.admin_handler.setFormatter(formatter)
        self.admin_logger.addHandler(self.admin_handler)

    def log_user_msg(self, tg_id, username, message: str, level: str = "INFO"):
        """Пользовательские логи"""
        
        full_msg = f"tg_id={tg_id} | username=@{username or 'no_username'} | {message}"
        
        if level.upper() == "ERROR":
            self.user_logger.error(full_msg)
        elif level.upper() == "WARNING":
            self.user_logger.warning(full_msg)
        elif level.upper() == "DEBUG":
            self.user_logger.debug(full_msg)
        else:
            self.user_logger.info(full_msg)

    def log_moderator_msg(self, tg_id, username, message: str, level: str = "INFO"):
        """Модераторские логи"""

        full_msg = f"tg_id={tg_id} | username=@{username or 'no_username'} | {message}"

        if level.upper() == "ERROR":
            self.moderator_logger.error(full_msg)
        elif level.upper() == "WARNING":
            self.moderator_logger.warning(full_msg)
        elif level.upper() == "DEBUG":
            self.moderator_logger.debug(full_msg)
        else:
            self.moderator_logger.info(full_msg)

    def log_admin_msg(self, tg_id, username, message: str, level: str = "INFO"):
        """Админские логи"""

        full_msg = f"tg_id={tg_id} | username=@{username or 'no_username'} | {message}"
        
        if level.upper() == "ERROR":
            self.admin_logger.error(full_msg)
        elif level.upper() == "WARNING":
            self.admin_logger.warning(full_msg)
        elif level.upper() == "DEBUG":
            self.admin_logger.debug(full_msg)
        else:
            self.admin_logger.info(full_msg)

# Глобальный экземпляр
bot_logger = BotLogger(config.log)
