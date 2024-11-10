"""Validate the structure and content of the transcripts, summaries and metadata files."""

import argparse
import csv
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
        description="Validate the structure and content of the transcripts, summaries and metadata files."
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

    with open(REPLACEMENTS_FILE, "r", encoding="utf-8") as csvfile:
        replacements = list(csv.DictReader(csvfile))
    with open(HIGHLIGHTS_FILE, "r", encoding="utf-8") as csvfile:
        highlights = list(csv.DictReader(csvfile))

    print("Validating transcripts...")

    for root, dirs, files in transcripts_dir_walker:
        for file in files:
            # Basic metadata checks
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
            # Basic transcript checks
            if file == "transcript.vtt":
                transcript.check_captions(root, file)
                transcript.fix_mistakes(replacements, root, file, True)
                transcript.highlight_ambiguities(highlights, root, file)

        # Check for missing files
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

    # Check summaries formatting
    npm_command = shutil.which("bun")
    if not npm_command:
        npm_command = shutil.which("npm")
    if npm_command is None:
        print("npm or bun command not found. Skipping linting of summaries.")
    else:
        subprocess.run([npm_command, "run", "lint-summaries"], check=True)

    # Check for long summaries
    # This is done after linting as the linting process may have changed the summaries
    for root, _, files in transcripts_dir_walker:
        for file in files:
            if file == "summary.md":
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    content = f.read()
                length = len(content)
                relative_path = os.path.relpath(os.path.join(root, file), os.getcwd())
                if length > SUMMARY_MAX_LENGTH:
                    print(
                        f"{relative_path} - File too long "
                        + f"({length} characters, max {SUMMARY_MAX_LENGTH})"
                    )
