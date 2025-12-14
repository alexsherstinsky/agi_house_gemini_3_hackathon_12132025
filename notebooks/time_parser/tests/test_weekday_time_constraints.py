# time_parser/tests/test_weekday_time_constraints.py
"""Tests for weekday_time_constraints parser module."""
import pytest
from datetime import datetime, UTC
from time_parser.parsers.weekday_time_constraints import parse

@pytest.mark.parametrize("input_text,expected_weekday_idx,expected_hour", [
    ("Monday morning", 0, 9),      # Mon=0, Morning=9
    ("Tuesday", 1, None),          # Tue=1, keep current hour
    ("Friday afternoon", 4, 14),   # Fri=4, Afternoon=14
    ("By 9 AM on Monday", 0, 9),   # Mon=0, 9 AM=9
    ("Mon morning", 0, 9),         # Abbr check
    ("Wednesday 10pm", 2, 22),     # Wed=2, 10pm=22
])
def test_weekday_constraints(input_text, expected_weekday_idx, expected_hour):
    """Test parsing of weekday and time constraints."""
    before = datetime.now(UTC)
    result = parse(input_text)
    
    assert result is not None, f"Failed to parse: {input_text}"
    assert result.tzinfo == UTC
    
    # Check weekday (0=Mon, 6=Sun)
    assert result.weekday() == expected_weekday_idx, f"Wrong weekday for {input_text}"
    
    # Check time if specified
    if expected_hour is not None:
        assert result.hour == expected_hour
        assert result.minute == 0
    else:
        # If no time specified, parser keeps current hour/minute
        # Allow small diff in case minute rolled over during test execution
        assert abs(result.hour - before.hour) <= 1

    # Ensure the date is in the future
    assert result > before, "Result date should be in the future"

def test_weekday_constraints_edge_cases():
    """Test edge cases like formatting and non-matches."""
    # Reverse ordering
    res1 = parse("morning of Monday")
    assert res1 is not None
    assert res1.weekday() == 0
    assert res1.hour == 9
    
    # Case sensitivity
    res2 = parse("FRIDAY AFTERNOON")
    assert res2 is not None
    assert res2.weekday() == 4
    assert res2.hour == 14
    
    # Non-match
    assert parse("Not a day") is None
