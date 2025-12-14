# time_parser/tests/test_specific_time_deadlines.py
"""Tests for specific_time_deadlines parser module."""
import pytest
from datetime import datetime, UTC, timedelta
from time_parser.parsers.specific_time_deadlines import parse

@pytest.mark.parametrize("input_text,expected_hour,expected_min,expected_weekday", [
    ("By 9 AM on Monday", 9, 0, 0),       # Mon=0
    ("9am on Monday", 9, 0, 0),
    ("at 5:30 PM on Friday", 17, 30, 4),  # 17:30, Fri=4
    ("by 2pm Tuesday", 14, 0, 1),         # Tue=1
    ("by 9 am on monday", 9, 0, 0),       # Lowercase check
    ("9:15am on Sat", 9, 15, 5),          # Abbreviation Sat=5
])
def test_specific_deadlines(input_text, expected_hour, expected_min, expected_weekday):
    """Test parsing of specific deadline patterns."""
    result = parse(input_text)
    
    assert result is not None, f"Failed to parse: {input_text}"
    assert isinstance(result, datetime)
    assert result.tzinfo == UTC
    
    assert result.hour == expected_hour
    assert result.minute == expected_min
    assert result.weekday() == expected_weekday
    
    # Ensure result is in the future
    assert result > datetime.now(UTC)

def test_deadline_edge_cases():
    """Test edge cases specifically."""
    # 1. Punctuation
    res = parse("By 5pm on Monday!")
    assert res is not None
    assert res.hour == 17
    
    # 2. Missing minutes (handled in param test, but explicit here)
    res = parse("10 AM on Wednesday")
    assert res.hour == 10
    assert res.minute == 0

def test_invalid_inputs():
    """Test inputs that should return None."""
    assert parse("just text") is None
    assert parse("9am without day") is None
    assert parse("Monday") is None # Handled by general parser, not this one
