# time_parser/tests/test_business_day_ranges.py
"""Tests for business_day_ranges parser module."""
import pytest
from datetime import datetime, timedelta, UTC
from time_parser.parsers.business_day_ranges import parse

@pytest.mark.parametrize("input_text, expected_business_days", [
    ("in 3 business days", 3),
    ("within 5 business days", 5),
    ("Within 1-2 business days", 2), # Uses max
    ("1 to 2 business days", 2)
])
def test_business_day_logic(input_text, expected_business_days):
    """Test parsing and business day calculation."""
    start_time = datetime.now(UTC)
    result = parse(input_text)
    
    assert result is not None, f"Failed to parse: {input_text}"
    assert result.tzinfo == UTC
    assert result > start_time
    
    # Verify basic constraints
    # The calendar days difference should be >= business days (due to weekends)
    total_days = (result - start_time).days
    assert total_days >= expected_business_days
    
    # Result should never be on a weekend
    assert result.weekday() < 5

def test_weekend_skipping_logic():
    """Verify specifically that weekends are skipped."""
    # 5 business days from any day is at least 7 calendar days (usually), unless started on weekend
    # 10 business days is guaranteed to include 2 weekends -> 14 calendar days
    res = parse("in 10 business days")
    assert res is not None
    
    now = datetime.now(UTC)
    diff = (res - now).days
    # 10 business days = 2 weeks = 14 days
    # It might be slightly less depending on start day (e.g. starting Sunday)
    # But generally >= 12
    assert diff >= 12

def test_variations():
    """Test text variations."""
    assert parse("1 business day") is not None
    assert parse("5 BUSINESS DAYS!") is not None
    assert parse("in   2 - 4   business  days") is not None

def test_failures():
    """Test non-matching inputs."""
    assert parse("in 3 days") is None # Missing 'business'
    assert parse("tomorrow") is None
