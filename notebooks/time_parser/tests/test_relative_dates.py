# time_parser/tests/test_relative_dates.py
"""Tests for relative_dates parser module."""
import pytest
from datetime import datetime, timedelta, UTC
from dateutil.relativedelta import relativedelta, MO, TU, WE, TH, FR, SA, SU
from time_parser.parsers.relative_dates import parse

@pytest.mark.parametrize("input_text,check_type,expected_val", [
    ("tomorrow", "days", 1),
    ("Tomorrow", "days", 1),
    ("next week", "days", 7),
    ("in 2 days", "days", 2),
    ("in 1 day", "days", 1),
])
def test_offsets(input_text, check_type, expected_val):
    """Test simple offset calculations."""
    # Freeze time concept by checking delta logic
    before = datetime.now(UTC)
    result = parse(input_text)
    after = datetime.now(UTC)
    
    assert result is not None
    assert result.tzinfo == UTC
    
    # Allow small execution time delta, essentially checking: result approx (now + offset)
    target = before + timedelta(days=expected_val)
    diff = abs((result - target).total_seconds())
    assert diff < 1.0, f"Expected offset {expected_val} days failed for '{input_text}'"

@pytest.mark.parametrize("input_text,target_weekday_idx,target_hour", [
    ("Monday morning", 0, 9),
    ("friday afternoon", 4, 14),
    ("Wednesday evening", 2, 18),
])
def test_day_parts(input_text, target_weekday_idx, target_hour):
    """Test 'Day PartOfDay' logic."""
    result = parse(input_text)
    assert result is not None
    assert result.tzinfo == UTC
    
    assert result.weekday() == target_weekday_idx
    assert result.hour == target_hour
    assert result.minute == 0
    
    # Ensure it is in the future
    assert result > datetime.now(UTC)

def test_edge_cases():
    """Test whitespace, punctuation, and invalid inputs."""
    # Whitespace and punctuation
    res1 = parse("  in 2 days.  ")
    assert res1 is not None
    
    # Case sensitivity
    res2 = parse("In 2 Days")
    assert res2 is not None
    
    # Invalid input
    assert parse("never") is None
    assert parse("in 5 years") is None # Only handles days per regex
