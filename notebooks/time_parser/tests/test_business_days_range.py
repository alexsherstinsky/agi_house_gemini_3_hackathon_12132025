# time_parser/tests/test_business_days_range.py
"""Tests for business_days_range parser module."""
import pytest
from datetime import datetime, timedelta, UTC
from time_parser.parsers.business_days_range import parse

@pytest.mark.parametrize("input_text,expected_business_days", [
    ("Within 1-2 business days", 2),
    ("within 3 business days", 3),
    ("WITHIN 5 BUSINESS DAYS", 5),
    ("within 1 business day", 1),
])
def test_business_days_logic(input_text, expected_business_days):
    """Test parsing and calculation of business days."""
    start_time = datetime.now(UTC)
    result = parse(input_text)
    
    assert result is not None, f"Failed to parse: {input_text}"
    assert isinstance(result, datetime)
    assert result.tzinfo == UTC
    assert result.hour == 9

    # Validate business logic manually
    # We add days one by one to start_time, skipping weekends, to verify result
    current = start_time
    added = 0
    while added < expected_business_days:
        current += timedelta(days=1)
        if current.weekday() < 5:
            added += 1
    
    # Reset time to 9am for comparison as parser sets it to 9am
    expected_date = current.replace(hour=9, minute=0, second=0, microsecond=0)
    
    # Compare (allowing match on Year-Month-Day Hour:Min)
    assert result.date() == expected_date.date()
    assert result.hour == expected_date.hour

def test_business_days_failures():
    """Test inputs that should fail."""
    assert parse("within -1 business days") is None
    assert parse("within 5 days") is None # Missing 'business'
    assert parse("random text") is None

def test_business_days_formatting():
    """Test formatting edge cases."""
    res = parse("within  2-4  business  days.")
    assert res is not None
    # Should pick upper bound 4
    # We verify roughly that it's > 2 days out
    assert res > datetime.now(UTC) + timedelta(days=3)
