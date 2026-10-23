"""Tests for the common.media module."""

import shutil
import subprocess
import wave
from typing import ClassVar

import pytest
from yt_dlp import YoutubeDL

from common import media

FAKE_FFMPEG = "/usr/bin/ffmpeg"
URL = "https://www.youtube.com/watch?v=Qd7ohtlOOkQ"


def mock_ffmpeg(monkeypatch, path):
    """Make media find FFmpeg at the given path, or not at all if it's None."""
    monkeypatch.setattr(media.shutil, "which", lambda _: path)


@pytest.fixture
def run_calls(monkeypatch):
    """Record the commands passed to subprocess.run instead of running them."""
    mock_ffmpeg(monkeypatch, FAKE_FFMPEG)
    calls = []
    monkeypatch.setattr(
        media.subprocess, "run", lambda args, **kwargs: calls.append((args, kwargs))
    )
    return calls


class FakeYoutubeDL:
    """Stand-in for YoutubeDL that records its options and downloaded URLs."""

    instances: ClassVar[list["FakeYoutubeDL"]] = []
    on_download = None  # Optional callback to simulate files written by yt-dlp.

    def __init__(self, opts):
        self.opts = opts
        self.urls = []
        FakeYoutubeDL.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def download(self, urls):
        """Record the URLs and run the on_download callback, if any."""
        self.urls.extend(urls)
        if FakeYoutubeDL.on_download:
            FakeYoutubeDL.on_download()


@pytest.fixture
def fake_ydl(monkeypatch):
    """Replace YoutubeDL with FakeYoutubeDL and return the class."""
    mock_ffmpeg(monkeypatch, FAKE_FFMPEG)
    monkeypatch.setattr(FakeYoutubeDL, "instances", [])
    monkeypatch.setattr(FakeYoutubeDL, "on_download", None)
    monkeypatch.setattr(media, "YoutubeDL", FakeYoutubeDL)
    return FakeYoutubeDL


# convert_to_wav


def test_convert_to_wav_requires_ffmpeg(monkeypatch, tmp_path):
    """Conversion fails if FFmpeg isn't installed."""
    mock_ffmpeg(monkeypatch, None)
    with pytest.raises(RuntimeError):
        media.convert_to_wav(str(tmp_path / "audio.webm"), "audio")


def test_convert_to_wav_command(run_calls, tmp_path):
    """FFmpeg is called to write a 16-bit 44.1 kHz stereo WAV next to the source."""
    source = str(tmp_path / "audio.webm")
    media.convert_to_wav(source, "converted")
    assert run_calls == [
        (
            [
                FAKE_FFMPEG,
                "-y",
                "-v",
                "warning",
                "-i",
                source,
                "-vn",
                "-acodec",
                "pcm_s16le",
                "-ar",
                "44100",
                "-ac",
                "2",
                str(tmp_path / "converted.wav"),
            ],
            {"check": True},
        )
    ]


@pytest.mark.parametrize(
    ("start_from", "end_at", "expected"),
    [
        ("00:01:00", "", ["-ss", "00:01:00"]),
        ("", "00:02:00", ["-to", "00:02:00"]),
        ("00:01:00", "00:02:00", ["-ss", "00:01:00", "-to", "00:02:00"]),
    ],
)
def test_convert_to_wav_trim(run_calls, tmp_path, start_from, end_at, expected):
    """The start and end times are passed to FFmpeg as output options."""
    media.convert_to_wav(str(tmp_path / "audio.webm"), "converted", start_from, end_at)
    args = run_calls[0][0]
    # The trim options must come right before the output path.
    assert args[-len(expected) - 1 : -1] == expected
    assert args[-1] == str(tmp_path / "converted.wav")


def test_convert_to_wav_replaces_existing_output(run_calls, tmp_path):
    """An existing WAV file is converted again, as it may be incomplete or stale."""
    (tmp_path / "converted.wav").touch()
    media.convert_to_wav(str(tmp_path / "audio.webm"), "converted")
    assert len(run_calls) == 1


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="FFmpeg not installed")
def test_convert_to_wav_with_ffmpeg(tmp_path):
    """A real conversion replaces the WAV file with a trimmed one."""
    source = tmp_path / "audio.ogg"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:sample_rate=22050:duration=3",
            "-ac",
            "1",
            str(source),
        ],
        check=True,
    )
    (tmp_path / "converted.wav").write_bytes(b"stale")
    media.convert_to_wav(str(source), "converted", "00:00:01", "00:00:02")
    with wave.open(str(tmp_path / "converted.wav")) as wav:
        assert wav.getframerate() == 44100
        assert wav.getnchannels() == 2
        assert wav.getsampwidth() == 2
        assert wav.getnframes() / wav.getframerate() == pytest.approx(1, abs=0.05)


