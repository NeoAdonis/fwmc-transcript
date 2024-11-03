"""Simple script to convert an audio file to WAV format using FFmpeg."""

import argparse
import os
import shutil
import subprocess

# Parse command line arguments
parser = argparse.ArgumentParser(
    description="Validate the structure and content of the transcripts and metadata files."
)
parser.add_argument(
    "--path",
    type=str,
    default="audio.wav",
    help="Path to the audio file to convert",
)
parser.add_argument(
    "--new_base_name",
    type=str,
    default="audio_converted",
    help="Base name for the converted audio file",
)
args = parser.parse_args()

path = args.path
new_base_name = args.new_base_name

# Check if the required dependencies are installed
FFMPEG_PATH = shutil.which("ffmpeg")
if FFMPEG_PATH is None:
    print("ffmpeg not found. Please make sure that ffmpeg is installed.")
    raise RuntimeError("Dependencies not met")

# Determine the parent folder of the given path
parent_folder = os.path.dirname(path)

# Construct the path for the converted audio file
converted_audio = os.path.join(parent_folder, f"{new_base_name}.wav")

# Check if the converted audio file already exists
if not os.path.exists(converted_audio):
    # Use ffmpeg to convert the audio file
    subprocess.run(
        [
            FFMPEG_PATH,
            "-v",
            "warning",
            "-i",
            path,
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "44100",
            "-ac",
            "2",
            converted_audio,
        ],
        check=True,
    )
