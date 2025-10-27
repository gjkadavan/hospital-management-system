import pytest
from backend.validators import (
    validate_name,
    validate_phone,
    validate_positive_int,
    validate_amount,
    validate_datetime,
)

def test_validate_name():
    assert validate_name("Alice")
    assert validate_name("Dr. John Smith")
    assert not validate_name("")
    assert not validate_name("<script>hack</script>")

def test_validate_phone():
    assert validate_phone("555-1234")
    assert validate_phone("+1 (555) 555-5555")
    assert not validate_phone("bad!!phone##")

def test_validate_positive_int():
    assert validate_positive_int(0)
    assert validate_positive_int("10")
    assert not validate_positive_int(-1)
    assert not validate_positive_int("nope")

def test_validate_amount():
    assert validate_amount("0")
    assert validate_amount("25.50")
    assert not validate_amount("-1")
    assert not validate_amount("abc")

def test_validate_datetime_format():
    assert validate_datetime("2025-10-24 13:30") is True
    assert validate_datetime("2025-10-24T13:30") is False
    assert validate_datetime("not-a-date") is False
