# time_parser/parsers/business_day_durations.py
"""Parser module for business day duration expressions."""
from datetime import datetime, timedelta, UTC
import re

def parse(text: str) -> datetime | None:
    """Parse business day offsets (e.g., 'within 2 business days').
    
    Args:
        text: Time expression string to parse
        
    Returns:
        datetime object with UTC timezone if successful, None otherwise
    """
    if not text:
        return None

    # Normalize
    clean_text = text.lower().strip()
    clean_text = re.sub(r'[.,;!?]+$', '', clean_text)
    
    # Regex for "[within] <N>[-<M>] business|working days"
    # Group 1: First number
    # Group 2: Optional second number (range end)
    pattern = r'(?:within|in)?\s*(\d+)(?:-(\d+))?\s*(?:business|working)\s*days?s?'
    
    match = re.search(pattern, clean_text)
    if not match:
        return None
        
    num1 = int(match.group(1))
    num2 = int(match.group(2)) if match.group(2) else None
    
    # If range (1-2 days), take the maximum (conservative deadline)
    days_to_add = num2 if num2 is not None else num1
    
    current_date = datetime.now(UTC)
    
    # Edge case: If starting on a weekend, move to Monday first before counting?
    # Standard business day logic often starts counting from next working slot.
    # If today is Sat, +1 business day -> Tuesday? Or Monday?
    # Let's align with plan: "skip Saturday (5) and Sunday (6)".
    # If we start on Sat, we treat it as non-working. 
    # Simple algorithm: Add 1 day at a time, if result is Sat/Sun, don't decrement counter.
    
    # First, if we define "1 business day" from Saturday as Monday (1 day later) or Tuesday?
    # Usually "1 business day" from Sat = End of Monday.
    # Let's iterate.
    
    remaining = days_to_add
    while remaining > 0:
        current_date += timedelta(days=1)
        if current_date.weekday() < 5:  # 0-4 are Mon-Fri
            remaining -= 1
            
    return current_date
