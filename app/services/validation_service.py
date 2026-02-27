import re
from datetime import datetime, date

def is_valid_full_name(full_name: str) -> bool:
    """Валидация ФИО: два или три слова на русском, каждое с заглавной буквы, допускается дефис"""
    full_name = full_name.strip()
    pattern = '[А-ЯЁ][А-ЯЁа-яё-]+ [А-ЯЁ][А-ЯЁа-яё-]+(?: [А-ЯЁ][А-ЯЁа-яё-]+)*'
    return bool(re.fullmatch(pattern, full_name))

def is_valid_group(group: str) -> bool:
    """Валидация группы: русские буквы, цифры, дефис, скобки и слэш"""
    group = group.strip()
    pattern = r'[А-ЯЁа-яё\d\-()/]+'
    return bool(re.fullmatch(pattern, group))

def is_valid_direction(direction: str) -> bool:
    """Валидация направления подготовки: формат XX.XX.XX Название"""
    direction = direction.strip()
    pattern = r'\d{2}\.\d{2}\.\d{2} [А-ЯЁа-яё ,.-]+'
    return bool(re.fullmatch(pattern, direction))

def is_valid_course(course: str) -> bool:
    """Валидация номера курса: цифра от 1 до 5"""
    course = course.strip()
    return bool(re.fullmatch(r'[1-5]', course))

def is_valid_study_years(start_year: str, end_year: str) -> bool:
    """Валидация срока обучения: ГГГГ формат, разница 1-5 лет"""
    start_year = start_year.strip()
    end_year = end_year.strip()
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
    """Валидация номера телефона +7 и еще 10 цифр"""
    phone_number = phone_number.strip()
    pattern = r'\+7\d{10}'
    return bool(re.fullmatch(pattern, phone_number))

def is_valid_email(email: str) -> bool:
    """Валидация почты: @std.tyuiu.ru"""
    email = email.strip()
    pattern = r'[a-z]+@std\.tyuiu\.ru'
    return bool(re.fullmatch(pattern, email))

def is_valid_event_date(event_date_str: str) -> bool:
    """Валидация даты мероприятия: формат ДД.ММ.ГГГГ, дата не в будущем и не старше одного года"""
    event_date_str = event_date_str.strip()
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
    confirmation_material = confirmation_material.strip()
    confirmation_material_lower = confirmation_material.lower()
  
    if confirmation_material_lower.startswith(('http://', 'https://')):
        return True

    file_pattern = r'.+\.(docx?|heic|heif|txt|pdf|jpe?g|png|mov|mkv|avi|mp4)$'
    return bool(re.fullmatch(file_pattern, confirmation_material_lower))