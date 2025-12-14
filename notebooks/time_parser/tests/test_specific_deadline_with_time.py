# time_parser/tests/test_specific_deadline_with_time.py
"""Tests for specific_deadline_with_time parser module."""
import pytest
from datetime import datetime, UTC
from time_parser.parsers.specific_deadline_with_time import parse

@pytest.mark.parametrize("input_text,expected_hour,expected_minute,expected_day_idx", [
    ("By 9 AM on Monday", 9, 0, 0),
    ("by 5pm on Friday", 17, 0, 4),
    ("By 10:30 am on Tuesday", 10, 30, 1),
    ("by 2:15 pm on wednesday", 14, 15, 2),
])
def test_parsing_success(input_text, expected_hour, expected_minute, expected_day_idx):
    """Test successful parsing of deadline strings."""
    result = parse(input_text)
    assert result is not None
    assert result.tzinfo == UTC
    
    assert result.hour == expected_hour
    assert result.minute == expected_minute
    assert result.weekday() == expected_day_idx
    
    # Ensure it's in the future
    assert result > datetime.now(UTC)

def test_variations_and_edges():
    """Test variations in formatting and edge cases."""
    # No space in AM/PM, abbreviated day
    res = parse("by 5pm on Fri")
    assert res is not None
    assert res.hour == 17
    assert res.weekday() == 4
    
    # Trailing punctuation
    res2 = parse("By 9 AM on Monday!")
    assert res2 is not None
    assert res2.weekday() == 0
    
    # Whitespace
    res3 = parse("  By 9 AM   on   Monday  ")
    assert res3 is not None

def test_invalid_inputs():
    """Test inputs that should return None."""
    assert parse("hello world") is None
    assert parse("by 25:00 on Monday") is None # Invalid time
    assert parse("by 9am on Funday") is None # Invalid day
