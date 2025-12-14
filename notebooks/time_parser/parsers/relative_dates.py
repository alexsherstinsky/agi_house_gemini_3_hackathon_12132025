"""Parser module for relative date expressions."""
from datetime import datetime, timedelta, UTC
import re
from dateutil.relativedelta import relativedelta

def parse(text: str) -> datetime | None:
    """Parse relative date expressions (tomorrow, in X days, next week).
    
    Args:
        text: Time expression string to parse
        
    Returns:
        datetime object with UTC timezone if successful, None otherwise
    """
    # Normalize: lowercase, strip whitespace, remove trailing punctuation
    clean_text = text.lower().strip()
    clean_text = re.sub(r'[.,!?]+$', '', clean_text)
    
    now = datetime.now(UTC)
    
    # 1. Handle fixed terms
    if clean_text == 'tomorrow':
        return now + timedelta(days=1)
        
    # 2. Handle "next [unit]"
    # Matches: "next week", "next month", "next year"
    next_unit_match = re.search(r'^next\s+(week|month|year)$', clean_text)
    if next_unit_match:
        unit = next_unit_match.group(1)
        if unit == 'week':
            return now + timedelta(weeks=1)
        elif unit == 'month':
            return now + relativedelta(months=1)
        elif unit == 'year':
            return now + relativedelta(years=1)
            
    # 3. Handle quantitative offsets "in X [units]"
    # Matches: "in 2 days", "in 5 weeks", "in 1 day"
    offset_match = re.search(r'^in\s+(\d+)\s+(day|week|month|year)s?$', clean_text)
    if offset_match:
        amount = int(offset_match.group(1))
        unit = offset_match.group(2)
        
        if unit == 'day':
            return now + timedelta(days=amount)
        elif unit == 'week':
            return now + timedelta(weeks=amount)
        elif unit == 'month':
            return now + relativedelta(months=amount)
        elif unit == 'year':
            return now + relativedelta(years=amount)
            
    return None
