"""Tests for relative_dates parser module."""
import pytest
from datetime import datetime, timedelta, UTC
from dateutil.relativedelta import relativedelta
from time_parser.parsers.relative_dates import parse

@pytest.mark.parametrize("input_text, expected_offset_params", [
    ("tomorrow", {"days": 1}),
    ("TOMORROW", {"days": 1}), # Case insensitive
    ("next week", {"weeks": 1}),
    ("in 2 days", {"days": 2}),
    ("in 3 weeks", {"weeks": 3}),
    ("IN 5 HOURS", {"hours": 5}),
    ("in 1 day", {"days": 1}), # Singular unit
    ("in 2 days.", {"days": 2}), # Punctuation
])
def test_relative_dates(input_text, expected_offset_params):
    """Test parsing of relative date expressions."""
    result = parse(input_text)
    
    assert result is not None, f"Failed to parse: {input_text}"
    assert isinstance(result, datetime)
    assert result.tzinfo == UTC
    
    # Calculate expected time roughly
    now = datetime.now(UTC)
    expected = now + relativedelta(**expected_offset_params)
    
    # Allow small time difference (execution time delta)
    diff = abs((result - expected).total_seconds())
    assert diff < 5.0, f"Time mismatch for {input_text}. Got {result}, expected ~{expected}"

def test_relative_dates_no_match():
    """Test expressions that should not match."""
    assert parse("random text") is None
    assert parse("in the future") is None
    assert parse("2 days") is None # Missing 'in'
