import re
from .logger import bot_logger
from typing import Dict, Optional

def parse_registration_form_from_message(message_text: str, user_id: int,
                            moderator_username:str, approval_date:str) -> Optional[Dict]:
    """Извлекает данные регистрационной анкеты"""
    
    try:
        data = {"tg_id": user_id,
                "approval_date": approval_date,
                "moderator_username": moderator_username
                }
        
        fields = [
            ("full_name", "ФИО"),
            ("institute", "Структурное подразделение обучения"),
            ("direction", "Направление"),
            ("course", "Курс"),
            ("group", "Группа"),
            ("start_year", "Год начала обучения"), 
            ("end_year", "Год окончания программы обучения"), 
            ("phone_number", "Номер телефона"),
            ("email", "Email")
        ]
        
        found_fields = []
        for key, field_name in fields:
            value = _extract_field(message_text, field_name)
            if value:
                data[key] = value
                found_fields.append(key)

        for key, field_name in fields:
            value = _extract_field(message_text, field_name)
            if value:
                data[key] = value

        return data
        
    except Exception as e:
        
        # даже при ошибке возвращаем хотя бы tg_id + full_name (если есть)
        return {"tg_id": user_id, "moderator_username": moderator_username, 
                 "approval_date": approval_date} if message_text else None

def _extract_field(text: str, field_name: str) -> str:
    """Улучшенный парсер"""

    # 1️⃣ • Поле: значение
    pattern = rf"•\s*{re.escape(field_name)}:\s*(.+?)(?=\n•|\n\n|\n|$)"
    match = re.search(pattern, text, re.DOTALL | re.MULTILINE | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # 2️⃣ Поле: значение
    pattern = rf"{re.escape(field_name)}:\s*(.+?)(?=\n•|\n\n|\n|$)"
    match = re.search(pattern, text, re.DOTALL | re.MULTILINE | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # 3️⃣ Любые варианты
    pattern = rf"{re.escape(field_name)}[:\s]+(.+?)(?=\n•|\n\n|\n|$)"
    match = re.search(pattern, text, re.DOTALL | re.MULTILINE | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return ""