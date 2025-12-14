"""Parser module for business day ranges."""
from datetime import datetime, timedelta, UTC
import re

def parse(text: str) -> datetime | None:
    """Parse business day ranges (e.g. '1-2 business days', '5 working days').
    
    Interprets ranges by taking the upper bound as the deadline.
    Skips Saturdays (5) and Sundays (6).
    
    Args:
        text: Time expression string to parse
        
    Returns:
        datetime object with UTC timezone if successful, None otherwise
    """
    clean_text = text.lower().strip()
    
    # Regex to capture numeric values associated with business/working days
    # Handles: "within 1-2 business days", "in 3 working days", "5 business days"
    # Group 1: Start of range (optional)
    # Group 2: End of range (or single number)
    pattern = r'(?:within\s+)?(?:(\d+)\s*-\s*)?(\d+)\s+(?:business|working)\s+days?'
    
    match = re.search(pattern, clean_text)
    if not match:
        return None
        
    # We take the upper bound (Group 2) as the target offset
    days_to_add = int(match.group(2))
    
    current_date = datetime.now(UTC)
    
    # Add days, skipping weekends
    while days_to_add > 0:
        current_date += timedelta(days=1)
        weekday = current_date.weekday()
        # 0=Mon, ..., 4=Fri, 5=Sat, 6=Sun
        if weekday < 5:
            # It's a weekday, decrement counter
            days_to_add -= 1
            
    return current_date
