# time_parser/parsers/specific_deadline_times.py
"""Parser module for specific deadline times cluster."""
from datetime import datetime, UTC
import re
from dateutil.relativedelta import relativedelta, MO, TU, WE, TH, FR, SA, SU

# Map for weekday names
WEEKDAYS = {
    "monday": MO, "mon": MO,
    "tuesday": TU, "tue": TU,
    "wednesday": WE, "wed": WE,
    "thursday": TH, "thu": TH,
    "friday": FR, "fri": FR,
    "saturday": SA, "sat": SA,
    "sunday": SU, "sun": SU
}

# Regex pattern breakdown:
# (?:by\s+)?       -> Optional 'By ' prefix
# (\d{1,2})        -> Hour (1-12)
# (?::(\d{2}))?    -> Optional Minute (:30)
# \s*              -> Whitespace
# (am|pm)          -> Meridiem
# \s*(?:on\s+)?    -> Connector ' on '
# (mon|tue...\w*)  -> Weekday
DEADLINE_PATTERN = re.compile(
    r"(?:by\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)\s*(?:on\s+)?(" + "|".join(WEEKDAYS.keys()) + r"\w*)",
    re.IGNORECASE
)

def parse(text: str) -> datetime | None:
    """Parse specific deadline expressions like 'By 9 AM on Monday'.
    
    Args:
        text: Time expression string
        
    Returns:
        datetime object with UTC timezone if successful, None otherwise
    """
    clean_text = text.lower().strip(" .,;!\t\n")
    
    match = DEADLINE_PATTERN.search(clean_text)
    if not match:
        return None
        
    hour_str, min_str, meridiem, day_str = match.groups()
    
    # Parse Time
    hour = int(hour_str)
    minute = int(min_str) if min_str else 0
    
    # 12-hour to 24-hour conversion
    if meridiem == 'pm' and hour != 12:
        hour += 12
    elif meridiem == 'am' and hour == 12:
        hour = 0
        
    # Determine Weekday
    # Regex matches 'mon', 'monday', etc. Need to match to key
    target_weekday = None
    # Try exact match first, then startswith
    if day_str in WEEKDAYS:
        target_weekday = WEEKDAYS[day_str]
    else:
        # Fallback for "mond" matching "monday" key if strictly needed, 
        # but regex ensures we have at least the prefix.
        for key, val in WEEKDAYS.items():
            if day_str.startswith(key):
                target_weekday = val
                break
                
    if not target_weekday:
        return None

    now = datetime.now(UTC)
    
    # Calculate target datetime
    # relativedelta(weekday=MO) finds the Monday in the current week (Sunday-Saturday scope in some locales) 
    # or strictly nearest. dateutil behavior: weekday=MO finds the *next* or *current* Monday.
    # We construct the specific time first.
    
    # Strategy: Find the weekday in the current week, set time.
    # If that time is in the past, add one week.
    
    candidate = now + relativedelta(weekday=target_weekday, hour=hour, minute=minute, second=0, microsecond=0)
    
    if candidate < now:
        candidate += relativedelta(weeks=1)
        
    return candidate
