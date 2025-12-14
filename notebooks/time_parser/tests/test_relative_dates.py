"""Tests for relative_dates parser module."""
import pytest
from datetime import datetime, timedelta, UTC
from dateutil.relativedelta import relativedelta
from time_parser.parsers.relative_dates import parse

@pytest.mark.parametrize("input_text,check_type,value", [
    ("tomorrow", "days", 1),
    ("next week", "weeks", 1),
    ("in 2 days", "days", 2),
    ("in 3 weeks", "weeks", 3),
    ("IN 5 DAYS", "days", 5),  # Case insensitivity
    ("tomorrow!", "days", 1),  # Punctuation
    ("in 1 day", "days", 1),   # Singular
    ("  tomorrow  ", "days", 1), # Whitespace
    ("next month", "months", 1),
])
def test_relative_dates(input_text, check_type, value):
    """Test parsing of relative date expressions."""
    # Capture 'now' roughly when parse happens
    before = datetime.now(UTC)
    result = parse(input_text)
    after = datetime.now(UTC)
    
    assert result is not None, f"Failed to parse: {input_text}"
    assert isinstance(result, datetime)
    assert result.tzinfo == UTC
    
    # Calculate difference
    # We account for slight execution time difference by checking bounds or approximate match
    # However, relative parsers use 'now()'. 
    # A robust test checks if result is roughly (now + delta)
    
    expected_delta = None
    if check_type == "days":
        expected_delta = timedelta(days=value)
    elif check_type == "weeks":
        expected_delta = timedelta(weeks=value)
    elif check_type == "months":
        # Months are variable, use approx check or reconstruct
        expected_delta = relativedelta(months=value)
    
    # Reconstruct expected base to compare
    # Note: Using 'before' might be slightly off vs parse's internal 'now', 
    # but usually <10ms diff. 
    
    # For precise relative delta checking (months/years), we check attributes or rough total seconds
    if check_type == "months":
        # Rough check: result month should be (now.month + value) % 12 (roughly)
        # Easier: ensure it's in the future by approx correct amount
        diff = result - before
        # 1 month is roughly 28-31 days. 
        assert diff.total_seconds() > 27 * 24 * 3600 * value
    else:
        diff = result - before
        expected_seconds = expected_delta.total_seconds()
        # Allow 1 second tolerance for execution time
        assert abs(diff.total_seconds() - expected_seconds) < 1.0

def test_relative_dates_no_match():
    """Test that invalid inputs return None."""
    assert parse("yesterday") is None
    assert parse("random text") is None
