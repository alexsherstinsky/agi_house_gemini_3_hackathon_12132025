# time_parser/parsers/specific_deadline_with_time.py
"""Parser module for specific deadline expressions with time."""
from datetime import datetime, UTC
import re
from dateutil.relativedelta import relativedelta, MO, TU, WE, TH, FR, SA, SU

def parse(text: str) -> datetime | None:
    """Parse expressions like 'By 9 AM on Monday'.
    
    Args:
        text: Time expression string to parse
        
    Returns:
        datetime object with UTC timezone if successful, None otherwise
    """
    text = text.strip().lower()
    text = re.sub(r'[.,;!]+$', '', text)

    # Regex pattern: By [Time] on [Day]
    # Groups: 1=Hour, 2=:Minute (optional), 3=am/pm (optional), 4=Day
    pattern = r'(?i)by\s+(\d{1,2})(:\d{2})?\s*(am|pm)?\s+on\s+([a-z]+)'
    match = re.search(pattern, text)
    
    if not match:
        return None
        
    hour_str = match.group(1)
    minute_str = match.group(2) # Includes colon, e.g., ":30" or None
    meridiem = match.group(3)   # "am", "pm", or None
    day_str = match.group(4)
    
    # 1. Parse Weekday
    weekdays = {
        'monday': MO, 'mon': MO,
        'tuesday': TU, 'tue': TU,
        'wednesday': WE, 'wed': WE,
        'thursday': TH, 'thu': TH,
        'friday': FR, 'fri': FR,
        'saturday': SA, 'sat': SA,
        'sunday': SU, 'sun': SU
    }
    
    target_weekday = weekdays.get(day_str)
    if not target_weekday:
        return None
        
    # 2. Parse Time
    try:
        hour = int(hour_str)
        minute = int(minute_str[1:]) if minute_str else 0
        
        if meridiem:
            if meridiem == 'pm' and hour < 12:
                hour += 12
            elif meridiem == 'am' and hour == 12:
                hour = 0
        
        # Validation check
        if hour > 23 or minute > 59:
            return None
            
    except ValueError:
        return None

    # 3. Calculate Date
    now = datetime.now(UTC)
    
    # Find next occurrence of the weekday
    target_date = now + relativedelta(weekday=target_weekday(1))
    
    result = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return result
