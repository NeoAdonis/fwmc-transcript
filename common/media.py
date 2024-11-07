"""This module contains common functions for manipulating media files."""

import os
import shutil
import subprocess


def convert_to_wav(path: str, new_base_name: str):
    """Convert the audio file to WAV format using FFmpeg."""

    # Check if the required dependencies are installed
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is None:
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
                ffmpeg_path,
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


def get_video_audio(url: str, output_dir: str, download_video: bool = False):
    """Download the audio and descriptions of the YouTube playlist or video using yt-dlp."""

    # Check if the required dependencies are installed
    yt_dlp_path = shutil.which("yt-dlp")
    if yt_dlp_path is None:
        print("yt-dlp not found. Please make sure that yt-dlp is installed.")
        raise RuntimeError("Dependencies not met")

    # Check if the output folder exists, and create it if it doesn't
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Download best source audio for better transcription and save some metadata
    subprocess.run(
        [
            yt_dlp_path,
            "-q",
            "--progress",
            "-f",
            "ba/b",
            "-P",
            output_dir,
            "--download-archive",
            os.path.join(output_dir, "archive.txt"),
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
    na_folder = os.path.join(output_dir, "NA")
    if os.path.exists(na_folder):
        shutil.rmtree(na_folder)

    # yt-dlp appends new info to title files if it exists already; keep only the latest info
    for root, _, files in os.walk(output_dir):
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
                yt_dlp_path,
                "-q",
                "--progress",
                "-f",
                "bv*[height>=480]+ba/b[height>=480]/bv*+ba/b",
                "-S",
                "+size,+br,+res,+fps",
                "-P",
                output_dir,
                "-o",
                "%(release_date)s/video.%(ext)s",
                "-N",
                "3",
                url,
            ],
            check=True,
        )
