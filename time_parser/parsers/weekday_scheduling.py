"""Parser module for weekday scheduling expressions."""
from datetime import datetime, UTC
import re
from dateutil.relativedelta import relativedelta, MO, TU, WE, TH, FR, SA, SU

def parse(text: str) -> datetime | None:
    """Parse weekday scheduling expressions (e.g., 'Monday morning', 'next Friday').
    
    Args:
        text: Time expression string to parse
        
    Returns:
        datetime object with UTC timezone if successful, None otherwise
    """
    clean_text = text.lower()
    
    # Weekday mapping
    weekdays = {
        "monday": MO, "mon": MO,
        "tuesday": TU, "tue": TU,
        "wednesday": WE, "wed": WE,
        "thursday": TH, "thu": TH,
        "friday": FR, "fri": FR,
        "saturday": SA, "sat": SA,
        "sunday": SU, "sun": SU
    }
    
    # 1. Identify Weekday
    target_day = None
    for name, day_const in weekdays.items():
        # Check for word boundary to avoid matching part of a word
        if re.search(r"\b" + name + r"\b", clean_text):
            target_day = day_const
            break
            
    if not target_day:
        return None

    # 2. Determine base date (Next occurrence of this weekday)
    # relativedelta(weekday=MO) finds the next Monday, or today if today is Monday.
    # Using MO(1) usually forces it forward if it's strictly in the future, 
    # but standard practice for 'next Monday' or just 'Monday' usually implies upcoming.
    now = datetime.now(UTC)
    result_dt = now + relativedelta(weekday=target_day(1))
    
    # If the found date is today, and the time has passed (not implemented here), 
    # or strictly based on "next" keyword logic: 
    # If "next" is explicitly present and the found date is close, logic might vary,
    # but for this scope, simple relative delta is sufficient.
    if "next" in clean_text and result_dt.date() == now.date():
        # If today is Monday and user says "next Monday", they usually mean +7 days
        result_dt += relativedelta(weeks=1)

    # 3. specific time overrides
    # Handle "morning" -> 9 AM
    if "morning" in clean_text:
        result_dt = result_dt.replace(hour=9, minute=0, second=0, microsecond=0)
    # Handle specific time (e.g., 9 am, 5 PM)
    else:
        time_match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", clean_text)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            meridiem = time_match.group(3)
            
            if meridiem == "pm" and hour < 12:
                hour += 12
            elif meridiem == "am" and hour == 12:
                hour = 0
                
            result_dt = result_dt.replace(hour=hour, minute=minute, second=0, microsecond=0)

    return result_dt
