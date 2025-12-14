# time_parser/parsers/relative_dates.py
"""Parser module for relative_dates cluster."""
from datetime import datetime, timedelta, UTC
import re
from dateutil.relativedelta import relativedelta

def parse(text: str) -> datetime | None:
    """Parse relative date expressions (tomorrow, next week, in N days, Day Time).
    
    Args:
        text: Time expression string to parse
        
    Returns:
        datetime object with UTC timezone if successful, None otherwise
    """
    # Normalize text: remove non-alphanumeric (keep spaces), lower case, strip
    # This handles punctuation like 'tomorrow!' -> 'tomorrow'
    clean_text = re.sub(r'[^\w\s]', '', text).strip().lower()
    # Normalize whitespace to single spaces
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    now = datetime.now(UTC)
    
    # 1. Simple offsets
    if clean_text == 'tomorrow':
        return now + timedelta(days=1)
    
    if clean_text == 'next week':
        return now + timedelta(weeks=1)
        
    # 2. Numeric offsets: "in N days"
    # Matches: "in 2 days", "in 1 day"
    numeric_match = re.match(r'^in\s+(\d+)\s+days?$', clean_text)
    if numeric_match:
        days = int(numeric_match.group(1))
        return now + timedelta(days=days)
        
    # 3. Weekday + Fuzzy Time: "Monday morning"
    weekdays_map = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 
        'friday': 4, 'saturday': 5, 'sunday': 6
    }
    
    fuzzy_times_map = {
        'morning': 9,    # 9 AM
        'afternoon': 14, # 2 PM
        'evening': 18    # 6 PM
    }
    
    days_pattern = '|'.join(weekdays_map.keys())
    times_pattern = '|'.join(fuzzy_times_map.keys())
    
    # Regex matches "monday morning", "friday afternoon", etc.
    fuzzy_match = re.match(f'^({days_pattern})\s+({times_pattern})$', clean_text)
    
    if fuzzy_match:
        day_name = fuzzy_match.group(1)
        time_name = fuzzy_match.group(2)
        
        target_weekday_idx = weekdays_map[day_name]
        target_hour = fuzzy_times_map[time_name]
        
        current_weekday_idx = now.weekday()
        
        # Calculate days until next occurrence of the weekday
        days_ahead = target_weekday_idx - current_weekday_idx
        if days_ahead <= 0:
            days_ahead += 7
            
        target_date = now + timedelta(days=days_ahead)
        
        # Return date with specific hour, 0 minutes/seconds
        return target_date.replace(hour=target_hour, minute=0, second=0, microsecond=0)
        
    return None
