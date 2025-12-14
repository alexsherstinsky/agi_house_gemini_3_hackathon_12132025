# time_parser/parsers/relative_dates.py
"""Parser module for relative date expressions."""
from datetime import datetime, timedelta, UTC
import re
from dateutil.relativedelta import relativedelta, MO, TU, WE, TH, FR, SA, SU

def parse(text: str) -> datetime | None:
    """Parse relative date expressions like 'tomorrow', 'next week', 'Monday morning'.
    
    Args:
        text: Time expression string to parse
        
    Returns:
        datetime object with UTC timezone if successful, None otherwise
    """
    text = text.strip().lower()
    # Remove trailing punctuation
    text = re.sub(r'[.,;!]+$', '', text)
    
    now = datetime.now(UTC)
    
    # 1. Exact Keywords
    if text == "tomorrow":
        return now + timedelta(days=1)
    
    if text == "next week":
        return now + timedelta(weeks=1)
    
    # 2. 'In N days' pattern
    # Matches: "in 2 days", "in 1 day"
    in_days_match = re.search(r'^in\s+(\d+)\s+days?$', text)
    if in_days_match:
        days = int(in_days_match.group(1))
        return now + timedelta(days=days)
        
    # 3. 'Day PartOfDay' pattern
    # Matches: "Monday morning", "Friday afternoon"
    
    # Mappings
    weekdays = {
        'monday': MO, 'mon': MO,
        'tuesday': TU, 'tue': TU,
        'wednesday': WE, 'wed': WE,
        'thursday': TH, 'thu': TH,
        'friday': FR, 'fri': FR,
        'saturday': SA, 'sat': SA,
        'sunday': SU, 'sun': SU
    }
    
    parts_of_day = {
        'morning': 9,    # 09:00
        'afternoon': 14, # 14:00
        'evening': 18    # 18:00
    }
    
    day_pattern = '|'.join(weekdays.keys())
    part_pattern = '|'.join(parts_of_day.keys())
    
    # Regex: (monday|mon) (morning|afternoon...)
    combo_regex = fr'^({day_pattern})\s+({part_pattern})$'
    combo_match = re.search(combo_regex, text)
    
    if combo_match:
        day_str = combo_match.group(1)
        part_str = combo_match.group(2)
        
        target_weekday = weekdays[day_str]
        target_hour = parts_of_day[part_str]
        
        # Logic: Find the *next* occurrence of this day. 
        # using (+1) ensures we look forward, not current day if match
        target_date = now + relativedelta(weekday=target_weekday(1))
        
        # Reset time to the specific part of day
        result = target_date.replace(hour=target_hour, minute=0, second=0, microsecond=0)
        return result

    return None
