# time_parser/tests/test_specific_weekday_deadline.py
"""Tests for specific_weekday_deadline parser module."""
import pytest
from datetime import datetime, UTC
from time_parser.parsers.specific_weekday_deadline import parse

@pytest.mark.parametrize("input_text,expected_hour,expected_minute,expected_day_str", [
    ("By 9 AM on Monday", 9, 0, "monday"),
    ("by 5:30 pm on Friday", 17, 30, "friday"),
    ("By 10 am on Tuesday", 10, 0, "tuesday"),
    ("BY 2 PM ON WEDNESDAY", 14, 0, "wednesday"),
    ("By 11 am on Thursday.", 11, 0, "thursday"),
])
def test_specific_weekday_success(input_text, expected_hour, expected_minute, expected_day_str):
    """Test successful parsing of specific weekday deadlines."""
    result = parse(input_text)
    
    assert result is not None, f"Failed to parse: {input_text}"
    assert isinstance(result, datetime)
    assert result.tzinfo == UTC
    
    assert result.hour == expected_hour
    assert result.minute == expected_minute
    
    # Check weekday (0=Mon, 6=Sun)
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    expected_idx = days.index(expected_day_str)
    assert result.weekday() == expected_idx
    
    # Ensure it's in the future
    assert result > datetime.now(UTC)

def test_specific_weekday_failures():
    """Test inputs that should return None."""
    assert parse("By 25 PM on Monday") is None  # Invalid time
    assert parse("By 9 AM on Blursday") is None # Invalid day
    assert parse("random text") is None
    assert parse("By 9 AM") is None # Missing day
    assert parse("") is None

def test_specific_weekday_edge_cases():
    """Test edge cases."""
    # Extra spaces
    res = parse("By  9  AM  on  Monday")
    assert res is not None
    assert res.hour == 9
