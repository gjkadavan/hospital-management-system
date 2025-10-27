import re
from datetime import datetime

def sanitize_text(s: str, max_len: int = 500):
    """
    Basic sanitizer:
    - strip whitespace
    - remove naive `<tag>` style HTML
    - truncate to max_len
    """
    if s is None:
        return ""
    s = s.strip()
    s = re.sub(r"<[^>]*?>", "", s)
    if len(s) > max_len:
        s = s[:max_len]
    return s


_name_re = re.compile(r"^[A-Za-z][A-Za-z\s\.'-]{0,49}$")
def validate_name(name: str) -> bool:
    """
    Very basic name validation.
    1-50 chars. Letters, spaces, apostrophes, periods, hyphens.
    """
    if not name:
        return False
    return bool(_name_re.match(name.strip()))


phone_re = re.compile(r"^[0-9\-\+\(\)\s]{7,20}$")
def validate_phone(phone: str) -> bool:
    """
    Loose phone validation: digits, (), +, -, spaces.
    Length 7..20 chars.
    """
    if not phone:
        return False
    return bool(phone_re.match(phone.strip()))


def validate_positive_int(n) -> bool:
    """
    True if n can be cast to int and is >= 0.
    """
    try:
        n = int(n)
        return n >= 0
    except (TypeError, ValueError):
        return False


def validate_amount(val) -> bool:
    """
    Amount must be a number >= 0.
    """
    try:
        f = float(val)
        return f >= 0.0
    except (TypeError, ValueError):
        return False


def validate_datetime(dt_str: str) -> bool:
    """
    Expect "YYYY-MM-DD HH:MM"
    """
    try:
        datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        return True
    except (TypeError, ValueError):
        return False
