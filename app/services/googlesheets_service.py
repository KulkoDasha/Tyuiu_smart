from typing import Dict, Any
import requests
from ..config import config
from .logger import bot_logger

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

                # Логгер
                bot_logger.log_moderator_msg(
                tg_id="googlesheet_service",
                username= "googlesheet_service",
                message=f"РЕГИСТРАЦИЯ: Google Sheets: не удалось распарсить JSON-ответ"
                )

                return {"success": False, "error": "Некорректный ответ от сервера"}

            return result
        
        except requests.exceptions.Timeout:
            
            # Логгер
            bot_logger.log_moderator_msg(
            tg_id="googlesheet_service",
            username= "googlesheet_service",
            message=f"РЕГИСТРАЦИЯ: Google Sheets: таймаут запроса"
            )

            return {"success": False, "error": "Таймаут запроса к Google Sheets"}

        except requests.exceptions.RequestException as e:

            # Логгер
            bot_logger.log_moderator_msg(
            tg_id="googlesheet_service",
            username= "googlesheet_service",
            message=f"РЕГИСТРАЦИЯ: Google Sheets: сетевая ошибка: {e}"
            )

            return {"success": False, "error": f"Сетевая ошибка: {e}"}

        except Exception as e:

            # Логгер
            bot_logger.log_moderator_msg(
            tg_id="googlesheet_service",
            username= "googlesheet_service",
            message=f"РЕГИСТРАЦИЯ: Google Sheets: непредвиденная ошибка: {e}"
            )

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
                "course": data.get("course", ""),
                "group": data.get("group", ""),
                "start_year": data.get("start_year", ""),
                "end_year": data.get("end_year", ""),
                "phone_number": data.get("phone_number", ""),
                "email": data.get("email", ""),
                "tiukoins": data.get("tiukoins", 0),
                "approval_date": data.get("approval_date", ""),
                "moderator_username": data.get("moderator_username", "")
            },
        }

        # Логгер
        bot_logger.log_moderator_msg(
        tg_id="googlesheet_service",
        username= data.get("moderator_username", ""),
        message=f"РЕГИСТРАЦИЯ: Google Sheets: отправка участника tg_id={tg_id}"
        )

        result = self.make_request(payload)
        if result.get("success"):
            row = result.get("row")

            # Логгер
            bot_logger.log_moderator_msg(
            tg_id="googlesheet_service",
            username= data.get("moderator_username", ""),
            message=f"РЕГИСТРАЦИЯ: Google Sheets: участник tg_id={tg_id} добавлен (row={row})"
            )

            return {"success": True, "row": row, "tg_id": tg_id}

        error = result.get("error") or result.get("message") or "Неизвестная ошибка"

        # Логгер
        bot_logger.log_moderator_msg(
        tg_id="googlesheet_service",
        username= data.get("moderator_username", ""),
        message=f"РЕГИСТРАЦИЯ: Google Sheets: ошибка добавления tg_id={tg_id}: {error}"
        )

        return {"success": False, "error": error}
    
    def add_event_application(self, data: Dict[str, Any], sheet_name: str) -> Dict[str, Any]:
        payload = {
            "secret": self.secret,
            "type": "new_event_application",
            "data": {"sheet_name": sheet_name, **data}
        }
        return self.make_request(payload)

    def update_application_status(self, sheet_name: str, row_id: int, status: str, moderator: str) -> Dict[str, Any]:
        payload = {
            "secret": self.secret,
            "type": "update_application_status",
            "data": {
                "sheet_name": sheet_name, "row_id": row_id, 
                "status": status, "moderator": moderator
            }
        }
        return self.make_request(payload)


# Глобальный экземпляр сервиса
googlesheet_service = GoogleSheetsService()
