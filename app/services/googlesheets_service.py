from typing import Dict, Any, Optional
import httpx
from ..config import config
import time

class GoogleSheetsService:
    """Сервис для работы с Google Apps Script (Google Sheets backend)"""

    def __init__(self) -> None:
        self.url = config.apps_script_url
        self.secret = config.google_secret_key
        self._catalog_cache: Optional[Dict[str, Any]] = None
        self._catalog_cache_time: float = 0
        self.CACHE_TTL = 300  # 5 минут
        
        if not self.url or not self.secret:
            raise ValueError("Не заданы обязательные переменные окружения:" \
            "APPS_SCRIPT_URL, GOOGLE_SECRET_KEY")
    
    async def _make_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Асинхронный базовый метод с поддержкой редиректов Google Apps Script"""

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            follow_redirects=True,           # Следовать за редиректами
            max_redirects=5,                 # Макс 5 редиректов
            headers={
                "User-Agent": "Tyuiumnichka/1.0",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        ) as session:
            try:
                response = await session.post(self.url, json=payload)
                response.raise_for_status()
                
                try:
                    result = response.json()
                    return result
                except ValueError:
                    return {"success": False, "error": "Некорректный ответ от сервера"}
                    
            except httpx.TimeoutException:
                return {"success": False, "error": "Таймаут запроса к Google Sheets"}
            except httpx.HTTPStatusError as e:
                return {"success": False, "error": f"HTTP {e.response.status_code}"}
            except Exception as e:
                return {"success": False, "error": f"Ошибка: {e}"}
    
    async def add_participant_async(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Добавляет участника после регистрации"""

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
            }
        }
        
        result = await self._make_request(payload)
        
        if result.get("success"):
            row = result.get("row")
            return {"success": True, "row": row, "tg_id": tg_id}
        
        error = result.get("error") or result.get("message") or "Неизвестная ошибка"
        return {"success": False, "error": error}

    async def add_event_application_async(self, data: Dict[str, Any], sheet_name: str) -> Dict[str, Any]:
        """
        Добавляет заявку на получение ТИУкоинов в соотвествующий лист направления внеучебной деятельности
        """

        payload = {
            "secret": self.secret,
            "type": "new_event_application",
            "data": {"sheet_name": sheet_name, **data}
        }
        return await self._make_request(payload)

    async def update_application_status_async(self, sheet_name: str, row_id: int, status: str, moderator: str) -> Dict[str, Any]:
        """Обновляет статус заявки на получение ТИУкоинов"""

        payload = {
            "secret": self.secret,
            "type": "update_application_status",
            "data": {
                "sheet_name": sheet_name, "row_id": row_id, 
                "status": status, "moderator": moderator
            }
        }
        return await self._make_request(payload)
    
    async def approve_application_async(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Одобрение заявки на получение ТИУкоинов(изменение статуса, Начисление ТИУкоинов"""

        payload = {
            "secret": self.secret,
            "type": "approve_application",
            "data": {
                "sheet_name": data["sheet_name"],
                "row_id": data["row_id"],
                "status": data["status"],
                "moderator": data["moderator"],
                "tg_id": data["tg_id"],
                "tiukoins": data["tiukoins"]
            }
        }
        return await self._make_request(payload)


    async def update_tiukoins_async(self, sheet_name: str, row_id: int, tiukoins: str) -> Dict[str, Any]:
        """
        Обновление ТИУкоинов при введении коэффицента повторяемости
        """

        payload = {
            "secret": self.secret,
            "type": "update_tiukoins", 
            "data": {
                "sheet_name": sheet_name,
                "row_id": row_id,
                "tiukoins": tiukoins
            }
        }
        return await self._make_request(payload)

    def _get_cached_catalog(self) -> Optional[Dict[str, Any]]:
        """Проверяет кэш каталога"""

        if (self._catalog_cache is None or
            time.time() - self._catalog_cache_time > self.CACHE_TTL):
            return None
        return self._catalog_cache

    async def get_catalog_items_async(self) -> Dict[str, Any]:
        """Возвращает каталог с автоматическим кэшированием"""

        cached = self._get_cached_catalog()
        if cached:
            return cached
        
        payload = {
            "secret": self.secret,
            "type": "get_catalog_items",
            "data": {}
        }
        catalog = await self._make_request(payload)
        self._catalog_cache = catalog
        self._catalog_cache_time = time.time()
        return catalog

    async def get_item_name_by_id_async(self, item_id: str) -> str:
        """Название предмета по ID из кэша"""

        catalog = await self.get_catalog_items_async() 
        for item in catalog.get("items", []):
            if item["id"] == item_id:
                return item["name"]
        return f"ID_{item_id[:8]}"

    async def invalidate_catalog_cache_async(self):
        """Принудительно обновить кэш  (не используется)"""

        self._catalog_cache = None
        print("🗑️ Кэш каталога сброшен!")

    async def purchase_item_async(self, tg_id: int, item_id: str, full_name: str, order_date: str = None) -> Dict[str, Any]:
        """
        Покупка поощрения пользователем (Списывание ТИУкоинов, создание заявки, -1 кол-во поощрения)
        """

        payload = {
            "secret": self.secret,
            "type": "purchase_item",
            "data": {
                "tg_id": tg_id,
                "item_id": item_id,
                "full_name": full_name,
                "order_date": order_date 
            }
        }
        return await self._make_request(payload)

    async def update_reward_status_async(self, request_id: int, status: str, moderator: str) -> Dict[str, Any]:
        """Обновление статуса выдачи поощрения"""

        payload = {
            "secret": self.secret,
            "type": "update_reward_status",
            "data": {
                "request_id": request_id,
                "status": status,
                "moderator": f"@{moderator}"
            }
        }
        return await self._make_request(payload)
    
    async def cancel_reward_purchase_async(self, tg_id: int, item_id: str, amount: float | int) -> Dict[str, Any]:
        """Отклонение заявки на выдачу поощрения (Возврат ТИУкоинов, изменение статуса)"""

        payload = {
            "secret": self.secret,
            "type": "cancel_reward_purchase",
            "data": {
                "tg_id": tg_id,
                "item_id": item_id,
                "amount": float(amount)
            }
        }
        return await self._make_request(payload)

    async def add_tiukoins_async(self, tg_id: int, amount: int) -> Dict[str, Any]:
        """Добавление ТИУкоинов"""

        payload = {
            "secret": self.secret,
            "type": "add_tiukoins",
            "data": {"tg_id": tg_id, "amount": amount}
        }
        return await self._make_request(payload)

    async def refund_tiukoins_async(self, tg_id: int, amount: int) -> Dict[str, Any]:
        """Возврат ТИУкоинов"""

        payload = {
            "secret": self.secret,
            "type": "refund_tiukoins",
            "data": {"tg_id": tg_id, "amount": amount}
        }
        return await self._make_request(payload)
    
    async def deduct_tiukoins_async(self, tg_id: int, amount: int) -> Dict[str, Any]:
        """Списание ТИУКоинов"""

        payload = {
            "secret": self.secret,
            "type": "deduct_tiukoins",
            "data": {"tg_id": tg_id, "amount": amount}
        }
        return await self._make_request(payload)
    
    async def delete_user_by_tg_id_async(self, tg_id: int) -> Dict[str, Any]:
        """Удаление пользователя по tg_id"""

        payload = {
            "secret": self.secret,
            "type": "delete_user",
            "data": {"tg_id": tg_id}
        }
        return await self._make_request(payload)

    async def clear_all_user_data_async(self) -> Dict[str, Any]:
        """Полная очистка системы (пользователи+заявки+выдача поощрений)"""

        payload = {
            "secret": self.secret,
            "type": "clear_all_data",
            "data": {}
        }
        return await self._make_request(payload)

# Глобальный экземпляр
googlesheet_service = GoogleSheetsService()
