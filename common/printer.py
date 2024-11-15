"""Printer module for printing warnings and highlighting text"""

import re

from termcolor import colored


def print_error(reason: str, location=""):
    """Print an error message with the location and reason"""
    if location != "":
        reason = f" {reason}"
    print(f"{colored(location, "red", attrs=["underline"])}{colored(reason, "red")}")


def print_warning(reason: str, location=""):
    """Print a warning message with the location and reason"""
    if location != "":
        reason = f" {reason}"
    print(
        f"{colored(location, "yellow", attrs=["underline"])}{colored(reason, "yellow")}"
    )


def print_info(reason: str, location=""):
    """Print an infomational message with the location and reason"""
    if location != "":
        reason = f" {reason}"
    print(f"{colored(location, attrs=["underline"])}{reason}")


def print_with_highlight(text: str, pattern: str | re.Pattern[str]):
    """Print the text with the pattern highlighted"""
    print(
        re.sub(
            pattern,
            lambda m: colored(str(m.group()), attrs=["bold"]),
            text,
            flags=re.IGNORECASE,
        )
    )
