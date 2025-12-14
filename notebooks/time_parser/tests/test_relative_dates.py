# time_parser/tests/test_relative_dates.py
"""Tests for relative_dates parser module."""
import pytest
from datetime import datetime, timedelta, UTC
from time_parser.parsers.relative_dates import parse

@pytest.mark.parametrize("input_text,description", [
    ("tomorrow", "Simple relative day"),
    ("Tomorrow", "Capitalized input"),
    ("next week", "Simple relative unit"),
    ("in 2 days", "Numeric offset days"),
    ("in 1 day", "Singular numeric offset"),
    ("Monday morning", "Weekday combined with fuzzy time"),
    ("Friday afternoon", "Different weekday and time part"),
    ("  tomorrow  ", "Whitespace handling"),
    ("tomorrow.", "Punctuation handling")
])
def test_relative_dates_parsing(input_text: str, description: str):
    """Test parsing of relative date expressions."""
    result = parse(input_text)
    
    assert result is not None, f"Failed to parse: {input_text} ({description})"
    assert isinstance(result, datetime), f"Result not datetime: {input_text}"
    assert result.tzinfo is not None, "Result not timezone-aware"
    assert result.tzinfo == UTC, "Result not UTC"
    
    # Check that the result is in the future
    now = datetime.now(UTC)
    assert result > now, f"Result should be in the future: {input_text}"

@pytest.mark.parametrize("input_text", [
    "invalid text",
    "next month", # Not implemented in this cluster
    "in 2 years",
    "Monday midnight"
])
def test_relative_dates_invalid(input_text: str):
    """Test that invalid inputs return None."""
    assert parse(input_text) is None
