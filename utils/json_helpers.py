"""JSON utility functions for the hackathon project."""

from __future__ import annotations

import json


def is_valid_json(json_string: str) -> bool:
    """Check if a string is valid JSON.
    
    Args:
        json_string: The string to validate.
        
    Returns:
        True if the string is valid JSON, False otherwise.
    """
    try:
        json.loads(json_string)
        return True
    except (json.JSONDecodeError, ValueError):
        return False

