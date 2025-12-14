"""Parser module for weekday expressions."""
from datetime import datetime, UTC
import re
from dateutil.relativedelta import relativedelta

# Map weekday names to dateutil constants
WEEKDAY_MAP = {
    'mon': relativedelta.MO,
    'monday': relativedelta.MO,
    'tue': relativedelta.TU,
    'tuesday': relativedelta.TU,
    'wed': relativedelta.WE,
    'wednesday': relativedelta.WE,
    'thu': relativedelta.TH,
    'thursday': relativedelta.TH,
    'fri': relativedelta.FR,
    'friday': relativedelta.FR,
    'sat': relativedelta.SA,
    'saturday': relativedelta.SA,
    'sun': relativedelta.SU,
    'sunday': relativedelta.SU,
}

# Map common day parts to hours (24h format)
DAY_PART_MAP = {
    'morning': 9,
    'afternoon': 14,
    'evening': 18,
    'night': 20
}

def parse(text: str) -> datetime | None:
    """Parse weekday expressions with optional time/day-part modifiers.
    
    Args:
        text: Time expression string to parse
        
    Returns:
        datetime object with UTC timezone if successful, None otherwise
    """
    clean_text = text.lower().strip()
    
    # 1. Identify Weekday
    # Look for full or 3-letter weekday names
    day_match = re.search(r'\b(mon|tue|wed|thu|fri|sat|sun)[a-z]*\b', clean_text)
    if not day_match:
        return None
        
    target_weekday_str = day_match.group(0)
    target_weekday_const = WEEKDAY_MAP.get(target_weekday_str)
    
    if not target_weekday_const:
        # Should be caught by regex, but safety check for abbrevs mapping
        # Need to handle 'mon' mapping to 'monday' key logic if dict keys differ
        # The current dict handles both full and abbr
        return None

    now = datetime.now(UTC)
    
    # Calculate the date: Find next occurrence of this weekday
    # relativedelta(weekday=X) finds the next X, or today if today is X.
    base_date = now + relativedelta(weekday=target_weekday_const)
    
    # If the found date is today, we check if we should move to next week 
    # based on time (logic handled after time extraction, or default to future)
    # For this strategy, we assume if it's strictly in the past, move +1 week.
    
    # 2. Identify Time or Day Part
    hour = 9 # Default start of day business hour
    minute = 0
    
    # Check for specific time: "9 am", "3:30 pm", "at 5pm"
    # Regex: (Hour)(:Minute)? (am/pm)
    time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', clean_text)
    
    time_found = False
    if time_match:
        time_found = True
        h_str = time_match.group(1)
        m_str = time_match.group(2)
        meridiem = time_match.group(3)
        
        hour = int(h_str)
        minute = int(m_str) if m_str else 0
        
        if meridiem == 'pm' and hour < 12:
            hour += 12
        elif meridiem == 'am' and hour == 12:
            hour = 0
    else:
        # Check for day parts: "morning", "afternoon"
        for part, h_val in DAY_PART_MAP.items():
            if part in clean_text:
                hour = h_val
                time_found = True
                break
    
    # Construct result
    result = base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # If the resulting time is in the past (e.g. "Monday" said on Monday evening),
    # assume next week.
    if result <= now:
        result += relativedelta(weeks=1)
        
    return result
