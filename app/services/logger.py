import logging
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
from typing import Optional
from ..config.bot_config import config 
from .pii_masker import pii_masker


class BotLogger:
    """Универсальный логгер"""
    
    def __init__(self, log_config):
        self.logs_dir = Path(log_config.logs_dir)
        self.logs_dir.mkdir(exist_ok=True)
        
        self.user_logger = self._setup_logger("UserLog", "UserLog.log")
        self.moderator_logger = self._setup_logger("ModeratorLog", "ModeratorLog.log")
        self.admin_logger = self._setup_logger("AdminLog", "AdminLog.log")
    
    def _setup_logger(self, name: str, filename: str) -> logging.Logger:
        logger = logging.getLogger(name)
        logger.propagate = False
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        handler = TimedRotatingFileHandler(
            self.logs_dir / filename,
            when='midnight', interval=1, backupCount=30, encoding='utf-8'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
    
    def log_user_msg(self, tg_id: int, message: str, level: str = "INFO") -> None:
        """Бизнес-события пользователей"""
        full_msg = f"tg_id={tg_id} | {message}"
        self._log_message(self.user_logger, full_msg, level)
    
    def log_moderator_msg(self, tg_id: int, message: str, level: str = "INFO") -> None:
        """Модераторские действия"""
        full_msg = f"tg_id={tg_id} | {message}"
        self._log_message(self.moderator_logger, full_msg, level)
    
    def log_admin_msg(self, tg_id: int, message: str, level: str = "INFO") -> None:
        """Админские действия"""
        full_msg = f"tg_id={tg_id} | {message}"
        self._log_message(self.admin_logger, full_msg, level)
    
    def _log_message(self, logger: logging.Logger, message: str, level: str):
        level = level.upper()
        getattr(logger, level.lower())(message)


bot_logger = BotLogger(config.log)
