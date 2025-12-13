#!/usr/bin/env python
"""Test exception interceptor wrapper."""
import json
from pathlib import Path
from time_parser import TimeParser
from time_parser.wrapper import intercept_parser_errors
from coding_agent.error_queue import read_error_queue

def test_wrapper():
    """Test exception interceptor with TimeParser."""
    # Clean up any existing error queue
    queue_path = Path("error_queue.jsonl")
    if queue_path.exists():
        queue_path.unlink()
    
    parser = TimeParser()
    
    # Wrap parser.parse method
    wrapped_parse = intercept_parser_errors(parser, queue_path=str(queue_path))(parser.parse)
    
    # Test with input that will fail
    try:
        wrapped_parse("tomorrow")
        print("✗ Should have raised ValueError")
        return False
    except ValueError:
        print("✓ Exception correctly raised and re-raised")
    
    # Verify error was logged
    errors = read_error_queue(queue_path)
    if len(errors) != 1:
        print(f"✗ Expected 1 error, got {len(errors)}")
        return False
    
    error = errors[0]
    print(f"✓ Error logged: {error['timing_description']}")
    
    # Validate error entry format
    assert error["timing_description"] == "tomorrow", "timing_description mismatch"
    assert error["deadline_at"] is None, "deadline_at should be None"
    assert "customer_id" in error, "customer_id missing"
    assert "auxiliary_pretty" in error, "auxiliary_pretty missing"
    
    # Parse auxiliary_pretty
    auxiliary = json.loads(error["auxiliary_pretty"])
    assert "parsing_error" in auxiliary, "parsing_error missing in auxiliary"
    assert "deadline_parsing" in auxiliary, "deadline_parsing missing in auxiliary"
    
    print("✓ Error entry format validated")
    print("✓ All wrapper tests passed")
    return True

if __name__ == "__main__":
    success = test_wrapper()
    exit(0 if success else 1)

