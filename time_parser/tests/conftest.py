"""Shared pytest fixtures for time parser tests."""
import pytest

from time_parser import TimeParser


@pytest.fixture
def parser():
    """Fixture providing TimeParser instance.
    
    Returns:
        TimeParser instance
    """
    return TimeParser()

