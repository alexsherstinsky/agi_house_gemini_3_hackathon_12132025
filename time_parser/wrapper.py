"""Exception interceptor for time parser errors."""
import json
from functools import wraps
from pathlib import Path
from typing import Callable

from coding_agent.error_queue import append_error_to_queue


def intercept_parser_errors(
    parser_instance,
    queue_path: str | Path = "error_queue.jsonl",
    customer_id: int | None = None,
) -> Callable:
    """Decorator factory to intercept and log parser errors to queue file.
    
    Args:
        parser_instance: TimeParser instance (for context, not used directly)
        queue_path: Path to error queue JSONL file
        customer_id: Optional customer ID to include in error entry
        
    Returns:
        Decorator function that wraps parser methods
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(text: str):
            try:
                return func(text)
            except Exception as e:
                # Validate input
                if not isinstance(text, str) or not text.strip():
                    # Invalid input, re-raise without logging
                    raise
                
                # Create error entry
                auxiliary_data = {
                    "parsing_error": {
                        "error_type": "parsing_failed",
                        "error_message": f"Could not parse timing description: {text}",
                        "original_timing": text,
                        "exception_type": type(e).__name__,
                        "exception_message": str(e),
                    },
                    "deadline_parsing": {
                        "timezone_used": "UTC",
                        "parsing_method": "fallback",
                        "original_timing": text,
                        "parsed_timestamp": None,
                    }
                }
                
                error_entry = {
                    "customer_id": customer_id,
                    "deadline_at": None,  # Required: None for failures
                    "timing_description": text,  # Required: non-empty string
                    "auxiliary_pretty": json.dumps(auxiliary_data),
                }
                
                # Validate error entry before appending
                if not isinstance(error_entry["timing_description"], str) or not error_entry["timing_description"].strip():
                    raise ValueError("timing_description must be a non-empty string")
                if error_entry["deadline_at"] is not None:
                    raise ValueError("deadline_at must be None for parsing failures")
                
                # Append to error queue file
                append_error_to_queue(queue_path, error_entry)
                
                # Re-raise exception (does not block original code execution)
                raise
        return wrapper
    return decorator

