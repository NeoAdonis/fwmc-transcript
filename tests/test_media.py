"""Unit tests for the common.media module."""

import os
import unittest
from unittest.mock import patch
from common.media import convert_to_wav, get_video_audio


class TestMedia(unittest.TestCase):
    """Unit tests for the common.media module."""

    @patch("common.media.os.path.exists")
    @patch("common.media.shutil.which")
    @patch("common.media.subprocess.run")
    def test_convert_to_wav_success(
        self, mock_subprocess_run, mock_shutil_which, mock_path_exists
    ):
        """Test the convert_to_wav function with a successful conversion."""
        mock_shutil_which.return_value = "/usr/bin/ffmpeg"
        mock_path_exists.return_value = False
        convert_to_wav("test_audio.mp3", "test_audio_converted")
        mock_subprocess_run.assert_called_once_with(
            [
                "/usr/bin/ffmpeg",
                "-v",
                "warning",
                "-i",
                "test_audio.mp3",
                "-vn",
                "-acodec",
                "pcm_s16le",
                "-ar",
                "44100",
                "-ac",
                "2",
                os.path.join(
                    os.path.dirname("test_audio.mp3"), "test_audio_converted.wav"
                ),
            ],
            check=True,
        )

    @patch("common.media.shutil.which")
    def test_ffmpeg_not_installed(self, mock_shutil_which):
        """Test the convert_to_wav function when ffmpeg is not installed"""
        mock_shutil_which.return_value = None
        with self.assertRaises(RuntimeError):
            convert_to_wav("test_audio.mp3", "test_audio_converted")

    @patch("common.media.os.path.exists")
    @patch("common.media.shutil.which")
    @patch("common.media.subprocess.run")
    def test_convert_to_wav_file_exists(
        self, mock_subprocess_run, mock_shutil_which, mock_path_exists
    ):
        """Test the convert_to_wav function when the output file already exists."""
        mock_shutil_which.return_value = "/usr/bin/ffmpeg"
        mock_path_exists.return_value = True
        convert_to_wav("test_audio.mp3", "test_audio_converted")
        mock_subprocess_run.assert_not_called()

    @patch("common.media.shutil.which")
    def test_yt_dlp_not_installed(self, mock_shutil_which):
        """Test the get_video_audio function when yt-dlp is not installed"""
        mock_shutil_which.return_value = None
        with self.assertRaises(RuntimeError):
            get_video_audio(
                "https://www.youtube.com/playlist?list=PL59FEE129ADFF2B12",
                "test_audio",
                False,
            )


if __name__ == "__main__":
    unittest.main()
