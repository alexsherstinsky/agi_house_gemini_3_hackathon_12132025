# time_parser/parsers/business_day_ranges.py
"""Parser module for business_day_ranges cluster."""
from datetime import datetime, timedelta, UTC
import re

def parse(text: str) -> datetime | None:
    """Parse business day range expressions (Within 1-2 business days).
    
    Args:
        text: Time expression string to parse
        
    Returns:
        datetime object with UTC timezone if successful, None otherwise
    """
    # Pattern: within X[-Y] business days
    # Handles: "Within 1-2 business days", "within 3 business days"
    pattern = re.compile(r"within\s+(\d+)(?:-(\d+))?\s+business\s+days?", re.IGNORECASE)
    
    clean_text = text.strip().rstrip(".,;!")
    match = pattern.search(clean_text)
    
    if not match:
        return None
        
    start_days = int(match.group(1))
    # If range (1-2), use upper bound (2). If single (3), use it.
    end_days = int(match.group(2)) if match.group(2) else start_days
    
    days_to_add = end_days
    
    current_date = datetime.now(UTC)
    days_added = 0
    
    # Loop to add business days (skipping Sat/Sun)
    while days_added < days_to_add:
        current_date += timedelta(days=1)
        weekday = current_date.weekday() # 0=Mon, ..., 5=Sat, 6=Sun
        
        if weekday < 5: # It is a weekday
            days_added += 1
            
    return current_date
