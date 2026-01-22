import re
from .logger import bot_logger
from typing import Dict

def parse_event_application_from_message(message_text: str, user_id: int) -> Dict:
    """Парсит заявку на получение ТИУкоинов"""
    
    data = {"user_id": user_id}
    
    fields = [
        ("full_name", "ФИО"),
        ("event_direction", "Направление внеучебной деятельности"),
        ("name_of_event", "Название мероприятия"),
        ("date_of_event", "Дата проведения"),
        ("event_location", "Место проведения"),
        ("event_role", "Роль в мероприятии")
    ]
    
    row_match = re.search(r"Строка:\s*(\d+)", message_text)
    if row_match:
        data["row_id"] = int(row_match.group(1))
    
    for key, field_name in fields:
        value = _extract_field(message_text, field_name)
        if value: 
            data[key] = value

    return data

def _extract_field(text: str, field_name: str) -> str:
    """Улучшенный парсер"""
    patterns = [
        rf"•\s*{re.escape(field_name)}:\s*(.+?)(?=\n•|\n\n|\n|$)",
        rf"{re.escape(field_name)}:\s*(.+?)(?=\n•|\n\n|\n|$)"
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL | re.MULTILINE | re.IGNORECASE)
        if match: return match.group(1).strip()
    return ""
