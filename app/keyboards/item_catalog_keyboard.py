from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram import Bot
from ..services import googlesheet_service

class DynamicCatalogKeyboard:
    @staticmethod
    async def create_table_keyboard(bot: Bot = None) -> InlineKeyboardMarkup:
        """Создает динамическую таблицу из Google Sheets"""
        try:
            catalog = googlesheet_service.get_catalog_items()
            
            if not catalog.get("success"):
                return InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="❌ Ошибка каталога", callback_data="error_catalog")]
                ])
            
            items = catalog.get("items", [])
            keyboard = []
            
            # Заголовок
            keyboard.append([
                InlineKeyboardButton(text="🎁 Поощрение", callback_data="ignore"),
                InlineKeyboardButton(text="💎 Стоимость", callback_data="ignore")
            ])
            
            # Товары (3 колонки)
            for item in items:
                keyboard.append([
                    InlineKeyboardButton(
                        text=item['name'][:20] + "..." if len(item['name']) > 20 else item['name'],
                        callback_data=f"view_item_{item['id']}"
                    ),
                    InlineKeyboardButton(text=f"{item['price']}", callback_data="ignore")
                ])
            
            # Навигация
            keyboard.append([
                InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_catalog"),
                InlineKeyboardButton(text="❌ Закрыть", callback_data="cancel_catalog")
            ])
            
            return InlineKeyboardMarkup(inline_keyboard=keyboard)
            
        except Exception as e:
            print(f"❌ Keyboard error: {e}")
            return InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Ошибка загрузки", callback_data="error_catalog")]
            ])

# ✅ Глобальная переменная (для совместимости)
catalog_of_rewards = DynamicCatalogKeyboard()
