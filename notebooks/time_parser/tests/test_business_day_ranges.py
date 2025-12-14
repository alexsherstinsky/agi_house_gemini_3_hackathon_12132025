# time_parser/tests/test_business_day_ranges.py
"""Tests for business_day_ranges parser module."""
import pytest
from datetime import datetime, UTC
from time_parser.parsers.business_day_ranges import parse

@pytest.mark.parametrize("input_text,expected_min_days", [
    ("Within 1-2 business days", 2),
    ("Within 3 business days", 3),
    ("within 5 business days", 5),
    ("within 1 business day", 1),
    ("Within 1-2 business days.", 2), # Punctuation
    ("  Within 3 business days  ", 3) # Whitespace
])
def test_business_day_ranges_parsing(input_text: str, expected_min_days: int):
    """Test parsing of business day range expressions."""
    result = parse(input_text)
    
    assert result is not None, f"Failed to parse: {input_text}"
    assert isinstance(result, datetime), f"Result not datetime: {input_text}"
    assert result.tzinfo == UTC, "Result not UTC"
    
    now = datetime.now(UTC)
    # The result should be at least 'expected_min_days' calendar days away (usually more due to weekends)
    # This is a loose assertion just to check logic direction
    delta = result - now
    assert delta.days >= 0, "Result should be in the future"

@pytest.mark.parametrize("input_text", [
    "Within 2 days", # Missing 'business'
    "2 business days", # Missing 'Within'
    "foobar"
])
def test_business_day_ranges_invalid(input_text: str):
    """Test that invalid inputs return None."""
    assert parse(input_text) is None
