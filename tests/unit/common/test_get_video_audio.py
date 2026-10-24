"""Tests for the common.get_video_audio script."""

import runpy

import pytest

from common import media


@pytest.mark.parametrize("success", [True, False])
def test_exit_code(monkeypatch, tmp_path, success):
    """The script exits with code 1 if any download failed."""
    calls = []

    def fake_get_video_audio(*args):
        calls.append(args)
        return success

    monkeypatch.setattr(media, "get_video_audio", fake_get_video_audio)
    monkeypatch.setattr("sys.argv", ["get_video_audio", "--output_dir", str(tmp_path)])
    if success:
        runpy.run_module("common.get_video_audio", run_name="__main__")
    else:
        with pytest.raises(SystemExit) as exc_info:
            runpy.run_module("common.get_video_audio", run_name="__main__")
        assert exc_info.value.code != 0
    assert len(calls) == 1
