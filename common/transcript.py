"""This module contains functions related to transcripts."""

import os
import re
import webvtt
import whisperx
from common import printer

# Define constants
INTRODUCTION_PATTERN = "Hallo hallo BAU BAU"
BATCH_SIZE = 16


def transcribe_audio(audio_path, model, align_model, align_metadata, new_output_dir):
    """Transcribe the audio file using the specified model"""
    audio = whisperx.load_audio(audio_path)
    result = model.transcribe(audio, BATCH_SIZE, language="en")
    result = whisperx.align(
        result["segments"],
        align_model,
        align_metadata,
        audio,
        "cuda",
        return_char_alignments=False,
    )

    writer = whisperx.utils.get_writer("vtt", new_output_dir)
    writer(result, audio_path)


# TODO: Consider merging this with the fix_mistakes function
def check_captions(root, file):
    """Check captions in a transcript."""
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
                    f"Repeated caption from {last_unique_caption.start} to {prev_caption.end}",
                    f"{relative_path}:{last_unique_ln}",
                )
                print(last_unique_caption.text)
            last_unique_id = i
            last_unique_ln = ln
            last_unique_caption = caption
        prev_caption = caption
        i += 1
        ln += 3


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
        replacement = replacement_entry["Replacement"]
        warning = (replacement_entry["Warning"] == "Y") or warn_only
        for i, line in enumerate(transcript_lines):
            if re.search(pattern, line, re.IGNORECASE):
                new_line = re.sub(pattern, replacement, line, flags=re.IGNORECASE)
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
                    if not warn_only:
                        changed = True
                        transcript_lines[i] = new_line
    if changed:
        with open(os.path.join(directory, transcript_file), "w", encoding="utf-8") as f:
            f.write("\n".join(transcript_lines))


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
        for i, line in enumerate(transcript_lines):
            if re.search(pattern, line, re.IGNORECASE):
                printer.print_info(
                    f"Potential ambiguity: {reason}", f"{relative_path}:{i+1}"
                )
                printer.print_with_highlight(line, pattern)
