"""Tests for the scripts that download audio with common.media."""

import runpy

import pytest

from common import media


@pytest.mark.parametrize("module", ["common.get_video_audio", "morning.get_audio"])
@pytest.mark.parametrize("success", [True, False])
def test_exit_code(monkeypatch, tmp_path, module, success):
    """The scripts exit with code 1 if any download failed."""
    calls = []

    def fake_get_video_audio(*args):
        calls.append(args)
        return success

    monkeypatch.setattr(media, "get_video_audio", fake_get_video_audio)
    monkeypatch.setattr("sys.argv", [module, "--output_dir", str(tmp_path)])
    monkeypatch.chdir(tmp_path)  # Restore the directory changed by get_audio.py.
    if success:
        runpy.run_module(module, run_name="__main__")
    else:
        with pytest.raises(SystemExit) as exc_info:
            runpy.run_module(module, run_name="__main__")
        assert exc_info.value.code != 0
    assert len(calls) == 1
