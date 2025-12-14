"""Parser module for business day ranges."""
from datetime import datetime, timedelta, UTC
import re

def parse(text: str) -> datetime | None:
    """Parse business day expressions (e.g., '3 business days', '1-2 business days').
    
    Args:
        text: Time expression string to parse
        
    Returns:
        datetime object with UTC timezone if successful, None otherwise
    """
    clean_text = text.lower()
    
    # Regex to find "X business days" or "X-Y business days"
    # Captures: Group 1 (start/single), Group 2 (end optional)
    pattern = r"(?:within\s+|in\s+)?(\d+)(?:\s*-\s*(\d+))?\s+business\s+days?"
    match = re.search(pattern, clean_text)
    
    if not match:
        return None
        
    # Determine the number of days to add
    # If range "1-2", we take the max (2) to be safe for a deadline parser, 
    # or based on planning, we extract the numeric range.
    start_num = int(match.group(1))
    end_num = int(match.group(2)) if match.group(2) else None
    
    days_to_add = end_num if end_num is not None else start_num
    
    # Calculate target date skipping weekends
    current_date = datetime.now(UTC)
    added_days = 0
    
    while added_days < days_to_add:
        current_date += timedelta(days=1)
        # weekday() returns 0=Mon, 6=Sun. 5=Sat, 6=Sun.
        if current_date.weekday() < 5:
            added_days += 1
            
    return current_date
