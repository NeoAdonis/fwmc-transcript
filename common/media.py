"""This module contains common functions for manipulating media files."""

import os
import shutil
import subprocess

from yt_dlp import YoutubeDL


def convert_to_wav(path: str, new_base_name: str, start_from="", end_at=""):
    """Convert the audio file to WAV format using FFmpeg.

    The WAV file is written next to the source file, replacing any existing file
    with the same name, since it may be incomplete or have been trimmed differently.
    """

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
        "-y",
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

    subprocess.run(args, check=True)


def get_video_audio(url: str, output_dir: str, download_video: bool = False) -> bool:
    """Download audio and descriptions of a YouTube playlist or video using yt-dlp.

    Each video is saved in a folder named after its release date (YYYYMMDD), or its
    upload date if it wasn't a live stream or premiere.

    Errors in a video are printed and don't stop the remaining downloads. Return
    whether all downloads succeeded.
    """

    def published_videos_filter(info, incomplete):
        """Download only VODs."""
        # Playlists have no live status, so they aren't filtered out. Recordings of
        # streams that just ended (post_live) may be incomplete while YouTube is
        # still processing them.
        if info.get("live_status") in ("is_live", "is_upcoming", "post_live"):
            return "Video not available yet"

    # Check if the required dependencies are installed
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is None:
        print("ffmpeg not found. Please make sure that ffmpeg is installed.")
        raise RuntimeError("Dependencies not met")

    # Check if the output folder exists, and create it if it doesn't
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Only live streams and premieres have a release date
    date = "%(release_date,upload_date)s"

    # Download best source audio for better transcription and save some metadata.
    # The yt-dlp stubs bundled with Pylance (typeshed) expect a single tuple per
    # print_to_file key, but yt-dlp takes a list of them.
    with YoutubeDL(
        {  # pyright: ignore[reportArgumentType]
            "quiet": True,
            "ignoreerrors": True,
            "ffmpeg_location": ffmpeg_path,
            "format": "ba/b",
            "paths": {"home": output_dir},
            "download_archive": os.path.join(output_dir, "archive.txt"),
            "match_filter": published_videos_filter,
            "print_to_file": {
                "video": [
                    ("%(id)s", f"{date}/{date}.title"),
                    ("%(title)s", f"{date}/{date}.title"),
                ],
            },
            "outtmpl": {
                "description": f"{date}/{date}",
                "thumbnail": f"{date}/thumbnail",
                "default": f"{date}/audio.%(ext)s",
            },
            "writedescription": True,
            "writethumbnail": True,
            "allow_playlist_files": False,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                }
            ],
            "noplaylist": False,
            "concurrent_fragment_downloads": 3,
        }
    ) as ydl:
        success = ydl.download([url]) == 0

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
        with YoutubeDL(
            {
                "quiet": True,
                "ignoreerrors": True,
                "ffmpeg_location": ffmpeg_path,
                "format": "bv*[height>=480]+ba/b[height>=480]/bv*+ba/b",
                "format_sort": ["+size", "+br", "+res", "+fps"],
                "paths": {"home": output_dir},
                "download_archive": os.path.join(output_dir, "video_archive.txt"),
                "match_filter": published_videos_filter,
                "outtmpl": f"{date}/video.%(ext)s",
                "concurrent_fragment_downloads": 3,
            }
        ) as ydl:
            success = ydl.download([url]) == 0 and success

    return success
