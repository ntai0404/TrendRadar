# coding=utf-8
"""
time tools module

This module provides a unified time processing function, and all time zone related operations should use the DEFAULT_TIMEZONE constant.
"""

from datetime import datetime
from typing import Optional

import pytz

# Default time zone constant - only as a fallback, during normal operation use app.timezone in config.yaml
DEFAULT_TIMEZONE = "Asia/Shanghai"


def get_configured_time(timezone: str = DEFAULT_TIMEZONE) -> datetime:
    """
    Get the current time in the configured time zone

    Args:
        timezone: time zone name, such as 'Asia/Shanghai', 'America/Los_Angeles'

    Returns:
        Current time with time zone information
    """
    try:
        tz = pytz.timezone(timezone)
    except pytz.UnknownTimeZoneError:
        print(f"[Warning] Unknown time zone '{timezone}', using default time zone {DEFAULT_TIMEZONE}")
        tz = pytz.timezone(DEFAULT_TIMEZONE)
    return datetime.now(tz)


def format_date_folder(
    date: Optional[str] = None, timezone: str = DEFAULT_TIMEZONE
) -> str:
    """
    Format date folder name (ISO format: YYYY-MM-DD)

    Args:
        date: Specifies the date string, if None, the current date is used
        timezone: time zone name

    Returns:
        Formatted date string, such as '2025-12-09'
    """
    if date:
        return date
    return get_configured_time(timezone).strftime("%Y-%m-%d")


def format_time_filename(timezone: str = DEFAULT_TIMEZONE) -> str:
    """
    Format time file name (Format: HH-MM, for file name)

    Windows systems do not support colons as file names, so use hyphens

    Args:
        timezone: time zone name

    Returns:
        Formatted time string, such as '15-30'
    """
    return get_configured_time(timezone).strftime("%H-%M")


def get_current_time_display(timezone: str = DEFAULT_TIMEZONE) -> str:
    """
    Get the current time display (format: HH:MM, for display)

    Args:
        timezone: time zone name

    Returns:
        Formatted time string, such as '15:30'
    """
    return get_configured_time(timezone).strftime("%H:%M")


def convert_time_for_display(time_str: str) -> str:
    """
    Convert HH-MM format to HH:MM format for display

    Args:
        time_str: input time string, such as '15-30'

    Returns:
        Converted time string, such as '15:30'
    """
    if time_str and "-" in time_str and len(time_str) == 5:
        return time_str.replace("-", ":")
    return time_str


def format_iso_time_friendly(
    iso_time: str,
    timezone: str = DEFAULT_TIMEZONE,
    include_date: bool = True,
) -> str:
    """
    Convert ISO format time to user time zone friendly display format

    Args:
        iso_time: ISO format time string, such as '2025-12-29T00:20:00' or '2025-12-29T00:20:00+00:00'
        timezone: target time zone name
        include_date: whether to include the date part

    Returns:
        Friendly formatted time string, such as '12-29 08:20' or '08:20'
    """
    if not iso_time:
        return ""

    try:
        # Try to parse various ISO formats
        dt = None

        # Try to parse the format with time zone
        if "+" in iso_time or iso_time.endswith("Z"):
            iso_time = iso_time.replace("Z", "+00:00")
            try:
                dt = datetime.fromisoformat(iso_time)
            except ValueError:
                pass

        # Attempt to parse the format without time zone (assuming UTC)
        if dt is None:
            try:
                # Handle T delimiter
                if "T" in iso_time:
                    dt = datetime.fromisoformat(iso_time.replace("T", " ").split(".")[0])
                else:
                    dt = datetime.fromisoformat(iso_time.split(".")[0])
                # Assume UTC time
                dt = pytz.UTC.localize(dt)
            except ValueError:
                pass

        if dt is None:
            # Unable to parse, return a simplified version of the original string
            if "T" in iso_time:
                parts = iso_time.split("T")
                if len(parts) == 2:
                    date_part = parts[0][5:]  # MM-DD
                    time_part = parts[1][:5]  # HH:MM
                    return f"{date_part} {time_part}" if include_date else time_part
            return iso_time

        # Convert to target time zone
        try:
            target_tz = pytz.timezone(timezone)
        except pytz.UnknownTimeZoneError:
            target_tz = pytz.timezone(DEFAULT_TIMEZONE)

        dt_local = dt.astimezone(target_tz)

        # Format output
        if include_date:
            return dt_local.strftime("%m-%d %H:%M")
        else:
            return dt_local.strftime("%H:%M")

    except Exception:
        # Return a simplified version of the original string on error
        if "T" in iso_time:
            parts = iso_time.split("T")
            if len(parts) == 2:
                date_part = parts[0][5:]  # MM-DD
                time_part = parts[1][:5]  # HH:MM
                return f"{date_part} {time_part}" if include_date else time_part
        return iso_time


