from typing import Dict, Any
import requests
import logging
from config.config import config

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    """
    Сервис для работы с Google Apps Script (Google Sheets backend).
    """

    def __init__(self) -> None:
        self.url = config.apps_script_url
        self.secret = config.google_secret_key
        
        if not self.url or not self.secret:
            raise ValueError("Не заданы обязательные переменные окружения:" \
            "APPS_SCRIPT_URL, GOOGLE_SECRET_KEY")
        
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent":"Tyuiumnichka/1.0",
                "Content-Type":"application/json"
            }
        )
    
    def make_request (self, payload: Dict[str,Any]) -> Dict[str,Any]:
        """
        Базовый метод отправки запросов к Apps Script.
        """

        try:
            response = self.session.post(self.url, json=payload, timeout=15)
            response.raise_for_status()

            try:
                result = response.json()
            
            except ValueError:
                logger.error("Google Sheets: не удалось распарсить JSON-ответ")
                return {"success": False, "error": "Некорректный ответ от сервера"}

            return result
        
        except requests.exceptions.Timeout:
            logger.error("Google Sheets: таймаут запроса")
            return {"success": False, "error": "Таймаут запроса к Google Sheets"}

        except requests.exceptions.RequestException as e:
            logger.error(f"Google Sheets: сетевая ошибка: {e}")
            return {"success": False, "error": f"Сетевая ошибка: {e}"}

        except Exception as e:
            logger.error(f"Google Sheets: непредвиденная ошибка: {e}")
            return {"success": False, "error": f"Непредвиденная ошибка: {e}"}
    
    def add_participant(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Добавляет нового участника в лист "Участники".
        """

        tg_id = data.get("tg_id")
        if tg_id is None:
            return {"success": False, "error": "Отсутствует tg_id"}

        payload = {
            "secret": self.secret,
            "type": "new_participant",
            "data": {
                "tg_id": int(tg_id),
                "full_name": data.get("full_name", ""),
                "institute": data.get("institute", ""),
                "direction": data.get("direction", ""),
                "form_of_education": data.get("form_of_education", ""),
                "course": data.get("course", ""),
                "group": data.get("group", ""),
                "start_year": data.get("start_year", ""),
                "end_year": data.get("end_year", ""),
                "phone": data.get("phone", ""),
                "email": data.get("email", ""),
                "tiukoins": data.get("tiukoins", 0),
                "approval_date": data.get("approval_date", ""),
                "moderator_username": data.get("moderator_username", "")
            },
        }

        logger.info(f"Google Sheets: отправка участника tg_id={tg_id}")
        result = self.make_request(payload)
        if result.get("success"):
            row = result.get("row")
            logger.info(f"Google Sheets: участник tg_id={tg_id} добавлен (row={row})")
            return {"success": True, "row": row, "tg_id": tg_id}

        error = result.get("error") or result.get("message") or "Неизвестная ошибка"
        logger.error(f"Google Sheets: ошибка добавления tg_id={tg_id}: {error}")
        return {"success": False, "error": error}
    
    def add_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Добавляет мероприятие в лист "Заявки".
        """

        tg_id = data.get("tg_id")
        if tg_id is None:
            return {"success": False, "error": "Отсутствует tg_id"}

        payload = {
            "secret": self.secret,
            "type": "new_event",
            "data": {
                "tg_id": int(tg_id),
                "event_direction": data.get("event_direction", ""),
                "event_name": data.get("event_name", ""),
                "event_date": data.get("event_date", ""),
                "event_place": data.get("event_place", ""),
                "participant_role": data.get("participant_role", ""),
                "status": data.get("status", "На рассмотрении"),
            },
        }

        logger.info(f"Google Sheets: отправка мероприятия tg_id={tg_id}")
        result = self.make_request(payload)

        if result.get("success"):
            row = result.get("row")
            logger.info(f"Google Sheets: мероприятие для tg_id={tg_id} добавлено (row={row})")
            return {"success": True, "row": row, "tg_id": tg_id}

        error = result.get("error") or result.get("message") or "Неизвестная ошибка"
        logger.error(f"Google Sheets: ошибка добавления мероприятия tg_id={tg_id}: {error}")
        return {"success": False, "error": error}


# Глобальный экземпляр сервиса
googlesheet_service = GoogleSheetsService()
