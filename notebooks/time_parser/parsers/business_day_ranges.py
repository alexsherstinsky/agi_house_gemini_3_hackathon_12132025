# time_parser/parsers/business_day_ranges.py
"""Parser module for business day ranges (e.g., 'within 1-2 business days')."""
from datetime import datetime, timedelta, UTC
import re

# Regex captures: 
# Group 1: Start of range (optional)
# Group 2: End of range (or single number)
# Matches "within 1-2 business days", "in 3 business days", "1 business day"
PATTERN = re.compile(r"(?:within|in)?\s+(?:(\d+)\s*-)?\s*(\d+)\s+business\s+days?", re.IGNORECASE)

def add_business_days(start_date: datetime, days_to_add: int) -> datetime:
    """Add business days to a date, skipping Saturday and Sunday."""
    current_date = start_date
    added = 0
    while added < days_to_add:
        current_date += timedelta(days=1)
        # weekday(): Monday=0, Sunday=6. 5=Sat, 6=Sun.
        if current_date.weekday() < 5:
            added += 1
    return current_date

def parse(text: str) -> datetime | None:
    """Parse business day expressions.
    
    Args:
        text: Time expression string to parse
        
    Returns:
        datetime object with UTC timezone if successful, None otherwise
    """
    if not text:
        return None
        
    clean_text = text.strip().rstrip(".,;!")
    
    match = PATTERN.search(clean_text)
    if match:
        # If a range "1-2" is provided, Group 2 is the upper bound (2).
        # If single number "3" is provided, Group 2 is the number (3).
        days_str = match.group(2)
        days = int(days_str)
        
        now = datetime.now(UTC)
        target_date = add_business_days(now, days)
        
        # Reset time to consistent EOD or keep 'now' time? 
        # Usually business deadlines imply End of Day, but strictly adding days 
        # preserves the current time. We will preserve current time for relative accuracy.
        return target_date
        
    return None
