# time_parser/parsers/business_day_ranges.py
"""Parser module for business day range expressions."""
from datetime import datetime, timedelta, UTC
import re

# Regex to capture numeric values associated with business days
# Handles "1-2 business days", "in 3 business days", "within 1 business day"
BUSINESS_DAY_PATTERN = re.compile(r'(?:within|in)?\s*(?:(\d+)\s*-\s*)?(\d+)\s+business\s+days?', re.IGNORECASE)

def add_business_days(start_date: datetime, days_to_add: int) -> datetime:
    """Add business days to a date, skipping weekends (Saturday=5, Sunday=6)."""
    current_date = start_date
    days_added = 0
    while days_added < days_to_add:
        current_date += timedelta(days=1)
        if current_date.weekday() < 5:  # 0-4 are Mon-Fri
            days_added += 1
    return current_date

def parse(text: str) -> datetime | None:
    """Parse business day expressions like 'in 3 business days', '1-2 business days'.
    
    Args:
        text: Time expression string to parse
        
    Returns:
        datetime object with UTC timezone if successful, None otherwise
    """
    if not text:
        return None
        
    match = BUSINESS_DAY_PATTERN.search(text.strip())
    if not match:
        return None
        
    # Group 1 is lower bound (if range), Group 2 is upper bound (or single value)
    # Strategy: If range '1-2', use upper bound '2'. If single '3', use '3'.
    # Regex logic: 
    # '1-2 business days': Group 1='1', Group 2='2'
    # '3 business days': Group 1=None, Group 2='3'
    
    days_str = match.group(2)
    if not days_str:
        # Should not happen given regex, but for safety
        return None
        
    days = int(days_str)
    
    now = datetime.now(UTC)
    target_date = add_business_days(now, days)
    
    return target_date
