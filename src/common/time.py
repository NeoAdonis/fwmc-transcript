"""Time-related utility functions."""

import datetime
import re

TIMESTAMP_PATTERN = re.compile(r"(\d{2,}):([0-5]\d):([0-5]\d)\.(\d{3})", re.ASCII)


def str_to_timedelta(time_str: str) -> datetime.timedelta:
    """Convert a WebVTT timestamp (HH:MM:SS.mmm) to a timedelta.

    Hours may have more than two digits. Raise ValueError for any other format.
    """
    match = TIMESTAMP_PATTERN.fullmatch(time_str)
    if match is None:
        raise ValueError(f"Invalid WebVTT timestamp: {time_str!r}")
    hours, minutes, seconds, milliseconds = map(int, match.groups())
    return datetime.timedelta(
        hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds
    )


def to_milliseconds(delta: datetime.timedelta) -> int:
    """Return the whole milliseconds in a timedelta, raising ValueError if negative."""
    if delta < datetime.timedelta(0):
        raise ValueError(f"Negative timedelta: {delta}")
    return delta // datetime.timedelta(milliseconds=1)


def timedelta_to_str(delta: datetime.timedelta) -> str:
    """Convert a timedelta to a WebVTT timestamp (HH:MM:SS.mmm).

    Hours aren't limited to 24 or two digits, and milliseconds are truncated.
    Raise ValueError if the timedelta is negative.
    """
    seconds, milliseconds = divmod(to_milliseconds(delta), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}"


def timedelta_to_simple_str(delta: datetime.timedelta) -> str:
    """Convert a timedelta to an LRC timestamp (mm:ss.xx).

    Minutes aren't limited to 60 or two digits, and hundredths are truncated.
    Raise ValueError if the timedelta is negative.
    """
    seconds, milliseconds = divmod(to_milliseconds(delta), 1000)
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes:02}:{seconds:02}.{milliseconds // 10:02}"
