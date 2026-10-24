"""Helpers to print colored errors, warnings and highlighted text.

Everything is printed to stdout. Colors follow termcolor's rules: they're disabled
when stdout isn't a terminal or NO_COLOR is set, and forced with FORCE_COLOR.
"""

import re

from termcolor import colored


def print_message(reason: str, location: str, color: str | None) -> None:
    """Print the reason after its underlined location, both in the given color."""
    message = colored(reason, color) if color else reason
    if location:
        message = f"{colored(location, color, attrs=['underline'])} {message}"
    print(message)


def print_error(reason: str, location: str = "") -> None:
    """Print an error in red, after its underlined location if given."""
    print_message(reason, location, "red")


def print_warning(reason: str, location: str = "") -> None:
    """Print a warning in yellow, after its underlined location if given."""
    print_message(reason, location, "yellow")


def print_info(reason: str, location: str = "") -> None:
    """Print an informational message, after its underlined location if given."""
    print_message(reason, location, None)


def print_with_highlight(text: str, pattern: str | re.Pattern[str]) -> None:
    """Print the text with the pattern's matches in bold.

    String patterns are matched case-insensitively; compiled patterns use their
    own flags.
    """
    if isinstance(pattern, str):
        pattern = re.compile(pattern, re.IGNORECASE)
    print(pattern.sub(lambda m: colored(m.group(), attrs=["bold"]), text))
