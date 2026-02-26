from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import *

from ..lexicon import LEXICON_USER_KEYBOARD

class DynamicCatalogKeyboard:
    @staticmethod
    async def create_table_keyboard(session: AsyncSession) -> InlineKeyboardMarkup:
        """Создает динамическую таблицу поощрений из БД и возвращает клавиатуру"""

        try:
            catalog = select(Catalog_of_reward).order_by(Catalog_of_reward.id)
            result = await session.execute(catalog)
            rewards = result.scalars().all()
            
            if not rewards:
                return InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="❌ Ошибка каталога", callback_data="error_catalog")]
                ])
            
            keyboard = []
            
            # Заголовок
            keyboard.append([
                InlineKeyboardButton(text="🎁 Поощрение", callback_data="ignore"),
                InlineKeyboardButton(text="💎 Стоимость", callback_data="ignore")
            ])
            
            # Товары (2 колонки)
            for item in rewards:
                keyboard.append([
                    InlineKeyboardButton(
                        text=item.name_of_reward[:20] + "..." if len(item.name_of_reward) > 20 else item.name_of_reward,
                        callback_data=f"view_item_{item.id}"
                    ),
                    InlineKeyboardButton(text=f"{item.price}", callback_data="ignore")
                ])
            
            # Навигация
            keyboard.append([
                InlineKeyboardButton(text="❌ Закрыть", callback_data="cancel_catalog")
            ])
            
            return InlineKeyboardMarkup(inline_keyboard=keyboard)
            
        except Exception as e:
            return InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Ошибка загрузки", callback_data="error_catalog")]
            ])

# Глобальный экземпляр
catalog_of_rewards = DynamicCatalogKeyboard()

