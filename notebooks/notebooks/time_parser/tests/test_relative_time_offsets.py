# time_parser/tests/test_relative_time_offsets.py
"""Tests for relative_time_offsets parser module."""
import pytest
from datetime import datetime, timedelta, UTC
from time_parser.parsers.relative_time_offsets import parse

@pytest.mark.parametrize("input_text,offset_kwargs", [
    ("tomorrow", {"days": 1}),
    ("Tomorrow", {"days": 1}),
    ("TOMORROW!", {"days": 1}),
    ("next week", {"weeks": 1}),
    ("next  week", {"weeks": 1}),
    ("in 2 days", {"days": 2}),
    ("in 5 days", {"days": 5}),
    ("in  1  day", {"days": 1}),
])
def test_relative_offsets_match(input_text: str, offset_kwargs: dict):
    """Test positive matches for relative offset patterns."""
    # Get time before and after parsing to establish a valid window
    before = datetime.now(UTC)
    result = parse(input_text)
    after = datetime.now(UTC)
    
    assert result is not None, f"Failed to parse: {input_text}"
    assert result.tzinfo == UTC
    
    expected_delta = timedelta(**offset_kwargs)
    
    # The result should be roughly (now + delta)
    # We allow a small margin for execution time
    expected_time_approx = before + expected_delta
    
    # Check that result is close to expected time (within 1 second)
    diff = abs((result - expected_time_approx).total_seconds())
    assert diff < 1.0, f"Time mismatch. Got {result}, expected approx {expected_time_approx}"

def test_relative_offsets_no_match():
    """Test non-matching inputs return None."""
    assert parse("yesterday") is None
    assert parse("next month") is None
    assert parse("random text") is None
    assert parse("") is None
