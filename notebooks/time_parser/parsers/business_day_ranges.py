# time_parser/parsers/business_day_ranges.py
"""Parser module for business day range expressions."""
from datetime import datetime, timedelta, UTC
import re

def add_business_days(start_date: datetime, days: int) -> datetime:
    """Add business days (skip Sat/Sun) to a date."""
    current = start_date
    added = 0
    while added < days:
        current += timedelta(days=1)
        # weekday() returns 0=Mon, 6=Sun. 5=Sat, 6=Sun.
        if current.weekday() < 5:
            added += 1
    return current

def parse(text: str) -> datetime | None:
    """Parse expressions like 'within 3 business days' or 'within 2-4 business days'.
    
    Args:
        text: Time expression string to parse
        
    Returns:
        datetime object with UTC timezone if successful, None otherwise
    """
    text = text.strip().lower()
    text = re.sub(r'[.,;!]+$', '', text)
    
    # Regex for "within X[-Y] business days"
    # Captures: 1=Start range, 2=End range (optional)
    pattern = r'(?i)within\s+(\d+)(?:\s*-\s*(\d+))?\s+business\s+days?'
    match = re.search(pattern, text)
    
    if not match:
        return None
        
    start_num = int(match.group(1))
    end_num_str = match.group(2)
    
    # If range (1-2), take upper bound. If single (3), take that.
    days_to_add = int(end_num_str) if end_num_str else start_num
    
    if days_to_add == 0:
        return datetime.now(UTC)
        
    now = datetime.now(UTC)
    deadline = add_business_days(now, days_to_add)
    
    # Return end of that business day (e.g., 17:00) or just keep time? 
    # Standard practice for deadlines often implies end of day, 
    # but strictly "in X days" often preserves current time.
    # Given parsing strategy said "calculate the date by adding Y days", we preserve time.
    
    return deadline
