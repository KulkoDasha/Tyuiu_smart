import re
from datetime import datetime, date

def is_valid_fullname(fullname: str) -> bool:
    """Валидация ФИО: 2-3 слова на русском и каждое с юольшой буквы"""
    pattern = r'[А-ЯЁ][а-яё]+ [А-ЯЁ][а-яё]+(?: [А-ЯЁ][а-яё]+)?'
    return bool(re.fullmatch(pattern, fullname))


def is_valid_group(group: str) -> bool:
    """Валидация группы: русские буквы и цифры через дефис"""
    group = group.upper()
    pattern = r'[А-ЯЁ]+-\d{2}-\d{1,2}'
    return bool(re.fullmatch(pattern, group))

def is_valid_study_years(start_year: str, end_year: str) -> bool:
    """
    Валидация лет обучения: ГГГГ формат, разница 1-7 лет
    """
    try:
        start_dt = datetime.strptime(start_year, '%Y')
        end_dt = datetime.strptime(end_year, '%Y')
        
        start = start_dt.year
        end = end_dt.year
        
        if (end <= start) or (end - start < 1) or (end - start > 7):
            return False
            
        return True
        
    except ValueError:
        return False

def is_valid_phone(phone: str) -> bool:
    """Валидация номера телефона +7 и 10 цифр"""
    pattern = r'\+7\d{10}'
    return bool(re.fullmatch(pattern, phone)) 

def is_valid_email(email: str) -> bool:
    """Валидация почты: @std.tyuiu.ru"""
    pattern = r'^[a-z]+@std\.tyuiu\.ru$'
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