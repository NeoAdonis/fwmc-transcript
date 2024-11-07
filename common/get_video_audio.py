"""Common script to download audio from a YouTube playlist using yt-dlp."""

import argparse
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
        "--output_dir",
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

    get_video_audio(args.url, args.output_dir, args.download_video)
