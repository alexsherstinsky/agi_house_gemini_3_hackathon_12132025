#!/usr/bin/env python
"""Test TimeParser basic functionality."""
from time_parser.parser import TimeParser

def test_parser():
    """Test TimeParser with basic cases."""
    p = TimeParser()
    print(f"✓ Loaded {len(p._cluster_parsers)} cluster modules")
    
    # Test basic cases
    result1 = p.parse("asap")
    print(f"✓ Parsed 'asap': {result1}")
    
    result2 = p.parse("now")
    print(f"✓ Parsed 'now': {result2}")
    
    # Test unknown pattern
    try:
        p.parse("tomorrow")
        print("✗ Should have raised ValueError")
        return False
    except ValueError as e:
        print(f"✓ Correctly raised ValueError for unknown pattern: {e}")
    
    print("✓ All basic parser tests passed")
    return True

if __name__ == "__main__":
    success = test_parser()
    exit(0 if success else 1)

