"""Download the audio and descriptions of the FUWAMOCO morning playlist."""

import argparse
import os
import sys

from common.media import get_video_audio

if __name__ == "__main__":
    # Paths are relative to the data in the morning directory at the repository root
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../morning"))

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Download the audio and descriptions of FWMC Morning episodes."
    )
    parser.add_argument(
        "--url",
        type=str,
        default="https://www.youtube.com/playlist?list="
        + "PLf4O_VcbYo27DpnCJZXRsxov6_DD2Q1NS",
        help="URL of the YouTube playlist or video",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="audio",
        help="Path to the output directory",
    )
    parser.add_argument(
        "--download_video",
        action="store_true",
        help="Download the video instead of audio only",
    )
    args = parser.parse_args()

    output_dir = os.path.join(os.getcwd(), args.output_dir)

    success = get_video_audio(args.url, output_dir, args.download_video)

    # Find the first time when there's a blank line after a non-blank line in the
    # description files, then keep only the lines before that
    for root, _, files in os.walk(output_dir):
        for file in files:
            if file.endswith(".description"):
                description_path = os.path.join(root, file)
                with open(description_path, "r", encoding="utf-8") as f:
                    content = f.readlines()
                for i in range(1, len(content)):
                    if content[i - 1].strip() != "" and content[i].strip() == "":
                        with open(description_path, "w", encoding="utf-8") as f:
                            f.writelines(content[:i])
                        break

    if not success:
        sys.exit("Some downloads failed; see the errors above.")