def is_within_days(
    iso_time: str,
    max_days: int,
    timezone: str = DEFAULT_TIMEZONE,
) -> bool:
    """
    Check if ISO format time is within specified number of days

    Used to filter RSS article freshness to determine whether the article has been published for more than a specified number of days.

    Args:
        iso_time: ISO format time string (such as '2025-12-29T00:20:00' or with time zone)
        max_days: Maximum number of days (True will be returned if the article publication time does not exceed this number of days)
            - max_days > 0: Normal filtering, retain articles within N days
            - max_days <= 0: disable filtering and keep all articles
        timezone: time zone name (used to get the current time)

    Returns:
        True if the time is within the specified number of days (should be retained), False if it is older than the specified number of days (should be filtered)
        If the time cannot be parsed, return True (keep the article)
    """
    # When there is no timestamp or filtering is disabled, keep the article
    if not iso_time:
        return True
    if max_days <= 0:
        return True # max_days=0 means disabling filtering

    try:
        dt = None

        # Try to parse the format with time zone
        if "+" in iso_time or iso_time.endswith("Z"):
            iso_time_normalized = iso_time.replace("Z", "+00:00")
            try:
                dt = datetime.fromisoformat(iso_time_normalized)
            except ValueError:
                pass

        # Attempt to parse the format without time zone (assuming UTC)
        if dt is None:
            try:
                if "T" in iso_time:
                    dt = datetime.fromisoformat(iso_time.replace("T", " ").split(".")[0])
                else:
                    dt = datetime.fromisoformat(iso_time.split(".")[0])
                dt = pytz.UTC.localize(dt)
            except ValueError:
                pass

        if dt is None:
            # Unable to parse time, keep the article
            return True

        # Get the current time (configured time zone, with time zone information)
        now = get_configured_time(timezone)

        # Calculate the time difference (subtracting two datetimes with time zones will automatically handle the time zone difference)
        diff = now - dt
        days_diff = diff.total_seconds() / (24 * 60 * 60)

        return days_diff <= max_days

    except Exception:
        # Keep the article in case of error
        return True


def calculate_days_old(iso_time: str, timezone: str = DEFAULT_TIMEZONE) -> Optional[float]:
    """
    Calculate how many days since ISO format time

    Args:
        iso_time: ISO format time string
        timezone: time zone name

    Returns:
        Number of days since today (floating point number), returns None if it cannot be parsed
    """
    if not iso_time:
        return None

    try:
        dt = None

        # Try to parse the format with time zone
        if "+" in iso_time or iso_time.endswith("Z"):
            iso_time_normalized = iso_time.replace("Z", "+00:00")
            try:
                dt = datetime.fromisoformat(iso_time_normalized)
            except ValueError:
                pass

        # Attempt to parse the format without time zone (assuming UTC)
        if dt is None:
            try:
                if "T" in iso_time:
                    dt = datetime.fromisoformat(iso_time.replace("T", " ").split(".")[0])
                else:
                    dt = datetime.fromisoformat(iso_time.split(".")[0])
                dt = pytz.UTC.localize(dt)
            except ValueError:
                pass

        if dt is None:
            return None

        now = get_configured_time(timezone)
        diff = now - dt
        return diff.total_seconds() / (24 * 60 * 60)

    except Exception:
        return None

