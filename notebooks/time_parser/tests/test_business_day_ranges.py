# time_parser/tests/test_business_day_ranges.py
"""Tests for business_day_ranges parser module."""
import pytest
from datetime import datetime, timedelta, UTC
from time_parser.parsers.business_day_ranges import parse

@pytest.mark.parametrize("input_text,expected_days_added", [
    ("Within 1-2 business days", 2),
    ("within 3 business days", 3),
    ("Within 5-7 business days", 7),
])
def test_business_day_logic(input_text, expected_days_added):
    """Test that business days are calculated correctly."""
    # We need to simulate the business day addition to verify logic matches parser
    start = datetime.now(UTC)
    result = parse(input_text)
    assert result is not None
    
    # Calculate actual days difference (total days, including weekends)
    diff = result - start
    total_days = diff.days
    
    # The result should be at least expected_days_added (if no weekends) 
    # or more (if weekends were skipped)
    assert total_days >= expected_days_added
    
    # Result should never be on a weekend
    assert result.weekday() < 5

def test_edge_cases():
    """Test edge cases for business ranges."""
    # Whitespace and punctuation
    res1 = parse("  within 1-2 business days. ")
    assert res1 is not None
    
    # Singular form
    res2 = parse("within 1 business day")
    assert res2 is not None
    
    # Case insensitive
    res3 = parse("WITHIN 2 BUSINESS DAYS")
    assert res3 is not None

def test_invalid_inputs():
    """Test inputs that should return None."""
    assert parse("within 2 days") is None # Missing 'business'
    assert parse("in 2 business days") is None # Strict start pattern 'within'
    assert parse("foobar") is None
