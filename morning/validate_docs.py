"""Validate the structure and content of the transcripts, summaries and metadata files."""

import argparse
import os
import json
import subprocess
import shutil
from common import printer, transcript

# Define constants
SUMMARY_MAX_LENGTH = 4000
HIGHLIGHTS_FILE = "config/highlights.csv"
REPLACEMENTS_FILE = "config/replacements.csv"

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Validate the structure & content of transcripts, summaries and metadata files."
    )
    parser.add_argument(
        "--transcripts_dir",
        type=str,
        default="transcripts",
        help="Path to the transcripts directory",
    )
    args = parser.parse_args()

    transcripts_dir = args.transcripts_dir

    transcripts_dir_walker = os.walk(transcripts_dir)

    replacements = transcript.fetch_patterns(REPLACEMENTS_FILE)
    highlights = transcript.fetch_patterns(HIGHLIGHTS_FILE)

    print("Validating file structure, metadata and transcripts...")
    for root, dirs, files in transcripts_dir_walker:
        for file in files:
            # Check metadata
            if file == "metadata.json":
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                relative_path = os.path.relpath(os.path.join(root, file), os.getcwd())
                if metadata.get("episode") == "???":
                    printer.print_error("Episode name/number not set", relative_path)
                if isinstance(metadata["episode"], int) and metadata["isSpecial"]:
                    printer.print_error(
                        "Numbered episode marked as special", relative_path
                    )
            # Check transcripts
            if file == "transcript.vtt":
                transcript.check_repeats(root, file)
                if transcript.fix_mistakes(replacements, root, file, True):
                    printer.print_info("File changed", relative_path)
                transcript.highlight_ambiguities(highlights, root, file)
        # Look for missing files
        for directory in dirs:
            summary_path = os.path.join(root, directory, "summary.md")
            transcript_path = os.path.join(root, directory, "transcript.vtt")
            relative_path = os.path.relpath(summary_path, os.getcwd())
            if not os.path.exists(summary_path):
                printer.print_error("No summary file found", relative_path)
            if os.path.exists(transcript_path):
                file = transcript_path
            else:
                printer.print_error("No transcript file found", relative_path)

    print("Validating summaries...")

    # Lint summaries
    npm_command = shutil.which("bun")
    if not npm_command:
        npm_command = shutil.which("npm")
    if npm_command is None:
        printer.print_warning(
            "npm or bun command not found. Summaries linting skipped."
        )
    else:
        subprocess.run([npm_command, "run", "lint-summaries"], check=True)

    # Check for long summaries
    # This is done after linting as summaries might have been changed
    for root, _, files in transcripts_dir_walker:
        for file in files:
            if file == "summary.md":
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    content = f.read()
                length = len(content)
                relative_path = os.path.relpath(os.path.join(root, file), os.getcwd())
                if length > SUMMARY_MAX_LENGTH:
                    printer.print_error(
                        f"File too long ({length} characters, max {SUMMARY_MAX_LENGTH})",
                        relative_path,
                    )
