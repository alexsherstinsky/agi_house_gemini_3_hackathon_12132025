# time_parser/tests/test_specific_deadlines.py
"""Tests for specific_deadlines parser module."""
import pytest
from datetime import datetime, UTC
from time_parser.parsers.specific_deadlines import parse

@pytest.mark.parametrize("input_text,description", [
    ("By 9 AM on Monday", "Standard deadline format"),
    ("By 5:30 PM on Friday", "Deadline with minutes"),
    ("Before 10 am on Tuesday", "Variation with Before"),
    ("Until 2 pm on Wednesday", "Variation with Until"),
    ("by 9 am on mon", "Abbreviated weekday"),
    ("By 9:00 AM on Monday.", "Trailing punctuation"),
    ("  By 9 AM on Monday  ", "Whitespace padding")
])
def test_specific_deadlines_parsing(input_text: str, description: str):
    """Test parsing of specific deadline expressions."""
    result = parse(input_text)
    
    assert result is not None, f"Failed to parse: {input_text} ({description})"
    assert isinstance(result, datetime), f"Result not datetime: {input_text}"
    assert result.tzinfo == UTC, "Result not UTC"
    
    # Basic sanity check: result should be in the future
    now = datetime.now(UTC)
    assert result > now, "Result should be in the future"

@pytest.mark.parametrize("input_text", [
    "By 9 AM", # Missing weekday
    "on Monday", # Missing time
    "random text"
])
def test_specific_deadlines_invalid(input_text: str):
    """Test that invalid inputs return None."""
    assert parse(input_text) is None
