# time_parser/parsers/business_day_ranges.py
"""Parser module for business day range expressions."""
from datetime import datetime, timedelta, UTC
import re

# Pattern: Capture first number, optional range connector + second number, then "business days"
# Examples: "3 business days", "1-2 business days", "1 to 5 business days"
BUSINESS_PATTERN = re.compile(r"(?:within|in)?\s*(\d+)(?:\s*(?:-|to)\s*(\d+))?\s*business\s*days?", re.IGNORECASE)

def add_business_days(start_date: datetime, days_to_add: int) -> datetime:
    """Add business days to a date, skipping weekends (Saturday=5, Sunday=6)."""
    current_date = start_date
    added = 0
    while added < days_to_add:
        current_date += timedelta(days=1)
        # 0=Mon, ..., 5=Sat, 6=Sun
        if current_date.weekday() < 5:
            added += 1
    return current_date

def parse(text: str) -> datetime | None:
    """Parse business day ranges.
    
    Args:
        text: Time expression string (e.g., 'in 3 business days', '1-2 business days')
        
    Returns:
        datetime object with UTC timezone if successful, None otherwise
    """
    clean_text = text.lower().strip(" .,;!\t\n")
    
    match = BUSINESS_PATTERN.search(clean_text)
    if not match:
        return None
        
    start_num = int(match.group(1))
    end_num_str = match.group(2)
    
    # Determine offset: if range (1-2), use max (2) per requirements
    days_offset = int(end_num_str) if end_num_str else start_num
    
    now = datetime.now(UTC)
    
    # Calculate deadline skipping weekends
    result_date = add_business_days(now, days_offset)
    
    return result_date
