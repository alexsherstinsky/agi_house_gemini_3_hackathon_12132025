# time_parser/tests/test_specific_deadline_times.py
"""Tests for specific_deadline_times parser module."""
import pytest
from datetime import datetime, UTC
from time_parser.parsers.specific_deadline_times import parse

@pytest.mark.parametrize("input_text, expected_hour, expected_weekday_idx", [
    ("By 9 AM on Monday", 9, 0),       # Mon=0
    ("5 PM on Friday", 17, 4),         # Fri=4
    ("by 10:30 am on Tuesday", 10, 1), # Tue=1
    ("12 PM on Wednesday", 12, 2),     # Wed=2, 12PM is Noon
    ("12 AM on Sunday", 0, 6)          # Sun=6, 12AM is Midnight
])
def test_specific_deadlines(input_text, expected_hour, expected_weekday_idx):
    """Test extraction of time and weekday."""
    result = parse(input_text)
    
    assert result is not None, f"Failed to parse: {input_text}"
    assert result.tzinfo == UTC
    
    assert result.hour == expected_hour
    assert result.weekday() == expected_weekday_idx
    
    # Ensure it's in the future
    assert result > datetime.now(UTC)

def test_edge_cases():
    """Test variations in whitespace and formatting."""
    # Short weekday, no space in time
    res1 = parse("9AM Mon") 
    assert res1 is not None
    assert res1.hour == 9
    assert res1.weekday() == 0
    
    # Punctuation
    res2 = parse("By 5 pm on Friday.")
    assert res2 is not None
    assert res2.hour == 17
    assert res2.weekday() == 4

def test_non_matches():
    """Test inputs that shouldn't match."""
    assert parse("Hello world") is None
    assert parse("9 AM") is None # Missing weekday
    assert parse("Monday") is None # Missing time
    assert parse("By 25 PM on Monday") is None # Invalid hour regex usually catches this or int conversion
