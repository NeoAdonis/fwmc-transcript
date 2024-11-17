"""Fix captions. EXPERIMENTAL."""

import argparse
import os

import torch
import whisperx

from common import asrtransform, printer, transcript

# Define constants
SUMMARY_MAX_LENGTH = 4000
HIGHLIGHTS_FILE = "config/highlights.csv"
REPLACEMENTS_FILE = "config/replacements.csv"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Fix captions")
    parser.add_argument(
        "--audio_dir",
        type=str,
        default="audio",
        help="Path to the audio directory",
    )
    parser.add_argument(
        "--transcripts_dir",
        type=str,
        default="transcripts",
        help="Path to the transcripts directory",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="large-v3",
        help="Whisper model to use for transcription",
    )
    args = parser.parse_args()

    audio_dir = args.audio_dir
    transcripts_dir = args.transcripts_dir

    transcripts_dir_walker = os.walk(transcripts_dir)

    replacements = transcript.fetch_patterns(REPLACEMENTS_FILE)
    highlights = transcript.fetch_patterns(HIGHLIGHTS_FILE)

    print("Loading transcription models...")
    model = whisperx.load_model(
        args.model,
        DEVICE,
        language="en",
    )
    align_model, align_metadata = whisperx.load_align_model(
        language_code="en", device=DEVICE
    )

    print("Reviewing captions...")
    for root, dirs, files in transcripts_dir_walker:
        for file in files:
            if file == "transcript.vtt":
                relative_path = os.path.relpath(os.path.join(root, file), os.getcwd())
                REPEATS_FIXED = asrtransform.fix_repeats(
                    root, file, audio_dir, model, align_model, align_metadata
                )
                if REPEATS_FIXED:
                    printer.print_info("Repeated sections rewritten", relative_path)
                if transcript.fix_mistakes(replacements, root, file, True):
                    if not REPEATS_FIXED:
                        printer.print_info("Mistakes fixed", relative_path)
                # transcript.highlight_ambiguities(highlights, root, file)
