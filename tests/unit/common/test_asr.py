"""Tests for the common.asr module."""

import re

import pytest

asr = pytest.importorskip("common.asr")

OPTIONS = {"highlight_words": False, "max_line_count": None, "max_line_width": None}
TIMING_LINE = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}$")


class FakeModel:
    """Stand-in for a WhisperX pipeline that records its transcribe calls."""

    def __init__(self, result):
        self.result = result
        self.calls = []

    def transcribe(self, *args, **kwargs):
        """Record the call and return the canned transcription."""
        self.calls.append((args, kwargs))
        return self.result


def _words(segment_text, start, end):
    """Build word-level timings spread evenly over a segment, as align does."""
    words = segment_text.split()
    step = (end - start) / len(words)
    return [
        {
            "word": word,
            "start": start + i * step,
            "end": start + (i + 1) * step,
            "score": 0.9,
        }
        for i, word in enumerate(words)
    ]


def _segment(text, start, end):
    """Build an aligned segment with word-level timings."""
    return {
        "start": start,
        "end": end,
        "text": f" {text}",
        "words": _words(text, start, end),
    }


def _aligned(*segments):
    """Build an aligned result from segments, as returned by whisperx.align."""
    return {
        "segments": list(segments),
        "word_segments": [word for segment in segments for word in segment["words"]],
    }


def _run(monkeypatch, aligned, audio_path, output_dir):
    """Run transcribe_audio with stubbed loading, transcription and alignment."""
    monkeypatch.setattr(asr.whisperx, "load_audio", lambda path: "AUDIO")
    monkeypatch.setattr(asr.whisperx, "align", lambda *args, **kwargs: aligned)
    model = FakeModel({"segments": [], "language": "en"})
    asr.transcribe_audio(
        str(audio_path),
        model,
        "ALIGN_MODEL",
        {"language": "en"},
        "cpu",
        str(output_dir),
    )


def test_transcribe_audio_orchestrates_whisperx(monkeypatch, tmp_path):
    """Audio is loaded, transcribed, aligned and written with the right arguments."""
    audio = object()
    segments = [{"start": 1.0, "end": 2.0, "text": " Hallo hallo BAU BAU!"}]
    transcription = {"segments": segments, "language": "en"}
    aligned = _aligned(_segment("Hallo hallo BAU BAU!", 1.0, 2.0))
    align_model = object()
    align_metadata = {"language": "en", "dictionary": {}}
    load_calls = []
    align_calls = []
    writer_factory_calls = []
    writer_calls = []

    def fake_load_audio(*args, **kwargs):
        load_calls.append((args, kwargs))
        return audio

    def fake_align(*args, **kwargs):
        align_calls.append((args, kwargs))
        return aligned

    class FakeWriter:
        always_include_hours = False

        def __call__(self, *args, **kwargs):
            writer_calls.append((args, kwargs, self.always_include_hours))

    def fake_get_writer(*args, **kwargs):
        writer_factory_calls.append((args, kwargs))
        return FakeWriter()

    monkeypatch.setattr(asr.whisperx, "load_audio", fake_load_audio)
    monkeypatch.setattr(asr.whisperx, "align", fake_align)
    monkeypatch.setattr(asr, "get_writer", fake_get_writer)
    model = FakeModel(transcription)
    audio_path = str(tmp_path / "audio_converted.wav")
    output_dir = str(tmp_path / "out")

    asr.transcribe_audio(
        audio_path, model, align_model, align_metadata, "cuda", output_dir
    )

    assert load_calls == [((audio_path,), {})]

    assert len(model.calls) == 1
    args, kwargs = model.calls[0]
    assert args == (audio,)
    assert kwargs == {"batch_size": 16, "language": "en"}
    assert asr.BATCH_SIZE == 16

    assert len(align_calls) == 1
    args, kwargs = align_calls[0]
    assert len(args) == 5
    assert args[0] == segments
    assert args[1] is align_model
    assert args[2] == align_metadata
    assert args[3] is audio
    assert args[4] == "cuda"
    assert kwargs == {"return_char_alignments": False}

    assert writer_factory_calls == [(("vtt", output_dir), {})]

    assert len(writer_calls) == 1
    args, kwargs, always_include_hours = writer_calls[0]
    assert always_include_hours is True
    assert kwargs == {}
    result, written_audio_path, options = args
    assert result["segments"] == aligned["segments"]
    assert result["language"] == "en"
    assert written_audio_path == audio_path
    assert options == OPTIONS


def test_transcribe_audio_names_file_after_audio(monkeypatch, tmp_path):
    """The WebVTT file is named after the audio file, in the output directory."""
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    output_dir = tmp_path / "transcripts"
    output_dir.mkdir()
    aligned = _aligned(_segment("Hallo hallo BAU BAU!", 298.275, 300.901))

    _run(monkeypatch, aligned, audio_dir / "audio_converted.wav", output_dir)

    assert [path.name for path in output_dir.iterdir()] == ["audio_converted.vtt"]
    assert list(audio_dir.iterdir()) == []


def test_transcribe_audio_replaces_existing_file(monkeypatch, tmp_path):
    """An existing WebVTT file with the same name is replaced."""
    output_file = tmp_path / "audio_converted.vtt"
    output_file.write_text("WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nOld text\n\n")
    aligned = _aligned(_segment("New text", 1.0, 2.0))

    _run(monkeypatch, aligned, tmp_path / "audio_converted.wav", tmp_path)

    content = output_file.read_text(encoding="utf-8")
    assert "Old text" not in content
    assert "New text" in content


def test_transcribe_audio_writes_expected_layout(monkeypatch, tmp_path):
    """The WebVTT file has the layout that common.transcript expects."""
    long_text = " ".join(f"word{i}" for i in range(40))
    aligned = _aligned(
        _segment("Hallo hallo BAU BAU!", 298.275, 300.901),
        _segment("It's time for FUWAMOCO Morning!", 300.921, 305.309),
        _segment(long_text, 3700.0, 3725.5),
    )

    _run(monkeypatch, aligned, tmp_path / "audio_converted.wav", tmp_path)

    content = (tmp_path / "audio_converted.vtt").read_text(encoding="utf-8")
    assert content.startswith("WEBVTT\n\n")
    cues = content.removeprefix("WEBVTT\n\n").rstrip("\n").split("\n\n")
    assert [cue.split("\n") for cue in cues] == [
        ["00:04:58.275 --> 00:05:00.901", "Hallo hallo BAU BAU!"],
        ["00:05:00.921 --> 00:05:05.309", "It's time for FUWAMOCO Morning!"],
        ["01:01:40.000 --> 01:02:05.500", long_text],
    ]
    for cue in cues:
        assert TIMING_LINE.match(cue.split("\n")[0])
    assert content.endswith("\n\n")


def test_transcribe_audio_includes_hours_under_one_hour(monkeypatch, tmp_path):
    """Timing lines include hours even when every time is under one hour."""
    aligned = _aligned(_segment("Hallo hallo BAU BAU!", 1.5, 3.25))

    _run(monkeypatch, aligned, tmp_path / "audio_converted.wav", tmp_path)

    content = (tmp_path / "audio_converted.vtt").read_text(encoding="utf-8")
    assert (
        content == "WEBVTT\n\n00:00:01.500 --> 00:00:03.250\nHallo hallo BAU BAU!\n\n"
    )
