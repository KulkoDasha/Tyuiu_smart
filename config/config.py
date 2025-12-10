from dataclasses import dataclass
from dotenv import load_dotenv
from pathlib import Path
import os
    
@dataclass
class LogSettings:
    level: str    
    format: str  

@dataclass
class TgBot:
    token: str
    
@dataclass
class Config:
    bot: TgBot
    log: LogSettings
    moderator_chat_id: int

def load_config(path: str | None = None) -> Config:
    """создает парсер(скрипт который собирает и структурирует данные), 
        считывает переменные из файла .env и заполняет их"""
    if path is None:
        env_path = str(Path(__file__).parent.parent / ".env")
    else:
        env_path = path
    load_dotenv(dotenv_path=path, override=True)
    token = os.getenv("BOT_TOKEN")
    moderator_chat_id = os.getenv("MODERATOR_CHAT_ID")
    if token is None:
        raise ValueError(f"BOT_TOKEN не найден в файле {env_path}")
    return Config(
        bot=TgBot(token=token),
        log=LogSettings(
            level=os.getenv("LOG_LEVEL", "INFO"), 
            format=os.getenv("LOG_FORMAT", "{asctime} - {levelname} - {name} - {message}"),
        ),
        moderator_chat_id = int(moderator_chat_id)
        )
    
config = load_config()