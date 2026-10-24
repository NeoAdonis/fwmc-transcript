"""Tests for the common.printer module."""

import re

import pytest
import termcolor
from termcolor import colored

from common import printer

ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")
UNDERLINE = "\x1b[4m"
RED = "\x1b[31m"
YELLOW = "\x1b[33m"
COLOR_CODES = re.compile(r"\x1b\[(3[0-9]|9[0-7]|38;[0-9;]*)m")

LOCATION = "morning/transcripts/20230731/transcript.vtt:3"
REASON = "Empty caption"


def _set_color_env(monkeypatch, *, enabled):
    """Configure termcolor's environment variables and reset its cached decision."""
    monkeypatch.delenv("ANSI_COLORS_DISABLED", raising=False)
    if enabled:
        monkeypatch.delenv("NO_COLOR", raising=False)
        monkeypatch.setenv("FORCE_COLOR", "1")
    else:
        monkeypatch.delenv("FORCE_COLOR", raising=False)
        monkeypatch.setenv("NO_COLOR", "1")
    termcolor.can_colorize.cache_clear()


@pytest.fixture
def color(monkeypatch):
    """Force colored output for the duration of the test."""
    _set_color_env(monkeypatch, enabled=True)
    yield
    termcolor.can_colorize.cache_clear()


@pytest.fixture
def no_color(monkeypatch):
    """Disable colored output for the duration of the test."""
    _set_color_env(monkeypatch, enabled=False)
    yield
    termcolor.can_colorize.cache_clear()


PRINT_FUNCTIONS = [printer.print_error, printer.print_warning, printer.print_info]


@pytest.mark.usefixtures("no_color")
@pytest.mark.parametrize("print_function", PRINT_FUNCTIONS)
def test_print_functions_plain_with_location(capsys, print_function):
    """Without colors, the location, a space and the reason are printed."""
    print_function(REASON, LOCATION)
    captured = capsys.readouterr()
    assert captured.out == f"{LOCATION} {REASON}\n"
    assert captured.err == ""


@pytest.mark.usefixtures("no_color")
@pytest.mark.parametrize("print_function", PRINT_FUNCTIONS)
@pytest.mark.parametrize("call", [lambda f: f(REASON), lambda f: f(REASON, "")])
def test_print_functions_plain_without_location(capsys, print_function, call):
    """Without colors and location, only the reason is printed."""
    call(print_function)
    captured = capsys.readouterr()
    assert captured.out == f"{REASON}\n"
    assert captured.err == ""


@pytest.mark.usefixtures("color")
@pytest.mark.parametrize(
    ("print_function", "color_name"),
    [(printer.print_error, "red"), (printer.print_warning, "yellow")],
)
def test_print_error_and_warning_colored_without_location(
    capsys, print_function, color_name
):
    """With colors and no location, only the colored reason is printed."""
    print_function(REASON)
    captured = capsys.readouterr()
    assert captured.out == colored(REASON, color_name) + "\n"
    assert captured.err == ""


@pytest.mark.usefixtures("color")
@pytest.mark.parametrize(
    ("print_function", "color_name", "color_code"),
    [(printer.print_error, "red", RED), (printer.print_warning, "yellow", YELLOW)],
)
def test_print_error_and_warning_colored_with_location(
    capsys, print_function, color_name, color_code
):
    """With colors, the location is underlined and colored, then the reason."""
    print_function(REASON, LOCATION)
    captured = capsys.readouterr()
    suffix = " " + colored(REASON, color_name) + "\n"
    assert captured.out.endswith(suffix)
    styled_location = captured.out.removesuffix(suffix)
    assert ANSI_ESCAPE.sub("", styled_location) == LOCATION
    assert UNDERLINE in styled_location
    assert color_code in styled_location
    assert captured.err == ""


@pytest.mark.usefixtures("color")
def test_print_info_colored_without_location(capsys):
    """With colors and no location, info prints the reason as plain text."""
    printer.print_info(REASON)
    captured = capsys.readouterr()
    assert captured.out == f"{REASON}\n"
    assert captured.err == ""


