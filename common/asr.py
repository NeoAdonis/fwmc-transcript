"""This module contains functions related to automatic speech recognition."""

import torch
import whisperx

# Define constants
BATCH_SIZE = 16


def transcribe_audio(
    audio_path: str,
    model: whisperx.asr.FasterWhisperPipeline,
    align_model: torch.nn.Module,
    align_metadata: dict,
    output_dir: str,
):
    """Transcribe the audio file using the specified model"""
    audio = whisperx.load_audio(audio_path)
    result = model.transcribe(audio, BATCH_SIZE, language="en")
    result = whisperx.align(
        result["segments"],
        align_model,
        align_metadata,
        audio,
        "cuda" if torch.cuda.is_available() else "cpu",
        return_char_alignments=False,
    )
    result["language"] = "en"
    writer = whisperx.utils.get_writer("vtt", output_dir)
    writer(
        result,
        audio_path,
        {
            "highlight_words": False,
            "max_line_count": None,
            "max_line_width": None,
        },
    )
