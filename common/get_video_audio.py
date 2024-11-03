"""Common script to download audio from a YouTube playlist using yt-dlp."""

import argparse
import os
import subprocess
import shutil

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

url = args.url
output_folder = args.output_folder
download_video = args.download_video

# Check if the output folder exists, and create it if it doesn't
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Check if the required dependencies are installed
dependencies_met = True
if not shutil.which("yt-dlp"):
    print("yt-dlp not found. Please make sure that yt-dlp is installed.")
    dependencies_met = False
if not shutil.which("ffmpeg"):
    print("ffmpeg not found. Please make sure that ffmpeg is installed.")
    dependencies_met = False
if not dependencies_met:
    raise RuntimeError("Dependencies not met")

# Download best source audio for better transcription and save some metadata
subprocess.run(
    [
        shutil.which("yt-dlp"),
        "-q",
        "--progress",
        "-f",
        "ba/b",
        "-P",
        output_folder,
        "--download-archive",
        os.path.join(output_folder, "archive.txt"),
        "--match-filter",
        "!is_live & live_status!=is_upcoming & availability=public",
        "--print-to-file",
        "%(id)s",
        "%(release_date)s/%(release_date)s.title",
        "--print-to-file",
        "%(title)s",
        "%(release_date)s/%(release_date)s.title",
        "--write-description",
        "-o",
        "description:%(release_date)s/%(release_date)s",
        "--write-thumbnail",
        "-o",
        "thumbnail:%(release_date)s/thumbnail",
        "-o",
        "%(release_date)s/audio.%(ext)s",
        "-N",
        "3",
        url,
    ],
    check=True,
)

# Remove the "NA" folder if it exists
na_folder = os.path.join(output_folder, "NA")
if os.path.exists(na_folder):
    shutil.rmtree(na_folder)

# yt-dlp appends new info to title files if it exists already; keep only the latest info
for root, dirs, files in os.walk(output_folder):
    for file in files:
        if file.endswith(".title"):
            title_path = os.path.join(root, file)
            with open(title_path, "r", encoding="utf-8") as f:
                content = f.readlines()
            with open(title_path, "w", encoding="utf-8") as f:
                f.writelines(content[-2:])

# If specified, download smallest video with at least 480p resolution for reference
if download_video:
    subprocess.run(
        [
            shutil.which("yt-dlp"),
            "-q",
            "--progress",
            "-f",
            "bv*[height>=480]+ba/b[height>=480]/bv*+ba/b",
            "-S",
            "+size,+br,+res,+fps",
            "-P",
            output_folder,
            "-o",
            "%(release_date)s/video.%(ext)s",
            "-N",
            "3",
            url,
        ],
        check=True,
    )
