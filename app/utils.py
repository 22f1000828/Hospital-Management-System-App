"""
Utility functions for timezone handling
"""
from datetime import datetime
import pytz

# IST timezone
IST = pytz.timezone('Asia/Kolkata')

def get_ist_now():
    """Get current datetime in IST timezone"""
    return datetime.now(IST)

def get_ist_datetime(dt):
    """Convert datetime to IST timezone"""
    if dt.tzinfo is None:
        # Assume UTC if no timezone info
        dt = pytz.UTC.localize(dt)
    return dt.astimezone(IST)

def get_ist_date():
    """Get current date in IST timezone"""
    return get_ist_now().date()

