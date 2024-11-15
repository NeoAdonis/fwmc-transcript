"""Simple script to convert an audio file to WAV format using FFmpeg."""

import argparse

from common.media import convert_to_wav

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Convert an audio file to WAV using FFmpeg."
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

    convert_to_wav(args.path, args.new_base_name)
