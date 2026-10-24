"""Convert existing transcripts to LRC files for easier processing by external tools
such as LLMs."""

import argparse
import os

from common import transcript


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert existing transcripts to LRC files for easier processing "
        + "by external tools such as LLMs"
    )
    parser.add_argument(
        "--transcripts_dir",
        type=str,
        default="transcripts",
        help="Path to the transcripts directory",
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Date of the transcript to convert in format YYYYMMDD",
    )
    return parser.parse_args()


def main():
    """Convert existing transcripts to LRC files for easier processing by external
    tools such as LLMs."""

    # Paths are relative to the data in the morning directory at the repository root
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../morning"))

    args = parse_args()

    for root, _, files in os.walk(os.path.join(args.transcripts_dir, args.date)):
        for file in files:
            if file.endswith(".vtt"):
                print(transcript.to_lrc(os.path.join(root, file)))


if __name__ == "__main__":
    main()
