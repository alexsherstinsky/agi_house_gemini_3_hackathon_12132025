# time_parser/tests/test_business_day_ranges.py
"""Tests for business_day_ranges parser module."""
import pytest
from datetime import datetime, timedelta, UTC
from time_parser.parsers.business_day_ranges import parse

@pytest.mark.parametrize("input_text,business_days", [
    ("in 3 business days", 3),
    ("1 business day", 1),
    ("Within 1-2 business days", 2), # Uses upper bound
    ("5 business days", 5),
    ("1 - 2 business days", 2),      # Spaces in range
    ("IN 2 BUSINESS DAYS", 2),       # Case insensitive
])
def test_business_days_logic(input_text, business_days):
    """Test parsing and calculation of business days."""
    start_time = datetime.now(UTC)
    result = parse(input_text)
    
    assert result is not None, f"Failed to parse: {input_text}"
    assert result.tzinfo == UTC
    
    # Verify logic: manually count business days from start
    curr = start_time
    count = 0
    while count < business_days:
        curr += timedelta(days=1)
        if curr.weekday() < 5: # Mon-Fri
            count += 1
            
    # Compare result with manual calculation
    # We compare dates (year, month, day) to avoid microsecond race conditions
    assert result.date() == curr.date(), f"Date mismatch: Got {result.date()}, expected {curr.date()}"

def test_business_days_non_match():
    """Test that non-business day strings return None."""
    assert parse("in 3 days") is None # Missing 'business'
    assert parse("today") is None
    assert parse("business") is None
