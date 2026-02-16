import re
from typing import Optional

class PIIMasker:
    """Сервис частичной маскировки персональных данных."""
    
    def __init__(self):
        self.patterns = {
            'full_name': r'[А-ЯЁ][А-ЯЁа-яё-]+ [А-ЯЁ][А-ЯЁа-яё-]+(?: [А-ЯЁ][А-ЯЁа-яё-]+)*',
            'email': r'[a-z]+@std\.tyuiu\.ru',
            'phone': r'\+7\d{10}',
            'group': r'[А-ЯЁа-яё\d\-()/]+',
            'direction': r'\d{2}\.\d{2}\.\d{2} [А-ЯЁа-яё ,.-]+'
        }
    
    def mask_group(self, group: str) -> str:
        """ИТ-21-1 → ИТ*1 (показывает первые/последние 3 символа)"""
        if len(group) > 6:
            return group[:3] + '*' * max(0, len(group) - 6) + group[-3:]
        return group
    
    def mask_email(self, email: str) -> str:
        """Фикс: проверка @."""
        if '@' not in email:
            return email
        
        try:
            local, domain = email.split('@', 1)
            if len(local) > 1:
                return local[0] + '*' * (len(local) - 2) + local[-1] + '@' + domain
            return email
        except (ValueError, IndexError):
            return email
    
    def mask_full_name(self, full_name: str) -> str:
        """Иванов Иван Иванович → Ива* И.И."""
        parts = full_name.strip().split()
        if len(parts) >= 2:
            # Фамилия: первые 3 символа + *
            first = parts[0][:3] + '*' if len(parts[0]) > 3 else parts[0]
            # Инициалы остальных
            rest = ' '.join([p[0] + '.' for p in parts[1:]])
            return f"{first} {rest}"
        return full_name

    def mask_phone(self, phone: str) -> str:
        """ +79831234567 → +7983******* """
        if re.fullmatch(r'\+7\d{10}', phone):
            return phone[:5] + '*' * 7
        return phone
    
    def mask_direction(self, direction: str) -> str:
        """01.02.03 Информатика → 01.02.03 И*********"""
        code, name = direction.split(' ', 1)
        masked_name = name[0] + '*' * (len(name) - 2) + name[-1] if len(name) > 2 else name
        return f"{code} {masked_name}"

# Глобальный маскировщик
pii_masker = PIIMasker()
