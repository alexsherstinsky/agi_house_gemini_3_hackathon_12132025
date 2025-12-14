# time_parser/tests/test_relative_date_offsets.py
"""Tests for relative_date_offsets parser module."""
import pytest
from datetime import datetime, UTC
from dateutil.relativedelta import relativedelta
from time_parser.parsers.relative_date_offsets import parse

@pytest.mark.parametrize("input_text,expected_offset,unit_type", [
    ("tomorrow", 1, "days"),
    ("next week", 1, "weeks"),
    ("in 2 days", 2, "days"),
    ("In 5 Weeks", 5, "weeks"),
    ("   tomorrow   ", 1, "days"),
    # Additional edge cases
    ("in 1 year", 1, "years"),
    ("in 100 days", 100, "days"),
    ("tomorrow!", 1, "days"),
])
def test_relative_date_offsets(input_text, expected_offset, unit_type):
    """Test parsing of relative date expressions."""
    # Capture 'now' before parsing to ensure comparison is valid
    # (Parsing happens instantly, so delta should be negligible)
    before = datetime.now(UTC)
    result = parse(input_text)
    after = datetime.now(UTC)
    
    assert result is not None, f"Failed to parse: {input_text}"
    assert isinstance(result, datetime), f"Result not datetime: {input_text}"
    assert result.tzinfo == UTC, f"Result not UTC: {input_text}"
    
    # Calculate expected target
    if unit_type == "days":
        expected_delta = relativedelta(days=expected_offset)
    elif unit_type == "weeks":
        expected_delta = relativedelta(weeks=expected_offset)
    elif unit_type == "months":
        expected_delta = relativedelta(months=expected_offset)
    elif unit_type == "years":
        expected_delta = relativedelta(years=expected_offset)
        
    # Logic: The result should be roughly (now + expected_delta)
    # We allow a small margin of error (e.g. 1 second) for execution time
    expected_date = before + expected_delta
    
    # Check that the difference between result and expected is minimal
    diff = abs((result - expected_date).total_seconds())
    assert diff < 2.0, f"Date mismatch. Got {result}, expected approx {expected_date}"

def test_invalid_input():
    """Test that invalid inputs return None."""
    assert parse("yesterday") is None # Not in this cluster
    assert parse("random text") is None
    assert parse("") is None
