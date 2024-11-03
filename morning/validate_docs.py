"""Validate the structure and content of the transcripts and metadata files."""

import argparse
import os
import json
import subprocess
import shutil

# Parse command line arguments
parser = argparse.ArgumentParser(
    description="Validate the structure and content of the transcripts and metadata files."
)
parser.add_argument(
    "--transcripts_folder",
    type=str,
    default="transcripts",
    help="Path to the transcripts directory",
)
args = parser.parse_args()

transcripts_folder = args.transcripts_folder

# Basic metadata checks
for root, dirs, files in os.walk(transcripts_folder):
    for file in files:
        if file == "metadata.json":
            with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                metadata = json.load(f)
            relative_path = os.path.relpath(os.path.join(root, file), os.getcwd())
            if metadata.get("episode") == "???":
                print(f"{relative_path} - Episode name/number not set")
            if isinstance(metadata.get("episode"), int) and metadata.get("isSpecial"):
                print(f"{relative_path} - Numbered episode marked as special")

# Check for missing summary files
for root, dirs, files in os.walk(transcripts_folder):
    for directory in dirs:
        summary_path = os.path.join(root, directory, "summary.md")
        relative_path = os.path.relpath(summary_path, os.getcwd())
        if not os.path.exists(summary_path):
            print(f"{relative_path} - No summary file found")

# Check summaries formatting
npm_command = shutil.which("bun")
if not npm_command:
    npm_command = shutil.which("npm")
subprocess.run([npm_command, "run", "lint-summaries"], check=True)

# Check for long summaries
for root, dirs, files in os.walk(transcripts_folder):
    for file in files:
        if file == "summary.md":
            with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                content = f.read()
            length = len(content)
            relative_path = os.path.relpath(os.path.join(root, file), os.getcwd())
            if length > 4000:
                print(f"{relative_path} - File too long ({length} characters)")
