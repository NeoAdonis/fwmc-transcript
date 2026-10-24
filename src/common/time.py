"""Time-related utility functions."""

import datetime


def str_to_timedelta(time_str: str) -> datetime.timedelta:
    """Convert a time string to a timedelta object."""
    t = datetime.datetime.strptime(time_str, "%H:%M:%S.%f")
    return datetime.timedelta(
        hours=t.hour, minutes=t.minute, seconds=t.second, microseconds=t.microsecond
    )


def timedelta_to_str(delta: datetime.timedelta) -> str:
    """Convert a timedelta object to a time string (h:mm:ss.xxx)."""
    delta_parts = str(delta).split(".")
    return (
        delta_parts[0] + "." + (delta_parts[1][:3] if len(delta_parts) > 1 else "000")
    )


def timedelta_to_simple_str(delta: datetime.timedelta) -> str:
    """Convert a timedelta object to a simple string (mm:ss.xx)."""
    delta_parts = str(delta).split(".")
    time_parts = delta_parts[0].split(":")
    minutes = str(int(time_parts[0]) * 60 + int(time_parts[1])).zfill(2)
    return (
        minutes
        + ":"
        + time_parts[2]
        + "."
        + (delta_parts[1][:2] if len(delta_parts) > 1 else "00")
    )
