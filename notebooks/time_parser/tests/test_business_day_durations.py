# time_parser/tests/test_business_day_durations.py
"""Tests for business_day_durations parser module."""
import pytest
from datetime import datetime, timedelta, UTC
from time_parser.parsers.business_day_durations import parse

@pytest.mark.parametrize("input_text,days_offset", [
    ("in 3 working days", 3),
    ("5 business days", 5),
    ("1 business day", 1),
    ("within 1-2 business days", 2), # Expect max of range
    ("IN 3 BUSINESS DAYS", 3),       # Case insensitivity
    ("5 business days.", 5)           # Punctuation
])
def test_business_days_calculation(input_text, days_offset):
    """Test business day math."""
    start = datetime.now(UTC)
    result = parse(input_text)
    
    assert result is not None
    assert result.tzinfo == UTC
    assert result > start
    
    # Calculate expected business days manually to verify
    # This mimics the implementation logic to ensure the test passes against the logic constraint
    current = start
    count = 0
    while count < days_offset:
        current += timedelta(days=1)
        if current.weekday() < 5:
            count += 1
            
    # Allow very small delta for execution time differences
    diff = abs((result - current).total_seconds())
    assert diff < 5, f"Expected {current}, got {result}"

def test_business_day_weekend_skip():
    """Specific test to ensure weekends are skipped."""
    # This test is tricky because it depends on when it is run.
    # We verify that the result is never a Saturday or Sunday if we added days.
    # Actually, the result *could* be a Saturday if we added 0 days? But regex requires >=1.
    # The logic moves forward by days, checking if valid.
    
    # Let's test a large number that forces a weekend cross
    result = parse("5 business days")
    # 5 business days will always cross at least one weekend unless starting Monday?
    # No, Mon->Fri is 5 days. 
    # 10 business days will definitely cross a weekend.
    
    result_10 = parse("10 business days")
    assert result_10 is not None
    # The resulting day should ideally be a weekday? 
    # If we land on Saturday, we wouldn't decrement counter, so we'd move to Sunday, then Monday.
    # So the result should always be a weekday (Mon-Fri).
    assert result_10.weekday() < 5, "Result landed on a weekend"

def test_no_match():
    assert parse("in 2 days") is None # Missing 'business' keyword
    assert parse("business") is None
