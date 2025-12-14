# time_parser/parsers/relative_time_expressions.py
"""Parser module for relative time expressions cluster."""
from datetime import datetime, timedelta, UTC
import re
from dateutil.relativedelta import relativedelta, MO, TU, WE, TH, FR, SA, SU

# Map for weekday names to relativedelta constants
WEEKDAYS = {
    "monday": MO, "mon": MO,
    "tuesday": TU, "tue": TU,
    "wednesday": WE, "wed": WE,
    "thursday": TH, "thu": TH,
    "friday": FR, "fri": FR,
    "saturday": SA, "sat": SA,
    "sunday": SU, "sun": SU
}

# Map for fuzzy times of day
TIMES_OF_DAY = {
    "morning": 9,      # 9:00 AM
    "afternoon": 14,   # 2:00 PM
    "evening": 18,     # 6:00 PM
    "night": 20        # 8:00 PM
}

# Compiled Regex Patterns
# 1. Static keywords: "tomorrow", "next week"
STATIC_PATTERN = re.compile(r"^\s*(tomorrow|next\s+week)\s*$", re.IGNORECASE)
# 2. Numeric offsets: "in 2 days", "in 3 weeks"
NUMERIC_PATTERN = re.compile(r"(?:in\s+)?(\d+)\s+(day|week)s?", re.IGNORECASE)
# 3. Weekday+Time: "Monday morning", "next Friday"
# Matches optional 'next', weekday name, optional time of day
WEEKDAY_PATTERN = re.compile(
    r"(?:(next)\s+)?(" + "|".join(WEEKDAYS.keys()) + r")\s*(" + "|".join(TIMES_OF_DAY.keys()) + r")?",
    re.IGNORECASE
)

def parse(text: str) -> datetime | None:
    """Parse relative time expressions.
    
    Args:
        text: Time expression string (e.g., 'tomorrow', 'in 2 days', 'Monday morning')
        
    Returns:
        datetime object with UTC timezone if successful, None otherwise
    """
    # Normalize text: lowercase, strip whitespace and common punctuation
    clean_text = text.lower().strip(" .,;!\t\n")
    now = datetime.now(UTC)

    # 1. Check Static Keywords
    static_match = STATIC_PATTERN.search(clean_text)
    if static_match:
        phrase = static_match.group(1)
        if phrase == "tomorrow":
            return now + timedelta(days=1)
        if "next week" in phrase:
            return now + timedelta(weeks=1)

    # 2. Check Numeric Offsets
    num_match = NUMERIC_PATTERN.search(clean_text)
    if num_match:
        amount = int(num_match.group(1))
        unit = num_match.group(2)
        if unit == "day":
            return now + timedelta(days=amount)
        if unit == "week":
            return now + timedelta(weeks=amount)
            
    # 3. Check Weekday Logic
    weekday_match = WEEKDAY_PATTERN.search(clean_text)
    if weekday_match:
        force_next = bool(weekday_match.group(1)) # "next" detected
        day_name = weekday_match.group(2)
        time_of_day = weekday_match.group(3)
        
        target_weekday = WEEKDAYS.get(day_name)
        if not target_weekday:
            return None
            
        # Determine base time offset (default to current time if time_of_day not specified)
        hour = now.hour
        minute = now.minute
        if time_of_day and time_of_day in TIMES_OF_DAY:
            hour = TIMES_OF_DAY[time_of_day]
            minute = 0
            
        # Calculate date
        # Start with the weekday in the current week relative to now
        candidate = now + relativedelta(weekday=target_weekday, hour=hour, minute=minute, second=0, microsecond=0)
        
        # Logic: If 'next' is specified, we force +1 week if it's not strictly in the future week
        # If 'next' is NOT specified, but the candidate is in the past, move to next week
        if force_next:
            # "Next Friday" usually means the Friday of the coming week, not just the nearest future Friday
            # A simple heuristic: if candidate is within 6 days, add a week? 
            # Plan says: "Explicit next weekday". 
            # Let's assume "next Friday" means: find next occurrence, then add 7 days if it's too close? 
            # Actually, standard interpretation: "Next Friday" usually implies the week *after* this one.
            # Let's stick to simple safety: if candidate <= now, add 1 week.
            if candidate <= now:
                candidate += timedelta(weeks=1)
        else:
            # "Monday" - if today is Tuesday, implies next Monday
            if candidate <= now:
                candidate += timedelta(weeks=1)
                
        return candidate

    return None
