import re
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

def parse_registration_form_from_message(message_text: str, user_id: int,
                            moderator_username:str, approval_date:str) -> Optional[Dict]:
    """
    Извлекает данные анкеты.
    """
    try:
        # ✅ tg_id извлекаем из параметра
        data = {"tg_id": user_id,
                "approval_date": approval_date,
                "moderator_username": moderator_username
                }
        
        # Остальные поля парсим
        fields = [
            ("full_name", "ФИО"),
            ("institute", "Структурное подразделение обучения"),
            ("direction", "Направление"),
            ("course", "Курс"),
            ("group", "Группа"),
            ("start_year", "Год начала обучения"), 
            ("end_year", "Год окончания программы обучения"), 
            ("phone", "Номер телефона"),
            ("email", "Email")
        ]
        
        found_fields = []
        for key, field_name in fields:
            value = _extract_field(message_text, field_name)
            logger.info(f"Поле '{field_name}' -> '{value}'")
            if value:
                data[key] = value
                found_fields.append(key)
        
        logger.info(f"✅ Найдено полей: {found_fields}")

        for key, field_name in fields:
            value = _extract_field(message_text, field_name)
            if value:  # Только непустые значения
                data[key] = value
        
        # ✅ Проверяем только ФИО (критичное поле)
        if not data.get("full_name"):
            logger.warning(f"Парсер: анкета без ФИО для user_id {user_id}")
            return None
            
        logger.info(f"🎯 ИТОГОВЫЕ данные: {data}")
        return data
        
    except Exception as e:
        logger.error(f"Ошибка парсинга анкеты для {user_id}: {e}")
        # даже при ошибке возвращаем хотя бы tg_id + full_name (если есть)
        return {"tg_id": user_id, "moderator_username": moderator_username, 
                 "approval_date": approval_date} if message_text else None

def _extract_field(text: str, field_name: str) -> str:
    """Улучшенный парсер"""
    try:
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
            
    except Exception as e:
        logger.error(f"Ошибка поиска '{field_name}': {e}")
    return ""