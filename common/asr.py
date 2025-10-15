"""This module contains functions related to automatic speech recognition."""

from typing import Any

import whisperx
from transformers import Wav2Vec2ForCTC
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
):
    """Transcribe the audio file using the specified model"""
    audio = whisperx.load_audio(audio_path)
    result = model.transcribe(audio, BATCH_SIZE, language="en")
    result["language"] = "en"
    result = whisperx.align(
        result["segments"],
        align_model,
        align_metadata,
        audio,
        device,
        return_char_alignments=False,
    )
    writer: WriteVTT = get_writer("vtt", output_dir)  # type: ignore[assignment]
    writer.always_include_hours = True
    writer_result = dict(result)
    writer_result["language"] = "en"
    writer(
        writer_result,
        audio_path,  # type: ignore
        {
            "highlight_words": False,
            "max_line_count": None,
            "max_line_width": None,
        },
    )
