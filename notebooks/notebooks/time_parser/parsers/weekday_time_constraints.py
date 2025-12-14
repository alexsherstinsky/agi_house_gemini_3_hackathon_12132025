# time_parser/parsers/weekday_time_constraints.py
"""Parser module for weekday and time constraint expressions."""
from datetime import datetime, UTC
import re
from dateutil.relativedelta import relativedelta, MO, TU, WE, TH, FR, SA, SU

# Weekday mapping
WEEKDAYS = {
    'mon': MO, 'monday': MO,
    'tue': TU, 'tuesday': TU,
    'wed': WE, 'wednesday': WE,
    'thu': TH, 'thursday': TH,
    'fri': FR, 'friday': FR,
    'sat': SA, 'saturday': SA,
    'sun': SU, 'sunday': SU
}

# Vague time period mapping (hour, minute)
PERIODS = {
    'morning': (9, 0),
    'afternoon': (14, 0),
    'evening': (18, 0),
    'night': (22, 0)
}

# Regex Patterns
DAY_PATTERN = re.compile(r'\b(mon|tue|wed|thu|fri|sat|sun)[a-z]*\b', re.IGNORECASE)
TIME_PATTERN = re.compile(r'\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b', re.IGNORECASE)
PERIOD_PATTERN = re.compile(r'\b(morning|afternoon|evening|night)\b', re.IGNORECASE)

def parse(text: str) -> datetime | None:
    """Parse weekday and time expressions like 'Monday morning', 'by 9 AM on Friday'.
    
    Args:
        text: Time expression string to parse
        
    Returns:
        datetime object with UTC timezone if successful, None otherwise
    """
    if not text:
        return None
        
    text_lower = text.lower()
    
    # 1. Identify Weekday
    day_match = DAY_PATTERN.search(text_lower)
    if not day_match:
        return None
        
    # Get the weekday constant (matches prefix key in WEEKDAYS)
    # We scan keys because regex matched prefix 'mon' or full 'monday'
    matched_day_str = day_match.group(0)
    target_weekday = None
    for key, val in WEEKDAYS.items():
        if matched_day_str.startswith(key):
            target_weekday = val
            break
    
    if not target_weekday:
        return None

    # Calculate next occurrence of the weekday (relativedelta weekday(1) finds next)
    now = datetime.now(UTC)
    target_date = now + relativedelta(weekday=target_weekday(1))
    
    # 2. Identify Time Constraints
    # Check for specific time (e.g., 9 AM)
    time_match = TIME_PATTERN.search(text_lower)
    hour, minute = now.hour, now.minute # Default to current time if no specific time found
    
    if time_match:
        h_str, m_str, meridiem = time_match.groups()
        h = int(h_str)
        m = int(m_str) if m_str else 0
        
        if meridiem == 'pm' and h < 12:
            h += 12
        elif meridiem == 'am' and h == 12:
            h = 0
        
        hour, minute = h, m
    else:
        # Check for vague period (e.g., morning)
        period_match = PERIOD_PATTERN.search(text_lower)
        if period_match:
            p_str = period_match.group(1)
            if p_str in PERIODS:
                hour, minute = PERIODS[p_str]

    # Apply time to target date
    return target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
