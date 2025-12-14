"""Tests for weekday_scheduling parser module."""
import pytest
from datetime import datetime, UTC
from dateutil.relativedelta import relativedelta, MO, TU, WE, TH, FR, SA, SU
from time_parser.parsers.weekday_scheduling import parse

@pytest.mark.parametrize("input_text, target_weekday", [
    ("Monday morning", 0), # 0 = Monday
    ("Friday", 4), 
    ("next Tuesday", 1),
    ("By 9 AM on Monday", 0),
])
def test_weekday_recognition(input_text, target_weekday):
    """Test that the correct weekday is identified."""
    result = parse(input_text)
    
    assert result is not None, f"Failed to parse: {input_text}"
    assert isinstance(result, datetime)
    assert result.tzinfo == UTC
    assert result.weekday() == target_weekday, f"Wrong weekday for {input_text}"

@pytest.mark.parametrize("input_text, expected_hour", [
    ("Monday morning", 9), # morning -> 9am
    ("By 9 AM on Monday", 9),
    ("Tuesday 5 PM", 17),
    ("Wednesday 2 am", 2)
])
def test_weekday_time_parsing(input_text, expected_hour):
    """Test that time modifiers are applied correctly."""
    result = parse(input_text)
    assert result is not None
    assert result.hour == expected_hour, f"Wrong hour for {input_text}"

def test_weekday_case_insensitivity():
    """Test case insensitivity."""
    res1 = parse("monday")
    res2 = parse("MONDAY")
    assert res1 is not None and res2 is not None
    assert res1.weekday() == res2.weekday()

def test_weekday_future_date():
    """Ensure the date returned is in the future."""
    # Note: If today is Monday, 'Monday' might return today if time is future,
    # or next week. The parser logic ensures next occurrence.
    result = parse("Monday")
    now = datetime.now(UTC)
    # We verify it's not in the past
    assert result >= now - relativedelta(seconds=1) # Allow for tiny execution delta
