"""Printer module for printing warnings and highlighting text"""
import re
from termcolor import colored

def print_warning(location, reason):
    """Print a warning message with the location and reason"""
    print(colored(f"{location} - {reason}", "yellow"))


def print_with_highlight(location, reason, text, pattern):
    """Print the text with the pattern highlighted"""
    print_warning(location, reason)
    print(re.sub(pattern, lambda m: colored(str(m.group()), attrs=["bold"]), text))
