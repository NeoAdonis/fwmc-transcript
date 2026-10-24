"""Tests for the common.convert_to_wav script."""

import runpy

import pytest

from common import media


@pytest.fixture
def calls(monkeypatch):
    """Replace common.media.convert_to_wav with a fake that records its calls."""
    recorded = []

    def fake_convert_to_wav(*args, **kwargs):
        recorded.append((args, kwargs))

    monkeypatch.setattr(media, "convert_to_wav", fake_convert_to_wav)
    return recorded


def _bound_args(args, kwargs):
    """Map a recorded call to convert_to_wav onto its parameter names."""
    names = ["path", "new_base_name", "start_from", "end_at"]
    bound = dict(zip(names, args))
    bound.update(kwargs)
    return bound


@pytest.mark.parametrize(
    ("argv", "expected_path", "expected_name"),
    [
        ([], "audio.wav", "audio_converted"),
        (["--path", "in/episode.m4a"], "in/episode.m4a", "audio_converted"),
        (["--new_base_name", "episode"], "audio.wav", "episode"),
        (
            ["--path", "in/episode.m4a", "--new_base_name", "episode"],
            "in/episode.m4a",
            "episode",
        ),
    ],
)
def test_passes_path_and_name(monkeypatch, calls, argv, expected_path, expected_name):
    """The path and base name, or their defaults, are passed to convert_to_wav."""
    monkeypatch.setattr("sys.argv", ["convert_to_wav.py", *argv])

    runpy.run_module("common.convert_to_wav", run_name="__main__")

    assert len(calls) == 1
    bound = _bound_args(*calls[0])
    assert bound["path"] == expected_path
    assert bound["new_base_name"] == expected_name


def test_does_not_trim(monkeypatch, calls):
    """The conversion is called without trimming arguments, or with empty ones."""
    monkeypatch.setattr(
        "sys.argv",
        ["convert_to_wav.py", "--path", "a.mp3", "--new_base_name", "b"],
    )

    runpy.run_module("common.convert_to_wav", run_name="__main__")

    assert len(calls) == 1
    bound = _bound_args(*calls[0])
    assert bound.get("start_from", "") == ""
    assert bound.get("end_at", "") == ""


def test_propagates_errors(monkeypatch):
    """Errors raised by convert_to_wav aren't caught by the script."""

    def failing_convert_to_wav(*args, **kwargs):
        raise RuntimeError("FFmpeg failed")

    monkeypatch.setattr(media, "convert_to_wav", failing_convert_to_wav)
    monkeypatch.setattr("sys.argv", ["convert_to_wav.py"])

    with pytest.raises(RuntimeError, match="FFmpeg failed"):
        runpy.run_module("common.convert_to_wav", run_name="__main__")


def test_does_nothing_when_imported(monkeypatch, calls):
    """Running the module under a name other than __main__ doesn't convert."""
    monkeypatch.setattr("sys.argv", ["convert_to_wav.py"])

    runpy.run_module("common.convert_to_wav")

    assert calls == []
