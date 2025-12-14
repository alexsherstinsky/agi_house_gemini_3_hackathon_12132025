"""Tests for business_day_ranges parser module."""
import pytest
from datetime import datetime, timedelta, UTC
from time_parser.parsers.business_day_ranges import parse

@pytest.mark.parametrize("input_text, days_to_add", [
    ("3 business days", 3),
    ("Within 1-2 business days", 2), # Takes max of range
    ("in 5 business days", 5),
    ("10 BUSINESS DAYS", 10), # Case insensitive
])
def test_business_days_calculation(input_text, days_to_add):
    """Test business day math logic."""
    result = parse(input_text)
    
    assert result is not None, f"Failed to parse: {input_text}"
    assert isinstance(result, datetime)
    assert result.tzinfo == UTC
    
    # Validation Logic Recreated
    now = datetime.now(UTC)
    count = 0
    check_date = now
    while count < days_to_add:
        check_date += timedelta(days=1)
        if check_date.weekday() < 5: # Mon-Fri are 0-4
            count += 1
            
    # Allow slight execution time diff
    diff = abs((result - check_date).total_seconds())
    assert diff < 5.0, f"Calculation mismatch for {input_text}"

def test_business_days_no_match():
    """Test strings that shouldn't parse."""
    assert parse("3 days") is None # Missing 'business'
    assert parse("tomorrow") is None
