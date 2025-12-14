# time_parser/tests/test_specific_dates.py
"""Tests for specific_dates_with_times parser module."""
import pytest
from datetime import datetime, UTC
from time_parser.parsers.specific_dates_with_times import parse

@pytest.mark.parametrize("input_text,expected_hour,expected_minute,expected_weekday_idx", [
    ("By 9 AM on Monday", 9, 0, 0),       # Mon=0
    ("at 5pm on Friday", 17, 0, 4),       # Fri=4
    ("9:30 AM Tuesday", 9, 30, 1),        # Tue=1
    ("by 3 pm on next wednesday", 15, 0, 2), # Wed=2
    ("9 AM Monday", 9, 0, 0),             # Implicit prepositions
    ("Monday at 9am", 9, 0, 0),           # Reversed order
    ("BY 9 AM ON MONDAY", 9, 0, 0),       # Case insensitivity
    ("By 9 AM on Monday!", 9, 0, 0),      # Punctuation
])
def test_specific_dates_parsing(input_text, expected_hour, expected_minute, expected_weekday_idx):
    """Test parsing of specific date and time combinations."""
    result = parse(input_text)
    
    assert result is not None, f"Failed to parse: {input_text}"
    assert isinstance(result, datetime)
    assert result.tzinfo == UTC
    
    # Check Time
    assert result.hour == expected_hour
    assert result.minute == expected_minute
    
    # Check Weekday
    assert result.weekday() == expected_weekday_idx
    
    # Check Future
    # Note: If today is Monday 9:00:01 AM and we ask for Monday 9:00 AM, it returns next week
    assert result > datetime.now(UTC)

def test_specific_dates_no_match():
    """Test inputs that should return None."""
    assert parse("hello world") is None
    assert parse("9 am tomorrow") is None # Matches relative date parser, not this one
    assert parse("monday") is None # Missing time
    assert parse("9 am") is None # Missing day
