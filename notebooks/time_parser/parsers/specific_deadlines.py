# time_parser/parsers/specific_deadlines.py
"""Parser module for specific_deadlines cluster."""
from datetime import datetime, timedelta, UTC
import re
from dateutil.relativedelta import relativedelta

def parse(text: str) -> datetime | None:
    """Parse specific deadline expressions (By 9 AM on Monday).
    
    Args:
        text: Time expression string to parse
        
    Returns:
        datetime object with UTC timezone if successful, None otherwise
    """
    # Regex pattern explanation:
    # (?:by|before|until) : Anchor words
    # \s+(\d{1,2})        : Hour (Group 1)
    # (?::(\d{2}))?       : Optional Minutes (Group 2)
    # \s*(am|pm)?         : Optional Meridiem (Group 3)
    # \s+on\s+            : Connector
    # (mon|tue...)[a-z]*  : Weekday, matches Mon, Monday, etc. (Group 4)
    pattern = re.compile(
        r"(?:by|before|until)\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s+on\s+(mon|tue|wed|thu|fri|sat|sun)[a-z]*",
        re.IGNORECASE
    )
    
    # Clean text to handle trailing punctuation safely, though regex might catch it inside text.
    # Using search allows the pattern to exist within the string, but we want to ensure
    # the text effectively matches the structure. 
    # Let's clean trailing punctuation first.
    clean_text = text.strip().rstrip(".,;!")
    
    match = pattern.search(clean_text)
    if not match:
        return None
        
    hour = int(match.group(1))
    minute = int(match.group(2)) if match.group(2) else 0
    meridiem = match.group(3).lower() if match.group(3) else None
    weekday_prefix = match.group(4).lower() # first 3 chars due to regex group
    
    # Convert 12h to 24h format
    if meridiem:
        if meridiem == 'pm' and hour < 12:
            hour += 12
        elif meridiem == 'am' and hour == 12:
            hour = 0
            
    # Map weekday prefix to index
    weekdays_map = {
        'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 
        'fri': 4, 'sat': 5, 'sun': 6
    }
    target_weekday_idx = weekdays_map.get(weekday_prefix)
    
    if target_weekday_idx is None:
        return None
        
    now = datetime.now(UTC)
    current_weekday_idx = now.weekday()
    
    # Calculate next occurrence
    days_ahead = target_weekday_idx - current_weekday_idx
    if days_ahead <= 0:
        days_ahead += 7
        
    target_date = now + timedelta(days=days_ahead)
    
    # Construct final datetime
    try:
        return target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
    except ValueError:
        return None # In case of invalid time e.g. 25:00
