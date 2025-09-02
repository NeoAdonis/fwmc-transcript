"""This module contains common functions for manipulating media files."""

import os
import shutil
import subprocess

from yt_dlp import YoutubeDL


def convert_to_wav(path: str, new_base_name: str, start_from="", end_at=""):
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

    # Construct the FFmpeg command
    args = [
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
    ]
    if start_from:
        args.extend(["-ss", start_from])
    if end_at:
        args.extend(["-to", end_at])
    args.append(converted_audio)

    # Check if the converted audio file already exists
    if not os.path.exists(converted_audio):
        # Use ffmpeg to convert the audio file
        subprocess.run(args, check=True)


def get_video_audio(url: str, output_dir: str, download_video: bool = False):
    """Download audio and descriptions of a YouTube playlist or video using yt-dlp."""

    def published_videos_filter(info, *, incomplete):  # pylint: disable=unused-argument
        """Download only VODs."""
        if info.get("playlist_index") is None:
            return  # Don't filter out playlists
        live_status = info.get("live_status")
        # availability = info.get("availability")
        if live_status == "is_live" or live_status == "is_upcoming":
            return "Video not available yet"

    # Check if the required dependencies are installed
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is None:
        print("ffmpeg not found. Please make sure that ffmpeg is installed.")
        raise RuntimeError("Dependencies not met")

    # Check if the output folder exists, and create it if it doesn't
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Download best source audio for better transcription and save some metadata
    ydl_opts = {
        "quiet": True,
        "ignoreerrors": True,
        "ffmpeg_location": ffmpeg_path,
        "format": "ba/b",
        "paths": {"home": output_dir},
        "download_archive": os.path.join(output_dir, "archive.txt"),
        "match_filter": published_videos_filter,
        "print_to_file": {
            "video": [
                ("%(id)s", "%(release_date)s/%(release_date)s.title"),
                ("%(title)s", "%(release_date)s/%(release_date)s.title"),
            ],
        },
        "outtmpl": {
            "description": "%(release_date)s/%(release_date)s",
            "thumbnail": "%(release_date)s/thumbnail",
            "default": "%(release_date)s/audio.%(ext)s",
        },
        "writedescription": True,
        "writethumbnail": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
            }
        ],
        "noplaylist": False,
        "concurrent_fragment_downloads": 3,
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # Remove the "NA" folder if it exists
    na_folder = os.path.join(output_dir, "NA")
    if os.path.exists(na_folder):
        shutil.rmtree(na_folder)

    # yt-dlp appends new info to title files if it exists already;
    # keep only the latest info
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
        video_opts = {
            "quiet": True,
            "format": "bv*[height>=480]+ba/b[height>=480]/bv*+ba/b",
            "format_sort": ["+size", "+br", "+res", "+fps"],
            "paths": {"home": output_dir},
            "outtmpl": "%(release_date)s/video.%(ext)s",
            "concurrent_fragment_downloads": 3,
        }
        with YoutubeDL(video_opts) as ydl:
            ydl.download([url])
