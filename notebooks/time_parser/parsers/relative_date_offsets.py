# time_parser/parsers/relative_date_offsets.py
"""Parser module for relative date offsets (e.g., 'tomorrow', 'in 2 days')."""
from datetime import datetime, timedelta, UTC
import re
from dateutil.relativedelta import relativedelta

# Keyword mappings for static relative terms
STATIC_KEYWORDS = {
    "tomorrow": relativedelta(days=1),
    "next week": relativedelta(weeks=1),
}

# Regex for dynamic offsets (e.g., "in 2 days", "5 weeks")
# Captures: 1=Amount, 2=Unit
DYNAMIC_PATTERN = re.compile(r"^(?:in\s+)?(\d+)\s+(day|week|month|year)s?\s*$", re.IGNORECASE)

def parse(text: str) -> datetime | None:
    """Parse relative date expressions.
    
    Args:
        text: Time expression string to parse
        
    Returns:
        datetime object with UTC timezone if successful, None otherwise
    """
    if not text:
        return None
        
    # Normalize text: strip whitespace and punctuation, convert to lower case
    clean_text = text.strip().rstrip(".,;!").lower()
    
    # Base time is current UTC time
    now = datetime.now(UTC)
    
    # 1. Check static keywords
    if clean_text in STATIC_KEYWORDS:
        return now + STATIC_KEYWORDS[clean_text]
        
    # 2. Check dynamic regex pattern
    match = DYNAMIC_PATTERN.match(clean_text)
    if match:
        amount = int(match.group(1))
        unit = match.group(2).lower()
        
        if unit == "day":
            delta = relativedelta(days=amount)
        elif unit == "week":
            delta = relativedelta(weeks=amount)
        elif unit == "month":
            delta = relativedelta(months=amount)
        elif unit == "year":
            delta = relativedelta(years=amount)
        else:
            return None
            
        return now + delta
        
    return None
