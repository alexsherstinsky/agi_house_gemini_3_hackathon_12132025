# time_parser/tests/test_weekday_time_expressions.py
"""Tests for weekday_time_expressions parser module."""
import pytest
from datetime import datetime, UTC
from dateutil.relativedelta import relativedelta, MO, TU, WE, TH, FR, SA, SU
from time_parser.parsers.weekday_time_expressions import parse

@pytest.mark.parametrize("input_text,day_const,expected_hour", [
    ("Monday morning", MO, 9),
    ("By 9 AM on Monday", MO, 9),
    ("Tuesday afternoon", TU, 14),
    ("friday at 5pm", FR, 17),
    ("Saturday evening", SA, 18),
    ("Sunday 10:00", SU, 10),
])
def test_weekday_time_expressions(input_text, day_const, expected_hour):
    """Test parsing of weekday and time expressions."""
    result = parse(input_text)
    
    assert result is not None, f"Failed to parse: {input_text}"
    assert isinstance(result, datetime)
    assert result.tzinfo == UTC
    
    # Verify Time
    assert result.hour == expected_hour
    
    # Verify Day: Should be the *next* occurrence of that day relative to now
    now = datetime.now(UTC)
    expected_date = now + relativedelta(weekday=day_const)
    if expected_date < now:
        expected_date += relativedelta(weeks=1)
        
    # Compare only the date part (Year-Month-Day)
    assert result.date() == expected_date.date(), (
        f"Day mismatch for '{input_text}'. "
        f"Got {result.date()}, expected {expected_date.date()}"
    )

def test_weekday_edge_cases():
    """Test edge cases for case insensitivity and punctuation."""
    res = parse("  MONday   Morning!  ")
    assert res is not None
    assert res.hour == 9
    
    res_specific = parse("Wed 2pm")
    assert res_specific is not None
    assert res_specific.hour == 14

def test_invalid_weekday():
    """Test inputs without valid weekdays return None."""
    assert parse("Tomorrow morning") is None # Belong to another cluster
    assert parse("9am") is None # No day specified
    assert parse("Notaday morning") is None
