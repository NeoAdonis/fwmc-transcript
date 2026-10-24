"""Tests for the common.time module."""

import datetime

import pytest

from common import time

td = datetime.timedelta

VALID_TIMESTAMPS = [
    ("00:00:00.000", td(0)),
    ("00:04:58.275", td(minutes=4, seconds=58, milliseconds=275)),
    ("00:05:00.901", td(minutes=5, seconds=0, milliseconds=901)),
    ("00:05:07.977", td(minutes=5, seconds=7, milliseconds=977)),
    ("01:02:03.004", td(hours=1, minutes=2, seconds=3, milliseconds=4)),
    ("00:00:00.001", td(milliseconds=1)),
    ("00:00:59.999", td(seconds=59, milliseconds=999)),
    ("00:01:00.000", td(minutes=1)),
    ("00:59:59.999", td(minutes=59, seconds=59, milliseconds=999)),
    ("01:00:00.000", td(hours=1)),
    ("23:59:59.999", td(hours=23, minutes=59, seconds=59, milliseconds=999)),
    ("24:00:00.000", td(days=1)),
    ("25:00:00.000", td(days=1, hours=1)),
    ("99:59:59.999", td(hours=99, minutes=59, seconds=59, milliseconds=999)),
    ("100:00:00.000", td(hours=100)),
    ("123:00:00.000", td(hours=123)),
]


@pytest.mark.parametrize(("time_str", "expected"), VALID_TIMESTAMPS)
def test_str_to_timedelta_valid(time_str, expected):
    """Valid WebVTT timestamps are converted to the matching timedelta."""
    assert time.str_to_timedelta(time_str) == expected


@pytest.mark.parametrize(
    "time_str",
    [
        "",
        "abc",
        "aa:bb:cc.ddd",
        "00:05:07",  # Missing fraction.
        "00:05:07.",  # Empty fraction.
        "00:05:07.9",  # One fraction digit.
        "00:05:07.97",  # Two fraction digits.
        "00:05:07.9777",  # Four fraction digits.
        "05:07.977",  # Missing hours.
        "0:05:07.977",  # Single-digit hours.
        "00:5:07.977",  # Single-digit minutes.
        "00:05:7.977",  # Single-digit seconds.
        "00:60:00.000",  # Minutes out of range.
        "00:00:60.000",  # Seconds out of range.
        "00:99:99.999",
        "-00:05:07.977",
        "+00:05:07.977",
        "00:-5:07.977",
        " 00:05:07.977",
        "00:05:07.977 ",
        "00:05:07.977\n",
        "00 :05:07.977",
        "00:05:07,977",  # SRT-style comma.
        "00:00:00:000",
        "00:05:07.977 --> 00:05:10.000",
        "00:00:00:05:07.977",
    ],
)
def test_str_to_timedelta_invalid(time_str):
    """Any format other than HH:MM:SS.mmm raises ValueError."""
    with pytest.raises(ValueError):
        time.str_to_timedelta(time_str)


@pytest.mark.parametrize(("expected", "delta"), VALID_TIMESTAMPS)
def test_timedelta_to_str_exact(delta, expected):
    """Millisecond-aligned timedeltas are formatted as HH:MM:SS.mmm."""
    assert time.timedelta_to_str(delta) == expected


@pytest.mark.parametrize(
    ("delta", "expected"),
    [
        (td(seconds=60), "00:01:00.000"),
        (td(seconds=3600), "01:00:00.000"),
        (td(minutes=60), "01:00:00.000"),
        (td(minutes=61, seconds=61), "01:02:01.000"),
        (td(hours=5), "05:00:00.000"),
        (td(hours=24), "24:00:00.000"),
        (td(days=4, hours=3), "99:00:00.000"),
        (td(days=5), "120:00:00.000"),
        (td(days=1000), "24000:00:00.000"),
    ],
)
def test_timedelta_to_str_rollover(delta, expected):
    """Units roll over into larger ones and hours aren't limited to 24 or 99."""
    assert time.timedelta_to_str(delta) == expected


@pytest.mark.parametrize(
    ("delta", "expected"),
    [
        (td(microseconds=1), "00:00:00.000"),
        (td(microseconds=999), "00:00:00.000"),
        (td(microseconds=1999), "00:00:00.001"),
        (td(milliseconds=977, microseconds=999), "00:00:00.977"),
        (td(seconds=59, microseconds=999_900), "00:00:59.999"),
        (td(seconds=59, microseconds=999_999), "00:00:59.999"),
        (td(minutes=59, seconds=59, microseconds=999_999), "00:59:59.999"),
        (td(hours=23, minutes=59, seconds=59, microseconds=999_999), "23:59:59.999"),
        (td(hours=99, minutes=59, seconds=59, microseconds=999_999), "99:59:59.999"),
    ],
)
def test_timedelta_to_str_truncates(delta, expected):
    """Milliseconds are truncated, not rounded."""
    assert time.timedelta_to_str(delta) == expected


