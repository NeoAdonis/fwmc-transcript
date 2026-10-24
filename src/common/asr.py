"""Automatic speech recognition with WhisperX.

Transcripts are written in the WebVTT layout that common.transcript expects: a
WEBVTT header and a blank line, then one cue per segment, made of a timing line
with hours always included, a single text line and a blank line, with no cue
identifiers.
"""

import warnings
from typing import Any

from transformers import Wav2Vec2ForCTC

# whisperx imports pyannote.audio, which warns that torchcodec cannot load
# FFmpeg: the torchcodec version pinned by whisperx's torch only supports
# FFmpeg 4-7. It is safe to ignore as long as audio is decoded with
# whisperx.load_audio() (FFmpeg CLI) and passed to pyannote as a waveform,
# which whisperx's VAD and DiarizationPipeline do.
# TODO: Remove this filter once torchcodec supports the system FFmpeg. Never
# pass file paths to pyannote directly (e.g. pyannote.audio.Pipeline for
# diarization) or use torchaudio.load(): both decode through torchcodec and
# raise RuntimeError until this is fixed.
with warnings.catch_warnings():
    warnings.filterwarnings(
        "ignore", message=r"\s*torchcodec is not installed correctly"
    )
    import whisperx
    from whisperx.asr import FasterWhisperPipeline
    from whisperx.utils import WriteVTT, get_writer

# Define constants
BATCH_SIZE = 16


def transcribe_audio(
    audio_path: str,
    model: FasterWhisperPipeline,
    align_model: Wav2Vec2ForCTC,
    align_metadata: dict[str, Any],
    device: str,
    output_dir: str,
) -> None:
    """Transcribe an English audio file into a WebVTT file in the output directory.

    Each segment becomes a single cue on a single line. The file is named after the
    audio file, replacing any existing one, and the output directory must exist.
    """
    audio = whisperx.load_audio(audio_path)
    result = model.transcribe(audio, batch_size=BATCH_SIZE, language="en")
    result = whisperx.align(
        result["segments"],
        align_model,
        align_metadata,
        audio,
        device,
        return_char_alignments=False,
    )
    result["language"] = "en"
    # TODO: Replace "-->" in words, as WhisperX only does it for segments without
    # word timings and it would break the cue.
    writer: WriteVTT = get_writer("vtt", output_dir)  # type: ignore[assignment]
    writer.always_include_hours = True
    writer(
        result,
        audio_path,
        {
            "highlight_words": False,
            "max_line_count": None,
            "max_line_width": None,
        },
    )