@pytest.mark.usefixtures("color")
def test_print_info_colored_with_location(capsys):
    """With colors, info underlines the location only and keeps the reason plain."""
    printer.print_info(REASON, LOCATION)
    captured = capsys.readouterr()
    suffix = f" {REASON}\n"
    assert captured.out.endswith(suffix)
    styled_location = captured.out.removesuffix(suffix)
    assert ANSI_ESCAPE.sub("", styled_location) == LOCATION
    assert UNDERLINE in styled_location
    assert not COLOR_CODES.search(styled_location)
    assert captured.err == ""


LINE = "I'm not a chihuahua, I'm Fuwawa!"

HIGHLIGHT_CASES = [
    # Case-insensitive match of a string pattern.
    (LINE, r"\bfuwawa\b", ["Fuwawa"]),
    # Several matches, with different case.
    ("Fuwawa and FUWAWA and fuwawa", r"fuwawa", ["Fuwawa", "FUWAWA", "fuwawa"]),
    # Regex special characters in the text are kept as is.
    ("Price: $5 (maybe?) [Moco-chan] *", r"moco-chan", ["Moco-chan"]),
    # An escaped special character in the pattern.
    ("Is it (really) true?", r"\(really\)", ["(really)"]),
]


def _expected_highlight(text, matches):
    """Return the text with each listed match, in order, wrapped in bold."""
    result = ""
    rest = text
    for match in matches:
        before, found, rest = rest.partition(match)
        assert found, f"{match!r} not found in the remaining text"
        result += before + colored(match, attrs=["bold"])
    return result + rest


@pytest.mark.usefixtures("color")
@pytest.mark.parametrize(("text", "pattern", "matches"), HIGHLIGHT_CASES)
def test_print_with_highlight_colored_string_pattern(capsys, text, pattern, matches):
    """With colors, matches of a string pattern are bold, ignoring case."""
    printer.print_with_highlight(text, pattern)
    captured = capsys.readouterr()
    assert captured.out == _expected_highlight(text, matches) + "\n"
    assert captured.err == ""


@pytest.mark.usefixtures("no_color")
@pytest.mark.parametrize(("text", "pattern", "matches"), HIGHLIGHT_CASES)
def test_print_with_highlight_plain_string_pattern(capsys, text, pattern, matches):
    """Without colors, the text is printed unchanged."""
    printer.print_with_highlight(text, pattern)
    captured = capsys.readouterr()
    assert captured.out == f"{text}\n"
    assert captured.err == ""


@pytest.mark.usefixtures("color")
@pytest.mark.parametrize(
    "pattern", [r"\bmococo\b", re.compile(r"Mococo"), re.compile(r"FUWAWA")]
)
def test_print_with_highlight_no_match(capsys, pattern):
    """With colors, text without matches is printed unchanged."""
    printer.print_with_highlight(LINE, pattern)
    captured = capsys.readouterr()
    assert captured.out == f"{LINE}\n"
    assert captured.err == ""


@pytest.mark.usefixtures("color")
@pytest.mark.parametrize(
    ("pattern", "matches"),
    [
        # A case-sensitive compiled pattern only matches the exact case.
        (re.compile(r"fuwawa"), ["fuwawa"]),
        (re.compile(r"Fuwawa"), ["Fuwawa"]),
        # A compiled pattern with IGNORECASE matches any case.
        (re.compile(r"fuwawa", re.IGNORECASE), ["Fuwawa", "fuwawa"]),
    ],
)
def test_print_with_highlight_compiled_pattern(capsys, pattern, matches):
    """With colors, compiled patterns are matched using their own flags."""
    text = "Fuwawa and fuwawa"
    printer.print_with_highlight(text, pattern)
    captured = capsys.readouterr()
    assert captured.out == _expected_highlight(text, matches) + "\n"
    assert captured.err == ""
