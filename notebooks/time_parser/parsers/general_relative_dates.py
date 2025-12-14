# time_parser/parsers/general_relative_dates.py
"""Parser module for general relative date expressions (tomorrow, in 2 days, next Friday)."""
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

# Map parts of day to specific hours (24h)
PART_OF_DAY_MAP = {
    'morning': 9,
    'afternoon': 14,
    'evening': 18
}

def parse(text: str) -> datetime | None:
    """Parse general relative date expressions.
    
    Handles:
    - Keywords: 'tomorrow', 'next week'
    - Offsets: 'in 2 days', 'in 5 minutes'
    - Contextual: 'Monday morning', 'next Friday'
    
    Args:
        text: Time expression string to parse
        
    Returns:
        datetime object with UTC timezone if successful, None otherwise
    """
    if not text:
        return None

    # Normalize: lowercase, strip extra whitespace, remove trailing punctuation
    clean_text = text.lower().strip()
    clean_text = re.sub(r'[.,;!?]+$', '', clean_text)
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    now = datetime.now(UTC)

    # 1. Simple Keyword Mapping
    # Note: 'tomorrow' preserves current time, just changes day
    if clean_text == 'tomorrow':
        return now + timedelta(days=1)
    if clean_text == 'next week':
        return now + timedelta(weeks=1)
    
    # 2. Regex for 'in <N> <units>'
    # Matches: "in 2 days", "in 5 mins", etc.
    offset_pattern = r'^in\s+(\d+)\s+(min(?:ute)?s?|hours?|days?|weeks?)$'
    match = re.search(offset_pattern, clean_text)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        
        if unit.startswith('min'):
            return now + timedelta(minutes=amount)
        elif unit.startswith('hour'):
            return now + timedelta(hours=amount)
        elif unit.startswith('day'):
            return now + timedelta(days=amount)
        elif unit.startswith('week'):
            return now + timedelta(weeks=amount)

    # 3. Regex for '(<Next>)? <Weekday> <Part_of_Day>?'
    # Matches: "Monday morning", "next friday", "tuesday"
    # Logic: Find the next occurrence of this weekday.
    
    # Construct regex from keys
    wd_keys = '|'.join(WEEKDAY_MAP.keys())
    pod_keys = '|'.join(PART_OF_DAY_MAP.keys())
    
    # Pattern: Optional 'next', then Weekday, then optional Part of Day
    context_pattern = f'(?:next\s+)?({wd_keys})(?:\s+({pod_keys}))?'
    
    # We use fullmatch or ensure the regex covers the significant part of the string
    # to avoid false positives on longer sentences not meant for this parser.
    # However, strict equality checks were done above. Here we check if the string *is* this pattern.
    match = re.fullmatch(context_pattern, clean_text)
    
    if match:
        weekday_str = match.group(1)
        pod_str = match.group(2)
        
        target_wd = WEEKDAY_MAP[weekday_str]
        
        # relativedelta(weekday=MO) finds the next Monday (or today if today is Monday)
        # We want to ensure it's in the future. 
        # Using MO(+1) ensures it looks forward, but we need to handle the specific logic:
        # If we say "Monday" and it's Tuesday, we want next Monday.
        # If we say "Monday" and it's Monday, usually implies next week unless time is later.
        
        # Base calculation: move to next occurrence of weekday
        # We use +1 to force looking forward if it's the same day but we want to be safe
        # However, dateutil's default behavior with weekday=MO is: if today is MO, it stays today.
        
        delta_args = {'weekday': target_wd}
        
        # If part of day is specified, set the hour
        if pod_str:
            hour = PART_OF_DAY_MAP[pod_str]
            delta_args['hour'] = hour
            delta_args['minute'] = 0
            delta_args['second'] = 0
            delta_args['microsecond'] = 0
            
        target_date = now + relativedelta(**delta_args)
        
        # If the target is in the past (e.g. said "Monday morning" on Monday afternoon),
        # or if it's too close to now (same day) but the text implied "next",
        # we might need to add a week. 
        # For this implementation, we ensure the result is in the future.
        if target_date <= now:
            target_date += timedelta(weeks=1)
            
        # Handle explicit "next monday" where the simple calculation might have landed on today
        if 'next' in clean_text and target_date.date() == now.date():
             target_date += timedelta(weeks=1)
             
        return target_date

    return None
