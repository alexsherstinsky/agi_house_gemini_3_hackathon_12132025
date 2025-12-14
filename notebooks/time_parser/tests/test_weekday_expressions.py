"""Tests for weekday_expressions parser module."""
import pytest
from datetime import datetime, UTC
from dateutil.relativedelta import relativedelta
from time_parser.parsers.weekday_expressions import parse

@pytest.mark.parametrize("input_text,expected_weekday_idx,expected_hour", [
    ("Monday morning", 0, 9),      # Monday is 0, morning is 9
    ("By 9 AM on Monday", 0, 9),
    ("Friday", 4, 9),              # Friday is 4, default 9
    ("on Tuesday at 3pm", 1, 15),  # Tuesday is 1, 3pm is 15
    ("wednesday", 2, 9),           # Case check
    ("Thu 2 pm", 3, 14),           # Abbrev + time
    ("Sat evening", 5, 18),        # Day part
])
def test_weekday_expressions(input_text, expected_weekday_idx, expected_hour):
    """Test parsing of weekday expressions."""
    result = parse(input_text)
    
    assert result is not None, f"Failed to parse: {input_text}"
    assert isinstance(result, datetime)
    assert result.tzinfo == UTC
    
    # Check Weekday
    assert result.weekday() == expected_weekday_idx
    
    # Check Hour
    assert result.hour == expected_hour
    
    # Check Future logic
    # The result must be in the future (or very recently now)
    assert result > datetime.now(UTC)

def test_weekday_expressions_invalid():
    """Test non-matches."""
    assert parse("Someday") is None
    assert parse("January 1st") is None
