"""This module contains functions related to automatic speech recognition."""

import whisperx

# Define constants
BATCH_SIZE = 16


def transcribe_audio(audio_path, model, align_model, align_metadata, new_output_dir):
    """Transcribe the audio file using the specified model"""
    audio = whisperx.load_audio(audio_path)
    result = model.transcribe(audio, BATCH_SIZE, language="en")
    result = whisperx.align(
        result["segments"],
        align_model,
        align_metadata,
        audio,
        "cuda",
        return_char_alignments=False,
    )

    writer = whisperx.utils.get_writer("vtt", new_output_dir)
    writer(result, audio_path)
