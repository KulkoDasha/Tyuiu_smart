from dataclasses import dataclass
from dotenv import load_dotenv
from pathlib import Path
import os
from .moderator_topics import *
    
@dataclass
class LogSettings:
    level: str    
    format: str  
    logs_dir: str = "logs"

@dataclass
class TgBot:
    token: str

@dataclass
class Config:
    bot: TgBot
    log: LogSettings
    moderator_chat_id: int
    admin_panel_id :None | int

def load_config(path: str | None = None) -> Config:
    """Принимает данные из .env и загружает конфиг"""

    if path is None:
        env_path = str(Path(__file__).parent.parent / ".env")
    else:
        env_path = path

    load_dotenv(dotenv_path=path, override=True)
    token = os.getenv("BOT_TOKEN")
    moderator_chat_id = os.getenv("MODERATOR_CHAT_ID")
    admin_panel_id = TOPIC_ADMIN_PANEL

    if token is None:
        raise ValueError(f"BOT_TOKEN не найден в файле {env_path}")
    
    return Config(
        bot=TgBot(token=token),
        log=LogSettings(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format=os.getenv("LOG_FORMAT", "{asctime} - {levelname} - {name} - {message}"),
        logs_dir=os.getenv("LOGS_DIR", "logs")),
        moderator_chat_id = int(moderator_chat_id),
        admin_panel_id = admin_panel_id
        )
    
config = load_config()