"""Tests for business_day_ranges parser module."""
import pytest
from datetime import datetime, timedelta, UTC
from time_parser.parsers.business_day_ranges import parse

@pytest.mark.parametrize("input_text,expected_business_days", [
    ("Within 1-2 business days", 2), # Takes upper bound
    ("in 3 business days", 3),
    ("5 working days", 5),
    ("1 business day", 1),
    ("within 2 - 4 working days", 4), # Spaced range
])
def test_business_day_ranges(input_text, expected_business_days):
    """Test parsing of business day ranges."""
    before = datetime.now(UTC)
    result = parse(input_text)
    
    assert result is not None, f"Failed to parse: {input_text}"
    assert isinstance(result, datetime)
    assert result.tzinfo == UTC
    
    # Logic verification: 
    # Calculate expected date manually to verify the 'skip weekend' logic
    current = before
    days_added = 0
    while days_added < expected_business_days:
        current += timedelta(days=1)
        if current.weekday() < 5:
            days_added += 1
            
    # result should be extremely close to 'current' (within ms execution time)
    # We strip microseconds for comparison or allow small delta
    diff = abs((result - current).total_seconds())
    assert diff < 1.0, f"Date calc mismatch. Got {result}, expected ~{current}"

def test_business_day_ranges_no_match():
    """Test inputs that should not match this cluster."""
    assert parse("in 2 days") is None # Missing 'business'
    assert parse("tomorrow") is None
