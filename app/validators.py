import re
import unicodedata

def normalize_input(value: str) -> str:
    """Prevent Unicode homoglyph / normalization bypass attacks."""
    if value is None:
        return value
    return unicodedata.normalize('NFKC', value).strip()

def validate_username(username: str) -> bool:
    if username is None:
        return False
    try:
        username.encode('ascii')
    except UnicodeEncodeError:
        return False
    username = normalize_input(username)
    return bool(re.fullmatch(r'[A-Za-z0-9_]{3,20}', username))

def validate_email(email: str) -> bool:
    email = normalize_input(email)
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.fullmatch(pattern, email))

def validate_age(age) -> bool:
    try:
        age = int(age)
        return 18 <= age <= 100
    except (ValueError, TypeError):
        return False

def validate_salary(salary) -> bool:
    try:
        salary = float(salary)
        return 0 < salary <= 10_000_000
    except (ValueError, TypeError):
        return False

def validate_phone(phone: str) -> bool:
    phone = normalize_input(phone)
    return bool(re.fullmatch(r'\+?\d{10,13}', phone))

def validate_department(dept: str) -> bool:
    dept = normalize_input(dept)
    allowed = {'HR', 'Engineering', 'Sales', 'Finance', 'Operations'}
    return dept in allowed

def validate_export_filename(filename: str) -> bool:
    filename = normalize_input(filename)
    return bool(re.fullmatch(r'[A-Za-z0-9_\-]{1,50}', filename))