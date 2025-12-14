# time_parser/parsers/weekday_time_expressions.py
"""Parser module for weekday and time expressions (e.g., 'Monday morning')."""
from datetime import datetime, UTC
import re
from dateutil.relativedelta import relativedelta, MO, TU, WE, TH, FR, SA, SU

# Map string names to dateutil weekday constants
WEEKDAY_MAP = {
    "monday": MO, "mon": MO,
    "tuesday": TU, "tue": TU,
    "wednesday": WE, "wed": WE,
    "thursday": TH, "thu": TH,
    "friday": FR, "fri": FR,
    "saturday": SA, "sat": SA,
    "sunday": SU, "sun": SU
}

# Map vague periods to (hour, minute)
VAGUE_TIMES = {
    "morning": (9, 0),
    "afternoon": (14, 0),
    "evening": (18, 0),
    "end of day": (17, 0),
    "eod": (17, 0)
}

def parse(text: str) -> datetime | None:
    """Parse weekday and time expressions.
    
    Args:
        text: Time expression string to parse
        
    Returns:
        datetime object with UTC timezone if successful, None otherwise
    """
    if not text:
        return None
        
    clean_text = text.strip().rstrip(".,;!").lower()
    
    # 1. Find the weekday
    target_weekday = None
    for name, day_const in WEEKDAY_MAP.items():
        # strict word boundary check to avoid matching 'mon' inside 'month'
        if re.search(r'\b' + re.escape(name) + r'\b', clean_text):
            target_weekday = day_const
            break
    
    if not target_weekday:
        return None

    # Calculate the date: The next occurrence of this weekday
    # (If today is the day, relativedelta(weekday=MO) returns today, 
    # but usually users mean the upcoming one. We use MO(1) to force forward look if needed,
    # but standard `weekday=MO` usually finds the next one including today.
    # To ensure we look forward if it's in the past today, we rely on standard behavior or use specific logic.
    # Here we assume 'next upcoming' logic.)
    now = datetime.now(UTC)
    # Using +1 ensures if today is Monday, we get next Monday. 
    # Using just `weekday=target_weekday` implies "this coming X".
    # If today is Mon, "Monday" usually means today or next week? 
    # Let's assume standard `relativedelta` behavior which finds the nearest instance forward.
    dt = now + relativedelta(weekday=target_weekday)
    
    # If the calculated date is earlier than now (e.g. earlier today), move to next week
    if dt < now:
        dt += relativedelta(weeks=1)

    # 2. Find time component
    hour, minute = 9, 0 # Default to start of day (9 AM) if only day is provided, or preserve regex findings
    time_found = False

    # A. Check for specific time format (e.g., 9am, 5:30 pm, 14:00)
    # Regex: (H or HH) (:MM optional) (AM/PM optional)
    time_pattern = re.compile(r'\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b')
    time_match = time_pattern.search(clean_text)
    
    if time_match:
        h = int(time_match.group(1))
        m = int(time_match.group(2)) if time_match.group(2) else 0
        meridiem = time_match.group(3)
        
        if meridiem:
            if meridiem == "pm" and h < 12:
                h += 12
            elif meridiem == "am" and h == 12:
                h = 0
        
        if 0 <= h <= 23 and 0 <= m <= 59:
            hour, minute = h, m
            time_found = True

    # B. If no specific time, check vague keywords
    if not time_found:
        for vague, (vh, vm) in VAGUE_TIMES.items():
            if vague in clean_text:
                hour, minute = vh, vm
                time_found = True
                break
    
    # Update datetime
    dt = dt.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # Ensure we didn't accidentally create a past time today by setting the time
    # (e.g. It's 10AM, user says "Monday 9AM" (today). Result should probably be next Monday?)
    # If the resulting time is in the past, add a week.
    if dt < now:
        dt += relativedelta(weeks=1)
        
    return dt
