# time_parser/tests/test_relative_time_expressions.py
"""Tests for relative_time_expressions parser module."""
import pytest
from datetime import datetime, timedelta, UTC
from dateutil.relativedelta import relativedelta, MO, TU, WE, TH, FR, SA, SU
from time_parser.parsers.relative_time_expressions import parse

@pytest.mark.parametrize("input_text, min_days, max_days", [
    ("tomorrow", 1, 1),
    ("next week", 7, 7),
    ("in 2 days", 2, 2),
    ("in 3 weeks", 21, 21),
])
def test_relative_offsets(input_text, min_days, max_days):
    """Test numeric and keyword offsets."""
    now = datetime.now(UTC)
    result = parse(input_text)
    
    assert result is not None, f"Failed to parse: {input_text}"
    assert result.tzinfo == UTC
    
    # Allow slight execution time delta, so check day difference roughly
    diff = result - now
    assert min_days <= diff.days <= max_days + 1 # +1 buffer for potentially crossing midnight during test execution

@pytest.mark.parametrize("input_text", [
    "Monday morning",
    "next Friday",
    "tuesday afternoon",
])
def test_weekday_logic(input_text):
    """Test weekday expressions return future dates."""
    now = datetime.now(UTC)
    result = parse(input_text)
    
    assert result is not None
    assert result.tzinfo == UTC
    assert result > now, f"Result for {input_text} should be in the future"
    
    # Logic check: shouldn't be more than 2 weeks away (next Friday is at most 13 days away)
    diff = result - now
    assert diff.days < 14

@pytest.mark.parametrize("input_text", [
    "random string",
    "in a while",
    "yesterday", # Not supported by current plan
    "2023-01-01" # Specific dates not handled here
])
def test_invalid_inputs(input_text):
    """Test that invalid inputs return None."""
    assert parse(input_text) is None

def test_case_insensitivity():
    """Test case and whitespace tolerance."""
    r1 = parse("tomorrow")
    r2 = parse("  TOMORROW  ")
    # They might differ by microseconds due to calling datetime.now() inside parse, 
    # but days should match
    assert r1.date() == r2.date()

def test_punctuation():
    """Test punctuation tolerance."""
    assert parse("tomorrow!") is not None
    assert parse("in 2 days.") is not None
