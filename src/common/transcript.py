"""Helpers to validate, fix and convert WebVTT transcripts.

Diagnostics are printed with common.printer, with paths relative to the current
directory. Line numbers from validate and check_repeats assume WhisperX's layout:
a WEBVTT header and a blank line, then cues made of a timing line, one or more
text lines and a blank line, with no cue identifiers or NOTE blocks.
"""

# TODO: Support cue identifiers and NOTE blocks when counting lines, so that
# edited transcripts can be validated too.
# TODO: Consider returning the issues found instead of printing them.

import csv
import html
import itertools
import os
import re
from collections.abc import Iterator
from typing import Any

import webvtt

from common import printer, time

INTRODUCTION_PATTERN = "Hallo hallo BAU BAU"
MIN_REPEATS = 3


def numbered_captions(path: str) -> Iterator[tuple[int, webvtt.Caption]]:
    """Yield the captions of a transcript with the line numbers of their timings."""
    line_number = 3
    for caption in webvtt.read(path):
        yield line_number, caption
        line_number += 3 + caption.text.count("\n")


def validate(path: str) -> None:
    """Print an error for each caption with invalid timing.

    A caption is invalid if it doesn't end after it starts or starts before the
    previous one ends.
    """
    relative_path = os.path.relpath(path)
    prev_end = None
    for line_number, caption in numbered_captions(path):
        location = f"{relative_path}:{line_number}"
        start = time.str_to_timedelta(caption.start)
        end = time.str_to_timedelta(caption.end)
        if start >= end:
            printer.print_error("Caption doesn't end after it starts", location)
        if prev_end is not None and prev_end > start:
            printer.print_error("Caption overlaps with the previous one", location)
        # TODO: Fix issues in transcripts first to minimize noise
        # if len(caption.text) > (42 * 3):
        #     printer.print_warning("Caption too long", location)
        #     print(caption.text)
        prev_end = end


def to_lrc(path: str) -> str:
    """Write an LRC file next to a transcript and return its path.

    Each caption becomes one line with its start time and plain text.
    """
    lrc_path = os.path.splitext(path)[0] + ".lrc"
    with open(lrc_path, "w", encoding="utf-8") as f:
        for caption in webvtt.read(path):
            start = time.str_to_timedelta(caption.start)
            # webvtt-py already removes tags from the text, but not entities.
            text = html.unescape(caption.text.replace("\n", " "))
            f.write(f"[{time.timedelta_to_simple_str(start)}]{text}\n")
    return lrc_path


def check_repeats(path: str) -> None:
    """Print a warning for each run of 3 or more consecutive identical captions."""
    # TODO: Accept arbitrary number of repeated captions.
    relative_path = os.path.relpath(path)
    runs = itertools.groupby(numbered_captions(path), key=lambda item: item[1].text)
    for text, group in runs:
        run = list(group)
        if len(run) < MIN_REPEATS:
            continue
        line_number, first = run[0]
        last = run[-1][1]
        printer.print_warning(
            f"Repeated caption from {first.start} to {last.end}",
            f"{relative_path}:{line_number}",
        )
        print(text)


def fetch_patterns(path: str) -> list[dict[str, Any]]:
    """Read a CSV file of patterns into one dictionary per row.

    Each row gets an extra "Regex" key with its "Pattern" column compiled
    case-insensitively.
    """
    with open(path, "r", encoding="utf-8") as csvfile:
        patterns = list(csv.DictReader(csvfile))
    for pattern in patterns:
        pattern["Regex"] = re.compile(pattern["Pattern"], re.IGNORECASE)
    return patterns


def fix_mistakes(
    replacements: list[dict[str, Any]], path: str, skip_flagged: bool = False
) -> bool:
    """Apply replacements from fetch_patterns to a transcript's text lines.

    Replacements are applied in order, each to the result of the previous ones,
    and can refer to groups as $n (a literal $ isn't supported). Those flagged for
    review ("Warning" is "Y") print a warning, or are skipped with skip_flagged.
    Return whether the transcript changed.
    """
    relative_path = os.path.relpath(path)
    with open(path, "r", encoding="utf-8") as f:
        transcript_lines = f.read().splitlines()
    changed = False
    for i, line in enumerate(transcript_lines):
        if line == "" or " --> " in line:
            continue
        for replacement_entry in replacements:
            flagged = replacement_entry["Warning"] == "Y"
            if flagged and skip_flagged:
                continue
            regex = replacement_entry["Regex"]
            new_line = regex.sub(
                replacement_entry["Replacement"].replace("$", "\\"), line
            )
            if new_line == line:
                continue
            if flagged:
                printer.print_warning(
                    f'Replaced with "{new_line}"', f"{relative_path}:{i + 1}"
                )
                printer.print_with_highlight(line, regex)
            line = new_line
            changed = True
        transcript_lines[i] = line
    if changed:
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(transcript_lines))
            f.write("\n")
    return changed


def highlight_ambiguities(highlights: list[dict[str, Any]], path: str) -> None:
    """Print the lines that match highlights from fetch_patterns, for review.

    Also warn if the FWMC Morning introduction is missing.
    """
    relative_path = os.path.relpath(path)
    with open(path, "r", encoding="utf-8") as f:
        transcript_content = f.read()
    transcript_lines = transcript_content.splitlines()
    # Detect and highlight potential mistakes that might actually be correct
    # for manual review
    # TODO: Move the introduction check out of common if another show needs this
    # module.
    if INTRODUCTION_PATTERN not in transcript_content:
        printer.print_warning("Potential missing introduction", relative_path)
    for highlight in highlights:
        reason = highlight["Reason"]
        regex = highlight["Regex"]
        for i, line in enumerate(transcript_lines):
            if regex.search(line):
                printer.print_info(
                    f"Potential ambiguity: {reason}", f"{relative_path}:{i + 1}"
                )
                printer.print_with_highlight(line, regex)
