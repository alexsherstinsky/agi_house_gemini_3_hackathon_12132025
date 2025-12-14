# time_parser/parsers/specific_time_deadlines.py
"""Parser module for specific time deadlines (e.g., By 9 AM on Monday)."""
from datetime import datetime, timedelta, UTC
import re
from dateutil.relativedelta import relativedelta, MO, TU, WE, TH, FR, SA, SU

# Map text to relativedelta weekday objects
WEEKDAY_MAP = {
    'monday': MO, 'mon': MO,
    'tuesday': TU, 'tue': TU,
    'wednesday': WE, 'wed': WE,
    'thursday': TH, 'thu': TH,
    'friday': FR, 'fri': FR,
    'saturday': SA, 'sat': SA,
    'sunday': SU, 'sun': SU
}

def parse(text: str) -> datetime | None:
    """Parse specific deadline expressions with optional prepositions.
    
    Args:
        text: Time expression string to parse
        
    Returns:
        datetime object with UTC timezone if successful, None otherwise
    """
    if not text:
        return None

    # Normalize: lowercase, strip punctuation
    clean_text = text.lower().strip()
    clean_text = re.sub(r'[.,;!?]+$', '', clean_text)
    clean_text = re.sub(r'\s+', ' ', clean_text)

    # Regex Pattern Breakdown:
    # (?:by|at)?      : Optional preposition 'by' or 'at'
    # \s*             : Whitespace
    # (\d{1,2})       : Group 1: Hour (1-12 or 0-23)
    # (?::(\d{2}))?   : Group 2: Optional Minutes (:30)
    # \s*             : Whitespace
    # (am|pm)?        : Group 3: Optional Meridium
    # \s*             : Whitespace
    # (?:on)?         : Optional preposition 'on'
    # \s*             : Whitespace
    # ([a-z]+)        : Group 4: Weekday name
    
    pattern = r'(?:by|at)?\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s*(?:on)?\s*([a-z]+)'
    
    match = re.fullmatch(pattern, clean_text)
    if not match:
        return None
        
    hour_str = match.group(1)
    min_str = match.group(2)
    meridium = match.group(3)
    weekday_str = match.group(4)
    
    # Validate Weekday
    if weekday_str not in WEEKDAY_MAP:
        return None
    target_weekday = WEEKDAY_MAP[weekday_str]
    
    # Parse Time
    hour = int(hour_str)
    minute = int(min_str) if min_str else 0
    
    # Handle 12h/24h conversion
    if meridium:
        if meridium == 'pm' and hour < 12:
            hour += 12
        elif meridium == 'am' and hour == 12:
            hour = 0
    # If no meridium, assume 24h or intuitive 12h? 
    # The plan says "assume 12h if am/pm present". 
    # If missing, we treat as 24h (e.g. 14:00) or 12h (9:00). 
    # Standard ambiguity handling: strictly follow number provided.
    
    now = datetime.now(UTC)
    
    # Calculate target date
    # relativedelta(weekday=WD) moves to the *next* occurrence of WD, 
    # or stays on *current* day if today is WD.
    delta = relativedelta(
        weekday=target_weekday,
        hour=hour,
        minute=minute,
        second=0,
        microsecond=0
    )
    
    target_date = now + delta
    
    # Logic: If the parsed time is in the past (e.g. today is Monday 5pm, input "9am Monday"),
    # relativedelta might return today 9am (which is past). We assume deadline is next week.
    if target_date <= now:
        target_date += timedelta(weeks=1)
        
    return target_date