# get_video_audio


def test_get_video_audio_requires_ffmpeg(monkeypatch, tmp_path):
    """Downloading fails if FFmpeg isn't installed."""
    mock_ffmpeg(monkeypatch, None)
    with pytest.raises(RuntimeError):
        media.get_video_audio(URL, str(tmp_path))


@pytest.mark.usefixtures("fake_ydl")
def test_get_video_audio_creates_output_dir(tmp_path):
    """The output directory is created, including its parents."""
    output_dir = tmp_path / "nested" / "audio"
    media.get_video_audio(URL, str(output_dir))
    assert output_dir.is_dir()


def test_get_video_audio_downloads_audio_only(fake_ydl, tmp_path):
    """By default, only the audio is downloaded into the output directory."""
    media.get_video_audio(URL, str(tmp_path))
    [ydl] = fake_ydl.instances
    assert ydl.urls == [URL]
    assert ydl.opts["ffmpeg_location"] == FAKE_FFMPEG
    assert ydl.opts["format"] == "ba/b"
    assert ydl.opts["paths"] == {"home": str(tmp_path)}
    assert ydl.opts["download_archive"] == str(tmp_path / "archive.txt")
    assert ydl.opts["allow_playlist_files"] is False


@pytest.mark.parametrize(
    ("release_date", "expected"), [("20230731", "20230731"), (None, "20230730")]
)
def test_get_video_audio_date_folders(fake_ydl, tmp_path, release_date, expected):
    """Files are saved by release date, falling back to the upload date."""
    media.get_video_audio(URL, str(tmp_path), download_video=True)
    audio_ydl, video_ydl = fake_ydl.instances
    with YoutubeDL({"quiet": True}) as ydl:
        templates = [
            *audio_ydl.opts["outtmpl"].values(),
            *(file for _, file in audio_ydl.opts["print_to_file"]["video"]),
            video_ydl.opts["outtmpl"],
        ]
        for template in templates:
            path = ydl.evaluate_outtmpl(
                template,
                {
                    "id": "Qd7ohtlOOkQ",
                    "ext": "webm",
                    "release_date": release_date,
                    "upload_date": "20230730",
                },
            )
            assert path.startswith(f"{expected}/")


def test_get_video_audio_downloads_video(fake_ydl, tmp_path):
    """If requested, the video is downloaded after the audio."""
    media.get_video_audio(URL, str(tmp_path), download_video=True)
    audio_ydl, video_ydl = fake_ydl.instances
    assert audio_ydl.urls == video_ydl.urls == [URL]
    assert video_ydl.opts["paths"] == {"home": str(tmp_path)}
    assert video_ydl.opts["outtmpl"].endswith("/video.%(ext)s")


@pytest.mark.parametrize(
    ("info", "skipped"),
    [
        ({"_type": "playlist", "id": "PL123"}, False),
        ({"live_status": "not_live"}, False),
        ({"live_status": "is_live"}, True),
        ({"live_status": "is_upcoming"}, True),
        ({"playlist_index": 1, "live_status": "not_live"}, False),
        ({"playlist_index": 1, "live_status": "was_live"}, False),
        ({"playlist_index": 1, "live_status": "post_live"}, False),
        ({"playlist_index": 1, "live_status": "is_live"}, True),
        ({"playlist_index": 1, "live_status": "is_upcoming"}, True),
    ],
)
def test_get_video_audio_match_filter(fake_ydl, tmp_path, info, skipped):
    """Live and upcoming videos are skipped, whether in a playlist or not."""
    media.get_video_audio(URL, str(tmp_path))
    match_filter = fake_ydl.instances[0].opts["match_filter"]
    result = match_filter(info, incomplete=False)
    assert (result is not None) == skipped


def test_get_video_audio_keeps_latest_title(fake_ydl, tmp_path):
    """Title files keep only the ID and title written by the latest download."""
    episode_dir = tmp_path / "20230731"
    episode_dir.mkdir()
    title_path = episode_dir / "20230731.title"
    title_path.write_text("old_id\nOld title\n", encoding="utf-8")

    def append_title():
        with open(title_path, "a", encoding="utf-8") as f:
            f.write("Qd7ohtlOOkQ\nNew title\n")

    fake_ydl.on_download = append_title
    media.get_video_audio(URL, str(tmp_path))
    assert title_path.read_text(encoding="utf-8") == "Qd7ohtlOOkQ\nNew title\n"
