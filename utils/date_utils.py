"""
Date utility functions for the Westfall Personal Assistant.

This module provides common date and time manipulation functions
used throughout the application.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Union
import calendar


def get_current_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def parse_date_string(date_str: str) -> Optional[datetime]:
    """
    Parse a date string in various formats.
    
    Args:
        date_str: Date string to parse
        
    Returns:
        Parsed datetime object or None if parsing fails
    """
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y",
        "%m/%d/%Y %H:%M:%S",
        "%d/%m/%Y",
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None


def format_relative_time(dt: datetime) -> str:
    """
    Format a datetime as relative time (e.g., '2 hours ago').
    
    Args:
        dt: Datetime to format
        
    Returns:
        Relative time string
    """
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    diff = now - dt
    
    if diff.days > 0:
        if diff.days == 1:
            return "1 day ago"
        return f"{diff.days} days ago"
    
    hours = diff.seconds // 3600
    if hours > 0:
        if hours == 1:
            return "1 hour ago"
        return f"{hours} hours ago"
    
    minutes = diff.seconds // 60
    if minutes > 0:
        if minutes == 1:
            return "1 minute ago"
        return f"{minutes} minutes ago"
    
    return "Just now"


def get_week_range(date: Optional[datetime] = None) -> tuple[datetime, datetime]:
    """
    Get the start and end of the week for a given date.
    
    Args:
        date: Date to get week range for (defaults to today)
        
    Returns:
        Tuple of (start_of_week, end_of_week)
    """
    if date is None:
        date = datetime.now()
    
    # Get start of week (Monday)
    start = date - timedelta(days=date.weekday())
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Get end of week (Sunday)
    end = start + timedelta(days=6)
    end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    return start, end


def get_month_range(date: Optional[datetime] = None) -> tuple[datetime, datetime]:
    """
    Get the start and end of the month for a given date.
    
    Args:
        date: Date to get month range for (defaults to today)
        
    Returns:
        Tuple of (start_of_month, end_of_month)
    """
    if date is None:
        date = datetime.now()
    
    # First day of month
    start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Last day of month
    last_day = calendar.monthrange(date.year, date.month)[1]
    end = date.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
    
    return start, end


def is_business_day(date: datetime) -> bool:
    """
    Check if a date is a business day (Monday-Friday).
    
    Args:
        date: Date to check
        
    Returns:
        True if business day, False otherwise
    """
    return date.weekday() < 5


def add_business_days(start_date: datetime, business_days: int) -> datetime:
    """
    Add business days to a date, skipping weekends.
    
    Args:
        start_date: Starting date
        business_days: Number of business days to add
        
    Returns:
        New date with business days added
    """
    current_date = start_date
    days_added = 0
    
    while days_added < business_days:
        current_date += timedelta(days=1)
        if is_business_day(current_date):
            days_added += 1
    
    return current_date


def format_duration(seconds: Union[int, float]) -> str:
    """
    Format a duration in seconds as a human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{int(seconds)} seconds"
    
    minutes = int(seconds // 60)
    if minutes < 60:
        remaining_seconds = int(seconds % 60)
        if remaining_seconds == 0:
            return f"{minutes} minutes"
        return f"{minutes} minutes {remaining_seconds} seconds"
    
    hours = int(minutes // 60)
    remaining_minutes = int(minutes % 60)
    
    if hours < 24:
        if remaining_minutes == 0:
            return f"{hours} hours"
        return f"{hours} hours {remaining_minutes} minutes"
    
    days = int(hours // 24)
    remaining_hours = int(hours % 24)
    
    if remaining_hours == 0:
        return f"{days} days"
    return f"{days} days {remaining_hours} hours"