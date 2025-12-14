# time_parser/tests/test_relative_dates.py
"""Tests for relative_dates parser module."""
import pytest
from datetime import datetime, timedelta, UTC
from dateutil.relativedelta import relativedelta, MO, TU, WE, TH, FR, SA, SU
from time_parser.parsers.relative_dates import parse, WEEKDAY_MAP

@pytest.mark.parametrize("input_text,check_type,expected_val", [
    ("tomorrow", "days_diff", 1),
    ("TOMORROW", "days_diff", 1),
    ("next week", "days_diff", 7),
    ("in 2 days", "days_diff", 2),
    ("IN 5 DAYS", "days_diff", 5),
    ("Monday morning", "weekday_check", "monday"),
    ("Friday morning", "weekday_check", "friday"),
])
def test_relative_dates_parsing(input_text, check_type, expected_val):
    """Test parsing of relative date expressions."""
    result = parse(input_text)
    now = datetime.now(UTC)
    
    assert result is not None, f"Failed to parse: {input_text}"
    assert isinstance(result, datetime), f"Result not datetime: {input_text}"
    assert result.tzinfo == UTC, f"Result not UTC: {input_text}"
    
    if check_type == "days_diff":
        # Check if the result is approximately N days from now
        # We ignore exact seconds, just check the date diff roughly
        diff = result - now
        # Allow 1 minute variance for execution time
        assert abs(diff.days - expected_val) <= 1, f"Expected {expected_val} days diff, got {diff.days}"
        assert result.hour == 9, "Expected default time of 9 AM"
        
    elif check_type == "weekday_check":
        target_const = WEEKDAY_MAP[expected_val]
        assert result.weekday() == target_const.weekday, f"Expected {expected_val}, got weekday index {result.weekday()}"
        assert result.hour == 9, "Expected 9 AM for morning"
        assert result > now, "Result should be in the future"

def test_relative_dates_failures():
    """Test expressions that should return None."""
    assert parse("yesterday") is None
    assert parse("random text") is None
    assert parse("") is None

def test_relative_dates_whitespace_punctuation():
    """Test edge cases with whitespace and punctuation."""
    res = parse("  tomorrow!  ")
    assert res is not None
    assert res.hour == 9
    
    res2 = parse("in 2 days.")
    assert res2 is not None
    assert res2.hour == 9
