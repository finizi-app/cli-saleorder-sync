"""Timezone utilities for converting local dates to UTC ranges."""

from datetime import datetime, timedelta
from typing import Tuple

import pytz


def date_to_utc_range(
    date_str: str, tz_name: str = "Asia/Ho_Chi_Minh"
) -> Tuple[str, str]:
    """
    Convert a local date string to UTC datetime range for Odoo queries.

    Args:
        date_str: Date in YYYY-MM-DD format (local timezone)
        tz_name: Timezone name (default: Asia/Ho_Chi_Minh for ICT)

    Returns:
        Tuple of (start_utc, end_utc) datetime strings in ISO format with Z suffix

    Example:
        >>> date_to_utc_range("2026-03-11", "Asia/Ho_Chi_Minh")
        ('2026-03-10T17:00:00Z', '2026-03-11T16:59:59Z')
    """
    local_tz = pytz.timezone(tz_name)
    utc_tz = pytz.UTC

    # Parse the date string
    local_date = datetime.strptime(date_str, "%Y-%m-%d")

    # Set start of day in local timezone
    local_start = local_tz.localize(local_date.replace(hour=0, minute=0, second=0))
    # Set end of day in local timezone
    local_end = local_tz.localize(local_date.replace(hour=23, minute=59, second=59))

    # Convert to UTC
    utc_start = local_start.astimezone(utc_tz)
    utc_end = local_end.astimezone(utc_tz)

    # Format as ISO strings with Z suffix (Odoo format)
    return (utc_start.strftime("%Y-%m-%d %H:%M:%S"), utc_end.strftime("%Y-%m-%d %H:%M:%S"))


def format_utc_datetime(dt_str: str) -> str:
    """
    Format Odoo datetime string to ISO format with Z suffix.

    Args:
        dt_str: Odoo datetime string (e.g., "2026-03-11 10:30:00")

    Returns:
        ISO formatted string with Z suffix (e.g., "2026-03-11T10:30:00Z")
    """
    if not dt_str:
        return ""
    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
