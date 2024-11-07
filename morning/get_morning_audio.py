"""Download the audio and descriptions of the FUWAMOCO morning playlist."""

import argparse
import os
from common.media import get_video_audio

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Validate the structure and content of the transcripts and metadata files."
    )
    parser.add_argument(
        "--url",
        type=str,
        default="https://www.youtube.com/playlist?list=PLf4O_VcbYo27DpnCJZXRsxov6_DD2Q1NS",
        help="URL of the YouTube playlist or video",
    )
    parser.add_argument(
        "--output_folder",
        type=str,
        default="audio",
        help="Path to the output directory",
    )
    parser.add_argument(
        "--download_video",
        type=bool,
        default=False,
        help="True if the video should be downloaded instead of audio only, False otherwise",
    )
    args = parser.parse_args()

    output_folder = args.output_folder

    get_video_audio(args.url, output_folder, args.download_video)

    # Find the first time when there's a blank line after a non-blank line in the description files,
    # then keep only the lines before that
    for root, _, files in os.walk(output_folder):
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
