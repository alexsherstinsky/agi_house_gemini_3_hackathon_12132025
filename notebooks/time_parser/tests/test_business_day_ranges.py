# time_parser/tests/test_business_day_ranges.py
"""Tests for business_day_ranges parser module."""
import pytest
from datetime import datetime, timedelta, UTC
from time_parser.parsers.business_day_ranges import parse

def add_business_days_reference(start_date, days):
    """Reference implementation for verification."""
    current = start_date
    added = 0
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5:
            added += 1
    return current

@pytest.mark.parametrize("input_text,days_to_add", [
    ("Within 1-2 business days", 2),
    ("in 3 business days", 3),
    ("within 1 business day", 1),
    ("In 5 Business Days", 5),
    ("within 1 - 3 business days", 3),
])
def test_business_day_ranges(input_text, days_to_add):
    """Test parsing of business day expressions."""
    before = datetime.now(UTC)
    result = parse(input_text)
    
    assert result is not None, f"Failed to parse: {input_text}"
    assert isinstance(result, datetime)
    assert result.tzinfo == UTC
    
    # Calculate expected
    # We calculate based on 'before' time. 
    # Note: If test runs exactly at midnight boundary, this might flake, 
    # but assuming standard execution speed.
    expected = add_business_days_reference(before, days_to_add)
    
    # Check date matches
    assert result.date() == expected.date()
    
    # Check time is preserved (approx equal)
    time_diff = abs((result - expected).total_seconds())
    # Allow slight variance for execution time
    assert time_diff < 5.0

def test_business_day_failures():
    """Test invalid inputs."""
    assert parse("in 2 days") is None # Missing 'business'
    assert parse("tomorrow") is None
    assert parse("within days") is None # No number
