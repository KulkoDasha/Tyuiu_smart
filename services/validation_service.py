import re
from datetime import datetime, date

def is_valid_full_name(full_name: str) -> bool:
    """Валидация ФИО: от 2-х слов на русском """
    pattern = r'^[А-ЯЁ][а-яё]+(?:-[А-ЯЁа-яё]+)* [А-ЯЁ][а-яё]+(?:-[А-ЯЁа-яё]+)*(?: [А-ЯЁа-яё -]+)*$'
    return bool(re.fullmatch(pattern, full_name))

def is_valid_group(group: str) -> bool:
    """Валидация группы: русские буквы и цифры через дефис"""
    pattern = r'^[А-ЯЁа-яё\d\-()/]+$'
    return bool(re.fullmatch(pattern, group))

def is_valid_direction(direction: str) -> bool:
    """Валидация направления подготовки: формат XX.XX.XX Название"""
    pattern = r'^\d{2}\.\d{2}\.\d{2} [А-ЯЁа-яё ,.-]+$'
    return bool(re.fullmatch(pattern, direction))

def is_valid_course(course: str) -> bool:
    """Валидация номера курса: цифра"""
    return bool(re.fullmatch(r'[1-4]', course))

def is_valid_study_years(start_year: str, end_year: str) -> bool:
    """Валидация срока обучения: ГГГГ формат, разница 1-5 лет"""
    try:
        start_dt = datetime.strptime(start_year, '%Y')
        end_dt = datetime.strptime(end_year, '%Y')
        
        start = start_dt.year
        end = end_dt.year
        
        if (end <= start) or (end - start < 1) or (end - start > 5):
            return False
            
        return True
        
    except ValueError:
        return False

def is_valid_phone_number(phone_number: str) -> bool:
    """Валидация номера телефона +7 и 10 цифр"""
    pattern = r'\+7\d{10}'
    return bool(re.fullmatch(pattern, phone_number)) 

def is_valid_email(email: str) -> bool:
    """Валидация почты: @std.tyuiu.ru"""
    pattern = r'[a-z]+@std\.tyuiu\.ru'
    return bool(re.fullmatch(pattern, email)) 

def is_valid_event_date(event_date_str: str) -> bool:
    """Валидация даты мероприятия: формат ДД.ММ.ГГГГ, не старше года"""
    if not re.fullmatch(r'\d{2}\.\d{2}\.\d{4}', event_date_str):
        return False
    
    try:
        event_date = datetime.strptime(event_date_str, '%d.%m.%Y').date()
        today = date.today()
        
        return event_date <= today and (today - event_date).days <= 365
    except ValueError:
        return False


def is_valid_confirmation_material(confirmation_material: str) -> bool:
    """Валидация материала подтверждения: поддерживаемые форматы файлов или URL"""
    confirmation_material_lower = confirmation_material.lower().strip()
  
    if confirmation_material_lower.startswith(('http://', 'https://')):
        return True

    file_pattern = r'.+\.(docx?|txt|pdf|jpe?g|png|mov|mkv|avi|mp[34])$'
    return bool(re.fullmatch(file_pattern, confirmation_material_lower))