from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

ITEM_BUTTON_NAMES = {
    "item_pencil": "✏️ Карандаш",
    "item_pen": "🖊️ Ручка",
    "item_sticker_pack": "📝 Стикерпак",
    "item_badge": "⭐ Значок",
    "item_notebook": "📓 Блокнот",
    "item_shopper": "🛍️ Шоппер",
    "item_cofer": "☕ Кофер",
    "item_cap": "🧢 Бейсболка",
    "item_sweatshirt": "👕 Свитшот",
    "item_sports_bag": "🎒 Сумка",
    "item_zodchiy": "🏊‍♂️ Зодчий",
    "item_olympia": "🏕️ Олимпия",
    "item_certificates": "📃 Сертификаты",
}

ITEM_DETAILS = {
    "item_pencil": {"title": "Карандаш с нанесением", "quantity": "100 ед.", "price": 5, "notes": "Индивидуально"},
    "item_pen": {"title": "Ручка шариковая с нанесением", "quantity": "100 ед.", "price": 10, "notes": "Индивидуально"},
    "item_sticker_pack": {"title": "Стикерпак", "quantity": "40 ед.", "price": 15, "notes": "Индивидуально"},
    "item_badge": {"title": "Значок с нанесением логотипа ТИУ", "quantity": "20 ед.", "price": 20, "notes": "Индивидуально"},
    "item_notebook": {"title": "Блокнот с нанесением А5", "quantity": "40 ед.", "price": 25, "notes": "Индивидуально"},
    "item_shopper": {"title": "Шоппер", "quantity": "20 ед.", "price": 35, "notes": "Индивидуально"},
    "item_cofer": {"title": "Кофер", "quantity": "20 ед.", "price": 40, "notes": "Индивидуально"},
    "item_cap": {"title": "Бейсболка", "quantity": "20 ед.", "price": 50, "notes": "Индивидуально"},
    "item_sweatshirt": {"title": "Свитшот унисекс", "quantity": "20 ед.", "price": 55, "notes": "Индивидуально"},
    "item_sports_bag": {"title": "Сумка спортивная", "quantity": "10 ед.", "price": 60, "notes": "Индивидуально"},
    "item_zodchiy": {"title": "СОЦ «Зодчий»", "quantity": "—", "price": 70, "notes": "Курс из нескольких посещений индивидуально"},
    "item_olympia": {"title": "СОБ «Олимпия»", "quantity": "—", "price": 600, "notes": "Совокупность баллов участников для группового посещения"},
    "item_certificates": {"title": "Сертификаты от партнеров", "quantity": "—", "price": "90-300+", "notes": "Индивидуально или совокупность баллов участников"},
}

class ItemKeyboard:
    """
    Каталог поощрений
    """
    
    async def create_table_keyboard(self) -> InlineKeyboardMarkup:
        keyboard = []
        
        keyboard.append([
            InlineKeyboardButton(text="Продукция", callback_data="ignore"),
            InlineKeyboardButton(text="Кол-во", callback_data="ignore"),
            InlineKeyboardButton(text="Цена", callback_data="ignore"),
        ])
        
        keyboard.append([
            InlineKeyboardButton(text="СУВЕНИРНАЯ ПРОДУКЦИЯ", callback_data="ignore")
        ])

        souvenir_items = list(ITEM_BUTTON_NAMES.items())[:10]
        for item_key, item_name in souvenir_items:
            data = ITEM_DETAILS[item_key]
            keyboard.append([
                InlineKeyboardButton(text=item_name, callback_data=f"view_item_{item_key}"),
                InlineKeyboardButton(text=data["quantity"], callback_data=f"quantity_{item_key}"),
                InlineKeyboardButton(text=str(data["price"]), callback_data=f"price_{item_key}"),
            ])
   
        keyboard.append([
            InlineKeyboardButton(text="НЕМАТЕРИАЛЬНЫЕ ПООЩРЕНИЯ", callback_data="ignore")
        ])
       
        intangible_items = list(ITEM_BUTTON_NAMES.items())[10:]
        for item_key, item_name in intangible_items:
            data = ITEM_DETAILS[item_key]
            price_text = str(data["price"]) if isinstance(data["price"], int) else data["price"]
            keyboard.append([
                InlineKeyboardButton(text=item_name, callback_data=f"view_item_{item_key}"),
                InlineKeyboardButton(text=data["quantity"], callback_data=f"quantity_{item_key}"),
                InlineKeyboardButton(text=price_text, callback_data=f"price_{item_key}"),
            ])
        
        keyboard.append([
            InlineKeyboardButton(text="❌ Закрыть", callback_data="cancel_item")
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def show_item_details(callback: CallbackQuery):
    """
    Показывает детальную информацию о товаре
    """
    item_key = callback.data.replace("view_item_", "")
    
    if item_key in ITEM_DETAILS:
        details = ITEM_DETAILS[item_key]
        
        await callback.message.edit_text(
            f"🎁 <b>Информация о товаре</b>\n"
            f"<b>Название:</b> {details['title']}\n"
            f"<b>Количество:</b> {details['quantity']}\n"
            f"<b>Цена:</b> {details['price']} ТИУкоинов\n"
            f"<b>Примечание:</b> {details['notes']}\n\n"
            f"<i>Хотите выбрать этот товар?</i>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Выбрать этот товар", callback_data=f"select_item_{item_key}")],
                [InlineKeyboardButton(text="⬅️ Назад к таблице", callback_data="show_table"),
                    InlineKeyboardButton(text="❌ Закрыть", callback_data="close_all")]
            ])
        )
    else:
        await callback.answer("❌ Товар не найден", show_alert=True)
    
    await callback.answer()

async def show_purchase_confirmation(callback: CallbackQuery):
    """
    Подтверждение покупки
    """
    item_key = callback.data.replace("select_item_", "")
    
    if item_key in ITEM_DETAILS:
        details = ITEM_DETAILS[item_key]
        price = details["price"]
        
        await callback.message.edit_text(
            f"✅ <b>Подтверждение покупки</b>\n\n"
            f"<b>Товар:</b> {details['title']}\n"
            f"<b>Цена:</b> {price} ТИУкоинов\n\n"
            f"<i>Подтверждаете списание {price} ТИУкоинов?</i>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Да, подтверждаю", 
                        callback_data=f"confirm_purchase_{item_key}"
                    ),
                    InlineKeyboardButton(
                        text="❌ Нет, отменить", 
                        callback_data=f"cancel_purchase_{item_key}"
                    )
                ]
            ])
        )
    else:
        await callback.answer("❌ Ошибка: товар не найден", show_alert=True)
    
    await callback.answer()