@pytest.mark.parametrize(
    "delta",
    [td(microseconds=-1), td(milliseconds=-1), td(seconds=-1), td(days=-1)],
)
def test_timedelta_to_str_negative(delta):
    """Negative timedeltas raise ValueError."""
    with pytest.raises(ValueError):
        time.timedelta_to_str(delta)


@pytest.mark.parametrize(("time_str", "_"), VALID_TIMESTAMPS)
def test_str_round_trip(time_str, _):
    """Converting a valid timestamp to a timedelta and back is lossless."""
    assert time.timedelta_to_str(time.str_to_timedelta(time_str)) == time_str


@pytest.mark.parametrize(
    "delta",
    [
        td(0),
        td(microseconds=999),
        td(minutes=5, seconds=7, milliseconds=977),
        td(seconds=59, microseconds=999_999),
        td(hours=123, microseconds=123_456),
        td(days=2, minutes=1, seconds=2, microseconds=3),
    ],
)
def test_timedelta_round_trip(delta):
    """Converting a timedelta to a timestamp and back truncates to milliseconds."""
    truncated = delta - td(microseconds=delta.microseconds % 1000)
    assert time.str_to_timedelta(time.timedelta_to_str(delta)) == truncated


@pytest.mark.parametrize(
    ("delta", "expected"),
    [
        (td(0), "00:00.00"),
        (td(milliseconds=10), "00:00.01"),
        (td(seconds=1), "00:01.00"),
        (td(minutes=4, seconds=58, milliseconds=270), "04:58.27"),
        (td(minutes=5, seconds=7, milliseconds=970), "05:07.97"),
        (td(seconds=59, milliseconds=990), "00:59.99"),
        (td(minutes=59, seconds=59, milliseconds=990), "59:59.99"),
    ],
)
def test_timedelta_to_simple_str_exact(delta, expected):
    """Hundredth-aligned timedeltas are formatted as mm:ss.xx."""
    assert time.timedelta_to_simple_str(delta) == expected


@pytest.mark.parametrize(
    ("delta", "expected"),
    [
        (td(seconds=60), "01:00.00"),
        (td(minutes=60), "60:00.00"),
        (td(hours=1, minutes=5, seconds=7, milliseconds=970), "65:07.97"),
        (td(minutes=99, seconds=59, milliseconds=990), "99:59.99"),
        (td(minutes=100), "100:00.00"),
        (td(hours=24), "1440:00.00"),
        (td(days=1, minutes=1), "1441:00.00"),
    ],
)
def test_timedelta_to_simple_str_rollover(delta, expected):
    """Seconds roll over into minutes, which aren't limited to 60 or 99."""
    assert time.timedelta_to_simple_str(delta) == expected


@pytest.mark.parametrize(
    ("delta", "expected"),
    [
        (td(microseconds=1), "00:00.00"),
        (td(microseconds=9_999), "00:00.00"),
        (td(microseconds=19_999), "00:00.01"),
        (td(minutes=4, seconds=58, milliseconds=275), "04:58.27"),
        (td(minutes=5, seconds=7, milliseconds=977), "05:07.97"),
        (td(seconds=59, milliseconds=999), "00:59.99"),
        (td(seconds=59, microseconds=999_999), "00:59.99"),
        (td(minutes=59, seconds=59, microseconds=999_999), "59:59.99"),
        (td(minutes=99, seconds=59, microseconds=999_999), "99:59.99"),
    ],
)
def test_timedelta_to_simple_str_truncates(delta, expected):
    """Hundredths are truncated, not rounded."""
    assert time.timedelta_to_simple_str(delta) == expected


@pytest.mark.parametrize(
    "delta",
    [td(microseconds=-1), td(milliseconds=-1), td(seconds=-1), td(days=-1)],
)
def test_timedelta_to_simple_str_negative(delta):
    """Negative timedeltas raise ValueError."""
    with pytest.raises(ValueError):
        time.timedelta_to_simple_str(delta)


@pytest.mark.parametrize(
    ("time_str", "expected"),
    [
        ("00:04:58.275", "04:58.27"),
        ("00:05:07.977", "05:07.97"),
        ("01:05:07.977", "65:07.97"),
    ],
)
def test_timedelta_to_simple_str_from_webvtt(time_str, expected):
    """WebVTT timestamps are converted to LRC timestamps with truncation."""
    delta = time.str_to_timedelta(time_str)
    assert time.timedelta_to_simple_str(delta) == expected
