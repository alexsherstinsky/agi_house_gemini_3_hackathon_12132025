"""Shared test utilities for time parser tests."""
from datetime import UTC, datetime


def assert_valid_datetime(result: datetime | None, input_text: str) -> None:
    """Assert that result is a valid datetime with UTC timezone.
    
    Args:
        result: The datetime result to validate
        input_text: The input text that was parsed (for error messages)
        
    Raises:
        AssertionError: If result is None, not a datetime, not timezone-aware, or not UTC
    """
    assert result is not None, f"Failed to parse: {input_text}"
    assert isinstance(result, datetime), f"Result not datetime: {input_text}"
    assert result.tzinfo is not None, f"Result not timezone-aware: {input_text}"
    assert result.tzinfo == UTC, f"Result not UTC: {input_text}"

