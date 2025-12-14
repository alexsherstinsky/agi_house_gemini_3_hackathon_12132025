"""Parser module for relative date expressions."""
from datetime import datetime, UTC
import re
from dateutil.relativedelta import relativedelta

def parse(text: str) -> datetime | None:
    """Parse relative date expressions (e.g., 'tomorrow', 'in 2 days').
    
    Args:
        text: Time expression string to parse
        
    Returns:
        datetime object with UTC timezone if successful, None otherwise
    """
    # Normalize text: lowercase, remove trailing punctuation
    clean_text = text.lower().strip().rstrip(".,!?")
    
    now = datetime.now(UTC)
    
    # 1. Handle exact keywords
    if clean_text == "tomorrow":
        return now + relativedelta(days=1)
    
    if clean_text == "next week":
        return now + relativedelta(weeks=1)
        
    # 2. Handle structured patterns: "in <num> <unit>"
    # Regex matches: "in", whitespace, number, whitespace, unit (singular or plural)
    pattern = r"^in\s+(\d+)\s+(day|week|hour|minute)s?$"
    match = re.match(pattern, clean_text)
    
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        
        if unit == "day":
            return now + relativedelta(days=amount)
        elif unit == "week":
            return now + relativedelta(weeks=amount)
        elif unit == "hour":
            return now + relativedelta(hours=amount)
        elif unit == "minute":
            return now + relativedelta(minutes=amount)
            
    return None
