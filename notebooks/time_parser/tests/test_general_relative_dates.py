# time_parser/tests/test_general_relative_dates.py
"""Tests for general_relative_dates parser module."""
import pytest
from datetime import datetime, timedelta, UTC
from time_parser.parsers.general_relative_dates import parse
from dateutil.relativedelta import relativedelta, MO, TU, WE, TH, FR, SA, SU

@pytest.mark.parametrize("input_text,check_type,value", [
    ("tomorrow", "days", 1),
    ("next week", "weeks", 1),
    ("in 2 days", "days", 2),
    ("in 5 minutes", "minutes", 5),
    ("tomorrow.", "days", 1),  # Punctuation
    ("NEXT WEEK", "weeks", 1),  # Case sensitivity
    ("in   2   days", "days", 2), # Whitespace
])
def test_relative_offsets(input_text, check_type, value):
    """Test relative offset calculations."""
    now = datetime.now(UTC)
    result = parse(input_text)
    
    assert result is not None
    assert result.tzinfo == UTC
    
    # Allow small delta for execution time (1 second)
    diff = result - now
    
    if check_type == "days":
        assert abs(diff - timedelta(days=value)) < timedelta(seconds=5)
    elif check_type == "weeks":
        assert abs(diff - timedelta(weeks=value)) < timedelta(seconds=5)
    elif check_type == "minutes":
        assert abs(diff - timedelta(minutes=value)) < timedelta(seconds=5)

@pytest.mark.parametrize("input_text,target_hour", [
    ("Monday morning", 9),
    ("Friday afternoon", 14),
    ("Sunday evening", 18)
])
def test_weekday_context(input_text, target_hour):
    """Test weekday and time of day parsing."""
    result = parse(input_text)
    assert result is not None
    assert result.tzinfo == UTC
    assert result.hour == target_hour
    assert result.minute == 0
    assert result > datetime.now(UTC)

def test_next_friday_logic():
    """Test specific 'next friday' logic."""
    input_text = "next Friday"
    result = parse(input_text)
    assert result is not None
    assert result.weekday() == 4  # Friday is 4
    assert result > datetime.now(UTC)

def test_non_matches():
    """Test strings that should not be parsed."""
    assert parse("random text") is None
    assert parse("in the sky") is None
