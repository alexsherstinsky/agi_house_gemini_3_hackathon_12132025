# time_parser/parsers/relative_time_offsets.py
"""Parser module for relative time offset expressions."""
from datetime import datetime, timedelta, UTC
import re
from typing import Pattern, Callable, Tuple, List

# Compile regex patterns for efficiency
PATTERNS: List[Tuple[Pattern, Callable[[re.Match], timedelta]]] = [
    (
        re.compile(r'^tomorrow\W*$', re.IGNORECASE),
        lambda m: timedelta(days=1)
    ),
    (
        re.compile(r'^next\s+week\W*$', re.IGNORECASE),
        lambda m: timedelta(weeks=1)
    ),
    (
        re.compile(r'in\s+(\d+)\s+days?\W*$', re.IGNORECASE),
        lambda m: timedelta(days=int(m.group(1)))
    )
]

def parse(text: str) -> datetime | None:
    """Parse relative time expressions like 'tomorrow', 'next week', 'in X days'.
    
    Args:
        text: Time expression string to parse
        
    Returns:
        datetime object with UTC timezone if successful, None otherwise
    """
    if not text:
        return None
        
    text_stripped = text.strip()
    
    # Iterate through patterns to find a match
    for pattern, handler in PATTERNS:
        match = pattern.search(text_stripped)
        if match:
            offset = handler(match)
            # Calculate target time relative to current UTC time
            return datetime.now(UTC) + offset
            
    return None
