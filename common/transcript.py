"""This module contains functions related to transcripts."""

import csv
import os
import re

import webvtt

from common import printer

# Define constants
INTRODUCTION_PATTERN = "Hallo hallo BAU BAU"


def check_repeats(root, file):
    """Check repeated lines in a transcript."""
    i = 1
    ln = 3
    prev_caption = None
    last_unique_caption = None
    last_unique_id = 0
    last_unique_ln = 0
    relative_path = os.path.relpath(os.path.join(root, file), os.getcwd())
    for caption in webvtt.read(os.path.join(root, file)):
        if i == 1:
            last_unique_caption = prev_caption = caption
        if caption.text == "":
            printer.print_warning("Empty caption", f"{relative_path}:{ln}")
        elif caption.text != last_unique_caption.text:
            if (i - last_unique_id) >= 3:
                printer.print_warning(
                    f"Repeated caption from {last_unique_caption.start}"
                    + f" to {prev_caption.end}",
                    f"{relative_path}:{last_unique_ln}",
                )
                print(last_unique_caption.text)
            last_unique_id = i
            last_unique_ln = ln
            last_unique_caption = caption
        prev_caption = caption
        i += 1
        ln += 3 + caption.text.count("\n")


def fetch_patterns(file):
    """Fetch CSV file containing pattern, adding a regex pre-compiled object"""
    with open(file, "r", encoding="utf-8") as csvfile:
        patterns = list(csv.DictReader(csvfile))
    for pattern in patterns:
        pattern["Regex"] = re.compile(pattern["Pattern"], re.IGNORECASE)
    return patterns


def fix_mistakes(replacements, directory, transcript_file, warn_only=False):
    """Fix common mistakes in a transcript"""
    relative_path = os.path.relpath(
        os.path.join(directory, transcript_file), os.getcwd()
    )
    with open(os.path.join(directory, transcript_file), "r", encoding="utf-8") as f:
        transcript_content = f.read()
    transcript_lines = transcript_content.splitlines()
    changed = False
    for replacement_entry in replacements:
        pattern = replacement_entry["Pattern"]
        regex = replacement_entry["Regex"]
        replacement = replacement_entry["Replacement"].replace("$", "\\")
        warning = replacement_entry["Warning"] == "Y"
        for i, line in enumerate(transcript_lines):
            if re.search(pattern, line, re.IGNORECASE):
                new_line = regex.sub(replacement, line)
                if new_line != line:
                    if warning:
                        printer.print_warning(
                            f'Replaced with "{replacement}"',
                            f"{relative_path}:{i+1}",
                        )
                        printer.print_with_highlight(
                            line,
                            pattern,
                        )
                    if not (warning and warn_only):
                        changed = True
                        transcript_lines[i] = new_line
    if changed:
        with open(os.path.join(directory, transcript_file), "w", encoding="utf-8") as f:
            f.write("\n".join(transcript_lines))
            f.write("\n")
    return changed


def highlight_ambiguities(highlights, directory, transcript_file):
    """Highlight potential ambiguities that could lead to mistakes in a transcript"""
    relative_path = os.path.relpath(
        os.path.join(directory, transcript_file), os.getcwd()
    )
    with open(os.path.join(directory, transcript_file), "r", encoding="utf-8") as f:
        transcript_content = f.read()
    transcript_lines = transcript_content.splitlines()
    # Detect and highlight potential mistakes that might actually be correct
    # for manual review
    if INTRODUCTION_PATTERN not in transcript_content:
        printer.print_warning("Potential missing introduction", relative_path)
    for highlight in highlights:
        pattern = highlight["Pattern"]
        reason = highlight["Reason"]
        regex = highlight["Regex"]
        for i, line in enumerate(transcript_lines):
            if regex.search(line):
                printer.print_info(
                    f"Potential ambiguity: {reason}", f"{relative_path}:{i+1}"
                )
                printer.print_with_highlight(line, pattern)
